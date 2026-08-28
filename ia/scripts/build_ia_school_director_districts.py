#!/usr/bin/env python3
"""
Build data/app/ia-school-director-districts.json — the sub-district fabric
inside Iowa's school districts, read by ia/index.html's School Director
District card (registered `subOf: "school-district-unified"`).

Iowa Code ch. 274/277: a school board is elected either AT LARGE or from
DIRECTOR DISTRICTS, and which one is the district's own choice. This layer
carries both, because the source does.

SOURCE AND LICENCE
------------------
The Iowa Legislature's own ArcGIS organization, `IowaSchoolDirectorDistricts`
(728 features, 326 school districts, verified 2026-08-28).

**THE LICENCE IS ON THE ITEM, NOT ON THE SERVICE.** The FeatureServer's own
metadata returns `licenseInfo: null` and an empty `copyrightText`, which reads
as "no licence stated" and is how this project nearly recorded it. The ITEM
behind it (`5d6e55f885c54dd282eb17daaca20740`, owner
`Jodi.Flory@legis.iowa.gov_iowa`, public) carries `licenseInfo: "<p>CC0</p>"`.
Query `arcgis.com/sharing/rest/search` for the service name before concluding
anything about an ArcGIS layer's terms — the same lesson the Illinois instance
learned about orgs publishing more than their viewers show.

FIVE MEASURED FACTS, THREE OF WHICH CORRECT THIS PROJECT'S OWN RECORD
---------------------------------------------------------------------
1. `DIST_NAME` AND `UID` ARE FULLY POPULATED. An earlier research note in
   docs/IA_EXPANSION_PLAN.md recorded both as "100% NULL across all 728 —
   declared but empty; never read them". Both are populated on all 728.
   `DIST_NAME` is the more useful of the two: its values are `D1`..`D7` and a
   literal **`AT-LARGE`**, so a district that elects at large is READ from the
   publisher's own label rather than inferred from `DISTRICT == 0`.

2. `UID` IS NOT A UNIQUE KEY, and treating it as one would silently drop a
   real district. WEBSTER CITY publishes districts 2 and 3 BOTH carrying
   `UID 3063002`, with different populations (3,611 and 3,666) and different
   geometry — an upstream typo in a key field, not a duplicate row. This
   builder keys on `<school district GEOID>-<DISTRICT>` and asserts that key
   is unique after the dedupe below.

3. TWO DISTRICTS ARE EXACTLY DUPLICATED, not one. The note on file named only
   DAVIS COUNTY (7 districts, every row twice); EAST BUCHANAN (3 districts,
   every row twice) is duplicated identically. A `DAVIS COUNTY`-shaped
   hard-code would have shipped East Buchanan as a six-seat board. The dedupe
   is therefore structural — identical attributes AND identical geometry —
   and it asserts the count it removes rather than naming any county.

4. KINGSLEY-PIERSON IS INCOHERENT AT SOURCE and ships that way, recorded. It
   carries BOTH an `AT-LARGE` row (population 2,503) AND a `D2` row
   (population 632), and has no District 1 at all. It is the single district
   that breaks the otherwise exact rule "at-large districts have exactly one
   feature" (194 of 195 hold). Nothing here invents a District 1 or drops
   either row; the card names what the source says.

5. THE NAME JOIN NEEDS TWO ALIASES, not the three an earlier note assumed.
   322 of 326 source names match a shipped district on the normalized name;
   `DES MOINES IND.` and `WESTERN DUBUQUE` need aliasing, and `MARION
   INDEPENDENT` — previously listed as needing one — matches on its own.
   The two source names left over are `LU VERNE` and `ORIENT-MACKSBURG`, both
   stale in the director layer and both correctly absent from ours.
   **Orient-Macksburg is an independent corroboration of this repo's own
   work**: `build_ia_school_districts.py` dissolved exactly that district into
   Nodaway Valley for 2026-2027, and a second Legislature layer having not
   caught up is the same lag measured from a different direction.

IDENTITY-ONLY, FOR A MEASURED REASON
------------------------------------
No statewide roster of Iowa school board members exists to join. The state
collects them through the Iowa Education Portal, which is login-gated, and the
Iowa Association of School Boards' directory is member-gated. That is a
specific, checkable cause rather than "none was found", and it is what the
card says instead of naming anybody.

Usage:
    python3 ia/scripts/build_ia_school_director_districts.py
    python3 ia/scripts/build_ia_school_director_districts.py --check
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "ia-school-director-districts.json"
PARENT_FILE = os.path.join(APP_DATA_DIR, "ia-school-districts.json")
MAPSHAPER = "mapshaper@0.6.102"

SOURCE = ("https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/"
          "IowaSchoolDirectorDistricts/FeatureServer/0")
ITEM_ID = "5d6e55f885c54dd282eb17daaca20740"      # carries the CC0 licence
PAGE = 1000                                        # the service's maxRecordCount

EXPECT_RAW = 728          # features as published
EXPECT_DUPLICATES = 10    # Davis County (7) + East Buchanan (3), measured
EXPECT_FEATURES = 718     # what ships
EXPECT_SOURCE_NAMES = 326
EXPECT_PARENT = 324       # districts in ia-school-districts.json

# Source names that are stale in the director layer and correctly absent from
# the shipped school-district fabric. ORIENT-MACKSBURG is the district
# build_ia_school_districts.py dissolved into Nodaway Valley for 2026-2027.
STALE_SOURCE_NAMES = {"LU VERNE", "ORIENT-MACKSBURG"}

# Two, and only two, source names that do not normalize onto a shipped name.
NAME_ALIASES = {
    "DESMOINESIND.": "DESMOINESINDEPENDENT",
    "WESTERNDUBUQUE": "WESTERNDUBUQUECOUNTY",
}

# The one district whose rows contradict each other at source (fact 4 above).
KNOWN_INCOHERENT = "KINGSLEY-PIERSON"

AT_LARGE_LABEL = "AT-LARGE"
# Retained-vertex percentage, matching the parent school-district layer. Both
# tighter settings were MEASURED and rejected: 5% clears the 99.5% agreement
# floor by only 0.1 points (99.60%) to save 375 KB, and 3% breaks topology
# outright (a point falling in two districts at once). 9% holds at 99.85% with
# zero overlaps.
SIMPLIFY = "9%"
PRECISION = "0.000001"
STATE_BBOX = {"minLng": -96.84, "minLat": 40.17, "maxLng": -89.94, "maxLat": 43.70}
VALIDATION_KEY = "dkey"


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True,
    ).stdout


def fetch_source():
    """All 728 features with geometry, paged — the service caps at 1,000 and
    a silent truncation here would ship a state with holes in it."""
    feats, offset = [], 0
    while True:
        url = ("%s/query?where=1%%3D1&outFields=SchoolDistrict,DISTRICT,POPULATION,"
               "DIST_NAME,UID&returnGeometry=true&outSR=4326&f=geojson"
               "&resultOffset=%d&resultRecordCount=%d" % (SOURCE, offset, PAGE))
        page = json.loads(_curl(url))
        got = page.get("features", [])
        feats.extend(got)
        if len(got) < PAGE:
            break
        offset += PAGE
    if len(feats) != EXPECT_RAW:
        raise RuntimeError(
            "IowaSchoolDirectorDistricts returned %d features, expected %d — the "
            "source moved; re-derive the duplicate and name-join counts below "
            "before changing this number" % (len(feats), EXPECT_RAW))
    return feats


def _norm(name):
    """Fold a source name onto the shipped school district's own name."""
    n = (name or "").upper()
    n = re.sub(r"\bMT\b", "MOUNT", n)
    n = re.sub(r"\s+SCHOOL\s+DISTRICT$", "", n)
    n = re.sub(r"\s+COMMUNITY$", "", n)
    n = re.sub(r"[^A-Z0-9.]+", "", n)
    return NAME_ALIASES.get(n, n)


def dedupe(feats):
    """Fact 3: two districts publish every row twice. Structural, not by name —
    a row is a duplicate only if its attributes AND its geometry are identical
    to one already kept, so Webster City's UID collision (fact 2, different
    geometry, different population) survives as the two real districts it is.
    """
    seen, kept, dropped = set(), [], []
    for f in feats:
        p = f["properties"]
        key = (p["SchoolDistrict"], p["DISTRICT"], p["POPULATION"], p["DIST_NAME"],
               p["UID"], json.dumps(f["geometry"], sort_keys=True))
        if key in seen:
            dropped.append(p["SchoolDistrict"])
            continue
        seen.add(key)
        kept.append(f)
    if len(dropped) != EXPECT_DUPLICATES:
        raise RuntimeError(
            "dropped %d exact-duplicate features (attributes AND geometry), "
            "expected %d — the source's duplication changed shape. Dropped: %s"
            % (len(dropped), EXPECT_DUPLICATES, sorted(set(dropped))))
    print("  deduped: %d exact duplicates dropped (%s)"
          % (len(dropped), ", ".join(sorted(set(dropped)))), file=sys.stderr)
    return kept


def parent_index():
    with open(PARENT_FILE) as f:
        feats = json.load(f)["features"]
    if len(feats) != EXPECT_PARENT:
        raise RuntimeError("%s carries %d districts, expected %d"
                           % (PARENT_FILE, len(feats), EXPECT_PARENT))
    idx = {}
    for ft in feats:
        p = ft["properties"]
        idx[_norm(p["NAME"])] = (p["NAME"], p["GEOID"])
    return idx


def build_properties(feats, parent):
    """Attach the shipped district's own name and GEOID to every sub-district.

    PROPERTY NAMES ARE ALL LOWERCASE ON PURPOSE: index.html's findPropCI
    lowercases the feature's key but NOT the candidate string, so a camelCase
    property silently never matches and the card row quietly does not render
    (the bug caught in phase 2 PR 6).
    """
    out, unmatched, at_large, numbered = [], set(), 0, 0
    for f in feats:
        p = f["properties"]
        src_name = p["SchoolDistrict"]
        hit = parent.get(_norm(src_name))
        if hit is None:
            unmatched.add(src_name)
            continue
        full_name, geoid = hit
        is_at_large = (p["DIST_NAME"] or "").strip().upper() == AT_LARGE_LABEL
        if is_at_large:
            at_large += 1
        else:
            numbered += 1
        # A display label composed from the publisher's OWN DIST_NAME rather
        # than from the numeric DISTRICT, so an at-large district reads as the
        # source labels it and never as "District 0".
        label = ("Elected at large" if is_at_large
                 else "District %d" % p["DISTRICT"])
        props = {
            "dkey": "%s-%s" % (geoid, p["DISTRICT"]),
            "label": label,
            "name": full_name,
            "geoid": geoid,
            "sourcename": src_name,
            "district": p["DISTRICT"],
            "distname": p["DIST_NAME"],
            "atlarge": is_at_large,
        }
        if p.get("POPULATION") is not None:
            props["population"] = int(p["POPULATION"])
        out.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})

    stale = unmatched - STALE_SOURCE_NAMES
    if stale:
        raise RuntimeError(
            "%d source district name(s) do not join to ia-school-districts.json and "
            "are not recorded as stale: %s. Either add an alias to NAME_ALIASES or "
            "record the name in STALE_SOURCE_NAMES with a reason."
            % (len(stale), sorted(stale)))
    missing = set(parent) - {_norm(f["properties"]["sourcename"]) for f in out}
    if missing:
        raise RuntimeError(
            "%d shipped school district(s) gained no director-district feature: %s"
            % (len(missing), sorted(missing)[:8]))

    keys = [f["properties"]["dkey"] for f in out]
    if len(keys) != len(set(keys)):
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        raise RuntimeError(
            "the <GEOID>-<DISTRICT> key is not unique: %s. UID cannot be used "
            "instead — Webster City publishes two districts under one UID." % dupes)
    print("  joined: %d features | %d at-large, %d numbered | %d stale source "
          "name(s) skipped (%s)"
          % (len(out), at_large, numbered, len(unmatched), ", ".join(sorted(unmatched))),
          file=sys.stderr)
    return out


def check_incoherent(feats):
    """Fact 4: report Kingsley-Pierson rather than smoothing it, and fail if a
    SECOND district ever develops the same contradiction unnoticed."""
    by_name = {}
    for f in feats:
        by_name.setdefault(f["properties"]["sourcename"], []).append(f["properties"])
    bad = []
    for name, rows in by_name.items():
        has_al = any(r["atlarge"] for r in rows)
        if has_al and len(rows) > 1:
            bad.append(name)
    if sorted(bad) != [KNOWN_INCOHERENT]:
        raise RuntimeError(
            "districts carrying an AT-LARGE row alongside numbered rows changed: "
            "%s (expected exactly [%r]). A new one is a source contradiction that "
            "needs recording, not absorbing." % (sorted(bad), KNOWN_INCOHERENT))
    rows = by_name[KNOWN_INCOHERENT]
    print("  recorded incoherence: %s publishes %s — no District 1 exists at source"
          % (KNOWN_INCOHERENT,
             ", ".join("%s (pop %s)" % (r["distname"], r.get("population"))
                       for r in sorted(rows, key=lambda z: z["district"]))),
          file=sys.stderr)


def run_mapshaper(source_path, out_path):
    subprocess.run(
        ["npx", "-y", MAPSHAPER, source_path,
         "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
         "-o", "precision=" + PRECISION, "format=geojson", out_path],
        check=True, cwd=REPO_ROOT,
    )


# --- point-in-polygon (fleet-standard copy, mirrors index.html's even-odd test) ---
def _point_in_ring(pt, ring):
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-16) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_polygon(pt, rings):
    if not rings or not _point_in_ring(pt, rings[0]):
        return False
    return not any(_point_in_ring(pt, h) for h in rings[1:])


def _point_in_geometry(pt, geom):
    if not geom:
        return False
    if geom["type"] == "Polygon":
        return _point_in_polygon(pt, geom["coordinates"])
    if geom["type"] == "MultiPolygon":
        return any(_point_in_polygon(pt, poly) for poly in geom["coordinates"])
    return False


def _bbox(geom):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for part in c:
                walk(part)
    walk(geom["coordinates"])
    return min(xs), min(ys), max(xs), max(ys)


def _model(features):
    return [(f["properties"][VALIDATION_KEY], _bbox(f["geometry"]), f["geometry"])
            for f in features]


def _hits(model, pt):
    x, y = pt
    out = []
    for key, (x0, y0, x1, y1), geom in model:
        if x0 <= x <= x1 and y0 <= y <= y1 and _point_in_geometry(pt, geom):
            out.append(key)
    return out


def validate(source_features, result_features, samples=2000, seed=2024):
    src, new = _model(source_features), _model(result_features)
    rng = random.Random(seed)
    agree = overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        s_hits, o_hits = _hits(new, pt), _hits(src, pt)
        if len(s_hits) > 1:
            overlaps += 1
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        o = o_hits[0] if len(o_hits) == 1 else (None if not o_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    if overlaps > 0:
        return False, "topology broken: %d/%d points fell in >1 district" % (overlaps, samples)
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, "%d/%d (%.2f%%) agreement over the state envelope, 0 overlaps" % (
        agree, samples, pct)


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    raw = fetch_source()
    names = {f["properties"]["SchoolDistrict"] for f in raw}
    if len(names) != EXPECT_SOURCE_NAMES:
        raise RuntimeError("source names %d, expected %d" % (len(names), EXPECT_SOURCE_NAMES))
    print("fetched %d features, %d school districts" % (len(raw), len(names)), file=sys.stderr)

    kept = dedupe(raw)
    if len(kept) != EXPECT_FEATURES:
        raise RuntimeError("after dedupe %d features, expected %d"
                           % (len(kept), EXPECT_FEATURES))
    joined = build_properties(kept, parent_index())
    check_incoherent(joined)

    src_geo = {"type": "FeatureCollection", "features": joined}
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.json")
        out_tmp = os.path.join(tmp, "out.json")
        with open(src_path, "w") as f:
            json.dump(src_geo, f)
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            result = json.load(f)

    n = len(result.get("features", []))
    if n != len(joined):
        raise RuntimeError("mapshaper returned %d features, expected %d" % (n, len(joined)))
    ok, msg = validate(joined, result["features"])
    if not ok:
        raise RuntimeError("simplification changed the answer: " + msg)
    print("  agreement gate: %s" % msg, file=sys.stderr)

    payload = json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n"
    if check_only:
        try:
            with open(out_path) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("%s is missing (%s) — run without --check" % (OUT_NAME, e))
        if shipped != payload:
            raise RuntimeError("%s has drifted from the source. Re-run this builder."
                               % OUT_NAME)
        print("check: shipped layer matches the source", file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/app/%s — %d features, %.1f KB (simplify %s)"
          % (OUT_NAME, n, len(payload) / 1024.0, SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/ia-cc-director-districts.json — the director districts a
community college's board of trustees is elected from, read by ia/index.html's
CC Director District card (registered `subOf: "community-college"`).

Iowa Code 260C.11: each merged area's board of directors is elected from
director districts of substantially equal population. This layer is that
sub-fabric inside the 15 merged areas the `community-college` layer ships.

SOURCE AND LICENCE — AND THE LICENCE IS NOT THE ONE NEXT DOOR'S
----------------------------------------------------------------
`.../CC_DD2023/FeatureServer/0`, 123 features across 15 colleges, effective
2023-08-01, item b89cf40cef40497e80ae8eb0a6e6d22f, owned by `education_iowa`
and attributed to the Iowa Department of Education's Division of Community
Colleges.

Its item `licenseInfo` is **EMPTY** — not the CC0 the school-director-district
layer's item carries. Both were checked the same way and they differ, so the
lesson from that build ("the licence lives on the item, not the service") does
NOT extend to "and it will say CC0". This ships on the same footing as the
parent `community-college` geometry, whose own item states no licence either;
what is recorded here is that the terms are UNSTATED, which is a different
claim from permissive and is written that way on the sources page.

**THE SERVICE'S NAME IS NOT ITS SLUG.** The URL says `CC_DD2023`; the service
calls itself `CC_DirectorDistricts_FINAL`, and searching ArcGIS for the slug
returns unrelated global items — the item is found by the NAME. This is the
`IowaSchoolBldgs`/`PublicSchoolBldgs` trap in a new place: pin the URL, and
search on the name.

THE JOIN IS NUMERIC, AND THAT IS NOT A PREFERENCE
--------------------------------------------------
`CCDISTNAME` does not match the shipped college names in two places — the
source writes "North Iowa Area" and "Northwest" where the app ships "North
Iowa" and "Northwest Iowa" — so a name join needs aliases that a numeric one
does not. `CCdist` matches the shipped `district` for 14 of 15 outright.

The 15th is SOUTHEASTERN, and it is not a data error to route around: this
source numbers it 8, the app ships it as 16, and the app is right. The parent
builder (build_ia_community_colleges.py) already documents that correction —
Southeastern's own board is the 16th merged area and a stale layer numbers it
8 — so the remap here is that same known fact applied once, named, and
asserted rather than discovered again.

DES MOINES AREA: THE TWO PUBLISHERS DISAGREE ABOUT THE COUNT, NOT THE GROUND
-----------------------------------------------------------------------------
This source publishes 123 polygons where the parent layer records 124 seated
directors, and Des Moines Area is the whole difference: it carries districts 1
and 3-9, with NO district numbered 2.

The obvious reading — a missing polygon leaving a hole in the map — was tested
and is WRONG. Two measurements settle it:

  * COVERAGE. Sampling the state, the share of each college's merged area
    covered by NONE of its own director districts runs 0.00%-0.64% across all
    fifteen, and Des Moines Area's is 0.11% — LOWER than most, and lower than
    Southeastern (0.64%), North Iowa (0.49%) and Western Iowa Tech (0.48%).
    Those slivers are digitisation differences between two independently drawn
    layers, the same artifact the Illinois instance measured between Richland
    County's precinct and board layers. Des Moines Area's eight polygons tile
    its merged area as completely as any other college's nine tile theirs.

  * THE SOURCE'S OWN ARITHMETIC. Every feature carries IDEAL, the target
    population per district. Des Moines Area's is 99,579 against a merged-area
    population of 794,895 — that is the total divided by EIGHT (99,362), not by
    nine (88,322) — and each district's DEVIATION is computed against it, all
    within +/-2%. The control confirms the method: Kirkwood's IDEAL implies
    nine for its nine polygons.

So this publisher drew Des Moines Area as EIGHT districts and balanced them for
eight, skipping the number 2. The parent layer says nine directors. **Nothing
here resolves which is right**, and nothing interpolates a district: the map is
complete, the counts disagree, and the card says only what this layer draws.
A build where the shortfall moves fails rather than absorbing the change.

Usage:
    python3 ia/scripts/build_ia_cc_director_districts.py
    python3 ia/scripts/build_ia_cc_director_districts.py --check
"""

import json
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "ia-cc-director-districts.json"
PARENT_FILE = os.path.join(APP_DATA_DIR, "ia-community-colleges.json")
MAPSHAPER = "mapshaper@0.6.102"

SOURCE = ("https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/"
          "CC_DD2023/FeatureServer/0")
SERVICE_NAME = "CC_DirectorDistricts_FINAL"   # NOT the slug; see the docstring
ITEM_ID = "b89cf40cef40497e80ae8eb0a6e6d22f"
PAGE = 1000

EXPECT_FEATURES = 123
EXPECT_COLLEGES = 15
EXPECT_PARENT_DIRECTORS = 124     # what the 15 colleges seat, per the parent layer

# The one college whose numbering differs, and the direction of the fix: this
# source says 8, the app ships 16, and build_ia_community_colleges.py explains
# why the app is right. Asserted below, never applied blind.
SOUTHEASTERN_SOURCE_KEY = 8
SOUTHEASTERN_SHIPPED_KEY = 16

# The single measured disagreement: college -> (polygons drawn here, directors
# the parent layer seats). Measured, not a hole -- see the docstring.
KNOWN_SHORT = {"Des Moines Area": (8, 9)}
KNOWN_SHORT_SKIPPED_NUMBER = 2

SIMPLIFY = "12%"
PRECISION = "0.000001"
STATE_BBOX = {"minLng": -96.84, "minLat": 40.17, "maxLng": -89.94, "maxLat": 43.70}
VALIDATION_KEY = "ddkey"


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True,
    ).stdout


def fetch_source():
    feats, offset = [], 0
    while True:
        url = ("%s/query?where=1%%3D1&outFields=CCdist,DISTRICT,POPULATION,IDEAL,"
               "DEVIATION,DISTNAME,CCDISTNAME&returnGeometry=true&outSR=4326&f=geojson"
               "&resultOffset=%d&resultRecordCount=%d" % (SOURCE, offset, PAGE))
        page = json.loads(_curl(url))
        got = page.get("features", [])
        feats.extend(got)
        if len(got) < PAGE:
            break
        offset += PAGE
    if len(feats) != EXPECT_FEATURES:
        raise RuntimeError(
            "%s returned %d features, expected %d — re-derive the per-college "
            "counts and the Des Moines Area shortfall before changing this number"
            % (SERVICE_NAME, len(feats), EXPECT_FEATURES))
    return feats


def parent_index():
    """college key -> (name, directors seated). Keyed on the SHIPPED district
    number, which is what CCdist joins to after the Southeastern remap."""
    with open(PARENT_FILE) as f:
        feats = json.load(f)["features"]
    if len(feats) != EXPECT_COLLEGES:
        raise RuntimeError("%s carries %d colleges, expected %d"
                           % (PARENT_FILE, len(feats), EXPECT_COLLEGES))
    idx = {}
    for ft in feats:
        p = ft["properties"]
        idx[int(p["district"])] = (p["name"], int(p["directordistricts"]))
    total = sum(v[1] for v in idx.values())
    if total != EXPECT_PARENT_DIRECTORS:
        raise RuntimeError("the parent layer seats %d directors, expected %d"
                           % (total, EXPECT_PARENT_DIRECTORS))
    return idx


def shipped_key(ccdist):
    return SOUTHEASTERN_SHIPPED_KEY if ccdist == SOUTHEASTERN_SOURCE_KEY else ccdist


def build_properties(feats, parent):
    """PROPERTY NAMES ARE ALL LOWERCASE ON PURPOSE: findPropCI lowercases the
    feature's key but NOT the candidate string, so a camelCase property never
    matches and its card row silently does not render."""
    out, per_college, seen_remap = [], {}, False
    for f in feats:
        p = f["properties"]
        ccdist = int(p["CCdist"])
        key = shipped_key(ccdist)
        if ccdist == SOUTHEASTERN_SOURCE_KEY:
            seen_remap = True
        hit = parent.get(key)
        if hit is None:
            raise RuntimeError(
                "source college %r (CCdist %d -> shipped key %d) joins to no "
                "shipped community college" % (p["CCDISTNAME"], ccdist, key))
        name, _seated = hit
        per_college.setdefault(name, 0)
        per_college[name] += 1
        district = int(p["DISTRICT"])
        props = {
            "ddkey": "%d-%d" % (key, district),
            "label": "District %d" % district,
            "district": district,
            "name": name,
            "collegedistrict": key,
            "distname": p["DISTNAME"],
        }
        if p.get("POPULATION") is not None:
            props["population"] = int(p["POPULATION"])
        if p.get("DEVIATION") is not None and p.get("IDEAL"):
            props["deviationpct"] = round(100.0 * float(p["DEVIATION"]) / float(p["IDEAL"]), 1)
        out.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})

    if not seen_remap:
        raise RuntimeError(
            "no feature carried CCdist %d — Southeastern's known mis-numbering is "
            "the reason SOUTHEASTERN_SHIPPED_KEY exists, and if the source has "
            "fixed it this remap must be RETIRED, not left to mis-key something else"
            % SOUTHEASTERN_SOURCE_KEY)

    keys = [f["properties"]["ddkey"] for f in out]
    if len(keys) != len(set(keys)):
        raise RuntimeError("the <college>-<district> key is not unique")

    # Every college must publish exactly the districts its board seats, except
    # the one measured shortfall.
    short = []
    for key, (name, seated) in sorted(parent.items()):
        got = per_college.get(name, 0)
        if got == seated:
            continue
        if KNOWN_SHORT.get(name) == (got, seated):
            short.append(name)
            continue
        raise RuntimeError(
            "%s publishes %d director-district polygons but seats %d directors. "
            "Only %s is a recorded shortfall; a new one is the source changing "
            "shape and needs recording, not absorbing."
            % (name, got, seated, sorted(KNOWN_SHORT)))
    for name in short:
        got, seated = KNOWN_SHORT[name]
        have = {f["properties"]["district"] for f in out
                if f["properties"]["name"] == name}
        missing = sorted(set(range(1, seated + 1)) - have)
        if missing != [KNOWN_SHORT_SKIPPED_NUMBER]:
            raise RuntimeError(
                "%s skips district number(s) %s, expected exactly [%d]"
                % (name, missing, KNOWN_SHORT_SKIPPED_NUMBER))
        print("  recorded disagreement: %s is drawn here as %d districts, skipping "
              "the number %d, and its own IDEAL is the merged area over %d — while "
              "the parent layer seats %d. The two publishers disagree about the "
              "COUNT, not the ground: these polygons tile the college completely."
              % (name, got, KNOWN_SHORT_SKIPPED_NUMBER, got, seated), file=sys.stderr)

    print("  joined: %d features across %d colleges (Southeastern remapped %d -> %d)"
          % (len(out), len(per_college), SOUTHEASTERN_SOURCE_KEY,
             SOUTHEASTERN_SHIPPED_KEY), file=sys.stderr)
    return out


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
    print("fetched %d features" % len(raw), file=sys.stderr)
    joined = build_properties(raw, parent_index())

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

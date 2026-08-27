#!/usr/bin/env python3
"""
Build data/app/ia-school-districts.json — Iowa's 324 unified school
districts, identity-only (no roster: boards are elected at-large or by
director district depending on the district, and no statewide roster of
school-board members exists — the WI school-district-unified precedent).

THE ONE-DISTRICT RECONCILIATION THIS BUILD EXISTS TO DO
----------------------------------------------------------
TIGERweb `School/MapServer/0` (STATE='19') carries **325** features — VERIFIED
live. The Iowa Department of Education's own ArcGIS organization
(services.arcgis.com/vPD5PVLI6sfkZ5E4, the same shared statewide GIS org
ia/scripts/build_ia_supervisor_districts.py reads) carries **324** across two
layers, `CurrentIowaSchoolDistricts` and the newest school-year-versioned
`IowaSchoolDistricts2026_2027` — VERIFIED both edited within two minutes of
each other on 2026-08-27 (the day this builder was written), so they are the
same content kept in sync, not two competing answers.

DIFFING that current (324) layer against the still-shipped-elsewhere
`IowaSchoolDistricts2025_2026` (325, last edited 2026-02-24 — last school
year's map) finds exactly one name absent from the current layer and none
added: **ORIENT-MACKSBURG COMMUNITY SCHOOL DISTRICT dissolved for the
2026-2027 school year.** Spatially sampling ten points across its old
boundary (the centroid plus nine points inset 30% from evenly-spaced
vertices) against the current layer put every one of them inside **NODAWAY
VALLEY COMMUNITY SCHOOL DISTRICT** — a clean, whole absorption, not a split
among several neighbors. TIGERweb is annual-vintage federal data and simply
has not caught up with a consolidation the state's own GIS recorded within
hours of this session's research.

So: TIGERweb's 325 features are the geometry SOURCE (as for every other
pre-built layer in this fleet), and this builder dissolves Orient-Macksburg's
polygon into Nodaway Valley's before simplifying, carrying Nodaway Valley's
own identity (name, GEOID) forward — never inventing a "merged district" name
neither publisher uses. The DE layer's 324 names are the WITNESS this build
checks itself against (a normalized name-set gate), not the geometry source;
if the state ever records a SECOND consolidation this gate fails loudly
rather than silently shipping a 325th-vs-324th mismatch again.

Prerequisites: curl and Node.js (mapshaper).

Usage:
    python3 ia/scripts/build_ia_school_districts.py
    python3 ia/scripts/build_ia_school_districts.py --check   # gates only, no write
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import urllib.parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "ia-school-districts.json"
MAPSHAPER = "mapshaper@0.6.102"

TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0"
IA_FIPS = "19"
TIGER_FIELDS = ["NAME", "BASENAME", "GEOID", "SDUNI", "STATE"]
EXPECT_TIGER = 325

DE_LAYER = "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CurrentIowaSchoolDistricts/FeatureServer/0"
EXPECT_DE = 324

# The one known, measured, dated reconciliation. If the state ever dissolves
# a SECOND district this constant does not cover, the name-set witness gate
# below fails loudly rather than silently accepting a new mismatch.
DISSOLVED_INTO = {
    "Orient-Macksburg Community School District": "Nodaway Valley Community School District",
}

# The DE layer's naming is not uniformly rule-based: it drops "Community" and
# "School District" everywhere, but keeps "Independent" for MARION
# INDEPENDENT while dropping it for WEST BURLINGTON (VERIFIED: the DE layer's
# own two rows are literally "MARION INDEPENDENT" and "WEST BURLINGTON").
# Recorded as an explicit exception rather than a broader regex that would
# risk silently mis-normalizing some other district's real name.
NORM_ALIASES = {
    "WESTBURLINGTONINDEPENDENT": "WESTBURLINGTON",
}

SIMPLIFY = "9%"
PRECISION = "0.000001"
STATE_BBOX = {"minLng": -96.84, "minLat": 40.17, "maxLng": -89.94, "maxLat": 43.70}
VALIDATION_KEY = "GEOID"


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True,
    ).stdout


def fetch_tiger():
    url = (
        TIGERWEB + "/query?where=" + "STATE%3D%27" + IA_FIPS + "%27"
        "&outFields=" + ",".join(TIGER_FIELDS) +
        "&outSR=4326&geometryPrecision=6&f=geojson"
    )
    geo = json.loads(_curl(url))
    feats = geo.get("features") or []
    if geo.get("exceededTransferLimit"):
        raise RuntimeError("TIGERweb School L0 hit the transfer cap — needs paging")
    if len(feats) != EXPECT_TIGER:
        raise RuntimeError(
            "TIGERweb School L0 returned %d Iowa features, expected %d — "
            "the DISSOLVED_INTO reconciliation below may need re-deriving"
            % (len(feats), EXPECT_TIGER)
        )
    return geo


def fetch_de_name_set():
    params = urllib.parse.urlencode({
        "where": "1=1", "outFields": "SchoolDistName", "returnGeometry": "false", "f": "json",
    })
    data = json.loads(_curl(DE_LAYER + "/query?" + params))
    feats = data.get("features") or []
    if len(feats) != EXPECT_DE:
        raise RuntimeError(
            "Dept. of Education CurrentIowaSchoolDistricts returned %d features, "
            "expected %d" % (len(feats), EXPECT_DE)
        )
    return {f["attributes"]["SchoolDistName"] for f in feats}


def _norm(name):
    # normalize away case, "Mt"/"Mount", the trailing "School District" the
    # DE layer never carries, ANY trailing "Community" left over once that's
    # gone (the DE layer drops "Community" too, but — verified against
    # Janesville/Marion/Olin — keeps "Consolidated"/"Independent" as part of
    # the substantive name, so only "School District" and "Community" are
    # ever safe to strip, never the other qualifiers), and all remaining
    # whitespace/punctuation, so a TIGERweb-style full legal name and a
    # DE-style bare name compare equal regardless of internal spacing.
    n = name.upper()
    n = re.sub(r"\bMT\b", "MOUNT", n)
    n = re.sub(r"\s+SCHOOL\s+DISTRICT$", "", n)
    n = re.sub(r"\s+CSD$", "", n)
    n = re.sub(r"\s+COMMUNITY$", "", n)
    n = re.sub(r"[^A-Z0-9]+", "", n)
    return NORM_ALIASES.get(n, n)


def dissolve_source(geo):
    """Overwrite the dissolving district's properties to exactly match its
    absorbing district's, so mapshaper's -dissolve merges the two features
    (and only those two) into one with no field ambiguity."""
    by_name = {f["properties"]["NAME"]: f for f in geo["features"]}
    for old_name, new_name in DISSOLVED_INTO.items():
        old_feat = by_name.get(old_name)
        new_feat = by_name.get(new_name)
        if old_feat is None or new_feat is None:
            raise RuntimeError(
                "DISSOLVED_INTO names %r not both found in TIGERweb's %r"
                % ((old_name, new_name), [f["properties"]["NAME"] for f in geo["features"]])
            )
        old_feat["properties"] = dict(new_feat["properties"])
    return geo


def run_mapshaper(source_path, out_path):
    subprocess.run(
        ["npx", "-y", MAPSHAPER, source_path,
         "-dissolve", "GEOID", "copy-fields=NAME,BASENAME,SDUNI,STATE",
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
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_geometry(pt, geom):
    if geom["type"] == "Polygon":
        inside = False
        for ring in geom["coordinates"]:
            if _point_in_ring(pt, ring):
                inside = not inside
        return inside
    if geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            inside = False
            for ring in poly:
                if _point_in_ring(pt, ring):
                    inside = not inside
            if inside:
                return True
    return False


def _bbox(geom):
    b = [1e9, 1e9, -1e9, -1e9]

    def walk(c):
        if c and isinstance(c[0], (int, float)):
            b[0], b[1] = min(b[0], c[0]), min(b[1], c[1])
            b[2], b[3] = max(b[2], c[0]), max(b[3], c[1])
        else:
            for x in c:
                walk(x)

    walk(geom["coordinates"])
    return b


def _model(features, key_prop):
    return [(f["properties"].get(key_prop), f["geometry"], _bbox(f["geometry"])) for f in features]


def _districts_at(model, pt):
    hits = []
    for key, geom, bb in model:
        if bb[0] <= pt[0] <= bb[2] and bb[1] <= pt[1] <= bb[3] and _point_in_geometry(pt, geom):
            hits.append(key)
    return hits


def validate(source_features, result_features, key_prop, samples=2000, seed=2024):
    src = _model(source_features, key_prop)
    new = _model(result_features, key_prop)
    rng = random.Random(seed)
    agree = overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        s_hits = _districts_at(new, pt)
        if len(s_hits) > 1:
            overlaps += 1
        o_hits = _districts_at(src, pt)
        o = o_hits[0] if len(o_hits) == 1 else (None if not o_hits else "MULTI")
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    if overlaps > 0:
        return False, "topology broken: %d/%d points fell in >1 district" % (overlaps, samples)
    if pct < 99.0:
        # a lower floor than the chambers' 99.5%: every sample point that
        # falls in the now-dissolved Orient-Macksburg sliver of source
        # geometry legitimately reads Nodaway Valley in the result, which
        # is agreement by name but a different TIGERweb source key
        return False, "point-in-district agreement only %.2f%% (need >= 99.0%%)" % pct
    return True, "%d/%d (%.2f%%) agreement over the state envelope, 0 overlaps" % (agree, samples, pct)


def main():
    check_only = "--check" in sys.argv[1:]

    source = fetch_tiger()
    de_names = fetch_de_name_set()
    dissolved = dissolve_source(json.loads(json.dumps(source)))  # deep copy

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "school-src.geojson")
        with open(src_path, "w") as f:
            json.dump(dissolved, f)
        out_tmp = os.path.join(tmp, "school.geojson")
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            simplified = json.load(f)

    n = len(simplified["features"])
    if n != EXPECT_DE:
        raise RuntimeError(
            "%d features after dissolve+simplify, expected exactly %d — the "
            "DISSOLVED_INTO reconciliation may be stale" % (n, EXPECT_DE)
        )

    result_names = {_norm(f["properties"]["NAME"]) for f in simplified["features"]}
    de_norm = {_norm(n) for n in de_names}
    missing = de_norm - result_names
    extra = result_names - de_norm
    if missing or extra:
        raise RuntimeError(
            "name-set witness mismatch against the DE layer — missing %s, extra %s"
            % (sorted(missing), sorted(extra))
        )
    print("witness: %d district names agree with the DE's CurrentIowaSchoolDistricts layer"
          % len(result_names), file=sys.stderr)

    # the un-dissolved TIGERweb source (325 features) is what a reader's
    # simplified result is validated against — dissolving is the fix, not
    # something to also validate the fix against
    ok, msg = validate(source["features"], simplified["features"], VALIDATION_KEY)
    if not ok:
        raise RuntimeError("validation failed: %s" % msg)
    print("gates: %d TIGERweb features dissolved (Orient-Macksburg -> Nodaway Valley) to %d; %s"
          % (EXPECT_TIGER, n, msg), file=sys.stderr)

    if check_only:
        return

    compact = json.dumps(simplified, separators=(",", ":"))
    if json.loads(compact) != simplified:
        raise RuntimeError("round-trip mismatch before writing")
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)
    with open(out_path, "w") as f:
        f.write(compact)
    print("ia-school-districts -> data/app/%s: %d features (statewide); %d bytes (%s retain, 6dp)"
          % (OUT_NAME, n, len(compact), SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

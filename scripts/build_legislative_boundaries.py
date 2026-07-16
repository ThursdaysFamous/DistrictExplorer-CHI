#!/usr/bin/env python3
"""
Build the pre-simplified legislative-district boundary files in data/app/ from
Census TIGERweb, so the app fetches them same-origin (cache-first) instead of
downloading the full statewide geometry live from TIGERweb on every first toggle.

Why this exists: the U.S. House / IL State Senate / IL State House layers used to
call loadTigerLayer(idx), which fetches every Illinois district for that chamber
from tigerweb.geo.census.gov in one shot — ~1-1.8 MB gzip each, measured at
~5.7 s in a production Firefox profile (docs/PERFORMANCE_ANALYSIS_2026-07.md
finding #2 / OPTIMIZATION_PLAYBOOK R2-2). Legislative districts change only on
the decade (post-census redistricting), the exact profile the P0 boundaries
(school-board, IL Supreme Court, Board of Review) were externalized under. This
script does the same for the legislative geometry: fetch → simplify → validate →
write data/app/<chamber>-districts.json, which index.html then fetches like any
other data/app boundary. A ~5.7 s live query becomes a ~200 ms same-origin fetch.

Like build_embedded_boundaries.py this is an occasional OPERATOR step, not weekly
CI — re-run it on redistricting (see docs/REDISTRICTING_RUNBOOK.md). The
officeholder ROSTERS (congress-roster / il-senate-members / il-house-members)
are separate and still refresh weekly; only the geometry is built here.

Simplification is topology-aware mapshaper (Visvalingam, keep-shapes), the same
tool + protocol build_embedded_boundaries.py uses, and the result is validated
against the pre-simplification fetch on the project's 2,000-random-point
point-in-district protocol before anything is written (no point may land in two
districts; classification must agree). If validation fails, nothing is written.

Property fields are trimmed to what the app reads so the file stays small:
extractDistrictNumber() keys on the numeric field (SLDU/SLDL) or, for congress,
the trailing number of a *NAME* field ("Congressional District 5" -> "5"); GEOID
is kept as a stable per-feature key for validation. Every kept field matches what
index.html's query() computes, so classification is byte-identical to the live
layer.

Prerequisites: curl (fetch, works through an HTTPS proxy) and Node.js (mapshaper
via `npx mapshaper@<pinned>`).

Usage:
    python3 scripts/build_legislative_boundaries.py            # build all three
    python3 scripts/build_legislative_boundaries.py congress   # one chamber
"""

import json
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
MAPSHAPER = "mapshaper@0.6.102"  # pinned for reproducible output (matches build_embedded_boundaries.py)
TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
IL_FIPS = "17"

# chamber -> how to build data/app/<out>.
#   layer:    TIGERweb Legislative MapServer layer index (0 US House, 1 IL Senate/Upper, 2 IL House/Lower)
#   fields:   outFields kept from TIGERweb. district_field is read by the app's
#             extractDistrictNumber (SLDU/SLDL directly; congress via the NAME
#             fallback since TIGERweb ships CD119, not the app's cd###fp names).
#   out:      the data/app file index.html fetches for this layer
#   simplify: mapshaper Visvalingam retain % (topology-aware, keep-shapes)
#   min_features: count guard — refuse to write a suspiciously short result
LAYERS = {
    "congress": {
        "layer": 0,
        "fields": ["CD119", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "congress-districts.json",
        "simplify": "12%",
        "min_features": 17,  # 17 IL congressional districts (+ a ZZ water pseudo-district)
    },
    "il-senate": {
        "layer": 1,
        "fields": ["SLDU", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "il-senate-districts.json",
        "simplify": "10%",
        "min_features": 59,  # 59 IL Senate districts (+ ZZ)
    },
    "il-house": {
        "layer": 2,
        "fields": ["SLDL", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "il-house-districts.json",
        "simplify": "9%",
        "min_features": 118,  # 118 IL House districts (+ ZZ)
    },
}
PRECISION = "0.000001"  # 6 decimals ~= 0.11 m — the precision the app requests live
VALIDATION_KEY = "GEOID"  # unique per district, preserved through simplification


def fetch_tiger(layer, fields):
    """Fetch every Illinois feature for a Legislative MapServer layer as GeoJSON.

    Uses curl so it works through an HTTPS proxy (as in the Claude Code sandbox)
    and anywhere curl is present. STATE='17' returns all IL districts for the
    chamber in one query (no transfer-cap paging for these layers)."""
    url = (
        TIGERWEB + "/" + str(layer) + "/query"
        "?where=" + "STATE%3D%27" + IL_FIPS + "%27"
        "&outFields=" + ",".join(fields) +
        "&outSR=4326&geometryPrecision=6&f=geojson"
    )
    out = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "120", url],
        check=True, capture_output=True,
    ).stdout
    geo = json.loads(out)
    feats = geo.get("features") or []
    if not feats:
        raise RuntimeError("TIGERweb layer %d returned no features" % layer)
    if geo.get("exceededTransferLimit"):
        raise RuntimeError("TIGERweb layer %d hit the transfer cap — needs paging" % layer)
    return geo


def run_mapshaper(source_path, simplify, out_path):
    subprocess.run(
        [
            "npx", "-y", MAPSHAPER, source_path,
            "-simplify", "visvalingam", "keep-shapes", simplify,
            "-o", "precision=" + PRECISION, "format=geojson", out_path,
        ],
        check=True, cwd=REPO_ROOT,
    )


# --- point-in-polygon mirroring index.html's even-odd test (so validation
#     agrees with what the app computes at runtime) — same as build_embedded_boundaries.py ---
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


def validate(source_features, simplified_features, key_prop, samples=2000, seed=2024):
    """Refuse the simplification unless it preserves district coverage vs the
    pre-simplification fetch, the project's way (2,000 uniform random points over
    the bbox; any point in two simplified districts is a topology break)."""
    if len(simplified_features) != len(source_features):
        return False, "feature count changed: %d -> %d" % (len(source_features), len(simplified_features))
    src_props = sorted(tuple(sorted(f["properties"].items())) for f in source_features)
    new_props = sorted(tuple(sorted(f["properties"].items())) for f in simplified_features)
    if src_props != new_props:
        return False, "feature properties changed during simplification"

    src = _model(source_features, key_prop)
    new = _model(simplified_features, key_prop)
    ob = [1e9, 1e9, -1e9, -1e9]
    for _, _, bb in src:
        ob[0], ob[1] = min(ob[0], bb[0]), min(ob[1], bb[1])
        ob[2], ob[3] = max(ob[2], bb[2]), max(ob[3], bb[3])

    rng = random.Random(seed)
    agree = overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(ob[0], ob[2]), rng.uniform(ob[1], ob[3]))
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
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, "%d/%d (%.2f%%) agreement, 0 overlaps" % (agree, samples, pct)


def build_chamber(name, cfg):
    source = fetch_tiger(cfg["layer"], cfg["fields"])
    if len(source["features"]) < cfg["min_features"]:
        raise RuntimeError(
            "%s: only %d features fetched (need >= %d) — refusing to write"
            % (name, len(source["features"]), cfg["min_features"])
        )

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, name + "-src.geojson")
        with open(src_path, "w") as f:
            json.dump(source, f)
        out_tmp = os.path.join(tmp, name + ".geojson")
        run_mapshaper(src_path, cfg["simplify"], out_tmp)
        with open(out_tmp) as f:
            simplified = json.load(f)

    ok, msg = validate(source["features"], simplified["features"], VALIDATION_KEY)
    if not ok:
        raise RuntimeError("%s validation failed: %s" % (name, msg))

    compact = json.dumps(simplified, separators=(",", ":"))
    if json.loads(compact) != simplified:
        raise RuntimeError("%s round-trip mismatch before writing" % name)

    os.makedirs(APP_DATA_DIR, exist_ok=True)
    out_path = os.path.join(APP_DATA_DIR, cfg["out"])
    with open(out_path, "w") as f:
        f.write(compact)

    print(
        "%s -> data/app/%s: %d districts; %s; %d bytes (%s retain, 6dp)"
        % (name, cfg["out"], len(simplified["features"]), msg, len(compact), cfg["simplify"]),
        file=sys.stderr,
    )


def main():
    targets = sys.argv[1:] or list(LAYERS)
    unknown = [t for t in targets if t not in LAYERS]
    if unknown:
        print("unknown chamber(s): %s; known: %s" % (unknown, list(LAYERS)), file=sys.stderr)
        sys.exit(1)
    for name in targets:
        build_chamber(name, LAYERS[name])


if __name__ == "__main__":
    main()

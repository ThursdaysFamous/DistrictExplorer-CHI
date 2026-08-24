#!/usr/bin/env python3
"""
Build the pre-simplified legislative-district boundary files in data/app/ from
Census TIGERweb, so the app fetches them same-origin (cache-first) instead of
downloading the full statewide geometry live from TIGERweb on every first toggle.

Why this exists: the U.S. House / CA State Senate / CA State Assembly layers used
to call loadTigerLayer(idx), which fetches every California district for that
chamber from tigerweb.geo.census.gov in one shot — ~8-10 MB each (California is
large: 52/40/80 districts). Legislative districts change only on the decade
(post-census redistricting), the exact profile the offline anchors were
externalized under. This script does the same for the legislative geometry:
fetch -> clip -> simplify -> validate -> write data/app/<chamber>-districts.json,
which index.html then fetches like any other data/app boundary. A ~5-9 s live
query becomes a ~200 ms same-origin fetch.

SF-specific deviation from the reference (which ships Illinois statewide):
California's districts are far larger and more numerous than Illinois's and many
reach hundreds of miles from SF, so shipping the whole state would be multi-MB
per chamber for a city app. Each district is instead CLIPPED to the SF window
(the app's permalink gate, the widest area it accepts a click in) with mapshaper.
Clipping is geometrically exact, so point-in-polygon *inside* the window is
identical to the full district — validate() re-checks that against the unclipped
fetch on the project's 2,000-random-point protocol before anything is written.

Like build_embedded_boundaries.py this is an occasional OPERATOR step, not weekly
CI — re-run it on redistricting. The officeholder ROSTERS (congress-roster /
ca-senate-members / ca-assembly-members) are separate; only the geometry is here.

Simplification is topology-aware mapshaper (Visvalingam, keep-shapes), the same
tool + protocol build_embedded_boundaries.py uses. If validation fails, nothing
is written.

Property fields are trimmed to what the app reads so the file stays small:
extractDistrictNumber() keys on the numeric field (SLDU/SLDL) or, for congress,
the trailing number of a *NAME* field ("Congressional District 11" -> "11");
GEOID is kept as a stable per-feature key for validation.

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
CA_FIPS = "06"

# SF clip window — the permalink gate (index.html's PERMALINK_GATE) plus a small
# margin, the widest area the app accepts a click in. Every kept district is
# clipped to this rectangle, and validation samples only inside it (outside, the
# clipped file intentionally has no geometry and the app never queries there).
CLIP = {"minLng": -122.62, "minLat": 37.58, "maxLng": -122.28, "maxLat": 37.97}

# chamber -> how to build data/app/<out>.
#   layer:    TIGERweb Legislative MapServer layer index (0 US House, 1 CA Senate/Upper, 2 CA Assembly/Lower)
#   fields:   outFields kept from TIGERweb. The app's extractDistrictNumber reads
#             SLDU/SLDL directly; congress uses the NAME fallback since TIGERweb
#             ships CD119, not the app's cd###fp names.
#   out:      the data/app file index.html fetches for this layer
#   simplify: mapshaper Visvalingam retain % (topology-aware, keep-shapes)
#   min_features: count guard — districts intersecting the SF clip window
LAYERS = {
    "congress": {
        "layer": 0,
        "fields": ["CD119", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "congress-districts.json",
        "simplify": "20%",
        "min_features": 4,  # observed 6 (CA-11 + San Mateo/Marin/East Bay edges)
    },
    "ca-senate": {
        "layer": 1,
        "fields": ["SLDU", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "ca-senate-districts.json",
        "simplify": "20%",
        "min_features": 3,  # observed 4 (SD-11 + neighbors)
    },
    "ca-assembly": {
        "layer": 2,
        "fields": ["SLDL", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "ca-assembly-districts.json",
        "simplify": "20%",
        "min_features": 5,  # observed 8 (AD-17 + AD-19 split SF, plus edges)
    },
}
PRECISION = "0.000001"  # 6 decimals ~= 0.11 m — the precision the app requests live
VALIDATION_KEY = "GEOID"  # unique per district, preserved through simplification


def _env():
    return "%s,%s,%s,%s" % (CLIP["minLng"], CLIP["minLat"], CLIP["maxLng"], CLIP["maxLat"])


def fetch_tiger(layer, fields):
    """Fetch the CA features for a Legislative MapServer layer that INTERSECT the
    SF window, as GeoJSON (full district polygons — clipping happens in mapshaper).

    Uses curl so it works through an HTTPS proxy (as in the Claude Code sandbox).
    The envelope query keeps the fetch to the handful of districts SF can touch,
    not all of California."""
    url = (
        TIGERWEB + "/" + str(layer) + "/query"
        "?where=" + "STATE%3D%27" + CA_FIPS + "%27"
        "&geometry=" + _env() +
        "&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects"
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
        raise RuntimeError("TIGERweb layer %d returned no features for the SF window" % layer)
    if geo.get("exceededTransferLimit"):
        raise RuntimeError("TIGERweb layer %d hit the transfer cap — needs paging" % layer)
    return geo


def run_mapshaper(source_path, simplify, out_path):
    subprocess.run(
        [
            "npx", "-y", MAPSHAPER, source_path,
            "-clip", "bbox=" + _env(),
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


def validate(source_features, result_features, key_prop, samples=2000, seed=2024):
    """Refuse the build unless clip+simplify preserves district coverage INSIDE the
    SF window vs the unclipped fetch, the project's way (2,000 uniform random
    points over the clip window). Points are sampled only inside the window —
    outside it the clipped file intentionally has no geometry, and the app never
    queries there. Any point landing in two result districts is a topology break.

    Note the classic feature-count/property-equality checks build_embedded_
    boundaries.py uses do NOT apply here: clipping legitimately drops per-district
    vertices and rewrites bboxes, so this validates by classification agreement
    against the full (unclipped) source instead."""
    src = _model(source_features, key_prop)
    new = _model(result_features, key_prop)
    rng = random.Random(seed)
    agree = overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(CLIP["minLng"], CLIP["maxLng"]), rng.uniform(CLIP["minLat"], CLIP["maxLat"]))
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
    return True, "%d/%d (%.2f%%) agreement over the SF window, 0 overlaps" % (agree, samples, pct)


def build_chamber(name, cfg):
    source = fetch_tiger(cfg["layer"], cfg["fields"])

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, name + "-src.geojson")
        with open(src_path, "w") as f:
            json.dump(source, f)
        out_tmp = os.path.join(tmp, name + ".geojson")
        run_mapshaper(src_path, cfg["simplify"], out_tmp)
        with open(out_tmp) as f:
            simplified = json.load(f)

    if len(simplified["features"]) < cfg["min_features"]:
        raise RuntimeError(
            "%s: only %d districts after clipping (need >= %d) — refusing to write"
            % (name, len(simplified["features"]), cfg["min_features"])
        )

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
        "%s -> data/app/%s: %d districts (clipped to SF); %s; %d bytes (%s retain, 6dp)"
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

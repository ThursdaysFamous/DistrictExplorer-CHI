#!/usr/bin/env python3
"""
Build the pre-simplified Wisconsin legislative-district boundary files in
data/app/ from Census TIGERweb, so the app fetches them same-origin
(cache-first) instead of downloading full statewide geometry live on every
first toggle.

Statewide, like the Illinois reference and unlike the SF fork: Wisconsin's
instance answers anywhere in the state, so each chamber ships whole —
fetch -> simplify -> validate -> write data/app/<chamber>-districts.json.
No clip step: the served area IS the state.

Like build_metro_outline.py this is an occasional OPERATOR step, not weekly
CI — re-run it on redistricting. The officeholder ROSTERS
(wi-senate-members / wi-assembly-members, from Open States) are separate;
only the geometry is here (build_wi_legislature_roster.py builds those).

`us-house` is carried as a target for redistricting re-runs, but the shipped
data/app/congress-districts.json bytes come from the state bootstrap and are
not rewritten unless you name the target explicitly — the default build is
the two chambers only, so a chamber refresh can never churn the congress
file's bytes as a side effect.

Great Lakes note: TIGERweb ships a ZZ "undefined" pseudo-district covering
state waters for each chamber, so Wisconsin's counts come back 34/100, not
33/99. The guards below expect the real district count and tolerate the ZZ
feature; validation is classification agreement, which the water feature
participates in like any other.

Simplification is topology-aware mapshaper (Visvalingam, keep-shapes), the
same tool + protocol as the reference. If validation fails, nothing is
written.

Prerequisites: curl (fetch, works through an HTTPS proxy) and Node.js
(mapshaper via `npx mapshaper@<pinned>`).

Usage:
    python3 wi/scripts/build_legislative_boundaries.py             # both chambers
    python3 wi/scripts/build_legislative_boundaries.py wi-senate   # one chamber
    python3 wi/scripts/build_legislative_boundaries.py us-house    # explicit only
"""

import json
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
MAPSHAPER = "mapshaper@0.6.102"  # pinned for reproducible output (fleet convention)
TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
WI_FIPS = "55"

# The state envelope the app accepts a click in (the worksheet's
# permalink_gate) — validation samples uniformly over it.
STATE_BBOX = {"minLng": -93.09, "minLat": 42.29, "maxLng": -86.04, "maxLat": 47.51}

# chamber -> how to build data/app/<out>.
#   layer:    TIGERweb Legislative MapServer layer index (0 US House, 1 upper, 2 lower)
#   fields:   outFields kept from TIGERweb. The app's extractDistrictNumber reads
#             SLDU/SLDL directly; congress uses the NAME fallback since TIGERweb
#             ships CD120, not a bare number.
#   out:      the data/app file index.html fetches for this layer
#   simplify: mapshaper Visvalingam retain % (topology-aware, keep-shapes)
#   min_features: count guard — the real district count (a ZZ water
#             pseudo-district on top of it is expected and tolerated)
LAYERS = {
    "us-house": {
        "layer": 0,
        # CD120, not CD119: TIGERweb rolled its congressional layer to the
        # 120th Congress ("120th Congressional Districts; January 1, 2026
        # vintage"). The retired field is GONE, not deprecated, and the
        # service answers a query naming it with HTTP 200 carrying a JSON
        # error envelope -- {"error":{"code":400,...}} with no "features"
        # key -- so a status-code check reads it as success. This builder's
        # own no-features guard is what surfaces it, as
        # "returned no features": read that as "the vintage rolled".
        # Measured 2026-09-03.
        "fields": ["CD120", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "congress-districts.json",
        "simplify": "12%",
        "min_features": 8,   # 8 WI congressional districts (+ ZZ)
    },
    "wi-senate": {
        "layer": 1,
        "fields": ["SLDU", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "wi-senate-districts.json",
        "simplify": "10%",
        "min_features": 33,  # 33 WI Senate districts (+ ZZ)
    },
    "wi-assembly": {
        "layer": 2,
        "fields": ["SLDL", "NAME", "BASENAME", "GEOID", "STATE"],
        "out": "wi-assembly-districts.json",
        "simplify": "9%",
        "min_features": 99,  # 99 WI Assembly districts (+ ZZ)
    },
}
DEFAULT_TARGETS = ["wi-senate", "wi-assembly"]  # us-house by explicit ask only
PRECISION = "0.000001"  # 6 decimals ~= 0.11 m — the precision the app requests live
VALIDATION_KEY = "GEOID"  # unique per district, preserved through simplification


def fetch_tiger(layer, fields):
    """Fetch every Wisconsin feature for a Legislative MapServer layer as
    GeoJSON. Uses curl so it works through an HTTPS proxy (as in the Claude
    Code sandbox)."""
    url = (
        TIGERWEB + "/" + str(layer) + "/query"
        "?where=" + "STATE%3D%27" + WI_FIPS + "%27"
        "&outFields=" + ",".join(fields) +
        "&outSR=4326&geometryPrecision=6&f=geojson"
    )
    out = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300", url],
        check=True, capture_output=True,
    ).stdout
    geo = json.loads(out)
    feats = geo.get("features") or []
    if not feats:
        raise RuntimeError("TIGERweb layer %d returned no Wisconsin features" % layer)
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
#     agrees with what the app computes at runtime) — fleet-standard copy ---
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
    """Refuse the build unless simplification preserves district coverage over
    the state envelope vs the full-precision fetch — the project's 2,000
    uniform-random-point protocol. Any point landing in two result districts
    is a topology break."""
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
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, "%d/%d (%.2f%%) agreement over the state envelope, 0 overlaps" % (agree, samples, pct)


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

    n = len(simplified["features"])
    if not (cfg["min_features"] <= n <= cfg["min_features"] + 1):
        raise RuntimeError(
            "%s: %d features after simplify (expected %d districts, +1 for the ZZ "
            "water pseudo-district at most) — refusing to write"
            % (name, n, cfg["min_features"])
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
        "%s -> data/app/%s: %d features (statewide); %s; %d bytes (%s retain, 6dp)"
        % (name, cfg["out"], n, msg, len(compact), cfg["simplify"]),
        file=sys.stderr,
    )


def main():
    targets = sys.argv[1:] or DEFAULT_TARGETS
    unknown = [t for t in targets if t not in LAYERS]
    if unknown:
        print("unknown chamber(s): %s; known: %s" % (unknown, list(LAYERS)), file=sys.stderr)
        sys.exit(1)
    for name in targets:
        build_chamber(name, LAYERS[name])


if __name__ == "__main__":
    main()

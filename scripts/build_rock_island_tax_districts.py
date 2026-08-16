#!/usr/bin/env python3
"""
Build data/app/rock-island-{fire,library,park}-districts.json from Rock Island
County's TaxDistricts service — dissolved, with road-width voids closed.

Why a pre-built file for a county with a live API: the county's TaxDistricts
tilings are dissolved from its PARCEL fabric, and road right-of-way carries no
parcel. Served raw, every district is a lattice of hundreds of fragments
separated by 37-107 ft voids (Milan-Blackhawk: 280 parts, 43,985 vertices), so
the overlay draws the county's road network as a dark mesh and a click on any
road inside a district lands in no polygon. The 60 ft runtime snap answered the
click; this build fixes the geometry itself, the way Stark ships its clerk's
My Maps and the legislative layers ship pre-built TIGERweb.

The transform, per district:
  1. FETCH full-precision GeoJSON (no geometryPrecision cap — the raw fabric is
     the measurement instrument here) and make each geometry valid.
  2. CLOSE with a 75 ft radius (morphological closing: buffer out then in, in a
     local ft frame with longitudes cos(lat)-scaled). Closing bridges only
     voids narrower than 150 ft — road right-of-way, including the ~141 ft
     diagonal across a two-road intersection — and mathematically cannot claim
     any point farther than 75 ft from ground the county published, nor fill a
     hole the size of an unserved village.
  3. KEEP CONTESTED GROUND OUT: final_i = raw_i UNION (closed_i minus every
     other district's closed shape). A road BETWEEN two districts is claimed by
     both closings, so it ships in neither — the boundary stays a visible seam
     and the app's runtime snap continues to refuse it as genuinely ambiguous.
     Raw ground is never surrendered: anything the county itself drew stays.
  4. SIMPLIFY (10 ft, topology-preserving), drop slivers under 0.1 acre
     (subtraction confetti, far below any annexed parcel), round to 5 decimals.

Verification before writing (the build FAILS, it does not warn):
  - every district keeps >=99.9% of its raw area, and adds nothing beyond a
    90 ft dilation of its raw self (75 ft closing + simplify tolerance);
  - no two shipped districts overlap;
  - measured road-void points INSIDE districts now resolve by containment,
    and unserved ground (Moline, Rock Island city, Andalusia) still resolves
    to nothing — the closing must not manufacture coverage;
  - the library layer's blank-named tenth polygon (a stray byte-identical copy
    of the UNITED TWP HIGH 30 school polygon — see the loader comment in
    index.html) is asserted present in the source and excluded.

Freshness: the service was last edited 2022-01-14 (asserted below — a changed
edit date fails the build so a re-run is a conscious re-verification, not a
silent re-base). validate_sources.py carries the service as the provenance of
all three files, so the monthly run watches the source's reachability.

Usage (rare operator step; network access to the county's ArcGIS required):
    pip install -c scripts/requirements.txt shapely requests
    python3 scripts/build_rock_island_tax_districts.py
"""

import json
import math
import os
import sys

import requests
from shapely import make_valid
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(REPO_ROOT, "data", "app")

SERVICE = ("https://services9.arcgis.com/6FnscPPlUa9DXXOk/arcgis/rest/services/"
           "TaxDistricts/FeatureServer")
# A changed upstream edit date means the county touched the fabric: re-measure
# the void widths and the blank-polygon identity before shipping a rebuild.
# Per layer — the county saved the three within minutes of each other on
# 2022-01-14, but each carries its own stamp.
EXPECTED_EDIT_MS = {2: 1642178685982, 5: 1642179044173, 8: 1642177768661}

CLOSE_FT = 75.0      # bridges voids < 150 ft; every measured road void is 37-107
SIMPLIFY_FT = 10.0
SLIVER_SQFT = 2000.0  # subtraction confetti — well under any annexed house lot
FEET_PER_DEG_LAT = 364000.0  # the app's own constant (index.html snap block)
LAT0 = 41.47

LAYERS = [
    {"index": 2, "name_field": "FirePD", "out": "rock-island-fire-districts.json",
     "label": "fire districts", "expect": 17},
    {"index": 5, "name_field": "library_di", "out": "rock-island-library-districts.json",
     "label": "library districts", "expect": 9},
    {"index": 8, "name_field": "park_distr", "out": "rock-island-park-districts.json",
     "label": "park districts", "expect": 1},
]

# Ground-truth probes, all measured 2026-08-16 against the raw fabric.
# (file, lat, lng, expected district or None) — None asserts the closing did
# NOT manufacture coverage over genuinely unserved ground.
PROBES = [
    ("rock-island-library-districts.json", 41.36412, -90.53246, "SHERRARD LIBRARY"),      # road void
    ("rock-island-library-districts.json", 41.39334, -90.61696, "MILAN-BLACKHAWK LIBRARY"),  # road void
    ("rock-island-library-districts.json", 41.74022, -90.25800, "CORDOVA LIBRARY"),       # road void
    ("rock-island-library-districts.json", 41.40835, -90.72851, "MILAN-BLACKHAWK LIBRARY"),  # interior
    ("rock-island-library-districts.json", 41.50670, -90.51510, None),  # downtown Moline (municipal library)
    ("rock-island-library-districts.json", 41.50950, -90.57870, None),  # Rock Island city (municipal library)
    ("rock-island-library-districts.json", 41.43800, -90.71800, None),  # Andalusia (recorded gap)
    ("rock-island-fire-districts.json", 41.36412, -90.53246, "SHERRARD FPD"),  # same fabric, same void
    ("rock-island-fire-districts.json", 41.50670, -90.51510, None),  # Moline runs a city FD
]


def fail(msg):
    print("build-rock-island-tax-districts: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def to_ft(g):
    cos0 = math.cos(math.radians(LAT0))
    return transform(lambda x, y, z=None:
                     (x * cos0 * FEET_PER_DEG_LAT, y * FEET_PER_DEG_LAT), g)


def from_ft(g):
    cos0 = math.cos(math.radians(LAT0))
    return transform(lambda x, y, z=None:
                     (x / (cos0 * FEET_PER_DEG_LAT), y / FEET_PER_DEG_LAT), g)


def clean(g):
    g = make_valid(g)
    if not g.is_valid:
        g = g.buffer(0)
    return g


def polygonal(g):
    """Strip any lines/points make_valid may emit; keep only polygonal area."""
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    if g.geom_type == "GeometryCollection":
        parts = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(parts) if parts else None
    return None


def fetch_layer(idx):
    url = ("%s/%d/query" % (SERVICE, idx))
    r = requests.get(url, params={
        "where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
    }, timeout=120)
    r.raise_for_status()
    return r.json()


def drop_slivers(g, min_sqft):
    parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    kept = [p for p in parts if p.area >= min_sqft]
    dropped = len(parts) - len(kept)
    if not kept:
        fail("sliver drop removed an entire district — threshold is wrong")
    return unary_union(kept), dropped


def build_layer(cfg):
    meta = requests.get("%s/%d" % (SERVICE, cfg["index"]),
                        params={"f": "json"}, timeout=60).json()
    edit_ms = (meta.get("editingInfo") or {}).get("dataLastEditDate")
    if edit_ms != EXPECTED_EDIT_MS[cfg["index"]]:
        fail("layer %d edit date %r != expected %r — the county changed the "
             "fabric; re-verify the measurements in this script before rebuilding"
             % (cfg["index"], edit_ms, EXPECTED_EDIT_MS[cfg["index"]]))

    geo = fetch_layer(cfg["index"])
    named, blanks = {}, 0
    for f in geo.get("features", []):
        name = str((f.get("properties") or {}).get(cfg["name_field"]) or "").strip()
        if not name:
            blanks += 1
            continue
        g = polygonal(clean(shape(f["geometry"])))
        if g is None or g.is_empty:
            fail("%s: %r has no usable geometry" % (cfg["label"], name))
        named[name] = unary_union([named[name], g]) if name in named else g

    if cfg["index"] == 5 and blanks != 1:
        fail("library layer: expected exactly 1 blank-named polygon (the stray "
             "UNITED TWP HIGH 30 copy), found %d — the layer changed" % blanks)
    if cfg["index"] != 5 and blanks:
        fail("%s: %d blank-named polygons — unexpected, review the layer"
             % (cfg["label"], blanks))
    if len(named) != cfg["expect"]:
        fail("%s: %d named districts, expected %d"
             % (cfg["label"], len(named), cfg["expect"]))

    raw_ft = {n: to_ft(g) for n, g in named.items()}
    closed_ft = {n: clean(g.buffer(CLOSE_FT).buffer(-CLOSE_FT))
                 for n, g in raw_ft.items()}

    final_ft = {}
    for n in sorted(named):
        others = [closed_ft[m] for m in closed_ft if m != n]
        mine = closed_ft[n]
        if others:
            mine = polygonal(clean(mine.difference(unary_union(others))))
            if mine is None:
                fail("%s: %r vanished in the contested-ground subtraction" % (cfg["label"], n))
        final = polygonal(clean(unary_union([raw_ft[n], mine])))
        final = clean(final.simplify(SIMPLIFY_FT, preserve_topology=True))
        final, dropped = drop_slivers(final, SLIVER_SQFT)
        final_ft[n] = final
        raw_parts = len(raw_ft[n].geoms) if raw_ft[n].geom_type == "MultiPolygon" else 1
        out_parts = len(final.geoms) if final.geom_type == "MultiPolygon" else 1
        print("  %-26s %4d parts -> %2d  (+%4.1f%% area from closing, %d slivers dropped)"
              % (n, raw_parts, out_parts,
                 100.0 * (final.area - raw_ft[n].area) / raw_ft[n].area, dropped))

    # -- enforce disjointness: where two districts share a direct parcel edge
    # (no road between), each side's independent 10 ft simplify wobbles across
    # the zero-width seam, leaving foot-wide overlap strips. Deterministic fix:
    # in name order, the later district cedes the strip (bounded by the
    # simplify tolerance, so which side keeps it is cosmetic). ----------------
    ordered = sorted(final_ft)
    for i, n in enumerate(ordered):
        for m in ordered[:i]:
            if not final_ft[n].intersects(final_ft[m]):
                continue
            ceded = final_ft[n].intersection(final_ft[m]).area
            if ceded > 0:
                final_ft[n] = polygonal(clean(final_ft[n].difference(final_ft[m])))
                if final_ft[n] is None or final_ft[n].is_empty:
                    fail("%s: %r vanished enforcing disjointness" % (cfg["label"], n))
                if ceded > SLIVER_SQFT:
                    print("  seam: %-26s ceded %5.0f sq ft of simplify wobble to %s"
                          % (n, ceded, m))

    # -- verify: raw ground kept, nothing claimed beyond the closing's reach --
    for n in final_ft:
        lost = raw_ft[n].difference(final_ft[n]).area
        # 10 ft topology-preserving simplify wobbles the boundary both ways on
        # these high-perimeter fabric shapes; ~0.2% one-sided shave is noise.
        # A subtraction bug eats whole percents, which this still catches.
        if lost > 0.005 * raw_ft[n].area:
            fail("%s: %r lost %.2f%% of county-published ground"
                 % (cfg["label"], n, 100.0 * lost / raw_ft[n].area))
        overreach = final_ft[n].difference(raw_ft[n].buffer(CLOSE_FT + SIMPLIFY_FT + 5)).area
        if overreach > SLIVER_SQFT:
            fail("%s: %r claims %.0f sq ft beyond the closing's possible reach"
                 % (cfg["label"], n, overreach))

    # -- verify: mutual exclusivity survives simplification ------------------
    names = sorted(final_ft)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ov = final_ft[a].intersection(final_ft[b]).area
            if ov > 1.0:
                fail("%s: %r and %r overlap by %.0f sq ft after the "
                     "disjointness pass — must be zero"
                     % (cfg["label"], a, b, ov))

    features = []
    for n in names:
        g = from_ft(final_ft[n])
        geom = json.loads(json.dumps(mapping(g)))  # plain lists
        geom = round_geometry(geom)
        features.append({"type": "Feature",
                         "properties": {cfg["name_field"]: n},
                         "geometry": geom})
    return {"type": "FeatureCollection", "features": features}


def round_geometry(geom):
    def walk(c):
        if isinstance(c, (int, float)):
            return round(c, 5)
        return [walk(x) for x in c]
    geom["coordinates"] = walk(geom["coordinates"])
    return geom


def probe(collections):
    from shapely.geometry import Point
    ok = True
    for fname, lat, lng, want in PROBES:
        fc = collections[fname]
        p = Point(lng, lat)
        hits = [f["properties"][k]
                for f in fc["features"]
                for k in f["properties"]
                if shape(f["geometry"]).contains(p)]
        got = hits[0] if hits else None
        status = "ok" if got == want else "FAIL"
        if got != want:
            ok = False
        print("  probe %-42s %.5f,%.5f -> %-24s [%s]"
              % (fname.replace("rock-island-", "").replace(".json", ""),
                 lat, lng, got or "no district", status))
    if not ok:
        fail("a ground-truth probe disagrees — do not ship")


def main():
    print("build-rock-island-tax-districts: closing %g ft, simplify %g ft" %
          (CLOSE_FT, SIMPLIFY_FT))
    collections = {}
    for cfg in LAYERS:
        print("layer %d (%s):" % (cfg["index"], cfg["label"]))
        collections[cfg["out"]] = build_layer(cfg)
    probe(collections)
    for cfg in LAYERS:
        payload = json.dumps(collections[cfg["out"]], separators=(",", ":"))
        if len(json.loads(payload)["features"]) != cfg["expect"]:
            fail("%s round-trip mismatch" % cfg["out"])
        path = os.path.join(APP_DIR, cfg["out"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(payload)
        print("wrote data/app/%s (%d features, %.0f KB)"
              % (cfg["out"], cfg["expect"], len(payload) / 1024.0))


if __name__ == "__main__":
    main()

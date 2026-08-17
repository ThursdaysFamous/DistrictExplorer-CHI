#!/usr/bin/env python3
"""
Build the pre-built parcel-fabric district files in data/app — every county
tiling whose upstream geometry is dissolved from a PARCEL fabric and therefore
draws the road network as voids. Supersedes build_rock_island_tax_districts.py
(Rock Island's three tilings moved into the source table here unchanged).

Why these files exist: a tax tiling dissolved from parcels excludes road
right-of-way, so served raw each district is a lattice of fragments separated
by 15-200 ft voids — the overlay draws the county's road grid as a dark mesh
and a click on any road inside a district lands in no polygon. The 2026-08-16
fleet survey measured the fabric signature across every fire/library/park
source; the SEVERE tier (hundreds of road-band voids: Kendall x3, Macon x3,
Sangamon fire, Cook fire, Rock Island x3) ships pre-built from this script,
while moderate sources keep live fetch + the 60 ft runtime snap.

The transform, per named district (identical to the Rock Island original):
  1. FETCH full-precision GeoJSON, make valid, DISSOLVE BY NAME (tax-code
     tilings publish many rows per district — Kendall's fire is 170 rows for
     10 FPDs).
  2. CLOSE with a 75 ft radius (morphological closing in a local ft frame,
     longitudes cos(lat)-scaled). Closing bridges only voids narrower than
     150 ft — road right-of-way, including the ~141 ft diagonal across an
     intersection — where the two sides face each other along enough
     frontage (erosion dissolves a bridge shorter than the closing diameter,
     so a lone outlying parcel across a road stays separate and the runtime
     snap covers its road strip). It mathematically cannot claim any point
     farther than 75 ft from ground the county published, nor fill a hole
     the size of an unserved municipality.
  3. KEEP CONTESTED GROUND OUT: final_i = raw_i UNION (closed_i minus every
     other district's closed shape). A road BETWEEN two districts is claimed
     by both closings, so it ships in neither — the seam stays visible and
     the runtime snap keeps refusing it as genuinely ambiguous. Raw
     county-published ground is never surrendered — including ground the
     county's own fabric puts in TWO districts (Cook's Clerk tiling double-
     claims Orland∩Mokena by 57 acres): that ships in both, exactly as the
     live layer answers today, and the disjointness pass strips only
     closing-added ground.
  4. SIMPLIFY (10 ft, topology-preserving), drop sub-2000-sq-ft slivers,
     enforce disjointness deterministically (later name cedes the
     simplify-wobble strip), round to 5 decimals.

Verification before writing (the build FAILS, it does not warn):
  - district count equals the pinned expectation, blank-named rows equal the
    pinned expectation (Rock Island's library carries exactly one — a stray
    byte-identical copy of the UNITED TWP HIGH 30 school polygon — excluded);
  - every district keeps >=99.5% of its raw area and claims nothing beyond a
    90 ft dilation of its raw self;
  - no two shipped districts overlap;
  - the road-void signature is GONE: at most a handful of sibling-part gaps
    in the 15-150 ft band survive per source (wider ones are genuine
    separations);
  - hand-measured probes hit: the dead-road points the survey proved
    (Kendall NEWARK FPD, Cook LEYDEN FPD, Rock Island's three) resolve, and
    unserved ground (Chicago Loop, Moline, Rock Island city, Andalusia)
    stays honestly empty — the closing must not manufacture coverage.

Freshness: sources that publish a dataLastEditDate are PINNED — a changed
stamp fails the build so a re-run is a conscious re-verification, not a
silent re-base. Kendall's hosted layers and Cook's MapServer publish no
stamp (Cook's Clerk refreshes tilings in place), so those pin the district
COUNT and name set instead, and validate_sources.py watches each service
monthly via the files' PROVENANCE entries.

Usage (rare operator step; network access to the county services required):
    pip install -c scripts/requirements.txt shapely requests
    python3 scripts/build_parcel_fabric_districts.py            # all sources
    python3 scripts/build_parcel_fabric_districts.py cook-fire  # one slug
"""

import json
import math
import os
import sys

import requests
from shapely import make_valid
from shapely.geometry import mapping, shape, Point
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(REPO_ROOT, "data", "app")

CLOSE_FT = 75.0       # bridges voids < 150 ft; survey medians run 39-107 ft
SIMPLIFY_FT = 10.0
SLIVER_SQFT = 2000.0  # subtraction confetti — well under any annexed house lot
FEET_PER_DEG_LAT = 364000.0  # the app's own constant (index.html snap block)
MAX_RESIDUAL_VOIDS = 5       # sibling gaps left in the 15-150 ft band

RI = ("https://services9.arcgis.com/6FnscPPlUa9DXXOk/arcgis/rest/services/"
      "TaxDistricts/FeatureServer/")
KENDALL = "https://maps.co.kendall.il.us/server/rest/services/Hosted/"
MACON = "https://services1.arcgis.com/a3k0qIja5SolIRYR/arcgis/rest/services/"

# slug -> source config. name_prop is both the case-insensitive read key and
# the property the shipped feature carries (upstream casing preserved).
SOURCES = [
    {"slug": "rock-island-fire", "out": "rock-island-fire-districts.json",
     "layer": RI + "2", "name_prop": "FirePD", "expect": 17,
     "edit_pin": 1642178685982,
     "probes": [(41.36412, -90.53246, "SHERRARD FPD"),      # measured road void
                (41.50670, -90.51510, None)]},              # Moline runs a city FD
    {"slug": "rock-island-library", "out": "rock-island-library-districts.json",
     "layer": RI + "5", "name_prop": "library_di", "expect": 9,
     "edit_pin": 1642179044173, "expect_blanks": 1,  # the stray UT30 school copy
     "probes": [(41.36412, -90.53246, "SHERRARD LIBRARY"),
                (41.39334, -90.61696, "MILAN-BLACKHAWK LIBRARY"),
                (41.74022, -90.25800, "CORDOVA LIBRARY"),
                (41.40835, -90.72851, "MILAN-BLACKHAWK LIBRARY"),
                (41.50670, -90.51510, None),   # downtown Moline (municipal library)
                (41.50950, -90.57870, None),   # Rock Island city (municipal library)
                (41.43800, -90.71800, None)]}, # Andalusia (recorded gap)
    {"slug": "rock-island-park", "out": "rock-island-park-districts.json",
     "layer": RI + "8", "name_prop": "park_distr", "expect": 1,
     "edit_pin": 1642177768661, "probes": []},
    {"slug": "kendall-fire", "out": "kendall-fire-districts.json",
     "layer": KENDALL + "Fire_Protection_Districts/FeatureServer/0",
     "name_prop": "fire", "expect": 10,
     # the loader's historical exclusion, baked in: Joliet runs a city FD
     "exclude_names": ["CITY OF JOLIET FIRE DISTRICT"],
     "probes": [(41.53252, -88.58756, "NEWARK FPD")]},  # measured 99 ft dead road
    {"slug": "kendall-park", "out": "kendall-park-districts.json",
     "layer": KENDALL + "Park_Districts/FeatureServer/0",
     "name_prop": "park", "expect": 5, "probes": []},
    {"slug": "kendall-library", "out": "kendall-library-districts.json",
     "layer": KENDALL + "Library_Districts/FeatureServer/0",
     "name_prop": "library", "expect": 9, "probes": []},
    {"slug": "macon-fire", "out": "macon-fire-districts.json",
     "layer": MACON + "Fire/FeatureServer/0", "name_prop": "Fire",
     "expect": 17, "edit_pin": 1770744832443, "probes": []},
    {"slug": "macon-library", "out": "macon-library-districts.json",
     "layer": MACON + "LibraryJoin_Dissolved/FeatureServer/0",
     "name_prop": "Library", "expect": 10, "edit_pin": 1770745259078,
     "probes": []},
    {"slug": "macon-park", "out": "macon-park-districts.json",
     "layer": MACON + "ParkJoin_Dissolve/FeatureServer/0", "name_prop": "Park",
     "expect": 6, "edit_pin": 1770754910514, "probes": []},
    # Sangamon fire is deliberately NOT here: its 226-fragment source measured
    # as INTERLEAVED, not void-carved — 168 of its sibling gaps are another
    # district's territory and only 2 are empty ground, and closing added
    # +0.0% area when tried. Pre-building it would accomplish nothing; the
    # entry keeps live fetch and the runtime snap covers the two dead spots.
    {"slug": "cook-fire", "out": "cook-fire-districts.json",
     "layer": "https://gis.cookcountyil.gov/traditional/rest/services/"
              "politicalBoundary/MapServer/17",
     "name_prop": "AGENCY_DESCRIPTION", "expect": 40,
     "probes": [(41.91589, -87.86480, "LEYDEN FIRE PROTECTION DISTRICT"),
                (41.88250, -87.62850, None)]},  # the Loop: Chicago has CFD, no FPD
]


def fail(msg):
    print("build-parcel-fabric-districts: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def clean(g):
    g = make_valid(g)
    if not g.is_valid:
        g = g.buffer(0)
    return g


def polygonal(g):
    if g is None:
        return None
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    if g.geom_type == "GeometryCollection":
        parts = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(parts) if parts else None
    return None


def parts_of(g):
    return list(g.geoms) if g.geom_type == "MultiPolygon" else [g]


def drop_slivers(g, label, name):
    parts = parts_of(g)
    kept = [p for p in parts if p.area >= SLIVER_SQFT]
    if not kept:
        fail("%s: sliver drop removed all of %r" % (label, name))
    return unary_union(kept), len(parts) - len(kept)


def residual_voids(final_ft):
    """Sibling-part gaps still in the road band after closing.

    A gap is only a FAILURE when nothing stopped the closing: a corridor
    another district's closing also reached was deliberately left open by the
    contested-ground rule (the seam the runtime snap refuses), so those are
    reported separately and don't fail the build."""
    from shapely.ops import nearest_points
    unexplained, seams = [], []
    for n, g in final_ft.items():
        parts = parts_of(g)
        if len(parts) < 2:
            continue
        tree = STRtree(parts)
        for i, p in enumerate(parts):
            best = None
            for j in tree.query(p.buffer(160)):
                if j == i:
                    continue
                d = parts[j].distance(p)
                if d > 1 and (best is None or d < best[0]):
                    best = (d, j)
            if best and 15 <= best[0] <= 150:
                a, b = nearest_points(p, parts[best[1]])
                mid = Point((a.x + b.x) / 2, (a.y + b.y) / 2)
                near_other = any(final_ft[m].distance(mid) <= CLOSE_FT + 10
                                 for m in final_ft if m != n)
                if near_other:
                    seams.append((n, round(best[0])))
                    break
                # Erosion dissolves a bridge whose facing frontage is shorter
                # than the closing diameter — a lone outlying parcel across a
                # road from its district body stays separate BY CONSTRUCTION.
                # The parcel itself answers by containment and the runtime
                # snap covers the road strip, so report it, don't fail on it.
                r = best[0] / 2.0 + 5
                ov = p.buffer(r).intersection(parts[best[1]].buffer(r))
                if ov.area < (2 * CLOSE_FT) ** 2:
                    seams.append((n, round(best[0])))
                else:
                    unexplained.append((n, round(best[0])))
                break
    return unexplained, seams


def build_source(cfg):
    meta = requests.get(cfg["layer"], params={"f": "json"}, timeout=90).json()
    edit_ms = (meta.get("editingInfo") or {}).get("dataLastEditDate")
    pin = cfg.get("edit_pin")
    if pin is not None and edit_ms != pin:
        fail("%s: edit date %r != pinned %r — the county changed the fabric; "
             "re-verify this script's measurements before rebuilding"
             % (cfg["slug"], edit_ms, pin))
    if pin is None:
        print("  (no edit stamp published — count+name pin is the guard; "
              "live stamp: %r)" % edit_ms)

    geo = requests.get(cfg["layer"] + "/query", params={
        "where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
    }, timeout=180).json()

    named, blanks = {}, 0
    excl = set(cfg.get("exclude_names", []))
    for f in geo.get("features", []):
        props = f.get("properties") or {}
        v = None
        for k in props:
            if k.lower() == cfg["name_prop"].lower():
                v = props[k]
        name = " ".join(str(v or "").split())
        if not name:
            blanks += 1
            continue
        if name in excl:
            continue
        g = polygonal(clean(shape(f["geometry"])))
        if g is None or g.is_empty:
            fail("%s: %r has no usable geometry" % (cfg["slug"], name))
        named[name] = unary_union([named[name], g]) if name in named else g

    if blanks != cfg.get("expect_blanks", 0):
        fail("%s: %d blank-named rows, expected %d — the layer changed"
             % (cfg["slug"], blanks, cfg.get("expect_blanks", 0)))
    if len(named) != cfg["expect"]:
        fail("%s: %d named districts, expected %d (got: %s)"
             % (cfg["slug"], len(named), cfg["expect"], sorted(named)[:20]))

    b = unary_union(list(named.values())).bounds
    lat0 = (b[1] + b[3]) / 2.0
    cos0 = math.cos(math.radians(lat0))

    def to_ft(g):
        return transform(lambda x, y, z=None:
                         (x * cos0 * FEET_PER_DEG_LAT, y * FEET_PER_DEG_LAT), g)

    def from_ft(g):
        return transform(lambda x, y, z=None:
                         (x / (cos0 * FEET_PER_DEG_LAT), y / FEET_PER_DEG_LAT), g)

    raw_ft = {n: to_ft(g) for n, g in named.items()}
    closed_ft = {n: clean(g.buffer(CLOSE_FT).buffer(-CLOSE_FT))
                 for n, g in raw_ft.items()}

    final_ft = {}
    for n in sorted(named):
        mine = closed_ft[n]
        others = [closed_ft[m] for m in closed_ft if m != n]
        if others:
            mine = polygonal(clean(mine.difference(unary_union(others))))
            if mine is None:
                fail("%s: %r vanished in the contested-ground subtraction"
                     % (cfg["slug"], n))
        final = polygonal(clean(unary_union([raw_ft[n], mine])))
        final = clean(final.simplify(SIMPLIFY_FT, preserve_topology=True))
        final, dropped = drop_slivers(final, cfg["slug"], n)
        final_ft[n] = final
        print("  %-42s %4d parts -> %3d  (+%4.1f%% area, %d slivers dropped)"
              % (n[:42], len(parts_of(raw_ft[n])), len(parts_of(final)),
                 100.0 * (final.area - raw_ft[n].area) / raw_ft[n].area, dropped))

    # Deterministic disjointness for CLOSING-ADDED ground only: the later name
    # cedes wobble strips and closing bulges, but ground the county's own
    # fabric puts in BOTH districts (Cook's Clerk tiling double-claims
    # Orland∩Mokena by 57 acres) ships in both, exactly as the live layer
    # answers today — raw ground is never surrendered, even to a sibling.
    ordered = sorted(final_ft)
    raw_overlaps = {}
    for i, a in enumerate(ordered):
        for bn in ordered[i + 1:]:
            ov = raw_ft[a].intersection(raw_ft[bn]).area
            if ov > SLIVER_SQFT:
                raw_overlaps[(a, bn)] = ov
                print("  county double-claim: %-30s ∩ %-30s %8.0f sq ft (kept in both)"
                      % (a[:30], bn[:30], ov))
    def cede(loser, keeper):
        """loser gives up its NON-RAW ground wherever keeper's final claims it."""
        takeable = final_ft[keeper].difference(raw_ft[loser])
        ceded = final_ft[loser].intersection(takeable).area
        if ceded > 0:
            final_ft[loser] = polygonal(clean(final_ft[loser].difference(takeable)))
            if final_ft[loser] is None or final_ft[loser].is_empty:
                fail("%s: %r vanished enforcing disjointness" % (cfg["slug"], loser))
            if ceded > SLIVER_SQFT:
                print("  seam: %-38s ceded %6.0f sq ft to %s"
                      % (loser[:38], ceded, keeper))
    for i, n in enumerate(ordered):
        for m in ordered[:i]:
            if not final_ft[n].intersects(final_ft[m]):
                continue
            cede(n, m)  # later name yields first…
            cede(m, n)  # …then the earlier one sheds any wobble left on n's raw
            # after both, remaining overlap ⊆ raw_n ∩ raw_m: the county's own claim

    for n in final_ft:
        lost = raw_ft[n].difference(final_ft[n]).area
        # Simplify wobble sheds foot-wide strips along shared seams, so a
        # TINY high-perimeter district (Kendall's 0.075 sq mi Montgomery
        # sliver) can lose a large FRACTION that is a trivial AREA. Fail only
        # when both the fraction and the absolute area say real ground went
        # missing — a subtraction bug loses whole percents of a real district.
        if lost > 0.005 * raw_ft[n].area and lost > 25000:
            fail("%s: %r lost %.2f%% of county-published ground (%.0f sq ft)"
                 % (cfg["slug"], n, 100.0 * lost / raw_ft[n].area, lost))
        elif lost > 0.005 * raw_ft[n].area:
            print("  tolerated: %-34s lost %.2f%% (%.0f sq ft of seam wobble)"
                  % (n[:34], 100.0 * lost / raw_ft[n].area, lost))
        over = final_ft[n].difference(
            raw_ft[n].buffer(CLOSE_FT + SIMPLIFY_FT + 5)).area
        if over > SLIVER_SQFT:
            fail("%s: %r claims %.0f sq ft beyond the closing's possible reach"
                 % (cfg["slug"], n, over))
    for i, a in enumerate(ordered):
        for bn in ordered[i + 1:]:
            ov = final_ft[a].intersection(final_ft[bn])
            if ov.area <= 1.0:
                continue
            # the only overlap allowed to survive is the county's own
            # double-claimed ground (plus a wobble margin around it)
            allowed = raw_ft[a].intersection(raw_ft[bn]).buffer(SIMPLIFY_FT + 5)
            extra = ov.difference(allowed).area
            if extra > SLIVER_SQFT:
                fail("%s: %r and %r overlap by %.0f sq ft beyond the county's "
                     "own double-claim" % (cfg["slug"], a, bn, extra))
    unexplained, seams = residual_voids(final_ft)
    if len(unexplained) > MAX_RESIDUAL_VOIDS:
        fail("%s: %d districts carry road-band voids the closing should have "
             "bridged: %s" % (cfg["slug"], len(unexplained), unexplained[:8]))
    if unexplained:
        print("  residual near-gaps (nothing nearby stopped the closing):", unexplained)
    if seams:
        print("  gaps kept by design (contested seam or short-frontage outlier):", seams)

    features = []
    for n in ordered:
        g = from_ft(final_ft[n])
        geom = json.loads(json.dumps(mapping(g)))

        def rnd(c):
            if isinstance(c, (int, float)):
                return round(c, 5)
            return [rnd(x) for x in c]
        geom["coordinates"] = rnd(geom["coordinates"])
        features.append({"type": "Feature",
                         "properties": {cfg["name_prop"]: n},
                         "geometry": geom})
    fc = {"type": "FeatureCollection", "features": features}

    for lat, lng, want in cfg["probes"]:
        p = Point(lng, lat)
        hits = [f["properties"][cfg["name_prop"]] for f in features
                if shape(f["geometry"]).contains(p)]
        got = hits[0] if hits else None
        print("  probe %.5f,%.5f -> %-30s [%s]"
              % (lat, lng, got or "no district", "ok" if got == want else "FAIL"))
        if got != want:
            fail("%s: probe %.5f,%.5f expected %r, got %r"
                 % (cfg["slug"], lat, lng, want, got))

    payload = json.dumps(fc, separators=(",", ":"))
    if len(json.loads(payload)["features"]) != cfg["expect"]:
        fail("%s round-trip mismatch" % cfg["out"])
    with open(os.path.join(APP_DIR, cfg["out"]), "w", encoding="utf-8") as f:
        f.write(payload)
    print("  wrote data/app/%s (%d features, %.0f KB)"
          % (cfg["out"], cfg["expect"], len(payload) / 1024.0))


def main():
    only = set(sys.argv[1:])
    print("build-parcel-fabric-districts: closing %g ft, simplify %g ft"
          % (CLOSE_FT, SIMPLIFY_FT))
    for cfg in SOURCES:
        if only and cfg["slug"] not in only:
            continue
        print("%s:" % cfg["slug"])
        build_source(cfg)


if __name__ == "__main__":
    main()

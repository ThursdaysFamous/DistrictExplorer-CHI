#!/usr/bin/env python3
"""
Build data/app/waterloo-wards.json — the City of Waterloo's five council
wards, drawn by the `city-ward` layer's Waterloo entry in ia/index.html.

Waterloo elects a mayor, two at-large council members, and one from each of
five wards. These are the five; the people are built separately by
build_waterloo_council.py from the city's own council page.

THE SOURCE, AND WHAT IT DOES AND DOES NOT LICENSE
---------------------------------------------------
The city publishes 71 public services from its own ArcGIS organization
(services1.arcgis.com/QOAXA4I2iTKKdBuy), `Wards_view` among them. Queried
unauthenticated on 2026-09-04: 5 polygons, capabilities "Query,Extract",
and BOTH `serviceDescription` AND `copyrightText` EMPTY.

That emptiness is recorded rather than read as permission or as refusal. It
is the plain difference from Des Moines, whose item's licenseInfo opens "All
rights reserved" and whose terms of use REQUIRE a verbatim disclaimer to ship
on the card. Waterloo states no such condition anywhere this build could find,
so no notice ships with this file — and this paragraph exists so the next
reader knows that absence was looked for, not overlooked.

THE IN-BAND ROSTER IS NOT READ HERE, AND IS THE WITNESS ELSEWHERE
------------------------------------------------------------------
Each polygon carries `Ward_Councilperson`, `At_Large1_Councilperson` and
`At_Large2_Councilperson`. Those are NOT shipped by this builder: a roster
attached to a boundary is refreshed when the boundary is (the Coles County
reading), and this layer has no phone, no e-mail and no term. They are read
once, by build_waterloo_council.py, as a cross-witness against the council
page. See that file.

The layer is nonetheless FRESH — dataLastEditDate 2026-09-03, measured
2026-09-04, one day old — which changes nothing about which publisher is
structurally right to read for people. Freshness today is not a maintenance
guarantee tomorrow.

THE TILING GATE, AND THE ONE THING IT DOES THAT DES MOINES'S DOES NOT
-----------------------------------------------------------------------
Erasing the five wards from the city's OWN limits layer should leave nothing
but the seam between two independently digitised outlines. Measured
2026-09-04: 0.013586 sq mi in 156 fragments — 0.0216% of a 62.98 square mile
city — the largest 7,909 m2.

That largest fragment is BIGGER than the 3,482 m2 Des Moines's build records,
and an area-only ceiling copied across would have made that look like a
regression. It is not. Its bounding box is 36 m by 3,156 m and its
Polsby-Popper compactness is 0.0025: a ribbon three kilometres long and a lane
wide, which is precisely what two outlines digitised apart look like. NOT ONE
of the 156 fragments has compactness above 0.30, and the median is 0.0016.

So this builder gates on SHAPE as well as size. A genuine hole — an annexation
the ward layer has not caught up with, where a reader would be told nothing at
all rather than which ward they are in — is one COMPACT part, and compactness
is what distinguishes it. Raising an area ceiling would eventually admit such
a hole; the compactness test would still catch it.

WATERLOO'S CITY LIMITS LAYER CARRIES NO ATTRIBUTES
----------------------------------------------------
`Waterloo_City_Limits_view/0` has exactly two fields, OBJECTID and GlobalID.
There is no Name to filter on and no SqMiles to read, both of which Des
Moines's boundary layer has and its builder uses. The one feature is taken
whole and its area is computed here.

WARD AREAS ARE VERY UNEQUAL AND THAT IS NOT A DEFECT
------------------------------------------------------
Measured: ward 5 is 2.97 sq mi and ward 3 is 18.19. Wards are drawn to equal
POPULATION, not equal area, and this ships the city's own adopted plan exactly
as drawn — no dissolve, no derivation — so no population-deviation ceiling
applies to it. (The fleet's ceilings exist for districts THIS project composes
from parts; see CLAUDE.md's Wayne and Clay paragraphs.)

Usage:
    python3 ia/scripts/build_waterloo_wards.py
    python3 ia/scripts/build_waterloo_wards.py --check
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import datetime
import random

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "waterloo-wards.json"
MAPSHAPER = "mapshaper@0.6.102"

ORG = "https://services1.arcgis.com/QOAXA4I2iTKKdBuy/ArcGIS/rest/services"
SOURCE = ORG + "/Wards_view/FeatureServer/0"
CITY_LAYER = ORG + "/Waterloo_City_Limits_view/FeatureServer/0"
SOURCE_PAGE = "https://www.cityofwaterlooiowa.com/government/city_council/index.php"

EXPECT_WARDS = [1, 2, 3, 4, 5]
CITY_NAME = "Waterloo"

SIMPLIFY = "20%"
PRECISION = "0.000001"

# Share of in-city sample points the SOURCE itself places in two wards at once.
# Measured 2026-09-04 at 0 in 4,000 over the city envelope; the ceiling is well
# above that so a genuine double-assignment fails while digitisation noise does
# not.
SOURCE_OVERLAP_CEILING = 0.02   # fraction of samples, i.e. 2%

# The tiling gate. Measured 2026-09-04: 0.013586 sq mi in 156 fragments,
# largest 7,909 m2, NO fragment with compactness above 0.30 (median 0.0016).
UNCOVERED_CEILING_SQMI = 0.06
UNCOVERED_LARGEST_CEILING_M2 = 20000.0
# The real hole test — see the docstring. A long thin seam scores near 0; a
# compact missing block scores near 1.
UNCOVERED_COMPACTNESS_CEILING = 0.30
# Below this a fragment is too small for compactness to mean anything (a
# handful of vertices), so it is exempt from the shape test but still counted
# in the totals above.
COMPACTNESS_MIN_AREA_M2 = 200.0

LAT0 = 42.495  # Waterloo's latitude, for the equirectangular area projection


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "180",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True).stdout


def fetch_source():
    url = ("%s/query?where=1%%3D1&outFields=SHORTNAME,LONGNAME&returnGeometry=true"
           "&outSR=4326&f=geojson" % SOURCE)
    data = json.loads(_curl(url))
    feats = data.get("features", [])
    nums = sorted(int(f["properties"]["SHORTNAME"]) for f in feats)
    if nums != EXPECT_WARDS:
        raise RuntimeError(
            "the City of Waterloo's Wards service returned wards %s, expected %s. "
            "Waterloo elects one council member from each of five wards; a "
            "different set is the city redistricting or the service changing "
            "shape, and both need reading before anything ships." % (nums, EXPECT_WARDS))
    return feats


def report_vintage():
    """Print the service's own last-edit date rather than pinning one."""
    meta = json.loads(_curl("%s?f=json" % SOURCE))
    ms = (meta.get("editingInfo") or {}).get("dataLastEditDate")
    when = (datetime.datetime.utcfromtimestamp(ms / 1000).isoformat() + "Z"
            if ms else "unknown")
    print("  source dataLastEditDate %s" % when, file=sys.stderr)


def build_properties(feats):
    """PROPERTY NAMES ARE ALL LOWERCASE ON PURPOSE: findPropCI lowercases the
    feature's key but NOT the candidate string, so a camelCase property never
    matches and its card row silently does not render."""
    out = []
    for f in sorted(feats, key=lambda f: int(f["properties"]["SHORTNAME"])):
        p = f["properties"]
        ward = int(p["SHORTNAME"])
        label = (p.get("LONGNAME") or "").strip() or ("Ward %d" % ward)
        props = {
            "ward": ward,
            "label": label,
            "city": CITY_NAME,
            "sqmiles": round(_geom_area_m2(f["geometry"]) / 2.58999e6, 2),
        }
        out.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    return out


# --- geometry -------------------------------------------------------------

def _ring_area_m2(r):
    mx = 111320.0 * math.cos(math.radians(LAT0))
    my = 110540.0
    s = 0.0
    for i in range(len(r) - 1):
        s += (r[i][0] * mx) * (r[i + 1][1] * my) - (r[i + 1][0] * mx) * (r[i][1] * my)
    return abs(s) / 2.0


def _ring_perimeter_m(r):
    mx = 111320.0 * math.cos(math.radians(LAT0))
    my = 110540.0
    p = 0.0
    for i in range(len(r) - 1):
        p += math.hypot((r[i + 1][0] - r[i][0]) * mx, (r[i + 1][1] - r[i][1]) * my)
    return p


def _rings_area_m2(rings):
    return _ring_area_m2(rings[0]) - sum(_ring_area_m2(h) for h in rings[1:])


def _each_polygon(geom):
    if not geom:
        return []
    if geom["type"] == "MultiPolygon":
        return [rings for rings in geom["coordinates"] if rings]
    if geom["type"] == "Polygon":
        return [geom["coordinates"]] if geom["coordinates"] else []
    return []


def _geom_area_m2(geom):
    return sum(_rings_area_m2(rings) for rings in _each_polygon(geom))


def check_tiles_the_city(ward_features):
    """Refuse if the five wards leave real city ground unrepresented.

    Erases the wards from the city's own limits layer. What survives should be
    the seam between two independently drawn outlines -- many long thin
    perimeter fragments. ONE COMPACT PART is a hole, and a reader standing in
    it would be told nothing at all rather than which ward they are in, which
    is the failure this gate exists for.
    """
    city = json.loads(_curl("%s/query?where=1%%3D1&outFields=*&returnGeometry=true"
                            "&outSR=4326&f=geojson" % CITY_LAYER))
    feats = city.get("features", [])
    if not feats:
        raise RuntimeError("the city's own City Limits layer returned no feature, "
                           "so the tiling gate cannot run")
    city_m2 = sum(_geom_area_m2(f["geometry"]) for f in feats)
    city_sqmi = city_m2 / 2.58999e6

    with tempfile.TemporaryDirectory() as tmp:
        cpath = os.path.join(tmp, "city.json")
        wpath = os.path.join(tmp, "wards.json")
        upath = os.path.join(tmp, "union.json")
        gpath = os.path.join(tmp, "gap.json")
        with open(cpath, "w") as f:
            json.dump(city, f)
        with open(wpath, "w") as f:
            json.dump({"type": "FeatureCollection", "features": ward_features}, f)
        subprocess.run(["npx", "-y", MAPSHAPER, wpath, "-dissolve",
                        "-o", upath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["npx", "-y", MAPSHAPER, cpath, "-erase", upath,
                        "-o", gpath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        with open(gpath) as f:
            gap = json.load(f)

    parts = []          # (area_m2, polsby_popper)
    for f in gap.get("features", []):
        for rings in _each_polygon(f.get("geometry")):
            a = _rings_area_m2(rings)
            per = _ring_perimeter_m(rings[0])
            pp = (4.0 * math.pi * a / (per * per)) if per else 0.0
            parts.append((a, pp))

    total_m2 = sum(a for a, _ in parts)
    total_sqmi = total_m2 / 2.58999e6
    largest = max((a for a, _ in parts), default=0.0)
    compact = [(a, pp) for a, pp in parts
               if a >= COMPACTNESS_MIN_AREA_M2 and pp > UNCOVERED_COMPACTNESS_CEILING]

    if compact:
        worst_a, worst_pp = max(compact, key=lambda t: t[0])
        raise RuntimeError(
            "%d uncovered fragment(s) are COMPACT (the largest %.0f m2 at "
            "Polsby-Popper %.3f, ceiling %.2f). A long thin fragment is two "
            "outlines digitised apart; a compact one is a HOLE -- ground inside "
            "the city that no ward claims, where the card would answer nothing. "
            "Find where it is before shipping."
            % (len(compact), worst_a, worst_pp, UNCOVERED_COMPACTNESS_CEILING))
    if total_sqmi > UNCOVERED_CEILING_SQMI or largest > UNCOVERED_LARGEST_CEILING_M2:
        raise RuntimeError(
            "the five wards leave %.4f sq mi of the city uncovered in %d parts, the "
            "largest %.0f m2 (ceilings %.2f sq mi / %.0f m2). Every fragment is thin, "
            "so this is seam and not a hole -- but it has grown well past what was "
            "measured, which means the two outlines have moved apart and both need "
            "re-reading." % (total_sqmi, len(parts), largest,
                             UNCOVERED_CEILING_SQMI, UNCOVERED_LARGEST_CEILING_M2))

    med = sorted(pp for _, pp in parts)[len(parts) // 2] if parts else 0.0
    print("  tiling gate: the 5 wards cover the city's %.2f sq mi to within %.4f sq mi "
          "(%.4f%%) in %d fragments, largest %.0f m2, median compactness %.4f, none "
          "compact" % (city_sqmi, total_sqmi, 100.0 * total_sqmi / max(city_sqmi, 1e-9),
                       len(parts), largest, med), file=sys.stderr)


def run_mapshaper(source_path, out_path):
    subprocess.run(
        ["npx", "-y", MAPSHAPER, source_path,
         "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
         "-o", "precision=" + PRECISION, "format=geojson", out_path],
        check=True, cwd=REPO_ROOT, capture_output=True)


def _point_in_ring(pt, ring):
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def _point_in_polygon(pt, rings):
    if not _point_in_ring(pt, rings[0]):
        return False
    return not any(_point_in_ring(pt, h) for h in rings[1:])


def _point_in_geometry(pt, geom):
    return any(_point_in_polygon(pt, rings) for rings in _each_polygon(geom))


def _bbox(geom):
    xs, ys = [], []
    for rings in _each_polygon(geom):
        for x, y in rings[0]:
            xs.append(x)
            ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys))


def _model(features):
    return [(f["properties"]["ward"], _bbox(f["geometry"]), f["geometry"])
            for f in features]


def _hits(model, pt):
    out = []
    for key, bb, geom in model:
        if bb[0] <= pt[0] <= bb[2] and bb[1] <= pt[1] <= bb[3]:
            if _point_in_geometry(pt, geom):
                out.append(key)
    return out


def validate(source_features, result_features, samples=4000, seed=2026):
    """Sample the WARDS' OWN envelope, not the state's.

    This layer covers 63 square miles. Over a state envelope virtually every
    sample would land outside all five wards, both models would answer "none",
    and a 99.5% gate would pass on a layer simplified into nothing. Sampling
    the city's own bounding box makes roughly half the points land inside a
    ward, which is what actually exercises the boundaries.
    """
    src, new = _model(source_features), _model(result_features)
    xs = [b for _, bb, _ in src for b in (bb[0], bb[2])]
    ys = [b for _, bb, _ in src for b in (bb[1], bb[3])]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    rng = random.Random(seed)
    agree = new_over = src_over = inside = 0
    for _ in range(samples):
        pt = (rng.uniform(lo_x, hi_x), rng.uniform(lo_y, hi_y))
        s_hits, o_hits = _hits(new, pt), _hits(src, pt)
        if len(s_hits) > 1:
            new_over += 1
        if len(o_hits) > 1:
            src_over += 1
        if o_hits:
            inside += 1
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        o = o_hits[0] if len(o_hits) == 1 else (None if not o_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    if new_over > src_over:
        return False, ("simplification ADDED overlap: %d/%d points fall in >1 ward "
                       "against the source's own %d" % (new_over, samples, src_over))
    if src_over > samples * SOURCE_OVERLAP_CEILING:
        return False, ("the source places %d/%d points in two wards at once "
                       "(ceiling %.0f); measure the overlap's SHAPE before raising "
                       "anything" % (src_over, samples, samples * SOURCE_OVERLAP_CEILING))
    if inside < samples * 0.25:
        return False, ("only %d/%d sample points fell inside any ward — the envelope "
                       "is not exercising the boundaries" % (inside, samples))
    if pct < 99.5:
        return False, "point-in-ward agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, ("%d/%d (%.2f%%) agreement over the city envelope, %d inside a ward; "
                  "overlap %d in the source and %d after simplifying"
                  % (agree, samples, pct, inside, src_over, new_over))


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    raw = fetch_source()
    print("fetched %d wards from the City of Waterloo" % len(raw), file=sys.stderr)
    report_vintage()
    built = build_properties(raw)
    for f in built:
        print("  %-8s %6.2f sq mi" % (f["properties"]["label"],
                                      f["properties"]["sqmiles"]), file=sys.stderr)
    check_tiles_the_city(built)

    src_geo = {"type": "FeatureCollection", "features": built}
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.json")
        out_tmp = os.path.join(tmp, "out.json")
        with open(src_path, "w") as f:
            json.dump(src_geo, f)
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            result = json.load(f)

    n = len(result.get("features", []))
    if n != len(built):
        raise RuntimeError("mapshaper returned %d features, expected %d"
                           % (n, len(built)))
    ok, msg = validate(built, result["features"])
    if not ok:
        raise RuntimeError("simplification changed the answer: " + msg)
    print("  agreement gate: %s" % msg, file=sys.stderr)

    # No `disclaimer` key: the city states no required notice (see the
    # docstring). The card renders that row only when the key is present, so
    # Waterloo's card correctly shows none.
    result["sourceUrl"] = SOURCE_PAGE

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
    print("wrote data/app/%s — %d wards, %.1f KB (simplify %s)"
          % (OUT_NAME, n, len(payload) / 1024.0, SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

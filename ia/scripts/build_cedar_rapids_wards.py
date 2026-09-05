#!/usr/bin/env python3
"""
Build data/app/cedar-rapids-wards.json — the City of Cedar Rapids' five
council districts, drawn by the `city-ward` layer's Cedar Rapids entry in
ia/index.html.

Cedar Rapids elects a mayor, three at-large council members, and one from each
of five districts. These are the five; the people are built separately by
build_cedar_rapids_council.py from the city's own seat pages.

THE SOURCE IS A COUNTY LAYER HOLDING TWO CITIES, KEYED BY AN OPAQUE CODE
-------------------------------------------------------------------------
Linn County's `ElectionsCityCouncilDistrict` is not Cedar Rapids' layer. It is
the COUNTY's, and it carries nine polygons for the two Linn cities that elect
by district: Cedar Rapids' five and Marion's four. The only thing separating
them is `POLITICAL_TWP`, which is '27' and '21' — a bare code with no name
field anywhere in the service, no domain, and no description.

**A BUILD KEYED ON AN OPAQUE CODE MUST PROVE THE CODE, NOT ASSUME IT.** Nothing
published says 27 is Cedar Rapids. A single point test inside downtown Cedar
Rapids returns 27, and that is exactly the evidence that would still look right
if the county swapped the two codes tomorrow — the point would then return 21
and a build that trusted one probe would ship Marion's four districts to Cedar
Rapids readers under Cedar Rapids labels. So the identity is established by
TILING and re-established on every run, in both directions (see
check_tiles_the_city and check_cross_control below).

Measured 2026-09-04, unauthenticated:

    POLITICAL_TWP='27'  5 polygons, districts 1-5, 76.340 sq mi
    POLITICAL_TWP='21'  4 polygons, districts 1-4, 18.253 sq mi
    Cedar Rapids place (TIGERweb)                 76.094 sq mi
    Marion place       (TIGERweb)                 18.096 sq mi

    27 vs Cedar Rapids  ratio 1.00323   residual 0.134%   <- ships
    21 vs Cedar Rapids  ratio 0.23987   residual 99.996%  <- the control
    21 vs Marion        ratio 1.00866   residual 0.246%
    27 vs Marion        ratio 4.21854   residual 99.986%  <- the control

The two controls are the point of the table. A gate that only checks that 27
tiles Cedar Rapids would also pass if 27 tiled EVERYTHING; the controls are
what make the first row mean "27 is Cedar Rapids" rather than "27 is large".

TWO INDEPENDENT PUBLISHERS AGREE WITH THAT ARITHMETIC, and neither was used to
derive it. Linn County's own election-services page is titled "Cedar Rapids
Council Districts & Marion Ward Maps" and publishes five Cedar Rapids district
PDFs beside a Marion wards map. And the City of Cedar Rapids' own "Find Your
District" page sends readers to precisely that county page — the city naming
the county as the authority for its own district lines, which is the provenance
link this build rides.

THERE IS NO IN-BAND ROSTER HERE, AND THAT IS A DIFFERENCE FROM WATERLOO
------------------------------------------------------------------------
Waterloo's ward layer carries `Ward_Councilperson` and both at-large names, so
its builder has a name-level cross-witness against the council page (the Coles
County reading: an in-band roster is a build-time WITNESS, never the roster).
Linn's layer carries `POLITICAL_TWP`, `CITYCOUNCIL` and `Updated`. There are no
names in band at all.

So no name-level witness exists for Cedar Rapids and this file does not pretend
one does. What IS witnessed is the COUNT and the NUMBERING: the city publishes
exactly five district pages numbered 1-5, the county publishes exactly five
district polygons numbered 1-5, and build_cedar_rapids_council.py fails if the
seats it scrapes do not match the districts shipped here. That is a weaker
check than Waterloo's and is recorded as weaker rather than described as the
same thing.

CITY LIMITS COME FROM TIGERWEB BECAUSE LINN PUBLISHES NONE
------------------------------------------------------------
Waterloo's own org publishes `Waterloo_City_Limits_view`; Des Moines' publishes
its boundary too. Linn County's 165 public services include no city-limits
polygon (`RealEstateBoundary` is a cadastral LINE layer — parcel, lot and ROW
lines, not municipal limits), so the tiling gate compares against TIGERweb's
incorporated-place layer, the same source `municipality` already ships from.

That is a CROSS-PUBLISHER comparison where Waterloo's is same-publisher, and it
is why every ceiling below is looser than Waterloo's. Cedar Rapids' residual is
0.134% where Waterloo's is 0.0216% — about six times larger — and none of that
difference is evidence of a worse boundary. It is two organisations digitising
the same city in different years.

THE COMPACTNESS FLOOR IS 2,000 m2 HERE AND 200 m2 IN WATERLOO'S BUILDER
------------------------------------------------------------------------
Waterloo's gate exempts fragments under 200 m2 from the shape test, because
below that a fragment is a handful of vertices and compactness means nothing.
COPIED ACROSS UNCHANGED, THAT GATE FAILS CEDAR RAPIDS — and not on a hole.

The residual's two most compact fragments are 263.6 m2 at Polsby-Popper 0.617
and 171.5 m2 at 0.461. The second is already exempt at Waterloo's floor; the
first is 0.065 acres, roughly a quarter of a suburban lot, and it is square
because a corner where two independent outlines disagree is square. Comparing
against a different publisher's digitisation produces more of those than
comparing against the city's own.

So the floor is raised to 2,000 m2, which is the scale at which a fragment
could hold somebody — a few residential parcels — and the gate keeps its
meaning: a compact fragment big enough to live in is a hole, and a reader
standing in it would be told nothing at all. Measured 2026-09-04: ZERO
fragments are both above 2,000 m2 and above 0.30 compactness. The number is
raised with a reason and the measurement recorded, not tuned until green.

DISTRICT AREAS ARE UNEQUAL AND THAT IS NOT A DEFECT
-----------------------------------------------------
Districts are drawn to equal POPULATION, not equal area, and this ships the
city's own adopted plan exactly as the county publishes it — no dissolve, no
derivation — so no population-deviation ceiling applies.

MARION IS MEASURED AND READY AND IS DELIBERATELY NOT SHIPPED HERE
-------------------------------------------------------------------
The same query with POLITICAL_TWP='21' yields Marion's four wards, and the
tiling table above shows they pass the same test. They are not built because a
boundary without a roster is half a card, and Marion's roster is its own
scrape, its own floors and its own weekly workflow. Recorded in ia/WATCH.md as
the next city rather than half-done here.
"""

import datetime
import json
import math
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "cedar-rapids-wards.json"
MAPSHAPER = "mapshaper@0.6.102"

ORG = "https://services.arcgis.com/i14SLLmXo7Hn9vNc/ArcGIS/rest/services"
SOURCE = ORG + "/ElectionsCityCouncilDistrict/FeatureServer/0"
TIGERWEB = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "Places_CouSub_ConCity_SubMCD/MapServer/4")
# Linn County's own page for these lines, which the CITY's "Find Your District"
# page links to. Provenance for the boundary; the council file carries the
# people's source and is what the card links.
SOURCE_PAGE = "https://www.linncountyiowa.gov/1350/Cedar-Rapids-Council-Districts-Marion-Wa"

CITY_NAME = "Cedar Rapids"
CITY_TWP = "27"
EXPECT_DISTRICTS = [1, 2, 3, 4, 5]

# The control: this code is Marion's, and it must NOT look like Cedar Rapids.
CONTROL_TWP = "21"
CONTROL_CITY = "Marion"
CONTROL_DISTRICTS = [1, 2, 3, 4]

SIMPLIFY = "20%"
PRECISION = "0.000001"

SOURCE_OVERLAP_CEILING = 0.02   # fraction of samples

# --- the tiling ceilings, all measured 2026-09-04 -------------------------
# residual 0.1018 sq mi (0.1338% of the city) in 366 fragments, largest
# 34,190 m2 at compactness 0.0396. See the docstring for why these are looser
# than Waterloo's: this compares two publishers, that one compares a city
# against itself.
UNCOVERED_CEILING_SQMI = 0.30
UNCOVERED_LARGEST_CEILING_M2 = 80000.0
UNCOVERED_COMPACTNESS_CEILING = 0.30
COMPACTNESS_MIN_AREA_M2 = 2000.0

# The identity gate. The city's districts must account for essentially all of
# the city (ratio near 1), and the CONTROL township must not (ratio far from
# 1). The bands are wide because they are asked to tell 1.003 from 0.240 and
# 4.219 — a distinction no plausible boundary drift can blur.
IDENTITY_RATIO_LO = 0.90
IDENTITY_RATIO_HI = 1.15
CONTROL_RESIDUAL_MIN_PCT = 50.0

LAT0 = 41.98  # Cedar Rapids' latitude, for the equirectangular area projection


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "180",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True).stdout


def fetch_districts(twp, expect, who):
    url = ("%s/query?where=POLITICAL_TWP%%3D%%27%s%%27&outFields=CITYCOUNCIL"
           "&returnGeometry=true&outSR=4326&f=geojson" % (SOURCE, twp))
    data = json.loads(_curl(url))
    feats = data.get("features", [])
    nums = sorted(int(f["properties"]["CITYCOUNCIL"]) for f in feats)
    if nums != expect:
        raise RuntimeError(
            "Linn County's ElectionsCityCouncilDistrict returned districts %s for "
            "POLITICAL_TWP=%r (%s), expected %s. Either the city redistricted, or "
            "the county has reassigned the township codes this build is keyed on. "
            "Both need reading before anything ships — and the second is why the "
            "cross-control gate exists." % (nums, twp, who, expect))
    return feats


def fetch_place(basename):
    """TIGERweb's incorporated place, by BASENAME.

    NAME carries the ' city' suffix ('Cedar Rapids city') and BASENAME does
    not; filtering on NAME returns nothing, silently, which reads exactly like
    a place that does not exist.
    """
    url = ("%s/query?where=STATE%%3D%%2719%%27+AND+BASENAME%%3D%%27%s%%27"
           "&outFields=GEOID,BASENAME&returnGeometry=true&outSR=4326&f=geojson"
           % (TIGERWEB, basename.replace(" ", "+")))
    data = json.loads(_curl(url))
    feats = data.get("features", [])
    if not feats:
        raise RuntimeError(
            "TIGERweb returned no Iowa place named %r, so the tiling gate cannot "
            "run. Check BASENAME rather than NAME — NAME carries a ' city' suffix "
            "and matching it returns an empty set that looks like absence."
            % basename)
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
    matches and its card row silently does not render.

    The label says DISTRICT because that is what Cedar Rapids calls these and
    what its own seat pages are titled. Des Moines and Waterloo say WARD and
    their files say Ward. The card renders whichever the city uses; only the
    toggle is generic.
    """
    out = []
    for f in sorted(feats, key=lambda f: int(f["properties"]["CITYCOUNCIL"])):
        num = int(f["properties"]["CITYCOUNCIL"])
        props = {
            "ward": num,
            "label": "District %d" % num,
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


def _residual(district_features, place_features):
    """Erase the districts from the place; return (parts, place_m2).

    parts is a list of (area_m2, polsby_popper) for every leftover ring.
    """
    place_m2 = sum(_geom_area_m2(f["geometry"]) for f in place_features)
    with tempfile.TemporaryDirectory() as tmp:
        ppath = os.path.join(tmp, "place.json")
        dpath = os.path.join(tmp, "districts.json")
        upath = os.path.join(tmp, "union.json")
        gpath = os.path.join(tmp, "gap.json")
        with open(ppath, "w") as f:
            json.dump({"type": "FeatureCollection", "features": place_features}, f)
        with open(dpath, "w") as f:
            json.dump({"type": "FeatureCollection", "features": district_features}, f)
        subprocess.run(["npx", "-y", MAPSHAPER, dpath, "-dissolve",
                        "-o", upath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["npx", "-y", MAPSHAPER, ppath, "-erase", upath,
                        "-o", gpath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        with open(gpath) as f:
            gap = json.load(f)

    parts = []
    for f in gap.get("features", []):
        for rings in _each_polygon(f.get("geometry")):
            a = _rings_area_m2(rings)
            per = _ring_perimeter_m(rings[0])
            pp = (4.0 * math.pi * a / (per * per)) if per else 0.0
            parts.append((a, pp))
    return parts, place_m2


def check_tiles_the_city(district_features, place_features):
    """Refuse if the five districts leave real city ground unrepresented.

    What survives the erase should be the seam between two independently drawn
    outlines -- many long thin perimeter fragments. ONE COMPACT PART BIG ENOUGH
    TO LIVE IN is a hole, and a reader standing in it would be told nothing at
    all rather than which district they are in.
    """
    parts, place_m2 = _residual(district_features, place_features)
    place_sqmi = place_m2 / 2.58999e6
    district_m2 = sum(_geom_area_m2(f["geometry"]) for f in district_features)
    ratio = district_m2 / place_m2 if place_m2 else 0.0

    if not (IDENTITY_RATIO_LO <= ratio <= IDENTITY_RATIO_HI):
        raise RuntimeError(
            "the districts under POLITICAL_TWP=%r cover %.3f sq mi against %s's "
            "%.3f sq mi — ratio %.5f, outside [%.2f, %.2f]. This build identifies "
            "the city BY AREA because the county publishes no name for the code; "
            "a ratio this far out means the code no longer means this city."
            % (CITY_TWP, district_m2 / 2.58999e6, CITY_NAME, place_sqmi, ratio,
               IDENTITY_RATIO_LO, IDENTITY_RATIO_HI))

    total_m2 = sum(a for a, _ in parts)
    total_sqmi = total_m2 / 2.58999e6
    largest = max((a for a, _ in parts), default=0.0)
    compact = [(a, pp) for a, pp in parts
               if a >= COMPACTNESS_MIN_AREA_M2 and pp > UNCOVERED_COMPACTNESS_CEILING]

    if compact:
        worst_a, worst_pp = max(compact, key=lambda t: t[0])
        raise RuntimeError(
            "%d uncovered fragment(s) are COMPACT and bigger than %.0f m2 (the "
            "largest %.0f m2 at Polsby-Popper %.3f, ceiling %.2f). A long thin "
            "fragment is two outlines digitised apart; a compact one this size is "
            "a HOLE -- ground inside the city that no district claims, where the "
            "card would answer nothing. Find where it is before shipping."
            % (len(compact), COMPACTNESS_MIN_AREA_M2, worst_a, worst_pp,
               UNCOVERED_COMPACTNESS_CEILING))
    if total_sqmi > UNCOVERED_CEILING_SQMI or largest > UNCOVERED_LARGEST_CEILING_M2:
        raise RuntimeError(
            "the five districts leave %.4f sq mi of %s uncovered in %d parts, the "
            "largest %.0f m2 (ceilings %.2f sq mi / %.0f m2). Every fragment is "
            "thin, so this is seam and not a hole -- but it has grown well past "
            "what was measured, which means the county's outline and the Census's "
            "have moved apart and both need re-reading."
            % (total_sqmi, CITY_NAME, len(parts), largest,
               UNCOVERED_CEILING_SQMI, UNCOVERED_LARGEST_CEILING_M2))

    med = sorted(pp for _, pp in parts)[len(parts) // 2] if parts else 0.0
    print("  tiling gate: POLITICAL_TWP=%s's 5 districts cover %s's %.2f sq mi to "
          "within %.4f sq mi (%.4f%%) in %d fragments, largest %.0f m2, median "
          "compactness %.4f, none compact above %.0f m2; area ratio %.5f"
          % (CITY_TWP, CITY_NAME, place_sqmi, total_sqmi,
             100.0 * total_sqmi / max(place_sqmi, 1e-9), len(parts), largest, med,
             COMPACTNESS_MIN_AREA_M2, ratio), file=sys.stderr)


def check_cross_control(place_features):
    """Prove POLITICAL_TWP=27 means Cedar Rapids by showing 21 does not.

    THE GATE ABOVE ALONE IS NOT AN IDENTITY TEST. It asks whether the polygons
    under one opaque code happen to cover Cedar Rapids, and it would pass just
    as happily for a code covering the whole county. This asks the other half:
    the code this build does NOT use must fail to cover the city, badly.

    Marion's four wards leave 99.996% of Cedar Rapids uncovered. If the county
    ever swaps the codes, THAT number collapses and this gate fires -- which is
    the only automated warning available for a key with no name attached.
    """
    control = fetch_districts(CONTROL_TWP, CONTROL_DISTRICTS, CONTROL_CITY)
    built = [{"type": "Feature", "properties": {}, "geometry": f["geometry"]}
             for f in control]
    parts, place_m2 = _residual(built, place_features)
    resid_pct = 100.0 * sum(a for a, _ in parts) / place_m2 if place_m2 else 0.0
    if resid_pct < CONTROL_RESIDUAL_MIN_PCT:
        raise RuntimeError(
            "CROSS-CONTROL FAILED: POLITICAL_TWP=%r (%s's %d wards) covers %.3f%% "
            "of %s, leaving only %.3f%% uncovered — the two codes are no longer "
            "telling the two cities apart. Nothing ships until the county's coding "
            "is re-read, because a swap here would put %s's districts on %s "
            "readers' cards under %s labels."
            % (CONTROL_TWP, CONTROL_CITY, len(CONTROL_DISTRICTS),
               100.0 - resid_pct, CITY_NAME, resid_pct, CONTROL_CITY, CITY_NAME,
               CITY_NAME))
    print("  cross-control: POLITICAL_TWP=%s (%s) leaves %.3f%% of %s uncovered, so "
          "the codes still distinguish the two cities"
          % (CONTROL_TWP, CONTROL_CITY, resid_pct, CITY_NAME), file=sys.stderr)


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
    """Sample the DISTRICTS' OWN envelope, not the state's.

    Over a state envelope virtually every sample would land outside all five
    districts, both models would answer "none", and a 99.5% gate would pass on
    a layer simplified into nothing.
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
        return False, ("simplification ADDED overlap: %d/%d points fall in >1 district "
                       "against the source's own %d" % (new_over, samples, src_over))
    if src_over > samples * SOURCE_OVERLAP_CEILING:
        return False, ("the source places %d/%d points in two districts at once "
                       "(ceiling %.0f); measure the overlap's SHAPE before raising "
                       "anything" % (src_over, samples, samples * SOURCE_OVERLAP_CEILING))
    if inside < samples * 0.25:
        return False, ("only %d/%d sample points fell inside any district — the "
                       "envelope is not exercising the boundaries" % (inside, samples))
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, ("%d/%d (%.2f%%) agreement over the city envelope, %d inside a "
                  "district; overlap %d in the source and %d after simplifying"
                  % (agree, samples, pct, inside, src_over, new_over))


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    raw = fetch_districts(CITY_TWP, EXPECT_DISTRICTS, CITY_NAME)
    print("fetched %d council districts from Linn County (POLITICAL_TWP=%s)"
          % (len(raw), CITY_TWP), file=sys.stderr)
    report_vintage()
    built = build_properties(raw)
    for f in built:
        print("  %-12s %6.2f sq mi" % (f["properties"]["label"],
                                       f["properties"]["sqmiles"]), file=sys.stderr)

    place = fetch_place(CITY_NAME)
    check_tiles_the_city(built, place)
    check_cross_control(place)

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

    # No `disclaimer` key: the service's copyrightText and serviceDescription
    # are both empty and Linn's page states no condition on reuse, so no notice
    # ships. Des Moines requires one; the card renders that row only when the
    # key is present. This absence was looked for, not overlooked.
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
    print("wrote data/app/%s — %d districts, %.1f KB (simplify %s)"
          % (OUT_NAME, n, len(payload) / 1024.0, SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

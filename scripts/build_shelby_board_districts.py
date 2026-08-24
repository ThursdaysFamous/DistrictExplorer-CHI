#!/usr/bin/env python3
"""
Build data/app/shelby-county-board-districts.json — Shelby's 11 County Board
districts, DERIVED by dissolving the Census 2020 voting districts (the
county's own precinct fabric) per the composition the county publishes, with
ONE precinct cut three ways along the two landmarks the county names.

WHY THIS EXISTS — Shelby publishes no board-district GIS. Its adopted plan is
a county-wide VECTOR PDF (ShelbyCoIL_CountyBoardDistricts.pdf, produced by
Bruce Harris & Associates, November 2021, filed under County Clerk > Election
Information on shelbycounty-il.gov), and shapefiles are purchasable from the
county's GIS vendor — an option recorded in docs/DATA_LAYER_GUIDEBOOK.md and
unnecessary, because the free adopted map plus public Census geometry
reproduce the plan exactly, as the checks below prove.

WHAT MAKES THE DERIVATION SOUND — three independent sources agree:

  1. TIGER's Census 2020 voting districts for Shelby carry EXACTLY the
     adopted map's 33 precincts — 33/33 by name, 31/33 by population to the
     person. The two exceptions are each other's inverse (Shelbyville 4 is
     +16 where Shelbyville 5 is -16 against the map's printed figures): the
     county's 2021 plan moved one ~16-person sliver on that single shared
     edge relative to the census snapshot. That sliver is DISCLOSED on the
     two affected districts' cards, not silently absorbed.
  2. The map prints every district's population, and the eleven totals sum
     to 20,990 — the county's exact 2020 census population — so a
     mis-transcription of the composition cannot balance.
  3. The county states the composition in WORDS on its County Board page
     (COBOARD_URL below), including the one split precinct's three pieces:
     District 8 takes "S5 (S of Rt 16)", District 9 "S5 (N of Rt 16 - E of
     Lake Shelbyville)", District 10 "S5 (N of Rt 16 - W of Lake
     Shelbyville)". The weekly roster job re-reads that page, so a
     redistricting fails CI instead of going unnoticed.

THE SPLIT — Shelbyville 5 wraps around the city of Shelbyville, and the
county divides it by two named landmarks, both of which exist as public
geometry:

  * The Rt 16 corridor (TIGER secondary roads: "State Rte 16" plus its
    in-town continuation "W Main St"/"E Main St") crosses the whole precinct
    east-west. South of it is District 8's piece.
  * Lake Shelbyville (TIGER areal hydrography) splits the northern remainder:
    east of the lake is District 9's, west is District 10's. Below the lake's
    southern tip the divider follows the Kaskaskia River (TIGER linear
    hydrography) through the dam reach; TIGER maps no linear river through
    the dam pool itself, so the last ~1 km is bridged straight to the lake —
    an approximation that crosses zero populated census blocks and is
    disclosed on both districts' cards.

THE ADJUDICATION — the cut is verified at CENSUS BLOCK level, not by eye.
Shelby's 2,605 blocks sum to the county's exact population; the 86 blocks
inside Shelbyville 5 sum to its exact VTD population; and the three pieces'
block sums are asserted EXACTLY (605 / 158 / 55, the census-frame values
whose whole-district totals reproduce the map's printed 1,948 and 1,833 for
Districts 9 and 10 to the person, and 1,925 - 16 for District 8 — the same
16-person Shelbyville 4/5 sliver, conserved: shipped D8+D9+D10+D11 equals
the map's printed total for those four districts). One block is the sharpest
pin: the only populated block in the dam reach (GEOID 171739593005007,
population 1) must land WEST of the divider — the county's own arithmetic
requires it, because 55 = 54 + 1.

Regenerate when the county re-precincts or reapportions (next due after the
2030 census); the guards fail loudly if the 33-precinct fabric or any
population moves.

Usage:
    python3 scripts/build_shelby_board_districts.py
    python3 scripts/build_shelby_board_districts.py --check
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Migrated onto vtd_board_districts by the 2026-08-24 scripts audit (the same
# follow-up the module's preamble named for Clark); --check is a byte compare,
# so the migration is proven. Everything Shelby-specific — the corridor split,
# the block adjudication, norm()'s whitespace-only collapse (V.norm strips all
# punctuation, which would change sort keys here) — stays local.
import vtd_board_districts as V  # noqa: E402  (shared machinery — do not fork)
from build_metro_outline import point_in_rings  # noqa: E402  (shared machinery — do not fork)
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "data", "app", "shelby-county-board-districts.json")
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "shelby-precincts.json")

COBOARD_URL = "https://www.shelbycounty-il.gov/coboard.aspx"
MAP_SOURCE = ("ShelbyCoIL_CountyBoardDistricts.pdf — the county's adopted 2021 plan "
              "(Bruce Harris & Associates, November 2021), County Clerk > Election "
              "Information, shelbycounty-il.gov")
SOURCE_LABEL = ("composed from Census 2020 voting districts per the district "
                "composition the county publishes on its County Board page and "
                "its adopted 2021 plan map")

TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
VTD_URL = TIGERWEB + "/tigerWMS_Census2020/MapServer/58/query"     # Voting Districts
BLOCKS_URL = TIGERWEB + "/tigerWMS_Census2020/MapServer/10/query"  # Census Blocks
ROADS_URL = TIGERWEB + "/Transportation/MapServer/6/query"         # Secondary Roads
HYDRO_LINE_URL = TIGERWEB + "/Hydro/MapServer/0/query"             # Linear hydrography
HYDRO_AREA_URL = TIGERWEB + "/Hydro/MapServer/1/query"             # Areal hydrography
STATE_FIPS = "17"
COUNTY_FIPS = "173"

# The composition exactly as the county states it on COBOARD_URL, cross-checked
# against the adopted map. A tuple marks a piece of the one split precinct; the
# second element is the county's own wording for that piece.
S5 = "SHELBYVILLE 5"
SIDE_SOUTH = "S of Rt 16"
SIDE_NE = "N of Rt 16 - E of Lake Shelbyville"
SIDE_NW = "N of Rt 16 - W of Lake Shelbyville"
COMPOSITION = {
    "1": ["MOWEAQUA 1", "MOWEAQUA 2"],
    "2": ["FLAT BRANCH", "PENN", "PICKAWAY", "RURAL", "TOWER HILL"],
    "3": ["ROSE 1", "ROSE 2"],
    "4": ["CLARKSBURG", "COLD SPRING", "LAKEWOOD", "OCONEE"],
    "5": ["DRY POINT", "HERRICK", "HOLLAND"],
    "6": ["PRAIRIE 1", "SIGEL"],
    "7": ["ASH GROVE", "BIG SPRING", "WINDSOR 1"],
    "8": ["RICHLAND", "WINDSOR 2", (S5, SIDE_SOUTH)],
    "9": ["OKAW", "RIDGE", "TODDS POINT", (S5, SIDE_NE)],
    "10": ["SHELBYVILLE 2", "SHELBYVILLE 6", "SHELBYVILLE 7", (S5, SIDE_NW)],
    "11": ["SHELBYVILLE 1", "SHELBYVILLE 3", "SHELBYVILLE 4"],
}
EXPECT_PRECINCTS = 33

# The adopted map's printed district populations. They sum to 20,990 — Shelby's
# exact 2020 census population — which is what makes them a checksum.
MAP_POP = {"1": 1931, "2": 1932, "3": 1947, "4": 1923, "5": 1864, "6": 1938,
           "7": 1929, "8": 1925, "9": 1948, "10": 1833, "11": 1820}
COUNTY_POP_2020 = 20990

# The Shelbyville 4/5 sliver: census geometry gives Shelbyville 4 sixteen
# people the adopted plan moves to Shelbyville 5. S4 is in District 11 and
# S5's affected piece is District 8's, so on census fabric D11 reads +16 and
# D8 reads -16 against the map. Frozen 2020 values; they can never drift.
SLIVER = 16
SLIVER_HIGH = "11"   # ships MAP_POP + SLIVER
SLIVER_LOW = "8"     # ships MAP_POP - SLIVER

# Block-level piece populations on census fabric (see THE ADJUDICATION above).
S5_POP = 818
PIECE_POP = {SIDE_SOUTH: 605, SIDE_NE: 158, SIDE_NW: 55}
# The one populated block in the dam reach; the county's 55 = 54 + 1 puts it west.
DAM_REACH_BLOCK = "171739593005007"
DAM_REACH_BLOCK_SIDE = SIDE_NW

# --- split instruments ------------------------------------------------------
# Fetch envelopes (WGS84 lon/lat), generous around Shelbyville so the corridor
# line always crosses clean out of the precinct on both sides.
CORRIDOR_NAMES = ("State Rte 16", "W Main St", "E Main St")
CORRIDOR_ENVELOPE = (-88.96, 39.35, -88.53, 39.46)
LAKE_NAME = "Lk Shelbyville"
RIVER_NAME = "Kaskaskia Riv"
RIVER_ENVELOPE = (-88.86, 39.30, -88.75, 39.41)
# Corridor sampling: the median of the strand crossings every ~43 m. Through
# downtown TIGER carries Rt 16 twice (the route and its Main St name), so the
# median rides between near-identical strands instead of picking one.
SAMPLE_STEP_DEG = 0.0005
CORRIDOR_X_RANGE = (-88.90, -88.60)   # must be gap-free across this window
DIVIDER_Y_START = 39.4000             # south of the corridor, so the cut enters
DIVIDER_Y_END = 39.4420               # north of the precinct, so the cut exits
# The river's mapped end must sit by the dam, close under the lake's tip —
# anything farther means TIGER renamed the reach and the bridge would be a guess.
MAX_BRIDGE_KM = 2.0

COORD_PRECISION = 6
LAT = 39.41                              # for degrees->metres at Shelby
# Districts vs the 33-VTD union, both at shipped precision. Not zero: where
# the cut lines meet the precinct edge, rounding moves the junction vertex up
# to ~11 cm off the edge, leaving hairline triangles measured at 2.4 m2 across
# all six junctions — roadway and water, three orders below anything a reader
# could click. Ten means the cut drifted, not the rounding.
MAX_TILING_SYMDIFF_M2 = 10.0
MAX_ROUNDED_OVERLAP_M2 = 5.0             # what COORD_PRECISION can re-create
# The shipped coverage outline is a simplified TIGER county boundary of an
# older vintage; the VTD union differs from it by a hairline band measured at
# 0.059% of the county in 2026. 4x that means a changed source, not noise.
OUTLINE_PATH = os.path.join(REPO_ROOT, "data", "app", "shelby-county-outline.json")
MAX_OUTLINE_SYMDIFF_PCT = 0.25

BOUNDARY_NOTES = {
    "8": ("This district includes Shelbyville 5 south of the Rt 16 corridor "
          "(Main Street through Shelbyville); the line follows the mapped "
          "road. On census geometry this district also reads 16 people fewer "
          "than the county's adopted plan prints: the plan moved a ~16-person "
          "sliver on the Shelbyville 4/5 edge shared with District 11."),
    "9": ("This district includes Shelbyville 5 north of Rt 16 and east of "
          "Lake Shelbyville. Below the lake's southern tip the line follows "
          "the Kaskaskia River, bridged straight through the dam reach where "
          "no linear river is mapped — an approximation that crosses no "
          "populated census block."),
    "10": ("This district includes Shelbyville 5 north of Rt 16 and west of "
           "Lake Shelbyville. Below the lake's southern tip the line follows "
           "the Kaskaskia River, bridged straight through the dam reach where "
           "no linear river is mapped — an approximation that crosses no "
           "populated census block."),
    "11": ("On census geometry this district reads 16 people more than the "
           "county's adopted plan prints: the plan moved a ~16-person sliver "
           "on the Shelbyville 4/5 edge shared with District 8."),
}


fail = make_fail("shelby-board")
title_case = V.title_case


def norm(name):
    return " ".join(str(name or "").upper().split())


def get_json(url, params):
    return V.get_json(url, params, fail)


def envelope_params(env):
    return {
        "geometry": "%s,%s,%s,%s" % env,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
    }


def fetch_vtds():
    data = get_json(VTD_URL, {
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
        "outFields": "GEOID,BASENAME,POP100", "returnGeometry": "true",
        "outSR": "4326", "f": "geojson",
    })
    feats = data.get("features") or []
    if len(feats) != EXPECT_PRECINCTS:
        fail("the Census voting-district layer carries %d Shelby precincts, "
             "expected %d — the fabric changed; re-read the county's plan "
             "before rebuilding" % (len(feats), EXPECT_PRECINCTS))
    return feats


def fetch_blocks():
    rows, offset = [], 0
    while True:
        data = get_json(BLOCKS_URL, {
            "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
            "outFields": "GEOID,POP100,INTPTLAT,INTPTLON", "returnGeometry": "false",
            "resultOffset": str(offset), "resultRecordCount": "2000", "f": "json",
        })
        feats = data.get("features") or []
        rows.extend(f["attributes"] for f in feats)
        if not data.get("exceededTransferLimit") and len(feats) < 2000:
            break
        offset += len(feats)
    total = sum(int(r["POP100"]) for r in rows)
    if total != COUNTY_POP_2020:
        fail("Shelby's census blocks sum to %d people, expected %d — the block "
             "fetch is incomplete or the layer changed" % (total, COUNTY_POP_2020))
    return rows


def fetch_lines(url, where, env):
    params = {"where": where, "outFields": "NAME", "returnGeometry": "true",
              "outSR": "4326", "f": "geojson"}
    params.update(envelope_params(env))
    return [f for f in (get_json(url, params).get("features") or [])]


def fetch_corridor():
    where = "NAME IN (%s)" % ",".join("'%s'" % n for n in CORRIDOR_NAMES)
    feats = fetch_lines(ROADS_URL, where, CORRIDOR_ENVELOPE)
    if not feats:
        fail("no Rt 16 corridor segments came back from the secondary-roads layer")
    return feats


def fetch_lake():
    params = {"where": "NAME='%s'" % LAKE_NAME, "outFields": "NAME",
              "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
    feats = get_json(HYDRO_AREA_URL, params).get("features") or []
    if not feats:
        fail("the areal-hydrography layer no longer carries %r" % LAKE_NAME)
    return feats


def fetch_river():
    feats = fetch_lines(HYDRO_LINE_URL, "NAME='%s'" % RIVER_NAME, RIVER_ENVELOPE)
    if not feats:
        fail("the linear-hydrography layer no longer carries %r by the dam" % RIVER_NAME)
    return feats


def vline_ys(geom, x):
    """Latitudes where the vertical line at x crosses a line geometry."""
    from shapely.geometry import LineString
    inter = geom.intersection(LineString([(x, 39.0), (x, 39.7)]))
    ys = []
    for g in ([] if inter.is_empty else getattr(inter, "geoms", [inter])):
        if g.geom_type == "Point":
            ys.append(g.y)
        elif g.geom_type == "LineString":
            ys.extend(c[1] for c in g.coords)
    return ys


def hline_intervals(poly, y):
    """West-to-east intervals where the horizontal line at y crosses a polygon."""
    from shapely.geometry import LineString
    inter = poly.intersection(LineString([(-89.1, y), (-88.4, y)]))
    out = []
    for g in ([] if inter.is_empty else getattr(inter, "geoms", [inter])):
        if g.geom_type == "LineString":
            xs = [c[0] for c in g.coords]
            out.append((min(xs), max(xs)))
    return sorted(out)


def build_corridor(road_feats):
    """One clean west-east polyline: the median of the strand crossings."""
    from shapely.geometry import LineString, shape
    from shapely.ops import unary_union
    roads = unary_union([shape(f["geometry"]) for f in road_feats])
    pts, x = [], CORRIDOR_ENVELOPE[0]
    while x <= CORRIDOR_ENVELOPE[2]:
        ys = sorted(vline_ys(roads, x))
        if ys:
            pts.append((x, ys[len(ys) // 2]))
        x += SAMPLE_STEP_DEG
    xs = [p[0] for p in pts]
    lo, hi = CORRIDOR_X_RANGE
    window = [p for p in pts if lo <= p[0] <= hi]
    if not window or min(xs) > lo or max(xs) < hi:
        fail("the Rt 16 corridor no longer spans %.2f..%.2f — a segment "
             "renamed or the route moved; re-check CORRIDOR_NAMES" % (lo, hi))
    for a, b in zip(window, window[1:]):
        if b[0] - a[0] > SAMPLE_STEP_DEG * 1.5:
            fail("the Rt 16 corridor has a gap between x=%.4f and x=%.4f — "
                 "a renamed segment would cut the precinct wrongly" % (a[0], b[0]))
    return LineString(pts)


def build_divider(lake_feats, river_feats):
    """South-to-north cut: river stub, dam-reach bridge, lake centerline."""
    from shapely.geometry import LineString, shape
    from shapely.ops import unary_union
    lake = max((shape(f["geometry"]).buffer(0) for f in lake_feats), key=lambda g: g.area)
    river = unary_union([shape(f["geometry"]) for f in river_feats])
    river_top = max((c for g in getattr(river, "geoms", [river]) for c in g.coords),
                    key=lambda c: c[1])
    lake_tip = min(lake.exterior.coords, key=lambda c: c[1])
    bridge_km = math.hypot((river_top[0] - lake_tip[0]) * 111.32 * math.cos(math.radians(LAT)),
                           (river_top[1] - lake_tip[1]) * 111.32)
    if bridge_km > MAX_BRIDGE_KM:
        fail("the dam-reach bridge would be %.1f km (max %.1f) — TIGER's river "
             "or lake changed shape; re-derive the divider" % (bridge_km, MAX_BRIDGE_KM))
    pts = [(river_top[0], DIVIDER_Y_START), (lake_tip[0], lake_tip[1])]
    prev_x, y = lake_tip[0], lake_tip[1] + SAMPLE_STEP_DEG
    while y <= DIVIDER_Y_END:
        ivs = hline_intervals(lake, y)
        if ivs:
            # follow the channel nearest the previous midpoint, so a side arm
            # never yanks the centerline off the main body
            best = min(ivs, key=lambda iv: abs((iv[0] + iv[1]) / 2 - prev_x))
            mid = (best[0] + best[1]) / 2
            pts.append((mid, y))
            prev_x = mid
        y += SAMPLE_STEP_DEG
    if pts[-1][1] < DIVIDER_Y_END - 0.005:
        fail("the lake centerline stops at y=%.4f, short of %.4f — the divider "
             "would not exit the precinct" % (pts[-1][1], DIVIDER_Y_END))
    return LineString(pts), lake, bridge_km


def split_s5(s5_geom, corridor, divider):
    """Cut Shelbyville 5 into its three county-named pieces."""
    from shapely.ops import split as shp_split, unary_union
    south_parts, north_parts = [], []
    for part in shp_split(s5_geom, corridor).geoms:
        rp = part.representative_point()
        ys = vline_ys(corridor, rp.x)
        if not ys:
            fail("a corridor-cut piece sits where the corridor has no crossing")
        (south_parts if rp.y < min(ys) else north_parts).append(part)
    if not south_parts or not north_parts:
        fail("the corridor cut left one side of Shelbyville 5 empty")
    south = unary_union(south_parts)
    north = unary_union(north_parts)

    div_coords = list(divider.coords)
    west_parts, east_parts = [], []
    for part in shp_split(north, divider).geoms:
        rp = part.representative_point()
        near = min(div_coords, key=lambda c: abs(c[1] - rp.y))
        (west_parts if rp.x < near[0] else east_parts).append(part)
    if not west_parts or not east_parts:
        fail("the lake divider left one side of northern Shelbyville 5 empty")
    pieces = {SIDE_SOUTH: south,
              SIDE_NW: unary_union(west_parts),
              SIDE_NE: unary_union(east_parts)}
    lost = abs(sum(p.area for p in pieces.values()) - s5_geom.area) / s5_geom.area
    if lost > 1e-9:
        fail("cutting Shelbyville 5 lost %.3g of its area" % lost)
    return pieces


def adjudicate(pieces, s5_geom, blocks):
    """Assert the cut reproduces the county's own arithmetic, block by block."""
    from shapely.geometry import Point
    inside = [b for b in blocks
              if s5_geom.contains(Point(float(b["INTPTLON"]), float(b["INTPTLAT"])))]
    got = sum(int(b["POP100"]) for b in inside)
    if got != S5_POP:
        fail("blocks inside Shelbyville 5 sum to %d people, expected %d" % (got, S5_POP))
    sums = dict.fromkeys(PIECE_POP, 0)
    for b in inside:
        pt = Point(float(b["INTPTLON"]), float(b["INTPTLAT"]))
        side = next((s for s, g in pieces.items() if g.contains(pt)), None)
        if side is None:
            fail("block %s (pop %d) falls in no piece of the cut"
                 % (b["GEOID"], b["POP100"]))
        sums[side] += int(b["POP100"])
        if b["GEOID"] == DAM_REACH_BLOCK and side != DAM_REACH_BLOCK_SIDE:
            fail("the dam-reach block %s landed %r, but the county's 55 = 54 + 1 "
                 "puts it %r — the divider drifted through the one place it "
                 "cannot" % (DAM_REACH_BLOCK, side, DAM_REACH_BLOCK_SIDE))
    for side, want in PIECE_POP.items():
        if sums[side] != want:
            fail("the %r piece holds %d people, the county's arithmetic says %d"
                 % (side, sums[side], want))
    return sums


def round_geom(geom):
    from shapely.geometry import mapping
    return V.round_geom(geom, mapping)


rings_of = V.rings_of


def main():
    # Heavy imports stay on the path that needs them: the ROSTER builder
    # imports this module's composition constants, and its CI job installs
    # no geometry stack (the DeWitt convention).
    from shapely.geometry import shape
    from shapely.ops import unary_union
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--check", action="store_true",
                    help="rebuild in memory and fail on drift; writes nothing")
    args = ap.parse_args()

    # ---- check 1: the composition is a partition, before any network call
    whole_names, split_sides = [], []
    for names in COMPOSITION.values():
        for member in names:
            if isinstance(member, tuple):
                split_sides.append(member[1])
                if member[0] != S5:
                    fail("only %s is split; the composition marks %r" % (S5, member[0]))
            else:
                whole_names.append(norm(member))
    if len(whole_names) != len(set(whole_names)):
        dupes = sorted({n for n in whole_names if whole_names.count(n) > 1})
        fail("the composition names these precincts more than once: %s" % ", ".join(dupes))
    if sorted(split_sides) != sorted(PIECE_POP):
        fail("the split pieces named in the composition are %s, expected %s"
             % (sorted(split_sides), sorted(PIECE_POP)))
    if len(whole_names) + 1 != EXPECT_PRECINCTS:
        fail("the composition covers %d precincts, the county runs %d"
             % (len(whole_names) + 1, EXPECT_PRECINCTS))
    if sum(MAP_POP.values()) != COUNTY_POP_2020:
        fail("the map's printed district totals sum to %d, not the county's %d"
             % (sum(MAP_POP.values()), COUNTY_POP_2020))

    # ---- fetch the fabric and the instruments
    vtd_feats = fetch_vtds()
    by_name, pop_of = {}, {}
    for f in vtd_feats:
        key = norm((f.get("properties") or {}).get("BASENAME"))
        if key in by_name:
            fail("the voting-district layer carries two features named %r" % key)
        geom = shape(f["geometry"])
        by_name[key] = geom if geom.is_valid else geom.buffer(0)
        pop_of[key] = int((f.get("properties") or {}).get("POP100") or 0)
    missing = sorted((set(whole_names) | {S5}) - set(by_name))
    if missing:
        fail("the composition names precincts the layer does not have: %s"
             % ", ".join(missing))
    unassigned = sorted(set(by_name) - set(whole_names) - {S5})
    if unassigned:
        fail("the layer has precincts no district claims: %s" % ", ".join(unassigned))
    if pop_of[S5] != S5_POP:
        fail("Shelbyville 5 carries %d people in the layer, expected %d"
             % (pop_of[S5], S5_POP))

    corridor = build_corridor(fetch_corridor())
    divider, lake, bridge_km = build_divider(fetch_lake(), fetch_river())
    pieces = split_s5(by_name[S5], corridor, divider)
    piece_sums = adjudicate(pieces, by_name[S5], fetch_blocks())

    # ---- dissolve, with the map's printed totals as the checksum
    features = []
    shipped_pop = {}
    for district in sorted(COMPOSITION, key=int):
        parts, labels, pop = [], [], 0
        for member in COMPOSITION[district]:
            if isinstance(member, tuple):
                parts.append(pieces[member[1]])
                labels.append("%s (%s)" % (title_case(member[0]), member[1]))
                pop += piece_sums[member[1]]
            else:
                parts.append(by_name[norm(member)])
                labels.append(title_case(member))
                pop += pop_of[norm(member)]
        merged = unary_union(parts)
        if merged.is_empty:
            fail("district %s dissolved to an empty geometry" % district)
        want = MAP_POP[district]
        if district == SLIVER_HIGH:
            want += SLIVER
        elif district == SLIVER_LOW:
            want -= SLIVER
        if pop != want:
            fail("district %s holds %d people on census fabric, expected %d "
                 "(map %d%s)" % (district, pop, want, MAP_POP[district],
                                 "" if want == MAP_POP[district] else
                                 " with the Shelbyville 4/5 sliver"))
        shipped_pop[district] = pop
        props = {"district": district, "name": "District %s" % district,
                 "precincts": labels, "pop2020": pop, "mapPop2020": MAP_POP[district]}
        if district in BOUNDARY_NOTES:
            props["boundaryNote"] = BOUNDARY_NOTES[district]
        features.append({"type": "Feature", "properties": props,
                         "geometry": round_geom(merged if merged.is_valid
                                                else merged.buffer(0))})
    if sum(shipped_pop.values()) != COUNTY_POP_2020:
        fail("the eleven districts sum to %d people, not the county's %d"
             % (sum(shipped_pop.values()), COUNTY_POP_2020))

    # ---- the shipped file must tile the fabric it came from. The comparison
    # union is rounded the same way the shipped features are, so the test
    # measures the dissolve, not the rounding (unrounded it reads ~6 m2 of
    # hairline triangles along the county perimeter).
    metres2 = (111320.0 * math.cos(math.radians(LAT))) * 111320.0
    county = unary_union([shape(round_geom(g)).buffer(0) for g in by_name.values()])
    shipped = [(f["properties"]["district"], shape(f["geometry"]).buffer(0))
               for f in features]
    tiled = unary_union([g for _, g in shipped])
    symdiff_m2 = county.symmetric_difference(tiled).area * metres2
    if symdiff_m2 > MAX_TILING_SYMDIFF_M2:
        fail("the districts differ from the 33-precinct union by %.1f m2 "
             "(max %.1f)" % (symdiff_m2, MAX_TILING_SYMDIFF_M2))
    worst, worst_pair = 0.0, None
    for i in range(len(shipped)):
        for j in range(i + 1, len(shipped)):
            area = shipped[i][1].intersection(shipped[j][1]).area * metres2
            if area > worst:
                worst, worst_pair = area, (shipped[i][0], shipped[j][0])
    if worst > MAX_ROUNDED_OVERLAP_M2:
        fail("after rounding, districts %s and %s overlap by %.1f m2 (max %.1f)"
             % (worst_pair[0], worst_pair[1], worst, MAX_ROUNDED_OVERLAP_M2))
    with open(OUTLINE_PATH) as handle:
        outline_gj = json.load(handle)
    outline = unary_union([shape(f["geometry"]) for f in outline_gj["features"]])
    outline_pct = tiled.symmetric_difference(outline).area / outline.area * 100
    if outline_pct > MAX_OUTLINE_SYMDIFF_PCT:
        fail("the districts differ from the shipped coverage outline by %.3f%% "
             "(max %.2f%%) — more than two vintages of the county border "
             "explain" % (outline_pct, MAX_OUTLINE_SYMDIFF_PCT))

    # ---- verify with the app's own even-odd test: every whole precinct's
    # interior point lands in exactly its own district, every piece in its
    for district in COMPOSITION:
        for member in COMPOSITION[district]:
            geom = (pieces[member[1]] if isinstance(member, tuple)
                    else by_name[norm(member)])
            probe = geom.representative_point()
            hits = [d for d, _ in shipped
                    for f in [next(f for f in features
                                   if f["properties"]["district"] == d)]
                    if point_in_rings(probe.y, probe.x, rings_of(f["geometry"]))]
            if hits != [district]:
                label = member[1] if isinstance(member, tuple) else member
                fail("precinct %s lands in %s, expected only district %s"
                     % (label, hits or "no district", district))

    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "rosterUrl": COBOARD_URL,
            "mapSource": MAP_SOURCE,
            "note": ("Shelby publishes no board-district GIS; these are the "
                     "Census 2020 voting districts — which match the county's "
                     "adopted 2021 plan 33/33 by name — dissolved per the "
                     "composition the county publishes, with Shelbyville 5 cut "
                     "along Rt 16 and Lake Shelbyville as the county describes. "
                     "Verified against the plan's printed populations at census-"
                     "block level."),
        },
        "features": features,
    }
    # ---- the precincts themselves -----------------------------------------
    # Shelby's 33 precincts ARE the Census 2020 voting districts: the adopted
    # map names all 33 and the layer carries them 33/33, which is what makes the
    # dissolve above legitimate in the first place. Nothing new is sourced here;
    # this absence simply had no gap record explaining it.
    #
    # SHELBYVILLE 5 SHIPS WHOLE AND CARRIES THREE DISTRICTS. The district
    # geometry above cuts it into three pieces along the two landmarks the
    # county names, but a PRECINCT is not cut — a voter in Shelbyville 5 is in
    # Shelbyville 5. Ships with the list of districts it spans, so the card says
    # which three it could be rather than picking the largest piece.
    whole_district = {}
    for district, names in COMPOSITION.items():
        for member in names:
            if not isinstance(member, tuple):
                whole_district[norm(member)] = district
    s5_districts = sorted((d for d, names in COMPOSITION.items()
                           if any(isinstance(m, tuple) for m in names)), key=int)
    if len(s5_districts) != len(PIECE_POP):
        fail("%s is cut across %d districts, expected %d"
             % (S5, len(s5_districts), len(PIECE_POP)))

    precinct_features = []
    for key in sorted(by_name):
        props = {"name": title_case(key), "pop2020": pop_of[key]}
        if key == S5:
            props["districts"] = s5_districts
        else:
            props["district"] = whole_district[key]
        precinct_features.append({"type": "Feature", "properties": props,
                                  "geometry": round_geom(by_name[key])})
    if len(precinct_features) != EXPECT_PRECINCTS:
        fail("built %d precincts, expected %d"
             % (len(precinct_features), EXPECT_PRECINCTS))
    if sum(f["properties"]["pop2020"] for f in precinct_features) != COUNTY_POP_2020:
        fail("the built precincts do not sum to the county's %d people"
             % COUNTY_POP_2020)

    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": payload["properties"].get("source"),
            "boardUrl": payload["properties"].get("boardUrl"),
            "mapUrl": payload["properties"].get("mapUrl"),
            "note": ("Shelby County's 33 voting precincts are the Census 2020 "
                     "voting districts, which carry the adopted County Board "
                     "map's own 33 precinct names 33/33 and sum to the county's "
                     "exact 2020 population of 20,990 — the same agreement that "
                     "lets the districts be dissolved from this fabric. "
                     "Thirty-two carry a single County Board district. "
                     "SHELBYVILLE 5 CARRIES THREE: it wraps around the city of "
                     "Shelbyville and the adopted plan divides it between "
                     "Districts 8, 9 and 10 along two landmarks the county "
                     "names. The precinct itself is not divided — it ships whole "
                     "and says which three districts it spans, because there the "
                     "precinct alone does not determine the district. No polling "
                     "place ships: a polling place is a roster fact rather than "
                     "geometry (the Calhoun rule)."),
        },
        "features": precinct_features,
    }
    prec_body = V.dumps(precincts_payload)

    body = V.dumps(payload)

    print("shelby-board: 11 districts dissolved from 33 precincts; "
          "Shelbyville 5 cut three ways (S %d / NE %d / NW %d people, exact)"
          % (piece_sums[SIDE_SOUTH], piece_sums[SIDE_NE], piece_sums[SIDE_NW]))
    print("  populations: %s (total %d = the county; nine districts match the "
          "adopted map to the person, D8/D11 carry the disclosed 16-person "
          "sliver)" % (", ".join("D%s=%d" % (d, shipped_pop[d])
                                 for d in sorted(shipped_pop, key=int)),
                       sum(shipped_pop.values())))
    print("  tiling: %.2f m2 symmetric difference vs the precinct union; worst "
          "rounded overlap %.2f m2; %.4f%% vs the coverage outline; dam-reach "
          "bridge %.2f km" % (symdiff_m2, worst, outline_pct, bridge_km))

    print("  precincts: %d shipped — 32 carrying one district, %s carrying the "
          "three it spans (%s)"
          % (len(precinct_features), title_case(S5), ", ".join(s5_districts)))

    outputs = [(OUT_PATH, body), (OUT_PRECINCTS, prec_body)]
    if args.check:
        for path, want in outputs:
            if not os.path.exists(path):
                fail("%s does not exist" % path)
            with open(path, encoding="utf-8") as f:
                if f.read() != want:
                    fail("%s differs from a fresh build" % path)
        print("  --check OK — matches a fresh build")
        return
    for path, want in outputs:
        with open(path, "w", encoding="utf-8") as f:
            f.write(want)
    print("  wrote %s"
          % ", ".join("%s (%s bytes)"
                      % (os.path.relpath(path, REPO_ROOT), "{:,}".format(len(want)))
                      for path, want in outputs))


if __name__ == "__main__":
    main()

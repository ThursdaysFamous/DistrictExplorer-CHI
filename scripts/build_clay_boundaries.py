#!/usr/bin/env python3
"""
Build data/app/clay-county-board-districts.json — Clay County's 14 lettered
County Board districts (one member each; docs/EXPANSION_GUIDE.md Part 2;
scripts/vtd_board_districts.py holds the shared machinery).

THE COMPOSITION IS THE COUNTY'S OWN, IN PLAIN HTML. claycounty.illinois.gov's
County Board page states it under a "Districts" heading, letter by letter:
A = Clay City I; B = Clay City II & Stanford; C = Xenia & Songer; D = Blair &
Bible Grove; E = Oskaloosa & Larkinsburg; F = Hoosier & Pixley; G-N one
precinct each (Louisville I-II, Harter I/V/IV/III/VI/VII). Its certified 2026
General Primary independently witnesses half the letters: seven single-member
district contests LETTERED B, C, D, G, I, K and N over 10 of the county's 18
precincts, none in two districts (ISBE's statewide certified CSV).

THE FABRIC HAS NOT MOVED — WITH ONE SPLIT THE COUNTY ITSELF DESCRIBES. Census
2020 carries 18 Clay voting districts summing to the county's exact 13,288,
and 17 of them match the county's names once two vestigial census suffixes
are aliased (census LARKINSBURG I / PIXLEY I; no II exists anywhere in any
source). The 18th is the county seat: the census carries ONE "CLAY CITY I"
(1,166 people) where the county's board page names Clay City I in District A
and Clay City II in District B. Nothing published said where that line runs
until Clerk Amy Britton answered directly (e-mail, 2026-08-24): "Clay City
Dist A is located within the Village limits of Clay City" and "Dist B is the
unincorporated area of Clay City/Stanford" — a corporate-limits line, not a
hand-drawn one, which the census can draw exactly.

THE SPLIT IS EXACT, AND THE BLOCKS PROVE IT. Intersecting the Village of Clay
City's own census place boundary (GEOID 1714715) with the CLAY CITY I voting
district at the BLOCK level: 108 blocks, matching the VTD's 1,166 people
exactly, and EVERY block sorts cleanly to one side (none straddles the
village line) — 55 blocks / 833 people inside the village (District A's
precinct), 53 blocks / 333 people outside (District B's, joining Stanford's
625). The shipped geometry is the village line itself, and this builder fails
if any block ever straddles it, if the counts move, or if the two halves stop
summing to the voting district.

ONE MEASURED MARGIN, RECORDED RATHER THAN ABSORBED: two census blocks
(...037 and ...069, 14 people together) sit inside the village limits but in
the STANFORD voting district, so they ship in District B with the rest of
their precinct. The Clerk's "within the Village limits" describes District
A's share of the Clay City precinct, not an annexation of Stanford territory
— precincts are the certified unit here, and the certified contests are
precinct-grouped. The census place boundary is also 2020-vintage; an
annexation since would not show.

WHY THIS WAS NOT BUILT FOR TWO DAYS AFTER THE SPLIT WAS SETTLED: POPULATION.
Against a 949-person ideal, District J (Harter V, one whole voting district)
runs 1,327 (+39.8%) and District L (Harter III) 1,265 (+33.3%), while
District H (Louisville II) runs 728 (-23.3%) — past the 30% ceiling this
project's dissolve guard uses everywhere else to catch a mis-assignment, and
the worst deviation the fleet has ever accepted. Every one of those is a
single, whole census voting district mapped to the county's own published
letter, so the imbalance is real rather than a derivation error. Clerk
Britton was asked directly whether the Harter and Louisville lines are the
board's current, adopted plan; her reply, 2026-08-26: "These are the current
maps" (sent beside the county's own board map and precinct reference PDFs).
BALANCE_DEV_MAX is raised for this county alone — the Wayne posture, measured
value recorded, ceiling not silently widened for the fleet.

NO PRECINCT FILE SHIPS, deliberately. The county's two surfaces disagree on
the precinct COUNT — its board page names 19 precinct-slots (Clay City twice)
while ISBE's certified 2026 returns list 18 with one Clay City — and the
Clerk's reply settles the district line without settling which count is the
current registration fabric. A precinct card that named either count would
overstate what is known; the board answer is complete without it.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Clay
reapportions, re-precincts, or TIGERweb republishes. Output is deterministic,
so --check is a byte compare.

Usage:
    python3 scripts/build_clay_boundaries.py [--check]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "clay-county-board-districts.json")

COUNTY_FIPS = "025"
COUNTY_POP_2020 = 13288
EXPECTED_VTDS = 18
SEATS_PER_DISTRICT = 1          # fourteen members, one per lettered district

BOARD_URL = "https://claycounty.illinois.gov/county-board/"
MEMBERS_URL = "https://claycounty.illinois.gov/county-board/members/"

BLOCKS_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
              "tigerWMS_Census2020/MapServer/10/query")
PLACES_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
              "tigerWMS_Census2020/MapServer/26/query")

SOURCE_LABEL = ("Census 2020 voting districts composed per Clay County's own "
                "County Board page, with the Clay City precinct split at the "
                "Village of Clay City's corporate limits as County Clerk Amy "
                "Britton described the line (e-mail, 2026-08-24), and the "
                "plan confirmed current by the Clerk (e-mail, 2026-08-26)")

# THE COMPOSITION, letter by letter as the county's own board page states it.
# "CLAY CITY I" and "CLAY CITY II" are the county's names for the two halves
# of the census's single CLAY CITY I voting district — village and
# unincorporated — split below at the village's own boundary.
COMPOSITION = {
    "A": ("CLAY CITY I",),
    "B": ("CLAY CITY II", "STANFORD"),
    "C": ("XENIA", "SONGER"),
    "D": ("BLAIR", "BIBLE GROVE"),
    "E": ("OSKALOOSA", "LARKINSBURG"),
    "F": ("HOOSIER", "PIXLEY"),
    "G": ("LOUISVILLE I",),
    "H": ("LOUISVILLE II",),
    "I": ("HARTER I",),
    "J": ("HARTER V",),
    "K": ("HARTER IV",),
    "L": ("HARTER III",),
    "M": ("HARTER VI",),
    "N": ("HARTER VII",),
}

# The census's two vestigial suffixes: it writes LARKINSBURG I and PIXLEY I
# where the county, ISBE's certified returns and the board page all write the
# bare name, and no II exists anywhere in any source.
ALIASES = {"LARKINSBURG": "LARKINSBURG I", "PIXLEY": "PIXLEY I"}

# The split, measured 2026-08-26 against TIGERweb's Census 2020 layers. Every
# number is a GATE below: if any moves, the census republished and the split
# needs re-deriving, not silently re-summing.
VILLAGE_PLACE_GEOID = "1714715"        # Village of Clay City
SPLIT_VTD = "CLAY CITY I"              # the census feature being split
SPLIT_VTD_POP = 1166
SPLIT_BLOCKS = 108
SPLIT_VILLAGE_POP = 833                # District A's precinct
SPLIT_OUTSIDE_POP = 333                # District B's Clay City II share
# Two blocks sit inside the village limits but in the STANFORD voting
# district (see the module docstring); they ship in District B with their
# precinct, and this asserts the margin stays exactly what was measured.
VILLAGE_BLOCKS_OUTSIDE_VTD = {"170259722001037": 7, "170259722001069": 7}

# Measured 0.398 in District J (Harter V, a single whole voting district) and
# 0.333 in District L (Harter III). Raised from this project's usual 0.30
# ceiling for Clay alone, and only after the Clerk confirmed the plan is
# current rather than stale (Clerk Britton, e-mail, 2026-08-26: "These are
# the current maps") — the Wayne posture. Left just above the measured worst
# so a real mis-assignment still fails loudly.
BALANCE_DEV_MAX = 0.399
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999
BLOCK_SIDE_MIN = 0.999                 # a block is IN the village above this…
BLOCK_SIDE_MAX = 0.001                 # …and OUT below this; between = straddle


fail = make_fail("clay-boundaries")


def fetch_village(shape_fn):
    data = V.get_json(PLACES_URL, {
        "where": "STATE='17' AND GEOID='%s'" % VILLAGE_PLACE_GEOID,
        "outFields": "GEOID,BASENAME,POP100", "returnGeometry": "true",
        "outSR": "4326", "f": "geojson"}, fail)
    feats = data.get("features") or []
    if len(feats) != 1:
        fail("expected exactly one census place for GEOID %s (Village of Clay "
             "City), got %d" % (VILLAGE_PLACE_GEOID, len(feats)))
    props = feats[0].get("properties") or {}
    if (props.get("BASENAME") or "").strip() != "Clay City":
        fail("place GEOID %s is named %r, expected 'Clay City' — the census "
             "re-keyed its places" % (VILLAGE_PLACE_GEOID, props.get("BASENAME")))
    geom = shape_fn(feats[0]["geometry"])
    return geom if geom.is_valid else geom.buffer(0)


def fetch_blocks_in(envelope_geom, shape_fn):
    minx, miny, maxx, maxy = envelope_geom.bounds
    data = V.get_json(BLOCKS_URL, {
        "where": "STATE='17' AND COUNTY='%s'" % COUNTY_FIPS,
        "geometry": json.dumps({"xmin": minx, "ymin": miny, "xmax": maxx,
                                "ymax": maxy, "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects", "inSR": "4326",
        "outFields": "GEOID,POP100", "returnGeometry": "true",
        "resultRecordCount": "2000", "outSR": "4326", "f": "geojson"}, fail)
    out = []
    for feature in data.get("features") or []:
        geom = shape_fn(feature["geometry"])
        props = feature.get("properties") or {}
        out.append((props.get("GEOID"), int(props.get("POP100") or 0),
                    geom if geom.is_valid else geom.buffer(0)))
    return out


def split_clay_city(vtds, shape_fn):
    """Replace the census CLAY CITY I record with the county's two precincts,
    CLAY CITY I (the village) and CLAY CITY II (unincorporated), split at the
    village's own boundary and gated block by block."""
    key = V.norm(SPLIT_VTD)
    if key not in vtds:
        fail("the census fabric carries no %r to split" % SPLIT_VTD)
    rec = vtds.pop(key)
    if rec["pop"] != SPLIT_VTD_POP:
        fail("%s carries %d people, measured %d — the census republished; "
             "re-derive the split" % (SPLIT_VTD, rec["pop"], SPLIT_VTD_POP))
    village = fetch_village(shape_fn)

    blocks = fetch_blocks_in(rec["geom"], shape_fn)
    inside = [(g, p, geom) for g, p, geom in blocks
              if geom.representative_point().within(rec["geom"])]
    if len(inside) != SPLIT_BLOCKS:
        fail("%d census blocks land inside %s, measured %d — the census "
             "republished; re-derive the split"
             % (len(inside), SPLIT_VTD, SPLIT_BLOCKS))
    if sum(p for _, p, _ in inside) != SPLIT_VTD_POP:
        fail("the blocks inside %s sum to %d people against the voting "
             "district's %d — the block instrument is broken"
             % (SPLIT_VTD, sum(p for _, p, _ in inside), SPLIT_VTD_POP))

    in_village, outside = [], []
    for geoid, pop, geom in inside:
        frac = (geom.intersection(village).area / geom.area) if geom.area else 0.0
        if frac > BLOCK_SIDE_MIN:
            in_village.append((geoid, pop, geom))
        elif frac < BLOCK_SIDE_MAX:
            outside.append((geoid, pop, geom))
        else:
            fail("census block %s straddles the village line (%.1f%% inside) — "
                 "the split is no longer clean and cannot ship as a "
                 "corporate-limits line" % (geoid, 100 * frac))
    pop_in = sum(p for _, p, _ in in_village)
    pop_out = sum(p for _, p, _ in outside)
    if (pop_in, pop_out) != (SPLIT_VILLAGE_POP, SPLIT_OUTSIDE_POP):
        fail("the split sums %d inside the village / %d outside, measured "
             "%d/%d — the census or the village boundary moved"
             % (pop_in, pop_out, SPLIT_VILLAGE_POP, SPLIT_OUTSIDE_POP))

    # The recorded margin: village blocks OUTSIDE this voting district.
    margin = {}
    for geoid, pop, geom in fetch_blocks_in(village, shape_fn):
        rp = geom.representative_point()
        frac = (geom.intersection(village).area / geom.area) if geom.area else 0.0
        if frac > 0.5 and not rp.within(rec["geom"]):
            margin[geoid] = pop
    if margin != VILLAGE_BLOCKS_OUTSIDE_VTD:
        fail("the village-limits blocks outside %s are %s, measured %s — the "
             "recorded 14-person Stanford margin moved; re-read the docstring "
             "before shipping" % (SPLIT_VTD, margin, VILLAGE_BLOCKS_OUTSIDE_VTD))

    part_a = rec["geom"].intersection(village)
    part_b = rec["geom"].difference(village)
    for name, part in (("A", part_a), ("B", part_b)):
        if part.is_empty or not part.is_valid:
            fail("the %s part of the split is empty or invalid" % name)
    lost = abs(rec["geom"].area - part_a.area - part_b.area) / rec["geom"].area
    if lost > 1e-6:
        fail("the two split parts lose %.6f%% of the voting district's area"
             % (100 * lost))
    for geoid, _, geom in in_village:
        if not geom.representative_point().within(part_a):
            fail("village block %s does not land in the village part — the "
                 "block instrument and the geometric split disagree" % geoid)
    for geoid, _, geom in outside:
        if not geom.representative_point().within(part_b):
            fail("outside block %s does not land in the unincorporated part — "
                 "the block instrument and the geometric split disagree" % geoid)

    vtds[V.norm("CLAY CITY I")] = {
        "geom": part_a, "geoid": rec["geoid"] + "-village",
        "pop": pop_in, "basename": "CLAY CITY I"}
    vtds[V.norm("CLAY CITY II")] = {
        "geom": part_b, "geoid": rec["geoid"] + "-unincorporated",
        "pop": pop_out, "basename": "CLAY CITY II"}
    return vtds


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    claimed = [n for names in COMPOSITION.values() for n in names]
    if len(claimed) != EXPECTED_VTDS + 1:
        fail("the composition names %d precinct-slots, expected %d (18 voting "
             "districts with Clay City split once)" % (len(claimed), EXPECTED_VTDS + 1))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    vtds = V.apply_aliases(vtds, ALIASES, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Clay features, "
             "expected %d" % (len(vtds), EXPECTED_VTDS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d" % (county_pop, COUNTY_POP_2020))
    V.check_fabric_composed(vtds, county_pop, fail)

    vtds = split_clay_city(vtds, shape)
    where = V.check_partition(COMPOSITION, vtds, fail)

    districts, pops = V.dissolve(COMPOSITION, vtds, unary_union)
    if sum(pops.values()) != county_pop:
        fail("the fourteen districts sum to %d people against the county's %d"
             % (sum(pops.values()), county_pop))
    ideal = county_pop / float(len(COMPOSITION))
    worst = max(((abs(pops[d] - ideal) / ideal), d) for d in pops)
    if worst[0] > BALANCE_DEV_MAX:
        fail("district %s deviates %.1f%% from the per-district ideal (ceiling "
             "%.1f%%) — that is a mis-assignment, not an apportionment"
             % (worst[1], 100 * worst[0], 100 * BALANCE_DEV_MAX))
    overlap, covered = V.check_tiling(districts, county_geom, transform,
                                      MAX_OVERLAP_M2, MIN_COVERED, unary_union, fail)

    district_features = []
    for letter in sorted(COMPOSITION):
        district_features.append({
            "type": "Feature",
            "properties": {"district": letter, "name": "District %s" % letter,
                           "precincts": [V.title_case(n) for n in COMPOSITION[letter]],
                           "pop2020": pops[letter], "seats": SEATS_PER_DISTRICT},
            "geometry": V.round_geom(districts[letter], mapping),
        })
    districts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "boardUrl": BOARD_URL, "membersUrl": MEMBERS_URL,
            "canvass": ("Composition from the county's own County Board page "
                        "(Districts section, letter by letter), independently "
                        "witnessed for seven letters by the county's certified "
                        "2026 General Primary, which ran single-member "
                        "district contests lettered B, C, D, G, I, K and N "
                        "over 10 of the 18 precincts with no precinct in two "
                        "districts (ISBE's certified statewide results)."),
            "note": ("Fourteen lettered districts electing ONE member each. "
                     "Clay City is split at the Village of Clay City's own "
                     "corporate limits, as the Clerk described the line "
                     "(2026-08-24): District A is the village (833 people), "
                     "District B the unincorporated remainder (333) plus "
                     "Stanford (625) — 108 census blocks, none straddling. "
                     "Two blocks inside the village limits (14 people) lie in "
                     "the Stanford voting district and ship in District B "
                     "with their precinct. Populations run 728-1,327 against "
                     "a 949 ideal — District J (Harter V) alone deviates "
                     "+39.8%, the fleet's largest accepted deviation. Clerk "
                     "Amy Britton confirmed the plan is current (e-mail, "
                     "2026-08-26): “These are the current maps.” The "
                     "imbalance is recorded as the county's own plan rather "
                     "than smoothed."),
        },
        "features": district_features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, district_features, point_in_rings, fail)

    dist_body = V.dumps(districts_payload)
    print("clay-boundaries: %d precinct-slots -> %d lettered districts of %d "
          "seat(s); Clay City split 833/333 at the village limits, 108 blocks, "
          "none straddling"
          % (len(claimed), len(COMPOSITION), SEATS_PER_DISTRICT))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s — confirmed the county's own current plan)"
          % (", ".join("%s=%d" % (d, pops[d]) for d in sorted(pops)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_DISTRICTS, dist_body)], args.check, REPO_ROOT, fail, "clay")


if __name__ == "__main__":
    main()

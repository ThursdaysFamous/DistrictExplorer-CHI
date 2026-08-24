#!/usr/bin/env python3
"""Build Menard County's fourteen voting precincts from Census 2020 voting districts.

WHY THIS COUNTY HAD NO PRECINCT LAYER. Menard has been served since its five
commissioner districts shipped — the county's OWN data, sent by the county. Nothing
was blocking its precincts either; there was simply no gap record saying they were
missing, which is how a county goes unbuilt while every guard in the repo stays
green. The 2026-08-20 audit that found eleven such counties is the reason this file
exists, and Menard is one of the last two of the eight it named.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 14/14 and
their POP100 sums to the county's 2020 population of 12,297 to the person. No
dissolve is needed and none is performed — each precinct IS one voting district.

TWO COUNTY SOURCES NAME THE SAME FOURTEEN, and neither is a canvass, which is worth
saying because the other seven counties in this batch were named by certified
returns. Menard is carried by no election-results platform this project has found —
il-menard.pollresults.net returns that vendor's 7,720-byte NotFound shell and GBS
does not list the county — so the names come from the Clerk's own publications
instead:

  1. THE COUNTY'S PRECINCT MAP (Precincts_for_website.pdf, linked from the County
     Clerk/Recorder page) is a VECTOR PDF WITH A TEXT LAYER — rare in this fleet,
     where a county's precinct map is almost always a scan — so its legend can be
     read as text rather than looked at. It lists all fourteen: East Menard, East
     Petersburg, Greenview, Indian Creek, North Athens City, North Athens Rural,
     North Petersburg, Northwest Menard, Rock Creek, South Athens City, South
     Athens Rural, South Petersburg, Southwest Menard, West Petersburg.
  2. THE CLERK'S POLLING-PLACE LIST numbers the same fourteen #1 through #14 and
     pairs them with seven buildings. It writes the Athens pairs with a slash —
     "#2 - South Athens/City" — where the map writes a space; the map's legend is
     the name list and the polling sheet is a building list, which is the
     distinction Cumberland's build had to learn the hard way.

THE SEPARATOR IS THE ONLY DIVERGENCE AND THE COUNTY WINS IT. The census hyphenates
NORTH ATHENS-CITY and SOUTH ATHENS-RURAL where the county's own map writes them
with a space. norm() absorbs that for the Jasper test, and the shipped features are
LABELLED from COUNTY_PRECINCTS rather than from the census basename, because a
county's own map is the authority on how it spells its own precinct.

NO BOARD DISTRICT IS CARRIED HERE. Menard's five commissioner districts ship
separately as menard-commissioner-districts.json, from the county's own file.

NO POLLING PLACE SHIPS. The county publishes a list and it belongs with a roster
guard and a date, which is the rule Calhoun's build set.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Menard
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_menard_precincts.py            # write
    python3 scripts/build_menard_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "menard-precincts.json")

COUNTY_FIPS = "129"
COUNTY_POP_2020 = 12297
EXPECTED_PRECINCTS = 14

CLERK_URL = "https://menardcountyil.gov/elected-officials/county-clerkrecorder/"
PRECINCT_MAP_URL = ("https://menardcountyil.gov/files/3514/4000/1134/"
                    "Precincts_for_website.pdf")
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "fourteen precinct names Menard County's own precinct map and "
                "polling-place list use")

# The county's fourteen precincts, spelled as its OWN PRECINCT MAP's legend spells
# them — with spaces, where the census hyphenates and the polling sheet uses a
# slash. This list IS the Jasper test's input AND the shipped labels.
COUNTY_PRECINCTS = (
    "EAST MENARD",
    "EAST PETERSBURG",
    "GREENVIEW",
    "INDIAN CREEK",
    "NORTH ATHENS CITY",
    "NORTH ATHENS RURAL",
    "NORTH PETERSBURG",
    "NORTHWEST MENARD",
    "ROCK CREEK",
    "SOUTH ATHENS CITY",
    "SOUTH ATHENS RURAL",
    "SOUTH PETERSBURG",
    "SOUTHWEST MENARD",
    "WEST PETERSBURG",
)

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

fail = make_fail("menard-precincts")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    if len(COUNTY_PRECINCTS) != EXPECTED_PRECINCTS:
        fail("the precinct list names %d precincts, expected %d"
             % (len(COUNTY_PRECINCTS), EXPECTED_PRECINCTS))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d"
             % (county_pop, COUNTY_POP_2020))

    # The Jasper test proper: names one-for-one AND the population identity.
    V.check_fabric(vtds, COUNTY_PRECINCTS, county_pop, fail)

    # One voting district per precinct, LABELLED FROM THE COUNTY'S OWN SPELLING.
    # check_partition still runs, because it is what proves nothing is claimed
    # twice and nothing is left over.
    composition = {V.title_case(p): [p] for p in COUNTY_PRECINCTS}
    V.check_partition(composition, vtds, fail)

    precincts, pops = V.dissolve(composition, vtds, unary_union)
    overlap, covered = V.check_tiling(precincts, county_geom, transform,
                                      MAX_OVERLAP_M2, MIN_COVERED, unary_union, fail)

    features = []
    for name in sorted(composition):
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "pop2020": pops[name],
            },
            "geometry": V.round_geom(precincts[name], mapping),
        })

    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "clerkUrl": CLERK_URL,
            "precinctMapUrl": PRECINCT_MAP_URL,
            "note": ("Menard County's fourteen voting precincts. The Census 2020 "
                     "voting districts carry the county's own fourteen precinct "
                     "names one for one and sum to its exact 2020 population, so "
                     "the fabric is the county's and nothing is dissolved. Unlike "
                     "the other counties built this way, Menard is on no election-"
                     "results platform this project has found, so the names come "
                     "from the Clerk's own publications: a precinct map that is a "
                     "VECTOR PDF with a readable text layer, and a polling-place "
                     "list numbering the same fourteen #1 to #14 across seven "
                     "buildings. Features are labelled from the county's spelling, "
                     "which writes NORTH ATHENS CITY with a space where the census "
                     "hyphenates it. No board district is carried here: Menard's "
                     "five commissioner districts ship separately as "
                     "menard-commissioner-districts.json, from the county's own "
                     "file. No polling place ships either — the county publishes a "
                     "list, and that belongs with a roster guard and a date."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("menard-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "menard")


if __name__ == "__main__":
    main()

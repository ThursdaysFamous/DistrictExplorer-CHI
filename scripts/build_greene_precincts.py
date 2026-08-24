#!/usr/bin/env python3
"""Build Greene County's twenty-two voting precincts from Census 2020 voting districts.

WHY THIS COUNTY HAD NO PRECINCT LAYER. Greene has been served since a 7th-Circuit
subcircuit answered here, and it moved to the County card when its seven at-large
board members shipped. Nothing was blocking its precincts; there was simply no gap
record saying they were missing, which is how a county goes unbuilt while every
guard in the repo stays green. The 2026-08-20 audit that found eleven such counties
is the reason this file exists.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 22/22 and
their POP100 sums to the county's 2020 population of 11,985 to the person.

ONE ALIAS, AND IT IS A DESIGNATION RATHER THAN A SPELLING. The county's returns
name WRIGHTS 2 where the census writes WRIGHTS — a number the county attaches and
the census does not, not two different renderings of one word. The alias is a
RENAME onto the county's own designation and apply_aliases refuses to make it a
merge: it fails if the census already carries the county's name, or if two aliases
point at one feature. Twenty-one of the twenty-two match with nothing to choose
between, which is what makes the twenty-second unambiguous.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time. Its
2026 General Primary, published by the Clerk's election-results publisher
(results.gbsvote.com), prints a precinct committeeperson contest per precinct per
party and its header reads "22 OF 22 PRECINCTS REPORTING".

NO BOARD DISTRICT SHIPS AND NONE EVER WILL. The same canvass carries a single
countywide "FOR COUNTY BOARD FOUR YEAR TERM" contest per party over all twenty-two
precincts, so Greene elects its board county-wide and there is no district for a
precinct to belong to. Its seven members ride the County card
(data/app/il-county-commissioners.json).

NO POLLING PLACE SHIPS — that belongs with a roster guard and a date.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Greene
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_greene_precincts.py            # write
    python3 scripts/build_greene_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "greene-precincts.json")

COUNTY_FIPS = "061"
COUNTY_POP_2020 = 11985
EXPECTED_PRECINCTS = 22

RESULTS_URL = "https://results.gbsvote.com/locations/counties.asp?p_id=3&l_id=11"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "twenty-two precinct names Greene County's certified 2026 "
                "General Primary names one committeeperson contest at a time")

# The county's twenty-two precincts, spelled as its own certified returns spell
# them. This list IS the Jasper test's input: the census fabric must carry these
# twenty-two names and no others.
COUNTY_PRECINCTS = (
    "ATHENSVILLE",
    "BLUFFDALE",
    "CARROLLTON 1",
    "CARROLLTON 2",
    "CARROLLTON 3",
    "KANE 1",
    "KANE 2",
    "LINDER",
    "PATTERSON",
    "ROCKBRIDGE 1",
    "ROCKBRIDGE 2",
    "ROCKBRIDGE 3",
    "ROODHOUSE 1",
    "ROODHOUSE 2",
    "ROODHOUSE 3",
    "RUBICON",
    "WALKERVILLE",
    "WHITE HALL 1",
    "WHITE HALL 2",
    "WHITE HALL 3",
    "WOODVILLE",
    "WRIGHTS 2",
)

# County spelling -> census BASENAME. One, and it is a designation rather than a spelling.
ALIASES = {
    # The county numbers a precinct the census leaves unnumbered. This is a
    # RENAME onto the county's own designation, never a merge — apply_aliases
    # refuses to touch a name the census already carries.
    "WRIGHTS 2": "WRIGHTS",
}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("greene-precincts")


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
    if ALIASES:
        V.apply_aliases(vtds, ALIASES, fail)

    # The Jasper test proper: names one-for-one AND the population identity.
    V.check_fabric(vtds, COUNTY_PRECINCTS, county_pop, fail)

    # One voting district per precinct, LABELLED from the census basename, which after the alias below is the county's own spelling throughout.
    # check_partition still runs, because it is what proves nothing is claimed
    # twice and nothing is left over — the guard that would catch a future
    # re-precincting that kept the same count.
    composition = {}
    for precinct in COUNTY_PRECINCTS:
        label = V.title_case(vtds[V.norm(precinct)]["basename"])
        if label in composition:
            fail("two precincts label as %r — the census basenames are not "
                 "distinct under this county's rendering" % label)
        composition[label] = [precinct]
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
            "resultsUrl": RESULTS_URL,
            "note": ("Greene County's twenty-two voting precincts. The Census 2020 voting "
                     "districts carry the county's own twenty-two precinct names and sum to "
                     "its exact 2020 population, so the fabric is the county's and nothing "
                     "is dissolved. The names and the count both come from the county's "
                     "certified 2026 General Primary, which prints a committeeperson "
                     "contest per precinct per party and reads \"22 OF 22 PRECINCTS "
                     "REPORTING\". One alias is applied and it is a designation rather than "
                     "a spelling: the county numbers WRIGHTS 2 where the census leaves "
                     "WRIGHTS unnumbered. NO BOARD DISTRICT is carried and none ever will "
                     "be: the same canvass carries a single countywide COUNTY BOARD "
                     "contest over all twenty-two precincts, so Greene elects its board "
                     "county-wide and its seven members ride the County card. No polling "
                     "place ships either — that belongs with a roster guard and a date."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("greene-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "greene")


if __name__ == "__main__":
    main()

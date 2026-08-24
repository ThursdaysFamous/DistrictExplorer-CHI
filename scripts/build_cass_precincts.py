#!/usr/bin/env python3
"""Build Cass County's twenty-one voting precincts from Census 2020 voting districts.

WHY THIS COUNTY HAD NO PRECINCT LAYER, WHICH IS THE ONLY INTERESTING PART. Cass has
been served since its board districts shipped, and nothing was blocking its
precincts — no refusal, no missing publisher, no split fabric. It simply had no gap
record saying why they were absent, which is how a county goes unbuilt for weeks
while every guard in the repo stays green. The 2026-08-20 audit that found eleven
such counties is the reason this file exists.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 21/21 with
no alias at all: the census voting districts carry Cass's twenty-one precinct names
exactly as its own certified returns spell them, and their POP100 sums to the
county's 2020 population of 13,042 to the person.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time. Its
2026 General Primary, published by the Clerk's election-results publisher
(results.gbsvote.com), prints a precinct committeeperson contest per precinct per
party — forty-two contests naming all twenty-one and no twenty-second — and its
header reads "21 OF 21 PRECINCTS REPORTING".

THE BOARD IS ALREADY SHIPPED AND IS NOT TOUCHED HERE. Cass elects four districts
whose contests on that same canvass report 4, 5, 6 and 6 precincts — summing to
twenty-one, the county's exact total, which is what a whole-precinct plan looks
like and is worth recording beside a file that carries the precincts those numbers
count. The districts themselves come from data/app/cass-county-board-districts.json
and nothing here changes them.

NO POLLING PLACE SHIPS. That belongs with a roster guard and a date rather than
inside a geometry file — the rule Calhoun's build set.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Cass re-precincts
or TIGERweb republishes the voting-district fabric. Output is deterministic, so
--check is a byte compare.

Usage:
    python3 scripts/build_cass_precincts.py            # write
    python3 scripts/build_cass_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "cass-precincts.json")

COUNTY_FIPS = "017"
COUNTY_POP_2020 = 13042
EXPECTED_PRECINCTS = 21

RESULTS_URL = "https://results.gbsvote.com/locations/counties.asp?p_id=3&l_id=8"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "twenty-one precinct names Cass County's certified 2026 "
                "General Primary names one committeeperson contest at a time")

# The county's twenty-one precincts, spelled as its own certified returns spell
# them. This list IS the Jasper test's input: the census fabric must carry these
# twenty-one names and no others.
COUNTY_PRECINCTS = (
    "ARENZVILLE 11",
    "ASHLAND 20",
    "ASHLAND 21",
    "BEARDSTOWN 1",
    "BEARDSTOWN 2",
    "BEARDSTOWN 3",
    "BEARDSTOWN 4",
    "BEARDSTOWN 5",
    "BEARDSTOWN 6",
    "BEARDSTOWN 7",
    "BEARDSTOWN 8",
    "BLUFF SPRINGS 10",
    "CHANDLERVILLE 18",
    "HAGENER 9",
    "NEWMANSVILLE 19",
    "PANTHER CREEK 17",
    "PHILADELPHIA 16",
    "SANGAMON VALLEY 12",
    "VIRGINIA 13",
    "VIRGINIA 14",
    "VIRGINIA 15",
)

# County spelling -> census BASENAME. Cass needs none: its returns and the census agree on all twenty-one.
ALIASES = {}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("cass-precincts")


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

    # One voting district per precinct, LABELLED from the census basename, which for this county is the county's own spelling exactly.
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
            "note": ("Cass County's twenty-one voting precincts. The Census 2020 voting "
                     "districts carry the county's own twenty-one precinct names one for "
                     "one and sum to its exact 2020 population, so the fabric is the "
                     "county's and nothing is dissolved. The names and the count both come "
                     "from the county's certified 2026 General Primary, which prints a "
                     "committeeperson contest per precinct per party and reads \"21 OF 21 "
                     "PRECINCTS REPORTING\". No board district is carried here: Cass's four "
                     "districts ship separately as cass-county-board-districts.json, and its "
                     "district contests on the same canvass report 4 + 5 + 6 + 6 precincts, "
                     "summing to the county's exact twenty-one. No polling place ships — "
                     "the county publishes no precinct-to-building table this project can "
                     "read, and such a table belongs with a roster guard in any case."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("cass-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "cass")


if __name__ == "__main__":
    main()

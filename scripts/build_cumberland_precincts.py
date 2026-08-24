#!/usr/bin/env python3
"""Build Cumberland County's twelve voting precincts from Census 2020 voting districts.

WHY THIS COUNTY JOINS ON PRECINCTS AND NOT ON ITS BOARD. Cumberland elects six
board members from three districts named by compass point — Western, Central and
Eastern — and those districts SPLIT PRECINCTS, so no union of whole precincts can
ever draw them. That is measured, not assumed, and it is re-measured here: the
county's certified 2026 General Primary reports its board contests as CENTRAL 6,
EASTERN 5, WESTERN 3 precincts, summing to FOURTEEN against a county of twelve,
identically for both parties, while every countywide contest on the same canvass
reports exactly twelve. Two precincts sit in two districts each. The board is
therefore permanently shut to this route and the county's own district boundary
is the only thing that would open it.

THE PRECINCTS ARE A DIFFERENT QUESTION AND THEY ARE ANSWERED. This is the join
bar the project settled on 2026-08-21 — a county joins on its BOARD or on its
PRECINCTS — and Cumberland clears it on the second, the way Calhoun, Morgan and
Gallatin did.

THE JASPER TEST PASSES 12/12 WITH NO ALIAS AT ALL, which is worth stating because
this project's own record predicted one. It read the Clerk's polling-place notice,
which groups the precincts under roman numerals — "NEOGA I & II", "SUMPTER I & II",
"GREENUP I, II, & III" — and concluded the county spelled them that way while the
census spelled them arabic. It does not. Those are POLLING-PLACE GROUPINGS, three
buildings serving seven precincts, not precinct names: the county's own certified
returns print PRECINCT COMMITTEEPERSON contests for GREENUP 1, GREENUP 2, GREENUP 3,
NEOGA 1, NEOGA 2, SUMPTER 1 and SUMPTER 2 in arabic, exactly as the census does.
Read the names from the contest list, never from the polling notice's headings.

THREE WITNESSES NAME THE SAME TWELVE, none of them this project's own guess:

  1. THE COUNTY'S CERTIFIED RETURNS NAME THEM ONE BY ONE. The 2026 General
     Primary, published by the Clerk's own election-results publisher
     (results.gbsvote.com), carries a precinct committeeperson contest per
     precinct per party — twenty-four contests, each "of 1 precincts", naming
     all twelve and no thirteenth.
  2. THE SAME CANVASS COUNTS THEM. Every countywide contest on it — County Clerk
     and Recorder, County Treasurer, Sheriff, Treasurer — reports "of 12
     precincts", and the canvass header reads "OF 12 PRECINCTS REPORTING".
  3. THE CLERK'S OWN POLLING NOTICE LISTS THEM. The 2026 General Primary Election
     Notice pairs the twelve with eight buildings, signed by County Clerk Beverly
     Howard.

And the census fabric answers to all three: TIGER's Census 2020 voting-district
layer carries exactly twelve Cumberland features whose BASENAMEs are those twelve
names and whose POP100 sums to the county's own 2020 population of 10,450 to the
person. No dissolve is needed and none is performed — each precinct IS one voting
district — so this file's geometry is the census fabric under the county's names.

NO BOARD DISTRICT SHIPS, for the reason at the top. NO POLLING PLACE SHIPS: the
county publishes a list and it belongs with a roster guard and a date, which is
the rule Calhoun's build set.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Cumberland
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_cumberland_precincts.py            # write
    python3 scripts/build_cumberland_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "cumberland-precincts.json")

COUNTY_FIPS = "035"
COUNTY_POP_2020 = 10450
EXPECTED_PRECINCTS = 12

ELECTIONS_URL = "https://cumberlandcoil.gov/elections/"
RESULTS_URL = "https://results.gbsvote.com/locations/counties.asp?p_id=3&l_id=9"
POLLING_NOTICE_URL = ("http://www.cumberlandcoil.gov/pdf/"
                      "Primary%20Election%20Notice%202026-%20Polling%20Places.pdf")
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "twelve precinct names Cumberland County's certified 2026 "
                "General Primary and its Clerk's polling notice use")

# The county's twelve precincts, spelled as its own certified returns spell them
# — arabic, not the roman numerals its polling notice groups them under. This
# list IS the Jasper test's input: the census fabric must carry these twelve
# names and no others.
COUNTY_PRECINCTS = (
    "COTTONWOOD",
    "CROOKED CREEK",
    "GREENUP 1",
    "GREENUP 2",
    "GREENUP 3",
    "NEOGA 1",
    "NEOGA 2",
    "SPRING POINT",
    "SUMPTER 1",
    "SUMPTER 2",
    "UNION",
    "WOODBURY",
)

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("cumberland-precincts")


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

    # One voting district per precinct. check_partition still runs, because it
    # is what proves nothing is claimed twice and nothing is left over — the
    # guard that would catch a future re-precincting that kept the same count.
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
            "electionsUrl": ELECTIONS_URL,
            "resultsUrl": RESULTS_URL,
            "pollingNoticeUrl": POLLING_NOTICE_URL,
            "note": ("Cumberland County's twelve voting precincts. The Census 2020 "
                     "voting districts carry the county's own twelve precinct names "
                     "one for one and sum to its exact 2020 population, so the "
                     "fabric is the county's and nothing is dissolved. The county's "
                     "certified 2026 General Primary names all twelve, one precinct "
                     "committeeperson contest apiece per party, and counts twelve on "
                     "every countywide contest; the Clerk's polling notice pairs the "
                     "same twelve with eight buildings. NO BOARD DISTRICT is carried: "
                     "Cumberland's three compass-point districts SPLIT precincts — its "
                     "own returns report Central 6, Eastern 5 and Western 3 against a "
                     "county of twelve — so no union of whole precincts can draw them, "
                     "and only the county's own boundary ever will. No polling place "
                     "is carried either — the county publishes a list, and that "
                     "belongs with a roster guard rather than in a geometry file."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("cumberland-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "cumberland")


if __name__ == "__main__":
    main()

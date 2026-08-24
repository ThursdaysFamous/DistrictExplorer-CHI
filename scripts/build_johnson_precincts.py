#!/usr/bin/env python3
"""Build Johnson County's sixteen voting precincts from Census 2020 voting districts.

WHY THIS COUNTY WAS DARK, AND WHAT OPENED IT. Johnson's recorded blocker is its
website: johnsoncountyil.com sits behind a host-level block that refuses this
client outright, so nothing the county publishes about itself could be read. That
blocker is unchanged and this build does not touch it. What changed is that the
county's ELECTION AUTHORITY publishes somewhere else — results.gbsvote.com, which
carries THIRTEEN Illinois counties (plus one in Indiana) — and a county's
certified canvass answers both questions a join needs without the county's own
site being reachable at all.

THE VENDOR WAS NOT A NEW DISCOVERY AND SHOULD NOT BE READ AS ONE. This project
recorded it in its own backlog on 2026-08-20, swept it county by county, and
measured this county's board form from it that day. What did not happen for the
day after is the rest: the finding never reached the county's gap record, never reached
CLAUDE.md's list of results platforms, and never became a build. A measurement
filed in a backlog and nowhere else is a measurement the next pass repeats.

THE BOARD'S FORM IS SETTLED, AND IT IS AT LARGE. Johnson's certified 2026 General
Primary carries a single "FOR COUNTY COMMISSIONER" contest per party, each
reporting 16 of 16 precincts — the same 16-of-16 every countywide office on that
ballot reports (County Clerk, County Treasurer, Sheriff, Treasurer). There is no
district-suffixed board contest anywhere in it, and the contests that report 1 of 1
are the sixteen precinct committeeperson races, which is the expected shape and the
check that the reporting counts mean what they appear to. So Johnson is a
COMMISSION county electing county-wide: THERE IS NO BOARD GEOMETRY TO SEEK and none
should be invented. Its commissioners are not carried here either — that is a
roster, it belongs on the County card with a source and a date, and the only county
source for it is the site this client cannot read.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 16/16:
the census voting districts carry Johnson's sixteen precinct names exactly, and
their POP100 sums to the county's own 2020 population of 13,308 to the person. No
dissolve is needed and none is performed — each precinct IS one voting district —
so this file's geometry is the census fabric under the county's names.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time: the
2026 General Primary prints a precinct committeeperson contest per precinct per
party, thirty-two contests naming all sixteen and no seventeenth, and its header
reads "16 OF 16 PRECINCTS REPORTING".

NO POLLING PLACE SHIPS. That belongs with a roster guard and a date rather than
inside a geometry file — the rule Calhoun's build set — and in this county it is
not readable anyway.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Johnson
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_johnson_precincts.py            # write
    python3 scripts/build_johnson_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "johnson-precincts.json")

COUNTY_FIPS = "087"
COUNTY_POP_2020 = 13308
EXPECTED_PRECINCTS = 16

RESULTS_URL = "https://results.gbsvote.com/locations/counties.asp?p_id=3&l_id=12"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "sixteen precinct names Johnson County's certified 2026 General "
                "Primary names one committeeperson contest at a time")

# The county's sixteen precincts, spelled as its own certified returns spell
# them. This list IS the Jasper test's input: the census fabric must carry these
# sixteen names and no others.
COUNTY_PRECINCTS = (
    "BELKNAP",
    "BLOOMFIELD",
    "BURNSIDE",
    "CACHE",
    "ELVIRA",
    "GOREVILLE 1",
    "GOREVILLE 2",
    "GRANTSBURG",
    "LAKE 1",
    "LAKE 2",
    "OZARK",
    "SIMPSON",
    "TUNNEL HILL",
    "VIENNA 1",
    "VIENNA 2",
    "VIENNA 3",
)

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("johnson-precincts")


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
            "resultsUrl": RESULTS_URL,
            "note": ("Johnson County's sixteen voting precincts. The Census 2020 "
                     "voting districts carry the county's own sixteen precinct "
                     "names one for one and sum to its exact 2020 population, so "
                     "the fabric is the county's and nothing is dissolved. The "
                     "names and the count both come from the county's certified "
                     "2026 General Primary, which prints a committeeperson contest "
                     "per precinct per party and reads \"16 OF 16 PRECINCTS "
                     "REPORTING\" — the county's own website is behind a host-level "
                     "block and was not readable. NO BOARD DISTRICT is carried: the "
                     "same canvass carries a single countywide FOR COUNTY "
                     "COMMISSIONER contest per party over all sixteen precincts and "
                     "no district-suffixed board contest at all, so Johnson elects "
                     "its board county-wide and there is no district for a precinct "
                     "to belong to. No commissioner is named here either — that is a "
                     "roster, and the only county source for it is the blocked site. "
                     "No polling place ships, for the same reason and by the same "
                     "rule."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("johnson-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "johnson")


if __name__ == "__main__":
    main()

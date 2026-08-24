#!/usr/bin/env python3
"""Build Hardin County's six voting precincts from Census 2020 voting districts.

WHY THIS COUNTY WAS RECORDED AS A ROSTER ASK AND NOTHING ELSE, and why that was
half right. Hardin's board form has been settled since 2026-08-20: it is a
COMMISSION county electing county-wide, proven from its certified 2026 General
Primary on il-hardin.pollresults.net and corroborated on 2026-08-23 by a second
vendor a decade apart (platinumelectionresults.com county id 20 — its 2016
General reports "For County Commissioner" over 6 of 6 precincts). So there is no
board geometry to seek here and none is invented. The record concluded from that
that Hardin was a roster ask alone, which skipped the question Johnson, Perry and
Pulaski all answered: THE PRECINCTS ARE A SEPARATE JOIN, and this county clears
that bar exactly as they do.

IT ALSO CORRECTS A BAR THIS PROJECT INVENTED FOR ONE AFTERNOON. Pulaski shipped
hours earlier and its build log said Hardin lacked "Pulaski's second naming
source", because the platinum canvass carries no committeeperson contests. That
was a bar the fleet does not use and had never used: Johnson, Perry and Pulaski
each joined on ONE certified canvass that names the precincts plus the Jasper
test. Hardin's pollresults feed meets that identically, and holding one county to
a stricter standard than three others is not caution — it is an inconsistency
that keeps a county dark for no stated reason.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time:
the 2026 General Primary (ElectionId 1566, Final, updated 2026-03-30) prints a
precinct committeeperson contest per precinct per party — twelve contests naming
all six precincts and no seventh, each reporting 1 of 1 — while every countywide
office on the same ballot reports 6 of 6. That is the shape that makes the
reporting counts mean what they appear to.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 6/6: the
census voting districts carry Hardin's six precinct names exactly, and their
POP100 sums to the county's own 2020 population of 3,649 to the person. No
dissolve is needed and none is performed.

NO ROSTER SHIPS. The commissioners are a County-card fact and hardincountyil.gov
is a parking lander on both hosts (a 114-byte script redirect to /lander), so no
county source names them. The returns cannot substitute: the 2026 contest is a
PRIMARY, which names nominees rather than officeholders (the Scott rule), and the
platinum general is from 2016. The standing ask to Clerk Cowsert remains the only
route to the names.

NO POLLING PLACE SHIPS, by the rule Calhoun's build set: that belongs with a
roster guard and a date rather than inside a geometry file.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Hardin
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_hardin_precincts.py            # write
    python3 scripts/build_hardin_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "hardin-precincts.json")

COUNTY_FIPS = "069"
COUNTY_POP_2020 = 3649
EXPECTED_PRECINCTS = 6

RESULTS_URL = "https://il-hardin.pollresults.net/"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "six precinct names Hardin County's certified 2026 General "
                "Primary names one committeeperson contest at a time")

# The county's six precincts, spelled as its own certified returns spell them.
# This list IS the Jasper test's input: the census fabric must carry these six
# names and no others.
COUNTY_PRECINCTS = (
    "CAVE IN ROCK",
    "MCFARLAN",
    "MONROE",
    "ROCK",
    "ROSICLARE",
    "STONE CHURCH",
)

# TWO NAMES NEED AN EXPLICIT LABEL, which is what vtd_board_districts.title_case's
# own docstring prescribes for a name no general rule gets right. Neither entry
# here is a guess; each cites a source.
#
#   MCFARLAN — the returns and the voting-district layer both print it in
#   capitals, so neither says where the internal capital falls, and
#   title_case() renders "Mcfarlan", which is not how any publisher writes it.
#   The CENSUS ITSELF answers, in mixed case, in its county-subdivision layer
#   for this county: BASENAME "McFarlan", NAME "McFarlan precinct". Same
#   publisher as the geometry, and a readable source rather than the "Mc" rule
#   applied on faith.
#
#   CAVE IN ROCK — here the two publishers genuinely disagree. The county's own
#   certified returns write "CAVE IN ROCK" with no hyphens; the census writes
#   CAVE-IN-ROCK in both its voting-district and county-subdivision layers. THE
#   COUNTY'S SPELLING WINS because these are the county's precincts and the card
#   names them to a voter who will see them on the county's own paperwork. The
#   disagreement is recorded rather than smoothed away.
DISPLAY_NAMES = {
    "MCFARLAN": "McFarlan",
    "CAVE IN ROCK": "Cave In Rock",
}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("hardin-precincts")


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
    composition = {DISPLAY_NAMES.get(p, V.title_case(p)): [p]
                   for p in COUNTY_PRECINCTS}
    if len(composition) != EXPECTED_PRECINCTS:
        fail("display names collided: %d labels for %d precincts"
             % (len(composition), EXPECTED_PRECINCTS))
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
            "note": ("Hardin County's six voting precincts. The Census 2020 "
                     "voting districts carry the county's own six precinct names "
                     "one for one and sum to its exact 2020 population, so the "
                     "fabric is the county's and nothing is dissolved. The names "
                     "and the count both come from the county's certified 2026 "
                     "General Primary, which prints a committeeperson contest per "
                     "precinct per party — the county's own web domain is a "
                     "parking lander on both hosts and publishes nothing. NO "
                     "BOARD DISTRICT is carried: the board is elected county-wide, "
                     "proven from that canvass and again from a 2016 General on a "
                     "second vendor, so there is no district for a precinct to "
                     "belong to. No commissioner is named here either — that is a "
                     "roster, the county publishes no page, and a primary names "
                     "nominees rather than officeholders. No polling place ships, "
                     "by the rule Calhoun's build set."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("hardin-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "hardin")


if __name__ == "__main__":
    main()

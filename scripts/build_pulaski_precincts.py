#!/usr/bin/env python3
"""Build Pulaski County's eleven voting precincts from Census 2020 voting districts.

WHAT WAS RECORDED ABOUT THIS COUNTY, AND WHY IT DID NOT SETTLE ANYTHING. Its gap
record has said since 4 Aug 2026 that "whether the board is districted or elected
county-wide was not determinable in this pass", and the reason given was the
website: pulaskicountyil.gov resolves to an address this research environment's
egress proxy refuses, so the county's own pages were never seen. That blocker is
unchanged and this build does not touch it. What changed is the third results
vendor: platinumelectionresults.com carries Pulaski at COUNTY ID 19, which this
project's own sweep of that vendor had missed because it swept ONE election slug.
Sweeping several found it — along with Hardin, Champaign and Calhoun — which is
the operational rule the Alexander build wrote down and this county is the first
to be opened by.

THE BOARD'S FORM IS SETTLED, AND IT IS AT LARGE. Pulaski's certified 2024 General
Primary carries a single "Pulaski County | For County Commissioner" contest per
party, each reporting 11 of 11 precincts — the same 11 of 11 every countywide
office on that ballot reports (Circuit Clerk, State's Attorney, County Coroner)
and the same the presidential contest reports. There is no district-suffixed
board contest anywhere in it, and the ONLY contests reporting 1 of 1 are the
eleven precinct committeeperson races, which is the expected shape and the check
that these reporting counts mean what they appear to. The 2016 General agrees
independently: one "For County Commissioner" over the same eleven precincts.
So Pulaski is a COMMISSION county electing county-wide — THERE IS NO BOARD
GEOMETRY TO SEEK and none should be invented.

ITS COMMISSIONERS ARE NOT CARRIED HERE. That is a roster, it belongs on the
County card with a source and a date, and the only county source for it is the
site this client cannot reach. The vendor cannot substitute: it holds a 2024
PRIMARY (nominees, not officeholders — the Scott rule) and a 2016 general, which
is one seat filled a decade ago. Union and Williamson could ship rosters from
returns because their canvasses covered every seat recently; Pulaski's do not.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 11/11:
the census voting districts carry Pulaski's eleven precinct names exactly, and
their POP100 sums to the county's own 2020 population of 5,193 to the person. No
dissolve is needed and none is performed — each precinct IS one voting district —
so this file's geometry is the census fabric under the county's names.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time:
the 2024 General Primary prints a precinct committeeperson contest per precinct
per party, twenty-two contests naming all eleven and no twelfth.

NO POLLING PLACE SHIPS. That belongs with a roster guard and a date rather than
inside a geometry file — the rule Calhoun's build set — and in this county it is
not readable anyway.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Pulaski
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_pulaski_precincts.py            # write
    python3 scripts/build_pulaski_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "pulaski-precincts.json")

COUNTY_FIPS = "153"
COUNTY_POP_2020 = 5193
EXPECTED_PRECINCTS = 11

RESULTS_URL = "https://platinumelectionresults.com/history"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "eleven precinct names Pulaski County's certified 2024 General "
                "Primary names one committeeperson contest at a time")

# The county's eleven precincts, spelled as its own certified returns spell them.
# This list IS the Jasper test's input: the census fabric must carry these eleven
# names and no others.
COUNTY_PRECINCTS = (
    "GRAND CHAIN",
    "KARNAK",
    "MOUND CITY",
    "MOUNDS 1",
    "MOUNDS 2",
    "MOUNDS 3",
    "OLMSTED",
    "PERKS-WETAUG",
    "PULASKI",
    "ULLIN",
    "VILLA RIDGE-AMERICA",
)

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


def fail(msg):
    print("pulaski-precincts: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


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
            "note": ("Pulaski County's eleven voting precincts. The Census 2020 "
                     "voting districts carry the county's own eleven precinct "
                     "names one for one and sum to its exact 2020 population, so "
                     "the fabric is the county's and nothing is dissolved. The "
                     "names and the count both come from the county's certified "
                     "2024 General Primary, which prints a committeeperson contest "
                     "per precinct per party — the county's own website resolves to "
                     "an address this project's network refuses and was not "
                     "readable. NO BOARD DISTRICT is carried: the same canvass "
                     "carries a single countywide For County Commissioner contest "
                     "per party over all eleven precincts and no district-suffixed "
                     "board contest at all, so Pulaski elects its board county-wide "
                     "and there is no district for a precinct to belong to. No "
                     "commissioner is named here either — that is a roster, and the "
                     "only county source for it is the unreachable site. No polling "
                     "place ships, for the same reason and by the same rule."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("pulaski-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "pulaski")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/clinton-county-board-districts.json — Clinton County's 5 County
Board districts, composed from the county's own certified election returns
(docs/EXPANSION_GUIDE.md §2.5.1, the canvass route; scripts/vtd_board_districts.py
holds the machinery).

SECOND COUNTY FROM THE PLATINUM VENDOR, found the same day as Franklin.
Clinton's Clerk publishes on platinumelectionresults.com (county 10), the third
results vendor this project recorded on 2026-08-20. Its per-precinct race pages
carry every contest a precinct actually voted on, so the set of precincts
carrying a district's board contest IS that district's composition.

THREE CERTIFIED ELECTIONS, AND THE THIRD IS THE INTERESTING ONE:

  * 2024 GENERAL — all 34 precincts carry one numbered contest, "FOR COUNTY
    BOARD DISTRICT n". They partition 7/9/6/5/7 = 34, each precinct once.
  * 2026 GENERAL PRIMARY — the identical partition, also numbered.
  * 2022 GENERAL — the contests are NOT numbered here; they name candidates.
    Those candidate sets key onto the county's own board page exactly (Jansen
    and Ken Knolhoff under District 1, Schroeder and Strieker under 3, Rapien
    and Haselhorst under 5), so the oldest election corroborates the two newer
    numbered ones from a different direction.

THIS COUNTY IS A COMPOSED FABRIC, NOT A ONE-TO-ONE ONE — the Calhoun shape,
and the reason this build uses check_fabric_composed rather than the Jasper
test's name-for-name comparison. Census 2020 carries 39 Clinton voting
districts; the county runs 34 precincts today, having merged four groups since:

    IRISHTOWN 1 + IRISHTOWN 2   -> Irishtown
    LAKE 1      + LAKE 2        -> Lake
    ST ROSE 1   + ST ROSE 2     -> St Rose
    BROOKSIDE 1..5              -> Brookside 1, Brookside 2, Brookside 3

THE FIRST THREE ARE NAMEABLE AND THE FOURTH IS NOT, and it does not matter
here — which is the point worth recording. Nothing published says which census
Brookside became which county Brookside. But all five Brookside voting
districts sit in District 1, so the ambiguity cannot move a district line: the
dissolve is the same whichever way the merge went. A county where an
unnameable merge STRADDLED a district line could not be built this way, and
Marion — measured the same afternoon — is exactly that county, its Centralia
and Salem voting districts spanning three districts each.

That is also why NO PRECINCT LAYER SHIPS for Clinton. A precinct card would
have to name Brookside, and this build cannot say which is which. The county
board card is whole and honest; the precinct answer is a recorded gap.

THE POPULATION SPREAD IS THE TIGHTEST THIS ROUTE HAS PRODUCED: 6,840 to 7,678
against a 7,380 ideal, worst deviation 7.3%. Edgar shipped at 11.8% and
Franklin at 11.4%; Wayne, measured the same afternoon, came out at 32.4% and
was NOT built for that reason. A spread this tight is what a post-2020 adopted
plan looks like, and it is the strongest evidence available that this
composition is the county's current map rather than a stale one.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Clinton
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_clinton_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DISTRICTS = os.path.join(REPO_ROOT, "data", "app",
                             "clinton-county-board-districts.json")

COUNTY_FIPS = "027"
COUNTY_POP_2020 = 36899
EXPECTED_VTDS = 39            # census 2020 voting districts
COUNTY_PRECINCTS = 34         # what the county runs today
SEATS_PER_DISTRICT = 3        # the board page lists three members per district

RESULTS_URL = "https://platinumelectionresults.com/turnouts/county/10"
BOARD_URL = "https://clintonco.illinois.gov/county-offices/county-board/"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "Clinton County's certified 2024 General, 2026 General Primary "
                "and 2022 General results, published per precinct by County "
                "Clerk & Recorder Vicky Albers's results system "
                "(platinumelectionresults.com)")

# Keyed by CENSUS voting district, because that is the geometry being
# dissolved. Every one of the 39 is claimed exactly once. The eight that carry
# no same-named county precinct today (the merges above) are placed by their
# base name, which is unambiguous for all four groups — see the docstring.
COMPOSITION = {
    "1": ("BROOKSIDE 1", "BROOKSIDE 2", "BROOKSIDE 3", "BROOKSIDE 4",
          "BROOKSIDE 5", "EAST FORK", "LAKE 1", "LAKE 2", "MERIDIAN", "SANTA FE"),
    "2": ("CARLYLE 1", "CARLYLE 2", "CARLYLE 3", "CARLYLE 4", "CLEMENT",
          "IRISHTOWN 1", "IRISHTOWN 2", "WADE 1", "WADE 2", "WHEATFIELD"),
    "3": ("BREESE 1", "BREESE 2", "BREESE 3", "BREESE 4",
          "GERMANTOWN 1", "GERMANTOWN 2"),
    "4": ("ST ROSE 1", "ST ROSE 2", "SUGAR CREEK 1", "SUGAR CREEK 2",
          "SUGAR CREEK 4", "SUGAR CREEK 5"),
    "5": ("LOOKINGGLASS 1", "LOOKINGGLASS 2", "LOOKINGGLASS 3", "LOOKINGGLASS 4",
          "LOOKINGGLASS 5", "LOOKINGGLASS 6", "SUGAR CREEK 3"),
}

# The county's own current precincts per district, as its certified returns
# tabulate them. Carried on the district feature so the card can name what a
# reader would recognise, and re-read weekly as the drift tripwire.
COUNTY_COMPOSITION = {
    "1": ("Brookside 1", "Brookside 2", "Brookside 3", "East Fork", "Lake",
          "Meridian", "Santa Fe"),
    "2": ("Carlyle 1", "Carlyle 2", "Carlyle 3", "Carlyle 4", "Clement",
          "Irishtown", "Wade 1", "Wade 2", "Wheatfield"),
    "3": ("Breese 1", "Breese 2", "Breese 3", "Breese 4", "Germantown 1",
          "Germantown 2"),
    "4": ("St Rose", "Sugar Creek 1", "Sugar Creek 2", "Sugar Creek 4",
          "Sugar Creek 5"),
    "5": ("Lookingglass 1", "Lookingglass 2", "Lookingglass 3", "Lookingglass 4",
          "Lookingglass 5", "Lookingglass 6", "Sugar Creek 3"),
}

BALANCE_DEV_MAX = 0.30        # measured 0.073 — the tightest this route has produced
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

fail = make_fail("clinton-boundaries")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    claimed = [n for names in COMPOSITION.values() for n in names]
    if len(claimed) != EXPECTED_VTDS:
        fail("the composition names %d voting districts, expected %d"
             % (len(claimed), EXPECTED_VTDS))
    county_named = sum(len(v) for v in COUNTY_COMPOSITION.values())
    if county_named != COUNTY_PRECINCTS:
        fail("the county-precinct composition names %d precincts, expected %d"
             % (county_named, COUNTY_PRECINCTS))
    if sorted(COMPOSITION) != sorted(COUNTY_COMPOSITION):
        fail("the two compositions describe different district sets")

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Clinton features, "
             "expected %d" % (len(vtds), EXPECTED_VTDS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d"
             % (county_pop, COUNTY_POP_2020))
    # The composed-fabric test (Calhoun): the population identity proves the
    # voting districts still tile the county; check_partition below proves the
    # composition accounts for every one of them exactly once. The assurance
    # that this is the county's CURRENT map comes from the three certified
    # elections in the docstring, not from either check.
    V.check_fabric_composed(vtds, county_pop, fail)
    V.check_partition(COMPOSITION, vtds, fail)

    districts, pops = V.dissolve(COMPOSITION, vtds, unary_union)
    ideal = county_pop / float(len(COMPOSITION))
    worst = max(((abs(pops[d] - ideal) / ideal), d) for d in pops)
    if worst[0] > BALANCE_DEV_MAX:
        fail("district %s deviates %.1f%% from the per-district ideal (ceiling "
             "%.0f%%) — that is a mis-assignment, not an apportionment"
             % (worst[1], 100 * worst[0], 100 * BALANCE_DEV_MAX))
    overlap, covered = V.check_tiling(districts, county_geom, transform,
                                      MAX_OVERLAP_M2, MIN_COVERED, unary_union, fail)

    features = []
    for dnum in sorted(COMPOSITION, key=int):
        features.append({
            "type": "Feature",
            "properties": {"district": dnum, "name": "District %s" % dnum,
                           "precincts": list(COUNTY_COMPOSITION[dnum]),
                           "pop2020": pops[dnum], "seats": SEATS_PER_DISTRICT},
            "geometry": V.round_geom(districts[dnum], mapping),
        })
    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "resultsUrl": RESULTS_URL, "boardUrl": BOARD_URL,
            "canvass": ("Composition from three certified elections. The 2024 "
                        "General and 2026 General Primary each carry a numbered "
                        "'FOR COUNTY BOARD DISTRICT n' contest in every one of "
                        "the county's 34 precincts, partitioning them 7/9/6/5/7; "
                        "the 2022 General names candidates rather than districts "
                        "and those candidates key onto the county's own board "
                        "page, corroborating the same five sets from a different "
                        "direction"),
            "note": ("Five districts of THREE members each, dissolved from the "
                     "Census 2020 voting districts. Clinton publishes its board "
                     "map only as a PDF, so these boundaries are derived from "
                     "the election returns instead. The county has merged four "
                     "groups of precincts since 2020 (Irishtown, Lake and St "
                     "Rose from numbered pairs; Brookside from five to three), "
                     "and all of the merged voting districts fall inside a "
                     "single board district, so the merges cannot move a "
                     "district line. The precinct list on each feature is the "
                     "county's own current 34, not the 39 census units the "
                     "geometry is built from."),
        },
        "features": features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, features, point_in_rings, fail)

    body = V.dumps(payload)
    print("clinton-boundaries: %d census voting districts -> %d districts of %d "
          "(the county's own 34 precincts named on the features)"
          % (EXPECTED_VTDS, len(COMPOSITION), SEATS_PER_DISTRICT))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_DISTRICTS, body)], args.check, REPO_ROOT, fail, "clinton")


if __name__ == "__main__":
    main()

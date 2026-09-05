#!/usr/bin/env python3
"""Build Jo Daviess County's twenty-eight voting precincts from Census 2020 voting districts.

WHY THIS COUNTY WAS RECORDED SHUT AND IS NOT. `jodaviess-jersey-precinct-geometry`
covers TWO counties, and its blocker is Jersey's. Jersey went from 25 census voting
districts to 22 through two events, and only one is composable: QUARRY 1 + QUARRY 2
-> QUARRY names itself, while JERSEY 9 AND JERSEY 10 SIMPLY VANISH into some subset
of Jersey 1-8 that nothing published identifies. Guessing which of the eight grew is
what the honesty rules forbid, so Jersey stays shut.

JO DAVIESS'S HALF IS A DIFFERENT SHAPE AND ALWAYS WAS. It runs 28 precincts against
the census's 29, and the single difference is WARREN I + WARREN II -> WARREN: a merge
the surviving name describes, which is the same thing check_fabric_composed was
written for on Calhoun's Belleview-Hamburg and the same thing the Knox record calls a
"nameable merge" when it accepts Henderson and Indian Point. Nothing is inferred: the
new Warren is the union of the two census districts, and there is no third possibility
for where Warren I's and Warren II's ground went. HOLDING A COUNTY SHUT BECAUSE THE
COUNTY IT SHARES A RECORD WITH IS SHUT IS NOT CAUTION — it is the Hardin lesson, and
it kept Jo Daviess dark for a fortnight for no stated reason.

TWO COUNTY WITNESSES, BOTH CURRENT, AND FROM TWO DIFFERENT OFFICES.

  1. THE CLERK'S OWN CERTIFIED RETURNS. jodaviesscountyil.gov's Election Results page
     for the 17 March 2026 General Primary — "OFFICIAL RESULTS", Clerk and Election
     Authority Dana Timmerman — lists its precincts by name in prose: Rawlins, Rice,
     Menominee, Vinegar Hill, Council Hill, Scales Mound, West Galena I/II/III, East
     Galena, Apple River, Dunleith I/II/III, Rush, Stockton I/II, Wards Grove,
     Pleasant Valley, Elizabeth, Berreman, Derinda, Hanover, WARREN, Nora, Guilford,
     Thompson, Woodbine. Twenty-eight, and Warren carries no numeral.
  2. THE GIS/IT DEPARTMENT'S POLLING MAP, revised 12 Aug 2026 — a different county
     office, and a vector PDF whose text layer lists the same twenty-eight grouped by
     shared polling place. It writes "Dunleith I, II, III" and "Stockton I, II" and
     "West Galena I, II, III" where precincts share a building, so it demonstrably
     WOULD have written "Warren I, II" had there been two. It writes "Warren".

WHAT THE POPULATION IDENTITY DOES AND DOES NOT PROVE, because this county is named in
check_fabric_composed's own docstring as a trap: the 29 voting districts sum to 22,035,
the county's exact Census 2020 count, and that says the fabric TILED the county in 2020
— never that it is the county's fabric today. The assurance that it still is comes from
the two witnesses above, which is what that docstring asks of the caller.

NO POLLING PLACE SHIPS, though the GIS map above carries one for every precinct. That
is a roster fact wanting a guard and a date of its own, and it goes in the gaps ledger
rather than into a geometry file — the rule Calhoun's build set.

NO BOARD DISTRICT IS TOUCHED. Jo Daviess's board districts already ship, from the
shapefile the county sold under a signed licence (see build_jodaviess_board_districts.py
and LICENSE-DATA.md); nothing here reads or changes them. This file is derived wholly
from Census 2020 geometry, so it carries none of that licence's conditions.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Jo Daviess
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_jodaviess_precincts.py            # write
    python3 scripts/build_jodaviess_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "jo-daviess-precincts.json")

COUNTY_FIPS = "085"
COUNTY_POP_2020 = 22035
EXPECTED_VTDS = 29
EXPECTED_PRECINCTS = 28

RESULTS_URL = "https://jodaviesscountyil.gov/1380/Election-Results"
POLLING_MAP_URL = ("https://jodaviesscountyil.gov/DocumentCenter/View/676/"
                   "Polling-Places-Map-revised-08-12-2026-PDF")
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct except Warren, "
                "which the county merged from Warren I and Warren II — the "
                "composition named by both the Clerk's certified 2026 General "
                "Primary results and the county GIS department's polling map")

# The composition. Keys are the county's own current precinct names as BOTH its
# certified returns and its GIS polling map spell them; values are the census
# voting districts each is made of. Every entry but Warren is one-to-one.
_ONE_TO_ONE = (
    "APPLE RIVER", "BERREMAN", "COUNCIL HILL", "DERINDA",
    "DUNLEITH I", "DUNLEITH II", "DUNLEITH III", "EAST GALENA", "ELIZABETH",
    "GUILFORD", "HANOVER", "MENOMINEE", "NORA", "PLEASANT VALLEY", "RAWLINS",
    "RICE", "RUSH", "SCALES MOUND", "STOCKTON I", "STOCKTON II", "THOMPSON",
    "VINEGAR HILL", "WARDS GROVE", "WEST GALENA I", "WEST GALENA II",
    "WEST GALENA III", "WOODBINE",
)
COMPOSITION = {V.title_case(n): [n] for n in _ONE_TO_ONE}
COMPOSITION["Warren"] = ["WARREN I", "WARREN II"]

# The one merge, asserted rather than assumed: if the census ever stops carrying
# both halves under these names, this build must stop rather than quietly ship a
# 27-precinct county.
MERGED_PRECINCT = "Warren"

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("jodaviess-precincts")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    if len(COMPOSITION) != EXPECTED_PRECINCTS:
        fail("the composition names %d precincts, expected %d"
             % (len(COMPOSITION), EXPECTED_PRECINCTS))
    # EXACTLY ONE precinct may be a merge. This is the guard that keeps this
    # build honest about what separates Jo Daviess from Jersey: a second
    # composed entry would mean a second event, and a second event is exactly
    # what nothing published describes.
    merges = [n for n, parts in COMPOSITION.items() if len(parts) > 1]
    if merges != [MERGED_PRECINCT]:
        fail("expected exactly one merged precinct (%r), got %r"
             % (MERGED_PRECINCT, merges))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Jo Daviess districts, "
             "expected %d — the fabric this build dissolves has changed shape"
             % (len(vtds), EXPECTED_VTDS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d" % (county_pop, COUNTY_POP_2020))

    # The population identity (the fabric tiled the county in 2020) plus the
    # partition (every voting district claimed exactly once, none left over).
    # Together these are what check_fabric gives a one-to-one county; the
    # currency of the composition comes from the two county witnesses named in
    # the docstring, which is what check_fabric_composed asks of its caller.
    V.check_fabric_composed(vtds, county_pop, fail)
    V.check_partition(COMPOSITION, vtds, fail)

    precincts, pops = V.dissolve(COMPOSITION, vtds, unary_union)
    overlap, covered = V.check_tiling(precincts, county_geom, transform,
                                      MAX_OVERLAP_M2, MIN_COVERED, unary_union, fail)

    features = []
    for name in sorted(COMPOSITION):
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "pop2020": pops[name],
                # The voting districts this precinct is made of, so a reader can
                # check the one merge against the county's returns without
                # re-deriving it.
                "votingDistricts": [V.title_case(n) for n in COMPOSITION[name]],
            },
            "geometry": V.round_geom(precincts[name], mapping),
        })

    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "resultsUrl": RESULTS_URL,
            "pollingMapUrl": POLLING_MAP_URL,
            "note": ("Jo Daviess County's twenty-eight precincts, dissolved from "
                     "the twenty-nine Census 2020 voting districts. The single "
                     "difference is Warren, which the county merged from Warren I "
                     "and Warren II — named singular by both the Clerk's certified "
                     "17 March 2026 results and the county GIS department's polling "
                     "map of 12 August 2026, a map that writes \"Dunleith I, II, "
                     "III\" where precincts share a building and so would have "
                     "written \"Warren I, II\" had there been two. No polling place "
                     "is carried: that is a roster fact wanting its own guard and "
                     "date. No board district either — those ship separately from a "
                     "licensed county shapefile, and nothing here reads them."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("jodaviess-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(COMPOSITION), county_pop))
    print("  merged: %s = %s (%d + %d = %d)"
          % (MERGED_PRECINCT, " + ".join(COMPOSITION[MERGED_PRECINCT]),
             vtds[V.norm("WARREN I")]["pop"], vtds[V.norm("WARREN II")]["pop"],
             pops[MERGED_PRECINCT]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "jodaviess")


if __name__ == "__main__":
    main()

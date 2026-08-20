#!/usr/bin/env python3
"""Build Calhoun County's five voting precincts from Census 2020 voting districts.

WHY THIS COUNTY NEEDED A NEW SHAPE. Calhoun is served through the County card
— its five commissioners are elected at large, so it has no board geometry and
never will — and its precincts were recorded as absent with the note that the
county "runs no mapping system" and publishes election files "in an unusual
form", the 2026 primary summary being "a raw printer file rather than a PDF".
Both halves of that read the wrong way round when they were re-measured on
2026-08-20. The county publishes no GEOMETRY, which was true. But the printer
file is HP PCL — ASCII with escape sequences — so stripping the escapes yields
cleaner text than the PDFs this fleet parses routinely, the county's own
Elections page serves its polling list as text, and the Illinois State Board of
Elections publishes precinct-level results as CSV for every election authority
in the state. The precinct list was never the obstacle it was recorded as.

THE COMPOSITION, AND WHY IT IS NOT A GUESS. Calhoun's five current precincts
are unions of WHOLE census voting districts, and the county wrote the
composition into their names:

    Belleview-Hamburg = BELLEVIEW + HAMBURG
    Hardin-Gilead     = HARDIN + GILEAD
    Crater-Carlin     = CRATER-CARLIN   (already one VTD; Crater and Carlin
                                         townships were merged before 2020)
    Point             = POINT
    Richwoods         = RICHWOODS

Three witnesses, none of them this project's own reading of a map:

  1. THE COUNTY'S OWN CERTIFIED RETURNS BRACKET THE MERGE. In the November 2022
     general the county ran exactly the seven census precincts; by November 2024
     it ran these five, and each merged precinct's registration equals the SUM
     of its two named components within the same two-year drift the three
     unmerged precincts show. A merge of whole precincts leaves that
     arithmetic; a redraw does not.
  2. THE NAMES SAY SO. Every merged precinct is named for both of its parts,
     which is the county describing its own composition.
  3. THE VOTING DISTRICTS ARE WHOLE TOWNSHIPS. Each of the seven is a township
     at an intersection-over-union of 1.000000 against TIGER's township layer,
     so the units being merged are the county's civil-township fabric rather
     than sub-township splits that could have moved.

WHY check_fabric IS THE WRONG GATE HERE, and what replaces it. The shared
module's Jasper test compares precinct NAMES against voting-district names
one-for-one. That is exactly right for Clark — one precinct per voting district
— and it rejects Calhoun, whose five precincts sit over seven voting districts
without its fabric having moved at all. check_fabric_composed keeps the half
that tests the fabric (the voting districts must still tile the county, which
the population identity proves) while check_partition supplies the other half
(every voting district claimed exactly once, none left over). Nothing is
relaxed: a composed county gets the same coverage from the pair that a
one-to-one county gets from check_fabric alone.

WHAT IS NOT SHIPPED. No polling place. The county publishes one — its Elections
page pairs each precinct with a building — but it is not in this file, because
this build's business is geometry and a polling place is a roster fact that
should arrive with a guard of its own and a date; it is recorded as available
in the gaps ledger instead. No board district either, and that is permanent
rather than pending: Calhoun elects its commissioners county-wide, so there is
no district for a precinct to belong to, and a `district` property here would
invent one.

Usage:
    python3 scripts/build_calhoun_precincts.py            # write
    python3 scripts/build_calhoun_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "calhoun-precincts.json")

COUNTY_FIPS = "013"
COUNTY_POP_2020 = 4437
EXPECTED_VTDS = 7
EXPECTED_PRECINCTS = 5

ELECTIONS_URL = "https://www.calhouncountyil.gov/government/county-clerk/elections/"
RESULTS_URL = ("https://www.elections.il.gov/ElectionOperations/"
               "ElectionVoteTotals.aspx")
SOURCE_LABEL = ("Census 2020 voting districts dissolved into the county's five "
                "current precincts, whose composition is named in the precincts' "
                "own titles and witnessed by the county's certified returns "
                "either side of the 2022-2024 merge")

# The composition. Keys are the county's own current precinct names, as its
# certified returns and its Elections page both spell them; values are the
# census voting districts each is made of.
COMPOSITION = {
    "Belleview-Hamburg": ["BELLEVIEW", "HAMBURG"],
    "Crater-Carlin": ["CRATER-CARLIN"],
    "Hardin-Gilead": ["HARDIN", "GILEAD"],
    "Point": ["POINT"],
    "Richwoods": ["RICHWOODS"],
}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


def fail(msg):
    print("calhoun-precincts: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


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

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Calhoun districts, "
             "expected %d — the fabric this build dissolves has changed shape"
             % (len(vtds), EXPECTED_VTDS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d" % (county_pop, COUNTY_POP_2020))

    V.check_fabric_composed(vtds, county_pop, fail)
    where = V.check_partition(COMPOSITION, vtds, fail)

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
                # The voting districts this precinct is made of, so a reader of
                # the file can check the composition against the county's
                # returns without re-deriving it.
                "votingDistricts": [V.title_case(n) for n in COMPOSITION[name]],
            },
            "geometry": V.round_geom(precincts[name], mapping),
        })

    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "electionsUrl": ELECTIONS_URL,
            "resultsUrl": RESULTS_URL,
            "note": ("Calhoun County's five precincts, dissolved from the seven "
                     "Census 2020 voting districts. Each merged precinct is named "
                     "for both of its parts (Belleview-Hamburg, Hardin-Gilead) and "
                     "the county's certified returns either side of the merge show "
                     "each one's registration equal to the sum of its components. "
                     "No board district is carried: Calhoun elects its five "
                     "commissioners county-wide, so there is none. No polling "
                     "place is carried either — the county publishes one, and it "
                     "belongs with a roster guard rather than in a geometry file."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("calhoun-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(COMPOSITION), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "calhoun")


if __name__ == "__main__":
    main()

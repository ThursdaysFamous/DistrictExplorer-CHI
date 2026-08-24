#!/usr/bin/env python3
"""Build Gallatin County's eleven voting precincts from Census 2020 voting districts.

HOW THIS COUNTY BECAME READABLE AT ALL, because the lesson generalises further
than Gallatin does. Its gap record said, as of 2026-08-20, that the county was
"DARK to this client on every route tried" and that its Clerk's own mail domain
"does not resolve at all". Both halves were wrong, and wrong for one reason:
gallatinco.illinois.gov serves an INCOMPLETE TLS CHAIN — the leaf without the
Sectigo intermediate that signs it. Browsers fetch the missing issuer from the
certificate's own Authority Information Access extension and say nothing;
requests, curl and every other automated client do not, and report a connection
failure that reads exactly like an absent host. That is the COLES PATTERN, and
this is the second county it has hidden. Supplying the intermediate the
certificate itself names — pinned by hash, verification never disabled — opened
the county in one step. See AIA_INTERMEDIATES in
scripts/il_county_commissioners_scraper.py, which does the same chase for the
roster.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE, and that is measured rather
than assumed. THE JASPER TEST PASSES 11/11: the census voting districts carry
Gallatin's eleven precinct names exactly, and their POP100 sums to the county's
own 2020 population of 4,946 to the person. No dissolve is needed and none is
performed — each precinct IS one voting district — so this file's geometry is
the census fabric relabelled with the county's spelling, nothing more.

THREE WITNESSES NAME THE SAME ELEVEN, none of them this project's own guess:

  1. THE COUNTY'S OWN PRECINCT MAP (Precient-map.pdf on the Clerk's elections
     page — the county's spelling of the filename, kept here so the link can be
     found) is a clean, fully legible plate labelling all eleven: Omaha, Asbury,
     New Haven, North Fork, Ridgway, Equality, Gold Hill 1, Gold Hill 2,
     Shawnee, Eagle Creek, Bowlesville. It has no text layer, so it is read as
     a picture and used only to corroborate names that arrive as text elsewhere.
  2. THE COUNTY'S CERTIFIED CANVASSES COUNT THEM. The 2026 General Primary
     summary reports "PRECINCTS COUNTED (OF 11)" over 3,489 registered voters.
  3. THE SAME CANVASSES NAME THEM. Precinct committeeperson contests are printed
     one per precinct, and across the 2024 and 2026 primaries they name Omaha,
     North Fork, Equality, Eagle Creek, Asbury, Ridgway, Gold Hill 1, Gold Hill 2
     and Bowlesville — nine of the eleven, every one of them in this set and not
     one name outside it.

NO BOARD DISTRICT SHIPS AND NONE EVER WILL. Gallatin elects its five county
board members COUNTYWIDE — proven twice from its own certified canvasses
("CO.BD.MEMBER CWD (VOTE FOR) 3" in 2026, "COUNTY BOARD MEMBER CWD (VOTE FOR) 2"
in 2024, where CWD is the marker every countywide office on those ballots
carries) — so there is no district for a precinct to belong to and a `district`
property here would invent one. The board rides the County card instead
(data/app/il-county-commissioners.json).

NO POLLING PLACE SHIPS. The county publishes a list (LIST-OF-POLLING-PLACES.docx
on the same page), and it belongs with a roster guard and a date rather than
inside a geometry file — the rule Calhoun's build set.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Gallatin
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_gallatin_precincts.py            # write
    python3 scripts/build_gallatin_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "gallatin-precincts.json")

COUNTY_FIPS = "059"
COUNTY_POP_2020 = 4946
EXPECTED_PRECINCTS = 11

ELECTIONS_URL = "https://gallatinco.illinois.gov/elections/"
PRECINCT_MAP_URL = ("https://gallatinco.illinois.gov/wp-content/uploads/2022/05/"
                    "Precient-map.pdf")
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "eleven precinct names Gallatin County's own precinct map and "
                "certified canvasses use")

# The county's eleven precincts, spelled as its own precinct map and its
# certified returns spell them. This list IS the Jasper test's input: the census
# fabric must carry these eleven names and no others.
COUNTY_PRECINCTS = (
    "ASBURY",
    "BOWLESVILLE",
    "EAGLE CREEK",
    "EQUALITY",
    "GOLD HILL 1",
    "GOLD HILL 2",
    "NEW HAVEN",
    "NORTH FORK",
    "OMAHA",
    "RIDGWAY",
    "SHAWNEE",
)

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("gallatin-precincts")


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
            "precinctMapUrl": PRECINCT_MAP_URL,
            "note": ("Gallatin County's eleven voting precincts. The Census 2020 "
                     "voting districts carry the county's own eleven precinct "
                     "names one for one and sum to its exact 2020 population, so "
                     "the fabric is the county's and nothing is dissolved. The "
                     "county's own precinct map labels the same eleven and its "
                     "certified canvasses count eleven and name nine of them. No "
                     "board district is carried: Gallatin elects its five board "
                     "members countywide, so there is none. No polling place is "
                     "carried either — the county publishes a list, and that "
                     "belongs with a roster guard rather than in a geometry file."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("gallatin-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "gallatin")


if __name__ == "__main__":
    main()

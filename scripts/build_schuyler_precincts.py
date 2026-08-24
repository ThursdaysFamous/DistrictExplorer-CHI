#!/usr/bin/env python3
"""Build Schuyler County's seventeen voting precincts from Census 2020 voting districts.

WHY THIS COUNTY HAD NO PRECINCT LAYER. Schuyler joined the ring on 2026-08-02
through the County card — seven board members elected countywide — and nothing was
blocking its precincts. There was simply no gap record saying they were missing,
which is how a county goes unbuilt while every guard in the repo stays green. The
2026-08-20 audit that found eleven such counties is the reason this file exists;
Schuyler is the LAST of the eight it named.

FIRST, A CORRECTION THIS BUILD FORCED, because it is the kind that wastes a whole
pass. The county's CLERK'S MAIL DOMAIN — schuylercountyil.gov, the address in
data/app/il-county-clerks.json — HAS NO A RECORD AT ALL, so the clerk-domain rule
that reached Cumberland, Massac and eighteen other counties does not reach this
one. Its actual site is www.schuylercounty.org, which this repo has been scraping
for the board roster since 2026-08-02. When the clerk-domain probe comes back
empty, check the scrapers before concluding anything.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 17/17
after one alias and their POP100 sums to the county's 2020 population of 6,902 to
the person. No dissolve is needed and none is performed.

ONE ALIAS, AND THE CENSUS IS THE ONE THAT IS WRONG. It writes FREDRICK where the
county writes FREDERICK, and Frederick is a real village in this county — so a
letter is missing from the census, not added by the county. This is the Hancock
shape (MONTIBELLO IV for Montebello 4) rather than Scott's, where the county's
results feed was the one dropping a letter. The alias renames the census feature
onto the county's spelling, which is also what ships on the card.

TWO COUNTY SOURCES, AND NEITHER IS A FULL CANVASS — which is why both are needed:

  1. THE COUNTY'S "POLLING PLACES BY PRECINCT" TABLE (schuylercounty.org/elections/
     voting-locations/) is the complete name list, and it GROUPS EXPLICITLY: three
     of its rows read "Buena Vista #1 & #2", "Rushville #1 & #2" and "Rushville #3
     & #4", one building serving two precincts apiece. Expanding those three rows
     gives seventeen, which is the number the county's own canvass reports. That
     ampersand is the difference between this table and Cumberland's polling
     notice, where the grouping was implicit in a heading and cost that build a
     wrong prediction.
  2. THE COUNTY'S OWN ELECTION-RESULTS SITE (elections.schuyler.il.us) carries the
     2026 General Primary, marked Official, reading "Precincts Reporting 17 of 17 =
     100.00%". It is a COUNTY-RUN results database — the second this project has
     found, after Hancock's — but its report is CUMULATIVE, so it names only the
     three precincts where a committeeperson contest was filed (Buenavista 1,
     Huntsville, Rushville 4). It confirms the COUNT and three of the names; the
     polling table supplies the rest.

The same canvass carries "FOR MEMBERS OF THE COUNTY BOARD - (Vote for not more than
four)" over all seventeen precincts and no district-suffixed board contest, which
re-confirms from a certified document what the County card already says: SCHUYLER
ELECTS ITS BOARD COUNTYWIDE, so NO BOARD DISTRICT SHIPS and there is no district
for a precinct to belong to.

BUENA VISTA KEEPS ITS SPACE. The census and the county's results feed both compress
it to BUENAVISTA; the township is Buena Vista, and the polling table writes it that
way, so the shipped label does too — the Du Quoin decision applied to a second
county.

NO POLLING PLACE SHIPS. The county publishes the table above and it belongs with a
roster guard and a date, which is the rule Calhoun's build set.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Schuyler
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_schuyler_precincts.py            # write
    python3 scripts/build_schuyler_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "schuyler-precincts.json")

COUNTY_FIPS = "169"
COUNTY_POP_2020 = 6902
EXPECTED_PRECINCTS = 17

POLLING_URL = "https://www.schuylercounty.org/elections/voting-locations/"
RESULTS_URL = "https://www.elections.schuyler.il.us/"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "seventeen precinct names Schuyler County's own polling-place "
                "table and its county-run results site use")

# The county's seventeen precincts, spelled as its own polling table spells them,
# with its three "&" rows expanded. This list IS the Jasper test's input AND the
# shipped labels.
COUNTY_PRECINCTS = (
    "BAINBRIDGE",
    "BIRMINGHAM",
    "BROOKLYN",
    "BROWNING",
    "BUENA VISTA 1",
    "BUENA VISTA 2",
    "CAMDEN",
    "FREDERICK",
    "HICKORY",
    "HUNTSVILLE",
    "LITTLETON",
    "OAKLAND",
    "RUSHVILLE 1",
    "RUSHVILLE 2",
    "RUSHVILLE 3",
    "RUSHVILLE 4",
    "WOODSTOCK",
)

# County spelling -> census BASENAME. ONE, and the census is the source at fault:
# Frederick is a village in this county and the census drops its middle E.
ALIASES = {
    "FREDERICK": "FREDRICK",
}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("schuyler-precincts")


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
    V.apply_aliases(vtds, ALIASES, fail)

    # The Jasper test proper: names one-for-one AND the population identity.
    V.check_fabric(vtds, COUNTY_PRECINCTS, county_pop, fail)

    # One voting district per precinct, LABELLED FROM THE COUNTY'S OWN SPELLING —
    # which keeps Buena Vista its space and Frederick its E. check_partition still
    # runs, because it is what proves nothing is claimed twice and nothing is left
    # over.
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
            "pollingUrl": POLLING_URL,
            "resultsUrl": RESULTS_URL,
            "note": ("Schuyler County's seventeen voting precincts. The Census 2020 "
                     "voting districts carry the county's own seventeen precinct "
                     "names one for one and sum to its exact 2020 population, so "
                     "the fabric is the county's and nothing is dissolved. The name "
                     "list is the county's \"Polling Places by Precinct\" table, "
                     "whose three \"& \" rows each serve two precincts from one "
                     "building; the count is confirmed by the county's OWN results "
                     "site, which reads \"Precincts Reporting 17 of 17\" on an "
                     "official 2026 General Primary. One alias is applied and the "
                     "census is the source at fault: it writes FREDRICK where the "
                     "county — and the village — write Frederick. Buena Vista keeps "
                     "its space, which the census and the results feed both drop. "
                     "NO BOARD DISTRICT is carried and none ever will be: the same "
                     "canvass carries a single countywide MEMBERS OF THE COUNTY "
                     "BOARD contest over all seventeen precincts, so Schuyler's "
                     "seven members ride the County card. No polling place ships "
                     "either — that belongs with a roster guard and a date."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("schuyler-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "schuyler")


if __name__ == "__main__":
    main()

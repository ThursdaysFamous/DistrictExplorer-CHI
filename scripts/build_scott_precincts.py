#!/usr/bin/env python3
"""Build Scott County's ten voting precincts from Census 2020 voting districts.

WHY THIS COUNTY HAD NO PRECINCT LAYER. Scott has been served since a 7th-Circuit
subcircuit answered here. Nothing was blocking its precincts; there was simply no
gap record saying they were missing, which is how a county goes unbuilt while every
guard in the repo stays green. The 2026-08-20 audit that found eleven such counties
is the reason this file exists.

THE PRECINCTS ARE THE CENSUS FABRIC, ONE FOR ONE. THE JASPER TEST PASSES 10/10 and
their POP100 sums to the county's 2020 population of 4,949 to the person.

ONE SPELLING IS RECORDED RATHER THAN CHOSEN BETWEEN, and it is decided the opposite
way from Greene's. The county's results feed writes MERRIT where the census writes
MERRITT — and MERRITT is the name of the township, so the feed has dropped a letter
rather than the census having added one. That is a misspelling, not a designation,
so no alias is applied: COUNTY_PRECINCTS below carries the county's rendering,
because that is what the Jasper test must match, while the shipped feature is
LABELLED from the census basename, because a reader in Merritt Township should not
be told they live in "Merrit". Both renderings are therefore in this file's
provenance and neither is silently preferred. (Contrast Greene, where WRIGHTS 2
against the census's WRIGHTS is a number the county attaches, and the county wins.)

THE ROMAN NUMERALS ARE REAL. Scott's county seat precincts are WINCHESTER I, II and
III in the county's returns AND in the census BASENAMEs — unlike Cumberland, where
roman numerals turned out to be polling-place groupings rather than precinct names.
Check which one you are looking at before normalising either.

THE NAMES COME FROM THE COUNTY'S OWN CERTIFIED RETURNS, one contest at a time. Its
2026 General Primary, published by the Clerk's election-results publisher
(results.gbsvote.com), prints a precinct committeeperson contest per precinct per
party and its header reads "10 OF 10 PRECINCTS REPORTING".

NO BOARD DISTRICT SHIPS AND NONE EVER WILL. The same canvass carries a single
countywide "FOR COUNTY COMMISSIONER" contest per party over all ten precincts, so
Scott elects its board county-wide and there is no district for a precinct to
belong to.

NO POLLING PLACE SHIPS — that belongs with a roster guard and a date.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Scott
re-precincts or TIGERweb republishes the voting-district fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_scott_precincts.py            # write
    python3 scripts/build_scott_precincts.py --check    # verify shipped == fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "scott-precincts.json")

COUNTY_FIPS = "171"
COUNTY_POP_2020 = 4949
EXPECTED_PRECINCTS = 10

RESULTS_URL = "https://results.gbsvote.com/locations/counties.asp?p_id=3&l_id=19"
SOURCE_LABEL = ("Census 2020 voting districts, one per precinct, carrying the "
                "ten precinct names Scott County's certified 2026 "
                "General Primary names one committeeperson contest at a time")

# The county's ten precincts, spelled as its own certified returns spell
# them. This list IS the Jasper test's input: the census fabric must carry these
# ten names and no others.
COUNTY_PRECINCTS = (
    "ALSEY",
    "BLOOMFIELD",
    "EXETER-BLUFFS",
    "GLASGOW",
    "MANCHESTER",
    "MERRIT",
    "NAPLES-BLUFFS",
    "WINCHESTER I",
    "WINCHESTER II",
    "WINCHESTER III",
)

# County spelling -> census BASENAME. ONE, and it is handled in an unusual
# direction: the alias exists so the Jasper test can compare the county's OWN
# list, while the shipped LABEL comes from the census name that the alias
# displaces. apply_aliases records the displaced spelling as censusName, which is
# what makes that possible without a second lookup.
ALIASES = {
    "MERRIT": "MERRITT",
}

MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

fail = make_fail("scott-precincts")


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

    # One voting district per precinct, LABELLED from the CENSUS name — which for
    # the one aliased precinct is the spelling apply_aliases displaced, so
    # Merritt Township keeps its own name where the county's feed drops a letter.
    # check_partition still runs, because it is what proves nothing is claimed
    # twice and nothing is left over — the guard that would catch a future
    # re-precincting that kept the same count.
    composition = {}
    for precinct in COUNTY_PRECINCTS:
        rec = vtds[V.norm(precinct)]
        label = V.title_case(rec.get("censusName") or rec["basename"])
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
            "note": ("Scott County's ten voting precincts. The Census 2020 voting districts "
                     "carry the county's own ten precinct names and sum to its exact 2020 "
                     "population, so the fabric is the county's and nothing is dissolved. "
                     "The names and the count both come from the county's certified 2026 "
                     "General Primary, which prints a committeeperson contest per precinct "
                     "per party and reads \"10 OF 10 PRECINCTS REPORTING\". Each feature is "
                     "labelled from the census basename, so Merritt Township keeps its own "
                     "name where the county's results feed drops a letter and writes "
                     "MERRIT. The Winchester roman numerals, by contrast, are real: the "
                     "county and the census both write WINCHESTER I, II and III. NO BOARD "
                     "DISTRICT is carried and none ever will be — the same canvass carries "
                     "a single countywide COUNTY COMMISSIONER contest over all ten "
                     "precincts. No polling place ships either."),
        },
        "features": features,
    }

    body = V.dumps(payload)
    print("scott-precincts: %d voting districts -> %d precincts (pop %d = census "
          "POP100)" % (len(vtds), len(composition), county_pop))
    print("  %s" % ", ".join("%s=%d" % (n, pops[n]) for n in sorted(pops)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, body)], args.check, REPO_ROOT, fail, "scott")


if __name__ == "__main__":
    main()

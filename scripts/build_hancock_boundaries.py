#!/usr/bin/env python3
"""
Build data/app/hancock-county-board-districts.json — Hancock County's 5 County
Board districts, dissolved from the Census 2020 voting districts per a
composition the county's OWN CERTIFIED RETURNS state, precinct by precinct.

THE SOURCE IS A COUNTY-RUN RESULTS DATABASE, and it is the first of its kind
this project has met. Hancock's Clerk publishes every contest back to at least
2020 at electionstats.hancockcounty-il.gov — not a vendor's portal keyed by
county id, but the county's own "Clerk Elections Database", and each contest
page carries a PER-PRECINCT results table. So a County Board district contest
does not merely report how MANY precincts voted in it, the way Knox's and
Richland's canvasses do; it names them, one row each. That is the difference
between a county that can be built and a county that cannot, and it is worth
looking for on any county site that offers "previous election results".

TWO WITNESSES PER DISTRICT, WHICH IS THE STANDARD CLARK SET. The 17 Mar 2026
Democratic primary carries all five district contests (ids 3222-3226) and the
28 Jun 2022 primary carries all five again (ids 45-49); the 19 Mar 2024 primary
re-confirms four of the five (2995-2998, District 1 unopposed that cycle). Every
district's precinct list is IDENTICAL across all of them, and both 2022 and 2026
are post-2021-redistricting, so no district rests on a single document.

THE PARTITION IS EXACT: 6 + 8 + 8 + 5 + 6 = 33 precinct slots, 33 distinct
names, none claimed twice and none left over. Hancock runs 33 precincts.

THE JASPER TEST PASSES 33/33 with the population identity to the person — the
census voting districts sum to Hancock's exact 17,620. Thirteen names differ in
SPELLING ONLY, the roman/arabic normalisation already recorded for Clay and
Cumberland: the census writes CARTHAGE I where the county writes Carthage 1.
ONE OF THE THIRTEEN IS A CENSUS TYPO rather than a numeral convention — the
census spells Montebello 4 as "MONTIBELLO IV", with an I, while writing
MONTEBELLO I, II and III correctly. It is aliased like the rest and named here
so nobody reads it as a different place.

THE POPULATION SPREAD IS 9.3%: 3,345 to 3,673 against a 3,524 ideal, every
district within 5.1% of it. That is an adopted plan's balance.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Hancock
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_hancock_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "hancock-county-board-districts.json")
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "hancock-precincts.json")

COUNTY_FIPS = "067"
COUNTY_POP_2020 = 17620
EXPECTED_VTDS = 33            # census 2020 voting districts
COUNTY_PRECINCTS = 33         # what the county runs today — the same 33

BOARD_URL = "https://hancockcounty-il.gov/county-board-members/"
RESULTS_URL = "https://electionstats.hancockcounty-il.gov/"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the per-precinct "
                "County Board district contests in Hancock County's own "
                "certified results database")

# county precinct spelling -> census BASENAME. Thirteen differences, all of them
# numeral convention (the county writes 1-4, the census writes I-IV) except
# MONTIBELLO IV, which is the census misspelling Montebello. A rename, never a
# merge: apply_aliases refuses if any target is missing or already taken.
CENSUS_SPELLING = {
    "CARTHAGE 1": "CARTHAGE I", "CARTHAGE 2": "CARTHAGE II",
    "CARTHAGE 3": "CARTHAGE III", "CARTHAGE 4": "CARTHAGE IV",
    "LAHARPE 1": "LAHARPE I", "LAHARPE 2": "LAHARPE II",
    "MONTEBELLO 1": "MONTEBELLO I", "MONTEBELLO 2": "MONTEBELLO II",
    "MONTEBELLO 3": "MONTEBELLO III", "MONTEBELLO 4": "MONTIBELLO IV",
    "WARSAW 1": "WARSAW I", "WARSAW 2": "WARSAW II", "WARSAW 3": "WARSAW III",
}

# Keyed by district, valued by the county's OWN precinct names exactly as its
# results database prints them. Re-keyed onto census geometry by the aliases
# above, so this table stays readable against the county's own publications.
COMPOSITION = {
    "1": ("APPANOOSE", "DALLAS CITY", "NAUVOO", "PONTOOSUC", "ROCK CREEK",
          "SONORA"),
    "2": ("AUGUSTA", "DURHAM", "FOUNTAIN GREEN", "HANCOCK", "LAHARPE 1",
          "LAHARPE 2", "PILOT GROVE", "ST. MARYS"),
    "3": ("BEAR CREEK", "CHILI", "ROCKY RUN-WILCOX", "ST. ALBANS", "WALKER",
          "WARSAW 1", "WARSAW 2", "WARSAW 3"),
    "4": ("MONTEBELLO 1", "MONTEBELLO 2", "MONTEBELLO 3", "MONTEBELLO 4",
          "WYTHE"),
    "5": ("CARTHAGE 1", "CARTHAGE 2", "CARTHAGE 3", "CARTHAGE 4", "HARMONY",
          "PRAIRIE"),
}

BALANCE_DEV_MAX = 0.30        # measured 0.051 worst district; 9.3% max-to-min
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("hancock-boundaries")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    claimed = [n for names in COMPOSITION.values() for n in names]
    if len(claimed) != COUNTY_PRECINCTS:
        fail("the composition names %d precinct slots, expected %d"
             % (len(claimed), COUNTY_PRECINCTS))
    if len(set(claimed)) != len(claimed):
        dupes = sorted({n for n in claimed if claimed.count(n) > 1})
        fail("these precincts are claimed by more than one district: %s — a "
             "district contest naming a shared precinct means the districts are "
             "not unions of whole precincts" % ", ".join(dupes))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Hancock features, "
             "expected %d" % (len(vtds), EXPECTED_VTDS))
    V.apply_aliases(vtds, CENSUS_SPELLING, fail)
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d"
             % (county_pop, COUNTY_POP_2020))
    # THE JASPER TEST, on the county's own 33 names after the spelling aliases.
    V.check_fabric(vtds, claimed, county_pop, fail)
    where = V.check_partition(COMPOSITION, vtds, fail)

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
                           "precincts": [V.title_case(p)
                                         for p in COMPOSITION[dnum]],
                           "pop2020": pops[dnum]},
            "geometry": V.round_geom(districts[dnum], mapping),
        })
    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "boardUrl": BOARD_URL,
            "resultsUrl": RESULTS_URL,
            "composition": ("Hancock County's own certified results database "
                            "publishes each County Board district contest with "
                            "a PER-PRECINCT results table, so each district's "
                            "precinct list is stated one row at a time rather "
                            "than inferred. The five lists agree exactly across "
                            "the 2022 and 2026 primaries, with 2024 "
                            "re-confirming four of the five."),
            "note": ("Five districts of three members each, dissolved from the "
                     "Census 2020 voting districts. The 33 census units are the "
                     "county's own 33 precincts 33/33 and sum to its exact 2020 "
                     "population of 17,620; thirteen names differ in spelling "
                     "only, the roman/arabic convention (CARTHAGE I for Carthage "
                     "1), one of which is a census typo for Montebello 4 "
                     "(MONTIBELLO IV). Populations run 3,345 to 3,673 against a "
                     "3,524 ideal."),
        },
        "features": features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, features, point_in_rings, fail)

    # ---- the precincts themselves -----------------------------------------
    # Nothing new is sourced here. The 33 census units ARE the county's 33
    # precincts — that is what the Jasper test above establishes — and the
    # composition already says which district each belongs to. This absence had
    # no gap record explaining it, which is the only reason it went unbuilt.
    # THE COUNTY'S SPELLING SHIPS, not the census's: apply_aliases renamed the
    # census features onto the names Hancock's own results database prints, and
    # one of those census names (MONTIBELLO IV) is a typo for Montebello 4.
    precinct_features = []
    for key in sorted(vtds, key=lambda k: vtds[k]["basename"]):
        rec = vtds[key]
        props = {"name": V.title_case(rec["basename"]), "geoid": rec["geoid"],
                 "pop2020": rec["pop"], "district": where[key]}
        if rec.get("censusName") and rec["censusName"] != rec["basename"]:
            # Kept so a reader who looks the precinct up in census products can
            # find it, and so the typo is visible rather than silently corrected.
            props["censusName"] = V.title_case(rec["censusName"])
        precinct_features.append({"type": "Feature", "properties": props,
                                  "geometry": V.round_geom(rec["geom"], mapping)})
    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "boardUrl": BOARD_URL,
            "resultsUrl": RESULTS_URL,
            "note": ("Hancock County's 33 voting precincts are the Census 2020 "
                     "voting districts, which ARE the county's own fabric: they "
                     "carry its 33 precinct names 33/33 as its certified "
                     "results database prints them, and sum to its exact 2020 "
                     "population of 17,620. Thirteen names differ in spelling "
                     "only — the roman/arabic convention (CARTHAGE I for "
                     "Carthage 1) — and one is a census TYPO, MONTIBELLO IV for "
                     "Montebello 4. The county's spelling is what ships; where "
                     "the census differs, its own name rides the feature as "
                     "censusName rather than being silently corrected away. "
                     "Every precinct carries its County Board district, because "
                     "Hancock's districts are unions of WHOLE precincts. No "
                     "polling place ships: a polling place is a roster fact "
                     "rather than geometry (the Calhoun rule)."),
        },
        "features": precinct_features,
    }

    body = V.dumps(payload)
    prec_body = V.dumps(precincts_payload)
    print("hancock-boundaries: %d census voting districts -> %d districts"
          % (EXPECTED_VTDS, len(COMPOSITION)))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    aliased = sum(1 for k in vtds
                  if vtds[k].get("censusName")
                  and vtds[k]["censusName"] != vtds[k]["basename"])
    print("  precincts: %d shipped, each carrying its district (%d census names "
          "differ from the county's and ride the feature as censusName)"
          % (len(precinct_features), aliased))
    V.write_or_check([(OUT_DISTRICTS, body), (OUT_PRECINCTS, prec_body)],
                     args.check, REPO_ROOT, fail, "hancock")


if __name__ == "__main__":
    main()

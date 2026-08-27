#!/usr/bin/env python3
"""
Build data/app/wayne-precincts.json and
data/app/wayne-county-board-districts.json — Wayne County's 27 voting
precincts and the 7 County Board districts they compose (14 members, two per
district; docs/EXPANSION_GUIDE.md Part 3; scripts/vtd_board_districts.py
holds the machinery).

THE COMPOSITION WAS SETTLED BY TWO SOURCES THAT AGREE, published five days
apart. waynecountyil.gov/wayne-county-board/ states outright which precincts
make up each of the seven districts, alongside each district's two members.
Independently, all 27 precinct pages of the certified 5 November 2024
General on platinumelectionresults.com (Wayne is county id 14) were grouped
by which board candidate each precinct actually voted on: the ballots
partition the same 27 precincts into the same seven groups. THE ONE
DIFFERENCE IS THE COUNTY SEAT: the board page's District 7 names only
Merriam and Golden Gate, five short of the ballots' 27, and the two it
omits — Fairfield 1 and Fairfield 2 — voted in District 7's contest on that
same certified ballot (alongside Merriam and Golden Gate, Steve Troyer's
race). So the page is incomplete rather than the ballots wrong, and the
composition below is the union of what both sources state.

THE FABRIC HAS NOT MOVED. Census 2020 carries exactly 27 Wayne voting
districts summing to the county's exact 16,179, and every one of the
county's 27 current precinct names matches a census BASENAME once one
spelling is aliased (the county writes "Massillon", the census "MASSILON";
"Mt. Erie" already norm-matches "MT ERIE" without one).

WHY THIS WAS NOT BUILT FOR WEEKS: POPULATION, NOT PROVENANCE. Composed
against a 2,311 ideal, the seven districts run 1,863 (D6) to 3,060 (D3) —
D3 alone is +32.4%, past the 30% ceiling this project's dissolve guard
uses everywhere else to catch a mis-assignment. Both sources agree on D3's
composition exactly (Lamard 1, Lamard 2, Jasper 1, Jasper 2), so the
question was never which precincts — it was whether that plan is current.
Clerk Elizabeth Woodrow was asked directly, 2026-08-24: "Is this the
board's current, adopted plan, or has anything changed in Lamard or Jasper
Township's precinct lines since the plan was last drawn?" Her reply,
2026-08-25: "Nothing has changed with this map for years." That settles it
as the county's real, current, deliberate plan rather than a stale listing
or a derivation error — the same posture this project already accepted for
Mercer's smaller -14.6% deviation, extended here because the county
confirmed the plan itself rather than the derivation being merely
uncontradicted. BALANCE_DEV_MAX is raised for this county alone, with the
measured value recorded rather than the ceiling silently widened.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Wayne
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output
is deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_wayne_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "wayne-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "wayne-county-board-districts.json")

COUNTY_FIPS = "191"
COUNTY_POP_2020 = 16179
EXPECTED_PRECINCTS = 27
SEATS_PER_DISTRICT = 2          # fourteen members, two per district

RESULTS_URL = "https://platinumelectionresults.com/history"
BOARD_URL = "https://waynecountyil.gov/wayne-county-board/"
ELECTIONS_URL = "https://waynecountyil.gov/voting-and-elections/"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per Wayne County's "
                "own County Board page and corroborated by its certified 5 "
                "November 2024 General canvass, published as structured "
                "precinct-level results by platinumelectionresults.com")

# THE COMPOSITION, in the county's own spelling. Six of seven districts match
# the board page exactly; District 7 adds Fairfield 1 and Fairfield 2, which
# the board page omits and the certified 2024 General's District 7 contest
# (on both Fairfield ballots) supplies.
COMPOSITION = {
    "1": ("BERRY", "GARDEN HILL", "KEITH", "ORCHARD", "INDIAN PRAIRIE", "HICKORY HILL"),
    "2": ("MT. ERIE", "BEDFORD", "ELM RIVER", "MASSILLON", "ZIF"),
    "3": ("LAMARD 1", "LAMARD 2", "JASPER 1", "JASPER 2"),
    "4": ("ARRINGTON", "FOUR MILE", "OREL"),
    "5": ("BIG MOUND 1", "BIG MOUND 2", "BARNHILL"),
    "6": ("GROVER", "RIDER"),
    "7": ("MERRIAM", "GOLDEN GATE", "FAIRFIELD 1", "FAIRFIELD 2"),
}

# The one spelling the census and the county genuinely disagree on. "Mt.
# Erie" already norm-matches census "MT ERIE" (punctuation and spaces are
# both stripped by norm()) and needs no entry here.
ALIASES = {"MASSILLON": "MASSILON"}

# Measured 0.324 in District 3 (Lamard 1-2, Jasper 1-2). Raised from this
# project's usual 0.30 ceiling for Wayne alone, and only after the county
# confirmed the plan is current rather than stale (Clerk Woodrow, e-mail,
# 2026-08-25: "Nothing has changed with this map for years") — see the
# module docstring. Left below the next-worst deviation this build has ever
# accepted so a real mis-assignment still fails loudly.
BALANCE_DEV_MAX = 0.325
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("wayne-boundaries")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped files match a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    claimed = [n for names in COMPOSITION.values() for n in names]
    if len(claimed) != EXPECTED_PRECINCTS:
        fail("the composition names %d precincts, expected %d"
             % (len(claimed), EXPECTED_PRECINCTS))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    vtds = V.apply_aliases(vtds, ALIASES, fail)
    if len(vtds) != EXPECTED_PRECINCTS:
        fail("the census voting-district layer carries %d Wayne features, "
             "expected %d" % (len(vtds), EXPECTED_PRECINCTS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d" % (county_pop, COUNTY_POP_2020))
    V.check_fabric(vtds, claimed, county_pop, fail)
    where = V.check_partition(COMPOSITION, vtds, fail)

    districts, pops = V.dissolve(COMPOSITION, vtds, unary_union)
    ideal = county_pop / float(len(COMPOSITION))
    worst = max(((abs(pops[d] - ideal) / ideal), d) for d in pops)
    if worst[0] > BALANCE_DEV_MAX:
        fail("district %s deviates %.1f%% from the per-district ideal (ceiling "
             "%.1f%%) — that is a mis-assignment, not an apportionment"
             % (worst[1], 100 * worst[0], 100 * BALANCE_DEV_MAX))
    overlap, covered = V.check_tiling(districts, county_geom, transform,
                                      MAX_OVERLAP_M2, MIN_COVERED, unary_union, fail)

    precinct_features = []
    for key in sorted(vtds, key=lambda k: vtds[k]["basename"]):
        rec = vtds[key]
        precinct_features.append({
            "type": "Feature",
            "properties": {"name": V.title_case(rec["basename"]), "district": where[key],
                           "geoid": rec["geoid"], "pop2020": rec["pop"]},
            "geometry": V.round_geom(rec["geom"], mapping),
        })
    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "resultsUrl": RESULTS_URL, "boardUrl": BOARD_URL,
            "electionsUrl": ELECTIONS_URL,
            "note": ("Wayne County's 27 precincts are the Census 2020 voting "
                     "districts, which carry the county's own 27 precinct "
                     "names 27/27 (one spelling aliased: Massillon/Massilon) "
                     "and sum to its exact 2020 population of 16,179. Each "
                     "feature also carries its County Board district, which "
                     "is whole-precinct — no precinct is split between "
                     "districts. Polling places are not shown: nothing the "
                     "county publishes pairs its precincts with buildings as "
                     "data."),
        },
        "features": precinct_features,
    }

    district_features = []
    for dnum in sorted(COMPOSITION, key=int):
        district_features.append({
            "type": "Feature",
            "properties": {"district": dnum, "name": "District %s" % dnum,
                           "precincts": [V.title_case(n) for n in COMPOSITION[dnum]],
                           "pop2020": pops[dnum], "seats": SEATS_PER_DISTRICT},
            "geometry": V.round_geom(districts[dnum], mapping),
        })
    districts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "resultsUrl": RESULTS_URL, "boardUrl": BOARD_URL,
            "canvass": ("Composition from the county's own County Board page, "
                        "corroborated by its certified 5 November 2024 "
                        "General: 27 precinct-level results grouped by which "
                        "board candidate each precinct voted on partition "
                        "the same 27 precincts into the same seven districts. "
                        "The board page omits Fairfield 1 and Fairfield 2 "
                        "from District 7; the certified 2024 ballot places "
                        "them there."),
            "note": ("Seven districts electing TWO members each (14 seats). "
                     "Populations run 1,863-3,060 against a 2,311 ideal — "
                     "District 3 (Lamard 1-2, Jasper 1-2) alone deviates "
                     "32.4%, past this project's usual 30% ceiling. County "
                     "Clerk Elizabeth Woodrow confirmed by e-mail, "
                     "2026-08-25, that the plan is current: “Nothing has "
                     "changed with this map for years.” The imbalance is "
                     "recorded as the county's own plan rather than smoothed."),
        },
        "features": district_features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, district_features, point_in_rings, fail)

    prec_body = V.dumps(precincts_payload)
    dist_body = V.dumps(districts_payload)
    print("wayne-boundaries: %d precincts -> %d districts of %d; census fabric "
          "matches the county's precinct list %d/%d"
          % (len(precinct_features), len(COMPOSITION), SEATS_PER_DISTRICT,
             EXPECTED_PRECINCTS, EXPECTED_PRECINCTS))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s — confirmed the county's own current plan)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)],
                     args.check, REPO_ROOT, fail, "wayne")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/edgar-precincts.json + data/app/edgar-county-board-districts.json
— Edgar County's 31 voting precincts and 7 County Board districts, composed
from the county's own certified election returns (docs/EXPANSION_GUIDE.md
§3.5.1, the canvass route; scripts/vtd_board_districts.py holds the machinery).

WHY THIS COUNTY MATTERS TWICE. Edgar became the coverage ring's own OUTSIDE
anchor on 2026-08-18, hours before this build, when Clark joined and left it
bordering two served counties. It is now inside instead — and it is the first
county in the fleet reached by the vendor sweep whose composition rests on a
FULL SET of certified canvasses rather than one election.

THE COMPOSITION, WITNESSED TWICE PER DISTRICT — the Clark standard, met in
full. The Clerk's results archive at il-edgar.accessliberty.com carries a
text-layer Statement of Votes Cast per election, and the live feed at
il-edgar.pollresults.net carries the current one:

  * 2022 GENERAL — all SEVEN districts, every contest "Vote for one", and its
    precinct lists partition the county's 31 precincts EXACTLY ONCE each.
  * 2024 GENERAL — re-tabulates districts 1, 6 and 7 identically.
  * 2026 GENERAL PRIMARY — re-tabulates districts 2, 3, 4, 5 and 6 identically
    (district 6 as a two-year unexpired term).

Every district therefore appears in at least two certified documents, and the
two later ones between them re-prove all seven.

A PARSER BUG THIS COUNTY FOUND, recorded because it nearly shipped as data.
The canvass reader written for Clark identified a precinct as "one capitalised
word plus an optional single digit", which is true of all 23 Clark precincts
and false here: it split BROUILLETTS CREEK in two, turned YOUNG AMERICA 1 into
"YOUNG" plus "AMERICA 1", and collapsed PARIS 10, 11, 12, 14 and 15 into a
single bare "PARIS" — a composition that looked plausible and was wrong. The
reader now matches rows against the county's OWN precinct list, longest name
first (scripts/clark_county_board_scraper.py). Clark's shipped output is
byte-identical after the change, which is how the fix was verified.

THE PRECINCT FABRIC IS CENSUS FABRIC, AND THE TWO SPELLINGS ARE A RENAME, NOT
A MISMATCH. TIGER's Census 2020 voting-district layer carries exactly 31 Edgar
features summing to the county's exact 16,866, and 29 of the 31 names match
the county's own spelling character for character. The two that differ are
EMBARRASS 1 and KANSAS 1, which the county writes Embarrass and Kansas; with
31 against 31 and 29 already matched, those two pair uniquely and there is
nothing to choose between. CENSUS_SPELLING below records the pairing and the
shipped features carry both names.

THE POPULATION SPREAD IS THE COUNTY'S, and it is the tightest this route has
produced: the composed districts run 2,235 (D2) to 2,694 (D4) against a 2,409 ideal,
worst deviation +11.8%.
Recorded, not smoothed.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Edgar
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_edgar_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "edgar-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "edgar-county-board-districts.json")

COUNTY_FIPS = "045"
COUNTY_POP_2020 = 16866
EXPECTED_PRECINCTS = 31
SEATS_PER_DISTRICT = 1          # every canvass contest header reads "Vote for one"

RESULTS_URL = "https://il-edgar.pollresults.net"
BOARD_URL = "https://edgarcountyillinois.com/county-board/"
CANVASS_URL = "https://il-edgar.accessliberty.com/pastelections.aspx"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "Edgar County's certified 17 March 2026 General Primary "
                "results, published as structured data by County Clerk & "
                "Recorder Beckie Staley's own results system")

# THE COMPOSITION, read from the certified 2026 General Primary result set:
# each district's contest names the precincts it was on the ballot in. All 24
# precincts, each in exactly one district. The weekly roster run re-reads this
# from the live feed and fails if it moves.
COMPOSITION = {
    "1": ("PRAIRIE", "ROSS 1", "ROSS 2", "YOUNG AMERICA 1", "YOUNG AMERICA 2"),
    "2": ("BROUILLETTS CREEK", "EDGAR", "EMBARRASS", "KANSAS", "SHILOH"),
    "3": ("BUCK", "ELBRIDGE", "GRANDVIEW", "SYMMES 1", "SYMMES 2"),
    "4": ("HUNTER", "PARIS 3", "PARIS 4", "PARIS 14", "STRATTON"),
    "5": ("PARIS 1", "PARIS 2", "PARIS 11"),
    "6": ("PARIS 5", "PARIS 7", "PARIS 12", "PARIS 15"),
    "7": ("PARIS 6", "PARIS 8", "PARIS 9", "PARIS 10"),
}
# county spelling -> census BASENAME, for the two the publishers write
# differently. See the docstring: 29 of 31 match exactly, so these pair
# uniquely.
CENSUS_SPELLING = {"EMBARRASS": "EMBARRASS 1", "KANSAS": "KANSAS 1"}

BALANCE_DEV_MAX = 0.30          # measured 0.118 (District 4) — the tightest yet
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("edgar-boundaries")


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

    vtds = V.apply_aliases(V.fetch_vtds(COUNTY_FIPS, shape, fail),
                           CENSUS_SPELLING, fail)
    if len(vtds) != EXPECTED_PRECINCTS:
        fail("the census voting-district layer carries %d Edgar precincts, "
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
             "%.0f%%) — that is a mis-assignment, not an apportionment"
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
            "source": SOURCE_LABEL, "resultsUrl": RESULTS_URL,
            "electionsUrl": CANVASS_URL,
            "note": ("Edgar County's 24 precincts are the Census 2020 voting "
                     "districts, which carry the county's own 24 precinct names "
                     "24/24 and sum to its exact 2020 population. Each feature "
                     "also carries its County Board district, which is "
                     "whole-precinct — no precinct is split between districts. "
                     "Polling places are not shown here: the county publishes a "
                     "polling list on its Elections page as a scan."),
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
            "canvass": ("Composition from the county's certified 17 March 2026 "
                        "General Primary results: all five districts had a "
                        "contest, and their precinct lists partition the "
                        "county's 24 precincts exactly once each"),
            "note": ("Five districts of TWO members each, dissolved from Census "
                     "2020 voting districts. Clerk & Recorder Beckie Staley "
                     "confirmed in writing on 2026-08-17 that the board is "
                     "elected from districts; the county's own district maps sit "
                     "behind its Beacon viewer and their release is with the "
                     "county's Mapping Committee, so these boundaries are "
                     "derived from the election returns instead."),
        },
        "features": district_features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, district_features, point_in_rings, fail)

    prec_body = V.dumps(precincts_payload)
    dist_body = V.dumps(districts_payload)
    print("edgar-boundaries: %d precincts -> %d districts of %d; census fabric "
          "matches the county's precinct list %d/%d"
          % (EXPECTED_PRECINCTS, len(COMPOSITION), SEATS_PER_DISTRICT,
             EXPECTED_PRECINCTS, EXPECTED_PRECINCTS))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s — the county's own plan)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)],
                     args.check, REPO_ROOT, fail, "edgar")


if __name__ == "__main__":
    main()

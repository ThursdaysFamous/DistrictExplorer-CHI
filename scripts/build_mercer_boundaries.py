#!/usr/bin/env python3
"""
Build data/app/mercer-precincts.json + data/app/mercer-county-board-districts.json
— Mercer County's 24 voting precincts and 5 County Board districts, composed
from the county's own certified election returns (docs/EXPANSION_GUIDE.md
§2.5.1, the canvass route; scripts/vtd_board_districts.py holds the machinery).

HOW THIS COUNTY CAME TO BE BUILDABLE. Mercer answered this project's ask on
2026-08-17: Deputy Clerk Adams, routed by County Clerk & Recorder Brian
Gerber, sent "Mercer County Precinct Map 1.pdf". It was read and archived the
same day and it is a 2021 SCAN — it shows the five board districts as
overlays, which EVIDENCES that the lines exist but supplies no data, so the
composition ask stayed open and the gap record said so. It is now answered,
and not by another e-mail: Mercer's districts are unions of WHOLE PRECINCTS,
and the county's own election authority publishes, as structured data, exactly
which precincts vote in each district's contest.

WHERE THE COMPOSITION COMES FROM, AND WHY ONE ELECTION IS ENOUGH HERE. The
Clerk's results system publishes the certified 17 March 2026 General Primary
at il-mercer.pollresults.net, with the whole result set embedded in the page
as JSON. All five districts had a contest (District 1 had two — a four-year
term and a two-year unexpired), and their precinct lists partition the
county's 24 precincts EXACTLY ONCE each, with nothing left over and nothing
claimed twice.

The Clark build required a second witness per district because its
composition was transcribed out of PDF text by column geometry, and a
transcription can slip. THERE IS NO TRANSCRIPTION HERE. The precincts listed
in a contest are the precincts where that contest was ON THE BALLOT and
counted — a record of ballots cast, not a claim about a map, and published by
the county as machine data rather than as a rendering. That is why a single
certified election is accepted for this county and stated plainly rather than
dressed up as two.

WHAT IS NOT AVAILABLE, recorded so nobody re-searches it: this county's
AccessLiberty site (il-mercer.accessliberty.com) is EMPTY — it answers 200
with the vendor's shell and carries no past-election archive at all, unlike
Clark's, so there are no older canvass PDFs to read. The Clerk's own
documents section carries the 2021 precinct map, which is the scan above. The
weekly roster run re-checks the composition against whatever election the live
feed carries instead.

THE PRECINCT FABRIC IS CENSUS FABRIC, AND THAT IS MEASURED. TIGER's Census
2020 voting-district layer carries exactly 24 Mercer features whose names are
the county's own 24 precinct names — 24/24 — and whose POP100 sums to the
county's exact 2020 population (15,699). That is the Jasper test, and it is
the gate: Jasper fails it and is still unbuilt.

THE POPULATION SPREAD IS THE COUNTY'S. The composed districts run 2,682 (D1)
to 3,577 (D5) against a 3,140 ideal — worst deviation -14.6%. Recorded, not
smoothed; the ceiling below exists to catch a mis-assignment, not to certify
the plan. Each district elects TWO members in staggered years, so the ideal is
per district, not per seat.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Mercer
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_mercer_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "mercer-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "data", "app",
                             "mercer-county-board-districts.json")

COUNTY_FIPS = "131"
COUNTY_POP_2020 = 15699
EXPECTED_PRECINCTS = 24
SEATS_PER_DISTRICT = 2          # two members per district, elected in staggered years

RESULTS_URL = "https://il-mercer.pollresults.net"
BOARD_URL = "https://www.mercercountyil.org/county_board/index.php"
ELECTIONS_URL = "https://www.mercercountyil.org/documents/elections.php"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "Mercer County's certified 17 March 2026 General Primary "
                "results, published as structured data by County Clerk & "
                "Recorder Brian Gerber's own results system")

# THE COMPOSITION, read from the certified 2026 General Primary result set:
# each district's contest names the precincts it was on the ballot in. All 24
# precincts, each in exactly one district. The weekly roster run re-reads this
# from the live feed and fails if it moves.
COMPOSITION = {
    "1": ("ABINGTON", "KEITHSBURG", "MERCER 6", "NORTH HENDERSON", "OHIO GROVE", "SUEZ"),
    "2": ("GREENE 1", "GREENE 2", "RICHLAND GROVE 2", "RIVOLI"),
    "3": ("PREEMPTION 1", "PREEMPTION 2", "RICHLAND GROVE 1", "RICHLAND GROVE 3"),
    "4": ("DUNCAN", "ELIZA", "MILLERSBURG", "NEW BOSTON", "PERRYTON"),
    "5": ("MERCER 1", "MERCER 2", "MERCER 3", "MERCER 4", "MERCER 5"),
}

BALANCE_DEV_MAX = 0.30          # measured 0.146 (District 1) — the county's plan
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("mercer-boundaries")


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
    if len(vtds) != EXPECTED_PRECINCTS:
        fail("the census voting-district layer carries %d Mercer precincts, "
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
            "electionsUrl": ELECTIONS_URL,
            "note": ("Mercer County's 24 precincts are the Census 2020 voting "
                     "districts, which carry the county's own 24 precinct names "
                     "24/24 and sum to its exact 2020 population. Each feature "
                     "also carries its County Board district, which is "
                     "whole-precinct — no precinct is split between districts. "
                     "Polling places are not shown here: nothing the county "
                     "publishes pairs its precincts with buildings as data."),
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
                     "2020 voting districts. The only map the county has sent is "
                     "a 2021 SCAN showing the districts as overlays (Deputy Clerk "
                     "Adams, 2026-08-17): it evidences the lines and supplies no "
                     "data, so these boundaries are derived from the county's own "
                     "certified election returns instead."),
        },
        "features": district_features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, district_features, point_in_rings, fail)

    prec_body = V.dumps(precincts_payload)
    dist_body = V.dumps(districts_payload)
    print("mercer-boundaries: 24 precincts -> 5 districts of %d; census fabric "
          "matches the county's precinct list 24/24" % SEATS_PER_DISTRICT)
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s — the county's own plan)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)],
                     args.check, REPO_ROOT, fail, "mercer")


if __name__ == "__main__":
    main()

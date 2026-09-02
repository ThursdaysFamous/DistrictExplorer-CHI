#!/usr/bin/env python3
"""
Build data/app/crawford-precincts.json + data/app/crawford-county-board-districts.json
— Crawford County's 24 voting precincts and 5 County Board districts, composed
from the county's own certified election returns (docs/EXPANSION_GUIDE.md
§3.5.1, the canvass route; scripts/vtd_board_districts.py holds the machinery).

HOW THIS COUNTY CAME TO BE BUILDABLE. County Clerk & Recorder Beckie Staley
answered this project's ask on 2026-08-17 in writing: the board is elected
FROM DISTRICTS, five of them, and the maps live behind the county's Beacon
viewer. The county's Assessor then wrote separately — "I created those layers
and I maintain them" — but releasing them needs the county's MAPPING
COMMITTEE, so the geometry ask has been sitting with a committee ever since.
It turns out not to matter: Crawford's districts are unions of WHOLE
PRECINCTS, and the county's own election authority publishes, as structured
data, exactly which precincts vote in each district's contest.

WHERE THE COMPOSITION COMES FROM, AND WHY ONE ELECTION IS ENOUGH HERE. The
Clerk's results system publishes the certified 17 March 2026 General Primary
at il-crawford.pollresults.net, with the whole result set embedded in the page
as JSON. Every one of the five districts had a contest (District 4 had two —
a four-year term and a two-year unexpired), and their precinct lists partition
the county's 24 precincts EXACTLY ONCE each, with nothing left over and
nothing claimed twice.

The Clark build required a second witness per district because its
composition was transcribed out of PDF text by column geometry, and a
transcription can slip. THERE IS NO TRANSCRIPTION HERE. The precincts listed
in a contest are the precincts where that contest was ON THE BALLOT and
counted — a record of ballots cast, not a claim about a map, and published by
the county as machine data rather than as a rendering. That is why a single
certified election is accepted for this county and stated plainly rather than
dressed up as two.

WHAT IS NOT AVAILABLE, recorded so nobody re-searches it: the county's older
canvasses ARE published (Statement of Votes Cast for 8 Nov 2022 and 5 Nov
2024, on the Clerk's Elections page) and are SCANS with no text layer, as is
"crawford-county-boundry-maps.pdf" on the same page. None of the three can be
read by a machine, so none is used, and the weekly roster run re-checks the
composition against whatever election the live feed carries instead.

THE PRECINCT FABRIC IS CENSUS FABRIC, AND THAT IS MEASURED. TIGER's Census
2020 voting-district layer carries exactly 24 Crawford features whose names
are the county's own 24 precinct names — 24/24 — and whose POP100 sums to the
county's exact 2020 population (18,679). That is the Jasper test, and it is
the gate: Jasper fails it and is still unbuilt.

THE POPULATION SPREAD IS THE COUNTY'S. The composed districts run 3,181 (D1)
to 4,489 (D5) against a 3,736 ideal — worst deviation +20.2%. Recorded, not
smoothed; the ceiling below exists to catch a mis-assignment, not to certify
the plan. Each district elects TWO members in staggered years, so the ideal is
per district, not per seat.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Crawford
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_crawford_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "crawford-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "crawford-county-board-districts.json")

COUNTY_FIPS = "033"
COUNTY_POP_2020 = 18679
EXPECTED_PRECINCTS = 24
SEATS_PER_DISTRICT = 2          # two members per district, elected in staggered years

RESULTS_URL = "https://il-crawford.pollresults.net"
BOARD_URL = "https://crawfordcounty.illinois.gov/department/county-board/"
ELECTIONS_URL = "https://crawfordcounty.illinois.gov/department/clerk-recorder/elections-voting/"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "Crawford County's certified 17 March 2026 General Primary "
                "results, published as structured data by County Clerk & "
                "Recorder Beckie Staley's own results system")

# THE COMPOSITION, read from the certified 2026 General Primary result set:
# each district's contest names the precincts it was on the ballot in. All 24
# precincts, each in exactly one district. The weekly roster run re-reads this
# from the live feed and fails if it moves.
COMPOSITION = {
    "1": ("HUTSONVILLE 1", "HUTSONVILLE 2", "LAMOTTE 1", "LAMOTTE 2", "PRAIRIE 1"),
    "2": ("HONEY CREEK 1", "HONEY CREEK 2", "MONTGOMERY", "ROBINSON 1", "SOUTHWEST"),
    "3": ("LICKING", "MARTIN", "OBLONG 1", "OBLONG 2", "OBLONG 3"),
    "4": ("PRAIRIE 2", "ROBINSON 2", "ROBINSON 3", "ROBINSON 4", "ROBINSON 9"),
    "5": ("ROBINSON 5", "ROBINSON 6", "ROBINSON 7", "ROBINSON 8"),
}

BALANCE_DEV_MAX = 0.30          # measured 0.202 (District 5) — the county's plan
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("crawford-boundaries")


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
        fail("the census voting-district layer carries %d Crawford precincts, "
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
            "note": ("Crawford County's 24 precincts are the Census 2020 voting "
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
    print("crawford-boundaries: 24 precincts -> 5 districts of %d; census fabric "
          "matches the county's precinct list 24/24" % SEATS_PER_DISTRICT)
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s — the county's own plan)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)],
                     args.check, REPO_ROOT, fail, "crawford")


if __name__ == "__main__":
    main()

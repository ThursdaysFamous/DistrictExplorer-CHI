#!/usr/bin/env python3
"""
Build data/app/richland-precincts.json and
data/app/richland-county-board-districts.json — Richland County's 21 voting
precincts and the 7 County Board districts they compose
(docs/EXPANSION_GUIDE.md Part 2; scripts/vtd_board_districts.py holds the
machinery).

THE FIRST COUNTY IN THE FLEET WHOSE COMPOSITION CAME FROM GEOMETRY RATHER THAN
FROM RETURNS. Every county on the canvass route so far was composed by reading
which precincts carried which district's contest. Richland's canvasses cannot
do that — they COUNT precincts per district and never name one, which is the
Knox shape — and this record spent weeks calling that the blocker. It was not.
The county publishes both layers itself, in its own GIS, and nothing here had
ever looked: richlandcounty.illinois.gov links richlandil.wthgis.com (WTH
Engineering's viewer), whose map "Richland_IL" carries

    County Board Districtrs   dsid 10698   7 features   \IL\Richland\17159countyboarddistricts.tml
    Voter Precincts           dsid 1283   21 features   \IL\Richland\votingprecincts.tml

— the county's own files, 17159 being Richland's FIPS. Both are readable as
geometry (tgis/getftr.aspx?D=<dsid>&F=<fid>&Z=0 returns delta-encoded rings in
Web Mercator pixels at zoom 19), so the composition below is not inferred from
anything: it is what falls out of overlaying the county's district polygons on
the county's own precinct polygons.

EVERY PRECINCT LIES WHOLLY IN ONE DISTRICT, and the margin is not close. Each
of the 21 sits between 98.4% and 100.0% inside its assigned district; the
largest share any precinct has in a SECOND district is 0.89%. Those remainders
are digitisation slivers between two independently drawn layers — the district
layer's union is 0.66% larger than the precinct layer's overall — and not
splits. So Richland's board districts ARE unions of whole precincts, and a
dissolve of the Census 2020 voting districts draws them.

THAT DISPROVES THIS COUNTY'S OWN GAP RECORD, which is why it is worth stating
plainly. The record read ISBE's precinct archive — 30 reporting units over 21
base precinct names, NINE precincts carrying two units each — as "strongly
suggestive" that district lines run through precincts, on the reading Cumberland
established. The county's own GIS says otherwise, and it outranks an inference.
WHAT THOSE NINE SUB-UNITS ACTUALLY ARE IS STILL UNKNOWN and is deliberately not
guessed at here: the county's unit school districts split two of the nine
(Bonpas, Madison 1) and also split two precincts that are NOT among them
(Denver, Noble 2), so school lines do not explain the set, and neither do the
county's fire protection districts or municipal boundaries. All that is
established is what they are not, and a board-district split is what they are
not.

THREE INDEPENDENT WITNESSES AGREE with the composition, none of them the GIS:

  * THE CERTIFIED 2024 GENERAL. Its cumulative report gives a precinct COUNT
    for the three districts on that ballot — District 1 = 4, District 3 = 4,
    District 5 = 2 — and the composition below produces exactly 4, 4 and 2.
    This is the test the gap record named as decisive and could only run for
    three of seven districts; it passes all three.
  * THE POPULATION IDENTITY. The 21 voting districts sum to 15,813, Richland's
    exact Census 2020 count, and the seven district sums land between 2,066 and
    2,494 against a 2,259 ideal — worst deviation 10.4%, spread 18.9%. That is
    what a lawfully apportioned post-2020 plan looks like.
  * THE COUNTY'S PUBLISHED MAP. Precinct-Map.pdf (May 2026) is a 939x860 raster
    and illegible where Olney's lines cut, which is why it could never compose
    the county — but where it IS legible it agrees: District 1 over Noble,
    Decker and Denver; District 2 over Preston and German; District 3 over
    Claremont, Bonpas and the two Madisons.

THE FABRIC HAS NOT MOVED (the Jasper test), and here it is checked twice. By
NAME: the county's own certified 2026 General Primary ballot publication prints
a committeeperson contest for each of the 21 precincts, and those names match
the census BASENAMEs 21/21 with no alias. By GEOMETRY: each county precinct
polygon is 98.8-100.0% contained in the same-named census voting district. The
county's GIS and its polling list write the county seat's precincts long
("Olney Precinct 5", "Olney Twp. Pct. #5") where its ballot and the census
write "OLNEY 5"; the shipped label follows the ballot and the census, because
that is the form the county itself certifies.

NO POLLING PLACE SHIPS HERE, by the rule Calhoun's build set: the county
publishes a good one, but a polling place is a roster fact and this build's
business is geometry.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Richland
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_richland_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "richland-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "richland-county-board-districts.json")

COUNTY_FIPS = "159"
COUNTY_POP_2020 = 15813
EXPECTED_PRECINCTS = 21
SEATS_PER_DISTRICT = 1          # seven single-member districts, staggered

GIS_URL = "https://richlandil.wthgis.com/"
BOARD_URL = "https://richlandcounty.illinois.gov/county-board/"
ELECTIONS_URL = "https://richlandcounty.illinois.gov/county-clerk-recorder/elections/"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per Richland County's "
                "own GIS, which publishes the County Board districts and the "
                "voting precincts as separate county-authored layers "
                "(richlandil.wthgis.com; 17159countyboarddistricts.tml and "
                "votingprecincts.tml)")

# THE COMPOSITION, keyed by CENSUS voting-district BASENAME because that is the
# geometry being dissolved. Derived by overlaying the county's own board-district
# polygons on its own precinct polygons: each precinct's assigned district holds
# 98.4-100.0% of it, and no precinct has more than 0.89% in any second district.
# The county's certified 2024 General independently reports the precinct counts
# for districts 1, 3 and 5 as 4, 4 and 2 — which is what these sets give.
COMPOSITION = {
    "1": ("DECKER", "DENVER", "NOBLE 1", "NOBLE 2"),
    "2": ("GERMAN", "OLNEY 11", "PRESTON 1", "PRESTON 2"),
    "3": ("BONPAS", "CLAREMONT", "MADISON 1", "MADISON 2"),
    "4": ("OLNEY 5", "OLNEY 9"),
    "5": ("OLNEY 1", "OLNEY 7"),
    "6": ("OLNEY 4", "OLNEY 6"),
    "7": ("OLNEY 2", "OLNEY 3", "OLNEY 10"),
}

# The county's own current precinct list, exactly as its certified 17 March 2026
# General Primary ballot publication prints the committeeperson contests. This
# is the Jasper test's input: 21 names, matching the census BASENAMEs 21/21.
COUNTY_PRECINCTS = (
    "BONPAS", "CLAREMONT", "DECKER", "DENVER", "GERMAN", "MADISON 1",
    "MADISON 2", "NOBLE 1", "NOBLE 2", "OLNEY 1", "OLNEY 2", "OLNEY 3",
    "OLNEY 4", "OLNEY 5", "OLNEY 6", "OLNEY 7", "OLNEY 9", "OLNEY 10",
    "OLNEY 11", "PRESTON 1", "PRESTON 2",
)

# The certified 2024 General reports a precinct count for the three districts on
# that ballot and names no precinct. Checked against the composition below.
CERTIFIED_2024_COUNTS = {"1": 4, "3": 4, "5": 2}

BALANCE_DEV_MAX = 0.30          # measured 0.104
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("richland-boundaries")


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
    if len(COUNTY_PRECINCTS) != EXPECTED_PRECINCTS:
        fail("the county precinct list carries %d names, expected %d"
             % (len(COUNTY_PRECINCTS), EXPECTED_PRECINCTS))
    for dnum, want in CERTIFIED_2024_COUNTS.items():
        got = len(COMPOSITION[dnum])
        if got != want:
            fail("district %s holds %d precincts and the county's certified 2024 "
                 "General counted %d — the composition contradicts the canvass"
                 % (dnum, got, want))

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_PRECINCTS:
        fail("the census voting-district layer carries %d Richland features, "
             "expected %d" % (len(vtds), EXPECTED_PRECINCTS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d"
             % (county_pop, COUNTY_POP_2020))

    V.check_fabric(vtds, COUNTY_PRECINCTS, county_pop, fail)
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
            "source": SOURCE_LABEL, "gisUrl": GIS_URL, "electionsUrl": ELECTIONS_URL,
            "note": ("Richland County's 21 precincts are the Census 2020 voting "
                     "districts, which carry the county's own 21 precinct names "
                     "21/21 — as its certified 2026 General Primary ballot "
                     "publication prints them — and sum to its exact 2020 "
                     "population of 15,813. Each county precinct polygon in the "
                     "county's own GIS is 98.8-100.0% contained in the "
                     "same-named voting district, so the fabric has not moved. "
                     "Each feature also carries its County Board district, which "
                     "is whole-precinct: no precinct is split between districts. "
                     "The county's GIS and polling list write the county seat's "
                     "precincts long ('Olney Precinct 5'); the label here "
                     "follows the ballot and the census. Polling places are not "
                     "shown: the county publishes a list, but a polling place is "
                     "a roster fact rather than geometry."),
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
            "source": SOURCE_LABEL, "gisUrl": GIS_URL, "boardUrl": BOARD_URL,
            "canvass": ("Composition from the county's own GIS, which publishes "
                        "the board districts and the voting precincts as "
                        "separate county-authored layers: every one of the 21 "
                        "precincts lies 98.4-100.0% inside a single district, "
                        "with no precinct holding more than 0.89% in any second "
                        "district. The county's certified 2024 General "
                        "independently counts 4, 4 and 2 precincts in districts "
                        "1, 3 and 5, which is what this composition gives."),
            "note": ("Seven single-member districts on staggered terms, drawn "
                     "after the 2020 census and, per the county board's own "
                     "minutes of 11 August 2022, running until the next "
                     "redistricting in 2032. Richland publishes its board map "
                     "only as a low-resolution raster, so these boundaries are "
                     "dissolved from the Census 2020 voting districts instead, "
                     "per the composition its GIS states."),
        },
        "features": district_features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, district_features, point_in_rings, fail)

    prec_body = V.dumps(precincts_payload)
    dist_body = V.dumps(districts_payload)
    print("richland-boundaries: %d census voting districts -> %d precincts and "
          "%d single-member board districts"
          % (EXPECTED_PRECINCTS, len(precinct_features), len(COMPOSITION)))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  certified 2024 precinct counts confirmed: %s"
          % ", ".join("D%s=%d" % (d, CERTIFIED_2024_COUNTS[d])
                      for d in sorted(CERTIFIED_2024_COUNTS, key=int)))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)],
                     args.check, REPO_ROOT, fail, "richland")


if __name__ == "__main__":
    main()

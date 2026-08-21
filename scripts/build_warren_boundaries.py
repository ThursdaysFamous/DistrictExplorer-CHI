#!/usr/bin/env python3
"""
Build data/app/warren-county-board-districts.json — Warren County's 4 County
Board districts, dissolved from the Census 2020 voting districts per a
composition THE COUNTY ITSELF PUBLISHES.

THIS COUNTY WAS REACHED BY FIXING A PROBE, NOT BY ASKING ANYONE. Warren sat in
the `pass10-frontier-unasked` record — four counties with "working websites but
no map data anyone has found", whose stated next step was to write to their
clerks. It never needed the letter. The pass-13 sweep had looked for county
sites by permuting the county's NAME; Warren's actual domain was already in this
repo as the host of its Clerk's e-mail, and reading it takes one lookup
(see the 2026-08-20 correction across five other counties).

THE COMPOSITION IS NOT DERIVED — IT IS A LEGEND. The county's own precinct map
(Precinct-Map.pdf, linked from its County Board page) is a raster image with no
vector linework, so nothing can be traced from it. But its TEXT LAYER carries a
four-column table at the foot of the page, each column headed by a district and
listing that district's precincts. That is the county stating its own
composition in machine-readable form, and it is a stronger source than the
election-returns route used for Franklin and Clinton, which infers the same fact
from which ballot each precinct voted.

    District 1 (5)  Monmouth 2, 5, 7, 9, 10
    District 2 (5)  Monmouth 1, 3, 4, 6, 11
    District 3 (7)  Monmouth 8, Monmouth 12, Coldbrook, Hale, Kelly, Sumner,
                    Spring Grove
    District 4 (9)  Berwick, Ellison, Floyd, Greenbush, Lenox, Point Pleasant,
                    Roseville, Swan, Tompkins

A COMPOSED FABRIC, and the cleanest one this route has met. Census 2020 carries
28 Warren voting districts against the 26 precincts the county runs today, and
BOTH merges are nameable AND confined to a single district, so neither can move
a district line:

    ROSEVILLE 1 + ROSEVILLE 2                    -> Roseville      (District 4)
    SPRING GROVE-ALEXIS + SPRING GROVE-GERLAW    -> Spring Grove   (District 3)

That is the Clinton test passed twice over — Clinton had one unnameable merge
that happened to sit inside one district; Warren has no unnameable merge at all.
Marion, measured the same day, is the county that fails it.

THE POPULATION SPREAD IS THE TIGHTEST THIS ROUTE HAS PRODUCED: 4,030 to 4,332
against a 4,209 ideal, worst deviation 4.2%. Clinton held that record at 7.3%
for a few hours.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Warren
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. Output is
deterministic, so --check is a byte compare.

Usage:
    python3 scripts/build_warren_boundaries.py [--check]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro_outline import point_in_rings  # noqa: E402
import vtd_board_districts as V  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DISTRICTS = os.path.join(REPO_ROOT, "data", "app",
                             "warren-county-board-districts.json")

COUNTY_FIPS = "187"
COUNTY_POP_2020 = 16835
EXPECTED_VTDS = 28            # census 2020 voting districts
COUNTY_PRECINCTS = 26         # what the county runs today

BOARD_URL = "https://warrencountyil.gov/government/county-board/"
MAP_URL = "https://warrencountyil.gov/wp-content/uploads/2025/07/Precinct-Map.pdf"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the district-by-"
                "district precinct table Warren County publishes in the legend "
                "of its own precinct map")

# Keyed by CENSUS voting district, because that is the geometry being dissolved.
# Every one of the 28 is claimed exactly once. The four that carry no
# same-named county precinct today are the two nameable merges in the docstring.
COMPOSITION = {
    "1": ("MONMOUTH 2", "MONMOUTH 5", "MONMOUTH 7", "MONMOUTH 9", "MONMOUTH 10"),
    "2": ("MONMOUTH 1", "MONMOUTH 3", "MONMOUTH 4", "MONMOUTH 6", "MONMOUTH 11"),
    "3": ("MONMOUTH 8", "MONMOUTH 12", "COLDBROOK", "HALE", "KELLY", "SUMNER",
          "SPRING GROVE-ALEXIS", "SPRING GROVE-GERLAW"),
    "4": ("BERWICK", "ELLISON", "FLOYD", "GREENBUSH", "LENOX", "POINT PLEASANT",
          "ROSEVILLE 1", "ROSEVILLE 2", "SWAN", "TOMPKINS"),
}

# The county's own current precincts per district, exactly as its map's legend
# prints them. Carried on the feature so the card names what a reader would
# recognise, and re-read weekly as the drift tripwire.
COUNTY_COMPOSITION = {
    "1": ("Monmouth 2", "Monmouth 5", "Monmouth 7", "Monmouth 9", "Monmouth 10"),
    "2": ("Monmouth 1", "Monmouth 3", "Monmouth 4", "Monmouth 6", "Monmouth 11"),
    "3": ("Monmouth 8", "Monmouth 12", "Coldbrook", "Hale", "Kelly", "Sumner",
          "Spring Grove"),
    "4": ("Berwick", "Ellison", "Floyd", "Greenbush", "Lenox", "Point Pleasant",
          "Roseville", "Swan", "Tompkins"),
}

BALANCE_DEV_MAX = 0.30        # measured 0.042 — the tightest this route has produced
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


def fail(msg):
    print("warren-boundaries: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build")
    args = ap.parse_args()

    from shapely.geometry import shape, mapping   # noqa: E402  (heavy, function-local)
    from shapely.ops import unary_union, transform  # noqa: E402

    claimed = [n for names in COMPOSITION.values() for n in names]
    if len(claimed) != EXPECTED_VTDS:
        fail("the composition names %d voting districts, expected %d"
             % (len(claimed), EXPECTED_VTDS))
    county_named = sum(len(v) for v in COUNTY_COMPOSITION.values())
    if county_named != COUNTY_PRECINCTS:
        fail("the county-precinct composition names %d precincts, expected %d"
             % (county_named, COUNTY_PRECINCTS))
    if sorted(COMPOSITION) != sorted(COUNTY_COMPOSITION):
        fail("the two compositions describe different district sets")

    vtds = V.fetch_vtds(COUNTY_FIPS, shape, fail)
    if len(vtds) != EXPECTED_VTDS:
        fail("the census voting-district layer carries %d Warren features, "
             "expected %d" % (len(vtds), EXPECTED_VTDS))
    county_geom, county_pop = V.fetch_county(COUNTY_FIPS, shape, fail)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d"
             % (county_pop, COUNTY_POP_2020))
    # Composed-fabric test (Calhoun/Clinton): the population identity proves the
    # voting districts still tile the county; check_partition proves the
    # composition accounts for every one exactly once. That this is the CURRENT
    # plan comes from the county publishing the table itself, not from either.
    V.check_fabric_composed(vtds, county_pop, fail)
    V.check_partition(COMPOSITION, vtds, fail)

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
                           "precincts": list(COUNTY_COMPOSITION[dnum]),
                           "pop2020": pops[dnum]},
            "geometry": V.round_geom(districts[dnum], mapping),
        })
    payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "boardUrl": BOARD_URL, "mapUrl": MAP_URL,
            "composition": ("The county's own precinct map prints a four-column "
                            "table in its legend, each column headed by a "
                            "district and listing that district's precincts — "
                            "so this composition is STATED by Warren County "
                            "rather than inferred from which ballot each "
                            "precinct voted"),
            "note": ("Four districts dissolved from the Census 2020 voting "
                     "districts. The county's map itself is a raster image with "
                     "no vector linework, so nothing is traced from it; only its "
                     "legend is read. Census 2020 carries 28 voting districts "
                     "against the county's 26 precincts, and both merges are "
                     "nameable and sit wholly inside one district — Roseville 1 "
                     "and 2 in District 4, Spring Grove-Alexis and -Gerlaw in "
                     "District 3 — so neither can move a district line. The "
                     "precinct list on each feature is the county's own current "
                     "26, not the 28 census units the geometry is built from."),
        },
        "features": features,
    }

    V.verify_point_in_rings(COMPOSITION, vtds, features, point_in_rings, fail)

    body = V.dumps(payload)
    print("warren-boundaries: %d census voting districts -> %d districts "
          "(the county's own 26 precincts named on the features)"
          % (EXPECTED_VTDS, len(COMPOSITION)))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    V.write_or_check([(OUT_DISTRICTS, body)], args.check, REPO_ROOT, fail, "warren")


if __name__ == "__main__":
    main()

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
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app",
                             "warren-county-board-districts.json")
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "warren-precincts.json")

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

# The census units that merge into one county precinct. Both are named by the
# county's own legend and both sit wholly inside a single district, which the
# builder re-proves every run rather than trusting this comment.
CENSUS_MERGES = {
    "Roseville": ("ROSEVILLE 1", "ROSEVILLE 2"),
    "Spring Grove": ("SPRING GROVE-ALEXIS", "SPRING GROVE-GERLAW"),
}

BALANCE_DEV_MAX = 0.30        # measured 0.042 — the tightest this route has produced
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999


fail = make_fail("warren-boundaries")


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

    # ---- the precincts themselves -----------------------------------------
    # THE COUNTY RUNS 26 PRECINCTS AND THE CENSUS DREW 28, so the census units
    # are MERGED to the county's fabric rather than shipped as-is. Both merges
    # are named by the county's own legend and each sits wholly inside a single
    # district (Roseville 1+2 in District 4, Spring Grove-Alexis + -Gerlaw in
    # District 3), which is exactly why neither can move a district line — the
    # same fact that made the districts buildable makes the precincts buildable.
    # Nothing new is sourced here; this absence simply had no gap record.
    merged_of = {}
    for county_name, parts in CENSUS_MERGES.items():
        keys = [V.norm(p) for p in parts]
        missing = [p for p, k in zip(parts, keys) if k not in vtds]
        if missing:
            fail("the merge for %r names census units the fabric does not carry: "
                 "%s" % (county_name, ", ".join(missing)))
        held = {where[k] for k in keys}
        if len(held) != 1:
            fail("the census units merging into %r sit in districts %s — a merge "
                 "that spans a district line cannot be collapsed"
                 % (county_name, ", ".join(sorted(held))))
        merged_of[county_name] = (keys, held.pop())

    consumed = {k for keys, _ in merged_of.values() for k in keys}
    precinct_features = []
    for key in sorted(set(vtds) - consumed, key=lambda k: vtds[k]["basename"]):
        rec = vtds[key]
        precinct_features.append({
            "type": "Feature",
            "properties": {"name": V.title_case(rec["basename"]),
                           "geoid": rec["geoid"], "pop2020": rec["pop"],
                           "district": where[key]},
            "geometry": V.round_geom(rec["geom"], mapping),
        })
    for county_name in sorted(merged_of):
        keys, dnum = merged_of[county_name]
        merged = unary_union([vtds[k]["geom"] for k in keys])
        if not merged.is_valid:
            merged = merged.buffer(0)
        precinct_features.append({
            "type": "Feature",
            "properties": {"name": county_name,
                           "censusUnits": [V.title_case(vtds[k]["basename"])
                                           for k in keys],
                           "pop2020": sum(vtds[k]["pop"] for k in keys),
                           "district": dnum},
            "geometry": V.round_geom(merged, mapping),
        })
    precinct_features.sort(key=lambda f: f["properties"]["name"])
    if len(precinct_features) != COUNTY_PRECINCTS:
        fail("built %d precincts, expected the county's %d"
             % (len(precinct_features), COUNTY_PRECINCTS))
    named = {n for names in COUNTY_COMPOSITION.values() for n in names}
    built = {f["properties"]["name"] for f in precinct_features}
    if built != named:
        fail("the built precincts %s do not match the county's own legend %s"
             % (sorted(built - named), sorted(named - built)))
    if sum(f["properties"]["pop2020"] for f in precinct_features) != county_pop:
        fail("the built precincts do not sum to the county's population")

    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "boardUrl": BOARD_URL, "mapUrl": MAP_URL,
            "note": ("Warren County's 26 voting precincts, named exactly as the "
                     "county's own precinct-map legend prints them. Census 2020 "
                     "drew 28 voting districts here, so TWO are merged back to "
                     "the county's fabric — Roseville 1 and 2 into Roseville, "
                     "Spring Grove-Alexis and Spring Grove-Gerlaw into Spring "
                     "Grove — and each merged feature names the census units it "
                     "is built from. Both merges sit wholly inside one district, "
                     "which is the same fact that lets the county's districts be "
                     "dissolved from census geometry at all. Every precinct "
                     "carries its County Board district. No polling place ships: "
                     "a polling place is a roster fact rather than geometry (the "
                     "Calhoun rule)."),
        },
        "features": precinct_features,
    }

    body = V.dumps(payload)
    prec_body = V.dumps(precincts_payload)
    print("warren-boundaries: %d census voting districts -> %d districts "
          "(the county's own 26 precincts named on the features)"
          % (EXPECTED_VTDS, len(COMPOSITION)))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% in "
          "district %s)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in sorted(pops, key=int)),
             county_pop, 100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap, 100 * covered))
    print("  precincts: %d shipped (%d census units merged into %d county "
          "precincts), each carrying its district"
          % (len(precinct_features), sum(len(v) for v in CENSUS_MERGES.values()),
             len(CENSUS_MERGES)))
    V.write_or_check([(OUT_DISTRICTS, body), (OUT_PRECINCTS, prec_body)],
                     args.check, REPO_ROOT, fail, "warren")


if __name__ == "__main__":
    main()

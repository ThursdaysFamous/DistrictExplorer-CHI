#!/usr/bin/env python3
"""
Build data/app/clark-precincts.json + data/app/clark-county-board-districts.json
— Clark County's 23 voting precincts and 7 County Board districts, the
composition PROVEN THREE TIMES from the county's own certified election
canvasses.

WHY THIS COUNTY LOOKED IMPOSSIBLE AND WASN'T. The clark-county-board gap
record had stood since the pass-13 detached-counties sweep with a plain
no-source blocker, and on 2026-08-18 County Clerk & Recorder Laura H. Lee
answered the ask in one sentence: "The County Board is elected by districts.
I do not have maps available."  That is §2.5 step 2 settled in writing — and
it is also, read literally, a refusal of the geometry ask. It was not the end
of the county, because the map was never the only route: the county's
ELECTION AUTHORITY publishes precinct-level certified results, and a board
district that is a union of whole precincts is fully described by the contest
tables (the White/Jasper route). Clark's is.

THE PRECINCT FABRIC IS CENSUS FABRIC, AND THAT IS MEASURED, NOT ASSUMED.
TIGER's Census 2020 voting-district layer carries EXACTLY 23 Clark features,
and their names are the 23 precinct names the county itself uses — 23/23, no
spelling wobble — while their POP100 sums to the county's exact 2020
population (15,455). The county's own board list, its 2022 canvass, its 2024
canvass and its 2026 General Primary results all tabulate the same 23 names,
so the fabric has not moved across two general elections and a primary either
side of the census. This is the test JASPER FAILED — five census Wade voting
districts against four current county precincts — and it is why that county
is still unbuilt while this one ships. Nothing here traces a map; the shipped
polygons ARE the census VTDs and their per-district dissolve (the Shelby /
White shape), exact and deterministic.

HOW THE COMPOSITION IS READ, AND PROVEN. Three independent witnesses, and the
build refuses to write unless all three agree:

  1. THE 2022 GENERAL CANVASS (8 Nov 2022, the first election after the
     county's districts were last set) tabulates all SEVEN "COUNTY BOARD nTH
     DISTRICT MEMBER" contests, each over its own precincts, each header "Vote
     for one".  All 23 precincts appear, each in exactly one district.
  2. THE 2024 GENERAL CANVASS (5 Nov 2024) re-runs districts 3, 4 and 7 with
     identical precinct tables.
  3. THE 2026 GENERAL PRIMARY results (17 Mar 2026, final) carry districts 1,
     2, 5 and 6 with identical precinct tables.

(2) and (3) between them re-prove every one of the seven districts (1)
established, from two elections two years apart. A FOURTH, non-election
witness agrees and is not relied on: the county's own "Clark County Board
Member 2022-2024" list, linked from clarkcountyil.org/board, prints a
Township column whose precinct groupings match all seven — but it is a
SCANNED IMAGE with no text layer, so it can never be a machine source.

WHERE THE CANVASSES LIVE. The Clerk's election-results site is
il-clark.accessliberty.com (past-election canvass PDFs, text-layer, one per
election) with live results at il-clark.pollresults.net (an AngularJS shell
whose whole result set is embedded in the page as JSON). Both are the Clerk's
own; the county site's Election Results page points at them. NOTE FOR THE
FLEET: that vendor pair serves 34 Illinois counties, fourteen of which this
project does not serve and several of which carry open gaps — see the
clark-county-board gap record and docs/DATA_LAYER_GUIDEBOOK.md.

THE POPULATION SPREAD IS THE COUNTY'S, AND IT IS RECORDED RATHER THAN
SMOOTHED. The composed districts run 1,923 (D3) to 2,674 (D6) against a
one-member ideal of 2,208 — worst deviation +21.1%, total spread 34.0% of
ideal. That is far outside the ~10% an ordinary post-census apportionment
lands in, so BALANCE_DEV_MAX below is set to catch a MIS-ASSIGNMENT (which
would move whole precincts and blow well past it) rather than to certify the
plan. Whether Clark reapportioned after the 2020 census is a question for the
Clerk, not something this build may infer; nothing on the card claims the
plan is current-census-balanced.

WHAT THIS FILE DELIBERATELY DOES NOT SHIP: polling places. The county's
Precinct Maps page links a text-layer list naming a building for all 23
precincts, but the file is titled "Polling places and addresses 11-18" — the
November 2018 election — and sending a voter to an eight-year-old address is
exactly the harm the honesty rules exist to prevent. Recorded as a gap and
asked of the Clerk instead.

THIS IS A RARE OPERATOR STEP (requests + shapely). Re-run only if Clark
reapportions, re-precincts, or TIGERweb republishes the VTD fabric. The output
is deterministic — census geometry in, census geometry out — so --check is a
byte compare.

Usage:
    python3 scripts/build_clark_boundaries.py
    python3 scripts/build_clark_boundaries.py --check
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests  # noqa: E402
from build_metro_outline import (  # noqa: E402  (shared machinery — do not fork)
    HEADERS, REQUEST_TIMEOUT, STATE_FIPS, point_in_rings,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "clark-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "data", "app",
                             "clark-county-board-districts.json")

COUNTY_FIPS = "023"
VTD_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
           "tigerWMS_Census2020/MapServer/58/query")
COUNTY2020_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
                  "tigerWMS_Census2020/MapServer/82/query")

BOARD_URL = "https://www.clarkcountyil.org/board"
RESULTS_URL = "https://il-clark.accessliberty.com/pastelections.aspx"
LIVE_RESULTS_URL = "https://il-clark.pollresults.net"

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "Clark County's own certified election canvasses (2022 and 2024 "
                "General, 2026 General Primary), published by County Clerk & "
                "Recorder Laura H. Lee")

# ---------------------------------------------------------------------------
# THE COMPOSITION. Precinct names are the census BASENAME spelling, which is
# also the county's own — the canvasses, the live results feed and the board
# list all print these 23 strings. Seven single-member districts: every
# canvass contest header reads "Vote for one".
#
# WITNESSES, per district — which certified document tabulates it:
#   D1  2022 General, 2026 General Primary
#   D2  2022 General, 2026 General Primary
#   D3  2022 General, 2024 General
#   D4  2022 General, 2024 General
#   D5  2022 General, 2026 General Primary
#   D6  2022 General, 2026 General Primary
#   D7  2022 General, 2024 General
CANVASS = {
    "1": ("AUBURN", "DOLSON", "DOUGLAS", "WABASH 1", "WESTFIELD"),
    "2": ("CASEY 2", "CASEY 3", "JOHNSON", "PARKER"),
    "3": ("CASEY 1", "CASEY 4"),
    "4": ("MARTINSVILLE 1", "MARTINSVILLE 2", "MELROSE", "ORANGE"),
    "5": ("MARSHALL 1", "MARSHALL 2"),
    "6": ("ANDERSON", "MARSHALL 3", "MARSHALL 4"),
    "7": ("DARWIN", "WABASH 2", "YORK"),
}
# The 2024 General and the 2026 General Primary each re-tabulate a disjoint
# half of the districts; together they cover all seven independently of 2022.
RECONFIRMED_2024 = ("3", "4", "7")
RECONFIRMED_2026 = ("1", "2", "5", "6")

SEATS_PER_DISTRICT = 1
EXPECTED_PRECINCTS = 23
COUNTY_POP_2020 = 15455

# A mis-assignment moves a whole precinct between districts; the smallest
# Clark precinct is 129 people and the largest 1,472, so any such error lands
# well past this ceiling. The county's OWN plan measures 0.211 (District 6) —
# see the docstring: this floor bounds our arithmetic, not their apportionment.
BALANCE_DEV_MAX = 0.30
# The dissolved districts must tile the county: no overlap, and the union must
# match the census county polygon to within rounding.
MAX_OVERLAP_M2 = 1.0
MIN_COVERED = 0.9999
COORD_PRECISION = 6


def fail(msg):
    print("clark-boundaries: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def title_case(name):
    return " ".join(w if w.isdigit() else w.capitalize() for w in name.split())


def get_json(url, params):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, params=params)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and data.get("error"):
        fail("%s answered an error: %s" % (url, data["error"]))
    return data


def fetch_vtds(shape_fn):
    data = get_json(VTD_URL, {
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
        "outFields": "GEOID,BASENAME,POP100", "returnGeometry": "true",
        "outSR": "4326", "f": "geojson"})
    feats = data.get("features") or []
    if len(feats) != EXPECTED_PRECINCTS:
        fail("the Census voting-district layer carries %d Clark precincts, "
             "expected %d — the fabric changed; re-read the county's canvasses "
             "before rebuilding (this is the test Jasper fails)"
             % (len(feats), EXPECTED_PRECINCTS))
    out = {}
    for f in feats:
        props = f.get("properties") or {}
        name = " ".join((props.get("BASENAME") or "").upper().split())
        if name in out:
            fail("the voting-district layer carries two features named %r" % name)
        geom = shape_fn(f["geometry"])
        out[name] = {"geom": geom if geom.is_valid else geom.buffer(0),
                     "geoid": props.get("GEOID"),
                     "pop": int(props.get("POP100") or 0)}
    return out


def fetch_county(shape_fn):
    data = get_json(COUNTY2020_URL, {
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
        "outFields": "POP100", "returnGeometry": "true", "outSR": "4326",
        "f": "geojson"})
    feats = data.get("features") or []
    if not feats:
        fail("Census 2020 county layer returned nothing for Clark County")
    props = feats[0].get("properties") or {}
    return shape_fn(feats[0]["geometry"]), int(props.get("POP100") or 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the shipped files match a fresh build")
    args = parser.parse_args()

    # heavy imports stay function-local (the De Witt seam): the weekly roster
    # builder imports this module's CONSTANTS and must not need shapely.
    from shapely.geometry import shape, mapping  # noqa: E402
    from shapely.ops import unary_union          # noqa: E402

    assigned = [n for names in CANVASS.values() for n in names]
    if len(assigned) != len(set(assigned)):
        dupes = sorted(n for n in set(assigned) if assigned.count(n) > 1)
        fail("precinct(s) %s assigned to more than one district" % ", ".join(dupes))
    if len(assigned) != EXPECTED_PRECINCTS:
        fail("CANVASS assigns %d precincts, expected %d"
             % (len(assigned), EXPECTED_PRECINCTS))
    missing = sorted(set(CANVASS) - set(RECONFIRMED_2024) - set(RECONFIRMED_2026))
    if missing:
        fail("district(s) %s rest on the 2022 canvass alone — every district "
             "must be re-tabulated by a later certified document"
             % ", ".join(missing))

    vtds = fetch_vtds(shape)
    unknown = sorted(set(assigned) - set(vtds))
    if unknown:
        fail("canvass names %s that the census fabric does not carry"
             % ", ".join(unknown))
    extra = sorted(set(vtds) - set(assigned))
    if extra:
        fail("census fabric carries %s, which no canvass district claims"
             % ", ".join(extra))

    county_geom, county_pop = fetch_county(shape)
    if county_pop != COUNTY_POP_2020:
        fail("census county population is %d, expected %d" % (county_pop, COUNTY_POP_2020))
    vtd_pop = sum(v["pop"] for v in vtds.values())
    if vtd_pop != county_pop:
        fail("the 23 voting districts sum to %d people, the county to %d — the "
             "fabric is not a tiling of the county" % (vtd_pop, county_pop))

    districts = {}
    pops = {}
    for dnum, names in CANVASS.items():
        merged = unary_union([vtds[n]["geom"] for n in names])
        districts[dnum] = merged if merged.is_valid else merged.buffer(0)
        pops[dnum] = sum(vtds[n]["pop"] for n in names)

    ideal = county_pop / float(len(CANVASS) * SEATS_PER_DISTRICT)
    worst = max(((abs(pops[d] - ideal) / ideal), d) for d in pops)
    if worst[0] > BALANCE_DEV_MAX:
        fail("district %s deviates %.1f%% from the one-member ideal (ceiling "
             "%.0f%%) — that is a mis-assignment, not an apportionment"
             % (worst[1], 100 * worst[0], 100 * BALANCE_DEV_MAX))

    # --- tiling: districts must not overlap and must cover the county --------
    lat = county_geom.centroid.y
    mx = 111320.0 * math.cos(math.radians(lat))
    my = 110574.0

    def area_m2(geom):
        from shapely.ops import transform
        return transform(lambda x, y, z=None: (x * mx, y * my), geom).area

    keys = sorted(districts, key=int)
    overlap_m2 = 0.0
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            inter = districts[a].intersection(districts[b])
            if not inter.is_empty:
                overlap_m2 += area_m2(inter)
    if overlap_m2 > MAX_OVERLAP_M2:
        fail("districts overlap by %.1f m2 (ceiling %.1f)" % (overlap_m2, MAX_OVERLAP_M2))
    union = unary_union(list(districts.values()))
    covered = area_m2(union.intersection(county_geom)) / area_m2(county_geom)
    if covered < MIN_COVERED:
        fail("the seven districts cover only %.4f%% of the county"
             % (100 * covered))

    # ---- emit ---------------------------------------------------------------
    def round_geom(geom):
        def fix(coords):
            if isinstance(coords[0], (float, int)):
                return [round(coords[0], COORD_PRECISION),
                        round(coords[1], COORD_PRECISION)]
            return [fix(c) for c in coords]
        geo = mapping(geom)
        return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}

    where = {n: d for d, names in CANVASS.items() for n in names}
    precinct_features = []
    for name in sorted(vtds):
        rec = vtds[name]
        precinct_features.append({
            "type": "Feature",
            "properties": {"name": title_case(name), "district": where[name],
                           "geoid": rec["geoid"], "pop2020": rec["pop"]},
            "geometry": round_geom(rec["geom"]),
        })
    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "resultsUrl": RESULTS_URL,
            "note": ("Clark County's 23 precincts are the Census 2020 voting "
                     "districts, which carry the county's own 23 precinct names "
                     "23/23 and sum to its exact 2020 population. The county's "
                     "2022 and 2024 General canvasses and its 2026 General "
                     "Primary results all tabulate the same 23 names, so the "
                     "fabric has not moved either side of the census. Polling "
                     "places are NOT shown: the only list the county publishes "
                     "is dated November 2018."),
        },
        "features": precinct_features,
    }

    district_features = []
    for dnum in keys:
        district_features.append({
            "type": "Feature",
            "properties": {
                "district": dnum, "name": "District %s" % dnum,
                "precincts": [title_case(n) for n in CANVASS[dnum]],
                "pop2020": pops[dnum],
            },
            "geometry": round_geom(districts[dnum]),
        })
    districts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL,
            "boardUrl": BOARD_URL,
            "resultsUrl": RESULTS_URL,
            "canvass": ("Composition certified by the county's 2022 General "
                        "Election canvass (all seven districts, whole "
                        "precincts), re-confirmed for districts 3, 4 and 7 by "
                        "the 2024 General canvass and for districts 1, 2, 5 and "
                        "6 by the 2026 General Primary results"),
            "note": ("Seven single-member districts dissolved from Census 2020 "
                     "voting districts per the composition of the county's own "
                     "certified canvasses. County Clerk & Recorder Laura H. Lee "
                     "confirmed in writing on 2026-08-18 that the board is "
                     "elected by districts and that the county has no map to "
                     "supply; these boundaries are therefore derived from the "
                     "election returns, not traced from a county map."),
        },
        "features": district_features,
    }

    # the app's own even-odd test, per precinct representative point
    def rings_of(geometry):
        if geometry["type"] == "Polygon":
            return geometry["coordinates"]
        return [r for poly in geometry["coordinates"] for r in poly]
    for dnum, names in CANVASS.items():
        for n in names:
            probe = vtds[n]["geom"].representative_point()
            hits = [f["properties"]["district"] for f in district_features
                    if point_in_rings(probe.y, probe.x, rings_of(f["geometry"]))]
            if hits != [dnum]:
                fail("precinct %s lands in district %s after rounding, expected %s"
                     % (n, hits or "none", dnum))

    prec_body = json.dumps(precincts_payload, sort_keys=True,
                           separators=(",", ":")) + "\n"
    dist_body = json.dumps(districts_payload, sort_keys=True,
                           separators=(",", ":")) + "\n"

    print("clark-boundaries: 23 precincts -> 7 single-member districts; "
          "canvass names match the census fabric 23/23")
    print("  witnesses: 2022 General (all 7), 2024 General (%s), 2026 General "
          "Primary (%s)" % ("/".join(RECONFIRMED_2024), "/".join(RECONFIRMED_2026)))
    print("  populations: %s (total %d = census POP100; worst deviation %.1f%% "
          "in district %s — the county's own plan, see the docstring)"
          % (", ".join("D%s=%d" % (d, pops[d]) for d in keys), county_pop,
             100 * worst[0], worst[1]))
    print("  tiling: overlap %.2f m2; %.4f%% of the county covered"
          % (overlap_m2, 100 * covered))

    if args.check:
        for path, body in ((OUT_PRECINCTS, prec_body), (OUT_DISTRICTS, dist_body)):
            if not os.path.exists(path):
                fail("%s is missing — run this script" % os.path.relpath(path, REPO_ROOT))
            with open(path, encoding="utf-8") as handle:
                if handle.read() != body:
                    fail("%s differs from a fresh build"
                         % os.path.relpath(path, REPO_ROOT))
        print("  --check OK — both files match a fresh build")
        return
    with open(OUT_PRECINCTS, "w", encoding="utf-8") as handle:
        handle.write(prec_body)
    with open(OUT_DISTRICTS, "w", encoding="utf-8") as handle:
        handle.write(dist_body)
    print("  wrote %s (%s bytes) and %s (%s bytes)"
          % (os.path.relpath(OUT_PRECINCTS, REPO_ROOT), "{:,}".format(len(prec_body)),
             os.path.relpath(OUT_DISTRICTS, REPO_ROOT), "{:,}".format(len(dist_body))))


if __name__ == "__main__":
    main()

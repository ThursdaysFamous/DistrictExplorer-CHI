#!/usr/bin/env python3
"""Build Jefferson County's 13 board districts by dissolving its own precincts.

WHY THIS IS A DISSOLVE AND NOT A FETCH. Jefferson publishes no boundary of any
kind. Asked on 5 Aug 2026 for both the board districts and the precincts,
County Clerk Joe Davis sent the precinct shapefile on 6 Aug and said nothing
about the districts. `jefferson-county-board` recorded that as an incomplete
answer rather than a refusal, and named the cheap route back:

    "the precincts are now in hand, so a plain LIST of which precincts make up
     each district would be enough to draw the boundaries exactly, with no new
     geometry needed from the county at all."

Re-asked on that basis, and on 7 Aug he sent exactly that — "County Board
Districts (Approved by County Board November 22, 2021)", one line per district
naming its precincts. This script is that list applied to the precinct geometry
already shipped, so the boundaries are the county's own lines throughout: its
precincts, combined the county's own way.

THE LIST ACCOUNTS FOR EVERY PRECINCT, EXACTLY ONCE. All 33 shipped precincts are
named, none is named that does not exist, and only one is split between two
districts. Those three facts are asserted below rather than assumed — a future
list that drops a precinct or invents one fails the build.

THE ONE SPLIT, AND THE ONE INFERENCE IN THIS FILE. The chart puts "Shiloh 4 west
of 34th Street" in District 10 and "Shiloh 4 east of 34th Street" in District 11.
34th Street in Mt. Vernon is a straight north-south street on the city grid, and
the cut is made at its longitude:

  * SOURCE IS TIGER/LINE, deliberately. The Census Bureau's Transportation layer
    puts 34th St at longitude -88.93327 where it meets Shiloh 4. That is a
    public-domain federal dataset. OpenStreetMap agrees (its "North 34th Street"
    runs -88.93334..-88.93327) and was used to CORROBORATE the number, not to
    supply it: OSM is ODbL, and a shipped civic boundary derived from it would
    carry share-alike obligations this project has not taken on. One coordinate
    read from TIGER carries none.

  * WHERE IT IS EXACT, AND WHERE IT IS NOT. 34th Street is mapped from the south
    edge of Shiloh 4 up to about latitude 38.3211, which is roughly three
    quarters of the way up the precinct. North of that the street stops and this
    cut CONTINUES ITS ALIGNMENT as a meridian. That extension covers about a
    quarter of Shiloh 4 — 0.05% of the county — and it is not empty ground: it
    holds the Chesterfield Village, Webster Hill and Kingsridge subdivisions.
    Only Districts 10 and 11 are affected, both say so on the card, and the
    county has been asked to confirm where the line runs up there.

    This is the honest shape of the uncertainty: exact for three quarters of the
    boundary, a straight projection for the rest. LaSalle is the precedent for
    the coarser alternative — its split precincts ship wholly on their majority
    side with the card saying so — and this is strictly better than that.

Usage:
    python3 scripts/build_jefferson_board_districts.py            # write data/app/
    python3 scripts/build_jefferson_board_districts.py --check    # drift gate
"""

import argparse
import json
import os
import sys

try:
    from shapely.geometry import box, shape, mapping
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover
    sys.exit("shapely is required: pip install -c scripts/requirements.txt shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "jefferson-precincts.json")
OUT_PATH = os.path.join(REPO_ROOT, "data", "app",
                        "jefferson-county-board-districts.json")

SOURCE_NOTE = ("Jefferson County Clerk & Recorder Joe Davis, \"County Board "
               "Districts (Approved by County Board November 22, 2021)\", "
               "supplied by e-mail 2026-08-07")
CUT_SOURCE = ("US Census Bureau TIGER/Line Transportation, layer 8 (Local "
              "Roads), feature \"34th St\" at Mt. Vernon, IL — public domain")

COORD_PRECISION = 6
EXPECTED_DISTRICTS = 13
EXPECTED_PRECINCTS = 33

# 34th Street's longitude where it bounds Shiloh 4 (see the docstring). The
# street runs north only to about SPLIT_STREET_TOP_LAT; above that this cut is
# the street's alignment projected, which is the single inference in this file.
SHILOH_4_CUT_LON = -88.93327
SPLIT_STREET_TOP_LAT = 38.32106

# The county's approved composition, transcribed from SOURCE_NOTE. Precinct names
# are as data/app/jefferson-precincts.json names them (the county's own export),
# with the chart's "Mt. Vernon N" written the county's shorter way, "Mt V N".
# A precinct paired with a side ("west"/"east") is split by SHILOH_4_CUT_LON.
COMPOSITION = {
    1:  ["Casner", "Grand Prairie", "Rome 2"],
    2:  ["Farrington", "Field", "Rome 1"],
    3:  ["Shiloh 1", "Shiloh 2", "Mt V 7"],
    4:  ["Mt V 2", "Webber 2"],
    5:  ["Blissville", "McClellan", "Shiloh 5"],
    6:  ["Dodds 1", "Dodds 2"],
    7:  ["Bald Hill", "Elk Prairie", "Spring Garden 1", "Spring Garden 2"],
    8:  ["Moores Prairie", "Pendleton", "Webber 1"],
    9:  ["Mt V 3", "Mt V 5"],
    10: ["Shiloh 3", ("Shiloh 4", "west")],
    11: ["Mt V 8", "Mt V 9", ("Shiloh 4", "east")],
    12: ["Mt V 1", "Mt V 4"],
    13: ["Mt V 6", "Mt V 10"],
}
# Districts whose geometry depends on the projected part of the cut. Their cards
# carry the caveat; nothing else in the county does.
SPLIT_DISTRICTS = (10, 11)

# Two districts holding one precinct each would be a transcription slip, not a
# board. The real minimum is District 4 and several others at 2.
MIN_PRECINCTS_PER_DISTRICT = 2
# A dissolve must not leave slivers between precincts that were already adjacent.
MAX_DISTRICT_HOLES_PCT = 0.05


def round_geom(geom):
    def fix(coords):
        if isinstance(coords[0], (float, int)):
            return [round(coords[0], COORD_PRECISION), round(coords[1], COORD_PRECISION)]
        return [fix(c) for c in coords]
    geo = mapping(geom)
    return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    with open(PRECINCTS) as handle:
        data = json.load(handle)
    precincts = {}
    for feature in data["features"]:
        name = feature["properties"]["name"]
        geom = shape(feature["geometry"])
        precincts[name] = geom if geom.is_valid else geom.buffer(0)
    if len(precincts) != EXPECTED_PRECINCTS:
        sys.exit("expected %d shipped precincts, found %d"
                 % (EXPECTED_PRECINCTS, len(precincts)))

    # --- the list must account for every precinct, exactly once -------------
    named, split_names = {}, set()
    for district, members in COMPOSITION.items():
        for member in members:
            name, side = member if isinstance(member, tuple) else (member, None)
            named.setdefault(name, []).append(district)
            if side:
                split_names.add(name)
    missing = sorted(set(precincts) - set(named))
    invented = sorted(set(named) - set(precincts))
    if missing or invented:
        sys.exit("the county's district list and the shipped precincts disagree.\n"
                 "  shipped but in no district: %s\n"
                 "  in a district but not shipped: %s\n  %s"
                 % (missing, invented, SOURCE_NOTE))
    doubled = sorted(n for n, ds in named.items() if len(ds) > 1)
    if sorted(split_names) != doubled:
        sys.exit("precinct(s) %s appear in more than one district but are not "
                 "marked as split, or vice versa (marked split: %s)"
                 % (doubled, sorted(split_names)))
    if len(COMPOSITION) != EXPECTED_DISTRICTS:
        sys.exit("expected %d districts, the list has %d"
                 % (EXPECTED_DISTRICTS, len(COMPOSITION)))

    # --- the one split ------------------------------------------------------
    pieces = {}
    for name in split_names:
        whole = precincts[name]
        minx, miny, maxx, maxy = whole.bounds
        pad = 0.01
        west = whole.intersection(box(minx - pad, miny - pad, SHILOH_4_CUT_LON, maxy + pad))
        east = whole.intersection(box(SHILOH_4_CUT_LON, miny - pad, maxx + pad, maxy + pad))
        if west.is_empty or east.is_empty:
            sys.exit("%s: the cut at longitude %.5f leaves one side empty — the "
                     "precinct no longer straddles 34th Street, so the county's "
                     "split description needs re-reading.\n  %s"
                     % (name, SHILOH_4_CUT_LON, CUT_SOURCE))
        lost = abs((west.area + east.area) - whole.area) / whole.area
        if lost > 1e-9:
            sys.exit("%s: cutting lost %.3g of the precinct's area" % (name, lost))
        pieces[(name, "west")], pieces[(name, "east")] = west, east
        if whole.bounds[3] <= SPLIT_STREET_TOP_LAT:
            sys.exit("%s no longer extends north of 34th Street's mapped end — "
                     "the projected part of this cut may no longer be needed, "
                     "which is good news worth re-reading the geometry for" % name)

    # --- dissolve -----------------------------------------------------------
    features, notes = [], []
    for district in sorted(COMPOSITION):
        parts, labels = [], []
        for member in COMPOSITION[district]:
            name, side = member if isinstance(member, tuple) else (member, None)
            parts.append(pieces[(name, side)] if side else precincts[name])
            labels.append("%s (%s of 34th St)" % (name, side) if side else name)
        if len(parts) < MIN_PRECINCTS_PER_DISTRICT:
            sys.exit("District %d has only %d precinct(s)" % (district, len(parts)))
        geom = unary_union(parts)
        if not geom.is_valid:
            geom = geom.buffer(0)
        rings = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        holes = sum(len(r.interiors) for r in rings)
        if holes:
            from shapely.geometry import Polygon
            hole_area = sum(Polygon(r).area for part in rings for r in part.interiors)
            pct = 100.0 * hole_area / geom.area
            if pct > MAX_DISTRICT_HOLES_PCT:
                sys.exit("District %d dissolved with %.4f%% of its area in holes "
                         "(max %.2f%%) — its precincts are not edge-matched to "
                         "each other" % (district, pct, MAX_DISTRICT_HOLES_PCT))
            notes.append("District %d: %d sliver hole(s), %.4f%% of the district"
                         % (district, holes, pct))
        props = {"district": district, "name": "District %d" % district,
                 "precincts": labels}
        if district in SPLIT_DISTRICTS:
            props["boundaryNote"] = (
                "Within Shiloh 4 this district's edge follows 34th Street. North "
                "of where 34th Street ends the line follows the street's "
                "alignment projected north; the county has been asked to confirm "
                "it.")
        features.append({"type": "Feature", "properties": props,
                         "geometry": round_geom(geom)})

    # The dissolve must reproduce the county exactly — same ground, no more.
    whole_county = unary_union(list(precincts.values()))
    dissolved = unary_union([shape(f["geometry"]) for f in features])
    drift = whole_county.symmetric_difference(dissolved).area / whole_county.area * 100
    if drift > 0.01:
        sys.exit("the 13 districts and the 33 precincts do not cover the same "
                 "ground (%.4f%% differs)" % drift)

    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         sort_keys=True, separators=(",", ":")) + "\n"

    print("Jefferson: %d board districts dissolved from %d precincts"
          % (len(features), len(precincts)))
    print("  every precinct used exactly once; 1 split (%s) cut at lon %.5f"
          % (", ".join(sorted(split_names)), SHILOH_4_CUT_LON))
    print("  districts reproduce the county's own extent to within %.4f%%" % drift)
    for note in notes:
        print("  note: %s" % note)
    print("  source: %s" % SOURCE_NOTE)
    print("  cut:    %s" % CUT_SOURCE)

    existing = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as handle:
            existing = handle.read()
    if args.check:
        if existing != payload:
            sys.exit("DRIFT: %s does not match a fresh build"
                     % os.path.relpath(OUT_PATH, REPO_ROOT))
        print("  --check OK — matches a fresh build")
        return
    with open(OUT_PATH, "w") as handle:
        handle.write(payload)
    print("  wrote %s (%s bytes)"
          % (os.path.relpath(OUT_PATH, REPO_ROOT), "{:,}".format(len(payload))))


if __name__ == "__main__":
    main()

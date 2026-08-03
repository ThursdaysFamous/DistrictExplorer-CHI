#!/usr/bin/env python3
"""Build Stark County's five district layers from the county's own Google My Maps.

WHAT THIS IS
------------
Stark County (pop. ~5,300) publishes no GIS server, no shapefiles and no
open-data portal. What it publishes instead is a single Google My Maps that the
County Clerk maintains by hand, and that map is unusually complete: county board
districts, precincts, fire, school, library and park districts, plus copies of
the statewide layers. The state's pointer file for Stark contains nothing but a
link to it.

For a year that map was unusable to us for one reason: DATE. The state's pointer
and its companion files date from August 2020 — before the late-2021
redistricting — and the county's online minutes only begin in July 2022, so the
adopting resolution is not published anywhere reachable. A map that might or
might not predate a redistricting is not a source.

That is now settled, and by the only authority that could settle it. County
Clerk Heather Hollis, asked directly, wrote on 3 Aug 2026:

    "The board districts and precincts are correct. The only thing that
     changed on the map is the congressional district."

So: the board districts and precincts are affirmed outright, and the rest of the
map is affirmed as unchanged since it was drawn. We build both halves of that
statement and no more — the congressional districts she names as changed are the
one thing we take from the map under no circumstances (we already carry TIGERweb
for those), and the school, ZIP and municipality folders are skipped because
those are statewide layers here, not Stark's to supply.

WHAT WE SHIP AND WHAT WE DELIBERATELY DO NOT READ
-------------------------------------------------
Five folders become five files. Two attribute decisions are load-bearing:

  * FIRE carries an `Ambulance` column, populated for all six districts, naming
    who actually responds — three different answers (Stark County Ambulance,
    Bradford Rescue Squad, and two departments that run their own). That is a
    real service fact about the point you clicked, so it ships.

  * PARK carries a `Fire Department` column. It is a leftover from whoever built
    the layer by copying the fire layer, and it is WRONG-headed rather than
    merely empty: "LaFayette Park District" claims `Fire Department:
    LaFayette Fire`. We read the park NAME and nothing else. This is the same
    posture as Freeport's stale GIS officer column and Peoria's stale REPNAME —
    a column that exists is not a column that is maintained.

GEOMETRY: HAND-DRAWN, AND MEASURED AS SUCH
------------------------------------------
This is a hand-drawn consumer map, not surveyed GIS, and the honest thing is to
measure it rather than assume either way. Measured against the TIGER county
outline it holds up well, because Stark's precincts ARE congressional-survey
townships and a rectangle is the correct shape for one:

    board districts   99.98% of the county, no overlap, 0.0000% interior gap
    precincts         99.96% of the county, no overlap, 0.0070% interior gap
    library           99.91%, worst pair overlap 0.06%
    fire              99.65%, worst pair overlap 0.02%, 0.0954% interior gap
    park               9.15% — partial by nature; parks do not tile a county

and the two halves agree with each other exactly: every board district is a
whole-precinct union (District 1 = East Toulon + Osceola + Penn + Valley;
District 2 = Elmira + Essex + Goshen + West Jersey + West Toulon), each precinct
falling >= 99.99% inside its district. Two independently drawn folders agreeing
to four decimal places is the strongest internal evidence available that the map
was drawn from real boundaries rather than sketched.

Everything is CLIPPED to the TIGER county outline, because a Stark district
cannot lie outside Stark; that removes the ~0.2% the hand-drawn edges spill over
the county line. What clipping cannot invent is the converse — where a hand-drawn
edge falls just inside the true county line, a hairline of the county is left
unclaimed. The layer answers "no district here" there rather than guessing, and
the guard below holds that hairline to a measured ceiling.

The thresholds are CEILINGS ON ERROR, not floors on record count. A floor cannot
see a swap; these can. If the clerk re-exports the map and a district silently
loses half its area, MIN_COVERAGE and MAX_PAIR_OVERLAP fail the build.

Usage:
    python3 scripts/build_stark_districts.py            # write data/app/*.json
    python3 scripts/build_stark_districts.py --check    # drift gate, writes nothing
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    from shapely.geometry import Polygon, shape, mapping
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover
    sys.exit("shapely is required: pip install -c scripts/requirements.txt shapely")

KML_NS = {"k": "http://www.opengis.net/kml/2.2"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_KML = os.path.join(ROOT, "data", "source", "raw",
                          "Stark County Illinois Maps 2026-08-03.kml")
OUTLINE = os.path.join(ROOT, "data", "app", "stark-county-outline.json")
APP_DIR = os.path.join(ROOT, "data", "app")

# The live export, kept here so a future operator can refresh the archive without
# hunting for the id. We do NOT fetch it at build time: a hand-maintained consumer
# map can change under us between a build and its verification, and the whole
# reason this county is buildable is a dated statement about one specific export.
SOURCE_URL = ("https://www.google.com/maps/d/kml"
              "?mid=1T0Iz1DogKirf-ZbEfFlFoIRSAxY&forcekml=1")

COORD_PRECISION = 6  # ~0.1 m; the source is hand-drawn, more digits are noise

# folder -> spec. `count` is EXACT, not a floor (see module docstring).
# `min_coverage` is the share of the county the folder must tile; `partial`
# marks the folders that are not supposed to tile it at all.
LAYERS = [
    {
        "folder": "County Board Districts",
        "out": "stark-county-board-districts.json",
        "count": 2,
        "min_coverage": 99.9,
        "max_pair_overlap": 0.01,
        "name_from": "placemark",
        "extra": {},
        # the shapes are named "County Board District 1"/"2"; every other county
        # board file in the fleet carries a bare `district`, so lift it here
        # rather than making the app parse a label
        "district_from_name": re.compile(r"(?i)^County Board District\s+(\d+)$"),
    },
    {
        "folder": "Precincts",
        "out": "stark-precincts.json",
        "count": 9,
        "min_coverage": 99.9,
        "max_pair_overlap": 0.01,
        "name_from": "placemark",
        "extra": {},
    },
    {
        "folder": "Fire Districts",
        "out": "stark-fire-districts.json",
        "count": 6,
        "min_coverage": 99.5,
        "max_pair_overlap": 0.10,
        "name_from": "placemark",
        # the one attribute column on this map that is real and maintained
        "extra": {"ambulance": "Ambulance"},
    },
    {
        "folder": "Library Districts",
        "out": "stark-library-districts.json",
        "count": 6,
        "min_coverage": 99.5,
        "max_pair_overlap": 0.10,
        "name_from": "placemark",
        "extra": {},
    },
    {
        "folder": "Park Districts",
        "out": "stark-park-districts.json",
        "count": 2,
        "partial": True,          # parks cover ~9% of the county, by nature
        "max_pair_overlap": 0.01,
        "name_from": "placemark",
        "extra": {},              # NOT the stale `Fire Department` column
    },
]

# Board districts must decompose into whole precincts. This is the cross-check
# that makes the whole build trustworthy — see the module docstring.
BOARD_COMPOSITION = {
    "County Board District 1": ["East Toulon", "Osceola", "Penn", "Valley"],
    "County Board District 2": ["Elmira", "Essex", "Goshen", "West Jersey",
                                "West Toulon"],
}
MIN_PRECINCT_IN_DISTRICT = 99.9  # percent of each precinct inside its district

SEATS_PER_DISTRICT = 4  # 8-member board, evenly split


def ring_coords(linear_ring):
    text = linear_ring.findtext("k:coordinates", default="", namespaces=KML_NS)
    out = []
    for token in text.split():
        parts = token.split(",")
        out.append((float(parts[0]), float(parts[1])))
    return out


def placemark_polygon(placemark):
    """Every Polygon in a placemark, unioned. KML states holes explicitly via
    innerBoundaryIs, so unlike the Esri ring format there is nothing to infer."""
    polys = []
    for poly in placemark.findall(".//k:Polygon", KML_NS):
        outer = poly.find("k:outerBoundaryIs/k:LinearRing", KML_NS)
        if outer is None:
            continue
        inners = [ring_coords(r) for r in
                  poly.findall("k:innerBoundaryIs/k:LinearRing", KML_NS)]
        geom = Polygon(ring_coords(outer), inners)
        if not geom.is_valid:
            geom = geom.buffer(0)
        polys.append(geom)
    if not polys:
        return None
    return unary_union(polys)


def placemark_data(placemark):
    out = {}
    for data in placemark.findall(".//k:Data", KML_NS):
        key = data.get("name")
        value = (data.findtext("k:value", default="", namespaces=KML_NS) or "").strip()
        if key and value:
            out[key] = value
    return out


def read_folders(path):
    doc = ET.parse(path).getroot().find("k:Document", KML_NS)
    if doc is None:
        raise RuntimeError("%s has no kml:Document" % path)
    folders = {}
    for folder in doc.findall("k:Folder", KML_NS):
        name = folder.findtext("k:name", default="", namespaces=KML_NS).strip()
        folders[name] = folder.findall("k:Placemark", KML_NS)
    return folders


def round_geom(geom):
    """Round to COORD_PRECISION. Done on the mapping, not the shapely object, so
    the measurements above are made at full precision and only the OUTPUT is
    rounded — rounding first would move the very edges we are measuring."""
    def fix(coords):
        if isinstance(coords[0], (float, int)):
            return [round(coords[0], COORD_PRECISION), round(coords[1], COORD_PRECISION)]
        return [fix(c) for c in coords]

    geo = mapping(geom)
    return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}


def build_layer(spec, placemarks, outline, warnings):
    if len(placemarks) != spec["count"]:
        raise RuntimeError(
            "%s: expected exactly %d shapes, found %d. This is an exact count, "
            "not a floor — if the clerk added or removed a district the change "
            "needs a human look before it ships."
            % (spec["folder"], spec["count"], len(placemarks)))

    geoms = {}
    props = {}
    for placemark in placemarks:
        name = placemark.findtext("k:name", default="", namespaces=KML_NS).strip()
        if not name:
            raise RuntimeError("%s: a shape has no name" % spec["folder"])
        if name in geoms:
            raise RuntimeError("%s: duplicate shape name %r" % (spec["folder"], name))
        geom = placemark_polygon(placemark)
        if geom is None or geom.is_empty:
            raise RuntimeError("%s: %s has no polygon" % (spec["folder"], name))
        geoms[name] = geom
        data = placemark_data(placemark)
        props[name] = {out_key: data[src_key]
                       for out_key, src_key in spec["extra"].items()
                       if data.get(src_key)}

    # --- measure BEFORE clipping, against the true county outline -------------
    union = unary_union(list(geoms.values()))
    coverage = union.intersection(outline).area / outline.area * 100.0
    spill = union.difference(outline).area / outline.area * 100.0

    worst_overlap = 0.0
    worst_pair = None
    names = list(geoms)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            area = geoms[names[i]].intersection(geoms[names[j]]).area
            if area > worst_overlap:
                worst_overlap = area
                worst_pair = (names[i], names[j])
    worst_overlap_pct = worst_overlap / outline.area * 100.0

    if not spec.get("partial"):
        if coverage < spec["min_coverage"]:
            raise RuntimeError(
                "%s tiles only %.2f%% of Stark County (need >= %.2f%%). A tiling "
                "layer that loses area has lost a district, not precision."
                % (spec["folder"], coverage, spec["min_coverage"]))
    if worst_overlap_pct > spec["max_pair_overlap"]:
        raise RuntimeError(
            "%s: %s and %s overlap by %.4f%% of the county (max %.2f%%). Two "
            "districts claiming the same ground is a redraw, not a seam."
            % (spec["folder"], worst_pair[0], worst_pair[1],
               worst_overlap_pct, spec["max_pair_overlap"]))
    if worst_pair and worst_overlap_pct > 0:
        warnings.append("%s: %s and %s overlap by %.4f%% of the county — a "
                        "hand-drawn seam; the app answers with whichever is "
                        "found first." % (spec["folder"], worst_pair[0],
                                          worst_pair[1], worst_overlap_pct))

    # --- clip: a Stark district cannot lie outside Stark ----------------------
    features = []
    for name in sorted(geoms):
        clipped = geoms[name].intersection(outline)
        if clipped.is_empty:
            raise RuntimeError("%s: %s falls entirely outside the county"
                               % (spec["folder"], name))
        if not clipped.is_valid:
            clipped = clipped.buffer(0)
        feature_props = {"name": name}
        pattern = spec.get("district_from_name")
        if pattern:
            match = pattern.match(name)
            if not match:
                raise RuntimeError("%s: %r does not name a district number"
                                   % (spec["folder"], name))
            feature_props["district"] = match.group(1)
        feature_props.update(props[name])
        features.append({"type": "Feature",
                         "properties": feature_props,
                         "geometry": round_geom(clipped)})

    stats = {"coverage": coverage, "spill": spill,
             "overlap": worst_overlap_pct}
    return {"type": "FeatureCollection", "features": features}, geoms, stats


def cross_check_board(board_geoms, precinct_geoms):
    """The board folder and the precinct folder were drawn separately. If they
    agree to four decimals, the map was drawn from real boundaries."""
    worst = 100.0
    for district, members in BOARD_COMPOSITION.items():
        if district not in board_geoms:
            raise RuntimeError("board cross-check: %r missing from the map" % district)
        dgeom = board_geoms[district]
        for precinct in members:
            if precinct not in precinct_geoms:
                raise RuntimeError("board cross-check: precinct %r missing" % precinct)
            pgeom = precinct_geoms[precinct]
            share = pgeom.intersection(dgeom).area / pgeom.area * 100.0
            worst = min(worst, share)
            if share < MIN_PRECINCT_IN_DISTRICT:
                raise RuntimeError(
                    "board cross-check: precinct %s sits only %.2f%% inside %s "
                    "(need >= %.2f%%). The board districts and the precincts no "
                    "longer agree, which means one of the two folders was "
                    "redrawn — stop and re-verify with the County Clerk."
                    % (precinct, share, district, MIN_PRECINCT_IN_DISTRICT))
    assigned = sorted(p for members in BOARD_COMPOSITION.values() for p in members)
    if assigned != sorted(precinct_geoms):
        missing = sorted(set(precinct_geoms) - set(assigned))
        extra = sorted(set(assigned) - set(precinct_geoms))
        raise RuntimeError("board cross-check: every precinct must belong to "
                           "exactly one district (unassigned: %s; unknown: %s)"
                           % (missing or "none", extra or "none"))
    return worst


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    if not os.path.exists(SOURCE_KML):
        sys.exit("missing archived export: %s\n(refresh from %s)"
                 % (SOURCE_KML, SOURCE_URL))

    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)

    folders = read_folders(SOURCE_KML)
    warnings = []
    built = {}
    raw_geoms = {}
    all_stats = {}

    for spec in LAYERS:
        placemarks = folders.get(spec["folder"])
        if placemarks is None:
            sys.exit("the export no longer has a %r folder — it now has: %s"
                     % (spec["folder"], ", ".join(sorted(folders))))
        collection, geoms, stats = build_layer(spec, placemarks, outline, warnings)
        built[spec["out"]] = collection
        raw_geoms[spec["folder"]] = geoms
        all_stats[spec["folder"]] = stats

    worst_share = cross_check_board(raw_geoms["County Board Districts"],
                                    raw_geoms["Precincts"])

    # Carry the (now cross-checked) composition onto the board features, so the
    # precinct card can name its board district by exact membership rather than
    # by a second point-in-polygon test against a hand-drawn seam.
    for feature in built["stark-county-board-districts.json"]["features"]:
        feature["properties"]["precincts"] = sorted(
            BOARD_COMPOSITION[feature["properties"]["name"]])

    for spec in LAYERS:
        stats = all_stats[spec["folder"]]
        print("%-24s %d shapes | covers %6.2f%% of county | spilled %.2f%% "
              "(clipped) | worst overlap %.4f%%"
              % (spec["folder"], spec["count"], stats["coverage"],
                 stats["spill"], stats["overlap"]))
    print("board/precinct cross-check: every precinct >= %.2f%% inside its "
          "district (worst %.2f%%)" % (MIN_PRECINCT_IN_DISTRICT, worst_share))
    for warning in warnings:
        print("  note: %s" % warning)

    changed = []
    for name, collection in sorted(built.items()):
        path = os.path.join(APP_DIR, name)
        payload = json.dumps(collection, indent=1, sort_keys=True) + "\n"
        existing = None
        if os.path.exists(path):
            with open(path) as handle:
                existing = handle.read()
        if existing != payload:
            changed.append(name)
            if not args.check:
                with open(path, "w") as handle:
                    handle.write(payload)

    if args.check:
        if changed:
            sys.exit("drift: %s differ from what the archived export builds. "
                     "Re-run without --check." % ", ".join(changed))
        print("--check: all five files match the archived export")
        return

    if changed:
        print("wrote %s" % ", ".join(changed))
    else:
        print("no change")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Montgomery County's 7 board districts AND 38 voting precincts.

Both come out of one archive, so they are built by one script — and that is not
just convenience. The two layers CROSS-CHECK each other against a document the
county publishes, which is the only reason this data could be trusted at all
(see "THE LAYER IS NAMED _2010" below). Splitting them into two builders would
put the interesting guard in neither.

SOURCE, AND WHY IT IS AN E-MAIL RATHER THAN A URL. Montgomery publishes no
boundaries: its GIS page links a Beacon/Schneider parcel viewer, and the gap
record `montgomery-county-board-geometry` recorded (2 Aug 2026) that the county
had "one of the best board member lists we have found and no district
boundaries at all". The request went out 5 Aug 2026; on 6 Aug Kevin Brink, GIS
Tech / Plat Act Officer, replied "Please see attached" with the archive this
script reads. Refreshing it means asking again, which is the Ogle and Henry
shape, and the reason this reads from data/source/raw/ rather than the web.

A FILE GEODATABASE, WHICH IS A FIRST HERE. Every previous county sent a
shapefile; Montgomery sent an ESRI .gdb, a directory of binary tables. pyogrio
reads it through GDAL's /vsizip/ handler straight out of the archived zip, so
the bytes the county sent are what ship — nothing is converted by hand in
between, which is the property that makes "ask again" a real refresh path.

THE LAYER IS NAMED `CountyBoardDistricts_2010`, AND IT IS NOT STALE. That name
is the first thing to check and the easiest thing to get wrong, because an
Illinois county MUST reapportion after each census and a 2010-cycle map would be
five years superseded. Two independent things say it is current:

  1. ARITHMETIC. The districts' Pop100 values sum to 28,210. District 4 carries
     the comment "5949-1894 (Graham CC) = 4055" — Graham Correctional Center,
     backed out of that district — so the RAW sum is 30,104, which is exactly
     Montgomery County's 2010 census population. (2020 was 28,288.) So the
     population data is 2010-vintage, and `_2010` names the census, not the map.

  2. THE COUNTY'S OWN POST-2020 CHART. The Clerk publishes "MONTGOMERY COUNTY
     DISTRICTS AFTER REDISTRICTING 2020-2030", a precinct-by-precinct table of
     which district each precinct is in. This geometry reproduces that table
     EXACTLY — all 38 precincts, including all five precincts the chart splits
     between two districts. Montgomery reapportioned after 2020 and kept its
     lines, which is why a 2010-population file is still the map in force.

That second check is asserted below rather than merely having been done once:
COMPOSITION is this file's real guard. A future export that moves a boundary
enough to change which district a precinct sits in fails the build, and the
person re-running it is pointed back at the county's chart. It is a much
sharper test than any count or area threshold, because it compares the geometry
against something the county SAYS in words.

SHIPPED AS DRAWN — NO REPAIR, DELIBERATELY. Both tilings have hairline cracks
where neighbours' edges were never snapped: 55 slivers in the districts, 184 in
the precincts, long and a couple of metres wide. That is the same defect
Jefferson had, at a completely different scale:

    Jefferson as sent      0.788%  in a crack   ~1 click in 127   -> repaired
    Jefferson repaired     0.025%               ~1 click in 4,000
    Montgomery districts   0.0064%              ~1 click in 15,600
    Montgomery precincts   0.0034%              ~1 click in 29,400

Montgomery as sent is several times cleaner than Jefferson ended up AFTER its
Voronoi repair, so repairing here would move real boundaries to buy nothing.
MAX_INTERNAL_HOLES_PCT asserts that this stays true: if a future export is as
bad as Jefferson's was, this build fails rather than quietly shipping it.

Those percentages are of INTERNAL crack area, which is not the same measure as
"coverage of the shipped outline" — check_tiling explains why, and prints both,
so this comparison and the build's own output can never drift apart.

PROJECTION. NAD83 / StatePlane Illinois West FIPS 1202, US survey feet
(EPSG:3436), as the geodatabase declares. Reprojected here with pyproj rather
than shipped as-is, because the app does point-in-polygon in degrees. The
reprojection is checked rather than trusted: the result must land on the county
outline the app already ships, which an EPSG mistake could not do.

Usage:
    python3 scripts/build_montgomery_boundaries.py            # write data/app/
    python3 scripts/build_montgomery_boundaries.py --check    # drift gate
"""

import argparse
import json
import os
import re
import sys

try:
    import pyogrio
    from pyproj import Transformer
    from shapely import wkb
    from shapely.geometry import Polygon, shape, mapping
    from shapely.ops import transform as shapely_transform, unary_union
except ImportError:  # pragma: no cover
    sys.exit("pyogrio, pyproj and shapely are required: "
             "pip install -c scripts/requirements.txt pyogrio pyproj shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ZIP = os.path.join(REPO_ROOT, "data", "source", "raw",
                          "MontgomeryCountyIL_GIS_2026-08-06.zip")
GDB_IN_ZIP = "Overberg Data/OverbergData.gdb"
OUTLINE = os.path.join(REPO_ROOT, "data", "app", "montgomery-county-outline.json")
DISTRICTS_OUT = os.path.join(REPO_ROOT, "data", "app",
                             "montgomery-county-board-districts.json")
PRECINCTS_OUT = os.path.join(REPO_ROOT, "data", "app", "montgomery-precincts.json")

DISTRICT_LAYER = "CountyBoardDistricts_2010"
PRECINCT_LAYER = "Precincts"

SOURCE_NOTE = ("Montgomery County GIS (Kevin Brink, GIS Tech/Plat Act Officer), "
               "file geodatabase supplied by e-mail 2026-08-06")
COMPOSITION_SOURCE = ("Montgomery County Clerk & Recorder, \"Montgomery County "
                      "Districts After Redistricting 2020-2030\", "
                      "montgomerycountyil.gov/wp-content/uploads/"
                      "MONTGOMERYCOUNTYREDISTRICTING2020-2030DISTRICTS.pdf")

SOURCE_EPSG = "EPSG:3436"
COORD_PRECISION = 6

EXPECTED_DISTRICTS = 7          # exact: the county seats two members from each
EXPECTED_PRECINCTS = 38         # exact: the county's own export, 2026-08-06

# The 2010 P.L. 94-171 count for Montgomery County, and the prison population
# District 4 backs out of its own total. Asserted because together they are what
# proves `_2010` is the census vintage rather than a superseded map — if a future
# export carries 2020 numbers, the map was redrawn and everything below needs
# re-checking against the county before it ships.
POP_2010_COUNTY = 30104
GRAHAM_CC_ADJUSTMENT = 1894

MIN_COVERAGE = 99.5             # both layers tile the whole county
MAX_PAIR_OVERLAP = 0.05         # percent of county area, worst single pair
# The "do not silently become Jefferson" ceiling, on INTERNAL cracks rather than
# on coverage — see check_tiling for why those are different questions. Measured
# 2026-08-06 at 0.0064% (districts) and 0.0034% (precincts); set an order of
# magnitude above that so ordinary re-digitising passes and a genuinely broken
# export does not. Jefferson's as-sent file was 0.788%, 120x this ceiling.
MAX_INTERNAL_HOLES_PCT = 0.05
# A precinct counts as belonging to a district when this much of its area is
# there. The real data leaves a wide margin either side: the smallest genuine
# split share is Hillsboro 5's 7.0% in District 6, and the largest digitising
# slop on a whole precinct is 0.4%.
SPLIT_THRESHOLD_PCT = 2.0

EXTENT_TOLERANCE_DEG = 0.01

# The county's published composition, transcribed from COMPOSITION_SOURCE.
# Keys are precinct names normalised by norm(); values are the district (or the
# set of districts, where the county splits a precinct) that chart assigns.
# This is the assertion that makes the geometry trustworthy — see the module
# docstring. Do not "fix" a mismatch here to make a build pass: a mismatch means
# the map and the chart disagree, which is a question for the county.
COMPOSITION = {
    "AUDUBON": {2},
    "BOIS D'ARC": {1},
    "BUTLER GROVE": {1, 6},          # N 1/2 & NW -> 1; SE Terr. incl. Butler -> 6
    "EAST FORK 1": {3, 4},           # N of Coffeen & Rt 185 -> 3; Coffeen + S -> 4
    "EAST FORK 2": {4},
    "EAST FORK 3": {3},
    "FILLMORE CONSOLIDATED": {3},
    "GRISHAM 1": {4},
    "GRISHAM 2": {4},
    "HARVEL": {1},
    "HILLSBORO 1": {6},
    "HILLSBORO 2": {6},
    "HILLSBORO 3": {6},
    "HILLSBORO 4": {6},
    "HILLSBORO 5": {4, 6},           # SW Rural + Center -> 4; Eastern City -> 6
    "HILLSBORO 6": {4},
    "IRVING": {3},
    "NOKOMIS 1": {2},
    "NOKOMIS 2": {2},
    "NOKOMIS 3": {2},
    "NOKOMIS 4": {2},
    "NORTH LITCHFIELD 1": {1, 7},    # NE Terr. E of I-55 -> 1; SE Terr. E of I-55 -> 7
    "NORTH LITCHFIELD 2": {7},
    "NORTH LITCHFIELD 3": {7},
    "NORTH LITCHFIELD 4": {5},
    "NORTH LITCHFIELD 5": {7},
    "NORTH LITCHFIELD 6": {7},
    "PITMAN": {1},
    "RAYMOND": {1, 2},               # Village of Raymond + surrounds -> 1; rest -> 2
    "ROUNTREE": {2},
    "SOUTH LITCHFIELD 1": {5},
    "SOUTH LITCHFIELD 2": {5},
    "SOUTH LITCHFIELD 3": {5},
    "SOUTH LITCHFIELD 4": {5},
    "WALSHVILLE": {4},
    "WITT 1": {3},
    "WITT 2": {3},
    "ZANESVILLE": {1},
}


def norm(name):
    """Precinct name as COMPOSITION keys it: upper, single-spaced, straight quote."""
    return re.sub(r"\s+", " ", str(name or "").replace("’", "'").strip()).upper()


def read_layer(layer):
    """[(attrs, shapely geometry in EPSG:3436)] for one geodatabase layer."""
    path = "/vsizip/%s/%s" % (SOURCE_ZIP, GDB_IN_ZIP)
    meta, _, geoms, fields = pyogrio.raw.read(path, layer=layer)
    names = list(meta["fields"])
    cols = dict(zip(names, fields))
    rows = []
    for i, raw in enumerate(geoms):
        geom = wkb.loads(bytes(raw))
        if not geom.is_valid:
            geom = geom.buffer(0)
        rows.append(({n: cols[n][i] for n in names}, geom))
    return rows


def round_geom(geom):
    def fix(coords):
        if isinstance(coords[0], (float, int)):
            return [round(coords[0], COORD_PRECISION), round(coords[1], COORD_PRECISION)]
        return [fix(c) for c in coords]
    geo = mapping(geom)
    return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}


def dump(features):
    """Compact, following henry-precincts.json — this is fetched, not read."""
    features.sort(key=lambda f: f["properties"].get("sort", f["properties"]["name"]))
    for f in features:
        f["properties"].pop("sort", None)
    return json.dumps({"type": "FeatureCollection", "features": features},
                      sort_keys=True, separators=(",", ":")) + "\n"


def check_tiling(label, geoms, outline, notes):
    """Coverage and overlap, measured two ways because they answer two questions.

    COVERAGE vs the shipped outline is the threshold guard every other county
    builder uses, so it is what the MIN_COVERAGE floor compares. It is also an
    upper bound on the real defect: the shipped outline is simplified at 25 m,
    so most of what it reports as "uncovered" is a hairline band along the county
    line rather than anything a click inland could land in.

    INTERNAL HOLES is the number that is comparable to Jefferson's, and the one
    the module docstring quotes. Jefferson's 0.788%% was a connected lattice of
    cracks running THROUGH the county, which is what makes a click answer "not
    in any district" somewhere a resident actually lives. Measuring the same
    thing here means measuring the union's interior rings, not its difference
    from an approximate boundary.
    """
    union = unary_union(list(geoms.values()))
    coverage = union.intersection(outline).area / outline.area * 100.0
    uncovered = outline.difference(union).area / outline.area * 100.0
    parts = list(union.geoms) if union.geom_type == "MultiPolygon" else [union]
    hole_area = sum(Polygon(ring).area for part in parts for ring in part.interiors)
    holes = 100.0 * hole_area / union.area
    hole_count = sum(len(part.interiors) for part in parts)
    keys = list(geoms)
    worst, worst_pair = 0.0, None
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            area = geoms[keys[i]].intersection(geoms[keys[j]]).area
            if area > worst:
                worst, worst_pair = area, (keys[i], keys[j])
    worst_pct = worst / outline.area * 100.0
    if coverage < MIN_COVERAGE:
        sys.exit("%s tile only %.3f%% of Montgomery County (need >= %.2f%%)"
                 % (label, coverage, MIN_COVERAGE))
    if holes > MAX_INTERNAL_HOLES_PCT:
        sys.exit("%s leave %.4f%% of the county in a crack between neighbours "
                 "(max %.2f%%) — that is the Jefferson failure mode; measure it "
                 "the way build_jefferson_precincts.py documents and decide "
                 "whether a repair is warranted before shipping"
                 % (label, holes, MAX_INTERNAL_HOLES_PCT))
    if worst_pct > MAX_PAIR_OVERLAP:
        sys.exit("%s: %s and %s overlap by %.4f%% of the county (max %.2f%%)"
                 % (label, worst_pair[0], worst_pair[1], worst_pct, MAX_PAIR_OVERLAP))
    notes.append("%s: tile %.3f%% of the shipped outline (%.4f%% outside, mostly "
                 "its 25 m simplification); %d internal cracks totalling %.4f%% "
                 "= ~1 click in %s; worst pair overlap %.4f%%"
                 % (label, coverage, uncovered, hole_count, holes,
                    "{:,}".format(int(100 / holes)) if holes else "inf", worst_pct))
    return union


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    if not os.path.exists(SOURCE_ZIP):
        sys.exit("missing archived source: %s" % SOURCE_ZIP)

    to_wgs84 = Transformer.from_crs(SOURCE_EPSG, "EPSG:4326", always_xy=True).transform
    notes = []

    # ---- districts -------------------------------------------------------
    rows = read_layer(DISTRICT_LAYER)
    if len(rows) != EXPECTED_DISTRICTS:
        sys.exit("expected %d board districts, the export has %d — Montgomery "
                 "seats two members from each of seven, so a different count "
                 "means the board changed shape" % (EXPECTED_DISTRICTS, len(rows)))
    dist_geoms, dist_features, pop_total = {}, [], 0
    for attrs, geom in rows:
        num = int(attrs["District"])
        if num in dist_geoms:
            sys.exit("duplicate district number %d" % num)
        pop_total += int(attrs["Pop100"])
        wgs = shapely_transform(to_wgs84, geom)
        dist_geoms[num] = wgs
        dist_features.append({
            "type": "Feature",
            "properties": {"district": num, "name": "District %d" % num,
                           "sort": "%02d" % num},
            "geometry": round_geom(wgs),
        })
    raw_pop = pop_total + GRAHAM_CC_ADJUSTMENT
    if raw_pop != POP_2010_COUNTY:
        sys.exit("district populations sum to %d (+%d backed out for Graham CC) "
                 "= %d, but Montgomery's 2010 census count is %d. The export's "
                 "population vintage changed, which is the signal that the map "
                 "was redrawn — re-verify against the county's redistricting "
                 "chart before shipping.\n  %s"
                 % (pop_total, GRAHAM_CC_ADJUSTMENT, raw_pop, POP_2010_COUNTY,
                    COMPOSITION_SOURCE))
    notes.append("districts: Pop100 sums to %d, +%d for Graham CC = %d = the 2010 "
                 "census count, so `_2010` is the population vintage"
                 % (pop_total, GRAHAM_CC_ADJUSTMENT, raw_pop))

    # ---- precincts -------------------------------------------------------
    rows = read_layer(PRECINCT_LAYER)
    if len(rows) != EXPECTED_PRECINCTS:
        sys.exit("expected %d precincts, the export has %d — re-check the county's "
                 "precinct list before shipping" % (EXPECTED_PRECINCTS, len(rows)))
    prec_geoms, prec_features = {}, []
    for attrs, geom in rows:
        name = norm(attrs["NAME"])
        if not name:
            sys.exit("a precinct has no NAME: %r" % attrs)
        if name in prec_geoms:
            sys.exit("duplicate precinct name %r" % name)
        code = str(attrs.get("VOTE00") or "").strip()
        wgs = shapely_transform(to_wgs84, geom)
        prec_geoms[name] = wgs
        props = {"name": name.title().replace("'S", "'s"), "sort": name}
        if code:
            props["code"] = code
        prec_features.append({"type": "Feature", "properties": props,
                              "geometry": round_geom(wgs)})

    # ---- the reprojection check, before the expensive geometry work ------
    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)
    for label, geoms in (("districts", dist_geoms), ("precincts", prec_geoms)):
        ub, ob = unary_union(list(geoms.values())).bounds, outline.bounds
        drift = max(abs(u - o) for u, o in zip(ub, ob))
        if drift > EXTENT_TOLERANCE_DEG:
            sys.exit("reprojected %s span %s but the county outline spans %s "
                     "(worst edge off by %.4f deg) — check SOURCE_EPSG"
                     % (label, ub, ob, drift))

    check_tiling("districts", dist_geoms, outline, notes)
    check_tiling("precincts", prec_geoms, outline, notes)

    # ---- THE COMPOSITION CROSS-CHECK ------------------------------------
    # Every precinct must land in exactly the district(s) the county's own
    # post-2020 chart puts it in. This is what proves the geometry is the map in
    # force rather than a 2010 leftover, and it is asserted on every build.
    if set(COMPOSITION) != set(prec_geoms):
        missing = sorted(set(COMPOSITION) - set(prec_geoms))
        extra = sorted(set(prec_geoms) - set(COMPOSITION))
        sys.exit("the export's precincts and the county's chart name different "
                 "precincts.\n  only in the chart: %s\n  only in the export: %s\n  %s"
                 % (missing, extra, COMPOSITION_SOURCE))
    disagreements, split_count = [], 0
    for name, geom in sorted(prec_geoms.items()):
        found = set()
        for num, dgeom in dist_geoms.items():
            share = 100.0 * geom.intersection(dgeom).area / geom.area
            if share >= SPLIT_THRESHOLD_PCT:
                found.add(num)
        if found != COMPOSITION[name]:
            disagreements.append((name, sorted(COMPOSITION[name]), sorted(found)))
        if len(found) > 1:
            split_count += 1
    if disagreements:
        lines = "\n".join("    %-22s chart says %s, geometry says %s"
                          % (n, c, g) for n, c, g in disagreements)
        sys.exit("the geometry disagrees with the county's published district "
                 "composition for %d precinct(s):\n%s\n  This is not a threshold "
                 "to loosen — it means the map and the chart describe different "
                 "districts. Ask the county which is current.\n  %s"
                 % (len(disagreements), lines, COMPOSITION_SOURCE))
    notes.append("composition: all %d precincts match the county's published "
                 "2020-2030 chart, including all %d it splits between districts"
                 % (len(prec_geoms), split_count))

    payloads = {DISTRICTS_OUT: dump(dist_features), PRECINCTS_OUT: dump(prec_features)}

    print("Montgomery: %d board districts, %d precincts" % (len(dist_geoms), len(prec_geoms)))
    for note in notes:
        print("  %s" % note)
    print("  source: %s" % SOURCE_NOTE)

    drifted = False
    for path, payload in payloads.items():
        existing = None
        if os.path.exists(path):
            with open(path) as handle:
                existing = handle.read()
        if args.check:
            if existing != payload:
                print("DRIFT: %s does not match a fresh build" % os.path.relpath(path, REPO_ROOT),
                      file=sys.stderr)
                drifted = True
            continue
        with open(path, "w") as handle:
            handle.write(payload)
        print("  wrote %s (%s bytes)"
              % (os.path.relpath(path, REPO_ROOT), "{:,}".format(len(payload))))
    if args.check:
        if drifted:
            sys.exit(1)
        print("  --check OK — both files match a fresh build")


if __name__ == "__main__":
    main()

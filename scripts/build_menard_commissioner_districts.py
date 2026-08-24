#!/usr/bin/env python3
"""Build Menard County's 5 commissioner districts from the county's own export.

SOURCE, AND THE CHAIN THAT PRODUCED IT. Menard publishes no boundary: the only
map is a flat picture on the state's site dated 8 Dec 2021, and the county's
viewer is a commercial parcel product. `menard-commissioner-districts` recorded
that, and recorded why the usual rescue does not work here — THE DISTRICT LINES
FOLLOW SECTION-LINE ROADS, NOT PRECINCT EDGES, so no combination of the county's
14 precincts reproduces them and the Jefferson-style dissolve is unavailable.

Asked 3 Aug 2026. Clerk & Recorder Martha "Marty" Gum answered the next day,
looped in Supervisor of Assessments Dawn Kelton, who requested the file from
Beacon (the county's GIS vendor) and forwarded it on 7 Aug. Three offices and
one vendor, four days. The archive is data/source/raw/, so refreshing it means
asking again — the Ogle and Henry shape.

THE CLEANEST COUNTY FILE THIS CAMPAIGN HAS RECEIVED, measured: zero invalid
geometries, zero self-overlap, and ZERO internal holes — the five polygons are
properly edge-matched to each other, which neither Jefferson's nor Montgomery's
were. Nothing here needed repairing and nothing was repaired.

IT PROVES ITSELF AGAINST THE CENSUS. The districts' POP20 values sum to 12,297,
which is exactly Menard County's 2020 census population. That is asserted on
every build: an export whose populations no longer add up to the county is
either a different vintage or a different county, and either way must not ship
quietly. (Montgomery's builder makes the same check for the same reason, and
there it was what proved a file named "_2010" was current.)

A CORRECTION WORTH KEEPING. The request that produced this file asked for
"the three district polygons". Menard has FIVE. The gap record had it right all
along — it says five, and it even quoted the population range printed on the
state's map, 2,436 to 2,486, which is exactly this file's five values. The error
was in the e-mail, not the record: a district count was asserted from a picture
that could not be read properly. The county ignored the wrong premise and sent
the real thing. Read your own gap record before you write the ask.

PROJECTION. The .prj declares GCS_North_American_1983 — GEOGRAPHIC degrees
(EPSG:4269), not a projected state plane like every other county file here. So
the transform is a datum shift to WGS84 rather than a projection, and it moves
coordinates by about a metre. It is still done explicitly rather than by
assuming the two are interchangeable, and the extent check below would catch it
either way.

Usage:
    python3 scripts/build_menard_commissioner_districts.py            # write
    python3 scripts/build_menard_commissioner_districts.py --check    # drift gate
"""

import argparse
import json
import os
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
SOURCE_ZIP = os.path.join(REPO_ROOT, "il", "data", "source", "raw",
                          "MenardCountyIL_CountyBoardDistricts_2026-08-07.zip")
SHAPE_IN_ZIP = "CountyBoardDistricts.shp"
OUTLINE = os.path.join(REPO_ROOT, "il", "data", "app", "menard-county-outline.json")
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app",
                        "menard-commissioner-districts.json")

SOURCE_NOTE = ("Menard County, Beacon/Schneider export of the Commissioner "
               "Districts, supplied by Supervisor of Assessments Dawn Kelton "
               "by e-mail 2026-08-07 at County Clerk & Recorder Martha Gum's "
               "request")

SOURCE_EPSG = "EPSG:4269"          # NAD83 geographic, per the .prj
COORD_PRECISION = 6

EXPECTED_DISTRICTS = 5
POP_2020_COUNTY = 12297            # Census 2020, Menard County (FIPS 17129)

MIN_COVERAGE = 99.5
MAX_PAIR_OVERLAP = 0.05
# This file arrived with NO internal holes. The ceiling is deliberately tight
# because there is nothing to tolerate: a future export that develops cracks is
# a change worth stopping for, not a nuisance to absorb.
MAX_INTERNAL_HOLES_PCT = 0.01
EXTENT_TOLERANCE_DEG = 0.01


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

    if not os.path.exists(SOURCE_ZIP):
        sys.exit("missing archived source: %s" % SOURCE_ZIP)

    to_wgs84 = Transformer.from_crs(SOURCE_EPSG, "EPSG:4326", always_xy=True).transform
    meta, _, geoms, fields = pyogrio.raw.read(
        "/vsizip/%s/%s" % (SOURCE_ZIP, SHAPE_IN_ZIP))
    names = list(meta["fields"])
    cols = dict(zip(names, fields))
    if len(geoms) != EXPECTED_DISTRICTS:
        sys.exit("expected %d commissioner districts, the export has %d — Menard "
                 "seats five, so a different count means the board changed shape"
                 % (EXPECTED_DISTRICTS, len(geoms)))

    districts, features, pop_total = {}, [], 0
    for i in range(len(geoms)):
        num = int(cols["DIST_ID"][i])
        if num in districts:
            sys.exit("duplicate district number %d" % num)
        label = str(cols["DistrictNa"][i] or "").strip()
        if not label:
            sys.exit("District %d has no name in the export" % num)
        pop_total += int(cols["POP20"][i])
        geom = wkb.loads(bytes(geoms[i]))
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = shapely_transform(to_wgs84, geom)
        districts[num] = geom
        features.append({
            "type": "Feature",
            "properties": {"district": num, "name": label,
                           "population": int(cols["POP20"][i]), "sort": "%02d" % num},
            "geometry": round_geom(geom),
        })

    if pop_total != POP_2020_COUNTY:
        sys.exit("district populations sum to %d, but Menard's 2020 census count "
                 "is %d — the export's vintage or extent changed. Re-verify "
                 "against the county before shipping.\n  %s"
                 % (pop_total, POP_2020_COUNTY, SOURCE_NOTE))

    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)

    union = unary_union(list(districts.values()))
    drift = max(abs(u - o) for u, o in zip(union.bounds, outline.bounds))
    if drift > EXTENT_TOLERANCE_DEG:
        sys.exit("reprojected districts span %s but the county outline spans %s "
                 "(worst edge off by %.4f deg) — check SOURCE_EPSG against the "
                 "archive's .prj" % (union.bounds, outline.bounds, drift))

    coverage = union.intersection(outline).area / outline.area * 100.0
    parts = list(union.geoms) if union.geom_type == "MultiPolygon" else [union]
    hole_area = sum(Polygon(r).area for p in parts for r in p.interiors)
    holes = 100.0 * hole_area / union.area
    hole_count = sum(len(p.interiors) for p in parts)
    keys = list(districts)
    worst, worst_pair = 0.0, None
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            area = districts[keys[i]].intersection(districts[keys[j]]).area
            if area > worst:
                worst, worst_pair = area, (keys[i], keys[j])
    worst_pct = worst / outline.area * 100.0

    if coverage < MIN_COVERAGE:
        sys.exit("the districts tile only %.3f%% of Menard County (need >= %.2f%%)"
                 % (coverage, MIN_COVERAGE))
    if holes > MAX_INTERNAL_HOLES_PCT:
        sys.exit("the districts leave %.4f%% of the county in cracks between "
                 "neighbours (max %.2f%%). This export arrived with none at all, "
                 "so a new one having any is a real change." % (holes, MAX_INTERNAL_HOLES_PCT))
    if worst_pct > MAX_PAIR_OVERLAP:
        sys.exit("Districts %s and %s overlap by %.4f%% of the county (max %.2f%%)"
                 % (worst_pair[0], worst_pair[1], worst_pct, MAX_PAIR_OVERLAP))

    payload = json.dumps({"type": "FeatureCollection",
                          "features": sorted(features, key=lambda f: f["properties"].pop("sort"))},
                         sort_keys=True, separators=(",", ":")) + "\n"

    print("Menard: %d commissioner districts (%s)"
          % (len(districts), ", ".join(f["properties"]["name"] for f in features)))
    print("  POP20 sums to %d = the county's 2020 census count" % pop_total)
    print("  tile %.3f%% of the shipped outline | %d internal crack(s), %.5f%% | "
          "worst pair overlap %.5f%% | extent within %.5f deg"
          % (coverage, hole_count, holes, worst_pct, drift))
    print("  source: %s" % SOURCE_NOTE)

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

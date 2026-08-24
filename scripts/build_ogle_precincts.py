#!/usr/bin/env python3
"""Build Ogle County's 51 current voting precincts from the county's shapefile.

SOURCE. Ogle publishes no precinct boundaries: only a 51-page PDF map book and a
polling-location dataset that is points only. The county's GIS Coordinator, Kris
Gilbert, sent this shapefile by e-mail on 2026-08-03. It is archived at
data/source/raw/ and built from there, so refreshing it means asking again.

WHAT THIS CLOSES, AND WHY IT TOOK TWO ANSWERS. The recorded gap asked for two
specific things, and the county supplied both on the same day:

  1. "Ogle's CURRENT precinct boundaries as map data" — this shapefile.
  2. "a county statement of how Forreston 3 was absorbed" — County Clerk Becky
     Duke, by e-mail: "Forreston 1 and 2 became Forreston 1. Forreston 3
     became 2."

The second mattered as much as the first. The app already had 2020 Census
versions of these precincts — the county's board districts are dissolved from
them — but that was the 52-precinct fabric of 2020 and the county now runs 51.
Shipping the old set would have put Forreston 3 on a card when it no longer
exists. FORRESTON_RETIREMENT below asserts the clerk's statement against the
data: exactly two Forreston precincts, numbered 1 and 2. If a future export
disagrees, the build stops rather than quietly contradicting her.

PROJECTION. The shapefile is NAD83 / StatePlane Illinois West FIPS 1202 in US
survey feet (EPSG:3436), which is what its .prj declares. Reprojected here with
pyproj rather than shipped as-is — the same step McDonough needed, for the same
reason: the app does point-in-polygon in degrees.

Usage:
    python3 scripts/build_ogle_precincts.py            # write data/app/
    python3 scripts/build_ogle_precincts.py --check    # drift gate, writes nothing
"""

import argparse
import io
import json
import os
import re
import sys
import zipfile

try:
    import shapefile                      # pyshp
    from pyproj import Transformer
    from shapely.geometry import Polygon, shape, mapping
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover
    sys.exit("pyshp, pyproj and shapely are required: "
             "pip install -c scripts/requirements.txt pyshp pyproj shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ZIP = os.path.join(REPO_ROOT, "il", "data", "source", "raw",
                          "Ogle County Voting Precincts 2026-08-03.zip")
OUTLINE = os.path.join(REPO_ROOT, "il", "data", "app", "ogle-county-outline.json")
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app", "ogle-precincts.json")
SHAPE_STEM = "Voting_Precincts_OgleCoIL"

SOURCE_NOTE = ("Ogle County GIS (Kris Gilbert, GIS Coordinator), voting-precinct "
               "shapefile supplied by e-mail 2026-08-03")

# NAD83 / Illinois West (ftUS) -> WGS84, per the shapefile's own .prj
SOURCE_EPSG = "EPSG:3436"
COORD_PRECISION = 6

EXPECTED_PRECINCTS = 51        # exact: the county runs 51 after retiring Forreston 3
MIN_COVERAGE = 99.5            # precincts tile a county
MAX_PAIR_OVERLAP = 0.05        # percent of county area

# The clerk's statement, asserted against the data rather than trusted.
FORRESTON_RETIREMENT = {"Forreston 1", "Forreston 2"}


def read_shapefile(path):
    with zipfile.ZipFile(path) as archive:
        names = {os.path.splitext(os.path.basename(n))[1].lower(): n
                 for n in archive.namelist()
                 if os.path.basename(n).startswith(SHAPE_STEM)}
        missing = [ext for ext in (".shp", ".dbf", ".shx") if ext not in names]
        if missing:
            raise SystemExit("archive lacks %s for %s" % (missing, SHAPE_STEM))
        parts = {ext: io.BytesIO(archive.read(names[ext])) for ext in names}
        reader = shapefile.Reader(shp=parts[".shp"], dbf=parts[".dbf"],
                                  shx=parts[".shx"], encoding="utf-8")
        fields = [f[0] for f in reader.fields[1:]]
        return [(dict(zip(fields, rec)), shp)
                for rec, shp in zip(reader.records(), reader.shapes())]


def to_wgs84(shp, transform):
    """A pyshp polygon's parts, reprojected, with holes nested by containment.

    Shapefile rings are ordered — outer clockwise, holes counter-clockwise — but
    relying on winding is what collapsed Emmet in the McDonough build. Grouping
    by CONTAINMENT is the rule this project settled on, so it is what runs here.
    """
    rings = []
    starts = list(shp.parts) + [len(shp.points)]
    for i in range(len(shp.parts)):
        pts = shp.points[starts[i]:starts[i + 1]]
        lon, lat = transform.transform([p[0] for p in pts], [p[1] for p in pts])
        ring = list(zip(lon, lat))
        if len(ring) >= 4:
            rings.append(ring)
    if not rings:
        return None

    polys = [Polygon(r) for r in rings]
    polys = [p if p.is_valid else p.buffer(0) for p in polys]
    outers, holes = [], []
    for i, poly in enumerate(polys):
        if any(j != i and polys[j].contains(poly.representative_point())
               for j in range(len(polys))):
            holes.append(poly)
        else:
            outers.append(poly)
    built = []
    for outer in outers:
        mine = [h.exterior.coords for h in holes
                if outer.contains(h.representative_point())]
        geom = Polygon(outer.exterior.coords, mine)
        built.append(geom if geom.is_valid else geom.buffer(0))
    return unary_union(built)


def round_geom(geom):
    def fix(coords):
        if isinstance(coords[0], (float, int)):
            return [round(coords[0], COORD_PRECISION), round(coords[1], COORD_PRECISION)]
        return [fix(c) for c in coords]
    geo = mapping(geom)
    return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    if not os.path.exists(SOURCE_ZIP):
        sys.exit("missing archived source: %s" % SOURCE_ZIP)

    transform = Transformer.from_crs(SOURCE_EPSG, "EPSG:4326", always_xy=True)
    rows = read_shapefile(SOURCE_ZIP)
    if len(rows) != EXPECTED_PRECINCTS:
        sys.exit("expected exactly %d precincts, the export has %d — the county's "
                 "fabric changed and the gap record, the clerk's Forreston "
                 "statement and this floor all need re-checking first"
                 % (EXPECTED_PRECINCTS, len(rows)))

    geoms, features = {}, []
    for attrs, shp in rows:
        name = (attrs.get("precinct") or "").strip()
        township = (attrs.get("TWP_NAME") or "").strip()
        if not name:
            sys.exit("a precinct has no name: %r" % attrs)
        if name in geoms:
            sys.exit("duplicate precinct name %r" % name)
        geom = to_wgs84(shp, transform)
        if geom is None or geom.is_empty:
            sys.exit("%s has no usable geometry" % name)
        geoms[name] = geom
        props = {"name": name}
        if township:
            props["township"] = township
        features.append({"type": "Feature", "properties": props,
                         "geometry": round_geom(geom)})

    forreston = {n for n in geoms if n.lower().startswith("forreston")}
    if forreston != FORRESTON_RETIREMENT:
        sys.exit("the county's Forreston precincts are %s, but the County Clerk "
                 "stated on 2026-08-03 that Forreston 1 and 2 became Forreston 1 "
                 "and Forreston 3 became 2, i.e. exactly %s. Data and statement "
                 "disagree — stop and re-ask."
                 % (sorted(forreston), sorted(FORRESTON_RETIREMENT)))

    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)

    union = unary_union(list(geoms.values()))
    coverage = union.intersection(outline).area / outline.area * 100.0
    names = list(geoms)
    worst, worst_pair = 0.0, None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            area = geoms[names[i]].intersection(geoms[names[j]]).area
            if area > worst:
                worst, worst_pair = area, (names[i], names[j])
    worst_pct = worst / outline.area * 100.0

    if coverage < MIN_COVERAGE:
        sys.exit("the precincts tile only %.2f%% of Ogle County (need >= %.2f%%)"
                 % (coverage, MIN_COVERAGE))
    if worst_pct > MAX_PAIR_OVERLAP:
        sys.exit("%s and %s overlap by %.4f%% of the county (max %.2f%%)"
                 % (worst_pair[0], worst_pair[1], worst_pct, MAX_PAIR_OVERLAP))

    features.sort(key=lambda f: f["properties"]["name"])
    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         indent=1, sort_keys=True) + "\n"

    print("%d precincts across %d townships | tiles %.2f%% of the county | "
          "worst pair overlap %.4f%%"
          % (len(features), len({f["properties"].get("township") for f in features}),
             coverage, worst_pct))
    print("Forreston is %s — matches the Clerk's 2026-08-03 statement"
          % ", ".join(sorted(forreston)))

    existing = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as handle:
            existing = handle.read()
    if args.check:
        if existing != payload:
            sys.exit("drift: %s differs from what the archived shapefile builds"
                     % OUT_PATH)
        print("--check: %s matches" % OUT_PATH)
        return
    if existing == payload:
        print("no change")
        return
    with open(OUT_PATH, "w") as handle:
        handle.write(payload)
    print("wrote %s" % OUT_PATH)


if __name__ == "__main__":
    main()

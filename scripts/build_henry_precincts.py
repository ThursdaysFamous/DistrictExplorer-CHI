#!/usr/bin/env python3
"""Build Henry County's 52 voting precincts from the county's own shapefile.

SOURCE, AND WHY IT IS AN E-MAIL RATHER THAN A URL. Henry County publishes no
precinct boundaries: its elections page carries around twenty-one per-township
picture maps from November 2021, the state holds the same pictures, and the
county's mapping system carries parcels and townships only. Re-probed
2026-08-06 for a public ArcGIS under every henrycty.com hostname pattern —
nothing. The gap record's sentence, "no usable boundaries are published
anywhere", is still literally true.

The boundaries exist anyway, because somebody asked. The request went to Clerk
& Recorder Barbara Link on 2026-08-01 and GUESSED, in writing, that the file
might live with Sidwell; it does not. She forwarded it inside the county and
Bruce Lang of HENRY COUNTY GIS replied on 2026-08-06 with the archive this
script reads. Refreshing it means asking again — which is the Ogle shape, and
the reason both counties' builders read from data/source/raw/ rather than from
the web.

WHAT THE ARCHIVE HOLDS. Five shapefiles: Precincts, Wards, and the 2022
Congressional / House / Senate districts. Only Precincts is built here. The
legislative three are already shipped statewide from TIGERweb and a county-local
copy would be a second answer to a question that already has one. Wards
(Galva 3, Colona 4, Geneseo 4) is real and verified but has NO gap record asking
for it, so it is recorded in the guidebook as available rather than shipped
blind — see "The ask ledger".

NAMES, NOT CODES. The precinct attribute carries a four-digit code ("0801") and
Descr carries what a resident would recognise ("Geneseo 1"). The card gets the
name and keeps the code alongside it; DeKalb's cards are the standing example of
what shipping a bare code reads like (see dekalb-precinct-names).

PROJECTION. NAD83 / StatePlane Illinois West FIPS 1202 in US survey feet
(EPSG:3436), which is what the .prj declares. Reprojected here with pyproj
rather than shipped as-is — the app does point-in-polygon in degrees. The
reprojection is checked rather than trusted: the rebuilt extent must match the
county outline the app already ships, which an EPSG mistake could not do.

Usage:
    python3 scripts/build_henry_precincts.py            # write data/app/
    python3 scripts/build_henry_precincts.py --check    # drift gate, writes nothing
"""

import argparse
import io
import json
import os
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
                          "HenryCountyIL_VR_2026-08-13.zip")
OUTLINE = os.path.join(REPO_ROOT, "il", "data", "app", "henry-county-outline.json")
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app", "henry-precincts.json")
SHAPE_STEM = "Precincts"

SOURCE_NOTE = ("Henry County GIS (Bruce Lang), voting-precinct shapefile "
               "supplied by e-mail 2026-08-06")

# NAD83 / Illinois West (ftUS) -> WGS84, per the shapefile's own .prj
SOURCE_EPSG = "EPSG:3436"
COORD_PRECISION = 6

EXPECTED_PRECINCTS = 52        # exact: the county's own export, 2026-08-06
MIN_COVERAGE = 99.5            # precincts tile a county
MAX_PAIR_OVERLAP = 0.05        # percent of county area

# The reprojection's own check. These are the county outline's bounds as the app
# already ships them; a wrong source EPSG lands the precincts hundreds of miles
# away and this catches it before any of the slower geometry work runs.
EXTENT_TOLERANCE_DEG = 0.01


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


# A ring this small is not a feature. Geneseo 6 carries a 4-point sliver of
# ~1e-9 deg^2 — about a hundredth of a square metre — which is digitising noise,
# and it is what broke the plain containment rule (see to_wgs84). Dropped, and
# always reported rather than silently swallowed.
MIN_RING_AREA_DEG2 = 1e-8


def to_wgs84(shp, transform, name, notes):
    """A pyshp polygon's parts, reprojected, with holes nested by containment.

    Shapefile rings are ordered — outer clockwise, holes counter-clockwise — but
    relying on winding is what collapsed Emmet in the McDonough build. Grouping
    by CONTAINMENT is the rule this project settled on.

    CONTAINMENT ALONE IS NOT ENOUGH, which Henry proved and Ogle never did. The
    older form of this function asked "is this ring inside any other ring?" and
    called it a hole. Geneseo 6 answers YES BOTH WAYS: it is an outer ring with
    a hole in it, and the outer ring's own representative point falls inside
    that hole — so the hole "contains" the outer just as the outer contains the
    hole, both were classified as holes, no outer survived, and the precinct
    built as empty geometry. The fix is to compare AREA as well: a ring is a
    hole only when a STRICTLY LARGER ring contains it, which cannot be mutual.
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
    kept = []
    for poly in polys:
        if poly.area <= MIN_RING_AREA_DEG2:
            notes.append("%s: dropped a %.2e deg^2 ring as digitising noise"
                         % (name, poly.area))
            continue
        kept.append(poly)
    if not kept:
        return None

    outers, holes = [], []
    for i, poly in enumerate(kept):
        if any(j != i and kept[j].area > poly.area
               and kept[j].contains(poly.representative_point())
               for j in range(len(kept))):
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
                 "fabric changed, so the gap record and this floor both need "
                 "re-checking against the county before shipping"
                 % (EXPECTED_PRECINCTS, len(rows)))

    geoms, codes, features, notes = {}, {}, [], []
    for attrs, shp in rows:
        name = (attrs.get("Descr") or "").strip()
        code = (attrs.get("Precinct") or "").strip()
        if not name:
            sys.exit("a precinct has no Descr to name it: %r" % attrs)
        if name in geoms:
            sys.exit("duplicate precinct name %r" % name)
        if code and code in codes:
            sys.exit("precincts %r and %r share code %r" % (codes[code], name, code))
        geom = to_wgs84(shp, transform, name, notes)
        if geom is None or geom.is_empty:
            sys.exit("%s has no usable geometry" % name)
        geoms[name] = geom
        if code:
            codes[code] = name
        props = {"name": name}
        if code:
            props["code"] = code
        features.append({"type": "Feature", "properties": props,
                         "geometry": round_geom(geom)})

    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)

    union = unary_union(list(geoms.values()))
    # The reprojection check, before the expensive pair scan: a wrong EPSG puts
    # the precincts nowhere near the county the app already draws.
    ub, ob = union.bounds, outline.bounds
    drift = max(abs(u - o) for u, o in zip(ub, ob))
    if drift > EXTENT_TOLERANCE_DEG:
        sys.exit("reprojected precincts span %s but the county outline spans %s "
                 "(worst edge off by %.4f deg) — check SOURCE_EPSG against the "
                 "archive's .prj" % (ub, ob, drift))

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
        sys.exit("the precincts tile only %.2f%% of Henry County (need >= %.2f%%)"
                 % (coverage, MIN_COVERAGE))
    if worst_pct > MAX_PAIR_OVERLAP:
        sys.exit("%s and %s overlap by %.4f%% of the county (max %.2f%%)"
                 % (worst_pair[0], worst_pair[1], worst_pct, MAX_PAIR_OVERLAP))

    features.sort(key=lambda f: f["properties"]["name"])
    # COMPACT, following mcdonough-precincts.json rather than ogle's indent=1.
    # Both formats ship in data/app/ today, and the difference is not cosmetic
    # at this size: indent=1 puts every coordinate on its own line, which cost
    # 536 KB for the same 9,970 vertices McDonough carries in 232 KB. This file
    # is fetched by a browser, not read by a human — git diffs it as one line
    # either way, because a boundary change rewrites the whole geometry.
    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         sort_keys=True, separators=(",", ":")) + "\n"

    print("%d precincts | %d carry a county code | tiles %.2f%% of the county | "
          "worst pair overlap %.4f%% | extent within %.5f deg of the outline"
          % (len(features), len(codes), coverage, worst_pct, drift))
    for note in notes:
        print("  note: %s" % note)
    print("source: %s" % SOURCE_NOTE)

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
    with open(OUT_PATH, "w") as handle:
        handle.write(payload)
    print("wrote %s (%d bytes)" % (OUT_PATH, len(payload)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Jefferson County's 33 voting precincts from the county's own shapefile.

SOURCE. Jefferson publishes no boundaries: the pass-10 sweep found its site up
and its board page listing sixteen member e-mail addresses, but no board
district or precinct geometry anywhere — nothing in the state map catalogue and
no mapping service at any of the usual addresses. That gap record's closing
line was "what has NOT been done is the step that worked repeatedly this week,
which is writing to the clerk and asking." Asked 2026-08-05; County Clerk
Davis replied on 2026-08-06 with "Please see attached" and this shapefile,
archived under data/source/raw/. Refreshing it means asking again.

PROJECTION. NAD83 / StatePlane Illinois EAST FIPS 1201 in US survey feet
(EPSG:3435) — note EAST, where Henry's file is WEST; the .prj is the authority
and is read, never assumed. Verified rather than trusted: the rebuilt extent
must land within a hair of the county outline the app already ships, which a
wrong EPSG could not do.

=============================================================================
THE COUNTY'S POLYGONS ARE NOT EDGE-MATCHED, AND THIS SCRIPT REPAIRS THAT.
=============================================================================

Measured before anything was written, because it is the whole reason this
builder is longer than Henry's:

  * The 33 precincts cover 99.212% of the county, NOT ~100%.
  * The missing 0.788% is not a hole and not a missing precinct. It is a
    single CONNECTED LATTICE of hairline gaps running along nearly every
    shared boundary — it touches all 33 precincts at once — because each
    polygon was digitised independently and neighbours never had their edges
    snapped together.
  * Every uncovered sample point lies within 31 m of a precinct edge.
  * Left alone that is roughly one click in 127 inside Jefferson answering
    "this point isn't inside any district", which is a lie: the point IS in a
    precinct, the county's file merely has a crack there.

THE REPAIR, AND WHY THIS ONE. Every point in a gap is given to the precinct
whose BOUNDARY IS NEAREST TO IT. That is the only defensible reading of what
the county meant in a crack it never intended to draw, and it is computed, not
eyeballed: each precinct's boundary is densified to ~30 m, a Voronoi diagram
over those points partitions the plane by nearest boundary, and each cell's
share of the gap is merged into its owner.

A SIMPLER RULE WAS TRIED FIRST AND IS WRONG — recorded so nobody re-tries it.
"Give each gap piece to the neighbour it shares the most edge with" sounds
right and fails badly here: the lattice is ONE connected piece spanning the
county, so the whole thing lands on a single precinct and moves a boundary
35 KILOMETRES. The connectedness of the defect is exactly what defeats the
obvious fix.

WHAT THE REPAIR COSTS, stated because a card should never imply more precision
than it has: median boundary movement 34.7 m, 90th percentile 43.6 m, worst
case 118 m (Dodds 2). That is the same order as Stephenson's traced ±20 m
boundaries, which ship with their caveat stated, and it is asserted below so a
future export that needs a bigger correction fails instead of quietly getting
one.

WHAT IS NOT REPAIRED. The county's file also contains a small genuine OVERLAP
between Dodds 1 and Dodds 2 (0.000467% of the county, ~7,000 m²). It is left
exactly as the county drew it: a gap is a crack with no owner and can be
assigned, but an overlap is two claims on the same ground, and choosing
between them would be inventing an answer the county did not give. It is
reported to the Clerk instead.

Note that the worst pair the build REPORTS is not that one. After simplifying,
Grand Prairie / Rome 2 overlap by 0.0044% — an artefact of the tolerance, not
something the county drew, and eight times larger than the county's own Dodds
overlap. Both sit far under MAX_PAIR_OVERLAP. Where two precincts claim a
point the app answers with the first match, so the visible effect is confined
to a few metres of one shared edge.

Usage:
    python3 scripts/build_jefferson_precincts.py            # write data/app/
    python3 scripts/build_jefferson_precincts.py --check    # drift gate, writes nothing
"""

import argparse
import io
import json
import math
import os
import sys
import zipfile

try:
    import shapefile                      # pyshp
    from pyproj import Transformer
    from shapely import segmentize
    from shapely.geometry import MultiPoint, Point, Polygon, mapping, shape
    from shapely.ops import unary_union, voronoi_diagram
    from shapely.strtree import STRtree
except ImportError:  # pragma: no cover
    sys.exit("pyshp, pyproj and shapely are required: "
             "pip install -c scripts/requirements.txt pyshp pyproj shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ZIP = os.path.join(REPO_ROOT, "data", "source", "raw",
                          "Jefferson County precinct shape files 2026-08-06.zip")
OUTLINE = os.path.join(REPO_ROOT, "data", "app", "jefferson-county-outline.json")
OUT_PATH = os.path.join(REPO_ROOT, "data", "app", "jefferson-precincts.json")
# The archive ships as "precinct shape files.zip" holding precinct_shape_files.*;
# the archive is renamed on the way in so data/source/raw/ says which county.
SHAPE_STEM = "precinct_shape_files"

SOURCE_NOTE = ("Jefferson County Clerk (Davis), voting-precinct shapefile "
               "supplied by e-mail 2026-08-06")

SOURCE_EPSG = "EPSG:3435"          # Illinois EAST (ftUS) — see the .prj
COORD_PRECISION = 6

EXPECTED_PRECINCTS = 33
EXTENT_TOLERANCE_DEG = 0.01
MIN_COVERAGE_RAW = 99.0            # what the county's own file achieves (99.212)
MIN_COVERAGE_REPAIRED = 99.9       # what the repair must achieve (99.975)
# The repaired boundary is SIMPLIFIED before shipping, and the tolerance is the
# whole reason this number is 99.975 and not 100. Nearest-boundary assignment
# closes the cracks perfectly but draws the new edge down a Voronoi medial line,
# which zig-zags at the sampling step and cost 52,538 vertices — a 1.2 MB file
# for 33 precincts, against Henry's 233 KB for 52. Simplifying at 10 m collapses
# that noise back onto the straight township lines the county actually drew:
# 3,798 vertices, and a shared edge stays shared because both neighbours
# simplify the SAME linework with the same tolerance and Douglas-Peucker is
# deterministic. It reopens 0.025% of the county — one click in 4,000, against
# one in 127 before any of this — and that residue is asserted, not hoped for.
SIMPLIFY_TOLERANCE_M = 10.0
MAX_PAIR_OVERLAP = 0.05            # percent of county area
# The repair's own ceiling. Jefferson needs 118 m; a future export needing much
# more is a differently-broken file and must be looked at, not silently fixed.
MAX_REPAIR_SHIFT_M = 200.0
BOUNDARY_STEP_M = 30.0
LAT = 38.3                         # county mid-latitude, for metre conversions


def metres_per_degree():
    return 111320.0 * math.cos(math.radians(LAT))


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
    """Reprojected polygon, holes nested by containment AND area.

    A ring is a hole only when a STRICTLY LARGER ring contains it — containment
    alone answers "yes both ways" when an outer ring's representative point
    falls inside its own hole, which built an empty precinct in the Henry
    import (see build_henry_precincts.py).
    """
    starts = list(shp.parts) + [len(shp.points)]
    polys = []
    for i in range(len(shp.parts)):
        pts = shp.points[starts[i]:starts[i + 1]]
        lon, lat = transform.transform([p[0] for p in pts], [p[1] for p in pts])
        ring = list(zip(lon, lat))
        if len(ring) < 4:
            continue
        poly = Polygon(ring)
        polys.append(poly if poly.is_valid else poly.buffer(0))
    if not polys:
        return None
    outers, holes = [], []
    for i, poly in enumerate(polys):
        if any(j != i and polys[j].area > poly.area
               and polys[j].contains(poly.representative_point())
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


def close_gaps(geoms, outline):
    """Give every un-owned crack to the precinct whose boundary is nearest.

    Returns (repaired, gap_area_pct, piece_count). See the module docstring for
    why nearest-boundary and not longest-shared-edge.
    """
    covered = unary_union(list(geoms.values()))
    gap = outline.difference(covered)
    if gap.is_empty:
        return dict(geoms), 0.0, 0
    pieces = list(getattr(gap, "geoms", [gap]))
    step = BOUNDARY_STEP_M / metres_per_degree()

    points, owner = [], []
    for name, geom in geoms.items():
        for poly in getattr(geom, "geoms", [geom]):
            for ring in [poly.exterior] + list(poly.interiors):
                for coord in segmentize(ring, step).coords:
                    points.append(coord)
                    owner.append(name)
    geom_points = [Point(p) for p in points]
    tree = STRtree(geom_points)
    cells = voronoi_diagram(MultiPoint(points), envelope=outline.buffer(0.05))

    claim = {name: [] for name in geoms}
    for cell in cells.geoms:
        inside = [i for i in tree.query(cell) if cell.covers(geom_points[i])]
        if not inside:
            continue
        piece = cell.intersection(gap)
        if not piece.is_empty:
            claim[owner[inside[0]]].append(piece)
    repaired = {n: unary_union([geoms[n]] + claim[n]) for n in geoms}
    return repaired, gap.area / outline.area * 100.0, len(pieces)


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

    geoms = {}
    for attrs, shp in rows:
        name = (attrs.get("Precinct_N") or "").strip()
        if not name:
            sys.exit("a precinct has no Precinct_N to name it: %r" % attrs)
        if name in geoms:
            sys.exit("duplicate precinct name %r" % name)
        geom = to_wgs84(shp, transform)
        if geom is None or geom.is_empty:
            sys.exit("%s has no usable geometry" % name)
        geoms[name] = geom

    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)

    raw_union = unary_union(list(geoms.values()))
    ub, ob = raw_union.bounds, outline.bounds
    drift = max(abs(u - o) for u, o in zip(ub, ob))
    if drift > EXTENT_TOLERANCE_DEG:
        sys.exit("reprojected precincts span %s but the county outline spans %s "
                 "(worst edge off by %.4f deg) — check SOURCE_EPSG against the "
                 "archive's .prj" % (ub, ob, drift))
    raw_cov = raw_union.intersection(outline).area / outline.area * 100.0
    if raw_cov < MIN_COVERAGE_RAW:
        sys.exit("the county's own precincts cover only %.3f%% of Jefferson "
                 "(floor %.2f%%) — that is worse than the edge-matching defect "
                 "this builder repairs, so look at the export before shipping"
                 % (raw_cov, MIN_COVERAGE_RAW))

    repaired, gap_pct, pieces = close_gaps(geoms, outline)
    tol = SIMPLIFY_TOLERANCE_M / metres_per_degree()
    repaired = {n: g.simplify(tol, preserve_topology=True) for n, g in repaired.items()}

    shifts = sorted(((repaired[n].hausdorff_distance(geoms[n]) * metres_per_degree(), n)
                     for n in geoms), reverse=True)
    if shifts and shifts[0][0] > MAX_REPAIR_SHIFT_M:
        sys.exit("closing the gaps would move %s by %.0f m (ceiling %.0f m) — this "
                 "export is broken differently from the one this repair was "
                 "written for; look at it rather than auto-fixing"
                 % (shifts[0][1], shifts[0][0], MAX_REPAIR_SHIFT_M))

    union = unary_union(list(repaired.values()))
    coverage = union.intersection(outline).area / outline.area * 100.0
    if coverage < MIN_COVERAGE_REPAIRED:
        sys.exit("after repair the precincts still tile only %.4f%% of the county "
                 "(need >= %.2f%%)" % (coverage, MIN_COVERAGE_REPAIRED))

    names = list(repaired)
    worst, worst_pair = 0.0, None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            area = repaired[names[i]].intersection(repaired[names[j]]).area
            if area > worst:
                worst, worst_pair = area, (names[i], names[j])
    worst_pct = worst / outline.area * 100.0
    if worst_pct > MAX_PAIR_OVERLAP:
        sys.exit("%s and %s overlap by %.4f%% of the county (max %.2f%%)"
                 % (worst_pair[0], worst_pair[1], worst_pct, MAX_PAIR_OVERLAP))

    features = [{"type": "Feature", "properties": {"name": n},
                 "geometry": round_geom(repaired[n])} for n in names]
    features.sort(key=lambda f: f["properties"]["name"])
    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         sort_keys=True, separators=(",", ":")) + "\n"

    med = shifts[len(shifts) // 2][0]
    print("%d precincts | county's own file tiles %.3f%%, %d gap piece(s) = %.3f%% "
          "of the county" % (len(features), raw_cov, pieces, gap_pct))
    print("repaired to %.4f%% by nearest-boundary assignment, simplified at %.0f m "
          "| boundary shift median %.1f m, worst %.1f m (%s)"
          % (coverage, SIMPLIFY_TOLERANCE_M, med, shifts[0][0], shifts[0][1]))
    print("worst pair overlap %.6f%% (%s) — left as the county drew it"
          % (worst_pct, " / ".join(worst_pair) if worst_pair else "none"))
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

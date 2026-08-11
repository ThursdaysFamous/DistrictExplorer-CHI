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

THE GEOMETRY IS NOW CHECKED AGAINST A PUBLISHED SOURCE, added 2026-08-10.
The shapefile arrived by e-mail, so for four days the only thing corroborating
it was that it looked right. On 2026-08-10 Clerk Davis pointed at a page this
project had not found — the county's PRECINCT LEGAL DESCRIPTIONS, one paragraph
per precinct, at LEGAL_DESCRIPTIONS_URL. That page is a public document a
reader can check, and it says where each precinct is in words:

  * twenty-two precincts are "all 36 sections of land located in Township N
    South Range M East", which places them in a 4x4 congressional-township grid
    (T1S..T4S north to south, R1E..R4E west to east);
  * the rest name their side of a township — Rome 1 "the east 18 sections",
    Spring Garden 1 "the south 18 sections", Webber 1 an explicit list of 18
    whole sections plus the east half of six more, Dodds 1 "east of Casey Fork
    creek", Shiloh 3 "south of Broadway and east of 34th Street", and so on.

check_legal_descriptions() asserts the shipped geometry against all of that:
every precinct's centroid must land in the township cell its description
declares, every side-of-township claim must hold, and the three described
half-township splits must divide their township's area in the published
proportion (Rome and Spring Garden 18/18, Webber 21/15 — that last one is
58.3%, and the county's file gives 58.7%). Nothing here is cosmetic: the ONE
failure mode a count guard cannot see is a re-supplied export with the same 33
rows and shuffled Precinct_N values, which would put voters in the wrong board
district while every other assertion in this file passed.

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
than it has: median boundary movement 34.4 m, worst case 153 m (Dodds 2, whose
number is dominated by the county's own Dodds 1/2 overlap). That is the same
order as Stephenson's traced ±20 m boundaries, which ship with their caveat
stated, and it is asserted below so a future export that needs a bigger
correction fails instead of quietly getting one.

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
# The county's own published wording for the same 33 precincts (see the
# docstring). Everything below is transcribed from this page.
LEGAL_DESCRIPTIONS_URL = ("https://jeffersoncounty.illinois.gov/services/"
                          "county_clerk___recorder/elections/precincts.php")

# "all 36 sections of land located in Township N South Range M East" — the
# whole-township precincts, which are what fixes the grid the rest are checked
# against. Keys are (township south, range east).
WHOLE_TOWNSHIP = {
    "Grand Prairie": (1, 1), "Field": (1, 3), "Farrington": (1, 4),
    "Casner": (2, 1),
    "Blissville": (3, 1), "McClellan": (3, 2), "Pendleton": (3, 4),
    "Bald Hill": (4, 1), "Elk Prairie": (4, 2), "Moores Prairie": (4, 4),
}
# Every precinct's township, whole or shared, from the same page.
TOWNSHIP_OF = dict(WHOLE_TOWNSHIP)
TOWNSHIP_OF.update({
    "Rome 1": (1, 2), "Rome 2": (1, 2),
    "Shiloh 1": (2, 2), "Shiloh 2": (2, 2), "Shiloh 3": (2, 2),
    "Shiloh 4": (2, 2), "Shiloh 5": (2, 2),
    "Webber 1": (2, 4), "Webber 2": (2, 4),
    "Dodds 1": (3, 3), "Dodds 2": (3, 3),
    "Spring Garden 1": (4, 3), "Spring Garden 2": (4, 3),
})
for _n in ("Mt V 1", "Mt V 2", "Mt V 3", "Mt V 4", "Mt V 5",
           "Mt V 6", "Mt V 7", "Mt V 8", "Mt V 9", "Mt V 10"):
    TOWNSHIP_OF[_n] = (2, 3)   # all ten are "(Mount Vernon Township)", T2S R3E

# A precinct is allowed to sit this far outside its township's band before the
# placement counts as wrong. Township lines are read off the whole-township
# precincts themselves, so this only absorbs their own digitising noise.
TOWNSHIP_BAND_SLACK_DEG = 0.004

# Descriptions that also fix which SIDE of its township a precinct is on. Every
# pair here is two descriptions naming the SAME line — a street, a railroad, a
# creek, a section line — with one precinct on each side of it, so the ordering
# follows from the county's words and nothing is inferred from the map.
# (precinct, other precinct, axis, which side of `other` it must be, wording)
ORIENTED = (
    ("Rome 1", "Rome 2", "x", "east", "the east 18 sections"),
    ("Spring Garden 1", "Spring Garden 2", "y", "south", "the south 18 sections"),
    ("Webber 1", "Webber 2", "x", "east", "sections 1, 2, 3, 10, … plus the east 1/2 of 4, 9, 16, 21, 28, 33"),
    ("Dodds 1", "Dodds 2", "x", "east", "east of Casey Fork creek"),
    # Shiloh Township: the CSX railroad, 42nd Street, 34th Street, Sandburg Lane.
    ("Shiloh 2", "Shiloh 4", "y", "north", "north of the CSX railroad"),
    ("Shiloh 2", "Shiloh 5", "y", "north", "north of the CSX railroad"),
    ("Shiloh 1", "Shiloh 5", "x", "west", "south along North Sandburg Lane"),
    ("Shiloh 4", "Shiloh 5", "x", "east", "east of 42nd Street"),
    ("Shiloh 3", "Shiloh 4", "x", "east", "east of 34th Street"),
    ("Shiloh 3", "Shiloh 5", "x", "east", "south of Broadway and east of 34th Street"),
    # Mount Vernon Township: Route 37 (10th St), the Union Pacific, Gaskin Ave,
    # Richview Rd, Logan St, 20th St, 7th St, and the section 28/33 west line.
    ("Mt V 7", "Mt V 8", "y", "north", "north of Richview Road/Oakland Avenue"),
    ("Mt V 7", "Mt V 5", "x", "west", "west of Illinois Route 37 (AKA Salem Road)"),
    ("Mt V 8", "Mt V 5", "x", "west", "west of Illinois Route 37 (AKA Salem Road)"),
    ("Mt V 7", "Mt V 3", "x", "west", "west of Illinois Route 37 (AKA Salem Road)"),
    ("Mt V 8", "Mt V 3", "x", "west", "west of Illinois Route 37 (AKA Salem Road)"),
    ("Mt V 5", "Mt V 3", "y", "north", "north of Gaskin Avenue"),
    ("Mt V 2", "Mt V 5", "x", "east", "east along Broadway … then south along the centerline of the Union Pacific"),
    ("Mt V 2", "Mt V 1", "y", "north", "north along the Mount Vernon Township line to the northeast corner"),
    ("Mt V 1", "Mt V 4", "x", "east", "north along the west section line for section 33 … to East Broadway"),
    ("Mt V 4", "Mt V 9", "x", "east", "starting at the intersection of Broadway and 7th Street, then east"),
    ("Mt V 4", "Mt V 6", "x", "east", "then north along South 10th Street to the intersection with Newby Avenue"),
    ("Mt V 9", "Mt V 10", "y", "north", "then west along Logan Street to the township line"),
    ("Mt V 6", "Mt V 10", "x", "east", "west along the township line to the intersection with 20th Street"),
    ("Mt V 3", "Mt V 4", "y", "north", "at the intersection of Tenth Street and Broadway, then east along Broadway"),
    ("Mt V 3", "Mt V 9", "y", "north", "at the intersection of Tenth Street and Broadway, then east along Broadway"),
    ("Mt V 8", "Mt V 9", "y", "north", "North of Illinois Route 15 (AKA Broadway)"),
    ("Mt V 9", "Mt V 6", "y", "north", "then west along Logan Street to the township line"),
    ("Mt V 6", "Mt V 3", "x", "west", "then South along South 10th Street (aka Illinois Route 37)"),
)
# Splits whose description states how many of the township's 36 sections each
# side gets, so the areas are checkable and not merely the ordering.
SECTION_SHARES = (
    ("Rome 1", "Rome 2", 18, 36),
    ("Spring Garden 1", "Spring Garden 2", 18, 36),
    ("Webber 1", "Webber 2", 21, 36),      # 18 whole + the east half of 6
)
# Sections in a PLSS township are not equal — correction lines make the tiers
# differ by a percent or two — so the share is checked to a few points, which is
# still far tighter than any mis-assignment of a section could hide in.
SECTION_SHARE_SLACK_PCT = 4.0

SOURCE_EPSG = "EPSG:3435"          # Illinois EAST (ftUS) — see the .prj
COORD_PRECISION = 6

EXPECTED_PRECINCTS = 33
EXTENT_TOLERANCE_DEG = 0.01
MIN_COVERAGE_RAW = 99.0            # what the county's own file achieves (99.212)
MIN_COVERAGE_REPAIRED = 99.9       # what the repair must achieve (99.949)
# The repaired boundary is SIMPLIFIED before shipping. Nearest-boundary
# assignment closes the cracks perfectly but draws the new edge down a Voronoi
# medial line, which zig-zags at BOUNDARY_STEP_M and cost 52,489 vertices — a
# 1.2 MB file for 33 precincts, against Henry's 233 KB for 52.
#
# THE TOLERANCE WAS 10 m UNTIL 2026-08-10, AND 10 m WAS THE WRONG SIDE OF A
# CLIFF. It was chosen on the belief that it "collapses that noise back onto the
# straight township lines the county actually drew". It collapses the COUNT, not
# the noise: a 10 m tolerance cannot remove a zig-zag whose amplitude is the
# 30 m sampling step, so all of it survived, and a reader looking at the board
# districts these precincts dissolve into reported exactly that — jagged lines
# and a 33 m spike on District 10's southern edge, on ground the county's own
# file never drew (its raw Shiloh 3 stops at latitude 38.299908; the shipped one
# reached 38.299619). Measured across the whole file at 8 m deviation from the
# chord between a vertex's neighbours:
#
#     tolerance   vertices   zig-zag vertices   tiling    median shift   worst
#         10 m       3,749             3,057   99.9753%        34.6 m   118.0 m
#         15 m         601                31   99.9504%        33.9 m   118.0 m
#         20 m         516                21   99.9237%        33.9 m   122.1 m
#
# 15 m is not a compromise, it is the correct side of the cliff: 99% less
# zig-zag, a sixth of the vertices, the same median shift and the SAME worst
# shift. Accuracy is unchanged; only the drafting noise goes.
#
# It reopens 0.051% of the county rather than 0.025%, against one click in 127
# before any of this, and that residue is asserted rather than hoped for. It is
# also no longer inherited downstream: build_jefferson_board_districts.py closes
# the reopened cracks when it dissolves these precincts into board districts.
# THAT CLAIM ABOUT SHARED EDGES IS WRONG, corrected 2026-08-10. Douglas-Peucker
# is deterministic on identical INPUT, and two neighbouring rings are not
# identical input: they share a sub-path but differ everywhere else, and which
# vertices DP keeps along the shared part depends on the whole ring. So shared
# edges DO diverge here, by up to a tolerance or two, and that — not some
# unavoidable rounding — is what the 0.025% below actually is. It is invisible in
# this layer, because a hairline between two precincts draws as nothing, and it
# was invisible in review for four days; it became glaring when these precincts
# were dissolved into board districts, where a reopened crack is an interior ring
# and an interior ring is stroked. See "WHY THE DISSOLVE IS REPAIRED" in
# build_jefferson_board_districts.py, which repairs it there rather than here:
# this file's residue is measured, asserted, byte-stable and now checked against
# the county's published legal descriptions, and re-cutting it to fix a rendering
# problem one layer downstream would trade a verified file for an unverified one.
SIMPLIFY_TOLERANCE_M = 15.0
# Simplification cannot reach an isolated spike — DP keeps whatever deviates by
# more than the tolerance — so despike() removes them afterwards. A vertex is a
# spike when it sits more than SPIKE_DEVIATION_M off the chord between its
# neighbours AND those neighbours are closer together than SPIKE_CHORD_M. The
# chord limit is what separates a spike from a real corner, which is just as far
# off its chord but has its neighbours far apart. Shipped: 50 vertices removed,
# 0.008% of the county moved, and the file's spiky-vertex count drops 31 -> 8.
SPIKE_DEVIATION_M = 12.0
SPIKE_CHORD_M = 150.0
MAX_DESPIKE_MOVED_PCT = 0.02
MAX_PAIR_OVERLAP = 0.05            # percent of county area
# The repair's own ceiling. Jefferson needs 118 m; a future export needing much
# more is a differently-broken file and must be looked at, not silently fixed.
# Dodds 2 needs 153 m, and that number is the county's own Dodds 1/2 overlap
# rather than the crack repair; despiking added 35 m to it by removing the one
# vertex that was tracking the overlap's edge.
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


def _deviation_m(prev, cur, nxt, mpd_lon):
    """Perpendicular distance of `cur` from the prev->nxt chord, in metres."""
    ax, ay = prev[0] * mpd_lon, prev[1] * 111320.0
    bx, by = nxt[0] * mpd_lon, nxt[1] * 111320.0
    px, py = cur[0] * mpd_lon, cur[1] * 111320.0
    length = math.hypot(bx - ax, by - ay)
    if length == 0:
        return math.hypot(px - ax, py - ay)
    return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / length


def _chord_m(prev, nxt, mpd_lon):
    return math.hypot((prev[0] - nxt[0]) * mpd_lon, (prev[1] - nxt[1]) * 111320.0)


def despike(geoms):
    """Drop the isolated spikes simplification cannot reach.

    Douglas-Peucker keeps any vertex that deviates from its neighbours by MORE
    than the tolerance, so raising SIMPLIFY_TOLERANCE_M to 15 m flattened the
    30 m zig-zag but left the tall thin spikes standing — including the one a
    reader reported on District 10's southern edge, a single vertex 33 m south
    of a straight township line, on ground the county's own file never drew
    (its raw Shiloh 3 stops at latitude 38.299908; this one reached 38.299619).
    Those come from the Voronoi crack repair claiming one sample point's cell
    where its neighbours' cells went to the precinct on the other side.

    A spike is a vertex far off the chord between its neighbours WHEN those
    neighbours are close together — a tall thin triangle. Both conditions
    matter: without the chord limit this would flatten real corners, which are
    exactly as far off the chord but have their neighbours far apart.
    """
    mpd_lon = metres_per_degree()

    def clean_ring(coords):
        ring, removed = list(coords[:-1]), 0
        changed = True
        while changed and len(ring) > 4:
            changed = False
            for i in range(len(ring)):
                prev, cur, nxt = ring[i - 1], ring[i], ring[(i + 1) % len(ring)]
                if (_deviation_m(prev, cur, nxt, mpd_lon) > SPIKE_DEVIATION_M
                        and _chord_m(prev, nxt, mpd_lon) < SPIKE_CHORD_M):
                    del ring[i]
                    removed += 1
                    changed = True
                    break
        return ring + [ring[0]], removed

    out, dropped = {}, 0
    for name, geom in geoms.items():
        polys = []
        for poly in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
            exterior, count = clean_ring(list(poly.exterior.coords))
            dropped += count
            interiors = []
            for ring in poly.interiors:
                cleaned, count = clean_ring(list(ring.coords))
                dropped += count
                if len(cleaned) >= 4:
                    interiors.append(cleaned)
            fixed = Polygon(exterior, interiors)
            polys.append(fixed if fixed.is_valid else fixed.buffer(0))
        out[name] = unary_union(polys)
    moved = sum(out[n].symmetric_difference(geoms[n]).area for n in geoms)
    return out, dropped, moved


def check_legal_descriptions(geoms, outline):
    """Assert the shipped precincts against the county's published descriptions.

    Run on what SHIPS, not on the raw export, so it covers both questions at
    once: that the county's file agrees with the county's page, and that the
    gap repair did not move a precinct out of the township it belongs to.

    The township grid is quartered off the COUNTY OUTLINE, not read off the
    whole-township precincts. That distinction is the difference between a real
    check and a tautology: derived from the precincts, a swap between two of the
    ten whole-township precincts merely redefines the grid and passes, which is
    exactly what the first draft of this function did.
    """
    missing = sorted(set(TOWNSHIP_OF) - set(geoms))
    unknown = sorted(set(geoms) - set(TOWNSHIP_OF))
    if missing or unknown:
        sys.exit("the export's precinct names no longer match the county's "
                 "published legal descriptions — described but absent: %s; "
                 "present but undescribed: %s (%s)"
                 % (missing, unknown, LEGAL_DESCRIPTIONS_URL))

    # Jefferson is a 4x4 block of congressional townships and nothing else, so
    # quartering its bounding box IS the T1S..T4S / R1E..R4E grid.
    minx, miny, maxx, maxy = outline.bounds
    lat_step, lon_step = (maxy - miny) / 4.0, (maxx - minx) / 4.0
    bands = {
        "row": {t: (maxy - t * lat_step, maxy - (t - 1) * lat_step) for t in (1, 2, 3, 4)},
        "col": {r: (minx + (r - 1) * lon_step, minx + r * lon_step) for r in (1, 2, 3, 4)},
    }

    wrong = []
    for name, (township, rng) in sorted(TOWNSHIP_OF.items()):
        centre = geoms[name].centroid
        lo, hi = bands["row"][township]
        in_row = lo - TOWNSHIP_BAND_SLACK_DEG <= centre.y <= hi + TOWNSHIP_BAND_SLACK_DEG
        lo, hi = bands["col"][rng]
        in_col = lo - TOWNSHIP_BAND_SLACK_DEG <= centre.x <= hi + TOWNSHIP_BAND_SLACK_DEG
        if not (in_row and in_col):
            wrong.append("%s is at %.4f,%.4f but its description puts it in "
                         "T%dS R%dE" % (name, centre.y, centre.x, township, rng))
    for name, other, axis, side, wording in ORIENTED:
        a, b = geoms[name].centroid, geoms[other].centroid
        got = ((a.x - b.x) if axis == "x" else (a.y - b.y))
        want_positive = side in ("east", "north")
        if (got > 0) != want_positive:
            wrong.append("%s is described as \"%s\" but sits %s of %s"
                         % (name, wording,
                            {"east": "west", "west": "east",
                             "north": "south", "south": "north"}[side], other))
    for name, other, sections, total in SECTION_SHARES:
        pair = geoms[name].area + geoms[other].area
        got = geoms[name].area / pair * 100.0
        want = sections / float(total) * 100.0
        if abs(got - want) > SECTION_SHARE_SLACK_PCT:
            wrong.append("%s takes %.1f%% of its township but its description "
                         "claims %d of %d sections (%.1f%%)"
                         % (name, got, sections, total, want))
    if wrong:
        sys.exit("the geometry disagrees with the county's published legal "
                 "descriptions (%s):\n  - %s"
                 % (LEGAL_DESCRIPTIONS_URL, "\n  - ".join(wrong)))
    return len(TOWNSHIP_OF), len(ORIENTED), len(SECTION_SHARES)


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
    repaired, spikes, spike_area = despike(repaired)
    spike_pct = spike_area / outline.area * 100.0
    if spike_pct > MAX_DESPIKE_MOVED_PCT:
        sys.exit("removing %d spike(s) would move %.4f%% of the county (max "
                 "%.2f%%) — at that size they are not spikes, they are the "
                 "boundary" % (spikes, spike_pct, MAX_DESPIKE_MOVED_PCT))

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

    placed, oriented, shares = check_legal_descriptions(repaired, outline)

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
    print("despiked %d vertex(es) off short chords, moving %.4f%% of the county"
          % (spikes, spike_pct))
    print("legal descriptions agree: %d precincts in their declared township, "
          "%d side-of-township claims, %d section shares" % (placed, oriented, shares))
    print("source: %s" % SOURCE_NOTE)
    print("checked against: %s" % LEGAL_DESCRIPTIONS_URL)

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

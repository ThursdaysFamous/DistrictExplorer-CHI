#!/usr/bin/env python3
"""
Build data/app/white-precincts.json + data/app/white-county-board-districts.json
— White County's 18 voting precincts and 5 County Board districts, the
composition PROVEN TWICE: once by tracing the county's own adopted map, once by
the county's own certified election canvasses.

THE SOURCE. White County publishes exactly one map file — "White County, IL
voting districts & precincts map.pdf", linked from the County Clerk's Elections
page and supplied directly by County Clerk & Recorder Kayci Heil in her e-mail
of 2026-08-17, which also stated in writing: "The County Board is elected by
district." Downloaded the same hour from the county site's CDN
(irp.cdn-website.com) and archived in data/source/raw/ under its own name;
sha256 0aff4c14c3ee8b7ce5bcc1807b36e62aa84f69c39aaf8d9491aa71dfb1ad7760 —
compare against a re-download before believing the county republished it (the
weekly roster job only watches the LINK; this fingerprint is the byte check).
The PDF is a single landscape page carrying TWO map panels over a raster base:
a county-wide panel and a Carmi inset, both drawn with REAL VECTOR district
lines (the 0.451-red 3.12 pt strokes; the precinct fills are burned into the
raster, so only the DISTRICT lines are vector). The legend names 18 precincts;
the panels label 5 districts by numeral.

WHY THE SHIPPED GEOMETRY IS CENSUS FABRIC, NOT A TRACING. TIGER's Census 2020
voting-district layer carries EXACTLY the map's 18 precincts — 18/18 by name
(one spelling wobble: the county prints HERALDS PRAIRIE 22, also the spelling
on its polling-place list; the census spells it HAROLDS PRAIRIE 22 under GEOID
1719300HP22) — and their POP100 sums to the county's exact 2020 population.
The Carmi inset then proves the county DREW its map from that fabric: every
sampled point of the inset's vector district lines lands within 35 m of the
composed districts' census edges, median ~2 m (measured at first ship; floors
below). So the map contributes the COMPOSITION — which precinct belongs to
which district — and the shipped polygons are the census VTDs themselves
(precincts) and their per-district dissolve (districts), exact and
deterministic, the Shelby shape rather than the Stephenson one.

HOW THE COMPOSITION IS READ, AND PROVEN. Three independent routes must agree
or this build refuses to write:

  1. THE MAP, machine-traced: the county panel's red line network polygonizes
     into exactly 5 faces; each face contains exactly one of the panel's own
     district numerals 1-5; the faces' union outline is fitted to the TIGER
     county boundary by trimmed-ICP affine (measured median ~16 m / RMS ~34 m);
     each transformed VTD must then sit at least MIN_VTD_SHARE inside a single
     face, and that face's numeral is the map's assignment.
  2. THE CANVASSES, transcribed as CANVASS below: the 2022 General Election
     canvass (the first election under the 2021 redistricting) tabulates each
     COUNTY BOARD MEMBER DISTRICT contest by precinct — whole precincts, all
     18, each in exactly one district's table — and the 2024 canvass repeats
     districts 3 and 4. Both are on the Clerk's own Elections page.
  3. THE INSET, independently anchored: scale from its own scale bar, north-up,
     translation solved by coarse-to-fine search against the composed district
     edges; its 7 CARMI precinct labels must land in their named VTDs and its
     4 district numerals in their assigned districts.

The map assignment (1) must equal the canvass composition (2) exactly, and the
inset (3) must agree, or the build fails. A per-member balance check closes the
loop: the canvass contests are each "Vote for one" (5 single-member districts),
and the composed populations sit within BALANCE_DEV_MAX of the one-member
ideal (measured worst 2.33% — an ordinary 2021 apportionment).

THIS IS A RARE OPERATOR STEP (pymupdf + numpy + shapely; the weekly roster
workflow imports only this module's CONSTANTS, so keep every heavy import
function-local — the De Witt seam). Re-run only if White reapportions (next
due after the 2030 census) or TIGERweb republishes the VTD fabric. The output
is deterministic — census geometry in, census geometry out — so --check is a
byte compare.

Usage:
    python3 scripts/build_white_boundaries.py
    python3 scripts/build_white_boundaries.py --check
"""

import argparse
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Migrated onto vtd_board_districts by the 2026-08-24 scripts audit (the same
# follow-up the module's preamble named for Clark); --check is a byte compare,
# so the migration is proven. County-specific machinery — the map tracing, the
# inset anchoring, the count guard's wording — stays here.
import vtd_board_districts as V  # noqa: E402  (shared machinery — do not fork)
from build_metro_outline import (  # noqa: E402  (shared machinery — do not fork)
    STATE_FIPS, TIGERWEB, point_in_rings,
)
from build_stephenson_board_districts import (  # noqa: E402  (same fit machinery)
    fit_affine_icp, need, pt_seg_factory, rings_of_path,
)
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "il", "data", "source", "raw")
MAP_PDF = os.path.join(RAW_DIR, "White County IL voting districts and precincts map.pdf")
OUT_PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "white-precincts.json")
OUT_DISTRICTS = os.path.join(REPO_ROOT, "il", "data", "app", "white-county-board-districts.json")
OUTLINE_PATH = os.path.join(REPO_ROOT, "il", "data", "app", "white-county-outline.json")

COUNTY_FIPS = "193"
COUNTY2020_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
                  "tigerWMS_Census2020/MapServer/82/query")

SOURCE_LABEL = ("Census 2020 voting districts dissolved per the composition of "
                "White County's own adopted map (\"White County, IL voting "
                "districts & precincts map.pdf\", County Clerk & Recorder Kayci "
                "Heil, 2026-08-17) and its certified 2022/2024 General Election "
                "canvasses")
MAP_URL = ("https://irp.cdn-website.com/4e51b38b/files/uploaded/"
           "White%20County%2C%20IL%20voting%20districts%20%26%20precincts%20map.pdf")
ELECTIONS_URL = "https://www.whitecounty-il.gov/elections925f89e8"

# ---------------------------------------------------------------------------
# THE COMPOSITION, from the county's own certified canvasses. 2022 General
# (11/8/2022, the first election on the 2021 map): FOR MEMBER OF THE COUNTY
# BOARD DISTRICT 1-5, each contest tabulated by whole precinct — pages 35-43 of
# the Clerk's published canvass PDF. 2024 General (11/5/2024) re-ran districts
# 3 and 4 with identical precinct tables. Every contest header reads "(Vote
# for one)": five single-member districts. Precinct names here use the MAP'S
# OWN SPELLING (legend + panel labels); CENSUS_SPELLING maps the one precinct
# the census spells differently.  The weekly roster builder
# (build_white_county_board.py) imports these constants as its drift check —
# keep this module import-light (heavy imports live inside functions).
CANVASS = {
    "1": ("CARMI 13", "ENFIELD 4", "MILL SHOALS 2"),
    "2": ("HERALDS PRAIRIE 22", "INDIAN CREEK 6", "INDIAN CREEK 8"),
    "3": ("BURNT PRAIRIE 10", "CARMI 12", "CARMI 14", "CARMI 16", "MILL SHOALS 1"),
    "4": ("CARMI 18", "CARMI 19", "CARMI 20"),
    "5": ("EMMA 30", "GREY 24", "HAWTHORNE 28", "PHILLIPS 26"),
}
SEATS_PER_DISTRICT = 1          # every canvass contest header: "(Vote for one)"
EXPECTED_PRECINCTS = 18
# map spelling -> census BASENAME, for the one name the two spell differently.
# The county's own Elections page polling list agrees with the map (Heralds);
# it also prints "Gray #24" where both the map and the census print GREY 24 —
# that normalisation lives in the polling builder, not here.
CENSUS_SPELLING = {"HERALDS PRAIRIE 22": "HAROLDS PRAIRIE 22"}

# ---------------------------------------------------------------------------
# PDF anatomy (all measured off the archived file; the guards below re-measure
# on every run so a republished map fails loudly instead of mis-tracing).
RED = (0.451, 0.0, 0.0)         # the district-line stroke colour, both panels
PANEL_SPLIT_X = 615.0           # county panel left of this, Carmi inset right
LEGEND_MAX_Y = 320.0            # the right half above this y is the legend
MIN_FACE_PT2 = 100.0            # polygonize slivers below this are stroke-join dust
NUMERAL_MIN_PT = 20.0           # district numerals are ~50 pt; label digits ~10 pt
MILE_M = 1609.344

# Accuracy floors — each is this build's own first-ship measurement with room
# for the iterative fit to wobble; a large miss means the map changed or the
# fit diverged, and the composition must be re-proven before shipping.
MAX_CONTROL_MEDIAN_M = 25.0     # measured 15.8
MAX_CONTROL_RMS_M = 50.0        # measured 33.6
MIN_VTD_SHARE = 0.98            # worst measured 0.9906 (CARMI 16)
MAX_INSET_MEDIAN_M = 10.0       # measured 2.0
MIN_INSET_WITHIN_35M = 0.99     # measured 1.000 (1104/1104 points)
BALANCE_DEV_MAX = 0.10          # worst measured 0.0233 (District 4)
# County-panel precinct labels are an independent check (text is never fitted);
# the county panel prints 14 of the 18 (the four smallest CARMI precincts are
# labelled only on the inset). A label may sit just outside a small precinct at
# county scale, but never further than this from the precinct it names.
MAX_LABEL_MISS_M = 150.0
MIN_PANEL_LABELS = 14
COORD_PRECISION = 6


fail = make_fail("white-boundaries")
title_case = V.title_case


def get_json(url, params):
    return V.get_json(url, params, fail)


def fetch_vtds(shape_fn):
    """V.fetch_vtds re-keyed onto the raw census BASENAME (White's lookups and
    sorted() feature order stay byte-for-byte), plus the White-worded count
    guard."""
    vtds = {rec["basename"]: rec
            for rec in V.fetch_vtds(COUNTY_FIPS, shape_fn, fail).values()}
    if len(vtds) != EXPECTED_PRECINCTS:
        fail("the Census voting-district layer carries %d White precincts, "
             "expected %d — the fabric changed; re-read the county's map and "
             "canvasses before rebuilding" % (len(vtds), EXPECTED_PRECINCTS))
    return vtds


def fetch_county_pop():
    data = get_json(COUNTY2020_URL, {
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
        "outFields": "POP100", "returnGeometry": "false", "f": "json"})
    rows = (data.get("features") or [])
    if not rows:
        fail("Census 2020 county layer returned nothing for White County")
    return int(rows[0]["attributes"]["POP100"])


def red_segments(page):
    """(county_panel_segs, inset_segs) — every red 'l' item, split by panel.
    The legend's own red swatch sits in the right half ABOVE the inset frame
    and is excluded by LEGEND_MAX_Y. rings_of_path is not used here: the lines
    are open polylines, not fills."""
    county, inset = [], []
    for p in page.get_drawings():
        colour = p.get("color")
        if colour is None or tuple(round(c, 3) for c in colour) != RED:
            continue
        into = county if p["rect"].x1 <= PANEL_SPLIT_X else inset
        if into is inset and p["rect"].y1 <= LEGEND_MAX_Y:
            continue                                    # the legend swatch
        for it in p["items"]:
            if it[0] == "l":
                a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
                if a != b:
                    into.append((a, b))
    if not county or not inset:
        fail("the map's red district linework is missing from a panel "
             "(county %d / inset %d segments)" % (len(county), len(inset)))
    return county, inset


def panel_words(page):
    return page.get_text("words")


def district_numerals(words, left_panel):
    """{district: (cx, cy)} for the panel's own district numerals 1-5.

    A bare digit is also how a stacked precinct label ends (MILL SHOALS / 2),
    so glyph SIZE is the separator: the district numerals are ~50 pt tall
    where every precinct-label digit is ~10 pt."""
    out = {}
    for w in words:
        if w[4] not in ("1", "2", "3", "4", "5"):
            continue
        if left_panel and w[0] >= PANEL_SPLIT_X:
            continue
        if not left_panel and w[0] < PANEL_SPLIT_X:
            continue
        if w[1] > 700 or (not left_panel and w[1] < LEGEND_MAX_Y):
            continue                                    # scale bars / legend
        if (w[3] - w[1]) < NUMERAL_MIN_PT:
            continue                                    # a precinct label's digit
        if w[4] in out:
            fail("panel prints district numeral %s twice — the labelling "
                 "changed" % w[4])
        out[w[4]] = ((w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0)
    return out


def precinct_labels(words, left_panel):
    """{map precinct name: (cx, cy)} read from a panel's own text, matched
    against the composition vocabulary so a stray word cannot become one.
    Handles both one-line labels (MILL SHOALS 2) and stacked ones (INDIAN
    CREEK / 8 on the next line)."""
    vocab = {}
    for names in CANVASS.values():
        for name in names:
            base, num = name.rsplit(" ", 1)
            vocab.setdefault(base, set()).add(num)
    toks = []
    for w in words:
        in_left = w[0] < PANEL_SPLIT_X
        if in_left != left_panel:
            continue
        if not left_panel and w[1] < LEGEND_MAX_Y:
            continue                                    # the legend column
        if left_panel and w[1] > 700:
            continue                                    # scale bar / credits
        toks.append(w)
    out = {}
    for i, w in enumerate(toks):
        for width in (1, 2):
            parts = [t[4] for t in toks[i:i + width]]
            base = " ".join(parts).upper()
            if base not in vocab or i + width >= len(toks):
                continue
            num_tok = toks[i + width]
            num = num_tok[4]
            if num.lstrip("0") not in {v.lstrip("0") for v in vocab[base]} and num not in vocab[base]:
                continue
            # the number must sit on the same line or the line just below
            if abs(num_tok[1] - w[1]) > 14:
                continue
            name = "%s %s" % (base, str(int(num)))
            if name not in {n for names in CANVASS.values() for n in names}:
                continue
            span = toks[i:i + width] + [num_tok]
            cx = sum((t[0] + t[2]) / 2.0 for t in span) / len(span)
            cy = sum((t[1] + t[3]) / 2.0 for t in span) / len(span)
            out.setdefault(name, (cx, cy))
    return out


def polygonize_county_panel(segs):
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    net = unary_union([LineString([a, b]) for a, b in segs])
    faces = [f for f in polygonize(net) if f.area >= MIN_FACE_PT2]
    if len(faces) != 5:
        fail("the county panel's district lines polygonize into %d faces, "
             "expected 5 — the map changed" % len(faces))
    return faces


def inset_scale(page):
    """Metres per PDF point, from the INSET'S OWN scale bar: its two black
    blocks run 0..0.125 mi and 0.25..0.5 mi, so the left edge of the first to
    the right edge of the second is exactly half a mile."""
    blocks = []
    for p in page.get_drawings():
        f = p.get("fill")
        if f and tuple(round(c, 3) for c in f) == (0.0, 0.0, 0.0):
            r = p["rect"]
            if r.x0 > PANEL_SPLIT_X and 735 < r.y0 < 760:
                blocks.append(r)
    if len(blocks) != 2:
        fail("expected the inset scale bar's 2 black blocks, found %d" % len(blocks))
    blocks.sort(key=lambda r: r.x0)
    span_pt = blocks[1].x1 - blocks[0].x0
    # sanity: the first block is 0.125 mi, the second 0.25 mi — 1:2 by width
    w1, w2 = blocks[0].width, blocks[1].width
    if not (1.8 < w2 / w1 < 2.2):
        fail("inset scale-bar blocks are %.1f and %.1f pt wide — not the "
             "0.125/0.25-mile pair this reading assumes" % (w1, w2))
    return (0.5 * MILE_M) / span_pt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped files, write nothing")
    args = ap.parse_args()
    pymupdf = need("pymupdf")
    np = need("numpy")
    need("shapely")
    from shapely.geometry import LineString, Point, mapping, shape  # noqa: E402
    from shapely.ops import transform as shp_transform, unary_union  # noqa: E402

    if not os.path.exists(MAP_PDF):
        fail("archived source map missing: %s" % os.path.relpath(MAP_PDF, REPO_ROOT))

    # ---- composition sanity before any network or PDF work -----------------
    all_names = [n for names in CANVASS.values() for n in names]
    if len(all_names) != len(set(all_names)):
        fail("a precinct is named in two districts")
    if len(all_names) != EXPECTED_PRECINCTS:
        fail("the canvass composition covers %d precincts, the county runs %d"
             % (len(all_names), EXPECTED_PRECINCTS))

    # ---- read the PDF ------------------------------------------------------
    page = pymupdf.open(MAP_PDF)[0]
    county_segs, inset_segs = red_segments(page)
    words = panel_words(page)
    faces = polygonize_county_panel(county_segs)

    numerals = district_numerals(words, left_panel=True)
    if sorted(numerals) != ["1", "2", "3", "4", "5"]:
        fail("county panel names districts %s, expected 1-5" % sorted(numerals))
    face_of = {}
    for dnum, (cx, cy) in sorted(numerals.items()):
        hits = [i for i, f in enumerate(faces) if f.contains(Point(cx, cy))]
        if len(hits) != 1:
            fail("district numeral %s sits in %d traced faces — refusing to "
                 "guess the labelling" % (dnum, len(hits)))
        if hits[0] in {v for v in face_of.values()}:
            fail("two district numerals share one traced face")
        face_of[dnum] = hits[0]

    # ---- fetch census fabric ----------------------------------------------
    vtds = fetch_vtds(shape)
    expected_census = {CENSUS_SPELLING.get(n, n) for n in all_names}
    if set(vtds) != expected_census:
        fail("census precinct names differ from the map's: missing %s, extra %s"
             % (sorted(expected_census - set(vtds)), sorted(set(vtds) - expected_census)))
    county_pop = fetch_county_pop()
    if sum(v["pop"] for v in vtds.values()) != county_pop:
        fail("the 18 precinct populations sum to %d but White County's Census "
             "2020 POP100 is %d" % (sum(v["pop"] for v in vtds.values()), county_pop))

    # ---- georeference the county panel against TIGER -----------------------
    union_pdf = unary_union(faces)
    if union_pdf.geom_type != "Polygon":
        fail("the five traced faces do not union to one polygon")
    P = np.array(sorted({(round(x, 6), round(y, 6))
                         for x, y in union_pdf.exterior.coords}), float)
    resp = get_json(TIGERWEB, {
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
        "outFields": "NAME", "returnGeometry": "true", "outSR": "4326",
        "f": "geojson"})
    county_geom = shape(resp["features"][0]["geometry"]).buffer(0)
    tg = mapping(county_geom)
    tparts = tg["coordinates"] if tg["type"] == "MultiPolygon" else [tg["coordinates"]]
    T = np.array([c[:2] for pp in tparts for r in pp for c in r], float)
    kx = math.cos(math.radians(float(T[:, 1].mean())))
    A, t, pt_seg, ctrl = fit_affine_icp(np, P, tparts, kx, fail)
    d, _ = pt_seg(P @ A.T + t, ctrl)
    matched = d[d < 120 / 111320] * 111320
    ctrl_median = float(np.median(matched))
    ctrl_rms = float((matched ** 2).mean() ** 0.5)
    if ctrl_median > MAX_CONTROL_MEDIAN_M or ctrl_rms > MAX_CONTROL_RMS_M:
        fail("county-outline fit degraded: median %.1f m (max %.1f), RMS %.1f m "
             "(max %.1f) — the traced outline no longer matches TIGER's White "
             "County; the georeference is wrong, so nothing ships"
             % (ctrl_median, MAX_CONTROL_MEDIAN_M, ctrl_rms, MAX_CONTROL_RMS_M))

    def tf(xs, ys, z=None):
        q = np.column_stack([np.asarray(xs, float), np.asarray(ys, float)]) @ A.T + t
        return q[:, 0] / kx, q[:, 1]
    faces_ll = {dnum: shp_transform(tf, faces[i]) for dnum, i in face_of.items()}

    # ---- route 1 vs route 2: the traced map must reproduce the canvass -----
    map_assignment, worst_share = {}, (1.0, None)
    for census_name, rec in sorted(vtds.items()):
        shares = {dn: rec["geom"].intersection(fl).area / rec["geom"].area
                  for dn, fl in faces_ll.items()}
        best = max(shares, key=shares.get)
        if shares[best] < MIN_VTD_SHARE:
            fail("precinct %s sits only %.2f%% inside traced district %s "
                 "(floor %.0f%%) — the map's lines do not follow this "
                 "precinct's census edges; the composition cannot be read "
                 "mechanically" % (census_name, 100 * shares[best], best,
                                   100 * MIN_VTD_SHARE))
        if shares[best] < worst_share[0]:
            worst_share = (shares[best], census_name)
        map_assignment[census_name] = best
    canvass_assignment = {CENSUS_SPELLING.get(n, n): dn
                          for dn, names in CANVASS.items() for n in names}
    disagreements = {n: (map_assignment[n], canvass_assignment[n])
                     for n in map_assignment
                     if map_assignment[n] != canvass_assignment[n]}
    if disagreements:
        fail("the traced map and the certified canvasses DISAGREE on %s — two "
             "county sources conflict; do not ship either reading" % disagreements)

    # ---- independent check: county-panel precinct labels (text, never fitted)
    panel_lbls = precinct_labels(words, left_panel=True)
    if len(panel_lbls) < MIN_PANEL_LABELS:
        fail("read only %d precinct labels off the county panel, expected >= %d"
             % (len(panel_lbls), MIN_PANEL_LABELS))
    for name, (cx, cy) in sorted(panel_lbls.items()):
        census_name = CENSUS_SPELLING.get(name, name)
        lx, ly = tf([cx], [cy])
        p = Point(float(lx[0]), float(ly[0]))
        containing = [n for n, rec in vtds.items() if rec["geom"].contains(p)]
        miss_m = vtds[census_name]["geom"].distance(p) * 111320
        if containing not in ([census_name], []) or miss_m > MAX_LABEL_MISS_M:
            fail("county-panel label %r lands in %s, %.0f m from the precinct "
                 "it names (max %.0f) — the georeference or the labelling is "
                 "wrong" % (name, containing or "no precinct", miss_m,
                            MAX_LABEL_MISS_M))

    # ---- compose the districts from census fabric --------------------------
    districts_ll = {}
    for dnum, names in CANVASS.items():
        geom = unary_union([vtds[CENSUS_SPELLING.get(n, n)]["geom"] for n in names])
        districts_ll[dnum] = geom if geom.is_valid else geom.buffer(0)

    # ---- route 3: the inset, anchored by its own scale bar ------------------
    m_per_pt = inset_scale(page)
    if not (5.0 < m_per_pt < 6.5):
        fail("inset scale bar reads %.2f m/pt — outside the plausible band; "
             "the bar moved or the reading broke" % m_per_pt)
    s = m_per_pt / 111320.0
    F = np.array([[1.0, 0.0], [0.0, -1.0]])
    pts = set()
    for a, b in inset_segs:
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.0))
        for i in range(n + 1):
            f = i / n
            pts.add((round(a[0] + f * (b[0] - a[0]), 3),
                     round(a[1] + f * (b[1] - a[1]), 3)))
    IP = np.array(sorted(pts), float)
    county_edge = unary_union(list(districts_ll.values())).buffer(0).exterior
    ctrl_segs = []
    for g in districts_ll.values():
        for poly in ([g] if g.geom_type == "Polygon" else list(g.geoms)):
            for ring in [poly.exterior] + list(poly.interiors):
                c = list(ring.coords)
                for i in range(len(c) - 1):
                    mid = Point((c[i][0] + c[i + 1][0]) / 2,
                                (c[i][1] + c[i + 1][1]) / 2)
                    if county_edge.distance(mid) > 1e-4:   # interior lines only
                        ctrl_segs.append(((c[i][0] * kx, c[i][1]),
                                          (c[i + 1][0] * kx, c[i + 1][1])))
    ictrl = np.array([np.stack([np.array(a), np.array(b)]) for a, b in ctrl_segs])
    IPc = IP @ F.T * s
    centre = IPc.mean(0)
    IPc = IPc - centre
    dec = IPc[::4]
    carmi_seed = np.array([vtds["CARMI 16"]["geom"].centroid.x * kx,
                           vtds["CARMI 16"]["geom"].centroid.y])
    best = (None, carmi_seed[0], carmi_seed[1])
    for step_m, span_m, tol_m in ((500, 6000, 400), (100, 900, 150), (25, 180, 60)):
        step, span = step_m / 111320.0, span_m / 111320.0
        cx0, cy0 = best[1], best[2]
        best = (None, cx0, cy0)
        rng = int(span / step)
        for ix in range(-rng, rng + 1):
            for iy in range(-rng, rng + 1):
                tt = np.array([cx0 + ix * step, cy0 + iy * step])
                dd, _ = pt_seg(dec + tt, ictrl, chunk=600)
                score = float((dd < tol_m / 111320.0).mean())
                if best[0] is None or score > best[0]:
                    best = (score, tt[0], tt[1])
    it = np.array([best[1], best[2]])
    for cut in [200 / 111320] * 6 + [80 / 111320] * 8 + [45 / 111320] * 10:
        dd, near = pt_seg(IPc + it, ictrl)
        keep = dd <= cut
        if keep.sum() < 80:
            fail("the inset fit lost its correspondences — the inset no longer "
                 "draws the composed district lines")
        it = it + (near[keep] - (IPc[keep] + it)).mean(0)
    dd, _ = pt_seg(IPc + it, ictrl)
    inset_m = dd * 111320
    inset_within = float((inset_m < 35).mean())
    inset_median = float(np.median(inset_m))
    if inset_within < MIN_INSET_WITHIN_35M or inset_median > MAX_INSET_MEDIAN_M:
        fail("inset agreement degraded: %.1f%% of its line points within 35 m "
             "(min %.0f%%), median %.1f m (max %.1f) — the county's fine-scale "
             "drawing no longer matches the composed districts"
             % (100 * inset_within, 100 * MIN_INSET_WITHIN_35M,
                inset_median, MAX_INSET_MEDIAN_M))

    def inset_ll(pt):
        q = np.array(pt, float) @ F.T * s - centre + it
        return (float(q[0] / kx), float(q[1]))

    inset_lbls = precinct_labels(words, left_panel=False)
    carmi_lbls = {n: xy for n, xy in inset_lbls.items() if n.startswith("CARMI")}
    if len(carmi_lbls) != 7:
        fail("read %d CARMI labels off the inset, expected 7" % len(carmi_lbls))
    for name, anchor in sorted(carmi_lbls.items()):
        p = Point(*inset_ll(anchor))
        containing = [n for n, rec in vtds.items() if rec["geom"].contains(p)]
        if containing != [name]:
            fail("inset label %r lands in %s — the inset disagrees with the "
                 "composition" % (name, containing or "no precinct"))
    inset_nums = district_numerals(words, left_panel=False)
    if sorted(inset_nums) != ["1", "3", "4", "5"]:
        fail("inset names districts %s, expected 1/3/4/5" % sorted(inset_nums))
    for dnum, anchor in sorted(inset_nums.items()):
        p = Point(*inset_ll(anchor))
        containing = [dn for dn, g in districts_ll.items() if g.contains(p)]
        if containing != [dnum]:
            fail("inset district numeral %s lands in district %s — the inset "
                 "disagrees with the composition" % (dnum, containing))

    # ---- balance (per member: five 'Vote for one' contests) -----------------
    pops = {dn: sum(vtds[CENSUS_SPELLING.get(n, n)]["pop"] for n in names)
            for dn, names in CANVASS.items()}
    ideal = county_pop / (len(CANVASS) * SEATS_PER_DISTRICT)
    worst_dev = max((abs(p / SEATS_PER_DISTRICT - ideal) / ideal, dn)
                    for dn, p in pops.items())
    if worst_dev[0] > BALANCE_DEV_MAX:
        fail("district %s deviates %.1f%% per member from the one-member ideal "
             "(max %.0f%%) — check the composition before trusting it"
             % (worst_dev[1], 100 * worst_dev[0], 100 * BALANCE_DEV_MAX))

    # ---- tiling and outline agreement --------------------------------------
    metres2 = (111320.0 * kx) * 111320.0
    all_geoms = [rec["geom"] for rec in vtds.values()]
    vtd_union = unary_union(all_geoms)
    overlap_m2 = (sum(g.area for g in all_geoms) - vtd_union.area) * metres2
    if overlap_m2 > 100.0:
        fail("the 18 precincts overlap each other by %.0f m2 — the census "
             "fabric no longer tiles" % overlap_m2)
    covered = vtd_union.intersection(county_geom).area / county_geom.area
    if covered < 0.995:
        fail("the 18 precincts cover only %.2f%% of TIGER's White County"
             % (100 * covered))
    with open(OUTLINE_PATH, encoding="utf-8") as handle:
        outline_gj = json.load(handle)
    outline = unary_union([shape(f["geometry"]) for f in outline_gj["features"]])
    outline_pct = vtd_union.symmetric_difference(outline).area / outline.area * 100
    if outline_pct > 0.25:
        fail("the precinct union differs from the shipped coverage outline by "
             "%.3f%% (max 0.25%%)" % outline_pct)

    # ---- emit ---------------------------------------------------------------
    def round_geom(geom):
        return V.round_geom(geom, mapping)

    precinct_features = []
    for map_name in sorted(all_names):
        census_name = CENSUS_SPELLING.get(map_name, map_name)
        rec = vtds[census_name]
        props = {"name": title_case(map_name),
                 "district": canvass_assignment[census_name],
                 "geoid": rec["geoid"],
                 "pop2020": rec["pop"]}
        if census_name != map_name:
            props["censusName"] = title_case(census_name)
        precinct_features.append({"type": "Feature", "properties": props,
                                  "geometry": round_geom(rec["geom"])})
    precincts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "mapUrl": MAP_URL,
            "electionsUrl": ELECTIONS_URL,
            "note": ("White County's 18 precincts are the Census 2020 voting "
                     "districts, which match the county's own adopted map 18/18 "
                     "by name; the Carmi inset of that map traces the census "
                     "edges to a measured ~2 m median. Names use the county's "
                     "spelling (Heralds Prairie 22, which the census spells "
                     "Harolds)."),
        },
        "features": precinct_features,
    }

    district_features = []
    for dnum in sorted(CANVASS, key=int):
        merged = districts_ll[dnum]
        district_features.append({
            "type": "Feature",
            "properties": {
                "district": dnum, "name": "District %s" % dnum,
                "precincts": [title_case(n) for n in CANVASS[dnum]],
                "pop2020": pops[dnum],
            },
            "geometry": round_geom(merged if merged.is_valid else merged.buffer(0)),
        })
    districts_payload = {
        "type": "FeatureCollection",
        "properties": {
            "source": SOURCE_LABEL, "mapUrl": MAP_URL,
            "canvass": ("Composition certified by the county's 2022 General "
                        "Election canvass (all five districts, whole precincts) "
                        "and re-confirmed for districts 3-4 by the 2024 canvass, "
                        "both on the Clerk's Elections page"),
            "note": ("Five single-member districts dissolved from Census 2020 "
                     "voting districts per the composition of the county's own "
                     "adopted map, which a machine tracing of that map and the "
                     "certified canvasses independently agree on 18/18."),
        },
        "features": district_features,
    }

    # the app's own even-odd test, per composition rep point (the Shelby guard)
    for dnum, names in CANVASS.items():
        for n in names:
            probe = vtds[CENSUS_SPELLING.get(n, n)]["geom"].representative_point()
            hits = [f["properties"]["district"] for f in district_features
                    if point_in_rings(probe.y, probe.x, V.rings_of(f["geometry"]))]
            if hits != [dnum]:
                fail("precinct %s lands in district %s after rounding, expected "
                     "%s" % (n, hits or "none", dnum))

    prec_body = V.dumps(precincts_payload)
    dist_body = V.dumps(districts_payload)

    print("white-boundaries: 18 precincts -> 5 districts; map tracing and "
          "canvasses agree 18/18 (worst VTD-in-face share %.4f, %s)"
          % (worst_share[0], worst_share[1]))
    print("  county-panel fit median %.1f m / RMS %.1f m; %d/%d panel labels "
          "verified" % (ctrl_median, ctrl_rms, len(panel_lbls), len(panel_lbls)))
    print("  inset: %.1f%% of %d line points within 35 m of composed edges, "
          "median %.1f m; 7/7 precinct labels + %d/%d numerals agree"
          % (100 * inset_within, len(IP), inset_median,
             len(inset_nums), len(inset_nums)))
    print("  populations: %s (total %d = census POP100; worst per-member "
          "deviation %.2f%% in district %s)"
          % (", ".join("D%s=%d" % (dn, pops[dn]) for dn in sorted(pops, key=int)),
             county_pop, 100 * worst_dev[0], worst_dev[1]))
    print("  tiling: overlap %.1f m2; %.3f%% of the county covered; %.4f%% vs "
          "the coverage outline" % (overlap_m2, 100 * covered, outline_pct))

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

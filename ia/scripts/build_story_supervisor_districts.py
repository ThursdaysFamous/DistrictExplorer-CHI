#!/usr/bin/env python3
"""
Build data/source/story-supervisor-districts.geojson — Story County's three
supervisor districts, read off the county Auditor's own printed district map
and resolved to whole Census 2020 blocks.

WHY THIS COUNTY NEEDED ITS OWN SCRIPT
---------------------------------------
Senate File 75 (signed 2025-04-11) forces Story, Johnson and Black Hawk from
at-large to single-member district elections for November 2026. Black Hawk
publishes its adopted plan as a hosted feature service, so
build_ia_supervisor_districts.py ships it as ordinary geometry. Story
publishes NO GIS service — re-swept 2026-09-05: the Legislature's own org
carries no Story plan layer, the county's Jurisdictional Maps page references
no ArcGIS host, and an arcgis.com catalog search returns nothing for it — so
Story shipped as ONE county-level TRANSITIONING placeholder that could not
tell a reader which district they were in. This script retires that.

THE JACKSON METHOD, AND THE ONE PLACE IT DID NOT APPLY
--------------------------------------------------------
scripts/build_jackson_boundaries.py reads a vector PDF by taking the FILLED
PATH OBJECTS whose fill colours pair with the legend — never by sampling
pixels, which is the Knox mistake (a clean, confident, wrong answer).

A previous pass in this repo recorded that Story's map carries "1,584 FILLED
curves — the Jackson precondition". THAT WAS AN OVER-CLAIM AND IS CORRECTED
HERE. 1,584 filled curves do exist and NONE OF THEM IS A DISTRICT: the
largest is 2.63% of the page and not one exceeds 5%. They are lakes, parks
and city fills. "This PDF has filled paths" and "this PDF's DISTRICTS are
filled paths" are different claims, and only the second one licenses the
Jackson method.

What draws Story's districts is STROKES — nine curves at linewidth 12, the
only curves on the page at that weight out of 10,761 (pdfplumber 0.11.10;
an earlier pass published 10,235 and that figure was wrong). The reading
rule survives intact, because the rule was never "look for fills": it is
READ THE PATH OBJECTS, NEVER THE PIXELS. These are path objects.

WHAT THE PAGE ACTUALLY CONTAINS (measured 2026-09-05)
-------------------------------------------------------
Two map panels. The LEFT is the whole county; the RIGHT is an Ames inset (its
own scale bar reads 0-1 miles and it is dense with Ames street names). The
page's own legend says what the numerals mean -- "Supervisor Districts" and
"1  Supervisor District Number" -- so the encoding is the map's statement,
not an inference. It is titled "STORY COUNTY / VOTING PRECINCTS &
SUPERVISOR DISTRICTS" and footed "Map prepared in the Story County Auditor's
Office on 3/13/2026", after the Board's 2026-01-27 adoption.

The left panel holds exactly THREE CLOSED linewidth-12 rings, and exactly one
legend-sized numeral falls inside each. That containment test is also what
settles the coordinate convention: pdfplumber's curve `path` operators are in
TOP-DOWN space, and read bottom-up the same test puts two numerals in one
ring and none in another. A test that can come out wrong is why it is a gate.

THE PROJECTION ANNOUNCED ITSELF, THE SAME WAY JACKSON'S DID
--------------------------------------------------------------
The three rings' union is 1716.2 x 1705.6 pt, aspect 1.00621. Story County's
true aspect is 1.00621 in EPSG:26975 (NAD83 / Iowa North) — agreeing to five
digits — against 1.0027 in UTM 15N, 1.0008 in Web Mercator and 1.3474 read as
plate carree. Fitting the drawn bbox to the county's bbox in each and
measuring the residual against the county's real outline ranks them the same
way: 0.6 m mean in Iowa North, 91 m in UTM, 26 m in either of the other two.

NOTHING TRACED SHIPS
----------------------
The fitted rings are used ONLY to sort Census 2020 blocks, and the shipped
polygons are unions of whole blocks — every vertex is the Census Bureau's,
none is this script's reading of a PDF. That is the Jackson posture: there,
the map only ever chose between two districts a canvass had already named.
Story has held no election on these lines, so the map is the only source for
the composition, which makes the independent check below load-bearing rather
than reassuring.

TWO CHECKS, NEITHER OF WHICH IS THE MAP CHECKING ITSELF
----------------------------------------------------------
THE POPULATIONS, AND THERE ARE TWO CANDIDATE PLANS. The Legislative Services
Agency published a First Plan (2025-12-04) at 32,783 / 32,894 / 32,860 and,
after the Board rejected it on 2026-01-06 "based on compactness of districts",
a Second Plan (2026-01-14) at 32,940 / 32,793 / 32,804. Iowa Code
331.210A(2)(d) then lets the Board approve either one or an amendment, and the
Board's 2026-01-27 approval does not say which. Sorting all 2,797 blocks by
the fitted rings and summing POP100 reproduces the FIRST plan's three numbers
EXACTLY, district by district IN ORDER, and matches none of the second's — so
the county adopted the first plan, and this build says so because it measured
it. That also confirms the numeral-to-ring labelling, since the three values
are distinct and a swap would show; a single misplaced populated block would
break it.

THE PRECINCT LISTS. The First Plan also names the precincts in each district,
and this app already ships Iowa's precinct fabric, so those lists can be
dissolved and compared to the districts the map produced — a different
document and a different geometry reaching the same answer, at worst IoU
0.99127. See check_against_lsa_precincts() for why it is an overlap test
rather than an equality.

CORRECTED 2026-09-05 — STORY'S DISTRICTS DO NOT SPLIT A PRECINCT, AND THIS
FILE SAID THEY DID. Iowa Code 49.3(2)(a) requires that "all boundaries ...
shall follow precinct boundaries", and LSA's First Plan lists Roland/Howard
Twp whole in District 2, so a split was never possible. THE PARAGRAPH IS
LETTERED, NOT NUMBERED, and it is not unconditional: it exempts "supervisor
districts for counties using supervisor representation plan 'two' pursuant to
section 331.209", which fifteen Iowa counties use. Story is not one of them --
both LSA reports are headed PLAN "THREE", 2025 Iowa Acts ch. 15 requires plan
three of a county holding a regents institution, and section 331.210 says
plan-three district boundaries "shall follow voting precinct lines" -- so the
rule binds here on two separate grounds and must not be quoted flat. What the block sort split
is the SHIPPED PRECINCT POLYGON: `ia-precincts.json` carries a 2024 vintage in
which that precinct still holds its 2020 census voting-district geometry —
measured against TIGERweb's own `HOWARD TWP W/O STORY CITY` at IoU 0.999573,
whose POP100 of 1,869 is exactly the 1,837 + 32 the sort divided. The county
re-precincted (43 census voting districts against 45 current precincts), and
only 6 of the 45 shipped Story precincts still match a voting district to
within IoU 0.999, so the stale ones are the rural remainder rather than the
fabric as a whole.

The conclusion that stood on that claim is unchanged and now rests on
something firmer: BLOCKS WERE STILL THE NECESSARY UNIT, because the precinct
layer this app ships cannot be trusted to draw the current lines — which is
what the precinct gate below measures rather than assumes.

One further measurement is recorded rather than gated: 16 of the 19 blocks the
fitted line does not cleanly nest hold ZERO people, and the three that hold
people nest at 88%, 99% and 99%.

Occasional OPERATOR step, not CI: these lines move when the county redraws
them, which SF 75 has just done and which will not happen again for years.
The PDF is pinned by SHA-256 so a re-print gets a human's attention rather
than silently re-deriving.

Usage:
    python3 ia/scripts/build_story_supervisor_districts.py
    python3 ia/scripts/build_story_supervisor_districts.py --check
"""

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import urllib.parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
OUT_DIR = os.path.join(REPO_ROOT, "data", "source")
OUT_NAME = "story-supervisor-districts.geojson"

# --- the county's own published map -----------------------------------------
PDF_URL = ("https://www.storycountyiowa.gov/DocumentCenter/View/17463/"
           "Board-of-Supervisors-District-Map")
PDF_SHA256 = "2c64a6d5f3cbc6cff1266e2dfab25a03b3294a8c1ee068ee60b0d0e2b00ebde9"
PDF_BYTES = 2815866
MAP_PREPARED = "2026-03-13"          # printed on the map itself
BOARD_ADOPTED = "2026-01-27"
SOURCE_ID = "STORY-COUNTY-AUDITOR-MAP-2026-03-13"
SOURCE_URL = "https://www.storycountyiowa.gov/1172/Jurisdictional-Maps"

# --- the census fabric the districts are resolved to ------------------------
BLOCK_URL = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
             "tigerWMS_Census2020/MapServer/10/query")
STATE_FIPS, COUNTY_FIPS = "19", "169"
EXPECTED_BLOCKS = 2797
COUNTY_POP_2020 = 98537

# --- what the map is expected to look like ----------------------------------
DISTRICT_LINEWIDTH = 12.0    # the only weight the district strokes use
PANEL_SPLIT_X = 1900         # left panel = county map; right panel = Ames inset
NUMERAL_SIZE = (45, 55)      # the legend's "Supervisor District Number" glyphs
EXPECT_DISTRICTS = ["1", "2", "3"]

# --- the georeference -------------------------------------------------------
# NAD83 / Iowa North. Named here rather than searched for: a projection this
# script picked by scoring candidates would quietly re-pick on a re-print.
PLAN_CRS = "EPSG:26975"
ASPECT_CEILING_PCT = 0.5     # measured 0.00
MEAN_OFFSET_CEILING_M = 10.0  # measured 0.6
MAX_OFFSET_CEILING_M = 25.0   # measured 2.0
MIN_BLOCK_SHARE = 0.50       # measured worst 0.6259
RING_OVERLAP_CEILING_M2 = 1.0
UNCOVERED_CEILING_PCT = 0.05  # of county area; measured 0.0057

# --- the independent witness, and there are TWO candidates ------------------
# The Legislative Services Agency published two plans for Story, and naming
# only one of them understated this gate. The Board REJECTED the first plan on
# 2026-01-06 "based on compactness of districts"; LSA published a second on
# 2026-01-14; and Iowa Code 331.210A(2)(d), quoted in that second report, lets
# the board then "approve the second plan, THE FIRST PLAN, or an amended plan".
# The board approved on 2026-01-27 without the record saying which.
#
# The geometry says which. The two plans reshuffle the county completely, and
# their population triples are disjoint: Ames 2 is in District 2 in the first
# plan and in District 3 in the second, and District 1 is a different set of
# precincts in each — thirteen in the first (the north Ames precincts plus
# Story City), nineteen in the second (the rural ring plus Story City). Story
# City itself is in District 1 in BOTH, which is why it is no use as a
# discriminator; an earlier draft of this comment said the second plan put
# Story City and Ames 2 together in District 1, and only the Story City half
# of that was true. The map's blocks reproduce the FIRST plan's three numbers
# exactly and match none of the second's, so the county adopted the first
# plan. Gating on the match alone would leave that inference invisible; gating
# on the MISMATCH too makes it a measurement.
LSA_FIRST_PLAN_DOC = "https://www.legis.iowa.gov/docs/publications/CSR/1545311.pdf"
LSA_SECOND_PLAN_DOC = "https://www.legis.iowa.gov/docs/publications/CSR/1595873.pdf"
LSA_POPULATIONS = {"1": 32783, "2": 32894, "3": 32860}    # First Plan, 2025-12-04
LSA_SECOND_POPULATIONS = {"1": 32940, "2": 32793, "3": 32804}   # rejected shape
LSA_CITE = ("Iowa Legislative Services Agency, Story County Supervisor "
            "Redistricting Report - First Plan (2025-12-04), Attachment 3: "
            "32,783 / 32,894 / 32,860")

# --- the second gate: LSA's own precinct lists ------------------------------
# The First Plan names the precincts in each district (Iowa Code 49.3(2)(a):
# "All boundaries shall follow precinct boundaries"), and this app already
# ships Iowa's precinct fabric. Dissolving those lists is therefore a check on
# the map that uses no part of the map — different document, different
# geometry, same answer.
LSA_FIRST_PLAN_PRECINCTS = {
    "1": ["Ames 10", "Ames 11", "Ames 12", "Ames 21", "Ames 22", "Ames 24",
          "Ames 7/Franklin Twp 2", "Ames 8", "Ames 9", "Franklin Twp", "Gilbert",
          "Story City 1", "Story City 2/Lafayette Twp/Howard Twp 2"],
    "2": ["Ames 2", "Ames 3/Grant Twp", "Ames 6", "Cambridge/Union Twp",
          "Collins/Collins Twp", "Colo/New Albany Twp", "Huxley 1",
          "Huxley 2/Palestine Twp", "Kelley", "Maxwell/Indian Creek Twp",
          "McCallsburg/Warren Twp", "Milford Twp", "Nevada 1/Richland Twp",
          "Nevada 2/Grant Twp 2", "Nevada 3", "Nevada 4/Nevada Twp",
          "Roland/Howard Twp", "Slater/Sheldahl", "Washington Twp",
          "Zearing/Lincoln Twp/Sherman Twp"],
    "3": ["Ames 1", "Ames 13", "Ames 14", "Ames 15", "Ames 16/Washington Twp 3",
          "Ames 17", "Ames 18", "Ames 19", "Ames 20", "Ames 23", "Ames 4",
          "Ames 5/Washington Twp 2"],
}
PRECINCTS_PATH = os.path.join(REPO_ROOT, "data", "app", "ia-precincts.json")
MIN_PRECINCT_IOU = 0.98      # measured 0.99127 / 0.99854 / 0.99646


def fail(msg):
    raise SystemExit("story-supervisor-districts: " + msg)


def curl(url, binary=True):
    out = subprocess.run(
        ["curl", "-sS", "--fail", "-L", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True).stdout
    return out if binary else out.decode()


def fetch_pdf():
    body = curl(PDF_URL)
    got = hashlib.sha256(body).hexdigest()
    if got != PDF_SHA256 or len(body) != PDF_BYTES:
        fail("the county's district map has changed (%d bytes, sha256 %s; "
             "expected %d / %s). A re-printed map may carry a redrawn plan, a "
             "different projection or a different panel layout — re-verify it "
             "by hand and re-pin, rather than letting this script re-derive "
             "silently." % (len(body), got, PDF_BYTES, PDF_SHA256))
    return body


def subpath_points(curve):
    """The curve's own path operators, as one polyline.

    pdfplumber's `pts` flattens subpaths together; `path` keeps the `m`/`l`
    operators, so a curve that is really two rings stays separable. Each of
    Story's district strokes turns out to be a single subpath, which this
    returns and the caller checks.
    """
    pts, cur = [], []
    for op in curve["path"]:
        if op[0] == "m":
            if len(cur) >= 3:
                pts.append(cur)
            cur = [op[1]]
        elif op[0] in ("l", "c", "v", "y"):
            cur.append(op[-1])
    if len(cur) >= 3:
        pts.append(cur)
    return pts


def read_rings(page, Polygon, Point):
    """The left panel's three district rings, each labelled by the numeral
    inside it. Every step here is a gate: this is the part that would fail
    quietly if the map were re-laid-out."""
    strokes = [c for c in page.curves
               if round(c.get("linewidth") or 0, 1) == DISTRICT_LINEWIDTH
               and c["x0"] < PANEL_SPLIT_X]
    if len(strokes) != len(EXPECT_DISTRICTS):
        fail("the left panel carries %d linewidth-%g curves, expected %d. The "
             "district strokes are the only curves on this page at that weight; "
             "a different count means the map was re-drawn or re-laid-out."
             % (len(strokes), DISTRICT_LINEWIDTH, len(EXPECT_DISTRICTS)))

    numerals = [c for c in page.chars
                if NUMERAL_SIZE[0] < c["size"] < NUMERAL_SIZE[1]
                and c["x0"] < PANEL_SPLIT_X and c["text"] in EXPECT_DISTRICTS]
    if sorted(c["text"] for c in numerals) != sorted(EXPECT_DISTRICTS):
        fail("the left panel's district numerals are %s, expected exactly %s"
             % (sorted(c["text"] for c in numerals), sorted(EXPECT_DISTRICTS)))

    rings = {}
    for c in strokes:
        parts = subpath_points(c)
        if len(parts) != 1:
            fail("a district stroke is %d subpaths, expected 1 — the ring may "
                 "be drawn with a slit and would need reassembling" % len(parts))
        ring = parts[0]
        if math.hypot(ring[0][0] - ring[-1][0], ring[0][1] - ring[-1][1]) > 2.0:
            fail("a district stroke is not closed (%.1f pt gap); an open path "
                 "cannot bound a district" % math.hypot(ring[0][0] - ring[-1][0],
                                                        ring[0][1] - ring[-1][1]))
        poly = Polygon(ring).buffer(0)
        # pdfplumber's `path` coordinates are TOP-DOWN, matching `top`/`bottom`
        # on chars. Read bottom-up this test puts two numerals in one ring and
        # none in another, so it is also the proof of the convention.
        inside = [n["text"] for n in numerals
                  if poly.contains(Point((n["x0"] + n["x1"]) / 2,
                                         (n["top"] + n["bottom"]) / 2))]
        if len(inside) != 1:
            fail("a district ring contains %d numerals (%s), expected exactly "
                 "one. The map's own legend calls these the Supervisor District "
                 "Number, so a ring with none or two is unlabelled and nothing "
                 "here guesses which it is." % (len(inside), inside))
        if inside[0] in rings:
            fail("numeral %r falls inside two rings" % inside[0])
        rings[inside[0]] = poly
    return rings


def fetch_blocks(shape_fn):
    """Every Census 2020 block in the county, with POP100.

    api.census.gov's /data endpoint now redirects to missing_key.html without
    an API key; TIGERweb carries the same POP100 unauthenticated and is what
    every other builder in this repo already uses. TIGERweb also pages, and
    returns an empty page for an unordered query, which reads as 'the county
    has no blocks' — hence orderByFields.
    """
    out, offset = {}, 0
    while True:
        q = urllib.parse.urlencode({
            "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, COUNTY_FIPS),
            "outFields": "GEOID,POP100", "returnGeometry": "true",
            "outSR": "4326", "f": "geojson", "orderByFields": "GEOID",
            "resultOffset": offset, "resultRecordCount": 1000})
        data = json.loads(curl(BLOCK_URL + "?" + q, binary=False))
        if "error" in data:
            fail("TIGERweb answered HTTP 200 with an error envelope: %r"
                 % data["error"])
        feats = data.get("features") or []
        for f in feats:
            out[f["properties"]["GEOID"]] = f
        offset += len(feats)
        if len(feats) < 1000:
            break
    if len(out) != EXPECTED_BLOCKS:
        fail("TIGERweb returned %d blocks for Story County, expected %d"
             % (len(out), EXPECTED_BLOCKS))
    total = sum(int(f["properties"].get("POP100") or 0) for f in out.values())
    if total != COUNTY_POP_2020:
        fail("the blocks sum to %d people, expected the county's Census 2020 "
             "population of %d" % (total, COUNTY_POP_2020))
    return out


def lsa_precinct_name(name):
    """LSA's precinct spelling -> the spelling ia-precincts.json ships.

    Two differences, both mechanical. LSA writes Ames precincts unpadded and
    sometimes with the township share appended ("Ames 7/Franklin Twp 2"), where
    the shipped fabric writes "Ames 07"; and LSA writes plain "Huxley 1" where
    the shipped name carries the township ("Huxley 1/Union Twp 2"). Everything
    else matches character for character.
    """
    name = re.sub(r"\s+", " ", name).strip()
    m = re.match(r"^Ames (\d+)", name)
    if m:
        return "Ames %02d" % int(m.group(1))
    if name == "Huxley 1":
        return "Huxley 1/Union Twp 2"
    return name


def check_against_lsa_precincts(shipped, shape_fn, union_fn, transform_fn, fwd):
    """Rebuild the districts from LSA's precinct lists and compare.

    This is the second witness, and it shares nothing with the first: the map
    supplies no part of it and the population figures supply no part of it. If
    the map were misread or misgeoreferenced, the dissolve would not land on it.

    It is an IoU rather than an equality because the two are not the same
    fabric: the districts here are unions of census BLOCKS, and Iowa's shipped
    precinct layer carries a 2024 vintage in which several rural Story
    precincts still hold their 2020 census voting-district geometry. Those
    disagree with the current lines by slivers, not by territory.
    """
    try:
        with open(PRECINCTS_PATH) as f:
            pf = json.load(f)
    except OSError as e:
        fail("%s is missing (%s); the precinct gate needs it"
             % (os.path.relpath(PRECINCTS_PATH, REPO_ROOT), e))
    by_name = {f["properties"]["name"]: shape_fn(f["geometry"]).buffer(0)
               for f in pf.get("features", [])
               if f["properties"].get("county") == "Story"}

    listed = [lsa_precinct_name(n)
              for v in LSA_FIRST_PLAN_PRECINCTS.values() for n in v]
    if len(listed) != len(set(listed)):
        fail("LSA's first plan lists a precinct in more than one district")
    missing = sorted(set(listed) - set(by_name))
    unlisted = sorted(set(by_name) - set(listed))
    if missing or unlisted:
        fail("LSA's first plan and the shipped precinct fabric do not describe "
             "the same %d precincts — listed but not shipped: %s; shipped but "
             "not listed: %s. A renamed or re-drawn precinct invalidates this "
             "gate rather than merely failing it."
             % (len(by_name), missing, unlisted))

    worst = 1.0
    for k in sorted(shipped):
        dissolved = union_fn([by_name[lsa_precinct_name(n)]
                              for n in LSA_FIRST_PLAN_PRECINCTS[k]]).buffer(0)
        inter = transform_fn(fwd, dissolved.intersection(shipped[k])).area
        union = transform_fn(fwd, dissolved.union(shipped[k])).area
        iou = inter / union if union else 0.0
        worst = min(worst, iou)
        if iou < MIN_PRECINCT_IOU:
            fail("district %s dissolved from LSA's own precinct list overlaps "
                 "the map-derived district at only IoU %.5f (floor %.2f) — two "
                 "independent descriptions of the same district disagree"
                 % (k, iou, MIN_PRECINCT_IOU))
    print("PRECINCT GATE: LSA's first-plan precinct lists (%d precincts, %d/%d "
          "matching the shipped fabric) dissolve onto the map-derived districts "
          "at worst IoU %.5f" % (len(listed), len(listed), len(by_name), worst),
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare against the shipped file")
    args = ap.parse_args()

    import pdfplumber                                        # noqa: E402
    from shapely.geometry import Polygon, Point, shape, mapping   # noqa: E402
    from shapely.ops import unary_union, transform            # noqa: E402
    from pyproj import Transformer                            # noqa: E402

    body = fetch_pdf()
    tmp = os.path.join(OUT_DIR, ".story-map.pdf")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(body)
    try:
        with pdfplumber.open(tmp) as pdf:
            rings = read_rings(pdf.pages[0], Polygon, Point)
    finally:
        os.remove(tmp)
    print("map: %d district rings, one legend numeral each (%s); prepared %s, "
          "board adopted %s" % (len(rings), "/".join(sorted(rings)),
                                MAP_PREPARED, BOARD_ADOPTED), file=sys.stderr)

    to_plan = Transformer.from_crs("EPSG:4326", PLAN_CRS, always_xy=True)
    fwd = lambda x, y, z=None: to_plan.transform(x, y)   # noqa: E731

    blocks = fetch_blocks(shape)
    county = unary_union([transform(fwd, shape(f["geometry"])).buffer(0)
                          for f in blocks.values()])
    if county.geom_type != "Polygon":
        fail("the county's blocks union to a %s, not one polygon"
             % county.geom_type)

    # --- georeference: fit the drawn extent to the county's own extent ------
    drawn = unary_union(list(rings.values())).buffer(0)
    db, cb = drawn.bounds, county.bounds
    a_drawn = (db[2] - db[0]) / (db[3] - db[1])
    a_true = (cb[2] - cb[0]) / (cb[3] - cb[1])
    off_pct = 100 * abs(a_drawn / a_true - 1)
    if off_pct > ASPECT_CEILING_PCT:
        fail("the drawn county's aspect is %.5f against %.5f in %s (%.2f%% off, "
             "ceiling %.2f%%). The map is not drawn in the projection this "
             "script fits, so a linear fit would misplace every line."
             % (a_drawn, a_true, PLAN_CRS, off_pct, ASPECT_CEILING_PCT))
    sx = (cb[2] - cb[0]) / (db[2] - db[0])
    sy = (cb[3] - cb[1]) / (db[3] - db[1])
    # PDF y runs TOP-DOWN; northing runs up, hence the subtraction.
    place = lambda x, y, z=None: (cb[0] + (x - db[0]) * sx,   # noqa: E731
                                  cb[3] - (y - db[1]) * sy)
    dist = {k: transform(place, v).buffer(0) for k, v in rings.items()}

    edge, n = county.exterior, 2000
    fitted_edge = transform(place, drawn).exterior
    offs = sorted(edge.distance(fitted_edge.interpolate(i * fitted_edge.length / n))
                  for i in range(n))
    mean_off = sum(offs) / len(offs)
    if mean_off > MEAN_OFFSET_CEILING_M or offs[-1] > MAX_OFFSET_CEILING_M:
        fail("the fitted map's outline sits %.1f m from the county's real "
             "outline on average (max %.1f m); ceilings are %.1f / %.1f"
             % (mean_off, offs[-1], MEAN_OFFSET_CEILING_M, MAX_OFFSET_CEILING_M))
    print("georeference: %s, aspect %.5f vs %.5f (%.2f%% off), boundary offset "
          "mean %.1f m / max %.1f m" % (PLAN_CRS, a_drawn, a_true, off_pct,
                                        mean_off, offs[-1]), file=sys.stderr)

    ks = sorted(dist)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            ov = dist[ks[i]].intersection(dist[ks[j]]).area
            if ov > RING_OVERLAP_CEILING_M2:
                fail("districts %s and %s overlap by %.1f m2 as drawn"
                     % (ks[i], ks[j], ov))
    uncovered = county.difference(unary_union(list(dist.values()))).area
    if 100 * uncovered / county.area > UNCOVERED_CEILING_PCT:
        fail("the three rings leave %.4f%% of the county uncovered — they do "
             "not tile it, so at least one line is misread"
             % (100 * uncovered / county.area))

    # --- resolve to whole blocks: nothing traced ships ---------------------
    groups, pops = {k: [] for k in ks}, {k: 0 for k in ks}
    worst, marginal = 1.0, []
    for f in blocks.values():
        g4 = shape(f["geometry"])
        g = transform(fwd, g4).buffer(0)
        if g.is_empty or g.area == 0:
            continue
        share = {k: g.intersection(dist[k]).area / g.area for k in ks}
        best = max(share, key=share.get)
        worst = min(worst, share[best])
        pop = int(f["properties"].get("POP100") or 0)
        if share[best] < 0.99:
            marginal.append((f["properties"]["GEOID"], pop))
        groups[best].append(g4.buffer(0))
        pops[best] += pop
    if worst < MIN_BLOCK_SHARE:
        fail("a block sits only %.2f%% inside its best district (floor %.0f%%) "
             "— the line runs through it and the map alone cannot say which "
             "side its people are on" % (100 * worst, 100 * MIN_BLOCK_SHARE))
    print("blocks: %d sorted, worst nesting %.2f%%; %d nest under 99%% and "
          "hold %d people between them"
          % (len(blocks), 100 * worst, len(marginal),
             sum(p for _, p in marginal)), file=sys.stderr)

    # --- THE GATE: a different county product, and it must agree exactly ----
    shipped = {}
    for k in ks:
        u = unary_union(groups[k]).buffer(0)
        if u.geom_type != "Polygon":
            fail("district %s dissolves to a %s — a district that is not one "
                 "contiguous piece is either misread or not a legal plan"
                 % (k, u.geom_type))
        if u.interiors:
            fail("district %s dissolves with %d hole(s)" % (k, len(u.interiors)))
        shipped[k] = u
    if pops != LSA_POPULATIONS:
        fail("the derived district populations are %s and the Legislative "
             "Services Agency's FIRST plan publishes %s. Those numbers are not "
             "an input to this derivation, so a disagreement means the lines, "
             "the labels or the fit are wrong — not that the check is. (Its "
             "SECOND plan is %s; if the derivation matches THAT, the county "
             "adopted the other plan and this whole build needs redoing "
             "against it, not adjusting.)"
             % (pops, LSA_POPULATIONS, LSA_SECOND_POPULATIONS))
    if pops == LSA_SECOND_POPULATIONS:
        fail("the derived populations match LSA's SECOND plan, which the map "
             "is not supposed to draw")
    print("POPULATION GATE: %s — matches LSA's FIRST plan exactly, district by "
          "district in order, and matches none of the second plan's %s"
          % (dict(sorted(pops.items())),
             dict(sorted(LSA_SECOND_POPULATIONS.items()))), file=sys.stderr)

    # --- SECOND GATE: LSA's own precinct lists, dissolved -------------------
    check_against_lsa_precincts(shipped, shape, unary_union, transform, fwd)

    # shipped[] is lon/lat, because that is what the app reads; `county` is in
    # the plan CRS, because a tolerance in square degrees means nothing. Project
    # before comparing -- the first draft did not, and this gate correctly
    # reported the whole county as the difference.
    total = transform(fwd, unary_union(list(shipped.values()))).buffer(0)
    slack = total.symmetric_difference(county).area
    if slack > 1.0:
        fail("the three dissolved districts do not tile the county (%.1f m2 of "
             "symmetric difference)" % slack)
    print("partition: 3 contiguous hole-free districts tiling the county to "
          "%.3f m2" % slack, file=sys.stderr)

    def rnd(o, p=6):
        """Round every coordinate to p decimals.

        THE TUPLE BRANCH IS THE WHOLE POINT. shapely's mapping() returns
        coordinates as nested TUPLES, not lists; a version of this that handled
        only list and dict fell through to `return o` on every coordinate pair
        and rounded nothing, shipping 15-decimal floats in a file whose whole
        precision budget is 6. It looked like it worked because the output was
        valid GeoJSON of the right shape -- 31% larger, and nothing measured
        the size.
        """
        if isinstance(o, float):
            return round(o, p)
        if isinstance(o, (list, tuple)):
            return [rnd(x, p) for x in o]
        if isinstance(o, dict):
            return {k: rnd(v, p) for k, v in o.items()}
        return o

    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "properties": {"DISTRICT": k, "POPULATION": pops[k],
                        "SOURCE": SOURCE_ID, "SOURCE_URL": SOURCE_URL},
         "geometry": rnd(mapping(shipped[k]))} for k in ks]}
    payload = json.dumps(fc, indent=1, sort_keys=True) + "\n"
    out_path = os.path.join(OUT_DIR, OUT_NAME)

    if args.check:
        try:
            with open(out_path) as f:
                have = f.read()
        except OSError as e:
            fail("%s is missing (%s)" % (OUT_NAME, e))
        if have != payload:
            fail("data/source/%s has drifted from a fresh derivation. Re-run: "
                 "python3 ia/scripts/build_story_supervisor_districts.py"
                 % OUT_NAME)
        print("check: the shipped districts match a fresh read of the map",
              file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/source/%s (%d districts, %s)"
          % (OUT_NAME, len(ks), LSA_CITE), file=sys.stderr)


if __name__ == "__main__":
    main()

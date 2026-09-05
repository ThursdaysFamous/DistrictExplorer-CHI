#!/usr/bin/env python3
"""Build mi/data/app/mi-grand-rapids-wards.json — Grand Rapids's three City
Commission wards, from the city's own ArcGIS org.

WHAT GRAND RAPIDS ELECTS, IN THE CITY'S OWN WORDS
---------------------------------------------------
From grandrapidsmi.gov/Government/City-Commission, quoted rather than
paraphrased because the arithmetic matters:

    "This legislative body consists of the Mayor and six Commissioners. The
     City is divided into three legislative districts called Wards. The
     residents of each Ward directly elect two commissioners to represent
     them. Commissioners serve four-year overlapping terms. Every two years,
     the community elects one commissioner from each ward."

So TWO commissioners ride each of these three polygons and the Mayor rides
none of them. That is why a ward layer is honest here where a polygon for an
at-large body would not be, and why the card carries the Mayor in a citywide
block rather than dropping him: a card naming two of seven would look complete.

THE CURRENCY QUESTION, AND THE WITNESS THAT ANSWERS IT
--------------------------------------------------------
THE CITY PUBLISHES EIGHT WARD SERVICES, AND AN EARLIER VERSION OF THIS
DOCSTRING SAID TWO. That number came from a search capped at the first 100 of
the org's 681 feature services — a truncated listing read as a measurement.
Swept in full and each compared against what ships (2026-09-05):

    City_of_Grand_Rapids_Wards   3 features   100.000%   identical
    GR Wards                     3 features   100.000%   identical
    City Wards                   3 features   100.000%   identical
    Wards                        3 features    99.733%   edge differences only
    GR 1st Ward                  1 feature    100.000%   vs shipped Ward 1
    GR 2nd Ward                  1 feature     98.400%   vs shipped Ward 2, 0
                                                         points in a different
                                                         ward, 24 edge-only
    GR 3rd Ward                  1 feature    100.000%   vs shipped Ward 3

The three `GR Nth Ward` services are SINGLE wards rather than rival plans, and
comparing them against the whole city is the wrong test — done that way they
score 26-38% purely because they cover a third of it. Measured against their
OWN ward they agree. So no newer plan exists anywhere in the org and the
conclusion below stands; the count was wrong, not the finding.

The duplicate gate below watches ONE of the seven siblings, which is a real
limit rather than an oversight: `City_of_Grand_Rapids_Wards` is the one that
has tracked `CGR_Wards` byte for byte, and widening the gate to all seven would
fail the build on the two that already differ at the city edge.

The real doubt was age. `CGR_Wards` has `editingInfo.dataLastEditDate` of
2018-01-24 — before the census these wards are checked against — while its
own item description claims it is "maintained to reflect the most current
adopted ward configuration". A description is a claim; this project measures.

THE MEASUREMENT IS THE STATE'S OWN CURRENT PRECINCT LAYER. Michigan's Bureau
of Elections publishes `2026_Voting_Precincts`, which this instance already
ships, and it carries a WARD column: it assigns each of the City of Grand
Rapids's 59 precincts (MCDFIPS 34000) to ward 1, 2 or 3, 20/20/19. Dissolved
by that column and compared against the city's polygons by point
classification, the two agree on 99.575% of 4,000 points, with just 2 landing
in a different ward and the rest at the city's outer edge. Two independent
publishers — one whose geometry was last edited in 2018, one built for the
2026 election cycle — drawing the same three lines. So 2018 means UNCHANGED
rather than stale, and the description is accurate.

That comparison is a GATE here, not a note, because it is the only thing
standing between this app and a decade-old ward map.

A THIRD WITNESS, AND THE CHEAPEST ONE: THE CITY CONSUMES THIS SERVICE ITSELF.
The org publishes two chains of ward products, and they point at the two
services. The city's public ward viewer — the web app "City of Grand Rapids
Wards" (modified 2026-05-15) — wraps the web map "Wards" (2026-03-05), which
draws `CGR_Wards/FeatureServer/0`, the exact service shipped here; so does
"Wards-Zoomed-Out" (2018-06-01). The duplicate is drawn by a departmental
chain: the web experience "City Wards for GRPD" (2026-06-23) wraps the web map
"Updated City Wards for GRPD" (2026-06-23), which pairs it with a Consumers
Energy outage layer. A publisher pointing its own public map products at a
layer is evidence about which layer it maintains, and it costs one catalogue
query to check.

RECENCY IS NOT WHAT MAKES THAT A WITNESS, and an earlier draft of this
paragraph said the duplicate was drawn by "an older map" — measured
2026-09-05, the GRPD pair is the NEWEST of the five, by three months. What the
chains show is which product is the CITY'S ward viewer, not which was touched
last. Not gated either way, because the two services are byte-identical
geometry and THAT is gated (100.00% agreement, above) — a city reorganising
its web maps is not a redraw. Worth reading before the expensive comparisons,
and this build did not.

THE POPULATION IDENTITY IS *NOT* EXACT HERE, AND IS NOT ASSERTED AS IF IT WERE
--------------------------------------------------------------------------------
Detroit's seven districts sum to its Census 2020 count exactly, so that build
asserts the identity as its tiling proof. Grand Rapids does not, and pretending
otherwise would be the more comfortable lie. Measured on the 2,883 Census 2020
blocks over the city's envelope:

    inside a ward but outside the Census place :  11 blocks,  78 people
    inside the Census place but outside a ward :  10 blocks,  12 people
    net                                        :  +66 against 198,917

Twenty-one blocks at the city's edge. THE DENOMINATOR IS 2,883 — the blocks
inside EITHER outline — and not the 4,202 the envelope fetch returns, which is
stated here because the two are easy to confuse and only one of them means
anything: a block a mile outside both outlines cannot disagree about where the
city edge runs, so including it would flatter the rate rather than tighten it.
(2,873 fall inside a ward, 2,872 inside the place, 2,883 inside either.)

The city's ward outline and the Census place outline are two independent
digitisations of one municipal boundary, and they disagree by metres along it.
So the gate is a TOLERANCE with the measured value recorded, plus a check that
the disagreement stays confined to that edge rather than opening a hole inside
the city.

BALANCE. Against Census 2020 the three wards run 64,400-68,716 on a 66,328
ideal, worst 3.60% — which is what a plan in force looks like, and is a second,
independent reason to believe the 2018 file.

LICENCE. The item carries a long `licenseInfo`, and it is the DES MOINES CASE
rather than a refusal: a "Data Access and Use Constraint Agreement" that
conditions use on carrying the city's disclaimer, provided "as a complementary
service to its residents". The card carries the sentences of that agreement
that describe the DATA, QUOTED FROM IT — not a paraphrase, which is what this
build shipped first while this paragraph called it verbatim. Des Moines's card
quotes its city's words too; that was the precedent being claimed and not
followed. THE SECOND DRAFT WAS NOT VERBATIM EITHER, in two ways a reader of the
card could not have caught: it dropped the ("City") parenthetical from the
opening sentence and cut the agreement's two acceptance sentences without an
ellipsis. Both are fixed, the cut is marked, and the quotation is now ASSERTED
segment by segment against the live licenceInfo on every run — so a reworded
agreement fails this build rather than leaving the card quoting words the city
has stopped saying.

A MAPSHAPER WARNING THAT IS NOT A DEFECT, MEASURED SO NOBODY RE-CHASES IT.
Every tolerance above 20% prints "Repaired 0 intersections; N intersections
could not be repaired" (5 at 30%, 10 at 40%, 11 at 50%), and the source is
silent at 100%, so simplification introduces them. They are NOT in the output:
a direct segment-crossing scan of the shipped rings finds ZERO
self-intersections, and no sampled point lands in two wards. The warning
describes shared arcs in mapshaper's own topology model, between features
rather than within a ring. `-clean` was tried and changes nothing measurable
(same 99.90% agreement, same zero overlaps, 436 bytes larger), so it is not
used.

A FIELD THAT LOOKS LIKE A PRECINCT COUNT AND IS NOT. `WARD_CNT` reads 49, 34,
33 — summing to 116, where the city has 59 precincts today. Whatever it counts,
it is not the current precinct fabric, and it is read nowhere here.

    python3 mi/scripts/build_mi_grand_rapids_wards.py           # rebuild
    python3 mi/scripts/build_mi_grand_rapids_wards.py --check   # offline gate
"""

import argparse
import html as htmllib
import json
import os
import random
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
INSTANCE_ROOT = os.path.dirname(HERE)
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
MAPSHAPER = "mapshaper@0.6.25"

CITY_ORG = "https://services2.arcgis.com/L81TiOwAPO1ZvU9b/arcgis/rest/services"
SERVICE = CITY_ORG + "/CGR_Wards/FeatureServer/0"
# The byte-identical sibling, one of SEVEN in the org (see the docstring). Read
# once, as a witness that it IS a duplicate — if the two ever diverge, a human
# should decide which the city maintains. The other six are not gated: three are
# single-ward layers and two already differ at the city edge, so a gate over all
# of them would refuse a correct build.
DUPLICATE = CITY_ORG + "/City_of_Grand_Rapids_Wards/FeatureServer/0"

# The state's own CURRENT precinct fabric, already shipped by this instance.
PRECINCTS = ("https://services3.arcgis.com/dxRQUfTDNtfqZ301/arcgis/rest/"
             "services/2026_Voting_Precincts/FeatureServer/0")
PRECINCT_WHERE = "Jurisdiction_Name = 'Grand Rapids'"

BLOCKS = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
          "tigerWMS_Census2020/MapServer/10/query")
PLACE = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
         "tigerWMS_Census2020/MapServer/26/query")
PLACE_GEOID = "2634000"          # Grand Rapids city, MI

OUT_FILE = "mi-grand-rapids-wards.json"
# 50%, AND THE SIBLINGS' 20-25% WOULD HAVE BEEN THE WRONG NUMBER TO COPY.
# mapshaper's percentage is a share of the SOURCE vertex count, so it means
# different things at different feature counts: Milwaukee's 25% and the three
# Iowa ward layers' 20% are applied to layers with far more geometry, while
# Grand Rapids is THREE features, and at 20% there is simply not enough left to
# describe the line. Measured on this layer, agreement against the
# full-precision source runs 98.95% at 20% (below the fleet's 99.5% floor),
# 99.70% at 30%, 99.80% at 40% and 99.90% at 50%. 50% is taken for the margin:
# the whole file is under 8 KB either way, so a kilobyte is nothing against a
# ward line that is somebody's representation. THE FLOOR WAS NEVER THE THING TO
# MOVE — the tolerance was.
SIMPLIFY = "50%"
PRECISION = "0.000001"

EXPECT_FEATURES = 3
EXPECT_WARDS = ("1", "2", "3")
# The city's own statement, above: two commissioners per ward, plus a mayor.
COMMISSIONERS_PER_WARD = 2

GR_POP_2020 = 198917             # re-fetched and asserted, never trusted from here
MAX_DEVIATION = 0.06             # measured 0.0360
# The wards and the Census place are two digitisations of one city line; this
# bounds their disagreement rather than pretending it is zero.
MAX_POP_DELTA_FRACTION = 0.002   # measured 0.00033 (+66 of 198,917)
MAX_EDGE_BLOCKS = 60             # measured 21
# The currency gate: the state's 2026 precincts must still describe these wards.
MIN_PRECINCT_AGREEMENT = 0.99    # measured 0.99575
EXPECT_PRECINCTS = {"1": 20, "2": 20, "3": 19}

KEEP_FIELDS = ("WARD",)
DERIVED_FIELDS = ("Ward",)


def fail(msg):
    print("build-mi-grand-rapids-wards: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def curl(url):
    return subprocess.run(["curl", "-sS", "--fail", "--max-time", "120", url],
                          check=True, capture_output=True).stdout


def fetch_license_info():
    """The city's use agreement, as HTML, off the service's OWN AGO item.

    The item id is read from the service rather than hardcoded, so a republish
    under a new item still lands on the agreement the shipped geometry actually
    carries. Observed 2026-09-05: a576ba34b3dd4a0ea6fef475d1100ef3."""
    svc = json.loads(curl(SERVICE + "?f=json"))
    iid = svc.get("serviceItemId")
    if not iid:
        fail("%s carries no serviceItemId, so its use agreement cannot be read — "
             "the disclaimer this build ships is quoted from that agreement and is "
             "not shipped unverified" % SERVICE)
    item = json.loads(curl(
        "https://www.arcgis.com/sharing/rest/content/items/%s?f=json" % iid))
    return item.get("licenseInfo") or ""


def flatten_licence(html_text):
    t = htmllib.unescape(re.sub(r"<[^>]+>", " ", html_text))
    # The agreement is typed with curly quotes; normalise BOTH sides rather than
    # matching on a character an editor can change without changing a word.
    t = t.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", t).strip()


def check_disclaimer_is_quoted(quote, license_info):
    """Every segment of the shipped disclaimer must appear, in order, in the
    city's live agreement — the gate that keeps a QUOTATION a quotation.

    Nothing compared the two before: the first draft of this build composed its
    own sentence, the second dropped a parenthetical and silently cut two
    sentences, and both shipped under a docstring calling the result verbatim.
    A reworded agreement now fails the build instead."""
    flat = flatten_licence(license_info)
    if len(flat) < 500:
        fail("the city's licenseInfo came back %d characters — too short to be the "
             "use agreement, so the shipped disclaimer cannot be verified against it"
             % len(flat))
    at = 0
    for seg in [s.strip() for s in flatten_licence(quote).split("\u2026")]:
        if not seg:
            continue
        i = flat.find(seg, at)
        if i < 0:
            fail("the shipped disclaimer quotes %r, which is not in the city's live "
                 "use agreement (in order, after character %d). The agreement has "
                 "been reworded: re-quote it, never reword the quotation" % (seg, at))
        at = i + len(seg)
    print("  disclaimer: %d character(s) quoted from the city's live use agreement "
          "(%d characters), in order" % (len(quote), len(flat)))


def esri(url, params):
    p = {"f": "geojson", "outSR": 4326, "geometryPrecision": 6}
    p.update(params)
    u = url + ("/query?" if not url.endswith("/query") else "?") + urllib.parse.urlencode(p)
    out = subprocess.run(["curl", "-sS", "--fail", "--max-time", "300", u],
                         check=True, capture_output=True).stdout
    d = json.loads(out)
    if isinstance(d, dict) and "error" in d:
        raise RuntimeError("%s answered an error envelope: %r" % (url, d["error"]))
    feats = d.get("features") or []
    if not feats:
        raise RuntimeError(
            "%s returned no features — an Esri error envelope arrives as HTTP 200, "
            "so read this as 'the field list or the service moved', not an outage" % url)
    if d.get("exceededTransferLimit"):
        raise RuntimeError("%s hit its transfer cap — needs paging" % url)
    return feats


# --- point-in-polygon, mirroring index.html's even-odd test -------------------
def _in_ring(pt, ring):
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def in_geometry(pt, geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if not poly or not _in_ring(pt, poly[0]):
            continue
        if any(_in_ring(pt, hole) for hole in poly[1:]):
            continue
        return True
    return False


def ward_of(props):
    """One ward id from either publisher's spelling.

    THE TWO PUBLISHERS DISAGREE ON THE SPELLING AND AGREE ON THE VALUE: the
    city writes the integers 1/2/3, the state's precinct layer writes the
    zero-padded strings '01'/'02'/'03'. Comparing them raw makes the currency
    gate below refuse a perfectly good pair, which is exactly what it did on
    the first run. Normalised NUMERICALLY rather than by stripping characters,
    so this can never quietly fold two distinct ward ids into one."""
    for k in ("WARD", "Ward", "ward"):
        v = props.get(k)
        if v in (None, ""):
            continue
        raw = str(v).strip()
        if raw.lower().startswith("ward"):
            raw = raw[4:].strip()
        try:
            return str(int(raw))
        except ValueError:
            return raw
    return None


def model(features, key=ward_of):
    return [(key(f.get("properties") or {}), f["geometry"])
            for f in features if f.get("geometry")]


def bbox(features):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for q in c:
                walk(q)
    for f in features:
        walk(f["geometry"]["coordinates"])
    return min(xs), min(ys), max(xs), max(ys)


def fetch_blocks(box):
    env = "%2C".join("%.5f" % v for v in box)
    url = (BLOCKS + "?where=STATE%3D%2726%27&geometry=" + env +
           "&geometryType=esriGeometryEnvelope&inSR=4326"
           "&spatialRel=esriSpatialRelIntersects"
           "&outFields=POP100,INTPTLAT,INTPTLON&returnGeometry=false"
           "&outSR=4326&f=json&resultRecordCount=100000")
    d = json.loads(subprocess.run(["curl", "-sS", "--fail", "--max-time", "600", url],
                                  check=True, capture_output=True).stdout)
    if "error" in d:
        raise RuntimeError("TIGERweb answered an error envelope: %r" % d["error"])
    if d.get("exceededTransferLimit"):
        raise RuntimeError("TIGERweb capped the block fetch — needs paging")
    rows = []
    for f in d.get("features", []):
        a = f["attributes"]
        try:
            rows.append((float(a["INTPTLON"]), float(a["INTPTLAT"]), int(a["POP100"] or 0)))
        except (TypeError, ValueError, KeyError):
            continue
    if len(rows) < 2000:
        raise RuntimeError("only %d usable blocks — expected ~2,900 over Grand Rapids" % len(rows))
    return rows


def point_agreement(a, b, box, samples=4000, seed=20260905):
    """Fraction of points landing in EITHER model that both put in the same
    unit. Used twice: city-wards vs state-precinct-dissolve (the currency
    gate) and full-precision vs simplified (the fleet's 2,000-point protocol)."""
    rng = random.Random(seed)
    hit = same = diff = only_a = only_b = 0
    tried = 0
    while hit < samples and tried < samples * 80:
        tried += 1
        pt = (rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3]))
        ha = [k for k, g in a if in_geometry(pt, g)]
        hb = [k for k, g in b if in_geometry(pt, g)]
        if not ha and not hb:
            continue
        hit += 1
        if ha and hb:
            if ha[0] == hb[0]:
                same += 1
            else:
                diff += 1
        elif ha:
            only_a += 1
        else:
            only_b += 1
    return {"hit": hit, "same": same, "diff": diff, "only_a": only_a, "only_b": only_b,
            "frac": (same / hit) if hit else 0.0}


def overlaps(m, box, samples=2000, seed=7):
    rng = random.Random(seed)
    n = 0
    for _ in range(samples):
        pt = (rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3]))
        if len([k for k, g in m if in_geometry(pt, g)]) > 1:
            n += 1
    return n


def check_shape(feats, require_derived=False):
    """`require_derived` is False upstream of the build, where the fetched
    features carry only the publisher's own WARD column, and True on the
    shipped file, where the bare `Ward` the card and hover both read must
    exist. Conflating the two is why the first run of this script refused its
    own input."""
    problems = []
    if len(feats) != EXPECT_FEATURES:
        problems.append("%d features, expected %d — Grand Rapids has three wards"
                        % (len(feats), EXPECT_FEATURES))
    seen = tuple(sorted((ward_of(f.get("properties") or {}) or "?") for f in feats))
    if seen != EXPECT_WARDS:
        problems.append("ward numbers are %s, expected %s" % (list(seen), list(EXPECT_WARDS)))
    if require_derived:
        for f in feats:
            if "Ward" not in (f.get("properties") or {}):
                problems.append("a feature carries no bare Ward number — the card headline "
                                "and the hover label both read it")
                break
    return problems


def check_shipped(path):
    if not os.path.exists(path):
        return ["%s is missing" % path]
    with open(path) as f:
        shipped = json.load(f)
    feats = shipped.get("features") or []
    problems = check_shape(feats, require_derived=True)
    keys = {k for f in feats for k in (f.get("properties") or {})}
    stray = keys - set(KEEP_FIELDS) - set(DERIVED_FIELDS)
    if stray:
        problems.append("shipped properties carry unexpected keys: %s" % sorted(stray))
    if not shipped.get("disclaimer"):
        problems.append("the city's required use disclaimer is missing — its licence "
                        "conditions use on carrying it, and the card renders it")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="offline gate on the shipped file")
    args = ap.parse_args()
    out_path = os.path.join(APP_DATA_DIR, OUT_FILE)

    if args.check:
        problems = check_shipped(out_path)
        if problems:
            fail("; ".join(problems))
        print("build-mi-grand-rapids-wards: OK — 3 wards shipped")
        return

    # First, because a quotation this cannot verify must not reach the geometry
    # work at all: the shipped disclaimer is the city's own words, and an
    # agreement that has been reworded is a build failure, not a card edit.
    print("reading the city's use agreement off the service's own AGO item…")
    license_info = fetch_license_info()

    print("fetching the city's ward service and its duplicate…")
    wards = esri(SERVICE, {"where": "1=1", "outFields": "WARD"})
    dup = esri(DUPLICATE, {"where": "1=1", "outFields": "WARD"})
    problems = check_shape(wards)
    if problems:
        fail("; ".join(problems))

    box = bbox(wards)
    wm = model(wards)

    # The duplicate must stay a duplicate. If the city ever edits one and not
    # the other, that is a human's call, not this script's.
    dm = model(dup)
    dupe = point_agreement(wm, dm, box, samples=1500, seed=11)
    if dupe["frac"] < 0.999:
        fail("City_of_Grand_Rapids_Wards has DIVERGED from CGR_Wards (%.3f%% agreement) — "
             "they were byte-identical when this was written, so a human must decide "
             "which the city now maintains" % (100 * dupe["frac"]))
    print("  the city's second ward service is still the same geometry (%.2f%%)"
          % (100 * dupe["frac"]))

    # ---- CURRENCY: the state's own 2026 precincts must describe these wards --
    print("fetching the state's 2026 precincts for the currency gate…")
    precs = esri(PRECINCTS, {"where": PRECINCT_WHERE, "outFields": "WARD,PRECINCT"})
    pm = model(precs, key=lambda p: ward_of(p))
    counts = {}
    for k, _ in pm:
        counts[k] = counts.get(k, 0) + 1
    if counts != EXPECT_PRECINCTS:
        fail("the state assigns %s precincts per ward, expected %s — the city's precinct "
             "fabric has moved and this ward file must be re-checked against it"
             % (counts, EXPECT_PRECINCTS))
    agree = point_agreement(wm, pm, box)
    print("  city wards vs state precinct dissolve: %d/%d (%.3f%%) same ward, "
          "%d different, %d edge" % (agree["same"], agree["hit"], 100 * agree["frac"],
                                     agree["diff"], agree["only_a"] + agree["only_b"]))
    if agree["frac"] < MIN_PRECINCT_AGREEMENT:
        fail("the city's wards and the state's CURRENT precincts agree on only %.3f%% of "
             "points (floor %.1f%%) — the city file was last edited 2018-01-24 and this "
             "gate is the only thing standing between the app and a stale ward map"
             % (100 * agree["frac"], 100 * MIN_PRECINCT_AGREEMENT))

    # ---- population: balance, and a bounded (not asserted-zero) city delta ---
    print("fetching Census 2020 blocks…")
    blocks = fetch_blocks(box)
    place = esri(PLACE, {"where": "GEOID='%s'" % PLACE_GEOID, "outFields": "NAME,POP100"})
    place_pop = int(place[0]["properties"]["POP100"])
    if place_pop != GR_POP_2020:
        fail("TIGERweb now reports Grand Rapids's Census 2020 population as %d, not %d — "
             "re-read the record before moving this constant" % (place_pop, GR_POP_2020))
    pg = place[0]["geometry"]

    pops = {k: 0 for k, _ in wm}
    ward_not_place = place_not_ward = 0
    pop_ward_not_place = pop_place_not_ward = 0
    for x, y, pop in blocks:
        hit = None
        for k, g in wm:
            if in_geometry((x, y), g):
                hit = k
                break
        in_place = in_geometry((x, y), pg)
        if hit is not None:
            pops[hit] += pop
            if not in_place:
                ward_not_place += 1
                pop_ward_not_place += pop
        elif in_place:
            place_not_ward += 1
            pop_place_not_ward += pop

    total = sum(pops.values())
    ideal = total / float(len(pops))
    worst = max(abs(v - ideal) / ideal for v in pops.values())
    for k in sorted(pops):
        print("    Ward %s  %6d  %+6.2f%%" % (k, pops[k], 100 * (pops[k] - ideal) / ideal))
    print("  worst deviation %.2f%%" % (100 * worst))
    if worst > MAX_DEVIATION:
        fail("worst ward deviation %.2f%% exceeds the %.0f%% ceiling"
             % (100 * worst, 100 * MAX_DEVIATION))

    delta = total - place_pop
    edge = ward_not_place + place_not_ward
    print("  wards total %d against the city's %d (%+d); %d edge block(s) disagree "
          "(%d in wards not place, %d in place not wards)"
          % (total, place_pop, delta, edge, ward_not_place, place_not_ward))
    if abs(delta) > MAX_POP_DELTA_FRACTION * place_pop:
        fail("the wards' population differs from the city's by %+d (%.3f%%), past the "
             "%.1f%% tolerance — this is meant to be edge digitisation, not a hole"
             % (delta, 100.0 * abs(delta) / place_pop, 100 * MAX_POP_DELTA_FRACTION))
    if edge > MAX_EDGE_BLOCKS:
        fail("%d blocks fall on one side of the ward outline and the other side of the "
             "Census place outline (ceiling %d) — that is no longer an edge disagreement"
             % (edge, MAX_EDGE_BLOCKS))

    # ---- write, then the fleet's 2,000-point simplification protocol ---------
    src = {"type": "FeatureCollection",
           "features": [{"type": "Feature",
                         "properties": {"WARD": ward_of(f["properties"]),
                                        "Ward": ward_of(f["properties"])},
                         "geometry": f["geometry"]} for f in wards]}
    tmp = os.path.join(APP_DATA_DIR, ".gr-wards-src.json")
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(tmp, "w") as f:
        json.dump(src, f)
    subprocess.run(["npx", "-y", MAPSHAPER, tmp,
                    "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
                    "-o", "precision=" + PRECISION, "format=geojson", out_path],
                   check=True)
    os.remove(tmp)

    with open(out_path) as f:
        built = json.load(f)
    bm = model(built["features"])
    proto = point_agreement(model(src["features"]), bm, box, samples=2000, seed=2026)
    src_ov = overlaps(model(src["features"]), box)
    new_ov = overlaps(bm, box)
    if new_ov > src_ov:
        fail("simplification ADDED overlaps: %d vs %d in the source" % (new_ov, src_ov))
    if proto["frac"] < 0.995:
        fail("point-in-ward agreement only %.2f%% (need >= 99.5%%)" % (100 * proto["frac"]))
    print("  simplification: %d/%d (%.2f%%) agreement, %d source overlap(s), none added"
          % (proto["same"], proto["hit"], 100 * proto["frac"], src_ov))

    # The city's licence conditions use on carrying its disclaimer, so it rides
    # the file and the card renders it (the Des Moines pattern).
    # QUOTED FROM THE CITY'S OWN `licenseInfo`, not paraphrased. An earlier
    # version of this build composed its own sentence and the docstring called
    # it verbatim, which it was not — and a use agreement is exactly the text
    # that must not be reworded. These are the sentences of the City of Grand
    # Rapids Data Access and Use Constraint Agreement that describe the DATA,
    # in its words and order, down to the (\u201cCity\u201d) parenthetical the
    # first draft silently dropped. THE ONE ELISION IS MARKED. Two sentences
    # sit between the first and the rest — the agreement's acceptance clause,
    # addressed to whoever ACCESSES the data (this build) rather than to
    # whoever reads a card — and cutting them without saying so made a
    # four-sentence quotation out of a five-sentence passage. The ellipsis
    # says a cut happened; the full agreement (3,050 characters, including its
    # arbitration clause) is on the item and linked from the card's source row.
    #
    # The quotation is ASSERTED against the live licenceInfo below, so a
    # reworded agreement fails the build instead of shipping a quotation the
    # city no longer makes.
    built["disclaimer"] = (
        "The City of Grand Rapids (\u201cCity\u201d) provides data for use "
        "\u201cas is\u201d as a complementary service to its residents. \u2026 "
        "The areas depicted by this special "
        "database are approximate and may not be accurate to surveying or engineering "
        "standards. The special data shown here are for illustration purposes only and "
        "are not suitable for site specific decision making.")
    check_disclaimer_is_quoted(built["disclaimer"], license_info)
    with open(out_path, "w") as f:
        json.dump(built, f, separators=(",", ":"))
        f.write("\n")

    problems = check_shipped(out_path)
    if problems:
        fail("; ".join(problems))
    print("build-mi-grand-rapids-wards: wrote %s (3 wards, %d bytes)"
          % (out_path, os.path.getsize(out_path)))


if __name__ == "__main__":
    main()

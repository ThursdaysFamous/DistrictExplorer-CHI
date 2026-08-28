#!/usr/bin/env python3
"""
Build data/app/dsm-wards.json — the four City of Des Moines council wards,
read by ia/index.html's `dsm-ward` card.

Iowa Code 372.4(1)(b): a city governed on 1 July 1975 by the mayor-council
form with "two council members elected at large and one council member from
each of four wards" may continue in that form. Des Moines does, so its seven
elected seats are a mayor, two at-large members and these four wards. (The
city describes itself as council-manager, which 372.4(1) permits by ordinance
"without changing the form"; and 372.4(2) is explicit that the mayor is NOT a
member of the council.) FOUR WARDS ARE THE WHOLE CITY: they tile it, which is
why the layer's own geometry is its coverage test and no separate city outline
ships. It is MEASURED rather than assumed -- see check_tiles_the_city -- because
a city that annexes land its ward layer has not caught up with would leave a
reader in a real hole, and nothing else in this build would notice.

THE LICENCE, AND WHY "ALL RIGHTS RESERVED" IS NOT THE ANSWER HERE
------------------------------------------------------------------
The item (040390033d514f19b7b62c8a23f30c0d, owner City_Des_Moines, public)
carries licenseInfo beginning "(c) Copyright City of Des Moines, Iowa 2025.
All rights reserved." Read alone that is the Piatt County answer — an
assertion of rights with no grant, which this project treats as a block.

IT IS NOT THAT, AND THE CITY'S OWN TERMS PAGE IS WHY. data.dsm.city publishes
"Terms and Conditions of Use for City of Des Moines Data", whose Source Data
clause reads, in full:

    Applications using data or services supplied by the City of Des Moines
    Data Portal must include the following disclaimer: "(c) Copyright City of
    Des Moines, Iowa. All rights reserved. There is no guarantee or warranty
    concerning the accuracy of the data and the City assumes no liability for
    its accuracy. The data is subject to change as modifications and updates
    are completed. It is understood that the information contained in the site
    is being used at one's own risk".

So the city CONTEMPLATES applications using this data and states one condition
for doing so: reproduce that disclaimer. The "All rights reserved" string in
licenseInfo is the text OF the required notice, not a refusal of use. The
disclaimer ships verbatim in DISCLAIMER below, on the layer's sources-page row
and on the card itself.

**READ THE PORTAL'S TERMS PAGE BEFORE WRITING A PUBLISHER OFF.** An item's
licenseInfo is where the licence lives, but it is not always where the GRANT
lives, and a copyright notice quoted as a required attribution reads exactly
like a copyright notice asserted as a prohibition.

The same terms carry a Right to Discontinue Feeds clause. Nothing here fetches
the city at runtime — this file is pre-built and same-origin — but that clause
is the reason ia/WATCH.md watches the service rather than assuming it persists.

THE CITY'S OWN WARDS 1 AND 2 OVERLAP, BY 9.3 ACRES, AND IT IS A SLIVER
------------------------------------------------------------------------
The agreement gate failed this layer at every simplification level tried, and
the reason was not simplification: the RAW, unsimplified source overlaps
itself. Wards 1 and 2 share 37,599 m2 -- 9.29 acres, 0.016% of a 90.66 square
mile city -- and its shape settles what it is. One part carries 37,561 m2 of
that with a 5,278 m perimeter over a 1,958 x 1,235 m extent: a Polsby-Popper
compactness of 0.0169 and a mean width of about 14 metres. That is a ribbon
running roughly 2.6 km along the two wards' shared edge, which is two
independently drawn polygons whose common boundary does not coincide to the
metre -- the same digitisation artifact the Illinois instance measured between
Richland County's precinct and district layers. It is not a disagreement about
which ward a place belongs to; there is no compact blob anywhere.

The city's own arithmetic agrees: its City Boundary layer gives Des Moines
90.66 square miles and these four wards' own SqMiles sum to 90.67, a 0.01
excess of the same order as the sliver.

SO THE GATE MEASURES THE SOURCE'S OVERLAP RATHER THAN FAILING ON IT, and
refuses only if simplification ADDS overlap or if the source's own rises past
SOURCE_OVERLAP_CEILING. A gate that fails on a defect present identically in
the input is not testing the build; it is testing the publisher, and it stops
the build without recording anything. What is recorded is the measurement.

NO ROSTER RIDES THIS BOUNDARY, AND THE LAYER OFFERS ONE
--------------------------------------------------------
The source carries PersonFName / PersonMName / PersonLName / EMail in band,
and every one of the four is correct today. It is still not read as the
roster, for the Coles County reason: a roster attached to a boundary is
refreshed when the boundary is, and this one demonstrably is not refreshed on
one schedule — Ward 2's feature was last edited 2024-02-16 while wards 1, 3
and 4 were edited 2025-12-29..31 (the November 2025 election cycle). It is
also THINNER than the city's own council page, which publishes a phone, a
term and an election date the layer has no field for, and PersonTitle is null
on all four.

So the geometry comes from here and the people come from the city's council
page (dsm_council_scraper.py). These in-band names are used ONCE, at build
time, as a WITNESS: build_dsm_council.py refuses to write a roster whose four
ward members disagree with them. Two publishers inside one city, each doing
what it maintains.

Usage:
    python3 ia/scripts/build_dsm_wards.py
    python3 ia/scripts/build_dsm_wards.py --check
"""

import datetime
import json
import math
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "dsm-wards.json"
MAPSHAPER = "mapshaper@0.6.102"

SOURCE = ("https://services.arcgis.com/HT7H9QGiZQoRJDpJ/arcgis/rest/services/"
          "Wards_view/FeatureServer/0")
ITEM_ID = "040390033d514f19b7b62c8a23f30c0d"
ITEM_URL = "https://www.arcgis.com/home/item.html?id=" + ITEM_ID
TERMS_URL = "https://data.dsm.city/pages/terms"

# Required verbatim by the city's own terms of use (see the docstring). Shipped
# on the card and on the sources page; do not paraphrase or shorten it.
DISCLAIMER = ("© Copyright City of Des Moines, Iowa. All rights reserved. There is "
              "no guarantee or warranty concerning the accuracy of the data and the "
              "City assumes no liability for its accuracy. The data is subject to "
              "change as modifications and updates are completed. It is understood "
              "that the information contained in the site is being used at one's own "
              "risk.")

EXPECT_WARDS = [1, 2, 3, 4]
EXPECT_CITY = "Des Moines"

SIMPLIFY = "20%"
PRECISION = "0.000001"
VALIDATION_KEY = "ward"

# The share of in-city sample points the SOURCE itself places in two wards at
# once. Measured 2026-08-28 at 8 in 40,000 over the city envelope (0.02%); the
# ceiling is two orders of magnitude above that, so a genuine double-assignment
# of a neighbourhood fails here while the known 14-metre sliver does not.
SOURCE_OVERLAP_CEILING = 0.02   # fraction of samples, i.e. 2%

# The tiling gate. Erasing the four wards from the city's own boundary should
# leave nothing but the seam between two independently digitised outlines.
# Measured 2026-08-28: 16,363 m2 in 753 fragments, the largest 3,482 m2 --
# 4.04 acres, 0.0070% of a 90.66 square mile city, mean fragment 22 m2. That
# shape is a perimeter artifact; a genuine hole (an annexation the ward layer
# has not caught up with) is ONE LARGE COMPACT PART, which is why the largest
# single fragment is capped as well as the total.
CITY_LAYER = ("https://services.arcgis.com/HT7H9QGiZQoRJDpJ/arcgis/rest/services/"
              "City_Boundary_view/FeatureServer/0")
CITY_NAME = "Des Moines"
UNCOVERED_CEILING_SQMI = 0.45
UNCOVERED_LARGEST_CEILING_M2 = 60000.0


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True,
    ).stdout


def fetch_source():
    url = ("%s/query?where=1%%3D1&outFields=WardNbr,City,SqMiles,last_edited_date"
           "&returnGeometry=true&outSR=4326&f=geojson" % SOURCE)
    page = json.loads(_curl(url))
    feats = page.get("features", [])
    got = sorted(int(f["properties"]["WardNbr"]) for f in feats)
    if got != EXPECT_WARDS:
        raise RuntimeError(
            "the city's Wards layer returned wards %s, expected %s. Des Moines's "
            "four-ward council is Iowa Code 372.4(1)(b) grandfathered form; a "
            "different count is the city changing its form of government, which "
            "needs reading before it ships" % (got, EXPECT_WARDS))
    for f in feats:
        city = f["properties"].get("City")
        if city != EXPECT_CITY:
            raise RuntimeError("a ward feature carries City=%r, expected %r"
                               % (city, EXPECT_CITY))
    return feats


def build_properties(feats):
    """PROPERTY NAMES ARE ALL LOWERCASE ON PURPOSE: findPropCI lowercases the
    feature's key but NOT the candidate string, so a camelCase property never
    matches and its card row silently does not render."""
    out = []
    for f in sorted(feats, key=lambda f: int(f["properties"]["WardNbr"])):
        p = f["properties"]
        ward = int(p["WardNbr"])
        props = {
            "ward": ward,
            "label": "Ward %d" % ward,
            "city": p["City"],
        }
        if p.get("SqMiles") is not None:
            props["sqmiles"] = round(float(p["SqMiles"]), 2)
        out.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
    return out


def report_vintage(feats):
    """Print each ward's own last-edited date rather than pinning one.

    These are DELIBERATELY uneven and that is not staleness: wards 1, 3 and 4
    were edited across 2025-12-29..31 for the November 2025 election cycle
    while ward 2, whose member was not on that ballot, still carries its
    2024-02-16 edit. A single pinned vintage would fail on every ordinary
    election; the dates are printed so an operator reads them.
    """
    for f in sorted(feats, key=lambda f: int(f["properties"]["WardNbr"])):
        p = f["properties"]
        ms = p.get("last_edited_date")
        when = (datetime.datetime.utcfromtimestamp(ms / 1000).date().isoformat()
                if ms else "unknown")
        print("  ward %d last edited %s" % (int(p["WardNbr"]), when), file=sys.stderr)


def _area_m2(rings, lat0=41.6):
    """Equirectangular ring area, adequate for measuring seams inside one city."""
    mx = 111320.0 * math.cos(math.radians(lat0))
    my = 110540.0

    def one(r):
        s = 0.0
        for i in range(len(r) - 1):
            s += (r[i][0] * mx) * (r[i + 1][1] * my) - (r[i + 1][0] * mx) * (r[i][1] * my)
        return abs(s) / 2.0
    return one(rings[0]) - sum(one(h) for h in rings[1:])


def check_tiles_the_city(ward_features):
    """Refuse if the four wards leave real city ground unrepresented.

    Fetches the city's OWN boundary layer and erases the wards from it. What
    survives should be the seam between two independently drawn outlines --
    many tiny fragments along the perimeter. One big compact part instead is a
    hole, and a reader standing in it would be told nothing at all rather than
    which ward they are in, which is the failure this gate exists for.
    """
    url = ("%s/query?where=Name%%3D%%27%s%%27&outFields=Name,SqMiles&returnGeometry=true"
           "&outSR=4326&f=geojson" % (CITY_LAYER, CITY_NAME.replace(" ", "%20")))
    city = json.loads(_curl(url))
    feats = city.get("features", [])
    if not feats:
        raise RuntimeError("the city's own City_Boundary layer returned no %r feature, "
                           "so the tiling gate cannot run" % CITY_NAME)
    city_sqmi = sum(float(f["properties"].get("SqMiles") or 0) for f in feats)

    with tempfile.TemporaryDirectory() as tmp:
        cpath = os.path.join(tmp, "city.json")
        wpath = os.path.join(tmp, "wards.json")
        upath = os.path.join(tmp, "union.json")
        gpath = os.path.join(tmp, "gap.json")
        with open(cpath, "w") as f:
            json.dump(city, f)
        with open(wpath, "w") as f:
            json.dump({"type": "FeatureCollection", "features": ward_features}, f)
        subprocess.run(["npx", "-y", MAPSHAPER, wpath, "-dissolve",
                        "-o", upath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["npx", "-y", MAPSHAPER, cpath, "-erase", upath,
                        "-o", gpath, "format=geojson"],
                       check=True, cwd=REPO_ROOT, capture_output=True)
        with open(gpath) as f:
            gap = json.load(f)

    parts = []
    for f in gap.get("features", []):
        g = f.get("geometry") or {}
        if not g:
            continue
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for rings in polys:
            if rings:
                parts.append(_area_m2(rings))
    total_m2 = sum(parts)
    total_sqmi = total_m2 / 2.58999e6
    largest = max(parts) if parts else 0.0

    if total_sqmi > UNCOVERED_CEILING_SQMI or largest > UNCOVERED_LARGEST_CEILING_M2:
        raise RuntimeError(
            "the four wards leave %.4f sq mi of the city uncovered in %d parts, the "
            "largest %.0f m2 (ceilings %.2f sq mi / %.0f m2). Many tiny perimeter "
            "fragments are two outlines digitised apart; one large part is a HOLE -- "
            "look at where it is before shipping a layer that answers nothing there."
            % (total_sqmi, len(parts), largest, UNCOVERED_CEILING_SQMI,
               UNCOVERED_LARGEST_CEILING_M2))
    print("  tiling gate: the 4 wards cover the city's %.2f sq mi to within %.4f sq mi "
          "(%.4f%%) in %d fragments, largest %.0f m2"
          % (city_sqmi, total_sqmi, 100.0 * total_sqmi / max(city_sqmi, 1e-9),
             len(parts), largest), file=sys.stderr)


def run_mapshaper(source_path, out_path):
    subprocess.run(
        ["npx", "-y", MAPSHAPER, source_path,
         "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
         "-o", "precision=" + PRECISION, "format=geojson", out_path],
        check=True, cwd=REPO_ROOT,
    )


# --- point-in-polygon (fleet-standard copy, mirrors index.html's even-odd test) ---
def _point_in_ring(pt, ring):
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-16) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_polygon(pt, rings):
    if not rings or not _point_in_ring(pt, rings[0]):
        return False
    return not any(_point_in_ring(pt, h) for h in rings[1:])


def _point_in_geometry(pt, geom):
    if not geom:
        return False
    if geom["type"] == "Polygon":
        return _point_in_polygon(pt, geom["coordinates"])
    if geom["type"] == "MultiPolygon":
        return any(_point_in_polygon(pt, poly) for poly in geom["coordinates"])
    return False


def _bbox(geom):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for part in c:
                walk(part)
    walk(geom["coordinates"])
    return min(xs), min(ys), max(xs), max(ys)


def _model(features):
    return [(f["properties"][VALIDATION_KEY], _bbox(f["geometry"]), f["geometry"])
            for f in features]


def _hits(model, pt):
    x, y = pt
    out = []
    for key, (x0, y0, x1, y1), geom in model:
        if x0 <= x <= x1 and y0 <= y <= y1 and _point_in_geometry(pt, geom):
            out.append(key)
    return out


def validate(source_features, result_features, samples=4000, seed=2024):
    """Sample the WARDS' OWN envelope, not the state's.

    The fleet's other geometry builders sample the whole of Iowa because their
    layers cover it. This one covers 91 square miles: over a state envelope
    virtually every sample would land outside all four wards, both models would
    answer "none", and a 99.5% gate would pass on a layer simplified into
    nothing. Sampling the city's own bounding box makes roughly half the points
    land inside a ward, which is what actually exercises the boundaries.
    """
    src, new = _model(source_features), _model(result_features)
    xs = [b for _, bb, _ in src for b in (bb[0], bb[2])]
    ys = [b for _, bb, _ in src for b in (bb[1], bb[3])]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    rng = random.Random(seed)
    agree = new_over = src_over = inside = 0
    for _ in range(samples):
        pt = (rng.uniform(lo_x, hi_x), rng.uniform(lo_y, hi_y))
        s_hits, o_hits = _hits(new, pt), _hits(src, pt)
        if len(s_hits) > 1:
            new_over += 1
        if len(o_hits) > 1:
            src_over += 1
        if o_hits:
            inside += 1
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        o = o_hits[0] if len(o_hits) == 1 else (None if not o_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    # The source's own sliver is measured and reported; only NEW overlap is a
    # build defect. See the docstring for what that sliver is.
    if new_over > src_over:
        return False, ("simplification ADDED overlap: %d/%d points fall in >1 ward "
                       "against the source's own %d" % (new_over, samples, src_over))
    if src_over > samples * SOURCE_OVERLAP_CEILING:
        return False, ("the source now places %d/%d points in two wards at once "
                       "(ceiling %.0f). The known artifact is a ~14 m sliver along "
                       "the ward 1/2 edge; this is larger, so measure its SHAPE "
                       "before raising anything"
                       % (src_over, samples, samples * SOURCE_OVERLAP_CEILING))
    if inside < samples * 0.25:
        return False, ("only %d/%d sample points fell inside any ward — the envelope "
                       "is not exercising the boundaries" % (inside, samples))
    if pct < 99.5:
        return False, "point-in-ward agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, ("%d/%d (%.2f%%) agreement over the city envelope, %d inside a ward; "
                  "overlap %d in the source and %d after simplifying"
                  % (agree, samples, pct, inside, src_over, new_over))


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    raw = fetch_source()
    print("fetched %d wards from the City of Des Moines" % len(raw), file=sys.stderr)
    report_vintage(raw)
    built = build_properties(raw)
    check_tiles_the_city(built)

    src_geo = {"type": "FeatureCollection", "features": built}
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.json")
        out_tmp = os.path.join(tmp, "out.json")
        with open(src_path, "w") as f:
            json.dump(src_geo, f)
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            result = json.load(f)

    n = len(result.get("features", []))
    if n != len(built):
        raise RuntimeError("mapshaper returned %d features, expected %d" % (n, len(built)))
    ok, msg = validate(built, result["features"])
    if not ok:
        raise RuntimeError("simplification changed the answer: " + msg)
    print("  agreement gate: %s" % msg, file=sys.stderr)

    # The required notice travels WITH the data, not only in a doc a reader of
    # this file might not open.
    result["disclaimer"] = DISCLAIMER
    result["sourceUrl"] = ITEM_URL
    result["termsUrl"] = TERMS_URL

    payload = json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n"
    if check_only:
        try:
            with open(out_path) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("%s is missing (%s) — run without --check" % (OUT_NAME, e))
        if shipped != payload:
            raise RuntimeError("%s has drifted from the source. Re-run this builder."
                               % OUT_NAME)
        print("check: shipped layer matches the source", file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/app/%s — %d wards, %.1f KB (simplify %s)"
          % (OUT_NAME, n, len(payload) / 1024.0, SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

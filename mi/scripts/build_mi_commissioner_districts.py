#!/usr/bin/env python3
"""
Build Michigan's statewide county-commissioner-district file in data/app/ from
the Bureau of Elections' own layer — the flagship this instance was stood up
for.

WHY THIS LAYER EXISTS AND WHY MICHIGAN WAS CHOSEN. Michigan is the rare state
that publishes every county's board districts in ONE place: the county
apportionment commissions file their adopted plans under MCL 46.401-46.405 and
the Department of State's Bureau of Elections compiles them. That is Wisconsin's
LTSB shape (a statutory filing mandate producing a single current statewide
aggregate) rather than Illinois's county-by-county grind, and it is why this
instance exists at all. 619 districts, all 83 counties, one query.

    https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/boundaries/MapServer/10

LICENCE, verbatim from the AGO item (4c8d0d854ac04d8787cb3cf6dab7fbec): "This
dataset is a public record and ... there are no restrictions on the use,
reproduction, or distribution of this dataset." No attribution is REQUIRED; the
card credits the Bureau of Elections anyway, per this project's practice. Two
terms survive redistribution and are recorded rather than smoothed: an
indemnification clause, and a carve-out excluding the state's own maps and
logos from the grant (so the geometry travels, the state's marks never do). The
publisher also "reserves the right to modify or remove this dataset ... without
notice", which is an argument for shipping a built file rather than fetching
live — which is what this script produces. NOTE the Hub SITE item carries a
separate CC-BY-SA; that is the site application, NOT this dataset, and the
share-alike half is not inherited. Do not conflate the two items.

*** THIS SCRIPT DELIBERATELY DISCARDS THE Commissioner AND Party FIELDS. ***

The source carries an officeholder name and party on every one of the 619
polygons, which looks like a free roster and is a trap. MEASURED 2026-09-03,
across 12 counties read district-by-district against each county's own board
page, plus ~40 more counties in an adversarial second pass:

  * The column is NOT a roster of officeholders. It is a list of CERTIFIED
    NOVEMBER 2024 ELECTION WINNERS -- the item's own description says so. That
    single fact explains its 100% fill rate: every district always has a
    winner, so a winners list is complete by construction and can never be
    blank. The absence of blanks is evidence AGAINST maintenance, not for it.
  * 115 of 123 sampled districts named the right person (93.5%) and that number
    is the trap: every one of the eight misses runs the SAME direction, the
    layer naming the 2024 winner and the county naming their replacement. Not
    one runs the other way. The right answers are right by inertia, not upkeep.
  * Wayne County District 5 still names IRMA CLARK-COLEMAN, who died on
    10 June 2025. Shipping this column would print a dead woman's name to a
    reader as their current commissioner, fifteen months on.
  * Four further rows misspell a real person's surname (Markam/Markham,
    Wuerful/Wuerfel, Richarc/Richard, Sealberg/Seaberg), so even rows naming
    the right human cannot be rendered verbatim.

So the names are dropped HERE, at the build, rather than being carried into
data/app/ and left for a later card to pick up by accident. This instance's
rule, and the fleet's: a roster attached to a boundary is refreshed when the
BOUNDARY is, and this boundary has not moved since the 2021 apportionment. The
honest route to Michigan commissioner NAMES is each county's own board page,
which is a separate build with its own weekly refresh; until it exists the gap
is recorded in the guidebook and stated on the card.

WHAT DOES SHIP: the district's identity (county, number, code) and its
apportionment POPULATION, which is a property of the plan rather than of any
person and is what the county was districted on. 611 of 619 carry it; the 8
that do not are Baraga District 1 and all seven Cheboygan districts, and the
card simply omits the row for them.

VINTAGE. The layer is "2021 County Commissioner Districts" (adoption year); the
state's own viewer labels it 2022 (first election held under it) and the
underlying feature class is CCD_2022_Edit. Three names, ONE layer -- do not
chase the discrepancy as evidence of a successor. There is none: an exhaustive
enumeration of all 294 michigan_admin AGO items found exactly one
commissioner-district item, and the state's current Election District Viewer
(touched 2026-07-31) still wires this exact endpoint. Michigan counties
reapportion on the decennial census (MCL 46.404), so the next plan is ~2031.

Prerequisites: curl (works through an HTTPS proxy) and Node.js (mapshaper).

Usage:
    python3 mi/scripts/build_mi_commissioner_districts.py
    python3 mi/scripts/build_mi_commissioner_districts.py --check
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile

INSTANCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
MAPSHAPER = "mapshaper@0.6.102"  # pinned for reproducible output (fleet convention)

SERVICE = ("https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/"
           "boundaries/MapServer/10")

OUT_FILE = "mi-commissioner-districts.json"
SIMPLIFY = "12%"
PRECISION = "0.000001"  # 6 decimals ~= 0.11 m

# Exact counts, not floors. The source is a single statutory compilation with a
# known shape, so anything else is a source change that wants a human.
EXPECT_FEATURES = 619
EXPECT_COUNTIES = 83

# Fields kept. Commissioner and Party are deliberately absent -- see the module
# docstring; this tuple is the enforcement, and dropping the guard below would
# put a dead woman's name back into data/app/.
KEEP_FIELDS = ("CountyFIPS", "County", "DistrictCode", "DistrictName", "Population")
# Derived, not fetched: the bare district number. The source only offers
# DistrictName ("District 9"), and a card row labelled "District" carrying
# "District 9" reads "District: District 9" — so the number is emitted
# separately for the card's headline and the hover label, both of which read
# this same property (the factory ties them together on purpose).
DERIVED_FIELDS = ("District",)
BANNED_FIELDS = ("Commissioner", "Party")

VALIDATION_KEY = "DistrictCode"  # unique per district statewide (619/619)

# Michigan's envelope, from the shipped county fabric.
STATE_BBOX = {"minLng": -90.42, "minLat": 41.69, "maxLng": -82.12, "maxLat": 48.31}


def fetch():
    """Every commissioner district as GeoJSON. Uses curl so it works through an
    HTTPS proxy (as in the Claude Code sandbox)."""
    url = (SERVICE + "/query?where=1%3D1"
           "&outFields=" + ",".join(KEEP_FIELDS + BANNED_FIELDS) +
           "&outSR=4326&geometryPrecision=6&f=geojson")
    out = subprocess.run(["curl", "-sS", "--fail", "--max-time", "600", url],
                         check=True, capture_output=True).stdout
    geo = json.loads(out)
    feats = geo.get("features") or []
    if not feats:
        raise RuntimeError(
            "the commissioner-district service returned no features -- if the body is a "
            "JSON error envelope the field list changed; if it is empty the layer moved")
    if geo.get("exceededTransferLimit"):
        raise RuntimeError("hit the service's 1000-record transfer cap -- needs paging")
    return geo


def strip_people(geo):
    """Drop the stale in-band roster, and prove it is gone.

    The measurement behind this is in the module docstring. The assertion is
    here rather than in a comment because a future 'why not just keep the extra
    fields' would otherwise be a one-line change with a fifteen-month-old
    factual error as its consequence.
    """
    for feat in geo["features"]:
        props = feat.get("properties") or {}
        kept = {k: props.get(k) for k in KEEP_FIELDS if props.get(k) is not None}
        kept["District"] = district_number(props)
        feat["properties"] = kept
    leaked = sorted({k for f in geo["features"] for k in f["properties"]}
                    - set(KEEP_FIELDS) - set(DERIVED_FIELDS))
    if leaked:
        raise RuntimeError("unexpected field(s) survived the strip: %s" % leaked)
    return geo


def district_number(props):
    """The number out of "District 7". The source is uniform (all 619 match), so
    anything else is a source change worth failing on."""
    name = str(props.get("DistrictName") or "")
    if not name.startswith("District "):
        raise RuntimeError("DistrictName %r is not 'District <n>' -- the source's own "
                           "naming changed" % name)
    return int(name.split(" ", 1)[1])


def check_shape(feats):
    """Counts, per-county numbering, and key uniqueness — before any geometry work."""
    problems = []
    if len(feats) != EXPECT_FEATURES:
        problems.append("%d features, expected exactly %d" % (len(feats), EXPECT_FEATURES))

    by_county = {}
    for f in feats:
        p = f["properties"]
        by_county.setdefault(p["CountyFIPS"], []).append(district_number(p))
    if len(by_county) != EXPECT_COUNTIES:
        problems.append("%d counties, expected exactly %d" % (len(by_county), EXPECT_COUNTIES))

    # Every board runs 1..N. A gap or a repeat means the compilation changed and
    # the card's "District n of N" would start lying.
    for fips, nums in sorted(by_county.items()):
        if sorted(nums) != list(range(1, len(nums) + 1)):
            problems.append("county %s numbers its districts %s, not 1..%d"
                            % (fips, sorted(nums), len(nums)))
        # MCL 46.401(1): not fewer than 5, not more than 21.
        if not 5 <= len(nums) <= 21:
            problems.append("county %s has %d districts, outside MCL 46.401(1)'s 5..21"
                            % (fips, len(nums)))

    keys = [f["properties"][VALIDATION_KEY] for f in feats]
    if len(set(keys)) != len(keys):
        problems.append("%s is not unique across the state" % VALIDATION_KEY)
    return problems


def run_mapshaper(src, out):
    subprocess.run(["npx", "-y", MAPSHAPER, src,
                    "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
                    "-o", "precision=" + PRECISION, "format=geojson", out],
                   check=True, cwd=INSTANCE_ROOT)


# --- point-in-polygon mirroring index.html's even-odd test -------------------
def _point_in_ring(pt, ring):
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_geometry(pt, geom):
    if geom["type"] == "Polygon":
        inside = False
        for ring in geom["coordinates"]:
            if _point_in_ring(pt, ring):
                inside = not inside
        return inside
    if geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            inside = False
            for ring in poly:
                if _point_in_ring(pt, ring):
                    inside = not inside
            if inside:
                return True
    return False


def _bbox(geom):
    b = [1e9, 1e9, -1e9, -1e9]

    def walk(c):
        if c and isinstance(c[0], (int, float)):
            b[0], b[1] = min(b[0], c[0]), min(b[1], c[1])
            b[2], b[3] = max(b[2], c[0]), max(b[3], c[1])
        else:
            for x in c:
                walk(x)

    walk(geom["coordinates"])
    return b


def _model(features):
    return [(f["properties"][VALIDATION_KEY], f["geometry"], _bbox(f["geometry"]))
            for f in features]


def _hits(model, pt):
    return [k for k, geom, bb in model
            if bb[0] <= pt[0] <= bb[2] and bb[1] <= pt[1] <= bb[3]
            and _point_in_geometry(pt, geom)]


def validate(source_features, result_features, samples=2000, seed=2026):
    """Refuse the build unless simplification preserves which district a point
    is in, against the full-precision fetch — the fleet's 2,000-point protocol.

    OVERLAPS ARE COMPARED, NOT ASSERTED AT ZERO. The source itself has a handful
    of self-overlaps (measured), and the Wisconsin dissolves set the precedent
    of tolerating what the publisher shipped while refusing to ADD any. So the
    gate is: simplification may not increase the overlap count.
    """
    src, new = _model(source_features), _model(result_features)
    rng = random.Random(seed)
    agree = src_overlaps = new_overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        s_hits, o_hits = _hits(new, pt), _hits(src, pt)
        if len(s_hits) > 1:
            new_overlaps += 1
        if len(o_hits) > 1:
            src_overlaps += 1
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        o = o_hits[0] if len(o_hits) == 1 else (None if not o_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    if new_overlaps > src_overlaps:
        return False, ("simplification ADDED overlaps: %d in the result vs %d in the source"
                       % (new_overlaps, src_overlaps))
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, ("%d/%d (%.2f%%) agreement over the state envelope, %d overlap(s) "
                  "inherited from the source and none added" % (agree, samples, pct, src_overlaps))


def check_shipped(path):
    with open(path) as f:
        shipped = json.load(f)
    feats = shipped.get("features") or []
    problems = check_shape(feats)
    if feats and "District" not in (feats[0].get("properties") or {}):
        problems.append("the shipped file carries no bare District number — the card's headline "
                        "and the hover label both read it")
    banned = sorted({k for f in feats for k in (f.get("properties") or {})} & set(BANNED_FIELDS))
    if banned:
        problems.append(
            "the shipped file carries %s -- this layer's officeholder column is a "
            "stale list of November 2024 election winners (it names a commissioner who "
            "died in June 2025) and must never reach data/app/. See the module docstring."
            % banned)
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--check", action="store_true",
                    help="validate the shipped file offline instead of rebuilding")
    args = ap.parse_args()
    out_path = os.path.join(APP_DATA_DIR, OUT_FILE)

    if args.check:
        problems = check_shipped(out_path)
        for p in problems:
            print("FAIL: %s" % p, file=sys.stderr)
        if problems:
            sys.exit(1)
        with open(out_path) as f:
            n = len(json.load(f)["features"])
        print("mi-commissioner-districts: OK — %d districts across %d counties, numbering "
              "clean, no officeholder columns" % (n, EXPECT_COUNTIES), file=sys.stderr)
        return

    source = strip_people(fetch())
    problems = check_shape(source["features"])
    if problems:
        for p in problems:
            print("FATAL: %s" % p, file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "cc-src.geojson")
        with open(src_path, "w") as f:
            json.dump(source, f)
        out_tmp = os.path.join(tmp, "cc.geojson")
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            simplified = json.load(f)

    problems = check_shape(simplified["features"])
    if problems:
        for p in problems:
            print("FATAL after simplify: %s" % p, file=sys.stderr)
        sys.exit(1)

    ok, msg = validate(source["features"], simplified["features"])
    if not ok:
        raise RuntimeError("validation failed: %s" % msg)

    compact = json.dumps(simplified, separators=(",", ":"))
    if json.loads(compact) != simplified:
        raise RuntimeError("round-trip mismatch before writing")

    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(compact)

    with_pop = sum(1 for f in simplified["features"] if f["properties"].get("Population"))
    print("mi-commissioner-districts -> data/app/%s: %d districts across %d counties; %s; "
          "%d carry a population; %d bytes (%s retain, 6dp); officeholder columns dropped"
          % (OUT_FILE, len(simplified["features"]), EXPECT_COUNTIES, msg, with_pop,
             len(compact), SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

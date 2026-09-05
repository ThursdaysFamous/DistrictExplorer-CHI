#!/usr/bin/env python3
"""Build mi/data/app/mi-detroit-council-districts.json — Detroit's seven City
Council districts, from the city's own ArcGIS org.

THE CITY PUBLISHES THREE COUNCIL-DISTRICT SERVICES AND THE NAMES DO NOT SETTLE
WHICH IS IN FORCE. `Council_Districts` is titled "Current Detroit City Council
Districts" and has existed since 2016; `city_council_districts_2013` was
CREATED in December 2025; `city_council_districts_2026` was created in February
2025. Read as names alone, at least two readings are defensible. Measured
2026-09-05, four of the city's own publications agree on one answer:

  * "Current" carries geometry IDENTICAL to the 2026 service, district for
    district, and DIFFERENT from the 2013 one. The city updated its canonical
    service in place on 2026-01-06, when the council elected in November 2025
    was seated.
  * The 2013 service was created in December 2025 — you archive the OLD plan.
  * The org also publishes "2026 to 2013 Council District Crosswalk for
    Parcels", which only makes sense in one direction.
  * AND THE POPULATION SETTLES IT INDEPENDENTLY OF EVERY NAME AND DATE. A plan
    drawn to a census balances on that census. Against Census 2020 blocks the
    2026 plan runs 87,393-94,820 against a 91,302 ideal (worst 4.28%); the 2013
    plan runs 78,966-100,623 (worst 13.51%), which is what a plan drawn on 2010
    looks like ten years later.

That last one is the gate, and it is enforced in BOTH DIRECTIONS: the build
refuses if the shipped plan is out of balance, AND it refuses if the archived
plan ever comes into balance too, because then the test has stopped
discriminating and a human should look. This is the Vermilion rule — currency
is a measurement, not a reading of a name.

THE SEVEN DISTRICTS SUM TO 639,111, WHICH IS DETROIT'S CENSUS 2020 POPULATION
EXACTLY. That is the tiling proof: no block double-counted, none missed. It is
asserted, not merely reported.

NO ROSTER SHIPS, AND THAT IS MEASURED RATHER THAN SKIPPED. Every route to
Detroit's council membership available to this client is shut:

  detroitmi.gov            Cloudflare managed challenge — 403 on /robots.txt
                           itself, so even the policy cannot be read. This
                           project does not defeat a challenge.
  data.detroitmi.gov       the same challenge.
  mvic.sos.state.mi.us     403, challenged.
  the city's ArcGIS org    225 items; district geometry and a parcel
                           crosswalk, and no roster of any kind.
  Legistar OfficeRecords   maintained to 2017-12-31 and abandoned since. Its
                           OfficeRecordTitle reads "Council Member" with NO
                           district even while it was maintained — so it could
                           not place a member on a district card even if it
                           were current. Milwaukee's Legistar carries "3rd
                           District" in that same field: TEST A VENDOR BY
                           CONTENT, PER CITY, never by the vendor's name.
  Legistar Persons         45 records, PersonActiveFlag=1 on ALL of them,
                           including five system accounts ("Legistar System",
                           "Granicus User", "View Only", "System
                           Administrator", "Daystar") and members who left
                           office in 2013. A scraper trusting that flag ships
                           "Legistar System" as a council member.

So the card names the district and says plainly that it names nobody, with the
reason. The gap is recorded in coverage-gaps.json; the ask is drafted and HELD.

    python3 mi/scripts/build_mi_detroit_council.py           # rebuild
    python3 mi/scripts/build_mi_detroit_council.py --check   # offline gate
"""

import argparse
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTANCE_ROOT = os.path.dirname(HERE)
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
MAPSHAPER = "mapshaper@0.6.25"

ORG = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services"
SERVICE = ORG + "/city_council_districts_2026/FeatureServer/0"
# The city's canonical service. Must AGREE with what ships.
WITNESS_CURRENT = ORG + "/Council_Districts/FeatureServer/0"
# The archived plan. Must DISAGREE with what ships — if it matches, the wrong
# service was fetched.
WITNESS_ARCHIVE = ORG + "/city_council_districts_2013/FeatureServer/0"

BLOCKS = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
          "tigerWMS_Census2020/MapServer/10/query")

OUT_FILE = "mi-detroit-council-districts.json"
SIMPLIFY = "8%"
PRECISION = "0.000001"

EXPECT_FEATURES = 7
EXPECT_DISTRICTS = tuple(str(n) for n in range(1, 8))
# Detroit's Census 2020 population. The seven districts must sum to it exactly.
DETROIT_POP_2020 = 639111
# The shipped plan must balance; the archived one must not. Both are gates.
MAX_DEVIATION = 0.06          # measured 0.0428 on the 2026 plan
MIN_ARCHIVE_DEVIATION = 0.09  # measured 0.1351 on the 2013 plan

KEEP_FIELDS = ("district_number", "district_name")
DERIVED_FIELDS = ("District",)

DETROIT_BBOX = {"minLng": -83.2877, "minLat": 42.2550,
                "maxLng": -82.9103, "maxLat": 42.4504}


def fetch_geojson(service, fields="*"):
    url = (service + "/query?where=1%3D1&outFields=" + fields +
           "&outSR=4326&geometryPrecision=6&f=geojson")
    out = subprocess.run(["curl", "-sS", "--fail", "--max-time", "300", url],
                         check=True, capture_output=True).stdout
    geo = json.loads(out)
    feats = geo.get("features") or []
    if not feats:
        raise RuntimeError(
            "%s returned no features — an Esri error envelope arrives as HTTP 200, "
            "so read this as 'the field list or the service moved', not an outage"
            % service)
    if geo.get("exceededTransferLimit"):
        raise RuntimeError("%s hit its transfer cap — needs paging" % service)
    return geo


def district_of(props):
    for k in ("district_number", "DistrictNu", "council_district"):
        if props.get(k) not in (None, ""):
            return str(props[k]).strip()
    return None


# --- point-in-polygon, mirroring index.html's even-odd test -------------------
def _point_in_ring(pt, ring):
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


def _point_in_geometry(pt, geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if not poly or not _point_in_ring(pt, poly[0]):
            continue
        if any(_point_in_ring(pt, hole) for hole in poly[1:]):
            continue
        return True
    return False


def _model(features):
    out = []
    for f in features:
        g = f.get("geometry")
        if not g:
            continue
        out.append((district_of(f.get("properties") or {}), g))
    return out


def _hits(model, pt):
    return [k for k, g in model if _point_in_geometry(pt, g)]


def fetch_blocks():
    """Census 2020 blocks over Detroit's envelope, with POP100 and the INTERIOR
    point. INTPT, never CENT: the interior point is guaranteed inside its own
    block, while a centroid can fall outside a non-convex one."""
    env = "%2C".join("%.5f" % DETROIT_BBOX[k]
                     for k in ("minLng", "minLat", "maxLng", "maxLat"))
    url = (BLOCKS + "?where=STATE%3D%2726%27&geometry=" + env +
           "&geometryType=esriGeometryEnvelope&inSR=4326"
           "&spatialRel=esriSpatialRelIntersects"
           "&outFields=POP100,INTPTLAT,INTPTLON&returnGeometry=false"
           "&outSR=4326&f=json&resultRecordCount=100000")
    out = subprocess.run(["curl", "-sS", "--fail", "--max-time", "600", url],
                         check=True, capture_output=True).stdout
    d = json.loads(out)
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
    if len(rows) < 15000:
        raise RuntimeError("only %d usable blocks — expected ~19,000 over Detroit's box"
                           % len(rows))
    return rows


def population_balance(features, blocks):
    model = _model(features)
    pops = {k: 0 for k, _ in model}
    for x, y, p in blocks:
        for k, g in model:
            if _point_in_geometry((x, y), g):
                pops[k] += p
                break
    total = sum(pops.values())
    ideal = total / float(len(pops)) if pops else 0
    worst = max(abs(v - ideal) / ideal for v in pops.values()) if ideal else 1.0
    return pops, total, ideal, worst


def check_shape(feats):
    problems = []
    if len(feats) != EXPECT_FEATURES:
        problems.append("%d features, expected %d — Detroit's council has seven "
                        "districts (its two at-large seats have no geometry and "
                        "must never acquire one)" % (len(feats), EXPECT_FEATURES))
    seen = sorted((district_of(f.get("properties") or {}) or "?") for f in feats)
    if tuple(seen) != EXPECT_DISTRICTS:
        problems.append("district numbers are %s, expected %s"
                        % (seen, list(EXPECT_DISTRICTS)))
    for f in feats:
        props = f.get("properties") or {}
        if "District" not in props:
            problems.append("a feature carries no bare District number — the card "
                            "headline and the hover label both read it")
            break
    return problems


def validate(source_features, result_features, samples=2000, seed=2026):
    """The fleet's 2,000-point protocol: simplification must not change which
    district a point is in, and must not introduce a double classification."""
    src, new = _model(source_features), _model(result_features)
    rng = random.Random(seed)
    agree = src_overlaps = new_overlaps = 0
    for _ in range(samples):
        pt = (rng.uniform(DETROIT_BBOX["minLng"], DETROIT_BBOX["maxLng"]),
              rng.uniform(DETROIT_BBOX["minLat"], DETROIT_BBOX["maxLat"]))
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
        return False, ("simplification ADDED overlaps: %d vs %d in the source"
                       % (new_overlaps, src_overlaps))
    if pct < 99.5:
        return False, "point-in-district agreement only %.2f%% (need >= 99.5%%)" % pct
    return True, ("%d/%d (%.2f%%) agreement over Detroit's envelope, %d source overlap(s), "
                  "none added" % (agree, samples, pct, src_overlaps))


def same_plan(a, b, tol=1e-9):
    """Do two services carry the same districts? Compared by each district's
    ring area, which is cheap and moves the moment a line does."""
    def areas(feats):
        out = {}
        for f in feats:
            k = district_of(f.get("properties") or {})
            g = f.get("geometry") or {}
            polys = g.get("coordinates", []) if g.get("type") == "MultiPolygon" else [g.get("coordinates", [])]
            tot = 0.0
            for p in polys:
                if not p:
                    continue
                for i, ring in enumerate(p):
                    s = 0.0
                    for j in range(len(ring) - 1):
                        x1, y1 = ring[j][0], ring[j][1]
                        x2, y2 = ring[j + 1][0], ring[j + 1][1]
                        s += (x2 - x1) * math.cos(math.radians((y1 + y2) / 2)) * (y2 + y1) / 2
                    tot += abs(s) if i == 0 else -abs(s)
            out[k] = tot
        return out
    A, B = areas(a), areas(b)
    if set(A) != set(B):
        return False
    return all(abs(A[k] - B[k]) <= tol * max(1.0, abs(A[k])) for k in A)


def check_shipped(path):
    if not os.path.exists(path):
        return ["%s is missing" % path]
    with open(path) as f:
        shipped = json.load(f)
    feats = shipped.get("features") or []
    problems = check_shape(feats)
    keys = {k for f in feats for k in (f.get("properties") or {})}
    stray = keys - set(KEEP_FIELDS) - set(DERIVED_FIELDS)
    if stray:
        problems.append("the shipped file carries unexpected properties %s — this "
                        "layer names nobody, and a name arriving in-band from the "
                        "source must not reach data/app/ unreviewed" % sorted(stray))
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
            print("build-mi-detroit-council: FAIL — " + p)
        if problems:
            sys.exit(1)
        with open(out_path) as f:
            n = len(json.load(f).get("features") or [])
        print("build-mi-detroit-council: OK — %d districts shipped" % n)
        return

    print("fetching the city's three council-district services…")
    src = fetch_geojson(SERVICE, ",".join(KEEP_FIELDS))
    current = fetch_geojson(WITNESS_CURRENT, "DistrictNu")
    archive = fetch_geojson(WITNESS_ARCHIVE, "district_number")

    if not same_plan(src["features"], current["features"]):
        sys.exit("build-mi-detroit-council: FAIL — the 2026 service and the city's "
                 "'Current' service no longer carry the same districts. One of them "
                 "has moved; find out which before shipping either.")
    if same_plan(src["features"], archive["features"]):
        sys.exit("build-mi-detroit-council: FAIL — the shipped plan is identical to "
                 "the ARCHIVED 2013 plan. That means the wrong service was fetched.")
    print("  the city's 'Current' service agrees, and the 2013 archive differs")

    print("fetching Census 2020 blocks for the currency gate…")
    blocks = fetch_blocks()
    pops, total, ideal, worst = population_balance(src["features"], blocks)
    _, atot, _, aworst = population_balance(archive["features"], blocks)
    for k in sorted(pops):
        print("    D%-3s %7d  %+6.2f%%" % (k, pops[k], (pops[k] - ideal) / ideal * 100))
    print("  shipped plan worst deviation %.2f%% | archived plan %.2f%%"
          % (worst * 100, aworst * 100))
    if total != DETROIT_POP_2020:
        sys.exit("build-mi-detroit-council: FAIL — the districts sum to %d, not Detroit's "
                 "Census 2020 population of %d. They do not tile the city."
                 % (total, DETROIT_POP_2020))
    if worst > MAX_DEVIATION:
        sys.exit("build-mi-detroit-council: FAIL — worst deviation %.2f%% exceeds %.0f%%. "
                 "A plan drawn to Census 2020 balances on it; this one does not."
                 % (worst * 100, MAX_DEVIATION * 100))
    if aworst < MIN_ARCHIVE_DEVIATION:
        sys.exit("build-mi-detroit-council: FAIL — the ARCHIVED plan now balances too "
                 "(%.2f%%), so this test no longer tells the two apart. A human should "
                 "look before trusting either." % (aworst * 100))
    print("  population identity exact: %d = Detroit's Census 2020 count" % total)

    kept = []
    for f in src["features"]:
        d = district_of(f.get("properties") or {})
        kept.append({"type": "Feature",
                     "properties": {"district_number": d,
                                    "district_name": (f["properties"].get("district_name")
                                                      or ("District " + str(d))),
                                    "District": d},
                     "geometry": f["geometry"]})
    full = {"type": "FeatureCollection", "features": kept}

    raw = os.path.join(APP_DATA_DIR, "_detroit_council_full.geojson")
    with open(raw, "w") as f:
        json.dump(full, f)
    subprocess.run(["npx", "-y", MAPSHAPER, raw,
                    "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
                    "-o", "precision=" + PRECISION, "format=geojson", out_path],
                   check=True, cwd=INSTANCE_ROOT)
    os.remove(raw)

    with open(out_path) as f:
        result = json.load(f)
    ok, note = validate(full["features"], result.get("features") or [])
    print("  simplification: " + note)
    if not ok:
        os.remove(out_path)
        sys.exit("build-mi-detroit-council: FAIL — " + note)
    problems = check_shipped(out_path)
    for p in problems:
        print("build-mi-detroit-council: FAIL — " + p)
    if problems:
        sys.exit(1)
    print("build-mi-detroit-council: wrote %s (%d districts, %d bytes)"
          % (out_path, len(result["features"]), os.path.getsize(out_path)))


if __name__ == "__main__":
    main()

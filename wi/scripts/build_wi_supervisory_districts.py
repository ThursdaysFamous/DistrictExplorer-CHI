#!/usr/bin/env python3
"""
Build data/app/county-supervisory-districts.json — every Wisconsin county
board supervisory district, statewide, in one pre-simplified file.

WHERE THE LINES COME FROM
-------------------------
Wisconsin is the one state in this fleet whose county board districts have a
STATEWIDE publisher. Wis. Stat. 5.15(4)(br)1 makes every county submit its
current supervisory district boundaries to the Legislative Technology
Services Bureau twice a year (15 January and 15 July), and LTSB publishes the
aggregate as an open ArcGIS feature service. So the 72-county answer that
costs Illinois one build per county costs Wisconsin one fetch.

That is a convenience, not an authority: LTSB republishes what a county
CLERK sent it, and a defective submission stays defective. This build
therefore never trusts the aggregate on its own — see the gates below.

TREMPEALEAU IS BUILT FROM THE COUNTY'S OWN LAYER, NOT LTSB
----------------------------------------------------------
LTSB's July 2026 file gives Trempealeau SIXTEEN districts numbered 1-14, 16,
17 — no district 15. It is not a missing polygon: the sixteen tile the county
completely (their union covers 100% of the county's own district 15 and
99.935% of its whole plan), because LTSB's "17" is drawn over the county's 15
AND 17 together. It is a MERGE.

The county did not merge them. Trempealeau County's own board page seats
SEVENTEEN supervisors in districts 1 through 17 — District 15 is David
Larson, term ending April 2028 — and the county's own 2021-2031 district
service publishes seventeen districts of 1,736-1,892 people each (ideal
1,809, worst deviation 4.6%), which is what an adopted plan looks like.
LTSB's merged district would hold about 3,478 against a sixteen-seat ideal of
1,922: +81%, which no county adopts and no court would allow.

So for Trempealeau alone the geometry comes from the county's own service and
the other 71 counties come from LTSB — the fleet's standing rule that
geometry comes from whatever proves the lines. Shipping LTSB's Trempealeau
would have told roughly 1,826 people they are in district 17, under a
supervisor who does not represent them.

WHAT THE GATES ACTUALLY CATCH
-----------------------------
* SUPERID continuity (1..n per county) is what caught Trempealeau, because
  the merge left a hole in the NUMBERING. It would not catch a county that
  merged and then renumbered cleanly.
* Ward reconciliation is the structural check: Wisconsin supervisory
  districts are built from whole municipal wards, so LTSB's ward layer
  carries each ward's SUPER_FIPS. Every ward must resolve to a district and
  every district must own at least one ward — a dropped district shows up as
  orphaned wards, whatever the numbering does.
* Per-county seat counts were checked against each county's OWN board page in
  a separate sweep (scripts/... see docs); this build re-asserts only what it
  can measure from the two services.

Population BALANCE is deliberately not a gate. It was measured (ward
populations from LTSB's 2024 election layer, which sum to 5,893,718 — the
state's exact 2020 census count) and it flags counties whose own adopted
plans are simply unequal: Juneau's spread is 466 to 2,157 across 21
districts, and Juneau County's own site publishes those same 21 districts.
An imbalanced plan is the county's, not this file's, and refusing to draw it
would hide a real district rather than fix anything.

Occasional OPERATOR step, not weekly CI — re-run after a 15 Jan / 15 Jul
submission window. Prerequisites: curl and Node.js (mapshaper).

Usage:
    python3 wi/scripts/build_wi_supervisory_districts.py
    python3 wi/scripts/build_wi_supervisory_districts.py --check   # gates only, no write
"""

import json
import os
import random
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "county-supervisory-districts.json"
MAPSHAPER = "mapshaper@0.6.102"  # pinned for reproducible output (fleet convention)

LTSB_ORG = "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services"
DISTRICTS = LTSB_ORG + "/WI_County_Supervisory_Districts_Current/FeatureServer/0"
WARDS = LTSB_ORG + "/WI_Municipal_Wards_Current/FeatureServer/0"

# Trempealeau County's own adopted plan, from the service its own "See What
# Voting District You're In" map draws (https://arcg.is/4GGSj0).
TREMPEALEAU_FIPS = "55121"
TREMPEALEAU_NAME = "Trempealeau"
TREMPEALEAU = (
    "https://services9.arcgis.com/cqHJZMbXoaOT0XrP/arcgis/rest/services"
    "/Trempealeau_County_County_Board_Supervisor_Districts_2021_2031_WFL1/FeatureServer/3"
)
TREMPEALEAU_SEATS = 17  # the county's own board page, districts 1-17

EXPECT_DISTRICTS = 1589   # LTSB, July 2026 submission window
EXPECT_COUNTIES = 72      # every Wisconsin county
EXPECT_WARDS_MIN = 7000   # LTSB ward layer, ~7,161 as of July 2026

SIMPLIFY = "9%"
PRECISION = "0.000001"    # 6 decimals ~= 0.11 m
STATE_BBOX = {"minLng": -93.09, "minLat": 42.29, "maxLng": -86.04, "maxLat": 47.51}
VALIDATION_KEY = "SUPER_FIPS"


def _curl(url):
    return subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "300",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/wi/)", url],
        check=True, capture_output=True,
    ).stdout


def oid_field(base):
    """The layer's own object-id column. LTSB's layers call it OBJECTID and
    Trempealeau's call it FID; paging with the wrong name returns nothing at
    all rather than erroring, so it is read from the layer rather than
    assumed."""
    meta = json.loads(_curl(base + "?f=json"))
    for f in meta.get("fields", []):
        if f.get("type") == "esriFieldTypeOID":
            return f["name"]
    raise RuntimeError("no object-id field on " + base)


def fetch_layer(base, out_fields, geometry=True, where="1=1"):
    """Page an ArcGIS feature layer out as GeoJSON in 4326."""
    import urllib.parse
    order = oid_field(base)
    feats = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true" if geometry else "false",
            "outSR": "4326",
            "geometryPrecision": "6",
            "f": "geojson",
            "resultOffset": str(offset),
            "resultRecordCount": "1000",
            "orderByFields": order,
        }
        data = json.loads(_curl(base + "/query?" + urllib.parse.urlencode(params)))
        batch = data.get("features") or []
        feats.extend(batch)
        if not data.get("properties", {}).get("exceededTransferLimit") \
           and not data.get("exceededTransferLimit"):
            break
        if not batch:
            break
        offset += len(batch)
    return feats


def normalize_ltsb(features):
    """Keep only what the card reads, and drop LTSB's CONTACT column — those
    are county staff members' individual e-mail addresses, published for
    redistricting correspondence and not for republication in a public app."""
    out = []
    for f in features:
        p = f["properties"]
        out.append({
            "type": "Feature",
            "properties": {
                "CNTY_FIPS": p["CNTY_FIPS"],
                "CNTY_NAME": p["CNTY_NAME"],
                "SUPERID": str(int(p["SUPERID"])),
                "SUPER_FIPS": p["SUPER_FIPS"],
            },
            "geometry": f["geometry"],
        })
    return out


def trempealeau_features():
    feats = fetch_layer(TREMPEALEAU, "DISTRICT")
    if len(feats) != TREMPEALEAU_SEATS:
        raise RuntimeError(
            "Trempealeau's own layer returned %d districts, expected %d — the county's "
            "plan may have changed; re-read its board page before shipping"
            % (len(feats), TREMPEALEAU_SEATS)
        )
    nums = sorted(int(f["properties"]["DISTRICT"]) for f in feats)
    if nums != list(range(1, TREMPEALEAU_SEATS + 1)):
        raise RuntimeError("Trempealeau districts are %s, expected 1..%d" % (nums, TREMPEALEAU_SEATS))
    out = []
    for f in feats:
        n = int(f["properties"]["DISTRICT"])
        out.append({
            "type": "Feature",
            "properties": {
                "CNTY_FIPS": TREMPEALEAU_FIPS,
                "CNTY_NAME": TREMPEALEAU_NAME,
                "SUPERID": str(n),
                "SUPER_FIPS": "%s%02d" % (TREMPEALEAU_FIPS, n),
            },
            "geometry": f["geometry"],
        })
    return out


def gate_districts(feats):
    """Structural gates on the assembled statewide set."""
    by_county = {}
    for f in feats:
        p = f["properties"]
        by_county.setdefault((p["CNTY_FIPS"], p["CNTY_NAME"]), []).append(int(p["SUPERID"]))
    if len(by_county) != EXPECT_COUNTIES:
        raise RuntimeError("%d counties, expected %d" % (len(by_county), EXPECT_COUNTIES))
    bad = []
    for (fips, name), ids in sorted(by_county.items()):
        if sorted(ids) != list(range(1, len(ids) + 1)):
            missing = [i for i in range(1, max(ids) + 1) if i not in set(ids)]
            bad.append("%s (%s): %d districts, numbering gaps at %s" % (name, fips, len(ids), missing))
    if bad:
        raise RuntimeError(
            "district numbering is not 1..n in %d county/counties — a county may have "
            "merged or dropped a district and the submission not caught up:\n  %s"
            % (len(bad), "\n  ".join(bad))
        )
    fipses = [f["properties"]["SUPER_FIPS"] for f in feats]
    if len(set(fipses)) != len(fipses):
        raise RuntimeError("SUPER_FIPS is not unique across the statewide set")
    return by_county


def gate_wards(feats):
    """Wisconsin supervisory districts are unions of whole municipal wards, so
    LTSB's ward layer is an independent witness to the district set: every
    ward must name a district that exists, and every district must own at
    least one ward. A district dropped from the district layer shows up here
    as orphaned wards even if the numbering was tidied afterwards."""
    wards = fetch_layer(WARDS, "WARD_FIPS,CNTY_FIPS,SUPER_FIPS", geometry=False)
    if len(wards) < EXPECT_WARDS_MIN:
        raise RuntimeError("ward layer returned %d wards, expected >= %d" % (len(wards), EXPECT_WARDS_MIN))
    ward_super = {w["properties"]["SUPER_FIPS"] for w in wards if w["properties"].get("SUPER_FIPS")}
    blank = sum(1 for w in wards if not w["properties"].get("SUPER_FIPS"))
    if blank:
        raise RuntimeError("%d ward(s) carry no SUPER_FIPS" % blank)

    # Trempealeau is deliberately not reconciled against the ward layer: the
    # ward layer rides the SAME county submission the district layer does, so
    # it repeats the merge (no ward there names district 15). It is the one
    # county whose witness is the county's own board page instead.
    dist_super = {f["properties"]["SUPER_FIPS"] for f in feats
                  if f["properties"]["CNTY_FIPS"] != TREMPEALEAU_FIPS}
    ward_super = {s for s in ward_super if not s.startswith(TREMPEALEAU_FIPS)}

    orphan_wards = sorted(ward_super - dist_super)
    empty_districts = sorted(dist_super - ward_super)
    if orphan_wards:
        raise RuntimeError("%d ward district-id(s) have no district polygon: %s"
                           % (len(orphan_wards), orphan_wards[:10]))
    if empty_districts:
        raise RuntimeError("%d district(s) own no ward: %s"
                           % (len(empty_districts), empty_districts[:10]))
    return len(wards)


# --- point-in-polygon mirroring index.html's even-odd test (fleet-standard copy) ---
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
    if geom is None:
        return False
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


def _model(features, key_prop):
    return [(f["properties"].get(key_prop), f["geometry"], _bbox(f["geometry"]))
            for f in features if f.get("geometry")]


def _districts_at(model, pt):
    hits = []
    for key, geom, bb in model:
        if bb[0] <= pt[0] <= bb[2] and bb[1] <= pt[1] <= bb[3] and _point_in_geometry(pt, geom):
            hits.append(key)
    return hits


def validate(source_features, result_features, samples=10000, seed=2026):
    """Refuse the build unless simplification preserves district coverage over
    the state envelope vs the full-precision fetch — the project's 2,000
    uniform-random-point protocol.

    OVERLAPS ARE MEASURED AGAINST THE SOURCE, NOT AGAINST ZERO. The fleet's
    other boundary builders draw on TIGERweb, a single topologically clean
    national product, so they can demand a perfect mosaic. This file is 72
    county submissions stitched together, and they disagree slightly about
    where the county lines are: LTSB's own published geometry overlaps itself
    on 0.017% of its area — 24.5 km2 of that between districts in DIFFERENT
    counties (two counties' files drawing one shared boundary differently)
    and only 0.28 km2 between districts in the SAME county, the largest of
    those 8.4 acres. Demanding zero would be demanding the publisher redraw
    the state; what this build can honestly require is that SIMPLIFICATION
    make it no worse, which is what the comparison below tests."""
    src = _model(source_features, VALIDATION_KEY)
    new = _model(result_features, VALIDATION_KEY)
    rng = random.Random(seed)

    # IN-STATE sampling, not envelope sampling. The fleet's other builders
    # scatter 2,000 points over the state's bounding box, which is the right
    # test for 8 or 33 or 99 districts. Wisconsin's envelope is about twice
    # the state's area and this layer has 1,590 districts, so envelope
    # sampling puts roughly one point in every other district — enough to
    # certify a chamber, far too thin to certify this. Points are drawn until
    # `samples` of them land in some district of the FULL-PRECISION source,
    # so every sample is a point that has a real answer to get wrong. (It
    # measured the difference: envelope-2,000 reported 100.00% for every
    # retain level from 4% to 14%, while in-state-20,000 separated them at
    # 99.895 / 99.950 / 99.995.)
    pts = []
    while len(pts) < samples:
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        hits = _districts_at(src, pt)
        if hits:
            pts.append((pt, hits))

    agree = src_overlaps = new_overlaps = 0
    for pt, o_hits in pts:
        s_hits = _districts_at(new, pt)
        if len(s_hits) > 1:
            new_overlaps += 1
        if len(o_hits) > 1:
            src_overlaps += 1
        o = o_hits[0] if len(o_hits) == 1 else "MULTI"
        s = s_hits[0] if len(s_hits) == 1 else (None if not s_hits else "MULTI")
        if o == s:
            agree += 1
    pct = 100.0 * agree / samples
    if new_overlaps > src_overlaps:
        return False, ("simplification introduced overlap: %d/%d sample points fall in >1 "
                       "district, against %d/%d in the full-precision source"
                       % (new_overlaps, samples, src_overlaps, samples))
    if pct < 99.9:
        return False, "point-in-district agreement only %.3f%% (need >= 99.9%%)" % pct
    return True, ("%d/%d (%.3f%%) agreement over %d in-state points; %d of them sit in "
                  "overlapping districts, unchanged from the source's %d"
                  % (agree, samples, pct, samples, new_overlaps, src_overlaps))


def run_mapshaper(source_path, out_path):
    subprocess.run(
        ["npx", "-y", MAPSHAPER, source_path,
         "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
         "-o", "precision=" + PRECISION, "format=geojson", out_path],
        check=True, cwd=REPO_ROOT,
    )


def main():
    check_only = "--check" in sys.argv[1:]

    raw = fetch_layer(DISTRICTS, "GEOID,SUPER_FIPS,SUPERID,CNTY_FIPS,CNTY_NAME")
    if len(raw) != EXPECT_DISTRICTS:
        raise RuntimeError("LTSB returned %d districts, expected %d — a county has "
                           "resubmitted; re-check the per-county seat counts before "
                           "moving this number" % (len(raw), EXPECT_DISTRICTS))
    ltsb = [f for f in normalize_ltsb(raw) if f["properties"]["CNTY_FIPS"] != TREMPEALEAU_FIPS]
    dropped = len(raw) - len(ltsb)
    feats = ltsb + trempealeau_features()

    by_county = gate_districts(feats)
    n_wards = gate_wards(feats)
    print("gates: %d districts across %d counties; numbering 1..n everywhere; "
          "%d wards reconcile with no orphans"
          % (len(feats), len(by_county), n_wards), file=sys.stderr)
    print("       Trempealeau: LTSB's %d merged districts replaced by the county's own %d"
          % (dropped, TREMPEALEAU_SEATS), file=sys.stderr)
    if check_only:
        return

    source = {"type": "FeatureCollection", "features": feats}
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "supervisory-src.geojson")
        with open(src_path, "w") as f:
            json.dump(source, f)
        out_tmp = os.path.join(tmp, "supervisory.geojson")
        run_mapshaper(src_path, out_tmp)
        with open(out_tmp) as f:
            simplified = json.load(f)

    n = len(simplified["features"])
    if n != len(feats):
        raise RuntimeError("simplify changed the feature count: %d -> %d" % (len(feats), n))

    ok, msg = validate(feats, simplified["features"])
    if not ok:
        raise RuntimeError("validation failed: %s" % msg)

    compact = json.dumps(simplified, separators=(",", ":"))
    if json.loads(compact) != simplified:
        raise RuntimeError("round-trip mismatch before writing")
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)
    with open(out_path, "w") as f:
        f.write(compact)
    print("county-supervisory-districts -> data/app/%s: %d features; %s; %d bytes (%s retain, 6dp)"
          % (OUT_NAME, n, msg, len(compact), SIMPLIFY), file=sys.stderr)


if __name__ == "__main__":
    main()

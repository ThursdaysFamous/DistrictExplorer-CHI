#!/usr/bin/env python3
"""
Build data/app/aldermanic-districts.json — every aldermanic (and village
trustee) district Wisconsin's ward fabric can honestly compose, dissolved
from LTSB's statewide municipal ward layer.

WHY A DISSOLVE, AND ON WHICH KEY. No Wisconsin publisher ships a statewide
aldermanic-district layer, but the state's ward layer carries each ward's
district assignment in ALDERID (Wis. Stat. 5.15(4)(br) filings, Jan/Jul).
The dissolve key is **COUSUBFP + ALDERID — never ALDER_FIPS**: ALDER_FIPS is
county-qualified, and 25 coded municipalities cross county lines, so keying
on it would split those cities' districts in two at the county line. An
incorporated place's COUSUBFP is statewide-unique (measured: no name
collision among coded C/V municipalities), which is exactly what lets the
dissolve merge a cross-county city back together.

MEASURED 2026-08-26 (July 2026 filing): 7,161 wards, 2,580 coded; 2,576 of
those in cities and villages (the other 4 are the Town of Mercer, Iron
County — a town elects no alderpersons, so the CTV gate drops them and this
builder prints them); 867 distinct district keys across 165 municipalities.
THE STATE'S OWN PRE-DISSOLVE AGREES: LTSB's BAS_Live_Collection_Alderpersons
layer (the mid-collection working set, currently the JANUARY session) holds
the same 867 C/V keys, key for key, across a different filing edition — a
two-edition witness this builder re-runs on every build. That BAS layer is
not the source (no stated terms, mutates mid-collection); the licensed AGOL
ward layer is.

THE PER-CITY COMPLETENESS GATE — the reason this file is not a one-liner.
Fourteen municipalities mix '00' placeholders with real district ids, and
the mix splits two ways, measured by uncoded-ward count and area share:

  * TEN ARE INCOMPLETE SUBMISSIONS and are EXCLUDED, each on the record in
    EXCLUDED below (uncoded share 9.4%-99.9% of the city's area). Appleton
    is the flagship: Outagamie County submits all 50 of its Appleton wards
    uncoded, only the Calumet/Winnebago fringes carry ids, and the city's
    own GIS publishes no aldermanic layer either (its pubserver's full
    service list and a portal-wide "alder" search both answer empty,
    measured 2026-08-26) — two dead routes, so the gap record stands.
    Bellevue is the INVERSE error and the reason the gate cuts both ways: a
    village with ONE spuriously coded ward (99.9% uncoded) would otherwise
    ship a single sliver posing as a trustee district.
  * FOUR ARE THE SLIVER SHAPE and SHIP WITH A HOLE: exactly one uncoded
    ward, 0.0%-1.4% of the city's area (Delavan, De Pere, Green Bay,
    Howard). Inside that sliver the card honestly answers no-district; the
    builder pins each and fails if a second uncoded ward ever appears.

An OPERATOR rebuild after each Jan-15 / Jul-15 filing window, exactly like
the supervisory build this file leans on (fetch/validate/mapshaper are
imported from it). A count change at a window is expected news — read it,
then move the EXPECT constants deliberately.

Usage:
    python3 wi/scripts/build_wi_aldermanic_districts.py
    python3 wi/scripts/build_wi_aldermanic_districts.py --check   # gates only
"""

import json
import os
import random
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from build_wi_supervisory_districts import (  # noqa: E402
    _curl, fetch_layer, _model, _districts_at, MAPSHAPER, STATE_BBOX, WARDS)

REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "aldermanic-districts.json"

BAS_ALDERS = ("https://mapservices.legis.wisconsin.gov/arcgis/rest/services"
              "/BAS_Collection/BAS_Live_Collection_Alderpersons/FeatureServer/0")

EXPECT_CODED_WARDS = 2580      # all coded wards, towns included
EXPECT_TOWN_CODED = 4          # the Town of Mercer anomaly, Iron County
EXPECT_DISTRICT_KEYS = 867     # distinct COUSUBFP+ALDERID over C/V
EXPECT_MUNICIPALITIES = 165    # C/V municipalities with any coded ward

# The ten measurably incomplete submissions: COUSUBFP -> (name, uncoded
# wards, uncoded share of the municipality's ward area). Computed fresh from
# the fetch every run and gated against this list — a change is a filing
# window doing its job, and the operator moves the entry with eyes open.
EXCLUDED = {
    "02375": ("Appleton", 50, 0.858),
    "06350": ("Bellevue", 11, 0.999),
    "06925": ("Berlin", 6, 0.874),
    "09725": ("Brillion", 2, 0.094),
    "17950": ("Cuba City", 1, 0.158),
    "21225": ("Durand", 1, 0.274),
    "22575": ("Edgerton", 8, 0.873),
    "38800": ("Kaukauna", 17, 0.998),
    "56925": ("New London", 3, 0.429),
    "64450": ("Port Washington", 1, 0.318),
}
# The four sliver-hole cities: ship, with exactly one uncoded ward each.
SLIVER_OK = {"19450": "Delavan", "19775": "De Pere",
             "31000": "Green Bay", "35950": "Howard"}

# 9% (the supervisory build's retain) measured 99.675% agreement here — city
# districts are small, so the same retain cuts proportionally deeper; 25%
# clears the 99.9% bar with the file still compact.
SIMPLIFY = "25%"
PRECISION = "0.000001"
UNCODED = ("", "00", "0000")


def is_coded(alderid):
    return (alderid or "").strip() not in UNCODED


def classify(attr_feats):
    """Group ward attributes by municipality; return (shipped keys by
    municipality, computed exclusions, computed slivers, town-coded count)."""
    mun = {}
    town_coded = 0
    for f in attr_feats:
        p = f["properties"]
        if is_coded(p.get("ALDERID")) and p.get("CTV") == "T":
            town_coded += 1
            continue
        if p.get("CTV") not in ("C", "V"):
            continue
        m = mun.setdefault(p["COUSUBFP"], {
            "name": p["MCD_NAME"], "ctv": p["CTV"], "coded": 0, "uncoded": 0,
            "coded_area": 0.0, "uncoded_area": 0.0, "districts": set()})
        area = p.get("Shape__Area") or 0.0
        if is_coded(p.get("ALDERID")):
            m["coded"] += 1
            m["coded_area"] += area
            m["districts"].add(p["ALDERID"].strip())
        else:
            m["uncoded"] += 1
            m["uncoded_area"] += area
    coded_mun = {k: m for k, m in mun.items() if m["coded"]}

    excluded, slivers = {}, {}
    for k, m in sorted(coded_mun.items()):
        if not m["uncoded"]:
            continue
        share = m["uncoded_area"] / (m["coded_area"] + m["uncoded_area"])
        if m["uncoded"] == 1 and share < 0.05:
            slivers[k] = m["name"]
        else:
            excluded[k] = (m["name"], m["uncoded"], round(share, 3))
    return coded_mun, excluded, slivers, town_coded


def bas_witness(shipped_keys, excluded_keys):
    """The state's own pre-dissolved layer, a different filing edition, must
    carry exactly the keys this build composed (shipped + excluded — the
    exclusions are OUR honesty call, not a disagreement about the coding)."""
    feats = fetch_layer(BAS_ALDERS, "COUSUBFP,CTV,ALDERID", geometry=False)
    bas = set()
    for f in feats:
        p = f["properties"]
        if p.get("CTV") in ("C", "V") and is_coded(p.get("ALDERID")):
            bas.add((p["COUSUBFP"], p["ALDERID"].strip()))
    ours = shipped_keys | excluded_keys
    if bas != ours:
        raise RuntimeError(
            "BAS witness disagrees: %d keys only in BAS (e.g. %s), %d only here (e.g. %s) — "
            "a filing edition moved; re-measure and move the EXPECT constants deliberately"
            % (len(bas - ours), sorted(bas - ours)[:4],
               len(ours - bas), sorted(ours - bas)[:4]))
    return len(bas)


def validate(source_wards, result_districts, samples=4000, seed=2026):
    """In-state sample points: wherever a full-precision coded ward answers,
    the dissolved+simplified district must answer with the same key. Tests
    the dissolve and the simplification in one measure."""
    src = _model(source_wards, "KEY")
    new = _model(result_districts, "KEY")
    rng = random.Random(seed)
    pts = []
    while len(pts) < samples:
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        hits = _districts_at(src, pt)
        if hits:
            pts.append((pt, hits))
    agree = 0
    for pt, o_hits in pts:
        s_hits = _districts_at(new, pt)
        if len(o_hits) == 1 and s_hits == o_hits:
            agree += 1
        elif len(o_hits) > 1:
            agree += 1  # a source self-overlap has no single right answer
    pct = 100.0 * agree / samples
    if pct < 99.9:
        return False, "point agreement only %.3f%% (need >= 99.9%%)" % pct
    return True, "%d/%d (%.3f%%) in-district point agreement" % (agree, samples, pct)


def main():
    check_only = "--check" in sys.argv[1:]

    attrs = fetch_layer(
        WARDS, "WARDID,COUSUBFP,MCD_NAME,CTV,ALDERID,Shape__Area", geometry=False)
    coded_total = sum(1 for f in attrs if is_coded(f["properties"].get("ALDERID")))
    if coded_total != EXPECT_CODED_WARDS:
        raise RuntimeError("ward layer carries %d coded wards, expected %d — a filing "
                           "window moved; re-measure before moving the constant"
                           % (coded_total, EXPECT_CODED_WARDS))
    coded_mun, excluded, slivers, town_coded = classify(attrs)
    if town_coded != EXPECT_TOWN_CODED:
        raise RuntimeError("%d coded TOWN wards (expected %d — the Mercer anomaly); "
                           "a town cannot elect alderpersons, re-read the filing"
                           % (town_coded, EXPECT_TOWN_CODED))
    if len(coded_mun) != EXPECT_MUNICIPALITIES:
        raise RuntimeError("%d municipalities carry coded wards, expected %d"
                           % (len(coded_mun), EXPECT_MUNICIPALITIES))
    all_keys = set()
    for k, m in coded_mun.items():
        all_keys |= {(k, d) for d in m["districts"]}
    if len(all_keys) != EXPECT_DISTRICT_KEYS:
        raise RuntimeError("%d district keys, expected %d" % (len(all_keys), EXPECT_DISTRICT_KEYS))

    if {k: v for k, v in excluded.items()} != EXCLUDED:
        raise RuntimeError(
            "computed exclusions differ from the pinned list:\n  computed: %s\n  pinned:   %s\n"
            "A county completed (or broke) a submission — re-measure, then move EXCLUDED."
            % (json.dumps(excluded, sort_keys=True), json.dumps(EXCLUDED, sort_keys=True)))
    if {k: v for k, v in slivers.items()} != SLIVER_OK:
        raise RuntimeError("computed sliver-hole cities differ from SLIVER_OK: %s vs %s"
                           % (sorted(slivers), sorted(SLIVER_OK)))

    shipped_mun = {k: m for k, m in coded_mun.items() if k not in EXCLUDED}
    shipped_keys = {(k, d) for k, m in shipped_mun.items() for d in m["districts"]}
    excluded_keys = all_keys - shipped_keys
    n_bas = bas_witness(shipped_keys, excluded_keys)
    print("gates: %d coded wards -> %d districts across %d municipalities shipped "
          "(%d districts in %d incomplete municipalities excluded; %d sliver holes; "
          "%d Mercer town wards dropped); BAS witness agrees on all %d keys"
          % (coded_total, len(shipped_keys), len(shipped_mun),
             len(excluded_keys), len(EXCLUDED), len(SLIVER_OK), town_coded, n_bas),
          file=sys.stderr)
    if check_only:
        return

    # geometry fetch: every coded C/V ward, filtered to shipped municipalities
    where = "CTV IN ('C','V') AND ALDERID IS NOT NULL AND ALDERID NOT IN ('00','0000','')"
    wards = fetch_layer(WARDS, "COUSUBFP,MCD_NAME,CTV,ALDERID", where=where)
    wards = [w for w in wards if w["properties"]["COUSUBFP"] in shipped_mun]
    expect_ward_n = sum(m["coded"] for m in shipped_mun.values())
    if len(wards) != expect_ward_n:
        raise RuntimeError("geometry fetch returned %d coded wards, attributes said %d"
                           % (len(wards), expect_ward_n))
    for w in wards:
        p = w["properties"]
        w["properties"] = {
            "KEY": p["COUSUBFP"] + "-" + p["ALDERID"].strip(),
            "COUSUBFP": p["COUSUBFP"],
            "MCD_NAME": p["MCD_NAME"],
            "CTV": p["CTV"],
            "ALDERID": p["ALDERID"].strip(),
        }

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "wards-src.geojson")
        with open(src_path, "w") as f:
            json.dump({"type": "FeatureCollection", "features": wards}, f)
        out_tmp = os.path.join(tmp, "alder.geojson")
        subprocess.run(
            ["npx", "-y", MAPSHAPER, src_path,
             "-dissolve2", "KEY", "copy-fields=COUSUBFP,MCD_NAME,CTV,ALDERID",
             "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
             "-o", "precision=" + PRECISION, "format=geojson", out_tmp],
            check=True, cwd=REPO_ROOT)
        with open(out_tmp) as f:
            dissolved = json.load(f)

    feats = dissolved["features"]
    if len(feats) != len(shipped_keys):
        raise RuntimeError("dissolve produced %d districts, expected %d"
                           % (len(feats), len(shipped_keys)))
    out_keys = {(f["properties"]["COUSUBFP"], f["properties"]["ALDERID"]) for f in feats}
    if out_keys != shipped_keys:
        raise RuntimeError("dissolved key set differs from the plan (e.g. %s)"
                           % sorted(shipped_keys ^ out_keys)[:4])

    ok, msg = validate(wards, feats)
    if not ok:
        raise RuntimeError("validation failed: %s" % msg)

    feats.sort(key=lambda f: (f["properties"]["COUSUBFP"],
                              f["properties"]["ALDERID"]))
    compact = json.dumps({"type": "FeatureCollection", "features": feats},
                         separators=(",", ":"), ensure_ascii=False)
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)
    with open(out_path, "w") as f:
        f.write(compact)
    print("aldermanic-districts -> data/app/%s: %d districts, %d municipalities; %s; "
          "%d bytes (%s retain, 6dp)"
          % (OUT_NAME, len(feats), len(shipped_mun), msg, len(compact), SIMPLIFY),
          file=sys.stderr)


if __name__ == "__main__":
    main()

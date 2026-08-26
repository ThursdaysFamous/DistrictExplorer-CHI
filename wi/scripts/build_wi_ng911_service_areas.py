#!/usr/bin/env python3
"""
Build the two statewide NG911 emergency-service-area files from the
Wisconsin Office of Emergency Communications' own aggregate — the route
the phase-2 research recorded and the guidebook backlog queued:

  data/app/fire-service-areas.json  which fire department responds at a
                                    point (FireBoundary, layer 3)
  data/app/law-service-areas.json   which law-enforcement agency serves a
                                    point (LawEnforcementBoundary, layer 4)
  data/app/psap-areas.json          which PSAP — public safety answering
                                    point — answers a 911 call placed at
                                    the point (PSAPBoundary, layer 6)

SOURCE. The OEC publishes every county's NG911 GIS filing as one public
feature service (org WI_OEC_GIS, item 593d0da225b24601ad0c21598ef52fb0,
updated roughly weekly) under an explicit licence: "This data is free and
open for use by the public." The schema is the WI NG911 GIS Data
Standards, "nearly identical to the NENA NG911 Standard". These are
RESPONSE areas — who is dispatched where — never taxing districts and
never electing bodies, which is why the cards name no officeholder; the
guidebook's fire cell calls this "the NYC operational shape, not the IL
taxing shape", and Illinois' own Lee County fire entry already ships the
same product one county at a time.

PER-AGENCY DISSOLVE, AND WHY THE KEY IS A PAIR. Counties file one polygon
per ESN-ish sub-area, so one department arrives as several rows (3,046
fire rows over 1,046 agencies at first build). The dissolve key is
DsplayName + Agency_ID, never DsplayName alone, because the bare name is
wrong in both directions at once: two UNRELATED departments share a name
across counties ("Rome Fire Department" files under both a Jefferson
County town's authority and Wood County's, ~100 miles apart), while one
REAL cross-county agency files under both its counties' authorities
(Appleton Fire under Outagamie's and Winnebago's). The pair keeps the two
Romes apart; a genuine cross-county agency ships as one feature per
filing authority, same name on each, which draws the county line inside
its area exactly as the source draws it — the card answer at any point is
identical either way.

EXPIRED ROWS ARE DROPPED BY DATE, NEVER BY COUNT. NENA carries an Expire
column; every expired fire/law row at first build (37 + 18) was
superseded history, and a FUTURE Expire date is a still-effective row
that must ship. The drop is computed against the clock each run.

WHAT THE DATA DOES NOT COVER IS MEASURED AND PINNED. Five authorities'
filings are absent or partial (Iowa, Vilas and Walworth file none of the
three tilings; Jefferson files law and PSAP but not fire; Polk's law
filing covers ~60% while its fire and PSAP file in full),
and LANGLADE COUNTY HAS NO PROVISIONING BOUNDARY AT ALL — 72 provisioning
polygons where the other 71 counties plus the City of Milwaukee each
carry one. Every rate is recomputed per run inside the counties' own
provisioning polygons and gated against UNFILED below, so a county
completing its filing fails the build loudly and the operator retires the
entry (and the matching gap record) with eyes open. The remaining
"uncovered" area in a naive statewide sample is Great Lakes water inside
TIGER county polygons — measured, not a gap.

An OPERATOR rebuild; the monthly source report watches the layer counts.
Prerequisites: curl and Node.js (mapshaper).
"""

import datetime
import json
import os
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from build_wi_supervisory_districts import (  # noqa: E402
    fetch_layer, _model, _districts_at, _bbox, _point_in_geometry,
    MAPSHAPER, STATE_BBOX)

REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

OEC = ("https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services"
       "/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer")
FIRE = OEC + "/3"
LAW = OEC + "/4"
PROVISIONING = OEC + "/5"
PSAP = OEC + "/6"

LAYERS = [
    {"name": "fire", "url": FIRE, "out": "fire-service-areas.json",
     "min_rows": 2800, "min_agencies": 950},
    {"name": "law", "url": LAW, "out": "law-service-areas.json",
     "min_rows": 2900, "min_agencies": 600},
    # PSAP is the tiling where the date filter EARNS its by-date form: 11 of
    # its 208 raw rows carried FUTURE Expire dates at first measurement —
    # still-effective rows a drop-anything-with-Expire filter would delete.
    # 205 effective rows over 95 answering points; its rare overlaps
    # (a county PSAP and a city PD's own dispatch both filed, ~0.1% of
    # points) render like law's, every center at the point.
    {"name": "psap", "url": PSAP, "out": "psap-areas.json",
     "min_rows": 190, "min_agencies": 88},
]

# Filing absences, pinned exactly as measured 2026-08-26 (40 seeded sample
# points inside each authority's own provisioning polygon; flagged under
# 90% coverage). Keyed by the provisioning DiscrpAgID; the value is the
# set of layers that authority has NOT (fully) filed. Mirrored by the gap
# records ng911-fire-filings / ng911-law-filings — retire both together.
UNFILED = {
    "iowacounty.org": {"fire", "law", "psap"},
    "vilascountywi.gov": {"fire", "law", "psap"},
    "co.walworth.wi.us": {"fire", "law", "psap"},
    "jeffersoncountywi.gov": {"fire"},    # law and PSAP file in full
    "polkcountywi.gov": {"law"},          # partial: ~60% covered at pin time
}
EXPECT_PROVISIONING = 72   # 71 counties + the City of Milwaukee; Langlade absent
NO_PROVISIONING = "langlade"

SIMPLIFY = "8%"
PRECISION = "0.000001"     # 6 decimals ~= 0.11 m
COVERAGE_SAMPLES = 40      # per provisioning polygon, seeded
VALIDATE_SAMPLES = 4000    # statewide dissolve+simplify agreement gate
SEP = "\x1f"               # KEY separator; never appears in either field


def fetch_retry(url, fields, attempts=3):
    """services3.arcgis.com drops the occasional mid-paging request (curl
    exit 92, an HTTP/2 stream reset — measured on the first live build);
    the shared pager has no retry, so the whole fetch retries here."""
    import time
    for attempt in range(attempts):
        try:
            return fetch_layer(url, fields)
        except subprocess.CalledProcessError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def effective(features):
    """Drop rows whose Expire date has passed — superseded filings. A future
    Expire is still in force and ships; the counts are printed, never pinned,
    because they move with the OEC's weekly refresh."""
    now_ms = (datetime.datetime.now(datetime.timezone.utc)
              - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
              ).total_seconds() * 1000
    keep, dropped, future = [], 0, 0
    for f in features:
        exp = f["properties"].get("Expire")
        if exp and exp < now_ms:
            dropped += 1
            continue
        if exp:
            future += 1
        keep.append(f)
    return keep, dropped, future


def keyed(features, layer_name):
    """Attach the dissolve KEY; refuse rows a card could not answer from."""
    for f in features:
        p = f["properties"]
        name = (p.get("DsplayName") or "").strip()
        agency = (p.get("Agency_ID") or "").strip()
        if not name or not agency:
            raise RuntimeError("%s: a row is missing DsplayName or Agency_ID "
                               "(NGUID %r) — the schema moved, re-measure"
                               % (layer_name, p.get("NGUID")))
        if SEP in name or SEP in agency:
            raise RuntimeError("%s: the KEY separator appears in %r" % (layer_name, name))
        f["properties"] = {"KEY": name + SEP + agency, "NAME": name}
    return features


def sample_inside(geom, n, seed):
    """n seeded uniform points inside a polygon (rejection over its bbox)."""
    import random
    rng = random.Random(seed)
    bb = _bbox(geom)
    pts, tries = [], 0
    while len(pts) < n and tries < n * 200:
        tries += 1
        pt = (rng.uniform(bb[0], bb[2]), rng.uniform(bb[1], bb[3]))
        if _point_in_geometry(pt, geom):
            pts.append(pt)
    return pts


def gate_filings(feats_by_layer):
    """Recompute per-authority coverage inside the provisioning polygons and
    refuse the build if it disagrees with the pinned UNFILED map."""
    prov = fetch_layer(PROVISIONING, "DiscrpAgID")
    if len(prov) != EXPECT_PROVISIONING:
        raise RuntimeError("provisioning layer carries %d polygons, expected %d — "
                           "an authority joined or left; re-measure UNFILED and the "
                           "gap records before moving this number"
                           % (len(prov), EXPECT_PROVISIONING))
    if any(NO_PROVISIONING in (f["properties"].get("DiscrpAgID") or "").lower()
           for f in prov):
        raise RuntimeError("Langlade County now carries a provisioning polygon — "
                           "its no-provisioning record (and the gap records) are "
                           "stale; re-measure")
    models = {name: _model(feats, "KEY") for name, feats in feats_by_layer.items()}
    computed = {}
    for i, f in enumerate(prov):
        agid = (f["properties"].get("DiscrpAgID") or "").strip()
        pts = sample_inside(f["geometry"], COVERAGE_SAMPLES, seed=7 + i)
        if not pts:
            raise RuntimeError("no sample points landed inside provisioning %r" % agid)
        missing = set()
        for lname, model in models.items():
            hit = sum(1 for pt in pts if _districts_at(model, pt))
            if 100.0 * hit / len(pts) < 90:
                missing.add(lname)
        if missing:
            computed[agid] = missing
    if computed != UNFILED:
        raise RuntimeError(
            "measured filing absences differ from the pinned UNFILED map — a county "
            "filed (or a filing broke). Re-measure, then move UNFILED and the gap "
            "records together.\n  computed: %s\n  pinned:   %s"
            % (sorted((k, sorted(v)) for k, v in computed.items()),
               sorted((k, sorted(v)) for k, v in UNFILED.items())))
    return len(prov)


def validate(source_feats, result_feats):
    """Statewide seeded sample: wherever the full-precision source answers a
    NAME set, the dissolved+simplified output must answer the same set. Name
    sets, not single names, because law jurisdictions genuinely overlap (a
    sheriff and a municipal PD both filed over ~0.5% of points at first
    build) and the card renders every agency at the point."""
    import random
    src = _model(source_feats, "NAME")
    new = _model(result_feats, "NAME")
    rng = random.Random(2026)
    tested = agree = 0
    while tested < VALIDATE_SAMPLES:
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        o_hits = _districts_at(src, pt)
        if not o_hits:
            continue
        tested += 1
        if set(_districts_at(new, pt)) == set(o_hits):
            agree += 1
    pct = 100.0 * agree / tested
    if pct < 99.9:
        raise RuntimeError("dissolve+simplify agreement only %.3f%% (need >= 99.9%%)"
                           % pct)
    return "%d/%d (%.3f%%) name-set agreement" % (agree, tested, pct)


def build(layer, check_only):
    feats = fetch_retry(layer["url"], "DsplayName,Agency_ID,NGUID,Expire")
    feats, dropped, future = effective(feats)
    if len(feats) < layer["min_rows"]:
        raise RuntimeError("%s: %d effective rows, floor %d — the service shrank; "
                           "re-measure before shipping"
                           % (layer["name"], len(feats), layer["min_rows"]))
    feats = keyed(feats, layer["name"])
    keys = {f["properties"]["KEY"] for f in feats}
    if len(keys) < layer["min_agencies"]:
        raise RuntimeError("%s: %d agencies, floor %d"
                           % (layer["name"], len(keys), layer["min_agencies"]))
    print("%s: %d effective rows (%d expired dropped, %d future-dated kept) "
          "-> %d agency keys" % (layer["name"], len(feats), dropped, future, len(keys)),
          file=sys.stderr)
    if check_only:
        return feats, None

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, layer["name"] + "-src.geojson")
        with open(src_path, "w") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f)
        out_tmp = os.path.join(tmp, layer["name"] + ".geojson")
        subprocess.run(
            # -dissolve, NEVER -dissolve2: dissolve2 flattens the layer into
            # a shared-topology mosaic and assigns each face to ONE group,
            # which silently deletes the real concurrent-jurisdiction
            # overlaps the law layer carries (a sheriff and a municipal PD
            # both filed over ~0.5% of points) — measured as a 98.750%
            # name-set agreement before the swap, 100.000% after it.
            ["npx", "-y", MAPSHAPER, src_path,
             "-dissolve", "KEY", "copy-fields=NAME",
             "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
             "-o", "precision=" + PRECISION, "format=geojson", out_tmp],
            check=True, cwd=REPO_ROOT)
        with open(out_tmp) as f:
            dissolved = json.load(f)

    out_feats = dissolved["features"]
    if len(out_feats) != len(keys):
        raise RuntimeError("%s: dissolve produced %d features, expected %d"
                           % (layer["name"], len(out_feats), len(keys)))
    out_feats.sort(key=lambda f: f["properties"]["KEY"])
    for f in out_feats:
        f["properties"] = {"NAME": f["properties"]["NAME"]}

    msg = validate(feats, out_feats)
    compact = json.dumps({"type": "FeatureCollection", "features": out_feats},
                         separators=(",", ":"), ensure_ascii=False)
    path = os.path.join(APP_DATA_DIR, layer["out"])
    with open(path, "w") as f:
        f.write(compact)
    print("%s: wrote %s — %d agency areas, %d bytes; %s"
          % (layer["name"], layer["out"], len(out_feats), len(compact), msg),
          file=sys.stderr)
    return feats, len(out_feats)


def main():
    check_only = "--check" in sys.argv[1:]
    built = {}
    for layer in LAYERS:
        built[layer["name"]] = build(layer, check_only)
    n_prov = gate_filings({name: pair[0] for name, pair in built.items()})
    print("gates: filing absences match the pinned UNFILED map across all %d "
          "provisioning authorities (Langlade still absent)" % n_prov,
          file=sys.stderr)


if __name__ == "__main__":
    main()

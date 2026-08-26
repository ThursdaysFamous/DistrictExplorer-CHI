#!/usr/bin/env python3
"""
Build the two Milwaukee city-scoped geography files the phase-3 record
queued behind the MPS board build, with the same two-surface machinery
(imported from build_mps_school_board_districts):

  data/app/mpd-districts.json            the 7 Milwaukee Police Department
                                         districts (MPD/MPD_geography layer 2,
                                         field POLICE = district number)
  data/app/milwaukee-neighborhoods.json  the city's 190 named neighborhoods
                                         (planning/special_districts layer 4,
                                         field NEIGHBORHD)
  data/app/mpd-squad-areas.json          the 25 MPD squad areas — the beat
                                         analog (MPD/MPD_geography layer 1,
                                         field SQUADAREA), whose HUNDREDS
                                         DIGIT IS THE DISTRICT (120-140 in
                                         District 1 ... 720-750 in District
                                         7): a structural fact the build
                                         GATES by sampling each squad
                                         against the shipped district file,
                                         the Richland two-layers-compose-
                                         each-other check in city form

Both are CC-BY city datasets published twice over — the measured-flaky
milwaukeemaps ArcGIS service (fetched at BUILD TIME with retries, server-
reprojected via outSR=4326, never fetched by the app) and the stable CKAN
shapefile, which is the WITNESS: same keys, and each feature's share of the
total area must agree between the two surfaces before either file ships.

MPD DISTRICTS REVISIT A RECORDED DROP with the city-scoped frame: the
safety matrix's Wisconsin police cell was a drop because no STATEWIDE
boundary publisher exists (the NG911 route stays the statewide candidate),
exactly as Chicago's own police-district layer is city-scoped. District
CAPTAINS are not shippable — city.milwaukee.gov sits behind a Cloudflare
challenge (an access control, never defeated) — so the card links MPD's own
district pages and names no one; the gap record carries it.

NEIGHBORHOOD NAMES are published ALL-CAPS ("BAY VIEW", "TOWN OF LAKE");
they ship title-cased with the small particles kept low ("Town of Lake"),
a stated display transformation of the city's own value, which also ships
verbatim on the feature as NAME_RAW so nothing is lost.

An OPERATOR rebuild; the monthly source report watches both endpoints.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_mps_school_board_districts import (  # noqa: E402
    fetch, geom_area, shp_areas, BBOX)
from build_wi_supervisory_districts import (  # noqa: E402
    _bbox, _point_in_geometry)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA = os.path.join(REPO_ROOT, "data", "app")

import math  # noqa: E402
SCALE = math.cos(math.radians(43.05))

LAYERS = [
    {
        "out": "mpd-districts.json",
        "rest": ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/MPD"
                 "/MPD_geography/MapServer/2"),
        "shp": ("https://data.milwaukee.gov/dataset/1cb11103-18df-4c6e-b622-859d1e217920"
                "/resource/cac45f22-0609-4972-88a5-a3f6d9f74f83/download/mpd.zip"),
        "key": "POLICE",
        "expect": [str(n) for n in range(1, 8)],
        "props": lambda a: {"DISTRICT": str(a["POLICE"])},
    },
    {
        "out": "milwaukee-neighborhoods.json",
        "rest": ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/planning"
                 "/special_districts/MapServer/4"),
        "shp": ("https://data.milwaukee.gov/dataset/0f5695f6-bca1-46e9-832b-54d1d906d28e"
                "/resource/964353e8-a579-402a-a8e9-c50ea0ae3aa4/download/neighborhood.zip"),
        "key": "NEIGHBORHD",
        "expect_n": 190,
        "props": lambda a: {"NAME": neighborhood_case(a["NEIGHBORHD"]),
                            "NAME_RAW": str(a["NEIGHBORHD"]).strip()},
    },
    {
        "out": "mpd-squad-areas.json",
        "rest": ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/MPD"
                 "/MPD_geography/MapServer/1"),
        "shp": ("https://data.milwaukee.gov/dataset/3216a1e4-4286-4247-a0c2-95551d5d268e"
                "/resource/1afe1cae-c409-43f0-a381-27dcaf519eec/download/mpd_squad_area.zip"),
        "key": "SQUADAREA",
        "expect_n": 25,
        # SQUAD carries the display form the compact card's header shows;
        # the city's own integer ships beside it, and DISTRICT is the
        # hundreds digit — verified against the shipped district file below,
        # never merely asserted
        "props": lambda a: {"SQUAD": "Squad " + str(a["SQUADAREA"]),
                            "SQUAD_RAW": str(a["SQUADAREA"]),
                            "DISTRICT": str(int(a["SQUADAREA"]) // 100)},
        "verify": "squads_in_districts",
    },
]


def squads_in_districts(out_feats):
    """The squad numbering ENCODES the district (hundreds digit), and the
    city publishes both layers independently — so the claim is checkable and
    is therefore a GATE: 60 seeded sample points inside each squad must land
    >= 97% inside the district its number names, against the mpd-districts
    file this same script builds. Run after the districts entry, which the
    LAYERS order guarantees."""
    import random
    with open(os.path.join(APP_DATA, "mpd-districts.json")) as f:
        districts = {feat["properties"]["DISTRICT"]: feat["geometry"]
                     for feat in json.load(f)["features"]}
    for feat in out_feats:
        p = feat["properties"]
        num, want = p["SQUAD_RAW"], p["DISTRICT"]
        if want not in districts:
            raise SystemExit("squad %s names district %s, which the district "
                             "file does not carry" % (num, want))
        rng = random.Random(int(num))
        bb = _bbox(feat["geometry"])
        pts, tries = [], 0
        while len(pts) < 60 and tries < 12000:
            tries += 1
            pt = (rng.uniform(bb[0], bb[2]), rng.uniform(bb[1], bb[3]))
            if _point_in_geometry(pt, feat["geometry"]):
                pts.append(pt)
        if not pts:
            raise SystemExit("no sample points landed inside squad %s" % num)
        hit = sum(1 for pt in pts if _point_in_geometry(pt, districts[want]))
        share = 100.0 * hit / len(pts)
        if share < 97:
            raise SystemExit("squad %s sits only %.1f%% inside District %s — "
                             "the hundreds-digit rule broke; re-measure before "
                             "shipping" % (num, share, want))
    print("mpd-squad-areas.json: all %d squads verified inside their "
          "hundreds-digit district (>= 97%% of sampled points each)"
          % len(out_feats))

LOW_WORDS = {"of", "the", "and", "at", "on", "in"}


def neighborhood_case(raw):
    words = str(raw).strip().split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        out.append(lw if i and lw in LOW_WORDS else lw.capitalize())
    return " ".join(out)


def build(layer):
    url = (layer["rest"] + "/query?where=1%3D1&outFields=" + layer["key"] +
           "&outSR=4326&geometryPrecision=6&f=geojson")
    gj = json.loads(fetch(url))
    feats = gj.get("features") or []
    by_key = {}
    for f in feats:
        k = str(f["properties"].get(layer["key"])).strip()
        if k in by_key:
            raise SystemExit("%s: key %r served twice" % (layer["out"], k))
        by_key[k] = f
    if "expect" in layer and sorted(by_key) != sorted(layer["expect"]):
        raise SystemExit("%s: keys %s, expected %s"
                         % (layer["out"], sorted(by_key)[:8], layer["expect"]))
    if "expect_n" in layer and len(by_key) != layer["expect_n"]:
        raise SystemExit("%s: %d features, expected %d"
                         % (layer["out"], len(by_key), layer["expect_n"]))
    for k, f in by_key.items():
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        lng, lat = polys[0][0][0]
        if not (BBOX["min_lat"] <= lat <= BBOX["max_lat"] and
                BBOX["min_lng"] <= lng <= BBOX["max_lng"]):
            raise SystemExit("%s: %r starts at (%s,%s) — outside Milwaukee; outSR "
                             "was ignored" % (layer["out"], k, lat, lng))

    # pair the two surfaces on a SPACE-INSENSITIVE key fold: the city's own
    # two copies spell one neighborhood apart ("MCGOVERN PARK" on the live
    # service, "MC GOVERN PARK" in the shapefile — measured at first build),
    # and the fold pairs them while the print below keeps the difference on
    # the record. The REST spelling ships (it is the maintained service).
    def kfold(k):
        return re.sub(r"\s+", "", str(k)).upper()
    witness = {}
    for k, v in shp_areas(fetch(layer["shp"], binary=True),
                          key_field=layer["key"]).items():
        witness[kfold(k)] = (str(k).strip(), v)
    rest_by_fold = {kfold(k): k for k in by_key}
    if sorted(witness) != sorted(rest_by_fold):
        only_r = sorted(set(rest_by_fold) - set(witness))[:4]
        only_s = sorted(set(witness) - set(rest_by_fold))[:4]
        raise SystemExit("%s: the two city surfaces disagree on the key set "
                         "even space-folded (REST-only %s, shapefile-only %s)"
                         % (layer["out"], only_r, only_s))
    for fk, (raw, _v) in sorted(witness.items()):
        rk = rest_by_fold[fk]
        if raw != rk:
            print("%s: the city's two surfaces spell %r apart (service %r, "
                  "shapefile %r) — the service spelling ships"
                  % (layer["out"], fk, rk, raw))
    got = {k: geom_area(f["geometry"], scale_x=SCALE) for k, f in by_key.items()}
    tot_g = sum(got.values())
    tot_w = sum(v for _raw, v in witness.values())
    worst = 0.0
    for k in by_key:
        w_val = witness[kfold(k)][1]
        diff = abs(got[k] / tot_g - w_val / tot_w)
        worst = max(worst, diff)
        if diff > 0.005:
            raise SystemExit("%s: %r is %.3f%% of the city on the REST layer but "
                             "%.3f%% in the shapefile — the surfaces disagree"
                             % (layer["out"], k, 100 * got[k] / tot_g,
                                100 * w_val / tot_w))

    out_feats = [{"type": "Feature", "geometry": by_key[k]["geometry"],
                  "properties": layer["props"](by_key[k]["properties"])}
                 for k in sorted(by_key)]
    if layer.get("verify"):
        globals()[layer["verify"]](out_feats)  # a failed gate refuses the write
    compact = json.dumps({"type": "FeatureCollection", "features": out_feats},
                         separators=(",", ":"), ensure_ascii=False)
    path = os.path.join(APP_DATA, layer["out"])
    with open(path, "w") as f:
        f.write(compact)
    print("%s: %d features, area shares witnessed (max diff %.4f%%), %d bytes"
          % (layer["out"], len(out_feats), 100 * worst, len(compact)))


def main():
    for layer in LAYERS:
        build(layer)


if __name__ == "__main__":
    sys.exit(main())

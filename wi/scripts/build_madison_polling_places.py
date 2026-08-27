#!/usr/bin/env python3
"""
Build data/app/madison-polling-places.json — the City of Madison ward ->
polling place pairing for the ward card, the second city to join after
Milwaukee (whose build this mirrors; see build_mke_polling_places.py).

WEC's statewide pairing stays unreadable (gap `ward-polling-places` —
the 2026-08-27 recon measured the commission's interior data pages
re-challenging a cleared browser, so the statewide question moved to the
ask ledger), but Madison publishes its own pairing as ONE LAYER on the
city's open-data server: Public/OPEN_DATA/MapServer/4 "Polling Places"
is a POINT PER WARD — 137 rows, each carrying the ward number, the
building name, the street address, and the point (measured 2026-08-27).
The pairing IS the layer, so unlike Milwaukee there is no separate CSV
of record to witness against; the witnesses are the ward KEYS:

  * THE LTSB KEY WITNESS (the gate that makes the pairing usable at
    all): the app's ward card renders LTSB's statewide fabric, so the
    137 ward numbers must equal LTSB's Madison city set exactly —
    measured 1..137 contiguous, re-fetched every build;
  * THE CITY'S OWN WARD LAYER (Public/OPEN_DATA/MapServer/11, the same
    fabric madisonCoverage's outline was dissolved from) must carry the
    same 137 ward numbers — two city layers composing, the Richland
    lesson in city form.

DATED AS FETCHED, PER ELECTION: the MapServer layer publishes no edition
date (no editingInfo — measured), so each record's asOf is the build
date, labeled as the day the city's layer was read, and the card states
it beside the MyVote link. No weekly workflow — re-run this builder when
an election approaches (WATCH.md row), exactly Milwaukee's cadence.

The licence is the city's Data Policy reference-use disclaimer with the
"City of Madison, Wisconsin" attribution — the Madison city tier's
captured posture (build_madison_city_layers.py).
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT = os.path.join(REPO_ROOT, "data", "app", "madison-polling-places.json")

POLLING = ("https://maps.cityofmadison.com/arcgis/rest/services/Public/"
           "OPEN_DATA/MapServer/4/query?where=1%3D1"
           "&outFields=tvpoll_p_WARD,tvpoll_p_BLDG_NAME,tvpoll_p_ADDRESS,"
           "tvpoll_p_HANDICAP_ACCESS,tvpoll_p_SPEC_COMMENTS"
           "&returnGeometry=true&outSR=4326&f=json")
CITY_WARDS = ("https://maps.cityofmadison.com/arcgis/rest/services/Public/"
              "OPEN_DATA/MapServer/11/query?where=1%3D1&outFields=WARD"
              "&returnGeometry=false&f=json")
LTSB_WARDS = ("https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/"
              "services/WI_Municipal_Wards_Current/FeatureServer/0/query"
              "?where=MCD_NAME%3D%27Madison%27+AND+CTV%3D%27C%27"
              "&outFields=WARDID&returnGeometry=false"
              "&resultRecordCount=2000&f=json")
SOURCE_URL = "https://www.cityofmadison.com/clerk/elections-voting"
BBOX = {"min_lat": 42.95, "max_lat": 43.25, "min_lng": -89.65,
        "max_lng": -89.15}


def fetch(url, tries=6, timeout=90):
    last = None
    for _ in range(tries):
        try:
            return subprocess.run(
                ["curl", "-sSL", "--fail", "--max-time", str(timeout),
                 "-H", "User-Agent: districtry/1.0 (+https://districtry.com/wi/)",
                 url],
                check=True, capture_output=True).stdout
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise last


def main():
    feats = json.loads(fetch(POLLING)).get("features") or []
    pairing = {}
    for f in feats:
        a = f["attributes"]
        ward = a.get("tvpoll_p_WARD")
        if not isinstance(ward, int):
            raise SystemExit("non-integer ward %r in the polling layer" % ward)
        if str(ward) in pairing:
            raise SystemExit("ward %d appears twice — the one-point-per-ward "
                             "shape broke; re-measure" % ward)
        name = re.sub(r"\s+", " ", str(a.get("tvpoll_p_BLDG_NAME") or "")).strip()
        addr = re.sub(r"\s+", " ", str(a.get("tvpoll_p_ADDRESS") or "")).strip()
        if not name or not addr:
            raise SystemExit("ward %d pairs to an empty name or address" % ward)
        g = f.get("geometry") or {}
        lat, lng = g.get("y"), g.get("x")
        if lat is None or lng is None:
            raise SystemExit("ward %d's polling point has no geometry" % ward)
        if not (BBOX["min_lat"] < lat < BBOX["max_lat"]
                and BBOX["min_lng"] < lng < BBOX["max_lng"]):
            raise SystemExit("ward %d's point (%s, %s) is outside Madison — "
                             "outSR ignored?" % (ward, lat, lng))
        rec = {"name": name, "address": addr,
               "lat": round(lat, 6), "lng": round(lng, 6)}
        access = str(a.get("tvpoll_p_HANDICAP_ACCESS") or "").strip()
        if access:
            rec["accessibleEntrance"] = access
        comments = str(a.get("tvpoll_p_SPEC_COMMENTS") or "").strip()
        if comments:
            rec["mainEntrance"] = comments
        pairing[str(ward)] = rec

    # ---- key witness: the pairing's ward set must BE LTSB's Madison set ----
    ltsb = json.loads(fetch(LTSB_WARDS))["features"]
    ltsb_ids = {str(int(f["attributes"]["WARDID"])) for f in ltsb}
    if set(pairing) != ltsb_ids:
        only_city = sorted(set(pairing) - ltsb_ids, key=int)[:8]
        only_ltsb = sorted(ltsb_ids - set(pairing), key=int)[:8]
        raise SystemExit(
            "the city's polling ward set no longer matches LTSB's Madison "
            "wards (city-only: %s; LTSB-only: %s) — a ward filing moved; "
            "re-measure before shipping" % (only_city, only_ltsb))

    # ---- composition witness: the city's own ward layer agrees ----
    city = json.loads(fetch(CITY_WARDS))["features"]
    city_ids = {str(int(f["attributes"]["WARD"])) for f in city}
    if set(pairing) != city_ids:
        raise SystemExit(
            "the city's polling layer and its own ward layer disagree "
            "(polling-only: %s; wards-only: %s) — the two city surfaces "
            "desynchronized; do not ship"
            % (sorted(set(pairing) - city_ids, key=int)[:8],
               sorted(city_ids - set(pairing), key=int)[:8]))

    if len(pairing) < 130:
        raise SystemExit("only %d wards paired — Madison has had 137; the "
                         "layer shrank, re-measure" % len(pairing))

    as_of = date.today().isoformat()
    out = {}
    for ward in sorted(pairing, key=int):
        rec = dict(pairing[ward])
        # the layer publishes no edition date (measured: no editingInfo),
        # so the honest date is the day this build read it
        rec["asOf"] = as_of
        rec["sourceUrl"] = SOURCE_URL
        out[ward] = rec

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    n_places = len({(r["name"], r["address"]) for r in out.values()})
    print("wrote %s — %d wards -> %d polling places, read %s; ward set "
          "equals LTSB's Madison wards AND the city's own ward layer exactly"
          % (os.path.relpath(OUT, REPO_ROOT), len(out), n_places, as_of),
          file=sys.stderr)


if __name__ == "__main__":
    main()

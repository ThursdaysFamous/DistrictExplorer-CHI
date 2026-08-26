#!/usr/bin/env python3
"""
Build data/app/mke-polling-places.json — the City of Milwaukee ward ->
polling place pairing for the ward card (phase 4 PR 3,
docs/WI_PHASE4_PLAN.md).

WEC's statewide polling data sits behind a Cloudflare challenge (gap
`ward-polling-places` — an access control, never defeated), but Milwaukee
publishes its own pairing THREE ways on data.milwaukee.gov (CC-BY,
"Voting Wards and Polling Places"), and this builder uses all three:

  * the CSV is the PAIRING OF RECORD — one row per ward: polling place
    name, address, and the entrance/parking guidance a voter actually
    needs. Its rows are CR-terminated (bare \\r, no LF) — a measured trap;
  * the city's REST voting-wards layer (election/election_wards/1) states
    the same pairing per ward and is the WITNESS: every ward's
    (name, address) must agree with the CSV after whitespace/case
    normalization, or the build refuses;
  * the REST polling-places layer (/0) supplies each place's POINT,
    server-reprojected to WGS84 and bbox-gated — matched to the CSV's
    distinct places by normalized (name, address), every place exactly
    once.

THE KEY WITNESS IS LTSB: the app's ward card renders LTSB's statewide
ward fabric, so the pairing is only usable if the city's ward numbers ARE
LTSB's. Measured 2026-08-26: LTSB carries exactly 356 wards for
CTV='C', MCD_NAME='Milwaukee', numbered 1-356 with no gaps — the CSV's
ward set must equal LTSB's exactly, re-fetched every build.

DATED, PER ELECTION: polling places move election to election, so every
record carries the dataset's own last-modified date and the card states
it beside a MyVote link for confirmation. There is no weekly workflow —
re-run this builder when an election approaches (WATCH.md row); the
CKAN resource's modified date moving is the signal.

The milwaukeemaps REST host resets ~1 in 4-8 connections and CKAN's
download 302s to a presigned URL that urllib's redirect-following 403s on
— both measured in the city-tier builds — so everything fetches through
curl with retries, at build time only, never by the app.
"""

import csv
import io
import json
import os
import re
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT = os.path.join(REPO_ROOT, "data", "app", "mke-polling-places.json")

PACKAGE = "https://data.milwaukee.gov/api/3/action/package_show?id=voting-wards"
DATASET_PAGE = "https://data.milwaukee.gov/dataset/voting-wards"
REST_WARDS = ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/"
              "election/election_wards/MapServer/1/query"
              "?where=1%3D1&outFields=WARD,ADDRESS,POLLING_PL"
              "&returnGeometry=false&f=json")
REST_PLACES = ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/"
               "election/election_wards/MapServer/0/query"
               "?where=1%3D1&outFields=ADDRESS,POLLING_PL"
               "&returnGeometry=true&outSR=4326&f=json")
LTSB_WARDS = ("https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/"
              "services/WI_Municipal_Wards_Current/FeatureServer/0/query"
              "?where=MCD_NAME%3D%27Milwaukee%27+AND+CTV%3D%27C%27"
              "&outFields=WARDID&returnGeometry=false"
              "&resultRecordCount=2000&f=json")
BBOX = {"min_lat": 42.8, "max_lat": 43.3, "min_lng": -88.2, "max_lng": -87.8}


def fetch(url, tries=8, timeout=90):
    last = None
    for _ in range(tries):
        try:
            return subprocess.run(
                ["curl", "-sSL", "--fail", "--max-time", str(timeout),
                 "-H", "User-Agent: districtry/1.0 (+https://districtry.com/wi/)",
                 url],
                check=True, capture_output=True).stdout
        except Exception as e:  # noqa: BLE001 — the measured flaky host
            last = e
            time.sleep(2)
    raise last


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def main():
    pkg = json.loads(fetch(PACKAGE))["result"]
    csv_res = next(r for r in pkg["resources"]
                   if r["format"] == "CSV" and "polling" in r["name"].lower())
    as_of = (csv_res.get("last_modified") or "")[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", as_of):
        raise SystemExit("CKAN resource carries no usable last_modified date")

    raw = fetch(csv_res["url"]).decode("utf-8-sig", "replace")
    # bare-CR row terminators (measured): normalize before csv sees it
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    rows = list(csv.DictReader(io.StringIO(text)))
    pairing = {}
    for r in rows:
        ward = (r.get("Ward") or "").strip()
        if not ward.isdigit():
            raise SystemExit("non-numeric ward %r in the CSV" % ward)
        if ward in pairing:
            raise SystemExit("ward %s appears twice in the CSV" % ward)
        rec = {"name": (r.get("Polling Place Name") or "").strip(),
               "address": (r.get("Polling Place Address") or "").strip()}
        if not rec["name"] or not rec["address"]:
            raise SystemExit("ward %s pairs to an empty name or address" % ward)
        for src, dst in (("Main Voter Entrance", "mainEntrance"),
                         ("Accessibility Voter Entrance", "accessibleEntrance"),
                         ("Main Voter Parking", "mainParking"),
                         ("Accessibility Voter Parking", "accessibleParking")):
            v = (r.get(src) or "").strip()
            if v:
                rec[dst] = v
        pairing[ward] = rec

    # ---- key witness: the CSV's ward set must BE LTSB's Milwaukee set ----
    ltsb = json.loads(fetch(LTSB_WARDS))["features"]
    ltsb_ids = {str(int(f["attributes"]["WARDID"])) for f in ltsb}
    if set(pairing) != ltsb_ids:
        only_csv = sorted(set(pairing) - ltsb_ids, key=int)[:8]
        only_ltsb = sorted(ltsb_ids - set(pairing), key=int)[:8]
        raise SystemExit(
            "the city's ward set no longer matches LTSB's Milwaukee wards "
            "(CSV-only: %s; LTSB-only: %s) — a ward filing moved; re-measure "
            "before shipping" % (only_csv, only_ltsb))

    # ---- pairing witness: the REST ward layer must state the same pairs ----
    rest = json.loads(fetch(REST_WARDS))["features"]
    rest_by_ward = {}
    for f in rest:
        a = f["attributes"]
        rest_by_ward[str(int(a["WARD"]))] = (norm(a.get("POLLING_PL")),
                                             norm(a.get("ADDRESS")))
    disagreements = []
    for ward, rec in pairing.items():
        got = rest_by_ward.get(ward)
        want = (norm(rec["name"]), norm(rec["address"]))
        if got != want:
            disagreements.append((ward, want, got))
    if disagreements:
        for ward, want, got in disagreements[:6]:
            print("ward %s: CSV %s vs REST %s" % (ward, want, got),
                  file=sys.stderr)
        raise SystemExit(
            "%d ward(s) pair differently in the CSV and the city's own REST "
            "layer — the two surfaces have desynchronized; do not ship either"
            % len(disagreements))

    # ---- the points: every distinct place, exactly once, inside the city.
    # The city's own layer carries EXACTLY ONE place with null geometry
    # (measured 2026-08-26: Starms Early Childhood Center, 2616 W Garfield
    # Av) — that place's wards ship name + address without a point, printed
    # loudly every build; MORE than the pinned tolerance means the layer
    # degraded and the build refuses. ----
    POINTLESS_OK = 1
    places = json.loads(fetch(REST_PLACES))["features"]
    point_by_place = {}
    for f in places:
        a = f["attributes"]
        key = (norm(a.get("POLLING_PL")), norm(a.get("ADDRESS")))
        g = f.get("geometry") or {}
        lat, lng = g.get("y"), g.get("x")
        if lat is None or lng is None:
            continue  # counted against POINTLESS_OK below, per the pairing
        if not (BBOX["min_lat"] < lat < BBOX["max_lat"]
                and BBOX["min_lng"] < lng < BBOX["max_lng"]):
            raise SystemExit("polling place %r point (%s, %s) is outside "
                             "Milwaukee — outSR was ignored?" % (key, lat, lng))
        point_by_place.setdefault(key, (round(lat, 6), round(lng, 6)))
    missing = {(norm(r["name"]), norm(r["address"])) for r in pairing.values()} \
        - set(point_by_place)
    if len(missing) > POINTLESS_OK:
        raise SystemExit("%d polling place(s) in the pairing have no point in "
                         "the places layer (tolerance %d): %s"
                         % (len(missing), POINTLESS_OK, sorted(missing)[:4]))
    for key in sorted(missing):
        print("no point for %r — its wards ship name + address only (the "
              "city's layer carries this place with null geometry)" % (key,),
              file=sys.stderr)

    if len(pairing) < 300:
        raise SystemExit("only %d wards paired — Milwaukee has had ~356 since "
                         "the 2022 redraw; the dataset shrank, re-measure"
                         % len(pairing))

    out = {}
    for ward, rec in sorted(pairing.items(), key=lambda kv: int(kv[0])):
        rec = dict(rec)
        pt = point_by_place.get((norm(rec["name"]), norm(rec["address"])))
        if pt:
            rec["lat"], rec["lng"] = pt
        rec["asOf"] = as_of
        rec["sourceUrl"] = DATASET_PAGE
        out[ward] = rec

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    n_places = len({(r["name"], r["address"]) for r in out.values()})
    print("wrote %s — %d wards -> %d polling places, dataset edition %s; "
          "ward set equals LTSB's Milwaukee wards exactly, every pair "
          "witnessed against the city's own REST layer, every place pointed "
          "and bbox-gated" % (os.path.relpath(OUT, REPO_ROOT), len(out),
                              n_places, as_of),
          file=sys.stderr)


if __name__ == "__main__":
    main()

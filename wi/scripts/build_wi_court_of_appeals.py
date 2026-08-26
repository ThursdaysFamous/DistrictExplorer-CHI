#!/usr/bin/env python3
"""
Wisconsin Court of Appeals districts — four county unions under a double
witness, the circuit-court derivation one tier up (build_wi_circuit_courts.py
carries the shared dissolve; this file imports it rather than copying it).

No agency publishes Court of Appeals geometry (measured 2026-08-25 alongside
the circuit search), so no new line is drawn: each district is a union of
whole counties from the shipped TIGERweb county file, and the composition
carries a DOUBLE WITNESS that agrees exactly, county for county:

  1. Wis. Stat. 752.11(1)(a)-(d) — text unchanged since 1977 c. 187 — naming
     District I (Milwaukee), II (12 counties), III (35) and IV (24).
  2. wicourts.gov's own appeals page (/courts/appeals/index.htm), which
     prints the same four county lists; the weekly roster scraper re-asserts
     them on every run, so a statutory change fails the scrape loudly.

Judges are ELECTED BY DISTRICT (752.03: one per district per year), which is
what makes this an honest layer where the Supreme Court — elected statewide —
is a recorded n/a.

Gates: exactly 4 features; all 72 counties partitioned exactly once; every
district dissolves to exactly ONE ring (a union of contiguous counties is
simply connected — a second ring means the county file changed under us);
every county's interior point lands in its own district.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_wi_circuit_courts import (  # noqa: E402
    COUNTIES_FILE, dissolve_pair, interior_point, point_in_geom)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_FILE = os.path.join(REPO_ROOT, "data", "app", "wi-court-of-appeals-districts.json")

# Wis. Stat. 752.11(1), cross-witnessed by wicourts.gov/courts/appeals —
# BASENAME spellings as the shipped county file carries them.
DISTRICTS = {
    "1": ["Milwaukee"],
    "2": ["Calumet", "Fond du Lac", "Green Lake", "Kenosha", "Manitowoc",
           "Ozaukee", "Racine", "Sheboygan", "Walworth", "Washington",
           "Waukesha", "Winnebago"],
    "3": ["Ashland", "Barron", "Bayfield", "Brown", "Buffalo", "Burnett",
           "Chippewa", "Door", "Douglas", "Dunn", "Eau Claire", "Florence",
           "Forest", "Iron", "Kewaunee", "Langlade", "Lincoln", "Marathon",
           "Marinette", "Menominee", "Oconto", "Oneida", "Outagamie", "Pepin",
           "Pierce", "Polk", "Price", "Rusk", "Sawyer", "Shawano", "St. Croix",
           "Taylor", "Trempealeau", "Vilas", "Washburn"],
    "4": ["Adams", "Clark", "Columbia", "Crawford", "Dane", "Dodge", "Grant",
           "Green", "Iowa", "Jackson", "Jefferson", "Juneau", "La Crosse",
           "Lafayette", "Marquette", "Monroe", "Portage", "Richland", "Rock",
           "Sauk", "Vernon", "Waupaca", "Waushara", "Wood"],
}
ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV"}
CHAMBERS = {"1": "Milwaukee", "2": "Waukesha", "3": "Wausau", "4": "Madison"}


def build():
    with open(COUNTIES_FILE) as f:
        counties = json.load(f)["features"]
    by_base = {feat["properties"]["BASENAME"]: feat for feat in counties}

    named = [c for members in DISTRICTS.values() for c in members]
    if len(named) != 72 or len(set(named)) != 72:
        raise SystemExit("composition table does not partition 72 counties (%d named)" % len(named))
    missing = set(named) - set(by_base)
    if missing:
        raise SystemExit("composition names counties not in the file: %s" % sorted(missing))

    features = []
    for did in sorted(DISTRICTS):
        members = DISTRICTS[did]
        feats = [by_base[c] for c in members]
        if len(feats) == 1:
            geom = feats[0]["geometry"]
        else:
            geom = dissolve_pair(feats)
            rings = geom["coordinates"] if geom["type"] == "Polygon" \
                else [r for poly in geom["coordinates"] for r in poly]
            if len(rings) != 1:
                raise SystemExit("District %s dissolved to %d rings — a contiguous "
                                 "county union must be one" % (did, len(rings)))
        features.append({
            "type": "Feature",
            "properties": {
                "DISTRICT": did,
                "NAME": "Court of Appeals District %s" % ROMAN[did],
                "CHAMBERS": CHAMBERS[did],
                "COUNTY_COUNT": len(members),
            },
            "geometry": geom,
        })

    by_district = {f["properties"]["DISTRICT"]: f for f in features}
    for did, members in DISTRICTS.items():
        for c in members:
            pt = interior_point(by_base[c])
            if not point_in_geom(pt, by_district[did]["geometry"]):
                raise SystemExit("containment gate: %s's interior point missed District %s"
                                 % (c, did))

    return {"type": "FeatureCollection", "features": features}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    built = build()
    if args.check:
        with open(OUT_FILE) as f:
            shipped = json.load(f)
        if json.dumps(shipped, sort_keys=True) != json.dumps(built, sort_keys=True):
            print("FAIL: shipped wi-court-of-appeals-districts.json differs from a fresh build",
                  file=sys.stderr)
            sys.exit(1)
        print("check: shipped Court of Appeals geometry matches the county file (4 districts)")
        return

    with open(OUT_FILE, "w") as f:
        json.dump(built, f, separators=(",", ":"))
    print("wrote %s — 4 districts (1 + 12 + 35 + 24 counties), %.1f KB"
          % (OUT_FILE, os.path.getsize(OUT_FILE) / 1024.0))


if __name__ == "__main__":
    main()

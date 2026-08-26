#!/usr/bin/env python3
"""
Build data/app/wi-alderpersons.json from wi_alderperson_scraper.py's
intermediate — the aldermanic-district card's roster for the six big cities
whose routes are verified (Milwaukee, Madison, Green Bay, Kenosha, Racine,
Waukesha; 94 seats, 93 filled + Madison's vacant District 1 as of the first
build). Keyed by COUSUBFP + zero-padded district id, the exact key pair the
dissolved geometry carries, and CROSS-GATED against the shipped geometry
file: a roster row naming a district the map does not draw fails the build,
as does a covered city whose district count stops matching its seat count.

Floors are per city and per field, tuned to the measured first run — a city
losing its e-mail column (the Brown County lesson) fails here before the
retention gate ever sees it.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RAW = os.path.join(SCRIPT_DIR, ".cache", "wi_alderpersons_raw.json")
GEOMETRY = os.path.join(REPO_ROOT, "data", "app", "aldermanic-districts.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "wi-alderpersons.json")

# COUSUBFP -> (name, seats, min named, min emails, min phones, min urls)
FLOORS = {
    "53000": ("Milwaukee", 15, 15, 0, 0, 0),
    "48000": ("Madison", 20, 18, 17, 0, 17),
    "31000": ("Green Bay", 12, 12, 10, 9, 10),
    "39225": ("Kenosha", 17, 17, 0, 0, 0),
    "66000": ("Racine", 15, 15, 0, 0, 13),
    "84250": ("Waukesha", 15, 15, 14, 14, 0),
}


def main():
    with open(RAW) as f:
        cities = json.load(f)["cities"]
    with open(GEOMETRY) as f:
        geo = json.load(f)["features"]
    geo_keys = {}
    for feat in geo:
        p = feat["properties"]
        geo_keys.setdefault(p["COUSUBFP"], set()).add(p["ALDERID"])

    if set(cities) != set(FLOORS):
        raise SystemExit("scraper covered %s, floors expect %s"
                         % (sorted(cities), sorted(FLOORS)))
    for k, (name, seats, mn, me, mp, mu) in FLOORS.items():
        c = cities[k]
        ms = c["members"]
        if c["municipality"] != name or c["seats"] != seats:
            raise SystemExit("%s: identity drifted (%r/%r)" % (name, c["municipality"], c["seats"]))
        if k not in geo_keys:
            raise SystemExit("%s (%s) has a roster but no districts in the shipped "
                             "geometry" % (name, k))
        if len(geo_keys[k]) != seats:
            raise SystemExit("%s: geometry draws %d districts, the city seats %d"
                             % (name, len(geo_keys[k]), seats))
        stray = set(ms) - geo_keys[k]
        if stray:
            raise SystemExit("%s: roster names district(s) %s the map does not draw"
                             % (name, sorted(stray)))
        vacant = set("%02d" % v for v in c.get("vacantDistricts", []))
        if set(ms) | vacant != geo_keys[k]:
            raise SystemExit("%s: %d named + %d vacant does not cover the %d districts"
                             % (name, len(ms), len(vacant), len(geo_keys[k])))
        counts = (len(ms),
                  sum(1 for m in ms.values() if m.get("email")),
                  sum(1 for m in ms.values() if m.get("phone")),
                  sum(1 for m in ms.values() if m.get("url")))
        for label, got, floor in zip(("named", "emails", "phones", "urls"),
                                     counts, (mn, me, mp, mu)):
            if got < floor:
                raise SystemExit("%s: only %d %s (floor %d) — the page shape moved"
                                 % (name, got, label, floor))

    with open(OUT, "w") as f:
        json.dump(cities, f, indent=1, ensure_ascii=False, sort_keys=True)
    total = sum(len(c["members"]) for c in cities.values())
    print("wi-alderpersons.json: %d alderpersons across %d cities -> %s"
          % (total, len(cities), os.path.relpath(OUT, REPO_ROOT)))


if __name__ == "__main__":
    main()

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


# How many cities may be CARRIED from the last shipped file in one run before
# this refuses. One unreadable site is a bad afternoon on somebody else's
# server; three at once is this end breaking, and shipping six-week-old rows
# under a current date is exactly what the fleet's dating discipline forbids.
MAX_CARRIED = 2


def carry_forward(cities, failures):
    """A city the scraper could not read keeps the rows it shipped last time.

    Dropping it instead would take real, correct alderpersons off the card
    because a webserver timed out — and the floors below, which are per city,
    would not even notice: they only measure the cities present. The carried
    rows are at most a week old and unchanged since the last human-reviewed PR,
    which is a far smaller claim than an empty card.

    Loud on purpose: every carry prints, and the weekly PR shows no diff for
    that city, which is the honest record of "nothing could be read".
    """
    missing = sorted(set(FLOORS) - set(cities))
    if not missing:
        return cities
    if not os.path.exists(OUT):
        raise SystemExit("%s missed %s and there is no shipped file to carry "
                         "them from" % (RAW, missing))
    with open(OUT) as f:
        shipped = json.load(f)
    carried = []
    for code in missing:
        previous = shipped.get(code)
        reason = (failures.get(code) or {}).get("reason", "no reason recorded")
        if not previous or not previous.get("members"):
            raise SystemExit("%s (%s) could not be read (%s) and has no shipped "
                             "rows to carry — a city cannot enter this file by "
                             "failing" % (FLOORS[code][0], code, reason))
        cities[code] = previous
        carried.append(FLOORS[code][0])
        print("  CARRIED %-12s %d members kept from the last shipped file — %s"
              % (FLOORS[code][0], len(previous["members"]), reason))
    if len(carried) > MAX_CARRIED:
        raise SystemExit("%d of %d cities were unreadable (%s) — that is this "
                         "end failing, not their servers; read the scraper log "
                         "before raising MAX_CARRIED (%d)"
                         % (len(carried), len(FLOORS), ", ".join(carried),
                            MAX_CARRIED))
    return cities


def main():
    with open(RAW) as f:
        raw = json.load(f)
    cities = raw["cities"]
    cities = carry_forward(cities, raw.get("failures") or {})
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

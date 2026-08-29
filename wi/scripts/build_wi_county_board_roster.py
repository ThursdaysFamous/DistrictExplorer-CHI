#!/usr/bin/env python3
"""
Build data/app/county-board-members.json from the county board scraper's
intermediate JSON, keyed by SUPER_FIPS so the card can look a supervisor up
straight from the district feature the map already matched.

The roster is checked against the SHIPPED GEOMETRY rather than against itself:
every county in it must exist in county-supervisory-districts.json, and its
seat count must equal the number of districts actually drawn for that county.
That is what stops a county's page reorganising into a plausible-but-wrong
number of members — the two files were built from different publishers (the
county's own page, and LTSB's statewide filing) and have to agree.

Thirty-three of Wisconsin's 72 counties publish a district-keyed member list;
the other 39 are recorded in the Data gaps panel and their cards keep linking
the county board rather than naming anybody. See the scraper's docstring for
what each of the other 39 actually publishes.

Usage:
    python3 wi/scripts/build_wi_county_board_roster.py
    python3 wi/scripts/build_wi_county_board_roster.py --check
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
GEOMETRY = os.path.join(APP_DATA_DIR, "county-supervisory-districts.json")
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "wi_county_boards_raw.json")
OUT = os.path.join(APP_DATA_DIR, "county-board-members.json")

MIN_COUNTIES = 31      # 33 ship one (29 pages + 2 county GIS layers + Taylor by document + Adams by PDF); tolerates two dark
MIN_SEATS = 680        # 709 today (633 page-scraped + Milwaukee 18 + Racine 21 + Taylor 17 + Adams 20)


def main():
    check_only = "--check" in sys.argv[1:]
    with open(GEOMETRY) as f:
        geo = json.load(f)
    drawn = {}
    names = {}
    for feat in geo["features"]:
        p = feat["properties"]
        drawn.setdefault(p["CNTY_FIPS"], set()).add(int(p["SUPERID"]))
        names[p["CNTY_FIPS"]] = p["CNTY_NAME"]

    with open(RAW) as f:
        raw = json.load(f)
    counties = raw["counties"]
    if len(counties) < MIN_COUNTIES:
        raise RuntimeError("only %d counties scraped, floor is %d — %s"
                           % (len(counties), MIN_COUNTIES, raw.get("failures")))

    roster = {}
    total = vacant = 0
    for fips, entry in sorted(counties.items()):
        if fips not in drawn:
            raise RuntimeError("county %s (%s) has members but no districts in the "
                               "shipped geometry" % (fips, entry["county"]))
        if entry["county"] != names[fips]:
            raise RuntimeError("county %s is %r in the geometry and %r in the roster"
                               % (fips, names[fips], entry["county"]))
        want = drawn[fips]
        got = {int(d) for d in entry["districts"]}
        if got != want:
            raise RuntimeError(
                "%s: the roster covers districts %s and the map draws %s — one of the "
                "two publishers has changed; re-read both before shipping"
                % (entry["county"], sorted(got), sorted(want)))
        for d, member in entry["districts"].items():
            key = "%s%02d" % (fips, int(d))
            row = {"county": entry["county"], "district": int(d),
                   "sourceUrl": entry["source_url"]}
            if member["vacant"]:
                row["vacant"] = True
                vacant += 1
            else:
                row["name"] = member["name"]
                if member["role"]:
                    row["role"] = member["role"]
                # CONTACT RIDES ONLY WHERE ITS COUNTY PUBLISHED IT. The two
                # county-GIS rosters carry an e-mail (and Milwaukee a profile
                # link) on the feature; Taylor's document and Adams's directory
                # carry an e-mail and a phone. The page-scraped counties publish
                # none of it, and an absent field renders nothing rather than a
                # placeholder.
                #
                # `phone` USED TO BE COLLECTED AND SILENTLY DROPPED HERE: the
                # scraper has carried Taylor's seventeen numbers since the day
                # it shipped, its own comment saying a phone is an official
                # contact detail and does ship, and this loop copied `email`
                # and `url` and nothing else. Adding a field to the scraper is
                # not adding it to the app — the two halves have to agree.
                if member.get("email"):
                    row["email"] = member["email"]
                if member.get("phone"):
                    row["phone"] = member["phone"]
                if member.get("url"):
                    row["profileUrl"] = member["url"]
            roster[key] = row
            total += 1

    if total < MIN_SEATS:
        raise RuntimeError("%d seats resolved, floor is %d" % (total, MIN_SEATS))

    payload = json.dumps(roster, indent=1, sort_keys=True) + "\n"
    print("county-board-members: %d counties, %d seats (%d named, %d vacant)"
          % (len(counties), total, total - vacant, vacant), file=sys.stderr)
    if check_only:
        try:
            with open(OUT) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("data/app/county-board-members.json is missing (%s)" % e)
        if shipped != payload:
            raise RuntimeError("data/app/county-board-members.json has drifted from the "
                               "scraper's output — re-run the builder")
        print("check: shipped roster matches", file=sys.stderr)
        return
    with open(OUT, "w") as f:
        f.write(payload)
    print("wrote data/app/county-board-members.json", file=sys.stderr)


if __name__ == "__main__":
    main()

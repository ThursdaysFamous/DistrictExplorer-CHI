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

Thirty-four of Wisconsin's 72 counties publish a district-keyed member list;
the other 38 are recorded in the Data gaps panel and their cards keep linking
the county board rather than naming anybody. See the scraper's docstring for
what each of the other 38 actually publishes.

CONTACT RIDES ONLY WHERE ITS COUNTY PUBLISHED IT, which is why these rows are
not uniform and should not be made uniform. Thirty counties publish a name and
a district and nothing else. Milwaukee and Racine carry an e-mail on their own
GIS features (and Milwaukee a member web page). Kenosha's Clerk prints a phone
AND an e-mail for all 23 seats in the county's own Directory of Public
Officials, and the county's board page links each supervisor's profile — the
fullest rows in the file. Taylor's carried document has both too.

THE PHONE PASSTHROUGH WAS MISSING AND TAYLOR PAID FOR IT: its 17 numbers were
read off the county's directory, carried in the scraper's own table, and
dropped here — published data going nowhere, the same shape as the e-mails
that sat in this file unrendered until the card learned to show them. An
absent field means the county does not publish it; it must never mean this
builder dropped it, and check_roster_retention.py holds that line per source
from the first day a field ships.

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

MIN_COUNTIES = 32      # 34 ship one (30 pages + 2 county GIS layers + Taylor
                       # carried by document + Kenosha witnessed); tolerates two dark
MIN_SEATS = 713        # 742 today (663 page-scraped + Milwaukee 18 + Racine 21
                       # + Taylor 17 + Kenosha 23)


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
                # contact rides only where its county published it (see the
                # docstring) — the two county-GIS rosters carry it on their
                # features, Kenosha's and Taylor's on their counties' own
                # documents, and the 30 page-scraped counties publish none
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

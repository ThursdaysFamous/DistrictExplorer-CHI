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

MIN_COUNTIES = 32      # 34 ship one (31 pages + 2 county GIS layers + Taylor by document); tolerates two dark
MIN_SEATS = 715        # 744 today (688 page-scraped + Milwaukee 18 + Racine 21 + Taylor 17)


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
                    # where the county STATES the role, when that is not the
                    # page the district list came from (Sheboygan names its
                    # chair on the board's landing page, not its roster table)
                    if member.get("role_url"):
                        row["roleSourceUrl"] = member["role_url"]
                # Contact rides only where its county published it: the two
                # county-GIS rosters carry it as feature attributes, Taylor's
                # comes with its document, and Sheboygan's off the page each
                # supervisor has of their own. A supervisor's ADDRESS is never
                # among these even where the county prints one — it is their
                # home, not an office (the scraper's MEMBER_PAGES comment).
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

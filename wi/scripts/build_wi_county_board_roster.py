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

Thirty-four of Wisconsin's 72 counties have a district-keyed member list this
can obtain; the other 38 are recorded in the Data gaps panel and their cards
keep linking the county board rather than naming anybody. See the scraper's
docstring for what each of the other 38 actually publishes.

A COUNTY THAT SHIPPED LAST WEEK MAY NOT VANISH QUIETLY. The scraper is built so
that one county's bad day never fails the run — which is right for the scrape
and wrong for the file, because a county that silently drops out takes its
whole board off the map and leaves a diff that reads like a routine refresh.
The floors below cannot catch it (losing Price's 13 of 748 seats clears both),
and neither can the repo's roster-retention gate, which measures this file
whole because it carries more than 200 top-level keys. So the builder compares
the new roster against the SHIPPED one county by county and refuses to write
when one disappears. Dropping a county on purpose is `--allow-drop <County>`,
which says so on the record instead of in a silence.

Usage:
    python3 wi/scripts/build_wi_county_board_roster.py
    python3 wi/scripts/build_wi_county_board_roster.py --check
    python3 wi/scripts/build_wi_county_board_roster.py --allow-drop Rock
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
MIN_SEATS = 719        # 748 today (692 page-scraped + Milwaukee 18 + Racine 21 + Taylor 17)


def shipped_counties():
    """{county name: seats} as the file on disk has them, or {} if it is new."""
    try:
        with open(OUT) as f:
            shipped = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for row in shipped.values():
        out[row["county"]] = out.get(row["county"], 0) + 1
    return out


def main():
    argv = sys.argv[1:]
    check_only = "--check" in argv
    allowed_drops = {argv[i + 1] for i, a in enumerate(argv) if a == "--allow-drop"}
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
                # the two county-GIS rosters carry contact on the feature —
                # fields the page-scraped counties never publish; each rides
                # only where its county published it
                if member.get("email"):
                    row["email"] = member["email"]
                if member.get("url"):
                    row["profileUrl"] = member["url"]
            roster[key] = row
            total += 1

    if total < MIN_SEATS:
        raise RuntimeError("%d seats resolved, floor is %d" % (total, MIN_SEATS))

    # See the docstring: the floors above are a fleet-sized net, and one county
    # falling out of a 34-county file slips straight through it.
    was = shipped_counties()
    gone = sorted(set(was) - {e["county"] for e in counties.values()} - allowed_drops)
    if gone:
        raise RuntimeError(
            "%s shipped last time and resolved nothing this time (%s) — that is a "
            "page to re-read, not a diff to merge; pass --allow-drop to drop a "
            "county deliberately"
            % (", ".join("%s (%d seats)" % (c, was[c]) for c in gone),
               raw.get("failures") or "no failure recorded"))

    for fips, entry in sorted(counties.items()):
        # A county read from anywhere but its own live page says so on the log,
        # so the weekly PR's reviewer can see which rung of the ladder answered.
        read_from = entry.get("read_from", "live")
        if read_from.startswith("archive:"):
            print("  %s: read from the Internet Archive capture of %s"
                  % (entry["county"], read_from.split(":", 1)[1][:8]), file=sys.stderr)

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

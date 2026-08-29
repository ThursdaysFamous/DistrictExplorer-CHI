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
project can carry; the other 38 are recorded in the Data gaps panel and their
cards keep linking the county board rather than naming anybody. See the
scraper's docstring for what each of them actually publishes.

TWO OF THE THIRTY-FOUR ARE CARRIED FROM A DOCUMENT, NOT RE-READ WEEKLY, AND
THE CARD HAS TO SAY SO. Taylor's host answers a captcha and Lafayette's a
Cloudflare challenge, so their rows come from a dated capture of each county's
own page. The scraper marks those counties `carried_from_document` with the
day they were read; this builder turns that into an `asOf` on every one of
their rows, and the card prints it rather than letting a dated snapshot read
like the weekly re-read the other thirty-two get. A county whose live page
answers on a later run loses the flag in the scraper, so the field disappears
here by itself.

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

MIN_COUNTIES = 32      # 34 ship one (30 pages + 2 county GIS layers + Taylor and
                       # Lafayette by document); tolerates two of the live ones dark
MIN_SEATS = 706        # 735 today (663 page-scraped + Milwaukee 18 + Racine 21
                       # + Taylor 17 + Lafayette 16)


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
            # Present only for a county the scraper marked as carried from a
            # document rather than read this run. `sourceUrl` is still the
            # page the names came from, so the pair is the whole provenance a
            # reader needs; the exact route lives in the scraper's
            # DOCUMENT_ROSTERS entry and on its NOT RE-READ line.
            if entry.get("carried_from_document"):
                row["asOf"] = "the county's own page, captured %s" % entry["read_on"]
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
    dated = sorted({r["county"] for r in roster.values() if r.get("asOf")})
    print("county-board-members: %d counties, %d seats (%d named, %d vacant)%s"
          % (len(counties), total, total - vacant, vacant,
             "; carried from a document: %s" % ", ".join(dated) if dated else ""),
          file=sys.stderr)
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

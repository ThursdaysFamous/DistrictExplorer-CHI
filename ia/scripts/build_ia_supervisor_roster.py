#!/usr/bin/env python3
"""
Build data/app/ia-supervisor-members.json -- which supervisor holds each county
supervisor district, keyed by 3-digit county FIPS (the same key
ia-county-board-directory.json uses) and read by ia/index.html's County
Supervisor District card.

WHAT IT IS FOR
---------------
data/app/ia-county-officers.json names every county's board but cannot say who
holds WHICH district, because no Iowa publisher attaches a district to a
supervisor's name (four statewide routes measured closed -- see
ia_supervisor_district_scraper.py). This file carries that one missing number
for the counties that publish it themselves, so the district card can name the
supervisor a reader actually elected instead of linking away to a board page.

PLAN 3 COUNTIES ONLY. Iowa Code 331.206: under plan 1 a county elects at large
with no districts, and under plan 2 supervisors are elected COUNTYWIDE and
merely reside in a district. Only under plan 3 does a district elect its own
supervisor, so only there does naming one answer a question the County card's
list does not already answer. Keying a plan 2 district would read as
district-based election, which is precisely what plan 2 is not.

THE PEOPLE COME FROM THE SHIPPED ROSTER, NOT FROM THE COUNTY PAGE. The scraper
recovers only a NUMBER; every name and party here is carried over from
data/app/ia-county-officers.json, which was itself gated against Iowa Code
331.201's legal board sizes and against the seat count in the shipped district
geometry. So a county page cannot introduce a person, only place one -- and
this builder re-checks that placement rather than trusting it:

  * every district 1..N is filled, exactly once,
  * the set of people placed is EXACTLY the set the roster names, and
  * N equals NUMDISTRICTS in data/app/ia-supervisor-districts.json.

A county failing any of these ships nothing and is named in the run's output;
its supervisors keep the unkeyed listing they already have on the County card.
NEVER infer a district from the order a page lists people in -- that is the one
failure mode that produces a complete, confident, wrong answer.

NO PHONE RIDES A SUPERVISOR ROW. Every one of these 17 counties publishes ONE
number for the whole board -- measured, one distinct value per county across
all 67 keyed districts -- which is the courthouse board office, not a
supervisor's line. build_ia_county_officers.py already hoists that number out
of its own member rows into `boardPhone`; this file carries the same field at
COUNTY level so the district card can print it as "Board office" instead of
presenting the switchboard as the direct line of whichever supervisor the
reader's district elected. A per-person number is a different fact and would
have to arrive from a source that publishes one; the officer roster this reads
from carries none, so none can leak through.

Usage:
    python3 ia/scripts/ia_supervisor_district_scraper.py   # refresh the cache
    python3 ia/scripts/build_ia_supervisor_roster.py
    python3 ia/scripts/build_ia_supervisor_roster.py --check
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache",
                     "ia_supervisor_districts_roster.json")

DISTRICTS = os.path.join(APP_DATA_DIR, "ia-supervisor-districts.json")
OFFICERS = os.path.join(APP_DATA_DIR, "ia-county-officers.json")
OUT = os.path.join(APP_DATA_DIR, "ia-supervisor-members.json")

# Floor, not a target: 20 of the 39 plan 3 counties published a keyable page on
# 2026-08-28 (the rest 403, sit behind a captcha, or name no district at all).
MIN_COUNTIES = 12
MIN_DISTRICTS = 40


def load(path, what):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError as e:
        raise RuntimeError("no %s at %s (%s)" % (what, path, e))


def main():
    check_only = "--check" in sys.argv[1:]

    feats = load(DISTRICTS, "supervisor districts")["features"]
    fips_by_county, seats_by_county, plan_by_county = {}, {}, {}
    for feat in feats:
        p = feat["properties"]
        fips_by_county[p["COUNTY"]] = p["FIPS"]
        seats_by_county[p["COUNTY"]] = p.get("NUMDISTRICTS")
        plan_by_county[p["COUNTY"]] = p.get("PLANTYPE")

    officers = load(OFFICERS, "county officers")
    board_by_county, board_phone_by_county = {}, {}
    for rec in officers.values():
        if rec.get("supervisors"):
            board_by_county[rec["county"]] = rec["supervisors"]
        if rec.get("boardPhone"):
            board_phone_by_county[rec["county"]] = rec["boardPhone"]

    cache = load(CACHE, "supervisor district cache -- run the scraper first")

    directory, skipped = {}, []
    for county in sorted(cache):
        entry = cache[county]
        keyed = entry.get("districts") or {}
        board = board_by_county.get(county)
        if not board:
            skipped.append((county, "no gated supervisor list"))
            continue
        if plan_by_county.get(county) != "PLAN 3":
            skipped.append((county, "not a plan 3 county (%s)" % plan_by_county.get(county)))
            continue

        by_name = {m["name"]: m for m in board}
        placed = list(keyed.values())
        # every district 1..N filled exactly once
        want = [str(i) for i in range(1, len(board) + 1)]
        if sorted(keyed, key=lambda k: int(k)) != want:
            skipped.append((county, "districts %s are not 1..%d"
                            % (sorted(keyed), len(board))))
            continue
        # the people placed are EXACTLY the people the roster names
        if sorted(placed) != sorted(by_name):
            skipped.append((county, "placed %s but the roster names %s"
                            % (sorted(placed), sorted(by_name))))
            continue
        seats = seats_by_county.get(county)
        if seats is not None and seats != len(board):
            skipped.append((county, "roster names %d, geometry seats %d"
                            % (len(board), seats)))
            continue

        members = {}
        for dist, name in keyed.items():
            src = by_name[name]
            row = {"name": name}
            if src.get("party"):
                row["party"] = src["party"]
            # src carries no phone by construction (the officer builder hoists
            # the shared board number out of its member rows). Should a source
            # ever start publishing a genuine per-supervisor line, it has to be
            # let through deliberately rather than inherited by this loop.
            if src.get("phone"):
                raise RuntimeError(
                    "%s names a phone on supervisor %s -- a per-person number "
                    "is a new fact here. Confirm it is that supervisor's line "
                    "and not the board switchboard before shipping it."
                    % (county, name))
            members[dist] = row
        rec = {
            "county": county,
            "districts": members,
            "sourceUrl": entry.get("sourceUrl"),
        }
        # The board office's own number, county-level and labelled as such on
        # the card. One number shared by every supervisor is a switchboard.
        if board_phone_by_county.get(county):
            rec["boardPhone"] = board_phone_by_county[county]
        directory[fips_by_county[county]] = rec

    # The scraper caps the name-to-district gap at PROXIMITY_CHARS, so this is
    # a tripwire rather than a second gate: counties publish this pairing
    # adjacently (max 42 characters measured across 67 districts), and a run
    # where the widest gap creeps toward the cap is the signal that assumption
    # has stopped holding somewhere.
    widest = max([cache[c].get("maxGap", 0) for c in cache] or [0])

    total_districts = sum(len(v["districts"]) for v in directory.values())
    if len(directory) < MIN_COUNTIES or total_districts < MIN_DISTRICTS:
        raise RuntimeError(
            "only %d counties / %d districts keyed (floors %d / %d) -- re-run the "
            "scraper and read its skip reasons before loosening anything"
            % (len(directory), total_districts, MIN_COUNTIES, MIN_DISTRICTS))

    # Structural refusal: only these two fields may ship on a person. No
    # address, ever -- and no phone, because the only number any of these
    # publishers gives is the board office's, which rides the county level.
    for fips, rec in directory.items():
        for dist, row in rec["districts"].items():
            extra = set(row) - {"name", "party"}
            if extra:
                raise RuntimeError("%s district %s carries %s -- only "
                                   "name/party may ship on a supervisor"
                                   % (fips, dist, sorted(extra)))

    print("ia-supervisor-members: %d plan 3 counties, %d districts keyed, %d "
          "skipped | widest name-to-district gap %d chars"
          % (len(directory), total_districts, len(skipped), widest), file=sys.stderr)
    for county, why in skipped:
        print("  skipped %-14s %s" % (county, why), file=sys.stderr)

    payload = json.dumps(directory, indent=1, sort_keys=True) + "\n"
    if check_only:
        try:
            with open(OUT) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("data/app/ia-supervisor-members.json is missing (%s)" % e)
        if shipped != payload:
            raise RuntimeError("data/app/ia-supervisor-members.json has drifted from "
                               "the cache. Re-run: python3 "
                               "ia/scripts/build_ia_supervisor_roster.py")
        print("check: shipped roster matches the cache", file=sys.stderr)
        return

    with open(OUT, "w") as f:
        f.write(payload)
    print("wrote data/app/ia-supervisor-members.json", file=sys.stderr)


if __name__ == "__main__":
    main()

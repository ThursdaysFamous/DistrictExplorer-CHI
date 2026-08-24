#!/usr/bin/env python3
"""
Write data/app/mcdonough-county-board-members.json from the intermediate JSON
mcdonough_county_board_scraper.py produces.

Shape matches every other county board roster the app ships: one entry per
district, each holding its members and the URL the card links.

    { "1": { "members": [ {name, party, phone, email, termExpires, role} ],
             "sourceUrl": "..." }, ... }

COUNT GUARDS. McDonough seats 21 members, seven from each of three districts,
and the district composition this roster sits beside is a perfect partition of
the county's 27 precincts — so the numbers here are known exactly rather than
approximately. The floors are still floors and not equalities, because a board
can carry a vacancy without being broken, but they sit only three under the
full set: a run that resolved 18 members is a parse regression, not turnover.

NO ADDRESSES REACH THIS FILE. The county's page prints every member's home
address; the scraper never carries one forward, and this builder asserts that
by refusing to write any field whose name looks like an address. That is a
belt-and-braces check on a rule that matters more than the data it guards.

Usage:
    python3 scripts/build_mcdonough_board_roster.py mcdonough_board_raw.json
    python3 scripts/build_mcdonough_board_roster.py raw.json --check
"""

import argparse
import collections
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app",
                        "mcdonough-county-board-members.json")

MIN_MEMBERS = 18
EXPECTED_DISTRICTS = ("1", "2", "3")
SEATS_PER_DISTRICT = 7
# Any key matching one of these would be a residence leaking into shipped data.
FORBIDDEN_KEY_PARTS = ("address", "addr", "street", "residence", "home")


def build(payload):
    members = payload.get("members") or []
    if len(members) < MIN_MEMBERS:
        raise RuntimeError("%d members < floor %d — refusing to write"
                           % (len(members), MIN_MEMBERS))

    by_district = collections.defaultdict(list)
    for member in members:
        district = str(member.get("district") or "").strip()
        name = (member.get("name") or "").strip()
        if not district or not name:
            raise RuntimeError("a member row carries no district or no name: %r"
                               % member)
        record = {"name": name}
        if member.get("party"):
            record["party"] = member["party"]
        if member.get("phone"):
            record["phone"] = member["phone"]
        if member.get("email"):
            record["email"] = member["email"]
        if member.get("term_expires"):
            record["termExpires"] = int(member["term_expires"])
        if member.get("role"):
            record["role"] = member["role"]
        for key in record:
            if any(part in key.lower() for part in FORBIDDEN_KEY_PARTS):
                raise RuntimeError("field %r would ship a residence — the county "
                                   "publishes members' home addresses and this "
                                   "app does not collect them" % key)
        by_district[district].append(record)

    missing = [d for d in EXPECTED_DISTRICTS if d not in by_district]
    if missing:
        raise RuntimeError("no members resolved for district(s) %s"
                           % ", ".join(missing))
    for district, records in by_district.items():
        records.sort(key=lambda r: r["name"].rsplit(" ", 1)[-1])
        if len(records) > SEATS_PER_DISTRICT:
            raise RuntimeError("district %s resolved %d members but the board "
                               "seats %d per district — rows are probably being "
                               "read under the wrong heading"
                               % (district, len(records), SEATS_PER_DISTRICT))

    return {district: {"members": records,
                       "sourceUrl": payload.get("source_url")}
            for district, records in sorted(by_district.items(), key=lambda kv: int(kv[0]))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", help="mcdonough_county_board_scraper.py output")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.raw, encoding="utf-8") as f:
            payload = json.load(f)
        roster = build(payload)
    except Exception as exc:  # noqa: BLE001
        print("FATAL: %s" % exc, file=sys.stderr)
        sys.exit(1)

    text = json.dumps(roster, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.check:
        if not os.path.exists(OUT_PATH):
            print("FAIL: %s is missing" % OUT_PATH, file=sys.stderr)
            sys.exit(1)
        with open(OUT_PATH, encoding="utf-8") as f:
            if f.read() != text:
                print("FAIL: %s does not match a rebuild from %s"
                      % (OUT_PATH, args.raw), file=sys.stderr)
                sys.exit(1)
        print("build-mcdonough-board-roster: OK — shipped file matches")
        return

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    total = sum(len(v["members"]) for v in roster.values())
    tagged = [m["role"] + ": " + m["name"] for v in roster.values()
              for m in v["members"] if m.get("role")]
    print("wrote %s: %d members across %d districts (%s)%s"
          % (OUT_PATH, total, len(roster),
             ", ".join("D%s=%d" % (d, len(v["members"]))
                       for d, v in sorted(roster.items(), key=lambda kv: int(kv[0]))),
             ("; " + ", ".join(sorted(tagged))) if tagged else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

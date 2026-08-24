#!/usr/bin/env python3
"""
Write data/app/stark-county-board-members.json from the intermediate JSON
stark_county_board_scraper.py produces.

Shape matches every other county board roster the app ships: one entry per
district, each holding its members and the URL the card links.

    { "1": { "members": [ {name, email, termExpires, role} ],
             "sourceUrl": "..." }, ... }

WHAT MAKES STARK'S ROSTER UNUSUAL: the e-mail addresses belong to the SEAT, not
the person — `boarddist1-1@starkco.illinois.gov` through
`boarddist2-4@starkco.illinois.gov`. A county of 5,300 people bothering to run
positional mailboxes is better practice than most of the fleet manages, and it
means these addresses stay correct through turnover. EMAIL_SHAPE_RE asserts the
pattern holds, because a personal address appearing in that slot would be a
change in county policy worth a human look, not something to ship quietly.

COUNT GUARDS. The board seats eight members, four from each of two districts,
and that count is pinned independently: the county's own map splits the county
into exactly two board districts, and this builder refuses to write more than
SEATS_PER_DISTRICT names into either. The floor sits two under the full board so
a genuine vacancy does not fail a Thursday run.

NO ADDRESSES REACH THIS FILE. Stark does not publish member home addresses, so
unlike McDonough there is nothing to strip — but the same belt-and-braces
assertion runs anyway, so that the day the county starts publishing them, the
build fails rather than the app quietly shipping them.

Usage:
    python3 scripts/build_stark_board_roster.py stark_board_raw.json
    python3 scripts/build_stark_board_roster.py stark_board_raw.json --check
"""

import argparse
import collections
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app",
                        "stark-county-board-members.json")

MIN_MEMBERS = 6
EXPECTED_DISTRICTS = ("1", "2")
SEATS_PER_DISTRICT = 4
EMAIL_SHAPE_RE = re.compile(r"(?i)^boarddist(\d)-(\d)@starkco\.illinois\.gov$")
# Any key matching one of these would be a residence leaking into shipped data.
FORBIDDEN_KEY_PARTS = ("address", "addr", "street", "residence", "home")
YEAR_RE = re.compile(r"(20\d\d)")


def build(payload):
    members = payload.get("members") or []
    if len(members) < MIN_MEMBERS:
        raise RuntimeError("%d members < floor %d — refusing to write"
                           % (len(members), MIN_MEMBERS))

    by_district = collections.defaultdict(list)
    off_pattern = []
    for member in members:
        district = str(member.get("district") or "").strip()
        name = (member.get("name") or "").strip()
        if not district or not name:
            raise RuntimeError("a member row carries no district or no name: %r"
                               % member)

        record = {"name": name}
        email = (member.get("email") or "").strip()
        if email:
            shape = EMAIL_SHAPE_RE.match(email)
            if not shape:
                off_pattern.append("%s <%s>" % (name, email))
            elif shape.group(1) != district:
                raise RuntimeError(
                    "%s sits in district %s but holds the district %s mailbox "
                    "(%s) — the roster and the seat numbering disagree"
                    % (name, district, shape.group(1), email))
            record["email"] = email
        if member.get("phone"):
            record["phone"] = member["phone"].strip()
        term = (member.get("term_expires") or "").strip()
        if term:
            year = YEAR_RE.search(term)
            record["termExpires"] = int(year.group(1)) if year else term
        if member.get("role"):
            # the page writes "Board Chair" / "Board Vice-Chair"; the cards
            # already sit under a board heading, so drop the redundant word
            record["role"] = re.sub(r"(?i)^board\s+", "", member["role"]).strip()

        for key in record:
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise RuntimeError("refusing to ship field %r for %s — member "
                                   "home addresses never reach data/app/"
                                   % (key, name))
        by_district[district].append(record)

    if off_pattern:
        raise RuntimeError(
            "these seats no longer use the county's positional mailboxes: %s. "
            "Stark gives each seat its own address rather than the member their "
            "own, so a personal address here is a policy change worth checking "
            "before it ships." % "; ".join(off_pattern))

    missing = [d for d in EXPECTED_DISTRICTS if d not in by_district]
    if missing:
        raise RuntimeError("no members for district(s) %s" % ", ".join(missing))
    unexpected = [d for d in by_district if d not in EXPECTED_DISTRICTS]
    if unexpected:
        raise RuntimeError("unknown district(s) %s — Stark's map has exactly "
                           "two board districts" % ", ".join(sorted(unexpected)))
    for district, records in sorted(by_district.items()):
        if len(records) > SEATS_PER_DISTRICT:
            raise RuntimeError("district %s has %d members but seats %d"
                               % (district, len(records), SEATS_PER_DISTRICT))

    source_url = payload.get("source_url") or ""
    out = {}
    for district, records in by_district.items():
        records.sort(key=lambda r: r["name"].rsplit(" ", 1)[-1].lower())
        out[district] = {"members": records, "sourceUrl": source_url}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", help="intermediate JSON from the scraper")
    parser.add_argument("--check", action="store_true",
                        help="compare against the shipped file; write nothing")
    args = parser.parse_args()

    with open(args.raw, encoding="utf-8") as handle:
        payload = json.load(handle)

    out = build(payload)
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"

    existing = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as handle:
            existing = handle.read()

    if args.check:
        if existing != text:
            sys.exit("drift: %s differs from what the scrape builds" % OUT_PATH)
        print("--check: %s matches" % OUT_PATH)
        return

    if existing == text:
        print("no change")
        return

    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(text)
    total = sum(len(v["members"]) for v in out.values())
    print("wrote %s — %d members across %d districts (%s)"
          % (OUT_PATH, total, len(out),
             ", ".join("D%s=%d" % (d, len(out[d]["members"]))
                       for d in sorted(out, key=int))))


if __name__ == "__main__":
    main()

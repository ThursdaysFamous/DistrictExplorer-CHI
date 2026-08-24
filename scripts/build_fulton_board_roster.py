#!/usr/bin/env python3
"""
Write data/app/fulton-county-board-members.json from the intermediate JSON
fulton_county_board_scraper.py produces.

Shape matches every other county board roster the app ships: one entry per
district, each holding its members and the URL the card links.

    { "1": { "members": [ {name, party, email, termExpires, role} ],
             "sourceUrl": "..." }, ... }

COUNT GUARDS. Fulton seats FIFTEEN members, five from each of three districts,
and the county states that arithmetic itself on the same page ("Five Fulton
County Board members are elected in each of the three districts"). So the
per-district ceiling is an equality the county asserts, not an inference, and
exceeding it means the page's Chairman feature was swept in as a sixteenth seat.
The floor sits three under the full board so a vacancy does not fail a run.

THE CHAIR AND VICE-CHAIR ARE DISTRICT MEMBERS, not countywide seats — Fulton
chooses both from among the fifteen — so they ride their own district's rows
with a role badge rather than appearing as extra people. That is the Grundy
shape, not the DuPage/McHenry countywide-chairman shape.

NO ADDRESSES REACH THIS FILE. Fulton publishes none, and the belt-and-braces
assertion runs anyway so that the day it starts, the build fails rather than the
app quietly shipping them.

Usage:
    python3 scripts/build_fulton_board_roster.py fulton_board_raw.json
    python3 scripts/build_fulton_board_roster.py fulton_board_raw.json --check
"""

import argparse
import collections
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app",
                        "fulton-county-board-members.json")

MIN_MEMBERS = 12
EXPECTED_DISTRICTS = ("1", "2", "3")
SEATS_PER_DISTRICT = 5
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
            record["party"] = member["party"].strip()
        if member.get("email"):
            record["email"] = member["email"].strip()
        if member.get("phone"):
            record["phone"] = member["phone"].strip()
        if member.get("term_expires"):
            record["termExpires"] = int(member["term_expires"])
        if member.get("role"):
            record["role"] = member["role"].strip()

        for key in record:
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise RuntimeError("refusing to ship field %r for %s — member "
                                   "home addresses never reach data/app/"
                                   % (key, name))
        by_district[district].append(record)

    missing = [d for d in EXPECTED_DISTRICTS if d not in by_district]
    if missing:
        raise RuntimeError("no members for district(s) %s" % ", ".join(missing))
    unexpected = [d for d in by_district if d not in EXPECTED_DISTRICTS]
    if unexpected:
        raise RuntimeError("unknown district(s) %s — Fulton has exactly three"
                           % ", ".join(sorted(unexpected)))
    for district, records in sorted(by_district.items()):
        if len(records) > SEATS_PER_DISTRICT:
            raise RuntimeError(
                "district %s has %d members but Fulton seats %d per district — "
                "the Members page's Chairman feature is a ROLE and must not be "
                "counted as a seat" % (district, len(records), SEATS_PER_DISTRICT))

    chairs = [r["name"] for rs in by_district.values() for r in rs
              if (r.get("role") or "").lower() == "chair"]
    if len(chairs) > 1:
        raise RuntimeError("more than one Chair badged: %s" % ", ".join(chairs))

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
                       for d in sorted(out))))


if __name__ == "__main__":
    main()

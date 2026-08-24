#!/usr/bin/env python3
"""
Resolve scripts/jackson_county_board_scraper.py's raw output into
data/app/jackson-county-board-members.json, keyed by Jackson County Board
district (7 districts electing TWO members each = 14 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/jackson-county-board-districts.json by district
number.

THE TWO-SURFACE CHECK IS THE POINT. The county states each member's district
twice — once as the heading that groups them on the board page, once as a field
on their own staff-directory entry — and this fails the run when the two
disagree rather than choosing a winner. That is the Coles rule applied to a
county that happens to agree with itself today: a directory that starts naming a
different district than the page's grouping is a thing a human should see, not a
thing a parser should silently resolve.

WHAT SHIPS: name, district, the county e-mail address, and the Chair's and Vice
Chair's roles. WHAT DOES NOT: party, phone, address, and the term length. The
directory publishes "2 Year Term" and "4 Year Term" but never a start or end
date, and a term that cannot be placed in time tells a reader nothing about
whether this member is in their first year or their last.

Usage:
    python3 build_jackson_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_jackson_boundaries import (SEATS_PER_DISTRICT,  # noqa: E402
                                      WHOLE_PRECINCTS)
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

BOARD_URL = "https://jacksoncounty-il.gov/158/County-Board"

EXPECT_DISTRICTS = 7
EXPECT_MEMBERS = EXPECT_DISTRICTS * SEATS_PER_DISTRICT      # 14 seats
MIN_EMAILS = 12         # measured 14/14; a directory that stops publishing them fails

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("jackson-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_jackson_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in raw.get("records") or []:
        dnum = str(rec.get("district") or "")
        if dnum not in WHOLE_PRECINCTS:
            fail("the board page names a district %r that does not exist" % dnum)
        seen = rec.get("directoryDistrict")
        if seen and str(seen) != dnum:
            fail("%s is grouped under District %s on the board page and District %s "
                 "on their own directory entry — the county's two surfaces disagree "
                 "and a human should decide which is right"
                 % (rec.get("name"), dnum, seen))
        member = {"name": re.sub(r"\s+", " ", rec["name"]).strip()}
        if rec.get("role"):
            member["role"] = rec["role"]
        if rec.get("email"):
            member["email"] = rec["email"]
        entry = roster.setdefault(dnum, {"members": [], "sourceUrl": BOARD_URL})
        entry["members"].append(member)

    if len(roster) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d" % (len(roster), EXPECT_DISTRICTS))
    total = sum(len(v["members"]) for v in roster.values())
    if total != EXPECT_MEMBERS:
        fail("parsed %d members, expected exactly %d (7 districts of %d)"
             % (total, EXPECT_MEMBERS, SEATS_PER_DISTRICT))
    for dnum, entry in roster.items():
        if len(entry["members"]) != SEATS_PER_DISTRICT:
            fail("district %s carries %d member(s), expected %d"
                 % (dnum, len(entry["members"]), SEATS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"])
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry an e-mail (floor %d) — the staff directory "
             "changed shape" % (emails, EXPECT_MEMBERS, MIN_EMAILS))
    roles = [m for v in roster.values() for m in v["members"] if m.get("role")]
    chairs = [m for m in roles if m["role"] == "Chair"]
    vices = [m for m in roles if m["role"] == "Vice Chair"]
    if len(chairs) > 1 or len(vices) > 1:
        fail("the page badges %d chair(s) and %d vice chair(s) — expected at most "
             "one of each" % (len(chairs), len(vices)))

    out_path = os.path.join(out_dir, "jackson-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("jackson-board-roster: wrote %s — %d districts x %d seats (%d e-mails), "
          "chair %s, vice chair %s"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS, SEATS_PER_DISTRICT,
             emails, chairs[0]["name"] if chairs else "not marked",
             vices[0]["name"] if vices else "not marked"))


if __name__ == "__main__":
    main()

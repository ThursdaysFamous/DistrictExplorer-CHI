#!/usr/bin/env python3
"""
Resolve scripts/peoria_county_board_scraper.py's raw output into
data/app/peoria-county-board-members.json, keyed by board district.

Peoria seats 18 SINGLE-member districts — the fleet's largest single-member
county board — so every district key holds exactly one member. The county
publishes a party for all 18 and an e-mail for all 18; phones are per-member
and about two thirds publish one.

The Chairperson and Vice-Chairperson are marked on the member who holds each
role. Both also hold a district seat (Peoria elects them from among the 18),
so the role rides that member's district row rather than becoming a separate
countywide entry — and it is written only where the county's own index page
states it.

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it to the live county GIS boundary
(2020_County_Board_Districts, the adopted 2021-11-30 map) by district number.

Usage:
    python3 build_peoria_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.peoriacounty.gov/755/County-Board-Members"

# 18 single-member districts. The county publishes an e-mail on every row and
# a party on every row; refuse to overwrite good data with a partial scrape.
EXPECT_DISTRICTS = tuple(str(n) for n in range(1, 19))
MEMBERS_PER_DISTRICT = 1
MIN_PHONES = 9
MIN_EMAILS = 16
MIN_PARTIES = 16
ALLOWED_ROLES = ("Chairperson", "Vice-Chairperson")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("peoria-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_peoria_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in records:
        if not rec.get("name") or not rec.get("district"):
            continue
        d = str(rec["district"])
        role = rec.get("role")
        if role and role not in ALLOWED_ROLES:
            fail("district %s carries unrecognized role %r — the index page's "
                 "wording changed; check it before shipping" % (d, role))
        member = {"name": rec["name"]}
        for key in ("party", "role", "phone", "email"):
            if rec.get(key):
                member[key] = rec[key]
        if rec.get("url") and re.match(r"^https://", rec["url"]):
            member["url"] = rec["url"]
        roster.setdefault(d, {"members": [], "sourceUrl": SOURCE_URL})
        roster[d]["members"].append(member)

    if sorted(roster, key=int) != sorted(EXPECT_DISTRICTS, key=int):
        fail("parsed districts %s, expected exactly 1-18"
             % sorted(roster, key=lambda x: int(x)))
    for d, entry in roster.items():
        if len(entry["members"]) != MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, Peoria's districts each seat exactly %d"
                 % (d, len(entry["members"]), MEMBERS_PER_DISTRICT))

    members = [m for e in roster.values() for m in e["members"]]
    phones = sum(1 for m in members if m.get("phone"))
    emails = sum(1 for m in members if m.get("email"))
    parties = sum(1 for m in members if m.get("party"))
    if phones < MIN_PHONES:
        fail("only %d phones resolved (expected >= %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d e-mails resolved (expected >= %d)" % (emails, MIN_EMAILS))
    if parties < MIN_PARTIES:
        fail("only %d parties resolved (expected >= %d)" % (parties, MIN_PARTIES))

    # Exactly one Chairperson and one Vice-Chairperson, or none at all (the
    # index page is the only surface that marks them; if it stops, the cards
    # simply carry no role rather than guessing one).
    for role in ALLOWED_ROLES:
        held = [m["name"] for m in members if m.get("role") == role]
        if len(held) > 1:
            fail("%d members marked %s (%s) — the board has one" % (len(held), role, ", ".join(held)))

    out_path = os.path.join(out_dir, "peoria-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    roles = sorted(m["role"] for m in members if m.get("role"))
    print("peoria-board-roster: %d districts, %d members (%d phones, %d e-mails, "
          "%d parties, roles: %s) -> %s"
          % (len(roster), len(members), phones, emails, parties,
             ", ".join(roles) or "none", out_path))


if __name__ == "__main__":
    main()

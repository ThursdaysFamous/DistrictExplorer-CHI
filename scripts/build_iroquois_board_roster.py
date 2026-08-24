#!/usr/bin/env python3
"""
Resolve scripts/iroquois_county_board_scraper.py's raw output into
data/app/iroquois-county-board-members.json, keyed by board district.

Iroquois seats 16 members across 4 districts, four each, and elects its
Chairman and Vice Chairman from among them — so both roles ride their own
member's district row rather than becoming countywide entries.

The district key is the INTEGER the county's GIS uses, converted from the
Roman numeral the roster table prints; the scraper refuses anything outside
I-IV, so a renumbering fails the build instead of silently dropping seats.

Note on e-mail domains: several members publish a personal address
(gmail/icloud/protonmail) rather than a county one. That is what the county
prints as the member's own contact, so it ships as published — inventing a
county-style address would be worse.

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it to the live county GIS boundary
(CountyBoardDistricts_REACH) by district number.

Usage:
    python3 build_iroquois_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://iroquoiscountyil.gov/offices/county-board"

EXPECT_DISTRICTS = ("1", "2", "3", "4")
MEMBERS_PER_DISTRICT = 4
MIN_PHONES = 13
MIN_EMAILS = 12
ALLOWED_ROLES = ("Chairman", "Vice-Chairman")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("iroquois-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_iroquois_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in records:
        if not rec.get("name") or rec.get("district") is None:
            continue
        role = rec.get("role")
        if role and role not in ALLOWED_ROLES:
            fail("%s carries unrecognized role %r" % (rec["name"], role))
        member = {"name": rec["name"]}
        for key in ("role", "phone", "email"):
            if rec.get(key):
                member[key] = rec[key]
        # the county prints a home town per member — a municipality, not a
        # street address, so it is location the reader can act on
        if rec.get("homeTown"):
            member["homeTown"] = rec["homeTown"]
        if rec.get("termExpires") and re.fullmatch(r"\d{4}", str(rec["termExpires"])):
            member["termExpires"] = int(rec["termExpires"])
        roster.setdefault(str(rec["district"]), {"members": [], "sourceUrl": SOURCE_URL})
        roster[str(rec["district"])]["members"].append(member)

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    for d, entry in roster.items():
        if len(entry["members"]) != MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, the county seats exactly %d per district"
                 % (d, len(entry["members"]), MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])

    members = [m for e in roster.values() for m in e["members"]]
    phones = sum(1 for m in members if m.get("phone"))
    emails = sum(1 for m in members if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d phones resolved (expected >= %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d e-mails resolved (expected >= %d) — the Cloudflare decode "
             "may have broken" % (emails, MIN_EMAILS))
    for role in ALLOWED_ROLES:
        held = [m["name"] for m in members if m.get("role") == role]
        if len(held) > 1:
            fail("%d members marked %s (%s) — the board has one"
                 % (len(held), role, ", ".join(held)))

    out_path = os.path.join(out_dir, "iroquois-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    roles = sorted(m["role"] for m in members if m.get("role"))
    print("iroquois-board-roster: %d districts, %d members (%d phones, %d e-mails, "
          "roles: %s) -> %s"
          % (len(roster), len(members), phones, emails, ", ".join(roles) or "none", out_path))


if __name__ == "__main__":
    main()

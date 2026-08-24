#!/usr/bin/env python3
"""
Resolve scripts/tazewell_county_board_scraper.py's raw output into
data/app/tazewell-county-board-members.json, keyed by board district, with a
countywide `chair` key.

Tazewell seats 21 members across 3 districts and elects its Board Chairman
COUNTYWIDE — the McHenry shape. The Chairman therefore lands under `chair`
(rendered in a separate Countywide section on every district card, because he
represents every resident) while the Vice-Chairman, who holds a district seat
as well, is badged on his own district row.

WHAT THIS GATE DOES AND DOESN'T ENFORCE. The county publishes its board twice
and the two surfaces disagree about one member's district (see the scraper's
header). Both agree on the TOTAL — 21 district members plus the countywide
chairman — so that is what's enforced here. Equal district sizes are NOT
enforced: the GIS says 7/7/7, the website says 7/8/6, and a builder that
insisted on 7/7/7 would be silently overruling the county's own current claim
to make the arithmetic pretty. If the county fixes its website, this file
starts reading 7/7/7 on its own.

Usage:
    python3 build_tazewell_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://tazewell-il.gov/boardreps/"

EXPECT_DISTRICTS = ("1", "2", "3")
EXPECT_DISTRICT_MEMBERS = 21          # agreed by both county surfaces
MIN_MEMBERS_PER_DISTRICT = 4          # a district emptying out is a parse failure
MIN_PHONES = 14
MIN_EMAILS = 18
ALLOWED_ROLES = ("Chairman", "Vice-Chairman")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("tazewell-board-roster")


def member_of(rec, keys=("party", "phone", "email")):
    member = {"name": rec["name"]}
    for key in keys:
        if rec.get(key):
            member[key] = rec[key]
    if rec.get("url") and re.match(r"^https://", rec["url"]):
        member["url"] = rec["url"]
    return member


def main():
    if len(sys.argv) < 2:
        fail("usage: build_tazewell_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    chair = None
    for rec in records:
        if not rec.get("name"):
            continue
        role = rec.get("role")
        if role and role not in ALLOWED_ROLES:
            fail("%s carries unrecognized role %r — the designation wording "
                 "changed; check it before shipping" % (rec["name"], role))
        if role == "Chairman":
            if chair:
                fail("two members marked Chairman (%s, %s) — the county elects one"
                     % (chair["name"], rec["name"]))
            chair = member_of(rec)
            continue
        district = rec.get("district")
        if not district:
            fail("%s holds a district seat but no district resolved — neither "
                 "county surface stated one" % rec["name"])
        member = member_of(rec)
        if role:
            member["role"] = role
        roster.setdefault(str(district), {"members": [], "sourceUrl": SOURCE_URL})
        roster[str(district)]["members"].append(member)

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    if not chair:
        fail("no countywide Chairman resolved — the county elects one")

    members = [m for e in roster.values() for m in e["members"]]
    if len(members) != EXPECT_DISTRICT_MEMBERS:
        fail("parsed %d district members, the county seats %d"
             % (len(members), EXPECT_DISTRICT_MEMBERS))
    for d, entry in roster.items():
        if len(entry["members"]) < MIN_MEMBERS_PER_DISTRICT:
            fail("district %s has only %d members (expected >= %d) — a parse failure"
                 % (d, len(entry["members"]), MIN_MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])

    everyone = members + [chair]
    phones = sum(1 for m in everyone if m.get("phone"))
    emails = sum(1 for m in everyone if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d phones resolved (expected >= %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d e-mails resolved (expected >= %d)" % (emails, MIN_EMAILS))

    vice = [m["name"] for m in members if m.get("role") == "Vice-Chairman"]
    if len(vice) > 1:
        fail("%d members marked Vice-Chairman (%s) — the board has one"
             % (len(vice), ", ".join(vice)))

    roster["chair"] = chair
    out_path = os.path.join(out_dir, "tazewell-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    sizes = ", ".join("D%s=%d" % (d, len(roster[d]["members"])) for d in EXPECT_DISTRICTS)
    print("tazewell-board-roster: %d district members (%s) + chair %s "
          "(%d phones, %d e-mails) -> %s"
          % (len(members), sizes, chair["name"], phones, emails, out_path))


if __name__ == "__main__":
    main()

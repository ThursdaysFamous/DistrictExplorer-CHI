#!/usr/bin/env python3
"""
Resolve scripts/cass_county_board_scraper.py's raw output into
data/app/cass-county-board-members.json, keyed by board district.

Cass seats ELEVEN members across four districts as 3/3/3/2 — the first board
in the fleet whose districts are not all the same size. The Chairman holds a
district seat and is badged on it.

THE SEAT-COUNT TRIPWIRE. Cass publishes its district composition only in a
linked PDF, so the weekly composition cross-check De Witt and Washington get is
not available here. What IS on this page is the number of seats per district —
and that is the input the shipped boundary's population test depends on
(scripts/build_cass_board_districts.py balances per MEMBER, because per-district
it reads as a 28.8% spread and looks broken). So this builder asserts the seat
counts still match that script's SEATS table and fails if they do not. A
reapportionment almost always moves a seat, which makes this an indirect but
real tripwire on a boundary that otherwise has none.

What it CANNOT catch is a redistricting that redraws the composition while
leaving every district the same size. That limitation is real; the composition
needs a human re-read at the next census. Say so rather than let the next
reader assume De Witt-grade protection.

Usage:
    python3 build_cass_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_cass_board_districts import SEATS as BOUNDARY_SEATS  # noqa: E402

SOURCE_URL = "https://co.cass.il.us/elected-officials/cass-county-board"

EXPECT_DISTRICTS = ("1", "2", "3", "4")
EXPECT_TOTAL_MEMBERS = 11
MIN_PHONES = 9
MIN_EMAILS = 6
ALLOWED_ROLES = ("Chairman",)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("cass-board-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_cass_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in records:
        if not rec.get("name") or not rec.get("district"):
            continue
        role = rec.get("role")
        if role and role not in ALLOWED_ROLES:
            fail("%s carries unrecognized role %r" % (rec["name"], role))
        member = {"name": rec["name"]}
        for key in ("role", "phone", "email"):
            if rec.get(key):
                member[key] = rec[key]
        roster.setdefault(str(rec["district"]), {"members": [], "sourceUrl": SOURCE_URL})
        roster[str(rec["district"])]["members"].append(member)

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))

    # --- the seat-count tripwire (see the module header)
    seats = {d: len(roster[d]["members"]) for d in roster}
    if seats != dict(BOUNDARY_SEATS):
        fail("SEATS CHANGED: the county board page now seats %s, the shipped boundary's "
             "population test was built for %s. Cass publishes its district composition "
             "only in a PDF, so a seat change is the strongest signal available that the "
             "districts were redrawn — re-read %s and rebuild "
             "data/app/cass-county-board-districts.json before shipping this roster."
             % (dict(sorted(seats.items())), dict(sorted(BOUNDARY_SEATS.items())),
                "https://co.cass.il.us/download_file/view/446/202"))

    members = [m for e in roster.values() for m in e["members"]]
    if len(members) != EXPECT_TOTAL_MEMBERS:
        fail("parsed %d members, the county seats %d" % (len(members), EXPECT_TOTAL_MEMBERS))
    for entry in roster.values():
        entry["members"].sort(key=lambda m: m["name"].split()[-1])

    phones = sum(1 for m in members if m.get("phone"))
    emails = sum(1 for m in members if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d phones resolved (expected >= %d) — the page wraps some numbers "
             "across lines, so a drop here usually means that handling broke"
             % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d e-mails resolved (expected >= %d)" % (emails, MIN_EMAILS))
    chairs = [m["name"] for m in members if m.get("role") == "Chairman"]
    if len(chairs) > 1:
        fail("%d members marked Chairman (%s) — the board has one" % (len(chairs), ", ".join(chairs)))

    out_path = os.path.join(out_dir, "cass-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print("cass-board-roster: %d districts, %d members seated %s (%d phones, %d e-mails, "
          "chair: %s); seat counts match the shipped boundary -> %s"
          % (len(roster), len(members),
             "/".join(str(seats[d]) for d in sorted(seats)),
             phones, emails, chairs[0] if chairs else "none", out_path))


if __name__ == "__main__":
    main()

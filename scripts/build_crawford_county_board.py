#!/usr/bin/env python3
"""
Resolve scripts/crawford_county_board_scraper.py's raw output into
data/app/crawford-county-board-members.json, keyed by Crawford County Board
district (5 districts electing TWO members each = 10 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/crawford-county-board-districts.json by district
number.

THE DRIFT CHECK IS THE POINT OF THIS BUILDER, not the roster. Crawford's board
districts are a DISSOLVE of its voting precincts (build_crawford_boundaries.py),
so the shipped boundary stays correct only while the county's election
authority keeps tabulating the same precincts in the same districts. This
compares the composition re-read from the Clerk's live results feed against
COMPOSITION in the boundaries module and FAILS on any disagreement — a red run
here means the county re-precincted or redistricted and a human must
re-measure against the census fabric before this county ships again.

The check is deliberately PARTIAL and says so: the feed carries only the most
recent election, so a run verifies whichever districts were on that ballot and
reports the rest as unchecked. Partial and honest beats a green tick that
covered nothing.

WHAT SHIPS: name, district, the county e-mail address the board page publishes
for each member, and the Chairman's role. WHAT DOES NOT: party, term and phone,
because the page publishes none of them for members — inventing any of the
three is exactly what the honesty rules forbid.

Usage:
    python3 build_crawford_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_crawford_boundaries import COMPOSITION, SEATS_PER_DISTRICT  # noqa: E402
from vtd_board_districts import norm  # noqa: E402

BOARD_URL = "https://crawfordcounty.illinois.gov/department/county-board/"
RESULTS_URL = "https://il-crawford.pollresults.net"

EXPECT_DISTRICTS = 5
EXPECT_MEMBERS = EXPECT_DISTRICTS * SEATS_PER_DISTRICT      # 10 seats
MIN_EMAILS = 9          # measured 10/10; a page that stops publishing them fails

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("crawford-board-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_crawford_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    # ---- the drift check ---------------------------------------------------
    scraped = raw.get("composition") or {}
    if not scraped:
        fail("the results feed yielded no county-board contests — this county's "
             "only automatic redistricting warning did not run")
    for dnum, precincts in sorted(scraped.items(), key=lambda kv: int(kv[0])):
        if dnum not in COMPOSITION:
            fail("the results feed carries a district %s the shipped boundaries do "
                 "not — the county redistricted" % dnum)
        want = tuple(sorted(norm(p) for p in COMPOSITION[dnum]))
        have = tuple(sorted(norm(p) for p in precincts))
        if want != have:
            fail("district %s now tabulates precincts %s, but the shipped boundary "
                 "was dissolved from %s — the county re-precincted or "
                 "redistricted; re-measure against the census fabric before "
                 "shipping again (scripts/build_crawford_boundaries.py)"
                 % (dnum, ", ".join(sorted(precincts)),
                    ", ".join(sorted(COMPOSITION[dnum]))))
    unchecked = sorted(set(COMPOSITION) - set(scraped), key=int)

    # ---- the roster --------------------------------------------------------
    roster = {}
    for rec in raw.get("records") or []:
        dnum = str(rec.get("district") or "")
        if dnum not in COMPOSITION:
            fail("the board page names a district %r that does not exist" % dnum)
        member = {"name": re.sub(r"\s+", " ", rec["name"]).strip()}
        if rec.get("role"):
            member["role"] = rec["role"]
        if rec.get("email"):
            member["email"] = rec["email"]
        if rec.get("url"):
            member["profileUrl"] = rec["url"]
        entry = roster.setdefault(dnum, {"members": [], "sourceUrl": BOARD_URL})
        entry["members"].append(member)

    if len(roster) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d" % (len(roster), EXPECT_DISTRICTS))
    total = sum(len(v["members"]) for v in roster.values())
    if total != EXPECT_MEMBERS:
        fail("parsed %d members, expected exactly %d (5 districts of %d)"
             % (total, EXPECT_MEMBERS, SEATS_PER_DISTRICT))
    for dnum, entry in roster.items():
        if len(entry["members"]) != SEATS_PER_DISTRICT:
            fail("district %s carries %d member(s), expected %d"
                 % (dnum, len(entry["members"]), SEATS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"])
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry an e-mail (floor %d) — the board page "
             "changed shape" % (emails, EXPECT_MEMBERS, MIN_EMAILS))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role")]
    if len(chairs) > 1:
        fail("two members are badged with a role (%s) — the page names one Chairman"
             % ", ".join(m["name"] for m in chairs))

    out_path = os.path.join(out_dir, "crawford-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("crawford-board-roster: wrote %s — %d districts x %d seats (%d e-mails), "
          "chair %s" % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS,
                        SEATS_PER_DISTRICT, emails,
                        chairs[0]["name"] if chairs else "not marked"))
    print("  composition verified against the shipped dissolve for district(s) %s%s"
          % (", ".join(sorted(scraped, key=int)),
             "" if not unchecked else
             "; NOT on this ballot, so unchecked this run: %s" % ", ".join(unchecked)))


if __name__ == "__main__":
    main()

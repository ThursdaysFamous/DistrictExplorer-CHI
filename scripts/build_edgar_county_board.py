#!/usr/bin/env python3
"""
Resolve scripts/edgar_county_board_scraper.py's raw output into
data/app/edgar-county-board-members.json, keyed by Edgar County Board district
(7 single-member districts).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/edgar-county-board-districts.json by district
number.

THE ROSTER IS THE PAGE AND THE GEOMETRY IS THE RETURNS, and Edgar is the
clearest case for that split in the fleet. Its 2022 and 2024 canvasses elected
Phillip R. Ludington in District 6; the county's board page names Samantha
McCarty, and the Clerk's own 2026 primary confirms it by carrying a "6th
District Member 2-YEAR UNEXPIRED TERM" contest. A seat filled mid-term is
exactly what a completed canvass cannot show, so a roster built from the
returns would name the wrong person for District 6 today.

THE DRIFT CHECK. Edgar's board districts are a DISSOLVE of its voting
precincts (build_edgar_boundaries.py), so the shipped boundary stays correct
only while the county's election authority keeps tabulating the same precincts
in the same districts. This compares the composition re-read from the Clerk's
live feed against COMPOSITION in the boundaries module and FAILS on any
disagreement. It is deliberately PARTIAL and says so: the feed carries one
election, so a run covers whichever districts were on that ballot — five of
the seven this cycle — and names the rest as unchecked.

WHAT SHIPS: name, district and party. WHAT DOES NOT: e-mail, phone, term and
any chairman. The page publishes none of them, and its committees table's
CHAIRMAN column is the chair OF EACH COMMITTEE — reading it as the board's
chair would be a fabrication.

Usage:
    python3 build_edgar_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_edgar_boundaries import COMPOSITION, SEATS_PER_DISTRICT  # noqa: E402
from vtd_board_districts import norm  # noqa: E402

BOARD_URL = "https://edgarcountyillinois.com/county-board/"
RESULTS_URL = "https://il-edgar.pollresults.net"

EXPECT_DISTRICTS = 7
EXPECT_MEMBERS = EXPECT_DISTRICTS * SEATS_PER_DISTRICT      # 10 seats
MIN_PARTIES = 7         # measured 7/7 — the page prints a party on every line

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("edgar-board-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_edgar_county_board.py <raw-scraper-output.json> [output_dir]")
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
                 "shipping again (scripts/build_edgar_boundaries.py)"
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
        if rec.get("party"):
            member["party"] = rec["party"]
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
    parties = sum(1 for v in roster.values() for m in v["members"] if m.get("party"))
    if parties < MIN_PARTIES:
        fail("only %d/%d members carry a party (floor %d) — the board page changed "
             "shape" % (parties, EXPECT_MEMBERS, MIN_PARTIES))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role")]
    if len(chairs) > 1:
        fail("two members are badged with a role (%s) — the page names one Chairman"
             % ", ".join(m["name"] for m in chairs))

    out_path = os.path.join(out_dir, "edgar-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("edgar-board-roster: wrote %s — %d single-member districts (%d parties); "
          "no chair marked, because the page publishes none"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS, parties))
    print("  composition verified against the shipped dissolve for district(s) %s%s"
          % (", ".join(sorted(scraped, key=int)),
             "" if not unchecked else
             "; NOT on this ballot, so unchecked this run: %s" % ", ".join(unchecked)))


if __name__ == "__main__":
    main()

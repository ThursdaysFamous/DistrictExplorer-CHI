#!/usr/bin/env python3
"""
Resolve scripts/wayne_county_board_scraper.py's raw output into
data/app/wayne-county-board-members.json, keyed by Wayne County Board
district (7 districts, two members each = 14 seats).

index.html's consolidated county-board layer fetches this file lazily on
first click and joins it to data/app/wayne-county-board-districts.json by
district number.

THE DRIFT CHECK IS HALF THE POINT OF THIS BUILDER, not just the roster.
Wayne's board districts are a dissolve of its voting precincts
(build_wayne_boundaries.py), composed from the SAME board page this scraper
re-reads every week — so a re-precincting or a redistricting that changed
what the page itself says would show up here first. This compares the
re-scraped per-district precinct list against build_wayne_boundaries's own
COMPOSITION and fails on any disagreement, EXCEPT District 7: the page has
never named Fairfield 1 or Fairfield 2, which the shipped composition places
there from the county's certified 2024 General instead (see the boundaries
module's docstring), so District 7 is checked as a SUBSET — the page's two
named precincts must still be exactly {Merriam, Golden Gate} — rather than an
exact match. A change to Fairfield's own district would not be caught here;
that is a stated limit, not an oversight.

WHAT THE PAGE PUBLISHES, and what it does not: a name and, for two members, a
Chairman or Vice Chairman title. No e-mail, no phone, no party and no term —
none of the four are invented.

Usage:
    python3 build_wayne_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_wayne_boundaries import COMPOSITION, SEATS_PER_DISTRICT  # noqa: E402
from vtd_board_districts import norm  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

BOARD_URL = "https://waynecountyil.gov/wayne-county-board/"

EXPECT_DISTRICTS = 7
EXPECT_MEMBERS = EXPECT_DISTRICTS * SEATS_PER_DISTRICT      # 14 seats
# District 7's page listing is a known, permanent SUBSET of the shipped
# composition — see the module docstring. Every other district must match
# the shipped composition exactly.
PAGE_SUBSET_DISTRICTS = {"7"}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("wayne-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_wayne_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    # ---- the drift check ---------------------------------------------------
    seen = {str(d.get("district")): d for d in raw.get("districts") or []}
    if set(seen) != set(COMPOSITION):
        fail("the board page now names districts %s, but the shipped boundary "
             "was dissolved for %s — the county redistricted; re-derive the "
             "composition before shipping again (scripts/build_wayne_boundaries.py)"
             % (", ".join(sorted(seen)), ", ".join(sorted(COMPOSITION, key=int))))
    for dnum, want_names in COMPOSITION.items():
        want = {norm(n) for n in want_names}
        have = {norm(p) for p in seen[dnum].get("precincts") or []}
        if dnum in PAGE_SUBSET_DISTRICTS:
            if not have <= want:
                fail("the board page's District %s now names a precinct outside "
                     "the shipped composition (%s) — re-derive before shipping "
                     "again" % (dnum, sorted(have - want)))
        elif have != want:
            fail("the board page's District %s now lists %s, shipped as %s — "
                 "the county re-precincted or redistricted; re-derive before "
                 "shipping again (scripts/build_wayne_boundaries.py)"
                 % (dnum, sorted(have), sorted(want)))

    # ---- the roster ----------------------------------------------------------
    roster = {}
    for dnum, entry in seen.items():
        members = []
        for rec in entry.get("members") or []:
            if not rec.get("name"):
                fail("district %s has a member with no name" % dnum)
            member = {"name": rec["name"]}
            if rec.get("role"):
                member["role"] = rec["role"]
            members.append(member)
        roster[dnum] = {"members": members, "sourceUrl": BOARD_URL}

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
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Chairman"]
    vice_chairs = [m for v in roster.values() for m in v["members"]
                   if m.get("role") == "Vice Chairman"]
    if len(chairs) > 1:
        fail("two members are badged Chairman (%s) — the page names one"
             % ", ".join(m["name"] for m in chairs))
    if len(vice_chairs) > 1:
        fail("two members are badged Vice Chairman (%s) — the page names one"
             % ", ".join(m["name"] for m in vice_chairs))

    out_path = os.path.join(out_dir, "wayne-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("wayne-board-roster: wrote %s — %d districts of %d (%d members), chair "
          "%s, vice chair %s"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS,
             SEATS_PER_DISTRICT, total,
             chairs[0]["name"] if chairs else "not marked",
             vice_chairs[0]["name"] if vice_chairs else "not marked"))
    print("  board page re-read from %s: all 7 districts still match the shipped "
          "dissolve (District 7 checked as the known page/canvass subset)" % BOARD_URL)


if __name__ == "__main__":
    main()

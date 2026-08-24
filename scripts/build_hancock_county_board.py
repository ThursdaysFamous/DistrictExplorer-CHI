#!/usr/bin/env python3
"""
Resolve hancock_county_board_scraper.py's output into
data/app/hancock-county-board-members.json.

Hancock seats FIFTEEN members, three in each of five districts, and the count
is the guard: the page is a plain list with no per-member contact of any kind,
so a shape change shows up as a wrong number rather than as a missing field.
That is also why there is no MIN_EMAILS/MIN_PHONES floor here — the county
publishes none, and a floor on a field nobody publishes would fail every run.

The party letter is kept because the county states it. Nothing else is
invented: no e-mail, no phone, no term, no chairman. Hancock's page names no
chair, so no row is badged one.

Usage:
    python3 build_hancock_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

EXPECT_DISTRICTS = 5
EXPECT_MEMBERS = 15
SEATS = {"1": 3, "2": 3, "3": 3, "4": 3, "5": 3}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("hancock-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_hancock_county_board.py <raw.json> [out_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        raw = json.load(f)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    districts = raw.get("districts") or {}

    if len(districts) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected %d" % (len(districts), EXPECT_DISTRICTS))

    roster = {}
    total = 0
    for dnum, members in districts.items():
        if dnum not in SEATS:
            fail("unexpected district %r — Hancock has districts 1-5" % dnum)
        if len(members) != SEATS[dnum]:
            fail("district %s parsed %d members, expected %d"
                 % (dnum, len(members), SEATS[dnum]))
        clean = []
        for m in members:
            name = (m.get("name") or "").strip()
            if not name:
                fail("district %s has a member with no name" % dnum)
            entry = {"name": name}
            if m.get("party"):
                entry["party"] = m["party"]
            clean.append(entry)
        roster[dnum] = {"members": clean}
        total += len(clean)

    if total != EXPECT_MEMBERS:
        fail("parsed %d members, expected exactly %d" % (total, EXPECT_MEMBERS))

    # Keyed by district at the TOP LEVEL, exactly like every other county-board
    # roster in data/app (Warren is the nearest twin). Two reasons, both real:
    # index.html's dispatch entries index straight into roster[district], and
    # check_roster_retention.py measures field coverage PER TOP-LEVEL KEY, so a
    # wrapper object would collapse five districts into one "source" and hide a
    # district that lost its members.
    payload = {d: roster[d] for d in sorted(roster, key=int)}
    path = os.path.join(out_dir, "hancock-county-board-members.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print("hancock-board-roster: %d districts, %d members -> %s"
          % (len(payload), total, path))


if __name__ == "__main__":
    main()

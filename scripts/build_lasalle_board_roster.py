#!/usr/bin/env python3
"""
Resolve scripts/lasalle_county_board_scraper.py's raw output into
data/app/lasalle-county-board-members.json, keyed by LaSalle County Board
district (plus a top-level "chair" for the countywide-elected Board Chairman —
the DuPage shape; the Nov 2024 general canvass carries the county-wide
COUNTY BOARD CHAIRMAN contest that proves the office is elected at large).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it to the DERIVED 2022-2031 district boundary
(data/app/lasalle-county-board-districts.json) by district number. The county's
own board-boundary GIS is the superseded 2011-2021 map with a 2015-frozen
roster — the 2026-07-31 validation-pass finding — so nothing here reads it.

Usage:
    python3 build_lasalle_board_roster.py <raw-scraper-output.json> [output_dir]

output_dir defaults to the repo's data/app/ directory.
"""

import json
import os
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://lasallecountyil.gov/m/directory/department?did=39"

# 29 single-member districts plus the countywide Chairman. The directory
# publishes a full 10-digit phone and a district-office e-mail on every row;
# refuse to overwrite good data with a suspiciously partial scrape.
EXPECT_DISTRICTS = 29
MIN_PHONES = 24
MIN_EMAILS = 24

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("lasalle-board-roster")


def member_obj(rec):
    m = {"name": rec["name"]}
    if rec.get("role") and rec["role"] not in ("Member",):
        m["role"] = rec["role"]
    for k in ("phone", "email", "url"):
        if rec.get(k):
            m[k] = rec[k]
    return m


def main():
    if len(sys.argv) < 2:
        fail("usage: build_lasalle_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    chair = None
    for rec in records:
        if not rec.get("name"):
            continue
        if rec.get("role") == "Chair":
            if chair is not None:
                fail("two Chairman rows (%s, %s) — the directory shape changed"
                     % (chair["name"], rec["name"]))
            chair = member_obj(rec)
            continue
        if rec.get("district") is None:
            continue
        d = str(rec["district"])
        if d in roster:
            fail("district %s appears twice — LaSalle districts are single-member" % d)
        roster[d] = {"members": [member_obj(rec)], "sourceUrl": SOURCE_URL}

    if len(roster) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d" % (len(roster), EXPECT_DISTRICTS))
    if chair is None:
        fail("no Chairman of the Board row parsed — the office is countywide-elected "
             "and the card renders it; refusing to ship a chairless roster")
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d/%d members carry a phone (floor %d)" % (phones, EXPECT_DISTRICTS, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry an e-mail (floor %d)" % (emails, EXPECT_DISTRICTS, MIN_EMAILS))

    roster["chair"] = chair
    out_path = os.path.join(out_dir, "lasalle-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("lasalle-board-roster: wrote %s — %d districts (%d phones, %d e-mails) + chair %s"
          % (os.path.relpath(out_path, REPO_ROOT), len(roster) - 1, phones, emails, chair["name"]))


if __name__ == "__main__":
    main()

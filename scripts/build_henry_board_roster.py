#!/usr/bin/env python3
"""
Resolve scripts/henry_county_board_scraper.py's raw output into
data/app/henry-county-board-members.json, keyed by board district — the
Livingston/Woodford shape scaled up: two ten-member districts, no chair key
(Henry's chair is elected from within the body and the directory does not
mark who holds it, so marking one would be a guess; the card links the
board page instead).

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it to the DERIVED district boundary
(data/app/henry-county-board-districts.json — TIGER townships dissolved
per Ordinance 21-33) by district number.

Usage:
    python3 build_henry_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.henrycty.com/193/County-Board"

# Two districts, ten members each; the directory publishes an e-mail on every
# row and a phone on most. Refuse to overwrite good data with a suspiciously
# partial scrape.
EXPECT_DISTRICTS = ("1", "2")
EXPECT_MEMBERS_PER_DISTRICT = 10
MIN_PHONES = 12
MIN_EMAILS = 17

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("henry-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_henry_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in records:
        if not rec.get("name") or rec.get("district") is None:
            continue
        d = str(rec["district"])
        roster.setdefault(d, {"members": [], "sourceUrl": SOURCE_URL})
        m = {"name": rec["name"]}
        for k in ("phone", "email"):
            if rec.get(k):
                m[k] = rec[k]
        roster[d]["members"].append(m)

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    for d, entry in roster.items():
        if len(entry["members"]) != EXPECT_MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, the county seats exactly %d"
                 % (d, len(entry["members"]), EXPECT_MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d/20 members carry a phone (floor %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d/20 members carry an e-mail (floor %d)" % (emails, MIN_EMAILS))

    out_path = os.path.join(out_dir, "henry-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("henry-board-roster: wrote %s — 2 districts x 10 members (%d phones, %d e-mails)"
          % (os.path.relpath(out_path, REPO_ROOT), phones, emails))


if __name__ == "__main__":
    main()

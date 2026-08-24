#!/usr/bin/env python3
"""
Resolve scripts/woodford_county_board_scraper.py's raw output into
data/app/woodford-county-board-members.json, keyed by board district — the
Livingston shape: three multi-member districts, five members each, no chair
key (Woodford's chair is elected from within the body every two years and the
directory does not mark who holds it, so marking one would be a guess; the
card links the directory instead).

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it to the DERIVED district boundary
(data/app/woodford-county-board-districts.json — TIGER townships dissolved
per Ordinance 2020/21 #005) by district number.

Usage:
    python3 build_woodford_board_roster.py <raw-scraper-output.json> [output_dir]

output_dir defaults to the repo's data/app/ directory.
"""

import json
import os
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.woodford-county.org/m/directory/department?did=22"

# Three districts, five members each, and the directory publishes a full
# 10-digit phone and an e-mail on every row; refuse to overwrite good data
# with a suspiciously partial scrape.
EXPECT_DISTRICTS = ("1", "2", "3")
EXPECT_MEMBERS_PER_DISTRICT = 5
MIN_PHONES = 12
MIN_EMAILS = 12

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("woodford-board-roster")


def member_obj(rec):
    m = {"name": rec["name"]}
    for k in ("phone", "email", "url"):
        if rec.get(k):
            m[k] = rec[k]
    return m


def main():
    if len(sys.argv) < 2:
        fail("usage: build_woodford_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for rec in records:
        if not rec.get("name") or rec.get("district") is None:
            continue
        d = str(rec["district"])
        roster.setdefault(d, {"members": [], "sourceUrl": SOURCE_URL})
        roster[d]["members"].append(member_obj(rec))

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    for d, entry in roster.items():
        if len(entry["members"]) != EXPECT_MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, the ordinance seats exactly %d"
                 % (d, len(entry["members"]), EXPECT_MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d/15 members carry a phone (floor %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d/15 members carry an e-mail (floor %d)" % (emails, MIN_EMAILS))

    out_path = os.path.join(out_dir, "woodford-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("woodford-board-roster: wrote %s — 3 districts x 5 members (%d phones, %d e-mails)"
          % (os.path.relpath(out_path, REPO_ROOT), phones, emails))


if __name__ == "__main__":
    main()

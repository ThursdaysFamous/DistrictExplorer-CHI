#!/usr/bin/env python3
"""
Resolve scripts/logan_county_board_scraper.py's raw output into
data/app/logan-county-board-members.json, keyed by board district — six
two-member districts, with the Chair and Vice Chair tags riding their own
member rows (the county elects both from within the body AND says who holds
them, unlike Woodford's unmarked directory).

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it to the TCRPC district boundary by
district number — closing the rule-4 branch-3 honesty floor the entry
shipped with (gap logan-county-board-members).

Usage:
    python3 build_logan_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = ("https://www.logancountyil.gov/index.php?option=com_content"
              "&view=article&id=176&Itemid=541&lang=en")

EXPECT_DISTRICTS = ("1", "2", "3", "4", "5", "6")
EXPECT_MEMBERS_PER_DISTRICT = 2
MIN_PHONES = 10
MIN_EMAILS = 10

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("logan-board-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_logan_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    chairs = []
    for rec in records:
        if not rec.get("name") or rec.get("district") is None:
            continue
        d = str(rec["district"])
        roster.setdefault(d, {"members": [], "sourceUrl": SOURCE_URL})
        m = {"name": rec["name"]}
        if rec.get("role"):
            m["role"] = rec["role"]
            chairs.append((rec["role"], rec["name"]))
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
    roles = sorted(r for r, _ in chairs)
    if roles != ["Chair", "Vice Chair"]:
        fail("expected exactly one Chair and one Vice Chair, got %s — the page's "
             "role tags changed" % (chairs or "none"))
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d/12 members carry a phone (floor %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d/12 members carry an e-mail (floor %d)" % (emails, MIN_EMAILS))

    out_path = os.path.join(out_dir, "logan-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("logan-board-roster: wrote %s — 6 districts x 2 members (%d phones, %d e-mails; %s)"
          % (os.path.relpath(out_path, REPO_ROOT), phones, emails,
             ", ".join("%s %s" % (r, n) for r, n in sorted(chairs))))


if __name__ == "__main__":
    main()

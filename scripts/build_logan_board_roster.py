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
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = ("https://www.logancountyil.gov/index.php?option=com_content"
              "&view=article&id=176&Itemid=541&lang=en")

EXPECT_DISTRICTS = ("1", "2", "3", "4", "5", "6")

# THE BOARD'S OWN OFFICE, and it is the board's rather than a member's because
# the county says so in those words: the page heads this block "Logan County
# Board Office" and then lists twelve members each with a DIFFERENT address.
# That distinction is the whole reason this ships and Franklin's and Warren's
# do not — a board page's only street address is very often a member's HOME,
# which this fleet never publishes (the Madison/Peoria rule). The county gives
# a PO Box (39) beside the street address; the street one ships, because the
# card's label is where a reader can go.
BOARD = {
    "address": "Logan County Board Office, 601 Broadway St., Lincoln, IL 62656",
    "phone": "(217) 732-6400",
    "email": "logancountyboard@logancountyil.gov",
    "sourceUrl": SOURCE_URL,
}
EXPECT_MEMBERS_PER_DISTRICT = 2
MIN_PHONES = 10
MIN_EMAILS = 10

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("logan-board-roster")


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

    # Added AFTER every district check above, all of which read roster's keys
    # as districts (sorted(roster) == EXPECT_DISTRICTS) or index members on
    # each value. A board block written earlier would fail the first and
    # KeyError the second.
    roster["board"] = dict(BOARD)

    out_path = os.path.join(out_dir, "logan-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("logan-board-roster: wrote %s — 6 districts x 2 members + the board "
          "office block (%d phones, %d e-mails; %s)"
          % (os.path.relpath(out_path, REPO_ROOT), phones, emails,
             ", ".join("%s %s" % (r, n) for r, n in sorted(chairs))))


if __name__ == "__main__":
    main()

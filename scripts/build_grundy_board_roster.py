#!/usr/bin/env python3
"""
Resolve scripts/grundy_county_board_scraper.py's raw output into
data/app/grundy-county-board-members.json, keyed by board district — three
six-member districts, every seat carrying party, the "Board Member Since"
year the page publishes, committee assignments verbatim (including the
page's own per-committee "– Chair"/"– Vice Chair" suffixes), a phone and an
e-mail. The Board Chairman tag rides his member row exactly as the page
states it ("County Board Chairman" — the chair is a district member, not a
countywide seat).

index.html's consolidated county-board layer fetches this file lazily on
first click (same-origin) and joins it by district number to the DERIVED
district boundary (data/app/grundy-county-board-districts.json — the
county's own precinct layer dissolved per the adopted 10/12/2021 map).

Usage:
    python3 build_grundy_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://www.grundycountyil.gov/government/county_board.php"

EXPECT_DISTRICTS = ("1", "2", "3")
EXPECT_MEMBERS_PER_DISTRICT = 6
MIN_PHONES = 15
MIN_EMAILS = 15
MIN_PARTIES = 15
MIN_SINCE = 15

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

fail = make_fail("grundy-board-roster")


def main():
    if len(sys.argv) < 2:
        fail("usage: build_grundy_board_roster.py <raw-scraper-output.json> [output_dir]")
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
            chairs.append(rec["name"])
        for k in ("party", "since", "phone", "email"):
            if rec.get(k):
                m[k] = rec[k]
        if rec.get("committees"):
            m["committees"] = rec["committees"]
        roster[d]["members"].append(m)

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    for d, entry in roster.items():
        if len(entry["members"]) != EXPECT_MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, the county seats exactly %d"
                 % (d, len(entry["members"]), EXPECT_MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])
    if len(chairs) != 1:
        fail("expected exactly one County Board Chairman tag, got %s — the "
             "page's role wording changed" % (chairs or "none"))
    counts = {k: sum(1 for v in roster.values() for m in v["members"] if m.get(k))
              for k in ("phone", "email", "party", "since")}
    for k, floor in (("phone", MIN_PHONES), ("email", MIN_EMAILS),
                     ("party", MIN_PARTIES), ("since", MIN_SINCE)):
        if counts[k] < floor:
            fail("only %d/18 members carry a %s (floor %d)" % (counts[k], k, floor))

    out_path = os.path.join(out_dir, "grundy-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("grundy-board-roster: wrote %s — 3 districts x 6 members "
          "(%d phones, %d e-mails, %d parties, %d since-years; Chairman %s)"
          % (os.path.relpath(out_path, REPO_ROOT), counts["phone"], counts["email"],
             counts["party"], counts["since"], chairs[0]))


if __name__ == "__main__":
    main()

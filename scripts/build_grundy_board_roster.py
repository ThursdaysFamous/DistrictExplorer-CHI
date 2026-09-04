#!/usr/bin/env python3
"""
Resolve scripts/grundy_county_board_scraper.py's raw output into
data/app/grundy-county-board-members.json, keyed by board district — three
six-member districts, every NAMED seat carrying party, the "Board Member Since"
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
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.grundycountyil.gov/government/county_board.php"

EXPECT_DISTRICTS = ("1", "2", "3")
EXPECT_SEATS_PER_DISTRICT = 6
EXPECT_SEATS_TOTAL = len(EXPECT_DISTRICTS) * EXPECT_SEATS_PER_DISTRICT
# A SEAT COUNT IS NOT A MEMBER COUNT, and conflating the two froze this refresh
# for twenty-one days. The builder used to demand exactly six members per
# district; on 2026-09-02 the county's page listed five in District 2, because
# Greg Ridenour had left and nobody had replaced him. That is the county
# telling us something true, and refusing the write turned it into silence —
# the shipped file went on naming Ridenour while the page did not, which is the
# one outcome worse than a card that says a seat is unfilled.
#
# So the floor moved from per-district equality to a board total with room for
# a departure or two, and every district now ships its `seats`, which is what
# lets boardDirectoryShortfallNote say "1 of 6 seats not listed in the county's
# directory" instead of quietly showing five. Three or more seats missing is
# not a board with vacancies, it is a parser that stopped finding rows, and
# that still refuses.
#
# The note says "not listed", never "vacant", and that wording is the point:
# the county's page carries no vacancy marker of any kind — it simply stops
# listing a person — so we can see that a seat is unaccounted for and cannot
# see why. `vacancies` is deliberately NOT set here (the helper treats it as
# the county having DECLARED a vacancy, and would let that claim win); Lee and
# Stephenson set it because their sources print the empty seat.
MIN_MEMBERS = EXPECT_SEATS_TOTAL - 2
MIN_PHONES = 15
MIN_EMAILS = 15
MIN_PARTIES = 15
MIN_SINCE = 15

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


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
        if len(entry["members"]) > EXPECT_SEATS_PER_DISTRICT:
            # Over-full is never a personnel event: either a row was counted
            # twice or the county re-apportioned, and both need a human.
            fail("district %s has %d members, the county seats only %d"
                 % (d, len(entry["members"]), EXPECT_SEATS_PER_DISTRICT))
        entry["seats"] = EXPECT_SEATS_PER_DISTRICT
        entry["members"].sort(key=lambda m: m["name"].split()[-1])
    total_members = sum(len(e["members"]) for e in roster.values())
    if total_members < MIN_MEMBERS:
        fail("only %d of the county's %d seats are named (floor %d) — that is "
             "site drift, not a vacancy; check the county's board page before "
             "lowering this floor"
             % (total_members, EXPECT_SEATS_TOTAL, MIN_MEMBERS))
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
    # Name the short districts in the run's own output. A refresh that ships
    # seventeen of eighteen seats should say so where the operator reads it,
    # not only on the card.
    short = ["district %s (%d of %d)" % (d, len(roster[d]["members"]),
                                         EXPECT_SEATS_PER_DISTRICT)
             for d in sorted(roster)
             if len(roster[d]["members"]) < EXPECT_SEATS_PER_DISTRICT]
    print("grundy-board-roster: wrote %s — %d districts, %d of %d seats named%s "
          "(%d phones, %d e-mails, %d parties, %d since-years; Chairman %s)"
          % (os.path.relpath(out_path, REPO_ROOT), len(roster), total_members,
             EXPECT_SEATS_TOTAL,
             "; unfilled: " + ", ".join(short) if short else "",
             counts["phone"], counts["email"], counts["party"], counts["since"],
             chairs[0]))


if __name__ == "__main__":
    main()

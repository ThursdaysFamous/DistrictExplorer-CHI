#!/usr/bin/env python3
"""
Resolve scripts/clay_county_board_scraper.py's raw output into
data/app/clay-county-board-members.json, keyed by Clay County Board district
letter (14 lettered districts, one member each).

index.html's consolidated county-board layer fetches this file lazily on
first click and joins it to data/app/clay-county-board-districts.json by
district letter.

THE DRIFT CHECK IS HALF THE POINT OF THIS BUILDER, not just the roster.
Clay's board districts are composed from the SAME county-board page this
pipeline re-reads every week (build_clay_boundaries.py — including the split
of Clay City at the village limits, which the page states as its two
precinct names). This compares the re-scraped per-district precinct list
against that builder's own COMPOSITION and fails on any disagreement, so a
redistricting or a re-precincting that changed what the county's own page
says surfaces here first. WHAT THIS CANNOT TRIP: the village-limits LINE
inside Clay City — the page names the two halves and never draws the line,
which came from the Clerk's e-mail (2026-08-24); a change to the village's
corporate limits would not show here. That is a stated limit, the Wayne
Fairfield shape.

ROLES COME FROM TWO COUNTY SURFACES AND MUST AGREE. The members page marks
the Chair in its own position line ("County Board Chair - District C") and
the county-board page names the Chairman and Vice Chairman in prose. The
Chair must be the same person on both, or the build fails. The Vice Chairman
is named ONLY in the prose, and under a different form of her name — the
board page writes "Barbara McGrew", the members page prints her card as
"Barb Mcgrew" — so the role is joined by SURNAME, required unique, and the
join is PRINTED on every run rather than becoming a silent identification.
The shipped name is the members page's, exactly as the county prints it
there (the Fulton "Karl WIlliams" rule: names ship as printed, including
the lowercase g).

WHAT SHIPS PER MEMBER: name, district letter, phone (as printed, dots and
all), and the two roles. No e-mail, no party, no term — the county publishes
none, and none is invented.

Usage:
    python3 build_clay_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_clay_boundaries import COMPOSITION  # noqa: E402
from vtd_board_districts import norm  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

MEMBERS_URL = "https://claycounty.illinois.gov/county-board/members/"

EXPECT_DISTRICTS = 14                      # lettered A-N, one member each
PHONE_RE = re.compile(r"^\d{3}[.\-]\d{3}[.\-]\d{4}$")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("clay-board-roster")


def surname(name):
    return norm(str(name).split()[-1]) if str(name).split() else ""


def main():
    if len(sys.argv) < 2:
        fail("usage: build_clay_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    # ---- the drift check ---------------------------------------------------
    seen = {str(d.get("district")).upper(): d for d in raw.get("districts") or []}
    if set(seen) != set(COMPOSITION):
        fail("the board page now names districts %s, but the shipped boundary "
             "was composed for %s — the county redistricted; re-derive before "
             "shipping again (scripts/build_clay_boundaries.py)"
             % (", ".join(sorted(seen)), ", ".join(sorted(COMPOSITION))))
    for letter, want_names in COMPOSITION.items():
        want = {norm(n) for n in want_names}
        have = {norm(p) for p in seen[letter].get("precincts") or []}
        if have != want:
            fail("the board page's District %s now lists %s, shipped as %s — "
                 "the county re-precincted or redistricted; re-derive before "
                 "shipping again (scripts/build_clay_boundaries.py)"
                 % (letter, sorted(have), sorted(want)))

    # ---- the roster --------------------------------------------------------
    members = raw.get("members") or []
    if len(members) != EXPECT_DISTRICTS:
        fail("parsed %d member cards, expected exactly %d (14 lettered "
             "districts of one member)" % (len(members), EXPECT_DISTRICTS))
    by_district = {}
    for rec in members:
        letter = str(rec.get("district") or "").upper()
        if letter not in COMPOSITION:
            fail("member %r carries district %r, which is not a lettered "
                 "district" % (rec.get("name"), letter))
        if letter in by_district:
            fail("districts must seat one member each and %s carries two (%s, %s)"
                 % (letter, by_district[letter]["name"], rec.get("name")))
        if not rec.get("name"):
            fail("district %s has a member with no name" % letter)
        member = {"name": rec["name"]}
        phone = rec.get("phone")
        if phone:
            if not PHONE_RE.match(phone):
                fail("member %r carries phone %r, which does not look like a "
                     "phone number — a mangled card, not a style choice"
                     % (rec["name"], phone))
            member["phone"] = phone
        by_district[letter] = member
    missing = sorted(set(COMPOSITION) - set(by_district))
    if missing:
        fail("no member card carries district(s) %s" % ", ".join(missing))

    # ---- the roles, from two county surfaces that must agree ---------------
    chair_cards = [(l, m) for l, m in by_district.items()
                   for rec in members
                   if rec["name"] == m["name"] and rec.get("chairOnCard")]
    if len(chair_cards) != 1:
        fail("expected exactly one member card marked 'County Board Chair', "
             "found %d" % len(chair_cards))
    chair_letter, chair_member = chair_cards[0]
    page_chair = str(raw.get("chair") or "").strip()
    if norm(page_chair) != norm(chair_member["name"]):
        fail("the members page marks %r as Chair while the county-board page "
             "names %r — the county's two surfaces disagree"
             % (chair_member["name"], page_chair))
    chair_member["role"] = "Chairman"

    page_vice = str(raw.get("viceChair") or "").strip()
    vice_hits = [(l, m) for l, m in by_district.items()
                 if surname(m["name"]) == surname(page_vice)]
    if len(vice_hits) != 1:
        fail("the Vice Chairman %r joins %d member card(s) by surname — the "
             "join must be unique" % (page_vice, len(vice_hits)))
    vice_letter, vice_member = vice_hits[0]
    if vice_member.get("role"):
        fail("the Vice Chairman join landed on the Chairman's own card (%s)"
             % vice_member["name"])
    vice_member["role"] = "Vice Chairman"
    joined_note = ""
    if norm(page_vice) != norm(vice_member["name"]):
        joined_note = (" (board page writes %r; the members page — the roster "
                       "source — prints %r, which ships)" % (page_vice, vice_member["name"]))

    roster = {letter: {"members": [member], "sourceUrl": MEMBERS_URL}
              for letter, member in by_district.items()}

    out_path = os.path.join(out_dir, "clay-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    phones = sum(1 for m in by_district.values() if m.get("phone"))
    print("clay-board-roster: wrote %s — %d lettered districts of one member, "
          "%d/%d with a phone"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS,
             phones, EXPECT_DISTRICTS))
    print("  chair: %s (District %s, both county surfaces agree); vice chair: "
          "%s (District %s), joined by surname from the board page's %r%s"
          % (chair_member["name"], chair_letter, vice_member["name"],
             vice_letter, page_vice, joined_note))
    print("  board page re-read: all 14 district lines still match the shipped "
          "composition (the village-limits line inside Clay City is the "
          "Clerk's, and no page re-read can trip it)")


if __name__ == "__main__":
    main()

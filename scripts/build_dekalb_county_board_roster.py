#!/usr/bin/env python3
"""
Resolve scripts/dekalb_county_board_scraper.py's raw output into
data/app/dekalb-county-board-members.json, keyed by DeKalb County Board district
("1".."12" — twelve districts electing two members each, 24 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to the county's own
District_AreaEffective2022 boundary service. The boundary carries Member1/Member2
too, which is why the join is worth spelling out: the GIS names are the same
people, but the GIS has NO phone numbers at all (0 of 12 on both columns) and is
missing two e-mails, so the roster is the officeholder source and the GIS is
purely geometry. See the scraper's header for the measurement.

Shape mirrors the McHenry/Kendall/Livingston rosters — {district: {members: [...],
sourceUrl}} — with the chair carried as a member `role` rather than a top-level
countywide officer, because DeKalb's chair is one of the 24 district members
(elected by the board from among themselves), not a separately elected countywide
office like McHenry's Chairman. Putting it in the district's own member list is
what keeps the card from implying a 25th, at-large seat.

Term dates are scraped and deliberately not carried into the card, matching
build_mchenry_county_board_roster.py's recorded call that term-end is not card
material. They stay in the raw scrape for anyone auditing the source.

Usage:
    python3 build_dekalb_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

SOURCE_URL = "https://dekalbcounty.org/government/county-board/county-board-members/"

# THE SEAT COUNT IS CARRIED INTO THE DATA, not just asserted in this docstring,
# because the card has no other way to know a district is SHORT. The floors
# below are deliberately permissive — a resignation between scrapes must not
# block a refresh — and that permissiveness had a silent side: the district
# keeps its key, one row simply stops appearing, and the card shows a smaller
# delegation than the county elects with nothing saying so. Emitting `seats`
# lets the card say "1 of 2 seats not listed in the county's directory"
# instead. It states what the source shows, never why: a row can be missing
# because a seat is empty or because the parse dropped it, and this county
# publishes nothing that tells the two apart (the Sangamon members-index
# distinction does not exist here). Making the shortfall VISIBLE is what avoids
# the false trade between a silently short card and a floor tightened to an
# equality, which would freeze the file with a departed member still named.
SEATS_PER_DISTRICT = 2

# Twelve districts, two seats each. Floors, not equalities: a resignation between
# scrapes is normal and must not block a refresh, while a collapse means the page
# markup changed and the old file should stand. Phones are floored well under the
# observed 22 because two members publish none and a third dropping off is not a
# reason to refuse an otherwise good roster.
MIN_DISTRICTS = 12
MIN_MEMBERS = 22
MIN_EMAILS = 20
MIN_PHONES = 18

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def norm_name(value):
    """Compare names on letters alone — the chair table and the member list are
    two separately maintained pages and differ in punctuation and spacing."""
    return re.sub(r"[^a-z]", "", (value or "").lower())


def member_obj(rec):
    member = {"name": rec["name"]}
    for key in ("party", "phone", "email"):
        if rec.get(key):
            member[key] = rec[key]
    return member


def resolve_roster(records, chair=None):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        name = (rec.get("name") or "").strip()
        if not district or not name:
            continue
        slot = roster.setdefault(district, {"members": [], "seats": SEATS_PER_DISTRICT,
                                            "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec))

    # The chair role is applied only on an unambiguous single match. A chair who
    # has left the board (the table is historical — its first row is merely the
    # most recent) matches nothing and the role is silently dropped; a name that
    # somehow matched two members would be ambiguous and is also dropped. Never
    # guessed onto a seat.
    if chair and chair.get("name"):
        target = norm_name(chair["name"])
        matches = [m for slot in roster.values() for m in slot["members"]
                   if norm_name(m["name"]) == target]
        if len(matches) == 1:
            matches[0]["role"] = "Board Chair"

    rank = {"Board Chair": 0}
    for slot in roster.values():
        # Stable, human-meaningful order: chair first, then alphabetical — so a
        # card does not reshuffle between weekly refreshes because the page
        # re-sorted.
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 1), m["name"]))
    return roster


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        records, chair = payload.get("records"), payload.get("chair")
    else:
        records, chair = payload, None
    roster = resolve_roster(records or [], chair)

    members = sum(len(v["members"]) for v in roster.values())
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    chaired = sum(1 for v in roster.values() for m in v["members"]
                  if m.get("role") == "Board Chair")
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if phones < MIN_PHONES:
        problems.append("%d phones (< %d)" % (phones, MIN_PHONES))
    if chaired > 1:
        problems.append("%d members marked Board Chair" % chaired)
    if problems:
        print("build-dekalb-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "dekalb-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-dekalb-board: wrote %s — %d districts, %d members, %d phones, "
          "%d e-mails, chair %s"
          % (out_path, len(roster), members, phones, emails,
             "resolved" if chaired else "unresolved"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Resolve scripts/lee_county_board_scraper.py's raw output into
data/app/lee-county-board-members.json, keyed by Lee County Board district
("1".."4" — four districts electing five members each, 20 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to the county's OWN drawn
boundary (gis.leecountyil.gov/leecogis, Election/County_Board_Districts). Lee is
therefore a rule-4 branch 2 county: the geometry is published, the officeholders
are not on it, and a weekly scrape supplies them.

The Board Chair carries a `role`, and it is derived from the document rather
than assumed: Lee's chair is a district member (the county board elects its
chair from among its own 20), and the roster PDF identifies him only by giving
his row the shared `leecochair@countyoflee.org` address instead of a personal
one. That is the county's own marker, not a guess about who presides — and it is
cross-checked against the County Board page, which names the chair in prose.

Usage:
    python3 build_lee_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://www.leecountyil.com/419/Member-Contact-List"
# The address the county publishes for the chair's seat rather than for a
# person. Whoever holds it holds the gavel.
CHAIR_EMAIL = "leecochair@countyoflee.org"

# Four districts, five seats each. Floors, not equalities: a resignation between
# scrapes is normal and must not block a refresh. MIN_MEMBERS is 19 rather than
# the full 20 for exactly that reason — but note the SCRAPER's floor is 20,
# because a member silently lost to a column-split bug is the failure this
# pipeline actually had, and that belongs where the columns are read.
MIN_DISTRICTS = 4
MIN_MEMBERS = 19
MIN_EMAILS = 18
MIN_PARTIES = 18

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    if (rec.get("email") or "").strip().lower() == CHAIR_EMAIL:
        member["role"] = "Board Chair"
    for key in ("party", "email"):
        if rec.get(key):
            member[key] = rec[key]
    # The county publishes the year each SEAT is next on the ballot, which is
    # staggered within a district (three of District 1's five run in 2026), so it
    # belongs on the member rather than the card.
    if rec.get("next_election"):
        member["nextElection"] = str(rec["next_election"])
    return member


def resolve_roster(records, vacancies=()):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        name = (rec.get("name") or "").strip()
        if not district or not name:
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec))
    # A seat the county prints with no name is counted and never named — the
    # Livingston/Stephenson posture. Lee's District 3 went unfilled in the
    # 2026-04-24 revision; the card should say a seat is vacant rather than
    # quietly show four members where the county apportioned five.
    for district in vacancies or ():
        district = str(district).strip()
        if not district:
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["vacancies"] = slot.get("vacancies", 0) + 1
    for slot in roster.values():
        # Chair first, then alphabetical — so a card does not reshuffle between
        # weekly refreshes because the PDF was re-sorted.
        slot["members"].sort(key=lambda m: (0 if m.get("role") else 1, m["name"]))
    return roster


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("members") if isinstance(payload, dict) else payload
    vacancies = payload.get("vacancies") if isinstance(payload, dict) else []
    roster = resolve_roster(records or [], vacancies or [])

    members = sum(len(v["members"]) for v in roster.values())
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    parties = sum(1 for v in roster.values() for m in v["members"] if m.get("party"))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chair"]
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    vacant = sum(v.get("vacancies", 0) for v in roster.values())
    if members + vacant < MIN_MEMBERS:
        problems.append("%d seats: %d members + %d vacant (< %d)"
                        % (members + vacant, members, vacant, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if parties < MIN_PARTIES:
        problems.append("%d parties (< %d)" % (parties, MIN_PARTIES))
    # A board has one chair. Two means the chair address appeared on two rows,
    # which would put the title on someone who does not hold it.
    if len(chairs) > 1:
        problems.append("%d members carry the chair address" % len(chairs))
    if problems:
        print("build-lee-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "lee-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-lee-board: wrote %s — %d districts, %d members, %d e-mails, "
          "%d parties, chair %s"
          % (out_path, len(roster), members, emails, parties,
             chairs[0]["name"] if chairs else "unresolved"))


if __name__ == "__main__":
    main()

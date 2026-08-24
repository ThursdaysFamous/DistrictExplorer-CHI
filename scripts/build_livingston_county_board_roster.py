#!/usr/bin/env python3
"""
Resolve scripts/livingston_county_board_scraper.py's raw output into
data/app/livingston-county-board-members.json, keyed by Livingston County Board
district ("1".."3" — three multi-member districts, six seats each).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to
data/app/livingston-county-board-districts.json, the township dissolve built by
build_livingston_board_districts.py. Livingston is the fleet's first county where
BOTH halves are derived rather than fetched: the county publishes no GIS, so the
boundary comes from TIGER townships per the county's published composition, and
the roster comes from its directory page.

Shape mirrors the McHenry/Kendall rosters — {district: {members: [...],
sourceUrl}} — with one addition this county forces: `vacancies`. The directory
lists an explicit "Vacancy" seat, which the scraper refuses to name. Carrying the
COUNT lets the card say six seats exist and five are filled, instead of quietly
showing five and implying that is the whole board.

Term expiry is scraped but deliberately not carried into the card, matching
build_mchenry_county_board_roster.py's recorded call that term-end is not card
material. It stays in the raw scrape for anyone auditing the source.

Usage:
    python3 build_livingston_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://www.livingstoncountyil.gov/government/county_board_members.php"

# Three districts, six seats each. Floors, not equalities: a resignation between
# scrapes is normal and must not block a refresh, while a collapse means the
# directory markup changed and the old file should stand.
MIN_DISTRICTS = 3
MIN_MEMBERS = 15
MIN_EMAILS = 13

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    for key in ("role", "party", "email"):
        if rec.get(key):
            member[key] = rec[key]
    return member


def resolve_roster(records):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        if not district:
            continue
        slot = roster.setdefault(district, {"members": [], "vacancies": 0,
                                            "sourceUrl": SOURCE_URL})
        if rec.get("vacant") or not rec.get("name"):
            slot["vacancies"] += 1
            continue
        slot["members"].append(member_obj(rec))
    for slot in roster.values():
        # Stable, human-meaningful order: chair first, then vice chair, then
        # alphabetical — so a card does not reshuffle between weekly refreshes
        # just because the directory re-sorted.
        rank = {"Board Chair": 0, "Vice Chair": 1}
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 2), m["name"]))
        if not slot["vacancies"]:
            del slot["vacancies"]
    return roster


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("records") if isinstance(payload, dict) else payload
    roster = resolve_roster(records or [])

    members = sum(len(v["members"]) for v in roster.values())
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    vacancies = sum(v.get("vacancies", 0) for v in roster.values())
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if problems:
        print("build-livingston-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "livingston-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-livingston-board: wrote %s — %d districts, %d members, %d e-mails, "
          "%d vacant seat(s)" % (out_path, len(roster), members, emails, vacancies))


if __name__ == "__main__":
    main()

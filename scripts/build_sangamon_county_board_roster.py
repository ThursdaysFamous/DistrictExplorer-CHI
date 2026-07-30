#!/usr/bin/env python3
"""
Resolve scripts/sangamon_county_board_scraper.py's raw output into
data/app/sangamon-county-board-members.json, keyed by Sangamon County Board
district ("1".."29" — 29 single-member districts).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to the county's own board
GIS (CountyBoardDistricts2020_WithURLs), which carries the district and a
per-district member URL but no name. That URL is what the scraper walks, so the
join key is published by the same body on both sides rather than inferred.

Shape mirrors the McHenry/Kendall/Livingston rosters — {district: {members: [...],
sourceUrl}} — with one member per district here.

Term is scraped but not carried into the card, matching
build_mchenry_county_board_roster.py's recorded call that term-end is not card
material; the members' street addresses are residences and are not collected at
all. The published phone IS carried: the county prints it as the way to reach
that member.

Usage:
    python3 build_sangamon_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://sangamonil.gov/departments/a-c/county-board/districts"

# 29 single-member districts. Floors, not equalities: a vacancy between scrapes
# is normal and must not block a refresh, while a collapse means the page shape
# changed and the shipped file should stand. Measured at build time: 29/29 names
# and parties, 27 e-mails, 22 phones — the contact floors sit below those because
# the county genuinely does not publish an e-mail for every member.
MIN_DISTRICTS = 27
MIN_MEMBERS = 27
MIN_EMAILS = 24

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    for key in ("party", "phone", "email", "url"):
        if rec.get(key):
            member[key] = rec[key]
    return member


def resolve_roster(records):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        if not district or not rec.get("name"):
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec))
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
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if problems:
        print("build-sangamon-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "sangamon-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    print("build-sangamon-board: wrote %s — %d districts, %d members, %d e-mails, %d phones"
          % (out_path, len(roster), members, emails, phones))


if __name__ == "__main__":
    main()

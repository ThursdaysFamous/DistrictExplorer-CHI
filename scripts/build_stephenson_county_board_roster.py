#!/usr/bin/env python3
"""
Resolve scripts/stephenson_county_board_scraper.py's raw output into
data/app/stephenson-county-board-members.json, keyed by Stephenson County Board
district ("B".."I" — eight districts electing two members each, 16 seats).

THE KEYS ARE LETTERS, not numbers, and there is no District A. That is the
county's own scheme, not a transcription slip: its adopted 2022 maps letter the
four Freeport Township districts B-E and the four rural districts F-I.

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district letter to
data/app/stephenson-county-board-districts.json. That boundary is the fleet's
only GEOREFERENCED one — see build_stephenson_board_districts.py — so the card
labels the four Freeport districts as derived from the county's published map.
This roster is ordinary weekly scrape work; only the geometry is unusual.

Shape mirrors the other rosters — {district: {members: [...], sourceUrl}} — with
`vacancies` where the page says a seat is vacant (District G's second seat, as
of 2026-07-30). The Chairman and Vice Chairman are district members carrying a
`role`: Stephenson's board elects its officers from among its own 16 members, so
there is no countywide seat to imply.

Usage:
    python3 build_stephenson_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

SOURCE_URL = "https://stephensoncountyil.gov/government/county_board/index.php"

# Eight districts, two seats each. Floors, not equalities: a vacancy between
# scrapes is normal (there is one already) and must not block a refresh, while a
# collapse means the board table changed and the old file should stand.
MIN_DISTRICTS = 8
MIN_MEMBERS = 14
MIN_EMAILS = 12
MIN_PHONES = 12

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


def norm_name(value):
    """Compare on letters alone — the officer block and the table are separately
    maintained bits of the same page and differ in punctuation."""
    return re.sub(r"[^a-z]", "", (value or "").lower())


def member_obj(rec):
    member = {"name": rec["name"]}
    for key in ("phone", "email"):
        if rec.get(key):
            member[key] = rec[key]
    return member


def resolve_roster(records, officers=None, vacancies=()):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        name = (rec.get("name") or "").strip()
        if not district or not name:
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec))
    for d in vacancies or ():
        slot = roster.setdefault(str(d), {"members": [], "sourceUrl": SOURCE_URL})
        slot["vacancies"] = slot.get("vacancies", 0) + 1

    # A role is applied only on an unambiguous single match, so an officer who
    # has left the board (or a name the table spells differently) resolves to
    # nothing rather than onto the wrong seat.
    for role, who in sorted((officers or {}).items()):
        target = norm_name((who or {}).get("name"))
        if not target:
            continue
        hits = [m for slot in roster.values() for m in slot["members"]
                if norm_name(m["name"]) == target]
        if len(hits) == 1:
            hits[0]["role"] = "Board Chair" if role.lower() == "chairman" else "Vice Chair"

    rank = {"Board Chair": 0, "Vice Chair": 1}
    for slot in roster.values():
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 2), m["name"]))
    return roster


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        records = payload.get("records")
        officers = payload.get("officers")
        vacancies = payload.get("vacancies") or []
    else:
        records, officers, vacancies = payload, None, []
    roster = resolve_roster(records or [], officers, vacancies)

    members = sum(len(v["members"]) for v in roster.values())
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    vac = sum(v.get("vacancies", 0) for v in roster.values())
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chair"]
    vices = [m for v in roster.values() for m in v["members"] if m.get("role") == "Vice Chair"]
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if phones < MIN_PHONES:
        problems.append("%d phones (< %d)" % (phones, MIN_PHONES))
    if len(chairs) > 1 or len(vices) > 1:
        problems.append("%d chairs / %d vice chairs" % (len(chairs), len(vices)))
    bad = sorted(k for k in roster if not re.fullmatch(r"[B-I]", k))
    if bad:
        problems.append("unexpected district key(s): %s" % ", ".join(bad))
    if problems:
        print("build-stephenson-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "stephenson-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-stephenson-board: wrote %s — %d districts, %d members, %d phones, "
          "%d e-mails, %d vacant seat(s), chair %s, vice chair %s"
          % (out_path, len(roster), members, phones, emails, vac,
             chairs[0]["name"] if chairs else "unresolved",
             vices[0]["name"] if vices else "unresolved"))


if __name__ == "__main__":
    main()

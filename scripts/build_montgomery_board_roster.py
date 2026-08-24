#!/usr/bin/env python3
"""
Resolve scripts/montgomery_county_board_scraper.py's raw output into
data/app/montgomery-county-board-members.json, keyed by Montgomery County Board
district ("1".."7" — seven districts electing two members each, 14 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to
data/app/montgomery-county-board-districts.json, the county's own GIS export
(build_montgomery_boundaries.py). Both halves come from the county itself,
which puts Montgomery in the better tier: no derivation, no tracing.

Shape mirrors the other rosters — {district: {members: [...], sourceUrl}}. The
Board Chairman is a district member carrying a `role`, not a countywide section:
Montgomery's board elects its chairman from among its own 14, so there is no
at-large seat to imply.

EVERY SEAT IS EVEN, WHICH IS WHY THE FLOORS ARE EXACT. Fourteen members, two per
district, and the county publishes a phone and an e-mail for every one of them.
That makes a partial scrape trivially detectable, so MIN_MEMBERS is the full
count rather than one under: on a two-seat district, losing one member leaves a
card that looks entirely normal, and there is no count between 13 and 14 that
represents a state worth shipping. A genuine vacancy is expected to need a human
to lower this deliberately — that is the point.

Usage:
    python3 build_montgomery_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://montgomerycountyil.gov/county-board/"

MIN_DISTRICTS = 7
MIN_MEMBERS = 14
MIN_EMAILS = 14
MIN_PHONES = 14
SEATS_PER_DISTRICT = 2

# The county writes "Board Chairman"; normalised to the label the other county
# cards use so one reader renders every fork's board the same way. Anything else
# in an <em> is carried through verbatim rather than guessed at.
ROLE_ALIASES = {
    "board chairman": "Board Chair",
    "board chair": "Board Chair",
    "chairman": "Board Chair",
    "vice chairman": "Vice Chair",
    "vice chair": "Vice Chair",
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    role = (rec.get("role") or "").strip()
    if role:
        member["role"] = ROLE_ALIASES.get(role.lower(), role)
    for key in ("phone", "email"):
        if rec.get(key):
            member[key] = rec[key]
    # A second published number is a second number, carried in the order the
    # county prints it. It is NOT labelled home/cell, here or on the page.
    extra = rec.get("phones_extra") or []
    if extra:
        member["phonesExtra"] = list(extra)
    return member


def resolve_roster(records):
    roster = {}
    for rec in records:
        district = str(rec.get("district") or "").strip()
        name = (rec.get("name") or "").strip()
        if not district or not name:
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec))
    rank = {"Board Chair": 0, "Vice Chair": 1}
    for slot in roster.values():
        # Stable, human-meaningful order: chair, vice chair, then alphabetical, so
        # a card does not reshuffle between weekly refreshes because the page's
        # column order changed.
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 2), m["name"]))
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
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chair"]
    vices = [m for v in roster.values() for m in v["members"] if m.get("role") == "Vice Chair"]
    names = [m["name"] for v in roster.values() for m in v["members"]]

    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if phones < MIN_PHONES:
        problems.append("%d phones (< %d)" % (phones, MIN_PHONES))
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        problems.append("duplicate member names (%s)" % ", ".join(dupes))
    # Two seats per district, every district. A district parsing three means a
    # heading was missed and somebody else's member landed on this card.
    lopsided = {d: len(v["members"]) for d, v in roster.items()
                if len(v["members"]) != SEATS_PER_DISTRICT}
    if lopsided:
        problems.append("districts not seating %d: %s" % (SEATS_PER_DISTRICT, lopsided))
    if len(chairs) > 1:
        problems.append("%d members marked Board Chair" % len(chairs))
    if len(vices) > 1:
        problems.append("%d members marked Vice Chair" % len(vices))
    if problems:
        print("build-montgomery-board: FAIL — refusing to overwrite a good file with "
              "a partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "montgomery-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-montgomery-board: wrote %s — %d districts, %d members, %d phones, "
          "%d e-mails, chair %s"
          % (out_path, len(roster), members, phones, emails,
             chairs[0]["name"] if chairs else "unresolved"))


if __name__ == "__main__":
    main()

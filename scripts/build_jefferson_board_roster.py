#!/usr/bin/env python3
"""
Resolve scripts/jefferson_county_board_scraper.py's raw output into
data/app/jefferson-county-board-members.json, keyed by Jefferson County Board
district ("1".."13" — thirteen SINGLE-member districts, 13 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to
data/app/jefferson-county-board-districts.json, the dissolve
build_jefferson_board_districts.py makes from the county's own precincts using
the county's own approved composition list. Both halves therefore trace back to
Jefferson County itself, which is the point: it publishes no boundary of any
kind, and everything here arrived because its Clerk answered three e-mails.

NAMES ARRIVE SURNAME-FIRST and are read forward by uninvert_name(), IMPORTED
from build_municipal_officials_roster.py rather than reimplemented. That guard
is what makes the inversion safe — it refuses anything whose trailing part is a
suffix, so a "Roy Williams, Jr." can never become "Jr. Roy Williams" — and this
is the third source in the fleet to need it in one week (after Stephenson's
Dakota and LaSalle's Village of Dana). Shared machinery, not forked.

THE ROLE IS SEPARATED IN THE SCRAPER, before inversion, because
"Draege, Steve (Vice Chair)" is not a name.

Usage:
    python3 build_jefferson_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_municipal_officials_roster import uninvert_name  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://jeffersoncounty.illinois.gov/county_board/index.php"

# THE BOARD'S OWN OFFICE, attributed by the county in its own words: the page
# heads this block "Office/Mailing Address: / Jefferson County Board / County
# Courthouse", above a staffed line ("County Board Executive Assistant") and a
# board mailbox. It is not a member's address — the thirteen member rows carry
# thirteen different phones and a per-district role e-mail and no address at
# all, which is why this one is safe to publish and a board page's lone street
# address usually is not (the Madison/Peoria rule).
BOARD = {
    "address": ("Jefferson County Board, County Courthouse, "
                "100 South 10th Street, Mt. Vernon, IL 62864"),
    "phone": "(618) 244-8000, option 2",
    "email": "jeffcoboard@jeffersoncounty.illinois.gov",
    "sourceUrl": SOURCE_URL,
}

# Thirteen single-member districts. The floor is the full board rather than one
# under: on a single-member district losing a member leaves a card with no name
# at all and no count anywhere would look wrong, so a genuine vacancy is meant
# to need a human to lower this.
MIN_DISTRICTS = 13
MIN_MEMBERS = 13
MIN_EMAILS = 13
MIN_PHONES = 13
SEATS_PER_DISTRICT = 1

# The county writes "Chairman" and "Vice Chair"; normalised to the labels the
# other county cards use so one reader renders every fork's board the same way.
ROLE_ALIASES = {
    "chairman": "Board Chair",
    "chair": "Board Chair",
    "board chairman": "Board Chair",
    "vice chair": "Vice Chair",
    "vice chairman": "Vice Chair",
    "vice-chair": "Vice Chair",
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


def member_obj(rec, notes):
    raw = rec["name"]
    flipped = uninvert_name(raw)
    if flipped:
        notes.append("%s -> %s" % (raw, flipped))
    elif "," in raw:
        # A comma the shared guard would not invert. Never silently reordered —
        # reported so a human sees it, and shipped exactly as published.
        notes.append("LEFT AS PUBLISHED (not a surname-first name): %s" % raw)
    member = {"name": flipped or raw}
    role = (rec.get("role") or "").strip()
    if role:
        member["role"] = ROLE_ALIASES.get(role.lower(), role)
    for key in ("phone", "email"):
        if rec.get(key):
            member[key] = rec[key]
    return member


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("records") if isinstance(payload, dict) else payload

    roster, notes = {}, []
    for rec in records or []:
        district = str(rec.get("district") or "").strip()
        if not district or not (rec.get("name") or "").strip():
            continue
        slot = roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        slot["members"].append(member_obj(rec, notes))

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
        problems.append("duplicate member names (%s)"
                        % ", ".join(sorted({n for n in names if names.count(n) > 1})))
    lopsided = {d: len(v["members"]) for d, v in roster.items()
                if len(v["members"]) != SEATS_PER_DISTRICT}
    if lopsided:
        problems.append("districts not seating %d: %s" % (SEATS_PER_DISTRICT, lopsided))
    # A name still carrying a comma means the shared guard declined to invert it
    # and nobody looked. Better to fail than to ship "Draege, Steve" on a card.
    still_inverted = [n for n in names if "," in n]
    if still_inverted:
        problems.append("name(s) still surname-first: %s" % ", ".join(still_inverted))
    if len(chairs) > 1:
        problems.append("%d members marked Board Chair" % len(chairs))
    if len(vices) > 1:
        problems.append("%d members marked Vice Chair" % len(vices))
    if problems:
        print("build-jefferson-board: FAIL — refusing to overwrite a good file "
              "with a partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    # District count is taken BEFORE the board block joins the mapping, so the
    # log line keeps reporting districts rather than districts-plus-one. Added
    # after every guard above too: each one reads roster's values as districts
    # and indexes ["members"], so a board block written earlier would KeyError.
    district_count = len(roster)
    roster["board"] = dict(BOARD)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "jefferson-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    for note in notes:
        print("  name: %s" % note)
    print("build-jefferson-board: wrote %s — %d districts, %d members, %d phones, "
          "%d e-mails, chair %s, vice chair %s"
          % (out_path, district_count, members, phones, emails,
             chairs[0]["name"] if chairs else "unresolved",
             vices[0]["name"] if vices else "unresolved"))


if __name__ == "__main__":
    main()

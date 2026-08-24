#!/usr/bin/env python3
"""
Resolve scripts/white_county_board_scraper.py's raw output into
data/app/white-county-board-members.json (keyed by district "1".."5") and
data/app/white-precinct-polling.json (keyed by shipped precinct name).

THE DISTRICT JOIN IS A CERTIFIED-DOCUMENT CONSTANT, NOT A SCRAPE. White's
board page lists five members with party and Chair/Vice roles and NO
districts; the join below was proven from the county's own certified
canvasses — the 2022 General Election (the first on the 2021 map) elected all
five by district, and the 2024 General re-elected districts 3 and 4:

    D1  DAVID J. SOUTH, REP        (2022 canvass p.35)
    D2  AMANDA CANNON, REP         (2022 canvass p.37)
    D3  KEN USERY, REP             (2022 p.39; re-elected 2024 p.16)
    D4  CASSIE "HUGHES" PIGG, REP  (2022 p.41; re-elected 2024 p.17)
    D5  CLINT SPENCER, DEM         (2022 canvass p.43)

Names are matched surname + first initial, and the match must be UNIQUE (the
§2.5.1 rule). ANY divergence — a name on the page this table cannot place, a
table row the page no longer lists, a party that moved — FAILS the build
instead of shipping a guess: a membership change means an appointment or an
election, and which district the new member represents is a fact only a new
certified document (or the Clerk) can supply. That failure is this pipeline's
drift alarm, by design.

CONTACT SHIPS AT BOARD LEVEL. The county prints one mailing address and one
e-mail (the Clerk's) for all five members; repeating either five times would
imply per-member channels that do not exist (the Calhoun switchboard rule),
so both ride a top-level "board" entry the card renders once.

THE POLLING FILE carries the Elections page's own list verbatim — place and
address as ONE string, because splitting "Fire House 912 Loy St." would be a
guess. The page spells one township "Gray" where the county's own map, the
census, and the canvasses all print GREY; the expansion normalises it and
says so here rather than shipping two spellings of one precinct.

THE MAP-LINK WATCH: build_white_boundaries.py derived this county's
boundaries from the adopted map PDF the same Elections page links. The
scraper records whether that exact link is still present; its absence fails
this build — a replaced map lands at a new CDN path while the old URL serves
the old bytes forever (the Mason watcher rule), and a re-precincting is
exactly what that link changing would mean. This is the weakest real
substitute for a composition re-read and is named as such: it cannot catch a
redraw that keeps the filename.

Usage:
    python3 build_white_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# The composition constants double as this pipeline's drift check; the heavy
# geometry imports in that module are function-local (the De Witt seam), so
# this import costs requests and nothing else.
from build_white_boundaries import (  # noqa: E402
    CANVASS, ELECTIONS_URL, EXPECTED_PRECINCTS,
)
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

BOARD_URL = "https://www.whitecounty-il.gov/county-board"

# surname + first initial -> (district, display name, party, canvass provenance).
# Display names are the board page's own spelling, read forward and title-cased
# once by a human (the parenthetical is the county's, not a role).
CANVASS_SEATS = {
    ("SOUTH", "D"): ("1", "David South", "R",
                     "elected 2022 (District 1, certified canvass)"),
    ("CANNON", "A"): ("2", "Amanda Cannon", "R",
                      "elected 2022 (District 2, certified canvass)"),
    ("USERY", "K"): ("3", "Ken Usery", "R",
                     "elected 2022, re-elected 2024 (District 3, certified canvasses)"),
    ("PIGG", "C"): ("4", "Cassie (Hughes) Pigg", "R",
                    "elected 2022, re-elected 2024 (District 4, certified canvasses)"),
    ("SPENCER", "C"): ("5", "Clint Spencer", "D",
                       "elected 2022 (District 5, certified canvass)"),
}
ROLE_LABELS = {"CHAIR": "Board Chair", "VICE": "Vice Chair"}

# The Elections page's township spellings, normalised to the map/census/canvass
# spelling where they differ. Deterministic, recorded, and the only edit made.
TOWNSHIP_ALIASES = {"GRAY": "GREY"}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("build-white-board")


# The shared implementation, not a fourth naive copy: identical on every name
# in the shipped polling file (proven by round-trip at migration, 2026-08-24),
# and roman-numeral/hyphen-aware should the county ever print one.
from vtd_board_districts import title_case  # noqa: E402  (shared machinery — do not fork)


def match_key(raw_name):
    """(SURNAME, first initial) from a page name like 'CASSIE (HUGHES) PIGG'."""
    words = [w for w in re.sub(r"\([^)]*\)", " ", raw_name).upper().split() if w]
    if len(words) < 2:
        return None
    return (words[-1], words[0][0])


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        raw = json.load(f)

    # ---- the map-link watch (the boundary's weekly drift substitute) --------
    if not raw.get("map_link"):
        fail("the Elections page no longer links the adopted district & "
             "precinct map this county's boundaries were traced from — a "
             "human must re-read the page before anything ships (a replaced "
             "map means a possible re-precincting)")

    # ---- members: page vs certified-canvass table, both directions ----------
    members = raw.get("members") or []
    if len(members) != len(CANVASS_SEATS):
        fail("the board page lists %d members; the certified-canvass table "
             "seats %d — a membership change needs a human and a new "
             "certified document before a district can be assigned"
             % (len(members), len(CANVASS_SEATS)))
    roster = {}
    seen_keys = set()
    for rec in members:
        key = match_key(rec.get("name") or "")
        if key is None or key not in CANVASS_SEATS:
            fail("board-page member %r matches no seat in the certified-"
                 "canvass table — a new member's district is a fact only a "
                 "certified document (or the Clerk) can supply; update "
                 "CANVASS_SEATS from one, never from adjacency"
                 % (rec.get("name"),))
        if key in seen_keys:
            fail("two board-page members match the same canvass seat %r" % (key,))
        seen_keys.add(key)
        district, display, party, provenance = CANVASS_SEATS[key]
        if (rec.get("party") or "").upper() != party:
            fail("board-page party %r for %s disagrees with the canvass (%s)"
                 % (rec.get("party"), display, party))
        member = {"name": display, "party": party, "districtSource": provenance}
        role = ROLE_LABELS.get((rec.get("role") or "").upper())
        if role:
            member["role"] = role
        roster[district] = {"members": [member], "sourceUrl": BOARD_URL}
    if sorted(roster) != sorted(CANVASS):
        fail("joined districts %s, expected %s" % (sorted(roster), sorted(CANVASS)))
    chairs = [m for v in roster.values() for m in v["members"]
              if m.get("role") == "Board Chair"]
    vices = [m for v in roster.values() for m in v["members"]
             if m.get("role") == "Vice Chair"]
    if len(chairs) != 1 or len(vices) != 1:
        fail("expected exactly one Chair and one Vice Chair, found %d/%d"
             % (len(chairs), len(vices)))
    board = {"sourceUrl": BOARD_URL}
    if raw.get("board_email"):
        board["email"] = raw["board_email"]
    if raw.get("board_address"):
        board["address"] = raw["board_address"]
    if "email" not in board:
        fail("the board's published e-mail is gone from the page — the "
             "retention gate would rightly refuse this")
    roster["board"] = board

    # ---- polling: expand the page's grouped lines over the 18 precincts -----
    shipped_names = {n for names in CANVASS.values() for n in names}
    polling = {}
    for entry in raw.get("polling") or []:
        township = re.sub(r"\s+", " ", entry.get("township") or "").upper().strip()
        township = TOWNSHIP_ALIASES.get(township, township)
        for num in entry.get("numbers") or []:
            name = "%s %d" % (township, num)
            if name not in shipped_names:
                fail("the Elections page names polling for %r, which is not a "
                     "shipped precinct — the fabric or the page changed" % name)
            if name in polling:
                fail("two polling lines cover precinct %r" % name)
            polling[title_case(name)] = {
                "location": entry["location"],
                "sourceUrl": ELECTIONS_URL,
            }
    if len(polling) != EXPECTED_PRECINCTS:
        missing = sorted({title_case(n) for n in shipped_names} - set(polling))
        fail("polling covers %d of %d precincts — missing %s"
             % (len(polling), EXPECTED_PRECINCTS, missing))

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    members_path = os.path.join(out_dir, "white-county-board-members.json")
    polling_path = os.path.join(out_dir, "white-precinct-polling.json")
    with open(members_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, sort_keys=True)
    with open(polling_path, "w", encoding="utf-8") as f:
        json.dump(polling, f, ensure_ascii=False, sort_keys=True)
    print("build-white-board: wrote %s — 5 single-member districts, chair %s, "
          "vice chair %s, board e-mail %s"
          % (members_path, chairs[0]["name"], vices[0]["name"], board["email"]))
    print("build-white-board: wrote %s — %d precincts across %d locations"
          % (polling_path, len(polling),
             len({v["location"] for v in polling.values()})))


if __name__ == "__main__":
    main()

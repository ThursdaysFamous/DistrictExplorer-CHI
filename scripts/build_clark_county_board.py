#!/usr/bin/env python3
"""
Resolve scripts/clark_county_board_scraper.py's raw output into
data/app/clark-county-board-members.json, keyed by Clark County Board district.

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it to data/app/clark-county-board-districts.json
by district number.

WHAT THIS ROSTER CLAIMS, EXACTLY. Not "who the county's website says sits on
the board" — the county's only board document is a scanned image and cannot be
read by a machine — but "who the county CERTIFIED as elected in this district,
in the most recent general election that seated it". Every name here comes off
a Statement of Votes Cast published by County Clerk & Recorder Laura H. Lee,
and every card renders the election that produced it. That is a narrower claim
than a roster page makes and a better-sourced one; where it can go wrong is a
mid-term vacancy filled by board appointment, which no canvass records — so
`districtSource` names the election on every member and the card never says
"current" of anything the returns do not show.

THE DRIFT CHECK. The scraped precinct composition per district must equal
build_clark_boundaries.CANVASS exactly, or this refuses to write. That single
comparison catches the two failures that matter: a county that re-precincts
(the shipped geometry would silently answer for the wrong district) and a
county that redistricts (the same). Either one has to be re-measured against
the census fabric by a human before this county ships again.

WHAT IS DELIBERATELY NOT HERE: per-member phone numbers and e-mail addresses.
The county publishes them, but only inside the scanned "2022 - 2024 County
Board List", where one of the seven addresses is genuinely unresolvable from
the image (it renders as "J m.bolin@bolininc.com", with a space no address can
contain). Shipping six read-by-eye personal addresses and guessing the seventh
is exactly what the honesty rules forbid, and a mistyped personal address
sends a constituent's mail to a stranger. So the card carries the COUNTY's own
switchboard and courthouse address at board level (the Calhoun rule) and the
current list is an open ask with the Clerk. The scan also prints every
member's HOME ADDRESS; that never ships, under any sourcing (the Madison /
Peoria rule).

Usage:
    python3 build_clark_county_board.py <raw-scraper-output.json> [output_dir]

output_dir defaults to the repo's data/app/ directory.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_clark_boundaries import CANVASS  # noqa: E402  (the drift check)
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

BOARD_URL = "https://www.clarkcountyil.org/board"
RESULTS_URL = "https://il-clark.accessliberty.com/pastelections.aspx"
# The county's own switchboard and courthouse address, as printed in the site
# footer of clarkcountyil.org. Board-level, because the county publishes no
# per-member contact a machine can read.
BOARD_PHONE = "217-826-8311"
BOARD_ADDRESS = "Clark County Courthouse, 501 Archer Ave., Marshall, IL 62441"

EXPECT_DISTRICTS = 7
SEATS_PER_DISTRICT = 1

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")

PARTY_LABEL = {"REP": "R", "DEM": "D", "IND": "I", "GRN": "G", "LIB": "L"}


fail = make_fail("clark-board-roster")


def display_name(raw):
    """Canvasses print some names in caps and some in title case; normalise
    the caps ones and leave anything already mixed exactly as published."""
    name = re.sub(r"\s+", " ", raw or "").strip()
    if not name or name != name.upper():
        return name
    out = []
    for word in name.split():
        if len(word) <= 2 and word.endswith("."):      # middle initial "E."
            out.append(word.upper())
        elif "-" in word:
            out.append("-".join(p.capitalize() for p in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_clark_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    records = raw.get("records") or []
    if len(records) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d — the Clerk's canvass "
             "layout changed or a district's contest went unread"
             % (len(records), EXPECT_DISTRICTS))

    roster = {}
    for rec in records:
        dnum = str(rec.get("district") or "")
        if dnum not in CANVASS:
            fail("canvass carries a district %r the shipped boundaries do not" % dnum)
        if dnum in roster:
            fail("district %s appears twice — Clark districts are single-member" % dnum)

        scraped = tuple(sorted(n.upper() for n in rec.get("precincts") or ()))
        expected = tuple(sorted(CANVASS[dnum]))
        if scraped != expected:
            fail("district %s now tabulates precincts %s, but the shipped "
                 "boundaries were dissolved from %s — the county re-precincted "
                 "or redistricted; re-measure against the census fabric before "
                 "shipping (scripts/build_clark_boundaries.py)"
                 % (dnum, ", ".join(scraped) or "none", ", ".join(expected)))

        named = [c for c in rec.get("candidates") or () if c.get("name")]
        if not named:
            fail("district %s has no named candidate in the %s canvass"
                 % (dnum, rec.get("electionTitle")))
        if len(named) > SEATS_PER_DISTRICT:
            if any(c.get("votes") is None for c in named):
                fail("district %s was contested in %s but the canvass totals "
                     "did not parse — a winner must never be inferred from "
                     "ballot order" % (dnum, rec.get("electedYear")))
            named.sort(key=lambda c: -c["votes"])
            if len(named) > 1 and named[0]["votes"] == named[1]["votes"]:
                fail("district %s ties at %d votes in %s — a human has to read "
                     "that canvass" % (dnum, named[0]["votes"], rec.get("electedYear")))
        winner = named[0]

        member = {
            "name": display_name(winner["name"]),
            "districtSource": "elected %s (District %s, certified canvass)"
                              % (rec.get("electedYear"), dnum),
        }
        party = PARTY_LABEL.get(winner.get("party"))
        if party:
            member["party"] = party
        roster[dnum] = {"members": [member], "sourceUrl": rec.get("sourceUrl") or RESULTS_URL}

    missing = sorted(set(CANVASS) - set(roster), key=int)
    if missing:
        fail("no member resolved for district(s) %s" % ", ".join(missing))

    roster["board"] = {
        "phone": BOARD_PHONE,
        "address": BOARD_ADDRESS,
        "note": ("Names and districts come from Clark County's certified "
                 "election canvasses; the county publishes no per-member "
                 "contact a machine can read, so the county's own switchboard "
                 "stands for the board."),
        "sourceUrl": BOARD_URL,
        "resultsUrl": RESULTS_URL,
    }

    out_path = os.path.join(out_dir, "clark-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    years = sorted({r.get("electedYear") for r in records})
    print("clark-board-roster: wrote %s — %d single-member districts from the "
          "%s canvass(es); composition matches the shipped boundaries 23/23"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS,
             "/".join(str(y) for y in years)))


if __name__ == "__main__":
    main()

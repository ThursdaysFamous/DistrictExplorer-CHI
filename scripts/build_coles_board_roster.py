#!/usr/bin/env python3
"""
Resolve scripts/coles_county_board_scraper.py's raw output into
data/app/coles-county-board-members.json, keyed by Coles County Board district
("1".."12" — twelve SINGLE-member districts).

index.html's consolidated county-board layer fetches this file lazily on first
click (same-origin) and joins it by district number to the county's OWN live
board-district service. THE TWO HALVES COME FROM THE SAME COUNTY BUT NOT THE
SAME SURFACE, DELIBERATELY: the service's polygons are the county's adopted
map, but its attribute table is a 2022-04-23 snapshot naming SIX members who
have since left the board, so the app reads geometry from the service and
people from the county's board page. scripts/coles_county_board_scraper.py's
header carries the six-name diff that settled it.

Shape mirrors the other rosters — {district: {members: [...], sourceUrl}} —
plus a top-level "board" entry carrying the County Board office's own phone
and address. Those ship ONCE at board level rather than under twelve names:
one office for twelve members is the board's, not each member's (the Calhoun
switchboard rule). They are the board's rather than the county's switchboard
by measurement, not assumption — the same navbar block reads (217) 348-0511 /
Room 124 on the Treasurer's page and (217) 348-0585 / 701 7th St on the
Sheriff's.

WHAT IS NOT HERE, and why each absence is correct rather than missing:

  * PARTY and TERM. The county's board page publishes neither. Both columns
    exist on the GIS layer and both belong to the same frozen 2022 table —
    its District 11 term reads "2022" — so taking them would import exactly
    the staleness this pipeline exists to reject.
  * HOME ADDRESSES. The board page prints a residence under most members. The
    scraper never parses that row (it keys on the icon class, not the href,
    because the address anchor is itself a `tel:` link), so nothing here can
    leak it — the Madison/Peoria precedent.
  * A CHAIRMAN. Neither the board page nor the committees page names one, so
    no seat is badged. A chair the sources do not name is not a chair this
    app may invent.

CROSS-CHECK, and it is a hard failure rather than a warning: every board-page
name must appear on the county's committees page and every committees-page
name must be a board member. Coles publishes its board twice, and a county
that publishes twice will eventually disagree with itself (the Tazewell
lesson); here the two surfaces agreed 12/12 at first ship, so any divergence
is news and stops the run rather than silently picking a side.

FLOORS, set at what the page actually publishes (2026-08-17): 12 seats
exactly, districts 1..12 each once; 12 e-mails (every member has one, so the
floor is exact — the Brown County failure was a whole column going quietly
empty); 7 phones, two under the published 9, so one member dropping a listing
reads as the county's change rather than a red week while a mass loss still
trips both this and check_roster_retention.py.

Usage:
    python3 build_coles_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://www.colesco.illinois.gov/board/"
COMMITTEES_URL = "https://www.colesco.illinois.gov/board/committees"

EXPECTED_SEATS = 12
EXPECTED_DISTRICTS = tuple(str(n) for n in range(1, EXPECTED_SEATS + 1))
MIN_EMAILS = 12
MIN_PHONES = 7

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def name_key(name):
    """Surname + first initial, the fleet's cross-surface match key."""
    parts = [p for p in str(name).replace(".", " ").split() if p]
    if len(parts) < 2:
        return str(name).strip().lower()
    return (parts[-1] + " " + parts[0][0]).lower()


def cross_check(members, committees):
    """Both directions, both fatal — see the module docstring."""
    by_key = {}
    for member in members:
        by_key.setdefault(name_key(member["name"]), []).append(member["name"])
    ambiguous = sorted(k for k, v in by_key.items() if len(v) > 1)
    if ambiguous:
        raise SystemExit(
            "coles: board names %s share a surname+initial key — the cross-check "
            "requires a UNIQUE match, so resolve it before shipping" % ambiguous)

    seen = set()
    unknown = []
    for names in committees.values():
        for name in names:
            key = name_key(name)
            if key in by_key:
                seen.add(key)
            else:
                unknown.append(name)
    if unknown:
        raise SystemExit(
            "coles: the committees page names %s, who are not on the board page — "
            "the county's two roster surfaces disagree, so nothing ships until a "
            "human decides which is current" % sorted(set(unknown)))
    missing = sorted(by_key[k][0] for k in by_key if k not in seen)
    if missing:
        raise SystemExit(
            "coles: %s hold no committee seat on the county's committees page. "
            "That is possible in principle, but it is also what a half-updated "
            "site looks like, so it stops the run for a human to confirm."
            % missing)


def committees_for(name, committees):
    key = name_key(name)
    return sorted(committee for committee, names in committees.items()
                  if any(name_key(n) == key for n in names))


def build(raw):
    members = raw["members"]
    committees = raw.get("committees") or {}
    if len(members) != EXPECTED_SEATS:
        raise SystemExit("coles: %d seats, expected %d"
                         % (len(members), EXPECTED_SEATS))
    districts = sorted(str(m["district"]) for m in members)
    if tuple(sorted(districts, key=int)) != EXPECTED_DISTRICTS:
        raise SystemExit(
            "coles: districts %s — expected 1..%d each exactly once. A changed "
            "district count reads as a reapportionment, which needs the boundary "
            "re-checked against the county's service before anything ships."
            % (districts, EXPECTED_SEATS))

    cross_check(members, committees)

    emails = sum(1 for m in members if m.get("email"))
    phones = sum(1 for m in members if m.get("phone"))
    if emails < MIN_EMAILS:
        raise SystemExit("coles: %d e-mails < floor %d" % (emails, MIN_EMAILS))
    if phones < MIN_PHONES:
        raise SystemExit("coles: %d phones < floor %d" % (phones, MIN_PHONES))

    distinct = {m["phone"] for m in members if m.get("phone")}
    if len(distinct) == 1 and phones > 1:
        raise SystemExit(
            "coles: all %d published phones are the same number — that is a "
            "switchboard, not %d direct lines (the Calhoun rule). Hoist it to "
            "the board entry instead of repeating it per member." % (phones, phones))

    out = {}
    for member in sorted(members, key=lambda m: m["district"]):
        person = {"name": member["name"]}
        for field in ("phone", "email"):
            if member.get(field):
                person[field] = member[field]
        seats = committees_for(member["name"], committees)
        if seats:
            person["committees"] = seats
        out[str(member["district"])] = {
            "members": [person],
            "sourceUrl": SOURCE_URL,
        }

    board = dict(raw.get("board") or {})
    board["sourceUrl"] = SOURCE_URL
    board["committeesUrl"] = COMMITTEES_URL
    out["board"] = board
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    payload = build(raw)
    path = os.path.join(out_dir, "coles-county-board-members.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    members = sum(len(v.get("members", [])) for k, v in payload.items()
                  if k != "board")
    print("coles: %d districts, %d members -> %s"
          % (len(payload) - 1, members, path))


if __name__ == "__main__":
    main()

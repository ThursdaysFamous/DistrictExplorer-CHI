#!/usr/bin/env python3
"""
Resolve scripts/rock_island_county_board_scraper.py's raw output into
data/app/rock-island-county-board-members.json, keyed by district ("1".."19" —
nineteen SINGLE-member districts, the most districts of any county on this
layer).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it by district number to the county's own drawn boundary
(services9.arcgis.com/6FnscPPlUa9DXXOk, Other_Layers layer 4). Rock Island is
rule-4 branch 2: the geometry is published, the officeholders are not on it —
the layer declares a NAME column and populates it on 0 of 19.

The Board Chairman and Vice-Chairman carry a `role` and stay on their own
district rows. Rock Island elects both from among its 19 district members, so
neither is a countywide seat; shipping the chair separately would imply a
twentieth member.

Usage:
    python3 build_rock_island_county_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = "https://www.rockislandcountyil.gov/263/County-Board"

# Nineteen single-member districts. Floors sit one under the full board so an
# ordinary vacancy does not block a weekly refresh, while a collapse leaves the
# last good file in place. The scraper additionally refuses any district holding
# two members, which is the failure this county's shape actually invites — the
# chairman appears twice on the page.
MIN_DISTRICTS = 18
MIN_MEMBERS = 18
MIN_PARTIES = 17

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    for key in ("role", "party"):
        if rec.get(key):
            member[key] = rec[key]
    # The county publishes each seat's full term, and the two cycles are
    # staggered (2022-2026 and 2024-2028 both sit on this board), so it belongs
    # on the member rather than the card. Labelled as the source labels it — a
    # term RANGE, not a next-election year like Lee's.
    if rec.get("term_start") and rec.get("term_end"):
        member["term"] = "%s-%s" % (rec["term_start"], rec["term_end"])
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
    rank = {"Board Chairman": 0, "Vice-Chairman": 1}
    for slot in roster.values():
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 2), m["name"]))
    return roster


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("members") if isinstance(payload, dict) else payload
    roster = resolve_roster(records or [])

    members = sum(len(v["members"]) for v in roster.values())
    parties = sum(1 for v in roster.values() for m in v["members"] if m.get("party"))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chairman"]
    overfull = sorted((d for d, v in roster.items() if len(v["members"]) > 1), key=int)
    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if members < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (members, MIN_MEMBERS))
    if parties < MIN_PARTIES:
        problems.append("%d parties (< %d)" % (parties, MIN_PARTIES))
    if overfull:
        problems.append("single-member districts holding two names: %s" % ", ".join(overfull))
    if len(chairs) > 1:
        problems.append("%d members tagged Board Chairman" % len(chairs))
    if problems:
        print("build-rock-island-board: FAIL — refusing to overwrite a good file with "
              "a partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "rock-island-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    print("build-rock-island-board: wrote %s — %d districts, %d members, %d parties, "
          "chair %s" % (out_path, len(roster), members, parties,
                        chairs[0]["name"] if chairs else "unresolved"))


if __name__ == "__main__":
    main()

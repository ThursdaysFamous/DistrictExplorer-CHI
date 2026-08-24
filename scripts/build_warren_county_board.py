#!/usr/bin/env python3
"""
Resolve scripts/warren_county_board_scraper.py's raw output into
data/app/warren-county-board-members.json, keyed by Warren County Board
district (4 districts seating 15 between them: 3/4/4/4).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/warren-county-board-districts.json by district.

THE DRIFT CHECK IS THE STRONGEST THIS ROUTE HAS. Warren's boundary was
dissolved from the legend of the county's own precinct map, and the scraper
re-reads that same legend every week — so the tripwire re-parses the exact
document the geometry came from, rather than a proxy for it. Any change to the
county's published table fails the run.

WHAT SHIPS: name, district, the committees the county lists, term-expiry year,
phone, e-mail, and the Chairman of the Board badge the page prints. WHAT DOES
NOT: the home address the county publishes for every member, which the scraper
identifies and drops by construction and which is asserted absent again here.

ONE E-MAIL IS MISSPELLED AT THE SOURCE — the county prints TWinkler at
"warrecountyil.gov", a domain missing the n. It ships exactly as published:
correcting it would be inventing an address the county did not give, and the
Carroll "Distirct" precedent says to carry a publisher's typo rather than
silently improve it.

Usage:
    python3 build_warren_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_warren_boundaries import COUNTY_COMPOSITION  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

BOARD_URL = "https://warrencountyil.gov/government/county-board/"

EXPECT_DISTRICTS = 4
EXPECT_MEMBERS = 15
SEATS = {"1": 3, "2": 4, "3": 4, "4": 4}
MIN_EMAILS = 12
MIN_TERMS = 12
STREET_RE = re.compile(
    r"\d+\s+\S+\s*(st|street|ave|avenue|rd|road|dr|drive|ln|lane|ct|court|"
    r"blvd|hwy|way|circle|cir|place|pl|trail)\b", re.I)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("warren-board-roster")


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def main():
    if len(sys.argv) < 2:
        fail("usage: build_warren_county_board.py <raw-scraper-output.json> "
             "[output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    # ---- the drift check: the legend IS the boundary's source ---------------
    legend = raw.get("composition") or {}
    if not legend:
        fail("the precinct map's legend yielded nothing — this county's only "
             "automatic redistricting warning did not run")
    want = {d: sorted(norm(p) for p in ps) for d, ps in COUNTY_COMPOSITION.items()}
    have = {str(d): sorted(norm(p) for p in ps) for d, ps in legend.items()}
    if have != want:
        for dnum in sorted(set(want) | set(have)):
            if want.get(dnum) != have.get(dnum):
                fail("district %s now reads %s in the county's precinct-map "
                     "legend, but the shipped boundary was dissolved from %s — "
                     "Warren reapportioned or re-precincted; re-measure against "
                     "the census fabric before shipping again "
                     "(scripts/build_warren_boundaries.py)"
                     % (dnum, ", ".join(sorted(legend.get(dnum, []))),
                        ", ".join(sorted(COUNTY_COMPOSITION.get(dnum, ())))))

    # ---- the roster --------------------------------------------------------
    roster = {}
    for dnum, members in (raw.get("districts") or {}).items():
        if str(dnum) not in COUNTY_COMPOSITION:
            fail("the board page names a district %r that does not exist" % dnum)
        entry = roster.setdefault(str(dnum), {"members": [], "sourceUrl": BOARD_URL})
        for rec in members:
            member = {"name": re.sub(r"\s+", " ", rec["name"]).strip()}
            for key in ("role", "phone", "email", "termExpires"):
                if rec.get(key):
                    member[key] = re.sub(r"\s+", " ", str(rec[key])).strip()
            if rec.get("committees"):
                member["committees"] = [re.sub(r"\s+", " ", c).strip()
                                        for c in rec["committees"]]
            entry["members"].append(member)

    if len(roster) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d"
             % (len(roster), EXPECT_DISTRICTS))
    total = sum(len(v["members"]) for v in roster.values())
    if total != EXPECT_MEMBERS:
        fail("parsed %d members, expected exactly %d" % (total, EXPECT_MEMBERS))
    for dnum, entry in roster.items():
        if len(entry["members"]) != SEATS[dnum]:
            fail("district %s carries %d member(s), expected %d"
                 % (dnum, len(entry["members"]), SEATS[dnum]))
        entry["members"].sort(key=lambda m: m["name"])
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    terms = sum(1 for v in roster.values() for m in v["members"] if m.get("termExpires"))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry an e-mail (floor %d)"
             % (emails, EXPECT_MEMBERS, MIN_EMAILS))
    if terms < MIN_TERMS:
        fail("only %d/%d members carry a term year (floor %d)"
             % (terms, EXPECT_MEMBERS, MIN_TERMS))
    # The privacy invariant, asserted on what is about to be written.
    for entry in roster.values():
        for member in entry["members"]:
            for key, value in member.items():
                if STREET_RE.search(str(value)):
                    fail("a residence reached %s's %s (%r) — the county prints "
                         "one per member and they are never carried"
                         % (member["name"], key, value))
    chairs = sorted(m["name"] for v in roster.values() for m in v["members"]
                    if (m.get("role") or "").lower().startswith("chairman of the board"))
    if len(chairs) != 1:
        fail("expected exactly one Chairman of the Board, got %s" % chairs)

    out_path = os.path.join(out_dir, "warren-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    print("warren-board-roster: wrote %s — %d districts seating %d (%d e-mails, "
          "%d phones, %d term years; Chairman of the Board %s)"
          % (os.path.relpath(out_path, REPO_ROOT), EXPECT_DISTRICTS, EXPECT_MEMBERS,
             emails, phones, terms, chairs[0]))
    print("  composition verified against the shipped dissolve, re-read from the "
          "county's own precinct-map legend: %s"
          % {d: len(p) for d, p in sorted(COUNTY_COMPOSITION.items())})


if __name__ == "__main__":
    main()

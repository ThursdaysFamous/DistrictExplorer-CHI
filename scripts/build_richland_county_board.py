#!/usr/bin/env python3
"""
Resolve scripts/richland_county_board_scraper.py's raw output into
data/app/richland-county-board-members.json, keyed by Richland County Board
district (7 single-member districts = 7 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/richland-county-board-districts.json by district
number.

THE DRIFT CHECK IS HALF THE POINT OF THIS BUILDER, not just the roster.
Richland's board districts are a DISSOLVE of its voting precincts
(build_richland_boundaries.py), composed from the county's OWN GIS rather than
from returns — so the shipped boundary stays correct only while that GIS keeps
publishing the same seven districts over the same twenty-one precincts. This
compares the layer inventory re-read from richlandil.wthgis.com against
COMPOSITION and COUNTY_PRECINCTS in the boundaries module and FAILS on any
disagreement. A red run here means the county redistricted or re-precincted,
and a human must re-derive the composition from the county's two GIS layers
before this county ships again.

WHAT THE CHECK CAN AND CANNOT SEE, said plainly because the alternative is a
green tick that covered nothing: it verifies that the county still publishes
SEVEN board districts and TWENTY-ONE precincts under the same names. It does
NOT re-run the spatial overlay that produced the composition, because that
needs the census fabric and shapely and does not belong in a weekly roster job.
So a county that redrew its lines while keeping seven districts and the same
twenty-one precinct names would pass this. That is a real limit; what it buys
is that every cheap way for this county to move is caught.

WHAT SHIPS: name, district, the county e-mail address the board page publishes
for each member, and the Chairman's role. WHAT DOES NOT: party, term and phone,
because the page publishes none of them for members — inventing any of the
three is exactly what the honesty rules forbid.

Usage:
    python3 build_richland_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_richland_boundaries import (COMPOSITION, COUNTY_PRECINCTS,  # noqa: E402
                                       SEATS_PER_DISTRICT)
from vtd_board_districts import norm  # noqa: E402

BOARD_URL = "https://richlandcounty.illinois.gov/county-board/"
GIS_URL = "https://richlandil.wthgis.com/"

EXPECT_DISTRICTS = 7
EXPECT_MEMBERS = EXPECT_DISTRICTS * SEATS_PER_DISTRICT      # 7 seats
MIN_EMAILS = 6          # measured 7/7; a page that stops publishing them fails

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("richland-board-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        fail("usage: build_richland_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    # ---- the drift check ---------------------------------------------------
    gis = raw.get("gis") or {}
    seen_districts = (gis.get("districtLayer") or {}).get("features")
    seen_precincts = (gis.get("precinctLayer") or {}).get("features")
    if not seen_districts or not seen_precincts:
        fail("the county's GIS yielded no layer inventory — this county's only "
             "automatic redistricting warning did not run")

    want_districts = {norm("DISTRICT %s" % d) for d in COMPOSITION}
    have_districts = {norm(d) for d in seen_districts}
    if want_districts != have_districts:
        fail("the county's GIS now publishes board districts %s, but the shipped "
             "boundary was dissolved for %s — the county redistricted; re-derive "
             "the composition from its two GIS layers before shipping again "
             "(scripts/build_richland_boundaries.py)"
             % (", ".join(sorted(seen_districts)),
                ", ".join("District %s" % d for d in sorted(COMPOSITION, key=int))))

    # The GIS writes the county seat's precincts long ("Olney Precinct 5") where
    # the ballot and the census write "OLNEY 5"; norm() collapses punctuation and
    # case but not that word, so it is dropped before comparing.
    def precinct_key(name):
        return norm(re.sub(r"\bprecinct\b", " ", str(name), flags=re.I))

    want_precincts = {precinct_key(p) for p in COUNTY_PRECINCTS}
    have_precincts = {precinct_key(p) for p in seen_precincts}
    if want_precincts != have_precincts:
        only_gis = sorted(p for p in seen_precincts if precinct_key(p) not in want_precincts)
        only_shipped = sorted(p for p in COUNTY_PRECINCTS if precinct_key(p) not in have_precincts)
        fail("the county's GIS precinct layer no longer matches the fabric the "
             "shipped boundary was dissolved from — GIS-only %s; shipped-only %s. "
             "The county re-precincted; re-measure against the census fabric "
             "before shipping again (scripts/build_richland_boundaries.py)"
             % (only_gis or "none", only_shipped or "none"))

    # ---- the roster --------------------------------------------------------
    roster = {}
    for rec in raw.get("records") or []:
        dnum = str(rec.get("district") or "")
        if dnum not in COMPOSITION:
            fail("the board page names a district %r that does not exist" % dnum)
        member = {"name": re.sub(r"\s+", " ", rec["name"]).strip()}
        if rec.get("role"):
            member["role"] = rec["role"]
        if rec.get("email"):
            member["email"] = rec["email"]
        entry = roster.setdefault(dnum, {"members": [], "sourceUrl": BOARD_URL})
        entry["members"].append(member)

    if len(roster) != EXPECT_DISTRICTS:
        fail("parsed %d districts, expected exactly %d" % (len(roster), EXPECT_DISTRICTS))
    total = sum(len(v["members"]) for v in roster.values())
    if total != EXPECT_MEMBERS:
        fail("parsed %d members, expected exactly %d (7 single-member districts)"
             % (total, EXPECT_MEMBERS))
    for dnum, entry in roster.items():
        if len(entry["members"]) != SEATS_PER_DISTRICT:
            fail("district %s carries %d member(s), expected %d"
                 % (dnum, len(entry["members"]), SEATS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"])
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry an e-mail (floor %d) — the board page "
             "changed shape" % (emails, EXPECT_MEMBERS, MIN_EMAILS))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role")]
    if len(chairs) > 1:
        fail("two members are badged with a role (%s) — the page names one Chairman"
             % ", ".join(m["name"] for m in chairs))

    out_path = os.path.join(out_dir, "richland-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("richland-board-roster: wrote %s — %d single-member districts (%d "
          "e-mails), chair %s" % (os.path.relpath(out_path, REPO_ROOT),
                                  EXPECT_DISTRICTS, emails,
                                  chairs[0]["name"] if chairs else "not marked"))
    print("  county GIS re-read from %s: %d board districts and %d precincts, "
          "both matching the shipped dissolve"
          % (GIS_URL, len(seen_districts), len(seen_precincts)))


if __name__ == "__main__":
    main()

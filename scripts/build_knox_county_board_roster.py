#!/usr/bin/env python3
"""Stage 2 of the Knox County Board roster pipeline: write data/app/knox-county-board-members.json.

The roster is the ROLL CALL of the county's own board minutes, because the page
that lists members cannot be read by any automated client (knoxcountyil.gov is a
403 to everyone) while the same website's documents are served plainly from its
Revize CMS. See scripts/knox_county_board_scraper.py for the anatomy.

WHAT SHIPS: fifteen members, three per district over five districts, each with
the district the county's own roll call puts them in, plus the Chair the same
minutes name. WHAT DOES NOT: party, term, phone, e-mail — the minutes publish
none of them and nothing here infers them. The board block carries the county's
switchboard and courthouse, the Calhoun/Clark posture of one number standing
for a board whose members publish no individual contact a machine can read.

ATTENDANCE NEVER SHIPS. The scraper records who was present and who was absent
because it must read both lists to find all fifteen seats, and a seat is not
vacated by missing a meeting. Which meeting somebody missed is not roster data
and would read as a judgement; it is dropped here.

EVERY ROW NAMES THE MINUTES IT CAME FROM. A roll call is a snapshot of one
evening: it cannot show a member seated the following week, and it is the
county's own record rather than an inference from election returns. Saying which
document and which meeting is the difference between a sourced roster and a
claim of currency this cannot support.

Usage:
    python3 scripts/build_knox_county_board_roster.py --raw raw.json
    python3 scripts/build_knox_county_board_roster.py            # scrape, then build
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_PATH = os.path.join(REPO, "data", "app", "knox-county-board-members.json")
SCRAPER = os.path.join(HERE, "knox_county_board_scraper.py")

EXPECTED_DISTRICTS = 5
SEATS_PER_DISTRICT = 3
EXPECTED_SEATS = EXPECTED_DISTRICTS * SEATS_PER_DISTRICT

BOARD = {
    "address": "Knox County Courthouse, 200 South Cherry Street, Galesburg, IL 61401",
    "phone": "(309) 345-3815",
    "phoneLabel": "County Clerk",
    "note": ("Members and districts come from the roll call of Knox County's own "
             "board minutes; the county's member page cannot be read by an "
             "automated client, so no per-member phone or e-mail is published here."),
    "sourceUrl": "https://www.knoxcountyil.gov/departments/county_board/",
}


def scrape_to_temp():
    fd, tmp = tempfile.mkstemp(suffix=".json", prefix="knox-raw-")
    os.close(fd)
    subprocess.run([sys.executable, SCRAPER, "-o", tmp], check=True)
    return tmp


def build(raw):
    def fail(msg):
        raise SystemExit("build-knox-board-roster: " + msg)

    seats = raw.get("seats") or []
    if len(seats) != EXPECTED_SEATS:
        fail("%d seats, expected %d — refusing to write" % (len(seats), EXPECTED_SEATS))
    chair = raw.get("chair")
    doc = raw.get("document")
    month = raw.get("meetingMonth")
    src = raw.get("source")

    by_district = {}
    for s in seats:
        by_district.setdefault(str(s["district"]), []).append(s)
    if len(by_district) != EXPECTED_DISTRICTS:
        fail("%d districts, expected %d" % (len(by_district), EXPECTED_DISTRICTS))
    for d, members in by_district.items():
        if len(members) != SEATS_PER_DISTRICT:
            fail("District %s carries %d members, expected %d"
                 % (d, len(members), SEATS_PER_DISTRICT))

    out = {}
    for d in sorted(by_district, key=int):
        rows = []
        for s in sorted(by_district[d], key=lambda x: x["name"]):
            row = {
                "name": s["name"],
                # The minutes, named on every row — a roll call is one evening's
                # record, not a standing claim.
                "districtSource": "roll call, %s minutes" % month,
            }
            if chair and s["name"] == chair:
                row["role"] = "Chair"
            rows.append(row)
        out[d] = {
            "members": rows,
            "seats": SEATS_PER_DISTRICT,
            "sourceUrl": src,
        }
    board = dict(BOARD)
    board["document"] = doc
    board["meeting"] = month
    board["documentUrl"] = src
    out["board"] = board
    return out, chair


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", help="scraper output JSON (default: run the scraper)")
    args = ap.parse_args()

    tmp = None
    try:
        path = args.raw or (tmp := scrape_to_temp())
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    out, chair = build(raw)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("build-knox-board-roster: wrote %s — %d districts, %d seats%s (%s)"
          % (os.path.relpath(OUT_PATH, REPO), EXPECTED_DISTRICTS, EXPECTED_SEATS,
             (", chair %s" % chair) if chair else "", raw.get("document")))


if __name__ == "__main__":
    main()

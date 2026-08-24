#!/usr/bin/env python3
"""
Resolve scripts/douglas_county_board_scraper.py's raw output into
data/app/douglas-county-board-members.json, keyed by Douglas County Board
district (7 single-member districts = 7 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it to data/app/douglas-county-board-districts.json by district
number.

TWO COUNTY DOCUMENTS, JOINED ON SURNAME, AND THE JOIN IS THE GUARD. The county
publishes no board members page at all, so the roster is assembled from the two
documents that each answer half of it: the annual COUNTY YEARBOOK names the
seven people and gives a county e-mail for each, and the certified ELECTION
SUMMARY REPORTS say which numbered district each of them won — in the county's
own numbering, the same one its GIS district layer uses. Neither alone is a
roster. This fails the run when they disagree about who sits on the board rather
than preferring one, because two county documents that stop naming the same
seven people is a thing a human should see.

WHY THE YEARBOOK'S OWN NUMBERS ARE NOT USED: it lists members "1. Tom
Hettinger", "2. Bibby Appleby", … which reads like a district column and is not
one. The certified returns put Hettinger in District 3 and Appleby in District
2; taking list position as district would misplace six of the seven.

WHAT SHIPS: name as the yearbook writes it (the county's own current form for
its own people), district from the returns, and the county e-mail. Each row also
carries the election that seated the member, because a certified return names
who WON rather than who holds the seat today (the Scott reasoning) and the
yearbook is what corroborates that they still do.

WHAT DOES NOT SHIP: the HOME ADDRESS the yearbook prints for every member, which
never ships; the term line, which reads "November 2024" / "November 2026" with
nothing saying whether that is the election that seated the member or the year
the term ends — and both readings contradict the returns for at least one member,
so it is not a fact worth rendering; and no phone, because none is published.

ONE PUBLISHED E-MAIL IS DROPPED, ON PURPOSE. The yearbook prints District 1's
address on the domain `douglascountuil.gov` — a typo for `douglascountyil.gov`,
which the other six all use. Shipping a knowingly dead address is worse than
shipping none, and silently correcting a character in someone's contact detail
is inventing data. The domain check below drops it and says so, and the card
shows six of seven with an e-mail.

Usage:
    python3 build_douglas_county_board.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_douglas_boundaries import EXPECTED_DISTRICTS, SEATS_PER_DISTRICT  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

YEARBOOK_LABEL = "Douglas County Yearbook"
SITE = "https://douglascountyil.gov"

EXPECT_MEMBERS = EXPECTED_DISTRICTS * SEATS_PER_DISTRICT      # 7 seats
COUNTY_EMAIL_DOMAIN = "douglascountyil.gov"
MIN_EMAILS = 5          # measured 6 of 7 — the seventh is a typo'd domain, see above

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")

SUFFIX_RE = re.compile(r"\b(jr|sr|ii|iii|iv)\b\.?$", re.I)


fail = make_fail("douglas-board-roster")


def surname(name):
    """Last real word of a name, for joining two county documents that write the
    same person differently ("Thomas Hettinger" / "Tom Hettinger", "Mary E.
    (Bibby) Appleby" / "Bibby Appleby")."""
    cleaned = re.sub(r"\([^)]*\)", " ", str(name))
    cleaned = SUFFIX_RE.sub("", cleaned.strip())
    parts = [p for p in re.split(r"\s+", cleaned.strip()) if p]
    return parts[-1].strip(".,").upper() if parts else ""


def main():
    if len(sys.argv) < 2:
        fail("usage: build_douglas_county_board.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        raw = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    book = raw.get("yearbook") or {}
    members = book.get("members") or []
    winners = (raw.get("returns") or {}).get("winners") or {}
    if len(members) != EXPECT_MEMBERS:
        fail("the yearbook yielded %d member(s), expected %d" % (len(members), EXPECT_MEMBERS))
    if sorted(winners, key=int) != [str(i) for i in range(1, EXPECTED_DISTRICTS + 1)]:
        fail("the certified returns name winners for districts %s, expected 1-%d"
             % (sorted(winners), EXPECTED_DISTRICTS))

    by_surname = {}
    for dnum, win in winners.items():
        key = surname(win["name"])
        if key in by_surname:
            fail("two districts were won by a %r — this join needs a distinguishing "
                 "name and cannot use surname alone" % key)
        by_surname[key] = (dnum, win)

    roster, dropped = {}, []
    for person in members:
        key = surname(person["name"])
        if key not in by_surname:
            fail("the yearbook names %r, whom no certified district contest elected "
                 "— the county's two documents disagree about who is on the board, "
                 "and a human should decide which is right" % person["name"])
        dnum, win = by_surname.pop(key)
        member = {"name": re.sub(r"\s+", " ", person["name"]).strip(),
                  "districtSource": "elected %s (certified county canvass)" % win["election"]}
        email = (person.get("email") or "").strip()
        if email:
            domain = email.rsplit("@", 1)[-1].lower()
            if domain == COUNTY_EMAIL_DOMAIN:
                member["email"] = email
            else:
                dropped.append((person["name"], email))
        roster[dnum] = {"members": [member], "sourceUrl": SITE,
                        "sourceLabel": "%s (%s)" % (YEARBOOK_LABEL, book.get("date", "")[:4])}
    if by_surname:
        fail("the certified returns elected %s, whom the yearbook does not list — the "
             "county's two documents disagree about who is on the board"
             % ", ".join(w["name"] for _, w in by_surname.values()))

    if len(roster) != EXPECTED_DISTRICTS:
        fail("parsed %d districts, expected exactly %d" % (len(roster), EXPECTED_DISTRICTS))
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    if emails < MIN_EMAILS:
        fail("only %d/%d members carry a county e-mail (floor %d) — the yearbook "
             "changed shape" % (emails, EXPECT_MEMBERS, MIN_EMAILS))

    out_path = os.path.join(out_dir, "douglas-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print("douglas-board-roster: wrote %s — %d single-member districts (%d county "
          "e-mails)" % (os.path.relpath(out_path, REPO_ROOT), EXPECTED_DISTRICTS, emails))
    for name, email in dropped:
        print("  DROPPED a published e-mail for %s: %r is not on %s — shipping a dead "
              "address is worse than shipping none, and correcting it would be "
              "inventing data" % (name, email, COUNTY_EMAIL_DOMAIN))


if __name__ == "__main__":
    main()

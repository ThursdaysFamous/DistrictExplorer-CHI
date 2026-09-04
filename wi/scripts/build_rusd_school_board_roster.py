#!/usr/bin/env python3
"""
Build data/app/rusd-school-board-members.json from the scraper's intermediate.

The count guards are the point. RUSD's page is a CMS whose fragments can be
reordered, and the scraper already refuses a shift by requiring each seat's own
"District N Schools" label to agree with the heading above it; this file
refuses a THINNING — a page that still parses and quietly stops publishing
phones, e-mails or terms.

ONE VACANCY IS ROUTINE HERE AND TWO IS NOT. District 2 has been empty since
2026-08-20 by RUSD's own notice, so the named floor is eight of nine rather
than nine; a second empty seat fails, because at that point somebody should
look at the page rather than at this roster. The vacancy is never dropped —
the seat ships carrying `vacant`, so the card can say the seat is empty rather
than saying nothing, which reads to a reader as a layer that does not know.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RAW = os.path.join(SCRIPT_DIR, ".cache", "rusd_school_board_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "rusd-school-board-members.json")

EXPECT_SEATS = [str(n) for n in range(1, 10)]
MIN_NAMED = 8
MIN_PHONES = 8
MIN_EMAILS = 8
MIN_TERMS = 8
MAX_VACANT = 1

BOARD_URL = "https://www.rusd.org/o/rusd/page/board-of-education"


def main():
    if not os.path.exists(RAW):
        raise SystemExit("no intermediate at %s — run rusd_school_board_scraper.py" % RAW)
    raw = json.load(open(RAW))
    members = raw["members"]

    if sorted(members, key=int) != EXPECT_SEATS:
        raise SystemExit("intermediate carries seats %s, expected %s"
                         % (sorted(members, key=int), EXPECT_SEATS))

    named = [d for d, r in members.items() if r.get("name")]
    vacant = [d for d, r in members.items() if r.get("vacant")]
    phones = sum(1 for r in members.values() if r.get("phone"))
    emails = sum(1 for r in members.values() if r.get("email"))
    terms = sum(1 for r in members.values() if r.get("termExpires"))

    if len(named) < MIN_NAMED:
        raise SystemExit("only %d of 9 seats named (floor %d)" % (len(named), MIN_NAMED))
    if len(vacant) > MAX_VACANT:
        raise SystemExit(
            "%d seats vacant (%s) against the %d this roster expects — read RUSD's "
            "page before shipping; a second vacancy is news, not routine"
            % (len(vacant), sorted(vacant), MAX_VACANT))
    if set(named) & set(vacant):
        raise SystemExit("seat(s) %s are both named and vacant"
                         % sorted(set(named) & set(vacant)))
    if phones < MIN_PHONES or emails < MIN_EMAILS or terms < MIN_TERMS:
        raise SystemExit(
            "contact or terms thinned: %d phones, %d e-mails, %d terms "
            "(floors %d/%d/%d) — the page still parses and has stopped publishing"
            % (phones, emails, terms, MIN_PHONES, MIN_EMAILS, MIN_TERMS))

    out = {"members": members,
           "office": {"boardUrl": BOARD_URL},
           "sourceUrl": raw.get("sourceUrl", BOARD_URL)}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("wrote data/app/%s — %d seats (%d named, %d vacant by RUSD's own notice), "
          "%d phones, %d e-mails, %d terms"
          % (os.path.basename(OUT), len(members), len(named), len(vacant),
             phones, emails, terms), file=sys.stderr)


if __name__ == "__main__":
    main()

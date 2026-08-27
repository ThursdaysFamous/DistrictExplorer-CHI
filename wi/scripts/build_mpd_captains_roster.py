#!/usr/bin/env python3
"""
Build data/app/mpd-district-captains.json from mpd_captains_scraper.py's
output — the roster that retires gap `mpd-district-leadership` (the
2026-08-27 recon measured the city's district pages answering PLAIN from
CI, with each district's commanding officer as a heading).

Count guards, the roster pattern: exactly districts 1-7; at least 6
named (a page that names nobody ships null and the card keeps its
link-only behavior there — never a guess); a name under two districts
refuses upstream in the scraper. Phones ride where the city Directory
page paired them (the 414-935-72x2 block, measured one per district).

Weekly CI re-runs this via update-mpd-captains-roster.yml, which opens a
PR for human review — officeholder-adjacent names never auto-commit.

Usage:
    python3 wi/scripts/build_mpd_captains_roster.py /tmp/mpd_captains.json
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT = os.path.join(REPO_ROOT, "data", "app", "mpd-district-captains.json")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_mpd_captains_roster.py <scrape.json>")
    doc = json.load(open(sys.argv[1]))
    districts = doc.get("districts") or {}
    if sorted(districts) != [str(n) for n in range(1, 8)]:
        raise SystemExit("expected districts 1-7, got %s" % sorted(districts))
    named = 0
    for n, rec in districts.items():
        if rec.get("district") != n:
            raise SystemExit("district key %s carries district %r"
                             % (n, rec.get("district")))
        if not (rec.get("sourceUrl") or "").startswith(
                "https://city.milwaukee.gov/police/districts/District-"):
            raise SystemExit("district %s sourceUrl is not the city's own "
                             "district page" % n)
        if rec.get("name"):
            if not rec.get("rank"):
                raise SystemExit("district %s has a name but no rank" % n)
            named += 1
    if named < 6:
        raise SystemExit("only %d of 7 districts named — floor 6; the page "
                         "structure moved, re-measure" % named)

    # FLAT, keyed by district at the top level (the polling files' shape):
    # validate_index floors the file on its top-level keys, so a wrapper
    # object would read as 2 entries; the scrape date rides each record
    as_of = doc.get("scrapedAt", "")[:10]
    out = {}
    for n in sorted(districts, key=int):
        rec = dict(districts[n])
        rec["asOf"] = as_of
        out[n] = rec
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote %s — %d/7 districts named, %d with phones"
          % (os.path.relpath(OUT, REPO_ROOT), named,
             sum(1 for r in districts.values() if r.get("phone"))),
          file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build stage 2: ia/data/app/ia-county-board-chairs.json.

Reads the scraper's cache and writes the roster the County Supervisor card
joins by name. A SEPARATE FILE FROM `ia-county-officers.json` ON PURPOSE:
that file is rebuilt weekly from its own sources, so writing chairs into it
would have each pipeline silently erase the other's work. This is the shape
Illinois already uses for Lake County's board roles -- a roles file that
joins to a members file by name -- and the join is the card's, not the
builder's, so a chair who leaves the board simply stops rendering.

WHAT THIS REFUSES TO WRITE, AND WHY EACH ONE IS HERE
-----------------------------------------------------
* Fewer than MIN_COUNTIES resolved. The floor is deliberately BELOW the 36
  measured, because the source is 98 separate county websites and one of them
  redesigning a page is ordinary churn, not a broken parser. What the floor
  catches is a COLLAPSE -- the parser stopped working, or the network did.
  Per-county loss is `check_roster_retention.py`'s job once this file ships.
* A chair who is not on that county's own supervisor roster. The scraper
  already gates on this; the builder re-gates because the two stages run
  against `ia-county-officers.json` at different times and that file has its
  own weekly refresh. A name that no longer appears there is DROPPED, never
  carried forward on the strength of last week's scrape.
* Any county the scraper reported with two candidates. It collapses those to
  `many` itself and none of 98 produced one, so this is an assertion about a
  thing that has never happened rather than a filter that does work.

Every join whose page form differs from the roster form is PRINTED on every
run -- `Mr. Mike Hadley` against Keokuk's `Michael C. Hadley` -- so a reviewer
sees the four inexact matches rather than trusting a diminutive table.

Usage:
    python3 ia/scripts/build_ia_county_chair.py [--check]
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "app")
CACHE = os.path.join(HERE, ".cache", "ia_county_chairs.json")
OFFICERS = os.path.join(DATA, "ia-county-officers.json")
OUT_PATH = os.path.join(DATA, "ia-county-board-chairs.json")

MIN_COUNTIES = 30           # measured 35 of 98 on 2026-09-05 (36 before the
                            # qualified-chair and expired-term refusals)
SOURCE_NOTE = ("each county's own board-of-supervisors page, paired "
               "structurally and gated on the county's supervisor roster")


def build(rows, officers):
    out, inexact, dropped = {}, [], []
    for r in sorted(rows, key=lambda x: x["fips"]):
        if r.get("verdict") != "one":
            continue
        assert r.get("chair"), "a verdict of one with no chair: %r" % r
        fips = "19" + r["fips"]
        roster = [m["name"] for m in (officers.get(fips) or {}).get("supervisors", [])]
        if r["chair"] not in roster:
            dropped.append((r["county"], r["chair"]))
            continue
        rec = {"county": r["county"], "chair": r["chair"],
               "sourceUrl": r["sourceUrl"]}
        if r.get("match") != "exact":
            rec["pageName"] = r["pageName"]
            rec["match"] = r["match"]
            inexact.append((r["county"], r["chair"], r["pageName"], r["match"]))
        out[fips] = rec
    return out, inexact, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="compare against the shipped file and exit non-zero on drift")
    args = ap.parse_args()

    if not os.path.exists(CACHE):
        sys.exit("build-ia-county-chair: FAIL — no scraper cache at %s; run "
                 "ia/scripts/ia_county_chair_scraper.py first" % CACHE)
    rows = json.load(open(CACHE, encoding="utf-8"))
    officers = json.load(open(OFFICERS, encoding="utf-8"))
    out, inexact, dropped = build(rows, officers)

    for county, chair in dropped:
        print("  DROPPED %s: %r is not on the county's supervisor roster" % (county, chair))
    for county, chair, page, how in inexact:
        print("  name join (%s) %s: roster %r <- page %r" % (how, county, chair, page))

    if len(out) < MIN_COUNTIES:
        sys.exit("build-ia-county-chair: FAIL — %d counties resolved, floor is %d"
                 % (len(out), MIN_COUNTIES))

    payload = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.check:
        have = open(OUT_PATH, encoding="utf-8").read() if os.path.exists(OUT_PATH) else ""
        if have != payload:
            sys.exit("build-ia-county-chair: FAIL — %s is not what this scrape "
                     "produces (%d counties)" % (OUT_PATH, len(out)))
        print("build-ia-county-chair: OK — %d counties, shipped file current" % len(out))
        return
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(payload)
    print("build-ia-county-chair: OK — wrote %d county board chairs to %s"
          % (len(out), OUT_PATH))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/mps-school-board-members.json from mps_school_board_scraper.py's
intermediate — the nine Milwaukee Board of School Directors (at-large
president + districts 1-8), keyed "AL" and "1".."8" to match the geometry
file's DISTRICT property.

The scraper's per-seat contact links are all the SAME JustFOIA form (the
board's one shared contact route, measured at first build), so they collapse
to a board-level contactUrl; if the district ever publishes per-director
forms, the divergence keeps them per-member automatically. Floors: all nine
seats named, the at-large seat present, at least seven term expirations
(staggered April terms), the office phone and e-mail both present.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RAW = os.path.join(SCRIPT_DIR, ".cache", "mps_school_board_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "mps-school-board-members.json")


def main():
    with open(RAW) as f:
        raw = json.load(f)
    members = raw["members"]
    office = raw["office"]
    expect = ["AL"] + [str(n) for n in range(1, 9)]
    if sorted(members) != sorted(expect):
        raise SystemExit("intermediate carries seats %s" % sorted(members))
    if sum(1 for m in members.values() if m.get("termExpires")) < 7:
        raise SystemExit("fewer than 7 term expirations parsed — the seat blocks moved")
    if not office.get("phone") or not office.get("email"):
        raise SystemExit("office contact incomplete: %r" % office)

    urls = {m.get("contactUrl") for m in members.values() if m.get("contactUrl")}
    if len(urls) == 1:
        office["contactUrl"] = urls.pop()
        for m in members.values():
            m.pop("contactUrl", None)

    out = {"members": members, "office": office, "sourceUrl": raw["sourceUrl"]}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    print("mps-school-board-members.json: 9 directors (%d with terms; board "
          "contact %s) -> %s"
          % (sum(1 for m in members.values() if m.get("termExpires")),
             "collapsed to office" if "contactUrl" in office else "per-member",
             os.path.relpath(OUT, REPO_ROOT)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/ia-judicial-judges.json from the iowacourts.gov scrape --
stage 2 of the pair (ia_judicial_district_scraper.py is stage 1).

Keyed by DISTRICT NUMBER (1-8) as a string -- the same key
build_ia_judicial_district.py stamps on the geometry's `district` property,
so the card's join cannot disagree with the map.

No phone, e-mail, or courthouse address ships: neither the roster listing
page nor a sampled individual profile page (fetched 2026-08-28) publishes
either for any judge, on any of the 8 districts -- measured, not assumed.
The only fields are a judge's name and their own page's title/role string,
shipped verbatim (ia_judicial_district_scraper.py's docstring records why it
is not parsed into rank + sub-district).

Floors (refuses to write otherwise): exactly 8 districts; >= 250 judges
total; every district carries at least one judge.

Usage:
    python3 ia/scripts/build_ia_judicial_district_roster.py
    python3 ia/scripts/build_ia_judicial_district_roster.py --in <path>   # alternate cache file
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache",
                    "ia_judicial_district_judges.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "ia-judicial-judges.json")

EXPECT_DISTRICTS = 8
MIN_JUDGES = 250


def main():
    raw_path = sys.argv[sys.argv.index("--in") + 1] if "--in" in sys.argv else RAW
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    if len(raw) != EXPECT_DISTRICTS:
        raise SystemExit("scrape carries %d districts, expected %d" % (len(raw), EXPECT_DISTRICTS))

    out = {}
    total = 0
    for dist_key in sorted(raw, key=int):
        entry = raw[dist_key]
        judges = [{"name": j["name"], "role": j["role"]} for j in entry.get("judges", []) if j.get("name")]
        if not judges:
            raise SystemExit("district %s parsed with no judges" % dist_key)
        total += len(judges)
        out[dist_key] = {"judges": judges, "sourceUrl": entry["url"]}

    if total < MIN_JUDGES:
        raise SystemExit("only %d judges across the bench (floor %d)" % (total, MIN_JUDGES))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    print("wrote %s -- %d districts, %d judges" % (OUT, len(out), total))


if __name__ == "__main__":
    main()

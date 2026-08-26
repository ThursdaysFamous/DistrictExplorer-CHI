#!/usr/bin/env python3
"""
Build data/app/wi-court-of-appeals-roster.json from the wicourts COA scrape —
stage 2 of the pair (wi_coa_scraper.py is stage 1, and it already asserted the
seat counts, the 16-judge total and the statutory composition before writing
its intermediate).

Keyed "1"-"4", matching the DISTRICT property build_wi_court_of_appeals.py
stamps on the geometry. Judges carry role and phone exactly as wicourts
prints them (Chief Judge is the court's own chief; Presiding Judge each
district's) — no e-mail exists on the host, so none ships.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "wi_coa_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "wi-court-of-appeals-roster.json")

EXPECT_SEATS = {"1": 4, "2": 4, "3": 3, "4": 5}


def main():
    raw_path = sys.argv[sys.argv.index("--in") + 1] if "--in" in sys.argv else RAW
    with open(raw_path) as f:
        raw = json.load(f)

    out = {}
    for did, expect in EXPECT_SEATS.items():
        block = raw.get(did)
        if not block or len(block["judges"]) != expect:
            raise SystemExit("district %s missing or off its %d-seat count" % (did, expect))
        judges = []
        for j in block["judges"]:
            entry = {"name": j["name"]}
            if j.get("role"):
                entry["role"] = j["role"]
            if j.get("phone"):
                entry["phone"] = j["phone"]
            judges.append(entry)
        out[did] = {
            "judges": judges,
            "chambers": block.get("address") or [],
        }

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    total = sum(len(d["judges"]) for d in out.values())
    print("wrote %s — 4 districts, %d judges" % (OUT, total))


if __name__ == "__main__":
    main()

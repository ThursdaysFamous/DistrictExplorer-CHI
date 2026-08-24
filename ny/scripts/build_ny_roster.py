#!/usr/bin/env python3
"""
Resolve the raw NY legislature scrape (ny_legislature_scraper.py) into the two
app-data roster files:
    data/app/ny-senate-members.json    { "<district>": {"name", "party"} }
    data/app/ny-assembly-members.json  { "<district>": {"name", "party"} }

Stage 2 of the two-stage pipeline (METRO_EXPANSION_PLAYBOOK §9). Dedupes the
session-member list to one current officeholder per district (incumbent
preferred), and REFUSES to overwrite a roster below its count floor so a partial
scrape can't ship. Party is null (the source doesn't publish it — never guessed).

Usage:
    python3 scripts/build_ny_roster.py [--in PATH]
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(REPO, "data", "app")
DEFAULT_IN = os.path.join(os.path.dirname(__file__), ".cache", "ny_legislature_raw.json")

# floors: 63 senate / 150 assembly districts; allow a little vacancy slack.
FLOORS = {"SENATE": 60, "ASSEMBLY": 145}
OUT = {"SENATE": "ny-senate-members.json", "ASSEMBLY": "ny-assembly-members.json"}


def _coverage_line(roster):
    """Per-field coverage one-liner (CHI fleet-status convention): makes
    parser drift visible at a glance in the weekly run logs. Honest nulls
    stay honest — this reports them, it never fills them."""
    rows = []
    for v in roster.values():
        if isinstance(v, dict):
            rows.append(v)
        elif isinstance(v, list):
            rows.extend(x for x in v if isinstance(x, dict))
    if not rows:
        return None
    fields = sorted({k for r in rows for k in r})
    return "  ".join("%s=%d/%d" % (f, sum(1 for r in rows if r.get(f)), len(rows)) for f in fields)


def resolve(records, chamber):
    by_district = {}
    for r in records:
        if r.get("chamber") != chamber:
            continue
        d = r.get("district")
        name = (r.get("name") or "").strip()
        if d is None or not name:
            continue
        key = str(int(d))
        prev = by_district.get(key)
        # prefer an incumbent; otherwise keep the first seen
        if prev is None or (r.get("incumbent") and not prev.get("_incumbent")):
            entry = {"name": name, "party": r.get("party"), "_incumbent": bool(r.get("incumbent"))}
            if r.get("districtOffice"):
                entry["districtOffice"] = r["districtOffice"]
            if r.get("capitolOffice"):
                entry["capitolOffice"] = r["capitolOffice"]
            if r.get("url"):
                entry["url"] = r["url"]
            by_district[key] = entry
    for v in by_district.values():
        v.pop("_incumbent", None)
    return by_district


def main():
    in_path = DEFAULT_IN
    argv = sys.argv[1:]
    if "--in" in argv:
        in_path = argv[argv.index("--in") + 1]
    if not os.path.exists(in_path):
        print("no scrape input at %s (run ny_legislature_scraper.py first)" % in_path, file=sys.stderr)
        sys.exit(2)

    raw = json.load(open(in_path))
    records = raw.get("members", [])

    for chamber, fname in OUT.items():
        roster = resolve(records, chamber)
        floor = FLOORS[chamber]
        if len(roster) < floor:
            print("REFUSING to write %s: %d districts < floor %d" % (fname, len(roster), floor), file=sys.stderr)
            sys.exit(1)
        roster = {k: roster[k] for k in sorted(roster, key=lambda x: int(x))}
        path = os.path.join(APP, fname)
        with open(path, "w") as f:
            json.dump(roster, f, indent=0, ensure_ascii=False)
        print("wrote data/app/%s: %d districts" % (fname, len(roster)), file=sys.stderr)
    cov = _coverage_line(roster)
    if cov:
        print("field coverage: %s" % cov, file=sys.stderr)


if __name__ == "__main__":
    main()

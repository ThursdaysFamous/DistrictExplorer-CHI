#!/usr/bin/env python3
"""
Resolve the CEC scrape (cec_scraper.py) into
data/app/cec-members.json  { "<district>": {"members": [{"name"}, ...]} }.

Stage 2 of the pipeline (METRO_EXPANSION_PLAYBOOK §9). Refuses to overwrite the
existing roster below the council floor, so a partial or WAF-blocked scrape can't
replace real data (or a good roster) with a broken one. Until the scrape reliably
resolves the councils, data/app/cec-members.json stays the empty placeholder and
the CEC card links to the council page (§7).

Usage:
    python3 scripts/build_cec_roster.py [--in PATH]
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "app", "cec-members.json")
DEFAULT_IN = os.path.join(os.path.dirname(__file__), ".cache", "cec_raw.json")
MIN_COUNCILS = 28  # 32 district councils; require most before shipping


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


def main():
    argv = sys.argv[1:]
    in_path = argv[argv.index("--in") + 1] if "--in" in argv else DEFAULT_IN
    if not os.path.exists(in_path):
        print("no scrape input at %s — keeping the existing cec-members.json placeholder." % in_path, file=sys.stderr)
        return

    councils = json.load(open(in_path)).get("councils", {})
    roster = {}
    for district, rec in councils.items():
        members = [{"name": m["name"]} for m in rec.get("members", []) if m.get("name")]
        if members:
            roster[str(int(district))] = {"members": members}

    if len(roster) < MIN_COUNCILS:
        print("Not writing cec-members.json: only %d councils resolved (< %d) — keeping placeholder."
              % (len(roster), MIN_COUNCILS), file=sys.stderr)
        # exit 0: a short CEC scrape is expected until the URL map is confirmed;
        # this is not a hard pipeline failure, just "no update this run".
        return

    roster = {k: roster[k] for k in sorted(roster, key=lambda x: int(x))}
    with open(OUT, "w") as f:
        json.dump(roster, f, indent=0, ensure_ascii=False)
    print("wrote data/app/cec-members.json: %d councils" % len(roster), file=sys.stderr)
    cov = _coverage_line(roster)
    if cov:
        print("field coverage: %s" % cov, file=sys.stderr)


if __name__ == "__main__":
    main()

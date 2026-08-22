#!/usr/bin/env python3
"""
Resolve scripts/ccbr_scraper.py's raw output into one record per Board of
Review district and write it as the JSON app-data file the CCBR card reads:
data/app/ccbr-roster.json, keyed by district number ("1"/"2"/"3").

index.html fetches this file lazily on first click (same-origin, network-first
via the service worker) and joins it to the pre-built PA 102-0012 district
geometry the app already ships (data/app/ccbr-districts.json). Same two-stage
build pattern as scripts/ccpsa_scraper.py + scripts/build_ccpsa_roster.py.

Usage:
    python3 build_ccbr_roster.py ccbr_commissioners.json [output_dir]

output_dir defaults to the repo's data/app/ directory.
"""

import json
import os
import re
import sys


def normalize_phone(raw):
    """10 digits -> "(312) 603-2676"; anything else passes through untouched
    (never drop a number the site published just because it's oddly shaped —
    but the common case, a US 10-digit line mangled by markup splits, comes
    out uniform)."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        return "(%s) %s-%s" % (digits[:3], digits[3:6], digits[6:])
    return raw

# The Board of Review is exactly three elected commissioners, one per PA
# 102-0012 district. Refuse to write anything else: a scrape that resolves
# fewer (template change, page error) or maps two commissioners to one
# district (parser bug) must never silently replace good data — same safety
# net as build_ccpsa_roster.py's MIN_COUNCILS.
EXPECTED_DISTRICTS = {1, 2, 3}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def resolve_roster(records):
    roster = {}
    for record in records:
        if record.get("error"):
            continue
        district = record.get("district_number")
        name = (record.get("name") or "").strip()
        if district is None or not name:
            continue
        key = str(int(district))
        if key in roster:
            print("FATAL: two commissioners resolved to district %s (%r and %r)"
                  % (key, roster[key]["name"], name), file=sys.stderr)
            sys.exit(1)
        entry = {"name": name}
        if record.get("url"):
            entry["url"] = record["url"]
        # First on-page email only — the pages list at most one (the district
        # inbox). Districts publishing none (District 2 used a contact form as
        # of 2026-07-20) honestly omit the key.
        emails = record.get("emails") or []
        if emails:
            entry["email"] = emails[0]
        # PHONES ARE NOT TAKEN IN DOCUMENT ORDER, and the comment this replaced
        # said they were ("the pages list at most one of each"). That was true
        # when it was written and false by 2026-08-22: every commissioner page
        # now carries several numbers in body copy, and the FIRST one was an SMS
        # shortcode on District 3 ("Text EZJOIN to 872-345-4747", shipped as the
        # office phone for weeks) and an event RSVP line on District 2 (PR #425,
        # caught in review). The scraper now marks which numbers are presented
        # as the commissioner's own contact — same sentence as the district
        # inbox — and only those are eligible. There is deliberately NO FALLBACK
        # to the raw list: a district that publishes no phone shows none.
        phones = record.get("contact_phones") or []
        if phones:
            entry["phone"] = normalize_phone(phones[0])
        roster[key] = entry
    return roster


def main():
    if len(sys.argv) < 2:
        print("usage: build_ccbr_roster.py <scraper_output.json> [output_dir]", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1]) as f:
        records = json.load(f)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = resolve_roster(records)
    got = {int(k) for k in roster}
    if got != EXPECTED_DISTRICTS:
        print("FATAL: resolved districts %s, expected exactly %s — refusing to write"
              % (sorted(got), sorted(EXPECTED_DISTRICTS)), file=sys.stderr)
        sys.exit(1)

    out_path = os.path.join(out_dir, "ccbr-roster.json")
    with open(out_path, "w") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote %s: %d commissioners (districts %s)"
          % (out_path, len(roster), ", ".join(sorted(roster))), file=sys.stderr)


if __name__ == "__main__":
    main()

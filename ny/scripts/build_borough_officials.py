#!/usr/bin/env python3
"""
Build data/app/borough-officials.json (Borough President + District Attorney
+ County Clerk) from the operator-maintained scripts/borough_officials_source.json
(METRO_EXPANSION_PLAYBOOK §9, §11.3).

There is no clean machine-readable roster for these 10 offices, and they change
only every 4 years, so — unlike the scraped rosters — this is an operator step:
edit the source JSON with hand-verified names + official URLs, then run this.
Only entries with a non-null name are emitted (a null name -> the card links to
the NYC Green Book and names no one). Officeholder data is never guessed.

Output shape: { "<Borough>": { "bp": {"name","url"}, "da": {"name","url"},
"clerk": {"name"?,"url","address"?,"phone"?} } }. Clerk entries are emitted even
without a name (the office/link rows are verifiable on their own; NYC County
Clerks are appointed and only some offices publish the incumbent's name).

Usage:
    python3 scripts/build_borough_officials.py
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(__file__), "borough_officials_source.json")
OUT = os.path.join(REPO, "data", "app", "borough-officials.json")
BOROUGHS = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]


def clean(entry, allow_nameless=False):
    if not entry:
        return None
    name = (entry.get("name") or "").strip()
    if not name and not allow_nameless:
        return None
    out = {}
    if name:
        out["name"] = name
    for field in ("url", "address", "phone"):
        value = (entry.get(field) or "").strip()
        if value:
            out[field] = value
    return out or None


def main():
    src = json.load(open(SRC)).get("boroughs", {})
    roster = {}
    filled = 0
    for boro in BOROUGHS:
        row = src.get(boro, {})
        entry = {}
        for role in ("bp", "da", "clerk"):
            # elected BP/DA rows require a name; the appointed clerk's office
            # row is verifiable without one (see the source's _verified note).
            person = clean(row.get(role), allow_nameless=(role == "clerk"))
            if person:
                entry[role] = person
                filled += 1
        if entry:
            roster[boro] = entry

    with open(OUT, "w") as f:
        json.dump(roster, f, indent=0, ensure_ascii=False)
    if filled == 0:
        print("wrote data/app/borough-officials.json: EMPTY — no names filled in the source yet "
              "(operator step §11.3; cards link to the NYC Green Book until then).", file=sys.stderr)
    else:
        print("wrote data/app/borough-officials.json: %d of 15 offices filled" % filled, file=sys.stderr)


if __name__ == "__main__":
    main()

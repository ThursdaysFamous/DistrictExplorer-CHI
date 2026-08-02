#!/usr/bin/env python3
"""
Resolve scripts/il_county_commissioners_scraper.py's raw output into
data/app/il-county-commissioners.json — the at-large county boards the COUNTY
card renders.

Why this file exists separately from the county-board layer: a county that
elects its board at large has no district geometry, so there is nothing for a
`county-board` dispatch entry to join. Its members represent every resident of
the county, which is exactly what the county card already answers
(docs/EXPANSION_GUIDE.md §1.5). Adding one of these counties therefore adds no
layer, no toggle and no dispatch entry — only rows on a card that already
renders.

Keyed by county name normalized to uppercase letters only ("STCLAIR"), the
SAME key data/app/il-county-clerks.json uses, so index.html performs one
lookup shape for both rosters.

Usage:
    python3 build_county_commissioners.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

# Every county here elects at large. The per-county seat count is the real
# guard — a board that suddenly parses one member short means the page changed
# shape, and that must not ship quietly. The range below is the backstop for a
# county added to the scraper before this table.
MIN_MEMBERS = 3
MAX_MEMBERS = 9
EXPECT_MEMBERS = {
    "MONROE": 3, "RANDOLPH": 3,      # commission form, 3 commissioners
    "PIKE": 9, "PUTNAM": 5, "BROWN": 7, "CALHOUN": 5,
    "SCHUYLER": 7,                   # pass-8; at-large proven from the canvass
}
MIN_COUNTIES = 7
ALLOWED_ROLES = ("Chairman", "Vice Chairman", "Vice-Chairman",
                 "Commissioner", "Board Member")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def fail(msg):
    print("county-commissioners-roster: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def norm_key(name):
    return re.sub(r"[^A-Z]", "", re.sub(r"\s*COUNTY\s*$", "", (name or "").upper()))


def main():
    if len(sys.argv) < 2:
        fail("usage: build_county_commissioners.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        counties = json.load(f)["counties"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster = {}
    for key, block in counties.items():
        members = block.get("members") or []
        if not (MIN_MEMBERS <= len(members) <= MAX_MEMBERS):
            fail("%s parsed %d members, outside the %d-%d an at-large board should have"
                 % (key, len(members), MIN_MEMBERS, MAX_MEMBERS))
        seats = EXPECT_MEMBERS.get(key)
        if seats is not None and len(members) != seats:
            fail("%s parsed %d members, the county seats %d — the page's shape "
                 "changed, or the board did. Re-read it before shipping."
                 % (key, len(members), seats))
        names = [m.get("name") for m in members]
        if len(set(names)) != len(names):
            fail("%s has duplicate member names (%s)" % (key, ", ".join(sorted(names))))
        chairs = [m["name"] for m in members if m.get("role") == "Chairman"]
        if len(chairs) > 1:
            fail("%s marks %d chairmen (%s) — a board has one" % (key, len(chairs), ", ".join(chairs)))
        clean_members = []
        for m in members:
            if not m.get("name"):
                fail("%s has a member with no name" % key)
            role = m.get("role")
            if role and role not in ALLOWED_ROLES:
                fail("%s: unrecognized role %r for %s" % (key, role, m["name"]))
            entry = {"name": m["name"]}
            for f_ in ("role", "phone", "email", "since"):
                if m.get(f_):
                    entry[f_] = m[f_]
            clean_members.append(entry)

        expected = norm_key(block.get("county"))
        if expected and expected != key:
            fail("%s is keyed inconsistently with its county name %r (expected key %s)"
                 % (key, block.get("county"), expected))

        out = {
            "county": block.get("county"),
            "structure": block.get("structure"),
            "sourceUrl": block.get("sourceUrl"),
            "members": clean_members,
        }
        office = block.get("office") or {}
        office = {k: v for k, v in office.items() if v}
        if office:
            out["office"] = office
        roster[key] = out

    if len(roster) < MIN_COUNTIES:
        fail("only %d counties resolved (expected >= %d)" % (len(roster), MIN_COUNTIES))

    out_path = os.path.join(out_dir, "il-county-commissioners.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    total = sum(len(v["members"]) for v in roster.values())
    contacts = sum(1 for v in roster.values() for m in v["members"] if m.get("email") or m.get("phone"))
    print("county-commissioners-roster: %d counties, %d members (%d with contact) -> %s"
          % (len(roster), total, contacts, out_path))


if __name__ == "__main__":
    main()

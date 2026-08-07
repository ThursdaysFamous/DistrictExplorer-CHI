#!/usr/bin/env python3
"""
Resolve scripts/menard_commissioners_scraper.py's raw output into
data/app/menard-commissioner-members.json, keyed by Menard County commissioner
district ("1".."5" — five SINGLE-member districts, 5 commissioners).

Menard runs a COMMISSION form of government, so unlike the at-large commission
counties already on the County card (Monroe, Randolph, Edwards), its five
commissioners are elected BY DISTRICT and have geometry to attach to. That is
why this is a county-board layer rather than a County-card roster.

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it by district number to
data/app/menard-commissioner-districts.json, the Beacon export
build_menard_commissioner_districts.py reads.

THE SUFFIX GUARD IS ASSERTED, NOT ASSUMED. District 5's commissioner is
published as "Ed Whitcomb, Jr." — a comma-carrying name that the shared
uninvert_name() must REFUSE to reorder, because "Jr. Ed Whitcomb" would be a
worse defect than the one that guard exists to fix. Menard is the first source
in the fleet to exercise the refusal path in production, so this builder checks
it explicitly rather than trusting it.

Usage:
    python3 build_menard_commissioners_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_municipal_officials_roster import uninvert_name  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.menardcountyil.gov/elected-officials/board-commissioners/"

# Five single-member districts. The floor is the full board: on a single-member
# district a lost commissioner leaves a card with no name at all, and no count
# anywhere would look wrong.
MIN_DISTRICTS = 5
MIN_MEMBERS = 5
MIN_EMAILS = 5
MIN_PHONES = 5
SEATS_PER_DISTRICT = 1

ROLE_ALIASES = {
    "chair": "Board Chair", "chairman": "Board Chair",
    "vice-chair": "Vice Chair", "vice chair": "Vice Chair",
    "vice-chairman": "Vice Chair",
}
# Names the shared guard must leave alone. Asserted below — see the docstring.
SUFFIX_NAMES = ("Ed Whitcomb, Jr.",)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("records") if isinstance(payload, dict) else payload

    roster, notes = {}, []
    for rec in records or []:
        district = str(rec.get("district") or "").strip()
        name = (rec.get("name") or "").strip()
        if not district or not name:
            continue
        # Menard prints names naturally, so this should never fire. It is here
        # because the county could change format, and a surname-first name is
        # now a known fleet-wide hazard rather than a surprise.
        flipped = uninvert_name(name)
        if flipped:
            notes.append("%s -> %s (surname-first)" % (name, flipped))
            name = flipped
        member = {"name": name}
        role = (rec.get("role") or "").strip()
        if role:
            member["role"] = ROLE_ALIASES.get(role.lower(), role)
        for key in ("phone", "email"):
            if rec.get(key):
                member[key] = rec[key]
        if rec.get("seated"):
            member["seated"] = rec["seated"]
        roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        roster[district]["members"].append(member)

    names = [m["name"] for v in roster.values() for m in v["members"]]
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    phones = sum(1 for v in roster.values() for m in v["members"] if m.get("phone"))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chair"]
    vices = [m for v in roster.values() for m in v["members"] if m.get("role") == "Vice Chair"]

    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if len(names) < MIN_MEMBERS:
        problems.append("%d commissioners (< %d)" % (len(names), MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if phones < MIN_PHONES:
        problems.append("%d phones (< %d)" % (phones, MIN_PHONES))
    if len(set(names)) != len(names):
        problems.append("duplicate names (%s)"
                        % ", ".join(sorted({n for n in names if names.count(n) > 1})))
    lopsided = {d: len(v["members"]) for d, v in roster.items()
                if len(v["members"]) != SEATS_PER_DISTRICT}
    if lopsided:
        problems.append("districts not seating %d: %s" % (SEATS_PER_DISTRICT, lopsided))
    # The refusal path, asserted. A suffix name that came through reordered
    # means the shared guard regressed, and that is a fleet-wide bug.
    for expected in SUFFIX_NAMES:
        if expected in names:
            continue
        surname = expected.split(",")[0].strip()
        mangled = [n for n in names if surname in n and n != expected]
        if mangled:
            problems.append("suffix name %r came through as %s — uninvert_name's "
                            "suffix guard regressed" % (expected, mangled))
    if len(chairs) > 1:
        problems.append("%d chairs" % len(chairs))
    if len(vices) > 1:
        problems.append("%d vice chairs" % len(vices))
    if problems:
        print("build-menard-commissioners: FAIL — refusing to overwrite a good "
              "file with a partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "menard-commissioner-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    for note in notes:
        print("  name: %s" % note)
    print("build-menard-commissioners: wrote %s — %d districts, %d commissioners, "
          "%d phones, %d e-mails, chair %s, vice chair %s"
          % (out_path, len(roster), len(names), phones, emails,
             chairs[0]["name"] if chairs else "unresolved",
             vices[0]["name"] if vices else "unresolved"))


if __name__ == "__main__":
    main()

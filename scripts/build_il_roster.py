#!/usr/bin/env python3
"""
Resolve scripts/ilga_scraper.py's raw output into the current officeholder
per district and write the IL Senate / IL House rosters as JSON app-data files.

These rosters used to be spliced into object literals inside index.html. They
now live in data/app/il-senate-members.json and data/app/il-house-members.json,
which index.html fetches lazily on first click (same-origin, no CORS needed).
Writing plain JSON instead of rewriting a 400 KB HTML file removes the regex
splice entirely — the class of bug that could silently drop live code (see
docs/BUILD_PLAYBOOK_1.md) no longer exists here.

Usage:
    python3 build_il_roster.py ilga_network.json [output_dir]

output_dir defaults to the repo's data/app/ directory.
"""

import json
import os
import re
import sys

PARTY_NAMES = {"D": "Democratic", "R": "Republican", "I": "Independent"}

DISTRICT_RE = re.compile(r"^\s*(\d+)")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def district_number(record):
    for field in ("district", "term"):
        value = record.get(field)
        if value:
            m = DISTRICT_RE.match(value)
            if m:
                return m.group(1)
    return None


def is_current(record):
    term = record.get("term") or ""
    return "present" in term.lower()


# A line with no letter and no digit carries no information: ilga.gov prints an
# office block for a newly-seated member before anyone fills it in, and its
# empty state is not a blank field but a FORM — "(217)    -", "(   )    -",
# ", IL". Carried through, those render on the card as a phone number that is
# punctuation and a district office in a state with no city. Dropping them is
# not editing the source; it is declining to present a blank form as an answer,
# which is the same rule that keeps this app from guessing an officeholder.
# Found on 2026-08-11 in District 97's first roster refresh after Harry Benton
# left the seat (his page now reads "January 2023 - July 3, 2026") and Jessica
# Dixon Heitman took it with no offices yet listed.
# "Has a letter or a digit" is NOT enough to tell a filled line from a blank
# form, and assuming it was is how the first version of this let both offenders
# through: "(217)    -" has an area code and ", IL" has a state. A line is kept
# only if what it carries is about THIS member.
PHONE_SHAPED_RE = re.compile(r"^[\s()\-.\d]+$")
STATE_RE = re.compile(r"\b(?:IL|Illinois)\b", re.I)
ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")
SPRINGFIELD_ZIP_ONLY_RE = re.compile(r"\s*Springfield,\s*IL\s*62706\s*\Z")


def informative(line):
    """True when the line says something a card could show."""
    text = (line or "").strip()
    if not text:
        return False
    if PHONE_SHAPED_RE.match(text):
        # A phone with fewer than ten digits is an area code and punctuation:
        # "(217)    -" is the Springfield prefix printed with nothing after it.
        return len(re.sub(r"\D", "", text)) >= 10
    # An address line is real if anything survives removing the state and the
    # zip — "Springfield" does, the "" in ", IL" does not.
    return bool(re.sub(r"[^A-Za-z0-9]+", "", ZIP_RE.sub(" ", STATE_RE.sub(" ", text))))


def meaningful_office(lines):
    """The office block minus its empty-form lines, or None if nothing is left.

    A block that loses every line becomes None so the card omits the office
    entirely rather than printing a heading over nothing.
    """
    if not lines:
        return None
    kept = [line for line in lines if informative(line)]
    # What survives an unfilled Springfield block is its own zip line, which is
    # the building's and not the member's — no room, no phone, no information.
    # It goes with the rest of the form.
    if len(kept) == 1 and SPRINGFIELD_ZIP_ONLY_RE.match(kept[0] or ""):
        return None
    return kept or None


def resolve_roster(records, chamber):
    by_district = {}
    for record in records:
        if record.get("chamber") != chamber or record.get("error"):
            continue
        district = district_number(record)
        if not district:
            continue
        by_district.setdefault(district, []).append(record)

    roster = {}
    for district, candidates in by_district.items():
        current = [c for c in candidates if is_current(c)]
        if current:
            chosen = current[0]
        else:
            # No record explicitly says "Present" (e.g. a same-day handoff) —
            # fall back to the highest member_id, since ILGA assigns these
            # sequentially and a newer id means a more recently seated member.
            chosen = max(candidates, key=lambda c: int(c["member_id"]))
        party_code = chosen.get("party")
        roster[district] = {
            "name": chosen.get("name"),
            "party": PARTY_NAMES.get(party_code, party_code),
            "springfieldOffice": meaningful_office(chosen.get("springfield_office")),
            "districtOffice": meaningful_office(chosen.get("district_office")),
            "url": chosen.get("source_url"),
        }
    return roster


def ordered(roster):
    # Emit districts in numeric order so the file diffs cleanly week to week.
    return {d: roster[d] for d in sorted(roster, key=int)}


def write_json(path, roster):
    with open(path, "w") as f:
        json.dump(ordered(roster), f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    if len(sys.argv) not in (2, 3):
        print(f"usage: {sys.argv[0]} <raw-scraper-output.json> [output_dir]", file=sys.stderr)
        sys.exit(1)

    raw_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_OUT_DIR

    with open(raw_path) as f:
        records = json.load(f)

    senate_roster = resolve_roster(records, "senate")
    house_roster = resolve_roster(records, "house")

    if len(senate_roster) < 59 or len(house_roster) < 118:
        print(
            f"WARNING: resolved {len(senate_roster)}/59 senate and "
            f"{len(house_roster)}/118 house districts — refusing to overwrite "
            "the roster files with an incomplete roster",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    write_json(os.path.join(out_dir, "il-senate-members.json"), senate_roster)
    write_json(os.path.join(out_dir, "il-house-members.json"), house_roster)

    print(
        f"Wrote {out_dir}/il-senate-members.json ({len(senate_roster)} districts), "
        f"il-house-members.json ({len(house_roster)} districts)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

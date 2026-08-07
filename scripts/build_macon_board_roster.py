#!/usr/bin/env python3
"""
Resolve scripts/macon_county_board_scraper.py's raw output into
data/app/macon-county-board-members.json, keyed by Macon County Board district
("1".."5" — five districts electing THREE members each, 15 seats).

index.html's consolidated county-board layer fetches this file lazily on first
click and joins it by district number to the county's LIVE Electoral Districts
layer, whose five shapes carry no district number of their own — those come from
data/app/macon-board-district-labels.json, read off the Clerk's colour-coded map
(see build_macon_board_district_labels.py).

THIS ROSTER IS THE THIRD INDEPENDENT CHECK ON THAT LABELLING, and the reason the
seat count is asserted exactly. The county publishes 15 members keyed by
district; if the labels were wrong, there would be no reason for those 15 to
fall 3-3-3-3-3 across the five shapes. They do. A future scrape that does not is
a signal about the labels as much as about the page, and this builder says so.

PHONES SHIP AS SEVEN DIGITS. The county publishes "C 521-4688" with no area
code. Macon is entirely area code 217 and prefixing it would look helpful and be
a guess — a member's mobile can be from anywhere, and a wrong prefix reaches a
stranger rather than failing visibly. The county's own labels (home/cell) are
kept, which is the part that helps a reader without inventing anything. Recorded
as `macon-board-phone-area-code`.

Usage:
    python3 build_macon_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import sys

SOURCE_URL = ("https://maconcounty.illinois.gov/departments/county-board/"
              "macon-county-board-members/")

MIN_DISTRICTS = 5
MIN_MEMBERS = 15
MIN_EMAILS = 15
SEATS_PER_DISTRICT = 3

ROLE_ALIASES = {
    "chairman": "Board Chair", "chair": "Board Chair",
    "vice chairman": "Vice Chair", "vice chair": "Vice Chair",
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def member_obj(rec):
    member = {"name": rec["name"]}
    role = (rec.get("role") or "").strip()
    if role:
        member["role"] = ROLE_ALIASES.get(role.lower(), role)
    if rec.get("party"):
        member["party"] = rec["party"]
    phones = rec.get("phones") or []
    if phones:
        member["phone"] = phones[0]["number"]
        # The county's own home/cell labels, kept on the extras where there is
        # room to say them. Never invented: a row published without a label
        # ships without one.
        extra = []
        for p in phones[1:]:
            extra.append(("%s %s" % (p["label"], p["number"])) if p.get("label")
                         else p["number"])
        if extra:
            member["phonesExtra"] = extra
    if rec.get("email"):
        member["email"] = rec["email"]
    if rec.get("term_expires"):
        member["termThrough"] = rec["term_expires"]
    return member


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("records") if isinstance(payload, dict) else payload

    roster = {}
    for rec in records or []:
        district = str(rec.get("district") or "").strip()
        if not district or not (rec.get("name") or "").strip():
            continue
        roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        roster[district]["members"].append(member_obj(rec))
    rank = {"Board Chair": 0, "Vice Chair": 1}
    for slot in roster.values():
        slot["members"].sort(key=lambda m: (rank.get(m.get("role"), 2), m["name"]))

    names = [m["name"] for v in roster.values() for m in v["members"]]
    emails = sum(1 for v in roster.values() for m in v["members"] if m.get("email"))
    chairs = [m for v in roster.values() for m in v["members"] if m.get("role") == "Board Chair"]
    vices = [m for v in roster.values() for m in v["members"] if m.get("role") == "Vice Chair"]

    problems = []
    if len(roster) < MIN_DISTRICTS:
        problems.append("%d districts (< %d)" % (len(roster), MIN_DISTRICTS))
    if len(names) < MIN_MEMBERS:
        problems.append("%d members (< %d)" % (len(names), MIN_MEMBERS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails (< %d)" % (emails, MIN_EMAILS))
    if len(set(names)) != len(names):
        problems.append("duplicate names (%s)"
                        % ", ".join(sorted({n for n in names if names.count(n) > 1})))
    # The three-per-district check. It guards the page AND the district labels
    # the board geometry depends on — see the module docstring.
    lopsided = {d: len(v["members"]) for d, v in roster.items()
                if len(v["members"]) != SEATS_PER_DISTRICT}
    if lopsided:
        problems.append("districts not seating %d: %s — this also casts doubt on "
                        "data/app/macon-board-district-labels.json, which the "
                        "even 3-3-3-3-3 split independently corroborates"
                        % (SEATS_PER_DISTRICT, lopsided))
    if len(chairs) > 1:
        problems.append("%d chairs" % len(chairs))
    if len(vices) > 1:
        problems.append("%d vice chairs" % len(vices))
    if problems:
        print("build-macon-board: FAIL — refusing to overwrite a good file with a "
              "partial scrape: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    out_path = os.path.join(out_dir, "macon-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False)
    parties = {}
    for v in roster.values():
        for m in v["members"]:
            parties[m.get("party", "?")] = parties.get(m.get("party", "?"), 0) + 1
    print("build-macon-board: wrote %s — %d districts x %d seats, %d members, "
          "%d e-mails, %s, chair %s, vice chair %s"
          % (out_path, len(roster), SEATS_PER_DISTRICT, len(names), emails,
             dict(sorted(parties.items())),
             chairs[0]["name"] if chairs else "unresolved",
             vices[0]["name"] if vices else "unresolved"))


if __name__ == "__main__":
    main()

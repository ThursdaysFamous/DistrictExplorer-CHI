#!/usr/bin/env python3
"""
Resolve the per-county municipal-officials scraper outputs into one record per
municipality and write the JSON app-data file the Municipality card reads:
data/app/municipal-officials.json.

Keys are the 7-digit CENSUS PLACE GEOID ("17" + PLACEFP, e.g. 1701010 for
Alsip) because that is exactly the `GEOID` the app's TIGERweb places layer
already carries on every municipality feature — so the card's join needs no
name normalization at query time, and the 47 metro municipalities that span
county lines resolve to ONE entry instead of one per county
(docs/MUNICIPAL_COUNCILS_PLAYBOOK.md).

The name -> GEOID mapping comes from the Census 2020 place-by-county reference
file committed at data/source/st17_il_place_by_county2020.txt. Lookup prefers
a place in the source's own county and falls back to a statewide unique match,
which is what resolves municipalities the county clerk claims but Census lists
only under a neighbour (Oak Brook is a Cook Clerk jurisdiction but is listed
under DuPage). Only two Illinois incorporated-place names collide statewide
(Wilmington, Windsor) and neither is in the metro; an ambiguous or unmatched
name is a hard failure, never a guess.

Contact data in these sources is MUNICIPALITY-level, not per-person — in the
Cook DOEO API every official of a municipality carries the same village-hall
phone/email/address and the per-person columns are empty for all 1,134
records. It is therefore emitted once under `office`, never on a person, so
the card cannot imply a direct line to a trustee that does not exist.

Usage:
    python3 build_municipal_officials_roster.py cook_municipal_officials.json [more...] [--out-dir DIR]

Each positional argument is one county scraper's output. Counties may be
built incrementally: this rewrites the whole file from the inputs given, so
pass every county's output that should ship.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")
PLACES_FILE = os.path.join(REPO_ROOT, "data", "source", "st17_il_place_by_county2020.txt")

# Census county FIPS for the seven metro counties, for county-preferred lookup.
COUNTY_FIPS = {
    "Cook": "031",
    "DuPage": "043",
    "Kane": "089",
    "Kendall": "093",
    "Lake": "097",
    "McHenry": "111",
    "Will": "197",
}

# Office classification. HEAD is the single head of government; BOARD is the
# governing body's seats; OFFICERS are the other municipality-wide elected
# officers. An office name not listed here still ships (under officers) and
# prints a warning — new office types get a human's attention, never a silent
# drop.
HEAD_OFFICES = {"mayor", "president", "village president"}
BOARD_OFFICES = {"trustee", "alderperson", "alderman", "council member",
                 "commissioner", "councilman", "councilwoman"}
OFFICER_OFFICES = {"clerk", "treasurer", "village clerk", "city clerk",
                   "taxpayer advocate", "collector", "supervisor"}

# Per-county floors: deliberate under-tolerances against the verified 2026-07
# live values (Cook 128 municipalities / 1,035 governing records / 128 heads;
# Will 34 / 303 / 34). A real coverage loss fails the build and leaves the last
# good file in place; ordinary turnover does not.
COUNTY_FLOORS = {
    "Cook": {"municipalities": 120, "members": 900, "heads": 120},
    "Will": {"municipalities": 30, "members": 260, "heads": 30},
    # The five mayor-level counties (2026-07 live values in parentheses). Their
    # sources publish no trustees, so `members` counts the head plus the elected
    # clerk/treasurer rows only — a floor equal to the head count would pass on
    # a run that silently lost every officer.
    "DuPage": {"municipalities": 32, "members": 32, "heads": 32},        # 36 / 36 / 36
    "Kane": {"municipalities": 26, "members": 50, "heads": 26},          # 29 / 58 / 29
    "McHenry": {"municipalities": 26, "members": 48, "heads": 24},       # 30 / 55 / 30
    "Kendall": {"municipalities": 12, "members": 28, "heads": 12},       # 14 / 34 / 14
    # Lake publishes NO officeholder names (rule-4 honesty floor), so its
    # member/head floors are 0 BY DESIGN — the municipality count is the real
    # guard. See lake_municipal_officials_scraper.py.
    "Lake": {"municipalities": 48, "members": 0, "heads": 0},            # 55 / 0 / 0
}
# Merged floor across all counties supplied. Cook + Will resolve to 156 unique
# municipalities (6 of Will's 34 are shared with Cook); all seven counties
# resolve to ~270 of the metro's 284, the rest being places no county source
# lists.
MIN_TOTAL_MUNICIPALITIES = 250

# Tie-break for a municipality claimed by two counties, applied only AFTER
# depth (see pick_entry). Both directories describe the same government, so
# this is a freshness call, not a correctness one: Cook's is a live API
# reflecting each election as it is certified, Will's is an annually
# republished directory.
COUNTY_PRECEDENCE = ["Cook", "Will", "DuPage", "Kane", "Kendall", "McHenry", "Lake"]


def norm_place(name):
    """Normalize a municipality name to letters only for joining.

    The two sides label the government form on opposite ends — the clerk
    writes "City of Calumet City", Census writes "Calumet City city" — so the
    strip is either/or, never both. Stripping both would reduce the clerk's
    "City of Calumet City" to "Calumet" and miss the join.
    """
    text = (name or "").strip()
    # "United City of Yorkville" is Yorkville's legal name and the form its
    # county clerk prints; Census lists it as "Yorkville city". The optional
    # qualifier keeps that join working without a per-place alias.
    prefixed = re.sub(r"^(?:united\s+)?(village|city|town)\s+of\s+", "", text, flags=re.I)
    if prefixed != text:
        text = prefixed
    else:
        text = re.sub(r"\s+(village|city|town|CDP)$", "", text, flags=re.I)
    return re.sub(r"[^A-Z]", "", text.upper())


def load_places(path):
    """-> {county_fips: {normname: geoid}}, {normname: set(geoid)} statewide."""
    if not os.path.exists(path):
        print("FATAL: Census place reference missing at %s" % path, file=sys.stderr)
        sys.exit(1)
    by_county = defaultdict(dict)
    statewide = defaultdict(set)
    with open(path, encoding="utf-8-sig") as f:
        rows = [line.rstrip("\n").split("|") for line in f if line.strip()]
    header = rows[0]
    for row in rows[1:]:
        if len(row) != len(header):
            continue
        rec = dict(zip(header, row))
        if rec.get("TYPE") != "INCORPORATED PLACE":
            continue
        key = norm_place(rec["PLACENAME"])
        geoid = "17" + rec["PLACEFP"]
        by_county[rec["COUNTYFP"]][key] = geoid
        statewide[key].add(geoid)
    if not statewide:
        print("FATAL: no incorporated places parsed from %s" % path, file=sys.stderr)
        sys.exit(1)
    return by_county, statewide


def resolve_geoid(name, county, by_county, statewide):
    key = norm_place(name)
    if not key:
        return None, "unparseable name"
    fips = COUNTY_FIPS.get(county)
    if fips and key in by_county.get(fips, {}):
        return by_county[fips][key], None
    matches = statewide.get(key) or set()
    if len(matches) == 1:
        return next(iter(matches)), None
    if not matches:
        return None, "no Census place matches"
    return None, "ambiguous statewide (%s)" % ", ".join(sorted(matches))


def classify(office):
    o = (office or "").strip().lower()
    if o in HEAD_OFFICES:
        return "head"
    if o in BOARD_OFFICES:
        return "board"
    if o in OFFICER_OFFICES:
        return "officer"
    return None


def election_year(value):
    """"2029-04-01T00:00:00-05:00" -> "2029"; anything unparseable -> None."""
    match = re.match(r"^(\d{4})-\d{2}-\d{2}", str(value or ""))
    return match.group(1) if match else None


def district_sort_key(member):
    """Ward 1 < Ward 2 < Ward 10; unnumbered seats sort last, then by name."""
    district = member.get("district") or ""
    nums = re.findall(r"\d+", district)
    return (0, int(nums[0])) if nums else (1, 0), member.get("name") or ""


def office_block(records):
    """One municipality-level office block from the shared contact fields."""
    rec = records[0]
    street = rec.get("office_address")
    city = rec.get("office_city")
    state = rec.get("office_state")
    zipcode = rec.get("office_zip")
    locality = " ".join(p for p in (city, state) if p)
    if locality and zipcode:
        locality = "%s %s" % (locality, zipcode)
    address = ", ".join(p for p in (street, locality) if p) or None
    block = {}
    if address:
        block["address"] = address
    phone = format_phone(rec.get("office_phone"))
    if phone:
        block["phone"] = phone
    if rec.get("office_email"):
        block["email"] = rec["office_email"]
    return block


def format_phone(phone):
    """10 digits -> 708-385-6902, the shape the card's phone helper renders.

    cardPhoneLink() prints the stored string verbatim (only swapping hyphens
    for non-breaking ones), so an unformatted run of digits would ship as
    '7083856902'. Anything that isn't a plain US number is left untouched
    rather than reshaped into a guess.
    """
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return phone
    return "%s-%s-%s" % (digits[:3], digits[3:6], digits[6:])


def normalize_website(url):
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def build_county(payload, by_county, statewide, warnings):
    county = payload.get("county") or "?"
    grouped = defaultdict(list)
    for rec in payload.get("officials") or []:
        if rec.get("jurisdiction"):
            grouped[rec["jurisdiction"]].append(rec)

    entries = {}
    for jurisdiction, records in grouped.items():
        geoid, problem = resolve_geoid(jurisdiction, county, by_county, statewide)
        if geoid is None:
            print("FATAL: cannot resolve '%s' (%s County) to a Census place GEOID — %s"
                  % (jurisdiction, county, problem), file=sys.stderr)
            sys.exit(1)

        head = None
        board = []
        officers = []
        for rec in records:
            name = rec.get("name")
            if not name:
                continue
            kind = classify(rec.get("office"))
            person = {"name": name, "role": rec.get("office")}
            if rec.get("district"):
                person["district"] = rec["district"]
            if rec.get("appointed"):
                person["appointed"] = True
            # Per-PERSON contact, carried only where the source publishes it per
            # member (McHenry prints a direct line or office e-mail for a few
            # officials). The municipality-level hall contact below is never
            # copied onto a person — that would imply a direct line that the
            # source does not publish.
            if rec.get("person_phone"):
                person["phone"] = format_phone(rec["person_phone"])
            if rec.get("person_email"):
                person["email"] = rec["person_email"]
            # When this seat is next on the ballot, where the source publishes
            # it (Cook: 100% of records). Terms are STAGGERED — 103 of Cook's
            # 104 village boards mix two cycles — so this belongs on the person,
            # not the card. Stored as the year; the card hides a year already
            # past rather than calling it "next".
            year = election_year(rec.get("next_election"))
            if year:
                person["nextElection"] = year
            if kind == "head":
                if head is not None:
                    print("FATAL: %s resolved two heads of government (%s, %s)"
                          % (jurisdiction, head["name"], name), file=sys.stderr)
                    sys.exit(1)
                head = person
            elif kind == "board":
                board.append(person)
            else:
                if kind is None:
                    warnings.append("unclassified office '%s' in %s — shipped under officers"
                                    % (rec.get("office"), jurisdiction))
                officers.append(person)

        board.sort(key=district_sort_key)
        officers.sort(key=lambda m: (m.get("role") or "", m.get("name") or ""))

        entry = {"name": jurisdiction, "county": county}
        # Chicago's 50 ward seats are published under a different jurisdiction
        # type and answered by the `ward` layer, so this card points there
        # instead of implying the city has no council.
        if any(rec.get("ward_seats_elsewhere") for rec in records):
            entry["councilOnWardLayer"] = True
        if head:
            entry["head"] = head
        if board:
            entry["board"] = board
        if officers:
            entry["officers"] = officers
        office = office_block(records)
        if office:
            entry["office"] = office
        website = normalize_website(records[0].get("website"))
        if website:
            entry["url"] = website
        entry["sourceUrl"] = payload.get("directory_url") or records[0].get("source_url")
        entries[geoid] = entry

    floors = COUNTY_FLOORS.get(county)
    if floors:
        n_munis = len(entries)
        n_members = sum(len(e.get("board") or []) + len(e.get("officers") or [])
                        + (1 if e.get("head") else 0) for e in entries.values())
        n_heads = sum(1 for e in entries.values() if e.get("head"))
        for label, actual, floor in (("municipalities", n_munis, floors["municipalities"]),
                                     ("members", n_members, floors["members"]),
                                     ("heads of government", n_heads, floors["heads"])):
            if actual < floor:
                print("FATAL: %s County resolved %d %s, floor is %d — refusing to write"
                      % (county, actual, label, floor), file=sys.stderr)
                sys.exit(1)
    return entries


def entry_depth(entry):
    """How much of the governing body a source actually names.

    2 = full body (a head plus the board), 1 = head only, 0 = contact only.
    This is what decides a cross-county municipality, NOT which county the
    place is mostly in: a village that straddles Cook and Will should show the
    board wherever one is published.
    """
    if entry.get("board"):
        return 2
    if entry.get("head"):
        return 1
    return 0


def describe_depth(entry):
    return {2: "full governing body", 1: "head of government only",
            0: "contact only"}[entry_depth(entry)]


def pick_entry(a, b):
    """-> (kept, dropped) for one municipality claimed by two counties."""
    if entry_depth(a) != entry_depth(b):
        return (a, b) if entry_depth(a) > entry_depth(b) else (b, a)
    rank = {c: i for i, c in enumerate(COUNTY_PRECEDENCE)}
    fallback = len(COUNTY_PRECEDENCE)
    if rank.get(a["county"], fallback) <= rank.get(b["county"], fallback):
        return a, b
    return b, a


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("inputs", nargs="+", help="per-county scraper output JSON files")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--places", default=PLACES_FILE)
    args = parser.parse_args()

    by_county, statewide = load_places(args.places)

    roster = {}
    warnings = []
    for path in args.inputs:
        with open(path) as f:
            payload = json.load(f)
        entries = build_county(payload, by_county, statewide, warnings)
        for geoid, entry in entries.items():
            if geoid in roster:
                keep, drop = pick_entry(roster[geoid], entry)
                print("NOTE: %s (%s) is listed by both %s and %s County — keeping the "
                      "%s entry (%s)" % (geoid, keep["name"], roster[geoid]["county"],
                                         entry["county"], keep["county"],
                                         describe_depth(keep)), file=sys.stderr)
                if drop.get("board") and not keep.get("board"):
                    print("FATAL: dropped entry for %s had a board and the kept one "
                          "does not — precedence is wrong" % geoid, file=sys.stderr)
                    sys.exit(1)
                roster[geoid] = keep
                continue
            roster[geoid] = entry

    if len(roster) < MIN_TOTAL_MUNICIPALITIES:
        print("FATAL: resolved %d municipalities, floor is %d — refusing to write"
              % (len(roster), MIN_TOTAL_MUNICIPALITIES), file=sys.stderr)
        sys.exit(1)

    for warning in warnings:
        print("WARNING: %s" % warning, file=sys.stderr)

    out_path = os.path.join(args.out_dir, "municipal-officials.json")
    with open(out_path, "w") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    n_board = sum(len(e.get("board") or []) for e in roster.values())
    n_seats = sum(1 for e in roster.values() for m in (e.get("board") or []) if m.get("district"))
    print("wrote %s: %d municipalities, %d board members (%d ward/district seats)"
          % (out_path, len(roster), n_board, n_seats), file=sys.stderr)


if __name__ == "__main__":
    main()

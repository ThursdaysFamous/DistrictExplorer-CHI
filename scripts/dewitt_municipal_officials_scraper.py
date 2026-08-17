#!/usr/bin/env python3
"""
Parse the De Witt County city/village officials list into the payload
build_municipal_officials_roster.py consumes.

SOURCE. "VILLIAGE/CITY OFFICIALS" (the heading's spelling), the one-page Word
document the De Witt County Clerk & Recorder keeps of every municipality's
governing body — last updated 7/28/2025, after the consolidated election.
It is not on the county's website. County Clerk Kari Harris sent the file by
e-mail on 2026-08-17, alongside a township-officials PDF that is archived for
provenance only (township officials are not a concept this builder carries).
The copy read here is archived at data/source/raw/, so refreshing it means
asking again; that is why this reads the archive rather than a URL — the
Marshall/Washington archived-document pattern.

DEPTH. All seven municipalities with full governing bodies. Two are CITIES
under the commission form — Clinton and Farmer City elect a mayor and
commissioners — and five are VILLAGES electing a president and trustees.

HOME ADDRESSES ARE NEVER COLLECTED. Every official's line prints their
residence after the first comma ("MAYOR  HELEN MICHELASSI, 511 S ISABELLA ST,
CLINTON, IL 61727"). The Washington rule applies: a name is taken only from
the segment BEFORE the first comma and only when it matches a NAME SHAPE no
address can satisfy (letters, apostrophes and hyphens, at least two parts, no
digits and no ", IL") — an allowlist, asserted again before writing. The ONLY
contact that ships is the municipality's own published contact number from its
heading line ("CLINTON – CONTACT NUMBER_ CITY HALL 217-935-9438"); the
document publishes no per-person phones and no office addresses, so those
fields stay empty rather than being invented.

NOT-ELECTED OFFICERS ARE MARKED. The Clerk is careful about this distinction:
appointed officers carry "(NOT ELECTED)" or "(APPT)", DeWitt's clerk is
"(ACTING)", and three Weldon trustees are "(APPT IN JUNE 2025)". All ship with
appointed=True — the builder's one not-elected field, the LaSalle precedent —
so a card never implies an appointee was elected. Clinton's mayor's
"(ELECTED IN APRIL 2025-2YR UNEXP TERM)" is the opposite fact and ships
unmarked; the parenthetical itself is stripped from every name.

HIRED STAFF ARE SKIPPED. Farmer City lists a PART-TIME CLERK and Weldon a
WATER CLERK; the fleet's rule is to carry elected and statutory officers and
leave staff out (the Washington precedent). A seat printed "VACANT" is counted
in the payload's `vacancies`, never invented as a person.

ALL-CAPS NAMES are recased the Grundy way: one capital per alphabetic run,
with only the Mc- family re-capitalized ("CONNIE MCNUTT" -> "Connie McNutt")
— enumerated, not guessed.

Usage:
    python3 scripts/dewitt_municipal_officials_scraper.py --out dewitt_muni.json
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DOC = os.path.join(REPO_ROOT, "data", "source", "raw",
                          "DeWitt County City and Village Officials 2025.docx")
COUNTY_SITE = "https://www.dewittcountyil.gov/"
SOURCE_NOTE = ("De Witt County Clerk & Recorder, \"Village/City Officials\" "
               "list (last updated 7/28/2025, after the consolidated "
               "election), supplied by e-mail 2026-08-17")

MIN_PLACES = 7
MIN_OFFICIALS = 40
MIN_HEADS = 7

# The seven municipalities the Clerk's document covers, exactly. A heading
# outside this table is a hard failure, never a guess — it would mean the
# document's layout changed or a municipality appeared, and both need a human.
JURISDICTIONS = {
    "CLINTON": "City of Clinton",
    "DEWITT": "Village of DeWitt",
    "FARMER CITY": "City of Farmer City",
    "KENNEY": "Village of Kenney",
    "WAPELLA": "Village of Wapella",
    "WAYNESVILLE": "Village of Waynesville",
    "WELDON": "Village of Weldon",
}

# "CLINTON –   CONTACT NUMBER_  CITY HALL  217-935-9438" — a municipality
# heading is the ALL-CAPS place name, a dash, then the contact-number tail.
HEADING_RE = re.compile(r"^([A-Z][A-Z ]*?)\s*[-–]\s*CONTACT NUMBER", re.I)
PHONE_RE = re.compile(r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})")

# The offices the document prints, verbatim -> (shipped office, is_head).
# CLERK/TREASURER (Weldon) and CLERK/COLLECTOR (Waynesville) are one officer
# elected to a combined office and ship as such — the builder's office classes
# carry both.
ROLES = {
    "MAYOR": ("Mayor", True),
    "VILLAGE PRESIDENT": ("President", True),
    "VIL PRES": ("President", True),
    "COMM": ("Commissioner", False),
    "TRUSTEE": ("Trustee", False),
    "CLERK": ("Clerk", False),
    "TREASURER": ("Treasurer", False),
    "TREAS": ("Treasurer", False),
    "CLERK/TREASURER": ("Clerk/Treasurer", False),
    "CLERK/COLLECTOR": ("Clerk/Collector", False),
}
# Hired staff, not the governing body (the Washington rule).
SKIP_ROLES = {"WATER CLERK", "PART-TIME CLERK"}

# "(NOT ELECTED)" / "(APPT)" / "(APPT IN JUNE 2025)" / "(ACTING)" — the three
# ways this document marks an officer who was not elected to the office.
# "(ELECTED IN APRIL 2025-…)" matches none of them, deliberately.
APPOINTED_RE = re.compile(r"\(\s*(?:NOT\s+ELECTED|APPT\b[^)]*|ACTING)\s*\)", re.I)

# The name allowlist (post-recase): at least two parts, letters/apostrophes/
# hyphens/periods only. A residence carries digits and/or ", IL" and can never
# match — same shape as the Washington scraper's.
NAME_RE = re.compile(r"^[A-Z][A-Za-z.'’-]*(?:\s+[A-Z][A-Za-z.'’-]*)+$")

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_lines(path):
    """The document's paragraphs, tabs preserved — stdlib only, no new dep."""
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    lines = []
    for para in root.iter(W_NS + "p"):
        parts = []
        for node in para.iter():
            if node.tag == W_NS + "t" and node.text:
                parts.append(node.text)
            elif node.tag == W_NS + "tab":
                parts.append("\t")
            elif node.tag == W_NS + "br":
                parts.append("\n")
        lines.extend("".join(parts).split("\n"))
    return lines


def recase(text):
    """'CONNIE MCNUTT' -> 'Connie McNutt'; only applied to ALL-CAPS strings."""
    if not text or not text.isupper():
        return text

    def one(match):
        word = match.group(0)
        if word.startswith("MC") and len(word) > 2:
            return "Mc" + word[2:].capitalize()
        return word.capitalize()

    return re.sub(r"[A-Z]+", one, text)


def scrape(lines, warnings):
    places = []
    officials = []
    office_phones = {}
    skipped_staff = []
    vacancies = 0
    current = None

    for raw in lines:
        line = raw.strip("\n").rstrip()
        if not line.strip():
            continue

        heading = HEADING_RE.match(line.strip())
        if heading:
            place_key = re.sub(r"\s+", " ", heading.group(1).strip().upper())
            if place_key not in JURISDICTIONS:
                raise SystemExit("unknown municipality heading %r — the "
                                 "document's layout changed, a human must look"
                                 % line.strip())
            current = JURISDICTIONS[place_key]
            places.append(current)
            phone = PHONE_RE.search(line)
            office_phones[current] = "%s-%s-%s" % phone.groups() if phone else None
            if not phone:
                warnings.append("%s: no contact number on its heading line" % current)
            continue
        if current is None:
            continue  # the document's title block, above the first heading

        cells = [c.strip() for c in line.split("\t") if c.strip()]
        if not cells:
            continue

        # The role label leads the line; a lone "(ACTING)"-style qualifier may
        # occupy its own tab stop before the person ("CLERK\t(ACTING)\tNICOLE…").
        role_parts = [cells[0]]
        rest = cells[1:]
        while rest and re.fullmatch(r"\([A-Z0-9 .'’-]+\)", rest[0], re.I):
            role_parts.append(rest.pop(0))
        person_text = " ".join(rest).strip()

        role_key = re.sub(r"\s+", " ",
                          re.sub(r"\([^)]*\)", " ", " ".join(role_parts))
                          .replace("_", " ")).strip().upper()
        if role_key in SKIP_ROLES:
            skipped_staff.append("%s: %s (%s)" % (current, role_key,
                                                  person_text.split(",")[0].strip() or "?"))
            continue
        if role_key not in ROLES:
            warnings.append("%s: unrecognised office label %r — skipped, not guessed"
                            % (current, " ".join(role_parts)))
            continue
        office, _is_head = ROLES[role_key]

        if not person_text or person_text.split(",")[0].strip().upper() == "VACANT":
            vacancies += 1
            warnings.append("%s: %s seat is VACANT — counted, never invented"
                            % (current, office))
            continue

        # NAME ALLOWLIST: only the segment before the first comma, only when it
        # is shaped like a name. Everything after the comma is a residence and
        # is never read.
        name = recase(person_text.split(",")[0].strip())
        if not NAME_RE.match(name or ""):
            warnings.append("%s: %s row's name cell %r does not match the name "
                            "shape — skipped, not guessed" % (current, office, name))
            continue

        officials.append({
            "jurisdiction": current,
            "office": office,
            "name": name,
            "district": None,
            "appointed": bool(APPOINTED_RE.search(line)),
            "person_phone": None,   # the document publishes none
        })

    for record in officials:
        if office_phones.get(record["jurisdiction"]):
            record["office_phone"] = office_phones[record["jurisdiction"]]
        record["source_url"] = COUNTY_SITE
        record["source_note"] = SOURCE_NOTE
    return places, officials, vacancies, skipped_staff


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="dewitt_muni.json")
    parser.add_argument("--doc", default=SOURCE_DOC)
    args = parser.parse_args()

    if not os.path.exists(args.doc):
        sys.exit("missing archived source: %s" % args.doc)

    warnings = []
    places, officials, vacancies, skipped_staff = scrape(docx_lines(args.doc),
                                                         warnings)

    heads = sum(1 for o in officials if o["office"] in ("President", "Mayor"))

    problems = []
    if len(set(places)) < MIN_PLACES:
        problems.append("%d municipalities < floor %d" % (len(set(places)), MIN_PLACES))
    if len(officials) < MIN_OFFICIALS:
        problems.append("%d officials < floor %d" % (len(officials), MIN_OFFICIALS))
    if heads < MIN_HEADS:
        problems.append("%d heads of government < floor %d" % (heads, MIN_HEADS))
    # The privacy invariant, asserted rather than assumed.
    for record in officials:
        if re.search(r"\d", record["name"]) or re.search(r"(?i),\s*IL", record["name"]):
            problems.append("an address fragment reached a name (%r in %s)"
                            % (record["name"], record["jurisdiction"]))
    if problems:
        for problem in problems:
            print("  FAIL: %s" % problem, file=sys.stderr)
        print("FATAL: refusing to write a payload that lost coverage or leaked",
              file=sys.stderr)
        sys.exit(1)

    payload = {
        "county": "De Witt",
        "officials_page": COUNTY_SITE,
        "source_note": SOURCE_NOTE,
        "scraped_at": datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "municipalities": sorted(set(places)),
        "officials": officials,
        "vacancies": vacancies,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    per = collections.Counter(o["jurisdiction"] for o in officials)
    print("scraped %d municipalities, %d officials (%d heads, %d marked "
          "appointed/acting), %d vacant seats counted, %d staff rows skipped -> %s"
          % (len(set(places)), len(officials), heads,
             sum(1 for o in officials if o["appointed"]), vacancies,
             len(skipped_staff), args.out), file=sys.stderr)
    for place in sorted(per):
        print("    %-26s %d" % (place, per[place]), file=sys.stderr)
    for item in skipped_staff:
        print("  staff (not the governing body): %s" % item, file=sys.stderr)
    for warning in warnings:
        print("  note: %s" % warning, file=sys.stderr)


if __name__ == "__main__":
    main()

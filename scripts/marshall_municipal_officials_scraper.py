#!/usr/bin/env python3
"""
Scrape Marshall County's "City & Village Elected Officers" table into the
payload build_municipal_officials_roster.py consumes.

SOURCE. A 5-page PDF the County Clerk's office produces for each 4-year term —
"CITY & VILLAGE ELECTED OFFICERS - 2025 / 4-YEAR TERM - EXPIRES 2029". It is
not published on the county's website; County Clerk Jill Lindsey sent it by
e-mail on 2026-08-03 when asked whether the county published a municipal list.
The copy read here is archived at data/source/raw/, and refreshing it means
asking again — which is why this parser reads the archive rather than a URL.

DEPTH. Full governing body for all nine municipalities: Henry, Hopewell, Lacon,
La Rose, Sparland, Toluca, Varna, Washburn and Wenona — head of government,
clerk, treasurer, and every alderperson (BY WARD) or trustee, with party where
the county records one, an appointment marker where the seat was filled by
appointment, the staggered term-expiry year, and a phone for some.

WHY NOT COLUMN POSITIONS. Every other positional parser in this repo (Cass,
LaSalle) drops the address by reading only certain x-ranges, which is a stronger
guarantee than filtering strings. That does NOT work here, because this
document's columns drift row to row:

    Mayor@72   Andrea@126  Mahoney-Platt@168  410@252 Highway@276 …
               Michelle@108 (Shelly)@162 Urnikis@216  713@288 …
    Clerk@72   Roanna@144  Lee@186 Richard@210  (Indep.)102@258 N.@330 …

A name starts at x=108 on one row and x=144 on the next, the address column
begins anywhere from 252 to 306, and the last line shows a token where the party
marker and the house number have been FUSED into "(Indep.)102" by the PDF's own
text layer. A fixed band would either truncate names or admit addresses.

SO THE RULE IS STRUCTURAL INSTEAD: **every address in this document begins with
a house number**, and a name never contains a digit. Name accumulation stops at
the first digit-leading token, and from the remainder only two token SHAPES are
ever collected — a phone pattern and a 4-digit term year. That is an allowlist,
not a blocklist: an address token has no shape that can be emitted, including
the fused "(Indep.)102" case, whose digits end the name and whose "(Indep.)"
half is kept as the party.

HOME ADDRESSES ARE NEVER COLLECTED. This table's ADDRESS column is the officer's
RESIDENCE — Mayor Bergfeld at 911 Edwards St., Trustee Casey at 233 Kickapoo Ct.
The Madison precedent applies and the rule is the same one this project has
followed since: an officeholder's home is not ours to publish.

VACANT SEATS ARE COUNTED, NEVER NAMED. The table prints "Vacant" as a seat with
its own term year (Henry's 1st Ward, Lacon's East Ward). Those are reported as a
count so the card can say a seat is empty, and never as a person.

THE LACON PARK BOARD IS SKIPPED. It sits in the middle of the table under its
own heading, and it is a park district body rather than a municipal one — it
does not belong in a municipal-officials roster.

Usage:
    python3 scripts/marshall_municipal_officials_scraper.py --out marshall_muni.json
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    sys.exit("pdfplumber is required: pip install -c scripts/requirements.txt pdfplumber")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PDF = os.path.join(REPO_ROOT, "data", "source", "raw",
                          "Marshall County Cities and Villages 2025-2029.pdf")
COUNTY_SITE = "https://marshallcountyillinois.gov/"
SOURCE_NOTE = ("Marshall County Clerk & Recorder, \"City & Village Elected "
               "Officers - 2025 (4-year term, expires 2029)\", supplied by "
               "e-mail 2026-08-03")

# Nine municipalities, and the counts the table prints. Floors sit under the
# full set so a vacancy or a single dropped seat does not fail the run, but a
# parse regression does.
MIN_PLACES = 8
MIN_OFFICIALS = 70
MIN_HEADS = 8

PLACE_RE = re.compile(r"(?i)^-?\s*(CITY|VILLAGE|TOWN)\s+OF\s+([A-Z][A-Za-z .'-]*)")
# Headings that are NOT municipalities
SKIP_HEADING_RE = re.compile(r"(?i)PARK\s+BOARD")
PHONE_RE = re.compile(r"^\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$")
YEAR_RE = re.compile(r"^(20\d\d)$")
PARTY_RE = re.compile(r"^\((Rep|Dem|Indep?\.?|Ind|R|D)\)", re.I)
APPT_RE = re.compile(r"(?i)^\(?Appt\.?")
WARD_RE = re.compile(r"(?i)^(?:Alderperson|Alderman|Trustee)s?\s*[-–]\s*(.+?)\s*:?$")
BARE_SEAT_RE = re.compile(r"(?i)^Trustee\(?s\)?\s*[-:]?\s*$")
OFFICE_WORDS = ("Mayor", "President", "Clerk", "Treasurer", "Comptroller",
                "Supervisor", "Collector", "Attorney")
PHONE_LABEL_RE = re.compile(r"(?i)^phone:?$")
# The same label with no space before the number, which the document does once.
PHONE_LABEL_GLUED_RE = re.compile(
    r"(?i)^phone:\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})$")
VACANT_RE = re.compile(r"(?i)^vacant\b")


ROW_TOLERANCE = 5.0   # points; see below


def rows_of(page):
    """Group a page's words into visual rows, each sorted left to right.

    CLUSTERED, not bucketed. The office label and the name beside it are not
    always at the identical `top`: "Mayor" sits at 221.0 while "Jeff Bergfeld"
    on the same printed line sits at 220.0. Rounding into fixed buckets put
    those two 1pt apart on opposite sides of a boundary and split the row —
    which cost Henry and Toluca their mayors, and was caught only because the
    head-count floor is a floor on HEADS and not just on total officials.
    """
    words = sorted(page.extract_words(), key=lambda w: (w["top"], w["x0"]))
    row, top = [], None
    for word in words:
        if top is None or word["top"] - top <= ROW_TOLERANCE:
            if top is None:
                top = word["top"]
            row.append(word)
        else:
            yield sorted(row, key=lambda w: w["x0"])
            row, top = [word], word["top"]
    if row:
        yield sorted(row, key=lambda w: w["x0"])


def normalise_party(token):
    match = PARTY_RE.match(token)
    if not match:
        return None
    raw = match.group(1).lower().rstrip(".")
    if raw.startswith("rep") or raw == "r":
        return "R"
    if raw.startswith("dem") or raw == "d":
        return "D"
    return "I"


def split_person(tokens):
    """Name / party / appointed / phone / term from the tokens after the office.

    Name accumulation stops at the first DIGIT-LEADING token, because every
    address in this document starts with a house number. After that point only
    two token shapes are collected — a phone and a 4-digit year — so no address
    fragment has any path into the output.
    """
    name_parts, party, appointed, phone, term = [], None, False, None, None
    in_name = True
    for word in tokens:
        text = word["text"].strip()
        if not text:
            continue

        if PHONE_RE.match(text.strip(".,")):
            phone = text.strip(".,")
            in_name = False
            continue
        if YEAR_RE.match(text):
            term = text
            in_name = False
            continue
        if APPT_RE.match(text):
            appointed = True
            in_name = False if not in_name else in_name
            continue

        this_party = normalise_party(text)
        if this_party:
            party = party or this_party
            # "(Indep.)102" — the party marker fused to a house number. The
            # party is kept; the digits are the address and end the name.
            if re.search(r"\d", text):
                in_name = False
            continue

        if text[0].isdigit():
            # A digit-leading token ends the name ONLY once a name has begun.
            # Some seats print the appointment date BEFORE the officer:
            # "Appt 12/03/2024 David Todd 309 Center St." — treating that date
            # as the start of the address dropped Varna's David Todd and Jeff
            # Rinaldo entirely. A house number always follows a name; an
            # appointment date always precedes one.
            if name_parts:
                in_name = False      # the address column starts here
            continue
        if not in_name:
            continue                 # still inside the address run
        name_parts.append(text)

    name = " ".join(name_parts).strip(" ,.-")
    return name, party, appointed, phone, term


def scrape(path, warnings):
    officials = []
    places = []
    current = None
    current_office = None
    current_ward = None
    skipping = False
    last = None

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for row in rows_of(page):
                line = " ".join(w["text"] for w in row).strip()
                if not line:
                    continue

                if SKIP_HEADING_RE.search(line) and line.lstrip().startswith("-"):
                    skipping = True
                    current_office = current_ward = None
                    warnings.append("skipped a non-municipal body: %s" % line.strip("-"))
                    continue

                place_match = PLACE_RE.match(line)
                if place_match:
                    kind = place_match.group(1).title()
                    name = re.split(r"[(,\-]", place_match.group(2))[0].strip()
                    name = " ".join(part.capitalize() if part.isupper() else part
                                    for part in name.split())
                    current = "%s of %s" % (kind, name.title())
                    places.append(current)
                    current_office = current_ward = None
                    skipping = False
                    last = None
                    continue

                if current is None or skipping:
                    continue

                first = row[0]["text"].strip()

                # "Phone: 309-238-8665" continues the previous person's record.
                # The label and the number are usually separate words, but the
                # document is not consistent about the space after the colon —
                # Wenona's city clerk is written "Phone:708-882-3173" as ONE
                # word, and reading only row[1:] dropped her number silently
                # (14 of the document's 15 numbers have the space, which is
                # exactly why the odd one out went unnoticed).
                glued = PHONE_LABEL_GLUED_RE.match(first)
                if (glued or PHONE_LABEL_RE.match(first.rstrip(":"))) and last is not None:
                    if glued:
                        last["person_phone"] = glued.group(1)
                        continue
                    for word in row[1:]:
                        if PHONE_RE.match(word["text"].strip(".,")):
                            last["person_phone"] = word["text"].strip(".,")
                            break
                    continue

                # A heading that opens a multi-seat office
                ward_match = WARD_RE.match(line)
                if ward_match and not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}\s*$", line):
                    current_office = ("Alderperson" if first.lower().startswith("alder")
                                      else "Trustee")
                    ward = ward_match.group(1).strip().rstrip(":")
                    current_ward = ward or None
                    last = None
                    continue
                if BARE_SEAT_RE.match(line):
                    current_office = "Trustee"
                    current_ward = None
                    last = None
                    continue

                office = None
                rest = row
                for wordname in OFFICE_WORDS:
                    if first.lower().startswith(wordname.lower()):
                        office = wordname
                        rest = row[1:]
                        break

                if office is None:
                    if current_office is None:
                        continue     # zip-code / address-only lines
                    office = current_office
                else:
                    current_ward = None if office not in ("Alderperson", "Trustee") else current_ward

                name, party, appointed, phone, term = split_person(rest)
                if not name:
                    continue
                if VACANT_RE.match(name):
                    officials.append({"jurisdiction": current, "office": office,
                                      "name": None, "vacant": True,
                                      "district": current_ward,
                                      "term_expires": term})
                    last = None
                    continue

                record = {
                    "jurisdiction": current,
                    "office": office,
                    "name": name,
                    "district": current_ward,
                    "party": party,
                    "appointed": appointed,
                    "term_expires": term,
                    "person_phone": phone,
                }
                officials.append(record)
                last = record
    return places, officials


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="marshall_muni.json")
    parser.add_argument("--pdf", default=SOURCE_PDF)
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit("missing archived source: %s" % args.pdf)

    warnings = []
    places, officials = scrape(args.pdf, warnings)

    named = [o for o in officials if o.get("name")]
    vacancies = [o for o in officials if o.get("vacant")]
    heads = sum(1 for o in named if o["office"] in ("Mayor", "President"))

    problems = []
    if len(places) < MIN_PLACES:
        problems.append("%d municipalities < floor %d" % (len(places), MIN_PLACES))
    if len(named) < MIN_OFFICIALS:
        problems.append("%d named officials < floor %d" % (len(named), MIN_OFFICIALS))
    if heads < MIN_HEADS:
        problems.append("%d heads of government < floor %d" % (heads, MIN_HEADS))
    # The privacy invariant, asserted rather than assumed.
    for record in named:
        if re.search(r"\d", record["name"]):
            problems.append("a digit reached a name (%r in %s) — the address "
                            "column may be leaking"
                            % (record["name"], record["jurisdiction"]))
    if problems:
        for problem in problems:
            print("  FAIL: %s" % problem, file=sys.stderr)
        print("FATAL: refusing to write a payload that lost coverage or leaked",
              file=sys.stderr)
        sys.exit(1)

    for record in officials:
        record["source_url"] = COUNTY_SITE
        record["source_note"] = SOURCE_NOTE

    payload = {
        "county": "Marshall",
        "officials_page": COUNTY_SITE,
        "source_note": SOURCE_NOTE,
        "scraped_at": datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "municipalities": sorted(set(places)),
        "officials": [o for o in officials if o.get("name")],
        "vacancies": len(vacancies),
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    per = collections.Counter(o["jurisdiction"] for o in named)
    print("scraped %d municipalities, %d named officials (%d heads, %d with a "
          "phone, %d with a party, %d ward seats), %d vacant seats counted -> %s"
          % (len(set(places)), len(named), heads,
             sum(1 for o in named if o.get("person_phone")),
             sum(1 for o in named if o.get("party")),
             sum(1 for o in named if o.get("district")),
             len(vacancies), args.out), file=sys.stderr)
    for place in sorted(per):
        print("    %-28s %d" % (place, per[place]), file=sys.stderr)
    for warning in warnings:
        print("  note: %s" % warning, file=sys.stderr)


if __name__ == "__main__":
    main()

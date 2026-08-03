#!/usr/bin/env python3
"""
Scrape the Washington County Blue Book into the payload
build_municipal_officials_roster.py consumes.

SOURCE. The "Blue Book of Washington County Illinois", a 40-page directory the
County Clerk & Recorder compiles each term — the 2027-2028 edition here, last
revised July 2026. It is not on the county's website. County Clerk Shari Hempen
forwarded the request to Deputy Recorder Amy Pedtke, who sent the file on
2026-08-03. The copy read here is archived at data/source/raw/, so refreshing it
means asking again; that is why this reads the archive rather than a URL.

WHY A HAND-WRITTEN .doc PARSER. The file is a Word 97 binary document.
LibreOffice is installed in CI's image but refuses to load it ("source file
could not be loaded", alongside a javaldx warning) — a broken install rather
than a broken document, since the OLE2 container is intact. So the text comes
from walking the format's own PIECE TABLE (see doc_text below). That is the only
correct way: a .doc stores text in runs that are NOT in document order, each
independently CP1252 or UTF-16, so scanning the stream for printable runs would
scramble the order and mangle every non-ASCII character. For a roster of
people's names, that kind of quiet corruption is worse than failing outright.

DEPTH. Fourteen municipalities with full governing bodies — president or mayor,
clerk, treasurer, and every trustee, councilman or alderman — carrying each
person's PHONE and, for many, their E-MAIL, plus each municipality's own hall
address and phone. That is the richest municipal source this project has been
given by a clerk.

HOME ADDRESSES ARE NEVER COLLECTED. Under each officer the Blue Book prints
their RESIDENCE — the Nashville mayor at 1652 W. Willowbrook Dr., a trustee at
923 S. Kaskaskia St. The Madison precedent applies. Names are taken only from
cells matching a NAME SHAPE that no address can satisfy (letters, apostrophes
and hyphens, at least two parts, no digits and no ", IL"), which is an allowlist
rather than a filter applied afterwards.

The one address that DOES ship is the municipality's own — the line directly
below each heading, which is the village or city hall and belongs on the card as
the office location. Position distinguishes the two: hall address on the line
after the heading, personal addresses under a person's name.

WRAPPED ROLE LABELS. Some titles occupy two printed lines with the NAME beside
the first half:

    City<TAB><TAB>Terrie Kurwicki<TAB>…<TAB>(618) 327-3058
    Collector:<TAB>371 W. Lebanon St., Nashville, IL. 62263

so "City Collector" has to be assembled across lines, and the second line is an
address rather than a person. Cass needed the same treatment for the same
reason.

DEPARTMENT HEADS ARE SKIPPED. Nashville lists a Chief of Police, a Street
Supervisor and a Utility Supervisor. Those are hired staff, not the governing
body, and the fleet's rule is to carry elected and statutory officers and leave
department heads out. Deputy and Water Clerks go the same way.

Usage:
    python3 scripts/washington_municipal_officials_scraper.py --out washington_muni.json
"""

import argparse
import collections
import datetime
import json
import os
import re
import struct
import sys

try:
    import olefile
except ImportError:  # pragma: no cover
    sys.exit("olefile is required: pip install -c scripts/requirements.txt olefile")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DOC = os.path.join(REPO_ROOT, "data", "source", "raw",
                          "Washington County Blue Book 2027-2028.doc")
COUNTY_SITE = "https://washingtonco.illinois.gov/"
SOURCE_NOTE = ("Washington County Clerk & Recorder, \"Blue Book of Washington "
               "County Illinois, 2027 and 2028\", supplied by e-mail 2026-08-03")

MIN_PLACES = 12
MIN_OFFICIALS = 80
MIN_HEADS = 12
MIN_EMAILS = 20

# The municipal section runs from the first "VILLAGE OF"/"CITY OF" heading to
# the voting-precinct map. Township sections above it use the same role words,
# so the boundary matters.
PLACE_RE = re.compile(r"^(CITY|VILLAGE|TOWN)\s+OF\s+([A-Z][A-Z .'-]*?)\s*$")
END_RE = re.compile(r"^(VOTING PRECINCT MAP|NINETEEN VOTING PRECINCTS)\s*$")

HEAD_OFFICES = {"president": "President", "mayor": "Mayor"}
BOARD_OFFICES = {"trustees": "Trustee", "trustee": "Trustee",
                 "councilmen": "Councilman", "councilman": "Councilman",
                 "aldermen": "Alderman", "alderman": "Alderman"}
OTHER_OFFICES = {"clerk": "Clerk", "city clerk": "Clerk",
                 "village clerk": "Clerk", "treasurer": "Treasurer",
                 "comptroller": "Comptroller", "collector": "Collector",
                 "city collector": "Collector"}
# Hired staff and deputies — not the governing body.
SKIP_OFFICES = ("deputy clerk", "water clerk", "chief of police", "police",
                "street supervisor", "utility supervisor", "supervisor",
                "attorney", "engineer", "superintendent", "zoning")

NAME_RE = re.compile(r"^[A-Z][A-Za-z.'’-]*(?:\s+[A-Z][A-Za-z.'’-]*)+$")
# ", Jr." / ", Sr." / ", III" — the ONLY comma a name may carry. Wamac's mayor
# is "Jackie Butch Mathus, Jr.", and rejecting every comma dropped him.
SUFFIX_RE = re.compile(r"(?i),\s*((?:Jr|Sr|II|III|IV)\.?)$")
WARD_RE = re.compile(r"(?i)^Ward\s*#?\s*(\d+)")
PHONE_RE = re.compile(r"\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MAILTO_RE = re.compile(r'mailto:([^"]+)"')
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def doc_text(path):
    """Word 97 text via the piece table. See the module docstring for why."""
    ole = olefile.OleFileIO(path)
    doc = ole.openstream("WordDocument").read()
    if struct.unpack_from("<H", doc, 0)[0] != 0xA5EC:
        raise SystemExit("%s is not a Word 97 document" % path)
    flags = struct.unpack_from("<H", doc, 0x000A)[0]
    table = ole.openstream("1Table" if (flags & 0x0200) else "0Table").read()

    off = 0x20
    csw = struct.unpack_from("<H", doc, off)[0]
    off += 2 + csw * 2
    cslw = struct.unpack_from("<H", doc, off)[0]
    off += 2 + cslw * 4
    off += 2
    # fcClx is at BYTE offset 0x108 into fibRgFcLcb97 — it is field 66 counting
    # the alternating 4-byte fc/lcb values, NOT the 66th 8-byte pair, which is
    # the easy off-by-double here and lands on a zeroed entry.
    fc_clx, lcb_clx = struct.unpack_from("<II", doc, off + 0x108)
    clx = table[fc_clx:fc_clx + lcb_clx]

    i = 0
    while i < len(clx) and clx[i] == 0x01:          # skip the Prcs
        i += 3 + struct.unpack_from("<h", clx, i + 1)[0]
    if i >= len(clx) or clx[i] != 0x02:
        raise SystemExit("no piece table found in %s" % path)
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5:i + 5 + lcb]

    n = (len(plc) - 4) // 12
    cps = struct.unpack_from("<%dI" % (n + 1), plc, 0)
    out = []
    for p in range(n):
        base = 4 * (n + 1) + p * 8
        fc = struct.unpack_from("<I", plc, base + 2)[0]
        compressed = bool(fc & 0x40000000)
        fc &= ~0x40000000
        length = cps[p + 1] - cps[p]
        if compressed:
            out.append(doc[fc // 2: fc // 2 + length].decode("cp1252", "replace"))
        else:
            out.append(doc[fc: fc + length * 2].decode("utf-16-le", "replace"))
    text = "".join(out).replace("\r", "\n").replace("\x0b", "\n").replace("\x0c", "\n")
    return "".join(c for c in text if c in "\n\t" or c >= " ")


def cells(line):
    return [c.strip() for c in line.split("\t")]


def classify_office(label):
    key = re.sub(r"\s+", " ", label.strip().rstrip(":").lower())
    if any(skip in key for skip in SKIP_OFFICES):
        return None, True
    if key in HEAD_OFFICES:
        return HEAD_OFFICES[key], False
    if key in BOARD_OFFICES:
        return BOARD_OFFICES[key], False
    if key in OTHER_OFFICES:
        return OTHER_OFFICES[key], False
    for word, office in BOARD_OFFICES.items():
        if key.endswith(word):
            return office, False
    for word, office in OTHER_OFFICES.items():
        if key.endswith(word):
            return office, False
    return None, False


def person_name(cell):
    """The name if this cell IS one, else None — the allowlist the privacy rule
    rests on. A residence carries digits and/or ", IL" and can never match."""
    if not cell:
        return None
    core, suffix = cell, ""
    match = SUFFIX_RE.search(cell)
    if match:
        core, suffix = cell[:match.start()].strip(), ", " + match.group(1)
    if "," in core or re.search(r"\d", core):
        return None
    if not NAME_RE.match(core):
        return None
    return core + suffix


def find_phone(cells_):
    for cell in cells_:
        match = PHONE_RE.search(cell or "")
        if match:
            return "(%s) %s-%s" % match.groups()
    return None


def split_hall(text):
    """'Address: 474 W. Main Street, PO Box 341, Ashley, IL. 62808' -> parts."""
    text = re.sub(r"(?i)^address:\s*", "", text).strip().rstrip(",")
    # "City of Nashville, 190 N. East Court" — the hall line sometimes repeats
    # the municipality's own name before the street.
    text = re.sub(r"(?i)^(?:city|village|town)\s+of\s+[^,]+,\s*", "", text)
    zipcode = None
    match = ZIP_RE.search(text)
    if match:
        zipcode = match.group(1)
        text = text[:match.start()].rstrip(" ,")
    text = re.sub(r"(?i),?\s*IL\.?\s*$", "", text).strip().rstrip(",")
    parts = [p.strip() for p in text.split(",") if p.strip()]
    city = parts.pop() if len(parts) > 1 else None
    street = ", ".join(parts) if parts else None
    return street, city, zipcode


def scrape(text, warnings):
    lines = text.split("\n")
    # locate the municipal section
    start = end = None
    for i, line in enumerate(lines):
        if start is None and PLACE_RE.match(line.strip()):
            start = i
        elif start is not None and END_RE.match(line.strip()):
            end = i
            break
    if start is None:
        raise SystemExit("no municipal section found — the Blue Book's layout changed")
    section = lines[start:end if end else len(lines)]

    places, officials = [], []
    halls = {}
    current = None
    office = None
    pending_label = None
    current_ward = None
    held = None
    last = None

    for raw in section:
        line = raw.rstrip()
        if not line.strip():
            continue

        place = PLACE_RE.match(line.strip())
        if place:
            kind = place.group(1).title()
            name = place.group(2).title().strip()
            current = "%s of %s" % (kind, name)
            places.append(current)
            office = None
            pending_label = None
            current_ward = None
            held = None
            last = None
            halls[current] = None
            continue
        if current is None:
            continue

        # The hall line: the first line under the heading. It is the ONLY
        # address that ships — everything else under a person is a residence.
        if halls[current] is None:
            hall_phone = None
            phone = PHONE_RE.search(line)
            if phone:
                hall_phone = "(%s) %s-%s" % phone.groups()
            addr = re.split(r"(?i)\bphone\s*:", line)[0].strip()
            street, city, zipcode = split_hall(addr)
            halls[current] = {"office_address": street, "office_city": city,
                              "office_state": "IL", "office_zip": zipcode,
                              "office_phone": hall_phone}
            continue

        # An e-mail line belongs to the person most recently seen.
        if re.search(r"(?i)e-?mail\s*:", line):
            match = MAILTO_RE.search(line) or EMAIL_RE.search(line)
            if match and last is not None:
                last["person_email"] = match.group(1) if match.re is MAILTO_RE else match.group(0)
            continue

        parts = [c for c in cells(line) if c]
        if not parts:
            continue

        # A label cell ends with ':'. It may be the second half of a WRAPPED
        # title whose first half — and whose person — arrived on the previous
        # line. When that happens the person is HELD rather than emitted, because
        # the office is not known until this line: emitting eagerly gave
        # Nashville's City Collector the previous label ("Treasurer") and let its
        # Street Supervisor through as a Collector, when department heads are
        # meant to be skipped entirely.
        label = None
        rest = parts
        if parts[0].endswith(":"):
            label = parts[0]
            if pending_label:
                label = pending_label + " " + label
                pending_label = None
            rest = parts[1:]
        elif WARD_RE.match(parts[0]):
            current_ward = WARD_RE.match(parts[0]).group(1)
            rest = parts[1:]
        elif (pending_label is None and len(parts) > 1
              and person_name(parts[1] or "")
              and not person_name(parts[0]) and not PHONE_RE.search(parts[0])):
            # "City   Terrie Kurwicki   (618) …" — a wrapped title's first half.
            pending_label = parts[0]
            held = (person_name(parts[1]), find_phone(parts[2:]), current_ward)
            continue

        if label is not None:
            office, skip = classify_office(label)
            if held:
                if not skip and office is not None:
                    record = {"jurisdiction": current, "office": office,
                              "name": held[0], "district": held[2],
                              "person_phone": held[1]}
                    officials.append(record)
                    last = record
                held = None
                # this line is the wrapped title's second half — its remaining
                # cell is the held person's address, so nothing else to read
                office = None if skip else office
                continue
            if skip:
                office = None
                last = None
                continue
            if office is None:
                warnings.append("%s: unrecognised office label %r" % (current, label))
                last = None
                continue
            if office in BOARD_OFFICES.values():
                current_ward = None if not WARD_RE.search(line) else current_ward
            else:
                current_ward = None
        if office is None:
            continue

        # NAME ALLOWLIST: an address cannot match the name shape (it carries
        # digits and/or ", IL"), so a residence has no path into the output.
        name = None
        for cell in rest:
            name = person_name(cell)
            if name:
                break
        if not name:
            continue

        record = {"jurisdiction": current, "office": office, "name": name,
                  "district": current_ward if office in BOARD_OFFICES.values() else None,
                  "person_phone": find_phone([c for c in rest if c != name])}
        officials.append(record)
        last = record

    for record in officials:
        record.update(halls.get(record["jurisdiction"]) or {})
        record["source_url"] = COUNTY_SITE
        record["source_note"] = SOURCE_NOTE
    return places, officials, halls


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="washington_muni.json")
    parser.add_argument("--doc", default=SOURCE_DOC)
    args = parser.parse_args()

    if not os.path.exists(args.doc):
        sys.exit("missing archived source: %s" % args.doc)

    warnings = []
    places, officials, halls = scrape(doc_text(args.doc), warnings)

    heads = sum(1 for o in officials if o["office"] in ("President", "Mayor"))
    emails = sum(1 for o in officials if o.get("person_email"))

    problems = []
    if len(set(places)) < MIN_PLACES:
        problems.append("%d municipalities < floor %d" % (len(set(places)), MIN_PLACES))
    if len(officials) < MIN_OFFICIALS:
        problems.append("%d officials < floor %d" % (len(officials), MIN_OFFICIALS))
    if heads < MIN_HEADS:
        problems.append("%d heads of government < floor %d" % (heads, MIN_HEADS))
    if emails < MIN_EMAILS:
        problems.append("%d e-mails < floor %d — the mailto parse may have moved"
                        % (emails, MIN_EMAILS))
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
        "county": "Washington",
        "officials_page": COUNTY_SITE,
        "source_note": SOURCE_NOTE,
        "scraped_at": datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "municipalities": sorted(set(places)),
        "officials": officials,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    per = collections.Counter(o["jurisdiction"] for o in officials)
    print("scraped %d municipalities, %d officials (%d heads, %d with a phone, "
          "%d with an e-mail), %d halls with an address -> %s"
          % (len(set(places)), len(officials), heads,
             sum(1 for o in officials if o.get("person_phone")), emails,
             sum(1 for h in halls.values() if h and h.get("office_address")),
             args.out), file=sys.stderr)
    for place in sorted(per):
        print("    %-26s %d" % (place, per[place]), file=sys.stderr)
    for warning in warnings:
        print("  note: %s" % warning, file=sys.stderr)


if __name__ == "__main__":
    main()

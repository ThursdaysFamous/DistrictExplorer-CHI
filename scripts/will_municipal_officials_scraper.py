#!/usr/bin/env python3
"""
Will County Municipal Officials Scraper (County Clerk's Will County Directory)
=============================================================================
Extracts every municipality's governing body — village president / mayor,
trustees, ward alderpersons and district councilmembers, plus the clerk and
treasurer — from the Will County Clerk's own annual "Will County Directory".

Why this source: the Clerk publishes the directory as a FlipHTML5 flipbook
linked from willcountyclerk.gov, and it is the county's canonical record of
who holds each local office (fed by the Clerk's Entity Change of Information
process). It covers every municipality that touches Will — including the
cross-county ones (Aurora, Naperville, Tinley Park, Park Forest, Lemont,
Oswego, Minooka) — with the FULL governing body, not just the mayor. The
Clerk's own "elected officials lookup" widget is a third-party JS app with no
scrapable payload, so the directory is the route.

The flipbook exposes a plain-HTML rendition at /basic (and /basic/51-100,
…/251-257) whose `<p class='basic-text'>` blocks carry each page's extracted
PDF text. Section 5, "Municipal Government Officials", holds the entries.
Emails there are Cloudflare-obfuscated (`data-cfemail`) and decoded with the
standard XOR scheme, the same as il_county_clerk_scraper.py.

The book id is NOT hardcoded: it is discovered from the Clerk's own page, so
a new edition published under a new id is followed rather than missed.

Parsing notes (the source is PDF-extracted text, so the shapes vary):
- Office labels can run straight into the name ("Term ExpiresMichael W. Glotz").
- Every board member ends with a 4-digit term-expiry year, which is what
  anchors the member scan.
- Ward/district seats appear as "Ward 3 - Name (PARTY) 2027", sometimes twice
  per ward for staggered terms (Crest Hill), and district cities interleave
  per-seat "Precincts: …" lists (Joliet) which are stripped.
- Clerk/Treasurer are often "(Appointed Position)" — recorded as appointed so
  the card never presents them as elected — and a municipality may list no
  person at all ("Contact Entity for Information"), which yields no record.
- The trailing "Attorney" block is appointed counsel, not an elected officer,
  and is cut before member parsing.

This is the build-time half of the usual two-stage roster pattern; the raw
output is resolved into data/app/municipal-officials.json by
scripts/build_municipal_officials_roster.py.

Usage:
    python3 will_municipal_officials_scraper.py --out will_municipal_officials.json

Notes on data honesty (per project conventions):
- Fields that can't be parsed are stored as null, never guessed.
- Every record includes `source_url` and `scraped_at` for traceability.
- Contact fields are MUNICIPALITY-level (the directory prints one hall
  address/phone/email per entry), so they are emitted per municipality and
  never as a person's own contact.
"""

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone

import requests

CLERK_PAGE = "https://www.willcountyclerk.gov/local-election-officials/"
FLIPBOOK_HOST = "https://fliphtml5.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}
REQUEST_TIMEOUT = 60

# The directory runs ~257 pages; these ranges are the flipbook's own chunking.
PAGE_RANGES = ["", "/51-100", "/101-150", "/151-200", "/201-250", "/251-257"]

HEAD_OFFICES = ("Mayor", "President")
# Board-section headers, longest first so "Councilmembers" wins over "Council".
BOARD_HEADERS = ("Councilmembers", "Councilmember", "Commissioners",
                 "Alderpersons", "Alderperson", "Aldermen", "Trustees", "Trustee")
BOARD_OFFICE_BY_HEADER = {
    "Councilmembers": "Council Member", "Councilmember": "Council Member",
    "Commissioners": "Commissioner",
    "Alderpersons": "Alderperson", "Alderperson": "Alderperson",
    "Aldermen": "Alderperson",
    "Trustees": "Trustee", "Trustee": "Trustee",
}

# Deliberate under-tolerances against the verified 2026-07 live values
# (34 municipal entries, 34 heads of government, 208 board members).
MIN_ENTRIES = 30
MIN_HEADS = 30
MIN_BOARD_MEMBERS = 180


def decode_cfemail(enc):
    """Cloudflare email obfuscation: hex string, first byte is the XOR key."""
    try:
        key = int(enc[:2], 16)
        return "".join(chr(int(enc[i:i + 2], 16) ^ key) for i in range(2, len(enc), 2))
    except (ValueError, IndexError):
        return None


def clean(value):
    if value is None:
        return None
    text = " ".join(str(value).replace(" ", " ").split())
    return text or None


def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def discover_flipbook(page_html):
    """Find the directory flipbook's id from the Clerk's own page."""
    match = re.search(r"(?:online\.)?fliphtml5\.com/([A-Za-z0-9]+)/([A-Za-z0-9]+)", page_html)
    if not match:
        print("FATAL: no FlipHTML5 directory link on %s — page structure changed"
              % CLERK_PAGE, file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2)


def page_texts(book_owner, book_id):
    """Every directory page's extracted text, in order."""
    pages = []
    for rng in PAGE_RANGES:
        url = "%s/%s/%s/basic%s" % (FLIPBOOK_HOST, book_owner, book_id, rng)
        markup = fetch(url)
        # Decode obfuscated emails in place so they survive tag stripping.
        markup = re.sub(
            r'<a[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</a>',
            lambda m: decode_cfemail(m.group(1)) or "",
            markup, flags=re.S)
        blocks = re.findall(r"<p class='basic-text'>(.*?)</p>", markup, re.S)
        if not blocks:
            print("FATAL: no page text blocks at %s — flipbook layout changed" % url,
                  file=sys.stderr)
            sys.exit(1)
        for block in blocks:
            text = re.sub(r"<[^>]+>", " ", block)
            pages.append(clean(html.unescape(text)) or "")
    return pages


def municipal_section(pages):
    """The run of pages holding Section 5, Municipal Government Officials."""
    start = None
    for i, text in enumerate(pages):
        if start is None and re.search(r"CITY OFFICIALS|VILLAGE OFFICIALS", text):
            start = i
        elif start is not None and re.search(r"TOWNSHIP OFFICIALS", text):
            return " ".join(pages[start:i])
    if start is None:
        print("FATAL: no municipal-officials section found — directory layout changed",
              file=sys.stderr)
        sys.exit(1)
    return " ".join(pages[start:])


def split_entries(section):
    parts = re.split(r"(?=(?:CITY|VILLAGE|TOWN) OF [A-Z])", section)
    return [p for p in parts if re.match(r"(CITY|VILLAGE|TOWN) OF [A-Z]", p)]


def strip_precincts(text):
    """Drop the interleaved per-seat precinct lists.

    The lookahead must name every marker that can follow a precinct list —
    including the head/officer labels, since the entry's first precinct list
    is followed by the hall contact block and then "Mayor"/"President".
    """
    return re.sub(
        r"Precincts?:.*?(?=(?:Ward|District)\s+\d+\s*-|"
        r"Attorney\b|Trustees?\b|Councilmembers?\b|Alderpersons?\b|Aldermen\b|"
        r"Commissioners?\b|Mayor\b|President\b|Clerk\b|Treasurer\b|$)",
        " ", text, flags=re.S)


def parse_header(entry):
    """-> (jurisdiction, address, phone, email, website)."""
    name_match = re.match(r"((?:CITY|VILLAGE|TOWN) OF [A-Z][A-Za-z\.\'’\- ]*?)\s*\(", entry)
    if not name_match:
        return None, None, None, None, None
    raw = clean(name_match.group(1))
    # "CITY OF CREST HILL" -> "City of Crest Hill" (the builder's GEOID join
    # normalizes anyway; this is what the card prints).
    kind, _, rest = raw.partition(" OF ")
    jurisdiction = "%s of %s" % (kind.capitalize(), rest.title())

    website = None
    site = re.search(r"Website:\s*([A-Za-z0-9\.\-/]+)", entry)
    if site:
        website = clean(site.group(1))

    email = None
    mail = re.search(r"Email:\s*([^\s]+@[^\s]+)", entry)
    if mail:
        email = clean(mail.group(1))  # "Contact Us link on website" is not an email

    phone = None
    tel = re.search(r"\((\d{3})\)\s*(\d{3})-(\d{4})", entry)
    if tel:
        phone = "%s-%s-%s" % tel.groups()

    return jurisdiction, parse_address(entry), phone, email, website


def parse_address(entry):
    """The hall address, or None when the flattened text can't delimit it.

    The PDF's line breaks are lost in this rendition, so a preceding precinct
    list runs straight into the street number. Where the join carries a
    separator the split is unambiguous — "…3P625 Dixie Highway" (the precinct
    token's trailing P), "…35P 44 E. Downer Pl." (whitespace), "(Will
    County)20600 City Center Blvd." (no precincts at all). Where the last
    precinct token is a BARE number the two run together with nothing between
    them ("…18P & 19150 W. Jefferson St." is precinct 19 + 150 W. Jefferson),
    and the street number cannot be recovered from the text. Those return
    None: the card drops the address line rather than print a guessed one.
    """
    anchor = re.search(r"(\d{5})\s*\(\d{3}\)\s*\d{3}-\d{4}", entry)
    if not anchor:
        return None
    head = entry[:anchor.start(1)]
    zipcode = anchor.group(1)

    # Walk candidate street starts left-to-right; the first one that reaches
    # the ZIP is the address (a later start would truncate the street).
    for m in re.finditer(r"\d", head):
        start = m.start()
        candidate = head[start:]
        if not re.match(r"\d{1,6}\s+[A-Z0-9]", candidate):
            continue
        if not re.search(r",\s*[A-Za-z\.\'’\- ]+\s*$", candidate):
            continue  # must end "…, City " right before the ZIP
        before = head[start - 1] if start else ")"
        if before.isdigit():
            return None  # glued to a bare precinct number — undelimitable
        if before.isspace():
            prev = head[:start].rstrip()
            # A preceding bare precinct number means the same ambiguity, one
            # space over ("& 19150"): only a P-suffixed or non-numeric token
            # proves the precinct list actually ended.
            if prev and prev[-1].isdigit():
                return None
        return clean(candidate.rstrip().rstrip(",") + " " + zipcode)
    return None


# A personal name as the directory prints it. Three shapes the flattened text
# forces us to absorb: an inline parenthetical nickname ("Teresa (Terry) A.
# Kernc" — distinguishable from a party code because party codes are ALL-CAPS),
# curly-quoted nicknames ("Sharon “Sherri” Reardon"), and a comma-separated
# generational suffix ("Joseph E. Roudez, III").
_CH = r"[A-Za-z\.\'‘’“”\-À-ɏ]"
NAME_RE = (r"[A-Z]" + _CH + r"*"
           r"(?:\s*\((?![A-Z]{1,6}\))[A-Za-z\.\'‘’“”\- ]+\))?"
           r"(?:\s+" + _CH + r"+){0,4}?"
           r"(?:,\s*(?:Jr|Sr|II|III|IV|V)\.?)?")
# Party codes are all-caps abbreviations (IND, OTP, DEM, D, R).
PARTY_RE = r"[A-Z]{1,6}"

# NAME_RE's trailing words are LAZY, which is right where a term-expiry year
# follows and forces them to expand. A clerk/treasurer line has no such anchor
# ("Clerk (Appointed Position)Laura Warren Email: …"), so the lazy form would
# stop at the first word and ship "Laura". This greedy variant takes the
# surname too, refusing to cross into the next label.
_LABELS = (r"Email|Website|Term|Expires|Precincts?|Attorney|Trustees?|"
           r"Alderpersons?|Aldermen|Councilmembers?|Commissioners?|"
           r"Clerk|Treasurer|Mayor|President|Appointed|Contact")
OFFICER_NAME_RE = (r"[A-Z]" + _CH + r"*"
                   r"(?:\s*\((?![A-Z]{1,6}\))[A-Za-z\.\'‘’“”\- ]+\))?"
                   r"(?:\s+(?!(?:" + _LABELS + r")\b)" + _CH + r"+){0,4}"
                   r"(?:,\s*(?:Jr|Sr|II|III|IV|V)\.?)?")

PERSON = re.compile(
    r"(?:(?P<kind>Ward|District)\s+(?P<num>\d+)\s*-\s*)?"
    r"(?:(?P<atlarge>At\s+Large)\s+)?"
    r"(?P<name>" + NAME_RE + r")"
    r"(?:\s*-\s*Appt\.?[^0-9]*\d{1,2}/\d{4})?"
    r"\s*(?:\((?P<party>" + PARTY_RE + r")\))?"
    r"\s*(?P<year>20\d{2})")


def parse_members(text, office):
    """Every '<name> [(PARTY)] <year>' run in a board section.

    "At Large" labels a GROUP of seats, not one ("Councilmembers At Large Joe
    Clement 2029 Juan Moreno 2029 Jan Quillman 2029"), so it stays in force
    until a Ward/District seat appears. A body with no at-large label never
    sets it, so ordinary village trustees keep district=None.
    """
    members = []
    at_large = False
    for m in PERSON.finditer(text):
        name = clean(m.group("name"))
        if not name or len(name) < 3:
            continue
        # Guard against label fragments the office headers leave behind.
        if re.fullmatch(r"(?:Term Expires|Expires|At Large|Trustees?|Alderpersons?|"
                        r"Councilmembers?|Commissioners?|Precincts?|Attorney|Email|Website)",
                        name, flags=re.I):
            continue
        district = None
        if m.group("kind"):
            at_large = False
            district = "%s %s" % (m.group("kind").capitalize(), m.group("num"))
        else:
            if m.group("atlarge"):
                at_large = True
            if at_large:
                district = "At Large"
        members.append({
            "office": office,
            "district": district,
            "name": name,
            "party": clean(m.group("party")),
            "term_expires": clean(m.group("year")),
            "appointed": False,
        })
    return members


def parse_officer(entry, label):
    """Clerk / Treasurer — elected or explicitly '(Appointed Position)'."""
    m = re.search(label + r"\s*(?P<appt>\(Appointed Position\))?\s*"
                  r"(?P<name>" + OFFICER_NAME_RE + r")", entry)
    if not m:
        return None
    name = clean(m.group("name"))
    if not name:
        return None
    # The directory prints this where an office has no named holder.
    if re.match(r"Contact Entity", name, flags=re.I):
        return None
    party = re.search(re.escape(name) + r"\s*\((" + PARTY_RE + r")\)", entry)
    year = re.search(re.escape(name) + r"[^0-9]{0,20}(20\d{2})", entry)
    return {
        "office": label,
        "district": None,
        "name": name,
        "party": clean(party.group(1)) if party else None,
        "term_expires": clean(year.group(1)) if year else None,
        "appointed": bool(m.group("appt")),
    }


def parse_entry(entry):
    jurisdiction, address, phone, email, website = parse_header(entry)
    if not jurisdiction:
        return None, []
    body = strip_precincts(entry)
    # Appointed counsel and the party legend trail every entry.
    body = re.split(r"\bAttorney\b", body)[0]

    people = []
    head = re.search(r"(Mayor|President)\s*(?:Term\s*Expires)?\s*"
                     r"(?P<name>" + NAME_RE + r")"
                     r"\s*(?:\((?P<party>" + PARTY_RE + r")\))?\s*(?P<year>20\d{2})", body)
    if head:
        people.append({
            "office": head.group(1), "district": None, "name": clean(head.group("name")),
            "party": clean(head.group("party")), "term_expires": clean(head.group("year")),
            "appointed": False,
        })
    for label in ("Clerk", "Treasurer"):
        officer = parse_officer(body, label)
        if officer:
            people.append(officer)

    # Board section: from its header to the end of the (attorney-trimmed) entry.
    for header in BOARD_HEADERS:
        # No \b anchors: the flattened text glues labels to their neighbours
        # ("Stacey PetersonAlderperson Ward 1", "AlderpersonWard 1"), so a
        # bounded match would skip the real section header. BOARD_HEADERS is
        # ordered longest-first, which keeps the plain substring unambiguous.
        m = re.search(re.escape(header), body)
        if not m:
            continue
        tail = body[m.end():]
        for label in BOARD_HEADERS:
            tail = tail.replace(label, " ")
        # Names already claimed by the head/clerk/treasurer scan must not repeat.
        claimed = {p["name"] for p in people if p["name"]}
        for member in parse_members(tail, BOARD_OFFICE_BY_HEADER[header]):
            if member["name"] in claimed:
                continue
            people.append(member)
        break

    for person in people:
        person["jurisdiction"] = jurisdiction
        person["office_address"] = address
        person["office_city"] = None
        person["office_state"] = None
        person["office_zip"] = None
        person["office_phone"] = phone
        person["office_email"] = email
        person["website"] = website
    return jurisdiction, people


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="will_municipal_officials.json")
    args = parser.parse_args()

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    owner, book = discover_flipbook(fetch(CLERK_PAGE))
    directory_url = "%s/%s/%s/" % (FLIPBOOK_HOST, owner, book)
    section = municipal_section(page_texts(owner, book))

    entries = split_entries(section)
    if len(entries) < MIN_ENTRIES:
        print("FATAL: only %d municipal entries parsed (expected >= %d) — layout changed"
              % (len(entries), MIN_ENTRIES), file=sys.stderr)
        sys.exit(1)

    municipalities = []
    officials = []
    for entry in entries:
        jurisdiction, people = parse_entry(entry)
        if not jurisdiction:
            continue
        municipalities.append({
            "name": jurisdiction,
            "source_url": directory_url,
            "scraped_at": scraped_at,
        })
        for person in people:
            person["source_url"] = directory_url
            person["scraped_at"] = scraped_at
            officials.append(person)

    heads = sum(1 for p in officials if p["office"] in HEAD_OFFICES)
    board = sum(1 for p in officials
                if p["office"] in set(BOARD_OFFICE_BY_HEADER.values()))
    if heads < MIN_HEADS:
        print("FATAL: only %d heads of government parsed (expected >= %d)"
              % (heads, MIN_HEADS), file=sys.stderr)
        sys.exit(1)
    if board < MIN_BOARD_MEMBERS:
        print("FATAL: only %d board members parsed (expected >= %d)"
              % (board, MIN_BOARD_MEMBERS), file=sys.stderr)
        sys.exit(1)

    payload = {
        "county": "Will",
        "directory_url": directory_url,
        "scraped_at": scraped_at,
        "municipalities": municipalities,
        "officials": officials,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    seats = sum(1 for p in officials if p["district"])
    print("scraped %d municipalities, %d officials (%d heads, %d board members, "
          "%d ward/district seats) -> %s"
          % (len(municipalities), len(officials), heads, board, seats, args.out),
          file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
DuPage County Municipal Officials Scraper (DMMC Membership Directory)
====================================================================
Extracts each DuPage-area municipality's head of government — plus village/city
hall address and official website — from the DuPage Mayors and Managers
Conference (DMMC) Membership Directory.

Why this source: DuPage County government publishes NO municipal-officials
directory (verified 2026-07: the county's Elected Officials page covers
countywide offices only, the Clerk's election division publishes candidate
listings but no officeholder roster, and the county GIS carries municipal
boundaries with zero officials data). DMMC — the council of governments whose
members are the municipalities themselves — is the only verified source naming
DuPage mayors and village presidents, which makes this rung 3 of the source
ladder (docs/EXPANSION_GUIDE.md Part 2.4).

DEPTH: head of government only. The directory prints no trustees or aldermen,
so this county ships a `head` with no `board`, and the Municipality card links
the village's own site for the full board.

Two deliberate omissions, both honesty-driven:
- The directory's phone numbers are printed WITHOUT an area code ("543-4100
  main"), and the document states no default. A 7-digit string would render as
  a dead tel: link, and DuPage-area municipalities span 630/331/708/847 — so
  phone is stored null rather than completed by guess.
- The manager/administrator printed under each mayor is APPOINTED staff, not
  an elected officer. The card's officers section is titled "Other Elected
  Officials", so shipping an appointee there would mislabel them; they are
  excluded rather than misfiled.

COVERAGE: DMMC has 35 full members plus 1 associate. A handful of
municipalities that touch DuPage are not DMMC members and therefore carry no
DuPage entry; those that also touch a sourced county resolve from it through
the builder's depth precedence.

The directory is a text PDF laid out in FOUR fixed columns, so it is parsed in
pypdf layout mode with the column boundaries derived from the entry headers'
own x-positions (never hardcoded — the edition's layout may shift). Kerning
splits long tokens with runs of spaces inside a single value
("www.burr       -ridge.gov"), so URLs are rejoined by stripping internal
whitespace (docs/EXPANSION_GUIDE.md Part 2.4, PDF-parse lessons).

The PDF's URL is date-stamped per edition
(.../2026/05/Membership-Directory-25-26-5.12.2026.pdf) and DOES change, so it
is always discovered from the membership-list page rather than hardcoded.

Usage:
    python3 dupage_municipal_officials_scraper.py --out dupage_municipal_officials.json

Notes on data honesty (per project conventions):
- Fields that can't be parsed are stored as null, never guessed.
- Every record includes `source_url` and `scraped_at` for traceability.
- Contact is MUNICIPALITY-level (one village hall per entry), emitted under the
  municipality and never as a person's own contact.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone

import requests

MEMBERSHIP_URL = "https://dmmc-cog.org/membership-list/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}
REQUEST_TIMEOUT = 120

# "ADDISON (V)  www.addisonadvantage.org" — (V)illage or (C)ity.
HEADER_RE = re.compile(
    r"^(?P<name>[A-Z][A-Z .'’\-]*?)\s*\((?P<kind>V|C)\)\s*(?P<web>.*)$"
)
HEADER_ANY_RE = re.compile(r"[A-Z][A-Z .'’\-]*?\s*\((?:V|C)\)")
# "Tom Hundley, Mayor" / "Heidi Rudolph, President"
HEAD_RE = re.compile(r"^(?P<name>.+?),\s*(?P<title>Mayor|President|Village President)$", re.I)
# "1 Friendship Plaza, 60101"
ADDRESS_RE = re.compile(r"^(?P<street>.+?),\s*(?P<zip>\d{5})$")

# Deliberate under-tolerance against the verified 2026-07 live value (36
# entries: 35 members + 1 associate, every one carrying a head and an address).
MIN_MUNICIPALITIES = 32
MIN_HEADS = 32


def fetch(url, binary=False):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.content if binary else resp.text


def discover_pdf_url(page_html):
    """The directory's URL carries its edition date and changes — never hardcode."""
    links = re.findall(r'href="(?P<url>[^"]+\.pdf)"', page_html, flags=re.I)
    preferred = [u for u in links if re.search(r"member", u, re.I)]
    chosen = preferred or links
    if not chosen:
        print("FATAL: no PDF link found on %s — the membership page changed"
              % MEMBERSHIP_URL, file=sys.stderr)
        sys.exit(1)
    return chosen[0]


def directory_pages(body):
    import io

    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(body))
    return [(page.extract_text(extraction_mode="layout") or "") for page in reader.pages]


def column_bounds(lines):
    """Derive the fixed column x-positions from where entry headers start.

    Deriving beats hardcoding: an edition that re-flows to three or five
    columns still parses, and a layout that stops matching fails the floor
    check loudly instead of silently halving the roster.
    """
    starts = sorted({m.start() for line in lines for m in HEADER_ANY_RE.finditer(line)})
    if not starts:
        return []
    return list(zip(starts, list(starts[1:]) + [10 ** 6]))


def clean(value):
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def clean_url(value):
    """Rejoin a URL the PDF's kerning split ("www.burr       -ridge.gov")."""
    if not value:
        return None
    text = re.sub(r"\s+", "", str(value))
    return text or None


def parse_entries(page_text):
    """-> [{name, kind, website, rows[]}] across every column of one page."""
    lines = [line.rstrip() for line in page_text.splitlines() if line.strip()]
    entries = []
    for start, end in column_bounds(lines):
        current = None
        for line in lines:
            cell = clean(line[start:end])
            if not cell:
                continue
            match = HEADER_RE.match(cell)
            if match:
                current = {
                    "name": clean(match.group("name")),
                    "kind": match.group("kind"),
                    "website": clean_url(match.group("web")),
                    "rows": [],
                }
                entries.append(current)
                continue
            if current is not None:
                current["rows"].append(cell)
    return entries


def records_for(entry, scraped_at, source_url):
    head = None
    address = None
    for row in entry["rows"]:
        if head is None:
            match = HEAD_RE.match(row)
            if match:
                head = (clean(match.group("name")), clean(match.group("title")))
        if address is None:
            match = ADDRESS_RE.match(row)
            if match:
                address = (clean(match.group("street")), match.group("zip"))
    if head is None:
        print("WARNING: no head of government parsed for %s — check the directory layout"
              % entry["name"], file=sys.stderr)
        return []

    # The directory prints the government form as (V)/(C); carrying it into the
    # jurisdiction name matches the Cook source's "Village of Alsip" shape, which
    # is what the card reads to title the hall row ("Village Hall" vs "City
    # Hall"). The builder strips the prefix again before joining on GEOID.
    plain = entry["name"].title()
    jurisdiction = ("Village of " if entry["kind"] == "V" else "City of ") + plain
    return [{
        "jurisdiction": jurisdiction,
        "office": head[1],
        "district": None,
        "name": head[0],
        "office_address": address[0] if address else None,
        "office_city": plain if address else None,
        "office_state": "IL" if address else None,
        "office_zip": address[1] if address else None,
        # Printed without an area code by the source — see the module docstring.
        "office_phone": None,
        "office_email": None,
        "website": entry["website"],
        "source_url": source_url,
        "scraped_at": scraped_at,
    }]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="dupage_municipal_officials.json")
    parser.add_argument("--pdf", help="parse a local PDF instead of fetching (testing)")
    args = parser.parse_args()

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.pdf:
        pdf_url = MEMBERSHIP_URL
        with open(args.pdf, "rb") as f:
            body = f.read()
    else:
        pdf_url = discover_pdf_url(fetch(MEMBERSHIP_URL))
        body = fetch(pdf_url, binary=True)
        if not body.startswith(b"%PDF"):
            print("FATAL: %s did not return a PDF — source moved" % pdf_url, file=sys.stderr)
            sys.exit(1)

    records = []
    for page_text in directory_pages(body):
        for entry in parse_entries(page_text):
            records.extend(records_for(entry, scraped_at, pdf_url))

    municipalities = sorted({r["jurisdiction"] for r in records})
    if len(municipalities) < MIN_MUNICIPALITIES:
        print("FATAL: parsed %d municipalities (expected >= %d) — the directory's layout "
              "changed or the fetch was partial" % (len(municipalities), MIN_MUNICIPALITIES),
              file=sys.stderr)
        sys.exit(1)
    if len(records) < MIN_HEADS:
        print("FATAL: parsed %d heads of government (expected >= %d)"
              % (len(records), MIN_HEADS), file=sys.stderr)
        sys.exit(1)

    payload = {
        "county": "DuPage",
        "directory_url": pdf_url,
        "scraped_at": scraped_at,
        "officials": records,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print("scraped %d municipalities, %d heads of government -> %s"
          % (len(municipalities), len(records), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()

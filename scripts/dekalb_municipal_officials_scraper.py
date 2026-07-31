#!/usr/bin/env python3
"""
Scrape DeKalb County's clerk yearbook into the payload
build_municipal_officials_roster.py consumes.

SOURCE. The clerk's "Municipalities of DeKalb County" section lists every one of
the county's fourteen municipalities with its FULL governing body — head of
government, clerk, treasurer where the municipality elects one, and every
trustee / ward alderman — plus the hall address, phone, website and, uniquely
among the county sources in this repo, the date each seat is NEXT on the ballot.
That is Cook/Will/LaSalle/Ogle depth from one county document, so DeKalb joins as
a full-governing-body county rather than a mayor-level one.

FETCH POSTURE: open. Plain `requests` with a browser UA gets both the landing
page and the PDF.

URL DISCOVERY, not a hardcoded path. The yearbook lives on the CLERK's domain
under a month-stamped uploads path (…/wp-content/uploads/2025/11/…), but it is
linked from the COUNTY's reference page — so the link is read off that page and
the constant below is only the fallback. Hardcoding the stamped path would go
stale the first time the clerk republishes, which is annually.

WHY A LINE PARSER. Each municipality is a "Position | Name | Next Election"
table rendered as one officer per line, and pypdf's line extraction preserves
that exactly — the same shape as Ogle's yearbook and unlike LaSalle's
six-column directory, which needed word positions.

TWO RULES THAT DROP PUBLISHED ROWS, both logged rather than silent:

  * A seat printed as "Vacant" is not a person. Somonauk publishes one; shipping
    it would put a trustee named Vacant on a card.
  * A name that appears BOTH as the head of government and as a board member is
    kept only as the head. Hinckley prints Sarah Quirk as President and again as
    a Trustee; Illinois village presidents are elected to that office separately
    and cannot simultaneously hold a trustee seat, so one of the two rows is
    stale. The head row is the more specific claim, so the board row goes and
    the drop is reported. This is a rule about what the source can be saying at
    once, not a guess about which name is right.

WHAT IS DELIBERATELY NOT COLLECTED: nothing per-person. The address, phone and
website are the municipality's, and are carried at that level only — this
document publishes no direct line or e-mail for any individual officer.

Usage:
    python3 dekalb_municipal_officials_scraper.py --out dekalb_municipal_officials.json
    python3 dekalb_municipal_officials_scraper.py --out out.json --pdf local.pdf
"""

import argparse
import datetime
import io
import json
import re
import sys
import urllib.parse

import requests

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None

REFERENCE_PAGE = "https://dekalbcounty.org/about/reference-yearbook/"
# Fallback only — the live URL is read off REFERENCE_PAGE (see module docstring).
YEARBOOK_URL = ("https://dekalbcountyclerkil.gov/wp-content/uploads/2025/11/"
                "2025-2026_Yearbook_Web.pdf")
CLERK_PAGE = "https://dekalbcountyclerkil.gov/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
}
REQUEST_TIMEOUT = 120

YEARBOOK_LINK_RE = re.compile(r'href="([^"]*[Yy]earbook[^"]*\.pdf)"')
# Both headings are anchored to a WHOLE LINE. The book's index carries each of
# them too, as "Municipalities of DeKalb County ......... 74" — a substring
# search finds the index entry first and bounds the section to a few characters
# of dot leaders, which is exactly what it did on the first run.
START_RE = re.compile(r"^Municipalities of DeKalb County$", re.I)
# The section is bounded on the far side by the county's township directory.
END_RE = re.compile(r"^Townships of DeKalb County$", re.I)

MUNI_RE = re.compile(r"^(City|Village|Town) of ([A-Z][A-Za-z .'-]+?)\s*$")
PHONE_RE = re.compile(r"Phone:\s*\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})", re.I)
WEBSITE_RE = re.compile(r"^(https?://\S+?)/?\s*$", re.I)
# The locality sits on its own line for eight of the fourteen halls ("Cortland,
# IL 60112") and shares the street's line for the other six ("164 E. Lincoln
# Hwy., DeKalb, IL 60115"), so the leading street group is OPTIONAL. Requiring
# it silently dropped the city and ZIP from eight of fourteen cards.
CITY_ZIP_RE = re.compile(r"^(?:(.*),\s*)?([A-Za-z][A-Za-z .'-]*),\s*IL\s*(\d{5})(?:-\d{4})?\s*$", re.I)
PO_BOX_RE = re.compile(r",?\s*P\.?\s?O\.?\s?Box\s+\d+,?\s*$", re.I)

# "1st Ward Alderman Carolyn Morris Zasada 04/06/2027"
WARD_SEAT_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)\s+Ward\s+"
                          r"(Alderman|Alderperson|Alderwoman|Councilman|Councilwoman|"
                          r"Council Member)\s+(.+?)\s+(\d{2}/\d{2}/\d{4}|Appointed)\s*$", re.I)
# "Trustee Doug Corson 04/06/2027" / "Clerk Elizabeth Losiniecki Appointed"
OFFICE_RE = re.compile(r"^(Mayor|President|Village President|Clerk|City Clerk|Village Clerk|"
                       r"Treasurer|Collector|Trustee|Commissioner|Alderman|Alderperson|"
                       r"Council Member|Councilman|Councilwoman)\s+(.+?)\s+"
                       r"(\d{2}/\d{2}/\d{4}|Appointed)\s*$", re.I)
DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

NON_PERSON_NAMES = {"vacant", "vacancy", "unassigned", "open", "tbd", "none", "n/a"}
HEAD_TITLES = {"mayor", "president", "village president"}

MIN_MUNICIPALITIES = 12
MIN_OFFICIALS = 110
MIN_HEADS = 12
MIN_WARD_SEATS = 25


def clean(value):
    value = re.sub(r"\s+", " ", (value or "")).strip().strip(",")
    return value or None


def norm_office(raw):
    office = re.sub(r"\s+", " ", (raw or "").strip()).rstrip(".")
    return office.title() if office.islower() or office.isupper() else office


def iso_date(raw):
    """'04/03/2029' -> '2029-04-03'. The builder keeps only the year."""
    match = DATE_RE.match((raw or "").strip())
    if not match:
        return None
    return "%s-%s-%s" % (match.group(3), match.group(1), match.group(2))


def discover_pdf_url(warnings):
    try:
        resp = requests.get(REFERENCE_PAGE, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        warnings.append("could not read %s (%s) — falling back to the last known "
                        "yearbook URL" % (REFERENCE_PAGE, exc))
        return YEARBOOK_URL
    links = YEARBOOK_LINK_RE.findall(resp.text)
    if not links:
        warnings.append("no *Yearbook*.pdf link on %s — falling back to the last "
                        "known yearbook URL" % REFERENCE_PAGE)
        return YEARBOOK_URL
    # Newest first: the clerk's uploads path is month-stamped, so the highest
    # path sorts to the current edition even when older ones stay linked.
    return sorted(urllib.parse.urljoin(REFERENCE_PAGE, href) for href in links)[-1]


def fetch_pdf(url):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    if not resp.content.startswith(b"%PDF"):
        raise RuntimeError("yearbook URL did not return a PDF (got %d bytes of %s)"
                           % (len(resp.content), resp.headers.get("Content-Type")))
    return resp.content


def section_lines(pdf_bytes):
    if pypdf is None:
        raise RuntimeError("pypdf is required (pip install -c scripts/requirements.txt pypdf)")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    lines = [l.rstrip() for l in text.split("\n")]
    start = next((i for i, l in enumerate(lines) if START_RE.match(l.strip())), None)
    if start is None:
        raise RuntimeError("could not find the 'Municipalities of DeKalb County' "
                           "heading — the yearbook's layout changed")
    end = next((i for i in range(start + 1, len(lines))
                if END_RE.match(lines[i].strip())), None)
    if end is None:
        raise RuntimeError("could not find the 'Townships of DeKalb County' heading "
                           "that bounds the municipal section")
    return lines[start + 1:end]


def parse_hall(lines):
    """-> (street, city, zip) from a block's pre-table header lines."""
    street = city = zipcode = None
    for raw in lines:
        text = raw.strip()
        if not text or WEBSITE_RE.match(text):
            continue
        if re.match(r"^(Phone|Fax|Position)\b", text, re.I):
            continue
        match = CITY_ZIP_RE.match(text)
        if match:
            city, zipcode = clean(match.group(2)), match.group(3)
            # "P.O. Box 65, Lee, IL 60530" carries the street part on the same
            # line as the locality; "Cortland, IL 60112" carries none.
            lead = clean(match.group(1))
            if lead and not street:
                street = lead
            continue
        if re.search(r"\d|P\.?\s?O\.?\s?Box", text, re.I) and not street:
            street = clean(text)
    # The hall is a physical place; where the county gives both a street and a
    # mailing box, the box is dropped rather than concatenated onto the address
    # a visitor would drive to. Where the box is all there is, it stays.
    if street and not PO_BOX_RE.match(street):
        trimmed = PO_BOX_RE.sub("", street)
        if trimmed.strip():
            street = clean(trimmed)
    return street, city, zipcode


def parse(lines, warnings):
    blocks, current = [], None
    for line in lines:
        match = MUNI_RE.match(line.strip())
        if match:
            current = {"kind": match.group(1), "name": clean(match.group(2)), "lines": []}
            blocks.append(current)
        elif current is not None:
            current["lines"].append(line)
    if not blocks:
        raise RuntimeError("no 'City/Village/Town of X' headers in the section")

    municipalities, officials = [], []
    for block in blocks:
        name = block["name"]
        municipalities.append(name)
        body = "\n".join(block["lines"])
        phone_match = PHONE_RE.search(body)
        site = None
        for raw in block["lines"]:
            site_match = WEBSITE_RE.match(raw.strip())
            if site_match:
                site = site_match.group(1)
                break

        head_lines = []
        for raw in block["lines"]:
            text = raw.strip()
            if WARD_SEAT_RE.match(text) or OFFICE_RE.match(text):
                break
            head_lines.append(raw)
        street, city, zipcode = parse_hall(head_lines)

        shared = {
            "jurisdiction": "%s of %s" % (block["kind"], name),
            "office_address": street,
            "office_city": city,
            "office_state": "IL" if city else None,
            "office_zip": zipcode,
            "office_phone": ("%s-%s-%s" % phone_match.groups()) if phone_match else None,
            "office_email": None,
            "website": site,
        }

        rows = []
        for raw in block["lines"]:
            text = raw.strip()
            if not text or text.lower().startswith("meetings:"):
                continue
            ward = WARD_SEAT_RE.match(text)
            if ward:
                rows.append({"office": norm_office(ward.group(2)),
                             "district": ward.group(1).lstrip("0") or ward.group(1),
                             "name": clean(ward.group(3)), "when": ward.group(4)})
                continue
            office = OFFICE_RE.match(text)
            if office:
                rows.append({"office": norm_office(office.group(1)), "district": None,
                             "name": clean(office.group(2)), "when": office.group(3)})
        if not rows:
            warnings.append("no officers parsed for %s — check the yearbook layout" % name)
            continue

        head_names = {r["name"].lower() for r in rows
                      if (r["office"] or "").lower() in HEAD_TITLES and r["name"]}
        for row in rows:
            person = row["name"]
            if not person or person.lower() in NON_PERSON_NAMES:
                warnings.append("dropped a %s seat published as '%s' in %s of %s"
                                % (row["office"], person, block["kind"], name))
                continue
            office_low = (row["office"] or "").lower()
            if office_low not in HEAD_TITLES and person.lower() in head_names:
                warnings.append("dropped the %s row for %s in %s of %s — the same "
                                "person is published as the head of government"
                                % (row["office"], person, block["kind"], name))
                continue
            record = dict(shared, office=row["office"], district=row["district"],
                          name=person)
            if row["when"].lower() == "appointed":
                record["appointed"] = True
            else:
                record["next_election"] = iso_date(row["when"])
            officials.append(record)
    return municipalities, officials


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--pdf", help="parse a local copy instead of fetching")
    args = parser.parse_args()

    warnings = []
    try:
        if args.pdf:
            source_url, pdf_bytes = YEARBOOK_URL, open(args.pdf, "rb").read()
        else:
            source_url = discover_pdf_url(warnings)
            pdf_bytes = fetch_pdf(source_url)
        municipalities, officials = parse(section_lines(pdf_bytes), warnings)
    except Exception as exc:  # noqa: BLE001
        print("FATAL: %s" % exc, file=sys.stderr)
        sys.exit(1)

    for warning in sorted(set(warnings)):
        print("  warning: %s" % warning, file=sys.stderr)

    heads = sum(1 for p in officials if (p["office"] or "").lower() in HEAD_TITLES)
    seats = sum(1 for p in officials if p.get("district"))
    problems = []
    if len(municipalities) < MIN_MUNICIPALITIES:
        problems.append("%d municipalities < floor %d" % (len(municipalities), MIN_MUNICIPALITIES))
    if len(officials) < MIN_OFFICIALS:
        problems.append("%d officials < floor %d" % (len(officials), MIN_OFFICIALS))
    if heads < MIN_HEADS:
        problems.append("%d heads of government < floor %d" % (heads, MIN_HEADS))
    # The four ward cities (DeKalb 7, Genoa 8, Sandwich 8, Sycamore 8) are the
    # half of this payload the municipal-ward layer joins to, and a table-shape
    # change that broke only the ward rows would otherwise pass every count above.
    if seats < MIN_WARD_SEATS:
        problems.append("%d ward seats < floor %d" % (seats, MIN_WARD_SEATS))
    if problems:
        for problem in problems:
            print("  FAIL: %s" % problem, file=sys.stderr)
        print("FATAL: refusing to write a payload that lost coverage", file=sys.stderr)
        sys.exit(1)

    scraped_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for record in officials:
        record["source_url"] = source_url
        record["scraped_at"] = scraped_at
    payload = {
        "county": "DeKalb",
        "directory_url": source_url,
        "officials_page": CLERK_PAGE,
        "scraped_at": scraped_at,
        "municipalities": [{"name": n, "source_url": source_url,
                            "scraped_at": scraped_at} for n in municipalities],
        "officials": officials,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("scraped %d municipalities, %d officials (%d heads, %d ward seats) -> %s"
          % (len(municipalities), len(officials), heads, seats, args.out), file=sys.stderr)


if __name__ == "__main__":
    main()

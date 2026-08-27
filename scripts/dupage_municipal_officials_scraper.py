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
ladder (docs/EXPANSION_GUIDE.md §3.4).

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
whitespace (docs/EXPANSION_GUIDE.md §3.4, PDF-parse lessons).

The PDF's URL is date-stamped per edition
(.../2026/05/Membership-Directory-25-26-5.12.2026.pdf) and DOES change, so it
is always discovered from the membership-list page rather than hardcoded.

FETCH POSTURE (measured 2026-07-28, after the first live CI run failed): the
site sits behind Cloudflare, which serves a developer machine 200 and a GitHub
Actions runner 403 for byte-identical requests. That is an edge policy keyed on
the client's network, not a change at the source — so plain `requests` works in
development and cannot be relied on in CI, and **Playwright is the day-one
rung** wherever the runner's ranges are challenged. The ladder is
requests -> playwright -> wayback.

Each rung returns the whole directory (URL + bytes) rather than one fetch,
because the two requests are inseparable: the page must be read to discover the
edition's URL, and on a challenged edge only the session that cleared the
challenge can then fetch the PDF. The Archive rung is a real last resort but is
expected to REFUSE today — DMMC's newest snapshot was 194 days old against the
fleet's 45-day guard, and it predates the current edition, so serving it would
present last year's directory as current.

Usage:
    python3 dupage_municipal_officials_scraper.py --out dupage_municipal_officials.json
    python3 dupage_municipal_officials_scraper.py --engine playwright   # forced rung

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
from scraper_common import UA_CHROME_WIN_124  # noqa: E402  (shared machinery — do not fork)

MEMBERSHIP_URL = "https://dmmc-cog.org/membership-list/"

HEADERS = {
    "User-Agent": UA_CHROME_WIN_124,
}
REQUEST_TIMEOUT = 120

WAYBACK_API = "https://archive.org/wayback/available?url=%s"
# Same guard as the other blocked-source scrapers: an archived copy may stand in
# for a live fetch only while it is recent enough to still describe today's
# officeholders. DMMC's newest snapshot was 194 days old when this ladder was
# written, so in practice this rung refuses — that is the intended behaviour,
# not a bug. It is kept because Archive coverage can improve and because a rung
# that fails loudly is better than a missing one that fails silently.
WAYBACK_MAX_AGE_DAYS = 45

# Cloudflare answers a blocked client with either a 403 or a 200 carrying an
# interstitial; the second is the dangerous one, because it parses as a page.
BLOCK_MARKERS = ("Just a moment", "Attention Required", "cf-browser-verification",
                 "Enable JavaScript and cookies", "Checking your browser",
                 "Access denied", "You don't have permission to access")

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


def blocked(html):
    return any(marker in html for marker in BLOCK_MARKERS)


# Each rung returns (pdf_url, pdf_bytes) — the WHOLE directory, not one fetch.
# The two requests are inseparable here: the page must be read to discover the
# edition's URL, and on a challenged edge only the session that cleared the
# challenge can then fetch the PDF. Splitting them per-URL (the Kendall shape)
# would let the page come from one rung and the PDF from another, which risks
# pairing an edition's URL with a different edition's bytes.
def rung_requests():
    page = requests.get(MEMBERSHIP_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    page.raise_for_status()
    if blocked(page.text):
        raise RuntimeError("edge returned an interstitial to the requests rung")
    pdf_url = discover_pdf_url(page.text)
    body = requests.get(pdf_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    body.raise_for_status()
    if not body.content.startswith(b"%PDF"):
        raise RuntimeError("directory URL did not return a PDF")
    return pdf_url, body.content


def rung_playwright():
    """The load-bearing rung for this source.

    dmmc-cog.org sits behind Cloudflare, which 403s plain clients from
    datacenter ranges — verified 2026-07: a developer machine gets 200 and a
    GitHub Actions runner gets 403 with byte-identical headers, so this is an
    edge policy on the client, not a change at the source. A real browser
    clears the challenge, the same rung cpd_district_scraper.py already relies
    on. Both fetches share ONE context so the PDF request carries the clearance
    the page load earned.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(user_agent=HEADERS["User-Agent"])
            page = context.new_page()
            page.goto(MEMBERSHIP_URL, wait_until="domcontentloaded", timeout=90000)
            # Waiting for a PDF link rather than sleeping a fixed interval: it
            # is the actual completion signal (the interstitial carries none),
            # so it neither races a slow challenge nor pads a fast one.
            page.wait_for_selector("a[href$='.pdf']", timeout=90000)
            html = page.content()
            if blocked(html):
                raise RuntimeError("edge kept the interstitial up for the browser rung")
            pdf_url = discover_pdf_url(html)
            body = context.request.get(pdf_url, timeout=90000)
            if not body.ok:
                raise RuntimeError("browser rung got HTTP %d for the directory" % body.status)
            content = body.body()
        finally:
            browser.close()
    if not content.startswith(b"%PDF"):
        raise RuntimeError("browser rung did not receive a PDF")
    return pdf_url, content


def wayback_snapshot(url):
    """The newest archived copy of `url`, or a raised error if it is too old."""
    from datetime import datetime as dt

    resp = requests.get(WAYBACK_API % url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    snapshot = ((resp.json() or {}).get("archived_snapshots") or {}).get("closest")
    if not snapshot or not snapshot.get("available"):
        raise RuntimeError("no Archive snapshot available for %s" % url)
    taken = dt.strptime(snapshot.get("timestamp") or "", "%Y%m%d%H%M%S").replace(
        tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - taken).days
    if age_days > WAYBACK_MAX_AGE_DAYS:
        raise RuntimeError("newest snapshot of %s is %d days old (max %d) — refusing to "
                           "serve stale data as current" % (url, age_days, WAYBACK_MAX_AGE_DAYS))
    archived = requests.get(snapshot["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
    archived.raise_for_status()
    return archived


def rung_wayback():
    page = wayback_snapshot(MEMBERSHIP_URL)
    pdf_url = discover_pdf_url(page.text)
    body = wayback_snapshot(pdf_url)
    if not body.content.startswith(b"%PDF"):
        raise RuntimeError("archived copy is not a PDF")
    return pdf_url, body.content


def obtain_directory(engine):
    rungs = {"requests": [rung_requests], "playwright": [rung_playwright],
             "wayback": [rung_wayback]}.get(
                 engine, [rung_requests, rung_playwright, rung_wayback])
    last = None
    for rung in rungs:
        try:
            return rung()
        except Exception as exc:  # noqa: BLE001 - every rung failure escalates
            last = exc
            print("%s failed (%s)" % (rung.__name__, exc), file=sys.stderr)
    print("FATAL: every fetch rung failed for %s — last error: %s"
          % (MEMBERSHIP_URL, last), file=sys.stderr)
    sys.exit(1)


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
    parser.add_argument("--engine", choices=("auto", "requests", "playwright", "wayback"),
                        default="auto",
                        help="fetch rung; auto walks requests -> playwright -> wayback")
    args = parser.parse_args()

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.pdf:
        pdf_url = MEMBERSHIP_URL
        with open(args.pdf, "rb") as f:
            body = f.read()
    else:
        pdf_url, body = obtain_directory(args.engine)

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

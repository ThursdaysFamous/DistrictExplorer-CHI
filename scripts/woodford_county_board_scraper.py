#!/usr/bin/env python3
"""
Scrape Woodford County's own board directory into raw roster records.

Stage 1 of the two-stage pipeline (scripts/build_woodford_board_roster.py is
stage 2), mirroring the LaSalle pair. The county's CivicPlus staff directory
(Directory.aspx?DID=22) is plain server-rendered HTML that answers a plain
requests client. The county board is FIFTEEN members, five elected at large
from each of THREE districts (Ordinance 2020/21 #005) — the directory groups
the member tables under DirectoryCategoryText headers reading "District 1/2/3",
so the district comes from the SECTION a row sits in, not from the row's title
(every title is the bare "County Board Member").

Each row carries the member's name link (/directory.aspx?EID=n), a phone with
a full 10-digit number, and an e-mail whose CivicPlus spam-wrapper script
carries the address VERBATIM in its own source (var w = "twilcoxen";
var x = "woodfordcountyil.gov") — read, not de-obfuscated, the same call as
LaSalle's. The 2026-07-31 validation pass recorded phones 15/15; the e-mails
turned out to be published too.

NO CHAIRMAN IS EMITTED: the chair is elected every two years from within the
body and the directory does not mark who holds it, so marking one would be a
guess. The card renders fifteen members by district and links the directory.

Usage:
    python3 woodford_county_board_scraper.py [output.json]   # default: stdout
"""

import json
import re
import sys

import requests

BASE = "https://www.woodford-county.org"
LIST_URL = BASE + "/Directory.aspx?DID=22"
UA = {"User-Agent": "Mozilla/5.0 (compatible; districtexplorer-roster/1.0)"}

DISTRICT_HEADER_RE = re.compile(
    r"class='DirectoryCategoryText'><span[^>]*>\s*District\s+(\d+)\s*</span>")
ROW_RE = re.compile(
    r'href="/directory\.aspx\?EID=(?P<eid>\d+)">(?P<name>[^<]+)</a>\s*</span>'
    r'.*?<span>(?P<title>[^<]*County Board Member[^<]*)</span>'
    r'(?P<rest>.*?)</tr>',
    re.S | re.I,
)
EMAIL_RE = re.compile(r'var w = "([^"]+)";\s*var x = "([^"]+)";')
PHONE_RE = re.compile(r'\(?(\d{3})\)?[.\- ](\d{3})[.\- ](\d{4})')


def fetch(url):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r.text


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def display_name(directory_name):
    """'Wilcoxen, Timothy' -> 'Timothy Wilcoxen' (the card renders given-name-first)."""
    parts = [p.strip() for p in directory_name.split(",", 1)]
    if len(parts) == 2 and parts[1]:
        return "%s %s" % (parts[1], parts[0])
    return directory_name.strip()


def main():
    html = fetch(LIST_URL)

    # Slice the page into district sections; each row inherits its section.
    sections = []
    headers = list(DISTRICT_HEADER_RE.finditer(html))
    if not headers:
        print("woodford-board-scraper: FAIL — no 'District N' section headers on %s "
              "(markup change?)" % LIST_URL, file=sys.stderr)
        sys.exit(1)
    for i, h in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(html)
        sections.append((int(h.group(1)), html[h.start():end]))

    records = []
    for district, segment in sections:
        for m in ROW_RE.finditer(segment):
            name = clean(m.group("name"))
            if not name:
                continue
            rest = m.group("rest") or ""
            email = None
            em = EMAIL_RE.search(rest)
            if em:
                email = "%s@%s" % (em.group(1), em.group(2))
            phone = None
            pm = PHONE_RE.search(re.sub(r"<[^>]+>", " ", rest))
            if pm:
                phone = "%s-%s-%s" % pm.groups()
            records.append({
                "name": display_name(name),
                "district": district,
                "phone": phone,
                "email": email,
                "url": BASE + "/directory.aspx?EID=" + m.group("eid"),
            })

    if not records:
        print("woodford-board-scraper: FAIL — zero rows parsed from %s (markup change?)"
              % LIST_URL, file=sys.stderr)
        sys.exit(1)

    out = json.dumps({"source": LIST_URL, "records": records}, indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(out)
        print("woodford-board-scraper: %d records -> %s" % (len(records), sys.argv[1]))
    else:
        print(out)


if __name__ == "__main__":
    main()

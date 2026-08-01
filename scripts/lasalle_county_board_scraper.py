#!/usr/bin/env python3
"""
Scrape LaSalle County's own board directory into raw roster records.

Stage 1 of the two-stage pipeline (scripts/build_lasalle_board_roster.py is
stage 2), mirroring the DuPage pair. The county's CivicPlus staff directory
(Directory.aspx?DID=39) is plain server-rendered HTML that answers a plain
requests client — no challenge, no JS rendering needed for the DATA: each row
is a <tr> carrying the member's name link (/directory.aspx?EID=n), a title
cell ("District N, Board Member" / "Chairman of the Board"), a phone cell with
a full 10-digit number, and an e-mail cell whose CivicPlus spam-wrapper script
carries the address VERBATIM in its own source (var w = "district22";
var x = "lasallecountyil.gov") — read, not de-obfuscated, the same call as
Winnebago's base64 Joomla wrapper. The e-mails are district-office addresses
(district<N>@lasallecountyil.gov), not personal inboxes.

WHY THIS SCRAPER EXISTS — the county's board-boundary GIS is the SUPERSEDED
2011-2021 map, frozen 2015-08-25, and its officeholder columns disagree with
this directory on 18 of 29 seats (the 2026-07-31 validation-pass finding). The
directory is the county's roster of record for the 2022-2031 board; the
boundary comes separately from scripts/build_lasalle_board_districts.py.

The Board Chairman is elected COUNTYWIDE (verified: the Nov 2024 general
canvass carries a county-wide COUNTY BOARD CHAIRMAN contest) and is emitted
with district=null, role="Chair". A "(Vice Chairman)" tag beside a member's
name is carried as role="Vice Chair" on that member's own district row.

Usage:
    python3 lasalle_county_board_scraper.py [output.json]   # default: stdout
"""

import json
import re
import sys

import requests

BASE = "https://lasallecountyil.gov"
LIST_URL = BASE + "/Directory.aspx?DID=39"
UA = {"User-Agent": "Mozilla/5.0 (compatible; districtexplorer-roster/1.0)"}

ROW_RE = re.compile(
    r'href="/directory\.aspx\?EID=(?P<eid>\d+)">(?P<name>[^<]+)</a>\s*</span>'
    r'(?:\s*<span>\s*\((?P<tag>[^)]+)\)\s*</span>)?'
    r'.*?<span>(?P<title>[^<]*(?:Board Member|Chairman of the Board)[^<]*)</span>'
    r'(?P<rest>.*?)</tr>',
    re.S | re.I,
)
EMAIL_RE = re.compile(r'var w = "([^"]+)";\s*var x = "([^"]+)";')
PHONE_RE = re.compile(r'(\d{3})[.\- ](\d{3})[.\- ](\d{4})')
DISTRICT_RE = re.compile(r'District\s+(\d+)', re.I)


def fetch(url):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r.text


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def display_name(directory_name):
    """'Aubry, Stephen' -> 'Stephen Aubry' (the card renders given-name-first)."""
    parts = [p.strip() for p in directory_name.split(",", 1)]
    if len(parts) == 2 and parts[1]:
        return "%s %s" % (parts[1], parts[0])
    return directory_name.strip()


def main():
    html = fetch(LIST_URL)
    records = []
    for m in ROW_RE.finditer(html):
        name = clean(m.group("name"))
        if not name:
            continue
        title = clean(m.group("title"))
        rest = m.group("rest") or ""
        district = None
        role = "Member"
        if "chairman of the board" in title.lower():
            role = "Chair"
        else:
            dm = DISTRICT_RE.search(title)
            if not dm:
                continue  # a staff row that merely mentions the board
            district = int(dm.group(1))
        tag = clean(m.group("tag") or "")
        if role == "Member" and "vice" in tag.lower():
            role = "Vice Chair"
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
            "role": role,
            "phone": phone,
            "email": email,
            "url": BASE + "/directory.aspx?EID=" + m.group("eid"),
        })

    if not records:
        print("lasalle-board-scraper: FAIL — zero rows parsed from %s (markup change?)"
              % LIST_URL, file=sys.stderr)
        sys.exit(1)

    out = json.dumps({"source": LIST_URL, "records": records}, indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(out)
        print("lasalle-board-scraper: %d records -> %s" % (len(records), sys.argv[1]))
    else:
        print(out)


if __name__ == "__main__":
    main()

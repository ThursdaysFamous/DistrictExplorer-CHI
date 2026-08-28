#!/usr/bin/env python3
"""
Fetch Iowa's 99 county auditors from the Iowa State Association of County
Auditors' own directory (iowaauditors.org), and cache the result for
build_ia_county_auditors.py.

WHY THIS PAGE
-------------
Iowa Code 47.2 designates the county auditor as each county's own election
commissioner. There is no statewide roster published by the Secretary of
State's office in a form this project can read (sos.iowa.gov/auditors links
out to each county's own page rather than listing names itself), but the
auditors' own trade association (https://iowaauditors.org/find/directory/)
publishes one entry per county on a single page — server-rendered, no
JavaScript required — carrying the auditor's name, party (as a Font Awesome
icon class, not text — verified 2026-08-28: `fa-republican` / `fa-democrat`,
present on 94 of 99 entries; the other 5 carry no party icon at all, and this
scraper ships those rows with party omitted rather than guessing), the office
name and mailing address, and a phone number. No e-mail is published anywhere
on the page.

Each entry's county name (the <h2> link text, e.g. "Black Hawk", "O'Brien")
matches ia/data/app/state-counties.json's BASENAME field exactly for all 99
counties (verified 2026-08-28) — no alias table needed for the join.

Usage:
    python3 ia/scripts/ia_county_auditor_scraper.py
"""

import json
import os
import re
import sys

import requests

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
OUT_PATH = os.path.join(CACHE_DIR, "ia_county_auditors.json")

DIRECTORY_URL = "https://iowaauditors.org/find/directory/"
HEADERS = {"User-Agent": "districtry/1.0 (+https://districtry.com/ia/)"}

EXPECT_COUNTIES = 99

LISTING_RE = re.compile(r'<div class="auditorListing"')
COUNTY_NAME_RE = re.compile(r'<h2><a href="/[^"]+/">([^<]+)</a></h2>')
NAME_PARTY_RE = re.compile(
    r'<div class="contentDetails">\s*<b>\s*([^<]+?)\s*(?:<i class="f[a-z]{2} (fa-[a-z\-]+)"[^>]*></i>)?\s*</b>',
    re.IGNORECASE,
)
OFFICE_RE = re.compile(
    r'fa-map-marker-alt.*?<div class="contentDetails">\s*<b>([^<]+)</b><br>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
PHONE_RE = re.compile(
    r'fa-phone.*?<div class="contentDetails"><b>Phone</b><br>([^<]+)</div>',
    re.IGNORECASE | re.DOTALL,
)

PARTY_LABELS = {"fa-republican": "Republican", "fa-democrat": "Democratic"}


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def split_listings(html):
    starts = [m.start() for m in LISTING_RE.finditer(html)]
    if not starts:
        raise RuntimeError("no auditorListing blocks found on %s" % DIRECTORY_URL)
    starts.append(len(html))
    # back up each start to the enclosing <div ...> so the block is self-contained
    blocks = []
    for i in range(len(starts) - 1):
        div_start = html.rfind("<div", 0, starts[i] + 1)
        blocks.append(html[div_start:starts[i + 1]])
    return blocks


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_address(raw):
    # e.g. "400 Public Square<br>Suite 5<br>        Greenfield, IA 50849  "
    lines = [clean(x) for x in raw.split("<br>")]
    return [x for x in lines if x]


def parse_block(block):
    cm = COUNTY_NAME_RE.search(block)
    if not cm:
        raise RuntimeError("a listing block has no county name: %r" % block[:200])
    county = cm.group(1).strip()

    nm = NAME_PARTY_RE.search(block)
    if not nm:
        raise RuntimeError("%s: no auditor name found" % county)
    name = clean(nm.group(1))
    party_class = nm.group(2)
    party = PARTY_LABELS.get(party_class) if party_class else None

    om = OFFICE_RE.search(block)
    office = clean(om.group(1)) if om else None
    address = parse_address(om.group(2)) if om else []

    pm = PHONE_RE.search(block)
    phone = clean(pm.group(1)) if pm else None

    return {
        "county": county,
        "name": name,
        "party": party,
        "office": office,
        "address": address,
        "phone": phone,
    }


def main():
    html = fetch(DIRECTORY_URL)
    blocks = split_listings(html)
    if len(blocks) != EXPECT_COUNTIES:
        raise RuntimeError(
            "iowaauditors.org listed %d auditorListing blocks, expected %d"
            % (len(blocks), EXPECT_COUNTIES)
        )

    records = [parse_block(b) for b in blocks]

    no_phone = [r["county"] for r in records if not r["phone"]]
    if no_phone:
        raise RuntimeError("%d counties carried no phone number: %s" % (len(no_phone), no_phone))
    no_address = [r["county"] for r in records if not r["address"]]
    if no_address:
        raise RuntimeError("%d counties carried no office address: %s" % (len(no_address), no_address))
    no_party = [r["county"] for r in records if not r["party"]]
    print(
        "iowaauditors.org: %d counties, %d with a party icon, %d without (%s)"
        % (len(records), len(records) - len(no_party), len(no_party), no_party),
        file=sys.stderr,
    )

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(records, f, indent=1)
    print("wrote %d county auditor records -> %s" % (len(records), OUT_PATH), file=sys.stderr)


if __name__ == "__main__":
    main()

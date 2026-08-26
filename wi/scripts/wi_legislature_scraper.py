#!/usr/bin/env python3
"""
Scrape the Wisconsin Legislature's own per-chamber pages for the office
fields Open States cannot supply. Companion to build_wi_legislature_roster.py,
which merges this enrichment onto its Open States base.

WHY THIS EXISTS (measured 2026-08-25): the Open States wi.csv carries
capitol_address / capitol_voice filled for 0 of 132 Wisconsin members — the
upstream YAML has no offices block for them — while the Legislature's own
index pages (docs.legis.wisconsin.gov/2025/legislators/{assembly,senate})
carry every member in a district-id-keyed block with the Madison office room,
one or two telephones, fax and e-mail. Two fetches cover all 132.

THE URL IS SESSION-SCOPED AND THE UNVERSIONED PATH 404s: /2025/ is the
2025-26 biennium, and the path must be bumped each odd-year January
(WATCH.md row) or this scraper silently reads a frozen roster. The floors
below are the tripwire for a page reshape; the biennium bump is a calendar
fact no floor can catch.

TWO FIELDS ARE REFUSED BY CONSTRUCTION, not filtered afterwards: each block
carries the member's **Voting Address** — their HOME address — and their
staff's names and mailboxes. Neither is read; the parser walks only the
Madison Office / Telephone / Fax / Email spans, and the builder asserts on
the merged payload that no voting-address line survived (the fleet's
Boone/Mason rule: refuse residences structurally, then prove it).
"""

import json
import os
import re
import ssl
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, ".cache", "wi_legislature_offices.json")

BIENNIUM = "2025"  # bump each odd-year January — see WATCH.md
BASE = "https://docs.legis.wisconsin.gov/%s/legislators/" % BIENNIUM
CHAMBERS = {"senate": 31, "assembly": 94}  # min district blocks (floors match the builder's)

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


def fetch(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def span_lines(block, cls):
    m = re.search(r"<span class='info %s'>.*?</span>\s*(.*?)</span>" % cls, block, re.S)
    if not m:
        return []
    return [strip_tags(x) for x in re.split(r"<br\s*/?>", m.group(1)) if strip_tags(x)]


def parse_chamber(html):
    out = {}
    blocks = re.split(r'id="district(\d+)"', html)
    for i in range(1, len(blocks) - 1, 2):
        district = str(int(blocks[i]))
        body = blocks[i + 1]
        entry = {}
        m = re.search(r'<strong><a href="(http[^"]+)">', body)
        if m:
            entry["url"] = m.group(1)
        office = span_lines(body, "office")
        if office:
            entry["capitolOffice"] = office
        phones = span_lines(body, "telephone")
        if phones:
            entry["phones"] = phones
        fax = span_lines(body, "fax")
        if fax:
            entry["fax"] = fax[0]
        m = re.search(r'<span class=\'info email\'>.*?mailto:([^"]+)"', body, re.S)
        if m:
            entry["email"] = m.group(1)
        out[district] = entry
    return out


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT

    payload = {}
    for chamber, floor in CHAMBERS.items():
        parsed = parse_chamber(fetch(BASE + chamber))
        if len(parsed) < floor:
            raise SystemExit("%s page yielded %d district blocks (floor %d) — the page "
                             "reshaped, or the biennium constant needs its bump"
                             % (chamber, len(parsed), floor))
        with_email = sum(1 for e in parsed.values() if e.get("email"))
        if with_email < floor - 3:
            raise SystemExit("%s page yielded only %d e-mails over %d blocks — the "
                             "mailto pattern moved" % (chamber, with_email, len(parsed)))
        payload[chamber] = parsed

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("scraped offices: senate %d, assembly %d -> %s"
          % (len(payload["senate"]), len(payload["assembly"]), out_path))


if __name__ == "__main__":
    main()

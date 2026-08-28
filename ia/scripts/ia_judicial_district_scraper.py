#!/usr/bin/env python3
"""
Scrape stage 1: fetch each of Iowa's 8 judicial districts' own "Judges and
Magistrates" roster page from iowacourts.gov and write the raw name/role
pairs to .cache/ia_judicial_district_judges.json for
build_ia_judicial_district_roster.py (stage 2) to join against the shipped
geometry's district numbers.

THREE DIFFERENT URL SHAPES, verified live 2026-08-28, one hardcoded per
district rather than derived from a single pattern:
    District 1:      .../judicial-district-1/judges-and-magistrates-district-1/  (number SUFFIX)
    Districts 2-7:    .../judicial-district-N/judges-and-magistrates/            (bare)
    District 8:       .../judicial-district-8/district-8-judges-and-magistrates/ (number PREFIX)

iowacourts.gov returns HTTP 403 to at least one common automated-client
signature; a plain browser User-Agent is required (verified: curl with one
gets 200, without one gets 403 from this same sandbox).

THE TITLE FIELD IS NOT SPLIT INTO RANK + SUB-DISTRICT. Sampled across all 8
districts (2026-08-28), the CMS punctuates it at least four different ways
with no consistent separator:
    "Chief Judge: District 1B"            (colon)
    "District court Judge; District 3A"   (semicolon, lowercase "court")
    "District Court Judge D5"             (no punctuation at all)
    "Senior Judge District 2A"            (no punctuation at all)
    "Magisrate"                           (a genuine misspelling in the source)
Guessing a split rule risks mis-parsing some of these into a wrong rank or a
wrong sub-district; shipping the whole string verbatim (HTML-entity-decoded,
whitespace-collapsed) as one field is the honest choice and the fleet's own
convention (never invent structure the source doesn't clearly state). A
sub-district or county named in the title (e.g. "District 1B", "Cedar
County") is informational only — this layer's own district is the whole
NUMBERED district a judge's page sits under, never the sub-division.

Markup (identical shape across all 8 districts, confirmed by direct fetch):
    <div class="cms_list_item">
      ...
      <h2 class="title_header">David P. Odekirk</h2>
      <div class="cms_metadata2 cms_title" ...>Chief Judge&#x3a; District 1B</div>
      ...
    </div>

Floors (refuses to write otherwise): all 8 districts present; >= 250 judges
total (measured 2026-08-28: District totals ranged 31-77, ~360 statewide);
every district has at least one judge.

Usage:
    python3 ia/scripts/ia_judicial_district_scraper.py
"""

import json
import html
import os
import re
import sys
import time

try:
    import requests
except ImportError:
    print("FATAL: pip install -r ia/scripts/requirements.txt", file=sys.stderr)
    sys.exit(1)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
OUT_FILE = os.path.join(CACHE_DIR, "ia_judicial_district_judges.json")

BASE = "https://www.iowacourts.gov/iowa-courts/district-court"
DISTRICT_URLS = {
    1: BASE + "/judicial-district-1/judges-and-magistrates-district-1/",
    2: BASE + "/judicial-district-2/judges-and-magistrates/",
    3: BASE + "/judicial-district-3/judges-and-magistrates/",
    4: BASE + "/judicial-district-4/judges-and-magistrates/",
    5: BASE + "/judicial-district-5/judges-and-magistrates/",
    6: BASE + "/judicial-district-6/judges-and-magistrates/",
    7: BASE + "/judicial-district-7/judges-and-magistrates/",
    8: BASE + "/judicial-district-8/district-8-judges-and-magistrates/",
}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
}
REQUEST_TIMEOUT = 60
MIN_TOTAL_JUDGES = 250

ITEM_RE = re.compile(
    r'<h2 class="title_header">([^<]*)</h2>\s*'
    r'<div class="cms_metadata2 cms_title"[^>]*>([^<]*)</div>',
    re.S)


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def fetch_district(dist, url):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    matches = ITEM_RE.findall(resp.text)
    judges = []
    for raw_name, raw_role in matches:
        name = clean(raw_name)
        role = clean(raw_role)
        if not name:
            continue
        judges.append({"name": name, "role": role})
    if not judges:
        raise SystemExit("district %d: parsed zero judges from %s -- markup changed?"
                          % (dist, url))
    return judges


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    out = {}
    total = 0
    for dist in sorted(DISTRICT_URLS):
        url = DISTRICT_URLS[dist]
        judges = fetch_district(dist, url)
        out[str(dist)] = {"url": url, "judges": judges}
        total += len(judges)
        print("district %d: %d judges (%s)" % (dist, len(judges), url), file=sys.stderr)
        time.sleep(1)  # a light touch across 8 sequential fetches to one host

    if len(out) != 8:
        raise SystemExit("scraped %d districts, expected 8" % len(out))
    if total < MIN_TOTAL_JUDGES:
        raise SystemExit("only %d judges total (floor %d)" % (total, MIN_TOTAL_JUDGES))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    print("wrote %s -- %d districts, %d judges" % (OUT_FILE, len(out), total), file=sys.stderr)


if __name__ == "__main__":
    main()

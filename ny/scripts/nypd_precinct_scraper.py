#!/usr/bin/env python3
"""
Scrape each NYPD precinct's commanding officer from its nyc.gov precinct page
(METRO_EXPANSION_PLAYBOOK §9). Stage 1 of the pipeline: the precinct list is
driven from the Socrata precinct boundary dataset (y76i-bdw7) — NYPD's precinct
numbers are irregular, so never loop 1..N — and each precinct's ordinal page
(…/precincts/{Nth}-precinct.page) yields the "Commanding Officer:" line.

Writes an intermediate JSON with source_url + scraped_at per record; the CO name
is the only field taken here (the precinct card already gets station address/phone
from FacDB). A page that WAF-blocks or omits the label yields a null commander —
never guessed. build_nypd_roster.py resolves this into data/app/nypd-precinct-info.json.

Usage:
    python3 scripts/nypd_precinct_scraper.py [--out PATH] [--limit N]
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SOCRATA = "https://data.cityofnewyork.us/resource/y76i-bdw7.json?$select=precinct&$limit=1000"
PAGE = "https://www.nyc.gov/site/nypd/bureaus/patrol/precincts/{ord}-precinct.page"
UA = "Mozilla/5.0 (compatible; NYCDistrictExplorer/1.0; +https://nyc.chidistricts.com)"
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), ".cache", "nypd_precincts_raw.json")


def ordinal(n):
    n = int(n)
    v = n % 100
    suffix = "th" if 11 <= v <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suffix)


def _get(url, timeout=45):
    headers = {"User-Agent": UA, "Accept": "text/html,application/json"}
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token and "data.cityofnewyork.us" in url:
        headers["X-App-Token"] = token
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def precinct_numbers():
    rows = json.loads(_get(SOCRATA))
    nums = sorted({int(r["precinct"]) for r in rows if r.get("precinct") not in (None, "")})
    return nums


def commander_from_html(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    m = re.search(r"Commanding Officer:\s*(.+?)\s+(?:The\s+\d|This\s+precinct|\bThe\b\s+[A-Z]\w+\s+Precinct)", text)
    if not m:
        m = re.search(r"Commanding Officer:\s*([A-Z][A-Za-z.\-' ]{4,60}?)(?:\s{2,}|$)", text)
    if not m:
        return None
    name = m.group(1).strip(" .")
    # sanity: a rank + name, not a stray sentence
    return name if 4 <= len(name) <= 60 else None


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    nums = precinct_numbers()
    if limit:
        nums = nums[:limit]
    scraped_at = os.environ.get("SCRAPED_AT") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    records = {}
    found = 0
    for n in nums:
        url = PAGE.format(ord=ordinal(n))
        commander = None
        try:
            commander = commander_from_html(_get(url))
        except urllib.error.HTTPError as e:
            commander = None  # 404/403 -> no CO for this precinct, never guessed
        except Exception:
            commander = None
        if commander:
            found += 1
        records[str(n)] = {"commander": commander, "source_url": url, "scraped_at": scraped_at}
        time.sleep(0.3)  # courteous to nyc.gov

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"precincts": records}, f, indent=2, ensure_ascii=False)
    print("wrote %s: %d precincts, %d with a commander" % (out_path, len(records), found), file=sys.stderr)


if __name__ == "__main__":
    main()

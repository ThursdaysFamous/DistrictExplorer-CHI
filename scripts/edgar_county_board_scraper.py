#!/usr/bin/env python3
"""
Stage 1 of the Edgar County Board roster pipeline: scrape the county's own
board page into raw JSON for build_edgar_county_board.py, and RE-READ the
district composition out of the Clerk's live results feed in the same run.

TWO SOURCES, TWO JOBS — the Crawford shape. The people come from
edgarcountyillinois.COM, which publishes the board as seven one-line entries,
"District #3: Andy Patrick (R)". READ THAT DOMAIN TWICE: the county also runs
edgarcountyillinois.GOV, and the .gov does not carry the board page — it links
across to the .com for it. This is the Morgan trap in a milder form, and the
URL below is the one that has the roster.

The DISTRICTS come from il-edgar.pollresults.net, the Clerk's own results
system, whose certified result set is embedded in the page as JSON. That is
one of the three documents the shipped boundaries' composition was proven from
(build_edgar_boundaries.py), and re-reading it weekly is the re-precincting /
redistricting tripwire.

WHY THE PAGE IS THE ROSTER AND THE RETURNS ARE THE GEOMETRY — this county
makes the case better than any so far. The 2022 and 2024 canvasses elected
PHILLIP R. LUDINGTON in District 6. The county's board page names SAMANTHA
McCARTY there, and the Clerk's own 2026 primary confirms it by carrying a "6TH
DISTRICT MEMBER 2-YEAR UNEXPIRED TERM" contest — a seat filled mid-term, which
no canvass of a completed term could ever show. A roster taken from the
returns alone would name the wrong person for District 6 today.

WHAT THE BOARD PAGE PUBLISHES, and what it does not: name, district and party
for all seven. No e-mail, no phone, no term, and NO BOARD CHAIRMAN — the
committees table beneath the roster has a CHAIRMAN column, but that is the
chair OF EACH COMMITTEE and reading it as the board's chair would be a
fabrication. None of those ship.

Usage:
    python3 scripts/edgar_county_board_scraper.py [-o raw.json]
"""

import argparse
import html
import json
import re
import sys

import requests

BOARD_URL = "https://edgarcountyillinois.com/county-board/"
RESULTS_URL = "https://il-edgar.pollresults.net/"
TIMEOUT = 60
HEADERS = {"User-Agent": "chidistricts.com roster bot (civic data; contact via site)"}

# One member per line: "<strong>District #3: </strong>Andy Patrick (R)".
MEMBER_RE = re.compile(
    r"District\s*#?\s*(\d+)\s*:?\s*</strong>\s*([^<(]+?)\s*\((R|D|I|G|L)\)",
    re.I)
# A street address would carry a number then a street word. The page prints
# bare names today; this is the tripwire if that ever changes, because home
# addresses never ship (the Madison/Peoria rule).
STREET_RE = re.compile(
    r"\d+\s+\w+\s+(st|street|ave|avenue|rd|road|dr|drive|ln|lane|ct|court|blvd|hwy)\b",
    re.I)


from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

fail = make_fail("edgar-board-scraper")


def get(url):
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def clean(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def scrape_members(page):
    records = []
    seen = set()
    for match in MEMBER_RE.finditer(page):
        district, name, party = match.group(1), clean(match.group(2)), match.group(3).upper()
        if not name or district in seen:
            continue
        if STREET_RE.search(name):
            fail("the board page now prints what looks like a street address (%r) — "
                 "home addresses never ship; tighten this parser rather than the "
                 "rule" % name)
        seen.add(district)
        records.append({"name": name, "district": district, "party": party})
    records.sort(key=lambda r: int(r["district"]))
    return records


def scrape_composition(page):
    """{district: [precinct, ...]} from the certified result set embedded in
    the Clerk's live results page."""
    match = re.search(r"var electionData = (\{.*?\});\s*\n", page, re.S)
    if not match:
        fail("the Clerk's results page no longer embeds its result set as JSON — "
             "the composition check cannot run, and it is this county's only "
             "automatic redistricting warning")
    data = json.loads(match.group(1))
    election = data.get("Election") or {}
    out = {}
    for race in data.get("Races") or []:
        name = (race.get("RaceName") or "").upper()
        if "COUNTY BOARD" not in name:
            continue
        hit = re.search(r"BOARD (\d+)(?:ST|ND|RD|TH) DISTRICT", name)
        if not hit:
            continue
        precincts = ([p["PrecinctName"] for p in race.get("Reporting") or []] +
                     [p["PrecinctName"] for p in race.get("NotReporting") or []])
        out.setdefault(hit.group(1), set()).update(precincts)
    return ({d: sorted(v) for d, v in out.items()},
            {"description": election.get("Description"),
             "date": (election.get("ElectionDate") or "")[:10],
             "officeTitle": election.get("OfficeTitle")})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", help="write raw JSON here (default: stdout)")
    args = ap.parse_args()

    members = scrape_members(get(BOARD_URL))
    composition, election = scrape_composition(get(RESULTS_URL))
    payload = {"source": BOARD_URL, "resultsUrl": RESULTS_URL,
               "election": election, "composition": composition,
               "records": members}
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        print("edgar-board-scraper: %d member(s), %d district(s) re-read from the "
              "%s -> %s" % (len(members), len(composition),
                            election.get("description"), args.output), file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()

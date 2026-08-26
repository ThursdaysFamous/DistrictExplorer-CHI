#!/usr/bin/env python3
"""
Build data/app/wi-county-clerks.json from the two-source clerk scrape — stage
2 of the pair (wi_county_clerk_scraper.py is stage 1, which already
cross-gated the Blue Book against the clerks' own association and recorded
any name divergence).

Keyed by county GEOID (the same GEOID the county card reads off its TIGERweb
feature), so the join cannot drift from the geometry. Party renders as the
Blue Book's legend spells it — A-Appointed; D-Democrat; I-Independent;
R-Republican — with APPOINTED carried as its own flag, never as a party: the
honesty rules require an appointed officer labeled as appointed.

THE MILWAUKEE EXCEPTION IS STATUTE, NOT DATA: Wis. Stat. 7.20(1) vests
election duties in counties over 750,000 — Milwaukee alone — in an APPOINTED
county Election Commission, so Milwaukee's entry carries an electionNote +
electionUrl the card renders beside its clerk (who exists and holds the
office's other duties). Both commission member rosters live behind hosts that
refuse automation (measured), so the card links the body and names nobody.

Floors: exactly 72 keys; every county named; >= 65 with a phone; >= 60 with
an e-mail; the divergence list printed on every run so a stale Blue Book
name is a visible fact, not a silent choice.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "wi_county_clerks_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "wi-county-clerks.json")

PARTY = {"D": "Democrat", "R": "Republican", "I": "Independent"}
MILWAUKEE_GEOID = "55079"
MILWAUKEE_NOTE = ("Elections in Milwaukee County are run by the appointed county "
                  "Election Commission, not the county clerk (Wis. Stat. 7.20).")
MILWAUKEE_URL = "https://county.milwaukee.gov/EN/Election-Commission"


def main():
    raw_path = sys.argv[sys.argv.index("--in") + 1] if "--in" in sys.argv else RAW
    with open(raw_path) as f:
        raw = json.load(f)

    counties = raw["counties"]
    if len(counties) != 72:
        raise SystemExit("scrape carries %d counties, expected 72" % len(counties))

    out = {}
    phones = emails = 0
    for geoid, c in counties.items():
        if not c.get("name"):
            raise SystemExit("county %s has no clerk name" % c.get("county"))
        entry = {
            "county": c["county"],
            "name": c["name"],
            "address": c.get("address") or [],
            "sourceUrl": c["sourceUrl"],
        }
        code = c.get("code")
        if code == "A":
            entry["appointed"] = True
        elif code in PARTY:
            entry["party"] = PARTY[code]
        for field in ("phone", "fax", "email", "hours", "website"):
            if c.get(field):
                entry[field] = c[field]
        phones += 1 if entry.get("phone") else 0
        emails += 1 if entry.get("email") else 0
        if geoid == MILWAUKEE_GEOID:
            entry["electionNote"] = MILWAUKEE_NOTE
            entry["electionUrl"] = MILWAUKEE_URL
        out[geoid] = entry

    if phones < 65:
        raise SystemExit("only %d clerks carry a phone (floor 65) — the page shape moved" % phones)
    if emails < 60:
        raise SystemExit("only %d clerks carry an e-mail (floor 60)" % emails)
    if "electionNote" not in out[MILWAUKEE_GEOID]:
        raise SystemExit("Milwaukee's election-commission note went missing")

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    div = raw.get("divergences") or []
    print("wrote %s — 72 clerks (%d phones, %d e-mails); Blue Book name divergences: %s"
          % (OUT, phones, emails,
             ", ".join("%(county)s (%(blueBook)s -> %(association)s)" % d for d in div) or "none"))


if __name__ == "__main__":
    main()

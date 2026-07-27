#!/usr/bin/env python3
"""
Suburban Cook County Municipal Officials Scraper (County Clerk DOEO API)
=======================================================================
Extracts every suburban Cook municipality's governing body — village
president / mayor, trustees, ward alderpersons, clerk, treasurer — from the
Cook County Clerk's own Directory of Elected Officials.

Why this source: the Clerk's DOEO web app
(cookcountyclerkil.gov/elections/directory-elected-officials) is backed by an
open, unauthenticated JSON API on the same domain, which is the county's
canonical record of who currently holds each local office. It is the only
verified source covering ALL suburban Cook municipalities with full governing
bodies (not just the mayor) plus office contact — Chicago's own council is
the app's separate `ward` layer, and the county's Socrata copies of this
directory (vw2r-zys4 / jsup-zs8y) have been frozen since 2014, so they are
deliberately NOT used.

Three endpoints, two of them bulk:
  /api/Jurisdiction/GetByJurisdictionType?id=MUNIS      -> the 128 municipalities
  /api/ElectedOfficial/GetByJurisdictionType?id=MUNIS   -> municipality-wide officers
  /api/ElectedOfficial/GetByJurisdictionType?id=MUNIW   -> ward/district seats
MUNIW's `Jurisdiction` carries the seat's district inline ("City of Berwyn,
Ward 1"), which is parsed out here so the ward-boundary layer can join later
without a re-scrape.

Library Trustees are excluded: they sit on library district boards (the app's
separate `library-district` layer), not the municipal governing body. They are
distinguishable structurally as well as by office name — their sole address
carries AddressTypeId 4 (library) rather than 3 (village/city hall).

The site is Cloudflare-fronted. Plain requests with a browser User-Agent is
the verified-working rung (2026-07); --engine playwright is available if that
tightens, matching the ladder in cpd_district_scraper.py.

This is the build-time half of the usual two-stage roster pattern; the raw
output is resolved into data/app/municipal-officials.json by
scripts/build_municipal_officials_roster.py.

Usage:
    python3 cook_municipal_officials_scraper.py --out cook_municipal_officials.json

Notes on data honesty (per project conventions):
- Fields that can't be parsed are stored as null, never guessed.
- Every record includes `source_url` and `scraped_at` for traceability.
- Contact fields (phone/email/address/website) are MUNICIPALITY-level in this
  source — every official of a municipality carries the same village-hall
  values, and the per-person PersonPhone/PersonEmail columns are empty for all
  1,134 records. They are emitted under the municipality, never as a person's
  own contact, so the card cannot imply a direct line that does not exist.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone

import requests

BASE = "https://www.cookcountyclerkil.gov/api"
JURISDICTIONS_URL = BASE + "/Jurisdiction/GetByJurisdictionType?id=MUNIS&language=en"
OFFICIALS_URL = BASE + "/ElectedOfficial/GetByJurisdictionType?id=MUNIS&language=en"
WARD_OFFICIALS_URL = BASE + "/ElectedOfficial/GetByJurisdictionType?id=MUNIW&language=en"
DIRECTORY_URL = "https://www.cookcountyclerkil.gov/elections/directory-elected-officials"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
REQUEST_TIMEOUT = 60

# Library district boards are a different body on a different layer.
EXCLUDED_OFFICES = {"Library Trustee"}
# The one head-of-government office per municipality (villages elect a
# President, cities a Mayor). Verified 2026-07: exactly one per municipality
# across all 128.
HEAD_OFFICES = {"Mayor", "President"}

# Minimums that prove the fetch returned the whole directory rather than a
# truncated or challenge-page response. Deliberate under-tolerances against
# the 2026-07 live values (128 municipalities / 879 governing records / 156
# ward seats) — a real shrink still fails, normal turnover does not.
MIN_JURISDICTIONS = 120
MIN_OFFICIALS = 800
MIN_WARD_OFFICIALS = 140


def fetch_json_requests(url):
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_json_playwright(url):
    """Escalation rung: run the request inside a real browser context.

    Only needed if Cloudflare starts challenging plain clients; the API is
    same-origin to the directory page, so a browser fetch() inherits the
    clearance cookie the page load earns.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(DIRECTORY_URL, wait_until="domcontentloaded", timeout=90000)
            payload = page.evaluate(
                "async (u) => { const r = await fetch(u, "
                "{headers: {'Accept': 'application/json'}}); "
                "if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }",
                url,
            )
        finally:
            browser.close()
    return json.loads(payload)


def fetch_json(url, engine):
    if engine == "playwright":
        return fetch_json_playwright(url)
    if engine == "requests":
        return fetch_json_requests(url)
    # auto: cheapest rung that works
    try:
        return fetch_json_requests(url)
    except Exception as exc:  # noqa: BLE001 - any transport/challenge failure escalates
        print("requests rung failed for %s (%s) — escalating to playwright" % (url, exc),
              file=sys.stderr)
        return fetch_json_playwright(url)


def envelope_data(payload, url):
    """The API wraps every response as {status, message, data:[...]}."""
    if isinstance(payload, dict) and "data" in payload:
        if payload.get("status") is False:
            print("FATAL: API reported failure for %s: %s"
                  % (url, payload.get("message")), file=sys.stderr)
            sys.exit(1)
        data = payload["data"]
    else:
        data = payload
    if not isinstance(data, list):
        print("FATAL: expected a list of records from %s — response shape changed" % url,
              file=sys.stderr)
        sys.exit(1)
    return data


def clean(value):
    """Trim to a real value or None — never an empty string, never a guess."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def full_name(rec):
    first = clean(rec.get("FirstName"))
    nickname = clean(rec.get("Nickname"))
    parts = [first]
    # A nickname stands in for the given name, so it reads after it —
    # 'Theodore J. "Teddy" Polashek', not 'Theodore J. Polashek "Teddy"'.
    if nickname and first and nickname.lower() != first.lower():
        parts.append('"%s"' % nickname)
    elif nickname and not first:
        parts.append('"%s"' % nickname)
    parts.extend([clean(rec.get("MiddleName")), clean(rec.get("LastName"))])
    name = " ".join(p for p in parts if p)
    suffix = clean(rec.get("Suffix"))
    if suffix:
        name = "%s %s" % (name, suffix)
    return name or None


def primary_address(rec):
    addresses = rec.get("Addresses") or []
    if not addresses:
        return {}
    addr = addresses[0]
    street = clean(addr.get("Address1"))
    line2 = clean(addr.get("Address2"))
    if street and line2:
        street = "%s, %s" % (street, line2)
    return {
        "address": street,
        "city": clean(addr.get("City")),
        "state": clean(addr.get("State")),
        "zip": clean(addr.get("Zip")),
        "phone": clean(addr.get("Phone")) or clean(rec.get("Phone")),
        "email": clean(addr.get("Email")) or clean(rec.get("Email")),
        "website": clean(addr.get("URL")),
        "address_type_id": addr.get("AddressTypeId"),
    }


def split_ward_jurisdiction(jurisdiction):
    """"City of Berwyn, Ward 1" -> ("City of Berwyn", "Ward 1")."""
    match = re.match(r"^(.*?),\s*((?:Ward|District)\s+.+)$", jurisdiction or "")
    if not match:
        return clean(jurisdiction), None
    return clean(match.group(1)), clean(match.group(2))


def official_record(rec, scraped_at, source_url, ward_seat=False):
    if ward_seat:
        jurisdiction, district = split_ward_jurisdiction(rec.get("Jurisdiction"))
    else:
        jurisdiction, district = clean(rec.get("Jurisdiction")), None
    addr = primary_address(rec)
    return {
        "jurisdiction": jurisdiction,
        "office": clean(rec.get("Office")),
        "district": district,
        "name": full_name(rec),
        "appointed": bool(rec.get("Appointed")),
        "last_elected": clean(rec.get("LastElected")),
        "next_election": clean(rec.get("NextElection")),
        # Municipality-level contact — see the module docstring.
        "office_address": addr.get("address"),
        "office_city": addr.get("city"),
        "office_state": addr.get("state"),
        "office_zip": addr.get("zip"),
        "office_phone": addr.get("phone"),
        "office_email": addr.get("email"),
        "website": addr.get("website"),
        "address_type_id": addr.get("address_type_id"),
        "source_url": source_url,
        "scraped_at": scraped_at,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default="cook_municipal_officials.json")
    parser.add_argument("--engine", choices=("auto", "requests", "playwright"),
                        default="auto",
                        help="fetch rung; auto tries requests then playwright")
    args = parser.parse_args()

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    jurisdictions = envelope_data(fetch_json(JURISDICTIONS_URL, args.engine), JURISDICTIONS_URL)
    officials = envelope_data(fetch_json(OFFICIALS_URL, args.engine), OFFICIALS_URL)
    ward_officials = envelope_data(fetch_json(WARD_OFFICIALS_URL, args.engine), WARD_OFFICIALS_URL)

    if len(jurisdictions) < MIN_JURISDICTIONS:
        print("FATAL: only %d municipalities returned (expected >= %d) — partial response"
              % (len(jurisdictions), MIN_JURISDICTIONS), file=sys.stderr)
        sys.exit(1)
    if len(officials) < MIN_OFFICIALS:
        print("FATAL: only %d municipal officials returned (expected >= %d) — partial response"
              % (len(officials), MIN_OFFICIALS), file=sys.stderr)
        sys.exit(1)
    if len(ward_officials) < MIN_WARD_OFFICIALS:
        print("FATAL: only %d ward officials returned (expected >= %d) — partial response"
              % (len(ward_officials), MIN_WARD_OFFICIALS), file=sys.stderr)
        sys.exit(1)

    municipalities = [{
        "tax_code": clean(j.get("TaxCode")),
        "jurisdiction_code": clean(j.get("JurisdictionCode")),
        "name": clean(j.get("LongDescription")) or clean(j.get("ShortDescription")),
        "source_url": JURISDICTIONS_URL,
        "scraped_at": scraped_at,
    } for j in jurisdictions]

    records = []
    for rec in officials:
        if clean(rec.get("Office")) in EXCLUDED_OFFICES:
            continue
        records.append(official_record(rec, scraped_at, OFFICIALS_URL))
    for rec in ward_officials:
        if clean(rec.get("Office")) in EXCLUDED_OFFICES:
            continue
        records.append(official_record(rec, scraped_at, WARD_OFFICIALS_URL, ward_seat=True))

    payload = {
        "county": "Cook",
        "directory_url": DIRECTORY_URL,
        "scraped_at": scraped_at,
        "municipalities": municipalities,
        "officials": records,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    heads = sum(1 for r in records if r["office"] in HEAD_OFFICES)
    seats = sum(1 for r in records if r["district"])
    print("scraped %d municipalities, %d governing-body officials "
          "(%d heads of government, %d ward seats) -> %s"
          % (len(municipalities), len(records), heads, seats, args.out), file=sys.stderr)


if __name__ == "__main__":
    main()

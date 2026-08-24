#!/usr/bin/env python3
"""
Resolve the Cicero Public Library's elected board out of the Cook County
Clerk's directory into data/app/cook-library-trustees.json, keyed by the
Clerk's own tax-agency id — the key the library-district layer's Cook entry
already carries on its boundary features.

WHY THIS FILE EXISTS. The Clerk's directory of elected officials publishes
library trustees for exactly ONE jurisdiction: Cicero (seven trustees, filed
under the TWNSP type beside the Town of Cicero's government — see
cook_municipal_officials_scraper.py's CICERO block for why the Clerk files
that town as a township). Everywhere else in Cook the library card is
name-only because no officeholder source exists; here one does, and the fleet
convention is that when identity, location or contact data exists in a
layer's source, it surfaces on the card rather than staying in the dataset.
The Will, Kane and Lake library entries already name people or contact — but
from attributes on their boundary services; this is the first carried as a
roster FILE, because Cook's boundary source (the Clerk's tax-agency tiling)
carries no people.

THE JOIN KEY IS THE CLERK'S OWN AGENCY ID, both sides published by the same
office: the tax tiling's Cicero feature is AGENCY 20060001 ("TOWN OF CICERO
LIBRARY FUND", politicalBoundary/MapServer layer 19 — a municipal library
FUND, not an independent district, which is why it is absent from layer 20),
and this file keys its one entry the same way. Verified live 2026-08-19:
layer 19 carries exactly one CICERO row.

Trustees are excluded from the MUNICIPAL card on purpose (they sit on the
library board, not the corporate authorities) and ship here instead. The
contact block is the LIBRARY's, not any person's: 5225 W. Cermak Rd. is the
library building (AddressTypeId 4, the directory's library type — the guard
below refuses any other type, so a residence can never ride this file), and
the directory's contact e-mail happens to live at the library's own domain.

Usage:
    python3 build_cicero_library_trustees.py <cook-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

AGENCY_ID = "20060001"
LIBRARY_NAME = "Cicero Public Library"
SOURCE_URL = "https://www.cookcountyclerkil.gov/elections/directory-elected-officials"
LIBRARY_ADDRESS_TYPE = 4

# Seven seats live (2026-08-19, staggered 2/4/6-year terms). A vacancy must
# not block the weekly refresh; a collapse means the TWNSP feed changed shape.
MIN_TRUSTEES = 5

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


fail = make_fail("build-cicero-library")


def clean(value):
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else None


def full_name(rec):
    parts = [clean(rec.get("FirstName")), clean(rec.get("MiddleName")),
             clean(rec.get("LastName")), clean(rec.get("Suffix"))]
    return " ".join(p for p in parts if p)


def phone_of(value):
    m = re.fullmatch(r"(\d{3})(\d{3})(\d{4})", value or "")
    return "%s-%s-%s" % m.groups() if m else clean(value)


def year_of(value):
    m = re.match(r"(\d{4})", value or "")
    return m.group(1) if m else None


def main():
    if len(sys.argv) < 2:
        fail("usage: build_cicero_library_trustees.py <cook-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        payload = json.load(f)
    records = payload.get("cicero_library_trustees") or []
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    trustees, office = [], {}
    for rec in records:
        name = full_name(rec)
        if not name:
            fail("a Library Trustee record has no name")
        addresses = rec.get("Addresses") or []
        addr = addresses[0] if addresses else {}
        # The library building or nothing: any other address type on a
        # trustee record would be a change in what the Clerk publishes, and
        # this file must never be the surface a residence slips through.
        if addr.get("AddressTypeId") != LIBRARY_ADDRESS_TYPE:
            fail("trustee %s carries address type %r, not the library's (%d) — "
                 "the directory changed what it publishes; re-read it before "
                 "shipping" % (name, addr.get("AddressTypeId"), LIBRARY_ADDRESS_TYPE))
        entry = {"name": name}
        next_election = year_of(clean(rec.get("NextElection")))
        if next_election:
            entry["nextElection"] = next_election
        if rec.get("Appointed"):
            entry["appointed"] = True
        trustees.append(entry)
        if not office:
            office = {
                "address": ", ".join(p for p in (
                    clean(addr.get("Address1")),
                    "%s IL %s" % (clean(addr.get("City")), clean(addr.get("Zip")))
                    if addr.get("City") else None) if p),
                "phone": phone_of(clean(addr.get("Phone"))),
                "email": clean(addr.get("Email")),
                "url": clean(addr.get("URL")),
            }
            office = {k: v for k, v in office.items() if v}

    if len(trustees) < MIN_TRUSTEES:
        fail("only %d trustees resolved (floor %d) — refusing to overwrite a "
             "good file with a partial scrape" % (len(trustees), MIN_TRUSTEES))
    trustees.sort(key=lambda t: t["name"])

    roster = {AGENCY_ID: {
        "name": LIBRARY_NAME,
        "trustees": trustees,
        "office": office,
        "sourceUrl": SOURCE_URL,
    }}
    out_path = os.path.join(out_dir, "cook-library-trustees.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print("build-cicero-library: wrote %s — %d trustees, contact %s"
          % (out_path, len(trustees), ", ".join(sorted(office)) or "none"))


if __name__ == "__main__":
    main()

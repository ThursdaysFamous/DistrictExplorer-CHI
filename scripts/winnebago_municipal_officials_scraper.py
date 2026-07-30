#!/usr/bin/env python3
"""
Stage 1 of Winnebago County's municipal-officials pipeline: read the twelve
municipal officeholder layers WinGIS publishes and emit the payload shape
build_municipal_officials_roster.py consumes.

WHY THIS SOURCE IS UNUSUAL — and why it is a scraper at all. Winnebago is the
only county in the fleet that publishes MUNICIPAL GOVERNING BODIES AS GIS
LAYERS: one layer per municipality on WinGIS's ElectedOfficials service,
carrying the village president or mayor and every trustee by name. Everywhere
else this data comes from a clerk's directory page or a PDF.

That makes it a rule-4 branch 2 source with an odd shape, not a branch 1: the
officials do NOT ride the boundary a card queries (the municipality layer is
statewide TIGER places), so they cannot be read at query time — they have to be
resolved to Census place GEOIDs and shipped in municipal-officials.json like
every other county's.

THREE LAYER SHAPES, because the county did not normalise them:

  WIDE      one feature, one column per seat — "President"/"Mayor" plus
            Trustee1..N or Commissioner1..N. Nine municipalities.
  PER-WARD  one feature per ward. Loves Park elects TWO aldermen per ward
            (Alderman1/Alderman2, each with its own phone); Machesney Park
            elects one trustee per district, with a phone.
  ROCKFORD  split across two layers — the mayor on one, the 14 alderpersons on
            another, each with a published city e-mail.

Two municipalities (Loves Park, Machesney Park) have NO head-of-government layer
— WinGIS publishes their council seats only. They ship council-only; a mayor is
never inferred from the fact that cities have one.

Nothing is inferred from column ORDER: a seat is emitted only when its column
holds a name, so a village that leaves Trustee6 empty ships five trustees
rather than a blank sixth.

Contact is PER-PERSON here, unlike the Cook DOEO API's municipality-level hall
contact, so it is emitted as `person_phone`/`person_email` — the builder's field
names for contact it may attach to an individual. Emitting plain `phone`/`email`
looks right and is silently DROPPED: the builder reads only the person_* keys,
by design, so a municipality-level number can never be printed as if it reached
one trustee directly.

The mayor's office WEBSITE that layer 19 carries is not emitted: the roster has
no per-person link field (only a municipality-level `url`), and a mayor's office
page is not the municipality's site.

Usage:
    python3 winnebago_municipal_officials_scraper.py [output.json]
"""

import argparse
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://maps.wingis.org/public/rest/services/ElectedOfficials/MapServer"
DIRECTORY_URL = "https://wingis.org/maps/electedofficials"
COUNTY = "Winnebago"
TIMEOUT = 90
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# layer -> how to read it. `name` is the municipality as the app's TIGER places
# layer spells it; the layers' own CityName is upper-cased and South Beloit's
# service is even titled "SouthBeloit", so the name is stated here rather than
# derived from a field that would need re-casing anyway.
WIDE = "wide"
PER_WARD = "per-ward"

LAYERS = [
    {"id": 13, "name": "Cherry Valley", "shape": WIDE, "head": "President", "seat": "Trustee"},
    {"id": 14, "name": "Durand", "shape": WIDE, "head": "Mayor", "seat": "Trustee"},
    {"id": 17, "name": "New Milford", "shape": WIDE, "head": "President", "seat": "Trustee"},
    {"id": 18, "name": "Pecatonica", "shape": WIDE, "head": "President", "seat": "Trustee"},
    {"id": 21, "name": "Rockton", "shape": WIDE, "head": "Mayor", "seat": "Trustee"},
    {"id": 22, "name": "Roscoe", "shape": WIDE, "head": "President", "seat": "Trustee"},
    {"id": 23, "name": "South Beloit", "shape": WIDE, "head": "Mayor", "seat": "Commissioner"},
    {"id": 24, "name": "Winnebago", "shape": WIDE, "head": "President", "seat": "Trustee"},
    # Loves Park: two aldermen per ward, each with its own phone column.
    {"id": 15, "name": "Loves Park", "shape": PER_WARD, "district": "Ward",
     "seats": [("Alderman1", "Alderman1Phone"), ("Alderman2", "Alderman2Phone")],
     "office": "Alderperson"},
    # Machesney Park: one trustee per district.
    {"id": 16, "name": "Machesney Park", "shape": PER_WARD, "district": "District",
     "seats": [("Trustee", "Ph_Number")], "office": "Trustee"},
    # Rockford is split across two layers; both are declared so the municipality
    # is built from the same table as the others rather than a special case.
    {"id": 19, "name": "Rockford", "shape": WIDE, "head": "Mayor", "seat": None,
     "head_email": "Email"},
    {"id": 20, "name": "Rockford", "shape": PER_WARD, "district": "Ward",
     "seats": [("Alderman", None)], "email": "Email", "office": "Alderperson"},
]

# Aggregate floors, deliberately under the 2026-07 live values (11
# municipalities / 9 heads / 75 seats / 16 phones / 15 e-mails). Per-municipality
# floors would be eleven separate guards over bodies of five to fifteen people,
# where one retirement reads as a collapse.
#
# HEADS IS 9, NOT 11, AND THAT IS THE SOURCE, NOT A PARSE FAILURE: WinGIS
# publishes no mayor/president layer for Loves Park or Machesney Park, only
# their council seats. Those two ship council-only rather than having a head
# invented for them.
#
# The floors sit just under the live values rather than well under, because a
# failed layer is now fatal (see main) — so these guard a COLUMN rename, which
# shows up as a quiet shortfall, not a fetch failure, which stops the run.
MIN_MUNICIPALITIES = 11
MIN_HEADS = 9
MIN_SEATS = 70


def get_json(url, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + "?" + query, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def rows(layer_id):
    payload = get_json("%s/%d/query" % (BASE, layer_id), {
        "where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json",
    })
    if "error" in payload:
        raise RuntimeError("layer %d: %s" % (layer_id, payload["error"].get("message")))
    return [f.get("attributes") or {} for f in payload.get("features") or []]


def clean(value):
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def clean_phone(value):
    text = clean(value)
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None  # a partial or malformed number is dropped, never padded
    return "%s-%s-%s" % (digits[:3], digits[3:6], digits[6:])


def read_wide(spec, attrs):
    out = []
    head = clean(attrs.get(spec["head"]))
    if head:
        person = {"office": spec["head"], "name": head}
        if spec.get("head_email"):
            email = clean(attrs.get(spec["head_email"]))
            if email:
                person["person_email"] = email
        out.append(person)
    seat = spec.get("seat")
    if seat:
        # Walk the numbered columns the layer actually has, in order, and emit a
        # seat only where a name sits. Column COUNT is not the seat count: some
        # villages leave a trailing column empty between appointments.
        index = 1
        while True:
            column = "%s%d" % (seat, index)
            if column not in attrs:
                break
            name = clean(attrs.get(column))
            if name:
                out.append({"office": seat, "name": name})
            index += 1
    return out


def read_per_ward(spec, attrs):
    out = []
    district = clean(attrs.get(spec["district"]))
    for name_col, phone_col in spec["seats"]:
        name = clean(attrs.get(name_col))
        if not name:
            continue
        person = {"office": spec["office"], "name": name}
        if district:
            person["district"] = "Ward %s" % district
        if phone_col:
            phone = clean_phone(attrs.get(phone_col))
            if phone:
                person["person_phone"] = phone
        if spec.get("email"):
            email = clean(attrs.get(spec["email"]))
            if email:
                person["person_email"] = email
        out.append(person)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="winnebago_municipal_officials.json")
    args = ap.parse_args()

    officials = []
    municipalities = []
    # EVERY LAYER MUST ANSWER, or this run produces nothing. WinGIS is
    # intermittently flaky (a run during development lost layer 19 and shipped a
    # Rockford with no mayor, under an aggregate floor that could not tell the
    # difference between "the county has 9 heads" and "we failed to read one").
    # Twelve small layers have no honest partial state, and the pipeline already
    # has the right answer for a failed source: the workflow's continue-on-error
    # plus PRESERVABLE carries the whole county forward from the shipped roster.
    # So a single failure is fatal here rather than a quiet coverage loss.
    for spec in LAYERS:
        try:
            data = rows(spec["id"])
        except Exception as exc:  # noqa: BLE001
            print("winnebago-municipal: FATAL — layer %d (%s) failed: %s. Refusing to "
                  "emit a partial county; the roster build will carry Winnebago "
                  "forward from the shipped file."
                  % (spec["id"], spec["name"], exc), file=sys.stderr)
            sys.exit(1)
        found = []
        for attrs in data:
            found.extend(read_wide(spec, attrs) if spec["shape"] == WIDE
                         else read_per_ward(spec, attrs))
        if not found:
            print("winnebago-municipal: FATAL — layer %d (%s) returned rows but no "
                  "officials; the column names changed."
                  % (spec["id"], spec["name"]), file=sys.stderr)
            sys.exit(1)
        if spec["name"] not in municipalities:
            municipalities.append(spec["name"])
        for person in found:
            person["jurisdiction"] = spec["name"]
            officials.append(person)

    heads = sum(1 for p in officials if p["office"].lower() in ("mayor", "president"))
    seats = len(officials) - heads
    problems = []
    if len(municipalities) < MIN_MUNICIPALITIES:
        problems.append("%d municipalities (< %d)" % (len(municipalities), MIN_MUNICIPALITIES))
    if heads < MIN_HEADS:
        problems.append("%d heads (< %d)" % (heads, MIN_HEADS))
    if seats < MIN_SEATS:
        problems.append("%d seats (< %d)" % (seats, MIN_SEATS))
    if problems:
        print("winnebago-municipal: FATAL — refusing to write a payload that lost "
              "coverage: %s" % "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    scraped_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for person in officials:
        person["source_url"] = DIRECTORY_URL
        person["scraped_at"] = scraped_at
    payload = {
        "county": COUNTY,
        "directory_url": DIRECTORY_URL,
        "scraped_at": scraped_at,
        "municipalities": [{"name": n, "source_url": DIRECTORY_URL,
                            "scraped_at": scraped_at} for n in municipalities],
        "officials": officials,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    phones = sum(1 for p in officials if p.get("person_phone"))
    emails = sum(1 for p in officials if p.get("person_email"))
    print("winnebago-municipal: %d municipalities, %d officials (%d heads, %d seats, "
          "%d phones, %d e-mails) -> %s"
          % (len(municipalities), len(officials), heads, seats, phones, emails, args.out))


if __name__ == "__main__":
    main()

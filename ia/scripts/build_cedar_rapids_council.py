#!/usr/bin/env python3
"""
Build stage 2: data/app/cedar-rapids-council-members.json from the cache
cedar_rapids_council_scraper.py writes.

WHAT SHIPS AND WHAT DOES NOT
------------------------------
Eight of the city's nine elected seats ship: five district members, keyed by
district so the card can name the reader's own, and three at-large members
under `citywide` so every card names them too.

THE MAYOR IS SCRAPED AND DELIBERATELY NOT SHIPPED. She is elected by the whole
city, and the fleet's at-large rule puts a citywide officer on the unit's
identity card rather than on a district card. The scraper reads her anyway --
see its docstring -- so that this exclusion is a decision this pipeline can
demonstrate rather than a gap it cannot see, and the drop is printed on every
run. The card's Council row SAYS SO WITHOUT NAMING HER -- "plus a mayor who is
elected citywide and is not named on this card" -- so a reader is not left
thinking the council is the whole of the city's elected government, and is not
told a name this card does not carry.

THE WITNESS HERE IS WEAKER THAN WATERLOO'S, AND IS RECORDED AS WEAKER
----------------------------------------------------------------------
build_waterloo_council.py cross-witnesses every scraped name against the name
the city's own ward polygons carry in band, which catches a member changing
without the page changing. Linn County's district layer carries no names at all
-- only POLITICAL_TWP, CITYCOUNCIL and Updated -- so no such check is possible
for Cedar Rapids and none is faked.

What IS witnessed is the NUMBERING, against the shipped boundary rather than
against a constant: the five districts this roster names must be exactly the
five the shipped cedar-rapids-wards.json draws. That catches the two failures
that would actually mislead a reader -- a district appearing on the map with no
member, or a member keyed to a district that is not on the map -- and it will
NOT catch a stale name. Saying which is which is the point.

THE ADDRESS TEST IS THE COUNTY OFFICERS' ONE, APPLIED UNCHANGED
-----------------------------------------------------------------
One of the eight addresses is not on a city domain: the city publishes
scott@scotteolson.com for District 4, his own consulting firm. The test asks
whether the officeholder's own name vouches for the local part, never what the
domain is -- and it passes here on "scott". Consulting the domain instead errs
in BOTH directions, which the five-city Tier A build measured on six of thirty
addresses, and it would drop an address the city itself publishes as the way to
reach that member.

The duplication of email_witnesses() from build_ia_county_officers.py is
deliberate, the same as in build_ia_city_officials.py: this is the test that
decides whether a real person's contact detail ships, and a change to it should
have to be made twice.

FLOORS ARE SET AT THE MEASUREMENT BECAUSE THE CITY PUBLISHES EVERY FIELD
-------------------------------------------------------------------------
Measured 2026-09-04: 8 of 8 shipped seats carry a phone, an e-mail and a term.
The floors are 8, not a hedge below it -- the Barron rule, that a floor
measures what a source actually publishes. A city that stops publishing one
member's phone fails this build, which is the point: that is a change somebody
should look at, not absorb.
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          ".cache", "cedar_rapids_council.json")
WARDS_PATH = os.path.join(APP_DATA_DIR, "cedar-rapids-wards.json")
OUT_NAME = "cedar-rapids-council-members.json"

EXPECT_DISTRICTS = [1, 2, 3, 4, 5]
EXPECT_AT_LARGE = 3
EXPECT_SEATS = 8          # what ships: 5 districts + 3 at-large
EXPECT_SCRAPED = 9        # what the scraper reads: the above plus the mayor
MIN_PHONES = 8
MIN_EMAILS = 8
MIN_TERMS = 8


def load(path, what):
    try:
        with open(path) as f:
            return json.load(f)
    except OSError as e:
        raise RuntimeError("%s missing (%s); run the scraper first" % (what, e))


def email_witnesses(name, email):
    """Does this address's local part carry THIS person's name?

    Lifted deliberately from build_ia_county_officers.py -- see the docstring.
    """
    local = re.sub(r"[^a-z]", "", email.split("@")[0].lower())
    toks = [t.lower() for t in re.findall(r"[A-Za-z]{3,}", name or "")]
    if any(t in local for t in toks):
        return True
    parts = [t.lower() for t in re.findall(r"[A-Za-z]{2,}", name or "")]
    if len(parts) >= 2:
        for sur in parts[1:]:
            if local.startswith(parts[0][0] + sur):
                return True
    return False


def person(rec, badge):
    out = {"name": rec["name"], "seat": badge}
    for key in ("phone", "email", "termExpires"):
        if rec.get(key):
            out[key] = rec[key]
    return out


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    cache = load(CACHE_PATH, "the Cedar Rapids council cache")
    members = cache.get("members") or []
    if len(members) != EXPECT_SCRAPED:
        raise RuntimeError("the cache carries %d seats, expected %d"
                           % (len(members), EXPECT_SCRAPED))

    by_district = {}
    at_large = []
    mayor = None
    for rec in members:
        if rec.get("kind") == "district":
            by_district[int(rec["district"])] = rec
        elif rec.get("kind") == "at-large":
            at_large.append(rec)
        elif rec.get("kind") == "mayor":
            mayor = rec

    if sorted(by_district) != EXPECT_DISTRICTS:
        raise RuntimeError("districts %s, expected %s"
                           % (sorted(by_district), EXPECT_DISTRICTS))
    if len(at_large) != EXPECT_AT_LARGE:
        raise RuntimeError("%d at-large members, expected %d"
                           % (len(at_large), EXPECT_AT_LARGE))
    if not mayor:
        raise RuntimeError(
            "the cache names no mayor. She is not shipped, but she IS scraped so "
            "that her absence from this file stays a decision rather than a gap "
            "nothing can see; her disappearance means the mayor page reshaped.")

    # --- the numbering witness, against the SHIPPED boundary ---------------
    wards = load(WARDS_PATH, "cedar-rapids-wards.json")
    drawn = sorted(int(f["properties"]["ward"]) for f in wards.get("features", []))
    if drawn != sorted(by_district):
        raise RuntimeError(
            "the roster names districts %s and the shipped boundary draws %s. One "
            "of them is stale: a district on the map with no member answers a "
            "reader with a blank card, and a member keyed to a district that is "
            "not drawn never reaches anybody."
            % (sorted(by_district), drawn))
    print("  numbering witness: the roster's districts %s match the %d shipped "
          "polygons exactly (no name-level witness exists — Linn's layer carries "
          "no roster in band)" % (sorted(by_district), len(drawn)), file=sys.stderr)

    print("  MAYOR NOT SHIPPED: %s is elected citywide, so by the fleet's at-large "
          "rule she belongs on the City card and not on a district card. The "
          "card's Council row states the office WITHOUT naming her."
          % mayor["name"], file=sys.stderr)

    districts = {str(n): person(by_district[n], "District %d" % n)
                 for n in EXPECT_DISTRICTS}
    citywide = [person(r, "At-Large")
                for r in sorted(at_large, key=lambda r: r["name"])]

    everyone = list(districts.values()) + citywide
    if len(everyone) != EXPECT_SEATS:
        raise RuntimeError("%d seats built, expected %d" % (len(everyone), EXPECT_SEATS))

    phones = [p["phone"] for p in everyone if p.get("phone")]
    emails = [p["email"] for p in everyone if p.get("email")]
    terms = [p["termExpires"] for p in everyone if p.get("termExpires")]
    if len(phones) < MIN_PHONES or len(emails) < MIN_EMAILS:
        raise RuntimeError(
            "%d phones and %d e-mails across %d seats (floors %d/%d). The city "
            "publishes both for every seat; fewer means the page changed shape."
            % (len(phones), len(emails), EXPECT_SEATS, MIN_PHONES, MIN_EMAILS))
    if len(terms) < MIN_TERMS:
        raise RuntimeError("%d terms across %d seats (floor %d)"
                           % (len(terms), EXPECT_SEATS, MIN_TERMS))

    # --- the address test ---------------------------------------------------
    for p in everyone:
        if p.get("email") and not email_witnesses(p["name"], p["email"]):
            raise RuntimeError(
                "%s's published address %r does not carry their name. An address "
                "that no part of the officeholder's name vouches for is somebody "
                "else's, and shipping it puts a real person's mail in front of a "
                "reader looking for someone else." % (p["name"], p["email"]))
    off_domain = [p["email"] for p in everyone
                  if p.get("email") and not p["email"].endswith("@cedar-rapids.org")]
    if off_domain:
        print("  address test: %d of %d addresses are off the city's own domain and "
              "ship anyway, witnessed by name: %s"
              % (len(off_domain), len(emails), ", ".join(sorted(off_domain))),
              file=sys.stderr)

    # --- the switchboard test (Part 5); it should NOT fire here ------------
    distinct = set(phones)
    if len(distinct) == 1:
        raise RuntimeError(
            "all %d seats now publish the SAME number (%s). That is a switchboard, "
            "not eight direct lines: hoist it to a council-office row the way "
            "build_ia_county_officers.py does rather than printing it eight times."
            % (EXPECT_SEATS, phones[0]))
    if len(distinct) != len(phones):
        dupes = sorted(p for p in distinct if phones.count(p) > 1)
        raise RuntimeError(
            "these numbers are shared by more than one seat: %s. A shared line is "
            "an office's, not a person's — read the page before shipping it as "
            "either member's direct line." % dupes)

    payload_obj = {
        "sourceUrl": cache.get("sourceUrl"),
        "wards": districts,
        "citywide": citywide,
    }
    payload = json.dumps(payload_obj, indent=1, sort_keys=True) + "\n"

    print("cedar-rapids-council-members: %d seats (%d district, %d citywide), %d "
          "distinct phones, %d e-mails, %d terms; mayor excluded by the at-large "
          "rule" % (EXPECT_SEATS, len(districts), len(citywide), len(distinct),
                    len(emails), len(terms)), file=sys.stderr)

    if check_only:
        try:
            with open(out_path) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("%s is missing (%s)" % (OUT_NAME, e))
        if shipped != payload:
            raise RuntimeError("data/app/%s has drifted from the cache. Re-run: "
                               "python3 ia/scripts/build_cedar_rapids_council.py"
                               % OUT_NAME)
        print("check: shipped roster matches the cache", file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/app/%s" % OUT_NAME, file=sys.stderr)


if __name__ == "__main__":
    main()

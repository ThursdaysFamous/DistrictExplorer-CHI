#!/usr/bin/env python3
"""Build mi/data/app/mi-grand-rapids-council-members.json — Grand Rapids's City
Commission, read by the Grand Rapids entry of mi/index.html's `city-ward` card.

SEVEN SEATS, SIX PUBLISHED, AND THE CARD SAYS SO
--------------------------------------------------
The city states the arithmetic on its own commission page: "This legislative
body consists of the Mayor and six Commissioners… The residents of each Ward
directly elect two commissioners." Two per ward ride the polygons; the Mayor
rides none of them and ships in a `citywide` block, because a ward card naming
two of seven would look complete.

The city publishes SIX of the seven — one Ward 1 commissioner where Wards 2 and
3 each have two — and says nothing about the seventh. So `seats` ships beside
the members and the card states the shortfall in its own words. That is the
Alexander County machinery, used here for the first time on a DISTRICTED body:
naming five and implying six would conceal a seat, and naming a sixth would
invent a person. Nothing here decides whether that seat is vacant or merely
unpublished; the city says neither.

WHAT SHIPS PER MEMBER, AND WHAT DOES NOT
------------------------------------------
Name, ward, e-mail and a direct phone, each read from that member's own page.
The number common to ALL of them is the city switchboard and is hoisted to the
body — six identical numbers are not six direct lines (docs/EXPANSION_GUIDE.md
Part 5) — and this REFUSES to write if the hoisted number ever reappears on a
member row. The address is City Hall, labelled as such: unlike Detroit's page,
which carries an explicit "City Council Office" block, Grand Rapids prints
300 Monroe Avenue NW only in its site-wide footer.

    python3 mi/scripts/mi_grand_rapids_council_scraper.py   # refresh the cache
    python3 mi/scripts/build_mi_grand_rapids_council.py
    python3 mi/scripts/build_mi_grand_rapids_council.py --check
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INSTANCE_ROOT = os.path.dirname(HERE)
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
OUT = os.path.join(APP_DATA_DIR, "mi-grand-rapids-council-members.json")
CACHE = os.path.join(HERE, ".cache", "mi_grand_rapids_council.json")

EXPECT_WARDS = ["1", "2", "3"]
COMMISSIONERS_PER_WARD = 2
EXPECT_SEATS = len(EXPECT_WARDS) * COMMISSIONERS_PER_WARD + 1
SITE = "https://www.grandrapidsmi.gov/"
# The city has never published fewer than five of its six commissioners; this
# floors the roster so a page rebuild that silently empties it fails loudly.
MIN_NAMED = 5


def fail(msg):
    print("grand-rapids-council: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def shape(cache):
    wards = {w: [] for w in EXPECT_WARDS}
    citywide = []
    for m in cache["members"]:
        row = {"name": m["name"], "profileUrl": m["profileUrl"]}
        if m.get("email"):
            row["email"] = m["email"]
        if m.get("phone"):
            row["phone"] = m["phone"]
        if m.get("isMayor"):
            row["seat"] = "Mayor"
            citywide.append(row)
        else:
            row["seat"] = "Ward %s Commissioner" % m["ward"]
            if m["ward"] not in wards:
                fail("member %s carries ward %r, which is not one of %s"
                     % (m["name"], m["ward"], EXPECT_WARDS))
            wards[m["ward"]].append(row)
    for w in wards:
        wards[w].sort(key=lambda r: r["name"])
    doc = {
        "citywide": sorted(citywide, key=lambda r: r["name"]),
        "seats": cache.get("seats", EXPECT_SEATS),
        # Shipped so the card never hardcodes the city's own arithmetic: how
        # many commissioners a ward elects is a civic fact and belongs in the
        # data, beside the members it is used to count.
        "seatsPerWard": COMMISSIONERS_PER_WARD,
        "sourceUrl": cache["sourceUrl"],
        "wards": wards,
    }
    office = {}
    if cache.get("switchboard"):
        office["phone"] = cache["switchboard"]
    if cache.get("address"):
        office["lines"] = list(cache["address"])
    if office:
        office["label"] = "City Hall"
        doc["office"] = office
    return doc


def validate(doc):
    if sorted(doc["wards"], key=int) != EXPECT_WARDS:
        fail("wards are %s, expected %s" % (sorted(doc["wards"], key=int), EXPECT_WARDS))
    named = len(doc["citywide"]) + sum(len(v) for v in doc["wards"].values())
    if doc["seats"] != EXPECT_SEATS:
        fail("seats is %r, but the city's own composition sentence gives %d"
             % (doc["seats"], EXPECT_SEATS))
    if named > doc["seats"]:
        fail("%d people named for %d seats" % (named, doc["seats"]))
    if named < MIN_NAMED:
        fail("only %d of %d seats named (floor %d) — the city's commission page has "
             "probably been rebuilt into a shape this parser no longer reads"
             % (named, doc["seats"], MIN_NAMED))
    if len(doc["citywide"]) != 1:
        fail("%d citywide seats, expected exactly the Mayor" % len(doc["citywide"]))
    if doc.get("seatsPerWard") != COMMISSIONERS_PER_WARD:
        fail("seatsPerWard is %r, but the city elects %d commissioners per ward"
             % (doc.get("seatsPerWard"), COMMISSIONERS_PER_WARD))
    for w, rows in doc["wards"].items():
        if len(rows) > COMMISSIONERS_PER_WARD:
            fail("ward %s has %d commissioners, more than the %d the city elects"
                 % (w, len(rows), COMMISSIONERS_PER_WARD))
        if not rows:
            fail("ward %s names nobody at all — the city publishes at least one per "
                 "ward, so this is a parse failure rather than a shortfall" % w)

    everyone = doc["citywide"] + [r for rows in doc["wards"].values() for r in rows]
    switchboard = (doc.get("office") or {}).get("phone")
    for r in everyone:
        if not r["name"].strip():
            fail("a member row carries no name")
        if not r["profileUrl"].startswith(SITE):
            fail("%s links off-site: %s" % (r["name"], r["profileUrl"]))
        if switchboard and r.get("phone") == switchboard:
            fail("%s carries the city switchboard as a direct line — it is the BODY's "
                 "number and is hoisted, never repeated per member" % r["name"])
    names = [r["name"] for r in everyone]
    if len(set(names)) != len(names):
        fail("one person holds two seats")


def check():
    if not os.path.exists(OUT):
        fail("%s is missing" % OUT)
    with open(OUT, encoding="utf-8") as fh:
        doc = json.load(fh)
    validate(doc)
    named = len(doc["citywide"]) + sum(len(v) for v in doc["wards"].values())
    print("grand-rapids-council: OK — %d of %d seats named (%s), source %s"
          % (named, doc["seats"],
             ", ".join("ward %s: %d" % (w, len(doc["wards"][w])) for w in EXPECT_WARDS),
             doc["sourceUrl"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="offline gate on the shipped file")
    args = ap.parse_args()
    if args.check:
        return check()

    if not os.path.exists(CACHE):
        fail("no scraper cache — run mi/scripts/mi_grand_rapids_council_scraper.py first")
    with open(CACHE, encoding="utf-8") as fh:
        cache = json.load(fh)

    doc = shape(cache)
    validate(doc)
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    named = len(doc["citywide"]) + sum(len(v) for v in doc["wards"].values())
    print("Wrote %s — %d of %d seats named" % (OUT, named, doc["seats"]))
    if named < doc["seats"]:
        print("  %d seat(s) the city does not publish; the card states this rather "
              "than concealing it" % (doc["seats"] - named))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/waterloo-council-members.json — the seven people Waterloo
elects to its council, read by ia/index.html's `city-ward` card.

A mayor, two at-large council members, and one from each of five wards.
FIVE OF THE SEVEN COUNCIL SEATS HAVE A WARD; the other two represent every
ward, so they ship in a `citywide` block that the card renders under its own
heading rather than being attached to a polygon they do not have. A ward layer
that named only the ward member would answer five sevenths of the question and
look complete doing it.

THE MAYOR IS DELIBERATELY ABSENT, and that is the one place this file differs
in SHAPE from its Des Moines counterpart. Waterloo publishes him on a separate
page and he is elected by the whole city, so the fleet's at-large rule
(docs/EXPANSION_GUIDE.md Part 1: "a body elected by the whole unit adds zero
point-discrimination -- it rides the unit's identity card, never a polygon
layer") puts him on the City card, not on a ward's. Des Moines carries its
mayor in `citywide` for historical reasons and that is left alone here; the
difference is recorded rather than smoothed.

THE CROSS-WITNESS, AND WHICH PUBLISHER IS THE AUTHORITY
---------------------------------------------------------
Two City of Waterloo publishers name the council:

  * the council page (waterloo_council_scraper.py) -- name, seat, term expiry,
    PHONE and e-mail; and
  * the Wards feature service, in band, on the polygons themselves --
    Ward_Councilperson, At_Large1_Councilperson, At_Large2_Councilperson and
    a link to that same council page. NO phone, NO e-mail, NO term.

The council page is the authority, for the reason Des Moines's is: the feature
service has no phone field at all, and a roster attached to a boundary is
refreshed when the BOUNDARY is, not when the seat changes (the Coles County
reading). Waterloo's layer happens to be fresh -- dataLastEditDate 2026-09-03,
measured 2026-09-04 -- and that changes nothing about which publisher is
structurally the right one to read.

But the service's names are still read, ONCE, here, as a WITNESS: every ward
member and both at-large members must match the polygons' own in-band names or
this refuses to write. Two publishers inside one city agreeing is worth more
than either alone, and it catches the expensive failure -- a council page
rebuilt into a different shape that still parses.

The witness compares first and last token, not whole strings, because the two
publishers do not spell one name identically: the page prints "Hector A.
Salamanca-Arroyo" where the polygon carries "Hector Salamanca-Arroyo". That is
a middle initial, not a disagreement about who holds the seat. THE MATCH IS
PRINTED on every run so a silent normalisation cannot hide a real difference.

NO SWITCHBOARD HERE, AND THAT IS MEASURED RATHER THAN ASSUMED
---------------------------------------------------------------
docs/EXPANSION_GUIDE.md Part 5: an identical phone on every member row is the
body's switchboard, not contact, and belongs hoisted to the body. Waterloo
publishes seven DISTINCT numbers, so nothing is hoisted. Re-run every build
rather than recorded as settled.

Usage:
    python3 ia/scripts/waterloo_council_scraper.py   # refresh the cache
    python3 ia/scripts/build_waterloo_council.py
    python3 ia/scripts/build_waterloo_council.py --check
"""

import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache",
                     "waterloo_council.json")
OUT_NAME = "waterloo-council-members.json"

WARDS_LAYER = ("https://services1.arcgis.com/QOAXA4I2iTKKdBuy/ArcGIS/rest/services/"
               "Wards_view/FeatureServer/0")

EXPECT_WARDS = [1, 2, 3, 4, 5]
EXPECT_AT_LARGE = 2
EXPECT_SEATS = 7

# Waterloo does NOT publish one phone format. Six read "(319) 324-0593" and
# two read "(319)-988-1960" -- a hyphen where the others have a space. Both
# ship verbatim; normalising a published number invents one.
PHONE_RE = re.compile(r"^\(\d{3}\)[\s-]\d{3}-\d{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
TERM_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")


def load_cache():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except OSError as e:
        raise RuntimeError("no scraper cache at %s (%s) -- run "
                           "ia/scripts/waterloo_council_scraper.py first" % (CACHE, e))


def fetch_witness():
    """ward number -> in-band councilperson name, plus the two at-large names."""
    url = ("%s/query?where=1%%3D1&outFields=SHORTNAME,Ward_Councilperson,"
           "At_Large1_Councilperson,At_Large2_Councilperson&returnGeometry=false"
           "&f=json" % WARDS_LAYER)
    raw = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "120",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True).stdout
    feats = json.loads(raw).get("features", [])
    by_ward, at_large = {}, set()
    for f in feats:
        a = f["attributes"]
        by_ward[int(a["SHORTNAME"])] = (a.get("Ward_Councilperson") or "").strip()
        for key in ("At_Large1_Councilperson", "At_Large2_Councilperson"):
            val = (a.get(key) or "").strip()
            if val:
                at_large.add(val)
    if sorted(by_ward) != EXPECT_WARDS:
        raise RuntimeError("the Wards layer carries wards %s, expected %s"
                           % (sorted(by_ward), EXPECT_WARDS))
    if len(at_large) != EXPECT_AT_LARGE:
        raise RuntimeError(
            "the Wards layer's at-large columns name %d distinct people (%s), "
            "expected %d. Every polygon repeats the same two; a third name means "
            "the columns disagree between wards and none of them can be trusted."
            % (len(at_large), sorted(at_large), EXPECT_AT_LARGE))
    return by_ward, at_large


def name_key(name):
    """(first token, last token), lowercased, punctuation stripped.

    Whole-string comparison would fail on "Hector A. Salamanca-Arroyo" against
    the polygon's "Hector Salamanca-Arroyo" -- a middle initial, not a
    disagreement. First and last token still catches a different PERSON, which
    is what is being witnessed.
    """
    toks = [re.sub(r"[^A-Za-z'-]", "", t) for t in name.split()]
    toks = [t for t in toks if t]
    if not toks:
        return ()
    return (toks[0].lower(), toks[-1].lower())


def person(rec, badge):
    out = {"name": rec["name"], "seat": badge}
    for key in ("phone", "email", "termExpires"):
        if rec.get(key):
            out[key] = rec[key]
    return out


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    cache = load_cache()
    wards_in = cache.get("wards") or {}
    at_large_in = cache.get("atLarge") or []

    if sorted(int(k) for k in wards_in) != EXPECT_WARDS:
        raise RuntimeError("the cache names wards %s, expected %s"
                           % (sorted(wards_in), EXPECT_WARDS))
    if len(at_large_in) != EXPECT_AT_LARGE:
        raise RuntimeError("the cache names %d at-large members, expected %d"
                           % (len(at_large_in), EXPECT_AT_LARGE))

    # --- the cross-witness -------------------------------------------------
    witness_wards, witness_at_large = fetch_witness()
    for num in EXPECT_WARDS:
        page = wards_in[str(num)]
        poly_name = witness_wards[num]
        if name_key(page["name"]) != name_key(poly_name):
            raise RuntimeError(
                "Ward %d: the council page names %r and the city's own Wards "
                "layer carries %r. Two City of Waterloo publishers disagree "
                "about who holds a seat -- read both before shipping either."
                % (num, page["name"], poly_name))
        if page["name"] != poly_name:
            # matched on first+last but spelled differently: SAY SO, every run
            print("  witness: Ward %d matches on first+last, spelled %r on the "
                  "page and %r on the polygon" % (num, page["name"], poly_name),
                  file=sys.stderr)
    page_at_large = {name_key(r["name"]) for r in at_large_in}
    if page_at_large != {name_key(n) for n in witness_at_large}:
        raise RuntimeError(
            "the council page's at-large members %s do not match the Wards "
            "layer's %s" % (sorted(r["name"] for r in at_large_in),
                            sorted(witness_at_large)))
    print("  witness: all %d ward members and both at-large members agree with "
          "the city's own Wards layer" % len(EXPECT_WARDS), file=sys.stderr)

    # --- shape -------------------------------------------------------------
    wards = {str(n): person(wards_in[str(n)], "Ward %d" % n) for n in EXPECT_WARDS}
    citywide = [person(r, "At-Large") for r in at_large_in]

    everyone = list(wards.values()) + citywide
    if len(everyone) != EXPECT_SEATS:
        raise RuntimeError("assembled %d seats, expected %d"
                           % (len(everyone), EXPECT_SEATS))

    for rec in everyone:
        if rec.get("phone") and not PHONE_RE.match(rec["phone"]):
            raise RuntimeError("%s carries phone %r, which is neither shape the "
                               "city publishes" % (rec["name"], rec["phone"]))
        if rec.get("email") and not EMAIL_RE.match(rec["email"]):
            raise RuntimeError("%s carries e-mail %r" % (rec["name"], rec["email"]))
        if rec.get("termExpires") and not TERM_RE.match(rec["termExpires"]):
            raise RuntimeError("%s carries term %r, expected MM/DD/YYYY"
                               % (rec["name"], rec["termExpires"]))

    # --- floors: a field that stops being published must not ship empty ----
    phones = [r["phone"] for r in everyone if r.get("phone")]
    emails = [r["email"] for r in everyone if r.get("email")]
    terms = [r["termExpires"] for r in everyone if r.get("termExpires")]
    if len(phones) != EXPECT_SEATS or len(emails) != EXPECT_SEATS:
        raise RuntimeError("%d of %d seats carry a phone and %d an e-mail; the city "
                           "publishes both for all seven, so a shortfall is the page "
                           "changing shape" % (len(phones), EXPECT_SEATS, len(emails)))
    if len(terms) != EXPECT_SEATS:
        raise RuntimeError("%d of %d seats carry a term-expiry date; the city "
                           "publishes one for every seat, and it is also the token "
                           "the scraper uses to tell a member's own line from the "
                           "bio link that repeats their name"
                           % (len(terms), EXPECT_SEATS))

    # --- the switchboard test (Part 5); it should NOT fire here ------------
    distinct = set(phones)
    if len(distinct) == 1:
        raise RuntimeError(
            "all %d seats now publish the SAME number (%s). That is a switchboard, "
            "not seven direct lines: hoist it to a council-office row the way "
            "build_ia_county_officers.py does rather than printing it seven times."
            % (EXPECT_SEATS, phones[0]))
    if len(distinct) != len(phones):
        dupes = sorted(p for p in distinct if phones.count(p) > 1)
        raise RuntimeError(
            "these numbers are shared by more than one seat: %s. A shared line is "
            "an office's, not a person's -- read the page before shipping it as "
            "either member's direct line." % dupes)

    payload_obj = {
        "sourceUrl": cache.get("sourceUrl"),
        "wards": wards,
        "citywide": citywide,
    }
    payload = json.dumps(payload_obj, indent=1, sort_keys=True) + "\n"

    print("waterloo-council-members: %d seats (%d ward, %d citywide), %d distinct "
          "phones, %d e-mails" % (EXPECT_SEATS, len(wards), len(citywide),
                                  len(distinct), len(emails)), file=sys.stderr)

    if check_only:
        try:
            with open(out_path) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("%s is missing (%s)" % (OUT_NAME, e))
        if shipped != payload:
            raise RuntimeError("data/app/%s has drifted from the cache. Re-run: "
                               "python3 ia/scripts/build_waterloo_council.py" % OUT_NAME)
        print("check: shipped roster matches the cache", file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/app/%s" % OUT_NAME, file=sys.stderr)


if __name__ == "__main__":
    main()

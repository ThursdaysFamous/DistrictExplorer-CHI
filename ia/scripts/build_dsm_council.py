#!/usr/bin/env python3
"""
Build data/app/dsm-council-members.json — the seven people Des Moines elects,
read by ia/index.html's `dsm-ward` card.

Iowa Code 372.4(1)(b): a mayor, two at-large council members, and one council
member from each of four wards. FOUR OF THE SEVEN SEATS HAVE A WARD; the other
three represent every ward, so they ship in a `citywide` block that the card
renders under its own heading rather than being attached to a polygon they do
not have. A ward layer that named only the ward member would answer four
sevenths of the question and look complete doing it.

THE CROSS-WITNESS, AND WHICH PUBLISHER IS THE AUTHORITY
---------------------------------------------------------
Two City of Des Moines publishers name the four ward members:

  * the council page (dsm_council_scraper.py) -- name, seat, PHONE, e-mail,
    election date and term expiry; and
  * the Wards feature service, in band, on the polygons themselves --
    PersonFName / PersonMName / PersonLName / EMail and nothing else.

The council page is the authority because it is the richer and the more
evenly maintained of the two: the feature service has no phone field at all,
its PersonTitle is null on all four, and its features are edited on the
redistricting/annexation schedule rather than the electoral one (ward 2's
feature still carried its 2024-02-16 edit while wards 1, 3 and 4 were edited
across 2025-12-29..31 for the November 2025 cycle). That is the Coles County
reading: a roster attached to a boundary is refreshed when the boundary is.

But the service's names are still read, ONCE, here, as a WITNESS. Every ward
member must match the polygon's own in-band name and e-mail, or this refuses
to write. Two publishers inside one city agreeing is worth more than either
alone, and the failure mode it catches is the expensive one -- a council page
rebuilt into a different shape that still parses.

THE SWITCHBOARD TEST RUNS HERE TOO, AND CORRECTLY DOES NOT FIRE
-----------------------------------------------------------------
docs/EXPANSION_GUIDE.md Part 5: an identical phone on every member row is the
body's switchboard, not contact, and belongs hoisted to the body. Des Moines
publishes seven DISTINCT numbers, so nothing is hoisted and each number stays
on its own member. The test is re-run on every build rather than recorded as
settled -- if the city ever collapses these to one City Hall line, that line
must stop being presented as seven direct lines.

Usage:
    python3 ia/scripts/dsm_council_scraper.py     # refresh the cache
    python3 ia/scripts/build_dsm_council.py
    python3 ia/scripts/build_dsm_council.py --check
"""

import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache",
                     "dsm_council.json")
OUT_NAME = "dsm-council-members.json"

WARDS_LAYER = ("https://services.arcgis.com/HT7H9QGiZQoRJDpJ/arcgis/rest/services/"
               "Wards_view/FeatureServer/0")

EXPECT_WARDS = [1, 2, 3, 4]
EXPECT_AT_LARGE = 2
EXPECT_SEATS = 7

PHONE_RE = re.compile(r"^\(\d{3}\)\s\d{3}-\d{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


def load_cache():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except OSError as e:
        raise RuntimeError("no scraper cache at %s (%s) -- run "
                           "ia/scripts/dsm_council_scraper.py first" % (CACHE, e))


def fetch_witness():
    """ward number -> (name as the polygon carries it, e-mail)."""
    url = ("%s/query?where=1%%3D1&outFields=WardNbr,PersonFName,PersonMName,"
           "PersonLName,PersonNameSuffix,EMail&returnGeometry=false&f=json" % WARDS_LAYER)
    raw = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "120",
         "-H", "User-Agent: districtry/1.0 (+https://districtry.com/ia/)", url],
        check=True, capture_output=True).stdout
    feats = json.loads(raw).get("features", [])
    out = {}
    for f in feats:
        a = f["attributes"]
        bits = [a.get("PersonFName"), a.get("PersonMName"), a.get("PersonLName"),
                a.get("PersonNameSuffix")]
        name = " ".join(b.strip() for b in bits if b and b.strip())
        out[int(a["WardNbr"])] = (name, (a.get("EMail") or "").strip())
    if sorted(out) != EXPECT_WARDS:
        raise RuntimeError("the Wards layer carries wards %s, expected %s"
                           % (sorted(out), EXPECT_WARDS))
    return out


def name_key(name):
    """(first token, last token), lowercased and stripped of punctuation.

    The two publishers do not spell a name identically: the council page
    prints "Rob X. Barron" where the polygon carries PersonFName "Rob" and
    PersonLName "Barron" with no middle name at all. Comparing whole strings
    would fail on a difference that is not a disagreement, so the witness is
    the first and last token -- which still catches a different PERSON, which
    is the thing being witnessed.
    """
    toks = [re.sub(r"[^A-Za-z'-]", "", t) for t in name.split()]
    toks = [t for t in toks if t]
    if not toks:
        return ()
    return (toks[0].lower(), toks[-1].lower())


def person(rec, badge):
    out = {"name": rec["name"], "seat": badge}
    for key in ("phone", "email", "elected", "termExpires"):
        if rec.get(key):
            out[key] = rec[key]
    return out


def main():
    check_only = "--check" in sys.argv[1:]
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)

    cache = load_cache()
    wards_in = cache.get("wards") or {}
    at_large_in = cache.get("atLarge") or []
    mayor_in = cache.get("mayor")

    if sorted(int(k) for k in wards_in) != EXPECT_WARDS:
        raise RuntimeError("the cache names wards %s, expected %s"
                           % (sorted(wards_in), EXPECT_WARDS))
    if len(at_large_in) != EXPECT_AT_LARGE or not mayor_in:
        raise RuntimeError("the cache names %d at-large members and %s mayor, "
                           "expected %d and one"
                           % (len(at_large_in), "no" if not mayor_in else "a",
                              EXPECT_AT_LARGE))

    # --- the cross-witness -------------------------------------------------
    witness = fetch_witness()
    for num in EXPECT_WARDS:
        page = wards_in[str(num)]
        poly_name, poly_email = witness[num]
        if name_key(page["name"]) != name_key(poly_name):
            raise RuntimeError(
                "Ward %d: the council page names %r and the city's own Wards "
                "layer carries %r. Two City of Des Moines publishers disagree "
                "about who holds a seat -- read both before shipping either."
                % (num, page["name"], poly_name))
        page_email = (page.get("email") or "").lower()
        if poly_email and page_email and poly_email.lower() != page_email:
            raise RuntimeError(
                "Ward %d: the council page gives %s and the Wards layer gives %s"
                % (num, page.get("email"), poly_email))
    print("  witness: all 4 ward members agree with the city's own Wards layer",
          file=sys.stderr)

    # --- shape -------------------------------------------------------------
    wards = {str(n): person(wards_in[str(n)], "Ward %d" % n) for n in EXPECT_WARDS}
    citywide = [person(mayor_in, "Mayor")]
    citywide += [person(r, "At-Large") for r in at_large_in]

    everyone = list(wards.values()) + citywide
    if len(everyone) != EXPECT_SEATS:
        raise RuntimeError("assembled %d seats, expected %d" % (len(everyone), EXPECT_SEATS))

    for rec in everyone:
        if rec.get("phone") and not PHONE_RE.match(rec["phone"]):
            raise RuntimeError("%s carries phone %r, which is not the (NNN) NNN-NNNN "
                               "shape the city publishes" % (rec["name"], rec["phone"]))
        if rec.get("email") and not EMAIL_RE.match(rec["email"]):
            raise RuntimeError("%s carries e-mail %r" % (rec["name"], rec["email"]))

    # --- floors: a field that stops being published must not ship empty ----
    phones = [r["phone"] for r in everyone if r.get("phone")]
    emails = [r["email"] for r in everyone if r.get("email")]
    if len(phones) != EXPECT_SEATS or len(emails) != EXPECT_SEATS:
        raise RuntimeError("%d of %d seats carry a phone and %d an e-mail; the city "
                           "publishes both for all seven, so a shortfall is the page "
                           "changing shape" % (len(phones), EXPECT_SEATS, len(emails)))

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

    print("dsm-council-members: %d seats (%d ward, %d citywide), %d distinct phones, "
          "%d e-mails" % (EXPECT_SEATS, len(wards), len(citywide), len(distinct),
                          len(emails)), file=sys.stderr)

    if check_only:
        try:
            with open(out_path) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("%s is missing (%s)" % (OUT_NAME, e))
        if shipped != payload:
            raise RuntimeError("data/app/%s has drifted from the cache. Re-run: "
                               "python3 ia/scripts/build_dsm_council.py" % OUT_NAME)
        print("check: shipped roster matches the cache", file=sys.stderr)
        return

    with open(out_path, "w") as f:
        f.write(payload)
    print("wrote data/app/%s" % OUT_NAME, file=sys.stderr)


if __name__ == "__main__":
    main()

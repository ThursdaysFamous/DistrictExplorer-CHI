#!/usr/bin/env python3
"""
Scrape stage 1: the elected officials of the Iowa cities whose own pages a
machine can read, cached for build_ia_city_officials.py (stage 2).

THIS IS A SHORT LIST ON PURPOSE, AND THE MEASUREMENT BEHIND IT IS THE POINT.
On 2026-09-04 all 532 Iowa cities that publish a website were swept for a
council roster. SIXTEEN yielded one; five of those cleared every check. That
is 1.7% of Iowa's 939 cities, and 407 of those cities publish no website at
all, which is the ceiling before any markup question is asked. The full
measurement lives in the `ia-municipal-officeholders` gap record's blocker.

So this file is NOT the beginning of a statewide roster and must never be
described as one. It is five cities that happen to publish readably, added
because a reader in one of them is better served than by a card that names
nobody -- and the gap stays open for the other 932 (939 less these five, Des Moines
and Waterloo, whose ward cards name theirs).

EVERY CITY HERE IS AT-LARGE, WHICH IS WHY NO LAYER SHIPS WITH THEM.
All five elect a mayor plus five council members, none of them by ward
(measured: not one carries a ward or district in its published role). The
fleet's at-large rule -- "a body elected by the whole unit adds zero
point-discrimination; it rides the unit's identity card, never a polygon
layer" -- puts them on the City card. Des Moines and Waterloo are the two
Iowa cities that DO elect by ward, and they are the `city-ward` layer.

TWO CONVENTIONS, AND THE PLATFORM DOES NOT PREDICT WHICH
----------------------------------------------------------
Four of the five write `Name, Role`; Tiffin writes `Role: Name`. That split
is not a property of the content system: Des Moines, Waterloo and Norwalk all
run the SAME system and need three different parsers. So each city carries its
convention explicitly in CITIES below rather than having it guessed, and a
city whose page changes convention fails its count gate rather than silently
returning nothing.

WHAT EACH CITY'S GATE IS
-------------------------
`seats` is what the city itself publishes, counted at first build, and the
scrape refuses on any other number. It is a measurement of the page, not a
target: Iowa Code 372.4 seats a mayor and five council members in the
mayor-council cities here, and all five pages agree, but the gate is the page.

A NAME MUST NOT APPEAR TWICE. That is the Waterloo lesson, earned on a city
NOT in this list: its page repeats every member in a bio-link anchor, two of
those anchors disagree with the member's own line, and one is a misspelling
unique enough to survive a dedupe. A plausible seat count does NOT catch it --
Waterloo parses to eight council members, which is an entirely ordinary
council. The duplicate check is what catches it, so it runs here on every city.

Usage:
    python3 ia/scripts/ia_city_officials_scraper.py
"""

import html as html_mod
import json
import os
import re
import sys

import requests

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
OUT_PATH = os.path.join(CACHE_DIR, "ia_city_officials.json")
HEADERS = {"User-Agent": "districtry/1.0 (+https://districtry.com/ia/)",
           "Accept": "text/html,application/xhtml+xml"}

# geoid -> the city's own council page, its naming convention, and the number
# of seats ITS OWN PAGE publishes. Keyed by 7-digit TIGER place GEOID, the key
# the City card already reads.
CITIES = [
    {"geoid": "1953985", "name": "Moravia", "convention": "fwd", "seats": 6,
     "url": "https://moraviaiowa.com/city-services/council-mayor/"},
    {"geoid": "1957675", "name": "Norwalk", "convention": "fwd", "seats": 6,
     "url": "https://www.norwalk.iowa.gov/government/mayor___city_council.php"},
    {"geoid": "1961230", "name": "Palo", "convention": "fwd", "seats": 6,
     "url": "https://cityofpalo.com/council"},
    {"geoid": "1967440", "name": "Riverside", "convention": "fwd", "seats": 6,
     "url": "https://riversideiowa.gov/government/mayor_and_council/"},
    {"geoid": "1978060", "name": "Tiffin", "convention": "rev", "seats": 6,
     "url": "https://www.tiffin-iowa.org/city_government/city_council.php"},
]

ROLE = (r"(?:Mayor\s*Pro[-\s]?Tem(?:pore)?|Mayor|Council\s*(?:Member|man|woman|person)"
        r"(?:\s*At[-\s]?Large)?|At[-\s]?Large\s*Council\s*\w*)")
NAME = r"[A-Z][A-Za-z.'\-]*(?:\s+[A-Za-z.'\-]+){0,3}"
FWD = re.compile(r"^(?P<name>%s)\s*[,–-]\s*(?P<role>%s)\b" % (NAME, ROLE), re.I)
REV = re.compile(r"^(?P<role>%s)\s*[:\-–]\s*(?P<name>%s)\s*$" % (ROLE, NAME), re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
MAYOR_ONLY = re.compile(r"(?i)^mayor$")


def text_lines(page):
    """Tags to text, with <br>, <hr> and block ends becoming LINE BREAKS first.

    Order matters, as it does in every scraper in this instance: strip tags
    first and a member's name, phone and e-mail collapse into one unsplittable
    string on the pages that separate them with <br> alone.

    A mailto anchor is rewritten to `text address` BEFORE tags are stripped.
    Wrapping the address in angle brackets instead -- the obvious thing -- makes
    the tag stripper eat it as though it were a tag, which silently returned
    zero e-mails for a whole city while the names parsed perfectly.
    """
    t = re.sub(r"(?is)<(script|style|nav|footer)[^>]*>.*?</\1>", " ", page)
    t = re.sub(r'<a[^>]*href="mailto:([^"?]+)[^"]*"[^>]*>(.*?)</a>', r" \2 \1 ", t,
               flags=re.I | re.S)
    t = re.sub(r"<br\s*/?>|<hr\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|h[1-6]|div|li|td|tr|strong|span|b|em|a|dt|dd)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_mod.unescape(t).replace("\xa0", " ")
    return [re.sub(r"\s+", " ", line).strip() for line in t.split("\n") if line.strip()]


def parse(page, convention):
    lines = text_lines(page)
    rx = FWD if convention == "fwd" else REV
    hits = [(i, m) for i, line in enumerate(lines) for m in [rx.match(line)] if m]
    out = []
    for n, (i, m) in enumerate(hits):
        # bound the scan at the NEXT record so a footer cannot donate a phone
        # number to the last member
        stop = hits[n + 1][0] if n + 1 < len(hits) else min(len(lines), i + 12)
        blob = " ".join(lines[i:stop])
        email = EMAIL.search(blob)
        phone = PHONE.search(blob)
        rec = {"name": m.group("name").strip(), "role": m.group("role").strip()}
        if email:
            rec["email"] = email.group(0)
        if phone:
            rec["phone"] = phone.group(0)
        out.append(rec)
    return out


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    payload = {}
    for city in CITIES:
        r = requests.get(city["url"], headers=HEADERS, timeout=45)
        r.raise_for_status()
        recs = parse(r.text, city["convention"])

        if len(recs) != city["seats"]:
            raise SystemExit(
                "%s: parsed %d officials, its page publishes %d. That is either the "
                "page changing shape or the city changing its council, and both need "
                "reading before anything ships." % (city["name"], len(recs), city["seats"]))

        names = [x["name"] for x in recs]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise SystemExit(
                "%s: these names appear more than once: %s. A repeated name means the "
                "page now names each member twice -- and the second naming is not always "
                "spelled the same, which is how a misspelt councilman would ship. Read "
                "the page." % (city["name"], ", ".join(dupes)))

        mayors = [x for x in recs if MAYOR_ONLY.match(x["role"])]
        if len(mayors) != 1:
            raise SystemExit(
                "%s: found %d plain 'Mayor' records, expected exactly one (a Mayor Pro "
                "Tem is a council member and is not one)." % (city["name"], len(mayors)))

        missing = [x["name"] for x in recs if not x.get("email")]
        if missing:
            raise SystemExit(
                "%s: no e-mail for %s. Every one of this city's published officials "
                "carried one at first build, so a shortfall is the page changing rather "
                "than a person declining to publish." % (city["name"], ", ".join(missing)))

        payload[city["geoid"]] = {"city": city["name"], "sourceUrl": city["url"],
                                  "members": recs}
        print("  %-11s %d officials, %d e-mails, %d phones"
              % (city["name"], len(recs), sum(1 for x in recs if x.get("email")),
                 sum(1 for x in recs if x.get("phone"))), file=sys.stderr)

    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print("ia-city-officials: %d cities cached to %s" % (len(payload), OUT_PATH),
          file=sys.stderr)


if __name__ == "__main__":
    main()

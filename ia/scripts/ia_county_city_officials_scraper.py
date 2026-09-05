#!/usr/bin/env python3
"""
Scrape the CITY-OFFICIALS pages Iowa counties publish for the cities in them.

THE ROUTE, AND WHY IT WAS SITTING UNREAD
------------------------------------------
`ia-municipal-officeholders`'s own blocker named exactly one route as NOT YET
PROBED: "whether any of the 99 county auditors -- Iowa's statutory
commissioners of elections under Iowa Code 47.2, and the natural upstream of
any state clerk file -- publishes a city-clerk list. Seven large counties'
HOME pages were fetched and none mentions a city clerk, which is what a
homepage looks like either way and settles nothing."

It does. Eleven counties publish, for every city inside them, the city's own
address and phone, its CITY CLERK by name, its MAYOR, and the whole CITY
COUNCIL -- each with a term end, a term length, and often a phone and an
e-mail. That is the WEC-shaped answer Iowa was assumed not to have, arriving
one county at a time instead of from one state office.

Probed 2026-09-05 with python-requests under a districtry research
user-agent: all 99 county domains, taken from the auditor e-mail already
shipped in `ia/data/app/ia-county-auditors.json` (99 addresses, 99 distinct
domains, none permuted from a county name). 71 answered; the other 28 are
recorded in the gap blocker BY WHO REFUSED, because seven of them are this
sandbox's own egress proxy and not the county at all.

THREE TRAPS, ALL IN THE MARKUP AND ALL SILENT
-----------------------------------------------
1. THE ROLE IS INSIDE THE NAME'S OWN DIV for the clerk and the mayor --
   `<div class="offName"><b>City Clerk </b><br>Sarah Miller</div>` -- while a
   council member's row carries no <b> and takes its role from the nearest
   preceding `div.positionTitle`. Read the text flat and the clerk is a person
   called "City Clerk Sarah Miller"; take positionTitle for every row and the
   clerk and the mayor are both filed as council members. That is the Franklin
   trap in both directions at once, so the role is read STRUCTURALLY here.
2. THE SEAT FOLLOWS A <br/> INSIDE THE SAME DIV. 109 of the officials carry
   `Ward 1` or `At Large` after the break -- so these counties publish which
   ward a council member holds, which no other Iowa source does -- and a
   parser that takes the div's text ships people whose surname is "Ward".
3. EVERY mailto: HREF IS EMPTY. The address is the link TEXT. An href-keyed
   scrape returns an e-mail for nobody and every count guard still passes,
   which is exactly how Brown County's seven addresses went out silently.

A vacancy annotation ("Appointed to Fill Vacancy until Election") sits in its
own `div.officialInfoDescription` behind an info icon; it is a real status and
is kept, but it is never part of the name.

WHAT THIS SCRIPT DOES NOT DECIDE. Whether a county's page is CURRENT is the
builder's question, not this one -- this emits what each page says, including
the three counties whose own term dates show they have not been touched since
the November 2023 election. Measuring that is `build_ia_county_city_officials.py`.
"""
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
OUT_PATH = os.path.join(CACHE_DIR, "ia_county_city_officials.json")
HEADERS = {"User-Agent": "districtry/1.0 (+https://districtry.com/ia/)",
           "Accept": "text/html,application/xhtml+xml"}
TIMEOUT = 45

# The eleven counties whose city-officials page this sweep found, PINNED rather
# than re-discovered: a county that redesigns its site should fail loudly here,
# not disappear from a roster nobody is watching. Re-run the sweep in the gap
# blocker to look for new ones; a twelfth county is an entry, not a code change.
COUNTIES = [
    ("19015", "Boone", "https://boonecounty.iowa.gov/about/elected_officials/city/"),
    ("19033", "Cerro Gordo", "https://cerrogordo.gov/about/elected_officials/city/"),
    ("19047", "Crawford", "https://www.crawfordcounty.iowa.gov/about/elected_officials/city/"),
    ("19095", "Iowa", "https://iowacounty.iowa.gov/about/elected_officials/city/"),
    ("19097", "Jackson", "https://jacksoncounty.iowa.gov/about/elected_officials/city/"),
    ("19107", "Keokuk", "https://keokukcounty.iowa.gov/about/elected_officials/city/"),
    ("19125", "Marion", "https://www.marioncountyiowa.gov/about/elected_officials/city/"),
    ("19139", "Muscatine", "https://muscatinecountyiowa.gov/about/elected_officials/city/"),
    ("19161", "Sac", "https://www.saccountyiowa.gov/about/elected_officials/city/"),
    ("19165", "Shelby", "https://shelbycounty.iowa.gov/about/elected_officials/city/"),
    ("19189", "Winnebago", "https://winnebagocountyiowa.gov/about/elected_officials/city/"),
]

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}")
TERM_ENDS = re.compile(r"Term Ends?:\s*(\d{4})", re.I)
TERM_LEN = re.compile(r"Term Length:\s*([\w ]+)", re.I)
# The seat as these pages write it, and nothing else -- a person whose surname
# is Ward must not become a seat.
SEAT = re.compile(r"^(?:Ward\s+\d+|At[- ]Large|District\s+\w+)$", re.I)


def flat(el):
    return re.sub(r"\s+", " ", el.get_text(" ")).strip() if el is not None else ""


def parse_off_name(nm):
    """Split div.offName into (role_or_None, name, seat_or_None, status_or_None).

    Order inside the div is: optional <b>Role</b>, the person's name, an
    optional status div behind an info icon, a <br/>, then the seat.
    """
    role = None
    b = nm.find("b")
    if b is not None:
        role = flat(b).rstrip(": ").strip() or None
        b.extract()
    status = None
    sd = nm.select_one("div.officialInfoDescription")
    if sd is not None:
        status = flat(sd) or None
        sd.extract()
    for a in nm.select("a.officialInfoDescriptionInfo"):
        a.extract()
    # Everything left splits on the <br/>: name first, seat after.
    parts, buf = [], []
    for node in nm.children:
        if getattr(node, "name", None) == "br":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(node.get_text(" ") if hasattr(node, "get_text")
                       else str(node))
    parts.append("".join(buf))
    parts = [re.sub(r"\s+", " ", p).strip() for p in parts]
    parts = [p for p in parts if p]
    name = parts[0] if parts else ""
    seat = None
    for p in parts[1:]:
        if SEAT.match(p):
            seat = p
            break
    return role, name, seat, status


def parse_city(div):
    name = flat(div.find(["h2", "h3"])) or None
    info = div.select_one("div.cityInfo")
    addr = flat(info.select_one("div.cityContact")) if info else ""
    numbers = flat(info.select_one("div.cityContact.numbers")) if info else ""
    officials, heading = [], None
    for el in div.find_all("div", class_=True):
        cl = el.get("class")
        if "positionTitle" in cl:
            heading = flat(el) or None
            continue
        if "offRow" not in cl:
            continue
        nm = el.select_one("div.offName")
        if nm is None:
            continue
        role, person, seat, status = parse_off_name(nm)
        if not person:
            continue
        contact = flat(el.select_one("div.offContact"))
        term = flat(el.select_one("div.offTerm"))
        em = EMAIL.search(contact)
        ph = PHONE.search(contact)
        te = TERM_ENDS.search(term)
        tl = TERM_LEN.search(term)
        officials.append({
            "role": role or heading,
            "name": person,
            "seat": seat,
            "status": status,
            "email": em.group(0) if em else None,
            "phone": ph.group(0) if ph else None,
            "termEnds": te.group(1) if te else None,
            "termLength": tl.group(1).strip() if tl else None,
        })
    return {"city": name, "cityAddress": addr or None,
            "cityPhone": (PHONE.search(numbers).group(0)
                          if PHONE.search(numbers) else None),
            "officials": officials}


def scrape(session, url):
    r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    cities = [parse_city(d) for d in soup.select("div.filterDiv")]
    return [c for c in cities if c["city"] and c["officials"]]


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    session = requests.Session()
    out, failed = {}, []
    for fips, county, url in COUNTIES:
        try:
            cities = scrape(session, url)
        except Exception as exc:
            failed.append((county, "%s: %s" % (type(exc).__name__, exc)))
            print("  %-14s FAILED %s" % (county, exc), file=sys.stderr)
            continue
        if not cities:
            failed.append((county, "page parsed to zero cities"))
            print("  %-14s parsed to ZERO cities" % county, file=sys.stderr)
            continue
        n = sum(len(c["officials"]) for c in cities)
        out[fips] = {"county": county, "sourceUrl": url, "cities": cities}
        print("  %-14s cities=%-3d officials=%-4d seats=%-4d emails=%-4d" % (
            county, len(cities), n,
            sum(1 for c in cities for o in c["officials"] if o["seat"]),
            sum(1 for c in cities for o in c["officials"] if o["email"])))
        time.sleep(0.5)
    if failed:
        print("\n%d county page(s) did not yield:" % len(failed), file=sys.stderr)
        for county, why in failed:
            print("  %-14s %s" % (county, why), file=sys.stderr)
    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("\nwrote %s (%d counties, %d cities, %d officials)" % (
        OUT_PATH, len(out),
        sum(len(v["cities"]) for v in out.values()),
        sum(len(c["officials"]) for v in out.values() for c in v["cities"])))
    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main())

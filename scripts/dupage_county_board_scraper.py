#!/usr/bin/env python3
"""
Scrape the DuPage County Board members directory into raw roster records.

Stage 1 of the two-stage pipeline (scripts/build_dupage_county_board_roster.py
is stage 2), mirroring the Will County board scraper. Unlike Will's, DuPage's
directory (dupagecounty.gov, a Revize CMS "business directory") is plain
server-rendered HTML with no JS challenge, so requests + BeautifulSoup suffice.

Each member is a <div class="rz-business-block"> carrying an <h2> name, an
inline "District N" field, term dates, and a "More about <name>" link to the
member's detail page; the detail page carries a member-specific mailto: address
when the county publishes one. The Board Chair is elected countywide (no
district) and is emitted with district=null, role="Chair".

Names and emails are read verbatim from the county's own pages — never guessed.
Phone is deliberately omitted: the detail pages show the general County Board
office line (630-407-6500) on every member, so a scraped "phone" would be
boilerplate, not the member's own — an honest null beats a misleading number.

Usage:
    python3 dupage_county_board_scraper.py [output.json]   # default: stdout
"""

import json
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://www.dupagecounty.gov"
LIST_URL = BASE + "/government/county_board/county_board_members/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; districtexplorer-roster/1.0)"}
# mailto: local-parts that are site chrome / role inboxes, not a member address.
BOILERPLATE_EMAIL = ("noreply", "webpageupdate", "bootstrap", "webmaster", "info@")


def fetch(url):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r.text


def abs_url(href):
    href = (href or "").strip()
    if not href:
        return None
    if href.startswith("http"):
        return href
    return BASE + "/" + href.lstrip("/")


def member_email(html):
    """The member's own @dupagecounty.gov address from a mailto: link, if any."""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if h.lower().startswith("mailto:"):
            addr = h[7:].split("?")[0].strip()
            low = addr.lower()
            if low.endswith("@dupagecounty.gov") and not low.startswith(BOILERPLATE_EMAIL):
                return addr
    return None


def scrape():
    soup = BeautifulSoup(fetch(LIST_URL), "html.parser")
    blocks = soup.find_all("div", class_="rz-business-block")
    records = []
    for b in blocks:
        h2 = b.find("h2")
        if not h2:
            continue
        raw_name = h2.get_text(" ", strip=True)
        is_chair = bool(re.search(r"chair", raw_name, re.I))
        name = re.sub(r"\s*[–—-]\s*chair\s*$", "", raw_name, flags=re.I).strip()
        if not name:
            continue
        text = b.get_text(" ", strip=True)
        dm = re.search(r"District\s+([1-6])\b", text)
        district = int(dm.group(1)) if (dm and not is_chair) else None
        link = b.find("a", href=re.compile(r"/[A-Za-z]+\.php", re.I))
        url = abs_url(link["href"]) if link else None
        email = None
        if url:
            try:
                email = member_email(fetch(url))
                time.sleep(0.5)  # be polite to the county's server
            except requests.RequestException as e:
                print("WARN: detail fetch failed for %s (%s)" % (name, e), file=sys.stderr)
        rec = {"name": name, "district": district,
               "role": "Chair" if is_chair else "Member", "url": url}
        if email:
            rec["email"] = email
        records.append(rec)
    return records


def main():
    records = scrape()
    n_dist = sum(1 for r in records if r["district"] is not None)
    n_chair = sum(1 for r in records if r["role"] == "Chair")
    n_email = sum(1 for r in records if r.get("email"))
    print("scraped %d records (%d district members, %d chair, %d emails)"
          % (len(records), n_dist, n_chair, n_email), file=sys.stderr)
    out = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    if len(sys.argv) >= 2:
        with open(sys.argv[1], "w") as f:
            f.write(out)
        print("wrote %s" % sys.argv[1], file=sys.stderr)
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()

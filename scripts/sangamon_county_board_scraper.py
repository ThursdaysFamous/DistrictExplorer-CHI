#!/usr/bin/env python3
"""
Stage 1 of the Sangamon County Board roster pipeline: walk the county's 29
per-district member pages into raw JSON for
build_sangamon_county_board_roster.py.

WHY 29 PAGE FETCHES AND NOT ONE: the county's board GIS
(CountyBoardDistricts2020_WithURLs) carries no member name — what it carries is
a `DistrictMemberURL` per district, pointing at exactly these pages. So the join
key is published and exact; the names simply live one hop away. This walks the
same URLs the GIS names, in district order, rather than guessing a URL pattern.

NEITHER THE TAGS NOR THE LABELS ARE RELIABLE, and both cost a rewrite to
discover. The member block is an <h3> on most pages, a plain <p> on district 21,
and a <p><span style="font-size:130%"> on district 12 — so keying on <h3> silently
lost two members. On district 4 the <h3> also wraps the address, so keying on the
element's whole text produced the name "Lanae Clarke (R) 1523 Horse Creek Trl
Pawnee, IL 62558". Labels vary the same way: some pages write "Email:" and "C:",
others print a bare address and phone, and one has no e-mail at all.

What IS stable across all 29 is the ORDER: a "Term:" paragraph, then a block
whose FIRST LINE is "Name (Party)" and whose remaining lines are the address and
contact. So the parse anchors on Term, takes the first line after it as the name,
and matches contact fields by SHAPE (an e-mail is an e-mail, a phone is a phone)
rather than by position or label. A missing field is left null instead of being
filled from whatever line happened to sit there.

The street addresses are RESIDENCES and are deliberately not collected, the same
call the McHenry and Livingston rosters made. The published phone is collected:
the county prints it as the way to reach that member.

Usage:
    python3 sangamon_county_board_scraper.py [output.json]
"""

import html
import json
import re
import sys
import time

import requests

BASE = "https://sangamonil.gov/departments/a-c/county-board/districts/members/district-%d"
SOURCE_URL = "https://sangamonil.gov/departments/a-c/county-board/districts"
DISTRICTS = range(1, 30)  # 29 single-member districts

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
}
REQUEST_TIMEOUT = 45
PAUSE_SECONDS = 0.6  # 29 sequential fetches; be a polite guest on a county server

SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
# Line-level structure matters here, so block-enders become newlines before tags
# are stripped — that is what keeps "Name (Party)" separate from the address that
# shares its element on district 4.
BREAK_RE = re.compile(r"<br[^>]*>|</p>|</h[1-6]>|</div>|</li>", re.I)
TERM_RE = re.compile(r"Term:\s*([0-9]{4}\s*-\s*[0-9]{4})")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(\d{3})[.\-\s]?(\d{3})[.\-\s]?(\d{4})\b")
PARTY_RE = re.compile(r"\(([RDI])\)\s*$")
# Curly quotes and the nickname convention ("Harry “Tom” Fraase, Jr.") are kept
# as published — a name is rendered as its owner's government publishes it.
QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def text_of(fragment):
    s = html.unescape(TAG_RE.sub(" ", fragment))
    for bad, good in QUOTES.items():
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def lines_after_term(body):
    """Content lines following the 'Term:' paragraph, in document order."""
    marker = body.find("Term:")
    if marker < 0:
        return []
    tail = BREAK_RE.sub("\n", body[marker:])
    out = []
    for raw in TAG_RE.sub(" ", tail).split("\n"):
        line = text_of(raw)
        if line and not line.startswith("Term:"):
            out.append(line)
    return out


def parse(page, district):
    body = SCRIPT_RE.sub("", page)
    rec = {"district": str(district)}

    for line in lines_after_term(body):
        party = PARTY_RE.search(line)
        if not party:
            # The name line is the one carrying the party marker. Nothing else on
            # these pages does, so this never has to guess which line is a name.
            continue
        rec["party"] = party.group(1)
        rec["name"] = PARTY_RE.sub("", line).strip(" ,")
        break

    flat = text_of(BREAK_RE.sub(" ", body))
    term = TERM_RE.search(flat)
    if term:
        rec["term"] = re.sub(r"\s*-\s*", "-", term.group(1))
    email = EMAIL_RE.search(flat)
    if email:
        rec["email"] = email.group(0)
    phone = PHONE_RE.search(flat)
    if phone:
        rec["phone"] = "-".join(phone.groups())
    rec["url"] = BASE % district
    return rec


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "sangamon_county_board_raw.json"
    session = requests.Session()
    records = []
    for district in DISTRICTS:
        url = BASE % district
        try:
            resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print("sangamon-scraper: district %d failed (%s) — skipped" % (district, exc),
                  file=sys.stderr)
            time.sleep(PAUSE_SECONDS)
            continue
        rec = parse(resp.text, district)
        if rec.get("name"):
            records.append(rec)
        else:
            print("sangamon-scraper: district %d had no member heading" % district,
                  file=sys.stderr)
        time.sleep(PAUSE_SECONDS)

    if not records:
        print("sangamon-scraper: FAIL — parsed 0 members; the page shape changed",
              file=sys.stderr)
        sys.exit(1)
    payload = {"source_url": SOURCE_URL, "records": records}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("sangamon-scraper: wrote %s — %d/%d districts, %d e-mails, %d phones, %d parties"
          % (out_path, len(records), len(list(DISTRICTS)),
             sum(1 for r in records if r.get("email")),
             sum(1 for r in records if r.get("phone")),
             sum(1 for r in records if r.get("party"))))


if __name__ == "__main__":
    main()

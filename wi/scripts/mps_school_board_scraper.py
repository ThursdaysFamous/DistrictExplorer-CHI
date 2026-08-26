#!/usr/bin/env python3
"""
Scrape the Milwaukee Board of School Directors from the district's own
directors page. Stage 1 of the pair; build_mps_school_board_roster.py writes
data/app/mps-school-board-members.json.

THE PAGE (milwaukeepublicschools.org/about/board/directors): one h3 per seat
in the real DOM — "At Large: NAME (President)" plus "District N: NAME" for
districts 1-8 — never the page's inline-JSON duplicates, which repeat the
same strings in script blobs the DOM read must not double-count (this parse
anchors on the <h3> tags alone). Each seat's block carries the term facts
("First elected … Term expires: April 2027") and an "Email Director X" link,
which is a JustFOIA contact FORM, not a mailto — the district's chosen
contact route, shipped as the member's contact link rather than an invented
address. The Board's office phone and e-mail come from the same page's Board
Contact Information block.

THE WITNESS: the board INDEX page (/about/board) lists the standing
committees with their member directors by surname. Every committee surname
must fold-match a roster surname — two surfaces the district maintains
separately agreeing on who sits on the board, so a stale directors page (or
a reshaped parse) fails loudly instead of shipping quietly.
"""

import html as html_mod
import json
import os
import re
import ssl
import sys
import unicodedata
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, ".cache", "mps_school_board_raw.json")

DIRECTORS_URL = "https://www.milwaukeepublicschools.org/about/board/directors"
INDEX_URL = "https://www.milwaukeepublicschools.org/about/board"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60,
                                context=ssl.create_default_context()) as r:
        return r.read().decode("utf-8", "replace")


def surname_fold(name):
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    toks = [t for t in re.split(r"[^a-z]+", s) if len(t) > 1 and t not in
            ("jr", "sr", "ii", "iii", "dr")]
    return toks[-1] if toks else ""


def parse_directors(page):
    members = {}
    office = {}
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|<h2|\Z)", page, re.S):
        head = html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        head = re.sub(r"\s+", " ", head)
        seat = re.match(r"^(At[- ]Large|District (\d)):\s*(.+?)(?:\s*\((.+?)\))?$", head)
        if not seat:
            continue
        key = "AL" if seat.group(1).lower().startswith("at") else seat.group(2)
        name = seat.group(3).strip()
        entry = {"name": name}
        if seat.group(4):
            entry["role"] = seat.group(4).strip()
        body = m.group(2)
        t = re.search(r"Term expires:\s*(?:<[^>]+>\s*)*([A-Z][a-z]+ \d{4})",
                      re.sub(r"&nbsp;", " ", body))
        if t:
            entry["termExpires"] = t.group(1)
        c = re.search(r'href="(https://[^"]*justfoia\.com[^"]+)"', body)
        if c:
            entry["contactUrl"] = c.group(1)
        if key in members:
            raise SystemExit("directors page lists seat %r twice" % key)
        members[key] = entry
    # "Phone:&nbsp;</strong>(414) …" — the entity sits INSIDE the strong tag
    ph = re.search(r"Board Contact Information.*?Phone:(?:&nbsp;|\s|<[^>]+>)*([\d() \-]{10,16})",
                   page, re.S)
    em = re.search(r"Board Contact Information.*?Email:.*?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)",
                   page, re.S)
    if ph:
        office["phone"] = ph.group(1).strip()
    if em:
        office["email"] = em.group(1)
    return members, office


def committee_witness(index_page, members):
    """Every 'Director SURNAME' the index page's committee lists name must be
    a surname on the roster."""
    surnames = {surname_fold(m["name"]) for m in members.values()}
    seen = set()
    for m in re.finditer(r"Director\s+([A-Z][A-Za-z'’.\-]+)",
                         html_mod.unescape(re.sub(r"<[^>]+>", " ", index_page))):
        seen.add(surname_fold(m.group(1)))
    seen.discard("")
    stray = seen - surnames
    if stray:
        raise SystemExit("committee lists name director surname(s) %s absent from the "
                         "directors page — one of the two surfaces is stale"
                         % sorted(stray))
    if len(seen) < 5:
        raise SystemExit("committee witness read only %d director surnames — the "
                         "index page shape moved" % len(seen))
    return len(seen)


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT

    members, office = parse_directors(fetch(DIRECTORS_URL))
    expect = ["AL"] + [str(n) for n in range(1, 9)]
    if sorted(members) != sorted(expect):
        raise SystemExit("directors page names seats %s, expected at-large + "
                         "districts 1-8" % sorted(members))
    if not office.get("phone") or not office.get("email"):
        raise SystemExit("the Board Contact Information block did not parse "
                         "(phone %r, email %r)" % (office.get("phone"), office.get("email")))
    n_witness = committee_witness(fetch(INDEX_URL), members)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"members": members, "office": office,
                   "sourceUrl": DIRECTORS_URL}, f, indent=2, ensure_ascii=False)
    print("scraped 9 MPS directors (committee witness matched %d surnames) -> %s"
          % (n_witness, out_path))


if __name__ == "__main__":
    main()

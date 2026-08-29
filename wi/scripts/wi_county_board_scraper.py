#!/usr/bin/env python3
"""
Scrape county board supervisors from the 32 Wisconsin counties that publish a
district-keyed member list. Stage 1 of the pair; build_wi_county_board_roster.py
turns the intermediate JSON into data/app/county-board-members.json.

WHY ONLY THIRTY-TWO OF SEVENTY-TWO
----------------------------------
Wisconsin publishes county board DISTRICTS statewide (Wis. Stat. 5.15(4)(br)1,
see build_wi_supervisory_districts.py) and publishes the PEOPLE in them
nowhere: each county names its own supervisors, 72 different ways. Twenty-nine
pair a district with a person on a PAGE this file can read, Milwaukee and
Racine publish theirs as attributes on their own GIS layers, and Kenosha
publishes its in a DOCUMENT — the Clerk's own directory (all three shapes
below). The other 40 are not oversights and are recorded as such:

  * Ozaukee publishes district MAPS — a page per district with a PDF and no
    name on it anywhere. It was checked three pages deep. This file used to
    claim 23 counties; that count came from a sweep that tested district
    NUMBERS, and numbers are what a map index has.
  * Marinette publishes 29 of its 30 seats. District 26 is an unnumbered
    "VACANT SEAT" row in an alphabetical list, and assigning it by elimination
    would be an inference the county never wrote, so the county stays out.
  * The rest could not be read: 9 answer 403 to a datacenter client and hold
    it against browser headers (Marathon, La Crosse, Outagamie, Fond du Lac,
    Lafayette, Lincoln, Monroe, Rock, Sheboygan), Taylor sits behind an
    sgcaptcha challenge answering 202 (an access control, not an obstacle to
    route around), Forest does not resolve, and the remainder publish their
    members as PDFs, images or prose with no district column. That last
    clause is the load-bearing one and Kenosha is why: the disqualifier is
    "no district column", never "PDF". A document that pairs a district with
    a person is a source (see DOCUMENT_COUNTIES); one that lists names
    alphabetically is not, whatever it is served as.

NINE OF THOSE "UNREADABLE" COUNTIES WERE PUBLISHING ALL ALONG (2026-08-27)
--------------------------------------------------------------------------
Dane 37, Shawano 27, Juneau 21, Oneida 21, Richland 21, Kewaunee 20, Rusk 19,
Trempealeau 17 and Price 13 — 196 seats — were recorded here as publishing
nothing readable, and both causes were on this side of the wire.

The re-sweep was provoked by one county: build_wi_supervisory_districts.py's
docstring cites Trempealeau's own board page as the authority for its
seventeen seats, that page was never wired into this scraper, and a cold-ask
e-mail was being drafted to the county for a list it publishes.

  CAUSE ONE, THE READER. `DIST` needs the literal word "district" beside the
  number. A page that says it once in a COLUMN HEADER and then prints bare
  numerals in the cells is invisible to all three original readings — so
  Oneida, Price and Trempealeau were filed under "no district column" when
  having one is exactly why they could not be read. `_column` reads the cell.

  CAUSE TWO, THE SWEEP. It asked each COUNTY's site and never the BOARD's.
  Dane's 37 supervisors are on board.danecounty.gov, a different host from the
  countyofdane.com this project's own clerk file carries. ASK THE BOARD'S OWN
  HOST BEFORE RECORDING THAT A COUNTY PUBLISHES NOTHING.

KENOSHA WAS THE TENTH, AND ITS RECORD NAMED THE WRONG PAGE (2026-08-29)
------------------------------------------------------------------------
Kenosha sat in the "publishes district MAPS" bucket above for a month, and
that description is accurate — about /142/County-Board-Supervisor-Districts,
which is an index of 23 links to 23 PDF maps with nobody's name on it. It is
NOT the county's roster page. /113/County-Board-of-Supervisors is, and it
publishes all 23 seats as "District N" followed by the supervisor's name — the
plain `after` reading, resolving 23 of 23 with no new code. TWO SLUGS ONE WORD
APART, one of them a map index and one of them the answer: when a county's
record says "checked the board page", check WHICH board page.

The Clerk publishes MORE, in a document rather than on a page: the annual
Directory of Public Officials (a 107-page PDF) prints the same 23 districts
with a PHONE and an E-MAIL each, and marks the Chair and Vice-Chair on their
own rows. So Kenosha does not ride a pinned reading at all — it is the first
county here whose roster comes from a DOCUMENT, witnessed against a page (see
DOCUMENT_COUNTIES below), and the first to ship contact for its supervisors.

THE STABLE URL IS A COUNTY PAGE ID, NEVER THE DOCUMENT'S OWN ADDRESS. The PDF
lives at /DocumentCenter/View/<edition>/County-Directory, and <edition> changes
with each year's directory — that URL freezes on the 2026-2027 edition and
would go on being fetched, successfully, forever. /1018/County-Directory-PDF is
the county's own page for "the current directory" and 302s to whichever edition
is live, so the run log prints the edition it landed on and an edition change is
visible instead of silent.

THE READING DIRECTION IS PINNED PER COUNTY, NOT DETECTED
--------------------------------------------------------
Three page shapes carry the same information:

    same-line   "District #1 - Steve Sandstrom"      (Bayfield)
    before      "Jim Brown" then ": District 1"      (Green)
    after       "District 1" then "Tim Lauffer"      (Dunn)

`before` and `after` are the SAME EXTRACTION SHIFTED BY ONE, so a page read in
the wrong direction yields a full, plausible, entirely wrong roster: every
supervisor filed under their neighbour's district. Green County resolves 31 of
31 under both readings and they name different people. Detecting the direction
at runtime would mean a page tweak could silently flip it, so each county's
direction is PINNED here and a mismatch fails the county's count guard loudly
instead.

Two more shapes joined in the 2026-08-27 re-sweep, and both are pinned the
same way:

    column      a District COLUMN of bare numerals (Oneida, Price,
                Trempealeau) — see `_column`
    -strict     as before/after, but the scan STOPS at the next district line
                (Richland, Rusk, Shawano) — see `_windowed_strict`

The strict readings exist because a district whose own row yields no readable
name reaches past the next heading and takes ITS name: Rusk prints an INDEX of
nineteen bare "District #N" links above its roster, and Richland's rows end in
an e-mail address. Both filed one person under two districts, both were caught
by the duplicate-name guard below, and neither ships. They are a separate
strategy rather than a change to `_windowed` so the twenty counties already
shipping keep byte-identical behaviour.

A COUNTY THAT DOES NOT FULLY RESOLVE YIELDS NOTHING. Partial output is worse
than none here: a card showing 18 of 21 districts reads as a complete board
with three empty seats.

OFFICERS PUBLISHED ABOVE THE DISTRICT LIST (added 2026-08-27)
--------------------------------------------------------------
Seven counties name their chair and vice-chairs in a block of their own rather
than beside the member's district row, so `split_role` — which only sees a role
attached to the name it is reading — never reached them. That is not cosmetic:
the county card's board chair is reconciled weekly against this roster, and a
roster with NO marked chair makes the officer builder WITHHOLD the Blue Book's
chair rather than supersede it. Attaching those roles took Juneau's and
Winnebago's cards from a withheld chair to the right one (the book still had
Timothy Cottingham and Thomas J Egan; their counties say Jim Cauley and Frank
Frassetto), and cut the withheld count from three to one.

`attach_officer_roles` joins on a UNIQUE FULL NAME and prints every join. It
never overwrites a role a member's own row already carries, and it walks into
the same before/after ambiguity the rest of this file pins per county — see
its comment for the three cases and for Jefferson, which a forward-only first
draft filed one seat off.

Vacancies are DATA, not misses. Winnebago district 33 ("Vacant Vacant"),
Shawano 5, Oneida 1 and Rusk 3 and 13 are seats the counties themselves say
nobody holds; they ship as vacant, and a vacancy overrides any name the search
window happens to reach. `vacant_districts` only scans FORWARD from the word
"district", which is why the strict and column readings report their own:
Shawano prints "Vacant ." ABOVE its "- District 5", and a column page names no
district beside a seat at all.

Usage:
    python3 wi/scripts/wi_county_board_scraper.py [--out PATH] [--only FIPS]
"""

import html as html_lib
import io
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

# The one county whose roster is a DOCUMENT (see DOCUMENT_COUNTIES). Imported at
# module scope on purpose: scripts/validate_workflow_deps.py reads these imports
# and fails the merge if the weekly workflow's pip line does not install pypdf,
# which is the gate that keeps this file's one dependency honest.
from pypdf import PdfReader

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), ".cache", "wi_county_boards_raw.json")
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# (county FIPS, name as LTSB spells it, seats, reading direction, page)
COUNTIES = [
    ("55007", "Bayfield", 13, "same-line",
     "https://bayfieldcounty.wi.gov/295/Board-of-Supervisors"),
    ("55009", "Brown", 26, "before",
     "https://www.browncountywi.gov/government/county-board-of-supervisors/"),
    ("55013", "Burnett", 21, "same-line",
     "https://burnettcountywi.gov/264/Supervisors"),
    ("55033", "Dunn", 29, "after",
     "https://dunncountywi.gov/supervisors"),
    ("55035", "Eau Claire", 29, "same-line",
     "https://eauclairecounty.gov/board_of_supervisors/district_representatives.php"),
    ("55043", "Grant", 17, "same-line",
     "https://co.grant.wi.gov/"),
    ("55045", "Green", 31, "before",
     "https://greencountywi.org/164/County-Board-of-Supervisors"),
    ("55055", "Jefferson", 30, "same-line",
     "https://jeffersoncountywi.gov/county_government/county_board/county_board_information/index.php"),
    ("55077", "Marquette", 17, "before",
     "https://www.marquettecountywi.gov/government/county-board-supervisors/"),
    ("55095", "Polk", 15, "same-line",
     "https://www.polkcountywi.gov/government/county_board_of_supervisors/index.php"),
    ("55097", "Portage", 25, "before",
     "https://www.co.portage.wi.gov/171/County-Board"),
    ("55123", "Vernon", 19, "same-line",
     "https://www.vernoncountywi.gov/government/county_board_of_supervisors/index.php"),
    ("55125", "Vilas", 21, "after",
     "http://www.vilascountywi.gov/departments/administration___officials/county_board_members/index.php"),
    ("55127", "Walworth", 11, "before",
     "https://co.walworth.wi.us/534/Board-of-Supervisors"),
    ("55129", "Washburn", 21, "after",
     "https://co.washburn.wi.us/county-board-supervisors/"),
    ("55131", "Washington", 21, "same-line",
     "https://www.washcowisco.gov/departments/county_board"),
    ("55133", "Waukesha", 25, "same-line",
     "https://www.waukeshacounty.gov/waukesha-county-board/county-board-supervisors/"),
    ("55137", "Waushara", 11, "after",
     "https://www.wausharacountywi.gov/13370/county-board-of-supervisors"),
    ("55139", "Winnebago", 36, "after",
     "https://www.winnebagocountywi.gov/703"),
    ("55141", "Wood", 19, "after",
     "https://woodcountywi.gov/CountyBoard/"),
    # --- the 2026-08-27 re-sweep: ten counties that were publishing all along ---
    # Dane's list is on the BOARD's host, not the county's — the county site was
    # checked and board.danecounty.gov was not.
    ("55025", "Dane", 37, "after",
     "https://board.danecounty.gov/Supervisors"),
    ("55057", "Juneau", 21, "same-line",
     "https://www.co.juneau.wi.gov/government/county_board_supervisors/index.php"),
    ("55061", "Kewaunee", 20, "before",
     "https://www.kewauneeco.org/government/boards_and_committees/"),
    ("55085", "Oneida", 21, "column-after",
     "https://www.oneidacountywi.gov/government/cb/"),
    ("55099", "Price", 13, "column-after",
     "https://co.price.wi.us/319/County-Board"),
    ("55103", "Richland", 21, "after-strict",
     "https://richlandcountywi.gov/index.asp?SEC=DB387A4E-E124-4584-B32C-2C95880C63F0"),
    ("55107", "Rusk", 19, "after-strict",
     "https://ruskcounty.org/supervisors"),
    ("55115", "Shawano", 27, "before-strict",
     "https://www.co.shawano.wi.us/county_board/"),
    ("55121", "Trempealeau", 17, "column-before",
     "https://co.trempealeau.wi.us/government/agendas_minutes/standing_committees/"
     "trempealeau_county_board_of_supervisors.php"),]

# --- text shaping -------------------------------------------------------------
# nav is NOT boilerplate everywhere: Grant County publishes its entire board in
# the site navigation, as "District 1 (Gary Ranum)", so it is kept.
_DROP = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
_BREAK = re.compile(r"(?is)<br\s*/?>|</t[dh]>|</tr>|</p>|</li>|</div>|</h\d>|</a>|</span>|</strong>|</b>")
_TAG = re.compile(r"(?s)<[^>]+>")
_FRAGMENT = re.compile(r"[a-z]{1,2}")


def to_lines(page_html):
    h = _BREAK.sub("\n", _DROP.sub(" ", page_html))
    raw = [" ".join(html_lib.unescape(x).split()) for x in _TAG.sub(" ", h).split("\n")]
    out = []
    for x in raw:
        # Markup can strand a word's tail on its own line ("Peg Sheaffe" then
        # "r"); rejoin a short lowercase fragment onto the line above.
        if out and _FRAGMENT.fullmatch(x) and out[-1] and out[-1][-1].isalpha():
            out[-1] = out[-1] + x
        else:
            out.append(x)
    return [x for x in out if x]


# --- name / role / vacancy ----------------------------------------------------
DIST = re.compile(r"(?i)(?:^|[^a-z0-9])district\s*#?\s*(\d{1,2})(?:st|nd|rd|th)?\b")
BAD = re.compile(r"(?i)\b(district|ward|phone|email|map|town|city|village|county|term|"
                 r"expires|chair|vice|contact|supervisor|address|click|more|view|home|"
                 r"menu|search|board|committee|login|election|results|show|again)\b")
SUFFIX = re.compile(r"^(?:I{1,3}|IV|Jr\.?|Sr\.?)$", re.I)
LEAD = re.compile(r"^(?:supervisory|supervisor|county|board|member)\b[\s\-–—:]*", re.I)
# Roles arrive attached to the name in every shape a county can think of.
_ROLE = r"(?:County\s+)?(?:(?:1st|2nd|First|Second)\s+)?(?:Vice[\s\-]?)?Chair(?:man|person|woman)?"
ROLE_PAREN = re.compile(r"\s*\((%s)\)\s*" % _ROLE, re.I)
ROLE_LEAD = re.compile(r"^(%s)\b[\s\-–—:,]*" % _ROLE, re.I)
ROLE_TAIL = re.compile(r"[\s,\-–—]+(%s)\s*$" % _ROLE, re.I)
VACANT = re.compile(r"(?i)\bvacan(?:t|cy)\b")
SPLIT_LETTER = re.compile(r"\b([A-Z])\s+([a-z]{2,})")


def repair(name):
    """Rejoin a capital split off its own word by markup ("T homas" -> "Thomas")."""
    return SPLIT_LETTER.sub(r"\1\2", name)


def split_role(text):
    """Return (text_without_role, role_or_None)."""
    role = None
    m = ROLE_PAREN.search(text)
    if m:
        role, text = m.group(1), ROLE_PAREN.sub(" ", text)
    m = ROLE_LEAD.match(text)
    if m:
        role, text = role or m.group(1), ROLE_LEAD.sub("", text)
    m = ROLE_TAIL.search(text)
    if m:
        role, text = role or m.group(1), ROLE_TAIL.sub("", text)
    return " ".join(text.split()), (" ".join(role.split()).title() if role else None)


def is_name(text):
    text = split_role(repair(text))[0]
    if not text or not (4 <= len(text) <= 44):
        return False
    if re.search(r"\d", text) or BAD.search(text):
        return False
    toks = [t for t in text.replace(".", "").replace(",", " ").replace("-", " ")
            .replace("'", "").split() if t]
    if not (2 <= len(toks) <= 5):
        return False
    return all(re.match(r"^[A-Za-z][A-Za-z'’\-]*$", t) for t in toks)


def clean(text):
    text, role = split_role(repair(text))
    text = LEAD.sub("", text).strip(" .,-–—")
    if "," in text:
        a, b = [x.strip() for x in text.split(",", 1)]
        # "Schaefer, II" is a SUFFIX; only a genuine "Last, First" is flipped.
        text = "%s %s" % (a, b) if SUFFIX.match(b) else "%s %s" % (b, a)
    return " ".join(text.split()), role


# --- the three readings -------------------------------------------------------
WINDOW_AFTER = [1, 2, 3, 4, 5, 6, 7]
WINDOW_BEFORE = [-1, -2, -3, -4, -5, -6, -7]


def _same_line(lines):
    out = {}
    for line in lines:
        m = DIST.search(line)
        if not m:
            continue
        rest = re.sub(r"^[\s\-–—:•]+", "", DIST.sub(" ", line, count=1)).strip()
        paren = re.fullmatch(r"\((.+)\)", rest)   # Grant: "District 17 (Brian Lucey)"
        if paren:
            rest = paren.group(1).strip()
        if is_name(rest):
            out.setdefault(int(m.group(1)), clean(rest))
    return out


def _windowed(lines, offsets):
    out = {}
    for i, line in enumerate(lines):
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if d in out:
            continue
        for off in offsets:
            j = i + off
            if 0 <= j < len(lines) and is_name(lines[j]):
                out[d] = clean(lines[j])
                break
    return out


# --- the fourth shape: a district COLUMN ---------------------------------------
# The three readings above all need the WORD "district" next to the number,
# because that is how a page written as prose or as a list says it. A page
# written as a TABLE says it once, in the column header, and then prints bare
# numerals in the cells:
#
#     District | Name            | Phone        (Oneida: number then name)
#     1        | Vacant          |
#     2        | Sandy Hamburg   | 715-499-3129
#
#     Members          | Phone        | District   (Trempealeau: name then number)
#     Andy Todd, Chair | 608-406-0616 | 5
#
# `DIST` cannot see either, so all three column counties were recorded as
# publishing "no district column" — when having one is precisely why they were
# unreadable. Found 2026-08-27 re-sweeping the 50 no-roster counties, after
# Trempealeau turned out to publish the roster this project was drafting an
# e-mail to ask it for.
BARE_NUM = re.compile(r"^#?\s*(\d{1,2})\s*$")
COLUMN_SPAN = 6
# Richland publishes "Melvin (Bob) Frank" — a parenthesised nickname, which
# `is_name`'s per-token test rejects. The nickname is stripped for the TEST
# only: what ships is the county's own spelling, parentheses and all.
NICKNAME = re.compile(r"\s*\([^)]{1,24}\)\s*")


def _reads_as_name(cell):
    return is_name(cell) or is_name(NICKNAME.sub(" ", cell).strip())


def _column(lines, seats, forward):
    """Pair a bare-numeral district cell with the nearest name cell.

    The scan STOPS at the next bare numeral in range: without that, a district
    whose own row carries no readable name would reach into its neighbour's row
    and every seat below it would shift by one — the same failure the pinned
    reading directions exist to prevent, one column over.
    """
    out, vacant = {}, set()
    step = 1 if forward else -1
    for i, line in enumerate(lines):
        m = BARE_NUM.match(line.strip())
        if not m:
            continue
        d = int(m.group(1))
        if not (1 <= d <= seats) or d in out or d in vacant:
            continue
        for off in range(1, COLUMN_SPAN + 1):
            j = i + off * step
            if not (0 <= j < len(lines)):
                break
            cell = lines[j].strip()
            if BARE_NUM.match(cell):
                break                       # the next row: this one has no name
            if VACANT.search(cell):
                vacant.add(d)
                break
            if _reads_as_name(cell):
                out[d] = clean(cell)
                break
    return out, vacant


def _windowed_strict(lines, offsets):
    """`_windowed`, but the scan STOPS at the next district line.

    Rusk prints an INDEX of nineteen bare "District #N" links above its roster,
    and Richland's rows end in an e-mail rather than a name. In both, a district
    whose own row yields no readable name reaches past the next district heading
    and takes ITS name — Rusk filed Alec Hampton under both 19 and 1, Richland
    filed Kerry Severson under 15 and 16. The duplicate-name guard caught both,
    which is what it is for; this reading removes the cause. It is a separate
    pinned strategy rather than a change to `_windowed` so the twenty counties
    already shipping keep byte-identical behaviour.
    """
    out, vacant = {}, set()
    for i, line in enumerate(lines):
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if d in out or d in vacant:
            continue
        for off in offsets:
            j = i + off
            if not (0 <= j < len(lines)):
                break
            if DIST.search(lines[j]):
                break               # the next district's row: stop, never borrow
            # A vacancy sits on the side the page reads from: Shawano prints
            # "Vacant ." ABOVE its "- District 5", where the forward-only
            # `vacant_districts` can never see it.
            if VACANT.search(lines[j]):
                vacant.add(d)
                break
            if _reads_as_name(lines[j]):
                out[d] = clean(lines[j])
                break
    return out, vacant


READINGS = {
    "same-line": _same_line,
    "before": lambda ls: _windowed(ls, WINDOW_BEFORE),
    "after": lambda ls: _windowed(ls, WINDOW_AFTER),
}
STRICT_READINGS = {
    "before-strict": lambda ls: _windowed_strict(ls, WINDOW_BEFORE),
    "after-strict": lambda ls: _windowed_strict(ls, WINDOW_AFTER),
}
COLUMN_READINGS = {"column-after": True, "column-before": False}


def vacant_districts(lines, seats):
    out = set()
    for i, line in enumerate(lines):
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if 1 <= d <= seats and VACANT.search(" ".join(lines[i:i + 3])):
            out.add(d)
    return out


def fetch_bytes(url, timeout=45):
    """Raw bytes plus THE URL THAT ANSWERED, which is not always the one asked.

    Kenosha's directory is addressed by a stable county page id that 302s to
    whichever DocumentCenter edition is current; returning the resolved URL is
    what lets the run log name the edition it actually read.
    """
    lax = ssl.create_default_context()
    lax.check_hostname = False
    lax.verify_mode = ssl.CERT_NONE
    last = None
    for ctx in (None, lax):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read(), r.geturl()
        except Exception as e:      # noqa: BLE001 - reachability probe
            last = e
    raise RuntimeError("could not fetch %s (%s)" % (url, last))


def fetch(url, timeout=45):
    return fetch_bytes(url, timeout)[0].decode("utf-8", "replace")


# COUNTIES WHOSE ROSTER RIDES THEIR OWN ARCGIS LAYER, NOT A PAGE. The
# "blocked county SITE is not a blocked county" lesson, applied at home:
# county.milwaukee.gov and racinecounty.com both refuse automated clients
# (a Cloudflare challenge and an Akamai deny — the county-officials gap
# record carries the measurements), and both counties turned out to publish
# their board ON THEIR OWN GIS instead, supervisor names as attributes on
# the district features. Currency is measured, not assumed: Milwaukee's
# layer was data-edited 2026-06-29 and Racine's 2026-04-23 — both after the
# April 2026 spring election that reseated every board — and Milwaukee is
# additionally WITNESSED on every run against the county's own Legistar web
# API (body 138, "Milwaukee County Board of Supervisors"): the layer's name
# set and Legistar's current-office set must agree exactly, or the county
# fails loudly. Legistar is a witness and never a source — its OData date
# filter is silently ignored server-side (filter client-side) and its end
# dates can be aspirational.
#
# Outagamie is DELIBERATELY not here: its board moved to outagamie.gov,
# which answered one probe on 2026-08-25 and refused every later one
# (HTTP 403 across UAs) — the gap record carries both measurements, and a
# roster this client cannot re-verify weekly does not ship.
ARCGIS_COUNTIES = [
    {
        "fips": "55079", "name": "Milwaukee", "seats": 18,
        "layer": ("https://services2.arcgis.com/s1wgJQKbKJihhhaT/arcgis/rest/"
                   "services/Milwaukee_County_Supervisory_Districts/FeatureServer/46"),
        "fields": {"district": "District_Nbr", "name": "Sup_Name",
                    "email": "Email_Addr", "url": "Website_Url"},
        "source_url": ("https://services2.arcgis.com/s1wgJQKbKJihhhaT/arcgis/rest/"
                        "services/Milwaukee_County_Supervisory_Districts/FeatureServer/46"),
        "witness": {"client": "milwaukeecounty", "body_id": 138},
    },
    {
        "fips": "55101", "name": "Racine", "seats": 21,
        "layer": ("https://services1.arcgis.com/z1oAk3W6cWVD8swZ/arcgis/rest/"
                   "services/County_Board_of_Supervisors_WFL1/FeatureServer/0"),
        "fields": {"district": "DISTRICTID", "name": "REPNAME", "email": "Contact"},
        "source_url": ("https://services1.arcgis.com/z1oAk3W6cWVD8swZ/arcgis/rest/"
                        "services/County_Board_of_Supervisors_WFL1/FeatureServer/0"),
    },
]


def _fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        return json.load(r)


def _fold_person(name):
    """First + last token, diacritics stripped: the layer prints
    'Caroline Gómez-Tom' and 'Sheldon A. Wasserman' where Legistar prints
    'Caroline Gomez-Tom' and 'Sheldon Wasserman' — same people, three
    styling axes (accents, middle initials, hyphens), so the witness match
    folds all three rather than failing on typography."""
    import unicodedata
    flat = unicodedata.normalize("NFKD", str(name))
    flat = "".join(ch for ch in flat if not unicodedata.combining(ch))
    toks = [t for t in re.split(r"[^A-Za-z]+", flat.lower()) if len(t) > 1]
    if not toks:
        return ""
    return toks[0] + "|" + toks[-1]


def scrape_arcgis_county(spec):
    """District -> member rows read as ATTRIBUTES off the county's own layer."""
    fields = spec["fields"]
    out_fields = ",".join(v for v in fields.values())
    data = _fetch_json(spec["layer"] + "/query?where=1%3D1&outFields=" +
                       out_fields + "&returnGeometry=false&f=json")
    feats = data.get("features") or []
    rows = {}
    for f in feats:
        a = f.get("attributes") or {}
        d = a.get(fields["district"])
        member = a.get(fields["name"])
        if d is None or not member:
            continue
        d = int(str(d).strip())
        member = str(member).strip()
        role = None
        # Milwaukee packs the officer's ROLE into the name field for its two
        # officers ("Chairwoman Marcelia Nicholson-Bovell") — the measured
        # trap; the role moves to its own field, never ships inside a name.
        rm = re.match(r"^(Chairwoman|Chairman|Chairperson|Chair|Vice[- ]?Chair(?:woman|man)?|1st Vice[- ]?Chair(?:woman|man)?|2nd Vice[- ]?Chair(?:woman|man)?)\s+(.+)$", member, re.I)
        if rm:
            role = rm.group(1).strip()
            member = rm.group(2).strip()
        email = a.get(fields.get("email")) if fields.get("email") else None
        if email:
            # Milwaukee packs its addresses as "mailto:x@y?subject=" — unwrap
            email = re.sub(r"^mailto:", "", str(email)).split("?")[0].strip() or None
        entry = {"name": member, "vacant": False, "role": role}
        if email:
            entry["email"] = email
        if fields.get("url") and a.get(fields["url"]):
            entry["url"] = str(a[fields["url"]]).strip()
        rows[d] = entry
    if set(rows) != set(range(1, spec["seats"] + 1)):
        missing = sorted(set(range(1, spec["seats"] + 1)) - set(rows))
        raise RuntimeError("%s: layer resolved %d of %d districts (missing %s)"
                           % (spec["name"], len(rows), spec["seats"], missing))
    witness = spec.get("witness")
    if witness:
        recs = _fetch_json("https://webapi.legistar.com/v1/%s/officerecords"
                           "?$filter=OfficeRecordBodyId+eq+%d&$top=400"
                           % (witness["client"], witness["body_id"]))
        # end-date filtering is CLIENT-side: the server ignores date filters,
        # and the cutoff is TODAY — an April term-end must not count as current
        today = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        current = {_fold_person(r["OfficeRecordFullName"]) for r in recs
                   if (r.get("OfficeRecordEndDate") or "9999") > today}
        layer_names = {_fold_person(v["name"]) for v in rows.values()}
        if layer_names != current:
            raise RuntimeError(
                "%s: the GIS layer and the Legistar witness disagree on the bench "
                "(layer-only: %s; legistar-only: %s) — do not ship either side"
                % (spec["name"], sorted(layer_names - current),
                   sorted(current - layer_names)))
    return {str(d): rows[d] for d in sorted(rows)}


# --- COUNTIES WHOSE ROSTER IS A DOCUMENT, WITNESSED AGAINST A PAGE -----------
# Kenosha's Clerk publishes an annual Directory of Public Officials — a 107-page
# PDF whose County Board section prints each district beside its supervisor's
# NAME, PHONE and E-MAIL, and marks the Chair and Vice-Chair on their own rows.
# No other county in this file publishes contact for its board at all.
#
# A document is a weaker thing to depend on than a page, so it ships only under
# a witness: the county's own board page carries the same 23 districts and the
# same 23 names, read with the plain `after` reading every page county uses.
# ALL 23 MUST AGREE OR THE COUNTY SHIPS NOTHING — the same all-or-nothing rule
# scrape_county holds, with the two surfaces checking each other rather than a
# reading direction checking itself.
#
# THE ROLES ARE HELD TO A SEPARATE, WEAKER GATE, and that split is deliberate.
# A directory is printed once a year; boards elect their chair every April, so
# the document is exactly the surface that can be a year stale about who chairs
# it — and the county card's board chair is reconciled against this roster, so a
# stale role here would supersede the Blue Book with something older still. The
# board page states its leadership in a sentence of prose ("Supervisor X is the
# Chairman and Supervisor Y is the Vice Chairman for the ... term"), so the
# roles ship only when that sentence names the same two people. If the sentence
# is reworded past this reader, the NAMES still ship and the roles are withheld
# with the reason printed — a re-worded sentence must not cost a county its
# whole roster, and an unwitnessed chair must not reach a card.
#
# THE PROFILE LINKS ARE PAIRED BY BLOCK, NOT BY POSITION. Each supervisor is one
# <p> on the board page holding one /Directory.aspx?EID=<n> link, the district
# and the name, so the link is read from the same block as the district it
# belongs to and a seat whose block does not resolve simply gets no link. Two
# reasons not to do it any other way, both measured on this page: District 7 is
# marked up as TWO anchors to one EID either side of a <br> where every other
# seat is one anchor, so an anchor-per-supervisor rule finds 22 of 23; and the
# image alt attributes — the obvious second pairing — carry the county's own
# typos, spelling District 9 "John Morissey" and District 23 "Aaron Karrow"
# against the visible text's "Morrissey" and "Karow". THE ALT TEXT WOULD HAVE
# WITNESSED THE DISTRICT AND CORRUPTED THE NAME.
DOCUMENT_COUNTIES = [
    {
        "fips": "55059", "name": "Kenosha", "seats": 23,
        # STABLE county page id -> 302 -> the current DocumentCenter edition;
        # never the /DocumentCenter/View/<edition>/ address, which freezes.
        "document": "https://www.kenoshacountywi.gov/1018/County-Directory-PDF",
        # the document's board section, sliced between two headings it prints
        # exactly once each in this order — "BOARD OF SUPERVISORS" occurs again
        # inside "COMMITTEES OF THE KENOSHA COUNTY BOARD OF SUPERVISORS", which
        # is precisely where the section has to stop: the committee lists name
        # supervisors as committee CHAIRS, a role that is not the board's.
        "section": ("BOARD OF SUPERVISORS", "COMMITTEES OF THE"),
        "witness": "https://www.kenoshacountywi.gov/113/County-Board-of-Supervisors",
        # the reader lands on the page, not on a 900 KB PDF; both publish every
        # name the card shows
        "source_url": "https://www.kenoshacountywi.gov/113/County-Board-of-Supervisors",
        "profile_prefix": "https://www.kenoshacountywi.gov",
    },
]

# "1. William Grady ....... 262-652-2020" for districts 1-14 and "15 Dave
# Geertsen ....... 262-515-3334" for 15-23: THE SAME DOCUMENT NUMBERS ITS ROWS
# TWO WAYS, so the period is optional or a reader gets 14 of 23. The leader run
# is optional too, and is not always dots — two rows use U+2026 ellipses with no
# space before the phone at all ("7. Daniel Gaschke…………262-902-7028").
DOC_ROW = re.compile(r"^(\d{1,2})[.)]?\s+(.+?)\s*"
                     r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\s*$")
DOC_LEADER_TAIL = re.compile(r"[\s.…]+$")
DOC_EMAIL = re.compile(r"(?i)^e-?\s?mail:?\s*(\S+@\S+)$")
# "Supervisor Mark Nordigian is the Chairman and Supervisor John Franco is the
# Vice Chairman for the 2026-2028 County Board term."
LEADERSHIP = re.compile(
    r"(?i)supervisor\s+(.+?)\s+is\s+the\s+chair(?:man|person|woman)?\b"
    r".{0,80}?supervisor\s+(.+?)\s+is\s+the\s+vice[\s-]?chair(?:man|person|woman)?\b")
# one supervisor's block on the board page: a <p> holding exactly one profile
# link, the district and the name
DOC_BLOCK = re.compile(r"(?is)<p\b[^>]*>(.*?)</p>")
DOC_PROFILE = re.compile(r"(?i)href=\"(/Directory\.aspx\?EID=\d+)\"")
DOC_DISTNAME = re.compile(r"(?i)^District\s*(\d{1,2})\s+(.+)$")


def document_rows(pdf_bytes, section):
    """District -> {name, role, phone, email} out of the Clerk's directory."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    whole = "\n".join(page.extract_text() or "" for page in reader.pages)
    try:
        start = whole.index(section[0])
        end = whole.index(section[1])
    except ValueError as e:
        raise RuntimeError("the directory no longer prints %r/%r — re-read it "
                           "before shipping (%s)" % (section[0], section[1], e))
    if not start < end:
        raise RuntimeError("the directory's %r heading now follows %r — the "
                           "board section is not where this reader slices it"
                           % (section[0], section[1]))
    lines = [" ".join(x.split()) for x in whole[start:end].split("\n")]
    rows, last = {}, None
    for line in [x for x in lines if x]:
        m = DOC_ROW.match(line)
        if m:
            d = int(m.group(1))
            member, role = clean(DOC_LEADER_TAIL.sub("", m.group(2)))
            if not is_name(member):
                last = None
                continue
            rows[d] = {"name": member, "vacant": False, "role": role,
                       "phone": m.group(3).strip()}
            last = d
            continue
        em = DOC_EMAIL.match(line)
        # the address sits on the row BELOW its member and nowhere else, so it
        # is only ever attached to the row just read — never searched for
        if em and last is not None:
            rows[last]["email"] = em.group(1)
            last = None
    return rows


def witness_profiles(page_html, prefix):
    """District -> (name, profile url) read one supervisor block at a time."""
    out = {}
    for inner in DOC_BLOCK.findall(page_html):
        links = set(DOC_PROFILE.findall(inner))
        if len(links) != 1:
            continue
        text = " ".join(html_lib.unescape(_TAG.sub(" ", inner)).split())
        m = DOC_DISTNAME.match(text)
        if not m:
            continue
        d = int(m.group(1))
        if d in out:            # two blocks claim one district: trust neither
            out[d] = None
            continue
        out[d] = (clean(m.group(2))[0], prefix + links.pop())
    return {d: v for d, v in out.items() if v}


def scrape_document_county(spec):
    """A roster read from a county DOCUMENT and witnessed against its page."""
    pdf_bytes, edition = fetch_bytes(spec["document"], timeout=90)
    print("  doc  %-12s edition %s (%d KB)"
          % (spec["name"], edition, len(pdf_bytes) // 1024), file=sys.stderr)
    rows = document_rows(pdf_bytes, spec["section"])
    seats = spec["seats"]
    want = set(range(1, seats + 1))
    if set(rows) != want:
        raise RuntimeError("%s: the directory resolved %d of %d districts "
                           "(missing %s) — re-read the document"
                           % (spec["name"], len(rows), seats,
                              sorted(want - set(rows))))

    page = fetch(spec["witness"])
    lines = to_lines(page)
    witness = _windowed(lines, WINDOW_AFTER)
    if set(witness) != want:
        raise RuntimeError("%s: the witness page resolved %d of %d districts "
                           "(missing %s) — the two surfaces can no longer check "
                           "each other, so neither ships"
                           % (spec["name"], len(witness), seats,
                              sorted(want - set(witness))))
    differ = [(d, rows[d]["name"], witness[d][0]) for d in sorted(want)
              if rows[d]["name"] != witness[d][0]]
    if differ:
        raise RuntimeError(
            "%s: the directory and the board page name different supervisors "
            "(%s) — one of the two is stale and this scraper cannot tell which"
            % (spec["name"], "; ".join("D%d %r vs %r" % x for x in differ)))

    # roles: shipped only where the page's own leadership sentence agrees.
    # Exactly one row may be marked chair and one vice-chair; anything else is
    # the document saying something this reader does not understand.
    def marked_as(vice):
        who = [v["name"] for v in rows.values() if v.get("role")
               and bool(re.match(r"(?i)vice", v["role"])) == vice]
        return who[0] if len(who) == 1 else None

    doc_chair, doc_vice = marked_as(False), marked_as(True)
    stated = LEADERSHIP.search(" ".join(lines))
    if not stated:
        print("  note %-12s the board page no longer states its leadership in a "
              "sentence this reader parses — roles withheld" % spec["name"],
              file=sys.stderr)
        confirmed = False
    else:
        chair, vice = clean(stated.group(1))[0], clean(stated.group(2))[0]
        confirmed = (doc_chair is not None and doc_vice is not None
                     and chair == doc_chair and vice == doc_vice)
        if not confirmed:
            print("  note %-12s the board page states chair %r / vice-chair %r "
                  "where the directory marks %r / %r — roles withheld"
                  % (spec["name"], chair, vice, doc_chair, doc_vice),
                  file=sys.stderr)
    if confirmed:
        print("  role %-12s chair %s, vice-chair %s (both witnessed on the "
              "county's own board page)" % (spec["name"], doc_chair, doc_vice),
              file=sys.stderr)
    else:
        for row in rows.values():
            row["role"] = None

    profiles = witness_profiles(page, spec["profile_prefix"])
    linked = 0
    for d, row in rows.items():
        found = profiles.get(d)
        # paired on the NAME the block itself carries, so a block that has
        # shifted takes its own link with it rather than someone else's
        if found and found[0] == row["name"]:
            row["url"] = found[1]
            linked += 1
    print("  link %-12s %d of %d supervisors carry the county's own profile page"
          % (spec["name"], linked, seats), file=sys.stderr)
    return {str(d): rows[d] for d in sorted(rows)}


# --- officers published ABOVE the district list ------------------------------
# Juneau and Oneida name their chair and vice-chairs in a block of their own,
# separate from the district rows, so the roles never reach a member through
# `split_role` (which only sees a role attached to the name it is reading).
# That is not cosmetic: the county card's board chair is reconciled weekly
# against this roster, and a roster with NO marked chair makes the builder
# WITHHOLD the Blue Book's chair rather than supersede it — which is how
# Juneau's card lost a chair its own page names in plain text.
#
# THE JOIN IS ON A FULL NAME AND MUST BE UNIQUE, and every join PRINTS. A role
# guessed onto the wrong supervisor is worse than no role at all.
OFFICER_LINE = re.compile(r"^\s*(%s)\s*(?:[-–—:]\s*(.+))?$" % _ROLE, re.I)
# str.title() turns "1st Vice Chair" into "1St Vice Chair" — it upper-cases the
# letter after every digit. Ordinals keep their own casing.
_ORDINAL = re.compile(r"^\d+(?:st|nd|rd|th)$", re.I)


def role_case(text):
    return " ".join(w.lower() if _ORDINAL.match(w) else w.title()
                    for w in text.split())


def attach_officer_roles(lines, districts, county):
    """Give a member the role their county states in its officers block."""
    by_name = {}
    for d, row in districts.items():
        if row.get("name"):
            by_name.setdefault(row["name"], []).append(d)
    for i, line in enumerate(lines):
        m = OFFICER_LINE.match(line)
        if not m:
            continue
        role = role_case(m.group(1))
        # THE SAME BEFORE/AFTER AMBIGUITY THE WHOLE FILE PINS, one block over,
        # and it is not hypothetical: a first draft scanned FORWARD only and
        # filed Jefferson's Blane Poulson — its Second Vice Chair — as First,
        # because Jefferson prints the NAME above the role ("James Braughler /
        # First Vice Chair / phone") where Brown prints it below ("Chair /
        # Buckley, Patrick"). Three cases, and only the first two attach:
        #   * the role line carries its own name  -> use it, and never look
        #     further; Juneau lists three officers in consecutive lines, so a
        #     fall-through files each role under the NEXT officer's name;
        #   * exactly ONE neighbouring line reads as a name -> that one;
        #   * BOTH neighbours read as names -> ambiguous, attach nothing.
        if m.group(2):
            cands = [m.group(2)]
        else:
            before = lines[i - 1] if i > 0 else ""
            after = lines[i + 1] if i + 1 < len(lines) else ""
            b_ok, a_ok = is_name(before), is_name(after)
            if b_ok and a_ok:
                print("  note %-12s role %r sits between two names (%r, %r) — "
                      "not attached" % (county, role, before, after), file=sys.stderr)
                continue
            cands = [after] if a_ok else ([before] if b_ok else [])
        for cand in cands:
            if not cand:
                continue
            who = clean(cand)[0]
            hits = by_name.get(who)
            if not hits:
                continue
            if len(hits) > 1:
                print("  note %-12s %r holds %d districts — role %r not attached"
                      % (county, who, len(hits), role), file=sys.stderr)
                break
            d = hits[0]
            if districts[d].get("role"):
                break                       # the row already said so
            districts[d]["role"] = role
            print("  role %-12s district %s: %s -> %s"
                  % (county, d, who, role), file=sys.stderr)
            break
    return districts


def scrape_county(fips, name, seats, strategy, url):
    """All seats or nothing — see the module docstring."""
    lines = to_lines(fetch(url))
    if strategy in STRICT_READINGS:
        found, vacant = STRICT_READINGS[strategy](lines)
    elif strategy in COLUMN_READINGS:
        # A column page names no district beside a seat, so `vacant_districts`
        # (which keys off the WORD) can never see its vacancies; the column
        # reader reports them from the cell it actually lands on instead.
        found, vacant = _column(lines, seats, COLUMN_READINGS[strategy])
    else:
        vacant = vacant_districts(lines, seats)
        found = READINGS[strategy](lines)
    for d in vacant:
        found.pop(d, None)          # the county says the seat is empty; believe it
    covered = set(found) | vacant
    if covered != set(range(1, seats + 1)):
        missing = sorted(set(range(1, seats + 1)) - covered)
        raise RuntimeError(
            "%s: resolved %d of %d districts (missing %s) under the pinned '%s' "
            "reading — the page has changed shape; re-read it before moving this "
            "entry" % (name, len(covered), seats, missing, strategy))
    names = [v[0] for v in found.values()]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise RuntimeError("%s: the same person is filed under two districts (%s) — "
                           "a sign the reading direction has shifted" % (name, dupes))
    out = {}
    for d in range(1, seats + 1):
        if d in vacant:
            out[str(d)] = {"name": None, "vacant": True, "role": None}
        else:
            member, role = found[d]
            out[str(d)] = {"name": member, "vacant": False, "role": role}
    return attach_officer_roles(lines, out, name)


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    scraped_at = os.environ.get("SCRAPED_AT") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    counties, failures = {}, []
    jobs = [(c["fips"], c["name"], c["seats"], "arcgis", c) for c in ARCGIS_COUNTIES]
    jobs += [(c["fips"], c["name"], c["seats"], "document", c) for c in DOCUMENT_COUNTIES]
    jobs += [(fips, name, seats, strategy, url) for fips, name, seats, strategy, url in COUNTIES]
    for fips, name, seats, strategy, src in jobs:
        if only and fips != only:
            continue
        try:
            if strategy == "arcgis":
                districts = scrape_arcgis_county(src)
                source_url = src["source_url"]
            elif strategy == "document":
                districts = scrape_document_county(src)
                source_url = src["source_url"]
            else:
                districts = scrape_county(fips, name, seats, strategy, src)
                source_url = src
        except Exception as e:      # noqa: BLE001 - one county never fails the run
            failures.append("%s (%s): %s" % (name, fips, e))
            print("  MISS %-12s %s" % (name, e), file=sys.stderr)
            continue
        counties[fips] = {"county": name, "seats": seats, "source_url": source_url,
                          "scraped_at": scraped_at, "districts": districts}
        vac = sum(1 for d in districts.values() if d["vacant"])
        print("  ok   %-12s %d seats%s" % (name, seats, " (%d vacant)" % vac if vac else ""),
              file=sys.stderr)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"counties": counties, "failures": failures}, f, indent=2, ensure_ascii=False)
    total = sum(c["seats"] for c in counties.values())
    print("wrote %s: %d/%d counties, %d seats%s"
          % (out_path, len(counties),
             len(COUNTIES) + len(ARCGIS_COUNTIES) + len(DOCUMENT_COUNTIES), total,
             ", %d county/counties missed" % len(failures) if failures else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

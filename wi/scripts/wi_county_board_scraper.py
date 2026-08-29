#!/usr/bin/env python3
"""
Scrape county board supervisors from the 31 Wisconsin counties that publish a
district-keyed member list. Stage 1 of the pair; build_wi_county_board_roster.py
turns the intermediate JSON into data/app/county-board-members.json.

WHY ONLY THIRTY-FOUR OF SEVENTY-TWO
-----------------------------------
Wisconsin publishes county board DISTRICTS statewide (Wis. Stat. 5.15(4)(br)1,
see build_wi_supervisory_districts.py) and publishes the PEOPLE in them
nowhere: each county names its own supervisors, 72 different ways. Thirty pair
a district with a person in a form a parser can read, Dodge does it in a
paginated constituent DIRECTORY that needs its own fetch shape (see
CONSTITUENT_COUNTIES), and Milwaukee and Racine publish theirs on their own GIS
layers. The rest are not oversights and are recorded as such:

  * Kenosha and Ozaukee publish district MAPS — a page per district with a PDF
    and no name on it anywhere. They were checked three pages deep apiece.
    This file used to claim 23 counties; that count came from a sweep that
    tested district NUMBERS, and numbers are what a map index has.
  * Marinette publishes 29 of its 30 seats. District 26 is an unnumbered
    "VACANT SEAT" row in an alphabetical list, and assigning it by elimination
    would be an inference the county never wrote, so the county stays out.
  * Dodge WAS in this bucket until 2026-08-29, filed under "publishes prose",
    and that was never measured against the county. The sweep asked
    co.dodge.wi.us, which had become a 261-byte "This site has permanently
    moved" stub answering HTTP 200; the county is at www.co.dodge.wi.gov and
    publishes all 33 seats district-keyed. A sweep that reads a STATUS CODE
    cannot tell a county that publishes nothing from a county that published a
    forwarding note, so both land in the same bucket — the Knox shape in
    Illinois, where a blocked WEBSITE was recorded as a blocked COUNTY. It
    ships now; see CONSTITUENT_COUNTIES for the fetch shape its directory
    needed, and build_wi_county_board_directory.py --probe for the sweep that
    reads the body rather than the status code.
  * The rest could not be read: 9 answer 403 to a datacenter client and hold
    it against browser headers (Marathon, La Crosse, Outagamie, Fond du Lac,
    Lafayette, Lincoln, Monroe, Rock, Sheboygan), Taylor sits behind an
    sgcaptcha challenge answering 202 (an access control, not an obstacle to
    route around), Forest does not resolve, and the remainder publish their
    members as PDFs, images or prose with no district column.

    TAYLOR IS NOT A "PUBLISHES NOTHING" COUNTY, and the bucket above said so
    only because nothing here can SEE the page. It publishes a County Board
    directory at co.taylor.wi.us/directory/county-board/ that is
    district-keyed and carries a name, a county e-mail, a street address and
    a phone per supervisor — richer than most of the counties that do ship.
    The block is the host, not the county: every path on co.taylor.wi.us
    answers HTTP 202 with a 196-byte meta-refresh to
    `/.well-known/sgcaptcha/` and an `sg-captcha: challenge` header, and the
    three other Taylor hosts tried (taylorcountywi.gov, its www, and
    gis.co.taylor.wi.us) do not resolve at all. A captcha is an access
    control and is not defeated here, so NO WEEKLY SCRAPE OF TAYLOR IS
    POSSIBLE: if its roster ever ships it must ride a document-carried
    route with a dated not-re-read line (the Edwards/Wabash pattern in
    Illinois's il_county_commissioners_scraper.py), never this table.

    WHAT IS KNOWN OF ITS CONTENTS CAME FROM THE OPERATOR'S OWN BROWSER
    (2026-08-29) and is INCOMPLETE: districts 1-12 of 17. The shipped LTSB
    geometry numbers Taylor 1..17, so the roster does not resolve and the
    all-seats-or-nothing rule applies — 12 of 17 would read as a complete
    board with five empty seats. Nothing is shipped for Taylor until 13-17
    are in hand.

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
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

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
    ("55075", "Marinette", 30, "same-line",
     "https://www.marinettecountywi.gov/county_board/"),
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


def vacant_districts(lines, seats, strategy="after"):
    """Districts the county itself marks empty, read from the district's OWN row.

    ON A `same-line` PAGE THE WINDOW IS THE LINE, and that is not a nicety.
    Marinette lists "Trygve Rhude - District 22", then his wards, then the
    next row — which is its unnumbered "VACANT SEAT". A three-line lookahead
    reached across the row boundary (the ward line in between says nothing
    about a district, so stopping at the next district heading does not help)
    and filed District 22 as vacant, ERASING A SITTING SUPERVISOR — silently,
    because the seat count still came to 30 and every guard stayed green.
    A page that puts name and district on one line states a vacancy there too.
    For the other readings the window survives, now stopping at the next
    district line. Measured 2026-08-29 while adding Marinette.
    """
    out = set()
    for i, line in enumerate(lines):
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if not (1 <= d <= seats):
            continue
        window = [line]
        if strategy != "same-line":
            # a page that puts the name on its own line may put the vacancy
            # there too; one that puts both on the district line never does
            for j in range(i + 1, min(i + 3, len(lines))):
                if DIST.search(lines[j]):
                    break           # the next district's row: never borrow it
                window.append(lines[j])
        if VACANT.search(" ".join(window)):
            out.add(d)
    return out


def fetch(url, timeout=45):
    lax = ssl.create_default_context()
    lax.check_hostname = False
    lax.verify_mode = ssl.CERT_NONE
    last = None
    for ctx in (None, lax):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:      # noqa: BLE001 - reachability probe
            last = e
    raise RuntimeError("could not fetch %s (%s)" % (url, last))


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


# COUNTIES WHOSE ROSTER RIDES A DOCUMENT, NOT A FETCH. Illinois's
# il_county_commissioners_scraper.py carries Edwards and Wabash this way, for
# the same reason: the county publishes the list and nothing here can read it,
# so pretending a weekly check happens would be the lie. Each run prints a NOT
# RE-READ line naming the source and its age instead.
#
# TAYLOR (2026-08-29). co.taylor.wi.us publishes a district-keyed County Board
# directory at /directory/county-board/ — name, county e-mail, street address
# and phone for all seventeen districts, richer than most counties that ship.
# Every path on that host answers HTTP 202 with a 196-byte meta-refresh to
# `/.well-known/sgcaptcha/`; a captcha is an access control and is not defeated
# here, and the three other Taylor hosts tried do not resolve at all. The
# contents below were read from that page by the OPERATOR in an ordinary
# browser and handed over — a human reading a public page is the route the
# challenge permits, and it is why this is a document and not a scrape.
#
# THE STREET ADDRESSES ARE DELIBERATELY NOT CARRIED. They are supervisors'
# homes (rural routes, "W5895 Jolly Ave."), and this fleet's standing rule is
# that a home address never ships even when the source publishes it; a
# supervisor's house is not an office location. Name, county e-mail and phone
# are official contact details and do.
DOCUMENT_ROSTERS = [
    {
        "fips": "55119", "name": "Taylor", "seats": 17,
        "read_on": "2026-08-29",
        "source_url": "https://co.taylor.wi.us/directory/county-board/",
        "how": "read from the county's own directory page in a browser by the "
               "operator; the host answers a captcha to every automated client",
        # district -> (name, e-mail, phone)
        "members": {
            "1": ("Lisa Carbaugh", "lisa.carbaugh@co.taylor.wi.us", "715-965-1980"),
            "2": ("Tim Hansen", "tim.hansen@co.taylor.wi.us", "715-965-7662"),
            "3": ("Susan Swiantek", "sue.swiantek@co.taylor.wi.us", "715-560-9409"),
            "4": ("Michael Bub", "michael.bub@co.taylor.wi.us", "715-965-7748"),
            "5": ("Loren (Jim) Metz", "jim.metz@co.taylor.wi.us", "715-748-0740"),
            "6": ("Scott Mildbrand", "scott.mildbrand@co.taylor.wi.us", "715-748-3988"),
            "7": ("Lorie Floyd", "lorie.floyd@co.taylor.wi.us", "608-412-2974"),
            "8": ("Charles Zenner", "chuck.zenner@co.taylor.wi.us", "715-678-2172"),
            "9": ("Diane J. Albrecht", "diane.albrecht@co.taylor.wi.us", "715-748-5471"),
            "10": ("Catherine Lemke", "catherine.lemke@co.taylor.wi.us", "715-748-5694"),
            "11": ("James Gebauer", "jim.gebauer@co.taylor.wi.us", "715-748-4871"),
            "12": ("Rollie Thums", "rollie.thums@co.taylor.wi.us", "715-427-5809"),
            "13": ("Harvey 'Bud' Suckow", "bud.suckow@co.taylor.wi.us", "715-897-4514"),
            "14": ("Karen Cummings", "karen.cummings@co.taylor.wi.us", "715-668-5226"),
            "15": ("Lynette Rosemeyer", "lynn.rosemeyer@co.taylor.wi.us", "715-827-0027"),
            "16": ("Darrell Thompson", "darrell.thompson@co.taylor.wi.us", "715-644-8285"),
            "17": ("Rodney Adams", "rod.adams@co.taylor.wi.us", "715-678-2397"),
        },
    },
]


def document_county(spec):
    """A roster carried from a document, with its age stated on every run."""
    import datetime
    read = datetime.date(*map(int, spec["read_on"].split("-")))
    age = (datetime.date.today() - read).days
    print("  NOT RE-READ %-12s %d seats from a document read %s (%d days ago)"
          % (spec["name"], spec["seats"], spec["read_on"], age), file=sys.stderr)
    members = spec["members"]
    want = {str(d) for d in range(1, spec["seats"] + 1)}
    if set(members) != want:
        missing = sorted(int(k) for k in want - set(members))
        raise RuntimeError("%s: the document carries %d of %d districts (missing %s)"
                           % (spec["name"], len(members), spec["seats"], missing))
    names = [v[0] for v in members.values()]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise RuntimeError("%s: the same person is filed under two districts (%s)"
                           % (spec["name"], dupes))
    out = {}
    for d in range(1, spec["seats"] + 1):
        name, email, phone = members[str(d)]
        row = {"name": name, "vacant": False, "role": None}
        if email:
            row["email"] = email
        if phone:
            row["phone"] = phone
        out[str(d)] = row
    return out


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


# COUNTIES WHOSE ROSTER IS A PAGINATED CONSTITUENT DIRECTORY, NOT A PAGE OF TEXT.
#
# DODGE (2026-08-29). Its board page publishes all 33 seats district-keyed
# ("County Board Supervisor, District 32") in a Finalsite constituent
# directory, and the whole county was recorded here as "publishes prose" until
# a reader reported that co.dodge.wi.us had moved. That host was answering
# HTTP 200 with a 261-byte "This site has permanently moved" stub, so a sweep
# reading STATUS CODES could not tell a county that publishes nothing from one
# that published a forwarding note.
#
# THE DIRECTORY PAGINATES AT TWELVE, which is why this is a separate strategy
# and not a row in COUNTIES. Three things about it were measured rather than
# assumed, and each was wrong on the first guess:
#
#   * `?const_page=2` ON THE PAGE ITSELF IS DECORATION. The server returns page
#     one for every value of it, so a single fetch of the members URL sees 12
#     of 33 — and 12 seats of a 33-seat board is exactly what the
#     all-seats-or-nothing rule exists to refuse.
#   * The pagination works on the ELEMENT endpoint (/fs/elements/<id>) and
#     ONLY when `const_search_group_ids` rides along. Without the group id that
#     endpoint also returns page one, silently and with a 200.
#   * NEITHER ID IS PINNED. Both are discovered from the members page on every
#     run — the directory element by its own `fsConstituent fsDirectory` class,
#     the group id from the county's own search form — so a site rebuild that
#     renumbers elements keeps working, and a page carrying two directories
#     fails loudly instead of scraping whichever came first.
#
# THE E-MAILS ARE OBFUSCATED and would otherwise have shipped as nothing at
# all: each address is written as a reversed-string JavaScript call
# (`FS.util.insertEmail(id, "su.iw.egdod.oc", "23tcirtsid")` is
# district32@co.dodge.wi.us). That is the Brown County shape from Illinois —
# seven addresses emptied silently when a county switched on Cloudflare's
# mailto obfuscation — so it is decoded, never dropped.
#
# THEY ARE ALSO DERIVABLE, AND ARE NOT DERIVED. Every address is
# district<N>@co.dodge.wi.us, so the district number in the address is a free
# CHECK on the row it was read from: an address whose number disagrees with
# its own row means the page has reshuffled under the parser, and the county
# fails rather than shipping a supervisor someone else's contact. An address
# that is not a district alias at all (a personal one) ships as published.
#
# The mail domain is the OLD one and that is correct: co.dodge.wi.us carries
# live MX and is what the county's own clerk page still prints. A web domain
# and a mail domain move separately.
CONSTITUENT_COUNTIES = [
    {
        "fips": "55027", "name": "Dodge", "seats": 33,
        "page_url": "https://www.co.dodge.wi.gov/government/county-board/members",
        "source_url": "https://www.co.dodge.wi.gov/government/county-board/members",
    },
]
_DIR_ELEMENT = re.compile(r'<div class="fsElement fsConstituent fsDirectory[^"]*" id="fsEl_(\d+)"')
_GROUP_ID = re.compile(r'name="const_search_group_ids" value="(\d+)"')
_PAGE_LABEL = re.compile(r'fsPaginationLabel">\s*showing\s+(\d+)\s*-\s*(\d+)\s+of\s+(\d+)')
_ITEM = re.compile(r'<div class="fsConstituentItem"(.*?)(?=<div class="fsConstituentItem"|\Z)', re.S)
_FULL_NAME = re.compile(r'class="fsFullName">\s*(?:<[^>]*>\s*)*([^<]+?)\s*</a>', re.S)
_TITLES = re.compile(r'<div class="fsTitles">(.*?)</div>', re.S)
# FS.util.insertEmail(elementId, reversedDomain, reversedLocalPart, ...)
_INSERT_EMAIL = re.compile(r'insertEmail\(\s*"[^"]*"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"')
_DISTRICT_ALIAS = re.compile(r"^district(\d{1,2})$", re.I)
CONSTITUENT_PAGE_CAP = 12          # 12 per page; a 33-seat board needs 3


def _constituent_items(page_html):
    """-> {district: {'name': str, 'email': str|None}} for ONE fetched page."""
    out = {}
    for m in _ITEM.finditer(page_html):
        chunk = m.group(1)
        nm = _FULL_NAME.search(chunk)
        ti = _TITLES.search(chunk)
        if not nm or not ti:
            continue
        titles = " ".join(html_lib.unescape(_TAG.sub(" ", ti.group(1))).split())
        dm = DIST.search(titles)
        if not dm:
            continue
        row = {"name": " ".join(html_lib.unescape(nm.group(1)).split()), "email": None}
        em = _INSERT_EMAIL.search(chunk)
        if em:
            row["email"] = "%s@%s" % (em.group(2)[::-1], em.group(1)[::-1])
        out[int(dm.group(1))] = row
    return out


def _constituent_officers(page_html, county):
    """-> {district: role}. The county states the DISTRICT beside each officer,
    so the join is on the file's own key rather than on a name — which is the
    stronger join and is also the only one available here: the officer cards
    say "Dave Frohling" where the directory says "David Frohling"."""
    out = {}
    for sec in re.findall(r'<section class="fsElement fsContent"[^>]*>(.*?)</section>',
                          page_html, re.S):
        title = re.search(r'<h2 class="fsElementTitle"[^>]*>(.*?)</h2>', sec, re.S)
        if not title:
            continue
        role = " ".join(html_lib.unescape(_TAG.sub(" ", title.group(1))).split())
        if not re.fullmatch(_ROLE, role, re.I):
            continue
        dm = DIST.search(" ".join(_TAG.sub(" ", sec).split()))
        if not dm:
            print("  note %-12s officer block %r names no district — not attached"
                  % (county, role), file=sys.stderr)
            continue
        d = int(dm.group(1))
        if d in out:
            raise RuntimeError("%s: two officer blocks claim district %d" % (county, d))
        out[d] = role_case(role)
    return out


def _surname(name):
    toks = [t for t in re.split(r"[^A-Za-z]+", name) if len(t) > 1]
    return toks[-1].lower() if toks else ""


def scrape_constituent_county(spec):
    """All seats or nothing, read from a paginated Finalsite directory."""
    county = spec["name"]
    page = fetch(spec["page_url"])
    els = sorted(set(_DIR_ELEMENT.findall(page)))
    gids = sorted(set(_GROUP_ID.findall(page)))
    if len(els) != 1 or len(gids) != 1:
        raise RuntimeError("%s: the page carries %d constituent director(ies) and %d "
                           "search group(s) — expected one of each; re-read it before "
                           "moving this entry" % (county, len(els), len(gids)))
    root = spec["page_url"].split("/", 3)
    base = "%s//%s/fs/elements/%s" % (root[0], root[2], els[0])
    label = _PAGE_LABEL.search(page)
    if not label:
        raise RuntimeError("%s: the directory states no total — it may have stopped "
                           "paginating; re-read it" % county)
    total = int(label.group(3))
    if total != spec["seats"]:
        raise RuntimeError("%s: the directory holds %d constituents and the board seats "
                           "%d — one of the two has changed"
                           % (county, total, spec["seats"]))

    found = {}
    pages = -(-total // CONSTITUENT_PAGE_CAP)
    for n in range(1, pages + 1):
        got = _constituent_items(
            fetch("%s?const_page=%d&const_search_group_ids=%s" % (base, n, gids[0])))
        if not got:
            raise RuntimeError("%s: page %d of %d parsed no members — the group id no "
                               "longer paginates this directory" % (county, n, pages))
        for d, row in got.items():
            if d in found and found[d] != row:
                raise RuntimeError("%s: district %d appears twice with different "
                                   "members (%r, %r)" % (county, d, found[d], row))
            found[d] = row
    want = set(range(1, spec["seats"] + 1))
    if set(found) != want:
        raise RuntimeError("%s: the directory resolved %d of %d districts (missing %s)"
                           % (county, len(found), spec["seats"],
                              sorted(want - set(found))))
    names = [r["name"] for r in found.values()]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise RuntimeError("%s: the same person is filed under two districts (%s)"
                           % (county, dupes))

    out = {}
    for d in sorted(found):
        row = {"name": found[d]["name"], "vacant": False, "role": None}
        email = found[d]["email"]
        if email:
            alias = _DISTRICT_ALIAS.match(email.split("@")[0])
            if alias and int(alias.group(1)) != d:
                raise RuntimeError(
                    "%s: district %d's row carries %s — the address names another "
                    "district, so the page has reshuffled under this parser"
                    % (county, d, email))
            row["email"] = email
        out[str(d)] = row

    for d, role in sorted(_constituent_officers(page, county).items()):
        if str(d) not in out:
            raise RuntimeError("%s: an officer block names district %d, which the "
                               "directory does not" % (county, d))
        listed = out[str(d)]["name"]
        block_name = None
        for sec in re.findall(r'<section class="fsElement fsContent"[^>]*>(.*?)</section>',
                              page, re.S):
            if not re.search(r"District\s*%d\b" % d, _TAG.sub(" ", sec)):
                continue
            h5 = re.search(r"<h5[^>]*>(.*?)(?:<br|</h5>)", sec, re.S)
            if h5:
                block_name = " ".join(html_lib.unescape(_TAG.sub(" ", h5.group(1))).split())
            break
        if block_name and _surname(block_name) != _surname(listed):
            raise RuntimeError(
                "%s: the %s block names %r and the directory puts %r in district %d — "
                "the officer cards and the member list disagree, ship neither"
                % (county, role, block_name, listed, d))
        if block_name and block_name != listed:
            print("  note %-12s district %s: officer card says %r, member list says %r "
                  "— shipping the member list" % (county, d, block_name, listed),
                  file=sys.stderr)
        out[str(d)]["role"] = role
        print("  role %-12s district %s: %s -> %s" % (county, d, listed, role),
              file=sys.stderr)
    return out


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


# COUNTIES WHOSE ONE VACANCY CARRIES NO DISTRICT NUMBER. Marinette lists its
# board alphabetically by surname, every row "Name - District N" except one
# that reads only "VACANT SEAT" with the ward description beneath it. Twenty-
# nine districts are named, one is not, and the county states one empty seat.
#
# ASSIGNING THAT SEAT IS AN INFERENCE, and it is opt-in per county rather than
# a general rule because a page that drops a numbered row for any OTHER reason
# would otherwise get a silently invented vacancy. The gate is arithmetic and
# is checked on every run: EXACTLY ONE district unclaimed AND EXACTLY ONE
# vacancy line that carries no district number. If the page ever names two
# vacancies, or loses a second row, the county fails its count guard as before
# and nothing is inferred.
ELIMINATION_VACANCY = {"55075"}      # Marinette


def eliminated_vacancy(lines, seats, found, vacant, county):
    """The single unclaimed district, when the page states a single unnumbered
    vacancy. Returns the district number, or None when the arithmetic does not
    force it."""
    unclaimed = [d for d in range(1, seats + 1) if d not in found and d not in vacant]
    if len(unclaimed) != 1:
        return None
    loose = [l for l in lines if VACANT.search(l) and not DIST.search(l)]
    if len(loose) != 1:
        print("  note %-12s %d unnumbered vacancy line(s) for %d unclaimed district(s)"
              " — nothing inferred" % (county, len(loose), len(unclaimed)), file=sys.stderr)
        return None
    print("  infer %-12s district %d is the county's one unnumbered %r row "
          "(29 of 30 numbered, one vacancy stated)"
          % (county, unclaimed[0], loose[0].strip()), file=sys.stderr)
    return unclaimed[0]


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
        vacant = vacant_districts(lines, seats, strategy)
        found = READINGS[strategy](lines)
    for d in vacant:
        found.pop(d, None)          # the county says the seat is empty; believe it
    if fips in ELIMINATION_VACANCY:
        d = eliminated_vacancy(lines, seats, found, vacant, name)
        if d is not None:
            vacant.add(d)
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
    jobs += [(d["fips"], d["name"], d["seats"], "document", d) for d in DOCUMENT_ROSTERS]
    jobs += [(c["fips"], c["name"], c["seats"], "constituent", c) for c in CONSTITUENT_COUNTIES]
    jobs += [(fips, name, seats, strategy, url) for fips, name, seats, strategy, url in COUNTIES]
    for fips, name, seats, strategy, src in jobs:
        if only and fips != only:
            continue
        try:
            if strategy == "arcgis":
                districts = scrape_arcgis_county(src)
                source_url = src["source_url"]
            elif strategy == "document":
                districts = document_county(src)
                source_url = src["source_url"]
            elif strategy == "constituent":
                districts = scrape_constituent_county(src)
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
        if strategy == "document":
            # the file must SAY the roster was not re-read this run; a reader
            # of the JSON should never have to know which table it came from
            counties[fips]["carried_from_document"] = True
            counties[fips]["read_on"] = src["read_on"]
            counties[fips]["how"] = src["how"]
        vac = sum(1 for d in districts.values() if d["vacant"])
        print("  ok   %-12s %d seats%s" % (name, seats, " (%d vacant)" % vac if vac else ""),
              file=sys.stderr)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"counties": counties, "failures": failures}, f, indent=2, ensure_ascii=False)
    total = sum(c["seats"] for c in counties.values())
    print("wrote %s: %d/%d counties, %d seats%s"
          % (out_path, len(counties),
             len(COUNTIES) + len(ARCGIS_COUNTIES) + len(DOCUMENT_ROSTERS)
             + len(CONSTITUENT_COUNTIES), total,
             ", %d county/counties missed" % len(failures) if failures else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

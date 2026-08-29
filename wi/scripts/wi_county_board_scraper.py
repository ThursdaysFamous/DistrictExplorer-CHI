#!/usr/bin/env python3
"""
Scrape county board supervisors from the 29 Wisconsin counties that publish a
district-keyed member list. Stage 1 of the pair; build_wi_county_board_roster.py
turns the intermediate JSON into data/app/county-board-members.json.

WHY ONLY TWENTY-NINE OF SEVENTY-TWO
-----------------------------------
Wisconsin publishes county board DISTRICTS statewide (Wis. Stat. 5.15(4)(br)1,
see build_wi_supervisory_districts.py) and publishes the PEOPLE in them
nowhere: each county names its own supervisors, 72 different ways. Twenty-nine
pair a district with a person in a form a parser can read (plus Milwaukee and
Racine off their own GIS layers, below). The rest are not oversights and are
recorded as such:

  * Kenosha and Ozaukee publish district MAPS — a page per district with a PDF
    and no name on it anywhere. They were checked three pages deep apiece.
    This file used to claim 23 counties; that count came from a sweep that
    tested district NUMBERS, and numbers are what a map index has.
  * Marinette publishes 29 of its 30 seats. District 26 is an unnumbered
    "VACANT SEAT" row in an alphabetical list, and assigning it by elimination
    would be an inference the county never wrote, so the county stays out.
  * The rest could not be read: 9 answer 403 to a datacenter client and hold
    it against browser headers (Marathon, La Crosse, Outagamie, Fond du Lac,
    Lafayette, Lincoln, Monroe, Rock, Sheboygan), Taylor sits behind an
    sgcaptcha challenge answering 202 (an access control, not an obstacle to
    route around), Forest does not resolve, and the remainder publish their
    members as PDFs, images or prose with no district column.
    FOND DU LAC LEFT THAT BUCKET ON 2026-08-29 WITHOUT ITS BLOCK LIFTING —
    the 403 is still there and still measured; what changed is that the page
    behind it is now read through the Internet Archive. See ARCHIVE_COUNTIES.

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

A COUNTY'S ROSTER NOW ARRIVES BY ONE OF FOUR CARRIERS (2026-08-29)
------------------------------------------------------------------
COUNTIES is the original and still the biggest: a page this client can fetch,
read by one of five pinned line readings. ARCGIS_COUNTIES reads Milwaukee's and
Racine's supervisors off their own GIS layers, because those two counties'
SITES refuse this client while their GIS does not. DOCUMENT_ROSTERS carries
Taylor, whose every host answers a captcha, from a page the operator read in a
browser — with a NOT RE-READ line and the document's age printed every run,
because pretending a weekly check happens would be the lie.

ARCHIVE_COUNTIES is the fourth and it is the one that needs its reasoning
stated. Fond du Lac's directory is richer than most of the pages that already
ship — name, district, county e-mail and phone for all twenty-five seats, the
Chair and both Vice Chairs titled — and www.fdlco.wi.gov answers this client
HTTP 403 from AkamaiGHost on every path, every user-agent and both schemes.
The county is not withholding anything; a CDN is refusing a datacenter
address. The Internet Archive's crawler has been taking copies of that same
public page for years, so the page is read from there.

THE LINE THIS SITS ON. A captcha is an access control and is never worked
around here (Taylor is the standing example). A client-fingerprint 403 is not
defeated either — nothing in this file forges a fingerprint or retries the
county's own server in disguise. Reading a public archive of a public page is
a third party's copy of a document the county published to the world, and it
is the arrangement Illinois already runs for Kendall and McHenry. The
difference from Taylor is not politeness, it is REPEATABILITY: an archive can
be re-read every week and a browser session in someone's memory cannot.

WHICH IS WHY FRESHNESS IS GATED AND NOT ASSUMED. The failure mode of an
archive is not a wrong answer, it is a stale one that looks current — see the
two measurements recorded above ARCHIVE_COUNTIES, one of which would have
stitched five supervisors from before an April election onto twenty from
after it. Save Page Now is asked for a new copy on every run, the copy's age
is checked before it is parsed, and the pages must have been captured close
together. A county that cannot be read FRESHLY is skipped for that run,
exactly like a county whose page has reshaped.

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
import urllib.parse
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


# =============================================================================
# COUNTIES WHOSE ROSTER RIDES THE INTERNET ARCHIVE (added 2026-08-29)
# =============================================================================
# THE THIRD CARRIER, after a page this client can fetch and a county's own GIS
# layer. Fond du Lac publishes a County Board Supervisors directory that is
# richer than most of the counties that already ship — a name, a district, a
# county e-mail and a phone for all twenty-five seats, with the Chair and both
# Vice Chairs titled — and this client cannot read a byte of it: every path on
# www.fdlco.wi.gov answers HTTP 403 from AkamaiGHost with the CDN's own "Access
# Denied" body, to every user-agent tried, over http and https alike. That is a
# client-fingerprint block on a datacenter address, not a refusal to publish,
# and the proof is that the Internet Archive's own crawler has been fetching
# the page successfully for years.
#
# So the county's own page is read through a public archive OF THAT PAGE. Not
# evasion — nothing here defeats the block, and a captcha would end the matter
# (see Taylor) — a second reader of a document the county publishes to the
# world, with the copy's timestamp carried into the run log for provenance.
# The Illinois side reached the same arrangement for Kendall and McHenry first
# (scripts/kendall_county_board_scraper.py's WaybackFetcher); this is that
# posture with Wisconsin's own gates around it.
#
# FRESHNESS IS THE WHOLE PROBLEM, AND IT IS MEASURED RATHER THAN ASSUMED.
# A snapshot is a photograph, and an old one shows a board that has since
# changed while looking exactly like a current one. Two measurements set the
# rules below, both taken 2026-08-29 from the Archive's own CDX index:
#
#   1. NATURAL CRAWLING IS NOT ENOUGH. The captures of page 1 over the past
#      year run 2025-08-15, 2025-10-02, ... 2026-02-09, 2026-05-05, 2026-05-11
#      and then nothing — gaps of 48, 85 and (at the time of writing) 110 days.
#      A roster resting on whatever the crawler happened to take would be
#      months stale for months at a time and never say so. SAVE PAGE NOW is
#      therefore the primary route: each run asks the Archive to take a FRESH
#      capture of each page, and only falls back to the newest existing one.
#   2. THE TWO PAGES CAN BE FROM DIFFERENT WORLDS. The directory paginates at
#      twenty, so twenty-five supervisors need two fetches — and on the day
#      this was written the newest capture of page 1 was 2026-05-11 while the
#      newest of page 2 was 2026-03-16. Wisconsin's county boards are ALL
#      reseated at the April spring election, so those two captures sit on
#      opposite sides of one, and stitching them would have shipped five
#      supervisors (districts 2, 4, 7, 16 and 21) who might no longer hold
#      their seats, presented beside twenty who certainly did. Nothing about
#      the merged result would have looked wrong. Hence PAGE_SPREAD_DAYS: the
#      pages must be captured close to each other as well as recently.
#
# Both limits FAIL LOUDLY rather than degrading. A county that cannot be read
# freshly is skipped for the run and its card goes back to linking the board,
# which is the same thing that happens to any county whose page reshapes.
WAYBACK_MAX_AGE_DAYS = 45     # Kendall's number, and for Kendall's reason
PAGE_SPREAD_DAYS = 14         # see measurement 2 above — an April election is
                              # the thing this stops a merge from straddling
WAYBACK_AVAILABLE = "https://archive.org/wayback/available?url=%s"
WAYBACK_SAVE = "https://web.archive.org/save/%s"
WAYBACK_RAW = "https://web.archive.org/web/%sid_/%s"

ARCHIVE_COUNTIES = [
    {
        "fips": "55039", "name": "Fond Du Lac", "seats": 25,
        # Page 1 is the source_url a reader is sent to; page 2 exists only
        # because the county's directory widget paginates at twenty. The pager
        # states its own arithmetic ("1 - 20 of 25 items"), which is what the
        # gates below check rather than trusting this list to stay complete.
        "pages": [
            "https://www.fdlco.wi.gov/government/county-board-supervisors",
            "https://www.fdlco.wi.gov/government/county-board-supervisors/-npage-2",
        ],
        "source_url": "https://www.fdlco.wi.gov/government/county-board-supervisors",
        "email_domain": "@fdlco.wi.gov",
        "min_emails": 23,     # 25 today; a page that stops publishing them fails
        "min_phones": 23,
    },
]


def _spn_save(url):
    """Ask Save Page Now for a fresh capture; return its 14-digit timestamp.

    Anonymous by default. ARCHIVE_SPN_ACCESS_KEY / ARCHIVE_SPN_SECRET_KEY (the
    same repo secrets Illinois' Kendall and McHenry workflows already pass)
    switch on the SPN2 job API, which is the reliable path when a shared runner
    address has spent the anonymous quota. Absent keys are not an error.
    """
    key = os.environ.get("ARCHIVE_SPN_ACCESS_KEY")
    secret = os.environ.get("ARCHIVE_SPN_SECRET_KEY")
    if key and secret:
        try:
            data = urllib.parse.urlencode({"url": url}).encode()
            req = urllib.request.Request(
                "https://web.archive.org/save", data=data,
                headers=dict(UA, Accept="application/json",
                             Authorization="LOW %s:%s" % (key, secret)))
            with urllib.request.urlopen(req, timeout=60) as r:
                job = json.load(r).get("job_id")
            if job:
                for _ in range(30):          # ~2.5 minutes, SPN2's own pace
                    time.sleep(5)
                    req = urllib.request.Request(
                        "https://web.archive.org/save/status/" + job,
                        headers=dict(UA, Accept="application/json",
                                     Authorization="LOW %s:%s" % (key, secret)))
                    with urllib.request.urlopen(req, timeout=30) as r:
                        st = json.load(r)
                    if st.get("status") == "success":
                        return st.get("timestamp")
                    if st.get("status") == "error":
                        break
        except Exception as e:              # noqa: BLE001 - save is best-effort
            print("    SPN2 save failed (%s): %s" % (url, e), file=sys.stderr)
    try:
        req = urllib.request.Request(WAYBACK_SAVE % url, headers=UA)
        with urllib.request.urlopen(req, timeout=180) as r:
            m = re.search(r"/web/(\d{14})", r.geturl() or "")
            if not m:
                m = re.search(r"/web/(\d{14})", r.headers.get("Content-Location", "") or "")
            if m:
                return m.group(1)
    except Exception as e:                  # noqa: BLE001 - save is best-effort
        print("    Save Page Now unavailable (%s): %s" % (url, e), file=sys.stderr)
    return None


def _wayback_latest(url):
    """Timestamp of the newest existing snapshot, or None."""
    try:
        req = urllib.request.Request(
            WAYBACK_AVAILABLE % urllib.parse.quote(url, safe=""), headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            snap = (json.load(r).get("archived_snapshots") or {}).get("closest") or {}
        return snap.get("timestamp") or None
    except Exception:                       # noqa: BLE001 - reachability probe
        return None


BLOCK_PAGE = re.compile(r"(?i)<title>\s*(?:Access Denied|Just a moment)")


def _snapshot_age_days(ts):
    import datetime
    taken = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S").replace(
        tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - taken).days


def fetch_archived(url):
    """(html, timestamp) for the county's page, read through the Archive.

    A fresh capture is REQUESTED first and the newest existing one is only the
    fallback; either way the copy's age is checked before it is parsed, so a
    stale archive fails the county loudly instead of shipping old officeholders
    behind a current-looking card.
    """
    ts = _spn_save(url) or _wayback_latest(url)
    if ts is None:
        raise RuntimeError("no archive snapshot available for %s" % url)
    age = _snapshot_age_days(ts)
    if age > WAYBACK_MAX_AGE_DAYS:
        raise RuntimeError(
            "the newest archive copy of %s is %d days old (limit %d) and Save Page "
            "Now did not take a fresh one — refusing to ship officeholders read "
            "from it" % (url, age, WAYBACK_MAX_AGE_DAYS))
    page = fetch(WAYBACK_RAW % (ts, url))
    if BLOCK_PAGE.search(page):
        raise RuntimeError("the archived copy of %s is itself a block page (%s)"
                           % (url, ts))
    return page, ts


def fetch_page(url):
    """(html, archived_at_or_None) — the county's own server first, the Archive
    second. The direct rung costs one request and is tried on every run rather
    than being written off: this project has twice recorded a county as blocked
    on the strength of one client's view (Knox's website, Gallatin's TLS chain),
    and a block that lifts should be noticed by the scraper, not by a person."""
    try:
        page = fetch(url, timeout=30)
        if not BLOCK_PAGE.search(page):
            return page, None
    except Exception:                       # noqa: BLE001 - the expected path
        pass
    return fetch_archived(url)


# --- reading a Granicus business-directory page -------------------------------
# The generic readers above flatten a page to lines and hunt for a district
# beside a name. This county's directory is STRUCTURED — one <h2 class=
# "detail-title"> per supervisor followed by a labelled <ul class="detail-list">
# — so it is read as the markup it is, which is what makes the e-mail and phone
# reachable at all. Deliberately a separate reader rather than a sixth reading
# direction: the thirty counties on the line readers keep byte-identical
# behaviour, the same reason `_windowed_strict` did not become a flag on
# `_windowed`.
_ENTRY = re.compile(r'(?is)<h2[^>]*class="[^"]*detail-title[^"]*"[^>]*>(.*?)</h2>\s*'
                    r'(?:<ul[^>]*class="[^"]*detail-list[^"]*"[^>]*>(.*?)</ul>)?')
_FIELD = re.compile(r'(?is)<span[^>]*detail-list-label[^>]*>(.*?)</span>\s*'
                    r'<span[^>]*detail-list-value[^>]*>(.*?)</span>')
_MAILTO = re.compile(r'(?i)href="mailto:([^"]+)"')
_PAGER = re.compile(r"(\d+)\s*[-–]\s*(\d+)\s+of\s+(\d+)\s+items")
# A SUFFIX IS NEVER ONE LETTER, and that rule cost a name. The county writes
# "Sippel, James V." — a middle initial — and a suffix pattern that accepted a
# lone roman "V" flipped it to "James Sippel V.", a plausible, wrong, and
# entirely silent rename. Jr/Sr/II/III/IV are two characters or more; a single
# letter, with or without its period, is an initial.
_NAME_SUFFIX = re.compile(r"^(?:Jr\.?|Sr\.?|II|III|IV)$", re.I)


def _flat(fragment):
    return " ".join(html_lib.unescape(_TAG.sub(" ", fragment or "")).split())


def flip_surname_first(name):
    """"Herlache, Thomas L. Jr." -> "Thomas L. Herlache Jr."

    The shared `clean()` flips a comma too, but it treats everything after the
    comma as given names, so a generational suffix ends up in the middle of the
    person's name. This directory prints both shapes.
    """
    if "," not in name:
        return name
    last, rest = [x.strip() for x in name.split(",", 1)]
    toks = rest.split()
    suffix = toks.pop() if toks and _NAME_SUFFIX.match(toks[-1]) else ""
    given = " ".join(toks)
    out = ("%s %s" % (given, last)).strip() if given else last
    return ("%s %s" % (out, suffix)).strip()


def read_directory_page(page, seats, spec):
    """(members_by_district, first_item, last_item, total) for one page."""
    pager = _PAGER.search(_flat(page))
    if not pager:
        raise RuntimeError("no pager on the page — the directory has changed shape")
    first, last, total = (int(x) for x in pager.groups())
    if total != seats:
        raise RuntimeError(
            "the directory says it holds %d supervisors and this county is entered "
            "with %d seats — one of the two has changed" % (total, seats))

    out, addresses = {}, 0
    for title_frag, list_frag in _ENTRY.findall(page):
        title = _flat(title_frag)
        m = DIST.search(title)
        if not m:
            continue
        district = int(m.group(1))
        if not 1 <= district <= seats:
            raise RuntimeError("the directory names District %d on a %d-district board"
                               % (district, seats))
        if district in out:
            raise RuntimeError("District %d appears twice on one page" % district)
        rest, role = split_role(DIST.sub(" ", title, count=1))
        if VACANT.search(rest):
            out[district] = {"name": None, "vacant": True, "role": None}
            continue
        row = {"name": flip_surname_first(rest.strip().strip("-–—").strip()),
               "vacant": False, "role": role}
        for label_frag, value_frag in _FIELD.findall(list_frag or ""):
            label = _flat(label_frag).rstrip(":").lower()
            if label == "address":
                # READ SO IT CAN BE REFUSED, never carried. Every one of these
                # is a supervisor's HOME (rural routes, "N5528 Ledgetop
                # Drive") — this fleet does not ship a home address even where
                # the county publishes one, the same call Taylor's document
                # roster records. Counting them is how the run proves it is
                # still reading the field it is declining, rather than having
                # quietly stopped seeing it.
                addresses += 1
            elif label == "email":
                mm = _MAILTO.search(value_frag)
                if mm:
                    email = html_lib.unescape(mm.group(1)).strip()
                    if email.lower().endswith(spec["email_domain"]):
                        row["email"] = email
            elif label == "phone":
                row["phone"] = _flat(value_frag)
        out[district] = row

    want = last - first + 1
    if len(out) != want:
        raise RuntimeError("the pager says items %d-%d (%d supervisors) and %d were "
                           "read" % (first, last, want, len(out)))
    if not addresses:
        raise RuntimeError("not one Address row on a page of %d supervisors — the "
                           "directory has changed shape and the field this build "
                           "deliberately drops can no longer be seen" % len(out))
    return out, first, last, total


def scrape_archive_county(spec):
    """All seats or nothing, from a paginated directory read through the Archive."""
    seats = spec["seats"]
    members, spans, stamps = {}, [], []
    for url in spec["pages"]:
        page, archived_at = fetch_page(url)
        got, first, last, _total = read_directory_page(page, seats, spec)
        for d, row in got.items():
            if d in members:
                raise RuntimeError("District %d appears on two pages" % d)
            members[d] = row
        spans.append((first, last))
        stamps.append(archived_at)
        print("    %-4s %s  items %d-%d"
              % ("live" if archived_at is None else archived_at[:8],
                 url.rsplit("/", 1)[-1][:34], first, last), file=sys.stderr)

    # THE PAGES MUST TILE THE BOARD, and be read from one moment in its life.
    covered = []
    for first, last in sorted(spans):
        covered.extend(range(first, last + 1))
    if covered != list(range(1, seats + 1)):
        raise RuntimeError("the pages fetched cover items %s of a %d-supervisor "
                           "directory — a page has been added or dropped"
                           % (sorted(spans), seats))
    # A PAGE THE COUNTY SERVED DIRECTLY COUNTS AS AGE ZERO, which is the whole
    # reason this is computed over ages rather than over the archive stamps: if
    # the block ever lifts for one request and not the next, page 1 arrives from
    # today and page 2 from the newest snapshot, and comparing only the stamps
    # would find one date, no spread, and nothing to complain about — the exact
    # straddle this gate exists to stop, wearing a fresher coat.
    ages = [0 if t is None else _snapshot_age_days(t) for t in stamps]
    spread = max(ages) - min(ages)
    if spread > PAGE_SPREAD_DAYS:
        raise RuntimeError(
            "the pages were captured %d days apart (limit %d) — a Wisconsin board "
            "is reseated every April, so a merge across that gap can pair "
            "supervisors who never sat together" % (spread, PAGE_SPREAD_DAYS))

    if set(members) != set(range(1, seats + 1)):
        missing = sorted(set(range(1, seats + 1)) - set(members))
        raise RuntimeError("resolved %d of %d districts (missing %s)"
                           % (len(members), seats, missing))
    named = [m["name"] for m in members.values() if not m["vacant"]]
    if len(set(named)) != len(named):
        dupes = sorted({n for n in named if named.count(n) > 1})
        raise RuntimeError("the same person is filed under two districts (%s)" % dupes)
    emails = sum(1 for m in members.values() if m.get("email"))
    phones = sum(1 for m in members.values() if m.get("phone"))
    if emails < spec["min_emails"]:
        raise RuntimeError("%d county e-mail addresses resolved, floor is %d"
                           % (emails, spec["min_emails"]))
    if phones < spec["min_phones"]:
        raise RuntimeError("%d phone numbers resolved, floor is %d"
                           % (phones, spec["min_phones"]))
    return {str(d): members[d] for d in sorted(members)}, stamps


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
    jobs += [(a["fips"], a["name"], a["seats"], "archive", a) for a in ARCHIVE_COUNTIES]
    jobs += [(d["fips"], d["name"], d["seats"], "document", d) for d in DOCUMENT_ROSTERS]
    jobs += [(fips, name, seats, strategy, url) for fips, name, seats, strategy, url in COUNTIES]
    for fips, name, seats, strategy, src in jobs:
        if only and fips != only:
            continue
        try:
            archived_at = None
            if strategy == "arcgis":
                districts = scrape_arcgis_county(src)
                source_url = src["source_url"]
            elif strategy == "archive":
                districts, archived_at = scrape_archive_county(src)
                source_url = src["source_url"]
            elif strategy == "document":
                districts = document_county(src)
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
        if strategy == "archive" and any(archived_at or []):
            # SAME PRINCIPLE AS THE DOCUMENT LINE ABOVE: the file records that
            # this county's page was read through a public archive and WHEN
            # each copy was taken, so nobody has to know which table it came
            # from to know how fresh it is. A page the county served directly
            # carries no stamp, which is how a lifted block shows up here.
            counties[fips]["read_via_archive"] = True
            counties[fips]["archived_at"] = archived_at
        vac = sum(1 for d in districts.values() if d["vacant"])
        print("  ok   %-12s %d seats%s" % (name, seats, " (%d vacant)" % vac if vac else ""),
              file=sys.stderr)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"counties": counties, "failures": failures}, f, indent=2, ensure_ascii=False)
    total = sum(c["seats"] for c in counties.values())
    print("wrote %s: %d/%d counties, %d seats%s"
          % (out_path, len(counties),
             len(COUNTIES) + len(ARCGIS_COUNTIES) + len(ARCHIVE_COUNTIES)
             + len(DOCUMENT_ROSTERS), total,
             ", %d county/counties missed" % len(failures) if failures else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

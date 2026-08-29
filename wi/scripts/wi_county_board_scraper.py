#!/usr/bin/env python3
"""
Scrape county board supervisors from the 31 Wisconsin counties that publish a
district-keyed member list. Stage 1 of the pair; build_wi_county_board_roster.py
turns the intermediate JSON into data/app/county-board-members.json.

WHY ONLY THIRTY-ONE OF SEVENTY-TWO
----------------------------------
Wisconsin publishes county board DISTRICTS statewide (Wis. Stat. 5.15(4)(br)1,
see build_wi_supervisory_districts.py) and publishes the PEOPLE in them
nowhere: each county names its own supervisors, 72 different ways. Thirty-one
pair a district with a person in a form a parser can read (plus Milwaukee and
Racine off their own GIS layers, below). The rest are not oversights and are
recorded as such:

  * Kenosha and Ozaukee publish district MAPS — a page per district with a PDF
    and no name on it anywhere. They were checked three pages deep apiece.
    This file used to claim 23 counties; that count came from a sweep that
    tested district NUMBERS, and numbers are what a map index has.
  * Marinette publishes 29 of its 30 seats: District 26 is an unnumbered
    "VACANT SEAT" row in an alphabetical list. It kept the county out until
    2026-08-29, when `eliminated_vacancy` made assigning that one seat an
    arithmetic gate rather than a guess — it ships, and this bullet stays as
    the record of why it did not.
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

A FIFTH SHAPE HAS NO DIRECTION TO PIN AT ALL (Sauk, 2026-08-29):

    fielded     the page LABELS its own fields — "Supervisor: Schroder,
                Palmer" — so the name is not near a district, it is in a
                field the page names; see `_fielded`

That is the whole point of it. `before` and `after` are one extraction shifted
by one BECAUSE adjacency is all those pages give; a labelled field cannot be
read off by one, and a page tweak cannot silently flip it. Sauk resolves all
thirty-one seats where every windowed reading resolves ZERO — `is_name` rejects
its "Supervisor: ..." line on the word supervisor and its ward lines on
town/city/village/ward, so the county sat in the bucket below reading as though
it published nothing. It publishes more than most: a name, a county e-mail, a
phone and the district's ward composition per seat. THE READER WAS THE BLOCK
FOR A THIRD TIME (nine counties on 2026-08-27, Taylor's host on 2026-08-29,
this reader now) — and the fielded shape brings its own witnesses with it,
which the FIELDED_PINS comment sets out: the e-mail on each row checks that
row's own name, and the ward composition checks the county's district NUMBERING
against LTSB's, the one thing no other county in this file can prove.

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
     "trempealeau_county_board_of_supervisors.php"),
    # --- 2026-08-29: the first county read by its page's own FIELD LABELS ---
    # co.sauk.wi.us/countyboard/sauk-county-board-members links this list as
    # "Committee Database: 2026-2028 Sauk County Board Supervisors" under the
    # heading "Term of Office: April 21, 2026 - April 18, 2028", so it is the
    # county's own current-term roster and not a stray application.
    ("55111", "Sauk", 31, "fielded",
     "https://saukdomino.co.sauk.wi.us/Internet/Applications/main.nsf/"
     "publicDistrictList.xsp"),]

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


# --- the fielded reading: a page that LABELS its own fields -------------------
# SAUK IS THE ONE COUNTY WITH NO READING DIRECTION TO PIN, because its page
# does not put a name NEAR a district — it puts one in a field whose own label
# says "Supervisor:". Everything the rest of this file pins per county exists
# to survive that ambiguity; here it does not arise, and a page tweak cannot
# silently flip a reading that keys off the page's own words.
#
# The county runs an IBM Domino/XPages application whose per-district panel is
# a heading ("DISTRICT #4") followed by the district's WARD COMPOSITION, then
# labelled Supervisor / Phone / Email / Address rows. The generic readings are
# blind to it in both directions: `is_name` rejects the "Supervisor: ..." line
# on the word supervisor, and rejects every ward line on town/city/village/ward
# — so all three windowed readings resolve ZERO of the thirty-one seats. That
# is a reader limit, not a publisher gap, and it is exactly the shape the
# 2026-08-27 re-sweep found nine counties sitting in.
PANEL_HEAD = re.compile(r"(?i)^district\s*#\s*(\d{1,2})$")
FIELD = re.compile(r"(?i)^(supervisor|phone|email)\s*:\s*(.+)$")
# The application has a template of its own for an empty seat — the panel
# renders a `NoSupervisorPanel` reading "There is no supervisor for this
# District." — so a vacancy here is the county's own statement, not an absence
# this reader inferred. `VACANT` cannot see it: the sentence never says vacant.
NO_SUPERVISOR = re.compile(r"(?i)\bno supervisor for this\s+district\b")
# Ward lines, the witness input: "Village Of Lake Delton Wards 1, 2, 3 and 7",
# "Town of Baraboo, Ward 4", "Town of Dellona, Ward 1 and Ward 2".
WARD_LINE = re.compile(r"(?i)^(town|city|village)\s+of\s+(.+?)[,\s]+wards?\s+(.+)$")


def flip_last_first(text):
    """"Deitrich, John M." -> "John M. Deitrich", punctuation as published.

    `clean` would do the flip and also strip the trailing period off a middle
    initial — its end-strip runs before the comma split, which is why the
    counties already shipping carry names like "Terry M Spencer". Those bytes
    are not re-litigated here; this reading keeps what the county printed.
    """
    text = " ".join(text.split())
    if "," not in text:
        return text
    a, b = [x.strip() for x in text.split(",", 1)]
    if SUFFIX.match(b):
        return "%s %s" % (a, b)     # "Schaefer, II" is a suffix, never a flip
    return "%s %s" % (b, a)


def _fielded(lines):
    """district -> {name, role, email, phone}, plus the seats the page empties."""
    heads = []
    for i, line in enumerate(lines):
        m = PANEL_HEAD.match(line)
        if m:
            heads.append((i, int(m.group(1))))
    seen = [d for _, d in heads]
    if len(set(seen)) != len(seen):
        dupes = sorted({d for d in seen if seen.count(d) > 1})
        raise RuntimeError("the page carries two panels for district(s) %s — a "
                           "later one would silently overwrite an earlier" % dupes)
    found, vacant, wards = {}, set(), {}
    for k, (i, d) in enumerate(heads):
        j = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        panel = lines[i + 1:j]
        row = {"name": None, "role": None, "email": None, "phone": None}
        for line in panel:
            m = FIELD.match(line)
            if m:
                label, value = m.group(1).lower(), m.group(2).strip()
                if label == "supervisor" and row["name"] is None:
                    row["name"] = flip_last_first(value)
                elif label == "phone" and row["phone"] is None:
                    row["phone"] = value
                elif label == "email" and row["email"] is None:
                    row["email"] = value
                continue
            wm = WARD_LINE.match(line)
            if wm:
                ctv = {"town": "T", "city": "C", "village": "V"}[wm.group(1).lower()]
                mcd = re.sub(r"[^a-z]", "", wm.group(2).lower())
                for n in re.findall(r"\d+", wm.group(3)):
                    wards.setdefault(d, set()).add((ctv, mcd, int(n)))
        if row["name"]:
            found[d] = row
        elif NO_SUPERVISOR.search(" ".join(panel)):
            vacant.add(d)
        # a panel that is neither is left unresolved: the all-seats guard fails
    return found, vacant, wards


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


# --- what a fielded county is held to ----------------------------------------
# THREE WITNESSES, none of them the page checking itself.
#
# ONE, THE E-MAIL ON EVERY SEAT'S OWN ROW. Sauk prints a county mailbox beside
# each supervisor, and the county builds it as first.last@saukcountywi.gov —
# so a reading shifted by one would file a name under a district whose e-mail
# names somebody else, on all thirty rows at once. That is the shift this whole
# file pins reading directions to avoid, answered here per seat rather than by
# a pin. Twenty-nine of thirty agree exactly; the thirtieth is `name_fixes`.
#
# TWO, THE WARD COMPOSITION AGAINST LTSB. Each panel lists the wards the
# district is built from, and LTSB's statewide ward layer — the same service
# the app's Municipal Ward layer draws — carries a SUPERID on every ward. That
# makes the county's numbering checkable against the state's, which is what the
# roster's district key actually rests on: the map is LTSB's and the people are
# the county's, and nothing else in this file proves the two number their
# districts alike. Measured 2026-08-29: 117 of the county's 118 listed wards
# land in LTSB's same-numbered district, and BOTH one-district shifts land
# ZERO — the witness discriminates completely.
#
# THREE, THE CLERK'S OWN CANDIDATE FILING LIST for the 2026-2028 term, which
# is where `name_fixes` and `phone_owner` come from. It is a January snapshot
# of who FILED and is never used as a roster (it has District 1 as Jake Roxen,
# where the county's maintained directory names Wally Czuprynko), but it is an
# independent county document for a name and a phone number.
#
# NO ROLE IS ATTACHED, AND THAT IS DELIBERATE. This page marks no chair, and
# `attach_officer_roles` therefore has nothing to find — Sauk names its chair
# on a DIFFERENT page (co.sauk.wi.us/countyboard/county-board-contacts, "Tim
# McCumber County Board Chair"), and a role read off one page cannot honestly
# be sourced to another, since the roster carries one sourceUrl per county.
# Nothing is lost: the officer builder's chair reconciliation finds the Blue
# Book's "Tim McCumber" sitting in district 20 and CONFIRMS the dated book row
# rather than withholding it, and the county's own contacts page independently
# agrees with the book on both the name and the phone number district 20
# carries here.
LTSB_WARD_QUERY = ("https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/"
                   "services/WI_Municipal_Wards_Current/FeatureServer/0/query")

FIELDED_PINS = {
    "55111": {
        # ONE SEAT'S NAME AND E-MAIL DISAGREE. District 4 prints "Schroder,
        # Palmer" beside palmer.schroeder@saukcountywi.gov, and the Clerk's
        # candidate filing list for this very term prints "Palmer B.
        # Schroeder" — two county documents to one, so the surname the county
        # mails to is what ships. The pin asserts the page still prints the
        # misspelling: the day Sauk fixes its own record, this FAILS and the
        # entry is deleted rather than quietly correcting a name forever.
        "name_fixes": {4: ("Palmer Schroder", "Palmer Schroeder")},
        # A PHONE PUBLISHED FOR TWO PEOPLE IS NOT A PER-PERSON PHONE. Districts
        # 28 (Tatone) and 29 (Evert) both carry 608-963-4067; the Clerk's
        # filing list gives that number as Evert's and Tatone's as another, so
        # the directory has copied one supervisor's number onto a second seat.
        # Evert keeps it on two documents' agreement and Tatone's is WITHHELD —
        # the number this project holds for her is demonstrably his, and a
        # candidate's own January phone is not the county's answer to "how do
        # I reach my supervisor". Any duplicate NOT pinned here loses the
        # number on every seat that shares it, which is the safe direction.
        "phone_owner": {"6089634067": 29},
    },
}


def digits(text):
    return re.sub(r"[^0-9]", "", str(text or ""))


def _email_agrees(name, email):
    """first.last@ against the name on the same row — the anti-shift witness."""
    local = str(email or "").split("@")[0].lower()
    parts = [re.sub(r"[^a-z]", "", x) for x in local.split(".")]
    parts = [x for x in parts if x]
    toks = [re.sub(r"[^a-z]", "", t) for t in str(name or "").lower().split()]
    toks = [t for t in toks if t]
    if len(parts) < 2 or len(toks) < 2:
        return False
    return parts[0] == toks[0] and parts[-1] == toks[-1]


def _ward_witness(fips, county, wards, seats):
    """The county's own ward composition against LTSB's ward-level SUPERID.

    A FETCH FAILURE IS NOT A DISAGREEMENT. An unreachable witness says nothing
    about the roster, so it prints and stands aside; a witness that RUNS and
    disagrees fails the county, because then the two publishers no longer
    number the same districts and the roster's district key is the thing in
    doubt.
    """
    try:
        data = _fetch_json(
            LTSB_WARD_QUERY + "?where=CNTY_FIPS%%3D%%27%s%%27&outFields="
            "MCD_NAME,CTV,WARDID,SUPERID&returnGeometry=false&f=json" % fips)
        feats = data.get("features") or []
        if not feats:
            raise RuntimeError("no wards returned")
    except Exception as e:      # noqa: BLE001 - the witness, never the source
        print("  WITNESS SKIPPED %-9s LTSB ward layer unreachable (%s) — the "
              "roster ships unwitnessed this run" % (county, e), file=sys.stderr)
        return
    ltsb = {}
    for f in feats:
        a = f.get("attributes") or {}
        key = (a.get("CTV"), re.sub(r"[^a-z]", "", str(a.get("MCD_NAME", "")).lower()),
               int(str(a.get("WARDID") or 0)))
        ltsb.setdefault(int(a["SUPERID"]), set()).add(key)
    placed = sum(len(v) for v in wards.values())
    if placed < 2 * seats:
        raise RuntimeError("%s: the page lists only %d wards across %d districts — "
                           "it has stopped printing its ward composition, and the "
                           "numbering witness with it" % (county, placed, seats))
    hit = sum(len(v & ltsb.get(d, set())) for d, v in wards.items())
    shifts = [sum(len(v & ltsb.get(d + off, set())) for d, v in wards.items())
              for off in (1, -1)]
    print("  witness %-12s %d/%d listed wards in LTSB's own district (shifts %d/%d)"
          % (county, hit, placed, shifts[0], shifts[1]), file=sys.stderr)
    if any(shifts):
        raise RuntimeError("%s: %d of its listed wards land one district off in "
                           "LTSB's file — the two publishers may have renumbered "
                           "apart; re-read both before shipping"
                           % (county, max(shifts)))
    if hit < 0.95 * placed:
        raise RuntimeError("%s: only %d of %d listed wards land in LTSB's "
                           "same-numbered district — the county's composition and "
                           "the state's filing no longer describe one plan"
                           % (county, hit, placed))


def scrape_fielded_county(fips, county, seats, url):
    """All seats or nothing, then the witnesses — see FIELDED_PINS above."""
    lines = to_lines(fetch(url))
    found, vacant, wards = _fielded(lines)
    covered = set(found) | vacant
    if covered != set(range(1, seats + 1)):
        missing = sorted(set(range(1, seats + 1)) - covered)
        raise RuntimeError(
            "%s: resolved %d of %d districts (missing %s) under the 'fielded' "
            "reading — the page has changed shape; re-read it before moving this "
            "entry" % (county, len(covered), seats, missing))
    pins = FIELDED_PINS.get(fips, {})
    for d, (was, now) in sorted(pins.get("name_fixes", {}).items()):
        if found.get(d, {}).get("name") != was:
            raise RuntimeError(
                "%s: district %s no longer prints %r (it prints %r) — the pinned "
                "correction to %r has been overtaken by the county; delete it"
                % (county, d, was, found.get(d, {}).get("name"), now))
        found[d]["name"] = now
        print("  name %-12s district %s: %r -> %r (the county's own e-mail and "
              "the Clerk's filing list)" % (county, d, was, now), file=sys.stderr)
    names = [r["name"] for r in found.values()]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise RuntimeError("%s: the same person is filed under two districts (%s)"
                           % (county, dupes))
    for d in sorted(found):
        if not _email_agrees(found[d]["name"], found[d]["email"]):
            raise RuntimeError(
                "%s: district %s pairs %r with %r — the county builds its "
                "mailboxes from its supervisors' own names, so a row whose "
                "e-mail names somebody else is the shift this reading exists to "
                "rule out" % (county, d, found[d]["name"], found[d]["email"]))
    shared = {}
    for d in sorted(found):
        shared.setdefault(digits(found[d]["phone"]), []).append(d)
    owner = pins.get("phone_owner", {})
    for num in sorted(owner):
        # the same rule the name pin follows: a pin that no longer describes
        # the page is deleted, never left standing as a fact nobody rechecks
        if len(shared.get(num, [])) < 2:
            raise RuntimeError(
                "%s: %s is no longer published for two districts — the pinned "
                "owner (district %s) has been overtaken by the county; delete it"
                % (county, num, owner[num]))
    for num, seats_sharing in sorted(shared.items()):
        if not num or len(seats_sharing) == 1:
            continue
        for d in seats_sharing:
            if owner.get(num) == d:
                continue
            print("  phone %-12s district %s: withheld — %s is published for "
                  "districts %s and cannot be all of theirs"
                  % (county, d, found[d]["phone"],
                     ", ".join(str(x) for x in seats_sharing)), file=sys.stderr)
            found[d]["phone"] = None
    _ward_witness(fips, county, wards, seats)
    out = {}
    for d in range(1, seats + 1):
        if d in vacant:
            out[str(d)] = {"name": None, "vacant": True, "role": None}
            continue
        row = {"name": found[d]["name"], "vacant": False, "role": found[d]["role"]}
        if found[d]["email"]:
            row["email"] = found[d]["email"]
        if found[d]["phone"]:
            row["phone"] = found[d]["phone"]
        out[str(d)] = row
    return out


def scrape_county(fips, name, seats, strategy, url):
    """All seats or nothing — see the module docstring."""
    if strategy == "fielded":
        return scrape_fielded_county(fips, name, seats, url)
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
             len(COUNTIES) + len(ARCGIS_COUNTIES) + len(DOCUMENT_ROSTERS), total,
             ", %d county/counties missed" % len(failures) if failures else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

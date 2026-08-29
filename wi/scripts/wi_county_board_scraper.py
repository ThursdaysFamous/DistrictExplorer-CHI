#!/usr/bin/env python3
"""
Scrape county board supervisors from the 31 Wisconsin counties that publish a
district-keyed member list. Stage 1 of the pair; build_wi_county_board_roster.py
turns the intermediate JSON into data/app/county-board-members.json.
Scrape county board supervisors from the 34 Wisconsin counties whose roster
this file can reach. Stage 1 of the pair; build_wi_county_board_roster.py turns
the intermediate JSON into data/app/county-board-members.json.

WHY ONLY THIRTY-FOUR OF SEVENTY-TWO
-----------------------------------
Wisconsin publishes county board DISTRICTS statewide (Wis. Stat. 5.15(4)(br)1,
see build_wi_supervisory_districts.py) and publishes the PEOPLE in them
nowhere: each county names its own supervisors, 72 different ways. Thirty pair
a district with a person in a form a parser can read, Dodge does it in a
paginated constituent DIRECTORY that needs its own fetch shape (see
CONSTITUENT_COUNTIES), and Milwaukee and Racine publish theirs on their own GIS
layers. The rest are not oversights and are recorded as such:

  * Kenosha and Oconto publish district MAPS — a page per district with a PDF
    and no name on it anywhere. Both were re-checked 2026-08-29 and both
    records held; Ozaukee was in this bullet until the same day, when the
    board's own page turned out to name all 26 (see COUNTIES).
    This file used to claim 23 counties; that count came from a sweep that
    tested district NUMBERS, and numbers are what a map index has.
  * Marinette publishes 29 of its 30 seats by number; the thirtieth is an
    unnumbered "VACANT SEAT" row in an alphabetical list. It SHIPS since
    2026-08-29, district 26 assigned by elimination under the arithmetic gate
    in ELIMINATION_VACANCY below — opt-in per county, never a general rule.
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
  * The rest could not be read: 7 answer 403 to a datacenter client and hold
    it against browser headers (Marathon, La Crosse, Outagamie, Fond du Lac,
    Lincoln, Monroe, Sheboygan) — Rock was one of them until 2026-08-29,
    see A REFUSED SITE IS NOT A REFUSED PAGE below — Taylor sits behind an sgcaptcha
    challenge answering 202 (an access control, not an obstacle to route
    around), Forest does not resolve, and the remainder publish their members
    as PDFs, images or prose with no district column.

    LAFAYETTE WAS THE NINTH OF THOSE 403s AND NOW RIDES DOCUMENT_ROSTERS.
    Its refusal was re-measured 2026-08-29 and is real (a Cloudflare managed
    challenge, bare host and www, browser headers), but the record had gone
    one step past the measurement: the county was filed under "could not be
    read" when what could not be read was its HOST. The page publishes all
    sixteen seats in the plainest shape on this list, which the Internet
    Archive's own 2025-02-14 capture of it shows and which `_same_line_lead`
    reads 16/16. THAT IS WHY ITS ENTRY CARRIES A `live` READING WHERE
    TAYLOR'S CANNOT: Taylor has no host to try, and Lafayette has a page that
    parses the moment its challenge lifts.
a district with a person on a PAGE a parser can read, Milwaukee and Racine
publish theirs as attributes on their own GIS layers, Kenosha publishes its in
a DOCUMENT this file fetches and witnesses every run
(WITNESSED_DOCUMENT_COUNTIES), and Taylor's is CARRIED from a document an
operator read once behind a captcha (DOCUMENT_ROSTERS). Those last two are not
the same thing and the difference is stated where they are defined. The other
38 are not oversights and are recorded as such:

  * Ozaukee publishes district MAPS — a page per district with a PDF and no
    name on it anywhere. It was checked three pages deep. This file used to
    claim 23 counties; that count came from a sweep that tested district
    NUMBERS, and numbers are what a map index has.
  * KENOSHA WAS IN THAT BUCKET UNTIL 2026-08-29 AND ITS RECORD NAMED THE WRONG
    PAGE. The description above is accurate about
    /142/County-Board-Supervisor-Districts — an index of 23 links to 23 PDF
    maps with nobody's name on it — and is not the county's roster page.
    /113/County-Board-of-Supervisors is, and it publishes all 23 seats as
    "District N" followed by the supervisor's name, resolving 23 of 23 under
    the plain `after` reading with no new code. TWO SLUGS ONE WORD APART, one
    of them a map index and one of them the answer: when a county's record
    says "checked the board page", check WHICH board page.
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
    a person is a source (see WITNESSED_DOCUMENT_COUNTIES); one that lists
    names alphabetically is not, whatever it is served as.

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

OZAUKEE WAS NEVER A MAP-ONLY COUNTY (2026-08-29)
-------------------------------------------------
Ozaukee was named in the map-index bullet above for four days — it is not
there now — as one of the counties that publish "district MAPS ... and no name
on it anywhere", checked "three pages deep". It
publishes all twenty-six supervisors in one district-keyed HTML TABLE at
ozaukeecounty.gov/701/County-Board — District Map / Name / Address / Phone /
Email, one row per seat — and it ships from that page under the ordinary
`column-after` reading, with no new code.

WHAT WENT WRONG IS THE SAME THING THAT WENT WRONG WITH DANE, ONE LEVEL DOWN.
Dane's lesson was recorded as "ask the BOARD's own HOST": its roster is on
board.danecounty.gov rather than the county domain. Ozaukee is on the county's
own host, so that rule reported nothing wrong — the miss is that the URL this
project already held for Ozaukee, in build_wi_county_board_directory.py, is
/2206/Supervisory-District-Maps. THAT PAGE IS EXACTLY WHAT THE OLD RECORD
DESCRIBES: a map index, a PDF per district, no person on it. The county's
BOARD page is a different page on the same host, and the sweep that wrote the
record never reached it. So the rule generalises past the host: ASK THE
BOARD'S OWN PAGE. A county filed under "publishes maps" is a county whose MAP
page was read, which is not evidence about its board page.

Whether the table was also there when the record was written could not be
established from here: web.archive.org holds a snapshot of /701/County-Board
from 2025-09-28, and this sandbox's egress policy blocks that host (the
availability API on archive.org answers; the snapshot itself does not). So
this entry does NOT claim the old check was careless — only that the page it
describes is the maps page, and that the board page reads cleanly today.

KENOSHA AND OCONTO WERE RE-CHECKED THE SAME DAY AND BOTH RECORDS HELD, which
is what bounds the correction to one county. Oconto's board page is a pure
index of 31 district PDFs with no person on it. Kenosha's own board pages link
"Who is my County Board Supervisor?", which sounds like the missing roster and
is a POINTER TO A LOOKUP TOOL ("Where Do I Vote and Who are My
Representatives?") carrying no roster of its own. Neither county yields a
single name-shaped line outside site navigation under any of the five
readings. They stay out on measurement, not on inheritance.

FOUR TRAPS ON OZAUKEE'S PAGE, THREE OF WHICH WOULD SHIP SILENTLY
----------------------------------------------------------------
  * A STRAY EMPTY <table> IS NESTED IN DISTRICT 9's PHONE CELL
    (`<table class="style4" id="table20"></table>262-377-7650`, CMS editor
    debris). A non-greedy `<table>.*?</table>` match therefore closes the
    outer table on the INNER one's tag and returns EIGHT rows of twenty-six —
    a clean-looking parse that drops two thirds of the board. `to_lines`
    strips tags rather than parsing the table, so this scraper never sees it;
    it is recorded because reaching for the row structure (to pick up the
    phone or e-mail columns) walks straight into it, and because eight
    plausible rows is precisely the partial output the all-seats-or-nothing
    rule exists to refuse.

  * THE ADDRESS COLUMN READS AS A NAME. "Belgium, WI" passes `is_name`, and
    `clean` flips it on the comma to "WI Belgium". Under `column-before` the
    page resolves 25 of 26 seats, reports NO vacancy, and fills the roster
    with mangled place names — a full, confident, entirely wrong answer, and a
    live demonstration of why the reading direction is PINNED per county
    rather than detected. `column-after` reaches the Name cell first and never
    sees the address.

  * THE E-MAIL COLUMN NAMES THE WRONG PEOPLE. Most rows link a CivicPlus
    contact FORM rather than an address, and the form slugs were not renamed
    when seats changed hands: District 3 (Marcia Nosko) links
    Email-Supervisor-Barbara-Jobs-223 and District 5 (Scott R. Fischer) links
    Email-Supervisor-Donald-Clark-225. A slug is not a name source.

  * SOME ROWS CARRY HIDDEN mailto: LINKS WITH EMPTY ANCHOR TEXT — invisible to
    a reader of the page, and a mixture of county addresses, private ones
    (gmail/aol/att.net), and at least one PREDECESSOR's: District 7's row
    holds Tony Matera's own tmatera@co.ozaukee.wi.us AND
    dbecker@x-celtooling.com, a private business address for someone not in
    office. No rule picks the right one — "prefer the county domain" works for
    District 7 and fails District 6 and 8, which carry only private
    addresses — so NO E-MAIL SHIPS FOR OZAUKEE. The county's own contact
    surface is the board page, which the card already links.

  Phone is not carried either, and for a plainer reason: five of the
  twenty-six rows print 262-284-9411, which is the county's MAIN SWITCHBOARD
  (it is the number in the site footer), so the column is not a per-supervisor
  fact. The card renders neither field today in any case.

WHAT WITNESSES THE OZAUKEE ROSTER
----------------------------------
Every one of the 25 named seats was confirmed against a SECOND county surface
on 2026-08-29: each row's Name cell links that supervisor's own profile page,
and all 25 state their district in their own text (District 1 Bichler ...
District 26 Foy) and repeat the member's surname — so a row shift of the kind
`column-before` produces would have been caught by 25 disagreements rather
than by eye. District 21, which the table marks Vacant, is the ONLY row with
no profile link, corroborating the vacancy independently of the word. Those
pages are a verification run by hand, not a weekly fetch: the shipped source
stays the one board page, and the builder's existing gate against the LTSB
geometry (26 districts, numbered 1..26) is what re-checks the shape each week.

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

IOWA COUNTY: THE PAGE ITS OWN HOME PAGE LINKS NO PATH TO (2026-08-29)
---------------------------------------------------------------------
Iowa was in the "publishes no district-keyed list on the pages their own sites
point to" bucket, and that sentence was exactly true and still described this
side of the wire. The county publishes all 21 districts at
/departments/countyboard/county-board-members with a name, a per-district county
e-mail alias and a phone on each — as rich as any page in this table — and
www.iowacountywi.gov's home page carries NOT ONE anchor whose href contains
"board", because its DEPARTMENTS menu is built by script. A harvest of a county
home page's own links therefore finds no route to it at all, and the page sits
two hops in behind a menu that only a browser assembles.

That is the Dane lesson one turn further on. Dane said ask the BOARD's host as
well as the county's; Iowa says a county's own site can HAVE the page and link
it from nowhere a link harvest can see. Neither county was withholding
anything.

READ THE SITEMAP. It is the route that would have found this one and costs a
single request: www.iowacountywi.gov/sitemap.xml lists 3,173 pages, and
`/county-board-members` — a flat alias of the same page, serving the same 21
supervisors — is one of them. A site whose menu is script-built still has to
tell search engines what it publishes. (Its robots.txt allows this path to a
general crawler: the `User-agent: *` block disallows only /calendar, /meetings,
/media, /portal and a few others, and asks a crawl-delay of 5 seconds, which a
weekly one-page fetch of this host meets by construction.)

WHAT IS NOT CARRIED, AND WHY. The page prints three things per supervisor this
table does not ship. The street addresses are supervisors' HOMES ("6067 Helena
Rd."), and a home address never ships here even when the source publishes it —
the same rule Taylor's document rides. The phone and the county e-mail alias
(supervisor14@iowacounty.org, on the county's older domain) are official
contact details and are simply not read: the county-board card renders a
supervisor's name and nothing else, so the two GIS counties' e-mails already
sit in the shipped file unread, and a new per-county contact reading with no
reader is risk for nothing. If that card ever grows a contact line, Iowa's
addresses are self-verifying — the number IN the alias must equal the district
it is filed under — and this paragraph is the note saying where to start.

Iowa marks no chair and no vacancy, which matters to the officer builder rather
than to this one: the Blue Book's Iowa chair, John M Meyers, sits at district
14, so its weekly reconciliation CONFIRMS the dated book row instead of
withholding it.
KENOSHA WAS THE TENTH, AND WHAT IT ADDS IS A ROUTE (2026-08-29)
----------------------------------------------------------------
Its own miss is recorded in the bucket list above — the wrong board page. What
it adds to this file is the route: the county's Clerk publishes MORE than the
board page does, in a DOCUMENT rather than on a page. The annual Directory of
Public Officials (a 107-page PDF) prints the same 23 districts with a PHONE and
an E-MAIL each, and marks the Chair and Vice-Chair on their own rows. No other
county here publishes contact for its board at all.

TWO KINDS OF DOCUMENT LIVE IN THIS FILE NOW AND THEY ARE OPPOSITES. Taylor's
roster is CARRIED (DOCUMENT_ROSTERS): read once by an operator in a browser
because a captcha fronts every automated client, never re-read by a run, and
the output SAYS SO on every record. Kenosha's is WITNESSED
(WITNESSED_DOCUMENT_COUNTIES): fetched fresh every run, cross-checked against
the county's own board page name-for-name, and no more stale than any page
county here. A record carrying `carried_from_document` is the first kind; the
absence of that flag is the second. Do not merge the two strategies because
both say "document" — the flag is a currency claim a reader sees.

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

A fifth joined on 2026-08-29 with Lafayette:

    same-line-lead
                the name FIRST and the district LAST, the office between them
                ("Larry Ludlum- Supervisor District #1") — see
                `_same_line_lead`. It is the only reading that recovers a ROLE
                from the seat's own row, because it is the only one that reads
                the words between the person and the district. It is pinned on
                a DOCUMENT_ROSTERS entry rather than in COUNTIES, because the
                host refuses this client; the run tries it anyway, every time.

The strict readings exist because a district whose own row yields no readable
name reaches past the next heading and takes ITS name: Rusk prints an INDEX of
nineteen bare "District #N" links above its roster, and Richland's rows end in
an e-mail address. Both filed one person under two districts, both were caught
by the duplicate-name guard below, and neither ships. They are a separate
strategy rather than a change to `_windowed` so the twenty counties already
shipping keep byte-identical behaviour.

A sixth joined on 2026-08-29, and it is the first that is not one shape at all:

    same-line-or-next
                BOTH of the first two, in one page (Iowa) — see
                `_same_line_or_next`

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

A SIXTH SHAPE, AND THE ONE THAT NEEDS NO DIRECTION AT ALL (2026-08-29)
----------------------------------------------------------------------
    row         a TABLE ROW pairing the two cells (Rock) — see `_rows`

Rock County publishes its board as a Granicus staff-directory TABLE, one
`<tr>` per supervisor holding `<td>Fleming, Patricia</td><td>District 01
Supervisor</td>`. Flattened to lines that reads as a `before` page — and it is
the sharpest example this file has of why the flattening is dangerous. The
`after` reading of the SAME page also resolves 29 of 29, names 29 DIFFERENT
people, every one of them their neighbour's supervisor, and files the site's
own footer — "Website design by Granicus" — as District 29. Both readings pass
every count guard; only the duplicate-name guard would have anything to say,
and it has nothing, because a shift by one duplicates nobody.

So Rock is not read by pinning a direction around the ambiguity. The county
wrote the pairing in a ROW, and `_rows` reads it there, where the ambiguity
does not arise: one district per row, one name per row, or the row is skipped
and the count guard fails loudly. THE ROW READING IS THE FIRST CHOICE FOR ANY
COUNTY WHOSE PAGE IS A TABLE; the line readings remain for the pages that are
lists and prose.

A REFUSED SITE IS NOT A REFUSED PAGE: ROCK AND THE ARCHIVE LADDER (2026-08-29)
------------------------------------------------------------------------------
co.rock.wi.us answers HTTP 403 from AkamaiGHost to EVERY request this project
can make: the board page, the front door, robots.txt and sitemap.xml alike,
under a Chrome user-agent, under a named bot user-agent and under curl's
default. A block that covers robots.txt is not a page refusing a reader and
not a header this client got wrong — it is the edge refusing this client's
network, and there is nothing about the request to fix. (The county's own GIS
is a separate host and publishes no supervisor names anyway: its supervisory
district service is an internal `.lan` URL, and its public service sits on
port 8443, which this project's egress does not reach.)

What the county publishes is nonetheless PUBLIC and ARCHIVED. The Internet
Archive holds the board page, so Rock is read from the newest capture rather
than not at all — the "engine ladder" the fleet already runs for blocked
counties, with the rung that answered recorded on the county's own entry
(`read_from`, which carries the capture's timestamp) instead of being passed
off as a live read.

THIS IS NOT TAYLOR'S CASE AND MUST NOT BECOME IT. Taylor rides
DOCUMENT_ROSTERS because a captcha admits only a human, so its roster cannot
be re-read by anything here and says so, dated, on every run. Rock's page is
re-fetched in full on every run — from the Archive rather than the county, but
fetched, parsed and count-guarded exactly like the other thirty. A capture is
a fetch; a document in this file is not.

Two things keep that honest.

  THE LADDER STARTS LIVE. `fetch_or_archive` asks the county first, every run,
  and only falls to the Archive on a refusal. The day Akamai stops refusing,
  Rock reads live with no code change, and the run log says which rung answered.

  A CAPTURE MUST POST-DATE THE BOARD IT NAMES. Wis. Stat. 59.10(3)(d) elects
  every supervisor in this class of county "for 2-year terms at the election to
  be held on the first Tuesday in April in even-numbered years", to "take office
  on the 3rd Tuesday in April of that year" — so a capture older than the most
  recent 3rd Tuesday in April of an even year shows a board that no longer
  sits. `board_seated_on` computes that date and the fetch REFUSES an older
  capture rather than shipping a stale roster under a current-looking card.
  Rock's board was seated 21 April 2026; the captures of 2026-06-04 and
  2026-08-14 both clear it, agree with each other on all 29 districts and on
  all three officers, and the second is what ships.

The chair the page names is a third witness on top of that: the Wisconsin Blue
Book (April 2025) already had Kevin Leavy as Rock's board chair, independently
of the county's own page, and the officer builder reconciles the two.

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

import datetime
import gzip
import html as html_lib
import io
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# For the one county whose roster is a document this file FETCHES (see
# WITNESSED_DOCUMENT_COUNTIES; DOCUMENT_ROSTERS needs nothing, its text is
# already here). Imported at module scope on purpose: scripts/validate_workflow_deps.py
# reads these imports and fails the merge if the weekly workflow's pip line
# does not install pypdf, which is the gate that keeps this dependency honest.
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
    # --- 2026-08-29: the county whose SITE refuses this client and whose PAGE
    # does not — read from the Internet Archive, see the docstring's ladder ---
    ("55105", "Rock", 29, "row",
     "https://www.co.rock.wi.us/government/county-board-of-supervisors"),
    # --- 2026-08-29: the county whose own home page links no path to it ---
    ("55049", "Iowa", 21, "same-line-or-next",
     "https://www.iowacountywi.gov/departments/countyboard/county-board-members"),
    # --- 2026-08-29: the county this file spent four days calling map-only ---
    # The BOARD page, not the /2206/Supervisory-District-Maps page the
    # directory holds. `column-after` is load-bearing: read the other way the
    # page yields a full 25-seat roster built out of the ADDRESS column, with
    # the vacancy silently gone. See the Ozaukee section of the docstring.
    ("55089", "Ozaukee", 26, "column-after",
     "https://ozaukeecounty.gov/701/County-Board"),]

# Counties whose own host refuses this client on every path and every header,
# whose page the Internet Archive nonetheless holds. The ladder still asks the
# county FIRST on every run (`fetch_or_archive`); this only says where to look
# when it refuses, and what the refusal measured as.
ARCHIVE_READ = {
    "55105": "co.rock.wi.us answers 403 from AkamaiGHost on every path, "
             "including robots.txt, under every user-agent tried",
}

# The officer block's reading direction, pinned per county, for the counties
# whose officers sit in a run of consecutive name/role pairs. Rock prints
# "Kevin Leavy / Chair / Barbara Tillman / Vice Chair / Ron Woodman / Second
# Vice Chair": every role line has a name on BOTH sides, which is the case
# `attach_officer_roles` deliberately refuses to guess at. The county's own
# table settles it — its Staff column precedes its Title column — so the side
# is PINNED here rather than detected, exactly as the district readings are.
OFFICER_NAME_SIDE = {"55105": "before"}

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


# --- the fifth shape: the office BETWEEN the name and the district -------------
# Lafayette writes each seat as one line with the person FIRST and the district
# LAST, the office sitting between them:
#
#     Larry Ludlum- Supervisor District #1
#     Jack Sauer- County Board Chairman District #3
#
# `_same_line` strips the district and tests what is left, and what is left ends
# in "Supervisor" — a word `BAD` rejects, and rightly: it is the word that makes
# a heading a heading everywhere else. So the county read as publishing nothing
# while publishing all sixteen seats in the plainest form on this list. The
# reading takes the text BEFORE the district and strips the office off its tail,
# which is also where the ROLE is: the chairman's own row says so, where every
# other county on this list needs `attach_officer_roles` to reach a block
# further up the page.
_OFFICE_ROLE = r"(?:(?:County\s+)?Board\s+)?%s" % _ROLE
LEAD_OFFICE = re.compile(r"^(?P<name>.+?)[\s,\-\u2013\u2014]+(?P<office>(?:Supervisor|%s))\s*$"
                         % _OFFICE_ROLE, re.I)


def office_role(office):
    """The office as a ROLE, or None when it is the plain seat.

    Every member of a county board is a supervisor, so "Supervisor" is the
    office and not a role — shipping it as one would put "Supervisor
    (Supervisor)" on the card. Anything else is trimmed to the words that
    distinguish it ("County Board Chairman" -> "Chairman"), which is the
    vocabulary the other counties' rows already use and the vocabulary
    build_wi_county_officer_roster.py's `marks_chair` reads.
    """
    office = " ".join(office.split())
    if office.lower() == "supervisor":
        return None
    return role_case(re.sub(r"(?i)^(?:county\s+)?(?:board\s+)?", "", office))


def _same_line_lead(lines):
    out, vacant = {}, set()
    for line in lines:
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if d in out or d in vacant:
            continue
        # DIST consumes the separator before "district", so the head is the
        # whole of the line the county wrote before naming the district. A page
        # of this shape states a vacancy on that same line, which is the
        # `vacant_districts` lesson Marinette taught, one reading over.
        head = line[:m.start()].strip(" \t\u2013\u2014-:\u2022,")
        if VACANT.search(head):
            vacant.add(d)
            continue
        om = LEAD_OFFICE.match(head)
        if not om or not _reads_as_name(om.group("name")):
            continue
        who, role = clean(om.group("name"))
        out[d] = (who, role or office_role(om.group("office")))
    return out, vacant


# Lafayette's chair and both vice-chairs are named again in an administration
# block above the seat list, as "Name, Role" — the reverse of the "Role - Name"
# shape `attach_officer_roles` reads, and unreachable by it. This is a separate
# pass rather than a widening of that function so the counties already shipping
# keep byte-identical behaviour, and it obeys the same two rules: the join is on
# a UNIQUE FULL NAME, and every join prints.
#
# The role must match to the END of its own line, which is what keeps the
# county's own rules text out of it: "Memorial Hospital Compensation Oversight
# Committee (Cty Bd Chair, First Vice Chair and 3 Cty Bd members...)" carries
# both the comma and the words and is not a roster row. It is also what drops
# "Carla M Jacobson, County Clerk" — the clerk is not a supervisor, and the
# county's own clerk record is a different file.
NAMED_OFFICER = re.compile(r"^(?P<name>[^,]{4,44}),\s*(?P<role>%s)\s*$"
                           % _OFFICE_ROLE, re.I)


def attach_named_officer_roles(lines, districts, county):
    by_name = {}
    for d, row in districts.items():
        if row.get("name"):
            by_name.setdefault(row["name"], []).append(d)
    for line in lines:
        m = NAMED_OFFICER.match(line)
        if not m or not is_name(m.group("name")):
            continue
        role = office_role(m.group("role"))
        if not role:
            continue
        who = clean(m.group("name"))[0]
        hits = by_name.get(who)
        if not hits:
            continue                    # named above the list but not on it
        if len(hits) > 1:
            print("  note %-12s %r holds %d districts \u2014 role %r not attached"
                  % (county, who, len(hits), role), file=sys.stderr)
            continue
        if districts[hits[0]].get("role"):
            continue                    # the seat's own row already said so
        districts[hits[0]]["role"] = role
        print("  role %-12s district %s: %s -> %s"
              % (county, hits[0], who, role), file=sys.stderr)
    return districts


# --- the sixth shape: a TABLE ROW ---------------------------------------------
# The five readings above all pair a district with a name by POSITION in a
# flattened line list, which is why four of them have to pin a direction. A
# page that writes the pairing into a table row does not need one — Rock's
# markup is literally
#
#     <tr><td>Fleming, Patricia</td><td>District 01 Supervisor</td>
#         <td>County Board</td><td>(608) 719-7943</td><td>Email</td></tr>
#
# so the district and its supervisor are in the same row, in whichever order
# the county likes. Read there, a shift by one cannot happen; read as lines,
# Rock's `after` reading resolves all 29 seats, names everybody's neighbour
# and files the page footer as District 29 (see the docstring).
#
# ONE DISTRICT AND ONE NAME PER ROW, OR THE ROW IS SKIPPED. A row that carries
# two of either is ambiguous, and a skipped row fails the caller's count guard
# loudly — which is the whole point of not guessing.
_ROW = re.compile(r"(?is)<tr[^>]*>(.*?)</tr>")


def _rows(page_html, seats):
    out, vacant = {}, set()
    for row_html in _ROW.findall(page_html):
        cells = to_lines(row_html)
        dists = {int(m.group(1)) for m in (DIST.search(c) for c in cells) if m}
        if len(dists) != 1:
            continue
        d = dists.pop()
        if not (1 <= d <= seats) or d in out or d in vacant:
            continue
        if any(VACANT.search(c) for c in cells):
            vacant.add(d)
            continue
        named = [c for c in cells if not DIST.search(c) and _reads_as_name(c)]
        if len(named) == 1:
            out[d] = clean(named[0])
    return out, vacant


# --- the sixth shape: same line OR the next one, in one page ------------------
# Iowa County writes both. Fourteen of its districts print "District 1 - Chuck
# Weigel"; the other seven print "District 3 -" and put the name on the line
# below, because the county's editor bolded some names and not others and the
# markup broke where it did. `same-line` resolves 14 of 21 and `after` resolves
# 0 of 21 (every district's own block is address, phone and e-mail before the
# next name appears), so neither pinned reading can read a page that mixes them.
#
# THE FALL-THROUGH IS ONE LINE AND ONLY FROM AN OTHERWISE EMPTY DISTRICT LINE.
# That is what keeps it as safe as the pinned readings it sits beside: a
# district line carrying ANY other text is taken at face value and never looked
# past, so "District 1 Map" — the per-district map link that follows every
# block — cannot reach forward into "District 2 - Ingmar Nelson" and file the
# wrong person. A district whose own line is bare and whose next line is not a
# name simply does not resolve, and the all-seats-or-nothing guard fails the
# county loudly.
def _same_line_or_next(lines):
    out, vacant = {}, set()
    for i, line in enumerate(lines):
        m = DIST.search(line)
        if not m:
            continue
        d = int(m.group(1))
        if d in out or d in vacant:
            continue                    # the heading wins; a later mention cannot move it
        rest = re.sub(r"^[\s\-–—:•]+", "", DIST.sub(" ", line, count=1)).strip()
        paren = re.fullmatch(r"\((.+)\)", rest)
        if paren:
            rest = paren.group(1).strip()
        if VACANT.search(rest):
            vacant.add(d)
            continue
        if _reads_as_name(rest):
            out[d] = clean(rest)
            continue
        if rest:
            continue                    # the line says something else — never look past it
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if DIST.search(nxt):
            continue                    # the next district's line: stop, never borrow
        if VACANT.search(nxt):
            vacant.add(d)
        elif _reads_as_name(nxt):
            out[d] = clean(nxt)
    return out, vacant


READINGS = {
    "same-line": _same_line,
    "before": lambda ls: _windowed(ls, WINDOW_BEFORE),
    "after": lambda ls: _windowed(ls, WINDOW_AFTER),
}
# The readings that STOP at the next district line, and therefore report their
# own vacancies: the forward-only `vacant_districts` cannot see a vacancy the
# page prints on the side it is not scanning.
STRICT_READINGS = {
    "before-strict": lambda ls: _windowed_strict(ls, WINDOW_BEFORE),
    "after-strict": lambda ls: _windowed_strict(ls, WINDOW_AFTER),
    "same-line-lead": _same_line_lead,
    "same-line-or-next": _same_line_or_next,
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


# --- the archive ladder ------------------------------------------------------
# For the counties in ARCHIVE_READ only: their own host refuses this client on
# every path and header, and the Internet Archive holds the page they refuse to
# hand over. See the docstring for why that is a network refusal rather than
# something to fix in the request, for the two rules below, and for why this is
# a FETCH and never the document route DOCUMENT_ROSTERS carries.
CDX = ("https://web.archive.org/cdx/search/cdx?url=%s&output=json"
       "&fl=timestamp,statuscode&filter=statuscode:200&limit=-10")
SNAPSHOT = "https://web.archive.org/web/%sid_/%s"     # id_ = the original bytes
# THE ARCHIVE IS ASKED AS THIS PROJECT, NOT AS A BROWSER, and that is load
# bearing rather than manners: web.archive.org answers its own "Temporarily
# Offline" page with HTTP 503 to the shared Chrome user-agent `UA` carries,
# and 200 to a client that says who it is (measured 2026-08-29 — the same
# capture, same second, 503 as Chrome and 200 as anything named). `UA` exists
# for county CMSs that refuse non-browser clients; it is the wrong header
# here, and sending it reads as an outage that is not one.
ARCHIVE_UA = {"User-Agent": "districtry-county-board-scraper/1.0 "
                            "(+https://districtry.com; civic boundary data)"}


def board_seated_on(today=None):
    """The date the sitting county board took office.

    Wis. Stat. 59.10(3)(d): supervisors are "elected for 2-year terms at the
    election to be held on the first Tuesday in April in even-numbered years"
    and "take office on the 3rd Tuesday in April of that year". So a page
    describes the board that sits NOW only if it is at least as new as that
    date — which is what makes this a usable guard on an archived capture
    rather than an arbitrary age limit.
    """
    today = today or datetime.date.today()
    year = today.year if today.year % 2 == 0 else today.year - 1
    while True:
        seated = datetime.date(year, 4, 15)
        seated += datetime.timedelta(days=(1 - seated.weekday()) % 7)   # 3rd Tue
        if seated <= today:
            return seated
        year -= 2               # April of this even year has not happened yet


assert board_seated_on(datetime.date(2026, 8, 29)) == datetime.date(2026, 4, 21)
assert board_seated_on(datetime.date(2026, 4, 20)) == datetime.date(2024, 4, 16)
assert board_seated_on(datetime.date(2025, 1, 1)) == datetime.date(2024, 4, 16)


def _archive_json(url, tries=5):
    """The Archive answers 503 while it is down; back off rather than give up."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=ARCHIVE_UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:      # noqa: BLE001 - reachability, retried below
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("the Internet Archive did not answer %s (%s)" % (url, last))


def fetch_archived(url):
    """(page html, capture timestamp) from the newest capture that post-dates
    the sitting board — never an older one."""
    rows = _archive_json(CDX % urllib.parse.quote(url, safe=""))
    stamps = sorted(r[0] for r in rows[1:]) if rows and rows[0][0] == "timestamp" \
        else sorted(r[0] for r in rows)
    if not stamps:
        raise RuntimeError("no archived capture of %s" % url)
    seated = board_seated_on().strftime("%Y%m%d")
    newest = stamps[-1]
    if newest[:8] < seated:
        raise RuntimeError(
            "the newest archived capture of %s is %s, older than the %s "
            "organizational meeting that seated this board (Wis. Stat. "
            "59.10(3)(d)) — it names a board that no longer sits"
            % (url, newest[:8], seated))
    req = urllib.request.Request(SNAPSHOT % (newest, url), headers=ARCHIVE_UA)
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                # `id_` replays the ORIGINAL bytes, original Content-Encoding
                # and all, whatever this client asked for — so a page the county
                # served gzipped comes back gzipped. Decoding that as text
                # yields 30 KB of mojibake in which every reading finds nothing
                # and the count guard blames the county for changing shape.
                body = r.read()
                if body[:2] == b"\x1f\x8b":
                    body = gzip.decompress(body)
                return body.decode("utf-8", "replace"), newest
        except Exception as e:      # noqa: BLE001 - retried; the Archive
            last = e                # answers 503 for minutes at a time
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("could not read the %s capture of %s (%s)" % (newest, url, last))


def fetch_or_archive(url, fips, county):
    """(page html, how it was read). LIVE FIRST, ALWAYS — a county that stops
    refusing this client starts reading live with no code change, and the run
    log says which rung answered either way."""
    try:
        return fetch(url), "live"
    except Exception as live_error:     # noqa: BLE001 - the refusal is the point
        if fips not in ARCHIVE_READ:
            raise
        page, stamp = fetch_archived(url)
        print("  note %-12s live read refused (%s); read the Internet Archive "
              "capture of %s-%s-%s instead"
              % (county, live_error, stamp[:4], stamp[4:6], stamp[6:8]),
              file=sys.stderr)
        return page, "archive:" + stamp
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
    # LAFAYETTE (2026-08-29), AND THE ONE ENTRY HERE THAT IS RE-TRIED LIVE.
    # lafayettecountywi.org and its www host both answer HTTP 403 carrying
    # Cloudflare's own "Just a moment..." interstitial (cf-mitigated:
    # challenge, server: cloudflare, a cf-ray) to a client sending full
    # browser headers. A managed challenge is an access control and is not
    # defeated here. But unlike Taylor — whose other three hosts do not
    # resolve at all — this county has a PAGE that parses: /bos lists all
    # sixteen seats as "Larry Ludlum- Supervisor District #1", which
    # `same-line-lead` reads 16/16 against the Internet Archive's own
    # 2025-02-14 capture of it. So `live` is pinned here and tried on every
    # run: the day the challenge lifts, the run says so and this entry can be
    # deleted in favour of a COUNTIES row.
    #
    # WITNESSES. The Archive's capture agrees name for name on districts 1-15
    # and disagrees on 16 (it has Rita R. Buchholz; the county now has David
    # Halloran) — a real turnover, and exactly why an eighteen-month-old
    # capture is a witness for the fifteen and never a source for the
    # sixteenth. The chair is the Blue Book's chair for this county, and the
    # clerk the page names (Carla M Jacobson) is the clerk wi-county-clerks
    # already carries for 55065.
    #
    # NO E-MAILS OR PHONES: the page publishes none per supervisor, so those
    # slots are empty rather than filled from anywhere else.
    {
        "fips": "55065", "name": "Lafayette", "seats": 16,
        "read_on": "2026-08-29",
        "source_url": "https://www.lafayettecountywi.org/bos",
        "how": "captured from the county's own Board of Supervisors page, which "
               "answers a Cloudflare managed challenge to every automated client",
        "live": {"strategy": "same-line-lead"},
        # District 3's own row says "County Board Chairman"; the two vice-chairs
        # come from the administration block above the list. Both are what
        # `same-line-lead` and `attach_named_officer_roles` recover when the
        # page is read live, so the document and the live read agree.
        "roles": {"3": "Chairman", "12": "2nd Vice Chair", "15": "1st Vice Chair"},
        "members": {
            "1": ("Larry Ludlum", None, None),
            "2": ("Mark Pinch", None, None),
            "3": ("Jack Sauer", None, None),
            "4": ("John E. Reichling", None, None),
            "5": ("Luke McGuire", None, None),
            "6": ("Jeff Berget", None, None),
            "7": ("Bob Boyle", None, None),
            "8": ("Jed Gant", None, None),
            "9": ("Joe Schutte", None, None),
            "10": ("Gary Benson", None, None),
            "11": ("Donna Flannery", None, None),
            "12": ("Carmen McDonald", None, None),
            "13": ("Lee A. Gill", None, None),
            "14": ("Emmett Reilly", None, None),
            "15": ("Scott Pedley", None, None),
            "16": ("David Halloran", None, None),
        },
    },
]


def document_county(spec):
    """A roster carried from a document, with its age stated on every run.

    Returns (districts, carried_from_document).

    THE LIVE PAGE IS TRIED FIRST WHERE THERE IS ONE TO TRY (`live`), and that
    is the difference between an entry that can leave this table and one that
    cannot. Taylor has no host that answers anything, so its rows are a
    document until somebody re-reads the page in a browser. Lafayette has a
    page that parses under a pinned reading and a host that refuses this
    client — twice now this project has recorded a block that described its
    own vantage rather than the world (city.milwaukee.gov answered GitHub's
    runners plain, and the Elections Commission simply sent the file), so the
    attempt is made on every run and the log says which way it went.
    """
    import datetime
    live = spec.get("live")
    if live:
        try:
            districts = scrape_county(spec["fips"], spec["name"], spec["seats"],
                                      live["strategy"], spec["source_url"])
            print("  ok   %-12s %d seats READ LIVE \u2014 the page answered this run, "
                  "so this DOCUMENT_ROSTERS entry can be retired and the county "
                  "moved to COUNTIES with the %r reading"
                  % (spec["name"], spec["seats"], live["strategy"]), file=sys.stderr)
            return districts, False
        except Exception as e:      # noqa: BLE001 - refusal is the expected case
            print("  live %-12s still refused (%s)" % (spec["name"], e),
                  file=sys.stderr)
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
    roles = spec.get("roles") or {}
    out = {}
    for d in range(1, spec["seats"] + 1):
        name, email, phone = members[str(d)]
        row = {"name": name, "vacant": False, "role": roles.get(str(d))}
        if email:
            row["email"] = email
        if phone:
            row["phone"] = phone
        out[str(d)] = row
    return out, True


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

# --- COUNTIES WHOSE ROSTER IS A DOCUMENT THIS FILE FETCHES AND WITNESSES ------
# NOT DOCUMENT_ROSTERS, which is the OPPOSITE arrangement: that table carries a
# roster an operator read once in a browser because a captcha fronts the host,
# marks every record `carried_from_document` and never re-reads it. These entries
# are FETCHED FRESH EVERY RUN and cross-checked against a second county surface,
# so they carry no such flag and no such caveat. Two routes, one word, opposite
# currency claims — keep them apart.
#
# Kenosha's Clerk publishes an annual Directory of Public Officials — a 107-page
# PDF whose County Board section prints each district beside its supervisor's
# NAME, PHONE and E-MAIL, and marks the Chair and Vice-Chair on their own rows.
# Only Taylor's carried directory (DOCUMENT_ROSTERS) is as rich; no county whose
# roster comes off a PAGE publishes contact for its board at all.
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
WITNESSED_DOCUMENT_COUNTIES = [
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
    """District -> {name, role, phone, email} out of the Clerk's directory.

    A row needs a PHONE to be recognised, which is how the directory writes
    every seat it fills, so a VACANT seat would not parse and its district
    would go missing — taking the whole county out through the count gate
    below rather than shipping 22 of 23. That is deliberate and it is the same
    all-or-nothing rule scrape_county holds, but it is NOT the vacancy handling
    the page counties have: this county has no vacancy today, and the day it
    has one the run fails naming the missing district, which is a person
    reading the directory rather than a silent short roster.
    """
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


def scrape_witnessed_document(spec):
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


def attach_officer_roles(lines, districts, county, name_side=None):
    """Give a member the role their county states in its officers block.

    `name_side` pins which neighbour of a bare role line carries its name, for
    the counties that print officers as a run of consecutive name/role pairs —
    where both neighbours read as names and the ambiguous case below would
    otherwise attach nothing. Pinned per county in OFFICER_NAME_SIDE, never
    detected, for the same reason the district readings are.
    """
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
        #   * the county pins a side (OFFICER_NAME_SIDE) -> that neighbour, and
        #     only that one; Rock's three officers are consecutive name/role
        #     pairs, so every role line has a name on both sides and the
        #     ambiguous case below would attach none of them;
        #   * exactly ONE neighbouring line reads as a name -> that one;
        #   * BOTH neighbours read as names -> ambiguous, attach nothing.
        before = lines[i - 1] if i > 0 else ""
        after = lines[i + 1] if i + 1 < len(lines) else ""
        if m.group(2):
            cands = [m.group(2)]
        elif name_side:
            pinned = before if name_side == "before" else after
            cands = [pinned] if is_name(pinned) else []
        else:
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
    page_html, read_from = fetch_or_archive(url, fips, name)
    lines = to_lines(page_html)
    if strategy == "row":
        found, vacant = _rows(page_html, seats)
    elif strategy in STRICT_READINGS:
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
    if strategy == "same-line-lead":
        # Lafayette names its officers "Name, Role" in a block above the seat
        # list; the "Role - Name" reader below cannot see that shape.
        return attach_named_officer_roles(lines, out, name), read_from
    return attach_officer_roles(lines, out, name, OFFICER_NAME_SIDE.get(fips)), read_from


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    scraped_at = os.environ.get("SCRAPED_AT") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    counties, failures = {}, []
    jobs = [(c["fips"], c["name"], c["seats"], "arcgis", c) for c in ARCGIS_COUNTIES]
    jobs += [(d["fips"], d["name"], d["seats"], "document", d) for d in DOCUMENT_ROSTERS]
    jobs += [(c["fips"], c["name"], c["seats"], "constituent", c) for c in CONSTITUENT_COUNTIES]
    jobs += [(c["fips"], c["name"], c["seats"], "witnessed-document", c)
             for c in WITNESSED_DOCUMENT_COUNTIES]
    jobs += [(fips, name, seats, strategy, url) for fips, name, seats, strategy, url in COUNTIES]
    for fips, name, seats, strategy, src in jobs:
        if only and fips != only:
            continue
        carried = False
        try:
            if strategy == "arcgis":
                districts = scrape_arcgis_county(src)
                source_url, read_from = src["source_url"], "live"
            elif strategy == "document":
                districts, carried = document_county(src)
                source_url = src["source_url"]
                # a document county whose live page answered this run was read
                # live, and the log has to say which it was
                read_from = "document" if carried else "live"
            elif strategy == "constituent":
                districts = scrape_constituent_county(src)
                source_url, read_from = src["source_url"], "live"
            elif strategy == "witnessed-document":
                districts = scrape_witnessed_document(src)
                source_url, read_from = src["source_url"], "live"
            else:
                districts, read_from = scrape_county(fips, name, seats, strategy, src)
                source_url = src
        except Exception as e:      # noqa: BLE001 - one county never fails the run
            failures.append("%s (%s): %s" % (name, fips, e))
            print("  MISS %-12s %s" % (name, e), file=sys.stderr)
            continue
        counties[fips] = {"county": name, "seats": seats, "source_url": source_url,
                          "scraped_at": scraped_at, "read_from": read_from,
                          "districts": districts}
        if carried:
            # the file must SAY the roster was not re-read this run; a reader
            # of the JSON should never have to know which table it came from.
            # Keyed off the RESULT rather than the table, so a county whose
            # live page answered this run ships as the live read it was.
            counties[fips]["carried_from_document"] = True
            counties[fips]["read_on"] = src["read_on"]
            counties[fips]["how"] = src["how"]
        vac = sum(1 for d in districts.values() if d["vacant"])
        print("  ok   %-12s %d seats%s%s"
              % (name, seats, " (%d vacant)" % vac if vac else "",
                 "" if read_from in ("live", "document") else " [%s]" % read_from),
              file=sys.stderr)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"counties": counties, "failures": failures}, f, indent=2, ensure_ascii=False)
    total = sum(c["seats"] for c in counties.values())
    print("wrote %s: %d/%d counties, %d seats%s"
          % (out_path, len(counties),
             len(COUNTIES) + len(ARCGIS_COUNTIES) + len(DOCUMENT_ROSTERS)
             + len(CONSTITUENT_COUNTIES)
             + len(WITNESSED_DOCUMENT_COUNTIES), total,
             ", %d county/counties missed" % len(failures) if failures else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main()

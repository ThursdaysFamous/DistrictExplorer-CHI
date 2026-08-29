#!/usr/bin/env python3
"""
Link gate for the URLs the app puts in front of a reader.

WHY THIS EXISTS. scripts/validate_sources.py watches the *data* sources — the
Socrata ids, the ArcGIS services, the shapefile provenance. It says nothing
about the other half of every result card: the `primaryLink` a reader actually
clicks, and the `sourceUrl` each roster carries. Those go dead in a way no
scraper notices, because the card renders the string whether or not anything is
at the other end.

The failure that prompted it: Macon County's card shipped `maconcountyil.gov`
for three days. Not a redirect, not a 404 — the hostname has no DNS record at
all. The county is at `maconcounty.illinois.gov`. Two counties that same week
turned out to live at `.illinois.gov` addresses rather than the obvious ones,
so the guess-the-domain failure mode is not rare here, and a county whose only
appearance in the app is a card link has nothing else that would catch it.

WHAT IT CHECKS. Every http(s) URL reachable from two places, extracted rather
than listed by hand — a hand-kept manifest of ~1,100 URLs across ~500 hosts
would be one more thing to update per county, and would drift the week it was
written:

  1. the authored HTML pages (index.html, sources.html) — `url: "…"` (card
     links) and `href="…"` (footer, credits, and the sources page's per-layer
     boundary links).
  2. data/app/*.json — every string value that starts with http, wherever it
     sits. That covers sourceUrl/profileUrl/mapUrl/rosterPdf/compositionPdf and
     whatever the next builder invents.

TWO KINDS OF LINK, split by who can fix a dead one:

  * AUTHORED — a URL this repo chose: everything in index.html, and every
    provenance field a builder writes from its own constant (sourceUrl, source,
    mapUrl, rosterPdf, …). A dead one is ours to replace, and it is why this
    script exists.
  * PUBLISHED — somebody else's own address carried through a roster: the `url`
    and `profileUrl` fields, which hold a village's website or a member's bio
    page exactly as the county clerk or ILGA published it. Four hundred small
    municipal sites will always have a few down, expired or misspelled at the
    source (one municipality's published website is literally `yahoo.com`), and
    the repair is upstream or a dropped field — never a guessed replacement.
    These are reported, and grouped, but they never FAIL the run: a monthly
    issue that is 90% other people's outages is an issue nobody reads.
    The split is by WHO CHOSE THE STRING, not by the key's name — see
    AUTHORED_URL_FILES for the one file whose `url` is a repo constant.

Severities (a PUBLISHED link's worst severity is WARN):
  * gone — no DNS, or 404/410/451                                       [FAIL]
    A publisher's decision, not a blip. This is the case the script exists for.
  * unreachable — 5xx, timeout, connection/TLS error (5xx retried once)  [WARN]
    One monthly run cannot tell a dead page from a bad afternoon.
  * blocked — 403 from a host NOT in EXPECTED_UNREACHABLE               [WARN]
    Very often a bot filter rather than a dead link: several county sites and
    every chicagopolice.org URL refuse this client and serve a browser fine.
    Check in a browser BEFORE editing a card, then record the host below.
    A PUBLISHED link that is merely refused is OK, not WARN — a CDN-fronted
    village site refusing a datacenter client says nothing about the link and
    there is nothing to do about it; ~50 of them would drown the report.
  * blocked, expected — 403 from a listed host                             [OK]
  * unreachable, expected — a listed host that cannot be reached at all     [OK]
    Not every permanent unreachability is a refusal: a host that serves an
    INCOMPLETE certificate chain fails verification for every plain client
    while loading fine in a browser. Listing it stops the report advising that
    a healthy link be treated as dead.
  * REACHABLE again — a listed host that now answers                     [WARN]
  * rate-limited — 429 twice, eight seconds apart                        [WARN]
    Said softly on purpose: this probe is a plausible cause of a 429, so the
    finding names itself as a suspect. Only a repeat across months means
    anything.
  * answers nothing — HTTP 200 whose body is empty, a parking page, or a
    default web-server placeholder                                       [FAIL]
    The one failure a status check cannot see, and the reason this state
    exists: on 2026-08-20 four municipality cards linked sites that answered
    200 perfectly and showed a reader nothing — a GoDaddy domain-for-sale
    lander (Morris), a completely empty body (Calumet Park), and the stock
    "IIS Windows Server" placeholder (Chatham and Rochester). A sweep of all
    406 municipal URLs surfaced exactly those four, every one under 1,200
    bytes against real front pages of tens of thousands, so the false-positive
    cost of the size test is close to nothing. Size alone is the trigger; a
    named marker in the body upgrades the message from "suspiciously small" to
    naming what it actually is.
  * redirected to site root — a deep path that lands on `/`              [WARN]
    The common soft-404: a CMS forwards a retired deep link to the homepage
    with a 200. Only this subset is detectable; a dead link that lands on a
    styled "not found" page with a 200 still reads as OK here, and this script
    does not claim otherwise.

The EXPECTED_UNREACHABLE inversion is borrowed from validate_sources.py's
`blocked` flag, and for the same measured reason: before that flag existed the
monthly issue reopened every month with the same no-op WARNs. A listed host
cannot calcify — it warns if it starts answering (drop the entry) and it warns
if the app stops citing it (delete the entry).

RUNNING IT SOMEWHERE SANDBOXED. An egress proxy can manufacture a 403 that has
nothing to do with the site — in the Claude Code sandbox github.com answers 403
with the proxy's own JSON body, because repository access there is scoped per
session. Nothing like that is true in GitHub Actions, which is where this runs
on a schedule, so do NOT record such a host below on the strength of a local
run. Every entry in EXPECTED_UNREACHABLE was confirmed to be the SITE talking:
a Cloudflare "Just a moment…" challenge or an Akamai "Access Denied" page,
served with that CDN's own headers.

This script never edits anything. Like validate_sources.py it reports, and
.github/workflows/validate-sources.yml folds its report into the same monthly
tracking issue.

Usage:
    python3 scripts/validate_card_links.py
    python3 scripts/validate_card_links.py --report r.md --status-file s.txt
    python3 scripts/validate_card_links.py --offline   # extract only, no network
"""

import argparse
import collections
import json
import glob
import os
import re
import socket
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from scraper_common import UA_CHROME_WIN_126  # noqa: E402  (shared machinery — do not fork)

try:
    import requests
except ImportError:  # pragma: no cover - requests is pinned in requirements.txt
    requests = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, "il", "index.html")
# EVERY AUTHORED HTML PAGE THIS REPO SERVES, DISCOVERED RATHER THAN LISTED.
#
# WHAT belongs here was never in doubt. sources.html carries the credit row
# that used to live in index.html's footer plus one boundary link per layer, so
# scanning index.html alone silently dropped ~50 authored URLs off this gate the
# day that page shipped; the repo-root index.html is the FLEET LANDING PAGE as
# of R4 and the most prominent authored surface on the site. Every link on both
# is a link a reader clicks, and a dead one is this repo's to fix — which is
# what AUTHORED, rather than PUBLISHED, means here.
#
# KEEPING THE LIST BY HAND WAS THE PROBLEM. Both this list and APP_DATA_DIRS
# below were last extended by hand on 2026-08-26, for Wisconsin. Iowa shipped as
# the fifth instance the NEXT DAY and was added to neither, so every URL in
# ia/index.html, ia/faq.html and ia/sources.html — and Iowa's whole data/app,
# 277 more — sat outside this gate, where a dead link would have stayed green
# forever. APP_DATA_DIRS is the sharper half of that: its own comment says the
# premise is that "a new county is covered the day it ships with nothing to
# update", and it named four instances out of five. That is the gate's premise
# failing on the gate, so both surfaces are now DISCOVERED:
#
#   * the repo root's own pages — the landing page, the coverage map the
#     landing page embeds in an iframe (its legend rows are links a reader
#     clicks on the front door), the one-for-the-fleet /privacy.html,
#     sponsorship.html, and the redirect shells that catch pre-R5 paths. A
#     shell's canonical names the page it forwards readers to, so probing it
#     answers whether that page is still there. coverage-map.html is the
#     argument in miniature: it shipped on 2026-08-28 and had to be added to
#     the literal by hand in the same commit, which is the step Iowa did not
#     get.
#   * every .html an instance directory owns — index, faq, sources, history and
#     the per-concept SEO pages alike, which is one fewer list to forget.
#
# An INSTANCE is a top-level directory that serves an app: its own index.html
# and its own data/app/. Discovery rather than the generator's INSTANCES table
# is deliberate — this gate's monthly workflow installs requests and shapely and
# nothing else, and `from generate_metro_files import INSTANCES` EXITS 1 at
# import when jsonschema is absent (not an ImportError, so it cannot be caught
# as one), which would take the whole run down. The rule also cannot name an
# instance that is not one: districtry/ has an index.html and no data/app.
def instance_dirs():
    """Every instance folder in this repo, in directory order."""
    out = []
    for entry in sorted(os.listdir(REPO_ROOT)):
        full = os.path.join(REPO_ROOT, entry)
        if entry.startswith(".") or not os.path.isdir(full):
            continue
        if (os.path.isfile(os.path.join(full, "index.html"))
                and os.path.isdir(os.path.join(full, "data", "app"))):
            out.append(entry)
    return out


def authored_pages(instances):
    """Repo-relative paths of the root's pages, then each instance's own.

    A page that vanishes is simply not found — the same posture the hand-kept
    list had ("absent is skipped, not fatal"), except that now an ADDED page is
    not missed either.
    """
    pages = [os.path.basename(p)
             for p in sorted(glob.glob(os.path.join(REPO_ROOT, "*.html")))]
    for inst in instances:
        pages += ["%s/%s" % (inst, os.path.basename(p))
                  for p in sorted(glob.glob(os.path.join(REPO_ROOT, inst, "*.html")))]
    return pages


INSTANCE_DIRS = instance_dirs()
AUTHORED_PAGES = authored_pages(INSTANCE_DIRS)
# One data/app per instance. This used to be il/data/app alone, which meant the
# gate watched Illinois's roster URLs and nobody else's — a sibling could ship a
# card link to a dead host and every check here stayed green. Listing the four
# instances that existed then fixed that case and not the class; discovery is
# what stops the next one.
APP_DATA_DIRS = [os.path.join(REPO_ROOT, inst, "data", "app")
                 for inst in INSTANCE_DIRS]

FAIL, WARN, OK = "FAIL", "WARN", "OK"

HTTP_TIMEOUT = 25
MAX_HOST_WORKERS = 8
# Per severity group, in the markdown report only. A GitHub issue body caps at
# 64 KB and this report is folded into one alongside validate_sources.py's.
MAX_ROWS_PER_GROUP = 60
# A browser UA. Not evasion — the identifying UA that validate_sources.py uses
# is refused by several county CDNs outright, and a probe that reports every
# such host dead would be worse than no probe. Hosts that refuse this too are
# recorded below rather than worked around further.
HEADERS = {
    "User-Agent": UA_CHROME_WIN_126,
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
}

GONE_STATUSES = {404, 410, 451}
# 403/401 is a refusal — a standing posture. 429 is deliberately NOT here: it
# means "too many requests", and this probe is a plausible cause of it. Recording
# a 429 host as permanently blocked was wrong the one time it was tried —
# wcgl.org answered 200 on the very next run — so 429 gets a backoff and a retry
# instead, and says plainly that the probe may have provoked it.
BLOCK_STATUSES = {401, 403}
RATE_LIMIT_STATUS = 429

# A 200 that shows a reader nothing. Only HTML-ish answers are measured — a
# small PDF or image is a document, not a hollow page — and only the first
# few KB are read, so this costs one streamed request per OK link.
HOLLOW_MAX_BYTES = 1200
HOLLOW_PEEK_BYTES = 4096
# Markers that say WHAT the hollow page is. Absence of a marker does not make a
# tiny page fine; presence just lets the report name it instead of guessing.
HOLLOW_MARKERS = (
    ("iis windows server", "the stock IIS placeholder page"),
    ("welcome to nginx", "the stock nginx placeholder page"),
    ("apache2 ubuntu default page", "the stock Apache placeholder page"),
    ("forsale.godaddy", "a GoDaddy domain-for-sale lander"),
    ("domain is for sale", "a domain-for-sale lander"),
    ("buy this domain", "a domain-for-sale lander"),
    ("future home of", "an unconfigured hosting placeholder"),
    # Checked LAST of the markers, because a parking service usually answers
    # the first hop with nothing but a script that sends the browser onward —
    # requests does not follow that, so the body this sees is the redirect
    # itself. Morris's domain is exactly this shape.
    ("window.location", "a script-only redirect, not a page"),
)
RATE_LIMIT_PAUSE = 8

# ==== TEMPLATE:BEGIN card-links-host-tables ====
# ---------------------------------------------------------------------------
# Hosts measured to refuse this client while serving a browser normally. The
# check INVERTS for these: refusal is OK, answering is the WARN. Keyed by host
# (a leading `www.` is ignored on both sides), not by URL, because one bot
# filter covers every path on the host — chicagopolice.org alone accounts for
# 22 card links and mchenrycountyil.gov for another 22.
#
# Add an entry ONLY after confirming that the page is really there and that the
# refusal is the SITE's, not the network's: look at who answered. Each of these
# was checked on 2026-08-07 and came back with the blocking CDN's own headers
# and error page. A dead link parked here is a dead link nobody looks at again.
#
# Four of the six are the same blocks validate_sources.py records against its
# own `blocked` entries, measured independently there — they agree.
# ---------------------------------------------------------------------------
EXPECTED_UNREACHABLE = {
    "chicagopolice.org":
        "Cloudflare managed challenge (\"Just a moment…\", cf-ray present) — the same "
        "posture the CPD roster scraper needs Playwright for",
    "mchenrycountyil.gov":
        "Akamai \"Access Denied\" — the client-fingerprint block that also makes the "
        "county's board roster hand-verified (issue #235)",
    "kendallcountyil.gov":
        "Akamai \"Access Denied\" — same posture; the county blocks the Internet "
        "Archive's crawler too, hence a hand-verified roster (issue #234)",
    "lakecountyil.gov":
        "Cloudflare managed challenge — the county edge refuses datacenter clients; "
        "the board-roles scraper carries it via the Internet Archive",
    "adamscountyil.gov":
        "Akamai \"Access Denied\" — same posture as McHenry and Kendall",
    # THE ONE HERE WHOSE PAGE THIS REPO STILL READS EVERY WEEK. Fond du Lac's
    # County Board Supervisors directory is Akamai-denied to this client on
    # every path and both schemes, and its twenty-five supervisors ship anyway
    # — read through the Internet Archive's copy of that same public page
    # (wi/scripts/wi_county_board_scraper.py's ARCHIVE_COUNTIES). So the WI
    # county-board card links a URL that will answer this checker 403 forever
    # while the data behind it is refreshed weekly. Listing it stops the
    # monthly report advising that a live link be treated as dead; the
    # inversion is worth as much as usual here, because the day this host
    # answers again is the day that scraper's direct rung starts serving and
    # the archive hop can go.
    "fdlco.wi.gov":
        "Akamai \"Access Denied\" — the client-fingerprint block that makes the "
        "county's board roster ride the Internet Archive instead",
    "chicagoelections.gov":
        "Cloudflare managed challenge — the Board of Election Commissioners' site "
        "refuses non-browser clients; the early-voting file is hand-transcribed",
    "co.rock.wi.us":
        "Akamai \"Access Denied\" — measured 2026-08-29 on the board page, the front "
        "door, robots.txt and sitemap.xml alike, under a Chrome UA, a named-bot UA and "
        "curl's default (server: AkamaiGHost, x-reference-error, errors.edgesuite.net "
        "in the body, so it is the SITE talking). A browser loads it fine, which is why "
        "the card still links it; the county's 29 supervisors are read from the "
        "Internet Archive instead (wi/scripts/wi_county_board_scraper.py's ladder)",
    # THE ONE ENTRY HERE THAT IS NOT A REFUSAL. Read the reason before treating
    # it as one: this county is not blocking anybody. Its server sends only its
    # leaf certificate and never the GoDaddy intermediate that signed it, so
    # requests/curl/urllib all stop at "unable to get local issuer certificate"
    # while a browser fetches the missing issuer from the leaf's AIA extension
    # and loads the page normally. Verified 2026-08-17 by counting the
    # certificates the host sends (one, against three from control hosts) and
    # by completing the fetch with the AIA-supplied intermediate — HTTP 200,
    # 43 KB. Listed so the monthly report does not advise treating a healthy
    # link as dead; it becomes a WARN the day the county fixes its chain, which
    # is when scripts/coles_county_board_scraper.py's AIA machinery could go.
    "colesco.illinois.gov":
        "incomplete TLS chain (leaf only, no intermediate) — NOT a block: the site "
        "answers HTTP 200 to a client that supplies the missing issuer, which the "
        "roster scraper does by AIA with a pinned hash",
    # THE SECOND OF THE SAME, and the reason Coles' entry above is worth its
    # length: this is a PATTERN, not one county's misconfiguration. Gallatin was
    # recorded on 2026-08-20 as "DARK to this client on every route tried" and
    # was not dark at all — gallatinco.illinois.gov answers HTTP 200 with 247 KB
    # and serves its leaf without the Sectigo intermediate that signs it.
    # Measured 2026-08-21 by reading the leaf's own AIA caIssuers URI and
    # completing the fetch with that certificate. The county shipped the same
    # day; scripts/il_county_commissioners_scraper.py does the chase for its
    # roster, pinned by hash, with verification never disabled.
    "gallatinco.illinois.gov":
        "incomplete TLS chain (leaf only, no intermediate) — NOT a block: the site "
        "answers HTTP 200 to a client that supplies the missing issuer, which the "
        "county-commissioners scraper does by AIA with a pinned hash",
    # THE THIRD OF THE SAME, and the most expensive one yet: Vermilion's gap
    # record called the county unreachable for three weeks on the strength of
    # this error, while the county published a maintained 27-member board
    # roster and its GIS published the districts. vercounty.org sends its leaf
    # signed by GoGetSSL RSA DV CA without that intermediate, so every plain
    # client stops at "unable to get local issuer certificate" and no browser
    # notices. Measured 2026-08-23 by reading the leaf's own AIA caIssuers URI
    # (crt.usertrust.com/GoGetSSLRSADVCA.crt) and completing the fetch with that
    # certificate — HTTP 200, 93 KB. Not listed separately but worth recording
    # here: vercountyil.gov, the domain in the state's clerk directory, is the
    # same site — it redirects to this host once the chain is completed, which
    # is why it was once wrongly recorded as "parked". The app cites only
    # vercounty.org, and this table warns about hosts the app has stopped
    # citing, so vercountyil.gov gets no entry of its own.
    "vercounty.org":
        "incomplete TLS chain (leaf only, no intermediate) — NOT a block: the site "
        "answers HTTP 200 to a client that supplies the missing issuer, which the "
        "board roster scraper does by AIA with a pinned hash",
    # THE FIRST WISCONSIN ENTRY. The wi ward card links MyVote as the honest
    # polling-place answer it cannot carry as data (gap ward-polling-places).
    # Measured 2026-08-25: HTTP 403 with `Cf-Mitigated: challenge` on every
    # path — the site AND its API routes — to curl with full browser headers
    # and WebFetch alike; browsers pass. A challenge is an access control and
    # is not defeated; if this host ever answers again, the WARN is the news
    # that a statewide polling-place source may have opened.
    "myvote.wi.gov":
        "Cloudflare managed JS challenge (Cf-Mitigated: challenge) on every path "
        "including the API routes — the wi ward card links it for readers; "
        "browsers pass, automation is refused",
    "city.milwaukee.gov":
        "Cloudflare challenge (measured 2026-08-25 in the WI phase-2 research and "
        "unchanged) — the wi mpd-district card links MPD's own district pages for "
        "readers; browsers pass, automation is refused, and the captain names "
        "behind it are why that card names no one (gap mpd-district-leadership)",
    # THE ENTRY WHOSE "REACHABLE again" WARN HAS SOMETHING SPECIFIC TO DO. The
    # wi county-board card names Lafayette's sixteen supervisors from a DATED
    # CAPTURE of the page this host serves, because the host will not serve it
    # to an automated reader; every card there says so. Measured 2026-08-29 on
    # both the bare and www hosts with full browser headers: HTTP 403,
    # `cf-mitigated: challenge`, `server: cloudflare`, a cf-ray, and the
    # "Just a moment..." interstitial — the site talking, not this sandbox's
    # proxy. If this host starts answering, the WARN is not paperwork: the
    # weekly scraper already re-tries the live page on every run, and the day
    # it succeeds Lafayette moves from DOCUMENT_COUNTIES to COUNTIES and its
    # capture date leaves the card.
    "lafayettecountywi.org":
        "Cloudflare managed challenge (cf-mitigated: challenge, \"Just a moment...\") "
        "— the wi county-board card links the county's own board page for readers "
        "and carries its sixteen supervisors as a dated capture; browsers pass, "
        "automation is refused",
}

# Some hosts publish nothing at `/` by design (the tile CDNs cited in the map
# attribution), so landing on the root says nothing about the link.
NO_ROOT_DOCUMENT = {
    "basemaps.cartocdn.com", "a.basemaps.cartocdn.com",
    "b.basemaps.cartocdn.com", "c.basemaps.cartocdn.com",
}
# ==== TEMPLATE:END card-links-host-tables ====


def expected_block(host):
    """EXPECTED_UNREACHABLE lookup, insensitive to a leading `www.`."""
    bare = host[4:] if host.startswith("www.") else host
    return EXPECTED_UNREACHABLE.get(host) or EXPECTED_UNREACHABLE.get(bare)


# ---- extraction --------------------------------------------------------------
INDEX_URL_RE = re.compile(r'url: *"(https?://[^"]+)"')
INDEX_HREF_RE = re.compile(r'href="(https?://[^"]+)"')
# A MEASURED GAP IN THESE TWO PATTERNS, recorded rather than quietly closed. A
# card link can also arrive as `directoryUrl` — the chamber factory's fallback
# when a member has no page of their own (`memberUrl || opts.directoryUrl`) —
# and on 2026-08-28 ten such URLs across all five instances were matched by
# neither pattern, so a reader clicks them and nothing probes them. A third
# regex is two lines and was deliberately NOT added in the same change that
# widened the PAGE list: these patterns also match inside COMMENTS, and the
# chamber factory's own worked example reads
# `directoryUrl: "https://example.gov/senate/members"` — so the naive version
# reports a documentation placeholder as a dead card link. Whoever adds the
# pattern answers the comment-line question with it.

AUTHORED, PUBLISHED = "authored", "published"

# data/app keys whose value is a third party's OWN address, copied verbatim by a
# scraper: a village's website, a legislator's bio page. Everything else in
# data/app is a provenance field a builder writes from its own constant, which
# this repo chose and can fix. A new roster field holding somebody else's URL
# belongs in this set.
PUBLISHED_KEYS = {"url", "profileUrl"}

# THE ONE FILE WHERE `url` MEANS THE OPPOSITE, and it took six broken links to
# find (2026-08-29). wi/data/app/county-board-directory.json holds one link per
# Wisconsin county to its own board page, and every one of them is a CONSTANT
# hand-picked in wi/scripts/build_wi_county_board_directory.py — that builder's
# docstring spends three paragraphs on why they could not be derived. So they
# are this repo's to fix, exactly like a `primaryLink` on a card, and the test
# above filed all 72 of them as somebody else's address on the strength of the
# key's NAME. Six were dead: an IIS placeholder (Fond du Lac), two GoDaddy
# parking landers (Kewaunee, Rusk), a "this site has permanently moved"
# sentence (Dodge), and two hosts that reset (Barron, Shawano) — every one a
# FAIL capped to WARN and lost in a monthly list, until a reader reported one.
#
# Iowa's ia-county-board-directory.json is NOT here and the near-identical name
# is the trap: ia_county_directory_scraper.py copies each county's website out
# of the Iowa State Association of Counties' member directory, so that `url` is
# a third party's own address and PUBLISHED is right for it. The question is
# never what a file is called — it is who chose the string.
AUTHORED_URL_FILES = {"county-board-directory.json"}


def from_pages(names):
    """URLs cited in the repo's authored HTML pages, with the line each sits on.

    Returns (citations, template_prefixes).

    A literal glued to an expression — `url: "…/schoolprofiles/" + schoolId` —
    is a PREFIX, not an address, and probing it answers the wrong question:
    cps.edu 404s that prefix bare while every built per-school URL resolves. A
    checker that reported it dead would be crying wolf about a working link, so
    those are separated out and named in the report rather than probed.
    """
    out = collections.defaultdict(list)
    prefixes = {}
    for name in names:
        path = os.path.join(REPO_ROOT, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                for rx, kind in ((INDEX_URL_RE, "card link"), (INDEX_HREF_RE, "href")):
                    for m in rx.finditer(line):
                        if re.match(r"\s*\+", line[m.end():]):
                            prefixes.setdefault(m.group(1), "%s:%d" % (name, n))
                            continue
                        out[m.group(1)].append("%s:%d (%s)" % (name, n, kind))
    return out, prefixes


def from_app_data(directory):
    """Every http(s) string value in data/app/*.json, with its JSON path.

    Deliberately key-agnostic about WHICH fields to read — a builder that ships
    a new URL field gets checked without this script being taught about it — and
    key-aware only about who owns the address (PUBLISHED_KEYS).

    Returns (citations, authored_urls).
    """
    out = collections.defaultdict(list)
    authored = set()
    rel_dir = os.path.relpath(directory, REPO_ROOT).replace(os.sep, "/")
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (ValueError, OSError) as e:
            print("validate_card_links: could not read %s (%s)" % (name, e),
                  file=sys.stderr)
            continue

        def walk(node, where, key):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, where + "/" + str(k), str(k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, where + "/" + str(i), key)
            elif isinstance(node, str) and node.startswith(("http://", "https://")):
                out[node].append("%s/%s%s" % (rel_dir, name, where))
                if key not in PUBLISHED_KEYS or name in AUTHORED_URL_FILES:
                    authored.add(node)

        walk(payload, "", "")
    return out, authored


def from_funding_manifest():
    """Every http(s) URL in the root funding.json, all of them AUTHORED.

    This is not read through from_app_data, and the reason is PUBLISHED_KEYS.
    There, a `url` key means "a village's website exactly as its county clerk
    published it" — somebody else's address, capped at WARN because there is
    nothing this repo can do about it. In a FLOSS/fund manifest `url` means
    the opposite: an address this repo wrote about itself. Running the manifest
    through that reader would file every one of its URLs as somebody else's.

    Two of them carry weight beyond being links. The spec requires a wellKnown
    pointer for any URL whose hostname differs from the manifest's own — a file
    on THAT host naming the manifest it authorises — so a funding directory
    resolves them to decide whether this project may solicit funding on behalf
    of overberg.co and of the GitHub repository. If one 404s the manifest stops
    verifying, and nothing else in this repo would notice.

    Returns (citations, authored_urls).
    """
    out = collections.defaultdict(list)
    path = os.path.join(REPO_ROOT, "funding.json")
    if not os.path.exists(path):
        return out, set()
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (ValueError, OSError) as e:
        print("validate_card_links: could not read funding.json (%s)" % e,
              file=sys.stderr)
        return out, set()

    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, where + "/" + str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, where + "/" + str(i))
        elif isinstance(node, str) and node.startswith(("http://", "https://")):
            out[node].append("funding.json%s" % where)

    walk(payload, "")
    return out, set(out)


def collect():
    """All cited URLs, plus each one's origin.

    A URL cited BOTH ways counts as authored: if ANY citation is one this repo
    chose, this repo can fix it, so it should not hide in the published group.
    """
    cites = collections.defaultdict(list)
    index_urls, prefixes = from_pages(AUTHORED_PAGES)
    authored = set(index_urls)
    sources = [index_urls]
    # EVERY instance's data/app, not just Illinois's. The gate's whole premise
    # is that a new county is covered the day it ships with nothing to update —
    # which held only for the instance whose directory was hardcoded here.
    # Wisconsin's county-board-directory alone carries 72 county URLs that
    # render on cards, and they were invisible to this script until this list
    # replaced the single path.
    for directory in APP_DATA_DIRS:
        app_urls, app_authored = from_app_data(directory)
        authored |= app_authored
        sources.append(app_urls)
    funding_urls, funding_authored = from_funding_manifest()
    authored |= funding_authored
    sources.append(funding_urls)
    for source in sources:
        for url, where in source.items():
            cites[url].extend(where)
    origin = {u: (AUTHORED if u in authored else PUBLISHED) for u in cites}
    return cites, origin, prefixes


def host_of(url):
    return (urllib.parse.urlparse(url).netloc.split("@")[-1].split(":")[0] or "").lower()


# ---- probing -----------------------------------------------------------------
def resolves(host, attempts=3):
    """Does `host` resolve? Returns (bool, detail).

    Retried, and called ONCE PER HOST rather than once per URL, because a
    single flaky lookup was enough to turn a live site into a FAIL: a run that
    reported chicagopolice.org and dupagecounty.gov as having no DNS record had
    reached both minutes earlier. Under parallel load the resolver drops
    queries, and "no such host" is exactly the finding that must not be wrong.
    """
    last = ""
    for attempt in range(attempts):
        try:
            socket.getaddrinfo(host, None)
            return True, ""
        except socket.gaierror as e:
            last = e.strerror or str(e)
        except Exception:
            return True, ""  # not a name problem; let the HTTP probe speak
        if attempt + 1 < attempts:
            time.sleep(0.5 * (attempt + 1))
    return False, last


# A page that forwards a browser onward the instant it loads. Both spellings
# appear in the wild: `content="0; url=x"` and a bare `content="0;x"`.
META_REFRESH_RE = re.compile(
    r"""<meta[^>]+http-equiv\s*=\s*["']?refresh["']?[^>]*content\s*=\s*["']([^"']*)["']""",
    re.I)


def meta_refresh_target(text, url):
    """Absolute URL this HTML instantly forwards a browser to, or None."""
    m = META_REFRESH_RE.search(text)
    if not m:
        return None
    content = m.group(1)
    at = re.search(r"""url\s*=\s*["']?([^"'\s;]+)""", content, re.I)
    if not at:
        # The bare form: everything after the delay, if it looks like a target.
        _, _, rest = content.partition(";")
        rest = rest.strip().strip('"\'')
        at = re.match(r"(\S+)", rest) if rest else None
    return urllib.parse.urljoin(url, at.group(1).strip()) if at else None


def peek_body(url):
    """(size, first few KB of text) for an HTML-ish answer, else None.

    Reads at most HOLLOW_PEEK_BYTES so a megabyte PDF costs nothing, and
    measures only HTML-ish answers — a 400-byte SVG or a small PDF is a
    document doing its job. Content-Length is trusted when the server sends
    one; otherwise the peeked length is the measurement, which is exact for
    anything this small.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT,
                            allow_redirects=True, stream=True)
    except Exception:
        return None  # the probe's own retry ladder owns transport failures
    try:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if ctype and "html" not in ctype and "text/plain" not in ctype:
            return None
        head = resp.raw.read(HOLLOW_PEEK_BYTES, decode_content=True) or b""
    except Exception:
        return None
    finally:
        resp.close()
    declared = resp.headers.get("Content-Length")
    try:
        size = int(declared) if declared is not None else len(head)
    except ValueError:
        size = len(head)
    return size, head.decode("utf-8", "replace")


def hollow_body(url, followed=False):
    """Does this 200 actually carry a page? Returns a detail string, or None.

    A SMALL PAGE THAT IS A META REFRESH IS NOT HOLLOW — it is a redirect, and
    the reader lands wherever it points. `tigerweb.geo.census.gov/` is 411
    bytes of `<meta http-equiv="REFRESH" content="0; url=tigerwebmain/…">`,
    titled "TIGERweb Redirect", and every browser lands on the real TIGERweb
    page; reporting it as a link that "answers nothing" told a maintainer to
    replace a working citation of the Census's own service root — cited from
    five instances' pages. So one hop is followed and the DESTINATION is
    measured by the same rules, which keeps the parking-lander catches this
    test exists for: Morris and Henderson forward with `window.location`
    rather than a meta refresh (still named as a script-only redirect below),
    and a meta refresh INTO a lander is caught at the destination by its own
    marker. One hop only, and a destination that cannot be fetched reads as
    fine, the same failing-open posture peek_body already takes — this test
    creates FAILs, so it errs quiet.
    """
    peeked = peek_body(url)
    if peeked is None:
        return None
    size, raw = peeked
    if size > HOLLOW_MAX_BYTES:
        return None
    target = None if followed else meta_refresh_target(raw, url)
    if target:
        onward = hollow_body(target, followed=True)
        return None if onward is None else "%s, via a meta refresh to %s" % (onward, target)
    text = raw.lower()
    for marker, what in HOLLOW_MARKERS:
        if marker in text:
            return "HTTP 200, %d bytes — %s" % (size, what)
    if size == 0:
        return "HTTP 200 with a COMPLETELY EMPTY body"
    return ("HTTP 200, only %d bytes — too small to be a page, and it carries no "
            "marker naming what it is" % size)


def probe(url, resolved=None):
    """Fetch one URL. Returns a dict; never raises.

    state: ok | gone | blocked | unreachable | root-redirect
    """
    host = host_of(url)
    if resolved is None:
        resolved = resolves(host)
    ok_dns, why = resolved
    if not ok_dns:
        return {"state": "gone", "detail": "no DNS record for %s (%s)" % (host, why)}

    # HEAD first (cheap, and PDFs here run to megabytes), GET on anything that
    # is not a clean answer: 405-on-HEAD is common, and a few servers 404 a HEAD
    # for a page they serve. GET is authoritative when the two disagree.
    result = None
    for method in ("head", "get"):
        try:
            resp = requests.request(method, url, headers=HEADERS, timeout=HTTP_TIMEOUT,
                                    allow_redirects=True, stream=(method == "get"))
        except Exception as e:
            result = {"state": "unreachable", "detail": "%s: %s" % (type(e).__name__, e)}
            continue
        code, final = resp.status_code, resp.url
        if method == "get":
            resp.close()
        if code == 202:
            # Same reading as validate_sources.py: "Accepted" is never a
            # document — it is what several counties' bot-management fronts
            # serve, and treating it as success is how a block goes unnoticed.
            # THIS TEST MUST PRECEDE `code < 400`, and for three weeks it did
            # not: 202 is under 400, so the success branch matched first and
            # this one could never run. The block was not missed outright,
            # because the hollow-body test then caught the interstitial as a
            # 169-to-220-byte page — but it named it the WRONG thing, telling a
            # maintainer to "find the real address and update every citation"
            # for co.taylor.wi.us and dekalbcounty.org, whose pages are fine
            # and whose sgcaptcha front this repo already knows about.
            result = {"state": "blocked", "detail": "HTTP 202 — bot-management interstitial"}
        elif code < 400:
            result = {"state": "ok", "detail": "HTTP %d" % code, "final": final}
            break
        elif code in GONE_STATUSES:
            result = {"state": "gone", "detail": "HTTP %d" % code}
        elif code in BLOCK_STATUSES:
            result = {"state": "blocked", "detail": "HTTP %d" % code}
        elif code == RATE_LIMIT_STATUS:
            result = {"state": "rate-limited", "detail": "HTTP 429"}
        else:
            result = {"state": "unreachable", "detail": "HTTP %d" % code}

    if result and result["state"] == "rate-limited":
        # Back off properly before believing it. Per-host serialisation keeps
        # this rare, so the pause costs one host a few seconds at most.
        time.sleep(RATE_LIMIT_PAUSE)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT,
                                allow_redirects=True, stream=True)
            resp.close()
            if resp.status_code < 400:
                result = {"state": "ok", "detail": "HTTP %d (after a 429 and a backoff)"
                                                   % resp.status_code, "final": resp.url}
            else:
                result["detail"] = "HTTP %d (twice, %ds apart)" % (resp.status_code,
                                                                   RATE_LIMIT_PAUSE)
        except Exception:
            pass

    if result and result["state"] == "unreachable" and (result.get("detail") or "").startswith("HTTP 5"):
        # One retry, then believe it. A monthly probe should not report a
        # restart as a dead link.
        try:
            resp = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT,
                                allow_redirects=True, stream=True)
            resp.close()
            if resp.status_code < 400:
                result = {"state": "ok", "detail": "HTTP %d (after retry)" % resp.status_code,
                          "final": resp.url}
            else:
                result["detail"] = "HTTP %d (twice)" % resp.status_code
        except Exception:
            pass

    if result and result["state"] == "ok":
        requested = urllib.parse.urlparse(url).path.strip("/")
        landed = urllib.parse.urlparse(result.get("final") or url)
        if requested and not landed.path.strip("/") and host not in NO_ROOT_DOCUMENT:
            result = {"state": "root-redirect",
                      "detail": "%s → %s" % (result["detail"], result.get("final")),
                      "final": result.get("final")}

    # Last, because it is the only test that needs the BODY: a link can answer
    # 200 and still show a reader nothing at all (see the docstring).
    if result and result["state"] == "ok":
        hollow = hollow_body(url)
        if hollow:
            result = {"state": "hollow", "detail": hollow, "final": result.get("final")}
    return result or {"state": "unreachable", "detail": "no response"}


def probe_all(urls):
    """Probe every URL, serialised per host and parallel across hosts.

    Per-host serialisation is politeness with teeth: chicagopolice.org is cited
    22 times, and 22 simultaneous requests is exactly what earns a rate-limit.
    """
    by_host = collections.defaultdict(list)
    for u in urls:
        by_host[host_of(u)].append(u)
    results = {}

    def run_host(item):
        host, host_urls = item
        resolved = resolves(host)
        return [(u, probe(u, resolved)) for u in host_urls]

    with ThreadPoolExecutor(max_workers=MAX_HOST_WORKERS) as pool:
        for batch in pool.map(run_host, by_host.items()):
            for url, res in batch:
                results[url] = res
    return results


# ---- findings ----------------------------------------------------------------
def cite_summary(places, limit=3):
    shown = "; ".join(places[:limit])
    if len(places) > limit:
        shown += "; and %d more" % (len(places) - limit)
    return shown


def evaluate(cites, origin, results):
    """Turn probe results into (severity, url, message, origin) rows."""
    rows = []
    for url in sorted(cites):
        res = results[url]
        host, state, detail = host_of(url), res["state"], res["detail"]
        expected = expected_block(host)
        who = origin[url]
        where = cite_summary(sorted(set(cites[url])))

        def row(sev, msg):
            # A published link's ceiling is WARN: see the module docstring. The
            # FAIL list has to stay short enough that someone reads it.
            rows.append((WARN if (sev == FAIL and who == PUBLISHED) else sev, url, msg, who))

        if state == "ok":
            if expected:
                row(WARN,
                    "REACHABLE again (%s) — the recorded block on %s appears to have "
                    "LIFTED. Re-check the other URLs on this host, then drop it from "
                    "EXPECTED_UNREACHABLE so a future block warns again. Recorded "
                    "block: %s. Cited at %s" % (detail, host, expected, where))
            else:
                row(OK, detail)
        elif state == "blocked" and expected:
            row(OK, "blocked AS EXPECTED (%s) — %s" % (detail, expected))
        elif state == "blocked" and who == PUBLISHED:
            # Nothing to do and nothing learned: CDN-fronted village sites
            # refuse datacenter clients as a matter of course, and the address
            # is the publisher's anyway. Counted in the summary, not listed.
            row(OK, "refused this client (%s) — a publisher's own address; not "
                    "actionable here" % detail)
        elif state == "blocked":
            row(WARN,
                "refused this client (%s). Usually a bot filter, not a dead link — OPEN "
                "IT IN A BROWSER before editing the card. If the page is there, add %s "
                "to EXPECTED_UNREACHABLE in this script with what you saw; if it is "
                "not, fix the link. Confirm the refusal came from the SITE and not from "
                "an egress proxy first — check who answered. Cited at %s"
                % (detail, host, where))
        elif state == "gone":
            row(FAIL,
                "DEAD (%s) — %s. %s Cited at %s"
                % (detail,
                   "this renders on a card" if who == AUTHORED
                   else "published this way by its own source",
                   "Find the page's current address and update every citation."
                   if who == AUTHORED
                   else "Fixing it means the publisher correcting their directory, or "
                        "the field being dropped — do NOT guess a replacement.",
                   where))
        elif state == "hollow":
            row(FAIL,
                "ANSWERS NOTHING (%s). The link is not broken — it is worse than "
                "broken, because every status check passes while a reader who "
                "clicks it sees a blank page, a parking lander or a default server "
                "screen. %s Cited at %s"
                % (detail,
                   "Find the real address and update every citation."
                   if who == AUTHORED
                   else "Published this way by its own source, so the fix is the "
                        "publisher correcting their directory — do NOT guess a "
                        "replacement address.",
                   where))
        elif state == "rate-limited":
            row(WARN,
                "rate-limited (%s), still after a %ds backoff. THIS PROBE is a plausible "
                "cause — the link is very likely fine. Only act on it if it repeats "
                "across months. Cited at %s" % (detail, RATE_LIMIT_PAUSE, where))
        elif state == "root-redirect":
            row(WARN,
                "redirects to the site root (%s) — the usual sign a deep link was "
                "retired and the CMS forwards it to the homepage. Verify the page still "
                "exists at some address, then cite that one. Cited at %s" % (detail, where))
        elif expected:
            # Same inversion as the `blocked` case above, and it exists because
            # a host can be permanently unreachable to this client WITHOUT
            # refusing it: colesco.illinois.gov serves an incomplete
            # certificate chain (leaf only, no intermediate), so every plain
            # client fails verification while the site answers HTTP 200 to a
            # browser. That is not transient and never will be until the county
            # fixes its server, so the default message below — "if it persists
            # next month, treat it as dead" — is exactly the wrong advice for
            # a link that is perfectly good.
            row(OK, "unreachable AS EXPECTED (%s) — %s" % (detail, expected))
        else:
            row(WARN,
                "not reachable (%s) — may be transient; if it persists next month, treat "
                "it as dead. Cited at %s" % (detail, where))
    return rows


def check_expected_list_still_earned(cites, rows):
    """A host nobody cites any more should not sit in EXPECTED_UNREACHABLE.

    Same self-retiring property as the reachable-again WARN: the list is only
    honest if entries have to keep earning their place.
    """
    cited_hosts = {host_of(u) for u in cites}
    cited_hosts |= {h[4:] for h in cited_hosts if h.startswith("www.")}
    for host, reason in sorted(EXPECTED_UNREACHABLE.items()):
        if host not in cited_hosts:
            rows.append((WARN, host,
                         "listed in EXPECTED_UNREACHABLE but the app no longer cites any URL "
                         "on this host — delete the entry. Recorded block: %s" % reason,
                         AUTHORED))


# ---- reporting ---------------------------------------------------------------
def render(rows, cites, origin, prefixes):
    order = {FAIL: 0, WARN: 1, OK: 2}
    rows = sorted(rows, key=lambda r: (order[r[0]], r[1]))
    n = {sev: sum(1 for s, _, _, _ in rows if s == sev) for sev in (FAIL, WARN, OK)}
    hosts = len({host_of(u) for u in cites})
    n_pub = sum(1 for v in origin.values() if v == PUBLISHED)

    lines = ["# Card + roster link validation", "",
             "**%d FAIL · %d WARN · %d OK** — %d URLs across %d hosts, extracted from "
             "%d authored pages and %d instances' `data/app/*.json`. Of those, %d chosen "
             "by this repo (a dead one is ours to fix) and %d carried from their own "
             "publisher (capped at WARN — see the script's header)."
             % (n[FAIL], n[WARN], n[OK], len(cites), hosts,
                len(AUTHORED_PAGES), len(INSTANCE_DIRS),
                len(cites) - n_pub, n_pub), ""]
    # Both phrases are the ones evaluate() writes for a refusal it counts OK;
    # keep them in step if either message is reworded.
    quiet = sum(1 for s, _, msg, _ in rows
                if s == OK and ("refused this client" in msg or "blocked AS EXPECTED" in msg))
    if quiet:
        lines += ["%d were refused outright — a CDN bot filter on a link this repo does "
                  "not control, or a host recorded in `EXPECTED_UNREACHABLE` — and count "
                  "OK. The script's header says why those are not WARNs." % quiet, ""]
    if n[FAIL] or n[WARN]:
        lines += ["Every URL below renders somewhere a reader can click. Nothing is "
                  "auto-changed — a FAIL is a link that is gone and needs its replacement "
                  "found; a WARN needs a look in a browser first.", ""]
    for sev in (FAIL, WARN):
        group = [r for r in rows if r[0] == sev]
        if not group:
            continue
        lines.append("## %s (%d)" % (sev, len(group)))
        # Ours first within a severity: those are the rows someone can act on
        # here, and they should not be read past a run of village outages.
        for who, heading in ((AUTHORED, "Links this repo chose"),
                             (PUBLISHED, "Links carried from their publisher")):
            part = [r for r in group if r[3] == who]
            if not part:
                continue
            if any(r[3] != who for r in group):
                lines += ["", "### %s (%d)" % (heading, len(part))]
            for _, url, msg, _o in part[:MAX_ROWS_PER_GROUP]:
                lines.append("- `%s` — %s" % (url, msg))
            if len(part) > MAX_ROWS_PER_GROUP:
                # A total outage would otherwise produce a thousand rows and
                # blow past GitHub's issue-body limit, losing the whole report.
                # stdout (the job log) always carries every row.
                lines.append("- _…and %d more, omitted to keep this readable — "
                             "the job log has the full list._"
                             % (len(part) - MAX_ROWS_PER_GROUP))
        lines.append("")
    # OK is a COUNT, not a list. A per-host roll-call of ~500 healthy hosts was
    # 21 KB of the 27 KB report, grew with every county added, and told nobody
    # anything. The recorded blocks are named, because those are the entries
    # that have to keep earning their place.
    ok_hosts = collections.Counter(host_of(u) for s, u, _, _ in rows if s == OK)
    if ok_hosts:
        lines += ["## OK (%d)" % n[OK], "",
                  "%d URLs across %d hosts answered normally."
                  % (n[OK], len(ok_hosts)), ""]
        blocked_seen = sorted(h for h in ok_hosts if expected_block(h))
        if blocked_seen:
            # "Unreachable", not "refused": most of these hosts do refuse this
            # client, but not all of them — colesco.illinois.gov merely serves
            # an incomplete certificate chain — and this summary line is
            # exactly where a reader would pick up the wrong word for it.
            lines.append("Unreachable as recorded in `EXPECTED_UNREACHABLE` (still "
                         "earning their entries; each row above says whether it is a "
                         "refusal or something else): %s."
                         % ", ".join("%s (%d)" % (h, ok_hosts[h]) for h in blocked_seen))
            lines.append("")
    if prefixes:
        lines += ["## Not probed (%d)" % len(prefixes), "",
                  "Built at runtime by concatenation, so the literal is a prefix rather "
                  "than an address — probing it would report a working link dead. Check "
                  "these by hand if a card's link ever looks wrong.", ""]
        for prefix, where in sorted(prefixes.items()):
            lines.append("- `%s…` — %s" % (prefix, where))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Check every card link and roster sourceUrl the app renders.")
    ap.add_argument("--report", metavar="PATH", help="write the markdown report to PATH")
    ap.add_argument("--status-file", metavar="PATH", help="write ok|warn|fail to PATH (for CI)")
    ap.add_argument("--offline", action="store_true",
                    help="extract and report the URL surface without probing it")
    args = ap.parse_args()

    if not os.path.exists(INDEX_HTML):
        print("validate_card_links: FAIL — index.html not found at %s" % INDEX_HTML,
              file=sys.stderr)
        sys.exit(1)

    # Discovery's one failure mode is finding nothing and reporting a narrowed
    # surface as a clean run — which is the failure this gate exists to catch,
    # so it is fatal rather than quiet.
    if not INSTANCE_DIRS:
        print("validate_card_links: FAIL — no instance directory found under %s. "
              "An instance is a folder with its own index.html and data/app/; "
              "finding none means this ran from the wrong tree." % REPO_ROOT,
              file=sys.stderr)
        sys.exit(1)

    cites, origin, prefixes = collect()
    if not cites:
        print("validate_card_links: FAIL — extracted 0 URLs, which cannot be right. "
              "The extraction patterns have drifted from the authored pages.", file=sys.stderr)
        sys.exit(1)

    if args.offline:
        hosts = collections.Counter(host_of(u) for u in cites)
        n_auth = sum(1 for v in origin.values() if v == AUTHORED)
        print("validate_card_links: %d URLs (%d chosen here, %d carried from their "
              "publisher) across %d hosts (offline; nothing probed)"
              % (len(cites), n_auth, len(cites) - n_auth, len(hosts)))
        # The pages and roster directories are discovered, so print what that
        # found: a missing instance is visible here rather than only as a
        # surface that quietly got smaller.
        print("  %d instances (%s); %d authored pages: %s"
              % (len(INSTANCE_DIRS), ", ".join(INSTANCE_DIRS),
                 len(AUTHORED_PAGES), ", ".join(AUTHORED_PAGES)))
        for host, count in sorted(hosts.items()):
            print("  %4d  %s" % (count, host))
        return

    if requests is None:
        print("validate_card_links: requests not installed; run with --offline or "
              "`pip install -c scripts/requirements.txt requests`", file=sys.stderr)
        sys.exit(1)

    rows = evaluate(cites, origin, probe_all(list(cites)))
    check_expected_list_still_earned(cites, rows)

    report = render(rows, cites, origin, prefixes)
    sys.stdout.write(report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)

    status = ("fail" if any(s == FAIL for s, _, _, _ in rows)
              else "warn" if any(s == WARN for s, _, _, _ in rows) else "ok")
    if args.status_file:
        with open(args.status_file, "w", encoding="utf-8") as f:
            f.write(status)
    sys.exit(1 if status == "fail" else 0)


if __name__ == "__main__":
    main()

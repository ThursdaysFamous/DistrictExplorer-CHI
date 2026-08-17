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

  1. index.html — `url: "…"` (card links) and `href="…"` (footer/credits).
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

try:
    import requests
except ImportError:  # pragma: no cover - requests is pinned in requirements.txt
    requests = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

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
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
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
RATE_LIMIT_PAUSE = 8

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
    "chicagoelections.gov":
        "Cloudflare managed challenge — the Board of Election Commissioners' site "
        "refuses non-browser clients; the early-voting file is hand-transcribed",
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
}

# Some hosts publish nothing at `/` by design (the tile CDNs cited in the map
# attribution), so landing on the root says nothing about the link.
NO_ROOT_DOCUMENT = {
    "basemaps.cartocdn.com", "a.basemaps.cartocdn.com",
    "b.basemaps.cartocdn.com", "c.basemaps.cartocdn.com",
}


def expected_block(host):
    """EXPECTED_UNREACHABLE lookup, insensitive to a leading `www.`."""
    bare = host[4:] if host.startswith("www.") else host
    return EXPECTED_UNREACHABLE.get(host) or EXPECTED_UNREACHABLE.get(bare)


# ---- extraction --------------------------------------------------------------
INDEX_URL_RE = re.compile(r'url: *"(https?://[^"]+)"')
INDEX_HREF_RE = re.compile(r'href="(https?://[^"]+)"')

AUTHORED, PUBLISHED = "authored", "published"

# data/app keys whose value is a third party's OWN address, copied verbatim by a
# scraper: a village's website, a legislator's bio page. Everything else in
# data/app is a provenance field a builder writes from its own constant, which
# this repo chose and can fix. A new roster field holding somebody else's URL
# belongs in this set.
PUBLISHED_KEYS = {"url", "profileUrl"}


def from_index(path):
    """URLs cited in index.html, with the line each sits on.

    Returns (citations, template_prefixes).

    A literal glued to an expression — `url: "…/schoolprofiles/" + schoolId` —
    is a PREFIX, not an address, and probing it answers the wrong question:
    cps.edu 404s that prefix bare while every built per-school URL resolves. A
    checker that reported it dead would be crying wolf about a working link, so
    those are separated out and named in the report rather than probed.
    """
    out = collections.defaultdict(list)
    prefixes = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            for rx, kind in ((INDEX_URL_RE, "card link"), (INDEX_HREF_RE, "href")):
                for m in rx.finditer(line):
                    if re.match(r"\s*\+", line[m.end():]):
                        prefixes.setdefault(m.group(1), "index.html:%d" % n)
                        continue
                    out[m.group(1)].append("index.html:%d (%s)" % (n, kind))
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
                out[node].append("data/app/%s%s" % (name, where))
                if key not in PUBLISHED_KEYS:
                    authored.add(node)

        walk(payload, "", "")
    return out, authored


def collect():
    """All cited URLs, plus each one's origin.

    A URL cited BOTH ways counts as authored: if ANY citation is one this repo
    chose, this repo can fix it, so it should not hide in the published group.
    """
    cites = collections.defaultdict(list)
    index_urls, prefixes = from_index(INDEX_HTML)
    app_urls, authored = from_app_data(APP_DATA_DIR)
    authored |= set(index_urls)
    for source in (index_urls, app_urls):
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
        if code < 400:
            result = {"state": "ok", "detail": "HTTP %d" % code, "final": final}
            break
        if code in GONE_STATUSES:
            result = {"state": "gone", "detail": "HTTP %d" % code}
        elif code in BLOCK_STATUSES:
            result = {"state": "blocked", "detail": "HTTP %d" % code}
        elif code == RATE_LIMIT_STATUS:
            result = {"state": "rate-limited", "detail": "HTTP 429"}
        elif code == 202:
            # Same reading as validate_sources.py: "Accepted" is never a
            # document — it is what several counties' bot-management fronts
            # serve, and treating it as success is how a block goes unnoticed.
            result = {"state": "blocked", "detail": "HTTP 202 — bot-management interstitial"}
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
             "`index.html` and `data/app/*.json`. Of those, %d chosen by this repo "
             "(a dead one is ours to fix) and %d carried from their own publisher "
             "(capped at WARN — see the script's header)."
             % (n[FAIL], n[WARN], n[OK], len(cites), hosts,
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

    cites, origin, prefixes = collect()
    if not cites:
        print("validate_card_links: FAIL — extracted 0 URLs, which cannot be right. "
              "The extraction patterns have drifted from index.html.", file=sys.stderr)
        sys.exit(1)

    if args.offline:
        hosts = collections.Counter(host_of(u) for u in cites)
        n_auth = sum(1 for v in origin.values() if v == AUTHORED)
        print("validate_card_links: %d URLs (%d chosen here, %d carried from their "
              "publisher) across %d hosts (offline; nothing probed)"
              % (len(cites), n_auth, len(cites) - n_auth, len(hosts)))
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

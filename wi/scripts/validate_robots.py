#!/usr/bin/env python3
"""
Check that every URL this instance's weekly scrapers FETCH is permitted by its
host's own robots.txt.

WHY THIS EXISTS
---------------
On 2026-08-31, adding Pepin County turned up seven county hosts publishing a
robots.txt whose `User-agent: *` group disallows the entire site — and this
repo was fetching all seven weekly, four of them for shipped board rosters.
Nothing in the repo could have noticed. `validate_sources.py` asks whether a
source still resolves; `validate_card_links.py` asks whether a link is alive;
neither asks whether the publisher wants an automated client there at all.

The scraper's COUNTIES table already carried a robots.txt note, and its whole
argument turned on the `*` group PERMITTING the board path for the two counties
it discussed (Iowa and Waushara, which disallow only /calendar, /meetings and
similar). That reasoning was right and was applied to two counties by hand. This
script applies it to every host, every month, so the answer cannot go stale and
a new county cannot be added against a host that has said no.

WHAT IT CHECKS, AND WHAT IT DELIBERATELY DOES NOT
-------------------------------------------------
It checks the URLs that are actually REQUESTED on a schedule, and it finds
them BY DISCOVERY rather than from a list of tables:

  * every http string in every upper-case attribute of BOTH scrapers —
    wi_county_board_scraper (weekly) and wi_county_officer_contact_scraper,
    which runs in TWO weekly workflows and so fetches its hosts twice a week,
  * a DOCUMENT_ROSTERS entry ONLY when it carries a `live` key, because that
    is the one thing in that table that makes a request. An entry without one
    is a transcription and is not a fetch — six of the nine are exactly that,
    and they must not be reported as a crawl of hosts they never touch.
  * everything EXCEPT the names in NOT_FETCHED (below), which are tables of
    already-read values the app displays. The default is to include, so a table
    added tomorrow is checked whether or not anyone remembers this file.

THE BOARD SIDE NAMED SIX TABLES BY HAND UNTIL 2026-09-02 and the paragraph
above claimed discovery of both. Three carriers written after it — Clark's
Official Directory, Pierce's annual directory, Marathon's members table — sat
outside all six, so this gate was not looking at `cms5.revize.com` or
`www.marathoncounty.gov` at all, and reported Clark's host green on four paths
the OFFICER scraper happens to read there. A hand-kept list of what a gate
covers is the one thing the gate cannot check. See NOT_FETCHED for what the
sweep then found that nobody had listed.

AND IT READS EACH POLICY WITH THE CLIENT THAT DOES THE CRAWLING (robots_headers
below). Sending a weaker client than the scraper's own turned seven counties'
readable policies into "unreadable — not assumed", which looks like caution and
means the rules were never read.

IT DOES NOT CHECK LINKS THE APP MERELY SHOWS. A `sourceUrl` on a card is an
address a reader clicks; robots.txt governs automated retrieval, not what a
page is allowed to link to. Mixing the two would report every carried county as
a violation of a rule it is the compliance with.

ROBOTS.TXT ITSELF IS ALWAYS FETCHED, by every agent, always — it is the file
whose entire purpose is to be read before deciding. A host that 404s it has no
policy and permits everything; a host that refuses to serve it is reported as
unknown rather than assumed either way.

THE `*` GROUP IS THE ONE THAT APPLIES, because this project's clients are none
of the named agents. Where a file names ClaudeBot or GPTBot and disallows them,
that is recorded in the scraper's own note and is not what this script reads:
a crawler that claims to be none of those is governed by `*`, and reading a
narrower group to get a friendlier answer would be picking the rule that suits.

Usage:
    python3 wi/scripts/validate_robots.py            # fetch and check
    python3 wi/scripts/validate_robots.py --offline  # list the surface only
"""

import glob
import gzip
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

def robots_headers(host):
    """The header set THIS host's own pages are already crawled with.

    ROBOTS.TXT MUST BE READ BY THE CLIENT THAT DOES THE CRAWLING, and until
    2026-09-02 this script sent its own bare User-Agent — one line, no Accept,
    no client hints — while the scraper it audits sends three carefully pinned
    header sets. That asymmetry is not a detail: `www.marathoncounty.gov`
    serves its board page to the scraper every week and answered THIS script
    403, so its policy was filed as "unreadable — not assumed", which reads
    like caution and means the rules were never read. It serves a 6,641-byte
    robots.txt to the scraper's own default client on the first try.

    Reading the policy with a WEAKER client than the crawl is the one
    asymmetry a compliance gate must not have. (The opposite — reaching for a
    stronger client than the crawl uses — would be defeating a control, and is
    not what this does: the pins below are exactly the scraper's own, host for
    host, and nothing is retried up the ladder.)
    """
    import wi_county_board_scraper as board
    if host in getattr(board, "HONEST_UA_HOSTS", ()):
        return board.HONEST_UA
    if host in _browser_header_hosts():
        return board.BROWSER
    return board.UA


def _browser_header_hosts():
    """Hosts whose county is pinned to the scraper's Chrome-navigation set."""
    import wi_county_board_scraper as board
    pinned = getattr(board, "BROWSER_HEADER_COUNTIES", set())
    return {urllib.parse.urlsplit(url).hostname
            for fips, _n, _s, _d, url in board.COUNTIES if fips in pinned}


def read_body(response):
    """The response text, gunzipped when the pinned header set asked for gzip.

    urllib does not decompress, and one of the three header sets sends
    `Accept-Encoding: gzip` — so without this, a host on that pin returns a
    robots.txt of binary noise that parses to zero rules and reports as
    permitting everything.
    """
    raw = response.read()
    if (response.headers.get("Content-Encoding") or "").lower() == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace")


def scheduled_scraper_modules():
    """[(module, label)] for every *_scraper.py a workflow runs on a schedule.

    The workflow files are the authority on "scheduled": a scraper nothing
    dispatches makes no requests, and sweeping it would report policies for
    fetches that never happen.
    """
    import importlib
    workflows = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)),
                             ".github", "workflows")
    texts = []
    for name in sorted(os.listdir(workflows)):
        if name.endswith((".yml", ".yaml")):
            with open(os.path.join(workflows, name), encoding="utf-8") as f:
                texts.append((name, f.read()))
    out = []
    for path in sorted(glob.glob(os.path.join(SCRIPT_DIR, "*_scraper.py"))):
        stem = os.path.basename(path)[:-3]
        runs = [n for n, t in texts if stem in t]
        if not runs:
            continue
        out.append((importlib.import_module(stem),
                    "%s [%s]" % (stem, ", ".join(runs))))
    if len(out) < 2:
        raise SystemExit("robots: discovered %d scheduled scraper(s) under %s — "
                         "that cannot be right, and a narrowed sweep reporting "
                         "OK is exactly what this gate must never do"
                         % (len(out), SCRIPT_DIR))
    return out


def fetched_urls():
    """[(url, why)] — every address this instance requests on a schedule."""
    import wi_county_board_scraper as board
    import wi_county_officer_contact_scraper as officers
    _excluded_specs_are_unscheduled(board)
    out = []
    for fips, name, seats, strategy, url in board.COUNTIES:
        out.append((url, "%s board roster (%s)" % (name, strategy)))
    # A CARRIED ROSTER IS NOT A FETCH unless it re-tries its live page.
    for spec in getattr(board, "DOCUMENT_ROSTERS", []):
        if spec.get("live"):
            out.append((spec["source_url"],
                        "%s carried roster, live re-try each run" % spec["name"]))
    # THE MODULE LIST IS DISCOVERED, NOT KEPT. It used to name three modules by
    # hand while eight other scheduled scrapers sat outside the sweep entirely —
    # this file's own comment called that "an open gap rather than a statement
    # that their hosts permit anything", and it was right: widening it found
    # milwaukeemaps.milwaukee.gov publishing `User-agent: * / Disallow: /` under
    # a fetch this repo had been making every week.
    #
    # A hand-kept list across modules is the same shape as the miss recorded
    # below, one level up, and the fleet has learned it twice elsewhere
    # (validate_card_links.py naming four instances of five;
    # check_roster_retention.py pointed at one instance's data/app). So the
    # subject is now every wi/scripts/*_scraper.py that a workflow actually
    # RUNS — which is exactly this gate's contract, "every address this
    # instance requests on a schedule". A scraper written tomorrow is swept the
    # day its workflow lands, and one that exists but is not scheduled is
    # correctly left alone.
    for module, label in scheduled_scraper_modules():
        for nm in dir(module):
            if not nm.isupper() or nm in NOT_FETCHED:
                continue
            for url in _strings(getattr(module, nm)):
                out.append((url, "%s %s" % (label, nm)))
    seen, uniq = set(), []
    for url, why in out:
        if url.startswith("http") and url not in seen:
            seen.add(url)
            uniq.append((url, why))
    return sorted(uniq)


# THE SWEEP IS BY DISCOVERY, NOT BY A LIST: it takes EVERY http string in every
# upper-case attribute of BOTH scrapers, so a table added tomorrow is checked
# whether or not anyone remembers this file. Over-reporting is the safe
# direction for a gate whose whole job is to never miss a fetch.
#
# THAT WAS TRUE OF THE CONTACT SCRAPER ONLY UNTIL 2026-09-02, and the docstring
# above claimed it of both. The board side named six tables by hand, and three
# carriers added after it was written — Clark's Official Directory, Pierce's
# annual directory and Marathon's members table — sat outside all six. So the
# gate whose entire purpose is to never miss a fetch was silently missing
# `cms5.revize.com` and `www.marathoncounty.gov` altogether; Clark's host was
# reported only because the OFFICER scraper happens to read four other paths
# there, which is the most misleading possible pass. Discovery also swept in
# four hosts nobody had listed at all: `web.archive.org` and `archive.org` (the
# archive ladder genuinely fetches them every run), `services1.arcgis.com` for
# the LTSB ward-witness query, and the second URL inside three specs whose
# key was not one of the three the hand list looked at. A HAND-KEPT LIST OF
# WHAT A GATE COVERS IS THE THING THE GATE CANNOT CHECK.
#
# Names listed below are the exceptions, and listing one is a CLAIM — that
# nothing in this repo requests those URLs — which is worth as much as the
# reading of the module that backs it.
#
#   CARRIED_CONTACTS holds the office contact of the four counties whose hosts
#   disallow this client. Its URLs are what the CARD SHOWS a reader, taken from
#   a capture made before the policy was read; `main()` emits them and makes no
#   request. It is the DOCUMENT_ROSTERS case one file over, and the same rule
#   applies for the same reason: a transcription is not a fetch. Note that this
#   table has no `live` escape hatch at all, so unlike a roster entry it cannot
#   drift back into being fetched without an edit here too.
#
#   Discovery also swept in four things nobody had listed: `web.archive.org`
#   and `archive.org`, which the archive ladder genuinely requests every run;
#   `services1.arcgis.com` for the LTSB ward-witness query that checks every
#   new county's district numbers; and the SECOND url inside three specs,
#   whose key was not one of the three the hand list looked at.
#
#   DOCUMENT_ROSTERS is the board scraper's own carried table — nine counties
#   read once and dated, six of them because their hosts ask automated readers
#   to stay off. Fetching those hosts to check a policy this project has ALREADY
#   read and complied with would be the one request the compliance forbids, so
#   the whole table is excepted here and its `live` entries are added back by
#   name in the loop above. That inversion is deliberate: an entry that starts
#   re-trying its page appears in this surface the moment it gains the key.
NOT_FETCHED = {"CARRIED_CONTACTS", "DOCUMENT_ROSTERS",
               # ASHLAND_BOARD is a reader kept for the day the county says
               # yes, not a schedule: ashlandcountywi.gov disallows the whole
               # site to every agent it does not name, so the roster moved to
               # DOCUMENT_ROSTERS and nothing dispatches this spec. The spec
               # stays because the reader needs it if the crawl is ever
               # re-enabled — see the scraper's Ashland section.
               "ASHLAND_BOARD"}
# AN EXCLUSION THAT CANNOT SILENTLY BECOME A LIE. Naming a spec here says
# "nothing fetches this", and the one way that stops being true is somebody
# re-registering it in SINGLE_COUNTY_CARRIERS — at which point the gate that
# exists to notice a disallowed crawl would be looking away from exactly the
# county it was hidden for. So the claim is CHECKED rather than trusted.
CARRIER_REGISTERED = "SINGLE_COUNTY_CARRIERS"


def _excluded_specs_are_unscheduled(board):
    """A NOT_FETCHED spec must not be registered as a live carrier."""
    registered = {id(spec) for spec, _strategy
                  in getattr(board, CARRIER_REGISTERED, ())}
    wrong = sorted(n for n in NOT_FETCHED
                   if id(getattr(board, n, None)) in registered)
    if wrong:
        raise SystemExit(
            "robots: FAIL — %s is listed in NOT_FETCHED (as not fetched) and is "
            "ALSO registered in %s, so it IS fetched weekly and this gate would "
            "not have checked its host. Either take it out of NOT_FETCHED or out "
            "of the carrier list." % (", ".join(wrong), CARRIER_REGISTERED))


def _strings(obj):
    """Every http string anywhere inside a nested structure."""
    if isinstance(obj, str):
        return [obj] if obj.startswith("http") else []
    if isinstance(obj, dict):
        return [u for v in obj.values() for u in _strings(v)]
    if isinstance(obj, (list, tuple, set)):
        return [u for v in obj for u in _strings(v)]
    return []


def star_disallows(text):
    """The `User-agent: *` group's Disallow lines, or None if it has no group.

    Consecutive `User-agent:` lines share one group, which is why the agents
    are collected and the Disallow lines applied to all of them — a file that
    reads `User-agent: A` / `User-agent: *` / `Disallow: /` disallows `*`.
    """
    groups, current, pending = {}, [], True
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (p.strip() for p in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not pending:
                current, pending = [], True
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif key in ("disallow", "allow") and current:
            pending = False
            for agent in current:
                groups.setdefault(agent, []).append((key, value))
    return groups.get("*")


def resolve_template(url):
    """A `%s`-templated URL as the path shape actually requested.

    Six of the swept constants are FORMAT TEMPLATES, not addresses — the
    archive ladder's four (`https://web.archive.org/save/%s` and friends) and
    Pierce's directory pair, which is templated on the year. Matching a
    template against robots.txt verbatim asks the wrong question twice: `%s`
    stands where a real path segment goes, and `%%20` is a doubled percent
    that means a literal `%20` on the wire. Pierce's real path is
    `/revize/piercewi/Agendas%20and%20Minutes/...`, so a host rule naming that
    directory would not have matched the string this script was holding.

    The substitution is exactly what `%` formatting does, in the same order:
    the placeholder first, then the doubled percent. A path segment is
    stand-in text of the right SHAPE, which is all a prefix rule can see; the
    report marks these rows so nobody reads a checked template as a checked
    address.
    """
    return url.replace("%s", "PLACEHOLDER").replace("%%", "%")


def _rule_re(value):
    """One robots.txt path pattern as a regex anchored at the path start.

    `*` matches any run of characters and a TRAILING `$` anchors the end of the
    path — RFC 9309 section 2.2.3, and what every major crawler implements.
    Everything else is a literal, so the regex is built from escaped chunks
    rather than by escaping the whole string and unescaping the metacharacters.
    """
    anchored = value.endswith("$")
    body = value[:-1] if anchored else value
    pattern = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile("^" + pattern + ("$" if anchored else ""))


def permitted(path, rules):
    """robots.txt longest-match: the most specific rule wins, Allow ties win.

    THE WILDCARDS ARE NOT DECORATION, and leaving them out got a real host
    wrong in the direction that matters. This did literal `startswith`
    matching, which cannot match a pattern containing `*` or `$` AT ALL — so
    every wildcard rule silently evaluated as "does not apply". On
    cms5.revize.com, whose `*` group reads

        Allow: /*.pdf$   (and .DOC/.DOCX/.PPT/.PPTX)
        Disallow: /

    that turned an unmistakable policy — documents yes, everything else no —
    into a flat refusal, because only the bare `Disallow: /` could match. The
    same blindness runs the other way and is worse: a wildcard DISALLOW that
    genuinely covers a path this repo fetches would have been ignored, and the
    gate would have reported the crawl permitted. Clark's own file carries
    `Disallow: *?lightbox=`, which this had been discarding; it happens not to
    cover anything fetched here, which is luck rather than a check.

    Specificity is the length of the rule as WRITTEN, which is what makes
    `/*.pdf$` (7) beat `/` (1) rather than the other way round.
    """
    best_len, best_kind = -1, "allow"
    for kind, value in rules:
        if not value:
            continue                    # `Disallow:` with no value permits all
        if not _rule_re(value).match(path):
            continue
        if len(value) > best_len:
            best_len, best_kind = len(value), kind
        elif len(value) == best_len and kind == "allow":
            best_kind = "allow"
    return best_kind == "allow"


def main():
    offline = "--offline" in sys.argv[1:]
    urls = fetched_urls()
    by_host = {}
    for url, why in urls:
        parts = urllib.parse.urlparse(resolve_template(url))
        # RFC 9309 section 2.2.2: the string a rule is matched against is the
        # path AND the query. Matching the path alone would let a rule like
        # `Disallow: /*?lightbox=` — which exists on one county's host — miss
        # the very URLs it names, and would call a cache-busted `.pdf?t=...`
        # permitted under an `Allow: /*.pdf$` that does not actually reach it.
        target = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
        by_host.setdefault(parts.netloc, []).append((target, why, url))
    print("robots: %d scheduled URLs across %d hosts" % (len(urls), len(by_host)),
          file=sys.stderr)
    if offline:
        for host in sorted(by_host):
            print("  %-34s %d URL(s)" % (host, len(by_host[host])))
        return 0

    disallowed, unknown = [], []
    for host in sorted(by_host):
        try:
            req = urllib.request.Request("https://%s/robots.txt" % host,
                                         headers=robots_headers(host))
            with urllib.request.urlopen(req, timeout=25) as r:
                body = read_body(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("  ok   %-34s no robots.txt (nothing disallowed)" % host)
                continue
            unknown.append((host, "HTTP %d" % e.code))
            print("  ?    %-34s robots.txt unreadable (HTTP %d)" % (host, e.code))
            continue
        except Exception as e:          # noqa: BLE001 - reachability, not policy
            unknown.append((host, str(e)[:50]))
            print("  ?    %-34s robots.txt unreadable (%s)" % (host, str(e)[:44]))
            continue
        rules = star_disallows(body)
        if rules is None:
            print("  ok   %-34s no `*` group (nothing disallowed to us)" % host)
            continue
        bad = [(p, why) for p, why, _u in by_host[host] if not permitted(p, rules)]
        if bad:
            for path, why in bad:
                disallowed.append((host, path, why))
            print("  STOP %-34s `*` disallows %d of %d scheduled path(s)"
                  % (host, len(bad), len(by_host[host])))
        else:
            print("  ok   %-34s `*` permits our %d path(s)"
                  % (host, len(by_host[host])))
        time.sleep(0.2)

    print(file=sys.stderr)
    if unknown:
        print("robots: %d host(s) would not serve robots.txt — policy unknown, "
              "not assumed: %s" % (len(unknown), ", ".join(h for h, _ in unknown)),
              file=sys.stderr)
    if disallowed:
        print("robots: FAIL — %d scheduled fetch(es) are disallowed by the host's "
              "own robots.txt:" % len(disallowed), file=sys.stderr)
        for host, path, why in disallowed:
            print("  %s%s  — %s" % (host, path, why), file=sys.stderr)
        print("\nA county that asks not to be crawled has not refused to publish: "
              "the routes are to carry the roster as a dated document "
              "(DOCUMENT_ROSTERS, no `live` key), to let the county go unnamed "
              "with a gap record, or to ask the county. Do not simply rename the "
              "user agent.", file=sys.stderr)
        return 1
    print("robots: OK — every scheduled fetch is permitted by its host's `*` group",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

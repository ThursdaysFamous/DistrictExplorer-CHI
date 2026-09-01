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
It checks the URLs that are actually REQUESTED on a schedule:

  * every `source_url` in wi_county_board_scraper's COUNTIES, plus the
    ARCGIS / ARCHIVE / CONSTITUENT / PDF / FRAMED_TABLE / WITNESSED tables,
  * OFFICER_PAGES and MEMBER_PAGES, which are second fetches per county,
  * every http URL in wi_county_officer_contact_scraper, which runs in TWO
    weekly workflows and so fetches its hosts twice a week,
  * a DOCUMENT_ROSTERS entry ONLY when it carries a `live` key, because that
    is the one thing in that table that makes a request. An entry without one
    is a transcription and is not a fetch — Pepin is exactly that, and it must
    not be reported as a crawl of a host it never touches.

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

import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"}


def fetched_urls():
    """[(url, why)] — every address this instance requests on a schedule."""
    import wi_county_board_scraper as board
    out = []
    for fips, name, seats, strategy, url in board.COUNTIES:
        out.append((url, "%s board roster (%s)" % (name, strategy)))
    for table, label in (
        (getattr(board, "ARCGIS_COUNTIES", []), "county GIS layer"),
        (getattr(board, "ARCHIVE_COUNTIES", []), "archive ladder (county asked first)"),
        (getattr(board, "CONSTITUENT_COUNTIES", []), "constituent directory"),
        (getattr(board, "PDF_COUNTIES", []), "directory PDF"),
        (getattr(board, "FRAMED_TABLE_COUNTIES", []), "framed table"),
        (getattr(board, "WITNESSED_DOCUMENT_COUNTIES", []), "witnessed document"),
    ):
        for spec in table:
            for key in ("source_url", "page", "url"):
                if spec.get(key):
                    out.append((spec[key], "%s %s" % (spec.get("name", "?"), label)))
    # A CARRIED ROSTER IS NOT A FETCH unless it re-tries its live page.
    for spec in getattr(board, "DOCUMENT_ROSTERS", []):
        if spec.get("live"):
            out.append((spec["source_url"],
                        "%s carried roster, live re-try each run" % spec["name"]))
    for fips, spec in (getattr(board, "OFFICER_PAGES", {}) or {}).items():
        if isinstance(spec, dict) and spec.get("url"):
            out.append((spec["url"], "officers block for %s" % fips))
    for fips, spec in (getattr(board, "MEMBER_PAGES", {}) or {}).items():
        for url in _strings(spec):
            out.append((url, "member pages for %s" % fips))

    import wi_county_officer_contact_scraper as officers
    for nm in dir(officers):
        if not nm.isupper():
            continue
        for url in _strings(getattr(officers, nm)):
            out.append((url, "county officer contact (twice weekly)"))
    seen, uniq = set(), []
    for url, why in out:
        if url.startswith("http") and url not in seen:
            seen.add(url)
            uniq.append((url, why))
    return sorted(uniq)


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


def permitted(path, rules):
    """robots.txt longest-match: the most specific rule wins, Allow ties win."""
    best_len, best_kind = -1, "allow"
    for kind, value in rules:
        if not value:
            continue                    # `Disallow:` with no value permits all
        if path.startswith(value) and len(value) > best_len:
            best_len, best_kind = len(value), kind
        elif path.startswith(value) and len(value) == best_len and kind == "allow":
            best_kind = "allow"
    return best_kind == "allow"


def main():
    offline = "--offline" in sys.argv[1:]
    urls = fetched_urls()
    by_host = {}
    for url, why in urls:
        parts = urllib.parse.urlparse(url)
        by_host.setdefault(parts.netloc, []).append(
            ((parts.path or "/"), why, url))
    print("robots: %d scheduled URLs across %d hosts" % (len(urls), len(by_host)),
          file=sys.stderr)
    if offline:
        for host in sorted(by_host):
            print("  %-34s %d URL(s)" % (host, len(by_host[host])))
        return 0

    disallowed, unknown = [], []
    for host in sorted(by_host):
        try:
            req = urllib.request.Request("https://%s/robots.txt" % host, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read().decode("utf-8", "replace")
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

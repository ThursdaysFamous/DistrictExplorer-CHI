#!/usr/bin/env python3
"""
One-shot WEC + MPD recon CAPTURE, designed to run FROM GITHUB ACTIONS —
the follow-through on the 2026-08-27 probe (`wi_wec_probe.py`), which
measured the Cloudflare block SANDBOX-SIDE: elections.wi.gov's managed
challenge clears for a real browser from a GitHub runner in ~4 seconds,
and myvote.wi.gov and city.milwaukee.gov answer PLAIN clients HTTP 200.

The probe answered "can this project look?"; this recon answers "what is
there to see?" — because the development sandbox still cannot read any of
these hosts, so every decision that follows must be made from what THIS
run brings back:

  * WEC (elections.wi.gov + MyVote): does the commission publish the
    statewide ward-to-polling-place pairing, early-voting/drop-box site
    lists, or a municipal-clerks roster AS DATA anywhere behind the
    front door? Gap `ward-polling-places` and two matrix cells wait on
    exactly this; the last bulk artifact any search index shows predates
    2020, and the probe's harvest found zero file anchors on the front
    pages. The recon starts at the front doors, harvests nav links whose
    text or URL reads data-ish (data, statistics, results, polling,
    clerk, voter, publication...), fetches a bounded set of those pages
    through the SAME cleared browser session, and inventories every
    bulk-file anchor (/media/<id>/download, .csv/.xlsx/.zip) it sees —
    re-fetching a few to learn whether the file URLs answer too.
  * MPD (city.milwaukee.gov/police): the district pages carry the
    captains this project could never verify (gap
    `mpd-district-leadership`). The recon fetches the police index,
    discovers district-page links, and captures each district page so
    the weekly captains scraper can be written against REAL page
    structure rather than a guess.

WHAT COMES BACK, in three channels sized to their readers:
  * GITHUB_STEP_SUMMARY — the inventory table (page, engine, status,
    bytes, bulk anchors found);
  * stdout (the job log) — per-page EXTRACT blocks: title, headings,
    matched links, tel:/mailto:, and a bounded text excerpt (larger for
    MPD pages, whose text carries the names) — this is the channel the
    development environment can actually read back;
  * a run artifact — every captured page's full HTML plus
    inventory.json, the durable record.

Same rules as the probe: plain requests first; a real headless Chromium
only where the plain client is refused (no evasion — a challenge still
standing after WEC_CHALLENGE_WAIT_S is recorded as refusal, never worked
around); ~1s politeness delay between fetches on the same host; hard
caps on page counts. Refusal and absence are MEASUREMENTS and exit 0; a
non-zero exit means the recon itself failed to run.

Usage:
    python3 wi/scripts/wi_wec_recon.py --out-dir wi-recon-capture
"""

import argparse
import html as html_mod
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
CHALLENGE_MARKERS = ("just a moment", "attention required",
                     "checking your browser", "cf-chl",
                     "challenges.cloudflare.com/turnstile")

BULK_LINK_RE = re.compile(
    r"/media/\d+/download|\.csv(?:$|[?#])|\.xlsx?(?:$|[?#])|\.zip(?:$|[?#])",
    re.IGNORECASE)
# nav links worth following on WEC's site, by URL or link text
WEC_FOLLOW_RE = re.compile(
    r"statistic|(?<![a-z])data(?![a-z])|result|polling|clerk|voter|absentee|"
    r"early.?voting|drop.?box|publication|report|election.?administration|"
    r"download", re.IGNORECASE)
MPD_DISTRICT_RE = re.compile(r"/police[^\"']*(district|Districts)[^\"']*",
                             re.IGNORECASE)

WEC_PAGE_CAP = 12
MPD_PAGE_CAP = 9
BULK_PROBE_CAP = 8
TEXT_EXCERPT_WEC = 2500
TEXT_EXCERPT_MPD = 6000


def looks_like_challenge(text):
    low = (text or "").lower()
    return any(m in low for m in CHALLENGE_MARKERS)


def page_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html or "",
                  re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:150] if m else None


def strip_text(html, limit):
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ",
               html or "")
    t = html_mod.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t).strip()[:limit]


def headings(html):
    out = []
    for m in re.finditer(r"<h([1-4])[^>]*>([\s\S]*?)</h\1>", html or "",
                         re.IGNORECASE):
        text = re.sub(r"\s+", " ",
                      html_mod.unescape(re.sub(r"<[^>]+>", " ",
                                               m.group(2)))).strip()
        if text:
            out.append("h%s: %s" % (m.group(1), text[:120]))
    return out[:40]


def links_of(html, base):
    out = []
    for m in re.finditer(r"""<a\s[^>]*href\s*=\s*["']([^"'#]+)["'][^>]*>"""
                         r"""([\s\S]{0,200}?)</a>""", html or "",
                         re.IGNORECASE):
        href = urljoin(base, m.group(1).strip())
        text = re.sub(r"\s+", " ",
                      html_mod.unescape(re.sub(r"<[^>]+>", " ",
                                               m.group(2)))).strip()[:100]
        out.append((href, text))
    return out


def contacts_of(html):
    tels = sorted(set(re.findall(r"""href=["']tel:([^"']+)""", html or "",
                                 re.IGNORECASE)))
    mails = sorted(set(re.findall(r"""href=["']mailto:([^"']+)""", html or "",
                                  re.IGNORECASE)))
    return tels[:20], mails[:20]


class Recon:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.session = requests.Session()
        self.browser = None
        self._pw = None
        self.pages = []       # inventory rows
        self.counter = 0
        self.last_fetch = {}  # host -> time

    def _polite(self, url):
        host = urlparse(url).netloc
        wait = 1.0 - (time.time() - self.last_fetch.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last_fetch[host] = time.time()

    def _ensure_browser(self):
        if self.browser is not None:
            return
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        exe = os.environ.get("WEC_CHROMIUM_EXECUTABLE")
        launch = (self._pw.chromium.launch(headless=True, executable_path=exe)
                  if exe else self._pw.chromium.launch(headless=True))
        self.browser = launch.new_context(
            user_agent=UA, locale="en-US",
            viewport={"width": 1366, "height": 900})
        self.wait_s = int(os.environ.get("WEC_CHALLENGE_WAIT_S", "120"))

    def fetch(self, url):
        """Plain first, browser fallback on refusal. Returns (record, html)."""
        self._polite(url)
        rec = {"url": url}
        try:
            resp = self.session.get(url, headers=HEADERS, timeout=45)
            rec["status"] = resp.status_code
            if resp.status_code == 200 and not looks_like_challenge(resp.text):
                rec["engine"] = "requests"
                return rec, resp.text
            rec["plain"] = ("challenge" if looks_like_challenge(resp.text)
                            else "HTTP %d" % resp.status_code)
        except requests.RequestException as e:
            rec["plain"] = str(e)[:200]
        try:
            self._ensure_browser()
        except Exception as e:  # noqa: BLE001
            rec["engine"] = "none"
            rec["error"] = "chromium unavailable: %s" % str(e)[:150]
            return rec, None
        page = self.browser.new_page()
        try:
            start = time.time()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            while (time.time() - start < self.wait_s
                   and looks_like_challenge(page.content())):
                page.wait_for_timeout(1000)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            html = page.content()
            rec["engine"] = "chromium"
            rec["seconds"] = round(time.time() - start, 1)
            if looks_like_challenge(html):
                rec["error"] = "challenge did not clear in %ds" % self.wait_s
                return rec, None
            return rec, html
        except Exception as e:  # noqa: BLE001
            rec["engine"] = "chromium"
            rec["error"] = str(e)[:200]
            return rec, None
        finally:
            page.close()

    def probe_link(self, url):
        """Status-only look at a bulk-file anchor, browser session preferred
        (its cookies carry any clearance)."""
        self._polite(url)
        rec = {"url": url}
        try:
            if self.browser is not None:
                resp = self.browser.request.get(url, timeout=45000)
                rec["status"] = resp.status
                rec["content_type"] = (resp.headers or {}).get("content-type")
                body = resp.body()
                rec["bytes"] = len(body)
                rec["challenge"] = looks_like_challenge(
                    body[:4096].decode("utf-8", "replace"))
                resp.dispose()
            else:
                resp = self.session.get(url, headers=HEADERS, timeout=45,
                                        stream=True)
                rec["status"] = resp.status_code
                rec["content_type"] = resp.headers.get("content-type")
                head = resp.raw.read(4096, decode_content=True)
                rec["challenge"] = looks_like_challenge(
                    head.decode("utf-8", "replace"))
                resp.close()
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:200]
        return rec

    def capture(self, url, tag, excerpt_limit):
        rec, html = self.fetch(url)
        rec["tag"] = tag
        if html is not None:
            self.counter += 1
            slug = re.sub(r"[^a-z0-9]+", "-",
                          urlparse(url).path.lower()).strip("-") or "root"
            fname = "%03d_%s_%s.html" % (self.counter, tag, slug[:60])
            with open(os.path.join(self.out_dir, fname), "w",
                      encoding="utf-8") as f:
                f.write(html)
            rec["file"] = fname
            rec["bytes"] = len(html)
            rec["title"] = page_title(html)
            rec["bulk_links"] = sorted(
                {h for h, _ in links_of(html, url) if BULK_LINK_RE.search(h)})
            # ---- the log extract: the channel the sandbox can read back ----
            tels, mails = contacts_of(html)
            print("\n===== EXTRACT [%s] %s" % (tag, url))
            print("title: %s" % rec["title"])
            for h in headings(html):
                print("  " + h)
            if rec["bulk_links"]:
                print("  bulk-file anchors (%d):" % len(rec["bulk_links"]))
                for b in rec["bulk_links"][:25]:
                    print("    " + b)
            if tels or mails:
                print("  tel: %s" % ", ".join(tels))
                print("  mailto: %s" % ", ".join(mails))
            print("  text: %s" % strip_text(html, excerpt_limit))
            print("===== END EXTRACT")
        self.pages.append(rec)
        return rec, html

    def close(self):
        if self._pw is not None:
            try:
                self.browser.close()
            finally:
                self._pw.stop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    r = Recon(args.out_dir)

    # ---- WEC: front doors, then the data-ish nav ----
    wec_queue = []
    for front in ("https://elections.wi.gov/", "https://myvote.wi.gov/en-us/"):
        rec, html = r.capture(front, "wec-front", TEXT_EXCERPT_WEC)
        if html:
            for href, text in links_of(html, front):
                host = urlparse(href).netloc
                if host not in ("elections.wi.gov", "myvote.wi.gov"):
                    continue
                if WEC_FOLLOW_RE.search(href) or WEC_FOLLOW_RE.search(text):
                    if href not in wec_queue:
                        wec_queue.append(href)
    seen = {p["url"] for p in r.pages}
    followed = 0
    for href in wec_queue:
        if followed >= WEC_PAGE_CAP:
            print("WEC follow cap reached — %d candidate link(s) not fetched: %s"
                  % (len(wec_queue) - followed,
                     [u for u in wec_queue if u not in seen][:15]))
            break
        if href in seen:
            continue
        seen.add(href)
        r.capture(href, "wec-data", TEXT_EXCERPT_WEC)
        followed += 1

    all_bulk = sorted({b for p in r.pages for b in p.get("bulk_links", [])})
    bulk_probes = [r.probe_link(b) for b in all_bulk[:BULK_PROBE_CAP]]

    # ---- MPD: police index, then the district pages ----
    mpd_queue = []
    rec, html = r.capture("https://city.milwaukee.gov/police", "mpd-index",
                          TEXT_EXCERPT_MPD)
    if html:
        for href, text in links_of(html, "https://city.milwaukee.gov/police"):
            if urlparse(href).netloc != "city.milwaukee.gov":
                continue
            if MPD_DISTRICT_RE.search(href) or re.search(
                    r"district\s*(one|two|three|four|five|six|seven|\d)\b",
                    text, re.IGNORECASE):
                if href not in mpd_queue:
                    mpd_queue.append(href)
    fetched = 0
    for href in mpd_queue:
        if fetched >= MPD_PAGE_CAP:
            print("MPD follow cap reached — not fetched: %s"
                  % mpd_queue[fetched:][:10])
            break
        if href in seen:
            continue
        seen.add(href)
        r.capture(href, "mpd-district", TEXT_EXCERPT_MPD)
        fetched += 1

    r.close()

    inventory = {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "vantage": ("github-actions" if os.environ.get("GITHUB_ACTIONS")
                    else "local"),
        "pages": r.pages,
        "bulk_probes": bulk_probes,
        "wec_candidates_found": wec_queue,
        "mpd_candidates_found": mpd_queue,
    }
    with open(os.path.join(args.out_dir, "inventory.json"), "w") as f:
        json.dump(inventory, f, indent=1)
        f.write("\n")

    def cell(s):
        # Playwright errors are multiline call logs; a table cell is one line
        return re.sub(r"\s+", " ", str(s)).strip()[:140]

    lines = ["## WEC + MPD recon — %s vantage" % inventory["vantage"], "",
             "| page | tag | engine | status | bytes | bulk anchors |",
             "|---|---|---|---|---|---|"]
    for p in r.pages:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            p["url"], p.get("tag"), p.get("engine"),
            cell(p.get("error") or p.get("status")), p.get("bytes", "—"),
            len(p.get("bulk_links", []))))
    if bulk_probes:
        lines.append("")
        lines.append("**Bulk-file anchors probed (%d of %d found):**"
                     % (len(bulk_probes), len(all_bulk)))
        for b in bulk_probes:
            lines.append("- `%s` -> %s" % (
                b["url"], b.get("error") or "HTTP %s, %s, %s bytes%s" % (
                    b.get("status"), b.get("content_type"), b.get("bytes"),
                    " (CHALLENGE BODY)" if b.get("challenge") else "")))
    summary = "\n".join(lines)
    print("\n" + summary)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a") as f:
            f.write(summary + "\n")

    captured = sum(1 for p in r.pages if p.get("file"))
    print("\nrecon: %d page(s) captured to %s, %d bulk anchor(s) found, "
          "%d probed" % (captured, args.out_dir, len(all_bulk),
                         len(bulk_probes)), file=sys.stderr)
    return 0 if captured else 1


if __name__ == "__main__":
    sys.exit(main())

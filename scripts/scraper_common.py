"""
Shared plumbing for the scripts/ fleet — the parts that are identical in
dozens of files BECAUSE they carry no county knowledge at all.

WHY THIS MODULE EXISTS. The 2026-08-24 scripts audit measured the fleet at 257
files and found the same three fragments pasted everywhere: 93 byte-identical
`fail()` definitions differing only in their label string, one browser
User-Agent pinned at Chrome/126 in 46 definitions (with six more multi-file UA
strings behind it), and four independent retellings of the same retry loop —
of which only henry_county_board_scraper.py's (written after Henry's directory
served back-to-back 429s on 2026-08-02) honours Retry-After and refuses to
retry a 404. The 2026-07-09 ruling in docs/OPTIMIZATION_PLAYBOOK.md ("keep
scrapers standalone") still governs everything HEURISTIC — parsers, selectors,
zero-row guards, per-county quirks stay in the county's own file, which is
where a reader looks for them — but a fail() that prints a label is not a
heuristic, and a UA string that exists in 46 files is 46 chances to drift.
docs/OPTIMIZATION_PLAYBOOK.md §8 records the supersession.

THE USER-AGENT CONSTANTS CONSOLIDATE THE DEFINITION, NEVER THE VALUE. Changing
a scraper's UA can change how a county site treats it — several sites in this
fleet block or challenge by client fingerprint — so each constant below is the
exact bytes its importers were already sending, drifted Chrome pins and all.
Unifying the VALUES is deliberately not done here; if it ever is, it happens
per county with that county's weekly run as the witness. Single-file UA
strings (the engine tooling, the jodaviess builder, validate_sources) stay in
their own files: a one-consumer constant consolidates nothing.

STDLIB-ONLY AT MODULE SCOPE, deliberately: scripts/validate_workflow_deps.py
walks module-scope import closures against each workflow's pip line, and this
module is imported by scripts whose workflows install nothing. `requests` is
imported inside fetch(), the one function that needs it.
"""
import sys
import time

# --- User-Agent strings (see the module docstring: definitions, not values).
# Browser strings, by platform token and pinned Chrome version:
UA_CHROME_WIN_126 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
UA_CHROME_WIN_126_FULL = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
UA_CHROME_WIN_124 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
UA_CHROME_X11_128 = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
UA_CHROME_X11_120 = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# Self-identifying bot strings:
UA_ROSTER_BOT = "chidistricts.com roster bot (civic data; contact via site)"
UA_ROSTER_COMPACT = "Mozilla/5.0 (compatible; districtexplorer-roster/1.0)"
UA_CIVIC_BOT = ("Mozilla/5.0 (compatible; chidistricts.com civic data bot; "
                "+https://chidistricts.com/)")


def make_fail(label):
    """The fleet's one failure voice: '<label>: FAIL — <msg>' to stderr, exit 1.

    Byte-identical output to the 93 inline copies this replaces; the label is
    the county/script slug those copies hard-coded.
    """
    def fail(msg):
        print("%s: FAIL — %s" % (label, msg), file=sys.stderr)
        sys.exit(1)
    return fail


def fetch(url, headers, timeout=60, attempts=5, retry_after_cap=30.0, verify=None):
    """GET with the fleet's pacing rules, modeled on henry_county_board_scraper
    (the 2026-08-02 back-to-back-429 story): 429 and 5xx are retried, honouring
    a numeric Retry-After capped at retry_after_cap so a hostile value cannot
    hang CI; 401/403/404 raise immediately — a moved or refused page is not
    fixed by waiting. Returns the requests Response (callers take .text or
    .content). Raises RuntimeError after `attempts` failures.

    `verify` passes through to requests untouched (None means the library
    default — verification ON); pinned-CA callers hand in the bundle path
    aia_bundle.ca_bundle() built. Nothing here can disable verification.
    """
    import requests  # function-local: see the module docstring

    last = None
    for attempt in range(attempts):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=verify)
            if resp.status_code == 429 or resp.status_code >= 500:
                # Retry-After may be seconds or a date; only the numeric form
                # is honoured.
                after = (resp.headers.get("Retry-After") or "").strip()
                delay = min(float(after), retry_after_cap) if after.isdigit() \
                    else 2.0 * (attempt + 1)
                last = "HTTP %d" % resp.status_code
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if getattr(exc.response, "status_code", None) in (401, 403, 404):
                raise
            last = str(exc)
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("failed to fetch %s after %d attempts: %s"
                       % (url, attempts, last))

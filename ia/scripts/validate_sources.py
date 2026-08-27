#!/usr/bin/env python3
"""
Source freshness gate for the app's data layers.

Why this exists: unlike the roster scrapers (which re-pull the same page every
week), several layers point at a *specific* upstream dataset that the publisher
silently supersedes with a new one:

  * Socrata portal datasets can be versioned by year. The reference fork's CPS
    attendance-boundary layers, for example, are published fresh every school
    year under a BRAND NEW dataset id (…SY2526 → …SY2627), so the id hardcoded
    in index.html keeps returning last year's boundaries long after a newer one
    exists. Nothing errors; the data just quietly goes stale.
  * Pre-built boundary layers (in this instance: the TIGERweb-derived district
    files) were downloaded at build time. The check there is provenance: is
    the source we cite still reachable, and a reminder to re-verify after
    each redistricting cycle.

This script does NOT edit index.html or any data file — swapping a dataset id
is a judgement call (the "newer" dataset may have a different schema), so, like
the roster workflows, it surfaces drift for a human instead of auto-applying it.

What it checks (findings carry a severity — FAIL, WARN, or OK):
  1. Manifest ↔ app coherence: every dataset id / data file the manifest knows
     about is still referenced in index.html (guards this file drifting from the
     app it validates).                                                   [FAIL]
  2. Socrata datasets: each id still resolves and still carries the stable part
     of its expected name (a rename usually means it was replaced).       [FAIL]
     For year-versioned datasets, the portal catalog is searched for a newer
     edition than the one in use.                                         [WARN]
  3. Shapefile provenance: the cited source URL is reachable and the built
     data/app file is present.                             [WARN / FAIL if gone]
  4. Live service endpoints (none in this instance's first PR — every layer
     ships pre-built; grown as later layers add live TIGERweb reads).      [WARN]

Exit status: 0 when nothing needs a human (OK or WARN only), 1 on any FAIL.
Newer-edition detection is deliberately WARN, not FAIL — the current dataset
still works and a person decides whether/when to migrate. The scheduled
workflow (.github/workflows/ia-validate-sources.yml) opens an issue on WARN or
FAIL so drift is never silent, without turning the build red.

Usage:
    python3 ia/scripts/validate_sources.py                 # human-readable report
    python3 ia/scripts/validate_sources.py --report r.md   # also write markdown
    python3 ia/scripts/validate_sources.py --status-file s.txt   # ok|warn|fail
    python3 ia/scripts/validate_sources.py --offline       # manifest↔app checks only
"""

import argparse
import json
import os
import re
import sys

try:
    import requests
except ImportError:  # pragma: no cover - requests is pinned in requirements.txt
    requests = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

HTTP_TIMEOUT = 25

# The freshness gate's source manifest for the Iowa instance. Every layer this
# instance adds gets its rows here in the same change (CLAUDE.md's
# conventions; the reference repo's validate_sources.py shows a mature
# manifest's full shape, including year-search patterns and the `blocked`
# inversion).
SOCRATA_DOMAIN = "data.invalid"  # this fork's Socrata portal, if it adopts one
CATALOG_API = "https://api.us.socrata.com/api/catalog/v1"

# Socrata dataset ids the app hardcodes (none in the starter set).
SOCRATA = []

# Same-origin data/app files and the upstream source each was built from.
PROVENANCE = [
    {
        "layer": "us-house",
        "app_file": "congress-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0",
        "note": "Congressional districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "us-house",
        "app_file": "congress-roster.json",
        "source_url": "https://unitedstates.github.io/congress-legislators/legislators-current.json",
        "note": "Delegation roster from the public-domain congress-legislators project; refreshed weekly by update-ia-congress-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "state-counties.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "County polygons pre-built from TIGERweb by ia/scripts/build_state_counties.py.",
    },
    {
        "layer": "county",
        "app_file": "metro-outline.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "The whole-state outline for the coverage wash, pre-built by ia/scripts/build_metro_outline.py — dissolved from all 99 counties' geometry on the same layer as state-counties.json, not fetched as a separate state polygon (so a future partial-coverage narrowing needs only a smaller METRO_COUNTY_FIPS, the Wisconsin precedent).",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/1",
        "note": "State Senate districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-members.json",
        "source_url": "https://data.openstates.org/people/current/ia.csv",
        "note": "Senate roster base (name, party) from the Open States current-people export; refreshed weekly by update-ia-legislature-roster.yml.",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-members.json",
        "source_url": "https://www.legis.iowa.gov/legislators/senate",
        "note": (
            "The Legislature's own senate directory — personIDs feed "
            "ia_legislature_scraper.py's per-legislator profile-page reads "
            "(Capitol phone/e-mail, and the Capitol's own address where "
            "published). Unlike Wisconsin's single listing page, Iowa's "
            "office/phone/email data lives on each member's own profile page, "
            "not this index — see WATCH.md's open question on whether those "
            "profile-page URLs are session-scoped."
        ),
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/2",
        "note": "State House districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-members.json",
        "source_url": "https://data.openstates.org/people/current/ia.csv",
        "note": "House roster base (name, party) from the Open States current-people export; refreshed weekly by update-ia-legislature-roster.yml.",
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-members.json",
        "source_url": "https://www.legis.iowa.gov/legislators/house",
        "note": (
            "The Legislature's own house directory — same personID-driven "
            "profile-page enrichment route as the senate row above."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CountySupervisorDistricts/FeatureServer/0",
        "note": (
            "The Iowa Legislature's own ArcGIS organization — county supervisor "
            "districts for 95 of 99 counties (the other 3 SF-75-transitioning "
            "counties and Jones's absence are handled separately below); "
            "vintage 2024-01-30 (WATCH.md tracks whether it moves)."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://services5.arcgis.com/ya62ECiavqTkK0wv/arcgis/rest/services/BlackHawkCoSupervisor_LSAplan1/FeatureServer/0",
        "note": (
            "Black Hawk County's own hosted GIS — its adopted Senate File 75 "
            "plan (5 districts), shipped in place of the state layer's stale "
            "pre-SF75 at-large row for this county alone."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://www.storycountyiowa.gov/1172/Jurisdictional-Maps",
        "note": (
            "Story County's own site — states its SOS-approved Senate File 75 "
            "plan's facts; no GIS service found, so the county ships as one "
            "county-level TRANSITIONING feature pending real district geometry."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://johnsoncountyiowa.gov/supervisor-districts",
        "note": (
            "Johnson County's own site — states its SOS-approved Senate File "
            "75 plan's facts; no GIS service found, so the county ships as "
            "one county-level TRANSITIONING feature pending real district "
            "geometry."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-county-board-directory.json",
        "source_url": "https://www.iowacounties.org/member-resources/county-directory/",
        "note": (
            "Iowa State Association of Counties' member directory — one "
            "detail page per county naming its own official website, read by "
            "ia_county_directory_scraper.py; not a roster of supervisors, "
            "since Iowa publishes no statewide one."
        ),
    },
    {
        "layer": "school-district-unified",
        "app_file": "ia-school-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0",
        "note": (
            "324 unified school districts (325 TIGERweb features, one "
            "dissolved into a neighbor — WATCH.md tracks the reconciliation) "
            "pre-built by ia/scripts/build_ia_school_districts.py."
        ),
    },
    {
        "layer": "school-district-unified",
        "app_file": "ia-school-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CurrentIowaSchoolDistricts/FeatureServer/0",
        "note": (
            "Iowa Dept. of Education's own current district layer — the "
            "name-set witness the builder checks its dissolve against, never "
            "the geometry source."
        ),
    },
]

# Live endpoints the app queries at runtime. Empty in this PR — every layer
# ships pre-built; grown as a later phase adds a live TIGERweb read
# (county-subdivision, municipality, zip-code — the WI/IL pattern).
ENDPOINTS = []

FAIL, WARN, OK = "FAIL", "WARN", "OK"


class Findings(object):
    """Collects (severity, layer, message) rows and tracks the worst seen."""

    def __init__(self):
        self.rows = []

    def add(self, severity, layer, message):
        self.rows.append((severity, layer, message))

    def status(self):
        if any(s == FAIL for s, _, _ in self.rows):
            return "fail"
        if any(s == WARN for s, _, _ in self.rows):
            return "warn"
        return "ok"


def http_get(url, want_json=True, params=None):
    """GET with a sane UA; returns (ok, payload_or_error). Never raises."""
    if requests is None:
        return False, "requests not installed"
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "District Explorer source validator (+https://districtry.com/ia/)"},
        )
    except Exception as e:  # network/TLS/proxy errors are a finding, not a crash
        return False, "request failed: %s" % e
    if resp.status_code >= 400:
        return False, "HTTP %d" % resp.status_code
    # 202 is never a real document. "Accepted" means the request was taken for
    # later processing, and the bot-management fronts in front of several
    # government sites use it for their interstitial. Treat it as unreachable
    # and say why, so the two signals agree.
    if resp.status_code == 202:
        return False, "HTTP 202 — bot-management interstitial, not the document"
    if not want_json:
        return True, resp
    try:
        return True, resp.json()
    except ValueError as e:
        return False, "non-JSON response: %s" % e


# ---- check 1: the manifest still matches what index.html actually uses -------
def check_manifest_matches_app(html, findings):
    for d in SOCRATA:
        if d["id"] not in html:
            findings.add(FAIL, d["layer"],
                         "dataset id %s not found in index.html — manifest is "
                         "out of sync with the app (update ia/scripts/validate_sources.py)"
                         % d["id"])
    for p in PROVENANCE:
        # A file the app addresses by a slug built at RUNTIME has no literal to
        # find — the same `dynamic_reference` exemption validate_index.py
        # grants. The entry names the suffix instead, and the drift check
        # looks for THAT: a card that stopped fetching the family at all
        # still fails here. (No such entries yet in this instance.)
        needle = p.get("app_file_pattern") or ("data/app/" + p["app_file"])
        if needle not in html:
            findings.add(FAIL, p["layer"],
                         "index.html no longer references %s — manifest drift"
                         % needle)


# ---- check 2: Socrata datasets resolve, keep their name, aren't superseded ---
def newest_edition(cfg):
    """Search the portal catalog for the newest edition matching cfg.

    Returns (id, name, year_int) for the highest `pattern` capture, or None if
    the search is unavailable / finds nothing usable.
    """
    ys = cfg["year_search"]
    ok, payload = http_get(CATALOG_API, params={
        "domains": SOCRATA_DOMAIN,
        "q": ys["query"],
        "only": "dataset,map,geospatial",
        "limit": 200,
    })
    if not ok or not isinstance(payload, dict):
        return None
    rx = re.compile(ys["pattern"])
    best = None
    for r in payload.get("results", []):
        res = r.get("resource", {})
        name = res.get("name", "")
        if cfg["name_contains"] not in name:
            continue
        m = rx.search(name)
        if not m:
            continue
        year = int(m.group(1))
        if best is None or year > best[2]:
            best = (res.get("id"), name, year)
    return best


def check_socrata(findings, offline):
    for cfg in SOCRATA:
        layer = cfg["layer"]
        if offline:
            continue
        ok, meta = http_get("https://%s/api/views/%s.json" % (SOCRATA_DOMAIN, cfg["id"]))
        if not ok:
            findings.add(FAIL, layer,
                         "dataset %s does not resolve on the portal (%s) — likely "
                         "retired or replaced" % (cfg["id"], meta))
            continue
        name = meta.get("name", "") if isinstance(meta, dict) else ""
        if cfg["name_contains"] not in name:
            findings.add(FAIL, layer,
                         "dataset %s is now named %r — expected it to contain %r; "
                         "the id may have been repurposed"
                         % (cfg["id"], name, cfg["name_contains"]))
            continue

        if "year_search" not in cfg:
            findings.add(OK, layer, "%s — %r" % (cfg["id"], name))
            continue

        # year-versioned: is a newer edition published?
        cur = re.search(cfg["year_search"]["pattern"], name)
        cur_year = int(cur.group(1)) if cur else None
        newest = newest_edition(cfg)
        if newest is None or cur_year is None:
            findings.add(OK, layer,
                         "%s — %r (newer-edition search unavailable)" % (cfg["id"], name))
        elif newest[2] > cur_year and newest[0] != cfg["id"]:
            findings.add(WARN, layer,
                         "in use: %s (%r). NEWER edition on the portal: %s (%r). "
                         "Review the newer dataset's schema, then update the id in index.html."
                         % (cfg["id"], name, newest[0], newest[1]))
        else:
            findings.add(OK, layer, "%s — %r (newest edition)" % (cfg["id"], name))


# ---- check 3: shapefile provenance reachable, built file present ------------
def check_provenance(findings, offline):
    for p in PROVENANCE:
        layer = p["layer"]
        fpath = os.path.join(APP_DATA_DIR, p["app_file"])
        if not os.path.exists(fpath):
            findings.add(FAIL, layer, "built data file data/app/%s is missing" % p["app_file"])
        if offline:
            continue
        ok, res = http_get(p["source_url"], want_json=False)
        blocked = p.get("blocked")
        if ok and blocked:
            # The block LIFTING is the news — see il/scripts/validate_sources.py
            # for the fuller rationale (the fleet-wide `blocked` inversion).
            findings.add(WARN, layer,
                         "source is REACHABLE again (%s) — its recorded block appears to "
                         "have LIFTED. Re-test the scraper; if it works, drop the "
                         "`blocked` flag on this entry so a future outage warns again. "
                         "Recorded block: %s" % (p["source_url"], blocked))
        elif ok:
            findings.add(OK, layer, "source reachable: %s — %s" % (p["source_url"], p["note"]))
        elif blocked:
            findings.add(OK, layer,
                         "unreachable AS EXPECTED (%s) — %s. %s"
                         % (res, blocked, p["source_url"]))
        else:
            findings.add(WARN, layer,
                         "source not reachable (%s): %s. Boundaries change ~once a "
                         "decade; verify the source still exists and re-download if redrawn. %s"
                         % (res, p["source_url"], p["note"]))


# ---- check 4: live endpoints reachable --------------------------------------
def check_endpoints(findings, offline):
    if offline:
        return
    for e in ENDPOINTS:
        ok, res = http_get(e["url"], want_json=False)
        if ok:
            findings.add(OK, e["layer"], "endpoint reachable")
        else:
            findings.add(WARN, e["layer"],
                         "endpoint not reachable (%s): %s — the service may have been "
                         "renamed or retired" % (res, e["url"]))


def render(findings):
    order = {FAIL: 0, WARN: 1, OK: 2}
    rows = sorted(findings.rows, key=lambda r: (order[r[0]], r[1]))
    n_fail = sum(1 for s, _, _ in rows if s == FAIL)
    n_warn = sum(1 for s, _, _ in rows if s == WARN)
    n_ok = sum(1 for s, _, _ in rows if s == OK)
    lines = []
    lines.append("# Layer source validation")
    lines.append("")
    lines.append("**%d FAIL · %d WARN · %d OK**" % (n_fail, n_warn, n_ok))
    lines.append("")
    if n_fail or n_warn:
        lines.append("Sources below need a human look. Nothing is auto-changed — "
                     "review, then update `index.html` (dataset ids) or re-download the "
                     "boundary shapefile as needed.")
        lines.append("")
    for sev in (FAIL, WARN, OK):
        group = [r for r in rows if r[0] == sev]
        if not group:
            continue
        lines.append("## %s (%d)" % (sev, len(group)))
        for _, layer, msg in group:
            lines.append("- **%s** — %s" % (layer, msg))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Validate the app's data-layer sources are current.")
    ap.add_argument("--report", metavar="PATH", help="write the markdown report to PATH (also printed to stdout)")
    ap.add_argument("--status-file", metavar="PATH", help="write ok|warn|fail to PATH (for CI)")
    ap.add_argument("--offline", action="store_true", help="run only the manifest↔index.html checks (no network)")
    args = ap.parse_args()

    if not os.path.exists(INDEX_HTML):
        print("validate_sources: FAIL — index.html not found at %s" % INDEX_HTML, file=sys.stderr)
        sys.exit(1)
    html = open(INDEX_HTML).read()

    if not args.offline and requests is None:
        print("validate_sources: requests not installed; run with --offline or "
              "`pip install -c ia/scripts/requirements.txt requests`", file=sys.stderr)
        sys.exit(1)

    findings = Findings()
    check_manifest_matches_app(html, findings)
    check_socrata(findings, args.offline)
    check_provenance(findings, args.offline)
    check_endpoints(findings, args.offline)

    report = render(findings)
    sys.stdout.write(report)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)

    status = findings.status()
    if args.status_file:
        with open(args.status_file, "w") as f:
            f.write(status)

    sys.exit(1 if status == "fail" else 0)


if __name__ == "__main__":
    main()

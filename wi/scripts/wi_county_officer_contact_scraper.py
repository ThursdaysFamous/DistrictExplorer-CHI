#!/usr/bin/env python3
"""
Scrape county officer CONTACT and name-currency from each county's OWN
pages — phase 4 PR 2, tranche 1 (docs/WI_PHASE4_PLAN.md).

The officer rows ship dated to the Blue Book because no STATEWIDE second
publisher measures open. That is a fact about aggregators, not about the
72 counties: a county's own sheriff/DA/treasurer pages are both the only
source of office contact and a fresher NAME witness than an April
snapshot. This scraper reads the counties measured open (2026-08-26),
each page PINNED, and writes an intermediate the officers builder merges:

  * "pages" mode — one pinned URL per office. The page must WITNESS the
    shipped officer: the surname as a WHOLE WORD with a word matching the
    first name's initial nearby. Substring matching is not enough —
    measured: "Jennifer Grant" matches inside Waukesha's "Community
    Block Grant" nav link, which is why the initial requirement exists.
    Contact (phone, e-mail) is taken only from a window around the name,
    never from the page at large — a department page carries many phones
    and shipping the wrong one is worse than shipping none.
  * "civicplus" mode — the platform's one-page staff directory
    (directory.aspx), parsed STRUCTURALLY: each entry is a list item with
    the person's name and exact title(s). Titles are comma-split, the
    "<County> County " prefix stripped, and matched EXACTLY against a
    per-office allow-set, so "Chief Deputy Sheriff" and "Jail Captain"
    can never match "Sheriff". These directories publish NO phone or
    e-mail in the listing (measured — the employee detail pages are
    account-gated), so this mode yields a name check and a link, and the
    extracted name lets the builder detect DIVERGENCE mechanically.
  * Waukesha's executive is a pinned SUPERSEDE: the county's own page
    says County Executive Paul Farrow — the Blue Book's row — died in
    office, and Interim County Executive Tom Farley was sworn in
    2026-07-30. The extraction reads the interim's name from that page;
    the builder refuses to ship the book's name for this county even
    when this scrape fails (STALE_EXEC there).

MEASURED REFUSALS AND MISSES (tranche 3 work, not silently skipped):
county.milwaukee.gov and racinecounty.gov answer 403 to this client
(their board rosters ship from their GIS layers for the same reason).
BAYFIELD's CivicPlus pages render as ~1KB JS shells to a non-JS client,
it has no /Directory staff list, and its directory.aspx carries no staff
rows. VILAS publishes department pages that name no officer (3-7KB
stubs). DANE's medical-examiner and clerk-of-courts subdomains do not
resolve from this network (proxy 502), and its treasurer subdomain is a
payment portal naming nobody. DUNN's administration page does not name
the county manager, dunncountysheriff.com is a JS shell, and its
DA/deeds/examiner pages 404 at every conventional path — so Dunn ships
its two witnessed offices only. JEFFERSON's own homepage links no
sheriff page and the conventional path 404s. GRANT publishes no
coroner/medical-examiner page at either conventional path. MARQUETTE's
DA page is a 1KB shell and its treasurer page is unlocated (finance
sits under administration). VERNON's DA page is a 2KB stub naming no
one and its clerk-of-courts page 404s (both spellings). WASHBURN's
clerk-of-courts page 404s (both spellings). WAUSHARA publishes a County
Clerk page but no clerk-of-courts page. Waukesha's medical-examiner
page deliberately names no person. A county below its pinned floor is
SKIPPED with a loud line, never shipped partial-silent.
"""

import json
import os
import re
import sys
import time
import html as htmllib
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT = os.path.join(SCRIPT_DIR, ".cache", "wi_county_officer_contacts_raw.json")
COUNTIES_FILE = os.path.join(REPO_ROOT, "data", "app", "state-counties.json")
OFFICERS = os.path.join(REPO_ROOT, "data", "app", "wi-county-officers.json")

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml"}

OFFICE_KEYS = ["sheriff", "districtAttorney", "treasurer",
               "clerkOfCircuitCourt", "registerOfDeeds", "coroner",
               "executive"]

# civicplus title allow-sets: a comma-split title segment, with the
# "<County> County " prefix stripped, must EQUAL one of these — deputies,
# chief deputies and jail staff can never match.
TITLE_SETS = {
    "sheriff": {"Sheriff"},
    "districtAttorney": {"District Attorney"},
    "treasurer": {"Treasurer", "County Treasurer"},
    "clerkOfCircuitCourt": {"Clerk of Courts", "Clerk of Court",
                            "Clerk of Circuit Court"},
    "registerOfDeeds": {"Register of Deeds"},
    "coroner": {"Coroner", "County Coroner", "Medical Examiner",
                "Chief Medical Examiner"},
    "executive": {"County Executive", "Interim County Executive",
                  "County Administrator", "Administrative Coordinator",
                  "County Manager"},
}

COUNTIES = {
    "Brown": {"mode": "pages", "floor": 6, "offices": {
        "sheriff": "https://www.browncountywi.gov/government/sheriffs-office/",
        "districtAttorney": "https://www.browncountywi.gov/government/district-attorney/",
        "treasurer": "https://www.browncountywi.gov/departments/treasurer/general-information/",
        "clerkOfCircuitCourt": "https://www.browncountywi.gov/departments/clerk-of-circuit-court/general-information/",
        "registerOfDeeds": "https://www.browncountywi.gov/departments/register-of-deeds/general-information/",
        "coroner": "https://www.browncountywi.gov/departments/medical-examiner/",
        "executive": "https://www.browncountywi.gov/government/county-executive/"}},
    "Washington": {"mode": "pages", "floor": 6, "offices": {
        "executive": "https://www.washcowisco.gov/departments/county_executive",
        "districtAttorney": "https://www.washcowisco.gov/departments/district_attorney",
        "treasurer": "https://www.washcowisco.gov/departments/county_treasurer",
        "registerOfDeeds": "https://www.washcowisco.gov/departments/register_of_deeds",
        "coroner": "https://www.washcowisco.gov/departments/medical_examiner",
        "clerkOfCircuitCourt": "https://www.washcowisco.gov/departments/clerk_of_circuit_court",
        "sheriff": "https://www.washcowisco.gov/elected_officials/sheriff_s_office"}},
    "Eau Claire": {"mode": "pages", "floor": 4, "offices": {
        "sheriff": "https://eauclairecounty.gov/departments/sheriff/index.php",
        "districtAttorney": "https://eauclairecounty.gov/departments/district_attorney/index.php",
        "clerkOfCircuitCourt": "https://eauclairecounty.gov/departments/clerk_of_courts/index.php",
        "treasurer": "https://eauclairecounty.gov/departments/treasurer/index.php",
        "registerOfDeeds": "https://eauclairecounty.gov/departments/register_of_deeds/index.php"}},
    # woodcountywi.gov resets connections intermittently — the fetch
    # retries carry it; its paths ABBREVIATE (DA, ROD, Courts), which is
    # why the conventional guesses 404'd in tranche 1
    "Wood": {"mode": "pages", "floor": 4, "offices": {
        "sheriff": "https://woodcountywi.gov/Departments/Sheriff/",
        "treasurer": "https://woodcountywi.gov/Departments/Treasurer/",
        "coroner": "https://woodcountywi.gov/Departments/Coroner/",
        "clerkOfCircuitCourt": "https://woodcountywi.gov/Departments/Courts/",
        "registerOfDeeds": "https://woodcountywi.gov/Departments/ROD/"}},
    # Dane publishes per-office SUBDOMAINS, not paths
    "Dane": {"mode": "pages", "floor": 3, "offices": {
        "sheriff": "https://danesheriff.com/",
        "executive": "https://exec.danecounty.gov/",
        "districtAttorney": "https://da.danecounty.gov/",
        "registerOfDeeds": "https://rod.danecounty.gov/"}},
    "Waukesha": {"mode": "pages", "floor": 3, "offices": {
        "districtAttorney": "https://www.waukeshacounty.gov/district-attorney/",
        "treasurer": "https://www.waukeshacounty.gov/treasurer/",
        "registerOfDeeds": "https://www.waukeshacounty.gov/register-of-deeds/",
        "sheriff": "https://www.waukeshacounty.gov/sheriff/"},
        "interim_exec": "https://www.waukeshacounty.gov/county-executive/"},
    "Grant": {"mode": "pages", "floor": 5, "offices": {
        "sheriff": "https://www.co.grant.wi.gov/grant-county-sheriffs-office/",
        "districtAttorney": "https://www.co.grant.wi.gov/district-attorney/",
        "treasurer": "https://www.co.grant.wi.gov/county-treasurer/",
        "clerkOfCircuitCourt": "https://www.co.grant.wi.gov/clerk-of-court/",
        "registerOfDeeds": "https://www.co.grant.wi.gov/register-of-deeds/",
        "executive": "https://www.co.grant.wi.gov/county-administrator/"}},
    "Jefferson": {"mode": "pages", "floor": 5, "offices": {
        "executive": "https://www.jeffersoncountywi.gov/administration/index.php",
        "treasurer": "https://www.jeffersoncountywi.gov/county_treasurer/index.php",
        "clerkOfCircuitCourt": "https://www.jeffersoncountywi.gov/courts___legal_services/clerk_of_courts/index.php",
        "districtAttorney": "https://www.jeffersoncountywi.gov/courts___legal_services/district_attorney/index.php",
        "coroner": "https://www.jeffersoncountywi.gov/medical_examiner/index.php",
        "registerOfDeeds": "https://www.jeffersoncountywi.gov/register_of_deeds/index.php"}},
    "Marquette": {"mode": "pages", "floor": 4, "offices": {
        "executive": "https://www.marquettecountywi.gov/administration/",
        "clerkOfCircuitCourt": "https://www.marquettecountywi.gov/clerk-of-courts/",
        "coroner": "https://www.marquettecountywi.gov/medical-examiner/",
        "sheriff": "https://www.marquettecountywi.gov/sheriff/",
        "registerOfDeeds": "https://www.marquettecountywi.gov/register-of-deeds/"}},
    "Polk": {"mode": "pages", "floor": 4, "offices": {
        "sheriff": "https://www.polkcountywi.gov/government/elected_officials/sheriff/index.php",
        "clerkOfCircuitCourt": "https://www.polkcountywi.gov/government/elected_officials/clerk_of_courts/index.php",
        "registerOfDeeds": "https://www.polkcountywi.gov/government/elected_officials/register_of_deeds/index.php",
        "districtAttorney": "https://www.polkcountywi.gov/government/divisions_and_departments/public_safety_public_works/district_attorney/index.php",
        "treasurer": "https://www.polkcountywi.gov/government/elected_officials/treasurer/index.php"}},
    "Vernon": {"mode": "pages", "floor": 3, "offices": {
        "coroner": "https://www.vernoncountywi.gov/departments/county_coroner/index.php",
        "treasurer": "https://www.vernoncountywi.gov/departments/county_treasurer/index.php",
        "registerOfDeeds": "https://www.vernoncountywi.gov/departments/register_of_deeds/index.php",
        "sheriff": "https://www.vernoncountywi.gov/departments/sheriff_s_office/index.php"}},
    "Washburn": {"mode": "pages", "floor": 4, "offices": {
        "executive": "https://co.washburn.wi.us/departments/administration-personnel/",
        "treasurer": "https://co.washburn.wi.us/departments/county-treasurer/",
        "districtAttorney": "https://co.washburn.wi.us/departments/district-attorney/",
        "registerOfDeeds": "https://co.washburn.wi.us/departments/register-of-deeds/",
        "sheriff": "https://www.washburnsheriff.org/"}},
    "Waushara": {"mode": "pages", "floor": 5, "offices": {
        "districtAttorney": "https://www.wausharacountywi.gov/12718/district-attorney",
        "registerOfDeeds": "https://www.wausharacountywi.gov/12726/register-of-deeds",
        "sheriff": "https://www.wausharacountywi.gov/12727/sheriffs-office",
        "treasurer": "https://www.wausharacountywi.gov/12730/treasurer",
        "coroner": "https://www.wausharacountywi.gov/41436/medical-examiner",
        "executive": "https://www.wausharacountywi.gov/12681/administration"}},
    # Dunn ships THIN on purpose: only two of its surfaces name their
    # officer to a non-JS client (the docstring carries the rest)
    "Dunn": {"mode": "pages", "floor": 2, "offices": {
        "clerkOfCircuitCourt": "https://dunncountywi.gov/clerkofcourts",
        "treasurer": "https://dunncountywi.gov/treasurer"}},
    "Winnebago": {"mode": "civicplus", "floor": 5,
                  "url": "https://www.winnebagocountywi.gov/directory.aspx"},
    "Burnett": {"mode": "civicplus", "floor": 5,
                "url": "https://burnettcountywi.gov/directory.aspx"},
    "Green": {"mode": "civicplus", "floor": 5,
              "url": "https://greencountywi.org/directory.aspx"},
    "Walworth": {"mode": "civicplus", "floor": 5,
                 "url": "https://co.walworth.wi.us/directory.aspx"},
    "Portage": {"mode": "civicplus", "floor": 5,
                "url": "https://www.co.portage.wi.gov/Directory"},
}

TAG_STRIP = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>")
PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "dr"}


def fetch(url, tries=3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=30).read().decode(
                "utf-8", "replace")
        except Exception as exc:  # noqa: BLE001 — retried, then surfaced
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("%s: %s" % (url, last))


def to_text(raw):
    return re.sub(r"\s+", " ", htmllib.unescape(TAG_STRIP.sub(" ", raw)))


def name_parts(name):
    parts = [p for p in re.sub(r"[^A-Za-z ]", " ", name or "").split()
             if p.lower() not in SUFFIXES]
    if not parts:
        return None, None
    return parts[0], parts[-1]


def witness_window(text, book_name, span=350):
    """Find the shipped officer on the page: the surname as a whole word,
    with a capitalized word sharing the first name's initial nearby.
    Returns the text window around the accepted hit, or None."""
    first, sur = name_parts(book_name)
    if not sur:
        return None
    for m in re.finditer(r"\b%s\b" % re.escape(sur), text, re.I):
        lo, hi = max(0, m.start() - 120), m.start() + 120
        near = text[lo:hi]
        if re.search(r"\b%s[a-z]" % re.escape(first[0]), near):
            lo2, hi2 = max(0, m.start() - span), m.start() + span
            return text[lo2:hi2]
    return None


def scrape_pages(county, cfg, book):
    out = {}
    for office, url in cfg["offices"].items():
        book_name = (book.get(office) or {}).get("name")
        if office == "executive":
            book_name = (book.get("executive") or {}).get("name")
        if not book_name:
            continue
        try:
            text = to_text(fetch(url))
        except RuntimeError as exc:
            print("%s/%s: fetch failed — %s" % (county, office, exc),
                  file=sys.stderr)
            continue
        window = witness_window(text, book_name)
        if window is None:
            print("%s/%s: page does not witness %r — no contact ships"
                  % (county, office, book_name), file=sys.stderr)
            continue
        entry = {"url": url}
        phone = PHONE_RE.search(window)
        if phone:
            entry["phone"] = phone.group(0).strip()
        email = EMAIL_RE.search(window)
        if email:
            entry["email"] = email.group(0)
        out[office] = entry
    return out


# Both gaps are BOUNDED: an entry with no title div must fail the match
# (and be skipped) rather than swallow forward and pair this person's name
# with the NEXT person's title — the measured gap is ~50 chars.
CIVICPLUS_ITEM = re.compile(
    r'employee\?eid=\d+">\s*([^<]+?)\s*</a>'
    r'[\s\S]{0,300}?<div class="d-sm-block d-none">([^<]*)</div>')


def scrape_civicplus(county, cfg, book):
    raw = fetch(cfg["url"])
    found = {}
    for name, titles in CIVICPLUS_ITEM.findall(raw):
        name = htmllib.unescape(name).strip()
        # Trailing certification initialisms are not part of a name
        # (measured: Walworth's medical examiner is listed "Kimberly Rossi
        # D-ABMDI"). Strip trailing all-caps tokens only while a mixed-case
        # token remains before them, so an all-caps SURNAME never strips.
        parts = name.split()
        while (len(parts) > 2 and re.fullmatch(r"[A-Z][-A-Z.]{1,9}", parts[-1])
               and not parts[-2].isupper()):
            parts.pop()
        name = " ".join(parts)
        for seg in htmllib.unescape(titles).split(","):
            seg = seg.strip()
            seg = re.sub(r"^%s County " % re.escape(county), "", seg)
            for office, allowed in TITLE_SETS.items():
                if seg in allowed:
                    found.setdefault(office, set()).add(name)
    out = {}
    for office, names in found.items():
        # The same person can be listed twice ("Eric Sparr" / "Eric D.
        # Sparr" — measured on Winnebago), so ambiguity means DISTINCT
        # PEOPLE: group by first-initial + surname and count groups. A
        # genuine multi-person title (Winnebago's directory titles a
        # committee treasurer "Treasurer" beside the county treasurer)
        # stays skipped with the loud line.
        groups = {}
        for n in names:
            first, sur = name_parts(n)
            groups.setdefault((first[0].lower() if first else "",
                               (sur or "").lower()), []).append(n)
        if len(groups) > 1:
            print("%s/%s: directory marks %d distinct people (%s) — "
                  "ambiguous, skipped" % (county, office, len(groups),
                                          sorted(names)), file=sys.stderr)
            continue
        best = max(list(groups.values())[0], key=len)  # fullest form ships
        out[office] = {"url": cfg["url"], "name": best}
    return out


INTERIM_EXEC_RE = re.compile(
    r"About\s+([A-Z][\w'.-]+(?:\s+[A-Z][\w'.-]+){1,2}?)\s+Interim\s+"
    r"(?:Waukesha\s+)?County\s+Executive")


def scrape_interim_exec(county, url):
    text = to_text(fetch(url))
    m = INTERIM_EXEC_RE.search(text)
    if not m:
        print("%s/executive: interim-executive extraction failed — the page "
              "reshaped; the builder will withhold rather than ship the "
              "book's deceased executive" % county, file=sys.stderr)
        return None
    entry = {"url": url,
             "supersede": {"name": m.group(1),
                           "title": "Interim County Executive",
                           "appointed": True}}
    window = witness_window(text, m.group(1))
    if window:
        phone = PHONE_RE.search(window)
        if phone:
            entry["phone"] = phone.group(0).strip()
    return entry


def main():
    feats = json.load(open(COUNTIES_FILE))["features"]
    geoid_by_base = {f["properties"]["BASENAME"]: f["properties"]["GEOID"]
                     for f in feats}
    officers = json.load(open(OFFICERS))
    book_by_base = {v["county"]: v for v in officers.values()}

    out = {}
    for county, cfg in COUNTIES.items():
        book = book_by_base[county]
        try:
            if cfg["mode"] == "pages":
                entries = scrape_pages(county, cfg, book)
                if cfg.get("interim_exec"):
                    exec_entry = scrape_interim_exec(county, cfg["interim_exec"])
                    if exec_entry:
                        entries["executive"] = exec_entry
            else:
                entries = scrape_civicplus(county, cfg, book)
        except RuntimeError as exc:
            print("%s: SKIPPED — %s" % (county, exc), file=sys.stderr)
            continue
        if len(entries) < cfg["floor"]:
            print("%s: SKIPPED — %d offices resolved, floor %d (a page "
                  "reshaped; re-read it, never loosen the floor)"
                  % (county, len(entries), cfg["floor"]), file=sys.stderr)
            continue
        out[str(geoid_by_base[county])] = {"county": county,
                                           "offices": entries}
        print("%s: %d offices (%s)" % (county, len(entries),
                                       ", ".join(sorted(entries))),
              file=sys.stderr)
        time.sleep(1)

    if len(out) < 14:
        raise SystemExit("only %d counties resolved — the tranche floor is "
                         "14; something structural broke" % len(out))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote %s — %d counties" % (OUT, len(out)), file=sys.stderr)


if __name__ == "__main__":
    main()

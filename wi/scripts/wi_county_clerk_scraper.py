#!/usr/bin/env python3
"""
Scrape Wisconsin's 72 county clerks from the two publishers that answer where
the state's own election agency does not. Stage 1 of the pair;
build_wi_county_clerk_roster.py turns the intermediate into
data/app/wi-county-clerks.json.

WHY NOT WEC: elections.wi.gov and myvote.wi.gov sit behind a Cloudflare
managed challenge (HTTP 403, Cf-Mitigated: challenge, measured 2026-08-25 on
every path including file downloads and API routes). A challenge is an access
control and is not defeated here. Two open sources cover the concept instead,
and CROSS-GATE each other:

  1. The Wisconsin Blue Book 2025-26 "Wisconsin county officers: county
     clerks, April 2025" table (docs.legis.wisconsin.gov, a state
     publication): all 72 clerks with a PARTY-OR-APPOINTED code — the page's
     own legend reads "A-Appointed; D-Democrat; I-Independent; R-Republican" —
     and the county website. TWO EXTRACTION TRAPS, both measured: the table
     STARTS mid-page beneath the circuit-judges footnotes (a header-scoped
     read finds only the continuation page), and the website column prints
     its dots as word gaps under pdfplumber ("www co brown wi us"), so the
     URL is re-joined on dots and verified to look like a hostname.
  2. wisconsincountyclerks.org — the clerks' own association, one page per
     county (72 verified) with the clerk's name, office address, hours,
     phone, fax, e-mail and county website. Its 403 is a plain UA rule (no
     cf-mitigated header), so browser headers suffice; robots.txt allows all
     with Crawl-delay 10, which this scraper HONORS — the 72-page crawl takes
     ~12 minutes and that is the cost of being a polite client.

THE CROSS-GATE: the two sources must name the same person per county
(case/punctuation-folded). Where they diverge, the ASSOCIATION'S name ships —
the Blue Book is an April 2025 snapshot and an appointed replacement
post-dates it — and the divergence is recorded in the intermediate so the
builder can print it. The Blue Book's party code rides only a matching name:
a divergent county ships without party rather than pinning the predecessor's
party on the successor.

County names key to FIPS through the shipped county file
(data/app/state-counties.json), so the roster's keys cannot drift from the
geometry the card queries.
"""

import html as html_mod
import json
import os
import re
import ssl
import sys
import time
import urllib.request

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_OUT = os.path.join(SCRIPT_DIR, ".cache", "wi_county_clerks_raw.json")
COUNTIES_FILE = os.path.join(REPO_ROOT, "data", "app", "state-counties.json")

BLUE_BOOK_URL = ("https://docs.legis.wisconsin.gov/misc/lrb/blue_book/"
                 "2025_2026/210_officials_and_employees.pdf")
WCCA_INDEX = "https://wisconsincountyclerks.org/wisconsin-counties/"
CRAWL_DELAY_S = 10  # robots.txt Crawl-delay — honored, never shortened

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
}
PARTY = {"D": "Democrat", "R": "Republican", "I": "Independent", "A": "Appointed"}


def fetch(url, binary=False):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def county_names():
    with open(COUNTIES_FILE) as f:
        feats = json.load(f)["features"]
    return {feat["properties"]["BASENAME"]: feat["properties"]["GEOID"] for feat in feats}


def fold_name(name):
    return "".join(ch for ch in name.lower() if ch.isalpha())


def person_key(name):
    """First + last token: the Blue Book prints 'Heather Schutte' where the
    association prints 'Heather W. Schutte' — the same clerk, styled apart —
    so a middle initial never reads as a succession and never costs the party
    code. A different FIRST name still diverges ('Elizabeth' vs a successor's
    'Samantha'), which is the distinction that matters; a nickname ('Liz',
    'Chris') also diverges and the party is withheld there too, which errs
    toward silence rather than a guess."""
    toks = [t for t in re.split(r"[^a-z]+", str(name).lower()) if len(t) > 1]
    if not toks:
        return ""
    return toks[0] + "|" + toks[-1]


def parse_blue_book(pdf_path, names):
    """-> {BASENAME: {'name':…, 'code':…, 'website':…}} — all 72 gated."""
    if pdfplumber is None:
        raise SystemExit("pdfplumber is required (wi/scripts/requirements.txt pins it)")
    # counties longest-first so "Green Lake" wins before "Green"; the PDF
    # drops periods everywhere, so "St. Croix" is matched as "St Croix" too
    prefixes = []
    for base in names:
        prefixes.append((base, base))
        stripped = base.replace(".", "")
        if stripped != base:
            prefixes.append((stripped, base))
    prefixes.sort(key=lambda p: len(p[0]), reverse=True)
    out = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "county clerks" not in text.lower():
                continue
            for line in text.split("\n"):
                line = line.strip()
                hit = next((p for p in prefixes if line.startswith(p[0] + " ")), None)
                if hit is None or hit[1] in out:
                    continue
                rest = line[len(hit[0]):].strip()
                # "\s*" before the paren: Price prints "Hueckman(R)" with no
                # gap; the site column mixes bare "www …" and "https://…" rows
                m = re.match(r"^(?P<name>.+?)\s*\((?P<code>[ADIR])\)\s+(?P<site>\S.*)$", rest)
                if not m:
                    continue
                site = ".".join(m.group("site").split())
                host = re.sub(r"^https?://", "", site)
                if not re.match(r"^[a-z0-9\-]+(\.[a-z0-9\-]+)+$", host):
                    raise SystemExit("Blue Book website re-join produced a non-hostname: %r" % site)
                out[hit[1]] = {"name": m.group("name").strip(),
                               "code": m.group("code"),
                               "website": site if site.startswith("http") else "https://" + site}
    if len(out) != len(names):
        missing = sorted(set(names) - set(out))
        raise SystemExit("Blue Book table parsed %d of %d counties (missing: %s) — "
                         "the two-column layout or the mid-page start moved"
                         % (len(out), len(names), missing[:6]))
    return out


def parse_wcca_page(html):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = html_mod.unescape(text)  # the pages entity-encode their en-dashes
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.split("\n") if l.strip()]
    # the content block starts at the county heading that follows the nav's
    # "Counties" item; the clerk's name is the next line
    idx = None
    for i in range(1, len(lines)):
        if lines[i - 1] == "Counties" and lines[i].endswith(" County"):
            idx = i
            break
    if idx is None:
        return None
    entry = {"address": [], "hours": None, "phone": None, "fax": None,
             "email": None, "website": None}
    entry["name"] = lines[idx + 1]
    i = idx + 2
    while i < len(lines) and not lines[i].startswith(("Hours", "Phone", "Fax", "Email", "Website")):
        entry["address"].append(lines[i])
        i += 1
    while i < len(lines) - 1:
        label = lines[i].rstrip(":")
        value = lines[i + 1]
        if label == "Hours":
            entry["hours"] = value if not value.startswith(("Phone", "Fax")) else None
        elif label == "Phone":
            entry["phone"] = value
        elif label == "Fax":
            entry["fax"] = value
        elif label == "Email":
            entry["email"] = value if "@" in value else None
        elif label == "Website":
            entry["website"] = value if value.startswith("http") or "." in value else None
            break
        i += 1
    return entry


def crawl_wcca(cache_dir):
    index = fetch(WCCA_INDEX)
    links = sorted(set(re.findall(
        r'href="(https?://wisconsincountyclerks\.org/counties/[^"]+)"', index)))
    if len(links) != 72:
        raise SystemExit("association index lists %d county pages, expected 72" % len(links))
    pages = {}
    for url in links:
        slug = url.rstrip("/").split("/")[-1]
        cached = os.path.join(cache_dir, slug + ".html") if cache_dir else None
        if cached and os.path.exists(cached) and os.path.getsize(cached) > 10000:
            html = open(cached, encoding="utf-8", errors="replace").read()
        else:
            html = fetch(url)
            if cached:
                open(cached, "w", encoding="utf-8").write(html)
            time.sleep(CRAWL_DELAY_S)
        entry = parse_wcca_page(html)
        if entry is None or not entry.get("name"):
            raise SystemExit("association page %s did not parse — the page shape moved" % url)
        county = slug.replace("-county", "").replace("-", " ").title()
        entry["sourceUrl"] = url
        pages[county] = entry
    return pages


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT
    cache_dir = argv[argv.index("--cache-dir") + 1] if "--cache-dir" in argv else None

    names = county_names()
    if len(names) != 72:
        raise SystemExit("county file carries %d counties" % len(names))

    pdf_path = os.path.join(os.path.dirname(out_path), "bluebook_210.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 100000:
        open(pdf_path, "wb").write(fetch(BLUE_BOOK_URL, binary=True))
    blue = parse_blue_book(pdf_path, names)

    wcca = crawl_wcca(cache_dir)
    # association slugs title-case differently for multiword counties —
    # fold-match onto BASENAME; the association writes "Saint Croix" where
    # the census abbreviates "St. Croix", so the expanded form aliases in
    by_fold = {fold_name(b): b for b in names}
    for b in names:
        if b.startswith("St."):
            by_fold[fold_name(b.replace("St.", "Saint"))] = b
    wcca_by_base = {}
    for county, entry in wcca.items():
        base = by_fold.get(fold_name(county))
        if base is None:
            raise SystemExit("association page county %r matches no census county" % county)
        wcca_by_base[base] = entry
    missing = sorted(set(names) - set(wcca_by_base))
    if missing:
        raise SystemExit("association pages missing counties: %s" % missing)

    counties = {}
    divergences = []
    for base, geoid in names.items():
        bb, assoc = blue[base], wcca_by_base[base]
        agree = person_key(bb["name"]) == person_key(assoc["name"])
        if not agree:
            divergences.append({"county": base, "blueBook": bb["name"],
                                "association": assoc["name"]})
        counties[geoid] = {
            "county": base,
            "name": assoc["name"],          # the association is the current name
            "code": bb["code"] if agree else None,  # party never rides a divergent name
            "website": assoc.get("website") or bb["website"],
            "address": assoc["address"],
            "hours": assoc.get("hours"),
            "phone": assoc.get("phone"),
            "fax": assoc.get("fax"),
            "email": assoc.get("email"),
            "sourceUrl": assoc["sourceUrl"],
        }

    with open(out_path, "w") as f:
        json.dump({"counties": counties, "divergences": divergences}, f,
                  indent=2, ensure_ascii=False)
    print("scraped 72 county clerks (%d name divergences: %s) -> %s"
          % (len(divergences), [d["county"] for d in divergences] or "none", out_path))


if __name__ == "__main__":
    main()

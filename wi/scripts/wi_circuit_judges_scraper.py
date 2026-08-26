#!/usr/bin/env python3
"""
Scrape Wisconsin's circuit-court bench from wicourts.gov. Stage 1 of the pair;
build_wi_circuit_court_roster.py turns the intermediate JSON into
data/app/wi-circuit-judges.json.

TWO PAGES, TWO ROLES (both answered plain curl HTTP 200 on every probe —
wicourts.gov runs no challenge, no WAF, nothing to route around):

  * /courts/circuit/judges.htm — the AUTHORITATIVE bench: a 72-row
    county-keyed table (County | Name | Court website), footer-dated and
    actively maintained (2026-08-24 at research time). This is also this
    layer's REDISTRICTING TRIPWIRE: the county set and the combined-circuit
    pattern are asserted against Wis. Stat. 753.06's table on every run, so a
    statutory change to the circuit map fails the scrape loudly instead of
    shipping stale composition.
  * /contact/Circuit_Courts.html — the ENRICHMENT: per-county blocks (an
    <a id="<County> County"> heading, p.address courthouse blocks, and
    group_contact_table rows) carrying each judge's BRANCH number and direct
    phone, plus the courthouse address. A judge missing here ships name-only —
    fields degrade individually, never invented.

FOUR MEASURED TRAPS, ALL ENCODED (research pass 2026-08-25):

  1. The judges table lists both slash pairs BOTH WAYS ROUND — Buffalo/Pepin
     AND Pepin/Buffalo, Menominee/Shawano AND Shawano/Menominee — so a naive
     row count double-counts two circuits. Rows are canonicalized to the
     statutory circuit key and deduped; the deduped bench must agree.
  2. Florence and Forest appear as two SLASH-LESS rows sharing one judge
     (they are one circuit under 753.06(8)(b)); both rows must name the same
     bench or the run fails.
  3. Judge names arrive in two shapes: the dominant "Lastname, Hon. First M."
     and the occasional "Judge First M. Lastname" — both are normalized to
     display order, and any row that matches neither fails the run rather
     than shipping a garbled name.
  4. "(Chief Judge)" rides some names in the judges table. It is rendered
     exactly as wicourts prints it (a chief judge of the judicial
     administrative district) — a badge, never a guessed office.

NO E-MAIL SHIPS BECAUSE NONE EXISTS: wicourts.gov publishes no judge e-mail
anywhere (measured). Phone and courthouse address are the contact story.
"""

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

DEFAULT_OUT = os.path.join(os.path.dirname(__file__), ".cache", "wi_circuit_judges_raw.json")
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

JUDGES_URL = "https://www.wicourts.gov/courts/circuit/judges.htm"
CONTACT_URL = "https://www.wicourts.gov/contact/Circuit_Courts.html"

# Wis. Stat. 753.06's three two-county circuits — must match
# build_wi_circuit_courts.py's MERGED table exactly (asserted in the builder).
MERGED = {
    frozenset(("Buffalo", "Pepin")): "buffalo-pepin",
    frozenset(("Florence", "Forest")): "florence-forest",
    frozenset(("Menominee", "Shawano")): "menominee-shawano",
}
EXPECT_COUNTIES = 72
EXPECT_CIRCUITS = 69
MIN_JUDGES = 240


def fetch(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def normalize_judge(raw):
    """'Lastname, Hon. First M.(Chief Judge)' / 'Kussel, Jr., Hon. William F.'
    / 'Judge First M. Lastname' -> (display name, role or None)."""
    raw = raw.strip()
    role = None
    m = re.search(r"\(([^)]*Judge[^)]*)\)\s*$", raw)
    if m:
        role = m.group(1).strip()
        raw = raw[: m.start()].strip()
    m = re.match(r"^(?P<last>[^,]+(?:,\s*(?:Jr|Sr|II|III|IV)\.?)?)\s*,\s*Hon\.\s*(?P<first>.+)$", raw)
    if m:
        last = m.group("last").strip()
        first = m.group("first").strip()
        suffix = ""
        sm = re.match(r"^(?P<base>[^,]+),\s*(?P<suf>(?:Jr|Sr|II|III|IV)\.?)$", last)
        if sm:
            last = sm.group("base").strip()
            suffix = " " + sm.group("suf")
        return ("%s %s%s" % (first, last, suffix), role)
    m = re.match(r"^(?:Judge|Hon\.)\s+(?P<name>.+)$", raw)
    if m:
        return (m.group("name").strip(), role)
    # Third measured shape (Waukesha's "Nehls, Anthony C."): comma-inverted
    # with no honorific at all. The column holds only judges, so the flip is
    # unambiguous; anything else still fails loudly.
    m = re.match(r"^(?P<last>[A-Z][A-Za-z.'\- ]+?)(?:,\s*(?P<suf>(?:Jr|Sr|II|III|IV)\.?))?,\s*(?P<first>[A-Z][A-Za-z.'\- ]+)$", raw)
    if m:
        suffix = (" " + m.group("suf")) if m.group("suf") else ""
        return ("%s %s%s" % (m.group("first").strip(), m.group("last").strip(), suffix), role)
    raise SystemExit("judge name matched no recorded shape: %r" % raw)


def parse_judges_table(html):
    """-> {frozenset(counties) or county: {'counties': [...], 'judges':
    [(name, role)], 'clerk_url': str|None}} keyed per RAW row; the caller
    canonicalizes and dedupes."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    out = []
    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        if len(cells) < 2 or "County" in strip_tags(cells[0]) and "Name" in strip_tags(cells[1]):
            continue
        county_raw = strip_tags(cells[0])
        if not county_raw:
            continue
        counties = [c.strip() for c in county_raw.split("/") if c.strip()]
        # Judges arrive one per <li> — read them structurally, never by
        # splitting flattened text (a lookahead split was tried first and
        # cleaved "Bonnett, Hon. Tania M." at the second surname).
        items = re.findall(r"<li[^>]*>(.*?)</li>", cells[1], re.S)
        if not items:  # a row without a list carries a single bare name
            items = [cells[1]]
        judges = [normalize_judge(strip_tags(p)) for p in items if strip_tags(p)]
        url = None
        m = re.search(r'href="([^"]+)"', cells[2]) if len(cells) > 2 else None
        if m:
            url = m.group(1)
        out.append({"counties": counties, "judges": judges, "clerk_url": url})
    return out


def parse_contact_page(html):
    """-> {county: {'addresses': [multi-line str], 'branch_rows':
    [(judge display name, branch or None, phone)]}}. Only the ALL-CAPS
    'X, HON. Y' rows are judges — mixed-case rows are staff and are never
    read (honesty: this file ships judges, not court reporters' phones)."""
    out = {}
    blocks = re.split(r'<a\s+id="([^"]+ County)">', html)
    for i in range(1, len(blocks) - 1, 2):
        county = blocks[i].replace(" County", "").strip()
        body = blocks[i + 1]
        addresses = []
        for m in re.finditer(r'<p class="address">(.*?)</p>', body, re.S):
            lines = [strip_tags(x) for x in re.split(r"<br\s*/?>", m.group(1))]
            lines = [x for x in lines if x]
            if lines:
                addresses.append(lines)
        branch_rows = []
        for m in re.finditer(r"<tr>\s*<td>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>", body):
            label, phone = strip_tags(m.group(1)), strip_tags(m.group(2))
            # Milwaukee (and only Milwaukee, measured) appends a courtroom to
            # the branch — "DAVILA, HON. JACK L. Br 1 Rm 608" — so the tail
            # tolerates an Rm token; a row that still doesn't match is staff.
            jm = re.match(r"^(?P<name>[A-Z][A-Z .,'\-]+),\s*HON\.\s*(?P<first>[A-Z][A-Z .,'\-]*?)(?:\s*-\s*(?P<role>[^-]*Judge[^-]*))?(?:\s+Br\.?\s*(?P<br>\d+))?(?:\s+Rm\.?\s*\S+)?$", label)
            if not jm:
                continue
            last = jm.group("name").title().strip()
            first = jm.group("first").title().strip()
            # Title-casing an all-caps name is display normalization of the
            # source's own styling, not a spelling change; suffixes like JR
            # keep their dot form.
            name = "%s %s" % (first, last)
            branch_rows.append({
                "name": name,
                "branch": jm.group("br"),
                "phone": phone,
                "role": (jm.group("role") or "").strip() or None,
            })
        out[county] = {"addresses": addresses, "branch_rows": branch_rows}
    return out


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT

    judges_html = fetch(JUDGES_URL)
    contact_html = fetch(CONTACT_URL)

    raw_rows = parse_judges_table(judges_html)

    # Canonicalize: combined circuits appear as slash pairs both ways round
    # (dedupe by frozenset) and Florence/Forest as two slash-less rows that
    # must agree.
    circuits = {}
    county_seen = set()
    for row in raw_rows:
        counties = row["counties"]
        key = None
        cset = frozenset(counties)
        if len(counties) > 1:
            key = MERGED.get(cset)
            if key is None:
                raise SystemExit("judges table names an unrecognized combined circuit: %s "
                                 "(a statutory change? re-read Wis. Stat. 753.06)" % counties)
        else:
            for mset, mkey in MERGED.items():
                if counties[0] in mset:
                    key = mkey
            key = key or counties[0].lower().replace(" ", "-").replace(".", "")
        bench = sorted(set(row["judges"]))
        if key in circuits:
            if sorted(set(circuits[key]["judges"])) != bench:
                raise SystemExit("circuit %s listed twice with different benches — "
                                 "the dedupe assumption broke" % key)
            circuits[key]["counties"].update(counties)
            if row["clerk_url"] and not circuits[key]["clerk_url"]:
                circuits[key]["clerk_url"] = row["clerk_url"]
        else:
            circuits[key] = {"counties": set(counties), "judges": row["judges"],
                             "clerk_url": row["clerk_url"]}
        county_seen.update(counties)

    if len(county_seen) != EXPECT_COUNTIES:
        raise SystemExit("judges table covered %d counties, expected %d"
                         % (len(county_seen), EXPECT_COUNTIES))
    if len(circuits) != EXPECT_CIRCUITS:
        raise SystemExit("canonicalized to %d circuits, expected %d"
                         % (len(circuits), EXPECT_CIRCUITS))
    total_judges = sum(len(set(c["judges"])) for c in circuits.values())
    if total_judges < MIN_JUDGES:
        raise SystemExit("only %d judges parsed (floor %d) — the page reshaped?"
                         % (total_judges, MIN_JUDGES))

    contact = parse_contact_page(contact_html)
    missing = county_seen - set(contact)
    if len(contact) < EXPECT_COUNTIES - 2 or len(missing) > 2:
        # The contact page is enrichment: tolerate a straggler block or two
        # (fields degrade name-only), refuse a page that lost its shape.
        raise SystemExit("contact page parsed %d county blocks (missing: %s)"
                         % (len(contact), sorted(missing)))

    payload = {
        "circuits": {k: {"counties": sorted(v["counties"]),
                          "judges": [{"name": n, "role": r} for n, r in v["judges"]],
                          "clerkUrl": v["clerk_url"]}
                      for k, v in circuits.items()},
        "contact": contact,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("scraped %d circuits / %d judges / %d contact blocks -> %s"
          % (len(circuits), total_judges, len(contact), out_path))


if __name__ == "__main__":
    main()

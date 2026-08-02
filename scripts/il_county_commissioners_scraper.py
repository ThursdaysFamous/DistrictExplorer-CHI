#!/usr/bin/env python3
"""
Scrape the boards of Illinois counties that elect them AT LARGE.

Stage 1 of the two-stage pipeline (scripts/build_county_commissioners.py is
stage 2). Seventeen Illinois counties run the COMMISSION form — three
commissioners elected countywide, no districts at all — and some township
counties likewise elect their board at large. Those boards have no geometry
to join, so they do not become `county-board` dispatch entries; their members
ride the COUNTY card instead (docs/EXPANSION_GUIDE.md §1.5), and this file is
that card's roster.

One shared file, keyed by county name normalized exactly the way
data/app/il-county-clerks.json is keyed, so the county card performs one
lookup shape for both. Adding a county here is a SITES entry plus a parser —
no new layer, no new toggle, no new fetch in the app.

Each county's block is deliberately explicit about what its source publishes
and what it does not. Where a county names only a shared office line, that is
what ships: a shared switchboard is honest, an invented per-member number is
not.

FETCH POSTURE: open. Plain server-rendered HTML; browser User-Agent sent
because two of the sites refuse the default one.

Usage:
    python3 il_county_commissioners_scraper.py [output.json]   # default: stdout
"""

import html as html_mod
import json
import re
import sys

import requests

UA = {"User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")}

PHONE_RE = re.compile(r"(\d{3})\D{0,3}(\d{3})\D?(\d{4})")
EXT_RE = re.compile(r"ext\.?\s*(\d+)", re.I)


def clean(fragment):
    return re.sub(r"\s+", " ", html_mod.unescape(
        re.sub(r"(?s)<[^>]+>", " ", fragment or ""))).strip()


def text_lines(page):
    body = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    text = html_mod.unescape(re.sub(r"(?s)<[^>]+>", "\n", body))
    return [l.strip() for l in text.splitlines() if l.strip()]


def normalize_phone(raw, keep_ext=True):
    m = PHONE_RE.search(raw or "")
    if not m:
        return None
    phone = "-".join(m.groups())
    if keep_ext:
        e = EXT_RE.search(raw or "")
        if e:
            phone += " ext. " + e.group(1)
    return phone


def role_of(text):
    """Only roles the source states. 'Chairman/Budget Director' keeps the
    board role and drops the administrative title the card has no use for."""
    t = (text or "").lower()
    if "vice" in t and "chair" in t:
        return "Vice Chairman"
    if "chair" in t:
        return "Chairman"
    if "commissioner" in t:
        return "Commissioner"
    return None


# ---------------------------------------------------------------- Monroe
def parse_monroe(page):
    """Monroe names its three commissioners in a prose sentence, one per line:
    "George E. Green, Commissioner – Chairman". No per-member phone or e-mail
    is published anywhere — only the board office's shared line — so that is
    all that ships."""
    members = []
    for line in text_lines(page):
        m = re.match(r"^([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3})\s*[,–-]\s*"
                     r"(Commissioner\s*[–-]\s*Chairman|Vice\s+Chairman|Commissioner)\s*$", line)
        if not m:
            continue
        role = role_of(m.group(2))
        if role and not any(x["name"] == m.group(1).strip() for x in members):
            members.append({"name": m.group(1).strip(), "role": role})
    office = None
    lines = text_lines(page)
    for i, line in enumerate(lines):
        if re.search(r"Administrative Assistant", line, re.I):
            addr = next((l for l in lines[i:i + 4] if re.search(r"\d+\s+\S+.*,\s*IL\s*\d{5}", l)), None)
            tel = next((l for l in lines[i:i + 8] if PHONE_RE.search(l)), None)
            office = {"label": "Board of Commissioners",
                      "address": addr,
                      "phone": normalize_phone(" ".join(lines[i:i + 8]))}
            break
    return members, office


# -------------------------------------------------------------- Randolph
def parse_randolph(page):
    """Randolph publishes one <p> per commissioner, <br>-separated:
    <strong>NAME</strong> / role / switchboard + that member's own extension /
    a mailto behind the words "Send Message"."""
    members = []
    for para in re.findall(r"(?is)<p[^>]*>(.*?)</p>", page):
        m = re.search(r"(?is)<strong>(.*?)</strong>", para)
        if not m:
            continue
        name = clean(m.group(1))
        if not re.fullmatch(r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3}", name or ""):
            continue
        rest = clean(para[m.end():])
        role = role_of(rest[:120])
        if not role:
            continue
        entry = {"name": name, "role": role}
        phone = normalize_phone(rest)
        if phone:
            entry["phone"] = phone
        email = re.search(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", para)
        if email:
            entry["email"] = email.group(1).lower()
        if not any(x["name"] == name for x in members):
            members.append(entry)
    return members, None


SITES = {
    # normalized county key (see build_county_commissioners.py) -> spec
    "MONROE": {
        "name": "Monroe County",
        "url": "https://monroecountyil.gov/departments/board-of-commissioners/",
        "structure": "Commission form — 3 commissioners elected countywide",
        "expect": 3,
        "parse": parse_monroe,
    },
    "RANDOLPH": {
        "name": "Randolph County",
        "url": "https://randolphcountyil.gov/board-of-commissioners/",
        "structure": "Commission form — 3 commissioners elected countywide",
        "expect": 3,
        "parse": parse_randolph,
    },
}


def main():
    out = {}
    session = requests.Session()
    for key, spec in SITES.items():
        try:
            resp = session.get(spec["url"], headers=UA, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print("county-commissioners: WARN — %s unreadable (%s)" % (key, exc), file=sys.stderr)
            continue
        members, office = spec["parse"](resp.text)
        if len(members) != spec["expect"]:
            print("county-commissioners: WARN — %s parsed %d members, expected %d"
                  % (key, len(members), spec["expect"]), file=sys.stderr)
        out[key] = {
            "county": spec["name"],
            "structure": spec["structure"],
            "sourceUrl": spec["url"],
            "members": members,
        }
        if office:
            out[key]["office"] = office

    if not out:
        print("county-commissioners: FAIL — no county parsed", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({"counties": out}, indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(payload)
        print("county-commissioners: %d counties (%d members) -> %s"
              % (len(out), sum(len(v["members"]) for v in out.values()), sys.argv[1]))
    else:
        print(payload)


if __name__ == "__main__":
    main()

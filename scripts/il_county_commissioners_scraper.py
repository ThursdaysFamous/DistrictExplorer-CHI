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

import datetime
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


# ------------------------------------------------------------------ Pike
def parse_pike(page):
    """Pike prints one <p> per member: "Reta Hoskin (Chairman)   rhoskin@pike…".
    Every member has a county e-mail; the county publishes no per-member phone
    and no board office address, so neither ships.

    AT-LARGE, PROVEN: the county's own certified summary report for the
    2024 General Election names the contest "FOR COUNTY BOARD - AT LARGE",
    counted across all 31 precincts. Not inferred from the page's silence about
    districts — silence is not evidence (see the module header)."""
    members = []
    for para in re.findall(r"(?is)<p[^>]*>(.*?)</p>", page):
        line = clean(para)
        m = re.match(r"^([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3})"
                     r"(?:\s*\((.*?)\))?\s+"
                     r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\s*$", line)
        if not m:
            continue
        entry = {"name": m.group(1).strip(),
                 "role": role_of(m.group(2)) or "Board Member",
                 "email": m.group(3).lower()}
        if not any(x["name"] == entry["name"] for x in members):
            members.append(entry)
    return members, None


# ---------------------------------------------------------------- Putnam
def parse_putnam(page):
    """Putnam lists its five members as <strong><a>Name, Role</a></strong>.

    READ THE TEXT, NOT THE LINK. Every one of those profile hrefs 404s, and TWO
    of them point at `steve_malavolti.php` — a member no longer on the board:
    once for the ", Vice-Chairman" fragment split off Anthony Rue's row, and
    once for Marlee Giacometti's whole row. Keying on the href would name a
    former member twice and lose two sitting ones. The visible text is what the
    county maintains, so the visible text is what is read. (St. Clair is the
    mirror image — there the caption is wrong and the URL right — which is why
    neither surface gets blanket trust.)

    No per-member contact is published; the shared courthouse line ships as the
    board office instead."""
    members = []
    block = re.search(r"(?is)Click on a board member(.*?)(?:<strong>\s*Mailing Address)", page)
    # Rows are <br>-separated, NOT tag-separated: the Vice-Chairman's name and
    # his title sit in two different <a> tags, so splitting on tags puts them on
    # separate lines and loses him. Split on the line break the county actually
    # uses, then strip tags within the row.
    for chunk in re.split(r"(?i)<br\s*/?>", block.group(1) if block else ""):
        line = clean(chunk)
        m = re.match(r"^(.*?)[,\s]\s*(Chairman|Vice-?\s*Chairman|Board Member)\s*$",
                     line, re.I)
        if not m:
            continue
        name = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(",").strip()
        # Names carry nicknames and suffixes ("Floyd "BJ" Holocker, III"); what
        # they never contain is a digit or an @, which is the cheap sanity test.
        if not name or re.search(r"[@\d]", name):
            continue
        role = ("Vice Chairman" if re.match(r"(?i)vice", m.group(2)) else
                "Chairman" if re.match(r"(?i)chair", m.group(2)) else "Board Member")
        if not any(x["name"] == name for x in members):
            members.append({"name": name, "role": role})
    office = None
    lines = text_lines(page)
    for i, line in enumerate(lines):
        if re.search(r"Putnam County Courthouse", line, re.I):
            addr = [l for l in lines[i + 1:i + 5]
                    if not re.match(r"(?i)^(P\.?O\.? Box|Phone|Fax)", l)]
            street = next((l for l in addr if re.match(r"^\d+\s", l)), None)
            city = next((l for l in addr if re.search(r",\s*IL\s*\d{5}", l)), None)
            office = {"label": "County Board",
                      "address": ", ".join(x for x in (street, city) if x) or None,
                      "phone": normalize_phone(" ".join(lines[i:i + 10]))}
            break
    return members, office


# ----------------------------------------------------------------- Brown
def parse_brown(page):
    """Brown groups members under role headings ("Chairman", "Vice-Chairman",
    "Board Members") with one <p> each: name, street, town, phone, e-mail.

    THE STREET AND TOWN ARE READ ONLY TO BE DROPPED — they are the member's
    RESIDENCE, and the fleet never collects those (the Madison precedent).

    ONE SOURCE TYPO TO SURVIVE: the Vice-Chairman's phone is marked up as
    `<a href="mail:2176538827">` — "mail:" where every other row has "tel:".
    Reading phones out of the href would silently drop his; the visible text is
    read instead."""
    members = []
    for heading, body in re.findall(
            r'(?is)<span class="title-text[^"]*">(.*?)</span>.*?'
            r'<div class="pp-sub-heading">(.*?)</div>', page):
        head = clean(heading)
        role = ("Chairman" if re.fullmatch(r"(?i)chairman", head) else
                "Vice Chairman" if re.search(r"(?i)vice", head) else
                "Board Member" if re.search(r"(?i)board member", head) else None)
        if not role:
            continue
        for para in re.findall(r"(?is)<p[^>]*>(.*?)</p>", body):
            name_m = re.search(r"(?is)<strong>(.*?)</strong>", para)
            if not name_m:
                continue
            name = clean(name_m.group(1))
            if not re.fullmatch(r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3}", name or ""):
                continue
            entry = {"name": name, "role": role}
            phone = normalize_phone(clean(para), keep_ext=False)
            if phone:
                entry["phone"] = phone
            em = re.search(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", para)
            if em:
                entry["email"] = em.group(1).strip().lower()
            if not any(x["name"] == name for x in members):
                members.append(entry)
    return members, None


# --------------------------------------------------------------- Calhoun
def parse_calhoun(page):
    """Calhoun gives each commissioner a `text-module-elected-person` block:
    name, title, "Term: YYYY to Present", a biography, e-mail, and a phone.

    THE PHONE IS THE SAME NUMBER ON EVERY ROW — 618-576-9700 ext. 2 — which
    makes it the board's switchboard, not per-member contact. Repeating it
    under five names would imply five direct lines that do not exist, so it is
    hoisted to the board office once (the Monroe posture: a shared switchboard
    is honest, an invented per-member number is not). The biographies are not
    card material and are dropped.

    AT-LARGE, PROVEN: the county's own certified 2026 primary report names the
    contest "CO.COMMISSIONER CWD" — countywide."""
    members, phones = [], set()
    for block in re.findall(r'(?is)text-module-elected-person.*?'
                            r'<div class="et_pb_text_inner">(.*?)</div>', page):
        parts = [clean(x) for x in re.split(r"(?is)<[^>]+>", block)]
        parts = [p for p in parts if p]
        if not parts:
            continue
        name = parts[0]
        if not re.fullmatch(r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3}", name or ""):
            continue
        joined = " ".join(parts)
        role = ("Vice Chairman" if re.search(r"(?i)vice\s*chair", joined) else
                "Chairman" if re.search(r"(?i)chair", joined) else
                "Commissioner" if re.search(r"(?i)commissioner", joined) else None)
        if not role:
            continue
        entry = {"name": name, "role": role}
        since = re.search(r"Term:\s*(\d{4})\s*to\s*Present", joined, re.I)
        if since:
            entry["since"] = int(since.group(1))
        em = re.search(r"mailto:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", block)
        if em:
            entry["email"] = em.group(1).strip().lower()
        tel = normalize_phone(joined)
        if tel:
            phones.add(tel)
        if not any(x["name"] == name for x in members):
            members.append(entry)
    # One distinct number across the whole board => switchboard, not per-member.
    office = ({"label": "Board of Commissioners", "phone": phones.pop()}
              if len(phones) == 1 else None)
    return members, office



def parse_schuyler(page):
    """Schuyler prints the board as three HEADED groups — "Chairman",
    "Vice-Chairman", then "County Board Members" — with each person followed by
    the courthouse address, a phone and a county e-mail.

    THE ROLE IS THE HEADING, NOT THE ROW. Every other county in this file marks
    the officer on the person's own line; here the heading above a name is the
    only thing that says who chairs. So the parse carries the current heading
    forward and applies it to the names beneath it, and a name appearing before
    any heading is dropped rather than given a default role.

    THE ADDRESS IS THE COURTHOUSE, ON ALL SEVEN ROWS — 102 S. Congress St.,
    Suite 104, Rushville. That makes it the board's office, not seven
    residences, so it is hoisted once (the Calhoun/Monroe posture) rather than
    repeated under each name as if it were personal. The PHONES do differ per
    member, so those stay on the rows.

    AT-LARGE, PROVEN: the County Clerk's own certified results
    (elections.schuyler.il.us/results-2.pdf) name the contest "FOR MEMBERS OF
    THE COUNTY BOARD ... (Vote for not more than four)" with "Precincts
    Reporting 17 of 17" — one countywide contest, and the word "District" does
    not appear anywhere in the 11-page canvass. Seven seats, elected in
    staggered groups."""
    ROLES = (("(?i)^vice[-\s]*chair", "Vice-Chairman"),
             ("(?i)^chair", "Chairman"),
             ("(?i)^county board members", "Board Member"))
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    text = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|td|tr)>", "\n", text)
    lines = [clean(l) for l in re.sub(r"<[^>]+>", "\n", text).split("\n")]
    lines = [l for l in lines if l]

    members, role, office_phone = [], None, None
    seen = set()
    for i, line in enumerate(lines):
        matched = next((r for pat, r in ROLES if re.search(pat, line)), None)
        if matched:
            role = matched
            continue
        if not role:
            continue
        if not re.fullmatch(r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3}", line):
            continue
        window = " ".join(lines[i:i + 4])
        email = re.search(r"[\w.+-]+@[\w.-]+\.\w+", window)
        phone = re.search(r"\b(\d{3}-\d{3}-\d{4})\b", window)
        # A name with neither is a nav item or a caption, not a member row.
        if not (email or phone):
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        entry = {"name": line, "role": role}
        if email:
            entry["email"] = email.group(0).lower()
        if phone:
            entry["phone"] = phone.group(1)
        members.append(entry)

    office = {"label": "Schuyler County Board",
              "address": "102 S. Congress St., Suite 104, Rushville, IL 62681"}
    return members, office



# ---------------------------------------------------------------- Hamilton
def parse_hamilton(page):
    """Hamilton's board page (the county's NEW site — it went live the morning
    of 2026-08-05, mid-migration by the Clerk's own description) renders each
    member as a card whose name sits alone in a `font-semibold text-ink` div —
    exactly five, and nothing else on the page uses that class. The cards
    carry committee lists but no per-member contact, so what ships per member
    is name and role, with the BOARD's shared departmental line hoisted to the
    office block — a shared line is honest, an invented per-member number is
    not.

    AT-LARGE, STATED BY THE ELECTION AUTHORITY: County Clerk & Recorder
    Heather Bowman, in writing, 2026-08-05, four minutes after being asked —
    "Our County Board is elected at large." The members page corroborates:
    no district appears anywhere on it.

    CHAIR FROM THE HEADER, NOT THE CARDS: the member cards are role-less; the
    department header reads "Kelly Woodrow / Board Chair". The parse takes the
    chair from that adjacency (normalized to the fleet's "Chairman"
    vocabulary) and applies Board Member to the rest. A header name that never
    appears among the cards is dropped, never added."""
    names = [clean(n) for n in
             re.findall(r'<div class="font-semibold text-ink">([^<]+)</div>', page)]
    names = [n for n in names if n]
    m = re.search(r">([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*){1,3})"
                  r"(?:\s*</?[a-zA-Z][^>]*>\s*)*Board\s+Chair", page)
    chair = clean(m.group(1)) if m else None
    members, seen = [], set()
    for n in names:
        if n.lower() in seen:
            continue
        seen.add(n.lower())
        members.append({"name": n,
                        "role": "Chairman" if (chair and n == chair) else "Board Member"})
    office = {"label": "Hamilton County Board",
              "address": "Hamilton County Courthouse, 100 S. Jackson Street, Room 2, McLeansboro, IL 62859",
              "phone": "618-643-2721",
              "email": "board@hamiltoncountyil.gov"}
    return members, office


# ---------------------------------------------------------------------------
# COUNTIES WITH NO WEBSITE TO SCRAPE.
#
# Every SITES entry below fetches a page. This table is for the counties that
# have no page to fetch — not blocked, not slow, ABSENT. Edwards is the first:
# asked directly on 2026-08-06 whether the county uses some other web address,
# County Clerk & Recorder Melanie Knight replied "The county does not currently
# have a website", which matches the measurement (edwardscounty.illinois.gov
# answers NOERROR with no A record; www. is NXDOMAIN — the domain carries mail
# and hosts nothing). No scraper can ever exist for such a county, so the
# roster comes from a document its Clerk sent and is carried here verbatim.
#
# THE HONESTY COST IS REAL AND IS PAID OUT LOUD. A weekly job that "refreshes"
# a hand-carried roster refreshes nothing: the same names ship every run
# whatever the county has done since. So each entry states the document and the
# date it was verified, and main() prints a line every run naming the county,
# the document and how old it is. It is never silently folded in with the
# counties that really were re-read.
#
# WHAT IS DELIBERATELY NOT SHIPPED. Knight's letterhead gives each commissioner
# a HOME address and a personal phone (two of them marked "(h)" and "(c)"). The
# roster ships neither — the same call every municipal source in this project
# makes, because a card must not publish a private home. What ships is the name,
# the office, and the county e-mail address the county itself assigns
# (commissioner1@…, commissioner2@…), which is a real contact route that belongs
# to the seat rather than the person. The office block gets the courthouse
# address only: the phone on the letterhead is the CLERK's line, and printing it
# under "Board Office" would imply the board answers it.
DOCUMENT_ROSTERS = {
    "EDWARDS": {
        "name": "Edwards County",
        "structure": "Commission form — 3 commissioners elected countywide",
        "document": "Commissioners names-addresses 2025.doc, sent by County Clerk "
                    "& Recorder Melanie Knight, 2026-08-06",
        "verified": "2026-08-06",
        "expect": 3,
        # Ordered as the county's own document orders them by seat number.
        "members": [
            {"name": "Duane Lear", "role": "Chairman",
             "email": "commissioner1@edwardscounty.illinois.gov", "since": 2020},
            {"name": "Davis Messman", "role": "Commissioner",
             "email": "commissioner2@edwardscounty.illinois.gov", "since": 2022},
            {"name": "Matthew R. St.Ledger", "role": "Commissioner",
             "email": "commissioner3@edwardscounty.illinois.gov", "since": 2024},
        ],
        "office": {
            "label": "Edwards County Courthouse",
            "address": "50 East Main Street, Albion, IL 62806",
        },
    },
}


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
    "SCHUYLER": {
        "name": "Schuyler County",
        "url": "https://www.schuylercounty.org/county-board/county-board-members/",
        "structure": "7 members elected countywide",
        "expect": 7,
        "parse": parse_schuyler,
    },
    "PIKE": {
        "name": "Pike County",
        "url": "https://www.pikecountyil.org/county-boards/",
        "structure": "9 members elected countywide — no districts",
        "expect": 9,
        "parse": parse_pike,
    },
    "PUTNAM": {
        "name": "Putnam County",
        "url": "https://putnamil.gov/government/county_board/index.php",
        "structure": "5 members elected countywide — no districts",
        "expect": 5,
        "parse": parse_putnam,
    },
    "BROWN": {
        "name": "Brown County",
        # browncountyil.org is a captcha-parked DECOY, not the county.
        "url": "https://www.browncoil.org/county-board/",
        "structure": "7 members elected countywide — no districts",
        "expect": 7,
        "parse": parse_brown,
    },
    "CALHOUN": {
        "name": "Calhoun County",
        # The apex does not resolve; the www host is required.
        "url": "https://www.calhouncountyil.gov/government/county-board/members/",
        "structure": "Commission form — 5 commissioners elected countywide",
        "expect": 5,
        "parse": parse_calhoun,
    },
    "HAMILTON": {
        "name": "Hamilton County",
        # The county's NEW site (live 2026-08-05). At-large per Clerk Bowman
        # in writing the same day; see parse_hamilton's provenance note.
        "url": "https://www.hamiltoncountyil.gov/departments/county-board/",
        "structure": "5 members elected countywide — no districts",
        "expect": 5,
        "parse": parse_hamilton,
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

    # The counties with no website. Emitted without a fetch, and never quietly:
    # a hand-carried roster that ages is the failure mode this list invites, so
    # every run says which county, from which document, and how stale.
    for key, spec in DOCUMENT_ROSTERS.items():
        if key in out:
            print("county-commissioners: FAIL — %s is in both SITES and "
                  "DOCUMENT_ROSTERS; a county has one source, not two" % key,
                  file=sys.stderr)
            sys.exit(1)
        if len(spec["members"]) != spec["expect"]:
            print("county-commissioners: FAIL — %s carries %d members, expected %d"
                  % (key, len(spec["members"]), spec["expect"]), file=sys.stderr)
            sys.exit(1)
        age = ""
        try:
            verified = datetime.date.fromisoformat(spec["verified"])
            age = ", %d days old" % (datetime.date.today() - verified).days
        except Exception:
            pass
        print("county-commissioners: NOT RE-READ — %s has no website; its %d "
              "members come from %s%s. Re-ask the Clerk to refresh."
              % (key, len(spec["members"]), spec["document"], age), file=sys.stderr)
        out[key] = {
            "county": spec["name"],
            "structure": spec["structure"],
            "sourceDocument": spec["document"],
            "verified": spec["verified"],
            "members": spec["members"],
        }
        if spec.get("office"):
            out[key]["office"] = spec["office"]

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

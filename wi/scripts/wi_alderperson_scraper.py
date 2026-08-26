#!/usr/bin/env python3
"""
Scrape the alderperson rosters for the six big Wisconsin cities whose
aldermanic districts the statewide dissolve ships AND whose rosters have a
verified open route (measured 2026-08-26). Stage 1 of the pair;
build_wi_alderperson_roster.py writes data/app/wi-alderpersons.json.

THE SIX, each with its route and its measured trap:

  Milwaukee (15)  — the city's own GIS layer election/alderman/MapServer/0,
                    whose ALDERPERSON attribute names all 15. The host drops
                    roughly 1 in 4-8 requests with TCP resets, so the fetch
                    retries and then falls back to the same data's CKAN
                    shapefile (data.milwaukee.gov, reliable). WITNESSED
                    weekly against the city's Legistar API (COMMON COUNCIL
                    is body 1): a name-set mismatch fails the city loudly.
                    Legistar is a witness, never a source — and its date
                    filters are ignored server-side (the county lesson), so
                    membership is filtered client-side against today.
  Madison (20)    — the council index page's per-alder links. THE INDEX'S
                    FLAT TEXT PAIRING IS A TRAP: District 1 is vacant, so a
                    flattened read pairs every alder with the district ABOVE
                    their real one (measured: "District 1 / Alder Ochowicz"
                    on the flat page; Ochowicz's own page is District 2).
                    The district comes from each alder's own /council/
                    districtN page — its H1 states "District N - Alder
                    SURNAME" or "District N - Vacant" — and the seat e-mail
                    districtN@cityofmadison.com rides the page.
  Green Bay (12)  — the city's staff directory, parsed per <li> entry
                    (never flattened: the responsive layout prints each
                    title twice). Name, real mailto, phone, profile URL.
                    One entry measures a display-name/e-mail nickname split
                    ("Bill Morgan" / mailto Jim... no — William) — the
                    display name ships.
  Kenosha (17)    — the city GIS's Districts_ElectedRepresentation layer
                    (REP_AREA='D' rows carry REPRESNTTV; each district
                    appears twice, once named and once 'N/A' — both facts
                    gated). kenosha.org itself is Cloudflare-challenged, so
                    the currency witness is the COUNTY's certified April
                    2026 spring canvass (kenoshacountywi.gov, open): all 17
                    alderperson contests, positionally parsed — candidate
                    names are CENTERED vertical column headers, so stacks
                    cluster by column CENTER (clustering by left edge reads
                    the winner out of the wrong column; measured), and the
                    Totals row's first k numbers are the k candidates'
                    votes. Every GIS name must match its district's
                    certified winner.
  Racine (15)     — the city's alderman index, "District #N – Alderman
                    NAME" one line per district, plus each district's page
                    link (the slugs are inconsistent — "district-1" and
                    "02-district" both live — so the link is captured from
                    the line, never composed).
  Waukesha (15)   — the common-council page's per-district blocks:
                    "Aldermanic District N" / "Wards …" / NAME / phone /
                    seat e-mail (alddistN@waukesha-wi.gov — the seat's, so
                    contact survives turnover).

Appleton's roster page is verified readable and is deliberately NOT here:
its geometry cannot ship (Outagamie submits all 50 of its wards uncoded and
the city's own GIS publishes no aldermanic layer — both measured), so a
roster would have no card to ride. The gap record carries the ready route.
"""

import io
import json
import os
import re
import ssl
import struct
import sys
import time
import unicodedata
import urllib.request
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, ".cache")
DEFAULT_OUT = os.path.join(CACHE_DIR, "wi_alderpersons_raw.json")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

MKE_GIS = ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/election"
           "/alderman/MapServer/0/query?where=1%3D1&outFields=DISTRICT,ALDERPERSON"
           "&returnGeometry=false&f=json")
MKE_CKAN_ZIP = ("https://data.milwaukee.gov/dataset/1301738f-4b4a-4f73-bbaa-a4cac069e371"
                "/resource/4b68b244-779e-406f-9d94-7fb85a764496/download/alderman.zip")
MKE_LEGISTAR = ("https://webapi.legistar.com/v1/milwaukee/officerecords"
                "?$filter=OfficeRecordBodyId%20eq%201&$top=1000")
MADISON_INDEX = "https://www.cityofmadison.com/council/council-members"
MADISON_DISTRICT = "https://www.cityofmadison.com/council/district%d"
GREEN_BAY_DIR = "https://www.greenbaywi.gov/m/directory"
KENOSHA_GIS = ("https://gis-city.kenosha.org/server/rest/services/Organizational_Layers"
               "/Districts_ElectedRepresentation/FeatureServer/150/query"
               "?where=REP_AREA%3D%27D%27&outFields=DIST_NO,REPRESNTTV"
               "&returnGeometry=false&f=json&resultRecordCount=100")
KENOSHA_CANVASS = ("https://www.kenoshacountywi.gov/DocumentCenter/View/31064"
                   "/OFFICIAL-CANVASSED-RESULTS")
RACINE_INDEX = ("https://cityofracinewi.gov/government/city-leadership"
                "/common-council/cityalderman/")
WAUKESHA_INDEX = "https://www.waukesha-wi.gov/about_the_common_council/index.php"

# Districts where the certified April 2026 canvass OVERRIDES the city GIS,
# each pinned only after its story was read. The pin is self-retiring twice
# over: it fails if the canvass stops naming this winner, and it fails the
# day the GIS catches up (remove it then).
KENOSHA_CANVASS_WINS = {
    14: {"name": "Daniel L. Prozanski, Jr.",
         "why": ("the GIS still names Kenny Harper, who won in April 2024 and did "
                 "not seek re-election in 2026 (he moved out of the district — "
                 "Ballotpedia/WGTD, read 2026-08-26); Prozanski won the certified "
                 "April 2026 contest 913 votes to write-ins' 17. The layer's recent "
                 "modified date is the VIEW definition's, not the data's — the "
                 "vintage trap, Kenosha edition.")},
}

CITIES = {  # COUSUBFP -> (name, seats)
    "53000": ("Milwaukee", 15),
    "48000": ("Madison", 20),
    "31000": ("Green Bay", 12),
    "39225": ("Kenosha", 17),
    "66000": ("Racine", 15),
    "84250": ("Waukesha", 15),
}


def fetch(url, binary=False, tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=ssl.create_default_context()) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 — retried, then re-raised
            last = e
            time.sleep(2 * (i + 1))
    raise last


def fold(name):
    """First + last alphabetic token, accent-stripped — the fleet's person
    fold: middle initials, suffixes and diacritics never read as different
    people; a genuinely different first or last name still does."""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    toks = [t for t in re.split(r"[^a-z]+", s) if len(t) > 1 and t not in
            ("jr", "sr", "ii", "iii", "iv")]
    return (toks[0] + "|" + toks[-1]) if toks else ""


def fold_set(name):
    """Unordered token fold, for a source that prints names surname-first:
    the Kenosha canvass's vertical column headers reassemble in reading
    order ('LaMacchia, Rocco Sr. J.'), so ordered first|last comparison
    reads a reversal as a different person. The token SET doesn't care."""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return frozenset(t for t in re.split(r"[^a-z]+", s) if len(t) > 1 and t not in
                     ("jr", "sr", "ii", "iii", "iv"))


def strip_tags(html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    import html as H
    return [l.strip() for l in H.unescape(t).split("\n") if l.strip()]


# ---------------------------------------------------------------- Milwaukee
def read_dbf(data):
    n_rec = struct.unpack("<I", data[4:8])[0]
    hdr_len = struct.unpack("<H", data[8:10])[0]
    rec_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    off = 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b"\x00")[0].decode()
        fields.append((name, data[off + 16]))
        off += 32
    rows = []
    pos = hdr_len
    for _ in range(n_rec):
        rec = data[pos:pos + rec_len]
        pos += rec_len
        o = 1
        row = {}
        for name, flen in fields:
            row[name] = rec[o:o + flen].decode("latin1").strip()
            o += flen
        rows.append(row)
    return rows


def scrape_milwaukee():
    members = {}
    try:
        for i in range(6):
            try:
                d = json.loads(fetch(MKE_GIS, tries=1, timeout=25))
                for f in d["features"]:
                    a = f["attributes"]
                    members["%02d" % int(a["DISTRICT"])] = {"name": a["ALDERPERSON"].strip()}
                break
            except Exception:  # noqa: BLE001 — the measured flaky host
                time.sleep(2)
    except Exception:  # noqa: BLE001
        pass
    source = MKE_GIS.split("/query")[0]
    if len(members) != 15:
        members = {}
        z = zipfile.ZipFile(io.BytesIO(fetch(MKE_CKAN_ZIP, binary=True)))
        dbf = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        for row in read_dbf(z.read(dbf)):
            members["%02d" % int(row["DISTRICT"])] = {"name": row["ALDERPERSO"].strip()}
        source = MKE_CKAN_ZIP
        print("milwaukee: GIS host dropped every try; the CKAN shapefile answered",
              file=sys.stderr)
    if len(members) != 15:
        raise SystemExit("milwaukee names %d of 15 districts" % len(members))

    # the Legistar witness: current COMMON COUNCIL membership, client-side
    # dated. NEVER OfficeRecordFullName — that column is "ALD. SURNAME"
    # (measured), so the fold is built from the First/Last columns.
    today = time.strftime("%Y-%m-%d")
    recs = json.loads(fetch(MKE_LEGISTAR))
    current = set()
    for r in recs:
        start = (r.get("OfficeRecordStartDate") or "")[:10]
        end = (r.get("OfficeRecordEndDate") or "9999")[:10]
        if start <= today <= end:
            full = ((r.get("OfficeRecordFirstName") or "") + " " +
                    (r.get("OfficeRecordLastName") or "")).strip()
            if full:
                current.add(fold(full))
    gis = {fold(m["name"]) for m in members.values()}
    if gis - current:
        raise SystemExit("milwaukee: GIS names %s absent from Legistar's current "
                         "COMMON COUNCIL membership — the layer went stale"
                         % sorted(gis - current))
    return members, source


# ------------------------------------------------------------------ Madison
def scrape_madison():
    index = fetch(MADISON_INDEX)
    by_href = {}
    for m in re.finditer(r'href="(?:https://www\.cityofmadison\.com)?/council/district(\d+)"'
                         r'[^>]*>\s*Alder\s+([^<]+)<', index):
        by_href[int(m.group(1))] = " ".join(m.group(2).split())
    if not (17 <= len(by_href) <= 20):
        raise SystemExit("madison index links %d alder districts (expected ~19-20 "
                         "with vacancies) — the page shape moved" % len(by_href))
    members = {}
    vacant = []
    for n in range(1, 21):
        page = fetch(MADISON_DISTRICT % n)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        head = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else ""
        if not head.startswith("District %d" % n):
            raise SystemExit("madison district page %d headlines %r" % (n, head))
        if "Vacant" in head:
            vacant.append(n)
            continue
        sur = re.sub(r"^District %d\s*-\s*Alder\s*" % n, "", head).strip()
        name = by_href.get(n)
        if not name or fold(name).split("|")[-1] != fold("x " + sur).split("|")[-1]:
            raise SystemExit("madison D%d: index name %r does not carry the page's "
                             "surname %r — the index/href pairing moved" % (n, name, sur))
        entry = {"name": name, "url": MADISON_DISTRICT % n}
        m = re.search(r'mailto:(district%d@cityofmadison\.com)' % n, page)
        if m:
            entry["email"] = m.group(1)
        members["%02d" % n] = entry
    if len(members) + len(vacant) != 20:
        raise SystemExit("madison: %d named + %d vacant != 20" % (len(members), len(vacant)))
    if len(members) < 17:
        raise SystemExit("madison names only %d of 20 districts" % len(members))
    return members, MADISON_INDEX, vacant


# ---------------------------------------------------------------- Green Bay
def scrape_green_bay():
    page = fetch(GREEN_BAY_DIR)
    members = {}
    # split on the ENTRY container class, never a bare <li>: each entry nests
    # a <ul><li> department list, so a bare-<li> split cuts the entry before
    # its e-mail and phone column (measured — the first draft shipped twelve
    # names with no contact at all)
    for li in re.split(r'<li class="list-group-item', page)[1:]:
        t = re.search(r"District\s+(\d+)\s+Alderperson", li)
        if not t:
            continue
        n = int(t.group(1))
        nm = re.search(r'href="(/m/directory/employee\?eid=\d+)"[^>]*>\s*([^<]+?)\s*<', li)
        if not nm:
            continue
        entry = {"name": " ".join(nm.group(2).split()),
                 "url": "https://www.greenbaywi.gov" + nm.group(1)}
        em = re.search(r'mailto:([^"?]+)"', li)
        if em:
            entry["email"] = em.group(1).strip()
        ph = re.search(r'href="tel:([^",]+)', li)
        if ph:
            entry["phone"] = ph.group(1).strip()
        key = "%02d" % n
        if key in members and members[key]["name"] != entry["name"]:
            raise SystemExit("green bay lists two names for district %d" % n)
        members[key] = entry
    if len(members) != 12:
        raise SystemExit("green bay names %d of 12 districts" % len(members))
    return members, GREEN_BAY_DIR


# ------------------------------------------------------------------ Kenosha
def kenosha_canvass_winners(pdf_path):
    """Positional parse of the county's certified canvass: per alderperson
    contest, candidate columns are centered vertical stacks; the Totals
    row's first k numbers are the k candidates' votes."""
    import pdfplumber
    BOIL = {"VOTE", "FOR", "of", "Precincts", "Reporting", "Totals", "Cast",
            "Total", "Votes", "Overvotes", "Undervotes", "Contest", "Write-in"}
    wins = {}
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            words = pg.extract_words()
            titles = []
            for i, w in enumerate(words):
                if (w["text"] == "Alderperson" and i + 2 < len(words)
                        and words[i + 1]["text"] == "District"
                        and re.match(r"^\d+$", words[i + 2]["text"])):
                    titles.append({"n": int(words[i + 2]["text"]), "x0": w["x0"]})
            if not titles:
                continue
            votes = sorted((w for i, w in enumerate(words) if w["text"] == "VOTE"
                            and i + 1 < len(words) and words[i + 1]["text"] == "FOR"),
                           key=lambda w: w["x0"])
            reps = [w for w in words if w["text"] == "Reporting"]
            units = [w for w in words if w["text"] in ("Town", "Village", "City")]
            tots = [w for w in words if w["text"] == "Totals"]
            if not (votes and reps and units and tots):
                continue
            h_top = max(r["top"] for r in reps) + 2
            unit_tops = [u["top"] for u in units if u["top"] > h_top]
            if not unit_tops:
                continue
            h_bot = min(unit_tops) - 2
            trow = max(tots, key=lambda w: w["top"])
            hw = [w for w in words if h_top < w["top"] < h_bot
                  and w["text"] not in BOIL and not re.match(r"^[\d,%.]+$", w["text"])]
            stacks = []
            for w in sorted(hw, key=lambda a: ((a["x0"] + a["x1"]) / 2, a["top"])):
                c = (w["x0"] + w["x1"]) / 2
                for s in stacks:
                    if abs(s["c"] - c) < 25:
                        s["ws"].append(w)
                        s["c"] = sum((x["x0"] + x["x1"]) / 2 for x in s["ws"]) / len(s["ws"])
                        break
                else:
                    stacks.append({"c": c, "ws": [w]})
            nums = sorted((w for w in words if abs(w["top"] - trow["top"]) < 3
                           and re.match(r"^[\d,]+$", w["text"])), key=lambda w: w["x0"])
            bounds = [0.0]
            for vi in range(1, len(votes)):
                bounds.append((votes[vi - 1]["x0"] + votes[vi]["x0"]) / 2)
            bounds.append(pg.width)
            for vi, v in enumerate(votes):
                lo, hi = bounds[vi], bounds[vi + 1]
                t = min(titles, key=lambda t: abs(t["x0"] - v["x0"]))
                if not (lo <= t["x0"] + 5 and t["x0"] - 5 <= hi):
                    continue  # this VOTE anchor belongs to a non-alder contest
                cst = sorted((s for s in stacks if lo <= s["c"] < hi), key=lambda s: s["c"])
                names = [" ".join(x["text"] for x in sorted(s["ws"], key=lambda a: a["top"]))
                         for s in cst]
                cnm = [w for w in nums if lo <= (w["x0"] + w["x1"]) / 2 < hi]
                k = len(names)
                if not k or len(cnm) < k:
                    continue
                pairs = [(names[i], int(cnm[i]["text"].replace(",", ""))) for i in range(k)]
                winner = max(pairs, key=lambda p: p[1])
                if t["n"] in wins:
                    raise SystemExit("kenosha canvass: contest %d parsed twice" % t["n"])
                wins[t["n"]] = winner
    return wins


def scrape_kenosha():
    d = json.loads(fetch(KENOSHA_GIS))
    members = {}
    for f in d["features"]:
        a = f["attributes"]
        name = (a.get("REPRESNTTV") or "").strip()
        if name and name != "N/A":
            key = "%02d" % int(a["DIST_NO"])
            if key in members and members[key]["name"] != name:
                raise SystemExit("kenosha GIS names two people for district %s" % key)
            members[key] = {"name": name}
    if len(members) != 17:
        raise SystemExit("kenosha GIS names %d of 17 districts" % len(members))

    os.makedirs(CACHE_DIR, exist_ok=True)
    pdf_path = os.path.join(CACHE_DIR, "kenosha_canvass_2026_spring.pdf")
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 100000:
        open(pdf_path, "wb").write(fetch(KENOSHA_CANVASS, binary=True))
    wins = kenosha_canvass_winners(pdf_path)
    if len(wins) != 17:
        raise SystemExit("kenosha canvass parsed %d of 17 alderperson contests" % len(wins))
    bad = []
    for n in range(1, 18):
        key = "%02d" % n
        # subset, not equality: the ballot prints middle names the GIS omits
        # ("Brandi Rose Ferree" / "Ruth Delace Dyson", measured) — the same
        # person styled apart, where a different person shares no tokens
        a, b = fold_set(members[key]["name"]), fold_set(wins[n][0])
        if a and b and (a <= b or b <= a):
            continue
        if n in KENOSHA_CANVASS_WINS:
            pin = KENOSHA_CANVASS_WINS[n]
            if fold_set(wins[n][0]) != fold_set(pin["name"]):
                raise SystemExit("kenosha D%d: the pinned canvass override no longer "
                                 "matches the canvass (%r vs pin %r)" % (n, wins[n][0], pin["name"]))
            if fold_set(members[key]["name"]) == fold_set(pin["name"]):
                raise SystemExit("kenosha D%d: the GIS now agrees with the canvass — "
                                 "the override has served its purpose; remove the pin" % n)
            stale = members[key]["name"]
            members[key] = {"name": pin["name"],
                            "note": "Elected April 2026 (certified by the Kenosha County "
                                    "Board of Canvassers)"}
            print("kenosha D%d: certified April 2026 winner %r ships over the GIS's "
                  "stale %r — %s" % (n, pin["name"], stale, pin["why"]),
                  file=sys.stderr)
            continue
        bad.append((n, members[key]["name"], wins[n][0]))
    if bad:
        raise SystemExit("kenosha: GIS name(s) differ from the certified April 2026 "
                         "winner(s): %s — an appointment or a stale layer; needs a "
                         "human look (pin a KENOSHA_CANVASS_WINS entry only after "
                         "reading the story)" % bad)
    return members, KENOSHA_GIS.split("/query")[0]


# ------------------------------------------------------------------- Racine
def scrape_racine():
    page = fetch(RACINE_INDEX)
    members = {}
    # each staff card: a "District #N – Alderman NAME" heading, then a "Read
    # More and Contact" link to the district's own page (slugs inconsistent
    # across districts — captured, never composed)
    for m in re.finditer(r'District\s*#(\d+)\s*[–-]\s*'
                         r'Alder(?:man|woman|person)?\s+([^<]+?)\s*<', page):
        n, name = int(m.group(1)), " ".join(m.group(2).split())
        key = "%02d" % n
        if key in members and members[key]["name"] != name:
            raise SystemExit("racine lists two names for district %d" % n)
        entry = {"name": name}
        tail = page[m.end():m.end() + 800]
        u = re.search(r'href="(https://cityofracinewi\.gov[^"]*cityalderman/[^"]+)"', tail)
        if u:
            entry["url"] = u.group(1)
        members[key] = entry
    if len(members) != 15:
        raise SystemExit("racine names %d of 15 districts" % len(members))
    return members, RACINE_INDEX


# ----------------------------------------------------------------- Waukesha
def scrape_waukesha():
    lines = strip_tags(fetch(WAUKESHA_INDEX))
    members = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^Aldermanic District (\d+)$", lines[i])
        # the page prints the district list twice; only the second pass has a
        # "Wards …" line under each heading, which is the block this reads
        if m and i + 2 < len(lines) and lines[i + 1].startswith("Wards"):
            n = int(m.group(1))
            entry = {"name": lines[i + 2]}
            j = i + 3
            while j < len(lines) and not lines[j].startswith("Aldermanic District"):
                if lines[j] == "P:" and j + 1 < len(lines):
                    entry["phone"] = lines[j + 1]
                if lines[j] == "E:" and j + 1 < len(lines) and "@" in lines[j + 1]:
                    entry["email"] = lines[j + 1]
                j += 1
            if not re.match(r"^[A-Z][A-Za-z.'\- ]+$", entry["name"]):
                raise SystemExit("waukesha district %d name line reads %r — the "
                                 "block shape moved" % (n, entry["name"]))
            members["%02d" % n] = entry
            i = j
        else:
            i += 1
    if len(members) != 15:
        raise SystemExit("waukesha names %d of 15 districts" % len(members))
    return members, WAUKESHA_INDEX


def main():
    argv = sys.argv[1:]
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT

    mke, mke_src = scrape_milwaukee()
    mad, mad_src, mad_vacant = scrape_madison()
    gb, gb_src = scrape_green_bay()
    ken, ken_src = scrape_kenosha()
    rac, rac_src = scrape_racine()
    wau, wau_src = scrape_waukesha()

    cities = {
        "53000": {"municipality": "Milwaukee", "seats": 15, "sourceUrl": mke_src,
                  "members": mke},
        "48000": {"municipality": "Madison", "seats": 20, "sourceUrl": mad_src,
                  "members": mad, "vacantDistricts": mad_vacant},
        "31000": {"municipality": "Green Bay", "seats": 12, "sourceUrl": gb_src,
                  "members": gb},
        "39225": {"municipality": "Kenosha", "seats": 17, "sourceUrl": ken_src,
                  "members": ken},
        "66000": {"municipality": "Racine", "seats": 15, "sourceUrl": rac_src,
                  "members": rac},
        "84250": {"municipality": "Waukesha", "seats": 15, "sourceUrl": wau_src,
                  "members": wau},
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"cities": cities}, f, indent=2, ensure_ascii=False)
    total = sum(len(c["members"]) for c in cities.values())
    print("scraped %d alderpersons across %d cities (Madison vacant: %s) -> %s"
          % (total, len(cities), mad_vacant or "none", out_path))


if __name__ == "__main__":
    main()

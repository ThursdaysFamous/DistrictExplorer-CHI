#!/usr/bin/env python3
"""
Resolve the per-county municipal-officials scraper outputs into one record per
municipality and write the JSON app-data file the Municipality card reads:
data/app/municipal-officials.json.

Keys are the 7-digit CENSUS PLACE GEOID ("17" + PLACEFP, e.g. 1701010 for
Alsip) because that is exactly the `GEOID` the app's TIGERweb places layer
already carries on every municipality feature — so the card's join needs no
name normalization at query time, and the 47 metro municipalities that span
county lines resolve to ONE entry instead of one per county
(docs/EXPANSION_GUIDE.md Part 2.4).

The name -> GEOID mapping comes from the Census 2020 place-by-county reference
file committed at data/source/st17_il_place_by_county2020.txt. Lookup prefers
a place in the source's own county and falls back to a statewide unique match,
which is what resolves municipalities the county clerk claims but Census lists
only under a neighbour (Oak Brook is a Cook Clerk jurisdiction but is listed
under DuPage). Only two Illinois incorporated-place names collide statewide
(Wilmington, Windsor) and neither is in the metro; an ambiguous or unmatched
name is a hard failure, never a guess.

Contact data in these sources is MUNICIPALITY-level, not per-person — in the
Cook DOEO API every official of a municipality carries the same village-hall
phone/email/address and the per-person columns are empty for all 1,134
records. It is therefore emitted once under `office`, never on a person, so
the card cannot imply a direct line to a trustee that does not exist.

Usage:
    python3 build_municipal_officials_roster.py cook_municipal_officials.json [more...] [--out-dir DIR]

Each positional argument is one county scraper's output. Counties may be
built incrementally: this rewrites the whole file from the inputs given, so
pass every county's output that should ship.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")
PLACES_FILE = os.path.join(REPO_ROOT, "data", "source", "st17_il_place_by_county2020.txt")

# Census county FIPS for every sourced county, for county-preferred lookup.
COUNTY_FIPS = {
    "Cook": "031",
    "LaSalle": "099",
    "DuPage": "043",
    "Kane": "089",
    "Kendall": "093",
    "Lake": "097",
    "McHenry": "111",
    "Winnebago": "201",
    "Will": "197",
    "Ogle": "141",
    "Stephenson": "177",
    "Carroll": "015",
    "DeKalb": "037",
    # The pass-6 tranche (2026-08-01): eight counties whose sources the
    # validation pass verified publishable, shipped together.
    "Grundy": "063",
    "Livingston": "105",
    "Logan": "107",
    "McLean": "113",
    "Sangamon": "167",
    "Madison": "119",
    "St. Clair": "163",
    "Rock Island": "161",
}

# Office classification. HEAD is the single head of government; BOARD is the
# governing body's seats; OFFICERS are the other municipality-wide elected
# officers. An office name not listed here still ships (under officers) and
# prints a warning — new office types get a human's attention, never a silent
# drop.
# "acting president" is a sitting trustee wearing the gavel (Spaulding,
# Williamsville, Worden print the office exactly that way); the same person's
# trustee row legitimately coexists with it, so the scrapers' head-duplicate
# rules already exempt it.
HEAD_OFFICES = {"mayor", "president", "village president", "acting president"}
BOARD_OFFICES = {"trustee", "alderperson", "alderman", "alderwoman",
                 "council member", "commissioner", "councilman", "councilwoman",
                 "councilperson"}
OFFICER_OFFICES = {"clerk", "treasurer", "village clerk", "city clerk",
                   "taxpayer advocate", "collector", "supervisor",
                   # Oak Grove (Rock Island) elects one officer to both
                   "clerk/treasurer",
                   # appointed staff LaSalle prints beside the elected officers;
                   # the record carries appointed=True so a card never implies
                   # these were elected
                   "deputy clerk", "administrator", "village administrator",
                   "city administrator", "city manager", "village manager",
                   "manager", "superintendent", "superintendent of public works"}

# Per-county floors: deliberate under-tolerances against the verified 2026-07
# live values (Cook 128 municipalities / 1,035 governing records / 128 heads;
# Will 34 / 303 / 34). A real coverage loss fails the build and leaves the last
# good file in place; ordinary turnover does not.
COUNTY_FLOORS = {
    "Cook": {"municipalities": 120, "members": 900, "heads": 120},
    "Will": {"municipalities": 30, "members": 260, "heads": 30},
    # LaSalle, the third full-governing-body source and the first county outside
    # the metro (2026-07 live: 26 municipalities / 206 officials / 26 heads).
    "LaSalle": {"municipalities": 22, "members": 170, "heads": 22},
    # Winnebago, the fourth full-governing-body source (2026-07 live: 11
    # municipalities / 84 officials / 9 heads). HEADS IS BELOW MUNICIPALITIES ON
    # PURPOSE: WinGIS publishes no mayor/president layer for Loves Park or
    # Machesney Park, only their council seats, so a floor of 11 heads would fail
    # on correct data. See winnebago_municipal_officials_scraper.py.
    "Winnebago": {"municipalities": 10, "members": 75, "heads": 8},
    # The five mayor-level counties (2026-07 live values in parentheses). Their
    # sources publish no trustees, so `members` counts the head plus the elected
    # clerk/treasurer rows only — a floor equal to the head count would pass on
    # a run that silently lost every officer.
    "DuPage": {"municipalities": 32, "members": 32, "heads": 32},        # 36 / 36 / 36
    "Kane": {"municipalities": 26, "members": 50, "heads": 26},          # 29 / 58 / 29
    "McHenry": {"municipalities": 26, "members": 48, "heads": 24},       # 30 / 55 / 30
    "Kendall": {"municipalities": 12, "members": 28, "heads": 12},       # 14 / 34 / 14
    # Lake publishes NO officeholder names (rule-4 honesty floor), so its
    # member/head floors are 0 BY DESIGN — the municipality count is the real
    # guard. See lake_municipal_officials_scraper.py.
    "Lake": {"municipalities": 48, "members": 0, "heads": 0},            # 55 / 0 / 0
    # The northern frontier (2026-07 live values in parentheses). Ogle and
    # Stephenson are full-governing-body sources; Carroll is mayor-level, so its
    # `members` counts the head plus the clerk only.
    "Ogle": {"municipalities": 11, "members": 90, "heads": 11},          # 13 / 110 / 13
    # DeKalb, the sixth full-governing-body source, and the only one whose
    # document gives every seat's NEXT ELECTION date (2026-07 live: 14 / 118 /
    # 14). Two rows the scraper drops by rule are already excluded from that
    # count — a seat published as "Vacant" and a trustee row duplicating the
    # village president.
    "DeKalb": {"municipalities": 12, "members": 100, "heads": 12},       # 14 / 118 / 14
    # HEADS IS BELOW MUNICIPALITIES ON PURPOSE for Stephenson: the county's page
    # lists no president for Dakota (one Dakota row carries a name and a blank
    # office cell), so a floor of 10 heads would fail on correct data. Freeport
    # is not counted here at all — the county page omits it and the city's own
    # payload supplies it through --enrich.
    "Stephenson": {"municipalities": 9, "members": 70, "heads": 7},      # 10 / 82 / 9
    # Carroll's whole county is seven municipalities, so the floors sit only
    # one or two under the full set. Thomson's president is vacant, which is why
    # heads is two under the municipality count rather than one.
    "Carroll": {"municipalities": 6, "members": 11, "heads": 5},         # 7 / 13 / 6
    # The pass-6 tranche (2026-08-01 live values in parentheses), all
    # full-governing-body sources — each scraper carries its own tighter
    # per-source floors, so these are the coarse back-stops.
    "Grundy": {"municipalities": 15, "members": 110, "heads": 15},       # 17 / 133 / 17
    "Livingston": {"municipalities": 14, "members": 120, "heads": 14},   # 16 / 153 / 16
    "Logan": {"municipalities": 10, "members": 75, "heads": 10},         # 11 / 92 / 11
    # McLean covers ONLY its three ward-electing cities (the county-wide
    # source is a JS-locked Airtable interface — see the scraper), so its
    # floors describe three municipalities, not a county sweep.
    "McLean": {"municipalities": 3, "members": 22, "heads": 3},          # 3 / 26 / 3
    "Sangamon": {"municipalities": 22, "members": 170, "heads": 20},     # 26 / 208 / 26
    "Madison": {"municipalities": 24, "members": 190, "heads": 24},      # 28 / 241 / 28
    "St. Clair": {"municipalities": 22, "members": 190, "heads": 22},    # 26 / 247 / 26
    "Rock Island": {"municipalities": 13, "members": 100, "heads": 13},  # 15 / 122 / 15
}
# Merged floor across all counties supplied. Cook + Will resolve to 156 unique
# municipalities (6 of Will's 34 are shared with Cook); the pre-tranche
# counties resolve to ~270, and the pass-6 tranche (Grundy, Livingston, Logan,
# McLean's three ward cities, Sangamon, Madison, St. Clair, Rock Island) adds
# ~140 more after cross-county dedupe.
MIN_TOTAL_MUNICIPALITIES = 380

# ---------------------------------------------------------------------------
# Preserving a blocked source's last-good entries.
#
# Several sources refuse GitHub's runner IPs outright — McHenry and Kendall
# block every rung including the Archive's crawler, and DuPage/Joliet 403 the
# datacenter ranges while answering a developer machine. Gating the build on
# all ten therefore froze the whole roster indefinitely: one permanently
# blocked county withheld every OTHER county's turnover too, which is the
# opposite of the isolation the workflow set out to provide.
#
# So a missing source no longer withdraws its data — it carries forward what is
# already shipped, and the run says exactly which sources were served that way.
# A preserved county's entries are re-inserted through the same cross-county
# precedence as a fresh build; a preserved city payload is re-applied through
# merge_contact, so it can still only FILL fields the county left empty and can
# never resurrect a seat-holder the county has since replaced.
#
# Cook and Will are not preservable: they are the only two full-governing-body
# sources, so building without either would silently ship a roster of mayors
# where councils used to be. If one of them is down, the run must fail.
REQUIRED_COUNTIES = ("Cook", "Will")
PRESERVABLE = {
    # LaSalle is a full-governing-body source like Cook and Will, but unlike them
    # it is NOT in REQUIRED_COUNTIES: Cook and Will are required because losing
    # either would silently replace councils that are already shipped with
    # mayors. LaSalle carries its own 26 municipalities and nothing else depends
    # on it, so a fetch failure should carry its last-good entries forward, not
    # fail every other county's turnover.
    "lasalle": {"kind": "county", "county": "LaSalle"},
    "winnebago": {"kind": "county", "county": "Winnebago"},
    "dupage": {"kind": "county", "county": "DuPage"},
    "kane": {"kind": "county", "county": "Kane"},
    "mchenry": {"kind": "county", "county": "McHenry"},
    "kendall": {"kind": "county", "county": "Kendall"},
    "lake": {"kind": "county", "county": "Lake"},
    "ogle": {"kind": "county", "county": "Ogle"},
    "stephenson": {"kind": "county", "county": "Stephenson"},
    "carroll": {"kind": "county", "county": "Carroll"},
    "dekalb": {"kind": "county", "county": "DeKalb"},
    "grundy": {"kind": "county", "county": "Grundy"},
    "livingston": {"kind": "county", "county": "Livingston"},
    "logan": {"kind": "county", "county": "Logan"},
    "mclean": {"kind": "county", "county": "McLean"},
    "sangamon": {"kind": "county", "county": "Sangamon"},
    "madison": {"kind": "county", "county": "Madison"},
    "st-clair": {"kind": "county", "county": "St. Clair"},
    "rock-island": {"kind": "county", "county": "Rock Island"},
    # City payloads name the municipalities they cover, because the payload
    # that would have named them is precisely what is missing. Each list is
    # guarded by its scraper's own floor, so a drift here fails there first.
    "freeport": {"kind": "enrich", "places": ["City of Freeport"]},
    "will-cities": {"kind": "enrich",
                    "places": ["City of Crest Hill", "City of Lockport",
                               "City of Wilmington"]},
    "skokie": {"kind": "enrich", "places": ["Village of Skokie"]},
    "joliet": {"kind": "enrich", "places": ["City of Joliet"]},
}

# Tie-break for a municipality claimed by two counties, applied only AFTER
# depth (see pick_entry). Both directories describe the same government, so
# this is a freshness call, not a correctness one: Cook's is a live API
# reflecting each election as it is certified, Will's is an annually
# republished directory.
# DeKalb sits ahead of LaSalle for the one municipality both name: Somonauk.
# Depth cannot separate them — each publishes the village's full board, and
# each names the same five sitting trustees — so this is the tie-break doing its
# job. DeKalb wins it because the village hall is in DeKalb County (LaSalle
# lists Somonauk because the village extends across the line) and because
# DeKalb's book additionally dates every seat's next election.
# Grundy sits ahead of Livingston for the one municipality both publish in
# full: Dwight. The two 2026 editions disagree on one trustee seat (Grundy:
# Randy Irvin; Livingston: Debra Karch) and Grundy's booklet is a month
# fresher (July vs June 2026) and dates every seat's term — the freshness
# call, made explicit. LaSalle already precedes both, which settles Streator
# (hall in LaSalle) the same way.
COUNTY_PRECEDENCE = ["Cook", "Will", "DeKalb", "LaSalle", "Winnebago", "Ogle",
                     "Stephenson", "Grundy", "Livingston", "Logan", "McLean",
                     "Sangamon", "Madison", "St. Clair", "Rock Island",
                     "DuPage", "Kane", "Kendall", "McHenry",
                     "Carroll", "Lake"]


def _fold(text):
    """Shared tail of both normalizers: expand "Mt.", then letters only.

    Carroll's clerk writes its county seat "Mt. Carroll"; Census writes
    "Mount Carroll". Expanded rather than aliased because it is an abbreviation
    of one word, not a different name, and every Illinois place spelled "Mt." on
    some source is "Mount" in the Census file.
    """
    text = re.sub(r"^Mt\.?(?=\s|$)", "Mount", (text or "").strip(), flags=re.I)
    return re.sub(r"[^A-Z]", "", text.upper())


def norm_census_place(name):
    """Normalize a name from the Census reference file, which SUFFIXES the form.

    "Calumet City city" -> CALUMETCITY, "Rock City village" -> ROCKCITY.
    """
    return _fold(re.sub(r"\s+(village|city|town|CDP)$", "", (name or "").strip(),
                        flags=re.I))


def norm_place(name):
    """Normalize a name from a county/city SOURCE, which PREFIXES the form.

    The two sides label the government form on opposite ends — the clerk writes
    "City of Calumet City", Census writes "Calumet City city" — so each side
    gets its own strip. Doing both here is what this function used to do, and it
    was wrong in both directions: it reduced the clerk's "City of Calumet City"
    to "Calumet", and for a source that publishes BARE names (Stephenson's
    county page, Winnebago's GIS layers) it ate the second word of "Rock City"
    and left "Rock", which matches no Census place at all.
    """
    text = (name or "").strip()
    # "United City of Yorkville" is Yorkville's legal name and the form its
    # county clerk prints; Census lists it as "Yorkville city". The optional
    # qualifier keeps that join working without a per-place alias.
    return _fold(re.sub(r"^(?:united\s+)?(village|city|town)\s+of\s+", "", text,
                        flags=re.I))


def load_places(path):
    """-> ({county_fips: {norm: geoid}}, {norm: set(geoid)}, {geoid: legal name}).

    The third map is the Census's own "<Name> <village|city|town>" wording,
    re-ordered into the "Village of <Name>" form the app's card labels read.
    """
    if not os.path.exists(path):
        print("FATAL: Census place reference missing at %s" % path, file=sys.stderr)
        sys.exit(1)
    by_county = defaultdict(dict)
    statewide = defaultdict(set)
    legal = {}
    with open(path, encoding="utf-8-sig") as f:
        rows = [line.rstrip("\n").split("|") for line in f if line.strip()]
    header = rows[0]
    for row in rows[1:]:
        if len(row) != len(header):
            continue
        rec = dict(zip(header, row))
        if rec.get("TYPE") != "INCORPORATED PLACE":
            continue
        key = norm_census_place(rec["PLACENAME"])
        geoid = "17" + rec["PLACEFP"]
        by_county[rec["COUNTYFP"]][key] = geoid
        statewide[key].add(geoid)
        form = re.search(r"\s+(village|city|town)$", rec["PLACENAME"], flags=re.I)
        if form:
            legal[geoid] = "%s of %s" % (form.group(1).capitalize(),
                                         rec["PLACENAME"][:form.start()].strip())
    if not statewide:
        print("FATAL: no incorporated places parsed from %s" % path, file=sys.stderr)
        sys.exit(1)
    return by_county, statewide, legal


# Places incorporated AFTER the committed Census 2020 reference file. Cahokia
# Heights formed in May 2021 from Cahokia, Alorton and Centreville; the 2020
# file still lists its three predecessors and not it, while the app's
# TIGERweb municipality layer serves the new city under this GEOID (verified
# live 2026-08-01). Keyed by norm_place() form.
POST_2020_GEOIDS = {
    "CAHOKIAHEIGHTS": "1710373",
}


def resolve_geoid(name, county, by_county, statewide):
    key = norm_place(name)
    if not key:
        return None, "unparseable name"
    if key in POST_2020_GEOIDS:
        return POST_2020_GEOIDS[key], None
    fips = COUNTY_FIPS.get(county)
    if fips and key in by_county.get(fips, {}):
        return by_county[fips][key], None
    matches = statewide.get(key) or set()
    if len(matches) == 1:
        return next(iter(matches)), None
    if not matches:
        return None, "no Census place matches"
    return None, "ambiguous statewide (%s)" % ", ".join(sorted(matches))


def classify(office):
    o = (office or "").strip().lower()
    if o in HEAD_OFFICES:
        return "head"
    if o in BOARD_OFFICES:
        return "board"
    if o in OFFICER_OFFICES:
        return "officer"
    return None


def election_year(value):
    """A four-digit year from either shape the sources use.

    Cook publishes ISO datetimes ("2029-04-01T00:00:00-05:00"), Will and
    Kendall bare years ("2027"). Anything else is None rather than a guess.
    """
    match = re.match(r"^(\d{4})(?:-\d{2}-\d{2})?", str(value or "").strip())
    return match.group(1) if match else None


def district_sort_key(member):
    """Ward 1 < Ward 2 < Ward 10; unnumbered seats sort last, then by name."""
    district = member.get("district") or ""
    nums = re.findall(r"\d+", district)
    return (0, int(nums[0])) if nums else (1, 0), member.get("name") or ""


def office_block(records):
    """One municipality-level office block from the shared contact fields."""
    rec = records[0]
    street = rec.get("office_address")
    city = rec.get("office_city")
    state = rec.get("office_state")
    zipcode = rec.get("office_zip")
    locality = " ".join(p for p in (city, state) if p)
    if locality and zipcode:
        locality = "%s %s" % (locality, zipcode)
    address = ", ".join(p for p in (street, locality) if p) or None
    block = {}
    if address:
        block["address"] = address
    phone = format_phone(rec.get("office_phone"))
    if phone:
        block["phone"] = phone
    if rec.get("office_email"):
        block["email"] = rec["office_email"]
    return block


def format_phone(phone):
    """10 digits -> 708-385-6902, the shape the card's phone helper renders.

    cardPhoneLink() prints the stored string verbatim (only swapping hyphens
    for non-breaking ones), so an unformatted run of digits would ship as
    '7083856902'. Anything that isn't a plain US number is left untouched
    rather than reshaped into a guess.
    """
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return phone
    return "%s-%s-%s" % (digits[:3], digits[3:6], digits[6:])


def normalize_website(url):
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def build_county(payload, by_county, statewide, legal, warnings, apply_floors=True):
    county = payload.get("county") or "?"
    grouped = defaultdict(list)
    for rec in payload.get("officials") or []:
        if rec.get("jurisdiction"):
            grouped[rec["jurisdiction"]].append(rec)

    entries = {}
    for jurisdiction, records in grouped.items():
        geoid, problem = resolve_geoid(jurisdiction, county, by_county, statewide)
        if geoid is None:
            print("FATAL: cannot resolve '%s' (%s County) to a Census place GEOID — %s"
                  % (jurisdiction, county, problem), file=sys.stderr)
            sys.exit(1)

        head = None
        board = []
        officers = []
        for rec in records:
            name = rec.get("name")
            if not name:
                continue
            kind = classify(rec.get("office"))
            person = {"name": name, "role": rec.get("office")}
            if rec.get("district"):
                person["district"] = rec["district"]
            if rec.get("appointed"):
                person["appointed"] = True
            # Per-PERSON contact, carried only where the source publishes it per
            # member (McHenry prints a direct line or office e-mail for a few
            # officials). The municipality-level hall contact below is never
            # copied onto a person — that would imply a direct line that the
            # source does not publish.
            if rec.get("person_phone"):
                person["phone"] = format_phone(rec["person_phone"])
            if rec.get("person_email"):
                person["email"] = rec["person_email"]
            # When this seat is next on the ballot, where the source publishes
            # it (Cook: 100% of records). Terms are STAGGERED — 103 of Cook's
            # 104 village boards mix two cycles — so this belongs on the person,
            # not the card. Stored as the year; the card hides a year already
            # past rather than calling it "next".
            # Term information, labelled as its own source labels it rather
            # than normalised into one field: Cook publishes the NEXT election
            # date, Will the year a term EXPIRES, Kendall the date an officer
            # was last ELECTED. Collapsing three different facts into one label
            # would state something none of them says.
            next_election = election_year(rec.get("next_election"))
            if next_election:
                person["nextElection"] = next_election
            term_expires = election_year(rec.get("term_expires"))
            if term_expires:
                person["termExpires"] = term_expires
            # Cook publishes BOTH a last-elected and a next-election date; the
            # next election is the more useful of the two and the card shows it,
            # so the last-elected date is kept only where it is the only term
            # fact a source gives (Kendall). Storing both would put ~1,000
            # fields in the file that nothing reads.
            last_elected = election_year(rec.get("last_elected"))
            if last_elected and not next_election:
                person["lastElected"] = last_elected
            if kind == "head":
                if head is not None:
                    print("FATAL: %s resolved two heads of government (%s, %s)"
                          % (jurisdiction, head["name"], name), file=sys.stderr)
                    sys.exit(1)
                head = person
            elif kind == "board":
                board.append(person)
            else:
                if kind is None:
                    warnings.append("unclassified office '%s' in %s — shipped under officers"
                                    % (rec.get("office"), jurisdiction))
                officers.append(person)

        board.sort(key=district_sort_key)
        officers.sort(key=lambda m: (m.get("role") or "", m.get("name") or ""))

        # The card's hall and body labels read the legal form off this name
        # ("Village of Alsip" -> "Village Hall"), so a source that publishes
        # BARE names — Stephenson's county page, Winnebago's GIS layers — would
        # otherwise land on the generic "Municipal Hall". The form comes from
        # the Census reference file's own designation ("Rock City village"),
        # not from an inference about the place. A source that already states
        # the form keeps its own wording: "United City of Yorkville" is the
        # city's legal name and the Census's plain "City of Yorkville" would be
        # a downgrade, not a fix.
        entry = {"name": legal.get(geoid, jurisdiction)
                 if not re.match(r"^(?:united\s+)?(village|city|town)\s+of\s+",
                                 jurisdiction, flags=re.I) else jurisdiction,
                 "county": county}
        # Chicago's 50 ward seats are published under a different jurisdiction
        # type and answered by the `ward` layer, so this card points there
        # instead of implying the city has no council.
        if any(rec.get("ward_seats_elsewhere") for rec in records):
            entry["councilOnWardLayer"] = True
        if head:
            entry["head"] = head
        if board:
            entry["board"] = board
        if officers:
            entry["officers"] = officers
        office = office_block(records)
        if office:
            entry["office"] = office
        website = normalize_website(records[0].get("website"))
        if website:
            entry["url"] = website
        entry["sourceUrl"] = payload.get("directory_url") or records[0].get("source_url")
        entries[geoid] = entry

    floors = COUNTY_FLOORS.get(county) if apply_floors else None
    if floors:
        n_munis = len(entries)
        n_members = sum(len(e.get("board") or []) + len(e.get("officers") or [])
                        + (1 if e.get("head") else 0) for e in entries.values())
        n_heads = sum(1 for e in entries.values() if e.get("head"))
        for label, actual, floor in (("municipalities", n_munis, floors["municipalities"]),
                                     ("members", n_members, floors["members"]),
                                     ("heads of government", n_heads, floors["heads"])):
            if actual < floor:
                print("FATAL: %s County resolved %d %s, floor is %d — refusing to write"
                      % (county, actual, label, floor), file=sys.stderr)
                sys.exit(1)
    return entries


def name_tokens(name):
    """Comparable name parts: lowercase alpha words, nicknames included."""
    return [t for t in re.split(r"[^A-Za-z]+", str(name or "").lower()) if t]


def same_person(a, b):
    """Match a city site's name against the clerk's, allowing nicknames.

    Surnames must agree and at least one given/nick name must overlap, so
    "Nathaniel "Nate" Albert" meets "Nate Albert" and "Angelo Sante Deserio"
    meets "Angelo Deserio", while two different Smiths never merge.
    """
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    given_a, given_b = ta[:-1], tb[:-1]
    if not given_a or not given_b:
        return False
    for x in given_a:
        for y in given_b:
            # Equal, or a truncation of the other ("Chris"/"Christine",
            # "Tom"/"Thomas"). Nicknames the clerk prints in quotes already
            # appear as their own token, so "Nate" meets
            # "Nathaniel \u201cNate\u201d Albert" by equality. Nicknames that
            # are NOT truncations ("Joe"/"Joseph" — Joseph is "jos…") fall to
            # the surname tier in merge_contact rather than a nickname table,
            # which would be guesswork dressed as data.
            if x == y:
                return True
            if len(x) >= 3 and len(y) >= 3 and (x.startswith(y) or y.startswith(x)):
                return True
    return False


def people_of(entry):
    return ([entry["head"]] if entry.get("head") else []) + \
        (entry.get("board") or []) + (entry.get("officers") or [])


def merge_contact(existing, addition, warnings):
    """Fill per-person fields the county left empty, from a municipality's own site.

    The county clerk's directory stays the roster of record: this never adds a
    seat-holder, renames one, or changes a role, and never overwrites a value
    the county already published — an unmatched name is reported instead,
    because a mismatch means one of the two sources is out of date and that is
    a human's call.

    Contact is the usual payload. DISTRICT is the exception that earns its
    keep: Skokie's four district trustees and two at-large trustees are all
    published municipality-wide by the Clerk, with no district on any of them,
    while Cook GIS carries the four district polygons — so the seats existed on
    the map with nobody attached. The village publishes the assignment itself,
    which is the authority on its own districting.
    """
    hall = existing.get("office") or {}
    for person in people_of(addition):
        matches = [c for c in people_of(existing)
                   if same_person(c.get("name"), person.get("name"))]
        if not matches:
            # Second tier: an unambiguous surname inside one small council is a
            # safe join even when given names differ by nickname. Logged so the
            # looser rule is always visible in the build output.
            surname = (name_tokens(person.get("name")) or [None])[-1]
            by_surname = [c for c in people_of(existing)
                          if (name_tokens(c.get("name")) or [None])[-1] == surname]
            if surname and len(by_surname) == 1:
                matches = by_surname
                warnings.append("%s: matched '%s' to '%s' on surname alone"
                                % (existing.get("name"), person.get("name"),
                                   by_surname[0].get("name")))
        if len(matches) > 1:
            # Two seat-holders could be this person: attributing a phone to the
            # wrong one is worse than shipping none.
            warnings.append("%s: '%s' matches %d people in the county directory — "
                            "ambiguous, contact not applied"
                            % (existing.get("name"), person.get("name"), len(matches)))
            continue
        match = matches[0] if matches else None
        if match is None:
            warnings.append("%s: '%s' is on the city site but not in the county "
                            "directory — not added (clerk is the roster of record)"
                            % (existing.get("name"), person.get("name")))
            continue
        # A district the county never published (Skokie). Filled, never
        # overwritten, and logged so the looser field is visible in the build.
        if person.get("district") and not match.get("district"):
            match["district"] = person["district"]
            warnings.append("%s: district '%s' for %s came from the municipality's "
                            "own site (the county published none)"
                            % (existing.get("name"), person["district"],
                               match.get("name")))
        phone = person.get("phone")
        # A "direct" number that is just the main line is not a direct line.
        if phone and phone != hall.get("phone") and not match.get("phone"):
            match["phone"] = phone
        email = person.get("email")
        if email and email != hall.get("email") and not match.get("email"):
            match["email"] = email


def entry_depth(entry):
    """How much of the governing body a source actually names.

    2 = full body (a head plus the board), 1 = head only, 0 = contact only.
    This is what decides a cross-county municipality, NOT which county the
    place is mostly in: a village that straddles Cook and Will should show the
    board wherever one is published.
    """
    if entry.get("board"):
        return 2
    if entry.get("head"):
        return 1
    return 0


def describe_depth(entry):
    return {2: "full governing body", 1: "head of government only",
            0: "contact only"}[entry_depth(entry)]


def pick_entry(a, b):
    """-> (kept, dropped) for one municipality claimed by two counties."""
    if entry_depth(a) != entry_depth(b):
        return (a, b) if entry_depth(a) > entry_depth(b) else (b, a)
    rank = {c: i for i, c in enumerate(COUNTY_PRECEDENCE)}
    fallback = len(COUNTY_PRECEDENCE)
    if rank.get(a["county"], fallback) <= rank.get(b["county"], fallback):
        return a, b
    return b, a


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("inputs", nargs="+", help="per-county scraper output JSON files")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--places", default=PLACES_FILE)
    parser.add_argument("--enrich", nargs="*", default=[],
                        help="city-site payloads: add per-seat contact to the "
                             "county roster, and supply municipalities the county "
                             "source omits entirely")
    parser.add_argument("--preserve", metavar="ROSTER_JSON",
                        help="the currently shipped roster, read to carry "
                             "forward the sources named by --preserved")
    parser.add_argument("--preserved", nargs="*", default=[], metavar="SOURCE",
                        help="sources whose scrape failed this run (%s); their "
                             "shipped entries are carried forward instead of "
                             "being dropped" % ", ".join(sorted(PRESERVABLE)))
    args = parser.parse_args()

    unknown = [s for s in args.preserved if s not in PRESERVABLE]
    if unknown:
        print("FATAL: --preserved names unknown source(s) %s; known: %s"
              % (", ".join(unknown), ", ".join(sorted(PRESERVABLE))), file=sys.stderr)
        sys.exit(1)
    if args.preserved and not args.preserve:
        print("FATAL: --preserved needs --preserve <shipped roster> to read from",
              file=sys.stderr)
        sys.exit(1)

    shipped = {}
    if args.preserve:
        with open(args.preserve) as f:
            shipped = json.load(f)

    by_county, statewide, legal = load_places(args.places)

    roster = {}
    warnings = []
    supplied_counties = set()

    def absorb(geoid, entry):
        """Merge one entry into the roster under cross-county precedence."""
        if geoid not in roster:
            roster[geoid] = entry
            return
        keep, drop = pick_entry(roster[geoid], entry)
        print("NOTE: %s (%s) is listed by both %s and %s County — keeping the "
              "%s entry (%s)" % (geoid, keep["name"], roster[geoid]["county"],
                                 entry["county"], keep["county"],
                                 describe_depth(keep)), file=sys.stderr)
        if drop.get("board") and not keep.get("board"):
            print("FATAL: dropped entry for %s had a board and the kept one "
                  "does not — precedence is wrong" % geoid, file=sys.stderr)
            sys.exit(1)
        roster[geoid] = keep

    for path in args.inputs:
        with open(path) as f:
            payload = json.load(f)
        supplied_counties.add(payload.get("county"))
        entries = build_county(payload, by_county, statewide, legal, warnings)
        for geoid, entry in entries.items():
            absorb(geoid, entry)

    # A full-body county is never preserved (see PRESERVABLE) — losing one would
    # turn councils into mayors across a third of the metro without any single
    # count floor noticing, since the municipalities all remain.
    for county in REQUIRED_COUNTIES:
        if county not in supplied_counties:
            print("FATAL: %s County is required and was not supplied — it is one "
                  "of the two full-governing-body sources, so building without it "
                  "would ship heads of government where councils belong"
                  % county, file=sys.stderr)
            sys.exit(1)

    # Carry forward a blocked county BEFORE the city payloads run, so the
    # enrichment step still refines it exactly as it would a fresh scrape.
    preserved_counts = {}
    for source in args.preserved:
        spec = PRESERVABLE[source]
        if spec["kind"] != "county":
            continue
        if spec["county"] in supplied_counties:
            print("FATAL: --preserved names %s but its county (%s) WAS supplied — "
                  "refusing to overwrite a fresh scrape with shipped data"
                  % (source, spec["county"]), file=sys.stderr)
            sys.exit(1)
        kept = 0
        for geoid, entry in shipped.items():
            if entry.get("county") != spec["county"]:
                continue
            absorb(geoid, json.loads(json.dumps(entry)))
            kept += 1
        if not kept:
            print("FATAL: --preserved %s carried forward 0 entries — the shipped "
                  "roster has none tagged %s, so this would silently drop the "
                  "county" % (source, spec["county"]), file=sys.stderr)
            sys.exit(1)
        preserved_counts[source] = kept

    # City-site payloads run last: they refine what the counties established.
    for path in args.enrich:
        with open(path) as f:
            payload = json.load(f)
        entries = build_county(payload, by_county, statewide, legal, warnings,
                               apply_floors=False)
        for geoid, entry in entries.items():
            if geoid not in roster:
                print("NOTE: %s (%s) is absent from its county's directory — "
                      "supplied by the city's own site" % (geoid, entry["name"]),
                      file=sys.stderr)
                roster[geoid] = entry
            else:
                merge_contact(roster[geoid], entry, warnings)

    # A blocked city payload is re-applied from what is shipped, through the
    # SAME merge_contact the live payload would have used. That matters: the
    # county's fresh entry stays the roster of record, so a seat-holder the
    # county has since replaced is not resurrected — only fields the county
    # left empty are filled, and an unmatched name is reported as a warning.
    for source in args.preserved:
        spec = PRESERVABLE[source]
        if spec["kind"] != "enrich":
            continue
        wanted = {norm_place(p) for p in spec["places"]}
        found = set()
        for geoid, entry in shipped.items():
            key = norm_place(entry.get("name"))
            if key not in wanted:
                continue
            found.add(key)
            if geoid not in roster:
                # The county source omits this municipality entirely and the
                # city payload was the only thing supplying it.
                print("NOTE: %s (%s) is absent from its county's directory and "
                      "its city payload is blocked — carried forward as shipped"
                      % (geoid, entry.get("name")), file=sys.stderr)
                roster[geoid] = json.loads(json.dumps(entry))
                continue
            merge_contact(roster[geoid], json.loads(json.dumps(entry)), warnings)
        missing = wanted - found
        if missing:
            print("FATAL: --preserved %s expected %d municipalities in the "
                  "shipped roster and %d are absent — the place list in "
                  "PRESERVABLE has drifted from what the scraper covers"
                  % (source, len(wanted), len(missing)), file=sys.stderr)
            sys.exit(1)
        preserved_counts[source] = len(found)

    # The Skokie class: a municipality whose seats the ward layer maps, but
    # whose roster carries no districted seat, renders a district polygon with
    # nobody attached. Warn rather than fail — a municipality may legitimately
    # have ward geometry drawn before it takes effect — but never let it pass
    # unseen again.
    coverage_path = os.path.join(args.out_dir, "municipal-ward-coverage.json")
    if os.path.exists(coverage_path):
        with open(coverage_path) as f:
            covered = json.load(f)
        for feature in (covered.get("features") or []):
            geoid = str((feature.get("properties") or {}).get("geoid") or "")
            entry = roster.get(geoid)
            if not entry or not entry.get("board"):
                continue
            if not any(m.get("district") and
                       not re.match(r"^at[\s-]*large$", str(m["district"]), re.I)
                       for m in entry["board"]):
                warnings.append("%s has ward geometry but no districted seat in the "
                                "roster — its ward card will name nobody"
                                % entry.get("name"))

    if len(roster) < MIN_TOTAL_MUNICIPALITIES:
        print("FATAL: resolved %d municipalities, floor is %d — refusing to write"
              % (len(roster), MIN_TOTAL_MUNICIPALITIES), file=sys.stderr)
        sys.exit(1)

    for warning in warnings:
        print("WARNING: %s" % warning, file=sys.stderr)

    out_path = os.path.join(args.out_dir, "municipal-officials.json")
    with open(out_path, "w") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    n_board = sum(len(e.get("board") or []) for e in roster.values())
    n_seats = sum(1 for e in roster.values() for m in (e.get("board") or []) if m.get("district"))
    print("wrote %s: %d municipalities, %d board members (%d ward/district seats)"
          % (out_path, len(roster), n_board, n_seats), file=sys.stderr)
    if preserved_counts:
        # Printed so the run log and the PR body both name every source that did
        # NOT refresh — a preserved county is data that is shipped but no longer
        # verified this week, and that has to stay visible.
        print("PRESERVED (blocked this run, carried forward from the shipped "
              "roster): %s" % ", ".join("%s %d" % (s, n) for s, n
                                        in sorted(preserved_counts.items())),
              file=sys.stderr)


if __name__ == "__main__":
    main()

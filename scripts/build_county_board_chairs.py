#!/usr/bin/env python3
"""
Resolve scripts/isbe_county_officers_scraper.py's raw output into
data/source/isbe-county-board-chairs.json — one record per Illinois county
whose board chair the State Board of Elections names, keyed by the repo's
county slug ("adams", "jo-daviess", "st-clair", "dewitt").

WHY NOTHING HERE REACHES A CARD. This pipeline was built to close a real gap:
the COUNTY card answers everywhere in Illinois and already names the county
clerk statewide (il-county-clerks.json), but it names a board chair only where
some county-specific scraper has been written. ISBE names a chair in all 102
counties at once, which looked like forty-six counties' worth of coverage for
one build. THE BUILD IS WHAT REFUTED THAT, and the refutation is the reason
this file exists at all:

    Of the 56 counties where this app ships its own roster and a comparison is
    therefore possible, ISBE names a DIFFERENT chair in 16 — and in the ten
    checked live against the county's own current board page (Ogle, Grundy,
    Marshall, Iroquois, Logan, Shelby, Greene, Moultrie, Carroll, McDonough),
    the person ISBE names appears NOWHERE on it while the app's name is there
    with the chair title. Not two sources differing: one source stale.

Twenty-nine per cent wrong is disqualifying for a name printed under "who
represents you", and no badge repairs it — the document's own "Last Updated
Monday, December 15, 2025" stamp is precisely what the 16 disprove, so
rendering `asOf` beside the name would assert a currency the source does not
have. THE REPO ALREADY HAS A RULE FOR THIS EXACT SHAPE. Coles County's board
layer publishes an `Official` column that gets six of twelve names wrong, and
the answer there was not to ship it with a caveat — it is read NOWHERE, and
Coles's people come from the county's board page instead. Freeport's stale
`Alderperson` column and McLean's stale `REPNAME` column are read nowhere for
the same reason. ISBE's chair column joins them.

So this builder writes OUTSIDE data/app, and its output is a measurement:
proof of what the source is worth, kept reproducible so the claim can be
re-tested rather than re-argued, and so a future reader who rediscovers this
directory finds the count instead of repeating the work. What it must never
become is a roster.

TWO CLAIMS THAT DID NOT SURVIVE CHECKING, recorded because both are the kind a
reader would otherwise make again. (1) The gap this would close is NOT limited
to well-served counties — the County card is statewide, so a chair would have
surfaced in all 46 — which makes the coverage case strong and the reliability
case decisive on its own. (2) `winnebago-county-board-members.json` carries no
`name` field, which reads like a card that names nobody; it is not. Winnebago's
names ride the WinGIS boundary 20/20 and that file is deliberately contact-only
enrichment (build_winnebago_county_board_roster.py's docstring says so). Its
`unchecked` verdict here is therefore a false negative: that county IS
checkable, through geometry this cross-check does not read.

WHAT STAYS OPEN, for anyone picking this up. Where the name AGREES with a
county's own publication (40 counties), the row is by definition not stale, so
its e-mail/phone/office could enrich a chair this app already names from the
county. That is a different and defensible build — contact only, never the
name — and it is recorded in the guidebook's backlog rather than done here.

THREE THINGS IT IS NOT, EACH MEASURED RATHER THAN ASSUMED.

  1. IT IS NOT A ROSTER AND CANNOT BECOME ONE. The 107-page directory contains
     the string "County Board Member" ZERO times and the word "District" ZERO
     times (isbe_county_officers_scraper.py's docstring carries the count). One
     row per office; the board's only row is its chair. A county's members
     still arrive the way they always have — from the county.

  2. IT IS NOT CURRENT, AND MUST NEVER OVERRIDE A COUNTY'S OWN PUBLICATION.
     This is the finding above, stated as the mechanism that produced it. The
     document stamps itself "Last Updated Monday, December 15, 2025"; that
     stamp is carried on every record as `asOf` so the measurement is
     self-dating, not so a card can print it. Every record also carries a
     `crossCheck` verdict against the rosters this app already ships, and it
     is the verdict distribution — not any single row — that is the output
     anyone should read:

         agrees     the county's own shipped roster marks this person chair
                    (or lists them as a member and marks no chair at all)
         differs    the county's own roster marks somebody else, or does not
                    list this person at all — the county is right; see above
         unchecked  this app ships no roster for that county. NOT a licence to
                    render: it means the comparison could not be made, and the
                    16 `differs` are the estimate of what it would have found

     The verdict is recomputed every run from the files as they stand, so a
     county whose roster arrives later flips from unchecked to agrees/differs
     in a PR diff where a human sees it. That is the Coles lesson generalised:
     an attribute table (or a state directory) is a snapshot of when it was
     written, and the county republishes the people long before anyone
     republishes the snapshot.

  3. IT IS NOT AN ADDRESS BOOK. See the next section — this is the part of
     this pipeline that had to be got right.

HOME ADDRESSES NEVER REACH THE OUTPUT, AND THIS DOCUMENT IS FULL OF THEM.
The rule below was written when this was going to be app data. It is kept in
force even though nothing here is rendered, because a measurement file is
still a file in this repo, and "we weren't going to show it" has never been a
reason to write somebody's home address to disk. ISBE prints a
mailing address for every officer, and for a board chair that address is
whatever the county reported: sometimes the courthouse, very often the chair's
farm. Measured over all 102 chair rows in the 2025-12-15 edition, 30 sit at an
address no other county officer uses — "26617 Samantha Court", "1630 Quail
Way", "13020 County Road 1220N", "5172 East 2200th Road" — and those are
residences, not offices. Nothing distinguishes them by shape: a courthouse can
be "111 East Chestnut Street" and a house can be "909 Pearl Street".

So an address ships ONLY when the document corroborates it as a public
building: the same street number and street name, in the same city, as at
least one of that county's COURTHOUSE_OFFICES rows — the clerk, circuit clerk,
recorder, treasurer, state's attorney, sheriff, assessor, auditor. Coroners are
excluded from that pool on purpose: several of them are listed at home too.
Comparison ignores suite/room/floor/PO-box fragments and directionals, because
one county's rows write "111 Chestnut Street" and "111 East Chestnut Street"
for the same courthouse; the house NUMBER and the city must match exactly, so
the loosening can only merge two spellings of one address and never two
addresses.

This is deliberately conservative in the direction of shipping nothing: it
drops DeKalb's "200 North Main Street" (the county's Legislative Center, a
real public building that simply houses no other constitutional officer) along
with the 29 residences. A missing office line is a gap; a published home
address is a harm, and the two are not comparable. 72 of 102 chairs carry an
address; the other 30 carry a name, a party and a contact and no location.

WHAT ELSE IS RECORDED, AND WHY. The e-mail and phone are kept as published, even
where they are personal (`lionrex1958@yahoo.com`, a mobile number). That is
the fleet's standing line: contact a government publishes as the way to reach
an officer is contact this app may pass on — it is how Boone's and Grundy's
members' mobiles already ship — while a residence is not contact, it is a
location, and it stays out. (Nothing here is passed on today; the distinction
is kept so the contact-only build named above can start from a clean file.) The party ships as the letter the document prints
in parentheses ("(R)" -> "R"), which is an unwrapping and not a reading.

THE TITLE IS KEPT AS PUBLISHED, and this matters more than it looks. Eighty-five
counties print "Chair, County Board", sixteen print "Chair, County Comm." and
Cook prints "County Board President" — 102 of 102, so every county names one.
The sixteen are the COMMISSION-form counties, where there is no county board
to chair; calling their officer a "board chair" would be the app inventing a
governance form the county does not have. A card should render the county's
own word.

FLOORS, set against the 2025-12-15 measurement (102 chairs, 94 e-mails, 97
phones, 72 corroborated offices) and low enough that ordinary turnover and a
county or two going quiet cannot trip them, high enough that a geometry change
in the PDF cannot pass as a smaller directory.

Usage:
    python3 build_county_board_chairs.py <isbe-county-officers.json> [out_dir]

Output defaults to data/source/ — deliberately not data/app. See the top of
this docstring.
"""

import ast
import collections
import datetime
import glob
import json
import os
import re
import sys
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

OUT_NAME = "isbe-county-board-chairs.json"

# The three chair-equivalent titles this document prints, and the only rows
# this builder reads. Anything else is another office.
CHAIR_TITLES = ("Chair, County Board", "Chair, County Comm.",
                "County Board President")

# Offices whose published address is a public building by construction. The
# coroner is NOT here: several counties list theirs at home or at a funeral
# home, and this set's whole job is to be the thing an address is trusted
# against.
COURTHOUSE_OFFICES = frozenset((
    "County Clerk", "Circuit Clerk", "Recorder", "Treasurer",
    "State's Attorney", "Sheriff", "Supervisor of Assessments", "Assessor",
    "Auditor", "Chief Executive Officer",
))

# ISBE's spelling of the three counties it writes differently from the repo's
# canonical list. Everything else matches build_county_status.py's names
# exactly, and an unmapped name is a hard failure rather than a new slug.
ISBE_COUNTY_SPELLINGS = {
    "JoDaviess": "Jo Daviess",
    "DeWitt": "De Witt",
    "St Clair": "St. Clair",
}

MIN_CHAIRS = 90         # 102 ship today; a collapse is a parse failure
MIN_EMAILS = 85         # 94 today
MIN_PHONES = 85         # 97 today
MIN_OFFICES = 55        # 72 today; see the address rule above
STALE_DAYS = 400        # past this the document's own date is the story

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# NOT data/app. This file is a MEASUREMENT, not app data — see the docstring's
# "WHY NOTHING HERE REACHES A CARD". Writing it into data/app would make it a
# shipped roster by the repo's own conventions (sw.js caching, validate_index,
# the link gate) and would invite a later change to render it.
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "source")
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
COUNTY_STATUS_PY = os.path.join(REPO_ROOT, "scripts", "build_county_status.py")
COMMISSIONERS_JSON = os.path.join(APP_DATA_DIR, "il-county-commissioners.json")

# Roster files the cross-check reads, by the slug they belong to. Everything
# else in data/app is geometry or not a county roster.
ROSTER_GLOBS = ("*-county-board-members.json", "*-commissioner-members.json",
                "lake-county-board-roles.json")
ROSTER_EXCLUDE = {"school-board-members.json"}

DIRECTIONALS = frozenset((
    "n", "s", "e", "w", "ne", "nw", "se", "sw", "north", "south", "east",
    "west", "northeast", "northwest", "southeast", "southwest",
))
STREET_SUFFIXES = {
    "street": "st", "st": "st", "avenue": "ave", "ave": "ave", "av": "ave",
    "road": "rd", "rd": "rd", "drive": "dr", "dr": "dr", "lane": "ln",
    "ln": "ln", "court": "ct", "ct": "ct", "place": "pl", "pl": "pl",
    "boulevard": "blvd", "blvd": "blvd", "highway": "hwy", "hwy": "hwy",
    "circle": "cir", "cir": "cir", "square": "sq", "sq": "sq",
    "terrace": "ter", "parkway": "pkwy", "pkwy": "pkwy", "trail": "trl",
}
UNIT_RE = re.compile(
    r"\b(?:p\.?\s?o\.?\s+box|box|suite|ste|room|rm|unit|apt|apartment|"
    r"floor|fl|#)\b.*", re.I)
FLOOR_RE = re.compile(r"\b\d+\s*(?:st|nd|rd|th)?\s*floor\b.*", re.I)
LEADING_HASH_RE = re.compile(r"^#\s*(?=\d)")
NAME_SUFFIXES = frozenset(("jr", "sr", "ii", "iii", "iv", "v", "md", "phd"))


fail = make_fail("county-board-chairs")


def warn(msg):
    print("county-board-chairs: WARN — %s" % msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# County identity. The 102-county list is the denominator of every claim in
# this repo and it already lives in one place; this reads it rather than
# keeping a second copy, the same ast trick and the same reason as
# build_county_status.py's own literals_from (importing it would drag in its
# module-level work for two constants).
# ---------------------------------------------------------------------------
def county_literals():
    with open(COUNTY_STATUS_PY, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), COUNTY_STATUS_PY)
    found = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in (
                    "ALL_COUNTIES", "SLUG_OVERRIDES"):
                found[target.id] = ast.literal_eval(node.value)
    missing = {"ALL_COUNTIES", "SLUG_OVERRIDES"} - set(found)
    if missing:
        fail("could not read %s from %s — the county list moved"
             % (sorted(missing), COUNTY_STATUS_PY))
    if len(found["ALL_COUNTIES"]) != 102:
        fail("%s lists %d counties, not 102"
             % (COUNTY_STATUS_PY, len(found["ALL_COUNTIES"])))
    return found["ALL_COUNTIES"], found["SLUG_OVERRIDES"]


def slug_of(name, overrides):
    if name in overrides:
        return overrides[name]
    return name.lower().replace(".", "").replace(" ", "-")


def letters_only(name):
    return re.sub(r"[^A-Z]", "", re.sub(r"\s*COUNTY\s*$", "", name.upper()))


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------
def street_key(line):
    """(house number, {street-name tokens}) — or None when there is no street.

    A PO box normalises to None on purpose: a box number is not a location and
    two officers sharing a building do not share a box.
    """
    text = LEADING_HASH_RE.sub("", (line or "").strip()).lower()
    if not text or text == "n/a":
        return None
    text = FLOOR_RE.sub(" ", text)
    text = UNIT_RE.sub(" ", text)
    text = re.sub(r"[.,]", " ", text)
    match = re.match(r"^(\d+[a-z]?)\s+(.*)$", re.sub(r"\s+", " ", text).strip())
    if not match:
        return None
    tokens = [STREET_SUFFIXES.get(token, token) for token in match.group(2).split()]
    tokens = [token for token in tokens if token and token not in DIRECTIONALS]
    if not tokens:
        return None
    return (match.group(1), frozenset(tokens))


def city_key(lines):
    if len(lines) < 2:
        return ""
    match = re.match(r"(.*?),\s*IL\b", lines[-1].strip(), re.I)
    return re.sub(r"\s+", " ", (match.group(1) if match else lines[-1])).strip().lower()


def place_key(lines):
    key = street_key(lines[0]) if lines else None
    return (key, city_key(lines)) if key else None


def office_for(chair, officers):
    """The chair's address IF the document corroborates it as a public
    building, plus the office that corroborates it. Otherwise nothing.

    The county clerk's office in this app's own il-county-clerks.json was
    tried as a second, independent axis and MEASURED TO ADD NOTHING: all 72
    corroborated addresses are already corroborated inside the document, which
    stands to reason, since the clerk's own row is one of the rows being
    compared against. A second check that can never change an answer is not a
    safeguard, so it is not here.
    """
    mine = place_key(chair.get("addressLines") or [])
    if not mine:
        return None
    for officer in officers:
        if officer is chair or officer.get("title") not in COURTHOUSE_OFFICES:
            continue
        if place_key(officer.get("addressLines") or []) == mine:
            return {"address": ", ".join(chair["addressLines"]),
                    "confirmedBy": officer["title"]}
    return None


# ---------------------------------------------------------------------------
# Cross-check against the rosters this app already ships
# ---------------------------------------------------------------------------
def name_parts(name):
    cleaned = re.sub(r'"[^"]*"|\([^)]*\)', " ", str(name))
    cleaned = re.sub(r"[.,]", " ", cleaned).lower()
    tokens = [t for t in cleaned.split() if t and t not in NAME_SUFFIXES]
    if not tokens:
        return "", ""
    return tokens[0], tokens[-1]


def within_one_edit(left, right):
    """Levenshtein <= 1 — "VanDoyne"/"VanDuyne", "Ester"/"Esther"."""
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    if len(left) > len(right):
        left, right = right, left
    for index in range(len(right)):
        if left[:index] == right[:index] and (
                left[index:] == right[index + 1:] or
                (len(left) == len(right) and left[index + 1:] == right[index + 1:])):
            return True
    return left == right[:-1]


def match_in(name, candidates):
    """The one candidate who is the same person, or None. Never a guess.

    Surname first, within one edit — the two directories spell Will County's
    chair "VanDoyne" and "VanDuyne", Schuyler's "Ester" and "Esther". A UNIQUE
    surname hit inside one county's roster is the match: given names are the
    unreliable half ("Bill Burke Jr." here, "William Burke Jr" on the county's
    page), and a board of a dozen people rarely repeats a surname. When it
    does, the given name has to agree too — equal, one a prefix of the other,
    or a shared initial — and an ambiguous surname resolves to nothing at all,
    the same unambiguous-match-only rule build_dekalb_county_board_roster.py
    applies to its chair.
    """
    given, family = name_parts(name)
    if not family:
        return None
    hits = [c for c in candidates if within_one_edit(name_parts(c)[1], family)]
    if len(hits) == 1:
        return hits[0]
    narrowed = []
    for candidate in hits:
        other = name_parts(candidate)[0]
        if given == other or given.startswith(other) or other.startswith(given) \
                or given[:1] == other[:1]:
            narrowed.append(candidate)
    return narrowed[0] if len(narrowed) == 1 else None


def roster_records(payload):
    """Every dict carrying a name, the shape-agnostic read that
    check_roster_retention.py uses on these same files."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("name"), str):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return found


def shipped_rosters(all_counties, overrides):
    """{slug: (label, [records])} for every county roster in data/app."""
    slug_by_letters = {letters_only(name): slug_of(name, overrides)
                       for name, _ in all_counties}
    rosters = {}
    for pattern in ROSTER_GLOBS:
        for path in sorted(glob.glob(os.path.join(APP_DATA_DIR, pattern))):
            base = os.path.basename(path)
            if base in ROSTER_EXCLUDE:
                continue
            slug = re.sub(r"-(?:county-board-members|commissioner-members|"
                          r"county-board-roles)\.json$", "", base)
            with open(path, encoding="utf-8") as handle:
                rosters[slug] = (base, roster_records(json.load(handle)))
    if os.path.exists(COMMISSIONERS_JSON):
        with open(COMMISSIONERS_JSON, encoding="utf-8") as handle:
            payload = json.load(handle)
        for key, value in payload.items():
            slug = slug_by_letters.get(letters_only(key))
            if slug and slug not in rosters:
                rosters[slug] = ("il-county-commissioners.json[%s]" % key,
                                 roster_records(value))
    return rosters


def chair_named_by(records):
    """The names a roster itself badges as chair (never vice-chair)."""
    named = []
    for record in records:
        role = record.get("role") or record.get("title") or ""
        if not isinstance(role, str):
            continue
        if re.search(r"chair", role, re.I) and not re.search(r"vice", role, re.I):
            named.append(record["name"])
    return named


def cross_check(name, roster):
    """(verdict, note) — see the module docstring for what each verdict means."""
    label, records = roster
    names = [record["name"] for record in records]
    if not names:
        return "unchecked", "%s ships no names to compare against" % label
    badged = chair_named_by(records)
    member = match_in(name, names)
    spelling = ""
    if member and member != name:
        spelling = " (spelled %r there)" % member
    if badged:
        if match_in(name, badged):
            return "agrees", "%s marks them chair%s" % (label, spelling)
        return "differs", ("%s marks %s as chair%s" % (
            label, " / ".join(badged),
            " and lists this person as a member" if member else
            " and does not list this person at all"))
    if member:
        return "agrees", ("%s lists them as a member and badges no chair%s"
                          % (label, spelling))
    return "differs", "%s does not list them at all" % label


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        fail("usage: build_county_board_chairs.py <isbe-county-officers.json> "
             "[output_dir]")
    with open(sys.argv[1], encoding="utf-8") as handle:
        payload = json.load(handle)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    document_date = payload.get("documentDate")
    source_url = payload.get("sourceUrl")
    if not document_date or not source_url:
        fail("the scraper output carries no documentDate/sourceUrl — this file "
             "dates itself from the document and cannot ship undated")

    all_counties, overrides = county_literals()
    canonical = {name: slug_of(name, overrides) for name, _ in all_counties}
    rosters = shipped_rosters(all_counties, overrides)

    roster, notes, no_chair = {}, [], []
    verdicts = collections.Counter()
    for isbe_name, entry in sorted(payload.get("counties", {}).items()):
        printed = isbe_name.replace(" County", "").strip()
        county = ISBE_COUNTY_SPELLINGS.get(printed, printed)
        if county not in canonical:
            fail("the document names %r, which is not one of Illinois's 102 "
                 "counties as build_county_status.py spells them — add the "
                 "spelling deliberately, never by widening the match"
                 % isbe_name)
        slug = canonical[county]
        officers = entry.get("officers") or []
        chairs = [o for o in officers if o.get("title") in CHAIR_TITLES]
        if not chairs:
            no_chair.append(county)
            continue
        if len(chairs) > 1:
            warn("%s names %d chairs (%s) — a county has one, so nothing "
                 "ships for it until a human reads the page"
                 % (county, len(chairs),
                    ", ".join(c.get("name") or "?" for c in chairs)))
            continue
        chair = chairs[0]
        name = (chair.get("name") or "").strip()
        if len(name.split()) < 2 or chair.get("titleUnknown"):
            warn("%s's chair row reads name=%r title=%r — that is a mangled "
                 "cell, not a person, so the county is omitted"
                 % (county, name, chair.get("title")))
            continue

        record = {
            "county": county,
            "name": name,
            "title": chair["title"],
            "asOf": document_date,
            "sourceUrl": source_url,
            # The page number the document PRINTS in its own footer, so a
            # reader can verify the row by eye. A viewer's #page= fragment
            # counts the cover and preface too, so a deep link needs +2.
            "documentPage": chair.get("page"),
        }
        if chair.get("party"):
            record["party"] = chair["party"]
        if chair.get("email"):
            record["email"] = chair["email"]
        if chair.get("phone"):
            record["phone"] = chair["phone"]
        office = office_for(chair, officers)
        if office:
            record["office"] = office
        elif chair.get("addressLines"):
            notes.append("%s: address withheld (%s corroborates no county "
                         "office)" % (county, ", ".join(chair["addressLines"])))

        if slug in rosters:
            verdict, note = cross_check(name, rosters[slug])
            record["crossCheck"] = verdict
            record["crossCheckSource"] = rosters[slug][0]
            # A plain agreement is a line nobody needs weekly; a disagreement
            # and a name the two sources spell differently are exactly what a
            # human reviewing the refresh PR has to see.
            if verdict != "agrees" or "spelled" in note:
                notes.append("%s: %s — %s" % (county, verdict, note))
        else:
            verdict = "unchecked"
            record["crossCheck"] = verdict
        verdicts[verdict] += 1
        roster[slug] = record

    # ---- guards ----------------------------------------------------------
    if len(roster) < MIN_CHAIRS:
        fail("only %d chairs resolved (floor %d) — refusing to overwrite a "
             "good file with a partial parse" % (len(roster), MIN_CHAIRS))
    emails = sum(1 for r in roster.values() if r.get("email"))
    phones = sum(1 for r in roster.values() if r.get("phone"))
    offices = sum(1 for r in roster.values() if r.get("office"))
    for label, count, floor in (("e-mails", emails, MIN_EMAILS),
                                ("phones", phones, MIN_PHONES),
                                ("corroborated offices", offices, MIN_OFFICES)):
        if count < floor:
            fail("only %d %s resolved (floor %d) — a whole column has gone "
                 "quiet, which is what this floor is for" % (count, label, floor))

    out_path = os.path.join(out_dir, OUT_NAME)
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as handle:
            previous = json.load(handle)
        shipped = sorted({r.get("asOf") for r in previous.values()
                          if isinstance(r, dict) and r.get("asOf")})
        if shipped and document_date < shipped[-1]:
            fail("the fetched document is stamped %s but the shipped file "
                 "already carries %s — that is an older edition being served, "
                 "not an update" % (document_date, shipped[-1]))

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(roster, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    # ---- the run's own report -------------------------------------------
    for note in notes:
        print("county-board-chairs: %s" % note, file=sys.stderr)
    if no_chair:
        print("county-board-chairs: %d counties name no chair: %s"
              % (len(no_chair), ", ".join(no_chair)), file=sys.stderr)

    age = (datetime.date.today() - datetime.date.fromisoformat(document_date)).days
    print("county-board-chairs: DOCUMENT DATE — the directory was re-fetched "
          "today, but ISBE last updated it %s, %d days ago. Every record "
          "carries that date; a chair elected since is not in it."
          % (payload.get("documentDateText") or document_date, age),
          file=sys.stderr)
    if age > STALE_DAYS:
        warn("the document is %d days old (past %d) — check whether ISBE has "
             "stopped maintaining it before trusting another refresh"
             % (age, STALE_DAYS))
    if verdicts["differs"]:
        warn("%d counties' own shipped rosters name a DIFFERENT chair — those "
             "records are marked crossCheck=differs and a card must prefer the "
             "county's roster" % verdicts["differs"])
    print("county-board-chairs: wrote %s — %d chairs (%d e-mails, %d phones, "
          "%d corroborated offices, %d addresses withheld); cross-check %s"
          % (out_path, len(roster), emails, phones, offices,
             len(roster) - offices,
             ", ".join("%s %d" % (k, verdicts[k])
                       for k in ("agrees", "differs", "unchecked"))),
          file=sys.stderr)


if __name__ == "__main__":
    main()

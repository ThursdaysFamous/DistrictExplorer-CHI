#!/usr/bin/env python3
"""
Build data/app/wi-county-officers.json from the Blue Book officer-table
intermediate (wi_county_clerk_scraper.py's parse_officer_tables — phase 4
PR 1, docs/WI_PHASE4_PLAN.md).

WHAT SHIPS, AND UNDER WHAT LABEL. Seven offices per county: board chair,
executive/administrator (the Blue Book's own type code decides the label —
CE is the state's only ELECTED type; CA, AC and CM are appointed forms,
and a code-less entry ships with the neutral label because the book prints
none), treasurer, clerk of circuit court, register of deeds, district
attorney, sheriff, and coroner or medical examiner (ME = the appointed
examiner alternative, labeled so). The book's "A" code means APPOINTED TO
FILL A VACANCY and ships as that phrase, never as a party.

DATED, DELIBERATELY: no second publisher for these offices measures open
(the sheriffs' association is unreachable, the DA association is
member-gated, DOJ's directory is SharePoint-JS — the phase-4 plan's
appendix), so every row carries the edition — "Wisconsin Blue Book
2025–26 (April 2025)" — rather than implying the weekly-verified currency
the clerk rows genuinely have. The scraper still re-reads the book weekly
(cheap; the biennium URL bump is a WATCH.md row).

THE CHAIR COLUMN CARRIES ITS OWN WITNESS: its "(# of supervisors)" must
equal the seat count county-board-directory.json reads back from the
shipped supervisory geometry. 71 of 72 agree. MENOMINEE IS THE MEASURED
EXCEPTION AND IT IS PINNED, NOT SMOOTHED: the Blue Book seats its board
at 7 where the state's own LTSB aggregate carries 5 districts numbered
1-5 — two state publications disagreeing — so Menominee's chair ships
WITHOUT a seat count and any drift in the exception fails the build.

THE CHAIR IS ALSO RECONCILED AGAINST THE WEEKLY BOARD ROSTER, because a
chair is the one officer who is also a supervisor, and Wisconsin boards
elect their chair at the organizational meeting after each April
election — a cycle an April-2025 snapshot cannot see. Measured on
2026-08-26, six of the 22 roster counties had visibly moved past the
book: three chairs had rotated (the county's own page marks a different
supervisor as chair), two had left their boards entirely, and one had
changed her surname. So, per county, in order:

  * the county's own board page MARKS a chair (a role containing "chair"
    and not "vice") -> that name ships, sourced to the page — the same
    rule the clerk row already follows, the fresher county source
    superseding the book;
  * no marked chair, and the book's chair still sits on the board
    (surname + first initial against the roster — initials, nicknames
    and case vary across the two publishers, so a full-name fold would
    wrongly evict Burnett's Don/Donald Taylor) -> the dated book row
    ships as before;
  * no marked chair and the book's chair is ABSENT from a COMPLETE
    roster -> the name is WITHHELD, with the reason on the card:
    naming someone the county's own roster no longer seats fails the
    honesty rules, and inventing the successor would too.

The 50 counties with no published roster keep the dated book row — there
is nothing to reconcile against. Every decision prints on the build log.

The Menominee/Shawano DA rows carry the book's own footnote — one
prosecutorial unit, one district attorney (Wis. Stat. ch. 978) — and the
builder writes that sentence onto both counties' entries.

CONTACT + CURRENCY, COUNTY BY COUNTY (phase 4 PR 2 tranche 1): where
wi_county_officer_contact_scraper.py has read a county's own officer
pages (run it FIRST — its intermediate is this builder's input; both
weekly workflows do), each witnessed office gains the office page URL and
the phone/e-mail found beside the officer's own name, and a name the
county's page carries that DISAGREES with the book's supersedes it — the
county's name ships, the book's party code is withheld (the clerk rule),
and the divergence prints. The first run proved the route on its biggest
case: Waukesha's own page records that County Executive Paul Farrow —
the Blue Book's row — DIED IN OFFICE, with Interim County Executive Tom
Farley sworn in 2026-07-30. STALE_EXEC pins that protection into the
builder itself: even when the contact scrape is absent or its extraction
fails, Waukesha's executive is WITHHELD with the reason stated rather
than ever again shipping the deceased officeholder's name. The pin lasts
until the next Blue Book edition re-bases the file.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
RAW = os.path.join(SCRIPT_DIR, ".cache", "wi_county_officers_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "wi-county-officers.json")
COUNTIES = os.path.join(REPO_ROOT, "data", "app", "state-counties.json")
DIRECTORY = os.path.join(REPO_ROOT, "data", "app", "county-board-directory.json")
MEMBERS = os.path.join(REPO_ROOT, "data", "app", "county-board-members.json")
CONTACTS = os.path.join(SCRIPT_DIR, ".cache", "wi_county_officer_contacts_raw.json")

EXEC_LABELS = {
    "CE": ("County Executive", False),
    "CA": ("County Administrator", True),
    "AC": ("Administrative Coordinator", True),
    "CM": ("County Manager", True),
    None: ("Executive / administrator", None),  # the book prints no type code
}
# Blue Book seats vs shipped-geometry seats: the one measured disagreement
# between two state publications. Recomputed every run; drift fails.
SEAT_EXCEPTIONS = {"Menominee": {"blueBook": 7, "geometry": 5}}

SHARED_DA_NOTE = ("Menominee and Shawano counties comprise a single "
                  "prosecutorial unit served by one district attorney "
                  "(Wis. Stat. ch. 978).")

WITHHELD_REASON = ("Not named: the Blue Book (April 2025) lists a chair who no "
                   "longer appears on the county's own supervisor roster, and "
                   "that roster does not mark a successor. The County Board "
                   "District card names the sitting supervisors.")

# Counties whose Blue Book EXECUTIVE is measurably no longer in office
# (the county's own page is the measurement). The contact scrape normally
# supersedes with the county's current name; this pin is the backstop —
# if the scrape is absent or its extraction fails, the executive is
# WITHHELD with this reason rather than the stale name shipping again.
# Remove an entry only when a new Blue Book edition re-bases the file.
STALE_EXEC = {
    "Waukesha": ("Not named: the county's own website records that the Blue "
                 "Book's April 2025 county executive died in office, and this "
                 "build could not read the interim executive's name from that "
                 "page. The county's website names the interim executive."),
}


def fold(name):
    return "".join(ch for ch in name.lower() if ch.isalpha())


def marks_chair(role):
    # "Chair", "Chairwoman", "County Chairman" mark the chair; "Vice Chair",
    # "Vice-Chair", "1st/2nd Vice Chair" never do (Polk marks all three
    # officers, and its 2nd Vice Chair is the Blue Book's chair — rotated).
    f = fold(role or "")
    return "chair" in f and "vice" not in f


assert marks_chair("County Chairman") and marks_chair("Chairwoman")
assert not marks_chair("1St Vice Chair") and not marks_chair("Vice-Chair")


_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
# leading honorifics are not first names: the book prints "Dr Elizabeth
# Douglas" where Oconto's directory prints "Dr. Elizabeth Douglas" — and a
# county page without the title must still match either form
_HONORIFICS = {"dr", "mr", "mrs", "ms", "hon", "rev"}


def surname_initial(name):
    parts = [p for p in "".join(ch if ch.isalpha() or ch.isspace() else " "
                                for ch in name).split()]
    while len(parts) > 1 and parts[0].lower() in _HONORIFICS:
        parts.pop(0)
    while len(parts) > 1 and parts[-1].lower() in _SUFFIXES:
        parts.pop()
    if not parts:
        return None
    return (parts[0][0].lower(), parts[-1].lower())


def on_board(bb_name, roster_names):
    # Presence test for the book's chair among the county's sitting
    # supervisors. Deliberately LOOSE — surname + first initial — because the
    # two publishers style the same person apart (Donald/Don Taylor, Steven
    # J/Steve Nass, Tom/THOMAS KRAMER, Robert C/Robert Keeney). A false match
    # keeps the dated book row (today's behavior); a false miss would wrongly
    # WITHHOLD a sitting chair, which is the worse error.
    key = surname_initial(bb_name)
    return key is not None and any(surname_initial(n) == key for n in roster_names)


# The book prints "Vacant" in an empty office's cell and the first parse
# shipped it as a person's name (measured: Sawyer's executive, Forest's
# and Oneida's coroners). A vacancy is the absence of an officer, never
# an officer called Vacant.
def is_vacant(name):
    return fold(name or "") == "vacant"


# When the county's own directory names (or fills) an executive, its own
# title decides the elected-vs-appointed label — same rule as the book's
# CE/CA/AC/CM codes.
APPOINTED_EXEC_TITLES = {"County Administrator", "Administrative Coordinator",
                         "County Manager", "Interim County Executive"}


def officer(cell, vacancy_note=True):
    if not cell or not cell.get("name") or is_vacant(cell["name"]):
        return None
    out = {"name": cell["name"]}
    code = cell.get("code")
    if code in ("D", "I", "R"):
        out["party"] = {"D": "Democrat", "I": "Independent", "R": "Republican"}[code]
    elif code == "A" and vacancy_note:
        out["note"] = "Appointed to fill a vacancy"
    return out


def main():
    raw = json.load(open(RAW))
    counties_by_base = raw["counties"]
    if len(counties_by_base) != 72:
        raise SystemExit("intermediate carries %d counties" % len(counties_by_base))

    feats = json.load(open(COUNTIES))["features"]
    geoid_by_base = {f["properties"]["BASENAME"]: f["properties"]["GEOID"] for f in feats}
    directory = json.load(open(DIRECTORY))
    seats_by_fold = {fold(v["county"]): v["seats"] for v in directory.values()}

    # The weekly board roster, grouped by county GEOID (its keys are
    # GEOID + zero-padded district). The board builder already refuses a
    # county whose scrape disagrees with the shipped geometry's seat count,
    # so a county present here is a COMPLETE roster — which is what makes
    # absence from it evidence rather than a scrape artifact.
    board_by_geoid = {}
    for key, rec in json.load(open(MEMBERS)).items():
        board_by_geoid.setdefault(key[:5], []).append(rec)

    out_counties = {}
    mismatches = {}
    superseded, confirmed, withheld = [], [], []
    for base, entry in counties_by_base.items():
        geoid = geoid_by_base[base]
        chair = dict(entry["chair"])
        dir_seats = seats_by_fold.get(fold(base))
        if dir_seats is None:
            raise SystemExit("%s: no seat count in county-board-directory" % base)
        if chair["seats"] != dir_seats:
            mismatches[base] = {"blueBook": chair["seats"], "geometry": dir_seats}
            chair.pop("seats")  # two state publications disagree: claim neither

        roster = board_by_geoid.get(str(geoid))
        if roster:
            if len(roster) != dir_seats:
                raise SystemExit(
                    "%s: board roster carries %d seats against the directory's %d "
                    "— the board builder's own gate should have caught this"
                    % (base, len(roster), dir_seats))
            marked = [r for r in roster
                      if r.get("name") and marks_chair(r.get("role"))]
            if len(marked) > 1:
                raise SystemExit("%s: board page marks %d chairs: %s" %
                                 (base, len(marked),
                                  [r["name"] for r in marked]))
            sitting = [r["name"] for r in roster if r.get("name")]
            if marked:
                page = marked[0]
                superseded.append("%s: %s -> %s" % (base, chair.get("name"),
                                                    page["name"]))
                new_chair = {"name": page["name"],
                             "source": "county-board-page"}
                if page.get("sourceUrl"):
                    new_chair["sourceUrl"] = page["sourceUrl"]
                if "seats" in chair:
                    new_chair["seats"] = chair["seats"]
                chair = new_chair
            elif on_board(chair.get("name", ""), sitting):
                confirmed.append(base)
            else:
                withheld.append("%s (Blue Book chair: %s)" %
                                (base, chair.get("name")))
                new_chair = {"withheld": True, "reason": WITHHELD_REASON}
                if "seats" in chair:
                    new_chair["seats"] = chair["seats"]
                chair = new_chair

        chair = {k: v for k, v in chair.items()
                 if not (k == "name" and is_vacant(v))}
        exec_cell = entry["executive"]
        executive = None
        if exec_cell and exec_cell.get("name") and not is_vacant(exec_cell["name"]):
            title, appointed = EXEC_LABELS[exec_cell.get("code")]
            executive = {"name": exec_cell["name"], "title": title}
            if appointed is True:
                executive["appointed"] = True

        da = officer(entry["districtAttorney"])
        if da and entry["districtAttorney"].get("shared"):
            da["sharedUnit"] = SHARED_DA_NOTE

        coroner_cell = entry["coroner"]
        coroner = officer(coroner_cell)
        if coroner:
            coroner["title"] = ("Medical Examiner (appointed)"
                                if (coroner_cell or {}).get("code") == "ME" else "Coroner")

        out_counties[str(geoid)] = {
            "county": base,
            # the edition rides every record (not a wrapper key): the file
            # stays GEOID-keyed like the clerk file, so the validator's
            # min_keys and the retention gate's per-record field coverage
            # both see the real 72-county shape
            "asOf": raw["edition"],
            "sourceUrl": raw["sourceUrl"],
            "chair": chair,
            "executive": executive,
            "treasurer": officer(entry["treasurer"]),
            "clerkOfCircuitCourt": officer(entry["clerkOfCircuitCourt"]),
            "registerOfDeeds": officer(entry["registerOfDeeds"]),
            "districtAttorney": da,
            "sheriff": officer(entry["sheriff"]),
            "coroner": coroner,
        }

    # ---- contact + currency merge (the per-county scrape's yield) ----
    contacts = json.load(open(CONTACTS)) if os.path.exists(CONTACTS) else None
    if contacts is None:
        print("WARNING: no contact intermediate (%s) — officer rows ship "
              "without contact; run wi_county_officer_contact_scraper.py "
              "first" % os.path.relpath(CONTACTS, REPO_ROOT), file=sys.stderr)
    n_contact, n_diverged = 0, 0
    for geoid, centry in (contacts or {}).items():
        entry = out_counties[geoid]
        checked = 0
        for office, c in centry["offices"].items():
            if "supersede" in c:
                s = c["supersede"]
                executive = {"name": s["name"], "title": s["title"],
                             "source": "county-page"}
                if s.get("appointed"):
                    executive["appointed"] = True
                if c.get("url"):
                    executive["url"] = c["url"]
                if c.get("phone"):
                    executive["phone"] = c["phone"]
                entry["executive"] = executive
                print("%s/executive superseded by the county's own page: %s"
                      % (centry["county"], s["name"]), file=sys.stderr)
                n_diverged += 1
                checked += 1
                continue
            rec = entry.get(office)
            if not rec or not rec.get("name"):
                if office == "executive" and c.get("name") and c.get("title"):
                    # the county's own directory names an executive the book
                    # leaves BLANK (Sawyer's cell literally prints "Vacant"):
                    # the page's name fills the office, its own title decides
                    # the label, appointed forms labeled so
                    executive = {"name": c["name"], "title": c["title"],
                                 "source": "county-page"}
                    if c["title"] in APPOINTED_EXEC_TITLES:
                        executive["appointed"] = True
                    if c.get("url"):
                        executive["url"] = c["url"]
                    entry["executive"] = executive
                    print("%s/executive FILLED from the county's own page: %s "
                          "(%s) — the book names nobody"
                          % (centry["county"], c["name"], c["title"]),
                          file=sys.stderr)
                    n_diverged += 1
                    checked += 1
                continue
            if "name" in c and \
               surname_initial(c["name"]) != surname_initial(rec["name"]):
                # the county's directory names a different person: the
                # county's name ships, the book's party code is withheld
                # (the clerk rule), the office title is kept
                print("%s/%s diverges — book %r, county page %r; the "
                      "county's name ships" % (centry["county"], office,
                                               rec["name"], c["name"]),
                      file=sys.stderr)
                new_rec = {"name": c["name"], "source": "county-page"}
                if office == "executive" and c.get("title"):
                    # the page's own title labels the person it names —
                    # the book's title belonged to the book's person
                    new_rec["title"] = c["title"]
                    if c["title"] in APPOINTED_EXEC_TITLES:
                        new_rec["appointed"] = True
                elif rec.get("title"):
                    new_rec["title"] = rec["title"]
                if rec.get("sharedUnit"):
                    new_rec["sharedUnit"] = rec["sharedUnit"]
                rec = new_rec
                entry[office] = rec
                n_diverged += 1
            elif "name" in c:
                rec["name"] = c["name"]  # the fuller/fresher county form
            if c.get("url"):
                rec["url"] = c["url"]
            if c.get("phone"):
                rec["phone"] = c["phone"]
            if c.get("email"):
                rec["email"] = c["email"]
            rec["checked"] = True
            checked += 1
            n_contact += 1
        entry["contactChecked"] = checked

    for base, reason in STALE_EXEC.items():
        geoid = str(geoid_by_base[base])
        entry = out_counties[geoid]
        ex = entry.get("executive")
        if not ex or ex.get("source") != "county-page":
            entry["executive"] = {"withheld": True, "reason": reason}
            print("%s/executive WITHHELD (STALE_EXEC pin): the scrape did "
                  "not supersede and the book's name is measurably stale"
                  % base, file=sys.stderr)

    if mismatches != SEAT_EXCEPTIONS:
        raise SystemExit(
            "chair seat counts vs shipped geometry moved off the pinned exception "
            "— a county changed board size (or a filing/table moved). Re-measure, "
            "then move SEAT_EXCEPTIONS deliberately.\n  computed: %s\n  pinned:   %s"
            % (json.dumps(mismatches, sort_keys=True),
               json.dumps(SEAT_EXCEPTIONS, sort_keys=True)))

    n_da = sum(1 for c in out_counties.values() if c["districtAttorney"])
    n_sheriff = sum(1 for c in out_counties.values() if c["sheriff"])
    n_chair = sum(1 for c in out_counties.values() if c["chair"].get("name"))
    if n_da != 72 or n_sheriff != 72 or n_chair + len(withheld) != 72:
        raise SystemExit("floors: chair %d named + %d withheld, DA %d, sheriff "
                         "%d — DA/sheriff must be 72 and every county's chair "
                         "must be named or explained"
                         % (n_chair, len(withheld), n_da, n_sheriff))
    if len(withheld) > 6:
        raise SystemExit(
            "%d chairs withheld — measured state is 2 (Portage, Winnebago, "
            "2026-08-26) and a spike this size is more likely a name-matching "
            "or scrape defect than %d boards evicting their Blue Book chairs "
            "at once. Re-measure county by county, then raise this cap "
            "deliberately:\n  %s" % (len(withheld), len(withheld),
                                     "\n  ".join(withheld)))

    for line in superseded:
        print("chair superseded by the county's own page — " + line,
              file=sys.stderr)
    for line in withheld:
        print("chair WITHHELD — " + line, file=sys.stderr)

    with open(OUT, "w") as f:
        json.dump(out_counties, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote %s — 72 counties, 7 offices each; chair seats witnessed against "
          "the shipped geometry (71 agree; Menominee pinned 7-vs-5); shared DA "
          "note on Menominee and Shawano; chairs reconciled against the weekly "
          "board roster (%d from county pages, %d confirmed dated, %d withheld, "
          "%d counties with no roster to check); officer contact from %d "
          "counties' own pages (%d offices checked, %d names superseded)"
          % (os.path.relpath(OUT, REPO_ROOT), len(superseded), len(confirmed),
             len(withheld), 72 - len(board_by_geoid),
             len(contacts or {}), n_contact, n_diverged),
          file=sys.stderr)


if __name__ == "__main__":
    main()

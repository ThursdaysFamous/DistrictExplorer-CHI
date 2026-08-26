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

The Menominee/Shawano DA rows carry the book's own footnote — one
prosecutorial unit, one district attorney (Wis. Stat. ch. 978) — and the
builder writes that sentence onto both counties' entries.
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


def fold(name):
    return "".join(ch for ch in name.lower() if ch.isalpha())


def officer(cell, vacancy_note=True):
    if not cell or not cell.get("name"):
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

    out_counties = {}
    mismatches = {}
    for base, entry in counties_by_base.items():
        geoid = geoid_by_base[base]
        chair = dict(entry["chair"])
        dir_seats = seats_by_fold.get(fold(base))
        if dir_seats is None:
            raise SystemExit("%s: no seat count in county-board-directory" % base)
        if chair["seats"] != dir_seats:
            mismatches[base] = {"blueBook": chair["seats"], "geometry": dir_seats}
            chair.pop("seats")  # two state publications disagree: claim neither

        exec_cell = entry["executive"]
        executive = None
        if exec_cell and exec_cell.get("name"):
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
    if n_da != 72 or n_sheriff != 72 or n_chair != 72:
        raise SystemExit("floors: chair %d, DA %d, sheriff %d — all must be 72"
                         % (n_chair, n_da, n_sheriff))

    with open(OUT, "w") as f:
        json.dump(out_counties, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote %s — 72 counties, 7 offices each; chair seats witnessed against "
          "the shipped geometry (71 agree; Menominee pinned 7-vs-5); shared DA "
          "note on Menominee and Shawano" % os.path.relpath(OUT, REPO_ROOT),
          file=sys.stderr)


if __name__ == "__main__":
    main()

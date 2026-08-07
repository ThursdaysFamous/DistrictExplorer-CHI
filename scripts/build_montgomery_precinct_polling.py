#!/usr/bin/env python3
"""Build Montgomery County's precinct -> polling place table.

WHY THERE ARE TWO SOURCES, AND WHY THE PDF WINS. Asked on 2026-08-07 whether a
precinct-to-polling-place mapping existed, Montgomery County GIS (Kevin Brink)
sent a second geodatabase carrying a POINT layer, `PollingPlaces` — 24 points,
each with a number, a location name and an address. That layer is archived
alongside the boundaries in MontgomeryCountyIL_GIS_2026-08-07.zip.

It is NOT the source of this file, because cross-checking it against the Clerk's
own published list found the GIS layer is behind in three ways:

  * ROUNTREE IS MISSING FROM IT ENTIRELY. 37 of the county's 38 precincts can be
    read out of the GIS layer's location strings; Rountree appears in none of
    them. The Clerk's list votes it at Nokomis Memorial Park House together with
    Nokomis 2, which is the answer, and no amount of parsing the GIS layer would
    have produced it.
  * IT NAMES A DIFFERENT BUILDING FOR N. LITCHFIELD 1 & 4 — "National Guard
    Armory" against the Clerk's "First Presbyterian Church, 1908 N. State St."
    Those are two different places, so this is not a wording difference.
  * IT USES A SUPERSEDED NAME for Hillsboro 5 & 6 — "K C Hall", which the
    Clerk's list calls "The Event Center of Montgomery County (former Hillsboro
    KC Hall)". Same building, old name.

A polling place is the one fact on this card where being out of date sends a
resident to the wrong building on election day, so the ELECTION AUTHORITY'S own
published list is what ships. The GIS layer is kept as a cross-check: main()
reports every disagreement it finds, so the next refresh of either source
surfaces the drift instead of hiding it. Both findings went back to the county.

WHY THE TABLE IS TRANSCRIBED AND NOT PARSED. The published list is a PDF whose
text layer is mangled — "Ohlman Village Hall (former Methodist Chur ch)",
"F armersville", "Irvin g", "N. Lfd. 1" for North Litchfield 1 — and a parser
that coped with all of it would be doing transcription anyway, with the mistakes
hidden inside a regex instead of visible on the page. So the table below is
hand-transcribed from the document, and the checks are what make it trustworthy:
every one of the 38 shipped precincts must appear exactly once, and the row
count and building count must match the totals the document prints in its own
header ("38 Precincts/ 24 Polling Places").

Usage:
    python3 scripts/build_montgomery_precinct_polling.py            # write
    python3 scripts/build_montgomery_precinct_polling.py --check    # drift gate
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECINCTS = os.path.join(REPO_ROOT, "data", "app", "montgomery-precincts.json")
GIS_ZIP = os.path.join(REPO_ROOT, "data", "source", "raw",
                       "MontgomeryCountyIL_GIS_2026-08-07.zip")
GDB_IN_ZIP = "Overberg Data/OverbergData.gdb"
OUT_PATH = os.path.join(REPO_ROOT, "data", "app",
                        "montgomery-precinct-polling.json")

SOURCE_URL = ("https://montgomerycountyil.gov/wp-content/uploads/"
              "PRECINCTPOLLINGPLACELISTING1124.pdf")
SOURCE_NOTE = ("Montgomery County Clerk & Recorder, \"Montgomery County "
               "Precincts and Polling Places\" (38 Precincts / 24 Polling "
               "Places), archived as data/source/raw/Montgomery PRECINCT "
               "POLLING PLACE LISTING 1124.pdf")
FETCHED = "2026-08-07"

EXPECTED_PRECINCTS = 38
EXPECTED_PLACES = 24        # the document's own header count, of DISTINCT buildings

# Transcribed from SOURCE_NOTE. Each entry is (precincts, place, address).
# Where the document groups precincts on one row they share a polling place;
# where two rows name the same building (the Litchfield pairs) that is the
# document's own layout and the building is counted once.
ROWS = [
    (["Audubon"], "Ohlman Village Hall (former Methodist Church)",
     "101 S. Washington St., Ohlman, IL"),
    (["Bois D'Arc"], "Farmersville KC Hall", "104 S. East St., Farmersville, IL"),
    (["Butler Grove"], "Butler Community Center", "Water St. (IL Rt. 127), Butler, IL"),
    (["East Fork 1"], "East Fork Township Community Building",
     "500 S. Prospect St., Coffeen, IL"),
    (["East Fork 2", "Grisham 2"], "Donnellson Community Center (former school)",
     "407 Jefferson St., Donnellson, IL"),
    (["East Fork 3"], "Schram City Village Hall", "510 22nd St., Schram City, IL"),
    (["Fillmore Consolidated"], "Fillmore Consolidated Township Hall",
     "110 S. Main St., Fillmore, IL"),
    (["Grisham 1"], "Old Town Hall", "147 Main St., Panama, IL"),
    (["Harvel"], "Harvel Village Hall", "201 Main St., Harvel, IL"),
    (["Hillsboro 1", "Hillsboro 2"], "Methodist Church (North Entrance)",
     "537 Rountree St., Hillsboro, IL"),
    (["Hillsboro 3", "Hillsboro 4"], "Free Methodist Church (South Entrance)",
     "1400 Seymour Ave., Hillsboro, IL"),
    (["Hillsboro 5", "Hillsboro 6"],
     "The Event Center of Montgomery County (former Hillsboro KC Hall), Main Entrance",
     "11198 Rt. 185, Hillsboro, IL"),
    (["Irving"], "Irving Century House", "121 E. Union St., Irving, IL"),
    (["Nokomis 1"], "Coalton Village Hall",
     "S. 5th St. and E. Wilson Ave., Coalton, IL"),
    # Rountree votes here. It is the precinct the GIS point layer omits.
    (["Nokomis 2", "Rountree"], "Nokomis Memorial Park House",
     "525 N. Cedar St., Nokomis, IL"),
    (["Nokomis 3", "Nokomis 4"], "St. Louis Parish Center",
     "523 E. Union St., Nokomis, IL"),
    (["North Litchfield 1", "North Litchfield 4"], "First Presbyterian Church",
     "1908 N. State St., Litchfield, IL"),
    (["North Litchfield 2", "North Litchfield 3"],
     "First Baptist Church (East Entrance)", "608 N. Van Buren St., Litchfield, IL"),
    (["North Litchfield 5", "North Litchfield 6"],
     "First Baptist Church (East Entrance)", "608 N. Van Buren St., Litchfield, IL"),
    (["Pitman"], "Pitman Township Hall", "217 W. Main St., Waggoner, IL"),
    (["Raymond"], "Raymond KC Hall", "510 E. Sparks St., Raymond, IL"),
    (["South Litchfield 1", "South Litchfield 4"], "Litchfield Community Center",
     "1100 S. State St., Litchfield, IL"),
    (["South Litchfield 2", "South Litchfield 3"], "Litchfield Community Center",
     "1100 S. State St., Litchfield, IL"),
    (["Walshville"], "Walshville Village Hall", "1st St. and C St., Walshville, IL"),
    (["Witt 1", "Witt 2"], "Witt Lions Building", "503 W. Broadway St., Witt, IL"),
    (["Zanesville"], "Pleasant Hill Christian Church",
     "19433 W. Frontage Road, Raymond, IL"),
]

# Abbreviations the GIS layer's free-text Location strings use, for the
# cross-check only. Never used to build the shipped table.
GIS_ABBR = {"n": "North", "n.": "North", "s": "South", "s.": "South"}

# ---------------------------------------------------------------------------
# The cross-check against the GIS point layer, and why it names its findings
# instead of diffing strings.
#
# Both sides are free text with different conventions — "United Methodist Church
# E. Ent." against "Methodist Church (North Entrance)", "First Bap Church E"
# against "First Baptist Church (East Entrance)". A fuzzy comparison flags every
# one of those, and a cross-check that cries wolf on a dozen wording differences
# is worse than none: the two findings that MATTER get lost in it. (The first
# version of this file did exactly that, which is why this comment exists.)
#
# So the real disagreements are named here, each with what the GIS layer says
# today. The check verifies they are STILL what it says — so when the county
# refreshes that layer and the Armory entry becomes the church, this build says
# so and the entry can be deleted. Same self-retiring shape as the Stephenson
# clerk-office override: a record of a conflict can never outlive the conflict.
GIS_DISAGREEMENTS = {
    "North Litchfield 1": "National Guard Armory",
    "North Litchfield 4": "National Guard Armory",
    "Hillsboro 5": "K C Hall",
    "Hillsboro 6": "K C Hall",
}
# Precincts the GIS layer's location strings do not mention at all.
GIS_ABSENT = ["Rountree"]


def gis_assignments():
    """{precinct: location string} read out of the GIS point layer, best effort.

    Only ever used to REPORT — see the module docstring. Returns an empty dict
    when the archive or pyogrio is unavailable, because a missing cross-check
    must not block the build.
    """
    try:
        import pyogrio
    except ImportError:
        return {}, "pyogrio not installed"
    if not os.path.exists(GIS_ZIP):
        return {}, "archive missing"
    meta, _, geoms, fields = pyogrio.raw.read(
        "/vsizip/%s/%s" % (GIS_ZIP, GDB_IN_ZIP), layer="PollingPlaces")
    names = list(meta["fields"])
    cols = dict(zip(names, fields))
    out = {}
    for i in range(len(geoms)):
        loc = str(cols["Location"][i])
        head = re.split(r"\s+-\s+|\s{2,}", loc)[0].strip()
        # Numbered form first ("N. Litchfield 2,3,5 & 6", "Witt 1 & 2"), then the
        # bare-township form ("Zanesville", "Fillmore Township Hall").
        m = re.match(r"^((?:[NS]\.?\s+)?[A-Za-z'’ ]+?)\s*((?:\d+\s*(?:,|&|and)\s*)*\d+)\b", head)
        if m:
            base = m.group(1).strip().split()
            if base and base[0].lower() in GIS_ABBR:
                base[0] = GIS_ABBR[base[0].lower()]
            base = " ".join(base)
            for num in re.findall(r"\d+", m.group(2)):
                out["%s %s" % (base, num)] = loc
            # "East Fork 2 & Grisham 2" names a SECOND township after the "&".
            tail = head[m.end():]
            for extra, num in re.findall(r"&\s*([A-Za-z'’ ]+?)\s*(\d+)", tail):
                out["%s %s" % (extra.strip(), num)] = loc
        else:
            bare = re.match(r"^([A-Za-z'’ ]+?)(?:\s+Township\b|\s*$)", head)
            if bare:
                out[bare.group(1).strip()] = loc
    return out, None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    with open(PRECINCTS) as handle:
        shipped = {f["properties"]["name"]
                   for f in json.load(handle)["features"]}
    if len(shipped) != EXPECTED_PRECINCTS:
        sys.exit("expected %d shipped precincts, found %d"
                 % (EXPECTED_PRECINCTS, len(shipped)))

    table, seen = {}, []
    for precincts, place, address in ROWS:
        for name in precincts:
            if name in table:
                sys.exit("%s is assigned two polling places" % name)
            table[name] = {"place": place, "address": address}
            seen.append(name)

    missing = sorted(shipped - set(table))
    invented = sorted(set(table) - shipped)
    if missing or invented:
        sys.exit("the transcribed table and the shipped precincts disagree.\n"
                 "  shipped but unassigned: %s\n  assigned but not shipped: %s\n  %s"
                 % (missing, invented, SOURCE_NOTE))
    buildings = {(r[1], r[2]) for r in ROWS}
    if len(buildings) != EXPECTED_PLACES:
        sys.exit("transcribed %d distinct polling places, the document's own "
                 "header says %d" % (len(buildings), EXPECTED_PLACES))

    payload = json.dumps({
        "fetched": FETCHED,
        "source": SOURCE_URL,
        "precincts": {k: table[k] for k in sorted(table)},
    }, ensure_ascii=False, indent=1, sort_keys=True) + "\n"

    print("Montgomery: %d precincts -> %d polling places (%d shared by more than "
          "one precinct)"
          % (len(table), len(buildings), sum(1 for r in ROWS if len(r[0]) > 1)))

    gis, why = gis_assignments()
    if why:
        print("  cross-check skipped: %s" % why)
    else:
        # "Fillmore Township Hall" is how the GIS layer writes the precinct the
        # county calls Fillmore Consolidated; the bare-name branch reads it as
        # "Fillmore". Aliased here rather than in the parser so the parser stays
        # a plain reading of the source.
        for alias, real in (("Fillmore", "Fillmore Consolidated"),):
            if alias in gis and real not in gis:
                gis[real] = gis.pop(alias)
        absent = sorted(set(table) - set(gis))
        print("  GIS point layer covers %d of %d precincts" % (len(gis), len(table)))
        if absent != sorted(GIS_ABSENT):
            sys.exit("the GIS layer's coverage changed: it now omits %s, this "
                     "file records %s. If a precinct has appeared, the layer was "
                     "refreshed and GIS_DISAGREEMENTS needs re-checking too."
                     % (absent, sorted(GIS_ABSENT)))
        if absent:
            print("  absent from the GIS layer, present in the Clerk's list: %s"
                  % ", ".join(absent))
        stale = []
        for name, expected in sorted(GIS_DISAGREEMENTS.items()):
            said = gis.get(name)
            if said is None:
                stale.append("%s is no longer in the GIS layer at all" % name)
            elif expected.lower() not in said.lower():
                stale.append("%s no longer says %r (now %r)" % (name, expected, said))
        if stale:
            sys.exit("a recorded GIS disagreement has changed — GOOD NEWS, "
                     "probably, but re-check it against the Clerk's list and "
                     "delete the entry if it is resolved:\n    %s"
                     % "\n    ".join(stale))
        for name in sorted(GIS_DISAGREEMENTS):
            print("  DISAGREES for %-20s GIS %r vs Clerk %r"
                  % (name, GIS_DISAGREEMENTS[name], table[name]["place"]))
    print("  source: %s" % SOURCE_NOTE)

    existing = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as handle:
            existing = handle.read()
    if args.check:
        if existing != payload:
            sys.exit("DRIFT: %s does not match a fresh build"
                     % os.path.relpath(OUT_PATH, REPO_ROOT))
        print("  --check OK — matches a fresh build")
        return
    with open(OUT_PATH, "w") as handle:
        handle.write(payload)
    print("  wrote %s (%s bytes)"
          % (os.path.relpath(OUT_PATH, REPO_ROOT), "{:,}".format(len(payload))))


if __name__ == "__main__":
    main()

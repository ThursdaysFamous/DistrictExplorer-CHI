#!/usr/bin/env python3
"""
ISBE's precinct-level results archive, read as a RE-PRECINCTING TRIPWIRE.

WHY THIS EXISTS. Most of this project's county precinct layers are built from
Census 2020 voting districts, which are a snapshot: the moment a county
consolidates, splits or renames a precinct, the shipped fabric is silently
wrong and nothing notices. docs/EXPANSION_GUIDE.md §2.5.1 step 6 asks for a
check on exactly that, and until now it could only be run where a results
vendor happened to carry the county — 34 counties on one vendor, 13 on
another, 17 on a third.

ISBE carries all 102, from one host, back to 1998:

    https://www.elections.il.gov/Downloads/ElectionOperations/ElectionResults/
        ByOffice/<electionId>/<electionId>-<officeCode>-<OFFICE>-<tag>.csv

The filenames are DISCOVERED from ElectionVoteTotals.aspx rather than guessed —
that page links every office's CSV for a chosen election, and the office code
and tag are not derivable from the election id.

HOW THE COMPARISON IS MADE, and why it is election-to-election rather than
against the shipped layer. The obvious check — diff ISBE's precinct names for a
county against the names in that county's shipped file — was tried first and is
WRONG. On the 2026 General Primary it agrees exactly for 20 of the 33 counties
that ship a precinct layer and disagrees for 13, and the disagreements are not
drift: Richland reports 30 names against 21 shipped precincts, which is the NINE
sub-precinct reporting units its own gap record already documents. A county may
report a precinct in parts, and that is a fact about ISBE's reporting units, not
about the fabric having moved.

Comparing one election to another is immune to all of it. Whatever convention a
county reports under, it reports under the same one in both files, so a name set
that CHANGES is the county having changed something. That is the check the
guidebook asked for.

TWO NORMALISATIONS, BOTH MEASURED. Federal/UOCAVA reporting units are dropped:
McDonough reports BETHEL-1 beside BETHEL-F15, one real precinct and one
ballot class, and 873 such names exist statewide. The rule matches `-F<digits>`
and `-FED<digits>` ONLY, and that precision is load-bearing — a rule that
stripped any trailing `-TOKEN` would eat Calhoun's HARDIN-GILEAD and
BELLEVIEW-HAMBURG, which are merged precincts whose names really do end that
way. Comparison is otherwise case- and whitespace-normalised, because ISBE's
own capitalisation drifts between elections ("McDONOUGH" / "MCDONOUGH").

WHAT THE ARCHIVE DOES NOT COVER, measured 2026-09-03 rather than assumed:
CONSOLIDATED ELECTIONS carry no by-office CSV at all. Ids 68 (2025), 64 (2023)
and 59 (2021) each link zero files, while every general and every primary links
18-23. So this reads the November and March ballots and cannot see the April
ones — which matters because a county that re-precincts for a municipal
election shows up here only at the next general. `--list` says which elections
have files, so that is visible before a comparison rather than as a failure
part-way through one.

THE CAVEAT TO CARRY INTO ANY BUILDER THAT USES THIS: the archive's
`Registration` column is self-reported and is sometimes 0 — Calhoun 2026, all
of Brown 2020 — so a floor keyed on it fires on the publisher's blank rather
than on a real loss. Nothing here reads it.

Usage:
    python3 scripts/isbe_precinct_fabric.py --list
    python3 scripts/isbe_precinct_fabric.py --compare 66 69
    python3 scripts/isbe_precinct_fabric.py --compare 62 66 --county CALHOUN
"""

import argparse
import collections
import csv
import io
import os
import re
import sys
import glob
import json
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scraper_common import UA_HINTS_CHROME_126, make_fail  # noqa: E402

BASE = "https://www.elections.il.gov"
TOTALS = BASE + "/ElectionOperations/ElectionVoteTotals.aspx"
# BALLOT CLASSES, NOT PRECINCTS. ISBE reports several ballot classes as if they
# were precincts, and counting them makes a county look re-precincted every time
# the ballot changes: on the first statewide run, the 2024 General's
# "PRESIDENTIAL ONLY BALLOT" row simply does not exist in 2026, which read as a
# lost precinct in 30-odd counties at once. That is the cry-wolf failure this
# tripwire would die of.
#
# The vocabulary was MEASURED across both elections rather than guessed — 130
# such names in three families:
#   -F12, -FED01, FEDERAL-F03   a UOCAVA class reported beside its precinct
#   PE01 FED ONLY, FED ONLY 16TH DEM, KI01 16TH FED ONLY
#   PRESIDENT ONLY, PRESIDENTIAL BALLOT ONLY, PRESIDENTIAL ONLY BALLOT
#
# Each pattern is deliberately narrow. `-(F|FED)\d+` matches digits after the
# dash and nothing else, because Calhoun's HARDIN-GILEAD and BELLEVIEW-HAMBURG
# are merged precincts whose real names end in `-<letters>`; and "ONLY" is only
# ever read as a ballot class when FED or PRESIDENT stands beside it.
FEDERAL_ONLY = re.compile(r"-(?:F|FED)\d+$", re.I)
BALLOT_CLASS = re.compile(r"\bFED\s+ONLY\b|\bPRESIDENT(?:IAL)?\b.*\bONLY\b", re.I)


def is_ballot_class(name):
    """True for a reporting unit that is a ballot type rather than a place."""
    return bool(FEDERAL_ONLY.search(name) or BALLOT_CLASS.search(name))


# THE TRAILING `-<digits>` IS A REPORTING ID, NOT PART OF THE PRECINCT'S NAME,
# and reading it as one is what made the first version of this check report four
# counties as having gained precincts when none had.
#
# The tell is that the id REPEATS across different precincts and CHANGES between
# elections. Cass's 2026 primary carries `-002` on six different precincts —
# Ashland 20, Ashland 21, Chandlerville 18, Newmansville 19, Panther Creek 17 and
# Philadelphia 16 — which is a polling place shared by six precincts, not a
# precinct number. And Chandlerville appears twice, as `CHANDLERVILLE 18-002` and
# `CHANDLERVILLE 18-012`: one precinct reported at two ids, which the raw
# comparison counted as two precincts and called Cass 21 -> 23.
#
# A PRECINCT'S OWN NUMBER IS SPACE-SEPARATED and survives: `BEARDSTOWN 5-004`
# strips to `BEARDSTOWN 5`, `GOREVILLE 1-1` to `GOREVILLE 1`, `WINCHESTER III-9`
# to `WINCHESTER III`. So a county that genuinely adds a precinct still shows a
# new name here; only the id collapses.
#
# MEASURED against the 33 counties whose precincts this app ships, 2026 primary:
# exact name-set agreement goes from 12/33 raw to 21/33 stripped, and NOT ONE
# county that agreed raw stops agreeing — the rule strictly improves
# reconciliation rather than trading one error for another. All four counties the
# first run wrongly flagged (Cass, Greene, Johnson, Scott) reconcile on count,
# three of them on names exactly.
#
# It leaves Calhoun alone, which is the check that matters most: neither its 2022
# nor its 2024 names carry a trailing `-<digits>`, so the 7-to-5 merge this script
# is validated against still reads exactly as it did.
REPORTING_ID = re.compile(r"-\d+$")


def precinct_key(name):
    """The precinct's own name, with any trailing reporting id removed."""
    return REPORTING_ID.sub("", name).strip()

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fail = make_fail("isbe-precinct-fabric")


def _get(url, timeout=180):
    req = urllib.request.Request(url, headers=UA_HINTS_CHROME_126)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def elections():
    """[(id, label)] from the results page's own election dropdown."""
    html = _get(TOTALS, timeout=60).decode("utf-8", "replace")
    m = re.search(r'<select[^>]*ddlElections[^>]*>(.*?)</select>', html, re.S | re.I)
    if not m:
        fail("no election dropdown on %s — the page's structure changed" % TOTALS)
    return re.findall(r'<option[^>]*value="(\d+)"[^>]*>([^<]*)</option>', m.group(1))


# Offices elected by the WHOLE STATE, so their results file carries every
# election authority. A congressional or judicial file covers only part of the
# state, and comparing two elections through one would silently compare a
# subset. Ordered by how reliably each appears on a ballot.
STATEWIDE_OFFICES = (
    "PRESIDENT AND VICE PRESIDENT", "PRESIDENT",
    "GOVERNOR AND LIEUTENANT GOVERNOR", "UNITED STATES SENATOR",
    "ATTORNEY GENERAL", "SECRETARY OF STATE", "COMPTROLLER", "TREASURER",
)


def _form_tokens(html):
    out = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        m = re.search(r'id="%s"[^>]*value="([^"]*)"' % name, html)
        if m:
            out[name] = m.group(1)
    return out


def csv_links(election_id):
    """[(office, url)] for one election, by replaying the page's own postback.

    The page shows only the election it is CURRENTLY displaying, which defaults
    to the newest — so a comparison against any past election has to select it
    first. The election dropdown carries an ASP.NET AutoPostBack, so selecting
    the option IS the submit; this replays that with the form's own three
    tokens rather than guessing a filename, because the office code and the
    election's tag ("2024GE") are not derivable from the election id.
    """
    html = _get(TOTALS, timeout=60).decode("utf-8", "replace")
    data = _form_tokens(html)
    if not data:
        fail("no ASP.NET form tokens on %s — the page's structure changed" % TOTALS)
    data.update({
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlElections",
        "__EVENTARGUMENT": "",
        "ctl00$ContentPlaceHolder1$ddlElections": str(election_id),
    })
    headers = dict(UA_HINTS_CHROME_126)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(TOTALS, data=urllib.parse.urlencode(data).encode(),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        page = resp.read().decode("utf-8", "replace")
    out = []
    for href in re.findall(r'href="([^"]*ByOffice[^"]*\.csv)"', page, re.I):
        path = href.replace("\\", "/")
        if "/%s/" % election_id not in path:
            continue
        office = os.path.basename(path).rsplit("-", 1)[0].split("-", 2)[-1]
        out.append((office.upper(), BASE + urllib.parse.quote(path)))
    return out


def csv_url_for(election_id):
    """The statewide results CSV for one election, or the widest available."""
    links = csv_links(election_id)
    if not links:
        fail("election %s links no results CSV — try --list for the ids that exist"
             % election_id)
    for want in STATEWIDE_OFFICES:
        for office, url in links:
            if office == want:
                return url, office
    # No statewide office on this ballot (a consolidated election has none).
    # Take the first and let the caller report how many authorities it covered.
    return links[0][1], links[0][0]


def precincts_for(election_id):
    """({AUTHORITY: {precinct name}}, office) for one election."""
    url, office = csv_url_for(election_id)
    rows = csv.DictReader(io.StringIO(_get(url).decode("utf-8-sig", "replace")))
    out = collections.defaultdict(set)
    for row in rows:
        name = (row.get("PrecinctName") or "").strip()
        if not name or is_ballot_class(name):
            continue
        out[(row.get("JurisName") or "").strip().upper()].add(
            precinct_key(name.upper()))
    if not out:
        fail("election %s's CSV parsed to zero precincts — the columns changed "
             "(expected JurisName + PrecinctName)" % election_id)
    return out, office


# A change that survives the id strip can still be COSMETIC — the county
# restyling its labels rather than moving a line. Measured on the 2024-to-2026
# pair, all four remaining shipped-county findings are exactly this: Hancock and
# Jefferson gained a full stop (ST ALBANS -> ST. ALBANS, MT VERNON -> MT. VERNON),
# Menard put spaces around a hyphen (NORTH ATHENS-CITY -> NORTH ATHENS - CITY),
# and Warren collapsed a double space (MONMOUTH  1 -> MONMOUTH 1).
#
# These are NOT filtered out, because a renamed precinct is a real event for this
# repo: several builders join a county's precincts to census geography BY NAME
# (the Jasper test), and every one of those joins breaks on a full stop. They are
# LABELLED instead, so a reader can tell in one line whether to rebuild geometry
# or to fix an alias.
def _loose(name):
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def classify(gone, added):
    """'cosmetic' when the two sides differ only in punctuation or spacing."""
    return ("cosmetic" if {_loose(x) for x in gone} == {_loose(x) for x in added}
            else "fabric")


def compare(older, newer, only=None):
    a, office_a = precincts_for(older)
    b, office_b = precincts_for(newer)
    print("  read %s via %s (%d authorities) and %s via %s (%d authorities)"
          % (older, office_a, len(a), newer, office_b, len(b)), file=sys.stderr)
    shared = sorted(set(a) & set(b))
    if only:
        shared = [j for j in shared if only.upper() in j]
    moved = []
    for juris in shared:
        gone, added = sorted(a[juris] - b[juris]), sorted(b[juris] - a[juris])
        if gone or added:
            moved.append((juris, len(a[juris]), len(b[juris]), gone, added,
                          classify(gone, added)))
    return moved, shared, sorted(set(a) ^ set(b))


def shipped_counties():
    """{NORMALISEDNAME: path} for every county whose precincts this app ships."""
    out = {}
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "il", "data", "app",
                                              "*-precincts.json"))):
        slug = os.path.basename(path).replace("-precincts.json", "")
        out[re.sub(r"[^A-Z]", "", slug.upper())] = path
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--list", action="store_true", help="list election ids")
    ap.add_argument("--compare", nargs=2, metavar=("OLDER", "NEWER"),
                    help="two election ids, oldest first")
    ap.add_argument("--county", help="limit the comparison to one authority")
    ap.add_argument("--shipped", action="store_true",
                    help="report only counties whose precincts this app ships")
    args = ap.parse_args()

    if args.list:
        print("  id   election                       results CSVs")
        for eid, label in elections():
            try:
                links = csv_links(eid)
            except Exception:  # noqa: BLE001 - a listing must not die on one row
                links = []
            offices = {o for o, _ in links}
            wide = next((o for o in STATEWIDE_OFFICES if o in offices), None)
            note = ("%2d  (statewide: %s)" % (len(links), wide) if wide
                    else "%2d  %s" % (len(links),
                                      "(none — consolidated elections carry no CSVs)"
                                      if not links else "(no statewide office; a subset)"))
            print("  %-4s %-30s %s" % (eid, " ".join(label.split()), note))
        return
    if not args.compare:
        ap.print_help()
        return

    older, newer = args.compare
    moved, shared, only_one = compare(older, newer, args.county)
    total_moved = len(moved)
    if args.shipped:
        ships = shipped_counties()
        moved = [m for m in moved if re.sub(r"[^A-Z]", "", m[0].upper()) in ships]
    print("isbe-precinct-fabric: %d authority(ies) reported in both elections; "
          "%d changed their precinct names%s"
          % (len(shared), total_moved,
             "; %d of them are counties whose precincts this app ships" % len(moved)
             if args.shipped else ""))
    if only_one:
        print("  (in one election only, not compared: %s)" % ", ".join(only_one[:6]))
    kinds = collections.Counter(m[5] for m in moved)
    if moved:
        print("  %d fabric change(s), %d cosmetic (punctuation or spacing only — "
              "no line moved, but a name join breaks on one)"
              % (kinds.get("fabric", 0), kinds.get("cosmetic", 0)))
    for juris, na, nb, gone, added, kind in moved:
        print("\n  %s [%s] — %d -> %d precinct(s)" % (juris, kind.upper(), na, nb))
        if gone:
            print("      gone : %s%s" % (", ".join(gone[:8]), " …" if len(gone) > 8 else ""))
        if added:
            print("      added: %s%s" % (", ".join(added[:8]), " …" if len(added) > 8 else ""))
    if not moved:
        print("  No authority changed a precinct name between these elections.")


if __name__ == "__main__":
    main()

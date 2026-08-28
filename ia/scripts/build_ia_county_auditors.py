#!/usr/bin/env python3
"""
Build data/app/ia-county-auditors.json — one row per Iowa county, keyed by
5-digit FIPS GEOID, naming its county auditor (Iowa Code 47.2 designates the
office as the county's own election commissioner). Read by ia/index.html's
County card, joined by GEOID the same way Wisconsin's county-clerk roster is.

WHERE THE DATA CAME FROM
-------------------------
ia_county_auditor_scraper.py reads all 99 rows off the Iowa State
Association of County Auditors' own directory (iowaauditors.org/find/directory/,
verified 2026-08-28: plain server-rendered HTML, name + party [as an icon
class, absent on 5 of 99] + office address + phone; no e-mail is published).
This builder only joins that cache to state-counties.json's GEOID by county
name — the join is exact for all 99 counties (verified 2026-08-28, no alias
table needed).

Usage:
    python3 ia/scripts/ia_county_auditor_scraper.py     # refresh the cache first
    python3 ia/scripts/build_ia_county_auditors.py
    python3 ia/scripts/build_ia_county_auditors.py --check
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
COUNTIES = os.path.join(APP_DATA_DIR, "state-counties.json")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "ia_county_auditors.json")
OUT = os.path.join(APP_DATA_DIR, "ia-county-auditors.json")

EXPECT_COUNTIES = 99


def main():
    check_only = "--check" in sys.argv[1:]

    with open(COUNTIES) as f:
        counties = json.load(f)
    geoid_by_name = {}
    for feat in counties["features"]:
        p = feat["properties"]
        geoid_by_name[p["BASENAME"]] = p["GEOID"]
    if len(geoid_by_name) != EXPECT_COUNTIES:
        raise RuntimeError(
            "state-counties.json carries %d counties, expected %d"
            % (len(geoid_by_name), EXPECT_COUNTIES)
        )

    try:
        with open(CACHE) as f:
            records = json.load(f)
    except OSError as e:
        raise RuntimeError(
            "no auditor cache at %s (%s) — run "
            "ia/scripts/ia_county_auditor_scraper.py first" % (CACHE, e)
        )
    if len(records) != EXPECT_COUNTIES:
        raise RuntimeError(
            "auditor cache carries %d records, expected %d" % (len(records), EXPECT_COUNTIES)
        )

    unmatched = sorted(r["county"] for r in records if r["county"] not in geoid_by_name)
    if unmatched:
        raise RuntimeError(
            "%d auditor county name(s) do not match state-counties.json's BASENAME: %s"
            % (len(unmatched), unmatched)
        )

    directory = {}
    for r in records:
        geoid = geoid_by_name[r["county"]]
        entry = {"county": r["county"], "name": r["name"], "office": r["office"],
                  "address": r["address"], "phone": r["phone"]}
        if r["party"]:
            entry["party"] = r["party"]
        directory[geoid] = entry

    missing = sorted(set(geoid_by_name.values()) - set(directory.keys()))
    if missing:
        raise RuntimeError("no auditor record for GEOID(s): %s" % missing)

    with_party = sum(1 for v in directory.values() if v.get("party"))
    print("ia-county-auditors: %d counties, %d with a party on record"
          % (len(directory), with_party), file=sys.stderr)

    payload = json.dumps(directory, indent=1, sort_keys=True) + "\n"
    if check_only:
        try:
            with open(OUT) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError(
                "data/app/ia-county-auditors.json is missing (%s) — run this "
                "script without --check" % e
            )
        if shipped != payload:
            raise RuntimeError(
                "data/app/ia-county-auditors.json has drifted from the auditor "
                "cache. Re-run: python3 ia/scripts/build_ia_county_auditors.py"
            )
        print("check: shipped roster matches the auditor cache", file=sys.stderr)
        return

    with open(OUT, "w") as f:
        f.write(payload)
    print("wrote data/app/ia-county-auditors.json", file=sys.stderr)


if __name__ == "__main__":
    main()

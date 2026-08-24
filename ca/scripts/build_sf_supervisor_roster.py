#!/usr/bin/env python3
"""
Build the SF Board of Supervisors roster (district -> current supervisor) as a
same-origin app-data file, so the supervisor-district card names the officeholder
without a live DataSF call at click time.

Source: DataSF "Current Supervisor Districts" (hcgx-vtsb) carries the current
sup_name per district — the same dataset the boundary geometry comes from, but
the volatile name is deliberately kept OUT of the decadal geometry
(build_embedded_boundaries.py strips it) and served here (network-first),
joined to the boundary by district number.

A weekly GitHub Action (.github/workflows/update-sf-supervisor-roster.yml) reruns
this and opens a PR when the roster changes, so officeholder data gets a human
look before it ships. Names are never guessed: a district missing from the source
simply doesn't appear, and the card falls back to the Board link.

Usage:
    python3 build_sf_supervisor_roster.py [hcgx-vtsb.json] [output_dir]

With no arguments it downloads the source and writes to the repo's data/app/.
"""

import json
import os
import sys
import urllib.request

SOURCE_URL = "https://data.sfgov.org/resource/hcgx-vtsb.json?$select=sup_dist_num,sup_name&$limit=50"

# SF has 11 supervisor districts. Refuse to overwrite with a short result.
EXPECTED_DISTRICTS = 11

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "data", "app")


def load_rows(path):
    if path:
        with open(path) as f:
            return json.load(f)
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:
        return json.load(resp)


def resolve(rows):
    roster = {}
    for r in rows:
        district = (r.get("sup_dist_num") or "").strip()
        name = (r.get("sup_name") or "").strip()
        if district and name:
            roster[district] = {"name": name}
    return roster


def ordered(roster):
    def key(d):
        try:
            return (0, int(d))
        except ValueError:
            return (1, d)
    return {d: roster[d] for d in sorted(roster, key=key)}


def main():
    if len(sys.argv) > 3:
        print(f"usage: {sys.argv[0]} [hcgx-vtsb.json] [output_dir]", file=sys.stderr)
        sys.exit(1)

    src_path = sys.argv[1] if len(sys.argv) >= 2 else None
    out_dir = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_OUT_DIR
    roster = resolve(load_rows(src_path))

    if len(roster) < EXPECTED_DISTRICTS:
        print(
            f"WARNING: resolved {len(roster)} SF supervisor districts "
            f"(expected {EXPECTED_DISTRICTS}) — refusing to overwrite the roster",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sf-supervisor-members.json")
    with open(out_path, "w") as f:
        json.dump(ordered(roster), f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {out_path} ({len(roster)} districts)", file=sys.stderr)


if __name__ == "__main__":
    main()

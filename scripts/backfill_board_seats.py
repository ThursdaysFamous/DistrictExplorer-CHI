#!/usr/bin/env python3
"""
Stamp `seats` onto a shipped board roster whose SCRAPER CANNOT BE RUN.

WHY THIS EXISTS AND WHY IT IS NOT A HAND-EDIT. `seats` — the number of members a
county elects in each district — is emitted by the county's own build_*.py from
its SEATS_PER_DISTRICT constant, and that constant is the one place the number
lives. For most counties adding it is nothing: re-run the scraper, re-run the
builder, done. Three counties cannot do that, and their blocks are measured and
recorded, not suspected:

  DeKalb   — dekalbcounty.org moved behind a captcha around 2026-07-31, and the
             scraper's Internet-Archive rung now answers 429 as well.
  Kendall  — blocks every automated client including the Archive's crawler; its
             roster is hand-verified (see CLAUDE.md).
  McHenry  — the same posture as Kendall, tracked on a standing issue.

Their rosters are otherwise correct and current. Rather than leave those five
multi-member counties half-converted — two able to say a district is short and
three not — this reads SEATS_PER_DISTRICT from the county's OWN BUILDER MODULE
and writes it onto the shipped file. The number therefore still has exactly one
source; only the delivery differs. It is idempotent, it refuses to touch a file
whose districts do not all hold at most that many members (which would mean the
constant is wrong, not the file), and it prints a no-op for a roster the builder
has already stamped — running it after a normal rebuild should change nothing,
which is the check that the two paths agree.

Usage:
    python3 scripts/backfill_board_seats.py            # all known counties
    python3 scripts/backfill_board_seats.py dekalb     # one county
    python3 scripts/backfill_board_seats.py --check    # non-zero if any is missing
"""

import importlib.util
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

# county -> (builder module filename, shipped roster filename)
COUNTIES = {
    "dekalb": ("build_dekalb_county_board_roster.py", "dekalb-county-board-members.json"),
    "kendall": ("build_kendall_county_board_roster.py", "kendall-county-board-members.json"),
    "mchenry": ("build_mchenry_county_board_roster.py", "mchenry-county-board-members.json"),
    "ogle": ("build_ogle_county_board_roster.py", "ogle-county-board-members.json"),
    "will": ("build_will_county_board_roster.py", "will-county-board-members.json"),
}


def seats_of(builder_filename):
    """SEATS_PER_DISTRICT out of the builder, read as source rather than imported.

    Importing would pull in whatever the builder imports; the constant is a bare
    integer literal on its own line, so reading it is both enough and cheaper.
    """
    path = os.path.join(REPO_ROOT, "scripts", builder_filename)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("SEATS_PER_DISTRICT"):
                return int(line.split("=", 1)[1].split("#")[0].strip())
    raise SystemExit("%s declares no SEATS_PER_DISTRICT" % builder_filename)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    names = args or sorted(COUNTIES)

    missing, changed = [], []
    for name in names:
        if name not in COUNTIES:
            raise SystemExit("unknown county %r (known: %s)" % (name, ", ".join(sorted(COUNTIES))))
        builder, filename = COUNTIES[name]
        seats = seats_of(builder)
        path = os.path.join(DATA_DIR, filename)
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        roster = json.loads(raw)
        # Write the file back the way its builder writes it. Kendall's and
        # McHenry's dump with indent=2 and the rest compact; normalising here
        # would show up as a whole-file diff now and get silently undone by the
        # next successful build.
        indent = 2 if raw.startswith("{\n") else None

        districts = {k: v for k, v in roster.items()
                     if isinstance(v, dict) and "members" in v}
        overfull = sorted(k for k, v in districts.items() if len(v["members"]) > seats)
        if overfull:
            raise SystemExit(
                "%s: districts %s hold more than %d member(s) — SEATS_PER_DISTRICT "
                "in %s disagrees with the shipped roster, so the constant is what "
                "needs fixing, not this file"
                % (name, ", ".join(overfull), seats, builder))

        todo = [k for k, v in districts.items() if v.get("seats") != seats]
        if not todo:
            print("backfill-seats: %-8s already carries seats=%d on all %d districts"
                  % (name, seats, len(districts)))
            continue
        missing.append(name)
        if check:
            print("backfill-seats: %-8s MISSING seats on %d district(s)" % (name, len(todo)))
            continue
        for k in todo:
            districts[k]["seats"] = seats
        with open(path, "w", encoding="utf-8") as f:
            json.dump(roster, f, ensure_ascii=False, indent=indent)
        changed.append(name)
        print("backfill-seats: %-8s stamped seats=%d on %d district(s)"
              % (name, seats, len(todo)))

    if check and missing:
        print("backfill-seats: FAIL — %s still missing seats" % ", ".join(missing),
              file=sys.stderr)
        sys.exit(1)
    if not check:
        print("backfill-seats: %d file(s) changed" % len(changed))


if __name__ == "__main__":
    main()

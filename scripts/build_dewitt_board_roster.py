#!/usr/bin/env python3
"""
Resolve scripts/dewitt_county_board_scraper.py's raw output into
data/app/dewitt-county-board-members.json, keyed by board district letter.

De Witt seats twelve members across four LETTERED districts (A-D), three
each, and elects its Chairman and Vice Chairman from among them.

THE COMPOSITION CROSS-CHECK — this is the part worth reading. The same page
this roster comes from is also the authority for the district BOUNDARIES:
scripts/build_dewitt_board_districts.py dissolves the county's precincts per
the composition printed on it. So this builder re-reads the composition the
scraper captured and compares it to the one compiled into that script. If the
county redraws its districts, the weekly roster run FAILS here — loudly, in a
job that runs every week — instead of leaving the shipped boundary quietly a
redistricting cycle out of date. A boundary derived from a page nobody watches
is exactly how the LaSalle defect happened.

The check is deliberately about the SET of precincts, not the exact wording:
the county writes "Santa Anna" for three numbered precincts and "Clintonia
7,8,9" in one breath, so both sides are normalized to a precinct set before
comparison.

Usage:
    python3 build_dewitt_board_roster.py <raw-scraper-output.json> [output_dir]
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_dewitt_board_districts import DISTRICTS as BOUNDARY_COMPOSITION  # noqa: E402
from scraper_common import make_fail  # noqa: E402  (shared machinery — do not fork)

SOURCE_URL = "https://www.dewittcountyil.gov/government/county_board.php"

EXPECT_DISTRICTS = ("A", "B", "C", "D")
MEMBERS_PER_DISTRICT = 3
MIN_PHONES = 8
MIN_EMAILS = 10
ALLOWED_ROLES = ("Chairman", "Vice-Chairman")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "il", "data", "app")


fail = make_fail("dewitt-board-roster")


def parse_composition(text):
    """Parse a composition string into {TOWNSHIP: set-of-numbers-or-None}.

    "Texas, Creek, Clintonia 7,8,9"        -> {TEXAS: None, CREEK: None,
                                               CLINTONIA: {7,8,9}}
    "Waynesville, ..., Clintonia 1 & 2"    -> {..., CLINTONIA: {1,2}}
    "Wilson, ..., Santa Anna, ..."         -> {..., SANTA ANNA: None}

    None means the county wrote the township bare, i.e. all of its precincts.
    Numbers are kept because they are where De Witt's districts actually
    differ — Clintonia's nine precincts are split across three districts, so a
    comparison that only reached township granularity would miss the most
    likely change there is. (It did: an earlier township-level version of this
    check passed a simulated "Clintonia 7,8" against a shipped "7,8,9".)
    """
    out, current = {}, None
    for chunk in re.split(r"\s*,\s*", (text or "").strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        # a bare number (or "8 & 9") continues the previous township
        if re.fullmatch(r"[\d\s&]+|(?:and\s*)?\d+", chunk, flags=re.I):
            if current is None:
                continue
            out[current] = (out.get(current) or set()) | _numbers(chunk)
            continue
        m = re.match(r"^(.*?)\s*((?:\d+[\s,&]*(?:and\s*)?)+)$", chunk, flags=re.I)
        if m and m.group(1).strip():
            current = _bare(m.group(1))
            out[current] = (out.get(current) or set()) | _numbers(m.group(2))
        else:
            current = _bare(chunk)
            out.setdefault(current, None)
    return out


def _numbers(text):
    return {int(n) for n in re.findall(r"\d+", text or "")}


def _bare(name):
    return " ".join(str(name).upper().split())


def boundary_composition(district):
    """The compiled boundary table in the same {TOWNSHIP: numbers} shape."""
    out = {}
    for name in BOUNDARY_COMPOSITION[district]:
        m = re.match(r"^(.*?)\s*(\d+)$", name)
        if m:
            key = _bare(m.group(1))
            out[key] = (out.get(key) or set()) | {int(m.group(2))}
        else:
            out.setdefault(_bare(name), None)
    return out


def compare_composition(district, published, shipped):
    """Return a human-readable difference, or None when they agree.

    A township the county writes BARE means "all of its precincts", so it
    matches the shipped side whether or not that side enumerates them (this is
    the "Santa Anna" case). A township the county NUMBERS must match exactly.
    """
    if set(published) != set(shipped):
        only_pub = sorted(set(published) - set(shipped))
        only_ship = sorted(set(shipped) - set(published))
        bits = []
        if only_pub:
            bits.append("the county now includes %s" % ", ".join(only_pub))
        if only_ship:
            bits.append("the county no longer includes %s" % ", ".join(only_ship))
        return "; ".join(bits)
    for township, nums in published.items():
        if nums is None:
            continue                      # written bare = all of it
        if shipped[township] is None or set(nums) != set(shipped[township]):
            return ("%s precincts changed: the county now says %s, the shipped boundary "
                    "was built from %s"
                    % (township, sorted(nums),
                       sorted(shipped[township]) if shipped[township] else "the whole township"))
    return None


def main():
    if len(sys.argv) < 2:
        fail("usage: build_dewitt_board_roster.py <raw-scraper-output.json> [output_dir]")
    with open(sys.argv[1], encoding="utf-8") as f:
        records = json.load(f)["records"]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR

    roster, seen_composition = {}, {}
    for rec in records:
        if not rec.get("name") or not rec.get("district"):
            continue
        district = str(rec["district"]).upper()
        role = rec.get("role")
        if role and role not in ALLOWED_ROLES:
            fail("%s carries unrecognized role %r" % (rec["name"], role))
        member = {"name": rec["name"]}
        for key in ("role", "phone", "email"):
            if rec.get(key):
                member[key] = rec[key]
        if rec.get("committees"):
            member["committees"] = rec["committees"]
        roster.setdefault(district, {"members": [], "sourceUrl": SOURCE_URL})
        roster[district]["members"].append(member)
        if rec.get("composition"):
            seen_composition.setdefault(district, rec["composition"])

    if sorted(roster) != sorted(EXPECT_DISTRICTS):
        fail("parsed districts %s, expected exactly %s" % (sorted(roster), list(EXPECT_DISTRICTS)))
    for d, entry in roster.items():
        if len(entry["members"]) != MEMBERS_PER_DISTRICT:
            fail("district %s has %d members, the county seats exactly %d per district"
                 % (d, len(entry["members"]), MEMBERS_PER_DISTRICT))
        entry["members"].sort(key=lambda m: m["name"].split()[-1])

    # --- the composition cross-check (see the module header)
    for d in EXPECT_DISTRICTS:
        published = parse_composition(seen_composition.get(d))
        if not published:
            fail("district %s published no precinct composition — the page's shape "
                 "changed, and the shipped boundary can no longer be cross-checked" % d)
        diff = compare_composition(d, published, boundary_composition(d))
        if diff:
            fail("district %s composition CHANGED — %s. Re-read the county board page "
                 "and rebuild data/app/dewitt-county-board-districts.json before "
                 "shipping this roster." % (d, diff))

    members = [m for e in roster.values() for m in e["members"]]
    phones = sum(1 for m in members if m.get("phone"))
    emails = sum(1 for m in members if m.get("email"))
    if phones < MIN_PHONES:
        fail("only %d phones resolved (expected >= %d)" % (phones, MIN_PHONES))
    if emails < MIN_EMAILS:
        fail("only %d e-mails resolved (expected >= %d)" % (emails, MIN_EMAILS))
    for role in ALLOWED_ROLES:
        held = [m["name"] for m in members if m.get("role") == role]
        if len(held) > 1:
            fail("%d members marked %s (%s) — the board has one" % (len(held), role, ", ".join(held)))

    out_path = os.path.join(out_dir, "dewitt-county-board-members.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    roles = sorted(m["role"] for m in members if m.get("role"))
    print("dewitt-board-roster: %d districts, %d members (%d phones, %d e-mails, roles: %s); "
          "composition matches the shipped boundary in all 4 districts -> %s"
          % (len(roster), len(members), phones, emails, ", ".join(roles) or "none", out_path))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build data/app/wi-circuit-judges.json from the wicourts scrape — stage 2 of
the pair (wi_circuit_judges_scraper.py is stage 1).

The join: the judges table's bench (authoritative) enriched per judge with the
contact page's branch number and direct phone, matched by normalized name.
Wisconsin's contact page prints judges ALL-CAPS ("WOOD, HON. DANIEL G. Br 1")
where the judges table prints display case, so matching is by
case-and-punctuation-folded surname + first token — a judge the contact page
lacks (or whose all-caps rendering title-cases differently, e.g. McDougal ->
Mcdougal) ships name-only rather than dropping. Fields degrade individually:
no e-mail exists anywhere on wicourts (measured), so none is invented.

Keyed by CIRCUIT KEY — the same keys build_wi_circuit_courts.py stamps on the
geometry (66 county slugs + buffalo-pepin, florence-forest,
menominee-shawano), so the card's join cannot disagree with the map.

Floors (refuses to write otherwise): exactly 69 circuit keys; >= 240 judges;
every circuit carries at least one judge and at least one courthouse address.
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "wi_circuit_judges_raw.json")
OUT = os.path.join(REPO_ROOT, "data", "app", "wi-circuit-judges.json")

EXPECT_CIRCUITS = 69
MIN_JUDGES = 240


def fold(name):
    return "".join(ch for ch in name.lower() if ch.isalpha() or ch == " ").split()


def match_key(name):
    parts = fold(name)
    if not parts:
        return None
    return (parts[-1], parts[0])  # (surname-ish, first token)


def main():
    raw_path = sys.argv[sys.argv.index("--in") + 1] if "--in" in sys.argv else RAW
    with open(raw_path) as f:
        raw = json.load(f)

    circuits = raw["circuits"]
    # The two pages spell county names differently ("Fond du Lac" in the
    # judges table, "Fond Du Lac" in the contact page's anchors), so the
    # contact lookup folds case and punctuation rather than trusting either
    # page's styling.
    def county_fold(name):
        return "".join(ch for ch in name.lower() if ch.isalnum())
    contact = {county_fold(k): v for k, v in raw["contact"].items()}
    if len(circuits) != EXPECT_CIRCUITS:
        raise SystemExit("scrape carries %d circuits, expected %d" % (len(circuits), EXPECT_CIRCUITS))

    out = {}
    total = 0
    for key, c in circuits.items():
        # branch/phone lookup across the circuit's counties (a merged
        # circuit's judge can sit in either county's courthouse block)
        enrich = {}
        courthouses = []
        for county in c["counties"]:
            block = contact.get(county_fold(county)) or {}
            for row in block.get("branch_rows", []):
                mk = match_key(row["name"])
                if mk and mk not in enrich:
                    enrich[mk] = row
            for addr in block.get("addresses", []):
                # first line is the judicial-district label; keep the location
                lines = [ln for ln in addr if not ln.lower().endswith("judicial district")]
                if lines and {"county": county, "lines": lines} not in courthouses:
                    courthouses.append({"county": county, "lines": lines})
        judges = []
        for j in c["judges"]:
            mk = match_key(j["name"])
            row = enrich.get(mk) if mk else None
            entry = {"name": j["name"]}
            if j.get("role"):
                entry["role"] = j["role"]
            if row:
                if row.get("branch"):
                    entry["branch"] = row["branch"]
                if row.get("phone"):
                    entry["phone"] = row["phone"]
                if row.get("role") and "role" not in entry:
                    entry["role"] = row["role"]
            judges.append(entry)
        if not judges:
            raise SystemExit("circuit %s parsed with no judges" % key)
        if not courthouses:
            raise SystemExit("circuit %s parsed with no courthouse address" % key)
        # A branch sort where branches exist keeps Milwaukee's 47 legible.
        judges.sort(key=lambda e: (int(e["branch"]) if e.get("branch", "").isdigit() else 999,
                                    e["name"].split()[-1]))
        total += len(judges)
        entry = {
            "counties": [n + " County" for n in c["counties"]],
            "judges": judges,
            "courthouses": courthouses[:4],
        }
        if c.get("clerkUrl"):
            entry["sourceUrl"] = c["clerkUrl"]
        out[key] = entry

    if total < MIN_JUDGES:
        raise SystemExit("only %d judges across the bench (floor %d)" % (total, MIN_JUDGES))

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
    enriched = sum(1 for c in out.values() for j in c["judges"] if "phone" in j)
    print("wrote %s — %d circuits, %d judges (%d with a direct phone), %.0f KB"
          % (OUT, len(out), total, enriched, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()

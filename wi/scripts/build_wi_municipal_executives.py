#!/usr/bin/env python3
"""
Write data/app/wi-municipal-executives.json from the scraper's raw capture.
Stage 2 of the pair; wi_municipal_executive_scraper.py is stage 1 and its
docstring carries the source, the witness rule and the measured outcome.

WHAT SHIPS, AND WHAT DELIBERATELY DOES NOT. A NAME ships only where the
municipality's own page witnessed it. Everything else about a municipality —
the office's own title ("City of Franklin Mayor"), the fact that the county
publishes an executive for it at all — is not in question and is not withheld.

CONTACT RIDES THE NAME, and that is a rule rather than a convenience. The
layer's e-mail addresses are PERSON-keyed (`jcyborowski@greendale.org`), so
shipping one beside a withheld name would publish the very name the witness
refused — the withholding would be cosmetic. Phone travels with it for the
same reason: the layer's numbers are direct lines, not switchboards. A
withheld municipality therefore carries its office title, its status and, when
the page answered at all, its link — never a person or a way to reach one.

THE LINK IS DROPPED WHEN IT 404s. Four of the layer's own `Exec_Url` values
are dead (Bayside, Hales Corners, South Milwaukee, West Allis), which is
corroborating evidence of the layer's 2024-07-30 vintage. A card must not hand
a reader a link this build already knows is broken, so `pageUrl` ships only
for a page that answered.

KEYED BY 7-DIGIT PLACE GEOID — "55" + the layer's own `Muni_Code`, which is
the Census place code (West Allis 85300 -> 5585300). That is the key the
municipality card already reads off its own feature, and the same join
Illinois's municipal roster uses.

THE FLOORS ARE MEASUREMENTS, NOT TARGETS (the Barron rule). 19 municipalities
is exact — Milwaukee County's incorporated count, and the scraper fails before
this if the dedupe gives anything else. MIN_WITNESSED is set BELOW the 9
measured on 2026-09-03 rather than at it: a village that redesigns its site
drops one honestly, and a build that refuses on that would wedge weekly for a
reason that is not a defect. It is a floor against the witness silently
breaking altogether.

Usage:
    python3 wi/scripts/build_wi_municipal_executives.py [--raw PATH] [--out PATH]
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "app")
DEFAULT_RAW = os.path.join(SCRIPT_DIR, ".cache", "wi_municipal_executives_raw.json")
DEFAULT_OUT = os.path.join(APP_DIR, "wi-municipal-executives.json")

EXPECT_MUNIS = 19
MIN_WITNESSED = 6          # 9 witnessed 2026-09-03; see the docstring
STATE_FIPS = "55"

# The county's own terms travel with the data (its item's licenseInfo opens
# "Use of this resource constitutes acknowledgement of these terms of use"),
# so the card credits the publisher by name.
SOURCE_NAME = "Milwaukee County GIS & Land Information"


def fail(msg):
    print("build-wi-municipal-executives: FAIL — %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    argv = sys.argv[1:]
    raw_path = argv[argv.index("--raw") + 1] if "--raw" in argv else DEFAULT_RAW
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else DEFAULT_OUT

    if not os.path.exists(raw_path):
        fail("no capture at %s — run wi/scripts/wi_municipal_executive_scraper.py first"
             % raw_path)
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)
    munis = raw.get("municipalities") or {}
    if len(munis) != EXPECT_MUNIS:
        fail("the capture holds %d municipalities, expected %d"
             % (len(munis), EXPECT_MUNIS))

    roster, witnessed = {}, 0
    for code, rec in munis.items():
        if not code.isdigit() or len(code) != 5:
            fail("municipality code %r is not a 5-digit place code, so the GEOID "
                 "join cannot be built" % code)
        geoid = STATE_FIPS + code
        entry = {
            "municipality": rec.get("municipality"),
            "office": rec.get("office"),
            "source": SOURCE_NAME,
            "sourceUrl": raw.get("source"),
        }
        if rec.get("witnessed"):
            witnessed += 1
            entry["name"] = rec.get("layerName")
            entry["witnessUrl"] = rec.get("pageUrl")
            # Contact rides the name — see the docstring.
            if rec.get("layerEmail"):
                entry["email"] = rec["layerEmail"]
            if rec.get("layerPhone"):
                entry["phone"] = rec["layerPhone"]
        else:
            entry["withheld"] = True
            entry["withheldWhy"] = rec.get("withheldWhy") or "not witnessed"
            # Only a link that actually answered.
            if rec.get("pageStatus") == "read" and rec.get("pageUrl"):
                entry["pageUrl"] = rec["pageUrl"]
        roster[geoid] = entry

    if witnessed < MIN_WITNESSED:
        fail("only %d of %d executive names were witnessed on the municipality's "
             "own page (floor %d). Either several sites reshaped at once or the "
             "witness itself broke — read the scraper's per-municipality log "
             "before lowering this." % (witnessed, len(roster), MIN_WITNESSED))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    withheld = len(roster) - witnessed
    print("build-wi-municipal-executives: OK — %d municipalities, %d name(s) "
          "shipped (witnessed on the municipality's own page), %d withheld -> %s"
          % (len(roster), witnessed, withheld, os.path.relpath(out_path, os.getcwd())))
    print("  withheld: %s" % ", ".join(sorted(
        v["municipality"] for v in roster.values() if v.get("withheld"))))
    print("  NOT CHECKED BY THIS BUILD: whether a witnessed name is still the "
          "sitting officer where the municipality's page is itself stale. The "
          "witness proves the county's layer and the municipality agree, which "
          "is the strongest available statement, not a guarantee.")


if __name__ == "__main__":
    main()

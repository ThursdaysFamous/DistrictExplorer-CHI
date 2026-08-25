#!/usr/bin/env python3
"""
Build data/app/county-board-directory.json — one row per Wisconsin county
naming its board's size and its own official page, so the supervisory-district
card can send a reader to the body that answers for them.

WHY THIS FILE EXISTS SEPARATELY FROM THE GEOMETRY
--------------------------------------------------
The districts come from one statewide publisher (LTSB). The PEOPLE do not:
Wisconsin has no statewide roster of county supervisors, so a reader's actual
supervisor is only ever published by their own county, 72 different ways. The
honesty rules say a card with no verifiable roster source links to the
official body rather than inventing a name, and this file is that link — one
verified URL per county, with the county's board size beside it.

It is also where a roster would land when one is built, which is why it is
keyed by county FIPS and shaped like the fleet's other roster files rather
than being folded into the geometry's properties.

WHERE THE URLS CAME FROM, AND WHY THEY ARE CURATED RATHER THAN DERIVED
----------------------------------------------------------------------
LTSB's district layer carries a CONTACT e-mail per county, which looks like a
free county-domain list and is not one. Five counties contract their GIS out,
so their contact is an ENGINEERING FIRM — Florence's is coleman-engineering
.com, Juneau's ncwrpc.org, Kewaunee's ruekert-mielke.com, Price's mi-tech.us,
Richland's msa-ps.com — and a card built from that list would have sent five
counties' readers to a consultancy captioned as their county board. Four more
contact domains host no website at all: Columbia, Crawford and Sauk are
MAIL-ONLY (no A record, live MX) and Iron's serves a certificate for another
name and 404s. Every URL below was fetched: 58 answer 200, 11 answer 403 to a
datacenter client while serving browsers normally, Barron and Shawano answer
503 to this client with DNS resolving, and Taylor sits behind an sgcaptcha
challenge that a person passes and no automation here tries to.

`seats` is the county's district count as SHIPPED — read back from the built
geometry rather than restated here, so the two can never disagree. The
counties marked below are the ones whose own board page independently named
districts 1..n matching that count when swept.

Usage:
    python3 wi/scripts/build_wi_county_board_directory.py
    python3 wi/scripts/build_wi_county_board_directory.py --check
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
GEOMETRY = os.path.join(APP_DATA_DIR, "county-supervisory-districts.json")
OUT = os.path.join(APP_DATA_DIR, "county-board-directory.json")
EXPECT_COUNTIES = 72

# county FIPS -> (name as LTSB spells it, the county's own official page).
# Hand-verified; see the module docstring for why this is not derived.
COUNTY_SITES = {
    "55001": ("Adams", "https://www.co.adams.wi.us/"),
    "55003": ("Ashland", "https://ashlandcountywi.gov/"),
    "55005": ("Barron", "https://co.barron.wi.us/"),
    "55007": ("Bayfield", "https://bayfieldcounty.wi.gov/295/Board-of-Supervisors"),  # county page confirms 1..13
    "55009": ("Brown", "https://www.browncountywi.gov/government/county-board-of-supervisors/"),  # county page confirms 1..26
    "55011": ("Buffalo", "https://www.buffalocountywi.gov/"),
    "55013": ("Burnett", "https://burnettcountywi.gov/264/Supervisors"),  # county page confirms 1..21
    "55015": ("Calumet", "https://calumetcounty.org/"),
    "55017": ("Chippewa", "https://chippewacountywi.gov/"),
    "55019": ("Clark", "https://www.clarkcountywi.gov/"),
    "55021": ("Columbia", "https://www.co.columbia.wi.us/ColumbiaCounty/"),
    "55023": ("Crawford", "https://www.crawfordcountywi.gov/"),
    "55025": ("Dane", "https://board.danecounty.gov/Supervisors"),
    "55027": ("Dodge", "https://co.dodge.wi.us/"),
    "55029": ("Door", "https://co.door.wi.gov/"),
    "55031": ("Douglas", "https://douglascountywi.gov/"),
    "55033": ("Dunn", "https://dunncountywi.gov/supervisors"),  # county page confirms 1..29
    "55035": ("Eau Claire", "https://eauclairecounty.gov/board_of_supervisors/district_representatives.php"),  # county page confirms 1..29
    "55037": ("Florence", "https://www.florencecountywi.com/"),
    "55039": ("Fond Du Lac", "http://fdlco.wi.gov/"),
    "55041": ("Forest", "https://co.forest.wi.gov/"),
    "55043": ("Grant", "https://co.grant.wi.gov/"),  # county page confirms 1..17
    "55045": ("Green", "https://greencountywi.org/164/County-Board-of-Supervisors"),  # county page confirms 1..31
    "55047": ("Green Lake", "https://www.greenlakecountywi.gov/"),
    "55049": ("Iowa", "https://www.iowacountywi.gov/"),
    "55051": ("Iron", "https://www.co.iron.wi.gov/"),
    "55053": ("Jackson", "https://www.co.jackson.wi.us/"),
    "55055": ("Jefferson", "https://jeffersoncountywi.gov/county_government/county_board/county_board_information/index.php"),  # county page confirms 1..30
    "55057": ("Juneau", "https://www.co.juneau.wi.gov/"),
    "55059": ("Kenosha", "https://www.kenoshacountywi.gov/142/County-Board-Supervisor-Districts"),  # county page confirms 1..23
    "55061": ("Kewaunee", "https://kewauneeco.com/"),
    "55063": ("La Crosse", "https://lacrossecounty.org/"),
    "55065": ("Lafayette", "https://lafayettecountywi.org/"),
    "55067": ("Langlade", "https://www.co.langlade.wi.us/"),
    "55069": ("Lincoln", "https://co.lincoln.wi.us/"),
    "55071": ("Manitowoc", "https://manitowoccountywi.gov/"),
    "55073": ("Marathon", "https://marathoncounty.gov/"),
    "55075": ("Marinette", "https://www.marinettecountywi.gov/county_board/"),
    "55077": ("Marquette", "https://www.marquettecountywi.gov/government/county-board-supervisors/"),  # county page confirms 1..17
    "55078": ("Menominee", "https://www.co.menominee.wi.us/"),
    "55079": ("Milwaukee", "https://county.milwaukee.gov/EN"),
    "55081": ("Monroe", "https://co.monroe.wi.us/"),
    "55083": ("Oconto", "https://www.ocontocountywi.gov/307/County-Board-Supervisory-District-Maps"),  # county page confirms 1..31
    "55085": ("Oneida", "https://www.oneidacountywi.gov/"),
    "55087": ("Outagamie", "https://www.outagamie.gov/"),
    "55089": ("Ozaukee", "https://ozaukeecounty.gov/2206/Supervisory-District-Maps"),  # county page confirms 1..26
    "55091": ("Pepin", "https://www.co.pepin.wi.us/"),
    "55093": ("Pierce", "https://co.pierce.wi.us/"),
    "55095": ("Polk", "https://www.polkcountywi.gov/government/county_board_of_supervisors/index.php"),  # county page confirms 1..15
    "55097": ("Portage", "https://www.co.portage.wi.gov/"),  # county page confirms 1..25
    "55099": ("Price", "https://co.price.wi.us/"),
    "55101": ("Racine", "https://racinecounty.gov/"),
    "55103": ("Richland", "https://richlandcountywi.gov/"),
    "55105": ("Rock", "https://co.rock.wi.us/"),
    "55107": ("Rusk", "https://ruskcountywi.gov/"),
    "55109": ("St Croix", "https://sccwi.gov/"),
    "55111": ("Sauk", "https://www.co.sauk.wi.us/"),
    "55113": ("Sawyer", "https://www.sawyercounty.gov/"),
    "55115": ("Shawano", "https://shawanocountywi.gov/"),
    "55117": ("Sheboygan", "https://sheboygancounty.com/"),
    "55119": ("Taylor", "https://co.taylor.wi.us/"),
    "55121": ("Trempealeau", "https://co.trempealeau.wi.us/"),  # county page confirms 1..17
    "55123": ("Vernon", "https://www.vernoncountywi.gov/government/county_board_of_supervisors/index.php"),  # county page confirms 1..19
    "55125": ("Vilas", "http://www.vilascountywi.gov/departments/administration___officials/county_board_members/index.php"),  # county page confirms 1..21
    "55127": ("Walworth", "https://co.walworth.wi.us/534/Board-of-Supervisors"),  # county page confirms 1..11
    "55129": ("Washburn", "https://co.washburn.wi.us/county-board-supervisors/"),  # county page confirms 1..21
    "55131": ("Washington", "https://www.washcowisco.gov/departments/county_board"),  # county page confirms 1..21
    "55133": ("Waukesha", "https://www.waukeshacounty.gov/waukesha-county-board/"),  # county page confirms 1..25
    "55135": ("Waupaca", "https://www.waupacacounty-wi.gov/"),
    "55137": ("Waushara", "https://www.wausharacountywi.gov/13370/county-board-of-supervisors"),  # county page confirms 1..11
    "55139": ("Winnebago", "https://www.winnebagocountywi.gov/703/County-Board-of-Supervisors"),  # county page confirms 1..36
    "55141": ("Wood", "https://woodcountywi.gov/CountyBoard/"),  # county page confirms 1..19
}


def main():
    check_only = "--check" in sys.argv[1:]
    with open(GEOMETRY) as f:
        geo = json.load(f)

    seats = {}
    names = {}
    for feat in geo["features"]:
        p = feat["properties"]
        seats[p["CNTY_FIPS"]] = max(seats.get(p["CNTY_FIPS"], 0), int(p["SUPERID"]))
        names[p["CNTY_FIPS"]] = p["CNTY_NAME"]

    if len(seats) != EXPECT_COUNTIES:
        raise RuntimeError("geometry covers %d counties, expected %d" % (len(seats), EXPECT_COUNTIES))
    missing = sorted(set(seats) - set(COUNTY_SITES))
    extra = sorted(set(COUNTY_SITES) - set(seats))
    if missing or extra:
        raise RuntimeError("county table and geometry disagree — missing %s, extra %s"
                           % (missing, extra))
    for fips, (name, url) in COUNTY_SITES.items():
        if name != names[fips]:
            raise RuntimeError("county %s is %r in the geometry and %r in the table"
                               % (fips, names[fips], name))
        if not url.startswith("https://") and not url.startswith("http://"):
            raise RuntimeError("county %s has no usable URL: %r" % (fips, url))

    directory = {
        fips: {"county": name, "seats": seats[fips], "url": url}
        for fips, (name, url) in sorted(COUNTY_SITES.items())
    }
    total = sum(v["seats"] for v in directory.values())
    print("county-board-directory: %d counties, %d supervisory seats, %d official links"
          % (len(directory), total, len(directory)), file=sys.stderr)

    payload = json.dumps(directory, indent=1, sort_keys=True) + "\n"
    if check_only:
        # The DRIFT gate, and it has to compare bytes rather than re-run the
        # validation above: `seats` is read back from the geometry, so the way
        # these two files come apart is someone rebuilding the districts and
        # not rebuilding this — which every check above still passes.
        try:
            with open(OUT) as f:
                shipped = f.read()
        except OSError as e:
            raise RuntimeError("data/app/county-board-directory.json is missing (%s) — run this "
                               "script without --check" % e)
        if shipped != payload:
            raise RuntimeError(
                "data/app/county-board-directory.json has drifted from the shipped districts. "
                "Re-run: python3 wi/scripts/build_wi_county_board_directory.py"
            )
        print("check: shipped directory matches the shipped districts", file=sys.stderr)
        return

    with open(OUT, "w") as f:
        f.write(payload)
    print("wrote data/app/county-board-directory.json", file=sys.stderr)


if __name__ == "__main__":
    main()

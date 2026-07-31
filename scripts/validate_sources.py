#!/usr/bin/env python3
"""
Source freshness gate for the app's data layers.

Why this exists: unlike the roster scrapers (which re-pull the same page every
week), several layers point at a *specific* upstream dataset that the publisher
silently supersedes with a new one:

  * Chicago Data Portal (Socrata) datasets are versioned by year. The CPS
    attendance-boundary layers, for example, are published fresh every school
    year under a BRAND NEW dataset id (…SY2526 → …SY2627), so the id hardcoded
    in index.html keeps returning last year's boundaries long after a newer one
    exists. Nothing errors; the data just quietly goes stale.
  * The three shapefile-derived boundary layers (school board, IL Supreme
    Court, Cook County Board of Review) were downloaded once from decennial
    redistricting sources with no API. They change ~once a decade, so the check
    there is provenance: is the source we cite still reachable, and a reminder
    to re-verify.

This script does NOT edit index.html or any data file — swapping a dataset id
is a judgement call (the "newer" dataset may have a different schema), so, like
the roster workflows, it surfaces drift for a human instead of auto-applying it.

What it checks (findings carry a severity — FAIL, WARN, or OK):
  1. Manifest ↔ app coherence: every dataset id / data file the manifest knows
     about is still referenced in index.html (guards this file drifting from the
     app it validates).                                                   [FAIL]
  2. Socrata datasets: each id still resolves and still carries the stable part
     of its expected name (a rename usually means it was replaced).       [FAIL]
     For year-versioned datasets, the portal catalog is searched for a newer
     edition than the one in use.                                         [WARN]
  3. Shapefile provenance: the cited source URL is reachable and the built
     data/app file is present.                             [WARN / FAIL if gone]
  4. Live service endpoints (CPD ArcGIS, Census TIGERweb): reachable.      [WARN]

Exit status: 0 when nothing needs a human (OK or WARN only), 1 on any FAIL.
Newer-edition detection is deliberately WARN, not FAIL — the current dataset
still works and a person decides whether/when to migrate. The scheduled
workflow (.github/workflows/validate-sources.yml) opens an issue on WARN or
FAIL so drift is never silent, without turning the build red.

Usage:
    python3 scripts/validate_sources.py                 # human-readable report
    python3 scripts/validate_sources.py --report r.md   # also write markdown
    python3 scripts/validate_sources.py --status-file s.txt   # ok|warn|fail
    python3 scripts/validate_sources.py --offline       # manifest↔app checks only
"""

import argparse
import json
import os
import re
import sys

try:
    import requests
except ImportError:  # pragma: no cover - requests is pinned in requirements.txt
    requests = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

SOCRATA_DOMAIN = "data.cityofchicago.org"
CATALOG_API = "https://api.us.socrata.com/api/catalog/v1"
HTTP_TIMEOUT = 25

# ---------------------------------------------------------------------------
# The manifest: every source index.html depends on that can go stale silently.
#
# Socrata datasets — `name_contains` is the part of the portal title that must
# stay stable (a change means the dataset was replaced/renamed). `year_search`,
# when present, turns on newer-edition detection: the catalog is searched with
# `query`, results are kept only if their name also contains name_contains, and
# the `pattern` capture group (an int) is compared to pick the newest edition.
# ---------------------------------------------------------------------------
SOCRATA = [
    {"id": "p293-wvbd", "layer": "Ward + Alderman boundary",
     "name_contains": "Boundaries - Wards"},
    {"id": "htai-wnw4", "layer": "Alderman / Ward Offices",
     "name_contains": "Ward Offices"},
    {"id": "i8fv-xe4b", "layer": "Ward Precincts",
     "name_contains": "Boundaries - Ward Precincts"},
    {"id": "igwz-8jzy", "layer": "Community Area",
     "name_contains": "Boundaries - Community Areas"},
    # ZIP Code moved off Socrata to the statewide Census ZCTA layer (no city
    # boundary line) — the endpoint is tracked in ENDPOINTS below, not here.
    {"id": "x8fc-8rcq", "layer": "Library locations (nearest N)",
     "name_contains": "Libraries - Locations"},
    {"id": "x72b-38qv", "layer": "CPS Elementary School Zone",
     "name_contains": "Elementary School Attendance Boundaries",
     "year_search": {"query": "Elementary School Attendance Boundaries",
                     "pattern": r"SY(\d{4})"}},
    {"id": "xg7c-d8rm", "layer": "CPS High School Zone",
     "name_contains": "High School Attendance Boundaries",
     "year_search": {"query": "High School Attendance Boundaries",
                     "pattern": r"SY(\d{4})"}},
    {"id": "fyff-53xy", "layer": "CPS Middle School Zone",
     "name_contains": "Middle School Attendance Boundaries",
     "year_search": {"query": "Middle School Attendance Boundaries",
                     "pattern": r"SY(\d{4})"}},
    {"id": "pnta-kuqa", "layer": "CPS Network (K-8)",
     "name_contains": "Elementary Geographic Networks"},
    {"id": "aupu-jt2g", "layer": "CPS Network (High School)",
     "name_contains": "High School Geographic Networks"},
]

# Decennial boundary layers built into same-origin data/app files: no runtime
# API. `source_url` is the provenance we cite; `app_file` is the built file.
# These go stale only when the underlying districts are redrawn — the check is a
# reachability probe plus a standing reminder to re-verify against the source.
# The first three are shapefile-derived; the three legislative layers are
# pre-built from Census TIGERweb by scripts/build_legislative_boundaries.py
# (R2-2 — they used to query TIGERweb live at ~5.7 s per first toggle).
PROVENANCE = [
    {"layer": "School Board (ERSB) districts",
     "app_file": "school-board-districts.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "ERSB 20-subdistrict map (SB 15). Redrawn ~once a decade."},
    {"layer": "IL Supreme Court districts",
     "app_file": "il-supreme-court-districts.json",
     "source_url": "https://www.illinoiscourts.gov/",
     "note": "PA 102-0011 shapefile. Redrawn ~once a decade."},
    {"layer": "Cook County Board of Review districts",
     "app_file": "ccbr-districts.json",
     "source_url": "https://www.cookcountyboardofreview.com/",
     "note": "PA 102-0012 shapefile. Redrawn ~once a decade."},
    {"layer": "Kane 16th-Circuit judicial subcircuits",
     "app_file": "kane-judicial-subcircuits.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "PA 102-0693 enacted-subcircuits shapefile ZIP (archived in "
             "data/source/raw/). Redrawn ~once a decade; the county's own "
             "services are permission-locked, hence the shapefile route."},
    {"layer": "McHenry 22nd-Circuit judicial subcircuits",
     "app_file": "mchenry-judicial-subcircuits.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "Same PA 102-0693 enacted-subcircuits shapefile ZIP as Kane "
             "(archived in data/source/raw/). Redrawn ~once a decade; the "
             "county publishes no subcircuit service at all."},
    {"layer": "Ogle County Board districts (8, dissolved from Census 2020 precincts)",
     "app_file": "ogle-county-board-districts.json",
     "source_url": "https://www.oglecountyil.gov/county/resolutions_and_ordinances/index.php",
     "note": "Resolution R-2021-1106, ADOPTION OF THE OGLE COUNTY REAPPORTIONMENT "
             "MAP (adopted 2021-11-16), names the 52 precincts making up the 8 "
             "districts; build_ogle_board_districts.py dissolves the Census 2020 "
             "voting districts accordingly. The county publishes no district "
             "geometry. Supersedes R-2021-0607 (June 2021), whose District 5 "
             "omitted Leaf River entirely. Next reapportionment due after the "
             "2030 census; the pinned URL is the county's resolutions index, "
             "since the monthly PDF filename changes."},
    {"layer": "Carroll County Board districts (3, whole townships)",
     "app_file": "carroll-county-board-districts.json",
     "source_url": "https://www.carrollcountyil.gov/County.Board.District.Update.2021.pdf",
     "note": "The county's published 2021 district map, whose lines run exactly "
             "along township boundaries, so the districts are a plain TIGER "
             "township dissolve (build_carroll_board_districts.py). The map is a "
             "RASTER export with no polygons to extract — none were needed. The "
             "map labels Carroll's two consolidated townships by their historic "
             "halves (Cherry Grove/Shannon, Rock Creek/Lima) where TIGER carries "
             "the merged names; both sit wholly in District 3. Redrawn ~once a "
             "decade."},
    {"layer": "Stephenson County Board districts (8, lettered B-I; B-E georeferenced)",
     "app_file": "stephenson-county-board-districts.json",
     "source_url": "https://stephensoncountyil.gov/government/county_board/district_maps_2012.php",
     "note": "The county's adopted 2022-01-06 district maps. F-I are whole "
             "townships (exact, and each district's township populations sum to "
             "the total the map prints). B-E subdivide Freeport Township and are "
             "GEOREFERENCED from the Freeport map's vector precinct polygons "
             "(build_stephenson_board_districts.py; PDFs archived in "
             "data/source/raw/) — the only boundary in the app whose accuracy is "
             "a measured number rather than an exact match, ~20 m, stated on the "
             "card. DELETE that script if Stephenson ever publishes precinct "
             "geometry. Redrawn ~once a decade."},
    {"layer": "Winnebago 17th-Circuit judicial subcircuits",
     "app_file": "winnebago-judicial-subcircuits.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "PA 102-0693 enacted-subcircuits shapefile ZIP (archived in "
             "data/source/raw/) — the SAME archive Kane and McHenry were built "
             "from, which carries nine circuits where the app long shipped six. "
             "17th Circuit = Winnebago + Boone, the first counties outside the "
             "seven-county metro. Redrawn ~once a decade."},
    {"layer": "Madison 3rd-Circuit judicial subcircuits",
     "app_file": "madison-judicial-subcircuits.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "Same PA 102-0693 archive. 3rd Circuit = Madison + Bond "
             "(Metro East). Redrawn ~once a decade."},
    {"layer": "Sangamon 7th-Circuit judicial subcircuits",
     "app_file": "sangamon-judicial-subcircuits.json",
     "source_url": "https://www.ilsenateredistricting.com/",
     "note": "Same PA 102-0693 archive. 7th Circuit = Sangamon + Greene, "
             "Jersey, Macoupin, Morgan and Scott — the widest of the three, so "
             "this one file answers for six counties. Redrawn ~once a decade."},
    {"layer": "Kane County Board members (roster)",
     "app_file": "kane-county-board-members.json",
     "source_url": "https://www2.kanecountyil.gov/pages/countyboard/boardMembers.aspx",
     "note": "Scraped weekly from the county's own SharePoint Board Members list "
             "API (kane_county_board_scraper.py) — the same data this directory "
             "page renders client-side: party, office phones, emails, and the "
             "countywide-elected Chair. No bot block (verified 2026-07-23); the "
             "boundary GIS separately carries member names (cross-checked)."},
    {"layer": "Lake County Board leadership roles (roster)",
     "app_file": "lake-county-board-roles.json",
     "source_url": "https://www.lakecountyil.gov/2336/Board-Members",
     "note": "Chair/Vice-Chair tags scraped weekly from the county's own "
             "directory (lake_county_board_roles_scraper.py; requests with an "
             "Internet Archive fallback — the site's edge 403s datacenter "
             "clients, so a reachability WARN here is expected, not drift). "
             "Member names/contact stay live on the boundary GIS; the card "
             "applies a role only when this file's name matches the GIS."},
    {"layer": "Kendall County Board members (roster)",
     "app_file": "kendall-county-board-members.json",
     "source_url": "https://www.kendallcountyil.gov/county-board/board-members",
     "note": "Hand-verified 2026-07-23 against the county's own member directory "
             "+ per-member pages (incl. the Chairman, a District 2 member); the "
             "weekly scraper (kendall_county_board_scraper.py) attempts a "
             "refresh, but the county currently blocks ALL automated fetch — "
             "direct, real-browser, and the Internet Archive's crawler (SPN2 "
             "error:no-request) — so the workflow tracks the block on a standing "
             "issue and a reachability WARN here is expected, not drift."},
    {"layer": "McHenry County Board members (roster)",
     "app_file": "mchenry-county-board-members.json",
     "source_url": "https://www.mchenrycountyil.gov/departments/county-board/meet-your-county-board-members",
     "note": "Hand-verified 2026-07-23 against the county's own member directory "
             "(incl. the countywide-elected Chairman); the weekly scraper "
             "(mchenry_county_board_scraper.py) attempts a refresh, but the county "
             "currently blocks ALL automated fetch — direct, real-browser, and the "
             "Internet Archive's crawler (SPN2 error:no-request) — so the workflow "
             "tracks the block on a standing issue and a reachability WARN here is "
             "expected, not drift."},
    {"layer": "Illinois county clerks (roster)",
     "app_file": "il-county-clerks.json",
     "source_url": "https://www.elections.il.gov/ElectionOperations/ElectionAuthorities.aspx",
     "note": "Scraped weekly from ISBE's election-authority directory "
             "(il_county_clerk_scraper.py); Peoria deliberately absent (its "
             "authority is the appointed county election commission)."},
    {"layer": "Suburban municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.cookcountyclerkil.gov/elections/directory-elected-officials",
     "note": "Scraped weekly from the Cook County Clerk's Directory of Elected "
             "Officials JSON API (cook_municipal_officials_scraper.py), keyed by "
             "Census place GEOID. The site is Cloudflare-fronted, so a "
             "reachability WARN here can be a bot filter rather than drift — "
             "confirm with a browser User-Agent before treating it as a source "
             "change. Cook is one of twelve counties shipped in this file, each "
             "with its own entry below (see docs/EXPANSION_GUIDE.md Part 2 "
             "rule 5). Five jurisdiction types "
             "are read: MUNIS (municipalities + citywide officers), MUNIW "
             "(suburban ward/district seats), CHIWD (Chicago citywide) and "
             "CHICA (Chicago's 50 ward seats, the only verified source of their "
             "term data — the City's own roster htai-wnw4 publishes none). "
             "The county's Socrata copies of this directory (vw2r-zys4, "
             "jsup-zs8y) are frozen at 2014 and deliberately unused."},
    {"layer": "Will County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.willcountyclerk.gov/local-election-officials/",
     "note": "The Clerk page that LINKS the Will County Directory flipbook — "
             "pinned here rather than the flipbook itself because the book id "
             "changes with each edition and will_municipal_officials_scraper.py "
             "discovers it from this page. The page serves 202/empty to "
             "non-browser user agents, so a reachability WARN can be its bot "
             "filter rather than drift."},
    {"layer": "Will ward-city council contact (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.wilmington-il.com/city-officials",
     "note": "The bounded per-city exception to the source ladder "
             "(will_city_councils_scraper.py): the Will County Clerk's directory "
             "publishes no per-SEAT council contact, and omits Lockport and "
             "Wilmington entirely — their entry headers are missing from the "
             "flipbook's text layer, so no parser can recover them. The three "
             "cities' own sites supply per-seat phone/e-mail plus those two "
             "rosters. Pinned to Wilmington's page as the representative one; "
             "Crest Hill (cityofcresthill.com staff directory) and Lockport "
             "(cityoflockport.net/153) are the others. Joliet is deliberately "
             "unbuilt: joliet.gov 403s non-browser clients, jolietcity.org is "
             "client-rendered, and the only Archive snapshot is from 2022. The "
             "county clerk remains the roster of record — for a municipality the "
             "county covers, this source contributes contact only."},
    {"layer": "Joliet council contact (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.joliet.gov/government/city-council-3189",
     "note": "Per-seat phone + e-mail for the metro's third-largest city, which "
             "the Will Clerk's directory does not publish "
             "(joliet_council_contact_scraper.py). TERMINAL BLOCK (re-measured "
             "2026-07-28, correcting an earlier read): joliet.gov is Akamai "
             "serving a HARD WAF DENY — a 408-byte static page with an "
             "x-reference-error, not a solvable challenge — so the Playwright "
             "rung fails exactly as requests does and no rung carries this city. "
             "A reachability WARN here is EXPECTED and permanent. The Internet "
             "Archive was re-evaluated and declined on its merits, not its age: "
             "the captures are good (the archived index still yields all nine "
             "bio links, the bio pages still carry their e-mails) but the newest "
             "index capture is 69 days old against the fleet's 45-day guard, so "
             "a conventional rung would refuse every run — and preservation "
             "already carries Joliet's last-good entry from a live scrape, which "
             "beats a dated copy. The Clerk stays the roster of record; this "
             "adds contact only. Note jolietcity.org is NOT the city — it is a "
             "parked domain."},
    {"layer": "Skokie trustee districts (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.skokie.org/486/Board-of-Trustees",
     "note": "Skokie is the one municipality whose ward geometry the app maps "
             "while its county publishes no district for any seat: Cook GIS "
             "carries four Skokie district polygons, the Clerk's directory "
             "lists all six trustees as municipality-wide "
             "(skokie_trustee_districts_scraper.py). The village's own board "
             "page carries the assignment — four district trustees + two "
             "at-large since the April 2025 consolidated election, per its "
             "2025 Electoral Changes page — plus a per-trustee e-mail. The "
             "Clerk stays the roster of record; this fills the district and "
             "e-mail only. If Skokie's board structure changes, the scraper "
             "fails loudly rather than reshaping the card."},
    {"layer": "DuPage municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://dmmc-cog.org/membership-list/",
     "note": "DuPage County government publishes NO municipal-officials "
             "directory (verified negative), so the DuPage Mayors and Managers "
             "Conference directory is the source of record "
             "(dupage_municipal_officials_scraper.py). Pinned to the membership "
             "page, not the PDF: the PDF's URL carries its edition date and "
             "changes, and the scraper discovers it here. Head of government "
             "only — the directory prints no trustees."},
    {"layer": "Kane County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://clerk.kanecountyil.gov/Elections/Documents/GovernmentGuide.pdf",
     "note": "The Clerk's annual Government Guide, 'Cities and Village "
             "Officials' section (kane_municipal_officials_scraper.py). Stable "
             "URL, linked from clerk.kanecountyil.gov/elections. Head of "
             "government + municipal clerk only — the guide prints no trustees."},
    {"layer": "McHenry County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.mchenrycountyil.gov/county-government/county-yearbook/cities-villages",
     "note": "The Clerk's County Yearbook 'Cities & Villages' page "
             "(mchenry_municipal_officials_scraper.py). Akamai-fronted and it "
             "fingerprints the HTTP CLIENT, not just headers: measured 2026-07, "
             "curl gets 200 where python-requests gets 403 with a byte-identical "
             "browser header set, so Playwright is the day-one rung and a "
             "reachability WARN here is EXPECTED, not drift. Head of government "
             "+ elected clerk/treasurer only; appointed administrators are "
             "excluded deliberately."},
    {"layer": "Kendall County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.kendallcountyil.gov/home/showdocument?id=184",
     "note": "The Clerk's Yearbook & Government Guide PDF, CITY/VILLAGE "
             "OFFICIALS sections (kendall_municipal_officials_scraper.py). Same "
             "Akamai client-fingerprint posture as McHenry — a reachability WARN "
             "is EXPECTED. The yearbook misspells Minooka as 'Minnoka'; the "
             "scraper carries an explicit alias so the place still joins."},
    {"layer": "Lake County municipal hall contact (roster)",
     "app_file": "municipal-officials.json",
     "source_url": ("https://services3.arcgis.com/HESxeTbDliKKvec2/arcgis/rest/"
                    "services/Municipalities/FeatureServer/0"),
     "note": "Lake publishes NO municipal officeholder names anywhere "
             "county-side (double-verified negative: county/Clerk pages, GIS, "
             "and the Municipal League). This service supplies hall address, "
             "phone, e-mail, and website only, so Lake ships contact-only cards "
             "— the rule-4 honesty floor (lake_municipal_officials_scraper.py). "
             "If a Lake roster ever appears, this is the entry to upgrade."},
    {"layer": "Lee County Board roster",
     "app_file": "lee-county-board-members.json",
     "source_url": "https://www.leecountyil.com/419/Member-Contact-List",
     "note": "The Clerk's Member Contact List — a PDF served at a page-looking URL, and "
             "the only place Lee publishes its membership (the County Board page names "
             "the Chair and Vice-Chair only). Read by WORD POSITION (pdfplumber): pypdf "
             "flattens it into a name block and a separately-ordered e-mail block, so a "
             "line-based read pairs members with the wrong addresses. The Board Chair is "
             "identified by his row carrying the shared leecochair@countyoflee.org "
             "address rather than a personal one."},
    {"layer": "Rock Island County Board roster",
     "app_file": "rock-island-county-board-members.json",
     "source_url": "https://www.rockislandcountyil.gov/263/County-Board",
     "note": "The county's board page — a CivicPlus staff-directory widget with "
             "h-card microformat classes (p-name, p-job-title), so this is a "
             "class parse rather than a text-shape guess. 19 single-member "
             "districts. The Chairman appears TWICE on the page (a prose block "
             "above the widget, and again as his district's member); he is "
             "deduped onto his district row and tagged there, because the county "
             "elects its chair from among the 19. The scraper refuses any "
             "single-member district that ends up holding two names."},
    {"layer": "LaSalle County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://lasallecountyil.gov/294/Officials",
     "note": "The Clerk's Municipality Officials PDF, linked from this page "
             "(lasalle_municipal_officials_scraper.py). Full governing body — "
             "every trustee and ward number — from one county document. Its "
             "directory is a six-column table whose columns interleave, so it "
             "is the one source in this file read from word POSITIONS "
             "(pdfplumber) rather than from extracted lines."},
    {"layer": "Winnebago County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://maps.wingis.org/public/rest/services/ElectedOfficials/MapServer",
     "note": "The only source in the fleet that publishes municipal governing "
             "bodies AS GIS LAYERS — one layer per municipality on WinGIS's "
             "ElectedOfficials service (winnebago_municipal_officials_scraper.py). "
             "A layer disappearing is the drift to watch for here, not a URL "
             "change. WinGIS publishes no mayor/president layer for Loves Park "
             "or Machesney Park, which is why the builder's Winnebago head "
             "floor sits below its municipality floor."},
    {"layer": "Ogle County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://www.oglecountyil.gov/departments/county_clerk/index.php",
     "note": "The Clerk's yearbook, 'OGLE COUNTY CITIES & VILLAGES' section "
             "(ogle_municipal_officials_scraper.py) — full governing body plus "
             "hall address, phone and website for all 13 municipalities. Pinned "
             "to the Clerk page rather than the PDF because the yearbook "
             "filename carries its edition ('2025- 2027 Yearbook.pdf'). Adeline "
             "is the one entry that labels a PHYSICAL and a MAILING address at "
             "different places; the scraper keeps them apart deliberately."},
    {"layer": "Stephenson County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": ("https://stephensoncountyil.gov/government/"
                    "boards_commissions_committees/city_and_villages.php"),
     "note": "The county's Cities & Villages directory "
             "(stephenson_municipal_officials_scraper.py) — full governing body "
             "for 10 of the county's 11 municipalities, and the only source in "
             "this file that marks each office '(Elected)' or '(Appointed)' "
             "explicitly. FREEPORT IS NOT ON THIS PAGE: the county seat comes "
             "from the city's own site, below. The address column is board "
             "members' RESIDENCES and is deliberately not collected."},
    {"layer": "Freeport city council (roster)",
     "app_file": "municipal-officials.json",
     "source_url": "https://cityoffreeport.org/wp-json/wp/v2/lsvr_person_cat?slug=elected-officials",
     "note": "Freeport is the one Stephenson municipality its county page omits "
             "— and it is the county seat, holding more than half the county's "
             "municipal population (freeport_council_scraper.py). Membership is "
             "a WordPress REST query on the city's own 'elected-officials' "
             "category, and each person page carries a schema.org Person block. "
             "The city ALSO publishes a Wards2022_Public FeatureServer with an "
             "Alderperson field: it is stale (data last edited 2024-05-21, "
             "still naming a pre-2025-election holder) and must not be used for "
             "officeholders — only its geometry would be sound."},
    {"layer": "Carroll County municipal governing bodies (roster)",
     "app_file": "municipal-officials.json",
     "source_url": ("https://www.carrollcountyil.gov/county_departments/"
                    "clerk___recorder/index.php"),
     "note": "The Clerk's yearbook, 'Cities and Village Officers' section "
             "(carroll_municipal_officials_scraper.py) — head of government + "
             "clerk for all seven municipalities; the county prints no "
             "trustees. Pinned to the Clerk page because the yearbook filename "
             "carries its edition and the scraper discovers it here; note the "
             "link is RELATIVE and only resolves against the Revize CDN root, "
             "which the scraper tries first."},
    {"layer": "Board of Review commissioners (roster)",
     "app_file": "ccbr-roster.json",
     "source_url": "https://www.cookcountyboardofreview.com/",
     "note": "Scraped weekly from the Board's commissioner pages "
             "(ccbr_scraper.py); the menu-discovered pages move to new "
             "name-derived paths after elections, which the scraper follows."},
    {"layer": "U.S. House districts (IL)",
     "app_file": "congress-districts.json",
     "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0?f=json",
     "note": "TIGERweb Legislative layer 0 (STATE=17), pre-built by build_legislative_boundaries.py. Redrawn ~once a decade."},
    {"layer": "IL State Senate districts",
     "app_file": "il-senate-districts.json",
     "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/1?f=json",
     "note": "TIGERweb Legislative layer 1 (2024 Upper, STATE=17), pre-built. Redrawn ~once a decade."},
    {"layer": "IL State House districts",
     "app_file": "il-house-districts.json",
     "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/2?f=json",
     "note": "TIGERweb Legislative layer 2 (2024 Lower, STATE=17), pre-built. Redrawn ~once a decade."},
    {"layer": "Early-voting sites (Chicago Board of Elections)",
     "app_file": "early-voting-sites.json",
     "source_url": "https://chicagoelections.gov/voting/early-voting",
     "note": "Hand-transcribed per election (see WATCH.md row). The site 403s "
             "non-browser clients, so a reachability WARN here is expected, "
             "not drift — refresh the file when the Board posts the next "
             "election's list."},
]

# Live named services the app queries at runtime. These aren't year-versioned
# (they're views/endpoints kept current by the publisher), so the only useful
# check is reachability — a rename or retirement shows up here before users hit
# a broken card. WARN-only: the app already isolates a down source per-card.
ENDPOINTS = [
    # Suburban municipal ward boundaries — the non-Chicago entries of the
    # consolidated `ward` layer. No consolidated source exists, hence four.
    {"layer": "Suburban Cook municipal wards (21 municipalities, ward layer)",
     "url": "https://gis.cookcountyil.gov/traditional/rest/services/politicalBoundary/MapServer/22?f=json"},
    {"layer": "Evanston wards (ward layer; carries per-ward alderperson contact)",
     "url": "https://maps.cityofevanston.org/arcgis/rest/services/OpenData/ArcGISOpenData2Administrative/MapServer/0?f=json"},
    {"layer": "Will County municipal wards (Lockport/Wilmington/Crest Hill/Joliet, ward layer)",
     "url": "https://services.arcgis.com/fGsbyIOAuxHnF97m/arcgis/rest/services/Ward_Districts/FeatureServer?f=json"},
    {"layer": "Aurora wards (ward layer)",
     "url": "https://gis.aurora.il.us/arcgis/rest/services/Administrative_Boundaries/2022Wards/FeatureServer/0?f=json"},
    {"layer": "CPD Police District boundaries",
     "url": "https://services2.arcgis.com/t3tlzCPfmaQzSWAk/arcgis/rest/services/Police_District_Boundary_View/FeatureServer/0?f=json"},
    {"layer": "CPD Police District stations",
     "url": "https://services2.arcgis.com/t3tlzCPfmaQzSWAk/arcgis/rest/services/Police_District_Stations_View/FeatureServer/0?f=json"},
    {"layer": "CPD Police Beat boundaries",
     "url": "https://services2.arcgis.com/t3tlzCPfmaQzSWAk/arcgis/rest/services/Police_Beat_Boundary/FeatureServer/0?f=json"},
    {"layer": "CPS school sites",
     "url": "https://services2.arcgis.com/t3tlzCPfmaQzSWAk/arcgis/rest/services/Schools/FeatureServer/0?f=json"},
    {"layer": "USGS National Map structures — post offices (layer 38)",
     "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/38?f=json"},
    {"layer": "USGS National Map structures — fire stations (layer 51; replaced CFD 28km-gtjn)",
     "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/51?f=json"},
    {"layer": "USGS National Map structures — police stations (layer 53; replaced the CPD station list for the nearest-3 layer)",
     "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/53?f=json"},
    {"layer": "Census TIGERweb counties (statewide county layer)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer?f=json"},
    {"layer": "Census TIGERweb county subdivisions + places (township/municipality layers)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer?f=json"},
    {"layer": "Census TIGERweb school districts (unified/secondary/elementary layers)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer?f=json"},
    {"layer": "Census TIGERweb ZCTAs (statewide ZIP Code layer)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer?f=json"},
    {"layer": "Census TIGERweb areal hydrography (Lake Michigan marker test)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Hydro/MapServer?f=json"},
    {"layer": "Will County Board districts 2022 (current 11-district map + reps)",
     "url": "https://services.arcgis.com/fGsbyIOAuxHnF97m/arcgis/rest/services/County_Board_Districts_2022/FeatureServer/0?f=json"},
    {"layer": "Lake County Board districts (19 members + contact carried on the county GIS)",
     "url": "https://services3.arcgis.com/HESxeTbDliKKvec2/arcgis/rest/services/LakeCounty_PoliticalBoundaries/FeatureServer/0?f=json"},
    {"layer": "Kane County Board districts (24 members carried on the county GIS)",
     "url": "https://services1.arcgis.com/oRKmdBXD6EbdmVgJ/arcgis/rest/services/KaneCo_IL_County_Board/FeatureServer/1?f=json"},
    {"layer": "McHenry County Board districts (9, district-number-only on the county GIS)",
     "url": "https://services1.arcgis.com/6iYC5AXXYapRVNzl/arcgis/rest/services/McHenry_County_Board_Districts/FeatureServer/0?f=json"},
    {"layer": "Kendall County Board districts (2, the current line — the county's ArcGIS Enterprise)",
     "url": "https://maps.co.kendall.il.us/server/rest/services/Hosted/County_Board_2010/FeatureServer/0?f=json"},
    {"layer": "Suburban Cook voting precincts (1,430 — the Clerk's current fabric, precinctHistorical L0; "
              "same geometry as Socrata k7sw-w3b8 'Suburban Cook Election Precincts - Current')",
     "url": "https://gis.cookcountyil.gov/traditional/rest/services/precinctHistorical/MapServer/0?f=json"},
    {"layer": "Cook TIF districts (418 — the Clerk's un-yeared current tiling, clerkTaxDistricts L18; "
              "retired year editions archive in Tax_Increment_Finance_District_Boundaries)",
     "url": "https://gis.cookcountyil.gov/traditional/rest/services/clerkTaxDistricts/MapServer/18?f=json"},
    {"layer": "MWRD of Greater Chicago boundary (1 district — the Clerk's tax-agency polygon)",
     "url": "https://gis.cookcountyil.gov/traditional/rest/services/politicalBoundary/MapServer/21?f=json"},
    # DeKalb's five entries all come off ONE ArcGIS Online org, so a single
    # org-level outage would fail all five at once — which is exactly the signal
    # wanted. Layer ids are NOT 0-based on this org (Precincts is 1, the
    # property-tax services are 4/7/9); a wrong id returns an error envelope that
    # parses as an empty result, so each is pinned explicitly here too.
    {"layer": "DeKalb County Board districts (12 electing 2 members each; officeholders come from the weekly roster)",
     "url": "https://services7.arcgis.com/hEXJrPwm89CLXBYe/arcgis/rest/services/District_AreaEffective2022/FeatureServer/0?f=json"},
    {"layer": "DeKalb voting precincts (69, named by the county's own township codes)",
     "url": "https://services7.arcgis.com/hEXJrPwm89CLXBYe/arcgis/rest/services/Precincts/FeatureServer/1?f=json"},
    {"layer": "DeKalb fire protection districts (18, the Clerk's property-tax tiling)",
     "url": "https://services7.arcgis.com/hEXJrPwm89CLXBYe/arcgis/rest/services/PT_Fire_Districts/FeatureServer/4?f=json"},
    {"layer": "DeKalb library districts (13, the Clerk's property-tax tiling)",
     "url": "https://services7.arcgis.com/hEXJrPwm89CLXBYe/arcgis/rest/services/PT_Library_Districts/FeatureServer/7?f=json"},
    {"layer": "DeKalb park districts (6, the Clerk's property-tax tiling)",
     "url": "https://services7.arcgis.com/hEXJrPwm89CLXBYe/arcgis/rest/services/PT_Park_Districts/FeatureServer/9?f=json"},
    # Ogle has no live endpoint of its own — both halves of its card are derived
    # files (see PROVENANCE). This is the census layer its district geometry is
    # dissolved from, so an outage or a schema change there is what would break a
    # rebuild.
    {"layer": "Census TIGERweb 2020 voting districts (Ogle board-district dissolve)",
     "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/58?f=json"},
    # Lee's REST root is /leecogis — NOT /server or /arcgis, which is what an
    # earlier pass tried before recording the county as unreachable. It was found
    # the way LaSalle's, Winnebago's, Madison's and DeKalb's were: the portal's
    # FEATURED GROUP (a plain search returns zero items) holds a "Voting Districts
    # & Election Precincts" app whose web map names the root. The county DRAWS its
    # four board districts, so the recorded precinct-dissolve blocker was moot.
    {"layer": "Lee County Board districts (4, county GIS)",
     "url": "https://gis.leecountyil.gov/leecogis/rest/services/Election/County_Board_Districts/MapServer/3?f=json"},
    {"layer": "Lee County precincts (46) + fire districts (22)",
     "url": "https://gis.leecountyil.gov/leecogis/rest/services/Election/Election_Precincts/MapServer/1?f=json"},
    # Whiteside runs the Esri Elections solution. Its Electoral Districts layer
    # holds EVERY office in one table keyed by electedoffice; only the three
    # County Board rows are consumed, filtered in the loader so the overlay draws
    # three shapes rather than twenty-one.
    #
    # DO NOT USE the same org's MyElectedRepresentatives service for
    # officeholders: it carries the same board with DIFFERENT names, its
    # dataLastEditDate is 2019-01-08, and only 11 of its 27 names appear on the
    # county's current board page — where this layer matches 27/27. Two services,
    # seven years apart, no naming cue; the edit date is the only tell.
    # Rock Island — the first served county on the Mississippi. Both layers sit
    # on one hosted service, reached the usual way (county site -> parcel viewer
    # -> web map -> operationalLayers). The board layer declares a NAME column
    # and populates it on 0 of 19 districts, which is why a roster scrape exists.
    # Rock Island's TaxDistricts service — a Cook-shaped tax-agency tiling, one
    # layer per levying body. Three of its ten are fleet concepts: fire (2, 17
    # districts), library (5, 10 polygons of which 9 are named — the tenth is the
    # un-districted remainder and the loader drops it) and park (8, a single
    # Cordova district). Incorporated cities correctly sit in NO fire or library
    # district: they run their own departments on a city levy.
    {"layer": "Rock Island County fire + library + park districts (tax-agency tiling)",
     "url": ("https://services9.arcgis.com/6FnscPPlUa9DXXOk/arcgis/rest/services/"
             "TaxDistricts/FeatureServer?f=json")},
    # Moline (7 wards) and Silvis (4) publish their own layers on the county's
    # hosted org, both edited in 2022 — after the redraw. Whiteside's ward layer
    # covers six MORE municipalities and is deliberately unused: last edited
    # 2019-11-05, before the 2020 census (recorded as a gap).
    {"layer": "Moline + Silvis municipal wards",
     "url": ("https://services9.arcgis.com/6FnscPPlUa9DXXOk/arcgis/rest/services/"
             "MolineWards2020/FeatureServer?f=json")},
    {"layer": "Rock Island County Board districts (19) + precincts (120)",
     "url": ("https://services9.arcgis.com/6FnscPPlUa9DXXOk/arcgis/rest/services/"
             "Other_Layers/FeatureServer?f=json")},
    {"layer": "Whiteside County electoral districts + precincts + polling places",
     "url": ("https://services.arcgis.com/l0M0OC6J9QAHCiGx/arcgis/rest/services/"
             "ElectionGeography_public/FeatureServer?f=json")},
]

FAIL, WARN, OK = "FAIL", "WARN", "OK"


class Findings(object):
    """Collects (severity, layer, message) rows and tracks the worst seen."""

    def __init__(self):
        self.rows = []

    def add(self, severity, layer, message):
        self.rows.append((severity, layer, message))

    def status(self):
        if any(s == FAIL for s, _, _ in self.rows):
            return "fail"
        if any(s == WARN for s, _, _ in self.rows):
            return "warn"
        return "ok"


def http_get(url, want_json=True, params=None):
    """GET with a sane UA; returns (ok, payload_or_error). Never raises."""
    if requests is None:
        return False, "requests not installed"
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "DistrictExplorer-CHI source validator (+https://chidistricts.com)"},
        )
    except Exception as e:  # network/TLS/proxy errors are a finding, not a crash
        return False, "request failed: %s" % e
    if resp.status_code >= 400:
        return False, "HTTP %d" % resp.status_code
    if not want_json:
        return True, resp
    try:
        return True, resp.json()
    except ValueError as e:
        return False, "non-JSON response: %s" % e


# ---- check 1: the manifest still matches what index.html actually uses -------
def check_manifest_matches_app(html, findings):
    for d in SOCRATA:
        if d["id"] not in html:
            findings.add(FAIL, d["layer"],
                         "dataset id %s not found in index.html — manifest is "
                         "out of sync with the app (update scripts/validate_sources.py)"
                         % d["id"])
    for p in PROVENANCE:
        if ("data/app/" + p["app_file"]) not in html:
            findings.add(FAIL, p["layer"],
                         "index.html no longer references data/app/%s — manifest drift"
                         % p["app_file"])


# ---- check 2: Socrata datasets resolve, keep their name, aren't superseded ---
def newest_edition(cfg):
    """Search the portal catalog for the newest edition matching cfg.

    Returns (id, name, year_int) for the highest `pattern` capture, or None if
    the search is unavailable / finds nothing usable.
    """
    ys = cfg["year_search"]
    ok, payload = http_get(CATALOG_API, params={
        "domains": SOCRATA_DOMAIN,
        "q": ys["query"],
        "only": "dataset,map,geospatial",
        "limit": 200,
    })
    if not ok or not isinstance(payload, dict):
        return None
    rx = re.compile(ys["pattern"])
    best = None
    for r in payload.get("results", []):
        res = r.get("resource", {})
        name = res.get("name", "")
        if cfg["name_contains"] not in name:
            continue
        m = rx.search(name)
        if not m:
            continue
        year = int(m.group(1))
        if best is None or year > best[2]:
            best = (res.get("id"), name, year)
    return best


def check_socrata(findings, offline):
    for cfg in SOCRATA:
        layer = cfg["layer"]
        if offline:
            continue
        ok, meta = http_get("https://%s/api/views/%s.json" % (SOCRATA_DOMAIN, cfg["id"]))
        if not ok:
            findings.add(FAIL, layer,
                         "dataset %s does not resolve on the portal (%s) — likely "
                         "retired or replaced" % (cfg["id"], meta))
            continue
        name = meta.get("name", "") if isinstance(meta, dict) else ""
        if cfg["name_contains"] not in name:
            findings.add(FAIL, layer,
                         "dataset %s is now named %r — expected it to contain %r; "
                         "the id may have been repurposed"
                         % (cfg["id"], name, cfg["name_contains"]))
            continue

        if "year_search" not in cfg:
            findings.add(OK, layer, "%s — %r" % (cfg["id"], name))
            continue

        # year-versioned: is a newer edition published?
        cur = re.search(cfg["year_search"]["pattern"], name)
        cur_year = int(cur.group(1)) if cur else None
        newest = newest_edition(cfg)
        if newest is None or cur_year is None:
            findings.add(OK, layer,
                         "%s — %r (newer-edition search unavailable)" % (cfg["id"], name))
        elif newest[2] > cur_year and newest[0] != cfg["id"]:
            findings.add(WARN, layer,
                         "in use: %s (%r). NEWER edition on the portal: %s (%r). "
                         "Review the newer dataset's schema, then update the id in index.html."
                         % (cfg["id"], name, newest[0], newest[1]))
        else:
            findings.add(OK, layer, "%s — %r (newest edition)" % (cfg["id"], name))


# ---- check 3: shapefile provenance reachable, built file present ------------
def check_provenance(findings, offline):
    for p in PROVENANCE:
        layer = p["layer"]
        fpath = os.path.join(APP_DATA_DIR, p["app_file"])
        if not os.path.exists(fpath):
            findings.add(FAIL, layer, "built data file data/app/%s is missing" % p["app_file"])
        if offline:
            continue
        ok, res = http_get(p["source_url"], want_json=False)
        if ok:
            findings.add(OK, layer, "source reachable: %s — %s" % (p["source_url"], p["note"]))
        else:
            findings.add(WARN, layer,
                         "source not reachable (%s): %s. Boundaries change ~once a "
                         "decade; verify the source still exists and re-download if redrawn. %s"
                         % (res, p["source_url"], p["note"]))


# ---- check 4: live endpoints reachable --------------------------------------
def check_endpoints(findings, offline):
    if offline:
        return
    for e in ENDPOINTS:
        ok, res = http_get(e["url"], want_json=False)
        if ok:
            findings.add(OK, e["layer"], "endpoint reachable")
        else:
            findings.add(WARN, e["layer"],
                         "endpoint not reachable (%s): %s — the service may have been "
                         "renamed or retired" % (res, e["url"]))


# The `ward` layer is the one CountyDispatch whose entries are keyed by SOURCE
# rather than by county, so its disjointness is not guaranteed by geography the
# way county-keyed layers' is. registerCountyLayer dispatches by containment and
# takes the FIRST entry that matches, so an overlap would not error — it would
# quietly answer from whichever entry happens to be ordered first, and the two
# sources disagree about ward numbering. Verified disjoint 2026-07-28 (206
# features, every ordered pair); this watches for a publisher extending one of
# them into another's territory, which is the realistic way it breaks.
WARD_SOURCES = [
    # Chicago is the pair that matters most: its 50 wards are ALSO in the Cook
    # county layer, and index.html drops them there by normalized name. If that
    # filter ever breaks, this is the check that says so.
    {"key": "chicago",
     "url": "https://data.cityofchicago.org/resource/p293-wvbd.geojson",
     "socrata": True},
    {"key": "cook-suburban",
     "url": "https://gis.cookcountyil.gov/traditional/rest/services/politicalBoundary/"
            "MapServer/22/query",
     # Chicago's 50 wards sit in this county layer too and the chicago entry
     # serves them from the City's own dataset; index.html filters them out by
     # normalized name, so the check must filter identically or report a
     # self-inflicted overlap.
     "drop_municipality": "CHICAGO"},
    {"key": "evanston",
     "url": "https://maps.cityofevanston.org/arcgis/rest/services/OpenData/"
            "ArcGISOpenData2Administrative/MapServer/0/query"},
    {"key": "aurora",
     "url": "https://gis.aurora.il.us/arcgis/rest/services/Administrative_Boundaries/"
            "2022Wards/FeatureServer/0/query"},
    {"key": "will",
     "url": "https://services.arcgis.com/fGsbyIOAuxHnF97m/arcgis/rest/services/"
            "Ward_Districts/FeatureServer/%d/query",
     "sublayers": [0, 1, 2, 3]},
]


def _ward_rings(feature):
    geom = feature.get("geometry") or {}
    if geom.get("type") == "Polygon":
        return list(geom.get("coordinates") or [])
    if geom.get("type") == "MultiPolygon":
        return [r for poly in (geom.get("coordinates") or []) for r in poly]
    return []


def _ward_point_in(feature, pt):
    x, y = pt
    inside = False
    for ring in _ward_rings(feature):
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[i + 1][0], ring[i + 1][1]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def _ward_probe_point(feature):
    """Average of the largest ring — not guaranteed interior for a concave ward,
    but it only has to be a stable point that lands in the RIGHT municipality,
    and an overlap this misses is one the next feature catches."""
    rings = _ward_rings(feature)
    if not rings:
        return None
    ring = max(rings, key=len)
    return (sum(c[0] for c in ring) / len(ring), sum(c[1] for c in ring) / len(ring))


def check_ward_dispatch_disjoint(findings, offline):
    if offline:
        return
    layer = "City Ward (dispatch disjointness)"
    loaded = {}
    for src in WARD_SOURCES:
        feats = []
        for sub in src.get("sublayers", [None]):
            url = src["url"] % sub if sub is not None else src["url"]
            params = ({"$limit": "1000"} if src.get("socrata") else
                      {"where": "1=1", "outFields": "*", "outSR": "4326",
                       "f": "geojson", "resultRecordCount": "2000"})
            ok, res = http_get(url, params=params)
            if not ok:
                findings.add(WARN, layer,
                             "%s source unreachable (%s) — disjointness unverified this "
                             "run" % (src["key"], res))
                return
            feats.extend((res or {}).get("features") or [])
        drop = src.get("drop_municipality")
        if drop:
            feats = [f for f in feats
                     if (f.get("properties", {}).get("MUNICIPALITY") or "").strip().upper() != drop]
        loaded[src["key"]] = feats

    overlaps = []
    keys = sorted(loaded)
    for a in keys:
        for b in keys:
            if a == b:
                continue
            for f in loaded[a]:
                pt = _ward_probe_point(f)
                if pt and any(_ward_point_in(g, pt) for g in loaded[b]):
                    overlaps.append((a, b))
                    break
    if overlaps:
        findings.add(FAIL, layer,
                     "ward dispatch entries overlap (%s) — registerCountyLayer takes the "
                     "FIRST containing entry, so one source is silently answering for "
                     "territory the other also claims"
                     % ", ".join("%s into %s" % p for p in overlaps))
    else:
        findings.add(OK, layer,
                     "%d ward features across %d sources, every ordered pair disjoint"
                     % (sum(len(v) for v in loaded.values()), len(loaded)))


def render(findings):
    order = {FAIL: 0, WARN: 1, OK: 2}
    rows = sorted(findings.rows, key=lambda r: (order[r[0]], r[1]))
    n_fail = sum(1 for s, _, _ in rows if s == FAIL)
    n_warn = sum(1 for s, _, _ in rows if s == WARN)
    n_ok = sum(1 for s, _, _ in rows if s == OK)
    lines = []
    lines.append("# Layer source validation")
    lines.append("")
    lines.append("**%d FAIL · %d WARN · %d OK**" % (n_fail, n_warn, n_ok))
    lines.append("")
    if n_fail or n_warn:
        lines.append("Sources below need a human look. Nothing is auto-changed — "
                     "review, then update `index.html` (dataset ids) or re-download the "
                     "boundary shapefile as needed.")
        lines.append("")
    for sev in (FAIL, WARN, OK):
        group = [r for r in rows if r[0] == sev]
        if not group:
            continue
        lines.append("## %s (%d)" % (sev, len(group)))
        for _, layer, msg in group:
            lines.append("- **%s** — %s" % (layer, msg))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Validate the app's data-layer sources are current.")
    ap.add_argument("--report", metavar="PATH", help="write the markdown report to PATH (also printed to stdout)")
    ap.add_argument("--status-file", metavar="PATH", help="write ok|warn|fail to PATH (for CI)")
    ap.add_argument("--offline", action="store_true", help="run only the manifest↔index.html checks (no network)")
    args = ap.parse_args()

    if not os.path.exists(INDEX_HTML):
        print("validate_sources: FAIL — index.html not found at %s" % INDEX_HTML, file=sys.stderr)
        sys.exit(1)
    html = open(INDEX_HTML).read()

    if not args.offline and requests is None:
        print("validate_sources: requests not installed; run with --offline or "
              "`pip install -c scripts/requirements.txt requests`", file=sys.stderr)
        sys.exit(1)

    findings = Findings()
    check_manifest_matches_app(html, findings)
    check_socrata(findings, args.offline)
    check_provenance(findings, args.offline)
    check_endpoints(findings, args.offline)
    check_ward_dispatch_disjoint(findings, args.offline)

    report = render(findings)
    sys.stdout.write(report)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)

    status = findings.status()
    if args.status_file:
        with open(args.status_file, "w") as f:
            f.write(status)

    sys.exit(1 if status == "fail" else 0)


if __name__ == "__main__":
    main()

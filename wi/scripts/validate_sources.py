#!/usr/bin/env python3
"""
Source freshness gate for the app's data layers.

Why this exists: unlike the roster scrapers (which re-pull the same page every
week), several layers point at a *specific* upstream dataset that the publisher
silently supersedes with a new one:

  * Socrata portal datasets can be versioned by year. The reference fork's CPS
    attendance-boundary layers, for example, are published fresh every school
    year under a BRAND NEW dataset id (…SY2526 → …SY2627), so the id hardcoded
    in index.html keeps returning last year's boundaries long after a newer one
    exists. Nothing errors; the data just quietly goes stale.
  * Pre-built boundary layers (in this instance: the TIGERweb-derived district
    files and LTSB's supervisory districts, which are REPUBLISHED each 15
    January and 15 July) were downloaded at build time. The check there is
    provenance: is the source we cite still reachable, and a reminder to
    re-verify after each publication window.

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
  4. Live service endpoints (Census TIGERweb, USGS structures): reachable.  [WARN]

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

HTTP_TIMEOUT = 25

# The freshness gate's source manifest for the Wisconsin instance. Every layer
# this instance adds gets its rows
# here in the same change (CLAUDE.md's conventions; the reference repo's
# validate_sources.py shows a mature manifest's full shape, including
# year-search patterns and the `blocked` inversion).
SOCRATA_DOMAIN = "data.invalid"  # this fork's Socrata portal, if it adopts one
CATALOG_API = "https://api.us.socrata.com/api/catalog/v1"

# Socrata dataset ids the app hardcodes (none in the starter set).
SOCRATA = []

# Same-origin data/app files and the upstream source each was built from.
PROVENANCE = [
    {
        "layer": "us-house",
        "app_file": "congress-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0",
        "note": "Congressional districts pre-built from TIGERweb by bootstrap_state.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "us-house",
        "app_file": "congress-roster.json",
        "source_url": "https://unitedstates.github.io/congress-legislators/legislators-current.json",
        "note": "Delegation roster from the public-domain congress-legislators project; refreshed weekly by update-wi-congress-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "state-counties.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "County polygons pre-built from TIGERweb by bootstrap_state.py.",
    },
    {
        "layer": "school-district-unified",
        "app_file": "school-districts-unified.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0",
        "note": "Unified school districts pre-built from TIGERweb by bootstrap_state.py.",
    },
    {
        "layer": "wi-senate",
        "app_file": "wi-senate-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/1",
        "note": "State Senate districts pre-built from TIGERweb by wi/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "wi-senate",
        "app_file": "wi-senate-members.json",
        "source_url": "https://data.openstates.org/people/current/wi.csv",
        "note": "Senate roster base (name, party) from the Open States current-people export; refreshed weekly by update-wi-legislature-roster.yml.",
    },
    {
        "layer": "wi-senate",
        "app_file": "wi-senate-members.json",
        "source_url": "https://docs.legis.wisconsin.gov/2025/legislators/senate",
        "note": (
            "The Legislature's own senate index — the office/phone/fax/e-mail "
            "enrichment (wi_legislature_scraper.py). SESSION-SCOPED URL: the "
            "/2025/ biennium path must be bumped each odd-year January "
            "(WATCH.md row) — this row going dead is that bump coming due."
        ),
    },
    {
        "layer": "wi-assembly",
        "app_file": "wi-assembly-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/2",
        "note": "State Assembly districts pre-built from TIGERweb by wi/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "wi-assembly",
        "app_file": "wi-assembly-members.json",
        "source_url": "https://data.openstates.org/people/current/wi.csv",
        "note": "Assembly roster base (name, party) from the Open States current-people export; refreshed weekly by update-wi-legislature-roster.yml.",
    },
    {
        "layer": "wi-assembly",
        "app_file": "wi-assembly-members.json",
        "source_url": "https://docs.legis.wisconsin.gov/2025/legislators/assembly",
        "note": (
            "The Legislature's own assembly index — the office enrichment; "
            "same session-scoped-path caveat as the senate row."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-supervisory-districts.json",
        "source_url": "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_County_Supervisory_Districts_Current/FeatureServer/0",
        "note": (
            "Supervisory districts for all 72 counties, pre-built by "
            "wi/scripts/build_wi_supervisory_districts.py from LTSB's statewide aggregate of "
            "county filings under Wis. Stat. 5.15(4)(br)1. The layer is REPUBLISHED each 15 "
            "January and 15 July, so re-run the builder after a submission window: its own "
            "gates (feature count, 1..n numbering per county, ward reconciliation) are what "
            "catch a county whose filing changed or broke."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-supervisory-districts.json",
        "source_url": "https://services9.arcgis.com/cqHJZMbXoaOT0XrP/arcgis/rest/services/Trempealeau_County_County_Board_Supervisor_Districts_2021_2031_WFL1/FeatureServer/3",
        "note": (
            "Trempealeau County's own adopted plan, shipped in place of LTSB's file for that "
            "county alone (LTSB merges its districts 15 and 17; the county still elects "
            "seventeen). If this service ever stops answering, the builder fails rather than "
            "silently falling back to the merged geometry."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-board-directory.json",
        "source_url": "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Municipal_Wards_Current/FeatureServer/0",
        "note": (
            "The ward layer is BOTH the independent witness the district builder "
            "reconciles against (every ward names a district that exists, every "
            "district owns a ward) AND, since phase 2, the live source behind the "
            "shipped `ward` card (its own ENDPOINTS row below). Listed here so its "
            "disappearance fails the supervisory build's provenance too."
        ),
    },
    {
        "layer": "wi-circuit-court",
        "app_file": "wi-circuit-courts.json",
        "source_url": "https://www.wicourts.gov/courts/circuit/judges.htm",
        "note": (
            "The 69 circuits as county unions under a double witness — Wis. Stat. "
            "753.06 and this wicourts listing, which the weekly roster scrape "
            "re-asserts (its failure is the redistricting tripwire). Cite the "
            "statute by per-subsection URLs when re-verifying: the chapter page "
            "lazy-loads and one fetch truncates at 52 of 63 entries (measured). "
            "Rebuild with wi/scripts/build_wi_circuit_courts.py only if the "
            "county file or the statute moves."
        ),
    },
    {
        "layer": "wi-circuit-court",
        "app_file": "wi-circuit-judges.json",
        "source_url": "https://www.wicourts.gov/contact/Circuit_Courts.html",
        "note": (
            "The bench's enrichment source (branch, direct phone, courthouse), "
            "joined onto the judges table by wi_circuit_judges_scraper.py + "
            "build_wi_circuit_court_roster.py; refreshed weekly by "
            "update-wi-circuit-court-roster.yml."
        ),
    },
    {
        "layer": "wi-court-of-appeals",
        "app_file": "wi-court-of-appeals-districts.json",
        "source_url": "https://www.wicourts.gov/courts/appeals/index.htm",
        "note": (
            "The four appellate districts as county unions under a double witness "
            "— Wis. Stat. 752.11 (unchanged since 1977) and this appeals page, "
            "whose county lists the weekly roster scrape re-asserts. Rebuild with "
            "wi/scripts/build_wi_court_of_appeals.py only if either witness moves."
        ),
    },
    {
        "layer": "wi-court-of-appeals",
        "app_file": "wi-court-of-appeals-roster.json",
        "source_url": "https://www.wicourts.gov/contact/Court_of_Appeals.html",
        "note": (
            "The sixteen-judge bench (4/4/3/5, gated) with roles, phones and "
            "chambers — read from this page's CONTENT blocks, never the judges "
            "index's stale nav list; refreshed weekly by "
            "update-wi-court-of-appeals-roster.yml."
        ),
    },
    {
        "layer": "county",
        "app_file": "wi-county-clerks.json",
        "source_url": "https://docs.legis.wisconsin.gov/misc/lrb/blue_book/2025_2026/210_officials_and_employees.pdf",
        "note": (
            "The Blue Book county-officers excerpt the clerk roster's names and "
            "party-or-appointed codes come from. A NEW BIENNIAL EDITION is the "
            "drift to watch: the 2027-28 book will publish under a new path, and "
            "the scraper's URL follows it by hand (WATCH.md row)."
        ),
    },
    {
        "layer": "county",
        "app_file": "wi-county-clerks.json",
        "source_url": "https://wisconsincountyclerks.org/wisconsin-counties/",
        "note": (
            "The clerks' association's county index (72 per-county pages) — the "
            "roster's contact half and its currency witness; crawled weekly at "
            "the robots-declared 10-second delay by wi_county_clerk_scraper.py."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-board-members.json",
        "source_url": "https://services2.arcgis.com/s1wgJQKbKJihhhaT/arcgis/rest/services/Milwaukee_County_Supervisory_Districts/FeatureServer/46",
        "note": (
            "Milwaukee's 18 supervisors as attributes on the county's own LIO "
            "layer (Sup_Name/Email_Addr/Website_Url) — the blocked-site-is-not-"
            "a-blocked-county route; witnessed per run against the county's "
            "Legistar API (body 138), which is a witness, never a source."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-board-members.json",
        "source_url": "https://services1.arcgis.com/z1oAk3W6cWVD8swZ/arcgis/rest/services/County_Board_of_Supervisors_WFL1/FeatureServer/0",
        "note": (
            "Racine's 21 supervisors with e-mails on the county's own AGO org "
            "(REPNAME/Contact, edited post-April-2026) — same route as "
            "Milwaukee, no witness needed: the layer is the county's only "
            "machine-readable roster and its edit date is the currency fact."
        ),
    },
    {
        "layer": "county-board",
        "app_file": "county-board-members.json",
        "source_url": "https://www.browncountywi.gov/government/county-board-of-supervisors/",
        "note": (
            "The supervisor roster — 20 counties' own board pages plus two county GIS layers (rows above), scraped weekly by "
            "update-wi-county-board-roster.yml with each county's reading direction "
            "pinned (the full URL table is COUNTIES in wi_county_board_scraper.py). "
            "One representative page is probed here — Brown, the largest launch-set "
            "board at 26 seats — because the weekly scrape already fails loudly per "
            "county; this row exists so the FILE's disappearance is noticed and so "
            "the roster has a manifest row at all."
        ),
    },
    {
        "layer": "school-site",
        "app_file": "school-sites.json",
        "source_url": "https://services8.arcgis.com/o4NJgD3NfeHnWy06/arcgis/rest/services/Wisconsin_Public_Schools/FeatureServer/20",
        "note": (
            "Public school sites from DPI's own ArcGIS org (2,290 records, "
            "2,138 placed — the rest are placeless virtual programs), "
            "pre-built by wi/scripts/build_wi_school_sites.py. An OPERATOR "
            "rebuild after DPI's school-year rotation (WATCH.md); the builder "
            "pages past the service's 2,000-record cap and asserts the total."
        ),
    },
    {
        "layer": "school-site",
        "app_file": "school-sites.json",
        "source_url": "https://services8.arcgis.com/o4NJgD3NfeHnWy06/arcgis/rest/services/WI_Private_Schools/FeatureServer/2",
        "note": (
            "Private school sites (828) from the same DPI org — the same "
            "builder, which encodes the per-layer attribute renames "
            "(LATITUDE/LONGITUDE here against the public layer's LAT/LON)."
        ),
    },
    {
        "layer": "school-site",
        "app_file": "school-sites.json",
        "source_url": "https://www.arcgis.com/sharing/rest/content/items/d383fe81275e46f2a5a5c4f1a0c2eb85?f=json",
        "note": (
            "The DPI school directory's AGO catalog item — the successor "
            "watch: DPI rotates the directory around each school year, and "
            "this item dying or renaming is the signal a successor item "
            "shipped (the Socrata newer-edition pattern, AGO edition)."
        ),
    },
    {
        "layer": "library",
        "app_file": "library-sites.json",
        "source_url": "https://services8.arcgis.com/o4NJgD3NfeHnWy06/arcgis/rest/services/WI_Public_Libraries_and_Branches/FeatureServer/6",
        "note": (
            "Public library outlets (482, branches included) from DPI's AGO "
            "org, pre-built by wi/scripts/build_wi_libraries.py — whose bbox "
            "gate holds the line on the layer's measured trap: its LAT/LONG "
            "attributes are Web Mercator meters despite their names, so only "
            "the outSR=4326 geometry is ever read."
        ),
    },
    {
        "layer": "aldermanic-district",
        "app_file": "aldermanic-districts.json",
        "source_url": "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Municipal_Wards_Current/FeatureServer/0",
        "note": (
            "The dissolve source — the coded city/village wards of LTSB's "
            "statewide layer, dissolved on COUSUBFP+ALDERID by "
            "wi/scripts/build_wi_aldermanic_districts.py (an OPERATOR rebuild "
            "each Jan/Jul filing window, WATCH.md). Same endpoint the ward "
            "layer queries live; this row ties the pre-built file to it."
        ),
    },
    {
        "layer": "aldermanic-district",
        "app_file": "aldermanic-districts.json",
        "source_url": "https://mapservices.legis.wisconsin.gov/arcgis/rest/services/BAS_Collection/BAS_Live_Collection_Alderpersons/FeatureServer/0",
        "note": (
            "The composition WITNESS — the state's own pre-dissolved working "
            "set, a different filing edition that must agree key for key "
            "(867/867 at first build). Never the source: no stated terms and "
            "it mutates mid-collection."
        ),
    },
    {
        "layer": "aldermanic-district",
        "app_file": "wi-alderpersons.json",
        "source_url": "https://www.cityofmadison.com/council/council-members",
        "note": (
            "One representative roster page of the six the weekly scrape "
            "reads (wi_alderperson_scraper.py carries the full table) — the "
            "scrape already fails loudly per city; this row exists so the "
            "FILE has a manifest row and a dead index page is noticed."
        ),
    },
    {
        "layer": "aldermanic-district",
        "app_file": "wi-alderpersons.json",
        "source_url": "https://gis-city.kenosha.org/server/rest/services/Organizational_Layers/Districts_ElectedRepresentation/FeatureServer/150",
        "note": (
            "Kenosha's roster layer (REP_AREA='D' rows; each district appears "
            "twice, one row named and one N/A). Its currency is WITNESSED "
            "against the county's certified spring canvass, which caught the "
            "layer stale on one seat at first build — the item's modified "
            "date is the VIEW definition's, never the data's."
        ),
    },
    {
        "layer": "aldermanic-district",
        "app_file": "wi-alderpersons.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/election/alderman/MapServer/0",
        "note": (
            "Milwaukee's roster layer (ALDERPERSON attribute, 15/15). The "
            "host drops ~1 in 4-8 requests with TCP resets — the scraper "
            "retries and falls back to the same data's CKAN shapefile — and "
            "the roster is witnessed against the city's Legistar API "
            "(webapi.legistar.com/v1/milwaukee, body 1) every run."
        ),
    },
    {
        "layer": "mps-school-board",
        "app_file": "mps-school-board-districts.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/AGO/MPS_School_Districts/MapServer/1",
        "note": (
            "Milwaukee's own MPS board-district layer, server-reprojected and "
            "pre-built by wi/scripts/build_mps_school_board_districts.py (the "
            "same measured-flaky host as the alderman layer — build-time only, "
            "retried). Adopted 2022-02-25; redraws each census (WATCH.md)."
        ),
    },
    {
        "layer": "mps-school-board",
        "app_file": "mps-school-board-districts.json",
        "source_url": "https://data.milwaukee.gov/dataset/milwaukee-public-school-board-districts",
        "note": (
            "The same districts as the city's CKAN shapefile (CC-BY) — the "
            "build-time WITNESS: districts 1-8 and their area shares must "
            "agree between the two city surfaces before the file ships "
            "(0.04% max share difference at first build)."
        ),
    },
    {
        "layer": "mps-school-board",
        "app_file": "mps-school-board-members.json",
        "source_url": "https://www.milwaukeepublicschools.org/about/board/directors",
        "note": (
            "The district's own directors page — one heading per seat, the "
            "at-large president plus districts 1-8 — scraped weekly by "
            "update-mps-school-board-roster.yml and witnessed against the "
            "board index's committee lists (two separately maintained "
            "surfaces must name the same directors)."
        ),
    },
    {
        "layer": "mpd-district",
        "app_file": "mpd-districts.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/MPD/MPD_geography/MapServer/2",
        "note": (
            "The city's own MPD districts layer (field POLICE, districts 1-7), "
            "server-reprojected and pre-built by "
            "wi/scripts/build_milwaukee_city_layers.py — the same measured-"
            "flaky host as the MPS/alderman layers, build-time only, retried. "
            "District CAPTAINS live only behind city.milwaukee.gov's "
            "Cloudflare challenge, which is why the card names no one."
        ),
    },
    {
        "layer": "mpd-district",
        "app_file": "mpd-districts.json",
        "source_url": "https://data.milwaukee.gov/dataset/milwaukee-police-district",
        "note": (
            "The same districts as the city's CKAN shapefile (CC-BY) — the "
            "build-time WITNESS: districts 1-7 and their area shares must "
            "agree between the two city surfaces before the file ships "
            "(0.04% max share difference at first build)."
        ),
    },
    {
        "layer": "milwaukee-neighborhoods",
        "app_file": "milwaukee-neighborhoods.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/planning/special_districts/MapServer/4",
        "note": (
            "The city's own neighborhoods layer (field NEIGHBORHD, 190 "
            "polygons), server-reprojected and pre-built by "
            "wi/scripts/build_milwaukee_city_layers.py. Names publish "
            "ALL-CAPS and ship title-cased, the raw value kept on each "
            "feature as NAME_RAW."
        ),
    },
    {
        "layer": "mpd-squad-area",
        "app_file": "mpd-squad-areas.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/MPD/MPD_geography/MapServer/1",
        "note": (
            "The city's own MPD squad-area layer (field SQUADAREA, 25 "
            "squads — the beat analog), server-reprojected and pre-built by "
            "wi/scripts/build_milwaukee_city_layers.py. A squad's number "
            "encodes its district (hundreds digit), which the builder "
            "sample-verifies against the shipped district file."
        ),
    },
    {
        "layer": "mpd-squad-area",
        "app_file": "mpd-squad-areas.json",
        "source_url": "https://data.milwaukee.gov/dataset/milwaukee-police-department-squad-areas",
        "note": (
            "The same squad areas as the city's CKAN shapefile (CC-BY) — "
            "the build-time WITNESS: all 25 keys and their area shares must "
            "agree between the two city surfaces before the file ships "
            "(0.02% max share difference at first build)."
        ),
    },
    {
        "layer": "milwaukee-neighborhoods",
        "app_file": "milwaukee-neighborhoods.json",
        "source_url": "https://data.milwaukee.gov/dataset/neighborhoods",
        "note": (
            "The same neighborhoods as the city's CKAN shapefile (CC-BY) — "
            "the build-time WITNESS on a space-insensitive key fold, because "
            "the city's two surfaces spell one neighborhood apart (service "
            "MCGOVERN PARK, shapefile MC GOVERN PARK — the service spelling "
            "ships; 0.007% max share difference at first build)."
        ),
    },
    {
        "layer": "county",
        "app_file": "wi-county-officers.json",
        "source_url": "https://docs.legis.wisconsin.gov/misc/lrb/blue_book/2025_2026/210_officials_and_employees.pdf",
        "note": (
            "The Blue Book's OTHER county-officer tables (phase 4): chair, "
            "executive/administrator (CE/CA/AC/CM typed), treasurer, clerk of "
            "circuit court, register of deeds, DA, sheriff, coroner/ME — "
            "layout-aware x-position parse, chair-seats witness against the "
            "shipped supervisory geometry (Menominee's 7-vs-5 pinned), the "
            "shared Menominee/Shawano DA footnote encoded. Shipped DATED "
            "(April 2025): no second publisher for these offices measures "
            "open. The 2027-28 edition moves this URL — the biennium row in "
            "WATCH.md."
        ),
    },
    {
        "layer": "tid-district",
        "app_file": "tid-districts.json",
        "source_url": "https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/planning/special_districts/MapServer/8",
        "note": (
            "The city's own Tax Incremental Districts layer (79 active; "
            "field TID + NAME + create date), server-reprojected and "
            "pre-built by wi/scripts/build_milwaukee_city_layers.py — "
            "dissolved TIDs drop by date. TIDs are created and closed by "
            "Common Council action, so the count here moves; a change is "
            "the operator's rebuild trigger."
        ),
    },
    {
        "layer": "tid-district",
        "app_file": "tid-districts.json",
        "source_url": "https://data.milwaukee.gov/dataset/tax-incremental-districts-tid",
        "note": (
            "The same districts as the city's CKAN shapefile (CC-BY) — the "
            "build-time WITNESS, scoped to the city's own STATUS flag "
            "because the shapefile keeps all 56 retired TIDs the live "
            "layer omits (0.007% max share difference at first build)."
        ),
    },
    {
        "layer": "fire-service",
        "app_file": "fire-service-areas.json",
        "source_url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/3",
        "note": (
            "The OEC's statewide NG911 FireBoundary aggregate (updated "
            "roughly weekly; licence \"free and open for use by the "
            "public\"), dissolved per agency on the DsplayName+Agency_ID "
            "pair by wi/scripts/build_wi_ng911_service_areas.py — 3,009 "
            "effective polygons to 1,046 department areas at first build, "
            "expired rows dropped by date, filing absences pinned (gap "
            "ng911-fire-filings)."
        ),
    },
    {
        "layer": "law-service",
        "app_file": "law-service-areas.json",
        "source_url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/4",
        "note": (
            "The same service's LawEnforcementBoundary layer, same builder "
            "and gates — 3,083 effective polygons to 639 agency areas at "
            "first build. Plain -dissolve, never -dissolve2, so the "
            "concurrent sheriff/PD overlaps the counties filed survive; "
            "absences are gap ng911-law-filings."
        ),
    },
    {
        "layer": "psap-area",
        "app_file": "psap-areas.json",
        "source_url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/6",
        "note": (
            "The same service's PSAPBoundary layer, same builder and gates — "
            "205 effective polygons to 95 answering points at first build. "
            "The tiling with FUTURE-dated Expire rows (11 kept), which is "
            "why the builder drops expired rows by date, never by presence; "
            "absences are gap ng911-psap-filings."
        ),
    },
    {
        "layer": "ems-service",
        "app_file": "ems-service-areas.json",
        "source_url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/2",
        "note": (
            "The same service's EmergencyMedicalServicesBoundary layer, same "
            "builder and gates — 2,443 effective polygons to 579 services at "
            "first build. Regional ambulance providers re-prove the "
            "DsplayName+Agency_ID pair key (some EMS Agency_IDs are not "
            "county domains); absences are gap ng911-ems-filings."
        ),
    },
]

# Live endpoints the app queries at runtime.
ENDPOINTS = [
    {
        "layer": "county-subdivision",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/1/query?where=STATE%3D%2755%27&returnCountOnly=true&f=json",
    },
    {
        # Nearest-3 station layers, live by the state envelope (WI plus the
        # border-state stations a reader near the line genuinely wants).
        "layer": "police-station",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/53/query?geometry=-92.94,42.44,-86.19,47.36&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        "layer": "fire-station",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/51/query?geometry=-92.94,42.44,-86.19,47.36&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        # The NG911 pair is PRE-BUILT, but the OEC refreshes the service
        # roughly weekly and a count change here is the operator's rebuild
        # trigger (WATCH.md); the service going dark is the failure. The
        # counts move a little week to week — expected news, not drift.
        "layer": "fire-service",
        "url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/3/query?where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        "layer": "law-service",
        "url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/4/query?where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        "layer": "psap-area",
        "url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/6/query?where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        "layer": "ems-service",
        "url": "https://services3.arcgis.com/GoOAGCoqFEhZEh7f/arcgis/rest/services/WI_NG911_GIS_Service_Polygons_and_Road_Centerline_Data_v2/FeatureServer/2/query?where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        # The ward layer queries this live (point-first + paged overlay). The
        # count moves with each Jan/July filing window (7,138 Jan 2026 -> 7,161
        # July 2026) — a change is expected news; the layer going unreachable
        # or answering zero is the drift this row exists to catch.
        "layer": "ward",
        "url": "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Municipal_Wards_Current/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json",
    },
    {
        "layer": "municipality",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query?where=STATE%3D%2755%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "school-district-secondary",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/1/query?where=STATE%3D%2755%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "school-district-elementary",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/2/query?where=STATE%3D%2755%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "zip-code",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/11?f=json",
    },
    {
        "layer": "post-office",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/38?f=json",
    },
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
            headers={"User-Agent": "District Explorer source validator (+https://districtry.com/wi/)"},
        )
    except Exception as e:  # network/TLS/proxy errors are a finding, not a crash
        return False, "request failed: %s" % e
    if resp.status_code >= 400:
        return False, "HTTP %d" % resp.status_code
    # 202 is never a real document. "Accepted" means the request was taken for
    # later processing, and the bot-management fronts in front of several county
    # sites use it for their interstitial — dekalbcounty.org started doing so
    # around 2026-07-31, which failed the DeKalb board scraper outright while
    # this validator went on reporting the source reachable, because 202 < 400.
    # (The Will County Clerk entry has documented the same "202/empty to
    # non-browser user agents" behaviour for longer.) Treat it as unreachable
    # and say why, so the two signals agree.
    if resp.status_code == 202:
        return False, "HTTP 202 — bot-management interstitial, not the document"
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
        blocked = p.get("blocked")
        if ok and blocked:
            # The block LIFTING is the news. Every one of these entries was
            # measured unreachable and says so in its own note, so a monthly
            # WARN on them was pure noise — seven of the eight WARNs in the
            # 2026-08-01 run were this, and the tracking issue reopened every
            # month with nothing to act on. Reachable-again is the state a
            # human should hear about, because it means automation can resume.
            findings.add(WARN, layer,
                         "source is REACHABLE again (%s) — its recorded block appears to "
                         "have LIFTED. Re-test the scraper; if it works, drop the "
                         "`blocked` flag on this entry so a future outage warns again. "
                         "Recorded block: %s" % (p["source_url"], blocked))
        elif ok:
            findings.add(OK, layer, "source reachable: %s — %s" % (p["source_url"], p["note"]))
        elif blocked:
            findings.add(OK, layer,
                         "unreachable AS EXPECTED (%s) — %s. %s"
                         % (res, blocked, p["source_url"]))
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


# Municipal ward boundary sources (none shipped yet; grown when this instance
# ships its ward layer — docs/WI_PHASE2_PLAN.md PR 1).
WARD_SOURCES = []


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
        urls = src.get("urls") or [src["url"] % sub if sub is not None else src["url"]
                                   for sub in src.get("sublayers", [None])]
        for url in urls:
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

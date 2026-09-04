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
    files) were downloaded at build time. The check there is provenance: is
    the source we cite still reachable, and a reminder to re-verify after
    each redistricting cycle.

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
  4. Live service endpoints (Census TIGERweb): reachable.                  [WARN]

Exit status: 0 when nothing needs a human (OK or WARN only), 1 on any FAIL.
Newer-edition detection is deliberately WARN, not FAIL — the current dataset
still works and a person decides whether/when to migrate. The scheduled
workflow (.github/workflows/ia-validate-sources.yml) opens an issue on WARN or
FAIL so drift is never silent, without turning the build red.

Usage:
    python3 ia/scripts/validate_sources.py                 # human-readable report
    python3 ia/scripts/validate_sources.py --report r.md   # also write markdown
    python3 ia/scripts/validate_sources.py --status-file s.txt   # ok|warn|fail
    python3 ia/scripts/validate_sources.py --offline       # manifest↔app checks only
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

# The freshness gate's source manifest for the Iowa instance. Every layer this
# instance adds gets its rows here in the same change (CLAUDE.md's
# conventions; the reference repo's validate_sources.py shows a mature
# manifest's full shape, including year-search patterns and the `blocked`
# inversion).
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
        "note": "Congressional districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md). Built against TIGERweb's 120th-Congress layer (field CD120, Jan 1 2026 vintage); the retired CD119 field is gone and a query naming it returns an HTTP-200 JSON error envelope with no features key, so a rebuild on the old name fails as no-features.",
    },
    {
        "layer": "us-house",
        "app_file": "congress-roster.json",
        "source_url": "https://unitedstates.github.io/congress-legislators/legislators-current.json",
        "note": "Delegation roster from the public-domain congress-legislators project; refreshed weekly by update-ia-congress-roster.yml.",
    },
    {
        "layer": "ia-judicial-district",
        "app_file": "ia-judicial-districts.json",
        "source_url": "https://www.iowacourts.gov/iowa-courts/district-court/",
        "note": (
            "8 judicial election districts, whole-county unions per Iowa Code "
            "SS602.6107/602.6109 (Code 2003) -- the county-to-district crosswalk "
            "is cross-verified against iowacourts.gov's own per-district county "
            "page and Ballotpedia, then dissolved from state-counties.json by "
            "ia/scripts/build_ia_judicial_district.py."
        ),
    },
    {
        "layer": "ia-judicial-district",
        "app_file": "ia-judicial-districts.json",
        "source_url": (
            "https://services2.arcgis.com/KhKjlwEBlPJd6v51/arcgis/rest/services/"
            "JudicialDistricts/FeatureServer/0"
        ),
        "note": (
            "LSAFiscal's own published district polygons -- the spatial double "
            "witness the builder checks the crosswalk against at build time, "
            "never the geometry source itself (this layer draws no new "
            "boundary; it dissolves whole counties)."
        ),
    },
    {
        "layer": "ia-judicial-district",
        "app_file": "ia-judicial-judges.json",
        "source_url": "https://www.iowacourts.gov/iowa-courts/district-court/judicial-district-1/judges-and-magistrates-district-1/",
        "note": (
            "371 judges across all 8 districts (measured 2026-08-28), from each "
            "district's own \"Judges and Magistrates\" page -- three different "
            "URL shapes, one per district (see "
            "ia_judicial_district_scraper.py). Judges are RETENTION, never "
            "elected; no phone/e-mail/address is published for any judge."
        ),
    },
    {
        "layer": "community-college",
        "app_file": "ia-community-colleges.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CC_2026update/FeatureServer/0",
        "note": (
            "15 community college merged areas, shipped as published (no "
            "dissolve) -- the 2026-07-02 vintage, which fixes a confirmed "
            "coding error the older CommColleges2020 layer carries for "
            "Southeastern Community College. Pre-built by "
            "ia/scripts/build_ia_community_colleges.py, witnessed against a "
            "second LSA layer on name set, 2020 census population (Iowa's "
            "exact 3,190,369) and director-district count (124)."
        ),
    },
    {
        "layer": "community-college",
        "app_file": "ia-community-colleges.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CommColleges2020/FeatureServer/1",
        "note": (
            "The second LSA layer used as the build-time witness (name set, "
            "population, director-district count) -- never the geometry "
            "source itself."
        ),
    },
    {
        "layer": "county",
        "app_file": "state-counties.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "County polygons pre-built from TIGERweb by ia/scripts/build_state_counties.py.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-auditors.json",
        "source_url": "https://iowaauditors.org/find/directory/",
        "note": "All 99 county auditors (Iowa Code 47.2), from the auditors' own association directory. Built by ia/scripts/ia_county_auditor_scraper.py + build_ia_county_auditors.py; refreshed weekly by update-ia-county-auditor-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-auditors.json",
        "source_url": "https://sos.iowa.gov/auditors/",
        "note": "The Secretary of State's own auditors page — the second witness on every auditor's name and party, and the ONLY published source of an auditor e-mail (Cloudflare data-cfemail, decoded at scrape time). Read by the same ia/scripts/ia_county_auditor_scraper.py.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://member-portal.iowacounties.org/countydirectory/directory/Story",
        "note": "ISAC's member portal, one page per county — the ONLY statewide source for the county treasurer and for the board of supervisors. Probed here at a single county (Story) because the portal has no index page; a bad county name answers HTTP 200 with an empty table, so the scraper gates on parsed row count and never on status. Built by ia/scripts/ia_county_officers_scraper.py + build_ia_county_officers.py; refreshed weekly by update-ia-county-officers-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://iowalandrecords.org/recorder-directory/",
        "note": "All 99 county recorders with a plain mailto: and office phone — the highest-quality county officer source found in Iowa, and the recorder row's authority over the ISAC portal.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://www.issda.org/assets/Gold-Star/2025%20Sheriff%20Directory.pdf",
        "note": "The Iowa State Sheriffs' & Deputies' Association directory (PDF, 4 April 2025) — the sheriff row's authority. A DATED DOCUMENT, so it is the half of the pair that goes stale: Sac County's own site names a sheriff this PDF has not caught up with, pinned in the builder's DIVERGENCE_RESOLVED. A newer edition appearing at a different path is the thing to watch for.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://iowa-icaa.com/Roster/%40RosterOfCA%26ACAs.pdf",
        "note": "The Iowa County Attorneys Association roster (PDF, 5 May 2026) — the county attorney row's authority. Note the literal @ and & in the filename. iowa-icaa.com answers 404 with a FULL page body, so a reachability check on any other path there proves nothing.",
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-members.json",
        "source_url": "https://www.polkcountyiowa.gov/board-of-supervisors/",
        "note": "Which supervisor holds each district, for PLAN 3 counties only (Iowa Code 331.206 — plan 1 has no districts and plan 2 elects countywide). There is no statewide source: the Legislature's own layer names DISTRICTS not people, the ISAC portal attaches a district to nobody, the Secretary of State's statewide canvass carries ZERO supervisor contests (counties canvass their own county offices), and electionresults.iowa.gov exposes no data API. So each county's own board page supplies the district NUMBER by proximity to names the shipped roster already carries. Probed here at one representative county (Polk); the run reads 40 and keys the ones that pass its gates. Built by ia/scripts/ia_supervisor_district_scraper.py + build_ia_supervisor_roster.py; refreshed weekly by update-ia-supervisor-roster.yml.",
    },
    {
        "layer": "dsm-ward",
        "app_file": "dsm-wards.json",
        "source_url": "https://services.arcgis.com/HT7H9QGiZQoRJDpJ/arcgis/rest/services/Wards_view/FeatureServer/0",
        "note": "The City of Des Moines's own four council wards, pre-built by ia/scripts/build_dsm_wards.py. THE ITEM'S licenseInfo OPENS \"All rights reserved\" AND IS NOT A REFUSAL: the city's own Terms and Conditions of Use (data.dsm.city/pages/terms) permit applications using portal data on condition they carry that exact disclaimer, so the string is the required NOTICE, and the app ships it verbatim on the card. The same terms carry a Right to Discontinue Feeds clause, which is the reason this row exists — a city may withdraw the service, and the shipped file would then be the only copy.",
    },
    {
        "layer": "dsm-ward",
        "app_file": "dsm-council-members.json",
        "source_url": "https://www.dsm.city/government/city_council/index.php",
        "note": "All seven seats Des Moines elects (Iowa Code 372.4(1)(b): a mayor, two at-large members, one from each of four wards). The page renders Appointed Staff and Department Directors in IDENTICAL card markup to the elected members, so the scrape is scoped by <h2> heading and refuses if a name appears under both; the four ward members are cross-witnessed against the Wards layer's own in-band names and e-mails. Built by ia/scripts/dsm_council_scraper.py + build_dsm_council.py; refreshed weekly by update-ia-dsm-council-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://www.iowatreasurers.org/index.php?module=treashome&idCounty=1",
        "note": "The Iowa county treasurers' own state site, ONE OF TWO sources for the treasurer's e-mail address -- the office no statewide directory carries one for (the ISAC portal has no e-mail column at all: re-checked 2026-08-29, zero mailto and zero @ on a county page). ITS PER-COUNTY PAGES SERVE THE WRONG COUNTY, WITH NO ERROR AND NO 404, AND THAT IS WHY NOTHING IS KEYED ON idCounty ALONE. Swept all 99 ids 2026-08-29: eight serve another county's page outright (Buchanan/Johnson/Linn/Montgomery/Poweshiek get Clarke; Floyd/Iowa/Polk get byte-identical Jefferson pages), and three more serve the right page carrying Jefferson's address anyway (Dallas, Kossuth, Muscatine) -- so the page-level county check is necessary and NOT sufficient, and the address's DOMAIN must also fit the county. Probed here at idCounty=1 (Adair) as a reachability check only.",
    },
    {
        "layer": "county",
        "app_file": "ia-county-officers.json",
        "source_url": "https://www.adaircounty.iowa.gov/",
        "note": "A representative COUNTY OWN SITE (Adair), the other source for treasurer and sheriff e-mail addresses. An address ships only if the officeholder's own name is in its local part (witnessed) or its form is the office's mailbox -- a page window is NOT a witness, and the first version of that probe returned a DEPUTY's personal address in four of the first seven counties tried (Appanoose, Boone, Bremer, Buchanan). Built by ia/scripts/ia_county_officer_email_scraper.py, refreshed weekly by update-ia-county-officers-roster.yml; 65 of 99 treasurers and 87 of 98 sheriffs carry an address as of 2026-08-29.",
    },
    {
        "layer": "county",
        "app_file": "metro-outline.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "The whole-state outline for the coverage wash, pre-built by ia/scripts/build_metro_outline.py — dissolved from all 99 counties' geometry on the same layer as state-counties.json, not fetched as a separate state polygon (so a future partial-coverage narrowing needs only a smaller METRO_COUNTY_FIPS, the Wisconsin precedent).",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/1",
        "note": "State Senate districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-members.json",
        "source_url": "https://data.openstates.org/people/current/ia.csv",
        "note": "Senate roster base (name, party) from the Open States current-people export; refreshed weekly by update-ia-legislature-roster.yml.",
    },
    {
        "layer": "ia-senate",
        "app_file": "ia-senate-members.json",
        "source_url": "https://www.legis.iowa.gov/legislators/senate",
        "note": (
            "The Legislature's own senate directory — personIDs feed "
            "ia_legislature_scraper.py's per-legislator profile-page reads "
            "(Capitol phone/e-mail, and the Capitol's own address where "
            "published). Unlike Wisconsin's single listing page, Iowa's "
            "office/phone/email data lives on each member's own profile page, "
            "not this index — see WATCH.md's open question on whether those "
            "profile-page URLs are session-scoped."
        ),
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/2",
        "note": "State House districts pre-built from TIGERweb by ia/scripts/build_legislative_boundaries.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-members.json",
        "source_url": "https://data.openstates.org/people/current/ia.csv",
        "note": "House roster base (name, party) from the Open States current-people export; refreshed weekly by update-ia-legislature-roster.yml.",
    },
    {
        "layer": "ia-house",
        "app_file": "ia-house-members.json",
        "source_url": "https://www.legis.iowa.gov/legislators/house",
        "note": (
            "The Legislature's own house directory — same personID-driven "
            "profile-page enrichment route as the senate row above."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CountySupervisorDistricts/FeatureServer/0",
        "note": (
            "The Iowa Legislature's own ArcGIS organization — county supervisor "
            "districts for 95 of 99 counties (the other 3 SF-75-transitioning "
            "counties and Jones's absence are handled separately below); "
            "vintage 2024-01-30 (WATCH.md tracks whether it moves)."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://services5.arcgis.com/ya62ECiavqTkK0wv/arcgis/rest/services/BlackHawkCoSupervisor_LSAplan1/FeatureServer/0",
        "note": (
            "Black Hawk County's own hosted GIS — its adopted Senate File 75 "
            "plan (5 districts), shipped in place of the state layer's stale "
            "pre-SF75 at-large row for this county alone."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://www.storycountyiowa.gov/1172/Jurisdictional-Maps",
        "note": (
            "Story County's own site — states its SOS-approved Senate File 75 "
            "plan's facts; no GIS service found, so the county ships as one "
            "county-level TRANSITIONING feature pending real district geometry."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-supervisor-districts.json",
        "source_url": "https://johnsoncountyiowa.gov/supervisor-districts",
        "note": (
            "Johnson County's own site — states its SOS-approved Senate File "
            "75 plan's facts; no GIS service found, so the county ships as "
            "one county-level TRANSITIONING feature pending real district "
            "geometry."
        ),
    },
    {
        "layer": "county-supervisor",
        "app_file": "ia-county-board-directory.json",
        "source_url": "https://www.iowacounties.org/member-resources/county-directory/",
        "note": (
            "Iowa State Association of Counties' member directory — one "
            "detail page per county naming its own official website, read by "
            "ia_county_directory_scraper.py; not a roster of supervisors, "
            "since Iowa publishes no statewide one."
        ),
    },
    {
        "layer": "school-director-district",
        "app_file": "ia-school-director-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/IowaSchoolDirectorDistricts/FeatureServer/0",
        "note": "716 school board director districts inside the 324 shipped school districts, from the Iowa Legislature's own ArcGIS org. LICENCE CC0 — carried on the ITEM (5d6e55f885c54dd282eb17daaca20740), NOT on the service, whose own licenseInfo is null and whose copyrightText is empty; query arcgis.com/sharing/rest/search for the service name before concluding an ArcGIS layer states no terms. 728 features are published: 10 are exact duplicates (Davis County and East Buchanan each publish every row twice) and 2 name districts stale in this layer. At-large boards are read from the publisher's own AT-LARGE label in DIST_NAME. Built by ia/scripts/build_ia_school_director_districts.py; operator-rebuilt, no weekly workflow (this is geometry, not a roster).",
    },
    {
        "layer": "cc-director-district",
        "app_file": "ia-cc-director-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CC_DD2023/FeatureServer/0",
        "note": "123 community college director districts (Iowa Code 260C.11) inside the 15 merged areas, effective 2023-08-01. THE SERVICE'S NAME IS NOT ITS SLUG: the URL says CC_DD2023, the service calls itself CC_DirectorDistricts_FINAL, and an ArcGIS item search on the slug returns unrelated global items — search the NAME (item b89cf40cef40497e80ae8eb0a6e6d22f, owner education_iowa). Its licence is EMPTY, i.e. terms UNSTATED, which is NOT the CC0 the school-director layer's item carries; the two were checked the same way and differ. Joined to the parent on the numeric key with one asserted Southeastern 8->16 remap. Registered BESPOKE rather than through the polygon factory: the children encode the 2023 merged-area plan and the parent layer the 2026 update, so in ~0.2% of ground the two name different colleges and the card must resolve both and decline rather than contradict its own parent. Built by ia/scripts/build_ia_cc_director_districts.py; operator-rebuilt, no weekly workflow (geometry, not a roster).",
    },
    {
        "layer": "iowa-aea",
        "app_file": "ia-aeas.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CurrentIowaSchoolDistricts/FeatureServer/0",
        "note": (
            "Iowa's nine Area Education Agencies (Iowa Code ch. 273). THE SOURCE URL "
            "HERE IS THE SCHOOL-DISTRICT LAYER ON PURPOSE, and that is the whole build: "
            "the Department of Education DOES publish an AEA polygon, and it is stamped "
            "'for the 2019-2020 school year - updated 3/9/2020', so it supplies the "
            "build's WITNESS and never its geometry. What draws the line is the "
            "Department's own CURRENT district layer, which carries AEA_NUM in band on "
            "all 324 districts; ia/scripts/build_ia_aea.py dissolves the districts this "
            "app already ships by that attribute, joined on DistrictNCESCode = Census "
            "GEOID (324/324, both directions, no alias table). TWO NAMING TRAPS, THE SAME "
            "ONE TWICE: the AEA item is titled IowaAEAs and its layer calls itself "
            "IdoeAeaFY20, and this district service calls itself IdoeSD -- pin the URL "
            "and the item id (AEA witness: 1cfa541b8ebe4bdcbc2f52cdd0977a2b; a second "
            "copy of the same FY20 layer sits on a University of Northern Iowa personal "
            "account). Each agency's name, phone and website come from the AEA system's "
            "own Find My AEA directory, keyed on the same two-digit code the geometry "
            "carries. Identity-only: Iowa Code 273.8 gives a voter no say in any of the "
            "nine directors. Operator-rebuilt, no weekly workflow (geometry, not a "
            "roster) -- but re-run it whenever ia-school-districts.json is rebuilt, "
            "because the two are joined."
        ),
    },
    {
        "layer": "school-site",
        "app_file": "ia-school-sites.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/IowaSchoolBldgs/FeatureServer/0",
        "note": (
            "1,321 public school buildings, pre-built by "
            "ia/scripts/build_ia_school_sites.py from the Iowa Legislature's "
            "own ArcGIS org (paginated past the layer's 1,000-record cap; "
            "pin the slug IowaSchoolBldgs, never its internal title "
            "PublicSchoolBldgs, which names a different, stale service)."
        ),
    },
    {
        "layer": "school-district-unified",
        "app_file": "ia-school-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0",
        "note": (
            "324 unified school districts (325 TIGERweb features, one "
            "dissolved into a neighbor — WATCH.md tracks the reconciliation) "
            "pre-built by ia/scripts/build_ia_school_districts.py."
        ),
    },
    {
        "layer": "school-district-unified",
        "app_file": "ia-school-districts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CurrentIowaSchoolDistricts/FeatureServer/0",
        "note": (
            "Iowa Dept. of Education's own current district layer — the "
            "name-set witness the builder checks its dissolve against, never "
            "the geometry source."
        ),
    },
    {
        "layer": "precinct",
        "app_file": "ia-precincts.json",
        "source_url": "https://services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/Iowa_Precincts/FeatureServer/0",
        "note": (
            "1,660 election precincts across all 99 counties, pre-built by "
            "ia/scripts/build_ia_precincts.py from the Iowa Legislature's "
            "own ArcGIS org (item d394edea208c4003ac1d6bd1ec78532f, pinned "
            "by URL rather than name — two decoy services with confusingly "
            "similar names live on the same and a sibling org). "
            "Visvalingam-simplified with a 2,000-point agreement gate; "
            "polling-place fields are never fetched."
        ),
    },
]

# Live endpoints the app queries at runtime.
ENDPOINTS = [
    {
        "layer": "county-subdivision",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/1/query?where=STATE%3D%2719%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "municipality",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query?where=STATE%3D%2719%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "zip-code",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/11?f=json",
    },
    {
        "layer": "post-office",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/38?f=json",
    },
    {
        "layer": "police-station",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/53?f=json",
    },
    {
        "layer": "fire-station",
        "url": "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/51?f=json",
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
            headers={"User-Agent": "District Explorer source validator (+https://districtry.com/ia/)"},
        )
    except Exception as e:  # network/TLS/proxy errors are a finding, not a crash
        return False, "request failed: %s" % e
    if resp.status_code >= 400:
        return False, "HTTP %d" % resp.status_code
    # 202 is never a real document. "Accepted" means the request was taken for
    # later processing, and the bot-management fronts in front of several
    # government sites use it for their interstitial. Treat it as unreachable
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
                         "out of sync with the app (update ia/scripts/validate_sources.py)"
                         % d["id"])
    for p in PROVENANCE:
        # A file the app addresses by a slug built at RUNTIME has no literal to
        # find — the same `dynamic_reference` exemption validate_index.py
        # grants. The entry names the suffix instead, and the drift check
        # looks for THAT: a card that stopped fetching the family at all
        # still fails here. (No such entries yet in this instance.)
        needle = p.get("app_file_pattern") or ("data/app/" + p["app_file"])
        if needle not in html:
            findings.add(FAIL, p["layer"],
                         "index.html no longer references %s — manifest drift"
                         % needle)


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
            # The block LIFTING is the news — see il/scripts/validate_sources.py
            # for the fuller rationale (the fleet-wide `blocked` inversion).
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
              "`pip install -c ia/scripts/requirements.txt requests`", file=sys.stderr)
        sys.exit(1)

    findings = Findings()
    check_manifest_matches_app(html, findings)
    check_socrata(findings, args.offline)
    check_provenance(findings, args.offline)
    check_endpoints(findings, args.offline)

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

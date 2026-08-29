#!/usr/bin/env python3
"""
Post-rewrite sanity gate for the app and its generated data files.

The weekly roster workflows regenerate the officeholder rosters under
data/app/*.json (scripts/build_il_roster.py, build_cpd_roster.py) and open a
PR. Those builders validate their *input* (they refuse an incomplete roster),
but this script is the *output*-side gate: run it after any regeneration and
before opening a PR to confirm the app and its data are still coherent.

Before the P0 externalization these datasets were spliced into object literals
inside index.html and the risk was a mis-anchored regex dropping live code.
Now the builders emit plain JSON with json.dump (no splice, no escaping), so the
checks here are: index.html still parses and carries every layer, it no longer
embeds any dataset inline, and every app-data file is present and well formed.

Checks (all must pass; exits non-zero on the first failure):
  1. The main inline <script> still parses (`node --check`).
  2. registerLayer( appears at least as many times as expected, AND every layer
     id in EXPECT_LAYER_IDS is registered. Most layers register through the
     factories, so a lost factory-registered module would not move the raw
     registerLayer( count — the per-id check catches that (ported from the NYC
     fork per docs/ENGINE_SYNC.md backlog item 8, "port checks, not bytes").
  3. index.html embeds no dataset inline (no `JSON.parse('...')` blobs remain)
     and references each data/app/* file it fetches.
  4. Every expected data/app/*.json exists, parses, and has the right shape.
  5. LAYER_AREA_RANK lists every registered layer id exactly once and nothing
     else — the z-order honesty rule made executable so a layer can never be
     registered but forgotten in the stack (or vice versa).
  6. METRO_EXPLORERS entries are well formed (id/label/https url; bbox, when
     present, is a sane min<max box that does NOT contain this metro's own
     center — a bbox covering home would make the sibling-metro portal easter
     egg fire on every pan). Guards the copy-verbatim config diff every fork
     applies when a new metro launches.
  7. sw.js exactly-one-list invariant: every data/app/*.json on disk is
     cached in exactly one of the service worker's GEOMETRY_URLS / ROSTER_URLS,
     so no data file is ever un-cached or double-listed.
  8. Every county with a per-county dispatch entry is inside the scope mask's
     county list, DERIVED from index.html rather than from a hand-kept list.
     The wash claims "beyond here only the statewide layers answer"; this is
     what stops that claim going stale, as it did for LaSalle, Kankakee, Boone
     and Grundy across two research passes with no gate noticing.

Usage:
    python3 scripts/validate_index.py [path/to/index.html]
"""

import json
import os
import re
import subprocess
import sys
import tempfile

# Machine-readable capability declaration (docs/MECHANIZATION_PLAYBOOK.md,
# Conversion 3). The fleet-status workflow in the CHI repo parses this list
# from every fork's validator and diffs it against CHI's: a capability present
# in a fork but absent here is a reverse-parity WARN — the mechanical form of
# "fork-born validator improvements must land in CHI within one release
# cycle". Shape contract (CHI is the master): a module-level list literal
# named CAPABILITIES of kebab-case strings, one per distinct check this
# validator actually performs. Add an entry when you add a check; never
# declare a capability the code doesn't have.
CAPABILITIES = [
    "engine-fence-lint",        # 0/0c: ENGINE markers well formed, index.html + sw.js
    "metro-explorers-lint",     # 0b: portal list shape/bbox sanity
    "inline-script-parses",     # 1: node --check on the main inline script
    "register-layer-floor",     # 2: raw registerLayer( count floor
    "expect-layer-ids",         # 2: every expected layer id registered
    "layer-area-rank-lint",     # 2b: rank array covers the id set exactly
    "layer-sidebar-rank-lint",  # 2c: sidebar rank covers the id set exactly
    "no-inline-datasets",       # 3: no JSON.parse blobs; data files referenced
    "data-file-shapes",         # 4: every data/app file exists with sane counts
    "sw-exactly-one-list",      # 5: each data file cached in exactly one sw list
    "negative-point-ground-truth",  # 4b: worksheet negative point misses every anchor geometry (born in NYC; back-ported per the ENGINE_SYNC DoD)
    "county-coverage-ring",     # 8: dispatched counties are all inside the scope mask
    "sources-page-coverage",    # 6: the public sources page covers every layer and the app links it
]

# The constants below are GENERATED from metro-worksheet.json (Conversion 2 —
# edit the worksheet, run scripts/generate_metro_files.py). Fork history worth
# keeping by hand: this fork's registerLayer floor arithmetic is 1 function
# definition + 11 direct registerLayer() calls + 5 factory bodies; it was
# lowered 16 -> 15 when police-station/fire-station moved onto the
# registerNearestPointLayer factory (-2 direct calls, +1 body), and raised
# 15 -> 17 when the municipality (2026-07) and township (2026-08-19)
# identity layers became bespoke roster-joined blocks (+1 direct call each).
# ==== GENERATED:BEGIN validator-config ====
# Floor, not a moving target: new layers only raise this; a drop means
# modules were lost.
MIN_REGISTER_LAYER = 19

# Every layer id that must be registered in index.html. Most modules register
# through the factories, so deleting one would NOT lower the raw registerLayer(
# count above — this per-id list is the direct module-loss guard. Emitted in
# LAYER_AREA_RANK order; check 5 keeps the two naming the same set.
EXPECT_LAYER_IDS = [
    "wi-court-of-appeals", "us-house", "wtcs-district", "wi-senate",
    "wi-assembly", "wi-circuit-court", "county", "psap-area",
    "school-district-secondary", "school-district-unified",
    "school-district-elementary", "ems-service", "law-service",
    "fire-service", "county-board", "county-subdivision", "municipality",
    "zip-code", "mpd-district", "mps-school-board", "mpd-squad-area",
    "aldermanic-district", "ward", "milwaukee-neighborhoods",
    "madison-neighborhood-assoc", "tid-district", "police-station",
    "fire-station", "school-site", "library", "post-office",
]

# file -> (min features, max features) for the boundary layers fetched by the app.
GEOMETRY_FILES = {
    "metro-outline.json": (1, 1),  # The dissolved outline of the counties whose county board card NAMES a supervisor (wi/scripts/build_metro_outline.py, anchor-verified inside and outside). Regenerate whenever a county's roster ships — the wash is a claim about coverage and has to track it.
    "state-counties.json": (72, 72),  # Every county in the state, pre-built from TIGERweb by bootstrap_state.py (bounds tightened to the real count at bootstrap).
    "adams-county-outline.json": (1, 1),  # Adams County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "ashland-county-outline.json": (1, 1),  # Ashland County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "barron-county-outline.json": (1, 1),  # Barron County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "bayfield-county-outline.json": (1, 1),  # Bayfield County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "brown-county-outline.json": (1, 1),  # Brown County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "buffalo-county-outline.json": (1, 1),  # Buffalo County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "burnett-county-outline.json": (1, 1),  # Burnett County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "calumet-county-outline.json": (1, 1),  # Calumet County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "chippewa-county-outline.json": (1, 1),  # Chippewa County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "clark-county-outline.json": (1, 1),  # Clark County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "columbia-county-outline.json": (1, 1),  # Columbia County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "crawford-county-outline.json": (1, 1),  # Crawford County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "dane-county-outline.json": (1, 1),  # Dane County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "dodge-county-outline.json": (1, 1),  # Dodge County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "door-county-outline.json": (1, 1),  # Door County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "douglas-county-outline.json": (1, 1),  # Douglas County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "dunn-county-outline.json": (1, 1),  # Dunn County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "eau-claire-county-outline.json": (1, 1),  # Eau Claire County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "florence-county-outline.json": (1, 1),  # Florence County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "fond-du-lac-county-outline.json": (1, 1),  # Fond du Lac County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "forest-county-outline.json": (1, 1),  # Forest County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "grant-county-outline.json": (1, 1),  # Grant County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "green-county-outline.json": (1, 1),  # Green County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "green-lake-county-outline.json": (1, 1),  # Green Lake County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "iowa-county-outline.json": (1, 1),  # Iowa County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "iron-county-outline.json": (1, 1),  # Iron County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "jackson-county-outline.json": (1, 1),  # Jackson County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "jefferson-county-outline.json": (1, 1),  # Jefferson County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "juneau-county-outline.json": (1, 1),  # Juneau County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "kenosha-county-outline.json": (1, 1),  # Kenosha County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "kewaunee-county-outline.json": (1, 1),  # Kewaunee County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "la-crosse-county-outline.json": (1, 1),  # La Crosse County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "lafayette-county-outline.json": (1, 1),  # Lafayette County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "langlade-county-outline.json": (1, 1),  # Langlade County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "lincoln-county-outline.json": (1, 1),  # Lincoln County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "manitowoc-county-outline.json": (1, 1),  # Manitowoc County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "marathon-county-outline.json": (1, 1),  # Marathon County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "marinette-county-outline.json": (1, 1),  # Marinette County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "marquette-county-outline.json": (1, 1),  # Marquette County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "menominee-county-outline.json": (1, 1),  # Menominee County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "milwaukee-county-outline.json": (1, 1),  # Milwaukee County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "monroe-county-outline.json": (1, 1),  # Monroe County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "oconto-county-outline.json": (1, 1),  # Oconto County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "oneida-county-outline.json": (1, 1),  # Oneida County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "outagamie-county-outline.json": (1, 1),  # Outagamie County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "ozaukee-county-outline.json": (1, 1),  # Ozaukee County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "pepin-county-outline.json": (1, 1),  # Pepin County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "pierce-county-outline.json": (1, 1),  # Pierce County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "polk-county-outline.json": (1, 1),  # Polk County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "portage-county-outline.json": (1, 1),  # Portage County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "price-county-outline.json": (1, 1),  # Price County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "racine-county-outline.json": (1, 1),  # Racine County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "richland-county-outline.json": (1, 1),  # Richland County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "rock-county-outline.json": (1, 1),  # Rock County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "rusk-county-outline.json": (1, 1),  # Rusk County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "sauk-county-outline.json": (1, 1),  # Sauk County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "sawyer-county-outline.json": (1, 1),  # Sawyer County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "shawano-county-outline.json": (1, 1),  # Shawano County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "sheboygan-county-outline.json": (1, 1),  # Sheboygan County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "st-croix-county-outline.json": (1, 1),  # St. Croix County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "taylor-county-outline.json": (1, 1),  # Taylor County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "trempealeau-county-outline.json": (1, 1),  # Trempealeau County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "vernon-county-outline.json": (1, 1),  # Vernon County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "vilas-county-outline.json": (1, 1),  # Vilas County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "walworth-county-outline.json": (1, 1),  # Walworth County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "washburn-county-outline.json": (1, 1),  # Washburn County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "washington-county-outline.json": (1, 1),  # Washington County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "waukesha-county-outline.json": (1, 1),  # Waukesha County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "waupaca-county-outline.json": (1, 1),  # Waupaca County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "waushara-county-outline.json": (1, 1),  # Waushara County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "winnebago-county-outline.json": (1, 1),  # Winnebago County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "wood-county-outline.json": (1, 1),  # Wood County containment outline (wi/scripts/build_wi_county_outlines.py, sliced from state-counties.json) — lets a Data gaps record name this county so the panel leads with the gaps that apply here.
    "congress-districts.json": (8, 8),  # The state's U.S. House districts, pre-built from TIGERweb by bootstrap_state.py (bounds tightened at bootstrap).
    "school-districts-unified.json": (369, 369),  # The state's unified school districts, pre-built from TIGERweb by bootstrap_state.py (bounds tightened at bootstrap).
    "wi-senate-districts.json": (34, 34),  # The 33 State Senate districts plus TIGERweb's ZZ water pseudo-district, pre-built by wi/scripts/build_legislative_boundaries.py (2,000-point agreement gate).
    "wi-assembly-districts.json": (100, 100),  # The 99 State Assembly districts plus TIGERweb's ZZ water pseudo-district, pre-built by wi/scripts/build_legislative_boundaries.py (2,000-point agreement gate).
    "county-supervisory-districts.json": (1590, 1590),  # Every county board supervisory district in the state — 1,573 from LTSB's statewide aggregate plus Trempealeau's own 17, built by wi/scripts/build_wi_supervisory_districts.py (numbering, ward-reconciliation and 10,000-in-state-point agreement gates).
    "wi-circuit-courts.json": (69, 69),  # The 69 circuit courts as county unions — 66 single counties plus the three statutory two-county circuits (Wis. Stat. 753.06), dissolved from the shipped county file by wi/scripts/build_wi_circuit_courts.py under its partition, merge and containment gates. Rebuild only if the county file or the statute moves.
    "wi-court-of-appeals-districts.json": (4, 4),  # The four Court of Appeals districts as county unions (Wis. Stat. 752.11 + the court system's own lists agreeing county for county), dissolved by wi/scripts/build_wi_court_of_appeals.py under one-ring contiguity and 72-county containment gates.
    "wi-state-outline.json": (1, 1),  # The Wisconsin state outline — the coverage wash's REGION band, marking where the statewide layers and the county board DISTRICTS still answer even though no supervisor is named. Split out from metro-outline.json when that became the 20-county roster ring.
    "school-sites.json": (2850, 3500),  # Every placed school site in the state, public and private (2,966 at build: 2,138 + 828), pre-built from the DPI org's two school layers by wi/scripts/build_wi_school_sites.py — its gates page past the 2,000-record cap, skip only DPI's placeless virtual-program rows, and witness every point against the layer's own coordinate attributes. Amenity points, not officeholder data: cache-first is fine, and the range tolerates DPI's school-year rotation (WATCH.md).
    "mpd-districts.json": (7, 7),  # Milwaukee's seven police districts, the city's own CC-BY layer server-reprojected and witnessed against the CKAN shapefile's area shares (wi/scripts/build_milwaukee_city_layers.py). An operator rebuild; the monthly source report watches both endpoints.
    "milwaukee-neighborhoods.json": (190, 190),  # The city's 190 named neighborhoods, same builder and witness — which caught the city's two copies spelling one neighborhood apart (the service spelling ships, the divergence prints every build). Names title-cased for display with the raw all-caps value kept on the feature.
    "mps-school-board-districts.json": (8, 8),  # Milwaukee's eight MPS board districts, the city's own layer server-reprojected and witnessed at build time against the CKAN shapefile's area shares (wi/scripts/build_mps_school_board_districts.py). Redraws each decennial census (adopted 2022-02-25); an operator rebuild.
    "aldermanic-districts.json": (838, 838),  # Every aldermanic (and village trustee) district the ward fabric composes completely — coded city/village wards dissolved on the statewide municipality key by wi/scripts/build_wi_aldermanic_districts.py under its completeness, BAS-witness and point-agreement gates (838 districts, 155 municipalities; ten incomplete submissions excluded on the record). Rebuild after each Jan/Jul filing window; a count change is expected news.
    "library-sites.json": (460, 560),  # Every public library outlet in the state (482 at build), pre-built from the DPI org's libraries layer by wi/scripts/build_wi_libraries.py — whose bbox gate is what catches that layer's measured trap (its LAT/LONG attributes are Web Mercator meters; only the outSR=4326 geometry is real). Same cache posture and annual rotation as the school file.
    "fire-service-areas.json": (1046, 1046),  # 1,046 fire-department dispatch areas — the OEC's 3,009 effective NG911 FireBoundary polygons dissolved per agency by wi/scripts/build_wi_ng911_service_areas.py (expired rows dropped by date; filing-absence and 100.000% name-set agreement gates). An operator rebuild; the monthly source report watches the layer counts.
    "law-service-areas.json": (639, 639),  # 639 law-enforcement dispatch areas — the OEC's 3,083 effective NG911 LawEnforcementBoundary polygons dissolved per agency; plain -dissolve, never -dissolve2, so the concurrent-jurisdiction overlaps the counties filed survive (measured). Same builder and gates as the fire file.
    "psap-areas.json": (95, 95),  # 95 public safety answering points — the OEC's 205 effective NG911 PSAPBoundary polygons dissolved per agency (11 future-dated Expire rows KEPT, the case that proves the drop-by-date rule; 3 expired dropped). Same builder and gates as the fire/law files; an operator rebuild watched by the monthly source report.
    "ems-service-areas.json": (579, 579),  # 579 EMS dispatch areas — the OEC's 2,443 effective NG911 EmergencyMedicalServicesBoundary polygons dissolved per agency (34 expired rows dropped by date). Same builder and gates as the other three NG911 files; an operator rebuild watched by the monthly source report.
    "mpd-squad-areas.json": (25, 25),  # Milwaukee's 25 MPD squad areas — the city's own CC-BY layer server-reprojected, witnessed against the CKAN shapefile's area shares AND sample-verified inside their hundreds-digit districts (wi/scripts/build_milwaukee_city_layers.py). An operator rebuild; the monthly source report watches both endpoints.
    "wtcs-districts.json": (16, 16),  # The 16 Wisconsin Technical College System districts — DPI's own layer, server-generalized (~55 m) and pre-built under five gates: seat witness (each college's home city inside its own district), no overlaps, and the union's one lawful hole being Lake Winnebago (wi/scripts/build_wi_wtcs_districts.py, operator rebuild). Boards appointed (Wis. Stat. 38.08) — identity-only by design.
    "madison-tid-districts.json": (14, 14),  # Madison's active Tax Incremental Districts — the city's open-data layer intersected with DOR's certified active list under a three-surface agreement (the GIS layer's HALFMILERULE flag drops its 9 planning buffers, DOR closes the layer's two stale districts, the city program page supplies names; wi/scripts/build_madison_city_layers.py, operator rebuild). TID 55 (Voit Farm) is active with no published geometry — gap madison-tid-undrawn — so the count is 14, not DOR's 15.
    "madison-neighborhood-assocs.json": (100, 141),  # Madison's ACTIVE city-registered association boundaries (116 at first build of the city's 141 rows — the city's own STATUS flag is the filter; the Inactive are lapsed registrations). Same builder, operator rebuild.
    "madison-outline.json": (1, 1),  # The City of Madison corporate limits — the city's own 137-ward fabric dissolved to one MultiPolygon (4 parts, enclave holes kept: Maple Bluff, Shorewood Hills, the town islands). madisonCoverage's ground; same builder.
    "tid-districts.json": (79, 79),  # Milwaukee's 79 active Tax Incremental Districts — the city's own CC-BY layer server-reprojected, dissolved TIDs dropped by date, witnessed against the CKAN shapefile's area shares scoped to the city's own STATUS flag (wi/scripts/build_milwaukee_city_layers.py). An operator rebuild; the monthly source report watches both endpoints.
}

# file -> minimum key count (officeholder rosters).
ROSTER_FILES = {
    "congress-roster.json": 8,  # U.S. House roster for the state, built from unitedstates/congress-legislators by bootstrap_state.py and refreshed weekly by update-wi-congress-roster.yml (min tightened at bootstrap).
    "wi-senate-members.json": 31,  # State Senate roster from the Open States current-people export (wi.csv), refreshed weekly by update-wi-legislature-roster.yml; the floor tolerates transient vacancies (33 seats).
    "wi-assembly-members.json": 94,  # State Assembly roster from the Open States current-people export (wi.csv), refreshed weekly by update-wi-legislature-roster.yml; the floor tolerates transient vacancies (99 seats).
    "coverage-gaps.json": 1,  # The Data gaps panel's content; seeded minimal by bootstrap_state.py, grown as the fork records real gaps.
    "county-board-directory.json": 72,  # One row per county: board size read back from the shipped geometry, plus the county's own official page for the card's footer link. Built by wi/scripts/build_wi_county_board_directory.py; not a roster of people — Wisconsin publishes none statewide.
    "county-board-members.json": 716,  # County board supervisors for the 34 counties whose district-keyed member list this can obtain (745 seats) — 31 scraped from board pages, Milwaukee and Racine read off their own GIS layers (Milwaukee Legistar-witnessed). Built by wi/scripts/build_wi_county_board_roster.py, checked seat-for-seat against the shipped district geometry; refreshed weekly by update-wi-county-board-roster.yml, and Taylor carried from its own directory page as a dated document because its host answers a captcha to every automated client. The other 38 counties name nobody — their cards link the county board instead.
    "wi-circuit-judges.json": 69,  # The circuit-court bench — every circuit's judges with branch and direct phone where wicourts publishes them, plus the courthouse — keyed by the same circuit keys the geometry carries. Built by wi/scripts/build_wi_circuit_court_roster.py from the wicourts scrape; refreshed weekly by update-wi-circuit-court-roster.yml, whose composition assertion doubles as the circuit map's redistricting tripwire.
    "wi-court-of-appeals-roster.json": 4,  # The Court of Appeals bench — sixteen judges keyed by district with role, direct phone and chambers, the 4/4/3/5 seat split gated at scrape time. Built by wi/scripts/build_wi_coa_roster.py; refreshed weekly by update-wi-court-of-appeals-roster.yml, whose composition assertion is the appeals map's redistricting tripwire.
    "wi-county-clerks.json": 72,  # All 72 county clerks — name, party-or-appointed per the Blue Book's own legend, office, hours, phone, fax, e-mail — keyed by county GEOID. Built by wi/scripts/build_wi_county_clerk_roster.py from the two cross-gating open publishers; refreshed weekly by update-wi-county-clerk-roster.yml. Milwaukee's entry carries the statutory election-commission note.
    "mps-school-board-members.json": 3,  # The nine Milwaukee Board of School Directors (at-large president + districts 1-8, keyed to the geometry's DISTRICT values) with roles, term expirations and the Board office's contact, under {members, office, sourceUrl}. Built by wi/scripts/build_mps_school_board_roster.py from the district's own directors page with the committee-list witness; refreshed weekly by update-mps-school-board-roster.yml.
    "wi-alderpersons.json": 6,  # The alderperson roster for the six big cities with a verified, witnessed route (Milwaukee, Madison, Green Bay, Kenosha, Racine, Waukesha — 94 seats), keyed by the municipality's statewide COUSUBFP and zero-padded district id, the geometry file's exact key pair. Built by wi/scripts/build_wi_alderperson_roster.py with per-city, per-field floors and a geometry cross-gate; refreshed weekly by update-wi-alderperson-roster.yml.
    "wi-county-officers.json": 72,  # 72 counties x 7 offices from the Blue Book's county-officer tables (build_wi_county_officer_roster.py; layout-aware x-position parse, chair-seats witness, Menominee pin, shared-DA footnote). Dated April 2025 on every card; refreshed weekly with the clerk scrape.
    "mke-polling-places.json": 356,  # Milwaukee ward -> polling place pairing (build_mke_polling_places.py; CC-BY city dataset, ward keys gated equal to LTSB's Milwaukee wards, every pair witnessed against the city's own REST layer, places pointed and bbox-gated). Dated per dataset edition; rebuilt per election, not weekly.
    "mpd-district-captains.json": 7,  # MPD district captains roster (mpd_captains_scraper.py + build_mpd_captains_roster.py from the city's own per-district pages; keys exactly 1-7, >=6 named, name implies rank, sourceUrl pinned to the city's district path). Refreshed weekly by update-mpd-captains-roster.yml as a reviewed bot PR.
    "madison-polling-places.json": 130,  # Madison ward -> polling place pairing (build_madison_polling_places.py; the city's open-data polling layer is one point per ward, ward keys gated equal to LTSB's Madison wards AND the city's own ward layer, points bbox-gated). The layer publishes no edition date, so records are dated as read; rebuilt per election, not weekly.
    "adams-polling-places.json": 35,  # Adams County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 39 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "ashland-polling-places.json": 36,  # Ashland County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 41 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "barron-polling-places.json": 81,  # Barron County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 90 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "bayfield-polling-places.json": 36,  # Bayfield County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 41 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "brown-polling-places.json": 189,  # Brown County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 210 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "buffalo-polling-places.json": 24,  # Buffalo County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 27 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "burnett-polling-places.json": 36,  # Burnett County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 40 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "calumet-polling-places.json": 57,  # Calumet County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 64 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "chippewa-polling-places.json": 91,  # Chippewa County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 102 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "clark-polling-places.json": 72,  # Clark County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 81 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "columbia-polling-places.json": 81,  # Columbia County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 90 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "crawford-polling-places.json": 29,  # Crawford County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 33 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "dane-polling-places.json": 442,  # Dane County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 492 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "dodge-polling-places.json": 140,  # Dodge County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 156 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "door-polling-places.json": 56,  # Door County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 63 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "douglas-polling-places.json": 52,  # Douglas County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 58 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "dunn-polling-places.json": 58,  # Dunn County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 65 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "eau-claire-polling-places.json": 136,  # Eau Claire County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 152 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "florence-polling-places.json": 17,  # Florence County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 19 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "fond-du-lac-polling-places.json": 106,  # Fond du Lac County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 118 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "forest-polling-places.json": 30,  # Forest County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 34 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "grant-polling-places.json": 86,  # Grant County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 96 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "green-polling-places.json": 54,  # Green County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 60 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "green-lake-polling-places.json": 36,  # Green Lake County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 41 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "iowa-polling-places.json": 54,  # Iowa County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 60 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "iron-polling-places.json": 17,  # Iron County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 19 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "jackson-polling-places.json": 45,  # Jackson County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 51 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "jefferson-polling-places.json": 99,  # Jefferson County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 110 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "juneau-polling-places.json": 60,  # Juneau County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 67 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "kenosha-polling-places.json": 170,  # Kenosha County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 189 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "kewaunee-polling-places.json": 37,  # Kewaunee County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 42 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "la-crosse-polling-places.json": 104,  # La Crosse County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 116 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "lafayette-polling-places.json": 45,  # Lafayette County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 51 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "langlade-polling-places.json": 32,  # Langlade County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 36 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "lincoln-polling-places.json": 50,  # Lincoln County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 56 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "manitowoc-polling-places.json": 80,  # Manitowoc County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 89 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "marathon-polling-places.json": 148,  # Marathon County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 165 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "marinette-polling-places.json": 58,  # Marinette County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 65 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "marquette-polling-places.json": 33,  # Marquette County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 37 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "menominee-polling-places.json": 4,  # Menominee County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 5 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "milwaukee-polling-places.json": 544,  # Milwaukee County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 605 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "monroe-polling-places.json": 77,  # Monroe County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 86 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "oconto-polling-places.json": 62,  # Oconto County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 69 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "oneida-polling-places.json": 57,  # Oneida County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 64 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "outagamie-polling-places.json": 189,  # Outagamie County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 210 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "ozaukee-polling-places.json": 90,  # Ozaukee County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 101 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "pepin-polling-places.json": 18,  # Pepin County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 21 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "pierce-polling-places.json": 53,  # Pierce County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 59 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "polk-polling-places.json": 63,  # Polk County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 70 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "portage-polling-places.json": 90,  # Portage County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 100 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "price-polling-places.json": 34,  # Price County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 38 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "racine-polling-places.json": 178,  # Racine County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 198 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "richland-polling-places.json": 45,  # Richland County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 51 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "rock-polling-places.json": 164,  # Rock County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 183 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "rusk-polling-places.json": 61,  # Rusk County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 68 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "sauk-polling-places.json": 109,  # Sauk County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 122 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "sawyer-polling-places.json": 36,  # Sawyer County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 41 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "shawano-polling-places.json": 68,  # Shawano County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 76 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "sheboygan-polling-places.json": 108,  # Sheboygan County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 121 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "st-croix-polling-places.json": 117,  # St. Croix County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 131 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "taylor-polling-places.json": 35,  # Taylor County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 39 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "trempealeau-polling-places.json": 49,  # Trempealeau County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 55 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "vernon-polling-places.json": 56,  # Vernon County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 63 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "vilas-polling-places.json": 39,  # Vilas County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 44 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "walworth-polling-places.json": 138,  # Walworth County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 154 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "washburn-polling-places.json": 33,  # Washburn County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 37 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "washington-polling-places.json": 158,  # Washington County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 176 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "waukesha-polling-places.json": 329,  # Waukesha County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 366 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "waupaca-polling-places.json": 88,  # Waupaca County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 98 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "waushara-polling-places.json": 40,  # Waushara County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 45 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "winnebago-polling-places.json": 142,  # Winnebago County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 158 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
    "wood-polling-places.json": 100,  # Wood County ward → polling place pairing for the 2026 General Election — wi/scripts/build_wi_polling_places.py, from the workbook the Wisconsin Elections Commission sent 2026-08-27 (wi/data/source/wec/). PROVISIONAL until the Commission publishes its November edition; 112 of the county's LTSB wards are paired, and the card names the election, the provisional status and MyVote as the confirmation route.
}

# Files the app references DYNAMICALLY — the URL is built from a slug at
# runtime (the gaps panel's <slug>-county-outline.json contract), so no
# literal appears in index.html. Exempt from the reference check only;
# existence, shape and the negative-point test still apply.
DYNAMIC_REFERENCE = frozenset({
    "adams-county-outline.json",
    "ashland-county-outline.json",
    "barron-county-outline.json",
    "bayfield-county-outline.json",
    "brown-county-outline.json",
    "buffalo-county-outline.json",
    "burnett-county-outline.json",
    "calumet-county-outline.json",
    "chippewa-county-outline.json",
    "clark-county-outline.json",
    "columbia-county-outline.json",
    "crawford-county-outline.json",
    "dane-county-outline.json",
    "dodge-county-outline.json",
    "door-county-outline.json",
    "douglas-county-outline.json",
    "dunn-county-outline.json",
    "eau-claire-county-outline.json",
    "florence-county-outline.json",
    "fond-du-lac-county-outline.json",
    "forest-county-outline.json",
    "grant-county-outline.json",
    "green-county-outline.json",
    "green-lake-county-outline.json",
    "iowa-county-outline.json",
    "iron-county-outline.json",
    "jackson-county-outline.json",
    "jefferson-county-outline.json",
    "juneau-county-outline.json",
    "kenosha-county-outline.json",
    "kewaunee-county-outline.json",
    "la-crosse-county-outline.json",
    "lafayette-county-outline.json",
    "langlade-county-outline.json",
    "lincoln-county-outline.json",
    "manitowoc-county-outline.json",
    "marathon-county-outline.json",
    "marinette-county-outline.json",
    "marquette-county-outline.json",
    "menominee-county-outline.json",
    "milwaukee-county-outline.json",
    "monroe-county-outline.json",
    "oconto-county-outline.json",
    "oneida-county-outline.json",
    "outagamie-county-outline.json",
    "ozaukee-county-outline.json",
    "pepin-county-outline.json",
    "pierce-county-outline.json",
    "polk-county-outline.json",
    "portage-county-outline.json",
    "price-county-outline.json",
    "racine-county-outline.json",
    "richland-county-outline.json",
    "rock-county-outline.json",
    "rusk-county-outline.json",
    "sauk-county-outline.json",
    "sawyer-county-outline.json",
    "shawano-county-outline.json",
    "sheboygan-county-outline.json",
    "st-croix-county-outline.json",
    "taylor-county-outline.json",
    "trempealeau-county-outline.json",
    "vernon-county-outline.json",
    "vilas-county-outline.json",
    "walworth-county-outline.json",
    "washburn-county-outline.json",
    "washington-county-outline.json",
    "waukesha-county-outline.json",
    "waupaca-county-outline.json",
    "waushara-county-outline.json",
    "winnebago-county-outline.json",
    "wood-county-outline.json",
    "adams-polling-places.json",
    "ashland-polling-places.json",
    "barron-polling-places.json",
    "bayfield-polling-places.json",
    "brown-polling-places.json",
    "buffalo-polling-places.json",
    "burnett-polling-places.json",
    "calumet-polling-places.json",
    "chippewa-polling-places.json",
    "clark-polling-places.json",
    "columbia-polling-places.json",
    "crawford-polling-places.json",
    "dane-polling-places.json",
    "dodge-polling-places.json",
    "door-polling-places.json",
    "douglas-polling-places.json",
    "dunn-polling-places.json",
    "eau-claire-polling-places.json",
    "florence-polling-places.json",
    "fond-du-lac-polling-places.json",
    "forest-polling-places.json",
    "grant-polling-places.json",
    "green-polling-places.json",
    "green-lake-polling-places.json",
    "iowa-polling-places.json",
    "iron-polling-places.json",
    "jackson-polling-places.json",
    "jefferson-polling-places.json",
    "juneau-polling-places.json",
    "kenosha-polling-places.json",
    "kewaunee-polling-places.json",
    "la-crosse-polling-places.json",
    "lafayette-polling-places.json",
    "langlade-polling-places.json",
    "lincoln-polling-places.json",
    "manitowoc-polling-places.json",
    "marathon-polling-places.json",
    "marinette-polling-places.json",
    "marquette-polling-places.json",
    "menominee-polling-places.json",
    "milwaukee-polling-places.json",
    "monroe-polling-places.json",
    "oconto-polling-places.json",
    "oneida-polling-places.json",
    "outagamie-polling-places.json",
    "ozaukee-polling-places.json",
    "pepin-polling-places.json",
    "pierce-polling-places.json",
    "polk-polling-places.json",
    "portage-polling-places.json",
    "price-polling-places.json",
    "racine-polling-places.json",
    "richland-polling-places.json",
    "rock-polling-places.json",
    "rusk-polling-places.json",
    "sauk-polling-places.json",
    "sawyer-polling-places.json",
    "shawano-polling-places.json",
    "sheboygan-polling-places.json",
    "st-croix-polling-places.json",
    "taylor-polling-places.json",
    "trempealeau-polling-places.json",
    "vernon-polling-places.json",
    "vilas-polling-places.json",
    "walworth-polling-places.json",
    "washburn-polling-places.json",
    "washington-polling-places.json",
    "waukesha-polling-places.json",
    "waupaca-polling-places.json",
    "waushara-polling-places.json",
    "winnebago-polling-places.json",
    "wood-polling-places.json",
})
# ==== GENERATED:END validator-config ====


def fail(msg):
    print("validate_index: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


# ENGINE fence lint (docs/ENGINE_SYNC.md): the cross-fork byte comparison is
# scripts/check_engine_parity.py's job; this merge gate only guards fence
# structure so a bad edit can't silently break the parity check itself.
ENGINE_MARKER_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--)[ \t]*==== ENGINE:(BEGIN|END) ([a-z0-9][a-z0-9-]*) ====[ \t]*(?:\*/|-->)[ \t]*$"
)


def check_engine_markers(html):
    open_name = None
    names = set()
    for lineno, line in enumerate(html.splitlines(), 1):
        m = ENGINE_MARKER_RE.match(line)
        if not m:
            continue
        kind, name = m.groups()
        if kind == "BEGIN":
            if open_name is not None:
                fail("line %d: ENGINE:BEGIN %s while %s is still open" % (lineno, name, open_name))
            if name in names:
                fail("line %d: duplicate ENGINE block name %r" % (lineno, name))
            open_name = name
            names.add(name)
        else:
            if name != open_name:
                fail("line %d: ENGINE:END %s does not match open block %r" % (lineno, name, open_name))
            open_name = None
    if open_name is not None:
        fail("ENGINE block %s is never closed" % open_name)
    if not names:
        fail("no ENGINE blocks found — fences were deleted? (docs/ENGINE_SYNC.md)")
    return len(names)


def _split_object_literals(block):
    """Split the body of a JS array literal into its top-level {...} entries
    (depth-tracked, so nested objects like bbox stay inside their entry)."""
    entries, depth, start = [], 0, None
    for i, ch in enumerate(block):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                entries.append(block[start:i + 1])
                start = None
    return entries


def check_metro_explorers(html):
    """Lint the METRO_EXPLORERS config list (the copy-verbatim cross-fork
    diff applied whenever a new metro launches — the likeliest place for a
    future typo to land). bbox drives the sibling-metro portal easter egg."""
    m = re.search(r'var THIS_METRO = "([a-z0-9-]+)"', html)
    if not m:
        fail("could not find THIS_METRO in the METRO config block")
    this_metro = m.group(1)
    m = re.search(r"var METRO_CENTER = \[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]", html)
    if not m:
        fail("could not find METRO_CENTER in the METRO config block")
    center_lat, center_lng = float(m.group(1)), float(m.group(2))
    m = re.search(r"var METRO_EXPLORERS = \[(.*?)\n\s*\];", html, re.DOTALL)
    if not m:
        fail("could not find the METRO_EXPLORERS list in the METRO config block")
    entries = _split_object_literals(m.group(1))
    if not entries:
        fail("METRO_EXPLORERS is empty")

    ids = []
    for entry in entries:
        eid = re.search(r'\bid:\s*"([^"]*)"', entry)
        label = re.search(r'\blabel:\s*"([^"]*)"', entry)
        url = re.search(r'\burl:\s*"([^"]*)"', entry)
        if not (eid and eid.group(1)):
            fail("METRO_EXPLORERS entry missing id: %s" % entry.strip()[:80])
        if not (label and label.group(1)):
            fail("METRO_EXPLORERS[%s] missing label" % eid.group(1))
        if not (url and url.group(1).startswith("https://")):
            fail("METRO_EXPLORERS[%s] url missing or not https" % eid.group(1))
        ids.append(eid.group(1))

        bm = re.search(r"\bbbox:\s*\{([^}]*)\}", entry)
        if not bm:
            continue  # no bbox = the metro opts out of the portal; allowed
        vals = dict(re.findall(r"(minLng|minLat|maxLng|maxLat):\s*(-?[\d.]+)", bm.group(1)))
        if sorted(vals) != ["maxLat", "maxLng", "minLat", "minLng"]:
            fail("METRO_EXPLORERS[%s] bbox is missing fields (need minLng/minLat/maxLng/maxLat)" % eid.group(1))
        b = {k: float(v) for k, v in vals.items()}
        if not (b["minLat"] < b["maxLat"] and b["minLng"] < b["maxLng"]):
            fail("METRO_EXPLORERS[%s] bbox is inverted (min must be < max on both axes)" % eid.group(1))
        if eid.group(1) != this_metro and (
            b["minLat"] <= center_lat <= b["maxLat"] and b["minLng"] <= center_lng <= b["maxLng"]
        ):
            fail(
                "METRO_EXPLORERS[%s] bbox contains this metro's own center (%s, %s) — "
                "the metro-portal easter egg would fire on every pan at home" % (eid.group(1), center_lat, center_lng)
            )

    if len(set(ids)) != len(ids):
        fail("METRO_EXPLORERS has duplicate ids: %s" % ids)
    if this_metro not in ids:
        fail('METRO_EXPLORERS has no entry for THIS_METRO ("%s")' % this_metro)
    return len(ids)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    if not os.path.exists(path):
        fail("no such file: " + path)
    html = open(path).read()
    repo_root = os.path.dirname(os.path.abspath(path))
    app_dir = os.path.join(repo_root, "data", "app")

    # 0. ENGINE fences are structurally sound (docs/ENGINE_SYNC.md)
    check_engine_markers(html)

    # 0b. METRO_EXPLORERS config list is sane (metro-portal easter egg)
    n_metros = check_metro_explorers(html)

    # 0c. sw.js ENGINE fences are structurally sound too (the service worker's
    # handler logic is shared engine; docs/ENGINE_SYNC.md). Absence is reported
    # by check_sw_lists below with a clearer message.
    sw_path = os.path.join(repo_root, "sw.js")
    if os.path.exists(sw_path):
        check_engine_markers(open(sw_path).read())

    # 1. main inline script parses
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    if not scripts:
        fail("no inline <script> blocks found")
    main_script = max(scripts, key=len)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
        tf.write(main_script)
        js_path = tf.name
    try:
        proc = subprocess.run(["node", "--check", js_path], capture_output=True, text=True)
    finally:
        os.unlink(js_path)
    if proc.returncode != 0:
        fail("inline script failed `node --check`:\n" + (proc.stderr or proc.stdout))

    # 2. no modules lost — engine floor plus every expected layer id present
    n = len(re.findall(r"registerLayer\(", html))
    if n < MIN_REGISTER_LAYER:
        fail("registerLayer( count %d < expected floor %d — a module was likely deleted" % (n, MIN_REGISTER_LAYER))
    for lid in EXPECT_LAYER_IDS:
        if ('id: "%s"' % lid) not in html:
            fail('layer id "%s" is not registered in index.html' % lid)

    # 2b. LAYER_AREA_RANK covers every registered id exactly once, and nothing
    # else (no "stub", no dropped layer). This is the z-order pass made
    # executable: reorderActiveLayers() walks this list, so a registered layer
    # missing here never gets restacked, and a stale id here is a silent no-op
    # that hides a rename.
    m = re.search(r"var LAYER_AREA_RANK = \[(.*?)\];", html, re.DOTALL)
    if not m:
        fail("LAYER_AREA_RANK array not found in index.html")
    rank = re.findall(r'"([a-z0-9-]+)"', m.group(1))
    dupes = sorted(set(x for x in rank if rank.count(x) > 1))
    if dupes:
        fail("LAYER_AREA_RANK lists these ids more than once: %s" % ", ".join(dupes))
    expected = set(EXPECT_LAYER_IDS)
    got = set(rank)
    missing = sorted(expected - got)
    extra = sorted(got - expected)
    if missing:
        fail("LAYER_AREA_RANK is missing registered layer id(s): %s" % ", ".join(missing))
    if extra:
        fail("LAYER_AREA_RANK has id(s) not in the registered set: %s" % ", ".join(extra))

    # 2c. LAYER_SIDEBAR_RANK covers every registered id exactly once, and
    # nothing else — same contract as 2b for the sidebar display order
    # (docs/EXPANSION_GUIDE.md Part 4 "Sidebar placement standard"): the boot
    # sort deliberately sinks an unranked id to the end instead of throwing,
    # so this check is the only place a rank/registry drift fails loudly.
    m = re.search(r"var LAYER_SIDEBAR_RANK = \[(.*?)\];", html, re.DOTALL)
    if not m:
        fail("LAYER_SIDEBAR_RANK array not found in index.html")
    srank = re.findall(r'"([a-z0-9-]+)"', m.group(1))
    dupes = sorted(set(x for x in srank if srank.count(x) > 1))
    if dupes:
        fail("LAYER_SIDEBAR_RANK lists these ids more than once: %s" % ", ".join(dupes))
    got = set(srank)
    missing = sorted(expected - got)
    extra = sorted(got - expected)
    if missing:
        fail("LAYER_SIDEBAR_RANK is missing registered layer id(s): %s" % ", ".join(missing))
    if extra:
        fail("LAYER_SIDEBAR_RANK has id(s) not in the registered set: %s" % ", ".join(extra))

    # 3. nothing embedded inline anymore, and every data file is referenced
    blobs = re.findall(r"var (\w+) = JSON\.parse\('", html)
    if blobs:
        fail("dataset(s) still embedded inline (should be in data/app/): %s" % blobs)
    for fname in list(GEOMETRY_FILES) + list(ROSTER_FILES):
        if fname in DYNAMIC_REFERENCE:
            continue  # URL built from a slug at runtime — see the generated set
        if ("data/app/" + fname) not in html:
            fail("index.html does not reference data/app/%s" % fname)

    # 4. every app-data file exists, parses, and has the right shape
    for fname, (lo, hi) in GEOMETRY_FILES.items():
        fpath = os.path.join(app_dir, fname)
        if not os.path.exists(fpath):
            fail("missing app-data file: data/app/%s" % fname)
        try:
            gj = json.load(open(fpath))
        except Exception as e:
            fail("data/app/%s does not parse as JSON: %s" % (fname, e))
        feats = gj.get("features") if isinstance(gj, dict) else None
        if gj.get("type") != "FeatureCollection" or not isinstance(feats, list):
            fail("data/app/%s is not a GeoJSON FeatureCollection" % fname)
        if not (lo <= len(feats) <= hi):
            fail("data/app/%s has %d features, expected %d-%d" % (fname, len(feats), lo, hi))

    for fname, min_keys in ROSTER_FILES.items():
        fpath = os.path.join(app_dir, fname)
        if not os.path.exists(fpath):
            fail("missing app-data file: data/app/%s" % fname)
        try:
            roster = json.load(open(fpath))
        except Exception as e:
            fail("data/app/%s does not parse as JSON: %s" % (fname, e))
        if not isinstance(roster, dict):
            fail("data/app/%s is not a JSON object" % fname)
        if len(roster) < min_keys:
            fail("data/app/%s has %d entries, expected at least %d" % (fname, len(roster), min_keys))

    # 5. sw.js exactly-one-list invariant: every data/app/*.json on disk
    # must be cached in exactly one of GEOMETRY_URLS (cache-first) or ROSTER_URLS
    # (network-first). A boundary served network-first would be a needless fetch;
    # a roster served cache-first could name a stale officeholder — the cardinal
    # sin here. An un-listed file silently loses offline support.
    # 4b. negative ground-truth point misses every anchor geometry
    check_negative_point(repo_root, app_dir)

    check_sw_lists(repo_root, app_dir)

    # 5. every county the app dispatches a layer on is inside the coverage ring
    n_counties = check_county_coverage_list(html, repo_root)

    # 6. the public sources page, if this fork ships one, still accounts for
    # every layer and is still reachable from the app.
    n_sourced = check_sources_page(html, repo_root)

    print(
        "validate_index: OK — inline script parses, %d registerLayer( calls, "
        "LAYER_AREA_RANK + LAYER_SIDEBAR_RANK cover all %d ids, no inline datasets, %d well-formed "
        "METRO_EXPLORERS entries, all data/app files present and cached in "
        "exactly one sw.js list, %d dispatched counties all inside the coverage ring%s"
        % (n, len(EXPECT_LAYER_IDS), n_metros, n_counties,
           "" if n_sourced is None else
           ", sources page linked and covering all %d layers" % n_sourced)
    )


SOURCES_PAGE = "sources.html"


def check_sources_page(html, repo_root):
    """The public sources page accounts for every registered layer, and the app
    still links to it. Returns the number of layers covered, or None if this
    fork ships no such page.

    Two failure modes, neither of which any other gate sees. A layer that ships
    without a matrix row leaves a reader reading the page as complete when it
    isn't — silence about a source reads as 'there is no source'. And a page
    nothing links to is a page nobody reads: the credits row that used to sit
    in the footer was self-evidently reachable, a separate page is only as
    reachable as its pointer. The row-per-layer content itself is generated
    from the same worksheet list as EXPECT_LAYER_IDS
    (scripts/generate_metro_files.py), so this checks the OUTCOME rather than
    trusting that the generator ran."""
    path = os.path.join(repo_root, SOURCES_PAGE)
    if not os.path.exists(path):
        return None
    page = open(path, encoding="utf-8").read()
    missing = [lid for lid in EXPECT_LAYER_IDS if ('id="layer-%s"' % lid) not in page]
    if missing:
        fail("%s has no matrix row for %d layer(s): %s — regenerate with "
             "scripts/generate_metro_files.py after adding the layer's source "
             "block to metro-worksheet.json"
             % (SOURCES_PAGE, len(missing), ", ".join(missing)))
    if SOURCES_PAGE not in html:
        fail("index.html no longer links to %s — the page ships but nothing in "
             "the app points a reader at it" % SOURCES_PAGE)
    return len(EXPECT_LAYER_IDS)


def _point_in_geometry(lng, lat, geom):
    """Stdlib ray-casting point-in-polygon over a GeoJSON (Multi)Polygon."""
    def ring_hit(ring):
        inside = False
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return any(ring_hit(p[0]) and not any(ring_hit(h) for h in p[1:]) for p in polys)


def check_negative_point(repo_root, app_dir):
    """4b. The worksheet's negative ground-truth point must miss EVERY feature
    of every anchor geometry file — the honest no-district state the smoke
    test asserts is only meaningful if the committed geometries agree. Catches
    a re-simplified boundary quietly swallowing the negative point."""
    ws_path = os.path.join(repo_root, "metro-worksheet.json")
    if not os.path.exists(ws_path):
        fail("metro-worksheet.json not found — negative-point ground truth needs it")
    ws = json.load(open(ws_path))
    neg = ws["negative_point"]
    lng, lat = neg["lng"], neg["lat"]
    for fname in GEOMETRY_FILES:
        gj = json.load(open(os.path.join(app_dir, fname)))
        for feat in gj.get("features", []):
            geom = feat.get("geometry") or {}
            if geom.get("type") not in ("Polygon", "MultiPolygon"):
                # amenity-point files (school-sites, library-sites) ride the
                # geometry list for their cache policy, but a point cannot
                # contain the negative point — nothing to assert here
                continue
            if _point_in_geometry(lng, lat, geom):
                fail(
                    "negative point %.5f,%.5f is INSIDE a feature of data/app/%s (%r) — "
                    "it must miss every anchor geometry; pick a new negative point in the "
                    "worksheet or check the geometry build" % (lat, lng, fname, feat.get("properties"))
                )


def _sw_url_list(sw, name):
    """Extract the ./data/app/*.json basenames from a `const NAME = [...]` array."""
    m = re.search(r"const %s = \[(.*?)\];" % name, sw, re.DOTALL)
    if not m:
        fail("sw.js: %s array not found" % name)
    return re.findall(r'\./data/app/([A-Za-z0-9._-]+\.json)', m.group(1))


def check_sw_lists(repo_root, app_dir):
    sw_path = os.path.join(repo_root, "sw.js")
    if not os.path.exists(sw_path):
        fail("sw.js not found next to index.html")
    sw = open(sw_path).read()
    geometry = _sw_url_list(sw, "GEOMETRY_URLS")
    roster = _sw_url_list(sw, "ROSTER_URLS")

    # No file appears in both lists.
    both = sorted(set(geometry) & set(roster))
    if both:
        fail("sw.js: file(s) in BOTH GEOMETRY_URLS and ROSTER_URLS: %s" % ", ".join(both))

    listed = geometry + roster
    dupes = sorted(set(x for x in listed if listed.count(x) > 1))
    if dupes:
        fail("sw.js: file(s) listed more than once: %s" % ", ".join(dupes))

    # Every listed file exists on disk.
    for fname in listed:
        if not os.path.exists(os.path.join(app_dir, fname)):
            fail("sw.js caches data/app/%s but the file does not exist" % fname)

    # Every data/app/*.json on disk is cached in exactly one list.
    on_disk = set(f for f in os.listdir(app_dir) if f.endswith(".json"))
    uncached = sorted(on_disk - set(listed))
    if uncached:
        fail("data/app file(s) not cached in any sw.js list: %s" % ", ".join(uncached))


# Layers that dispatch by MUNICIPALITY rather than by county. Their entry keys
# are place names, so they are exempt from the county check below. Listed, not
# inferred: a new municipality-keyed concept should have to say so here rather
# than quietly opting itself out of the guard.
MUNICIPALITY_KEYED_LAYERS = {"ward"}


# The distinctive word each county-dispatched layer's loader names carry. Used
# to catch an entry pasted into the wrong table: a loader that reads as another
# concept, and not as its own, is misfiled. Keys absent here are not checked.
LAYER_CONCEPT_TOKEN = {
    "county-board": "Board",
    "county-precinct": "Precinct",
    "fire-district": "Fire",
    "library-district": "Library",
    "park-district": "Park",
    "judicial-subcircuit": "Subcircuit",
}


def _literals_from(path, names):
    """Read module-level literals without importing the module.

    build_metro_outline.py imports `requests`, which is not installed in the
    smoke-test workflow where this gate runs — and executing a builder to read
    two constants would be the wrong trade anyway. ast parses, never runs.
    """
    import ast
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    found = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                try:
                    found[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    pass
    missing = sorted(set(names) - set(found))
    if missing:
        fail("%s no longer defines %s — the county-list check cannot run"
             % (os.path.basename(path), ", ".join(missing)))
    return found


def check_county_coverage_list(html, repo_root):
    """Every county the app dispatches a layer on must be inside the scope mask.

    THE BUG THIS EXISTS FOR: the mask's county list was previously guarded only
    by the outline builder's OUTSIDE anchors, which catch a county only if
    somebody had already thought to name it. LaSalle, Kankakee, Boone and Grundy
    therefore shipped layers and stayed greyed out for two research passes —
    the wash telling residents "beyond here only the statewide layers answer"
    while five of their layers answered. Nothing failed, because nothing was
    comparing the list against what the app actually registers.

    So this derives the answer instead of trusting a list: it reads the county
    keys out of index.html's own dispatch tables and requires each one to be in
    METRO_COUNTY_FIPS. An unrecognised key fails too — a new county that nobody
    added to DISPATCH_COUNTY_FIPS is exactly the case that used to slip through.

    IT ALSO CHECKS THE REVERSE, which for a long time nothing did: a
    DISPATCH_COUNTY_FIPS row with no dispatch entry behind it. That gap was
    found on 2026-08-02 while shipping the at-large tier (Pike, Brown, Calhoun,
    Putnam) — counties served entirely through the COUNTY card, with no dispatch
    entry of any kind. The expansion guide had said to add such a county to
    DISPATCH_COUNTY_FIPS "if any other layer answers there", and adding one
    anyway passed every gate silently, because this function only ever looked
    from index.html outward. A stale row is not cosmetic: DISPATCH_COUNTY_FIPS
    is what build_county_outline.py cross-checks FIPS against and what the
    guidebook and CLAUDE.md quote as the count of dispatched counties, so a
    county listed there but dispatching nothing makes all three quietly wrong.
    An at-large county belongs in METRO_COUNTY_FIPS only.
    """
    outline_py = os.path.join(repo_root, "scripts", "build_metro_outline.py")
    if not os.path.exists(outline_py):
        fail("scripts/build_metro_outline.py not found — the county-list check "
             "cannot run; it is the source of the coverage ring")
    consts = _literals_from(outline_py, ("DISPATCH_COUNTY_FIPS", "METRO_COUNTY_FIPS"))
    slug_fips = consts["DISPATCH_COUNTY_FIPS"]
    in_ring = set(consts["METRO_COUNTY_FIPS"])

    # Split the script at every top-level register*() call so each dispatch
    # table is read within its own call and cannot absorb a neighbour's keys.
    chunks = re.split(r"\n  (register[A-Za-z]*)\(\{", html)
    unknown, outside, misfiled = [], [], []
    seen_counties = set()
    for i in range(1, len(chunks) - 1, 2):
        if chunks[i] != "registerCountyLayer":
            continue
        body = chunks[i + 1]
        layer_id = re.search(r'id:\s*"([a-z-]+)"', body)
        if not layer_id or layer_id.group(1) in MUNICIPALITY_KEYED_LAYERS:
            continue
        lid = layer_id.group(1)
        keys_here = re.findall(r'key:\s*"([a-z-]+)"', body)
        dupes = sorted({k for k in keys_here if keys_here.count(k) > 1})
        if dupes:
            fail("%s registers the same county key twice: %s. registerCountyLayer's "
                 "byKey lookup is LAST-WINS and render/cardIdentifier/primaryLink "
                 "all dispatch through it, so the duplicate silently re-points the "
                 "first entry's card at the second entry's renderer — no gate "
                 "notices, because the layer still registers and still queries."
                 % (lid, ", ".join(dupes)))
        # An entry whose loader belongs to a DIFFERENT concept is an entry pasted
        # into the wrong table. That shipped twice (2026-08-03/04): precinct
        # entries for Stephenson and Macon landed in county-board, which gave
        # Macon a board card it must not have and broke Stephenson's. The keys
        # were legal and unique, so nothing above caught it.
        own = LAYER_CONCEPT_TOKEN.get(lid)
        if own:
            others = {t for k, t in LAYER_CONCEPT_TOKEN.items() if t != own}
            for ekey, loader in re.findall(
                    r'key:\s*"([a-z-]+)",\s*\n\s*coverage:[^\n]*\n\s*'
                    r'(?:loadGeometry|loader):\s*(\w+)', body):
                foreign = sorted(t for t in others if t in loader)
                if foreign and own not in loader:
                    misfiled.append("%s entry '%s' uses %s (reads as %s, not %s)"
                                    % (lid, ekey, loader, "/".join(foreign), own))
        for key in keys_here:
            if key not in slug_fips:
                unknown.append("%s: %s" % (lid, key))
                continue
            seen_counties.add(key)
            if slug_fips[key] not in in_ring:
                outside.append("%s (%s)" % (key, lid))

    if misfiled:
        fail("dispatch entr%s sitting in the wrong layer's table: %s. Move the "
             "entry into the registerCountyLayer call for its own concept."
             % ("ies are" if len(misfiled) > 1 else "y is", "; ".join(sorted(misfiled))))
    if unknown:
        fail("dispatch entr%s for a county with no DISPATCH_COUNTY_FIPS entry: %s. "
             "Add the county (slug -> Census FIPS) to scripts/build_metro_outline.py, "
             "or list its layer in MUNICIPALITY_KEYED_LAYERS if it dispatches by "
             "place rather than county."
             % ("ies" if len(unknown) > 1 else "y", ", ".join(sorted(set(unknown)))))
    if outside:
        fail("county/counties serve layers but are NOT in METRO_COUNTY_FIPS, so the "
             "out-of-scope wash greys them out while their cards answer: %s. Add "
             "them to scripts/build_metro_outline.py and rebuild "
             "data/app/metro-outline.json."
             % ", ".join(sorted(set(outside))))

    # The reverse direction (see the docstring): listed as dispatched, but
    # dispatching nothing.
    undispatched = sorted(set(slug_fips) - seen_counties)
    if undispatched:
        fail("county/counties in DISPATCH_COUNTY_FIPS that register NO dispatch "
             "entry in index.html: %s. That list is the count of dispatched "
             "counties the docs quote and the FIPS table build_county_outline.py "
             "cross-checks, so a row with nothing behind it makes both wrong. If "
             "the county is served only through the COUNTY card (an AT-LARGE "
             "board — EXPANSION_GUIDE §2.5.1), remove it from DISPATCH_COUNTY_FIPS "
             "and leave it in METRO_COUNTY_FIPS. Otherwise its dispatch entry was "
             "dropped — restore it."
             % ", ".join(undispatched))
    return len(seen_counties)


if __name__ == "__main__":
    main()

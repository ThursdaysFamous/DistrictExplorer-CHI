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
MIN_REGISTER_LAYER = 17

# Every layer id that must be registered in index.html. Most modules register
# through the factories, so deleting one would NOT lower the raw registerLayer(
# count above — this per-id list is the direct module-loss guard. Emitted in
# LAYER_AREA_RANK order; check 5 keeps the two naming the same set.
EXPECT_LAYER_IDS = [
    "il-supreme-court", "congress", "il-senate", "il-house", "county", "mwrd",
    "school-district-secondary", "school-district-unified",
    "school-district-elementary", "township", "municipality",
    "judicial-subcircuit", "county-board", "ccbr", "fire-district",
    "dupage-county-special-police", "park-district", "library-district",
    "school-board", "cps-hs-network", "cps-network", "ward", "ward-precinct",
    "police-district", "police-beat", "ccpsa-district-council",
    "community-area", "zip-code", "cps-high", "cps-middle", "county-precinct",
    "tif-district", "cps-elementary", "school-site", "police-station",
    "fire-station", "post-office", "library", "early-voting",
]

# file -> (min features, max features) for the boundary layers fetched by the app.
GEOMETRY_FILES = {
    "adams-county-outline.json": (1, 1),  # Adams County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "alexander-county-outline.json": (1, 1),  # Alexander County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "bond-county-outline.json": (1, 1),  # Bond County outline — gap-location geometry only. Bond is served as a judicial-circuit secondary with no dispatch entry, so this ships purely so its 2026-08-08 board gap record attaches to ground the gaps panel can locate.
    "boone-county-outline.json": (1, 1),  # Boone County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "brown-county-outline.json": (1, 1),  # Brown County outline — the county IS served, but through the COUNTY card's board section rather than a dispatch entry: it elects its board at large, so there is no district geometry to dispatch on and index.html names no loader for this file. It is fetched by slug for the gaps panel, and it is what puts the county inside the coverage ring.
    "bureau-county-outline.json": (1, 1),  # Bureau County outline — gap-location geometry only, not a dispatched county: no layer answers here, but the gaps panel tests the pin against <slug>-county-outline.json, and without this file a pin in the gray-washed county was told 'nothing missing where you clicked'. Ships so bureau-county-board-districts attaches to its ground. (This note used to point at jo-daviess-county-outline.json as the pattern's exemplar; Jo Daviess was promoted to a dispatched county on 2026-08-17, so the explanation lives here now.)
    "calhoun-county-outline.json": (1, 1),  # Calhoun County outline — the county IS served, but through the COUNTY card's board section rather than a dispatch entry: it elects its board at large, so there is no district geometry to dispatch on and index.html names no loader for this file. It is fetched by slug for the gaps panel, and it is what puts the county inside the coverage ring.
    "carroll-county-board-districts.json": (3, 3),  # Carroll's 3 board districts, dissolved from TIGER townships per the county's published 2021 district map, whose lines run exactly along township boundaries (scripts/build_carroll_board_districts.py; --check runs monthly in validate-sources.yml). The county publishes no vector district data — its map is a raster export — but none was needed.
    "carroll-county-outline.json": (1, 1),  # Carroll County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "cass-county-board-districts.json": (4, 4),  # Cass County Board districts, DERIVED: Census 2020 voting districts dissolved per the county's own published district table (scripts/build_cass_board_districts.py; --check is the drift gate). Its GIS is a Beacon parcel viewer with no public REST. The table's 21 precinct names match TIGER's 21 exactly. The board seats ELEVEN members as 3/3/3/2, so the build balances per MEMBER (12.3% spread) — per district it reads 28.8% and looks broken.
    "cass-county-outline.json": (1, 1),  # Cass County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entry.
    "ccbr-districts.json": (3, 3),
    "champaign-county-outline.json": (1, 1),  # Gap-location outline for Champaign County — NOT a dispatched county. Its districts and precincts are live on the CCGISC portal but LICENSED (sold under signed agreement; the terms forbid copying, mirroring and public display), so no layer answers there. This outline exists solely so the champaign-piatt-ccgisc-license gap attaches to its ground.
    "christian-county-outline.json": (1, 1),  # Gap-location outline for Christian County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "clark-county-board-districts.json": (7, 7),  # Clark County's 7 single-member County Board districts, DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per a composition its own certified canvasses state THREE times over: the 2022 General canvass carries all seven contests over whole precincts (23 precincts, each in exactly one district), the 2024 General re-tabulates districts 3, 4 and 7, and the 2026 General Primary re-tabulates 1, 2, 5 and 6 — so every district is witnessed by a document later than 2022. County Clerk & Recorder Laura H. Lee stated in writing on 2026-08-18 that the board is elected by districts AND that the county has no map to supply, which is why this is the first county in the fleet whose boundaries come entirely from election returns. The seven populations sum to the county's exact 15,455 and run 1,923–2,674 against a one-member ideal of 2,208 — a 21.1% worst deviation that is the COUNTY'S apportionment, recorded rather than smoothed; the builder's ceiling exists to catch a mis-assignment, not to certify the plan. The weekly roster run re-reads the canvasses and fails if any district's precinct list stops matching this dissolve. Full re-verification is scripts/build_clark_boundaries.py --check (operator step: requests/shapely).
    "clark-county-outline.json": (1, 1),  # Clark County outline — the coverage test for the county's board and precinct dispatch entries (clarkCountyCoverage). Shipped 2026-08-04 as gap-location geometry when Clark read as source-less; promoted to a coverage outline on 2026-08-18 when the county joined as the 53rd dispatched county, so index.html now names it literally and it is no longer a dynamic reference.
    "calhoun-precincts.json": (5, 5),  # Calhoun County's five voting precincts — the seven Census 2020 voting districts DISSOLVED into the five the county runs today, which is a different shape from Clark's and needed a different gate. The county names the composition in the precincts' own titles (Belleview-Hamburg = BELLEVIEW + HAMBURG, Hardin-Gilead = HARDIN + GILEAD), and its certified returns either side of the 2022-2024 merge show each merged precinct's registration equal to the sum of its two named parts. Bounds are an EQUALITY because five is the county's whole precinct list. The Jasper test's name-for-name comparison is NOT the right gate here and would reject a fabric that has not moved; check_fabric_composed keeps the population identity while check_partition proves every voting district is claimed exactly once. NO BOARD DISTRICT ships and none ever will — Calhoun elects its five commissioners county-wide, so there is no district for a precinct to belong to. NO POLLING PLACE ships: the county publishes one, and it belongs with a roster guard and a date rather than inside a geometry file (scripts/build_calhoun_precincts.py).
    "clark-precincts.json": (23, 23),  # Clark County's 23 voting precincts — the Census 2020 voting districts, which ARE the county's own fabric and are measured to be: the names match the county's 23/23, their POP100 sums to its exact 2020 population (15,455), and the county's 2022 General, 2024 General and 2026 General Primary returns all tabulate the same 23 names, so nothing moved either side of the census. This is the test JASPER FAILS (five census Wade voting districts against four current county precincts). Bounds are an EQUALITY because the fabric is the county's whole precinct list. Each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct (no split). NO POLLING PLACE ships: the only list the county publishes is titled "Polling places and addresses 11-18" — the November 2018 election (scripts/build_clark_boundaries.py).
    "clay-county-outline.json": (1, 1),  # Clay County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "clinton-county-outline.json": (1, 1),  # Gap-location outline for Clinton County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "coles-county-outline.json": (1, 1),  # Coles County outline — the coverage test for the county's board and precinct dispatch entries (colesCountyCoverage). Shipped 2026-08-04 as gap-location geometry when Coles read as source-less; promoted to a coverage outline on 2026-08-17 when the county joined as the 52nd dispatched county, so index.html now names it literally and it is no longer a dynamic reference.
    "congress-districts.json": (18, 18),  # 17 IL U.S. House districts + a ZZ water pseudo-district; pre-built from TIGERweb by scripts/build_legislative_boundaries.py (R2-2)
    "cook-fire-districts.json": (40, 40),  # Cook's 40 suburban Fire Protection Districts, pre-built from the Clerk's L17 tax-agency tiling by scripts/build_parcel_fabric_districts.py — the 2026-08-16 fabric survey measured 102 empty road-band voids in the live layer. Road voids closed at 75 ft; the seven district pairs the Clerk's own tiling double-claims (Orland-Mokena is 57 acres) ship in both districts exactly as the live layer answers; a Loop click stays outside every FPD because Chicago runs its own fire department. No upstream edit stamp exists (the Clerk refreshes in place), so the builder pins count and names and validate_sources watches the service monthly.
    "crawford-county-board-districts.json": (5, 5),  # Crawford County's 5 County Board districts, each electing TWO members in staggered years, DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per the composition its certified 17 March 2026 General Primary results publish as STRUCTURED DATA: every district had a contest, and their precinct lists partition the county's 24 precincts exactly once each. A single certified election is accepted here and said so plainly — unlike Clark, nothing is transcribed, because the precincts listed in a contest are the precincts it was ON THE BALLOT in. Populations sum to the county's exact 18,679; worst deviation +20.2% from the per-district ideal, which is the COUNTY'S apportionment and is recorded rather than smoothed. The weekly roster run re-reads the composition from the Clerk's feed and fails if it moves; full re-verification is scripts/build_crawford_boundaries.py --check (operator step: requests/shapely).
    "crawford-county-outline.json": (1, 1),  # Crawford County outline — the coverage test for the county's board and precinct dispatch entries (crawfordCountyCoverage). Built 2026-08-18 when the county joined as the 54th dispatched county.
    "crawford-precincts.json": (24, 24),  # Crawford County's 24 voting precincts — the Census 2020 voting districts, which ARE the county's own fabric and are measured to be: the names match its 24 precinct names 24/24 and their POP100 sums to its exact 2020 population (18,679). Bounds are an EQUALITY because the fabric is the county's whole precinct list. Each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct — no precinct is split. NO POLLING PLACE ships: nothing the county publishes pairs precincts with buildings as data (scripts/build_crawford_boundaries.py).
    "cumberland-county-outline.json": (1, 1),  # Cumberland County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "dekalb-county-outline.json": (1, 1),  # DeKalb County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "dewitt-county-board-districts.json": (4, 4),  # De Witt County Board districts, DERIVED: the county's own precinct layer dissolved per the composition it prints for every board member (scripts/build_dewitt_board_districts.py; --check is the drift gate). The county publishes only a raster JPG. Checked three ways: the four districts partition all 23 precincts exactly, every name resolves in the live layer, and the resulting Census 2020 populations balance to 3.2% spread. Districts are LETTERED A-D.
    "dewitt-county-outline.json": (1, 1),  # De Witt County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "douglas-county-outline.json": (1, 1),  # Douglas County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "dupage-county-outline.json": (1, 1),
    "edgar-county-board-districts.json": (7, 7),  # Edgar County's 7 single-member County Board districts, DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per a composition THREE certified documents agree on — the first county the vendor sweep reached that meets Clark's two-witnesses-per-district standard in full. The 2022 General canvass tabulates all seven districts over all 31 precincts, each claimed exactly once; the 2024 General re-tabulates 1, 6 and 7; the 2026 General Primary re-tabulates 2, 3, 4, 5 and 6. Populations sum to the county's exact 16,866 and run 2,235-2,694 against a 2,409 ideal — worst deviation +11.8%, the tightest this route has produced, and still the COUNTY'S apportionment rather than a certification of it. The weekly roster run re-reads the composition from the Clerk's feed and fails if it moves; full re-verification is scripts/build_edgar_boundaries.py --check (operator step: requests/shapely).
    "edgar-county-outline.json": (1, 1),  # Edgar County outline — the coverage test for the county's board and precinct dispatch entries (edgarCountyCoverage). Built 2026-08-18 when the county joined as the 56th dispatched county, hours after Paris had been written into the coverage ring's OUTSIDE anchor list by Clark's join.
    "edgar-precincts.json": (31, 31),  # Edgar County's 31 voting precincts — the Census 2020 voting districts, which ARE the county's own fabric: 29 of the 31 names match its own spelling character for character, their POP100 sums to its exact 2020 population (16,866), and the two that differ (the census writes EMBARRASS 1 and KANSAS 1 where the county writes Embarrass and Kansas) PAIR UNIQUELY at 31 against 31 — recorded as a rename in the builder's CENSUS_SPELLING, with both names shipped on the feature so a reader searching either finds it. Bounds are an EQUALITY because the fabric is the county's whole precinct list. Each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct. NO POLLING PLACE ships: the county publishes none as data (scripts/build_edgar_boundaries.py).
    "franklin-county-board-districts.json": (3, 3),  # Franklin County's 3 County Board districts of THREE members each (staggered), DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per a composition THREE certified elections agree on EXACTLY — one better than Clark's two-witnesses-per-district standard. The 2024 General and the 2022 General each tabulate a board contest in every one of the county's 35 precincts, partitioning them 13/13/9 with each precinct claimed exactly once; the 2026 General Primary reproduces the same three sets and NAMES the districts in its contest headers, which corroborates the county members page's district key rather than resting on it. Populations sum to the county's exact 37,804 and run 11,172-14,044 against a 12,601 ideal — worst deviation +11.4%, the COUNTY'S apportionment rather than a certification of it. A SHORTCUT THAT LOOKED RIGHT AND WAS NOT: the results vendor's precinct ids group 51xx/61xx/71xx, which reads like a district key — Browning 1 and 3 sit in District 1 while Browning 2 sits in District 2, and the prefixes interleave across all three. The weekly roster run re-reads each district's precinct COUNT from the Clerk's newest board election and fails if it moves (scripts/build_franklin_boundaries.py; --check is the drift gate).
    "franklin-precincts.json": (35, 35),  # Franklin County's 35 voting precincts — the Census 2020 voting districts, which ARE the county's own fabric: 34 of the 35 names match its own spelling character for character, their POP100 sums to its exact 2020 population (37,804), and the one that differs (the census writes CAVE 1 where the county writes Cave) pairs uniquely at 35 against 35 — the vestigial-1 rule, recorded in the builder's CENSUS_SPELLING with both names shipped on the feature. Bounds are an EQUALITY because the fabric is the county's whole precinct list. Each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct. NO POLLING PLACE ships: the county publishes no precinct-to-building pairing as data (scripts/build_franklin_boundaries.py).
    "clinton-county-board-districts.json": (5, 5),  # Clinton County's 5 County Board districts of THREE members each, DISSOLVED from the Census 2020 voting districts per a composition THREE certified elections agree on: the 2024 General and the 2026 General Primary each carry a numbered 'FOR COUNTY BOARD DISTRICT n' contest in every one of the county's 34 precincts and partition them 7/9/6/5/7, and the 2022 General names candidates whose districts key onto the county's own board page — so the oldest election corroborates the two numbered ones from a different direction. A COMPOSED FABRIC, not a one-to-one one (the Calhoun shape, hence check_fabric_composed): census 2020 carries 39 Clinton voting districts against the 34 the county runs today, Irishtown/Lake/St Rose having each merged a numbered pair and Brookside gone from five to three. The first three merges are nameable and the fourth is NOT — and it cannot matter, because all five Brookside voting districts sit in District 1, so no merge can move a district line. Populations sum to the county's exact 36,899 and run 6,840-7,678 against a 7,380 ideal — worst deviation 7.3%, THE TIGHTEST THIS ROUTE HAS PRODUCED and the strongest evidence available that this is the county's current map rather than a stale one (Wayne, measured the same afternoon on the identical technique, came out at 32.4% and was NOT built). Each feature names the county's own 34 current precincts, not the 39 census units the geometry is built from (scripts/build_clinton_boundaries.py; --check is the drift gate).
    "warren-county-board-districts.json": (4, 4),  # Warren County's 4 County Board districts (seating 15, as 3/4/4/4), DISSOLVED from the Census 2020 voting districts per a composition THE COUNTY ITSELF PUBLISHES. Its precinct map is a raster image with no vector linework, so nothing is traced from it — but the map's TEXT LAYER carries a four-column table at the foot of the page, each column headed by a district and listing that district's precincts. That is Warren stating its own composition in machine-readable form, which is a STRONGER source than the election-returns route used for Franklin and Clinton, where the same fact is inferred from which ballot each precinct voted. A COMPOSED FABRIC and the cleanest this route has met: census 2020 carries 28 Warren voting districts against the 26 precincts the county runs today, and BOTH merges are nameable AND confined to one district — ROSEVILLE 1 + ROSEVILLE 2 in District 4, SPRING GROVE-ALEXIS + SPRING GROVE-GERLAW in District 3 — so neither can move a district line. That is the Clinton test passed twice over, where Clinton had one unnameable merge that merely happened to sit inside a single district. Populations sum to the county's exact 16,835 and run 4,030-4,332 against a 4,209 ideal — worst deviation 4.2%, THE TIGHTEST THIS ROUTE HAS PRODUCED, taking the record from Clinton's 7.3% hours later. Each feature names the county's own current 26 precincts, not the 28 census units the geometry is built from (scripts/build_warren_boundaries.py; --check is the drift gate).
    "edwards-county-outline.json": (1, 1),  # Edwards County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "effingham-county-outline.json": (1, 1),  # Effingham County outline — the coverage test for the county's five dispatch entries (board/precinct/fire/park/library), and the FIRST ISLAND: joined detached on 2026-08-04 under the retired-contiguity policy, so metro-outline.json is now a MultiPolygon. Shipped as a gap-location outline by pass 13 and promoted in the same week.
    "fayette-county-outline.json": (1, 1),  # Gap-location outline for Fayette County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "ford-county-outline.json": (1, 1),  # Gap-location outline for Ford County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "franklin-county-outline.json": (1, 1),  # Franklin County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "fulton-county-outline.json": (1, 1),  # Fulton County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "gallatin-county-outline.json": (1, 1),  # Gallatin County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "greene-county-outline.json": (1, 1),  # Greene County outline — gap-location geometry only. Greene is served as a judicial-circuit secondary with no dispatch entry, so this ships purely so its 2026-08-08 board gap record attaches to ground the gaps panel can locate.
    "grundy-county-board-districts.json": (3, 3),  # Grundy County Board districts, DERIVED: the county's own precinct layer dissolved per the adopted 'Approved County Board Districts (10/12/2021)' map (scripts/build_grundy_board_districts.py; --check is the drift gate). The transcription is proven by the map's printed populations — all three district totals to the person.
    "grundy-county-outline.json": (1, 1),  # Grundy County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "hamilton-county-outline.json": (1, 1),  # Hamilton County outline — the coverage test for the county's precinct and fire dispatch entries, and the SECOND island (pass 14, 2026-08-05): the ask campaign's first fruit, joined the day the Clerk answered. Shipped as a gap-location outline by pass 13 and promoted the next day.
    "hancock-county-outline.json": (1, 1),  # Hancock County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "hardin-county-outline.json": (1, 1),  # Hardin County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "henderson-county-outline.json": (1, 1),  # Henderson County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "henry-county-board-districts.json": (2, 2),  # Henry County Board districts, DERIVED: TIGER townships dissolved per adopted Ordinance 21-33 (scripts/build_henry_board_districts.py; --check is the drift gate). The county publishes no board GIS — its viewer is Sidwell Portico, parcels + townships only. The 12+12 composition is proven by the adopted map's own two-census population table (all four printed district totals to the person) and by live Census POP100 on every run.
    "henry-county-outline.json": (1, 1),  # Henry County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "henry-precincts.json": (52, 52),  # Henry's 52 voting precincts, each with the county's own readable name ("Geneseo 1") and its four-digit code. Bounds are an EQUALITY because the export is the county's whole fabric, counted: nothing here is derived or sampled. The county publishes NOTHING usable — around 21 per-township picture maps from November 2021, no precincts in its mapping system, and no public ArcGIS under any henrycty.com hostname (re-probed 2026-08-06) — so this is a shapefile Henry County GIS (Bruce Lang) sent by e-mail 2026-08-06 after the Clerk forwarded the request internally, archived under data/source/raw/ and reprojected from EPSG:3436 by scripts/build_henry_precincts.py. That builder proves the reprojection rather than trusting it: the rebuilt extent must land within 0.01 deg of the county outline the app already ships (it lands within 0.00004), the precincts must tile at least 99.5% of the county (99.95) and no pair may overlap by more than 0.05% (0.0000). It also caught a real defect in the county's file: Geneseo 6 carries a ~0.01 m2 sliver ring that made the old "inside another ring means hole" test classify BOTH of that precinct's real rings as holes, building it empty — the rule now requires the containing ring to be strictly larger. PERMISSION TO PUBLISH WAS ASKED TWICE AND NEVER ANSWERED, and that is recorded here rather than rounded off, because the gap record it used to live in closed when the polling join shipped. Bruce Lang declined the question as the Clerk's ('The other questions are for Barb to answer/supply'), and Clerk Link's 11 Aug reply addressed the data and not the permission. She was told in writing that the 52 precincts were live and offered immediate removal, and replied without asking for removal. That is NO OBJECTION STATED. It is not consent and is not written down as consent; a third ask would be badgering. The position stands on what it actually is: a public record supplied on request, no raw file redistributed, Henry County GIS credited on the card, and an open offer to take the boundaries down on one line from either office.
    "il-house-districts.json": (119, 119),  # 118 IL House districts + ZZ; pre-built from TIGERweb layer 2
    "il-senate-districts.json": (60, 60),  # 59 IL Senate districts + ZZ; pre-built from TIGERweb layer 1
    "il-supreme-court-districts.json": (5, 5),
    "iroquois-county-outline.json": (1, 1),  # Iroquois County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "jackson-county-outline.json": (1, 1),  # Jackson County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "jasper-county-outline.json": (1, 1),  # Jasper County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "jefferson-county-board-districts.json": (13, 13),  # Jefferson County Board districts, DISSOLVED from the county's own precincts per the county's own approved list. Jefferson publishes no boundary of any kind; asked for districts AND precincts, County Clerk Joe Davis sent the precinct shapefile on 2026-08-06 and, re-asked on the cheaper basis the gap record had named, sent "County Board Districts (Approved by County Board November 22, 2021)" on 2026-08-07 — one line per district naming its precincts. scripts/build_jefferson_board_districts.py applies that list and asserts it accounts for all 33 precincts exactly once, that the 13 districts reproduce the county's own extent (0.0000%), and that no district dissolves with more than 0.05% of its area in slivers. ONE PRECINCT IS SPLIT: Shiloh 4, west/east of 34th Street, between Districts 10 and 11. The cut longitude comes from TIGER/Line (public domain) and is corroborated by OSM rather than taken from it, because a shipped civic boundary derived from ODbL data would carry share-alike obligations this project has not taken on. 34th Street stops about three quarters of the way up the precinct; north of that the cut is the street's alignment projected, which is the one inference in the file, and Districts 10 and 11 carry a boundaryNote saying so. Asked on 2026-08-07 where the line runs past the pavement, Clerk Davis answered on 2026-08-10 by pointing at the county's PUBLISHED PRECINCT LEGAL DESCRIPTIONS — which establish that "34th Street" is a boundary the county draws (Shiloh 3 is "south of Broadway and east of 34th Street") and put the county's own Shiloh 3 edge within about seven metres of the TIGER longitude used here, but do not say where the line goes once the street ends. The cut is therefore unmoved and the boundaryNote is unretired; it now names the published descriptions instead of an outstanding ask. TWO MORE ARTIFACTS AT THAT CUT WERE FIXED 2026-08-10, both drawing as a line standing inside District 10 and each with its own cause. A 9 m wide, 408 m tall slice of Shiloh 4 fell east of the TIGER meridian but SOUTH OF BROADWAY, where the county's own description says there is no Shiloh 4 east of 34th Street at all (that ground is Shiloh 3) — District 11 territory standing inside District 10, now returned to the west side by testing each stranded part against Shiloh 3's own northern edge. And a 7 m wide, 190 m deep slot between Shiloh 3 and Shiloh 4, both walls District 10, which resolve_tiling's reach rule declined because the slot's mouth opens onto the District 5 township line and that rule is blind to shape; pass 2b adds the shape test, giving a crack to the district holding 90% of its outline. Inter-district cracks in this county score 50-58% and surrounded ones 87% or more, so the threshold is nowhere near anything. District 10 finished at 14 vertices, from 129. AND ROUND FOUR: four clicks near district borders answered that the point was not inside any district in this layer, all four in inter-district hairlines the reach rule leaves unowned by design. 0.0235% of the county, one click in four thousand, and a false answer every time — the point IS in a district, the county's file merely has a crack there, which is the same sentence that justifies closing these one layer down. Closed at both layers now (close_reopened() in the precinct builder, pass 2b here): a crack goes whole to the district holding most of its outline, or is split at 40 m per side when it is one of the two lattices spanning 9 and 14 km. Both files tile 100.0000% of Jefferson. THE DISSOLVE IS ALSO REPAIRED, from 2026-08-10, after a reader reported strange artifacts in these boundaries: they were real. A plain union of the precincts left 108 SLIVER HOLES (the worst 7,545 m long and 124 m wide, inside District 8; District 7 had 64 along one township line), and a hole is stroked, so each drew a dark line across a filled district. It also left five spurious parts — Districts 5 and 7 rendered as two disconnected blocks each because a crack ran the full width between two of their own precincts — and 28 overlapping pairs, worst 33,126 m2, pooled from the county's own overlapping precincts. The cause is upstream: build_jefferson_precincts.py simplifies each precinct independently AFTER repairing the county's cracks, and Douglas-Peucker is deterministic only on identical input, so shared edges diverge. That file is deliberately NOT re-cut — its residue is measured, asserted, byte-stable and now checked against the county's published descriptions — so resolve_tiling() repairs the dissolve instead: double-claimed ground to the lower-numbered district, unowned cracks to the district that is the only one within 150 m, then enclosed rings filled and sub-5,000 m2 dust dropped, every step with a ceiling asserted. Result is 13 districts, 13 parts, 0 sliver holes, worst overlap 74 m2 (rounding), tiling 99.988% of the county. Jefferson is the only dissolve in the fleet that needs this; every other county-board file built this way has holes of at most 191 m2, because their precincts arrived edge-matched.
    "jefferson-county-outline.json": (1, 1),  # Jefferson County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "jefferson-precincts.json": (33, 33),  # Jefferson's 33 voting precincts, named as the county names them (Grand Prairie, Rome 1/2, Mt V 1-10, Shiloh 1-5, …). Bounds are an EQUALITY because the export is the county's whole fabric. Jefferson publishes NO boundary of any kind — its site is up and its board page lists sixteen member e-mail addresses, but nothing geographic — so this is a shapefile County Clerk Davis sent on request 2026-08-06, archived under data/source/raw/ and reprojected from EPSG:3435 (Illinois EAST, where Henry's is WEST) by scripts/build_jefferson_precincts.py. THAT BUILDER ALSO REPAIRS THE FILE, which is unusual and is why its docstring is long: the county's polygons are not edge-matched, so they tile only 99.212% of the county, the shortfall being one CONNECTED LATTICE of sub-31 m cracks running along nearly every shared boundary. Each crack is given to the precinct whose boundary is nearest (Voronoi over densified boundaries), then simplified to undo the vertex explosion that assignment causes — 99.949% coverage, median boundary shift 34 m, worst 153 m, all asserted. close_reopened() then gives the cracks that simplification reopens back to the precinct around them, so the shipped file tiles 100.0000% rather than 99.949%. THE TOLERANCE WAS 10 m UNTIL 2026-08-10 AND WAS ON THE WRONG SIDE OF A CLIFF: 10 m cannot remove a zig-zag whose amplitude is the 30 m Voronoi sampling step, so all 3,057 zig-zag vertices survived — invisible here, because a hairline between two precincts draws as nothing, and glaring in the board districts these dissolve into, where a reader reported them. 15 m leaves 31 of them for the same median shift and the same worst shift at a sixth of the vertices; an explicit despike() pass then removes the isolated spikes simplification keeps by construction (a vertex far off the chord between its neighbours WHEN they are close together, which is what separates a spike from a real corner) — 50 vertices, 0.008% of the county — including one 33 m south of a straight township line, on ground the county's raw file never drew. The county's own small Dodds 1 / Dodds 2 OVERLAP is deliberately left alone: a crack has no owner and can be assigned, two claims on the same ground cannot. SINCE 2026-08-10 THE SHAPES ARE CHECKED AGAINST A PUBLISHED SOURCE: Clerk Davis pointed at the county's precinct LEGAL DESCRIPTIONS page, which says in words where each precinct is, and check_legal_descriptions() asserts all 33 land in the congressional township their description declares (the grid quartered off the county outline, not off the precincts, so a swap among the whole-township ones cannot redefine the grid and pass), that 28 side-of-a-named-line claims hold, and that the three described section splits divide their township in the published proportion. Every one of the 528 possible name swaps in the export fails it.
    "jersey-county-outline.json": (1, 1),  # Jersey County outline — gap-location geometry only. Jersey is served as a judicial-circuit secondary with no dispatch entry, so this ships purely so its 2026-08-08 board gap record attaches to ground the gaps panel can locate.
    "jo-daviess-county-board-districts.json": (17, 17),  # Jo Daviess County's 17 single-member County Board districts — the county's OWN shapefile, and the fleet's first PURCHASED boundary: 14 of the 17 districts cut across precincts along roads (the county's 2 Dec 2021 mapping memo), so no dissolve or tracing could draw them, and the export was bought under Jo Daviess County GIS Digital Data License Agreement #008382 ($33.50, 2026-08-17) with display on chidistricts.com authorized in writing by IT/GIS Director Joe Kratcha the same day. The licence's redistribution clause is why the RAW shapefile is NOT in data/source/raw — it is retained offline, and scripts/build_jodaviess_board_districts.py records each component's byte size and sha256 so a re-supplied copy can be authenticated. Bounds are an EQUALITY (CtyBrdDist DISTRICT 01..17 each exactly once, guarded; the dbf's CtyBrdMemb column is declared-and-empty and read NOWHERE — the builder fails if it ever fills, because members come from the county's board page weekly). Reprojected from the .prj's EPSG:3436 and simplified topology-aware (pinned mapshaper, -clean either side): the full-precision export tiles TIGER's county at 99.93% with 0.3 m2 worst pairwise overlap, the shipped file at 99.93% with zero overlap, median boundary movement ~0.6 m (max ~54 m), 2000/2000 sample points classifying identically. The licence's Credits clause is why the card names Jo Daviess County GIS on every render.
    "jo-daviess-county-outline.json": (1, 1),  # Jo Daviess County coverage outline — gates the county's dispatch entry. Shipped 2026-08-02 as gap-location geometry (the gaps panel tests pins against <slug>-county-outline.json); promoted 2026-08-17 to the dispatched county's coverage test when Jo Daviess joined as the 51st, referenced by loadJoDaviessCountyOutline in index.html. The board-district builder asserts its district union stays within 0.25% of this outline, so the coverage test and the card cannot disagree about where the county is.
    "johnson-county-outline.json": (1, 1),  # Johnson County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "kane-county-outline.json": (1, 1),
    "kane-judicial-subcircuits.json": (4, 4),  # 16th-Circuit subcircuits, pre-built from the PA 102-0693 enacted shapefile
    "kankakee-county-outline.json": (1, 1),  # Kankakee County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "kendall-county-outline.json": (1, 1),
    "kendall-fire-districts.json": (10, 10),  # Kendall's 10 FPDs, pre-built from the county's parcel-derived tax-code tiling (170 rows dissolved by name; scripts/build_parcel_fabric_districts.py). The 2026-08-16 fabric survey measured 977 empty road-band voids in the raw fabric - the 'hairline no-result gaps' the old note admitted, quantified. Voids closed at 75 ft; the municipal CITY OF JOLIET FIRE DISTRICT rows the old runtime loader filtered are excluded at build time.
    "kendall-library-districts.json": (9, 9),  # Kendall's 9 library taxing bodies (145 tax-code rows dissolved by name), pre-built with road voids closed - 1158 empty voids measured in the raw fabric. The municipal Joliet/Yorkville city-library funds STAY, the Cook-style complete shape the guidebook records.
    "kendall-park-districts.json": (5, 5),  # Kendall's 5 park districts (65 tax-code rows dissolved by name), pre-built with road voids closed - 578 empty voids measured in the raw fabric.
    "knox-county-outline.json": (1, 1),  # Gap-location outline for Knox County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "lake-county-outline.json": (1, 1),
    "lasalle-county-board-districts.json": (29, 29),  # LaSalle's 29 board districts (2022-2031 map, Resolution #21-126), DERIVED: the county's own precinct layer dissolved per the district assignment its Nov 2024 + Mar 2026 election canvasses administer (scripts/build_lasalle_board_districts.py; --check runs monthly in validate-sources.yml — it needs the county's precinct service and shapely). The county's published board GIS is the superseded 2011-2021 map; 11 split precincts are drawn with their majority side and the card says so.
    "lasalle-county-outline.json": (1, 1),  # LaSalle County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "lawrence-county-outline.json": (1, 1),  # Lawrence County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "lee-county-outline.json": (1, 1),  # Lee County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "livingston-county-board-districts.json": (3, 3),  # Livingston County Board districts, DERIVED: TIGER townships dissolved per the county's own published composition (scripts/build_livingston_board_districts.py; --check is the drift gate). The county publishes no GIS, so this file IS the boundary source, not a cache of one.
    "livingston-county-outline.json": (1, 1),  # Livingston County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "logan-county-outline.json": (1, 1),  # Logan County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "macon-county-outline.json": (1, 1),  # Gap-location outline for Macon County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "macon-fire-districts.json": (17, 17),  # Macon's 17 fire districts, pre-built from the county's AGOL Fire layer by scripts/build_parcel_fabric_districts.py. Upstream is parcel-join-derived and kept every road void - 1318 empty road-band voids measured 2026-08-16 at full precision, the fleet's worst. Names ship EXACTLY as the county writes them (the macon-district-name-formatting posture); the upstream edit date is pinned in the builder.
    "macon-library-districts.json": (10, 10),  # Macon's 10 library districts, pre-built with road voids closed - 960 empty voids measured in the raw LibraryJoin_Dissolved layer (dissolved by name upstream, but from a parcel join that kept the voids). Names verbatim (HopeWelty, MtZion); edit date pinned.
    "macon-park-districts.json": (6, 6),  # Macon's 6 park districts, pre-built with road voids closed - 556 empty voids measured in the raw ParkJoin_Dissolve layer. Names verbatim; edit date pinned.
    "macoupin-county-outline.json": (1, 1),  # Macoupin County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "madison-county-outline.json": (1, 1),  # Madison County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "madison-judicial-subcircuits.json": (4, 4),  # 3rd Circuit (Madison + Bond) subcircuits, PA 102-0693 enacted map.
    "marion-county-outline.json": (1, 1),  # Marion County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "marshall-county-board-districts.json": (3, 3),  # Marshall County Board districts, DERIVED: Census townships dissolved per the composition the county prints in the DISTRICT #n headings of its own board roster PDF (scripts/build_marshall_board_districts.py; --check is the drift gate). The county runs no public GIS. No township is split, so every district edge is a township edge; the build asserts the three districts partition all 12 townships exactly and that their Census 2020 populations balance (1.4% spread across three equal four-member districts).
    "marshall-county-outline.json": (1, 1),  # Marshall County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entry.
    "mason-county-board-districts.json": (2, 2),  # Mason County Board districts, DERIVED: Census townships dissolved per the two composition lines the county prints under its board roster (scripts/build_mason_board_districts.py; --check is the drift gate). Its only mapping surface is a WTH parcel viewer with no feature service. No township is split, so every district edge is a township edge; the build asserts the two districts partition all 13 townships exactly and that their Census 2020 populations balance (0.2% spread — 6,528 against 6,558 — across two equal four-member districts).
    "mason-county-outline.json": (1, 1),  # Mason County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entry.
    "massac-county-outline.json": (1, 1),  # Massac County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "mcdonough-board-districts.json": (3, 3),  # McDonough's 3 county board districts, seven members each. DERIVED by scripts/build_mcdonough_board_districts.py: the 27 precincts above dissolved per the composition the county board page prints under each district heading, verified to be a perfect partition (4+12+11) before anything is unioned. The county DOES publish a board-district layer, but its attribute table is corrupt — two districts share an identical population and acreage to eight decimals, the third has neither — so that layer is used only as a geometric cross-check, which the derivation passes at better than 0.999 IoU on all three.
    "mcdonough-county-outline.json": (1, 1),  # McDonough County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "mcdonough-precincts.json": (27, 27),  # McDonough's 27 voting precincts, each carrying its own polling place and address (27/27). Built by scripts/build_mcdonough_precincts.py from the WIU GIS Center's precinct_map layer 4 via /identify — the layer is a JOIN whose /query returns attributes with the geometry silently omitted, and identify ignores outSR, so the polygons are reprojected here from EPSG:3436 rather than by the server. Bounds are an EQUALITY, not a floor: the board-district composition names all 27 exactly once, so any other count means the fabric changed and the districts must be re-derived first.
    "mchenry-county-outline.json": (1, 1),
    "mchenry-judicial-subcircuits.json": (4, 4),  # 22nd-Circuit subcircuits, pre-built from the PA 102-0693 enacted shapefile
    "mclean-county-outline.json": (1, 1),  # McLean County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "menard-commissioner-districts.json": (5, 5),  # Menard County's 5 commissioner districts, the COUNTY'S OWN BEACON EXPORT and the cleanest county file this campaign has received: zero invalid geometries, zero self-overlap, and ZERO internal cracks — properly edge-matched, which neither Jefferson's nor Montgomery's file was. Menard publishes no boundary (its only map is a 2021-12 raster on the state's site) and its district lines follow SECTION-LINE ROADS rather than precinct edges, so the dissolve route that built Jefferson was unavailable here — the export was the only way. Obtained through three offices in four days: asked County Clerk & Recorder Martha Gum 3 Aug, who looped in Supervisor of Assessments Dawn Kelton, who requested it from Beacon and forwarded it 7 Aug. scripts/build_menard_commissioner_districts.py proves it against the Census on every run: the districts' POP20 values sum to 12,297, exactly Menard's 2020 count. The .prj is GEOGRAPHIC NAD83 (EPSG:4269), not a state plane like every other county file here, so the transform is a datum shift rather than a projection. Districts carry the county's own names — Rock Creek, East Menard, Northwest Menard, Southwest Menard, South Petersburg.
    "menard-county-outline.json": (1, 1),  # Gap-location outline for Menard County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "mercer-county-board-districts.json": (5, 5),  # Mercer County's 5 County Board districts, each electing TWO members in staggered years, DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per the composition its certified 17 March 2026 General Primary results publish as STRUCTURED DATA: every district had a contest, and their precinct lists partition the county's 24 precincts exactly once each. A single certified election is accepted here and said so plainly — unlike Clark, nothing is transcribed, because the precincts listed in a contest are the precincts it was ON THE BALLOT in. Populations sum to the county's exact 15,699; worst deviation -14.6% from the per-district ideal, which is the COUNTY'S apportionment and is recorded rather than smoothed. The weekly roster run re-reads the composition from the Clerk's feed and fails if it moves; full re-verification is scripts/build_mercer_boundaries.py --check (operator step: requests/shapely).
    "mercer-county-outline.json": (1, 1),  # Mercer County outline — the coverage test for the county's board and precinct dispatch entries (mercerCountyCoverage). Built 2026-08-18 when the county joined as the 55th dispatched county.
    "mercer-precincts.json": (24, 24),  # Mercer County's 24 voting precincts — the Census 2020 voting districts, which ARE the county's own fabric and are measured to be: the names match its 24 precinct names 24/24 and their POP100 sums to its exact 2020 population (15,699). Bounds are an EQUALITY because the fabric is the county's whole precinct list. Each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct — no precinct is split. NO POLLING PLACE ships: nothing the county publishes pairs precincts with buildings as data (scripts/build_mercer_boundaries.py).
    "metro-outline.json": (1, 1),  # Coverage outline of every served county, dissolved from TIGERweb by scripts/build_metro_outline.py; drives the out-of-scope wash. Kept to ONE connected region — a county joins only once it touches the served area.
    "monroe-county-outline.json": (1, 1),  # Monroe County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "montgomery-county-board-districts.json": (7, 7),  # Montgomery County Board districts, the COUNTY'S OWN GIS EXPORT — nothing derived and nothing traced, which is rare for a county this size. Montgomery publishes no boundaries (its GIS page links a Beacon/Schneider parcel viewer), so this is an ESRI FILE GEODATABASE that Kevin Brink of Montgomery County GIS sent by e-mail 2026-08-06, archived under data/source/raw/ and reprojected from EPSG:3436 by scripts/build_montgomery_boundaries.py. The .gdb is the fleet's first — read through GDAL's /vsizip/ handler with pyogrio, straight out of the archived zip. THE LAYER IS NAMED CountyBoardDistricts_2010 AND IS NOT STALE, which the builder proves two ways on every run: the districts' Pop100 values sum to 28,210 and District 4's own comment backs out 1,894 for Graham Correctional Center, so the raw sum is 30,104 — exactly Montgomery's 2010 census count, meaning _2010 names the POPULATION vintage; and the geometry reproduces the county's published 'Districts After Redistricting 2020-2030' chart exactly, all 38 precincts including the five it splits between two districts. That composition assertion is the real gate: a future export that moves a boundary enough to change a precinct's district fails the build.
    "montgomery-county-outline.json": (1, 1),  # Gap-location outline for Montgomery County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "montgomery-precincts.json": (38, 38),  # Montgomery's 38 voting precincts, named as the county names them (Audubon, Bois D'Arc, Hillsboro 1-6, North Litchfield 1-6, ...) and each carrying the county's five-digit VOTE00 code. Bounds are an EQUALITY because the export is the county's whole fabric. Same source and same builder as the board districts above — one geodatabase, one ask, one script, because the two layers CROSS-CHECK each other against the county's published composition chart. SHIPPED AS DRAWN, no repair: like Jefferson's, the polygons are not edge-matched, but at a completely different scale — 184 hairline cracks totalling 0.0034% of the county (about one click in 29,000) against Jefferson's 0.788% (one in 127), which is several times cleaner than Jefferson ended up AFTER its Voronoi repair. Repairing here would move real boundaries to buy nothing; MAX_INTERNAL_HOLES_PCT fails the build if a future export is genuinely broken.
    "morgan-county-outline.json": (1, 1),  # Morgan County outline — gap-location geometry only. Morgan is served as a judicial-circuit secondary with no dispatch entry, so this ships purely so its 2026-08-08 board gap record attaches to ground the gaps panel can locate.
    "moultrie-county-outline.json": (1, 1),  # Moultrie County outline — NOT a dispatched county: its board is elected AT LARGE, so it has no district geometry and its members ride the County card via il-county-commissioners.json. The outline exists so the county's recorded gaps attach to ground in the data-gaps panel; referenced by slug-built URL, so the validator's literal-reference check skips it (scripts/build_county_outline.py).
    "municipal-ward-coverage.json": (50, 70),  # Ward-electing municipalities' outlines, tagged by dispatch entry — the cheap same-origin coverage test for every non-Chicago entry of the ward layer, metro or not (build_municipal_ward_coverage.py; Rockford is the first outside the metro, Moline and Silvis the first on the Mississippi, Mendota the first whose seats were already in the roster before its geometry was). 56 municipalities across twenty-one entries after the pass-6 ward tranche (2026-08-02) added thirteen sources / twenty-two cities.
    "ogle-county-board-districts.json": (8, 8),  # Ogle's 8 board districts, dissolved from Census 2020 voting districts per the composition its reapportionment resolution R-2021-1106 adopts (scripts/build_ogle_board_districts.py; --check runs monthly in validate-sources.yml, alongside Livingston's, because it needs TIGERweb and a network call on every PR is a flake waiting to happen). The county publishes no district geometry.
    "ogle-county-outline.json": (1, 1),  # Ogle County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "ogle-precincts.json": (51, 51),  # Ogle's 51 CURRENT voting precincts, each with its township. The county publishes no precinct boundaries — a 51-page PDF map book and a points-only polling dataset — so this comes from a shapefile the county's GIS Coordinator sent by e-mail 2026-08-03, archived under data/source/raw/ and reprojected from EPSG:3436 by scripts/build_ogle_precincts.py. Bounds are an EQUALITY because the count is the substance of the answer: the app already had the 2020 Census versions (the board districts are dissolved from them) but that was the 52-precinct fabric, and shipping it would have put the retired Forreston 3 on a card. The County Clerk supplied the missing half in one line — Forreston 1 and 2 became Forreston 1, Forreston 3 became 2 — which the builder asserts against the data rather than trusting.
    "peoria-county-outline.json": (1, 1),  # Peoria County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "perry-county-outline.json": (1, 1),  # Perry County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "piatt-county-outline.json": (1, 1),  # Gap-location outline for Piatt County — NOT a dispatched county. Its districts and precincts are live on the CCGISC portal but LICENSED (sold under signed agreement; the terms forbid copying, mirroring and public display), so no layer answers there. This outline exists solely so the champaign-piatt-ccgisc-license gap attaches to its ground.
    "pike-county-outline.json": (1, 1),  # Pike County outline — the county IS served, but through the COUNTY card's board section rather than a dispatch entry: it elects its board at large, so there is no district geometry to dispatch on and index.html names no loader for this file. It is fetched by slug for the gaps panel, and it is what puts the county inside the coverage ring.
    "pope-county-outline.json": (1, 1),  # Pope County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "pulaski-county-outline.json": (1, 1),  # Pulaski County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "putnam-county-outline.json": (1, 1),  # Putnam County outline — the county IS served, but through the COUNTY card's board section rather than a dispatch entry: it elects its board at large, so there is no district geometry to dispatch on and index.html names no loader for this file. It is fetched by slug for the gaps panel, and it is what puts the county inside the coverage ring.
    "randolph-county-outline.json": (1, 1),  # Randolph County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "richland-county-outline.json": (1, 1),  # Richland County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "rock-island-county-outline.json": (1, 1),  # Rock Island County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries. The first served county on the Mississippi; building it forced permalink_gate.minLng west of -91.
    "rock-island-fire-districts.json": (17, 17),  # Rock Island's 17 fire protection districts, pre-built from the county's TaxDistricts tax-agency tiling by scripts/build_parcel_fabric_districts.py. The tiling is dissolved from the PARCEL fabric and road right-of-way carries no parcel, so served raw every district was a lattice of fragments split by 37-107 ft voids; the builder closes those voids at 75 ft (nothing farther than 75 ft from county-published ground is ever claimed), ships ground both neighbours' closings reach in NEITHER district, and re-verifies road-void and unserved-ground probes before writing. Bounds are an EQUALITY: the county levies exactly these 17.
    "rock-island-library-districts.json": (9, 9),  # Rock Island's 9 named library districts, pre-built from the county's TaxDistricts tiling with parcel-fabric road voids closed (same builder and rules as the fire file). The source's blank-named tenth row - a byte-identical stray copy of the UNITED TWP HIGH 30 school polygon, which overlaps Rock River and River Valley and fully contains Hampton - is asserted present and excluded at build time. Moline and Rock Island city correctly sit in NO district: both run municipal libraries on a city levy, and Andalusia Township's library is the recorded rock-island-andalusia-township-library gap.
    "rock-island-park-districts.json": (1, 1),  # Rock Island's single levied park district (Cordova), pre-built from the county's TaxDistricts tiling with road voids closed (same builder as the fire and library files). A one-feature file is honest rather than thin: everywhere else in the county genuinely sits in no park district.
    "saline-county-outline.json": (1, 1),  # Saline County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "sangamon-county-outline.json": (1, 1),  # Sangamon County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "sangamon-judicial-subcircuits.json": (7, 7),  # 7th Circuit (Sangamon + Greene/Jersey/Macoupin/Morgan/Scott) subcircuits, PA 102-0693 enacted map.
    "school-board-districts.json": (20, 20),
    "scott-county-outline.json": (1, 1),  # Scott County outline — gap-location geometry only. Scott is served as a judicial-circuit secondary with no dispatch entry, so this ships purely so its 2026-08-08 board gap record attaches to ground the gaps panel can locate.
    "shelby-county-board-districts.json": (11, 11),  # Shelby County Board districts, DISSOLVED from Census 2020 voting districts per the composition the county publishes — the DeWitt shape at its most verified, and the build that ended the shelby-county-board gap Clerk Jessica Fox's 2026-08-11 reply de-risked. Shelby publishes no board GIS; its adopted plan is a vector PDF (Bruce Harris & Associates, November 2021) whose 33 precincts TIGER's VTD layer carries EXACTLY — 33/33 by name, 31/33 by population to the person, the two exceptions being each other's inverse (a ~16-person sliver the plan moved across the Shelbyville 4/5 edge relative to the census snapshot). ONE PRECINCT IS SPLIT THREE WAYS: Shelbyville 5, which wraps the county seat, goes to District 8 south of Rt 16, District 9 north of it east of Lake Shelbyville, District 10 north-west of the lake — the county's own wording on coboard.aspx. The cut instruments are public geometry: the Rt 16 corridor from TIGER secondary roads (its in-town Main Street names included; through downtown the median of the route's twin strands), and the lake from TIGER areal hydrography with the Kaskaskia River carrying the divider below the lake's tip, bridged straight through the ~1.4 km dam reach TIGER maps no linear river for. scripts/build_shelby_board_districts.py verifies the cut at CENSUS-BLOCK level — the three pieces' block sums are asserted EXACTLY (605/158/55; the one populated dam-reach block must land west, because the county's own 55 = 54 + 1) — and the eleven districts against the plan's printed populations: nine match to the person, Districts 8/11 carry the sliver at its exact ±16, the total is the county's exact 20,990, and the file tiles the VTD union to within 2.4 m2 of rounding hairline. Districts 8/9/10/11 carry boundaryNotes disclosing the split approximations and the sliver. The weekly roster job re-parses the composition — split pieces included — so a redistricting fails CI (the DeWitt pattern).
    "shelby-county-outline.json": (1, 1),  # Shelby County coverage outline — gates the county's dispatch entries. Shipped 2026-08-04 by the pass-13 research sweep as gap-location geometry; promoted 2026-08-11 to the dispatched county's coverage test when Shelby joined as the 49th, referenced by loadShelbyCountyOutline in index.html.
    "st-clair-county-outline.json": (1, 1),  # St. Clair County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "stark-county-board-districts.json": (2, 2),  # Stark's 2 county board districts, FOUR members each — the smallest board the layer carries. Built by scripts/build_stark_districts.py from the County Clerk's own Google My Maps, the county's entire GIS. That map was unusable for a year because its DATE could not be established (the state's pointer files are from August 2020, before the late-2021 redistricting, and the county's online minutes only begin in July 2022), and what settled it was asking: Clerk Heather Hollis wrote on 2026-08-03 that "the board districts and precincts are correct" and that "the only thing that changed on the map is the congressional district". Bounds are an EQUALITY: the county has exactly two districts, and each is a whole-precinct union cross-checked at build time with every precinct >=99.99% inside its district.
    "stark-county-outline.json": (1, 1),  # Gap-location outline for Stark County — NOT a dispatched county. The pass-7 sweep measured its board geometry as blocked/partial; this outline exists solely so its recorded gap attaches to its ground in the data-gaps panel (scripts/build_county_outline.py). Referenced by slug-built URL, so the validator's literal-reference check skips it.
    "stark-fire-districts.json": (6, 6),  # Stark's 6 fire departments from the clerk-confirmed My Maps. Uniquely in the fire layer, the source also names who responds with an AMBULANCE, and it is not always the fire department — three districts are covered by Stark County Ambulance, Bradford by Bradford Rescue Squad, Kewanee Rural and Neponset by themselves — so that column ships as its own card row. Tiles 99.65% of the county; Toulon and LaFayette overlap by 0.024% on a hand-drawn seam.
    "stark-library-districts.json": (6, 6),  # Stark's 6 library districts from the clerk-confirmed My Maps. Two of the six (Kewanee, Williamsfield) are seated in a NEIGHBOURING county and reach across the line, which is why the county drew them — a Stark resident's library is not always a Stark library.
    "stark-park-districts.json": (2, 2),  # Stark's 2 park districts (LaFayette, Bradford) from the clerk-confirmed My Maps — together about 9% of the county, the rest genuinely sitting in none. NAME ONLY: this folder carries a `Fire Department` column left over from whoever built it by copying the fire layer, and it is confidently wrong rather than blank ("LaFayette Park District" claims a fire department), so the builder never carries it forward and nothing reads it.
    "stark-precincts.json": (9, 9),  # Stark's 9 voting precincts — the county's eight congressional-survey townships with Toulon split east/west, which is why they are drawn as near-rectangles and why that is correct rather than approximate. Same clerk-confirmed My Maps source as the board districts, and the two folders agree exactly: the board composition names all 9 precincts exactly once. No polling place is published as data. Clipped to the TIGER county outline, since a Stark precinct cannot lie outside Stark.
    "stephenson-county-board-districts.json": (8, 8),  # Stephenson's 8 board districts, lettered B-I. F-I are whole townships and exact; B-E subdivide Freeport Township and are GEOREFERENCED off the county's adopted vector-PDF map (scripts/build_stephenson_board_districts.py, a rare operator step needing pymupdf+numpy; source PDFs archived in data/source/raw/). The only boundary in the app whose accuracy is a measured number — ~20 m — which the card states.
    "stephenson-county-outline.json": (1, 1),  # Stephenson County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "stephenson-fire-districts.json": (15, 15),  # Stephenson County's 15 named fire services, GEOREFERENCED from the county's own 2014 vector-PDF map (scripts/build_stephenson_fire_districts.py — fitted on hydrography, median 11.5 m; verified by the map's own town labels; --check is the drift gate). The county publishes no fire boundary as data; the card carries the 2014-vintage caveat. Several services keep their true extents past the county line — the map draws them that way — and the entry's coverage keeps answers inside Stephenson.
    "stephenson-precincts.json": (36, 36),  # Stephenson's 36 CURRENT voting precincts — 20 rural + Freeport 01-16. Bounds are an EQUALITY because the two source maps enumerate the whole county exactly once. For a year the app recorded that Stephenson published no current precinct boundaries; it does, as two vector PDFs on the County Clerk's own Elections page, which Clerk Jazmin Wingert pointed at on 2026-08-03 in reply to a records request. Georeferenced by scripts/build_stephenson_precincts.py, which proves the transcription two ways before writing: the 36 printed populations total 44,630, the county's live Census 2020 POP100 to the person, and the Freeport sixteen are cross-checked against the SAME sixteen polygons the board-district map draws — read off a different document, georeferenced independently, and agreeing 16/16 on district assignment at IoU 0.996 or better.
    "tazewell-county-outline.json": (1, 1),  # Tazewell County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "union-county-outline.json": (1, 1),  # Union County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "vermilion-county-outline.json": (1, 1),  # Vermilion County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "wabash-county-outline.json": (1, 1),  # Wabash County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "warren-county-outline.json": (1, 1),  # Warren County outline — gap-location geometry only, not a dispatched county. Added by the pass-10 frontier sweep (2026-08-03) so its gap entry attaches to ground.
    "washington-county-board-districts.json": (3, 3),  # Washington County Board districts, DERIVED: Census townships dissolved per the whole-township composition the county prints under each district heading (scripts/build_washington_board_districts.py; --check is the drift gate). The county runs NO GIS of any kind. No township is split, so every district edge is a township edge; the build asserts the three districts partition all 16 townships exactly and that their Census 2020 populations balance (5.1% spread).
    "washington-county-outline.json": (1, 1),  # Washington County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entry.
    "wayne-county-outline.json": (1, 1),  # Wayne County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "white-county-outline.json": (1, 1),  # White County coverage outline — gates the county's dispatch entries. Shipped 2026-08-04 by the pass-13 research sweep as gap-location geometry; promoted 2026-08-17 to the dispatched county's coverage test when White joined as the 50th, referenced by loadWhiteCountyOutline in index.html.
    "white-precincts.json": (18, 18),  # White County's 18 voting precincts — the Census 2020 voting districts, which match the county's own adopted map ("White County, IL voting districts & precincts map.pdf", supplied by County Clerk & Recorder Kayci Heil 2026-08-17, archived in data/source/raw/) 18/18 by name. Bounds are an EQUALITY because the fabric is the county's whole precinct list. Names use the county's spelling — HERALDS PRAIRIE 22, also the spelling on its polling list, where the census GEOID 1719300HP22 spells HAROLDS — and each feature carries its census GEOID, POP100 and its County Board district, which is whole-precinct (no split, proven by the certified 2022/2024 canvasses). scripts/build_white_boundaries.py verifies the composition three independent ways before writing: a machine tracing of the map's vector district lines (county-panel fit median ~16 m, every VTD ≥ 99% inside one traced face), the certified canvasses (18/18 agreement required), and the map's Carmi inset, whose lines trace the census edges to a measured ~2 m median. The 18 populations sum to the county's exact Census 2020 POP100.
    "white-county-board-districts.json": (5, 5),  # White County's 5 single-member County Board districts, DISSOLVED from the county's own precinct fabric (Census 2020 VTDs) per a composition proven twice: a machine tracing of the county's adopted map and the county's certified 2022 General Election canvass (the first on the 2021 map; districts 3-4 re-confirmed by the 2024 canvass) agree 18/18, and the build refuses to write on any disagreement. Clerk Heil stated in writing 2026-08-17 that the board is elected by district. Populations balance within 2.33% of the one-member ideal and sum to the county's exact 13,877. The weekly roster workflow watches the Elections page's link to the adopted map as the redistricting tripwire (build_white_county_board.py); a full re-verification is scripts/build_white_boundaries.py --check (operator step: pymupdf/numpy/shapely).
    "whiteside-county-outline.json": (1, 1),  # Whiteside County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "will-county-outline.json": (1, 1),
    "williamson-county-outline.json": (1, 1),  # Williamson County outline — gap-location geometry only, not a dispatched county. Added by the pass-13 detached-counties research sweep (2026-08-04) so its gap entry attaches to ground.
    "winnebago-county-outline.json": (1, 1),  # Winnebago County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
    "winnebago-judicial-subcircuits.json": (2, 2),  # 17th Circuit (Winnebago + Boone) subcircuits, PA 102-0693 enacted map.
    "woodford-county-board-districts.json": (3, 3),  # Woodford County Board districts, DERIVED: TIGER townships dissolved per the county's adopted Ordinance 2020/21 #005 (scripts/build_woodford_board_districts.py; --check is the drift gate). The county publishes no board GIS — TCRPC, its GIS of record, carries precincts and townships only — so this file IS the boundary source, not a cache of one.
    "woodford-county-outline.json": (1, 1),  # Woodford County coverage outline (scripts/build_county_outline.py) — gates the county's dispatch entries.
}

# file -> minimum key count (officeholder rosters).
ROSTER_FILES = {
    "clark-county-board-members.json": 8,  # Clark County Board members keyed by district (7 single-member districts) plus a top-level 'board' entry carrying the COUNTY's switchboard and courthouse address — the county publishes no per-member contact a machine can read, so one number stands for the board (the Calhoun switchboard rule). THE ROSTER IS THE COUNTY'S CERTIFIED ELECTION RETURNS, not a board page: the county's only board document is a SCANNED IMAGE with no text layer, so each member is whoever the county certified as elected in the most recent general election that seated their district (districts 3, 4 and 7 in 2024; 1, 2, 5 and 6 in 2022), and every row renders that election in districtSource because a canvass cannot show a mid-term appointment. Party ships; no term or chair does, because the returns publish neither. Per-member phones and e-mails are DELIBERATELY ABSENT — they exist only in that scan, where one of the seven addresses is unresolvable from the image, and six read-by-eye personal addresses plus a guess is not a roster; the current list is an open ask with the Clerk. The scan also prints every member's HOME ADDRESS, which never ships under any sourcing (the Madison/Peoria rule). The weekly run re-reads the canvasses and fails if a district's tabulated precincts stop matching the shipped boundaries (scripts/clark_county_board_scraper.py + build_clark_county_board.py).
    "crawford-county-board-members.json": 5,  # Crawford County Board members keyed by district (5 districts electing TWO members each = 10 seats). Scraped weekly from the county's own board page, which publishes each member as a linked personnel entry with a county e-mail — 10/10 carry one — and badges the Chairman. No party, term or phone ships because the page publishes none. THE SAME WEEKLY RUN IS THE REDISTRICTING TRIPWIRE: it re-reads the district composition from the Clerk's live results feed and fails if it stops matching the shipped dissolve, which is this county's only automatic warning — the check is partial by construction (the feed carries one election) and the run says which districts it could not cover.
    "edgar-county-board-members.json": 7,  # Edgar County Board members keyed by district (7 single-member districts). Scraped weekly from the county's own board page, which publishes name, district and party for all seven — 7/7 with a party — AND NOTHING ELSE: no e-mail, phone, term or board chairman ships, because none is published and the committees table's CHAIRMAN column names the chair of each COMMITTEE. READ THE DOMAIN: the roster is on edgarcountyillinois.COM; the county's .GOV links across to it and does not carry the board. THIS ROSTER IS THE PAGE AND NOT THE RETURNS, and Edgar is the fleet's clearest case for that split — its 2022 and 2024 canvasses elected Phillip Ludington in District 6, the page names Samantha McCarty, and the Clerk's 2026 primary confirms her with a '2-year unexpired term' contest for the seat. A mid-term appointment is exactly what a completed canvass cannot show. The same weekly run re-reads the district composition from the Clerk's feed as the redistricting tripwire, covering whichever districts were on the last ballot and naming the rest as unchecked.
    "franklin-county-board-members.json": 3,  # Franklin County Board members keyed by district (3 districts seating 3 each, staggered — 9 members; 8/9 with a phone, 1 e-mail, and the role the county prints beside 5 of them). Scraped weekly from the county's own members page. THE PAGE IS A GRID AND IS READ AS ONE: its WP Table Builder cells carry data-y-index/data-x-index, and a flattened text read pairs every role with the WRONG member because column 0's role arrives before its own row's name — the Cumberland trap. Its Address column is every member's HOME address and is never read (the Madison/Peoria rule), asserted address-free in both stages. Its e-mail column is Cloudflare-obfuscated, the exact failure that silently emptied Brown County's seven addresses, so the scraper decodes data-cfemail and FAILS if the markup is present and nothing decodes. The 'Home or E-Mail' column ships only its e-mail half — a home telephone is the one contact this project does not publish and the county does not say which a cell holds. NO PARTY: the page publishes none, and taking it from the canvasses would label only the third of the board last on the ballot. THE CHAIR IS THE COUNTY'S OWN LABEL, not an inference from returns — the table names committee chairs by their committee and the board's own officers plainly ('Chairman', 'Vice Chairman'). The same run re-checks the district composition against the Clerk's results system and fails on a re-precincting or a redistricting.
    "clinton-county-board-members.json": 5,  # Clinton County Board members keyed by district (5 districts seating 3 each — 15 members, ALL FIFTEEN with a phone, an e-mail and a term-expiry year, the richest board source the canvass route has met). Scraped weekly from the county's own board page, whose Board Chairman and Vice Chairman lines are matched onto their own member rows by name — a label matching no member is a hard failure rather than a badge attached to nobody. TWO OF THE FIFTEEN OPEN THEIR COLUMN WITH a photo wrapped in the same <strong> tag the name uses, so a reader that takes the FIRST match cleans to an empty string and drops the member while every other count still passes; the parser walks every one instead, which is how Kurt Schmitz was recovered on the first run. One member's published address is a personal gmail among fourteen on the county domain and ships as published — substituting a county address the county did not print would be inventing one. NO PARTY: the page publishes none. The same run re-checks the district composition against the Clerk's results system and fails on a re-precincting or a redistricting.
    "warren-county-board-members.json": 4,  # Warren County Board members keyed by district (4 districts seating 15 as 3/4/4/4 — 14 e-mails, 7 phones, a term-expiry year on every seat, the committees the county lists, and the Chairman of the Board badged from his own row). Scraped weekly from the county's board page. THE PAGE WRITES MEMBERS TWO WAYS and only one is the obvious shape: thirteen are <li>Name<ul>details</ul></li> and two are <li>Name</li><li><ul>details</ul></li>. Matching only the first drops two of the fifteen — and one of the two is the CHAIRMAN OF THE BOARD, so the naive parse loses a member and the chair while every district still looks populated. Both shapes are matched explicitly rather than by searching backwards for a name, which is how an earlier attempt started reading members' HOME ADDRESSES as their names. THE COUNTY PUBLISHES A HOME ADDRESS FOR EVERY MEMBER: those lines are identified and dropped by construction, the run reports how many it saw and refused, and it FAILS if it sees none — because their disappearance would mean the layout moved and the parse should be re-read. Every e-mail is Cloudflare-obfuscated with no plain mailto anywhere, the exact markup that silently emptied Brown County's addresses, so data-cfemail is decoded and markup-present-but-nothing-decoded is a hard failure. ONE E-MAIL IS MISSPELLED AT SOURCE — the county prints TWinkler at 'warrecountyil.gov', missing the n — and ships as published, the Carroll 'Distirct' precedent. The same run re-reads the precinct-map legend the BOUNDARY was dissolved from, which makes this the strongest drift check in the fleet: the tripwire re-parses the exact document the geometry came from.
    "il-senate-members.json": 59,
    "il-house-members.json": 118,
    "mercer-county-board-members.json": 5,  # Mercer County Board members keyed by district (5 districts electing TWO members each = 10 seats). Scraped weekly from the county's own board table, which prints party and a term-expiry on every row (10/10 each), the member's home TOWN — how the county identifies who represents where, and not a street address; the scraper FAILS if that column ever starts printing one — and badges the Chairman with his phone. THE SAME WEEKLY RUN IS THE REDISTRICTING TRIPWIRE: it re-reads the district composition from the Clerk's live results feed and fails if it stops matching the shipped dissolve. That matters more here than most: the only map the county has sent is a 2021 scan, so nothing else would ever show the districts moving.
    "school-board-members.json": 20,
    "congress-roster.json": 17,
    "cpd-district-info.json": 0,  # ships as an empty placeholder until its first scrape lands
    "ccpsa-district-councils.json": 20,  # 22 councils (13 & 21 retired); floor guards a partial scrape
    "will-county-board-members.json": 11,  # 11 board districts (2 members each) scraped weekly from willcountyboard.com
    "kane-county-board-members.json": 24,  # 24 single-member board districts + the countywide-elected Chair, scraped weekly from the county's own SharePoint Board Members list (no bot block — plain requests)
    "lake-county-board-roles.json": 19,  # Lake board leadership tags (Chair/Vice-Chair) + all 19 member names for the card's stale-role guard, scraped weekly from the county directory (requests with an Internet Archive fallback); names/contact stay live on the boundary GIS
    "kendall-county-board-members.json": 2,  # 2 board districts (5 members each incl. the Chairman) scraped weekly from kendallcountyil.gov (Akamai-fronted; the scraper falls back to Playwright)
    "mchenry-county-board-members.json": 9,  # 9 board districts (2 members each) + the countywide-elected Chairman, scraped weekly from mchenrycountyil.gov (bot-managed; the scraper falls back to Playwright)
    "early-voting-sites.json": 3,  # GeoJSON FeatureCollection (type/metadata/features — key floor is shape-only); hand-curated per election from chicagoelections.gov, network-first so a new election's list is never served stale
    "ccbr-roster.json": 3,
    "il-county-clerks.json": 101,
    "dupage-county-board-members.json": 6,
    "winnebago-county-board-members.json": 18,  # Winnebago County Board CONTACT keyed by district (20) — the phone and official @board.wincoil.gov e-mail the county's GIS declares and populates on 0 of 20 rows. Enrichment only: the member and party come from the GIS, so losing this file costs contact rows, never the officeholder. Each row is name-matched to the GIS at build time.
    "sangamon-county-board-members.json": 27,  # Sangamon County Board members keyed by district (29 single-member districts) — scraped weekly from the 29 per-district member pages the county's own board GIS links to.
    "livingston-county-board-members.json": 3,  # Livingston County Board members keyed by district (3 multi-member districts, six seats each) — scraped weekly from the county directory. Carries a `vacancies` count per district because the directory lists an explicit "Vacancy" seat that must be counted, never named.
    "dekalb-county-board-members.json": 12,  # DeKalb County Board members keyed by district (12 districts electing two members each) — scraped weekly from the county's own members page, which carries the party, phone and e-mail the boundary GIS declares and leaves empty. The Board Chair is one of the 24 members and rides that member's row.
    "ogle-county-board-members.json": 8,  # Ogle County Board members keyed by district (8 districts electing three members each) — scraped weekly from the county's staff directory, which carries party, phone and e-mail 24/24 plus the Board Chair and Vice Chair. Joined to the derived district geometry above.
    "stephenson-county-board-members.json": 8,  # Stephenson County Board members keyed by district LETTER (B-I, two seats each; there is no District A) — scraped weekly from the county board page, which carries phone, e-mail and the Chairman/Vice Chairman. The scraper drops a mailto whose local part does not match the member's surname: one seat currently links its predecessor's address.
    "carroll-county-board-members.json": 3,  # Carroll County Board members keyed by district (3 districts electing three members each) — scraped weekly from the county's board directory, which writes ROMAN numerals the scraper converts to the Arabic keys the map uses. Its member floor is the full board of 9, not one under: the county has "District" typo'd on one row and the first scraper silently dropped that member.
    "lee-county-board-members.json": 4,  # Lee County Board members keyed by district (4 districts electing five members each, 20 seats) — scraped weekly from the Clerk's Member Contact List, which the CMS serves as a PDF. Read by WORD POSITION (pdfplumber): pypdf flattens it into a name block and a separately-ordered e-mail block, so pairing by sequence would mis-assign addresses. The Board Chair is derived from the row carrying the county's shared leecochair@ address rather than a personal one.
    "rock-island-county-board-members.json": 18,  # Rock Island County Board members keyed by district (19 SINGLE-member districts, the most of any county on this layer) — scraped weekly from the county's board page, whose CivicPlus staff-directory widget carries h-card microformat classes. The county GIS declares a NAME column and populates it on 0 of 19, which is why this file exists. Chairman and Vice-Chairman are tagged on their own district rows; both are elected from among the 19.
    "coverage-gaps.json": 8,  # Known data gaps keyed by gap id, driving the app's Data gaps panel — emitted from the guidebook's GUIDEBOOK:BEGIN gaps block by scripts/build_coverage_gaps.py (--check is the drift gate). Network-first like the rosters on purpose: a gap that has been closed should stop being advertised on the next visit, not a release later.
    "municipal-officials.json": 500,  # Municipal governing bodies keyed by Census place GEOID; all seven metro counties plus LaSalle, Winnebago, Ogle, Stephenson, Carroll, DeKalb, the pass-6 tranche (Grundy, Livingston, Logan, McLean's three ward cities, Sangamon, Madison, St. Clair, Rock Island), the pass-9 clerk-reply tranche (Henry, Cass, Whiteside, Peoria, Tazewell), Boone, Macoupin and the three counties whose clerks sent a DOCUMENT rather than a link — Marshall's elected-officers table, Washington's 40-page Blue Book and De Witt's "Village/City Officials" Word list (e-mailed 2026-08-17; all seven municipalities, appointed/acting officers marked), all archived under data/source/raw/ and parsed from there — shipped: 623 municipalities — incl. the Town of Cicero, which the Cook Clerk files under the TWNSP township type as 'Cicero Township' (one coterminous town/township government; absent from MUNIS entirely), and the Village of Crete, whose Will-flipbook entry loses its header to PDF-text extraction and is recovered from the orphaned block + the county's certified 2025 canvass (will_municipal_officials_scraper.py recover_crete) — per docs/EXPANSION_GUIDE.md Part 2.4. Winnebago is the only source that publishes governing bodies AS GIS LAYERS (winnebago_municipal_officials_scraper.py); Freeport, the one Stephenson municipality its county page omits, comes from the city's own site (freeport_council_scraper.py); Madison and St. Clair share one source (the East-West Gateway Public Officials Directory, ewg_municipal_officials_scraper.py); Cahokia Heights (incorporated 2021) joins via an explicit post-Census-2020 GEOID. Boone's yearbook prints a RESIDENCE under almost every official, so boone_municipal_officials_scraper.py refuses address lines by construction and proves on the built payload that none survived; its edition is discovered from the link TEXT ('2026 Yearbook') because the Clerk's page slug still reads 2019. Macoupin's directory PAGE carries no names at all — a vendor plugin (SOE Software) draws them in from a Java/Seam REST service beside the CMS, which is why no WordPress action ever answered; the service's address was recorded from a browser capture on 2026-08-20 and is an unauthenticated JSONP GET, so macoupin_municipal_officials_scraper.py needs no browser. Its per-office `effectiveAtLarge` flag means APPOINTED TO FILL AN UNEXPIRED TERM, not elected at large — the site's own legend for the asterisk it renders — and the scraper re-reads that legend every run rather than trusting the field name.
    "lasalle-county-board-members.json": 29,  # LaSalle County Board members keyed by district (29 single-member districts) plus the countywide-elected Chairman under 'chair' — scraped weekly from the county's own CivicPlus directory (full 10-digit phones + district-office e-mails). Replaces the 2015-frozen officeholder columns on the county's superseded board GIS.
    "logan-precinct-polling.json": 3,  # Logan County precinct polling places, scraped from the clerk's own Polling Places page by scripts/build_logan_precinct_polling.py (29 precincts; --check compares against the live page). Polling assignments are per-election — re-run the builder when the clerk updates the page.
    "carroll-precinct-polling.json": 3,  # Carroll County precinct polling places, expanded from the clerk's published polling notice by scripts/build_carroll_precinct_polling.py against the county's 22 unchanged Census-2020 precinct names (deterministic grouped-label expansion; --check compares against the live notice). Per-election, like Logan's.
    "dekalb-precinct-townships.json": 4,  # The key pairing DeKalb County's nineteen two-letter precinct codes with their townships. The county prints precincts as 'AF 01' / 'DK 15' / 'SG 01' on its precinct layer, its board-district listings and its committeeperson lists, and publishes no expansion anywhere; five townships start with S, so the names could not be worked out without guessing, which is what the dekalb-precinct-codes gap recorded for a year. County Clerk & Recorder Tasha Sims sent the key by e-mail on 2026-08-17 in reply to the question. The card now leads with 'South Grove Precinct 1' and keeps the county's own code beside it, so nothing the county publishes is hidden. Her list spells the MI township 'MILAND' where the Census Bureau and the township spell it MILAN; MI is the only M township left once MA (Malta) and MF (Mayfield) are taken, so the pairing is unambiguous and the shipped name is the spelling everyone else uses, with the discrepancy recorded in the file. Her three village annotations (Waterman, Kirkland, Hinckley) ride along and surface as a card note, because 'why does my Waterman address say Clinton?' is the question the codes actually provoke.
    "whiteside-precinct-polling.json": 3,  # The TWO voting locations Whiteside County references but does not publish. Its precinct layer points at facility ids 22 and 26, which are absent from the 29 locations its own polling layer publishes, leaving Sterling 9/14/18 and Prophetstown 1 with no polling place on the card. County Clerk Karen Stralow named both buildings by e-mail on 2026-08-03 — facility 22 is Self Help Enterprises, 2300 W. LeFevre Rd., Sterling; facility 26 is Winning Wheels, 701 E. 3rd St., Prophetstown — and this file exists only to fill those two ids. The loader consults it ONLY when the county's own layer has no match, so publishing those facilities upstream retires it silently. Names AND addresses, both from the Clerk on request — nothing here is looked up elsewhere. Unlike Logan's and Carroll's this is NOT a whole-county polling table and has no builder — it is two hand-entered records from a named source.
    "hamilton-precinct-polling.json": 3,  # Hamilton County precinct polling places, parsed from the Clerk's statutory notice for the March 17, 2026 General Primary — published on the county's post-migration website — by scripts/build_hamilton_precinct_polling.py (16 precincts, 13 locations, the shared McLeansboro gym and the Clerk's 13-location count asserted; --check compares against the live notice). The notice settled the Dahlgren #1/#2 pairing that two ~0.3 mi-coarse georeferencing instruments could not, exactly as the 2026-08-05 gap record predicted only the election authority could. Per-election, like Logan's and Carroll's — the card labels the row with the election the notice names.
    "woodford-county-board-members.json": 3,  # Woodford County Board members keyed by district (3 multi-member districts, five seats each, 15/15 with phone and e-mail) — scraped weekly from the county's own CivicPlus directory. No chair key: the chair is elected from within the body and the directory does not mark who holds it.
    "logan-county-board-members.json": 6,  # Logan County Board members keyed by district (6 two-member districts, 12/12 with phone and e-mail; the Chair and Vice Chair tags ride their member rows — the county says who holds them) — scraped weekly from the county's own board page. Its existence retired the entry's rule-4 branch-3 honesty floor.
    "boone-county-board-members.json": 3,  # Boone County Board members keyed by district (3 four-member districts, 12/12 with phone, e-mail and a term-expiry year — terms are staggered, so the year is per-seat ballot information) — scraped weekly from the county's own board page. Role tags verbatim: currently one Vice-Chairman; the page names no Chairman, so none is rendered. The boundary half is live GIS (three per-district layers merged at load time), not a data/app file.
    "grundy-county-board-members.json": 3,  # Grundy County Board members keyed by district (3 six-member districts, 18/18 with party, the page's 'Board Member Since' year, committee assignments verbatim, phone and e-mail; the Board Chairman tag rides Drew Muffler's row as the page states it) — scraped weekly from the county's own board page.
    "henry-county-board-members.json": 2,  # Henry County Board members keyed by district (2 ten-member districts — the fleet's widest; 20/20 with e-mail, 15 with phone) — scraped weekly from the county's own CivicPlus directory, which the county itself keys by district (DID=39/40), so the assignment is the county's own. No chair key: the chair is elected from within the body and the directory does not mark who holds it.
    "jefferson-county-board-members.json": 13,  # Jefferson County Board members keyed by district (13 SINGLE-member districts; 13/13 with a phone and a per-district e-mail, district1@… — a role address rather than a personal one, which is what the county publishes) — scraped weekly from the county's own board page. THE PAGE IS AT THE SITE ROOT: /county_board/index.php, not the /government/county_board/index.php the site's own navigation links, which 404s while rendering a full-looking page. Names arrive SURNAME-FIRST and are read forward by uninvert_name() imported from build_municipal_officials_roster.py — the third source in the fleet to need that guard in one week. Chairman and Vice Chair hold district seats and are badged on their own rows.
    "macon-board-district-labels.json": 3,  # Five ANCHOR POINTS that label Macon County's five board district shapes, which the county publishes live with EVERY ATTRIBUTE NULL — no district number, no representative, no contact. macon-county-board-labels held the board card back from 2026-08-02 for exactly that reason, and named its own cure: "a labelled clerk's map". County Clerk Josh Tanner sent one on 2026-08-07, colour-coded with a numbered legend, archived under data/source/raw/. This ships the five labels rather than the geometry, so the county's own shapes stay live and authoritative; index.html assigns each shape the district whose anchor it contains and refuses to serve ANY feature unless that is one-to-one, which puts Macon back in the held-back state rather than showing a wrong commissioner. The assignment was verified precinct by precinct, not by position: each shape's membership across the county's own 64 precincts reproduces the map's colour regions exactly, outliers included (Decatur 24 alone in the northern district, Decatur 4/7/28 in the eastern, Decatur 22/25 in the western). The 15-member roster falling 3-3-3-3-3 is a third independent check.
    "macon-county-board-members.json": 5,  # Macon County Board members keyed by district (5 districts electing THREE members each, 15 seats; 15/15 with party and a county e-mail, 14 with a phone, 13 with a term-expiry date) — scraped weekly from the county's own board-members page, which is the ONLY place Macon publishes which district a member sits for. Party and district arrive as one token ("D-1", "R-4"). PHONES SHIP AS SEVEN DIGITS, as the county publishes them: Macon is entirely area code 217, but a member's mobile can be from anywhere and prefixing would reach a stranger rather than fail visibly — the county's own home/cell labels are kept instead. THE DOMAIN IS maconcounty.illinois.gov; maconcountyil.gov has no DNS record at all and shipped as a dead card link from 2026-08-04 until this change.
    "menard-commissioner-members.json": 5,  # Menard County commissioners keyed by district (5 SINGLE-member districts; 5/5 with a phone and a county e-mail, plus the year each was elected or appointed) — scraped weekly from the county's own board page. District comes from the COLUMN POSITION in a one-row, five-column table, so the scraper reads the header rather than assuming order: shuffled columns would still look like a valid board. DISTRICT 1'S E-MAIL LINK AND ITS LABEL DISAGREE — the page links djwhitley@ and displays dwhitley@ — and the HREF ships, because that is where the county's own page actually sends mail; the run prints a NOTE rather than resolving it silently. District 5's "Ed Whitcomb, Jr." is the first name in the fleet to exercise uninvert_name()'s REFUSAL path in production, and the builder asserts it came through unreordered.
    "henry-precinct-polling.json": 3,  # Henry's precinct -> polling place table, all 52 precincts. THE SOURCE IS THE CLERK'S OWN POLLING PLACES DIRECTORY, and finding it is the point: the county GIS office sent the precinct shapefile on 2026-08-06 with no polling assignment and said plainly that a polling list is the Clerk's record, not theirs, so this sat open for five days. Clerk Barbara Link answered on 2026-08-11 with one sentence — "I have pdf precinct maps on my webpage ... Also, I have polling place locations as well" — which reads as a brush-off and is a POINTER, and the pointer was correct: her directory lists all 52 locations, one per precinct, and had been reachable for the entire life of this project without anyone opening it. The Stephenson lesson, a second time. THE JOIN IS ON THE PRECINCT'S OWN FIELD, not the listing title, because the title is not a key: the county writes "Colona 3- Colona Activity Center" without the space and "Andover Village Hall" with no precinct prefix at all. ONE ALIAS, ENUMERATED: sixteen townships hold a single precinct and the two sources disagree about its number ("Alba" in the directory, "Alba 1" in the shapefile), so a bare name maps to "<name> 1" ONLY where the shapefile has exactly one precinct in that township and no bare form; anything else fails the build. scripts/build_henry_precinct_polling.py refuses to write unless the directory's own stated listing count parses and all 52 precincts resolve — a partial join would leave a resident with a blank row on the one card where being wrong sends them to the wrong building. REFRESHED WEEKLY by .github/workflows/update-henry-precinct-polling.yml (Fri 18:00 UTC), the fleet's first scheduled polling job — the other three are operator steps, and this field is the one where staleness sends someone to the wrong building. The job opens a PR only when a polling place actually moved, not when the fetch date did.
    "montgomery-precinct-polling.json": 3,  # Montgomery's precinct -> polling place table, all 38 precincts across 24 buildings (12 precincts share a site with another). THE SOURCE IS THE CLERK'S PUBLISHED LIST, NOT THE GIS LAYER THAT ARRIVED WITH IT. Asked on 2026-08-07 whether a precinct-to-polling-place mapping existed, Montgomery County GIS sent a PollingPlaces point layer; cross-checking it against the Clerk's own "38 Precincts / 24 Polling Places" document found the layer omits ROUNTREE entirely (it votes at Nokomis Memorial Park House with Nokomis 2) and still names the National Guard Armory for North Litchfield 1 and 4 where the Clerk has First Presbyterian Church — two different buildings, not a wording difference — plus a superseded name for Hillsboro 5 and 6. A polling place is the one field on this card where being stale sends a resident to the wrong building on election day, so the election authority's list wins. scripts/build_montgomery_precinct_polling.py keeps the GIS layer as a self-retiring cross-check: it names those disagreements and FAILS if the layer's answer changes, so a county refresh that fixes them is noticed rather than hidden.
    "montgomery-county-board-members.json": 7,  # Montgomery County Board members keyed by district (7 districts electing TWO members each; 14/14 with a direct phone AND a county e-mail, four with a second published number) — scraped weekly from the county's own board page. The page rather than the Clerk's members PDF: checked 2026-08-06 the PDF still named two members who had been replaced, so the two county documents are trusted for different things — the PDF for district COMPOSITION, the page for names. The Board Chairman is badged on his own district row; he holds a district seat, so there is no countywide section. One published e-mail (District 5's, at cody.gudel@) does not match the member's surname and is carried exactly as the county publishes it — correcting it would mean inventing an address.
    "peoria-county-board-members.json": 18,  # Peoria County Board members keyed by district (18 SINGLE-member districts — the app's largest single-member board; 18/18 with party and e-mail, 12 with phone). Scraped weekly: the county's own ElectoralDistricts GIS layer is the machine-readable spine (district -> name, party, member-page URL) and each member page supplies the contact. The Chairperson and Vice-Chairperson are badged on their own district rows — both hold district seats — and only where the county's index page states the role.
    "tazewell-county-board-members.json": 4,  # Tazewell County Board members keyed by district (3 districts seating 21 members) plus a `chair` key for the COUNTYWIDE-elected Board Chairman (the McHenry shape). Scraped weekly from the county's own member pages (21 e-mails, 18 phones) rather than from its GIS layer, whose member attributes are stale. The scraper records the one district assignment the county's two surfaces disagree about instead of silently picking the tidier arithmetic.
    "iroquois-county-board-members.json": 4,  # Iroquois County Board members keyed by district (4 districts, four members each; 16/16 with phone, 15 with e-mail, every seat with a home town and term-expiry year). Scraped weekly from the county's own table, which prints ROMAN numerals the scraper converts to the integers its GIS keys by. Chairman and Vice Chairman are badged on their own district rows — both hold district seats.
    "il-county-commissioners.json": 12,  # At-large county boards, keyed like il-county-clerks.json. Counties that elect their board COUNTYWIDE have no district geometry, so their members ride the COUNTY card rather than a county-board dispatch entry (EXPANSION_GUIDE §1.5). Twelve counties, 60 members: Monroe and Randolph (commission form, 3 each), Pike 9, Brown 7, Schuyler 7, GREENE 7, MORGAN 3, Calhoun 5, Putnam 5, Hamilton 5, EDWARDS 3 and WABASH 3 — the last two being the counties whose rosters are NOT scraped from a page. Greene, added 2026-08-08, is the first of these that was ALREADY SERVED before its board arrived (a 7th-Circuit subcircuit answered there), so it moved tier without changing the coverage ring or any anchor. Edwards has no website at all (its Clerk said so on 2026-08-06, and the domain answers NOERROR with no A record), so its three commissioners come from a document she sent. Wabash, added 2026-08-17, is the second such county — wabashcounty.illinois.gov carries mail and serves no web page (port 80 answers 503, measured 5 Aug and re-checked 9 Aug) — and its three come from Clerk Will's e-mail of 2026-08-16; her e-mail lists only HOME addresses, which do not ship, so each Wabash row is a name alone, and nobody is marked Chairman until she answers which of the three chairs. The scraper carries both counties in DOCUMENT_ROSTERS and prints a NOT RE-READ line naming each document and its age on every run, because a weekly job that refreshes a hand-carried roster refreshes nothing. Each shipped county carries EITHER a sourceUrl or a sourceDocument+verified pair; the builder fails on a county with neither. MORGAN, added 2026-08-08, is the cautionary one: the county has TWO sites and this project read the wrong one for a day — morgancounty-il.GOV is a content-free React shell, while morgancounty-il.COM publishes all three with role, party, term dates and a personal e-mail apiece.
    "dewitt-county-board-members.json": 4,  # De Witt County Board members keyed by district LETTER (A-D, three members each; 12/12 with e-mail, 10 with phone, committees per member). Scraped weekly — and the same scrape re-reads the district composition printed on that page and FAILS if it no longer matches the compiled boundary, so a redistricting surfaces in CI rather than leaving the derived lines a cycle out of date.
    "washington-county-board-members.json": 3,  # Washington County Board members keyed by district (3 districts, five members each; 15/15 with BOTH phone and e-mail). Scraped weekly, and the same scrape re-reads the township composition printed on that page and FAILS if it no longer matches the compiled boundary. Member HOME ADDRESSES are published on that page and are deliberately never collected (the Madison precedent). One member's published e-mail domain is misspelled at the source; it ships as published and the builder WARNs.
    "cass-county-board-members.json": 4,  # Cass County Board members keyed by district (4 districts seating 11 as 3/3/3/2; 11/11 phones, 8 e-mails, the Chairman badged on his own district row). Scraped weekly. Because Cass publishes its district composition only in a PDF, the weekly composition check De Witt and Washington get is impossible — instead the builder asserts the SEAT COUNTS still match the boundary's SEATS table, which is what its population test depends on.
    "marshall-county-board-members.json": 3,  # Marshall County Board members keyed by district (3 districts, four members each; 12/12 phones, 11 e-mails, Chairperson and Vice-Chairperson badged, staggered 2026/2028 term years). Scraped weekly from the roster PDF, and the same scrape re-reads the township composition printed in that PDF's district headings and FAILS if it no longer matches the compiled boundary. Member home addresses are printed in that table and are deliberately never collected (the Madison precedent).
    "mcdonough-county-board-members.json": 3,  # McDonough County Board members keyed by district (3 districts of SEVEN members each = 21, the county's full board), scraped weekly from http://mcg.mcdonough.il.us/members.html — the same page whose district headings supply the boundary composition, so membership and boundary move together and are checked together. The page prints every member's HOME ADDRESS and none is collected: the scraper reads only the phone out of that cell, and the builder refuses to write any field whose name looks like an address.
    "fulton-county-board-members.json": 3,  # Fulton County Board members keyed by district (3 districts of FIVE members each = 15, the count the county states on the same page it publishes them). Scraped weekly from https://fultoncountyil.gov/county-board/members/, which publishes the board TWICE — a photo grid grouped by district (the only place the district is stated) and hidden popup blocks carrying the e-mail the grid omits — so the scraper joins the two halves on the member's name. Above District #1 sits a fourth section headed "Fulton County Board Chairman" containing a member who ALSO appears in his own district; it is read as the source of the Chair ROLE, not as a sixteenth seat, and the per-district ceiling fails the build if it is ever swept in as one. Names ship as the county prints them, including "Karl WIlliams" with its capital I.
    "stark-county-board-members.json": 2,  # Stark County Board members keyed by district (2 districts of four = 8, the county's full board; 8/8 with an e-mail and a term year, Chair and Vice-Chair badged). Scraped weekly from the county's Elected Officials page. The e-mail addresses belong to the SEAT rather than the person — boarddist1-1 through boarddist2-4 — which is better practice than most of the fleet manages and means the contact survives turnover; the builder asserts that pattern still holds and fails if a personal address appears in its place. No member home addresses are published by the county, and the address-key assertion runs anyway so that the day it starts, the build fails rather than the app quietly shipping them.
    "mason-county-board-members.json": 2,  # Mason County Board members keyed by district (2 districts, four members each; 8/8 with party, phone, e-mail and a term year, Chairman and Vice-Chairman badged). HAND-TRANSCRIBED 2026-08-02, not scraped: the county's roster PDF is a scan whose text layer extracts as line noise rather than failing, so a scraper would ship confident garbage. scripts/mason_roster_watch.py runs weekly instead and opens a tracking issue when the board page stops linking that PDF or its bytes change. No residence data ships at all — not even the home town — because one member's address is legally protected and a town-for-seven-blank-for-one roster would single her out.
    "shelby-county-board-members.json": 11,  # Shelby County Board members keyed by district (11 districts electing TWO members each = 22 seats; currently 20 filled + District 7's two shipped AS VACANCIES exactly as the county prints them, 'Currently Vacant' with the seat's e-mail — dropping them would misstate the board's size). Scraped weekly from coboard.aspx and CROSS-CHECKED against the county's second published roster, the contacts.aspx e-mail directory: every directory row must match a card seat by e-mail and name, so a half-updated site fails instead of shipping whichever page the scraper read. Every filled seat carries party, a term string as printed ('2024–2028', 'through 2026') and an e-mail; 20/20 with a phone. The Chair and Vice Chair hold District 3's two seats, badged on their own rows with the role alias e-mail (shcoboardchair@/shcovicechair@) the county publishes beside each district address. Home addresses are printed on every card and NEVER shipped (the Mason/Marshall precedent) — the scraper does not capture them, so nothing downstream can leak them. The same scrape re-parses each card's precinct composition, split pieces included, against the boundary compiled into build_shelby_board_districts.py.
    "white-county-board-members.json": 6,  # White County Board members keyed by district (5 single-member districts) plus a top-level 'board' entry carrying the board's ONE published contact — the Clerk's e-mail and the PO Box the county prints for all five members (one address for five members is the board's, not five members', the Calhoun switchboard rule). Scraped weekly from the county's own board page, which lists name, party and Chair/Vice roles and NO districts: each member's district is joined from the certified-canvass table in build_white_county_board.py (2022 General elected all five by district; 2024 re-elected districts 3-4), matched surname + first initial and required UNIQUE. Any page name that table cannot place FAILS the weekly build instead of shipping a guess — a new member's district is a fact only a new certified document (or the Clerk) can supply.
    "white-precinct-polling.json": 18,  # White County's polling places keyed by shipped precinct name — the County Clerk's own POLLING PLACES list on her Elections page, eleven buildings covering all 18 precincts (Carmi's seven vote at one building; the builder refuses to write on any coverage short of 18/18). Place and address ship as the ONE string the county prints, because splitting 'Fire House 912 Loy St.' into place/address would be a guess. The page's 'Gray #24' is normalised to the GREY 24 spelling the county's own map, the census and the canvasses share, recorded in the builder. Scraped weekly by the same run as the board roster; that run also fails if the Elections page stops linking the adopted district & precinct map the county's boundaries were traced from (the Mason watcher rule).
    "coles-county-board-members.json": 13,  # Coles County Board members keyed by district (12 single-member districts) plus a top-level 'board' entry carrying the County Board office's own address and phone — one office for twelve members is the board's, not each member's (the Calhoun switchboard rule), and it is the BOARD's rather than a county switchboard by measurement: the same navbar block reads Room 124 / (217) 348-0511 on the Treasurer's page and 701 7th St / (217) 348-0585 on the Sheriff's. Scraped weekly from the county's own board page. THE COUNTY'S BOARD-DISTRICT GIS LAYER ALSO CARRIES A MEMBER COLUMN AND IT IS NOT USED: that table is a 2022-04-23 snapshot which names six members who have since left the board, still reads term '2022' for District 11, and carries 2010 populations — so the app reads geometry from the service and people from here (scripts/coles_county_board_scraper.py has the six-name diff). No party, term or chair ships because the page publishes none; home addresses are printed under most members and are never parsed (the scraper keys on the contact row's ICON, not its href, because the address anchor is itself a tel: link). The county's committees page is the cross-check and a disagreement in either direction fails the weekly run.
    "jo-daviess-county-board-members.json": 17,  # Jo Daviess County Board members keyed by district (17 single-member districts — the seat count the boundary module exports, so the roster and the purchased geometry cannot drift apart silently). Scraped weekly from the county's own board page at jodaviesscountyil.gov (NEVER the old jodaviess.org, which answers every URL with its home page): name, party and term on every seat, Chair/Vice-Chair badged, plus a direct phone and an e-mail per member from each member's own directory page — 16 distinct numbers at first ship, so no switchboard hoist, and personal gmail/icloud addresses carried exactly as published. A seat the county prints as VACANT ships as a counted, never named vacancy (District 16 at first ship, the Livingston posture). The directory pages also print members' HOME ADDRESSES, which the scraper never parses (the Madison/Peoria precedent). The count guard counts SEATS (named + vacant = exactly 17, districts 1..17 each once), so a vacancy is distinguishable from a parse regression — and a changed district count reads as a reapportionment, which would need the purchased boundary re-licensed.
    "cook-library-trustees.json": 1,  # Cicero Public Library's seven elected trustees + the library's own contact, keyed by the Cook Clerk's tax AGENCY id (20060001, the fund tiling's own key) — the one Cook library body whose board the county publishes, filed in the Clerk's directory beside the Town of Cicero's government (build_cicero_library_trustees.py). Joined onto the library-district layer's Cook card; every other Cook agency stays name-only because no officeholder source exists for it.
    "township-officials.json": 25,  # Township governing bodies keyed by Census county-subdivision GEOID — supervisor (or Cicero's president), four trustees, clerk/assessor/collector/highway commissioner, township-hall contact — from the Cook County Clerk's directory TWNSP type (build_township_officials.py, 29 townships live; Evanston Township dissolved 2014 and is skipped by name). Party committeepersons and per-person contact never ship: the committeeperson records are the feed's one personal-e-mail surface, and the hall mailbox is shared township-wide. Townships in uncovered counties keep the identity-only card.
}

# Files the app references DYNAMICALLY — the URL is built from a slug at
# runtime (the gaps panel's <slug>-county-outline.json contract), so no
# literal appears in index.html. Exempt from the reference check only;
# existence, shape and the negative-point test still apply.
DYNAMIC_REFERENCE = frozenset({
    "alexander-county-outline.json",
    "bond-county-outline.json",
    "brown-county-outline.json",
    "bureau-county-outline.json",
    "calhoun-county-outline.json",
    "champaign-county-outline.json",
    "christian-county-outline.json",
    "clay-county-outline.json",
    "clinton-county-outline.json",
    "cumberland-county-outline.json",
    "douglas-county-outline.json",
    "edwards-county-outline.json",
    "fayette-county-outline.json",
    "ford-county-outline.json",
    "franklin-county-outline.json",
    "fulton-county-outline.json",
    "gallatin-county-outline.json",
    "greene-county-outline.json",
    "hancock-county-outline.json",
    "hardin-county-outline.json",
    "henderson-county-outline.json",
    "jackson-county-outline.json",
    "jasper-county-outline.json",
    "jefferson-county-outline.json",
    "jersey-county-outline.json",
    "johnson-county-outline.json",
    "knox-county-outline.json",
    "lawrence-county-outline.json",
    "macon-county-outline.json",
    "marion-county-outline.json",
    "massac-county-outline.json",
    "menard-county-outline.json",
    "montgomery-county-outline.json",
    "morgan-county-outline.json",
    "moultrie-county-outline.json",
    "perry-county-outline.json",
    "piatt-county-outline.json",
    "pike-county-outline.json",
    "pope-county-outline.json",
    "pulaski-county-outline.json",
    "putnam-county-outline.json",
    "richland-county-outline.json",
    "saline-county-outline.json",
    "scott-county-outline.json",
    "stark-county-outline.json",
    "union-county-outline.json",
    "vermilion-county-outline.json",
    "wabash-county-outline.json",
    "warren-county-outline.json",
    "wayne-county-outline.json",
    "williamson-county-outline.json",
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
    # (docs/EXPANSION_GUIDE.md Part 5 "Sidebar placement standard"): the boot
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
            if _point_in_geometry(lng, lat, feat["geometry"]):
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

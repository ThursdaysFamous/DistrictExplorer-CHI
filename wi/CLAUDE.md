# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

districtry Wisconsin: a single-file, dependency-light web app. Click a point in Wisconsin (or search an address) and it reports every civic district containing that point and who represents you there. It serves at **districtry.com/wi/** as a folder of the consolidated districtry repo — the first state to expand **in place** rather than as a fork (the retired template route proved this tree end-to-end on the archived `DistrictExplorer-WI` repo before the fleet consolidated; `docs/EXPANSION_GUIDE.md` §4.10 is the decision record). It ships twelve statewide layers. Eleven come from national publishers: U.S. House, WI Senate, WI Assembly, County, the three TIGER school-district tilings (Unified / Union High / Elementary), County Subdivision, Municipality, ZIP Code (ZCTA), and Post Office. The twelfth is **County Board District** — all 1,590 county board supervisory districts, from a STATE publisher rather than a national one, which is why Wisconsin gets in one fetch what Illinois builds county by county: Wis. Stat. 5.15(4)(br)1 makes every county file its current boundaries with the Legislative Technology Services Bureau each 15 January and 15 July, and LTSB publishes the aggregate. Trempealeau's 17 districts come from the county's own service instead, because LTSB's file merges two of them; `wi/scripts/build_wi_supervisory_districts.py` carries the whole measurement. Everything beyond these is this instance's own growth per `docs/EXPANSION_GUIDE.md` (Part 2 for county-by-county builds, §4.3 for new layer modules) — the standing gap is now the county-supervisor roster in the 52 counties that publish none: 20 of the 72 publish a district-keyed member list and their 437 seats ship (`wi/scripts/wi_county_board_scraper.py`, refreshed weekly), the rest are recorded in the Data gaps panel.

**There is no build step, no framework, and no server-side code.** The app — styles, engine, and layer modules — lives inline in `index.html`. `sw.js` is the service worker; `data/app/*.json` are runtime-fetched data files; `data/state/` is the bootstrap's state config (`build_congress_roster.py` reads its FIPS/USPS/seat count — it ships in the repo and is excluded from the Pages deploy). `sources.html` carries the generated per-layer provenance matrix; `faq.html` the ten common questions, mirrored exactly in its FAQPage JSON-LD.

<!-- ==== GENERATED:BEGIN metro-facts ==== -->
**Metro facts** (generated from `metro-worksheet.json` — edit the worksheet and run
`python3 scripts/generate_metro_files.py`; hand-edits here fail CI):

- Metro: Wisconsin (`wisconsin`) — https://districtry.com/wi/
- Geocoders: address Photon (Wisconsin-bounded type-ahead); unbounded Photon (whole-coverage, sibling-metro lookup); POI Nominatim (office-address pin lookup, Wisconsin-bounded, serial >=1s queue)
- Ground truth: 44.89804,-89.75782 (inside Marathon County) → county Marathon County; us-house 7; school-district-unified Marathon City School District; wi-senate 29; wi-assembly 86; county-board 35. Negative point 47.39000,-92.97000 (off the northwest corner of Wisconsin — outside the state and every starter layer).
- Layers: 15 registered (political 4, safety 2, schools 3, geography 6); `registerLayer(` floor 10. Debug namespace `window.WisconsinExplorer`.
- Scheduled workflows: `update-wi-congress-roster.yml` (Mon 13:30 UTC); `update-wi-legislature-roster.yml` (Tue 13:30 UTC); `update-wi-county-board-roster.yml` (Thu 14:30 UTC); `wi-validate-sources.yml` (1st of month 13:00 UTC).
- Source registry: `scripts/validate_sources.py` (machine-checked monthly)
<!-- ==== GENERATED:END metro-facts ==== -->

## Running & testing

```bash
# From the REPO ROOT — one server, every instance:
python3 -m http.server 8000    # then open http://localhost:8000/wi/

# Behaviour gate (real Chromium boot via Playwright) — the main test:
npm install playwright@1.56.1 && npx playwright install --with-deps chromium
BASE_URL=http://localhost:8000/wi/ node wi/scripts/smoke_test.mjs

# Static gate (run after any data/app regeneration or app edit):
python3 wi/scripts/validate_index.py wi/index.html

# Generated-region gate: per-instance facts live ONCE in wi/metro-worksheet.json;
# GENERATED regions are emitted from it. NEVER hand-edit a GENERATED region:
pip install -c scripts/requirements.txt jsonschema
python3 scripts/generate_metro_files.py            # regenerate in place (all instances)
python3 scripts/generate_metro_files.py --check    # the CI drift gate

# Engine parity: the ENGINE fences are composed from the repo-root engine/ —
# edit a block THERE and recompose, never inside an instance file:
python3 scripts/compose_app.py            # splice engine/ into every instance
python3 scripts/compose_app.py --check    # the CI drift gate
```

**Sandboxed environments (Claude Code web):** the headless browser cannot reach the Leaflet CDN. The repo root's `.claude/settings.json` SessionStart hook runs `scripts/vendor_leaflet.sh`, which vendors Leaflet into `wi/scripts/vendor/leaflet/` (gitignored); `wi/scripts/smoke_test.mjs` serves it same-origin. Production and GitHub Actions CI reach the CDN directly.

## Architecture: stable core + pluggable layer modules

The metro-agnostic engine inside `index.html` is fenced with `/* ==== ENGINE:BEGIN <name> ==== */ … ENGINE:END` markers and is **composed from the single copy under the repo root's `engine/`** by `scripts/compose_app.py` — there is no release channel and no per-fork copy to drift. **Never edit inside an ENGINE fence in this file** — edit the block under `engine/` (when the change is right for every instance) and recompose. Everything Wisconsin-specific lives in the `METRO:BEGIN config` block (worksheet-generated) and this instance's own module code.

A layer module is registered via `registerLayer({ id, group, label, overlay, query, render })`; families of similar layers use the fenced factory helpers (`registerPolygonLayer`, `registerIlgaChamber` — the generic chamber factory both WI chambers and the U.S. House card use — `registerNearestPointLayer`, `registerSchoolZone`). The modules section in `index.html` carries a commented crib of each. Two invariants pervade the code: the **stale-async guard** (`if (seq !== state.sequence) return;` after every await) and **per-layer failure isolation** (a layer's failure shows a Retry inside its own card, never breaks the others).

**Honesty rules (non-negotiable):** officeholder data is never guessed — where no verifiable roster source exists, cards link to the official body instead of inventing a name (both chamber cards degrade to the district number + the legislature's own directory on a roster miss). External strings always render through `sanitize()`/`textContent`. Roster refreshes always land as PRs for human review — the two root workflows `update-wi-congress-roster.yml` and `update-wi-legislature-roster.yml` follow the fleet pattern — never as direct commits to main.

## Data pipeline

Live layers fetch Census TIGERweb (county subdivisions, places, School layers 1/2, ZCTA by state envelope) and the USGS National Map (post offices) at runtime with the point-first `.atPoint` hook. Pre-built layers ship as same-origin `data/app/` files: `state-counties.json`, `school-districts-unified.json`, `congress-districts.json` (from the bootstrap), and `wi-senate-districts.json` / `wi-assembly-districts.json` (from `wi/scripts/build_legislative_boundaries.py` — statewide TIGERweb, mapshaper-simplified, refused unless the 2,000-random-point agreement gate passes; each carries TIGERweb's ZZ water pseudo-district). Rosters: `congress-roster.json` (congress-legislators) and `wi-{senate,assembly}-members.json` (Open States `wi.csv` via `build_wi_legislature_roster.py`, floors 31/94) — all count-guarded, all refreshed weekly by CI as reviewed PRs. `county-supervisory-districts.json` and its companion `county-board-directory.json` are OPERATOR builds, not weekly ones: re-run them after an LTSB filing window (WATCH.md). The directory is not a roster of people — it carries each county's board size, read back from the shipped geometry so the two cannot disagree, and the county's own official page for the card's footer link, because Wisconsin publishes no statewide roster of county supervisors. The PEOPLE, where a county publishes them, are `county-board-members.json` — 20 counties, 437 seats, scraped weekly from each county's own page with that county's reading direction PINNED, because the three page shapes include two that are the same extraction shifted by one and a wrong guess files every supervisor under their neighbour's district.

## Growing this instance

A new county or layer follows the repo's `docs/EXPANSION_GUIDE.md`. The working order that guide teaches: prove the source first (a live fetch you performed), ship the boundary and its officeholder sourcing in the same change, floor every scraped count, and record what a publisher does NOT publish in the Data gaps panel rather than guessing. When a layer ships, its row in `wi/metro-worksheet.json` (`layers[]`, with a `source` block) is what puts it on the sources page and in every gate — a layer cannot ship without a provenance row. Extend `LAYER_SIDEBAR_RANK` and `WATCH.md` in the same change.

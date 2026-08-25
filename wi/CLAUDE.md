# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Wisconsin District Explorer: a single-file, dependency-light web app. Click a point (or search an address) and it reports every civic district containing that point and who represents you there. **This repository was created from the District Explorer state-expansion template** (generated from the fleet's reference implementation, `ThursdaysFamous/DistrictExplorer-CHI`) and ships five statewide starter layers any U.S. state can serve from national publishers: County, County Subdivision, Municipality, School District (Unified), and U.S. House. Everything beyond those five is this fork's own expansion, done per the reference repo's `docs/EXPANSION_GUIDE.md` (Part 2 for county-by-county growth, §4.3 for new layer modules, §4.10 for the state-template route this repo was born from).

**If `scripts/check_template_placeholders.py` still fails, this fork is not bootstrapped yet.** Run `python3 scripts/bootstrap_state.py --state-fips NN --state-name <Name> ...` first — it derives the state's bbox/center/anchors from TIGERweb, pre-builds the starter data files under `data/app/`, fills every placeholder token and sentinel, and prints the registration checklist of what it cannot do itself (fleet registration in the reference repo, plus the operator items: Pages + custom domain, `BOT_PR_TOKEN`, the Actions "allow PR creation" toggle, a GoatCounter site, real icons).

**There is no build step, no framework, and no server-side code.** The app — styles, engine, and layer modules — lives inline in `index.html`. `sw.js` is the service worker; `data/app/*.json` are runtime-fetched data files. `sources.html` is the one sub-page, carrying the generated per-layer provenance matrix.

**Metro facts** (generated from `metro-worksheet.json` — edit the worksheet and run
`python3 scripts/generate_metro_files.py`; hand-edits here fail CI):

<!-- ==== GENERATED:BEGIN metro-facts ==== -->
**Metro facts** (generated from `metro-worksheet.json` — edit the worksheet and run
`python3 scripts/generate_metro_files.py`; hand-edits here fail CI):

- Metro: Wisconsin (`wisconsin`) — https://districtry.com/wi/
- Geocoders: address Photon (Wisconsin-bounded type-ahead); unbounded Photon (whole-coverage, sibling-metro lookup); POI Nominatim (office-address pin lookup, Wisconsin-bounded, serial >=1s queue)
- Ground truth: 44.89804,-89.75782 (inside Marathon County) → county Marathon County; us-house 7; school-district-unified Marathon City School District; wi-senate 29; wi-assembly 86. Negative point 47.39000,-92.97000 (off the northwest corner of Wisconsin — outside the state and every starter layer).
- Layers: 11 registered (political 3, schools 3, geography 5); `registerLayer(` floor 8. Debug namespace `window.WisconsinExplorer`.
- Scheduled workflows: `update-wi-congress-roster.yml` (Mon 13:30 UTC); `update-wi-legislature-roster.yml` (Tue 13:30 UTC).
- Source registry: `scripts/validate_sources.py` (machine-checked monthly)
<!-- ==== GENERATED:END metro-facts ==== -->

## Running & testing

```bash
# Run locally — any static server works; internet needed for live-API layers:
python3 -m http.server 8000    # then open http://localhost:8000/

# Behaviour gate (real Chromium boot via Playwright) — the main test:
npm install playwright@1.56.1 && npx playwright install --with-deps chromium
BASE_URL=http://localhost:8000/ node scripts/smoke_test.mjs   # serve first, then run

# Static gate (run after any data/app regeneration or app edit):
python3 scripts/validate_index.py index.html

# Generated-region gate: per-fork facts live ONCE in metro-worksheet.json;
# GENERATED regions are emitted from it. NEVER hand-edit a GENERATED region:
pip install -c scripts/requirements.txt jsonschema
python3 scripts/generate_metro_files.py            # regenerate in place
python3 scripts/generate_metro_files.py --check    # the CI drift gate

# Placeholder / localization gate (red until bootstrap; a standing guard after):
python3 scripts/check_template_placeholders.py
```

## Architecture: stable core + pluggable layer modules

The metro-agnostic engine inside `index.html` is fenced with `/* ==== ENGINE:BEGIN <name> ==== */ … ENGINE:END` markers and must stay **byte-identical across the fleet** — it ships as a hash-verified release artifact from the reference repo, pinned in `engine.lock.json` and spliced at deploy time (`scripts/apply_engine.py`); `.github/workflows/engine-bump.yml` answers each release with a validated bump PR. **Never edit inside an ENGINE fence** — a fork-local engine edit is overwritten by the next deploy's splice and reads as drift to every fleet check. Everything state-specific lives in the `METRO:BEGIN config` block (worksheet-generated) and the fork's own module code. The full contract is `docs/ENGINE_SYNC.md` (a verbatim fleet-shared copy — a change to it lands in every fleet repo or none).

A layer module is registered via `registerLayer({ id, group, label, overlay, query, render })`; families of similar layers use the fenced factory helpers (`registerPolygonLayer`, `registerIlgaChamber`, `registerNearestPointLayer`, `registerSchoolZone`). The starter modules section in `index.html` carries a commented crib of each. Two invariants pervade the code: the **stale-async guard** (`if (seq !== state.sequence) return;` after every await) and **per-layer failure isolation** (a layer's failure shows a Retry inside its own card, never breaks the others).

**Honesty rules (non-negotiable):** officeholder data is never guessed — where no verifiable roster source exists, cards link to the official body instead of inventing a name. External strings always render through `sanitize()`/`textContent`. Roster refreshes always land as PRs for human review (see `.github/workflows/update-congress-roster.yml` for the pattern), never as direct commits to main.

## Growing this fork

A new county or layer follows the reference repo's `docs/EXPANSION_GUIDE.md` — this repo intentionally does not carry its own copy (the stubs under `docs/` say where each lives). The working order that guide teaches: prove the source first (a live fetch you performed), ship the boundary and its officeholder sourcing in the same change, floor every scraped count, and record what a publisher does NOT publish in the Data gaps panel rather than guessing. When a layer ships, its row in `metro-worksheet.json` (`layers[]`, with a `source` block) is what puts it on the sources page and in every gate — a layer cannot ship without a provenance row.

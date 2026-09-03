# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

districtry Michigan: a single-file, dependency-light web app. Click a point in Michigan (or
search an address) and it reports every civic district containing that point and who
represents you there. It serves at **districtry.com/mi/** as a folder of the consolidated
districtry repo — following the Wisconsin/Iowa shape (`docs/EXPANSION_GUIDE.md` Part 2), not
the Illinois root-scripts shape. It ships four layers, the national tier every U.S. state can
serve from national publishers: **County** (83, from Census TIGERweb, identity-only),
**U.S. House** (13 districts, TIGERweb geometry joined to the public-domain
unitedstates/congress-legislators roster, refreshed weekly), and **Michigan Senate** /
**Michigan House** (38 and 110 districts, TIGERweb geometry joined to Open States' current-people
export).

**THE FLAGSHIP LAYER THIS INSTANCE IS BUILT TOWARD IS `county-commissioner`**, and it is the
reason Michigan was chosen as the fleet's sixth state ahead of four other candidates. The
Michigan Department of State's Bureau of Elections publishes **one statewide layer carrying
every county's commissioner districts** — `2021 County Commissioner Districts v25`, all 83
counties in a single query at
`gisagocss.state.mi.us/arcgis/rest/services/OpenData/boundaries/MapServer/10` — compiled from
the filings MCL 46.404/46.405 requires each county apportionment commission to make. That is
Wisconsin's LTSB shape (a statutory filing mandate producing one current statewide aggregate)
rather than Illinois's county-by-county grind, and unusually **the same records carry the
commissioner's own name and party**, derived from the canvassed November 2024 election. Its AGO
item states its licence outright: "this dataset is a public record and…there are no
restrictions on the use, reproduction, or distribution of this dataset". None of that ships
yet — a roster attached to a boundary is refreshed when the boundary is, so the names get
their own verification rather than riding in on the geometry's coat-tails.

**TWO MEASUREMENTS FROM THE ARRIVAL BUILD ARE WORTH CARRYING FORWARD.** First, **TIGERweb's
congressional layer has rolled to the 120th Congress**: the district field is `CD120`, and a
query naming the retired `CD119` is not merely empty but REJECTED — HTTP 400, "Failed to
execute query". Michigan's builder names `CD120`; **the sibling instances' builders still name
`CD119` and would fail the same way on a rebuild**, which is a live finding rather than a
hypothetical (their shipped files are fine; only a re-run breaks). Second, **Michigan's county
fabric is WATER-INCLUSIVE**: every Great Lakes county's polygon runs out to the state water
boundary — Keweenaw County alone spans 2.57° of longitude, out past Isle Royale — so the two
peninsulas and every island dissolve into ONE ring, and a mid-lake click lands INSIDE coverage,
which is correct. A first draft of the outline builder's own docstring asserted "several rings,
two peninsulas plus islands" before the build was run and was wrong: **read the ring count from
`build_metro_outline.py --check`, never from a map in your head.**

**There is no build step, no framework, and no server-side code.** The app — styles, engine,
and layer modules — lives inline in `index.html`. `sw.js` is the service worker;
`data/app/*.json` are runtime-fetched data files; `data/state/` carries the bootstrap state
config (`build_congress_roster.py` reads its FIPS/USPS/seat count — it ships in the repo and is
excluded from the Pages deploy). `sources.html` carries the generated per-layer provenance
matrix and `faq.html` the common questions; both compose from the same shared engine blocks as
every other instance via `scripts/compose_app.py`.

<!-- ==== GENERATED:BEGIN metro-facts ==== -->
**Metro facts** (generated from `metro-worksheet.json` — edit the worksheet and run
`python3 scripts/generate_metro_files.py`; hand-edits here fail CI):

- Metro: Michigan (`michigan`) — https://districtry.com/mi/
- Geocoders: address Photon (Michigan-bounded type-ahead); unbounded Photon (whole-coverage, sibling-metro lookup); POI Nominatim (office-address pin lookup, Michigan-bounded, serial >=1s queue)
- Ground truth: 42.73370,-84.55530 (the Michigan State Capitol, downtown Lansing (Ingham County)) → county Ingham County; us-house 7; mi-senate 21; mi-house 77. Negative point 41.65280,-83.53790 (downtown Toledo, Ohio — south of the Michigan line and inside permalink_gate's minLat (41.55), so the point is still selectable; measured to miss all four layers).
- Layers: 4 registered (political 3, geography 1); `registerLayer(` floor 4. Debug namespace `window.MichiganExplorer`.
- Scheduled workflows: `update-mi-congress-roster.yml` (Mon 15:30 UTC); `update-mi-legislature-roster.yml` (Tue 15:30 UTC); `mi-validate-sources.yml` (1st of month 16:00 UTC).
- Source registry: `mi/scripts/validate_sources.py` (machine-checked monthly)
<!-- ==== GENERATED:END metro-facts ==== -->

## Running & testing

```bash
# From the REPO ROOT — one server, every instance:
python3 -m http.server 8000    # then open http://localhost:8000/mi/

# Behaviour gate (real Chromium boot via Playwright) — the main test:
npm install playwright@1.56.1 && npx playwright install --with-deps chromium
BASE_URL=http://localhost:8000/mi/ node mi/scripts/smoke_test.mjs

# Static gate (run after any data/app regeneration or app edit):
python3 mi/scripts/validate_index.py mi/index.html

# Coverage-wash gate (anchors + envelopes, offline against the shipped file):
python3 mi/scripts/build_metro_outline.py --check

# Generated-region gate: per-instance facts live ONCE in mi/metro-worksheet.json;
# GENERATED regions are emitted from it. NEVER hand-edit a GENERATED region:
pip install -c scripts/requirements.txt jsonschema
python3 scripts/generate_metro_files.py            # regenerate in place (all instances)
python3 scripts/generate_metro_files.py --check    # the CI drift gate

# Engine parity: the ENGINE fences are composed from the repo-root engine/ —
# edit a block THERE and recompose, never inside an instance file:
python3 scripts/compose_app.py            # splice engine/ into every instance
python3 scripts/compose_app.py --check    # the CI drift gate
```

**Sandboxed environments (Claude Code web):** the headless browser cannot reach the Leaflet
CDN. The repo root's `.claude/settings.json` SessionStart hook runs `scripts/vendor_leaflet.sh`,
which vendors Leaflet into `mi/scripts/vendor/leaflet/` (gitignored);
`mi/scripts/smoke_test.mjs` serves it same-origin. Production and GitHub Actions CI reach the
CDN directly.

## Architecture: stable core + pluggable layer modules

The metro-agnostic engine inside `index.html` is fenced with
`/* ==== ENGINE:BEGIN <name> ==== */ … ENGINE:END` markers and is **composed from the single
copy under the repo root's `engine/`** by `scripts/compose_app.py` — there is no release
channel and no per-instance copy to drift. **Never edit inside an ENGINE fence in this file** —
edit the block under `engine/` (when the change is right for every instance) and recompose.
Everything Michigan-specific lives in the `METRO:BEGIN config` block (worksheet-generated) and
this instance's own module code, between the `chamber-factory` and `hover-explorer` fences.

A layer module is registered via `registerLayer({ id, group, label, overlay, query, render })`;
this instance's three chamber layers use the fenced factory helper `registerIlgaChamber` (the
generic chamber factory both state chambers and the U.S. House card use). Two invariants
pervade the code: the **stale-async guard** (`if (seq !== state.sequence) return;` after every
await) and **per-layer failure isolation** (a layer's failure shows a Retry inside its own card,
never breaks the others).

**Honesty rules (non-negotiable):** officeholder data is never guessed — where no verifiable
roster source exists, cards link to the official body instead of inventing a name. Both chamber
cards degrade to the district number + the chamber's own directory on a roster miss; the county
card carries no roster at all and **says so on the card**, because Michigan's commissioner
districts ship as their own change rather than half-joined here. External strings always render
through `sanitize()`/`textContent`. Roster refreshes always land as PRs for human review —
never as direct commits to main.

## Data pipeline

Pre-built layers ship as same-origin `data/app/` files, all rebuilt from a live fetch by an
operator script: `metro-outline.json` (the whole-state outline for the coverage wash,
`mi/scripts/build_metro_outline.py` — one INSIDE anchor per county, each an area-weighted
centroid verified interior against that county's own rings), `state-counties.json`
(`mi/scripts/build_state_counties.py`), and `congress-districts.json`,
`mi-senate-districts.json`, `mi-house-districts.json`
(`mi/scripts/build_legislative_boundaries.py` — statewide TIGERweb, mapshaper-simplified,
refused unless the 2,000-random-point agreement gate passes; all three built at 100.00%
agreement with 0 overlaps). Rosters: `congress-roster.json`
(`mi/scripts/build_congress_roster.py`, from unitedstates/congress-legislators) and
`mi-{senate,house}-members.json` (`mi/scripts/build_mi_legislature_roster.py`, from Open States
`mi.csv`, with the Senate enriched by `mi/scripts/mi_senate_scraper.py`) — all count-guarded,
all refreshed weekly by CI as reviewed PRs.

**THE TWO CHAMBERS CARRY DIFFERENT CONTACT DEPTH, AND IT IS MEASURED.** Open States publishes no
capitol phone or address for ANY Michigan legislator (0 of 148, measured 2026-09-03), so every
contact detail has to come from the chambers themselves. The Senate's own all-senators
directory carries a Capitol phone, e-mail, office building and contact page for all 38 seats —
and it is worth knowing HOW: the roster is an HTML-escaped `senatorInfo` attribute feeding a Lit
component, not a `var senatorInfo = [...]` assignment, so a parser written against the obvious
shape returns nothing. `house.mi.gov` could not be reached from this project's build environment
at all (TLS: "unable to get local issuer certificate", with the egress proxy's CA bundle
explicitly supplied, while `senate.michigan.gov` answers 200 on identical flags) — the
incomplete-chain shape this repo already documents for Coles, Gallatin and Vermilion, but
**whether it is the site's own chain or an artifact of this sandbox is UNRESOLVED** and owes one
CI-side probe before it is recorded as anything more. See `WATCH.md`.

## Growing this instance

A new layer or county-level concept follows the repo's `docs/EXPANSION_GUIDE.md` and this
instance's own `docs/MI_EXPANSION_PLAN.md`. The working order those documents teach: prove the
source first (a live fetch you performed), ship the boundary and its officeholder sourcing in
the same change, floor every scraped count, and record what a publisher does NOT publish rather
than guessing. When a layer ships, its row in `mi/metro-worksheet.json` (`layers[]`, with a
`source` block) is what puts it on the sources page and in every gate — a layer cannot ship
without a provenance row. Extend `LAYER_SIDEBAR_RANK` and `WATCH.md` in the same change.

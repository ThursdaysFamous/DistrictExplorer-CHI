# districtry Iowa — Deployment Phase 1: arrival

> Planning document, researched and verified 2026-08-27. `docs/archive/WI_PHASE2_PLAN.md` is the
> precedent for a committed phase plan; like it, this file moves to `docs/archive/` when phase 1 ships
> and the shipped state (`ia/metro-worksheet.json`, `ia/CLAUDE.md`, the guidebook's Iowa column)
> supersedes it. Sources marked **VERIFIED** were fetched 2026-08-27 — endpoint, count, licence and
> failure mode recorded from the response, not a catalog page; four of the load-bearing ones were
> independently re-fetched a second time while writing this document (§ Appendix, "re-verified"). Facts
> marked **ASSERTED** are Iowa civic-structure claims (statutory citations, office titles, election
> mechanics) carried from the research pass without a second independent fetch in this session — they
> read as true and are consistent with what was verified, but each must be pinned to a primary citation
> in the PR that ships it, per `docs/EXPANSION_GUIDE.md`'s honesty rules.

## Context

The fleet is four state instances as of 2026-08-27: Illinois (91 counties, reference implementation),
NYC, SF, and Wisconsin (31 layers across four phases, arrived in place 2026-08-25).
`docs/EXPANSION_GUIDE.md` was rewritten around the STATE instance after Wisconsin's fourth phase and
names Wisconsin the worked example for state N+1: fill the worksheet first (§2.1), ship the national
tier first (§2.3 step 4 — TIGERweb + USGS National Map + `unitedstates/congress-legislators`, "~12
honest layers before you have asked anybody for anything"), decide the roster from the concept matrix
and drop rather than fake where no honest analog exists (§2.3 step 5), ship officeholder sourcing WITH
each boundary in the same change (rule 4, never deferred), and follow the WI shape — own
`ia/scripts/`, own `ia/metro-worksheet.json`, own `ia/CLAUDE.md`/`WATCH.md` — not the Illinois
root-scripts shape (§0.1: "a new state follows the WI shape, not the IL one").

This document plans **Phase 1: arrival** in full PR-by-PR detail, and Phases 2–4 at roadmap altitude
(each opens its own refreshed plan PR, with its own measured ledger, when it begins — the
`WI_PHASE4_PLAN.md` pattern, including that phase's own "what this phase deliberately is not"
section). Phase 1 takes Iowa from nothing to **10 statewide layers**.

## The thesis: why Iowa's arrival differs from Wisconsin's

Wisconsin's arrival keyed on exactly one state-publisher layer: LTSB's statewide county-supervisory
aggregate, shippable because Wis. Stat. 5.15(4)(br) forces every county to file its district plan with
the state twice a year. **Iowa arrives with an entire state-published local-election fabric already
sitting on one ArcGIS organization.** The Iowa Legislature's own account
(`services.arcgis.com/vPD5PVLI6sfkZ5E4`, `legis.iowa.gov`'s GIS) publishes, statewide, as a single
family of feature services: precincts (1,660), county supervisor districts for **all 99 counties, each
county's own election-plan type carried in-band** (266 features — VERIFIED, re-fetched this session),
school-board director districts (728), and polling places (1,386 points). The Department of Education
account on the same organization publishes current school districts (324, item touched the day this
document was written), school buildings (1,321), community-college merged areas (15) and their elected
director districts (123). A third, older account (`LSAFiscal`) publishes judicial districts (8) and
judicial election sub-districts (14).

The trade-off, carried through every phase of this plan: **none of these items states a licence**
(`licenseInfo` is null on every one checked — VERIFIED on the flagship layer, re-fetched this session;
licence capture or an ask is step zero on each), **vintages are uneven and at least one is already
stale** (the supervisor layer's own edit timestamp is 2024-01-30 — VERIFIED, re-fetched this session —
which predates **Senate File 75**: signed by Gov. Reynolds 2025-04-11, it forces Story, Johnson and
Black Hawk counties from at-large to district-based supervisor elections for the November 2026 cycle;
litigation over the maps is active as of this writing — VERIFIED via web search this session, three
independent news sources), and **several of the surfaces this plan needs — `sos.iowa.gov`,
`iowacourts.gov`, `data.iowa.gov` — return 403 from this sandbox while `legis.iowa.gov` and every
ArcGIS endpoint answer plain**. Per the fleet's own standing rule ("a measurement is not a
conclusion" — `docs/EXPANSION_GUIDE.md` §0.4 item 6), every one of those blocks gets one CI-side probe
before it is recorded as anything more than sandbox-side — Wisconsin's WEC block turned out to be
exactly that (PR 5, `docs/WI_PHASE4_PLAN.md`: "the block is sandbox-side, not WEC-side").

## Scope decisions

- **Phase 1 is statewide-first, national-tier-plus-one-flagship, exactly the WI shape.** Ten layers:
  the three chambers, county, the one state-publisher flagship (`county-supervisor`), the school and
  geography identity tiers, ZIP, post office.
- **The supervisor layer's per-county election-plan type ships in the card copy, not just the
  geometry.** Iowa Code lets each county elect its board under plan 1 (at-large), plan 2 (residence
  district, elected countywide) or plan 3 (single-member district) — ASSERTED, Iowa Code ch. 331,
  Div. II Part 1, to be pinned to exact section numbers in the PR. The layer's own `PLANTYPE` field
  (VERIFIED present) makes this a per-county fact the card can state honestly rather than a
  fleet-wide assumption.
- **No supervisor, school-board, or township-trustee roster ships in phase 1.** No statewide source
  for any of the three was found in the research pass; each is a recorded gap from day one, not a
  silent absence discovered later.
- **City tiers (Des Moines, Cedar Rapids) are phases 3–4, not phase 1** — mirrors WI's
  operator-confirmed "statewide only" call in its own phase 2 plan.
- **The elementary/secondary school-district tilings are a recorded drop, not a missing layer.**
  TIGERweb School layers 1 and 2 return zero features for Iowa (STATE='19') — Iowa runs unified
  districts only. The guidebook records this as a measured zero, not a gap.

## Conventions binding every PR

Scripts `ia/scripts/build_ia_*.py` / `ia_*_scraper.py`; workflows
`.github/workflows/update-ia-*.yml`, **every one `ia`-prefixed with no exceptions** — Wisconsin's
`update-mps-school-board-roster.yml` / `update-mpd-captains-roster.yml` shipped without the `wi-`
prefix and collided with the pre-consolidation Illinois naming convention; Iowa does not repeat it,
including for city-tier workflows in later phases (`update-ia-dsm-council-roster.yml`, never
`update-dsm-council-roster.yml`). `BOT_PR_TOKEN`, fixed `bot/ia-*` branch, PR-never-push. Every layer
gets a worksheet `source` block (the generator refuses otherwise), a `LAYER_SIDEBAR_RANK` slot, a
`validate_sources.py` row, a `WATCH.md` row, and guidebook coverage-map + matrix + inventory updates in
the same change. GENERATED regions and ENGINE fences are never hand-edited — all module code is
fork-side, added via `ia/index.html`'s own `registerLayer`/factory calls, never inside an
`ENGINE:BEGIN/END` fence. Scraped strings render through `sanitize()`/`textContent`. The officeholder
story ships with each boundary — a roster, or a recorded gap, never silence.
`min_register_layer` only rises. Files inside `ia/data/app/` are named `ia-*`, never `iowa-*` (see
Traps, below).

---

## PR 0 — scaffold + four national-tier layers

> **Corrected 2026-08-27, in the same change that shipped it.** This document originally planned PR 0
> as a layer-less scaffold, deferring the first layer to a separate "PR 1". Direct verification of
> `schema/metro-worksheet.schema.json` against that plan, done while starting the implementation,
> found it unbuildable: `layers` requires `minItems: 1` and `anchors` requires `minItems: 3` (each
> anchor must reference a real registered layer id), independently confirmed by
> `scripts/build_landing_page.py`'s `instance_layer_count()`, which refuses an empty `layers[]`. A
> layer-less scaffold cannot pass `generate_metro_files.py --check` — the PR's own CI gate — so it was
> never a shippable PR 0. This section folds the originally-separate "PR 0" (scaffold only) and "PR
> 1–4" (four layers, below) into the single PR that actually shipped: the scaffold bundled with the
> four simplest, most uniform phase-1 layers — `county`, `us-house`, `ia-senate`, `ia-house` — all
> pre-built, statewide, and TIGERweb-sourced. The project's own convention is to fix a wrong record in
> the same change that disproves it, not as separate follow-up work; the old separate PR 1/2/3/4
> headings below are retired along with the layer-less PR 0 they depended on. PR numbering for
> everything from `county-supervisor` onward (still "PR 5") is unchanged — only the four PRs this
> section absorbs are renumbered, so every downstream cross-reference elsewhere in this document and
> in `ia/CLAUDE.md`/the guidebook's Iowa section (both of which cite "phase 1 PR 5" for
> `county-supervisor`) still resolves.

Creates `ia/` from the `wi/` shape (§0.1: a new state follows Wisconsin's structure, not Illinois's
root-scripts structure) — `index.html` composed by `scripts/compose_app.py` from `engine/` with an
`ia/` `METRO:BEGIN config` block, `sw.js`, `CLAUDE.md`, `WATCH.md`, `ia/metro-worksheet.json` filled
per §2.1, and `ia/scripts/` scaffolded with `validate_index.py` + `smoke_test.mjs` (both carrying
`GENERATED:BEGIN validator-config`/`smoke-config` regions populated from the worksheet's four layers
from the start, not left empty) + `validate_sources.py` (9 PROVENANCE rows across the four layers).

**Fleet registration, done dark in this PR** (§2.4's day-one list, run mechanically, all gated by
`--check`) — **with one resolved design decision that departs from the original plan**: direct
verification of `render_cards()` (`scripts/build_landing_page.py`) and `sync_fleet()`
(`scripts/generate_metro_files.py`) showed neither filters a dark/unpublished fork — every
`metros.json` entry renders as a live, clickable landing-page card regardless of the Pages deploy
excludes. Adding `iowa` to `metros.json` in this PR, even with `ia/` excluded from the deploy, would
therefore publish a card linking to a 404. **So, unlike the original plan text (and unlike the
`metros.json` JSON shown in the Worksheet section below, which is the entry a later go-live PR adds),
this PR does NOT touch `metros.json` and does NOT run `--sync-fleet`.**
`ia/metro-worksheet.json`'s `metro_explorers` is instead hand-seeded with the four existing siblings'
entries (copied from any current worksheet's array), which is exactly what `--sync-fleet` would
produce once `iowa` is added — deferred to the go-live PR (still "PR 10").
- `scripts/generate_metro_files.py` `INSTANCES` gains an `ia` row; `scripts/compose_app.py`
  `INSTANCES`/`SUBPAGES` gain `ia` rows.
- `scripts/build_landing_page.py` `INSTANCE_WORKSHEET` gains the `ia` → `ia/metro-worksheet.json`
  mapping — needed even while `ia` stays out of `metros.json`, since this is what lets a later
  `instance_layer_count("ia")` call resolve once `iowa` is eventually added.
- `scripts/build_manifests.py`, `scripts/build_history_page.py`, `scripts/build_brand_tokens.py`
  (`FACE_CARRIERS`) each gain their `ia` row.
- `scripts/vendor_leaflet.sh` bash `INSTANCES` array gains
  `"ia:ia/index.html:ia/scripts/vendor/leaflet"` — so the SessionStart hook vendors Leaflet/MapLibre
  for `ia/` in every sandboxed session from this PR forward, not retrofitted later.
- `.github/workflows/smoke-test.yml` gains the `ia/scripts/validate_index.py ia/index.html` and
  `BASE_URL=http://localhost:8000/ia/ node ia/scripts/smoke_test.mjs` lines, plus
  `python3 scripts/build_coverage_gaps.py --check --metro iowa --out ia/data/app/coverage-gaps.json`
  — **CI runs against `ia/` from PR 0 onward**, not after a dark period, so a broken layer is caught
  the day it lands rather than at go-live.
- `.github/workflows/deploy-pages.yml` EXCLUDES gains one blanket line, `ia/**` — nothing half-built
  publishes, and (per the resolved decision above) `ia` staying out of `metros.json` means the
  fleet-status/landing-page machinery never expects it live either; PR 10 (go-live) narrows the
  exclude to the granular set the other three instances use and adds the `metros.json` entry together.
- **`.github/workflows/ia-validate-sources.yml` is created in this PR**, cloned from
  `wi-validate-sources.yml` (monthly, staggered cron, its own tracking issue). Wisconsin's equivalent
  workflow did not exist on day one — its own phase-2 plan recorded this as discrepancy #4 ("the
  workflow existed complete and nothing scheduled it"). Iowa does not repeat it.
- **`history_page` is set in the worksheet from this PR**, not backfilled later (Wisconsin's `history_page`
  key was added only in phase 4, with three phases of changelog entries written after the fact from
  git history). Entry 1: "Launched — the national tier: county, U.S. House, Iowa Senate, Iowa House."

**The four layers**, all pre-built and TIGERweb-sourced (`ia/scripts/build_state_counties.py` for
`county`, `ia/scripts/build_legislative_boundaries.py` for the three chambers — `DEFAULT_TARGETS` must
list all three explicitly, unlike Wisconsin's builder, which omits `us-house` because WI's
`congress-districts.json` came from the now-deleted bootstrap script; Iowa has no such bootstrap step):

- **`us-house` (4)**: TIGERweb `Legislative/MapServer/0`, `STATE='19'` — VERIFIED, count 4. Roster:
  `unitedstates/congress-legislators` (`legislators-current.json`, CC0), the fleet-standard loader
  every instance already carries. Weekly workflow `update-ia-congress-roster.yml` (Mon 14:30 UTC).
- **`ia-senate` (50)** and **`ia-house` (100)**: TIGERweb `Legislative/1` and `/2`, `STATE='19'` —
  VERIFIED. Each Senate district contains exactly 2 House districts (ASSERTED — Iowa Code
  42.4-adjacent apportionment provision; the build gate proves it structurally against the shipped
  geometry rather than trusting the citation). Roster ships with both boundaries, in this same PR
  (rule 4): `data.openstates.org/people/current/ia.csv` (VERIFIED, same column shape as Wisconsin's
  `wi.csv`) merged with each member's own `legis.iowa.gov` profile page (VERIFIED server-rendered
  plain HTML, name/district/party/county/email plus a per-member page carrying Capitol phone —
  Iowa's site has no single listing page with every member's contact block the way Wisconsin's does,
  so each of the ~149 current members needs its own page fetch). One weekly workflow,
  `update-ia-legislature-roster.yml`, feeds both layers' rosters (Tue 14:30 UTC). Floors set from the
  verified 50+100 seat counts.
- **`county` (99)**: TIGERweb `State_County/MapServer/1`, `STATE='19'` — VERIFIED, count 99. Identity
  card only in phase 1 (no statewide auditor roster yet — that ships in phase 2 alongside `precinct`).

`min_register_layer` → 4.

**Localization sweep** (§2.7), run at the end of this PR and again before go-live: grep the new tree
for `wisconsin`, `Wisconsin`, `WisconsinExplorer`, `Marathon`, `LTSB`, the `🧀` emoji, and Wisconsin's
GoatCounter tag, across `index.html sw.js README.md CLAUDE.md WATCH.md manifest.webmanifest scripts/
.github/`. **Run it scoped to `ia/` only** — a sweep for the string "iowa" run carelessly across the
whole repo, rather than confined to the new tree, returns false positives from
`wi/data/app/iowa-county-outline.json` and `wi/data/app/iowa-polling-places.json`, which are Iowa
**County, Wisconsin** (see Traps).

---

## PR 5 — `county-supervisor`: the flagship, 270 features / 98 of 99 counties

> **Shipped 2026-08-27.** Re-verification at execution time found the plan's own count was an
> ASSERTED estimate that didn't survive contact with the live layer: the state's aggregate carries
> **266** features across **98**, not 99, counties — Jones County is entirely absent (measured by name
> AND by its own FIPS code 105, not a naming mismatch), a gap this section's original text never
> anticipated. Black Hawk's reconciliation found MORE than the plan asked for: not just an adopted
> plan to cite, but a live, county-hosted ArcGIS feature service with real, current 5-district
> geometry (`BlackHawkCoSupervisor_LSAplan1`), which ships as ordinary `PLAN 3` data rather than the
> planned "currently effective at-large form with a dated note" fallback. Story and Johnson got that
> fallback, refined: each ships as one county-level feature (PLANTYPE `TRANSITIONING`, not the at-large
> plan-1 form — their old at-large rows are dropped entirely, not retained) carrying their SOS-approved
> plan's real facts. Final shipped count: 270 features (263 kept from the state aggregate + Black
> Hawk's 5 + Story's 1 + Johnson's 1), 98 counties, Jones recorded as gap `jones-county-supervisor` in
> `docs/DATA_LAYER_GUIDEBOOK.md`. The board-size directory needed a source this section didn't specify
> — Iowa counties share no domain convention, so `ia_county_directory_scraper.py` reads all 99 (including
> Jones, whose own site is real even though its geometry isn't shipped) from the Iowa State Association
> of Counties' member directory rather than guessing a pattern.

> **OUTCOME UPDATE 2026-09-05 — STORY'S PLACEHOLDER IS RETIRED, and the count above moves
> 270 → 272.** Step 2's "currently effective at-large form with a dated note" fallback was
> always meant to be temporary, and Story's ended by reading the county Auditor's own printed
> district map: three closed stroke path objects at linewidth 12 (the only curves on the page
> at that weight out of 10,761 under pdfplumber 0.11.10 — an earlier pass published 10,235
> and it was wrong), one legend-declared numeral inside each, georeferenced to
> NAD83 / Iowa North — which the drawn aspect ratio identifies to five digits, and which fits
> the county's real outline to 0.6 m mean / 2.0 m max — then resolved to whole Census 2020
> blocks so nothing traced ships. **The gate is a different county product and it is exact**:
> the derived populations reproduce the Legislative Services Agency's published
> 32,783 / 32,894 / 32,860 district by district in order, and a negative test with the labels
> for districts 2 and 3 swapped passes every other gate and fails only this one.
> **A CORRECTION TO THIS PROJECT'S OWN RECORD went with it**: an earlier pass had called the
> map's 1,584 FILLED curves "the Jackson precondition". None of them is a district (largest
> 2.63% of the page); they are lakes, parks and city fills. Reading the FILLS would have found
> nothing — **read the path OBJECTS, never the pixels** is the rule that survived.
> Story keeps PLANTYPE `TRANSITIONING`, not `PLAN 3`: the lines are adopted and first elect in
> November 2026, and the board sitting now is still at-large, so `ia-supervisor-members.json`
> correctly keys no supervisor to a Story district. **JOHNSON IS UNCHANGED** and now carries
> its own gap record (`johnson-county-supervisor-districts`); its recorded source URL, which
> ia/WATCH.md had called dead, answers 200 — the original probe hit a different path read from
> a truncated string in tool output.
>
> **REVIEW FOLLOW-UP 2026-09-05 — two of this entry's own claims were wrong and a second
> gate went in.** (a) **THE LSA PUBLISHED TWO PLANS.** The First (2025-12-04) gives
> 32,783 / 32,894 / 32,860; the Board REJECTED it on 2026-01-06 "based on compactness of
> districts"; the Second (2026-01-14) gives 32,940 / 32,793 / 32,804 and reshuffles the
> county completely. Iowa Code 331.210A(2)(d) lets the Board then approve either or an
> amendment, and its 2026-01-27 approval does not say which — the geometry does, matching the
> First exactly and none of the Second. Both directions are now gated, and the citation names
> the document rather than "the ledger". (b) **STORY'S DISTRICTS DO NOT SPLIT A PRECINCT.**
> Iowa Code 49.3(2)(1) makes district boundaries follow precinct boundaries and the First
> Plan lists Roland/Howard Twp whole in District 2. What the block sort divided is the
> SHIPPED precinct polygon, still carrying its 2020 census voting-district geometry (IoU
> 0.999573 against `HOWARD TWP W/O STORY CITY`, POP100 1,869 = 1,837 + 32); the county
> re-precincted 43 → 45 and only 6 of 45 shipped Story precincts still match a voting district
> that closely. Blocks were still the necessary unit — now for a better reason. (c) A SECOND
> GATE dissolves the First Plan's own precinct lists out of `ia-precincts.json` (45/45 names
> match after zero-padding and one suffix alias) and lands on the map-derived districts at
> worst IoU 0.99127. (d) `rnd()` never rounded — `shapely.mapping()` emits TUPLES and it
> handled list/dict only — so the committed source shipped 15-decimal coordinates, 225,722
> bytes against 172,833. **The app file was never affected**, because mapshaper re-rounds at
> `precision=0.000001`; rebuilding the aggregate after the fix changed zero features and zero
> properties.

**Geometry — VERIFIED and re-verified this session**:
`services.arcgis.com/vPD5PVLI6sfkZ5E4/arcgis/rest/services/CountySupervisorDistricts/FeatureServer/0`.
This session's own fetch confirms: 266 features; fields `COUNTY, DISTRICT, NAME, PLANTYPE,
NUMDISTRICTS, MEMBERS, CODIST_ID, CONO, FIPS, AREA, TOTAL, IDEAL_VALU, DEVIATION`; `licenseInfo` not
present in the service metadata (attribution-only posture — capture the organization's stated terms
before shipping, the DPI reference-use-disclaimer precedent); last edit timestamp `1706643533798` =
**2026-01-30 2024** (i.e. **2024-01-30** — the layer is roughly two and a half years old at Iowa's
projected ship date).

**The card's honesty contract, driven entirely by the layer's own `PLANTYPE` field** (no fleet-wide
assumption): plan 3 counties (single-member districts, ASSERTED ≈39–40 of 99 per the research pass,
re-count at build) → "Your district elects one supervisor"; plan 2 counties (residence districts,
elected countywide, ASSERTED ≈16 of 99) → "This district is drawn for residence; supervisors are
elected countywide" — the card must not imply a plan-2 reader's vote is confined to their district;
plan 1 counties (at-large, ASSERTED ≈44 of 99, one county-wide feature each) → "Elected at large."
Board size (`NUMDISTRICTS`/`MEMBERS`) is read back from the same file, the WI county-board-directory
pattern (`build_ia_county_board_directory.py --check`, cloned from
`build_wi_county_board_directory.py`).

**The staleness gate — this PR's real work.** Senate File 75 (signed 2025-04-11, **confirmed this
session by independent web search across three news sources**: The Gazette, KCRG, Johnson County's own
website) forces **Story, Johnson and Black Hawk** counties from plan 1 to plan 3 for the November 2026
election; the shipped layer still carries all three as plan-1 rows as of its January 2024 vintage. The
builder (`build_ia_supervisor_districts.py`) must reconcile before writing:
1. Pull the three counties' new district plans from LSA's county-redistricting ledger
   (`legis.iowa.gov/publications/legalPubs/countyRedistricting` — VERIFIED to exist, 47 documents,
   Iowa Code 331.210A cited) — Johnson's plan is SOS-approved as of 2026-01-07 per the research pass;
   Story's first submitted map was rejected by its own board 2026-01-06, a second LSA letter followed
   2026-01-14, and litigation over the maps is active — the builder must gate on **finding an
   SOS-approved (not merely LSA-drafted) plan** for each of the three before treating it as current,
   and ship the count/board-size fact even where the exact line geometry is still in dispute, per
   this project's "over-claim rather than under-claim absence" convention only where county
   granularity genuinely can't express the truth — here it can (each county is its own feature), so
   the honest move is the pinned-source override, not a guess.
2. Where a county's SOS-approved plan cannot yet be confirmed, ship it under its **currently effective**
   at-large form with a dated note ("supervisor districts as of [layer date]; [county] is transitioning
   to district elections for November 2026 under Senate File 75 — see [SOS/county source] for the
   adopted map") rather than silently carrying the stale plan-1 geometry as if uncontested.
3. Gate: exactly 99 counties represented; every `PLANTYPE` value one of the three known strings; the
   three SF-75 counties specifically diffed against the ledger on every rebuild (a `KNOWN_TRANSITIONING`
   pin, the Madison TID pattern from `docs/WI_PHASE4_PLAN.md` PR 4 — any change to their status fails
   the build for a human look, rather than silently drifting).

No statewide supervisor roster exists (measured-no, research pass) → the coverage-key middle band
states it ("The state publishes every county's districts; no state source names who holds each seat"),
and the county-by-county attrition route is phase 4 work, not this PR's. Bookkeeping: worksheet source
block naming both LSA and the county-redistricting ledger; area rank placed after `county`; sidebar
rank; `validate_sources.py` row; guidebook new concept row ("County supervisor district (plan-type
aware)"); `min_register_layer` → 5.

## PR 6 — `school-district-unified`: 325 (TIGER) reconciled against 324 (DE)

> **Shipped 2026-08-27.** The one-district gap named itself precisely, and the plan's own guess at the
> cause ("most likely a district consolidation TIGER's vintage hasn't caught") was right: diffing the
> DE's current layer against last year's found **Orient-Macksburg Community School District** dissolved
> into **Nodaway Valley Community School District** for 2026-2027 — confirmed by the DE's
> `CurrentIowaSchoolDistricts` and newest year-versioned layer both being edited within two minutes of
> each other on the day this shipped, and by spatially sampling ten points across Orient-Macksburg's old
> boundary, all ten landing inside Nodaway Valley. TIGERweb's 325 dissolves to 324 in the builder
> (mapshaper `-dissolve` on a shared key), carrying Nodaway Valley's own identity forward rather than
> inventing a merged name. The DE layer's own naming needed one recorded exception rather than a
> broader rule: it drops "Independent" for WEST BURLINGTON but keeps it for MARION INDEPENDENT.

TIGERweb `School/MapServer/0`, `STATE='19'` — **VERIFIED, this session's research pass: 325.**
Cross-witness: Iowa Dept. of Education's `CurrentIowaSchoolDistricts` layer on the same state ArcGIS
organization — **VERIFIED, item touched the same day this document was written: 324.** The one-district
gap is named and resolved in the builder before shipping (most likely a district consolidation TIGER's
vintage hasn't caught — the builder names which district differs between the two counts and which
source wins, rather than silently picking the higher number). `School/MapServer/1` (secondary) and
`/2` (elementary) both return **zero** for Iowa — a measured drop, recorded in the guidebook as
"n/a — Iowa runs unified districts only," not left as an unexplained gap. Boards are elected (at-large
or by director district, varies by district — the director-district geometry itself is phase 3's
`school-director-district`); no statewide board-member roster exists → identity + district link, no
roster, exactly the WI `school-district-unified` precedent. Bookkeeping as above;
`min_register_layer` → 6.

## PR 7 — `county-subdivision`: 1,663

> **Shipped 2026-08-27.** Re-verification at execution time confirmed the count exactly (1,663) and
> found its composition: **1,600 civil townships** (`LSADC` 44, `FUNCSTAT` G — an active government),
> **62 incorporated cities that double as their own subdivision record** (`LSADC` 25, `FUNCSTAT` F — the
> Census Bureau's own term for a "fictitious" bookkeeping placeholder filling the MCD void under a city,
> not a second government), and **one federal reservoir** carried as unorganized territory (`LSADC` 46,
> `FUNCSTAT` S — a statistical entity, not a government at all; Saylorville Reservoir). This ships as a
> **live** layer — no builder script, no committed `data/app/` file — reusing `tigerStatewideLoader`,
> which PR 0 had already scaffolded and left unused for exactly this. Per the WI-precedent anchor policy
> (pre-built, election-stable values only), it is deliberately **absent from `anchors[]`**. The card's
> type row is read from what TIGER's own `NAME` carries beyond `BASENAME` ("Brighton" + " township"),
> the same technique WI's `county-subdivision` card uses. Township trustees are elected (ASSERTED, Iowa
> Code ch. 359) with no statewide roster found; per the precedent set by `county`'s and
> `county-supervisor`'s own no-roster facts, this ships as **worksheet + card-copy prose**, not a formal
> `coverage-gaps.json` entry — that mechanism is for a per-area/county peer-comparison absence (Jones
> County's missing supervisor geometry), not a uniform, statewide "no source exists for this concept at
> all" fact. The 62 city-type and 1 UT-type records carry no roster claim at all, since they are not
> separate governments.

TIGERweb `Places_CouSub_ConCity_SubMCD/MapServer/1`, `STATE='19'` — **VERIFIED, research pass: 1,663.**
This is Iowa's civil-township fabric plus incorporated-place MCD records. Card carries an explicit type
row (the WI "City or Village vs County Subdivision" label lesson applied from day one rather than
re-learned). Township trustees are elected (ASSERTED, Iowa Code ch. 359) with no statewide roster found
→ recorded gap, never guessed. `min_register_layer` → 7.

## PR 8 — `municipality`, labeled "City": 939

> **Shipped 2026-08-27.** Re-verification at execution time confirmed the count exactly (939) and the
> single-legal-class claim: `LSADC` is uniformly `25` across all 939 records (no separate village/town
> class to distinguish), so the layer ships labeled **"City"** with no type row needed, unlike
> `county-subdivision`'s three-way split. This ships as a **live** layer, the same
> `tigerStatewideLoader` pattern PR 7 established — no builder script, no committed `data/app/` file,
> deliberately absent from `anchors[]`. The execution note's `data.iowa.gov` check was run: the host
> does **not** 403 from this sandbox (that recorded block did not reproduce — corrected rather than
> repeated), but the site itself, "Iowa Data Hub," turned out to be a **client-rendered Next.js catalog
> of state-agency datasets**, not a Socrata portal (`api.us.socrata.com`'s catalog API returns "Domain
> not found" for it) and not a municipal aggregator by its own description ("data collected, created,
> and maintained by **state agencies**"). Its catalog listing is rendered client-side with no
> discoverable backend API in its compiled JS, and this sandbox's Chromium cannot reach the host
> directly to render/search it live (the same CDN-proxy gap documented for Leaflet and TIGERweb) — so
> the search was not exhaustively completed, but the platform finding itself (not Socrata, not
> municipal-scoped) plus the fleet's own precedent (no other instance has ever found a single
> state-level source of city council rosters; Chicago's and Wisconsin's municipal-officials data are
> both built city by city) is enough to record the same "no statewide source" conclusion the plan
> predicted, now measured rather than assumed. Per-city rosters stay phase 3–4 work.

TIGERweb `Places_CouSub_ConCity_SubMCD/MapServer/4`, `STATE='19'` — **VERIFIED, research pass: 939
incorporated places.** Iowa incorporates only "cities" — no villages or towns as a separate legal
class — so the layer label ships as **"City" from day one**, skipping the mislabel-then-correct journey
Illinois's `municipality` layer went through. Empty state outside every incorporated place reads
"unincorporated township land," which is a true and complete answer given `county-subdivision` already
covers the township fabric. No statewide municipal-officials source was found in the research pass
(**both halves of that were re-measured on 2026-09-03 and one was wrong**: the League's own city
directory is NOT gated and publishes a phone for 935 of 948 cities while naming nobody, so it is a
shippable City-card improvement rather than a dead end; and the execution note's `data.iowa.gov`
check was run — the host answers 200 while `api.us.socrata.com` reports "Domain not found" for it,
so it is a client-rendered catalog of state-agency datasets and not a Socrata portal at all). Per-city rosters
are phase 3–4 work (Des Moines, Cedar Rapids) and a later per-county ladder, not phase 1.
`min_register_layer` → 8.

## PR 9 — `zip-code` and `post-office`

> **Shipped 2026-08-27.** Both live endpoints re-verified exactly as planned, with nothing to correct:
> the ZCTA envelope query measured **1,443** features in Iowa's bounding envelope and the USGS post-office
> structures query measured **1,170** points in the same envelope, both fetched by `tigerStatewideLoader`-
> and `makeCached`-based live loaders (no builder script, no committed `data/app/` file, deliberately
> absent from `anchors[]` — neither is a fixed count worth gating on, since an envelope query legitimately
> moves as ZCTA boundaries redraw or post offices open/close near the state line). Both layers ship at
> the exact code shape WI's own `zip-code`/`post-office` blocks use, cloned nearly verbatim with only the
> Iowa envelope substituted.

`zip-code`: ZCTA layer by Iowa envelope, no `STATE` field on that TIGERweb layer — envelope query,
verbatim the Wisconsin/Illinois pattern. `post-office`: USGS National Map
`carto.nationalmap.gov/.../structures/MapServer/38`, nearest-3, envelope query (deliberately catches
border-state post offices near the Iowa line — correct behavior, the WI precedent). Both fleet-standard
loaders, no new code beyond worksheet rows and layer registration. `min_register_layer` → 10.

## PR 10 — go-live

> **Shipped 2026-08-27.** The mechanical checklist below (deploy exclude, sitemap, sync-fleet,
> landing/privacy regeneration, history finalization) shipped exactly as planned — but making
> `/ia/` genuinely live surfaced six real defects the dark instance's own gates had no way to
> catch, since nothing had ever loaded these pages in a browser against the real sitemap before:
> **(1)** `ia/index.html`'s hand-authored JSON-LD (`WebSite`/`Organization`/`WebApplication`),
> its map `aria-label`, its empty-state teaser copy, and one code comment about the map's
> `minZoom` were all uncorrected copies of Wisconsin's own text, left over from the PR 0 clone —
> found by a `grep -rn "Wisconsin"` sweep of `ia/` run for the first time at go-live (the sweep
> `docs/EXPANSION_GUIDE.md` §2.7 calls for, which PR 0 evidently ran incompletely). Fixed to
> describe Iowa; the many other "Wisconsin"/"Chicago" hits in that sweep are legitimate —
> `METRO_EXPLORERS`' own sibling entry, or ENGINE-fenced shared-code comments citing a real
> fork as an example, never hand-edited. **(2)** `ia/faq.html` never existed — PR 0 deferred it
> as "new hand-authored content, not this PR's scope," and no PR since had reason to create it —
> so the sitemap row this PR was about to add would have been a live 404. Written now: ten
> Iowa-accurate Q&A pairs (mirrored exactly in FAQPage JSON-LD, matching every sibling's own
> count), composed from `wi/faq.html`'s shell via `scripts/compose_app.py` (newly registered in
> `SUBPAGES["ia"]`). **(3)** `ia/og-image.png` was referenced by `index.html`, `sources.html` and
> the new `faq.html` but was never generated — a 1200×630 placeholder now ships (violet ground,
> wordmark, tagline), the same "simple placeholder art, real branding later" posture PR 0 used
> for the app icons. **(4)** `ia/vendor/leaflet-maplibre-gl.js` (the same-origin MapLibre bridge
> plugin every other instance vendors for itself) was never committed — the app degraded silently
> to its raster-tile fallback, which is why no smoke test caught it. Copied byte-for-byte from
> `wi/vendor/` (confirmed identical across all four siblings). **(5)** `ia/fonts/` did not exist
> at all — all eighteen self-hosted Barlow/IBM Plex Mono `.woff2` files `index.html`, `faq.html`,
> `sources.html` and `history.html` each declare `@font-face` rules for were missing, so every
> Iowa page has been silently rendering in a browser's fallback font since PR 0. Copied from
> `wi/fonts/` (confirmed byte-identical across siblings). None of (2)-(5) tripped any existing
> gate because nothing before this PR ever served `ia/` pages against their real relative paths
> in a browser with the sitemap driving navigation — `page_consistency_test.mjs` is what finally
> caught all four, the moment `/ia/faq.html` and `/ia/history.html` first entered `sitemap.xml`.
> **(6)** `ia/history.html` — and, it turns out, the already-live `wi/history.html` — carried no
> Open Graph tags, no `.districtry-mark` brand element, and no "Why this exists" link, because
> `scripts/build_history_page.py`'s template never had them; every OTHER sub-page type
> (faq/sources) gets these from the shared `styles-subpage` ENGINE fence, but `history.html` uses
> its own bespoke, simpler template that was never given the same treatment. This was invisible
> for Wisconsin because `docs/IA_EXPANSION_PLAN.md` itself records that WI's own `history.html`
> was never added to `sitemap.xml` — so `page_consistency_test.mjs`, which walks the sitemap,
> had literally never visited a `history.html` page before this PR added Iowa's. Fixed at the
> generator (og:title/og:image/og:description, a small inline `.districtry-mark` SVG, the
> why-exists footer link), then regenerated — which correctly updated `wi/history.html` too,
> fixing the same latent gap on Wisconsin's own already-public page as a direct, desirable
> consequence of fixing the shared machinery at its root rather than hand-patching one output.

Swap the PR 0 blanket `ia/**` deploy exclude for the granular set the other three instances use
(`ia/data/state`, `ia/data/source`, `ia/scripts`, `ia/data/*.geojson`); add `ia` to the
`for published in ny ca wi; do test -f "_site/$published/index.html"` presence loop. Add `/ia/`,
`/ia/faq.html`, `/ia/sources.html`, and `/ia/history.html` to `sitemap.xml` — **Wisconsin's
`history.html` is missing from its own sitemap row; Iowa's go-live PR includes it rather than repeating
the omission.** Run `scripts/generate_metro_files.py --sync-fleet` so all five instances' worksheets
carry the new `metro_explorers` entry. Regenerate the landing page (new card, JSON-LD entry) and
`privacy.html` (Iowa's shipped `index.html` is measured for the fleet-gated analytics vocabulary and
`.toFixed(2)` coordinate rounding — both must already match by construction, since PR 0 composed
`ia/index.html` from the same `engine/` every instance shares). `history_page`'s "Launched" entry is
finalized with the real final layer count and date. Full verification battery (below) run clean before
merge.

---

## Phase 2 roadmap — statewide parity (+7; corrected 2026-08-28 against a live re-verification pass, own plan PR when it opens)

CORRECTED 2026-08-28 — the original research pass materially undercounted `police-station` and
`fire-station`: live-requerying `carto.nationalmap.gov/.../structures/MapServer/{53,51}` against
Iowa's own shipped `METRO_BBOX` returns **449 police points and 1,262 fire points**, not 53/51 (the
original figures read at roughly Chicago-metro-bbox scale, not statewide-envelope scale — a
methodology error, not a wrong endpoint). Both remain fleet-standard, licence-free (`licenseInfo`
null), no-roster nearest-N layers with the exact shape `post-office` already ships — **now PR 1 of
phase 2**, ahead of the three layers `ia/index.html`'s own sequencing comment assumed would go first.

`precinct` (`Iowa_Precincts/FeatureServer/0`, item id `d394edea208c4003ac1d6bd1ec78532f` on the LSA
org — CONFIRMED 1,660 features, `maxRecordCount` 1,000 so paginate, `licenseInfo` null, fields
confirmed including `PollingPlace`/`PollingPlaceAddr`/`PPID`, deliberately **withheld from the card**
until phase 4's dated-polling display contract is built). **A TRIPLE-DUPLICATE-SERVICE TRAP,
confirmed live**: two decoys exist at deceptively similar names — `IaPrecincts` on the separate
`LSAFiscal` org (1,651 features, titled "2022 Precincts", last edited 2022-08-30, stale) and a bare
`Precincts` service on the SAME org as the real one (1,689 features, no edit metadata, unexplained) —
**the builder must pin the item id, never search by service name.** PR 4.

**Shipped 2026-08-28 (PR 4).** The raw fetch (native precision, all 1,660 features) ran ~18 MB —
this instance's largest single source file by a wide margin, because precincts follow actual
parcel/road boundaries rather than county lines the way the chamber districts do. Cut to under 3 MB
(2,945,407 bytes) by the same Visvalingam `keep-shapes` mapshaper pipeline
`build_legislative_boundaries.py` established, adapted to precincts' `PCTID_TXT` key, gated at the
fleet's standard 2,000-random-point agreement check: 1999/2000 (99.95%) agreement, 0 multi-feature
overlaps. mapshaper reports 78 source self-intersections it cannot auto-repair, unchanged across
reruns — a property of the source digitization, not treated as fatal, since the point-agreement gate
is what actually proves correctness, not mapshaper's own repair log. The predicted name gap was
confirmed exactly as expected: `PctNameOfficial` is empty on 2 of 1,660 records (Warren County
precincts 91-1 and 91-31), recovered via a title-cased `Label` fallback (Label is populated on all
1,660 with no exceptions). Shipped `precinct` via `registerPolygonLayer` (compact, identity-only —
name + county, no roster: a precinct has no elected representative of its own). Polling-place fields
are withheld the strongest way available: `PollingPlace`/`PollingPlaceAddr`/`PPID` are never added to
the builder's `outFields` query parameter at all, so a future edit cannot add them to a card by
merely forgetting a display-only filter.

`ia-judicial-district` (8 whole-county unions). Iowa Code §§602.6107/602.6109, Code 2003 — CONFIRMED,
was ASSERTED, frozen by a transitional provision subject to a decennial Supreme Court review (next
possible redraw window opened 2012, none enacted — worth a one-line card/backlog note that the
composition is statutorily revisable, not frozen forever). **`iowacourts.gov` does NOT 403 this
sandbox** (corrected, not repeated — the Coles/data.iowa.gov pattern for a fourth time in this
fleet); per-district URL pattern confirmed `iowacourts.gov/iowa-courts/district-court/judicial-district-{N}/`,
and the "inconsistent slugs" trap is now characterized exactly: District 1's roster page is
`.../judges-and-magistrates-district-1/` (number-suffixed) where Districts 2 and 3 are
`.../judges-and-magistrates/` (bare) — a scraper must discover the slug per district, never assume one
pattern fleet-wide. **Buildable with NO new boundary fetch**: `ia/data/app/state-counties.json`
(shipped in PR 0, 99 features, GEOID/COUNTY/NAME) dissolves directly against a compiled
county→district table sourced from the Code citation, with the LSAFiscal `JudicialDistricts/FeatureServer/0`
(8 features, real polygons, `JUD_DIST`/`POP_2010` only, no county field — usable only as a spatial
third witness, never as the crosswalk itself) as the double-witness gate — mirroring Wisconsin's
`wi-circuit-court` build exactly (69 whole-county unions per Wis. Stat. 753.06, same
partition/containment-gate, double-witness shape), the closer fleet analog than Illinois's
judicial-subcircuit, which is a per-county-dispatch pattern Iowa's single-org geometry doesn't need.
Judges are RETENTION, never "elected" — the card must say so. PR 5.

**Shipped 2026-08-28 (PR 5).** The county citation didn't survive as predicted: the CURRENT codified
SS602.6107/602.6109 carry no county list at all (confirmed live — SS602.6107(3) freezes the "Code 2003"
composition in effect rather than restating it, and the legacy 2003 code archive at
`legis.iowa.gov/DOCS/IACODE/2003/...` returns connection failures from this sandbox on every URL
variant tried). The operative crosswalk instead comes from two independent CURRENT publishers who
agree exactly — iowacourts.gov's own per-district "District N Counties" page and Ballotpedia's compiled
table — and is spatially DOUBLE-WITNESSED at build time against the LSAFiscal organization's own REAL
published district polygons (not merely a text cross-check the way Wisconsin's `wi-circuit-court`
precedent needed, since Iowa actually has independently-drawn geometry to check against): all 99
counties' proven-interior anchor points confirmed inside the correct real district polygon, 0
mismatches. **The URL-pattern prediction was an undercount, not wrong**: verified live for all 8
districts, there are THREE shapes, not two — District 1 number-suffixed, Districts 2–7 bare (not just
2 and 3), District 8 a still-different number-PREFIXED shape (`district-8-judges-and-magistrates`) the
original research pass never reached. **The bench data is far richer, and far messier, than planned
for**: 371 judges across all 8 districts (roughly the scale of Wisconsin's 261-judge bench), each
carrying their own role/title string that the CMS punctuates at least four inconsistent ways — colon
("Chief Judge: District 1B"), semicolon ("District court Judge; District 3A"), no separator at all
("District Court Judge D5", "Senior Judge District 2A"), and one outright typo ("Magisrate"). Rather
than guess a single split rule and risk mis-parsing some fraction of 371 rows into a wrong rank or
sub-district, the shipped card renders each title VERBATIM as one field. No phone, e-mail, or
courthouse address ships for any judge — measured absent on both the roster listing and a sampled
individual profile page, not assumed. `ia/scripts/build_ia_judicial_district.py`'s general N-way county
dissolve (District 2 unions 22 counties — Wisconsin's own circuit-court dissolve only ever merges
pairs) reuses `build_metro_outline.py`'s segment-count algorithm rather than forking a new one.

`community-college` (Iowa Code 260C.11 — CONFIRMED, was ASSERTED: an ELECTED board, one member per
director district — mirrors the fleet's DISTRICTED political-layer pattern, **not** Wisconsin's
`wtcs-district` shape, whose board is appointed under a different statute; a real divergence the
original roadmap note didn't flag). **AN ACTIVE, PREVIOUSLY-UNKNOWN 2026 BOUNDARY REVISION**: the LSA
org carries `CommColleges2020` (15 features, 2021-12-15 vintage) AND `CC_Boundaries_REV2026` (15
features, last edited 2026-07-02 — eight weeks before this correction), plus a
`CC_BoundaryReviewQuestion` scratch/comment layer edited the same day — evidence of an active or
just-closed boundary review with no primary citation found yet. Needs the same SF-75 discipline PR 5
(`county-supervisor`) already built: pin which vintage is authoritative, find the primary source for
what changed, gate the build both ways. **The roster problem is likely SOLVED, reversing the original
"15-site attrition project" call**: `ccforiowa.org/about/board-members-officers` — the trustees' own
association page — states "124 Trustees" and publishes a name/roman-numeral-district/college table
spanning all 15 colleges, the Vermilion/Douglas "the association's own directory" pattern again; 124
trustees against `CC_DD2023`'s 123 director districts is a one-off to reconcile at build time, not yet
resolved. Also needs a design decision on whether the merged-area outline alone is enough to name a
trustee (the roster is elected by director sub-district, `CC_DD2023`, itself phase 3 scope) or whether
phase 2 must reach into that geometry early. The most complex remaining phase-2 item — PR 6, last, and
possibly worth its own short research pass before a PR is written rather than implementing straight
from this record.

**Shipped 2026-08-28 (PR 6), after that research pass.** The dedicated pass resolved everything the
note above left open, and corrected two of its own premises along the way. **The boundary revision
question is answered, not merely gated both ways**: `CC_Boundaries_REV2026` turned out to be a LAYER
name, not the service name — the service is `CC_2026update`, and querying
`.../CC_Boundaries_REV2026/FeatureServer` (rather than `.../CC_2026update/FeatureServer/0`) 400s. The
newer layer is shipped for a confirmed reason rather than a guess: it recodes Southeastern Community
College from the older layer's "08" to "16", and Southeastern's own institutional history page states
it was chartered in 1965 as "Merged Area XVI" — corroborated independently by the trustees'
association's own I-VII/IX-XVI numbering (Iowa's original Merged Area 8 was dissolved into its
neighbors decades ago; no "VIII" survives in current use anywhere). No primary legislative document
explains the revision — the evidence (both layers edited within 2.3 minutes of each other, review notes
about aligning the CC boundary to school-district lines rather than about population or reorganization)
points to a routine LSA GIS data-accuracy pass, recorded as an inference, not a citation.
**`ccforiowa.org`'s "124 Trustees" is NOT a 124-row roster** — the research corrected this before any
code was written: that page publishes exactly 15 rows, one representative per college (its own
governing table), with "124 Trustees" appearing only as prose on the same page. The real per-trustee
rosters are the 15 individual colleges' own sites — DMACC, Kirkwood and Iowa Western were each
confirmed live to publish a clean, complete, per-district table — meaning a real roster needs 15
separate scrapers, not one. **The 124-vs-123 mismatch is fully resolved, not merely a one-off to
reconcile**: `CC_DD2023` (the 123-feature sub-district layer) is short exactly one polygon, Des Moines
Area's own District 2 — confirmed by DMACC's site naming 9 sitting trustees across Districts 1-9 while
the layer carries only 8 Des Moines Area features, and independently by the LSA's own
`NumberofDirectorDistricts` field, which gives DMACC's true count as 9 and sums to exactly 124 across
all 15 colleges statewide. **Given both of those findings, the design decision resolves in favor of
identity-only, matching Iowa's own `school-district-unified` precedent exactly**: shipping a districted
card today would mean either fabricating Des Moines Area's missing seat or misrepresenting it as
unrepresented territory, and no single roster source exists to populate 124 individual trustees even if
the geometry were complete. `cc-director-district` stays deferred, now for a measured reason rather than
an open question. Three independent witnesses gate the build exactly, all at build time: the 15 college
names match a second LSA layer one for one, that layer's population sums to Iowa's exact 2020 census
total (3,190,369), and its director-district count sums to 124. A card for each college links that
specific college's own site (15 domains, each verified live — content-matched where reachable, and
where blocked, confirmed via a recognized access-control signature already on record elsewhere in this
fleet: `indianhills.edu` behind a genuine Cloudflare managed challenge, `nwicc.edu` behind the
`sgcaptcha`/202 gate this project has already named for two Illinois counties).

`school-site` (Iowa DE `IowaSchoolBldgs` — CONFIRMED 1,321 features, `licenseInfo` null, edited
2026-07-29, genuinely current). **A NAMING TRAP, confirmed live**: the service's own internal title is
"PublicSchoolBldgs", and querying that STRING as a slug returns a completely different, stale service
(title "Public School Buildings", 1,336 features, last edited 2018-01-12, sparse fields, no
administrator contact) — **the correct slug is `IowaSchoolBldgs`, never the visually-identical
internal title.** Fields are richer than expected (per-building administrator name/title/phone/email
in-band); default to WI's `school-site` precedent (proximity-only, no admin roster row) unless the
implementing PR decides otherwise. `maxRecordCount`/pagination unchecked — live-load (matching
`county-subdivision`/`municipality`'s pattern) if it fits under the cap in one request, else pre-build
like WI's own `school-site`. PR 3.

**Shipped 2026-08-28 (PR 3).** `maxRecordCount` measured 1,000, below the layer's own 1,321-feature
count, so a live single-request load would have silently truncated — pre-built via
`ia/scripts/build_ia_school_sites.py`, matching WI's precedent rather than the live-load pattern.
Unlike Wisconsin's DPI layers, this dataset carries no placeless rows, no private-school class, and no
reprojection trap (native WGS84) — measured across the full 1,321 records, not sampled — so the
builder needed none of WI's placeless-skip or dual-layer-merge machinery. Shipped proximity-only
(name, `SchoolType` as the tag, physical address), the administrator contact fields left unused on the
card as planned.

`police-station` + `fire-station` — see the correction above. PR 1.

`library` — State Library of Iowa. **CONFIRMED no ArcGIS layer exists anywhere in Iowa's state GIS
presence** (both the LSA and LSAFiscal orgs fully enumerated; an unauthenticated
`arcgis.com/sharing/rest/search` catalog sweep for "iowa library"/"state library of iowa" turns up
only third-party/hobbyist maps — unlike Wisconsin's own DPI-published layer). The real directory is
`statelibraryofiowa.gov/resources/iowa-library-directory` (not `/libraries/directory`, which 404s),
linking a Knack app at `silo.knack.com/directory`. **DEFINITIVELY NOT PLAIN-GET-AUTOMATABLE**: Knack's
public application-metadata endpoint (app id `5adf7c79596212286f183285`) is open, but both real
record-fetching routes (`api.knack.com/v1/pages/scene_120/views/view_231/records` and
`.../objects/object_8/records`) return `401 Invalid API Key` without a private key — needs the
Playwright rung (the Kendall/McHenry-class ladder), untested in this pass. Neither a simple layer nor
a recorded gap yet — attempt the browser rung before deciding either way. Sequenced inside or just
after PR 6's window.

**Attempted 2026-08-28, after PR 6. THE PLAYWRIGHT RUNG ITSELF DOES NOT WORK IN THIS SANDBOX FOR THIS
HOST** — a stronger block than the documented Leaflet/MapLibre CDN case: `page.goto("https://
silo.knack.com/directory")` fails `net::ERR_CONNECTION_RESET` even with Chromium launched with an
explicit `proxy: { server: ... }` pointed at this environment's own `HTTPS_PROXY`, where a plain `curl`
to the same URL succeeds (curl honours `HTTPS_PROXY`; this sandbox's Chromium does not honour an
explicit launch-time proxy option for arbitrary third-party hosts either, only the documented CDN
workaround's same-origin `page.route` substitution — there is no live-browser route to this host from
here at all). **CURL, WITH THE RIGHT HEADERS, SUCCEEDED WHERE THE BROWSER COULD NOT REACH IT**: the
`api.knack.com` host in the note above was itself imprecise — the app's own boot config (fetched from
the embed's thin loader HTML) declares `api_subdomain = 'us-api'`, so requests belong on
`us-api.knack.com` — but that alone still 401'd. The actual missing piece was a header, not a host:
Knack's own client sends `X-Knack-REST-API-Key: knack` (the literal string "knack" — a documented
placeholder value, not a real secret) for anonymous, view-scoped record access, together with a
`Referer`/`Origin` matching the embed's own origin. With both, `GET https://us-api.knack.com/v1/pages/
scene_120/views/view_231/records` returns HTTP 200 with real, paginated data — 776 libraries total.
Knack's own public, unauthenticated application-schema endpoint
(`GET /v1/applications/5adf7c79596212286f183285`, 557 KB, no key needed) is what confirmed
`scene_120`/`view_231`/`object_8` were the right ids in the first place (the original note's guesses
were correct) and let every OTHER scene/view in the 85-scene app be enumerated — the large majority sit
on `staff*`/`admin*`-slugged scenes (edit/add forms, internal detail views) that are a separate,
non-public administrative area and were deliberately never probed, matching this project's own
never-work-around-an-access-control posture; only `scene_120` (slug `directory`) and `scene_130` (slug
`library1a`, reached by the SAME public page's own hash routing, confirmed `authenticated: false` in
the schema like `scene_120`) were tried, and only the former answered.

**THE ONE GENUINELY PUBLIC VIEW DOES NOT CARRY WHAT A NEAREST-N CARD NEEDS, AND THAT IS NOW A MEASURED
FACT RATHER THAN AN OPEN QUESTION.** `view_231`'s records expose exactly 8 real fields: Library Name,
Agency, City, County, Director/Administrator, Director email, Library Telephone Number, and an internal
District Office region code — no street address, no coordinates. Cross-checked against `object_8`'s
full 158-field schema (reachable only because the app-schema endpoint is itself public, not because any
object-level record endpoint was tried): the object DOES define "Physical Location (street address)"
and "Latitude" fields (no matching "Longitude" field found under any name), proving the State Library's
own system tracks more than the public embed exposes — the state drew its own public/private line
narrower than "does this data exist," and this project's own convention is to read fields as scoped by
the VIEW that serves them, never by what the underlying object happens to also contain. Every sibling
`library` layer in this fleet (Chicago, NYC, SF, Wisconsin) is a NEAREST-N proximity card built from
real building-level coordinates; a per-county roster list was considered as a different shape this
County field could support, and rejected — it would answer a different question than every other
`library` card in the fleet ("every library in your whole county" against "the nearest 3, straight-line
distance"), and 776 libraries across 99 counties skew heavily toward the handful of urban counties,
risking a card that is a wall of names in exactly the places most readers would open it. **RECORDED AS
A GAP, not a retry candidate**: reached, not merely "couldn't reach it" — the public boundary the state
drew itself excludes exactly the field this concept's own established shape needs. Phase 2 closes
without `library`.

County card gains the **auditor**, Iowa's county election commissioner (Iowa Code 47.2 — CONFIRMED,
was ASSERTED): `iowaauditors.org/find/directory/` — CONFIRMED, 99 rows embedded directly in
server-rendered HTML, each carrying name, **party as a CSS icon class** (`fa-republican`/`fa-democrat`
— not plain text; present on 94 of 99 rows, the other 5 carrying no party icon at all, shipped with
party omitted rather than guessed), office name, full mailing
address, and phone in `(NNN) NNN-NNNN` format; zero e-mails anywhere on the page, confirming the
no-email call. `sos.iowa.gov/auditors` does NOT 403 this sandbox either (corrected), but is a
per-county page-link directory, not a second name/phone list — useful as "does this county have an
official auditor page," not as a row-for-row cross-gate.

**Shipped 2026-08-28 (PR 2).** The 99 auditor names join `state-counties.json`'s BASENAME field
exactly for all 99 counties — no alias table needed. `ia_county_auditor_scraper.py` +
`build_ia_county_auditors.py` produce `data/app/ia-county-auditors.json`, keyed by GEOID, joined into
the already-shipped `county` layer's card (mirroring Wisconsin's clerk-join pattern: a roster fetch
failure degrades to the identity card the layer shipped with at launch, never breaks the county
lookup). Refreshed weekly by `update-ia-county-auditor-roster.yml` (Wed 14:30 UTC) as a reviewed PR.

**Sequencing, corrected from `ia/index.html`'s own "phase 2 begins with precinct, ia-judicial-district
and community-college" note (wrong — fixed in the same change as PR 1)**: PR 1 police-station +
fire-station (zero roster/licence/currency risk) → PR 2 auditor (roster-only, no new geometry) → PR 3
school-site (naming trap to navigate, otherwise simple) → PR 4 precinct (pagination +
honesty-critical field-withholding, no roster complexity) → PR 5 ia-judicial-district (buildable from
data already shipped, moderate scraper/statute work) → PR 6 community-college (currency reconciliation
+ elected sub-district roster design, the hardest remaining item) → library (attempted inside or after
PR 6's window, contingent on the untested Playwright rung).

## Phase 3 roadmap — the officeholder pass, elected-education fabrics, first city tier

**PR 1 — the County card's full elected officer slate — SHIPPED 2026-08-28.** This was phase 4
work in the committed roadmap and was pulled forward, because a boundary and its officeholder
sourcing belong in the same change (`docs/EXPANSION_GUIDE.md` Part 2 rule 4) and the County card
was answering *where* for 99 counties while naming 1 of their 6 elected offices. It ships all six
(Iowa Code ch. 331) from **five publishers**, and the reason it is five is measured rather than
architectural — no publisher covers Iowa's county offices, and the two that come closest are each
wrong in a way the other catches:

- **The ISAC member portal** (`member-portal.iowacounties.org/countydirectory/directory/<County>`)
  is the only statewide source for the **treasurer** and the **board of supervisors**, regenerated
  daily — and it publishes an **APPOINTED chief deputy in the elected sheriff's row** in Crawford,
  Page and Sioux, and an appointed assistant in Page's county-attorney row. Four mislabels, detected
  only because each office's own directory names the same person as a deputy.
- **The dated directories** — Iowa Land Records (recorders, 99/99 with a plain `mailto:`, the
  best-quality county source found in Iowa), the ISSDA sheriff directory (PDF, April 2025) and the
  ICAA roster (PDF, May 2026) — are better on identity and carry e-mail, and they **go stale**: Sac
  County's own site names a sheriff the ISSDA PDF has not caught up with.
- **The Secretary of State's auditors page** turned out to publish a full card per county — name,
  party and a Cloudflare-obfuscated e-mail for all 99. The auditor scraper's own docstring had said
  no such statewide roster existed "in a form this project can read", because the page's county
  DROPDOWN was read instead of the page body underneath it. **That correction is the phase's
  cheapest yield**: 99 e-mails and 4 parties on a layer that had shipped weeks earlier.

Neither publisher wins categorically, so the builder does not pick one. It resolves what it can
MEASURE (the deputy mislabels), pins what a county's own site settled (Sac's sheriff, and three
auditors where the two directories disagree — resolving **2-1 for the SoS**, which is exactly why
it is a pinned table and not a preference), and **withholds the rest**: five offices ship no name
at all and say on the card that two directories disagree and who each names. Seven counties ship
no board of supervisors, gated on Iowa Code §331.201's "three members unless increased to five"
AND on the seat count read back from the supervisor-district geometry this repo already ships.

Coverage: treasurer 99/99, recorder 97/99, sheriff 98/99, county attorney 97/99, 92 of 99 boards,
277 officer e-mails, 741 phone numbers. **No address from any of these sources ships** — the ICAA
prints private-law-office addresses, so both PDFs are read for a phone and an e-mail and never for
the line itself, and the builder asserts structurally that no field beyond name/phone/e-mail/party
can reach a card. Files: `ia/scripts/ia_county_officers_scraper.py`,
`ia_county_officer_sources_scraper.py`, `build_ia_county_officers.py`,
`ia/data/app/ia-county-officers.json`, `.github/workflows/update-ia-county-officers-roster.yml`.

**PR 2 — the County Supervisor District card names its supervisor — SHIPPED 2026-08-28.**
The district card could say *where* you are and how big the board is; it could not say who
represents you. It now can, for the counties where that question even has a district-level answer.

**The scope is a legal distinction, not a convenience.** Iowa Code §331.206 lets each county pick
one of three representation plans, and the shipped geometry carries which: **plan 1** (44 counties)
elects at large with no districts at all, **plan 2** (15) elects supervisors COUNTYWIDE who merely
have to *reside* in a district, and **plan 3** (39-40) has each district elect its own supervisor.
Only under plan 3 does naming a district's supervisor tell a reader something PR 1's countywide
board listing does not — and keying a plan 2 district would read as a district election that did
not happen. So 44 counties needed nothing and 15 were deliberately left alone.

**Four statewide routes are measured closed**, which is why this is per-county at all: the
Legislature's own `CountySupervisorDistricts` layer *has* a `NAME` field and it holds the
DISTRICT's name ("Bremer Supervisor District 1"), all 266 distinct; the ISAC member portal
publishes every supervisor and attaches a district to none of them, in all 99 counties; the
Secretary of State's statewide canvass summary carries **zero** supervisor contests, because Iowa
counties canvass their own county offices — so the Illinois canvass route simply does not exist
here; and electionresults.iowa.gov is an Angular application with no reachable data API.

**The parse reads no markup, and that is what made one script cover 39 counties across four-plus
CMSes.** The names were already known and already gated — PR 1's `ia-county-officers.json` — so the
only missing fact is a *number*. Each page is flattened to text and each known surname matched to
the nearest "District N", which is Wisconsin's `witness_window()` pattern pointed at a district
instead of a phone number. Four gates, all of which must pass or the county ships nothing: every
supervisor found, every one within the window, the districts exactly 1..N with no repeats, and N
equal to the geometry's `NUMDISTRICTS`.

**The window was then tightened by measurement rather than left generous.** A first pass at 300
characters keyed 17 counties; measuring the gap it actually used on all 67 districts found a
maximum of **42** and nothing above 60 — a county that publishes this pairing publishes it
adjacently. The window is now 80. That matters concretely: Polk's page prints its five supervisors
TWICE, once as a bare navigation run with no districts near it, and a window wide enough to reach
from that run to an unrelated "District 5" elsewhere on the page would have paired them
confidently and wrongly. Every run prints its widest gap so the assumption can be re-checked
rather than assumed.

Result: **17 counties, 67 districts**. The other 23 plan 3 counties ship nothing and say why —
several refuse this client outright, two sit behind a captcha (an access control, not an obstacle
to route around), and the rest name no district on any page the scraper can find. None of them is
degraded: their supervisors are still named, unkeyed, on the County card.

**Two counties surfaced a conflict rather than a gap, and they resolve in opposite directions** —
which is why neither is settled by a rule. **Humboldt** is one of PR 1's seven withheld boards
(ISAC lists 6, illegal under §331.201); its own page shows 5 districts and 5 of those 6 names, so
the portal's 6 looks like the defect. **Warren** is also withheld (ISAC 5 against geometry 3), and
its own page shows 5 districts and 5 names — so there the likely stale party is the LSA GEOMETRY,
not the county. Both are recorded in `ia/WATCH.md` rather than guessed at.

Files: `ia/scripts/ia_supervisor_district_scraper.py`, `build_ia_supervisor_roster.py`,
`ia/data/app/ia-supervisor-members.json`, `.github/workflows/update-ia-supervisor-roster.yml`.

**PR 3 — `school-director-district` — SHIPPED 2026-08-28.** The sub-district fabric a school
board is actually elected from, registered `subOf: "school-district-unified"` so turning it on
frames the parent as an outline and fills its director districts inside it. 716 features inside
the 324 shipped districts: **193 whole-district AT-LARGE features and 523 numbered ones**, because
Iowa Code ch. 274/277 lets each district choose, and the layer carries both.

**The build corrected three things this document itself had on record wrong**, which is the reason
to re-measure a source at build time rather than trust a research note:

- `DIST_NAME` and `UID` were recorded here as *"100% NULL across all 728 — declared but empty;
  never read them"*. Both are fully populated. `DIST_NAME` is the more valuable: its values are
  `D1`..`D7` **and a literal `AT-LARGE`**, so a district that elects at large is now READ from the
  publisher's own label instead of inferred from `DISTRICT == 0` — and no card can ever say
  "District 0".
- **`UID` is not a unique key.** WEBSTER CITY publishes districts 2 and 3 *both* carrying
  `UID 3063002`, with different populations and different geometry — an upstream typo in a key
  field, not a duplicate row. The layer keys on `<GEOID>-<DISTRICT>` and asserts uniqueness.
- **Two districts publish every row twice, not one.** The note on file named only `DAVIS COUNTY`;
  `EAST BUCHANAN` is duplicated identically. A Davis-shaped hard-code would have shipped East
  Buchanan as a six-seat board, so the dedupe is structural — identical attributes AND identical
  geometry — and asserts the count it removes rather than naming any county.

Two further things are recorded rather than smoothed. `KINGSLEY-PIERSON` is incoherent at source
(an `AT-LARGE` row of 2,503 people *and* a `D2` row of 632, with no District 1 anywhere); nothing
invents the missing district or drops either row, and a gate fails if a *second* district ever
develops the same contradiction. And the name join needed **two** aliases rather than the three
assumed — `MARION INDEPENDENT` matches on its own — leaving `LU VERNE` and `ORIENT-MACKSBURG`
stale in the director layer and correctly absent from ours. That second one is worth stating
plainly: **it independently corroborates this repo's own work**, since
`build_ia_school_districts.py` dissolved exactly that district into Nodaway Valley for 2026-2027.

**The licence nearly went on the record wrong too.** The FeatureServer returns `licenseInfo: null`
and an empty `copyrightText`, which reads as "no terms stated". The ITEM behind it
(`5d6e55f885c54dd282eb17daaca20740`) carries `licenseInfo: "<p>CC0</p>"`. **Query
`arcgis.com/sharing/rest/search` for the service name before concluding anything about an ArcGIS
layer's terms** — the same shape as the Illinois lesson that an org publishes more than its viewer
shows.

Simplification was chosen by measurement, not habit: 9% retained vertices holds the 2,000-point
gate at **99.85% with zero overlaps**, where 5% clears the 99.5% floor by only 0.1 points and 3%
breaks topology outright (a point falling in two districts at once).

**Identity-only, for a checkable reason.** No statewide roster of Iowa school board members exists
to join: the state collects them through the login-gated Iowa Education Portal, and the Iowa
Association of School Boards' directory is member-gated. The card says that in those words.

Files: `ia/scripts/build_ia_school_director_districts.py`,
`ia/data/app/ia-school-director-districts.json`.

**PR 4 — the County card's board section, corrected against the Wisconsin/Illinois
exercise — SHIPPED 2026-08-28.** A review of how the board of supervisors is surfaced,
against the fleet rules that earlier exercise produced, found Iowa breaking **both** of
them. Neither was a new judgement call; both are written in `docs/EXPANSION_GUIDE.md`
Part 5 with a stated test.

**"AN IDENTICAL PHONE NUMBER ON EVERY MEMBER ROW IS A SWITCHBOARD, NOT CONTACT."** The
guide states the test mechanically — *collect the distinct numbers, and if exactly one
covers the whole board, it belongs to the board* — and Iowa failed it in **every one of
the 92 counties ISAC publishes**: a single board-office number repeated under three to
five names, implying direct lines that do not exist. Adams printed `(641) 322-3240` five
times on the County card and a sixth on the district card. The test now runs in the
builder exactly as the guide words it, hoisting the number to `boardPhone` and rendering
it once as a "Board office" row; 350 redundant values were removed. It is deliberately
NOT a per-county pin — a county that ever publishes real per-member lines keeps them.

**"PROVE 'AT LARGE' FROM A CERTIFIED ELECTION DOCUMENT."** The rule warns that putting a
county's whole board on the County card *"claims that all N members represent every
resident… it tells a reader nine people represent them when one does"*. Iowa listed the
whole board unqualified for all 92, and **35 of those counties elect by district** under
Iowa Code 331.206 plan 3. Iowa's position was better than the Illinois case that produced
the rule — it has certified proof of each county's method in the Legislature's own
`PLANTYPE` — it simply was not using it on that card. `supervisorPlan` now rides the
roster (read back from the shipped geometry, where `seats` already comes from) and every
list is qualified: plans 1 and 2 say every voter votes on every seat, and plan 3 says one
of these is your supervisor rather than all of them. **Jones County, which is absent from
the state's district layer, claims NEITHER method** rather than defaulting to one.

**AMENDED 2026-08-28 — QUALIFYING A LIST IS NOT THE SAME AS HELPING SOMEONE READ IT.** The
first plan-3 wording was *"one of these supervisors represents you, not the whole board"*.
It is true, it satisfies the rule above, and in the 18 plan 3 counties whose districts are
NOT keyed it is a dead end: it tells a reader the list in front of them cannot answer their
question and stops. The fix is not softer wording, it is the next step — **all 40 plan 3
counties ship numbered district geometry**, so the County Supervisor District card names the
district a reader is in whether or not anyone has keyed its supervisors, and its own footer
links that county's board page (present for all 18). So the note is now conditional on
keying rather than on the plan alone: a keyed county explains its district badges, and an
unkeyed one adds a second row in the card's own *"Not shown — <reason>"* idiom naming the
limitation and where to go. It also counts the board rather than assuming five ("one of
these three is your supervisor" in a 3-seat county). The general rule: **when a card cannot
answer the reader's question, say what it cannot answer AND what in the app can.**

Two smaller improvements came with it: where phase 3 PR 2 keyed a county's districts, each
name now carries the district it holds and the board is ordered by district rather than by
surname — a plan-3 reader is looking for a number, not a name.

A note for whoever next diffs this data: the phone drop is 741 → 391, **47.2%**, and
`check_roster_retention.py` fails a field that loses at least HALF its records. It is
silent here by twenty records. That is the gate working to spec rather than a blind spot,
and the change is intentional — but it is close enough to the line to be worth stating.

**PR 5 — `cc-director-district` — SHIPPED 2026-08-28.** The sub-fabric a community
college's board of trustees is elected from (Iowa Code 260C.11), 123 districts inside the
15 merged areas, `subOf: "community-college"`.

**Two things this build found are worth more than the layer.**

**The child and the parent disagree about where colleges end, and the browser spot-check
is what caught it.** The director districts encode the 2023 plan; the parent
`community-college` layer is the 2026 update. In roughly 0.2% of the state they name
DIFFERENT colleges — at 41.536,-92.685 the parent card said Des Moines Area while the
child's polygon said Indian Hills. A `registerPolygonLayer` single-source lookup ships
that contradiction silently, so this layer is registered BESPOKE with a two-leg query
that resolves both and, on a mismatch, names **neither** district and tells the reader
which plan says what. **A sub-layer that contradicts its own parent is worse than one
that declines to answer.**

**Des Moines Area's "missing District 2" is not missing.** The source publishes 123
polygons against a parent that seats 124 directors, and DMACC carries districts 1 and
3-9. The obvious reading — a hole in the map — was tested and is wrong, twice over.
Sampling puts the share of each merged area covered by none of its own director districts
at 0.00-0.64% across all fifteen colleges, and **Des Moines Area's is 0.11%, LOWER than
most and far below Southeastern's 0.64%** — those slivers are digitisation differences
between independently drawn layers, the same artifact Illinois measured between
Richland's precinct and board layers. And the source's own `IDEAL` for Des Moines Area is
99,579 against a merged-area population of 794,895, which is the total over EIGHT
(99,362) rather than nine (88,322), with every deviation computed against it and inside
±2%. Kirkwood is the control: its IDEAL implies nine for nine polygons. So this publisher
drew eight districts deliberately, skipping the number 2, and the disagreement with the
parent is about the COUNT, not the ground. **Nothing here resolves which is right.**

The join is numeric rather than by name (the source writes "North Iowa Area" and
"Northwest" where the app ships "North Iowa" and "Northwest Iowa"), with one asserted
`8 -> 16` Southeastern remap — the same stale-numbering correction the parent builder
documents — and the builder FAILS if `CCdist 8` ever stops appearing, so a remap that has
outlived its reason cannot quietly mis-key a different college.

**The licence does NOT follow the school-director precedent.** That layer's item carries
CC0; this one's item states an EMPTY licence. Both were checked the same way and they
differ, so "the licence lives on the item" is a place to look, not a promise about what
is written there. The terms here are recorded as UNSTATED, which is a different claim
from permissive.

Identity-only: trustees are elected per district, but 6 of the 15 colleges name a
numbered district on a discoverable page, one sits behind a captcha and one refuses this
client — joining six would read as the other nine having no trustees. Per-college
measurements are in `ia/WATCH.md` for a future keying pass.

Files: `ia/scripts/build_ia_cc_director_districts.py`,
`ia/data/app/ia-cc-director-districts.json`.


### PR 5 — `dsm-ward`, the instance's first city tier — SHIPPED 2026-08-28

4 wards, `ia/data/app/dsm-wards.json` + `dsm-council-members.json`, weekly CI
(`update-ia-dsm-council-roster.yml`, Thu 17:30 UTC). Four things the roadmap above got wrong or
under-specified, all corrected by measuring at build time:

* **The composition citation.** §372.4 is the *mayor-council* form, not council-manager; its
  subsection (1)(b) grandfathers exactly Des Moines's 1975 shape — "two council members elected at
  large and one council member from each of four wards" — and (1)(a) permits the city manager the
  city's own page describes, "without changing the form". §372.4(2) also states plainly that the
  mayor **is not a member of the council**, which is why the card badges him Mayor rather than
  folding him into a council list.
* **"No separate scrape needed for ward seats" was wrong, and shipping on it would have been the
  Coles County mistake.** The in-band `PersonFName`/`PersonLName`/`EMail` are correct today and are
  still not read as the roster: a roster attached to a boundary is refreshed when the boundary is,
  and these demonstrably are not on one schedule (ward 2's feature carried its **2024-02-16** edit
  while wards 1, 3 and 4 were edited across **2025-12-29..31** for the November 2025 cycle). The
  service also has no phone field and a null `PersonTitle` on all four. So the council page is the
  authority and the in-band names are the build-time **witness** the scrape must agree with.
* **The licence nearly stopped the layer, and the stop would have been wrong.** The item's
  `licenseInfo` opens "© Copyright City of Des Moines, Iowa 2025. All rights reserved." — read
  alone, the Piatt County answer. The city's own **Terms and Conditions of Use** (data.dsm.city)
  say the opposite: applications using portal data "must include the following disclaimer", and
  quote that same string. It is the text of a **required notice**, not a refusal, and it ships
  verbatim on the card. **Read the portal's terms page before writing a publisher off** —
  `licenseInfo` is where the licence lives but not always where the grant lives.
* **Two geometry artifacts, both measured and neither smoothed.** The city's own wards 1 and 2
  overlap by 9.29 acres, of which one part is a 14 m-wide ribbon running 2.6 km along their shared
  edge (compactness **0.0169**) — so the agreement gate now measures the SOURCE's overlap and fails
  only if simplification adds to it. And the four wards leave **0.0070%** of the city uncovered in
  753 perimeter fragments; that is a **weekly gate**, because Des Moines annexes land and a ward
  layer that has not caught up would leave a reader in a real hole no roster check would notice.

The page's **Appointed Staff and Department Directors sections use identical card markup to the
elected members**, so the scrape is scoped by `<h2>` heading, refuses if a name appears under both,
and refuses if the unelected sections vanish — they are the control proving the split still works.

### PR 6 — `iowa-aea`, the phase's last item — SHIPPED 2026-09-03

Nine Area Education Agencies (Iowa Code ch. 273), `ia/data/app/ia-aeas.json`, no weekly
workflow — it is geometry, not a roster. **The roadmap framed this as a vintage caveat to write
on a card and it turned out to be a build decision**, which is why it is worth writing up rather
than ticking off.

* **The two services the roadmap named are one service.** The public item
  `1cfa541b8ebe4bdcbc2f52cdd0977a2b` is titled **`IowaAEAs`**; the layer it serves calls itself
  **`IdoeAeaFY20`**. This plan treated them as separate and worried only about the second. They
  are the same data — the `IowaSchoolBldgs`/`PublicSchoolBldgs` trap a second time, and a third
  time in the same build, since `CurrentIowaSchoolDistricts` is internally `IdoeSD`. **Pin the
  item id.** A second copy of the FY20 layer also sits on a University of Northern Iowa personal
  account, so a name search returns two.
* **The vintage worry was CONFIRMED, and then made irrelevant.** The item's own description reads
  "for the 2019-2020 school year - updated 3/9/2020" — six school years back, on a fabric this
  repo has already watched move. But the Department's **current** district layer carries
  `AEA_NUM` in band on all 324 districts, so the line is drawn by dissolving the school-district
  fabric this app already ships, joined on `DistrictNCESCode` = Census `GEOID`. **324/324, both
  directions, no alias table** — and TIGERweb's 325th, Orient-Macksburg, has no row in the
  Department's layer at all, a THIRD independent corroboration of this repo's own dissolve into
  Nodaway Valley. The join is also the tripwire: the next consolidation fails it loudly.
* **The demoted polygon still had a job, and it is the one that mattered.** An AEA line only
  moves when a member district CHANGES agency, so the builder asks that of all 324 directly —
  five interior points each, a majority must land inside that district's own agency in the FY20
  polygon. All 324 pass, which is what licenses trusting a six-year-old shape as a witness.
  Statewide agreement is 99.8% over 13,072 in-state points.
* **A gate that measured a proxy instead of the question, and fired wrongly for it.** The first
  draft inferred "seam vs moved district" from how far apart the disagreeing sample points fell,
  citing a measured 50.5 km closest pair. That is not a property of the data: two independent
  points on one long shared boundary land close together as soon as the sample is big enough, and
  the gate duly fired at 4.3 km on the same boundary one seed later. **When a proxy and the real
  question are both cheap, ask the real question.**
* **The overlap test is split by whose defect it is** (`build_dsm_wards.py`'s lesson). The
  dissolve gets zero tolerance. The published layer's own overlaps are reported and merely
  capped — four of its pairs overlap across ~5.3 sq mi, `01×07` alone 2.989 sq mi in 124 slivers,
  the largest 171 acres at Polsby-Popper 0.042. **The layer this build declined to ship does not
  close on itself; the one it built does.**
* **No second simplification, deliberately.** The parent is already simplified at 9% and gated;
  a dissolve merges interior edges and leaves exterior ones alone, so re-simplifying would only
  move edges `school-district-unified` does not move and break the nesting that is half the point.
* **Identity-only is statutory, not a missing roster.** Iowa Code §273.8 gives a voter no say in
  any of the nine directors: five are elected by the boards of the member school districts on a
  population-weighted vote, four are appointed by those districts' superintendents. What the card
  CAN name comes from the agencies themselves — the Iowa AEA system's own **Find My AEA** page
  publishes a block per agency keyed on the same two-digit code the geometry carries, with a name,
  a phone and a website, 9/9, and the builder requires both publishers' names to agree before it
  writes. One guess caught by probing: Keystone's site is **not** `aea1.k12.ia.us` derived from
  its agency number (that host does not resolve) — it is `keystoneaea.org`, off that page.
  **A hostname that looks derivable is still a guess.**

Files: `ia/scripts/build_ia_aea.py`, `ia/data/app/ia-aeas.json`. The guidebook's per-fork
inventory also gained a correction found while filing the row: Iowa's `school-director-district`
entry was sitting in the **Wisconsin** table, and Iowa's header count read 16 against 18 rows.
Both tables now agree with their worksheets.

**Still to come this phase:**


`school-director-district` (LSA `IowaSchoolDirectorDistricts` — VERIFIED exists, 728 features, "as of
2023-12-18" — this PR's first deliverable is the coverage/semantics gate: which of the 324 districts
actually elect by director district vs. at-large, since not every district necessarily uses the
geometry the same way; identity + district link only, board-member roster stays a recorded gap).
`cc-director-district` (DE `CC_DD2023` — VERIFIED exists, 123 features, effective 2023-08-01 through
the statutory decade term to 2033; `subOf: "community-college"`). **The HSEMD NG911 ask goes out this phase**: Iowa's Homeland Security &amp;
Emergency Management Dept. runs a 911 program requiring counties to submit PSAP/Fire/Law/EMS service
boundaries to a state GIS standard, but no open statewide aggregate was found on the state's ArcGIS
organization in the research pass (only county-local layers, e.g. Linn and Scott) — the "ask is a
route, not a last resort" precedent (`docs/EXPANSION_GUIDE.md` §5.1; Wisconsin's WEC answered in 22
minutes). SOS asks go out alongside it: licence terms for the LSA/DE layers, and whether a
current-edition polling-place export exists beyond the 2024-08 item.

## Phase 4 roadmap — officeholders, polling, second city

~~County card gains the remaining elected county officers~~ — **DONE in phase 3 PR 1** (above), and
it did not need the Wisconsin tranche model: ISAC's member portal plus three per-office statewide
directories covered all 99 counties in one PR. What phase 4 still owns here is the **board CHAIR**,
which no statewide publisher names, and keying supervisors to their own districts (phase 3 PR 2). **JONES COUNTY WAS MEASURED ON 2026-09-04 AND ITS NAMED ROUTE IS CLOSED** — the one Iowa county
with no supervisor-district card at all, absent from the state's 98-county aggregate. This plan and
the `jones-county-supervisor` gap both said its adopted-map PDF "does carry real vector path data
(moveto/lineto/stroke operators), so a Jackson-County-IL-style extraction is plausible". **It is
not.** The Jackson method reads FILLED path objects whose colours pair with a legend; stroke
operators appear in nearly every vector PDF, including ones whose map body is a raster. Measured
with pdfplumber: 554 curves, **zero filled**, plus **22 raster images**, 20 of them full-width strips stacked to form the map body, and the
largest vector path on the page is an 18×14 pt road shield. Reading it would mean sampling pixels,
which the Jackson record forbids and the Knox build proved wrong. What the PDF DOES have is a TEXT
LAYER giving all five districts' populations and compositions (the Menard shape — look for text
before any raster method), and that text is what closes the composition route too: **every** district
takes PART of a township, and the state precinct layer's single `Castle Grove/Lovell/Wayne` precinct
spans districts 1, 2 and 3. So the remaining route is the county's own GIS file, drafted as Ask 14
and held for the operator. **A ROUTE NAMED IN A GAP RECORD IS A HYPOTHESIS UNTIL SOMEBODY OPENS THE
FILE.**
**Polling places** ship only if the SOS ask
in phase 3 lands a current per-election edition — `IowaPollingPlaces` joined to `precinct` by `PPID`
under the full Wisconsin display contract (election named, provisional wording while pre-certification,
pull dated, retired once the election passes) — the August 2024 item never ships labeled "current."
**The municipal probe ran on 2026-09-03 and its yield was three findings, one of which SHIPPED the next day** (the full
measurement is the `ia-municipal-officeholders` gap record): the League of Cities is NOT gated
and publishes a phone for 935 of 948 cities while naming nobody; the Secretary of State
publishes no clerk directory on either its Schools & Cities or its Research & Data page, so the
WEC-shaped ask was drafted rather than skipped; and an ArcGIS catalog sweep found no Iowa
analogue of Milwaukee County's `Municipal_Executives` layer but did find **Waterloo** publishing
5 wards that name their own councilperson, both at-large members and a council-page link in band
— a second city tier on the Des Moines pattern, subject to the same Coles rule (the in-band
names are the witness, the city's own page is the authority).
**WATERLOO SHIPPED ON 2026-09-04, AND IT RETIRED THE `dsm-ward` LAYER** (`waterloo-wards.json`,
`waterloo-council-members.json`, weekly Thu 18:30). The second city made this a DISPATCHED
concept rather than a second layer, which is `docs/EXPANSION_GUIDE.md` §3.0 stated plainly and
this plan's own earlier note had got wrong by calling Waterloo "a new layer with its own
geometry, gates, `area_rank` renumber and workflow". It is none of those: **one `city-ward`
toggle, two municipality-keyed entries, `area_rank` unchanged at 14, and the layer count still
20** — plus an alias shim, which this instance did not have, so every `#layers=dsm-ward` link
already shared keeps working. Iowa needed the dispatcher itself: `registerCountyLayer` lived
ONLY in Illinois as fork-level code and was ported (its `polygonCountyEntry` companion was
deliberately left behind — both city entries render bespoke person rows, and it needs two
helpers Iowa lacks). Promoting the dispatcher to `engine/` for all six instances is the real
debt and is recorded in `ia/WATCH.md`, not done in a PR about Iowa's cities.
Two measurements worth carrying forward. **The mayor is not on the ward card**: he is elected
citywide, so the at-large rule puts him on the unit's identity card, and the card names him in
prose instead of implying the council is the whole city government. And **a hole is COMPACT, a
seam is thin**: Waterloo's largest uncovered tiling fragment is 7,909 m² against Des Moines's
3,482, which an area-only ceiling copied across would read as a regression — it is 36 m by
3,156 m at Polsby-Popper 0.0025, and not one of its 156 fragments scores above 0.30, so its
builder gates on SHAPE as well as size.
**THE FIVE-CITY OFFICIALS TIER SHIPPED THE SAME DAY, AND THE MEASUREMENT BEHIND IT IS WHY IT IS
FIVE** (`ia-city-officials.json`, `ia/scripts/ia_city_officials_scraper.py` +
`build_ia_city_officials.py`, weekly Fri 16:30). All 532 Iowa cities that publish a website were
swept for a council roster — the ceiling, because 407 of the 939 publish none — and 16 yielded
one a machine could read, of which five cleared every check: **Moravia, Norwalk, Palo, Riverside
and Tiffin**, a mayor and five council members apiece, 30 people with an e-mail and 18 with a
phone. **All five elect AT LARGE, so nothing here is a layer**: the at-large rule sends a body
elected by the whole unit to that unit's identity card, so these are roster rows on `municipality`
with no dispatch entry, no coverage function and nothing in `LAYER_AREA_RANK`, and `city-ward`
stays the two ward-electing cities. Sixteen of 939 is 1.7%, so **per-city scraping is now a
MEASURED poor statewide route rather than an untried one** — the five ship because a reader in one
of them is better served than by a card naming nobody, not because the route scales, and the
statewide ask is still what would close the gap.
Three things the sweep settled are gates in the scraper rather than notes. **A seat-count gate
alone does not validate a parse**: Waterloo's own page yields eight council members, an entirely
plausible council, and only the duplicate-name check demotes it — so ranking candidates on
plausibility would have promoted the one city already known to be a trap. **The platform does not
predict the markup**: Des Moines, Waterloo and Norwalk run the same content system and need three
different parsers, so each city's naming convention is declared in the scraper's `CITIES` table
instead of being guessed from the host. And **the address's domain decides nothing**: six of the
30 published addresses sit on consumer, provider or business domains — Moravia lists webmail, an
ISP account and the contracting business one of its councilmen runs, which is what a town of a few
hundred people has and what the city publishes as the way to reach them — so the test is
`build_ia_county_officers.py`'s, applied unchanged (the officeholder's own name in the local part,
or an office-mailbox form; 27 and 3 of the 30). Consulting the domain instead was tried and errs
in BOTH directions: it read Riverside's and Waterloo's own municipal mail as third-party. Every
address is re-tested each build against the name actually SHIPPED, so a name correction cannot
leave one witnessed against somebody the card is no longer naming.
**THE CITY CARD GAINED CONTACT ON 2026-09-04, AND IT IS NOT A ROSTER** (`ia-city-contact.json`,
`ia/scripts/build_ia_city_contact.py`, weekly Fri 15:30). The League of Cities' own ungated city
table gives all 939 cities their office phone (927) and website (532), plus 2 office mailboxes;
11 carry none of the three and render exactly as they did before. **The join is total and that is
the gate** — 939 of 939 TIGER places, one alias (`Jewell` -> `Jewell Junction`), and the nine
non-joining League rows asserted by shape, so a city renamed or dissolved fails the build instead
of quietly losing its contact. Iowa's join is simpler than Wisconsin's because `LSADC` is
uniformly 25: one place class, so the city name alone is a unique key. **The
`ia-municipal-officeholders` gap is unchanged by it** — a reader can now reach their city hall and
still cannot be told who runs it, which is what the card's own row says — it pointed at Des Moines
as the one city whose published council districts named them, and by the end of the same day it
named seven cities instead of one. Two things fell out of the build
worth carrying: six League cities are absent from TIGERweb and the cause is NOT established (the
absence is, against a working control — run the control, because a query returning zero for
everything looks identical); and the worksheet's `workflows[]` list had gone two short since phase
3, so the history page's job tile read 6 against 8 on disk, which nothing gates.

~~**Cedar Rapids tier** from Linn County's own `ElectionsCityCouncilDistrict` layer (VERIFIED exists,
modified within the research pass's own week) plus its roster from `cedar-rapids.org`.~~ — **DONE
2026-09-04**, as a third entry on the consolidated `city-ward` dispatcher rather than a layer, and the
plan's one-line description hid the thing that actually needed solving. That layer is **not Cedar
Rapids's** — the city publishes no boundary at all — and it is not Cedar Rapids's *alone*: it is a
COUNTY service carrying **two** cities' districts, Cedar Rapids's five and Marion's four, separated
only by a `POLITICAL_TWP` code ('27', '21') with no name field, no domain and no description anywhere
in the service. **Nothing published says which code is which**, so the build proves it by TILING and
re-proves it weekly IN BOTH DIRECTIONS — 27 must cover Cedar Rapids (ratio 1.00323) and Marion's 21
must fail to (99.996% left uncovered). A single downtown point test returns 27 today and would return
21 just as confidently after a swap, which is exactly why the control is the gate. Two independent
publishers corroborate the pairing without being used to derive it: Linn's own page is titled *Cedar
Rapids Council Districts & Marion Ward Maps*, and the city's own *Find Your District* page links to
it. The roster is eight of the nine seats from the city's seven seat pages; the mayor is scraped and
excluded under the at-large rule. **The toggle is renamed City Council District** — Cedar Rapids has
never used the word ward, and a generic label must be one no city is contradicted by. **Marion is
measured, passes the same tiling test, and is NOT shipped**: a boundary without a roster is half a
card, so it is `ia/WATCH.md`'s next city. NG911 tier ships
here if HSEMD answered in phase 3. ~~Area Education Agency geometry resolved one way or the
other~~ — **DONE in phase 3 PR 6** (above), and it resolved as a SHIP rather than a recorded no:
the identity-only card this section anticipated, with the §273.8 sourcing confirmed exactly as
asserted, but on geometry built from the current school-district fabric rather than on the
Department's own 2019-2020 polygon.

---

## What this plan deliberately is not

No party offices or caucus/precinct-committee units (standing fleet rule). No guessed officeholders
anywhere in any phase — not supervisors (no statewide roster exists), not school or community-college
board members (no per-body source proven yet), not township trustees (unsourced), not municipal
officials statewide — **and the parenthesis this sentence used to carry was measurably wrong.**
It read "League of Cities is membership-gated"; it is not. `iowaleague.org/cities/` answers 200
to an ordinary browser request with 948 city rows carrying a phone for 935 and a website for 536,
and names NO PERSON in any column — right about the officeholders, wrong about the directory, and
the difference matters because that table alone would give every Iowa city card its own phone
number and front door. The officeholder gap is now recorded properly as
`ia-municipal-officeholders` (2026-09-03, four routes measured), the SoS ask that Wisconsin's
whole municipal tier rests on is drafted at last (`docs/ASK_DRAFTS.md` Ask 8), and the per-city
GIS route has a second city ready: Waterloo's `Wards_view` names each ward's councilperson and
both at-large members in band. No boundaries nobody publishes: no soil-and-water-conservation-district geometry
(elected, ASSERTED Iowa Code 161A.5, but the only located layer is LSA-vintage 2016 — backlog, not a
phase 1–4 layer), no county-hospital-trustee, ag-extension-council, drainage-district, or
benefited-fire-district geometry, no judicial election sub-district layer at launch (data exists, not
surfaced). No statewide-office cards — Governor, Secretary of State, Attorney General, Iowa Supreme
Court, Iowa Court of Appeals are all at-large or appointed-statewide with no polygon and no fleet
precedent for a statewide office card. No "current" polling-place claim off a stale file. No Census
Designated Places (TIGERweb layer 4 is incorporated-only by construction; unincorporated land reads
correctly through `county-subdivision` instead). No conclusion that an Iowa agency "publishes nothing"
or "refuses this project" from a sandbox 403 alone — every block gets one CI-side probe first.

## Verification (every PR, in order)

1. `python3 scripts/generate_metro_files.py` then `--check` — never hand-edit a GENERATED region.
2. `python3 scripts/compose_app.py --check` — no `ENGINE:BEGIN/END` fence touched this phase; all
   module code is fork-side in `ia/index.html`.
3. `python3 scripts/build_coverage_gaps.py --check --metro iowa --out ia/data/app/coverage-gaps.json`.
4. `python3 ia/scripts/validate_index.py ia/index.html` — rank lists 1:1 against registered ids,
   count floors, the `data/app/` exactly-one-list invariant.
5. `python3 scripts/build_landing_page.py` + `--check`, `build_privacy_page.py --check`,
   `build_manifests.py --check`, `build_dark_map_palette.py --check` (every new layer color needs a
   dark-theme twin).
6. `python3 ia/scripts/validate_sources.py` — every new PROVENANCE/ENDPOINTS row resolves, zero FAIL;
   blocked hosts recorded per the `"blocked"` inversion convention (unreachable = OK, reachable-again
   = the WARN), never disabled TLS verification.
7. `python3 scripts/validate_workflow_deps.py` — `ia/scripts/*` imports resolve inside `ia/`'s own
   tree only.
8. Behaviour gate — serve the repo root, one server for every instance:
   `python3 -m http.server 8000` then
   `BASE_URL=http://localhost:8000/ia/ node ia/scripts/smoke_test.mjs` — `EXPECT_LAYERS` asserted
   exactly, ground truth classifies against the Marshalltown anchor point, the negative point misses
   every anchor. `BASE_URL=http://localhost:8000 node scripts/landing_test.mjs` and
   `node scripts/page_consistency_test.mjs` don't exercise `ia/` until go-live (PR 10) — `ia` stays
   out of `metros.json` through phase 1, per PR 0's resolved design decision.
9. Every builder proves its own gates on a real run before its data file is committed;
   `check_roster_retention.py --base origin/main` before every push once a roster exists (PR 0
   onward — `congress-roster.json` and both chamber rosters ship in PR 0 itself).

---

## Worksheet and fleet values

**`metros.json` entry** (per PR 0's resolved design decision above, **not** added dark in PR 0 —
`render_cards()`/`sync_fleet()` render every entry live regardless of the deploy exclude, so this
entry ships only at go-live, still "PR 10"):
```json
{ "id": "iowa", "explorer_name": "districtry Iowa", "label": "Iowa",
  "url": "https://districtry.com/ia/", "emoji": "🌽",
  "repo": "ThursdaysFamous/districtry",
  "bbox": { "minLng": -96.64, "minLat": 40.37, "maxLng": -90.14, "maxLat": 43.50 },
  "tag": "ia", "landing_name": "Iowa",
  "blurb": "All 99 counties: supervisor districts with each county's own election plan, precincts, school and community-college districts, judicial districts, cities and townships — and the Iowa Senate, House and U.S. House seats, and who holds those." }
```

**`ia/metro-worksheet.json` identity values** (keys mirror `wi/metro-worksheet.json` exactly):
`this_metro` "iowa"; `metro_name` "Iowa"; `metro_bbox` `{minLng -96.69, minLat 40.32, maxLng -90.09,
maxLat 43.55}` (state extent padded ~0.05°, the WI convention); `metro_center` `[41.94, -93.39]`, zoom
~7 (frames the whole state, not a city); `permalink_gate`/`poi_geocode_bbox`
`{minLat 40.17, maxLat 43.70, minLng -96.84, maxLng -89.94}` (padded ~0.15°); `exports_name`
"IowaExplorer"; `sw.cache_name` "districtry-ia-shell-v1"; `brand.theme_color` and `palette` identical
to Wisconsin's (`#6d3fd1` family — the worksheet's own label is "districtry palette — brand violet is
CHROME ONLY, never map data"; state theming is not a fleet convention); `geocoder` Photon
Iowa-bounded type-ahead + unbounded Photon + Nominatim POI serial queue, `search_placeholder` "Search
an Iowa address"; `min_register_layer` 10 at phase-1 close; `coverage_key` (2 bands): `outside`
"Outside Iowa", `region` edge "Iowa" / label "District shown, supervisor not named" / sub "The state
publishes every county's districts; no state source names who holds each seat."

**Anchor: Marshalltown, Marshall County.** Central, mid-size (~28,000 pop. ASSERTED), and specifically
**not** Story, Johnson, or Black Hawk — whose supervisor geometry is mid-transition under SF 75 and
therefore not election-stable, which anchors must be (`docs/EXPANSION_GUIDE.md` §2.5.1's WI-precedent
anchor policy: "pre-built layers only, election-stable expected values"). Marshall County is `PLANTYPE`
plan 1 (at-large), so its one supervisor-district feature is the stable record. Candidate
`anchor_point`: lat 42.0494, lng −92.9071 (downtown Marshalltown, near the Marshall County Courthouse
— coordinates to validate against every shipped layer at build, never shipped un-validated). Launch
`anchors[]` (values DERIVED from fetched data at build time, never typed from memory): `county` →
"Marshall County"; `us-house`; `ia-senate`; `ia-house`; `school-district-unified` → expected
"Marshalltown Community School District"; `county-supervisor` → the Marshall at-large record. Phase 2
adds `ia-judicial-district` and `community-college`. Alternates if Marshalltown fails validation at
build time: Boone, Carroll (both ASSERTED plan-1 mid-size counties, to be confirmed).

**Negative point: lat 43.65, lng −93.37** — inside Minnesota, near Albert Lea and comfortably north of
the Iowa border (~43.50), chosen deliberately against the **land** border rather than a river. Carter
Lake, Iowa sits **west** of the Missouri River inside the Omaha river bend, so "across the Missouri" is
not safely outside Iowa; both the Missouri and Big Sioux river borders carry oxbow/avulsion
irregularities. The Minnesota land border has none of that. **Corrected 2026-08-27, caught by the
behaviour gate**: an original choice of lat 43.75 sat outside this instance's own `permalink_gate`
(`maxLat: 43.70`, a strict `<` comparison in the engine's hash-point validator), so the point was
silently rejected at selection time — every layer's card stayed on its unqueried "Layer off."
placeholder rather than genuinely querying and reporting no match, which the smoke test's negative-point
check (expecting the honest empty state, not a stuck placeholder) caught. lat 43.65 sits inside the
gate with margin on both sides. Validate at build time against every shipped layer, per the standard
negative-point contract — including against `permalink_gate` itself, not only against the shipped
boundaries.

---

## Traps (carried into every phase, not just phase 1)

1. **`wi/data/app/iowa-county-outline.json` and `wi/data/app/iowa-polling-places.json` are Iowa
   County, Wisconsin** — not this project. Iowa the state also has its own Iowa County (one of the 99,
   `PLANTYPE`-tagged like every other), so "Iowa County" is an ambiguous name across two live instances
   permanently. Iowa-instance data files are named `ia-*`; the string "iowa" alone is never sufficient
   to identify a file as belonging to this instance, and any repo-wide grep for "iowa" must be read
   file-path-first.
2. **Every workflow is `ia`-prefixed, no exceptions** — Wisconsin's two Milwaukee-tier workflows
   (`update-mps-school-board-roster.yml`, `update-mpd-captains-roster.yml`) shipped without the `wi-`
   prefix; Iowa's city-tier workflows in phases 3–4 (`update-ia-dsm-council-roster.yml`, an eventual
   Cedar Rapids equivalent) do not repeat it.
3. **`ia-validate-sources.yml` exists from PR 0**, not retrofitted after a gap is noticed (Wisconsin's
   equivalent shipped without one and it went unscheduled for its first weeks).
4. **`history_page` is opted into the worksheet from PR 0**, with a live changelog from the first
   commit, not backfilled in a later phase from git history (Wisconsin's was backfilled in phase 4).
5. **Sandbox-vs-site vantage recorded on every source measurement** — `sos.iowa.gov`, `iowacourts.gov`,
   and `data.iowa.gov` all 403 from this development sandbox while `legis.iowa.gov` and every ArcGIS
   REST endpoint answer plain; a block recorded from this sandbox is not evidence the agency itself
   refuses automated readers, and gets one CI-side probe before it is written up as anything more than
   "unreachable from here."
6. **Vintage gates, one per state-published layer**: the supervisor-district layer (2024-01-30) is
   already superseded in three counties by Senate File 75 and needs the PR 5 reconciliation gate on
   every rebuild; the precinct layer carries a 2022 reprecincting fabric that can drift under mid-decade
   city annexations; the polling-place layer is dated 2024-08 and must never render as "current"
   without a fresher per-election source; the school-district count differs by exactly one between
   TIGER (325) and the Dept. of Education's own layer (324) and that delta is named, not silently
   resolved by picking a number. Watch for **duplicate stale services on the same ArcGIS organization**
   (Wisconsin's LTSB org carried a live-named item that was actually a year-old copy) — pin exact
   service item ids, not just names, when wiring each builder.
7. **`maxRecordCount` 1,000 on the state services** — `Iowa_Precincts` (1,660) and
   `IowaSchoolDirectorDistricts` (728) both exceed it and must be paginated, not silently truncated.
   Des Moines's `Wards_view` layer serves in state-plane WKID 102676 and needs a server-side reproject
   request, the Milwaukee-WKID-32054 pattern from Wisconsin's own `mpd-district` build.
8. **Card-copy honesty traps specific to Iowa's structure**: plan-2 supervisor counties draw district
   lines but elect countywide — the card must not read as district election; judicial-district judges
   are never described as "elected" (merit-appointed, stand for retention); party affiliation ships
   only where a specific source states it per office (county officers are ASSERTED partisan, school
   and community-college boards and city councils are ASSERTED nonpartisan — confirm each at the PR
   that ships it, never assume from one office to the next).

---

## Appendix — measured source ledger

**Fetched during the research pass, 2026-08-27** (TIGERweb, LSA/DE ArcGIS organization, Open States,
`legis.iowa.gov`, `iowaauditors.org`, `iowacourts.gov`'s existence, Des Moines and Linn County GIS,
SOS/HSEMD page existence via search) unless marked otherwise. Four of the load-bearing ones were
**independently re-fetched a second time**, in this session, while writing this document — those are
marked "re-verified."

- **TIGERweb `Legislative/MapServer`** (`tigerweb.geo.census.gov`), `STATE='19'`: layer 0 (U.S. House)
  = **4 — re-verified**; layer 1 (Iowa Senate) = 50; layer 2 (Iowa House) = 100.
- **TIGERweb `State_County/MapServer/1`**, `STATE='19'`: counties = 99.
- **TIGERweb `Places_CouSub_ConCity_SubMCD/MapServer`**, `STATE='19'`: layer 1 (county subdivisions) =
  1,663; layer 4 (incorporated places) = 939.
- **TIGERweb `School/MapServer`**, `STATE='19'`: layer 0 (unified) = 325; layers 1/2
  (secondary/elementary) = 0/0.
- **LSA org `services.arcgis.com/vPD5PVLI6sfkZ5E4`**: `CountySupervisorDistricts/FeatureServer/0` —
  **re-verified: 266 features, fields COUNTY/DISTRICT/NAME/PLANTYPE/NUMDISTRICTS/MEMBERS/CODIST_ID/
  CONO/FIPS/AREA/TOTAL/IDEAL_VALU/DEVIATION, licenseInfo absent, last edit 1706643533798 = 2024-01-30.**
  `Iowa_Precincts/FeatureServer/0` — 1,660 features, attribution string "Iowa Secretary of State, Iowa
  Legislatives Services Agency" [sic], `maxRecordCount` 1,000, item modified 2024-01-30.
  `IowaPollingPlaces/FeatureServer/0` — 1,386 points, modified 2024-08. `IowaSchoolDirectorDistricts/
  FeatureServer/0` — 728 features, "as of 2023-12-18."
- **DE org (same organization, education account)**: `CurrentIowaSchoolDistricts` — 324, item touched
  the week this document was written. `IowaSchoolBldgs` — 1,321 points, modified within the same week.
  `CC_DD2023` — 123 features, "Approved Director Districts 2023 — effective 2023-08-01," statutory
  decade term to 2033. `CommunityCollegeDistricts` / `CommColleges2020` — 15 merged areas (two items,
  same count, pin the current one at build). `IowaAEAs` / `AEADirectorDistricts2025` — exist, not
  count-verified.
- **`LSAFiscal` org** (`services2.arcgis.com/KhKjlwEBlPJd6v51`): `JudicialDistricts/FeatureServer` —
  layer 0 = 8 districts, layer 1 = 14 election sub-districts; copyright "Iowa Judicial Branch";
  2010-population vintage fields.
- **Senate File 75 — re-verified by independent web search this session**, three sources (The Gazette,
  KCRG, Johnson County's own government site): signed by Gov. Reynolds 2025-04-11; forces Story,
  Johnson, and Black Hawk counties (each home to a Regents university) from at-large to district
  supervisor elections effective the November 2026 cycle; Johnson's plan cuts 5 districts and was
  SOS-technically-approved 2026-01-07 per the research pass; Story's board rejected its first submitted
  map 2026-01-06, a second LSA letter followed 2026-01-14; litigation from affected-county voters is
  active as of this writing.
- **`legis.iowa.gov`**: chamber pages `/legislators/senate` and `/legislators/house` — server-rendered
  plain HTML, name/district/party/county/email; no blocks observed. County-redistricting ledger at
  `/publications/legalPubs/countyRedistricting` — exists, 47 documents, cites Iowa Code 331.210A.
- **`data.openstates.org/people/current/ia.csv`** — reachable, same column shape as Wisconsin's
  `wi.csv` build already consumes.
- **`iowaauditors.org/find/directory/`** — reachable, plain HTML, all 99 county auditors with office
  address and phone; no email column observed.
- **`sos.iowa.gov`, `iowacourts.gov`, `data.iowa.gov`** — pages/endpoints **exist per search-index
  results** (per-county shapefile pages, auditor list, district court and judges-and-magistrates pages,
  a Socrata catalog) but **return 403 from this development sandbox** — recorded as
  UNREACHABLE-FROM-SANDBOX, not as agency refusal; each needs one CI-side probe before any block is
  written up as more than that.
- **Des Moines**: `services.arcgis.com/HT7H9QGiZQoRJDpJ/.../Wards_view/FeatureServer/0` — 4 wards,
  fields include `WardNbr, PersonTitle, PersonFName, PersonLName, EMail`; served in state-plane WKID
  102676; CSV/GeoJSON/SHP exports also published; item dated January 2025.
- **Linn County** (Cedar Rapids' county): `services.arcgis.com/i14SLLmXo7Hn9vNc/.../
  ElectionsCityCouncilDistrict` — exists, modified within the week this document was written; the same
  county org also carries `ElectionsPrecinctSplit` and Kirkwood Community College director districts.
- **Iowa HSEMD 911 Program** — program's existence and its requirement that counties file PSAP/Fire/
  Law-Enforcement/EMS service boundaries to a state GIS standard is confirmed from the agency's own
  program page; **no open statewide aggregate of that filed data was found** on the state ArcGIS
  organization in the research pass (only county-local layers, e.g. Linn, Scott) — recorded as a
  genuine absence-of-publication finding, the trigger for the phase-3 ask, not yet re-probed from CI.

**Environment note**: this sandbox's egress runs through a pre-configured proxy; a 403 or connection
reset from this environment is checked against its response body before being recorded as a site
property, per the fleet's standing rule that a proxy's own refusal is not the site's.

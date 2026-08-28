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
(Iowa League of Cities is a membership directory with no public officials export located; **execution
note: check `data.iowa.gov`'s Socrata catalog for a city-officials dataset before finalizing this as a
recorded gap** — that host 403s from this sandbox and was not checked past the proxy). Per-city rosters
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

## Phase 3 roadmap — elected-education fabrics + first city tier

`school-director-district` (LSA `IowaSchoolDirectorDistricts` — VERIFIED exists, 728 features, "as of
2023-12-18" — this PR's first deliverable is the coverage/semantics gate: which of the 324 districts
actually elect by director district vs. at-large, since not every district necessarily uses the
geometry the same way; identity + district link only, board-member roster stays a recorded gap).
`cc-director-district` (DE `CC_DD2023` — VERIFIED exists, 123 features, effective 2023-08-01 through
the statutory decade term to 2033; `subOf: "community-college"`). **Des Moines tier**: `dsm-ward` — the
city's own `Wards_view/FeatureServer/0` — VERIFIED exists, 4 wards, fields including
`PersonFName`/`PersonLName`/`EMail`, i.e. **the city's own layer names the sitting council member
in-band**, no separate scrape needed for ward seats; served in state-plane WKID 102676, reproject
server-side; mayor + at-large members (composition to confirm on `dsm.city` at PR time) ship as card
rows, never polygons. **The HSEMD NG911 ask goes out this phase**: Iowa's Homeland Security &amp;
Emergency Management Dept. runs a 911 program requiring counties to submit PSAP/Fire/Law/EMS service
boundaries to a state GIS standard, but no open statewide aggregate was found on the state's ArcGIS
organization in the research pass (only county-local layers, e.g. Linn and Scott) — the "ask is a
route, not a last resort" precedent (`docs/EXPANSION_GUIDE.md` §5.1; Wisconsin's WEC answered in 22
minutes). SOS asks go out alongside it: licence terms for the LSA/DE layers, and whether a
current-edition polling-place export exists beyond the 2024-08 item.

## Phase 4 roadmap — officeholders, polling, second city

County card gains the remaining elected county officers (treasurer, recorder, sheriff, county attorney,
board chair where published) — ISAC's (Iowa State Association of Counties) directory checked first at
execution time, else the Wisconsin tranche model: per-county scrape, per-office floors, dated rows,
landing in reviewed tranches rather than one 99-county PR. **Polling places** ship only if the SOS ask
in phase 3 lands a current per-election edition — `IowaPollingPlaces` joined to `precinct` by `PPID`
under the full Wisconsin display contract (election named, provisional wording while pre-certification,
pull dated, retired once the election passes) — the August 2024 item never ships labeled "current."
**Cedar Rapids tier** from Linn County's own `ElectionsCityCouncilDistrict` layer (VERIFIED exists,
modified within the research pass's own week) plus its roster from `cedar-rapids.org`. NG911 tier ships
here if HSEMD answered in phase 3. Area Education Agency geometry (9 AEAs; boards chosen by member
school-board members, not the public — ASSERTED, Iowa Code 273.8) resolved one way or the other: either
an identity-only "board chosen by member school boards" card (the WTCS pattern from
`docs/WI_PHASE4_PLAN.md` PR 6) or a recorded no — not left open past phase 4.

---

## What this plan deliberately is not

No party offices or caucus/precinct-committee units (standing fleet rule). No guessed officeholders
anywhere in any phase — not supervisors (no statewide roster exists), not school or community-college
board members (no per-body source proven yet), not township trustees (unsourced), not municipal
officials statewide (League of Cities is membership-gated; only the per-city ladder and per-city GIS
routes are real). No boundaries nobody publishes: no soil-and-water-conservation-district geometry
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

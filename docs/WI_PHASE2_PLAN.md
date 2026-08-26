# districtry Wisconsin — Deployment Phase 2: statewide Illinois parity

> Planning document, researched and verified 2026-08-25. The SF worksheet
> (`docs/archive/METRO_EXPANSION_SF_WORKSHEET.md`) is the precedent for a
> committed phase plan; like it, this file moves to `docs/archive/` when the
> phase closes and the shipped state supersedes it. Every source below marked
> **verified** was fetched during the research pass — endpoint, count, licence
> and failure mode recorded from the response, not from a catalog page.

## Context

Wisconsin shipped in place on 2026-08-25 (`wi/`, PRs #511 → #523) with **12
statewide layers**: the three chambers, congress, county, county-board (LTSB's
statewide supervisory districts, supervisors named in 20 of 72 counties), three
TIGERweb school-district layers, county-subdivision, municipality, ZIP, and
post-office. No safety group exists yet; the county and municipality cards are
identity-only; and phase 1 left ten recorded doc/infra discrepancies.

This phase replicates the remaining Illinois concepts that have **verified,
honest Wisconsin sources**. It takes the instance from **12 → 19 layers**
(political 6, safety 2, schools 4, geography 7) and closes: the electoral
precinct analog (`ward`), police/fire station points (the safety group's first
members), the trial and intermediate appellate courts, the county clerk on the
county card, school and library points, legislature-roster office parity, and
the county-board roster's growth from 20 to 23 counties.

**Scope decisions (operator-confirmed):**
- **Statewide only.** All Milwaukee city-scoped work — MPS school board, MPD
  districts, neighborhoods — defers to phase 3, with its verified sources
  recorded in the guidebook backlog so nothing is lost.
- **Phase 3's aldermanic ambition is boundary + rosters** for the seven
  verified-scrapeable big cities (the county-board attrition model applied to
  cities), not boundary-only.

**Resolved design calls:**
- `ward` registers as **geography, `subOf: "county-subdivision"`** — `WARDID`
  numbers within the MCD, and the CouSub layer contains towns where
  `municipality` (TIGERweb Places) does not, so it is the parent that actually
  contains every ward. This matches IL's `county-precinct` (geography, subOf
  township) precedent.
- **Anchor policy, made explicit:** `anchors[]` admits only pre-built layers
  with election-stable expected values. The two court layers join at the
  Marathon point; `ward` does not (live layer + semiannual re-filing churn),
  and nearest-N layers never do (facility churn). All six existing anchors
  already satisfy this — the policy is descriptive, now stated.
- Courts ship as **two PRs / two workflows** (per-concept convention).
- New political layers slot after `county-board` in the sidebar.
- Chamber labels reconcile **worksheet → registered** ("Wisconsin State Senate
  District" / "Wisconsin State Assembly District").

**Conventions binding every PR:** scripts `wi/scripts/build_wi_*.py` /
`wi_*_scraper.py`; workflows `.github/workflows/update-wi-*.yml` cloning
`update-wi-county-board-roster.yml` (BOT_PR_TOKEN, fixed `bot/wi-*` branch,
PR-never-push); every layer gets a worksheet `source` block (the generator
refuses otherwise), a `LAYER_SIDEBAR_RANK` slot, a `validate_sources.py` row, a
`WATCH.md` row, and guidebook coverage-map + matrix + inventory updates in the
same change; GENERATED regions and ENGINE fences are never hand-edited — all
new code is fork-side; scraped strings render through `sanitize()`/
`textContent`; the officeholder story ships with each boundary (a roster or a
recorded gap, never silence); `min_register_layer` only rises.

---

## PR 0 — hygiene: the ten phase-1 discrepancies + missing bookkeeping

1. `wi/README.md` — "Eleven statewide layers" → twelve; add the county-board
   row (LTSB + Trempealeau, 20-county roster); rewrite the stale "growth"
   paragraph (county-board already shipped).
2. `docs/EXPANSION_GUIDE.md` — §4.10 close-out "eleven layers" → twelve;
   §4.5.1's band table row for Wisconsin rewritten: the instance ships **3**
   bands (coverage = the 20-roster-county ring in `metro-outline.json`,
   region = `wi-state-outline.json`), not the 2 the table still claims.
3. `docs/DATA_LAYER_GUIDEBOOK.md` —
   - Fleet totals line gains `Wisconsin 12` (later PRs bump it as they land).
   - A `### Wisconsin — 12 layers` per-fork inventory table is added.
   - The **Geography/amenities matrix gains its missing Wisconsin column**,
     every cell measured: ZIP/county/municipality SHIPPED; neighborhood
     recorded (Milwaukee CKAN is the phase-3 candidate); park district **n/a**
     — not a Wisconsin unit of government (Legislative Council Special Purpose
     Districts IssueBrief, Aug 2024 — the single citation for the column);
     library taxing district NO HONEST ANALOG (boards appointed, s. 43.54 —
     the points layer ships instead, PR 8); TIF — no statewide geometry (DOR
     is tabular; Milwaukee's city TID dataset recorded); water reclamation —
     **MMSD is APPOINTED** (7 mayoral + 4 ICC, s. 200.09(1)(b)) where
     Chicago's MWRD is elected, and its boundary layer carries SEWRPC
     copyright needing a licence check before any ship; town sanitary /
     public inland lake districts — the one Wisconsin special-district class
     with elected commissioners — have **zero statewide geometry** (DNR hub
     measured 0 with a positive control), recorded drop.
   - Safety matrix, fire-boundary Wisconsin cell: supersede "no statewide
     boundary publisher found" with the **NG911 finding** (WI_OEC_GIS org:
     FireBoundary 3,046 / LawEnforcementBoundary 3,101 / PSAP 208 statewide
     polygons, ~weekly, needing a per-agency dissolve) — still unshipped, but
     the publisher now measurably exists and the backlog records it.
   - Elected-school-board cell: append the statute finding — only MPS
     (ch. 119) and Racine Unified (s. 120.42(1)(d)2, nine election districts)
     elect by geographic district; RUSD's geometry is PDF-only → measured gap.
     The trial-court row gains the municipal-courts record-drop (219 courts,
     71 joint serving 2–23 municipalities, PDF-only mapping whose subset-font
     encoding garbles extraction).
   - The informal `NOT SHIPPED` status in Wisconsin cells is normalized to the
     documented vocabulary (GAP-with-rationale or NO HONEST ANALOG), and the
     backlog gains the Tier-2 entries (aldermanic, MPS board, MPD,
     neighborhoods, NG911) with their verified endpoints.
4. **NEW `.github/workflows/wi-validate-sources.yml`** — clone
   `ca-validate-sources.yml` (monthly, staggered cron, its own tracking
   issue). `wi/scripts/validate_sources.py` is complete and nothing schedules
   it today, contradicting the worksheet's own claim of a monthly check.
5. `wi/WATCH.md` — the 1,589 / 1,590 row: both numbers are real and the row
   conflates them. 1,589 is the LTSB raw-fetch gate (`EXPECT_DISTRICTS` in
   `build_wi_supervisory_districts.py`); 1,590 is shipped (−16 LTSB
   Trempealeau + 17 county-own). Rewrite the row to say so.
6. `wi/metro-worksheet.json` — `sources_page.credits` gains Wisconsin LTSB and
   Trempealeau County (the flagship layer's two publishers, both currently
   uncredited); chamber labels updated to the registered long forms.
7. `wi/scripts/` Illinois leftovers — rewrite the docstrings in
   `build_congress_roster.py` ("Build the IL U.S. House roster"),
   `build_metro_outline.py`, and `validate_sources.py`'s header + its
   IL-workflow credit note.
8. `scripts/generate_metro_files.py` (~lines 145–146) — the hardcoded "…so
   this is Illinois" comment emitted into every instance's generated
   metro-config: make it instance-neutral, then regenerate **all four**
   instances.
9. `wi/scripts/validate_sources.py` — add the missing PROVENANCE row for
   `county-board-members.json`.

## PR 1 — `ward`: LTSB municipal wards, live point-first

The phase's headline and its most shovel-ready item — the supervisory builder
already fetches this layer as its reconciliation witness.

- **Module** (fork-side, after `municipality`): bespoke `registerLayer`, group
  geography, `subOf: "county-subdivision"`. Point query via the engine's
  `loadArcGISPointGeoJSON` against LTSB
  `WI_Municipal_Wards_Current/FeatureServer/0` (**verified**: 7,161 features,
  open licence, stable-URL promise, point-in-polygon answers confirmed for a
  Madison and a rural Forest County point at ~2–3 KB a response). The map
  overlay is a fork-side paged loader (2,000/page × 4) with
  `maxAllowableOffset=0.0005&geometryPrecision=4` and minimal `outFields`
  (`WARDID,MCD_NAME,CTV,CNTY_NAME,SUPERID,ALDERID`) — full precision measures
  ~85 MB statewide, which is why this layer is live, not pre-built. Measure
  the generalized overlay payload before shipping; the recorded fallback is a
  pre-built mapshaper-simplified file rebuilt each filing window.
- **Traps encoded:** display name composed as CTV-word + `MCD_NAME` +
  `int(WARDID)` ("City of Madison — Ward 52") — never the clerk-submitted
  `LABEL`, which is case-inconsistent across counties; `ALDERID === "00"` is a
  placeholder (all towns/villages AND at-large cities) and never renders;
  currency is the item's `lastEditDate`, cadence Wis. Stat. 5.15(4)(br)
  (Jan-15 / Jul-15 county filings; the editions ran Jan 7,138 → Jul 7,161).
- **Card:** ward pill; rows County, County board district (`SUPERID` — the
  same value the county-board card answers), Aldermanic district (only when
  ≠ "00"). No officeholder — a ward elects no one, and the card says so.
- **Gap record `ward-polling-places`:** WEC and MyVote sit behind a Cloudflare
  managed challenge (**verified**: HTTP 403 `Cf-Mitigated: challenge` on every
  path including file downloads and the MyVote API routes) — an access
  control, never defeated; one CPD-style Playwright-from-CI attempt is queued
  before the block is filed permanent. Milwaukee's CC-BY "Voting Wards and
  Polling Places" CKAN dataset is recorded as a future city-scoped enrichment.
- Bookkeeping: worksheet entry + area-rank insert (after `zip-code`, before
  `post-office`); sidebar after `county-subdivision`; `validate_sources`
  ENDPOINTS row; guidebook precinct cell → SHIPPED; WATCH semiannual row;
  `docs/REDISTRICTING_RUNBOOK.md` ward row (SEMIANNUAL class);
  `min_register_layer` 9 → 10. No data file, no workflow, no anchor.

## PR 2 — `police-station` + `fire-station`: nearest-3, USGS structures

Two clones of the shipped post-office module against the same service:
`carto.nationalmap.gov/.../structures/MapServer/53` (police — **verified** 807
points in the WI envelope) and `/51` (fire — 1,743). Group `safety` — already
declared in the engine GROUPS block with zero members; registering populates
it. No coverage function, matching IL, and the envelope deliberately catches
border-state stations (correct behaviour near Superior/Marinette/Beloit).
Spot-checks passed: all 7 MPD district stations with correct addresses, all 14
Madison fire stations 1:1. One verified ghost record (Town of Madison FD,
defunct since 2020) — the card intro presents "nearest stations", a proximity
fact, never "your" station or a jurisdictional claim. Bookkeeping: two
worksheet entries, sidebar's new safety section, ENDPOINTS rows, safety-matrix
cell → SHIPPED, `min_register_layer` 10 → 12. No data files, workflows, or
anchors.

## PR 3 — `wi-circuit-court`: county-union geometry + wicourts roster

- **Geometry — the honesty argument, stated in every artifact:** no agency
  publishes circuit geometry (**measured**: ArcGIS catalog zero across three
  queries, LTSB's org has no court layer). County unions are legitimate only
  because the composition carries a **double witness** that agrees exactly:
  Wis. Stat. **753.06** and wicourts.gov's own circuit listing — 69 circuits,
  every county its own except Buffalo+Pepin, Florence+Forest,
  Menominee+Shawano. NEW `build_wi_circuit_courts.py` dissolves the shipped
  `state-counties.json` → `data/app/wi-circuit-courts.json`. Gates: exactly
  69; every county assigned exactly once; the three merges present. Validator
  trap: docs.legis statute pages lazy-load — 753.06 truncates at 52 of 63
  entries in one fetch, so cite per-subsection URLs.
- **Roster:** NEW `wi_circuit_judges_scraper.py` + builder →
  `data/app/wi-circuit-judges.json` from wicourts.gov's judges table
  (**verified**: ~260 judges, footer-dated 2026-08-24, plain curl 200 — no
  blocks anywhere on the host) joined with the contact directory (branch,
  courthouse address, phone). Traps: slash-row dedupe (two cross-listed pairs
  double-count); Florence/Forest render as separate rows sharing one judge; no
  judge e-mails exist anywhere (never invented); everyone is titled "Judge" —
  appointees filling vacancies are indistinguishable from elected judges in
  any wicourts source, so the card claims neither. Floors ≥65 circuits, ≥240
  judges. NEW `update-wi-circuit-court-roster.yml` (Wed 14:30 UTC).
- **Card:** "<County> County Circuit" pill; the bench behind an expander when
  branches exceed ~7 (Milwaukee seats 47); courthouse office group;
  primaryLink = the circuit's wicourts page.
- Bookkeeping: worksheet entry citing all three witnesses; area rank 4 (69
  circuits ≥ 72 counties); data_files geometry (69/69) + roster (min 65);
  **sw cache v4 → v5**; guidebook trial-court cell → SHIPPED; WATCH (April
  judicial elections; a 753.06 amendment is the boundary trigger) + runbook
  row; smoke anchor `wi-circuit-court: "Marathon"`; `min_register_layer`
  12 → 13.

## PR 4 — `wi-court-of-appeals`: 4 districts + 16 judges

Same shape one tier up. `build_wi_court_of_appeals.py` → 4 county-union
features per Wis. Stat. **752.11** (text unchanged since 1977), cross-witnessed
by wicourts' own district lists; gates: 4 features, 72 counties partitioned
exactly once. Scraper + builder → 16 judges keyed "1"–"4" — **read the content
cards, never the page's nav menu**, which is a stale former-judge list (6 of 16
names wrong, measured); gate the 4/4/3/5 split per 752.03. NEW
`update-wi-court-of-appeals-roster.yml` (Wed 15:30 UTC). Area rank **1** (4
districts outrank 8 congressional). The guidebook gains a **new fleet-wide
concept row** — "Intermediate appellate district (elected)" — per the
procedure's add-the-row rule. Anchor `wi-court-of-appeals: "District III"`
(match the rendered identifier exactly). `min_register_layer` 13 → 14.

## PR 5 — county clerks on the county card (no new layer)

- WEC is Cloudflare-blocked (recorded, not defeated). Two **verified**
  substitutes cover the concept: the **Wisconsin Blue Book 2025-26** "County
  officers: county clerks" table (docs.legis PDF — all 72 with party; the
  two-column layout scrambles under linear extraction, so the parse is
  layout-aware with a 72-row gate) **cross-gated** against
  **wisconsincountyclerks.org**'s 72 per-county pages (name, address, phone,
  fax, email, website, hours; its 403 is a plain UA rule, not a challenge —
  browser headers suffice; robots `Crawl-delay: 10` honored, a ~12-minute
  crawl). A name disagreement between the two ships only the agreed fields for
  that county, logged — the Blue Book is an April 2025 snapshot and appointed
  replacements post-date it, so the association's name wins where they
  diverge.
- **Milwaukee exception, from statute** (Wis. Stat. 7.20(1), fetched): the
  county election authority in Milwaukee County is the **appointed** county
  Election Commission — the card links the body, labeled appointed, and names
  no one (both its hosts block automation). Builder floor: 71 named + 1
  exception entry.
- Module: convert wi's `county` from a compact polygon layer to a bespoke one
  following IL's county module (clerk person-row, office group, party note,
  the Peoria-exception rendering pattern for Milwaukee). NEW
  `update-wi-county-clerk-roster.yml` (Fri 14:30 UTC). Guidebook county-clerk
  cell → SHIPPED; WATCH row (clerks elect November of even years). No
  rank/floor/anchor changes.

## PR 6 — legislature roster upgrade (no new layer)

- Fix two **measured** defects in `build_wi_legislature_roster.py`: the Open
  States CSV's `email` column (132/132 populated) is currently discarded, and
  `first_url()` ships the **oldest** session link (a senator's card links a
  2019 page today).
- NEW `wi_legislature_scraper.py` for
  `docs.legis.wisconsin.gov/2025/legislators/{assembly,senate}` — two fetches,
  all 132 members in district-id-keyed DOM with Madison office room, phones,
  fax, and email (**verified**; no blocks; Open States carries none of the
  office fields — capitol address/voice measured 0/132). Merged as an
  enrichment on the Open States base. The URL is session-scoped and the
  unversioned path 404s — the **biennium bump** goes in WATCH.md (odd-year
  January) so the scraper never silently reads a frozen roster.
- Extend `update-wi-legislature-roster.yml` to run the scraper before the
  builder; floors stay 31/94; the retention gate protects the new fields
  automatically from the next change onward.

## PR 7 — county-board roster 20 → 23 + coverage-ring consequences

The "a blocked county site is not a blocked county" lesson, applied: three of
the ten blocked counties fell to alternate hosts this research pass.

- Extend `wi_county_board_scraper.py`'s COUNTIES table with an `arcgis`
  strategy (attribute read, per-county field map):
  - **Milwaukee (18 seats)** — the county's own LIO layer (**verified**:
    `Sup_Name`/`Email_Addr`, 18/18, data edited 2026-06-29), **gated against
    the Legistar web API witness** (`webapi.legistar.com/v1/milwaukeecounty` —
    a witness, never a sole source: its OData date filter is silently ignored
    and end dates can be aspirational; a name-set mismatch fails the county
    loudly).
  - **Racine (21)** — the county's own AGO org
    (`County_Board_of_Supervisors_WFL1/0`, `REPNAME`/`Contact`, 21/21, edited
    2026-04-23 — post-election).
  - **Outagamie (36)** — the county left its Akamai-blocked domain for
    `outagamie.gov`, which serves a readable 36-district roster with 36
    e-mails; the existing scraper repoints, reading direction pinned.
  - The remaining seven (La Crosse, Lafayette, Lincoln, Marathon, Monroe,
    **Rock**, Sheboygan) are now **measured** no's — AGO catalog sweeps
    returned zero; Rock's portal is LAN-only and its public host resets.
- Builder floors 18 counties/400 seats → 21/470. **The phase-1 rule fires:**
  `METRO_COUNTY_FIPS` += 079/087/101 with INSIDE anchors, OUTSIDE anchors
  dropped, `metro-outline.json` regenerated in the same change.
- The guidebook's `county-officials` gap updates (52 → 49 unnamed; the blocker
  appends the three recoveries plus two standing lessons: re-probe a recorded
  block after a county domain move, and enumerate a county's AGO org before
  writing its roster off) → coverage-gaps regenerated.

## PR 8 — `school-site` + `library`: nearest-3, DPI, pre-built

- NEW `build_wi_school_sites.py` → `data/app/school-sites.json` from DPI's own
  AGO org: `Wisconsin_Public_Schools/FeatureServer/20` (**verified**: 2,290
  points — **must page past the 2,000 hosted-layer cap**, which silently
  truncates otherwise) + `WI_Private_Schools/FeatureServer/2` (828 — the
  **LATITUDE/LONGITUDE vs LAT/LON field-rename trap**), tagged
  public|private; fields SCHOOL, DISTRICT, SCHOOLTYPE, GRADE_RANGE, FULL_ADDR,
  SCHOOL_URL. Gates ≥2,200 / ≥780.
- NEW `build_wi_libraries.py` → `data/app/library-sites.json` from DPI's
  `WI_Public_Libraries_and_Branches` layer **/6** (**verified**: 482 points
  with address, phone, website, director + email, and parent system). Gate
  ≥460. Statewide — better than IL's Chicago-scoped library layer; the matrix
  cell says so.
- **Licence:** DPI's text is a reference-use disclaimer, not a redistribution
  ban ("intended for your reference use only… no guarantee of accuracy…
  derived conclusions… not attributable to the DPI") — carried verbatim into
  the source blocks (→ sources.html), aligned with the app's own
  no-legal-precision disclaimer. Item `d383fe81275e46f2a5a5c4f1a0c2eb85`
  registers in `validate_sources.py` as the annual-supersession watch.
- Two `registerNearestPointLayer` modules; operator rebuild, no weekly
  workflow (amenity precedent). Final area-rank renumber 1..19;
  `min_register_layer` 14 → 16.

**Final phase state:** 19 layers, `EXPECT_LAYERS` 19 (generated), rank order:
`wi-court-of-appeals, us-house, wi-senate, wi-assembly, wi-circuit-court,
county, school-district-secondary, school-district-unified,
school-district-elementary, county-board, county-subdivision, municipality,
zip-code, ward, police-station, fire-station, school-site, library,
post-office`. The root landing card's layer count bumps automatically
(`build_landing_page.py` reads the worksheet); the `metros.json` blurb is
re-verified to cover courts, wards and clerks in the same change they ship.

---

## Phase 3 roadmap (recorded in the guidebook backlog now, built next)

1. **`aldermanic-district` statewide — boundary + seven city rosters**
   (operator-confirmed ambition). Geometry: dissolve LTSB wards on
   **COUSUBFP + ALDERID** — never `ALDER_FIPS`, which is county-qualified and
   splits cross-county cities' districts in two (measured): 2,580 coded wards
   → ~893 districts across 166 municipalities (156 cities + 9
   trustee-district villages; exclude the CTV='T' anomaly). A per-city
   completeness gate is mandatory — 14 municipalities mix '00' placeholders
   with real ids — and **Appleton ships as a recorded gap**: Outagamie County
   submits all 50 of its Appleton wards uncoded in both 2026 editions, and the
   city's own GIS route is unverified. (LTSB's pre-dissolved
   `BAS_Live_Collection_Alderpersons` MapServer exists — 893 real + 1,731
   placeholder polygons, verified — but carries no stated terms and mutates
   mid-collection, so the licensed AGOL dissolve is preferred.) Rosters:
   Madison, Green Bay (parse the CivicPlus grid structurally, never
   flattened), Racine, Appleton, Waukesha from their own sites; Milwaukee from
   the city's own GIS layer whose ALDERPERSON attribute names all 15 alders,
   cross-witnessed weekly against the Legistar API (verify the CKAN
   alderman.zip carries the attribute before building); Kenosha from its own
   ArcGIS layer only after an independent post-April-2026 currency witness.
   Oshkosh and Janesville elect at-large (verified) — municipality-card facts,
   never aldermanic rows. Recorded blocks: Eau Claire/Janesville (Akamai),
   kenosha.org / city.milwaukee.gov (Cloudflare).
2. **`mps-school-board`** — city-scoped, the ERSB precedent: geometry from the
   city's CKAN SHP (verify contents first; `milwaukeemaps` drops ~1 in 4–8
   requests with TCP resets — build-time only, never runtime), roster from the
   MPS board page (9 members: 8 district + 1 at-large; read the real DOM
   headings, not the page's inline-JSON duplicates). Racine Unified stays a
   measured gap: the state's only other districted school board publishes
   geometry as ArcMap-generated PDFs — a Jackson-style vector-path extraction
   or a direct ask, never a raster trace.
3. **Milwaukee city layers** — `mpd-district` (CKAN SHP, CC-BY, 7 districts,
   reproject from WKID 32054; captains not shippable — the city site is
   Cloudflare-challenged, so the card links; shipping it formally revisits the
   guidebook's "police: NO HONEST ANALOG" with the city-scoped frame, exactly
   Chicago's pattern) and `milwaukee-neighborhoods` (CKAN, CC-BY, 190
   polygons). MPD squad areas (the beat analog — sublayer verified) and the
   city TID dataset are recorded candidates behind them.
4. **Standing follow-ups:** one Playwright-from-CI attempt on WEC before its
   Cloudflare block is filed permanent; the NG911 per-agency dissolve as the
   fire-boundary route; municipal clerks — the honest record is "no statewide
   source, per-county route open" (Dane, Brown and Waukesha county clerk
   directories verified current; the Milwaukee County LIO officials layer
   covers all ~19 of its municipalities once its currency is gated; the League
   of WI Municipalities directory is member-gated — a Jo Daviess-shaped
   purchase/permission conversation is the recorded alternative).

## Verification (every PR, in order)

1. `python3 scripts/generate_metro_files.py` then `--check` — never hand-edit
   a GENERATED region.
2. `python3 scripts/compose_app.py --check` — no ENGINE fence is touched this
   phase; all module code is fork-side.
3. `python3 scripts/build_coverage_gaps.py --check` (+ regenerate
   `--metro wisconsin` in PRs 1 and 7).
4. `python3 wi/scripts/validate_index.py wi/index.html` — rank lists 1:1,
   floors, the sw exactly-one-list invariant.
5. `python3 wi/scripts/build_wi_county_board_directory.py --check` — stays
   green; the supervisory geometry is untouched all phase.
6. `python3 scripts/build_landing_page.py` + `--check`,
   `build_privacy_page.py --check`, `build_manifests.py --check`,
   `build_dark_map_palette.py --check` (new layer colours feed the dark
   palette — PRs 1–4 and 8).
7. `python3 wi/scripts/validate_sources.py` — new PROVENANCE/ENDPOINTS rows
   resolve, zero FAIL.
8. Behaviour gate: serve the repo root, then
   `BASE_URL=http://localhost:8000/wi/ node wi/scripts/smoke_test.mjs` —
   `EXPECT_LAYERS` exact equality; the new anchors (`wi-circuit-court`
   "Marathon", `wi-court-of-appeals` "District III") classify at the Marathon
   point; the negative point stays honest.
9. Every builder runs its gates before its data file is committed; every
   scraper floor is proven by a real run; `check_roster_retention.py
   --base origin/main` before push.

---

## Appendix — verified source ledger (fetched 2026-08-25)

**LTSB** (ArcGIS org `WI_Legislature`, services1.arcgis.com/FDsAtKBk8Hy4cAH0;
hub gis-ltsb.hub.arcgis.com): Municipal Wards Current **7,161** (open licence;
stable-URL promise in the item; PIP verified; editions Jan 2026 = 7,138, Jul
2026 = 7,161 — and Jul 2025 also 7,161, a verified coincidence, not a
transcription); County Supervisory Current 1,589 raw (1,590 shipped with the
Trempealeau override); Cities/Towns/Villages Current; Assembly/Senate 2024
(`ASM2024`/`SEN2024`); Congressional 2022 (`CON2021`). Direct BAS MapServers at
mapservices.legis.wisconsin.gov, including the pre-dissolved Alderpersons
layer (893 real + 1,731 placeholders; no stated terms; mutates during
collection windows). Vintage trap on record: an item titled "(July 2026)" has
a `_July_2025` URL — currency is `lastEditDate`, never a name.

**Chamber vintage:** TIGERweb Legislative layers 1/2 self-describe as "2024
State Legislative Districts — January 1, 2025 vintage"; 10/10 test-point
agreement with LTSB's 2024 layers; measured disagreement with the 2022 layers
exactly where the remedial map moved lines (Appleton sen 19→18 / asm 57→52,
Madison asm 76→77). The shipped geometry is the post-remedial map — no
rebuild.

**wicourts.gov:** every page answered plain curl 200 — no captcha, no
Cloudflare. Circuit judges table ~260 (footer-dated 2026-08-24) + contact
directory (branch, courthouse, phone); COA 16 judges (the nav menu is a stale
former-judge list, 6/16 wrong — read the content cards); municipal courts 219
(71 joint serving 2–23 municipalities; the only statewide mapping is a 531 KB
PDF whose subset fonts garble extraction) → record-drop. Statutes fetched:
753.06 (circuits; the chapter page lazy-loads and truncates at 52/63 — cite
per-subsection URLs), 752.11 (COA composition, unchanged since 1977), 752.03
(the 4/4/3/5 seat split).

**Clerks:** elections.wi.gov and myvote.wi.gov are Cloudflare-challenged (403
`Cf-Mitigated: challenge` on every path, media downloads and API routes
included) — recorded, never defeated. Blue Book 2025-26 county-officers table
(72 clerks + party; two-column PDF). wisconsincountyclerks.org (72 per-county
pages; plain UA WAF — browser headers pass; robots Crawl-delay 10).
Wis. Stat. 7.20(1)-(2): appointed election commissions exist only in Milwaukee
County and the City of Milwaukee.

**USGS structures** (carto.nationalmap.gov …/structures/MapServer): L53 police
807 / L51 fire 1,743 / L38 post offices 1,244 in the WI envelope; republished
July 2026; spot-checks passed (7/7 MPD district stations, Madison 14/14 fire);
one verified ghost record (Town of Madison FD, defunct 2020).

**DPI** (AGO org Wisconsin_DPI): Public Schools /20 = 2,290 (over the 2,000
cap — page); Private Schools /2 = 828 (LATITUDE/LONGITUDE rename); Public
Libraries and Branches **/6** = 482 with director + email + system; licence is
a reference-use disclaimer with no redistribution ban (text captured); item
`d383fe81275e46f2a5a5c4f1a0c2eb85` is the supersession watch.

**County-board recoveries:** Milwaukee County LIO FeatureServer/46
(`Sup_Name`/`Email_Addr` 18/18, edited 2026-06-29; Legistar
`webapi.legistar.com/v1/milwaukeecounty` as the independent witness — its
OData date filter is silently ignored and end dates can be aspirational, so it
is a witness, never a source); Racine County AGO
`County_Board_of_Supervisors_WFL1/0` (21/21, edited 2026-04-23);
`outagamie.gov` (36/36 with e-mails — the county moved domains, which is why
its old block record went stale). The remaining seven measured shut, Rock
included (LAN-only portal; public host resets).

**Milwaukee city:** data.milwaukee.gov CKAN, CC-BY (police districts, voting
wards + polling places, aldermanic districts, neighborhoods 190, TID);
milwaukeemaps ArcGIS drops ~1 in 4–8 requests with TCP resets — build-time SHP
downloads only, never a runtime dependency; MPD_geography sublayers 0
reporting districts / 1 squad areas / 2 districts; election_geography/3 = MPS
board districts (8).

**Special districts** (single citation: Legislative Council Special Purpose
Districts IssueBrief, Aug 2024): MMSD appointed (s. 200.09(1)(b)), boundary
under SEWRPC copyright; WTCS 16 districts, boards appointed (DPI 2019-build
geometry); town sanitary / lake districts — elected commissioners exist but
zero statewide geometry (DNR hub measured 0 with a positive control); park
districts not a Wisconsin unit of government; library boards appointed
(s. 43.54); drainage — DATCP publishes 195 districts, boards court-appointed;
NG911 (WI_OEC_GIS, ~weekly): FireBoundary 3,046 / LawEnforcementBoundary
3,101 / PSAP 208.

**Legislature:** docs.legis.wisconsin.gov/2025/legislators/{assembly,senate} —
132 members, district-id-keyed DOM with office room, phones, fax, e-mail; no
blocks; the URL is session-scoped and the unversioned path 404s. Open States
wi.csv: capitol office fields 0/132, e-mail 132/132 (currently discarded by
the builder); `first_url()` ships the oldest session link.

**Environment note:** web.archive.org is blocked by this sandbox's egress
proxy (fine from CI or a normal network), and a 403 with a proxy JSON body is
the proxy, not the site — never record a host from a local run without
checking who answered.

# SF Port — §0 City Worksheet (Thread 0 deliverable)

Working artifact for porting District Explorer to **San Francisco**, per
`docs/METRO_EXPANSION_PLAYBOOK.md` Part I §0. This is the parameter block the
rest of the port refers back to. It lives here on the `next-metro-port` branch
until the `DistrictExplorer-SF` fork repo exists, then moves into that repo as
its own worksheet (the NYC record — `docs/archive/METRO_EXPANSION_NYC.md` — is
the model for a completed one).

**Honesty markers** (repo convention — never guess officeholders or IDs):
- ✅ **Confirmed** — established from an authoritative source *this session* (July 2026); see the verification log.
- 🔎 **Needs live-fetch** — value is proposed, but the playbook's VERIFIED bar means *fetching that exact endpoint and seeing records* before wiring. Not yet done.
- ⏳ **TBD (mid-port)** — cannot be finalized until the layer roster / anchor files exist (§0 marks these).
- 🎛️ **Operator decision** — a choice for Adam (domain, brand, repo).

---

## The worksheet

| Parameter | San Francisco value | Status |
|---|---|---|
| `CITY_NAME` | San Francisco | ✅ |
| Metro slug (`THIS_METRO`) | `sf` | ✅ (matches the `nyc` convention) |
| `METRO_NAME` | San Francisco | ✅ |
| `STATE_FIPS` | `'06'` (California) | ✅ |
| County structure | **City and County of San Francisco** — consolidated, **coterminous** (city = county), FIPS **06075**. One county, no multi-county partial-coverage problem. The Board of Supervisors is simultaneously the city council **and** the county board. | ✅ — the single biggest simplifier vs. Chicago; kills the §7 multi-county gotcha outright |
| School governance | **One unified district (SFUSD).** Board of Education = **7 commissioners elected *at-large* (citywide)**, *not* by district → per §3 step 4's at-large rule there is **no districted `school-board` layer** (the biggest roster delta from Chicago's 10 ERSB districts). Assignment is **choice-based / lottery** (attendance area is only a tiebreaker) → the schools group needs NYC-style honest "not a guaranteed school" empty states. | ✅ governance; 🔎 zone datasets |
| `BBOX` | `{minLng:-122.517, minLat:37.703, maxLng:-122.353, maxLat:37.833}` — mainland peninsula + Treasure Island. **Farallon Islands** (~-123.00, 37.70) are legally SF but excluded from the box (far-west exclave — handle as MultiPolygon per §7, don't let them blow out the bias box). | 🔎 (tighten against the real county polygon at conversion) |
| `CENTER` + zoom | `[37.7749, -122.4194]`, initial zoom **12**, `minZoom` **11** (SF is compact — ~47 mi², smaller than Chicago, so one notch tighter than Chicago's 11/9). | 🔎 (eyeball after boot) |
| Permalink sanity bounds | lat **37.60–37.95**, lng **-122.60–-122.30** (deliberately looser than `BBOX` — greater SF/peninsula; independent constant, §1's easiest-to-miss row). | 🔎 |
| Open-data portal(s) | **`data.sfgov.org` — Socrata** (DataSF; mature, same platform + SoQL grammar as Chicago/NYC → the engine's whole Socrata stack ports as a host-constant swap). Consolidation means nearly all civic geometry lives on DataSF; SF Enterprise GIS / `sfgov` ArcGIS backs a few layers. | ✅ platform; 🔎 per-dataset |
| App token needed? | Start anonymous; register a **free Socrata app token** at the first 403/429. NYC's DataSF twin WAF-throttled anonymous clients during research, so budget for one (public constant in `index.html`, `X-App-Token` repo secret for CI — §5.4). | 🔎 |
| Geocoders | **Photon** (SF-biased type-ahead) + **Nominatim** (POI, submit-time, serial ≥1s queue) — Chicago's stack, unchanged. **No city-run keyless autocomplete API found** (SF publishes the **EAS** address-point dataset `3mea-di5p` on DataSF but not a GeoSearch-style endpoint), so §5.3 rule → fall back to Photon/Nominatim. EAS noted as a possible future self-hosted-Pelias upgrade, not a launch dependency. | ✅ decision; 🔎 EAS-upgrade |
| School profile URL | SFUSD school pages under `sfusd.edu` (exact deep-link slug pattern to confirm). | 🔎 |
| Domain / CNAME | **`sf.chidistricts.com`** (proposed — mirrors `nyc.chidistricts.com`). | 🎛️ |
| Feedback email | `adam@overberg.co` | ✅ |
| Repo | **`ThursdaysFamous/DistrictExplorer-SF`** (public, same account as CHI/NYC — to create). | 🎛️ |
| Brand | Proposed: **International Orange** (Golden Gate Bridge, ≈`#C0362C`) primary + a bay-blue / SF-gold secondary; SF-flag phoenix as the masthead emblem. | 🎛️ / ⏳ |
| Offline anchors *(mid-port)* | Candidates: **`supervisor-districts` (11)**, **`analysis-neighborhoods` (41)**, and a third stable one (**`police-districts` (10)** or the countywide **Superior Court** = 1 feature, weak). Use **`supervisor-districts`** as the out-of-scope mask tiler — 11 districts tile the city exactly (Chicago's ERSB / NYC's boroughs analog). | ⏳ |
| Ground truth *(mid-port)* | Primary: **SF City Hall `37.77927,-122.41924`** → Supervisor District 5 (verify), + its neighborhood + police district. Second point (different districts): **Ferry Building `37.79550,-122.39370`** → Supervisor District 3. Negative point: mid-Bay or Pacific (e.g. `37.83,-122.37`) → honest no-match on the shoreline-clipped supervisor/neighborhood layer (§4 negative-point). | ⏳ — assert only after classifying against the converted files |
| `EXPECT_LAYERS` *(mid-port)* | TBD — final registered-layer count (expect **fewer** than Chicago's 33 / NYC's 24-analog: SF drops the districted school board, districted supreme court, separate county commissioner, and board-of-review layers). | ⏳ |

---

## Roster implications worth flagging now (headline deltas from Chicago)

Full §3-step-4 map-or-drop table is Thread 4 work, but the structural consequences of SF's government shape are already clear and shape the whole port:

- **Board of Supervisors (11) is one shared-loader layer doing two jobs** — city council *and* county board (consolidated). Chicago needs separate `ward` (50) + `commissioner`; SF collapses both into 11 supervisor districts. (§7 "one boundary hosts several offices → one cached loader.")
- **Drop the districted `school-board` layer** — SF's Board of Education is elected **at-large**; no district geometry exists to map. The board becomes a citywide office (at-large rule: link/defer, never a polygon).
- **Drop `il-supreme-court` analog** — the California Supreme Court is statewide (not districted). CA Courts of Appeal have districts but justices are **appointed** → link-only at most.
- **Drop `ccbr` / `commissioner` analogs** — SF's assessment-appeals board is appointed; there's no elected county board of review, and no county commissioner separate from the supervisors.
- **District Attorney is countywide (citywide)** — unlike NYC's five borough DAs, SF's DA is one at-large office → no DA polygon layer.
- **Federal/state tier is free & standard** — CA Senate (40) / Assembly (80) / US House (52) via TIGERweb `STATE='06'` + `congress-legislators` (re-parameterize `IL`→`CA`, 17→52). SF spans a handful of each.
- **Candidate SF-specific *add*: BART Director districts** — the regional transit board **is elected by district**, and part of the network sits in SF. A genuinely local, honestly-districted, roster-backed layer with no Chicago analog. Flag for the roster thread.

Net: SF's *political* stack is **thinner** than Chicago's (consolidation + at-large offices remove several districted layers), but cleaner — and the schools group leans on NYC's choice-based honest-empty precedent rather than Chicago's attendance-guarantee model.

---

## Draft METRO config values (the §1 constant swaps — partial, §0-level only)

The layers / anchors / data-files / rosters sections of a real `metro-worksheet.json`
are filled during the module threads; this is only the config-level block.

```jsonc
{
  "this_metro": "sf",
  "metro_name": "San Francisco",
  "metro_bbox": { "minLng": -122.517, "minLat": 37.703, "maxLng": -122.353, "maxLat": 37.833 },
  "metro_center": [37.7749, -122.4194],
  "permalink_gate": { "minLat": 37.60, "maxLat": 37.95, "minLng": -122.60, "maxLng": -122.30 },
  "socrata_host": "https://data.sfgov.org",
  "socrata_app_token": "",                       // set at first 403/429
  "repo_issues": "https://github.com/ThursdaysFamous/DistrictExplorer-SF/issues/new",
  "feedback_subject": "San Francisco District Explorer feedback",
  "exports_name": "SFExplorer",                  // rename ChiExplorer in index.html + smoke_test.mjs together
  "domains": { "canonical": "https://sf.chidistricts.com/" }
}
```

**Cross-metro footer (`METRO_EXPLORERS`) — add this entry in *every* fork (CHI, NYC, SF) per §1:**

```jsonc
{ "id": "sf", "label": "San Francisco", "url": "https://sf.chidistricts.com/", "emoji": "🌉",
  "bbox": { "minLng": -122.60, "minLat": 37.60, "maxLng": -122.30, "maxLat": 37.95 } }
```

---

## Verification log (this session, July 2026)

Established from authoritative sources — **not** yet the playbook's endpoint-level VERIFIED (no DataSF endpoint fetched this session):

- **Consolidated city-county / coterminous** — SF government structure. *(Wikipedia: Government of San Francisco.)*
- **Board of Supervisors: 11 districts, elected by district, nonpartisan 4-yr terms.** *(Wikipedia: SF Board of Supervisors; Ballotpedia 2026.)*
- **Board of Education: 7 commissioners, elected at-large citywide.** *(Wikipedia: SF Board of Education.)*
- **DataSF is Socrata; SFUSD Attendance Areas published there (`e6tr-sxwg`, 2024-25).** *(DataSF; dev.socrata.com foundry.)*
- **Assignment is choice-based/lottery, attendance area a tiebreaker.** *(SFUSD student-assignment pages; KQED.)*
- **EAS address points on DataSF (`3mea-di5p`); no city keyless autocomplete geocoder surfaced.** *(DataSF EAS dataset.)*

## Still to verify at build time (the 🔎 rows)

1. One live `intersects(the_geom,'POINT(lng lat)')` on a DataSF dataset at a known SF landmark — validates endpoint + geometry column + app-token posture in one shot (§6.5).
2. Exact dataset IDs + geometry route + observed field names for: supervisor districts, analysis neighborhoods, police districts/companies, SFPD/SFFD stations, ES/MS/HS attendance zones (rotate yearly → freshness chore), SFUSD schools points.
3. SFUSD school-profile deep-link pattern.
4. BART director-district geometry + elected roster source (candidate add).

## Resolved data registry (by thread)

**Thread 1 — offline anchors (2026-07-17):** `supervisor-districts` → DataSF table `hcgx-vtsb` (11); `analysis-neighborhoods` → `j2bu-swwd` (41); `police-districts` → `d4vc-q76h` (10). Each mapshaper-simplified into `data/app/` and validated on the 2,000-point protocol (≥99.5% agreement, 0 overlaps). Ground truth City Hall → Supervisor **5** / **Tenderloin** / **NORTHERN**; negative point corrected to open Bay `37.800,-122.355`.

**Thread 2 — safety point layers (2026-07-17):**

| Layer | Dataset | Route / loader | Fields the card reads | Verified |
|---|---|---|---|---|
| `police-station` (nearest 3) | DataSF **Police Stations** `rwdu-9wb2` (10 rows) | `.geojson` route serves real Point geometry → `makeCachedLoader` | `district_name`, `address`, `telephone_number` | ✅ City Hall → Tenderloin/Northern/Southern Stn |
| `fire-station` (nearest 3) | DataSF **City Facilities** `nc68-ngbr`, `$where=department_name='Fire Department' AND common_name like 'Fire Station #%'` (44 active) | `.geojson` route omits point geometry (coords in `latitude`/`longitude` props) → `makeSocrataPointLoader` | `common_name`, `address` | ✅ City Hall → Stations #36/#3/#5 |

**Safety drops (no honest SF analog in open data — never invent geometry, per §3 step 4):**
- **police-beat / sector** — SFPD publishes no current patrol-beat boundary; the only "beats" dataset (`jc6y-96en`) is Parking Control's, a different body. Chicago's `police-beat` `subOf` layer has no SF counterpart.
- **fire-battalion** — SFFD organizes into battalions/divisions, but no battalion or division *boundary* is published on DataSF or SF's ArcGIS; battalion appears only inside the live incident feed, not as a standalone polygon to classify against. (NYC ships `fire-battalion` because DCP publishes the boundary; SF does not.)

The `nc68-ngbr` "Fire Station #%" filter excludes 12 non-station Fire-Department rows (HQ, Bureau of Equipment, Division of Training, Chief's Residence, and a decommissioned "Old Fire Station 21") — showing those as a "nearest station" would be dishonest.

**Thread 3 — schools (2026-07-17):**

| Layer | Dataset | Route / loader | Fields the card reads | Verified |
|---|---|---|---|---|
| `elementary-attendance-area` (point-in-polygon) | DataSF **SFUSD School Attendance Areas (2024-25)** `e6tr-sxwg` (58 elementary zones) | `.geojson` serves MultiPolygon → `makeCachedLoader`; **bespoke** `registerLayer` (not `registerSchoolZone`) so the card can state the lottery caveat | `sch_lng_na` (school), `aaname` | ✅ City Hall → Tenderloin Community School |
| `school-site` (nearest 3) | DataSF **Schools** `7e7j-59qk`, `$where=status='Active'` (232 active; public/charter/private) | `.geojson` serves Point geometry, but we filter status → `makeSocrataPointLoader` | `school`, `low_grade`/`high_grade`, `charter_yesno`/`public_yesno`, `street_address` | ✅ City Hall → Mission Montessori / Tenderloin Community / Millennium |

The elementary card carries an explicit honesty caveat — "SFUSD assigns elementary seats by lottery; this attendance area is a tiebreaker preference, not a guaranteed seat" — and links to `sfusd.edu/enroll` (verified 200). `e6tr-sxwg` is year-versioned (2024-25) → a Thread-5 freshness chore (a new `SY####` edition supersedes it).

**Schools drops (no honest SF analog in open data — never invent, per §3 step 4):**
- **Middle / High attendance zones** — only *elementary* attendance areas are published (the `e_aa_` field prefix). SFUSD middle school is a feeder pattern with no boundary dataset; high school is citywide choice with no zones. (CHI ships ES/MS/HS zones because CPS publishes all three; SF publishes only ES.)
- **CPS-style administrative networks** — SFUSD is one undivided district with no "network" sub-regions carrying a named chief, so the inherited `registerCpsNetwork` factory stays unused.
- **Districted school board** — already dropped in Thread 0 (SF's Board of Education is elected at-large).

Also removed the inherited Chicago `schoolProfileHtml` helper (hardcoded `cps.edu`, unreferenced in the SF fork).

**Thread 4 — political / legislative chambers (2026-07-17):**

| Layer | Source | Field → district | City Hall |
|---|---|---|---|
| `congress` (U.S. House) | Census TIGERweb Legislative MapServer layer 0, `STATE='06'` (52 CA districts) | `CD119` + NAME fallback | ✅ District 11 |
| `ca-senate` (CA State Senate) | TIGERweb layer 1 / SLDU, `STATE='06'` (40) | `SLDU` (`011`→11) | ✅ District 11 |
| `ca-assembly` (CA State Assembly) | TIGERweb layer 2 / SLDL, `STATE='06'` (80) | `SLDL` (`017`→17) | ✅ District 17 |

All three register through the shared `registerIlgaChamber` factory with **live TIGERweb** geometry (`loadTigerLayer`, retargeted Illinois FIPS 17 → California FIPS 06). Rosters ship as **empty placeholders**, so each card degrades to the honest "district number + official chamber directory" — no guessed names. Point-in-polygon verified against the full CA layers (single-containment at City Hall).

**Thread 5 will:** pre-build the decadal geometry into same-origin `data/app/{congress,ca-senate,ca-assembly}-districts.json` (`build_legislative_boundaries.py`, `STATE='06'`, via the `opts.loadDistricts` hook — turning the ~8–9 MB statewide fetch into a ~200 ms load) and add the scraped officeholder rosters (US House / CA Senate / CA Assembly, plus the SF supervisor roster) via scraper→builder pairs + weekly workflows.

**Removed dead code:** the inherited Chicago Cook County political loader (`loadCookCountyLayerGeoJSON` / `COOK_COUNTY_POLITICAL_BOUNDARY`) — a Thread-0 re-core miss (its layer registration was deleted but the helper survived, unreferenced). The Cook County Commissioner / Board of Review analogs were already dropped in Thread 0 (SF has no county board separate from the Supervisors).

**Thread 5 (pipeline, part 1) — pre-built legislative geometry (2026-07-17):**

The three chambers moved from live TIGERweb to same-origin, cache-first `data/app` files via `build_legislative_boundaries.py` (wired through the `opts.loadDistricts` hook):

| File | Districts (SF window) | Size | Validation (2,000-point protocol) |
|---|---|---|---|
| `congress-districts.json` | 6 | 11.9 KB | 99.95% agreement, 0 overlaps |
| `ca-senate-districts.json` | 4 | 11.3 KB | 100% agreement, 0 overlaps |
| `ca-assembly-districts.json` | 8 | 24.0 KB | 100% agreement, 0 overlaps |

**SF-specific builder deviation (recorded):** unlike the reference (which ships Illinois statewide), California's districts are far larger/more numerous (52/40/80), so each is **clipped to the SF permalink-gate window** with mapshaper (`-clip bbox`) — ~47 KB total vs the ~26 MB the three statewide layers would be. Clipping is geometrically exact, so point-in-polygon *inside* the window is identical to the full district; `validate()` re-checks that against the unclipped fetch. The chambers now classify **offline** in CI (the smoke test asserts US House 11 / CA Senate 11 / CA Assembly 17).

**Negative-point moved (§7):** the TIGERweb chambers are **water-inclusive** — they cover the SF Bay — so the old Bay negative point (37.80, -122.355) now falls *inside* a district and `validate_index`'s "negative point misses every anchor geometry" gate rejected it. Moved to the **open Pacific west of Ocean Beach, beyond CA state waters** (37.74, -122.59), which misses every layer including the chambers (the SF analog of CHI's Indiana-waters negative point).

**Thread 5 (pipeline, part 2) — officeholder rosters (2026-07-18):**

| Roster | Source | Builder | Count | City Hall |
|---|---|---|---|---|
| `congress-roster.json` | unitedstates/congress-legislators | `build_congress_roster.py` (filter CA) | 51 (52 seats, 1 vacant) | Rep. Nancy Pelosi (D) |
| `ca-senate-members.json` | OpenStates `ca.csv` | `build_ca_legislature_roster.py` (upper) | 40 | Sen. Scott Wiener (D) |
| `ca-assembly-members.json` | OpenStates `ca.csv` | `build_ca_legislature_roster.py` (lower) | 80 | Asm. Matt Haney (D) |

Each chamber's `loadRoster` now fetches its same-origin roster and joins by district number (the `registerIlgaChamber` path). **Names are never guessed:** a vacant district or a fetch failure degrades to "district number + chamber directory". Refreshed weekly by `update-congress-roster.yml` (Mon) and `update-ca-legislature-roster.yml` (Tue), each opening a PR for a human look before it ships. The chambers now render + are smoke-tested with the officeholder, fully offline.

**Pipeline cleanup:** removed the inherited Chicago roster pipeline that doesn't apply to SF and would otherwise run weekly and inject Chicago rosters — 8 scripts (`ilga_scraper` / `build_il_roster` / `cpd_district_scraper` / `build_cpd_roster` / `ccpsa_scraper` / `build_ccpsa_roster` / `will_county_board_scraper` / `build_will_county_board_roster`) and 4 workflows (`update-{ilga,cpd,ccpsa,will-county-board}-roster.yml`).

**Thread 5 (pipeline, finish) — supervisor name + source manifest + pin fix (2026-07-18):**

- **SF supervisor name.** Converted `supervisor-district` from the `registerPolygonLayer` factory (no roster-join hook) to a bespoke `registerLayer` that joins `data/app/sf-supervisor-members.json` by district number — so the card names the officeholder (City Hall → District **5** / Supervisor **Bilal Mahmood**). Roster built by `build_sf_supervisor_roster.py` from DataSF Current Supervisor Districts (`hcgx-vtsb`, `sup_name`, all 11), refreshed weekly by `update-sf-supervisor-roster.yml` (Wed) via PR. Names never guessed: a district absent from the source degrades to the Board-of-Supervisors link. `min_register_layer` 7 → 8 (the bespoke block adds a literal `registerLayer(`).
- **Source-freshness manifest.** Re-derived `validate_sources.py` from CHI's inherited manifest to SF's actual sources: 4 live DataSF datasets (`rwdu-9wb2` Police Stations, `nc68-ngbr` City Facilities/fire, `e6tr-sxwg` SFUSD attendance areas *year-versioned*, `7e7j-59qk` Schools), 6 pre-built boundary files (3 DataSF anchors + 3 TIGERweb CA chambers), 1 live endpoint (Census ZCTA). **Catalog fix:** DataSF is *not* indexed by the federated `api.us.socrata.com`, so newer-edition search now hits the portal-local `data.sfgov.org/api/catalog/v1` with no `domains`/`only` filters (SFUSD editions are `federated_href`); `e6tr-sxwg` itself is an uncatalogued derived view, so the search compares against catalog sibling `…School Attendance Areas <year>` editions. Full run: **0 FAIL · 0 WARN · 11 OK**.
- **District-office pin fix** (reported not working). Root cause: `cleanPoiAddress` only strips a unit designator that is its own comma-part, but OpenStates packs the suite into the street segment ("455 Golden Gate Ave. Suite 14800, …"), which Nominatim won't geocode. Because the engine is re-spliced from CHI's pinned release at deploy, the fix is **data-side**: `build_ca_legislature_roster.py` `normalize_address` inserts a comma before an embedded unit ("… Ave., Suite 14800, …") so `cleanPoiAddress` drops it and the pin drops. Verified end-to-end (Wiener/Haney district office → 455 Golden Gate Ave.).

## Performance parity for the SF port (see playbook §13)

The reference forks' measured perf campaign splits into what SF **already has** and what SF **must re-earn** — playbook §13 is the full guide; this is the SF-specific cut.

**Already in the SF seed (engine-fenced — do NOT delete in the Thread-0 re-core):** bbox pre-reject in `findFeatureContaining` (R2-6), `whenIdle` scope-mask boot-defer (R2-3), drop-shadow pan-pause (R2-5), memoized/incremental click + toggle paths (P7/P8/P11), loader hardening (`geometryPrecision=6`, timeouts, `hasUsableGeometry`), `loadArcGISPaged` + `makeSocrataPointLoader`, geocoder debounce + serial POI queue, the whole `sw.js` handler block. SF's `index.html` is byte-identical to the current CHI reference (verified), so it carries all 45 engine fences at their latest state. **Guard after the re-core:** `check_engine_parity.py index.html --against https://chidistricts.com/ --strict` clean.

**SF must re-earn (metro-specific — §13.2):**
- *Thread 0 `<head>`:* inline `leaflet.css`; self-host + subset SF's fonts via `scripts/build_fonts.py` (International Orange brand faces, `font-display: swap`, metric-matched fallback) and precache them in `SHELL_URLS`; defer `leaflet.js` + gate boot on `DOMContentLoaded` as `initSFExplorer()` (defer **both** — the bare-defer trap).
- *Thread 0 preconnects (≤4):* `preconnect` cdnjs + the CARTO basemap tile shards (the LCP is a tile); `dns-prefetch` `data.sfgov.org`, `photon.komoot.io`, `nominatim.openstreetmap.org`.
- *Thread 5 pipeline:* `build_legislative_boundaries.py` with `STATE='06'` → same-origin cache-first `data/app/{congress,ca-senate,ca-assembly}-districts.json` (CA U.S. House 52 / State Senate 40 / State Assembly 80), simplified through the §6.7 gate — turns the ~5.7 s TIGERweb query into a ~200 ms fetch. The engine's `opts.loadDistricts` hook is already present.
- *Thread 6:* measure on **production PSI mobile** after deploy (sandbox scores are a lower bound); expect an LCP-bound frontier (~78) — don't chase past it.
- **Don't** implement the canvas renderer (§13.4) — inherit it when the reference ships it.

## Operator decisions — RESOLVED (2026-07-16)

1. ✅ **Repo created & seeded** — `ThursdaysFamous/DistrictExplorer-SF` (public), seeded byte-identical from the CHI tree (engine/gates/CI + this worksheet).
2. ✅ **Domain** — `sf.chidistricts.com` (Thread 0 points the CNAME).
3. ✅ **Brand** — International Orange (Golden Gate) direction confirmed.

*Outstanding operator item (not blocking the SF port):* the Claude GitHub App lacks repository-**creation** permission (Administration: write) — granting it would enable hands-off creation of future metro forks.

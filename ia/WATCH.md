# WATCH.md — redistricting watch calendar

The one place the dates live: *when to look* for boundary and roster changes in this
instance's sources. The repo's `docs/REDISTRICTING_RUNBOOK.md` is *what to do* when a
boundary changes. Update the "Last done" column each time you complete a row — a
checkpoint with a stale date is a checkpoint that didn't happen.

---

## Standing (automated — verify, don't perform)

| Cadence | What | Where | You do |
|---|---|---|---|
| Weekly (Mon 14:30 UTC) | U.S. House (IA) roster refresh | `.github/workflows/update-ia-congress-roster.yml` → PR on change | Review + merge the PR; a week with a surprise diff is worth a look at the source |
| Weekly (Tue 14:30 UTC) | Iowa Senate + House roster refresh (Open States ia.csv + legis.iowa.gov office enrichment) | `.github/workflows/update-ia-legislature-roster.yml` → PR on change | Review + merge the PR — especially after an Iowa general (November, even years) and each January seating |

---

## Per-election — the seats above the boundaries

| When | What | Last done |
|---|---|---|
| After each Iowa general (November, even years) and any special election | The chamber rosters turn over; the weekly Open States refresh picks it up, but verify the first post-election PR against the Legislature's own directory before merging | 2026-08-27 (initial build: 49/50 Senate seats, 100/100 House seats) |
| After each U.S. general (November, even years) | The delegation turns over; the weekly congress-legislators refresh picks it up | 2026-08-27 (initial build: 4/4) |

---

## Per-decade — the census redistricting cycle

| When | What | Last done |
|---|---|---|
| After each decennial census (next: 2031–2032) | Congressional + legislative districts redraw: re-run `ia/scripts/build_legislative_boundaries.py` (all three targets — see its docstring for why the default differs from Wisconsin's), confirm the district counts against the apportioned delegation and the 50/100 chambers, and re-verify the smoke anchors against the rebuilt geometry | 2026-08-27 (all three built at 100.00% agreement) |
| Mid-decade — Iowa specifically | County-level SUPERVISOR districts move off the census cycle under Iowa's own law: **Senate File 75** (signed 2025-04-11) forced Story, Johnson and Black Hawk counties from at-large to district elections for November 2026. `ia/scripts/build_ia_supervisor_districts.py` pins the state aggregate's vintage (`LSA_LAST_EDIT_MS` = 2024-01-30) and refuses to build silently if it ever moves — re-run the builder and re-verify all three counties' PLANTYPE the day that check fires, not just the three named here | 2026-08-26 (Black Hawk shipped real geometry from its own hosted GIS; Story and Johnson shipped as county-level TRANSITIONING placeholders, both SOS-approved but no GIS service found for either) |
| Iowa specifically, no fixed cadence | Story's and Johnson's `TRANSITIONING` placeholders are the layer's known incompleteness, not a permanent design: re-check both counties' own sites (and a fresh ArcGIS org sweep, the Black Hawk precedent) periodically for a published district-map GIS service, which would let a future build replace the county-level fallback with real sub-district geometry the same way Black Hawk's was found | 2026-08-27 (first build; both still PDF-only) |
| Iowa specifically, no fixed cadence | Jones County is entirely absent from the state's own CountySupervisorDistricts aggregate (measured by name and by FIPS 105) — re-check on each vintage change (see the row above) whether the state has added it, and separately whether the county's own vector PDF map (`jonescountyiowa.gov/files/board_of_supervisors/bos_districts_final_23073.pdf`) is worth a Jackson-County-IL-style extraction | 2026-08-27 (first build; recorded as a coverage-gaps.json gap) |
| Iowa specifically, no fixed cadence | `county-subdivision` is live-fetched (no builder script, no committed data/app file — `ia/index.html`'s `tigerStatewideLoader`), so TIGERweb's own vintage bumps (this layer's metadata reads "January 1, 2025 vintage" as of this build) reach the app with nothing to rebuild. What CAN silently go stale is the card's three-way type classification (`township`/`city`/`ut`, read from `LSADC` via the NAME-minus-BASENAME suffix) — periodically re-run the tally query (`WHERE STATE='19'`, group by `LSADC`) and confirm it still returns exactly the three values this build measured (44 ×1,600, 25 ×62, 46 ×1); a fourth value would render with no Type row rather than break, which is safe but worth a look | 2026-08-27 (first build; 1,663 records, 3 LSADC values) |
| Iowa specifically, no fixed cadence | `municipality` is likewise live-fetched (same `tigerStatewideLoader`) with nothing to rebuild — new incorporations/dissolutions reach the app automatically. Nothing to classify (its `LSADC` is uniformly 25 — measured 2026-08-27), so unlike `county-subdivision` there is no derived value that can drift; if a periodic re-check ever turns up a second `LSADC` value, that is the signal Iowa has grown a second incorporated-place class and the card would need one | 2026-08-27 (first build; 939 records, 1 LSADC value) |
| Iowa specifically, per school year (consolidations effective each July 1) | School districts consolidate independently of any census: TIGERweb's `School/MapServer/0` (325 as of this build) already trailed the Dept. of Education's own current layer by one district — Orient-Macksburg dissolved into Nodaway Valley for 2026-2027, and TIGERweb's federal vintage hadn't caught up when this shipped. `ia/scripts/build_ia_school_districts.py`'s `DISSOLVED_INTO`/`EXPECT_TIGER`/`EXPECT_DE` constants gate on the counts it knows about and fail loudly the day either source's count moves again — re-derive the reconciliation (which district, into which neighbor) the same way this one was found: diff the DE org's newest and previous school-year-versioned layers (`IowaSchoolDistricts<YYYY>_<YYYY+1>`) by name, then spatially sample the dissolved district's old boundary against the new layer | 2026-08-27 (first build; DE layers for 2026-2027 and 2025-2026 both fetched and diffed the same day) |
| Iowa specifically, no fixed cadence | `zip-code` and `post-office` are both live-fetched by an Iowa bounding envelope, no builder script and nothing to rebuild — new ZCTAs and post offices reach the app automatically. Neither carries a derived classification that can drift (no `LSADC`-style field this app reads), and neither is a fixed count to gate on (envelope queries move as ZCTA boundaries and post offices near the state line change) — this row exists only so both live-fetched sources are on record, not because either needs periodic re-checking | 2026-08-27 (first build; 1,443 ZCTAs and 1,170 post offices measured in-envelope) |

---

## Unresolved — confirm at the next legislature roster refresh

| What | Why it's here |
|---|---|
| Whether `legis.iowa.gov/legislators/{senate,house}`'s per-legislator profile-page URLs (`…/legislator?personID=<id>`) are session-scoped like Wisconsin's biennium-versioned `docs.legis.wisconsin.gov/<biennium>/…` path, or evergreen | Not confirmed in this PR's research — `ia_legislature_scraper.py` sources every personID fresh from the Open States CSV on each run rather than caching IDs, which sidesteps the question for now, but if the state ever moves to session-scoped profile URLs the scraper's floor (45/93) would start silently failing rather than reading a frozen roster the way Wisconsin's BIENNIUM constant would. Watch the weekly workflow's floor-failure behavior, not a calendar date |
| Whether the "Business Address" field's two observed ZIP variants (50319 and 50311, both "1007 E Grand Ave, Des Moines, IA") are both currently correct, or one is a site error | Low-stakes (both identify the Capitol) — `build_ia_legislature_roster.py`'s honesty assertion checks the street/city/state prefix only, deliberately tolerant of this |

---

## Grow this file

Every new layer ships with a row here naming when its source moves (school-year datasets
rotate every summer; county precinct files change per election; rosters change per election
and per resignation). A source with no row is a source nobody is watching.

# WATCH.md — redistricting watch calendar

The one place the dates live: *when to look* for boundary and roster changes in this
instance's sources. The repo's `docs/REDISTRICTING_RUNBOOK.md` is *what to do* when a
boundary changes. Update the "Last done" column each time you complete a row — a
checkpoint with a stale date is a checkpoint that didn't happen.

---

## Standing (automated — verify, don't perform)

| Cadence | What | Where | You do |
|---|---|---|---|
| Weekly (Mon 13:30 UTC) | U.S. House (WI) roster refresh | `.github/workflows/update-wi-congress-roster.yml` → PR on change | Review + merge the PR; a week with a surprise diff is worth a look at the source |
| Weekly (Tue 13:30 UTC) | WI Senate + Assembly roster refresh (Open States wi.csv) | `.github/workflows/update-wi-legislature-roster.yml` → PR on change | Review + merge the PR — especially after a Wisconsin general (November, even years) and each January seating |
| Weekly (Thu 14:30 UTC) | County board supervisors, 20 counties | `.github/workflows/update-wi-county-board-roster.yml` → PR on change | Review + merge. **A county DISAPPEARING from the roster is the signal that matters**: the scraper reads each county with its direction pinned, so a page that has reshaped fails its count guard and is skipped rather than shipping a shifted roster. Go and re-read that county's page |

---

## Semiannual — the county supervisory filing windows

| When | What | Last done |
|---|---|---|
| Shortly after **15 January** and **15 July** | Wis. Stat. 5.15(4)(br)1 makes every county file its current supervisory district boundaries with LTSB on those two dates, and LTSB republishes the statewide layer. Re-run `wi/scripts/build_wi_supervisory_districts.py`: its gates (1,589 LTSB features raw — the SHIPPED file is 1,590, −16 LTSB Trempealeau +17 from the county's own service — 72 counties, 1..n numbering per county, ward reconciliation) are what catch a county whose plan changed or whose filing broke. A count change is expected news, not a failure — read it, then move the expected number | 2026-08-25 (July 2026 filing; 1,590 districts shipped) |
| Same run | Re-check **Trempealeau**, the one county whose geometry comes from its own service rather than LTSB's. If a future LTSB filing restores its district 15, drop the override and ship the statewide file whole — the builder will tell you, because the override's own guards fail if the county's layer stops publishing 17 districts numbered 1..17 | 2026-08-25 (LTSB still merges 15 into 17) |
| Spring elections (April) | **Court of Appeals judgeships** elect one per district per year at most (Wis. Stat. 752.03), staggered six-year terms — the weekly wicourts scrape carries turnover as a roster-PR diff. A FAILED run means a seat count moved off 4/4/3/5 (a vacancy — read it) or the district composition itself changed (752.11 — rebuild the geometry in the same change) | 2026-08-25 (layer shipped; 16 judges) |
| Spring elections (April, odd and even years) | **Circuit judgeships** elect every April on staggered six-year terms, and vacancies fill by appointment year-round — the weekly wicourts scrape carries both without ceremony (a new name is a diff on the roster PR). What deserves a read is a FAILED weekly run: the scrape asserts the statutory circuit composition (Wis. Stat. 753.06 — the three two-county circuits), so a failure can mean the circuit map itself moved, which needs `wi/scripts/build_wi_circuit_courts.py` re-run in the same change | 2026-08-25 (layer shipped; 261 judges, 234 with direct phones) |
| USGS republication (roughly annual, unannounced) | The **police-station / fire-station / post-office** layers all ride the USGS National Map structures service live, which is republished wholesale without a schedule. Nothing to rebuild — the monthly source report's envelope returnCountOnly rows are where a count change (or the service going dark) surfaces. The known data caveat travels with the source: ghost records happen (a fire department defunct since 2020 is the verified example), which is why the cards present proximity and never a service claim | 2026-08-25 (July 2026 republication; 807 police / 1,743 fire / 1,244 post offices in the envelope) |
| Same windows | The **ward layer** rides the same filings LIVE — no rebuild to run, because both its point query and its paged overlay hit LTSB's Current service directly. What to do instead: read the count off the monthly source report (the returnCountOnly ENDPOINTS row) and treat a change as expected news (Jan 2026 filed 7,138, July 2026 filed 7,161 — the same total as July 2025, a verified coincidence); it is the layer going unreachable or answering zero that is a failure. The supervisory builder's ward-reconciliation gate independently re-witnesses the ward↔district pairing on its own re-run | 2026-08-25 (layer shipped against the July 2026 filing) |

---

## Per-election — the seats above the boundaries

| When | What | Last done |
|---|---|---|
| After each Wisconsin general (November, even years) and any special election | The chamber rosters turn over; the weekly Open States refresh picks it up, but verify the first post-election PR against the Legislature's own directory before merging | 2026-08-25 (initial build: 33/33 + 99/99) |
| After each **spring election (April, even years)** | County supervisors are elected to two-year terms then, so the 20 shipped rosters turn over at once. The weekly run picks it up, but verify the first post-seating PR against a couple of counties' own pages before merging — this is also when counties reorganise their board pages, which is what breaks the pinned reading direction | 2026-08-25 (20 counties, 437 seats: 435 named, 2 vacant; 72/72 county links verified) |

---

## Per-decade — the census redistricting cycle

| When | What | Last done |
|---|---|---|
| After each decennial census (next: 2031–2032) | Congressional + legislative districts redraw: re-run `wi/scripts/build_legislative_boundaries.py` (all three targets), confirm the district counts against the apportioned delegation and the 33/99 chambers, and re-verify the smoke anchors against the rebuilt geometry | 2026-08-25 (chambers built at 100.00% agreement) |
| Mid-decade — Wisconsin specifically | Wisconsin's legislative maps have moved OFF-cycle before (the 2024 remap after Clarke v. WEC). A chamber-map change outside the census cycle is plausible here in a way it isn't in most states: any news of a court-ordered remap means re-running the chamber builds and anchors without waiting for the decade | _(watching)_ |
| Same cycle | County subdivisions / places / school districts shift in TIGERweb continuously; the live layers pick changes up on their own, but the PRE-BUILT files (`state-counties.json`, `school-districts-unified.json`) need a rebuild | _(never)_ |

---

## Grow this file

Every new layer ships with a row here naming when its source moves (school-year datasets
rotate every summer; county precinct files change per election; rosters change per election
and per resignation). A source with no row is a source nobody is watching.

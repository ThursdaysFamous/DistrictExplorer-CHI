# WATCH.md — redistricting watch calendar (San Francisco)

The one place the dates live. `docs/REDISTRICTING_RUNBOOK.md` (master in the Chicago repo;
pointer stub here) is *what to do* when a boundary changes; this file is *when to look*.
Keep it at repo root so it's the first thing seen. Update the "Last done" column each time
you complete a row — a checkpoint with a stale date is a checkpoint that didn't happen.

Rule of thumb: **detection runs itself monthly; you run the SFUSD drill yearly; you open
the runbook per-layer whenever a map is enacted.** Everything below is just those three
habits pinned to dates so a trigger never catches you cold.

---

## Standing (already automated — verify, don't perform)

| Cadence | What | Where | You do |
|---|---|---|---|
| Monthly (1st, 14:00 UTC) | Source-freshness + redistricting-watch scan | `.github/workflows/validate-sources.yml` → single tracking issue on WARN/FAIL | Glance at the issue when it updates. A WARN = a trigger below may have fired. |

---

## Yearly — the SFUSD drill (the load-bearing habit)

| When | What | Runbook steps | Last done |
|---|---|---|---|
| Late summer, when SFUSD's new school-year attendance-area dataset posts | The attendance areas are republished each school year under a **brand-new dataset id** (in use: `e6tr-sxwg`, "…(2024-2025)"); `validate_sources.py`'s year-search WARNs when a newer edition appears. Execute the response procedure against the rotated dataset as a live rehearsal. | Steps 2–6, 10–11 | _(never — first cycle is summer 2026)_ |

This is the only time the machinery gets exercised before it matters. If the drill is
painful, fix the runbook **that year**, not during the 2031 census scramble.

---

## Per-election — voting center & drop-box refresh

| When | What | Last done |
|---|---|---|
| ~1 month before each election, when sf.gov posts the election's drop-box / voting-center locations | Refresh `data/app/early-voting-sites.json` (hand-transcribe the official list from sf.gov/return-your-ballot + the Voter Information Pamphlet, geocode, verify pins against the Department's own locations map), update the election name in the `early-voting` layer's `intro` in `index.html`, update the `source_url` in `scripts/validate_sources.py` PROVENANCE if the page moved, and bump `sw.cache_name` in `metro-worksheet.json` + regenerate | 2026-07 (initial — June 2026 primary list; the Department describes the 37 drop boxes in recurring terms) |

The layer's honesty depends on this row: the card **intro** names the election the shipped
list was published for, so a stale file is visibly stale rather than silently wrong — but
refresh it anyway (each feature also carries an `election` property for provenance; it is
not rendered). The transcription is manual (no open point dataset exists on DataSF —
re-check the catalog each cycle in case that changes).

---

## Fixed checkpoints (put these on a real calendar)

| Date | Trigger | Action | Done |
|---|---|---|---|
| **2029 Q4** | Pre-cycle dry read | Re-read the redistricting runbook against current code; confirm the per-layer inventory still matches reality. Catches drift while it's calm. | ☐ |
| **2031 Q2** | P.L. 94-171 redistricting data delivered to states (statutory deadline ~Apr 1 2031; the 2020 cycle slipped — don't assume) | Begin active watch on congressional + state-legislative layers. | ☐ |
| **2031–2032** | CA Citizens Redistricting Commission adopts new maps (congressional / senate / assembly), effective 2032 elections | Per-layer response for `congress` / `ca-senate` / `ca-assembly` — all three are **pre-built SF-clipped geometry** (`build_legislative_boundaries.py` from TIGERweb), so the work is a rebuild + anchor re-verify, staged on enactment, shipped at effectiveness. | ☐ |
| **2032** | SF Redistricting Task Force redraws Supervisor districts (charter: within ~9 months of census data; last map April 2022) | `supervisor-district` is an **offline anchor + roster layer**: rebuild `supervisor-districts.json` from the successor DataSF dataset, re-verify the City Hall / Ferry Building ground-truth anchors, confirm the roster builder still joins. The **election-precinct map redraws on the same cycle** — expect a successor to `jg6x-23ig` with a new "Defined <year>" title (`validate_sources`' year-search watches for it). | ☐ |
| **Nov 2026, then every even-year November** | BART Director elections (staggered 4-year terms; SF districts on the ballot: **7 & 8 in 2026**, 9 in 2028) | Re-verify `data/app/bart-directors.json` against bart.gov/about/bod (names, board roles, member URLs); bump `sw.cache_name` + regenerate. | ☐ |
| **2031–2032** | BART redistricting (the 2022 Plan E2 map holds "until the next round following the 2030 US Census") | Rebuild/re-verify the `bart-director` geometry against BART's updated ArcGIS service; re-confirm which districts cover SF. | ☐ |
| Rolling, post-enactment | Census TIGERweb publishes the new CD vintage | The monthly scan's watch should flag it; update the TIGERweb layer index + rebuild per the runbook. | ☐ |
| Per-body, ad hoc | A commission convenes to redraw any mapped body | Open that layer's watch window; expect an enactment within the session. | ☐ |

---

## Off-cycle triggers (no date — stay alert)

Redistricting is **not** only decennial. Any of these fires the per-layer response
procedure immediately:

- **Court order** — very common 2022–2024 (NY, AL, LA, GA congressional maps).
- **Mid-decade partisan redraw** — the 2025–2026 wave is the live example, and it includes
  **California (Prop 50)**: if the CA congressional map changes mid-decade, `congress`
  rebuilds here on the same staged-enactment rule.
- **Administrative safety reorg** — SFPD redraws district boundaries administratively
  (last major realignment 2015). `police-district` is a **pre-built offline anchor**
  (`d4vc-q76h`): rebuild the file, re-verify the Tenderloin/NORTHERN anchor expectations.
- **Annual school-zone rotation** — the SFUSD drill above is the scheduled instance.

When one fires: confirm enactment + effective date, then work **one layer at a time**
through the runbook. Don't touch layers that didn't change.

---

## Per-metro note

**This file is SF's.** Each sibling fork carries its own `WATCH.md` with its own bodies
and enactment history (Chicago: wards/ERSB/CPS + collar counties; NYC: Districting
Commission, BOE election districts, NYPD precinct reorgs). The decennial and off-cycle
framing is shared; the layer rows are per-city.

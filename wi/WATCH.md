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

---

## Per-election — the seats above the boundaries

| When | What | Last done |
|---|---|---|
| After each Wisconsin general (November, even years) and any special election | The chamber rosters turn over; the weekly Open States refresh picks it up, but verify the first post-election PR against the Legislature's own directory before merging | 2026-08-25 (initial build: 33/33 + 99/99) |

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

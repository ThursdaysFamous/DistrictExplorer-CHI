# WATCH.md — redistricting watch calendar

The one place the dates live: *when to look* for boundary and roster changes in this fork's
sources. The reference repo's `docs/REDISTRICTING_RUNBOOK.md` is *what to do* when a boundary
changes. Keep this file at repo root and update the "Last done" column each time you complete
a row — a checkpoint with a stale date is a checkpoint that didn't happen.

This is the template's SCAFFOLD: it starts with the rows the five starter layers need, and
every layer this fork adds should bring its own row in the same change.

---

## Standing (automated — verify, don't perform)

| Cadence | What | Where | You do |
|---|---|---|---|
| Weekly (Mon 13:00 UTC) | U.S. House roster refresh | `.github/workflows/update-congress-roster.yml` → PR on change | Review + merge the PR; a week with a surprise diff is worth a look at the source |

---

## Per-decade — the census redistricting cycle

| When | What | Last done |
|---|---|---|
| After each decennial census (next: 2031–2032) | Congressional districts redraw: re-run `scripts/bootstrap_state.py --refresh-boundaries` (or re-derive `data/app/congress-districts.json` from TIGERweb), confirm the new district count against the apportioned delegation, and re-verify the smoke anchors | _(never)_ |
| Same cycle | County subdivisions / places / school districts shift in TIGERweb continuously; the live layers pick changes up on their own, but the PRE-BUILT files (`state-counties.json`, `school-districts-unified.json`) need a rebuild | _(never)_ |

---

## Grow this file

Every new layer ships with a row here naming when its source moves (school-year datasets
rotate every summer; county precinct files change per election; rosters change per election
and per resignation). A source with no row is a source nobody is watching.

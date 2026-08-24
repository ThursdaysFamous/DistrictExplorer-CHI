# Redistricting Runbook — pointer

The **master lives in the Chicago repo** (owner: CHI; applies fleet-wide), at
[`DistrictExplorer-CHI/docs/REDISTRICTING_RUNBOOK.md`](https://github.com/ThursdaysFamous/DistrictExplorer-CHI/blob/main/docs/REDISTRICTING_RUNBOOK.md).

This fork deliberately carries no copy — a per-metro copy of a fleet-wide
runbook is exactly the stale-duplicate failure mode the pointer stubs exist to
kill. NYC does not write a runbook of its own; it supplies its per-layer facts
through two mechanisms the master defines:

- **Detection layer (live here):** `scripts/validate_sources.py` carries the
  NYC source manifest with per-source `vintage` / `expected_successor` fields
  and the TIGERweb congressional layer-name watch (CD119 → CD121), run monthly
  by `.github/workflows/validate-sources.yml`.
- **Response facts:** `metro-worksheet.json` (the live per-fork source of
  truth; the historical conformance record is archived at
  `docs/archive/NYC_CONFORMANCE.md`) feeds the master's per-metro appendix
  tables.
- **When to look:** the dates live in this repo's root `WATCH.md` — the
  per-metro redistricting watch calendar.

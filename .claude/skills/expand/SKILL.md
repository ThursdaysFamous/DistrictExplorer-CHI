---
name: expand
description: The shared plumbing every districtry expansion rides — which file owns each fact (worksheet vs engine/ vs data/app), the roster triad's contract, the fetch-engine ladder, which route to try first for each datum, and what a change still owes after it merges. Use it at the START of any change that grows an instance when no narrower skill fits, and for the cross-cutting questions: "where does the Iowa auditor builder go", "add a layers[] row and regenerate everything that reads the worksheet", "do I need --sync-fleet before regenerating", "the card helper needs an emptyNote, where does that edit go", "which route first for Kenosha's board roster", "Pierce is behind Akamai — Playwright day one or the Archive rung", "what do I still owe after shipping the precinct layer". It routes to county-n-plus-1, new-state-instance, new-layer, roster-pipeline, municipal-officials and boundary-change, and points at docs/EXPANSION_GUIDE.md Part 6 rather than restating it. Not for a red PR (steward) or a data question.
---

# The spine every expansion rides

`CLAUDE.md` carries the worksheet mechanism, the engine fences, the layer
contract, the scraper → builder → bot-PR pattern and every gate's story, and is
loaded on every turn. `docs/EXPANSION_GUIDE.md` §0 and Part 6 are the doctrine.
This carries the part an agent gets wrong at the START of an expansion task —
where each kind of edit actually goes, and what a change owes after it merges
— once, so the path skills can point here instead of each restating it.

## 1. Route the task (§0.3)

- A new state → **new-state-instance**.
- One more county, city tier or roster inside an instance → **county-n-plus-1**; its roster mechanics → **roster-pipeline**; an Illinois county's villages → **municipal-officials**.
- A new concept or toggle → **new-layer**, gated by §1.6.
- A boundary that moved → **boundary-change**.
- An e-mail to a public office → **outbound-ask**.
- A PR to drive to green → **steward**.

The expansion invariant (§0.4): a county adds dispatch entries and roster
rows, never a layer; an at-large body adds roster rows ONLY — no dispatch
entry, no coverage function, no toggle.

A CITY tier inside a state instance (§3.0) is that instance's depth, and no
narrower skill owns it: one coverage gate per city, dissolved from the city's
own ward fabric and never a bbox; a concept that appears in a second city
becomes a dispatched concept exactly as a county concept does; the city's
publisher outranks the state's for what the city administers, with the state's
answer kept as the fallback so a failed city file degrades instead of
dead-ending; two surfaces always, the live service and the open-data extract,
with a build-time witness comparing them. §3.1 holds the dispatcher's
semantics — coverage is the OR of the entries, the query dispatches by
containment, a downed county's error propagates rather than reading as "no
result" — and the rule that every retired per-county id is appended to the
instance's alias shim, so shipped permalinks keep working.

## 2. Find the instance's files before writing anything (§0.1)

`<tag>/metro-worksheet.json`, `<tag>/scripts/` (builders, scrapers, the
instance's own `validate_index.py`, `smoke_test.mjs`, `validate_sources.py`),
`<tag>/data/app/` (runtime files), `<tag>/data/source/` (build inputs, excluded
from the deploy), `<tag>/WATCH.md`, `<tag>/CLAUDE.md`. The exception is
Illinois, which runs from the ROOT: the root `metro-worksheet.json` is
Chicago's, root `scripts/` holds fleet tooling AND some 260 Illinois builders,
and there is no `il/scripts/`. A new state follows Wisconsin's shape. Never
`sys.path` into another instance's scripts — `scripts/validate_workflow_deps.py`
walks each workflow-run script's module-scope imports inside ITS tree against
that workflow's `pip install` line; a shared helper moves to root `scripts/`.

## 3. Any per-instance fact → the worksheet → regenerate

```bash
python3 scripts/generate_metro_files.py                  # every instance
python3 scripts/generate_metro_files.py --instance wi    # one
python3 scripts/generate_metro_files.py --sync-fleet     # first, whenever metros.json changed
python3 scripts/generate_metro_files.py --check          # the CI gate
```

The generated regions are in `index.html`, `sw.js`, `sources.html`,
`validate_index.py`, `smoke_test.mjs`, `CLAUDE.md` and `README.md`. A layer is
a `layers[]` row with a `source` block — the generator refuses without one
whenever the worksheet sets `sources_page`, which also requires
`verified_date`; the schema (`schema/metro-worksheet.schema.json`) itself
requires only id, label, group and area rank. Set both keys and give every
layer a `source`.

## 4. An engine change → the block under `engine/` → recompose

```bash
python3 scripts/compose_app.py                  # splice engine/ into every instance
python3 scripts/compose_app.py --instance ia    # one
python3 scripts/compose_app.py --check          # the CI gate
```

It is a FLEET change and must be right for every instance. The
instance-neutral way to add behaviour is an optional field a layer opts into —
`emptyNote`, `coverage`, `subOf`, `pointOfInterest`'s coordinates — so a layer
declaring nothing is unchanged. Never edit inside an `ENGINE:BEGIN/END` fence in
an instance file; never inline an instance value in a fence (add a
`METRO:BEGIN config` variable). Do not reach for `--extract-from` — it
repopulates `engine/` FROM one instance and is the adoption door, not the edit
path. `docs/ENGINE_SYNC.md`'s banner describes the RETIRED release channel as
current; use it only for its block inventory and the tombstone convention for
retiring helpers. `ny/CLAUDE.md` and `ca/CLAUDE.md` predate the consolidation
and still describe a lockfile, an apply script and an engine-bump workflow —
none exists; `compose_app.py` is the mechanism in those folders too.

## 5. A new roster → the triad (§6.3; roster-pipeline has the mechanics)

Scraper: raw intermediate JSON, one record per member with its source URL and
a scrape timestamp; unfindable fields null; a per-member failure becomes an
error record — never dropped, never invented. Builder: writes `<tag>/data/app`,
refuses below its floor (a deliberate under-tolerance so a vacancy does not
wedge the weekly run; a placeholder roster gets floor 0, raised after the
first real scrape), stable key order. Workflow: a fixed `bot/*` branch,
force-pushed, opening a PR — never a commit to `main`. Shared machinery lives
in `scripts/scraper_common.py` (fail voices, UA definitions, retry) and
`scripts/aia_bundle.py` (the pinned intermediates); a new scraper reuses them
rather than hand-rolling a retry loop or its own certificate pin. A retired
script gets a "Supersedes …" line in its successor's docstring AND is deleted —
`docs/OPTIMIZATION_PLAYBOOK.md` §8 records the one a merge resurrected.

## 6. Choose the fetch engine by the ladder, and record the rung per target

Plain requests (`scripts/ilga_scraper.py` is the template) → `--engine auto`,
requests then Playwright (`scripts/cpd_district_scraper.py`) → Playwright from
day one for a known bot block → the Internet Archive Save-Page-Now rung for a
total block (`scripts/kendall_county_board_scraper.py`, with its
`WAYBACK_MAX_AGE_DAYS` guard and standing-issue conversion) → REJECTED, with
the alternative documented. A captcha or a 202 is an access control, not an
obstacle. If the official site is unscrapeable, a maintained open aggregator
(Open States, `congress-legislators`) may supply STRUCTURED fields while the
official site stays the card's link. Keyed enrichments ship dark — a missing
secret degrades to the unenriched roster; app tokens are public, real API keys
are repo secrets and never in `index.html`.

## 7. For each datum, work §6.4's route column top-down — by path, never copied

Statewide boundary → TIGERweb live, then pre-built
(`scripts/build_legislative_boundaries.py`); county or city boundary → a GIS
dispatch entry → pre-built from an enacted shapefile → a tax-agency tiling,
every id in the instance's `validate_sources.py`; officeholders → boundary-GIS
attributes verified against the directory → a directory scrape → an
aggregator's structured fields → a hand-verified transcription with a watcher
→ the link-only floor; municipal bodies → §3.4's five rungs; contact → the
roster's OWN source, never backfilled from a weaker one; amenity points → USGS,
then portal points. Take the first route that honestly works, record the
outcome, and never invent what no route provides. VERIFIED means you fetched
it and saw records (§2.6.1).

## 8. Freshness fires on a successor, never on age

A year-versioned Socrata id gets a manifest row in the instance's
`validate_sources.py`; the check fires on a newer edition in the catalogue or
a 404 — age alone cries wolf. The ArcGIS analogue: record layer URL and item
id, treat an HTTP-200 JSON error body as unreachable, search the owning org's
catalogue for a successor item. Both surface as tracking issues, never as
edits.

## 9. Gates: the steward battery, not §6.5's table

`.github/workflows/smoke-test.yml` is the source of truth and the steward
skill carries it in CI's order with the real invocations; §6.5's table already
omits eight gates CI runs. Two worth naming for a fleet change:
`python3 scripts/build_landing_page.py --check` (the front door must list the
instance) and `python3 scripts/validate_workflow_deps.py`.

## 10. What a change still owes after it merges (§6.6)

- The weekly workflow(s) it added, on staggered cron slots — the live schedule is the instance `CLAUDE.md`'s generated metro-facts block.
- A `validate_sources.py` manifest row per dataset endpoint (not per roster — the link gate extracts those).
- A `<tag>/WATCH.md` row for anything with a date, a filing window or a per-election refresh, with its last-run value: the calendar is the only thing that fires for data no gate can check.
- `docs/DATA_LAYER_GUIDEBOOK.md` rows — coverage map, inventory, matrix, gap records naming their counties.
- A blast-radius row in `docs/REDISTRICTING_RUNBOOK.md` for every new boundary layer. That runbook has NO Iowa section and undercounts Illinois; the obligation is standing and already unmet — check it, never assume it is current.

## 11. Working style (§0.5)

Locate code by grep anchor, never by line number. Work one module at a time.
Record every surprise in the same change — an unrecorded one is paid for
again. Keep measurement separate from conclusion: "this host refuses this
client" is what was measured; "this agency publishes nothing" is a claim the
measurement does not support.

## 12. Nevers

- Never hand-edit a GENERATED region or an ENGINE fence in an instance file.
- Never put an instance's builder in another instance's tree, or reach across with `sys.path`.
- Never drop a member whose fields failed; never invent one.
- Never backfill a contact from a weaker source.
- Never fire freshness on age.
- Never ship a boundary layer without its runbook row and its WATCH row.

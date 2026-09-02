---
name: new-layer
description: Add a NEW layer, toggle or concept to an instance — starting with the test that decides whether it is a layer at all (most proposals are a dispatch entry or a card row), then the factory, the card, the sidebar position, nesting, and the same-change bookkeeping split by what the worksheet GENERATES and what is hand-edited. Use it for "add an appellate-district layer to il", "wi: new layer for technical college districts", "is ROE a layer or a county-card row?", "where does community-college sit in the sidebar", "nest mpd-squad-area under mpd-district", "validate_index says LAYER_SIDEBAR_RANK is missing an id", "add the guidebook matrix row for ia-judicial-district", "should mwrd become a sanitary-district concept now that a second county publishes one". Not for a county's dispatch entry into a shipped concept (county-n-plus-1), a new state (new-state-instance), restyling an existing layer, or a red PR (steward).
---

# A new layer

`CLAUDE.md` carries the layer contract, the factories by name, the card order,
the honesty rules and the worksheet mechanism, and is loaded every turn. This
carries what an agent gets wrong at the moment it is asked for "a new layer":
it skips the gate (most proposals are not layers), forgets the one rank list
the worksheet does not generate, and never writes the guidebook rows that only
the weekly fleet-status run notices, a week later.

## 1. Run the gate before writing code — §1.6, five questions

1. **Level and function** (§1.1). If it duplicates a concept that exists at that level, it is a dispatch entry (county-n-plus-1) or a card row. Stop; no layer.
2. **Election geometry** (§1.2) decides the surface. DISTRICTED → a polygon concept layer. AT-LARGE → roster rows on the unit's identity card, never a polygon. APPOINTED → labelled rows or links only. PARTY OFFICE (committeeperson and the like) → out of scope by standing decision.
3. **Dispatch dimension** (§1.3): by county (`registerCountyLayer`), by municipality (a place-GEOID join or entries keyed by municipality), by election authority (coverage carved out of the county, the `suburbanCookCoverage` shape), or none (one statewide source).
4. **The officeholder story**, decided AND built in the same change (§3.3, rule 4). The honesty floor is a link plus a recorded gap.
5. **The record**: a guidebook row, and an Appendix A row for the reference instance only.

A dedicated single-county layer (`tif-district`, `mwrd`) converts to a
dispatched concept when its SECOND county ships; never create a second
dedicated layer for the same class (§1.5, §3.2).

## 2. Check the record before researching

`docs/DATA_LAYER_GUIDEBOOK.md` — the concept coverage matrix, its Pattern
legend (which factory each shipped sibling used), the parity debts and the
backlog. A sibling that SHIPS the concept: reuse its pattern and source
notes. A sibling that recorded NO HONEST ANALOG: check whether the rationale
applies here before re-researching. A cell already marked not shipped carries
a measured route; start from it.

## 3. Launch consolidated, through a factory

A genuinely new concept launches with a `registerCountyLayer` dispatch table
from day one if it is multi-source, entries via `polygonCountyEntry`, and
through a factory where one fits — `registerPolygonLayer`,
`registerSchoolZone`, `registerCpsNetwork`, `registerIlgaChamber`,
`registerNearestPointLayer`. Non-factory patterns worth copying: two live
datasets joined (`ward`), one loader feeding N layers
(`ccpsa-district-council`), a bespoke nearest-N (`school-site`). The two
school factories build loaders through the Socrata-only `makeCachedLoader`;
on another portal convert to an injected loader as `registerPolygonLayer`
accepts. Declare an honest `coverage(point)`. A bespoke block declares
`hoverName` from the SAME properties the card reads, and
`hoverOfficial{load?, name()}` when the card joins a roster — prefetched on
toggle-on, so hover never fires a network request; an appointed official's
hover name carries its role.

## 4. The card

The content order maps onto `docs/CARD_RENDER_API.md`'s helpers: identifier
pill (`cardIdentifier`) → person rows (badges, notes, committee expanders) →
office group → contact line → footer link (`primaryLink`); a name-only layer
sets `compact`. Helpers are data-only by contract: never pass HTML; e-mail
renders as `mailto:` and is never printed; phone rows get a `tel:` href the
helper builds; absent fields render nothing. Deviate only where the concept
demands it. If the source carries identity, location or contact the card does
not yet show, record the gap in the guidebook backlog rather than shipping
silently.

## 5. Bookkeeping in the same change — generated vs hand-edited

**Generated from the worksheet.** Add a `layers[]` entry to the instance's
`metro-worksheet.json` (the root one for Illinois): `id`, `group`, `label`,
`area_rank`, `rank_note`, and `source` (`answers`, `boundary`, `people`,
`applies`) — `source` is REQUIRED or the generator refuses. Bump
`min_register_layer` if the layer uses a bare `registerLayer(` call; add to
`hover_name_keys` / `hover_number_keys` only if the generic hover path needs a
new property; add the file to `data_files.geometry` or `data_files.rosters`
if a `<tag>/data/app` file ships. Then one run:

```bash
python3 scripts/generate_metro_files.py
```

emits `LAYER_AREA_RANK`, `EXPECT_LAYER_IDS` and `MIN_REGISTER_LAYER`, the
`sw.js` URL lists, the smoke test's `EXPECT_LAYERS`, the `sources.html` matrix
row and the instance `CLAUDE.md` layer count.

**Hand-edited, because nothing generates them.**
- `LAYER_SIDEBAR_RANK` in the instance's `index.html` — a `TEMPLATE:BEGIN sidebar-rank` region; grep for it.
- A dark twin for any new outline colour: `python3 scripts/build_dark_map_palette.py`.
- A row in the instance's `validate_sources.py` manifest.
- The guidebook: the `GUIDEBOOK:BEGIN coverage-map` JSON (the weekly `scripts/fleet_status.py` diffs it against the worksheet), the matrix row, and any drop WITH its rationale — silence is the only wrong answer.
- An Appendix A row for Illinois only; the appendix is the reference's classification and lacks every layer since its date.
- A blast-radius row in `docs/REDISTRICTING_RUNBOOK.md` for any new boundary layer, and a `WATCH.md` row for anything date-bound (§6.6).

## 6. Sidebar position

Position is the explicit rank list, never registration order. Within a group:
identity hierarchy → representation → service and taxing overlays → amenity
points, broad to specific within each family; a `subOf` layer is listed
immediately after its parent so the validator's 1:1 check holds; toggled-on
layers float to the top regardless, so the rank governs the RESTING order.
The Political group is the exception — DEMAND-ordered, most-searched first,
by an operator decision recorded in Part 4 with its evidence; re-rank only
from real Search Console or GoatCounter data, never by feel. The instance's
validator (`scripts/validate_index.py` for Illinois) asserts `LAYER_SIDEBAR_RANK`
matches the registered id set 1:1 in `il/`, `wi/` and `ia/`; in `ny/` and `ca/` it does not, and an unranked
id sinks silently to the end.

## 7. Nesting

Set `subOf` only for genuine legal containment PLUS numbering — County →
Township → Precinct or Municipal Ward; Ward → Ward Precinct; Police District →
Beat — never mere geometric overlap. Cross-group nesting is impossible by
design. Never gate an elected body behind a service toggle. A municipality
cannot nest under a county: a TIGER Place is one record however many
counties it spans. Special districts are independent taxing bodies and do not
nest under county either. Part 4 holds the evaluated-and-rejected list; read
it before proposing a nest that is on it.

## 8. Gates

`python3 scripts/generate_metro_files.py --check`; the instance's
`validate_index.py` (the `registerLayer(` floor, both rank lists, the
exactly-one-list rule for `<tag>/data/app`, a `sources.html` row per layer); its
`smoke_test.mjs` (exact layer count, coverage-hide, permalink stability, the
alias shim if an id was renamed); `python3 scripts/build_dark_map_palette.py --check`
if a colour was added; `python3 scripts/compose_app.py --check` if a fence was
touched; `python3 scripts/build_coverage_gaps.py --check` (with `--metro` and
`--out` for a non-Illinois instance) if a gap was written. The steward skill
carries the whole battery.

## 9. Nevers

- Never register a polygon for a body that elects at large, or a layer for an appointed or party office.
- Never a second dedicated layer for a class that has one; convert at the second county.
- Never rank by registration order; never re-rank Political by feel.
- Never rename a layer id — ids live in shipped permalinks; change the label and add an alias.
- Never pass HTML to a card helper; never print an e-mail address.
- Never ship a layer with no guidebook row, and never a drop without its reason.

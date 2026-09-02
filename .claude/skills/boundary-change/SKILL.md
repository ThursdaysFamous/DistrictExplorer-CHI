---
name: boundary-change
description: Respond to a boundary change in any instance — a redistricting, a court-ordered remap, a TIGERweb vintage roll, a Socrata dataset-id rotation, an LTSB filing, an administrative district reorg — by classifying how the layer ships, rebuilding it through the 2,000-point gate, bumping the service-worker cache the RIGHT way, re-anchoring the smoke test, auditing roster join keys, and landing it without stale maps. Use it for "CPS posted the SY2627 boundaries, run the drill", "TIGERweb rolled to CD120, the congress layer is stale", "LTSB republished after the July filing", "Council passed the new ward map, effective 2027 — what breaks", "rebuild the legislative boundaries", "Kane redrew its subcircuits", "P.L. 94-171 data landed". It carries the drill's corrected mechanics — docs/REDISTRICTING_RUNBOOK.md still says to bump sw.js by hand, and that is a GENERATED region — and points at the runbook's tables, never copies them. Not for adding a county (county-n-plus-1), a new layer (new-layer), or a red PR (steward).
---

# When a boundary moves

`docs/REDISTRICTING_RUNBOOK.md` holds the decennial timeline, the off-cycle
triggers, the per-instance blast-radius inventories and the appendix of
authorities — read them there. Three of its MECHANICS are wrong today, in the
direction an agent following it would fail a gate: it says to bump `CACHE_NAME`
in `sw.js` (a GENERATED region — the bump is a worksheet key), it says one of
three anchors is registered in the embedded-boundaries builder (all three are,
plus five judicial layers), and it promises a detection layer that was never
built. It also has no Iowa section, though `ia/WATCH.md` cites it. This carries
the drill with those corrected. `CLAUDE.md` carries the cache-first /
network-first split, the freshness gate and the worksheet mechanism.

## 0. Open the instance's calendar first

The row for the source that moved — root `WATCH.md` for Illinois, `wi/WATCH.md`,
`ia/WATCH.md`, `ca/WATCH.md`, `ny/WATCH.md` — names the builder to re-run and
its gates, and has a "Last done" column to stamp at the end. A checkpoint with
a stale date is a checkpoint that didn't happen.

## 1. Enactment and effective date, separately, citing the instrument

Ordinance, public act, court order, statutory filing. The policy is
show-current-until-effective: do the geometry work on enactment, but the app
keeps showing current districts until the effective date — a not-yet-effective
map on the card is a correctness bug. Dual-map display is out of scope
without an explicit instruction. Do nothing to geometry until both dates are
recorded.

## 2. Classify how the layer SHIPS — the drill differs

- **Live-fetched** (statewide TIGERweb county, township, municipality and school layers; the fetched wards and subdivisions): nothing to rebuild — a vintage roll reaches the app on its own.
- **Pre-built from a service by a builder**: Illinois legislative via `scripts/build_legislative_boundaries.py` (the `LAYERS` dict: layer index, `fields`, `out`, `simplify`, `min_features`); Wisconsin via `wi/scripts/build_legislative_boundaries.py`, `wi/scripts/build_wi_supervisory_districts.py`, `wi/scripts/build_wi_aldermanic_districts.py`, `wi/scripts/build_wi_court_of_appeals.py`, `wi/scripts/build_wi_circuit_courts.py`; Iowa via `ia/scripts/build_legislative_boundaries.py`; and every `scripts/build_<county>_boundaries.py`. The builder IS the intake.
- **Shapefile-derived**: the original into `il/data/source/raw/` under a name encoding layer, vintage and enactment citation; full-precision GeoJSON beside it; then its `LAYERS` entry in `scripts/build_embedded_boundaries.py`.

## 3. Acquire in this order, and never trace

The enacting body's own shapefile or service → the portal's new dataset id →
the TIGER/Line vintage. Never scrape or trace a rendered map; the county
builders enforce the same. Check the enacting body's ArcGIS org and the
`arcgis.com/sharing/rest/search` catalogue before any map method.

## 4. Rebuild and let the gate decide

Every boundary builder validates 2,000 seeded random points against the
pre-simplification source and refuses to write below 99.5% agreement or on ANY
point landing in two districts. `min_features` is a count guard: on a remap
that changes seat count, re-read the number from the apportioned delegation
and update it with a comment — never raise it to get past a failure. The
Wisconsin supervisory builder's feature guard is meant to fail on a filing and
be re-read, not raised reflexively.

## 5. The two rolls that recur

**TIGERweb Congress.** The numbered field is Congress-numbered (CD119 today)
and rolls with each seating. Update `fields` in the builder's `LAYERS`; the
app's district-number extractor has a name-regex fallback, but the builder's
requested fields must match or the fetch trims the field away. Update the
`note` on the TIGERweb `PROVENANCE` entries in `scripts/validate_sources.py`.

**Socrata year.** The CPS annual rotation: swap the `datasetId` literals in
`il/index.html` AND the matching ids in the `SOCRATA` list of
`scripts/validate_sources.py` — the manifest-vs-index drift guard fails
otherwise. This is the ONLY boundary roll the monthly issue detects on its
own (its newer-edition search); the runbook's per-source vintage watch was
never built, so do not expect the monthly issue to flag a Congress roll or a
shapefile redraw.

## 6. The worksheet, never the generated files

In `metro-worksheet.json` (or the instance's): `data_files.geometry[]`
`min_features` / `max_features` for each rebuilt file (the validator's floors
are emitted from them); **`sw.cache_name`** — the bump is the ONLY thing that
forces a returning visitor's cache-first geometry to refetch, and no gate
reminds you; `anchors[].expected`, `anchor_point`, `negative_point` if an
anchor layer moved (they emit the smoke test's `EXPECT_DISTRICT`, `POINT`,
`NEGATIVE_POINT`); `layers[].area_rank` if relative area ordering changed
(`LAYER_AREA_RANK` must stay 1..N with no gaps); `verified_date`. Then:

```bash
python3 scripts/generate_metro_files.py
python3 scripts/generate_metro_files.py --check
```

Every `<tag>/data/app` file must sit in exactly one of the service worker's two
lists; `validate_index.py` enforces it.

## 7. Two smoke fixtures are hand-kept

`MOVE_POINT` and `STRAGGLER_FILE` in `scripts/smoke_test.mjs` sit in a
`TEMPLATE` region, not a generated one. Re-classify the existing landmark
points against the NEW geometry, and ADD a regression sentinel — a point that
changed district across the remap — so the test proves the geometry is new
rather than stale.

## 8. Audit the roster join keys

Districts can be RENUMBERED, not only redrawn. Check that each scraper and
builder still joins officials to the right district ids. Where a county's
roster builder asserts the precinct composition against its boundary builder,
the weekly job going RED after a remap is the tripwire working: update the
compiled composition, never silence it. Official sources lag a remap, so
spot-check three known officials' districts against news sources before
merging the roster PR that follows.

## 9. Land it, and stamp what the runbook cannot generate

The steward battery, then a PR — officeholder changes stay human-reviewed. In
the same PR: stamp "Last done" in the `WATCH.md` row; update the layer's
blast-radius row and appendix row in `docs/REDISTRICTING_RUNBOOK.md` BY HAND —
the runbook says these become generated once Conversion 2 lands, Conversion 2
landed on 2026-07-13, and the tables were never converted, so a runbook whose
tables go stale on first use has failed its purpose. An instance with no
section (Iowa) gets a Wisconsin-style inventory block.

Permalinks need no migration — they encode lat/lng, not district ids, and
resolve to the new district after the update, which is correct. Work one
layer at a time; touch nothing that did not change.

## 10. Nevers

- Never show a not-yet-effective map; never touch geometry before both dates are recorded.
- Never trace a rendered map, and never take a portal id over the enacting body's own file.
- Never raise `min_features` or the agreement floor to get past a rebuild failure.
- Never bump `CACHE_NAME` in `sw.js`; bump `sw.cache_name` in the worksheet and regenerate.
- Never ship a remap without a regression sentinel in the smoke test.
- Never silence a composition tripwire that went red on a remap.
- Never leave the runbook's own rows stale in the PR that changed what they describe.

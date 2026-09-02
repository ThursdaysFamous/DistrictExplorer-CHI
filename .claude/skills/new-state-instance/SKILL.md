---
name: new-state-instance
description: Stand up a brand-new state instance `<tag>/` in this repo — worksheet first, engine composition, the national tier, anchors and the coverage wash, fleet registration, the localization sweep, go-live. Use it whenever a task names a state the fleet does not serve, from its very first PR — "stand up Minnesota as mn/", "Indiana PR 1, worksheet and national tier", "bring up mo/", "register Michigan in the fleet", "what does the coverage key need for a two-band state", "Ohio go-live PR", "pick the anchors for the mn smoke test". It carries the bring-up ORDER, the three decisions that come before the first layer, and the fleet registration steps that docs/EXPANSION_GUIDE.md Part 2 does not name and a real port missed; Part 2 holds the rules and this says when to open it. Not for deepening a state that already exists (county-n-plus-1), a new layer inside an instance (new-layer), or a red PR (steward).
---

# A new state

Five instances exist and two arrived after the consolidation; the next one
will follow the same twenty-odd steps, and the failure mode is recorded in the
guide's own words: of the registration list, "every item on that list was
missed by a real port." `CLAUDE.md` carries the instance model, the worksheet
mechanism, the engine fences and the layer contract, and is loaded every turn;
`docs/EXPANSION_GUIDE.md` Part 2 is the bring-up procedure. Neither is
restated here. What is here is the ORDER, the three decisions that precede
the first layer, and the registration steps Part 2 leaves out — found by
reading the scripts, not the guide.

## 1. Three decisions before the first layer

**Arrival shape** (§0.2). Statewide-first is the default for a state: three
national publishers — TIGERweb, the USGS National Map, the
`unitedstates/congress-legislators` roster — tile every state on day one, so
an instance has ~12 honest layers before anyone has been asked for anything.
That gives TWO coverage bands and a wash that never shrinks. Metro-first
(Illinois, NYC, SF) is the three-band shape. Statewide-first must not fake
depth: a county card that names nobody is honest; a polygon for a body that
elects at large is not.

**Platform** (§2.6). Identify the state's portal before wiring a layer.
Socrata: four-by-four ids, `/resource/{id}.json`; server-side point-in-polygon
is a research tool, never the runtime path. ArcGIS Hub/REST:
`…/FeatureServer/<n>/query`, always `outSR=4326`, page past `maxRecordCount`
while `exceededTransferLimit` with `loadArcGISPaged`. CKAN is a catalogue, not
a query engine: download once, ship static. A real API key that 401s without
it is a repo secret and never goes in `index.html`; a Socrata app token is a
public front-end constant.

**Geocoder** (§2.6). In order: a state-authoritative keyless geocoder WITH real
autocomplete replaces both reference geocoders; else Photon, state-bounded,
for type-ahead; Nominatim only as a debounced submit-time fallback, on the
serial ≥1 s POI queue its policy requires.

## 2. The instance takes Wisconsin's shape, never Illinois's

Illinois runs out of the repo root — its worksheet, scripts and smoke test sit
at `metro-worksheet.json`, `scripts/`, `scripts/smoke_test.mjs` — and that
asymmetry is history, not a pattern. A new instance is a folder:
`<tag>/index.html`, `sw.js`, `sources.html`, `faq.html`,
`metro-worksheet.json`, `<tag>/data/app/`, `<tag>/data/source/`, `<tag>/scripts/` (its own
`validate_index.py`, `smoke_test.mjs`, `validate_sources.py`, builders),
`WATCH.md`, `CLAUDE.md`. `wi/` and `ia/` are the live worked examples. Every
instance script resolves imports inside its own tree;
`scripts/validate_workflow_deps.py` fails a `sys.path` reach into another.

## 3. The worksheet, before any layer

The required keys are the schema's, not the guide's table:
`schema/metro-worksheet.schema.json`. The derivations that matter: `tag` is
the postal code (URL segment and folder); `STATE_FIPS` is the two-digit Census
FIPS that drives every TIGERweb query; `metro_center` and zoom frame the WHOLE
state; `permalink_gate` is looser than `metro_bbox`; domain, brand and
analytics are never the reference's and never absent. Read
`wi/metro-worksheet.json` beside the schema rather than the guide's example
column.

## 4. Register in the fleet on day one — including the lists Part 2 does not name

Fleet-level machinery should DISCOVER instances (`validate_card_links.py`
does), and every hand-kept list that does not is a registration step. Part 2
names five; two more break the build and are in no document:

- `INSTANCES` in `scripts/generate_metro_files.py` — app, scripts, docs and worksheet paths per instance; nothing generates for a tag that is not here.
- `AREAS` in `scripts/build_coverage_map.py` — tag → outline files; a tag missing here renders on the coverage map as a point, and `build_coverage_map.py` REQUIRES `scope` and `bbox` on the `metros.json` entry, which Part 2's field list omits.
- `metros.json` — the entry (`tag`, `landing_name`, `blurb`, `scope`, `url`, `bbox` and the rest, copied from a sibling), then `python3 scripts/generate_metro_files.py --sync-fleet`.
- `.github/workflows/smoke-test.yml` — the instance's `validate_index.py` line and its `smoke_test.mjs` line; an ungated folder merges through CI while nothing looks at it.
- `.github/workflows/deploy-pages.yml` — `EXCLUDES`: add `<tag>/data/source`, `<tag>/data/state`, `<tag>/scripts` and `<tag>/data/*.geojson` so build inputs never publish, and add the instance folder ITSELF — that line is the go-live switch (§7).
- `docs/DATA_LAYER_GUIDEBOOK.md` — coverage map, inventory, matrix, and each drop with its structural reason.
- Regenerate `python3 scripts/build_landing_page.py`, `python3 scripts/build_privacy_page.py`, `python3 scripts/build_coverage_map.py` — the privacy page is MEASURED from the shipped `index.html`, so it reflects the instance only once its analytics and geocoder posture are real.
- `sitemap.xml` — every page the instance serves; `scripts/page_consistency_test.mjs` derives its page list from it, so an unlisted page is never checked and never indexed.
- The reader-facing counts `python3 scripts/build_county_status.py --check` scans: README's fleet table (a row per `metros.json` entry, and its "<n> instances" prose) and `funding.json`. Iowa shipped while README said "four instances" and every gate stayed green; this one was written to stop that.
- Instance-side: PWA icons and `manifest.webmanifest` via `python3 scripts/build_manifests.py`; its own GoatCounter site and tag (`trackEvent` no-ops silently without one — a real port shipped days of zero analytics); any CI secrets its scrapers need.

## 5. Compose, generate, then the national tier

```bash
python3 scripts/compose_app.py               # splice engine/ into every instance
python3 scripts/generate_metro_files.py      # emit every GENERATED region from the worksheets
```

Then ship the national tier first: TIGERweb counties, county subdivisions,
places, the three school-district kinds, ZCTAs, and `Legislative/MapServer`
layers 0/1/2 with `STATE='<fips>'` (a unicameral legislature rides layer 1 —
register ONE chamber); USGS police, fire and post offices as nearest-N; the
congress roster from `legislators-current.json`, district offices joined by
bioguide id from `legislators-district-offices.json`.

Decide the rest of the roster from the guidebook's concept matrix: walk the
reference's layers, map each to the local equivalent, and DROP, NEVER FAKE,
recording each drop with its structural reason. Wisconsin's three drops are
the model (no park districts as a unit of government; appointed library
boards ship as points; an appointed technical-college board is identity-only
and says so).

## 6. Every layer is a worksheet row — and what that row generates

A `layers[]` entry carries `source` or the generator refuses. That ordered
list IS `LAYER_AREA_RANK` — largest to smallest, every registered id with no
exceptions, sub-layers ranked just before their parent — and one run of
`generate_metro_files.py` emits it along with `EXPECT_LAYER_IDS`,
`MIN_REGISTER_LAYER`, the `sw.js` URL lists, the smoke test's `EXPECT_LAYERS`
and the `sources.html` matrix row. `LAYER_SIDEBAR_RANK` is hand-edited in the
instance's `index.html` (the new-layer skill carries the placement rule).

Factories before bespoke blocks: `registerPolygonLayer`, `registerSchoolZone`,
`registerCpsNetwork`, `registerIlgaChamber` (boundary plus a same-origin
roster keyed by district — the congress and state-chamber pattern),
`registerNearestPointLayer`. The two school factories build loaders through
the Socrata-only `makeCachedLoader`; on any other portal convert them to an
injected loader the way `registerPolygonLayer` accepts one. A bespoke block
declares `hoverName` from the SAME properties its card reads, and
`hoverOfficial{load?, name()}` when the card joins a roster — prefetched on
toggle-on so hover never fires a request. Cards go through the helpers in
`docs/CARD_RENDER_API.md`, data-only, never HTML.

Land the cheapest REAL roster during the module work, not in a later
pipeline pass: real data flushes factory paths a placeholder never exercises.

## 7. Anchors, ground truth, and the wash

Pick at least three API-free anchor layers. The worksheet's `anchors[]` names
each layer and the district expected at `anchor_point`; `negative_point`
must miss EVERY anchor, chosen against a shoreline-clipped layer (mid-water
positives are legally correct on water-inclusive layers). Build the anchors
with `scripts/build_embedded_boundaries.py`, registered in its `LAYERS`
dict, and hold them to ≥99.5% agreement on 2,000 seeded points with zero
double-classification. Every `<tag>/data/app/` file appears in exactly one of the
worksheet's `data_files.geometry` / `data_files.rosters`; bump `sw.cache_name`
on any change to those lists.

Draw the wash from a purpose-built outline, never from an anchor and never
from stitched per-county files — the engine cancels interior borders only on
EXACT shared coordinates, and independently simplified county files leave
seams. One query, dissolved at build time, simplified hard, and the builder
refuses to write unless one anchor per county still falls inside and known
outside cities fall outside; `scripts/build_metro_outline.py` is the
reference.

Then decide the BANDS (§2.5.1): two by default; three only when full coverage
is a proper subset of a wider region whose layers still answer throughout. A
two-band key is not a degraded key. Add `coverage_key` to the worksheet —
`outside` required, `region{edge,label,sub}` only for three bands — and do not
derive the words from the metro name. **A three-band instance owes GEOMETRY as
well as words**: the region ring is the second output of
`build_metro_outline.py` (layer 0 of the same MapServer), simplified at the
SAME tolerance as the coverage outline, wired as the second argument of
`drawOutOfScopeMask`. A declared `region` with no geometry silently yields a
two-band key and no error — check the map, not the worksheet.

## 8. Verify each dataset before wiring it (§2.6.1)

The protocol has twelve steps; three fail silent and are worth carrying.
Sample exact VALUES, not field names — equality is case-sensitive and numerics
arrive as strings. Re-seed the worksheet's `hover_number_keys` and
`hover_name_keys` from OBSERVED keys; a stale list degrades the popup softly
and no gate notices. Verify COVERAGE, not existence — count how many of N
records carry the field and set floors below 100%. Label every registry row
VERIFIED / UNVERIFIED with a date, and record which of `loadSocrataGeoJSON`'s
routes actually served geometry.

## 9. Re-derive every gate constant; then the two hand audits

Smoke `POINT` / `EXPECT_LAYERS` / `EXPECT_DISTRICT` and a second point;
`MIN_REGISTER_LAYER`, `GEOMETRY_FILES`, `ROSTER_FILES`; the
`validate_sources.py` manifest; every count floor; `sw.js` `CACHE_NAME` and its
lists. Most are worksheet-emitted, so the write point is the worksheet. If
re-coring from a copy, delete only the `registerXxx({…})` calls and their
preamble, keep every factory and loader, then grep the ENTIRE file for
now-undefined identifiers in both directions.

No gate covers two things. Cross-group parity: for each field any card renders
(address, pin, phone, links), check every other card that could carry it. And
toggle every polygon layer and hover the ground-truth points, confirming REAL
identities — a real port shipped label-only.

## 10. The localization sweep, at assembly and again before launch (§2.7)

Grep the instance for the five fingerprints — `//chidistricts` (anchored to
URL position; the fleet's own domains contain the bare string),
`cityofchicago`, `ChiExplorer`, `chicago`, and the reference's
`data-goatcounter` tag — across `index.html`, `sw.js`, `README.md`,
`CLAUDE.md`, `WATCH.md`, `manifest.webmanifest`, `scripts/` and `.github/`.
Allowed: fence comments naming the reference, the reference's own
`metro_explorers` entry, deliberate citations. Never police `<tag>/data/` — the real
world contains the reference's vocabulary. Leave the `TEMPLATE:BEGIN/END`
markers alone.

## 11. Verify with the WHOLE battery, then go live as its own change

§2.9's list is a subset of CI by about nine gates. Run the steward skill's
battery (`.claude/skills/steward/SKILL.md` §1) from the repo root, one server
for every instance; `EXPECT_LAYERS` is asserted exactly and the negative point
must miss every anchor. In a sandbox the SessionStart hook vendors Leaflet; a
`page.waitForFunction` timeout is environmental.

Go-live is its own PR (Iowa's was its tenth): drop `<tag>` from the deploy's
`EXCLUDES`, confirm the landing pill, the privacy row and the coverage-map
outline through their `--check`s, and write `<tag>/CLAUDE.md`,
`<tag>/WATCH.md`, and the phase plan as `docs/<TAG>_EXPANSION_PLAN.md`
(`docs/IA_EXPANSION_PLAN.md` is the precedent).

## 12. Nevers

- Never copy the Illinois root layout; never copy a gate constant, a floor, or a hover-key list from a sibling.
- Never fake depth — no polygon for an at-large body, no name for an office nobody publishes.
- Never stitch county outlines into a wash; never derive the coverage key's words from the metro name.
- Never put a real API key in `index.html`.
- Never police `<tag>/data/` in the localization sweep, and never sweep the `TEMPLATE` markers away.
- Never run §2.9's subset and call it verified.

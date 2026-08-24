# NYC Conformance — adopting the mechanized structure

**ARCHIVED 2026-07-13 — executed in full.** Phases 0–3 done with every drill's failing
run URL recorded below. Moved to `docs/archive/` per this work order's own mandate.

Status: **work order, not a living document.** This file exists to be executed once and
archived. When the final checklist is fully green, move this file to `docs/archive/` (or
delete it) — a completed work order left at `docs/` is exactly the stale-copy failure mode
the mechanization exists to kill. Do not "maintain" this file.

Scope: everything the **NYC repo** must do to conform to the published-artifact /
generated-docs / reverse-parity structure defined in the Chicago repo's
`docs/MECHANIZATION_PLAYBOOK.md`, plus the NYC-side prerequisites of
`docs/REDISTRICTING_RUNBOOK.md`. Masters for both live in
`ThursdaysFamous/DistrictExplorer-CHI` under `docs/`; read them before executing any phase
here. Cross-refs in this repo: `METRO_EXPANSION_PLAYBOOK.md` (root pointer stub — the
pattern Phase 0 extends), `docs/ENGINE_SYNC.md`, `scripts/validate_index.py`,
`scripts/check_engine_parity.py`, `.github/workflows/deploy-pages.yml`.

Standing rule (inherited): a phase is DONE only when its acceptance check has run — and,
where a drill is specified, has **failed once on purpose** with the failing run URL
recorded in the evidence table at the bottom.

---

## Blocking map — what can start now vs. what waits on CHI

| NYC work | Blocks on CHI? |
|---|---|
| Phase 0 (pointer stubs, validate_sources port, repo setting) | **No — start today.** |
| Phase 1 (engine.lock.json, engine-bump.yml, deploy assembly) | Yes — CHI must tag the first `engine-v*` release and ship `apply_engine.py` in it. |
| Phase 2 (worksheet, generator, regenerate docs) | Yes — CHI publishes `generate_metro_files.py` + `schema/metro-worksheet.schema.json` (in the engine release tarball). Worksheet **authoring** can start today; generation waits. |
| Phase 3 (CAPABILITIES, generated METRO_EXPLORERS, coverage rollup) | Partially — CAPABILITIES shape and `chidistricts.com/metros.json` must exist CHI-side first. Builder coverage summaries can start today. |

Recommended order: Phase 0 immediately; author the Phase 2 worksheet while waiting; then
1 → 2 → 3 as CHI lands each dependency.

---

## Phase 0 — no CHI dependency, start today

**0.1 — Pointer-stub the two duplicated playbooks.**
`docs/BUILD_PLAYBOOK_1.md` and `docs/OPTIMIZATION_PLAYBOOK.md` in this repo are stale
verbatim Chicago copies (the build playbook is missing CHI's newest entries; the
optimization playbook is byte-identical to a past CHI snapshot — neither contains one line
of NYC history, which is archived at CHI `docs/archive/METRO_EXPANSION_NYC.md`). Replace
each with a pointer stub in the exact style of this repo's root
`METRO_EXPANSION_PLAYBOOK.md` stub: master location in the CHI repo, the one-paragraph
rationale ("the two copies drifted once already"), and where NYC's own history lives.
Conversion 2 does not generate these files; they simply must not exist as copies.
Also add `docs/REDISTRICTING_RUNBOOK.md` as a third pointer stub (master: CHI
`docs/REDISTRICTING_RUNBOOK.md`; owner CHI, applies fleet-wide).
*Acceptance:* each file ≤ 20 lines, contains the CHI master URL, contains no Chicago
build-log content. Update the `README.md` line that currently claims "the engine contract
and build history live in docs/BUILD_PLAYBOOK_1.md" to point at the stubs' targets.

**0.2 — Port `validate_sources.py` + monthly workflow.**
NYC's only freshness gate today is `check-school-zone-ids.yml` (monthly, cron
`0 12 1 * *`, watching the three year-versioned school-zone datasets `cmjf-yawu`,
`ruu9-egea`, `t26j-jbq7`). CHI has the full gate; NYC needs it for the redistricting
runbook's detection layer. Port CHI's `scripts/validate_sources.py` and
`.github/workflows/validate-sources.yml` (monthly; opens/updates ONE tracking issue on
WARN/FAIL; never edits anything; job stays green — the issue is the signal). Build the NYC
manifest by harvesting every source from `index.html` and labeling each from its module
comment. The harvested inventory, verified against the working tree:

- Socrata (`data.cityofnewyork.us`): `872g-cjhh` (council), `5crt-au7u` (community
  districts) + `ruf7-3wgc` (CB leadership roster, rows), `8ugf-3d8u` / `9nt8-h7nd`
  (precinct / sector boundaries), `ji82-xba5` (FacDB police-station points),
  `hc8x-tcnd` (firehouse points), `5rqd-h5ci`, `pri4-ifjk`, `y76i-bdw7`
  (NTA / MODZCTA / school districts — confirm each label from its module comment when
  writing the manifest), and the three school-zone ids above.
- ArcGIS: `services5.arcgis.com/GfwWNkhOj9bNBqoJ/.../NYC_Election_Districts/FeatureServer/0`,
  `.../NYC_Fire_Battalions/FeatureServer/0`;
  `services6.arcgis.com/EbVsqZ18sv1kVJ3k/.../NYS_Schools/FeatureServer/` layers 2/3/4.
- TIGERweb `Legislative/MapServer` (congress + NY Senate/Assembly).
- Anchor provenance (lives in `scripts/build_embedded_boundaries.py` comments, not
  index.html — the manifest must carry these like CHI's does): borough `gthc-hcne`,
  municipal court `7vpq-4bh4`, judicial districts (TIGERweb county-derived).

Add the runbook's `vintage` + `expected_successor` fields per source. The TIGERweb watch
matters double for NY — three congressional maps in three years — so the CD119→CD121
layer-name watch is not optional here. Fold the school-zone newer-edition search into this
script (it is the same catalog search) and retire `check-school-zone-ids.yml` +
`scripts/check_school_zone_ids.py` in the same PR.
*Acceptance:* `python3 scripts/validate_sources.py --offline` passes (manifest↔index drift
guard green); a deliberate manifest typo (`872g-cjhX`) makes it FAIL; the school-zone
workflow is deleted and its three ids appear in the new manifest with `year_search`
patterns.

**0.3 — Confirm the Actions PR setting.**
Settings → Actions → General → Workflow permissions → "Allow GitHub Actions to create and
approve pull requests" must be ON. Roster PR #6 suggests it is, but CHI shipped with this
exact setting off (the R11 postscript), and Phase 1's `engine-bump.yml` dies silently
without it. *Acceptance:* `gh api repos/ThursdaysFamous/DistrictExplorer-NYC/actions/permissions/workflow`
shows `"can_approve_pull_request_reviews": true`, or a screenshot of the setting recorded
in the evidence table.

---

## Phase 1 — Conversion 1 adoption (published engine artifact)

Prerequisite: CHI has tagged the first `engine-v*` release with `engine.bundle.js`,
`engine.manifest.json`, and the shared scripts (`apply_engine.py` at minimum) in the
release tarball.

**1.1 — Pin.** Add `engine.lock.json` at repo root:
`{ "engine_version": "engine-v1.0.0", "sha256": "<from CHI release manifest>", "source_repo": "ThursdaysFamous/DistrictExplorer-CHI" }`.

**1.2 — Bootstrap the shared scripts once.** Copy `scripts/apply_engine.py` from the CHI
release tarball by hand — this is the ONE manual copy. Every subsequent version arrives via
the bump PR, because the scripts ship inside the engine release. (The playbook's known gap:
shared scripts have no distribution channel of their own; the tarball IS the channel.)

**1.3 — `.github/workflows/engine-bump.yml`, on `main`.** `repository_dispatch` only
triggers default-branch workflows — a bump workflow parked on a feature branch never fires.
`on: repository_dispatch: types: [engine-release]` → update `engine.lock.json` from the
payload (`engine_version`, `sha256` — the payload carries nothing else) → run
`apply_engine.py` → `python3 scripts/validate_index.py index.html` →
`node scripts/smoke_test.mjs` → PR on the **fixed** branch `bot/engine-bump` with
force-push + the `gh pr list --head --state open` duplicate guard, byte-for-byte matching
the five roster workflows' pattern.

**1.4 — Deploy-time assembly.** In `.github/workflows/deploy-pages.yml`, insert BEFORE the
"Assemble site" rsync step:

```yaml
      - name: Fetch + verify + apply pinned engine
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          ver="$(jq -r .engine_version engine.lock.json)"
          gh release download "$ver" \
            --repo ThursdaysFamous/DistrictExplorer-CHI \
            --pattern 'engine.bundle.js' --pattern 'engine.manifest.json' --clobber
          echo "$(jq -r .sha256 engine.lock.json)  engine.bundle.js" | sha256sum --check -
          python3 scripts/apply_engine.py
          python3 scripts/validate_index.py index.html
          python3 scripts/check_engine_parity.py index.html --against-bundle engine.manifest.json --strict
```

Two spaces between hash and filename in the `sha256sum --check` line — one space breaks
parsing. CHI is public, so `github.token` suffices for the download; NYC needs **no**
`ENGINE_DISPATCH_TOKEN` (that secret is CHI-side only). The last line is the parity
checker's demotion: post-assembly assertion against the downloaded bundle, no longer a
cross-fork drift detector. The fences in `index.html` / `sw.js` do not change — they are
assembly markers now. NYC's 45 + 2 ENGINE blocks are already byte-identical to CHI
(verified `--strict` clean), so the first assembly must be a **no-op**: after step 1.4's
first successful run, `git diff index.html sw.js` is empty.

**1.5 — The corruption drill (required evidence).** On a branch: set a wrong sha in
`engine.lock.json`, push, and confirm CI fails at `sha256sum --check`. Record the failing
run URL below. This is NYC's contribution to the metro-#3 gate.

**1.6 — Retire `engine-parity.yml`.** NYC's copy is already `workflow_dispatch`-only;
after one clean assembled deploy plus the drill, delete it. The weekly cross-fork watcher
was always CHI-side and is superseded by construction.

*Phase DONE when:* first automated bump PR from CHI merges green here, AND the corruption
drill URL is recorded.

*Phase 1 DONE 2026-07-13.* Both conditions met: the corruption drill is recorded in the
evidence table below (run 29209945390), and the first automated bump PR —
[#23](https://github.com/ThursdaysFamous/DistrictExplorer-NYC/pull/23), opened by
`engine-bump.yml` from CHI's `engine-v1.0.1` fan-out (dispatch run
[29212955843](https://github.com/ThursdaysFamous/DistrictExplorer-NYC/actions/runs/29212955843),
all gates green; branch smoke run 29213011493 green) — merged. The bump delivered the
`--against-bundle` mode in the shared parity script; the explicit post-assembly assertion
lines now live in `deploy-pages.yml`, and `engine-parity.yml` is deleted (1.6).

---

## Phase 2 — Conversion 2 adoption (generated docs/config)

Prerequisite: CHI publishes `generate_metro_files.py` + `schema/metro-worksheet.schema.json`
in the engine release.

**2.1 — Author `metro-worksheet.json` (can start today).** The real NYC facts, all
verified against the working tree:

- Identity: `this_metro: "nyc"`, `metro_name: "New York City"`,
  `metro_bbox: {-74.27, 40.48, -73.68, 40.93}`, `metro_center: [40.7128, -74.0060]`,
  `permalink_gate` (the wider box already in the METRO block).
- Socrata: `socrata_host: "https://data.cityofnewyork.us"`; app-token as a secret
  reference.
- `repo_issues`, `feedback_subject: "NYC District Explorer feedback"`;
  `highlight_class: "nyc-region-highlight"`, `poi_pin_class: "nyc-poi-pin"`;
  `hover_number_keys` / `hover_name_keys` re-seeded from **observed NYC field names**
  (this is the layer where Chicago vocabulary once survived the port invisibly — treat the
  worksheet as the audit).
- `layers`: all 24 ids with group + area_rank, transcribed from `LAYER_AREA_RANK` and
  `EXPECT_LAYER_IDS` (they already agree; the worksheet becomes the single source both are
  generated from).
- `anchors`: borough / judicial-district / municipal-court, ground truth City Hall
  `40.71274,-74.00602` → Manhattan, negative point `40.7223,-73.9697` (mid-East-River, no
  borough), plus the runbook's second-point-that-changed-districts slot (empty until the
  first remap).
- `data_sources`: the Phase 0.2 manifest rows (one authoring, two consumers).
- `workflows`: the **actual five** — `update-cec-roster`, `update-congress-roster`,
  `update-council-roster`, `update-ny-legislature-roster`, `update-nypd-roster` — with
  schedules and secrets (`NYSENATE_API_KEY`, `OPENSTATES_API_KEY`).
- `geocoder`: `geocodeAddress` = GeoSearch (`geosearch.planninglabs.nyc/v2/autocomplete`),
  `geocodeUnbounded` = Photon, `poiGeocodeRequest` = GeoSearch.
- `palette` (`#12305C` / `#FF6319` family), `domains`: `nyc.chidistricts.com`; exports
  name `window.NycExplorer`; sw cache prefix `nyc-district-explorer-shell` (current `-v6`).

*Acceptance:* worksheet validates against the schema (`jsonschema`, pinned).

**2.2 — Generate.** Add `GENERATED:BEGIN/END` fences to the six targets (`CLAUDE.md`,
README skeleton sections, the index.html METRO block, sw.js METRO config, validator
constants, smoke-test constants) and run the generator. Two long-standing lies die in this
step, and the diff should show both: (a) the stale Chicago `CLAUDE.md` is replaced wholesale
— wrong city, wrong geocoder, wrong workflows, wrong ground truth, and the obsolete
`js_string()` guidance CHI already retired; (b) the sw.js comment claiming
`nypd-precinct-info.json` "ships as an empty placeholder" is corrected — that roster is
populated (78 keys); the actual placeholders are `cec-members.json` and
`borough-officials.json`.

**2.3 — Wire `--check` into CI** (new step alongside `validate_index.py` in the smoke-test
workflow, or folded into the validator per the CHI master's choice).

**2.4 — The drift drill (required evidence).** Hand-edit one generated region in a
committed file (flip the ground-truth borough to "Brooklyn"), push, confirm the `--check`
step fails. Record the run URL.

*Phase DONE when:* NYC's `CLAUDE.md` at HEAD is generator output, the old copy is gone,
and the drift-drill URL is recorded.

---

## Phase 3 — Conversion 3 participation (reverse-parity)

**3.1 — Declare `CAPABILITIES`** in `scripts/validate_index.py`, in the machine-readable
shape the CHI fleet-status job parses (a module-level list of strings; take the shape from
the CHI master, don't invent one). NYC's opening list is the interesting one — it is what
fires the first reverse-parity WARN against CHI: `expect-layer-ids`,
`layer-area-rank-lint`, `sw-exactly-one-list`, `metro-explorers-lint`,
`all-anchors-registered`. When the parallel CHI session back-ports the first two, the WARN
clears — that clearing is Conversion 3's own definition-of-done, and NYC's declaration is
what makes it fire at all.

**3.2 — `METRO_EXPLORERS` becomes generated.** Stop hand-editing the list in the METRO
block; the generator emits it from `chidistricts.com/metros.json` at generation time.
**Runtime behavior unchanged** — the app never fetches metros.json; the hardcoded copy in
the page remains the offline value, exactly as the CHI master decided. Launching metro #3
then touches this repo only via a regeneration PR, not a hand edit.

**3.3 — Per-field coverage summaries.** The CHI CPD scraper prints a one-line per-field
coverage summary; NYC's five builders don't. Add the same one-liner to each
(`build_council_roster.py`, `build_ny_roster.py`, `build_nypd_roster.py`,
`build_cec_roster.py`, `build_congress_roster.py`) so the CHI fleet rollup isn't
single-city. Known baseline to encode, not "fix": NYPD resolves ~74/78 commanding officers
— honest nulls, floors already below 100%.

**3.4 — PR-template DoD line.** Add to `.github/pull_request_template.md`: a fork-born
engine-quality change must link its CHI tracking issue and is not done until the CHI
release containing it is tagged (ENGINE_SYNC DoD addition).

*Phase DONE when:* NYC appears in CHI's first fleet-status output with version, capability
diff, and scraper rollup populated.

---

## Explicitly NOT this repo's job

`ENGINE_DISPATCH_TOKEN`, `release-engine.yml`, the fleet-status workflow, hosting
`metros.json`, and the engine changelog — all CHI-side. NYC also does not write a
redistricting runbook of its own; it carries the Phase 0 pointer stub and supplies its
per-layer facts through the worksheet.

## Already conformant (no work, worth knowing)

`scripts/build_embedded_boundaries.py` here registers **all three** anchors — NYC is ahead
of CHI on redistricting-runbook step 5, so no NYC work there. The validator's per-ID and
area-rank guards are likewise ahead; Phase 3.1 turns that lead into the mechanism that
forces the back-port. Orthogonal and out of scope for this work order: populating the
`cec-members.json` / `borough-officials.json` placeholders (tracked by their own §9/§11.3
operator steps).

---

## Final conformance checklist

| # | Item | Check | Done |
|---|---|---|---|
| 0.1 | Three pointer stubs, README fixed | files ≤20 lines, CHI URLs present | ☑ 2026-07-12 (15/15/16 lines, CHI URLs in all three, zero Chicago build-log content) |
| 0.2 | validate_sources ported, school-zone check folded in | offline gate green; typo drill FAILs | ☑ 2026-07-12 (`--offline` exit 0; full online run 0 FAIL · 0 WARN · 24 OK; drill below) |
| 0.3 | Actions-can-create-PRs confirmed | API/screenshot evidence | ☑ 2026-07-12 (empirical — see evidence note below the drill table) |
| 1.1–1.4 | Lockfile, bump workflow, deploy assembly | first assembly = empty `git diff` | ☑ 2026-07-12 (engine-v1.0.0 pinned, sha `47d6d1ff…`; local assembly run: sha256sum OK, 45+2 blocks spliced **0 updated**, `git diff index.html sw.js` empty; note: the 1.4 snippet's `check_engine_parity.py --against-bundle` flag doesn't exist in the shared script yet — must land CHI-first; until then apply_engine.py's splice self-check enforces the same assertion, documented in deploy-pages.yml. **Resolved 2026-07-13:** the flag landed CHI-side (CHI #91), shipped in `engine-v1.0.1`, arrived here via bump PR #23; the explicit `--strict` assertion lines are now in deploy-pages.yml) |
| 1.5 | Corruption drill | failing run URL recorded | ☑ 2026-07-12 (failed at `sha256sum --check` — see evidence table; first attempt exposed that the one-job deploy layout could never run on a branch — github-pages environment branch protection — fixed by splitting assemble/deploy jobs) |
| 1.6 | engine-parity.yml deleted | one clean assembled deploy first | ☑ 2026-07-13 (clean assembled deploys on main: run 29212551023 after #22 merged, again after bump PR #23; workflow deleted + `--against-bundle --strict` assertion lines added in the close-out PR) |
| 2.1 | Worksheet authored + schema-valid | jsonschema pass | ☑ 2026-07-13 (metro-worksheet.json validates against schema/metro-worksheet.schema.json from the engine-v1.0.2 release assets; all 24 layers, City Hall anchors, mid-East-River negative point) |
| 2.2 | Six targets generated; stale CLAUDE.md gone; sw.js comment fixed | diff shows both | ☑ 2026-07-13 (seven GENERATED regions across six files; CLAUDE.md replaced wholesale — the stale copy still opened "Chicago District Explorer" — and the sw.js nypd-placeholder claim is gone, both visible in the #27 diff) |
| 2.3–2.4 | `--check` in CI + drift drill | failing run URL recorded | ☑ 2026-07-13 (--check step first in smoke-test.yml; drill below) |
| 3.1 | CAPABILITIES declared | first reverse-parity WARN fires CHI-side | ☑ 2026-07-13 (#28 declared the CHI-mastered shape + negative-point-ground-truth, born here; the WARN fired CHI-side — run 29217295970, issue CHI#98 — and cleared after the engine-v1.0.3 back-port, run 29217657897) |
| 3.2 | METRO_EXPLORERS generated | hand-edit now fails `--check` | ☑ 2026-07-13 (emitted from the worksheet, synced from chidistricts.com/metros.json via `--sync-fleet` — arrived with the v1.0.3 bump #29; live sync verified a byte no-op; hand-edits fail `--check` per the 2.4 drill) |
| 3.3 | Coverage one-liners in five builders | visible in weekly roster runs | ☑ 2026-07-13 (#28; fleet-status greps them from run logs — CHI#98 already shows the convention working on CHI's CPD line; NYC lines appear as the weekly runs cycle) |
| 3.4 | PR-template DoD line | present | ☑ 2026-07-13 (#28) |
| — | Archive this file | moved to docs/archive/ | ☑ 2026-07-13 (this PR — the checklist is fully green) |

## Drill evidence (fill in — metro-#3 gate inputs)

| Drill | Failing run URL | Date | Cleared by |
|---|---|---|---|
| Engine hash corruption (1.5) | https://github.com/ThursdaysFamous/DistrictExplorer-NYC/actions/runs/29209945390 — `assemble` failed at step "Fetch + verify + apply pinned engine": `engine.bundle.js: FAILED / sha256sum: WARNING: 1 computed checksum did NOT match / exit 1`; deploy job skipped (main-only). Invalid first attempt for the record: run 29209843703 died at github-pages environment branch protection with zero steps run, which forced the assemble/deploy job split. | 2026-07-12 | lockfile restored |
| Generated-region drift (2.4) | https://github.com/ThursdaysFamous/DistrictExplorer-NYC/actions/runs/29216548888 — commit 2e9edc2 hand-flipped the ground-truth borough to "Brooklyn" inside smoke_test.mjs's GENERATED region; the `Generated regions match the worksheet` step failed with the unified diff, all downstream steps skipped | 2026-07-13 | regeneration (revert commit) |
| validate_sources manifest typo (0.2) | local pre-CI run (no run URL): `872g-cjhh`→`872g-cjhX` in the manifest, `python3 scripts/validate_sources.py --offline` exited **1** with `FAIL — City Council District (51) — dataset id 872g-cjhX not found in index.html — manifest is out of sync with the app (update scripts/validate_sources.py)`; exit 0 after revert | 2026-07-12 | typo reverted |

**0.3 evidence (2026-07-12).** The direct check could not run from the sandbox: the
session's egress proxy answers `GET repos/ThursdaysFamous/DistrictExplorer-NYC/actions/permissions/workflow`
with HTTP 403 `"Access to this GitHub Actions path is not permitted through this proxy"`.
Recorded empirically instead, which is conclusive: [PR #6](https://github.com/ThursdaysFamous/DistrictExplorer-NYC/pull/6)
was created 2026-07-10 by `github-actions[bot]` via `gh pr create` running with
`GH_TOKEN: ${{ github.token }}` (`update-ny-legislature-roster.yml`), and PR creation with
the built-in Actions token hard-fails ("GitHub Actions is not permitted to create or
approve pull requests") unless the Settings → Actions → General toggle is ON. An operator
`gh api` run from outside the sandbox can double-confirm at any time.

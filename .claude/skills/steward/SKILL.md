---
name: steward
description: How to drive a districtry pull request to green — the full local gate battery with its real invocations, and why a red bot roster PR is a data event rather than a code bug.
---

# Stewarding a districtry PR

This file exists for one job: an agent reacting to CI or review activity on a
districtry pull request. It carries only what the default PR-driving rules and
`CLAUDE.md` do **not** already say. Everything about architecture, the ENGINE
fences, the honesty rules and the layer contract lives in `CLAUDE.md` and the
per-instance `<tag>/CLAUDE.md`, is loaded on every turn, and is deliberately
**not** restated here — two documents stating one convention is how
`ENGINE_SYNC.md` drifted 164 lines from the fences it described.

## 1. Reproduce CI locally — the whole battery, in CI's own order

The generic advice ("run the repo's lint, format, typecheck and unit tests")
does not apply: this repo has none of those. It has ~20 Python drift gates and
7 browser runs. **`.github/workflows/smoke-test.yml` is the source of truth** —
if this list and that file disagree, that file wins and this one is stale.

Two of these are easy to get wrong, and both fail in a way that misleads:

- **Illinois' smoke test lives at the repo root**, `scripts/smoke_test.mjs`,
  not `il/scripts/`. The other four instances have their own. Guessing the
  symmetric path gives `MODULE_NOT_FOUND`, which reads like a missing
  dependency rather than a wrong path.
- **`build_coverage_gaps.py` needs `--out` as well as `--metro`.** `--metro`
  only chooses which key to emit; without `--out` it still compares against
  Illinois' shipped file and fails with a byte-count mismatch
  (`60884 vs 745 bytes`) that looks like real drift in the instance you named.

```bash
pip install -c scripts/requirements.txt jsonschema

# --- static gates (stdlib unless noted; fail fast, run these first)
python3 scripts/generate_metro_files.py --check          # GENERATED regions vs worksheets
python3 scripts/build_coverage_gaps.py --check
python3 scripts/build_coverage_gaps.py --check --metro wisconsin --out wi/data/app/coverage-gaps.json
python3 scripts/build_coverage_gaps.py --check --metro iowa      --out ia/data/app/coverage-gaps.json
python3 wi/scripts/build_wi_county_board_directory.py --check
python3 wi/scripts/build_wi_county_outlines.py --check
python3 scripts/build_brand_tokens.py --check            # must precede compose_app
python3 scripts/validate_contrast.py                     # text vs ground, both tiers
python3 scripts/compose_app.py --check                   # engine/ vs every instance's fences
python3 scripts/build_county_status.py --check
python3 scripts/backfill_board_seats.py --check
python3 scripts/build_dark_map_palette.py --check
python3 scripts/build_landing_page.py --check
python3 scripts/build_privacy_page.py --check
python3 scripts/build_history_page.py --check
python3 scripts/build_manifests.py --check
python3 scripts/validate_favicon.py
python3 scripts/validate_shell_continuations.py
python3 scripts/validate_workflow_deps.py
python3 scripts/validate_skills.py                       # every skill's pointers resolve
python3 scripts/check_roster_retention.py --base origin/main

# --- per-instance static gate (all five run from the repo ROOT)
python3 scripts/validate_index.py    il/index.html
python3 ca/scripts/validate_index.py ca/index.html
python3 ny/scripts/validate_index.py ny/index.html
python3 wi/scripts/validate_index.py wi/index.html
python3 ia/scripts/validate_index.py ia/index.html

# --- browser gates: ONE server at the repo root, every instance
python3 -m http.server 8000 &
BASE_URL=http://localhost:8000/il/ node scripts/smoke_test.mjs
BASE_URL=http://localhost:8000/ca/ node ca/scripts/smoke_test.mjs
BASE_URL=http://localhost:8000/ny/ node ny/scripts/smoke_test.mjs
BASE_URL=http://localhost:8000/wi/ node wi/scripts/smoke_test.mjs
BASE_URL=http://localhost:8000/ia/ node ia/scripts/smoke_test.mjs
BASE_URL=http://localhost:8000      node scripts/landing_test.mjs
BASE_URL=http://localhost:8000      node scripts/page_consistency_test.mjs
```

`BASE_URL` for the two root tests takes **no trailing slash** — a trailing one
produces `http://localhost:8000//` and two spurious failures.

Not in CI, but run it before shipping a change that touches a source or a
card link, because the monthly job will otherwise find it for you:
`python3 ia/scripts/validate_sources.py` (or the instance's own) and
`python3 scripts/validate_card_links.py`.

## 2. A red bot roster PR is usually a DATA event, not a code bug

~68 weekly workflows open `bot/*` PRs into this repo, so they are the majority
of PRs it will ever see, and the generic "fix and push" posture points the
wrong way on them. When one goes red the cause is nearly always **a publisher
changing what it publishes**, not a defect in the diff:

- **`check_roster_retention.py` failed** — a field stopped being published.
  Read the failure: it names the file, the field and the per-source coverage.
  Go look at the publisher's page before touching anything. If the drop is
  real and legitimate (a consolidated election emptying a column, an office
  genuinely vacated), record it in `ACCEPTED_DROPS` **with a reason and a
  date**. If it is a scrape regression (the Brown County case: Cloudflare
  turned `mailto:` into `data-cfemail` and seven addresses silently emptied),
  fix the scraper.
- **A builder refused to write** — its count guard or floor tripped. That
  refusal is the builder working. Diagnose the source; do not lower the floor.
- **`validate_sources.py` reports a host reachable that is recorded as
  blocked** — that inversion is deliberate. Becoming reachable is the
  actionable state, and the fix is to reconsider the block, not to silence it.

## 3. Nevers specific to this repo

- **Never loosen a floor, a count guard, a retention threshold or a population
  deviation ceiling to get a check green.** Those numbers are the honesty
  mechanism, not test scaffolding. Raising one is a decision with a named
  reason and a source that confirms it (see how Wayne's and Clay's deviation
  ceilings were raised — each on the county clerk's own written confirmation,
  for that county alone, with the measured value recorded rather than smoothed).
- **Never hand-edit a `GENERATED:BEGIN/END` region or an `ENGINE:BEGIN/END`
  fence inside an instance file to satisfy a drift check.** Edit
  `metro-worksheet.json` or the block under `engine/` and regenerate. The
  check is telling you the generate step was skipped.
- **Never commit roster data straight to `main`.** Officeholder data gets a
  human review; the refresh workflows open PRs for exactly that reason.
- **Never chase a sandbox Leaflet/MapLibre failure into app code.** `L is not
  defined` in a local headless run is the CDN being unreachable from the
  sandbox — `CLAUDE.md` has the vendoring story. Production and GitHub Actions
  reach the CDN directly.

## 4. Judgment

A gate that fails is usually right. Before changing code to satisfy one, state
what the gate is actually asserting and why the current tree violates it — the
most common correct fix in this repo is to run a generator, not to edit an
artifact.

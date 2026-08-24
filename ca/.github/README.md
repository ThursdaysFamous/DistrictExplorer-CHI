# Nothing here runs. The refreshes that used to be here now do.

GitHub Actions reads workflows only from **`.github/workflows/` at the
repository root**. Anything under `ca/.github/` is inert — nothing in this
directory is scheduled, nothing fires on a push, and nothing here has ever run
in this repository.

This directory came across with the `ca/` tree when `DistrictExplorer-SF` was
imported (R3, `docs/DEV_PROCESS_ASSESSMENT.md`), bringing that fork's whole
`.github/` with it. Until 2026-08-24 its seven workflows were parked here as
the source material for the move. **That move is done.**

## Where each one went

Four were rewritten with instance-aware paths and moved to the root, prefixed
`ca-` because five basenames collided across the three instances:

| was | now |
|---|---|
| `update-sf-supervisor-roster.yml` | `.github/workflows/ca-update-sf-supervisor-roster.yml` |
| `update-ca-legislature-roster.yml` | `.github/workflows/ca-update-legislature-roster.yml` |
| `update-congress-roster.yml` | `.github/workflows/ca-update-congress-roster.yml` |
| `validate-sources.yml` | `.github/workflows/ca-validate-sources.yml` |

Three were **deleted**, not moved, because the monorepo's own root workflows
already do their job for all three instances: `deploy-pages.yml` (the root job
publishes the whole tree), `smoke-test.yml` (the root job runs every instance's
`validate_index` and `smoke_test.mjs`), and `engine-bump.yml` (it consumed a
`repository_dispatch` from the Chicago fork's engine-release channel, which was
retired at R2.1 — one repo now holds one engine, spliced by
`scripts/compose_app.py`).

## What is still inert here, and why that is fine

`ISSUE_TEMPLATE/source-submission.yml` and `rulesets/protect-main.json` remain.
They configure nothing from this path either, but they refresh no data and
freeze nothing — both are byte-identical to the root's live copies. They are
left alone rather than swept in a change about roster automation.

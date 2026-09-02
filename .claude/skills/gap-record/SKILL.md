---
name: gap-record
description: Write, correct or retire an entry in the guidebook's gaps block — record a MEASURED absence in the two-audience shape build_coverage_gaps.py enforces, keep the ask ledger inside its blocker field, and regenerate the panel files and COUNTY_STATUS so the gates stay green. Use it for "record the gap for Jasper — measured, not guessed", "write up Bureau's blocker, the assessor sent a licence", "Pope says NOT YET ASKED but we sent three, fix the ledger", "add a coverage gap for Jones County's supervisor districts", "retire the stale coverage claims for the seven counties that shipped", "build_coverage_gaps says summary is 312 characters", "the NYC panel needs a gap for the community-board roster". Not for probing the source (county-n-plus-1), drafting the e-mail (outbound-ask), or a red PR (steward).
---

# A gap record

A gap record is the only thing that makes an absence visible: four counties
sat unbuilt for weeks with every gate green because nothing was on file to
notice. `CLAUDE.md` carries that lesson and the "record the blocker you
MEASURED" rule; `scripts/build_coverage_gaps.py` enforces the record's shape
and is the authority on it. This is the procedure, thin because the content
churns daily.

## 1. Where it lives, and what reads it

The block between `<!-- ==== GUIDEBOOK:BEGIN gaps ==== -->` and its END marker
in `docs/DATA_LAYER_GUIDEBOOK.md` — one JSON object keyed per metro
(`chicago`, `nyc`, `sf`, `wisconsin`, `iowa`; an instance's array must exist
even if empty). `scripts/build_coverage_gaps.py` renders it to each instance's
`<tag>/data/app/coverage-gaps.json` for the Data gaps panel; `docs/COUNTY_STATUS.md`
and the weekly fleet-status run read the result. Line numbers in the block
move daily; grep the markers.

## 2. Before writing, read your own records

Grep the guidebook for the unit — it may already live inside another record
that names several counties. Grep the scraper tables and builder docstrings.
Read `docs/ASK_DRAFTS.md`. Search the sent mail: treat the record as a
hypothesis about the mailbox, and write the real date back. A near-duplicate
ask to a non-replying office is worse than no ask.

## 3. Decide whether it belongs

Only gaps a READER COULD HELP CLOSE — a missing or blocked source, or a shipped
layer's known hole. Not a concept that structurally does not apply (that is a
matrix cell), not a live outage (the card reports it), not a parity debt.

## 4. The shape — two audiences, four lints

`REQUIRED` in the builder: `id`, `concept`, `area`, `kind`, `summary`, `why`,
`blocker`, `wanted`, plus `layer` and `counties`. `id` is stable kebab-case
and unique (it keys the shipped file and appears in `COUNTY_STATUS`). `layer`
is a registered id in THAT instance's worksheet, or null for an unbuilt
concept. `counties` are shipped outline slugs — an unserved county with a gap
ships its outline as gap-location geometry only. `kind` is one of `KINDS`:
`no-source` / `blocked` (a source exists and refuses automation or is
licence-gated) / `data-quality` (a shipped layer with a known hole).

**The reader fields** — `summary`, `why`, `wanted` — ship to the panel. Each
is at most `READER_MAX` characters, carries no URL or hostname, no ISO date
(write "since 2021"), and no two adjacent ALL-CAPS words; the builder refuses
on any of the four. `summary` speaks from the reader's side and says what
DOES work in the same breath; `why` is one plain sentence of cause; `wanted`
states what would close it, so a reader is never invited to re-send a source
already checked and found wanting.

**`blocker`** — unbounded, never shipped, an append-only dated log in record
voice for the next maintainer. Open with `MEASURED <date> by <method>` (or
"Checked / Probed <date>"); prefix every later finding with a dated tag —
CORRECTED, RE-MEASURED, SWEPT, PARTLY CLOSED, CLOSED, ANSWERED — and keep the
disproved sentence in place under its correction. Every host, date and
status goes here, in the vocabulary of what was measured: unresponsive,
licence-gated, split-precinct, raster-only. "No source exists" is almost
never one of them. A domain that resolves AND has MX AND refuses only HTTP is
a county with e-mail and no website.

## 5. The ask ledger lives inside `blocker`, as prose

`NOT YET ASKED` → `NOT YET ASKED — DRAFTED` (the draft goes in
`docs/ASK_DRAFTS.md`; the agent never sends) → `ASKED <date>`, written the day
it goes and never before → `ANSWERED <date>` with the reply's substance, or
`UNRESPONSIVE` only after the follow-up cadence the outbound-ask skill
carries. No structured `asked` field exists; the vocabulary is the contract.

## 6. Closing

A shipped county's entry is DELETED from the block — its story moves to a
dated backlog section. A multi-county record shrinks and says so ("this
record used to name five counties"). A partial close stays, with
`PARTLY CLOSED <date>` and a narrowed `wanted`. A gap that says a source does
not exist ages badly in one direction only; re-test the `no-source` entries
periodically.

## 7. Regenerate, then gate — every instance whose key changed

```bash
python3 scripts/build_coverage_gaps.py                                                     # Illinois
python3 scripts/build_coverage_gaps.py --metro wisconsin --out wi/data/app/coverage-gaps.json
python3 scripts/build_coverage_gaps.py --metro iowa      --out ia/data/app/coverage-gaps.json
python3 scripts/build_county_status.py
```

(`--metro nyc` / `--metro sf` with their `--out` when those keys change.)
`--metro` only chooses the key; without `--out` the check still compares
against Illinois's shipped file and fails with a byte-count mismatch that
looks like real drift. Then `--check` on each, and the steward battery.

## 8. Nevers

- Never a hostname, a status code or a date in a reader field.
- Never `ASKED` before the day it went; never `UNRESPONSIVE` before the follow-ups.
- Never "no source exists" for a blocker that was measured as something else.
- Never edit the record without regenerating every file that reads it.
- Never a gap for a concept that structurally does not apply, or for a live outage.

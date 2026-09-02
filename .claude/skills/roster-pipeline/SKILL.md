---
name: roster-pipeline
description: Write or clone the roster pipeline for a county whose source and board form are already settled — the districted scraper → builder → weekly-workflow triple, or the at-large rows in the shared commissioners pair — so the file, its guards, its tripwire, its workflow and its registrations match the fleet's conventions and pass every gate on the first dispatch. Use it for "ship Jasper's roster, the Richland shape", "write build_ford_county_board.py and its workflow", "clone the Wayne triple for Marion", "Pope's clerk e-mailed three names, carry them like Wabash", "what cron slot is free", "MIN_EMAILS for Bureau, measured 5 of 7", "SITES entry or RETURNS_ROSTERS?", "what does a new roster builder have to refuse on". Not for deciding the source or the board's form (county-n-plus-1), municipal officials (municipal-officials), a red bot PR (steward), or Wisconsin and Iowa, which run one workflow per state.
---

# A roster's pipeline

`CLAUDE.md` carries the scraper → builder → bot-PR pattern, `BOT_PR_TOKEN`,
the diff gate and the retention gate; the steward skill carries what to do
when a run goes red; county-n-plus-1 carries how the source and the board's
form were settled. This carries the MECHANICS: the three most recent Illinois
triples — Richland, Wayne, Clay — are line-for-line identical in everything
that is not a county fact, and an agent opening a blank scraper file gets
those lines wrong by guessing. What varies per county is listed at the end so
it is never mistaken for convention.

## 1. Pick the shape; it decides which files exist

**Districted** → its own triple: `scripts/<county>_county_board_scraper.py`,
`scripts/build_<county>_county_board.py`,
`.github/workflows/update-<county>-county-board-roster.yml`, writing
`il/data/app/<county>-county-board-members.json`. Older builders carry a
`_roster` suffix (`scripts/backfill_board_seats.py`'s `COUNTIES` lists five);
the 2026-08-23 and later ones drop it — match the newer form.

**At-large** → NO new files. A `SITES` entry with a `parse_<county>` function
in `scripts/il_county_commissioners_scraper.py` — or a `DOCUMENT_ROSTERS` row
(a document the clerk sent: `document`, `verified`, `expect`, `members`) or a
`RETURNS_ROSTERS` row (certified winners) — plus an `EXPECT_MEMBERS` row in
`scripts/build_county_commissioners.py`. The key is `norm_key()`'s: uppercase
letters only, "COUNTY" stripped, the same key `il-county-clerks.json` uses. A
county sits in exactly ONE of the three tables. If the county styles its chair
a new way, widen `ALLOWED_ROLES` and `CHAIR_ROLES` TOGETHER — widening one
without the other is the hole.

## 2. Clone from the three complete triples

Richland is the two-source tripwire (composition read from the county's GIS
each run); Wayne is the composition on the roster page, with a per-district
SUBSET exception (`PAGE_SUBSET_DISTRICTS` in
`scripts/build_wayne_county_board.py`, reason in the docstring); Clay is two
pages, with roles joined across surfaces. Then grep the new files for the old
county's name, slug and domain — the workflow's PR title and body are a
human-review surface.

## 3. The scraper

`from scraper_common import make_fail, UA_ROSTER_BOT` (`scripts/scraper_common.py`);
`fail = make_fail("<county>-board-scraper")`; a `HEADERS` dict with the bot UA.
Never change a shipped scraper's UA constant — each constant is the exact
bytes its importers were already sending. `argparse` with `-o/--output`; the
workflow always passes `-o /tmp/<county>_board_raw.json`. Emit
`json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)` plus a
newline, naming the source beside the records. Scope the parse to the county's
MAINTAINED block and `fail()` if its marker vanishes, rather than reading names
off the whole page (Richland's committees list people who do not sit on the
board). `fail()` on a card whose position line does not parse. Where the page
prints a datum twice, require the copies to agree. Emit ONLY what the page
publishes — no party, term, phone or e-mail invented — and say in the
docstring what it publishes and what it does not. If the tripwire input lives
on the same page or on the county's GIS, re-read it into the payload every run.

## 4. The builder

`sys.argv[1]` is the raw JSON, optional `sys.argv[2]` the out dir,
`DEFAULT_OUT_DIR` is `il/data/app`; `fail = make_fail("<county>-board-roster")`.
Import ONLY constants — `COMPOSITION`, `COUNTY_PRECINCTS`,
`SEATS_PER_DISTRICT` — from `scripts/build_<county>_boundaries.py`
(`scripts/build_richland_boundaries.py` is the shape); that module's shapely
import is function-local, the De Witt seam, or `scripts/validate_workflow_deps.py`
fails the merge and the weekly job dies on import. Compare names with `norm`
from `scripts/vtd_board_districts.py`.

**Run the drift check FIRST, before the roster.** Re-read the composition
against `COMPOSITION`: district set equal; per-district precinct set equal,
or a subset for districts in the subset exception. Every drift `fail()` names
the re-derivation script. Then the roster guards — EXACT, never floored:
district count `== EXPECT_DISTRICTS`; total `== EXPECT_MEMBERS`; per district
`== SEATS_PER_DISTRICT`; every district key present in `COMPOSITION`; a
duplicate in a one-member district fails; a nameless member fails. Field
floors are the MEASURED count minus one vacancy
(`MIN_EMAILS` in `scripts/build_richland_county_board.py` reads
`6  # measured 7/7`), and phones get a shape check. At most one Chairman and
one Vice Chairman; when two county surfaces name the chair they must agree or
the build fails; a role joined by surname must be UNIQUE and the join is
PRINTED every run, shipping the roster page's spelling. Members sorted by name;
`json.dump(roster, indent=2, ensure_ascii=False, sort_keys=True)` plus newline.
The final prints say what was written, with counts and the chair, and then
state that the tripwire matched AND what it cannot see — a green tick that
covered nothing is the alternative.

## 5. The two output schemas

**Districted:** `{ "<district id>": { "members": [ {name, role?, email?, phone?} ], "sourceUrl": <roster page> } }`.
The district is the KEY, never a member field. `seats` per entry only where
the builder tolerates a short list; `vacancies` only where the county prints
the word.

**At-large** (`il/data/app/il-county-commissioners.json`):
`{ "<KEY>": { county, structure, members[], seats?, office?, and EXACTLY ONE of sourceUrl | sourceDocument + verified } }`.
`seats` may not be smaller than the roster and may not EQUAL it — drop the
field rather than ship a shortfall of nothing. The returns tier adds `seat`,
`party`, `since`, `districtSource`.

There is NO `verifiedDate` key anywhere in the repo: the document tier uses
`verified` (an ISO date); `verified_date` is the worksheet's UI key and
unrelated. The card renders exactly `name`, `role`, `party`, `city`, `phone`,
`phonesExtra`, `email`, `url`, `committees` per member and reads `seats` /
`vacancies` for the shortfall note (`boardMemberPerson` in `il/index.html`).
ADDING A FIELD TO THE SCRAPER IS NOT ADDING IT TO THE APP.

## 6. The workflow

Five load-bearing lines, identical across the three
(`.github/workflows/update-richland-county-board-roster.yml` is the template):

- a header explaining BOTH jobs, roster and tripwire, and WHAT THE CHECK CANNOT SEE;
- `on: schedule` on the hour in a free weekday/hour slot between 13:00 and 22:00 UTC — grep every `.github/workflows/update-*.yml` for `cron:` and take an unused pair; `roster-health.yml` runs daily at 23:00 after the last roster slot — plus `workflow_dispatch: {}`;
- `permissions: contents: write / pull-requests: write`; checkout with `token: ${{ secrets.BOT_PR_TOKEN || github.token }}`; `pip install -c scripts/requirements.txt requests` — only what the module-scope closure needs;
- scrape to `/tmp`, build, `python3 scripts/validate_index.py il/index.html`; a diff step on the whole `il/data/app/` directory writing `changed` to `$GITHUB_OUTPUT`;
- a PR step gated on `changed == 'true'`: a FIXED branch `bot/<county>-county-board-roster-update` (an unmerged PR is refreshed in place by the force-push rather than duplicated), `git add` of the ONE data file (plus `il/history.html` if a history tile counts it), `git push -u origin "$branch" --force`, `gh pr list --head "$branch" --state open` guarding `gh pr create`, `GH_TOKEN` the same expression. The body names both scripts, says the PR changes data about real officeholders, and states what a tripwire failure would mean.

## 7. Register, regenerate, dispatch

One `data_files[]` entry in `metro-worksheet.json` —
`{"file": "<county>-county-board-members.json", "min_keys": N, "note": …}` —
generates BOTH `ROSTER_FILES` in `validate_index.py` and the network-first
`ROSTER_URLS` list in `il/sw.js` (`scripts/generate_metro_files.py`; a
`<tag>/data/app` file in zero or two lists fails). A `workflows[]` entry
`{"file", "purpose", "schedule"}` feeds the metro facts. Then:

```bash
python3 scripts/generate_metro_files.py
python3 scripts/validate_workflow_deps.py
python3 scripts/check_roster_retention.py --base origin/main   # a NEW file is ignored; a reshaped one is not
```

and the steward battery. `scripts/validate_card_links.py` picks up `sourceUrl`
by extraction — a roster's source gets NO row in `scripts/validate_sources.py`
(none of the six newest districted counties has one; that manifest is for
dataset endpoints). `roster-health.yml` discovers the workflow by filename
(everything not in `NOT_A_REFRESH`, `scripts/check_roster_workflow_health.py`)
and reports it NEW until one interval has passed.

**Dispatch the workflow the day it ships and read the log.** A green
`validate_index.py` says nothing about whether the job runs, and the sandbox
is not CI's address.

## 8. NOT RE-READ and carry-forward — the at-large pair only

The commissioners scraper prints a NOT RE-READ line for every
`DOCUMENT_ROSTERS` county naming the document and its age; the builder prints
one for a county the scraper could not read this run and carries its shipped
members forward, refusing the whole write when `MAX_CARRIED_FRACTION` of
counties were carried — a run that carries most of the file is a systemic
block wearing a green tick. A zero parse on a 200 is treated as UNREAD, never
as an empty board. A single-county districted builder has NO carry-forward:
an unreadable page is a red run by design, and `roster-health.yml` is what
gives that red an owner.

## 9. Retention exceptions

`ACCEPTED_DROPS` in `scripts/check_roster_retention.py` is keyed
`"<file>:<field>"` or `"<file>:<group>:<field>"` with a dated reason; the
thresholds (`MIN_PRESENT`, `MIN_ABSOLUTE_DROP`, `RECORD_COLLAPSE_RATIO`) live
beside it. Copy the shape of the entry that exists — it records that the
builder now REFUSES the field, not merely that its absence is tolerated.

## 10. What legitimately varies — and so never belongs here

URLs, markers and regexes; which contact fields ship; every `EXPECT_*` and
`MIN_*` number; the tripwire input (GIS inventory, page composition, none) and
its stated blind spot; subset exceptions; role-join rules; fetch posture
(plain `requests.get`, `scraper_common.fetch`, or a pinned intermediate); the
UA constant; the cron slot; the `-o` default. Wisconsin and Iowa do NOT use the
per-county triple. Wisconsin: a `COUNTIES` entry in
`wi/scripts/wi_county_board_scraper.py`, a robots.txt check
(`wi/scripts/validate_robots.py`), and one
`.github/workflows/update-wi-county-board-roster.yml` re-scraping every
reachable county into one file with `--allow-drop`. Iowa: one state aggregate,
every file and workflow `ia-` prefixed, the board switchboard hoisted to
`boardPhone`, under `docs/IA_EXPANSION_PLAN.md`. Read the instance's
`CLAUDE.md` first.

## 11. Nevers

- Never floor a count the source states exactly; never lower a floor to get a build to write.
- Never invent a field the page does not publish; never add a field the card does not render and call it shipped.
- Never put shapely, pypdf or requests at module scope in a script a workflow runs.
- Never carry a districted county forward; never treat a zero parse as an empty board.
- Never a per-run branch name; never `git add` the whole directory.
- Never change a shipped scraper's UA constant in a shared module.
- Never call a workflow shipped before it has been dispatched and its log read.

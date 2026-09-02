---
name: county-n-plus-1
description: Take ONE county from unserved to in-the-ring, or repair one that is — research its publishers in the right order, settle its board's form from a certified election document, build the roster and (if districted) the geometry by the route the source's shape allows, join the coverage ring, and do the bookkeeping the gates check. Use it the moment a task names a county and something it lacks — "ship Jasper", "add Pope to the ring", "Bureau, anything new?", "Marion's board from the canvasses", "Christian re-precincted, can we build it now", "county N+1 Fayette", "Pierce County board, 17 supervisors", a red FIRST run of a new county's roster workflow — in Illinois, Wisconsin or Iowa — even just to look. It carries the ORDER of the work and the test that settles each decision; the rules live in docs/EXPANSION_GUIDE.md §3.5 and §3.5.1 and this says when to open them. Not for a red bot PR on a shipped county (steward), a new layer (new-layer), a new state (new-state-instance), or "which district is this address in".
---

# One more county

This file exists for the moment an agent starts on a county. `CLAUDE.md`
carries ninety counties of narrative and every gate's name and is loaded on
every turn; `docs/EXPANSION_GUIDE.md` §3.5 is the checklist and §3.5.1 the
thirty-odd rules the counties taught, and both are pointed at below rather than
restated — two documents stating one rule is how `ENGINE_SYNC.md` drifted 164
lines. What neither gives an agent at the moment it starts is the **order**,
the **test that settles each decision**, and the **current names** of the
tables and files the steps hang on. That is what is here.

One correction to carry: §3.5 still writes `data/app/…`. Since R2.3 the
Illinois files live at `il/data/app/`; the root `data/app` does not exist.

## 1. Before touching the world, read your own records

A gap record, a builder docstring and a scraper table can describe one county
three different ways, and when they disagree one of them is a shipped bug. Two
counties' board forms once sat answered in a backlog for a day while their
records went on calling the question undeterminable. So before any fetch:

- `docs/COUNTY_STATUS.md` — the county's row (generated; tier, posture, entries, open gaps).
- `docs/DATA_LAYER_GUIDEBOOK.md` — grep the county's name; its gap record and every dated ask.
- `scripts/il_county_commissioners_scraper.py` — `SITES`, `DOCUMENT_ROSTERS`, `RETURNS_ROSTERS`: is it already known here?
- `scripts/build_metro_outline.py` — the county's `INSIDE` / `OUTSIDE` anchor comments, which are the history of every ring-count change.
- `WATCH.md` — any standing watch on it.
- `docs/ASK_DRAFTS.md` — a drafted or sent ask you would otherwise send twice.

If the record names a blocker, the question is not "is it still blocked" but
"has the METHOD changed" — five counties were shut on split precincts until the
question became "does it publish a VECTOR map", and one shipped that day.

## 2. Research, in this order — each step is cheaper than the next

**Minus one — the clerk's domain, one line.**
`il/data/app/il-county-clerks.json` carries every clerk's e-mail, scraped
weekly from ISBE. `clerk_email.split("@")[-1]` is very often the county's web
domain, correct and maintained by someone else. Try `https://<domain>` and
`https://www.<domain>` before permuting the county's name — nine counties
recorded as having no website had one at exactly this address. A domain with
no A record but a live MX (`<county>.illinois.gov` for Pope, Jasper, Marion) is
a mail-only domain: no site here, not an unreachable clerk.

**Zero — search the web, for the county AND for the artifact.** An ordinary
search-engine query, before any host sweep or catalogue. A county is not a
domain: `.gov` and `.com` can coexist with different content, the clerk may run
a site of their own, the board can have its own subdomain, and the election
authority is a separate publisher on a separate host. Search for
"<county> Illinois county board district map" as well as the county. Read the
strings inside a site's own JavaScript bundle for other hosts it names.
**Verify every hit is the county government** — look for the clerk, board,
sheriff and treasurer — before it goes in any record; results carry same-name
counties in other states and same-name businesses.

**The catalogue query that needs nothing from the county.** An unauthenticated
search of `arcgis.com/sharing/rest/search` for the county's name finds the GIS
org a county's own site never links — Vermilion's 26 services were found this
way while its site could not be read. Then enumerate the ORG behind any viewer
you do find: a viewer shows what it uses; the org shows what the county has
(Douglas: one parcel service in the app config, fifty-four in the org, board
districts and precincts among them).

**Licence before any technical probe.** When a source is gated by anything — a
Referer check, a token, a login, a portal app — find out WHY before how: the
publisher's terms-of-use, data-request and pricing pages. A layer that answers
once a header is set can be the edge of a licence, not hotlink protection.
Sells the data, requires a signed agreement, forbids redistribution → gap kind
`blocked`, ship the county's outline, route the unlock to the clerk. Ask for
written permission BEFORE signing or paying; a purchased raw file stays out of
`il/data/source/raw/` with its size and sha256 recorded (Jo Daviess is the
pattern). The inverse holds too: an `All rights reserved` string in
`licenseInfo` may be a REQUIRED NOTICE — find the portal's own terms page
before recording a refusal, and if the terms impose a condition, satisfy it on
the card.

**Classify reachability from the vantage that matters.**
- `python3 scripts/probe_incomplete_tls_chains.py --clerk-domains` (or with hosts) — a leaf served without its intermediate reads to every automated client as a dead host and to every browser as fine. Coles, Gallatin, Knox's GIS. The remedy is the intermediate fetched by AIA with a PINNED hash (`scripts/coles_county_board_scraper.py`), never verification off.
- `openssl s_client -connect <host>:443 -showcerts | grep -c 'BEGIN CERTIFICATE'` against a control host that sends three: two is an incomplete chain, not a refusal.
- HTTP 202 is never a document — it is what a captcha front returns. A captcha is an access control, not an obstacle to route around.
- A blocked WEBSITE is not a blocked COUNTY. Knox had four hosts; Johnson and Perry shipped with their sites never read, from their election authority's results vendor.
- A block seen from this sandbox is a fact about this address. The scrapers' vantage is CI: dispatch the workflow on your branch and sample several runs before recording a block as terminal.

**The ask is a rung, not a last resort.** `docs/ASK_DRAFTS.md` holds the
protocol and the drafts. Nothing there is sent by the agent that wrote it;
record the send date the day it goes, follow up at ~3 weeks and again ~2 weeks
later, and only then record UNRESPONSIVE — which is a different claim from "no
source exists". A follow-up is a recovery mechanism: Clay's clerk answered the
question that unblocked the build on the third attempt, after her spam folder
ate two. A clean, citable NO is a good outcome; say so in the ask.

Never write "the county publishes no X" — into a record, and above all to the
person who maintains the source — without having searched.

## 3. Settle the board's form from a certified election document

Districted or at-large is decided by a canvass, a results page or a specimen
ballot — never by a board page's silence. A countywide contest
(`COUNTY BOARD - AT LARGE`, `CWD`, `COUNTY BOARD MEMBER (VOTE FOR) N`) counted
in ALL of the county's precincts proves at-large; district-suffixed contests
counted in subsets prove districted. Record WHICH document proved it, in the
scraper's table or the builder's docstring. This decision routes everything
below, and it caught a stale state record once: ISBE's 2007 structure table
calls Union districted while Union's own returns count every seat in 20 of 20
precincts.

The results vendors and which counties each carries are a TABLE in
`docs/DATA_LAYER_GUIDEBOOK.md` (grep `pollresults`). Test carriage by CONTENT,
never by a vendor's landing page, and sweep several election slugs before
recording that a vendor lacks a county — carriage is per election. A wrong
download-handler pair returns the vendor's login page as a 200 PDF: check for
`%PDF` and the canvass's own title.

## 4. The build, by the route the source's shape allows

**At-large.** The board rides the County card with no dispatch entry, no
toggle, no coverage function and no new fetch. Add a `SITES` entry and parser
to `scripts/il_county_commissioners_scraper.py` — or a `DOCUMENT_ROSTERS` row
(a document the clerk sent) or `RETURNS_ROSTERS` row (certified winners, each
row naming its election) when the county's page cannot be read — and a seat
count to `EXPECT_MEMBERS` in `scripts/build_county_commissioners.py`. The
county lands in `il/data/app/il-county-commissioners.json`, keyed UPPERCASE
exactly as `il-county-clerks.json` is. It STILL needs its outline and INSIDE
anchor (§5 below), goes in `METRO_COUNTY_FIPS` and NOT `DISPATCH_COUNTY_FIPS`,
and its precinct card must carry no board-district row. A roster the county
publishes short of its seats ships with `seats` beside the members, so the
card can say a seat is unlisted rather than concealing it.

**Districted, with a published boundary layer.** Before choosing the
no-scraper "roster rides the layer" shape, spend one fetch comparing the
layer's name columns against the county's own board page. Two mechanical
staleness tells: the item's `created` / `modified` timestamps, and a
`Population` column that sums to the PREVIOUS decennial against TIGERweb
`POP100`. Stale → geometry from the service, people from the page (Coles: six
of twelve names wrong on the layer). Several district layers on offer →
balance each on the Census 2020 blocks; the plan in force is the one that
balances, whatever it is called (Vermilion's well-labelled layer was the 2011
plan), and the builder gates that comparison in BOTH directions.

**Districted, no map, districts are whole precincts — the canvass route**
(§3.5.1's whole-precinct entry numbers the steps, from results archive to the weekly composition check). Find the election
authority's results archive; read the board contests; take a second witness of
a DIFFERENT kind (a second certified election, a precinct count, a population
sum — arithmetic beats another map); run THE JASPER TEST in
`scripts/vtd_board_districts.py` before any dissolve — the Census 2020 voting
districts must match the county's CURRENT precinct names one for one and sum
to its exact population, and failing is the correct outcome for a county that
re-precincted. Walk GENERALS newest-first; primaries never seat anybody. Read
precinct names from a canvass's contest list, never from a polling notice's
headings (those group buildings, not precincts).

**Districted, composition published on the page the roster is scraped from.**
The scraper emits the composition it read; the ROSTER builder compares it to
the table compiled into the boundary builder and FAILS on any difference, so
the weekly job turns red on a redistricting. Compare at precinct level, not
township names. Write the negative tests (a unit lost, gained, renamed).

**Districted, and the districts split precincts.** The census fabric cannot
draw it. Three things have: two county-published LAYERS that compose each
other though neither is labelled with the other (Richland — overlay them);
the county's own polygons as drawn, found by enumerating its org (Douglas);
and a VECTOR PDF whose districts are filled path objects — read the objects,
never the pixels (Jackson). A genuine raster scan is still shut, and a
clerk's written sentence can draw one line (Clay's corporate-limits split).

**The population ceiling.** The dissolve guard's worst-deviation ceiling is
30%. A board whose districts elect different numbers of members balances PER
MEMBER — get seats per district from the county's roster page before writing
the check. The ceiling is raised for ONE county, on that county's own written
confirmation that the plan is current, with the measured value recorded rather
than smoothed (Wayne 32.4%, Clay 39.8%). Never widened for the fleet.

**Roster rules that apply everywhere.** Match names across surfaces on
surname plus first initial and require the match UNIQUE, dropping ambiguous
keys. A party letter ships; a bare year does not; a HOME ADDRESS is never
collected, and if any row is marked a secured address, the residence-derived
columns — town included — drop for the whole roster. A nameless seat is a
VACANCY: count seats against the floor, attach `vacancies`, never lower the
floor and never drop the row. Two surfaces naming different people for a
seat: decide which surface wins BEFORE looking at the numbers, record
`districtSource` and the other claim, and never let a count guard launder a
disagreement — WITHHOLD, do not prefer. Before a PDF scraper, run
`pdfimages -list`: a scan with a garbage text layer parses cleanly. A
fetchable-but-not-machine-readable roster is hand-transcribed and gets a
WATCHER (`scripts/mason_roster_watch.py`), not a scraper.

## 5. The coverage ring

A county joins when its BOARD or its PRECINCTS answer — a fire, park, library
or drainage tiling alone never qualifies, and a county never joins for a rich
statewide answer. In `scripts/build_metro_outline.py`, in ONE step: the slug →
FIPS row in `DISPATCH_COUNTY_FIPS` (only if the county registers a dispatch
entry — an at-large county belongs in `METRO_COUNTY_FIPS` alone, and
`validate_index.py` check 8 fails in BOTH directions), the FIPS in
`METRO_COUNTY_FIPS`, an INSIDE anchor, and its removal from OUTSIDE if listed.
Then:

```bash
python3 scripts/build_metro_outline.py            # rebuild the dissolve
python3 scripts/build_metro_outline.py --check    # READ THE RING COUNT FROM THIS
```

Read the ring count from `--check`, never from a map in your head — the
enclave predictions were wrong twice in one day. A county with no unserved
neighbour is an enclave only if it is INTERIOR; one that fronts the state line
is a notch. A new hole needs its own OUTSIDE anchor inside it; an island
follows the **First-island checklist** entry in §3.5.1 (CLAUDE.md still cites it
as §2.5.1, from before the guide's 2026-08-27 rewrite). A frontier county you cannot
serve but have recorded a gap for still ships `<slug>-county-outline.json`
with the worksheet entry marked `dynamic_reference: true` and NOTHING in
`DISPATCH_COUNTY_FIPS`; derive its anchors from TIGERweb place centroids and
round-trip each through a point-in-county query rather than recalling
coordinates.

## 6. The other concepts — §3.5's numbered steps, one line each

- `judicial-subcircuit`: an entry only if the circuit has PA 102-0693 subcircuits; otherwise record "structurally n/a" (Kendall), never silence.
- `fire-district` / `park-district` / `library-district`: one `polygonCountyEntry` per tiling the county publishes; municipal rows only where the county records that class COMPLETELY (municipal fire rows never); each absent tiling is a gap.
- `county-precinct`: keyed to the county's ELECTION AUTHORITY; polling places joined where published (Kendall's GlobalID join); carve out any municipal election commission the county contains.
- `tif-district`: an entry where the county publishes a tiling.
- Municipal officials: the county's rung of §3.4's ladder, keyed by place GEOID; suburban ward polygons join the consolidated `ward` layer and `scripts/build_municipal_ward_coverage.py` is rerun.
- County officers: the clerk row is automatic (ISBE, weekly); further officers per §3.3 rule 4, in the same change.
- Statewide layers: nothing to do.
- The layer count is unchanged. If any step wants a new toggle, stop and run §1.6's five questions — that is the new-layer skill's territory.

## 7. Each new roster is a scraper, a builder and a workflow

The mechanics — file names, the two schemas, the exact-count guard ladder,
the drift-check-first ordering, the workflow's five load-bearing lines, the
worksheet registration that feeds `validate_index.py` and `sw.js` together —
are the **roster-pipeline** skill's; Richland, Wayne and Clay are its three
complete reference triples. Two things county work adds on top:

- **grep the cloned workflow for the OLD county's name and domain** — its PR title and body are a human-review surface;
- **dispatch every new workflow the day it ships and read the log.** A green `validate_index.py` says nothing about whether the job runs; heavy imports go function-local, and `scripts/validate_workflow_deps.py` is what caught the five roster jobs that were dead from the day they shipped.

Officeholder sourcing is settled in the SAME change that ships the boundary,
never deferred (§3.3).

## 8. Record, then bookkeep, then run the battery

Write the finding where the next reader will look — the gap record, the
builder's docstring, or a `WATCH.md` row — never only the guidebook backlog. A
gap record's reader fields (`summary` / `why` / `wanted`, each ≤240 chars) name
the COUNTIES it affects; the unbounded `blocker` field holds every host, date
and status; `kind` is one of `KINDS` in `scripts/build_coverage_gaps.py`
(`no-source` / `blocked` / `data-quality`). Record the blocker you MEASURED, in
its vocabulary — unresponsive, licence-gated, split-precinct, raster-only are
different claims with different routes out; "no source exists" is almost never
one of them. When a build disproves its own record, rewriting the record is
part of the build.

Then, in order:

```bash
python3 scripts/generate_metro_files.py          # worksheet entries → generated regions
python3 scripts/build_coverage_gaps.py           # the gap block → il/data/app/coverage-gaps.json
python3 scripts/build_county_status.py           # docs/COUNTY_STATUS.md; its --check fails a lagging table
```

plus the guidebook's coverage-map, inventory and matrix rows, the smoke
ground truth if the county adds an anchor, and then the whole steward battery
(`.claude/skills/steward/SKILL.md` §1) before the push.

## 9. Wisconsin and Iowa

The ladder in §2–§3 is the same in every state; the files are not. Read the
instance's `CLAUDE.md` (`wi/CLAUDE.md`, `ia/CLAUDE.md`) and its `scripts/`
before assuming the Illinois shape — Wisconsin's boards are supervisory
districts read by `wi/scripts/wi_county_board_scraper.py`; Iowa's officers
come from ISAC's member portal plus one statewide directory per office, which
can disagree, and `DIVERGENCE_RESOLVED` in `ia/scripts/build_ia_county_officers.py`
is the pin table that withholds a name until a third witness settles it; both
instances carry their own worksheets and gap blocks (`--metro wisconsin` / `--metro iowa` on `build_coverage_gaps.py`).
Part 5 of the guide is the cross-state statement of these rules; §3.5.1 is
their Illinois-worded original.

## 10. Nevers specific to county work

- Never decide a board's form from a board page's silence, or from a state table older than the county's own returns.
- Never write "publishes no X" without having searched, and never to the source's maintainer.
- Never lower a count floor, a field floor or the deviation ceiling to get a build to write. A refusal to write is the builder working.
- Never name an officeholder two publishers disagree on. Withhold and say who names whom.
- Never collect a home address; never mirror a private location the source printed by mistake.
- Never ship a traced raster, a colour-sampled fill, or a dissolve that failed the Jasper test.
- Never disable TLS verification to reach a host; supply the intermediate and pin it.
- Never join a county for a statewide answer, and never let a city carry its unserved county.
- Never predict the ring count. Run `--check`.

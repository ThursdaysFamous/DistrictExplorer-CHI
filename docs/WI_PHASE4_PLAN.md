# districtry Wisconsin — Deployment Phase 4 (the officeholders phase + the second city tier)

Status: **IN PROGRESS** — every source below was fetched and measured on
2026-08-26 (the appendix is the ledger). PR 1 is DELIVERED (2026-08-26, with
its 1b follow-up the same day); PR 2 was slotted next by the operator after
1b's measurement showed what per-county pages are worth. Phases 1–3 are
delivered: 29 layers as of 2026-08-26, the phase-3 backlog fully cleared
(`docs/DATA_LAYER_GUIDEBOOK.md`).
Phase 4 is smaller than its predecessors by design: the cheap boundary wins are
taken, so this phase spends its effort where Wisconsin still says nothing —
**who holds the county offices**, **where you vote**, and **the second city
tier** — plus the one standing measurement the record owes.

## What phase 4 deliberately is not

The concept matrix's remaining Wisconsin cells are measured no's, and this
phase does not reopen them: town boards (1,200+ towns, no statewide roster —
the towns' association publishes none this project can read), municipal heads
statewide (no statewide source; the per-county clerk-directory route verified
for Dane/Brown/Waukesha in phase 2 is real but is phase-5 *scale* — an IL
`municipal-officials`-class system, not a phase-4 PR), MPS attendance zones
(MPS is a choice-based system; the city publishes school POINTS, no zone
geometry — school-site already answers proximity), MMSD (appointed board,
SEWRPC-copyright boundary), sanitary/lake districts (elected, zero statewide
geometry — measured), and the Wisconsin Supreme Court (seven justices elected
STATEWIDE — an at-large body has no polygon, and the fleet ships no statewide
office card; recorded, not built).

---

## PR 1 — County officers on the county card (no new layer) — DELIVERED 2026-08-26

Shipped as planned (#543), plus a same-day **1b follow-up** the first
measurement forced: the board chair is the one officer who is also a
supervisor, and cross-checking the shipped file against the weekly
`county-board-members.json` found SIX of the 22 roster counties visibly past
the book's April 2025 snapshot — three rotated chairs (Bayfield, Dunn, Polk),
two chairs off their boards entirely (Portage, Winnebago), one changed
surname (Milwaukee). The builder now reconciles per county: a chair the
county's own page marks supersedes the book's (the clerk precedent — the
fresher county source wins, said on the card), a book chair absent from a
complete roster is WITHHELD with the reason stated, and both the Thursday
board workflow and the Friday clerk workflow rebuild the officers file so
the decision ships the same week it moves.

The county card names the clerk today. The same Blue Book PDF the clerk
scraper already parses (`210_officials_and_employees.pdf`, cached) carries
TWO MORE county-officer tables, measured page by page:

- p19: **board chair** (with the county's supervisor count in parens),
  **executive / administrator / administrative coordinator** (typed `CE` /
  `CA` / `AC`), **treasurer** (party).
- p22–23: **district attorney** (party), **sheriff** (party),
  **coroner / medical examiner** (`ME` marks the appointed-examiner
  counties).

Extend `wi_county_clerk_scraper.py`'s `parse_blue_book` to the two tables
(same longest-prefix county matching, same mid-page-start and joined-column
traps) and the county card gains the officer rows. The honesty machinery:

1. **The executive-type code decides the label.** `CE` is an ELECTED county
   executive; `CA`/`AC` are APPOINTED administrators — the card labels
   appointed roles exactly as the clerk build labels appointed clerks.
2. **The chair column carries its own witness**: its "(# of supervisors)"
   must equal the seat count `county-board-directory.json` already reads
   back from the shipped geometry — a real cross-gate for that column,
   gated in the builder.
3. **The Shawano–Menominee DA is one office**, and the Blue Book says so
   itself: both rows are footnoted and name the same person (Gregory
   Parker, measured). Encode the pair; both county cards state the shared
   prosecutorial unit (Wis. Stat. ch. 978).
4. **No second publisher exists for these offices, so the rows ship
   DATED.** Measured: badgersheriffs.com is unreachable from this client
   (bare domain 502 via proxy, www has no DNS — ONE CI-side probe owed
   before recording it permanently), the DA association is member-gated,
   the treasurers' association is unreachable, and DOJ's DA page is
   SharePoint-JS with no content in the HTML (its JSON API is worth one
   probe). Until a second source proves out, every non-clerk officer row
   renders with its source date — "per the Wisconsin Blue Book, April
   2025" — rather than implying a weekly-verified currency the data does
   not have. The clerk rows keep their two-source freshness untouched.
5. Cadence: the Blue Book revises per biennium; the existing clerk workflow
   re-reads it weekly anyway (cheap, already scheduled) and the biennium
   URL bump already sits in WATCH.md.

Bookkeeping: county `source.people` extended; retention gate auto-protects
the new fields; no rank/floor/cache changes beyond the roster file.

**Recommendation folded in**: the DA rides the county card, NOT a new
71-unit layer — the units are county-tiled except one merge, and two card
sentences carry that merge more honestly than a near-duplicate county layer
draws it. (NYC's `district-attorney` layer exists because boroughs ≠ its
other tilings; Wisconsin's units ARE the county fabric minus one seam.)

## PR 2 — The county-by-county officer scrape (NEXT: contact + currency, the attrition route)

The officer rows ship dated and contact-free because no STATEWIDE second
publisher measures open — but that is a fact about aggregators, not about
the 72 counties, and 1b just proved what a county's own page is worth: it
is both the fresher NAME witness and the only source of office contact.
This step works the same attrition model as the county-board roster (22
counties and counting, each page shape pinned, per-county floors, weekly
CI): a per-county scrape of each county's own officer/department pages —
sheriff, DA, treasurer, clerk of circuit court, register of deeds,
executive, coroner/ME — shipping counties as they prove out and
gap-recording the rest.

What a scraped county gains, in order of value:

1. **Contact on the officer rows** — office phone, address, and the
   office's own page link (the card convention's missing half; today the
   reader is handed the county website and left to navigate).
2. **A per-county currency upgrade**: a county page naming its sheriff is
   a second witness for that NAME, so the row's "As of" can state the
   county's own page beside the book for scraped counties — the dated
   caveat narrows county by county instead of all at once.
3. **Divergences surface weekly** — a county page naming a DIFFERENT
   person than the book is the chair-reconciliation case generalized:
   print it, ship the county's name, withhold the book's party code
   (the clerk rule), never smooth it.

Order of attack, from what is already measured: the 22 board-roster
counties are proven-readable sites with pinned shapes — extend those
scrapers' reach to the officer pages first; then the phase-2 clerk-directory
counties (Dane/Brown/Waukesha measured); then the frontier, county by
county, recording each refusal (the EXPECTED_UNREACHABLE hosts — Rock's
LAN-only portal, the Cloudflare-fronted counties — are known no's going
in). Floors per county per office; a county ships only what its own page
publishes; nothing is invented for the counties that publish nothing —
they keep the dated Blue Book row and join the standing gap record.
Scale honestly stated: this is the largest roster effort the instance has
taken on (up to 72 sites × 7 offices), so it lands in TRANCHES — each
tranche a reviewed PR with its own measured ledger, the board-roster
precedent exactly.

## PR 3 — Milwaukee polling places on the ward card (city-scoped enrichment)

The `ward-polling-places` gap records the statewide block (WEC Cloudflare)
and names the city-scoped opening. Measured: Milwaukee's `voting-wards`
CKAN dataset (CC-BY) publishes the pairing THREE ways — a "Voting wards and
polling places" CSV, Ward + PollingPlace shapefiles, and two live REST
layers (`election/election_wards` 0 = polling-place points, 1 = wards). A
pre-built `data/app/mke-polling-places.json` pairs ward → polling place
(name + address + point), witnessed across the surfaces (the CSV pairing
must agree with the shapefile/REST attributes; ward keys must match the
LTSB ward layer's Milwaukee wards). The WARD card gains a "Polling place"
row inside Milwaukee only (the ward module already knows the selected
ward; the enrichment is coverage-scoped exactly like the city tier).
The gap record narrows to "statewide minus Milwaukee" rather than closing.
Election-cycle churn: polling places move per election — WATCH.md row, and
the card states the pairing's edition.

## PR 4 — The Madison city tier (tid-district's second city + neighborhood associations)

Measured on the city's own server (maps.cityofmadison.com, catalogued in
its open-data portal):

- **TIF Districts** (OPEN_DATA_PLANNING/8): 25, with `TIF_NO`, `TIF_NAME`,
  `TIF_STATUS`, creation/expiration dates — the Milwaukee STATUS lesson
  repeats: filter on the city's own status field, never dates alone.
  `tid-district` becomes a two-city layer: per-city entries, coverage = OR
  of the two city tests, each entry keeping its own builder witness.
  Wisconsin's DOR-tabular statewide reading stands; cities join one at a
  time exactly as counties join concepts in IL.
- **Neighborhood Associations** (OPEN_DATA/12): 141 city-REGISTERED
  association boundaries. Madison's official neighborhood fabric IS its
  registered associations, and the layer ships under that honest name —
  "Neighborhood Association", never "Neighborhood" — beside Milwaukee's
  official neighborhoods (which stay their own layer; different concepts
  are not merged for tidiness).
- Step zero for both: the licence/terms check on the city's open-data
  program (the portal catalogues these as open data; capture the terms
  text for the source block, the DPI-licence precedent), and a
  `madisonCoverage` test built from the city's corporate-limit layer.

## PR 5 — The WEC Playwright-from-CI attempt (a measurement, not a layer)

The standing follow-up phase 2 recorded and three gap records wait on: one
CPD-style Playwright challenge attempt against elections.wi.gov / MyVote
FROM GITHUB ACTIONS (this sandbox's Chromium has no egress — the block is
recorded as measured-from-here, not permanent, until CI tries once). A
one-shot workflow, run manually, with both outcomes wired: success unlocks
the statewide polling-place, early-voting and municipal-clerk bulk files
(each becomes its own follow-up build); refusal files the block PERMANENT —
EXPECTED_UNREACHABLE entries, the `ward-polling-places` blocker rewritten
from "one attempt owed" to "attempted from CI on <date>, refused", and the
ask ledger takes over. Either way a three-week-old "owed" comes off the
books.

## PR 6 (stretch) — Technical college districts, identity-only

DPI's own org publishes "Technical College Districts, Wisconsin" (measured
present; same org and licence posture as the shipped school-site/library
builds). Sixteen districts, boards APPOINTED (Leg. Council, phase-2
appendix) — so if it ships, it ships as an identity + labeled-appointed
card (the WTCS district your point funds through its property tax), never
with invented officeholders. Honest but low-reader-value: proposed as the
phase's stretch item, cut first.

---

## Order and scope calls

Recommended order: PR 1 (delivered), PR 2 in tranches (slotted next by the
operator, 2026-08-26), PR 3, PR 5 (its outcome may spawn follow-ups), PR 4,
PR 6 if wanted. Three calls are made
above rather than left open — DA on the county card (not a layer), dated
Blue Book-only officer rows (not waiting for second sources that measure
closed), Madison associations under their honest name — each reversible if
the operator prefers otherwise.

## Verification (per PR, the standing battery)

`generate_metro_files` + `--check` · `compose_app --check` ·
`validate_index` · `build_coverage_gaps --check` (+ regenerate on gap
edits) · privacy/landing/manifests/dark-palette checks ·
`validate_sources --offline` + new PROVENANCE/ENDPOINTS rows ·
`check_roster_retention --base origin/main` · builder gates proven by a
real run · browser probes per new surface · the full WI smoke test.

---

## Appendix — measured source ledger (all fetched 2026-08-26)

**Blue Book 210 (cached PDF, 25pp)**: p17–18 clerks (shipped); p19 "county
board chair; executive (or alternative); treasurer" — chair carries "(# of
supervisors)", executive typed CE/CA/AC; p22–23 "district attorney;
sheriff; coroner (or alternative)" — parties per name, ME marks medical
examiners, Menominee¹/Shawano¹ footnoted sharing DA Gregory Parker (R).
**Second-source probes**: badgersheriffs.com — proxy CONNECT 502 bare, no
DNS on www (CI probe owed); wdaa.org — 200, member-gated (MemberClicks);
wicountytreasurers.org — unreachable; doj.state.wi.us — 200 but the
district-attorneys page is SharePoint with JS-rendered content (JSON API
unprobed).
**Milwaukee voting-wards (CKAN, CC-BY)**: CSV "Voting wards and polling
places" + Ward SHP + PollingPlace SHP + REST `election/election_wards`
layers 0 (polling places) and 1 (wards).
**Madison (maps.cityofmadison.com via its open-data portal)**: TIF
Districts OPEN_DATA_PLANNING/8 — 25 rows, TIF_NO/TIF_NAME/TIF_STATUS/
CREATION_DATE/EXPIRATION_DATE; Neighborhood Associations OPEN_DATA/12 —
141 rows. Licence text capture is each build's step zero.
**MPS attendance zones**: `AGO/MPS_School_Districts` layer 0 is school
POINTS (name/type/grades/phone/address), not zones — no zone geometry
published; honest no.
**WTCS**: Wisconsin_DPI org publishes "Technical College Districts,
Wisconsin" (feature service, present; boards appointed per the phase-2
Leg. Council citation).
**Statute anchor**: Wis. Stat. ch. 978 (prosecutorial units; 978.01 —
docs.legis chapter page lazy-loads, cite section URLs, the 753.06 lesson).

# Expansion Guide — the primary deployment guide for all future expansion

Status: **live — the single entry point for growing District Explorer.** Owner: CHI
(reference implementation; forks carry a pointer stub).
Consolidated 2026-07-27 from five docs — `METRO_EXPANSION_PLAYBOOK.md`,
`STATEWIDE_EXPANSION_PLAYBOOK.md`, `COUNTY_LAYER_CONSOLIDATION.md`,
`MUNICIPAL_COUNCILS_PLAYBOOK.md`, `ILLINOIS_LAYER_STANDARDIZATION.md` — whose full original
texts are preserved verbatim under `docs/archive/` (pointer stubs remain at the old paths so
existing references resolve). Live companions that deliberately stay separate: Appendix B.

---

## 0. Orientation

### 0.1 The four expansion paths

| Path | You are… | Part |
|---|---|---|
| **A — New Illinois county** | adding a county to this app's deep coverage (board, subcircuit, fire/park/library, precincts, municipal officials) | Part 2 |
| **B — Statewide Illinois** | widening this app's shell/brand toward all 102 counties | Part 3 |
| **C — New metro fork** | porting the app to another city (a separate repo + site) | Part 4 |
| **D — New concept/layer** | adding a layer idea to any existing deployment | Part 5 |

Every path rides the same machinery — worksheet/generated regions, scraper→builder→PR
pipelines, gates, engine releases — documented once in **Part 6**.

### 0.2 The standing invariants (every path, non-negotiable)

1. **Honesty rules.** Officeholder data is never guessed; no verifiable source → the card
   links the official body and the gap is recorded. Honesty is **per-field** (a source that
   verifies names may not publish party/contact — store `null`, render "not published",
   never backfill from a weaker source). External strings always render through
   `sanitize()`/`textContent`. Never draw a boundary no agency publishes; never snap a
   no-match to the nearest polygon; appointed officials are labeled, never presented as
   elected.
2. **The expansion invariant** (Part 1): expanding coverage changes **which dispatch
   entries and roster rows exist — never which layers exist.** A new toggle is justified
   only by a governance function no current concept covers, and it launches consolidated.
3. **The at-large rule**: a body elected by the whole unit adds zero point-discrimination —
   it rides the unit's identity card, never a polygon layer.
4. **Officeholder sourcing ships with the boundary** (rule 4, Part 2.3) — decided and
   BUILT in the same change, never deferred.
5. **Engine parity.** Code inside `ENGINE:BEGIN/END` fences is byte-identical across forks
   and changes only via the release pipeline (`docs/ENGINE_SYNC.md`). Never inline a
   city value in a fence — add a `METRO:BEGIN config` variable.
6. **Gates green before merge** (Part 6.5) — and roster changes always land as
   human-reviewed PRs, never direct commits to `main`.

### 0.3 Working style

Build in small, cheap, focused threads; paste only this guide's relevant contract/tables +
the one module being worked on — never the whole app. Locate code by **grep anchor** (a
symbol or distinctive substring), never by line number (line-number anchors went stale
within weeks the one time they were tried). End every thread with handoff lines:
`[module] DONE — exposes contract, tested against <point>` · `[module] STUB — <what's
faked>` · `[module] SURPRISE — <any dataset quirk found>`.

---

# PART 1 — Doctrine: the governance taxonomy

The audit behind this Part classified all 39 shipped layers (2026-07-27, Appendix A) by
**purpose, level of governance, function within governance, and election geometry**, so
expansion reuses concepts instead of multiplying them. Chicago is not a special case — it
is the **reference instance** of each concept (`ward` = districted municipal council;
`ward-precinct` = municipal-election-authority precinct; CPS zones = one district's
attendance boundaries). Where Chicago has a concept nobody else has, that is recorded, not
generalized; where others have the same concept in a different *shape*, the axes below
absorb the difference.

## 1.1 The axes

**Level:** Federal · State (incl. elected judiciary) · County · Township · Municipal ·
School district · Special-purpose district · Election administration · Reference/amenity.

**Function:** representation (a seat on a body) · whole-unit office (mayor, clerk) ·
service/taxing jurisdiction (fire/park/library/TIF) · service assignment (attendance zone,
police beat, polling place) · election administration · reference.

Out of scope by standing decision: **party offices** (precinct committeeperson,
ward/township committeeman) — the fleet's "recommend never" class.

## 1.2 Election geometry — the axis that decides surfacing

| Election geometry | Surfacing rule | Shipped precedents |
|---|---|---|
| **DISTRICTED** — seats elected by sub-geography | polygon concept layer; card names *your* representative | `ward`, `county-board`, `school-board`, `judicial-subcircuit`, `ccbr` |
| **AT-LARGE** — whole-unit electorate | roster rows on the unit's **identity card**; never a polygon | mayor + trustees on `municipality`; clerk on `county`; MWRD's nine at-large commissioners = link row |
| **APPOINTED** | labeled rows/links only | CPS network chiefs; NYC community-board chair |
| **NONE / ADMINISTRATIVE** | identity + honest links | precincts, ZIP, TIF, attendance zones |

This is the answer to "Chicago elects its council by ward; Elmhurst elects at-large": same
concept, different election geometry, zero new layers. Worked example:

| Place | Head of government | Governing body | Surface |
|---|---|---|---|
| Chicago | Mayor + City Clerk + City Treasurer on the `municipality` card (SHIPPED 2026-07-28) | 50 alderpersons by ward | body: `ward` layer; head + citywide officers: `municipality` card, whose council section points at the ward layer rather than listing 50 seats |
| Berwyn (Cook) | Mayor on `municipality` card | full ward-badged council on the card; *your* alderperson from the consolidated `ward` layer (SHIPPED 2026-07, §2.4) | Pattern A card + Pattern B polygon, both live |
| Alsip (Cook) | Village President on card | 6 at-large trustees on card | identity card only — correctly no polygon |

## 1.3 Sourcing dimension ≠ dispatch dimension

- **Dispatch by county** — disjoint county footprints, one concept toggle
  (`registerCountyLayer`): `county-board`, `judicial-subcircuit`, `fire-district`,
  `park-district`, `library-district`, `county-precinct`.
- **Dispatch by municipality** — two shipped shapes: the `municipality` card's roster
  join (one statewide tiling, county-*sourced* rosters keyed by place GEOID), and the
  consolidated `ward` layer's dispatch table keyed by municipality (the dispatcher's
  first non-county key — `opts.entries`; Chicago + suburban Cook + Evanston + Will
  cities + Aurora), whose suburban seat-holders join `municipal-officials.json` by
  municipality + seat number so the ward card can never name someone different from
  the Municipality card's list.
- **Dispatch by election authority** — Illinois voting is run by ~108 authorities: 101
  county clerks (scraped weekly from ISBE for the `county` card), a few municipal boards
  of election commissioners (Chicago's is one), Peoria's appointed commission.
  `ward-precinct` (Chicago BOE) vs `county-precinct` (clerks) is this dimension in
  production; a future municipal-commission city (Rockford/Bloomington class) joins as an
  authority entry, coverage-carved out of its county exactly as `suburbanCookCoverage`
  carves Chicago out of Cook. `early-voting` generalizes the same way (per-authority site
  files, hand-curated per election).
- **No dispatch** — one statewide source: the TIGERweb identity layers, the chamber
  layers, `zip-code`.

## 1.4 The three surfacing patterns

- **Pattern A — identity layer + whole-unit officers on its card** (`county` + clerk;
  `municipality` + mayor/board/officers; `township` — officers are a recorded candidate).
- **Pattern B — districted-body concept layer**, dispatched per source (`ward`,
  `county-board`, `school-board`, `judicial-subcircuit`, `ccbr`, the service/taxing
  district layers).
- **Pattern C — nearest-N amenity** (`police-station`, `fire-station`, `post-office`,
  `library`, `school-site`, `early-voting`) — honest straight-line proximity, N small.

## 1.5 Standing rules earned by the audit

- **Commission-county boards** (17 downstate counties elect 3 commissioners county-wide;
  some township counties elect boards at-large): at-large → `county`-card roster rows, no
  polygon, no toggle change. Decide districted-vs-at-large per county at expansion.
- **School governance:** every IL district board except Chicago's ERSB is elected
  whole-district → Pattern A enrichment on the `school-district-*` cards; attendance zones
  are per-district opt-ins; a new county changes nothing in the schools group.
- **Complete-tiling rule** for special-district layers: municipal service rows belong in a
  county's tiling only where it records that municipal class **completely** (Kendall
  library funds kept; McHenry's lone Crystal Lake row excluded; municipal fire rows always
  excluded — a municipal fire department is the municipality). A partial inclusion lies by
  omission.
- **Single-county conversion triggers:** a dedicated layer converts to a dispatched
  concept when its second county ships — `tif-district` → Kendall's `TIF_Districts`
  service; `mwrd` → a `sanitary-district` concept if a second county's sanitary tiling
  ships (the MWRD *body* is unique; the *class* isn't — Cook's Clerk catalog carries an
  unwired Sanitary tiling L12). `dupage-county-special-police` has no analog sighted.
- **Whole-unit officer rosters recur** and often share sources: county officers beyond the
  clerk (per county, rule 4), township officers (the same clerk yearbooks as the municipal
  scrape — capture both sections in one pass; verify depth at build time; TOI link floor).
- **"Who polices this point"** generalizes as card rows (municipal PD candidate row +
  Sheriff among county officers) + the metro-wide `police-station` layer — never invented
  geography. `ccpsa-district-council` stays Chicago-unique.
- Cheap statewide judicial notes: the five **Appellate Districts** share the Supreme Court
  map (a card row, never a layer); the elected **ROE regional superintendent** is a
  DERIVE-class candidate (verify the Cook/Chicago carve-outs); the statewide
  `judicial-circuit` DERIVE stays blocked (no authoritative machine-readable
  county→circuit source — never hand-encode).

Recorded candidates from the audit live in `docs/DATA_LAYER_GUIDEBOOK.md`'s backlog
(the "Governance-standardization pass" entry).

## 1.6 The new-concept test (gatekeeper for every proposal)

1. Which level + function (§1.1)? Duplicates an existing concept at that level → it is a
   dispatch entry or card row there, full stop.
2. Which election geometry (§1.2)? Districted → consolidated concept layer. At-large →
   identity-card rows. Appointed → labeled links. Party office → out of scope.
3. Which dispatch dimension (§1.3)?
4. Officeholder story in the same change (rule 4); honesty floor = link, gap recorded.
5. Guidebook row + Appendix A classification updated in the same change.

---

# PART 2 — Path A: a new Illinois county

**Decided architecture: one layer per concept, holding a per-county dispatch table**
(fork-level `registerCountyLayer` — no engine change; grep it in `index.html`). The
per-county layers of one concept are mutually exclusive by construction, so per-county
toggles buy nothing and scale hostilely (7 counties × 5 concepts ≈ 35 toggles vs 5;
statewide would be impossible). Consolidation is **UI-level, not source-level** — there is
no statewide GIS for boards/fire/park/precincts, so each county keeps its own loader,
query, and card; one layer dispatches among them. **Adding a county is adding table
entries, not layers.**

## 2.1 Dispatcher semantics (decided, shipped)

- **Coverage = OR of the entries' coverages**, checked in table order (cached same-origin
  outline tests). Outside every sourced county the layer hides; a throwing check falls
  through; an all-throwing miss propagates so the engine's fail-open applies.
- **Query dispatches by containment, not coverage**: try each county's own geometry in
  order; first containment hit wins (they cannot overlap). A downed county is skipped
  while others resolve; if no county matched and one errored, the error propagates — a
  point in the downed county gets the honest error card + Retry, never a lying "No
  result".
- **Overlay = union** of sourced counties' boundaries, each feature wrapped (not mutated —
  caches are shared) and stamped `dxCounty` for hover dispatch. A county failing at load
  drops out of the union while others draw (known tradeoff: the engine caches overlay
  geojson per session, so a partial union persists until reload; the query path refetches
  with Retry and is unaffected).
- **Hover-roster prefetch is all-or-retry**: the composite `hoverOfficial.load` rejects if
  any county's load fails (the engine caches only resolved rosters), so the next toggle-on
  retries; already-loaded counties resolve instantly from cache.
- **One style + a generic toggle label** per concept. County identity moves into the card
  (a `Body`/`Court`/`County` row, or the clerk link) right after the district identifier.
- **Permalinks keep working**: retired per-county ids are rewritten by the fork-side alias
  shim that runs before boot-time hash parsing; every consolidation appends its retired
  ids there.
- An entry's coverage may be **narrower than its county**: `county-precinct`'s Cook entry
  uses `suburbanCookCoverage` (in Cook AND NOT Chicago) because city precincts belong to
  the BOE's `ward-precinct` layer — the carve-out test fails toward "not Chicago" so a
  city-tiling outage can't take down suburban service.
- **The key doesn't have to be a county** — the dispatch only ever required disjoint
  footprints. `ward` is the precedent (2026-07): municipal wards consolidated onto it as
  municipality-keyed entries via `opts.entries` (the general spelling alongside
  `opts.counties`). Two wrinkles worth copying: order the table so the cheapest
  already-cached coverage test sits first and short-circuits the OR (Chicago first —
  most traffic never fetches the suburban coverage file), and make a multi-source
  entry's coverage test a small **prebuilt outline file**
  (`data/app/municipal-ward-coverage.json`, `build_municipal_ward_coverage.py`) rather
  than the live services — the engine evaluates `coverage` for every declaring layer on
  every point selection.

## 2.2 What consolidates, what doesn't

- Concepts consolidate; **bodies don't merge** — `ccbr` (property-tax appeals) is not
  Cook's legislature and stays its own layer.
- `ward-precinct` stays a city layer: same concept as county precincts, different parent
  (`subOf ward`) and different election authority (§1.3).
- **Municipal governments are NOT county-dispatched**: the sourcing dimension is the
  county, but the dispatch dimension is the municipality — 284 metro municipalities tile
  from one statewide source and 47 span county lines, so a county-keyed table would
  resolve the wrong body at borders. They join the statewide `municipality` card by place
  GEOID (§2.4).
- **Single-county concepts** stay dedicated until a second county ships (conversion
  triggers in §1.5).
- A county-specific layer is only ever created for a concept no consolidated layer covers
  yet (as `dupage-county-special-police` remains).

## 2.3 Rule 4 — officeholder sourcing is determined AT expansion, never deferred

For every concept a new county brings in, the same change that ships the boundary decides
— and builds — the officeholder story:

1. **GIS attrs**: the county's boundary service carries member/contact fields (Lake; Kane
   names) → verify against the published directory and use them; no pipeline. GIS attrs
   and a directory pipeline **compose** (Kane: GIS names as hover+fallback, weekly
   SharePoint scrape adds party/phone/email + the countywide Chair; Lake: GIS live fields
   + a weekly scrape adds Chair/Vice-Chair tags, applied only on a name match so a missed
   reorganization degrades to role-less rows).
2. **Official directory, no GIS fields** (Will, DuPage, Kendall class): scraper + builder
   + weekly PR-opening workflow ships **in the same expansion change**. Bot-managed sites
   are not an excuse — the engine ladder (requests → Playwright → Internet Archive SPN;
   `kendall_county_board_scraper.py` / `mchenry_county_board_scraper.py` are the
   templates) handles Cloudflare and Akamai fronts alike.
3. **No verifiable source**: the card links the official body; the guidebook records the
   gap. The floor, never the default.

**Terminal case (verified 2026-07 on Kendall/McHenry):** a source may block ALL automated
fetch — direct, real-browser, and the Archive's crawler. The pipeline still ships: the
roster holds hand-verified transcription (every record carrying `source_url`), the weekly
workflow attempts the ladder and converts total failure into a standing tracking issue
(green run — the validate-sources pattern), a 45-day snapshot age guard ensures stale is
never served as fresh, and automation resumes the moment any rung unblocks.

## 2.4 Rule 5 — municipal governments ship with their county

A county brings its municipalities; rule 4 applies to them in the same expansion change.
Status: **all seven metro counties SHIPPED** (2026-07-28) — 279 municipalities on one
weekly-CI `municipal-officials.json`: **156 full governing bodies** (Cook + Will), **82
head-of-government** entries (DuPage, Kane, McHenry, Kendall), and **41 contact-only**
(Lake, which publishes no names anywhere county-side), plus 958 board members and 184
ward/district seats. The concept: for a point in an incorporated place, name who governs it — head of
government, governing body, other elected officers, hall contact, official site — joined
onto the statewide `municipality` card by **7-digit place GEOID** (join precedent:
`il-county-clerks.json` on `county`). Unsourced places keep the identity-only card, so
statewide behavior degrades honestly with no coverage declaration.

**The two-body split** (the `county`/`county-board` shape): whole-municipality officers
ride this card, with a ward-elected city's full council listed ward-badged; *your* seat
is answered by the consolidated `ward` layer wherever ward polygons are published
(SHIPPED 2026-07 — see Tier B below). **The roster carries a per-member `district` field
from day one** (Cook MUNIW and the Will directory supply it) — that is what made the
ward tier a geometry-and-dispatch change with no re-scrape, and the rule holds for every
future county source.

**The five-rung source ladder** (work in order, take the first hit, record the outcome in
the guidebook either way):

1. County clerk elected-officials database/API (Cook's DOEO class — look for an XHR/JSON
   backend before settling for PDFs).
2. Clerk directory/yearbook document (Will's flipbook directory; Kane/Kendall/McHenry
   yearbooks — expect mayor-level depth, full-body if lucky).
3. Council-of-governments / mayors-conference directory (DuPage's DMMC class).
4. County GIS municipal-boundary contact attributes (Lake class — contact-only card).
5. Link-only — the rule-4 floor. Never scrape 50 heterogeneous municipal sites as a
   default (a per-muni upgrade is a deliberate decision, not a source of record).

**Per-county sources, as built** (each scraper names its own source; postures measured
2026-07-28 during the build):

| County | Source | Depth | Fetch class |
|---|---|---|---|
| **DuPage** | DMMC Membership Directory PDF — discover the dated URL from `dmmc-cog.org/membership-list/` (it rotated between research and build: `…/2025/08/…8.4.2025-1.pdf` → `…/2026/05/…5.12.2026.pdf`) | head of government only; **no trustees** (county publishes nothing municipal — verified negative) | clean fetch; 4-column text PDF, annual |
| **Kane** | Clerk Government Guide PDF — `clerk.kanecountyil.gov/Elections/Documents/GovernmentGuide.pdf` (stable URL) | head + municipal clerk; **no trustees** | clean fetch; 84-page text PDF, annual |
| **McHenry** | Clerk County Yearbook "Cities & Villages" page — `mchenrycountyil.gov/county-government/county-yearbook/cities-villages` | head + elected clerk/treasurer (+ per-person contact for a few); **no trustees** | Akamai **client-fingerprinted** — see below |
| **Kendall** | Clerk Yearbook & Government Guide PDF — `kendallcountyil.gov/home/showdocument?id=184` | head + clerk + treasurer; **no trustees** | same Akamai posture as McHenry; pypdf |
| **Lake** | **No names published county-side (firm double-verified negative).** Lake GIS Municipalities FeatureServer — `services3.arcgis.com/HESxeTbDliKKvec2/arcgis/rest/services/Municipalities/FeatureServer/0` | hall address/phone/email/website; **no names** → rule-4 branch 3 | open ArcGIS query |

**The Akamai counties fingerprint the HTTP CLIENT, not just its headers** (measured on
both, 2026-07-28, with a byte-identical full browser header set): **curl gets 200 where
python-requests gets 403**. So a complete header set is necessary but not sufficient, and
"add a browser User-Agent" is not the fix — **Playwright is the day-one rung** for these
two, which is why the workflow installs Chromium. Their scrapers still try `requests`
first (cheap, fails fast) and fall back to the Internet Archive, which genuinely does hold
snapshots of the McHenry yearbook path again (2025-03-06 onward). Note for the next
county: measure the rung with the *client the scraper will actually use* — a successful
curl proves nothing about `requests`.

**Three kinds of block, and only two of them have a rung** (taxonomy from the first live
CI run, 2026-07-28 — the run that took six of ten scrapers and blocked four). Read the
response *headers and body size* before writing anything, because they tell you which
one you have and therefore whether a rung can exist at all:

| Block | Signature | Beaten by |
|---|---|---|
| **Challenge** | Cloudflare; 403 or a 200 interstitial ("Just a moment", `cf-browser-verification`) | a browser rung — there is something to solve |
| **Network deny** | same request, 200 from a developer machine and 403 from a CI runner | a browser rung **only if** a challenge sits underneath (DuPage: it did) |
| **Hard WAF deny** | Akamai; small static body (~408 bytes) with `x-reference-error` | *nothing* — Joliet's browser rung fails identically to `requests` |

A hard deny is rule-4 terminal: record it, keep whatever rungs exist so the source
resumes automatically if the edge relaxes, and let preservation carry the data. Do NOT
reach for the Archive reflexively — evaluate it, then say what you found. Joliet's
captures are *good* (the archived index still yields all nine bio links, the bio pages
still carry their e-mails) and it was still declined, because the newest index capture
was 69 days old against the 45-day guard: a conventional rung would refuse every run,
and widening the guard for one source spends a fleet-wide honesty rule on data that
preservation already covers — a last-good entry scraped from the real site beats a dated
copy of it. **The guard is the point, not an obstacle to route around.**

**Two source defects worth expecting elsewhere.** DMMC prints phone numbers with **no
area code** and states no default, so DuPage ships `phone: null` rather than a dead
`tel:` link — per-field honesty beats a completed guess. Kendall's yearbook misspells
Minooka as "Minnoka"; the scraper carries an explicit, reviewable alias so the place
still joins its Census GEOID. Correcting a place NAME to make a geographic join is not
the same as inventing officeholder data — no person's name is ever altered.

**Appointed staff are excluded, never misfiled.** Four of these sources print village
administrators, city managers, and deputy clerks beside the elected officers. The card's
officers section is titled "Other Elected Officials", so an appointee shipped there would
be mislabeled; only elected offices (head, clerk, treasurer) ship. A future card that
wants them needs a separately-labeled section first.

(Shipped-county sources, for reference: Cook = the Clerk's Directory of Elected Officials
JSON API, `cookcountyclerkil.gov/api/ElectedOfficial/GetByJurisdictionType?id=MUNIS` +
`id=MUNIW` for ward alderpersons — its Socrata copies are 2014-frozen, never use; Will =
the Clerk's "Will County Directory" FlipHTML5 flipbook, discovered from willcountyclerk.gov
nav, never a hardcoded book id.) **Statewide aggregators are a verified dead end** (IML
paid print; the Comptroller's "CEO" is often the appointed manager; Google Civic reps
endpoint sunset) — per-county clerk sources are the only honest architecture.

**Merge & precedence (the 47 multi-county municipalities):** key by place GEOID via the
Census place-by-county file (`st17_il_place_by_county2020.txt`, copy under
`data/source/`); dedupe to the **deepest** source — full body (2) > head-only (1) >
contact-only (0) — county order breaks ties only at equal depth. Never blend member lists
from two sources; record the winning `sourceUrl` per entry. The builder refuses to write
if the dropped entry had a board and the kept one didn't.

**Roster schema + shape decisions the Cook/Will builds settled** (inherit them):
`{ "<geoid>": { name, county, head?, board?: [{name, role, district?}], officers?,
office?: {address?, phone?, email?}, url?, sourceUrl } }` — people keys **omitted
entirely** where the source names nobody; contact is municipality-level (verified: Cook's
per-person phone/email columns are empty for all 1,134 records) and renders once on the
hall row; head/board/officers stay separate sections so a mayor-level county ships a
`head` with no `board` honestly; **Library Trustees are excluded** (they sit on
`library-district` boards, not the municipal body). Two shape additions from the
five-county build: **per-person `phone`/`email` ride the person** where — and only where —
the source publishes them per member (McHenry prints a direct line or office e-mail for a
few officials); a "personal" number equal to the village-hall line is dropped, because
carrying it would imply a direct line the source doesn't publish. And **`nextElection`
(a year) rides the person** where the county publishes it (Cook: 100% of records):
municipal terms are STAGGERED — 103 of suburban Cook's 104 village boards mix two cycles —
so "when is this seat next on the ballot" varies seat by seat and is exactly what a
resident wants; the card drops a year already past rather than calling a stale seat's
election "next". Count floors as built:
per-county muni floors (cook ≥120 · will ≥30 · dupage ≥32 · kane ≥26 · mchenry ≥26 ·
kendall ≥12 · lake ≥48), member floors (cook ≥900, will ≥260, and for the mayor-level
counties a floor ABOVE the head count so a run that silently lost every clerk still
fails), Lake's member/head floors 0 by design, merged total ≥250 (built: 279).

**The central city is a municipality too.** Chicago's own card named nobody until
2026-07-28 while every suburb named its mayor — the recorded suburban-parity asymmetry.
The fix needed no new source: the Cook Clerk's directory covers all of Cook (only its
address *search* is suburban-only) and publishes the city's three citywide elected
officers under its own jurisdiction type (`CHIWD`), while the 50 ward seats sit under a
separate type (`CHICA`) and stay the `ward` layer's answer. The card renders the head +
citywide officers and, in place of a 50-row council, a section that says the seats are
elected by ward and points at that layer — an empty section there would read as "this
city has no council". **Check this for every fork:** the reference city is the one
municipality a metro build is most likely to skip, because its council already has a
layer.

**Term data: label it as the source labels it.** Three counties publish three different
term facts and none of them is interchangeable — Cook the next election date, Will the
year a term expires, Kendall the date last elected. They ride the person as
`nextElection` / `termExpires` / `lastElected` and render as "Next election 2029" /
"Term expires 2027" / "Elected 2025". Normalising them into one field would state
something no source says. Two rules that fall out: a *future*-tense fact already in the
past is not rendered (both feeds carry a few stale seats), and where a source publishes
more than one fact, keep only the one the card will show — Cook's last-elected date would
have added ~1,000 unread fields beside its next-election date.

**A fact that appears on two cards gets ONE render helper.** Municipal term data surfaces
on both the Municipality card and the City Ward seat card, and the concept is split by
design — the Municipality card suppresses districted councils, so a ward-elected
resident's own seat exists only on the Ward card. Two copies of the labelling and the
past-year gate would let the same fact drift into two wordings, which reads to a user as
two different claims. Extract the helper the moment the second card wants the fact
(`municipalTermNote()`), rather than pasting the branch.

**Match a fact to the SEAT or to the PERSON, and let that decide whether you need a name
join.** Chicago's term data comes from a different source than its alderperson names (the
City's roster carries contact but no term fields, so the Clerk's `CHICA` type supplies
them). Next-election is the seat's — all 50 wards run on one cycle, so it is true of Ward
43 whoever sits in it, and it needs no name match at all. The Clerk's `appointed` flag is
the person's, and the two rosters format names differently enough (12 of 50 differ by
middle initial, nickname or suffix) that pinning it to the other roster's name would be a
heuristic — so it is deliberately not carried. When two sources describe one seat, sort
each field this way before joining; it usually removes the need for fuzzy name matching
rather than motivating it.

**A multi-source roster build must never gate on a source that can block
permanently.** The municipal-officials workflow originally required all ten
scrapers to succeed, reasoning that dropping a county would delete live
officeholders. The first live run (2026-07-28) showed the cost: four sources
403'd GitHub's runner IPs — McHenry and Kendall block every rung including the
Archive's crawler, DuPage and Joliet answer a developer machine but not the
datacenter ranges — so the build skipped and the roster froze *for every
county*, including six that had scraped perfectly. An all-or-nothing gate over
N sources fails whenever ANY one is permanently blocked, and rule-4's terminal
case guarantees some will be.

The fix is per-source preservation, not a looser gate: a blocked source carries
forward its currently shipped entries (`--preserve` + `--preserved <id>`) while
every other source refreshes. Three properties make that safe to automate —
copy them:
1. **Some sources are not preservable.** Cook and Will are the only
   full-governing-body sources here, so building without either would silently
   ship mayors where councils belong — no count floor would notice, because the
   municipalities all remain. The builder refuses rather than degrade.
2. **Preserved data re-enters through the ordinary merge paths**, so it cannot
   take a shortcut the fresh path doesn't have: a preserved county goes through
   the same cross-county precedence, and a preserved city payload through the
   same `merge_contact` that can only fill fields the county left empty — so it
   can never resurrect a seat-holder the county has since replaced.
3. **Preservation is stated, never silent.** The build prints which sources were
   carried forward and how many entries each contributed, and the PR body
   repeats it: preserved data is shipped but *not re-verified this run*, which a
   reviewer has to be able to see.

Diagnostic note for any workflow using `continue-on-error`: the jobs API reports
a swallowed failure as `conclusion: success`, so a run can look entirely green
while half its steps failed. Read `steps.<id>.outcome` (the result *before*
`continue-on-error`), or the step logs — not the API's conclusion.

**Name the jurisdiction the way the source labels its form of government.** Cook prints
"Village of Alsip"; Kane groups under CITIES/VILLAGES and DMMC tags each entry (V)/(C).
Carrying that into the jurisdiction string is what lets the card title the hall row "City
Hall" vs "Village Hall" — the builder strips the prefix again before joining on GEOID, so
it costs nothing and a county that ships bare names silently degrades to "Municipal Hall".

**PDF-parse lessons (the Will build was ~10× Cook, all source-format; the PDF counties
will hit the same class):** parse the real PDF with a layout-preserving reader (`pypdf`
layout mode / `pdfplumber`), never a line-flattened rendition. In flattened text: labels
glue to neighbors (match section headers as plain substrings, longest-first — `\b` fails
silently); a repeated section header absorbs into the next name (blank headers before
scanning); "At Large" labels a group, not a seat; names carry nicknames/curly quotes/comma
suffixes (an ALL-CAPS `(IND)` is a party code, not a nickname); officer names need a
greedy-but-bounded pattern (the term-expiry anchor that saves board names is absent);
an undelimitable address returns None — ship no address line rather than a guessed one.

**The bounded per-city exception (Will, 2026-07-28).** Rung 5 says never scrape
heterogeneous municipal sites as a source of record. The one shape that earns an
exception: **the cities whose seats the `ward` layer answers**, because the Municipality
card now sends readers to a per-seat card and that card should be able to name a way to
reach the seat's holder. Will's clerk directory publishes no per-seat contact (only the
municipality's and, sometimes, the clerk's), and its ward GIS carries geometry only, so
the three reachable ward cities' own sites supply it — Crest Hill per-alderperson phones,
Wilmington per-alderperson e-mail. Two rules keep it safe: **the county clerk stays the
roster of record** (a city site contributes CONTACT to a municipality the county already
covers — never adding, renaming, or re-roling a seat-holder; an unmatched name is logged,
not merged), and **a per-person value equal to the municipality's main line is dropped**,
since that is not a direct line. Name matching is surname + given-name overlap or
truncation, falling back to a *unique* surname within that one council and logging when
it does; two possible matches refuse rather than guess.

**Never join on a name that isn't unique in your state.** Illinois has two Wilmingtons and
two Windsors, and a first-match-wins lookup picks whichever the file lists first — that put
Greene County's Wilmington in the ward-coverage file and hid the ward layer in the real one.
Every name→entity lookup is county-qualified, or refuses an ambiguous name; none of them
silently take the first hit. The same rule covers a *key* that isn't unique: a ward number
identifies two people in cities that elect two alderpersons per ward, so the seat lookup
returns all holders, not the first. Both classes fail silently and neither has a gate —
audit them by running the lookup over real data (`docs/DATA_LAYER_GUIDEBOOK.md`, the
2026-07-28 name-collision sweep, records what was checked).

**When the county source silently omits a municipality.** Will's directory drops Lockport
and Wilmington entirely — the flipbook's text layer is missing their entry HEADERS, so the
entry split cannot see them, and no parser recovers text that isn't there. Both are ward
cities, so each resolved a ward polygon with no seat-holder behind it. The same city-site
pass supplies those two rosters outright. **Check for this class after any document-sourced
county build:** compare the scraped municipality list against the county's Census place
list, since a missing entry is invisible in the output — it simply isn't there.

**When the county and the county's GIS disagree, the municipality is the tiebreaker.**
Cook GIS mapped four Skokie trustee districts while the Clerk's directory listed all six
trustees as municipality-wide — a district polygon with nobody attached. Neither source
was lying: Skokie moved to four districts plus two at-large in April 2025, the GIS
followed, and the Clerk's feed simply doesn't carry the assignment. The village's own
site is the authority on its own districting, and it is the only thing that settles which
side is stale. A municipality with ward geometry and no districted seat in the roster is
that smell; the builder now warns on it against `municipal-ward-coverage.json`.

**Re-test a recorded "unbuildable" before believing it.** Joliet was skipped as
unbuildable — joliet.gov 403'd every client tried, jolietcity.org looked client-rendered,
and the only Archive snapshot was four years stale. Re-tested a day later, both premises
were wrong in instructive ways: the 403 was the same **client fingerprint** as the Akamai
counties (a complete browser header set gets 200, so Playwright carries it), and
jolietcity.org is not the city's site at all but a parked domain serving a redirect stub.
The city publishes a council index plus a page per member, each with a direct phone and
e-mail. A non-build record is a snapshot of what was tried, not a property of the source;
re-testing one costs minutes.

**Budget for per-page layout drift within a single site.** Joliet's nine bio pages use
four shapes: the mayor has no seat line where members do, one member's seat rides inline
after the name ("…Quillman, At-large"), one member's e-mail is split across two lines
mid-token, and one member's URL lacks the "-bio" suffix every other page has — that last
one silently dropped him until the link pattern was widened. Anchor on the stable element
(here the e-mail address) and walk outward, rather than trusting fixed offsets, and make
the count floor the real roster size so a dropped member fails the run.

**Tier B — suburban municipal wards (SHIPPED 2026-07).** Shipped as **entries of the
existing `ward` layer**, keyed by municipality (§2.1) — one toggle, one concept, whether
Chicago calls it a ward or Joliet a council district. Sources: Cook GIS
`politicalBoundary/MapServer/22` "Municipal Ward" (21 suburbs incl. Skokie's 2025
trustee districts; joins the DOEO MUNIW roster — same publisher); Will GIS
`Ward_Districts` (Joliet/Lockport/Crest Hill/Wilmington); Evanston + Aurora
self-publish. Seat-holders join `municipal-officials.json` by municipality + seat
number; per-seat contact renders ONLY where a source carries it per-member (Evanston) —
the roster's shared hall line on an individual's row would be a false implication.
Verified negatives, standing for future counties: no county-level ward layers in
Lake/DuPage/Kane/McHenry/Kendall (Waukegan is PDF-only) — a new county's ward-electing
suburbs join as further `ward` entries when a polygon source appears.

## 2.5 The county-N+1 checklist (one change-set)

1. Coverage outline (TIGER county boundary → pre-built outline file).
2. `county-board`: districted → dispatch entry + officeholder story; **at-large →
   county-card roster rows** (§1.5). Decide and record which.
3. `judicial-subcircuit`: entry if the circuit has PA 102-0693 subcircuits; structurally
   n/a otherwise (Kendall precedent — record it).
4. `fire-district` / `park-district` / `library-district`: entries per available tilings
   (`polygonCountyEntry` adapter); municipal rows per the complete-tiling rule; gaps
   recorded (McHenry-park precedent).
5. `county-precinct`: entry keyed to the county's election authority; polling-place join
   where published (Kendall's GlobalID join is the model); carve out any municipal
   election commission the county contains.
6. `tif-district` (post-conversion): entry where the county publishes a tiling.
7. Municipal officials: the county's ladder rung (§2.4), keyed by place GEOID; township
   sections captured in the same scrape where the source prints them. Where the county
   or its cities publish suburban ward polygons, they join the consolidated `ward` layer
   as municipality-keyed entries (rebuild `municipal-ward-coverage.json` via
   `build_municipal_ward_coverage.py`).
8. County officers: the clerk row is automatic (ISBE, statewide); further officers per
   rule 4.
9. Statewide layers (`county`, `township`, `municipality`, `school-district-*`, chambers,
   `zip-code`): **nothing to do.**
10. Bookkeeping + gates: Part 6.1 worksheet entries and regeneration, Part 6.3 pipeline
    artifacts per new roster, Part 6.5 gates, guidebook coverage-map/inventory/matrix
    rows, smoke ground truth if the county adds an anchor.

**Layer-count check: unchanged** — if a step wants a new toggle, run §1.6.

## 2.6 Verification

The standard gates (Part 6.5) plus: the Playwright smoke test's coverage-hide, permalink
stability, and alias-shim assertions (an old-id `layers=` link must light the consolidated
toggle); a live dispatch harness against the real county endpoints asserting (a) each test
point matches exactly one county's geometry and (b) known ground-truth districts resolve
(Loop → Cook commissioner district; Wheaton → DuPage board 4; a Will point → board
district + roster entry). For municipal rosters: a point sweep per depth class — full
council, mayor-level, contact-only, identity-only, unincorporated-empty — plus one
independent cross-check of a parsed council against the city's own published roster
(the Aurora check pattern).

---

# PART 3 — Path B: statewide Illinois

**Decided shape: expand this app in place, rebranded toward Illinois — not a separate
statewide fork** (a separate deployment duplicates CI/SW surface and fragments the
cross-county experience; more city forks can't host township/county/circuit concepts).
The gating is practical — per-county data availability and careful evolution of the live
reference app — not procedural.

## 3.1 Already done (don't rebuild)

- **Relevance-aware hiding** (`mod.coverage`, hide-only): outside a layer's coverage the
  toggle block, card, overlay, hover row, and query are suppressed **without touching
  `state.layersOn`** — permalinks survive and the layer reappears in coverage. Shipped
  through the engine pipeline; a throwing coverage test fails open.
- **The statewide identity set** resolves for any Illinois point today: `congress`,
  `il-senate`, `il-house`, `il-supreme-court` (pre-built statewide geometry + rosters),
  `county` (+ clerk), `township`, `municipality`, `school-district-{unified,secondary,
  elementary}`, `zip-code`.
- Structural empty states where a null is honest (Chicago townships, unincorporated
  municipality clicks).

## 3.2 The remaining shell/rebrand pass (fork config, no engine change)

Map clicks resolve statewide already; the **input shell still stops at the greater-metro
envelope**. The pass: widen `METRO_BBOX` (geocoder bias/viewbox) and `PERMALINK_GATE` to
the state envelope; swap the scope-mask loader to a 102-county `STATE='17'` tiling so the
wash marks only genuinely-outside-Illinois; audit `METRO_NAME`/brand copy (several strings
compose as "the {METRO_NAME} District Explorer"); the name/domain question ("Illinois
District Explorer" at chidistricts.com vs a neutral domain) is an operator product call.
Verify per §3.5 and keep every Chicago ground-truth assertion green — the reference
experience must not move.

## 3.3 Downstate rollout rules

Source classes (per family): **FREE** = one statewide GIS lights up all 102 counties
(TIGERweb `STATE='17'` — counties, CouSub/townships, places, school districts ×3; already
shipped). **DERIVE** = FREE layer + a lookup table (judicial circuit — **blocked**: no
authoritative machine-readable county→circuit source; ROE regions — candidate, verify
carve-outs; never hand-encode either). **PER-COUNTY** = no uniform source (boards,
precincts, park/fire/library, subcircuits beyond the enacted shapefiles) → collar-first,
grow outward by data availability, **hidden where unsourced** — relevance-hiding is what
makes deep-in-some-places coverage honest and legible. All Part 2 rules apply per county;
at-large boards land as county-card rows (§1.5).

**Risks, ranked:** precinct sourcing statewide is hardest (102 clerks, non-uniform,
frequently redrawn; Census VTD stale — never claim statewide, never block Phases on it);
officeholder rosters beyond the metro have no keyed statewide source (identity +
official-body link is the floor; the metro carve-out exists because seven clerks publish
keyable directories); every step preserves Chicago byte-for-byte where fenced and
behavior-identical where not.

## 3.5 Verification

Ground-truth a downstate point against every statewide layer (the shipped check: Homer
Glen → Will County / Homer Township / Homer Glen village / Lockport Twp HSD 205 / Homer
CCSD 33C / no unified district); confirm the Chicago Loop stack unchanged; confirm the
scope mask washes only outside coverage; after the rebrand, grep the pre-rename brand
strings (title, masthead, meta description, geolocation strings, manifest).

---

# PART 4 — Path C: a new metro fork

**Chicago is the reference implementation; each metro is its own fork** — separate repo
and site, evolving independently in metro-specific code only; the fenced ENGINE blocks
stay byte-identical via the release pipeline. The **metro-#3 gate is OPEN** (all three
mechanization conversions DONE 2026-07-13; drill evidence in
`docs/archive/MECHANIZATION_PLAYBOOK.md`) — new metros are unblocked procedurally.
**Scope, honestly:** this recipe targets large US metros with district-based elected civic
geography; non-US cities lose the federal/universal tier, and small towns may have no
digitized boundaries at all. Completed-port worked examples: NYC
(`docs/archive/METRO_EXPANSION_NYC.md` — thread log; registry/roster model in
`docs/archive/METRO_EXPANSION_PLAYBOOK.md` Part II) and SF
(`docs/archive/METRO_EXPANSION_SF_WORKSHEET.md` — a completed §0 worksheet).

## 4.1 City Worksheet — fill this in first (Thread 0's first deliverable)

| Parameter | Chicago (reference) | Derive yours |
|---|---|---|
| `CITY_NAME` | Chicago | title/masthead/meta/aria/geolocation strings |
| `STATE_FIPS` | `'17'` | 2-digit Census FIPS — drives every TIGERweb query |
| County structure | city ⊂ Cook (17031) | coterminous / inside / spread-across — "spread" means county-office layers cover part of the city: plan honest partial-coverage empty states + a county context layer (§4.8) |
| School governance | one unified district (CPS), elected board | one entry per system serving the metro (Houston: HISD + ~10 ISDs); elected vs appointed board per system — shapes the whole schools group |
| `BBOX` | tight city envelope | feeds geocoder bias, POI viewbox, geolocation check |
| `CENTER` + zooms | downtown, zoom 11, minZoom 9 | frame the city; keep the metro reachable |
| Permalink gate | greater-metro box, deliberately looser than BBOX | rejects absurd `#point=` values; independent of BBOX |
| Portal(s) + platform | Socrata `data.cityofchicago.org` | host AND platform (Socrata/ArcGIS/CKAN) — changes how every layer queries (§4.6) |
| App token? | anonymous OK | start anonymous; free token at first 403/429 |
| Geocoders | Photon + Nominatim POI | §4.6 decision rule; city-authoritative instance wins if one exists |
| School profile URL(s) | `cps.edu/schools/schoolprofiles/{id}` | per school system; lives in `schoolProfileHtml` |
| Domain / email / repo / brand | chidistricts.com etc. | fork's own — grep `github.com/ThursdaysFamous` for all three link sites |
| Offline anchors *(mid-port)* | school-board, il-supreme-court, ccbr | ≥3 static-file layers (§4.5) |
| Ground truth *(mid-port)* | Loop point → 3 anchor districts; second point in different districts | + a negative point where geography allows (§4.5) |
| `EXPECT_LAYERS` *(mid-port)* | (live count: CLAUDE.md metro-facts) | asserted exactly by the smoke test |

## 4.2 What the fork keeps vs rewrites

`index.html` is ~60–65% metro-agnostic engine — map boot, registry + card framework,
state/sequence, permalinks, hover explorer, shared utilities, loaders, factories — all
fenced and machine-enforced (`check_engine_parity.py … --strict` passes when the re-core
is done and stays a per-thread gate). The fork rewrites the **layer modules** (the THREAD
banner spans) and the **METRO config + branding constants**.

**Re-core surgery notes (paid for in NYC):** delete only the `registerXxx({…})` calls and
their city-specific preamble; keep every factory and loader. Then grep the ENTIRE
surviving file for calls to now-undefined identifiers — dangling references run both
directions (a kept factory calling a deleted helper crashes only when the first REAL
roster lands — placeholder data hides the path; kept core calling a deleted layer-span
helper — Chicago's water-taxi easter egg — throws on every click). City vocabulary also
hides in engine code as **feature-property name literals**: re-seed
`HOVER_NUMBER_KEYS`/`HOVER_NAME_KEYS` from the new city's observed field names (stale
lists fail silently — the hover popup degrades softly by design and no gate notices), and
generalize city strings inside kept factories (`schoolProfileHtml`, the chamber factory's
capitol/directory labels — parameterized opts exist).

**Core constants to swap** (each by grep anchor; most live in the `METRO:BEGIN config`
block): `THIS_METRO`/`METRO_NAME` · `METRO_BBOX` · `METRO_CENTER` + zooms ·
`PERMALINK_GATE` · geocoder endpoints/bias (§4.6) · `GROUPS` (usually verbatim — the four
buckets are city-agnostic) · `LAYER_AREA_RANK` (rewritten entirely; every registered id
present — §4.4 step 4) · `SOCRATA_HOST`/`SOCRATA_APP_TOKEN` (or delete the Socrata stack
if unused — fenced-block deletion reads as honest "unused", not drift) ·
`arcgisServiceUrl` org id · TIGERweb `STATE='NN'` filter · school-profile URL builder ·
"data last verified" date · debug namespace (twinned in `smoke_test.mjs`) · hover fallback
key lists · preconnect/dns-prefetch set (≤4, aimed at your LCP — §4.10) · analytics tag
(fork's own GoatCounter — never the reference's, never absent) · `METRO_EXPLORERS`
(shared canonical list — a new metro's entry is added in EVERY sibling as the same config
diff, with `emoji` + `bbox` for the metro-portal easter egg; `validate_index.py` lints
entries).

**Branding rows:** `<title>`/meta description, theme-color + favicon SVG, `:root` palette
custom properties (grep the var prefix for downstream uses), masthead heading + emblem,
city-named a11y strings, footer source attributions, feedback email, repo/sponsor links.
**Sibling files:** `CNAME`, `manifest.webmanifest`, `icons/`, `README.md`, `CLAUDE.md`
(rewrite for the fork or agents get steered wrong), `sw.js`'s three lists, everything
under `data/`. Workflows carry over structurally (constants, dataset names, cron slots) —
except the fleet machinery listed in §4.4 item 11. `docs/ENGINE_SYNC.md` +
`scripts/check_engine_parity.py` ship **verbatim** — they are engine.

**Test/gate constants are re-derived, never copied** (§4.9 + Part 6.5): smoke `POINT` /
`OFFLINE` / `EXPECT_LAYERS` / `EXPECT_DISTRICT` + second point + kill target;
`validate_index.py` `MIN_REGISTER_LAYER` / `GEOMETRY_FILES` / `ROSTER_FILES`; the
`validate_sources.py` manifest; every count guard; `sw.js` `CACHE_NAME` + lists.

## 4.3 The layer contract (verbatim across the fleet)

```js
{
  id, group,                    // political | safety | schools | geography
  label,
  overlay: { load, style | pointToLayer },   // lazy, cached
  query(point, seq) -> Promise<Result|null>, // point-in-district + roster join; seq-tagged
  render(result) -> HTMLElement,             // all external strings sanitized
  pointOfInterest(result) -> {label,address}|null   // optional geocoded pin
}
```

Optional fields the core honors: `subOf`, `color`, `onToggle(on)`, `hoverName(feature)`,
`hoverOfficial{load?, name()}`, `coverage(point)`, `compact`, `primaryLink`. Five
non-negotiable module rules: seq-tagged results; toggle-off clears the card; failures
surface inside that card only; sanitize everything external; explicit honest
no-result/no-match/slow states. **Hover-parity rule:** hover identity comes from the same
properties the card reads (factories derive it; a bespoke block declares `hoverName`, plus
`hoverOfficial` when the card joins a roster — prefetched on toggle-on so hover never
fires a network request). An appointed official's hover name carries its role.

**Factories before bespoke blocks:** `registerPolygonLayer` (declarative fields card) ·
`registerSchoolZone` (zone → school + POI + profile link) · `registerCpsNetwork`
(officeholder rides the boundary dataset's props) · `registerIlgaChamber` (boundary +
same-origin roster keyed by district; the congress/state-chamber pattern, incl. office
groups) · `registerNearestPointLayer` (nearest-N haversine). Non-factory patterns to
copy: two-live-datasets join (`ward`); shared-geometry, one loader → N layers
(`ccpsa-district-council`; NYC borough = county serving three offices); nearest-N bespoke
(`school-site`, polygon campus footprints). Platform coupling: `registerSchoolZone` /
`registerCpsNetwork` build loaders via the Socrata-only `makeCachedLoader` — on a
non-Socrata portal convert them to an injected `loader` (follow `registerPolygonLayer`'s
existing opt).

**Cards** follow the fleet content order — layer name, district identifier, then wherever
a verifiable source exists: representative(s), office location, contact, link — rendered
through the card-helpers vocabulary (`docs/CARD_RENDER_API.md`; helpers are data-only by
contract, never pass HTML).

## 4.4 The porting checklist (in order)

1. **Fork** the reference repo (the engine, gates, and CI shape are the value).
2. **Fill the §4.1 worksheet.**
3. **Swap the METRO config + §4.2 constants/branding**; never edit inside a fence;
   `check_engine_parity.py --against https://chidistricts.com/ --strict` passes at
   re-core and stays a per-thread gate.
4. **Decide the layer roster from the concept matrix** (`docs/DATA_LAYER_GUIDEBOOK.md`):
   reuse siblings' recorded patterns and drop rationales; walk the reference layers and
   map each to the local equivalent; **drop, never fake, where no honest analog exists**
   and record each drop with its structural reason (the NYC drop table is the model).
   Apply §1.2 to the two edge cases: elected citywide/at-large offices get an explicit,
   recorded per-office decision (shared-loader city polygon, labeled At-Large rows, or a
   recorded deferral — silence is the only wrong answer); multi-district school metros
   register per-system layers or record the drop — never stitch. Add local layers the
   reference lacks. Then write `LAYER_AREA_RANK` largest→smallest — **every registered id
   appears, no exceptions** (two consumers: restacking + hover profiles; a missing id is
   invisible to both), with sub-layers ranked just before their parent.
5. **Build the data registry** (§4.7 template): one row per layer, VERIFIED only after a
   live fetch *you* performed.
6. **Pick ≥3 offline anchors + ground truth** (§4.5), including the scope-mask tiler and
   the negative point.
7. **Map the pipeline** per roster (Part 6.3): engine ladder rung, count floors — and
   **land the cheapest real roster during the module threads**, not the pipeline thread
   (real data flushes factory paths placeholders never exercise).
   7a. **Officeholder sourcing ships with each layer** (rule 4 — Part 2.3 verbatim).
   7b. **Suburban municipal governments are a decided concept** — any metro whose
   coverage passes the central city inherits Part 2.4 wholesale (GEOID join, depth
   ladder, district captured at scrape time).
8. **Re-derive every gate constant** and the three `sw.js` lists.
9. **Cross-group parity audit**: for each field any group's card renders (address, pin,
   phone, links), check every other card that could carry it — no gate catches this
   class; only a side-by-side pass does. Second axis: **hover sweep** — toggle every
   polygon layer, hover the ground-truth points, confirm real identities (the popup fails
   soft by design and shipped label-only in NYC).
10. **Swap deploy, register the fork in the fleet (§4.4.1), run the localization sweep
    (§4.4.2)**, replace this guide with the fork's pointer stub, and record the final
    roster in the guidebook.

### 4.4.1 Day-one fork registration (every item was missed by a real port)

In the **Chicago repo**: (1) add the fork to `metros.json` + `--sync-fleet` regeneration
in every fork (regeneration PRs, never hand edits — a fork missing here is invisible to
fleet-status); (2) add the repo to `release-engine.yml`'s fan-out list; (3) *(operator)*
add it to the `ENGINE_DISPATCH_TOKEN` PAT; (4) add it to the guidebook (coverage map +
inventory + matrix, drops included). In the **new fork**: (5) delete the producer
`release-engine.yml`, carry the consumer `engine-bump.yml`; (6) deploy downloads the
engine per `engine.lock.json`; (7) *(operator)* Pages source + custom domain + `CNAME`;
(8) *(operator)* Actions → "Allow GitHub Actions to create and approve pull requests" =
ON (bot PRs die silently without it); (9) *(operator)* CI secrets (tokens/keys); (10)
replace PWA icons; (11) pointer-stub every CHI-mastered doc (`EXPANSION_GUIDE.md` and the
legacy stub set — `METRO_EXPANSION_PLAYBOOK.md`, `BUILD_PLAYBOOK_1.md`,
`OPTIMIZATION_PLAYBOOK.md`, `REDISTRICTING_RUNBOOK.md`, `MECHANIZATION_PLAYBOOK.md`; all
stubs under `docs/`); `ENGINE_SYNC.md` stays a full copy; the guidebook and
`docs/archive/` are CHI-master with no sibling copy; the fleet machinery (`metros.json`,
`fleet_status.py`, `fleet-status.yml`, `engine-parity.yml`, `release-engine.yml`,
`create-engine-tag.yml`, `docs/engine-changelog/`) stays Chicago-only; (12) localize
`WATCH.md`; (13) re-derive `validate_sources.py` incl. `SOCRATA_DOMAIN`/`CATALOG_API`;
(14) *(operator)* create the fork's own GoatCounter site and set the tag — `trackEvent`
no-ops silently without one (SF shipped days of zero analytics).

### 4.4.2 The localization sweep (leftover-reference-city gate)

At assembly and again before launch, grep the fork for the reference city's fingerprints
(`chidistricts.com`, `cityofchicago`, `ChiExplorer`, `chicago`, `data-goatcounter` across
`index.html sw.js README.md CLAUDE.md WATCH.md manifest.webmanifest scripts/ .github/`).
Allowlist: fence comments naming the reference, `engine.lock.json` `source_repo`, the
reference's own `METRO_EXPLORERS` entry, deliberate doc citations. **Everything else is a
leftover** — past escapes include a Chicago-biased geocoder shipping through five SF
threads, Chicago SEO metadata, stale `validate_sources.py` manifests, orphaned seal art.

## 4.5 Offline anchors, ground truth, and the scope mask

Live civic APIs are flaky and CI-hostile, so the test strategy rests on ≥3 **API-free
anchor layers** shipped as same-origin static files: the smoke test classifies ground
truth against them; `validate_index.py` pins their feature counts; `sw.js` serves them
cache-first (vs network-first rosters — never a stale officeholder). The wash marks
*where deep coverage ends*, never "no data here" — regional layers still resolve under
it, and it fails silent.

**Draw the wash from a purpose-built metro outline, not from whichever anchor happens to
tile something** (revised 2026-07-28; Chicago previously passed its school-board anchor).
Two reasons, and the second is the one that bites:

1. **The boundary must track coverage as it grows.** Chicago's wash was the *city* limits
   because that is what the anchor tiled, so as the collar counties filled in it kept
   greying out territory the app had come to serve — a Will or DuPage point resolves
   17–21 of 39 layers against Chicago's 32 and suburban Cook's 25. Coverage thins across
   a metro; it rarely stops at one layer's edge. Pick the boundary from what the app
   *answers*, and re-check it after any county expansion. Removing the wash entirely is
   the opposite error: the tiers are real, and a wash-free map claims a parity the data
   does not support.
2. **Per-county outline files will not dissolve.** The engine cancels an interior border
   only where the two neighbours share EXACT coordinates. Chicago's six
   `*-county-outline.json` files were simplified independently, so they share as few as
   **2** vertices along a real border and would leave hairline seams or fail the closure
   guard. Build one polygon from a **single** query against one source (a TIGERweb
   multi-county fetch returns 2,034 shared vertices on Cook/DuPage) and dissolve it at
   build time — `scripts/build_metro_outline.py` is the reference, mirroring the engine's
   own algorithm so the shipped file is what the browser would have computed.

Simplify hard and validate the *simplified* rings: metro outlines are mostly survey-grid
straight lines, so Douglas-Peucker at 25 m took Chicago's from 2,665 vertices to **62**
(2.5 KB), and the builder refuses to write unless one anchor per county still falls
inside and known outside cities fall outside — ring closure alone does not prove a county
wasn't dropped. The payoff is also a boot cost: the old anchor was an 83 KB fetch in PSI's
669 ms initial-navigation chain for a decorative wash.

Produce anchors with `scripts/build_embedded_boundaries.py`
(pinned mapshaper, Visvalingam keep-shapes) and its validation: **≥99.5% agreement on
2,000 seeded points AND zero double-classification**, counts/properties unchanged —
register every anchor in its `LAYERS` dict so regeneration never regresses to manual.
Pin a **negative point** where geography allows (water, enclaves, county slivers) and
pick it against a shoreline-clipped layer — whether mid-water is a no-match depends on
the dataset, and the water-inclusive layer's positive answer is legally correct.
**Exactly-one-list invariant:** every `data/app/` file appears in exactly one of
`GEOMETRY_URLS`/`ROSTER_URLS` (in neither = never cached; wrong list = wrong freshness) —
machine-checked in `validate_index.py`; bump `CACHE_NAME` on any list change.

## 4.6 Platforms, sources, geocoding

Identify the portal platform first — it changes how every layer queries:

- **Socrata**: four-by-four ids, `/resource/{id}.json` SoQL; server-side
  point-in-polygon via `intersects(geom, 'POINT(lng lat)')` (lng-first WKT) — a
  *research/verification* tool here, not the runtime path (every layer downloads its
  boundary once and classifies client-side; per-click portal calls would multiply
  throttling exposure and break overlays/hover/anchors/failure isolation).
- **ArcGIS Hub / REST FeatureServer**: `…/FeatureServer/<n>/query`; always request
  `outSR=4326` (native projections are often State Plane); page past `maxRecordCount`
  while `exceededTransferLimit` (`loadArcGISPaged`).
- **CKAN**: a catalog, not a query engine — download once, convert, ship as a §4.5-style
  static file (follow "GeoServices/WFS" links to any real live endpoint).

**The federal/universal tier is free for any US metro**: TIGERweb
(`Legislative/MapServer` 0/1/2 + county/place siblings, `STATE='<fips>'`; unicameral and
council-only jurisdictions ride layer 1 — register one chamber, not two) +
`unitedstates/congress-legislators` (`legislators-current.json`, CC0 — the reference
builder re-parameterizes on state + count; the 2026-07 enrichment joins
`legislators-district-offices.json` by bioguide id).

**Geocoding decision rule:** (1) a city-authoritative keyless geocoder with real
autocomplete replaces *both* reference geocoders (NYC GeoSearch is the exemplar); else
(2) Photon for type-ahead; (3) Nominatim as debounced submit-time fallback ONLY (its
policy forbids autocomplete; keep the serial ≥1s POI queue). **App tokens:** a Socrata
app token is a public throttling identifier — front-end constant by design; a real API
key (401s without it) is a repo secret, server-side only, never in `index.html`. No
token analog exists for ArcGIS/TIGERweb/CKAN public reads — if a public endpoint
throttles/WAFs, ship the layer as a static file instead.

## 4.7 Dataset research & verification protocol

1. Live-sample field names before wiring; seed `findPropCI` aliases with observed keys.
2. Label every registry row VERIFIED / UNVERIFIED / **UNVERIFIED-fetch** (exists but
   WAF/key-blocked — it changes the pipeline engine), with the fetch date.
3. The portal-page id and the geometry-serving id can differ — record which of
   `loadSocrataGeoJSON`'s three routes actually served geometry.
4. Map-type Socrata datasets serve geometry only via the export or v3-view route — set
   the per-dataset route override rather than burning failing routes per load.
5. Probe server-side point-in-polygon once with a known landmark — validates endpoint,
   operator, and geometry column in one query.
6. Watch record caps (Socrata `$limit=1000`; ArcGIS transfer caps) — filter server-side
   or page.
7. Anchor simplification passes the 2,000-point protocol (§4.5), unmodified.
8. A layer with no honest source gets an honest registry row — drop or link, never
   invent.
9. Point datasets may serve no geometry on the geojson route (coordinates only in
   `latitude`/`longitude` properties) — `makeSocrataPointLoader` assembles the
   FeatureCollection.
10. Sample exact **values**, not just field names — SoQL string equality is
    case-sensitive (`'Police Station'` matched 0 where `'POLICE STATION'` matched 80);
    numeric-looking fields arrive as float strings. Normalize in the loader.
11. **Verify coverage, not existence** — a pattern confirmed on one sample can cover a
    fraction of the roster (Legistar carried district URLs for ~24/51 members; NYPD pages
    resolve 74/78 COs). Count how many of N records carry the thing; set floors below
    100%.
12. **Soft-degrading surfaces ship broken — audit by hand**: the hover popup's fallback
    keys, empty states, anything that renders em-dashes instead of erroring (§4.4 step 9).

Registry columns: layer target (+ expected count) · source type · id/endpoint **+ the
route that served geometry** · geometry column + observed fields · roster source ·
CRS/paging/auth notes · status + date.

## 4.8 Generic metro gotchas (each paid for in a real port)

One boundary hosting several offices → one cached loader, N layers. Assume MultiPolygon;
spot-check a gnarly one. Trust authoritative polygons over intuition (Marble Hill).
In-bounds ≠ in-district — honest no-match, never snap; in multi-county metros register a
county context layer and word county-office empty states to point at it. Nearest-N can
cross water — keep N=3, label "as the crow flies". Non-residential polygons are real
answers — surface the type field. Honesty is per-field (§0.2). Elected-but-superseded
bodies exist (HISD's trustees under a state-appointed board): label the actual governance
status, show both bodies, each labeled — never hide the elected roster, never present
appointees as it.

## 4.9 Thread sequence, operator steps, performance parity

**Threads:** 0 fork & re-core (worksheet, constants, module delete + dangling-identifier
grep, geocoder decision, `EXPECT_LAYERS=1`, parity green) → 1 anchors + geography (ground
truth pinned, MultiPolygon check) → 2 safety → 3 schools (honest choice-based empty
states; per-system profile URLs) → 4 political (heaviest; operator rosters arrive here)
→ 5 pipeline & CI (all scraper/builder pairs + workflows + full gate re-derivation) → 6
assembly & audit (rank visual check, `sw.js` lists, final `EXPECT_LAYERS`, step-9 parity
audits, a11y, attribution, deploy).

**Operator steps:** portal tokens; domain/CNAME/manifest/icons/README/CLAUDE.md;
hand-verify operator-maintained rosters (a human checks each name); review anchor
conversions and pin gate values; evaluate key-gated upgrades (record, don't block);
work every *(Operator)* item of §4.4.1.

**Performance parity:** engine-fenced wins ride along free (bbox pre-reject +
point-query memo, incremental highlight, toggle rescale, graph release, scope-mask boot
defer, pan-pause, SW handler discipline — confirm the anchors `featureBBox(features[i])`
and `whenIdle(function () { drawOutOfScopeMask` survived the re-core). The fork
**re-earns** the metro-specific set: kill `<head>` render-blocking (inline leaflet.css;
self-host + subset fonts with metric-matched fallback; defer BOTH leaflet.js and the
boot script — a bare defer on Leaflet alone breaks boot); preconnect ≤4 aimed at the
basemap-tile LCP; **pre-build decadal legislative geometry** (live TIGERweb measured
5.69s time-to-answer; `build_legislative_boundaries.py` re-parameterized, cache-first,
tied to the redistricting runbook); keep boot lazy; per-layer precision budgets; SW
freshness split; deploy exclude list. **Measure on production PSI mobile, never a
sandbox proxy** (the sandbox stubs exactly the third parties that dominate delivery;
the reference banked at 78 on an LCP-bound frontier — don't chase the last points).
The canvas renderer stays a fleet-shared open item — inherit it, don't preempt.

---

# PART 5 — Path D: a new concept/layer in an existing deployment

1. **Run the §1.6 taxonomy test.** Most proposals resolve to a dispatch entry (Part 2) or
   an identity-card enrichment, not a layer.
2. **Consult the concept matrix** (`docs/DATA_LAYER_GUIDEBOOK.md`): if a sibling ships
   the concept, reuse its recorded pattern and source notes; if a sibling recorded a
   drop, check whether the rationale applies before re-researching.
3. **Genuinely new concept:** it launches consolidated (a dispatch table from day one if
   multi-source), registers through a factory where one fits, declares honest coverage,
   and ships its officeholder story in the same change (rule 4; the route map is §6.4).
4. **Card — the information-surfacing standard.** The card leads with the layer name
   (the card header), then the district identifier, then — **wherever a verifiable
   source exists** — the representative(s)/officeholder(s), the office location,
   contact info, and a link to more detail, in that order. The order maps onto the
   card-helpers vocabulary (`docs/CARD_RENDER_API.md`) as: **identifier pill
   (`cardIdentifier`) → person rows (badges/notes/committee expanders) → office group →
   contact line → footer link (`primaryLink`)**; name-only layers render as `compact`
   cards. Helpers are data-only by contract: never pass HTML; email renders as a mailto
   link and is never printed; phone rows carry a `tel:` href built by the helper; absent
   fields render nothing. Deviate from the order only where the concept demands it
   (nearest-N lists, no-officer geography/identity concepts, honesty-rule link-only
   judicial bodies) — and when identity, location, or contact data exists in a layer's
   source but isn't on the card yet, **record the gap in the guidebook backlog rather
   than shipping it silently**. Hover identity follows the parity rule (§4.3): the
   popup reads the same fields the card does.
5. **Bookkeeping in the same change**: worksheet layer entry (+ rank, hover keys as
   needed) → regenerate; `LAYER_AREA_RANK` placement; a `LAYER_SIDEBAR_RANK` position
   (below); sw list if a `data/app/` file is added; `validate_sources.py` manifest row;
   guidebook coverage map + inventory + matrix (drops recorded with rationale — silence
   is the only wrong answer); Appendix A row.

**Sidebar placement standard (recorded 2026-07-28).** A layer's position in its sidebar
group is set by the fork's explicit `LAYER_SIDEBAR_RANK` (grep it in `index.html` —
applied by a boot-time sort; `validate_index.py` asserts the list matches the registered
id set 1:1, exactly as it does for `LAYER_AREA_RANK`) — never by registration order,
which had accreted by build thread rather than design (Early Voting led the Political
group; a DuPage unincorporated tax district led Public Safety). The order within each
group: **identity hierarchy → representation → service/taxing overlays → amenity
points, broad → specific within each family.** Toggled-on layers still float to the top
of their group, so the rank governs the resting order, not the active one. A new layer
takes its rank in the same change that registers it.

**Exception — Political is DEMAND-ordered, most-searched concept first** (operator
call, 2026-07-28). No Search Console / query data is connected, so the ranking rests on
the best available public proxy — 12-month Wikipedia pageviews (Jul 2025 – Jun 2026,
en.wiki, user traffic) for each concept's closest article: congressional districts of
Illinois **254k** ≫ IL House **62k** > IL Senate **49k** ≈ Chicago City Council **48k**
(ward) > early voting **23k** > Cook County Board **19k** ≫ Board of Review **4.2k** ≈
Chicago Board of Education **3.4k** ≈ IL Supreme Court **3.4k** ≫ judicial subcircuits
(~0, no article). Hence: congress → il-house → il-senate → ward → early-voting →
county-board → ccbr → school-board → il-supreme-court → judicial-subcircuit. Known
proxy weaknesses, recorded so the next pass can do better: pageviews measure national
concept interest, not Chicago-resident lookup intent (which likely boosts `ward` — the
city runs a dedicated alderman-lookup tool for a reason), and early-voting/CCBR demand
is seasonal (election windows, appeal windows) rather than steady. **Re-rank from real
query data when Search Console (or GoatCounter arrival) exports exist; the bottom tier
(ccbr / school-board / il-supreme-court) is statistically tied and ordered by
recurrence of its seasonal spikes.**

**Nesting determination (recorded 2026-07-28).** The `subOf` tree — County → Township →
Voting Precinct, Ward → Ward Precinct, Police District → Beat — encodes genuine legal
containment-plus-numbering hierarchies and is complete. Evaluated and deliberately kept
flat: **CCPSA District Council** under Police District (shares geometry 1:1, but it is
an elected representation body — the app never gates an elected office behind a service
toggle); **CPS zones/networks** under the unified school district (a toggle
prerequisite on the city's most-used school layers, with no fleet precedent);
**special districts** under `county` (independent taxing bodies, not county sub-units —
the county is their sourcing dimension, not their parent); **`tif-district`** under
`municipality` (legally defensible — TIFs are municipal ordinance districts — but low
benefit, and TIF converts to a dispatched concept at its second county, §1.5).
Cross-group nesting is impossible by design: a sub renders inside its parent's block in
the parent's group section. The bar for a future nest is genuine containment-with-
numbering (precincts are numbered within townships, beats within districts), never
mere geometric overlap.

---

# PART 6 — Shared machinery (every path)

## 6.1 Worksheet + generated regions

Per-fork facts live ONCE in `metro-worksheet.json`; `GENERATED:BEGIN/END` regions in
`index.html`, `sw.js`, `validate_index.py`, `smoke_test.mjs`, `CLAUDE.md`, `README.md`
are emitted from it. **Never hand-edit a generated region** — edit the worksheet, run
`python3 scripts/generate_metro_files.py` (`--check` is the CI drift gate; `--sync-fleet`
propagates fleet-manifest changes).

## 6.2 Engine releases

Fenced engine code changes land in Chicago, ship as hash-verified release artifacts on
`engine-v*` tags, and fan out to forks as gated bump PRs — parity is true by
construction. Protocol, block inventory, new-block seeding, the tombstone convention for
retiring helpers, and the fork-born-improvement definition of done (reverse-parity WARNs)
live in **`docs/ENGINE_SYNC.md`** — the authoritative engine doc, shipped verbatim in
every fork. Expansion work needs only: don't edit in fences outside that pipeline; add
METRO config variables instead of inlining city values; when an expansion feature is
genuinely metro-agnostic, land it as an engine release so siblings inherit it.

## 6.3 The pipeline pattern (every roster)

**Scraper** → raw intermediate JSON, one record per member with `source_url` +
`scraped_at`; unfindable fields are `null`, per-member failures become `{error}` records
— never dropped or invented members. **Builder** → `data/app/*.json`, refusing to
overwrite below its count floor (floors are deliberate under-tolerances so vacancies
don't wedge the weekly run; placeholder rosters get floor 0, raised after first scrape),
stable key order for clean diffs. **Weekly workflow** → fixed `bot/*` branch, force-push,
**opens a PR, never commits to main** — officeholder data always gets human review.

**Fetch-engine escalation ladder** (cheapest that works, recorded per target): plain
requests (`ilga_scraper.py` template) → `--engine auto` requests+Playwright fallback
(`cpd_district_scraper.py`) → Playwright day one (known bot-block) → Internet Archive
SPN rung for total blocks (`kendall_county_board_scraper.py` — with the 45-day age guard
and standing-issue conversion, Part 2.3) → **rejected** (key-gated AND WAF-hard),
documented with the alternative. When the official site is unscrapeable, a maintained
open aggregator honestly supplies *structured* fields (Open States, congress-legislators)
while the official site stays the card's link target. **Ship keyed enrichments dark** —
a missing secret degrades to the unenriched roster. Key hygiene: app tokens are public;
real API keys are repo secrets, never in `index.html`.

**Freshness chores:** year-versioned Socrata datasets get a monthly successor check —
fire on a **newer edition in the catalog or a 404, never on age** (age alone cries
wolf). ArcGIS analog: record layer URL + item id; treat an HTTP-200 JSON *error body* as
unreachable; search the owning org's catalog for a successor item. Both surface as
tracking issues (`validate_sources.py` + `validate-sources.yml`), never auto-edits —
dataset swaps are schema-sensitive.

## 6.4 Routes to data — the determined map

Every datum a card surfaces has a determined route family. Work each column top-down —
take the first route that honestly works, record the outcome, and never invent what no
route provides. Fetch posture for anything scraped is always the §6.3 engine ladder;
the verification bar for any source is §4.7 (VERIFIED means *you* fetched it and saw
records); freshness watching is §6.3's chores.

| Data | Routes, in preference order | Governing rule | Shipped precedents |
|---|---|---|---|
| **District boundary — statewide concept** | TIGERweb `STATE='NN'` live → pre-built statewide file (`build_legislative_boundaries.py`, cache-first) | FREE class (§3.3); 2,000-point simplification gate on pre-built (§4.5) | chambers + congress; county/township/municipality/school-district/ZCTA |
| **District boundary — county/city concept** | county or city GIS service (dispatch entry) → pre-built static from the enacted shapefile or a one-time download (throttled/CKAN/permission-locked class) → county Clerk tax-agency tiling | one district per point (§2.1); municipal rows per the complete-tiling rule (§1.5); every id in the `validate_sources.py` manifest | county boards; Kane/McHenry subcircuits pre-built; Cook fire/park/library/TIF tilings |
| **Officeholders (any elected body)** | boundary-GIS attributes verified against the published directory → official directory scrape (weekly review-PR) → maintained open aggregator for *structured* fields only → hand-verified transcription (terminal case: 45-day age guard + standing issue) → link-only floor | rule 4 (§2.3): decided and built with the boundary; never guessed; per-field honesty; count floors | Lake/Kane GIS attrs; ILGA/CPD/county-board scrapers; Open States + congress-legislators; Kendall/McHenry rosters; `il-supreme-court` link-only |
| **Municipal governing bodies** | the five-rung ladder: clerk elected-officials API → clerk yearbook/directory → COG directory → county-GIS contact attributes → link-only | §2.4: GEOID-keyed, deepest-source precedence, statewide aggregators are a recorded dead end | Cook DOEO; Will directory; DMMC; Lake GIS |
| **Office location + contact** | the roster's own source, never backfilled from a weaker one; unit-level contact renders once on the hall/office row; per-seat contact only where the source is per-member | §0.2 per-field honesty; §2.4 schema rules | congress district offices (congress-legislators join); Evanston per-seat contact |
| **Election administration** | authority-keyed sources (ISBE's election-authority directory is the roster of authorities) → county polling-place joins where published → hand-curated per-election site files | §1.3 dispatch-by-authority; human-review PRs | county-clerk roster; Kendall's GlobalID polling join; `early-voting` |
| **Amenity points (nearest-N)** | national USGS structures layers (bbox-widened) → city/portal point datasets (`makeSocrataPointLoader` class) | nearest-N honesty: N small, "as the crow flies" on the card | police/fire stations + post offices (USGS); CPL `library`, `school-site` |

## 6.5 The gates

- `python3 scripts/validate_index.py index.html` — merge gate: parse check,
  `registerLayer(` floor, layer-id/rank/worksheet cross-checks, no inline datasets,
  `data/app/` presence + counts, sw exactly-one-list, `METRO_EXPLORERS` lint, engine
  fence lint.
- `BASE_URL=… node scripts/smoke_test.mjs` — behaviour gate (real Chromium): boot, all
  layers register, ground-truth classification, re-highlight second point, roster-join
  label render, failure isolation (killed source → isolated error card + Retry),
  coverage-hide + permalink stability, alias shim. Sandbox note: the SessionStart hook
  vendors Leaflet (`scripts/vendor_leaflet.sh`) because headless Chromium can't reach
  the CDN through the agent proxy — environmental, never a code regression.
- `python3 scripts/check_engine_parity.py index.html` — fence lint (also inside
  validate_index); `--against <sibling> --strict` for byte comparison.
- `python3 scripts/generate_metro_files.py --check` — generated-region drift.
- `python3 scripts/validate_sources.py` — monthly freshness (see 6.3).
- `scripts/fleet_status.py` (weekly, Chicago only) — deploy/engine-pin/roster state per
  fork + guidebook coverage-map diff; WARNs on a standing issue.

## 6.6 Post-expansion operations

Every expansion leaves standing obligations: the weekly roster workflows it added
(staggered cron slots; the live schedule is CLAUDE.md's generated metro-facts block);
its `validate_sources.py` manifest rows; `WATCH.md` (the per-fork operations calendar —
localize it in forks); guidebook rows kept current (fleet-status WARNs on drift); and
**redistricting exposure** — every new boundary layer gets a blast-radius row in
`docs/REDISTRICTING_RUNBOOK.md`'s inventory, and pre-built geometry ties its rebuild to
that runbook's triggers (decennial, court-ordered, administrative, annual school-zone
rotation).

---

# APPENDIX A — The 39-layer classification (audit of record, 2026-07-27)

Classification is this guide's; **counts, sources, and roster provenance live in
`docs/DATA_LAYER_GUIDEBOOK.md`** (machine-checked weekly). Statewide story: DONE =
already statewide · ENTRY = counties join as dispatch entries · ROSTER = counties join
as roster rows · GATED = honest instance of a general concept, generalized through a
different concept/card · UNIQUE = recorded Chicago/Cook-only.

### Political (11)

| id | Answers | Level | Elected by | Statewide story |
|---|---|---|---|---|
| `congress` | your U.S. House rep | Federal | district | DONE |
| `il-senate` / `il-house` | your state legislators | State | district | DONE |
| `il-supreme-court` | your Supreme Court district | State (judicial) | district (5) | DONE · Appellate-row candidate (§1.5) |
| `judicial-subcircuit` | your resident-judge subcircuit | State (judicial), county-organized | subcircuit; structurally n/a in some circuits | ENTRY · statewide circuit DERIVE blocked |
| `county-board` | your county-board district + member | County | district (metro); commission counties at-large | ENTRY where districted · county-card rows where at-large |
| `ccbr` | your Board of Review district | County | district — elected only in Cook | UNIQUE · elsewhere appointed → link row at most |
| `school-board` | your ERSB district + member | School district | district — IL's only districted school board | UNIQUE as polygon · elsewhere Pattern A (§1.5) |
| `ward` | your alderperson / council member | Municipal | ward or council district | ENTRY — the consolidated municipal-ward concept, dispatch keyed by municipality (Chicago + suburban Cook + Evanston + Will cities + Aurora shipped 2026-07); new ward-publishing sources join as entries |
| `ward-precinct` | your Chicago precinct | Election administration | n/a | GATED — authority-dispatched concept (§1.3) |
| `early-voting` | nearest early-voting/drop-box sites | Election administration | n/a | GATED — per-authority files (§1.3) |

### Safety (7)

| id | Answers | Level | Elected by | Statewide story |
|---|---|---|---|---|
| `police-district` | your CPD district + station | Municipal dept | n/a (labeled) | GATED — general concept = card rows + Sheriff (§1.5) |
| `police-beat` | your CPD beat | Municipal dept | n/a | UNIQUE (`subOf police-district`) |
| `ccpsa-district-council` | your elected police-oversight council | Municipal | district (22) | UNIQUE — no analog anywhere in the fleet |
| `fire-district` | which FPD taxes/serves you | Special district | trustees typically appointed; card follows source depth | ENTRY · municipal fire depts excluded by rule |
| `dupage-county-special-police` | township special-police tax area | Township special district | n/a (funds elected Sheriff) | single-county; converts only on a second analog |
| `police-station` / `fire-station` | nearest stations | amenity | n/a | DONE-capable (USGS national; bbox widens) |

### Schools (9)

| id | Answers | Level | Elected by | Statewide story |
|---|---|---|---|---|
| `school-district-{unified,secondary,elementary}` | which district serves/taxes you | School district | board elected whole-district (ERSB the exception) | DONE (identity) · Pattern A enrichment candidate |
| `cps-network` / `cps-hs-network` | your CPS admin network + chief | District internal | n/a (appointed, labeled) | UNIQUE (mega-district phenomenon) |
| `cps-elementary` / `cps-middle` / `cps-high` | your zoned school | School district | n/a | GATED — per-district opt-in class, never statewide |
| `school-site` | nearest schools | amenity | n/a | Chicago-sourced · statewide source candidates recorded |

### Geography (12)

| id | Answers | Level | Elected by | Statewide story |
|---|---|---|---|---|
| `county` | your county + clerk | County | clerk county-wide | DONE · officer-roster enrichment per rule 4; at-large boards land here |
| `township` | your township / county subdivision | Township | officers township-wide | DONE (identity) · officer candidate via clerk yearbooks; Chicago structural empty |
| `municipality` | your municipality + its government | Municipal | head municipal-wide; board at-large or by ward | DONE (identity) · ROSTER per county (Part 2.4) · Chicago head + citywide officers SHIPPED |
| `county-precinct` | your voting precinct (+ polling place) | Election administration | n/a | ENTRY per authority · Kendall polling-place join is the model |
| `park-district` | which park district serves you | Special district | elected commissioners | ENTRY · McHenry recorded gap |
| `library-district` | which library body taxes you | Special district | district trustees elected; municipal funds appointed | ENTRY · complete-tiling rule |
| `mwrd` | in/out of the MWRD | Special district | nine at-large commissioners → link row | Cook body UNIQUE; class conversion trigger (§1.5) |
| `tif-district` | your TIF district | Municipal finance overlay | none | Cook today · Kendall conversion trigger |
| `community-area` | your Chicago community area | Reference | none | UNIQUE — correctly city-only |
| `zip-code` | your ZCTA | Reference | none | DONE |
| `post-office` | nearest post offices | amenity | n/a | DONE-capable (USGS national) |
| `library` | nearest library branches | amenity | n/a | Chicago (CPL) · statewide candidate recorded; `library-district` answers governance |

# APPENDIX B — Doc map

**This guide is the only entry point for expansion work.** Deliberately separate, live:

- `docs/DATA_LAYER_GUIDEBOOK.md` — the fleet layer **registry**: coverage map
  (machine-checked weekly), concept × metro matrix, recorded drops, backlog. Updated in
  the same change as any layer add/rename/remove.
- `docs/ENGINE_SYNC.md` — the engine parity **protocol** (ships verbatim in every fork).
- `docs/CARD_RENDER_API.md` — the card-helper **API reference**.
- `docs/REDISTRICTING_RUNBOOK.md` — the boundary-change **ops runbook** (blast-radius
  inventory, decennial + off-cycle triggers).
- `WATCH.md` — the per-fork operations calendar. `CLAUDE.md` — agent instructions + the
  generated metro-facts block (live counts/schedules).

**History & records** (frozen, provenance only): `docs/archive/` —
`METRO_EXPANSION_PLAYBOOK.md` (original Part I + the NYC worked example Part II),
`METRO_EXPANSION_NYC.md` (NYC thread log), `METRO_EXPANSION_SF_WORKSHEET.md` (completed
SF worksheet), `STATEWIDE_EXPANSION_PLAYBOOK.md`, `COUNTY_LAYER_CONSOLIDATION.md`,
`MUNICIPAL_COUNCILS_PLAYBOOK.md` (decision records this guide absorbed),
`MECHANIZATION_PLAYBOOK.md` (conversions 1–3, done). Root-level:
`docs/BUILD_PLAYBOOK_1.md` (original build log; CLAUDE.md wins on contract language),
`docs/OPTIMIZATION_PLAYBOOK.md` + `docs/PERFORMANCE_ANALYSIS_2026-07.md` (dated
measurement records), `docs/COUNTY_SEALS_REVIEW.md` (marker-art tracker),
`docs/engine-changelog/` (per-release notes), `docs/design_handoff_*/` (design records).

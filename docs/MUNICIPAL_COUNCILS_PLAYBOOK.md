# Municipal Councils — sourcing & deployment for suburban municipal governing bodies

Status: **Cook + Will SHIPPED (2026-07-27) — scrapers, builder, weekly workflow, and
the Municipality card join are live (156 municipalities, 958 board members, 184
ward/district seats); the other five counties are sourced and specified but unbuilt.**
Every source below was live-fetched twice (independent research + adversarial re-verification)
on 2026-07-27; officeholder entries were sighted in each positive source, and every negative
finding was independently confirmed.
Owner: CHI (fork-level — no engine change). Cross-refs: `docs/COUNTY_LAYER_CONSOLIDATION.md`
(rule 4 governs the sourcing; the "What does NOT consolidate" note explains why this is not a
county-dispatched layer), `docs/DATA_LAYER_GUIDEBOOK.md` (backlog entries until it ships),
`docs/STATEWIDE_EXPANSION_PLAYBOOK.md` §4/§8 (the statewide "link-only" stance this carves out),
`docs/METRO_EXPANSION_PLAYBOOK.md` §3 step 4 (port-time checklist hook).

## The concept

For any clicked point inside an incorporated municipality, the card should answer: who
governs this municipality — mayor / village president, the city council / village board of
trustees, plus office location, contact, and the official website. Today the `municipality`
layer is an identity-only compact card (TIGERweb Places layer 4, name + GEOID). Chicago is
excluded throughout — its council is the `ward` layer.

**Decided shape: enrich the existing `municipality` card, not a new layer.** The layer stays
the statewide single-source tiling it is; an officeholder roster joins it the way
`il-county-clerks.json` joins the `county` card (the exact precedent — grep `countyClerkFor`).
Where the roster has no entry for a place GEOID the card degrades to today's name-only
compact card, so statewide behavior outside the metro is unchanged and no `coverage`
declaration is needed. `registerCountyLayer` is the wrong tool here: it dispatches disjoint
per-county footprints, while municipalities are one statewide tiling — **the county is the
sourcing dimension, not the dispatch dimension.**

**Ward-elected councils — the `county` / `county-board` split applies.** The fleet already
answers this two-body question at the county level: `county` (geography) carries the
whole-unit officer (the clerk), while `county-board` (political) resolves *which district
you are in* and names your commissioner. Municipalities divide identically:

- **Whole-municipality officers** — mayor/village president, clerk, treasurer, at-large
  trustees — are answered by the municipality polygon itself; every point in the city gets
  the same correct answer. That is this roster enrichment.
- **Ward/district-elected alderpersons** need ward polygons to answer *yours*, and only
  Cook, Will, Evanston, and Aurora publish them (Tier B below). Until that ships, a
  ward-elected city's card lists the **full council with each member's ward as their badge**
  ("Ward 3 Alderperson") behind a details expander — honest and complete, simply not
  point-discriminating. When Tier B lands it nests `subOf municipality` (the
  ward → ward-precinct precedent) and answers "your alderperson" while this card keeps
  answering "your mayor".

**Consequence for Phase 1 (load-bearing):** the roster must carry a per-member `district`
field from day one even though nothing consumes it yet. Cook's API supplies it directly
(the 135 MUNIW alderperson records carry `Jurisdiction: "City of Berwyn, Ward 1"`) and the
Will directory prints district numbers. Capturing it now makes Tier B a geometry-and-dispatch
change with **no roster rebuild and no re-scrape**. Only Cook and Will are affected — the
other five counties' sources publish no council members at all.

## Scale (verified)

**284 unique municipalities** across the seven counties (CMAP: "7 counties, 284
municipalities"). Census 2020 place-by-county counts (FUNCSTAT=A incorporated places):
Cook 136 · Lake 52 · DuPage 39 · Will 37 · Kane 30 · McHenry 30 · Kendall 14 = 338
county-appearances, i.e. **47 municipalities span county lines** and must be deduped.
Canonical dedup reference:
`https://www2.census.gov/geo/docs/reference/codes2020/place_by_cou/st17_il_place_by_county2020.txt`
(pipe-delimited; commit a copy under `data/source/`). **Key everything by 7-digit place
GEOID (17 + PLACEFP)** — it is exactly the `GEOID` the app's TIGERweb `municipality` layer
already fetches, so the roster join needs no name normalization at query time.

## Per-county sources (all verified 2026-07-27)

| County | Source | Coverage | Depth | Fetch class |
|---|---|---|---|---|
| **Cook** | Clerk **Directory of Elected Officials JSON API** — `https://www.cookcountyclerkil.gov/api/ElectedOfficial/GetByJurisdictionType?id=MUNIS&language=en` (+ `id=MUNIW` ward alderpersons; `GetByTaxCode?id=<taxcode>` per-muni; enumerate via `/api/Jurisdiction/GetByJurisdictionType?id=MUNIS`) | 128 suburban munis, 1,134 records | **Full governing body** — mayor/president, trustees, alderpersons, clerk, treasurer; term dates (LastElected/NextElection); office address/phone/email/website per record | Open unauthenticated JSON. Cloudflare-fronted: WebFetch-class clients 403, plain curl/requests 200 (as of verification). April-2025 consolidated-election data confirmed loaded. The portal's Socrata copies (`vw2r-zys4`, `jsup-zs8y`) are **2014-frozen — never use** |
| **Will** | Clerk **"Will County Directory"** — FlipHTML5 flipbook (book `hbvu/bbmp`), plain-HTML chunks at `https://fliphtml5.com/hbvu/bbmp/basic` (+ `/basic/51-100` …); **discover the link from willcountyclerk.gov's nav** ("Will County Directory"), never hardcode the book id | all 37 munis touching Will (incl. cross-county Aurora, Naperville, Tinley Park, Woodridge, Oswego, Minooka) | **Full governing body** — mayor/president (party, term-expiry), clerk, treasurer, every trustee/councilmember; hall address/phone/email/website | Flipbook itself fetches clean; willcountyclerk.gov serves 202/empty to non-browser UAs — use a browser UA. Updated in place (edit sighted 2026-07-15), fed by the clerk's Entity Change of Information process |
| **DuPage** | **DMMC Membership Directory PDF** — discover the date-stamped URL from `https://dmmc-cog.org/membership-list/` (2025-26 edition: `.../2025/08/Membership-Directory-25-26-8.4.2025-1.pdf`) | 35 of 39 munis + 1 associate; the ~4 sliver munis (e.g. Elk Grove Village, St. Charles) are covered by their home counties | Mayor/president + manager/administrator + website/hall address/phone. **No trustees** | Clean fetch; 2-page text PDF, highly regular entries; refreshed annually (county government itself publishes nothing municipal — verified negative) |
| **Kane** | Clerk **Government Guide PDF** — `https://clerk.kanecountyil.gov/Elections/Documents/GovernmentGuide.pdf` (stable URL; anchor "Government Guide" on `/elections`) | all 29–30 munis | Mayor (5 cities) / village president (24 villages) + municipal clerk + website/address/phone/email. **No trustees** | Clean fetch; 84-page text PDF, "Cities and Villages" section; annual (2025-26 edition, Last-Modified 2026-05-22) |
| **McHenry** | Clerk **County Yearbook — Cities & Villages** page — `https://www.mchenrycountyil.gov/county-government/county-yearbook/cities-villages` | all ~28 munis | President/mayor + clerk + administrator/manager + address/phone/email/website. **No trustees** | Akamai-fronted: 403s plain curl **even with a browser UA**, but browser-context fetch works, and — correcting the repo's standing note — **archive.org now HAS snapshots of this domain** (cities-villages captured 2025-03-06; homepage 2026-05-27), so the wayback rung is live again. Full engine ladder |
| **Kendall** | Clerk **Yearbook & Government Guide PDF** — `https://www.kendallcountyil.gov/home/showdocument?id=184` (CITY OFFICIALS / VILLAGE OFFICIALS sections) | all 14 munis | Mayor/president (+ election date) + municipal clerk + treasurer + address/phone/website. **No trustees** | Akamai 403s plain curl; browser-context fetch retrieved the full 70-page PDF. Updated 2026-06-30. Playwright rung day one |
| **Lake** | **No officeholder names published county-side — firm double-verified negative** (Clerk, GIS hub, and Municipal League all checked). Use Lake GIS **Municipalities FeatureServer** — `https://services3.arcgis.com/HESxeTbDliKKvec2/arcgis/rest/services/Municipalities/FeatureServer/0` | all 52 munis | Hall address, phone, fax, email, official-website URL per muni. **No names** → rule-4 branch 3: identity + office + contact + link only; gap recorded in the guidebook | Open ArcGIS query, actively maintained (edited 2025-06). lakecountyil.gov itself 403s datacenter egress |

**Statewide aggregators: verified dead end.** IL Comptroller's Local Government Registry
(identity/contact only; its "CEO" is frequently the appointed manager — unusable as "mayor"
under the never-guess rule), IML directory (paid print), ISBE (no local results/officials),
Census GUS (no names), Ballotpedia (partial), Wikidata (sparse), Google Civic (representatives
endpoint sunset), Cicero (commercial). Full council rosters exist only in the county sources
above or on individual municipal sites — the per-county architecture is not a preference,
it is the only honest option.

## Merge & precedence (the 47 multi-county municipalities)

Merge per-county intermediates keyed by place GEOID via the Census place-by-county file.
When a muni appears in several sources, take the **deepest** source, not the home county:

1. Full governing body — Cook DOEO, Will Directory
2. Mayor-level — Kane Guide, Kendall Yearbook, McHenry Yearbook, DMMC
3. Contact-only — Lake GIS

Example: Aurora (home Kane, mayor-only there) takes its full council from the Will
Directory, which covers every municipality touching Will. Record the winning source per
entry (`sourceUrl` on every record, per the honesty rules); never blend member lists from
two sources.

## Pipeline spec

Follows the repo's scraper → builder → weekly-PR pattern verbatim
(`docs/archive/MECHANIZATION_PLAYBOOK.md` "Deliberately NOT mechanized": roster changes are
always human-reviewed via PR on a fixed bot branch).

- **Seven scrapers**, one per source, each emitting intermediate JSON with `source_url` +
  `scraped_at` per record, `null` for unparseable fields:
  `cook_municipal_officials_scraper.py` (two bulk API GETs: MUNIS + MUNIW; plain requests;
  Playwright rung only if Cloudflare tightens) ·
  `will_municipal_officials_scraper.py` (nav-discover flipbook → `/basic` chunk parse;
  browser UA) ·
  `dupage_municipal_officials_scraper.py` (discover current PDF from membership-list page;
  pypdf) ·
  `kane_municipal_officials_scraper.py` (stable PDF URL; pypdf) ·
  `mchenry_municipal_officials_scraper.py` (full engine ladder requests → Playwright →
  wayback; wayback is viable again for this domain) ·
  `kendall_municipal_officials_scraper.py` (Playwright day one; pypdf) ·
  `lake_municipal_officials_scraper.py` (ArcGIS query; contact fields only).
- **One builder** `build_municipal_officials_roster.py` → `data/app/municipal-officials.json`:
  `{ "<geoid>": { name, county, head?: {name, role}, board?: [{name, role, district?}],
  officers?: [{name, role}], office?: {address?, phone?, email?}, url?, sourceUrl } }`.
  Every people key is **omitted entirely** where the source names nobody (Lake) — never
  an invented or empty-guess list. `district` is captured whenever the source carries it
  (Cook MUNIW, Will) even though no consumer exists until Tier B — that is what keeps the
  ward layer a geometry-only follow-up.

  Three shape decisions the Cook build settled, which the remaining counties inherit:
  - **Contact is municipality-level, not per-person.** Verified in the Cook source: all
    128 municipalities carry one shared hall phone/email/address across every official,
    and the per-person `PersonPhone`/`PersonEmail` columns are empty for all 1,134
    records. It therefore lives once under `office` and renders on the hall row —
    attaching a shared village-hall address to a trustee's row would imply a direct line
    that does not exist.
  - **head / board / officers, not a flat `members` list.** The card renders three
    distinct sections (head of government, the governing body, other elected officers
    like clerk and treasurer), and the split is what lets a mayor-level county ship a
    `head` with no `board` and stay honest rather than padding a list.
  - **Cross-county municipalities resolve by DEPTH, then county order.** Six
    municipalities are listed by both the Cook and Will clerks (Lemont, Orland Park,
    Park Forest, Steger, Tinley Park, University Park). `entry_depth()` ranks a source
    by what it actually names — full body (2) > head only (1) > contact only (0) — and
    only when depths tie does `COUNTY_PRECEDENCE` break it, Cook first because its API
    reflects each election as certified while Will republishes annually. The builder
    refuses to write if the dropped entry had a board and the kept one did not, so a
    precedence mistake fails loudly instead of silently thinning a card.
  - **Library Trustees are excluded** — they sit on library district boards (the app's
    separate `library-district` layer), not the municipal governing body. In the Cook
    source they are 255 of the 1,134 records and are distinguishable structurally as
    well as by office name (their address carries AddressTypeId 4, not 3).
  Count guards (`sys.exit(1)` under any floor): per-county muni floors cook ≥120 · will ≥35
  · dupage ≥33 · kane ≥27 · mchenry ≥26 · kendall ≥13 · lake ≥48; member floors cook ≥900
  records incl. ≥500 trustees, will ≥150; merged total ≥270 of 284. Stable key order for
  clean diffs.
- **One workflow** `update-municipal-officials.yml` — weekly, Wed 14:00 UTC (after CCPSA's
  Wed 13:00). Each scraper step `continue-on-error: true`; a blocked source converts to its
  own standing tracking issue (title-searched, the validate-sources pattern) while the other
  six proceed; build + PR (fixed branch `bot/municipal-officials-update`) gated on every
  *required* scrape either succeeding or being covered by a fresh (≤45-day) archive rung.
  `ARCHIVE_SPN_*` secrets wired for the wayback rung.
- **New dependency:** `pypdf` pinned in `scripts/requirements.txt` — the repo's first PDF
  parser (verified against the DMMC and Kane PDFs during research).
- **Bookkeeping (the standard eight-artifact checklist):** worksheet `data_files.rosters`
  entry (`municipal-officials.json`, min_keys 270) + `workflows` entry + `sw.cache_name`
  bump → `python3 scripts/generate_metro_files.py`; `validate_sources.py` PROVENANCE ×7
  (note expected-WARN for the Akamai-fronted McHenry/Kendall URLs and bot-gated
  willcountyclerk.gov); `index.html` references the file (required by validate_sources
  check 1).

## App join spec

Rewrite the `municipality` `registerPolygonLayer` call as an explicit `registerLayer` block
on the `county`-layer template (grep `loadIlCountyClerks` for the whole pattern):
`Promise.all([loadIlPlaces(), loadMunicipalOfficials().catch(function(){return {};})])` —
roster failure isolated so the identity card always survives; `seq` threaded per the
stale-async invariant. Card in the fleet order (identity → representative → location →
contact → link): name + GEOID meta preserved → mayor/president via `renderPersonRows`
(badge = the source's actual title — "Mayor", "Village President") → board via
`renderSectionLabel("Council" / "Village Board")` + person rows (details-expander for long
boards; ward-elected members badge their seat, "Ward 3 Alderperson", from the roster's
`district` field) → `renderOfficeGroup` (hall address/phone) → `primaryLink` (official
website).
`hoverOfficial` names the mayor/president. Mayor-level counties render mayor + link and
**no board section** (absent data renders nothing); Lake renders office/contact/link only.
The explicit block raises the raw `registerLayer(` count by one — the validator floor is a
floor; no id-list change (`municipality` is already in `EXPECT_LAYER_IDS` and
`LAYER_AREA_RANK`), and the layer count stays 39.

Two implementation notes from the shipped Cook build:
- **The layer leaves the 4b compact presentation.** `mod.compact` is decided once at
  card-construction time and *skips `render()` entirely on success*
  (`runLayerQueryAt`), so a card cannot be compact for an unsourced municipality and
  full for a sourced one. `municipality` therefore renders the standard card — name +
  FIPS via `renderBodyIntro`, exactly as `county` does. This is the same trade `county`
  already made, and it is what makes room for the officials rows.
- **The body and hall labels follow the municipality's own legal form**, derived from
  the source's name string: trustees sit on a "Board of Trustees" and alderpersons on a
  "City Council"; "Village of Alsip" yields "Village Hall", "City of Berwyn" yields
  "City Hall". Both fall back to neutral labels rather than asserting a form the roster
  does not evidence.

## Tier B — suburban municipal wards (SHIPPED 2026-07)

Some suburbs elect by ward; resolving *which alderperson* needs ward polygons. These
shipped as **entries of the existing `ward` layer**, keyed by municipality — the same
toggle and the same place in the Political group a Chicago ward answers from, which is
the point: the concept is one council seat whether Chicago calls it a ward or Joliet a
council district. `registerCountyLayer` needed no change beyond accepting `entries` as
a synonym for `counties`; the dispatch only ever required disjoint footprints.

Seat-holders join `municipal-officials.json` by municipality name + seat number, so a
ward card can never name someone different from the Municipality card's list. Where a
source publishes its own per-seat attributes they compose on top — Evanston's service
carries each alderperson's email, phone and ward page, which the roster has no
per-member equivalent for. Per-seat contact is shown ONLY from such a source: the
roster's phone/email are the shared hall line and would be a false implication on an
individual's row.

Coverage is a prebuilt same-origin outline file (`data/app/municipal-ward-coverage.json`,
`build_municipal_ward_coverage.py`) rather than the live services, because the engine
evaluates `coverage` for every declaring layer on every point selection — deriving it
from the sources would pull four ArcGIS payloads on the first click anywhere in
Illinois. Chicago sits first in the dispatch table so its already-cached coverage test
short-circuits the OR and most traffic never fetches that file at all.

The sources:

- **Cook GIS `politicalBoundary/MapServer/22` "Municipal Ward"** — 169 polygons, all 22
  ward-electing munis incl. 21 suburbs (Berwyn, Des Plaines, Park Ridge, Palatine, Skokie
  incl. its new 2025 trustee districts, Oak Lawn, Calumet City, Chicago Heights, Harvey,
  Blue Island, …); fields MUNICIPALITY/NUMBER/TYPE; actively maintained; filter
  `MUNICIPALITY <> 'Chicago'`. **Joins the DOEO `MUNIW` roster (135 alderpersons) — same
  publisher, clean key.**
- **Will GIS `Ward_Districts` FeatureServer** (`services.arcgis.com/fGsbyIOAuxHnF97m`) —
  Joliet Council Wards, Lockport, Crest Hill, Wilmington (Joliet's own GIS is broken;
  the county layer is the source).
- **Evanston** (`maps.cityofevanston.org` OpenData2Administrative L0, 9 wards) and
  **Aurora** (`gis.aurora.il.us` 2022Wards FeatureServer, + the city's published 12-member
  aldermen roster) self-publish.
- Verified negatives: no county-level municipal-ward layers in Lake/DuPage/Kane/McHenry/
  Kendall; Waukegan publishes a PDF map only.

Recorded gaps: **Berwyn** elects 8 alderpersons by ward but is absent from Cook's ward
layer and from every other published source, so its seats show on the Municipality card
with no ward behind them. **Skokie** is the inverse — Cook's layer carries its 2025
trustee districts while the Clerk's roster still lists its trustees as at-large, so a
Skokie point resolves a district with no seat-holder joined. Both are recorded in the
guidebook backlog rather than papered over.

## The future-county source ladder (the repeatable recipe)

When any new county (or a sibling metro's county) ships, municipal-government sourcing is
decided **in the same change** (COUNTY_LAYER_CONSOLIDATION rule 4 — this ladder is the
municipal instantiation of its decision tree). Check in order; take the first hit;
record the outcome in the guidebook either way:

1. **County clerk elected-officials database/API** (Cook's DOEO class — check for an
   XHR/JSON backend behind any "elected officials" search app before settling for PDFs).
2. **County clerk directory/yearbook document** (Will's directory, Kane/Kendall/McHenry's
   yearbooks — HTML page, PDF, or flipbook; expect mayor-level depth, full-body if lucky).
3. **Council-of-governments / mayors-conference directory** (DuPage's DMMC class —
   verify currency and coverage; usually mayor + manager only).
4. **County GIS municipal-boundary attributes** (Lake class — office contact/website
   riding the polygons; contact-only card).
5. **Link-only** — the rule-4 honesty floor: identity + official-website link, gap
   recorded in the guidebook. Never guess; never scrape 50 heterogeneous municipal sites
   as a default (that is a deliberate, per-muni upgrade decision, not a source of record).

Fetch posture mirrors the county-board ladder: cheapest engine that works, escalating
requests → Playwright → wayback, with the 45-day snapshot age guard and standing-issue
conversion for total blocks.

## What the Will parse cost (read this before building the PDF counties)

Will was ~10x the work of Cook, and all of it was the source format rather than the
pipeline. The flipbook's `/basic` rendition is **PDF text with the line breaks
removed**, which produces failure modes worth naming in advance because the four
remaining PDF counties will hit the same class:

- **Labels glue to their neighbours** — "Stacey PetersonAlderperson Ward 1",
  "AlderpersonWard 1", "Term ExpiresMichael W. Glotz". Word-boundary anchors (`\b`)
  silently fail on these, and the section header then matches a *later* occurrence,
  which quietly halves a council. Match section headers as plain substrings,
  longest-first.
- **A repeated section header is absorbed into the following name** —
  "Councilmembers At Large Joe Clement" parsed as one 4-word name. Blank every header
  occurrence out of the section before scanning members.
- **"At Large" labels a group, not a seat** — it must stay in force until the next
  Ward/District seat, or only the first at-large member gets it.
- **Names carry parenthetical nicknames** ("Teresa (Terry) A. Kernc"), curly-quoted
  ones ("Sharon “Sherri” Reardon"), and comma suffixes ("Joseph E. Roudez, III").
  A party-code group `(IND)` is distinguishable from a nickname only by being ALL-CAPS.
- **A lazy trailing-word quantifier needs an anchor.** Board members end in a
  term-expiry year, which forces the name to expand; clerk/treasurer lines have no
  such anchor, so the same pattern shipped "Laura" for "Laura Warren". Officer names
  need a greedy variant that refuses to cross into the next label.
- **Addresses can be undelimitable.** A preceding precinct list runs straight into the
  street number. Where the join carries a separator the split is clean ("…3P625 Dixie
  Highway", "…35P 44 E. Downer Pl."); where the last precinct token is a bare number
  there is nothing between them ("…18P & 19150 W. Jefferson St." is precinct 19 + 150
  W. Jefferson) and the street number cannot be recovered. Those return None — one
  municipality (Shorewood, whose address also begins with a word, "One Towne Center
  Blvd.") ships with no address line rather than a guessed one.

The lesson for the PDF counties: parse the real PDF with a layout-preserving reader
(`pypdf` with layout mode, or `pdfplumber`) rather than a line-flattened rendition,
and only fall back to flattened text where no PDF is reachable. Every one of the
failures above is an artifact of losing line breaks, not of the data.

## Verification

- **Pipeline PRs:** builder floors + `validate_index.py` (+ `generate_metro_files.py
  --check` after the worksheet edit).
- **App-join PR:** Playwright smoke test, plus a point sweep of the card. **Verified for
  Will (2026-07-27):** Joliet → Mayor Terry D'Arcy, 5 district councilmembers + 3
  at-large; Aurora's 12-member council matches the city's own published roster
  name-for-name (10 wards + White and Larson at-large — the independent check that the
  parse is right); Diamond → its commission-form board; Shorewood → hall row with no
  address line (the undelimitable case); Tinley Park → the Cook entry, proving
  precedence. **Verified for Cook (2026-07-27):** Berwyn → Mayor Robert J. Lovero, a "City Council" section of 8
  alderpersons each badged with their ward, Clerk + Treasurer, and City Hall with
  address, formatted phone and Email link; Alsip → President John D. Ryan, a "Board of
  Trustees" of 6, Clerk, Village Hall; Chicago Loop → identity only (excluded by
  concept); Naperville → identity only (county not yet sourced); an unincorporated point
  → the honest empty card. Remaining to verify as their counties land: a Joliet point's
  full council (Will Directory), a Wheaton point mayor + link only (DMMC), a Waukegan
  point office/contact/link only (Lake).
  Note for anyone re-running this in the Claude Code sandbox: Chromium cannot reach live
  APIs through the agent proxy, so the municipality layer errors there by default (its
  geometry is live TIGERweb). Fetch the places payload with `curl` and serve it back via
  `page.route` to exercise the real query/render path — the same trick
  `smoke_test.mjs` uses for Leaflet.
- **Monthly freshness:** the seven PROVENANCE entries keep `validate_sources.py` watching
  for moved PDFs/pages (the DMMC URL *will* move annually by design — the scraper
  discovers it, the manifest pins the discovery page, not the PDF).

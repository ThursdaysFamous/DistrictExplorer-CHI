# districtry Michigan — the expansion plan and its running record

> **SHIPPED 2026-09-03 — phases 1, 2 and go-live, in three PRs on one day.** Michigan is live at
> districtry.com/mi/ with 10 layers. **The running status is the Status table near the foot of this
> file; what is left is under Still open.** What go-live actually cost is recorded here because it
> was almost entirely NOT on any checklist.
> **Four defects had survived the full 38-gate battery twice, and three were the same shape — a
> claim nothing compared against the thing it claimed.** (1) `mi/fonts/` did not exist while
> `mi/index.html` declared 18 `@font-face` rules against it, and `mi/og-image.png` did not exist
> while three tags named it: the app would have served in system fonts forever and every social
> share would have been broken, with no error anywhere. `scripts/validate_instance_assets.py` is
> the new gate, and it had to be fixed mid-write — its first draft scanned `src`/`href` only,
> caught the fonts, and sailed straight past the og-image, which lives in a `content=` attribute.
> (2) `mi/sources.html` served **Iowa's entire identity block** — canonical, `og:url`,
> `og:site_name`, title and the whole ld+json graph — because the page was cloned from Iowa and
> only its GENERATED regions were ever regenerated; a canonical pointing at a sibling asks Google
> to drop this page in favour of that one. `page_consistency_test.mjs` passed it, because its check
> was `!!document.querySelector("link[rel=canonical]")` — whether the tag was THERE, never what it
> SAID. (3) A dead `tigerStatewideLoader`, inherited from Iowa and never called, made
> `build_privacy_page.py` publish that a Michigan layer sends your exact selected point to a
> government server, when none does. (4) **The fleet bbox is the portal hand-off box, not
> `metro_bbox`**: Michigan's water-inclusive fabric put Chicago's and Wisconsin's own centres inside
> Michigan's box and hard-failed `validate_index.py` on both — found only because the per-instance
> `validate_index` block had been skipped in favour of a remembered subset of the battery. **Run the
> workflow's own command list.** The western-UP counties that fall outside the narrowed box are
> recorded in `mi/WATCH.md`. **That record named a fix and the fix was wrong**: a smallest-bbox-AREA
> tie-break measures no better than the nearest-CENTRE rule it would replace (7 wrong of 37 either
> way, just at different places). #698 routed the front door against each instance's real coverage
> ring instead — 7 misroutes of 28 down to 4 — and four counties remain, for a reason that is not a
> tie-break at all.
>
> Two things go-live did NOT need, contrary to the guide: no sibling `CACHE_NAME` bump (the sibling
> change is confined to the network-first shell), and this file does not move to `docs/archive/` —
> neither Iowa's nor Wisconsin's plan did.

> Planning document, researched and verified 2026-09-03. `docs/IA_EXPANSION_PLAN.md` is the
> precedent for a committed phase plan; like it, this file STAYS IN `docs/` and is APPENDED TO
> when a phase ships (the header used to say it moves to `docs/archive/`; git says otherwise —
> Iowa's go-live commit 258022d appended 43 lines to `docs/IA_EXPANSION_PLAN.md` and renamed
> nothing, and the only archived plan, `docs/archive/WI_PHASE2_PLAN.md`, closed a PHASE rather
> than a go-live). The shipped instance (`mi/metro-worksheet.json`, `mi/CLAUDE.md`, the
> guidebook's Michigan column) supersedes it as the record of what IS; this stays the record of
> what was decided and why. Sources marked **VERIFIED** were fetched or queried on
> 2026-09-03 — endpoint, count, licence and failure mode recorded from the response, not from a
> catalog page. Facts marked **ASSERTED** are Michigan civic-structure claims carried from the
> research pass without a second independent fetch; each must be pinned to a primary citation in
> the PR that ships it, per `docs/EXPANSION_GUIDE.md`'s honesty rules.

## Why Michigan, and why now

The fleet was five instances when this was written on 2026-09-03 (Michigan made it six the same day): Illinois (91 counties, the reference
implementation), NYC, SF, Wisconsin (all 72 counties) and Iowa (all 99). Michigan was chosen as
the sixth from a five-state recon pass across the states bordering the existing
Illinois/Wisconsin/Iowa footprint, scored on one question: **does a single statewide publisher
carry county-board-district boundaries for every county?** That is the trait that made Wisconsin
and Iowa fast builds and whose absence made Illinois a county-by-county grind of 91 separate
research problems.

| Candidate | Verdict | The measurement |
|---|---|---|
| **Michigan** | **GREEN** | One state-owned layer, **83/83 counties in a single query** |
| Indiana | YELLOW | IGIO's Data Harvest is real but voluntary — **65/92 counties** across two vintages; the rest would be Illinois-shaped work |
| Nebraska | YELLOW | NebraskaMap hosts county-board layers **owned per county**, not one aggregate |
| Minnesota | RED | The Secretary of State states outright it has no commissioner-district maps online; MnGeo's statewide catalog carries none either; the shapefile page is bot-gated |
| Missouri | RED | No statewide aggregate; county government genuinely fragmented (valuation classes + a township-organization overlay in ~20 of 114); the SOS **sells** precinct results |

## The thesis: Michigan arrives with Wisconsin's shape, not Iowa's or Illinois's

Wisconsin's arrival keyed on one state-publisher layer, shippable because Wis. Stat.
5.15(4)(br) forces every county to file its district plan with the state. **Michigan has the
same shape and the same reason.** MCL 46.404/46.405 (ASSERTED — to be pinned in the PR that
ships the layer) requires each county's apportionment commission to file its adopted plan, and
the Department of State's Bureau of Elections compiles those filings into
**`2021 County Commissioner Districts v25`** —
`gisagocss.state.mi.us/arcgis/rest/services/OpenData/boundaries/MapServer/10`, **VERIFIED: all
83 county names returned by a single distinct-values query**, fields `CountyFIPS, County,
DistrictCode, DistrictName, Population, Commissioner, Party`.

Three things separate it from Iowa's flagship, and all three are in its favour:

- **The licence is stated, not merely absent.** Iowa's supervisor layer carries a null
  `licenseInfo` and an attribution-only posture inferred from silence. Michigan's AGO item
  (`4c8d0d854ac04d8787cb3cf6dab7fbec`) states it outright — **VERIFIED, verbatim**: "this
  dataset is a public record and…there are no restrictions on the use, reproduction, or
  distribution of this dataset". Note the Hub *site* item separately carries a site-wide
  `CC-BY-SA`; the dataset's own custom licence is what governs, and the two must not be
  conflated.
- **It carries people, not just polygons.** `Commissioner` and `Party` are **VERIFIED
  populated** on sampled records ("Jonathan Turnbull"/"Republican"), derived per the item's own
  description from the canvassed November 2024 election.
- **No known staleness bomb.** Iowa's shipped layer predated Senate File 75 and needed a
  three-county reconciliation before it could ship. Nothing equivalent surfaced for Michigan;
  county apportionment runs on the census cycle.

**NONE OF THAT SHIPS IN PHASE 1, DELIBERATELY.** A roster attached to a boundary is refreshed
when the boundary is — this repo's own Des Moines finding — so those names get their own
verification pass and their own change rather than riding in on the geometry's coat-tails. The
`county` card ships identity-only and *says on the card* that it does not name commissioners.

## Scope decisions

- **Phase 1 is the national tier only, exactly the WI/IA shape.** Four layers: `county`,
  `us-house`, `mi-senate`, `mi-house`. Every one is TIGERweb geometry plus a roster from a
  publisher already trusted fleet-wide.
- **The instance arrives DARK.** No `metros.json` entry, no `--sync-fleet`, no
  `build_coverage_map.py` row, and one blanket `mi/**` line in the deploy's EXCLUDES — the Iowa
  PR 0 posture, for the reason Iowa measured: a manifest entry renders a live landing card the
  day it lands, and for an excluded folder that card is a 404. CI runs against `mi/` from this
  PR forward all the same.
- **`sources_page` and `history_page` are set from this PR**, not backfilled (Wisconsin's
  `history_page` arrived three phases late and had to be written from git history).
- **No county-officer roster, no precinct layer, no school tier in phase 1** — each is a later
  change with its own verification, and each is a stated absence rather than a silent one.

## What phase 1 shipped, and what it measured

| Layer | Count | Boundary | Roster |
|---|---|---|---|
| `us-house` | 13 | TIGERweb Legislative/0 (**CD120**) | congress-legislators (CC0), 13/13 with a district office |
| `mi-senate` | 38 | TIGERweb Legislative/1 (SLDU) | Open States `mi.csv` + the Senate's own directory — **38/38 with a Capitol office** |
| `mi-house` | 110 | TIGERweb Legislative/2 (SLDL) | Open States `mi.csv` — 110/110 with e-mail, **no capitol office block** (below) |
| `county` | 83 | TIGERweb State_County/1 | none — identity only, stated on the card |

All four boundary builds passed the 2,000-random-point agreement gate at **100.00% with 0
overlaps**. Ground truth: the Michigan State Capitol (42.7337, -84.5553) → Ingham County, U.S.
House 7, Senate 21, House 77 — **VERIFIED against the shipped geometry, not assumed**. The
negative point is downtown Toledo, Ohio, measured to miss all four layers.

### Three findings worth carrying forward

**1. TIGERweb's congressional layer has rolled to the 120th Congress, and the old field is
GONE.** The layer is now named "120th Congressional Districts" and its district field is
`CD120`. A query naming the retired `CD119` does not return an empty set — it is **rejected with
HTTP 400, "Failed to execute query"** (VERIFIED; it is what made this instance's first
congressional build fail). Michigan's builder names `CD120`. **The sibling instances' builders
still name `CD119` and would fail identically on a rebuild** — their shipped files are fine, so
this is a latent break rather than a live one, but it is real and belongs to whoever next
rebuilds a congressional boundary in `il/`, `wi/` or `ia/`. It is deliberately not fixed here:
this PR does not touch sibling instances.

**2. Michigan's county fabric is WATER-INCLUSIVE, and the coverage ring is one polygon because
of it.** Every Great Lakes county's TIGERweb polygon runs out to the state water boundary —
Keweenaw County alone spans **2.57° of longitude**, from the Keweenaw Peninsula out past Isle
Royale — so both peninsulas and every island tile continuously and the dissolve yields **ONE
ring, 1,716 vertices** (VERIFIED via `--check`). Mid-Lake Michigan, mid-Lake Huron and the
Mackinac Straits all measure *inside* coverage; Toledo, Chicago and Toronto all measure outside.
That is correct — the water genuinely is assigned to Michigan counties — and it is why the
negative point had to be a point on land in another state. **The first draft of the outline
builder's own docstring asserted "several rings, two peninsulas plus islands" before the build
was run, and was wrong**: the same error this repo keeps re-learning in Illinois. Read the ring
count from `--check`, never from a map in your head.

**3. The Michigan House site could not be reached, and what that does and does not mean.**
Open States carries **no capitol phone or address for any Michigan legislator** (VERIFIED, 0 of
148 rows), so every contact detail must come from the chambers. The Senate's own all-senators
directory supplies phone, e-mail, office and contact page for all 38 seats — **but the parse is
not the obvious one**: the roster is an HTML-escaped `senatorInfo` attribute feeding a Lit
component, not a `var senatorInfo = [...]` assignment, and a parser written against the obvious
shape returns nothing from a page that plainly contains the data. (A research pass reported the
data's existence correctly and its shape incorrectly; the scraper was written against the page,
not the report.) `house.mi.gov`, meanwhile, fails TLS from this build environment with "unable
to get local issuer certificate" **even with the egress proxy's CA bundle explicitly supplied**,
while `senate.michigan.gov` answers 200 on identical flags and the proxy records no relay
failure. That is the incomplete-chain shape this repo documents for Coles, Gallatin and
Vermilion — **but TLS is re-terminated at the sandbox proxy, so this environment cannot observe
the site's real chain at all.** A measurement is not a conclusion (`docs/EXPANSION_GUIDE.md`
§0.4): it is recorded as unresolved in `mi/WATCH.md`, owing **one CI-side probe**, and the House
card ships without an office block rather than claiming one it cannot source.

## One gate changed, and why

`scripts/validate_instance_registration.py` required every instance in the tree to appear in
`metros.json`. That is right for a published instance and wrong for a dark one, and it collided
head-on with the arrival posture the same repo documents: Iowa's PR 0 measured that a
`metros.json` entry renders a live landing card immediately, so listing a deploy-excluded folder
publishes a 404. The gate now reads the deploy's own EXCLUDES to tell the two apart and checks
the biconditional — **listed if and only if published** — which is strictly stronger than what
it checked before: it now catches the 404 case as well as the invisible-instance case. Verified
in both directions (a dark `mi` passes; `mi` added to `metros.json` while still excluded fails
with the reason).

## Status

| | Shipped | What it cost, measured |
|---|---|---|
| **Phase 1 — the national tier** | 2026-09-03 (#685) | 4 layers: `county` 83, `us-house` 13, `mi-senate` 38, `mi-house` 110. All three boundary builds at 100.00% agreement, 0 overlaps. Found the CD119→**CD120** roll, which had broken nothing yet and would have broken the next rebuild in all five sibling instances |
| **Phase 2 — the flagship** | 2026-09-03 (#691) | `county-commissioner`, 619 districts across all 83 counties, GEOMETRY ONLY. The layer's own `Commissioner`/`Party` columns were measured against twelve counties' board pages (123 districts) and **dropped**: 93.5% right, every miss the same direction, and Wayne D5 still naming a commissioner who died in June 2025. A winners list is complete by construction, so its 100% fill rate is evidence AGAINST maintenance |
| **Go-live** | 2026-09-03 (#694) | Michigan published at districtry.com/mi/. Four defects surfaced that the full battery had been green on — missing fonts and OG image, Iowa's identity block on the sources page, a dead helper that made the privacy page overstate what the app sends, and a fleet bbox containing two siblings' centres. Two new gates (`validate_instance_assets.py`, and identity checks in `page_consistency_test.mjs`) |
| **Routing follow-up** | 2026-09-04 (#698) | Front-door routing moved off bbox tie-breaks onto each instance's own coverage ring: 7 misroutes of 28 real places down to 4. Also corrected three records that had named smallest-bbox-AREA as the fix — measured, it is no better than the rule it would replace |

**Phase 1's own "what shipped" section above is left exactly as written on the day.** It is the
record of what was true then, not a status board; this table is the status board.

## Still open

Each opens its own refreshed plan PR with its own measured ledger when it begins.

- ~~**Phase 3 — the fabric.**~~ **DONE, in two PRs (2026-09-04).** PR 1 shipped the four live
  TIGERweb layers — `county-subdivision`, `municipality` and the two school tilings — and PR 2 the
  precinct layer. Three things it settled that this entry got wrong or left open:
  - **The charter-township claim needed no citation.** It is readable straight off TIGER's own
    `NAME` suffix, 1,581 records of 1,581 (1,122 general-law, 118 charter), so the card's type row
    can never disagree with the name printed above it.
  - **The city/village distinction is the one that mattered, and this entry did not name it.** A
    Michigan city is independent of any township; a VILLAGE remains part of one — measured across
    all 252 villages at their interior points, zero exceptions — so a village resident has two
    general-purpose local governments and each card names the other.
  - **The precinct layer nearly shipped the wrong vintage.** The MapServer carrying the
    commissioner flagship stops at 2024; the 2026 map is on the state's AGO org, on another host,
    and Michigan consolidated 4,340 precincts into 3,895 between the cycles. What caught it was
    this repo's own guidebook cell, which had recorded the 2026 layer weeks earlier and never been
    acted on.
- **Phase 4 — the city tiers.** Detroit and Grand Rapids council districts, with the per-city
  roster work that implies.
- **The 619 commissioners** — gap `mi-commissioner-roster`. The honest route is county-by-county
  against each board's own page, weekly and count-guarded; ten of the twelve counties sampled
  publish a readable one. Oakland answers only through its CMS origin and Ottawa sits behind a
  captcha, which this project does not route around.
- **Michigan's full fleet bbox**, and with it the last four misroutes (Ironwood, Houghton, Iron
  Mountain, Menominee). Needs `validate_index`'s "a bbox must not contain a sibling's centre"
  rule relaxed AND the in-app `metro-portal` moved onto the same ring test — its `siblingMetroAt`
  runs on `moveend`, so it needs the same pre-filter discipline and must never let a fetch block
  a pan. `mi/WATCH.md` carries the measurement; the ceiling is 0 misroutes.
- **One CI-side probe of `house.mi.gov`**, to settle whether its TLS failure is the site's own
  incomplete chain or an artifact of the build sandbox. Until then the House card ships without
  the Capitol contact block the Senate card has, rather than claiming one it cannot source.

## Conventions binding every PR

Scripts `mi/scripts/build_mi_*.py` / `mi_*_scraper.py`; workflows
`.github/workflows/update-mi-*.yml`, **every one `mi`-prefixed with no exceptions** — Wisconsin's
unprefixed workflows collided with the pre-consolidation Illinois naming and neither Iowa nor
Michigan repeats it. `BOT_PR_TOKEN`, fixed `bot/mi-*` branch, PR-never-push. Every layer gets a
worksheet `source` block (the generator refuses otherwise), a `LAYER_SIDEBAR_RANK` slot, a
`validate_sources.py` row, a `WATCH.md` row, and guidebook coverage-map + matrix updates in the
same change. GENERATED regions and ENGINE fences are never hand-edited — all module code is
instance-side, between the `chamber-factory` and `hover-explorer` fences. Scraped strings render
through `sanitize()`/`textContent`. The officeholder story ships with each boundary — a roster,
or a recorded gap, never silence. `min_register_layer` only rises. Files inside `mi/data/app/`
are named `mi-*`, never `michigan-*`.

# Data Layer Guidebook — the fleet's layer roster, in one place

**This is the master copy, in the Chicago repo (the reference implementation), covering
every metro fork.** Sibling forks do not carry a copy — not even a stub
(`docs/EXPANSION_GUIDE.md` §4.4.1 item 11 is the authoritative list of what is
stubbed vs. not carried). It answers, for every civic-district concept the
fleet has ever considered: which metros ship it, which metros *can't* honestly ship it and
why (recorded drop rationale), which metros simply haven't yet (parity debt), and what's
in the researched-but-unbuilt backlog.

**Maintenance contract — this file is load-bearing, not decorative:**

1. **Any PR in any fork that adds, renames, or removes a layer updates this guidebook in
   the same change** (for a fork PR, a companion CHI PR — same rule as fork-born engine
   improvements). Update the machine-readable coverage map below *and* the affected
   tables.
2. **The weekly fleet-status run enforces it**: `scripts/fleet_status.py` diffs each
   fork's live `metro-worksheet.json` layer roster against the coverage map below and
   puts a **GUIDEBOOK WARN** on the standing "Fleet status" issue on any mismatch. A
   layer that ships without a guidebook row is drift, exactly like an engine fence
   mismatch. The same run diffs each fork's shipped `data/app/coverage-gaps.json`
   against the gaps block below and raises a **GAPS WARN** on any disagreement —
   naming which ids differ and the exact regenerate command. That check matters most
   for the SIBLINGS: this guidebook lives in the Chicago repo only, so their files are
   generated here and land there through a bump PR, which leaves them with no local
   drift gate of their own.
3. **A gap a reader could help close goes in the `GUIDEBOOK:BEGIN gaps` block, and the
   app then says so out loud.** That block drives the in-app **Data gaps** panel via
   `scripts/build_coverage_gaps.py` (`--check` runs in CI, so guidebook and panel cannot
   drift). Record the blocker as something *measured* and say in `wanted` what a
   submission would need to contain — the panel shows both, so a reader is never invited
   to re-send a source that was already checked and rejected. Accepted submissions are
   credited in `docs/SOURCE_CREDITS.md`.
4. **A deliberate "we will not ship this here" is recorded, never implied.** Every
   NO HONEST ANALOG cell cites its rationale; a concept a fork lacks *without* a recorded
   rationale sits in the Parity debts table until someone either ships it or records the
   drop. (This rule exists because SF's BART-districts candidate silently evaporated
   between worksheet and launch; the debt is since paid — `bart-director` shipped
   July 2026 — but the rule stays.)

<!-- ==== GUIDEBOOK:BEGIN coverage-map ==== -->
```json
{
  "chicago": ["il-supreme-court", "congress", "il-senate", "il-house", "county", "mwrd", "school-district-secondary", "school-district-unified", "school-district-elementary", "township", "municipality", "judicial-subcircuit", "county-board", "ccbr", "fire-district", "dupage-county-special-police", "park-district", "library-district", "school-board", "cps-hs-network", "cps-network", "ward-precinct", "ward", "police-beat", "police-district", "ccpsa-district-council", "community-area", "zip-code", "cps-high", "cps-middle", "county-precinct", "tif-district", "cps-elementary", "school-site", "police-station", "fire-station", "post-office", "library", "early-voting"],
  "nyc": ["borough", "judicial-district", "borough-president", "district-attorney", "congress", "municipal-court", "state-senate", "school-district", "cec", "fire-battalion", "council", "community-district", "election-district", "state-assembly", "police-sector", "police-precinct", "zip-code", "neighborhood", "hs-zone", "ms-zone", "es-zone", "school-site", "police-station", "fire-station", "post-office", "library", "early-voting"],
  "sf": ["congress", "ca-senate", "ca-assembly", "bart-director", "election-precinct", "supervisor-district", "police-district", "zip-code", "neighborhood", "elementary-attendance-area", "police-station", "fire-station", "school-site", "post-office", "library", "early-voting"]
}
```
<!-- ==== GUIDEBOOK:END coverage-map ==== -->

<!-- ==== GUIDEBOOK:BEGIN gaps ==== -->
```json
{
  "chicago": [
    {
      "id": "kankakee-municipal-officials",
      "concept": "Municipal officials",
      "area": "Kankakee County",
      "counties": [
        "kankakee"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "No officeholder names for Kankakee County's 21 municipalities — the card shows identity and a link only.",
      "blocker": "No county-published roster exists. The clerk site publishes no directory, and the county GIS Municipalities layer declares telephone/website/email columns but populates none of them (measured 0/21).",
      "wanted": "Any county- or COG-level directory naming mayors/village presidents and boards — ideally with a stable URL that is republished after each election."
    },
    {
      "id": "dekalb-county-gis",
      "concept": "All county layers",
      "area": "DeKalb County",
      "counties": [],
      "kind": "no-source",
      "layer": null,
      "summary": "DeKalb County, Illinois has no located GIS — so none of its county layers can be built.",
      "blocker": "ArcGIS Online results for “DeKalb” are dominated by DeKalb County GEORGIA. Field-qualified searches for the Illinois county return only historical plat maps, and three plausible self-hosted hostnames do not resolve.",
      "wanted": "A working URL for DeKalb County IL's GIS server or ArcGIS org — a county web map that draws precincts or board districts is enough; its operational layers reveal the server."
    },
    {
      "id": "lake-municipal-names",
      "concept": "Municipal officials",
      "area": "Lake County",
      "counties": [
        "lake"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Lake County's 41 municipalities ship with hall contact but no officeholder names.",
      "blocker": "No Lake County body publishes municipal officeholder names anywhere county-side. The county GIS supplies hall address/phone/website, which is what the card shows.",
      "wanted": "A Lake County clerk or council-of-governments directory naming heads of government — the DuPage DMMC directory is the shape that would work."
    },
    {
      "id": "boone-county-board",
      "concept": "County board districts",
      "area": "Boone County",
      "counties": [
        "boone"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Boone County's 3 board districts are not shipped.",
      "blocker": "The county publishes them as three separate single-feature layers with no officeholder attribute, so the layer needs both a merge loader and an officeholder source before it can name anyone.",
      "wanted": "A Boone County board member directory keyed by district (names, and contact if published)."
    },
    {
      "id": "grundy-county-board",
      "concept": "County board districts",
      "area": "Grundy County",
      "counties": [
        "grundy"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Grundy County's board districts are not shipped.",
      "blocker": "The county's GIS publishes no board-district geometry at all — only precincts and polling places.",
      "wanted": "Board-district boundaries in any GIS or shapefile form, plus a member directory keyed by district."
    },
    {
      "id": "blocked-crawlers",
      "concept": "Roster refresh",
      "area": "McHenry, Kendall and Joliet",
      "counties": [
        "mchenry",
        "kendall"
      ],
      "kind": "blocked",
      "layer": "county-board",
      "summary": "Three sources refuse every automated fetch, so their rosters are hand-verified rather than refreshed weekly.",
      "blocker": "Hard WAF denies — direct request, real browser, and the Internet Archive's crawler are all refused. The weekly workflow still attempts the ladder and tracks the block on a standing issue; a 45-day snapshot-age guard keeps stale data from being served as fresh.",
      "wanted": "A machine-readable feed for the same data (JSON/CSV/RSS), or any mirror the sources permit crawling."
    },
    {
      "id": "dupage-municipal-phones",
      "concept": "Municipal officials",
      "area": "DuPage County",
      "counties": [
        "dupage"
      ],
      "kind": "data-quality",
      "layer": "municipality",
      "summary": "DuPage municipal entries carry no phone numbers.",
      "blocker": "The DMMC directory prints numbers without an area code and states no default, so rendering them would mean guessing which area code to dial.",
      "wanted": "A DuPage directory that prints full ten-digit numbers, or an authoritative statement of the default area code per municipality."
    },
    {
      "id": "aurora-council-contact",
      "concept": "Municipal officials",
      "area": "Aurora",
      "counties": [
        "kane",
        "will",
        "dupage",
        "kendall"
      ],
      "kind": "data-quality",
      "layer": "municipality",
      "summary": "Aurora's 12 council members render with correct wards but no phone or e-mail.",
      "blocker": "aurora-il.org returns 403 to every client (a hard deny, not a challenge); Aurora's own ward FeatureServer carries no officeholder fields; the county directory that supplies Aurora has names only; and the Internet Archive's newest useful captures are 2015–2017.",
      "wanted": "Any reachable Aurora source with per-seat contact — a council roster page, a published PDF, or an open dataset."
    },
    {
      "id": "lasalle-board-phones",
      "concept": "County board districts",
      "area": "LaSalle County",
      "counties": [
        "lasalle"
      ],
      "kind": "data-quality",
      "layer": "county-board",
      "summary": "LaSalle board members show e-mail and mailing address but no phone.",
      "blocker": "The county GIS records phone numbers without an area code (“672-2115”) and states no default, so they are deliberately not rendered rather than guessed at.",
      "wanted": "LaSalle board contact with full ten-digit numbers, or the county's stated default area code."
    },
    {
      "id": "kankakee-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Kankakee County",
      "counties": [
        "kankakee"
      ],
      "kind": "data-quality",
      "layer": "fire-district",
      "summary": "Kankakee's fire, park and library districts show a name only — no address, phone or website.",
      "blocker": "The county's taxing-district layers declare telephone/website/email on every row and populate none of them (measured 0/17, 0/4, 0/8).",
      "wanted": "A Kankakee directory of fire protection, park and library districts with contact details."
    },
    {
      "id": "boone-fire-names",
      "concept": "Fire protection districts",
      "area": "Boone County",
      "counties": [
        "boone"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Boone County's fire districts are not shipped.",
      "blocker": "The county's fire tiling keys its 5 districts by NUMBER with no district name, and a card reading “Fire District 1” would tell a reader nothing they can act on.",
      "wanted": "A mapping from Boone's fire-district numbers to district names, or a named fire-district boundary layer."
    },
    {
      "id": "logan-county-board-members",
      "concept": "County board members",
      "area": "Logan County",
      "counties": [
        "logan"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Logan County's 6 board districts resolve, but no member is named on the card.",
      "blocker": "The regional GIS (Tri-County RPC) publishes the district number and a population count and no officeholder. The county's only published roster is its statutory salary publication, which lists twelve board members with no district against any of them, so it cannot be joined to a district.",
      "wanted": "Any Logan County list that pairs a board member with their DISTRICT number — a directory page, a board roster PDF, or an election canvass. A list of members alone is not enough; the district is the join key."
    },
    {
      "id": "macoupin-county-board-districts",
      "concept": "County board districts",
      "area": "Macoupin County",
      "counties": [
        "macoupin"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Macoupin's 9 two-member board districts do not resolve — only its precincts do.",
      "blocker": "The county composes board districts from PRECINCTS, and its precinct polygons are published (Socrata ab79-cnsh), but the precinct-to-district mapping is only in a scanned image PDF still titled \"proposed\" (2021). Drawing real district lines from a proposal, via OCR, is not something this app will do. The member roster itself IS published and complete (Socrata rxtc-9j2k, 9 districts x 2 members).",
      "wanted": "A machine-readable precinct-to-board-district assignment for the adopted 2022-2032 map — a spreadsheet, a Socrata column on the precinct dataset, or district polygons. The roster is already in hand; only the geography is missing."
    },
    {
      "id": "st-clair-precinct-polling-places",
      "concept": "Polling places",
      "area": "St. Clair County",
      "counties": [
        "st-clair"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "St. Clair precinct cards name the precinct and its board district but not where to vote.",
      "blocker": "The county publishes 103 polling places, but keys them by a COMBINED human label rather than a precinct id — \"Belleville9,10, 12 & 16\", with non-breaking spaces and inconsistent zero-padding against the precinct layer's \"Belleville 9\". Joining them means parsing prose into a set of precincts, which would silently mis-assign a polling place whenever the phrasing changes.",
      "wanted": "A precinct-keyed polling assignment — a column on the precinct layer, or a polling table with one row per precinct id, as Madison, Kendall, LaSalle and Grundy all publish."
    },
    {
      "id": "madison-ward-officials",
      "concept": "Municipal ward officials",
      "area": "Madison County",
      "counties": [
        "madison"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Madison County's 31 municipal wards are published but not shipped, because no alderperson is named on them.",
      "blocker": "MadCo_Wards declares OFFICIAL, ADDRESS, CITY, STATE, ZIPCODE, PHONE, EMAIL and URL on every row and populates every one of them on 0 of 31. A ward layer with a number and nobody in it would add a toggle that answers 'Ward 4' and stops.",
      "wanted": "Any Madison County or municipal list pairing a ward number with its alderperson — Edwardsville, Alton, Granite City and Collinsville all elect by ward. The polygons are already in hand; only the names are missing."
    },
    {
      "id": "winnebago-village-heads",
      "concept": "Municipal officials",
      "area": "Loves Park and Machesney Park",
      "counties": [
        "winnebago"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Loves Park and Machesney Park show their full councils but no mayor or village president.",
      "blocker": "WinGIS publishes an officeholder layer per municipality, but for these two it carries the council seats only — there is no mayor/president layer to read. Every other Winnebago municipality has one.",
      "wanted": "A Loves Park mayor and a Machesney Park village president, from either city's own site or a WinGIS layer if the county adds one. The councils are already complete; only the head of government is missing."
    },
    {
      "id": "rockford-city-precincts",
      "concept": "Voting precincts",
      "area": "City of Rockford",
      "counties": [
        "winnebago"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Precincts resolve everywhere in Winnebago County except inside Rockford itself.",
      "blocker": "Rockford runs its own Board of Election Commissioners, so the county's 94-precinct tiling stops at the city line — measured, not documented: 130 of 131 uncovered grid samples fall inside the TIGER Rockford polygon. The clerk publishes a city-precinct committeeperson PDF, so the precincts exist; no boundary layer for them does.",
      "wanted": "Rockford Board of Election Commissioners precinct polygons, or a city precinct layer on WinGIS. This is the Chicago/suburban-Cook split repeating in a smaller city, and the app already models that shape."
    }
  ],
  "nyc": [
    {
      "id": "nyc-school-zone-details",
      "concept": "School zones",
      "area": "New York City",
      "counties": [],
      "kind": "data-quality",
      "layer": "es-zone",
      "summary": "School-zone cards name the zoned school but carry no school address or grade range.",
      "blocker": "Verified live during the 2026-07 card audit: the DOE zone datasets carry neither field, so the app's addressKeys/gradeKeys are deliberately unwired rather than pointed at columns that do not exist.",
      "wanted": "A DOE dataset joining zone to school address and grade span by DBN, refreshed each school year."
    },
    {
      "id": "nyc-amenity-phones",
      "concept": "Fire stations and libraries",
      "area": "New York City",
      "counties": [],
      "kind": "data-quality",
      "layer": "fire-station",
      "summary": "Fire-station and library cards carry no phone number.",
      "blocker": "Checked in the 2026-07 card audit: the upstream station and library datasets genuinely have no phone column — this is an absence in the source, not an unwired field.",
      "wanted": "An FDNY firehouse or NYPL/BPL/QPL branch dataset that includes public phone numbers."
    },
    {
      "id": "nyc-congress-district-offices",
      "concept": "U.S. House district",
      "area": "New York City",
      "counties": [],
      "kind": "data-quality",
      "layer": "congress",
      "summary": "Congressional cards show the Washington D.C. office only, not the local district office.",
      "blocker": "The roster builder's source publishes the D.C. office; district-office addresses are not in it. Recorded as a builder-scope enrichment candidate rather than a missing source.",
      "wanted": "A machine-readable list of House members' DISTRICT office addresses and phones, keyed by member or district."
    }
  ],
  "sf": [
    {
      "id": "sf-supervisor-contact",
      "concept": "Supervisor district",
      "area": "San Francisco",
      "counties": [],
      "kind": "data-quality",
      "layer": "supervisor-district",
      "summary": "Supervisor districts name the supervisor but the boundary source carries no contact fields.",
      "blocker": "Verified in the 2026-07 card audit: the upstream DataSF dataset (hcgx-vtsb) has no contact columns, so contact would have to come from a separate roster.",
      "wanted": "A DataSF or Board of Supervisors dataset with per-district office phone and e-mail."
    },
    {
      "id": "sf-amenity-phones",
      "concept": "Fire stations and libraries",
      "area": "San Francisco",
      "counties": [],
      "kind": "data-quality",
      "layer": "fire-station",
      "summary": "Fire-station and library cards carry no phone number.",
      "blocker": "Checked in the 2026-07 card audit: the upstream SFFD station and SFPL branch datasets have no phone column.",
      "wanted": "An SFFD station or SFPL branch dataset that includes public phone numbers."
    },
    {
      "id": "sf-congress-district-offices",
      "concept": "U.S. House district",
      "area": "San Francisco",
      "counties": [],
      "kind": "data-quality",
      "layer": "congress",
      "summary": "Congressional cards show the Washington D.C. office only, not the local district office.",
      "blocker": "The roster builder's source publishes the D.C. office; district-office addresses are not in it.",
      "wanted": "A machine-readable list of House members' DISTRICT office addresses and phones, keyed by member or district."
    }
  ]
}
```
<!-- ==== GUIDEBOOK:END gaps ==== -->

This block is the machine truth behind the app's **Data gaps** panel, emitted to
`data/app/coverage-gaps.json` by `scripts/build_coverage_gaps.py` (`--check` is the CI
drift gate). It carries only gaps a READER COULD HELP CLOSE — a missing or blocked source
(`no-source` / `blocked`) or a shipped layer with a known hole (`data-quality`).
Deliberately NOT in here: layers that correctly do not apply somewhere (a subcircuit in a
circuit that has none is not a gap), and live source outages, which are transient runtime
state the affected card already reports itself.

Every entry states its blocker as something MEASURED, and `wanted` says what a submission
would have to contain to be useful — so a reader is never invited to re-send a source that
was already checked and found wanting. `counties` are outline slugs, which is what makes a
gap location-aware: with a point selected the panel shows the gaps that apply THERE first.
An empty `counties` means the gap has no mappable footprint (DeKalb has no GIS to draw)
and it appears only in the everywhere list.

Accepted submissions are credited by name in `docs/SOURCE_CREDITS.md`; see the intake
template at `.github/ISSUE_TEMPLATE/source-submission.yml`.


The block above is the machine truth `fleet_status.py` checks — one array per metro
(keys = `metros.json` ids), each listing that fork's registered layer ids exactly as its
`metro-worksheet.json` declares them. Everything below is the human explanation.

## How to read the tables

Status key: **SHIPPED** `id` · **NO HONEST ANALOG** (recorded drop — the body doesn't
exist, isn't elected, or publishes no boundary; never faked) · **GAP** (a sibling ships
the concept, this fork doesn't, and no rationale is recorded — parity debt) · **n/a**
(structurally inapplicable, e.g. a township layer in a consolidated city).

Pattern legend (which engine factory a layer uses): **Polygon** `registerPolygonLayer` ·
**Bespoke** hand-written `registerLayer` (roster joins, shared geometry, filters) ·
**Chamber** `registerIlgaChamber` (legislative boundary + roster file) · **SchoolZone**
`registerSchoolZone` via each fork's wrapper · **CpsNetwork** `registerCpsNetwork` ·
**BoroughOffice** `registerBoroughOfficeLayer` (NYC) · **NearestPt**
`registerNearestPointLayer` (nearest-3 haversine; hover identity built in as of engine
v1.0.6) · **CountyDispatch** `registerCountyLayer` (CHI fork-level dispatcher: one
concept layer holding a per-county entry table — see
`docs/EXPANSION_GUIDE.md` Part 2; adding a county is a table entry, not a layer).

Fleet totals: **Chicago 39 · NYC 27 · SF 16** layers.

---

## Concept coverage matrix

### Political / legislative

| Concept | Chicago | NYC | SF |
|---|---|---|---|
| U.S. House district | SHIPPED `congress` | SHIPPED `congress` | SHIPPED `congress` |
| State upper chamber | SHIPPED `il-senate` | SHIPPED `state-senate` | SHIPPED `ca-senate` |
| State lower chamber | SHIPPED `il-house` | SHIPPED `state-assembly` | SHIPPED `ca-assembly` |
| City council district | SHIPPED `ward` — consolidated CountyDispatch keyed by MUNICIPALITY (the dispatcher's first non-county key): Chicago 50 (Socrata wards + alderman roster) + suburban Cook 21 municipalities (county GIS layer 22) + Evanston 9 (city GIS, which also carries each alderperson's email/phone/ward page) + Will 4 cities incl. Joliet's council DISTRICTS (county GIS) + Aurora 10 (city GIS). Suburban seat-holders join `municipal-officials.json` by municipality + seat number, so a ward card names the same person the Municipality card lists for that seat | SHIPPED `council` (51) | SHIPPED `supervisor-district` (11; doubles as the county board — consolidated city-county) |
| Electoral precinct / ballot sub-unit | SHIPPED `ward-precinct` + `county-precinct` (consolidated CountyDispatch: suburban Cook current map 1,430 — Cook-outside-Chicago only, city precincts are the BOE ward-precinct layer — + Will 2022 map 310 + DuPage 2024 map 600 + Lake current map 431 + Kane current map 292 + McHenry current map 223 + Kendall current map 78 w/ the county's own polling-place assignment per precinct; every metro county covered) | SHIPPED `election-district` (~4,200) | SHIPPED `election-precinct` (`jg6x-23ig`, 2022 map; subOf `supervisor-district`, polling-place lookup link) |
| County legislature / commissioner | SHIPPED `county-board` (consolidated CountyDispatch layer: Cook Commissioner 17 + Will 11 + DuPage 6 + Lake 19 + Kane 24 + McHenry 9 + Kendall 2 + LaSalle 29 + Kankakee 28 + Winnebago 20 + Livingston 3 + McLean 10 + Logan 6 + Sangamon 29 + Madison 26 + St. Clair 28 districts; absorbed the former `commissioner` / `will-county-board` / `dupage-county-board` layers, old permalink ids aliased; Lake's members + contact + office address ride live on the county's own boundary GIS, with Chair/Vice-Chair tags from a weekly directory scrape (name-match guarded); Kane's GIS carries member names while a weekly scrape of the county's SharePoint directory list adds party/office phone/email + the countywide-elected Chair; Kendall's members + Chairman and McHenry's members + countywide-elected Chairman — each with contact + profile links — join from hand-verified rosters of each county's own directory — those two counties block all automated fetch incl. the Archive's crawler, so their weekly scrape attempts feed standing tracking issues until the block lifts) | NO HONEST ANALOG¹ | NO HONEST ANALOG (folded into `supervisor-district`) |
| County property-tax appeals board (elected) | SHIPPED `ccbr` (commissioner roster scraped weekly from the Board's own site) | NO HONEST ANALOG² | NO HONEST ANALOG⁵ |
| State high-court electoral district | SHIPPED `il-supreme-court` | SHIPPED `judicial-district` (NY Supreme is trial-level, elected by district) | NO HONEST ANALOG⁶ |
| Trial/civil-court sub-district | SHIPPED `judicial-subcircuit` (consolidated CountyDispatch: Cook 20 — live from the county GIS, cross-validated against the enacted ilsenateredistricting.com shapefile, with the Circuit Court's 6 municipal districts + courthouses as a card row — + Will 12th-Circuit 5 + DuPage 18th-Circuit 7 + Lake 19th-Circuit 12 + Kane 16th-Circuit 4 (pre-built from the enacted shapefile — the county's services are permission-locked) + McHenry 22nd-Circuit 4 (pre-built — the county publishes no subcircuit service), all PA 102-0693; Kendall's 23rd Circuit received NO subcircuits under the act — structurally n/a, the layer hides there) | SHIPPED `municipal-court` (28) | NO HONEST ANALOG⁶ |
| District Attorney (districted) | n/a (Cook State's Attorney is one countywide office) | SHIPPED `district-attorney` (5 borough DAs) | NO HONEST ANALOG (one citywide DA)⁷ |
| Borough president / by-county executive | n/a | SHIPPED `borough-president` | n/a |
| Community district / board (appointed, labeled so) | n/a | SHIPPED `community-district` | n/a |
| Elected school board (districted) | SHIPPED `school-board` (ERSB) | NO HONEST ANALOG³ | NO HONEST ANALOG (at-large board)⁴ |
| Parent-elected education council | n/a | SHIPPED `cec` | n/a |
| Elected regional transit board | NO HONEST ANALOG⁸ | NO HONEST ANALOG⁸ | SHIPPED `bart-director` (9 districts, BART's own ArcGIS + hand-verified roster) |
| Municipal governing body (surfaced on the municipality-identity card) | SHIPPED on `municipality` — 156 municipalities across suburban Cook (Clerk's Directory of Elected Officials API) and Will (Clerk's Will County Directory), with head of government + 958 board members incl. 184 ward/district seats + clerks/treasurers + hall contact, joined by Census place GEOID (weekly CI). Six municipalities listed by both counties resolve by source depth, then county order. Chicago is excluded by concept — its council is `ward`. The other five metro counties are sourced but unbuilt, and depth varies honestly by county (`docs/MUNICIPAL_COUNCILS_PLAYBOOK.md`); an unsourced municipality keeps the identity-only card | n/a (NYC's municipalities are the five boroughs — `borough-president`) | n/a (consolidated city-county) |
| County clerk (surfaced on the county-identity card) | SHIPPED on `county` — all 101 clerk-authority counties via ISBE's election-authority directory (weekly CI; Peoria deliberately absent, its authority is an appointed election commission) | SHIPPED on `borough` — appointed (Appellate Division), labeled so; operator-verified `clerk` entries in `borough-officials.json` (nycourts.gov is Cloudflare-fronted, so no scraper; names only where the office's own page publishes one) | n/a⁹ |
| Early-voting / vote-center sites | SHIPPED `early-voting` (hand-curated per election; every site doubles as a secured ballot drop box) | SHIPPED `early-voting` (live NYS GIS) | SHIPPED `early-voting` (hand-curated; includes the 37 ballot drop boxes) |

Recorded drop rationales (full quotes live in the cited docs):
¹ NYC counties have no legislature — county government absorbed into the City (*Board of
Estimate v. Morris*, 1989). ² NYC's Tax Commission is appointed, citywide, no districts.
³ Mayoral control; the Panel for Educational Policy is appointed — `cec` is the honest
*parent*-elected analog and its card says so. ⁴ SF's Board of Education is elected
at-large; no district geometry exists. ⁵ SF's assessment-appeals board is appointed.
⁶ California Supreme Court is statewide; Courts of Appeal justices are appointed →
link-only at most. ⁷ SF's DA is one at-large office. ⁸ Neither sibling elects its
transit board: the Chicago Transit Board is appointed (4 mayoral + 3 gubernatorial
appointees, 70 ILCS 3605/19) and the MTA board is appointed (Governor + city/county
recommendations) — BART is the fleet's only transit board elected by district.
⁹ SF has no county-identity card to host a clerk (city and county are coterminous —
the `county` concept itself is recorded n/a) and the SF County Clerk is an appointed
city office under the City Administrator. **Future-metro recipe for this concept:**
if the fork has a county-identity layer, join the state's election-authority /
clerk directory (Illinois: ISBE's ElectionAuthorities.aspx — one postback returns
every county; other states usually have a Secretary-of-State analog) via the
weekly scraper→builder→review-PR pattern; where the authoritative source is
challenge-fronted or names aren't published, fall back to NYC's operator-verified
entries with per-office source URLs, and label appointed clerks as appointed. (¹–³:
`docs/archive/METRO_EXPANSION_PLAYBOOK.md` Part II "NO honest NYC analog" table /
`docs/archive/METRO_EXPANSION_NYC.md` §7; ⁴–⁷: `docs/archive/METRO_EXPANSION_SF_WORKSHEET.md`
§0 + the SF repo's worksheet drop appendix.)

### Public safety

| Concept | Chicago | NYC | SF |
|---|---|---|---|
| Police district / precinct | SHIPPED `police-district` (22) | SHIPPED `police-precinct` (78) | SHIPPED `police-district` (10) |
| Police subdivision (beat / sector) | SHIPPED `police-beat` | SHIPPED `police-sector` | NO HONEST ANALOG — SFPD publishes no patrol-beat boundary (the only "beats" dataset is Parking Control's) |
| Elected police oversight | SHIPPED `ccpsa-district-council` | NO HONEST ANALOG — CCRB is appointed/citywide; oversight story lives as labeled link rows on the precinct card | NO HONEST ANALOG — the SF Police Commission (Charter §4.109) and Department of Police Accountability are appointed (Mayor + Board of Supervisors), citywide, no districts; NYC's labeled-link-row precedent is the upgrade path if oversight links are ever wanted on the card |
| Fire-service boundary | SHIPPED `fire-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + McHenry + Kendall suburban Fire *Protection* Districts; Cook from the Clerk's tax-agency tiling and DuPage/McHenry/Kendall name-only, Lake carries office contact, Kane names each district's chief + contact) | SHIPPED `fire-battalion` (operational battalions, 49) | NO HONEST ANALOG — SFFD battalions exist but no boundary is published |
| Township police-service tax district | SHIPPED `dupage-county-special-police` (unincorporated-area township tax districts that fund supplemental DuPage County Sheriff patrol; card links the elected Sheriff, coverage-gated) | NO HONEST ANALOG — NYC has no townships | NO HONEST ANALOG — SF has no townships |
| Police / fire station points | SHIPPED `police-station` · `fire-station` (both metro-wide from USGS National Map structures L53/L51 as of 2026-07 — replaced the city-gated CPD/CFD point sets after a completeness check: 22/22 CPD stations, 91/92 CFD houses; the CPD source still feeds the police-district card's station rows) | SHIPPED (city sources) | SHIPPED (city sources) |

Note the fire-boundary concept is not equivalent across forks: NYC maps *operational*
battalions; CHI maps suburban *taxing* districts. Chicago-proper CFD battalion/division
boundaries are a **recorded drop (verified negative, 2026-07)**: neither the Chicago Data
Portal nor CFD publishes any battalion/division boundary — the only official CFD spatial
dataset is the station-point file the `fire-station` layer already uses (`28km-gtjn`);
the boundary maps that circulate online are hobbyist reconstructions (e.g. FDmaps),
which the never-guess rule excludes as a source.

### Schools

| Concept | Chicago | NYC | SF |
|---|---|---|---|
| Elementary attendance zone | SHIPPED `cps-elementary` | SHIPPED `es-zone` | SHIPPED `elementary-attendance-area` (bespoke — card carries the lottery-tiebreaker caveat) |
| Middle / high attendance zone | SHIPPED `cps-middle` · `cps-high` | SHIPPED `ms-zone` · `hs-zone` | NO HONEST ANALOG — SFUSD publishes only elementary areas; MS is feeder-pattern, HS is citywide choice |
| School admin region / network | SHIPPED `cps-network` · `cps-hs-network` | SHIPPED `school-district` (32 CSDs) | NO HONEST ANALOG — one undivided district, no sub-regions |
| Statewide school-district identity | SHIPPED `school-district-{unified,secondary,elementary}` (TIGERweb, coverage-gated) | n/a | n/a |
| School site points | SHIPPED `school-site` | SHIPPED `school-site` | SHIPPED `school-site` |

### Geography / amenities

| Concept | Chicago | NYC | SF |
|---|---|---|---|
| Neighborhood / community area | SHIPPED `community-area` (77) | SHIPPED `neighborhood` (NTA, ~262) | SHIPPED `neighborhood` (41) |
| ZIP code | SHIPPED `zip-code` (ZCTA) | SHIPPED `zip-code` (MODZCTA) | SHIPPED `zip-code` (ZCTA) |
| County | SHIPPED `county` (statewide IL) | SHIPPED `borough` (= county) | n/a — city and county are coterminous (recorded) |
| Township / municipality | SHIPPED `township` · `municipality` (statewide IL; the municipality card names the municipal government — head of government, board, other elected officers, hall contact — for 280 of the metro's 284 municipalities incl. Chicago's citywide officers, county-sourced and joined by place GEOID) | n/a | n/a |
| Park district | SHIPPED `park-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + Kendall; Cook's Clerk tiling includes the Chicago Park District — a Loop click resolves the city's own park taxing body; DuPage/Kendall name-only, Lake carries office contact, Kane names each district's board president + contact; McHenry is the one sourced county with no entry — recorded gap, it publishes facilities not district boundaries) | n/a | n/a |
| Library taxing district | SHIPPED `library-district` (CountyDispatch, born consolidated: Cook's two Clerk tax-agency tilings — 59 Public Library Districts + 54 municipal Library Funds, incl. the City of Chicago Library Fund at a Loop click — + Will 27 w/ trustees + DuPage 32 name-only + Lake 15 w/ office contact + Kane 16 w/ board president + contact + McHenry 13 name-only + Kendall 9 name-only incl. the municipal Joliet/Yorkville city-library funds its tax tiling records, the Cook-style shape) | n/a — NYC's three library systems (NYPL/BPL/QPL) are nonprofit corporations, not taxing districts | n/a — SFPL is a city department |
| Tax increment financing (TIF) district | SHIPPED `tif-district` (Cook, 418 — the Clerk's un-yeared current agency tiling, clerkTaxDistricts L18; dedicated Cook layer per the single-county rule until a second county ships — Kendall's `TIF_Districts` service is the recorded next entry) | n/a — New York State discontinued NYC-style TIF; no city program | n/a — SF uses IFDs/CFDs, no published district tiling evaluated |
| Water reclamation / sewerage special district | SHIPPED `mwrd` (Cook, 1 — the Metropolitan Water Reclamation District of Greater Chicago, the Clerk's tax-agency boundary; nine commissioners elected at large, card links the official board; in/out is the real discrimination — Cook's fringe townships sit outside) | n/a — NYC DEP is a city department, not a separate elected district | n/a — SFPUC is a city department |
| Post office points | SHIPPED `post-office` (USGS National Map L38 — same national source in every fork) | SHIPPED | SHIPPED |
| Library points | SHIPPED `library` (CPL) | SHIPPED `library` (NYPL/BPL/QPL) | SHIPPED `library` (SFPL) |
| Ballot drop boxes | SHIPPED — folded into `early-voting`: Chicago's secured drop boxes (10 ILCS 5/19-6 collection sites, chicagoelections.gov/voting/drop-boxes) are hosted at the early-voting sites themselves — the 50 ward sites in the shipped 52-site file (plus the 2 downtown sites) — and the card intro says so | NO HONEST ANALOG — NYC runs no standalone drop-box program; absentee/mail ballots return by mail, at any poll site, or at BOE offices (vote.nyc / RequestBallot), all already covered by `early-voting` + the card's official links | SHIPPED (inside `early-voting`) |

---

## Parity debts (GAPs with no recorded decision — work them or record the drop)

_None open._ The original five debts were cleared in July 2026 — the outcomes now live
in the matrix above: SF shipped `election-precinct` and `bart-director`; the SF
police-oversight and NYC ballot-drop-box gaps are recorded NO HONEST ANALOG cells;
Chicago's drop boxes folded into `early-voting` (hosted at the same sites); and Chicago-proper CFD
battalions are a verified-negative drop (see the fire-boundary note). New GAP cells go
here as rows until shipped or recorded.

**Rendering debt — resolved (July 2026):** the card-system redesign is fully adopted
fleet-wide. Chicago migrated in CHI #172/#173; NYC (#68) and SF (#34) migrated their
fork-local cards the same week, so the fleet-wide `renderFieldList` grep is at
**zero call sites** — the only remaining references are the engine's own sibling-
compat legacy branches, now dead code. The retirement engine release (delete
`render-helper`, the `.result-row` CSS, and the legacy branches;
`docs/CARD_RENDER_API.md`) is unblocked and awaits an operator's release cut. New
cards follow procedure 2b.

**Design-review polish + Handoff 3 (July 2026):** a design review of the first
redesign pass produced two engine releases and a fork pass in each metro.
`engine-v1.0.11` restored the layer-colored card accent/shadow tie, made the
`<details>` expanders default closed fleet-wide, and added the `pill`/`dotColor`
opts (CHI #181). `engine-v1.0.12` shipped Handoff 3's engine surface
(`docs/design_handoff_fixes_and_schools/`, ids 5a/6a/8a): the card shadow +
id pill tinted with the layer color (§5a), `cardTitleCase`/`cardGradeRange`
and `renderNearestRows` `tag`/`accentColor` (§6a/§8a), and the
`school-zone-factory` `titleCaseData` opt + grade-range identifier pill (§6a).
CHI shipped the engine surface plus its `school-site` chips rebuild in #183;
NYC (#71) and SF (#37) took their fork passes on the `v1.0.12` bump —
universal id pills on their court/ZIP/school-district layers, a compact
neighborhood card, and the §8a/§8b **School Location** chips rebuild (type
filter chips + typed rows + per-session persistence) mirroring Chicago's
reference. The three `school-site` cards now share one interaction model,
differing only in each metro's type taxonomy (CHI grade-band, NYC/SF
public/charter/private) and whether the feed carries a grade range.

## Backlog — researched candidates, deliberately not (yet) built

Every entry cites where it's recorded and the blocker. When one ships, move it into the
matrix; when one is rejected, move the rationale into a NO HONEST ANALOG footnote.

> **Read this first — what is actually open.** Most of what follows is a *completion
> log*, not a queue: an entry titled "… — SHIPPED/FIXED/RESOLVED (date)" is a record of
> work already done, kept for its rationale. Grepping this section for open work returns
> mostly noise, which is why "what's next?" is hard to answer from it. As of
> **2026-07-28** the genuinely open items are exactly these, and every one is blocked on
> a publisher rather than on build effort:
>
> | Open item | Blocker | Actionable? |
> |---|---|---|
> | Lake County municipal officeholders | no Lake body publishes names anywhere county-side | no — needs a new publisher |
> | Aurora per-seat contact | own site hard-403s; GIS has no officeholder fields; Will has names only; Archive is 2015–17 | no — see below |
> | DuPage municipal phones | DMMC prints no area codes and states no default | no — needs DMMC |
> | McHenry / Kendall / Joliet | hard WAF denies, data preserved, standing issues | no — rule-4 terminal |
> | Will's `party` field | deliberate non-ship (nonpartisan offices, local slate names) | no — decision, not gap |
> | **Statewide expansion (next 10 counties)** | nothing — research pass 1 done, pass 2 scoped | **yes — the live candidate** |
>
> **The Illinois *concept* frontier is closed — the *geographic* one is not.** Of the 40
> concepts in the matrix above, Chicago ships 35; the other five are correctly
> `n/a`/NO HONEST ANALOG (NYC-specific constructs, a countywide State's Attorney, and
> appointed transit boards). There are no unfilled cells. So growing Illinois means
> either *more counties for the concepts already built* — see the statewide-expansion
> entry below, which is the live candidate list — or *proposing new concepts* under
> `docs/EXPANSION_GUIDE.md` Part 5 (community college districts, Regional Offices of
> Education, sanitary/drainage districts and township road districts are the unresearched
> families).

**Open — Illinois**
- **RESEARCH PASS 4 (2026-07-30) — Winnebago SHIPPED; the Metro East is researched and
  waiting on a bridge.** Pass 1's border ring is exhausted, so this pass went after the
  large detached candidates. Winnebago (#1, 285,350) turned out **not** to be detached —
  it touches Boone — so its `county-board` ships here and the served area stays one ring.
  Madison (#2) and St. Clair (#3) are fully researched and ready to build, but they sit
  200 miles south; **the operator's call is that coverage grows as a connected region, so
  they wait** rather than shipping as an island.

  **STATUS 2026-07-30: all three SHIPPED, and so is the five-county bridge that
  made Madison and St. Clair reachable without an island.** The served area is
  now 19 counties in ONE ring, from the Wisconsin line to the Metro East.

  | concept | Winnebago (285,350) | Madison (265,859) | St. Clair (257,400) |
  |---|---|---|---|
  | `county-board` | **SHIPPED** — 20 districts, WinGIS `ElectedOfficials/26`, member + party 20/20 | **SHIPPED** — 26 districts, `CountyClerk/CBDWS/0`, **the fleet's richest**: official 26/26, party, term, e-mail 26/26, URL 26/26, phone 25/26, address 18/26 | **SHIPPED** — 28 districts, `SCC_voting_districts/2`, member name 28/28 (no contact) |
  | `county-precinct` | **SHIPPED** — 94, `WardsAndDistricts/7`, county-clerk jurisdiction only (Rockford runs its own election commission); no polling join published | **SHIPPED** — 191, `pollingid` GlobalID join measured **191/191**, the cleanest in the fleet | **SHIPPED** — 150, identity + board district only; the 103 polling places are keyed by a combined label ("Belleville9,10, 12 & 16") so the join is a recorded gap, not a guess |
  | `fire-district` | **none** as a county tiling (one department's own operational map only) | **SHIPPED** — 42, the fleet's **first contact-bearing fire entry**: dept head 39/42, address 41/42, phone 41/42, URL 30/42 (e-mail 3/42, not requested) | none published |
  | `park-district` | none | **SHIPPED** — 6, identity-only | none published |
  | `library-district` | none | **SHIPPED** — 18, identity-only | none published |
  | `judicial-subcircuit` | 17th — **already shipped** (pass 1) | 3rd — **already shipped**; the county republishes the same 4, unused | **structurally n/a** — 20th Circuit is not among PA 102-0693's nine |
  | `ward` | **SHIPPED** — Rockford's 14 wards w/ alderperson + e-mail, the first ward source outside the metro; Loves Park's 5 and Machesney Park's 6 ride the municipal roster instead | 31 wards, `official`/contact declared and **0/31 populated** | Belleville + O'Fallon, identity-only |
  | municipal officials | **SHIPPED** — 11 municipalities, 84 officials, the fleet's FOURTH full-governing-body county and the only one publishing bodies AS GIS LAYERS | — | — |

  **All three board rosters were cross-checked against the counties' own pages before
  anything shipped**, since a GIS attribute can go stale silently: St. Clair matched on
  five districts, Madison on four, Winnebago on four (D15 is "Chris Scrol" in the GIS and
  "Christopher Scrol" on the page — the GIS short form is what ships, being the source
  actually rendered). Winnebago's board page additionally carries per-district phone and
  address that the GIS declares and leaves empty on all 20 rows — a scraper, recorded in
  the backlog rather than guessed at. Winnebago also publishes a countywide **board
  chairman** (`ElectedOfficials/25`) that this entry does not yet fetch.

  **The discovery method now has a perfect record and a sharpened rule.** Hostname
  guessing failed again on all three (`gis.wincoil.gov`, `wingis.org/arcgis`,
  `gis.co.madison.il.us/arcgis` — all 404/dead); following the county's own site to a web
  map and reading its `operationalLayers` found all three on the first try. The sharpening:
  **the REST instance is not always at `/arcgis`** — WinGIS mounts at `/public`, St. Clair
  at `/server`, Madison at `/servera` and `/serverh`. And **layer ids are not 0-based** —
  Madison's are 40/41, Woodford's 2/8/3; a query against `/0` returns an *error envelope*
  that parses as an empty result, so "0 features" must never be read as "no data".

  **Winnebago precincts + board contact (SHIPPED 2026-07-30), and a measured
  city/county split.** The 94-precinct tiling covers the county OUTSIDE the City
  of Rockford, which runs its own Board of Election Commissioners — the
  Chicago/suburban-Cook shape repeating in a smaller city. Nothing on the service
  says so; it was found by gridding the county outline and noticing 12% of it had
  no precinct, then testing that hole against the TIGER place polygon: 130 of 131
  uncovered samples inside Rockford, 936 of 937 covered ones outside it. Shipping
  county-wide would have answered "no precinct" across Illinois's third-largest
  city with the layer on, so the entry declares `winnebagoOutsideRockfordCoverage`
  and reuses the Rockford outline already shipped for the ward layer.

  The `winnebago-board-contact` gap is CLOSED. It was recorded as one that
  "closes with work, not data", and that was right: the board page prints a phone
  and an official @board.wincoil.gov address per district, base64-obfuscated
  behind Joomla's spam wrapper (reading the rendered text would have collected
  the sentence "This email address is being protected from spambots" for twenty
  people). 20/20 e-mails, 19/20 phones, refreshed weekly.

  **The builder cross-checks rather than trusting either source.** The GIS and
  the board page are maintained separately, and a phone attached to the wrong
  person is worse than no phone — so every scraped row is matched to the GIS name
  the card will actually render, tolerating only a shortened forename
  ("Chris"/"Christopher"), and a district whose sources disagree ships no contact
  at all. Currently 20/20 match. The street address the page also prints is NOT
  collected: those are residences, the same call McHenry, Livingston and Sangamon
  made.

  **Winnebago municipal officials — the fleet's only GIS-published governing
  bodies (SHIPPED 2026-07-30).** WinGIS publishes one officeholder LAYER per
  municipality rather than a directory page or a PDF: 11 municipalities, 84
  officials, in three shapes the county never normalised — WIDE (one feature,
  one column per seat: President/Mayor + Trustee1..N), PER-WARD (Loves Park
  elects two aldermen per ward with a phone each; Machesney Park one trustee per
  district), and Rockford split across two layers (mayor on one, 14 alderpersons
  with city e-mails on the other). Rockford's wards also became the ward layer's
  first entry outside the metro.

  Three things the build had to get right, each of which failed quietly first:
  **(1)** the roster builder reads `person_phone`/`person_email`, not
  `phone`/`email` — emitting the plain names looks correct and is silently
  dropped, which is deliberate so a municipality's main line can never print as
  a trustee's direct line; **(2)** `build_municipal_ward_coverage.py` iterated a
  hardcoded entry tuple, so a newly added entry (rockford) produced no coverage
  feature and no error — the order is now derived from the entry table and an
  entry missing from it is fatal; **(3)** a transient WinGIS failure on layer 19
  shipped a Rockford with no mayor and still cleared the aggregate floor, so a
  failed layer is now fatal in the scraper and the county carries forward from
  the shipped roster instead.

  **Two municipalities have no head of government published**, and that is the
  source, not a parse failure: WinGIS carries council seats only for Loves Park
  and Machesney Park. They ship council-only rather than having a mayor inferred
  from the fact that cities have one.

  **A trap the bridge nearly walked into, caught by testing rather than reading.**
  St. Clair's precinct layer carries a `bdnum` column that looks exactly like a
  County Board district — small integers over roughly the right range, sitting
  next to the precinct name. Tested against the county's own board polygons it
  agrees on **23 of 150** precincts, no better than chance. Rendering it would
  have put a wrong board district on 127 precinct cards, with nothing failing.
  The board row comes from the spatial join every other county's precinct entry
  uses; `bdnum` is left unread and its meaning is unknown.

  **The bridge, and why it is the real cost.** Shortest verified chain from the served
  footprint to Madison is five counties (BFS over TIGER adjacency, ≥20 shared vertices):
  **Livingston → McLean → Logan → Sangamon → Macoupin**. Every link is a real shared
  border (LaSalle↔Livingston 418 shared vertices, the thinnest is McLean↔Logan at 73).
  Researched:

  | bridge county | pop | board geometry | officeholders | other |
  |---|---|---|---|---|
  | **McLean** | 170,954 | ✅ 10 districts, `Clerks/MyElectedRepresentatives/1` | ✅ in GIS — **two members per district** (the fleet's first multi-member board), each w/ party, term, directory URL | precincts w/ `POLLINGID` (Kendall join model) |
  | **Sangamon** | 196,343 | ✅ 29 districts, AGOL `CountyBoardDistricts2020_WithURLs` | ⚠️ no name in GIS, but a **per-district member URL**; the county's own pages carry name, party, term, address, e-mail, cell → 29-page scraper | `FireDistrictEtc` |
  | **Logan** | 27,987 | ✅ 6 districts, TCRPC `Logan_County_Districts_and_Zoning/39` | ❌ none in GIS → rule-4 branch 3 floor | precincts, fire zones, 6 library districts |
  | **Macoupin** | 44,967 | ❌ none published | ✅ Socrata `Elected Officials Directory` — board by district, 2 members each | 105 precinct polygons + polling places on its own Socrata portal |
  | **Livingston** | 35,815 | ❌ **no GIS presence at all** | ✅ full roster on the county page (district, name, party, term, e-mail, address) | nothing |

  **Livingston is the blocker, and it has a way through.** It publishes no GIS anywhere —
  no ArcGIS Online items, no self-hosted server, only a vendor assessor site. But the
  county defines its **three** board districts as *whole townships*, in prose on its board
  page, and the app already trusts TIGER township geometry. Checked: 30 published township
  names against TIGER's 30 for county 105 — **29 exact matches**, with the county writing
  "Newton" where TIGER has "Newtown"; 30 = 30 and every other name agrees, so the mapping
  is unambiguous. So Livingston's districts are buildable by dissolving TIGER townships per
  the published composition, with that one name reconciliation recorded rather than
  silently patched. The alternative first hop, **Woodford**, is worse: its board districts
  and precincts are PDF-only, and its "Fire Protection Districts" feature service is
  actually the parcel layer with a tax-code column — carrying owner names and billing
  addresses this app would never ship.
- **Boone + Grundy — RESEARCH PASS 3, `county-precinct` SHIPPED (2026-07-29); DeKalb NOT
  FOUND.** With LaSalle and Kankakee shipped, the border ring is down to Boone, DeKalb and
  Grundy. Two of the three are now partly built; the third could not be located.

  | concept | Boone (53,606) | Grundy (52,533) | DeKalb (100,420) |
  |---|---|---|---|
  | `county-precinct` | **SHIPPED** — 37, polling place carried ON the precinct feature | **SHIPPED** — 40, polling joined on `POLLINGID` (38/40; two share an id the polling layer omits) | — |
  | `county-board` | 3 districts, but published as **three separate single-feature layers** with no officeholder attribute — needs a merge loader *and* an officeholder source before rule 4 is met | **none published** | — |
  | `ward` (Belvidere) | **ready, high value** — `Clerk_and_Recorder/Belvidere_Wards`, 5 wards each carrying `ald_1`/`phone_1`/`ald_2`/`phone_2` | n/a | — |
  | `fire-district` | 5 polygons keyed by NUMBER only, no district name — a "Fire District 1" card is honest but near-useless, so not built | none published | — |
  | park / library | none published (the BCCD Park_Map is conservation-district *facilities*, not a district tiling) | none published | — |
  | `judicial-subcircuit` | **already answered** — Boone is the secondary county of the 17th Circuit, covered by the Winnebago entry | n/a — 13th Circuit has no subcircuits | n/a — 23rd, recorded at Kendall |

  **DeKalb County IL was not found, and that is the finding.** Its ArcGIS Online presence is
  dominated by DeKalb County **Georgia** (`DeKalbGISAdmin`, `djburge_DeKalbGIS`,
  `amore_DeKalbGIS` → `dcgis.dekalbcountyga.gov`, "Super Commissioner Districts", Druid
  Hills, Soapstone Ridge) — a same-name trap that would have shipped Georgia geometry into
  an Illinois app had the owner accounts been taken at face value. Field-qualified searches
  for the Illinois county returned only historical plat maps and university coursework, and
  the three plausible self-hosted hostnames (`gis.`/`maps.dekalbcounty.org`,
  `gis.dekalbcountyil.gov`) do not resolve or reset. **Pass 4 should start from the
  county's own site**, not from a portal search: that is how Boone's
  `maps.boonecountyil.org` and Grundy's `maps.grundyco.org` were both found — via a web
  map's `operationalLayers`, which is the only discovery route that has worked twice.

  **Two defects found by probing, not by reading.** Grundy's precinct cards first rendered
  with no polling place: `POLLINGID` exists on *both* layers but the service omits it unless
  it is named in `outFields`, and my first request left it off — the join key was there all
  along. And Boone stamps unincorporated precincts `Munic="County"`, its own shorthand, which
  rendered as a municipality *called* "County" until it was suppressed.
- **LaSalle + Kankakee — RESEARCH PASS 2 done, `county-board` SHIPPED (2026-07-29).**
  The two counties the pass-1 border-ring computation identified as both large and
  contiguous. Sources were determined for every concept the county-N+1 checklist asks
  about (`docs/EXPANSION_GUIDE.md` §2.5) before anything shipped, per rule 4:

  | concept | LaSalle (109,658) | Kankakee (107,502) |
  |---|---|---|
  | `county-board` | **SHIPPED** — 29 districts, [ArcGIS Online FeatureServer](https://services3.arcgis.com/H84yQSxNIj9pXjJ7/arcgis/rest/services/CountyBoardDistricts/FeatureServer), member in GIS attrs | **SHIPPED** — 28 districts, self-hosted `k3gis.net` `BASE/Elected_Officials/1`, member in GIS attrs |
  | `county-precinct` | **SHIPPED** — `PollingPlaceLocator/1` (119) + polling points, **119/119 exact join** on `USER_Precinct` | **SHIPPED** — `BASE/Elected_Officials/0` (59), name only, no polling join published |
  | `fire-district` | **none published** | **SHIPPED** — `BASE/Taxing_Districts2/10` (17), identity-only |
  | `park-district` | **none published** | **SHIPPED** — `…/5` (4), identity-only |
  | `library-district` | **none published** | **SHIPPED** — `…/3` (8), identity-only |
  | `judicial-subcircuit` | **structurally n/a** — 13th Circuit | **structurally n/a** — 21st Circuit |
  | municipal officials | ready, **full governing bodies** — the clerk's [Municipality Officials PDF](https://lasallecountyil.gov/DocumentCenter/View/1425/Municipality-Officials-PDF) carries president/mayor, clerk, treasurer and every trustee/alderperson **with ward numbers**, address and phone | **rule-4 floor** — no county-published roster found |

  **Both boards are rule-4 branch 1** (the Lake/Kane shape): the officeholder rides the
  county's own boundary GIS, so this shipped with **no scraper, no weekly workflow and no
  roster file** — measured populated 29/29 (name, e-mail, mailing address) and 28/28
  (name, party, phone, e-mail) respectively.

  **Recorded upstream gaps.** LaSalle's three phone columns are recorded *without an area
  code* ("672-2115") and the county states no default, so they are deliberately not
  rendered — the same call DuPage's municipal phones got; inventing 815 would be guessing
  how to reach an officeholder. Kankakee's board features carry a `chair` column set on
  only 2 of 28 rows, which does not describe a single countywide chair, so it is left
  unread rather than interpreted.

  **Judicial subcircuits are n/a for both, on evidence:** the PA 102-0693 enacted map
  covers nine circuits (Cook, 3rd, 7th, 12th, 16th, 17th, 18th, 19th, 22nd) and the app
  now ships **all nine** — neither LaSalle's 13th nor Kankakee's 21st is among them. Same
  recorded-n/a as Kendall's 23rd.

  **Discovery method that worked, for pass 3.** Pass 1's note stands (hostname guessing
  finds nothing; ArcGIS search needs field-qualified syntax) and this pass adds the step
  that actually pays: find the county's GIS *org account* with `owner:"<org>"` and
  enumerate everything it owns — `LaSalleCoGIS` and `k3gis_1` each surfaced their whole
  catalogue that way. Then follow a web map's `operationalLayers` to the services behind
  it: LaSalle's polling-place app is what exposed `gis.lasallecounty.org`, a second,
  self-hosted server carrying the precinct tiling that the ArcGIS Online org does not
  have. **A schema is not data** — Kankakee's taxing-district layers declare
  `telephone`/`website`/`email` on every row and populate **none** of them (0/21, 0/8,
  0/4, 0/17), so those entries will be identity-only when built.

  **Kankakee's special districts are partial tilings, correctly.** The county has no
  countywide fire, park or library coverage — Kankakee city runs a municipal fire
  department and sits in no library district — so those cards honestly report "this point
  isn't inside any district in this layer" there while resolving at Momence and Herscher.
  Verified in a browser against the services' real captured payloads.

  **LaSalle municipal officials — SHIPPED (2026-07-29), and LaSalle is the fleet's third
  full-governing-body county.** The clerk's Municipality Officials PDF yields **26
  municipalities / 206 officials** — head of government, clerk, treasurer and every
  trustee/alderperson, ward-numbered, with a phone on 187 of them. The shipped roster went
  **279 → 307 municipalities** and **185** of those are now full governing bodies. Millington,
  which Kendall also lists, moved to LaSalle on depth, exactly as `COUNTY_PRECEDENCE`
  intends.

  *The parser is the interesting part, and the obvious approaches are both wrong.* This is
  not the repo's first PDF source — `pypdf` already reads DuPage's, Kane's and Kendall's —
  but it is the first that needs word POSITIONS, so it adds a `pdfplumber` pin. A
  flattened `extract_text()` interleaves the six columns with the left-hand hall-address
  block, gluing an official's title onto a fragment of the village's address. Fixing that
  with a row grid then splits each record from its own phone, which renders ~2 pt above the
  name. And single-linkage clustering over all words **merges adjacent records**: the
  document's y-gap histogram runs continuously from 0 to 15 pt with *no empty band*,
  because the hall-address block and the phone column each keep their own line rhythm
  against the officials' 12.6 pt one. What works is anchoring records on the title+name
  columns only — those sit ~1 pt apart and keep a clean rhythm — then attaching the nearest
  unclaimed address/city/phone within 3.5 pt. The interleaved columns are never anchors, so
  nothing can chain through them.

  Three further traps, each measured: the municipality header does **not** reliably share a
  row with the official it heads (after a page break it lands one row *below* its own
  village president), so attribution pairs the header sequence with the head-of-government
  sequence in document order — 26 and 26, and the scraper refuses to emit if that equality
  breaks rather than mis-filing a block's first official. The cities print each ward twice
  ("Alderperson ward 1" and "City Alderperson ward 1" are the ward's *two* aldermen, not
  two offices). And some cells carry two overlapping text layers, which extraction
  interleaves character by character — recoverable for a header (`TTIITTLLEE` → `TITLE`)
  but *not* for a phone, where the digits could de-interleave two ways, so those are
  dropped: a missing phone is a gap, a wrong phone sends someone to a stranger.

  Cross-checked against a city's own published roster (the Aurora check pattern): Mendota's
  page lists mayor, clerk and all eight aldermen with wards, and the parse matches **all
  eleven** records including every ward assignment. One noted discrepancy — the county
  lists a Treasurer the city's elected-officials page omits, which in Illinois usually
  means the office is appointed there; the county's label is what ships.

  **Kankakee's municipal officials stay at the rule-4 floor:** no county-published roster
  exists, its GIS `Municipalities` layer declares contact columns and populates none of
  them (0/21), and the clerk site publishes no directory.
- **Office-pin geocoding: unit fragments and the metro bound — FIXED (2026-07-29).**
  Cards kept losing their office pin on addresses carrying "Room 230" / "Suite 104", and
  the question raised was whether to swap geocoders. Measured first, against the app's
  own corpus (409 addresses in `data/app/`, 37 carrying a unit fragment), issuing the
  request exactly as `poiGeocodeRequest` builds it:

  | | unit-bearing (37) | control (20) |
  |---|---|---|
  | as shipped | 5 (14%) | 16 (80%) |
  | after | **35 (95%)** | **17 (85%)** |

  Three causes, only one of which was the reported one. (1) `cleanPoiAddress` handled
  numeric units only, so letter units ("ROOM J", "BUILDING B", "Suite B"), PO boxes —
  including the parenthesized form Kane's roster uses — and the dash left behind by a
  removed floor all survived, 8 of the 37. (2) The search box never called the cleaner at
  all: `runGeocodeSearch` passed the typed string through verbatim, so a pasted
  letterhead address failed even though the POI path had handled that shape for months.
  On 12 paired Chicago queries the cleaner moved the box from 7/12 to 9/12 — which is
  also what the hand-stripped address scores, so it closes the entire gap the fragment
  opens. (3) The dominant cause was not formatting at all: `poiGeocodeRequest` bounded
  every lookup to `METRO_BBOX` while the county-clerk card answers **statewide**, so all
  ~95 downstate clerks failed on perfectly clean addresses. That is now
  `POI_GEOCODE_BBOX` (worksheet-driven, Illinois for this fork) — the rule is that the
  bound tracks the fork's **widest layer**, not its metro.

  Recorded because it settles the swap question: 35/37 matches what the US Census
  geocoder scores on the same corpus *with no cleaning at all*, so the remaining headroom
  no longer justifies a second provider. Census stays a documented fallback rather than a
  replacement — it loses 5 addresses Nominatim gets (it needs a complete address, where
  Nominatim's viewbox rescues a bare "4314 S. Cottage Grove Ave.") and, decisively for a
  static site, sends **no CORS header**, so it is reachable only via JSONP — remote script
  execution in an app whose posture is that every external string is sanitized. Chaining
  the two would reach 55/57 if that ever becomes worth the trust widening.
- **Statewide expansion: the next 10 counties — RESEARCH PASS 1 (2026-07-28).** The
  ultimate goal is all 102 counties. Today's seven cover **8,577,735 of 12,812,508
  Illinoisans — 66.9%** (2020 PL, via TIGERweb `tigerWMS_Census2020` layer 82, which
  carries `POP100` keylessly; the Census API needs a key). The next ten by population
  take that to **82.2%**:

  | # | County | 2020 pop | | # | County | 2020 pop |
  |---|---|---|---|---|---|---|
  | 1 | Winnebago | 285,350 | | 6 | Peoria | 181,830 |
  | 2 | Madison | 265,859 | | 7 | McLean | 170,954 |
  | 3 | St. Clair | 257,400 | | 8 | Rock Island | 144,672 |
  | 4 | Champaign | 205,865 | | 9 | Tazewell | 131,343 |
  | 5 | Sangamon | 196,343 | | 10 | LaSalle | 109,658 **adjacent** |

  **Contiguity is not on offer.** Computed from TIGER geometry (≥20 shared vertices with
  the current footprint), the border ring is exactly **Boone, DeKalb, Grundy, Kankakee,
  LaSalle** — so only LaSalle (#10) and Kankakee (#11, 107,502) are both large and
  contiguous. Every other candidate is a detached island, which the **scope mask** must
  absorb: `metro-outline.json` is currently one dissolved ring, and a detached county
  makes it a MultiPolygon. `build_metro_outline.py` dissolves by edge-cancellation and
  chains each closed ring independently, so it already handles that — but its `--check`
  anchors and the single-ring assumption in the guide's §4.5 note both need revisiting at
  that point.

  **SHIPPED 2026-07-28 — the three unshipped judicial subcircuits.** Winnebago (17th),
  Madison (3rd) and Sangamon (7th) are live as `judicial-subcircuit` dispatch entries,
  the first counties outside the seven-county metro. The layer now answers for **ten**
  counties beyond the metro's seven, since each circuit spans more than its headline
  county. Coverage for these three is the **subcircuit geometry itself** rather than a
  county outline — the one deviation from the metro entries' pattern, taken because a
  county-outline test would have needed ten new files to describe where three layers
  answer, and the subcircuits tile their circuit exactly so containment in them IS the
  coverage. Verified against real points in both the headline and secondary counties
  (Rockford + Belvidere/Boone, Edwardsville + Greenville/Bond, Springfield +
  Jacksonville/Morgan), with Peoria correctly matching none and no point landing in two
  circuits. Original finding below.

  **Free win, already in the repo: three unshipped judicial subcircuits.**
  `data/source/raw/Enacted_Judicial_Sub_Circiuts.zip` (the PA 102-0693 enacted map, the
  same archive Kane and McHenry were built from) contains **nine** circuits; the app
  ships **six**. Parsing the raw `.shp` polygons and testing county centroids against
  them identifies the three that are sitting unused:

  | Circuit | Subcircuits | Counties |
  |---|---|---|
  | **17th** | 2 | **Winnebago**, Boone |
  | **3rd** | 4 | **Madison**, Bond |
  | **7th** | 7 | **Sangamon**, Greene, Jersey, Macoupin, Morgan, Scott |

  That is candidates **#1, #2 and #5** each getting `judicial-subcircuit` with no new
  source, no new layer, and the conversion path Kane/McHenry already proved — the
  cheapest real expansion available. It is a `registerCountyLayer` dispatch entry per
  county (Part 2's invariant), plus the `data/*.geojson` → `build_embedded_boundaries.py`
  step and a `polygonCountyEntry`.

  **NOT researched — the bulk of the work.** This pass established the ranking and
  settled one concept. For all ten counties the other five dispatchable concepts
  (**county-board** districts + member roster, **county-precinct**, **fire-district**,
  **park-district**, **library-district**) and the **municipal-officials** clerk
  directory are unresearched — roughly 60 source investigations, and rule 4 requires each
  county's officeholder sourcing to be settled in the same change that ships its
  boundary.

  **Discovery-method notes, so pass 2 does not repeat pass 1's dead ends:** guessing
  hostnames (`gis.<county>.org/arcgis/rest/services`, `maps.…`) found nothing across five
  counties — modern county GIS is ArcGIS Online-hosted, not self-hosted. Both
  `arcgis.com/sharing/rest/search` and `hub.arcgis.com/api/v3/datasets` return **0** for
  multi-word natural-language queries; only field-qualified forms (`title:Winnebago`,
  `tags:…`) return anything, so per-county discovery needs that syntax or manual portal
  identification. Suggested order for pass 2: Winnebago, Madison, Sangamon first, since
  those three would already be partly built.
- **Aurora per-seat contact — RECORDED GAP (2026-07-28), no reachable source.** Aurora is
  the metro's second-largest city and its 12 council members (10 wards + 2 at-large) all
  render with correct districts, but with **no phone or e-mail**. Aurora spans four
  counties and resolves from **Will** under the builder's depth precedence — Will
  publishes full governing bodies where Kane, which holds most of Aurora, publishes heads
  only — and Will's flipbook carries names without member contact. All four routes to
  fill it were measured and are closed: `aurora-il.org` returns **403 to every client**
  (Microsoft-IIS, 306-byte body — a hard deny, not a challenge); Aurora's own ward
  FeatureServer is open but carries only `WARD`/`URL`/acreage, no officeholder fields;
  the Will directory has names only; and the Internet Archive's newest useful captures of
  the city site are **2015–2017**. The card is therefore already at the honesty floor —
  name, ward, and the per-ward page link the GIS supplies (`dxUrl` → "Ward website").
  Upgrading needs Aurora to unblock, or a hand-verified curated file on the
  McHenry/Kendall precedent.

**Completion log (kept for rationale — not a queue)**

**Fleet-wide**
- **Card-order conformance audit — RUN 2026-07-20** (sweep of all 79 cards against
  procedure step 2a and against each layer's source). Result: 73 of 79 conform or
  deviate with a justified reason (nearest-N lists; no-officer geography/identity
  concepts; honesty-rule link-only judicial bodies). Fixes shipped from the findings:
  - *Engine v1.0.7*: `cps-network-factory` location-before-contact row swap;
    `chamber-factory` profile-link label now follows the actual href (a directory
    fallback no longer masquerades as the member's own page).
  - *CHI `ward`*: the roster's real phone column (`ward_phone`) was never matched, so
    the Office Phone row had been silently dead — fixed; rows reordered to
    location→contact; per-ward `website` (in the roster all along) now rendered, with
    the chicago.gov lookup as fallback — ward was the only officeholder card with no
    link.
  - *NYC*: `police-precinct` latent contact-before-location order fixed; the state
    legislature scraper/builder now capture each member's official page (Open States
    `links`) so the chamber cards gain per-member links on the next weekly roster PR.
  - *SF `early-voting`*: drop-box features' `supervisorial_district` (present on
    37/38 sites) now surfaces on the card line.
  Recorded as fine-as-is (checked, no action): NYC school zones carry no school
  address/grades in the DOE datasets (verified live — `addressKeys`/`gradeKeys`
  deliberately unwired, now documented in code); CHI/SF/NYC fire-station + SF/NYC
  library sources genuinely carry no phone; SF `supervisor-district` upstream
  (`hcgx-vtsb`) carries no contact fields; congress rosters ship the D.C. office only
  (a builder-scope enrichment candidate, below). Cosmetic unfetched-or-unrendered
  fields (SF/NYC `post-office` STATE, NYC `school-site` city/zip, NYC `early-voting`
  county) trimmed or left recorded here.
- **Congress district-office enrichment** — **shipped for Chicago (2026-07).**
  `build_congress_roster.py` now joins unitedstates/congress-legislators'
  `legislators-district-offices.json` by bioguide id, so `congress-roster.json`
  carries each rep's primary district office (street + phone) and D.C. office
  alongside name/party. The CHI congress card was migrated off its bespoke block
  onto the shared `registerIlgaChamber` factory (new backward-compatible
  `districtPrefix` opt keeps the "IL-7" header), so it now surfaces a map-pinned
  District Office + D.C. Office like the ILGA chambers. The factory change ported
  byte-identical to NYC/SF. **Follow-ups:** migrate the NYC/SF congress cards onto
  the factory and enrich their builders the same way (their card layout is
  unchanged until then); and the same source family offers committee assignments
  and social media (both bioguide-keyed) as further per-member enrichment.

**San Francisco**
- _(empty — BART Director districts, formerly the strongest unbuilt candidate in the
  fleet, shipped as `bart-director` in July 2026: geometry from BART's own ArcGIS org,
  roster hand-verified against bart.gov/about/bod.)_

**New York City** (from `docs/archive/METRO_EXPANSION_PLAYBOOK.md` Part II "Future layers")
- Surrogate's Court judges — borough geometry ready; roster unverified.
- FDNY Divisions — Socrata `68m2-uzcb` is map-type (export-route geometry only).
- NYPD sector NCO names — no structured source exists (honesty rules say wait).
- Full community-board member lists — per-borough HTML, non-uniform; only chair/manager
  are machine-readable today.
- LCGMS principal enrichment for `school-site` — needs a Socrata app token.
- Mayor / Public Advocate / Comptroller — real citywide electeds, but an at-large
  citywide polygon adds zero point-discrimination (the at-large rule: link, don't map).
- District Leader / State Committee — party-internal; recorded as "recommend never".

**Chicago / Illinois** (from `docs/archive/STATEWIDE_EXPANSION_PLAYBOOK.md` §4/§7 +
`docs/BUILD_PLAYBOOK_1.md` §2b)
- Statewide judicial circuits (25) — blocked: the county→circuit table has no
  authoritative machine-readable source (ilga.gov 403s; illinoiscourts.gov JS-rendered);
  hand-encoding violates the never-guess rule.
- Judicial subcircuits — **complete for the metro (2026-07)**: every PA 102-0693
  subcircuit county in coverage has shipped inside `judicial-subcircuit` (Cook
  live from county GIS L5; Will/DuPage/Lake from their county GIS; Kane 16th +
  McHenry 22nd pre-built from the enacted ilsenateredistricting.com shapefile
  ZIP archived in data/source/raw/, each 100% on the 2,000-point agreement
  protocol — Kane's services are permission-locked, McHenry publishes none).
  Kendall's 23rd Circuit received NO subcircuits under PA 102-0693 (absent from
  the enacted set) — structurally n/a, not a gap.
- Statewide voting precincts — hardest class: 102 clerks, non-uniform, frequently
  redrawn. **The metro is complete (2026-07)**: suburban Cook (1,430, the
  Clerk's `precinctHistorical` L0 current fabric — the Socrata `k7sw-w3b8`
  geometry — coverage-gated to Cook-outside-Chicago since city precincts are
  the BOE's `ward-precinct` layer) + all six collar counties ship inside
  `county-precinct`; Chicago's own precincts were day-one (`ward-precinct`).
  Beyond the metro remains the recorded statewide frontier (95 more clerks).
- Collar-county boards — **complete (2026-07): all seven counties shipped.**
  Cook + Will + DuPage + Lake + Kane + McHenry + Kendall (Kendall 2026-07:
  five dispatch entries from the county's own ArcGIS Enterprise
  (maps.co.kendall.il.us/server) — board 2 districts (the current line: the
  post-2020-census reapportionment kept it, so the County_Board_2010 service
  IS the current map; members + Chairman + contact joined from a
  weekly-scraped roster of the county's Akamai-fronted directory — the
  scraper that motivated the officeholder-sourcing-at-expansion rule),
  fire 10 FPDs / park 5 / library 9 on the county's
  parcel-derived tax-code tilings, precincts 78 with township names derived
  from the county's own layers and the county's per-precinct polling-place
  assignment joined by GlobalID).
  **McHenry retro-debt: RESOLVED (2026-07)** — the board card now joins
  `mchenry-county-board-members.json` (from the county's own directory,
  hand-verified with the weekly refresh attempted: 18 members across the 9
  districts plus the countywide-elected Chairman, phones + emails + profile
  links), clearing the last deferred-scraper debt under
  `docs/COUNTY_LAYER_CONSOLIDATION.md` rule 4 (McHenry 2026-07: five
  dispatch entries — board 9 district-number-only, 22nd-Circuit judicial
  pre-built, fire 19 and library 13 after excluding the county's own
  Z-filler/municipal/rescue-squad rows, precincts 223 — the county GIS
  carries no officeholder or contact fields, so cards link the county's own
  directories) (Kane 2026-07: the Lake recipe again — five dispatch entries, zero new layers/scrapers at expansion; the KaneCo_IL_* hosted family carries board member names, precinct board-district fields, and fire/park/library officer + office contact. The board card later gained a weekly-scraped contact roster — party/office phone/email + the countywide-elected Chair — from the county's SharePoint directory list, the rule-4 GIS+pipeline composition) (DuPage board 2026-07: boundary + coverage
  + a weekly-scraped member roster — 18 members across 6 districts + the
  countywide Chair. Lake 2026-07: the first county to land entirely as dispatch
  entries — zero new layers, and zero scrapers, because Lake's own boundary GIS
  carries each member's name/phone/official email/district page, verified
  against the county's published directory). 2026-07 enrichment checks
  (post-ship audit of each board card against its county's full published
  surface) upgraded Lake (GIS office address + newsletter, scraped
  Chair/Vice-Chair tags), Kane (SharePoint contact roster), and McHenry +
  Kendall (per-member profile links each scraper already collected but the
  builders dropped; rosters re-verified name-for-name via each directory's
  Archive snapshot — both counties block live fetch). The sweep is
  complete: no county-board card leaves published officeholder data
  unconsumed. Future counties join the consolidated `county-board` layer
  as dispatch entries, not new layers
  (`docs/COUNTY_LAYER_CONSOLIDATION.md`).
- Municipal governments (mayor / village president + city council / village board) —
  **ALL SEVEN METRO COUNTIES SHIPPED 2026-07-28** (`docs/EXPANSION_GUIDE.md` Part 2.4;
  governance rules 4–5 in Part 2.3). 280 of the metro's 284 municipalities resolve on one
  weekly-CI roster joined onto the statewide `municipality` card by place GEOID — the
  `county` + `il-county-clerks.json` shape, not a new layer and not a county-dispatched
  one; 47 cross-county municipalities dedupe to their deepest source. Depth is honest per
  county, because that is what each county publishes: **full governing body** Cook (Clerk
  DOEO API) + Will (Clerk directory) = 156; **head of government** DuPage (DMMC
  directory) + Kane / McHenry / Kendall (clerk yearbooks) = 82, their cards linking the
  municipality's own site for the board; **contact only** Lake = 41 — see the recorded
  gap below. Statewide aggregators are a verified dead end (IML paid print; Comptroller's
  "CEO" is often the appointed manager; Google Civic reps endpoint sunset) — per-county
  clerk sources are the only honest architecture. **Chicago shipped 2026-07-28** from the
  same Cook directory (head + City Clerk + City Treasurer; its 50 ward seats stay the
  `ward` layer's answer and the card says so). Cook person rows also carry
  **`nextElection`**, the year a seat is next on the ballot — staggered, so it varies
  within one board.
- **Term data — SHIPPED for all three publishing counties (2026-07-28).** Each is labelled
  as its own source labels it, because they are three different facts and collapsing them
  into one label would state something none of them says: Cook publishes the NEXT election
  date (`nextElection`, 1,038 people → "Next election 2029"), Will the year a term EXPIRES
  (`termExpires`, 215 → "Term expires 2027"), Kendall the date an officer was last ELECTED
  (`lastElected`, 9 → "Elected 2025"). A person carries at most one, since a municipality
  resolves to exactly one county source. The card hides a next-election or term-expiry
  year already in the past — a few seats in both feeds are stale, and printing one would
  state something false — while a last-elected year is past by definition and always
  shows. Cook publishes a last-elected date too, but the next election is the more useful
  fact and the card shows that, so the roster keeps last-elected ONLY where it is a
  source's only term fact; storing both would add ~1,000 fields nothing reads.
  **Still unconsumed: Will's `party`** (176 of 302 records). Municipal offices in Illinois
  are largely nonpartisan and several Will "parties" are local slate names (BTS = Better
  Together For Steger), so surfacing it as a party badge would misrepresent what it is —
  deliberately deferred, not overlooked.
- **Term data on the City Ward card — SHIPPED (2026-07-28), all five entries.** The
  Municipality card stopped listing districted councils, so a ward-elected resident's seat
  appears only here; showing the term fact on one card and not the other would have split
  the same data across two answers. `municipalTermNote()` is now shared by both, so they
  cannot word or gate it differently. The four suburban entries (Cook-suburban, Evanston,
  Will, Aurora) already had the fields and needed only the render. **Chicago needed a new
  source:** the City's own alderperson roster (`htai-wnw4`) publishes contact but no term
  fields at all, so the Clerk's `CHICA` jurisdiction type — all 50 ward seats, verified
  complete — was added to `cook_municipal_officials_scraper.py`, normalized from its
  ordinal wording ("Chicago, 1st Ward" → "City of Chicago" + "Ward 1") to group with the
  citywide records and match every other seat's district string. Two deliberate limits:
  the seats land on Chicago's roster `board`, which the Municipality card still suppresses
  as districted, so that card is byte-identical and the 50 names never swamp it; and the
  Clerk's person-level **`appointed` flag is NOT carried onto the Chicago ward card** —
  the term fact is the SEAT's (all 50 wards run on one cycle, so it holds whoever sits
  there, needing no name match), whereas `appointed` describes a named individual and the
  two rosters format names differently enough — 12 of 50 differ by middle initial,
  nickname or suffix — that pinning it to the City's name would be a heuristic.
- **Municipal roster build — per-source preservation (2026-07-28).** The first
  live run of `update-municipal-officials.yml` had six of ten scrapers succeed and four
  403 GitHub's runner IPs: McHenry and Kendall (every rung, incl. the Archive — McHenry's
  newest snapshot was 509 days old against a 45-day guard, Kendall had none), plus DuPage
  and Joliet, which both answer a developer machine but not the datacenter ranges. The
  all-ten build gate meant one permanently blocked source froze the roster for *every*
  county, so the gate is now Cook + Will (the two full-governing-body sources, which the
  builder refuses to build without) and every other source is preservable — it carries
  forward its shipped entries, re-entering through the ordinary precedence/`merge_contact`
  paths, and the run and PR body both name what was preserved. Standing issues #199–#202
  track the four blocks. **DuPage was the tractable one and is now laddered
  (2026-07-28):** its Cloudflare edge keys on the client's *network* rather than its
  fingerprint — a developer machine gets 200 where the runner gets 403 for a
  byte-identical request, which is exactly why it passed in development and failed on
  its first live run — so the scraper gained `requests → playwright → wayback`, with the
  browser rung load-bearing. Each rung returns the whole directory (URL + bytes) rather
  than one fetch, because only the session that cleared the challenge can fetch the PDF
  the page names. Its Archive rung is real but expected to refuse: the newest snapshot
  was 194 days old against the 45-day guard and predates the current edition.
  **Joliet is rule-4 terminal, not laddered (decided 2026-07-28).** Its edge is Akamai
  serving a hard WAF deny — a 408-byte static page with an `x-reference-error`, not a
  solvable challenge — so the Playwright rung it already had fails exactly as plain
  requests does; this is the McHenry/Kendall class, not DuPage's. An Archive rung was
  evaluated and deliberately declined: the captures are good (the archived index still
  yields all nine bio links and the bio pages still carry their e-mails) but the newest
  index capture was 69 days old against the 45-day guard, so a conventional rung would
  refuse every run, and widening the guard for one source would spend a fleet-wide
  honesty rule on data preservation already covers — Joliet's last-good entry came from
  a live scrape of the real site, which beats a dated copy of it. McHenry/Kendall remain
  terminal for the same reason (they block the Archive's crawler outright).
  **Blocked-source taxonomy, worth keeping:** a *challenge* (Cloudflare) is beaten by a
  browser rung; a *network deny* keyed on the client's ASN is beaten by a browser only
  if it is really a challenge underneath; a *hard WAF deny* (Akamai) is beaten by
  nothing, and the honest move is preservation plus a standing issue. Measure which one
  you have — the response headers and body size say so — before writing a rung.
- **Two scrapers hardened after Cloudflare tightened (2026-07-28).** Both surfaced on the
  fleet-status dashboard, both are the *challenge* class (browser-clearable), and in both
  cases the count guards refused to write, so no shipped data was ever lost.
  **CPD** (`chicagopolice.org`) began 403ing every client, with its browser rung reporting
  "challenge did not clear within 20s"; the interstitial is a genuine managed challenge
  ("Just a moment…", `challenge-platform`, `__cf_chl`), not a block, so the challenge
  budget went 20s → 60s. The cost is bounded because the browser context is reused across
  all 22 district pages, so only the first fetch pays it. An Archive rung was evaluated
  and rejected: only the finder page has a 200 capture, the district pages are 301/403
  (the crawler was blocked too), so it could supply links but not commanders.
  **County clerk** (`elections.il.gov`) had no ladder at all and started 403ing the runner
  while still answering a developer machine 200 — the DuPage class — so it gained
  requests → playwright. Its browser rung drives the page rather than replaying the
  postback: the county dropdown is an ASP.NET AutoPostBack, so selecting the option *is*
  the submit and the browser generates the viewstate tokens itself, which makes the
  fallback sturdier than the primary rung as well as edge-proof.
- **The wash now means "at least one county-specific layer answers here", and
  that widened it by five counties (2026-07-30).** Bond, Jersey, Greene, Morgan
  and Scott have no dispatch entries of their own, but they are the SECONDARY
  counties of shipped judicial circuits — Bond in Madison's 3rd, the other four
  in Sangamon's 7th — so a resident there gets a real county-specific card and
  was still being told "beyond here only the statewide layers answer". That is
  the same defect as the stale-county-list bug below, arriving from the opposite
  direction: not a served county dropped from the list, but a served county
  nobody thought to list, because its coverage came through a layer keyed to a
  CIRCUIT rather than to a county. The list's meaning is now stated in the
  builder: every county where a county-specific layer answers, not every county
  with an entry. Fayette and Pike — which border the new five but sit in no
  shipped circuit — are OUTSIDE anchors, so "a circuit's secondary counties"
  cannot quietly become "everything nearby". 24 counties, still one ring.
- **Out-of-scope wash moved from the city line to the metro edge (2026-07-28).** The wash
  had been drawn from the ERSB school-board tiling — Chicago's limits — so it greyed out
  suburban Cook and all six collar counties. Measured against the registered layers, that
  had stopped being true: Chicago resolves **32** of 39, suburban Cook **25**, DuPage and
  Will **21**, Kane 20, Lake 19, McHenry and Kendall **17**. Coverage tiers across the
  metro rather than stopping at the city line, so the wash now marks the 7-county edge,
  beyond which only the statewide layers answer; the city/suburb difference is carried by
  the cards, which already hide an out-of-coverage layer outright. Removing the wash
  entirely was rejected — the tiers are real and a wash-free map would claim parity the
  data doesn't support. Geometry is `data/app/metro-outline.json` (one dissolved polygon,
  62 vertices, 2.5 KB, `scripts/build_metro_outline.py`); the existing per-county outline
  files could not be reused because they were simplified independently and their shared
  borders would not cancel in the in-browser dissolve.

  **The list is now DERIVED-CHECKED, not anchor-checked (2026-07-30).** The fix
  below added INSIDE anchors, which stops a listed county being dropped — but it
  could not stop a NEW county shipping unlisted, because anchors only assert
  counties someone already thought to name. `validate_index.py` check 8 closes
  that: it reads the per-county dispatch keys straight out of index.html, maps
  them through `DISPATCH_COUNTY_FIPS`, and fails the merge gate if any is absent
  from `METRO_COUNTY_FIPS` — or if a key has no FIPS entry at all, which is the
  case that used to slip through silently. Layers keyed by municipality rather
  than county (`ward`) are exempt by an explicit list, so opting out is a
  decision someone writes down. Verified by probe: dropping Madison from the ring
  fails with six named layers, and a fictitious "peoria" entry fails as unknown.

  **The county list then went stale, and the wash lied for two passes (fixed 2026-07-30).**
  Research passes 2 and 3 shipped LaSalle, Kankakee, Boone and Grundy layers without
  revisiting `METRO_COUNTY_FIPS`, so the wash kept greying out all four — it told a
  Kankakee user "beyond here only the statewide layers answer" while five Kankakee layers
  were answering, and told an Ottawa user the same while LaSalle's county board and its
  119-precinct tiling resolved. Nothing failed, because the builder's anchors only assert
  the counties already in the list; a served county that is missing from it is invisible to
  every gate. Now eleven counties, still **one ring** (94 vertices, 3.8 KB) because all four
  additions came from the pass-1 border ring and are mutually contiguous. Two guards added
  against a third recurrence: the four new counties are INSIDE anchors, and the checklist
  step (`docs/EXPANSION_GUIDE.md` §2.5 step 1) now says the coverage outline and this list
  move together. The OUTSIDE list is the other half — a county named there cannot be
  quietly served, because shipping it fails the build.
- **Lake County municipal officeholders — RECORDED GAP (not a parity debt).** No Lake
  body publishes a municipal roster anywhere county-side: county/Clerk elected-officials
  pages cover only county offices, county GIS carries no officials data, and the Lake
  County Municipal League publishes no member directory (double-verified 2026-07-27).
  Lake's 41 cards therefore ship hall address, phone, e-mail, and the official-site link
  and name nobody — rule-4 branch 3, the honesty floor. Upgrading needs either a Lake
  source that starts publishing, or a deliberate decision to scrape 50+ heterogeneous
  municipal sites, which the source ladder rejects as a source of record.
- **Mayor-level counties leave no published data unconsumed, with one exception to
  watch:** DuPage's DMMC directory prints phone numbers with **no area code** and no
  stated default, so those entries ship `phone: null` rather than a dead `tel:` link. If
  DMMC ever adds area codes — or DuPage County itself starts publishing a directory —
  that is the upgrade. Appointed administrators/managers printed beside the elected
  officers in four sources are deliberately excluded (the card's section is titled
  "Other Elected Officials"); surfacing them needs a separately-labeled section first.
- **Districted seats now render once, on the layer that answers them (2026-07-28).** Where
  the City Ward layer publishes a municipality's seat geometry, the Municipality card no
  longer repeats the council: it names the head, says "elected by ward/district — turn on
  the City Ward layer", and lists only the seats that layer CANNOT answer. Two deliberate
  limits, both information-preserving: **at-large colleagues stay listed** (Joliet elects
  five by district and three citywide — nothing else answers the three), and a
  **municipality the ward layer doesn't cover keeps its full list** (Berwyn, Waukegan),
  since suppressing seats with nowhere to send the reader would lose them. The card reads
  the same prebuilt `municipal-ward-coverage.json` the ward layer's own coverage test
  uses, so the two cannot disagree.
- **Will ward-city per-seat contact + the two omitted cities — SHIPPED 2026-07-28.**
  The bounded per-city exception (`docs/EXPANSION_GUIDE.md` Part 2.4): Crest Hill's staff
  directory supplies per-alderperson phones and Wilmington's officials page per-alderperson
  e-mail, neither of which any Will County source publishes; the same pass supplies
  **Lockport and Wilmington's rosters outright**, closing the gap below. The clerk remains
  the roster of record — for a municipality the county covers this adds contact only.
  Per-seat contact now renders on the `ward` layer's seat card as well as here.
  **Joliet — BUILT 2026-07-28**, and the recorded non-build was wrong on both counts.
  joliet.gov fingerprints the HTTP client, not the path: a complete browser header set
  gets a plain 200, so Playwright carries it exactly as it does McHenry and Kendall. And
  jolietcity.org is not the city's site at all — it is a parked domain serving a 114-byte
  lander, which is why it read as "client-rendered". The city publishes a council index
  plus a page per member; all nine (mayor + eight council members) now carry a direct
  phone and e-mail. **A recorded "unbuildable" is a snapshot of what was tried, not a
  property of the source** — this one cost one re-test.
- **Name-collision sweep — RUN 2026-07-28, 3 findings, all fixed.** Prompted by the
  wrong-Wilmington bug below: an audit of every name-keyed lookup in the pipeline and the
  app, checked against real data rather than by inspection.
  - *Fixed, latent:* `municipalRosterByName` (the `ward` layer's seat join — its features
    carry a municipality NAME, not a GEOID) scanned the statewide roster and returned the
    FIRST name match. No duplicate exists in today's 282-entry roster, so nothing was
    wrong on screen, but a statewide roster or a downstate county would have made it
    answer with another municipality's council. It now returns nothing on an ambiguous
    name, so the card falls back to the boundary's own official field.
  - *Fixed, LIVE BUG:* `municipalSeatHolder` returned the FIRST board member matching a
    ward number — but Crest Hill, Lockport and Wilmington each elect TWO alderpersons per
    ward, so half of those residents' representation was hidden, and hidden *more* once
    the Municipality card stopped listing districted councils and made this card the only
    place those seats appear. Now returns every holder (`municipalSeatHolders`); a ward's
    GIS contact attaches only where the ward has ONE holder, since it identifies one
    person.
  - *Fixed, latent:* `build_municipal_ward_coverage.py` deduped its municipality list by
    NAME, which would silently drop a second municipality sharing a name; it now dedupes
    on the resolved GEOID.
  - *Checked and sound, recorded so the next sweep can skip them:* the 101-key county
    clerk roster (Illinois county names are collision-free, verified); every other
    `data/app` roster is district-number keyed; nothing joins by TOWNSHIP name (those
    collide heavily across Illinois); the Cook tax tilings key on agency number; Lake's
    Chair/Vice-Chair tag is district-scoped with a surname guard; and
    `build_municipal_officials_roster.py` already fails hard on an ambiguous place name.
  - **Statewide fact worth keeping:** exactly two Illinois incorporated-place names are
    not unique — **Wilmington** (Will 1782101 / Greene 1782088) and **Windsor** (Shelby /
    Mercer). Only Wilmington touches the metro. Any new name→place lookup must be
    county-qualified or fail loudly.
- **`municipal-ward-coverage.json` resolved the wrong Wilmington — FIXED 2026-07-28.**
  Illinois has two Wilmingtons, and the coverage builder's first-wins name lookup picked
  Greene County's village (GEOID 1782088) for the Will entry, putting the coverage polygon
  180 miles downstate: the City Ward layer **hid in the real Wilmington** and switched
  itself on in a village with no ward services. Resolution is now county-qualified, with a
  hard failure on any name the entry's county can't disambiguate — the same rule the roster
  builder already used. Worth re-checking in any fork: a name collision fails silently.
- **Three malformed office e-mails — FIXED 2026-07-28.** The Will directory's flattened
  text ran the next label onto the domain, so Coal City, Elwood and Joliet shipped dead
  mailto addresses (`cityclerk@joliet.govTreasurer`,
  `fred.hayes@villageofelwood.comTrusteesDarryl`). Same glue class as the Oswego treasurer
  name, on the e-mail field instead: addresses are now cut at the TLD when a capitalized
  label follows. Worth re-checking after any flattened-text parse — a broken address looks
  like data until someone clicks it.
- **Will's Lockport and Wilmington were missing from the municipal roster — CLOSED above.**
  Both are City Ward layer entries with published ward geometry, but neither appears in
  `municipal-officials.json`: the Clerk's flipbook directory omits their entry HEADERS from
  its text layer entirely (Wilmington's alderpersons appear orphaned mid-page after
  Naperville's entry; Lockport's block is absent), so the scraper's entry split cannot see
  them. This is a source-side text-layer defect, not a parse bug — no amount of parsing
  recovers text the flipbook does not contain. Consequence: a Lockport or Wilmington point
  resolves a ward polygon with no seat-holder joined, the same class as the recorded Skokie
  disagreement. Fixing it needs a different source for those two cities.
- Suburban municipal wards — **SHIPPED 2026-07** into the consolidated `ward` layer
  (see the concept row above), which is where the remaining gaps are now recorded:
  **Berwyn** elects 8 alderpersons by ward but appears in no published ward-boundary
  source (it is absent from Cook's ward layer), so its seats show on the Municipality
  card with no ward geometry behind them; **Waukegan** publishes a ward map as PDF
  only; and no county-level ward layer exists in Lake/DuPage/Kane/McHenry/Kendall.
  The Skokie source disagreement is **RESOLVED (2026-07-28)** — see below.
- **Skokie's trustee districts — RESOLVED 2026-07-28.** Cook GIS carried four Skokie
  district polygons while the Clerk's directory listed all six trustees as
  municipality-wide, so a Skokie point resolved a district with nobody attached. The
  village settles it: its own "2025 Electoral Changes" page states that from the April
  2025 consolidated election "four geographic election districts now exist, with voters
  in each district electing one trustee. In addition, two trustees are elected
  at-large." So the GIS was right and the Clerk's roster was the incomplete side — the
  correct six people, without their district assignments.
  `skokie_trustee_districts_scraper.py` reads the assignments (and a per-trustee e-mail)
  from the village's Board of Trustees page; the Clerk stays the roster of record and the
  builder fills only the fields the county left empty. Skokie's card now shows the
  ward-layer pointer plus its two at-large trustees, and a Skokie district point names
  its trustee. **A guard now prevents recurrence:** the builder cross-checks
  `municipal-ward-coverage.json` against the roster and warns for any municipality with
  ward geometry but no districted seat — the check that found Skokie was the only one.
  Two trustees share the surname Levy, which is why the scraper's e-mail matcher
  disambiguates on given name and refuses an ambiguous match (it initially handed Lissa
  Kimani's address — the sweep's own lesson, re-learned).
- Park districts statewide (~350) — no statewide GIS; per-county sources. Will +
  DuPage + Lake + Kane + Kendall shipped inside the consolidated
  `park-district` layer (Will: commissioners in GIS attrs; DuPage: name-only —
  its GIS carries no commissioner/contact fields; Lake: district office
  contact in GIS attrs; Kane: board president + contact; Kendall: name-only
  tax-code tiling).
  **McHenry: recorded gap (2026-07)** — the county publishes park *facilities*
  (~350 point/asset features), not park-district boundaries, so no honest
  McHenry entry is possible until the county ships a district tiling.
- Cook County GIS tax-agency tilings — **the original "never wired" trio is
  resolved (2026-07)**: TIF shipped as `tif-district` (the Clerk's un-yeared
  current tiling, clerkTaxDistricts L18, 418 agencies), MWRD shipped as `mwrd`
  (one district, nine at-large commissioners, in/out coverage), and **forest
  preserve is a recorded drop, not a gap**: the Forest Preserve District of
  Cook County's taxing district is coterminous with the county (zero point
  discrimination) and its board is the county Board of Commissioners **ex
  officio** — the `county-board` Cook card carries that fact as a row, so FPD
  representation is already answered; the Clerk's "Forest Preserve Holdings"
  layer maps the FPD's exempt land (an asset map — same drop class as
  McHenry's park facilities). (Earlier waves: the library L20+L19, fire L17,
  and park L23 tilings shipped 2026-07 as Cook entries in their consolidated
  layers.) **Still-unwired Clerk tilings sighted in the same
  `clerkTaxDistricts` catalog** (recorded candidates, not evaluated):
  Home Equity Assurance (L5), Mosquito Abatement (L9), Sanitary (L12),
  Special Service Area (L13), Street Light (L14), Drainage (L1). Kendall's
  `TIF_Districts` service is the recorded second-county entry that would
  consolidate `tif-district`.
- **Governance-standardization pass (2026-07, now `docs/EXPANSION_GUIDE.md` Part 1 + Appendix A)** —
  the pre-county-expansion audit of all 39 layers by governance level / function /
  election geometry, fixing the expansion invariant (a new county adds dispatch entries
  and roster rows, never toggles). Its recorded candidates, each detailed there:
  Chicago's citywide officers (Mayor / City Clerk / City Treasurer) on the `municipality`
  card — **SHIPPED 2026-07-28**, closing the suburban-parity asymmetry from the same Cook
  Clerk directory (jurisdiction type `CHIWD`); the card's council section points at the
  `ward` layer rather than listing 50 seats; election-authority dispatch for the precinct / early-voting
  concepts (a collar-clerk early-voting tranche is the natural first increment);
  at-large / commission-county boards render as `county`-card roster rows, never a
  polygon; `school-district-*` card enrichment (every non-Chicago board is elected
  whole-district → Pattern A rows; ISBE directory candidate); township officers captured
  by the municipal clerk-yearbook scrapers when those five counties are built (verify
  depth at build time); countywide elected officers beyond the clerk (per-county, rule
  4); a law-enforcement row on `municipality` + Sheriff among county officers (never a
  boundary no agency publishes); the `mwrd` → `sanitary-district` concept conversion
  trigger (second-county tiling; the body is unique, the class isn't); an Appellate
  District row on `il-supreme-court` (same five districts) and the elected ROE regional
  superintendent (DERIVE-class, verify the Cook/Chicago carve-outs); statewide source
  candidates for the `school-site` / `library` point layers.

---

## Per-fork inventories

### Chicago — 39 layers

| id | label | group | pattern | source | roster / join | coverage |
|---|---|---|---|---|---|---|
| `il-supreme-court` | IL Supreme Court District | political | Polygon | pre-built (PA 102-0011 shapefile) | link-only | — |
| `congress` | U.S. House District | political | Bespoke | pre-built (TIGERweb L0, STATE=17) | `congress-roster.json` (weekly CI; incl. each rep's district office + D.C. office from congress-legislators — the 2026-07 enrichment) | — |
| `il-senate` | IL State Senate District | political | Chamber | pre-built (TIGERweb L1) | `il-senate-members.json` (weekly CI) | — |
| `il-house` | IL State House District | political | Chamber | pre-built (TIGERweb L2) | `il-house-members.json` (weekly CI) | — |
| `county` | County | geography | Bespoke | live TIGERweb State_County | `il-county-clerks.json` (weekly CI from ISBE; Peoria deliberately absent) | — |
| `school-district-secondary` | High School District | schools | Polygon | live TIGERweb School L1 | — | outsideChicagoSchoolCoverage |
| `school-district-unified` | Unified School District | schools | Polygon | live TIGERweb School L0 | — | — |
| `school-district-elementary` | Elementary School District | schools | Polygon | live TIGERweb School L2 | — | outsideChicagoSchoolCoverage |
| `township` | Township / County Subdivision | geography | Polygon | live TIGERweb CouSub | — | — (subOf `county`) |
| `municipality` | Municipality | geography | Bespoke | live TIGERweb Places | `municipal-officials.json` (weekly CI; all seven metro counties + Chicago's citywide officers, 280 municipalities — head of government + board + other elected officers + hall contact, joined by place GEOID; depth per county: full body Cook/Will, head-only DuPage/Kane/McHenry/Kendall, contact-only Lake) | — |
| `judicial-subcircuit` | Judicial Subcircuit | political | CountyDispatch | Cook County GIS L5 (20 subcircuits) + L27 (municipal districts) · Will County ArcGIS · DuPage County ArcGIS (`Judicial_Subcircuits`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L1) · pre-built `kane-judicial-subcircuits.json` + `mchenry-judicial-subcircuits.json` (PA 102-0693 enacted shapefile) — no Kendall entry: its 23rd Circuit received no subcircuits under the act | link-only (each card links its circuit's court; Cook adds the Municipal District + courthouse row) | OR of cook/will/dupage/lake/kane/mchenry county coverages |
| `county-board` | County Board District | political | CountyDispatch | Cook County GIS L9 · Will County ArcGIS · DuPage County ArcGIS (`County_Board_Dist_new`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L0) · Kane County ArcGIS (`KaneCo_IL_County_Board` L1) · McHenry County ArcGIS (`McHenry_County_Board_Districts` L0) · Kendall County ArcGIS Enterprise (`County_Board_2010` — the CURRENT 2-district map: the post-2020-census reapportionment kept the line, Dec 2021 hearing) · LaSalle County ArcGIS (`CountyBoardDistricts`) · Kankakee self-hosted `k3gis.net` (`BASE/Elected_Officials/1`) · Winnebago WinGIS (`ElectedOfficials/26`, mounted at `/public` not `/arcgis`) · Livingston **derived** (`livingston-county-board-districts.json` — TIGER townships dissolved per the county's published composition; it publishes no GIS) · McLean (`Clerks/MyElectedRepresentatives/1`) · Logan via Tri-County RPC (`Logan_County_Districts_and_Zoning/39`) · Sangamon AGOL (`CountyBoardDistricts2020_WithURLs`) · Madison (`CountyClerk/CBDWS/0`, on `/servera`) · St. Clair (`SCC_voting_districts/2`, on `/server`) | Cook: live office join (same server); Will: `will-county-board-members.json` (weekly CI); DuPage: `dupage-county-board-members.json` (weekly CI; + countywide Chair); Lake: member + phone/email/office address/district page + newsletter on the boundary GIS itself (live, county-edited; re-verified vs the county directory 2026-07-23) + `lake-county-board-roles.json` (weekly CI — the Chair/Vice-Chair tags the GIS lacks, applied only on a name match so a missed reorganization degrades to role-less rows); Kane: member names on the boundary GIS (verified incl. the 2026 D2/D9 appointments) + `kane-county-board-members.json` (weekly CI from the county's SharePoint Board Members list API — party, official office phones, emails, profile links, and the countywide-elected Board Chair; GIS names stay as hover + fallback, cross-checked 24/24 against the roster); Kendall: `kendall-county-board-members.json` (10 members incl. the Chairman — a District 2 member, not a separate countywide seat — phones + emails + per-member profile links; 2026-07 enrichment check re-verified all 10 names 1:1 against the directory's 2026-03 Archive snapshot); McHenry: `mchenry-county-board-members.json` (18 members + the countywide-elected Chairman, phones + emails + per-member profile links; the DuPage countywide-chair shape; 2026-07 enrichment check re-verified all 19 names 1:1 against the directory's 2026-05 Archive snapshot — the county publishes no party or committee data, the one missing phone (D3) is confirmed unpublished at the source, and members' street addresses are residences, deliberately not collected). Both hand-verified 2026-07-23 against the counties' own directories: the counties block ALL automated fetch (direct, real-browser, and the Archive's crawler — SPN2 error:no-request), so the weekly engine-ladder scrapers run green and track the block on standing issues, resuming automation the moment any rung unblocks. LaSalle, Kankakee and Winnebago are all **rule-4 branch 1** — the member rides the county's own boundary GIS, so no scraper, no roster file and no weekly workflow: LaSalle 29/29 (name, e-mail, mailing address; its area-code-less phones deliberately unrendered), Kankakee 28/28 (name, party, phone, e-mail), Winnebago 20/20 (name, party, term year — its address/phone columns are declared and empty on every row, and the richer per-district contact on the county's board page is a backlog scraper, not a guess) . Pass 4's bridge counties: **McLean** 10 districts electing TWO members each, both seats + parties + profile links on the boundary GIS 10/10 (branch 1); **Sangamon** 29, GIS carries the district and a per-district MEMBER URL but no name, so a weekly scraper walks exactly those 29 URLs (29/29 names + parties, 27 e-mails, 22 phones); **Livingston** 3 multi-member districts, boundary AND roster both derived — townships per the county's published composition, members scraped weekly, with an explicit `vacancies` count because the directory lists a "Vacancy" seat that must be counted and never named; **Logan** 6, rule-4 branch **3** — the GIS carries no officeholder and the county's only roster is a salary publication with no district against any name, so the card says so and links the board (recorded gap); **Madison** 26, the fleet's RICHEST board source — official/party/term/phone/e-mail/per-district page all on one feature (26/26 name, party, e-mail, URL; 25/26 phone); **St. Clair** 28, branch 1 at its thinnest — name 28/28 and nothing else. Winnebago, McLean, Madison and St. Clair were each spot-checked against their county's own board page before shipping | OR of cook/will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/winnebago/livingston/mclean/logan/sangamon/madison/st-clair county coverages |
| `ccbr` | Cook County Board of Review District | political | Bespoke | pre-built (PA 102-0012 shapefile) | `ccbr-roster.json` (weekly CI from cookcountyboardofreview.com) | cookCountyCoverage |
| `fire-district` | Fire Protection District | safety | CountyDispatch | Cook County GIS L17 (Clerk fire tax-agency tiling) · Will County ArcGIS · DuPage County ArcGIS (`Fire_Protection_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L4) · Kane County ArcGIS (`KaneCo_IL_Districts_Fire` L1, IDOR-coded districts only) · McHenry County ArcGIS (`Fire_Districts` L0, 19 after the loader excludes the 8 'Z NO FIRE DISTRICT' fillers, the municipal Crystal Lake city-fire row, and the overlapping Marengo rescue-squad district — a 70 ILCS 3105 ambulance body, not a fire protection district) · Kendall County ArcGIS Enterprise (`Fire_Protection_Districts` L0 — the parcel-derived tax-code tiling, 10 FPDs after excluding the municipal 'CITY OF JOLIET FIRE DISTRICT' rows; hairline no-result gaps at unparceled slivers) | Cook: name-only; Will: trustees in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: chief + office contact in GIS attrs; McHenry + Kendall: name-only | OR of cook/will/dupage/lake/kane/mchenry/kendall county coverages |
| `dupage-county-special-police` | DuPage Special Police District | safety | Polygon | DuPage County ArcGIS (`Special_Police_Districts_`, "Real Estate Tax Code polygons") | link-only (elected DuPage County Sheriff; unincorporated-area police-tax district) | dupageCountyCoverage |
| `park-district` | Park District | geography | CountyDispatch | Cook County GIS L23 (Clerk park tax-agency tiling, incl. the Chicago Park District) · Will County ArcGIS · DuPage County ArcGIS (`Park_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L11) · Kane County ArcGIS (`KaneCo_IL_Districts_Park` L1) · Kendall County ArcGIS Enterprise (`Park_Districts` L0 tax-code tiling, 5 genuine districts — Fox Valley/Joliet/Oswegoland/Plainfield/Sandwich) — McHenry: recorded gap, publishes facilities not district boundaries | Cook: name-only; Will: commissioners in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; Kendall: name-only | OR of cook/will/dupage/lake/kane/kendall county coverages |
| `library-district` | Library District | geography | CountyDispatch | Cook County GIS L20 (Library Tax District) + L19 (Library Fund) · Will County ArcGIS (`Library_District`) · DuPage County ArcGIS (`Library_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L8) · Kane County ArcGIS (`KaneCo_IL_Districts_Library` L1) · McHenry County ArcGIS (`Library_Districts` L0, 13 after the loader excludes 6 'Z_None' fillers + the lone municipal Crystal Lake city row) · Kendall County ArcGIS Enterprise (`Library_Districts` L0 tax-code tiling, 9 bodies incl. the municipal Joliet/Yorkville city-library funds — Kendall's tiling records EVERY library taxing body, the Cook-style complete shape, so its municipal rows stay) | Cook: agency name + a Type row distinguishing district vs municipal fund; Will: trustees in GIS attrs (sparse); DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; McHenry + Kendall: name-only | OR of cook/will/dupage/lake/kane/mchenry/kendall county coverages |
| `school-board` | Elected School Board District | political | Bespoke | pre-built (ERSB SB15 shapefile) | `school-board-members.json` (hand-curated) | chicagoCoverage |
| `cps-hs-network` | CPS Network (High School) | schools | CpsNetwork | Socrata `aupu-jt2g` | chief in dataset props | chicagoCoverage |
| `cps-network` | CPS Network (K-8) | schools | CpsNetwork | Socrata `pnta-kuqa` | chief in dataset props | chicagoCoverage |
| `ward-precinct` | Ward Precinct | political | Bespoke | Socrata `i8fv-xe4b` | — | chicagoCoverage (subOf `ward`) |
| `ward` | City Ward | political | CountyDispatch | Socrata `p293-wvbd` | live Socrata `htai-wnw4` join | chicagoCoverage |
| `police-beat` | Police Beat | safety | Bespoke | CPD ArcGIS | — | chicagoCoverage (subOf `police-district`) |
| `police-district` | Police District | safety | Bespoke | CPD ArcGIS | `cpd-district-info.json` (weekly CI, Playwright) | chicagoCoverage |
| `ccpsa-district-council` | CCPSA District Council | safety | Bespoke | shares `police-district` geometry | `ccpsa-district-councils.json` (weekly CI) | chicagoCoverage |
| `mwrd` | Water Reclamation District (MWRD) | geography | Polygon | Cook County GIS (`politicalBoundary` L21 — the Clerk's tax-agency boundary, 1 district) | none elected per sub-area (nine commissioners at large) — card links mwrd.org's board page | cookCountyCoverage (in-county fringe outside the district honestly reports "No result") |
| `tif-district` | TIF District | geography | Polygon | Cook County GIS (`clerkTaxDistricts` L18 — the Clerk's un-yeared CURRENT tiling, 418; retired year editions archive in the `Tax_Increment_Finance_District_Boundaries` service) | no elected body (TIFs are municipal ordinance districts) — card shows the Clerk agency number + links the Clerk's TIF-reports page | cookCountyCoverage (most points are in no TIF) |
| `community-area` | Community Area | geography | Polygon | Socrata `igwz-8jzy` | — | chicagoCoverage |
| `zip-code` | ZIP Code | geography | Polygon | live TIGERweb ZCTA | — | — |
| `cps-high` | CPS High School Zone | schools | SchoolZone | Socrata `xg7c-d8rm` (year-versioned) | zoned-school POI | chicagoCoverage |
| `cps-middle` | CPS Middle School Zone | schools | SchoolZone | Socrata `fyff-53xy` (year-versioned) | zoned-school POI | chicagoCoverage |
| `county-precinct` | Voting Precinct | geography | CountyDispatch | Cook County GIS (`precinctHistorical` L0, the Clerk's current suburban fabric, 1,430 — same geometry as Socrata `k7sw-w3b8`) · Will County ArcGIS `Precincts_2022` · DuPage County ArcGIS `Precincts_2024` (current 600-precinct map) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L7, 431) · Kane County ArcGIS (`KaneCo_IL_ElectionsPrecincts` L1, 292) · McHenry County ArcGIS (`Precincts` L0, 223) · Kendall County ArcGIS Enterprise (`Voting_Precincts_and_Polling_Places` L1 `status='A'`, 78 — township names derived at load from the county's own townships layer, the assigned polling place joined by GlobalID from L0) | County Board district via spatial join (Cook: Commissioner District; Kane: carried on the features); Kendall also shows the county's own polling-place assignment; each card links its county clerk | suburban-Cook (in Cook AND NOT Chicago — city precincts are the BOE's `ward-precinct` layer) OR will/dupage/lake/kane/mchenry/kendall county coverages (subOf `township`) |
| `cps-elementary` | CPS Elementary School Zone | schools | SchoolZone | Socrata `x72b-38qv` (year-versioned) | zoned-school POI | chicagoCoverage |
| `school-site` | School Location (nearest N) | schools | Bespoke nearest | CPD-org ArcGIS `Schools` | — | chicagoCoverage |
| `police-station` | Police Station | safety | NearestPt | USGS National Map structures L53 (metro bbox) | — | — (metro-wide) |
| `fire-station` | Fire Station | safety | NearestPt | USGS National Map structures L51 (metro bbox) | — | — (metro-wide) |
| `post-office` | Post Office | geography | NearestPt | USGS National Map structures L38 | — | — |
| `library` | Library | geography | NearestPt | Socrata `x8fc-8rcq` | — | chicagoCoverage |
| `early-voting` | Early Voting Site | political | NearestPt | hand-curated `early-voting-sites.json` (per election; sites double as the secured drop boxes; WATCH.md row) | — | chicagoCoverage |

### NYC — 27 layers

| id | label | group | pattern | source | roster / join |
|---|---|---|---|---|---|
| `borough` | Borough / County | geography | Bespoke | pre-built (offline anchor) | `borough-officials.json` clerk entries (operator-verified; appointed, labeled) |
| `judicial-district` | NY Supreme Court Judicial District | political | Polygon | pre-built (counties → districts derivation) | link-only |
| `borough-president` | Borough President | political | BoroughOffice | shares `borough` geometry | `borough-officials.json` (operator-maintained) |
| `district-attorney` | District Attorney | political | BoroughOffice | shares `borough` geometry | same roster |
| `congress` | U.S. House District | political | Chamber | pre-built (TIGERweb L0, STATE=36) | `congress-roster.json` (weekly CI) |
| `municipal-court` | Civil Court District | political | Polygon | pre-built (offline anchor) | link-only |
| `state-senate` | NY State Senate District | political | Chamber | pre-built (TIGERweb L1) | `ny-senate-members.json` (weekly CI; API keys) |
| `school-district` | Community School District | schools | Polygon | Socrata `8ugf-3d8u` | superintendent link-only |
| `cec` | Community Education Council | schools | Bespoke | shares `school-district` geometry | `cec-members.json` (weekly CI, placeholder until scrape lands) |
| `fire-battalion` | FDNY Battalion | safety | Polygon | DCP ArcGIS | — |
| `council` | City Council District | political | Bespoke | Socrata `872g-cjhh` | `council-members.json` (weekly CI) |
| `community-district` | Community District / Board | political | Bespoke | Socrata `5crt-au7u` | live Socrata `ruf7-3wgc` join (chair/manager, labeled appointed) |
| `election-district` | Election District | political | Bespoke | DCP ArcGIS (paged, ~4,200) | — (subOf `state-assembly`) |
| `state-assembly` | NY State Assembly District | political | Chamber | pre-built (TIGERweb L2) | `ny-assembly-members.json` (weekly CI) |
| `police-sector` | NYPD Sector | safety | Bespoke | Socrata `5rqd-h5ci` | — (subOf `police-precinct`) |
| `police-precinct` | NYPD Precinct | safety | Bespoke | Socrata `y76i-bdw7` | `nypd-precinct-info.json` (weekly CI) |
| `zip-code` | ZIP Code (MODZCTA) | geography | Polygon | Socrata `pri4-ifjk` | — |
| `neighborhood` | Neighborhood (NTA 2020) | geography | Polygon | Socrata `9nt8-h7nd` | — |
| `hs-zone` / `ms-zone` / `es-zone` | School Zones | schools | SchoolZone | Socrata `ruu9-egea` / `t26j-jbq7` / `cmjf-yawu` (year-versioned) | zoned-school POI |
| `school-site` | School (nearest 3) | schools | NearestPt | NYSED ArcGIS L2/3/4 (paged) | — |
| `police-station` | Police Station | safety | NearestPt | Socrata `ji82-xba5` (FacDB) | — |
| `fire-station` | Firehouse | safety | NearestPt | Socrata `hc8x-tcnd` | — |
| `post-office` | Post Office | geography | NearestPt | USGS National Map L38 | — |
| `library` | Library | geography | NearestPt | Socrata `feuq-due4` (all 3 systems) | — |
| `early-voting` | Early Voting Site | political | NearestPt | live NYS GIS elections service L1 | — |

### SF — 16 layers

| id | label | group | pattern | source | roster / join |
|---|---|---|---|---|---|
| `congress` | U.S. House District | political | Chamber | pre-built SF-clipped (TIGERweb L0, STATE=06) | `congress-roster.json` (weekly CI) |
| `ca-senate` | CA State Senate District | political | Chamber | pre-built SF-clipped (TIGERweb L1) | `ca-senate-members.json` (weekly CI, OpenStates) |
| `ca-assembly` | CA State Assembly District | political | Chamber | pre-built SF-clipped (TIGERweb L2) | `ca-assembly-members.json` (weekly CI) |
| `bart-director` | BART Director District | political | Bespoke | BART's own ArcGIS org (Board_of_Directors_District_Boundary, 9 districts) | `bart-directors.json` (hand-verified per election cycle; WATCH.md rows) |
| `election-precinct` | Election Precinct | political | Bespoke | Socrata `jg6x-23ig` (2022 map, 514 precincts) | — (subOf `supervisor-district`; polling-place lookup link) |
| `supervisor-district` | Supervisor District | political | Bespoke | pre-built (DataSF `hcgx-vtsb`, water-trimmed; offline anchor) | `sf-supervisor-members.json` (weekly CI) |
| `police-district` | Police District | safety | Polygon | pre-built (DataSF `d4vc-q76h`; offline anchor) | — |
| `zip-code` | ZIP Code | geography | Polygon | live TIGERweb ZCTA | — |
| `neighborhood` | Neighborhood | geography | Polygon | pre-built (DataSF `j2bu-swwd`; offline anchor) | — |
| `elementary-attendance-area` | Elementary Attendance Area | schools | Bespoke | Socrata `e6tr-sxwg` (year-versioned) | — (lottery caveat on card) |
| `police-station` | Police Station | safety | NearestPt | Socrata `rwdu-9wb2` | — |
| `fire-station` | Fire Station | safety | NearestPt | Socrata `nc68-ngbr` (City Facilities filter) | — |
| `school-site` | School Location | schools | NearestPt | Socrata `7e7j-59qk` | — |
| `post-office` | Post Office | geography | NearestPt | USGS National Map L38 | — |
| `library` | Library | geography | NearestPt | Socrata `fhhu-wqa7` (support facility excluded) | — |
| `early-voting` | Voting Center & Ballot Drop-off | political | NearestPt | hand-curated `early-voting-sites.json` (incl. 37 drop boxes; WATCH.md row) | — |

---

## Adding or changing a layer — the procedure

1. Consult the matrix first: if a sibling already ships the concept, reuse its recorded
   pattern and source-hunting notes (`docs/EXPANSION_GUIDE.md` §§4.3, 4.6–4.7); if a
   sibling recorded a drop, check whether the rationale applies to your metro before
   re-researching.
2. Build per the guide (`docs/EXPANSION_GUIDE.md` Part 5: worksheet entry → regenerate → registration → source manifest
   → docs), and **in the same change** update: the coverage-map JSON above, the fork's
   inventory table, the concept matrix row (add the row if the concept is new
   fleet-wide), and — if the layer resolves a Parity debt or Backlog entry — move that
   entry accordingly.
1a. **Officeholder sourcing is part of the expansion, not a follow-up** (2026-07 rule,
   `docs/EXPANSION_GUIDE.md` Part 2 rule 4): the change that ships a new
   county's/metro's boundary also determines and BUILDS its officeholder story —
   GIS attrs verified against the published directory where the boundary service
   carries them; otherwise a scraper + builder + weekly PR-opening workflow in the
   same change (bot-managed sites use the requests→Playwright→Internet-Archive engine ladder);
   only when no verifiable source exists does the card fall back to linking the
   official body, with the gap recorded here.
2a. **Card content order (fleet convention):** the result card leads with the layer name
   (card header), then the district identifier, then — wherever a verifiable source
   exists — the representative(s)/officeholder(s), the office location, contact info,
   and a link to more detail, in that order. Deviate only where the concept demands it
   (nearest-N lists, layers with no elected officer) — and when identity/location/contact
   data exists in the layer's source but isn't on the card yet, record the gap in the
   Backlog rather than shipping it silently.
2b. **Card construction (engine-v1.0.10+, docs/CARD_RENDER_API.md):** new and edited
   cards render through the shared card-helpers vocabulary — person rows with
   badges/notes/committee expanders, office groups, nearest rows, link rows, the
   generic field stack — with the district identifier in the header pill
   (`cardIdentifier`), the official link in the footer (`primaryLink`), and name-only
   layers as `compact` cards. The helpers are data-only by contract: never pass HTML
   (`renderFieldList` and the factories' caller-HTML opts are legacy paths kept alive
   only for unmigrated fork call sites, and are scheduled for removal once the
   fleet-wide grep hits zero). The content order in 2a maps onto the vocabulary as:
   pill → person rows → office group → contact line → footer link.
3. If you decide a concept **won't** ship in a metro, add the NO HONEST ANALOG footnote
   with the rationale and source of truth. Silence is the only wrong answer.
4. The weekly fleet-status run cross-checks the coverage map against every fork's live
   worksheet; a mismatch WARNs on the "Fleet status" issue until the guidebook and the
   fleet agree.

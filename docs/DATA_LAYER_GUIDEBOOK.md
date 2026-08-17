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
      "id": "adams-county-board-roster",
      "concept": "County board members",
      "area": "Adams County",
      "counties": [
        "adams"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Adams County publishes its 7 board districts as map data, but its website refuses every automated visit, so the card can show which district you are in without naming who represents it.",
      "blocker": "Checked 2 Aug 2026, when the county's districts and precincts were added: adamscountyil.gov answers every request with a 391-byte Access Denied from its Akamai edge — a flat refusal rather than a puzzle a browser could solve, the same kind that blocks Joliet — and the Internet Archive has saved the site's front page but never its board page. The county's own mapping service is open and complete, which is why the districts, the 92 precincts and Quincy's wards are all here; only the list of people is missing.",
      "wanted": "The list of board members by district from any source that permits automated reading — the county's own page becoming reachable, an Archive capture of it, or a Clerk directory."
    },
    {
      "id": "alexander-county-board",
      "concept": "County board",
      "area": "Alexander County",
      "counties": [
        "alexander"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Alexander County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. alexandercounty.illinois.gov answers 200 and is the county's own site, with a County Board page naming Chairman Joe Griggs and Vice Chairman Bruce Sims; alexandercountyil.org, the Clerk's e-mail domain, also resolves. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
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
      "summary": "Aurora's 12 council members show with the right wards but no phone or email yet. The site that was blocking us no longer does, and the update is queued.",
      "blocker": "Re-checked 31 Jul 2026, and the old blocker is gone: Aurora has moved to www.aurora.il.us and the new site is open to us. All 12 aldermen's pages publish a city email address and the Alderman's Office phone. The ward boundary data itself carries no officeholder details, so contact has to come from those 12 pages.",
      "wanted": "Nothing from readers — reading those 12 pages is already on our to-do list."
    },
    {
      "id": "blocked-crawlers",
      "concept": "Roster refresh",
      "area": "McHenry, Kendall and DeKalb",
      "counties": [
        "mchenry",
        "kendall",
        "dekalb"
      ],
      "kind": "blocked",
      "layer": "county-board",
      "summary": "Three county directories turn away the computer that checks them each week, so their board member lists are checked by hand or on a delay. The names on the cards are current either way.",
      "blocker": "Re-checked 31 Jul 2026: McHenry's and Kendall's directories refuse every request from a server. What has improved is that the Internet Archive now holds complete 2026 captures of both board directories (McHenry 20 May, Kendall 13 Mar), so an Archive-based refresh is newly possible for the board lists. McHenry's municipal yearbook page has no capture newer than 6 Mar 2025, and Kendall's municipal list has never been archived at all. DeKalb joined 2 Aug 2026 and is much the mildest of the three: it turns away some of the machines the weekly check runs from and not others, so the refresh works some weeks by itself. Its list was confirmed current on 2 Aug 2026.",
      "wanted": "A machine-readable list from any of the three directories, or any mirror they permit automated access to."
    },
    {
      "id": "bond-county-board-districts",
      "kind": "no-source",
      "concept": "County board districts",
      "area": "Bond County",
      "layer": "county-board",
      "counties": [
        "bond"
      ],
      "summary": "Bond names all five board members by district, but publishes no district boundaries — so the county is served only by its 3rd-Circuit subcircuit.",
      "blocker": "Researched 8 Aug 2026, closing an absence that had NO record at all: Bond is served as a judicial-circuit secondary, its board did not surface, and nothing said why. FORM SETTLED — DISTRICTED: bondcountyil.gov/bond-county-board/ lists Board Districts 1-5 with one member each and a county e-mail apiece (Chris Timmerman 1, Bernard Myers 2, Jacob Rayl 3, Wesley L. Pourchot 4, Jeff Rehkemper 5), so this is a geometry ask and NOT the at-large County-card path. GEOMETRY IS ABSENT, measured not assumed: the county runs a real ArcGIS Online org (bondcountygis.maps.arcgis.com, service root services.arcgis.com/VbP0KHITyLTMBTy3) whose 24 feature services were enumerated in full — parcels in five vintages, zoning, townships, municipal boundaries, floodplain, cemeteries, K12 school boundaries and FPD_Boundaries — with NO board-district layer and NO precinct layer among them. A DECOY TO NAME BEFORE IT COSTS SOMEONE THE BUILD: searching ArcGIS Online for \"Bond districts\" returns a feature service titled exactly \"Bond Districts\", which is municipal BOND (debt-financing) districts in DuPage County, owner Tamara.Freihat_DuPage — the word is the county's name and a finance term, so this is the easiest decoy in the file to walk into. NOT YET ASKED.",
      "wanted": "The five board districts as map data, or a written description of which townships or precincts make up each — plus precinct boundaries if the description is precinct-based, since the county publishes none. The member-by-district list on the board page is the authority to check any submission against."
    },
    {
      "id": "boone-fire-names",
      "concept": "Fire protection districts",
      "area": "Boone County",
      "counties": [
        "boone"
      ],
      "kind": "data-quality",
      "layer": "fire-district",
      "summary": "Boone County's five fire districts now show, but by number — the county publishes no names for them.",
      "blocker": "Shipped 3 Aug 2026, having been withheld until then on the reasoning that a card reading “Fire District 1” told a reader nothing they could act on. Asking the County Clerk settled it in the opposite direction from the one expected: Amy Ohlsen replied with names, and then volunteered that she had “just done a google search to get these names,” and that “when we complete tax extensions, it is just 1-5.” So the names are not a county record and are not used; the numbers are, because they are what the county's own tax extensions run on, and a numbered district that says it is numbered is the honest form of this data rather than a degraded one. The boundary layer carries a single `district` column and nothing else.",
      "wanted": "A county-published list matching Boone's fire district numbers to district names — from the county itself rather than assembled by search."
    },
    {
      "id": "boone-municipal-officials",
      "concept": "Municipal officials",
      "area": "Boone County",
      "counties": [
        "boone"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Boone's five municipalities show a name and a link only. The clerk's yearbook covers all five, but the newest edition posted predates the April 2025 election.",
      "blocker": "The clerk's “Boone County, Illinois Year Book” is exactly the right kind of source — all five municipalities, and Belvidere's alderpersons by ward with contact details — but the newest edition posted is 2024, and it names three Belvidere aldermen the April 2025 election replaced. The regional council of governments publishes a membership list only, and the county's municipal boundary data carries no contact or officeholder details.",
      "wanted": "A post-April-2025 edition of the yearbook on the clerk's page. Belvidere's current council can be built separately from county data and is already queued."
    },
    {
      "id": "boone-park-library-districts",
      "concept": "Park and library districts",
      "area": "Boone County",
      "counties": [
        "boone"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "Boone's park and library districts are not shown — the county publishes no boundary for either.",
      "blocker": "Re-checked 31 Jul 2026 across the county's mapping server (56 datasets) and its online map catalogue (360 items): no park or library district boundaries anywhere, and every item labelled “park” turns out to be a conservation-district facility map. The districts do exist on paper — the clerk's yearbook prints the Belvidere Park District commissioners and the Ida Public Library board with contact details.",
      "wanted": "Park and library district boundaries from the county. The yearbook's trustee lists are ready to go alongside them."
    },
    {
      "id": "brown-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Brown County",
      "counties": [
        "brown"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Brown County's 14 voting precincts are not shown, and the county's own election reports are scans rather than text.",
      "blocker": "Checked 2 Aug 2026 when the county was added: Brown publishes no precinct boundaries, and no county items appear in any public map catalogue. Its election summaries and precinct reports are posted as scanned images — readable by a person, not by software — so even the precinct NAMES cannot be lifted from them automatically. (A separate warning for anyone searching: browncountyil.org is a captcha-parked decoy. The county's real site is browncoil.org.)  NOT YET ASKED: this records what the county's WEBSITE shows, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Brown County's precinct boundaries as map data, and ideally election reports with a text layer. The board half is already served — its seven members are elected countywide."
    },
    {
      "id": "bureau-county-board-districts",
      "concept": "County board districts",
      "area": "Bureau County",
      "counties": [
        "bureau"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Bureau publishes its 18 board members and their parties, but its 18 district boundaries appear nowhere the public can use.",
      "blocker": "ASKED 1 Aug 2026 and ANSWERED 10 Aug: Clerk Matthew Eggers sent three PDFs — the county-wide map and the Princeton and Spring Valley insets — with \"this is what I have\", and said he had asked the Assessor's GIS deputy whether she has something different. Measured rather than eyeballed, they split two ways. THE COUNTY-WIDE MAP IS STILL NOT USABLE, for a reason worse than resolution: it is one 3300x2550 JPEG with zero text and zero vector content, it is stamped \"10/27/2021 — PROPOSED REAPPORTIONMENT MAP\" rather than the plan the board adopted 23-0 on 9 Nov 2021, and NO DISTRICT BOUNDARY IS DRAWN ON IT AT ALL — the heavy black lines are township lines, and a district is a per-PARCEL colour fill with white unfilled parcels scattered through every one of them, so dissolving the colours would leave holes with no rule to close them. That parcel-level colouring is also why the Assessor's office is the right place to have asked. THE TWO CITY INSETS ARE REAL VECTOR PDFs, 1,981 and 1,004 drawing paths and 1,892 and 1,746 characters — the first machine-readable geometry Bureau has produced, and they cover exactly the street-by-street city splits that were the previous blocker. They do not cover the rural districts, so on their own they build nothing. AND THE SHAPEFILES EXIST, 11 Aug: pressed on the two cheaper routes, Eggers replied that the county-wide map is not digital in his office and named the Assessor's GIS deputy, Christine Anderson — who answered the same morning that she HAS shapefiles of the board districts. Two conditions came with that: the requester must be able to open a shapefile, and she reads this as a COMMERCIAL request, which it is not. Asked her directly 11 Aug, correcting the category rather than letting it stand: chidistricts.com is free, carries no advertising, sells nothing and redistributes no data file, the county is credited on its own card, and a formal FOIA on whatever form the office prefers is offered instead if that is cleaner. The precinct boundaries were asked for in the same message. ANSWERED 12 Aug, and the answer is a CONDITION, not the file: Anderson sent a user agreement to sign and a $150 invoice 'per our data fee schedule' — the campaign's first fee demand, a class no other county has raised. Neither document has been read (they sit as e-mail attachments outside the pipeline's reach), and NOTHING has been signed, paid, or replied: signing a license and spending money are the operator's decisions, not an agent's. The deciding fact is the agreement's terms — chidistricts ships derived boundary JSON publicly, so redistribution/derivative restrictions would put Bureau in the licensed-not-open class (the Champaign/Piatt precedent: WITHDRAWN rather than take on obligations), making the $150 moot; permissive terms would make this a cheap, clean buy. The free routes named on 10 Aug — a precinct list or block-assignment table, plain public records — remain unanswered and unaffected by the fee schedule. READ 13 Aug (the operator relayed both PDFs to Drive): the invoice is a flat $150 ('GIS Project Fee & prep charge', payable on receipt) — honest cost recovery, not the obstacle. The agreement is, and by its own words: the PROTECTION OF PROPRIETARY RIGHTS clause forbids 'reproduction or redistribution of digital datasets OR PRODUCTS DERIVED THEREFROM outside of licensee's organization', and a shipped bureau-county-board-districts.json is a derived product served publicly to every visitor's browser — so signing as written is off the table at any price. The Champaign/Piatt class, CONFIRMED BY READING rather than assumed. Two things keep the door open. First, the clause's own tail — 'without permission from Bureau County GIS' — is a valve: the obligations the agreement otherwise imposes (source credit, modifications described) are ones this fleet already practices on every card, so permission scoped to the site's actual use would make the buy clean. A reply is DRAFTED for the operator asking exactly that, with the no-license fallback (the composition list — the DeWitt/Shelby route) in the same message. Second, nothing about the county's posture reads as refusal: a form agreement built for parcel-data buyers, applied to the first civic reuser who asked. Nothing signed, nothing paid; the decision and the send are the operator's. Re-checked 31 Jul 2026: the county runs no mapping system. ITS BOARD PAGE IS NOT WRONG — the 16-of-18 listing was reported to the Clerk as a website omission and he corrected it: districts 9 and 15 are VACANT and the county is filling them, so a roster built from that page should carry 16 members and say why, not wait for two names that do not exist.",
      "wanted": "Two things, in Jefferson's order of preference. FIRST, the assignment list rather than new geometry: a block equivalency / block assignment file, or the parcels-to-district table behind the colouring, or a plain list of which precincts make up each district — any of which draws the districts exactly against public geometry with no drafting by the county. SECOND, confirmation of which map is the ADOPTED plan, since the file in hand is stamped PROPOSED and dated 10/27/2021 while the board adopted on 9 Nov. The Princeton and Spring Valley vector insets are already in hand and check out; the county-wide extent is the whole of what is missing. AS OF 11 AUG THE ASK IS NARROWER THAN EITHER: the Assessor's GIS deputy has the board districts AS A SHAPEFILE, so what is wanted is that file (.shp/.dbf/.shx/.prj) and, if it exists, the voting precincts alongside it — nothing to draw, nothing to derive, and the request is with her. (13 Aug: the file arrived priced at $150 behind a license whose standard terms forbid redistribution of derivatives — so what is wanted is now the clause's own valve: written permission for the site's specific use, or failing that the composition list, which needs no license at all.)"
    },
    {
      "id": "calhoun-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Calhoun County",
      "counties": [
        "calhoun"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Calhoun County's voting precincts are not shown — the county publishes election documents but no boundaries.",
      "blocker": "Checked 2 Aug 2026 when the county was added: Calhoun runs no mapping system, and nothing for the county appears in any public map catalogue. The clerk does publish election files, though in an unusual form — the 2026 primary summary is a raw printer file rather than a PDF — and none of them carries geometry. The board half needs none: its five commissioners are elected countywide.",
      "wanted": "Calhoun County's precinct boundaries as map data, or a polling place list keyed by precinct."
    },
    {
      "id": "carroll-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Carroll County",
      "counties": [
        "carroll"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Carroll's fire, park and library districts exist as names and tax rates only — no boundary is published in any form.",
      "blocker": "Checked 31 Jul 2026: the county runs no mapping system, and the GIS page on its site links a parcel-search portal with no usable data behind it. The clerk's 2025 tax report names nine fire districts, three park districts and seven library tax lines, but gives rates only and no maps; the yearbook adds library opening hours.",
      "wanted": "Boundaries for the districts as map data. Several cross county lines — the Polo, Hanover and Shannon fire districts, and Pearl City's park and library — so their full extents matter."
    },
    {
      "id": "carroll-ward-geometry",
      "concept": "City council district",
      "area": "Savanna, Mount Carroll and Lanark",
      "counties": [
        "carroll"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "All three Carroll cities elect aldermen by ward. None publishes ward boundaries, and the one dataset we found is private and predates redistricting.",
      "blocker": "Savanna (4 wards, 2 seats each), Mount Carroll (3 wards, 2 seats each) and Lanark (3 wards) were confirmed ward-electing from city sources on 31 Jul 2026. Savanna's own map account holds exactly one ward item, titled “Ward Districts (Pre-Redistricting)” and set to private. Lanark and Mount Carroll publish no ward map, and the county has no mapping system to carry them.",
      "wanted": "Current post-2020-census ward boundaries for any of the three. Savanna's public works department runs a 102-item map account, so making a current version public is the most plausible single unlock."
    },
    {
      "id": "champaign-piatt-ccgisc-license",
      "concept": "County board districts and voting precincts",
      "area": "Champaign and Piatt Counties",
      "counties": [
        "champaign",
        "piatt"
      ],
      "kind": "blocked",
      "layer": "county-board",
      "summary": "Champaign's and Piatt's district and precinct maps are complete, current and online — but we are not allowed to republish them.",
      "blocker": "Checked 2 Aug 2026. This block is legal, not technical. Both counties' maps are run by the Champaign County GIS Consortium, which sells this data: buying it requires a signed licence, and the consortium's terms let you view the maps but not copy them, display them publicly, or put them on another server. Showing them here would do all three. The maps are easy to fetch, and that is exactly what makes this worth spelling out — easy is not the same as allowed. CONFIRMED BY THE COUNTY CLERK, 3 Aug 2026. A records request to Champaign County's election authority for the board-district and precinct boundaries was answered by the Clerk's elections division: \"The shape files for the requested data are maintained by the Champaign County GIS Consortium. You will need to reach out to them.\" So the county's own election authority says it does not hold the files — this blocker is now a named source rather than an inference from the consortium's terms, and the remaining ask is to the consortium, not to the clerk. The Piatt half was ALSO asked directly (3 Aug 2026, board+precinct GIS to Clerk Harper — pending), and the consortium permission letter is drafted in pass 14.",
      "wanted": "Written permission from the Champaign County GIS Consortium, or the same boundaries released by a county under its own records law. The clerk route has now been tried in Champaign and closed — the election authority says it does not hold the shapefiles — so the live ask is to the consortium itself, and Piatt's clerk has not been asked yet. Both counties are ready to add the day the data may be republished; Champaign also has fire, library, park, cemetery and transit district maps behind the same licence."
    },
    {
      "id": "chicago-amenity-phones",
      "concept": "Fire stations",
      "area": "Chicago metro",
      "counties": [],
      "kind": "data-quality",
      "layer": "fire-station",
      "summary": "Fire station cards do not show a phone number.",
      "blocker": "Checked in the July 2026 card review: the national dataset these station locations come from has no phone field at all. It is missing at the source, not something we have failed to display.",
      "wanted": "A Chicago Fire Department or region-wide station list that includes public phone numbers."
    },
    {
      "id": "christian-county-board-districts",
      "concept": "County board districts",
      "area": "Christian County",
      "counties": [
        "christian"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Christian County's current board map is a picture, and the readable file sitting beside it on the same page is the previous decade's plan.",
      "blocker": "Checked 2 Aug 2026: “County-Board-Districts-2022.pdf” has no readable text or lines at all, and the state's copy of the adopted plan is a scan. The trap is the file next to it: “County-Board-Districts-with-Rep.pdf” IS readable, but the populations printed on it are from the 2010 census, so it is the pre-2021 map and using it would draw superseded lines. The county has an online map account but publishes only assessment data on it. The member list is missing too — the county site names the Chairman and Vice-Chairman only, not the 16 members or their districts. ENCLOSED 2026-08-11: Shelby's join made Christian the coverage wash's second enclave after Bureau — Sangamon, Macon, Shelby and Montgomery are all served, so this county now reads as a doughnut on the map rather than as frontier, which makes its absence the visible kind.",
      "wanted": "The four districts adopted in 2021 as map data, plus a member list with district assignments. The county's own map account could carry both."
    },
    {
      "id": "clark-county-board",
      "concept": "County board",
      "area": "Clark County",
      "counties": [
        "clark"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Clark County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. clarkcountyil.org — 'The Official Website of Clark County, IL' — answers 200 with a County Board department page and a full directory. A .ORG, a TLD the probe never tried. The Clerk's own domain is a third address, clarkcounty.illinois.gov. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "clay-county-board",
      "concept": "County board",
      "area": "Clay County",
      "counties": [
        "clay"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Clay County's board is not shown — the pass-13 probe found nothing for the Illinois county; the name's only catalogue hit is Clay County MISSOURI's election service.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The one ArcGIS Online result for the name — an ElectionDistricts service owned by voteclaycountymo.gov, carrying a 'MO Central Committee' layer — is Clay County MISSOURI, rejected by owner and layer names exactly as pass 11 rejected Mercer County New Jersey: check what a hit IS before recording it. No Illinois county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "clinton-county-board-geometry",
      "concept": "County board districts",
      "area": "Clinton County",
      "counties": [
        "clinton"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Clinton's precincts are current and published; its 5 board districts are drawn only on a PDF.",
      "blocker": "Checked 2 Aug 2026: the county's online mapping publishes 28 datasets, including a 34-precinct map created in April 2026 that matches the clerk's own polling table exactly, and a township map — but no board districts, confirmed by going through all 28. The districts exist as “NEW-2022-Clinton-County-Board-Districts.pdf”, a readable map drawn over the county's 15 townships. The member list is published in full: all 15 with phone, email and term.",
      "wanted": "A board district dataset on the county's mapping system — the townships and precincts it would be built from are already there — or the map file behind the 2022 PDF."
    },
    {
      "id": "coles-county-board",
      "concept": "County board",
      "area": "Coles County",
      "counties": [
        "coles"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Coles County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer under the probed patterns.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. Coles has TWO sites, colesco.illinois.gov and www.co.coles.il.us, the second carrying a board member CONTACT page (/Board/memberContact.html) and minutes back to 2012. Both are indexed by search engines and BOTH REFUSE THIS NETWORK — a TLS reset and a 503 — so this is the blocked-not-absent distinction, and the earlier record conflated them. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "county-board-office-addresses",
      "concept": "County board office location",
      "area": "Every county board except Cook",
      "counties": [
        "will",
        "dupage",
        "kane",
        "mchenry",
        "kendall",
        "kankakee",
        "winnebago",
        "livingston",
        "mclean",
        "logan",
        "sangamon",
        "madison",
        "st-clair",
        "dekalb",
        "ogle",
        "stephenson",
        "carroll",
        "lee",
        "whiteside",
        "rock-island",
        "lasalle"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Only Cook's and Lake's board cards name an office you can visit. No other county publishes one.",
      "blocker": "Corrected in the 31 Jul 2026 review: Cook does publish a district office for each commissioner (17 of 17, now pinned on the map), so this entry's earlier claim that no board card named an office was wrong. Lake's card shows the shared county building office at 18 N County St, Waukegan, plus the district newsletter link. No other county in the app publishes a board office address. Madison publishes members' home addresses, which were removed rather than presented as somewhere a resident could go.",
      "wanted": "An office address for each district, or confirmation that a county's board members hold office hours somewhere specific. Most county boards meet in one building, so a single board office address per county — the way Lake's works — is probably the honest fix."
    },
    {
      "id": "crawford-county-board",
      "concept": "County board",
      "area": "Crawford County",
      "counties": [
        "crawford"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Crawford County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. crawfordcounty.illinois.gov answers 200 with a County Board page and a 'Board Members 2024' document; crawfordcountyil.org is a second county site. crawfordcountyil.com is a DECOY — the Crawford County Development Association, not the county. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website. ANSWERED 17 Aug 2026 — Clerk Beckie Staley, back from vacation and apologizing for the delay: \"They are elected. Two from each district. We have 5 Districts.\" The election authority stating the form in writing: DISTRICTED, five districts of two members — a ten-seat board — so this is a geometry ask after all (§2.5 step 2 satisfied). For maps she points to the county website \"through the Assessors page\" and refers questions to assessor@crawfordcounty.illinois.gov. MEASURED THE SAME DAY: crawfordcounty.illinois.gov answers this project's network normally (HTTP 200), and the Assessor page's one map link is a Beacon viewer (beacon.schneidercorp.com, App=CrawfordCountyIL) — the MENARD SHAPE: the county, as the vendor's customer, can export the layers behind the viewer; the public cannot, and a viewer is not a licence to take from (§2.5.1). The route is an export request to the Assessor, exactly how Menard's Beacon data landed.",
      "wanted": "The board-district polygons — and precincts, if the county holds them — as an export from the county's Beacon instance, the Menard route: its Assessor can export the layer and e-mail it. The Clerk herself pointed to the Assessor, and the export request was ASKED 17 Aug 2026 — sent by the operator to assessor@crawfordcounty.illinois.gov the same day she pointed there. ANSWERED THE SAME DAY: the Assessor — who created the layers herself — replied that she ‘would need to discuss this request with the Mapping Committee’, so the export decision now sits with that committee; nothing further to ask until it answers."
    },
    {
      "id": "cumberland-county-board",
      "concept": "County board",
      "area": "Cumberland County",
      "counties": [
        "cumberland"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Cumberland County's board is not shown — the pass-13 probe found no county GIS, no catalogued map data, and no county website.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed — cumberlandcounty.org is Cumberland County MAINE's, a decoy of the browncountyil.org kind. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". Re-searched 2026-08-09 and CONFIRMED: no Cumberland County Illinois site was found under any pattern, and cumberlandcounty.org is Cumberland County MAINE exactly as this record already warned. One of only two in the sweep that held up.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "dekalb-hinckley-board",
      "concept": "Municipal officials",
      "area": "Hinckley",
      "counties": [
        "dekalb"
      ],
      "kind": "data-quality",
      "layer": "municipality",
      "summary": "Hinckley's card shows five trustees where an Illinois village board seats six.",
      "blocker": "The county yearbook prints Sarah Quirk twice for Hinckley — once as Village President and again as a Trustee. In Illinois a village president is elected to that office separately and cannot also hold a trustee seat, so one of the two entries is out of date. We keep the president row, which is the more specific claim. Who actually holds the sixth seat is not published by the county or the village.",
      "wanted": "A corrected Hinckley entry in the DeKalb County yearbook, or a village board list on hinckleyil.com. Every other DeKalb municipality is complete."
    },
    {
      "id": "dekalb-precinct-codes",
      "concept": "Voting precincts",
      "area": "DeKalb County",
      "counties": [
        "dekalb"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "DeKalb precinct cards read “Precinct SG 01” — the county's own two-letter township code, not a name anyone would recognise.",
      "blocker": "That code is exactly what the county publishes: its board-district listings and its committeeperson lists both print “AF 01”, “DK 15”, “SG 01”, and nothing anywhere spells the prefixes out. Nineteen townships share two-letter codes and several start with the same letters (Sandwich, Shabbona, Somonauk, South Grove, Sycamore), so the full names cannot be worked out without guessing. The township shown just above the precinct on the same card does at least answer which township you are in. Re-checked 31 Jul 2026: the yearbook, the polling list and the voting-location data all still print bare codes.",
      "wanted": "Any DeKalb County list that pairs a precinct code with its township or full precinct name — a clerk's precinct table, a polling place list carrying both, or a key printed on the precinct map."
    },
    {
      "id": "douglas-county-board-districts",
      "concept": "County board districts",
      "area": "Douglas County",
      "counties": [
        "douglas"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Douglas County's board districts are not shown — the county has a real website but publishes no election geometry.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (douglascountyil.gov) is real and current: elections live under the County Clerk, and assessments run on DEVNET tooling plus the illinoisassessors.com parcel viewer — a commercial parcel product, not an election map system. Nothing on the site links district or precinct boundaries.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Douglas County's board district boundaries as map data, or the composition (whole townships or precincts) they are built from."
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
      "summary": "DuPage municipal entries do not show phone numbers.",
      "blocker": "The regional mayors' directory prints numbers without an area code and never says which one to assume, so showing them would mean guessing what to dial. Re-checked 31 Jul 2026 against the current 2025-26 edition (revised 12 May 2026): still seven digits, still no stated area code, and DuPage County itself still publishes no municipal directory.",
      "wanted": "A DuPage directory that prints full ten-digit numbers, or an official statement of each municipality's area code."
    },
    {
      "id": "dupage-ward-cities",
      "concept": "City council district",
      "area": "Wood Dale, Oakbrook Terrace and Warrenville",
      "counties": [
        "dupage"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Three DuPage ward cities exist only in a county dataset whose officeholder details froze in 2021 and whose boundaries may predate the post-census redraw.",
      "blocker": "The 31 Jul 2026 sweep found current city-published ward data with officeholder details for Elmhurst, Wheaton, West Chicago, Lombard and Glendale Heights — West Chicago was added on 2 Aug 2026, and the other four need re-finding — plus Darien with recent-ish boundaries but stale details. Wood Dale, Oakbrook Terrace and Warrenville appear only in the county's municipal ward dataset, whose details read “Updated 04/29/2021” and whose boundaries have not been checked against the post-2020 redraws. Showing it could draw pre-redistricting lines.",
      "wanted": "City-published ward data for the three, or each city's adopted redistricting ordinance so the county dataset's boundaries can be checked against it."
    },
    {
      "id": "edgar-county-board",
      "concept": "County board",
      "area": "Edgar County",
      "counties": [
        "edgar"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Edgar County's board is not shown — its .gov domain redirects to a site that surfaced no election, board, or map links in this probe.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. edgarcountyil.gov does not resolve; edgarcountyillinois.gov answers and redirects to edgarcountyillinois.com, whose homepage surfaced no GIS, election, or board links to follow. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "edwards-county-precincts",
      "concept": "Voting precincts",
      "area": "Edwards County",
      "counties": [
        "edwards"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Edwards County's voting precinct boundaries exist on paper only — its Clerk said so directly.",
      "blocker": "Stated 6 Aug 2026 by County Clerk & Recorder Melanie Knight, unprompted, in the same reply that settled the board's form: 'Our voting district boundaries currently exist on paper.' No hedging and no qualification, from the office that draws them. That is a closed route rather than an unmeasured one, and it is recorded so nobody re-probes for a file the county has said does not exist. There is also nowhere else to look: Edwards has no county website (confirmed by the same Clerk on the same day), no self-hosted ArcGIS under ten hostname patterns, and nothing county-keyed in the ArcGIS Online catalogue.",
      "wanted": "Either the county digitising its precincts, or a paper map good enough to georeference — the Stephenson route, where two adopted PDFs from the Clerk's own page became 36 precincts. Edwards publishes no such document today because it publishes nothing; a scan sent by the Clerk would be the equivalent."
    },
    {
      "id": "effingham-municipal-officials",
      "concept": "Municipal officials",
      "area": "Effingham County",
      "counties": [
        "effingham"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Effingham County's 12 municipalities' councils are not shown — the county's own GIS names its BOARD members, but no source for city councils was found in this pass.",
      "blocker": "Found 4 Aug 2026 in the pass-13 sweep, and the county SHIPPED the same day as the forty-fourth dispatched county and the outline's first island — board, precincts, fire, park and library all from its GIS org (effinghamcoil.maps.arcgis.com, EFFINGHAM COUNTY GIS, invisible to keyword search because no item title names the county). What that org does NOT carry is the municipalities: 12 boundary shapes with no officials, so the Municipality card names each city without its council.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "A roster source for the 12 municipalities' presidents/mayors and councils — the county build ships without them otherwise, linking each municipality's official site instead."
    },
    {
      "id": "fayette-county-board-geometry",
      "concept": "County board districts",
      "area": "Fayette County",
      "counties": [
        "fayette"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Fayette's own district map was made with professional mapping software, which proves the underlying files exist. The county publishes the printout instead.",
      "blocker": "Checked 2 Aug 2026: “County-Board-District-Map-Effective-2022.pdf” is an export from mapping software, its text reads cleanly, and it draws both the 7 board districts and 28 named precincts — so a mapping system somewhere holds both. Neither appears among the 34 datasets the county publishes online (all of them checked), and the state's copy is a 2014 scan. One caveat about the PDF: its title block reads “2020 ... District & Precinct Map” though it is filed as effective 2022. The member list is unusually complete: all 14 with party (12 Republican, 2 Democratic) and term end.",
      "wanted": "The board district and precinct map files behind the county's own printout, from the county or its mapping vendor."
    },
    {
      "id": "ford-county-board-vintage",
      "concept": "County board districts",
      "area": "Ford County",
      "counties": [
        "ford"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Ford lists which townships make up each district, but one precinct is shared between two districts — and the only map's date cannot be established.",
      "blocker": "Checked 2 Aug 2026: the board page prints each district's townships, and the board is unevenly sized (District 1 has 3 members, District 2 has 4, District 3 has 4). But Patton 3 appears in both District 1 and District 3, so that precinct is split and township boundaries alone cannot rebuild the lines. The one map, on the state's site, is titled “2011 County Board Districts” while the file itself was last changed on 9 Nov 2021 — either a re-upload of the old plan or a mistitled new one, and nothing published settles which. The county runs no mapping system of its own. The member list (names, district, phone and county emails) is freely available. ASKED 3 Aug 2026 — this record's exact question (which plan is in force, and the Patton 3 split), to Clerk Vaughn; no response as of 4 Aug.",
      "wanted": "Confirmation of which plan is currently in force, plus precinct boundaries — or simply a description of how Patton 3 is split. The township list is otherwise ready to use."
    },
    {
      "id": "franklin-county-board-districts",
      "concept": "County board districts",
      "area": "Franklin County",
      "counties": [
        "franklin"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Franklin County's board districts are not shown — the board IS districted (its own members page groups Districts 1–3) but no boundary is published as data.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (franklincountyil.gov) is real: a County Board Members page grouping members under Districts 1, 2 and 3 — so the board is districted and the site itself is a roster source — plus Elections pages and a GIS page. The GIS page, though, links no public map service the probe could reach, and assessments run on DEVNET's parcel product.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Franklin County's three board-district boundaries as map data, or the precinct/township composition they are built from — the members page already covers the roster half."
    },
    {
      "id": "galesburg-wards-outside-the-ring",
      "concept": "City council district",
      "area": "City of Galesburg",
      "counties": [
        "knox"
      ],
      "kind": "data-quality",
      "layer": "ward",
      "summary": "Galesburg publishes its seven council wards as map data — the only buildable ward source found outside the coverage ring — and building it alone would be the first ward group in an unserved county.",
      "blocker": "Found 3 Aug 2026 in the pass-11 probe. The City of Galesburg runs a 75-service ArcGIS Online account which publishes Galesburg_City_Council_Wards, a Precincts layer (20 city precincts carrying ward, county board district and polling place), and Knox County Board Districts *in the City of Galesburg*. All three are real and current. None is countywide, so none of them serves Knox County itself. That is what makes this a decision rather than a build: every one of the 21 ward groups shipped today sits in a county inside the coverage ring, 21 of 21 with no exception, and Galesburg would be the first outside it. A Galesburg resident would then resolve the ward layer — which is dispatched, not statewide — while the out-of-scope wash greys their location out, which is the shape of the 2026-07-30 Kankakee bug rather than the Centralia municipality case (see scripts/build_metro_outline.py: `municipality` is statewide, `ward` is not). Adding Knox to the ring to compensate would be worse: nothing county-keyed answers anywhere else in Knox. DECIDED 4 Aug 2026, in the same decision that retired contiguity as a shipping gate (EXPANSION_GUIDE §2.5.1): the county stays the unit of coverage — a city cannot carry its unserved county in, so these wards wait for Knox rather than shipping into the wash. Note the retirement itself changes nothing here: Knox borders Fulton, so it was never contiguity-blocked; this gap always turned on the county-keyed test, and still does.",
      "wanted": "Any county-keyed Knox layer makes Knox served and ships these wards in the same change. The live asks (Tier 3): the adopted board plan's districts 4 and 5 — the rural remainder the city's own account proves exists in digital form — or countywide precincts, from Knox County GIS or the County Clerk."
    },
    {
      "id": "gallatin-county-board",
      "concept": "County board",
      "area": "Gallatin County",
      "counties": [
        "gallatin"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Gallatin County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. gallatinco.illinois.gov answers 200 and is the county's own site. Note the abbreviation: gallatinCO, not gallatincounty — the same shape as colesco.illinois.gov. gallatincounty.org is a decoy (a weather site). The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "grundy-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Grundy County",
      "counties": [
        "grundy"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Grundy's fire, park and library districts are not shown — the county's mapping publishes no boundaries for them.",
      "blocker": "Re-checked 31 Jul 2026 across all 23 sections of the county's mapping system: the fire departments section is literally empty, and no district boundaries exist anywhere on it. The names are published — the clerk's July 2026 Directory of Officials names 12 fire protection districts, the library districts and 2 park districts with their trustees — but the boundaries exist in no usable form.",
      "wanted": "Fire, park and library district boundaries as map data. The clerk's 2026 directory already supplies the trustees."
    },
    {
      "id": "hamilton-municipal-officials",
      "concept": "Municipal officials",
      "area": "Hamilton County",
      "counties": [
        "hamilton"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Hamilton County's municipalities show boundaries but no councils — no roster source was found for them.",
      "blocker": "Found 5 Aug 2026: the county org's Corporations_Hamilton layer draws the municipal boundaries, and neither the county's new website (mid-migration, live 2026-08-05) nor the org carries their officials. McLeansboro and Dahlgren's own web presence was not surveyed in this pass.",
      "wanted": "A roster source for the municipalities' presidents/mayors and councils — the county's Blue-Book equivalent, if one exists, is the Washington County precedent."
    },
    {
      "id": "hardin-county-board",
      "concept": "County board",
      "area": "Hardin County",
      "counties": [
        "hardin"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Hardin County's board is not shown — the county's minimal website surfaced no election, board, or map links.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. hardincountyil.gov answers but is minimal: its homepage surfaced no GIS, election, or board links to follow. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "henderson-county-website",
      "concept": "County board districts",
      "area": "Henderson County",
      "counties": [
        "henderson"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Henderson County's published web address leads to a holding page, not a county site.",
      "blocker": "Checked 3 Aug 2026. hendersoncountyil.gov, the domain in the state's clerk directory, returns a 114-byte page whose only content forwards the visitor to a generic parking screen. At roughly 6,000 people Henderson is the smallest county on the frontier, and it became one only because neighbouring McDonough was added the same day. Nothing for it appears in the state map catalogue.",
      "wanted": "Whether the county has a website at all, and whether its board districts and precincts exist as map data. Its clerk has a working e-mail."
    },
    
    {
      "id": "jasper-county-board",
      "concept": "County board",
      "area": "Jasper County",
      "counties": [
        "jasper"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Jasper County's board is not shown — the county shares a website with the City of Newton, and its Maps page carries reference PDFs but no election geometry.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county's web presence is a SHARED site with the City of Newton (jaspercountyillinois.gov) — one site, two governments. It carries a County Board page and a Maps page, but the maps are reference PDFs (county map, city limits, TIF areas), not election geometry, and no district or precinct boundary appears. jaspercounty.org is Jasper County MISSOURI's, a decoy. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". ANSWERED 17 Aug 2026 — Clerk Tarr, in writing: ‘board members are elected from districts. Please see the attached map.’ FORM SETTLED — DISTRICTED (§2.5 step 2 satisfied by the election authority's own statement plus the county's adopted map, ‘County Board Redistricting Effective 2022’, archived from her e-mail). The map shows THREE districts (CB 1–3) assembled from townships, with Wade Township — which contains Newton — split: its inset pairs Wade 1/Ward 1 → CB 3, Wade 2/Ward 2 → CB 2, Wade 3/Ward 3 → CB 3 and Wade 4 → CB 1. The map's linework is RASTER inside the PDF (13 vector paths on the county page, all decoration), so nothing polygonizes; the geometry route is census fabric — TIGER townships for the whole-township districts and the 2020 VTD fabric for the Wade splits — IF the VTDs carry Jasper's Wade precincts, which is the next thing to measure (the White shape if they do).",
      "wanted": "A per-township composition read carefully off the archived 2022 map (its raster layout scrambles text extraction), then verification that TIGER's 2020 VTDs carry Wade's four precincts so the districts can be composed from census fabric; failing the VTD match, Wade's precinct boundaries from the county. The board's form is settled — districted, three districts."
    },
    {
      "id": "jersey-county-board-districts",
      "kind": "no-source",
      "concept": "County board districts",
      "area": "Jersey County",
      "layer": "county-board",
      "counties": [
        "jersey"
      ],
      "summary": "Jersey publishes all twelve board members with their districts, and its Clerk publishes a district MAP — but as a PDF dated 2016, with no data behind it and no post-redistricting edition found.",
      "blocker": "Researched 8 Aug 2026, closing an absence that had NO record at all: Jersey is served as a 7th-Circuit secondary and its board did not surface. FORM SETTLED — DISTRICTED: jerseycounty-il.gov/county-board/ gives each member a \"Jersey County Board District N\" line, three members per district across Districts 1-4 (Crone, Grizzle, Hayes 1; Heitzig, Mills, Ward 2; Wagner as Chairman, Ontis as Vice Chair, Beasley 3; Figge, Beers, Keonig 4), with committee assignments and biographies. That is a geometry ask, not the County-card path. No GIS SERVICE exists: gis.jerseycounty-il.gov and maps.jerseycounty-il.gov have no DNS record (resolved directly rather than inferred from a failed fetch), and the ArcGIS Online catalogue returns nothing county-keyed. CORRECTED 2026-08-08, and the correction is the point: this record originally said Jersey publishes no district boundaries at all, which was FALSE and was written without ever running a web search. THE COUNTY CLERK HAS A SEPARATE DOMAIN — jerseycountyclerk-il.gov, never probed because the clerk roster carries jerseycounty-il.gov — with a MAPS section publishing County Board Districts, Precincts/Polling Places and School Districts. The board-districts file (/media/pdf/County_Board_Districts___County__Roads2016.pdf, 792 KB) is a genuine VECTOR map, 5,117 paths, whose legend names District 1 through District 4, matching the twelve members three-per-district. TWO THINGS STILL STAND BETWEEN THAT AND A BUILD, and neither is 'nothing exists'. Its filename and content date it to 2016 — BEFORE the post-2020 redistricting every Illinois county did in 2021 — so it may describe superseded lines, and no newer edition was found. And a first pass found no large filled paths to lift the district polygons from, so the fills may be among the page's 14 raster images rather than vectors; the Stephenson georeferencing precedent applies if they are recoverable at all.",
      "wanted": "Whether the 2016 map on jerseycountyclerk-il.gov is still the operative one after the 2021 redistricting, and if so the GIS or CAD file behind it — the map exists, so this is a request for its data and its currency rather than for a boundary nobody has drawn. Failing that, the precincts making up each district, which the Clerk also maps."
    },
    {
      "id": "johnson-county-board",
      "concept": "County board",
      "area": "Johnson County",
      "counties": [
        "johnson"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Johnson County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer under the probed patterns.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask. PARTLY ANSWERED BEFORE IT WAS ASKED: the Clerk herself wrote on 21 Jul 2026 — \"We don't have a website to point back to\" — so the probe's no-website finding is now the county's own statement. The board-form and boundary questions remain open; the pass-14 draft asks them and thanks her for the earlier reply. CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. johnsonco.illinois.gov RESOLVES, though it refuses this network (TLS reset). That sits in tension with the Clerk's written statement that the county has no website, which stands as the authority until re-asked — but the domain is live and should be re-checked from an ordinary browser before this record is trusted again. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "joliet-municipal-contact",
      "concept": "Municipal officials",
      "area": "Joliet",
      "counties": [
        "will"
      ],
      "kind": "blocked",
      "layer": "municipality",
      "summary": "Joliet's council contact details can only be refreshed through a real web browser or the Internet Archive — the city's site refuses ordinary automated requests.",
      "blocker": "Re-checked 31 Jul 2026: joliet.gov refuses every automated request coming from a server, even one that identifies itself exactly like a browser. A full browser does work, and the Internet Archive's most recent capture (20 May 2026) carries the complete council, so the details do stay current. Listed separately from the other blocked sites so it appears under Will County, where it actually affects a card.",
      "wanted": "Any council list joliet.gov is willing to publish in a machine-readable form (JSON, CSV or RSS). Until then, the browser-and-Archive route keeps this current."
    },
    {
      "id": "kankakee-city-wards",
      "concept": "City council district",
      "area": "City of Kankakee",
      "counties": [
        "kankakee"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Kankakee city's ward data exists but mixes old and new maps — a single address can fall in two different wards — so it cannot be used as published.",
      "blocker": "Checked 31 Jul 2026: the city's data returns 10 shapes for 7 wards, with duplicates of the 4th, 6th and 7th. Test points land inside both copies of the 6th and 7th, and the centre of the 1st ward also falls inside the 2nd ward's shape. Nothing in the data marks which copies are the current, 2022-approved ones, so removing duplicates would be guesswork until each is checked against the city's adopted 2022 ward map. The city's directory publishes all 14 alderpersons with phone and email, ready to attach.",
      "wanted": "A defensible set of current shapes for the 7 wards — confirmation from the city, a cleaned-up single-version dataset, or a check of each shape against the 2022 map."
    },
    {
      "id": "kankakee-municipal-officials",
      "concept": "Municipal officials",
      "area": "Kankakee County",
      "counties": [
        "kankakee"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "No officeholder names for Kankakee County's 21 municipalities — the card shows the municipality and a link only.",
      "blocker": "No county-published list exists. The clerk's site has no directory, and the county's municipal boundary data has fields for phone, website and email that are empty on all 21. Re-checked 31 Jul 2026: the clerk's site, the yearbook and the regional council all still publish nothing.",
      "wanted": "Any county or regional directory naming mayors, village presidents and boards — ideally at a stable web address that is republished after each election."
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
      "blocker": "The county's data has fields for phone, website and email on every district and leaves all of them empty: none of the 17 fire districts, 4 park districts or 8 library districts carries any contact detail.",
      "wanted": "A Kankakee directory of fire protection, park and library districts with contact details."
    },
    {
      "id": "knox-county-board-districts",
      "concept": "County board districts",
      "area": "Knox County",
      "counties": [
        "knox"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Knox County's entire website blocks automated visits, and only the Galesburg half of its 5 board districts exists as usable map data.",
      "blocker": "Checked 2 Aug 2026: knoxcountyil.gov — and the old address, which redirects into the same block — refuses every request, including the page that lists all 15 members with district, term and contact details. The only usable district boundaries published anywhere are on the City of Galesburg's map account: districts 1 to 3, the three that fall within the city, adopted by the County Board on 27 Oct 2021. Districts 4 and 5, the rural remainder, appear in no usable source we could find, and the state's countywide map is provably 2011 content, from before the 2021 redistricting.",
      "wanted": "The countywide map adopted in 2021 as map data — most likely inside the 27 Oct 2021 board packet — plus any member list the county is willing to publish in machine-readable form, or simply a mirror its blocking does not cover."
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
      "summary": "Lake County's 41 municipalities show village hall contact details but no officeholder names.",
      "blocker": "No Lake County body publishes municipal officeholder names, re-checked 31 Jul 2026. The county's municipal data carries hall address, phone and website only; the Lake County Municipal League's pages repeat the same hall contact with no names, and its board page names only the League's own officers; the Council of Mayors membership list gives municipality names only. lakecountyil.gov itself now challenges automated visits, though not the kind of block that refuses outright.",
      "wanted": "A Lake County clerk or regional directory naming heads of government. The DuPage mayors' directory is the shape that would work."
    },
    {
      "id": "lasalle-board-districts-stale",
      "concept": "County board districts",
      "area": "LaSalle County",
      "counties": [
        "lasalle"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "LaSalle's board card runs on boundaries we built ourselves: the county publishes no map of its adopted 2022-2031 districts, and eleven split precincts are drawn whole on the side where most of their voters live.",
      "blocker": "Rebuilt 1 Aug 2026. (It previously showed the superseded 2011-2021 map, which was pulled the same day that was found.) The boundaries now come from combining the county's own precincts according to the district assignments its November 2024 and March 2026 elections were actually run under: 108 whole precincts on county-drawn lines, and nine districts that reproduce the adopted map's printed populations to the person. What keeps this open is that the county redrew its precincts after adopting the map, and eleven of them now straddle district lines — Serena 1, Eden 2, Mission 2, Peru 4, Ottawa 5, 6 and 7, La Salle 7 and 8, and Bruce 6 and 12. Each is drawn whole on its majority side, which places about 1,659 of 109,658 residents in the wrong district, and the card says so wherever it applies. The adopted map itself exists only as PDFs, the county's one published board map is still the superseded one, and its mapping vendor's server has an expired security certificate. The member list is complete: a weekly update covers all 29 members with full phone numbers and district-office emails, plus the countywide-elected Chairman.",
      "wanted": "The county publishing its adopted 2022-2031 districts as map data, which would retire our version outright. Short of that, cutting the eleven split precincts along the adopted map's own lines would narrow the approximation from whole precinct halves to a band about 20 metres wide."
    },
    {
      "id": "lasalle-municipal-wards",
      "concept": "City council district",
      "area": "La Salle, Peru and Earlville",
      "counties": [
        "lasalle"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Three of LaSalle County's four ward-electing cities are unmapped; only Mendota's wards are shown.",
      "blocker": "La Salle publishes a ward map, but as a picture: a single image on its city profile page, with no boundaries to read. Peru and Earlville publish nothing at all — no map link on either city site, and nothing in any public map catalogue. The county's own mapping carries city limits but no wards. Mendota is the exception that shows what this needs: its own map account, four ward shapes, last edited December 2022 — and it is already here.",
      "wanted": "Ward boundaries for La Salle (4), Peru (4) and Earlville (3) as map data. All three cities' aldermen are already in hand from the county clerk's directory, two per ward, so each card would name its seats immediately."
    },
    {
      "id": "lawrence-county-board",
      "concept": "County board",
      "area": "Lawrence County",
      "counties": [
        "lawrence"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Lawrence County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer under the probed patterns.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. lawrencecounty.illinois.gov answers 200 with a /boards section. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "lee-municipal-officials",
      "concept": "Municipal officials",
      "area": "Lee County",
      "counties": [
        "lee"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Lee's 13 municipalities show a name and a link only — the county publishes no municipal officeholders anywhere.",
      "blocker": "CONFIRMED BY THE COUNTY CLERK, 3 Aug 2026, which upgrades this from a search that found nothing to a statement that there is nothing to find. Asked directly whether the county published such a list in any form, Clerk Nancy Petersen replied: \"Lee County does not have a updated yearbook, or government guide, a directory or a PDF at this time.\" That matches what the four search routes had already shown — the Clerk runs no elected-officials database; neither the Clerk nor the Election Information page links a yearbook or municipal directory, and the site's only directory is of county STAFF; the area's regional council publishes no member directory; and the county's municipal data carries names only, with no contact fields at all, unlike Lake's which at least has hall address and phone. Note her wording: \"updated\" and \"at this time\" both leave the door open, so this is worth re-asking once a year rather than treating as permanent.",
      "wanted": "Any Lee County list pairing a municipality with its mayor or president: a clerk's yearbook, a regional membership directory, or contact details added to the county's municipal data. Scraping 13 separate village websites is deliberately not the answer. Since the clerk has now been asked and answered, the next move is hers to make rather than another search of ours."
    },
    {
      "id": "lee-park-library-districts",
      "concept": "Park and library districts",
      "area": "Lee County",
      "counties": [
        "lee"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "Lee shows fire districts but publishes no park or library district boundary.",
      "blocker": "Re-checked 31 Jul 2026: the county's mapping server carries the 911 fire service areas the app already shows, and no park or library district boundaries of any kind.",
      "wanted": "Park and library district boundaries from the county's mapping system."
    },
    {
      "id": "livingston-precincts",
      "concept": "Voting precincts",
      "area": "Livingston County",
      "counties": [
        "livingston"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Livingston's voting precincts are not shown — the county publishes no precinct boundaries in any form.",
      "blocker": "Checked 31 Jul 2026: the county runs no public mapping system. Its only mapping product is the assessment office's mail-order parcel program, at 10 to 20 cents per parcel paid by posted cheque; no county items appear in any public map catalogue; and the regional planning commission's 363 datasets include nothing for Livingston. The clerk's yearbook lists precincts and polling places as text only.",
      "wanted": "Precinct boundaries from any county-published source. The yearbook's polling place list is ready to attach."
    },
    {
      "id": "livingston-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Livingston County",
      "counties": [
        "livingston"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Livingston's fire, park and library districts are not shown — no boundary source exists.",
      "blocker": "The same finding as Livingston's precincts: the county publishes no mapping data at all. The one fragment we found is Flanagan Park District, which appears inside a neighbouring region's combined park map — one of the county's own districts, in someone else's dataset.  NOT YET ASKED: this records what the county's WEBSITE shows, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Countywide fire, park and library district boundaries from any official source. The yearbook's fire agency directory supplies contacts the day boundaries exist."
    },
    {
      "id": "logan-fire-districts",
      "concept": "Fire protection districts",
      "area": "Logan County",
      "counties": [
        "logan"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Logan's fire card cannot be shown: the county's only fire boundaries are dispatch zones, not the districts themselves.",
      "blocker": "Checked 31 Jul 2026: the “fire zones” data splits 14 agencies into compass quadrants and includes the Lincoln city fire department. These are emergency dispatch areas, filed alongside ambulance and law enforcement zones, and joining the quadrants back together does not match any adopted district. No fire protection district boundary exists among the 63 datasets on the county's mapping system, and the yearbook's fire district directory is text only.",
      "wanted": "Adopted fire protection district boundaries. The yearbook supplies contacts once boundaries exist."
    },
    {
      "id": "macon-board-phone-area-code",
      "concept": "County board districts",
      "area": "Macon County",
      "counties": [
        "macon"
      ],
      "kind": "data-quality",
      "layer": "county-board",
      "summary": "Macon's board members are shown with seven-digit phone numbers, because that is how the county publishes them.",
      "blocker": "Found 7 Aug 2026, when the board card shipped. The county's board-members page lists each member's number without an area code — \"C 521-4688\", \"H 864-2349\" — and labels them home or cell. Macon County is entirely in area code 217, so prefixing it is the obvious fix and it is the same class of mistake this project refuses elsewhere: a member's MOBILE can be issued anywhere, and a wrong prefix does not fail visibly, it reaches a stranger. So the numbers ship as seven digits with the county's own home/cell labels, which is less useful to someone dialling from outside Decatur and claims only what the source says. 14 of the 15 members are affected; the fifteenth publishes no number at all.",
      "wanted": "The members' numbers with area codes, from the county's own page or a clerk's list. Nothing else about this roster is missing — party, district, e-mail and term-expiry are all published and all shipped."
    },
    {
      "id": "macon-district-name-formatting",
      "concept": "Fire, library and park districts",
      "area": "Macon County",
      "counties": [
        "macon"
      ],
      "kind": "data-quality",
      "layer": "fire-district",
      "summary": "Macon's fire, library and park district names are shown with their spaces missing, because that is how the county publishes them.",
      "blocker": "Found 4 Aug 2026, when the three tilings were added. The county's own labels have had their spaces stripped: MtZion, BlueMound, CerroGordo, HickoryPoint, SouthWheatland, FriendsCreek, MarrowBone, IlliopNian, HopeWelty. Putting the spaces back automatically is the obvious fix and it is wrong: splitting on the capital letters turns MarrowBone into \"Marrow Bone\" and IlliopNian into \"Illiop Nian\", and neither is the name of anything. So the names ship exactly as the county writes them, which looks worse and claims less. This is the posture Boone's fire districts already set, where numbers shipped rather than names nobody could source.",
      "wanted": "The districts' names as the county actually spells them — a list from the clerk or the GIS office, or the same layers republished with the spaces intact. Nine of the 33 names across the three layers are affected."
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
      "summary": "Macoupin's 9 two-member board districts do not show — only its precincts do.",
      "blocker": "Re-checked 31 Jul 2026 and half-overturned: the 2022-2032 map WAS adopted. Ordinance O-2021.06, passed 18-0 on 9 Nov 2021, is readable on the county's code site, and the clerk's Map Room publishes readable maps of all nine districts. But the precinct data still carries no district field, so boundaries would have to be built by combining townships as the ordinance describes, with Cahokia and Shipman split along the published 2005-2021 precinct lines its amendments are written in. The member list is a problem too: the county's downloadable directory stopped being updated in November 2015, and the current list sits behind the clerk's browser-only directory.",
      "wanted": "District boundaries, or a table pairing each precinct with its district — or acceptance of the township-plus-split build the adopted ordinance now supports, together with a current member list."
    },
    {
      "id": "macoupin-municipal-officials",
      "concept": "Municipal officials",
      "area": "Macoupin County",
      "counties": [
        "macoupin"
      ],
      "kind": "blocked",
      "layer": "municipality",
      "summary": "Macoupin's current municipal officials load only inside a web browser, and the one downloadable list stopped being updated in 2015.",
      "blocker": "The clerk's directory at macoupinvotes.gov builds its list after the page loads, so the page itself arrives empty and the address it pulls names from is assembled on the fly rather than written in the page. The county's downloadable export (dataset rxtc-9j2k, 892 rows including aldermen by ward) was last updated on 3 Nov 2015; publishing that today would present a decade-old snapshot as the current officeholders.",
      "wanted": "The address that directory pulls its names from — one look at the page in a browser's developer tools would reveal it — or a fresh export from the clerk."
    },
    {
      "id": "macoupin-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Macoupin County",
      "counties": [
        "macoupin"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Macoupin's fire, park and library districts are not shown — its data portal carries no boundaries for them.",
      "blocker": "The county's only publishing channel for maps is its open-data portal, and the full catalogue of 61 datasets (checked 31 Jul 2026) contains precinct and school district boundaries and nothing else. The clerk's Map Room is election maps only.",
      "wanted": "Any Macoupin fire, park or library district boundary: a new portal dataset, a county mapping system, or a statewide taxing-district source covering the county."
    },
    {
      "id": "macoupin-ward-geometry",
      "concept": "City council district",
      "area": "Macoupin County's eight ward cities",
      "counties": [
        "macoupin"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Eight Macoupin cities elect aldermen by ward; none has published ward boundaries.",
      "blocker": "Benld, Bunker Hill, Carlinville, Gillespie, Girard, Mt. Olive, Staunton and Virden all elected by ward as of the clerk's 2015 directory, which is the newest downloadable list. The county's 61-dataset portal and the clerk's Map Room carry no municipal ward boundaries, and the city sites we sampled publish none. Because the current directory only loads inside a browser, even these ward counts rest on the 2015 snapshot.",
      "wanted": "Ward boundaries — or the adopted ordinances describing them — for any of the eight cities, plus a current aldermen-by-ward list."
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
      "summary": "Madison County's 31 municipal wards across six cities are mapped but not shown: the county's shapes name nobody, though the names now exist elsewhere.",
      "blocker": "The county's ward data has fields for official, address, phone, email and website on every row and fills none of them on any of the 31 — re-checked 31 Jul 2026 on data that is otherwise actively maintained, last edited in May 2026. What has changed is that the names are now available: Alton (7 alderpersons with ward, phone and email), Granite City (10 across 5 wards with email) and Edwardsville (7) publish ward-keyed lists on their own sites, and the regional 2026 Public Officials Directory covers all six cities. The six ward cities are Alton, Edwardsville, Granite City, Madison, Troy and Venice; Collinsville elects at-large.",
      "wanted": "Nothing from readers — the ward-keyed lists were added on 1 Aug 2026 (Alton 7, Edwardsville 7, Granite City 10, Troy 8 and Venice 8 seats). What remains is attaching them to the county's ward shapes, which is already queued."
    },
    {
      "id": "marshall-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Marshall County",
      "counties": [
        "marshall"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Marshall County's 14 voting precincts exist only inside a PDF map, and two of them split municipalities rather than following township lines.",
      "blocker": "Checked 2 Aug 2026, when the county was added: Marshall runs no public mapping system, and the regional planning commission that maps Logan and Woodford carries nothing for it. Its precinct map is a PDF, and unlike its board districts the precincts do not follow whole township lines — two split municipalities, so census data cannot rebuild them. The board districts were added anyway because they ARE whole townships, which the census publishes as usable map data.  NOT YET ASKED: this records what the county's WEBSITE shows, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Marshall County's precinct boundaries as map data, plus polling places if published. The board half is already covered."
    },
    {
      "id": "mason-precinct-vintage",
      "concept": "Voting precincts",
      "area": "Mason County",
      "counties": [
        "mason"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "Mason's 21 precinct shapes are the 2020 Census ones. The county's own current polling list names the same 21, so the names and the count are confirmed — whether any LINE moved is not.",
      "blocker": "PARTLY ANSWERED 4 Aug 2026. The County Clerk's published directory lists the county's polling places precinct by precinct, and it names twenty-one: Allens Grove, Bath, Crane Creek, Forest City, Havana 1 to 6, Kilbourne, Lynchburg, Manito 1 and 2, Mason City 1 to 3, Pennsylvania, Quiver, Salt Creek and Sherman. That is exactly the set of 21 shapes the app already holds from the 2020 Census, so nothing has been added, removed or renamed. What it does not establish is whether the county moved a boundary without changing a name, which a polling list cannot show. The shapes ship, as they did before, and the card does not claim a vintage the county has not confirmed.",
      "wanted": "A yes or no from the Clerk on whether any precinct BOUNDARY has moved since the 2020 Census \\u2014 the names and the count are already confirmed. If one did, the precinct geometry as map data."
    },
    {
      "id": "massac-county-board",
      "concept": "County board",
      "area": "Massac County",
      "counties": [
        "massac"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Massac County's board is not shown — the county has a real website, but it surfaced only clerk and assessment pages, no board or election geometry.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (massaccountyil.gov) is real; the probe surfaced Circuit Clerk, County Clerk and Supervisor of Assessments pages, and nothing carrying district or precinct geometry. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "mchenry-park-district",
      "concept": "Park districts",
      "area": "McHenry County",
      "counties": [
        "mchenry"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "McHenry is the one metro county whose park districts cannot be shown: the county publishes park facilities, not district boundaries.",
      "blocker": "The county's mapping publishes around 350 individual parks and facilities and no park district boundaries at all (measured July 2026; the county's 132 datasets re-checked 31 Jul 2026).",
      "wanted": "Park district boundaries on the county's mapping system."
    },
    {
      "id": "mchenry-ward-cities",
      "concept": "City council district",
      "area": "Harvard and Marengo",
      "counties": [
        "mchenry"
      ],
      "kind": "blocked",
      "layer": "ward",
      "summary": "Harvard's and Marengo's city wards cannot even be checked: Harvard's website blocks automated visits, and Marengo's ward setup is not confirmed anywhere official.",
      "blocker": "Checked 31 Jul 2026. Every request to cityofharvard.org is refused by the site's bot protection, and neither city's ward boundaries appear in any public map catalogue. We also could not confirm from an official source how Marengo's wards are arranged. (The City of McHenry's own seven wards were added 2 Aug 2026, naming the seat but not drawing the boundary.)",
      "wanted": "Ward boundaries for either city from any official source, plus a plain description of how each city's wards are laid out."
    },
    {
      "id": "mclean-special-districts",
      "concept": "Fire, park and library districts",
      "area": "McLean County",
      "counties": [
        "mclean"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "McLean publishes rich election mapping and no fire, park or library district boundary.",
      "blocker": "Checked three ways on 31 Jul 2026 — the county's own mapping server, its data hub of 28 datasets, and its online map account of 183 items — with no district boundaries in any of them. The park layers are county park facilities, and Allin Park District appears only inside a neighbouring region's combined map. The clerk's officials database carries fire, park and library trustee lists with nothing to attach them to.",
      "wanted": "Fire, park and library district boundaries. The clerk's trustee lists are already published."
    },
    {
      "id": "mercer-county-board-districts",
      "concept": "County board districts",
      "area": "Mercer County",
      "counties": [
        "mercer"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Mercer publishes its ten board members and their districts but draws the five districts nowhere.",
      "blocker": "The county runs no mapping system: parcels go to an outside tax vendor, and the only map results for the county are commercial aggregators rather than anything it publishes. Its own board page says “Mercer County Board Districts, Map and Contact List are found in the Document Section”, and they are NOT there — the public document index carries 90 files across eight folders, and none is a district map, a composition list or a reapportionment ordinance. The elections page's 109 files are election results and candidate packets. Re-checked 31 Jul 2026: the board page still points at the Document Section, the documents are still missing, and the index now even has a “County Board” category, which is empty. ASKED 1 Aug 2026 — the broken Document-Section link named to Clerk Gerber; no response as of 4 Aug (mailbox reconciliation). PARTLY ANSWERED 17 Aug 2026: Deputy County Clerk Brianna Adams sent ‘Mercer County Precinct Map 1.pdf’ — a 2021 SCAN (raster, no vector data) that draws the five board districts as overlays on the precinct fabric, archived from her e-mail. It evidences the lines without supplying them, and the composition list the board page promises is still unpublished; the composition ask remains open on her thread.",
      "wanted": "Mercer County board district boundaries, or a list naming the townships or precincts in each of the five districts — the document its own board page already claims to publish. The member list is published and detailed: 5 districts electing two members each, with party, home town, term and the Chairman flagged."
    },
    {
      "id": "momence-ward-geometry",
      "concept": "City council district",
      "area": "Momence",
      "counties": [
        "kankakee"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Momence elects eight alderpersons across four wards, mapped only on a 2017 image.",
      "blocker": "Checked 31 Jul 2026: the city's own ward map page serves a single image last changed on 30 Oct 2017, before the census. No Momence ward data exists in any public map catalogue, and the county's mapping carries no municipal wards. The per-ward member list is on the city's own pages.",
      "wanted": "Momence's adopted ward boundaries as map data. The seats are already published."
    },
    {
      "id": "monroe-fire-district-names",
      "concept": "Fire protection districts",
      "area": "Monroe County",
      "counties": [
        "monroe"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Monroe's fire districts are labelled only by abbreviation — NAVFD, MVFD, PDRVFD — and nothing published spells them out.",
      "blocker": "Checked 2 Aug 2026, when the county was added: the county's fire data carries 26 shapes labelled with a three-to-six letter abbreviation plus a zone number, so the 26 are zone fragments of a smaller number of departments. No key exists on the county's mapping, its website or the fire districts' own pages, and the “VFD” ending plus the zone column suggest these are response areas rather than the taxing districts. A card reading “MVFD” tells a reader nothing they can act on, and guessing which of several similarly-initialled districts it is would be worse.",
      "wanted": "A key matching Monroe's fire abbreviations to district names, or boundaries that carry the names. The shapes are already published and would be shown the day the names exist."
    },
    {
      "id": "morris-ward-geometry",
      "concept": "City council district",
      "area": "Morris",
      "counties": [
        "grundy"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Morris — Grundy's county seat and its only ward-electing municipality — elects eight aldermen from four wards that are mapped nowhere usable.",
      "blocker": "The county's mapping has no ward data and nothing appears in any public map catalogue. The city's own site blocks automated visits, its ward map is an image from 2021, and Ordinance 3977 defines the wards as a map exhibit plus written legal descriptions. The alderman list itself is published by ward in the clerk's July 2026 directory.",
      "wanted": "Morris ward boundaries as map data — from the city, from the county, or through any public map catalogue."
    },
    {
      "id": "moultrie-county-board",
      "concept": "County board",
      "area": "Moultrie County",
      "counties": [
        "moultrie"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Moultrie County's board is not shown — the county has a full website with election pages, but publishes no election geometry.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (moultriecountyil.gov, also at co.moultrie.il.us) is real and current: an Election & Voting department, a Precinct Committeemen page, and a separate Circuit Clerk site (moultrieco.org). None of it carries boundaries. Moultrie was one of the two counties pass 12 pushed the frontier onto when Macon shipped; it is now researched. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "ogle-lasalle-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Ogle and LaSalle Counties",
      "counties": [
        "ogle",
        "lasalle"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Neither Ogle nor LaSalle contributes fire, park or library districts, though both levy taxes for them.",
      "blocker": "Neither county publishes the boundaries anywhere. Ogle's whole online map account was checked — 91 datasets, all cemeteries, bike routes, COVID sites and survey forms — and its parcel viewer is a commercial product with nothing readable behind it. LaSalle runs its own mapping server, and every dataset on it was listed: zoning, flood, wetlands, parcels, tax maps, city limits, board districts and polling places, and no taxing district boundaries at all. Both counties DO publish the districts' names and tax rates — Ogle's yearbook even carries a valuation table for park and fire districts — but a name is not a boundary.",
      "wanted": "Fire protection, park and library district boundaries from either county as map data. The property-tax boundaries both counties already maintain in order to levy those taxes are exactly what DeKalb, Kankakee and Rock Island publish."
    },
    {
      "id": "ogle-municipal-wards",
      "concept": "City council district",
      "area": "Byron and Polo",
      "counties": [
        "ogle"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Byron and Polo elect by ward and their aldermen already appear on the Municipality card, but neither city's wards are mapped.",
      "blocker": "Neither city publishes ward boundaries. Nothing appears in any public map catalogue, the county's own mapping does not carry them, and neither cityofbyron.com nor poloil.gov links a ward map of any kind — not even a picture. The seats are not the problem: the Ogle clerk's yearbook already gives Byron's seven aldermen across four wards and Polo's six across three, and both are shown today.",
      "wanted": "Byron's four and Polo's three ward boundaries as map data. The names are already here and would attach to the seat the day the boundaries arrive."
    },
    {
      "id": "park-city-wards",
      "concept": "City council district",
      "area": "Park City",
      "counties": [
        "lake"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Park City is Lake County's one ward-electing city with no published ward boundaries.",
      "blocker": "Checked in the 31 Jul 2026 ward sweep: Waukegan and North Chicago now publish current ward data on their own accounts, and Lake Forest's wards ride the regional mapping consortium — all three are queued. Zion and Highwood elect at-large. Park City's 3 wards appear in no city, county or public map source.",
      "wanted": "Park City ward boundaries as map data."
    },
    {
      "id": "pass10-frontier-unasked",
      "concept": "County board districts",
      "area": "Hancock, Jackson, Marion and Warren counties",
      "counties": [
        "hancock",
        "jackson",
        "marion",
        "warren"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Four frontier counties have working websites but no map data anyone has found; none has been asked directly yet.",
      "blocker": "Checked 3 Aug 2026 in the pass-10 sweep. All answer normally on the web — Warren's board page even numbers four districts — but none publishes board district or precinct boundaries as map data anywhere that could be found: nothing in the state map catalogue, and no mapping service at any of the usual addresses. Marion is worth a note: the address the state publishes for its clerk does not exist, and the county is actually at marioncountyil.gov. What has NOT been done is the step that worked repeatedly this week, which is writing to the clerk and asking. Every one has a working e-mail address. THIS RECORD USED TO NAME FIVE COUNTIES. Jefferson left it on 6 Aug 2026 by being asked: its Clerk replied with a precinct shapefile the next day and the county is now served. That is the record's own prescription working on the first try, and it is the reason the remaining four are worth writing to rather than probing again.",
      "wanted": "For each: whether the county's board districts and voting precincts exist as map data, and where. Asking the four clerks is the next move, not more searching — Jefferson proved it takes one e-mail."
    },
    {
      "id": "pass9-ward-seats-without-maps",
      "concept": "City council district",
      "area": "Chillicothe, Elmwood, West Peoria, Colona, Galva, Geneseo, Beardstown and Virginia",
      "counties": [
        "peoria",
        "henry",
        "cass"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Eight cities now name their council members by ward, but publish no ward map, so the site can say who represents each ward without saying where the wards are.",
      "blocker": "Created by our own progress on 3 Aug 2026. The Henry, Cass and Peoria county clerk directories added this pass all give each alderman a ward number, so the Municipality card can say “Alderman, Ward 2” for these eight cities — but the ward layer cannot answer which ward a reader is standing in, because none of the eight publishes boundaries. All eight were searched in the public map catalogue on 3 Aug 2026 and none returned a ward or district layer of any kind. The City of Peoria was the ninth city in the same position and is the exception that shipped: it publishes its five council districts on its own map account.",
      "wanted": "Ward boundaries as map data from any of the eight — a city map account, a county layer, or a shapefile on request. The members are already in hand, ward by ward, so each card would name its seats the day the geometry arrives."
    },
    {
      "id": "peoria-fire-park-library-contact",
      "concept": "Fire, park and library districts",
      "area": "Peoria County",
      "counties": [
        "peoria"
      ],
      "kind": "data-quality",
      "layer": "fire-district",
      "summary": "Peoria's fire, park and library cards link each district's own website but still name no trustee, address or phone.",
      "blocker": "The county's district data carries a name and, unusually, a link to each district's own site, which the cards now use — but no officer, address or phone, and the link itself is filled in on some districts and blank on others. Trustees of Illinois fire, park and library districts are elected or appointed separately, and the county publishes no list of them.",
      "wanted": "A trustee list or contact details keyed to each district. The boundaries and the district's own link are already here."
    },
    {
      "id": "perry-county-website-blocked",
      "concept": "County board districts",
      "area": "Perry County",
      "counties": [
        "perry"
      ],
      "kind": "blocked",
      "layer": "county-board",
      "summary": "Perry County's website answers automated visits with a holding page instead of its content.",
      "blocker": "Checked 3 Aug 2026. Requests to perrycountyil.gov come back as a 168-byte holding response rather than any of the county's pages — the signature of a challenge screen sitting in front of the site, the same one this project has recorded in front of other county sites. Nothing about the county's board districts or precincts can be read while that is in place, and the state's map catalogue lists nothing for the county either.",
      "wanted": "Either a way through for an automated reader, or the board district and precinct information sent directly. The clerk's e-mail works."
    },
    {
      "id": "pike-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Pike County",
      "counties": [
        "pike"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Pike County's 31 voting precincts are not shown — the county runs no mapping system of its own.",
      "blocker": "Checked 2 Aug 2026 when the county was added: Pike publishes no precinct boundaries anywhere, and nothing for the county appears in any public map catalogue. Its election results are handled by an outside vendor whose site publishes turnout and totals, not boundaries. The precincts themselves are certainly defined — the county's own 2024 results report counts all 31 — but only as names.  NOT YET ASKED: this records what the county's WEBSITE shows, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "Pike County's precinct boundaries as map data, plus polling places if published. The board half needs nothing: Pike elects its nine members countywide, and they already show on the County card."
    },
    {
      "id": "plano-ward-officials",
      "concept": "City council district",
      "area": "Plano",
      "counties": [
        "kendall"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Plano's four wards have county-hosted boundaries and no published seat-holders anywhere.",
      "blocker": "Checked 31 Jul 2026: the county's ward data carries both Yorkville's and Plano's ward shapes from January 2022, and Yorkville's aldermen ride a companion dataset — but no county or city source names Plano's aldermen by ward. The county yearbook goes only as deep as the mayor and clerk, and the city publishes no list the sweep could find.",
      "wanted": "A Plano aldermen-by-ward list, from the city, the clerk or a county dataset, plus confirmation that the January 2022 ward boundaries survived post-census redistricting."
    },
    {
      "id": "pope-county-board",
      "concept": "County board",
      "area": "Pope County",
      "counties": [
        "pope"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Pope County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. popecountyil.com resolves and answers 503 to this network; the Clerk's domain is popeco.illinois.gov. Unverified from here, but 'no website' is not the finding. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "pulaski-county-board",
      "concept": "County board",
      "area": "Pulaski County",
      "counties": [
        "pulaski"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Pulaski County's board is not shown — the county's domain resolves to an address this project's environment refuses to connect to, so even its website went unverified.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. pulaskicountyil.gov resolves in DNS, but to an address the research environment's egress proxy refuses (\"DNS points to prohibited IP\") — a fact about THIS probe's environment, not about the county, recorded so the next pass knows the site was never actually seen. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "putnam-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Putnam County",
      "counties": [
        "putnam"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Putnam County's voting precincts are not shown — Illinois's smallest county publishes no boundaries for them.",
      "blocker": "Checked 2 Aug 2026 when the county was added: Putnam runs no mapping system beyond an assessment-office parcel tool, and no county items appear in any public map catalogue. The clerk publishes specimen ballots and polling places as documents, not as data. The board half needs no geometry — the five members are elected countywide.",
      "wanted": "Putnam County's precinct boundaries as map data, or a polling place list keyed by precinct."
    },
    {
      "id": "quincy-ward-officeholders",
      "concept": "City council members",
      "area": "Quincy (Adams County)",
      "counties": [
        "adams"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Quincy's 7 wards are on the map, but the city's website turns away automated visits, so the card can show which ward you are in without naming your alderman.",
      "blocker": "Checked 2 Aug 2026: quincyil.gov answers every address tried with a short Access Denied from the same kind of edge that blocks its county — a flat refusal, not a puzzle a browser could work through. Adams County is not yet one of the counties whose clerk directory this project reads, so there is no second source to fall back on. The ward boundaries themselves come from the county's mapping service, which is open.",
      "wanted": "The council roster by ward from any source that permits automated reading — the city's own page becoming reachable, or an Adams County clerk directory."
    },
    {
      "id": "randolph-fire-park-library",
      "concept": "Fire, park and library districts",
      "area": "Randolph County",
      "counties": [
        "randolph"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Randolph publishes no taxing district boundaries; its only countywide fire shapes are 911 response zones.",
      "blocker": "Checked 2 Aug 2026: among the county's 39 published datasets are two fire layers credited to Randolph County 911, and both are emergency response areas rather than fire protection districts. Presenting a dispatch zone as a taxing district would misstate who levies the tax, so neither is used. No park or library boundaries exist on the account at all.",
      "wanted": "Fire protection, park and library district boundaries as taxing districts. The county clearly has the capacity: its precinct and ward data is current and well maintained."
    },
    {
      "id": "randolph-precinct-polling",
      "concept": "Polling places",
      "area": "Randolph County",
      "counties": [
        "randolph"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "Randolph's precinct cards name the precinct and nothing else — the county's data has a field for the polling place and leaves it empty on every row.",
      "blocker": "Checked 2 Aug 2026: the precinct data lists 35 named precincts with a polling-place field that is blank on all 35, and no separate polling place dataset exists among the county's 39 published map layers. Randolph also elects its board countywide, so there is no district row either, which is why this is the sparsest precinct card here. Everything on it is what the county publishes.",
      "wanted": "Polling places filled in on the precinct data, or any list from the clerk pairing precincts with polling places."
    },
    {
      "id": "richland-county-board",
      "concept": "County board",
      "area": "Richland County",
      "counties": [
        "richland"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Richland County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer under the probed patterns.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. richlandcounty.illinois.gov answers 200 with a /county-board/ page. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "rock-island-andalusia-township-library",
      "concept": "Library taxing district",
      "area": "Andalusia Township (Rock Island County)",
      "counties": [
        "rock-island"
      ],
      "kind": "no-source",
      "layer": "library-district",
      "summary": "Andalusia Township elects a library board the map cannot show: the county's library layer carries nine districts, and the township's library is not one of them, so its 11 square miles read as having no library at all.",
      "blocker": "Measured 16 Aug 2026 against the county's own certified record: the Clerk's April 2023 consolidated-election candidate list names TEN library bodies electing trustees, and the county GIS library layer (TaxDistricts layer 5, edited 2022-01-14) draws only nine. The missing tenth is the Andalusia Township Library — a TOWNSHIP library under a different statute than the nine library districts, which is almost certainly why a layer named Library Districts omits it. Its service area is presumably the township itself, but presumably is not a boundary this app will draw: shipping the township line as the library's would assert a taxing boundary no county source states.",
      "wanted": "The Andalusia Township Library's taxing/service boundary as map data, or a county statement that the township boundary is that library's boundary — either lets the card answer there instead of showing nothing."
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
      "summary": "Precincts show up everywhere in Winnebago County except inside Rockford itself.",
      "blocker": "Rockford runs its own Board of Election Commissioners, so the county's 94-precinct map stops at the city line. That was measured rather than documented: of 131 test points that returned nothing, 130 fall inside Rockford. The clerk publishes a list of city precinct committeepeople, so the precincts clearly exist — no boundaries for them do. Re-checked 31 Jul 2026 and unchanged: the election board's 2026 polling list shows 89 city precincts across 14 wards, still with no boundaries behind them.",
      "wanted": "Precinct boundaries from the Rockford Board of Election Commissioners, or a city precinct dataset on the county's mapping system. This is the Chicago-and-suburban-Cook split repeating in a smaller city, and the app already handles that shape."
    },
    {
      "id": "saline-county-board",
      "concept": "County board",
      "area": "Saline County",
      "counties": [
        "saline"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Saline County's board is not shown — the county HAS a website (found 2026-08-09); what is missing is map data and a board-form answer.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed — salinecounty.org is Saline County ARKANSAS's, a decoy. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. salinecounty.illinois.gov answers 200 with a /county-board/ page. salinecountyil.com is a separate site and should be checked before use. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website.",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "sangamon-park-library-districts",
      "concept": "Park and library districts",
      "area": "Sangamon County",
      "counties": [
        "sangamon"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "Sangamon's park and library districts have published trustee lists and no boundaries.",
      "blocker": "The county's 203 published datasets, all checked on 31 Jul 2026, contain no park or library district boundaries. The clerk publishes the officeholder half in full: the Springfield Park District board and 14 library district boards, each with a trustees list.",
      "wanted": "Park and library district boundaries — from the county, from the districts themselves, or from a statewide taxing-district source. The trustee lists are already in hand."
    },
    {
      "id": "scott-county-commissioners",
      "kind": "no-source",
      "concept": "County commissioners (at-large)",
      "area": "Scott County",
      "layer": "county-board",
      "counties": [
        "scott"
      ],
      "summary": "Scott is a commission county — three commissioners elected countywide — and while its own results name every winner, nothing confirms those three still hold the seats.",
      "blocker": "Researched 8 Aug 2026, closing an absence that had NO record at all. AT-LARGE PROVEN from the county's own results portal at results.gbsvote.com, which names the county clerk as Election Authority (Greene l_id=11, Morgan l_id=16, Scott l_id=19): the 8 Nov 2022 GENERAL ELECTION, marked ** OFFICIAL RESULTS **, carries \"FOR COUNTY COMMISSIONER / 10 of 10 precincts reporting / Vote for ( 1 )\" (John D. Simmons), and the 19 Mar 2024 PRIMARY, also OFFICIAL, repeats it for both parties (Thomas L. Peterson, Republican). The whole county votes for one seat at a time; the only \"DISTRICT\" strings on the 2022 canvass are the Fifteenth Congressional, One Hundredth Representative and Fiftieth Legislative districts. So there is no geometry to seek and none should be invented. scottcoil.gov/commissioners publishes the office phone (217-742-5532) and commissioners@scottcoil.gov but renders the members themselves through a Munibit \"People\" widget whose /api/public/mwjsPeople endpoint returns HTTP 500 without the page's own parameters, and the Internet Archive preserved the same empty shell. CORRECTED 2026-08-08, hours after this record first shipped: the claim above that the names are unreachable was WRONG, and the source that disproves it is the very one cited for the board form. The county's results portal names the winner of every commissioner contest in plain HTML — Robert L. Schafer (R) in Nov 2020 and John D. Simmons (R) in Nov 2022, both on OFFICIAL canvasses; Thomas L. Peterson (R) in Nov 2024. Three separate patterns of mine missed them, not the data: the office is headed \"FOR COUNTY COMMISSIONER\" in recent years but plain \"COUNTY COMMISSIONER\" in 2020 and abbreviated \"COUNTY COMM\" on Morgan's 2020 page, and each time the fix was in the reader. WHAT IS ACTUALLY MISSING is narrower and does not go away with better parsing: election returns record who WON a contest, never who holds the seat today. A mid-term vacancy filled by APPOINTMENT appears in no return anywhere, and the staggered six-year, one-per-general structure that turns three contests into three sitting members is an INFERENCE from the pattern, not something the county states. Publishing these three unconfirmed would be precisely the guess the honesty rules forbid, so the ask became a confirmation rather than a request for a roster. ASKED 2026-08-08: confirm those three, name the chairman, correct the term assumption.",
      "wanted": "Confirmation that Schafer, Simmons and Peterson are the three currently serving, and which is chairman. Not a roster from scratch: a yes/no on three names the county itself published. No geometry."
    },
    {
      "id": "st-clair-board-contact",
      "concept": "County board members",
      "area": "St. Clair County",
      "counties": [
        "st-clair"
      ],
      "kind": "data-quality",
      "layer": "county-board",
      "summary": "St. Clair board cards name the member and nothing else, because the county publishes no contact details for individual members.",
      "blocker": "Checked 31 Jul 2026 on the county's own board pages: all 28 district pages give only the shared countyboard@co.st-clair.il.us address and the (618) 277-6600 switchboard. Not one member has a published direct phone or email. Committee assignments are the only extra detail available — with one trap: District 16's photo caption reads “District 17”, so the district has to be read from the page's web address, never from the caption.",
      "wanted": "Any county-published phone or email for individual members. Short of that, the shared mailbox plus committee assignments is as far as this card can honestly go."
    },
    {
      "id": "st-clair-park-library-districts",
      "concept": "Park and library districts",
      "area": "St. Clair County",
      "counties": [
        "st-clair"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "St. Clair publishes no park or library district boundaries anywhere in its mapping.",
      "blocker": "Everything checked on 31 Jul 2026: the county's mapping server (17 datasets plus two folders), its online map account (36 items) and the 30 datasets hosted there — zero park or library boundaries. Fire fared better: a 44-shape countywide fire map turned up in the county's dispatch folder, names only, and is queued with a caveat about whether it maps taxing districts or dispatch zones.",
      "wanted": "Published park and library district boundaries for St. Clair County."
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
      "blocker": "The county publishes 103 polling places, but labels them in groups written for people rather than one per precinct — “Belleville9,10, 12 & 16” — with spacing and numbering that do not match the precinct data's “Belleville 9”. Matching them up means interpreting that phrasing, which would quietly send someone to the wrong place the moment the wording changed. Re-checked 31 Jul 2026: still only the combined labels.",
      "wanted": "Polling places listed one per precinct, or a polling place field on the precinct data — the way Madison, Kendall, LaSalle and Grundy all publish it."
    },
    {
      "id": "stephenson-freeport-precincts",
      "concept": "County board districts",
      "area": "Freeport Township, Stephenson County",
      "counties": [
        "stephenson"
      ],
      "kind": "data-quality",
      "layer": "county-board",
      "summary": "Stephenson's four Freeport Township districts are traced from the county's printed map rather than built from published data. They are accurate to roughly 20 metres, and the card says so.",
      "blocker": "ASKED AND ANSWERED, 3 Aug 2026 — and the answer changed what this gap says. It used to read 'Stephenson publishes no precinct boundaries'. The county does publish them: County Clerk Jazmin Wingert replied to a records request by pointing at her own Elections page, which carries the adopted 2022 precinct maps for Freeport Township and for the rural half. They are printed maps, not map data, so they are traced the same way these four districts are — and the county's 36 precincts now ship as their own layer, traced from exactly those documents. What is still missing is the same thing as before: precinct geometry as DATA. The four Freeport districts remain accurate to roughly 20 metres, and the card says so. As a check, the fit places the map's own rivers and creeks — features it was never fitted against — within 50 metres for 98.9% of their points, with a typical error of 16 metres; the county's four rural districts are whole townships and are exact. THE SECOND DESK IS NOW NAMED AND MEASURED, 5 Aug 2026: asked who 'GIS' is, Clerk Wingert pointed at the county's Maps & GIS page, whose entire content is a link to WINGIS (wingis.org) — the regional consortium that holds Stephenson's parcel and layer data. WinGIS does not publish it. Its data page says digital data must be PURCHASED: submit a Data Request, receive a quote within 24 hours, and have a signed Data License Agreement on file; its subscription tier is open to 'non-profit organizations & commercial businesses only' and grants access 'through a custom mapping interface through the Internet only'. Measured rather than inferred from the terms: the Stephenson public viewer's own service, maps.wingis.org/public/rest/services/StephensonPublicPropertySearch/MapServer, answers an unauthenticated request with 'Token Required', while the neighbouring WardsAndDistricts and ElectedOfficials services on the same host are open (and are Winnebago-only). So the data demonstrably EXISTS and has a price — the same shape as the counties whose assessor sells parcels — rather than being missing. That is a different gap from 'nobody has it', and it is the one to record.",
      "wanted": "Freeport Township's 16 precincts as map data. The holder is now known to be WinGIS, which sells rather than publishes it. ONE OF THE THREE ROUTES IS NOW CLOSED, by the Clerk herself: asked in writing on 5 Aug 2026 whether her office could release the county's own precinct file directly — with an offer to file a formal FOIA if that was the required form — County Clerk & Recorder Jazmin Wingert answered on 6 Aug, 'The only precinct maps I have are the ones that are accessible on the website.' So the election authority holds no digital precinct file at all; the published maps this project already traced ARE the county's copy, and no FOIA can produce a file that does not exist. That is a definitive answer and not a refusal, and it means the 20-metre tracing is very likely the best this concept gets in Stephenson until one of the two remaining routes opens: a quote through WinGIS's Data Request process, or a public WinGIS service for Stephenson equivalent to the open Winnebago ones."
    },
    {
      "id": "stephenson-park-library-districts",
      "concept": "Park and library districts",
      "area": "Stephenson County",
      "counties": [
        "stephenson"
      ],
      "kind": "no-source",
      "layer": "park-district",
      "summary": "Stephenson's park and library districts exist only as shading inside pictures in the county's 2014 maps — unlike its fire map, which has real lines and is already shown.",
      "blocker": "Checked 2 Aug 2026, when the fire map was traced: in the county's 2014 park and library district maps on the state's site, only the legend is drawn with real lines — the district shading itself is baked into sixteen image strips covering the map body. The fire map, from the same July 2014 series, draws its districts as real lines, which is why it could be traced. The district names still match the 2025 tax roll (park 4 of 4, library 4 of 4). Tracing the shading is possible in principle, but it would stack pixel-level error on top of the fitting error and land far coarser than any other boundary here. ASKED 1 Aug 2026, ANSWERED 3 Aug 2026: County Clerk Jazmin Wingert holds only the election maps and directed anything else to the county GIS office — so the ask is live but has moved to a second desk, which is the Tier-3 pattern in \"The ask ledger\". THAT DESK IS NOW IDENTIFIED, 5 Aug 2026, and it is not a county office: asked who GIS is, the Clerk pointed at the county's Maps & GIS page, which contains nothing but a link to WINGIS (wingis.org), the regional consortium. WinGIS SELLS digital data — Data Request, quote within 24 hours, signed Data License Agreement — and its Stephenson viewer service is token-gated (see stephenson-freeport-precincts for the measurement). Two things follow for park and library specifically. First, whether WinGIS even holds these boundaries is unknown: its open services on the same host carry Winnebago wards, precincts and townships but nothing about park or library districts in any county, so a purchase might buy a file that does not exist. Second, and more usefully, the DISTRICTS THEMSELVES were never asked. Four park districts and four library districts are eight small public bodies that each hold their own boundary, and no one has written to them.",
      "wanted": "Park and library district boundaries as map data. Three live routes, cheapest first: the eight districts themselves (each holds its own boundary); a re-export of the county's own 2014 maps with the shading as lines rather than images; or a WinGIS quote, if WinGIS turns out to hold these layers at all. THE FIRST ROUTE IS NOW THE ONE TO WORK, and the county has said so: asked 5 Aug 2026 whether she happened to have contact information for any of the eight districts, County Clerk & Recorder Jazmin Wingert answered on 6 Aug that the county neither publishes it nor holds a report that generates it — and offered, unprompted, to help with any district this project cannot reach on its own. So the county is a named fallback for reaching the districts, not a source for their boundaries."
    },
    {
      "id": "tazewell-precinct-polling",
      "concept": "Polling places",
      "area": "Tazewell County",
      "counties": [
        "tazewell"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "Six of Tazewell's 82 precincts name no polling place: the county's precinct data points them at buildings its own polling place list does not include.",
      "blocker": "Checked 2 Aug 2026, when the county was added: 76 of the 82 precincts match a published polling place. The six that do not — Elm Grove 02, Cincinnati 02 and 05, Pekin 01 and 06, and Morton 01 — point at three building IDs that appear on no published county dataset. That is a gap in the county's own records, not in how we match them. Everything else on those cards still shows. ANSWERED 17 Aug 2026: Deputy Clerk Reynolds sent the Clerk's own polling-place listing for the 2026 General Primary — 19 townships, 82 precincts, 49 polling places, every precinct paired with a named building and address, archived from her e-mail. All six orphans are in it: Elm Grove 02 → Grace Baptist Church; Cincinnati 02 and 05 → Pekin Bible Church; Pekin 01 → First Christian Church; Pekin 06 → Miller Center; Morton 01 → Eastside Bible Church (Cincinnati 01's own site is marked ‘pending resolution’ by the county — read the list, not this note, when building).",
      "wanted": "A supplement file in the Whiteside shape — the six orphaned precincts' sites from the Clerk's 17 Aug 2026 list, consulted only where the county's own layer has no match, the card saying where the location came from. The list is in hand; what remains is the build."
    },
    {
      "id": "union-county-board",
      "concept": "County board",
      "area": "Union County",
      "counties": [
        "union"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Union County's board is not shown — the county's website refuses every automated request, the Knox pattern.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. unioncountyil.gov answers 403 Forbidden to every request from this environment, on both the apex and www hosts — the same refuse-all posture Knox County's site takes, so nothing behind it could be characterized. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "vermilion-county-website",
      "concept": "County board districts",
      "area": "Vermilion County",
      "counties": [
        "vermilion"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "The largest unserved county on the frontier. Asked twice and answered twice: the site is vercounty.org, and the election authority has now stated in writing that her office holds no shapefiles or GIS layers — the maps it publishes are the only maps there are.",
      "blocker": "Checked 3 Aug 2026. Vermilion is about 74,000 people, the biggest county adjacent to the served area, and none of its geography is on the site. The state's election directory gives the clerk an address at vercountyil.gov. That domain exists, but it refuses secure connections and, over an ordinary one, forwards visitors to Google — it is parked, not a county website. Several likely alternatives were tried and none exists. This is the same trap McDonough set: an e-mail address at a domain that hosts nothing. McDonough was solved by asking its clerk, who named a website no amount of guessing would have found. SO WAS THIS ONE, and the record predicted its own solution: ASKED 5 Aug 2026, ANSWERED THE SAME DAY by Chief Deputy County Clerk and Supervisor of Elections Carrie Wilson — the county's website is vercounty.org, and the maps her office publishes are at vercounty.org/county-clerk/voter-maps/. (Seal permissions, separately, go to Jennifer Jenkins in the County Board office, jjenkins@vercounty.org.) THE METHOD LESSON IS IN THE HOSTNAME: \"ver\" is an ABBREVIATION of Vermilion, so no ladder built from the county slug — vermilioncountyil.gov, vermilioncounty.org, co.vermilion.il.us — could ever have reached it, which is why two passes of searching failed where one question succeeded. Neither the site nor the Archive is reachable from this project's network, so what the voter-maps page actually carries is still unmeasured. THE FORMAT QUESTION IS NOW ANSWERED, AND THE ANSWER IS NO: asked on 5 Aug whether those maps exist as data, Wilson replied the same evening — \"Those are the only maps we offer, our county does not have shapefiles or GIS layers for precinct look ups. There is a precinct finder on the Illinois State Board of Elections site voters may utilize or they may call our office.\" That is a refusal from the right desk, which this ledger treats as a finding rather than a dead end: it converts an inferred blocker into a stated one, and it means no amount of further searching of the county's own publications will produce geometry. Read exactly, her sentence is explicit for PRECINCTS and covers board districts by implication (\"the only maps we offer\"), so it settles what the CLERK holds; a county GIS or assessor's desk, if Vermilion has one, is a different office and was not asked. The lookup she named — ova.elections.il.gov/PollingPlaceLookup.aspx — was measured before being recorded and is NOT a data lead: it is a per-address form (zip, then a street from a fixed dropdown, then a house number) that answers one voter at a time, holds no boundary, and offers no download.",
      "wanted": "A shapefile or GIS layer of Vermilion's board districts or precincts from some holder OTHER than the Clerk's office — a county GIS or assessor department, the regional planning commission, or whoever drew the current district map — because the election authority has now confirmed in writing that her office has none. The county's own published maps are pictures and no further ask of that desk will change it."
    },
    {
      "id": "wabash-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Wabash County",
      "counties": [
        "wabash"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Wabash is served through the County card — three at-large commissioners, from the Clerk's own e-mail — but its voting precincts are not shown: the county has no website to publish boundaries on, and the precinct half of the question its Clerk answered about the board is still unanswered.",
      "blocker": "Successor to wabash-county-board, RETIRED 2026-08-17: Clerk Will's e-mail of 16 Aug 2026 carried the three commissioners' names — Timothy R. Hocking, Robert G. Dean, Scott C. West — answering that record's wanted line six hours after the follow-up, and Wabash shipped on the County card the next day as the second DOCUMENT_ROSTERS county (her e-mail lists a HOME address per commissioner and no county contact; per the Edwards rule none of that ships, so each row is a name alone, and the chairman question is asked but unanswered — nobody is marked Chairman until she says). What the retired record established still stands and moves here. The BOARD question is CLOSED: commission form, three commissioners at large, one elected each General Election for a six-year term — the election authority in writing, 5 Aug 2026; there are no districts to draw and none should ever be invented. WABASH COUNTY HAS NO WEBSITE: wabashcounty.illinois.gov resolves (A record 157.185.73.189, a southern-Illinois ISP), carries mail (Rackspace MX — why the Clerk's e-mail arrives), and serves nothing — port 80 answers HTTP 503 on every attempt, 443 resets, www is NXDOMAIN; measured 5 Aug 2026, re-checked 9 Aug, the JOHNSON COUNTY pattern. What is NOT settled is this record's subject: the same 5 Aug e-mail that asked the board question also asked whether voting precinct boundaries exist as map data, and none of the Clerk's replies has addressed that half. So whether Wabash's precincts exist as a file, on paper, or only in a vendor's system is UNMEASURED — unlike Edwards, whose Clerk stated \"on paper\" outright. THE DECOY THE RETIRED RECORD NAMED STILL APPLIES to any future search from this record: in.gov/counties/wabash is Wabash County INDIANA, across the river; Illinois's seats at Mount Carmel, and anything built here must come from Clerk Will or a Mount Carmel source.",
      "wanted": "The precinct boundaries in any form — a shapefile from whoever draws them, or a paper map scanned into a reply (the Stephenson route) — or failing both, the Clerk's word that they exist only on paper, which would convert this to a closed route the way Edwards' record closed. The precinct half of the 5 Aug 2026 question is still open with the Clerk."
    },
    {
      "id": "washington-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Washington County",
      "counties": [
        "washington"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Washington County's voting precincts are not shown — the county runs no mapping system and publishes its precinct map only as a picture.",
      "blocker": "Checked 2 Aug 2026, when the county was added: Washington has no online map account, no maps page and no viewer linked anywhere on its site, so there are no precinct boundaries to read. Its polling place list is an image-only PDF, and the state's copy of its district breakdown is a three-page picture with no readable text. The board districts were added anyway because they are made of whole townships, which the census publishes as usable map data — precincts have no such shortcut.",
      "wanted": "Washington County's precinct boundaries as map data, plus polling places if published. The board half is already covered."
    },
    {
      "id": "wayne-county-board",
      "concept": "County board",
      "area": "Wayne County",
      "counties": [
        "wayne"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Wayne County's board is not shown — the county has a real website whose mapping runs on a parcel portal, with no election geometry.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (waynecountyil.gov) is real: a Wayne County Board page, a Voting and Elections page, and an Online Mapping link into Sidwell's Portico portal — an ArcGIS-based PARCEL product whose configuration loads client-side; no election layer surfaced. waynecounty.org is a domain-for-sale page, a decoy. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "wenona-two-clerks-disagree",
      "concept": "Municipal officials",
      "area": "City of Wenona",
      "counties": [
        "marshall",
        "lasalle"
      ],
      "kind": "data-quality",
      "layer": "municipality",
      "summary": "Wenona straddles the Marshall/LaSalle line and its two county clerks publish different city councils. The card now shows Marshall's, because only Marshall's clerk has said where her list comes from.",
      "blocker": "Found 3 Aug 2026, when Marshall's municipal source shipped. Both clerks publish Wenona in full, and both agree on the mayor (Mary Jane Bade) and the clerk. They do not agree on the council. LaSalle's directory names EIGHT alderpersons — Flanigan, John Simmons, Julia Kitchens, Kym Healy, Nathen Anderson, Randy Lohr, Russell Skaggs Sr. and William Simmons — and no treasurer. Marshall's table names SIX trustees — Anderson, Healy, Zulz, John Simmons, Flanigan and Skaggs — plus Treasurer Jaclyn DeRubeis, dates every seat 2027 or 2029, and carries four direct phone numbers where LaSalle repeats the city-hall line on every row. RESOLVED ENOUGH TO SHIP, 3 Aug 2026, and on provenance rather than on our reading of which document looks fresher. Asked which list was right, Marshall County Clerk Jill Kenyon answered: “I just go by what the City has furnished to me.” That is a chain — City of Wenona to its county clerk to here — and LaSalle's directory states no origin at all. Marshall's document is also not careless about the very distinction it is being trusted on: it labels the board of its three OTHER cities “Alderperson” and only Wenona's “Trustee”, so that word is the city's rather than a habit of the table. The card therefore shows Marshall's roster, and three people LaSalle names (Kitchens, Lohr, William Simmons) are no longer shown. This gap stays OPEN rather than being retired, because only one of the two clerks has explained her source, and LaSalle has not been asked. ONE THING GOT WORSE, recorded rather than hidden: LaSalle repeated the city-hall line 815-853-4227 on every Wenona row, so the old card gave a phone number for all nine officials. Marshall publishes no hall contact at all — only four direct numbers — so the mayor and three trustees now show none. Carrying LaSalle's number across would mean showing one county's data under the other county's source link, which this project does not do. Marshall also prints every official's HOME address, which is not collected and never reaches data/app/. The switch also surfaced a parser bug: the county writes one of its fifteen numbers with no space after the Phone: label, and the scraper read only the words after that label — so Wenona's own city clerk had been silently losing her phone number. Fourteen of fifteen carrying the space is exactly why the odd one went unnoticed.",
      "wanted": "LaSalle's clerk saying where her Wenona list comes from, or the city itself publishing its council. Either would confirm the choice already made or overturn it — and the three people currently not shown are why it still matters."
    },
    {
      "id": "white-special-districts",
      "concept": "Fire, park and library districts",
      "area": "White County",
      "counties": [
        "white"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "White County's board districts, precincts, roster and polling places all shipped 2026-08-17; its fire, park and library districts have no known boundary source.",
      "blocker": "Successor to white-county-board, RETIRED 2026-08-17 when White shipped as the 50th dispatched county — and the record closed better than its own wanted line asked. That record wanted a Stephenson-style tracing; the build (scripts/build_white_boundaries.py) did the tracing and then did not ship it, because the tracing PROVED something better was available: TIGER's Census 2020 voting districts carry the county's 18 precincts exactly (18/18 by name; the map's Carmi inset traces the census edges to a measured ~2 m median), so the shipped geometry is exact census fabric and the county's own vector map decided only the COMPOSITION — confirmed 18/18 against the certified 2022/2024 General Election canvasses on the Clerk's Elections page, which also yielded every member's district (the board page names none) and the polling list (11 buildings, 18/18 precincts). What the retired record established still stands: the county's map data is the ONE FILE Clerk Kayci Heil linked on 2026-08-17 (\"White County, IL voting districts & precincts map.pdf\", archived in data/source/raw/), and the county runs no GIS beyond a parcel-search page. So no fire, park or library tiling has any known source — the 2026-08-04 hostname sweep found no self-hosted ArcGIS and nothing county-keyed in the ArcGIS Online catalogue, and nothing on the county's site names special-district boundaries. Mail-history note carried forward: clerk@whitecounty-il.gov hard-bounced a July 2026 message permanently (5-day retry, dead MX) and later recovered — delivery to this county is fragile, so an unanswered ask deserves a delivery check before a re-ask.",
      "wanted": "Any adopted boundary source for the county's fire protection, park or library districts — a map from the Clerk (who answered the board ask), the 911/ETSB office, or a district's own filing. Several such districts likely cross county lines, so a neighbouring county's GIS could answer for White's edge too."
    },
    {
      "id": "whiteside-municipal-officials",
      "concept": "Municipal officials",
      "area": "Whiteside County",
      "counties": [
        "whiteside"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Whiteside's 11 municipalities show a name and a link only, even though the county publishes unusually rich election mapping.",
      "blocker": "The county's map account carries precincts, polling places, electoral districts and an elected-representatives dataset — but every one of them stops at the county board and the state and federal offices. No municipal data exists. The Clerk publishes no yearbook or municipal directory, and the regional council publishes no member list. A county can have the best election mapping in the area and still name no village president.",
      "wanted": "A municipal officials dataset on the county's own map account — it would fit the pattern the county already uses — or a clerk-published directory."
    },
    {
      "id": "whiteside-precinct-polling",
      "concept": "Voting precincts",
      "area": "Whiteside County",
      "counties": [
        "whiteside"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "All 60 of the county's precincts now name a polling place and an address — but two of the locations come from the Clerk directly, because the county's own list still omits them.",
      "blocker": "CLOSED for the reader, still open at the source, 3 Aug 2026. The county's own join is 56 of 60 — re-measured live, and the previous entry was WRONG about which precinct: Coloma 9 resolves fine (facility 4, Rock River Christian Center), the Clerk confirmed that venue the same day, and the layer already agreed with her, so an override written for it was reverted rather than ship dead code for data that is already correct. The four that do not resolve are Sterling 9, 14 and 18 (all facility 22) and Prophetstown 1 (facility 26), neither id being among the 29 voting locations the county publishes. Asked which buildings those are, County Clerk Karen Stralow named them, and on a follow-up supplied their street addresses: facility 22 is Self Help Enterprises, 2300 W. LeFevre Rd., Sterling 61081; facility 26 is Winning Wheels, 701 E. 3rd St., Prophetstown 61277. Those two records ship in data/app/whiteside-precinct-polling.json and are consulted ONLY where the county's own layer has no match, so the day the county publishes them the file stops being read with no code change. All 60 precincts now show a polling place AND an address, and the four say on the card that the location came from the Clerk rather than from the published list. She has said she is forwarding both to the county's GIS department.",
      "wanted": "The two missing voting locations added to the county's own published polling list, which would retire our two hand-entered records. Nothing is missing from the card itself any more — this stays open only because the app is carrying data the county has not yet published."
    },
    {
      "id": "whiteside-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Whiteside County",
      "counties": [
        "whiteside"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Whiteside publishes unusually rich election mapping and no fire, park or library district boundaries.",
      "blocker": "The county's 63 published datasets, re-checked 31 Jul 2026: election geography, precincts, polling places and board districts — and no taxing district boundaries of any kind.",
      "wanted": "Fire, park and library district boundaries on the county's map account."
    },
    {
      "id": "williamson-county-board",
      "concept": "County board",
      "area": "Williamson County",
      "counties": [
        "williamson"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Williamson County's board is not shown — the county's website refuses every automated request, the Knox pattern.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. williamsoncountyil.gov answers 403 Forbidden to every request from this environment, on both the apex and www hosts — the same refuse-all posture Knox County's site takes, so nothing behind it could be characterized. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".",
      "wanted": "The board's form (districted or at-large) from a certified election document, then either the district boundaries as map data or the commissioners' roster from a county source."
    },
    {
      "id": "winnebago-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Winnebago County",
      "counties": [
        "winnebago"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Winnebago publishes no fire, park or library district boundaries — its only countywide fire shapes are 911 dispatch zones.",
      "blocker": "The county mapping system's full public catalogue (45 datasets, checked 31 Jul 2026) carries no taxing district boundaries for any of the three. The nearest datasets are the wrong kind rather than merely incomplete: the 911 “Fire” layer is a 364-shape dispatch map, one fire agency publishes its own boundary, and the park layers are individual park properties. A dispatch zone is not a taxing district, and presenting one as the other would misstate who levies the tax.",
      "wanted": "Fire protection, park or library district boundaries on the county's mapping, or on any Winnebago agency's. The county's 911 mapping proves the capacity is there."
    },
    {
      "id": "woodford-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Woodford County",
      "counties": [
        "woodford"
      ],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Woodford names its fire, park and library districts, but every “district” dataset it publishes is the parcel map wearing the district's name.",
      "blocker": "Checked 31 Jul 2026: the county's “Fire Protection Districts” dataset returns 25,824 records, one per parcel of land — property ID numbers, tax codes, owner and billing names, none of which this app would ever show — and the park and library datasets are built the same way. The tax codes prove the county maintains the real boundaries; it publishes the individual parcels instead of the combined district. (Woodford's board districts and precincts were added 2 Aug 2026; this is what remains.)",
      "wanted": "Fire, park and library district boundaries as actual districts — one shape per district — as map data."
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
      "blocker": "The roster builder's source publishes the D.C. office; district-office addresses are not in it. Recorded as a builder-scope enrichment candidate rather than a missing source. Noted in the 2026-07-31 validation pass: the wanted source exists and is already consumed by the Chicago fork (the congress-legislators district-offices file), so what remains is this fork's builder enrichment and factory migration — build work, not a missing source.",
      "wanted": "Nothing new from readers — the enrichment is a recorded builder-scope follow-up; the entry stays only until the card shows the district office."
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
      "blocker": "The roster builder's source publishes the D.C. office; district-office addresses are not in it. Noted in the 2026-07-31 validation pass: the wanted source exists and is already consumed by the Chicago fork (the congress-legislators district-offices file), so what remains is this fork's builder enrichment and factory migration — build work, not a missing source.",
      "wanted": "Nothing new from readers — the enrichment is a recorded builder-scope follow-up; the entry stays only until the card shows the district office."
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
An empty `counties` means the gap has no mappable footprint and appears only in the
everywhere list. Bureau, Mercer and Jo Daviess sat there until 2026-08-02 — each has a
real, published board roster or district composition but nothing that draws the
boundary — when a pin dropped in gray-washed Jo Daviess getting told "nothing missing
where you clicked" exposed the cost: their gaps were real and unmatchable. All three now
ship `<slug>-county-outline.json` as GAP-LOCATION geometry only (build_county_outline.py
documents the distinction — an outline alone dispatches nothing), so their gaps attach to
their ground. (Henry sat in the same list until 2026-08-02, when its "Alternate" map
proved to be the adopted plan and the county shipped outright.) (The original example here was DeKalb, on the strength of a
`dekalb-county-gis` entry claiming the county had no GIS at all. It has a 72-service
ArcGIS Online org; the entry was wrong, not merely stale, and it is retired. A gap that
says a source does not exist ages badly in one direction only — worth re-testing the
"no-source" entries periodically rather than trusting them.)

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
| City council district | SHIPPED `ward` — consolidated CountyDispatch keyed by MUNICIPALITY (the dispatcher's first non-county key): Chicago 50 (Socrata wards + alderman roster) + suburban Cook 21 municipalities (county GIS layer 22) + Evanston 9 (city GIS, which also carries each alderperson's email/phone/ward page) + Will 4 cities incl. Joliet's council DISTRICTS (county GIS) + Aurora 10 (city GIS) + Rockford 14 (WinGIS `ElectedOfficials` L20 — alderperson + e-mail ride the boundary) + Rock Island's Moline 7 and Silvis 4 (county-hosted city layers, both edited 2022 — Whiteside's six-municipality layer is a recorded gap at a 2019 vintage) + DeKalb's DeKalb 7 / Sycamore 4 / Genoa 4 / Sandwich 4 (four county-hosted city layers, all edited 2023) + Mendota 4 (the city's own org, edited 2022 — the only one of LaSalle's four ward cities that publishes geometry; La Salle's ward map is a raster PNG, Peru's and Earlville's do not exist, and Ogle's Byron and Polo are the same gap) **+ the pass-6 ward tranche (2026-08-02): thirteen sources / twenty-two cities** — Berwyn 8 (city org; roster seats) + Waukegan 9 (city 2025 locator — alderman + per-seat phone AND e-mail on the polygon) + North Chicago 7 (city 2026 layer, honestly seat-only) + Belvidere 5 (Boone county GIS — BOTH aldermen + phones per ward) + St. Charles 5 and Geneva 5 (city orgs — both aldermen w/ per-seat contact; St. Charles' literal 'Unknown' phone strings dropped) + Batavia 7 (city server '2027/2025' map — both aldermen's names; its contact columns are declared-and-empty) + West Chicago 7 (city 2025 service — both aldermen + per-ward page URL) + McHenry 7 (city org, seat-only) + Yorkville 4 and Plano 4 (Kendall Hosted/Wards filtered to the two — the Aurora/Joliet sliver rows are dropped; seat-only, Plano's missing roster a recorded gap) + Pontiac 5 (city org; roster seats 2/ward) + Bloomington 9, Le Roy 4 and Lexington 3 (ONE McLean clerk layer parsed by name; its REPNAME column measured stale on two cities is read nowhere — all three join the roster) + Lincoln 4 (city org; roster + current GIS names as fallback) + Springfield 10 (SPI 2022 map at layer 4; roster) + Freeport 7 (city org; roster — the layer's stale Alderperson column is read nowhere) + East Moline 7 (city org, joined the rock-island entry; alderman + contact on the polygon) + Belleville 8 (St. Clair county L13 — the duplicate-id sliver dropped by largest-ring-per-id) and O'Fallon 7 (L14), both joining the roster 2/ward. Suburban seat-holders join `municipal-officials.json` by municipality + seat number, so a ward card names the same person the Municipality card lists for that seat | SHIPPED `council` (51) | SHIPPED `supervisor-district` (11; doubles as the county board — consolidated city-county) |
| Electoral precinct / ballot sub-unit | SHIPPED `ward-precinct` + `county-precinct` (consolidated CountyDispatch: suburban Cook current map 1,430 — Cook-outside-Chicago only, city precincts are the BOE ward-precinct layer — + Will 2022 map 310 + DuPage 2024 map 600 + Lake current map 431 + Kane current map 292 + McHenry current map 223 + Kendall current map 78 w/ the county's own polling-place assignment per precinct — every metro county covered — plus the sixteen expansion counties: LaSalle 119 (polling joined 119/119) + Kankakee 59 + Boone 37 (polling on the feature) + Grundy 40 (polling joined 38/40) + Macoupin 45 (the county's own Socrata portal — the 2022-2032 fabric ab79-cnsh; polling joined 45/45 from its sibling polling dataset by deterministic label expansion, 2026-08-02 — the pass-4 note of 105 was the superseded map) + Madison 191 (polling joined 191/191, the fleet's cleanest) + St. Clair 150 (polling is a recorded gap) + Winnebago 94 (county-clerk jurisdiction only — Rockford runs its own election commission, a recorded gap) + DeKalb 69 + Ogle 51 (the county GIS Coordinator's shapefile, sent on request; the Clerk supplied the other half of the answer — how retired Forreston 3 was absorbed — without which the 2020 fabric would have shipped a precinct that no longer exists) + Lee 46 + Whiteside 60 (polling joined 56/60 from the county's layer; the last four filled from two locations the Clerk supplied with addresses, which the county does not publish — all 60 now show a polling place and an address) + Rock Island 120 + McLean 141 (polling joined 141/141) + Logan 29 (the clerk's HTML polling table shipped as a same-origin file, joined 29/29) + Sangamon 166 (polling joined 165/166) + Carroll 22 (TIGERweb Census-2020 VTDs live — the county did not re-precinct; the clerk's polling notice shipped as a same-origin file, 22/22) + Woodford 37 (TCRPC's election service, polling joined 37/37 on the numeric polling reference, 2026-08-02) + Macon 64 (polling joined 64/64 to 29 locations — recorded here 2026-08-04 with the matrix row it was omitted from at ship time) + Effingham 38 (the first island — polling joined 38/38 to 24 locations by facilityid, every location with a full address) + Hamilton 16 (the second island, from the GIS the Clerk pointed to in a four-minute reply; the layer's 17th row is a null-named byte-for-byte duplicate of Dahlgren 1, dropped in the loader; polling joined 16/16 to 13 locations from the Clerk's statutory 3/17/2026 General Primary notice on the county's post-migration website, shipped as a same-origin file with the card row election-labelled — the notice settled the Dahlgren #1/#2 pairing two ~0.3 mi-coarse georeferencing instruments could not, 2026-08-11); Kane's card also gained the township name from the clerk's own prefix pairing and the election-labelled polling row, 292/292 — the pass-6 precinct tranche, 2026-08-02) | SHIPPED `election-district` (~4,200) | SHIPPED `election-precinct` (`jg6x-23ig`, 2022 map; subOf `supervisor-district`, polling-place lookup link) |
| County legislature / commissioner | SHIPPED `county-board` (consolidated CountyDispatch layer: Cook Commissioner 17 + Will 11 + DuPage 6 + Lake 19 + Kane 24 + McHenry 9 + Kendall 2 + LaSalle 29 (DERIVED — see below) + Kankakee 28 + Winnebago 20 + Livingston 3 + McLean 10 + Logan 6 + Sangamon 29 + Madison 26 + St. Clair 28 + DeKalb 12 + Ogle 8 + Stephenson 8 + Carroll 3 + Lee 4 + Whiteside 3 + Rock Island 19 + Woodford 3 (DERIVED — TIGER townships per adopted Ordinance 2020/21 #005; five members per district from a weekly directory scrape, 15/15 with phone and e-mail; no chair marked — elected from within the body, the directory doesn't say) + Boone 3 (RUNTIME-MERGED — the county GIS's three per-district layers, each pre-dissolved, merged and district-tagged at load time; four members per district from a weekly board-page scrape, 12/12 with phone, e-mail and term-expiry year; one Vice-Chairman tagged verbatim, no Chairman named) + Grundy 3 (DERIVED — the county's own precinct layer dissolved per the adopted 10/12/2021 map, the transcription proven by the map's printed populations to the person; six members per district from a weekly board-page scrape, 18/18 with party, since-year, committees, phone and e-mail; Chairman tagged from his own row) + Henry 2 (DERIVED — TIGER townships per adopted Ordinance 21-33, twelve whole townships per district, the composition proven by the adopted map's own two-census population table AND live Census POP100, all to the person; TEN members per district — the fleet's widest — from a weekly scrape of the county's own district-keyed directory, 20/20 with e-mail; no chair marked, so none is tagged) + Stark 2 (2 districts of FOUR, the smallest board here — boundary from the County Clerk's own Google My Maps, which is the county's entire GIS and which she confirmed current by e-mail; per-SEAT e-mail addresses, Chair and Vice-Chair badged) + Effingham 9 (the FIRST ISLAND, 2026-08-04 — single-member districts lettered A-I with the roster ON the district features: name, party, phone and e-mail read straight off the county's own live service, the McLean pattern with one seat and no scraper between the card and the county) + Jo Daviess 17 (PURCHASED, 2026-08-17 — the fleet's first bought boundary: 14 of the 17 single-member districts cut across precincts along roads, so no dissolve or tracing could draw them, and the county SELLS its GIS data; the county's own shapefile under Jo Daviess County GIS Digital Data License Agreement #008382, displayed under the county's written authorization, the raw file retained offline per the licence, the card crediting Jo Daviess County GIS per its Credits clause; roster weekly from the county's own board page — party and term on every seat, a direct phone and e-mail per member, one counted-never-named vacancy) districts — LaSalle REBUILT 2026-08-01 on derived geometry (its own board GIS is the superseded 2011-2021 map): the county's precinct layer dissolved per its 2024+2026 election canvasses, 11 split precincts drawn with their majority side and stated on the card, roster scraped weekly from the county directory with the countywide-elected Chairman (gap lasalle-board-districts-stale records what remains); absorbed the former `commissioner` / `will-county-board` / `dupage-county-board` layers, old permalink ids aliased; Lake's members + contact + office address ride live on the county's own boundary GIS, with Chair/Vice-Chair tags from a weekly directory scrape (name-match guarded); Kane's GIS carries member names while a weekly scrape of the county's SharePoint directory list adds party/office phone/email + the countywide-elected Chair; Kendall's members + Chairman and McHenry's members + countywide-elected Chairman — each with contact + profile links — join from hand-verified rosters of each county's own directory — those two counties block all automated fetch incl. the Archive's crawler, so their weekly scrape attempts feed standing tracking issues until the block lifts) | NO HONEST ANALOG¹ | NO HONEST ANALOG (folded into `supervisor-district`) |
| County property-tax appeals board (elected) | SHIPPED `ccbr` (commissioner roster scraped weekly from the Board's own site) | NO HONEST ANALOG² | NO HONEST ANALOG⁵ |
| State high-court electoral district | SHIPPED `il-supreme-court` | SHIPPED `judicial-district` (NY Supreme is trial-level, elected by district) | NO HONEST ANALOG⁶ |
| Trial/civil-court sub-district | SHIPPED `judicial-subcircuit` (consolidated CountyDispatch: Cook 20 — live from the county GIS, cross-validated against the enacted ilsenateredistricting.com shapefile, with the Circuit Court's 6 municipal districts + courthouses as a card row — + Will 12th-Circuit 5 + DuPage 18th-Circuit 7 + Lake 19th-Circuit 12 + Kane 16th-Circuit 4 (pre-built from the enacted shapefile — the county's services are permission-locked) + McHenry 22nd-Circuit 4 (pre-built — the county publishes no subcircuit service) + Winnebago 17th-Circuit 2 + Madison 3rd-Circuit 4 + Sangamon 7th-Circuit 7 (the three 2026-07-28 entries, pre-built from the same enacted archive; their coverage is the subcircuit geometry itself, so each circuit's secondary counties — Boone; Bond; Greene/Jersey/Macoupin/Morgan/Scott — answer too), all PA 102-0693; the app ships all nine circuits the act covers, and Macoupin — a 7th-Circuit secondary county — is answered by the Sangamon entry; every other served county's circuit (Kendall + DeKalb's 23rd, LaSalle + Grundy's 13th, Kankakee's 21st, Livingston/McLean/Logan/Woodford's 11th, St. Clair's 20th, Ogle/Lee/Stephenson/Carroll's 15th, Whiteside + Rock Island + Henry's 14th) received NO subcircuits under the act — structurally n/a, the layer hides there) | SHIPPED `municipal-court` (28) | NO HONEST ANALOG⁶ |
| District Attorney (districted) | n/a (Cook State's Attorney is one countywide office) | SHIPPED `district-attorney` (5 borough DAs) | NO HONEST ANALOG (one citywide DA)⁷ |
| Borough president / by-county executive | n/a | SHIPPED `borough-president` | n/a |
| Community district / board (appointed, labeled so) | n/a | SHIPPED `community-district` | n/a |
| Elected school board (districted) | SHIPPED `school-board` (ERSB) | NO HONEST ANALOG³ | NO HONEST ANALOG (at-large board)⁴ |
| Parent-elected education council | n/a | SHIPPED `cec` | n/a |
| Elected regional transit board | NO HONEST ANALOG⁸ | NO HONEST ANALOG⁸ | SHIPPED `bart-director` (9 districts, BART's own ArcGIS + hand-verified roster) |
| Municipal governing body (surfaced on the municipality-identity card) | SHIPPED on `municipality` — **590 municipalities across thirty counties**, with 548 heads of government + 2,788 board members incl. 687 ward/district seats + clerks/treasurers + hall contact, joined by Census place GEOID (weekly CI). Depth varies honestly by county: **full governing body** Cook 129 / Will 30 / Madison 28 / Sangamon 26 / St. Clair 26 / LaSalle 25 / Tazewell 16 / Rock Island 15 / Peoria 15 / Washington 14 / Henry 14 / Livingston 14 / DeKalb 14 / Ogle 13 / Logan 11 / Stephenson 11 / Winnebago 11 / Grundy 9 / Mason 8 / Marshall 8 / De Witt 7 / Cass 5 / McLean 3 (its three ward-electing cities from their own pages — the county-wide source is a JS-locked Airtable interface), **head-level** McHenry 27 / Kane 23 / DuPage 23 / Whiteside 11 / Carroll 7 / Kendall 6, **contact-only** Lake 41 (publishes no names county-side). The 2026-08-01 tranche (Grundy, Livingston, Logan, McLean, Sangamon, Madison, St. Clair, Rock Island — the pass-6 build-ready ledger's municipal-officials half) shipped in one change; Madison + St. Clair share one source (the East-West Gateway POD) and Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city payloads fill what a county cannot — Will's ward cities + Joliet (per-seat contact), Skokie (trustee districts), Freeport (the whole city; Stephenson's source is a village directory that omits its own county seat). A municipality listed by two counties resolves by source depth, then county order. Chicago's citywide officers ride this card while its 50 ward seats stay `ward`'s answer. **Two of Washington's municipalities reach past the coverage ring, and that is correct rather than a mask defect.** Its Blue Book gives the full governing bodies of Centralia and Wamac, and both cities extend well beyond Washington County — Centralia into Clinton, Jefferson and Marion, Wamac into Clinton and Marion — so a resident in the Marion County part of Centralia now sees their whole city council while the out-of-scope wash greys their location out. That resembles the 2026-07-30 wash bug and is not it: `municipality` is a STATEWIDE layer keyed by Census place GEOID, so the set of layers answering in Marion is unchanged and only the quality of one statewide answer improved. Adding Marion or Clinton to `METRO_COUNTY_FIPS` would assert that a point ANYWHERE in them resolves county-specific data, which is false one step outside Centralia's limits. The test, recorded in `scripts/build_metro_outline.py`: a county joins the ring only if a point anywhere in it resolves a layer keyed to that COUNTY. **Mason is the fleet's first source that is a SPREADSHEET THE CLERK PUBLISHES**: its elections office shared the county's own "Mason County Directory" as a Google Sheet on 2026-08-04, readable by anyone with the link and exportable as CSV, which is what let a scraper replace a document that had previously needed a human. All nine municipalities come with their whole body, and Havana's eight aldermen carry their ward. NO ADDRESS AND NO HOME TOWN SHIPS FOR ANY MASON OFFICIAL — the directory prints home addresses throughout and one county board member's row reads "SECURED ADDRESS" (an address-confidentiality program), so the rule the board roster already set is asserted in the municipal scraper too: shipping the town for everyone else would make the protected row the one that stands out. **Marshall, Washington and De Witt are the fleet's ARCHIVED-DOCUMENT sources**: none of the three publishes a municipal list on the web, and each clerk sent a file on request (Marshall a 5-page elected-officers table on 2026-08-03, Washington its 40-page Blue Book the same day, De Witt its one-page "Village/City Officials" Word list on 2026-08-17 — all seven municipalities in full, its two commission-form cities' commissioners included, with appointed/acting officers marked so a card never implies they were elected, and a township-officials PDF archived alongside for provenance only), so all three are committed under `data/source/raw/` and re-parsed weekly as a PARSER guard rather than a freshness check — refreshing them means asking again. Washington's is the richest municipal source a clerk has given this project: 14 municipalities with every trustee's phone and, for 64 of them, an e-mail. An unsourced municipality keeps the identity-only card — Lee's 13 is the newest, at the rule-4 floor after all four sourced rungs were worked (`docs/EXPANSION_GUIDE.md` §2.4) | n/a (NYC's municipalities are the five boroughs — `borough-president`) | n/a (consolidated city-county) |
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
| Fire-service boundary | SHIPPED `fire-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + McHenry + Kendall suburban Fire *Protection* Districts; Cook from the Clerk's tax-agency tiling and DuPage/McHenry/Kendall name-only, Lake carries office contact, Kane names each district's chief + contact) · Kankakee 17 (identity-only — the county declares contact columns and populates none) · Madison 42 (the fleet's first contact-bearing fire entry: dept head 39/42, address 41/42, phone 41/42) · DeKalb 18 · Lee 22 (NG911 service areas) · Rock Island 17 (PRE-BUILT from the county's tax-agency tiling by build_rock_island_tax_districts.py — the parcel fabric excludes road right-of-way, so the raw layer was a lattice of 37-107 ft voids; the builder closes them at 75 ft, ships ground both neighbours' closings reach in neither, and the 60 ft snap still answers perimeter roads while refusing between-district seams) · Sangamon 29 FPDs + Springfield's corporate area (FireDistrictEtc L2 — 226 fragments grouped per district at load; the Springfield card states the city is served by its own Fire Department, not an FPD) · St. Clair 44 (CentralSquare/DATA/8, the county's CAD folder — identity-only, with the source's unstated taxing-vs-dispatch status carried as a caveat on every card) · Stephenson 15 (GEOREFERENCED from the county's own 2014 vector-PDF map — the fleet's second measured boundary, hydrography-fitted to 11.5 m median; 2014-vintage caveat on every card) · Macon 17 (named — recorded here 2026-08-04 with the matrix row it was omitted from at ship time) · Effingham 17 (the org's dissolved tiling, names matching the county's own fire-protection-district list; the zone literally named 'None' is excluded in the loader) · Hamilton 3 (the county's own layer; an unnamed ~0.4 km² sliver excluded — most of the county sits in no district, and the empty state says so) | SHIPPED `fire-battalion` (operational battalions, 49) | NO HONEST ANALOG — SFFD battalions exist but no boundary is published |
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
| Township / municipality | SHIPPED `township` · `municipality` (statewide IL; the municipality card names the municipal government — head of government, board, other elected officers, hall contact — for 575 municipalities across twenty-eight counties incl. Chicago's citywide officers, county-sourced and joined by place GEOID) | n/a | n/a |
| Park district | SHIPPED `park-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + Kendall; Cook's Clerk tiling includes the Chicago Park District — a Loop click resolves the city's own park taxing body; DuPage/Kendall name-only, Lake carries office contact, Kane names each district's board president + contact; McHenry has no entry — recorded gap, it publishes facilities not district boundaries) · Kankakee 4 (identity-only) · Madison 6 (identity-only) · DeKalb 6 · Rock Island 1 (Cordova — the county levies only one; pre-built with road voids closed, same builder as its fire/library siblings, and the 60 ft snap still answers its perimeter roads) · Macon 6 (recorded here 2026-08-04 with the matrix row it was omitted from at ship time) · Effingham 4 named districts (Effingham's drawn as two polygons) | n/a | n/a |
| Library taxing district | SHIPPED `library-district` (CountyDispatch, born consolidated: Cook's two Clerk tax-agency tilings — 59 Public Library Districts + 54 municipal Library Funds, incl. the City of Chicago Library Fund at a Loop click — + Will 27 w/ trustees + DuPage 32 name-only + Lake 15 w/ office contact + Kane 16 w/ board president + contact + McHenry 13 name-only + Kendall 9 name-only incl. the municipal Joliet/Yorkville city-library funds its tax tiling records, the Cook-style shape) · Kankakee 8 (identity-only) · Madison 18 (identity-only) · DeKalb 13 · Rock Island 9 named districts (PRE-BUILT with road voids closed by build_rock_island_tax_districts.py — raw, the parcel-derived tiling drew the road grid as void lattice and road clicks found nothing; the blank-named tenth source row, a stray byte-identical copy of the UNITED TWP HIGH 30 school polygon measured 2026-08-16 and not the un-districted remainder the first record guessed, is asserted and excluded at build time; the 60 ft snap still answers perimeter roads and refuses between-district seams) · Macon 10 (recorded here 2026-08-04 with the matrix row it was omitted from at ship time) · Effingham 1 (the St Elmo district reaching in from Fayette — the county's only one; everywhere else the empty state is the answer) | n/a — NYC's three library systems (NYPL/BPL/QPL) are nonprofit corporations, not taxing districts | n/a — SFPL is a city department |
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

## The ask ledger — what a clerk e-mail actually returns

**Recorded 2026-08-03, after seven asks produced seven usable answers in one day.**
This section exists because that success rate is not what the gap records predicted, and
the reason they were wrong is worth stating precisely.

### What the seven asks returned

| County | What was asked | What came back |
|---|---|---|
| Stark | "Is the Google map current?" | "The board districts and precincts are correct." **Five layers**, from one sentence |
| Ogle (GIS) | "Do the current precincts exist as map data?" | The shapefile, by return e-mail |
| Ogle (Clerk) | "How was Forreston 3 absorbed?" | "Forreston 1 and 2 became Forreston 1. Forreston 3 became 2." |
| Whiteside | "Which buildings are facilities 22 and 26?" | Both names, then both **street addresses** on a follow-up |
| Boone | "What are the fire district names?" | Names, **plus the caveat that made them unusable** — and the numbering that was usable |
| Marshall | "Do you publish a municipal list?" | A 5-page elected-officers table |
| Washington | "Do you publish a municipal list?" | A 40-page Blue Book, the richest municipal source in the fleet |

### The finding: "publishes no X" is not "cannot obtain X"

Ogle is the proof. Its gap record read *"The county publishes no precinct boundaries —
only a 51-page PDF map book and a polling-location dataset that is points only."* Every
word of that was **true**, and had been re-verified. The shapefile still arrived the day
someone asked for it, because a county that runs elections necessarily HAS precinct
geometry; publishing it on a website is a separate act it may simply never have had a
reason to perform.

So a blocker sentence of the form "the county publishes no …" is evidence about a
**website**, not about a **county**. Fifteen of the ninety gaps here assert exactly that,
and ten of those record no ask at all. Those ten are not blocked; they are unasked, and
the guidebook was quietly filing them as the same thing.

The same reframing applies to the tax-funded special districts: a county that levies for
a fire district necessarily knows its boundary, whatever its GIS portal shows.

### The three shapes that work, in order of hit rate

1. **One narrow factual question a clerk can answer from memory.** "Is this current?"
   "Which building is this?" "How was this precinct absorbed?" "Which district is this
   shape?" Four of today's seven were this, and all four came back same-day. It costs the
   clerk a sentence, which is why it works.
2. **"Do you publish X in any form — and if you don't, that's a useful answer too."**
   Both document sources today came from this, phrased with the explicit permission to
   say no. Neither document was findable by search; neither is on the county's website.
3. **Ask the GIS office for geometry, not the Clerk.** Ogle's shapefile came from the GIS
   Coordinator after the Clerk forwarded the request. The Clerk owns the *facts*; GIS owns
   the *files*. Sending a geometry request to the Clerk still works — it gets forwarded —
   but naming both offices is faster.

A fifth, learned from Stephenson on the same day: **ask the clerk what she has, not
whether the thing you want exists.** Jazmin Wingert's whole reply was one line — *"Here is
a link to the maps I have record of"* — pointing at her own Elections page. That page had
been reachable for the entire life of this project. It carries CITY OF FREEPORT PRECINCT
MAP and RURAL PRECINCT MAP, both vector PDFs of the current precincts, one navigation step
from the county-board district maps this repo already used. Two gap records had said flatly
that Stephenson published no current precinct boundaries, and a build script's header said
it twice. All of it was wrong, and no amount of re-checking the *board* page would ever
have caught it, because the miss was in which page was looked at.

That makes Stephenson a sharper version of the Ogle finding rather than a repeat of it.
Ogle showed that "publishes no X" can be false because the county never posted the file.
Stephenson shows it can be false because the county DID post the file and we did not find
it. The second failure mode is worse, because nothing in the gap record distinguishes the
two — both read as a settled fact about the county. The cheap corrective is the ask
itself: a clerk enumerating her own holdings costs her one sentence and audits the search
from the inside.

A sixth, and it is about what to do with the answer: **a cross-check between two of the
county's own documents is worth more than either alone.** Stephenson's precinct maps and
its board-district map draw the same sixteen Freeport polygons. Building the precincts
gave the project two independent georeferences of one boundary, and asserting they agree
caught a real defect on the first run — not in the older shipped file, as suspected, but
in the new build, which was filling interior holes the PDFs' own declared even-odd fill
rule says are holes. Neither map alone would have shown it.

A seventh, learned from Champaign the same day: **a refusal from the right desk is worth
collecting.** The Champaign clerk's elections division answered a boundary request with
"the shape files are maintained by the Champaign County GIS Consortium — you will need to
reach out to them." That does not unblock anything, but it converts a blocker inferred
from a licence page into one stated by the county's own election authority, and it retires
the "ask the clerk instead" branch for that county. A gap that records who said no, and
when, is a different object from one that records a guess about who would.

A fourth, learned from Boone: **invite the caveat.** Amy Ohlsen volunteered that she had
"just done a google search" for the fire district names, which is what stopped this
project from publishing them as a county record. An ask phrased so that "I'm not certain"
is a comfortable answer returns better data than one that pressures a source into
confidence.

### Candidates, highest expected return first

Contact details for every Illinois county clerk already ship in
`data/app/il-county-clerks.json` (name, office address, phone, e-mail; refreshed weekly by
`update-county-clerk-roster.yml`). Use that rather than a list copied into this document,
which would rot.

**Tier 1 — a single question, answerable from memory.** These are the Stark/Whiteside
shape and should go first.

| Gap | County | The question |
|---|---|---|
| `mason-precinct-vintage` | Mason | Are the 21 precincts unchanged since 2020? *(We already hold the shapes — this is a yes/no.)* |
| `ford-county-board-vintage` | Ford | Which board plan is in force, and how is Patton 3 split between districts 1 and 3? |
| `monroe-fire-district-names` | Monroe | What do the fire district abbreviations stand for? *(Shapes already published.)* |
| `macon-county-board-labels` | Macon | Which district is which, for the five unlabelled shapes? |
| `tazewell-precinct-polling` | Tazewell | What are building IDs 43, 50 and 54? *(The Whiteside question, verbatim.)* |
| `dekalb-precinct-codes` | DeKalb | Is there a key pairing each precinct code with its township name? |
| `randolph-precinct-polling` | Randolph | Which polling place serves each precinct? |
| `st-clair-precinct-polling-places` | St. Clair | Same, one per precinct |
| `dakota-village-president` · `dekalb-hinckley-board` · `winnebago-village-heads` | Stephenson · DeKalb · Winnebago | Who currently holds this one seat? |
| `wenona-two-clerks-disagree` | Marshall / LaSalle | Whose council list is current? **Asked 2026-08-03.** |

**Tier 2 — "do you publish it in any form?"** The Marshall/Washington shape. Every one of
these is a municipal-officials or roster gap where the county may hold a document.

`kankakee-municipal-officials` · `lake-municipal-names` · `lee-municipal-officials` ·
`whiteside-municipal-officials` · `mason-roster-is-a-scan` (ask for the board list as text
or a spreadsheet rather than a scan) · `adams-county-board-roster` and
`quincy-ward-officeholders` (both blocked at the website, neither asked directly).

**Tier 3 — geometry, addressed to GIS.** The Ogle shape, and the largest tier by count.
Precinct boundaries: Brown, Calhoun, Henry, Livingston, Marshall, Pike, Putnam,
Washington. (Stephenson left this list on 2026-08-03: its 36 precincts now ship, traced
from the Clerk's own maps. The ask survives in a narrower form — the same lines as DATA,
which the Clerk has directed to the county GIS office.) Board districts: Bureau, Christian,
Clinton, Fayette, Knox, Menard, Mercer, Montgomery, Macoupin, Jo Daviess (whose mapping
department *sells* the data, so it demonstrably exists). Special districts, where the
county levies the tax and therefore holds the boundary: Boone, Carroll, Grundy,
Livingston, Logan, Macoupin, McHenry, McLean, Ogle, LaSalle, Randolph, Sangamon,
St. Clair, Stephenson, Whiteside, Winnebago, Woodford. City wards, addressed to the city:
the eight in `pass9-ward-seats-without-maps`, plus LaSalle, Macoupin, Carroll, Ogle,
Morris, Momence, Park City, Plano.

**Tier 4 — the five never contacted at all.** `pass10-frontier-unasked` (Hancock, Jackson,
Jefferson, Marion, Perry, Vermilion, Warren, Fulton, Henderson) says so in its own text:
*"Asking the five clerks is the next move, not more searching."* Two of them —
`henderson-county-website` and `vermilion-county-website` — are asking whether the county
has a website at all, which is the cheapest question on this page.

### Pass 11 (2026-08-03): the search lever is spent

Fulton shipped from this pass — the county the pass-10 sweep had already marked
build-ready, hidden behind non-zero layer ids. After that, the same pass went
looking for another and **found none**, which is worth recording as a result
rather than as an absence of work.

**What was probed.** All 21 counties that appear in a gap record but sit outside
the coverage ring: Bureau, Champaign, Christian, Clinton, Fayette, Ford, Hancock,
Henderson, Jackson, Jefferson, Jo Daviess, Knox, Macon, Marion, Menard, Mercer,
Montgomery, Perry, Piatt, Vermilion, Warren. Two methods, both applied to all 21:

  * **Hostname probing** — ten naming patterns (`gis.<county>countyil.gov`,
    `maps.<county>county.org`, `gis.co.<county>.il.us`, …) against both
    `/arcgis/rest/services` and `/server/rest/services`. Every layer id of every
    hit was enumerated rather than assuming `0`, which is the trap that hid
    Fulton and would otherwise have hidden anything shaped like it.
  * **ArcGIS Online catalogue search**, per county, for precinct and board
    district services, filtered to items whose title, owner or snippet actually
    names the county.

**What came back.** One hostname hit, `maps.mercercounty.org`, **correctly
rejected**: its extent resolves to roughly -74.9°, 40.1°, which is Mercer County
NEW JERSEY. Checking the extent rather than trusting the name is the whole
lesson of that one. Knox returned real services, all of them **city-scoped** —
Galesburg's own account publishes Galesburg precincts, Galesburg council wards
and "Knox County Board Districts *in the City of Galesburg*", but nothing
countywide. Nothing else returned anything usable.

**So the frontier is ask-gated, not search-gated.** That is the ask ledger's
central claim, now with a measured negative to sit beside the seven positives:
searching 21 counties two ways produced zero builds, while asking seven counties
produced seven answers on the same day. The remaining counties do not have
findable data that we have failed to find; they have data that is not published,
which is a different problem with a different lever.

Two counties are excluded from that conclusion for a reason that is not about
searching at all: **Champaign and Piatt** publish complete, current maps through
the Champaign County GIS Consortium and we are **not licensed to republish
them**. Easy to fetch is not the same as allowed, and no amount of asking a
clerk changes a licence.

### 2026-08-04: the ring stopped ordering the asks

The day after pass 11, contiguity was retired as a shipping gate (EXPANSION_GUIDE
§2.5.1; the policy note in `scripts/build_metro_outline.py` records the full
reasoning — the short form is that the outline already carried two holes, so
adjacency had stopped predicting serveability, and an ask-gated frontier makes a
ring-adjacency rule refuse wins rather than order work). For this ledger it
changes exactly one thing: **an ask's expected return no longer discounts by
distance from the frontier.** The 29 counties with no gap record at all were
unresearched mostly because research passes walked the frontier; they are now
ordinary candidates for the Tier-4 cheapest question, and a county that answers
with a full GIS ships as the outline's first island (first-island checklist,
§2.5.1) instead of waiting for a bridge. What a licence forbids still stands
(Champaign, Piatt), and what the county-keyed test forbids still stands — a city
cannot carry its unserved county (`galesburg-wards-outside-the-ring`, decided
the same day).

### Pass 13 (2026-08-04): the detached sweep — and its Fulton

The retirement's first test, run the same day: all 29 never-researched counties
— the deep south plus the Moultrie/Shelby/Coles belt — probed with the pass-11
method (ten hostname patterns × two service roots, every layer id enumerated;
per-county ArcGIS Online catalogue search) plus a website-reachability sweep
and a homepage-link crawl of every site that answered.

**What came back, in pass-11's terms: zero hostname hits in 29 counties, and
one catalogue hit that was Clay County MISSOURI** (voteclaycountymo.gov's
election service, rejected by owner and layer names — Mercer New Jersey's
lesson, reapplied). Ten counties have real websites (Douglas, Edgar via a
.gov→.com redirect, Effingham, Franklin, Hamilton, Hardin, Jasper — shared
with the City of Newton — Massac, Moultrie, Wayne); two more refuse all
automation in the Knox posture (Union, Williamson); Pulaski's domain resolves
to an address this environment's proxy refuses, so it went unseen; the rest
answered under none of the probed patterns. Three name-decoys recorded so
nobody re-walks them: cumberlandcounty.org is Maine, salinecounty.org is
Arkansas, jaspercounty.org and hamiltoncounty.org are Missouri and Iowa. (A
fourth joined on 5 Aug, and it is the sharpest: in.gov/counties/wabash is
Wabash County INDIANA, whose board — like Illinois's — is three commissioners,
so its roster would look correct on the wrong county's card. See
`wabash-county-board`.)

**The exception found the same way Fulton was — by refusing the conventional
probe's verdict.** Effingham's county site links Instant Apps on an ArcGIS
Online org (effinghamcoil.maps.arcgis.com, "EFFINGHAM COUNTY GIS") that
keyword search cannot see, because no item title names the county. Enumerating
the org's 39 public items instead of searching for them found
`ElectionGeography_public` — the same CentralSquare family Tazewell, Whiteside,
Iroquois and Macon already ship from — with **9 labelled County Board districts
(A–I) carrying member name, party and e-mail on the features themselves**, 38
voting precincts joined to 24 polling locations, and fire (18) / park (5) /
library / school tilings, plus countywide officers with contacts. That is more
than several SERVED counties publish, and it makes Effingham the first-island
candidate (Backlog). The method lesson for this ledger: **when a county site
links any *.maps.arcgis.com app, enumerate that org's public items — catalogue
search misses orgs whose item titles don't name the county.**

One roster fact worth its own line: Franklin County's board members page groups
its members under Districts 1–3, so that board is districted and its roster is
already published — the ask there is geometry only.

The 29 records this pass added follow the post-Ogle discipline: each states
what the probe could see, and none claims the county publishes nothing — ten of
them could not even be looked at. All 29 are Tier-4 candidates; clerk contacts
ship in `data/app/il-county-clerks.json`.

### 2026-08-04, evening: the mailbox is the second ledger

Drafting the pass-14 asks surfaced a recording failure in this ledger itself:
**seven boundary asks had already been sent (1–3 Aug) and never recorded here**
— Bureau, Jo Daviess (to the GIS desk, the right one), Mercer (the
broken-Document-Section angle) on the 1st; Ford (this ledger's own Tier-1
question, verbatim), Piatt, Menard and the Champaign referral follow-up on the
3rd. The ledger records what someone remembered to write down; the mailbox
records what happened. **The corrective is now procedure: cross-reference the
mailbox before drafting or recording an ask** — the pass-14 drafts were rebuilt
against it, which converted five would-be duplicate asks into status rows.

What the mailbox also held, none of it recorded anywhere:

- **Menard ANSWERED (4 Aug), a Tier-3 success in motion**: Clerk Gum looped in
  Supervisor of Assessments Dawn Kelton, who has requested the commissioner-
  district shapefile from Beacon and will forward it. When it lands, Menard
  builds — and the coverage outline's first HOLE closes.
- **Mason's municipal-officials ask ANSWERED (4 Aug)**: Election Coordinator
  Mariah Kolves added the project to the county's Google Doc directory; the
  share notification arrives separately. (`mason-roster-is-a-scan`'s successor
  question, answered by access rather than by file.)
- **A July seal-permission campaign** (18–21 Jul) had already reached most
  frontier clerks — so most pass-14 drafts open as follow-ups, the shape the
  Mason/Marshall/Stark follow-ups proved. Its three substantive replies each
  carried intelligence: Johnson's Clerk confirmed the county has NO website
  (her words — the pass-13 finding, county-stated); Wabash's Clerk referred in
  passing to the "Wabash County Board of Commissioners" (commission-form
  language, certified-document check still owed); Jo Daviess has no seal PNG.
- **Two address facts the weekly clerk roster needs a human look at**: White's
  published address (clerk@whitecounty-il.gov) hard-bounced permanently on
  31 Jul — the roster ships a dead e-mail; and Marshall's Clerk states her
  e-mail changed ("please update your records") even though the old address
  still delivered.

### Pass 14's first fruit (2026-08-05): Hamilton, asked and answered in four minutes

The 42 reconciled asks went out on the morning of 2026-08-05. Hamilton County
answered FIRST — Clerk & Recorder Heather Bowman, at 9:08 a.m., four minutes
after the 9:04 send: *"Our County Board is elected at large. For the map, you
can use our County's GIS map and turn on the voter precinct layer."* One reply
settled the board form (from the election authority herself, in writing), and
pointed at a GIS the pass-13 probe had missed for exactly the reason it missed
Effingham's — a vendor-hosted AGO org (Magnasoft) whose item titles never name
the county. **Hamilton was BUILT the same day**: the 45th dispatched county and
the outline's second island — precincts (17, one unnamed — asked back) and
fire (3 named) as dispatch entries, the five-member at-large board on the
County card via the commissioners roster, scraped from the county's brand-new
website (live that same morning, mid-migration by the Clerk's own note).

Ledger arithmetic so far: 43 asks sent across two days, two counties BUILT
from answers (Menard pending its Beacon shapefile would make a third), zero
refusals. The Tier-D form-first shape works exactly as designed — one
memory-answerable question, and the at-large answer collapses the geometry
ask to nothing.

### 2026-08-05: the bounce guard, and what a check cannot see

The mailbox reconciliation turned up a quiet honesty failure: the weekly clerk
roster shipped **White County's published address, which had hard-bounced
permanently on 31 Jul** after five days of retries. The County card was
rendering it as a mailto link — telling a White County resident "write to your
clerk here" when nothing they sent could arrive. Every existing gate was
green, because the address parses, the roster count is right, and ISBE still
publishes it.

`build_county_clerk_roster.py` now carries a `KNOWN_UNDELIVERABLE` list: an
address proven undeliverable by an actual bounce is dropped from the shipped
file, while the clerk's NAME, PHONE and ADDRESS still ship — the card keeps
every route that works and stops offering the one that doesn't. No app change
was needed; the card already renders the e-mail row only when the field is
present. When ISBE publishes a different address the list stops matching and
the build prints a RETIRE line, so the entry cannot quietly outlive the fact
it records.

**The part worth remembering is what the cheap check could NOT do.** Before
writing the list, the obvious guard — verify the domain's mail route in DNS —
was measured against this exact failure: `whitecounty-il.gov` HAS a valid MX
record, and that MX host resolves to a live A record. Every DNS-visible signal
was healthy; the failure was at SMTP delivery time. A DNS check would have
passed White and shipped the dead address anyway. It ships regardless
(`--verify-mx`, run weekly, reported to the job summary and the PR body) —
because it catches a DIFFERENT failure, a domain with no mail route at all —
but it is explicitly not the guard for this class, and the code says so. Only
a real send catches a real bounce, which is why every entry's evidence is a
bounce and never an inference.

Live measurement, same day: all 100 shipped clerk addresses' domains have live
mail routes. Marshall's Clerk separately asked that her address be updated —
the roster already carries the one she now sends from, so nothing to change,
recorded here so the next reader does not go looking.

### 2026-08-05: the state has been hosting precinct maps all along

Chasing Hamilton's polling places turned up something bigger than Hamilton.
Clerk Bowman's second reply linked a precinct map — not on the county's site,
but on the **State Board of Elections'** at
`elections.il.gov/PrecinctMaps/<County>/`. That directory is not a Hamilton
courtesy: probing all 102 county names found **98 with at least one map file**,
served as open IIS directory listings, requiring nothing of anybody.

**Sized before it was believed.** A fourteen-county sample (the frontier
counties with open asks, plus controls) was downloaded and opened: **3 of 14
are vector PDFs with an extractable text layer** — Knox, Menard and Williamson
— and the rest are scans, which are pictures of maps and no more usable than
the ones the gap records already describe. So this is a real lead worth a
research pass, not a statewide unlock: on that rate perhaps twenty counties
statewide carry a machine-readable map here.

**And for the two counties whose asks are most specific, it CONFIRMS the gap
records rather than closing them** — which is why it was checked before being
celebrated. Knox's `PrecinctsByCountyBoard.pdf` is vector and readable, and its
own title says **"Knox County Board Districts 2011"**: the pre-redistricting
content `knox-county-board-districts` already records as provably stale, now
verified from the file itself. Menard's `Menard County Commissioner Map.pdf`
extracts ZERO words — the flat image `menard-commissioner-districts` describes.
Both records were right, and the route is closed rather than opened; Menard's
live route remains the Beacon shapefile its Assessor is pulling.

The standing lesson for this ledger: **a source can be public, free, complete
and STILL not be data.** The discriminator is one download and one text
extraction, which is cheap enough that no future pass should record a PDF
source without running it.

### 2026-08-05, later: two more answers, and the hostname blind spot

The campaign's second and third replies landed within hours, and neither
produced a build — both produced something this ledger values as much, which is
a record that is now true.

**Wabash: the form, from the election authority.** County Clerk & Recorder
Janet L. Will wrote back: *"Wabash County is a commissioner form of government,
not township. We have three commissioners elected at large. One commissioner is
elected each General Election for a six year term."* That closes the geometry
question permanently — there are no districts, and none should ever be drawn —
and converts Wabash into a County-card county needing only three NAMES, which
her reply did not include. The July seal-reply clue ("Board of Commissioners")
was right, and was correctly recorded as a clue rather than a fact until she
confirmed it.

**Vermilion: the website, by asking — and the reason searching could not
work.** Chief Deputy Clerk Carrie Wilson named the county's site:
**vercounty.org**, with its voter maps at `/county-clerk/voter-maps/`. The gap
record had predicted exactly this outcome, citing McDonough, and the reason
both counties defeated the hostname ladder is worth stating as a rule:
**"ver" is an ABBREVIATION of Vermilion.** Every pattern the probes generate is
built from the county's own name — `vermilioncountyil.gov`,
`vermilioncounty.org`, `co.vermilion.il.us` — and none can reach a site whose
name is a contraction. That is a permanent blind spot in hostname probing, not
a gap in the probing effort, and the only instrument that closes it is a
question. Two counties have now proved it (McDonough's `mcg.mcdonough.il.us`,
Vermilion's `vercounty.org`).

A caveat kept deliberately: neither vercounty.org nor the Internet Archive is
reachable from this project's network, so the voter-maps page's CONTENTS remain
unmeasured. The address is recorded as a fact; what it holds is not yet a
finding, and the PDF lesson from earlier today applies to it in full. *(That
caveat was answered a few hours later — see "a refusal is a finding", below.)*

### The §2.5-step-2 document comes from the COUNTY, never the state

Worth pinning, because the rule that governs every county build says to settle
a board's form "from a certified election document" without saying who holds
one. Checked 5 Aug 2026 against the state itself: **ISBE publishes results only
for federal, statewide, legislative and judicial offices**, and says so on its
own results page — *"Unofficial local results are not reported to the State
Board of Elections or posted to the Agency's website... may be obtained by
accessing the local jurisdiction's website."* Odd-year local elections are
canvassed by the local election authority outright.

So for county board and commissioner races there is no state-level canvass to
fall back on, ever. The certified document lives with the county clerk, which
means §2.5 step 2 is always an ASK (or a county-site fetch) and never a
statewide scrape — the same reason `il-county-clerks.json` comes from ISBE
while every county's BOARD does not. Two routes that look promising and are
not: the Secretary of State's IRAD depository pages (historical archives —
Wabash's stops at an 1857 fire) and ISBE's results downloads.

### "Blocked" and "absent" are different findings, and the probe conflated them

Wabash forced a correction worth generalising. Its record said the county's
domain "refuses connections from this project's network" — the
Adams/Knox/DeKalb shape, where a site serves humans and turns away servers.
Measured 5 Aug 2026, that was wrong: `wabashcounty.illinois.gov` resolves (A
157.185.73.189, reverse-DNS at a southern-Illinois ISP) and carries mail
(Rackspace MX — which is why the Clerk's replies arrive), but **port 80
answers 503 on every attempt, 443 resets, and the `www` host is NXDOMAIN.** A
mail domain with no web server behind it. Independently, an ordinary web
search returns no Wabash County site at all.

The pass-13 probe recorded this as `conn-fail`, the same bucket as a hostname
that never existed, and the write-up then reached for the familiar explanation.
**The two need separating, because they imply opposite next moves:** a blocked
site is worth retrying from a browser, a phone, or the Archive; an absent site
is worth nothing at all, forever, and its county's only channel is its clerk.
Johnson County's Clerk stated the absent case in her own words on 21 Jul
("We don't have a website to point back to"); Wabash is the second, and the
first established by measurement rather than testimony.

The cheap discriminator, for the next sweep: a domain that resolves AND has MX
AND refuses only HTTP is a county with e-mail and no website — which is a
publishable fact about that county, not a failure of the probe.

### 2026-08-05, evening: a refusal is a finding, and Vermilion supplied one

The pass-14 campaign's fourth reply closed a question instead of opening a
county, and that is the outcome this section exists to make respectable.

Asked whether the voter maps her office publishes exist as data, Vermilion's
Chief Deputy Clerk and Supervisor of Elections **Carrie Wilson** answered the
same evening: *"Those are the only maps we offer, our county does not have
shapefiles or GIS layers for precinct look ups. There is a precinct finder on
the Illinois State Board of Elections site voters may utilize or they may call
our office."*

**Why that is worth as much as a shapefile would have been.** Before it,
`vermilion-county-website` held an INFERRED blocker — the site is unreachable
from here, so the format was unknown, so the record had to say "unmeasured" and
the county stayed in the queue as something to go back to. After it, the
blocker is STATED, by the office that would hold the file if it existed. The
county's own publications are now a closed route, permanently, and the record
says so instead of inviting a fifth pass over the same ground. **A stated no
from the right desk retires a line of inquiry; an unmeasured maybe never
does.** Johnson ("we don't have a website"), Wabash ("three commissioners
elected at large") and now Vermilion are the same shape.

**Read exactly, not generously.** Her sentence is explicit about PRECINCTS and
covers board districts by implication — *"the only maps we offer"* is a claim
about her office's inventory, not about every desk in the county. So the record
was written to that boundary: the Clerk is closed, a county GIS or assessor's
office (if Vermilion has one) is a different desk and was never asked, and that
is what `wanted` now names. Over-reading a reply into "Vermilion has no GIS
anywhere" would have been the easy version and would have been unsourced.

**The lookup she named was measured before it was recorded.** Following the
standing rule that a source is not data until someone opens it,
`ova.elections.il.gov/PollingPlaceLookup.aspx` was fetched and driven: it is a
per-address ASP.NET form — five-digit zip, then a street picked from that zip's
fixed dropdown (616 streets for Danville's 61832), then a house number — that
answers one voter at a time. No boundary, no download, no bulk anything. It is
a good thing to hand a resident and worth nothing to a boundary layer, which is
the same discriminator the ISBE PrecinctMaps pass applied this morning. Recorded
as a non-lead **so that it is never re-investigated as a lead.**

### 2026-08-05, evening: the phantom precinct was a duplicate row, and it was shadowing a real one

Hamilton's Clerk answered a third time, and the answer exposed a bug that had
been live since the county shipped that morning. Worth recording in full,
because the failure was mine and the instrument that caught it was a clerk
reading her own county back to me.

**What was shipped, and what was actually there.** The build recorded
`Voter_Precincts_Hamilton` as "17 features, sixteen named; OBJECTID 12 carries
no name, rendered Unknown" and opened `hamilton-unnamed-precinct` for it. That
description was wrong in the way that matters. Measured 5 Aug: **OBJECTID 12 is
a duplicate of OBJECTID 13, DAHLGREN 1** — same bounding box to five decimals,
same area (25.3 sq mi), and of 4,000 points sampled in their shared box, 3,379
fall inside both and **zero** inside only one. It is one polygon stored twice,
the second copy nameless. And because it sorts first, `findFeatureContaining`
returned it first: **every point in Dahlgren 1 answered "Unknown."** The county
had a precinct whose voters were told the app didn't know where they were.

The fix is one clause — the loader now takes `Precinct_Name IS NOT NULL`, the
same shape already used for the county's unnamed fire sliver — and Hamilton
ships sixteen precincts, which is what both the county's own FY 2017 map and
its Clerk say it has. `hamilton-unnamed-precinct` is deleted rather than
rewritten: there was never a seventeenth precinct to name.

**A badly described ask gets a plausible wrong answer.** The question sent to
Clerk Bowman called the unnamed shape "one full-sized area **in the middle of
the county**." It is not in the middle; it is on the western edge, stacked on
Dahlgren 1. Reasoning from that, she offered a reasonable hypothesis — *"It
looks to me that the assessor has included the City Wards in the middle instead
of the voting precincts... We have 3 City Wards"* — and it is wrong, but only
because the premise was. The layer's middle carries MCLEANSBORO 1–4, four
precincts, exactly matching her own description of how McLeansboro township is
split. **The lesson is not "verify what clerks tell you."** It is that a
question containing an unverified claim spends the answerer's time on the
claim; describing the shape by its neighbour ("a nameless copy of Dahlgren 1")
would have cost the same sentence and returned the actual answer.

**What the map can and cannot settle.** The FY 2017 PDF is vector and yields all
13 polling places with names and street addresses. Currency and structure came
back confirmed. The pairing did not, and the attempt is recorded because the
negative result is reusable: an affine fit from 14 precinct labels to their
polygon centroids georeferences the sheet to a median 0.35 mi, which puts every
marker inside a precinct and lands 10 of 12 rural assignments consistently — but
both Dahlgren markers fall in DAHLGREN 2, and geocoding the McLeansboro gym
independently puts it in MCLEANSBORO 3 where the sheet's placement said
MCLEANSBORO 4. **A polling-place map shows where a location IS, not which
precinct it SERVES**, and 0.3-mile instruments cannot bridge that. The ledger's
existing phrasing — "containment on a page is not evidence" — was right, and is
now measured rather than asserted.

### 2026-08-05: "contact GIS" turned out to mean a consortium that sells it

Stephenson's Clerk answered the follow-up, and the answer is the most useful
kind of no this ledger collects: it names a holder and a price where two gap
records had only a vague second desk.

**Who "GIS" is.** Both `stephenson-freeport-precincts` and
`stephenson-park-library-districts` ended with the same sentence — the Clerk
holds only the election maps and directs everything else to the county GIS
office. Asked who that is, Clerk Wingert sent the county's Maps & GIS page.
Its entire content is a link to **WinGIS** (wingis.org), the regional
consortium that holds the county's layers. So the second desk is not a county
office at all, which is why no amount of probing county hostnames would have
found it.

**And what WinGIS's terms are, read rather than assumed.** Digital data must be
*purchased*: submit a Data Request, get a quote within 24 hours, and have a
signed Data License Agreement on file. Subscription membership is open to
"non-profit organizations & commercial businesses only" and grants access
"through a custom mapping interface through the Internet only." Measured, not
inferred from that prose: the Stephenson public viewer's own backing service,
`maps.wingis.org/public/rest/services/StephensonPublicPropertySearch/MapServer`,
answers an unauthenticated request with **"Token Required."**

**Why that is progress.** "Nobody has it" and "somebody has it and charges for
it" are different gaps and deserve different records. Stephenson's precincts
are not missing — they exist, in a consortium's hands, with a quoting process.
The records now say so, and they name the routes that stay free: the county
releasing its own election geography directly (it is the county's, not
WinGIS's), or a public Stephenson service equivalent to the open Winnebago ones.

**A free lead fell out of the same probe.** On the identical host, two services
answer without a token and are wide open: `WardsAndDistricts` (Winnebago County
Board, **WinCo Voting Precincts**, WinCo Political Townships, Rockford/Loves
Park/Machesney Park wards) and `ElectedOfficials` (per-municipality officeholder
layers plus board chairman and districts). Winnebago is already a served county
and ships **no precinct layer** — `WardsAndDistricts` layer 7 is exactly that
layer, free and public. Recorded here rather than built today, but it is a
build, not a research question.

**The reply also settled a seat, and the settlement had to be built carefully.**
Asked who Dakota's village president is — the county directory shows the
village none — Clerk Wingert named Jonathon Riley. The directory prints him as
a **Trustee**. That is not a blank to fill but two sourced claims in conflict,
so the scraper grew `CLERK_STATED_OFFICES`, which ships the election
authority's answer, records the page's, and **pins the office the page printed
when the entry was written** — change that cell in any direction and the entry
stops applying and prints a RETIRE line. The corroboration is structural: an
Illinois village board is a president plus six trustees, and the directory's
Dakota is six trustees, a clerk, a treasurer, no president, and one row with an
empty office cell. Riley as president makes it lawful. **What was deliberately
NOT done:** that same arithmetic makes the blank row obviously the sixth
trustee, and it stays blank. One sourced correction does not license a second
unsourced one.

> **Superseded the next day, and by the best possible route** — the county
> republished the Dakota table, the entry stopped matching, and the RETIRE line
> fired. See "2026-08-06: the ask fixed the SOURCE" below. Everything above is
> kept because the mechanism is still in the file for the next conflict.

### 2026-08-06: the campaign's best morning — a shapefile, and a county that will never need one

Two replies, and between them they cover both ways an ask can succeed.

**Henry: the file arrived, from a desk the ask never named.** The 1 Aug request
went to Clerk & Recorder Barbara Link and guessed, in writing, that the data
might live with Sidwell. It didn't. She forwarded it inside the county, and on
6 Aug **Bruce Lang of Henry County GIS** replied with
`HenryCountyIL_VR_2026-08-13.zip` attached: *"The data is attached in shapefile
formats. The file names should be self-explanatory, but I'll answer any
questions."*

Worth being precise about what that does and does not change. It does not
change the county's PUBLISHED position at all — the elections page still
carries only the November 2021 township pictures, the county's mapping system
still holds parcels and townships and no precincts, and a re-probe on 6 Aug
found no public ArcGIS under any `henrycty.com` hostname. `henry-county-precincts`
had said *"no usable boundaries are published anywhere"*, and that sentence is
STILL TRUE. The boundaries exist anyway, because somebody asked. That is the
Ogle shape exactly, and it is the reason this ledger exists.

**The record stayed open until the file had been read — and then it shipped the
same day.** A shapefile in an inbox is not a layer, so the record sat at
answered-not-built until the archive was opened. What it held: five shapefiles
— `Precincts`, `Wards`, and the 2022 Congressional / House / Senate districts.
**52 precincts**, each carrying the county's own readable name ("Geneseo 1")
alongside a four-digit code, which is the difference between a card a resident
recognises and DeKalb's bare "SG 01".

Four checks before anything drew, because a file from an inbox has no publisher
to blame if it is wrong:

  * **The reprojection proved itself.** NAD83 / Illinois West in survey feet
    (EPSG:3436), reprojected to degrees — and the rebuilt extent lands within
    **0.00004°** of the county outline the app already ships. A wrong EPSG
    misses by hundreds of miles, so this is a check and not a coincidence.
  * **The tiling holds.** 3,000 random points inside the county outline:
    **2,999 in exactly one precinct, zero in two.** The single miss sits
    **4.4 m** from a precinct edge — the TIGER outline and the county's own
    StatePlane linework disagreeing at the border, not a hole.
  * **99.95% coverage, 0.0000% worst pair overlap**, both asserted in the
    builder rather than eyeballed.
  * **And the county's data had one real defect, which the build caught.**
    Geneseo 6 carries three rings, one of them a 4-point sliver of ~0.01 m².
    The hole-nesting rule this project has used since McDonough — "a ring
    inside another ring is a hole" — answered YES BOTH WAYS on the real pair,
    because the outer ring's own representative point falls inside its hole. So
    both were classified as holes, no outer survived, and the precinct built as
    EMPTY. The rule now also compares area — a ring is a hole only when a
    strictly LARGER ring contains it, which cannot be mutual — and the sliver
    is dropped with a printed note. Ogle's data never triggered it; Henry's did.

Live in the browser at two points in different townships: Geneseo → "Precinct
Geneseo 4", code 0804, County Board District 1; Kewanee → "Precinct Burns 1",
code 1901, District 2. The board district is a spatial join, so it is the
geometry answering rather than a name being parsed.

**What did NOT ship, deliberately.** The archive's `Wards` layer is real and
verified — Galva 3, Colona 4, Geneseo 4 — and **no gap record asks for it**.
Recorded here as available rather than shipped blind, so the decision to add
Henry's city wards is made against the ward layer's own conventions instead of
being smuggled in on a precinct build. The 2022 legislative three are already
shipped statewide from TIGERweb; a county-local copy would be a second answer
to a question that already has one.

**The half that is still open** is the half the reply did not address: which
precinct votes where. That was in the original ask, it went to a mapping office
rather than to the Clerk, and a polling list is a Clerk's record — so it is not
a refusal. `henry-county-precincts` is retired and replaced by the narrower
`henry-precinct-polling`, and the county's own four-digit precinct code is the
key any list can be joined on.

**Edwards: the answer that closes a county rather than opening one.** County
Clerk & Recorder Melanie Knight, the next morning: *"the county board is
elected countywide (at large.) We are a commission county. Our voting district
boundaries currently exist on paper."*

Two facts in three lines, and both are terminal. An at-large commission county
has **no board districts to draw, ever** — it moves to the §1.5 County-card
tier, where three commissioners ride the County card and no geometry, coverage
function or toggle is ever written. And the precincts are paper, said plainly,
so no precinct layer will come from this county either. What is left is three
names.

**And the names are blocked by an absence, not a refusal — measured, not
assumed.** `edwardscounty.illinois.gov` answers NOERROR with **no A record**;
`www.edwardscounty.illinois.gov` is NXDOMAIN. The domain carries mail (the
Clerk writes from it) and hosts no web. No scraper can ever exist for this
county, so the roster has to be asked for, exactly as Wabash's is. **Edwards is
the third county measured into this state** — Johnson said it in words, Wabash
and Edwards were measured — and the pattern is now common enough to expect: a
small Illinois county may have e-mail and no website at all, and the pass-13
probe's `conn-fail` bucket cannot tell that apart from a block.

### 2026-08-06, afternoon: both counties answered the follow-up, and one drew a line

**Henry: the currency question, answered by the person who could answer it —
and only that one.** Asked whether the file's 2026-08-13 name is an effective
date, Bruce Lang: *"I can only speak to the 2026-08-13 date. This is the date
as to how it currently stands. No changes have been made to the data for a long
time - over a year."* So the date is an as-of stamp on stable data, not a
future redistricting boundary, which is what the shipped layer needed to know.

Then the sentence worth keeping: *"The other questions are for Barb to
answer/supply."* He declined the attribution and polling-table questions rather
than guessing at them — a GIS office saying where its authority ends. That is
the same instinct this ledger tries to hold itself to, and it means **two**
things now sit with Clerk Link, not one: the polling assignment, and permission
to publish. The boundaries shipped the day they arrived because the data is a
public record supplied on request and the app redistributes no raw file — but
permission was ASKED and explicitly not answered, so it is pending, and
`henry-precinct-polling` now says so rather than letting it be assumed.

**Edwards: the negative got stated as well as measured, and the names were
sent.** Asked whether the county uses some other web address, Clerk Knight:
*"The county does not currently have a website."* Edwards is now the
best-evidenced of the three counties in this state — Johnson was stated only,
Wabash measured only, Edwards is both.

The same reply attached `Commissioners names-addresses 2025.doc`. **Nothing is
built from it yet and no name from it appears anywhere in this project**, for
the same reason Henry's shapefile sat unread for a few hours: a file in an
inbox is not a source until someone opens it. When it lands, Edwards ships as a
County-card county — a roster row in `il-county-commissioners.json`, no dispatch
entry, no coverage function, no toggle, no ring change.

**One pattern across the two.** Both counties answered a follow-up within the
hour, and in both cases the follow-up was worth sending precisely because the
first reply left something ambiguous — a file name that might have been an
effective date, a domain that might have been blocked rather than absent.
Neither ambiguity would have been visible without asking, and neither answer
could have been guessed.

**And Edwards shipped the same afternoon — the 56th county, the THIRD island,
and the first to join on the at-large tier alone.** The document held three
commissioners: Duane Lear (Chairman, elected 2020), Davis Messman (2022) and
Matthew R. St.Ledger (2024) — one seat per general election, which is the
commission form's staggered six-year cycle showing in the dates. They ride the
County card via `il-county-commissioners.json`: no dispatch entry, no coverage
function, no toggle, no layer. `edwards-county-board` is retired.

**What was left out of the roster, and why.** The Clerk's letterhead gives each
commissioner a HOME address and a personal phone, two of them marked "(h)" and
"(c)". None of that ships — the same call every municipal source here makes,
because a card must not publish a private home. What ships is the name, the
office, and the `commissioner1@…` address the COUNTY assigns, which belongs to
the seat rather than the person. The office block carries the courthouse address
and no phone: the number on the letterhead is the CLERK's line, and printing it
under "Board Office" would imply the board answers it.

**The mechanism this needed, and the honesty cost it carries.** Every other
county in that roster is scraped from a page each week. Edwards has no page, so
it became the first entry in a new `DOCUMENT_ROSTERS` table — names carried from
the Clerk's document with the document named and a verification date attached.
That is a real cost: **a weekly job that "refreshes" a hand-carried roster
refreshes nothing**, and the same three names would ship every week whatever the
county did. So the scraper prints a `NOT RE-READ` line on every run naming the
county, the document and how many days old it is, the builder refuses any county
carrying neither a `sourceUrl` nor a `sourceDocument`, and the worksheet note
says all of it. The cost is paid out loud rather than hidden.

**Ring work, per the §2.5.1 checklist.** Edwards is FIPS 047 and White County
sits between it and Hamilton, so it lands DETACHED rather than extending the
second island: `metro-outline.json` is now four polygons. Albion anchors it
INSIDE, and **Carmi (White) was added OUTSIDE** — that anchor is what proves the
two southern islands stayed two rather than quietly merging across an unserved
county. All 56 inside and 13 outside anchors verify.

### 2026-08-06: Jefferson, the county that ended an island — and the first source that had to be REPAIRED

`pass10-frontier-unasked` named five counties and ended with a prescription:
*"Asking the five clerks is the next move, not more searching."* Jefferson was
asked on 5 Aug and its Clerk replied the next day with "Please see attached"
and a precinct shapefile. It is the 46th dispatched county, and adding it
**merged the Hamilton island back into the mainland** — Jefferson borders both
Washington and Hamilton, so the outline drops from four polygons to three.
Islands can un-island; the ring code handles it because the dissolve is
recomputed rather than patched.

**The file needed work no previous county's has, and that is the part worth
recording.** Measured before a line of builder was written:

  * The 33 precincts tile **99.212%** of the county, not ~100%.
  * The missing 0.788% is not a hole and no precinct is absent. It is a single
    **connected lattice of hairline cracks** running along nearly every shared
    boundary — it touches all 33 precincts at once — because each polygon was
    digitised independently and neighbours' edges were never snapped.
  * Every uncovered sample point lies within **31 m** of a precinct edge.
  * Left alone that is about **one click in 127** answering "this point isn't
    inside any district", which is a lie: the point IS in a precinct.

**Two repairs were tried and the obvious one is wrong.** "Give each gap piece
to the neighbour it shares the most edge with" is the natural rule and it fails
badly here, because the lattice is ONE connected piece spanning the county — the
whole thing lands on a single precinct and moves a boundary **35 kilometres**.
The connectedness of the defect is exactly what defeats the obvious fix, which
is why it is written down rather than left for the next person to rediscover.

What ships is **nearest-boundary assignment**: every point in a crack goes to
the precinct whose boundary is nearest, computed as a Voronoi partition over
densified boundaries. Correct ownership, but it draws the new edge down a
zig-zagging medial line and cost 52,538 vertices — a 1.2 MB file for 33
precincts, against Henry's 233 KB for 52. Simplifying at 10 m collapses that
noise back onto the straight township lines the county actually drew: **89 KB,
3,798 vertices, 99.975% coverage**, median boundary shift 35 m and worst 118 m.
A shared edge survives simplification because both neighbours simplify the SAME
linework at the same tolerance and Douglas-Peucker is deterministic.

**The residue is asserted, not hoped for.** 0.025% of the county still falls in
a crack — one click in 4,000, against one in 127 — and the builder fails if a
future export needs a bigger correction than this one did.

**What was deliberately NOT repaired.** The county's file also contains a small
genuine OVERLAP between Dodds 1 and Dodds 2. It stays exactly as drawn: **a
crack has no owner and can be assigned; two claims on the same ground cannot**,
and picking a winner would be inventing an answer the county did not give. It
goes back to the Clerk as a bug report instead.

**The half that did not arrive.** The 5 Aug ask covered board districts AND
precincts; only precincts came back, with no covering note. That is an
incomplete answer, not a refusal, and `jefferson-county-board` records it with
the cheap route named: now that the precincts are in hand, **a plain list of
which precincts make up each district** would let the boundaries be dissolved
exactly, with no new geometry needed from the county at all.

Four sources now ship from **archived files** rather than live fetches — Stark's map,
Ogle's shapefile, Marshall's table, Washington's Blue Book. Their weekly jobs guard the
parsers, not the sources. If one of those counties changes something, nothing turns red.
Every ask that returns a file adds one of these, so the cost of this strategy is a slowly
growing set of things that must be re-asked rather than re-fetched. Worth it, and worth
counting.

### 2026-08-06: the ask fixed the SOURCE, and the override retired itself in a day

The best outcome an ask can have is not a file. It is the publisher correcting the
thing everybody reads.

**The override lasted about eighteen hours.** `CLERK_STATED_OFFICES` was written on
5 Aug because Stephenson's Cities & Villages directory printed Jonathon Riley as a
Dakota *Trustee* while Clerk & Recorder Jazmin Wingert said in writing he was the
village president. It was built to ship her answer, record the page's, pin the office
the page printed, and print a RETIRE line the moment that cell changed in any
direction. On 6 Aug the county changed it. The run printed the RETIRE line exactly as
designed, and the entry was deleted. **The table is still there and still empty**, which
is the correct end state for a mechanism of this shape: the next conflict gets the same
handling, and no dead override sits in the file pretending to be load-bearing.

**But the correction was not the interesting part of the update.** The county did not
fix one title — it republished the whole Dakota table, and four of the eight people on
the live card are not on the new one:

| Live card before 6 Aug | The county's page now |
|---|---|
| Jonathon Riley, Village President *(shipped only because the override said so)* | **Jonathan Riley, President (Appointed)** — the page now says it itself, and settles the spelling |
| Jessie Wenger, Clerk | **McKenzie Holste**, Clerk (Appointed) |
| Melody Sweet, Treasurer | Melody Sweet, Treasurer (Appointed) — unchanged |
| Trustees Alisha Lizer, Diane Clay, Eric Lizer | Trustees **Otis Holley, Thomas Long, Andrew Workinger** |
| Trustees Jeremy Knox, Kenneth Vrazsity | Jeremy Knox, Kenneth Vrazsity — unchanged |
| *(Kaytlyn Vrazsity's blank-office row was parsed and dropped, never shipped)* | *(row gone)* |

So `dakota-village-president` is **CLOSED**, and the blank-office row that the 5 Aug
entry deliberately refused to fill resolved itself by removal — which is the vindication
of refusing. Had that blank been "obviously" filled in as the sixth trustee, this project
would have invented a seat for someone who had already left the board, and then shipped
it with confidence. Note also what the override got right for the wrong reason: it pinned
the *published* spelling "Jonathon" on the principle that a document outranks a hurried
e-mail on orthography, and the county has now settled it the other way, at the source,
with no code change needed.

**The Clerk also explained the conflict, and neither source had been wrong.** Asked
which of the two was right, she answered from the election records: *"Jonathan Riley was
elected as a trustee and later appointed as President."* Both documents were accurate on
the day each was written — the directory had simply not been updated across the
appointment. That is worth holding onto the next time two sourced claims disagree: the
`CLERK_STATED_OFFICES` design assumed one of them had to lose, and the real shape was a
stale snapshot of a true fact. It is also why the republished page marks him
"(Appointed)" rather than elected, which no amount of reading either source would have
revealed.

**No gate here could have caught this, and that is the finding.** Every name parsed.
Every count held. The scraper was doing its job perfectly against a page whose *contents*
had gone stale — the one failure mode a parser guard is structurally blind to, because
nothing about a wrong name is malformed. `validate_sources.py` catches a superseded
dataset id; the roster builders catch a page that changes shape; nothing catches a page
that changes people. The only thing that surfaced this was **asking a human about one
seat**, and the answer came back as a rewrite of the whole village.

That generalises past Dakota. Roughly forty asks are outstanding, and their value has
been counted so far in files received. This one returned no file and closed a gap
anyway, by changing the source. **An ask is worth sending to a county this project
already scrapes**, not only to one it cannot read.

**Three names were being rendered backwards, in two counties.** The republished table
arrived with `Holste, McKenzie` — surname-first, the only such row on a page of eighty-two.
Checking whether that was a Stephenson quirk found it was not: LaSalle's Village of Dana
has shipped **`Centeno, Joseph L.`** and **`Centeno, Rebecca`** on live cards all along.
Two sources means the fix belongs in `build_municipal_officials_roster.py` beside the
vacancy guard rather than in one county's parser, and `uninvert_name()` now re-orders
around the comma. **The guard is the whole design**: 24 of the roster's 27 comma-carrying
names are suffixes — "Roy Williams, Jr.", "John W. Hamm, III" — and inverting one of
those yields "Jr. Roy Williams", a worse defect than the one being fixed. An inversion
therefore requires exactly one comma, both sides non-empty, a trailing side that is not
a known suffix, and both sides matching name text; everything else ships verbatim and
says so in the run's warnings.

**One thing was deliberately NOT claimed.** The 5 Aug reply also pointed at a polling-place
heading, reported here at the time as a 404. It resolves now, and it lists **five
Freeport-area churches with no precinct keys** — which cannot serve thirty-six precincts
and cannot be joined to any of them. `stephenson-freeport-precincts` and the county's
polling gap stay open. A page existing is not a page answering.

**And the same reply closed a route rather than opening one, which is still worth having.**
The 5 Aug follow-up asked the Clerk directly whether her office could release the county's
own precinct file — offering to file a formal FOIA if that was the required form, since the
precincts are election geography her office draws and adopts rather than WinGIS's product.
Her answer: *"The only precinct maps I have are the ones that are accessible on the website."*
So the election authority holds no digital precinct file at all, and the published maps this
project traced at ~20 m ARE the county's copy. No FOIA produces a file that does not exist.
That is a definitive answer, not a refusal, and both Stephenson gap records now say so —
which matters more than it sounds, because "ask the county directly" is the route this
ledger otherwise recommends on nearly every unbuilt precinct gap in the file, and here is
the case where working it to the end returned nothing. **A route measured to its end and
closed is a real return on an ask.** The remaining routes are a paid WinGIS quote or a
public WinGIS service for Stephenson equivalent to the open Winnebago ones.

The same reply answered the park/library sub-question the same way and better: the county
publishes no contact information for its eight park and library districts and holds no
report that would generate it, but the Clerk offered — unprompted — to help reach any
district this project cannot find on its own. So `stephenson-park-library-districts` now
names the districts-themselves route as the one to work, with the Clerk as a named fallback
for reaching them.

### 2026-08-07: Montgomery answered with BOTH halves, and the file's own name was a trap

Asked 5 Aug. On 6 Aug **Kevin Brink, GIS Tech / Plat Act Officer**, replied
"Please see attached" with a file geodatabase holding **the board districts AND
the precincts** — the first ask in this campaign to return both halves of a
county at once. Montgomery ships as the **47th dispatched county** with nothing
derived and nothing traced, which for a county of 28,000 is the better tier.

**The gap record had it exactly backwards, and that is worth keeping.** It read:
"Montgomery has one of the best board member lists we have found and no district
boundaries at all", and prescribed tracing the county's readable map as the
fallback. What it was measuring was the county's WEBSITE, which publishes a
Beacon/Schneider parcel viewer and no geometry. The GIS office had the shapes the
whole time. That is the Ogle finding for the fifth or sixth time — *"publishes no
X" is not "cannot obtain X"* — and it is now the single most repeated lesson in
this ledger.

**A file geodatabase, which is a first here.** Every previous county sent a
shapefile. A .gdb is a directory of binary tables, and pyshp cannot read one at
all; `pyogrio` reads it through GDAL's `/vsizip/` handler straight out of the
archived zip, so what ships is built from the bytes the county sent with no hand
conversion in between — which is what keeps "ask again" a real refresh path
rather than a re-do of somebody's manual export.

**The trap: the layer is named `CountyBoardDistricts_2010`.** An Illinois county
must reapportion after each census, so a 2010-cycle map would be five years
superseded and shipping it would tell residents the wrong commissioner. Two
independent things say it is current, and the builder now asserts both on every
run rather than having checked once:

| Check | Result |
|---|---|
| Districts' `Pop100` sum | 28,210 |
| District 4's own comment | `5949-1894 (Graham CC) = 4055` — Graham Correctional Center backed out |
| So the raw sum is | **30,104 = Montgomery's 2010 census count exactly** (2020 was 28,288) |
| The county's published **"Districts After Redistricting 2020-2030"** chart | geometry reproduces it for **all 38 precincts**, including **all five it splits** |

So `_2010` names the **population vintage**, not the map: Montgomery
reapportioned after 2020 and kept its lines. **The composition assertion is the
real gate**, and it is a much sharper one than any count or area threshold
because it compares geometry against something the county says *in words* —
"N 1/2 & NW of Butler Grove Twp-1 / SE Territory... including Village of
Butler-6" lands as Butler Grove 81.9% in District 1 and 18.1% in District 6. A
future export that moves a boundary enough to change a precinct's district fails
the build and points the next person back at the chart.

**Those five splits are also why the precinct card joins its board district
spatially rather than by table.** A precinct name does not determine a district
in Montgomery — only the clicked point can.

**Shipped as drawn, and this time that is the finding.** Both tilings have the
same unsnapped-neighbour cracks Jefferson had, at a completely different scale:

| | in a crack | ≈ 1 click in |
|---|---|---|
| Jefferson, as sent | 0.788% | 127 — **repaired** |
| Jefferson, after its Voronoi repair | 0.025% | 4,000 |
| Montgomery districts, as sent | 0.0064% | 15,600 |
| Montgomery precincts, as sent | 0.0034% | 29,400 |

Montgomery as sent is several times cleaner than Jefferson ended up *after*
repair, so repairing here would move real boundaries to buy nothing. Jefferson
established that a county's file can need fixing; Montgomery establishes the
other half of that rule — **measure before repairing, and usually don't.** The
ceiling is asserted so a genuinely broken future export cannot ship quietly.

**Two county documents, trusted for two different things.** The Clerk's "County
Board Districts/Members" PDF (revised 12/2024) is the source for the district
COMPOSITION above. It is deliberately NOT the source for the roster: checked
6 Aug it still named Bill Bergen (District 5) and Andy Ritchie (District 7) where
the county's board page has Cody Gudgel and Roy Schieferdecker. Same county, same
office, one stale document — the Dakota lesson from the day before, arriving
again before the ink was dry. The roster is scraped weekly from the page, and it
is the richest per-seat set in the fleet's smaller counties: **14 of 14 with a
direct phone and a county e-mail**, four with a second published number.

**One published e-mail is wrong and ships anyway.** District 5's Cody Gudgel is
listed at `cody.gudel@montgomerycountyil.gov` — "gudel", where every other
address on the page is firstname.lastname. Almost certainly the county's typo.
It is carried exactly as published: correcting it would mean inventing an address
string, which could belong to nobody or to somebody else. The scraper prints a
NOTE naming it on every run so the discrepancy stays visible, and it goes back to
the county as a bug report. **Compare the Stephenson comma, which WAS normalised
the same week** — reordering "Holste, McKenzie" around a comma invents nothing,
while changing "gudel" to "gudgel" invents a string. That is the line, and these
two cases sit on either side of it.

### 2026-08-11: the Stephenson lesson, a second time — Henry's polling list

`henry-precinct-polling` opened on 6 Aug as the REMAINDER of a gap that
otherwise closed. The 1 Aug ask wanted two things; Henry County GIS answered the
geometry half completely — a shapefile by return e-mail, the cleanest precinct
data any county has sent this project — and drew the line on the other half
itself: *"The other questions are for Barb to answer/supply."* So the polling
assignment sat with Clerk Barbara Link for five days.

Her whole reply, on 11 Aug:

> "I have pdf precinct maps on my webpage for all precinct boundaries so I feel
> that my webpage is sufficient for what is needed. Also, I have polling place
> locations as well."

**That reads as a brush-off and is a pointer, and the pointer is correct.** Her
Polling Places directory lists all 52 locations, one per precinct, each with a
street address and the precinct repeated in a field of its own. It had been
reachable for the entire life of this project. Nobody opened it.

This is Stephenson on 3 Aug arriving a second time, and the repeat is the
finding. Jazmin Wingert's one line — *"Here is a link to the maps I have record
of"* — pointed at a page carrying two vector precinct PDFs, one navigation step
from maps this repo already used, while two gap records said flatly that the
county published no current precinct boundaries. **The failure mode is not "the
county has nothing" and not "the county never posted it" — it is that the file
is posted, on a page nobody looked at, and no amount of re-checking the pages
already known will ever surface it.** The only thing that does is asking a clerk
to enumerate her own holdings, which costs her a sentence and audits the search
from the inside.

Two mechanical notes from the build, both of the kind that ship silently wrong:

- **The listing title is not the key.** Every row reads "`<Precinct> - <Location>`"
  until it doesn't — Henry writes "Colona 3- Colona Activity Center" without the
  space and "Andover Village Hall" with no precinct at all. The precinct is also
  in a field of its own, and that is what the builder joins on.
- **One row of 52 has no "View Map" link.** A parser keyed to that link drops
  Colona 4 and reports 51 successes. The builder now reads the directory's own
  stated listing count and refuses if what it parsed does not equal it, because
  a polling place silently missing is a resident sent nowhere.

The gap record is retired. What it also held — that permission to publish was
asked twice and never answered — moved to `henry-precincts.json`'s own note,
where the file's provenance lives, rather than disappearing with the record.

**And it is the fleet's first SCHEDULED polling job**, which is a departure worth
stating. Carroll's, Logan's and Montgomery's polling tables are operator steps —
re-run when the clerk republishes — and that is fine for a table nobody reads
between elections. A polling place is not that table. It is the one row on any
card in this app where being a cycle out of date sends a resident to the wrong
building on election day, and six page fetches a week turn "we will remember to
re-run it" into a pull request. The job opens one **only when a polling place
actually moved**: the shipped file carries a fetch date that changes every run,
and a weekly PR that is nothing but a new date teaches a reviewer to stop
reading them, which costs more than the job saves.

**And the lesson landed twice in one day.** Shelby's Clerk answered the 5 Aug
board-form ask the same afternoon, and her one pointer — "under county clerk,
election information" — was the fourth clerk-enumeration in the sequence
(Stephenson, Henry, Hamilton, Shelby): sitting on `coclerk.aspx` the whole time
was `ShelbyCoIL_CountyBoardDistricts.pdf`, the adopted 2021 plan as a
county-wide **vector** PDF with all 11 districts and all 33 precincts, names
and populations printed. Measured the same day, TIGER's 2020 VTDs are that
fabric exactly (33/33 names, 31/33 populations to the person), which converts
Shelby from a vector-extraction candidate into a DeWitt-class dissolve. The
same reply carried the campaign's **first seal denial**, recorded in
`docs/COUNTY_SEALS_REVIEW.md` as its own permanent class — a denial is not a
missing image, and no later free-license find reopens it.

### 2026-08-07: the gap record wrote its own closing instructions, and they worked

`jefferson-county-board` was opened on 6 Aug when an ask for both halves of a
county returned only one. Rather than record that as a refusal, it named the
cheap route back:

> "the precincts are now in hand, so a plain LIST of which precincts make up
> each district would be enough to draw the boundaries exactly, with no new
> geometry needed from the county at all."

Re-asked on exactly that basis. On 7 Aug County Clerk Joe Davis sent **"County
Board Districts (Approved by County Board November 22, 2021)"** — one line per
district naming its precincts — and the gap is **CLOSED** the same day. **A gap
record that states what would close it is worth more than one that states what
is missing**, because the second time you write to a county you can ask for the
cheap thing instead of the expensive one. Three asks total to this office, and
Jefferson now ships both its precincts and its board.

**The thread is closed, 2026-08-11.** Four asks in total to this office, and the
last of them — where the District 10/11 line runs inside Shiloh 4 once 34th
Street's pavement ends — was answered on 10 Aug by Clerk Davis pointing at the
county's published precinct legal descriptions. That page settles that "34th
Street" is a line the county draws and puts the county's own Shiloh 3 edge
within seven metres of the cut already in use; it does not say where the line
goes past the pavement. The shipped geometry was reviewed and accepted as
accurate on 11 Aug, the drafted follow-up was withdrawn unsent, and **nothing is
outstanding with Jefferson County.** The card's boundaryNote stays: closing an
ask and deleting a caveat are different acts, and the note describes how the
line was drawn rather than a question still hanging.

**The list is self-proving, and the builder makes it prove itself every run.**
All 33 shipped precincts are named, none is named that does not exist, and the
13 dissolved districts reproduce the county's own extent to **0.0000%**. A future
list that drops or invents a precinct fails the build.

**One precinct is split, and it is where the only inference in the file lives.**
The chart puts "Shiloh 4 west of 34th Street" in District 10 and "east" in
District 11. Three things were decided here rather than assumed:

- **The cut longitude comes from TIGER/Line, not OpenStreetMap.** OSM has the
  street mapped in more detail and was used to *corroborate* the number — but
  OSM is **ODbL**, and a shipped civic boundary derived from it would carry
  share-alike obligations this project has not taken on. The Census
  Transportation layer is public domain and puts 34th St at −88.93327; OSM's
  "North 34th Street" runs −88.93334..−88.93327, so they agree to about 6 m.
  **Reading one coordinate to check a number is not the same act as building a
  boundary from a database**, and the distinction is worth stating before the
  next county needs a road.
- **34th Street does not reach the top of the precinct.** It stops about three
  quarters of the way up; north of that the cut is the street's alignment
  projected. That zone is 25% of Shiloh 4 and 0.05% of the county — and it is
  *not* empty ground: it holds the Chesterfield Village, Webster Hill and
  Kingsridge subdivisions. So the caveat is real and it ships on the card, on
  Districts 10 and 11 only. The county has been asked to confirm where the line
  runs up there.
- **This is still strictly better than the precedent.** LaSalle's split precincts
  ship wholly on their majority side with the card saying so. Here three quarters
  of the boundary is exact and the rest is a straight projection.

**The Dodds overlap has an explanation now, and it changes nothing about the
board.** Asked about the one genuine defect in the precinct file, Davis replied
that the two are divided by the **Casey Fork river**, "Dodds 2 being left or west
of and Dodds 1 being on the right or east of it" — prefaced with "I believe". It
stays unrepaired for two reasons: the answer is hedged, and it does not matter
here anyway, because **Dodds 1 and Dodds 2 are both District 6**, so the overlap
is interior to a single board district and cannot change anyone's answer. A
defect that can't reach the reader is not worth a repair built on "I believe".

**The names arrived surname-first — the third source in one week.** After
Stephenson's Dakota clerk and LaSalle's Village of Dana, Jefferson's board table
prints every one of its thirteen as "Draege, Steve". The builder imports
`uninvert_name()` from `build_municipal_officials_roster.py` rather than carrying
a third copy, and refuses to write if any name still holds a comma. Three
independent counties in seven days is enough to call this a *format*, not an
anomaly, and the next county that does it should cost nothing.

**One trap for whoever maintains this.** The county's own navigation links
`/government/county_board/index.php`, which **404s while rendering the full site
chrome** — it looks like a working page with no roster on it. The live page is
`/county_board/index.php` at the root. The scraper's zero-row guard says so in
its failure message, because "the layout changed" is the wrong conclusion to
reach here.

### 2026-08-07, afternoon: two follow-ups landed, and both corrected THIS project

Neither reply was a new ask. Both were answers to notes sent that morning, and
between them they fixed one thing on the map and one thing in the method.

**Montgomery: the polling places arrived, and the GIS layer was the wrong source
for them.** Asked whether a precinct-to-polling-place mapping existed, County GIS
sent a second geodatabase with a `PollingPlaces` point layer — 24 points with
names and addresses. Cross-checking it against the Clerk's own published
"38 Precincts / 24 Polling Places" list found the point layer is behind:

| | GIS point layer | Clerk's published list |
|---|---|---|
| **Rountree** | absent entirely | votes at Nokomis Memorial Park House with Nokomis 2 |
| **N. Litchfield 1 & 4** | National Guard Armory | **First Presbyterian Church, 1908 N. State St.** |
| **Hillsboro 5 & 6** | "K C Hall" | The Event Center of Montgomery County (former Hillsboro KC Hall) |

So the shipped table is transcribed from the **Clerk's** document, not from the
file that arrived in answer to the question. **A polling place is the one field
on these cards where being out of date sends a person to the wrong building on
election day**, and the election authority's own list outranks a GIS office's
point layer for that. The GIS layer stays as a *named* cross-check: the builder
records those three findings and FAILS if the layer's answer changes, so a
county refresh that fixes them is noticed rather than silently absorbed.

**That cross-check had to be rewritten before it was worth having.** The first
version fuzzy-matched the two sources' place names and reported a dozen
"disagreements" that were pure wording — "United Methodist Church E. Ent."
against "Methodist Church (North Entrance)". A check that cries wolf on wording
buries the two findings that matter, which is worse than no check at all. Naming
the real disagreements and verifying they persist is both quieter and stricter.

**Kevin Brink confirmed the `_2010` reading at the source.** The two-way proof
that Montgomery's oddly-named layer was current — the Graham CC arithmetic and
the composition chart — is now corroborated by the county's own GIS tech: *"I had
not been notified of any update to it that would have changed the year given, and
the '_2010' name predates my employment. Please feel free to truncate the layer
name."* He also confirmed the `cody.gudel@` typo is real and sent it to IT, which
is the vindication of publishing it as-listed: **the fix comes from the source and
arrives through the weekly scrape with no code change here.**

### 2026-08-07: Menard ships as the 48th county, and the OUTSIDE list was wrong about it in a useful way

Asked 3 Aug. Clerk & Recorder **Martha "Marty" Gum** replied the next morning,
looped in **Supervisor of Assessments Dawn Kelton**, who requested the file from
**Beacon** — the county's GIS vendor — and forwarded it on 7 Aug. Three offices
and one vendor, four days, for a county that publishes no boundary at all.

**It is the cleanest county file this campaign has received.** Zero invalid
geometries, zero self-overlap, and — unlike both Jefferson's and Montgomery's —
**zero internal cracks**. The five polygons are properly edge-matched. Nothing
needed repairing and nothing was repaired. It proves itself against the Census
too: the districts' POP20 values sum to **12,297**, exactly Menard's 2020 count,
asserted on every build.

**The ring's OUTSIDE list had recorded exactly why this was impossible**, and
every word of it was true:

> *"Menard's five commissioner districts run section-line roads rather than
> precinct or township unions, so no composition route exists and its only map is
> a 2021-12 raster."*

All correct — and none of it mattered. **That list records what can be DERIVED,
which was never the same question as what a county will send.** The reasoning
stays in the file as a correction rather than being deleted, because the next
"this one is genuinely impossible" entry deserves the same scepticism.

**A mistake worth keeping, this project's own.** The e-mail that produced this
file asked for *"the three district polygons"*. Menard has **five**. The gap
record had it right the whole time — it says five, and it quotes the population
range printed on the state's map, 2,436 to 2,486, which is exactly this file's
five values. The error was in the ask, not the record: a district count asserted
from a picture that could not properly be read. The county ignored the wrong
premise and sent the real thing. **Read your own gap record before writing the
ask** — the same lesson as the Vermilion "middle of the county" slip, and the
second time this campaign has sent a county a premise it had already disproved.

**A commission county that is NOT a County-card county.** Menard elects five
commissioners, but **by district** — so unlike Monroe, Randolph and Edwards,
which ride the County card at large, it has geometry and takes a layer. The
§1.5 at-large tier turns on *how* a commission is elected, not on the word
"commissioner", and Menard is the first county to make that distinction load-
bearing.

**"Ed Whitcomb, Jr." exercised the suffix guard in production.** District 5's
chair is the first shipped name to hit `uninvert_name()`'s **refusal** path — the
branch that exists so a suffix never becomes "Jr. Ed Whitcomb". Written for
Stephenson, needed by LaSalle and Jefferson, and now proven by the case it was
built to protect. The builder asserts the name came through unreordered rather
than trusting it.

**One published e-mail disagrees with its own label.** District 1's link points
at `djwhitley@` while the text beside it reads `dwhitley@`. The **href** ships —
that is where the county's own page sends mail when a resident clicks it — and
the run prints a NOTE. Same rule as Montgomery's `cody.gudel@`, two counties
apart on the same day.

### 2026-08-07, evening: Macon's board ships, and the missing thing was five numbers

`macon-county-board-labels` was the most precisely-specified gap in the file. The
county publishes its five board districts as **live GIS with every attribute
null** — no district number, no representative, no contact — and the record
refused to number them by position, because that is a guess about who represents
whom. It named three cures and said any one would work "on the same day":

> "District numbers for the five shapes — a labelled clerk's map, the adopted
> redistricting ordinance, or simply the county filling in the district field its
> own data already has."

County Clerk **Josh Tanner** sent the first: *"Macon County Board Districts
2022"*, colour-coded, with a legend numbering 1 to 5. **Five numbers, and a
county that had been held back for five days ships its board.**

**What was actually missing was tiny, and that is the point.** The geometry was
always there and always correct. This gap was never about data the county
lacked — it was about five integers that existed only in a picture. It is the
cheapest close in the campaign and it took the same thing every other close took:
writing to somebody.

**How the labelling was verified, because "look at the map" is not a method.**
The map is a raster — no text layer, ~50 image tiles — so nothing could be
extracted from it programmatically. It was read by eye. That makes verification
the whole job, and it was done three independent ways:

1. **Membership, precinct by precinct.** Each of the county's five shapes was
   intersected with the county's own 64 precincts to get its member list, and
   those lists were matched against the map's colour regions. Every outlier lands
   correctly — **Decatur 24** alone in the northern district, **Decatur 4, 7 and
   28** in the eastern, **Decatur 22 and 25** in the western. A position-based
   guess reproduces none of that.
2. **The bijection.** Five anchor points, one per district, each inside a
   precinct the map colours unambiguously. Each falls in exactly one shape and
   the five are distinct.
3. **The roster.** The county publishes 15 members keyed by district. They come
   out **3-3-3-3-3** across the five shapes. There is no reason for that to hold
   if the labels were wrong.

**What ships is the labels, not the geometry.** Five anchor points in a 1 KB
file; the county's shapes stay live, so a redraw still reaches the app. The
labelling happens at runtime and **must be one-to-one or the layer serves
nothing** — which returns Macon to exactly the held-back state this gap
describes, rather than showing somebody the wrong commissioner. The county's own
`district` field is preferred the day it is ever filled in, and the builder says
so out loud when that happens.

**Anchors rather than OBJECTIDs, deliberately.** OBJECTID is the only other
handle the service offers and it is precisely the key that changes when a layer
is republished — silently reassigning every district. An anchor survives a
republish and a boundary nudge, and it states the finding in the form it was
read: *the district containing Maroa is District 3*. (The OBJECTIDs happen to run
16–20 in district order. That is a coincidence, and relying on it would have been
the guess the gap record refused to make.)

**A dead link, found while looking for the roster.** Macon's precinct card has
been linking `maconcountyil.gov` since 2026-08-04. That domain **has no DNS
record at all** — not a redirect, not a 404, no address associated with the
hostname. The county is at `maconcounty.illinois.gov`, the same `illinois.gov`
pattern Jefferson uses and the same trap: a plausible-looking domain that was
never checked because nothing checks a link that is only ever rendered. Both
replacements verified 200. Worth a standing lesson — **`validate_sources.py`
checks dataset endpoints but nothing checks the `primaryLink` URLs the cards
render**, and this is the second county this week whose real domain turned out to
be the `illinois.gov` form.

**The phones ship at seven digits.** The county lists "C 521-4688" with no area
code. Macon is entirely 217, and prefixing it is the obvious improvement and the
same class of mistake refused all week: a member's mobile can be issued anywhere,
and a wrong prefix does not fail visibly — it reaches a stranger. The county's
own home/cell labels are kept, which helps without inventing. Recorded as
`macon-board-phone-area-code`.

### 2026-08-08: the five counties that were served and silent, and what a canvass settled

`build_county_status.py`'s board column fell through to "no board layer — see gaps"
whenever a served county had no `county-board` entry. For five counties that pointer
led nowhere: **Bond, Greene, Jersey, Morgan and Scott** are judicial-circuit
secondaries whose only county-specific card is the subcircuit, and NOTHING anywhere
said why their board was missing. Their gaps column read `none`, so the roll-up also
counted them as COMPLETE. That is the inversion worth naming: nobody had measured
them, which is a weaker claim than nothing being missing, and the generator was
stating the stronger one.

The cell now distinguishes `see gaps` from **`no gap record`**, the doc carries a
callout, and every build prints the count — but the count only reaches zero by doing
the research, so it was done.

**The form question answered for all five, from certified canvasses — and it split
3-2 in a way the websites alone would have got wrong.** All three of Greene, Morgan
and Scott publish results through `results.gbsvote.com`, which names each county
clerk as Election Authority:

| County | Contest, from an OFFICIAL canvass | Reading |
|---|---|---|
| Greene | "FOR COUNTY BOARD FOUR YEAR TERM / 22 of 22 precincts reporting / Vote for ( 4 )" (2026 primary); "FOR MEMBER OF THE COUNTY BOARD / 22 of 22 / Vote for ( 1 )" (2024 primary) | **at-large**, 7 members, no districts |
| Morgan | "FOR COUNTY COMMISSIONER / 27 of 27 precincts reporting / Vote for ( 1 )" (2024 primary, repeated in the 2022 and 2024 generals) | **commission**, 3 at-large |
| Scott | "FOR COUNTY COMMISSIONER / 10 of 10 precincts reporting / Vote for ( 1 )" (2022 general) | **commission**, 3 at-large |
| Bond | board page lists Board Districts 1-5, one member each | **districted** — geometry ask |
| Jersey | board page gives every member a "Jersey County Board District N" line, 3 per district across 1-4 | **districted** — geometry ask |

So three of the five need NO geometry ever, and two need boundaries nobody publishes.
Bond's absence is measured rather than assumed: its ArcGIS Online org
(`services.arcgis.com/VbP0KHITyLTMBTy3`) was enumerated in full — 24 services of
parcels, zoning, townships, municipal, floodplain, cemeteries, schools and fire — with
no board and no precinct layer. Jersey has no GIS host at all, confirmed by DNS rather
than by a failed fetch.

**MORGAN'S OWN WEBSITE CONTRADICTS MORGAN'S OWN CANVASS**, and that is the lesson to
carry. `morgancounty-il.gov` ships the sentence "the county is governed by a board of
commissioners **elected by district**". It is CMS filler sitting in the site's
JavaScript bundle as a default template, and four certified canvasses say every
commissioner is elected by the whole county. A researcher reading the website would
have built districts that do not exist — which is exactly why §2.5 step 2 requires the
election document and not the page. The rule earned its keep here.

Two decoys were checked before they cost anything: ArcGIS Online's "Bond Districts"
is municipal BOND (debt) districts in DuPage County, and Morgan's Supabase backend
exposes zero tables to the anonymous key its own app ships, so the SPA is not a roster
source. Scott's commissioners render only inside a Munibit "People" widget whose API
500s without the page's parameters, and the Internet Archive's capture preserved the
same empty shell.

**Five gap records written, five county outlines built** (Census place centroids tested
against each county's own TIGER rings for inside, nearest place in a neighbour resolved
by point-in-polygon for outside — Jersey carries four because it has four Illinois
neighbours). The gaps panel now locates every one: a click in Carrollton or Greenville
leads with that county's own record. Gaps 116 → 121.

**What each now needs is small and different. GREENE IS ALREADY DONE — it shipped the
same day**, since it needed no ask: its seven members were already published with county
e-mails, so a SITES entry and a parser put them on the County card exactly as Schuyler's
were. It is the first County-card county that was ALREADY SERVED before its board
arrived, so it moved tier (judicial 5 -> 4, card 6 -> 7) without touching the ring.
Its chair is styled **Chairwoman** and its deputy **Vice Chair**; both are kept verbatim
and `ALLOWED_ROLES` was widened rather than normalising a real person's own county's
wording to the -man forms — with `CHAIR_ROLES` added in the same change, because the
one-chair guard matched the literal "Chairman" and would otherwise have let a board
seat two chairs silently. Morgan and Scott need three
names each from a clerk, the one-e-mail shape that closed Wabash. Bond and Jersey need
boundaries, and both publish the member-by-district list that any submission can be
checked against.

### 2026-08-08: shipping Greene found two ways the at-large roster was failing quietly

Greene itself was twenty minutes of work. Regenerating the shared roster to include
it surfaced two faults that had nothing to do with Greene, and both were the silent
kind.

**A single flaky fetch failed the whole weekly refresh, and the county it failed on
moved.** `il_county_commissioners_scraper.py` fetched each county once, with no retry.
One bad response — several of these sites are Cloudflare-fronted — made that county
parse 0 members, and `build_county_commissioners.py` then correctly refused to write
the file, so ALL ten counties' refresh failed on one county's bad afternoon.
Consecutive runs failed on Brown, then on Calhoun, then on neither, which is the
signature of flake rather than of a page that changed. Now: three attempts with
backoff, plus one extra re-fetch when a parse yields ZERO where the county expects
members. Re-fetching cannot hide a real break — a shape change usually still yields
some rows, and a genuine zero still WARNs and still stops the build — it only removes
the coin-flip.

**Cloudflare's e-mail obfuscation would have deleted seven published addresses with
nothing failing.** browncoil.org turned on Email Address Obfuscation at some point
after Brown was built: every `mailto:` became
`<span class="__cf_email__" data-cfemail="79…">`. The parser read `mailto:` only, so
it returned seven members and zero e-mails — and the seat-count guard, which checks
that Brown seats SEVEN, passed happily. A regenerate would have silently dropped
seven addresses from a tool whose entire purpose is telling residents how to reach
their board. THE GUARD MEASURED THE WRONG THING: counting rows says nothing about
whether the rows still carry what they carried yesterday.

The fix is a shared `email_in()` that reads both encodings — the obfuscation is a
one-byte XOR that the page's own JavaScript undoes for every visitor, so the address
is published exactly as before and only its wire format changed. It was VERIFIED
BEFORE IT WAS TRUSTED: the decoder reproduces all seven addresses already sitting in
`data/app/il-county-commissioners.json`, exactly. That is what makes it the same data
rather than a new claim about it, and it is the check to repeat if this is ever
extended to another county.

**The general lesson, worth more than either fix: a count guard protects against a
page that BREAKS, not against a page that quietly stops saying something.** Every
roster in the fleet is guarded by row counts. None of them would notice a field going
empty across the board. Worth a pass sometime over which fields a builder should
refuse to lose, not merely how many rows it should refuse to lose.

### 2026-08-08: the due-diligence pass over the roster builders

Prompted by the Brown near-miss the same day. The question was simple — how many
other rosters could lose a field without anything failing — and the answer was all
of them, in the general case.

**The audit.** 43 roster builders. Every one floors a COUNT. Thirty additionally
floor one or two named fields (`MIN_EMAILS`, `MIN_PHONES`); thirteen floor none at
all, including `build_county_commissioners.py`, which is precisely where Brown lives.
But even the thirty are only as good as the fields someone thought to name: each
floor is hand-set per county, and a field added next month ships unguarded by
construction. Adding thirteen more constants would have been the obvious move and
the wrong one.

**What shipped instead: `scripts/check_roster_retention.py`.** It lives outside the
builders and compares every `data/app` roster against the same file at the change's
base, asking one question of each field — does it still appear on about as many
records as before? The shipped file is the baseline, so a field is protected the
moment it first ships, with nothing to configure and no per-county number to drift.
161 files, every field, zero maintenance.

**The subtlety that cost the first draft its first test, and the reason to write the
test first.** The check passed the actual Brown case. Pooled across
`il-county-commissioners.json`, seven vanished e-mails read as 40 -> 33 — an 18% dip,
under every threshold. Ten counties share that file and each breaks on its own, so
coverage is now measured PER TOP-LEVEL KEY as well as per file. Files pooling more
than 200 sources (`municipal-officials.json`, ~1,500 municipalities) stay file-level,
where per-group thresholds would fire on every village that reshuffles a page.
A guard that has never been shown to fail is not a guard; this one now has six
recorded cases — the real Brown shape, a per-district phone loss, a whole-file field
loss, a record collapse, single-member turnover that must NOT fire, and a brand-new
file that must skip.

**The second question, and a clean answer.** If Cloudflare quietly emptied Brown,
how many others were already in that state? Twenty-five scrapers read `mailto:` with
no obfuscation awareness. Every one of their sources was fetched and counted:
**none serves `data-cfemail`.** Brown was the only one, and it is fixed. That is a
measurement rather than a reassurance, and it is worth re-running whenever a county's
e-mails go missing for no visible reason.

**The general shape to carry forward.** A count guard answers "did this break?" It
cannot answer "does this still say what it said?" Any pipeline whose output is
copied from a source it does not control needs the second question asked separately,
and the cheapest way to ask it is to diff against the last known-good copy —
which, in a repo, is free.

### 2026-08-09: the resweep — nine of fourteen "no website" records were false, and the repo already held the answer

Ordered after the Morgan miss: re-examine every gap record whose claim a search could
test. Fifty-two records across 48 counties make a "publishes no X" claim; fourteen say
flatly that no county website answered. **Nine of those fourteen have a live county
website. A tenth and eleventh have sites that refuse this network. Two were right.**

| verdict | counties |
|---|---|
| site found, county government confirmed | Alexander, Clark, Crawford, Gallatin, Lawrence, Richland, Saline, Shelby, White |
| site exists, unreachable from here | Coles (two sites), Pope, Johnson |
| correct as recorded | Cumberland (nothing found), Wabash (503, mail domain, no web server) |

**The answer was in this repository the whole time.** `data/app/il-county-clerks.json`,
scraped weekly from ISBE, carries every Clerk's e-mail — and for NINE of the fourteen the
clerk's e-mail domain IS the county's web domain. On 2026-08-05 this project e-mailed
these counties at `clerk@crawfordcounty.illinois.gov`, `CountyClerk@gallatinco.illinois.gov`,
`acc@alexandercountyil.org` and eleven more, and on the same data recorded that those
counties had no website. The probe permuted the county's NAME; the clerk's address was
sitting one field away, correct and maintained by somebody else.

Why name-permutation could never have worked: counties do not name domains predictably.
The live set includes `gallatinCO.illinois.gov` and `colesCO.illinois.gov` (abbreviated),
`clarkcountyil.ORG` (a TLD never tried at all), `shelbycounty-il.gov`, `whitecounty-il.gov`
and `popecountyil.com`. Six shapes across nine counties.

**It had already been caught once and not generalised.** On 2026-08-05 the Vermilion
County Clerk replied "Yes, Vermilion County does have a website and the link is..." and
the answer sent back said "My automated search tool looks for variations of the full
county name, so I missed it." That was the whole diagnosis, in writing, four days before
the resweep — applied to one county and never turned into a rule. A correction that
stays local to the county that prompted it is a correction that will be needed again.

**Decoys the resweep had to reject**, all on first pages: Scott County TENNESSEE,
Cumberland County MAINE, a Crawford County *Development Association*, a Shelby County
*real-estate agency*, a Gallatin *weather* site. Searching does not lower the bar for
verifying; it raises the volume of things to verify.

**And Wabash is the model.** Its record predicted the exact behaviour re-measured today —
resolves, answers 503, mail domain with no web server — because it was written from a
Clerk's reply plus a measurement instead of from a failed guess. The two records that
survived the resweep are the two that were never guesses.

### 2026-08-08: the county had a SECOND website, and it had everything

The sequel to the record below, and the sharper version of the same lesson. Told that
the Morgan draft claimed the names were unreachable, the reply was a URL:
`morgancounty-il.com/wp/departments/county-commissioners/`. Plain WordPress on Apache,
37 KB, no obfuscation, publishing all three commissioners with ROLE, PARTY, FULL TERM
DATES, NEXT ELECTION and a personal e-mail apiece — richer than most counties in this
fleet.

**The county has two sites and this project read the wrong one.** `morgancounty-il.GOV`,
the domain carried in the ISBE-derived clerk roster, is a client-rendered React shell
marked noindex whose Supabase backend serves no tables. Everything written about
Morgan — the gap record, the ask, the "publishes their names nowhere a machine can
read" — came from measuring that shell carefully and never asking whether it was the
whole county. **The .com host was listed in the .gov bundle's own strings**, alongside
morgancountyil.gov, and went unfollowed.

**The correction is not cosmetic: the derived roster would have named the wrong person.**
Working from election returns gave Zeller (2020), Wankel (2022), Wood (2024). The real
third member is **Michael D. Woods, whose term starts 1 October 2024** — a mid-term
start, i.e. an appointment filling the 2020 seat's vacancy. That is precisely the
failure mode the draft e-mail warned about in the abstract, and it had already happened
in the very county being written to. Returns are a record of contests, not of who holds
the seat; here the gap between those two things is one whole commissioner.

So Morgan SHIPPED instead of being asked: gap closed, three members on the County card
with role, term start and e-mail, no clerk's time spent. Scott was checked for the same
trap under eight domain patterns and has none — `scottcoil.gov` really is its only site
and its Munibit widget really is the only place its names appear, so that ask stands.

**The rule this earns, stronger than the last one:** before recording that a county
publishes nothing, enumerate the county's WEBSITES, not just its pages. A clerk-roster
domain is where the CLERK is, not necessarily where the county is; `.gov` and `.com`
can both exist with entirely different content; and the strings inside a site's own
JavaScript are a free list of the other places it knows about.

### 2026-08-08: "I can't read the names" was false, and the draft e-mail said it out loud

Caught in review, on the Morgan and Scott asks. Both drafts cited the counties' own
election results to prove the board form in one paragraph, then claimed two paragraphs
later that the names were unreachable. A clerk reading that would have been entitled
to reply with the link.

**The results name every winner.** Morgan: Bradley A. Zeller (2020, OFFICIAL), Michael
Wankel (2022), Donny "Racer" Wood (2024). Scott: Robert L. Schafer (2020, OFFICIAL),
John D. Simmons (2022, OFFICIAL), Thomas L. Peterson (2024). Complete sets for both,
from the same portal already cited.

**Three patterns of mine missed them, and the data never moved.** The office is headed
`FOR COUNTY COMMISSIONER` in recent cycles, plain `COUNTY COMMISSIONER` in 2020, and
abbreviated `COUNTY COMM` on Morgan's 2020 page. Each time the first read produced
"no contest here", and each time the fix was in the reader. A probe that reports
absence should be suspected before the source is.

**What is actually missing survives the correction, and is narrower.** Election returns
record who WON a contest, never who holds the seat now. A mid-term vacancy filled by
APPOINTMENT appears in no return anywhere. And the staggered six-year, one-per-general
structure that turns three contests into three sitting members is an inference from the
pattern, not a thing either county states. Publishing the six names on that chain would
be exactly the guess the honesty rules forbid.

So the ask changed shape rather than disappearing: from "please send me your roster" to
"here are three names from your own results — confirm, correct, and say which chairs."
That is a far smaller favour to ask, it shows the homework, and it is the true statement.
Both gap records carried the same false claim and were corrected in the same change;
they had been live for a matter of hours.

**The transferable bit:** the sentence "the source doesn't publish X" is a claim about
the source that is very often a claim about the parser. Before writing it into a gap
record — or worse, into an e-mail to the person who maintains the source — try the
thing a human would try, which here was reading the page.

### 2026-08-09: the resweep tranche — opening state of the nine recovered counties

The nine counties whose websites the resweep recovered, triaged by the only question
that decides their path (EXPANSION_GUIDE §2.5 step 2). **None of this is proof yet** —
every "candidate" below is the page's silence or the page's labels, and this project
does not accept either as the form. A certified canvass or a Clerk's written statement
settles it, and eight of the nine already have an unanswered ask sitting in the mailbox
from 2026-08-05 asking exactly that.

| county | board page shows | reading | path if confirmed |
|---|---|---|---|
| Crawford | Districts 1-5, 11 e-mails | DISTRICTED | geometry ask — stays a gap |
| Richland | Districts 1-7 | DISTRICTED | geometry ask — stays a gap |
| Shelby | Districts 1-7+, 24 e-mails, plus a board e-mail directory | DISTRICTED | geometry ask — stays a gap |
| Lawrence | flat list, Chairman + Vice Chairman, no districts | at-large candidate | **County card — ships** |
| Saline | flat list of 12, Chairman + Vice-Chairman, no districts | at-large candidate | **County card — ships** |
| White | 5 members with party, Chair + Vice, no districts | at-large candidate | **County card — ships** |
| Alexander | department pages for Chairman / Vice Chairman / Member | roster exists, structure unread | TBD |
| Clark | landing page only; roster on a sub-page | TBD | TBD |
| Gallatin | site flaky from here (200 once, TLS reset once) | TBD | TBD |

**The important asymmetry, and the reason this tranche is smaller than it looks.** A
recovered website does not make a county shippable. These nine are all UNSERVED, so a
county joins only when a county-keyed layer answers in it — and for a DISTRICTED board
with no published geometry, there is still nothing to draw. Crawford, Richland and
Shelby therefore stay gaps; what changed is that their gaps are now well-specified
(board page known, member counts known, contacts known) instead of "no website found".

The three at-large candidates are the actual prize: an at-large board needs no geometry
at all, so Lawrence, Saline and White could ship as County-card counties the moment
their form is confirmed — the Greene path, which took twenty minutes.

**Do not confirm the form from these pages.** Greene looked exactly like Lawrence does
here and was only shipped after two OFFICIAL canvasses were read; Morgan's own website
asserted a form its canvasses contradict. The 2026-08-05 asks are the cheapest route and
are already sent; results.gbsvote.com covers some counties and is the second.

### 2026-08-11: Hamilton's pairing was published while the record still called it unguessable

`hamilton-precinct-polling` had narrowed to one ask: a 13-row table for Clerk
Bowman to CONFIRM, because the two instruments this project could bring — an
affine georeference of the county's FY 2017 map and an independent geocode of
the McLeansboro gym — were each ~0.3 mi coarse, put both northwest markers in
DAHLGREN 2, and disagreed with each other about which McLeansboro precinct
holds the gym. The record said only the election authority could settle it.

**She had already settled it, in public, before the table was drafted.** The
gap was reopened for a research pass on 11 Aug, and a web search found the
county's post-migration website — mid-migration when the gap was written on
5 Aug — now carries an Election Notices section, and in it the statutory
notice **"Polling Places and Addresses — 03-17-2026 General Primary
Election"** (posted 19 Feb 2026, signed Heather Bowman, Hamilton County
Clerk): all SIXTEEN precincts, each with its polling place and street
address. The pairing that could not be measured is simply stated, by the
election authority, in a public record.

What the notice settled, against what the record had:

- **The Dahlgren pair, exactly as feared unguessable**: Dahlgren #1 votes at
  the **Township Building, 19283 County Road 200 E**; Dahlgren #2 at
  **Dahlgren Baptist Church, 402 W Main St** — two distinct locations both
  of which the georeference had put inside DAHLGREN 2's polygon.
- **The gym question is MOOT, not resolved for one side**: all four
  McLeansboro precincts vote at the Old Highschool Gym, 204 S Pearl St, so
  the instruments' MCLEANSBORO 3-vs-4 disagreement was about a distinction
  the county does not make. The Clerk's 5 Aug written statement is
  re-confirmed by the notice verbatim in structure — 12 rural precincts at
  their own township building or church, 13 locations in all.
- **Currency**: the FY 2017 map's "has not changed" now has a 2026 primary
  notice agreeing with it, which is the per-election evidence the 5 Aug
  record said was missing.

**The Stephenson/Henry lesson, a third time in one week: the miss is in
which page was looked at.** The old WordPress uploads path 404s — the
migrated site serves documents from `cms.hamiltoncountyil.gov` — so anyone
re-checking the URL recorded in August would have concluded the county still
published nothing. One web search found the notice's landing page in the
first result set.

Shipped the same day, the Carroll/Logan shape: `scripts/
build_hamilton_precinct_polling.py` parses the notice with a 16-name guard,
the Clerk's confirmed 13-location count asserted and the shared-gym rows
asserted to be exactly McLeansboro 1-4; the file joins onto `Precinct_Name`
at load and the card row is labelled with the election the notice names,
because a polling assignment is per-election, not a standing fact. The
drafted 13-row confirmation table was **withdrawn unsent** — the Jefferson
rule: the public record answers, so a fourth message to a four-minute-reply
office would have asked her to hand-confirm what her own notice already
states. Nothing is outstanding with Hamilton County but
`hamilton-municipal-officials`.

### 2026-08-11: Shelby ships as the 49th county — one island merged, one enclave created, and the fleet's first three-way precinct split

`shelby-county-board`'s "wanted" line asked for *"a BUILD, not another ask —
the DeWitt shape, fully de-risked,"* and that is what shipped, to its exact
spec. `scripts/build_shelby_board_districts.py` dissolves TIGER's Census 2020
VTDs — proven 33/33 by name against the county's adopted 2021 plan — per the
composition the county prints on coboard.aspx, asserts each district against
the plan's printed populations (nine of eleven to the person; the map's
totals sum to the county's exact 20,990, so a mis-transcription cannot
balance), and carries the Shelbyville 4/5 sliver exactly as the record
prescribed: the two edges land in different districts, so **both D8 and D11
carry a boundaryNote** naming the ±16.

**The new machinery is the split.** Shelbyville 5 wraps the county seat and
goes three ways — D8 south of Rt 16, D9 north-east of Lake Shelbyville, D10
north-west — the first precinct in the fleet cut into three pieces, and cut
by LANDMARKS the county names rather than by a meridian (Jefferson's 34th
Street was two pieces, one longitude). Both instruments are public geometry:
the Rt 16 corridor from TIGER secondary roads (through downtown the route is
"W Main St"/"E Main St", so the corridor is three names merged, sampled as
the median of the twin strands), and the lake from TIGER areal hydrography
with the Kaskaskia River carrying the divider below the lake's southern tip.
TIGER maps no linear river through the ~1.4 km dam reach, so the divider is
bridged straight — an approximation that crosses **zero populated census
blocks**, disclosed on both cards. The cut is adjudicated at census-block
level, not by eye: Shelby's 2,605 blocks sum to the county's exact
population, the 86 inside S5 to its exact 818, and the three pieces to
**605/158/55 exactly** — the values that reproduce the plan's printed 1,948
(D9) and 1,833 (D10) to the person. The sharpest single check is one block:
the only populated block in the dam reach (pop 1) must land west of the
divider, because the county's own arithmetic says 55 = 54 + 1. It does.

The roster (22 seats, two per district) ships with a cross-check no other
county needed because no other county publishes its roster twice: every
contacts.aspx directory row must match a coboard.aspx card seat by e-mail
and name, both role aliases must land on the members the cards tag Chair and
Vice Chair, so a mid-edit site fails the weekly job instead of shipping
whichever page the scraper read. District 7's two seats are **"Currently
Vacant" and ship that way** (the Bureau rule); home addresses are printed on
every card and are not even captured by the scraper (the Mason/Marshall
rule). The weekly job re-parses the composition, split pieces included — a
redistricting fails CI, the DeWitt pattern.

**The ring event is a double.** Shelby borders Macon and Montgomery on the
mainland AND Effingham, so the first island (2026-08-04) merged back in —
and the same join enclosed CHRISTIAN, whose neighbours (Sangamon, Macon,
Shelby, Montgomery) are now all served: the wash's second doughnut beside
Bureau, held OUTSIDE by a new Taylorville anchor. Four rings across two
polygons — the same four rings as before Shelby, differently distributed.
Islands can un-island and enclaves can appear in the same stroke; the
dissolve is recomputed, never patched.

One process lesson repeated itself with a new layer id: the census-blocks
fetch was first pointed at tigerWMS_Census2020 **layer 12** on a guess and
returned three features — the same false-negative shape as the layer-58 VTD
guess and the FULLNAME field guess before it. The service's own layer list
says blocks are **layer 10**; one metadata request before concluding remains
cheaper than any amount of debugging a wrong assumption.

### 2026-08-17: Wabash ships as the 61st county — the island grows, and the names only the Clerk could send, she sent

`wabash-county-board`'s wanted line asked for *"just the three commissioners'
names"* and its blocker established that the county clerk was not merely the
easiest source but the only one. That is exactly how it closed: six hours
after a follow-up, County Clerk & Recorder Janet L. Will's e-mail carried
Timothy R. Hocking, Robert G. Dean and Scott C. West. Wabash ships on the
County card as the SECOND `DOCUMENT_ROSTERS` county — a mail domain with no
web server can never be scraped, so the roster is carried from her e-mail with
the source named, a verification date attached, and the weekly NOT RE-READ
line saying so out loud. The Edwards mechanism, second use, exactly as that
entry predicted it would be reused.

**What ships is less than what arrived, by rule.** Her e-mail gives each
commissioner a HOME address and nothing else; the Edwards rule (a card must
not publish a private home) withholds all three, and unlike Edwards this
county assigns no per-seat e-mail, so each row is a name alone. Nobody is
marked Chairman: the e-mail does not say, the question has been asked, and a
guessed chair is exactly the invented fact the honesty rules exist to prevent.

**Ring work.** Wabash borders Edwards and nothing else served — Lawrence and
White are frontier — so the one remaining island GROWS to two counties rather
than a second island forming: `metro-outline.json` stays two polygons and four
rings (the Bureau and Christian enclaves unchanged), Mt. Carmel anchors
INSIDE, and Carmi (White) still holds the southern corridor OUTSIDE. Counts:
61 served — 49 dispatch, 3 judicial, 9 County card.

**A drift found in passing.** Rebuilding the roster re-read every scraped
county: ten parsed byte-identical to the shipped file, and PIKE parsed 0 of 9
from a live 200-status page — pikecountyil.gov's board page has changed shape
since it was last read. Pike ships unchanged in this build (carried forward
from the shipped file, not re-read), and the weekly run will fail loudly on
it; the parser repair is its own change, not smuggled into this one.

`wabash-county-board` is retired; `wabash-precinct-geometry` succeeds it,
carrying forward the no-website measurement and the Indiana-decoy warning,
because the precinct half of the 5 Aug question is still open with the Clerk.

### 2026-08-17: De Witt's last gap closes from the Clerk's filing cabinet — the third document-carried municipal county

Adam's Aug 3 ask named the municipal list "the final gap" for De Witt; Clerk
Kari Harris's Aug 17 reply delivered it as two attachments with no body text —
the delivery WAS the attachments. The city/village list ships: 7
municipalities, 52 officials, 7 heads, via a new document-carried scraper —
the third, after Marshall and Washington — reading the archived .docx with
stdlib alone. The Washington privacy rule held by construction (names via the
name-shape allowlist; the clerk's per-person home addresses never had a path
into the payload; the only contact shipped is each municipality's own
published number), and the source's own "(NOT ELECTED)" / "(ACTING)" / "(APPT
IN JUNE 2025)" markings carry as `appointed` so no card implies an appointee
was elected. Two vacancies print as vacancies; a water clerk and a part-time
clerk are staff and stay out.

**The township list waits its turn, on purpose.** The same reply carried a
township-officials PDF (updated 8-4-2026), archived beside the build source
and deliberately unbuilt: township officials are not a concept any fork
carries, and the PDF's two-column text extraction decouples role labels from
names in several townships — shipping it would mean guessing attributions, and
a new concept is a Part 5 decision, not an improvisation.

**A plumbing fact worth naming, because it will recur:** the Gmail connector
cannot download attachments. The working bridge is the operator clicking
"Add to Drive" on the message, after which the Drive connector reads the file
— that is how both De Witt documents arrived, and the hourly reply-check now
checks Drive for bridged county files every run.

### 2026-08-17, afternoon: the two heads WinGIS never published, from the election authority's own e-mail

`winnebago-village-heads` recorded the fleet's oddest absence — two
municipalities showing complete councils and no mayor, because WinGIS
publishes no head-of-government layer for Loves Park or Machesney Park. The
county's elections office closed it in one reply: Mayor Greg Jury (Loves
Park) and Mayor Steve Johnson (Machesney Park), the latter titled MAYOR by
the county's own ballot heading even though Adam's ask said "village
president" — the county's word ships. The two ride `EMAIL_CARRIED_HEADS` in
the Winnebago scraper rather than a layer: the heads floor rises 9 → 11, the
weekly run prints a NOT RE-READ line per head naming the e-mail and its age,
and the reply's home addresses ship nowhere. The roster diff was two entries,
each gaining exactly its head. The record is retired outright — nothing
succeeds it, because nothing about Winnebago is now missing.

### 2026-08-17, evening: White ships as the 62nd county — the last island merges, and the tracing that proved it didn't need to ship

`white-county-board`'s wanted line asked for a Stephenson-style tracing —
"trace the board districts and precincts from the county's own vector PDF" —
and the build did exactly that tracing, then shipped something stronger. The
map's only vector linework is its DISTRICT lines (the precinct fills are
burned into the raster base; most of the record's "18,600+ path operators"
are text halos), but the county panel's red network polygonizes into exactly
5 faces, one district numeral each, and TIGER's Census 2020 voting districts
carry the county's 18 precincts EXACTLY — 18/18 by name, populations summing
to the county's 13,877 to the person. The Carmi inset settled which fabric
the county drew from: anchored by its own scale bar, every one of its 1,104
sampled line points sits within 35 m of the census district edges, median
1.9 m. So `scripts/build_white_boundaries.py` ships exact census fabric, and
the traced map decides only the COMPOSITION — the Shelby shape, reached by
doing the Stephenson work and measuring that it wasn't needed.

**The composition is proven three independent ways, and the roster fell out
of the proof.** The traced faces assign all 18 VTDs (worst share 99.06%,
county-panel fit median 15.8 m / RMS 33.6 m); the county's certified 2022
General Election canvass — the first on the 2021 map — tabulates all five
COUNTY BOARD MEMBER DISTRICT contests by whole precinct and agrees 18/18;
the inset agrees at ~2 m. The same canvasses answered what the board page
never says: WHICH district each member represents. All five 2022 winners
(South D1, Cannon D2, Usery D3, Pigg D4, Spencer D5) are the five names on
today's board page, parties matching, districts 3-4 re-confirmed by the 2024
canvass. The weekly scrape (`build_white_county_board.py`) joins page names
to that certified table, surname + first initial, unique match required —
any unplaceable name fails the run, because a new member's district is a
fact only a new certified document can supply. Polling shipped the same day:
the Clerk's own Elections-page list, 11 buildings covering 18/18 precincts,
place-and-address as the one string the county prints. Board contact ships
ONCE at board level (one PO Box, one clerk e-mail for five members — the
Calhoun switchboard rule). Balance closes the loop: five "Vote for one"
contests, populations within 2.33% of the one-member ideal.

**The ring event: the last island is gone.** White borders Hamilton on the
mainland side and Edwards AND Wabash on the island's — the same island
Wabash had grown that morning — so the dissolve was recomputed (never
patched) and `metro-outline.json` dropped from two polygons to ONE: three
rings, the outer plus the Bureau and Christian enclave holes. Carmi moved
from OUTSIDE (where it had proven the islands stayed two since 2026-08-06)
to INSIDE, failing the build until it moved, exactly as designed;
Shawneetown (Gallatin) inherits the southern-frontier watch and Fairfield
(Wayne) now proves a NOTCH rather than a corridor. Counts: 62 served — 50
dispatch, 3 judicial, 9 County card.

**Deliberately not shipped:** the tracing itself (census fabric is exact
where a georeference is ~16-34 m; the tracing survives as the builder's
composition proof), any fire/park/library tiling (no known source — the
successor record `white-special-districts` carries the measurement), and
White's municipal officials (unresearched this change; the §2.4 ladder is
future work, recorded here rather than implied).

`white-county-board` is retired; `white-special-districts` succeeds it,
carrying forward the fragile-mail note and the "one map file" measurement.

### 2026-08-17, night: Jo Daviess ships as the 63rd county — the first boundary this project ever BOUGHT, and the first licence-gated county cleared

`jo-daviess-county-board-districts` was the gap no free route could close, and
its own record said so precisely: 14 of the 17 districts are made of PARTS of
precincts, District 10 is a fraction of a single one, the county's 2021 mapping
memo split along ROADS, every published map is a raster export, and the GIS
viewer has no REST surface. So when GIS Technician/Website Administrator Diane
LaScala priced the export on 17 Aug — labor ½ hour $25.00, 17 polygons at
$0.50 each, **$33.50 total**, invoice and SIGNED LICENSE AGREEMENT required —
the price was never the question. **The licence was**, because Bureau had
already taught what a quote under redistribution-forbidding terms is worth: a
block, at any price. Licence #008382's Protection of Proprietary Rights clause
IS the Bureau clause — redistribution of the dataset and derived products
forbidden — with five words that change everything: *"without permission from
JoDavGIS."* Asked BEFORE anything was signed or paid, IT/GIS Director Joe
Kratcha put the permission in writing the same morning: *"Please let this
email serve as official authorization, in addition to the signed license
agreement, granting you permission to display the requested Jo Daviess County
Board District boundaries to be provided in shapefile format on your website:
chidistricts.com for public viewing."* The operator signed and paid online the
same day; LaScala delivered the five shapefile components by e-mail at 15:34Z
("Thank you Adam. Attached are your files"); Jo Daviess shipped that night.

**The licence shapes the artifact, and the deviation is deliberate.** The
authorization covers DISPLAY on chidistricts.com — which the simplified
`data/app/jo-daviess-county-board-districts.json` is — not republication of
the raw dataset. So, for the first time, a county's source file is NOT in
`data/source/raw/`: the originals are retained offline (the operator's Drive
and the session archive), and `scripts/build_jodaviess_board_districts.py`
records each component's byte size and sha256 (shp 4,813,436 / shx 236 /
dbf 2,017 / prj 508 / csf 10,240 bytes) so a re-supplied copy can be
authenticated against the licensed delivery. Rebuilding therefore needs the
offline directory (`--source`), and the builder refuses a component that
hashes differently. The Credits clause is honoured where a reader can see it:
the card names Jo Daviess County GIS on every render.

**The build proves the purchase was what it claimed.** The dbf carries
`CtyBrdDist` "DISTRICT 01".."DISTRICT 17" each exactly once — and `CtyBrdMemb`
DECLARED AND EMPTY on all 17 rows, which the builder asserts and reads
nowhere: members come from the county's board page weekly, never a static
column. Reprojected from the .prj's NAD83 / Illinois West ftUS (EPSG:3436)
with pyproj, the full-precision districts tile TIGER's Jo Daviess County at
**99.9327%** with a worst pairwise overlap of **0.3 m²** — edge-matched as
delivered, the Menard class. Simplification is the repo's own tool (pinned
mapshaper, Visvalingam keep-shapes at 25 m) with a `-clean` pass either side —
without the first, the source's 280 hairline slivers pin the vertices and
4.8 MB of shapefile refuses to shrink below ~1 MB; with it, 49.5 KB — at a
measured cost of **0.6 m median / 54 m max** boundary movement, 2,000/2,000
seeded sample points classifying identically to full precision, zero
overlap left, coverage 99.9335%, and 0.125% symmetric difference against the
county outline the coverage test uses. Deterministic: `--check` byte-compares
a fresh rebuild from the licensed bytes.

**The roster came free where the boundary cost $33.50.** The county's board
page (on jodaviesscountyil.gov — NEVER the old jodaviess.org, which answers
every URL with its home page) lists all 17 seats with party, term and a
precinct-parts description, and links 16 member directory pages carrying a
direct phone and an e-mail each — 16 DISTINCT numbers, so the Calhoun
switchboard test was run and does not apply, and personal gmail/icloud
addresses ship exactly as published. District 16 is printed VACANT and ships
as a counted, never named vacancy (the Livingston posture). The weekly
scraper cross-checks each directory page against the board page on district
number and surname + first initial (unique, asserted), paces its seventeen
fetches, and never parses the home addresses the directory pages print (the
Madison/Peoria rule). The count guard counts SEATS — named + vacant = exactly
17, districts 1..17 each once, the district set asserted against the boundary
module's constant — so the weekly run doubles as the reapportionment
tripwire: new lines would need a NEW licensed export, an operator step the
workflow's PR body says out loud.

**The ring event: a corner completes.** Jo Daviess borders served Stephenson
and Carroll, so this is a plain mainland join — 3 rings before, 3 rings after
(the outer plus the Bureau and Christian enclaves) — and Galena moved up from
OUTSIDE, where it had held the north-west corner since the Lee/Whiteside/
Rock Island/Henry tranche, failing the build until it moved, exactly as
designed. For the first time a newly served county leaves NO unserved
Illinois neighbour behind: everything Jo Daviess touches is Stephenson,
Carroll, Wisconsin or the Mississippi, so no successor OUTSIDE anchor exists
for its corner and none was invented. Counts: 63 served — 51 dispatch, 3
judicial, 9 County card.

**Deliberately not shipped, stated rather than implied (no successor gap
records were invented for surfaces this change did not research):** the
county's PRECINCTS (pass 5e measured the county's GIS as a vendor viewer with
no REST surface and every published map raster; whether the county would sell
a precinct export under the same licence machinery was NOT asked this change
— the board thread is the obvious place to ask next); fire/park/library
tilings (never researched for this county); municipal officials (the §2.4
ladder, unresearched); and the board page's precinct-parts district
descriptions (the scraper reads them only for the district NUMBER and ships
no prose — the purchased polygons are the authoritative geometry, and a
prose composition beside them would invite the reader to reconcile two
surfaces this project already has).
The retired record's full licence story survives verbatim in this entry and
in the builder's header; `jo-daviess-county-board-districts` itself is
retired outright.

## Backlog — researched candidates, deliberately not (yet) built

Every entry cites where it's recorded and the blocker. When one ships, move it into the
matrix; when one is rejected, move the rationale into a NO HONEST ANALOG footnote.

> **Read this first — what is actually open.** Most of what follows is a *completion
> log*, not a queue: an entry titled "… — SHIPPED/FIXED/RESOLVED (date)" is a record of
> work already done, kept for its rationale. Grepping this section for open work returns
> mostly noise, which is why "what's next?" is hard to answer from it. For "where does
> county X stand?" don't grep at all: `docs/COUNTY_STATUS.md` is the GENERATED per-county
> join of the coverage-ring lists, the dispatch tables and the gaps block (service tier,
> board posture, entries, open gaps) — start there, come back here for rationale. As of
> **2026-08-02** (RESEARCH PASS 7 and its build tranches, below) the open items split
> cleanly into work that is ready and gaps that need a publisher:
>
> | Open item | Blocker | Actionable? |
> |---|---|---|
> | **Winnebago voting precincts, free and public** (found 2026-08-05 while measuring what Stephenson's Clerk meant by "GIS" — see the ask ledger) — `maps.wingis.org/public/rest/services/WardsAndDistricts/MapServer`, no token, layer 7 **WinCo Voting Precincts**, alongside Winnebago County Board, political townships and the Rockford/Loves Park/Machesney Park ward layers. Winnebago is a served county that ships **no precinct layer**. The same host's `ElectedOfficials` service carries per-municipality officeholder layers (already the source behind Winnebago's municipal roster) | none found — the service is open and answers unauthenticated | **yes — a build, not a research question** |
> | **The ISBE precinct-map collection** (found 2026-08-05 via Hamilton's Clerk — see the ask ledger) — `elections.il.gov/PrecinctMaps/<County>/`, **98 of 102 counties**, open directory listings. A 14-county sample measured **3 vector / 11 scan**, so the lead is the vector subset (Knox, Menard, Williamson confirmed so far). Knox's and Menard's files were checked and CONFIRM their existing gap records (2011 content; raster) rather than closing them | needs a per-county download-and-extract pass to find which counties' maps are vector AND current | **yes — a cheap research pass, unstarted** |
> | ~~**Pass-14 first fruit — Hamilton**~~ **SHIPPED 2026-08-05, the forty-fifth dispatched county and SECOND island**, four hours after its Clerk's four-minute reply settled the at-large question and surfaced the county's vendor-hosted GIS org: precincts 17 (one unnamed — `hamilton-unnamed-precinct`, asked back) + fire 3 named as dispatch entries; the five-member board rides the County card from the weekly commissioners scrape of the county's own new site. `hamilton-precinct-polling` CLOSED 2026-08-11 — the county's post-migration site published the Clerk's statutory GPE polling notice, all sixteen pairings (see the ask ledger). STILL OPEN: `hamilton-municipal-officials` | nothing | done — one live ask recorded |
> | ~~**The pass-13 build-ready ledger** — Effingham~~ **SHIPPED 2026-08-04, same day — the forty-fourth dispatched county and the FIRST ISLAND** (§2.5.1 checklist exercised: metro-outline.json is now a MultiPolygon, the island proven an OUTER ring by anchor, the Vandalia/Shelbyville corridor proven washed): board 9 districts A–I with the roster ON the features (no scraper — the county's own live service is the officeholder source), precincts 38 (polling 38/38), fire 17, park 4, library 1. The build's verification also caught findPropCI's lowercase-candidate contract being violated by six `keys:` entries — Macon's fire/park/library cards had shipped reading "Unknown" — fixed in the same change. STILL OPEN: `effingham-municipal-officials` (12 municipalities, no councils source) | nothing | done — municipal officials stay a recorded gap |
> | ~~LaSalle county-board rebuild~~ **SHIPPED 2026-08-01** — boundary derived from the county's precinct layer per its full 2024+2026 canvass record; weekly directory roster with the countywide Chairman; 11 split precincts drawn with their majority side and stated on the card | remaining: the split-precinct cut refinement, or the county publishing its adopted map as GIS | done — refinement recorded |
> | **The pass-7 build-ready ledger** (RESEARCH PASS 7, below) — ~~Peoria + Tazewell~~ **SHIPPED** (29th/30th), ~~Iroquois + Monroe + Randolph~~ **SHIPPED** (31st-33rd, the at-large posture's debut), ~~De Witt~~ **SHIPPED** (34th), ~~Washington~~ **SHIPPED** (35th), ~~Cass~~ **SHIPPED** (36th), ~~Marshall~~ **SHIPPED** (37th), ~~Mason~~ **SHIPPED** (38th) — the derivation tier is COMPLETE. ~~Pike + Putnam + Brown + Calhoun~~ **SHIPPED** (the at-large tier — served through the County card, no dispatch entries). **Champaign + Piatt WITHDRAWN — licensed, not open** (see the tranche-2 entry). STILL OPEN: nothing from pass 7 — the ledger is CLEARED | nothing for the open tiers — every source measured live 2026-08-02 | **yes — the live work queue** |
> | **The pass-6 build-ready ledger** — ~~8 counties' municipal-officials sources~~ **SHIPPED 2026-08-01** (Grundy, Livingston, Logan, McLean's three ward cities, Sangamon, Madison, St. Clair, Rock Island — the roster grew 360 → 492 municipalities; McLean's county-wide Airtable route stays open, see its row); ~~4 precinct counties + 3 polling/naming joins~~ **SHIPPED 2026-08-02**; ~~Woodford's board~~ shipped with the county 2026-08-02; ~~3 board-geometry builds~~ **ALL SHIPPED 2026-08-02** (Boone + Grundy + Henry — Henry as the twenty-eighth county), ~~the Logan board roster scraper~~ (SHIPPED 2026-08-02), still open: Aurora per-seat contact (re-measured 2026-08-02: Akamai 403s every rung reachable from CI — see its ledger row), ~~2 fire tilings~~ **SHIPPED 2026-08-02** (Sangamon 29 FPDs + St. Clair 44, each with its recorded caveat on the card), ~~Stephenson fire~~ **SHIPPED 2026-08-02** (georeferenced; its park/library maps measured RASTER-baked — see the new gap), ~~the verified city ward layers~~ **SHIPPED 2026-08-02** (22 cities across 13 sources; Lake Forest + 4 DuPage cities still to chase — see the ward ledger) | nothing — every source verified live 2026-07-31 | done — Aurora per-seat contact is the one open remainder |
> | ~~**Woodford County**~~ **SHIPPED 2026-08-02 — the twenty-seventh dispatched county**: board (3 DERIVED districts per Ord 2020/21 #005 + 15-member weekly roster with phones and e-mails) and precincts (TCRPC, 37, polling 37/37); its fire/park/library absences were already recorded (woodford-special-districts) | — | done |
> | The 64 no-source + 5 blocked + 16 data-quality gap entries — **85 in all as of 2026-08-02** (fire/park/library tilings in a dozen counties, precinct geometry or polling assignments in seventeen counties and cities, ward geometry in nine cities, three municipal-officials counties, and the frontier boards incl. the two Champaign-consortium counties whose data is sold rather than published). Every entry was rewritten in plain language on 2026-08-02 for the reader who could actually close it | publishers — each entry's `wanted` says exactly what | no — recorded, panel-visible |
> | McHenry / Kendall / Joliet | hard WAF denies (the two board directories now have verified 2026 Archive captures; McHenry's yearbook page and Kendall's municipal PDF still don't) | no — rule-4 terminal |
> | DuPage municipal phones; Will's `party` field | unchanged (re-verified 2026-07-31); deliberate non-ship | no |
>
> **The Illinois *concept* frontier is closed — the *geographic* one is not.** Of the 40
> concepts in the matrix above, Chicago ships 35; the other five are correctly
> `n/a`/NO HONEST ANALOG (NYC-specific constructs, a countywide State's Attorney, and
> appointed transit boards). There are no unfilled cells. So growing Illinois means
> either *more counties for the concepts already built* — see RESEARCH PASS 7 below,
> which is the live candidate list — or *proposing new concepts* under
> `docs/EXPANSION_GUIDE.md` Part 5 (community college districts, Regional Offices of
> Education, sanitary/drainage districts and township road districts are the unresearched
> families).

**Open — Illinois**
- **RESEARCH PASS 13 (2026-08-04) — the detached sweep: all 29 never-researched counties
  probed the day contiguity retired; one build-ready (Effingham — SHIPPED the same day as
  the first island, see the ledger row above), one districted-with-roster (Franklin,
  geometry ask only), two Knox-style refuse-all sites (Union, Williamson), ten live
  websites, zero self-hosted GIS.** Full
  findings in the ask ledger's pass-13 section; per-county records in the gaps block
  (every one of the 29 now carries a gap record and an outline, so COUNTY_STATUS's
  unresearched tier is EMPTY — the whole state is now either served, or recorded with a
  reason). The board-form question (districted vs at-large) is open in 24 of the 29 and
  is a certified-document check, not a website check (§2.5 step 2).
- **RESEARCH PASS 7 (2026-08-02) — the frontier REOPENED: twenty-five counties now adjoin
  the served ring; surveyed six ways in parallel. Eight build-ready, four cheap at-large
  adds, ten partial, three blocked.** PASS 5h's "expansion by adjacency has run out" was
  true of the ring it measured and expired the moment Woodford, Henry and the
  judicial-secondary counties (Bond, Jersey, Greene, Morgan, Scott) joined it: recomputing
  adjacency from TIGER county geometry against the full 33-county `METRO_COUNTY_FIPS` set
  finds 25 unresearched counties sharing a real edge with the served area — only Bureau,
  Mercer and Jo Daviess remain researched-and-blocked (source-request emails for all
  three, plus twelve other recorded gaps, were drafted 2026-08-02). Survey depth per
  county: official domain → GIS of record → board geometry + roster → precincts → crawl
  posture; every feature count below was measured by querying the named layer.

  **Build-ready — full county adds (geometry + roster machine-readable today):**

  | county (pop) | board | geometry | precincts | notes |
  |---|---|---|---|---|
  | Peoria (~182k) | 18 districts × 1 | own AGOL org `iPiPjILCMYxPZWTc`: `2020_County_Board_Districts/FeatureServer/0` = **18** (adopted 2021-11-30) | `2020_Voting_Precincts` = **116** (edited 2026-06) + 55 polling points joining on `POLLINGID` | fire **13** / park **4** / library **10** / townships 26 / school 20 on the same org; roster = CivicPlus page, per-member profiles, no party on the index |
  | Tazewell (~131k) | 3 districts × 7 + countywide Chairman | Esri election template — `ElectionGeography_public…/FeatureServer/2` carries 21 County-Board member rows WITH party and district polygons (the Whiteside pattern; edited 2026-01) | layer 1 = **82** + 49 polling points (counts cross-checked on the on-prem `Clerk` folder) | per-municipality `*_Officials` services ≈ a GIS municipal directory (~15 munis) + 153 township-official and 126 school-board rows on the same layer; **one-seat GIS-vs-website drift** (Longfellow D3+Phillips vs D2+Glueck) — the roster scraper must tie-break; old domain tazewell.com is dead but still cited in stale GIS attrs |
  | ~~Champaign (~206k)~~ **WITHDRAWN — LICENSED** | 11 × 2 | CCGISC `CountyClerk/CountyBoard/MapServer/0` = **11** | `CountyClerk/Precincts` = **118** | The sweep called this BUILD-READY on fetchability alone. It is not buildable: **CCGISC SELLS Champaign and Piatt GIS data under signed licence agreements**, and its Terms of Use grant only personal, non-commercial, transitory viewing — no copying, no public display, no mirroring on another server. The referer lock is the edge of that licence, not hotlink protection to route around. Recorded as `champaign-piatt-ccgisc-license`; a rich taxing-district shelf (fire/library/park/cemetery/mass-transit/forest-preserve) sits behind the same licence. (champaigncountyclerk.com is separately UA-filtered — plain clients 403, browser UA passes.) |
  | ~~Piatt (~17k)~~ **WITHDRAWN — LICENSED** | 3 × 2 | CCGISC `Piatt_CountyClerk/CountyBoardDistricts/MapServer/0` = **3** | `Piatt_CountyClerk/Precincts` = **16** | Same licence, same consortium — CCGISC is Piatt's GIS of record too, so ONE licensing block covers both counties. Roster carries no party. (Moved-domain trap either way: the old piattcounty.org apex is dead while `maps.piattcounty.org` lives.) |
  | Iroquois (~27k) | 4 × 4 | CCAO org `6FZQl5a5SiSFMv8P`: `CountyBoardDistricts_REACH/FeatureServer/8` = **4** (item 2024-12) | `ElectionGeography_public/FeatureServer/1` = **37** + polling points (layer 0) | fire **46** / school **13** / municipal wards **7** / townships 42 on the same org; use the APEX domain with a browser UA (www 403s); roster e-mails are cf-obfuscated (mechanically decodable); the org's "Electoral Districts" layer has the rich rep-name schema and **0 features** — never populated, don't rely on it |
  | Monroe (~35k) | **COMMISSION — 3 commissioners at-large** | none needed — county outline is the geometry | `VoterPrecinct/FeatureServer/0` = **25** (geometry reloaded 2026-03 — freshest of the pass) | own ArcGIS Enterprise 11.5 + AGOL mirror; fire **26** / municipal wards **23** / school 5 / road districts 20 / polling 16; EWG's 2026 POD covers Monroe municipals but its commission rows are stale — the county page is the authority |
  | Randolph (~30k) | **COMMISSION — 3 commissioners at-large** | none needed | `VotingPrecincts/FeatureServer/1` = **35** (layer id **1**, not 0; edited 2026-04; ISBE's 37 per-precinct vector PDFs corroborate names) | ESB_FIRE = 17 is response-zone semantics (the Winnebago/Logan caveat — not a taxing tiling); municipal wards 9; the old `am.randolphco.org` still serves a stale Joomla site while staff e-mails stay @randolphco.org |
  | De Witt (~16k) | 4 lettered districts (A-D) × 3 | **DERIVED**: the roster page prints the full official composition and it assigns ALL 23 precincts — dissolve the live precinct layer | `ElectionPrecincts_DeWittIL/FeatureServer/0` = **23** (Sidwell/Magnasoft org; schema is 2020-VTD but names match the county's current compositions verbatim) | roster has phone/e-mail/committees and NO party; the org's fire layer is 466 undissolved section-level slivers (needs dissolve if ever shipped) |

  ~~**At-large boards — cheap adds**~~ **SHIPPED 2026-08-02 (tranche 5)** — Pike (~15k, 9
  members), Brown (~6k, 7), Calhoun (~4k, 5) and Putnam (~6k, 5): 26 members on the County
  card, no dispatch entries, no toggles, no engine change. What the build found beyond the
  sweep:

  - **The sweep's "at-large" call was under-evidenced and had to be re-proved.** It rested
    on board pages that never say "district" — which proves nothing. Each county was
    re-checked against a certified election document first: Pike's 2024 general summary
    names the contest **"FOR COUNTY BOARD - AT LARGE"** across all 31 precincts, Brown's
    2026 primary shows **"COUNTY BOARD MEMBER (VOTE FOR) 3"** countywide across all 14,
    and Calhoun's 2026 ballot file reads **"CO.COMMISSIONER CWD"**. Putnam keeps the
    sweep's specimen-ballot finding, now cited in the scraper. Rule recorded in
    EXPANSION_GUIDE §2.5.1.
  - **Putnam's board page links five member profiles; all five 404, and TWO point at a
    member who has left the board** (a ", Vice-Chairman" fragment split off one row, and
    another member's whole row). The visible text is correct and maintained; the hrefs are
    not. Exactly inverted from St. Clair, where the caption is wrong and the URL right.
  - **Brown marks one member's phone `mail:` where every other row has `tel:`** — reading
    phones out of hrefs silently drops him. Brown also publishes all seven members' HOME
    ADDRESSES; none is collected.
  - **Calhoun prints the same number, 618-576-9700 ext. 2, under all five commissioners** —
    a switchboard, not five direct lines, so it is hoisted to the board office row and
    shown once (the Monroe posture). Calhoun is also the tier's only county with a term
    fact ("Term: YYYY to Present"), rendered as "Serving since YYYY".
  - **Pike's widen fired as predicted**: measured west edge −91.3701, so metro_bbox went
    −91.15 → −91.55 and permalink_gate −91.25 → −91.65.
  - **Domain traps confirmed live**: `browncountyil.org` is a captcha-parked DECOY (the
    county is at browncoil.org); Calhoun needs the `www` host; and Putnam has MOVED to
    **putnamil.gov** — the `co.putnam.il.us` host the sweep recorded as a dead legacy
    domain now fails to resolve entirely.
  - All four counties' precinct geometry is raster- or document-only, now recorded as four
    gaps (`pike-`, `putnam-`, `brown-`, `calhoun-precinct-geometry`).

  **Partial — board derivable now, something else missing:** **Washington** (~14k — 3×5
  by WHOLE-township composition printed on the board page → TIGER dissolve, the Woodford
  route; precincts raster-only), **Marshall** (~12k — 3×4 whole-township composition on
  the county's 2026 roster PDF; 14 precincts PDF-only with two municipal splits),
  **Mason** (~13k — 2×4 township composition WITH party on the county's May-2026 roster
  PDF; precincts: TIGER 2020 VTDs match the current 21-precinct list **21/21**),
  **Cass** (~13k — 4×3 by precinct-union composition in a county vector PDF; TIGER VTDs
  match **21/21**), **Macon** (~104k — **one artifact from build-ready**: its
  `ElectionGeography_public…/2` holds the correct five post-2022 district polygons with
  EVERY attribute NULL, so the districts need labels from the clerk's map or the adoption
  ordinance; precincts = **64** + fire **17** / library **10** / park **6** are ready
  today; its site soft-404s unknown paths with a 200 stub — content-verify every hit),
  **Clinton** (~37k — 5×3; precinct layer = **34**, current, polling table matches 34/34;
  the 2022 district map is a text-extractable vector PDF drawn over its 15 townships; no
  district layer among its Sidwell org's 28 public services), **Fayette** (~21k — roster
  WITH party (12R/2D); an ArcMap-authored vector PDF carries districts AND its 28
  precincts, so the shapefiles demonstrably exist at Sidwell — request-or-digitize),
  | ~~municipal officials — Tazewell~~ **SHIPPED 2026-08-02, 22nd county on the Municipality card** | the County Clerk's yearbook on **tazewell-il.gov** (the app's own il-county-clerks.json named that domain; tazewell.com fails TLS at the gateway with a VALID cert and tazewellcountyil.gov does not resolve) | 16 municipalities, 141 officials, 16 heads — full governing bodies with hall address, website and e-mail. Read from word POSITIONS, not lines: on many pages the office titles and the names extract as separate blocks (Marquette Heights prints Mayor/Clerk/Treasurer/6x Alderperson, then eight names), so a line read pairs the wrong people with the wrong offices. Verified against a hand-read page before the parser was written and again after. ZERO phones ship: the yearbook prints 389 of them with no area code and states no default, so the DMMC rule nulls them all — Tazewell is entirely 309, but the document does not say so. Minier's vacant deputy clerk is counted and never named |
  | ~~ward — City of Peoria's 5 council districts~~ **SHIPPED 2026-08-03; the largest municipality the app districts outside Chicago and the collar (~113k)** | the CITY's own org (`services1/Vm4J3EDyqMzmDYgP`, "Council of Districts of Peoria"), not the county's | Follows directly from the Peoria municipal roster shipped hours earlier: that gave the city's five DISTRICT members and five AT-LARGE members, and this gives the districts they sit for. Seat label is **"District", not "Ward"** — `municipalSeatHolders` keys on the digit in the roster's district string, so "District 3" joins and "At-Large" correctly matches nothing, which is right: the at-large five represent the whole city and belong on the Municipality card rather than any one district's. **VINTAGE VERIFIED TWO WAYS.** By date: last edited May 2022, after the post-2020-census redraw, the same bar Moline and Silvis shipped on. And geometrically, which is the stronger check — the five districts cover **94.9%** of the TIGER place polygon, and the 5.07% they miss is the **Illinois River**: Peoria's own water share is **5.09%**, agreeing to two hundredths of a point. TIGER counts a city's water and a council map does not, so the districts tile the city's LAND essentially exactly. No two districts overlap (largest pairwise intersection 2.7e-9 deg²). **REPNAME is read nowhere** and this is the third stale officer column this pass: the 2022 layer names Chuck Grayeb in District 2 where the 2026-27 clerk directory names Alex Carmona, and the browser prober asserts that a click downtown returns **Carmona** and never Grayeb. Ward-coverage file 63 → 64 municipalities |

  | ~~ward — Whiteside's six municipalities~~ **SHIPPED 2026-08-03, the second gap this pass closed by a clerk's sentence** | the county's `PrecinctWardMap/0` (a DIFFERENT service from the `ElectionGeography_public` its precincts and board come from) | 21 wards across Sterling 4, Rock Falls 4, Morrison 4, Fulton 4, Prophetstown 3, Erie 2. Held back from the pass-6 tranche as gap `whiteside-municipal-wards` because the layer's last edit is **2016** and municipal wards are redrawn on the census cycle — publishing it risked answering "which ward am I in" with a pre-2020 line and no way for a reader to tell. The gap named two things that would settle it, the second being "confirmation from the county that these six municipalities did not redistrict," and County Clerk Karen Stralow wrote exactly that on 2026-08-03: *"The wards were not redrawn at the time of the census in 2020."* So the 2016 timestamp is stale metadata on a current boundary — the same posture as Rock Island's `Pop_2010`, and the second time in one day that a dated attribute turned out to describe the edit rather than the line. **21 wards on 22 polygons**: Fulton Ward 4 is published twice, both parts carrying the same name (the DeKalb Ward 7 / Rock Island Ward Two shape); the old gap's "Fulton (5)" counted polygons rather than wards, now corrected. `REPNAME` is declared and null on all 22 and the county yearbook stops at mayors and clerks, so **no alderperson is named** — the card gives the ward and links the municipality, the Quincy/McHenry-city floor. Ward-coverage file 57 → 63 municipalities. Verified in a browser at Sterling, Rock Falls, Morrison and Fulton, with an assertion that no officeholder is invented |

  | ~~whiteside-precinct-polling — CORRECTED, not closed~~ **re-measured 2026-08-03** | the county's own `ElectionGeography_public` L0/L1 | **The previous entry was wrong about which precinct.** It recorded 55/60 with "Coloma 9's polling place appears in none of the three" datasets. Live measurement says otherwise: Coloma 9 references facility 4, which the county publishes as **Rock River Christian Center** — and Clerk Stralow independently confirmed that venue by e-mail the same day ("Coloma 9 votes at the Rock River Christian Center and that should be updated on the layer"). The layer already agreed with her. An override keyed on her statement was written and then **reverted**, because shipping a hardcoded value for data that is already correct is dead code that rots silently. The real join is **56/60**, and the four that fail are Sterling 9, Sterling 14 and Sterling 18 (all facility 22) plus Prophetstown 1 (facility 26) — two buildings absent from the 29 published voting locations. Three of the four share one missing building, so publishing two records would close the whole thing. Gap rewritten to say that |

  | ~~municipal officials — Peoria~~ **SHIPPED 2026-08-03, 26th county, and the gap `peoria-municipal-officials` is CLOSED** | the Clerk's *Peoria County Officials & Services Directory 2026-2027* (DocumentCenter 295, linked from `/250/Service-Directory`) | **The gap said "no source at any rung", and it was a correct finding about the places looked at and a wrong conclusion about the county.** The pass-7 probe worked the usual order — election commission (publishes candidates, not seated officers), county phone directory (county staff), Tri-County RPC (no member roster), county GIS municipality layer (CORP_NAME and nothing else) — and concluded there was no equivalent to Tazewell's yearbook. There is; it is called a Service Directory, which is why no search for "officials" found it, and the Clerk's office named it the day it was asked. A related correction: the old blocker said Peoria "is run by an election commission rather than a county clerk". The ELECTION AUTHORITY is a commission; the county clerk exists (Rachael Parker, named on this directory's cover) and is who answered. 15 municipalities — the county's ENTIRE incorporated set — 140 officials, 15 heads, **27 ward/district seats**. This is the richest municipal source in the fleet: every place carries hall address, phone, fax, **e-mail AND website**, then head, clerk, treasurer and every governing seat. Four ward cities (Chillicothe 8, West Peoria 8, Elmwood 6) plus the City of Peoria's council of **five district seats and five at-large**, each labelled. Peoria is also the largest county on this card outside the collar (~180k; the city alone ~113k). Every field is a dot-leader row, so the parse matches a known LABEL and takes the rest of the line rather than splitting on dots — the leader collapses to nothing when a name is long ("District 3 Council Member: Timothy D. Riggenbach"), and one field prints with no colon at all ("Treasurer ....... Andrea Bredeman"). **Fire and police chiefs are deliberately skipped** (six municipalities list them): neither is elected, and a chief is a department rather than a government — the Logan call. Appointed MANAGERS are kept and flagged. Two "Vacant" trustee seats (Hanna City, Mapleton) counted and never named |

  | ~~municipal officials — Cass~~ **SHIPPED 2026-08-03, 24th county on the Municipality card** | the Clerk's 43-page *Cass County Directory*, linked from the front page of `co.cass.il.us` under a label that says nothing about officials (Clerk Shelly Wessel named it on request) | 5 municipalities — the county's ENTIRE incorporated set — 47 officials, 5 heads, **14 ward seats** (Beardstown 8, Virginia 6). Full governing bodies: head, clerk, treasurer AND every trustee/alderperson, from two facing tables. May 2026 edition with terms running to April 2027/2029, so it postdates the 2025 consolidated election. Read POSITIONALLY because the office titles wrap — "President of / Village Board" and "Village Treasurer / (Appointed)" each span two printed lines with a member's name on the first and their phone on the second, so a line read pairs the second line of one record with the first of the next. **The x-split is also the privacy mechanism**: both tables print each officer's HOME address in a column of its own, and that column is never read — discarding a coordinate range is a stronger guarantee than filtering strings afterwards, because no residence can reach the payload by being formatted unexpectedly. The municipal hall address still ships: it is printed in each section heading ("VILLAGE OF ARENZVILLE – 201 E. MAIN…"), which is the village office. Two page-selection bugs fixed before it shipped — requiring a heading to carry a dash AND an address (four later pages name a municipality in passing, which attributed a drainage-district board to the City of Virginia), and requiring "Term Expires" on the boards page (the table of CONTENTS also contains the words "City & Village Boards") |

  | ~~municipal officials — Whiteside~~ **SHIPPED 2026-08-03, 25th county, at the MAYOR-AND-CLERK tier because that is all the county publishes** | the Clerk's *Whiteside County Yearbook 2025-2026* (CivicPlus DocumentCenter 236) | 11 municipalities, 22 officials, 11 mayors + 11 clerks. Clerk Karen Stralow's wording was exact — the yearbook "has **some** municipal officials listed" — and its index confirms the limit: "Mayors of Whiteside County" p.41 and "City Clerks" p.43, with no trustees anywhere. So Whiteside joins the Kane/McHenry/Kendall/Carroll tier rather than as a full-body county. **The "(Office)" marker is the whole address rule, and it is the county's own distinction rather than an inference**: eight of the eleven mayors' rows end "Phone: … (Office)" and carry the city hall, while the three that do not (Coleta, Deer Grove, Tampico) carry something else — Coleta's mayor at 110 Summit St and its clerk at 211 S. Main are two different houses, not one village office. An address ships ONLY from a row the county marks; the other three ship name and phone and no address. **A collapse that lost real data, caught and reverted**: four of the eight halls print a DIFFERENT office line for the mayor than for the clerk (Rock Falls 815-622-1110 vs 815-622-1100; likewise Fulton, Prophetstown, Sterling), so those are direct lines at one hall rather than one switchboard — gathering "the" hall phone per place silently replaced each clerk's number with their mayor's. A place whose office-marked rows agree now gets a hall phone; a place whose rows differ keeps each officer's own |

  | ~~McDonough — board districts, precincts, roster~~ **SHIPPED 2026-08-03 (pass 9; the 40th dispatched county), and the pass-8 "no locatable public website" finding is RETRACTED** | the county at `mcg.mcdonough.il.us` (a subdomain, HTTP only, no HTTPS listener) + its GIS, which is hosted by **Western Illinois University** (`gis.wiu.edu/arcgis/rest/services/precinct_map`) rather than by the county | **The retraction first.** Pass 8 tried nine hostnames, none resolved, and recorded McDonough as having NO public website — "a different finding from 'blocked' and rarer than either". It was wrong, and no amount of further guessing would have fixed it: neither an HTTP-only subdomain nor a university-hosted GIS is reachable by hostname inference. Clerk Jeremy Benson supplied both in one reply, twenty minutes after being asked. 3 board districts × **7 members** = 21, 27 precincts, 27/27 polling places and addresses ON the feature. **Precinct geometry is only obtainable from /identify**: the layer is a JOIN (key `OBJECTID_12`, no Shape field) and its /query returns attributes with the geometry silently omitted — in Esri JSON and GeoJSON alike, for one feature or all 27 — while declaring `Map,Query,Data`, `esriGeometryPolygon` and `hasGeometryProperties: true`. identify also ignores `outSR`, so the polygons ship reprojected here from EPSG:3436 (pyproj, newly pinned; sibling layer 3 reprojects fine, so this is identify-specific). **Board districts are DERIVED even though the county publishes a board layer**, because that layer's attributes are corrupt: Districts 2 and 3 carry an identical Population (20,045) AND an identical Acres to eight decimals, District 1 has neither, and the two sum to 40,090 against a county of ~27,000. So the boundary is the 27 precincts dissolved per the composition the board page prints under each district heading — verified a PERFECT PARTITION before anything is unioned (4+12+11=27, every precinct named once, nothing unassigned) — and the county's own polygons are demoted to a geometric cross-check, which the derivation passes at **IoU 0.9996 / 0.9998 / 0.9998**. Two source defects the build caught rather than absorbed: Emmet is FOUR SEPARATE PARTS and a naive Esri-rings→Polygon read made three of them holes, collapsing it by 99.5% (caught by an area-drift guard, fixed by nesting rings via the shared `group_rings`); and Scotland is self-invalid at source, repaired with zero area change. The roster page is malformed HTML — District Three's Vicky Kipling has NO opening `<tr>` — so rows are split on `<tr>` **or** `</tr>` rather than matched as pairs; the 21-member floor is what caught her absence. Chair Eric Blakeley and Vice-Chair Mike Cox are badged, resolved by longest-prefix against the member list after two word-blacklist attempts each fixed one case and missed the other. **Every member's HOME ADDRESS is printed on that page and none is collected**: the scraper reads only the phone out of that cell, the builder refuses any field whose name looks like an address, and the browser prober asserts no street address reaches a card. 21/21 phones, 20/21 e-mails. Weekly workflow re-checks the composition AND the cross-check, so a reapportionment turns the job red rather than leaving the lines a cycle stale |

  | ~~ward — City of Rock Island~~ **SHIPPED 2026-08-03, and the gap was closed by ONE SENTENCE from a clerk** | the city's own org (`rigov`, `Wards_Map/FeatureServer/0`, last edited 2025-05) | 7 wards on 8 polygons (Ward Two is published in two parts, both carrying ID 2 — the DeKalb Ward 7 shape). The layer was held back from the pass-6 tranche and recorded as gap `rock-island-city-wards` for a reason that no amount of searching could resolve: the service was created in 2017 from a 2012 map, its only population column is `Pop_2010`, no post-2020 redistricting ordinance exists anywhere reachable, and the city code library that would carry one blocks automated access. The gap named three things that would settle it, the second being "a clerk's statement that the older wards were kept" — and City Clerk Amanda Torres wrote exactly that on 2026-08-03: *"The existing ward boundaries were retained after the 2020 census."* **That makes `Pop_2010` a stale ATTRIBUTE on a CURRENT boundary** — the city decided not to redraw — so the column is read nowhere rather than shown as though it described today, and the prober asserts none of the seven figures reaches a card. The layer's own `Alderman` column is also read nowhere (the Freeport / McLean-cities posture): the county clerk's roster already names all seven seats with terms and phones and is the certified record, while the GIS restates them in familiar forms ("Randy" for Randall, "Bill" for William) and is one un-edited election from being wrong. Only the per-ward directory URL, which the roster does not carry, is taken from the feature. Verified in a real browser at three points in three different wards: each card names the ward, the city, the alderman from the roster, the term, the phone and the ward page. Ward-coverage file 56 → 57 municipalities; the gaps block drops 88 → 87. **The lesson is the cheap one: a gap that no search can close is often one e-mail from closed.** |

  | ~~municipal officials — Henry~~ **SHIPPED 2026-08-03, 23rd county on the Municipality card, and the first unlocked by ASKING** | the Clerk's *Handbook of Elected & Appointed Officials* (CivicPlus DocumentCenter 1102, linked only from the left nav of `/221/County-Clerk` — the site's own search surfaces nothing) | 15 municipalities, 120 officials, 15 heads, 22 ward seats (Colona 8, Geneseo 8, Galva 6) — the county's ENTIRE incorporated set, full governing bodies with term-expiry years throughout. **The date is why it is publishable**: "Printed June 1, 2025, Updated January 29, 2026", i.e. after the April 2025 consolidated election. Line-parsed, not positional — every officer extracts on one line — but ANCHORED on the place list the mayors section establishes, because four sections spell the separator four ways (`ALPHA ----------`, `(V) ALPHA----`, `(H) BISHOP HILL—---` em-dash, `(C) GALVA-----–` en-dash, and a bare `V ALPHA 102 S 2nd St` where only a digit divides place from address). **Addresses come from the CLERKS OFFICES section alone** — the trustee rows print HOME addresses, and so do the mayor/clerk rows in the smaller villages (Alpha's president is listed at his house, the village office is elsewhere); every other section's address text is discarded unread, and Hooppole, absent from that section, ships with no address rather than its president's home. Only the five-digit ZIP is lifted from the discarded lines, because a ZIP names a town and not a household. Head TITLES are read from the trustee section's own headings (`City of Colona` → Mayor, `Village of Alpha` → President): the mayors section is headed "MAYOR OR VILLAGE PRESIDENT" and never says which is which, so labelling all fifteen "Mayor" would assert what the source declines to — 4 cities / 11 villages, matching the handbook's own C/V legend. Nine of the fifteen mayor/clerk "direct" phones are simply the village office line already carried under `office`, and are dropped rather than shipped as direct numbers. **Orion is the near-miss worth recording**: the handbook prints "Steve Newman" as head and "Stephen R. Newman" among the trustees, which reads exactly like a stale duplicate row — it is not. Orion's April 2025 winner could not take the oath, and the board elected a sitting trustee to the presidency, so he holds both offices and both rows are true. The head-duplicate rule is deliberately written to MISS this (surname plus a given-name truncation, and "Stephen" is not a truncation of "Steve"); a surname-only rule would have "fixed" Orion by deleting a seat the village really fills. Coal Valley goes to Rock Island on the precedence tie-break — Henry's own handbook marks its clerk "(R.I. Co.)" — so the county's net contribution is 14 |

  **MUNICIPAL BACKLOG, first pair probed (2026-08-02) — Peoria and Tazewell, the two
  largest served counties with no municipal officials.** Opposite outcomes. **Peoria: no
  source at any rung** (recorded as gap peoria-municipal-officials). Its election authority
  is a commission, which publishes CANDIDATES rather than seated officers; the county phone
  directory is county staff; Tri-County RPC — which covers Peoria, Tazewell and Woodford, and
  looked like the one source that could answer two counties at once — publishes no member
  roster at all (zero "mayor"/"village president" occurrences across every About page); and
  the county GIS Municipality layer is CORP_NAME and nothing else, the Lee shape, with no
  address, phone or officer to ship even at the contact-only floor. **Tazewell: BUILDABLE,
  and the domain was the whole obstacle.** tazewell.com fails TLS at the egress gateway
  (valid cert, handshake rejected — not a bot block and not fixable by disabling
  verification), and www.tazewellcountyil.gov does not exist. The county is actually at
  **tazewell-il.gov**, which the app's own il-county-clerks.json named all along via
  jcackerman@tazewell-il.gov — the SECOND time in one day the shipped clerk roster located a
  county that hostname guessing could not (see McDonough). Its Clerk's Yearbook (FULL-YEARBOOK-1.pdf,
  uploaded 2026-05) carries "OFFICERS OF CITIES AND VILLAGES OF TAZEWELL COUNTY" — full
  governing bodies with hall address, phone, website and e-mail. It needs POSITIONAL parsing,
  not line parsing: on many pages the office titles and the names extract as separate blocks
  (Marquette Heights lists Mayor/Clerk/Treasurer/6x Alderperson, then eight names), so a
  line-based read pairs the wrong people with the wrong offices — the LaSalle problem, and
  the LaSalle recipe (pdfplumber, y-banded at 3pt, split by x: office <128, name 128-282,
  contact >282) recovers every row cleanly. Two rules already in this file apply on sight:
  "Vacant" appears as a name (Minier's deputy clerk) and must be counted and never named, and
  the yearbook prints 389 phones WITHOUT an area code while stating no default, so those ship
  null under the DMMC rule — Tazewell is entirely 309, but mostly-true is not stated.
  **PASS-9 PROBE (2026-08-02), the three counties Adams and Schuyler made adjacent —
  all three are a LOW-GIS frontier, unlike Adams, and none is buildable from what is
  reachable today:** **Fulton** (~34k — the best of the three and still not enough: a live
  county site AND a dedicated elections domain, fultoncountyilelections.gov, carrying pages
  titled "Fulton County Election District GIS" and "Precincts and Polling Places". The GIS
  page contains NO map — no ArcGIS service, no KML, no PDF, only a tag-manager iframe — so
  the title promises a layer the page does not hold. 12 board-member e-mails are published,
  several of them personal gmail/outlook addresses, and no district label appears anywhere;
  whether the board is districted or at-large is UNDETERMINED and must come from a certified
  election document, not from the page's silence). **Hancock** (~17k — live site with a
  County Board Members page that renders its content client-side: 170 KB of jQuery loader
  with zero e-mails or district labels in the served HTML, so it needs a browser render this
  sandbox cannot give a live site. No AGOL items at all). **McDonough** (~29k — the county appears to have
  NO LOCATABLE PUBLIC WEBSITE, which is a different finding from "blocked" and rarer than
  either. Nine hostnames were tried and none resolves, including the one the ISBE clerk
  directory implies: jbenson@mcdonoughcountyclerk.org is the state's published contact, yet
  that domain has no A record — so it is e-mail-only or stale. DNS itself is fine in the
  probing environment (neighbouring fultoncountyil.gov resolves), so the failures are real
  rather than environmental, and a proxy 502 seen mid-probe was a CONNECT rejection for that
  same unresolvable host, not a signal about the county. The route that DID work is the one
  already in this repo: data/app/il-county-clerks.json, built weekly from ISBE, carries the
  clerk's name, address and phone — which is how the records request was addressed. **Lesson:
  the app's own clerk roster is a domain-discovery tool, and should be the FIRST stop when a
  county cannot be found, ahead of hostname guessing.**).
  **Ford** (~13k — township-precinct composition with a SHARED split (Patton 3 sits in
  two districts); the ISBE map is titled 2011 with Last-Modified 2021 — vintage
  unproven), ~~**Stark**~~ **SHIPPED 2026-08-03, and the way it shipped is the point.** Everything
  existed in a county-produced Google My Maps KML — 2 board districts, 9 precincts, PLUS
  fire 6 / school 4 / library 6 / park 2 — and the ONLY thing blocking it was vintage: the
  ISBE pointer dates to 2020-08, the county's online minutes begin 2022-07, and the
  post-2021-reapportionment vintage was unconfirmable **online**. No further searching could
  have closed that, because the missing thing was not published anywhere. Asking closed it in
  one sentence: County Clerk Heather Hollis wrote "the board districts and precincts are
  correct" and "the only thing that changed on the map is the congressional district" —
  which both affirms the two folders outright and dates the rest. Five dispatch entries
  followed (board, precincts, fire, library, park; school/ZIP/municipality are statewide
  layers here, and the congressional folder she names as changed is the one thing taken
  from the map under no circumstances). **The first county in the fleet unlocked by asking
  rather than by finding** — and the lesson for the ledger is that "vintage unproven" is a
  question for a human, not a search, **Montgomery** (~28k — the
  best roster of the pass: party + full composition, revised 2024-12; but its districts
  split precincts at SUB-precinct level ("N ½ of Butler Grove", "E of I-55 of North
  Litchfield #1"), so a composition dissolve cannot be exact — needs the polygon layer
  Beacon locks away, or a Stephenson-style georeference of its vector PDF).

  **Blocked, each on a named artifact:** **Knox** (~50k — the county's ENTIRE web estate
  is Cloudflare-challenge-fronted, roster page included; Galesburg's city org publishes
  board districts 1-3 (= **3** features, adopted 2021-10-27 per the item) but the rural
  districts 4-5 appear in NO vector source found, and ISBE's vector PDF is provably 2011
  content), **Christian** (~34k — the current 2022 district map is RASTER while the
  vector PDF beside it is the PRIOR-decade plan with 2010 populations — a vintage trap;
  no member roster online beyond chair/vice), **Menard** (~12k — 5 single-member
  commissioner districts whose only map is a 2021-12 raster; boundaries run section-line
  roads, not precinct unions, so no composition route exists; the roster and
  TIGER-VTD precincts (**14/14** name match) are otherwise ready).

  **Pass-wide findings:** (1) the ISBE precinct-maps mirror is PRE-2021-vintage for
  nearly everything here (Knox 2011, De Witt 2015, Piatt/Putnam 2015 scans, Montgomery
  2012/2015) — Macon's 63 per-precinct 2022 PDFs are the exception; treat the mirror as
  superseded unless a file proves otherwise. (2) TIGER 2020 VTDs are the small-county
  precinct route — Mason 21/21, Menard 14/14, Cass 21/21 current-name matches — each
  needing a one-time vintage sign-off. (3) New crawl-block class members:
  knoxcountyil.gov (CF managed challenge, whole estate), beacon.schneidercorp.com (hard
  403), browncountyil.org (captcha-parked decoy), champaigncountyclerk.com (UA filter).
  (4) Dead legacy domains still alive in search indexes: tazewell.com, masoncountyil.org,
  casscountyil.org, piattcounty.org apex, co.putnam.il.us — and Macon's CURRENT domain
  200-stubs unknown paths. (5) Commission/at-large counties (Monroe, Randolph; Pike,
  Putnam, Brown, Calhoun) debut the county-board concept's no-district posture: the member
  list renders on the COUNTY card. All six shipped 2026-08-02. The tranche-5 four went
  further than the posture the sweep described — they have **no dispatch entry of any
  kind**, the first counties served that way, so `METRO_COUNTY_FIPS` gains them while
  `DISPATCH_COUNTY_FIPS` must NOT (and no gate would catch the mistake — see
  EXPANSION_GUIDE §2.5.1). One correction to the sweep's own method: it inferred "at
  large" from board pages that omit districts. That is not evidence; each was re-proved
  from a certified election document before shipping. (6) Regional orgs: TCRPC
  (verified at 363 services) is GIS of record for Logan and Woodford ONLY — nothing
  usable for Peoria/Marshall/Stark/Putnam; CCGISC serves TWO frontier counties
  (Champaign + Piatt) through one integration; EWG's POD reaches only Monroe among the
  southern five.

  **TRANCHE 1 SHIPPED 2026-08-02 — Peoria (29th dispatched county) and Tazewell
  (30th), ~313k residents, seven dispatch entries between them.** Peoria: board (18
  single-member districts, live from the county's open-data org), precincts (116, polling
  joined on POLLINGID against 55 sites), and fire (13) / park (4) / library (10) — the
  first taxing tilings in the fleet whose source publishes a per-district WEBSITE, which
  the cards use as the footer link rather than printing a URL mid-card (a new
  `hidden: true` field flag on `polygonCountyEntry` captures a column for
  primaryLink()/when() without rendering it). Tazewell: board (3 districts seating 21 +
  a countywide-elected Chairman) and precincts (82).

  Three findings the build surfaced, each recorded rather than smoothed over:
  - *Tazewell publishes its board twice and the two disagree.* Its GIS roster attributes
    are stale — they seat a member the county's own site no longer lists and omit one who
    has his own member page. The scraper reads the WEBSITE and follows one stated rule:
    the website wins where they disagree, the GIS fills only where the website is silent.
    That fills the Vice-Chairman's undistricted row (GIS says District 3) and PRESERVES
    the disagreement about Greg Longfellow (site says D2, GIS says D3). Taking the site at
    its word gives 7/8/6 where the GIS says 7/7/7 — the builder enforces the TOTAL both
    surfaces agree on (21 + chairman) and deliberately NOT equal district sizes, because a
    gate insisting on 7/7/7 would silently overrule the county's own current claim to make
    the arithmetic pretty.
  - *Six of Tazewell's 82 precincts name no polling place* — its precinct layer points them
    at three facility ids its Voting Locations layer does not publish. The Whiteside shape,
    in the county's own data rather than in the join. New gap `tazewell-precinct-polling`.
  - *Peoria's member pages publish HOME ADDRESSES and an unlabeled year.* Neither is read:
    the residence follows the Madison precedent (a residence is not an office you can
    visit) and the year is dropped because nothing on the page says whether it is a term
    expiry or an election year. The party letter beside it IS read — unambiguous, and the
    county GIS independently agrees on every member it still carries.

  **TRANCHE 3 SHIPPED 2026-08-02 — Iroquois (31st), Monroe (32nd), Randolph (33rd), and
  the fleet's first AT-LARGE board posture.** Iroquois is a full-fat add: board (4
  districts × 4 members), precincts (37, polling joined against 32 sites) and a 46-feature
  fire tiling. Monroe and Randolph contribute precincts (25 and 35) and, more
  importantly, establish how a county with NO district geometry is served at all.

  - *At-large boards are county-card rows, not a dispatch entry.* Both counties run the
    commission form — three commissioners elected countywide — so there is nothing for
    `county-board` to join, and inventing a district would be a lie about how the county
    elects. Their members ride the COUNTY card through a new shared
    `il-county-commissioners.json`, keyed exactly like `il-county-clerks.json` so the card
    performs one lookup shape for both. This is EXPANSION_GUIDE §1.5 finally exercised;
    adding such a county adds ROWS, not a layer, and tranche 5's four at-large counties
    extend the same file. A districted county's card is untouched (asserted in the card
    tests against Cook).
  - *Iroquois's fire source does something no other county's does.* Its tiling carries a
    `Discrepancy` column in which the county records where its OWN two sources disagree —
    "Parcel Data shows this in Milford Fire District, but map shows Cissna Park" —
    populated on 20 of 46. The card surfaces that text wherever present, because a reader
    working out who covers their property should see the county's caveat rather than a
    false certainty. It is the most honest special-district source in the fleet.
  - *The Roman-numeral join.* Iroquois's roster table prints districts as I-IV while its
    GIS keys them by integer; the scraper converts and rejects anything outside I-IV, so a
    renumbering fails the build rather than silently dropping seats. Its e-mails are
    Cloudflare-obfuscated — decoded the same way every visitor's browser does, on contacts
    the county publishes for residents to use — and the builder's e-mail floor is what
    catches a broken decode.
  - *The southern gate moved.* Randolph reaches 37.80°N and `build_metro_outline.py`
    refused to write until `permalink_gate.minLat` and `metro_bbox.minLat` widened — the
    Rock Island lesson repeating on the other axis. A shared permalink in Chester would
    otherwise have been dropped on load with no error. Waterloo moved from the OUTSIDE
    anchor list to INSIDE in the same change, and Ava (Jackson) took its place as the
    southern frontier guard.
  - Three gaps recorded: Monroe's fire tiling names its districts only by unexpandable
    abbreviation (`monroe-fire-district-names`), Randolph publishes only 911 response
    zones rather than taxing districts (`randolph-fire-park-library`), and Randolph's
    precinct layer declares a polling id it populates on no row
    (`randolph-precinct-polling`).

  **TRANCHE 4 (first half) SHIPPED 2026-08-02 — De Witt, the 34th county, and a derived
  boundary that WATCHES ITS OWN SOURCE.** The county publishes no board-district GIS (only
  a 97 KB raster JPG) but states each district's precinct composition as text on every one
  of its twelve members' rows, and its precinct fabric is published — so the boundary is
  that fabric dissolved per that text, checked three ways: the four districts partition all
  23 precincts exactly (6+8+5+4), every name resolves in the live layer, and the resulting
  Census 2020 populations balance to a 3.2% spread, consistent with a real apportionment.

  What is new here is the WEEKLY DRIFT CHECK. Every derived boundary in the fleet has the
  same latent failure — the source page changes, the compiled composition does not, and the
  app keeps drawing superseded lines. That is precisely how the LaSalle defect survived
  years. De Witt's roster scraper therefore re-reads the composition off the same page it
  scrapes the roster from, and `build_dewitt_board_roster.py` FAILS if it no longer matches
  the table compiled into `build_dewitt_board_districts.py`. The comparison is
  precinct-level, not township-level: an earlier township-granularity version passed a
  simulated "Clintonia 7,8" against a shipped "7,8,9", which is the likeliest change there
  is in a county where one township's nine precincts are split across three districts. All
  four drift cases (a precinct lost, gained, renumbered, and a whole township moved) are
  now caught, verified by negative test.

  De Witt also debuts LETTERED districts (A-D) — every prior county numbers them.

  **TRANCHE 4b SHIPPED 2026-08-02 — Washington, the 35th county, and the drift check
  generalizes.** The county runs NO GIS of any kind — no org, no viewer, no maps page —
  so its board boundary is Census townships dissolved per the parenthetical it prints
  under each district heading. No township is split, so every district edge is a Census
  township edge; the build asserts the three districts partition all 16 townships exactly
  and that their 2020 populations balance (5.1% spread). Its roster is unusually complete
  for a county this size: 15/15 with BOTH phone and e-mail.

  Two honesty details worth keeping:
  - *The county publishes every member's HOME ADDRESS.* All fifteen. The scraper skips
    them all — the Madison precedent, a residence is not an office a resident can visit —
    and a card test asserts no street address reaches the card.
  - *One member's published e-mail domain is misspelled at the source*
    (`washingtonco.illnois.gov`). It ships AS PUBLISHED and the builder WARNs on every
    weekly run: correcting an officeholder's contact details is the county's call, not
    this pipeline's. The warning had to be made precise first — a looser near-miss rule
    flagged `hotmail.com` as a misspelling of `gmail.com`, so the check now uses real
    edit distance and only compares against the county's OWN .gov domain, since members
    legitimately publish personal addresses.

  Washington's precincts are a new recorded gap (`washington-precinct-geometry`): with no
  GIS at all there is no precinct layer to read, and its precinct map is raster-only. The
  board shipped anyway precisely because whole townships ARE published as vector.

  **TRANCHE 4c SHIPPED 2026-08-02 — Cass, the 36th county, and the first board whose
  districts are NOT all the same size.** Its GIS is a Beacon parcel viewer with no public
  REST, but it publishes a one-page district table (text-extractable, read directly rather
  than OCR'd) whose 21 precinct names match TIGER's Census 2020 voting districts exactly,
  name and number. The boundary is those VTDs dissolved per that table.

  **The population check nearly rejected a correct build.** Cass seats ELEVEN members as
  3/3/3/2. Measured per DISTRICT the populations are 28.8% apart, which reads as a broken
  transcription and would have failed the standard 20% guard; measured per MEMBER — the
  basis a multi-member apportionment actually balances on — they are 12.3% apart, which is
  an ordinary rural apportionment. The seat counts came from the county's own roster page,
  and finding them is what turned an apparent defect into a correct build. **Any county
  whose districts elect different numbers of members must be checked per member**; that
  rule is now in EXPANSION_GUIDE §2.5.1.

  **A PDF composition cannot have De Witt's weekly drift check** — the roster page merely
  links the table rather than printing it. What Cass gets instead is a SEAT-COUNT
  tripwire: the weekly roster build asserts the seats per district still match the
  boundary's SEATS table, since that is the input its population test depends on and a
  reapportionment almost always moves one. It cannot catch a redraw that leaves every
  district the same size, and the builder says so rather than letting a reader assume
  otherwise.

  Two scraper details from a hand-maintained page: phone numbers WRAP mid-string ("2" /
  "17-323-4586"), so digits are gathered across lines rather than matched line-by-line —
  a line-anchored regex silently drops two members' phones; and the Chairman is announced
  as "Bill Merriman" while his member row reads "William (Bill) Merriman", so the
  parenthetical had to be treated as a name he is announced under rather than stripped.

  **TRANCHE 4d/4e SHIPPED 2026-08-02 — Marshall (37th) and Mason (38th), the two
  whole-township dissolves that close the derivation tier.** Marshall's composition and
  roster are the SAME TABLE in the SAME PDF, which makes it the tightest weekly drift
  check in the fleet: the county cannot publish a new roster under new districts without
  the check seeing both at once. Three districts × four members partition all 12 townships
  (5+4+3), balancing at 1.4%. Two parser findings: fixed-width row bins silently dropped a
  member whose name (y=361.56) and title (y=362.02) straddled a bin edge — eleven members,
  nothing failing — so rows are clustered by proximity instead; and a blanket
  `.capitalize()` flattens McGlasson/McLaughlin, so only the Mc/Mac/O' families are
  re-capitalized.

  **Mason is the county that changed the method.** Its roster PDF is a SCAN carrying a
  text layer, and that layer is the trap — it is encoded so extraction returns line noise
  ("xRF# ISgH tlgP") and NEITHER pdfplumber NOR pdftotext errors. Noise that parses is
  worse than no text: a scraper would ship confident garbage under real officeholders'
  names. So the roster is hand-transcribed and a weekly WATCHER replaces the scrape,
  checking the two things software still can — that the board page still links that exact
  PDF (a WordPress replacement lands at a new upload path while the old URL serves the old
  file forever) and that its bytes are unchanged. Its output is a request for a person,
  not a diff. Mason also prints seven members' home addresses and an eighth row reading
  "SECURED ADDRESS" — a legally protected address — so the county ships NO residence data
  at all, not even the home town: a town-for-seven roster would single her out.

  **Mason closed the served ring around MENARD**, giving `metro-outline.json` its first
  interior HOLE (one ring → two). Both consumers were already even-odd —
  `pointInPolygonRings` and Leaflet's fill under the wash — so the enclosed county
  correctly reads as UNCOVERED, which is true: Menard cuts its districts along section-line
  roads. The Mason card test asserts the hole directly, because one that silently inverted
  would tell an unserved county's residents they were covered.

  A defect found while cloning workflows, worth remembering: three roster workflows cloned
  from Iroquois kept Iroquois's DOMAIN and its "4 districts, four members each" body while
  scraping a different county — so a Washington roster PR would have asked a reviewer to
  approve officeholder changes under another county's provenance. A workflow's PR title
  and body are a human-review surface, not cosmetics.

  **TRANCHE 5 SHIPPED 2026-08-02 — Pike, Brown, Calhoun and Putnam: the at-large tier, and
  the first counties in the fleet served with NO dispatch entry at all.** 26 members on the
  County card across ~31k residents; coverage reaches **47 counties where a
  county-specific layer answers** — 38 through their own dispatch entries, 5 through a
  shipped judicial circuit, and these 4 through the County card alone. (The tranche-5
  commit message said "42 counties"; that undercounted by omitting the five
  judicial-subcircuit secondary counties, which are served too. Both figures are the
  2026-08-02 snapshot and stayed in this log as if current until 2026-08-03 — for the
  live count and the per-county roll-up read `docs/COUNTY_STATUS.md`, GENERATED from
  the coverage-ring lists precisely so this arithmetic is never done by hand again.) The structural lesson is the one to carry forward: `METRO_COUNTY_FIPS`
  means "a county-specific layer answers here", NOT "this county has a dispatch entry", so
  these four join it with INSIDE anchors while `DISPATCH_COUNTY_FIPS` must not gain them.
  When the tier shipped, `validate_index.py` would NOT have caught that mistake — its
  coverage-ring check only looked from index.html outward — so the check now runs both
  directions and fails on a county listed as dispatched that registers nothing. Their
  outlines ship `dynamic_reference: true`. Everything else the build found is recorded in
  the at-large paragraph of the pass-7 research block above; the two rules with the widest
  reach are **prove "at large" from a certified election document, never from a page that
  omits districts**, and **an identical phone number on every member row is a switchboard,
  not contact**.

  **The pass-7 build-ready ledger** (the live work queue, recommended order):
  1. ~~**Peoria + Tazewell**~~ **SHIPPED 2026-08-02** — the two anchors (~313k), both
     standard patterns (polygon layers + roster scrape; the Esri election template).
  2. ~~**Champaign + Piatt**~~ **WITHDRAWN 2026-08-02 — LICENSED, not open.** Reading
     the publisher's own pages before building overturned the sweep's verdict: CCGISC
     sells both counties' GIS data under signed licence agreements, and its Terms grant
     only personal, non-commercial, transitory viewing — no copying, no public display,
     no mirroring, which is all three of the things a dispatch entry does. Both counties
     are now the fleet's first LICENSING block (`champaign-piatt-ccgisc-license`) with
     gap-location outlines; the unlock is a records request to each county CLERK, who
     holds election geography as a public record whatever the consortium licenses.
  3. ~~**Iroquois + Monroe + Randolph**~~ **SHIPPED 2026-08-02** — the full-fat eastern
     add plus the two commission counties that debut the at-large posture (~92k).
  4. ~~**The derivation tier**~~ **COMPLETE 2026-08-02** — De Witt (precinct dissolve) as
     the 34th county, Washington as the 35th, Cass as the 36th, Marshall as the 37th and
     Mason as the 38th. Mason closed the ring around MENARD, giving the coverage outline
     its first interior hole (both consumers are even-odd, so the enclosed county
     correctly reads as uncovered — asserted in the Mason card test).
  5. ~~**The at-large tier**~~ **COMPLETE 2026-08-02** — Pike, Putnam, Brown and Calhoun
     (~31k), all four served through the County card with no dispatch entry, the first
     counties in the fleet to be served that way. Pike's permalink-gate widen fired as
     predicted (west edge -91.15 -> -91.55). Coverage still one connected region with
     one hole (Menard); no new hole appeared.
  6. **Chases, not builds** (e-mail or artifact-hunt): Macon's district labels, ~~Stark's
     2021 ordinance~~ (**resolved 2026-08-03 — not by finding the ordinance but by the
     County Clerk confirming the map; the chase category's first win, and it took an
     e-mail rather than an artifact**), Knox's rural map + roster access, Christian's
     roster + labeled map,
     Menard's commissioner geometry, Clinton's and Fayette's Sidwell shapefiles, Ford's
     adopted-map vintage, Montgomery's polygon layer.

- **VALIDATION + SOURCING PASS 6 (2026-07-31) — every county × concept cell walked against
  this guidebook, then a 13-way live sourcing round over everything open. The gaps block
  grew 33 → 65 entries, two defects surfaced in SHIPPED data, six recorded blockers turned
  out stale, and eight counties' municipal officials turned out to be publishable all
  along.** The pass had two halves: a static audit (does every cell that ships, doesn't
  ship, or can't ship have a matching record — the maintenance contract, applied
  exhaustively) and a live round re-testing every blocker and researching every cell no
  pass had ever examined.

  **2026-08-01 follow-up — the LaSalle defect was the tip; the Lake defect is fixed.**
  Starting the roster rebuild pulled the thread further:
  - *The shipped LaSalle BOUNDARY was the superseded map.* The layer is frozen at
    2015-08-25 in schema and data and its Pop100 column balances 2010 census populations
    — it is the 2011-2021 apportionment. The county adopted "Redistricting Map Scenario
    6A" by Resolution #21-126 (Nov 2021, 24-4; found in the county's consolidated 2021
    minutes — the meeting-portal lesson again) and publishes the 2022-2031 districts
    ONLY as a vector-PDF map pair (DocumentCenter 318/319, per-district 2020 populations
    printed on the sheet). No current board GIS exists on either county server or its
    AGOL org; the one webmap-referenced clerk service is deleted, and the map vendor's
    own ArcGIS host answers with an expired TLS certificate.
  - *A dissolve of the current precincts cannot draw the adopted lines.* The 2026
    primary Statement of Votes Cast proves the county now runs SPLIT precincts across
    district boundaries — Serena 1 (D3: 504 / D5: 345 registered), Eden 2 (D15: 271 /
    D29: 105), La Salle 7 (D14: 466 / D16: 11), La Salle 8 (D14: 664 / D16: 46) — so the
    Ogle/Grundy composition route is structurally unavailable here. The same canvass
    yields the authoritative whole-precinct district assignment for 63 precincts across
    the 16 districts contested in 2026 (the 2024 reports cover the other 13), which is
    one of the rebuild's two verification anchors; the map's printed populations are the
    other, valid for the districts the county has not re-precincted since adoption.
  - *What shipped today (interim honesty):* the LaSalle county-board dispatch entry and
    the precinct card's board-district row are SUPPRESSED — rendering superseded names
    on superseded lines was the Whiteside-ward situation live in production. The gap is
    recorded as `lasalle-board-districts-stale` (absorbing `lasalle-board-phones`); the
    rebuild — georeference the adopted map, Stephenson-style, verify against canvass +
    printed populations, join the directory roster — is the ledger's top item.
  - *Lake shipped:* the board card's District Office group and Newsletter link render
    as of 2026-08-01 (the loader now requests ADDR/CITY/ZIP/URL2; re-verified 19/19
    live). The county-board-office-addresses gap narrows to every county except Cook
    and Lake.

  **2026-08-01 tranche — the ledger's municipal-officials half shipped in one change.**
  Eight counties' scrapers (seven new scripts — Madison and St. Clair share
  `ewg_municipal_officials_scraper.py`, which emits two payloads from one COG
  document) joined the weekly workflow, all preservable, and the roster grew
  360 → 492 municipalities / 2,279 board members / 583 ward-district seats.
  Findings the build surfaced, each recorded on its ledger row: McLean's clerk
  GIS is stale across the April 2025 election on two of its three ward cities
  (the cities' own pages ship instead) and its county-wide Airtable is an
  unrenderable interface share; Grundy and Livingston disagree on one Dwight
  trustee seat (Grundy's month-fresher booklet wins precedence); Sangamon has
  two more ward cities than the pass recorded (Virden 8, Leland Grove 6) and
  one sheet with no Office column (offices read from e-mail prefixes);
  Alorton and Centreville are disbanded into Cahokia Heights, which needed the
  roster's first post-Census-2020 GEOID alias; and the EWG directory's
  side-by-side board columns fuse in extraction (split by case-boundary +
  word-gap geometry, every split logged for the PR review).

  **Two defects in shipped data, both found by measuring, not reading:**
  - *LaSalle's board card renders a superseded roster.* The boundary layer the card reads
    members from was last edited **2015-08-25**; 18 of its 29 surnames appear nowhere in
    the county's current board directory, and several returning members sit in different
    districts. Nothing failed on screen — the card names real-looking people. Recorded as
    `lasalle-board-roster-stale`; the fix source (the county's own CivicPlus directory,
    names + full 10-digit phones by district) is verified and also retires the old
    area-code half of `lasalle-board-phones`. *A branch-1 county needs its GIS edit date
    checked at every enrichment pass, not just at ship time.*
  - *Lake's board office address is fetched into view and never rendered.* The card
    contains the render path for a District Office group and the county GIS populates
    ADDR on 19/19 features ('18 N County St, Waukegan' — the county building), but
    `loadLakeCountyBoard`'s outFields never request the address columns, so the office
    group and the newsletter link are dead code. One line lights both up — and it
    falsified the `county-board-office-addresses` entry's claim that *no* card names an
    office (Cook's District Office group ships today, measured 17/17 live).

  **Recorded blockers that did not survive re-testing** (the dekalb-county-gis lesson,
  now at scale — six in one pass):
  - **Henry**: the "Alternate" map IS the adopted plan — Ord 21-33 (11/18/2021, 16-0) in
    the board minutes, codified at county code Sec. 30.03, republished by the clerk as
    "2022 County Board Districts", and filed with the ISBE. The 12+12 township
    composition is proven by the map's own population table for both census years;
    the county's townships layer (edited 2026-06) supplies dissolve geometry. Build-ready.
  - **Macoupin**: the board map WAS adopted — O-2021.06 (2021-11-09, 18-0), machine-readable,
    with vector-PDF maps of all nine districts on the clerk's Map Room. A derived build
    exists (townships + the two precinct-split townships). Its precinct dataset now serves
    the 45-precinct 2022-2032 fabric, not the 105 pass 4 recorded.
  - **Bureau**: the adopted 18-district map is downloadable after all (IQM2 minutes/packet,
    23-0) — but as 300-dpi JPEG scans with street-level city splits, so the gap stands,
    sharpened.
  - **Logan**: the board page now pairs all 12 members with their districts, with contact —
    the "salary publication only" blocker is gone; a scraper build closes the card.
  - **Aurora**: the city relaunched on www.aurora.il.us, fully crawlable; all 12 per-seat
    pages publish e-mail + office phone. The 403 era is over.
  - **Waukegan**: "publishes a ward map as PDF only" is stale — the city's own AGOL org
    serves 9 ward polygons with alderman/phone/e-mail on every feature, edited 2025-07.

  The counter-examples held too: Mercer (document section still empty — now with an empty
  'County Board' folder), Jo Daviess, Rockford precincts, Dakota's president, the DMMC
  area codes, DeKalb's precinct codes and the McHenry/Kendall WAF denies all re-tested
  unchanged — though the Archive now holds verified 2026 captures of BOTH blocked board
  directories, so their Archive rungs are newly viable.

  **The build-ready ledger** — everything verified publishable on 2026-07-31 and blocked
  on nothing but build effort (this is the live work queue; sources and measured counts):

  | build | source (verified live) | measured |
  |---|---|---|
  | ~~LaSalle board REBUILD — boundary + roster~~ **SHIPPED 2026-08-01** | boundary DERIVED: the county's precinct layer dissolved per the FULL canvass record (2024 general + 2026 primary — all 29 districts, 108 whole + 11 split precincts); roster scraped weekly from county directory DID=39 | 9 districts reproduce the adopted map's printed populations to the person; the 11 splits are drawn with their majority side (~1,659 residents misplaced, stated on the card) — cutting them along the adopted vector map is the recorded refinement |
  | ~~Lake board office + newsletter~~ **SHIPPED 2026-08-01** | one-line outFields fix | District Office group + Newsletter link now render (ADDR/URL2 re-verified 19/19 live) |
  | ~~Municipal officials — Grundy~~ **SHIPPED 2026-08-01** | clerk Directory of Officials booklet ("Updated July 2026"; the county DELETES prior editions, so the scraper discovers the link) | 17 munis / 133 officials / 17 heads / Morris's 8 ward seats, with TERM ENDS years; the booklet prints everything in caps, recased before it ships |
  | ~~Municipal officials — Livingston~~ **SHIPPED 2026-08-01** | clerk Yearbook (06-2026 edition, linked from the county homepage) | 16 munis / 153 officials / 16 heads / 18 ward seats (Fairbury 8 + Pontiac 10); Dwight's roster conflicts with Grundy's July booklet on one trustee seat — Grundy's fresher edition wins the precedence tie-break |
  | ~~Municipal officials — Logan~~ **SHIPPED 2026-08-01** | clerk Reference & Yearbook (word-position parse — half-letter paired person-cards) | 11 munis / 92 officials / 11 heads / 20 ward seats (Lincoln 8 + Mt. Pulaski 6 + Atlanta 6), with PER-PERSON phone + e-mail; home addresses printed by the yearbook are never collected; department heads deliberately skipped |
  | ~~Municipal officials — McLean~~ **SHIPPED 2026-08-01, narrower than recorded** | the three ward cities' OWN pages (Bloomington BEC + leroy.org + lexingtonil.gov — the city moved to lexingtonil.gov) | 3 munis / 26 officials / 3 heads / 23 ward seats. What the record got wrong, measured 2026-08-01: the clerk's GIS City Council layer is STALE across the April 2025 election on Le Roy (2 of 8 seats) and Lexington (2 of 6; one member appointed 2025-05) — only Bloomington's rows are current, and the BEC page beats them anyway (mayor + terms). The county-wide Airtable is an INTERFACE share (pag…): fully JS-rendered, its data API needs undocumented per-request parameters, and no fetch rung available to CI renders it — the county's other ~17 municipalities remain open against that route |
  | ~~Municipal officials — Sangamon~~ **SHIPPED 2026-08-01** | clerk per-municipality officials PDFs (SAS-signed Azure blob URLs — discovery from the page is mandatory every run) | 26 munis / 208 officials / 26 heads / 32 ward seats (Springfield 10, Auburn 8, Virden 8, Leland Grove 6 — two more ward cities than the pass recorded); Jerome's sheet omits its Office column, so offices read from the officials' own e-mail prefixes; two Acting Presidents ship as heads while keeping their trustee seats |
  | ~~Municipal officials — Madison + St. Clair~~ **SHIPPED 2026-08-01** | East-West Gateway 2026 POD (one COG document, two counties — one scraper, two payloads, both preserve together) | Madison 28 munis / 241 officials / 28 heads / 40 ward seats; St. Clair 26 / 247 / 26 / 49. Alorton and Centreville are in the index but disbanded into Cahokia Heights (the POD itself says so) — Cahokia Heights ships under an explicit post-Census-2020 GEOID; side-by-side board columns fuse in extraction and are split by case-boundary + word-gap geometry, each split logged |
  | ~~Municipal officials — Rock Island~~ **SHIPPED 2026-08-01** | clerk Elected Officials listing (DocumentCenter 291 — the county's own certified record, Cook-DOEO depth from a PDF) | 15 munis / 122 officials / 15 heads / 27 ward seats (E. Moline 7, Moline 7, Rock Island 7, Silvis 6), with term years, appointment flags and many direct phones; Oak Grove's combined Clerk/Treasurer office ships as printed |
  | ~~county-precinct — McLean~~ **SHIPPED 2026-08-02** | clerk GIS PollingPlaces L1 + L0 | 141 precincts, polling joined **141/141** by POLLINGID at load (the Kendall model); board district via spatial join; the polling features' CONTACT/PHONE columns are the election AUTHORITY's, not the venue's, and are deliberately not requested |
  | ~~county-precinct — Logan~~ **SHIPPED 2026-08-02** | TCRPC L40 + the clerk's HTML polling table, shipped as a same-origin file (scripts/build_logan_precinct_polling.py, --check against the live page) | 29, joined 29/29 — the "one alias" turned out to be a class: the clerk writes "#1" and bare "Atlanta" where the GIS writes "1" and "Atlanta 1", absorbed by normalization plus a bare-base fallback applied only when neither side has another numbered variant |
  | ~~county-precinct — Sangamon~~ **SHIPPED 2026-08-02** | ApprovedPrecincts20231012 + ElectionPollingAndPrecincts L0 | 166, polling joined **165/166** by POLLID→POLLINGID (one precinct's id resolves to no polling feature at the source; its card omits the row rather than guessing); board district via spatial join |
  | ~~county-precinct — Carroll~~ **SHIPPED 2026-08-02** | TIGERweb Census-2020 VTDs live (the county did not re-precinct, so the 22 VTDs ARE the current fabric) + the clerk's polling notice shipped as a same-origin file (scripts/build_carroll_precinct_polling.py — deterministic grouped-label expansion with a 22-name guard that fails the build if the county ever re-precincts) | 22/22 |
  | ~~Macoupin polling join~~ **SHIPPED 2026-08-02** | Socrata rc5v-ajnf | 45/45 — comma-expansion ("BRIGHTON 1,2" is two precincts) plus one rename class the county itself created (polling says "NILWOOD 1" where the fabric has bare "NILWOOD"; dropped only when neither side has another numbered variant) |
  | ~~Kane precinct township names~~ **SHIPPED 2026-08-02** | the clerk's Elections Maps page — its per-precinct map files are FILED UNDER township folders (…/Precincts/Big Rock/Precinct_BR01.pdf), pairing all 16 prefixes from the county's own structure | 16/16, carried as a code-level constant; the entry's old "mapping the prefix would be a guess" comment retired |
  | ~~Kane polling line~~ **SHIPPED 2026-08-02** | KaneCo_IL_Elections_PollingPlaces (its only layer id is **1**; 320 rows total, filtered to LocationType='ElectionDay') | 292/292 joined on the precinct code; the card labels the row with the layer's own Election field ("Polling place (2025 General Election)") because a polling assignment is per-election, not a standing fact |
  | ~~county-board — Woodford~~ **SHIPPED 2026-08-02, and Woodford is now a SERVED COUNTY** | TIGER township dissolve per Ord 2020/21 #005 (scripts/build_woodford_board_districts.py — 3 districts of whole townships, five members elected at large from each; anchors prove the composition) + weekly directory scrape (woodford_county_board_scraper.py) | 17/17 township match, no reconciliation needed; roster 15/15 with phone AND e-mail (the pass recorded phones only — the e-mails are spam-wrapped but verbatim in the wrapper's own source); no chair marked — elected from within the body, the directory doesn't say who holds it. Precincts shipped in the same change: TCRPC's election service, 37, polling joined 37/37 on the numeric polling reference with the precinct's own name cross-checked in the polling row's grouped label |
  | ~~county-board — Henry~~ **SHIPPED 2026-08-02, and Henry is the TWENTY-EIGHTH dispatched county** | TIGER townships dissolved per adopted Ordinance 21-33 (scripts/build_henry_board_districts.py — two districts of twelve whole townships, ten members each, the fleet's widest multi-member districts) + weekly scrape of the county's own CivicPlus directory, which the county itself keys BY DISTRICT (DID=39/40) | The double population proof landed THREE ways: the composition reproduces all four printed district totals to the person (2010: 25,158 + 25,328; 2020: 24,931 + 24,353 — each summing to the county's official census total), all 24 printed 2020 township populations equal live Census POP100 exactly (re-asserted on every build), and all 24 names match TIGER 24/24. Roster 20/20 with e-mail, 15 with phone; no chair marked anywhere in the directory, so none is tagged (the Woodford posture). Precincts stay raster-only — recorded as the new gap henry-county-precincts; municipal-officials rungs not yet worked (backlog). Gap henry-county-board-districts closed and henry-county-precincts opened in its place (the block holds at 61) |
  | ~~county-board — Boone~~ **SHIPPED 2026-08-02** | the county GIS's three per-district MapServer layers (District_1/2/3 at indexes 0/1/2, each pre-dissolved — verified to tile the county outline: 0 overlaps on a 479-point grid, anchors match member addresses) merged and district-tagged at load time + weekly board-page scrape (boone_county_board_scraper.py) | 12/12 by district with phone, e-mail AND the term-expiry year (staggered terms — per-seat ballot information, rendered through the shared stale-year gate); role tags verbatim: one Vice-Chairman, and NO Chairman named anywhere — one member is merely listed above the district sections, which earns no title. The leftover census-block attributes on the merged features are read nowhere; the precinct card gained the standard best-effort board-district join. Gap boone-county-board closed (the gaps block drops to 62) |
  | ~~Adams — wards, fire, library~~ **SHIPPED 2026-08-02 (pass 8, second tranche)** | the same county AGOL org (`Web_Voting_Data/0`, `Web_District_Data/3` and `/2`) | Quincy's 7 wards SEAT-ONLY — quincyil.gov sits behind the same Akamai deny as its county, so no alderman is named and gap quincy-ward-officeholders records it. 26 fire districts across the county's 48 polygons: the 911 layer splits each district into MUTUAL-AID sub-areas ("TTFD: MA-Payson", "TTFD: MA-E4"), so DsplayName is the district and MapLabel is which partner responds there — drawn as published rather than dissolved, since each sub-area is a real answer to "who comes here". Every row is keyed to @quincyadams911.org, so this is a DISPATCH tiling and the caveat rides every card (the St. Clair posture). Library: 7 districts on 10 polygons, one of which the county names "None" — that is the county recording an area NO library district serves, so the card states the absence instead of naming a district called None. **School districts deliberately NOT added**: the app already answers statewide from TIGERweb, and a county-specific copy would duplicate an existing answer |
  | ~~Adams — board districts + precincts~~ **SHIPPED 2026-08-02 (pass 8; 39th dispatched county, and the fleet's westernmost)** | the county's own AGOL org (`Web_Voting_Data/2`, `Adams_County_Voting_Precincts_view/0`) | 7 board districts VERIFIED to tile the county before shipping — 99.997% of the TIGER outline covered, largest pairwise overlap 5e-7 deg², Quincy/Camp Point/Mendon each resolving to exactly one — four small city districts inside Quincy plus three rural, which the areas confirm (D1-D4 ≈ 14 sq mi against Quincy's 15.7; D5-D7 ≈ 856; county 867). 92 precincts whose own feature carries BOTH the polling place (92/92) and the precinct's board district, so the precinct card is the fleet's least-joined: no spatial join, no name match. **NO ROSTER, and none invented**: adamscountyil.gov is an Akamai hard WAF deny (391 bytes, x-reference-error, errors.edgesuite.net — the Joliet class) and the Archive holds the site root but not the board page, so the board card names the district, says plainly that the county publishes no membership, and links the body. Gap adams-county-board-roster records what would lift it. Quincy's 7 wards, 48 fire, 10 library and 10 school districts are present on the same org and deliberately left for a later tranche |
  | ~~Schuyler — at-large board~~ **SHIPPED 2026-08-02 (pass 8, the SEVENTH at-large county)** | the county's own Meet-the-Board page (weekly CI via il_county_commissioners_scraper.py) | 7 members with per-member phone and county e-mail, roles read from the page's own HEADINGS rather than from each row — Schuyler is the first county in this file where "Chairman" is a section title above a name, so the parser carries the heading forward and drops any name appearing before one rather than defaulting a role. AT-LARGE PROVEN from the Clerk's certified canvass (elections.schuyler.il.us/results-2.pdf): the contest is "FOR MEMBERS OF THE COUNTY BOARD … (Vote for not more than four)" with "Precincts Reporting 17 of 17", and the word "District" appears nowhere in its 11 pages. All seven rows print the SAME courthouse address (102 S. Congress St., Suite 104, Rushville), so it is hoisted to the board office once rather than repeated as seven residences — the Calhoun/Monroe posture; the phones do differ and stay on the rows. No dispatch entry, no coverage function, no toggle: Rushville simply moves from OUTSIDE to INSIDE in build_metro_outline, exactly as its OUTSIDE comment predicted when Mason and Brown closed the line around it |
  | ~~county-board — Grundy~~ **SHIPPED 2026-08-02** | the SHIPPED precinct layer dissolved per the adopted 10/12/2021 map (scripts/build_grundy_board_districts.py, the LaSalle machinery minus the splits — Grundy's districts are compositions of whole current precincts) + weekly board-page scrape (grundy_county_board_scraper.py) | The "40-row color transcription" was done programmatically, not by eye: the map PDF rendered at 300 dpi, the teal district-boundary strokes isolated, the three enclosed regions flood-labeled, and each precinct label placed by its text-layer coordinates — then PROVEN arithmetically, because the map prints every precinct's 2020 population: all three district sums reproduce the printed totals to the person (17,663/17,364/17,506). Roster 18/18 with party, since-year, committees verbatim (per-committee Chair/Vice-Chair suffixes kept), phone + e-mail; Chairman Drew Muffler tagged from his own row. Precinct card gains the board-district join. Gap grundy-county-board closed (61 remain) |
  | ~~Logan board roster scraper~~ **SHIPPED 2026-08-02** | the county's own board page (weekly scrape, logan_county_board_scraper.py + build_logan_board_roster.py) | 12/12 by district with phone + e-mail; Chair James Glenn and Vice Chair Dale Nelson tagged on their own rows — the county says who holds them, so the tags are read, not guessed. The entry's rule-4 branch-3 honesty floor is retired and the gap logan-county-board-members closed (the gaps block drops to 63) |
  | Aurora per-seat contact | www.aurora.il.us Meet-Your-Aldermen | 12/12 seats w/ e-mail — **re-measured 2026-08-02: the Akamai edge 403s datacenter ranges** (Reference #18.… errors.edgesuite.net, the DuPage/Joliet deny class) and the Archive holds no capture of the relaunched URL, so the pass-6 "the 403 era is over" held only for residential clients. Building this means the Joliet pattern: a scraper that is EXPECTED to fail in CI and preserves — but unlike Joliet, no rung reachable from CI has ever returned the content to write a verified parser against. Stays open until a capture or an unblocked rung exists |
  | ~~fire-district — Sangamon~~ **SHIPPED 2026-08-02** | FireDistrictEtc L2 on the county org | 226 fragments grouped client-side into 29 FPDs + SPRINGFIELD CORP — kept and RELABELED rather than dropped: a Springfield click answers with the city's corporate area and the card states the city is served by its own Fire Department, not an FPD. Identity-only (trustees partly elected via four clerk PDFs, partly board-appointed — no keyed roster); the source's doubled-space 'LOAMI  FPD' collapsed |
  | ~~fire-district — St. Clair~~ **SHIPPED 2026-08-02** | CentralSquare/DATA/8 (the county's CAD folder) | 44 named departments, identity-only; disttype/agency/agencyurl declared and 0/44 populated, so the taxing-vs-dispatch caveat rides every card verbatim |
  | fire ~~/park/library~~ — Stephenson **fire SHIPPED 2026-08-02** | the county's 2014 COUNTY FIRE DISTRICT MAP on the ISBE mirror — a genuine vector PDF, georeferenced by scripts/build_stephenson_fire_districts.py | 15 named services shipped with the 2014-vintage caveat on every card. The fit had to INVERT the board build's route: the fire services keep their true extents past the county line, so the union outline is not the county boundary (fitting it there landed only 11% of hydro within 50 m) — the fit runs ON the map's hydrography instead (median 11.5 m / RMS 18.2 m), independently checked by the map's own town labels (median 402 m — label offsets). The grey 'Corporate' overlay is base-map annotation drawn ON TOP of the fills (Lena sits in both) and is deliberately not shipped. **Park/library re-measured: NOT buildable by this route** — those two maps bake their district shading into 16 raster JPEG strips (only the basemap is vector), recorded as the new gap stephenson-park-library-districts |
  | park/library — Logan | 7 + 6 single-feature layers (edited 2026-04) | Emden/Armington boundaries conflict with TCRPC's own regional dissolve — resolve first |

  ~~City ward layers verified current enough to build~~ **SHIPPED 2026-08-02 — the
  pass-6 ward tranche: thirteen sources across twenty-two cities**, every source
  re-verified live at build time (schemas, counts, vintage) before its loader was
  written: Belvidere (both aldermen + phones on the Boone county feature), Berwyn,
  Waukegan (per-seat phone + e-mail on the 2025 locator polygons), North Chicago
  (2026 layer, seat-only), St. Charles + Geneva (both aldermen w/ per-seat contact;
  St. Charles' literal 'Unknown' phone strings dropped), Batavia (both aldermen's
  names; its per-seat contact columns are declared-and-empty), West Chicago (both
  aldermen + per-ward page URL), McHenry city (seat-only), Yorkville + Plano
  (Kendall Hosted/Wards filtered to the two; the layer's Aurora/Joliet sliver rows
  dropped), Pontiac, Bloomington + Le Roy + Lexington (one clerk layer parsed by
  its own 'City of X Ward N' names; the REPNAME column measured stale on two of
  the three is read NOWHERE — all three join the roster), Lincoln, Springfield,
  Freeport (the layer's stale Alderperson column read nowhere), East Moline
  (joined the rock-island entry; full per-seat contact on the polygon), Belleville
  (the duplicate-id sliver dropped by keeping each id's largest ring) + O'Fallon.
  The municipal-ward coverage file grew 35 → 56 municipalities across 21 entries.

  **Still to chase** (verified current in the sweep, but the service URLs did not
  survive to the build pass): **Lake Forest** 4 (GIS Consortium — the CLF
  MapGallery viewer resolves to no public REST endpoint yet), **Elmhurst /
  Wheaton / Lombard / Glendale Heights** (city-grade layers w/ populated attrs;
  Lombard's AGOL app item resolves but its webmap data is unreadable
  anonymously; Darien's attrs stale — all re-discovery candidates).

  **What was recorded as confirmed-absent** (each a new gaps-block entry with the full
  enumeration in its blocker): fire/park/library tilings in Livingston, McLean, Winnebago,
  Carroll and Macoupin (all three concepts), Grundy, Boone (park/library — fire's naming
  gap already stood), Sangamon (park/library), St. Clair (park/library), Lee
  (park/library), Whiteside (all three), Logan (fire — the sighted "fire zones" are
  dispatch quadrants, not districts), Woodford (all three — every "district" service is
  the parcel fabric wearing the district's name); precinct geometry in Livingston and
  Stephenson; ward geometry in Morris, Momence, Kankakee city (mixed-vintage layer with
  measured overlaps), Park City, three Carroll cities, eight Macoupin cities, three
  DuPage cities, Harvard/Marengo (challenge-blocked), Plano (seats), Rock Island city
  (vintage); and Boone + Macoupin municipal officials (stale yearbook; JS-locked
  directory). McHenry's long-prose-recorded park gap finally got its panel entry.

  **Discovery notes for pass 7:**
  - **The meeting portal is the resolution archive.** Bureau's adopted map was in IQM2
    minutes, Henry's ordinance in AgendaCenter, Woodford's in its agenda packet,
    Macoupin's on its code site. When a county's *pages* say nothing, its *minutes* often
    say everything — the Ogle lesson, one level deeper.
  - **County domains keep moving**: sangamonil.gov, aurora.il.us, woodfordcountyil.gov,
    bureaucounty-il.gov, grundycountyil.gov, rockislandcountyil.gov — old domains 301 or
    serve stale copies; re-derive the domain before concluding anything.
  - **Full-folder enumeration is the standard.** St. Clair's fire tiling sat in a CAD
    (CentralSquare) folder pass 4 never opened; Kane's polling service has no layer 0
    (/0 returns an error envelope — its only layer is 1); Springfield's wards live at
    layer 4. "None published" claims made without a folder-by-folder listing don't count.
  - **A COG can be the source for two counties at once** (EWG's POD covers Madison and
    St. Clair), and **a regional org can be two counties' GIS of record** (TCRPC serves
    Logan and Woodford).
  - **The ISBE's static precinct-maps mirror** holds county-produced vector PDFs
    (Stephenson's 2014 special-district maps, 2021 precinct sets) — check the vintage
    before using any of it.
  - New members of the Cloudflare-challenge class (solvable, browser rung): lakecountyil.gov,
    cityofharvard.org, morrisil.org, O'Fallon's site, Rock Island's city-code library.

  **Guidebook drift fixed in the same change** (maintenance-contract rule 1, applied
  late): the concept-matrix and inventory rows for county-precinct, fire/park/library,
  judicial-subcircuit and ward now list every shipped county (they had drifted up to
  twelve counties behind index.html); the municipality counts moved to 360/thirteen
  counties; congress's pattern column reads Chamber (it migrated off its bespoke block in
  2026-07); PASS 5j's claim that Whiteside sits in the 15th Circuit is corrected (14th);
  the empty-counties explainer now names Bureau/Henry/Mercer/Jo Daviess; and two
  index.html comments were corrected (the Madison fire loader's phantom "Logan" entry;
  Rock Island's "two ward-electing cities" — it has four).

- **RESEARCH PASS 5 (2026-07-30) — the northern tier: DeKalb SHIPPED, and the ring's
  last interior notch is closed.** Four counties sit on the northern frontier —
  DeKalb (037), Ogle (141), Lee (103) and Stephenson (177). DeKalb was the one that
  mattered most: it touches SIX already-served counties (Boone, McHenry, Kane, Kendall,
  LaSalle, Winnebago) and was greyed out between all of them, so the wash had a bite
  taken out of it. Adding it made the metro outline *smaller* (25.7 KB → 25.4 KB) because
  the notch it filled cost more vertices than the county's own edge does.

  **DeKalb was recorded as having no GIS at all. That was wrong.** The `dekalb-county-gis`
  gap said "ArcGIS Online results for DeKalb are dominated by DeKalb County GEORGIA…
  three plausible self-hosted hostnames do not resolve", and both halves were true — but
  the conclusion wasn't. The county runs a 72-service ArcGIS Online org
  (`services7.arcgis.com/hEXJrPwm89CLXBYe`), found the way LaSalle's, Winnebago's and
  Madison's were: follow the county's own site to a web map, read its operational layers.
  Hostname guessing has now failed in five counties and the web-map route has worked in
  five; **stop guessing hostnames**.

  | concept | DeKalb (100,420) | source | shipped |
  |---|---|---|---|
  | `county-board` | 12 districts × 2 members | `District_AreaEffective2022/0` + weekly roster | **yes** |
  | `county-precinct` | 69 | `Precincts/1` | **yes** |
  | `fire-district` | 18 | `PT_Fire_Districts/4` | **yes** |
  | `library-district` | 13 | `PT_Library_Districts/7` | **yes** |
  | `park-district` | 6 | `PT_Park_Districts/9` | **yes** |

  Five consolidated concepts from one org, and **not one new layer** — the county-expansion
  invariant (`docs/EXPANSION_GUIDE.md` Part 2) working exactly as written.

  **The board looked like rule-4 branch 1 and isn't.** `District_AreaEffective2022`
  declares `Member1`/`Member2` with their own phone and e-mail columns, which is the
  signature of a county whose officeholders ride the boundary. Measured: both phone
  columns are populated on **0 of 12** districts and `Member2_EMail` on 10 of 12, while
  the county's own members page carries party, term, **22 phones and 24 e-mails**. A
  schema is not data. So DeKalb is a roster join — GIS for geometry, weekly scrape for
  people — and the Board Chair (published on a separate chairperson table, first row =
  sitting chair) rides the matching member's row rather than a countywide section,
  because DeKalb's board elects its chair from among its own 24 members.

  **Two bugs this county surfaced, both of the silent kind:**
  1. *The scraper's first parser attributed one member's phone to another.* Two members
     publish no phone; a fixed line-window scan ran past the end of their blocks and
     picked up the next member's number. Blocks are now bounded by the next block's start
     before any field is read, and each block's "Map of County Board District N" link is
     cross-checked against its declared district.
  2. *This ArcGIS org's `f=geojson` output is lossy.* A multi-PART polygon comes back as a
     single `Polygon` with every part's rings concatenated — DeKalb Park is 48 parts
     flattened into a 49-ring "Polygon". Under GeoJSON semantics ring 0 is the outside and
     the rest are holes, so any part sitting inside another part becomes a false hole.
     Measured against the same features read as Esri JSON: **1.6 km² of the park tiling
     (0.44%) and 1.2 km² of the fire tiling (0.08%)** answered "no district" while being
     in one, with two single holes over 1 km² each. Esri JSON keeps the part structure in
     ring WINDING, so the DeKalb loaders fetch `f=json` and reassemble
     (`esriRingsToGeoJSON`). **Worth re-testing on the other AGOL-hosted counties**
     (Logan, Sangamon, Madison's `/serverh`) — the quirk is the writer's, not DeKalb's.

  **The other three northern counties are blocked on geometry, not on rosters** — each is
  a recorded gap with a measured blocker:
  - **Ogle — SHIPPED, see pass 5b below.** The composition existed after all; it was in
    the resolution that adopted the map, not on any page describing it.
  - **Lee** — publishes its district composition precisely (D1/D2 are whole townships,
    D3 = Dixon 1-9, D4 = Dixon 10-17 + Palmyra 2) but no precinct geometry; its ArcGIS
    Enterprise portal exposes zero public items. Census 2020 VTDs contain all 46 named
    precincts **plus Dixon 18, 19 and 20**, which the county's list does not — the two
    vintages disagree about how Dixon township is cut, and Dixon township is exactly the
    D3/D4 line. Palmyra is split too. A township dissolve would misplace the county seat.
  - **Stephenson — composition FOUND, geometry still missing (see 5c).** The maps are
    vector, not scans, and the composition reads off them; one township's precinct
    boundaries are what block the build.

  Next out are Carroll, Jo Daviess and Whiteside, none of which touch the ring today.
  (Carroll and Jo Daviess both do now — see 5e. Carroll shipped; Jo Daviess is a
  recorded gap.)
  Whiteside is worth noting for later: its AGOL org publishes `PrecinctWardMap`,
  `ElectionGeography_public` and a `MyElectedRepresentatives` table — the Esri Elections
  solution, the same family DeKalb and McLean use — so it would be a cheap county to build
  **once Ogle or Lee connects it**. (Ogle did — see 5b. Whiteside is now one county out,
  behind Carroll or Lee.)

- **RESEARCH PASS 5b (2026-07-30) — Ogle SHIPPED. THE COMPOSITION WAS IN THE
  RESOLUTION, NOT ON ANY PAGE ABOUT THE DISTRICTS.** Pass 5 recorded Ogle as
  no-source after checking the GIS, the AGOL org, the precinct PDF atlas, the
  county board pages and the clerk's yearbook. All of that was accurate and the
  conclusion was still wrong. Illinois counties adopt a reapportionment by
  **resolution** (55 ILCS 5/2-3001), and a resolution is a numbered document in a
  monthly PDF — not a page in the section that describes the thing it created. Ogle
  archives every resolution and ordinance it has passed since 2007; all 460 were
  scanned, and the composition was in two of them.

  **`RESOLUTION R-2021-1106` (adopted 2021-11-16)** names all 52 precincts of the 8
  districts, 24 members, effective December 2022 to December 2031. It supersedes
  **R-2021-0607** (June 2021), whose District 5 read "Marion Township precincts 1, 2,
  and 3, and Rockvale Township precincts 1 and 2" and named **Leaf River nowhere at
  all** — a township in no district. The November text adds it. That is a useful
  calibration on trusting a single published document: the county's own first
  adopted plan had a township-sized hole in it, and the builder's
  every-precinct-claimed-exactly-once guard is what reproduces the catch.

  The build (`scripts/build_ogle_board_districts.py`) dissolves **Census 2020 voting
  districts** — the precincts the resolution is written in — and the match is exact:
  52 precincts named, 52 VTDs published, one for one, nothing left over on either
  side. This is the same "compose published boundaries per a published rule" move as
  Livingston, one level down from townships to precincts.

  Two things make it checkable rather than merely plausible:
  - **23 of the 24 townships are corroborated against a second census layer.** Only
    FLAGG (the city of Rochelle) is split, between districts 3 and 4 — so every other
    district edge is also a township edge, and the builder asserts that each whole
    township is exactly reconstructed by its own precincts in the county-subdivision
    layer. Two independently generalized census layers have to agree about where the
    county's internal lines run, and they do at every sampled point.
  - **The one divergence is recorded and shown to be harmless.** The county has since
    retired FORRESTON 3 and now runs 51 precincts (its 2025-2027 yearbook lists
    Forreston 1 and 2 only, in the polling places and both parties' committeeperson
    lists). Forreston 1, 2 and 3 are all in District 7, so the union — and therefore
    the district line — is unchanged. The split-township assertion is what keeps that
    true going forward: a re-precincting that divided a second township would fail the
    build rather than ship a line the county never drew.

  The roster half was already in hand from pass 5 and needed only a scraper: 24/24 with
  party, phone and e-mail, plus the Board Chair and Vice Chair, from the county's staff
  directory. That page beats the county's own yearbook, which still prints District 8's
  second 2028-term seat as vacant.

  **The lesson worth carrying: when a county publishes officeholders but no district
  geometry, read its resolutions before recording a no-source gap.** Lee and Stephenson
  were the immediate re-tests; Stephenson's is 5c below.

- **RESEARCH PASS 5c (2026-07-30) — Stephenson: composition FOUND and verified, one
  township's geometry short of shippable. NOTHING SHIPS.** The Ogle lesson was applied
  and it half-worked. Stephenson does not publish a resolution archive the way Ogle does
  — its board minutes are SCANS, 162 of the 220 documents from 2021-2022 carrying no
  text layer at all, and a full-text sweep of those 220 found one irrelevant hit. But the
  earlier entry's premise was wrong in the other direction: the county's two adopted
  district maps are **vector PDFs with real text layers**, not scans, and the composition
  reads straight off them.

  | district | composition | printed pop | township sum |
  |---|---|---|---|
  | F | Winslow, West Point, Waddams, Kent, Jefferson | 5398 | **5398** |
  | G | Oneco, Buckeye, Dakota, Lancaster, Silver Creek | 5356 | **5356** |
  | H | Rock Grove, Rock Run, Ridott | 5037 | **5037** |
  | I | Erin, Harlem, Loran, Florence | 5195 | **5195** |
  | B | Freeport precincts 01, 02, 03, 06 | 5875 | — |
  | C | Freeport precincts 04, 05, 07, 10 | 5834 | — |
  | D | Freeport precincts 08, 09, 13, 14 | 6003 | — |
  | E | Freeport precincts 11, 12, 15, 16 | 5966 | — |

  The rural half is confirmed **three independent ways**: read by eye, read by machine
  from the PDF's own fill colours (the legend defines colour → district), and by
  arithmetic — each district's township populations sum EXACTLY to the total printed on
  the same map. Four exact sums is not a coincidence. The Freeport half was machine-read
  the same way, four precincts per district, no ambiguity.

  **What blocks it is one township.** The county re-precincted after the census: Census
  2020 publishes FREEPORT 1-18, the county now runs Freeport 01-16, and B/C/D/E are drawn
  from the 16 — a different division of the same township, so census voting districts
  cannot draw those lines. (Waddams 2→1 and West Point 3→2 changed too and are harmless:
  both sit wholly inside District F, the Forreston-3 situation again.) Freeport Township
  is **53% of the county**, so shipping F-I alone would answer "no district" for most
  Stephenson residents — worse than not shipping, so nothing ships.

  Sources checked and empty for precinct geometry: no county GIS server; no ArcGIS Online
  presence beyond third-party research layers; the assessment office points at **WinGIS**,
  which turns out to serve Stephenson only an address locator (`StephCoCompostie`) and no
  boundary layers; and the Illinois SBE's GIS viewer (gis.elections.il.gov) is down —
  503 over HTTP, no HTTPS at all.

  **One file would close this county**: Freeport Township's current 16 precinct
  boundaries in any vector form. Everything else is already in hand.

  **STATUS: the operator took the georeferencing option, and Stephenson SHIPPED.** See
  5d below. The gap stays open, narrowed to that one file, because traced geometry is
  not published geometry.

- **RESEARCH PASS 5d (2026-07-30) — Stephenson SHIPPED with the fleet's first and only
  GEOREFERENCED boundary, and the first card that tells the reader its boundary is
  approximate.** The Freeport map is a vector PDF: its 16 precinct polygons are real
  paths, its legend maps fill colour to district, and the polygons share exact vertices
  (710 of 2,507 edges cancel in a dissolve). So the missing geometry was recoverable
  without a new source, and on the operator's call it was recovered.

  **How it is fitted.** The 16 polygons dissolve to a union outline; that outline is
  matched to the TIGER county-subdivision polygon for Freeport — the same geographic
  area — by trimmed ICP solving a 6-parameter affine. Trimming matters: the precinct map
  carries interior enclaves the TIGER outline does not, and an untrimmed fit drags on
  them (RMS 639 m before trimming, 10.9 m after).

  **How it is checked — this is the part that makes it publishable.** The fit is measured
  two ways, both re-run on every rebuild with floors that fail the build:
  - *Control*: PDF union outline vs TIGER Freeport subdivision — median **1.6 m**,
    RMS **10.9 m** over the 80% of vertices with a counterpart.
  - *INDEPENDENT*: the map's own HYDROGRAPHY layer, which the fit never touched, against
    TIGER hydrography — **98.9% of vertices within 50 m, median 15.7 m**. A transform
    fitted on one feature class landing a different one within ~16 m is the evidence;
    the control number alone would only prove the fit converged.

  So a Freeport district line is good to roughly 15-20 m, a fraction of a city block.
  **The card says so** — the four derived districts carry a Boundary note reading
  "Traced from Stephenson County's published district map (adopted 2022) … accurate to
  about 20 metres — treat the district line itself as approximate." The four rural
  districts carry no such note because they are exact township edges. That asymmetry is
  the point: the app has one boundary that is a measurement rather than a fact, and it
  is labelled where a reader will see it, not only in a build script.

  Two smaller things this county forced:
  - **A hand-rolled ring walk swallowed a district.** Chaining the dissolved boundary
    edges with a naive "walk until a dead end" produced a district B polygon that
    contained district D's own map label. build_metro_outline's `dissolve()` closes each
    ring back to its start instead; the anchor check caught it, and the shared
    implementation is now used.
  - **A roster e-mail belonging to someone else.** District C's member is linked to his
    predecessor's address (tmckenna@). The scraper drops any mailto whose local part does
    not contain the member's surname — publishing it would have put a real, wrong
    person's inbox on a card. It fires on exactly one seat today.

  This script should be **deleted, not maintained**, the day Stephenson publishes
  precinct geometry.

- **RESEARCH PASS 5k (2026-07-31) — DeKalb, Ogle and LaSalle: the same question asked
  of three counties that were already served, and three different answers.** All three
  were shipped counties; this pass asked what each still publishes that the app has not
  consumed, and — for the first time in this series — found two live data DEFECTS rather
  than only absent sources.

  | concept | DeKalb (100,420) | Ogle (50,832) | LaSalle (109,658) |
  |---|---|---|---|
  | `county-board` | already shipped (12x2) | already shipped (8, derived) | already shipped (29) |
  | `county-precinct` | already shipped (69) | **none published** — gap | already shipped (119) |
  | `fire` / `park` / `library` | already shipped (18/6/13) | **none published** — gap | **none published** — gap |
  | municipal officials | **+14 municipalities, 118 officials** | already shipped — **2 defects fixed** | already shipped (26) |
  | `ward` | **+19 wards across 4 cities** | none published — gap | **+4** (Mendota only) |
  | `judicial-subcircuit` | n/a (23rd Circuit) | n/a (15th) | n/a (13th) |

  **Two defects were already shipping, and neither would have been found by a count
  guard.** Both were in the Ogle yearbook parser, and both are the same class of error —
  a parser that is *right about shape* and *wrong about where the shape stops*:
  - Stillman Valley shipped **ten trustees who are phrases**: "Other Special Districts",
    "Library Districts Townships", "www.census.gov". The section-end sentinel named the
    POLLING PLACES heading, which is one heading too late — GENERAL INFORMATION sits
    between them, its levy-deadline list is indented, and the last municipality's still
    open "Trustees" group swallowed it. The bound is now the next ALL-CAPS heading of any
    kind, which was measured before it was adopted: four lines in the whole book match
    that shape after the start, the first is GENERAL INFORMATION, and no line inside any
    municipality block matches at all.
  - **Rochelle, the county's largest city, shipped with no council** — a mayor, a clerk,
    a treasurer and nothing else. Its six seats are printed under the heading
    "Councilmen", and the parser's group vocabulary knew Trustees, Council Members,
    Commissioners and Aldermen. One word.

  The lesson generalises past this parser: **a floor counts what you got, not what you
  should have got.** 114 officials passed a floor of 90 while ten of them were sentences
  and six real ones were missing, because the two errors ran in opposite directions. What
  caught both was reading the shipped file back — per-municipality board sizes, sorted —
  and noticing that a village had sixteen trustees and a city of 9,600 had none. That
  read is cheap and belongs in every roster pass.

  **DeKalb was the county with the most left on the table, and its clerk publishes the
  richest municipal document in the fleet.** The Reference Yearbook's "Municipalities of
  DeKalb County" section carries all 14 municipalities' full governing bodies *plus the
  date each seat is next on the ballot* — nothing else sourced does that. Three of the 14
  were already in the roster at a shallower depth from a neighbouring county (Maple Park
  from Kane, Sandwich from Kendall, Somonauk from LaSalle); depth precedence took the
  first two automatically, and Somonauk needed a tie-break entry because both counties
  publish its full board and name the same five trustees. DeKalb wins it on two grounds
  stated in the builder: the village hall is in DeKalb County, and DeKalb's book dates
  every seat.

  Two rows the DeKalb scraper drops by rule, both logged:
  - a seat published as **"Vacant"** (Somonauk) is not a person;
  - a name published **both as head of government and as a board member** (Hinckley's
    Sarah Quirk) keeps only the head row. An Illinois village president is elected to
    that office separately and cannot also hold a trustee seat, so one row is stale. That
    is a rule about what the source can be saying at once, not a guess about which name
    is right — and because it leaves Hinckley one trustee short of a six-member board, it
    is recorded as a gap rather than quietly absorbed.

  **The ward frontier moved by two entries and stopped at a raster.** DeKalb County's own
  org publishes one ward layer per ward-electing municipality — DeKalb 7 (as 8 polygons;
  Ward 7 is two parts), Sycamore 4, Genoa 4, Sandwich 4 — all edited 2023-11, after the
  redraw, which is the measurement that decides whether a ward layer ships. Mendota
  publishes its own four, edited 2022-12. Every one of those five cities' aldermen was
  *already* in the roster, so all twenty-three cards named their seats the day the
  geometry landed — verified point by point before shipping. The three that did not make
  it are instructive: **La Salle publishes a ward map as a single PNG**, Peru and Earlville
  publish nothing, and Byron and Polo publish nothing — so five cities whose seat-holders
  the app already knows still cannot answer "which ward am I in". That asymmetry (roster
  ahead of geometry) is the mirror image of Rock Island's in pass 5j, where the geometry
  shipped and nobody could be named.

  **Ogle and LaSalle are now the two counties measured hardest for special districts and
  found to publish none.** Not "not found" — enumerated: Ogle's entire ArcGIS Online org
  is 91 services of cemeteries, bike routes, COVID points and survey forms, and its
  parcel viewer is a Beacon/Schneider product with no REST endpoint; LaSalle's own ArcGIS
  Server was listed folder by folder and carries zoning, flood, wetlands, parcels, tax
  maps, corporate boundaries, board districts and the polling-place locator, and no
  taxing-district layer at all. Both counties levy for fire, park and library districts
  and print their names and rates in tax tables. A name is not a boundary.

  **Ogle's precincts are the one gap where the data exists and still cannot ship.**
  `build_ogle_board_districts.py` already dissolves the Census 2020 voting districts into
  the county's eight board districts, so the 2020 precinct geometry is in hand. But the
  county has since retired Forreston 3 and runs 51 where the census has 52. That cannot
  move a board-district line — Forreston 1, 2 and 3 are all in District 7, so their union
  is unchanged, which is exactly why the dissolve is still sound — but shipping the VTDs
  as *precincts* would put a precinct on a card that no longer exists, and nothing
  published says where its territory went. Same data, different claim, different answer.

- **RESEARCH PASS 5j (2026-07-31) — enriching the three newest counties. Rock Island
  went from 2 concepts to 6; Lee and Whiteside had nothing safe left to add.** The
  question this pass answers is not "which county is next" but "what does a county we
  already serve still publish that we have not consumed".

  | concept | Lee | Whiteside | Rock Island |
  |---|---|---|---|
  | `county-board` / `county-precinct` | already shipped | already shipped | already shipped |
  | `fire-district` | already shipped (22) | none published | **+17** |
  | `library-district` | none published | none published | **+9** |
  | `park-district` | none published | none published | **+1** (Cordova) |
  | `ward` | n/a | published but STALE — gap | **+11** (Moline 7, Silvis 4) |
  | `judicial-subcircuit` | structurally n/a | structurally n/a | structurally n/a |

  **The subcircuit answer is a clean structural negative, not a gap.** PA 102-0693
  created subcircuits in exactly nine circuits, and the enacted archive carries exactly
  those nine (3rd, 7th, 12th, 16th, 17th, 18th, 19th, 22nd, Cook). Lee sits in the
  **15th**, Whiteside and Rock Island in the **14th** — neither circuit received any. That is the same
  answer Kendall's 23rd already has: the layer honestly hides there, and no artifact
  would change it.

  **Rock Island's TaxDistricts service is a Cook-shaped tax-agency tiling** — one layer
  per levying body, ten in all, of which three are fleet concepts. Worth noting how the
  cards read: Moline, Silvis and Rock Island city all resolve to **no** fire, library or
  park district, and that is correct rather than a join failure. Incorporated cities run
  their own departments on a city levy; only unincorporated ground and small towns sit
  in a district. Cordova, at the county's north-east corner, resolves all three.

  **The one-feature park district is honest, not thin.** Rock Island levies exactly one
  (Cordova). A tiling of one is the accurate shape of that county's park provision, and
  everywhere else the card correctly finds nothing.

  **Two ward layers shipped and six municipalities' worth did not — on vintage alone.**
  Moline (7 wards, edited 2022-08) and Silvis (4, edited 2022-01) both postdate the 2020
  census, so they reflect the redraw a resident is currently voting under. Whiteside's
  `PrecinctWardMap` carries 22 wards across Sterling, Rock Falls, Morrison, Fulton,
  Prophetstown and Erie — more municipalities than Rock Island's two — and was last
  edited **2019-11-05**, before the census that would have redrawn them. It is recorded
  as a data-quality gap rather than shipped. *Municipal wards are redistricting
  geometry; an edit date that predates the decennial census is a snapshot, exactly as it
  was for Freeport's alderperson column and Whiteside's own MyElectedRepresentatives.*
  The same service's precinct layer (2015, with a polling-place NAME on every row) was
  likewise NOT used to fill the five precincts whose polling join fails — an
  eleven-year-old address is worse than an honest blank.

- **RESEARCH PASS 5i (2026-07-31) — Mercer and Jo Daviess: NEITHER SHIPS, and the
  Jo Daviess blocker survives its re-test.** Both were researched to the same depth as
  the counties that did ship; both came back genuinely empty.

  **Jo Daviess — the recorded gap was right, and is now sharper.** Every clause was
  re-tested and every one held: the composition is published (better than recorded —
  in prose on the board page, member by member, rather than only as PDF titles), 14 of
  17 districts are still made of PARTS of precincts (District 10 is a fraction of a
  single one), the GIS at `gismaps.jodaviess.org` is still a vendor `gwmpub.aspx`
  viewer with no REST endpoint, and the countywide district map is still a raster —
  measured this time: **32 embedded images and 261 characters of text**, which is the
  title and the legend.

  What changed is the *wanted*. The county's GIS department **sells** this data: it
  runs a paid subscription mapping site and publishes a "Digital Data Order Form". The
  district shapefiles demonstrably exist and are simply not public, so the unlock is a
  licensing or records question, not a technical one. That is a materially more
  actionable gap than "the legal descriptions are not on the redistricting page".

  **One wasted-effort note worth keeping: the county moved domains.** It is now
  `jodaviesscountyil.gov`; the old `jodaviess.org` answers *every* path with its home
  page, so `/redistricting` returns HTTP 200 and 81 KB of news items. A 200 that looks
  like a hit is worse than a 404 — check the body, not the status. The redistricting
  page, the 17 district PDFs and the GIS page are all on the new domain, and a web
  search found it in one query after direct probing had stalled.

  **Mercer — a new gap, and an unusually clean one to state.** It elects ten members
  from five two-member districts and publishes them well (party, home town, term
  expiry, Chairman flagged). It draws the districts nowhere. There is no county GIS at
  all — parcels go to a third-party tax vendor, and every "Mercer County GIS" result is
  a commercial aggregator rather than the county. The board page itself says *"Mercer
  County Board Districts, Map and Contact List are found in the Document Section"* —
  and they are not: the public index carries 90 PDFs across eight folders and none is a
  district map, composition list or reapportionment ordinance.

  **The frontier is now entirely gaps.** Every county adjacent to the served ring —
  Bureau, Henry, Mercer, Jo Daviess — has been researched and each is blocked on a
  named artifact rather than on effort. Expansion by adjacency has run out; the next
  county needs someone to publish something, and the four `wanted` fields say exactly
  what.

- **RESEARCH PASS 5h (2026-07-31) — Rock Island SHIPPED; Bureau and Henry are
  recorded gaps with rosters and no boundary.** The three counties the previous pass
  left as the frontier, researched together.

  | concept | Rock Island (145,415) | Bureau (33,244) | Henry (49,317) |
  |---|---|---|---|
  | `county-board` | **SHIPPED** — 19 SINGLE-member districts, the most of any county here; GIS + weekly roster (party, term, Chair/Vice-Chair) | **gap** — 18 districts drawn nowhere public | **gap** — 2 districts, raster map only |
  | `county-precinct` | **SHIPPED** — 120 | none published | per-township PDFs only |
  | roster available? | yes (county page) | yes, 16 of 18 seats | yes, with e-mail + phone |

  **Rock Island pushed the app past its own western edge.** It is the first served
  county on the Mississippi, reaching -91.07, and `build_metro_outline.py` refused to
  write: *"permalink_gate.minLng is -90.8500 but the served area reaches -91.0721 —
  widen it, or a point there is silently rejected."* That is the whole value of that
  guard. A shared or embedded permalink in Moline would have been dropped on load with
  no error, and nothing else in the pipeline would have noticed. `metro_bbox` (the
  address-geocoder bound) and `permalink_gate` both moved west.

  **Bureau is the first county in the served ring with no GIS at all.** Not a portal
  that hides its items (Lee), not a vendor viewer without a REST root (Jo Daviess) —
  nothing. Its site's only mapping links are a Google MyMaps document and a
  third-party tax lookup, and the promising-sounding "2024 Bureau County Handbook" is
  an HR employee handbook. It publishes 18 board members with parties and draws its 18
  districts nowhere.

  **Henry is the "Alternate" case, and it is a deliberate refusal.** Its only
  board-district document is a raster PDF (0 extractable characters, one image object)
  titled **"Alternate Two Board"**, whose colour legend is SCHOOL districts with the
  board line drawn over the top. The county does seat exactly 2 districts, which
  corroborates the structure — and the line does appear to follow township boundaries,
  so Carroll's dissolve recipe would apply immediately. It is still not built, because
  *"Alternate"* means this was one option among several and nothing published says it
  was the adopted one. **Ogle already priced this mistake**: its June 2021 map omitted
  Leaf River entirely and was superseded in November. A map that is probably right is
  not a source.

  Worth noting against the pass-5g lesson: re-testing a recorded gap is cheap and
  sometimes overturns it (Lee), but it does not follow that every gap is soft. Bureau
  and Henry were researched to the same depth as Lee and came back genuinely empty.
  The difference is that Lee's blocker asserted something checkable and false ("the
  REST instance is not reachable"), while these two assert an absence that survives
  the check.

- **RESEARCH PASS 5g (2026-07-31) — Lee and Whiteside SHIPPED. The Lee blocker was
  wrong, and the way it was wrong is the same way DeKalb's was.** Both counties became
  reachable once Ogle, Stephenson and Carroll landed, and both went in together.

  | concept | Lee (34,096) | Whiteside (54,979) |
  |---|---|---|
  | `county-board` | **SHIPPED** — 4 districts × 5 members, county GIS + a weekly roster scrape (party, seat's next election, e-mail 20/20) | **SHIPPED** — 3 districts × 9 members = 27, the largest board in the served area; branch 1, members ride the boundary |
  | `county-precinct` | **SHIPPED** — 46, identity + board district | **SHIPPED** — 60, identity + board district + polling place (join 55/60, gap recorded) |
  | `fire-district` | **SHIPPED** — 22, NG911 service areas | none published |
  | municipal officials | **rule-4 floor** — recorded gap | **rule-4 floor** — recorded gap |

  **"Its REST instance is not reachable" was an assumption about a URL.** Pass 5 recorded
  Lee as no-source after finding that its ArcGIS Enterprise portal returns zero items to a
  search. That half is literally true and still is. But the portal's **featured group**
  holds eleven items, one of them "Voting Districts & Election Precincts", and that app's
  web map names the real REST root: **`gis.leecountyil.gov/leecogis`** — not `/server`,
  not `/arcgis`, which is what had been tried. Sixth county where the web-map route found
  what hostname guessing missed, and the second time (after DeKalb) that a *recorded gap*
  was the thing standing in the way rather than the county.

  The correction is bigger than a URL. The gap said Lee's districts could only be
  reconstructed by dissolving precincts, and that Census 2020's Dixon 18-20 disagreed with
  the county's precinct list on exactly the D3/D4 line — a careful, correct piece of
  analysis about a problem that **does not exist**: the county DRAWS its four districts,
  so there is nothing to dissolve. *An unbuildable recorded with a detailed blocker reads
  as more authoritative than one recorded with a vague one, and is no more likely to be
  true.*

  **Whiteside publishes its board TWICE, seven years apart, with no cue which is which.**
  Its org carries both `ElectionGeography_public/2` (Electoral Districts) and a
  `MyElectedRepresentatives` service, and both hold county-board members — with
  *different names*. Measured: MyElectedRepresentatives' `dataLastEditDate` is
  **2019-01-08** and only 11 of its 27 names appear on the county's current board page;
  ElectionGeography's is **2026-07-10** and matches **27/27**. Nothing in either service's
  name or description says which is current. This is the Freeport `Wards2022_Public`
  lesson repeating inside a single org, and it is now the reason the edit-date check is
  written into `docs/EXPANSION_GUIDE.md` §2.3 rather than left as a habit.

  Two smaller things worth keeping:
  - **Whiteside's Electoral Districts layer holds every office in one table**, keyed by
    `electedoffice` — county board, congressional, legislative and the countywide row
    offices all overlapping the same ground. The board rows are filtered out **in the
    loader**, not at query time: an unfiltered containment test answers with whichever
    polygon comes first, and the map overlay would have drawn 21 shapes instead of 3.
  - **Lee's roster PDF needs positional parsing for a reason worth naming.** `pypdf`
    flattens it into 20 name rows followed by 20 e-mail addresses *in a different order*.
    Pairing by sequence mis-assigns addresses to people; pairing by initial-and-surname
    would be an inference, and it would fail on the one row that matters most — the Board
    Chair's address is `leecochair@countyoflee.org`, which no name rule produces. Read by
    row, it is simply what the document says, and the chair it identifies cross-checks
    against the board page's prose ("Bob Olson, Board Chair").

  **Neither county publishes municipal officers**, and all four sourced rungs were worked
  before that was recorded: no clerk elected-officials database, no yearbook or municipal
  directory on either clerk's site (their only `/directory.aspx` is county staff), no
  member list from Blackhawk Hills Regional Council, and — the near miss — Lee's GIS does
  carry a `Municipalities` layer, but it is `CORP_NAME` and nothing else, where Lake's
  equivalent carries hall address and phone. Twenty-four municipalities keep the
  identity-only card; two gaps record what would lift them.

- **RESEARCH PASS 5f (2026-07-31) — municipal officials for the three new northern
  counties. Ogle and Stephenson are the fleet's FIFTH and SIXTH full-governing-body
  counties; Carroll joins at mayor level; and Freeport is the first county seat a
  county source omits entirely.** The three counties had just shipped their board
  districts, and the highest-value follow-on was the concept that touches every town in
  them rather than one district line.

  | county | source | depth | live |
  |---|---|---|---|
  | Ogle | Clerk's yearbook, "OGLE COUNTY CITIES & VILLAGES" | **full body** + hall address/phone/website | 13 munis / 114 officials / 13 heads |
  | Stephenson | county Cities & Villages directory page | **full body**, each office marked (Elected)/(Appointed) | 10 munis / 82 officials / 9 heads |
  | Carroll | Clerk's yearbook, "Cities and Village Officers" | head + clerk (the county prints no trustees) | 7 munis / 13 officials / 6 heads |
  | Freeport | the CITY's WordPress person directory | **full body** + per-seat e-mail/phone | 10 officials / 8 council seats |

  **The county seat was missing from its own county's directory.** Stephenson's page is a
  VILLAGE directory: it carries all ten villages and not Freeport, which is ~23,600 people
  — more than half the county's municipal population. Left alone, the largest city in the
  county would have been the only one whose card named nobody. It enters as an `--enrich`
  payload, the path Lockport and Wilmington already take, which inserts a municipality the
  county source omits wholesale rather than merely filling contact.

  **A tidy-looking GIS layer was the wrong source, and only measurement showed it.**
  Freeport publishes a `Wards2022_Public` FeatureServer whose features carry an
  `Alderperson` field — apparently rule-4 branch 1, officeholder riding the boundary. Its
  `dataLastEditDate` is **2024-05-21**, so it still named the 2nd Ward's pre-2025-election
  holder. The city's WordPress directory had the current one. *A live service is not a
  current service; check the edit date before trusting an officeholder column.* The
  geometry would still be sound if ward polygons are ever wanted.

  **Three parser bugs this pass surfaced, all in the silent class:**
  1. *`norm_place()` ate the second word of "Rock City".* It stripped both the "City of"
     PREFIX and a trailing `village|city|town` SUFFIX, so a source publishing BARE names
     — Stephenson's page, Winnebago's GIS layers — reduced "Rock City" to "Rock", which
     matches no Census place. The two sides label the government form on opposite ends,
     so they now have separate normalizers: `norm_census_place()` strips the suffix,
     `norm_place()` the prefix. Measured first: **no** source in the file emits a
     Census-style suffix, so the split is safe.
  2. *Ogle's Adeline shipped an address that appears on no document.* Adeline is the one
     block labelling a PHYSICAL and a MAILING address, and they are different places
     (8763 vs 9069 N. Main St, and the mailing city is Leaf River, not Adeline). The old
     scan took the street from one and the city/ZIP from the other. Header lines are now
     grouped by label and never blended. Same fix run caught Rochelle's ZIP+4 failing a
     `\d{5}$` anchor, which had silently dropped that city's whole locality.
  3. *Non-people and non-offices were about to ship as officeholders.* Stephenson lists
     Davis's zoning board and German Valley's "Village Police (Hired)" beside the real
     officers, one with the name "Unassigned"; Carroll's Thomson president reads
     "Vacant". Both are dropped and REPORTED, never silently. The one combined title
     ("Trustee/Zoning Chairperson") is reduced to the seat he actually holds rather than
     dropped with the committee.

  **A side effect worth keeping:** the builder now takes a bare-named municipality's
  legal form from the Census reference file's own designation ("Rock City village" →
  "Village of Rock City"), so those cards say "Village Hall" instead of the generic
  "Municipal Hall". It applies only where the source publishes no form — a source that
  states one keeps its own wording, since "United City of Yorkville" is the city's legal
  name and Census's plain "City of Yorkville" would be a downgrade.

- **RESEARCH PASS 5e (2026-07-31) — Carroll SHIPPED; Jo Daviess is blocked below the
  precinct.** Both counties became adjacent once Ogle and Stephenson landed, so both
  were researched together.

  **Carroll — the easiest county in three passes.** Its three districts run EXACTLY
  along township lines, so the composition reads straight off the county's published
  map and the boundary is a plain TIGER township dissolve — the Livingston recipe
  unchanged, no georeferencing needed even though the map itself is a raster export.

  | district | townships | printed 2020 pop |
  |---|---|---|
  | 1 | Washington, Woodland, Freedom, Salem, Savanna | 5190 |
  | 2 | Mount Carroll, York, Fairhaven | 5459 |
  | 3 | Cherry Grove-Shannon, Rock Creek-Lima, Wysox, Elkhorn Grove | 5053 |

  The one reconciliation is **forced, not chosen**: the map labels Carroll's two
  CONSOLIDATED townships by their historic halves (Cherry Grove + Shannon, Rock Creek
  + Lima) where TIGER carries the merged names, and both merged townships sit wholly
  in District 3, so no district line depends on the distinction. Unlike Stephenson
  there is no per-township population printed, so the check that carries the weight is
  completeness: all 12 TIGER townships claimed exactly once.

  Two things Carroll forced out:
  - **Two labels collapsing onto one township broke the dissolve.** Passing the same
    feature twice makes every edge cancel, which surfaces as `FATAL: open chain` — a
    message about tiling, not about duplicates. The members are deduped before the
    dissolve now.
  - **The county has "District" typo'd as "Distirct" on one row**, and the first
    scraper silently dropped that member. On a three-member district a card showing
    two names looks entirely normal. The pattern now tolerates the transposition, the
    scraper logs it, and the roster's member floor is the FULL board of 9 rather than
    one under — on a board this small, a floor with slack would have let it through.
    (The county also writes ROMAN numerals where its map uses Arabic; the scraper
    converts, or the join would silently find nothing.)

  **Jo Daviess — blocked below the precinct, and the first county where that is the
  reason.** It publishes the composition of all 17 districts, as the titles of 17
  per-district PDFs. But **14 of the 17 are made of PARTS of precincts**, and the
  county's own GIS memo of 2021-12-02 says why: *"If one of those boundaries needed to
  be split I used roads."* Only districts 1, 3 and 16 are whole precincts, so even
  precinct geometry would not finish the county — the lines are sub-precinct.

  And the Stephenson route does not transfer: its GIS is a vendor `gwmpub` viewer with
  no REST endpoint, and **every published map is a RASTER export** (32-81 embedded
  images, only frame-and-legend vector paths). There are no polygons to extract, so
  there is nothing to georeference. The artifact that would unlock it is named in the
  county's own memo — *"A written legal description for each district has also been
  prepared"* — and is not on its redistricting page. That is what the gap asks for.

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

  **Board members' street addresses removed from LaSalle and Madison
  (2026-07-30), settling a fleet inconsistency.** Six counties' board cards took
  two different positions on the same question: LaSalle and Madison rendered the
  address their county GIS publishes per member, while McHenry, Livingston,
  Sangamon and Winnebago deliberately never collected theirs. Measured rather
  than assumed before acting — 29 DISTINCT addresses for LaSalle's 29 members
  (including rural route numbers and a PO box) and 18 distinct for the 18 Madison
  members that have one. Those are residences, not offices, so they are no longer
  requested from either service or rendered on either card.

  That leaves a real hole in the card convention (identifier → representative →
  office LOCATION → contact → link): **no county board card in the app names an
  office you can visit**, because no Illinois county in it publishes one.
  Recorded as `county-board-office-addresses` with the likely honest fix noted —
  county boards mostly meet in one building and members have no individual
  office, so a per-COUNTY board-office address is probably the right answer
  rather than a per-member one. LaSalle's existing phone gap was reworded in the
  same change: its summary said members show "e-mail and mailing address", which
  this made false.

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
  **municipality the ward layer doesn't cover keeps its full list** (Berwyn and Waukegan were the examples until their wards shipped 2026-08-02; Rock Island city is one now),
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
| `congress` | U.S. House District | political | Chamber | pre-built (TIGERweb L0, STATE=17) | `congress-roster.json` (weekly CI; incl. each rep's district office + D.C. office from congress-legislators — the 2026-07 enrichment) | — |
| `il-senate` | IL State Senate District | political | Chamber | pre-built (TIGERweb L1) | `il-senate-members.json` (weekly CI) | — |
| `il-house` | IL State House District | political | Chamber | pre-built (TIGERweb L2) | `il-house-members.json` (weekly CI) | — |
| `county` | County | geography | Bespoke | live TIGERweb State_County | `il-county-clerks.json` (weekly CI from ISBE; Peoria deliberately absent) **+ `il-county-commissioners.json`** — the AT-LARGE board section (weekly CI): seven counties, 39 members, each proven elected countywide from a certified election document. Monroe 3 and Randolph 3 (commission form), Pike 9, Brown 7, Calhoun 5, Putnam 5, Schuyler 7. Pike/Brown/Calhoun/Putnam/Schuyler have **no dispatch entry of any kind** — this card is the only county-specific answer they have | — |
| `school-district-secondary` | High School District | schools | Polygon | live TIGERweb School L1 | — | outsideChicagoSchoolCoverage |
| `school-district-unified` | Unified School District | schools | Polygon | live TIGERweb School L0 | — | — |
| `school-district-elementary` | Elementary School District | schools | Polygon | live TIGERweb School L2 | — | outsideChicagoSchoolCoverage |
| `township` | Township / County Subdivision | geography | Polygon | live TIGERweb CouSub | — | — (subOf `county`) |
| `municipality` | Municipality | geography | Bespoke | live TIGERweb Places | `municipal-officials.json` (weekly CI; twenty-eight counties + Chicago's citywide officers, 575 municipalities — head of government + board + other elected officers + hall contact, joined by place GEOID; depth per county: full body Cook/Will/DeKalb/LaSalle/Winnebago/Ogle/Stephenson/Grundy/Livingston/Logan/Sangamon/Madison/St. Clair/Rock Island/Henry/Cass/Peoria/Tazewell/Marshall/Washington (+ McLean's three ward cities from their own pages — the county-wide source is a JS-locked Airtable interface), head+clerk DuPage/Kane/McHenry/Kendall/Carroll/Whiteside, contact-only Lake. Madison + St. Clair share the East-West Gateway POD (one COG document, two counties); Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city-level payloads fill what a county cannot: Will's ward cities and Joliet for per-seat contact, Skokie for trustee districts, and Freeport — the whole city, since Stephenson's county source is a village directory that omits its own county seat) | — |
| `judicial-subcircuit` | Judicial Subcircuit | political | CountyDispatch | Cook County GIS L5 (20 subcircuits) + L27 (municipal districts) · Will County ArcGIS · DuPage County ArcGIS (`Judicial_Subcircuits`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L1) · pre-built `kane-judicial-subcircuits.json` + `mchenry-judicial-subcircuits.json` + `winnebago-judicial-subcircuits.json` (17th) + `madison-judicial-subcircuits.json` (3rd) + `sangamon-judicial-subcircuits.json` (7th) (all PA 102-0693 enacted shapefile) — no Kendall entry: its 23rd Circuit received no subcircuits under the act (nor did the 13th/14th/15th/20th/21st, so the other expansion counties are structurally n/a) | link-only (each card links its circuit's court; Cook adds the Municipal District + courthouse row) | OR of cook/will/dupage/lake/kane/mchenry county coverages; the Winnebago/Madison/Sangamon entries use the subcircuit geometry itself as coverage, so each circuit's secondary counties answer too |
| `county-board` | County Board District | political | CountyDispatch | Cook County GIS L9 · Will County ArcGIS · DuPage County ArcGIS (`County_Board_Dist_new`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L0) · Kane County ArcGIS (`KaneCo_IL_County_Board` L1) · McHenry County ArcGIS (`McHenry_County_Board_Districts` L0) · Kendall County ArcGIS Enterprise (`County_Board_2010` — the CURRENT 2-district map: the post-2020-census reapportionment kept the line, Dec 2021 hearing) · LaSalle **derived** (`lasalle-county-board-districts.json` — the county's own precinct layer dissolved per its 2024+2026 election canvasses by scripts/build_lasalle_board_districts.py; its published board GIS is the superseded 2011-2021 map) · Kankakee self-hosted `k3gis.net` (`BASE/Elected_Officials/1`) · Winnebago WinGIS (`ElectedOfficials/26`, mounted at `/public` not `/arcgis`) · Livingston **derived** (`livingston-county-board-districts.json` — TIGER townships dissolved per the county's published composition; it publishes no GIS) · McLean (`Clerks/MyElectedRepresentatives/1`) · Logan via Tri-County RPC (`Logan_County_Districts_and_Zoning/39`) · Sangamon AGOL (`CountyBoardDistricts2020_WithURLs`) · Madison (`CountyClerk/CBDWS/0`, on `/servera`) · St. Clair (`SCC_voting_districts/2`, on `/server`) · DeKalb AGOL (`District_AreaEffective2022/0`, Esri-JSON fetch — the org's `f=geojson` is lossy on multipart polygons) · Ogle **derived** (`ogle-county-board-districts.json` — Census 2020 VTDs dissolved per resolution R-2021-1106) · Stephenson **part-derived** (`stephenson-county-board-districts.json` — 4 rural districts as TIGER township dissolves, 4 Freeport districts georeferenced from the county's vector-PDF map, the card says so) · Carroll **derived** (`carroll-county-board-districts.json` — TIGER townships per the county's published map) · Lee (`gis.leecountyil.gov/leecogis`) · Whiteside (`ElectionGeography_public/2`, board rows filtered in the loader) · Rock Island (county org, 19 single-member districts) · Woodford **derived** (`woodford-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 2020/21 #005 by scripts/build_woodford_board_districts.py; the county publishes no board GIS) · Boone **runtime-merged** (the county GIS's three per-district MapServer layers — `County_Board_Districts` indexes 0/1/2, each pre-dissolved, verified to tile the county outline — merged and district-tagged by the loader; the features' leftover census-block attributes are read nowhere) · Grundy **derived** (`grundy-county-board-districts.json` — the county's own precinct layer dissolved per the adopted 'Approved County Board Districts (10/12/2021)' map by scripts/build_grundy_board_districts.py; the county GIS publishes no board geometry, and the transcription is proven by the map's own printed populations, all three district totals to the person) · Henry **derived** (`henry-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 21-33 by scripts/build_henry_board_districts.py; the county's viewer is Sidwell Portico, parcels + townships only, and the composition is proven by the adopted map's own two-census population table and live Census POP100, all to the person) · Peoria (county open-data org, `2020_County_Board_Districts/0` — 18 SINGLE-member districts, the app's largest single-member board; chosen over the roster-carrying `ElectoralDistricts/3`, which draws the SAME lines (point-tested 8/8, the area difference projection only), because only this layer carries the per-district 2020 populations that prove it is the adopted 2021-11-30 map) · Tazewell (`ElectionGeography_public…/2` filtered to `County Board Member` and deduped to one polygon per district — the layer repeats a district once per member) · Iroquois (assessor AGOL org, `CountyBoardDistricts_REACH/8` — 4 districts × 4 members) · Adams (county AGOL org, `Web_Voting_Data/2` — 7 districts VERIFIED to tile the county before shipping: 99.997% of the TIGER outline covered, largest pairwise overlap 5e-7 deg², Quincy/Camp Point/Mendon each resolving to exactly one. Four small city districts inside Quincy plus three rural. **No roster** — the county's site is an Akamai hard deny with no Archive capture of its board page, so the card names the district and links the body and guesses no one: rule-4 branch 3, gap adams-county-board-roster) · Cass **derived** (`cass-county-board-districts.json` — Census 2020 voting districts dissolved per the county's own published district table by scripts/build_cass_board_districts.py; its GIS is a Beacon parcel viewer with no public REST. The fleet's first board whose districts are NOT all the same size: 11 members seated 3/3/3/2, so the build balances per MEMBER) · Washington **derived** (`washington-county-board-districts.json` — Census townships dissolved per the whole-township composition the county prints under each district heading by scripts/build_washington_board_districts.py; the county runs NO GIS of any kind, and no township is split, so every district edge is a township edge) · Marshall **derived** (`marshall-county-board-districts.json` — Census townships dissolved per the composition the county prints in the DISTRICT #n headings of its own board roster PDF by scripts/build_marshall_board_districts.py; the county runs no public GIS. Boundary and roster are the SAME TABLE in the SAME document, which is the fleet's tightest binding for the weekly composition drift check) · Mason **derived** (`mason-county-board-districts.json` — Census townships dissolved per the two composition lines the county prints under its roster by scripts/build_mason_board_districts.py; its only mapping surface is a WTH parcel viewer with no feature service) · Fulton (its own ArcGIS at gis.fultoncountyil.gov, `county_board_districts` — 3 districts of FIVE members, tiling 99.98% of the county. NOTE THE LAYER ID: each Fulton dataset is a single-layer hosted FeatureServer at a NON-ZERO id — board 50, precincts 43, polls 12 — so a probe of `/FeatureServer/0` errors on all three and would file this county as publishing nothing. Roster scraped weekly from the county's Members page, which publishes the board twice: a district-grouped photo grid, joined by name to hidden per-member popups carrying the e-mails. A fourth section headed "County Board Chairman" repeats a district member and is read as the Chair ROLE, never a sixteenth seat) · De Witt **derived** (`dewitt-county-board-districts.json` — the county's own precinct layer dissolved per the composition it prints for every board member by scripts/build_dewitt_board_districts.py; the county publishes only a raster JPG. LETTERED districts A-D, the fleet's first) · Stark **from a GOOGLE MY MAPS** (`stark-county-board-districts.json` — the county's entire GIS is one hand-maintained Google My Maps kept by the County Clerk, and the state's pointer file for Stark contains nothing but a link to it. It was unusable for a year on DATE alone, the pointer files predating the 2021 redistricting with no adopting resolution published anywhere reachable; County Clerk Heather Hollis settled it by e-mail on 2026-08-03 — “the board districts and precincts are correct”. 2 districts of FOUR members, the smallest board the layer carries; built by scripts/build_stark_districts.py and cross-checked against the map's own precinct folder, every precinct ≥ 99.99% inside its district) | Cook: live office join (same server); Will: `will-county-board-members.json` (weekly CI); DuPage: `dupage-county-board-members.json` (weekly CI; + countywide Chair); Lake: member + phone/email/office address/district page + newsletter on the boundary GIS itself (live, county-edited; re-verified vs the county directory 2026-07-23; the office-address and newsletter columns were fetched-but-never-requested dead code until 2026-08-01 — the pass-6 finding) + `lake-county-board-roles.json` (weekly CI — the Chair/Vice-Chair tags the GIS lacks, applied only on a name match so a missed reorganization degrades to role-less rows); Kane: member names on the boundary GIS (verified incl. the 2026 D2/D9 appointments) + `kane-county-board-members.json` (weekly CI from the county's SharePoint Board Members list API — party, official office phones, emails, profile links, and the countywide-elected Board Chair; GIS names stay as hover + fallback, cross-checked 24/24 against the roster); Kendall: `kendall-county-board-members.json` (10 members incl. the Chairman — a District 2 member, not a separate countywide seat — phones + emails + per-member profile links; 2026-07 enrichment check re-verified all 10 names 1:1 against the directory's 2026-03 Archive snapshot); McHenry: `mchenry-county-board-members.json` (18 members + the countywide-elected Chairman, phones + emails + per-member profile links; the DuPage countywide-chair shape; 2026-07 enrichment check re-verified all 19 names 1:1 against the directory's 2026-05 Archive snapshot — the county publishes no party or committee data, the one missing phone (D3) is confirmed unpublished at the source, and members' street addresses are residences, deliberately not collected). Both hand-verified 2026-07-23 against the counties' own directories: the counties block ALL automated fetch (direct, real-browser, and the Archive's crawler — SPN2 error:no-request), so the weekly engine-ladder scrapers run green and track the block on standing issues, resuming automation the moment any rung unblocks. LaSalle: `lasalle-county-board-members.json` (weekly CI from the county's own directory — 29/29 names, full 10-digit phones and district-office e-mails, plus the countywide-elected Chairman; the 2015-frozen officeholder columns on the superseded GIS are read nowhere). Kankakee and Winnebago are **rule-4 branch 1** — the member rides the county's own boundary GIS, so no scraper, no roster file and no weekly workflow: Kankakee 28/28 (name, party, phone, e-mail), Winnebago 20/20 (name, party, term year — its address/phone columns are declared and empty on every row, and the richer per-district contact on the county's board page is a backlog scraper, not a guess) . Pass 4's bridge counties: **McLean** 10 districts electing TWO members each, both seats + parties + profile links on the boundary GIS 10/10 (branch 1); **Sangamon** 29, GIS carries the district and a per-district MEMBER URL but no name, so a weekly scraper walks exactly those 29 URLs (29/29 names + parties, 27 e-mails, 22 phones); **Livingston** 3 multi-member districts, boundary AND roster both derived — townships per the county's published composition, members scraped weekly, with an explicit `vacancies` count because the directory lists a "Vacancy" seat that must be counted and never named; **Logan** 6 two-member districts — shipped at the rule-4 branch-3 floor (the county's only roster was a salary publication) until 2026-08-02, when the county's own board page began pairing all twelve members with their districts: a weekly scrape now joins them, 12/12 with phone + e-mail and the county's own Chair/Vice-Chair tags; **Madison** 26, the fleet's RICHEST board source — official/party/term/phone/e-mail/per-district page all on one feature (26/26 name, party, e-mail, URL; 25/26 phone); **St. Clair** 28, branch 1 at its thinnest — name 28/28 and nothing else. Winnebago, McLean, Madison and St. Clair were each spot-checked against their county's own board page before shipping. The northern/western counties (passes 5–5h): **DeKalb** 12 districts × 2 members, weekly roster scrape (party, contact, the Board Chair riding the matching member's row) since the GIS declares member columns and populates almost none; **Ogle** 24 (8 × 3), weekly scrape of the county staff directory (party, phone, e-mail, Chair + Vice Chair); **Stephenson** 8 districts, weekly scrape (a surname guard drops a predecessor's e-mail the county still publishes on one seat); **Carroll** 3 × 3, weekly scrape tolerant of the county's 'Distirct' typo and Roman numerals; **Lee** 4 × 5, weekly positional-parse of the roster PDF (party, e-mail 20/20, the Board Chair cross-checked in prose); **Whiteside** 3 × 9 = 27, branch 1 — members ride `ElectionGeography_public` (27/27 vs the county page; the org's 2019 `MyElectedRepresentatives` service is the stale twin, unused); **Rock Island** 19, weekly roster scrape (party, term, Chair/Vice-Chair); **Boone** 3 × 4, weekly scrape of the county's own board page (12/12 phone + e-mail + term-expiry year, rendered through the shared stale-year gate; role tags verbatim — one Vice-Chairman, no Chairman named anywhere on the page, so none is rendered); **Grundy** 3 × 6, weekly scrape of the county's own board page (18/18 party + since-year + committees verbatim, incl. per-committee Chair/Vice-Chair suffixes + phone + e-mail; the Board Chairman a district member, tagged from his own row); **Henry** 2 × 10 — the fleet's widest multi-member districts — weekly scrape of the county's own CivicPlus directory, which the county itself keys by district (20/20 e-mail, 15/20 phone; no chair marked anywhere, so none is tagged). The pass-7 tranche-1 pair: **Peoria** 18 × 1, weekly scrape whose SPINE is a GIS layer rather than a page — the county's `ElectoralDistricts/3` enumerates district → name, party and member-page URL, and each member page supplies the contact (18/18 party + e-mail, 12/18 phone), cross-checked against the County Board Members index (a third county surface) with a diminutive-tolerant name match; the Chairperson and Vice-Chairperson are badged on their own district rows because Peoria elects both from among the 18. **Tazewell** 3 districts seating 21 + a COUNTYWIDE-elected Chairman (the McHenry shape), weekly scrape of the county's own member pages (21 e-mails, 18 phones, 19 parties) — deliberately NOT the county GIS's member attributes, which are stale (they seat a member the county's own site no longer lists and omit one who has his own page). The scraper follows one stated rule — the website wins where the two surfaces disagree, the GIS fills only where the website is silent — which fills the Vice-Chairman's undistricted row from the GIS and PRESERVES the one district assignment the two still disagree about (the county's own site says D2, its GIS says D3), logging both rather than picking the tidier 7/7/7 arithmetic. **Stark** 2 × 4 = 8, weekly scrape of the county's Elected Officials page (8/8 e-mail + term year, Chair and Vice-Chair badged) — and the e-mails belong to the SEAT rather than the person (`boarddist1-1` … `boarddist2-4`), so contact survives turnover; the builder fails if a personal address ever appears in that slot | OR of cook/will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/winnebago/livingston/mclean/logan/sangamon/madison/st-clair/dekalb/ogle/stephenson/carroll/lee/whiteside/rock-island/woodford/boone/grundy/henry/peoria/tazewell/iroquois/dewitt/washington/cass/marshall/mason/stark/fulton county coverages. **Monroe, Randolph, Pike, Putnam, Brown, Calhoun and Schuyler are deliberately ABSENT**: all seven elect their boards COUNTYWIDE, so they have no district geometry to dispatch on and their members ride the COUNTY card instead (`il-county-commissioners.json`, 39 members) — the at-large board posture, per EXPANSION_GUIDE §1.5. Monroe and Randolph run the commission form (3 commissioners each); the tranche-5 four seat 9 / 5 / 7 / 5 and are the first counties in the fleet served with NO dispatch entry of any kind; pass-8 Schuyler (7) joins them. Every one of the seven was proven at-large from a certified election document rather than from a board page that omits districts |
| `ccbr` | Cook County Board of Review District | political | Bespoke | pre-built (PA 102-0012 shapefile) | `ccbr-roster.json` (weekly CI from cookcountyboardofreview.com) | cookCountyCoverage |
| `fire-district` | Fire Protection District | safety | CountyDispatch | Cook County GIS L17 (Clerk fire tax-agency tiling) · Will County ArcGIS · DuPage County ArcGIS (`Fire_Protection_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L4) · Kane County ArcGIS (`KaneCo_IL_Districts_Fire` L1, IDOR-coded districts only) · McHenry County ArcGIS (`Fire_Districts` L0, 19 after the loader excludes the 8 'Z NO FIRE DISTRICT' fillers, the municipal Crystal Lake city-fire row, and the overlapping Marengo rescue-squad district — a 70 ILCS 3105 ambulance body, not a fire protection district) · Kendall County ArcGIS Enterprise (`Fire_Protection_Districts` L0 — the parcel-derived tax-code tiling, 10 FPDs after excluding the municipal 'CITY OF JOLIET FIRE DISTRICT' rows; hairline no-result gaps at unparceled slivers) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/10`, 17) · Madison (`MadCo/FireDistrictsWS/0`, 42) · DeKalb AGOL (`PT_Fire_Districts/4`, 18 — Esri-JSON fetch) · Lee (`leecogis`, 22 NG911 service areas) · Rock Island (`rock-island-fire-districts.json`, 17 — pre-built from the county TaxDistricts tiling with parcel-fabric road voids closed at 75 ft, build_rock_island_tax_districts.py) · Sangamon AGOL (`FireDistrictEtc` L2 — 226 fragments grouped per district at load into 29 FPDs + `SPRINGFIELD CORP`, the city's corporate area, whose card states it is served by the city's own Fire Department rather than an FPD) · St. Clair (`CentralSquare/DATA/8`, the county's CAD folder — 44 named departments; disttype/agency declared and 0/44 populated, so the taxing-vs-dispatch caveat rides every card) · Stephenson **georeferenced** (`stephenson-fire-districts.json` — the county's 2014 vector-PDF fire map measured by scripts/build_stephenson_fire_districts.py, hydrography-fitted; 15 named services, 2014-vintage caveat on every card) · Peoria (county open-data org, `Fire_Protection_Districts/0`, 13) · Iroquois (assessor AGOL org, `FireDistricts_REACH/5`, 46) · Boone (`Fire_Districts/0`, 5 — NUMBERED, not named) · Stark **from the County Clerk's Google My Maps** (`stark-fire-districts.json`, 6) · Macon (its AGOL org's `Fire` layer, 17) | Cook: name-only; Will: trustees in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: chief + office contact in GIS attrs; McHenry + Kendall + Kankakee + DeKalb + Lee + Rock Island: name-only; Madison: dept head + address + phone + URL in GIS attrs (the fleet's first contact-bearing fire entry); Sangamon + St. Clair + Stephenson: name-only; **Peoria: name + the district's OWN WEBSITE** — the first fire tiling in the fleet whose source publishes a link, so the card's footer links the district that answers the call rather than the county (populated on some rows and null on others; no officer or address column exists — recorded as `peoria-fire-park-library-contact`) ; **Iroquois: name + the county's own DISCREPANCY note** — its source carries a column recording where the county's two sources disagree ("Parcel Data shows this in Milford Fire District, but map shows Cissna Park"), populated on 20 of 46, and the card surfaces that text rather than a false certainty; **Boone: NUMBER only, and the card says so** — the layer carries a lone `district` column, and the numbering was confirmed as the county's real identifier by County Clerk Amy Ohlsen, who supplied names and then volunteered that she had “just done a google search to get these names” while “when we complete tax extensions, it is just 1-5”, so the names are not used and the numbers are (gap boone-fire-names, narrowed rather than closed); **Stark: name + AMBULANCE** — the only fire entry in the fleet whose source names who responds with an ambulance, and it is not always the fire department (3 districts Stark County Ambulance, Bradford by Bradford Rescue Squad, Kewanee Rural and Neponset their own) | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/lee/rock-island/sangamon/st-clair/stephenson/peoria/iroquois/boone/stark/macon county coverages |
| `dupage-county-special-police` | DuPage Special Police District | safety | Polygon | DuPage County ArcGIS (`Special_Police_Districts_`, "Real Estate Tax Code polygons") | link-only (elected DuPage County Sheriff; unincorporated-area police-tax district) | dupageCountyCoverage |
| `park-district` | Park District | geography | CountyDispatch | Cook County GIS L23 (Clerk park tax-agency tiling, incl. the Chicago Park District) · Will County ArcGIS · DuPage County ArcGIS (`Park_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L11) · Kane County ArcGIS (`KaneCo_IL_Districts_Park` L1) · Kendall County ArcGIS Enterprise (`Park_Districts` L0 tax-code tiling, 5 genuine districts — Fox Valley/Joliet/Oswegoland/Plainfield/Sandwich) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/5`, 4) · Madison (6) · DeKalb AGOL (`PT_Park_Districts/9`, 6 — Esri-JSON fetch) · Rock Island (`rock-island-park-districts.json`, 1 — Cordova, pre-built with road voids closed) · Peoria (county open-data org, `Park_Districts/0`, 4) · Macon (its AGOL org's `ParkJoin_Dissolve` layer, 6) · Stark **from the County Clerk's Google My Maps** (`stark-park-districts.json`, 2 — LaFayette and Bradford, together ~9% of the county) — McHenry: recorded gap, publishes facilities not district boundaries | Cook: name-only; Will: commissioners in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only; Peoria: name + the district's own website (footer link); **Stark: name only, deliberately** — that folder of the county's map carries a `Fire Department` column left over from whoever built it by copying the fire layer, and it is confidently wrong rather than blank (“LaFayette Park District” claims a fire department), so the builder never carries it forward and nothing reads it — the Freeport/Peoria-REPNAME posture ; **Macon: name only, space-stripped as published** (see the library row) | OR of cook/will/dupage/lake/kane/kendall/kankakee/madison/dekalb/rock-island/peoria/stark/macon county coverages |
| `library-district` | Library District | geography | CountyDispatch | Cook County GIS L20 (Library Tax District) + L19 (Library Fund) · Will County ArcGIS (`Library_District`) · DuPage County ArcGIS (`Library_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L8) · Kane County ArcGIS (`KaneCo_IL_Districts_Library` L1) · McHenry County ArcGIS (`Library_Districts` L0, 13 after the loader excludes 6 'Z_None' fillers + the lone municipal Crystal Lake city row) · Kendall County ArcGIS Enterprise (`Library_Districts` L0 tax-code tiling, 9 bodies incl. the municipal Joliet/Yorkville city-library funds — Kendall's tiling records EVERY library taxing body, the Cook-style complete shape, so its municipal rows stay) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/3`, 8) · Madison (18) · DeKalb AGOL (`PT_Library_Districts/7`, 13 — Esri-JSON fetch) · Rock Island (`rock-island-library-districts.json`, 9 named districts — pre-built with road voids closed at 75 ft; the blank-named tenth source row, a stray byte-identical copy of the UNITED TWP HIGH 30 school polygon and not an un-districted remainder, is asserted and excluded at build time; the 60 ft snap still answers perimeter roads and refuses between-district seams) · Peoria (county open-data org, `Library_Districts/0`, 10) · Macon (its AGOL org's `LibraryJoin_Dissolved` layer, 10) · Stark **from the County Clerk's Google My Maps** (`stark-library-districts.json`, 6 — two of them, Kewanee and Williamsfield, seated in a NEIGHBOURING county and reaching across the line, which is why the county drew them) | Cook: agency name + a Type row distinguishing district vs municipal fund; Will: trustees in GIS attrs (sparse); DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; McHenry + Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only; Peoria: name + the district's own website (footer link); Stark: name-only; **Macon: name only, and the names ship EXACTLY as the county writes them** — its labels are space-stripped (`MtZion`, `HopeWelty`, `IlliopNian`, `MarrowBone`), and re-inserting the spaces mechanically would produce “Marrow Bone” and “Illiop Nian”, which are not those districts' names. Recorded as macon-district-name-formatting rather than guessed | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/rock-island/peoria/stark/macon county coverages |
| `school-board` | Elected School Board District | political | Bespoke | pre-built (ERSB SB15 shapefile) | `school-board-members.json` (hand-curated) | chicagoCoverage |
| `cps-hs-network` | CPS Network (High School) | schools | CpsNetwork | Socrata `aupu-jt2g` | chief in dataset props | chicagoCoverage |
| `cps-network` | CPS Network (K-8) | schools | CpsNetwork | Socrata `pnta-kuqa` | chief in dataset props | chicagoCoverage |
| `ward-precinct` | Ward Precinct | political | Bespoke | Socrata `i8fv-xe4b` | — | chicagoCoverage (subOf `ward`) |
| `ward` | City Ward | political | CountyDispatch | Chicago Socrata `p293-wvbd` (50) · suburban Cook GIS `politicalBoundary` L22 (21 municipalities) · Evanston city ArcGIS · Will County ArcGIS `Ward_Districts` (Lockport/Wilmington/Crest Hill/Joliet) · Aurora city ArcGIS · WinGIS `ElectedOfficials` L20 (Rockford, 14) · Rock Island County org (`MolineWards2020`, `SilvisWards`) · DeKalb County org (`DeKalb_Wards` 7 across 8 polygons, `Sycamore_Wards` 4, `Genoa_Wards` 4, `Sandwich_Wards` 4) · Mendota city org (`Mendota_Wards`, 4) · Berwyn city org (`City_Wards…Berwyn_WFL1` L1, 8) · Waukegan city org (2025 `WARDS_LOCATOR` L2, 9 — alderman + per-seat phone/e-mail on the polygon) · North Chicago city org (`2026_Ward_Boundaries`, 7) · Boone county GIS (`Belvidere_Wards`, 5 — both aldermen + phones) · St. Charles city org (`St_Charles_Ward_Boundary` L1, 5 — both aldermen w/ contact) · Geneva city org (`Wards_view`, 5 — both aldermen w/ contact) · Batavia city server (`External/WARDS_20`, 7 — both aldermen's names) · West Chicago city org (`2025_WC_WardBoundaries`, 7 wards/16 polygons — both aldermen + ward page URL) · McHenry city org (`Wards(Monte)`, 7 wards/13 polygons) · Kendall Enterprise (`Hosted/Wards` filtered to Yorkville 4 + Plano 4; its Aurora/Joliet sliver rows dropped) · Pontiac city org (`Wards`, 5 wards/6 polygons) · McLean clerk GIS (`Clerks/MyElectedRepresentatives` L0 parsed by its own 'City of X Ward N' names — Bloomington 9, Le Roy 4, Lexington 3; the stale REPNAME column read nowhere) · Lincoln city org (`Lincoln_Wards_View_Only`, 4 — current GIS names as roster fallback) · SPI org (`Springfield_Wards_2022` **L4**, 10) · Freeport city org (`Wards2022_Public`, 7 — its stale Alderperson column read nowhere) · East Moline city org (infrastructure service L23, 7 — alderman + contact; rides the rock-island entry) · St. Clair county (`SCC_voting_districts` L13 Belleville 8 — duplicate-id sliver dropped by largest-ring-per-id — + L14 O'Fallon 7) | Chicago: live Socrata `htai-wnw4` join; every suburban entry: the seat's holder(s) from `municipal-officials.json` matched on the ward number, falling back to officeholder attribute(s) on the boundary where they exist (Evanston, Rockford, Waukegan, Belvidere, St. Charles, Geneva, Batavia, West Chicago, Lincoln, East Moline — several publish BOTH aldermen per ward, and both are rendered) | chicagoCoverage OR `municipal-ward-coverage.json` tagged by entry (56 municipalities across 21 non-Chicago entries) |
| `police-beat` | Police Beat | safety | Bespoke | CPD ArcGIS | — | chicagoCoverage (subOf `police-district`) |
| `police-district` | Police District | safety | Bespoke | CPD ArcGIS | `cpd-district-info.json` (weekly CI, Playwright) | chicagoCoverage |
| `ccpsa-district-council` | CCPSA District Council | safety | Bespoke | shares `police-district` geometry | `ccpsa-district-councils.json` (weekly CI) | chicagoCoverage |
| `mwrd` | Water Reclamation District (MWRD) | geography | Polygon | Cook County GIS (`politicalBoundary` L21 — the Clerk's tax-agency boundary, 1 district) | none elected per sub-area (nine commissioners at large) — card links mwrd.org's board page | cookCountyCoverage (in-county fringe outside the district honestly reports "No result") |
| `tif-district` | TIF District | geography | Polygon | Cook County GIS (`clerkTaxDistricts` L18 — the Clerk's un-yeared CURRENT tiling, 418; retired year editions archive in the `Tax_Increment_Finance_District_Boundaries` service) | no elected body (TIFs are municipal ordinance districts) — card shows the Clerk agency number + links the Clerk's TIF-reports page | cookCountyCoverage (most points are in no TIF) |
| `community-area` | Community Area | geography | Polygon | Socrata `igwz-8jzy` | — | chicagoCoverage |
| `zip-code` | ZIP Code | geography | Polygon | live TIGERweb ZCTA | — | — |
| `cps-high` | CPS High School Zone | schools | SchoolZone | Socrata `xg7c-d8rm` (year-versioned) | zoned-school POI | chicagoCoverage |
| `cps-middle` | CPS Middle School Zone | schools | SchoolZone | Socrata `fyff-53xy` (year-versioned) | zoned-school POI | chicagoCoverage |
| `county-precinct` | Voting Precinct | geography | CountyDispatch | Cook County GIS (`precinctHistorical` L0, the Clerk's current suburban fabric, 1,430 — same geometry as Socrata `k7sw-w3b8`) · Will County ArcGIS `Precincts_2022` · DuPage County ArcGIS `Precincts_2024` (current 600-precinct map) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L7, 431) · Kane County ArcGIS (`KaneCo_IL_ElectionsPrecincts` L1, 292 — township named from the clerk's own Maps-page prefix pairing, election-day polling joined 292/292 from `KaneCo_IL_Elections_PollingPlaces` and labelled with its Election field, 2026-08-02) · McHenry County ArcGIS (`Precincts` L0, 223) · Kendall County ArcGIS Enterprise (`Voting_Precincts_and_Polling_Places` L1 `status='A'`, 78 — township names derived at load from the county's own townships layer, the assigned polling place joined by GlobalID from L0) · LaSalle self-hosted (`PollingPlaceLocator/1`, 119 + polling points joined 119/119 on `USER_Precinct`) · Kankakee `k3gis.net` (`BASE/Elected_Officials/0`, 59, name-only) · Boone (37, polling place carried ON the feature) · Grundy (40, polling joined 38/40 on `POLLINGID`) · Macoupin Socrata (`ab79-cnsh`, 45 — the current 2022-2032 fabric, refreshed upstream 2025-11; polling joined 45/45 from the clerk's own Socrata polling dataset (`rc5v-ajnf`) by deterministic label expansion, 2026-08-02) · Madison (191, `pollingid` GlobalID join 191/191) · St. Clair (`SCC_voting_districts`, 150 — polling is a recorded gap) · Winnebago WinGIS (`WardsAndDistricts/7`, 94, county-clerk jurisdiction only — Rockford runs its own election commission) · DeKalb AGOL (`Precincts/1`, 69) · Ogle **from the county GIS Coordinator's own shapefile** (`ogle-precincts.json`, 51 — the county publishes none, so this was supplied by e-mail 2026-08-03 and is archived under `data/source/raw/`; township on the feature, board district by SPATIAL join because the 2021 resolution names bare townships where the shapefile numbers them; no polling place, its polling dataset being points with no precinct key) · Lee (46) · Whiteside (60 — polling joined 56/60 from the county's own layer, and the remaining four filled from `whiteside-precinct-polling.json`, two locations the County Clerk supplied — name and street address — because the county's published list omits their facility ids; consulted only where the county's own layer has no match, and the card says where the location came from, so all 60 now show a polling place and an address) · Rock Island (120) · McLean (`Clerks/PollingPlaces` L1, 141 — polling joined 141/141 by POLLINGID from L0) · Logan (TCRPC `Logan_County_Districts_and_Zoning/40`, 29 township-named — the clerk's HTML polling table ships as `logan-precinct-polling.json`, joined 29/29) · Sangamon AGOL (`ApprovedPrecincts20231012`, 166 — polling joined 165/166 by POLLID from `ElectionPollingAndPrecincts` L0) · Carroll (TIGERweb Census-2020 VTDs live, 22 — the county did not re-precinct; the clerk's polling notice ships as `carroll-precinct-polling.json`, joined 22/22) · Woodford (TCRPC election service, 37 — polling joined 37/37 on the numeric polling reference, the precinct's own name cross-checked in the polling row's grouped label) · Peoria (county open-data org, `2020_Voting_Precincts/0`, 116 — polling joined on POLLINGID against its 55 published locations, many-to-one by design) · Tazewell (`ElectionGeography_public…/1`, 82 — polling joined on facilityid 76/82; six precincts reference three facility ids the county's own Voting Locations layer does not publish, recorded as `tazewell-precinct-polling`) · Iroquois (`ElectionGeography_public/1`, 37 — polling joined on pollingid against 32 sites) · Adams (`Adams_County_Voting_Precincts_view/0`, 92 — the fleet's least-joined precinct card: the county's own feature carries the polling place (92/92) AND the precinct's board district, so neither is a spatial join nor a name match. Quincy's ward rides the same feature, trimmed and shown only where it is non-blank) · Monroe (`VoterPrecinct/0`, 25 — polling joined 25/25 by expanding the polling layer's comma-separated precinct list, every token a bare integer; NO board-district row, the county elects at large) · Randolph (`VotingPrecincts/1`, 35 — identity only: pollingid is declared and null on all 35, and the county elects at large, so this is the fleet's thinnest precinct card and says only what the county publishes) · De Witt (Sidwell/Magnasoft org, `ElectionPrecincts_DeWittIL/0`, 23 — the same fabric its board districts are dissolved from, so the board-district row comes from the derived boundary; no polling published) · Fulton (`voting_precincts` layer 43, 44 — each precinct carries its own polling place NAME, ADDRESS and TOWN on the feature, 44/44, so neither is a join and the county's separate polls layer is never fetched; the Adams and McDonough shape) · Stark **from the County Clerk's Google My Maps** (`stark-precincts.json`, 9 — the county's eight congressional-survey townships with Toulon split east/west, which is why they are drawn as near-rectangles and why that is correct rather than approximate; no polling published)  · Macon (its AGOL org's `ElectionGeography_public` layer 1, **64** named precincts with the polling place joined 64/64 on facilityid against 29 voting locations — the county's `fulladdr` already ends in the municipality on all 29, so the loader trims the trailing CRLF the service returns and does not append the city twice. NO county-board row: Macon's five board shapes carry no district number at all, see `macon-county-board-labels`) · Stephenson **georeferenced from the County Clerk's own two adopted maps** (`stephenson-precincts.json`, 36 = 20 rural + Freeport 01-16). The app recorded for a year that the county published no current precinct boundaries; it does, as vector PDFs on the Clerk's own Elections page, and Clerk Jazmin Wingert pointed at them on 2026-08-03 in reply to a records request. scripts/build_stephenson_precincts.py measures them and proves the transcription twice before writing: the 36 printed populations total 44,630, the county's live Census 2020 count to the person, and the Freeport sixteen are the SAME polygons the board-district map draws, read off a different document and georeferenced independently — 16/16 land in the district the board build assigns, at IoU 0.996 or better. That cross-check earned its keep immediately: it failed on the first run, and the culprit was this build filling holes the PDF's declared EVEN-ODD fill rule says are holes, not the shipped board file. Township on the feature, board district by SPATIAL join; no polling place — the Clerk's page links a countywide polling list whose link is dead at the source. PRECINCT LINES ARE NOT TOWNSHIP LINES here: the rural precincts reach into Freeport township and take 329 people with them, which the populations and the geometry agree on | County Board district via spatial join (Cook: Commissioner District; Kane: carried on the features); Kendall also shows the county's own polling-place assignment; each card links its county clerk | suburban-Cook (in Cook AND NOT Chicago — city precincts are the BOE's `ward-precinct` layer) OR will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/boone/grundy/macoupin/madison/st-clair/dekalb/lee/whiteside/rock-island/mclean/logan/sangamon/carroll/woodford county coverages, plus peoria/tazewell/iroquois/monroe/randolph/dewitt/stark/ogle/fulton/stephenson/macon, plus Winnebago-outside-Rockford (subOf `township`) |
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

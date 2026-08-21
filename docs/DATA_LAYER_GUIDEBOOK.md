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
5. **The per-fork inventory below now has a PUBLIC twin, and a layer needs a row in
   both.** Chicago's `sources.html` renders one provenance row per registered layer —
   what it answers, the publisher its boundary comes from, where the names on its card
   come from, the ground it answers on — generated from `metro-worksheet.json`'s
   `layers[].source`. The two are deliberately not the same document: this inventory is
   for whoever maintains the fleet (factory pattern, coverage function names, per-county
   entry counts), the page is for a reader deciding whether to trust an answer. But a
   layer that ships without a `source` block now fails `generate_metro_files.py`
   outright, and a page missing a row fails `validate_index.py` — so "add the layer,
   write the row" is enforced on the public side and remains a review rule here.

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
      "summary": "Adams County publishes its 7 board districts as map data, but its website refuses every automated visit, so the card can show which district you are in without naming the 21 people who represent it. Only the board chair is nameable, from a state source.",
      "blocker": "Checked 2 Aug 2026, when the county's districts and precincts were added, and RE-MEASURED IN DEPTH 2026-08-20. THE BLOCK IS A FLAT WAF DENY AND NOT THE COLES CASE, which had to be established rather than assumed: adamscountyil.gov and quincyil.gov both answer 403 Access Denied (370-418 bytes, the length varying only because the denied path is echoed into the body) with server AkamaiGHost and Akamai's own edgesuite error reference. The TLS chain is COMPLETE on both \u2014 leaf plus Let's Encrypt intermediate plus root, openssl verify return code 0 \u2014 so the missing-intermediate story that turned out to be Coles's whole blocker does not apply here and no AIA fetch would change anything. The deny is invariant across browser UA, this project's own bot UA, no UA at all, HTTP/1.1, plain http, and the apex domain, and it is not this sandbox's address: a fetch from a different network on a different client was refused the same way. Both sites are Granicus GovAccess behind Akamai, which is why county and city fail identically. One nuance the earlier record lacked: /favicon.ico returns 200 from the Granicus origin while /robots.txt, /sitemap.xml, every made-up extension and a real document path all deny \u2014 a single-path allowance, not a content channel. THE VENDOR ROUTE IS CLOSED, PROVEN RATHER THAN UNTRIED: il-adams.pollresults.net returns a 7,720-byte NotFound shell whose md5 is IDENTICAL to that of a made-up county name and to il-cook's, il-adams.accessliberty.com/pastelections.aspx is a 404 against Clark's working 57,700 bytes, and the vendor's own county list names fourteen counties without Adams among them. So the canvass route cannot name a single Adams seat from any election date. TWO STATE SOURCES DO ANSWER, neither of them read anywhere in this repo. (1) ISBE's county-board table (elections.il.gov ComplianceRecord.htm) gives Adams as 21 SEATS ACROSS 7 MULTI-MEMBER DISTRICTS, 3 PER DISTRICT, no cumulative voting \u2014 and its Clark and Brown rows independently match counties this project verified by other means, which is the check that makes it trustworthy; its embedded metadata is from 2007 and it carries no revision date, so it is cited for STRUCTURE and not as a currency claim. (2) ISBE's County Officers Book (coofficers.pdf, 107 text-layer pages, stamped last updated 15 Dec 2025) names the board CHAIR in all 102 counties: Adams's is Kent Snider (R), ksnider@adamscountyil.gov, 507 Vermont Street, 217-257-6830. THAT NAME IS NOT SHIPPED AND SHOULD NOT BE: the book's chair column was parsed and cross-checked on 2026-08-20 and names a different chair than the county does in 16 of the 56 counties where a comparison is possible, wrong in all ten checked live, so it is read nowhere (the Coles rule). It names no other board member anywhere \u2014 \"County Board Member\" and \"District\" occur zero times in the whole document \u2014 so it can badge a chair and can never supply 21 members by district. WHAT MAKES THIS WORTH KEEPING WARM: the county's own precinct service already carries CountyBoard on 92 of 92 precincts and Ward on 57, so the day a precinct-level canvass is obtained, both the board roster and Quincy's council key straight onto the shipped geometry with no spatial join and no name matching. The missing ingredient is only the returns.",
      "wanted": "The 21 members by district from any source that permits automated reading \u2014 the county's page becoming reachable, or the Clerk sending precinct-level certified returns, which would key straight onto the precinct layer's existing CountyBoard column. The board's shape (7 districts x 3) and its chair are no longer the missing part."
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
      "concept": "Municipal council contact",
      "area": "Aurora (Kane, DuPage, Kendall and Will counties)",
      "counties": [
        "kane",
        "will",
        "dupage",
        "kendall"
      ],
      "kind": "blocked",
      "layer": "municipality",
      "summary": "Aurora's 12 council members show with the right wards but still no phone or e-mail \u2014 the city's site was open for a month and refuses automated visits again.",
      "blocker": "Re-checked 31 Jul 2026, when the old blocker had genuinely lifted: Aurora had moved to www.aurora.il.us, the new site answered, and all 12 aldermen's pages published a city e-mail address and the Alderman's Office phone. The ward boundary data carries no officeholder details, so contact has to come from those 12 pages, and reading them was queued rather than done. RE-MEASURED 2026-08-20: THE WINDOW CLOSED FIRST. www.aurora.il.us now answers 403 Access Denied to every path tried \u2014 the root, /government, /government/city-council, /residents and /directory.aspx, 374 to 405 bytes each \u2014 and the refusal is AKAMAI's: the body carries Akamai's own error reference and errors.edgesuite.net, and the response carries the ak_p server-timing header. That is the Joliet class, a flat WAF deny rather than a challenge a browser works through, so this stopped being queued work and became a sourcing block. CHECKED WHO ANSWERED, because this project's own rule is that a 403 from an egress proxy is not a 403 from a site: the proxy reported the tunnel established and the denial is the origin's. THE READER IS UNAFFECTED AND THAT DISTINCTION IS THE POINT \u2014 the card's link (aurora-il.org, which 301s to www.aurora.il.us) opens normally in a real browser; what is refused is the automated read, so this is a sourcing block and not a broken link, and the link gate is right to treat a roster-carried 403 as ordinary. A DECOY TO NAME BEFORE IT COSTS SOMEONE THE BUILD: cityofaurora.org redirects to aurorane.gov, the City of Aurora NEBRASKA \u2014 the browncountyil.org / Clay-County-Missouri class of wrong-state hit, and the obvious thing to type for Illinois's second-largest city.",
      "wanted": "The 12 aldermen's phone and e-mail in any form that permits automated reading \u2014 the city's site answering automated clients again, or a council directory from one of the four county clerks Aurora spans. The ward assignments are already correct and shipped; only contact is missing."
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
      "summary": "Three county directories turn away the computer that checks them each week \u2014 two by flat refusal, DeKalb now behind a captcha \u2014 so their board member lists are checked by hand or on a delay. The names on the cards are current either way.",
      "blocker": "Re-checked 31 Jul 2026: McHenry's and Kendall's directories refuse every request from a server. What had improved is that the Internet Archive then held complete 2026 captures of both board directories (McHenry 20 May, Kendall 13 Mar), making an Archive-based refresh newly possible for the board lists; McHenry's municipal yearbook page had no capture newer than 6 Mar 2025 and Kendall's municipal list had never been archived at all. That Archive finding is left at its own date on purpose \u2014 this environment's egress policy blocks archive.org, so this pass could not re-test it and does not restate it as current. RE-MEASURED 2026-08-20, and the three have diverged. Kendall and McHenry are unchanged but now precisely attributed: both answer HTTP 403 \"Access Denied\" (415 and 485 bytes) from AkamaiGHost, carrying Akamai's own edgesuite error reference \u2014 the Joliet class of flat WAF deny, not a puzzle a browser solves. DEKALB HAS HARDENED RATHER THAN STAYED THE MILDEST: where it used to turn away some of the weekly check's machines and not others, dekalbcounty.org now answers HTTP 202 with a 220-byte body whose whole content is a meta-refresh to /.well-known/sgcaptcha/ keyed to the caller's IP \u2014 the SiteGround captcha front, the same one that hides Crete's village site. The 202 is the sharp edge here: it is not an error status, so a reachability check that keys on 400-and-above reads a captcha as a healthy source while every scraper behind it fails, which is why this project now counts 202 as unreachable. DeKalb's list was last confirmed current 2 Aug 2026, by hand.",
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
      "summary": "Bond names all five board members by district, but publishes no district boundaries \u2014 and its certified returns now prove no published geometry can draw them, because four of its twenty precincts are split between districts.",
      "blocker": "Researched 8 Aug 2026, closing an absence that had NO record at all: Bond is served as a judicial-circuit secondary, its board did not surface, and nothing said why. FORM SETTLED \u2014 DISTRICTED: bondcountyil.gov/bond-county-board/ lists Board Districts 1-5 with one member each and a county e-mail apiece (Chris Timmerman 1, Bernard Myers 2, Jacob Rayl 3, Wesley L. Pourchot 4, Jeff Rehkemper 5) \u2014 re-verified unchanged 2026-08-20, 5 of 5. GEOMETRY IS ABSENT, measured not assumed: the county's ArcGIS Online org (bondcountygis.maps.arcgis.com, service root services.arcgis.com/VbP0KHITyLTMBTy3) was re-enumerated 2026-08-20 and still carries exactly 24 feature services \u2014 parcels in five vintages, townships, zoning, municipal boundaries, floodplain, cemeteries, K12 school boundaries, FPD_Boundaries \u2014 with NO board-district layer and NO precinct layer, and its public viewer's nine layers carry nothing electoral. A DECOY TO NAME BEFORE IT COSTS SOMEONE THE BUILD, re-verified the same day: searching ArcGIS Online for \"Bond districts\" returns a service owned by Tamara.Freihat_DuPage and actually named \"Bonds\" \u2014 municipal BOND (debt-financing) districts in DuPage County. THE CANVASS ROUTE WAS THEN RUN IN FULL ON 2026-08-20, AND BOND FAILS IT TWICE OVER, either failure fatal alone. Both vendor hosts answer (il-bond.pollresults.net, il-bond.accessliberty.com), the archive runs 2006 to Apr 2025, and every district is witnessed twice \u2014 all five contests in the 2022 General canvass, districts 2 and 4 again in 2024, and 1, 3 and 5 in the final 2026 primary feed. A THIRD DOWNLOAD-HANDLER ID PAIR, worth recording beside Clark's 58/188 and Edgar's 59/189: Bond's is pageid=52&mid=220, so the per-county keying is a rule rather than a coincidence, and each of the six PDFs fetched was verified to start %PDF and read \"Statement of Votes Cast \u2026 BOND COUNTY\" rather than being the vendor's login page. (1) BOND SPLITS PRECINCTS. Four of twenty appear in two districts' contests apiece \u2014 BURGESS 2 across districts 1 and 3, CENTRAL 6 across 4 and 5, OLD RIPLEY across 3 and 4, SHOAL CREEK 2 across 2 and 3 \u2014 and this is not a parse artifact: in all four cases the two portions sum to the county's own whole-precinct registration exactly (474, 466, 655, 175), the five district totals sum to the county's 10,725, and the 2024 canvass and 2026 feed reproduce the same cuts. Three are slivers (9 of 474, 10 of 655, 34 of 175) and Central 6 is a real 262/204 cut. check_partition refuses in exactly these words, and the consequence is bigger than this route: a district here is not a union of whole precincts, so publishing precinct geometry later would STILL not draw these lines. This is the Bureau/Piatt/Douglas shape. (2) BOND FAILS THE JASPER TEST INDEPENDENTLY: 25 census VTDs against the county's 20 current precincts \u2014 LaGrange 1+2 consolidated to LaGrange, Tamalco 1+2 to Tamalco, Shoal Creek 3 and 4 absorbed, CENTRAL 5 retired outright \u2014 proven from the county's own documents, since the 2020 canvass lists the census 25 and every canvass from the June 2022 primary onward lists the current 20, as does the Clerk's own polling-locations PDF. THE TRAP INSIDE THAT TEST, worth naming: the population half PASSES (VTD POP100 sums to 16,725, the county's exact Census 2020 count), so a builder checking only the sum would have sailed straight past a fabric that had moved. NO WRITTEN COMPOSITION IS PUBLISHED EITHER: the site's own search returns zero results for redistricting and for precinct, and all 26 minutes and 15 agendas from the 2021 redistricting year are image scans with a zero-length text layer, so machine search of them is impossible by construction. NOT YET ASKED.",
      "wanted": "The 2021 board reapportionment ordinance with its map or legal description \u2014 or, failing that, the census-block or metes-and-bounds description of how BURGESS 2, CENTRAL 6, OLD RIPLEY and SHOAL CREEK 2 divide between their two districts. That is now the whole ask, and it is a small one: the certified canvasses already establish which WHOLE precincts sit in each district, so nobody needs to be asked for a precinct list, and asking for one would be asking the Clerk to redo work her own returns already publish. Any GIS file of the five districts, even an internal one, closes it outright. Address the election authority (Bond County Clerk & Recorder) \u2014 but confirm the name first: the county site and the results vendor name different people, and this record deliberately names neither as current. One correction for whoever builds the roster: the board page spells District 1 \"Chris Timmerman\", while his own county e-mail address and every certified canvass spell it TIMMERMANN."
    },
    {
      "id": "boone-fire-belvidere-city",
      "concept": "Fire protection district coverage",
      "area": "City of Belvidere (Boone County)",
      "counties": [
        "boone"
      ],
      "kind": "data-quality",
      "layer": "fire-district",
      "summary": "Inside the City of Belvidere the fire card names Fire District 2, but the city levies no fire protection district at all \u2014 it runs its own municipal fire department.",
      "blocker": "Found 2026-08-20 while re-measuring Boone's fire-district names, and confirmed directly against the live service: a point at Belvidere City Hall returns district 2 from the county's Fire_Districts layer, which carries exactly five polygons that tile the whole county with no gap over the city. The county's own tax roll says that is not where the city sits. Of the 55 tax codes in the Clerk's district-rates report, 18 carry NO fire-protection district line at all \u2014 they are the City of Belvidere codes \u2014 and a sample of 150 parcels drawn from those 18 codes falls inside fire polygon 2, 150 of 150. The county yearbook says the same thing from the other side, naming a Belvidere Fire Chief under the city's own officers: the city is served by a MUNICIPAL fire department, which is a department of the city and not a separate taxing district a resident lives inside. So the card is not merely missing a name here, it asserts a membership that the county's own levy contradicts, and it does so for the largest population in the county. This is the tiling assumption failing rather than the data being stale: a five-polygon layer that covers every acre implies every acre is in a fire protection district, and in Illinois a municipality with its own department is exactly the case where that is false. Worth checking for the same shape wherever a county fire tiling is shipped.",
      "wanted": "Confirmation from the county of which territory each fire polygon actually covers \u2014 specifically whether the City of Belvidere should be a hole in the tiling rather than part of polygon 2. Short of that, the honest fix is ours to make: suppress or relabel the fire card inside the city's limits, which the app already knows from the municipality layer."
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
      "summary": "Boone's five fire districts show by number. The county DOES publish their names \u2014 in the Clerk's tax-extension reports, not its GIS \u2014 but two measured mismatches have to be handled before a name can honestly go on the card.",
      "blocker": "Shipped 3 Aug 2026 by number, on the reasoning that names assembled from a Google search are not a county record: asked for them, County Clerk Amy Ohlsen supplied names and then volunteered that she had \"just done a google search to get these names\" and that \"when we complete tax extensions, it is just 1-5.\" THE REASONING WAS RIGHT AND THE FACTUAL PREMISE WAS WRONG, found 2026-08-20. The names ARE county-published, in the very document the Clerk was describing: her own District Rate Listing and Tax Extension Worksheet, linked from the Clerk's tax-reports page, print FD01 - CAPRON FPD, FD02 - BOONE COUNTY FPD2, FD03 - NORTH BOONE FPD, FD04 - LEROY FPD, FD05 - MANCHESTER FPD and FDCV - CHERRY VALLEY FIRE \u2014 the same six lines byte-identical in the reports for tax years 2020, 2022, 2023, 2024 and 2025, so this is a standing series and not a one-off. The GIS side of the record is unchanged and re-verified: the Fire_Districts layer carries exactly five fields with a smallint `district` and no name column, its renderer is simple with no class labels, and the web maps consuming it declare no popup at all. THE FD0n-TO-POLYGON MAPPING WAS PROVEN RATHER THAN ASSUMED, twice over from county-published sources: taking each FD code's tax codes from the Clerk's own by-taxcode report and testing those parcels against the polygons lands 100%/100%/98%/100%/98% in districts 1-5 respectively, and independently the political-township geography agrees (district 1 is Boone Township, which contains Capron; 4 is LeRoy; 5 is Manchester) as do the fire-board addresses the county yearbook prints under DISTRICT NO. 1 through 5. TWO MISMATCHES STOP A NAIVE SHIP, and they are the reason this record stays open rather than closing. (1) THERE IS A SIXTH TAXING DISTRICT THE LAYER DOES NOT CARRY: FDCV - CHERRY VALLEY FIRE has a real Boone rate (0.77048) and a real extension in the Clerk's TY2025 worksheet, but Fire_Districts has five polygons that tile the whole county, so {1,2,3,4,5} and {FD01-FD05, FDCV} are not the same set and a name assigned by position could be assigned to the wrong body. (2) See the separate boone-fire-belvidere-city record: the layer's polygon 2 covers the City of Belvidere, which levies no fire protection district at all, so naming polygon 2 would put a district's name on residents who are not in it.",
      "wanted": "A county statement tying each of the five POLYGONS to a named district \u2014 the Clerk's tax reports already name six districts and the mapping to polygons 1-5 is now measured, so what is missing is confirmation of the two mismatches: where Cherry Valley Fire's Boone territory sits, and whether the City of Belvidere should be excluded from the tiling."
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
      "blocker": "Re-checked 31 Jul 2026 across the county's mapping server (56 datasets) and its online map catalogue (360 items): no park or library district boundaries anywhere, and every item labelled \"park\" turns out to be a conservation-district facility map. The districts do exist on paper \u2014 the clerk's yearbook prints the Belvidere Park District commissioners and the Ida Public Library board with contact details. RE-MEASURED WIDER 2026-08-20 and the finding holds: the county's ArcGIS server was enumerated in full (12 folders, 99 services, 279 layers, 240 distinct layer names) and the ArcGIS Online org queried across ALL owners rather than one (510 items against the 360 the earlier check saw) \u2014 LIBRARY matches across all 510: zero. The 63 park matches are every one a conservation-district or foundation FACILITY layer, individual properties with park_name and acres columns, not a district boundary. THE DISTRICTS THEMSELVES WERE CHECKED THIS TIME, which the earlier pass did not do. The Belvidere Park District does publish a boundary map \u2014 a 34x22-inch, purely vector PDF of nearly 59,000 line elements \u2014 but it is an assessor's plat sheet with the district edge drawn on it, carrying no title block, no legend, no coordinate grid and no georeferencing of any kind, so it is usable only by hand-digitising and is not a publisher-supplied boundary. The Ida Public Library publishes nothing: its own sitemap's 33 pages contain no boundary, service-area map or district page, and the one service-area mention is a sentence on the library-card page with no map behind it. Its site served a transient verification interstitial on one fetch and real content on the others, so this is \"not published\", not \"unreachable\". A DERIVABLE ROUTE EXISTS AND IS WORTH RECORDING even though it is not a published boundary, because this repo already ships the pattern for Rock Island: the county's parcel layer carries a tax_code column across 24,320 parcels, and the Clerk's district-rates-by-taxcode report maps each code to its constituent districts \u2014 PDBV (Belvidere Park District) appears in 20 tax codes covering 11,861 parcels and LYBV (Ida Library) in 16 covering 8,167, so dissolving parcels by those sets yields a footprint from two county-published sources. The catch a builder must reconcile first: the parcel layer's tax-code domain and the Clerk's report are different vintages and disagree on about a dozen codes in each direction.",
      "wanted": "Park and library district boundaries from the county as map data. Failing that, a reconciled tax-code vintage would make the parcel-dissolve route honest \u2014 or the Belvidere Park District's plat map republished with georeferencing. The yearbook's trustee lists are ready to go alongside whichever arrives."
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
      "summary": "Brown County's 14 voting precincts are not shown \u2014 but the boundaries are now one yes/no question away, not missing: the census fabric matches the county's precincts except for one pair of renamed precincts nobody outside the Clerk's office can disambiguate.",
      "blocker": "Checked 2 Aug 2026 when the county was added: Brown publishes no precinct boundaries, no county items appear in any public map catalogue, and its election summaries are scanned images \u2014 the record concluded that even the precinct NAMES could not be lifted automatically. THAT PREMISE IS FALSE AS OF 2026-08-20, and the correction matters more than the original finding. The county's own site (browncoil.org \u2014 browncountyil.org remains a SiteGround-captcha decoy, re-verified) is WordPress and serves its Election Information page through the REST API as plain text, polling place by polling place. And the Illinois State Board of Elections publishes precinct-level results as CSV for every election authority in the state, carrying a PrecinctName column \u2014 Brown's 14 current precincts read straight out of it. The scans are still scans (zero extractable characters across 42 pages) and the county still publishes no precinct map, but the NAMES were never the obstacle they were recorded as. THE CENSUS FABRIC FITS: 14 Census 2020 voting districts against 14 current precincts, and the VTD populations sum to 6,244, the county's own Census 2020 count, exactly. Twelve of the fourteen match by name once the county's own spelling drift is allowed for \u2014 it prints BUCKHORN TWP in 2020, BUCKHORN TOWNSHIP in 2022, plain BUCKHORN in 2024 and BUCKHORN TOWNSHIP again in 2026 with no boundary changing, and the November 2024 list matches the census names 14 of 14 with no aliasing at all. THE WHOLE REMAINING QUESTION IS TWO PRECINCTS. Between November 2024 and April 2025 the county renamed precincts 0005 and 0012 from MISSOURI and RIPLEY to MISSOURI-RIPLEY TOWNSHIP 1 and MISSOURI-RIPLEY TOWNSHIP 2, and by name alone either could be either. The evidence leans hard toward a rename rather than a redraw: the two precinct NUMBERS were preserved, and 5 and 12 are the alphabetical slots Missouri and Ripley already held; registration moved +2 and 0 across the change while sibling precincts moved by as much as 23; the two kept separate polling places, the second inside Ripley village; Missouri and Ripley are still separate townships today, and each census VTD is exactly its township at an intersection-over-union of 1.000000. But the county's own grammar reads the other way \u2014 VERSAILLES TOWNSHIP 1/2 really is one township split in two \u2014 so \"Missouri-Ripley 1 and 2\" parses just as naturally as one combined area divided afresh, and this project does not ship a boundary on the better-looking reading of an ambiguity.",
      "wanted": "One yes/no answer from the County Clerk: when precincts 0005 and 0012 were renamed to Missouri-Ripley Township 1 and 2, was that only a change of name \u2014 0005 still Missouri Township and 0012 still Ripley Township \u2014 or was the line between them redrawn? Every other piece is in hand and verified: with that answered, the dissolve passes the tiling and containment gates as they stand."
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
      "blocker": "ASKED 1 Aug 2026 and ANSWERED 10 Aug: Clerk Matthew Eggers sent three PDFs — the county-wide map and the Princeton and Spring Valley insets — with \"this is what I have\", and said he had asked the Assessor's GIS deputy whether she has something different. Measured rather than eyeballed, they split two ways. THE COUNTY-WIDE MAP IS STILL NOT USABLE, for a reason worse than resolution: it is one 3300x2550 JPEG with zero text and zero vector content, it is stamped \"10/27/2021 — PROPOSED REAPPORTIONMENT MAP\" rather than the plan the board adopted 23-0 on 9 Nov 2021, and NO DISTRICT BOUNDARY IS DRAWN ON IT AT ALL — the heavy black lines are township lines, and a district is a per-PARCEL colour fill with white unfilled parcels scattered through every one of them, so dissolving the colours would leave holes with no rule to close them. That parcel-level colouring is also why the Assessor's office is the right place to have asked. THE TWO CITY INSETS ARE REAL VECTOR PDFs, 1,981 and 1,004 drawing paths and 1,892 and 1,746 characters — the first machine-readable geometry Bureau has produced, and they cover exactly the street-by-street city splits that were the previous blocker. They do not cover the rural districts, so on their own they build nothing. AND THE SHAPEFILES EXIST, 11 Aug: pressed on the two cheaper routes, Eggers replied that the county-wide map is not digital in his office and named the Assessor's GIS deputy, Christine Anderson — who answered the same morning that she HAS shapefiles of the board districts. Two conditions came with that: the requester must be able to open a shapefile, and she reads this as a COMMERCIAL request, which it is not. Asked her directly 11 Aug, correcting the category rather than letting it stand: chidistricts.com is free, carries no advertising, sells nothing and redistributes no data file, the county is credited on its own card, and a formal FOIA on whatever form the office prefers is offered instead if that is cleaner. The precinct boundaries were asked for in the same message. ANSWERED 12 Aug, and the answer is a CONDITION, not the file: Anderson sent a user agreement to sign and a $150 invoice 'per our data fee schedule' — the campaign's first fee demand, a class no other county has raised. Neither document has been read (they sit as e-mail attachments outside the pipeline's reach), and NOTHING has been signed, paid, or replied: signing a license and spending money are the operator's decisions, not an agent's. The deciding fact is the agreement's terms — chidistricts ships derived boundary JSON publicly, so redistribution/derivative restrictions would put Bureau in the licensed-not-open class (the Champaign/Piatt precedent: WITHDRAWN rather than take on obligations), making the $150 moot; permissive terms would make this a cheap, clean buy. The free routes named on 10 Aug — a precinct list or block-assignment table, plain public records — remain unanswered and unaffected by the fee schedule. READ 13 Aug (the operator relayed both PDFs to Drive): the invoice is a flat $150 ('GIS Project Fee & prep charge', payable on receipt) — honest cost recovery, not the obstacle. The agreement is, and by its own words: the PROTECTION OF PROPRIETARY RIGHTS clause forbids 'reproduction or redistribution of digital datasets OR PRODUCTS DERIVED THEREFROM outside of licensee's organization', and a shipped bureau-county-board-districts.json is a derived product served publicly to every visitor's browser — so signing as written is off the table at any price. The Champaign/Piatt class, CONFIRMED BY READING rather than assumed. Two things keep the door open. First, the clause's own tail — 'without permission from Bureau County GIS' — is a valve: the obligations the agreement otherwise imposes (source credit, modifications described) are ones this fleet already practices on every card, so permission scoped to the site's actual use would make the buy clean. A reply is DRAFTED for the operator asking exactly that, with the no-license fallback (the composition list — the DeWitt/Shelby route) in the same message. Second, nothing about the county's posture reads as refusal: a form agreement built for parcel-data buyers, applied to the first civic reuser who asked. Nothing signed, nothing paid; the decision and the send are the operator's. Re-checked 31 Jul 2026: the county runs no mapping system. ITS BOARD PAGE IS NOT WRONG — the 16-of-18 listing was reported to the Clerk as a website omission and he corrected it: districts 9 and 15 are VACANT and the county is filling them, so a roster built from that page should carry 16 members and say why, not wait for two names that do not exist.  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR BUREAU THE ANSWER IS NO, AND THIS CLOSES THE LAST ROUTE. Its certified 2026 General Primary carries ten of the eighteen district contests, and SIXTEEN precincts appear in more than one district's contest apiece — Princeton 2 in districts 6 and 7, Hall 1 in 10 and 11, and so on through Hall, La Moille, Princeton and Walnut. Bureau SPLITS precincts between districts, so no dissolve of whole precincts can draw its map, exactly as Jasper's Wade Township blocks Jasper. The census fabric itself is fine (50 VTDs, 50 county precincts, names matching, populations summing to the county's exact 33,244) — it is the PLAN that cuts through them. This county now needs the boundary itself and nothing else will do.",
      "wanted": "Two things, in Jefferson's order of preference. FIRST, the assignment list rather than new geometry: a block equivalency / block assignment file, or the parcels-to-district table behind the colouring, or a plain list of which precincts make up each district — any of which draws the districts exactly against public geometry with no drafting by the county. SECOND, confirmation of which map is the ADOPTED plan, since the file in hand is stamped PROPOSED and dated 10/27/2021 while the board adopted on 9 Nov. The Princeton and Spring Valley vector insets are already in hand and check out; the county-wide extent is the whole of what is missing. AS OF 11 AUG THE ASK IS NARROWER THAN EITHER: the Assessor's GIS deputy has the board districts AS A SHAPEFILE, so what is wanted is that file (.shp/.dbf/.shx/.prj) and, if it exists, the voting precincts alongside it — nothing to draw, nothing to derive, and the request is with her. (13 Aug: the file arrived priced at $150 behind a license whose standard terms forbid redistribution of derivatives — so what is wanted is now the clause's own valve: written permission for the site's specific use, or failing that the composition list, which needs no license at all.)"
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
      "summary": "Carroll's fire and park districts have no boundary published anywhere \u2014 the county SELLS its GIS rather than publishing it. Its seven library districts are a different story: a statewide layer carries them.",
      "blocker": "Checked 31 Jul 2026: the county runs no mapping system, its GIS page links a parcel-search portal with no usable data behind it, and the clerk's 2025 tax report names nine fire districts, three park districts and seven library tax lines with rates only. RE-MEASURED 2026-08-20 AND THE FIRST CLAUSE IS WRONG IN A WAY THAT CHANGES THE ASK. Carroll DOES run a mapping operation: an ArcGIS Online organisation (83 public items, 26 hosted services \u2014 all of it highway capital-improvement machinery, no parcel, fire, park, library, precinct or tax-code layer among them) AND a staffed GIS department with a named director, a published fee schedule and a 2017 cost study that says in its own words that the department maintains boundary layers including FIRE districts and that it SELLS digital data. So the blocker is not absence, it is the JO DAVIESS POSTURE \u2014 the data exists inside a county that treats it as a product, and the assessor portal the earlier note called empty is a paywalled search rather than a hollow one. The tax report is unchanged (2025 is still newest, posted May 2026), but the same page carries a Tax Code by District Listing that the earlier pass missed: it gives every district's exact tax-code composition, confirms the 9 fire / 3 park / 7 library counts precisely, and pins the two cross-line fire districts to one Carroll tax code each (Hanover 09001, Polo 02002). FIRE AND PARK ARE NOW MEASURED SHUT RATHER THAN UNSEARCHED, and the neighbouring-county idea was tested and failed on its merits: Stephenson publishes a fire-district map but it is CLIPPED AT THE COUNTY LINE \u2014 Shannon village sits provably outside Stephenson's own Shannon Fire polygon \u2014 Whiteside's 227-item GIS carries zero fire layers, Ogle exposes one public service unrelated to fire, Jo Daviess exposes no REST directory at all, and no statewide Illinois fire or park district layer exists. THE LIBRARY HALF IS BUILDABLE TODAY, from a statewide layer this project had not found: the Illinois Broadband Office / Connected Nation IL_Boundary_Layers service carries 642 Library Districts polygons for the whole state, and over Carroll it returns exactly the clerk's seven tax lines name for name \u2014 Savanna, Mount Carroll, Chadwick, Milledgeville, York Township, Lanark and Pearl City. It is right on the negatives too, which is the check that matters: Shannon village and Lake Carroll land in NO library district, and the clerk's own tax codes agree that Shannon's code carries no library line. Its extents are true rather than county-clipped, so Pearl City's Carroll-side reach is present \u2014 the thing this record asked for. THE PROVENANCE CAVEAT IS REAL AND MUST RIDE ANY BUILD: the publisher is a broadband contractor, not the county and not the districts; the layer is undocumented in its own item description; copyrightText is empty; and every attribute besides the name is a broadband service metric, which means these are library SERVICE AREAS compiled for broadband planning. That is a real published boundary with a weak provenance line, and a card would have to say whose boundary it is.",
      "wanted": "Fire and park district boundaries as map data \u2014 which for Carroll means a price and a licence rather than a search, since the county sells what it maintains, so the question to put to its GIS director is whether a free civic reuse is possible and on what terms (the Jo Daviess precedent says ask). The library half needs no publisher: it needs a decision on whether a broadband contractor's compiled service areas are provenance enough to name on a card."
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
      "summary": "All three Carroll cities elect aldermen by ward. Savanna publishes its wards \u2014 as a 1977-code text description and a scanned map \u2014 while the only digital copy is withheld inside the city's own map account, and Lanark's site now refuses automated visits.",
      "blocker": "Savanna (4 wards, 2 seats each), Mount Carroll (3 wards, 2 seats each) and Lanark (3 wards) were confirmed ward-electing from city sources on 31 Jul 2026. RE-MEASURED 2026-08-20, and three things changed. FIRST, THE HEADLINE CLAIM THAT NONE PUBLISHES WARD BOUNDARIES IS FALSE FOR SAVANNA: its council page links an \"Election Wards\" PDF carrying City Code chapter 1-17 in full \u2014 a street-centerline legal description of all four wards, the composable kind this project already builds from elsewhere \u2014 plus a hand-coloured ward map and a separate precinct map confirming the city's 6 precincts are not its 4 wards. What it is not is CURRENT: the description ends \"(1977 Code)\" and every page is a pure raster scan with no text layer and no georeference, so it answers \"does anyone publish?\" without answering \"post-2020-census?\". SECOND, THE PRIVATE THING IS NOT WHAT THE RECORD SAID: the city's map account still holds exactly one ward item among 102, but the WEB MAP is public and anonymously readable \u2014 it is the feature collection it points at that is withheld, and that was proved rather than inferred, since ArcGIS answers a withheld item with a 403 permissions error and a non-existent one with a 400, and a fabricated control id returns the 400. So the polygons exist inside the city's account and are being kept back; whether the public shell was already visible in July cannot be established here, because the platform exposes no sharing history and archive.org is blocked by this environment. THIRD, LANARK MOVED FROM SILENT TO UNREACHABLE: lanarkil.gov now answers HTTP 202 behind a SiteGround captcha, and 202 counts as unreachable here, so \"Lanark publishes no ward map\" is no longer a measurement anyone can make from outside. Mount Carroll is unchanged and genuinely publishes nothing \u2014 its council page names all six aldermen by ward and its site carries no ward map or ordinance. All three cities' codes live on American Legal, which refuses this client with a Cloudflare challenge: published, unreadable from here, which is a different fact from unpublished. No current post-2020 ward layer for any of the three exists anywhere public \u2014 searched across the city org, the whole ArcGIS catalogue and ArcGIS Hub.",
      "wanted": "Current post-2020-census ward boundaries for any of the three. For Savanna the cheapest unlock is unchanged and now precisely located: the city sharing the feature collection behind its own public web map, or confirming whether the 1977 code description it already publishes is still the operative one \u2014 if it is, the text alone builds the wards. Mount Carroll and Lanark still need a first publication."
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
      "blocker": "Checked 2 Aug 2026. This block is legal, not technical. Both counties' maps are run by the Champaign County GIS Consortium, which sells this data: buying it requires a signed licence, and the consortium's terms let you view the maps but not copy them, display them publicly, or put them on another server. Showing them here would do all three. The maps are easy to fetch, and that is exactly what makes this worth spelling out — easy is not the same as allowed. CONFIRMED BY THE COUNTY CLERK, 3 Aug 2026. A records request to Champaign County's election authority for the board-district and precinct boundaries was answered by the Clerk's elections division: \"The shape files for the requested data are maintained by the Champaign County GIS Consortium. You will need to reach out to them.\" So the county's own election authority says it does not hold the files — this blocker is now a named source rather than an inference from the consortium's terms, and the remaining ask is to the consortium, not to the clerk. The Piatt half was ALSO asked directly (3 Aug 2026, board+precinct GIS to Clerk Harper — pending), and the consortium permission letter is drafted in pass 14.  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR PIATT THIS WOULD HAVE BEEN THE WAY AROUND THE LICENCE, and it is not: Piatt's census fabric passes cleanly (16 VTDs, 16 county precincts, populations summing to its exact 16,673), but its certified results put MONTICELLO 1-4 and WILLOW BRANCH in more than one district's contest apiece — the county seat is split five ways across three districts. So the returns route cannot draw Piatt either, and the licence is no longer the only obstacle there. Champaign was not measured this pass; its own results are not on this vendor.",
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
      "blocker": "Checked 2 Aug 2026: “County-Board-Districts-2022.pdf” has no readable text or lines at all, and the state's copy of the adopted plan is a scan. The trap is the file next to it: “County-Board-Districts-with-Rep.pdf” IS readable, but the populations printed on it are from the 2010 census, so it is the pre-2021 map and using it would draw superseded lines. The county has an online map account but publishes only assessment data on it. The member list is missing too — the county site names the Chairman and Vice-Chairman only, not the 16 members or their districts. ENCLOSED 2026-08-11: Shelby's join made Christian the coverage wash's second enclave after Bureau — Sangamon, Macon, Shelby and Montgomery are all served, so this county now reads as a doughnut on the map rather than as frontier, which makes its absence the visible kind.  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR CHRISTIAN THE FORM IS NOW SETTLED AND THE FABRIC IS NOT. The certified 2026 General Primary carries all four districts, each 'Vote for 2' (an eight-member board), and their precinct lists partition the county's 29 precincts exactly once each with NO split — so the composition is in hand. What fails is the Jasper test: the census carries THIRTY Christian voting districts to the county's 29, with PANA 5 and SOUTHFORK 3 in the census that the county no longer runs and TAYLORVILLE 9 in the county that the census does not carry. The county re-precincted after 2020, so census geometry cannot be dissolved as-is. Worth one more look: if the changed precincts sit wholly inside single districts the districts may still be recoverable, which is a measurement nobody has made. THE MEASUREMENT THIS RECORD ASKED FOR IS NOW MADE (2026-08-20), and it narrows the county to ONE QUESTION. The record's own closing line — 'if the changed precincts sit wholly inside single districts the districts may still be recoverable, which is a measurement nobody has made' — was the right test, and it comes back three ways. PANA RESOLVES: all four of the county's Pana precincts sit in District 4, so census PANA 5 can only be District 4. SOUTH FORK RESOLVES: both of the county's South Fork precincts sit in District 2, so census SOUTH FORK 3 can only be District 2. TAYLORVILLE DOES NOT: the county's Taylorville precincts are SPLIT, #4, #5 and #9 in District 2 against #1, #2, #3, #6, #7 and #8 in District 3 — and TAYLORVILLE #9 is precisely the county precinct the census does not carry. So the whole county turns on where #9 was carved from. If it came out of #4 or #5, both already District 2, no district line moves and Christian is buildable today; if it came out of a District 3 Taylorville, a census voting district straddles the D2/D3 line and no dissolve of whole census units can express the plan. THREE SIGNALS FAVOUR THE FIRST AND NONE IS PROOF, which is why nothing is built. (1) Under that reading the four districts run 8,210 to 8,918 against an 8,508 ideal — 4.8% worst deviation, the tightest this project has measured anywhere, and the shape of a real adopted plan. (2) Census TAYLORVILLE 4 (1,859) and 5 (2,037) are the two largest Taylorville units by a wide margin, the rest running 1,122-1,394; splitting the largest precinct is the ordinary reason a county adds one, and both of the largest are in District 2. (3) The county's own registration counts discriminate against the alternative: were #9 carved from District 3, District 3 would hold about 21.9% of the county's population while carrying 26.96% of its registered voters, a ratio roughly 23% above District 2's, which nothing supports — under the first reading the two sit within half a point of each other. THE COMPOSITION ITSELF IS COMPLETE AND UNSPLIT: the Clerk's live results feed at il-christian.pollresults.net names all four district contests, each 'Vote for 2' (consistent with a 16-member board seating four per district on staggered terms), and their precinct lists partition the county's 29 precincts exactly once with nothing overlapping. ALSO MEASURED, so a later pass does not repeat it: the county's canvass archive at il-christian.accessliberty.com LISTS 60 PDFs back to 2006 but its download handler returns 404 for the pageid/mid pair its own page advertises (56/186), so those canvasses — which could date the Taylorville change outright — are listed but not fetchable from here. AND THE COUNTY PUBLISHES VECTOR PRECINCT MAPS THIS RECORD NEVER NOTED (2026-08-20). The record dismissed both board-district PDFs correctly — the 2022 one carries no readable text or lines, the readable one is the pre-2021 plan — but the same Elections page also publishes PER-TOWNSHIP precinct and ward maps: Taylorville-Precincts.pdf, South-Fork-Precincts.pdf and Pana-Precincts-4.pdf. Taylorville's is a REAL VECTOR DRAWING, not a scan: 2,094 curves and 1,164 line objects with a live text layer that labels the precincts individually, 'Precinct 1' through 'Pcnt 9'. That is the same class of artifact White County was built from on 2026-08-17, and it is aimed squarely at this record's one remaining question — a traced Taylorville precinct 9, intersected against the census Taylorville voting districts, would say which one it was carved from without anybody replying to an e-mail. Reaching that page needed the .GOV: the Clerk's e-mail domain is christiancountyil.COM and it links across to christiancountyil.GOV, the Edgar trap in another form. A FOURTH SIGNAL WAS TESTED AND IS RECORDED WITH THE REASON IT DOES NOT SETTLE ANYTHING (2026-08-20). The county's polling-place list names a site for every precinct, so the cheap proxy was to geocode Taylorville #9's — the Taylorville Township Building, 1620 W Spresser Street — and ask which census voting district contains it. It falls inside census TAYLORVILLE 4, a District 2 unit, which is exactly what the reading favoured above predicts. THE SAME RUN'S CONTROL REFUTES THE METHOD, which is why this is written down as a caution rather than banked as evidence: Christian pairs precincts at shared buildings, and two of those pairs STRADDLE the district line. County Taylorville #3 (District 3) and #4 (District 2) share the VFW Hall, which geocodes into census TAYLORVILLE 4; #5 (District 2) and #6 (District 3) share Davis Memorial Christian Church. So in this county a polling place demonstrably serves precincts that do not contain it, and #9's location cannot establish which precinct it was carved from. It also exposes an assumption underneath all of this worth stating plainly: every reading here maps county Taylorville #N onto census TAYLORVILLE N by name, and a county that re-precincted Taylorville may have renumbered it too. The one-sentence question to the Clerk, or a trace of the county's own vector precinct map, remain the only routes that would actually settle it. THE TRACE ROUTE WAS ASSESSED RATHER THAN ATTEMPTED (2026-08-20), so the next pass starts from facts instead of optimism. Taylorville-Precincts.pdf is one 792x612pt page carrying 2,094 curves, 1,164 lines and 417 word objects. WHAT IT HAS: real vector linework, and the county's rural survey grid labelled along the edges (1150 N through 1800 N, with matching E roads), which is a genuine georeferencing basis because those are regularly spaced section-line roads at known mileages. WHAT IT LACKS: any scale bar, coordinate tick, datum or projection statement — nothing in the file states where it sits on the earth. AND ITS LABELS ARE FRAGMENTED: a clean word extraction finds only seven of the nine precinct labels (1, 2, 3, 4, 5, 7 and 8); 'Pcnt 9' and 'Pcnt 6' appear in the raw character stream but split across text runs, so even reading which polygon is precinct 9 takes character-level work before any georeferencing begins. A trace is therefore POSSIBLE and is NOT a small job: it needs the grid roads geocoded to fit an affine transform, the precinct labels reassembled from character runs, the polygons traced from the curve set, and the result sanity-checked against the census units it is meant to be compared with. The failure mode is a wrong district line, which is the worst output this pipeline produces, so it should be done deliberately or not at all — and the Clerk's one-sentence answer would make the whole exercise unnecessary. ASKED 2026-08-21: that one-sentence question went to County Clerk Kandi Badman at elections@christiancountyil.com — \"One question about Taylorville #9 — Christian County board districts\", following up the 5 Aug inquiry. This line is written the day the mail actually left, never the day a draft was written (the Scott rule). No reply yet; nobody should re-ask this county until one arrives or the follow-up interval has genuinely passed.",
      "wanted": "ONE SENTENCE WOULD DO IT, and that is new as of 2026-08-20: which precinct was TAYLORVILLE #9 created out of? If it was split from Taylorville #4 or #5, this county can be drawn today from its own certified returns with nothing further from anybody. Everything else is already in hand — the four districts' composition, complete and unsplit, from the Clerk's own results feed, and Pana and South Fork both resolved. Failing that one answer: the four districts adopted in 2021 as map data, or a member list with district assignments, either of which the county's own map account could carry."
    },
    {
      "id": "clark-board-contact",
      "concept": "County board members",
      "area": "Clark County",
      "counties": [
        "clark"
      ],
      "kind": "data-quality",
      "layer": "county-board",
      "summary": "Clark board cards name the member, their party and the election that seated them, and give the county switchboard rather than a direct line — the county publishes per-member contact only inside a scan.",
      "blocker": "Measured 18 Aug 2026 when the county was built. The county's only board document is \"2022 - 2024 County Board List\", linked from clarkcountyil.org/board, and it is a SCANNED IMAGE with no text layer \u2014 no scraper can ever read it, and nothing else the county publishes names a board member at all. It does print a phone and an e-mail for each of the seven, and they were read by eye; six resolve cleanly and the seventh does not, rendering as \"J m.bolin@bolininc.com\", with a space no address can contain. Shipping six read-by-eye personal addresses and guessing the seventh is what the honesty rules forbid, and a mistyped personal address sends a constituent's mail to a stranger \u2014 so none ship, and the county's own switchboard stands for the board (the Calhoun rule). The same scan prints every member's HOME ADDRESS, which never ships under any sourcing (the Madison/Peoria rule). NOT YET ASKED \u2014 DRAFTED: the reply to County Clerk & Recorder Laura H. Lee that thanks her for settling the board's form asks for the board's current contact list in any typed form, and for who chairs the board (the returns cannot show a chairmanship, so no chair is badged). It is drafted for the operator to send; this record gets its ASKED date when it goes, never before (the Scott rule). THE CHAIR HALF OF THIS ASK LOOKED ANSWERABLE ON 2026-08-20 AND IS NOT, which is worth recording so it is not re-tried: ISBE publishes a County Officers Book (elections.il.gov, coofficers.pdf, 107 text-layer pages, stamped last updated 15 Dec 2025) naming a board chair in all 102 counties, and Clark's is given as Rex Goble (R) \u2014 who IS one of the seven this card already names from the certified canvasses, so here the state and the county agree. But the pipeline built to read that book measured its chair column against every roster this app ships and found it names a DIFFERENT chair in 16 of the 56 comparable counties, wrong in all ten checked live \u2014 so it is read nowhere (the Coles rule; see the guidebook's ISBE County Officers Book entry). Clark's row agreeing is not evidence the column is sound, it is one of the 40 that happen to. The chairmanship still needs the Clerk, or an election the returns can show. The CONTACT half is untouched by this \u2014 ISBE names no board member but the chair anywhere in the file (\"County Board Member\" occurs zero times in 107 pages), so the seven phone numbers and e-mail addresses still exist only inside the county's scan.",
      "wanted": "The seven members' county-published phone numbers and e-mail addresses in any text form, and the Chairman's name \u2014 ISBE's County Officers Book names him and agrees with this card's roster, but that book's chair column is measured 16-of-56 wrong and is read nowhere, so it does not answer this. Short of that, the switchboard plus the certified election on each row is as far as this card can honestly go."
    },
    {
      "id": "clark-precinct-polling",
      "concept": "Polling places",
      "area": "Clark County",
      "counties": [
        "clark"
      ],
      "kind": "data-quality",
      "layer": "county-precinct",
      "summary": "Clark's precinct cards name the precinct and its board district and stop there — the county's only polling-place list is eight years old.",
      "blocker": "Measured 18 Aug 2026 when the county was built. The county's Precinct Maps page states \"Clark County has 23 precincts, but only 15 polling places\" and links a list that names a building and address for all 23 — a text-layer PDF, so it would join cleanly. Its title is \"Polling places and addresses 11-18\": the November 2018 election. Nothing on the page or in the file dates it any later, the four precinct maps beside it are dated 2014, and the county's election-results vendor publishes returns but no polling locations. Sending a voter to an eight-year-old address is precisely the harm these rules exist to prevent, so nothing ships rather than shipping it labelled. NOT YET ASKED — DRAFTED on the Clerk's own thread, alongside the contact ask, and dated here only when it is sent (the Scott rule).",
      "wanted": "Clark County's CURRENT polling places paired with the 23 precinct names, in any text form. The 2018 list already proves the shape joins; it only needs to be current."
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
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The one ArcGIS Online result for the name — an ElectionDistricts service owned by voteclaycountymo.gov, carrying a 'MO Central Committee' layer — is Clay County MISSOURI, rejected by owner and layer names exactly as pass 11 rejected Mercer County New Jersey: check what a hit IS before recording it. No Illinois county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR CLAY THE FORM IS SETTLED AND THE ROUTE IS OPEN. Its certified 2026 General Primary carries seven single-member district contests LETTERED rather than numbered — B, C, D, G, I, K and N — over 10 of the county's 18 precincts, with no precinct in two districts. The lettering implies a board of about fourteen, of which only these seven were up. The census fabric passes on count and population (18 VTDs, 18 precincts, exactly 13,288) with a NAMING wobble that is a normalisation rather than a mismatch: the census spells its sub-precincts in ROMAN numerals where the county uses arabic (HARTER I vs Harter 1, CLAY CITY I vs Clay City). THE OTHER HALF IS NO LONGER MISSING, AND FINDING IT CLOSED THE ROUTE RATHER THAN OPENING IT (2026-08-20). The county publishes its ENTIRE district composition in plain HTML on its own County Board page, under a heading called Districts — no canvass needed, older or otherwise: A = Clay City I; B = Clay City II & Stanford; C = Xenia & Songer; D = Blair & Bible Grove; E = Oskaloosa & Larkinsburg; F = Hoosier & Pixley; G = Louisville I; H = Louisville II; I = Harter I; J = Harter V; K = Harter IV; L = Harter III; M = Harter VI; N = Harter VII. Fourteen districts, which confirms what the lettering implied. THE SAME PAGE ANSWERS THE ROSTER AND THE CHAIR: thirteen members are named with their district letter and a phone (A Terry Woodrow, B Rod Franklin, D Janice Brooks, E Troy Britton, F Tara Bangert, G Mary Cisne, H Terry Hronec, I Kelly Colclasure, J Jeremy Kohn, K David Johnson, L Cory Hodges, M Barb Mcgrew, N Troy Leonard), with Board Chairman Joe Goodman and Vice Chairman Barbara McGrew stated separately. DISTRICT C IS THE ONE LETTER THE MEMBER LIST OMITS, and no source here says why — Goodman holds no listed letter, so it is tempting to read him into C, and that is exactly the inference the honesty rules forbid. It is recorded as unexplained. NOW THE ARITHMETIC, WHICH IS WHY NOTHING SHIPS. Those fourteen districts name NINETEEN precinct-slots. The county has EIGHTEEN precincts, and that is not this project's count — two independent sources agree: Census 2020 carries 18 Clay voting districts summing to the county's exact 13,288, and ISBE's certified precinct-level returns for the 2026 General Primary list 18 precinct names for the CLAY authority. Both carry exactly ONE Clay City. The board page is the only source anywhere that names two, splitting 'Clay City I' into District A and 'Clay City II' into District B. So one precinct is divided between two board districts, and the districts are NOT unions of whole precincts — the Bond/Douglas/Ford/Cumberland shape. Whether the page preserves pre-merge names or describes a line drawn through a single precinct, the present-day effect is identical and it is fatal to the precinct route: nothing published says where inside Clay City the A/B boundary runs. MEASURED SHUT for board geometry. TWO SUFFIX DIFFERENCES ARE NOT PART OF THIS and should not be mistaken for it: the census writes LARKINSBURG I and PIXLEY I where the county and ISBE write LARKINSBURG and PIXLEY, with no II anywhere in any source — a vestigial suffix, matching 16 of the 19 slots cleanly. AND THE COUNTY'S OWN CANVASSES CANNOT HELP, checked rather than assumed: its Official Results PDFs for March 2026, November 2024 and March 2024 are all SCANNED IMAGES — 10, 3 and 10 pages at zero extractable characters. The earlier note that Clay's vendor archive is empty stands; what replaces it is ISBE's statewide CSV, which is where the 18 precinct names above come from. CORRECTED 2026-08-20 — THE 'NO WEBSITE' FINDING ABOVE IS FALSE, and it was false the day it was written. The pass-13 probe permuted the county's NAME across five domain patterns; the county's actual domain was already in this repo, in data/app/il-county-clerks.json, as the host of its Clerk's own e-mail address. That is the identical systematic failure Johnson's record diagnosed on 2026-08-09 and it was never swept across the other counties. Probing every frontier county's clerk-e-mail domain instead reaches a live site in EIGHTEEN of the thirty-one, several of them at hostnames no name permutation would produce (piatt.gov, bureaucounty-il.gov, hancockcounty-il.gov, champaigncountyclerkil.gov). For Clay the site is https://claycounty.illinois.gov/ (183 KB), and its own homepage links Board Members, County Board and a GIS Property Search. What that means for THIS record is narrow and should not be overstated: the county's board form and roster were already settled from its certified returns, and the open item — where the District A/B line runs inside the split Clay City precinct — is a sub-precinct boundary that a board page will not answer. The site is a new place to look for it, not an answer.",
      "wanted": "Nothing on the form and nothing on the roster — the county publishes both, and they are read above. ONE THING ONLY: where the District A / District B boundary runs INSIDE the Clay City precinct, since the county splits it and no other source does. A district shapefile would answer it; so would a written description of the A/B line, or confirmation that Clay City is in fact two precincts today and that the census and ISBE are both behind. Absent that, thirteen of fourteen districts are derivable and the county still cannot be drawn."
    },
    {
      "id": "clinton-precinct-geometry",
      "concept": "Voting Precinct",
      "area": "Clinton County",
      "counties": [
        "clinton"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Clinton's board districts ship but its precincts do not \u2014 five of the county's Brookside precincts became three and nothing says which.",
      "blocker": "Measured 2026-08-20, while the board districts were being built. Census 2020 carries 39 Clinton voting districts; the county runs 34 precincts today. Three of the four merges are nameable from the names themselves \u2014 IRISHTOWN 1 + IRISHTOWN 2 became Irishtown, LAKE 1 + LAKE 2 became Lake, ST ROSE 1 + ST ROSE 2 became St Rose \u2014 and the fourth is not: BROOKSIDE 1 through 5 became Brookside 1, 2 and 3, and no published source says which census unit became which county precinct. THAT AMBIGUITY DOES NOT BLOCK THE BOARD DISTRICTS and does block a precinct card, which is the distinction worth recording. All five Brookside voting districts sit in board District 1, so the merge cannot move a district line and the dissolve is the same whichever way it went; but a precinct card has to NAME the precinct a reader is standing in, and this build cannot say whether that is Brookside 1, 2 or 3. So the county ships a board-district dispatch entry and no precinct entry.",
      "wanted": "Which Census 2020 Brookside voting districts make up each of the county's three current Brookside precincts \u2014 a sentence from the Clerk would do it, as would any precinct boundary file. Irishtown, Lake and St Rose need nothing; they are already derivable."
    },
    {
      "id": "county-board-office-addresses",
      "concept": "County board office location",
      "area": "47 county boards — every districted board but Cook, Lake, Coles, Clark and White",
      "counties": [
        "adams",
        "boone",
        "carroll",
        "cass",
        "clinton",
        "crawford",
        "dekalb",
        "dewitt",
        "dupage",
        "edgar",
        "effingham",
        "franklin",
        "fulton",
        "grundy",
        "henry",
        "iroquois",
        "jefferson",
        "jo-daviess",
        "kane",
        "kankakee",
        "kendall",
        "lasalle",
        "lee",
        "livingston",
        "logan",
        "macon",
        "madison",
        "marshall",
        "mason",
        "mcdonough",
        "mchenry",
        "mclean",
        "menard",
        "mercer",
        "montgomery",
        "ogle",
        "peoria",
        "rock-island",
        "sangamon",
        "shelby",
        "st-clair",
        "stark",
        "stephenson",
        "tazewell",
        "warren",
        "washington",
        "whiteside",
        "will",
        "winnebago",
        "woodford"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Five county boards name an address on their card and 50 name none \u2014 Cook, Lake and Coles give an office, Clark and White a mailing line.",
      "blocker": "Corrected twice, and the second correction is the larger one. THE 31 JUL 2026 REVIEW fixed the original claim that no board card named an office: Cook does publish a district office for each commissioner (17 of 17, pinned on the map), and Lake's card shows the shared county-building office at 18 N County St, Waukegan, live from its own boundary GIS. RE-MEASURED 2026-08-20 across all 52 districted-board counties the app now serves, by reading every board-address render site in index.html and every shipped board roster rather than by sampling: FIVE counties name an address, 47 name none. Three present it as an OFFICE \u2014 Cook's per-commissioner district offices, Lake's shared county building, and Coles's 651 Jackson Ave, Room 326 with a board phone beside it. Clark and White label theirs \"Board mail\" instead, and that wording is the point rather than a shortcut: a courthouse mail line and a PO box are places to write, not places a resident can turn up at, and the card says which it is. THE SCOPE WAS THE REAL DEFECT. This record named 21 counties while 47 qualify, so 26 \u2014 Adams, Boone, Cass, Crawford, De Witt, Edgar, Effingham, Fulton, Grundy, Henry, Iroquois, Jefferson, Jo Daviess, Macon, Marshall, Mason, McDonough, Menard, Mercer, Montgomery, Peoria, Shelby, Stark, Tazewell, Washington and Woodford \u2014 carried exactly the same absence with nothing recording it, and therefore read as COMPLETE in the generated county-status table, whose own instructions say a served county with no open gap is finished. An absence recorded for 21 counties and silently tolerated in 26 more is the one claim this project's rules forbid; all 47 are listed here now, which is why this record's county count jumped rather than its substance changing. Madison publishes members' HOME addresses, which were removed rather than presented as somewhere a resident could go (the Madison/Peoria rule). The at-large counties were checked in the same pass and are a different surface: their commissioners ride the County card, where 7 of 13 publish an office (Edwards, Greene, Hamilton, Monroe, Morgan, Putnam and Schuyler), so what is recorded here is specifically the districted board card's absence.",
      "wanted": "An office address for each district, or confirmation that a county's board members hold office hours somewhere specific. Most county boards meet in one building, so a single board office address per county \u2014 the way Lake's works \u2014 is probably the honest fix, and Coles shows a county-published room number is enough to carry it."
    },
    {
      "id": "crete-municipal-clerk",
      "concept": "Municipal officials",
      "area": "Village of Crete (Will County)",
      "counties": [
        "will"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Crete's card names its President, six Trustees and Treasurer but no Village Clerk, and carries no hall address or phone.",
      "blocker": "Measured 19 Aug 2026, the day Crete first shipped. The Will Clerk's directory covers Crete, but PDF-text extraction loses the entry's head — the header, hall address/phone, the President line and the Clerk's name — the same defect that hides Lockport and Wilmington. What survives is recovered (six trustees, the appointed Treasurer), the President comes from the county's certified April 2025 canvass (Mark S. Wiater, unopposed, 720 votes), and the directory's own link annotations supply the website and clerk's-office e-mail. The Clerk herself cannot be NAMED from any readable source: the certified 2025 contest for Village Clerk reads 'No Candidate' with zero votes cast, so the office was filled by appointment afterward — the surviving fragment 'will need to run in 2027 as an unexpired 2-year term' is the tail of that note — and villageofcrete.org answers every automated client with a SiteGround captcha challenge (HTTP 202, the DeKalb posture), so the appointee's name is behind a page this project cannot read.",
      "wanted": "The appointed Village Clerk's name in any sendable form, and the village hall's street address and phone — or the village site readable, or the next directory edition's text layer carrying Crete's header. The clerk's-office e-mail the directory publishes (ktellef@villageofcrete.org) suggests the surname Tellef, which is a hint for a human, never something to ship."
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
      "summary": "Cumberland County's board is not shown, and the reason is now measured rather than assumed: its districts SPLIT precincts, so no precinct-union geometry can ever draw them. The county has a website, a GIS and a published roster — all three of which this record previously denied.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed — cumberlandcounty.org is Cumberland County MAINE's, a decoy of the browncountyil.org kind. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". Re-searched 2026-08-09 and CONFIRMED: no Cumberland County Illinois site was found under any pattern, and cumberlandcounty.org is Cumberland County MAINE exactly as this record already warned. One of only two in the sweep that held up. THAT RE-CONFIRMATION WAS ALSO WRONG, AND THE ANSWER WAS IN THIS REPO BOTH TIMES. Re-measured 2026-08-20: cumberlandcoil.gov answers HTTP 200 with a full county site — and that domain is the Clerk's own e-mail domain, sitting in data/app/il-county-clerks.json (bhoward@cumberlandcoil.gov) since long before either probe. This is the identical failure the Alexander record already named on 2026-08-09 — the probe permutes the county's NAME while the clerk roster carries the county's actual DOMAIN — and the 2026-08-09 re-search applied that lesson to Alexander and not to Cumberland, then recorded Cumberland as one of the two that 'held up'. A correction written into one record does not propagate itself. THE GIS EXISTS TOO: the county's Assessor page links a Sidwell-hosted portal (portico.sidwellco.com) backed by ArcGIS org services3.arcgis.com/wLNQBWR5Fy6KPoGg, enumerated in full at 29 services — parcels, tax, soils, roads, sections, subdivisions and Political_Townships_Cumberland. No precinct layer and no board-district layer among them, so the 'no map data' half stands; the 'no GIS' half does not, and a hostname permutation was never going to find a vendor-hosted portal. THE BOARD'S FORM IS SETTLED, AND IT RULES THE GEOMETRY OUT. The county publishes its board at cumberlandcoil.gov/county-board-members-committees/: SIX members across THREE districts named by compass point — Western, Central and Eastern — two seats each, with a phone for all six and an e-mail for five. (Read it from the HTML table, not from flattened text: district sits in column 2 and a flat extract pairs each label with the NEXT member, which silently moves everybody one row. The page also prints every member's HOME ADDRESS, which never ships.) The composition, however, cannot be built from precincts: the county's certified results at results.gbsvote.com give each district contest's precinct count as Central 6, Eastern 5, Western 3 — SUM 14 against a county of 12 precincts, identically for both parties. The over-count is real and not a pseudo-precinct artifact, which was tested rather than assumed: every countywide contest on the same canvass reports exactly 12, and the split-district state-representative contest reports 3, so the field means what it appears to. Two precincts sit in two districts each. That is the Bond/Douglas/Ford shape — MEASURED SHUT for district geometry, permanently, not pending a better source. WHAT IS BUILDABLE, and it is not the board: the PRECINCTS pass the Jasper test cleanly. TIGER's Census 2020 voting-district layer carries exactly 12 Cumberland VTDs whose names are the county's own 12 precinct names 12/12 (the county's 2026 polling notice writes roman numerals where the census writes arabic — NEOGA I & II vs NEOGA 1 / NEOGA 2 — a normalisation, not a mismatch) and whose POP100 sums to the county's exact 2020 population of 10,450. The vendor's own county page independently states 'Precincts: 12'. A THIRD SOURCE AGREES AND ADDS SOMETHING, found 2026-08-20 in the frontier fabric sweep: ISBE's certified precinct-level returns for the 2026 General Primary carry TWENTY rows for the CUMBERLAND authority, not twelve — but they are sub-precinct REPORTING UNITS, numbered 1-20 in township order (SPRING POINT-7, -8, -9, -10; CROOKED CREEK-19, -20; NEOGA 1-3, -4), and stripping the trailing id reduces them to exactly the census twelve. So the precinct count is 12 and that is now three-way confirmed. The twenty is not noise either: a county subdivides a precinct for reporting when a district line runs through it, which is independent corroboration of the split this record proves from the board contests' 6+5+3 against 12. So Cumberland could join for precincts alone, the way Calhoun and Morgan did, with polling places available from the Clerk's 2026 General Primary notice (eight buildings serving the twelve). CORRECTED 2026-08-20 — THE 'NO WEBSITE' FINDING ABOVE IS FALSE, and it was false the day it was written. The pass-13 probe permuted the county's NAME across five domain patterns; the county's actual domain was already in this repo, in data/app/il-county-clerks.json, as the host of its Clerk's own e-mail address. That is the identical systematic failure Johnson's record diagnosed on 2026-08-09 and it was never swept across the other counties. Probing every frontier county's clerk-e-mail domain instead reaches a live site in EIGHTEEN of the thirty-one, several of them at hostnames no name permutation would produce (piatt.gov, bureaucounty-il.gov, hancockcounty-il.gov, champaigncountyclerkil.gov). For Cumberland the site is https://cumberlandcoil.gov/ (58 KB) — the clerk-e-mail domain, note, not the cumberlandcounty.org the probe rejected as Cumberland County MAINE — and its homepage links County Board, County Board Members & Committees, Elections, Election Results and a GIS Portal. The GIS Portal is the interesting one, since this record's standing blocker is that Cumberland's districts SPLIT precincts and only a county-drawn boundary can express them. THE GIS PORTAL LEAD IS MEASURED SHUT (2026-08-21), and it is closed here by the same pass that opened it. The 2026-08-20 correction that found this county's website called its GIS Portal 'genuinely promising', because this record's blocker is that Cumberland's districts SPLIT precincts and only a county-drawn boundary can express them. It publishes no such boundary. The portal is an ArcGIS Experience Builder app (portico.sidwellco.com, item a9b99ff31b794f79936608e22b50effa) and its own configuration references SEVEN services, every one of them parcel or tax valuation. Widening to the whole Sidwell hosting org (services3.arcgis.com/wLNQBWR5Fy6KPoGg) finds 26 services, of which 7 are Cumberland-keyed — Parcel, Parcel_Landuse, Parcel_Soils, Sections, SubDivisions, Corporations and Political_Townships — and ZERO across the entire org carry district, precinct, board, election or voting in their name. So this is the Henry pattern confirmed for a second county: Sidwell Portico is a parcel product, and a county whose only mapping surface is Portico has no GIS route to its board districts. The ask is unchanged and is now the only route: the county's own district boundary as data or as a map.",
      "wanted": "Nothing further on the board's FORM or its roster — both are published and read above. For the DISTRICTS, the only thing that would help is the county's own district boundary as data or a map, because the precinct route is measured shut. The buildable work needs no publisher at all: the 12 precincts are already derivable from census voting districts that match the county's own precinct list 12/12, and the Clerk's 2026 polling notice pairs them with buildings."
    },
    {
      "id": "dewitt-township-officials",
      "concept": "Township officials",
      "area": "De Witt County's 13 townships",
      "counties": [
        "dewitt"
      ],
      "kind": "data-quality",
      "layer": "township",
      "summary": "De Witt's township cards name the township but not its officers, even though the county's own township-officials list is in hand \u2014 the document itself blocks an honest build.",
      "blocker": "Measured 19 Aug 2026, the day township officials became a concept (Cook shipped first, from its Clerk's structured directory API). Clerk Kari Harris's 17 Aug reply carried 'DeWitt County Township Officials', updated 8/4/2026, archived under data/source/raw/ beside the municipal list that DID build \u2014 13 townships, every officer named. Three defects block it, each measured rather than assumed: the PDF is a page-per-image scan with NO text layer at all (pypdf extracts zero characters from every page), so any read is OCR; its two-column layout prints role labels ('Trustees' spanning four name rows) whose line spacing does not match the name column, so attaching a role to a name means guessing \u2014 the exact thing the honesty rules forbid; and every address on it is a HOME address, the class this fleet never ships (the Washington/Mason rule), so even a clean read would ship names and roles only.",
      "wanted": "The same list in any text-bearing form \u2014 the file it was scanned from, a spreadsheet, or a re-export \u2014 with each role attached to its name unambiguously. Only names, offices and any township-hall contact would ship; the home addresses never would."
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
      "summary": "Douglas County's board districts are not shown — the county's own certified results settle its board's form and then rule the returns route OUT.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (douglascountyil.gov) is real and current: elections live under the County Clerk, and assessments run on DEVNET tooling plus the illinoisassessors.com parcel viewer — a commercial parcel product, not an election map system. Nothing on the site links district or precinct boundaries.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR DOUGLAS THE FORM IS SETTLED AND THE ROUTE IS OPEN. Its certified 2026 General Primary carries single-member contests for districts 4, 5 and 6 over 7 of the county's 17 precincts, with no precinct in two districts, so the board is districted and at least six-membered. The census fabric passes cleanly: 17 VTDs, 17 county precincts, names matching, populations summing to the county's exact 19,740. WHAT IS MISSING is districts 1-3, which were not on this ballot and which the county's older certified canvasses would supply.  ROUTE CLOSED 2026-08-18, by finding the older results the note above asked for. Douglas publishes them on its own site as tagged news posts (douglascountyil.gov/news?tags=35), and the 2022 and 2024 General files are text-layer PDFs. They are ELECTION SUMMARY REPORTS, not Statements of Votes Cast: each district contest prints its winner and its NUMBER of precincts, never their names. That number is what closes the route. The 2022 General shows SEVEN single-member districts — the board is bigger than the three-district 2026 ballot suggested — with precinct counts of 2, 2, 3, 2, 3, 2 and 5. THOSE SUM TO 19 AGAINST THE COUNTY'S OWN 17 PRECINCTS, stated on every page of the same document as \"17 of 17 Precincts Reporting\". Two precincts are therefore in two districts each: Douglas SPLITS precincts, so no dissolve of whole ones can draw it — the Jasper/Wade shape, reached here by arithmetic rather than by a map. A SECOND, INDEPENDENT PROBLEM found in the same pass: the county ran 17 precincts in 2022, EIGHTEEN in 2024 (\"18 of 18 Precincts Reporting\") and 17 again in 2026, so its fabric moved twice after the census and the 2020 VTDs cannot be assumed to be its current precincts even where the counts agree. What the pass DID settle, and is worth keeping: the board is seven single-member districts, and the 2022 General certified Hein (1), Appleby (2), Hettinger (3), Morris (4), Henry (5), Carleton (6) and Luth (7), with Travis L. Wilson taking District 1 in 2024.",
      "wanted": "Douglas County's seven board district boundaries as map data — that is now the whole ask, because the returns route is measured shut. Failing that, the composition in a form that says WHERE the two split precincts divide, since a precinct list alone cannot describe this county's districts. A Statement of Votes Cast (rather than the summary report the county posts) would at least name the precincts in each district."
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
      "blocker": "The 31 Jul 2026 sweep found current city-published ward data with officeholder details for Elmhurst, Wheaton, West Chicago, Lombard and Glendale Heights — West Chicago was added on 2 Aug 2026, and the other four need re-finding — plus Darien with recent-ish boundaries but stale details. Wood Dale, Oakbrook Terrace and Warrenville appear only in the county's municipal ward dataset, whose details read “Updated 04/29/2021” and whose boundaries have not been checked against the post-2020 redraws. Showing it could draw pre-redistricting lines. RE-MEASURED 2026-08-20 AND TWO OF THE THREE NOW HAVE A CITY-PUBLISHED, POST-REDRAW SOURCE. WARRENVILLE publishes a 'Ward Boundaries Map' on its OWN ArcGIS org (warrenville.maps.arcgis.com, webmap cd142fb55239400b8ca2c207417ad771) backed by services5.arcgis.com/TkBKgQn8d3sPkMZo/Wards_DEC22 — four layers, Ward_1 through Ward_4, last edited 2025-04-17 and named for a December 2022 redraw, so it post-dates the 2020 census. BUT IT IS NOT A BOUNDARY LAYER AND MUST NOT BE PULLED AS ONE: its fields are PARCEL fields (PIN, BILLNAME, BILLSTNUM, BILLSTNAME, BILLCITY, BILLZIP, PROPNAME), so each 'ward' is a set of parcels grouped by ward — 1,771 / 1,246 / 1,376 / 1,036, and ALL 5,429 of them carry a populated BILLNAME, which is the property owner's billing name, alongside their mailing address. A builder reaching for 'Warrenville wards' would ingest five thousand owners' names and addresses. A ward boundary can be DISSOLVED from it — the Rock Island / Boone tax-parcel pattern — provided every attribute is dropped, and with the caveat that a parcel dissolve covers only parcelled land, so rights-of-way and water fall outside and the edge is approximate. OAKBROOK TERRACE publishes ward_map_2025_opt.pdf from its own Ward Map page — one page, 2.1 MB, a REAL TEXT LAYER (7,954 characters) and 923 VECTOR PATHS alongside 25 embedded images. That is the White County route and it is worth attempting; the thing a builder must establish first is that the WARD LINES are among those vector paths rather than inside the rasters, because a map whose linework turns out to be raster is what sank Jasper's. WOOD DALE IS THE ONE STILL DARK: wooddale.com answers 403 with a 408-byte body, so nothing city-published could be read at all. It remains the only one of the three for which the county's 2021 dataset is the sole source.",
      "wanted": "City-published ward data for the three, or each city's adopted redistricting ordinance so the county dataset's boundaries can be checked against it."
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
      "blocker": "Found 4 Aug 2026 in the pass-13 sweep, and the county SHIPPED the same day as the forty-fourth dispatched county and the outline's first island — board, precincts, fire, park and library all from its GIS org (effinghamcoil.maps.arcgis.com, EFFINGHAM COUNTY GIS, invisible to keyword search because no item title names the county). What that org does NOT carry is the municipalities: 12 boundary shapes with no officials, so the Municipality card names each city without its council.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". RE-CHECKED 2026-08-20 and the finding holds, with one route now measured rather than untried: the county's own site (effinghamcountyil.gov, reached from the Clerk's e-mail domain) publishes a page literally called Directory, which is the obvious candidate and is NOT one — it lists county DEPARTMENTS only, and none of the county's municipalities except Effingham itself appears on it at all (Altamont, Beecher City, Dieterich, Edgewood, Montrose, Shumway, Sigel: zero hits each). So there is no county-published municipal roster to find, and the remaining route is per-municipality — the Will-cities / Freeport pattern of city-level payloads — rather than one county document.",
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
      "blocker": "Checked 2 Aug 2026: “County-Board-District-Map-Effective-2022.pdf” is an export from mapping software, its text reads cleanly, and it draws both the 7 board districts and 28 named precincts — so a mapping system somewhere holds both. Neither appears among the 34 datasets the county publishes online (all of them checked), and the state's copy is a 2014 scan. One caveat about the PDF: its title block reads “2020 ... District & Precinct Map” though it is filed as effective 2022. The member list is unusually complete: all 14 with party (12 Republican, 2 Democratic) and term end. RE-MEASURED 2026-08-20, AND THE PRINTOUT IS BETTER THAN THIS RECORD GIVES IT CREDIT FOR. The map the county publishes — County-Board-District-Map-Effective-2022.pdf, linked from its own County Board page as 'View The District Map' — is a VECTOR PDF, not a raster printout: one page at 792x1224pt carrying 802 drawing paths, of which the large ones are multi-segment strokes of 99, 243, 311 and 748 items each, i.e. real boundary linework. Its 26 embedded images are every one 2250x234 — banner strips, a title/legend band and Esri basemap furniture, not the map body. That is the WHITE COUNTY ROUTE, where a vector PDF became shipped geometry. WHAT THE MAP'S OWN TEXT LAYER CARRIES, and it is the useful part: TWENTY TOWNSHIP NAMES and the district numbers 1 through 7. The townships match TIGER's twenty Fayette county subdivisions TWENTY OUT OF TWENTY, the single difference being the map's abbreviation 'SO HURRICANE' against TIGER's 'South Hurricane' — an abbreviation, not a different place. So if Fayette's seven districts are unions of WHOLE TOWNSHIPS, the geometry does not need the PDF at all: it needs only the township-to-district assignment, and TIGER supplies the polygons. WHAT IS NOT ESTABLISHED, and must be before any build: whether the districts ARE whole-township. Twenty townships over seven districts averages under three apiece, and the county seat (Vandalia) is exactly where a split would fall — the Bond and Douglas failures were both splits found only by counting. The assignment itself is encoded spatially on the map, district-number labels sitting inside district areas and township names inside townships, so extracting it means reading label positions against the vector boundaries rather than reading a list. THE BALLOT ROUTE IS CLOSED HERE, checked rather than assumed: il-fayette.pollresults.net returns the vendor's generic 2,788-byte shell (4 electionData blocks) rather than a carried county's payload, and Fayette appears on neither the GBS nor the platinumelectionresults county lists.",
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
      "blocker": "Checked 2 Aug 2026: the board page prints each district's townships, and the board is unevenly sized (District 1 has 3 members, District 2 has 4, District 3 has 4). But Patton 3 appears in both District 1 and District 3, so that precinct is split and township boundaries alone cannot rebuild the lines. The one map, on the state's site, is titled “2011 County Board Districts” while the file itself was last changed on 9 Nov 2021 — either a re-upload of the old plan or a mistitled new one, and nothing published settles which. The county runs no mapping system of its own. The member list (names, district, phone and county emails) is freely available. ASKED 3 Aug 2026 — this record's exact question (which plan is in force, and the Patton 3 split), to Clerk Vaughn; no response as of 4 Aug.  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR FORD THE SWEEP CONFIRMS WHAT THIS RECORD ALREADY SAID, from an independent source. Its certified 2026 General Primary carries all three districts ('Vote for 2' apiece, a six-member board) covering all 22 precincts, and PATTON 3 appears in BOTH the 1st and the 3rd district's contest — the same shared precinct this record was written about, now visible in the county's own returns rather than only in its township list. The census fabric otherwise passes cleanly (22 VTDs, 22 precincts, exactly 13,534), so Patton 3's division is the whole remaining ask.",
      "wanted": "Confirmation of which plan is currently in force, plus precinct boundaries — or simply a description of how Patton 3 is split. The township list is otherwise ready to use."
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
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. gallatinco.illinois.gov answers 200 and is the county's own site. Note the abbreviation: gallatinCO, not gallatincounty — the same shape as colesco.illinois.gov. gallatincounty.org is a decoy (a weather site). The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website. RE-MEASURED 2026-08-20 and the county is DARK to this client on every route tried. The clerk's own e-mail domain — CountyClerk@gallatinco.illinois.gov, from il-county-clerks.json, which is the lookup that corrected Cumberland and Alexander — does not resolve at all, nor do gallatincountyil.gov, gallatincounty.illinois.gov, co.gallatin.il.us or gallatincountyillinois.gov. So the 2026-08-09 correction that found websites for nine of these counties by reading the Clerk's mail domain does NOT rescue Gallatin: here the mail domain is itself unresolvable. THE BALLOT ROUTE IS ALSO CLOSED, and measured: il-gallatin.pollresults.net returns the vendor's generic 2,788-byte shell — byte-identical in size to Fayette's and to a made-up county's — rather than a carried county's payload, and Gallatin is on neither the GBS nor the platinumelectionresults county list. Nothing here is a refusal; it is absence. The board's form remains undetermined and an e-mail to the Clerk is the only route left.",
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
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. hardincountyil.gov answers but is minimal: its homepage surfaced no GIS, election, or board links to follow. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\".  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR HARDIN THE FABRIC IS PROVEN AND THE FORM IS STILL UNKNOWN. The census fabric passes cleanly — 6 VTDs, the county's 6 precincts, populations summing to its exact 3,649 — but its certified 2026 General Primary carries NO county-board contest at all, so this pass could not tell whether the board is districted or elected at large. Its Clerk's results archive on the same vendor is where that answer lives; an at-large answer makes Hardin a County-card county needing no geometry whatsoever. ANSWERED 2026-08-20 WITHOUT THE COUNTY'S WEBSITE AND WITHOUT A REPLY — Hardin IS carried by the il-<county>.pollresults.net vendor, which this project's own 34-county list did not record it under. TESTED BY CONTENT, NOT STATUS, because that is the documented trap: il-hardin.pollresults.net returns 128 KB carrying a real embedded result set, where il-gallatin and il-fayette both return the SAME 2,788-byte generic shell (the uncarried signature) and il-henderson answers 302 with an empty body. THE FORM IS SETTLED — AT LARGE. Its certified 2026 General Primary (ElectionId 1566, Final: true, updated 2026-03-30) carries 43 races, and the board's are a single 'D COUNTY COMMISSIONER' and a single 'R COUNTY COMMISSIONER', each reporting ALL SIX precincts with none not-reporting. There is no district-suffixed board contest anywhere in the file; every county office reports 6 of 6, and the only races reporting 1 are the six precinct-committeeperson contests, which is the expected shape and the check that the reporting counts mean what they appear to. So Hardin is a COMMISSION county electing county-wide: there is no board geometry to seek and none should be invented, and this moves to the tranche-5 County-card roster path exactly as this record's own instruction prescribed. The 2026 Republican primary winner is named (Darrick Armstrong, 475 votes) but a primary winner is not a sitting member and no roster is claimed from it — the Scott reasoning applies unchanged. THE FABRIC IS ALSO CONFIRMED, incidentally: the vendor names the county's six precincts (Rock, Monroe, Rosiclare, Stone Church, McFarlan, Cave In Rock) and Census 2020's six Hardin voting districts match them 6/6 on name (hyphenation aside) and sum to the county's exact 3,649. RE-MEASURED 2026-08-20, and the parking lander is confirmed on BOTH hosts. hardincountyil.gov and www.hardincountyil.gov each answer HTTP 200 with the same 114-byte body — a bare <script> that redirects to /lander — so there is no county content on that domain to scrape, and this is a genuine parking page rather than the Coles case of a real site behind a broken certificate. The www host was checked separately because the Internet Archive's index points at it, and it serves the identical lander. The Archive does hold a 200 capture of www.hardincountyil.gov dated 2026-07-18, whose CONTENT this environment cannot read (web.archive.org is refused by the sandbox's egress policy, while archive.org's availability API answers normally) — so whether that capture is the lander too, or a real site parked since July, is not determinable from here and should not be guessed. The Clerk's e-mail works; the standing third-attempt draft to Clerk Cowsert remains the only route.",
      "wanted": "Not the form — it is settled AT LARGE above from certified returns, so there is no board geometry to seek and none should be invented. What is wanted is the County-card roster path this record's own instruction prescribes: a county-published list of the sitting commissioners. A certified return names who WON a contest, never who holds the seat today, and a mid-term appointment appears in no return anywhere (the Scott reasoning)."
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
      "blocker": "Checked 3 Aug 2026. hendersoncountyil.gov, the domain in the state's clerk directory, returns a 114-byte page whose only content forwards the visitor to a generic parking screen. At roughly 6,000 people Henderson is the smallest county on the frontier, and it became one only because neighbouring McDonough was added the same day. Nothing for it appears in the state map catalogue. RE-MEASURED 2026-08-20 AND THE MECHANISM IS NOW NAMED: hendersoncountyil.gov is not a holding page the county controls, it is a PARKED DOMAIN. It answers 200 with a 114-byte body whose entire content is window.location.href=\"/lander\", and /lander identifies itself as parking (LANDER_SYSTEM=\"PW\", _trfd.push({ap:\"parking\"})), on A record 15.197.148.33. That 114-byte script-only redirect is the exact `hollow` state validate_card_links.py learned to catch this week, and byte-for-byte the same shape as Morris's. Three alternate patterns were tried and none resolves at all (henderson-county-il.gov, hendersoncounty.illinois.gov, hendersoncountyillinois.gov), so there is no county website anywhere to find. WHAT THIS APP SHIPS ON THAT DOMAIN: the Clerk's e-mail, avanarsdale.coclerk@hendersoncountyil.gov, carried in il-county-clerks.json from ISBE. The domain DOES have MX records, so that address plausibly still receives mail even though the web side is parked — the Wabash pattern, where a domain carries mail and serves no page. That was checked rather than assumed, and it is the reason this record does not claim the Clerk is unreachable.",
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
      "summary": "Jasper's three districts are now fully composed from certified canvasses — every township but one is whole; only Wade Township's four current precinct boundaries are missing.",
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county's web presence is a SHARED site with the City of Newton (jaspercountyillinois.gov) \u2014 one site, two governments. It carries a County Board page and a Maps page, but the maps are reference PDFs (county map, city limits, TIF areas), not election geometry, and no district or precinct boundary appears. jaspercounty.org is Jasper County MISSOURI's, a decoy. Whether the board is districted or elected county-wide was not determinable in this pass \u2014 determine it from a certified election document (EXPANSION_GUIDE \u00a72.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request \u2014 its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". ANSWERED 17 Aug 2026 \u2014 Clerk Tarr, in writing: \u2018board members are elected from districts. Please see the attached map.\u2019 FORM SETTLED \u2014 DISTRICTED (\u00a72.5 step 2 satisfied by the election authority's own statement plus the county's adopted map, \u2018County Board Redistricting Effective 2022\u2019, archived from her e-mail). The map's linework is RASTER inside the PDF (13 vector paths on the county page, all decoration), so nothing polygonizes and the labels this record originally transcribed from it were unreliable. MEASURED 17 Aug 2026, and the map turned out not to be needed: THE COMPOSITION IS SETTLED FROM CERTIFIED CANVASSES, the White route. The county publishes precinct-level results, and its 2024 General and 2026 General Primary reports each tabulate the three 'FOR MEMBERS OF THE COUNTY BOARD DISTRICT n' contests precinct by precinct \u2014 the two canvasses agree on all 15 precincts, independently. DISTRICT 1: Crooked Creek, Grandville, Hunt City and Willow Hill townships + Wade 4. DISTRICT 2: Grove, North Muddy and South Muddy townships + Wade 2. DISTRICT 3: Fox, Smallwood and Ste. Marie townships (BOTH its precincts, so the township is whole) + Wade 1 and Wade 3. Ten of the eleven townships are undivided; only WADE TOWNSHIP, which contains Newton the county seat, is split \u2014 four ways, across all three districts. THE ONE REMAINING OBSTACLE IS WADE'S GEOMETRY, and it is measured rather than assumed: Census 2020's VTD fabric carries FIVE Wade voting districts (WADE 1-5, populations 756/1098/924/707/895) where the county currently runs FOUR precincts, and no assignment of the fifth to a district reproduces a lawful plan \u2014 the best case leaves a 22.0% spread between the largest and smallest district (3462/2780/3045 against an ideal of 3096), against roughly 10% for an adopted map. So the county re-precincted Wade after 2020 and the census Wade fabric is NOT the county's current one. Everything outside Wade builds from TIGER townships today; nothing was built, because a board layer that cannot answer the county seat is not a county. ONE SURFACE FOUND 2026-08-20 THAT DOES NOT CLOSE THIS, recorded so nobody re-finds it hopefully: Jasper is carried by a SECOND statewide results vendor (results.gbsvote.com, thirteen Illinois counties) that this project had not previously recorded. It publishes the county's current precinct list and per-precinct committeeperson contests, so it can corroborate that Wade runs four precincts today \u2014 but it carries no geometry of any kind, and geometry for those four lines is the entire remaining ask here.",
      "wanted": "WADE TOWNSHIP'S FOUR CURRENT PRECINCT BOUNDARIES — as GIS data, or as the streets/wards dividing Newton between Wade 1, 2, 3 and 4. That is the whole remaining ask: the districts' composition is settled from two certified canvasses and the other ten townships are whole, so Wade is the only geometry this county still needs. ASKED 17 Aug 2026 in general terms on the Clerk's own thread; the narrowed Wade-only question is drafted for the operator to send."
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
      "blocker": "Researched 8 Aug 2026, closing an absence that had NO record at all: Jersey is served as a 7th-Circuit secondary and its board did not surface. FORM SETTLED — DISTRICTED: jerseycounty-il.gov/county-board/ gives each member a \"Jersey County Board District N\" line, three members per district across Districts 1-4 (Crone, Grizzle, Hayes 1; Heitzig, Mills, Ward 2; Wagner as Chairman, Ontis as Vice Chair, Beasley 3; Figge, Beers, Keonig 4), with committee assignments and biographies. That is a geometry ask, not the County-card path. No GIS SERVICE exists: gis.jerseycounty-il.gov and maps.jerseycounty-il.gov have no DNS record (resolved directly rather than inferred from a failed fetch), and the ArcGIS Online catalogue returns nothing county-keyed. CORRECTED 2026-08-08, and the correction is the point: this record originally said Jersey publishes no district boundaries at all, which was FALSE and was written without ever running a web search. THE COUNTY CLERK HAS A SEPARATE DOMAIN — jerseycountyclerk-il.gov, never probed because the clerk roster carries jerseycounty-il.gov — with a MAPS section publishing County Board Districts, Precincts/Polling Places and School Districts. The board-districts file (/media/pdf/County_Board_Districts___County__Roads2016.pdf, 792 KB) is a genuine VECTOR map, 5,117 paths, whose legend names District 1 through District 4, matching the twelve members three-per-district. TWO THINGS STILL STAND BETWEEN THAT AND A BUILD, and neither is 'nothing exists'. Its filename and content date it to 2016 — BEFORE the post-2020 redistricting every Illinois county did in 2021 — so it may describe superseded lines, and no newer edition was found. And a first pass found no large filled paths to lift the district polygons from, so the fills may be among the page's 14 raster images rather than vectors; the Stephenson georeferencing precedent applies if they are recoverable at all. RE-MEASURED 2026-08-20. The Clerk's MAPS menu was inventoried and the 2016 date on the board map is confirmed as the newest: jerseycountyclerk-il.gov offers exactly three, County Board Districts (County_Board_Districts___County__Roads2016.pdf), Precincts/Polling Places (CC-Polling-Places-2021.pdf) and a Jersey-PnP-GIS.jpg. THE 2021 FILE IS NOT A POLLING LIST, it is a precinct MAP with a text layer — road names and 22 precinct labels, and ZERO occurrences of the word district — so it does not pair precincts to districts and cannot answer the composition question the wanted line asks. THE BALLOT ROUTE IS CLOSED, measured rather than assumed: il-jersey.pollresults.net returns the vendor's generic 2,788-byte shell (4 electionData blocks), the same response a made-up county name gets, and Jersey is on neither the GBS nor the platinumelectionresults county list. So no certified return names which precincts vote in which district contest, which is the route that settled Franklin and Wayne. The roster half remains fine — the county board page names all twelve members with their district numbers.",
      "wanted": "Whether the 2016 map on jerseycountyclerk-il.gov is still the operative one after the 2021 redistricting, and if so the GIS or CAD file behind it — the map exists, so this is a request for its data and its currency rather than for a boundary nobody has drawn. Failing that, the precincts making up each district, which the Clerk also maps."
    },
    {
      "id": "jodaviess-jersey-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Jo Daviess and Jersey counties",
      "counties": [
        "jo-daviess",
        "jersey"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Neither county publishes precinct boundaries, and neither can be built from census geometry \u2014 each merged precincts after 2020, so the census fabric is one merge out of date in both.",
      "blocker": "Measured 2026-08-20, in a sweep of ten served counties that had no precinct layer and \u2014 until this record and its backlog sibling \u2014 nothing saying why. Both counties turned out to be the hard case, and for the same reason. JO DAVIESS runs 28 precincts against the census's 29: it merged WARREN I and WARREN II into a single Warren, which the county's own two surfaces both confirm (its results page lists the 28 in prose, and its GIS department's polling map, revised 12 Aug 2026, groups shared sites explicitly while writing Warren singular). JERSEY runs 22 against the census's 25: Jersey Township went from ten precincts to eight and Quarry 1 and Quarry 2 became one Quarry, read from the Clerk's own precinct-level Statement of Votes Cast. IN BOTH COUNTIES THE POPULATION CHECK PASSES EXACTLY (22,035 and 21,512 against each county's own Census 2020 count), which is precisely the trap this project has now hit three times: a census fabric that tiles the county perfectly is still not the county's CURRENT fabric, and only the name comparison catches it. NEITHER PUBLISHES THE GEOMETRY. Jo Daviess runs a GeoMedia mapping portal rather than ArcGIS \u2014 reached only through a hostname its own GIS page names, not through the usual slug ladder, the Vermilion lesson repeating \u2014 whose free public tier carries township and road layers and the word \"precinct\" nowhere; its countywide precinct map is a raster with 81 characters of text on it. Jersey's county ArcGIS carries township, section, subdivision and parcel layers and no precinct layer, which is pointed: the same vendor org publishes precinct layers for its other clients, including one for a neighbouring Illinois county. Jersey's precinct map is a vector PDF with the precinct names drawn as labels rather than attributed geometry. Note Jo Daviess is also the county that sells its GIS data under a signed licence (the boundary this project bought), so its precinct geometry may exist behind that same counter rather than not at all. JERSEY'S HALF RE-MEASURED 2026-08-20 AND IT IS NOT ONE MERGE — it is two events, and only one of them is composable. Census 2020 carries 25 Jersey voting districts summing to the county's exact 21,512; the Clerk's own 2021 precinct map carries 22 labels. Five differences are pure suffix normalisation (the Clerk writes English 1, Fidelity 1, Richwood 1, Rosedale 1, Ruyle 1 where the census writes the bare name). The real differences are: (1) QUARRY 1 + QUARRY 2 -> QUARRY, a merge the surviving name describes, which check_fabric_composed handles exactly as it handles Calhoun's Belleview-Hamburg; and (2) JERSEY 9 AND JERSEY 10 SIMPLY VANISH. Jersey 1 through 8 all survive, so those two precincts' population was absorbed into some subset of them and NOTHING PUBLISHED SAYS WHICH. 25 - 1 (Quarry) - 2 (Jersey 9, 10) = 22, which is the arithmetic that proves the account complete. That second event is the whole blocker: a self-describing merge can be dissolved, an unnamed absorption cannot, and guessing which of Jersey 1-8 grew is precisely what the honesty rules forbid. So this record's ask for Jersey narrows to one sentence from the Clerk: where did Jersey 9 and Jersey 10 go.",
      "wanted": "The current precinct boundaries as map data from either county \u2014 or, for Jo Daviess, the single fact of how the old Warren I/Warren II line was dissolved, and for Jersey how Jersey Township's ten precincts became eight and where Quarry's internal line went. Each county is exactly one merge away from being buildable from census geometry, so a short written answer would do as well as a shapefile. Neither has been asked."
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
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask. PARTLY ANSWERED BEFORE IT WAS ASKED: the Clerk herself wrote on 21 Jul 2026 — \"We don't have a website to point back to\" — so the probe's no-website finding is now the county's own statement. The board-form and boundary questions remain open; the pass-14 draft asks them and thanks her for the earlier reply. THE BOARD-FORM QUESTION IS NOW ANSWERED, 2026-08-20, without the county's website and without a reply: Johnson is one of thirteen Illinois counties whose Clerk publishes certified results through results.gbsvote.com (l_id=12), and both the 8 Nov 2022 and 5 Nov 2024 GENERAL ELECTIONS — each marked OFFICIAL — carry a single contest, \"FOR COUNTY COMMISSIONER\", reading \"16 of 16 precincts reporting / Vote for ( 1 )\" (John McCuan in 2022, Jason Taylor in 2024). One seat, the whole county voting, no district string anywhere on the ballot. So Johnson is a COMMISSION county electing at large: there is no board geometry to seek and none should be invented, and this becomes a roster ask on the tranche-5 County-card path exactly as this record's own instruction said it would. The portal also states the county's precinct count as 16, which the two canvasses corroborate. What it cannot supply is the sitting roster — returns record who WON a contest, never who holds the seat today, and an appointment to a mid-term vacancy appears in no return (the reasoning already worked out in full on the Scott record, which is the same shape and the same portal). CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. johnsonco.illinois.gov RESOLVES, though it refuses this network (TLS reset). That sits in tension with the Clerk's written statement that the county has no website, which stands as the authority until re-asked — but the domain is live and should be re-checked from an ordinary browser before this record is trusted again. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website. TWO CORRECTIONS 2026-08-20, and the first invalidates evidence this record was resting on. (1) THE 'TLS RESET' WAS NEVER EVIDENCE ABOUT THE COUNTY. Re-probing johnsonco.illinois.gov and reading the certificate actually presented shows it is issued by 'O = Anthropic, CN = Egress Gateway SDS Issuing CA (production)' — this sandbox's own MITM proxy, not the county's server — so what the 2026-08-09 note recorded as the county refusing this network is a measurement of the intermediary. That is the same class of mistake already recorded for github.com's proxy-issued 403s: never record a host from a local run without checking who answered. Sibling .illinois.gov hosts verify cleanly through the identical proxy (clintonco and www.illinois.gov both return 200), and Johnson's OpenSSL verify code differs from the code Coles's genuinely incomplete chain produces, so the failure is specific to this host and its cause remains UNMEASURED from here rather than established. (2) THE SITE IS LIVE, which contradicts the Clerk's July statement that the county has none: the Internet Archive's availability API reports a 200 capture of https://johnsonco.illinois.gov/ dated 2026-08-11, nine days before this check. Its content could not be read here because web.archive.org is refused by the sandbox's egress policy while archive.org itself answers. So the county very likely publishes its commissioners today, and reading them needs a client outside this environment — an ordinary browser would settle it in one visit.",
      "wanted": "Not the form — it is settled AT LARGE above from certified returns, so there is no board geometry to seek and none should be invented. What is wanted is the County-card roster path this record's own instruction prescribes: a county-published list of the sitting commissioners. A certified return names who WON a contest, never who holds the seat today, and a mid-term appointment appears in no return anywhere (the Scott reasoning)."
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
      "blocker": "Checked 31 Jul 2026: the city's data returns 10 shapes for 7 wards, with duplicates of the 4th, 6th and 7th. Test points land inside both copies of the 6th and 7th, and the centre of the 1st ward also falls inside the 2nd ward's shape. Nothing in the data marks which copies are the current, 2022-approved ones, so removing duplicates would be guesswork until each is checked against the city's adopted 2022 ward map. The city's directory publishes all 14 alderpersons with phone and email, ready to attach. RE-MEASURED 2026-08-20 AND THE REFEREE THIS RECORD ASKS FOR IS PUBLISHED, but it cannot settle the question automatically. The city links 'Ward Map PDF Download' from its own elected-officials directory at a stable address (citykankakee-il.gov/perch/resources/admin/ward-map2022approved.pdf) — literally the 2022 approved map the wanted line names. It is a RASTER: one page, ONE embedded image, ZERO text characters and ZERO vector paths, so unlike Fayette's or Oakbrook Terrace's maps the White route does not apply and no geometry can be extracted from it. It can still adjudicate the mixed old/new shapes, but only by eye, one ward at a time — which makes this a human comparison rather than a build, and is worth knowing before anyone budgets it as the latter.",
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
      "blocker": "Checked 2 Aug 2026: knoxcountyil.gov — and the old address, which redirects into the same block — refuses every request, including the page that lists all 15 members with district, term and contact details. The only usable district boundaries published anywhere are on the City of Galesburg's map account: districts 1 to 3, the three that fall within the city, adopted by the County Board on 27 Oct 2021. Districts 4 and 5, the rural remainder, appear in no usable source we could find, and the state's countywide map is provably 2011 content, from before the 2021 redistricting. BALLOT ROUTE CHECKED AND CLOSED 2026-08-20: il-knox.pollresults.net returns the vendor's generic 7,583-byte shell with 4 electionData blocks — the response a made-up county name gets — against the ~52 blocks a carried county returns, so no certified per-precinct return is available to compose districts from. Knox is on neither the GBS nor the platinumelectionresults county list either. That closes the route that settled Franklin and Wayne, and leaves this record's own asks (the 2021 board packet, or a mirror the blocking does not cover) as the only ones open. ENCLOSED 2026-08-21: Warren's join made Knox the coverage wash's THIRD ENCLAVE, after Bureau and Christian. Every one of its seven neighbours \u2014 Henry, Stark, Peoria, Fulton, McDonough, Mercer and now Warren \u2014 is served, so this county now reads as a doughnut on the map rather than as frontier, which makes its absence the visible kind. Nothing about the blocker changed: the countywide 2021 map is still most likely inside the 27 Oct 2021 board packet on a site that refuses automated visits. What changed is who notices. A FOURTH RESULTS VENDOR, found 2026-08-21 and recorded here because nobody had it: results.gbsvote.com (GBS). It is not the accessliberty/pollresults pair and not platinumelectionresults.com; it carries THIRTEEN Illinois counties — Cass, Cumberland, Fulton, Greene, Grundy, Jasper, Johnson, Knox, Morgan, Perry, Scott, Warren and Washington — of which FIVE are unserved (Cumberland, Jasper, Johnson, Knox, Perry). Each county page lists its election authority and an archive of result sets back to 2016 at /locations/county_results.asp?id=N, and it was reached from the county's own Elections page rather than by guessing a hostname. FOR KNOX IT OPENS A DOOR AND THEN SHOWS THE ROOM IS PROBABLY EMPTY. The vendor carries Knox with an archive back to 2016 and names its election authority (County Clerk Scott G. Erickson), which is a route into a county whose own website refuses automated visits — worth recording for that alone. But the 2024 General reports COUNTY BOARD DIST 4 across 13 precincts and DIST 5 across 15, against a county total of 29. Two of five districts covering 28 of 29 precincts is only possible if precincts are SHARED between districts, which would put Knox with Bureau, Cumberland, Douglas, Ford and Piatt in the split-precinct class that no whole-precinct dissolve can draw. That reading is consistent with what this record already says — only the Galesburg half of the five districts exists as usable map data, the city being where the lines cut. IT IS NOW MEASURED SHUT RATHER THAN SUGGESTIVE, 2026-08-21, on the vendor's own archive across SIX result sets and TWO districting plans. Under the 2021 map: Nov 2022 (OFFICIAL) DIST 4 = 13 and DIST 5 = 15 against a county total of 28 — the districts covering the whole county; Mar 2024 (OFFICIAL) the same 13 and 15 against 28; Nov 2024 13 and 15 against 29; Mar 2026 (OFFICIAL) 13 and 15 against 29. Under the 2011 map: Nov 2018 15 and 16 against 31, Nov 2020 (OFFICIAL) 15 and 16 against 32. In every one of them TWO of the five districts report across the entire county bar at most one precinct, which leaves nothing for districts 1, 2 and 3 — and a whole-precinct plan requires the five districts' precinct counts to SUM to the county total, not for two of them to reach it alone. So Knox's precincts are split among its board districts, under both plans, and no whole-precinct dissolve can ever draw them. Knox joins Bureau, Cumberland, Douglas, Ford, Jackson and Piatt in the split-precinct class. THE PRECINCT LISTS THEMSELVES REMAIN UNAVAILABLE and that is a fact about the vendor, not the county: GBS publishes countywide totals with an \"N of N precincts reporting\" counter and no per-precinct breakdown anywhere, so the earlier note that this rested on COUNTS rather than LISTS cannot be resolved through this route at all — what replaced the missing lists is arithmetic repeated across six elections rather than one. The earlier remark that \"the 2022 page renders a different structure and could not be compared\" was wrong: it parses like the others.",
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
      "blocker": "No Lake County body publishes municipal officeholder names, re-checked 31 Jul 2026. The county's municipal data carries hall address, phone and website only; the Lake County Municipal League's pages repeat the same hall contact with no names, and its board page names only the League's own officers; the Council of Mayors membership list gives municipality names only. lakecountyil.gov itself now challenges automated visits, though not the kind of block that refuses outright. RE-MEASURED 2026-08-20, and the county's own site is now the obstacle rather than merely silent. www.lakecountyil.gov answers HTTP 403 with server: cloudflare and cf-mitigated: challenge — a Cloudflare MANAGED CHALLENGE ('Just a moment...'), not a flat deny, and served by the site's edge rather than by this environment's proxy, which passed the connection through. The county's GIS is unaffected: maps.lakecountyil.gov answers 200, which is precisely why this app already carries village-hall contact for all 41 and no names — the layer works and the website does not. THE REGIONAL-DIRECTORY ROUTE THE WANTED LINE PROPOSES WAS TRIED AND THERE IS NOTHING TO FETCH: neither lcmil.org nor lakecountymunicipalleague.org resolves at all, so the DuPage-mayors shape has no Lake equivalent at those addresses. A challenge-gated site is a different ask from a silent one — it may answer a real browser, which is how DuPage's own directory is already handled in CI.",
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
      "summary": "Four LaSalle-county cities elect by ward. Only Mendota publishes boundaries as map data; La Salle, Peru and Earlville publish maps you can look at but not read.",
      "blocker": "Re-measured 2026-08-20, and the claim that Peru and Earlville publish nothing at all is FALSE \u2014 both publish ward maps, neither as data. PERU has a Ward Maps page carrying a separate map for each of its four wards, three as PDF and one as JPG; their file metadata dates them to 2012 ArcMap exports despite the page's 2020 label, and the city's codified ordinance still carries the ward boundaries as Code 1996 section 30.01 with no later amendment through the November 2025 supplement \u2014 so they are pre-2020-census and, as codified, pre-2010. EARLVILLE publishes a Ward Map page with two 2025 PDFs, and one of them is the most promising document in this record: a June 2025 Autodesk Civil 3D plot that is FULLY VECTOR, zero raster images, which is the one thing here a tracing route could work from. LA SALLE is unchanged \u2014 a single PNG on its city-profile page, though re-uploaded in January 2026, so it is a maintained picture rather than an abandoned one. The county's own server was re-enumerated (28 services): it carries corporate boundaries, county board districts, polling places and precincts, and no ward layer. The public catalogue still returns exactly one ward item for all four cities, Mendota's, whose four shapes were last edited 2022-12-16. Aldermen for all four cities remain in hand, two per ward.",
      "wanted": "Ward boundaries as map data from La Salle, Peru or Earlville \u2014 or, for Earlville, confirmation that its 2025 vector PDF is the adopted current plan, since a vector drawing is a tracing away from geometry. Peru's would need re-drawing regardless: its own code still describes wards adopted before the 2010 census."
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
      "blocker": "Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. No county website answered under the five domain patterns probed. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". CORRECTED 2026-08-09 by a web search, the step this record was written without. The line above claiming no county website answered is FALSE. lawrencecounty.illinois.gov answers 200 with a /boards section. The systematic failure: the probe permuted the county's NAME, while the answer was already in this repo — data/app/il-county-clerks.json carries each Clerk's e-mail, and for 9 of the 14 counties recorded this way the CLERK'S E-MAIL DOMAIN IS THE COUNTY'S WEB DOMAIN. This project was e-mailing these counties at those very domains on 2026-08-05 while telling readers the counties had no website. BALLOT ROUTE CHECKED AND CLOSED 2026-08-20: il-lawrence.pollresults.net returns the vendor's generic 7,583-byte shell (4 electionData blocks) rather than a carried county's payload, and Lawrence appears on neither the GBS nor the platinumelectionresults county list. So the certified-return route that determined the form for Cumberland, Johnson, Perry, Hardin and Wayne without anyone replying is unavailable here, and the form stays undetermined. The clerk's own mail domain (lawrencecounty.illinois.gov) is the remaining lead. CORRECTED 2026-08-20 — THE 'NO WEBSITE' FINDING ABOVE IS FALSE, and it was false the day it was written. The pass-13 probe permuted the county's NAME across five domain patterns; the county's actual domain was already in this repo, in data/app/il-county-clerks.json, as the host of its Clerk's own e-mail address. That is the identical systematic failure Johnson's record diagnosed on 2026-08-09 and it was never swept across the other counties. Probing every frontier county's clerk-e-mail domain instead reaches a live site in EIGHTEEN of the thirty-one, several of them at hostnames no name permutation would produce (piatt.gov, bureaucounty-il.gov, hancockcounty-il.gov, champaigncountyclerkil.gov). For Lawrence the site is https://www.lawrencecounty.illinois.gov/ (57 KB), whose homepage links a County Board Meeting page. Thin, but real, and it is the first place this county's board form can be asked of rather than guessed.",
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
      "blocker": "Re-checked 31 Jul 2026 and half-overturned: the 2022-2032 map WAS adopted. Ordinance O-2021.06, passed 18-0 on 9 Nov 2021, is readable on the county's code site, and the clerk's Map Room publishes readable maps of all nine districts. But the precinct data still carries no district field, so boundaries would have to be built by combining townships as the ordinance describes, with Cahokia and Shipman split along the published 2005-2021 precinct lines its amendments are written in. THE MEMBER-LIST HALF OF THIS RECORD IS ANSWERED as of 2026-08-20, and it is only geometry that is still missing. The clerk's directory turned out to be readable after all — its page is empty and fills itself from a REST service beside the CMS, whose address a browser capture supplied — and that service publishes all eighteen seats by district (nine districts, two each), every one with the year it is next on the ballot, plus the board CHAIR by name (Larry Schmidt, who also holds a District 5 seat) and the six countywide officers. Two seats carry the county's asterisk for 'appointed to fill an unexpired term'. Nothing of that is shipped yet: with no district geometry there is no county-board dispatch entry for it to ride, and Macoupin elects by district, so its members cannot ride the at-large County card either. The list is available the moment the boundary is.",
      "wanted": "District boundaries, or a table pairing each precinct with its district — or acceptance of the township-plus-split build the adopted ordinance now supports. The current member list is no longer part of the ask: scripts/macoupin_municipal_officials_scraper.py already reads the service that carries it, and the same call returns the board."
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
      "blocker": "Re-measured 2026-08-20, and the county-side claims hold to the number: the data portal still carries exactly 61 assets whose only boundaries are precincts and school districts, the clerk's Map Room still publishes county-board, legislative, township and precinct maps and not one municipal ward map, and the downloadable elected-officials directory is still frozen at 3 November 2015 \u2014 it is that snapshot which establishes all eight cities as ward-electing. TWO CITY-SIDE FINDINGS CHANGE THE SAMPLED CLAIM. CARLINVILLE publishes its full city code as a single posted PDF, and its Article V carries COMPLETE WRITTEN BOUNDARY DESCRIPTIONS for all four wards, street by street \u2014 not map data, but a described boundary, which is a different class of finding from \"publishes none\" and the class this project has built from before. Its vintage is decisive and negative: the closing citation is an ordinance of 1 October 2012, the 2010-census redraw, carried into the 2022 code revision with no post-2020 amendment. GILLESPIE publishes a current aldermen-by-ward roster on its own council page, which answers the officeholder half of this record for one of the eight cities without touching the 2015 snapshot. A DECOY TO NAME: the catalogue's one \"Voting Wards\" layer for these city names belongs to STAUNTON, VIRGINIA \u2014 its own description says that city elects at large, its population column is from 2000, and its projection is Virginia State Plane. One city's site rate-limited this pass and answered on a third try after backing off, which may have been caused by the probing itself rather than by any block. THE DIRECTORY HALF OF THIS RECORD CLOSED THE SAME DAY: the clerk's browser-only directory was read at its source (see macoupin_municipal_officials_scraper.py), and it names all 53 sitting aldermen across all 28 wards of all eight cities \u2014 not Gillespie alone \u2014 each with the year the seat is next on the ballot. Those names now ship on the Municipality card. What is still missing is the geometry, and only the geometry: a reader can be told who represents Ward 3 of Staunton but not shown where Ward 3 is.",
      "wanted": "Ward boundaries as map data for any of the eight. The 2015 snapshot is no longer the roster of record \u2014 the clerk's live directory supplies every ward seat \u2014 so this record is now geometry alone. Carlinville's written descriptions could be built from as they stand, but they define the pre-2020 wards, so what that city actually needs is confirmation of whether it redrew after the 2020 census or kept these lines \u2014 the one-sentence answer that settled Rock Island."
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
      "id": "marion-county-board-districts",
      "concept": "County board districts",
      "area": "Marion County",
      "counties": [
        "marion"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Marion's board districts are composed by its own certified returns \u2014 but six census voting districts cannot be placed, because Centralia and Salem are split across three districts each.",
      "blocker": "MEASURED 2026-08-20, in the sweep of the platinum results vendor that shipped Franklin and Clinton, and this county is the sweep's honest no. Marion is carried at platinumelectionresults.com (county 18), and its per-precinct pages settle the board's form and composition completely: the 2024 General and the 2026 General Primary each carry a numbered 'FOR COUNTY BOARD DISTRICT n' contest in all 37 of the county's precincts, partitioning them 10/7/7/7/6 with every precinct claimed exactly once. Nothing is missing on the elections side. THE FABRIC IS WHERE IT FAILS. Census 2020 carries 48 Marion voting districts against the 37 precincts the county runs today, and eleven of them have no same-named county precinct. Four merges are nameable (ALMA, KINMUNDY, ODIN and PATOKA each merged a numbered pair). The other seven are not, and six of those seven are fatal: CENTRALIA 2, 8, 10, 16 and 18 and SALEM 3 belong to base names that the board plan SPLITS \u2014 Centralia's precincts sit in districts 3, 4 and 5, Salem's in 1, 2 and 3 \u2014 so no name can say which district those census units belong to, and guessing would move a district line through a city. This is the exact test Clinton passes on the same afternoon: Clinton's one unnameable merge (Brookside) sits entirely inside a single district, so it cannot move a line, and Clinton shipped.",
      "wanted": "Either the county's own board-district boundary as map data, or which Census 2020 voting districts make up each of the county's current Centralia and Salem precincts. The elections half of this county is already answered and needs nothing further \u2014 the composition, the district numbers and the precinct lists are all published in the Clerk's certified returns."
    },
    {
      "id": "jackson-county-board-districts",
      "concept": "County board districts",
      "area": "Jackson County",
      "counties": [
        "jackson"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Jackson publishes its 14 board members, its 7 districts, 56 precinct maps and certified canvasses back to 1996 — and its districts still cannot be drawn, because three precincts are split down the middle.",
      "blocker": "FIRST RECORD FOR THIS COUNTY, 2026-08-21. Jackson had no gap entry at all until now, which was itself the finding: at roughly 52,000 people (Carbondale, Murphysboro, SIU) it is the largest unserved county on the frontier after Champaign and Vermilion, and it went unrecorded because the pass-13 sweep never reached its website. jacksoncounty-il.gov answers HTTP 200 and always did — it is the domain in the County Clerk's own record in data/app/il-county-clerks.json, and probing THAT rather than permuting the county's name is what reached it, the same correction Cumberland forced on 2026-08-20. THE BOARD'S FORM AND ROSTER ARE BOTH ANSWERED: the county's own board page states \"fourteen members that are elected from seven districts\" and lists all fourteen by district with a contact page each, chaired by C.J. Calandro with Tamiko Mueller as vice chair. So this is a GEOMETRY ask, not a roster one, and the county even publishes a \"Board District Map (PDF)\" — a vector export dated 7/26/2022 whose text reads cleanly, drawn as \"County Districts and Townships\". THE CANVASS ROUTE IS OPEN AND THEN CLOSES, and this is the measurement worth keeping. The Clerk publishes machine-readable CANVASS RESULTS marked Official — the 5 Nov 2024 General runs one page per district, listing for each contest exactly the precincts that voted in it, which is precisely the input EXPANSION_GUIDE §2.5.1's canvass route needs. Reading all seven pages against the county's own 56-name precinct list gives 9/11/9/7/9/7/6 precincts, and 53 of the 56 fall in exactly one district. THREE DO NOT, and the canvass says so in the county's own numbers rather than by inference: CARBONDALE 24 appears under District 5 with 609 registered voters and under District 6 with 98; CARBONDALE 21 under District 6 with 600 and District 7 with 282; MURPHYSBORO 4 under District 3 with 166 and District 5 with 391. A precinct reported twice with its registration divided between two districts is the county stating that the precinct straddles the line. So no whole-precinct dissolve can draw Jackson's seven districts, and Jackson joins Bureau, Cumberland, Douglas, Ford, Knox and Piatt in the split-precinct class. Nothing was built. One parse caution for whoever returns: BRADLEY - CAMPBELL HILL wraps across two lines in the canvass and reads as missing unless the wrap is rejoined — it is in District 2.",
      "wanted": "The seven board districts as map data — from the county GIS that produced the 7/26/2022 district map (the north arrow and styling are ArcGIS output, so a layer exists somewhere), or from the Clerk as election authority. Failing that, the district assignment of the split halves of Carbondale 21, Carbondale 24 and Murphysboro 4, which is the only thing standing between the certified canvasses and a complete plan. NOT YET ASKED."
    },
    {
      "id": "massac-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Massac County",
      "counties": [
        "massac"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Massac is served through the County card — three at-large commissioners from the county's own page — but its 17 voting precincts are not shown: the county publishes no boundary of any kind.",
      "blocker": "Successor to massac-county-board, RETIRED 2026-08-21 when Massac shipped as the fleet's FOURTH ISLAND and its thirteenth at-large county. WHAT THE RETIRED RECORD GOT WRONG IS THE PART WORTH KEEPING. It said the county's site \"surfaced only clerk and assessment pages, no board\" — the site has a Commissioners page and always did, and what reached it was not a better crawl but a different question: probe the domain sitting in data/app/il-county-clerks.json (massaccountyil.gov) instead of permuting the county's NAME. That is the identical correction Cumberland forced on 2026-08-20, applied to the whole frontier at once, and it is why four other records were corrected in the same change. THE BOARD QUESTION IS CLOSED: the Clerk's own \"March 17, 2026 Primary Election Results\" cumulative report carries \"FOR COUNTY COMMISSIONER - REPUBLICAN PARTY - (Vote for one)\" over \"Precincts Counted 17 / Total 17 / 100.00%\" against all 11,265 registered voters, with no district string anywhere on the ballot; the countywide County Clerk and Regional Superintendent contests on the same pages report the identical 17-of-17 and 11,265, which is the control that makes the commissioner contest countywide in the same sense they are. A districted board reports only its own district's precincts — neighbouring Jackson's canvass shows 9 of its 56 for District 1. So Massac is a commission county electing three commissioners at large; there is no board geometry to seek and none should be invented. THAT REPORT IS MARKED \"Unofficial Results\" and is the only results document the county publishes; it is relied on for the FORM alone, which certification does not change — a canvass corrects counts, never the shape of the ballot — and the roster comes from the county's own commissioners page rather than from any return, per the Scott reasoning. WHAT IS NOT SETTLED is this record's subject. The 17 precincts are named nowhere as geometry: the county publishes no GIS, no precinct list and no polling-place map, and the pass-13 finding that no self-hosted ArcGIS answers under ten hostname patterns and that the ArcGIS Online catalogue names nothing county-keyed still stands, re-checked 2026-08-21. NO COMMISSIONER CONTACT DETAIL SHIPS EITHER, and that is the county's doing, not an omission here: its homepage prints a phone number for eight departments and none for the commissioners, and the commissioners' page carries no address, phone or e-mail. The courthouse address on the County Clerk's record is the CLERK's office and is not asserted as theirs.",
      "wanted": "The 17 precinct boundaries in any form — a shapefile, or a paper map scanned into a reply (the Stephenson route) — or the Clerk's word that they exist only on paper, which would convert this to a closed route the way Edwards' record closed. A certified canvass would also be welcome in place of the unofficial cumulative report the board form currently rests on, and contact details for the three commissioners would fill the one thing their card rows are missing. NOT YET ASKED: Massac shipped without an e-mail being sent, so every line here is an open ask to County Clerk Hailey Miles."
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
      "id": "momence-ward-geometry",
      "concept": "City council district",
      "area": "Momence",
      "counties": [
        "kankakee"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Momence elects eight alderpersons across four wards, mapped only on a 2017 image.",
      "blocker": "Checked 31 Jul 2026: the city's own ward map page serves a single image last changed on 30 Oct 2017, before the census. No Momence ward data exists in any public map catalogue, and the county's mapping carries no municipal wards. The per-ward member list is on the city's own pages. RE-CHECKED 2026-08-20: momence.net answers 200 but is a 9KB site that surfaces NO ward, council, alderman, map or GIS link at all, so there is nothing city-published to supersede the 2017 image. The seats remain published elsewhere; the boundaries are not.",
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
      "id": "municipal-website-dead-ends",
      "concept": "Municipal website link",
      "area": "Morris, Calumet Park, Chatham and Rochester",
      "counties": [
        "grundy",
        "sangamon"
      ],
      "kind": "data-quality",
      "layer": "municipality",
      "summary": "Four municipality cards link a website that answers perfectly and shows nothing \u2014 a domain for sale, an empty page, and two unconfigured web servers.",
      "blocker": "Found 2026-08-20 while re-measuring Morris's ward record, then swept across every municipal website this app ships \u2014 all 406 distinct URLs \u2014 because one of these is never just one. Four answer HTTP 200 and serve nothing a reader wants: MORRIS (morrisil.com) returns 114 bytes whose entire content is a script redirecting to a GoDaddy domain-for-sale lander, and the city's real site is morrisil.org; CALUMET PARK (calumetparkvillage.org) returns 200 with a COMPLETELY EMPTY BODY, zero bytes; CHATHAM (chathamil.gov) and ROCHESTER (rochesteril.org) both return the default \"IIS Windows Server\" placeholder page that ships with an unconfigured web server. THIS IS THE ONE FAILURE A STATUS-CODE CHECK CANNOT SEE, and it is worth stating plainly because this project already runs a link gate: validate_card_links.py asks whether a URL answers, and all four answer flawlessly. The tell is CONTENT, and the cheap version of it is size \u2014 every one of the four came back under 1,200 bytes, against a real municipal front page that runs to tens of thousands, and the whole 406-URL sweep surfaced only these four, so the false-positive cost of that check is close to nothing. NONE OF THE FOUR ENTERED THE ROSTER BY ERROR: each was published as that municipality's website by the county source the builder reads \u2014 Grundy's own 2026 directory of officials still prints WWW.MORRISIL.COM on its Morris page \u2014 so the counties are citing them too, and the Tazewell rule says a county's published value is not overridden on this project's own initiative. (This record is tagged to Grundy and Sangamon only for a mechanical reason worth stating rather than hiding: the gaps builder requires every county it names to have a shipped county-outline file, and Cook's coverage is drawn from a different tiling, so no record can tag it. Calumet Park is in Cook and is named here in full.)",
      "wanted": "For Morris: the county directory updated to morrisil.org, or the city confirming the move, which would give the builder a source to correct the value against. For Calumet Park, Chatham and Rochester: each village's working address, from the village or from its county clerk. And one thing that is ours rather than a publisher's \u2014 a content check in the link gate, so the next parked domain is caught by CI instead of by somebody reading a ward record."
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
      "blocker": "Re-measured 2026-08-20 and every claim holds, with two datable additions. The county's mapping server was swept in full \u2014 97-plus services across 23 folders \u2014 and not one layer name contains \"ward\"; its county-website folder carries city LIMITS and no wards. The public catalogue returns nothing for Morris (its one near-hit is the City of Washington, Illinois). The city's own site refuses this client, and the refusal is the SITE's rather than this environment's \u2014 a Cloudflare challenge from the origin \u2014 so the 2021 ward image could not be re-tested and is not restated as current. WHAT IS NEW AND USEFUL: Ordinance 3977 is now datable. Its own text says it was adopted because \"the 2010 census \u2026 revealed numerical inequalities in population of the wards as currently drawn\", and the city code as codified through Ordinance 4705 of 2 February 2026 still cites 3977 and nothing later. So Morris HAS NOT REDISTRICTED SINCE THE 2020 CENSUS, and its 2013 lines are current law rather than superseded ones \u2014 which is a different judgement from the usual \"pre-redraw, will not ship\", and the same posture Rock Island's clerk confirmed in writing. The code also settles how to read a discrepancy: where the map and the written descriptions disagree, \"the word description shall prevail\". The clerk's directory still lists all eight aldermen by ward, in a booklet refreshed 5 August 2026. See also the separate morris-website-parked record: the city's domain has moved, and the one this project cites is now a parked for-sale page.",
      "wanted": "Morris's ward boundaries as map data, or Ordinance 3977's Group Exhibit A in a text form that can be read \u2014 the ordinance PDF is a scan, and its written descriptions are the controlling definition by the code's own tie-break rule, so a readable copy of those words would be enough to build from."
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
      "summary": "Byron and Polo both elect by ward. Byron publishes ward maps as scanned pictures, Polo publishes nothing, and neither city's boundaries exist as map data anywhere.",
      "blocker": "Re-measured 2026-08-20. The claim that neither city links a ward map \"not even a picture\" is FALSE FOR BYRON: cityofbyron.com carries a dedicated Ward Maps page linking five PDFs \u2014 a citywide map plus one per ward. They are pictures in the strict sense, carrying zero fonts, no extractable text and hundreds of embedded images apiece, so nothing can be traced from them as vector; their production metadata dates them to 30 November 2023, which is after the 2020 census, though NO adopting ordinance could be confirmed (Byron's code sits in a single-page-application code viewer whose ordinance interface this pass could not address), so the post-2020 reading rests on file-production evidence alone and not on a legal citation. POLO publishes nothing, re-verified across its whole sitemap: not a page, not a document, not a string. The county side is unchanged and was checked harder than before \u2014 the county GIS coordinator's 95 published items and a second county account's 647 were paged in full, and neither carries a ward layer; the county's GIS hostnames resolve to the county website rather than to any map server. The public catalogue returns nothing for either city. The clerk's yearbook still gives Byron seven aldermen across four wards and Polo six across three, both already shown.",
      "wanted": "Ward boundaries as map data from either city \u2014 or Byron's adopting ordinance, which would at least date its 2023 maps to a plan and say whether they are the post-2020 redraw they appear to be."
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
      "blocker": "Checked in the 31 Jul 2026 ward sweep: Waukegan and North Chicago now publish current ward data on their own accounts, and Lake Forest's wards ride the regional mapping consortium — all three are queued. Zion and Highwood elect at-large. Park City's 3 wards appear in no city, county or public map source. RE-CHECKED 2026-08-20: parkcityil.org answers 200 and links a city-clerk page for council meetings, but surfaces no ward map, ward list or GIS of any kind. Nothing city-published has appeared since this record was written.",
      "wanted": "Park City ward boundaries as map data."
    },
    {
      "id": "pass10-frontier-unasked",
      "concept": "County board districts",
      "area": "Hancock, Jackson, Marion and Warren counties",
      "counties": [
        "hancock",
        "jackson",
        "warren"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Two frontier counties have working websites but no map data anyone has found; none has been asked directly yet.",
      "blocker": "Checked 3 Aug 2026 in the pass-10 sweep. All answer normally on the web \u2014 Warren's board page even numbers four districts \u2014 but none publishes board district or precinct boundaries as map data anywhere that could be found: nothing in the state map catalogue, and no mapping service at any of the usual addresses. Marion is worth a note: the address the state publishes for its clerk does not exist, and the county is actually at marioncountyil.gov. What has NOT been done is the step that worked repeatedly this week, which is writing to the clerk and asking. Every one has a working e-mail address. THIS RECORD USED TO NAME FIVE COUNTIES. Jefferson left it on 6 Aug 2026 by being asked: its Clerk replied with a precinct shapefile the next day and the county is now served. That is the record's own prescription working on the first try, and it is the reason the remaining four are worth writing to rather than probing again. MEASURED 2026-08-20 against the election-results vendor, which is the route that has settled county after county since this record was written \u2014 and it is NOT available for any of the four. All eight hostnames answer HTTP 200 (il-hancock, il-jackson, il-marion and il-warren on both pollresults.net and accessliberty.com), which is exactly why this needed measuring rather than probing: THE VENDOR'S HOSTNAMES RESOLVE FOR ANY COUNTY NAME AND SERVE A GENERIC SHELL, so a 200 from one proves nothing at all. The tell is content, not status. A carried county returns its whole certified result set inline and an archive full of documents \u2014 Bond and Clark both return 34 electionData blocks and 57-58 KB past-election pages listing 60 downloadable canvasses. These four return a 7,720-byte template whose only electionData hits are unfilled Angular placeholders ({{electionData.MenuItem}}), and a past-elections page of 10.6 KB \u2014 byte-identical across all four counties \u2014 carrying ZERO download links. So the canvass route cannot answer these counties, which removes the cheapest remaining alternative to writing and strengthens rather than changes this record's own prescription.",
      "wanted": "MARION LEFT THIS RECORD on 2026-08-20 for one of its own \u2014 its returns route was measured and found insufficient, which is more than this record ever knew about it. WARREN LEFT THIS RECORD on 2026-08-21 by SHIPPING, and it never needed the letter this record prescribes \u2014 its own board page and precinct-map legend were reachable the whole time at the domain of its Clerk\u0027s e-mail. For each of the remaining two: whether the county's board districts and voting precincts exist as map data, and where. Asking the two clerks is the next move, not more searching — Jefferson proved it takes one e-mail."
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
      "summary": "Eight cities name their council members by ward. Six of them DO have ward boundaries \u2014 on a county server nobody searched, in a shapefile already sitting in this repo, or published since \u2014 and only Beardstown and Virginia have nothing.",
      "blocker": "Created by our own progress on 3 Aug 2026: the Henry, Cass and Peoria county clerk directories gave each alderman a ward number, so the Municipality card can say \"Alderman, Ward 2\" for these eight cities while the ward layer cannot say where the wards are. All eight were searched in the public map catalogue that day and none returned a ward layer. RE-MEASURED 2026-08-20, AND THE RECORD IS WRONG FOR SIX OF THE EIGHT \u2014 for a reason worth keeping: the 3 Aug pass searched ONE SURFACE, the ArcGIS Online catalogue, and generalised the miss to \"nobody publishes\". That catalogue does not index self-hosted county servers. PEORIA COUNTY PUBLISHES A WARDS LAYER ON ITS OWN SERVER \u2014 gis.peoriacounty.gov, the DP/Elections map service, layer 13 \u2014 carrying 13 polygons for exactly the record's three Peoria cities (Chillicothe 5, Elmwood 3, West Peoria 5, two of them wards drawn in two pieces), public, token-free, CORS-enabled to this site's own origin and serving GeoJSON. GALVA HAS BEEN PUBLISHED SINCE 2025-09-22, three weeks after this record was written, as a public ArcGIS Online feature service \u2014 owned by the city's consulting firm rather than the city, which is a provenance line a card would have to carry. AND COLONA, GENESEO AND GALVA'S WARD POLYGONS HAVE BEEN INSIDE THIS REPOSITORY SINCE 13 AUG: Henry County GIS e-mailed a voter-registration archive that contains a Wards shapefile (11 features, Galva 3 / Colona 4 / Geneseo 4), committed under data/source/raw/. The build log recorded that archive as \"available rather than shipped blind\" and added that no gap record asked for it \u2014 while THIS record had been asking for those three cities for ten days. Two documents in one repository, each describing the other's subject as absent; both corrected in the same change. BEARDSTOWN AND VIRGINIA ARE STILL EXACTLY AS RECORDED, and their blocker is sharper than a search miss: Cass County has no public GIS surface at all \u2014 its only mapping is a parcel viewer behind a Cloudflare challenge, the clerk's polling-place links point at a hostname with no DNS record, and there is no county map account \u2014 while neither city publishes a ward map in any format, not data, not PDF, not a picture. TWO CAVEATS FOR WHOEVER BUILDS THE SIX, because neither is hidden by shipping. NOTHING FOUND IS POST-2020-CENSUS: Peoria's layer is stamped Feb 2021 and its precinct column cites a precinct set the county has since retired, Henry's linework is 2012, Geneseo's own map cites Henry County GIS 2015 and 2010 census population, Colona's is the plan adopted in 2011, Chillicothe's own map is 2017 and West Peoria's 2006. No city publishes anything later, so the evidence says none of the six redrew \u2014 but that is an ABSENCE, and this project's own precedent (Rock Island's clerk writing \"the existing ward boundaries were retained after the 2020 census\") says one e-mail settles it properly. AND COVERAGE IS CLOSE BUT NOT EXACT, measured against each city's Census place polygon: West Peoria leaves about 8% of the city in no ward at all and Elmwood puts about 12% of its ward area outside the city limits \u2014 the two that need resolving before a card claims to answer everywhere in those cities.",
      "wanted": "For BEARDSTOWN and VIRGINIA: ward boundaries in any form, from the cities or from a Cass County that currently publishes no map surface at all. For the other six the geometry is in hand and what is missing is a date \u2014 each city's clerk confirming whether the wards were redrawn after the 2020 census or retained, which is the same one-sentence answer that settled Rock Island \u2014 plus a look at West Peoria's uncovered eighth and Elmwood's overhang before either ships."
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
      "blocker": "Checked 3 Aug 2026. Requests to perrycountyil.gov come back as a 168-byte holding response rather than any of the county's pages — the signature of a challenge screen sitting in front of the site, the same one this project has recorded in front of other county sites. Nothing about the county's board districts or precincts can be read while that is in place, and the state's map catalogue lists nothing for the county either. THE BLOCK IS REAL AND STILL IN PLACE — re-checked 2026-08-20, perrycountyil.gov answers HTTP 202 with 169 bytes, and 202 counts as unreachable here for the reason recorded fleet-wide: 'Accepted' is never a document, and it is what a captcha front returns. BUT THE SENTENCE ABOVE IS NOW TOO STRONG, because the county's board can be read WITHOUT its website. Perry's Clerk publishes certified results through results.gbsvote.com (l_id=283), whose archive runs back to 2016, and the board question falls out of it: the 8 Nov 2022 general carries TWO countywide commissioner contests — \"COUNTY COMMISSIONER\" (Jennifer Martin) and \"CO COMMISSIONER 2YR\" (Joseph W. Folden) — each reading '27 of 27 precincts reporting / Vote for ( 1 )', and the 2018, 2020 and 2024 canvasses repeat the pattern. That is a three-member commission elected AT LARGE in staggered terms, so there is no board geometry to seek. The portal also states the county's precinct count as 27. What remains behind the block is the sitting roster and any contact for it — returns name winners, not who holds the seat today. A FOURTH RESULTS VENDOR, found 2026-08-21 and recorded here because nobody had it: results.gbsvote.com (GBS). It is not the accessliberty/pollresults pair and not platinumelectionresults.com; it carries THIRTEEN Illinois counties — Cass, Cumberland, Fulton, Greene, Grundy, Jasper, Johnson, Knox, Morgan, Perry, Scott, Warren and Washington — of which FIVE are unserved (Cumberland, Jasper, Johnson, Knox, Perry). Each county page lists its election authority and an archive of result sets back to 2016 at /locations/county_results.asp?id=N, and it was reached from the county's own Elections page rather than by guessing a hostname. AND IT SETTLES THIS COUNTY'S BOARD FORM, which this record could not: PERRY IS ELECTED AT LARGE, on the commission form. Three certified elections agree and every one of them puts the contest across the WHOLE county — the 2020 General (COUNTY COMMISSIONER, 27 of 27 precincts, Vote for 1), the 2022 General (COUNTY COMMISSIONER and a CO COMMISSIONER 2YR unexpired term, both 27 of 27, Vote for 1) and the 2024 Primary (both parties' COUNTY COMMISSIONER contests, 27 of 27, Vote for 1). A contest that spans all 27 precincts is county-wide by construction, so there is NO DISTRICT GEOMETRY TO SEEK and none should be invented — this is the Monroe/Randolph shape. Per EXPANSION_GUIDE §2.5.1 that converts Perry from a geometry ask into a COUNTY-CARD ROSTER ask. What is still missing is only the sitting commissioners' names from a county source: the returns name who WON each contest, never who holds the seat today, and Perry's own site is BLOCKED rather than absent (it answers 202 with a holding page), so the county does publish a roster somewhere and asking for it is the honest route rather than deriving one from the returns.",
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
      "summary": "Quincy's 7 wards are on the map, but the city's website turns away automated visits, and the one city archive that is reachable names aldermen without ever saying which ward they hold.",
      "blocker": "Checked 2 Aug 2026 and re-measured 2026-08-20. quincyil.gov answers 403 Access Denied (370-386 bytes) from AkamaiGHost with Akamai's edgesuite reference \u2014 the same Granicus GovAccess-behind-Akamai stack as its county, and the same flat refusal rather than a puzzle a browser works through; its TLS chain verifies cleanly, so this is not the Coles missing-intermediate case. A REAL DOCUMENT PATH WAS TESTED, not just the front page: a council minutes PDF harvested from search denies too. WHAT IS NEW, AND THE REASON THIS RECORD NOW SAYS MORE THAN \"BLOCKED\": quincyil.granicus.com sits OUTSIDE the WAF and is a live, machine-readable archive \u2014 61 council meetings from May 2025 to Aug 2026, agendas as real text-layer PDFs, an RSS index, and minutes carrying a roll call. It was read, and it still cannot answer this gap. Across 49 agendas fetched, every aldermanic name appears incidentally (a committee appointment, a motion to table) and NOT ONE is paired with a ward; the minutes' roll call lists ten of the fourteen seats with no ward on any of them. The trap to name explicitly, because the next reader will hit it: agenda text does contain \"Ward 3\", \"Ward 4\", \"Wards 4 & 7\" \u2014 but those are the LOCATION OF THE AGENDA ITEM (a street closure, a parade route, a zoning case), not the speaking alderman's ward, and reading \"Ald. Sassen \u2026 Ward 4\" as a ward assignment is precisely the inference the honesty rules forbid. The two meetings that would settle it \u2014 the May 2025 post-election organizational meetings where oaths are administered by ward \u2014 are the only ones whose agendas the portal reports as not published. A SECOND TRAP, reproduced byte-for-byte and worth recording fleet-wide: one minutes link taken from Quincy's OWN archive returns HTTP 200 and a well-formed 3-page PDF that is the governing body of TOPEKA, KANSAS, served under a quincyil_-prefixed filename, identical md5 on two fetches. That is the AccessLiberty login-page-as-PDF class and worse, because what it hands you is a tidy roster of names paired with district numbers. Any Granicus reader must check that the document names the jurisdiction it asked for.",
      "wanted": "The council roster BY WARD from any source that permits automated reading \u2014 the city's site becoming reachable, the May 2025 organizational agendas being published, or an Adams County Clerk directory. Names alone are already reachable and are not enough: this layer answers \"which ward am I in\", so a name without a ward cannot ride it."
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
      "id": "richland-county-board-districts",
      "concept": "County board districts",
      "area": "Richland County",
      "counties": [
        "richland"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Richland publishes a seven-district board map, names a member for every district, and still cannot be drawn: the map is a picture, and its own certified returns count districts without ever listing them.",
      "blocker": "MEASURED IN FULL 2026-08-21, replacing a record that said no county website answered and that the board's form was undeterminable. Both of those are now false. THE SITE: richlandcounty.illinois.gov answers 200 (809 KB, the largest of the five frontier sites the clerk-domain sweep opened) and is the Clerk's own e-mail domain, which is the Cumberland correction again. THE FORM IS SETTLED, from the county's own certified Official Results and not from any structure table: the 5 Nov 2024 General carries 'FOR MEMBERS OF THE COUNTY BOARD DISTRICT 1 / 3 / 5 - (Vote for one)' and the 17 Mar 2026 General Primary carries DISTRICTS TWO, SIX and SEVEN on the Republican ballot and FOUR on the Democratic — seven single-member districts on a stagger, odd years then even. The county's own board page independently names one member per district for all seven, chaired by Morgan Henton. So this is a GEOMETRY ask and nothing else. WHAT THE COUNTY PUBLISHES AS A MAP IS A PICTURE. 'District Map' on the board page links Precinct-Map.pdf (May 2026): one page, ZERO extractable characters, a single raster image. It is a real seven-district map and legible in the countryside — DISTRICT 1 over Noble/Decker/Denver, DISTRICT 2 over Preston 1, Preston 2 and German, DISTRICT 3 over Claremont, Bonpas and the two Madisons — but Olney's core is where the lines actually cut, and there the labels do not survive: several precinct slivers carry unreadable names, and 'Olney Precinct 5' is a narrow strip that appears to straddle the District 4/5 area. Upscaling does not help, because the resolution is the source's. Reading composition off it would be guessing at exactly the points that decide a district line, which is the one output this pipeline must never produce. NOT TRACED, deliberately. THE CANVASSES COUNT BUT DO NOT LIST, the Knox shape. The 2024 report gives each district's precinct COUNT — District 1 = 4, District 3 = 4, District 5 = 2, against a county total of 21 precincts and 10,755 registered — and never names one. Those counts are consistent with a lawful whole-precinct plan (registration 1,491 / 1,474 / 1,530 against an ideal of about 1,536), and the map independently shows District 5 as exactly two Olney precincts, which is real corroboration — but three districts of seven, by count alone, cannot compose a county. A UNIT TRAP TO CARRY: the 2024 report counts PRECINCTS (21 of 21) and the 2026 report counts POLLING PLACES (14 of 14). The two are not the same denominator and a build that mixed them would mis-size every district. A NEW MEASUREMENT, 2026-08-21, AND IT POINTS AWAY FROM BUILDABILITY. ISBE's precinct-level archive (2026 General Primary) lists THIRTY reporting units for the RICHLAND authority. Stripping the trailing id reduces them to exactly TWENTY-ONE base precinct names — BONPAS, CLAREMONT, DECKER, DENVER, GERMAN, MADISON 1, MADISON 2, NOBLE 1, NOBLE 2, OLNEY 1-7 and 9-11, PRESTON 1, PRESTON 2 — which matches the county's own canvass count of 21 and makes that number three-way confirmed. NINE of the twenty-one carry TWO reporting units each: Bonpas, Madison 1, and Olney 3, 4, 5, 7, 9, 10 and 11. That is NOT a primary artifact, which was tested rather than assumed — every one of the thirty units carries both a Republican and a Democratic row, so the split is not by party ballot. On the Cumberland record this project reads sub-precinct reporting units as the signature of a district line running through a precinct, and if that reading holds here then nine of Richland's twenty-one precincts straddle district lines and no whole-precinct dissolve can ever draw this county. IT IS RECORDED AS STRONGLY SUGGESTIVE AND NOT AS PROVEN, because Cumberland's reading was corroborated there by its district contests over-summing (6+5+3 against 12 precincts) and Richland has no such corroboration: its only precinct-counted canvass gives three districts totalling 10 of 21, which contradicts nothing either way. THE DECISIVE TEST IS NAMED AND IS NOT AVAILABLE ONLINE: the even districts' PRECINCT counts, which the 2022 General would carry. If D2+D4+D6+D7 = 11 the plan is whole-precinct and the nine sub-units mean something else; if they sum to more, the county is measured shut. AND THE 2026 PRIMARY CANNOT SUBSTITUTE, which is now proven rather than merely warned about: it counts POLLING PLACES, and its four district figures (5+4+3+3 = 15) already exceed the county's fourteen polling places while three of the seven districts are not even on that ballot. Polling places are therefore SHARED between districts and can never test a precinct partition. THIS COUNTY IS ALSO THE COUNTER-EXAMPLE TO A TOOL THIS PROJECT ADOPTED THE SAME DAY. ISBE's statewide county-board structure table — introduced for Saline, and checked before use against Clay, Hancock, Lawrence and Adams, matching all four — gives RICHLAND as 'At-Large'. The county has drawn seven numbered districts since at least 2024 and elects from them. The table's metadata is from 2007 and it carries no revision date, so the likeliest reading is that Richland was at-large then and districted after a later redistricting; either way the operational rule is now proven rather than merely stated: THE TABLE IS EVIDENCE OF STRUCTURE AT AN UNKNOWN DATE AND NEVER OF CURRENCY, and it must not be the last word for any county. Saline's at-large finding does not rest on it — that was proven from Saline's own certified canvass, with the table as third-place corroboration — but this is why it was written that way.",
      "wanted": "Which precincts make up each of the seven districts — the redistricting ordinance's written description, a precinct-to-district table, or the map as data rather than as an image. Any one of those finishes the county, because everything else is already in hand: the form, the roster, the 21 precinct names and three districts' counts. Both places this record named as unread have now been read and neither holds it: the ordinance category publishes exactly one ordinance (commercial solar farms, 2022), site search returns nothing for redistricting, reapportionment or district boundaries, and the 1841-2021 minutes archive at gov.arcasearch.com is a session-based scanned-minutes viewer that no automated client can read. The county's own results archive begins at 2024, so the 2022 General — the one document that would carry the EVEN districts' precinct counts and settle the partition — is not online. Asking the Clerk for the precinct-to-district table is now the only open route. NOT YET ASKED."
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
      "id": "saline-precinct-geometry",
      "concept": "Voting precincts",
      "area": "Saline County",
      "counties": [
        "saline"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Saline is served through the County card — thirteen members elected countywide — but its 28 voting precincts are not shown: the county publishes a polling list and no boundary.",
      "blocker": "Successor to saline-county-board, RETIRED 2026-08-21 when Saline shipped as the 74th county and the fifteenth at-large one. THE BOARD QUESTION IS CLOSED, on three sources that agree. (1) The county's own certified canvass: its \"2026 Primary Results\" report, run 26 Mar 2026 and headed Official Results, carries \"FOR MEMBERS OF THE COUNTY BOARD - REPUBLICAN PARTY - (Vote for not more than seven)\" over \"Precincts Counted 28 / Total 28 / 100.00%\" against all 15,441 registered voters, with no district string anywhere on the contest; the Appellate Court contest on the same page reports the identical 28-of-28 and 15,441, which is the control that makes it countywide in the same sense. Both party ballots print the contest the same way, and seven seats of thirteen is the stagger. (2) The county's own board page names exactly thirteen members with no district labels. (3) ISBE's county-board structure table gives Saline as 13 members, At-Large, one district. THAT THIRD SOURCE WAS NOT TAKEN ON TRUST, and the check is worth keeping: its embedded metadata is from 2007 and it carries no revision date, so before it was used here it was verified against four counties whose current pages this project can read — Clay (14 single-member districts A-N), Hancock (5 districts of 3), Lawrence (7 single-member) and Adams (21 across 7 multi-member) — and it matches all four exactly. It is cited for STRUCTURE, never for currency, and no name was read from it. WHAT IS NOT SETTLED is this record's subject. The county's 28 precincts are named nowhere as geometry: the Clerk's elections page publishes a polling list, early-voting schedule and results PDFs, and no boundary of any kind. The pass-13 finding that no self-hosted ArcGIS answers under ten hostname patterns and that the ArcGIS Online catalogue names nothing county-keyed still stands. ONE ROUTE IS RECORDED AS UNTRIED rather than closed: ISBE's precinct-level results archive covers all 102 counties and would supply Saline's 28 precinct NAMES, which is the input a census-fabric dissolve needs — but names alone are not boundaries, and whether the Census 2020 voting-district fabric still matches those 28 has not been measured. HOW THE COUNTY WAS REACHED, because it generalises: this record used to say no county website answered under the five domain patterns probed. That was false. salinecounty.illinois.gov answers 200 and is the Clerk's own e-mail domain, sitting in data/app/il-county-clerks.json all along — the Cumberland correction, and the reason four other frontier records were corrected in the same sweep. The earlier note that the probe rejected salinecounty.org as Saline County ARKANSAS stands and was never the obstacle.",
      "wanted": "The 28 precinct boundaries in any form — a shapefile, a GIS layer, or a paper map scanned into a reply — or the Clerk's word that they exist only on paper, which would convert this to a closed route the way Edwards' record closed. Failing that, a measurement of whether Census 2020's Saline voting districts still match the county's 28 current precinct names (the Jasper test), which would say whether a dissolve is even possible. Per-member contact details would also fill the one thing the card rows lack; the county publishes a board office address and phone and nothing per member."
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
      "blocker": "Checked 3 Aug 2026. Vermilion is about 74,000 people, the biggest county adjacent to the served area, and none of its geography is on the site. The state's election directory gives the clerk an address at vercountyil.gov. That domain exists, but it refuses secure connections and, over an ordinary one, forwards visitors to Google — it is parked, not a county website. Several likely alternatives were tried and none exists. This is the same trap McDonough set: an e-mail address at a domain that hosts nothing. McDonough was solved by asking its clerk, who named a website no amount of guessing would have found. SO WAS THIS ONE, and the record predicted its own solution: ASKED 5 Aug 2026, ANSWERED THE SAME DAY by Chief Deputy County Clerk and Supervisor of Elections Carrie Wilson — the county's website is vercounty.org, and the maps her office publishes are at vercounty.org/county-clerk/voter-maps/. (Seal permissions, separately, go to Jennifer Jenkins in the County Board office, jjenkins@vercounty.org.) THE METHOD LESSON IS IN THE HOSTNAME: \"ver\" is an ABBREVIATION of Vermilion, so no ladder built from the county slug — vermilioncountyil.gov, vermilioncounty.org, co.vermilion.il.us — could ever have reached it, which is why two passes of searching failed where one question succeeded. Neither the site nor the Archive is reachable from this project's network, so what the voter-maps page actually carries is still unmeasured. THE FORMAT QUESTION IS NOW ANSWERED, AND THE ANSWER IS NO: asked on 5 Aug whether those maps exist as data, Wilson replied the same evening — \"Those are the only maps we offer, our county does not have shapefiles or GIS layers for precinct look ups. There is a precinct finder on the Illinois State Board of Elections site voters may utilize or they may call our office.\" That is a refusal from the right desk, which this ledger treats as a finding rather than a dead end: it converts an inferred blocker into a stated one, and it means no amount of further searching of the county's own publications will produce geometry. Read exactly, her sentence is explicit for PRECINCTS and covers board districts by implication (\"the only maps we offer\"), so it settles what the CLERK holds; a county GIS or assessor's desk, if Vermilion has one, is a different office and was not asked. The lookup she named — ova.elections.il.gov/PollingPlaceLookup.aspx — was measured before being recorded and is NOT a data lead: it is a per-address form (zip, then a street from a fixed dropdown, then a house number) that answers one voter at a time, holds no boundary, and offers no download.  MEASURED 2026-08-18 by the 34-county sweep of the `il-<county>.pollresults.net` / `il-<county>.accessliberty.com` election-results vendor (see the backlog entry and the Clark build log). That platform publishes each county's certified results as STRUCTURED DATA, naming which precincts vote in each board contest — which answers §2.5 step 2 outright and, where districts are unions of whole precincts AND the Census 2020 VTD fabric still matches the county's precinct names (the Jasper test), supplies the composition too. FOR VERMILION THE ANSWER IS NO, AND IT IS THE CLEAREST FABRIC FAILURE in the sweep. The county's certified 2026 General Primary reports 38 precincts; the Census 2020 voting-district fabric carries EIGHTY-FOUR, with Danville alone contributing a dozen the county no longer runs. Vermilion consolidated its precincts wholesale after the census, so census geometry is not its fabric and no dissolve of it could answer here — and two of its precincts (Middlefork, Newell 1) are split between districts besides. Its results DID settle the form: eight board districts electing one or two members each, plus a separate three-district Board of Review.",
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
      "blocker": "MEASURED AGAIN 2026-08-20 AND ONE HALF OF THE ASK IS ANSWERED. Probed 4 Aug 2026 in the pass-13 detached-counties sweep: no self-hosted ArcGIS under ten hostname patterns across two service roots, and the ArcGIS Online catalogue names nothing county-keyed for it. The county site (waynecountyil.gov) is real: a Wayne County Board page, a Voting and Elections page, and an Online Mapping link into Sidwell's Portico portal — an ArcGIS-based PARCEL product whose configuration loads client-side; no election layer surfaced. waynecounty.org is a domain-for-sale page, a decoy. Whether the board is districted or elected county-wide was not determinable in this pass — determine it from a certified election document (EXPANSION_GUIDE §2.5 step 2) before any build: an at-large answer makes this a roster ask (the tranche-5 County-card path), not a geometry ask.  NOT YET ASKED: this records what the pass-13 probe could see, which Ogle proved on 2026-08-03 is a different question from what the county will send on request — its precinct shapefile arrived by return e-mail from a gap that read exactly like this one. See \"The ask ledger\". ANSWERED 2026-08-20 WITHOUT ASKING, from two sources that corroborate each other and disagree in a way worth recording. FORM SETTLED — DISTRICTED, seven districts of TWO members each. The county's own Wayne County Board page publishes the composition outright: DISTRICT 1 Berry, Garden Hill, Keith, Orchard, Indian Prairie, Hickory Hill (Daryl Hargrave Chairman, Quinton Greenwalt); 2 Mt. Erie, Bedford, Elm River, Massillon, Zif (Randy Hedrick, Greg Keyser); 3 Lamard 1-2, Jasper 1-2 (Brandon Bittles, Eddie Barbre); 4 Arrington, Four Mile, Orel (Cody Ehrhart, Steve Manning); 5 Big Mound 1-2, Barnhill (Matt Shreve, T.J. Vaughan); 6 Grover, Rider (Vern Hutson Sr., Bill Bruce); 7 Merriam, Golden Gate (Gene Kollak Vice Chairman, Steve Troyer). INDEPENDENTLY DERIVED FROM THE BALLOTS, via platinumelectionresults.com (Wayne is county/14 — see the third-vendor entry): all 27 precinct pages for the 2024 General were fetched and grouped by which board candidate each precinct actually voted on. They partition all 27 exactly once, into seven groups. SIX OF THE SEVEN MATCH THE COUNTY'S PAGE PRECISELY. THE SEVENTH IS THE FINDING: the county's page lists seven districts totalling only 25 precincts, and the two it omits — FAIRFIELD 1 and FAIRFIELD 2 — voted in District 7's contest on the certified 2024 ballot (Steve Troyer's, alongside Merriam and Golden Gate). So the page is incomplete rather than the ballots being wrong, and 25 against the county's 27 is the arithmetic that says so. District 5's group is the one that returned NO CANDIDATE in 2024 — its seat was on the ballot with nobody filed, which is why the ballot route names six people and the page names fourteen. THE FABRIC PASSES: Census 2020 carries exactly 27 Wayne voting districts summing to the county's exact 16,179, and all 27 current precinct names map onto them (Massilon/Massillon and Goldengate/Golden Gate are spelling variants between the two sources, not different places). WHY THIS IS NOT YET A BUILD, and the reason is population rather than provenance. Composed against a 2,311 ideal the districts run D1 2,572 (+11.3%), D2 1,895 (-18.0%), D3 3,060 (+32.4%), D4 2,229 (-3.6%), D5 2,387 (+3.3%), D6 1,863 (-19.4%), D7 2,173 (-6.0%) — a spread of about 52 points, and D3 EXCEEDS THE 30% CEILING this repo's own Mercer builder uses. That ceiling exists to catch a mis-assignment, and here it fires on a district whose composition BOTH sources agree on exactly, so the likely reading is that the county's plan really is this unbalanced rather than that the derivation slipped. That is a fact about Wayne and not a defect to smooth: a builder must either establish why (a plan drawn on older figures, or one never redrawn after 2020) and accept it on the record the way Mercer's -14.6% was accepted, or find the county's own adopted map. Nothing ships until that is stated rather than assumed.",
      "wanted": "ONE THING, narrowed 2026-08-20. The Fairfield question is CLOSED: the county\u0027s own certified 2026 General Primary carries a numbered \u0027FOR COUNTY BOARD DISTRICT 7\u0027 contest on the ballots of Fairfield 1 and Fairfield 2 themselves, which is the county stating the assignment rather than this project inferring it from candidate names. The full seven-district composition is confirmed too, from three certified elections that agree exactly and partition all 27 precincts once each \u2014 including District 6 (Grover, Rider), which the 2026 primary omits because that seat was not on the ballot. WHAT REMAINS IS THE POPULATION QUESTION, and it is now measured rather than suspected: against Census 2020 the seven districts run 1,863 to 3,060 against a 2,311 ideal \u2014 worst deviation 32.4%, District 3 some 64% larger than District 6. That is beyond the 30% ceiling this project\u0027s own dissolve guard enforces, and well beyond every plan it has shipped (Clark 21.1%, Mercer 14.6%, Edgar 11.8%, Franklin 11.4%, Clinton 7.3%). So the county is NOT built, and the single question left is whether this plan post-dates the 2020 census and, if so, what figures it was drawn on. A sentence from the Clerk, or the adopted map, settles it."
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
      "summary": "Whiteside's 11 municipalities name a mayor and a clerk with contact \u2014 what none of them names is a council or village board, because the county's yearbook does not carry one.",
      "blocker": "CORRECTED 2026-08-20, and the correction is against this repository's own shipped data rather than against the world. This record said Whiteside's municipalities \"show a name and a link only\" and that \"the Clerk publishes no yearbook or municipal directory\". Both are false, and were already false when written: the Clerk publishes a 68-page County Yearbook whose Mayors of Whiteside County and City Clerks sections cover all eleven municipalities with name, address and phone; this project's own Whiteside scraper reads exactly that document; and the shipped roster carries a mayor, a clerk, an office address and a phone for all eleven. A gap record describing an absence the app had already filled is the inverse of the usual failure and just as misleading, since it invites someone to go find what is already here. THE REAL REMAINING GAP IS NARROWER AND DIFFERENT: no governing BODY. The yearbook names no aldermen and no village trustees anywhere in its 68 pages \u2014 a search for either term returns nothing outside county contexts \u2014 so what is missing for all eleven is the council or board, not the officers. The county's map data is unchanged and re-verified: its elected-representatives service still stops at the county board and the state and federal offices, and its electoral-districts table names eighteen offices without a municipal one among them. The regional council still publishes no member roster. ONE FIND WORTH RECORDING FROM THE SAME ACCOUNT, though it belongs to a different concept: the county publishes a Wards layer carrying 22 municipal ward polygons across six of its cities. It is not shippable \u2014 its officeholder column is null on every row and its last data edit is November 2019, so the geometry is pre-2020-census under this project's redraw rule \u2014 but it is real ward map data on a county's own account, and worth knowing about before anyone records Whiteside's cities as publishing nothing.",
      "wanted": "The eleven municipalities' councils and village boards \u2014 which the county yearbook does not carry, so this needs the cities' own pages or a different county document. The mayors and clerks are already shipped and are not what is missing."
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
| Electoral precinct / ballot sub-unit | SHIPPED `ward-precinct` + `county-precinct` (consolidated CountyDispatch: suburban Cook current map 1,430 — Cook-outside-Chicago only, city precincts are the BOE ward-precinct layer — + Will 2022 map 310 + DuPage 2024 map 600 + Lake current map 431 + Kane current map 292 + McHenry current map 223 + Kendall current map 78 w/ the county's own polling-place assignment per precinct — every metro county covered — plus the sixteen expansion counties: LaSalle 119 (polling joined 119/119) + Kankakee 59 + Boone 37 (polling on the feature) + Grundy 40 (polling joined 38/40) + Macoupin 45 (the county's own Socrata portal — the 2022-2032 fabric ab79-cnsh; polling joined 45/45 from its sibling polling dataset by deterministic label expansion, 2026-08-02 — the pass-4 note of 105 was the superseded map) + Madison 191 (polling joined 191/191, the fleet's cleanest) + St. Clair 150 (polling is a recorded gap) + Winnebago 94 (county-clerk jurisdiction only — Rockford runs its own election commission, a recorded gap) + DeKalb 69 + Ogle 51 (the county GIS Coordinator's shapefile, sent on request; the Clerk supplied the other half of the answer — how retired Forreston 3 was absorbed — without which the 2020 fabric would have shipped a precinct that no longer exists) + Lee 46 + Whiteside 60 (polling joined 56/60 from the county's layer; the last four filled from two locations the Clerk supplied with addresses, which the county does not publish — all 60 now show a polling place and an address) + Rock Island 120 + McLean 141 (polling joined 141/141) + Logan 29 (the clerk's HTML polling table shipped as a same-origin file, joined 29/29) + Sangamon 166 (polling joined 165/166) + Carroll 22 (TIGERweb Census-2020 VTDs live — the county did not re-precinct; the clerk's polling notice shipped as a same-origin file, 22/22) + Woodford 37 (TCRPC's election service, polling joined 37/37 on the numeric polling reference, 2026-08-02) + Macon 64 (polling joined 64/64 to 29 locations — recorded here 2026-08-04 with the matrix row it was omitted from at ship time) + Effingham 38 (the first island — polling joined 38/38 to 24 locations by facilityid, every location with a full address) + Hamilton 16 (the second island, from the GIS the Clerk pointed to in a four-minute reply; the layer's 17th row is a null-named byte-for-byte duplicate of Dahlgren 1, dropped in the loader; polling joined 16/16 to 13 locations from the Clerk's statutory 3/17/2026 General Primary notice on the county's post-migration website, shipped as a same-origin file with the card row election-labelled — the notice settled the Dahlgren #1/#2 pairing two ~0.3 mi-coarse georeferencing instruments could not, 2026-08-11) + Coles 44 (live from the county's own public ArcGIS org, 2026-08-17 — READ THE LAYER ID: layer 0 of that service is "Polling Places", 24 POINT features, and the precinct polygons are layer 1. Expanding the 24 points' comma-separated `Precinct` lists ("CH 1, 12") yields exactly the 44 precinct names once each, and every polygon independently names its own building in `PollingLocation` — two surfaces agreeing 44/44 — so the address joins by name in the loader and the card also carries the county board district by spatial join. Tiling measured: 0.021% of the county uncovered and 0.023% spill against TIGER, 19 hairline overlap pairs totalling 2,029 m²) + Clark 23 (Census 2020 voting districts, 2026-08-18 — and they ARE the county's own fabric by measurement, not by assumption: names match the county's 23/23, POP100 sums to its exact 15,455, and its 2022 General, 2024 General and 2026 General Primary returns all tabulate the same 23 names, so nothing moved either side of the census. This is the test JASPER FAILS — five census Wade voting districts against four current county precincts — which is why that county is still unbuilt. The board district rides ON the feature, the composition being whole-precinct. NO POLLING PLACE: the only list the county publishes is titled "Polling places and addresses 11-18", the November 2018 election, and shipping an eight-year-old address is the harm these rules exist to prevent — gap clark-precinct-polling) + Crawford 24 and Mercer 24 (Census 2020 voting districts, 2026-08-18 — each county's own fabric by measurement: names matching 24/24 and POP100 summing to 18,679 and 15,699 respectively, their exact 2020 counts. The board district rides ON the feature, the composition being whole-precinct. NO POLLING PLACE in either: Crawford's polling list and both its archived Statements of Votes Cast are scans, and nothing Mercer publishes pairs precincts with buildings as data) + Edgar 31 (Census 2020 voting districts, 2026-08-18 — 29 of the 31 names match the county's own spelling character for character, POP100 sums to its exact 16,866, and the two that differ pair uniquely at 31 against 31: the census writes EMBARRASS 1 and KANSAS 1 where the county writes Embarrass and Kansas. Recorded as a RENAME in the builder rather than smoothed away, with both spellings shipped on the feature. The board district rides ON the feature. No polling place: the county publishes none as data) + Franklin 35 (Census 2020 voting districts, 2026-08-20 — 34 of the 35 names match the county's own spelling character for character, POP100 sums to its exact 37,804, and the one that differs pairs uniquely at 35 against 35: the census writes CAVE 1 where the county writes Cave, the vestigial-1 rule, shipped as a recorded rename with both spellings on the feature. The board district rides ON the feature, the composition being whole-precinct. No polling place: the county publishes no precinct-to-building pairing as data — its Elections page carries sample ballots and statutory notices only); Kane's card also gained the township name from the clerk's own prefix pairing and the election-labelled polling row, 292/292 — the pass-6 precinct tranche, 2026-08-02) | SHIPPED `election-district` (~4,200) | SHIPPED `election-precinct` (`jg6x-23ig`, 2022 map; subOf `supervisor-district`, polling-place lookup link) |
| County legislature / commissioner | SHIPPED `county-board` (consolidated CountyDispatch layer: Cook Commissioner 17 + Will 11 + DuPage 6 + Lake 19 + Kane 24 + McHenry 9 + Kendall 2 + LaSalle 29 (DERIVED — see below) + Kankakee 28 + Winnebago 20 + Livingston 3 + McLean 10 + Logan 6 + Sangamon 29 + Madison 26 + St. Clair 28 + DeKalb 12 + Ogle 8 + Stephenson 8 + Carroll 3 + Lee 4 + Whiteside 3 + Rock Island 19 + Woodford 3 (DERIVED — TIGER townships per adopted Ordinance 2020/21 #005; five members per district from a weekly directory scrape, 15/15 with phone and e-mail; no chair marked — elected from within the body, the directory doesn't say) + Boone 3 (RUNTIME-MERGED — the county GIS's three per-district layers, each pre-dissolved, merged and district-tagged at load time; four members per district from a weekly board-page scrape, 12/12 with phone, e-mail and term-expiry year; one Vice-Chairman tagged verbatim, no Chairman named) + Grundy 3 (DERIVED — the county's own precinct layer dissolved per the adopted 10/12/2021 map, the transcription proven by the map's printed populations to the person; six members per district from a weekly board-page scrape, 18/18 with party, since-year, committees, phone and e-mail; Chairman tagged from his own row) + Henry 2 (DERIVED — TIGER townships per adopted Ordinance 21-33, twelve whole townships per district, the composition proven by the adopted map's own two-census population table AND live Census POP100, all to the person; TEN members per district — the fleet's widest — from a weekly scrape of the county's own district-keyed directory, 20/20 with e-mail; no chair marked, so none is tagged) + Stark 2 (2 districts of FOUR, the smallest board here — boundary from the County Clerk's own Google My Maps, which is the county's entire GIS and which she confirmed current by e-mail; per-SEAT e-mail addresses, Chair and Vice-Chair badged) + Effingham 9 (the FIRST ISLAND, 2026-08-04 — single-member districts lettered A-I with the roster ON the district features: name, party, phone and e-mail read straight off the county's own live service, the McLean pattern with one seat and no scraper between the card and the county) + Jo Daviess 17 (PURCHASED, 2026-08-17 — the fleet's first bought boundary: 14 of the 17 single-member districts cut across precincts along roads, so no dissolve or tracing could draw them, and the county SELLS its GIS data; the county's own shapefile under Jo Daviess County GIS Digital Data License Agreement #008382, displayed under the county's written authorization, the raw file retained offline per the licence, the card crediting Jo Daviess County GIS per its Credits clause; roster weekly from the county's own board page — party and term on every seat, a direct phone and e-mail per member, one counted-never-named vacancy) + Coles 12 (2026-08-17 — single-member districts live from the county's own public ArcGIS org, GEOMETRY ONLY. The same layer carries Official/party/term/phone/email/Population columns and NONE of them is read: that table is a 2022-04-23 snapshot which names SIX members who have since left the board, still reads term "2022" for District 11, and whose populations sum to 53,873 — Coles's 2010 census count to the person, against a 2020 count of 46,863. So this is the anti-Effingham: the roster-on-the-boundary shape that looks identical and is false, and the roster comes from the county's board page weekly instead. The polygons themselves are current, proven two ways: they are exact unions of the county's own 2022 precincts, and their precinct composition matches 12/12 the composition the county's board page publishes today. No party, term or chair ships because the page publishes none; the board office's own address and phone ship once at board level, measured against the Treasurer's and Sheriff's pages to prove it is the board's office and not a switchboard + Clark 7 (DERIVED, 2026-08-18 — the first county in the fleet whose BOUNDARY comes out of election returns. Its Clerk answered the standing ask with "The County Board is elected by districts. I do not have maps available", which settles the form and refuses the geometry in one sentence; the districts are unions of WHOLE PRECINCTS, so the county's own certified canvasses describe them completely and the Census 2020 voting districts — matching the county's 23 precinct names 23/23, summing to its exact 15,455 — supply the polygons. The composition is witnessed three times: the 2022 General canvass carries all seven contests, the 2024 General re-tabulates 3/4/7 and the 2026 General Primary re-tabulates 1/2/5/6, so no district rests on one document. The ROSTER is the same canvasses, weekly: each member is whoever the county certified as elected in the most recent general election that seated their district, and the card renders that election rather than claiming a currency the returns cannot show. Party ships; no term or chair does, and NO per-member contact does — the county publishes phones and e-mails only inside that scan, where one of the seven addresses is unresolvable from the image, so the county switchboard stands for the board and the rest is a recorded gap. Populations run 1,923–2,674 against a 2,208 ideal, a 21.1% worst deviation that is the county's apportionment and is recorded, not smoothed) + Crawford 5 and Mercer 5 (DERIVED, 2026-08-18 — five districts of TWO members apiece in each county, dissolved from their Census 2020 voting districts per the composition their own CERTIFIED RESULTS publish as structured data. Neither came from a reply: a sweep of the `il-<county>.pollresults.net` results vendor found that each county's certified 2026 General Primary names which precincts vote in each district's contest, and in both counties those lists partition all 24 precincts exactly once with none split. A single certified election is accepted and SAID SO — unlike Clark nothing is transcribed here, because the precincts listed in a contest are the precincts it was on the ballot in. Both walked past a standing obstacle: Crawford's district layers exist and its Assessor maintains them, but their release sits with the county's MAPPING COMMITTEE; Mercer's only map is a 2021 SCAN that evidences the lines and supplies no data. Rosters weekly from each county's own board page — Crawford 10/10 with a county e-mail and its Chairman titled, Mercer 10/10 with party and term-expiry plus home town and the Chairman's phone — and the same run re-reads the composition from the Clerk's feed and fails if it moves, which is these counties' only automatic redistricting warning) + Edgar 7 (DERIVED, 2026-08-18 — seven single-member districts, and the first county the vendor sweep reached that meets Clark's TWO-WITNESSES-PER-DISTRICT standard in full: the Clerk's 2022 General canvass tabulates all seven over all 31 precincts, the 2024 General re-tabulates 1/6/7 and the 2026 General Primary 2/3/4/5/6. THE ROSTER IS THE COUNTY'S PAGE AND NOT THE RETURNS, and this county is the clearest argument for that split anywhere in the fleet — the 2022 and 2024 canvasses elected Phillip Ludington in District 6, the board page names Samantha McCarty, and the Clerk's own 2026 primary confirms her by carrying a '2-year unexpired term' contest for that seat. A mid-term appointment is exactly what a completed canvass cannot show. Party ships for all seven; no e-mail, phone, term or chairman does, because the page publishes none and its committees table's CHAIRMAN column is the chair of each committee. Read the domain twice: the roster is on edgarcountyillinois.COM and the county's .GOV links across to it) + Franklin 3 (DERIVED, 2026-08-20 — three districts of THREE members each, staggered, and the first county the fleet has reached through a THIRD results vendor: its Clerk publishes on platinumelectionresults.com, which serves eight Illinois counties and two still-unserved ones (Marion, Wayne). THREE CERTIFIED ELECTIONS AGREE EXACTLY, which is one better than Clark's standard: the 2024 General and the 2022 General each tabulate a board contest in every one of the county's 35 precincts and partition them 13/13/9, and the 2026 General Primary reproduces the same three sets while NAMING the districts in its contest headers — so the county members page's district key is corroborated rather than relied on. A SHORTCUT THAT LOOKED RIGHT AND WAS NOT is recorded with it: the vendor's precinct ids group 51xx/61xx/71xx, which reads exactly like a district key, and Browning 1 and 3 sit in District 1 while Browning 2 sits in District 2 — tested against the ballots, and it failed. THE ROSTER IS THE COUNTY'S PAGE, necessarily: three seats per district on staggered terms means any one canvass elected a third of the board. That page is a WP Table Builder GRID and is read by cell coordinate, because flattened it pairs every role with the WRONG member — column 0's role arrives before its own row's name, the Cumberland trap. Phone 8/9, one e-mail, and the role the county prints beside five members ship, the table distinguishing its committee chairs (named by committee) from the board's own Chairman and Vice Chairman; NO PARTY does, because the page publishes none and the canvasses would label only the third last on the ballot. Its Address column is every member's HOME address and is never read. Populations run 11,172–14,044 against a 12,601 ideal, an 11.4% worst deviation recorded, not smoothed + Clinton 5 (DERIVED, 2026-08-20 — five districts of THREE members each, and the SECOND county from the platinum vendor the same afternoon. The 2024 General and 2026 General Primary each carry a numbered contest in all 34 precincts (7/9/6/5/7) and the 2022 General names candidates whose districts key onto the county's own board page, so three certified elections agree from two directions. THIS IS A COMPOSED FABRIC, the Calhoun shape: census 2020 carries 39 Clinton voting districts against the 34 the county runs today, Irishtown/Lake/St Rose each having merged a numbered pair and Brookside gone five to three. THE BROOKSIDE MERGE IS NOT NAMEABLE AND CANNOT MATTER — all five of its voting districts sit in District 1, so no merge can move a district line — which is precisely the test MARION FAILS on the identical technique, its Centralia and Salem units spanning three districts each. NO PRECINCT LAYER SHIPS here for that same Brookside ambiguity: a precinct card would have to say which is which and nothing published does (gap clinton-precinct-geometry). The roster is the richest this route has met — phone, e-mail AND term-expiry year on all fifteen, Chairman and Vice Chairman badged by name match; two members whose photo sits inside the same tag as their name had to be recovered by walking every match rather than the first, which is how Kurt Schmitz was nearly lost with every count guard passing. Populations run 6,840–7,678 against a 7,380 ideal — 7.3% worst, THE TIGHTEST THIS ROUTE HAS PRODUCED + Warren 4 (DERIVED, 2026-08-21 — four districts seating 15 as 3/4/4/4, and THE FIRST COUNTY REACHED BY FIXING A PROBE rather than by asking or by finding a vendor: it sat in the pass-10 'frontier unasked' record whose prescribed next step was a letter, and its own site was reachable the whole time at the domain of its Clerk's e-mail. THE COMPOSITION IS A LEGEND, NOT A DERIVATION — the county's precinct map is a raster image with no vector linework, so nothing is traced from it, but its text layer carries a four-column table naming each district's precincts, which makes this a STRONGER source than Franklin's and Clinton's returns route where the same fact is inferred from which ballot a precinct voted. Both census merges are nameable AND district-confined (Roseville 1+2 in D4, Spring Grove-Alexis and -Gerlaw in D3), so the Clinton test passes twice over. The roster is the county's board page — 14 e-mails, 7 phones, a term year on every seat, the committees it lists, Chairman of the Board Mike Pearson badged — and it set TWO parser traps: the page writes members two ways, and matching only the obvious one drops two of fifteen INCLUDING THE CHAIRMAN while every district still looks full; then fixing that by searching backwards for a name started reading members' HOME ADDRESSES as their names. The county prints an address for every member and none is carried — the scraper drops them by construction and FAILS if it stops seeing them. Populations run 4,030–4,332 against a 4,209 ideal, 4.2% worst, taking the tightest-spread record off Clinton hours later. Its join also closed a doughnut round KNOX, the fleet's third enclave)))) districts — LaSalle REBUILT 2026-08-01 on derived geometry (its own board GIS is the superseded 2011-2021 map): the county's precinct layer dissolved per its 2024+2026 election canvasses, 11 split precincts drawn with their majority side and stated on the card, roster scraped weekly from the county directory with the countywide-elected Chairman (gap lasalle-board-districts-stale records what remains); absorbed the former `commissioner` / `will-county-board` / `dupage-county-board` layers, old permalink ids aliased; Lake's members + contact + office address ride live on the county's own boundary GIS, with Chair/Vice-Chair tags from a weekly directory scrape (name-match guarded); Kane's GIS carries member names while a weekly scrape of the county's SharePoint directory list adds party/office phone/email + the countywide-elected Chair; Kendall's members + Chairman and McHenry's members + countywide-elected Chairman — each with contact + profile links — join from hand-verified rosters of each county's own directory — those two counties block all automated fetch incl. the Archive's crawler, so their weekly scrape attempts feed standing tracking issues until the block lifts) | NO HONEST ANALOG¹ | NO HONEST ANALOG (folded into `supervisor-district`) |
| County property-tax appeals board (elected) | SHIPPED `ccbr` (commissioner roster scraped weekly from the Board's own site) | NO HONEST ANALOG² | NO HONEST ANALOG⁵ |
| State high-court electoral district | SHIPPED `il-supreme-court` | SHIPPED `judicial-district` (NY Supreme is trial-level, elected by district) | NO HONEST ANALOG⁶ |
| Trial/civil-court sub-district | SHIPPED `judicial-subcircuit` (consolidated CountyDispatch: Cook 20 — live from the county GIS, cross-validated against the enacted ilsenateredistricting.com shapefile, with the Circuit Court's 6 municipal districts + courthouses as a card row — + Will 12th-Circuit 5 + DuPage 18th-Circuit 7 + Lake 19th-Circuit 12 + Kane 16th-Circuit 4 (pre-built from the enacted shapefile — the county's services are permission-locked) + McHenry 22nd-Circuit 4 (pre-built — the county publishes no subcircuit service) + Winnebago 17th-Circuit 2 + Madison 3rd-Circuit 4 + Sangamon 7th-Circuit 7 (the three 2026-07-28 entries, pre-built from the same enacted archive; their coverage is the subcircuit geometry itself, so each circuit's secondary counties — Boone; Bond; Greene/Jersey/Macoupin/Morgan/Scott — answer too), all PA 102-0693; the app ships all nine circuits the act covers, and Macoupin — a 7th-Circuit secondary county — is answered by the Sangamon entry; every other served county's circuit (Kendall + DeKalb's 23rd, LaSalle + Grundy's 13th, Kankakee's 21st, Livingston/McLean/Logan/Woodford's 11th, St. Clair's 20th, Ogle/Lee/Stephenson/Carroll's 15th, Whiteside + Rock Island + Henry's 14th) received NO subcircuits under the act — structurally n/a, the layer hides there) | SHIPPED `municipal-court` (28) | NO HONEST ANALOG⁶ |
| District Attorney (districted) | n/a (Cook State's Attorney is one countywide office) | SHIPPED `district-attorney` (5 borough DAs) | NO HONEST ANALOG (one citywide DA)⁷ |
| Borough president / by-county executive | n/a | SHIPPED `borough-president` | n/a |
| Community district / board (appointed, labeled so) | n/a | SHIPPED `community-district` | n/a |
| Elected school board (districted) | SHIPPED `school-board` (ERSB) | NO HONEST ANALOG³ | NO HONEST ANALOG (at-large board)⁴ |
| Parent-elected education council | n/a | SHIPPED `cec` | n/a |
| Elected regional transit board | NO HONEST ANALOG⁸ | NO HONEST ANALOG⁸ | SHIPPED `bart-director` (9 districts, BART's own ArcGIS + hand-verified roster) |
| Municipal governing body (surfaced on the municipality-identity card) | SHIPPED on `municipality` — **623 municipalities across thirty-two counties**, with 580 heads of government + 2,980 board members incl. 742 ward/district seats + clerks/treasurers + hall contact, joined by Census place GEOID (weekly CI). Depth varies honestly by county: **full governing body** Cook 130 (incl. the Town of Cicero, which the Clerk files under the TWNSP township type — one coterminous town/township government, absent from the MUNIS list entirely, so ~85,000 residents had an identity-only card until 2026-08-19) / Will 31 (incl. the Village of Crete, whose flipbook entry loses its header to PDF-text extraction and is recovered from the orphaned block, its President from the county's certified 2025 canvass) / Madison 28 / Sangamon 26 / St. Clair 26 / Macoupin 26 / LaSalle 24 / Tazewell 16 / Rock Island 15 / Peoria 15 / Washington 14 / Henry 14 / Livingston 14 / DeKalb 14 / Ogle 13 / Logan 11 / Stephenson 11 / Winnebago 11 / Grundy 9 / Marshall 9 / Mason 8 / De Witt 7 / Boone 5 / Cass 5 / McLean 3 (its three ward-electing cities from their own pages — the county-wide source is a JS-locked Airtable interface), **head-level** McHenry 27 / Kane 23 / DuPage 23 / Whiteside 11 / Carroll 7 / Kendall 6, **contact-only** Lake 41 (publishes no names county-side). **Boone (2026-08-20) is the source that prints a RESIDENCE under almost every official** — 54 street-address lines in its municipal section, only the section headers being municipal offices — so its scraper takes name, office, ward, term, phone and e-mail and refuses address lines by construction, then proves on the BUILT payload that none survived; the Madison/Peoria rule made structural rather than filtered afterwards. It is also the first source whose EDITION is discovered from a link's text rather than its filename: the Clerk's page slug still says 2019 while it serves the 2026 book. Belvidere's ten ward seats are cross-checked name-for-name against the county's own `Belvidere_Wards` service (10/10) before the payload is written, and the one disagreement — Sandra Gramkowski's phone, transposed between the two sources — ships as no phone at all rather than as a coin-flip, discovered by comparison at build time so it retires itself the day either publisher fixes the digit. Cherry Valley and Loves Park are printed in Boone's booklet and deliberately not taken: both cross the county line, and Winnebago already publishes them more deeply (all ten of Loves Park's ward alderpersons against Boone's three citywide officers), so taking Boone's copies would settle a cross-county contest by list position rather than by evidence. The 2026-08-01 tranche (Grundy, Livingston, Logan, McLean, Sangamon, Madison, St. Clair, Rock Island — the pass-6 build-ready ledger's municipal-officials half) shipped in one change; Madison + St. Clair share one source (the East-West Gateway POD) and Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city payloads fill what a county cannot — Will's ward cities + Joliet (per-seat contact), Skokie (trustee districts), Freeport (the whole city; Stephenson's source is a village directory that omits its own county seat). A municipality listed by two counties resolves by source depth, then county order. Chicago's citywide officers ride this card while its 50 ward seats stay `ward`'s answer. **Two of Washington's municipalities reach past the coverage ring, and that is correct rather than a mask defect.** Its Blue Book gives the full governing bodies of Centralia and Wamac, and both cities extend well beyond Washington County — Centralia into Clinton, Jefferson and Marion, Wamac into Clinton and Marion — so a resident in the Marion County part of Centralia now sees their whole city council while the out-of-scope wash greys their location out. That resembles the 2026-07-30 wash bug and is not it: `municipality` is a STATEWIDE layer keyed by Census place GEOID, so the set of layers answering in Marion is unchanged and only the quality of one statewide answer improved. Adding Marion or Clinton to `METRO_COUNTY_FIPS` would assert that a point ANYWHERE in them resolves county-specific data, which is false one step outside Centralia's limits. The test, recorded in `scripts/build_metro_outline.py`: a county joins the ring only if a point anywhere in it resolves a layer keyed to that COUNTY. **Mason is the fleet's first source that is a SPREADSHEET THE CLERK PUBLISHES**: its elections office shared the county's own "Mason County Directory" as a Google Sheet on 2026-08-04, readable by anyone with the link and exportable as CSV, which is what let a scraper replace a document that had previously needed a human. All nine municipalities come with their whole body, and Havana's eight aldermen carry their ward. NO ADDRESS AND NO HOME TOWN SHIPS FOR ANY MASON OFFICIAL — the directory prints home addresses throughout and one county board member's row reads "SECURED ADDRESS" (an address-confidentiality program), so the rule the board roster already set is asserted in the municipal scraper too: shipping the town for everyone else would make the protected row the one that stands out. **Marshall, Washington and De Witt are the fleet's ARCHIVED-DOCUMENT sources**: none of the three publishes a municipal list on the web, and each clerk sent a file on request (Marshall a 5-page elected-officers table on 2026-08-03, Washington its 40-page Blue Book the same day, De Witt its one-page "Village/City Officials" Word list on 2026-08-17 — all seven municipalities in full, its two commission-form cities' commissioners included, with appointed/acting officers marked so a card never implies they were elected, and a township-officials PDF archived alongside for provenance only), so all three are committed under `data/source/raw/` and re-parsed weekly as a PARSER guard rather than a freshness check — refreshing them means asking again. Washington's is the richest municipal source a clerk has given this project: 14 municipalities with every trustee's phone and, for 64 of them, an e-mail. **Macoupin is the fleet's first source that a page cannot be read from at all.** Its Clerk's directory returns 78,839 bytes with zero occurrences of Mayor, President, Alderman, Trustee or Ward: a vendor plugin (SOE Software) draws the names in afterwards from a Java/Seam REST service mounted beside the CMS, which is why every WordPress action name tried against it came back unregistered. A browser capture on 2026-08-20 supplied the address — the one step this project's sandbox cannot take, its Chromium having no egress — and what it revealed needs no browser at all: an unauthenticated JSONP GET. All 27 of the county's incorporated places ship with their whole bodies, and all 28 wards of its eight ward cities carry their number, which retires the 2015 snapshot that had been the only Macoupin roster anyone could cite. TWO THINGS IN THAT SERVICE ARE TRAPS AND ARE HANDLED AS SUCH. Its per-office `effectiveAtLarge` flag does NOT mean elected at large: the vendor's own script renders it as an asterisk and the site's text map glosses that asterisk 'Appointed to Fill Unexpired Term', so it maps to `appointed` and the scraper re-reads the legend on every run rather than trusting a field name. And its per-office detail carries the officeholder's HOME address in two places (`person.address`, and `office.address2` on 149 of 245 offices) beside the hall address in a third, so only the hall slot is read and the shipped address is asserted against every residence in the municipality. Contact ships at municipality level only, which is a measurement rather than a default: the service's per-office e-mail is not reliably the person beside it — Staunton's Ward 4 alderman carries his predecessor's address and four different Virden officeholders carry one clerk's — so what ships is the MODAL hall phone, address and mailbox, which also disposes of the county's own transcription typos (Brighton's hall is (618)372-8860 on eight rows and (608)372-8860 on the ninth). Virden is the one municipality Macoupin and Sangamon both publish; the two agree on every name, and Sangamon keeps it because it prints a direct e-mail and phone for all nine officeholders. An unsourced municipality keeps the identity-only card — Lee's 13 is the newest, at the rule-4 floor after all four sourced rungs were worked (`docs/EXPANSION_GUIDE.md` §2.4) | n/a (NYC's municipalities are the five boroughs — `borough-president`) | n/a (consolidated city-county) |
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
| Fire-service boundary | SHIPPED `fire-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + McHenry + Kendall suburban Fire *Protection* Districts; Cook PRE-BUILT from the Clerk's L17 tax-agency tiling with road voids closed (102 empty voids measured raw; the Clerk's seven double-claimed pairs, Orland∩Mokena at 57 acres, ship in both exactly as the live layer answers) and DuPage/McHenry/Kendall name-only, Lake carries office contact, Kane names each district's chief + contact) · Kankakee 17 (identity-only — the county declares contact columns and populates none) · Madison 42 (the fleet's first contact-bearing fire entry: dept head 39/42, address 41/42, phone 41/42) · DeKalb 18 · Lee 22 (NG911 service areas) · Rock Island 17 (PRE-BUILT from the county's tax-agency tiling by build_parcel_fabric_districts.py — the parcel fabric excludes road right-of-way, so the raw layer was a lattice of 37-107 ft voids; the builder closes them at 75 ft, ships ground both neighbours' closings reach in neither, and the 60 ft snap still answers perimeter roads while refusing between-district seams) · Sangamon 29 FPDs + Springfield's corporate area (FireDistrictEtc L2 — 226 fragments grouped per district at load; the Springfield card states the city is served by its own Fire Department, not an FPD. The 2026-08-16 fabric survey measured this fabric INTERLEAVED, not void-carved — 168 of its sibling gaps are another district's territory and only 2 are dead ground, so it stays live-fetched and the snap covers the two dead spots) · St. Clair 44 (CentralSquare/DATA/8, the county's CAD folder — identity-only, with the source's unstated taxing-vs-dispatch status carried as a caveat on every card) · Stephenson 15 (GEOREFERENCED from the county's own 2014 vector-PDF map — the fleet's second measured boundary, hydrography-fitted to 11.5 m median; 2014-vintage caveat on every card) · Macon 17 (PRE-BUILT with road voids closed — 1,318 empty voids measured raw 2026-08-16, the fleet's worst; names verbatim) · Effingham 17 (the org's dissolved tiling, names matching the county's own fire-protection-district list; the zone literally named 'None' is excluded in the loader) · Hamilton 3 (the county's own layer; an unnamed ~0.4 km² sliver excluded — most of the county sits in no district, and the empty state says so) | SHIPPED `fire-battalion` (operational battalions, 49) | NO HONEST ANALOG — SFFD battalions exist but no boundary is published |
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
| Township / municipality | SHIPPED `township` · `municipality` (statewide IL; the municipality card names the municipal government — head of government, board, other elected officers, hall contact — for 592 municipalities across thirty counties incl. Chicago's citywide officers, county-sourced and joined by place GEOID. **The township card names the township government since 2026-08-19** — supervisor (Cicero: president), four trustees, clerk/assessor/collector/highway commissioner, hall contact — for Cook's 29 townships from the Clerk's directory TWNSP type, joined by county-subdivision GEOID (township-officials.json, weekly CI); a township in an uncovered county keeps the identity-only card, and the concept grows county-by-county exactly as the municipal roster did — Tazewell holds the next recorded sources (its GIS's 153 township-official rows + its yearbook's township section, with a one-seat GIS-vs-website drift to tie-break), a dozen shipped yearbook scrapers already bound their township sections out additively, and De Witt's clerk-sent list is recorded as gap `dewitt-township-officials`) | n/a | n/a |
| Park district | SHIPPED `park-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + Kendall; Cook's Clerk tiling includes the Chicago Park District — a Loop click resolves the city's own park taxing body; DuPage/Kendall name-only (Kendall PRE-BUILT with road voids closed — 578 empty voids measured raw in its 65-row tax-code fabric), Lake carries office contact, Kane names each district's board president + contact; McHenry has no entry — recorded gap, it publishes facilities not district boundaries) · Kankakee 4 (identity-only) · Madison 6 (identity-only) · DeKalb 6 · Rock Island 1 (Cordova — the county levies only one; pre-built with road voids closed, same builder as its fire/library siblings, and the 60 ft snap still answers its perimeter roads) · Macon 6 (PRE-BUILT with road voids closed — 556 empty voids measured raw) · Effingham 4 named districts (Effingham's drawn as two polygons) | n/a | n/a |
| Library taxing district | SHIPPED `library-district` (CountyDispatch, born consolidated: Cook's two Clerk tax-agency tilings — 59 Public Library Districts + 54 municipal Library Funds, incl. the City of Chicago Library Fund at a Loop click, one of them CARRYING ITS BOARD: the Town of Cicero Library Fund joins the Cicero Public Library's seven elected trustees + contact from the Clerk's own directory by the Clerk's own tax AGENCY id (cook-library-trustees.json) — + Will 27 w/ trustees + DuPage 32 name-only + Lake 15 w/ office contact + Kane 16 w/ board president + contact + McHenry 13 name-only + Kendall 9 name-only incl. the municipal Joliet/Yorkville city-library funds its tax tiling records, the Cook-style shape — PRE-BUILT with road voids closed, 1,158 empty voids measured raw) · Kankakee 8 (identity-only) · Madison 18 (identity-only) · DeKalb 13 · Rock Island 9 named districts (PRE-BUILT with road voids closed by build_parcel_fabric_districts.py — raw, the parcel-derived tiling drew the road grid as void lattice and road clicks found nothing; the blank-named tenth source row, a stray byte-identical copy of the UNITED TWP HIGH 30 school polygon measured 2026-08-16 and not the un-districted remainder the first record guessed, is asserted and excluded at build time; the 60 ft snap still answers perimeter roads and refuses between-district seams) · Macon 10 (PRE-BUILT with road voids closed — 960 empty voids measured raw despite the upstream 'Join_Dissolved' name) · Effingham 1 (the St Elmo district reaching in from Fayette — the county's only one; everywhere else the empty state is the answer) | n/a — NYC's three library systems (NYPL/BPL/QPL) are nonprofit corporations, not taxing districts | n/a — SFPL is a city department |
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
| `tazewell-precinct-polling` | Tazewell | Which building is current for the five precincts where the county's live layer and the Clerk's list disagree? *(The building-ID question was **answered 2026-08-17**; the ids turned out to be ambiguous rather than missing.)* |
| `randolph-precinct-polling` | Randolph | Which polling place serves each precinct? |
| `st-clair-precinct-polling-places` | St. Clair | Same, one per precinct |
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
verified — Galva 3, Colona 4, Geneseo 4. **CORRECTION, 2026-08-20: the claim that
no gap record asked for it was wrong when written.** `pass9-ward-seats-without-maps`
had asked for exactly these three cities' wards since 3 Aug, ten days before this
archive arrived, and the two records sat contradicting each other until a sweep of
that gap read them side by side — the file says "nobody wants this" while the gap
says "nobody publishes this", about the same three cities. Both are now corrected.
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

**CORRECTION, 2026-08-17 — the "unreachable" row was itself a misread, at least
for Coles.** `colesco.illinois.gov` is not unreachable and never was: it answers
HTTP 200 with a complete page. It serves an **incomplete TLS chain** — one
certificate where a control host sends three, its issuer reachable only through
the leaf's AIA extension — which every plain client reports as a connection
failure and which no browser notices. Coles shipped that day as the 52nd
dispatched county on data that had been public throughout. Its two other
hostnames are genuinely different failures, which is why "Coles (two sites)"
was already too coarse: `www.co.coles.il.us` really does reset the connection,
and bare `co.coles.il.us` has no DNS record at all.
**Checked at the same time so the correction is not over-generalised:**
`popecountyil.com` sends a COMPLETE four-certificate chain, so whatever refuses
there is not this; and no `johnsoncountyil.gov` / `johnsoncountyillinois.com`
resolves at all, so Johnson's entry cannot be tested this way. The transferable
step is one command per host — `openssl s_client -connect <host>:443 -showcerts
| grep -c 'BEGIN CERTIFICATE'` — before any "unreachable" is written down.

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
| Clark | landing page only; the board sub-page's only document is a SCAN | **DISTRICTED — the Clerk, in writing 2026-08-18** | **SHIPPED 2026-08-18 — boundary + roster both from the county's certified canvasses** |
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
and deliberately unbuilt: township officials were not then a concept any fork
carried, and the PDF's two-column text extraction decouples role labels from
names in several townships — shipping it would mean guessing attributions, and
a new concept is a Part 5 decision, not an improvisation. **That Part 5
decision was made on 2026-08-19** (Cook shipped the concept from its Clerk's
directory API — see that build-log entry), and this PDF was re-measured the
same day: it is a page-per-image scan with NO text layer at all — pypdf
extracts zero characters from every page, so the "text extraction" the
sentence above described can only have been an OCR-class read, and the
role/name decoupling it saw is a property of the PRINTED two-column layout
(one "Trustees" label spanning four name rows on a different line spacing),
which any OCR read inherits. Every address on it is a home address. The concept existing does not make this document buildable — gap
`dewitt-township-officials` carries the ask for a text-bearing form.

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

### 2026-08-17, late: Coles ships as the 64th county — a gap that was a certificate, and a roster column that was a trap

`coles-county-board` had read "no source" for a year, and its blocker was
wrong in a way worth naming precisely, because the same mistake is available
in every county still on the list. The record said **"BOTH REFUSE THIS
NETWORK — a TLS reset and a 503"**. Measured again on 17 Aug, those are three
different facts wearing one word:

- `co.coles.il.us` — **no DNS record at all.**
- `www.co.coles.il.us` — a genuine refusal; the connection resets.
- `colesco.illinois.gov` — **answers HTTP 200 with a complete 43 KB page.**
  What fails is *certificate verification*, because the county's server sends
  only its leaf certificate and never the GoDaddy intermediate that signed it.
  Browsers and search crawlers don't notice — they fetch the missing issuer
  from the leaf's own AIA extension — while `requests`, `curl` and `urllib`
  all stop at "unable to get local issuer certificate". **A server
  misconfiguration had been recorded as a refusal**, and the Clerk was told as
  much: the drafted reply flagged a block that does not exist.

The rule this earns, and it is cheap: **a TLS error is not an HTTP status.**
Before recording a host as blocked, get it to the point of *answering* —
count the certificates it sends (`openssl s_client -showcerts`), compare
against a control host, and separate "refused me" from "handed me a chain I
could not build". The fix is standard and disables nothing: the scraper
downloads the intermediate from the AIA URL the certificate itself publishes,
refuses to continue unless the bytes match a pinned SHA-256, and then verifies
the full chain. Nothing here sets `verify=False`.

**The county's GIS was public the whole time** — an ArcGIS Online org keyed
`coles` (org `MgTN1xrZnaahv1AF`, 172 public items) that no name-permutation
probe reached, the Effingham/Hamilton shape again.

**And then the trap.** `County_Board_District_View/0` carries 12 districts
*and* an `Official`, `phone`, `email`, `party`, `term` and `Population`
column — the exact shape that let Effingham and McLean ship a roster with no
scraper at all. It is false. Checked against the county's own board page:

| District | the layer says | the county says |
|---|---|---|
| 2 | Mike Clayton | Brian Ingram |
| 3 | Michael Watts | Doug Kanouse |
| 4 | Jeremy Doughty | Brandon Stewart |
| 6 | Andrew McDevitt | Tom Royal |
| 9 | Denise Corray | David Johnson |
| 12 | Gail Mason | Bristole Zimmerman |

**Six of twelve**, plus stale phones on 7 and 8 and a stale e-mail on 11. The
item was created 2022-04-23 and its whole attribute table froze there: its
District 11 `term` still reads 2022, and its `Population` column sums to
**53,873 — Coles's 2010 census count to the person**, against a 2020 count of
46,863. So the app reads `District` from the service and nothing else, and the
roster is scraped weekly from `colesco.illinois.gov/board/`.
**The general rule: an attribute table on a boundary layer is a snapshot of
whenever that layer was published, and a county that republishes a boundary
rarely republishes its people. One fetch of the county's roster page is the
difference between a correct card and six wrong officeholders.**

**The polygons, unlike their attributes, are current — proven twice.** They
are exact unions of the county's own 2022 precincts (44/44 nest, worst share
99.85%, zero pairwise overlap, 0.021% of the county uncovered against TIGER),
and their precinct composition matches **12/12** the composition the county's
board page publishes today. The 2010 populations say the county has not
redrawn since 2011, which is the county's business and not a defect in the
data; what would have been a defect is shipping the *people* from the same
frozen table.

**The 24 features that are not precincts.** `2022_Voter_Precincts_WFL1/0` was
expected to be polling-place service *areas*. It is 24 POINTS — "Polling
Places" — whose `Precinct` column lists the precincts each building serves
("CH 1, 12"). The precinct polygons are **layer 1**, 44 of them. Expanding the
24 comma-separated lists yields exactly the 44 precinct names, once each, with
no label unmatched in either direction and none claimed twice; separately,
every polygon names its own building in `PollingLocation` and all 44 agree
with the point layer's own claim. Two independent surfaces, 44/44 — so the
polling place and its address join by name in the loader (the Effingham
shape), and the card says "Polling place", which is what it is.

**Contact decisions.** The board page publishes 12 e-mails and 9 phones, all 9
distinct, so no switchboard hoist. The board OFFICE's own phone and address
ship once at board level, and that they belong to the board rather than to a
county switchboard is measured, not assumed: the same navbar block reads
(217) 348-0511 / Room 124 on the Treasurer's page and (217) 348-0585 / 701 7th
St on the Sheriff's. **The 7-digit-phone question the layer raised is moot** —
six of its numbers are published without an area code ("273-5871"), and the
resolution is not to guess 217 but to not read that column at all; the
authoritative page publishes full numbers. Likewise the stale `term` year
needed no rendering gate, because no term ships: the page publishes no party,
no term and no chairman, so none is shown. **Home addresses are printed under
most members and are never parsed** — and note the shape of that trap, because
it is new: the address anchor is itself a `tel:` link, so a parser keyed on
hrefs would have collected residences by accident. The scraper keys on the
contact row's ICON class instead. One more: three seats render `<a
href="tel:None">None</a>`, the CMS's Python `None` leaking through its
template, so a bare "None" is dropped rather than shipped as a phone number.

**A soft 404 nearly shipped on the precinct card.** The county's Clerk lives at
`/coclerk/`, not the guessable `/county-clerk/` — and the guessable path
answers **HTTP 200 with a "404 Page" body**, which `validate_card_links.py`
reads as alive by its own admission ("a dead link that lands on a styled 'not
found' page with a 200 still reads as OK here"). Caught by opening the page
rather than by probing its status. The card now links
`/coclerk/elections/`, which is also where the county points the public at the
very data the card draws: that page links a "Polling Location Map" web app
backed by the same `2022_Voter_Precincts` service. **Read a new card link, do
not merely probe it** — and while there, note the fourth data point for the
switchboard test: the Clerk's own navbar block reads (217) 348-0501 / Room 122.

**The committees page is the cross-check** (the Shelby posture — a county that
publishes its board twice will eventually disagree with itself). All 12
board-page names appear across its 19 committees and every committee name is a
board member; the weekly run fails in either direction rather than picking a
side, and the committee memberships ride each member's card.

**The ring event: a plain mainland join.** Coles borders served Shelby for
6.2 km at its south-west corner, so 3 rings before and 3 rings after (the
outer plus the Bureau and Christian enclave holes). No OUTSIDE anchor became
interior, so none moved; one was ADDED. Coles leaves five unserved neighbours
behind (Douglas, Edgar, Clark, Cumberland, Moultrie) and encloses none, but
**Cumberland now borders three served counties** — Coles, Shelby and
Effingham — with only Jasper and Clark keeping it off the enclave list, so
Toledo joins OUTSIDE to prove the fill stopped at the county line. Sullivan
(Moultrie) stays and now watches a three-sided frontier. Counts: 64 served —
52 dispatch, 3 judicial, 9 County card.

**Deliberately not shipped, stated rather than implied (no successor gap
records were invented for surfaces this change did not research):** the same
org publishes **School Districts, two Drainage District services, ESN/911
boundaries and Mattoon TIF districts**, none of them examined this pass — the
drainage and ESN layers in particular would each need the Part 5 new-concept
test before anyone assumes they belong; Coles's fire, park and library
tilings were never looked for; its municipal officials (Charleston, Mattoon,
Oakland, Ashmore, Humboldt, Lerna) are unresearched, the §2.4 ladder untouched;
and the layer's `Cong`/`Leg` columns on the precinct features are ignored
because the app already answers both from TIGER. `coles-county-board` is
retired outright; the correction its blocker needed survives in this entry,
in `scripts/coles_county_board_scraper.py`'s header and in
`build_metro_outline.py`'s county note.

### 2026-08-18: Clark ships as the 65th county — a Clerk said "I do not have maps available", and the county built anyway

`clark-county-board` had read "no source" since the pass-13 sweep, and its
ask had been sitting in the mailbox since 2026-08-05. County Clerk & Recorder
**Laura H. Lee** answered it on 2026-08-18 in one sentence: *"Good morning,
The County Board is elected by districts. I do not have maps available.
Thank You."*

That is EXPANSION_GUIDE §2.5 step 2 settled in writing — and, read literally,
a refusal of the geometry ask in the same breath. The county shipped four
hours later, because **the map was never the only route**. Clark's districts
are unions of WHOLE PRECINCTS, and a district that is a union of whole
precincts is described completely by the contest tables in the county's own
certified canvasses. That is the White/Jasper route, and Clark is the first
county where it is the ONLY route: nothing here traces a map, because there
is no map to trace.

**Three witnesses, and the build refuses to write unless all three agree.**
The Clerk's election-results site (`il-clark.accessliberty.com`, one
text-layer canvass PDF per election back to 2006) carries the 2022 General
canvass, which tabulates all SEVEN "COUNTY BOARD nTH DISTRICT MEMBER"
contests over their own precincts — 23 precincts, each in exactly one
district, every header "Vote for one". The 2024 General re-tabulates
districts 3, 4 and 7; the 2026 General Primary (final, on the live feed at
`il-clark.pollresults.net`) re-tabulates 1, 2, 5 and 6. So **no district
rests on a single document**, and the two later canvasses between them
re-prove every one of the seven. A fourth witness agrees and is deliberately
not relied on: the county's own "Clark County Board Member 2022-2024" list,
linked from `clarkcountyil.org/board`, prints a Township column matching all
seven — but it is a SCANNED IMAGE with no text layer, so it can never be a
machine source, and its district column even renders District 6 as a "5"
under the scan. The canvass is what settled that digit.

**The polygons are census fabric, and that is MEASURED, not assumed.** TIGER's
Census 2020 voting-district layer carries exactly 23 Clark features whose
names are the county's own 23 precinct names — 23/23, no spelling wobble —
and whose POP100 sums to the county's exact 15,455. All three canvasses
tabulate those same 23 names, so the fabric did not move either side of the
census. **This is the test JASPER FAILS**: five census Wade voting districts
against four current county precincts, which is why that county is still
unbuilt while this one ships on the same technique. The shipped precincts ARE
the VTDs and the districts ARE their per-district dissolve — the Shelby/White
shape, exact and deterministic, `--check` a byte compare.

**What the returns can't say, the card doesn't say.** The roster is the same
canvasses, scraped weekly: each member is whoever the county certified as
elected in the most recent GENERAL election that seated their district
(3/4/7 in 2024; 1/2/5/6 in 2022, and on the ballot again in November 2026,
which the weekly run will pick up by itself). Every row renders that election
in `districtSource`, because a canvass cannot show a mid-term appointment and
this card must not imply one. Party ships. **No chair is badged** — a
chairmanship is elected from within the body and no certified document shows
it — and **no per-member contact ships at all**: the county publishes phones
and e-mails only inside that scan, where one of the seven addresses is
unresolvable from the image (it renders as `J m.bolin@bolininc.com`, with a
space no address can contain). Six read-by-eye personal addresses plus a
guess is not a roster, so the county's switchboard stands for the board (the
Calhoun rule) and the rest is `clark-board-contact`. The same scan prints
every member's HOME ADDRESS, which never ships under any sourcing.

**Polling places were available and declined.** The county's Precinct Maps
page states "Clark County has 23 precincts, but only 15 polling places" and
links a text-layer list naming a building for all 23 — it would join cleanly.
Its title is "Polling places and addresses 11-18": the November **2018**
election. The four precinct maps beside it are dated 2014. Sending a voter to
an eight-year-old address is exactly the harm these rules exist to prevent,
so nothing ships and `clark-precinct-polling` records the ask.

**The population spread is the county's and is recorded rather than
smoothed.** The composed districts run 1,923 (D3) to 2,674 (D6) against a
one-member ideal of 2,208 — a 21.1% worst deviation, 34.0% total spread, far
outside the ~10% an ordinary post-census apportionment lands in. Nothing here
infers why; the builder's ceiling exists to catch a mis-assignment (which
would move a whole precinct and blow well past it), not to certify the plan,
and no card claims the plan is current-census-balanced. Whether Clark
reapportioned after 2020 is a question for the Clerk and is asked.

**The ring event: a plain mainland join.** Clark borders served **Coles**, which
shipped the day before, for ~16 km along its north-west edge — so the outline
stays 3 rings (the outer plus the Bureau and Christian enclave holes) and no
island appears. Clark leaves four unserved neighbours behind (Edgar,
Cumberland, Crawford, Jasper) and encloses none. **Edgar** now borders two
served counties and takes the new OUTSIDE anchor at Paris; Toledo (Cumberland)
stays, Cumberland still touching unserved Jasper and Clark's departure not
closing it.

**A fleet-wide find, recorded here because it outlives this county.** Clark's
results live on a shared vendor pair — `il-<county>.accessliberty.com` (the
Clerk's site) and `il-<county>.pollresults.net` (an AngularJS shell whose
entire result set is embedded in the page as JSON, no API needed). Its own
navigation names **34 Illinois counties**: Bond, Boone, Bureau, Carroll,
Christian, Clark, Clay, Coles, Crawford, DeWitt, Douglas, Edgar, Ford,
Hardin, Kankakee, LaSalle, Lee, Livingston, Logan, Macon, Macoupin, Marshall,
Mason, Mercer, Montgomery, Moultrie, Ogle, Piatt, Putnam, Shelby, Stephenson,
Tazewell, Vermilion, Whiteside. Fourteen of those are unserved, **including
both enclaves** (Bureau and Christian) and three counties with open threads
(Crawford, Mercer, Clay). Precinct-level certified returns are exactly what
turns a "no map" county into a buildable one when its districts are
whole-precinct — so this is a research pass worth running, and it is recorded
in the backlog rather than started here.

**What was NOT done, stated so nobody reads a shipped county as a finished
one.** Clark's fire, park and library tilings were never looked for; its
municipal officials (Marshall, Casey, Martinsville, Westfield, West Union) are
unresearched and the §2.4 ladder is untouched; its judicial circuit (the 4th)
has no PA 102-0693 subcircuits to check; and the 2014 precinct-map PDFs on the
county site were opened only far enough to confirm they carry no usable
linework. `clark-county-board` is retired outright, replaced by the two
narrower records above.


### 2026-08-18, afternoon: the vendor sweep — three counties ship, and eight gaps get an answer instead of a guess

Clark's build turned up a shared election-results platform:
`il-<county>.accessliberty.com` (the Clerk's site) paired with
`il-<county>.pollresults.net`, an AngularJS shell whose ENTIRE certified
result set is embedded in the page as JSON — no API, no key, one GET. Its own
navigation names **34 Illinois counties**. Twelve of them were unserved, and
all twelve were swept the same afternoon.

**The method, two gates, both cheap.** For each county: read the board
contests out of the feed (which settles §2.5 step 2 — districted or at large —
without anyone replying to an e-mail), then run **the Jasper test** (do the
Census 2020 VTDs still carry the county's current precinct names, and do their
populations sum to the county's own count?) and **a partition check** (does any
precinct appear in two districts' contests — i.e. is it split?). A county needs
BOTH to pass before a dissolve can draw it.

| county | board | Jasper test | splits | verdict |
|---|---|---|---|---|
| **Crawford** | 5 districts × 2 | 24/24, pop exact | none | **SHIPPED** |
| **Mercer** | 5 districts × 2 | 24/24, pop exact | none | **SHIPPED** |
| **Moultrie** | **AT LARGE**, 9 seats | 16/16, pop exact | n/a | **SHIPPED — County card** |
| Clay | ~14 lettered districts | 18/18, roman-numeral spelling | none seen | needs the rest of the board |
| Douglas | 6 districts | 17/17, pop exact | none seen | needs districts 1-3 |
| Edgar | 6 districts | 31/31, two name suffixes | none | needs district 1 |
| Hardin | **form still unknown** | 6/6, pop exact | — | no board contest on this ballot |
| Christian | 4 districts × 2 | **29 county vs 30 census** | none | re-precincted — one measurement short |
| Ford | 3 districts × 2 | 22/22, pop exact | **Patton 3** | blocked, and it CONFIRMS the old record |
| Piatt | 3 districts | 16/16, pop exact | **Monticello 1-4, Willow Branch** | blocked |
| **Bureau** | 18 districts | 50/50, pop exact | **16 precincts** | blocked — the last route closes |
| Vermilion | 8 districts + Board of Review | **38 county vs 84 census** | 2 | blocked, hard |

**The three that shipped.** Crawford and Mercer are the same build: five
districts of two members, all 24 precincts partitioning cleanly, dissolved
from census VTDs. Both walked past a standing obstacle that had stopped the
e-mail route — Crawford's district layers exist and its Assessor maintains
them, but their release is with the county's **Mapping Committee**; Mercer's
only map is a **2021 scan** that evidences the lines and supplies no data.
Moultrie needed no geometry at all: its results carry "COUNTY BOARD DISTRICT
AT LARGE MEMBER / 16 of 16 precincts / Vote For 5", so its nine members ride
the County card, and **Sullivan moved from the OUTSIDE anchor list to INSIDE**
in the same change — the guard failing the build until it was moved, exactly
as designed.

**THE CLERK CONFIRMED MOULTRIE'S FORM IN WRITING THE SAME DAY, hours after it
shipped.** County Clerk Linda S. Qualls answered the standing ask at 17:14Z on
2026-08-18 with one sentence — "Our county board members are elected at large"
— against a question first put on 5 August and followed up on the 16th. The
build did not wait for it and did not need to: the county's own certified
returns had already said the same thing in machine-readable form. Recording it
anyway matters for a reason worth stating plainly, because this is the ONE
county where the two witnesses arrived in that order. A Clerk's answer is this
project's authority on a board's FORM — it is what settles at-large versus
districted, and Clark shipped on exactly such a sentence ("The County Board is
elected by districts. I do not have maps available"). Here the returns got
there first and the Clerk's sentence is the corroboration rather than the
premise. Both point the same way, so nothing about the shipped data changes;
what changes is that Moultrie's at-large posture now rests on the county's
returns AND its Clerk, and a future reader asking "who says this board is at
large?" has two answers instead of an inference.

**ONE CERTIFIED ELECTION IS ACCEPTED HERE, AND SAID SO.** Clark's build
required a second witness per district because its composition was transcribed
out of PDF text by column geometry, and a transcription can slip. There is no
transcription in these two: the precincts listed in a contest are the precincts
that contest was ON THE BALLOT in, published by the county as machine data.
That is a record of ballots cast rather than a claim about a map, and if
anything it is better evidence than a map. The weekly roster run re-reads it
and fails on any change, which is the drift half of the same argument.

**The eight that did not ship are the sweep's real yield**, because every one
of them now has a MEASURED blocker in place of a guess:

- **Bureau — the last route closes.** This enclave's map exists only as
  street-split JPEG scans and its GIS licence lacks a display permission; the
  returns were the remaining hope. Sixteen of its precincts appear in more than
  one district's contest apiece (Princeton 2 in districts 6 and 7, Hall 1 in 10
  and 11, and so on through Hall, La Moille, Princeton and Walnut). Bureau
  SPLITS precincts, so nothing but the boundary itself will do. Its census
  fabric is perfectly fine — it is the PLAN that cuts through it.
- **Piatt — the licence is no longer the only obstacle.** Its census fabric
  passes cleanly, and the returns route would have walked straight past the
  CCGISC licence, except Monticello is split five ways across three districts.
- **Christian — one measurement short.** The other enclave. Its four districts
  partition its 29 precincts cleanly, so the composition is in hand; the census
  carries THIRTY, with Pana 5 and Southfork 3 that the county no longer runs and
  Taylorville 9 that the census never had. If the changed precincts sit wholly
  inside single districts the districts may still be recoverable — nobody has
  measured that.
- **Clay, Douglas, Edgar** — form settled, fabric passes, and each needs only
  the districts that were not on the 2026 ballot, which their older certified
  canvasses would supply. Edgar matters twice over: Clark's join made Paris the
  ring's own OUTSIDE anchor the same day. *(Both halves of this line were later
  overtaken. EDGAR SHIPPED the same evening as the 69th county — see its own
  entry. DOUGLAS'S ROUTE CLOSED: its older results turned out to be summary
  reports that count each district's precincts without naming them, and those
  counts sum to 19 against the county's own 17, so Douglas splits precincts.
  Its gap record carries the arithmetic.)*
- **Hardin** — fabric proven, form still unknown: no county-board contest
  appeared on its 2026 ballot at all. An at-large answer would make it a
  County-card county needing no geometry whatsoever.
- **Ford** — the sweep CONFIRMS the existing record from an independent source:
  Patton 3 shows up in both the 1st and 3rd districts' contests, which is the
  shared precinct that record was written about.
- **Vermilion** — the clearest fabric failure in the sweep: 38 county precincts
  against 84 census voting districts, Danville alone contributing a dozen the
  county no longer runs.

**What the sweep did NOT do**, stated so nobody reads this as finished: the 22
SERVED vendor counties were not re-examined, though several carry open gaps the
same feed might answer; the four Tier-2 counties' older canvasses were not
fetched; Christian's recoverability was not measured; and none of the three
shipped counties had its fire, park, library, municipal or judicial layers
looked at.


### 2026-08-18, evening: Edgar ships as the 69th county — an OUTSIDE anchor that lasted four hours

Edgar was written into `build_metro_outline.py`'s OUTSIDE anchor list at
lunchtime, when Clark's join left it bordering two served counties and Paris
became the frontier the fill had to stop at. It stopped there for about four
hours. The Tier-2 pass of the vendor sweep came back to it the same evening and
the guard did exactly what it exists for: the build FAILED until Paris was
moved up to INSIDE.

**Why Edgar was Tier 2, and what moved it.** The 2026 General Primary carried
only districts 2-6, so the sweep could settle the board's FORM but not its full
composition, and Edgar went into the "needs its older canvasses" pile with
Clay, Douglas and Hardin. Unlike those three, its Clerk's archive at
`il-edgar.accessliberty.com` **is populated**, and its canvasses are text-layer
PDFs.

**A wrong turn worth recording.** The first download returned a 12 KB PDF that
was the vendor's LOGIN PAGE rendered as a document — a 200, a plausible size,
and no canvass in it. The cause was assuming Clark's download parameters
generalised: Clark's handler is keyed `pageid=58&mid=188`, Edgar's is
`pageid=59&mid=189`. Read the county's own href; do not carry another county's.

**A PARSER BUG THIS COUNTY FOUND, and it nearly shipped as data.** The canvass
reader written for Clark identified a precinct as "one capitalised word plus an
optional single digit". That is true of all 23 Clark precincts and false here.
On Edgar's 2022 canvass it split BROUILLETTS CREEK into two precincts, turned
YOUNG AMERICA 1 into "YOUNG" plus "AMERICA 1", and collapsed PARIS 10, 11, 12,
14 and 15 into a single bare "PARIS" — producing a composition of 32 slots
across seven districts that looked entirely plausible and was wrong. The reader
now matches each row against the county's OWN precinct list, longest name
first, which the Clerk's results feed publishes. **Clark's shipped roster is
byte-identical after the change**, which is how the fix was verified rather
than asserted. The general lesson: a heuristic that fits the county you wrote
it for is not a parser, and the thing that would have caught this anyway is the
builder's composition check — which fails the weekly run rather than shipping a
guess.

**THE COMPOSITION, WITNESSED TWICE PER DISTRICT — Clark's standard, met in
full, and the first time this route has managed it.** The 2022 General
tabulates all seven districts over all 31 precincts, each claimed exactly once;
the 2024 General re-tabulates 1, 6 and 7; the 2026 General Primary re-tabulates
2, 3, 4, 5 and 6. Crawford and Mercer ship on a single certified election, said
plainly. Edgar does not have to.

**The two spellings are a rename, not a mismatch.** The census carries 31 Edgar
voting districts summing to the county's exact 16,866, and 29 of the names
match the county's own character for character. The two that differ are
EMBARRASS 1 and KANSAS 1, which the county writes Embarrass and Kansas; at 31
against 31 with 29 already matched, those pair uniquely and there is nothing to
choose between. `CENSUS_SPELLING` records the pairing, the shipped features
carry BOTH names, and `vtd_board_districts.apply_aliases` refuses an alias that
names a census feature which does not exist, collides with an existing name, or
shares a target with another alias.

**THE ROSTER IS THE PAGE AND THE GEOMETRY IS THE RETURNS — and Edgar is the
fleet's clearest case for that split.** Its 2022 and 2024 canvasses elected
PHILLIP R. LUDINGTON in District 6. The county's board page names SAMANTHA
McCARTY, and the Clerk's own 2026 primary confirms her by carrying a "6th
District Member 2-YEAR UNEXPIRED TERM" contest. **A seat filled mid-term is
exactly what a completed canvass cannot show**, so a roster built from the
returns would name the wrong person for District 6 today. Coles taught the
opposite half of this lesson a day earlier — a boundary layer's roster column
frozen at 2022 — and between them the rule is now plain: geometry from whatever
proves the lines, people from whatever the county maintains as people.

**Read the domain twice.** The roster lives on `edgarcountyillinois.COM`. The
county also runs `edgarcountyillinois.GOV`, which links ACROSS to the .com for
its board page and does not carry the board itself — a milder form of the
Morgan trap, and enough to make a .gov-only probe report a county with no
roster.

**The ring event: a plain mainland join.** Edgar borders served Clark and Coles
and leaves Douglas and Vermilion behind, enclosing neither. Tuscola already
held Douglas OUTSIDE from Moultrie's join that afternoon; **Danville takes
Vermilion**, which is the largest unserved county left and a recorded gap
rather than an unexamined one — the sweep measured its 38 current precincts
against EIGHTY-FOUR census voting districts.

**What is NOT done.** Clay's board is known (14 lettered districts A-N, each
with a phone, Chair Joe Goodman) and its composition still needs the seven
districts absent from the 2026 ballot, with an empty vendor archive to find
them in. Douglas needs districts 1-3, whose results sit in tagged news posts on
the county site. **Hardin is a dead end for automation**: empty vendor archive,
no county-board contest on its 2026 ballot at all, and `hardincountyil.gov` is
a DOMAIN-PARKING LANDER — 114 bytes redirecting to `/lander`. Its board's form
is unknown and only its Clerk can settle it. Edgar's fire, park, library,
municipal and judicial layers were not looked at.


### 2026-08-18, night: Sangamon district 2 went vacant, and the roster answered by deleting the district

The weekly Sangamon refresh (PR #373) came back one district short. It was
right about the fact and wrong about the shape, and the gap between those two
is the whole lesson.

**The fact.** Sangamon's per-district page for district 2 now reads
`<h3>&nbsp;(R)</h3>` — the name, the address, the phone and the e-mail all
deleted, the term "2022 - 2026" and a stranded party marker left behind. The
county's own members index says why in one word: **"District 2 - vacant"**.
Casey Constant is gone from the board. Nothing was scraped wrong.

**The shape.** The scraper skips a district whose page yields no name, so the
district lost its KEY, not just its member — and a district with no key renders
a card headed "District 2" with nothing under it. `boardCountNote(0, null)`
returns null, the member list is empty, and the reader gets a blank card. That
is indistinguishable from a layer whose data source broke, which is precisely
the state this project promises never to ship silently.

**What every guard did.** The builder's floor is 27 districts and its comment
already said, in as many words, that "a vacancy between scrapes is normal and
must not block a refresh" — 28 passed. `check_roster_retention.py` passed too,
correctly: it measures whether FIELDS stop being published, and 29 records
falling to 28 is a 3% drop that no threshold should fire on. Every gate was
working as designed. **The failure had no owner because nothing was measuring
the difference between a district that is empty and a district that is absent.**

**The fix, and why it needed a thirtieth fetch.** On the per-district page
alone, "the county emptied this seat" and "our parse broke" are the same bytes.
The members index is the thing that tells them apart, so the scraper now reads
it once per run and records a vacancy only when BOTH sources agree — the index
prints the word and the district page yields no name. A disagreement leaves the
district out the old way rather than inventing an empty seat, and an index that
cannot be fetched or parsed degrades to exactly the previous behaviour. The
party marker stranded on the emptied page is NOT carried: it belonged to the
member who left, not to the seat.

The district then ships with `vacancies: 1` and an empty member list — the
Livingston posture, counted but never named — and the card says **"Sangamon
County Board · 1 vacant seat"**. Verified in a real browser against the county's
own geometry: district 20 renders Linda Douglas-Williams unchanged, district 2
renders the vacancy line. The builder's two floors were also split to say what
they each mean: `MIN_DISTRICTS` counts vacant districts (does the walk still
cover the board?), `MIN_MEMBERS` counts only named people (are names still being
published?). A seat going vacant moves the second and not the first, because the
board did not get smaller — one of its seats got emptier.

**The general shape, for the other 42 roster builders.** A count floor that
tolerates vacancies is not the same as a pipeline that REPORTS them. Any builder
keyed by district, where the key is created from a parsed member, has this hole:
lose the member, lose the district, and the card goes quiet instead of going
honest. Livingston's `vacancies` field is the fleet's answer and it predates
this; what was missing was anyone applying it to a single-member board, where a
vacancy takes the whole key with it rather than one row out of six.

### 2026-08-18, night: the sweep for Sangamon's hole — one more county had it, and the rest fail loudly instead

Sangamon's vacancy showed that a district key created from a parsed member
disappears when the member does. This is the sweep of every other board builder
for the same shape: 44 district-keyed rosters, classified by what ONE vacancy
actually does to each. Nothing here is a guess — the seats-per-district figure
is measured off the shipped file, and each verdict is read off the builder's own
guard.

**Six counties already answer it.** Livingston, Lee, Stephenson, Shelby, Jo
Daviess and now Sangamon carry an explicit vacancy path; Jo Daviess ships
`vacancies: 1` on district 16 today. The vocabulary was never missing — its
application to single-member boards was.

**Ten counties elect single-member districts, where a vacancy takes the whole
key.** Eight of them REFUSE THE WRITE rather than ship a short roster, because
their guards are equalities rather than floors: Clark (`len(records) != 7`),
Coles (`sorted(districts) != 1..12`), Edgar (`len(roster) != 7`), LaSalle
(`!= 29`), Peoria (`!= 1..18`), White (`!= sorted(CANVASS)`), Jefferson (MIN
13 of 13) and Menard (MIN 5 of 5). Two write:

- **Rock Island** — 19 districts, floors 18/18/17. A vacancy leaves 18/18/18,
  every floor satisfied, the key gone, and the card blank. **This is Sangamon
  exactly**, and it is fixed here.
- **Kane** — 24 districts, floors 22/22/20. The builder behaves the same way,
  but the card does NOT go blank: Kane's boundary GIS carries `cbname`, so the
  render falls back to the sitting member's name off the county's own geometry.
  That is a deliberate "never blank" fallback and it holds. Its residual risk is
  a different one and worth naming: the GIS attribute is the county's, not ours,
  and a departed member stays in it until the county updates it — so Kane would
  keep NAMING someone who left, and would silently lose their phone and e-mail,
  with no note either way. Left as it stands; changing it is a judgement about
  how far to trust that attribute, not a bug fix.

**What Rock Island could NOT do, and why the fix is a sentence rather than a
count.** Sangamon has two surfaces — a per-district page and a members index —
and the index prints the word "vacant", which is what licenses `vacancies: 1`.
Rock Island's directory is a list of PERSON CARDS with "Member - District N" as
a job title, and Kane's is a SharePoint list with District as a field on the
member. In both, the district rides the person: a seat with nobody in it is
simply ABSENT, and nothing in the source says whether it is vacant or whether
the parse broke. So the card claims neither. It says the one thing that is
known — **"No member listed in the county's directory"** — and leaves the reader
at the link. `boardDirectorySilentNote()` is shared, so any entry can adopt it.

**The guard that keeps it honest.** The note fires only when the roster ACTUALLY
LOADED. Every county-board query swallows a roster failure with
`.catch(function () { return {}; })`, and without that check a failed fetch would
have printed "the directory lists no member" for all 19 districts — inventing a
county-wide vacancy out of our own network error. Verified three ways in a
browser: roster loaded with district 7 removed renders the note; roster intact
renders Richard Morthland; roster fetch aborted renders neither.

**Five multi-member counties carry the milder version.** DeKalb, Kendall,
McHenry, Ogle and Will all have member floors below their full board, so a
vacancy keeps the district key and quietly drops one row — the card then shows a
smaller delegation than the county elects, with nothing saying so. Not fixed
here, because the fix is a policy choice rather than a bug: tightening the floor
to an equality (the posture Carroll, DuPage, Macon, Montgomery and Lee already
chose) trades a blank row for a frozen file.

**Which is the sweep's second finding, and it has no owner yet.** A builder that
refuses the write leaves the weekly workflow RED and the shipped file naming a
member who has left. That is the deliberate design in at least five counties —
"a genuine vacancy is expected to need a human to lower it" — but the only
signal it produces is a red run in the Actions tab. The roster workflows open a
PR when data changes and nothing at all when the build fails; `validate-sources`
opens a tracking issue on a WARN and the roster jobs have no equivalent. So the
counties that handle a vacancy most conservatively are also the ones whose
vacancy is least likely to be NOTICED. Worth a standing issue on builder
failure, in the same shape as the source-drift issue.

### 2026-08-18, night: the five multi-member counties — the trade between a short card and a frozen file was false

The sweep left DeKalb, Kendall, McHenry, Ogle and Will carrying the quieter half
of Sangamon's hole: their member floors sit below their full boards, so a
vacancy keeps the district key and one row simply stops appearing. The card then
shows a smaller delegation than the county elects with nothing saying so. That
entry recorded the fix as a POLICY CHOICE — tighten the floor to an equality
(the Carroll/DuPage/Macon/Montgomery/Lee posture) and trade a silently short
card for a frozen file naming a departed member. **That framing was wrong, and
the third option is the one that was missing: make the shortfall VISIBLE and
leave the floors exactly where they are.**

**What the card was never told.** Every one of the five states its composition in
its own builder's docstring, in the county's own terms — DeKalb 12 districts of
two, Kendall 2 of five, McHenry 9 of two plus a countywide Chairman, Ogle 8 of
three, Will 11 of two — and every one of those figures matches the shipped file
exactly today. The number existed; it just never left the docstring. Promoting it
to `SEATS_PER_DISTRICT` and emitting `seats` on each district entry is all the
card needed to tell "this district has two members" from "this district has one
of its two listed".

**The note says what the source shows and never why**, which is the same line the
Rock Island fix drew and for the same reason: a row can be missing because a seat
is empty or because the parse dropped it, and none of these five publishes
anything that tells the two apart — Sangamon's members index, which prints the
word "vacant" and is what licenses `vacancies`, has no counterpart here. So the
card reads **"2 district members · 1 of 3 seats not listed in the county's
directory"**, and a county that DOES say a seat is vacant still wins outright: an
entry carrying `vacancies` suppresses this note in favour of its own.
`boardDirectorySilentNote` was generalised into `boardDirectoryShortfallNote`
rather than joined by a second overlapping helper, so the whole-district and
short-by-a-seat cases are one piece of code.

**The roster-loaded guard earns itself twice.** Every county-board query swallows
a roster failure with `.catch(function () { return {}; })`. Without the check,
five counties would now print "not listed in the county's directory" across every
district on any failed fetch. Verified in a browser on Ogle: roster intact renders
three members; a roster short one member renders "2 district members · 1 of 3
seats not listed"; an aborted roster fetch renders neither.

**Two of the five could not be rebuilt, and that is recorded rather than worked
around.** Ogle and Will re-scraped and rebuilt cleanly, and their rosters came
back byte-identical apart from the new key. DeKalb, Kendall and McHenry cannot:
dekalbcounty.org is behind a captcha and its Archive rung now answers 429,
Kendall and McHenry block every automated client including the Archive's crawler.
Rather than ship the concept half-converted, `scripts/backfill_board_seats.py`
reads `SEATS_PER_DISTRICT` from the county's OWN BUILDER and stamps it onto the
shipped file — one source for the number, different delivery. It is idempotent,
it refuses a file whose districts hold more members than the constant allows
(that would mean the constant is wrong, not the file), and running it after a
normal rebuild is a no-op — which is exactly what Ogle and Will report, and is
the check that the two paths agree. It also preserves each file's existing
indentation, because normalising Kendall's and McHenry's `indent=2` would have
shown as a whole-file diff now and been silently undone by their next build.

### 2026-08-18, night: the watchdog over the roster refreshes — and the four failures it found in its first run

The sweep's second finding was that a builder which REFUSES THE WRITE has no
owner. Refusing is correct — a dozen counties floor at their exact board size so
that any vacancy stops the write rather than shipping a short roster — but the
consequence is a red run in the Actions tab and nothing else: no pull request
opens, no issue is filed, and the shipped file goes on naming whoever it named
last week. `roster-health.yml` and `scripts/check_roster_workflow_health.py` are
the thing that looks. Daily, 53 refresh workflows, one standing issue, same
posture as `validate-sources.yml`: report, never edit, keep the job green.

**Discovered, not listed.** The script reads `.github/workflows/` and treats
everything that is not on a short not-a-refresh list as a refresh, so a new
county is watched the day it ships — the argument `validate_card_links.py` makes
for extracting its URL surface rather than keeping a manifest of it. Fifty-three
copies of a failure-reporting step, one per workflow and one more with every
county, was the alternative.

**Staleness is the half that matters.** A red run is often nothing — a county's
site was down for an hour. A roster that has not refreshed successfully in three
weeks is a roster frozen three weeks ago. Each workflow is measured against its
OWN cron cadence and reported as FAILING, STALE, SILENT, DISABLED, NEW or OK.

**Two false-alarm shapes were designed out, one of them by the first live run.**
Clark, Edgar and Mercer shipped that same afternoon and their weekly crons had
not come round once, so all three read SILENT on a report whose entire value is
being actionable. The workflows API carries `created_at`, so anything younger
than one of its own intervals now reads NEW and is never counted. The same call
carries `state`, which catches the other silent death: GitHub disables scheduled
workflows after 60 days of repository inactivity, and a disabled workflow is not
failing, not stale, and not running. There is deliberately NO expected-failure
list yet — the two counties known to block every automated client, Kendall and
McHenry, do not red their runs by design — and if one is ever needed it earns
its place by measurement, with the same inversion `validate_sources.py`'s
`blocked` flag uses, so that RECOVERING becomes the reportable event.

**It found four failures on its first run, none of which anyone knew about.**

- **`update-county-commissioners-roster.yml` — failing 16 days.** "CALHOUN
  parsed 0 members, outside the 3-9 an at-large board should have." This is the
  builder for `il-county-commissioners.json`, which carries ALL THIRTEEN
  at-large counties on the County card. Every one of them has been frozen since
  2 August — including Moultrie, whose commissioners were added on the 18th and
  have never been refreshed since.
- **`update-cpd-roster.yml` — failing 14 days.** "resolved only 0/20+ expected
  districts". The Chicago Police district scrape returns nothing; that scraper
  is the one that needs Playwright for a Cloudflare managed challenge.
- **`update-lasalle-county-board-roster.yml` — failing 16 days.** "zero rows
  parsed from lasallecountyil.gov/Directory.aspx?DID=39 (markup change?)".
- **`update-mchenry-county-board-roster.yml` — failing 19 days, AND ITS
  BLOCKED-SOURCE HANDLER HAS A HOLE.** McHenry is supposed to stay green: its
  scrape step carries `continue-on-error` and feeds a standing issue. But the
  scraper no longer FAILS — it exits 0 having "Scraped 19 members" with `field
  coverage: district=0/0 email=0/0 phone=0/0`, nineteen empty shells. So the
  handler, which fires on `steps.scrape.outcome == 'failure'`, never fires; the
  builder then refuses on 0 e-mails and reds the run with nothing filed. **A
  guard keyed on a step failing is blind to a step that succeeds at nothing** —
  the same shape as the count floor that passed while Brown County's seven
  e-mails emptied, and the same shape as the district key that vanished with its
  member. Worth stating as the general rule: guard the OUTPUT, not the exit code.

None of the four is fixed here; each is a different source and a different
repair, and this change is the thing that makes them visible. They are the
watchdog's first report rather than its backlog.

### 2026-08-18, night: Calhoun and LaSalle — two failing refreshes, neither of them broken

The watchdog's first report named four failing roster workflows. Two were taken
first, and both turned out to be the same non-bug wearing two different wrong
error messages. **Neither county's page had changed, and neither parser needed a
line altered.** Re-running both scrapers by hand, against the same URLs, on the
day the report landed: LaSalle parsed all 30 rows on the first try, Calhoun
parsed its five commissioners with every name, role, term and e-mail. Both
rebuilt to a BYTE-IDENTICAL shipped file, which is what proves the data was
never the issue.

**What the messages said, and why that cost time.** LaSalle's read `zero rows
parsed from …Directory.aspx?DID=39 (markup change?)`. The markup had not
changed; the parenthetical was a guess, and it sent the reader to the parser
instead of to the response. Both scrapers now print WHAT ARRIVED — status, byte
count, `<title>` — because those three facts separate a redesigned page from a
challenge screen or an error page, and they cost nothing. A guessed cause in an
error message is worse than no cause at all: it is a confident pointer in a
direction nobody checked.

**LaSalle had no retry at all.** One `requests.get`, one chance. The sibling
commissioners scraper has carried a three-attempt `fetch` since 2026-08-08 with
a docstring explaining precisely this — "several of these sites sit behind
Cloudflare, and one bad fetch out of ten made that county parse 0 members" — and
the lesson had simply never been ported. Sixteen days of red runs for want of a
retry that was already written next door.

**Calhoun's was the more interesting shape, and it is the sweep's lesson again.**
The commissioners scraper SKIPS a county it cannot fetch — carried forward, WARN
logged — but WROTE an empty member list for a county that answered 200 with
nothing usable. Two opposite treatments for the same practical outcome, with the
worse one going to the case that looks fine from the outside. None of these
counties seats zero commissioners, so zero never means an empty board; it means
the response was not the page. It is now skipped like any other unread county.

**And the real reason the job had been dead for sixteen days was neither of
those.** `MIN_COUNTIES` equals the number of counties the file actually ships,
so ANY single unreachable county failed the entire refresh. The 15 August run
lost Greene to a 429, Pike and Brown to 403s, and Calhoun to the empty 200 —
four at once — and eleven counties that answered perfectly well went unrefreshed
for over two weeks because a handful of small county sites do not like GitHub's
runners. The builder now CARRIES FORWARD any county it could not read, printing
a NOT RE-READ line per county in the same idiom Edwards and Wabash already use,
and refuses only when at least HALF the roster would be last week's — below that
line some sites were grumpy; at or above it, something changed about how this
project reaches them. Exercised rather than assumed: 2 carried succeeds, 5
carried succeeds, 6 of 12 fails, the actual 15 August combination now ships all
twelve with four disclosed as carried, and a fresh clone with no shipped file
behaves exactly as before.

**The general rule, stated once.** A guard that fires on a request FAILING is
blind to a request that succeeds at nothing — the McHenry handler, the Brown
e-mail floor, the vanished district key, and now Calhoun's empty 200 are four
instances of it in one week. And a pipeline whose floor equals its exact content
cannot survive its own dependencies having a bad day; it needs somewhere to put
partial success, or it converts every wobble into a total outage.

**A footnote that is really about this session's own process.** All of the above
was first written against a working tree four commits stale, because a
`git fetch origin --prune` with its output redirected to `/dev/null` had not
updated `origin/main` and nothing said so. The tell was `build_coverage_gaps.py
--check` reporting 113 gaps where the live site served 109 — a generated-file
gate disagreeing with production is the cheapest stale-checkout detector there
is, and it is worth reading that number rather than skimming past an OK. Never
silence a fetch.

### 2026-08-19: McHenry needed no fix, and finding that out fixed the watchdog

McHenry was the third of the watchdog's four findings and the one with the
sharpest diagnosis: its scraper "Scraped 19 members" with `field coverage:
district=0/0 email=0/0`, nineteen empty shells, so the workflow's blocked-source
handler — which fires on `steps.scrape.outcome == 'failure'` — never fired, and
the builder's refusal turned the run red with nothing filed. That was all true.
It was also **already fixed**: commit 02442cc (#342) added `if not ok:
sys.exit(1)` to the scraper at 17:33 UTC on 13 August, NINETY-ONE MINUTES after
the 16:02 run the watchdog was reporting, and its comment describes that exact
shape. Running the scraper today, it exits 1 at the fetch ladder, so the handler
does fire. McHenry's weekly cron simply had not come round again.

**Six days of a report saying FAILING about a bug that no longer existed, and
someone acted on it** — read the run, diagnosed the shape, went looking for a
fix already in the tree. The watchdog was right that the last run failed and
wrong about what a reader should do, which is the same class of error as
LaSalle's "(markup change?)": a true statement arranged so that it points the
wrong way.

**So the fix went into the watchdog.** Each workflow's latest run is now compared
against the last commit touching the workflow file or the scripts it runs; if the
code moved after the run, the verdict is UNPROVEN rather than FAILING — do not
chase this, but do not forget it either. UNPROVEN never fails the check, because
the fix is in the tree and the next scheduled run is what settles it.

**And the first draft of that would have switched the whole watchdog off.**
Counting every script a workflow runs marked ALL FOUR findings UNPROVEN,
including CPD, which nothing had touched. The reason: `validate_index.py` is
invoked by 54 of the 53 watched workflows plus itself and had changed that day,
so one commit to a shared gate would have excused every red run in the fleet —
a guard that stops guarding the moment anyone edits a common file. Only scripts
run by exactly ONE workflow now count as that workflow's own. With that in
place the report reads correctly: CPD FAILING, and the commissioners, LaSalle
and McHenry runs UNPROVEN pending their next crons.

The check needs history for that `git log`, so `roster-health.yml` checks out
with `fetch-depth: 0`; where git cannot answer, the comparison is skipped and
the verdict falls back to FAILING rather than guessing in either direction.

### 2026-08-19: CPD — the last of the four, and the one that is genuinely blocked

CPD was the only finding of the four the watchdog raised that was still failing
for its own reasons. The run log says exactly what happened, and it says it
twelve lines before the message anyone reads:

    requests engine blocked (HTTP 403); falling back to Playwright
    finder fetch failed: Cloudflare challenge did not clear within 60s
    sitemap index fetch failed: Cloudflare challenge did not clear within 60s
    WARNING: discovered 0/22 districts
    Wrote 0 records to /tmp/cpd_district_info.json (0 without error)
    build-cpd-roster: resolved only 0/20+ expected districts   <- the red

**Both rungs were refused and the scraper returned success anyway**, so the
workflow walked past its own diagnosis into the builder, and the failure that
reddened the run announced itself as a roster problem. It was a fetch problem
throughout. That is the same shape as McHenry's scraper before #342, as Brown's
e-mail floor, as Calhoun's empty 200 — **a guard keyed on a request failing is
blind to a request that succeeds at nothing** — and it is the fourth instance in
one week. The scraper now exits non-zero when no district resolves.

**What is NOT fixed, stated plainly: the block itself.** Cloudflare's managed
challenge stopped clearing from GitHub's runners around 4 August. This is a
genuine JS challenge rather than a hard deny — something a browser CAN pass,
given a residential-looking address — and the per-attempt wait has already been
raised once for exactly this reason, 20s to 60s on 2026-07-28, which bought
about three weeks. It is now 120s AND an env knob (`CPD_CHALLENGE_WAIT_S`), so
the next attempt costs a workflow edit rather than a code change. **If runs still
fail at 120s the wait is not the problem and nobody should keep doubling it** —
that sentence is in the standing issue as well as here, because the obvious next
move is the wrong one.

Nothing was verifiable from the authoring environment, and that is worth
recording rather than hiding: its Chromium cannot egress at all
(`ERR_CONNECTION_RESET`, the same limitation CLAUDE.md documents for the Leaflet
CDN), and archive.org is refused by egress policy, so neither a longer wait nor
an Archive rung could be tested here. What COULD be checked was re-checked: a
sweep of ArcGIS Online for CPD-published commander or CAPS contact found other
cities' police-district layers and nothing of Chicago's, which agrees with the
2026-07-09 sweep the scraper's docstring records. Station address, phone and
boundaries remain the only CPD data available without the challenge; commander
name, status and CAPS contact exist solely as rendered HTML behind it.

**So CPD joins Kendall and McHenry in the measured-block posture**, which is what
this repo does with a source it cannot reach: the scrape step carries
`continue-on-error`, a standing issue records the block and is commented on by
each blocked run, the builder is skipped, `data/app/cpd-district-info.json`
keeps its last good values, and the job stays GREEN with the state tracked
instead of red with it hidden. The issue names what to try next in order, and
rules out the one thing that must not be tried: no evasion, no fingerprint
spoofing. The scraper drives a real browser on purpose, and a project that
publishes other people's contact details does not get to start pretending to be
someone else to collect them.

One consequence to watch: a green run now means "either refreshed or knowingly
blocked", so the roster-health watchdog will stop reporting CPD. The standing
issue becomes the only freshness signal, which is the same trade Kendall and
McHenry already carry — acceptable because the issue is commented weekly, and
the data it guards changes on the order of a commander reassignment rather than
an election.

### 2026-08-19: Cicero and Crete — the two municipalities every guard called complete

A reader asked why Cicero — Cook's sixth-largest municipality, ~85,000 people —
had an identity-only card, and the answer turned out to be a filing quirk on one
side of the county line and a PDF-extraction defect on the other. Both shipped
the same day; neither had a gap record, because nothing measured the difference
between "every source parsed" and "every municipality covered".

**CICERO: the Clerk files a town as a township.** The suburban Cook roster reads
the Clerk's directory API by jurisdiction type, and MUNIS — the municipalities
type — carries 128 entries: 107 Villages, 21 Cities, and not one Town. Cicero is
an incorporated TOWN coterminous with Cicero Township — one government — and the
Clerk files that single body under TWNSP as "Cicero Township" (code CICTW), its
President, Clerk and Trustees beside the township's Supervisor, Assessor and
Collector. The scraper now reads TWNSP for exactly that jurisdiction and emits
it as "Town of Cicero" (the legal form the Census, TIGERweb and the town itself
use), which the existing GEOID join resolves to 1714351 with no builder change.
Verified against the town's own officials page name for name, office for
office, exactly four trustees on both sides. Distribution followed the
coterminous fact: President to head, Trustees to board, and Clerk, Supervisor,
Assessor and Collector to officers — they are officers of the one government,
not a second body — with "assessor" added to the builder's officer set. The two
party committeepersons are excluded (party posts, and the one place this API
carries PERSONAL e-mail addresses — a gmail and a yahoo in the address slot the
government records fill with the town hall block, which an unfiltered read
would have shipped as hall contact).

**THE LIBRARY BOARD WENT TO THE LIBRARY CARD.** The same TWNSP read carries the
Cicero Public Library's seven elected trustees — the ONLY library body in the
Clerk's directory, unique in the whole feed. They are not the corporate
authorities, so they do not ride the municipality card; they join the
library-district layer's Cook entry instead, keyed by the Clerk's own tax
AGENCY id (20060001, "TOWN OF CICERO LIBRARY FUND", fund tiling layer 19 —
verified live: exactly one Cicero row, and none on the independent-districts
layer 20). Will, Kane and Lake already put people or contact on this layer from
their boundary attributes; Cook's boundary source carries no people, so this is
the layer's first roster-FILE join (cook-library-trustees.json, guarded so a
record whose address is not the library's AddressTypeId-4 block can never
ship — the residence door stays closed by construction).

**CRETE: the entry the directory's text layer eats.** The Will flipbook COVERS
the Village of Crete (its own table of contents says so), but PDF-text
extraction loses the entry's head — header, hall address and phone, the
President line, and the Clerk's name — the same defect class recorded for
Lockport and Wilmington. Because the header is what split_entries anchors on,
the surviving tail rode the END of Coal City's block, where Coal City's own
Attorney cut silently discarded it: Crete shipped nothing, and every floor
passed. (Checked while here: Coal City's shipped card is CORRECT — its
president really is David A. Spesia per the directory, a surname coincidence
with Crete's attorneys Spesia & Taylor that briefly looked like a leak.)
recover_crete() now parses that orphaned tail — six trustees with parties and
terms, the appointed Treasurer — anchored on the orphan's SHAPE (a second full
member block after the host's own Attorney cut), refusing loudly if the block
shares members with its host, and standing down automatically if a future
edition's text layer carries the header again.

**Crete's President is named by the election that seated him** (the Clark
posture): Will County's certified Official Results for the April 1, 2025
Consolidated Election — Mark S. Wiater (IND), unopposed, 720 votes, 310/310
precincts — carried as a document constant with a NOT RE-READ line every run.
The Village CLERK is deliberately absent, and each reason is measured: the same
certified canvass's Clerk contest reads "No Candidate" with zero votes cast (so
the office was filled by appointment afterward — the orphan fragment "will need
to run in 2027 as an unexpired 2-year term" is that note's tail), the appointee
is named only in text the extraction lost, and villageofcrete.org serves a
SiteGround captcha to every automated client. The website and clerk's-office
e-mail DO ship, from the directory's own clickable link annotations, which
survive exactly where its text did not. A gap record (crete-municipal-clerk)
carries the ask.

**Two absence guards came out of this, because the Sangamon lesson generalizes.**
The Will scraper now FAILS a run where neither path yields Crete (the ToC lists
it, so its absence is a parse break, not a departure), and Cicero has a floor of
its own (8 of 9 governing records) rather than riding the county-wide one that
could never notice nine records among a thousand. Totals moved 590 -> 592
municipalities, 548 -> 550 heads, 2,789 -> 2,799 board members; every prose
count was re-measured from the rebuilt file rather than incremented.

### 2026-08-19, evening: township officials — the recorded candidate becomes a concept

The Cicero build left 29 townships' governments sitting in a feed the fleet
already read, and the operator called the Part 5 question the same day:
township officers had been a RECORDED CANDIDATE since the governance audit
(Appendix A's township row, Pattern A's parenthetical, a dozen municipal
scrapers bounding their county's township section out "so a future township
scrape is additive") — this entry is that candidate shipping, not a new idea.

**The taxonomy test resolves it in one line.** Township officers are elected
at-large township-wide, so §1.6 rule 2 puts them on the identity card as
rows — no new layer, no toggle, no dispatch entry. The `township` layer's
compact name-only card became a bespoke block (the municipality card's exact
shape one layer down): head, Board of Trustees, other officers, Township
Hall contact, official-website footer, executive's name on hover. Everything
rides the existing card helpers; no engine fence moved.

**Cook launches it because its source needed no new fetch.** The Clerk's
TWNSP jurisdiction type — already fetched weekly for the Town of Cicero —
carries every Cook township's government, and the whole feed was
privacy-audited BEFORE the builder existed: 284 records, ZERO home
addresses anywhere (every governing record's single address is the township
hall, AddressTypeId 3, byte-identical across a township's officials), zero
personal e-mails on any governing office, and the two known hazards exactly
where the Cicero build had mapped them — party committeeperson records hold
the feed's only personal mailboxes (31 gmail/yahoo/aol of 57) and are
excluded as party offices anyway (§1.6: out of scope), and the hall mailbox
is ONE SHARED address per township, often a named staffer's, so contact
ships on the hall row and never on a person, where it would be wrong
attribution. The builder (build_township_officials.py) asserts the hall
address type on every record it ships, so a residence can never ride the
file — the build_cicero_library_trustees.py posture, now on its second file.

**The join is the municipal join one keyspace over.** Census 2020
county-subdivision GEOID ("17" + county FIPS + COUSUBFP), resolved from a
new committed reference (data/source/st17_il_cousub2020.txt — the Illinois
rows of the Census national cousub codes file, the cousub sibling of the
places file). The Clerk's 30 jurisdictions matched 29/29 townships exactly
on first measurement; the 30th is EVANSTON, whose township government
dissolved into its city in 2014 — TIGER carries no township polygon for it,
its only TWNSP records are the two committeepersons, and the builder skips
it BY NAME (any other township going officeless is FATAL, the Sangamon
lesson). CICERO ships on this card TOO, deliberately: town and township are
one consolidated government (FUNCSTAT C), the Clerk answers "Cicero
Township" with that government, so both containment questions get the
county's own answer — President as head on both cards, keyed 1714351 as a
place and 1703114364 as a cousub, no collision (7- vs 10-digit keyspaces).

**Counts, all measured live 2026-08-19:** 29 townships, 220 officials — 29
heads (28 Supervisors + Cicero's President), 116 trustees (exactly 4 per
board), 29 clerks, 29 assessors, 15 highway commissioners, Cicero's
supervisor/collector riding its officers row. Verified in a real browser
(geometry transport mocked with the real GEOIDs — this sandbox's Chromium
cannot reach TIGERweb — while the join and render ran against the real
shipped roster): Schaumburg Township renders head → trustees → officers →
hall → website in card order with mailto:/tel: links and no personal domain
anywhere; Cicero renders President Dominick; a Chicago click keeps the
identity-only card ("Chicago city" is a city-type cousub, in no township); a
downstate click keeps today's identity-only card; an aborted roster fetch
degrades to identity-only, never an error card. Hover shares the card's
join by construction (hoverOfficial runs townshipGovFor against the same
cache) and names the executive.

**What this supersedes and what it does not.** The De Witt build-log entry's
"township officials are not a concept any fork carries" is amended — the
concept now exists — but De Witt's own PDF stays unbuilt for its own
measured reasons (image-only scan, role/name decoupling, home addresses
throughout; gap `dewitt-township-officials`). Tazewell is the next recorded
candidate, with TWO sources in hand (its GIS's 153 township-official rows,
its yearbook's township section) and a recorded one-seat drift to
tie-break. The dozen yearbook counties stay additive exactly as their
scrapers promised.

### 2026-08-20: Calhoun and Morgan — the first counties dispatched for precincts alone

An audit of which served counties have no `county-precinct` layer AND no gap
record explaining why turned up eleven. Ten were measured, and the answer was
lopsided: not one lacked a readable current precinct list, and eight were
buildable that day. These are the first two built, and they are deliberately the
two that answer the question differently.

**Both are at-large counties, and that is the point.** Calhoun and Morgan elect
their commissioners county-wide, so neither has board geometry and neither ever
will — their members ride the County card. What each gains here is the precinct
answer alone, which makes them the first two counties in the fleet whose dispatch
entry exists for a single concept. Neither card carries a board-district row, and
that absence is permanent rather than pending: an at-large county has no district
for a precinct to belong to, and a `district` property would invent one.

**MORGAN NEEDED NO BUILD.** Its GIS Coordinator maintains a public feature
service — `copyrightText: "Morgan County GIS"`, 27 polygons, each carrying its
polling place and street address — so the layer is live and there is no data
file. Currency was proven against the county's own certified returns rather than
assumed (the Coles rule): the 2026 primary reports 27 of 27 precincts and 25 of
the 27 names match the layer exactly, the two differences being the county's own
short forms for hyphenated precincts. **The census route would have failed here**
— 27 current precincts against 40 Census 2020 voting districts, Jacksonville
alone having gone from eighteen to twelve — so the published layer is not a
convenience, it is the only route. That is the argument for looking for a
published layer *before* reaching for the fabric.

**CALHOUN NEEDED A NEW GATE**, and the gate is the interesting part. Its five
precincts are unions of WHOLE census voting districts, and the county wrote the
composition into their names: Belleview-Hamburg is BELLEVIEW plus HAMBURG,
Hardin-Gilead is HARDIN plus GILEAD. `check_fabric` compares precinct names to
voting-district names one-for-one, which is exactly right for Clark — one
precinct per voting district — and rejects Calhoun outright, whose fabric has not
moved at all. `check_fabric_composed` keeps the half that actually tests the
fabric (the voting districts must still tile the county, which the population
identity proves) while `check_partition` supplies the other half (every voting
district claimed exactly once, none left over). **Nothing is relaxed** — the test
is split across two calls instead of one, and a composed county gets the same
coverage a one-to-one county gets. The composition itself rests on three
witnesses, none of them this project reading a map: the county's certified
returns bracket the 2022-2024 merge with each merged precinct's registration
equal to the sum of its parts; the names say so; and each voting district is a
whole township at an intersection-over-union of 1.000000.

**Measured on build:** Calhoun 7 voting districts → 5 precincts, populations
summing to its exact 4,437, tiling overlap 0.00 m², county coverage 100.0000%.
Verified in a real browser against the shipped geometry: a Calhoun point names
Belleview-Hamburg and its county and claims no board district; a Morgan point
names Meredosia with its polling place and street address; each county's outline
contains only its own test point. Dispatch counties 56 → 58; the `calhoun-precinct-geometry`
gap record is retired, and Morgan needed none because its absence had never been
recorded — which is what the audit that started this was about.

## Backlog — researched candidates, deliberately not (yet) built

Every entry cites where it's recorded and the blocker.

### Eight precinct layers that are buildable today, and a SECOND results vendor (found 2026-08-20)

An audit asked which served counties have no `county-precinct` layer and no gap record
saying why. Eleven did. Ten were measured county by county (Bond, the eleventh, is covered
by its own board record), and the result is lopsided: **not one of the ten lacks a
readable current precinct list** — every one publishes it, most in two or three places —
and **eight of the ten are buildable now**. Only Jo Daviess and Jersey are genuinely
blocked, and they have their own gap record (`jodaviess-jersey-precinct-geometry`).

**SHIPPED 2026-08-20: MORGAN AND CALHOUN.** Both gained a `county-precinct`
dispatch entry the same day this was written — the first two counties in the
fleet to get a dispatch entry for PRECINCTS ALONE, since both elect their boards
at large and neither has or will have board geometry. Morgan rides its own live
layer; Calhoun ships `calhoun-precincts.json` from the dissolve below, which
needed a new gate in the shared module (`check_fabric_composed` — the Jasper
test's name-for-name comparison is right for Clark's one-precinct-per-VTD shape
and wrong for a county whose five precincts sit over seven voting districts
without its fabric having moved). **Six of the eight remain**: Cass, Menard,
Moultrie, Greene, Schuyler and Scott.

**MORGAN IS PUBLISHED — build it first.** The county's GIS Coordinator maintains a public,
anonymous, county-owned feature service:
`services3.arcgis.com/95PFahBF8eyGEfuc/…/VotingPrecincts/FeatureServer/0` — **27 polygons,
`copyrightText: "Morgan County GIS"`, Illinois State Plane West**, each carrying its
polling place AND street address, with a companion PollingPlaces service. Currency was
proven against the county's own certified returns rather than assumed (the Coles lesson):
the 2026 primary reports 27 of 27 precincts and 25 of the 27 names match the layer exactly,
the two differences being the county's own short forms. Morgan would ship a precinct card
WITH polling place in one build. Note the census route would have been dead here (27
current against 40 census VTDs) — the published layer is the only route, which is the
argument for looking for one before reaching for the fabric.

**SEVEN PASS THE JASPER TEST**, populations exact in every case:

| county | precincts | census VTDs | names | alias needed |
|---|---|---|---|---|
| Cass | 21 | 21 | 21/21 exact | none |
| Menard | 14 | 14 | 14/14 exact | none |
| Moultrie | 16 | 16 | 16/16 exact | none |
| Greene | 22 | 22 | 21/22 | `WRIGHTS 2` ↔ `WRIGHTS` |
| Schuyler | 17 | 17 | 16/17 | `Frederick` ↔ `FREDRICK` |
| Scott | 10 | 10 | 9/10 | `MERRIT` ↔ `MERRITT` |
| Shelby | 33 | 33 | 32/33 | `PRAIRIE` ↔ `PRAIRIE 1` — **already adjudicated in this repo** by `build_shelby_board_roster.py` |

Carroll is the shipped precedent for exactly this shape. Five of the seven also publish a
per-precinct polling table that would join cleanly (Moultrie, Menard, Schuyler, Greene, and
Jo Daviess among the blocked pair); Cass and Scott do not appear to.

**AND A SECOND STATEWIDE RESULTS VENDOR, previously unrecorded here.**
`results.gbsvote.com` (GBS, of Lisle/Sycamore) is structurally the twin of the
`accessliberty` / `pollresults` pair and names **thirteen Illinois counties** — Cass,
Cumberland, Fulton, Greene, Grundy, **Jasper**, Johnson, Knox, Morgan, Perry, Scott,
Warren, Washington. It publishes each county's precinct COUNT on a profile page and its
full current precinct NAME list through one committeeperson contest per precinct per party,
back to 2016, with no login. **Six of its thirteen are counties this app does not serve**
(Cumberland, Jasper, Johnson, Knox, Perry, Warren), so this is a research pass of its own,
and it partially overlaps the 34-county sweep rather than duplicating it. What it does NOT
publish is geometry — which is why it corroborates Jasper's precinct list without touching
Jasper's actual blocker.

**SWEPT COUNTY BY COUNTY ON 2026-08-20, and it answers §2.5 step 2 for three unserved
counties that had it recorded as undeterminable.** The portal's archive runs to 10–16
elections per county back to 2016, most marked OFFICIAL, and a board contest's header
carries the precinct count it was on the ballot in — so the board's FORM falls straight out
of it without a website, a reply, or any map:

| county | precincts | board contests on an OFFICIAL canvass | form |
|---|---|---|---|
| **Johnson** | 16 | one, `FOR COUNTY COMMISSIONER`, 16 of 16, Vote for (1), 2022 + 2024 | **AT LARGE** |
| **Perry** | 27 | two, `COUNTY COMMISSIONER` + `CO COMMISSIONER 2YR`, each 27 of 27, Vote for (1) | **AT LARGE**, staggered |
| Scott | 10 | one, 10 of 10, Vote for (1), across six elections | at large (already recorded) |
| **Cumberland** | 12 | three, Central 6 / Eastern 5 / Western 3 | **DISTRICTED — and splitting precincts** |

Johnson and Perry therefore move off the geometry path entirely and onto the County-card
roster path; Perry's own site is still behind a captcha (HTTP 202) and that did not matter.
**Cumberland is the counter-example that makes the method worth trusting**: its three
district contests sum to 14 against a county of 12, which is only meaningful because the
same canvass reports exactly 12 for every countywide contest and 3 for the split
state-representative contest. Test the field against a countywide race before reading
anything into it — a pseudo-precinct for early or mail voting would have inflated every
count equally and this arithmetic would have been noise.

What the portal still cannot do, for any of them, is name who SITS today: a return records
who won a contest, never who holds the seat now, and an appointment to a mid-term vacancy
appears in no return at all. That reasoning is worked out in full on the Scott record and
applies unchanged to Johnson and Perry.

**The recurring trap, now seen three times in one day** (Bond, Jo Daviess, Jersey): the VTD
population sum passing EXACTLY says only that the census fabric tiled the county in 2020.
It is silent about whether the county has re-precincted since, and only the name comparison
catches that. Any future builder that checks the sum without the names will ship a stale
fabric and pass its own gate.

### A statewide library-district layer — 642 polygons, weak provenance (found 2026-08-20)

Found while re-measuring Carroll's special districts, and it reaches much further than
Carroll. `services.arcgis.com/R0IGaIgf2sox9aCY/…/IL_Boundary_Layers/FeatureServer` **layer
11, "Library Districts", carries 642 polygons for the whole state**, public and
token-free, with a `Library` name field. Verified directly: 642 features, and over Carroll
it returns exactly the seven library tax lines the county clerk's own report names, one
for one.

**Why it matters beyond one county.** Eight gap records across seven counties — Boone,
Lee, Peoria, Randolph, Rock Island, Sangamon, St. Clair, Stephenson, plus Carroll — record
a missing library-district boundary, and the app's `library-district` layer today
dispatches only Cook, DuPage, Kane, Lake and Will. One public statewide layer bears on all
of them at once, which is a different kind of find from a county-by-county unlock.

**What makes it trustworthy, measured on Carroll.** It is right on the NEGATIVES, which is
the check a wrong layer fails: Shannon village and Lake Carroll land in no library district
at all, and the clerk's tax codes independently agree that Shannon's code carries no
library line. Its extents are true rather than county-clipped, so a district that straddles
a county line (Pearl City, into Stephenson) keeps its full reach — the thing several of
these gap records explicitly ask for.

**Why it is recorded rather than shipped.** The publisher is the Illinois Broadband Office
/ Connected Nation — **a broadband contractor, not the county and not the districts**. The
layer is not mentioned in its own item description, `copyrightText` is empty, and every
attribute besides the name is a broadband service metric, which means these are library
**service areas compiled for broadband planning** rather than districts filed by the bodies
themselves. That is a real published boundary with a weak provenance line. Under this
project's rules that is a judgement call, not a default: a card carrying it would have to
say whose boundary it is, and the alternative — leaving seven counties' library cards
name-only — is also a cost. Worth deciding deliberately, and the same service's other ten
layers (village boundaries, township/precinct, school districts) deserve the same look.

### ISBE's precinct-level results archive — a statewide superset of the vendor route (found 2026-08-20)

Found while measuring whether Brown's and Calhoun's precincts could be built. **ISBE
publishes precinct-level certified results as CSV for every election authority in
Illinois**, and nothing in this repo reads it.

    https://www.elections.il.gov/Downloads/ElectionOperations/ElectionResults/ByOffice/
        <electionId>/<electionId>-<officeCode>-<OFFICE>-<tag>.csv

Verified directly: one file (2026 General Primary, Treasurer) is 4.06 MB, 51,570 rows,
**108 election authorities**, columns `JurisdictionID, JurisContainerID, JurisName,
EISCandidateID, CandidateName, EISContestID, ContestName, PrecinctName, Registration,
EISPartyID, PartyName, VoteCount`. Election ids come from `ElectionVoteTotals.aspx`
(69 = 2026 GP, 68 = 2025 CE, 66 = 2024 GE, 62 = 2022 GE, 58 = 2020 GE), and the archive
runs back to 1998. Calhoun's five precincts and Brown's fourteen were read straight out of
it, matching each county's own reports name for name.

**Why this outranks the vendor sweep.** The `pollresults.net` / `accessliberty.com` pair
carries **34** counties and answers §2.5 step 2 for those; this carries **all 102**, from
one host, in a documented file layout, including every county the vendor never touched —
and the counties it settles are exactly the ones with nothing else readable (Brown's own
reports are image scans; Calhoun's are printer files; Adams's site refuses automation
outright, though ADAMS IS THE LIMIT CASE — its returns are published only on the blocked
host, so ISBE covers the county but not that county's own archive).

**Two uses, one of them free.**
1. **A precinct list for any county, any year** — the input `check_fabric` needs, plus the
   date-bracketing that shows *when* a county re-precincted (Brown's rename landed between
   Nov 2024 and Apr 2025; Calhoun's 7→5 merge between Nov 2022 and Nov 2024, both read off
   consecutive files).
2. **A re-precincting tripwire for every census-derived layer already shipped** — diff this
   election's `PrecinctName` set against last election's and a moved fabric announces
   itself. §2.5.1 step 6 asks for exactly that check and currently gets it only where the
   vendor carries the county.

**The caveat to carry into any builder:** `Registration` is self-reported and is sometimes
`0` (Calhoun 2026, all of Brown 2020). Zero is not a measurement, and a floor keyed on it
would fire on the publisher's blank rather than on a real loss.

### ISBE's county-board STRUCTURE table — every county's board shape, at an unknown date (found 2026-08-21)

Found while settling Saline's board form, and nothing in this repo read it.

    https://www.elections.il.gov/ElectionOperations/ComplianceRecord.htm

An Excel-exported HTML table with a row for **all 102 counties** and five columns:
number of board members, `Single-Member` / `Multi-Member` / `At-Large`, number of
districts, members per district, and whether cumulative voting is used. It answers
§2.5 step 2's *shape* question for any county in one fetch, with no canvass to read and
nobody to e-mail — which matters most for exactly the counties whose own returns are
image scans.

**It was checked before it was used, and the check is the point.** Its embedded metadata
is from **2007** and it carries no revision date. Before it informed anything it was
verified against four counties whose current pages this project can read:

| County | Table | The county today |
|---|---|---|
| Clay | 14 single-member | 14 districts A–N ✓ |
| Hancock | 15, five multi-member × 3 | District One–Five, 3 each ✓ |
| Lawrence | 7 single-member | Districts 1–7, one each ✓ |
| Adams | 21, seven multi-member × 3 | matches the recorded finding ✓ |

**And then RICHLAND broke it, the same day.** The table calls Richland `At-Large`; the
county has drawn **seven numbered districts** since at least 2024 and elects from them,
which its own certified Official Results for 2024 and 2026 state outright. The likeliest
reading is that Richland was at-large in 2007 and districted at a later redistricting.

So the rule, now proven rather than asserted: **this table is evidence of a county's
board structure at an UNKNOWN DATE, never of its structure today.** Use it to know what
to look for and to corroborate a finding; never let it be the last word, and never read a
name from it (there is none to read — it names no members and no chairs). Saline shipped
on its own certified canvass with this table in third place, which is why Richland's
counter-example cost nothing.

### A THIRD results vendor, and the one that publishes per-precinct BALLOTS (found 2026-08-20)

`platinumelectionresults.com`, linked from Franklin County's own Elections page. It is not a
variant of the other two — it is the only one of the three that answers the composition
question directly, and it is what made Franklin buildable in an afternoon with nobody asked.

**Five Illinois counties**, probed by id: Clinton (`/turnouts/county/10`), Randolph (13),
Wayne (14), Marion (18), Franklin (21). All five already carry gap records, and the index
page is JS-driven so the list has to be probed rather than scraped.

**What makes it different.** `pollresults`/`accessliberty` and `gbsvote` publish a contest's
precinct COUNT; this publishes a **page per precinct per election**, back to 2016, listing the
contests that were actually on that precinct's ballot:

    /history/prraces/<year>_<ge|gp|ce>/<countyId>/<precinctId>

So the district a precinct belongs to is not inferred from arithmetic — it is read off the
ballot the county certified. Fetch all N precinct pages, group by which board candidate each
one voted on, key the groups to the county's own members page, and the composition falls out
as a partition you can check: Franklin's 35 precincts split 13/13/9, every precinct claimed
exactly once, nothing left over. That check is the proof the districts are whole-precinct
unions, and it is the same check that FAILED for Clay (19 slots over 18 precincts) and
Cumberland (14 over 12).

**A wrong shortcut, recorded because it looked right.** The vendor's precinct ids group
`51xx`–`54xx`, `61xx`–`64xx`, `71xx`–`74xx` — three clean families that read exactly like a
district key. They are not one. Franklin's Browning 1 and Browning 3 sit in District 1 while
Browning 2 sits in District 2, and the prefixes interleave across all three districts. The id
grouping was tested against the ballots and failed; only the ballots are evidence.

**AND THE OLDER VENDOR'S COUNTY LIST IS INCOMPLETE, found the same day.** This project records `il-<county>.pollresults.net` / `accessliberty` as carrying **34** Illinois counties. HARDIN IS NOT ON THAT LIST AND IS CARRIED: `il-hardin.pollresults.net` returns 128 KB with a full embedded result set — its certified 2026 General Primary, 43 races, `Final: true` — and it settled Hardin's board form outright. So the 34 is a floor, not a census, and any county recorded as "not on the vendor" without a content test should be re-probed. The test matters: `il-gallatin` and `il-fayette` both return the SAME 2,788-byte generic shell (uncarried), and `il-henderson` answers 302 with an empty body — three measured negatives that a status-code check would have called 200-and-present.

**Worth doing next, cheaply, by the same method:** Wayne (id 14) already passes the fabric test
— 27 census VTDs matching its current precinct names — so if its board is districted and
whole-precinct, it resolves the same way Franklin did. Marion (18) does not: its fabric
genuinely moved, 48 census VTDs against 37 current precincts.

### The Jasper test false-rejects about a third of counties, and the causes are mechanical (measured 2026-08-20)

`check_fabric`'s name comparison is this fleet's primary gate on whether a county's precinct
fabric has moved since 2020, and the guidebook has warned four times that the population sum
alone cannot catch a moved fabric — **only the name comparison can**. That is still true. What
was never measured is the comparison's own error rate, and it is high in one direction.

**The measurement.** All 33 frontier counties, Census 2020 VTD names against the county's own
CURRENT precinct names, taken from ISBE's certified precinct-level returns for the 2026 General
Primary (one statewide CSV, so every county on the same footing; Gallatin's census fetch failed
and is excluded, leaving 32).

    naive comparison (case + whitespace only)     9 of 32 match
    after normalising four mechanical causes     19 of 32 match

**Ten counties — 31% — were rejected for reasons that are not a moved fabric.** A builder
following the recipe as written would have recorded each of them as re-precincted and stopped.

**The four causes, each verifiable rather than judged.**

1. **Census truncates long names at 17 characters.** Champaign's `COMPROMISE GIFFOR` is the
   county's `COMPROMISE GIFFORD`; `COMPROMISE PENFIE` is `COMPROMISE PENFIELD`. Safe to match
   only when the census name is exactly 17 characters AND prefixes the county's — both testable,
   so this never merges two real precincts.
2. **Zero-padding.** `CUNNINGHAM 01` vs `CUNNINGHAM 1`, throughout Champaign.
3. **A vestigial `1`/`I` on single-precinct townships.** The census writes `CAVE 1`, `UNION 1`,
   `AVENA 1`, `LARKINSBURG I` where the county writes `CAVE`, `UNION`, `AVENA`, `LARKINSBURG` —
   and **no `2` exists anywhere in either set**. Strip the trailing `1` ONLY when the stem has no
   `2` sibling; that condition is checkable and makes the rule safe by construction. Hits Clay,
   Fayette, Franklin, Union and Warren.
4. **ISBE reporting-unit suffixes.** ISBE reports sub-precinct units, not precincts:
   Cumberland's 12 precincts appear as 20 rows (`SPRING POINT-7`, `-8`, `-9`, `-10`,
   `CROOKED CREEK-19`, `-20`), Warren's as `BERWICK 1-2`, Richland's 21 as 30, Jackson's 56 as
   63. Strip the trailing `-N` and the base names reduce exactly. **This one cuts both ways** —
   it is also the tell that a county subdivides precincts for reporting, which is what a county
   does when district lines cut through them.

**What still differs is real, and worth separating from the noise.** Alexander, Christian,
Clinton, Jasper, Knox, Lawrence, Marion, Massac, Vermilion and Williamson genuinely moved.
Two are near-misses of a different kind: **Fayette** differs on one township only (`HURRICANE`
became `NORTH HURRICANE` + `SOUTH HURRICANE` — a real split, one precinct), and **Hancock**
differs on one name where the **census is misspelt** (`MONTIBELLO IV` for the county's
`MONTEBELLO 4`). **Saline** is a rename, not a move (`ELDORADO n` → `EAST ELDORADO #n`).

**Why this matters beyond tidiness.** The counties it rescues are the input a composition search
needs. Of the 19 that match, four are already measured shut for splits (Bureau, Douglas, Ford,
Piatt), two more were shut on splits today (Clay, Cumberland), and two are at-large so need no
geometry at all (Johnson, Perry). That leaves **Franklin, Hardin, Henderson, Jackson, Pope,
Pulaski, Richland, Union, Warren and Wayne with a verified-current fabric and no recorded reason
they cannot be built** — the missing piece for each is a district composition, not geometry.
Franklin is the nearest: its own record already establishes the board is districted and its
members page groups Districts 1-3.

**The rule to carry forward:** a name mismatch is a hypothesis, not a verdict. Before recording a
county as re-precincted, check it against these four causes — and record which one you ruled out,
because "the names differ" turned out to be wrong ten times in one sweep.

### The app ships 1,602 e-mail addresses and no gate checks one of them (found 2026-08-20)

Found while re-measuring Henderson, whose published web address turns out to be a PARKED DOMAIN —
`hendersoncountyil.gov` answers 200 with a 114-byte body that is nothing but
`window.location.href="/lander"`, and `/lander` identifies itself as parking (`LANDER_SYSTEM="PW"`,
`_trfd.push({ap:"parking"})`). That is the `hollow` state `validate_card_links.py` learned to catch this
week, and the same 114-byte script-only-redirect shape as Morris. The county's clerk e-mail that this app
SHIPS — `avanarsdale.coclerk@hendersoncountyil.gov`, from `il-county-clerks.json` — sits on that domain.

**Which raised the general question, and the answer is a surface nothing guards.** `validate_card_links.py`
extracts exactly two things: `url: "http…"` and `href="http…"`. The app also ships **1,602 e-mail addresses
across 480 domains** in `data/app/` — more addresses than the ~1,230 URLs the gate does check — and not one
of them is verified by anything.

**Measured, and the measurement's first answer was wrong in a way worth recording.** Resolving all 480
domains by A record leaves 33 that do not resolve, including `kanecoboard.org` (25 Kane board addresses) and
`board.wincoil.gov` (20 Winnebago board addresses). Reporting those as dead would have been a false alarm on
45 officials: **an A record is the wrong test for a mail domain.** Re-tested for MX over DNS-over-HTTPS,
**23 of the 33 route mail perfectly well and simply have no website** — a mail-only domain is normal, not
broken. Only **10 have no MX at all**, and those 10 addresses genuinely cannot receive mail:
`cityofalton.il.gov`, `offallon.org`, `sugargroveil.org`, `southerview.us`, `gmail.org`, `hormil.xom`,
`vilageofjerome.com`, `villaegofgrandview.gov`, `villageofgrandvew.gov` (nine in `municipal-officials.json`)
and `washingtonco.illnois.gov` (one in `washington-county-board-members.json`). Six are plainly transcription
slips — `gmail.org` for gmail.com, `.xom` for `.com`, `vilage`/`villaeg` for village, `grandvew` for
grandview, `illnois` for illinois.

**Whose slips, checked rather than assumed — and the first check pointed the wrong way.** Washington's
archived Blue Book contains `illnois` zero times and `illinois` 71, with `doug.bening@washingtonco.illinois.gov`
spelled correctly, which reads as proof the parser corrupted it. It is not: the Blue Book feeds the MUNICIPAL
roster, while the board roster is scraped from the county's own `/county-board/` page — and that page carries
`doug.bening@washingtonco.illnois.gov`, once, against 175 correct spellings of illinois elsewhere on it. So
the app is faithfully shipping the county's own typo, which is the Shelby `distric1-2@` precedent and correct
behaviour under the honesty rules.

**The judgement this leaves, which is a decision rather than a fix.** Shelby's typo was in the LOCAL PART of a
real domain, so mail bounces to a real server. These ten are typos in the DOMAIN, so mail cannot be attempted
at all — a reader who clicks gets silence. Shipping a contact that provably cannot receive mail is faithful to
the source and useless to the reader, and the repo already has a precedent for exactly that tension: Boone's
Gramkowski phone, where two publishers disagreed and the build shipped NEITHER, discovering it by comparison
at build time so it retires itself when either side fixes it.

**Proposed guard, matching the `hollow` addition.** Extract e-mail domains alongside URLs, resolve MX once per
domain with retries (never A — that is the false-alarm trap above, and it would have condemned Kane and
Winnebago), and fail on a domain with no MX. It is ~10 findings against 480 domains today, so the signal is
small and specific rather than a monthly wall. It also cannot calcify: a county fixing its page clears the
finding by itself.

### ISBE's County Officers Book — a statewide chair source nothing here reads (found 2026-08-20)

Found while re-measuring Adams, whose own website refuses every automated visit:
`elections.il.gov/Downloads/ElectionOperations/PDF/coofficers.pdf` is a **107-page,
text-layer, all-102-county** directory stamped *last updated 15 Dec 2025*, carrying party,
name, e-mail, street address and phone for County Clerk, Circuit Clerk, Recorder,
Treasurer, Sheriff, State's Attorney, Coroner, Supervisor of Assessments, Regional
Superintendent, both party chairs — and **County Board Chair for 85 counties**. Nothing in
this repo reads it (`coofficers` and `ComplianceRecord` return no grep hits; the shipped
clerk pipeline reads a different ISBE surface).

**BUILT AND REJECTED, 2026-08-20 — the pipeline exists and its output is deliberately not
app data.** `scripts/isbe_county_officers_scraper.py` + `scripts/build_county_board_chairs.py`
parse the whole directory and write `data/source/isbe-county-board-chairs.json` (102 chairs;
NOT `data/app/`, so nothing can render it). They were written to close the gap below and they
are what refuted it, which is why they are kept rather than deleted: the measurement should be
re-runnable by whoever next finds this directory and thinks it looks authoritative.

**Why it is rejected: the chair column is stale, and that is measured, not suspected.** Of
the 56 counties where this app ships its own roster and a comparison is possible, ISBE names
a **DIFFERENT chair in 16** — Carroll, DeKalb, De Witt, Edwards, Greene, Grundy, Iroquois,
Logan, Marshall, McDonough, Menard, Moultrie, Ogle, Pike, Randolph, Shelby. In **ten checked
live against the county's own current board page** (Ogle, Grundy, Marshall, Iroquois, Logan,
Shelby, Greene, Moultrie, Carroll, McDonough) the person ISBE names appears **nowhere on it**
while the app's name is there with the chair title — Carroll's own page reads "Julie
Bickelhaupt Chair" with ISBE's Joseph Payette absent entirely; McDonough's reads "County
Board Chair - Eric Blakeley" with ISBE's Scott Schwerer absent. That is not two sources
differing. That is one source stale, and its own *last updated 15 Dec 2025* stamp is exactly
what those 16 disprove, so no `asOf` badge repairs it — printing the date beside the name
would assert a currency the document does not have.

**The precedent that decides it.** This repo already has a rule for a published column that
is substantially wrong: Coles County's board layer publishes an `Official` column that gets
**six of twelve** names wrong, and the answer was not to ship it with a caveat — it is read
NOWHERE, and Coles's people come from the county's board page instead. Freeport's stale
`Alderperson` column and McLean's stale `REPNAME` column are read nowhere for the same
reason. **29% wrong is worse than Coles's own layer is on the counties where anyone checked.**
ISBE's chair column joins them.

**Two claims from the build that did not survive checking**, recorded because both are the
kind a reader would make again. (1) The coverage case is *stronger* than it first looked, not
weaker — the County card is statewide, so a chair would have surfaced in all 46 unchecked
counties, not only the ten of them this app serves with a county-keyed layer. The reliability
finding is therefore decisive on its own and does not lean on coverage at all. (2)
`winnebago-county-board-members.json` carries no `name` field, which reads like a card that
names nobody. **It is not** — Winnebago's names ride the WinGIS boundary 20/20, and that file
is deliberately contact-only enrichment (`build_winnebago_county_board_roster.py`'s docstring
says so). Its `unchecked` verdict is a false negative, which also means the 29% is measured
against a cross-check that is itself slightly too generous to ISBE.

**What it can never do, unchanged:** name a board MEMBER. `"County Board Member"` occurs zero
times in the file and `"District"` zero times — it is an officers directory, not a roster.

**What stays open.** Where ISBE's name AGREES with a county's own publication (40 counties)
the row is by definition not stale, so its e-mail/phone/corroborated office could enrich a
chair this app already names *from the county* — contact only, never the name. That is a
different and defensible build and is the one piece of this worth picking up. The second ISBE
surface found in the same pass, `ComplianceRecord.htm` (each county's board size, district
structure and members-per-district; Adams 21 seats / 7 multi-member districts / 3 each),
carries 2007 metadata and no revision date, so it stays citable for STRUCTURE and never as
currency — structure is the thing about a county that does not turn over.

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
> | **The `pollresults.net` / `accessliberty.com` county pair** (found 2026-08-18 while building Clark) — one election-results vendor serving **34 Illinois counties**, each at `il-<county>.accessliberty.com` (the Clerk's site, one TEXT-LAYER certified canvass PDF per election back to ~2006) and `il-<county>.pollresults.net` (an AngularJS shell whose ENTIRE result set is embedded in the page as JSON — no API, no key, one GET). Its own navigation names them: Bond, Boone, Bureau, Carroll, Christian, Clark, Clay, Coles, Crawford, DeWitt, Douglas, Edgar, Ford, Hardin, Kankakee, LaSalle, Lee, Livingston, Logan, Macon, Macoupin, Marshall, Mason, Mercer, Montgomery, Moultrie, Ogle, Piatt, Putnam, Shelby, Stephenson, Tazewell, Vermilion, Whiteside. **EIGHT are unserved as of 2026-08-21 — Bureau, Christian, Clay, Douglas, Ford, Hardin, Piatt and Vermilion — down from fourteen as Clark, Coles, Crawford, Edgar, Macoupin, Mercer, Moultrie and Shelby shipped; two of the eight are enclaves (Bureau, Christian).** AND THE LIST OVERSTATES WHAT IS REACHABLE, measured 2026-08-21: probing `pastelections.aspx` across all thirty frontier counties, only BUREAU (68 canvasses) and CHRISTIAN (60) actually return an archive — every other frontier county 404s with a ~9.6 KB error page, and the two carried ones are already measured shut for reasons the vendor cannot fix (Bureau splits precincts between districts; Christian re-precincted, and its own download handler 404s on the pageid/mid pair its page advertises). So this route is EXHAUSTED for the current frontier rather than merely unworked.  A FOURTH VENDOR JOINS THIS BACKLOG (2026-08-21): **results.gbsvote.com** (GBS), neither the accessliberty/pollresults pair nor platinumelectionresults.com, carrying THIRTEEN Illinois counties — Cass, Cumberland, Fulton, Greene, Grundy, Jasper, Johnson, Knox, Morgan, Perry, Scott, Warren, Washington — five of them unserved (Cumberland, Jasper, Johnson, Knox, Perry). Archives run back to 2016 at /locations/county_results.asp?id=N and each county page names its election authority. It was found the way the others should have been: on a county's OWN Elections page, not by guessing a hostname. Its first yield was PERRY's board form, settled AT LARGE from three certified elections whose commissioner contests each span all 27 precincts — a county-card answer, not a geometry one. THE FLEET NOW HAS FOUR SUCH VENDORS AND THE LESSON IS THE SAME EACH TIME: read the county's Elections page first, because every one of these was linked from one. Clark proved what this is worth: precinct-level canvasses turn a "no map" county into a buildable one whenever its board districts are unions of whole precincts, and they answer §2.5 step 2 (districted or at-large) without anyone replying to an e-mail | none — the pages are public and static; the work is per-county, and each still needs the Jasper test (do the census VTDs match the county's CURRENT precincts?) before any dissolve ships | **yes — a research pass, unstarted** |
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
- **PARCEL-FABRIC SURVEY (2026-08-16) — every fire/park/library source measured for the
  road-void lattice, and the fix shipped in two tiers.** Rock Island's report ("why does
  the library map draw the road grid?") generalized: a tiling dissolved from a PARCEL
  fabric excludes road right-of-way, so districts render as void-split lattices and a
  click on a road inside a district finds nothing. All 51 sources were measured twice —
  first for sibling-part gaps in the 15–200 ft road band, then, decisively, for whether
  each gap is EMPTY (dead ground: nothing answers there) or NEIGHBOR-FILLED (another
  district's territory: containment already answers, no defect). The second measurement
  overturned four verdicts the first had flagged: **Sangamon fire (168 filled / 2 empty),
  St. Clair fire, Iroquois fire, Stephenson fire and Kankakee library are INTERLEAVED,
  not void-carved** — their fragmentation is annexation patchwork, and closing them would
  have accomplished nothing (+0.0% area when tried on Sangamon).

  **Severe tier — PRE-BUILT** by `scripts/build_parcel_fabric_districts.py` (which
  absorbed `build_rock_island_tax_districts.py`): Kendall ×3 (977/578/1,158 empty voids
  in tax-code fabric of 170/65/145 rows), Macon ×3 (1,318/960/556 — the fleet's worst,
  despite upstream layers literally named `Join_Dissolved`), Cook fire (102, plus seven
  district pairs the Clerk's own tiling DOUBLE-CLAIMS — Orland∩Mokena is 57 acres —
  shipped in both exactly as the live layer answers), Rock Island ×3. The transform:
  dissolve by name, close road voids at 75 ft (never claims ground farther than 75 ft
  from county-published fabric, cannot fill a village-sized hole; a bridge whose facing
  frontage is shorter than the closing diameter erodes away, so lone outlying parcels
  stay separate), contested ground BOTH neighbours' closings reach ships in NEITHER,
  raw county ground is never surrendered — not to simplify wobble (symmetric cede), not
  to a sibling (double-claims survive). Build FAILS on count drift, edit-stamp drift
  (where published), raw ground lost, overreach, non-raw overlap, unexplained residual
  voids, or a probe miss (measured dead points: Kendall NEWARK FPD 99 ft, Cook LEYDEN
  39 ft; negatives: the Loop, Moline, Rock Island city, Andalusia stay empty).

  **Moderate tier — 60 ft runtime snap** (`PARCEL_FABRIC_SNAP_FT`, wired per entry,
  measured empty voids only): Cook library-districts/library-funds (32/33, snapped
  across BOTH tilings at once so a district/fund boundary road still refuses) + Cook
  park (43) · Will fire/park/library (3/42/38) · DuPage ×3 (67/17/18) · Lake ×3
  (62/13/9) · Kane ×3 (70/17/15) · McHenry library (5) · Kankakee fire (10) · Madison
  fire/park (6/25) · DeKalb ×3 (20/14/8) · Sangamon fire (2) · Peoria fire/library
  (11/6) · Effingham fire (2). A snapped card carries a Note naming the distance. NOT
  wired (no empty voids measured): McHenry fire (true exclaves), Madison library,
  Kankakee library/park, St. Clair, Iroquois, Stephenson, Peoria park, Effingham
  park/library, Lee, Adams, Boone, Hamilton, Stark — a snap on a drawn-boundary source
  would assert membership the source doesn't.

  Untested siblings of the same fabric families, left for a later pass: Cook's TIF
  tiling (`tif-district`, the same Clerk family as its fire layer) and Kendall's ward
  tiling (same Hosted parcel fabric).

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
  whole-district → Pattern A rows; ISBE directory candidate); township officers SHIPPED as a concept 2026-08-19
  (Cook, township-officials.json — Part 5 build-log entry); remaining counties captured
  by the municipal clerk-yearbook scrapers as each is built (verify
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
| `township` | Township / County Subdivision | geography | Bespoke | live TIGERweb CouSub | `township-officials.json` (weekly CI; Cook's 29 townships — supervisor/president, trustees, clerk/assessor/collector/highway commissioner + hall contact, joined by county-subdivision GEOID; uncovered counties keep the identity-only card) | — (subOf `county`) |
| `municipality` | Municipality | geography | Bespoke | live TIGERweb Places | `municipal-officials.json` (weekly CI; thirty-one counties + Chicago's citywide officers, 597 municipalities incl. the TWNSP-filed Town of Cicero and the canvass-headed Village of Crete — head of government + board + other elected officers + hall contact, joined by place GEOID; depth per county: full body Cook/Will/DeKalb/LaSalle/Winnebago/Ogle/Stephenson/Grundy/Livingston/Logan/Sangamon/Madison/St. Clair/Rock Island/Henry/Cass/Peoria/Tazewell/Marshall/Washington/Boone (+ McLean's three ward cities from their own pages — the county-wide source is a JS-locked Airtable interface), head+clerk DuPage/Kane/McHenry/Kendall/Carroll/Whiteside, contact-only Lake. Madison + St. Clair share the East-West Gateway POD (one COG document, two counties); Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city-level payloads fill what a county cannot: Will's ward cities and Joliet for per-seat contact, Skokie for trustee districts, and Freeport — the whole city, since Stephenson's county source is a village directory that omits its own county seat) | — |
| `judicial-subcircuit` | Judicial Subcircuit | political | CountyDispatch | Cook County GIS L5 (20 subcircuits) + L27 (municipal districts) · Will County ArcGIS · DuPage County ArcGIS (`Judicial_Subcircuits`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L1) · pre-built `kane-judicial-subcircuits.json` + `mchenry-judicial-subcircuits.json` + `winnebago-judicial-subcircuits.json` (17th) + `madison-judicial-subcircuits.json` (3rd) + `sangamon-judicial-subcircuits.json` (7th) (all PA 102-0693 enacted shapefile) — no Kendall entry: its 23rd Circuit received no subcircuits under the act (nor did the 13th/14th/15th/20th/21st, so the other expansion counties are structurally n/a) | link-only (each card links its circuit's court; Cook adds the Municipal District + courthouse row) | OR of cook/will/dupage/lake/kane/mchenry county coverages; the Winnebago/Madison/Sangamon entries use the subcircuit geometry itself as coverage, so each circuit's secondary counties answer too |
| `county-board` | County Board District | political | CountyDispatch | Cook County GIS L9 · Will County ArcGIS · DuPage County ArcGIS (`County_Board_Dist_new`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L0) · Kane County ArcGIS (`KaneCo_IL_County_Board` L1) · McHenry County ArcGIS (`McHenry_County_Board_Districts` L0) · Kendall County ArcGIS Enterprise (`County_Board_2010` — the CURRENT 2-district map: the post-2020-census reapportionment kept the line, Dec 2021 hearing) · LaSalle **derived** (`lasalle-county-board-districts.json` — the county's own precinct layer dissolved per its 2024+2026 election canvasses by scripts/build_lasalle_board_districts.py; its published board GIS is the superseded 2011-2021 map) · Kankakee self-hosted `k3gis.net` (`BASE/Elected_Officials/1`) · Winnebago WinGIS (`ElectedOfficials/26`, mounted at `/public` not `/arcgis`) · Livingston **derived** (`livingston-county-board-districts.json` — TIGER townships dissolved per the county's published composition; it publishes no GIS) · McLean (`Clerks/MyElectedRepresentatives/1`) · Logan via Tri-County RPC (`Logan_County_Districts_and_Zoning/39`) · Sangamon AGOL (`CountyBoardDistricts2020_WithURLs`) · Madison (`CountyClerk/CBDWS/0`, on `/servera`) · St. Clair (`SCC_voting_districts/2`, on `/server`) · DeKalb AGOL (`District_AreaEffective2022/0`, Esri-JSON fetch — the org's `f=geojson` is lossy on multipart polygons) · Ogle **derived** (`ogle-county-board-districts.json` — Census 2020 VTDs dissolved per resolution R-2021-1106) · Stephenson **part-derived** (`stephenson-county-board-districts.json` — 4 rural districts as TIGER township dissolves, 4 Freeport districts georeferenced from the county's vector-PDF map, the card says so) · Carroll **derived** (`carroll-county-board-districts.json` — TIGER townships per the county's published map) · Lee (`gis.leecountyil.gov/leecogis`) · Whiteside (`ElectionGeography_public/2`, board rows filtered in the loader) · Rock Island (county org, 19 single-member districts) · Woodford **derived** (`woodford-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 2020/21 #005 by scripts/build_woodford_board_districts.py; the county publishes no board GIS) · Boone **runtime-merged** (the county GIS's three per-district MapServer layers — `County_Board_Districts` indexes 0/1/2, each pre-dissolved, verified to tile the county outline — merged and district-tagged by the loader; the features' leftover census-block attributes are read nowhere) · Grundy **derived** (`grundy-county-board-districts.json` — the county's own precinct layer dissolved per the adopted 'Approved County Board Districts (10/12/2021)' map by scripts/build_grundy_board_districts.py; the county GIS publishes no board geometry, and the transcription is proven by the map's own printed populations, all three district totals to the person) · Henry **derived** (`henry-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 21-33 by scripts/build_henry_board_districts.py; the county's viewer is Sidwell Portico, parcels + townships only, and the composition is proven by the adopted map's own two-census population table and live Census POP100, all to the person) · Peoria (county open-data org, `2020_County_Board_Districts/0` — 18 SINGLE-member districts, the app's largest single-member board; chosen over the roster-carrying `ElectoralDistricts/3`, which draws the SAME lines (point-tested 8/8, the area difference projection only), because only this layer carries the per-district 2020 populations that prove it is the adopted 2021-11-30 map) · Tazewell (`ElectionGeography_public…/2` filtered to `County Board Member` and deduped to one polygon per district — the layer repeats a district once per member) · Iroquois (assessor AGOL org, `CountyBoardDistricts_REACH/8` — 4 districts × 4 members) · Adams (county AGOL org, `Web_Voting_Data/2` — 7 districts VERIFIED to tile the county before shipping: 99.997% of the TIGER outline covered, largest pairwise overlap 5e-7 deg², Quincy/Camp Point/Mendon each resolving to exactly one. Four small city districts inside Quincy plus three rural. **No roster** — the county's site is an Akamai hard deny with no Archive capture of its board page, so the card names the district and links the body and guesses no one: rule-4 branch 3, gap adams-county-board-roster) · Cass **derived** (`cass-county-board-districts.json` — Census 2020 voting districts dissolved per the county's own published district table by scripts/build_cass_board_districts.py; its GIS is a Beacon parcel viewer with no public REST. The fleet's first board whose districts are NOT all the same size: 11 members seated 3/3/3/2, so the build balances per MEMBER) · Washington **derived** (`washington-county-board-districts.json` — Census townships dissolved per the whole-township composition the county prints under each district heading by scripts/build_washington_board_districts.py; the county runs NO GIS of any kind, and no township is split, so every district edge is a township edge) · Marshall **derived** (`marshall-county-board-districts.json` — Census townships dissolved per the composition the county prints in the DISTRICT #n headings of its own board roster PDF by scripts/build_marshall_board_districts.py; the county runs no public GIS. Boundary and roster are the SAME TABLE in the SAME document, which is the fleet's tightest binding for the weekly composition drift check) · Mason **derived** (`mason-county-board-districts.json` — Census townships dissolved per the two composition lines the county prints under its roster by scripts/build_mason_board_districts.py; its only mapping surface is a WTH parcel viewer with no feature service) · Fulton (its own ArcGIS at gis.fultoncountyil.gov, `county_board_districts` — 3 districts of FIVE members, tiling 99.98% of the county. NOTE THE LAYER ID: each Fulton dataset is a single-layer hosted FeatureServer at a NON-ZERO id — board 50, precincts 43, polls 12 — so a probe of `/FeatureServer/0` errors on all three and would file this county as publishing nothing. Roster scraped weekly from the county's Members page, which publishes the board twice: a district-grouped photo grid, joined by name to hidden per-member popups carrying the e-mails. A fourth section headed "County Board Chairman" repeats a district member and is read as the Chair ROLE, never a sixteenth seat) · De Witt **derived** (`dewitt-county-board-districts.json` — the county's own precinct layer dissolved per the composition it prints for every board member by scripts/build_dewitt_board_districts.py; the county publishes only a raster JPG. LETTERED districts A-D, the fleet's first) · Stark **from a GOOGLE MY MAPS** (`stark-county-board-districts.json` — the county's entire GIS is one hand-maintained Google My Maps kept by the County Clerk, and the state's pointer file for Stark contains nothing but a link to it. It was unusable for a year on DATE alone, the pointer files predating the 2021 redistricting with no adopting resolution published anywhere reachable; County Clerk Heather Hollis settled it by e-mail on 2026-08-03 — “the board districts and precincts are correct”. 2 districts of FOUR members, the smallest board the layer carries; built by scripts/build_stark_districts.py and cross-checked against the map's own precinct folder, every precinct ≥ 99.99% inside its district) | Cook: live office join (same server); Will: `will-county-board-members.json` (weekly CI); DuPage: `dupage-county-board-members.json` (weekly CI; + countywide Chair); Lake: member + phone/email/office address/district page + newsletter on the boundary GIS itself (live, county-edited; re-verified vs the county directory 2026-07-23; the office-address and newsletter columns were fetched-but-never-requested dead code until 2026-08-01 — the pass-6 finding) + `lake-county-board-roles.json` (weekly CI — the Chair/Vice-Chair tags the GIS lacks, applied only on a name match so a missed reorganization degrades to role-less rows); Kane: member names on the boundary GIS (verified incl. the 2026 D2/D9 appointments) + `kane-county-board-members.json` (weekly CI from the county's SharePoint Board Members list API — party, official office phones, emails, profile links, and the countywide-elected Board Chair; GIS names stay as hover + fallback, cross-checked 24/24 against the roster); Kendall: `kendall-county-board-members.json` (10 members incl. the Chairman — a District 2 member, not a separate countywide seat — phones + emails + per-member profile links; 2026-07 enrichment check re-verified all 10 names 1:1 against the directory's 2026-03 Archive snapshot); McHenry: `mchenry-county-board-members.json` (18 members + the countywide-elected Chairman, phones + emails + per-member profile links; the DuPage countywide-chair shape; 2026-07 enrichment check re-verified all 19 names 1:1 against the directory's 2026-05 Archive snapshot — the county publishes no party or committee data, the one missing phone (D3) is confirmed unpublished at the source, and members' street addresses are residences, deliberately not collected). Both hand-verified 2026-07-23 against the counties' own directories: the counties block ALL automated fetch (direct, real-browser, and the Archive's crawler — SPN2 error:no-request), so the weekly engine-ladder scrapers run green and track the block on standing issues, resuming automation the moment any rung unblocks. LaSalle: `lasalle-county-board-members.json` (weekly CI from the county's own directory — 29/29 names, full 10-digit phones and district-office e-mails, plus the countywide-elected Chairman; the 2015-frozen officeholder columns on the superseded GIS are read nowhere). Kankakee and Winnebago are **rule-4 branch 1** — the member rides the county's own boundary GIS, so no scraper, no roster file and no weekly workflow: Kankakee 28/28 (name, party, phone, e-mail), Winnebago 20/20 (name, party, term year — its address/phone columns are declared and empty on every row, and the richer per-district contact on the county's board page is a backlog scraper, not a guess) . Pass 4's bridge counties: **McLean** 10 districts electing TWO members each, both seats + parties + profile links on the boundary GIS 10/10 (branch 1); **Sangamon** 29, GIS carries the district and a per-district MEMBER URL but no name, so a weekly scraper walks exactly those 29 URLs (29/29 names + parties, 27 e-mails, 22 phones); **Livingston** 3 multi-member districts, boundary AND roster both derived — townships per the county's published composition, members scraped weekly, with an explicit `vacancies` count because the directory lists a "Vacancy" seat that must be counted and never named; **Logan** 6 two-member districts — shipped at the rule-4 branch-3 floor (the county's only roster was a salary publication) until 2026-08-02, when the county's own board page began pairing all twelve members with their districts: a weekly scrape now joins them, 12/12 with phone + e-mail and the county's own Chair/Vice-Chair tags; **Madison** 26, the fleet's RICHEST board source — official/party/term/phone/e-mail/per-district page all on one feature (26/26 name, party, e-mail, URL; 25/26 phone); **St. Clair** 28, branch 1 at its thinnest — name 28/28 and nothing else. Winnebago, McLean, Madison and St. Clair were each spot-checked against their county's own board page before shipping. The northern/western counties (passes 5–5h): **DeKalb** 12 districts × 2 members, weekly roster scrape (party, contact, the Board Chair riding the matching member's row) since the GIS declares member columns and populates almost none; **Ogle** 24 (8 × 3), weekly scrape of the county staff directory (party, phone, e-mail, Chair + Vice Chair); **Stephenson** 8 districts, weekly scrape (a surname guard drops a predecessor's e-mail the county still publishes on one seat); **Carroll** 3 × 3, weekly scrape tolerant of the county's 'Distirct' typo and Roman numerals; **Lee** 4 × 5, weekly positional-parse of the roster PDF (party, e-mail 20/20, the Board Chair cross-checked in prose); **Whiteside** 3 × 9 = 27, branch 1 — members ride `ElectionGeography_public` (27/27 vs the county page; the org's 2019 `MyElectedRepresentatives` service is the stale twin, unused); **Rock Island** 19, weekly roster scrape (party, term, Chair/Vice-Chair); **Boone** 3 × 4, weekly scrape of the county's own board page (12/12 phone + e-mail + term-expiry year, rendered through the shared stale-year gate; role tags verbatim — one Vice-Chairman, no Chairman named anywhere on the page, so none is rendered); **Grundy** 3 × 6, weekly scrape of the county's own board page (18/18 party + since-year + committees verbatim, incl. per-committee Chair/Vice-Chair suffixes + phone + e-mail; the Board Chairman a district member, tagged from his own row); **Henry** 2 × 10 — the fleet's widest multi-member districts — weekly scrape of the county's own CivicPlus directory, which the county itself keys by district (20/20 e-mail, 15/20 phone; no chair marked anywhere, so none is tagged). The pass-7 tranche-1 pair: **Peoria** 18 × 1, weekly scrape whose SPINE is a GIS layer rather than a page — the county's `ElectoralDistricts/3` enumerates district → name, party and member-page URL, and each member page supplies the contact (18/18 party + e-mail, 12/18 phone), cross-checked against the County Board Members index (a third county surface) with a diminutive-tolerant name match; the Chairperson and Vice-Chairperson are badged on their own district rows because Peoria elects both from among the 18. **Tazewell** 3 districts seating 21 + a COUNTYWIDE-elected Chairman (the McHenry shape), weekly scrape of the county's own member pages (21 e-mails, 18 phones, 19 parties) — deliberately NOT the county GIS's member attributes, which are stale (they seat a member the county's own site no longer lists and omit one who has his own page). The scraper follows one stated rule — the website wins where the two surfaces disagree, the GIS fills only where the website is silent — which fills the Vice-Chairman's undistricted row from the GIS and PRESERVES the one district assignment the two still disagree about (the county's own site says D2, its GIS says D3), logging both rather than picking the tidier 7/7/7 arithmetic. **Stark** 2 × 4 = 8, weekly scrape of the county's Elected Officials page (8/8 e-mail + term year, Chair and Vice-Chair badged) — and the e-mails belong to the SEAT rather than the person (`boarddist1-1` … `boarddist2-4`), so contact survives turnover; the builder fails if a personal address ever appears in that slot | OR of cook/will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/winnebago/livingston/mclean/logan/sangamon/madison/st-clair/dekalb/ogle/stephenson/carroll/lee/whiteside/rock-island/woodford/boone/grundy/henry/peoria/tazewell/iroquois/dewitt/washington/cass/marshall/mason/stark/fulton/franklin/clinton/warren county coverages. **Monroe, Randolph, Pike, Putnam, Brown, Calhoun and Schuyler are deliberately ABSENT**: all seven elect their boards COUNTYWIDE, so they have no district geometry to dispatch on and their members ride the COUNTY card instead (`il-county-commissioners.json`, 39 members) — the at-large board posture, per EXPANSION_GUIDE §1.5. Monroe and Randolph run the commission form (3 commissioners each); the tranche-5 four seat 9 / 5 / 7 / 5 and are the first counties in the fleet served with NO dispatch entry of any kind; pass-8 Schuyler (7) joins them. Every one of the seven was proven at-large from a certified election document rather than from a board page that omits districts |
| `ccbr` | Cook County Board of Review District | political | Bespoke | pre-built (PA 102-0012 shapefile) | `ccbr-roster.json` (weekly CI from cookcountyboardofreview.com) | cookCountyCoverage |
| `fire-district` | Fire Protection District | safety | CountyDispatch | Cook (`cook-fire-districts.json`, 40 — pre-built from the Clerk's L17 tax-agency tiling with road voids closed at 75 ft; the tiling's seven double-claimed pairs ship in both districts, scripts/build_parcel_fabric_districts.py) · Will County ArcGIS · DuPage County ArcGIS (`Fire_Protection_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L4) · Kane County ArcGIS (`KaneCo_IL_Districts_Fire` L1, IDOR-coded districts only) · McHenry County ArcGIS (`Fire_Districts` L0, 19 after the loader excludes the 8 'Z NO FIRE DISTRICT' fillers, the municipal Crystal Lake city-fire row, and the overlapping Marengo rescue-squad district — a 70 ILCS 3105 ambulance body, not a fire protection district) · Kendall (`kendall-fire-districts.json`, 10 — pre-built from the parcel-derived tax-code tiling, 170 rows dissolved by name with road voids closed; the old 'hairline no-result gaps' measured as 977 empty voids, and the municipal Joliet rows are excluded at build time) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/10`, 17) · Madison (`MadCo/FireDistrictsWS/0`, 42) · DeKalb AGOL (`PT_Fire_Districts/4`, 18 — Esri-JSON fetch) · Lee (`leecogis`, 22 NG911 service areas) · Rock Island (`rock-island-fire-districts.json`, 17 — pre-built from the county TaxDistricts tiling with parcel-fabric road voids closed at 75 ft, build_parcel_fabric_districts.py) · Sangamon AGOL (`FireDistrictEtc` L2 — 226 fragments grouped per district at load into 29 FPDs + `SPRINGFIELD CORP`, the city's corporate area, whose card states it is served by the city's own Fire Department rather than an FPD) · St. Clair (`CentralSquare/DATA/8`, the county's CAD folder — 44 named departments; disttype/agency declared and 0/44 populated, so the taxing-vs-dispatch caveat rides every card) · Stephenson **georeferenced** (`stephenson-fire-districts.json` — the county's 2014 vector-PDF fire map measured by scripts/build_stephenson_fire_districts.py, hydrography-fitted; 15 named services, 2014-vintage caveat on every card) · Peoria (county open-data org, `Fire_Protection_Districts/0`, 13) · Iroquois (assessor AGOL org, `FireDistricts_REACH/5`, 46) · Boone (`Fire_Districts/0`, 5 — NUMBERED, not named) · Stark **from the County Clerk's Google My Maps** (`stark-fire-districts.json`, 6) · Macon (`macon-fire-districts.json`, 17 — pre-built with road voids closed, 1,318 empty voids measured raw) | Cook: name-only; Will: trustees in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: chief + office contact in GIS attrs; McHenry + Kendall + Kankakee + DeKalb + Lee + Rock Island: name-only; Madison: dept head + address + phone + URL in GIS attrs (the fleet's first contact-bearing fire entry); Sangamon + St. Clair + Stephenson: name-only; **Peoria: name + the district's OWN WEBSITE** — the first fire tiling in the fleet whose source publishes a link, so the card's footer links the district that answers the call rather than the county (populated on some rows and null on others; no officer or address column exists — recorded as `peoria-fire-park-library-contact`) ; **Iroquois: name + the county's own DISCREPANCY note** — its source carries a column recording where the county's two sources disagree ("Parcel Data shows this in Milford Fire District, but map shows Cissna Park"), populated on 20 of 46, and the card surfaces that text rather than a false certainty; **Boone: NUMBER only, and the card says so** — the layer carries a lone `district` column, and the numbering was confirmed as the county's real identifier by County Clerk Amy Ohlsen, who supplied names and then volunteered that she had “just done a google search to get these names” while “when we complete tax extensions, it is just 1-5”, so the names are not used and the numbers are (gap boone-fire-names, narrowed rather than closed); **Stark: name + AMBULANCE** — the only fire entry in the fleet whose source names who responds with an ambulance, and it is not always the fire department (3 districts Stark County Ambulance, Bradford by Bradford Rescue Squad, Kewanee Rural and Neponset their own) | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/lee/rock-island/sangamon/st-clair/stephenson/peoria/iroquois/boone/stark/macon county coverages |
| `dupage-county-special-police` | DuPage Special Police District | safety | Polygon | DuPage County ArcGIS (`Special_Police_Districts_`, "Real Estate Tax Code polygons") | link-only (elected DuPage County Sheriff; unincorporated-area police-tax district) | dupageCountyCoverage |
| `park-district` | Park District | geography | CountyDispatch | Cook County GIS L23 (Clerk park tax-agency tiling, incl. the Chicago Park District) · Will County ArcGIS · DuPage County ArcGIS (`Park_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L11) · Kane County ArcGIS (`KaneCo_IL_Districts_Park` L1) · Kendall (`kendall-park-districts.json`, 5 genuine districts — Fox Valley/Joliet/Oswegoland/Plainfield/Sandwich; pre-built from the 65-row tax-code tiling with road voids closed, 578 empty voids measured raw) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/5`, 4) · Madison (6) · DeKalb AGOL (`PT_Park_Districts/9`, 6 — Esri-JSON fetch) · Rock Island (`rock-island-park-districts.json`, 1 — Cordova, pre-built with road voids closed) · Peoria (county open-data org, `Park_Districts/0`, 4) · Macon (`macon-park-districts.json`, 6 — pre-built with road voids closed, 556 empty voids measured raw) · Stark **from the County Clerk's Google My Maps** (`stark-park-districts.json`, 2 — LaFayette and Bradford, together ~9% of the county) — McHenry: recorded gap, publishes facilities not district boundaries | Cook: name-only; Will: commissioners in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only; Peoria: name + the district's own website (footer link); **Stark: name only, deliberately** — that folder of the county's map carries a `Fire Department` column left over from whoever built it by copying the fire layer, and it is confidently wrong rather than blank (“LaFayette Park District” claims a fire department), so the builder never carries it forward and nothing reads it — the Freeport/Peoria-REPNAME posture ; **Macon: name only, space-stripped as published** (see the library row) | OR of cook/will/dupage/lake/kane/kendall/kankakee/madison/dekalb/rock-island/peoria/stark/macon county coverages |
| `library-district` | Library District | geography | CountyDispatch | Cook County GIS L20 (Library Tax District) + L19 (Library Fund) · Will County ArcGIS (`Library_District`) · DuPage County ArcGIS (`Library_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L8) · Kane County ArcGIS (`KaneCo_IL_Districts_Library` L1) · McHenry County ArcGIS (`Library_Districts` L0, 13 after the loader excludes 6 'Z_None' fillers + the lone municipal Crystal Lake city row) · Kendall (`kendall-library-districts.json`, 9 bodies incl. the municipal Joliet/Yorkville city-library funds — the tiling records EVERY library taxing body, the Cook-style complete shape, so its municipal rows stay; pre-built from 145 tax-code rows with road voids closed, 1,158 empty voids measured raw) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/3`, 8) · Madison (18) · DeKalb AGOL (`PT_Library_Districts/7`, 13 — Esri-JSON fetch) · Rock Island (`rock-island-library-districts.json`, 9 named districts — pre-built with road voids closed at 75 ft; the blank-named tenth source row, a stray byte-identical copy of the UNITED TWP HIGH 30 school polygon and not an un-districted remainder, is asserted and excluded at build time; the 60 ft snap still answers perimeter roads and refuses between-district seams) · Peoria (county open-data org, `Library_Districts/0`, 10) · Macon (`macon-library-districts.json`, 10 — pre-built with road voids closed; the upstream 'Join_Dissolved' dissolve kept 960 parcel voids) · Stark **from the County Clerk's Google My Maps** (`stark-library-districts.json`, 6 — two of them, Kewanee and Williamsfield, seated in a NEIGHBOURING county and reaching across the line, which is why the county drew them) | Cook: agency name + a Type row distinguishing district vs municipal fund; Will: trustees in GIS attrs (sparse); DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; McHenry + Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only; Peoria: name + the district's own website (footer link); Stark: name-only; **Macon: name only, and the names ship EXACTLY as the county writes them** — its labels are space-stripped (`MtZion`, `HopeWelty`, `IlliopNian`, `MarrowBone`), and re-inserting the spaces mechanically would produce “Marrow Bone” and “Illiop Nian”, which are not those districts' names. Recorded as macon-district-name-formatting rather than guessed | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/rock-island/peoria/stark/macon county coverages |
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
| `county-precinct` | Voting Precinct | geography | CountyDispatch | Cook County GIS (`precinctHistorical` L0, the Clerk's current suburban fabric, 1,430 — same geometry as Socrata `k7sw-w3b8`) · Will County ArcGIS `Precincts_2022` · DuPage County ArcGIS `Precincts_2024` (current 600-precinct map) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L7, 431) · Kane County ArcGIS (`KaneCo_IL_ElectionsPrecincts` L1, 292 — township named from the clerk's own Maps-page prefix pairing, election-day polling joined 292/292 from `KaneCo_IL_Elections_PollingPlaces` and labelled with its Election field, 2026-08-02) · McHenry County ArcGIS (`Precincts` L0, 223) · Kendall County ArcGIS Enterprise (`Voting_Precincts_and_Polling_Places` L1 `status='A'`, 78 — township names derived at load from the county's own townships layer, the assigned polling place joined by GlobalID from L0) · LaSalle self-hosted (`PollingPlaceLocator/1`, 119 + polling points joined 119/119 on `USER_Precinct`) · Kankakee `k3gis.net` (`BASE/Elected_Officials/0`, 59, name-only) · Boone (37, polling place carried ON the feature) · Grundy (40, polling joined 38/40 on `POLLINGID`) · Macoupin Socrata (`ab79-cnsh`, 45 — the current 2022-2032 fabric, refreshed upstream 2025-11; polling joined 45/45 from the clerk's own Socrata polling dataset (`rc5v-ajnf`) by deterministic label expansion, 2026-08-02) · Madison (191, `pollingid` GlobalID join 191/191) · St. Clair (`SCC_voting_districts`, 150 — polling is a recorded gap) · Winnebago WinGIS (`WardsAndDistricts/7`, 94, county-clerk jurisdiction only — Rockford runs its own election commission) · DeKalb AGOL (`Precincts/1`, 69) · Ogle **from the county GIS Coordinator's own shapefile** (`ogle-precincts.json`, 51 — the county publishes none, so this was supplied by e-mail 2026-08-03 and is archived under `data/source/raw/`; township on the feature, board district by SPATIAL join because the 2021 resolution names bare townships where the shapefile numbers them; no polling place, its polling dataset being points with no precinct key) · Lee (46) · Whiteside (60 — polling joined 56/60 from the county's own layer, and the remaining four filled from `whiteside-precinct-polling.json`, two locations the County Clerk supplied — name and street address — because the county's published list omits their facility ids; consulted only where the county's own layer has no match, and the card says where the location came from, so all 60 now show a polling place and an address) · Rock Island (120) · McLean (`Clerks/PollingPlaces` L1, 141 — polling joined 141/141 by POLLINGID from L0) · Logan (TCRPC `Logan_County_Districts_and_Zoning/40`, 29 township-named — the clerk's HTML polling table ships as `logan-precinct-polling.json`, joined 29/29) · Sangamon AGOL (`ApprovedPrecincts20231012`, 166 — polling joined 165/166 by POLLID from `ElectionPollingAndPrecincts` L0) · Carroll (TIGERweb Census-2020 VTDs live, 22 — the county did not re-precinct; the clerk's polling notice ships as `carroll-precinct-polling.json`, joined 22/22) · Woodford (TCRPC election service, 37 — polling joined 37/37 on the numeric polling reference, the precinct's own name cross-checked in the polling row's grouped label) · Peoria (county open-data org, `2020_Voting_Precincts/0`, 116 — polling joined on POLLINGID against its 55 published locations, many-to-one by design) · Tazewell (`ElectionGeography_public…/1`, 82 — polling joined on POLLINGID against the locations layer's GLOBALID, 82/82. It joined on `facilityid` from 2026-08-02 until 2026-08-20, which is where this county's three-week correspondence with its Clerk's office came from: six "orphan" precincts and three "disagreements" that were all artifacts of the wrong key. Deputy Clerk Reynolds' "we are not seeing the issues you are listing" was right. Measured: facilityid resolves 75/82, sends THREE precincts to the wrong building — Washington 05 and 12 to Spring Lake Town Hall in Manito, twenty miles away in another township — and is not even unique on the locations layer, where 48 names both Cincinnati Fire Station and Pekin Bible Church; pollingid→globalid resolves 82/82 and agrees with the Clerk's own countywide listing 9/9 on every precinct that had been in dispute. NO facilityid fallback, because falling back would reinstate those three wrong buildings. The clerk-supplied supplement this county needed for three weeks is retired) · Iroquois (`ElectionGeography_public/1`, 37 — polling joined on pollingid against 32 sites) · Adams (`Adams_County_Voting_Precincts_view/0`, 92 — the fleet's least-joined precinct card: the county's own feature carries the polling place (92/92) AND the precinct's board district, so neither is a spatial join nor a name match. Quincy's ward rides the same feature, trimmed and shown only where it is non-blank) · Monroe (`VoterPrecinct/0`, 25 — polling joined 25/25 by expanding the polling layer's comma-separated precinct list, every token a bare integer; NO board-district row, the county elects at large) · Randolph (`VotingPrecincts/1`, 35 — identity only: pollingid is declared and null on all 35, and the county elects at large, so this is the fleet's thinnest precinct card and says only what the county publishes) · De Witt (Sidwell/Magnasoft org, `ElectionPrecincts_DeWittIL/0`, 23 — the same fabric its board districts are dissolved from, so the board-district row comes from the derived boundary; no polling published) · Fulton (`voting_precincts` layer 43, 44 — each precinct carries its own polling place NAME, ADDRESS and TOWN on the feature, 44/44, so neither is a join and the county's separate polls layer is never fetched; the Adams and McDonough shape) · Stark **from the County Clerk's Google My Maps** (`stark-precincts.json`, 9 — the county's eight congressional-survey townships with Toulon split east/west, which is why they are drawn as near-rectangles and why that is correct rather than approximate; no polling published)  · Macon (its AGOL org's `ElectionGeography_public` layer 1, **64** named precincts with the polling place joined 64/64 on facilityid against 29 voting locations — the county's `fulladdr` already ends in the municipality on all 29, so the loader trims the trailing CRLF the service returns and does not append the city twice. NO county-board row: Macon's five board shapes carry no district number at all, see `macon-county-board-labels`) · Stephenson **georeferenced from the County Clerk's own two adopted maps** (`stephenson-precincts.json`, 36 = 20 rural + Freeport 01-16). The app recorded for a year that the county published no current precinct boundaries; it does, as vector PDFs on the Clerk's own Elections page, and Clerk Jazmin Wingert pointed at them on 2026-08-03 in reply to a records request. scripts/build_stephenson_precincts.py measures them and proves the transcription twice before writing: the 36 printed populations total 44,630, the county's live Census 2020 count to the person, and the Freeport sixteen are the SAME polygons the board-district map draws, read off a different document and georeferenced independently — 16/16 land in the district the board build assigns, at IoU 0.996 or better. That cross-check earned its keep immediately: it failed on the first run, and the culprit was this build filling holes the PDF's declared EVEN-ODD fill rule says are holes, not the shipped board file. Township on the feature, board district by SPATIAL join; no polling place — the Clerk's page links a countywide polling list whose link is dead at the source. PRECINCT LINES ARE NOT TOWNSHIP LINES here: the rural precincts reach into Freeport township and take 329 people with them, which the populations and the geometry agree on · Calhoun (`calhoun-precincts.json`, 5 — the county runs no mapping system, so its five precincts are DISSOLVED from the seven Census 2020 voting districts, a composition the county names in the precincts' own titles (Belleview-Hamburg, Hardin-Gilead) and its certified returns witness either side of the 2022-2024 merge; needed `check_fabric_composed` because the Jasper test's name-for-name comparison is the wrong gate for five precincts over seven voting districts) · Morgan (the county's OWN live layer, `VotingPrecincts/0` on its GIS Coordinator's org, 27 — polling place AND street address on every feature, so neither is a join; currency proven against the county's certified returns, 27 of 27 precincts and 25 names matching exactly, the two differences being the county's own short forms). NEITHER CALHOUN NOR MORGAN CARRIES A BOARD-DISTRICT ROW, and that is permanent: both elect their boards at large, so there is no district for a precinct to belong to — they are the first two counties in the fleet whose dispatch entry exists for precincts alone | County Board district via spatial join (Cook: Commissioner District; Kane: carried on the features); Kendall also shows the county's own polling-place assignment; each card links its county clerk | suburban-Cook (in Cook AND NOT Chicago — city precincts are the BOE's `ward-precinct` layer) OR will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/boone/grundy/macoupin/madison/st-clair/dekalb/lee/whiteside/rock-island/mclean/logan/sangamon/carroll/woodford county coverages, plus peoria/tazewell/iroquois/monroe/randolph/dewitt/stark/ogle/fulton/stephenson/macon/calhoun/morgan, plus Winnebago-outside-Rockford (subOf `township`) |
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

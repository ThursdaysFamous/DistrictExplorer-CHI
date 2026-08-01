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
      "blocker": "No county-published roster exists. The clerk site publishes no directory, and the county GIS Municipalities layer declares telephone/website/email columns but populates none of them (measured 0/21). Re-tested 2026-07-31: the clerk site, yearbook rungs and COG still publish nothing (the county GIS re-measure was egress-blocked from the test client, with nothing indicating change).",
      "wanted": "Any county- or COG-level directory naming mayors/village presidents and boards — ideally with a stable URL that is republished after each election."
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
      "blocker": "No Lake County body publishes municipal officeholder names — re-verified 2026-07-31: the county GIS Municipalities layer carries hall address/phone/website only (schema and 5-feature sample re-read; last edited 2025-06); the Lake County Municipal League's per-municipality pages repeat the same hall contact with no names, and its board page names only the League's own officers; the Council of Mayors membership PDF lists municipality names only. lakecountyil.gov itself now fronts a Cloudflare challenge to datacenter clients (the solvable class, not a hard deny).",
      "wanted": "A Lake County clerk or council-of-governments directory naming heads of government — the DuPage DMMC directory is the shape that would work."
    },
    {
      "id": "blocked-crawlers",
      "concept": "Roster refresh",
      "area": "McHenry and Kendall",
      "counties": [
        "mchenry",
        "kendall"
      ],
      "kind": "blocked",
      "layer": "county-board",
      "summary": "Two county directories refuse every automated fetch, so their board rosters are hand-verified rather than refreshed weekly.",
      "blocker": "Hard Akamai WAF denies, re-measured 2026-07-31: both counties' board-directory and document URLs return 403 with an x-reference-error and small static bodies to every datacenter client. What changed: the Internet Archive now holds verified-content 2026 captures of BOTH board directories (McHenry 2026-05-20, all districts and member links; Kendall 2026-03-13, all 10 member slugs), so an Archive-rung refresh is newly viable for the board rosters — while McHenry's municipal-yearbook page's newest capture remains 2025-03-06 and Kendall's municipal PDF has never been archived at all (measured via CDX, both case variants). Joliet's block is now recorded separately (joliet-municipal-contact).",
      "wanted": "A machine-readable feed for either directory, or any mirror the sources permit crawling; the board directories' 2026 Archive captures are fresh enough to re-verify the shipped rosters."
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
      "blocker": "The DMMC directory prints numbers without an area code and states no default, so rendering them would mean guessing which area code to dial. Re-verified 2026-07-31 against the current 25-26 directory (revised 5.12.2026): still area-code-less 7-digit numbers, no stated default, and DuPage County itself still publishes no municipal directory.",
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
      "summary": "Aurora's 12 council members render with correct wards but no phone or e-mail — the reachability blocker is resolved and a per-seat scrape is pending.",
      "blocker": "Re-tested 2026-07-31 and overturned: Aurora relaunched on www.aurora.il.us (aurora-il.org now 301s there) and the new site serves plain clients with no challenge. All 12 per-seat alderman pages publish a per-seat @aurora.il.us e-mail plus the Alderman's Office phone. The ward FeatureServer still carries no officeholder fields, so contact comes from the 12 pages, not the GIS.",
      "wanted": "Nothing further from readers — a scrape of the Meet-Your-Aldermen per-seat pages is pending (see the build-ready ledger)."
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
      "id": "macoupin-county-board-districts",
      "concept": "County board districts",
      "area": "Macoupin County",
      "counties": [
        "macoupin"
      ],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Macoupin's 9 two-member board districts do not resolve — only its precincts do.",
      "blocker": "Re-tested 2026-07-31 and half-overturned: the 2022-2032 map WAS adopted — Ordinance O-2021.06 (2021-11-09, 18-0) is machine-readable on the county's code site, and the clerk's Map Room publishes vector-PDF maps of all nine districts — so the 'still titled proposed' clause is retired. The precinct dataset (ab79-cnsh) still carries no district column, so geometry would be a derived build: townships dissolved per the ordinance, with Cahokia and Shipman split along the published 2005-2021 precinct polygons the ordinance's amendments are written in. The entry's 'roster in hand' claim is corrected too: the Socrata directory (rxtc-9j2k) froze 2015-11-03, and the current roster sits behind the clerk's JS-rendered SOE component (see macoupin-municipal-officials).",
      "wanted": "District polygons or a machine-readable precinct-to-district table from the county — or acceptance of the derived township+precinct-split build the adopted ordinance now supports, plus a resolved roster source."
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
      "blocker": "The county publishes 103 polling places, but keys them by a COMBINED human label rather than a precinct id — \"Belleville9,10, 12 & 16\", with non-breaking spaces and inconsistent zero-padding against the precinct layer's \"Belleville 9\". Joining them means parsing prose into a set of precincts, which would silently mis-assign a polling place whenever the phrasing changes. Re-tested 2026-07-31: the 103 polling places are still keyed only by the combined labels; no precinct-keyed column has appeared.",
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
      "summary": "Madison County's 31 municipal wards across six cities are published but not shipped — the county polygons name nobody, though the names now exist first-party.",
      "blocker": "MadCo_Wards declares OFFICIAL, ADDRESS, PHONE, EMAIL and URL on every row and populates every one of them on 0 of 31 — re-measured 2026-07-31 on a layer that is otherwise actively maintained (edited 2026-05). What changed: the names are now sourceable. Alton (7 alderpersons with ward + phone + e-mail), Granite City (10 across 5 wards with e-mail) and Edwardsville (7) publish ward-keyed rosters on their own sites, and the East-West Gateway 2026 Public Officials Directory covers all six polygon cities. The six ward cities are Alton, Edwardsville, Granite City, Madison, Troy and Venice — Collinsville elects at-large (this entry's original city list corrected).",
      "wanted": "Nothing further from readers — the ward-keyed rosters SHIPPED 2026-08-01 in municipal-officials.json (Alton 7, Edwardsville 7, Granite City 10, Troy 8, Venice 8 seats); what remains is the ward-layer build that joins them to the MadCo_Wards polygons (see the build-ready ledger's ward tranche)."
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
      "blocker": "WinGIS publishes an officeholder layer per municipality, but for these two it carries the council seats only — there is no mayor/president layer to read. Every other Winnebago municipality has one. Re-enumerated 2026-07-31: still council-seats-only for both municipalities; every other Winnebago municipality layer still names its head of government.",
      "wanted": "A Loves Park mayor and a Machesney Park village president, from either city's own site or a WinGIS layer if the county adds one. The councils are already complete; only the head of government is missing."
    },
    {
      "id": "dakota-village-president",
      "concept": "Municipal officials",
      "area": "Village of Dakota",
      "counties": [
        "stephenson"
      ],
      "kind": "no-source",
      "layer": "municipality",
      "summary": "Dakota shows its full board, clerk and treasurer but no village president.",
      "blocker": "The county's Cities & Villages directory lists no president for Dakota. One Dakota row carries a resident's name with a BLANK office cell, which is very likely the missing seat — but the county publishes no title against it, and filling one in would be a guess. Every other village on the page names its president. Re-measured 2026-07-31: Dakota is still the only village block without a named president; the blank-office row persists.",
      "wanted": "A Dakota village president from the county directory once it names one, or from any village-published list. The rest of the board is already complete."
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
      "blocker": "Rockford runs its own Board of Election Commissioners, so the county's 94-precinct tiling stops at the city line — measured, not documented: 130 of 131 uncovered grid samples fall inside the TIGER Rockford polygon. The clerk publishes a city-precinct committeeperson PDF, so the precincts exist; no boundary layer for them does. Re-tested 2026-07-31: unchanged — the county layer remains the only precinct geometry (94, township-coded), and the BOEC's 2026 polling list shows 89 city precincts across 14 wards with still no boundary layer behind them.",
      "wanted": "Rockford Board of Election Commissioners precinct polygons, or a city precinct layer on WinGIS. This is the Chicago/suburban-Cook split repeating in a smaller city, and the app already models that shape."
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
      "summary": "Only Cook's and Lake's board cards name an office you can visit — no other county publishes one.",
      "blocker": "Corrected in the 2026-07-31 validation pass: of the 26 county-board entries, Cook DOES ship a per-commissioner 'District Office' group (measured live: 17/17 office addresses on the county's electedOfficials table, map-pinned on the card), so the entry's old 'no county board card names an office' claim was wrong. Lake's card renders the shared county-building office ('18 N County St, Waukegan', 19/19 on its GIS) plus the district newsletter link as of 2026-08-01 — the loader had never requested those columns, the pass-6 dead-code finding, now fixed. No other county in the app publishes a board office address; Madison publishes member RESIDENCES, which were removed rather than presented as somewhere to go (LaSalle's did too, on the superseded layer its suppressed entry used to read).",
      "wanted": "A per-district OFFICE address, or confirmation that a county's board members hold office hours somewhere specific. County boards mostly meet at one building, so a per-county board-office address on the card — the Lake shape — is probably the honest fix."
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
      "blocker": "The code is exactly what the county publishes: its board-district listings and its committeeperson lists both print “AF 01”, “DK 15”, “SG 01”, and no page or dataset expands the prefixes. Nineteen townships share a two-letter namespace where several start with the same letters (Sandwich, Shabbona, Somonauk, South Grove, Sycamore), so the expansion cannot be inferred without guessing. The township layer directly above precinct in the nest does answer which township a point is in. Re-tested 2026-07-31: the yearbook, the polling list and the voting-locations layer all still print bare codes; no expansion list has appeared.",
      "wanted": "Any DeKalb County list that pairs a precinct code with its township or full precinct name — a clerk's precinct table, a polling-place list carrying both, or a legend on the precinct map."
    },
    {
      "id": "bureau-county-board-districts",
      "concept": "County board districts",
      "area": "Bureau County",
      "counties": [],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Bureau publishes its 18 board members and their parties but draws its 18 districts nowhere the public can reach.",
      "blocker": "Sharpened 2026-07-31: the adopted 18-district map IS publicly downloadable after all — the Nov 9, 2021 board minutes and agenda packet on the county's IQM2 meeting portal record its adoption 23-0 and carry the map — but every map page is a 300-dpi JPEG scan (zero vector content, zero extractable text), with Princeton and Spring Valley insets splitting those cities at individual-street level, so no township or precinct dissolve can reproduce the lines and the county publishes no precinct geometry to rebuild them from. The county still runs no GIS of any kind, and its board page still lists 16 of the 18 seats (districts 9 and 15 are the missing two).",
      "wanted": "Vector geometry for the 18 districts, or the plan's precinct/street-range composition plus precinct geometry to rebuild it. The adopted raster in the IQM2 packet is now the authority to check any submission against."
    },
    {
      "id": "henry-county-precincts",
      "concept": "Voting precincts",
      "area": "Henry County",
      "counties": [
        "henry"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Henry County's voting precincts exist only as raster per-township PDF maps — no vector geometry is published anywhere.",
      "blocker": "Measured 2026-08-01 on both ends: the county's own elections page (henrycty.com/244/Precinct-Maps) lists ~21 per-township precinct-map PDFs (Nov 2021 vintage, one link text mislabeled), and the ISBE holds the same rasters; no precinct layer exists in the county's Sidwell-hosted GIS (Portico ArcGIS Enterprise — parcels and townships only) or its AGOL org. The board-district layer shipped anyway because Ordinance 21-33 composes districts from whole TOWNSHIPS, which are published as vector — precincts have no such workaround.",
      "wanted": "Henry County's precinct boundaries countywide in any vector form (shapefile, GeoJSON, or an ArcGIS service), plus a polling assignment if published."
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
      "summary": "Lee's 13 municipalities keep the identity-only card — the county publishes no municipal officeholders anywhere.",
      "blocker": "All four sourced rungs are exhausted. The Clerk runs no elected-officials database; neither the Clerk nor the Election Information page links a yearbook or municipal directory (the site's only /directory.aspx is county STAFF); Blackhawk Hills Regional Council, the area's COG, publishes no member directory; and the county GIS's Municipalities layer is name-only — CORP_NAME on all 13 and no contact column at all, unlike Lake's, which at least carries hall address and phone.",
      "wanted": "Any Lee County list pairing a municipality with its mayor/president — a clerk's yearbook, a COG membership directory, or contact attributes on the county's Municipalities layer. Scraping 13 heterogeneous village sites is explicitly not the answer (source ladder rung 5)."
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
      "summary": "Whiteside's 11 municipalities keep the identity-only card, even though the county publishes an unusually rich elections GIS.",
      "blocker": "The county's ArcGIS org carries precincts, polling places, electoral districts and a MyElectedRepresentatives service — but every one of them stops at the county board and the state/federal offices. No municipal layer exists. The Clerk publishes no yearbook or municipal directory, and Blackhawk Hills Regional Council publishes no member list. A county can have the best election GIS in the served area and still name no village president.",
      "wanted": "A Whiteside municipal-officials layer on the county's own ArcGIS org (it would fit the Esri Elections pattern the county already runs), or a clerk-published directory."
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
      "summary": "Two of the five orphaned precinct polling assignments are now published; only Coloma 9's remains missing.",
      "blocker": "Re-measured 2026-07-31: the shipped Voting Locations layer still skips facility ids 22, 26 and 32 (join 55/60), but two sibling layers on the same county org now publish id 22 (Self Help Enterprises, Sterling) and id 26 (Winning Wheels, Prophetstown) with current 2026-primary data, so a supplement join can reach 59/60. Facility 32 — Coloma 9's polling place — appears on none of the three services.",
      "wanted": "Facility 32 on any published county layer finishes it; the sibling-layer supplement join for 22 and 26 is meanwhile a build candidate."
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
      "summary": "Stephenson's four Freeport Township districts are traced from the county's published map, not published data — their lines are accurate to about 20 metres, and the card says so.",
      "blocker": "Stephenson publishes no precinct geometry. Census 2020 carries FREEPORT 1-18; the county re-precincted afterwards and now runs Freeport 01-16, which is what districts B-E are drawn from, so the census cannot draw those lines. The county runs no GIS server, has no ArcGIS Online presence beyond third-party research layers, its assessment office points at WinGIS (which serves the county an address locator and no boundary layers), and the Illinois SBE's GIS viewer is down. The four districts therefore come from the vector PDF of the county's adopted map, georeferenced against TIGER; the fit lands the map's own hydrography — data the fit never saw — within 50 m for 98.9% of its vertices, median 15.7 m. The county's four RURAL districts (F-I) are whole townships and are exact.",
      "wanted": "Freeport Township's current 16 precinct boundaries in any vector form (shapefile, GeoJSON, KML or an ArcGIS service). That one file would replace the traced geometry with published data and let the georeferencing script be deleted."
    },
    {
      "id": "jo-daviess-county-board-districts",
      "concept": "County board districts",
      "area": "Jo Daviess County",
      "counties": [],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Jo Daviess County's 17 board districts cut ACROSS precincts along roads, and nothing publishes those lines.",
      "blocker": "The county publishes the composition of all 17 districts — now in PROSE on its County Board page, member by member, not just as the titles of 17 per-district PDFs — but 14 of the 17 are made of PARTS of precincts, and District 10 is a fraction of a single one (\"Part of West Galena I precinct\"). Its own GIS memo of 2021-12-02 says why: “If one of those boundaries needed to be split I used roads.” Only districts 1, 3 and 16 are whole precincts, so even precinct geometry would not finish the county. Re-tested 2026-07-31 and every half of this still holds: the GIS at gismaps.jodaviess.org is a vendor gwmpub.aspx (Portalsdk12) viewer with no REST endpoint, and the countywide district map is a RASTER export (32 embedded images, 261 characters of text — the title and legend), so the vector-PDF route that built Stephenson's Freeport districts does not apply. NOTE FOR THE NEXT PASS: the county has moved to jodaviesscountyil.gov; the old jodaviess.org answers every path with its home page, which makes a 200 look like a hit.",
      "wanted": "The county's GIS department SELLS this data — it runs a paid subscription mapping site and a \"Digital Data Order Form\", so the district shapefiles demonstrably exist and are simply not public. The unlock is therefore a licensing/records question rather than a technical one: a public release, a records request, or the written legal descriptions the 2021-12-02 memo says were prepared. The roster half is already published (all 17 members with party and term)."
    },
    {
      "id": "whiteside-municipal-wards",
      "concept": "City council district",
      "area": "Sterling, Rock Falls, Morrison, Prophetstown, Erie and Fulton",
      "counties": [
        "whiteside"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Whiteside publishes ward polygons for six of its municipalities, but the layer predates the redraw it would need to reflect.",
      "blocker": "PrecinctWardMap layer 0 carries 22 wards across Sterling (4), Rock Falls (4), Morrison (4), Fulton (5), Prophetstown (3) and Erie (2), named and complete. Its dataLastEditDate is 2019-11-05 — BEFORE the 2020 census, and municipal wards are redrawn on that cycle. Shipping it would answer \"which ward am I in\" with a pre-redistricting line and no way for a reader to tell. Rock Island's Moline and Silvis layers were shipped instead precisely because theirs were edited in 2022, after the redraw. Re-tested 2026-07-31: the layer's vintage is still 2019-11-05 and no county or municipal statement about (not) redistricting was found. (Kind corrected from data-quality in the 2026-07-31 validation pass: nothing ships here, so this is a missing-source gap, not a hole in a shipped layer.)",
      "wanted": "A post-2020-census refresh of Whiteside's ward layer, or confirmation from the county that these six municipalities did not redistrict. The geometry is already published and would ship the day its vintage is current."
    },
    {
      "id": "mercer-county-board-districts",
      "concept": "County board districts",
      "area": "Mercer County",
      "counties": [],
      "kind": "no-source",
      "layer": "county-board",
      "summary": "Mercer publishes its ten board members and their districts but draws the five districts nowhere.",
      "blocker": "The county runs no GIS — parcels go to a third-party tax vendor (govtechtaxpro), and the only mapping results for the county are commercial aggregators, not anything it publishes. Its own board page says \"Mercer County Board Districts, Map and Contact List are found in the Document Section\", and they are NOT there: the public document index carries 90 PDFs across eight folders (Assessments, Audits & Budgets, Board of Review, Contracts, Forms, Ordinances, Taxes, Zoning) and none is a district map, composition list or reapportionment ordinance. The elections page's 109 PDFs are canvasses and candidate packets. Re-tested 2026-07-31: the board page still points at the Document Section and the documents are still not there — the index now even carries a 'County Board' category, and it is empty.",
      "wanted": "Mercer County board-district geometry, or a composition naming the townships or precincts in each of the five districts — the document its own board page already claims to publish. The roster is published and rich (5 districts electing two members each, with party, home town, term expiry and the Chairman flagged)."
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
      "blocker": "Neither county publishes the geometry anywhere. Ogle's whole ArcGIS Online org was enumerated — 91 services, all cemeteries, bike routes, COVID points and survey forms; its parcel viewer is a Beacon/Schneider product with no REST endpoint. LaSalle runs its own ArcGIS Server and every service on it was listed: zoning, flood, wetlands, parcels, tax maps, corporate boundaries, board districts and the polling-place locator, and no taxing-district layer at all. Both counties DO publish the districts' names and rates — Ogle's yearbook carries a tax-valuation table for park and fire districts — but a name is not a boundary.",
      "wanted": "Fire protection, park and library district boundaries from either county in any GIS or shapefile form. The property-tax tiling both counties already maintain to extend those levies is exactly the layer DeKalb, Kankakee and Rock Island publish."
    },
    {
      "id": "ogle-precincts",
      "concept": "Voting precincts",
      "area": "Ogle County",
      "counties": [
        "ogle"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Ogle's voting precincts are not shipped, even though the app already dissolves 2020 versions of them into the county's board districts.",
      "blocker": "The county publishes no precinct geometry — only a 51-page PDF map atlas and a points-only Polling_Locations service. The Census 2020 voting districts ARE available and build_ogle_board_districts.py uses them, but they are the fifty-two precincts of 2020 and the county now runs fifty-one: it has since retired Forreston 3. That cannot move a board-district line (Forreston 1, 2 and 3 are all in District 7, so their union is unchanged), but it would put a precinct on a card that no longer exists, and nothing published says where its territory went.",
      "wanted": "Ogle's CURRENT precinct boundaries in any GIS or shapefile form, or a county statement of how Forreston 3 was absorbed. The polling places are already published and would join on the precinct name."
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
      "summary": "Byron and Polo elect by ward and their aldermen are already on the Municipality card, but neither city's wards are mapped.",
      "blocker": "Neither city publishes ward geometry. The ArcGIS Online catalogue returns nothing for either, the county's own org holds no ward layer, and neither cityofbyron.com nor poloil.gov links a GIS or a ward map of any kind — not even a raster. The seats themselves are not the problem: the Ogle clerk's yearbook already gives Byron's seven aldermen across four wards and Polo's six across three, and they ship today on the Municipality card.",
      "wanted": "Byron's four and Polo's three ward boundaries in any GIS or shapefile form. The rosters are already in data/app/municipal-officials.json and would name the seat the day the geometry arrives."
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
      "summary": "Three of LaSalle County's four ward-electing cities are unmapped; only Mendota's wards ship.",
      "blocker": "La Salle publishes a ward map, but as a RASTER — a single PNG on its city-profile page, with no polygons to read. Peru and Earlville publish nothing: no GIS link on either city site, and nothing in the ArcGIS Online catalogue. The county's own ArcGIS Server carries corporate boundaries but no wards. Mendota is the exception that shows the shape this wants — its own ArcGIS org, four ward polygons, edited 2022-12 — and it shipped.",
      "wanted": "Ward boundaries for La Salle (4), Peru (4) and Earlville (3) in any vector form. All three cities' aldermen are already in data/app/municipal-officials.json from the county clerk's directory, two per ward, so each card would name its seats immediately."
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
      "blocker": "The county yearbook prints Sarah Quirk twice for Hinckley — once as Village President and again as a Trustee. An Illinois village president is elected to that office separately and cannot hold a trustee seat at the same time, so one of the two rows is stale and the scraper keeps only the head-of-government row (the more specific claim). Which trustee actually holds the sixth seat is not published anywhere the county or the village puts online.",
      "wanted": "A corrected Hinckley entry in the DeKalb County yearbook, or a village board roster on hinckleyil.com. Every other DeKalb municipality's board is complete."
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
      "summary": "Boone's park and library districts are not shipped — the county publishes no boundary for either.",
      "blocker": "Re-enumerated 2026-07-31: the county REST server (56 services across 12 folders) and the BooneGIS ArcGIS Online org (360 items) carry no park- or library-district tiling — every 'park' item is a conservation-district facility map. The districts exist on paper: the clerk's yearbook prints the Belvidere Park District commissioners and the Ida Public Library board with contacts.",
      "wanted": "Park- and library-district boundary tilings from the county GIS; the yearbook's trustee lists are ready to ride them."
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
      "summary": "Boone's five municipalities keep identity-only cards: the clerk's yearbook covers all five, but its newest posted edition predates the April 2025 election.",
      "blocker": "The clerk's 'Boone County, Illinois Year Book' is the right source shape — all five municipalities, Belvidere's alderpersons by ward with contact — but the newest posted edition is 2024 (probes for 2025/2026 editions 404), and it names three Belvidere aldermen the April 2025 election replaced (measured against the city's current page). NorthCOG publishes a member list only, and the county GIS Municipalities layer (63 features) carries no contact or officeholder columns.",
      "wanted": "A post-April-2025 yearbook edition on the clerk's page. Belvidere's current council is separately buildable today from the county GIS Belvidere_Wards layer (verified current — see the build-ready ledger)."
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
      "summary": "Grundy's fire, park and library districts are not shipped — the county GIS publishes no taxing-district geometry.",
      "blocker": "Re-enumerated 2026-07-31 across all 23 folders of the county GIS: the FireDepartments folder is literally empty and no taxing-district service exists anywhere. The identities are now published — the clerk's July 2026 Directory of Officials names 12 fire protection districts, the library districts and 2 park districts with their trustees — but boundaries exist in no machine-readable form.",
      "wanted": "Fire, park and library district boundary tilings in any GIS or shapefile form; the clerk's 2026 directory already supplies the trustees."
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
      "summary": "Morris — Grundy's seat and its only ward-electing municipality — elects eight aldermen from four wards that are mapped nowhere machine-readable.",
      "blocker": "The county GIS (23 folders) has no ward layer and the ArcGIS Online catalog returns zero Morris ward items; the city's own site sits behind a Cloudflare managed challenge, its ward map is a raster JPG (2021 vintage), and Ordinance 3977 defines the wards as a map exhibit plus prose legal descriptions. The alderman roster itself is published ward-keyed in the clerk's July 2026 directory.",
      "wanted": "Morris ward polygons in any vector form — a city GIS layer, a county-hosted layer, or an ArcGIS Online item."
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
      "summary": "Livingston's voting precincts are not shipped — the county publishes no precinct geometry in any form.",
      "blocker": "Measured 2026-07-31: the county runs no public GIS — its only GIS artifact is the assessment office's mail-order parcel program ($0.10-0.20 per parcel by mailed check), an ArcGIS Online title search returns zero county items, and the regional TCRPC org (363 services) hosts no Livingston layers. The clerk's yearbook lists precincts and polling places as text only.",
      "wanted": "Precinct polygons from any county-published source; the yearbook's polling-place list is ready for the join."
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
      "summary": "Livingston's fire, park and library districts are not shipped — no boundary source exists.",
      "blocker": "Same measured basis as livingston-precincts: the county publishes no GIS at all. The one fragment found is Flanagan Park District appearing inside TCRPC's Peoria-region park dissolve — one of the county's districts, in another region's layer.",
      "wanted": "County-wide fire/park/library district polygons from any official source; the yearbook's fire-agency directory supplies contacts the day geometry exists."
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
      "summary": "McLean publishes rich election GIS and no fire, park or library district boundary.",
      "blocker": "Enumerated three ways 2026-07-31: the county server's 14 folders, the McGIS hub's 28 datasets, and the 183-item ArcGIS Online org — no district tiling in any of them (the parks layers are county park facilities; Allin Park District appears only inside TCRPC's foreign regional dissolve). The clerk's officials database carries fire/park/library trustee rosters with nothing to sit them on.",
      "wanted": "FPD, park- and library-district boundary polygons; the clerk's rosters are already published."
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
      "summary": "Logan's fire card cannot ship: the county's only fire geometry is a dispatch-quadrant layer, not the districts.",
      "blocker": "Measured 2026-07-31: the sighted 'fire zones' layer subdivides 14 agencies into compass quadrants and includes the municipal Lincoln city fire department — ESZ/response-zone semantics, filed under Emergency Services beside ambulance and law-enforcement zones — and a quadrant union does not match any adopted district. No FPD boundary exists among the 63 layers of the county's GIS of record; the yearbook's FPD directory is text only.",
      "wanted": "Adopted fire-protection-district boundaries; the yearbook directory supplies contacts once geometry exists."
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
      "summary": "Sangamon's park and library districts have published trustee rosters and no boundaries.",
      "blocker": "The county's 203-service ArcGIS Online org (fully enumerated 2026-07-31) contains no park- or library-district geometry. The clerk publishes the officeholder half in full: the Springfield Park District board and 14 library-district boards, each with a trustees PDF.",
      "wanted": "Park- and library-district boundary polygons — a county org layer, district-published files, or a state taxing-district source; the rosters are already in hand."
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
      "summary": "Stephenson's park and library districts exist only as raster shading inside the county's 2014 maps — unlike its fire map, which is vector and shipped.",
      "blocker": "Measured 2026-08-02 when the fire map was georeferenced: the county's 2014 PARK and LIBRARY DISTRICT maps on the ISBE precinctmaps mirror carry only legend swatches as vector fills — the district shading itself is baked into sixteen 3165x166 raster JPEG strips tiling the map body (the FIRE map, from the same 2014-07-08 series, draws its districts as real vector paths and shipped). Names still concord with the 2025 tax roll (park 4/4, library 4/4). A raster-classification georeference is possible in principle but would stack pixel-tracing error (~11 m/px) on the transform's, landing far coarser than the fleet's other measured boundary.",
      "wanted": "Park- and library-district boundaries in any vector form — a re-export of the county's own 2014 maps, district-published files, or a state taxing-district source."
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
      "summary": "Macoupin's fire, park and library districts are not shipped — its Socrata portal carries no district geometry.",
      "blocker": "The county's only spatial publishing channel is its Socrata portal; the full 61-asset catalog (enumerated 2026-07-31) contains precinct and school-district geometry and nothing else, and the clerk's Map Room is election maps only.",
      "wanted": "Any Macoupin fire/park/library district boundary publication — a new portal dataset, a county GIS debut, or a state-level taxing-district source covering the county."
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
      "summary": "Macoupin's current municipal officials sit behind a JavaScript-only component; the only machine-readable export froze in 2015.",
      "blocker": "The clerk's live seat-level directory on macoupinvotes.gov renders entirely client-side through SOE Software's elected-officials component — the page returns 200 with zero officials in the body, and the JSONP endpoint is constructed at runtime, not extractable from the script. The Socrata export (rxtc-9j2k, 892 rows incl. ward-keyed aldermen) was last updated 2015-11-03; shipping it would present a decade-old snapshot as current officeholders.",
      "wanted": "The SOE component's underlying data endpoint (one captured browser session on the elected-officials page would reveal it), or a clerk-published export or refresh of the Socrata directory."
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
      "summary": "Eight Macoupin cities elect aldermen by ward; none has published ward geometry.",
      "blocker": "Benld, Bunker Hill, Carlinville, Gillespie, Girard, Mt. Olive, Staunton and Virden all elected by ward as of the clerk's 2015 directory — the newest machine-readable roster. The 61-asset county portal and the clerk's Map Room carry no municipal ward geometry, and sampled city sites publish none. Because the live directory is JS-blocked (see macoupin-municipal-officials), even the current ward counts rest on the 2015 snapshot.",
      "wanted": "Ward polygons (or adopted ward-description ordinances) for any of the eight cities, plus a current aldermen-by-ward roster — the clerk's SOE directory would supply it once its endpoint is resolved."
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
      "summary": "St. Clair publishes no park- or library-district geometry on any of its GIS surfaces.",
      "blocker": "Full enumeration 2026-07-31: the 17 root services plus the CentralSquare and Utilities folders on the county's ArcGIS server, the 36-item county AGOL account and its 30 hosted services — zero park or library layers. (Fire fared better: a 44-polygon countywide fire tiling turned up in the county's CAD folder, identity-only — recorded in the build-ready ledger with its taxing-vs-dispatch caveat.)",
      "wanted": "A published park- and library-district polygon tiling for St. Clair County."
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
      "summary": "St. Clair board cards name the member and nothing else, because the county publishes no per-member contact.",
      "blocker": "Measured 2026-07-31 on the county's own /board pages: all 28 district pages carry only the shared countyboard@co.st-clair.il.us mailbox and the (618) 277-6600 switchboard — per-member phone and e-mail are published 0/28. Committee assignments are the only per-member enrichment available (with one trap: District 16's photo caption reads 'District 17', so any scraper must key on the URL, never the caption).",
      "wanted": "Any county-published per-member phone or e-mail keyed by district; short of that, the shared mailbox plus committee assignments are the honest ceiling for this card."
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
      "summary": "Winnebago publishes no fire, park or library district tiling — its only countywide fire polygons are NG911 dispatch zones.",
      "blocker": "WinGIS's full public surface (45 services across the root and four folders, enumerated 2026-07-31) carries no taxing-district tiling for any of the three. The nearest layers fail on kind, not reach: the NG911 'Fire' layer is a 364-polygon dispatch segmentation, one fire agency publishes its own boundary, and the park layers are facility parcels. A dispatch zone is not a taxing district, and presenting one as the other would misstate who levies the tax.",
      "wanted": "Fire-protection, park- or library-district tilings on WinGIS or any Winnebago agency org — the county's NG911 stack proves the GIS capacity exists."
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
      "blocker": "Measured 2026-07-31: the county runs no GIS (its GIS page links a Vanguard parcel-search portal with no REST services) and no county AGOL org exists. The clerk's 2025 Final Tax Computation Report names 9 fire districts, 3 park districts and 7 library taxing rows (3 true districts + 4 municipal/township funds) — rates only; the yearbook adds library hours but no maps.",
      "wanted": "Vector boundaries for the districts — several cross county lines (Polo, Hanover and Shannon fire districts; Pearl City park and library), so full extents matter."
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
      "summary": "All three Carroll cities elect aldermen by ward; none publishes ward geometry, and the one sighted layer is private and pre-redistricting.",
      "blocker": "Savanna (4 wards x 2 seats), Mount Carroll (3 x 2) and Lanark (3) confirmed ward-electing from city sources 2026-07-31. Savanna's own AGOL org holds exactly one ward artifact — a feature collection titled 'Ward Districts (Pre-Redistricting)' that returns 403-private; Lanark and Mount Carroll publish no ward map; the county has no GIS to carry them.",
      "wanted": "Current post-2020-census ward polygons for any of the three — Savanna Public Works demonstrably runs a 102-item AGOL org, so a public share of a current layer is the most plausible single unlock."
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
      "summary": "McHenry is the metro county whose park districts cannot ship: the county publishes park facilities, not district boundaries.",
      "blocker": "The county GIS publishes ~350 park point/asset features and no park-district boundary tiling (measured 2026-07; the county's 132-service org re-checked 2026-07-31). Long recorded in the concept matrix as a gap — this entry finally makes it visible to the Data gaps panel, per the guidebook's own contract rule 3.",
      "wanted": "A McHenry park-district boundary tiling on the county GIS."
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
      "summary": "Lee ships fire districts but publishes no park- or library-district boundary.",
      "blocker": "Re-enumerated 2026-07-31: the county's leecogis server carries the NG911 fire service areas the app ships and no park- or library-district layer of any kind.",
      "wanted": "Park- and library-district tilings from the county GIS."
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
      "summary": "Whiteside publishes an unusually rich election GIS and no fire, park or library district tiling.",
      "blocker": "The county's 63-service ArcGIS Online org re-enumerated 2026-07-31: election geography, precincts, polling places and board layers — and no taxing-district tiling of any kind.",
      "wanted": "Fire, park and library district tilings on the county org."
    },
    {
      "id": "stephenson-precincts",
      "concept": "Voting precincts",
      "area": "Stephenson County",
      "counties": [
        "stephenson"
      ],
      "kind": "no-source",
      "layer": "county-precinct",
      "summary": "Stephenson's voting precincts are not shipped: the county publishes no current precinct geometry.",
      "blocker": "The county re-precincted after the 2020 census (Freeport 1-18 became 01-16; Waddams and West Point renumbered), so Census 2020 VTDs cannot draw the current fabric. Found 2026-07-31: the Illinois SBE's static precinct-maps mirror carries per-precinct VECTOR PDFs for the county — but at the 2021 pre-redraw vintage, so the extractable geometry is the superseded map. The state's GIS viewer that might carry current data remains down (503).",
      "wanted": "The county's current precinct boundaries in any vector form. The Freeport Township subset of the same file would also replace the georeferenced board-district geometry — see stephenson-freeport-precincts."
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
      "summary": "Momence elects eight alderpersons across four wards mapped only on a 2017 raster JPG.",
      "blocker": "Measured 2026-07-31: the city's own ward-map page serves a single JPEG (Last-Modified 2017-10-30 — pre-census vintage); no Momence ward item exists in the ArcGIS Online catalog, and the county GIS's visible inventory carries no municipal ward layer. The per-ward roster is on the city's own pages.",
      "wanted": "Adopted Momence ward polygons in any vector form; the seat roster is already published."
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
      "summary": "Kankakee city's ward layer exists but mixes map vintages — a point can resolve two different wards — so it cannot ship as-is.",
      "blocker": "Measured 2026-07-31: the city's AGOL WARD layer returns 10 polygons for 7 wards — duplicate rows for the 4th, 6th and 7th, with centroid point-tests returning BOTH copies of the 6th and 7th, and the 1st ward's centroid also falling inside the 2nd ward's polygon. No row-level flag distinguishes the current (2022-approved) geometry from superseded rows, so any dedupe would be a guess until verified against the city's adopted 2022 ward-map PDF. The city's directory publishes all 14 alderpersons with per-seat phone and e-mail, ready to join.",
      "wanted": "A defensible current-rows selection for the 7 wards — city confirmation, a cleaned single-vintage layer, or per-row verification against the 2022-approved map."
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
      "summary": "Park City is Lake County's one ward-electing city with no published ward geometry.",
      "blocker": "Measured in the 2026-07-31 collar ward sweep: Waukegan and North Chicago now publish current ward layers on their own orgs and Lake Forest's wards ride the GIS Consortium (all three are build candidates in the backlog); Zion and Highwood elect at-large. Park City's 3 wards appear in no city, county or ArcGIS Online source.",
      "wanted": "Park City ward polygons in any vector form."
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
      "summary": "Three DuPage ward cities exist only in a county layer whose officeholder attributes froze in 2021 and whose boundary vintage is unproven.",
      "blocker": "The 2026-07-31 sweep found current city-grade ward layers with populated officeholder attributes for Elmhurst, Wheaton, West Chicago, Lombard and Glendale Heights (West Chicago SHIPPED 2026-08-02; the other four's service URLs did not survive to the build pass and are re-discovery candidates in the backlog), and Darien with current-ish geometry but stale attributes. Wood Dale, Oakbrook Terrace and Warrenville appear only in the county's Municipal_Wards layer, whose attributes read 'Updated 04/29/2021' and whose boundary vintage against the post-2020 redraws is unproven — shipping it could draw pre-redistricting lines.",
      "wanted": "City-published ward layers for the three, or each city's adopted redistricting ordinance so the county layer's vintage can be verified against it."
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
      "summary": "McHenry County's other two aldermanic cities cannot even be measured: Harvard's site is challenge-fronted and Marengo's ward structure is unverified.",
      "blocker": "Measured 2026-07-31: cityofharvard.org answers every fetch with a Cloudflare managed challenge (403, cf-mitigated: challenge), and no Harvard or Marengo ward geometry exists in the ArcGIS Online catalog; Marengo's ward structure itself could not be confirmed from an official source. (City of McHenry's own 7 wards SHIPPED 2026-08-02, seat-only.)",
      "wanted": "A challenge-capable read of the two cities' council/ward pages to establish structure, then ward geometry from any official source."
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
      "summary": "Plano's four wards have county-hosted geometry and no published seat-holders anywhere.",
      "blocker": "Measured 2026-07-31: the county's Hosted/Wards layer carries Yorkville and Plano ward polygons (2022-01 vintage), and Yorkville's aldermen ride the companion Alderman_Points layer — but no county or city source names Plano's aldermen by ward: the county yearbook is head+clerk depth and the city publishes no roster the sweep could find.",
      "wanted": "A Plano aldermen-by-ward roster (city site, clerk, or a county layer), plus confirmation the 2022-01 ward boundaries survived the post-census redistricting cycle."
    },
    {
      "id": "rock-island-city-wards",
      "concept": "City council district",
      "area": "City of Rock Island",
      "counties": [
        "rock-island"
      ],
      "kind": "no-source",
      "layer": "ward",
      "summary": "Rock Island City publishes its 7 wards with current aldermen on every polygon, but nothing proves the boundaries reflect the post-2020-census redraw.",
      "blocker": "Measured 2026-07-31: the city's own AGOL layer carries the current council (verified 7/7 against the city site and the county clerk's 2026 roster) and was edited 2025-05 — but the service was created in 2017 from a 2012 map package, its only population column is Pop_2010, and no post-2020 redistricting ordinance could be located; the city-code library that would carry it answers with a Cloudflare challenge.",
      "wanted": "Confirmation of the ward map's vintage — a redistricting ordinance citation, a clerk statement that the 2010-cycle wards were retained, or a re-published layer with 2020 populations. Everything else about this entry is ship-ready."
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
      "summary": "Joliet's per-seat council contact refreshes only by browser engine or Archive: the city hard-denies every plain datacenter client.",
      "blocker": "Re-measured 2026-07-31: joliet.gov returns 403 from AkamaiGHost with an x-reference-error and a ~406-byte static body to every plain HTTP client from a datacenter — identical with a complete browser header set, so the fingerprint sits below HTTP at the TLS level. The Playwright rung and the Internet Archive both work (newest capture 2026-05-20, verified to carry the full council). Split out of blocked-crawlers so the panel files it under the municipality layer in Will County, where the block actually bites.",
      "wanted": "Any machine-readable council roster joliet.gov permits (JSON/CSV/RSS); until then the browser-rung scrape plus Archive fallback remains the refresh path."
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
      "summary": "LaSalle's board card runs on DERIVED geometry: the county publishes no GIS of its adopted 2022-2031 map, and eleven split precincts are drawn with their majority side.",
      "blocker": "REBUILT 2026-08-01 (was: the entry shipped the superseded 2011-2021 map with a 2015-frozen roster — pulled the same day it was found). The shipped boundary now dissolves the county's own precinct layer per the district assignment its Nov 2024 + Mar 2026 canvasses administer: 108 whole precincts exact on county-drawn lines, nine districts reproducing the adopted map's printed populations to the person. What keeps this entry open: the county re-precincted after adopting 'Redistricting Map Scenario 6A' (Resolution #21-126) and now runs ELEVEN precincts that straddle district lines (Serena 1, Eden 2, Mission 2, Peru 4, Ottawa 5/6/7, La Salle 7/8, Bruce 6/12 — registered-voter counts per side are in the build script); each is drawn whole with its majority side, misplacing ~1,659 of 109,658 residents, and the card says so wherever it applies. The adopted map itself exists only as a vector-PDF pair; the county's one published board GIS remains the superseded map, and its GIS vendor's own server presents an expired TLS certificate. The roster half is closed: a weekly scrape of the county directory ships all 29 members with full phones and district-office e-mails, plus the countywide-elected Chairman.",
      "wanted": "The county publishing its adopted 2022-2031 board districts as GIS — that retires the derived build outright. Short of that, the recorded refinement is cutting the eleven split precincts along the adopted map's vector district lines (the Stephenson georeference route), which would shrink the approximation from whole minority sides to a ~20 m band."
    },
    {
      "id": "woodford-special-districts",
      "concept": "Fire, park and library districts",
      "area": "Woodford County",
      "counties": [],
      "kind": "no-source",
      "layer": "fire-district",
      "summary": "Woodford names its fire, park and library districts, but every 'district' service it publishes is the parcel fabric wearing the district's name.",
      "blocker": "Measured 2026-07-31: the county's 'Fire Protection Districts' FeatureServer returns 25,824 features on a 110-field parcel schema — PINs, tax codes, owner and billing names, data this app would never ship — and the park and library services share the same schema. The tax codes prove the county maintains the real tiling; it publishes the parcels instead of the dissolve. (Woodford's board districts and precincts, by contrast, SHIPPED 2026-08-02 — the county is now served; this special-districts gap is what remains.)",
      "wanted": "Fire, park and library district boundaries as actual district polygons — one named feature per district — in any GIS or shapefile form."
    },
    {
      "id": "chicago-amenity-phones",
      "concept": "Fire stations",
      "area": "Chicago metro",
      "counties": [],
      "kind": "data-quality",
      "layer": "fire-station",
      "summary": "Fire-station cards carry no phone number.",
      "blocker": "Verified in the 2026-07 card audit alongside the NYC/SF twins: the USGS National Map structures source the metro-wide station layers read genuinely carries no phone column — an absence in the source, not an unwired field.",
      "wanted": "A CFD or metro-wide station dataset with public phone numbers, or phone attributes on the National Map structures layers."
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
An empty `counties` means the gap has no mappable footprint — Bureau, Mercer and
Jo Daviess each have a real, published board roster or district composition but nothing
that draws the boundary, so there is no outline to attach the gap to — and it appears only
in the everywhere list. (Henry sat in that list until 2026-08-02, when its "Alternate"
map proved to be the adopted plan and the county shipped.) (The original example here was DeKalb, on the strength of a
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
| Electoral precinct / ballot sub-unit | SHIPPED `ward-precinct` + `county-precinct` (consolidated CountyDispatch: suburban Cook current map 1,430 — Cook-outside-Chicago only, city precincts are the BOE ward-precinct layer — + Will 2022 map 310 + DuPage 2024 map 600 + Lake current map 431 + Kane current map 292 + McHenry current map 223 + Kendall current map 78 w/ the county's own polling-place assignment per precinct — every metro county covered — plus the sixteen expansion counties: LaSalle 119 (polling joined 119/119) + Kankakee 59 + Boone 37 (polling on the feature) + Grundy 40 (polling joined 38/40) + Macoupin 45 (the county's own Socrata portal — the 2022-2032 fabric ab79-cnsh; polling joined 45/45 from its sibling polling dataset by deterministic label expansion, 2026-08-02 — the pass-4 note of 105 was the superseded map) + Madison 191 (polling joined 191/191, the fleet's cleanest) + St. Clair 150 (polling is a recorded gap) + Winnebago 94 (county-clerk jurisdiction only — Rockford runs its own election commission, a recorded gap) + DeKalb 69 + Lee 46 + Whiteside 60 (polling joined 55/60, recorded gap) + Rock Island 120 + McLean 141 (polling joined 141/141) + Logan 29 (the clerk's HTML polling table shipped as a same-origin file, joined 29/29) + Sangamon 166 (polling joined 165/166) + Carroll 22 (TIGERweb Census-2020 VTDs live — the county did not re-precinct; the clerk's polling notice shipped as a same-origin file, 22/22) + Woodford 37 (TCRPC's election service, polling joined 37/37 on the numeric polling reference, 2026-08-02); Kane's card also gained the township name from the clerk's own prefix pairing and the election-labelled polling row, 292/292 — the pass-6 precinct tranche, 2026-08-02) | SHIPPED `election-district` (~4,200) | SHIPPED `election-precinct` (`jg6x-23ig`, 2022 map; subOf `supervisor-district`, polling-place lookup link) |
| County legislature / commissioner | SHIPPED `county-board` (consolidated CountyDispatch layer: Cook Commissioner 17 + Will 11 + DuPage 6 + Lake 19 + Kane 24 + McHenry 9 + Kendall 2 + LaSalle 29 (DERIVED — see below) + Kankakee 28 + Winnebago 20 + Livingston 3 + McLean 10 + Logan 6 + Sangamon 29 + Madison 26 + St. Clair 28 + DeKalb 12 + Ogle 8 + Stephenson 8 + Carroll 3 + Lee 4 + Whiteside 3 + Rock Island 19 + Woodford 3 (DERIVED — TIGER townships per adopted Ordinance 2020/21 #005; five members per district from a weekly directory scrape, 15/15 with phone and e-mail; no chair marked — elected from within the body, the directory doesn't say) + Boone 3 (RUNTIME-MERGED — the county GIS's three per-district layers, each pre-dissolved, merged and district-tagged at load time; four members per district from a weekly board-page scrape, 12/12 with phone, e-mail and term-expiry year; one Vice-Chairman tagged verbatim, no Chairman named) + Grundy 3 (DERIVED — the county's own precinct layer dissolved per the adopted 10/12/2021 map, the transcription proven by the map's printed populations to the person; six members per district from a weekly board-page scrape, 18/18 with party, since-year, committees, phone and e-mail; Chairman tagged from his own row) + Henry 2 (DERIVED — TIGER townships per adopted Ordinance 21-33, twelve whole townships per district, the composition proven by the adopted map's own two-census population table AND live Census POP100, all to the person; TEN members per district — the fleet's widest — from a weekly scrape of the county's own district-keyed directory, 20/20 with e-mail; no chair marked, so none is tagged) districts — LaSalle REBUILT 2026-08-01 on derived geometry (its own board GIS is the superseded 2011-2021 map): the county's precinct layer dissolved per its 2024+2026 election canvasses, 11 split precincts drawn with their majority side and stated on the card, roster scraped weekly from the county directory with the countywide-elected Chairman (gap lasalle-board-districts-stale records what remains); absorbed the former `commissioner` / `will-county-board` / `dupage-county-board` layers, old permalink ids aliased; Lake's members + contact + office address ride live on the county's own boundary GIS, with Chair/Vice-Chair tags from a weekly directory scrape (name-match guarded); Kane's GIS carries member names while a weekly scrape of the county's SharePoint directory list adds party/office phone/email + the countywide-elected Chair; Kendall's members + Chairman and McHenry's members + countywide-elected Chairman — each with contact + profile links — join from hand-verified rosters of each county's own directory — those two counties block all automated fetch incl. the Archive's crawler, so their weekly scrape attempts feed standing tracking issues until the block lifts) | NO HONEST ANALOG¹ | NO HONEST ANALOG (folded into `supervisor-district`) |
| County property-tax appeals board (elected) | SHIPPED `ccbr` (commissioner roster scraped weekly from the Board's own site) | NO HONEST ANALOG² | NO HONEST ANALOG⁵ |
| State high-court electoral district | SHIPPED `il-supreme-court` | SHIPPED `judicial-district` (NY Supreme is trial-level, elected by district) | NO HONEST ANALOG⁶ |
| Trial/civil-court sub-district | SHIPPED `judicial-subcircuit` (consolidated CountyDispatch: Cook 20 — live from the county GIS, cross-validated against the enacted ilsenateredistricting.com shapefile, with the Circuit Court's 6 municipal districts + courthouses as a card row — + Will 12th-Circuit 5 + DuPage 18th-Circuit 7 + Lake 19th-Circuit 12 + Kane 16th-Circuit 4 (pre-built from the enacted shapefile — the county's services are permission-locked) + McHenry 22nd-Circuit 4 (pre-built — the county publishes no subcircuit service) + Winnebago 17th-Circuit 2 + Madison 3rd-Circuit 4 + Sangamon 7th-Circuit 7 (the three 2026-07-28 entries, pre-built from the same enacted archive; their coverage is the subcircuit geometry itself, so each circuit's secondary counties — Boone; Bond; Greene/Jersey/Macoupin/Morgan/Scott — answer too), all PA 102-0693; the app ships all nine circuits the act covers, and Macoupin — a 7th-Circuit secondary county — is answered by the Sangamon entry; every other served county's circuit (Kendall + DeKalb's 23rd, LaSalle + Grundy's 13th, Kankakee's 21st, Livingston/McLean/Logan/Woodford's 11th, St. Clair's 20th, Ogle/Lee/Stephenson/Carroll's 15th, Whiteside + Rock Island + Henry's 14th) received NO subcircuits under the act — structurally n/a, the layer hides there) | SHIPPED `municipal-court` (28) | NO HONEST ANALOG⁶ |
| District Attorney (districted) | n/a (Cook State's Attorney is one countywide office) | SHIPPED `district-attorney` (5 borough DAs) | NO HONEST ANALOG (one citywide DA)⁷ |
| Borough president / by-county executive | n/a | SHIPPED `borough-president` | n/a |
| Community district / board (appointed, labeled so) | n/a | SHIPPED `community-district` | n/a |
| Elected school board (districted) | SHIPPED `school-board` (ERSB) | NO HONEST ANALOG³ | NO HONEST ANALOG (at-large board)⁴ |
| Parent-elected education council | n/a | SHIPPED `cec` | n/a |
| Elected regional transit board | NO HONEST ANALOG⁸ | NO HONEST ANALOG⁸ | SHIPPED `bart-director` (9 districts, BART's own ArcGIS + hand-verified roster) |
| Municipal governing body (surfaced on the municipality-identity card) | SHIPPED on `municipality` — **492 municipalities across twenty-one counties**, with head of government + 2,279 board members incl. 583 ward/district seats + clerks/treasurers + hall contact, joined by Census place GEOID (weekly CI). Depth varies honestly by county: **full governing body** Cook 129 / Will 30 / Madison 28 / Sangamon 26 / St. Clair 26 / LaSalle 25 / Rock Island 15 / Livingston 14 / DeKalb 14 / Ogle 13 / Logan 11 / Stephenson 11 / Winnebago 11 / Grundy 9 / McLean 3 (its three ward-electing cities from their own pages — the county-wide source is a JS-locked Airtable interface), **head-level** McHenry 27 / Kane 23 / DuPage 23 / Carroll 7 / Kendall 6, **contact-only** Lake 41 (publishes no names county-side). The 2026-08-01 tranche (Grundy, Livingston, Logan, McLean, Sangamon, Madison, St. Clair, Rock Island — the pass-6 build-ready ledger's municipal-officials half) shipped in one change; Madison + St. Clair share one source (the East-West Gateway POD) and Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city payloads fill what a county cannot — Will's ward cities + Joliet (per-seat contact), Skokie (trustee districts), Freeport (the whole city; Stephenson's source is a village directory that omits its own county seat). A municipality listed by two counties resolves by source depth, then county order. Chicago's citywide officers ride this card while its 50 ward seats stay `ward`'s answer. An unsourced municipality keeps the identity-only card — Lee's 13 and Whiteside's 11 are the newest, both at the rule-4 floor after all four sourced rungs were worked (`docs/EXPANSION_GUIDE.md` §2.4) | n/a (NYC's municipalities are the five boroughs — `borough-president`) | n/a (consolidated city-county) |
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
| Fire-service boundary | SHIPPED `fire-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + McHenry + Kendall suburban Fire *Protection* Districts; Cook from the Clerk's tax-agency tiling and DuPage/McHenry/Kendall name-only, Lake carries office contact, Kane names each district's chief + contact) · Kankakee 17 (identity-only — the county declares contact columns and populates none) · Madison 42 (the fleet's first contact-bearing fire entry: dept head 39/42, address 41/42, phone 41/42) · DeKalb 18 · Lee 22 (NG911 service areas) · Rock Island 17 (the county's tax-agency tiling, FirePD 17/17) · Sangamon 29 FPDs + Springfield's corporate area (FireDistrictEtc L2 — 226 fragments grouped per district at load; the Springfield card states the city is served by its own Fire Department, not an FPD) · St. Clair 44 (CentralSquare/DATA/8, the county's CAD folder — identity-only, with the source's unstated taxing-vs-dispatch status carried as a caveat on every card) · Stephenson 15 (GEOREFERENCED from the county's own 2014 vector-PDF map — the fleet's second measured boundary, hydrography-fitted to 11.5 m median; 2014-vintage caveat on every card) | SHIPPED `fire-battalion` (operational battalions, 49) | NO HONEST ANALOG — SFFD battalions exist but no boundary is published |
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
| Township / municipality | SHIPPED `township` · `municipality` (statewide IL; the municipality card names the municipal government — head of government, board, other elected officers, hall contact — for 492 municipalities across twenty-one counties incl. Chicago's citywide officers, county-sourced and joined by place GEOID) | n/a | n/a |
| Park district | SHIPPED `park-district` (consolidated CountyDispatch: Cook + Will + DuPage + Lake + Kane + Kendall; Cook's Clerk tiling includes the Chicago Park District — a Loop click resolves the city's own park taxing body; DuPage/Kendall name-only, Lake carries office contact, Kane names each district's board president + contact; McHenry has no entry — recorded gap, it publishes facilities not district boundaries) · Kankakee 4 (identity-only) · Madison 6 (identity-only) · DeKalb 6 · Rock Island 1 (Cordova — the county levies only one) | n/a | n/a |
| Library taxing district | SHIPPED `library-district` (CountyDispatch, born consolidated: Cook's two Clerk tax-agency tilings — 59 Public Library Districts + 54 municipal Library Funds, incl. the City of Chicago Library Fund at a Loop click — + Will 27 w/ trustees + DuPage 32 name-only + Lake 15 w/ office contact + Kane 16 w/ board president + contact + McHenry 13 name-only + Kendall 9 name-only incl. the municipal Joliet/Yorkville city-library funds its tax tiling records, the Cook-style shape) · Kankakee 8 (identity-only) · Madison 18 (identity-only) · DeKalb 13 · Rock Island 9 named districts (the tenth polygon is the un-districted remainder, dropped in the loader) | n/a — NYC's three library systems (NYPL/BPL/QPL) are nonprofit corporations, not taxing districts | n/a — SFPL is a city department |
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
> **2026-07-31** (validation + sourcing pass 6, below) the open items split cleanly into
> work that is ready and gaps that need a publisher:
>
> | Open item | Blocker | Actionable? |
> |---|---|---|
> | ~~LaSalle county-board rebuild~~ **SHIPPED 2026-08-01** — boundary derived from the county's precinct layer per its full 2024+2026 canvass record; weekly directory roster with the countywide Chairman; 11 split precincts drawn with their majority side and stated on the card | remaining: the split-precinct cut refinement, or the county publishing its adopted map as GIS | done — refinement recorded |
> | **The pass-6 build-ready ledger** — ~~8 counties' municipal-officials sources~~ **SHIPPED 2026-08-01** (Grundy, Livingston, Logan, McLean's three ward cities, Sangamon, Madison, St. Clair, Rock Island — the roster grew 360 → 492 municipalities; McLean's county-wide Airtable route stays open, see its row); ~~4 precinct counties + 3 polling/naming joins~~ **SHIPPED 2026-08-02**; ~~Woodford's board~~ shipped with the county 2026-08-02; ~~3 board-geometry builds~~ **ALL SHIPPED 2026-08-02** (Boone + Grundy + Henry — Henry as the twenty-eighth county), ~~the Logan board roster scraper~~ (SHIPPED 2026-08-02), still open: Aurora per-seat contact (re-measured 2026-08-02: Akamai 403s every rung reachable from CI — see its ledger row), ~~2 fire tilings~~ **SHIPPED 2026-08-02** (Sangamon 29 FPDs + St. Clair 44, each with its recorded caveat on the card), ~~Stephenson fire~~ **SHIPPED 2026-08-02** (georeferenced; its park/library maps measured RASTER-baked — see the new gap), ~~the verified city ward layers~~ **SHIPPED 2026-08-02** (22 cities across 13 sources; Lake Forest + 4 DuPage cities still to chase — see the ward ledger) | nothing — every source verified live 2026-07-31 | **yes — the live work queue** |
> | ~~**Woodford County**~~ **SHIPPED 2026-08-02 — the twenty-seventh dispatched county**: board (3 DERIVED districts per Ord 2020/21 #005 + 15-member weekly roster with phones and e-mails) and precincts (TCRPC, 37, polling 37/37); its fire/park/library absences were already recorded (woodford-special-districts) | — | done |
> | The 49 no-source + 4 blocked gap entries (fire/park/library tilings in ten counties, precinct geometry in two, ward geometry in nine cities, three municipal-officials counties, four frontier boards…) | publishers — each entry's `wanted` says exactly what | no — recorded, panel-visible |
> | McHenry / Kendall / Joliet | hard WAF denies (the two board directories now have verified 2026 Archive captures; McHenry's yearbook page and Kendall's municipal PDF still don't) | no — rule-4 terminal |
> | DuPage municipal phones; Will's `party` field | unchanged (re-verified 2026-07-31); deliberate non-ship | no |
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
| `county` | County | geography | Bespoke | live TIGERweb State_County | `il-county-clerks.json` (weekly CI from ISBE; Peoria deliberately absent) | — |
| `school-district-secondary` | High School District | schools | Polygon | live TIGERweb School L1 | — | outsideChicagoSchoolCoverage |
| `school-district-unified` | Unified School District | schools | Polygon | live TIGERweb School L0 | — | — |
| `school-district-elementary` | Elementary School District | schools | Polygon | live TIGERweb School L2 | — | outsideChicagoSchoolCoverage |
| `township` | Township / County Subdivision | geography | Polygon | live TIGERweb CouSub | — | — (subOf `county`) |
| `municipality` | Municipality | geography | Bespoke | live TIGERweb Places | `municipal-officials.json` (weekly CI; twenty-one counties + Chicago's citywide officers, 492 municipalities — head of government + board + other elected officers + hall contact, joined by place GEOID; depth per county: full body Cook/Will/DeKalb/LaSalle/Winnebago/Ogle/Stephenson/Grundy/Livingston/Logan/Sangamon/Madison/St. Clair/Rock Island (+ McLean's three ward cities from their own pages — the county-wide source is a JS-locked Airtable interface), head+clerk DuPage/Kane/McHenry/Kendall/Carroll, contact-only Lake. Madison + St. Clair share the East-West Gateway POD (one COG document, two counties); Cahokia Heights (inc. 2021) joins via an explicit post-Census-2020 GEOID. Four city-level payloads fill what a county cannot: Will's ward cities and Joliet for per-seat contact, Skokie for trustee districts, and Freeport — the whole city, since Stephenson's county source is a village directory that omits its own county seat) | — |
| `judicial-subcircuit` | Judicial Subcircuit | political | CountyDispatch | Cook County GIS L5 (20 subcircuits) + L27 (municipal districts) · Will County ArcGIS · DuPage County ArcGIS (`Judicial_Subcircuits`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L1) · pre-built `kane-judicial-subcircuits.json` + `mchenry-judicial-subcircuits.json` + `winnebago-judicial-subcircuits.json` (17th) + `madison-judicial-subcircuits.json` (3rd) + `sangamon-judicial-subcircuits.json` (7th) (all PA 102-0693 enacted shapefile) — no Kendall entry: its 23rd Circuit received no subcircuits under the act (nor did the 13th/14th/15th/20th/21st, so the other expansion counties are structurally n/a) | link-only (each card links its circuit's court; Cook adds the Municipal District + courthouse row) | OR of cook/will/dupage/lake/kane/mchenry county coverages; the Winnebago/Madison/Sangamon entries use the subcircuit geometry itself as coverage, so each circuit's secondary counties answer too |
| `county-board` | County Board District | political | CountyDispatch | Cook County GIS L9 · Will County ArcGIS · DuPage County ArcGIS (`County_Board_Dist_new`) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L0) · Kane County ArcGIS (`KaneCo_IL_County_Board` L1) · McHenry County ArcGIS (`McHenry_County_Board_Districts` L0) · Kendall County ArcGIS Enterprise (`County_Board_2010` — the CURRENT 2-district map: the post-2020-census reapportionment kept the line, Dec 2021 hearing) · LaSalle **derived** (`lasalle-county-board-districts.json` — the county's own precinct layer dissolved per its 2024+2026 election canvasses by scripts/build_lasalle_board_districts.py; its published board GIS is the superseded 2011-2021 map) · Kankakee self-hosted `k3gis.net` (`BASE/Elected_Officials/1`) · Winnebago WinGIS (`ElectedOfficials/26`, mounted at `/public` not `/arcgis`) · Livingston **derived** (`livingston-county-board-districts.json` — TIGER townships dissolved per the county's published composition; it publishes no GIS) · McLean (`Clerks/MyElectedRepresentatives/1`) · Logan via Tri-County RPC (`Logan_County_Districts_and_Zoning/39`) · Sangamon AGOL (`CountyBoardDistricts2020_WithURLs`) · Madison (`CountyClerk/CBDWS/0`, on `/servera`) · St. Clair (`SCC_voting_districts/2`, on `/server`) · DeKalb AGOL (`District_AreaEffective2022/0`, Esri-JSON fetch — the org's `f=geojson` is lossy on multipart polygons) · Ogle **derived** (`ogle-county-board-districts.json` — Census 2020 VTDs dissolved per resolution R-2021-1106) · Stephenson **part-derived** (`stephenson-county-board-districts.json` — 4 rural districts as TIGER township dissolves, 4 Freeport districts georeferenced from the county's vector-PDF map, the card says so) · Carroll **derived** (`carroll-county-board-districts.json` — TIGER townships per the county's published map) · Lee (`gis.leecountyil.gov/leecogis`) · Whiteside (`ElectionGeography_public/2`, board rows filtered in the loader) · Rock Island (county org, 19 single-member districts) · Woodford **derived** (`woodford-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 2020/21 #005 by scripts/build_woodford_board_districts.py; the county publishes no board GIS) · Boone **runtime-merged** (the county GIS's three per-district MapServer layers — `County_Board_Districts` indexes 0/1/2, each pre-dissolved, verified to tile the county outline — merged and district-tagged by the loader; the features' leftover census-block attributes are read nowhere) · Grundy **derived** (`grundy-county-board-districts.json` — the county's own precinct layer dissolved per the adopted 'Approved County Board Districts (10/12/2021)' map by scripts/build_grundy_board_districts.py; the county GIS publishes no board geometry, and the transcription is proven by the map's own printed populations, all three district totals to the person) · Henry **derived** (`henry-county-board-districts.json` — TIGER townships dissolved per adopted Ordinance 21-33 by scripts/build_henry_board_districts.py; the county's viewer is Sidwell Portico, parcels + townships only, and the composition is proven by the adopted map's own two-census population table and live Census POP100, all to the person) | Cook: live office join (same server); Will: `will-county-board-members.json` (weekly CI); DuPage: `dupage-county-board-members.json` (weekly CI; + countywide Chair); Lake: member + phone/email/office address/district page + newsletter on the boundary GIS itself (live, county-edited; re-verified vs the county directory 2026-07-23; the office-address and newsletter columns were fetched-but-never-requested dead code until 2026-08-01 — the pass-6 finding) + `lake-county-board-roles.json` (weekly CI — the Chair/Vice-Chair tags the GIS lacks, applied only on a name match so a missed reorganization degrades to role-less rows); Kane: member names on the boundary GIS (verified incl. the 2026 D2/D9 appointments) + `kane-county-board-members.json` (weekly CI from the county's SharePoint Board Members list API — party, official office phones, emails, profile links, and the countywide-elected Board Chair; GIS names stay as hover + fallback, cross-checked 24/24 against the roster); Kendall: `kendall-county-board-members.json` (10 members incl. the Chairman — a District 2 member, not a separate countywide seat — phones + emails + per-member profile links; 2026-07 enrichment check re-verified all 10 names 1:1 against the directory's 2026-03 Archive snapshot); McHenry: `mchenry-county-board-members.json` (18 members + the countywide-elected Chairman, phones + emails + per-member profile links; the DuPage countywide-chair shape; 2026-07 enrichment check re-verified all 19 names 1:1 against the directory's 2026-05 Archive snapshot — the county publishes no party or committee data, the one missing phone (D3) is confirmed unpublished at the source, and members' street addresses are residences, deliberately not collected). Both hand-verified 2026-07-23 against the counties' own directories: the counties block ALL automated fetch (direct, real-browser, and the Archive's crawler — SPN2 error:no-request), so the weekly engine-ladder scrapers run green and track the block on standing issues, resuming automation the moment any rung unblocks. LaSalle: `lasalle-county-board-members.json` (weekly CI from the county's own directory — 29/29 names, full 10-digit phones and district-office e-mails, plus the countywide-elected Chairman; the 2015-frozen officeholder columns on the superseded GIS are read nowhere). Kankakee and Winnebago are **rule-4 branch 1** — the member rides the county's own boundary GIS, so no scraper, no roster file and no weekly workflow: Kankakee 28/28 (name, party, phone, e-mail), Winnebago 20/20 (name, party, term year — its address/phone columns are declared and empty on every row, and the richer per-district contact on the county's board page is a backlog scraper, not a guess) . Pass 4's bridge counties: **McLean** 10 districts electing TWO members each, both seats + parties + profile links on the boundary GIS 10/10 (branch 1); **Sangamon** 29, GIS carries the district and a per-district MEMBER URL but no name, so a weekly scraper walks exactly those 29 URLs (29/29 names + parties, 27 e-mails, 22 phones); **Livingston** 3 multi-member districts, boundary AND roster both derived — townships per the county's published composition, members scraped weekly, with an explicit `vacancies` count because the directory lists a "Vacancy" seat that must be counted and never named; **Logan** 6 two-member districts — shipped at the rule-4 branch-3 floor (the county's only roster was a salary publication) until 2026-08-02, when the county's own board page began pairing all twelve members with their districts: a weekly scrape now joins them, 12/12 with phone + e-mail and the county's own Chair/Vice-Chair tags; **Madison** 26, the fleet's RICHEST board source — official/party/term/phone/e-mail/per-district page all on one feature (26/26 name, party, e-mail, URL; 25/26 phone); **St. Clair** 28, branch 1 at its thinnest — name 28/28 and nothing else. Winnebago, McLean, Madison and St. Clair were each spot-checked against their county's own board page before shipping. The northern/western counties (passes 5–5h): **DeKalb** 12 districts × 2 members, weekly roster scrape (party, contact, the Board Chair riding the matching member's row) since the GIS declares member columns and populates almost none; **Ogle** 24 (8 × 3), weekly scrape of the county staff directory (party, phone, e-mail, Chair + Vice Chair); **Stephenson** 8 districts, weekly scrape (a surname guard drops a predecessor's e-mail the county still publishes on one seat); **Carroll** 3 × 3, weekly scrape tolerant of the county's 'Distirct' typo and Roman numerals; **Lee** 4 × 5, weekly positional-parse of the roster PDF (party, e-mail 20/20, the Board Chair cross-checked in prose); **Whiteside** 3 × 9 = 27, branch 1 — members ride `ElectionGeography_public` (27/27 vs the county page; the org's 2019 `MyElectedRepresentatives` service is the stale twin, unused); **Rock Island** 19, weekly roster scrape (party, term, Chair/Vice-Chair); **Boone** 3 × 4, weekly scrape of the county's own board page (12/12 phone + e-mail + term-expiry year, rendered through the shared stale-year gate; role tags verbatim — one Vice-Chairman, no Chairman named anywhere on the page, so none is rendered); **Grundy** 3 × 6, weekly scrape of the county's own board page (18/18 party + since-year + committees verbatim, incl. per-committee Chair/Vice-Chair suffixes + phone + e-mail; the Board Chairman a district member, tagged from his own row); **Henry** 2 × 10 — the fleet's widest multi-member districts — weekly scrape of the county's own CivicPlus directory, which the county itself keys by district (20/20 e-mail, 15/20 phone; no chair marked anywhere, so none is tagged) | OR of cook/will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/winnebago/livingston/mclean/logan/sangamon/madison/st-clair/dekalb/ogle/stephenson/carroll/lee/whiteside/rock-island/woodford/boone/grundy/henry county coverages |
| `ccbr` | Cook County Board of Review District | political | Bespoke | pre-built (PA 102-0012 shapefile) | `ccbr-roster.json` (weekly CI from cookcountyboardofreview.com) | cookCountyCoverage |
| `fire-district` | Fire Protection District | safety | CountyDispatch | Cook County GIS L17 (Clerk fire tax-agency tiling) · Will County ArcGIS · DuPage County ArcGIS (`Fire_Protection_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L4) · Kane County ArcGIS (`KaneCo_IL_Districts_Fire` L1, IDOR-coded districts only) · McHenry County ArcGIS (`Fire_Districts` L0, 19 after the loader excludes the 8 'Z NO FIRE DISTRICT' fillers, the municipal Crystal Lake city-fire row, and the overlapping Marengo rescue-squad district — a 70 ILCS 3105 ambulance body, not a fire protection district) · Kendall County ArcGIS Enterprise (`Fire_Protection_Districts` L0 — the parcel-derived tax-code tiling, 10 FPDs after excluding the municipal 'CITY OF JOLIET FIRE DISTRICT' rows; hairline no-result gaps at unparceled slivers) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/10`, 17) · Madison (`MadCo/FireDistrictsWS/0`, 42) · DeKalb AGOL (`PT_Fire_Districts/4`, 18 — Esri-JSON fetch) · Lee (`leecogis`, 22 NG911 service areas) · Rock Island (county TaxDistricts tiling, 17) · Sangamon AGOL (`FireDistrictEtc` L2 — 226 fragments grouped per district at load into 29 FPDs + `SPRINGFIELD CORP`, the city's corporate area, whose card states it is served by the city's own Fire Department rather than an FPD) · St. Clair (`CentralSquare/DATA/8`, the county's CAD folder — 44 named departments; disttype/agency declared and 0/44 populated, so the taxing-vs-dispatch caveat rides every card) · Stephenson **georeferenced** (`stephenson-fire-districts.json` — the county's 2014 vector-PDF fire map measured by scripts/build_stephenson_fire_districts.py, hydrography-fitted; 15 named services, 2014-vintage caveat on every card) | Cook: name-only; Will: trustees in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: chief + office contact in GIS attrs; McHenry + Kendall + Kankakee + DeKalb + Lee + Rock Island: name-only; Madison: dept head + address + phone + URL in GIS attrs (the fleet's first contact-bearing fire entry); Sangamon + St. Clair + Stephenson: name-only | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/lee/rock-island/sangamon/st-clair/stephenson county coverages |
| `dupage-county-special-police` | DuPage Special Police District | safety | Polygon | DuPage County ArcGIS (`Special_Police_Districts_`, "Real Estate Tax Code polygons") | link-only (elected DuPage County Sheriff; unincorporated-area police-tax district) | dupageCountyCoverage |
| `park-district` | Park District | geography | CountyDispatch | Cook County GIS L23 (Clerk park tax-agency tiling, incl. the Chicago Park District) · Will County ArcGIS · DuPage County ArcGIS (`Park_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L11) · Kane County ArcGIS (`KaneCo_IL_Districts_Park` L1) · Kendall County ArcGIS Enterprise (`Park_Districts` L0 tax-code tiling, 5 genuine districts — Fox Valley/Joliet/Oswegoland/Plainfield/Sandwich) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/5`, 4) · Madison (6) · DeKalb AGOL (`PT_Park_Districts/9`, 6 — Esri-JSON fetch) · Rock Island (1, Cordova) — McHenry: recorded gap, publishes facilities not district boundaries | Cook: name-only; Will: commissioners in GIS attrs; DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only | OR of cook/will/dupage/lake/kane/kendall/kankakee/madison/dekalb/rock-island county coverages |
| `library-district` | Library District | geography | CountyDispatch | Cook County GIS L20 (Library Tax District) + L19 (Library Fund) · Will County ArcGIS (`Library_District`) · DuPage County ArcGIS (`Library_Districts_`) · Lake County ArcGIS (`LakeCounty_TaxDistricts` L8) · Kane County ArcGIS (`KaneCo_IL_Districts_Library` L1) · McHenry County ArcGIS (`Library_Districts` L0, 13 after the loader excludes 6 'Z_None' fillers + the lone municipal Crystal Lake city row) · Kendall County ArcGIS Enterprise (`Library_Districts` L0 tax-code tiling, 9 bodies incl. the municipal Joliet/Yorkville city-library funds — Kendall's tiling records EVERY library taxing body, the Cook-style complete shape, so its municipal rows stay) · Kankakee `k3gis.net` (`BASE/Taxing_Districts2/3`, 8) · Madison (18) · DeKalb AGOL (`PT_Library_Districts/7`, 13 — Esri-JSON fetch) · Rock Island (9 named districts; the un-districted remainder polygon is dropped in the loader) | Cook: agency name + a Type row distinguishing district vs municipal fund; Will: trustees in GIS attrs (sparse); DuPage: name-only; Lake: district office contact in GIS attrs; Kane: board president + office contact in GIS attrs; McHenry + Kendall + Kankakee + Madison + DeKalb + Rock Island: name-only | OR of cook/will/dupage/lake/kane/mchenry/kendall/kankakee/madison/dekalb/rock-island county coverages |
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
| `county-precinct` | Voting Precinct | geography | CountyDispatch | Cook County GIS (`precinctHistorical` L0, the Clerk's current suburban fabric, 1,430 — same geometry as Socrata `k7sw-w3b8`) · Will County ArcGIS `Precincts_2022` · DuPage County ArcGIS `Precincts_2024` (current 600-precinct map) · Lake County ArcGIS (`LakeCounty_PoliticalBoundaries` L7, 431) · Kane County ArcGIS (`KaneCo_IL_ElectionsPrecincts` L1, 292 — township named from the clerk's own Maps-page prefix pairing, election-day polling joined 292/292 from `KaneCo_IL_Elections_PollingPlaces` and labelled with its Election field, 2026-08-02) · McHenry County ArcGIS (`Precincts` L0, 223) · Kendall County ArcGIS Enterprise (`Voting_Precincts_and_Polling_Places` L1 `status='A'`, 78 — township names derived at load from the county's own townships layer, the assigned polling place joined by GlobalID from L0) · LaSalle self-hosted (`PollingPlaceLocator/1`, 119 + polling points joined 119/119 on `USER_Precinct`) · Kankakee `k3gis.net` (`BASE/Elected_Officials/0`, 59, name-only) · Boone (37, polling place carried ON the feature) · Grundy (40, polling joined 38/40 on `POLLINGID`) · Macoupin Socrata (`ab79-cnsh`, 45 — the current 2022-2032 fabric, refreshed upstream 2025-11; polling joined 45/45 from the clerk's own Socrata polling dataset (`rc5v-ajnf`) by deterministic label expansion, 2026-08-02) · Madison (191, `pollingid` GlobalID join 191/191) · St. Clair (`SCC_voting_districts`, 150 — polling is a recorded gap) · Winnebago WinGIS (`WardsAndDistricts/7`, 94, county-clerk jurisdiction only — Rockford runs its own election commission) · DeKalb AGOL (`Precincts/1`, 69) · Lee (46) · Whiteside (60, polling joined 55/60 — recorded gap) · Rock Island (120) · McLean (`Clerks/PollingPlaces` L1, 141 — polling joined 141/141 by POLLINGID from L0) · Logan (TCRPC `Logan_County_Districts_and_Zoning/40`, 29 township-named — the clerk's HTML polling table ships as `logan-precinct-polling.json`, joined 29/29) · Sangamon AGOL (`ApprovedPrecincts20231012`, 166 — polling joined 165/166 by POLLID from `ElectionPollingAndPrecincts` L0) · Carroll (TIGERweb Census-2020 VTDs live, 22 — the county did not re-precinct; the clerk's polling notice ships as `carroll-precinct-polling.json`, joined 22/22) · Woodford (TCRPC election service, 37 — polling joined 37/37 on the numeric polling reference, the precinct's own name cross-checked in the polling row's grouped label) | County Board district via spatial join (Cook: Commissioner District; Kane: carried on the features); Kendall also shows the county's own polling-place assignment; each card links its county clerk | suburban-Cook (in Cook AND NOT Chicago — city precincts are the BOE's `ward-precinct` layer) OR will/dupage/lake/kane/mchenry/kendall/lasalle/kankakee/boone/grundy/macoupin/madison/st-clair/dekalb/lee/whiteside/rock-island/mclean/logan/sangamon/carroll/woodford county coverages, plus Winnebago-outside-Rockford (subOf `township`) |
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

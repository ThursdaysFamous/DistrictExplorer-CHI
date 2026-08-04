# Illinois county completion status

<!-- ==== GENERATED FILE — DO NOT HAND-EDIT ==== -->
<!-- Emitted by scripts/build_county_status.py from the coverage-ring
     lists (scripts/build_metro_outline.py), index.html's dispatch
     tables, data/app/coverage-gaps.json and
     data/app/il-county-commissioners.json. Regenerate:
         python3 scripts/build_county_status.py
     CI drift gate (smoke-test.yml):
         python3 scripts/build_county_status.py --check -->

**53 of 102 Illinois counties are served** — 43 through their own dispatch entries, 5 through a shipped judicial circuit, and 5 through the County card alone. 49 more are researched-but-unserved (every one carries a recorded gap saying why), leaving 0 unresearched.

## How to read this

- **Served through** — `dispatch`: the county has its own entries in index.html's county dispatch tables; `judicial circuit`: a secondary county of a shipped judicial circuit (its only county-specific card is the subcircuit); `County card`: an at-large county with no district geometry, its board riding the County card (`docs/EXPANSION_GUIDE.md` §2.5.1).
- **Board** — how the county board surfaces: `districted` (own `county-board` dispatch entry), `at-large — County card` (data/app/il-county-commissioners.json), or a pointer to the gap record that says why neither ships.
- **County-keyed dispatch entries** — read from index.html itself, the same scan `validate_index.py` check 8 gates on.
- **Open gaps** — records from the guidebook's gaps block (`data/app/coverage-gaps.json`, the app's Data gaps panel). A record naming several counties appears in each of their rows.
- **"Complete"** here means: served, and `none` in the gaps column. A served county with open gaps is honest-but-unfinished; what each gap needs is the record's `wanted` line in the guidebook.

## Served counties (53)

| County | FIPS | Served through | Board | County-keyed dispatch entries | Open gaps |
|---|---|---|---|---|---|
| Adams | 17001 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district` | 2 — `adams-county-board-roster` (no-source); `quincy-ward-officeholders` (no-source) |
| Bond | 17005 | judicial circuit | no board layer — see gaps | — | none |
| Boone | 17007 | dispatch | districted | `county-board`, `county-precinct`, `fire-district` | 3 — `boone-fire-names` (data-quality); `boone-municipal-officials` (no-source); `boone-park-library-districts` (no-source) |
| Brown | 17009 | County card | at-large — County card | — | 1 — `brown-precinct-geometry` (no-source) |
| Calhoun | 17013 | County card | at-large — County card | — | 1 — `calhoun-precinct-geometry` (no-source) |
| Carroll | 17015 | dispatch | districted | `county-board`, `county-precinct` | 3 — `carroll-special-districts` (no-source); `carroll-ward-geometry` (no-source); `county-board-office-addresses` (no-source) |
| Cass | 17017 | dispatch | districted | `county-board` | 1 — `pass9-ward-seats-without-maps` (no-source) |
| Cook | 17031 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | none |
| De Witt | 17039 | dispatch | districted | `county-board`, `county-precinct` | none |
| DeKalb | 17037 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | 4 — `blocked-crawlers` (blocked); `county-board-office-addresses` (no-source); `dekalb-hinckley-board` (data-quality); `dekalb-precinct-codes` (data-quality) |
| DuPage | 17043 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | 4 — `aurora-council-contact` (data-quality); `county-board-office-addresses` (no-source); `dupage-municipal-phones` (data-quality); `dupage-ward-cities` (no-source) |
| Fulton | 17057 | dispatch | districted | `county-board`, `county-precinct` | none |
| Greene | 17061 | judicial circuit | no board layer — see gaps | — | none |
| Grundy | 17063 | dispatch | districted | `county-board`, `county-precinct` | 2 — `grundy-special-districts` (no-source); `morris-ward-geometry` (no-source) |
| Henry | 17073 | dispatch | districted | `county-board` | 2 — `henry-county-precincts` (no-source); `pass9-ward-seats-without-maps` (no-source) |
| Iroquois | 17075 | dispatch | districted | `county-board`, `county-precinct`, `fire-district` | none |
| Jersey | 17083 | judicial circuit | no board layer — see gaps | — | none |
| Kane | 17089 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | 2 — `aurora-council-contact` (data-quality); `county-board-office-addresses` (no-source) |
| Kankakee | 17091 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | 5 — `county-board-office-addresses` (no-source); `kankakee-city-wards` (no-source); `kankakee-municipal-officials` (no-source); `kankakee-special-districts` (data-quality); `momence-ward-geometry` (no-source) |
| Kendall | 17093 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | 4 — `aurora-council-contact` (data-quality); `blocked-crawlers` (blocked); `county-board-office-addresses` (no-source); `plano-ward-officials` (no-source) |
| LaSalle | 17099 | dispatch | districted | `county-board`, `county-precinct` | 5 — `county-board-office-addresses` (no-source); `lasalle-board-districts-stale` (no-source); `lasalle-municipal-wards` (no-source); `ogle-lasalle-special-districts` (no-source); `wenona-two-clerks-disagree` (data-quality) |
| Lake | 17097 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | 2 — `lake-municipal-names` (no-source); `park-city-wards` (no-source) |
| Lee | 17103 | dispatch | districted | `county-board`, `county-precinct`, `fire-district` | 3 — `county-board-office-addresses` (no-source); `lee-municipal-officials` (no-source); `lee-park-library-districts` (no-source) |
| Livingston | 17105 | dispatch | districted | `county-board` | 3 — `county-board-office-addresses` (no-source); `livingston-precincts` (no-source); `livingston-special-districts` (no-source) |
| Logan | 17107 | dispatch | districted | `county-board`, `county-precinct` | 2 — `county-board-office-addresses` (no-source); `logan-fire-districts` (no-source) |
| Macon | 17115 | dispatch | no board layer — see gaps | `county-precinct`, `fire-district`, `library-district`, `park-district` | 2 — `macon-county-board-labels` (data-quality); `macon-district-name-formatting` (data-quality) |
| Macoupin | 17117 | dispatch | no board layer — see gaps | `county-precinct` | 4 — `macoupin-county-board-districts` (no-source); `macoupin-municipal-officials` (blocked); `macoupin-special-districts` (no-source); `macoupin-ward-geometry` (no-source) |
| Madison | 17119 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | 2 — `county-board-office-addresses` (no-source); `madison-ward-officials` (no-source) |
| Marshall | 17123 | dispatch | districted | `county-board` | 2 — `marshall-precinct-geometry` (no-source); `wenona-two-clerks-disagree` (data-quality) |
| Mason | 17125 | dispatch | districted | `county-board` | 1 — `mason-precinct-vintage` (data-quality) |
| McDonough | 17109 | dispatch | districted | `county-board`, `county-precinct` | none |
| McHenry | 17111 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district` | 4 — `blocked-crawlers` (blocked); `county-board-office-addresses` (no-source); `mchenry-park-district` (no-source); `mchenry-ward-cities` (blocked) |
| McLean | 17113 | dispatch | districted | `county-board`, `county-precinct` | 2 — `county-board-office-addresses` (no-source); `mclean-special-districts` (no-source) |
| Monroe | 17133 | dispatch | at-large — County card | `county-precinct` | 1 — `monroe-fire-district-names` (no-source) |
| Morgan | 17137 | judicial circuit | no board layer — see gaps | — | none |
| Ogle | 17141 | dispatch | districted | `county-board`, `county-precinct` | 3 — `county-board-office-addresses` (no-source); `ogle-lasalle-special-districts` (no-source); `ogle-municipal-wards` (no-source) |
| Peoria | 17143 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | 2 — `pass9-ward-seats-without-maps` (no-source); `peoria-fire-park-library-contact` (data-quality) |
| Pike | 17149 | County card | at-large — County card | — | 1 — `pike-precinct-geometry` (no-source) |
| Putnam | 17155 | County card | at-large — County card | — | 1 — `putnam-precinct-geometry` (no-source) |
| Randolph | 17157 | dispatch | at-large — County card | `county-precinct` | 2 — `randolph-fire-park-library` (no-source); `randolph-precinct-polling` (data-quality) |
| Rock Island | 17161 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | 1 — `county-board-office-addresses` (no-source) |
| Sangamon | 17167 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit` | 2 — `county-board-office-addresses` (no-source); `sangamon-park-library-districts` (no-source) |
| Schuyler | 17169 | County card | at-large — County card | — | none |
| Scott | 17171 | judicial circuit | no board layer — see gaps | — | none |
| St. Clair | 17163 | dispatch | districted | `county-board`, `county-precinct`, `fire-district` | 4 — `county-board-office-addresses` (no-source); `st-clair-board-contact` (data-quality); `st-clair-park-library-districts` (no-source); `st-clair-precinct-polling-places` (data-quality) |
| Stark | 17175 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `library-district`, `park-district` | none |
| Stephenson | 17177 | dispatch | districted | `county-board`, `county-precinct`, `fire-district` | 4 — `county-board-office-addresses` (no-source); `dakota-village-president` (no-source); `stephenson-freeport-precincts` (data-quality); `stephenson-park-library-districts` (no-source) |
| Tazewell | 17179 | dispatch | districted | `county-board`, `county-precinct` | 1 — `tazewell-precinct-polling` (data-quality) |
| Washington | 17189 | dispatch | districted | `county-board` | 1 — `washington-precinct-geometry` (no-source) |
| Whiteside | 17195 | dispatch | districted | `county-board`, `county-precinct` | 4 — `county-board-office-addresses` (no-source); `whiteside-municipal-officials` (no-source); `whiteside-precinct-polling` (data-quality); `whiteside-special-districts` (no-source) |
| Will | 17197 | dispatch | districted | `county-board`, `county-precinct`, `fire-district`, `judicial-subcircuit`, `library-district`, `park-district` | 3 — `aurora-council-contact` (data-quality); `county-board-office-addresses` (no-source); `joliet-municipal-contact` (blocked) |
| Winnebago | 17201 | dispatch | districted | `county-board`, `county-precinct`, `judicial-subcircuit` | 4 — `county-board-office-addresses` (no-source); `rockford-city-precincts` (no-source); `winnebago-special-districts` (no-source); `winnebago-village-heads` (no-source) |
| Woodford | 17203 | dispatch | districted | `county-board`, `county-precinct` | 1 — `woodford-special-districts` (no-source) |

## Researched frontier (49) — gap-recorded, not yet served

Counties outside the coverage ring that a research pass has already measured; each row's records say what blocks it and what a submission would need to contain.

| County | FIPS | Gap records |
|---|---|---|
| Alexander | 17003 | 1 — `alexander-county-board` (no-source) |
| Bureau | 17011 | 1 — `bureau-county-board-districts` (no-source) |
| Champaign | 17019 | 1 — `champaign-piatt-ccgisc-license` (blocked) |
| Christian | 17021 | 1 — `christian-county-board-districts` (no-source) |
| Clark | 17023 | 1 — `clark-county-board` (no-source) |
| Clay | 17025 | 1 — `clay-county-board` (no-source) |
| Clinton | 17027 | 1 — `clinton-county-board-geometry` (no-source) |
| Coles | 17029 | 1 — `coles-county-board` (no-source) |
| Crawford | 17033 | 1 — `crawford-county-board` (no-source) |
| Cumberland | 17035 | 1 — `cumberland-county-board` (no-source) |
| Douglas | 17041 | 1 — `douglas-county-board-districts` (no-source) |
| Edgar | 17045 | 1 — `edgar-county-board` (no-source) |
| Edwards | 17047 | 1 — `edwards-county-board` (no-source) |
| Effingham | 17049 | 1 — `effingham-municipal-officials` (no-source) |
| Fayette | 17051 | 1 — `fayette-county-board-geometry` (no-source) |
| Ford | 17053 | 1 — `ford-county-board-vintage` (no-source) |
| Franklin | 17055 | 1 — `franklin-county-board-districts` (no-source) |
| Gallatin | 17059 | 1 — `gallatin-county-board` (no-source) |
| Hamilton | 17065 | 1 — `hamilton-county-board` (no-source) |
| Hancock | 17067 | 1 — `pass10-frontier-unasked` (no-source) |
| Hardin | 17069 | 1 — `hardin-county-board` (no-source) |
| Henderson | 17071 | 1 — `henderson-county-website` (no-source) |
| Jackson | 17077 | 1 — `pass10-frontier-unasked` (no-source) |
| Jasper | 17079 | 1 — `jasper-county-board` (no-source) |
| Jefferson | 17081 | 1 — `pass10-frontier-unasked` (no-source) |
| Jo Daviess | 17085 | 1 — `jo-daviess-county-board-districts` (no-source) |
| Johnson | 17087 | 1 — `johnson-county-board` (no-source) |
| Knox | 17095 | 2 — `galesburg-wards-outside-the-ring` (data-quality); `knox-county-board-districts` (no-source) |
| Lawrence | 17101 | 1 — `lawrence-county-board` (no-source) |
| Marion | 17121 | 1 — `pass10-frontier-unasked` (no-source) |
| Massac | 17127 | 1 — `massac-county-board` (no-source) |
| Menard | 17129 | 1 — `menard-commissioner-districts` (no-source) |
| Mercer | 17131 | 1 — `mercer-county-board-districts` (no-source) |
| Montgomery | 17135 | 1 — `montgomery-county-board-geometry` (no-source) |
| Moultrie | 17139 | 1 — `moultrie-county-board` (no-source) |
| Perry | 17145 | 1 — `perry-county-website-blocked` (blocked) |
| Piatt | 17147 | 1 — `champaign-piatt-ccgisc-license` (blocked) |
| Pope | 17151 | 1 — `pope-county-board` (no-source) |
| Pulaski | 17153 | 1 — `pulaski-county-board` (no-source) |
| Richland | 17159 | 1 — `richland-county-board` (no-source) |
| Saline | 17165 | 1 — `saline-county-board` (no-source) |
| Shelby | 17173 | 1 — `shelby-county-board` (no-source) |
| Union | 17181 | 1 — `union-county-board` (no-source) |
| Vermilion | 17183 | 1 — `vermilion-county-website` (no-source) |
| Wabash | 17185 | 1 — `wabash-county-board` (no-source) |
| Warren | 17187 | 1 — `pass10-frontier-unasked` (no-source) |
| Wayne | 17191 | 1 — `wayne-county-board` (no-source) |
| White | 17193 | 1 — `white-county-board` (no-source) |
| Williamson | 17199 | 1 — `williamson-county-board` (no-source) |

## Unresearched (0)

.

## Gap records not tagged to a county (1)

City- or app-scoped records with no `counties` tag, listed so the table reconciles with the 118 records in the Data gaps panel: `chicago-amenity-phones`.

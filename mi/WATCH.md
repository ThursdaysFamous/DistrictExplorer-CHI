# WATCH.md — redistricting watch calendar

The one place the dates live: *when to look* for boundary and roster changes in this
instance's sources. The repo's `docs/REDISTRICTING_RUNBOOK.md` is *what to do* when a
boundary changes. Update the "Last done" column each time you complete a row — a
checkpoint with a stale date is a checkpoint that didn't happen.

---

## Standing (automated — verify, don't perform)

| Cadence | What | Where | You do |
|---|---|---|---|
| Weekly (Mon 15:30 UTC) | U.S. House (MI) roster refresh | `.github/workflows/update-mi-congress-roster.yml` → PR on change | Review + merge the PR; a week with a surprise diff is worth a look at the source |
| Weekly (Tue 15:30 UTC) | Michigan Senate + House roster refresh (Open States mi.csv + the Senate's own all-senators directory) | `.github/workflows/update-mi-legislature-roster.yml` → PR on change | Review + merge the PR — especially after a Michigan general (November, even years) and each January seating |
| Monthly (1st, 16:00 UTC) | Source freshness for every dataset this instance depends on | `.github/workflows/mi-validate-sources.yml` → tracking issue on WARN/FAIL | Read the issue; the job stays green on purpose |
| Monthly, with the run above | **The commissioner layer's own republish signal, which its endpoint cannot give.** The service carries no `editingInfo`, no `lastEditDate` and no date field, so a republish is invisible there | `arcgis.com/sharing/rest/content/items/4c8d0d854ac04d8787cb3cf6dab7fbec?f=json` — compare `modified` against **1764783222000** (2025-12-03) and the title's own `vNN` suffix against **v25** | If either moved, re-run `mi/scripts/build_mi_commissioner_districts.py` and diff: the count guard (619/83) fails loudly on an apportionment, and a quiet change is a correction |

---

## Open questions this instance owes an answer to

| Question | Why it is open | What would close it |
|---|---|---|
| **Who are Michigan's 619 county commissioners?** | The `county-commissioner` layer names the district and not the person, because the only statewide name source — the Commissioner/Party columns on the boundary layer itself — is a list of the certified **November 2024 election winners**, not a maintained roster. Measured 2026-09-03: 93.5% right, every miss the same direction, and Wayne District 5 still names a commissioner who died on 10 June 2025. Recorded as gap `mi-commissioner-roster` | A county-by-county roster build against each county's own board page, weekly and count-guarded — the route every other instance uses. Ten of the twelve counties sampled publish a readable one. Oakland answers only through its CMS origin (`www.oakgov.com` is an Akamai 403 to this client); Ottawa is behind an sgcaptcha gate, which is an access control this project does not route around |
| **Six western-UP counties hand off to Wisconsin, and no rectangle can fix it.** | Michigan's TIGERweb county fabric is WATER-INCLUSIVE, so the state's own bbox runs west across Lake Michigan to -90.42 and contains both Chicago's centre (41.8781, -87.6298) and Wisconsin's (44.9, -89.565) — `validate_index.py` hard-fails `il` and `wi` on it, since a metro must never claim a sibling's centre. The shipped fleet bbox is therefore the county fabric clipped to `lng >= -87.60` (measured, 2026-09-03), which leaves **Baraga, Dickinson, Gogebic, Houghton, Iron and Ontonagon** outside the portal HAND-OFF box. They are offered Wisconsin instead — which is exactly what they got before Michigan existed, since `wi`'s own bbox already covers them — and Michigan's app still ANSWERS there, because `metro_bbox` is untouched and full-state. Narrowing cannot fix it and neither can widening: the western UP shares Wisconsin's longitudes, so no axis-aligned rectangle separates them | Change the portal's tie-break from **nearest bbox CENTRE** to **smallest bbox AREA**. Measured over 26 probe cities during the go-live sweep, that drops misroutes from 13 to 5 on the FULL honest bbox. It is an engine change (`metroAt` in every instance's `index.html`, plus `build_landing_page.py`'s own copy for the address box), so it touches all six instances and wants its own PR and its own probe set — deliberately NOT folded into go-live |
| **Is `house.mi.gov` actually unreachable, or is this sandbox?** | The Michigan House site fails TLS from the build environment with "unable to get local issuer certificate" even with the egress proxy's CA bundle supplied, while `senate.michigan.gov` answers 200 on identical flags and the proxy logs no relay failure. That is the incomplete-chain shape this repo documents for Coles, Gallatin and Vermilion — **but TLS is re-terminated at the proxy here, so this environment cannot see the site's real chain at all.** A measurement is not a conclusion (`docs/EXPANSION_GUIDE.md` §0.4). | ONE CI-side probe, from a GitHub Actions runner rather than this sandbox. If the site answers there, the House card gains the same capitol contact block the Senate card already has, from the House's own directory. If it fails there too with a leaf-only chain, `scripts/probe_incomplete_tls_chains.py` reports the intermediate's SHA-256 and a scraper PINS it — never by disabling verification. |
| ~~When does the Bureau of Elections republish the commissioner-district layer?~~ **ANSWERED 2026-09-03** | It has not, and there is no successor: all 294 `michigan_admin` AGO items were enumerated and exactly one is a commissioner-district item, while the state's own current Election District Viewer (touched 2026-07-31) still wires this exact endpoint. Michigan counties reapportion on the decennial census (MCL 46.404), so the next plan is ~2031. | Closed. The republish WATCH now has a concrete mechanism — the standing monthly row above, against the AGO item's `modified` epoch, because the service itself carries no date field of any kind. |

---

## Per-election — the seats above the boundaries

| When | What | Last done |
|---|---|---|
| After each Michigan general (November, even years) and any special election | The chamber rosters turn over; the weekly Open States refresh picks it up, but verify the first post-election PR against each chamber's own directory before merging | 2026-09-03 (initial build: 38/38 Senate seats, 110/110 House seats — no vacancies at arrival) |
| After each U.S. general (November, even years) | The delegation turns over; the weekly congress-legislators refresh picks it up | 2026-09-03 (initial build: 13/13) |

---

## Per-decade — the census redistricting cycle

| When | What | Last done |
|---|---|---|
| After each decennial census (P.L. 94-171 release, spring of the year after) | Every boundary this instance ships is redrawn. Michigan's congressional and legislative lines are drawn by the **Independent Citizens Redistricting Commission** (2018 Prop 2), not the legislature; county commissioner districts are redrawn by each county's own apportionment commission under MCL 46.404/46.405. Rebuild all three chamber files and the county file, then re-anchor the smoke test | 2026-09-03 (built against the 2020-cycle maps) |
| After each decennial census, ~2031 | **County commissioner districts are reapportioned** by each county's own apportionment commission under MCL 46.404, and the Bureau of Elections recompiles the statewide layer. The 2021 plans shipped here run the 2020-census cycle | 2026-09-03 (built against the 2021 plans, 619 districts / 83 counties) |
| After each Michigan general seating commissioners (November 2028, then every 4 years) | Terms went to FOUR years under PA 121-122 of 2021, so the boards seated January 2025 run to December 2028 — there is NO 2026 commissioner election, and a re-verify scheduled for then would be wasted. The live risk between generals is mid-term vacancies | 2026-09-03 (no roster shipped; see the open question above) |
| Whenever TIGERweb rolls a vintage | **The congressional layer's district field is versioned and the old one is REMOVED, not merely stale.** It rolled to `CD120` for the 120th Congress; a query naming the retired `CD119` returns HTTP 400, "Failed to execute query" — measured 2026-09-03. `mi/scripts/build_legislative_boundaries.py` names `CD120`; the app's `CONGRESS_DISTRICT_FIELDS` lists it first with `cd119` behind it. On the next roll, both need the new name | 2026-09-03 (CD120) |

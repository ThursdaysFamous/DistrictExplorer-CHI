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

---

## Open questions this instance owes an answer to

| Question | Why it is open | What would close it |
|---|---|---|
| **Is `house.mi.gov` actually unreachable, or is this sandbox?** | The Michigan House site fails TLS from the build environment with "unable to get local issuer certificate" even with the egress proxy's CA bundle supplied, while `senate.michigan.gov` answers 200 on identical flags and the proxy logs no relay failure. That is the incomplete-chain shape this repo documents for Coles, Gallatin and Vermilion — **but TLS is re-terminated at the proxy here, so this environment cannot see the site's real chain at all.** A measurement is not a conclusion (`docs/EXPANSION_GUIDE.md` §0.4). | ONE CI-side probe, from a GitHub Actions runner rather than this sandbox. If the site answers there, the House card gains the same capitol contact block the Senate card already has, from the House's own directory. If it fails there too with a leaf-only chain, `scripts/probe_incomplete_tls_chains.py` reports the intermediate's SHA-256 and a scraper PINS it — never by disabling verification. |
| **When does the Bureau of Elections republish the commissioner-district layer?** | The flagship layer (`2021 County Commissioner Districts v25`) carries commissioner names and party derived from the canvassed **November 2024** election, and county apportionment commissions file under MCL 46.404/46.405 on the census cycle. A roster attached to a boundary is refreshed when the boundary is — which is exactly why those names are not shipped yet. | Re-fetch the layer's item metadata after each November general and compare its edit timestamp and a sample of `Commissioner`/`Party` values against the certified canvass before shipping any name from it. |

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
| Whenever TIGERweb rolls a vintage | **The congressional layer's district field is versioned and the old one is REMOVED, not merely stale.** It rolled to `CD120` for the 120th Congress; a query naming the retired `CD119` returns HTTP 400, "Failed to execute query" — measured 2026-09-03. `mi/scripts/build_legislative_boundaries.py` names `CD120`; the app's `CONGRESS_DISTRICT_FIELDS` lists it first with `cd119` behind it. On the next roll, both need the new name | 2026-09-03 (CD120) |

<!-- ==== GENERATED:BEGIN metro-header ==== -->
# Wisconsin District Explorer

**Click any point in Wisconsin — or search an address — and see every civic district that contains it, and who represents you there.**
<!-- ==== GENERATED:END metro-header ==== -->

A single-file, dependency-light web app: one `index.html`, Leaflet for the map, no build step, no framework, no server-side code. One instance of the [districtry](https://districtry.com/) fleet, serving at **[districtry.com/wi/](https://districtry.com/wi/)** — the first state to expand **in place** as a folder of the consolidated repo rather than as a fork.

Seventeen statewide layers — thirteen from national publishers, four from state sources:

| Group | Layer | Source |
|---|---|---|
| **Political** | U.S. House District | U.S. Census TIGERweb boundary (pre-built, shipped with the app) + the public-domain [congress-legislators](https://github.com/unitedstates/congress-legislators) roster, refreshed weekly by CI |
| | WI Senate District (33) | TIGERweb Legislative boundary (pre-built, 2,000-point agreement gate) + the [Open States](https://openstates.org) roster, refreshed weekly by CI |
| | WI Assembly District (99) | Same pair as the Senate — boundary pre-built, roster from Open States |
| | Court of Appeals District (4) | County unions under the same double-witness discipline (Wis. Stat. 752.11 + the court system's own lists) — judges elected by district, all sixteen named with phones and chambers, refreshed weekly by CI |
| | Circuit Court (69) | County unions under a double witness (Wis. Stat. 753.06 + the court system's own listing) — geometry derived, never drawn — with the full bench from wicourts.gov: 261 judges, branch and direct phone where published, courthouse per circuit, refreshed weekly by CI |
| | County Board District (1,590) | Wisconsin LTSB's statewide aggregate of every county's twice-yearly filing (Wis. Stat. 5.15(4)(br)1), pre-built; Trempealeau County's 17 from the county's own service; supervisors named in the 20 counties that publish a district-keyed member list, refreshed weekly by CI |
| **Public Safety** | Police Station / Fire Station | USGS National Map structures, nearest three each — a proximity fact, never a claim about which agency serves the point |
| **Schools** | School District — Unified / Union High / Elementary | TIGERweb School layers 0/1/2; the tilings are mutually exclusive, so exactly one of Unified and the pair answers for any point |
| **Geography** | County | TIGERweb State_County, pre-built — the app's offline anchor; names the county clerk (party or appointed, office, hours, contact) from the Blue Book cross-gated against the clerks' own association, refreshed weekly by CI; Milwaukee's card states that its elections sit with the appointed county Election Commission |
| | County Subdivision | TIGERweb CouSub, live (Wisconsin's towns) |
| | Municipality | TIGERweb Places, live (cities and villages; unincorporated points say so) |
| | Municipal Ward (7,161) | Wisconsin LTSB's live statewide ward layer — the ballot sub-unit every district is composed from; the card cross-references the county board district and, where a city elects by district, the aldermanic district, and links MyVote for the polling place |
| | ZIP Code | TIGERweb ZCTA by state envelope, live |
| | Post Office | USGS National Map structures, nearest three |

Everything beyond these is this instance's own growth — laid out in [`docs/WI_PHASE2_PLAN.md`](../docs/WI_PHASE2_PLAN.md) (municipal wards, the courts, station and school points, the county clerk on the county card) and added layer by layer as Wisconsin's publishers are proven out, following the repo's [`docs/EXPANSION_GUIDE.md`](../docs/EXPANSION_GUIDE.md). What no publisher answers — the county-supervisor roster in the 52 counties that publish none — is recorded in the app's Data gaps panel rather than papered over.

## Running it

```bash
# From the repo root — one server, every instance:
python3 -m http.server 8000    # then open http://localhost:8000/wi/
```

The gates, generated regions, engine composition and data pipeline are documented in [`wi/CLAUDE.md`](CLAUDE.md); the fleet-wide architecture in the repo root's [`CLAUDE.md`](../CLAUDE.md).

## Honesty rules

Officeholder data is never guessed: a vacant or unsourced seat degrades to the district number and the official body's own directory. Every layer carries a provenance row on [sources.html](https://districtry.com/wi/sources.html), and what the app *cannot* answer is recorded in its Data gaps panel rather than papered over. Not for legal or official use.

<!-- ==== GENERATED:BEGIN metro-header ==== -->
# Wisconsin District Explorer

**Click any point in Wisconsin — or search an address — and see every civic district that contains it, and who represents you there.**
<!-- ==== GENERATED:END metro-header ==== -->

A single-file, dependency-light web app: one `index.html`, Leaflet for the map, no build step, no framework, no server-side code. One instance of the [districtry](https://districtry.com/) fleet, serving at **[districtry.com/wi/](https://districtry.com/wi/)** — the first state to expand **in place** as a folder of the consolidated repo rather than as a fork.

Eleven statewide layers, all from national publishers:

| Group | Layer | Source |
|---|---|---|
| **Political** | U.S. House District | U.S. Census TIGERweb boundary (pre-built, shipped with the app) + the public-domain [congress-legislators](https://github.com/unitedstates/congress-legislators) roster, refreshed weekly by CI |
| | WI Senate District (33) | TIGERweb Legislative boundary (pre-built, 2,000-point agreement gate) + the [Open States](https://openstates.org) roster, refreshed weekly by CI |
| | WI Assembly District (99) | Same pair as the Senate — boundary pre-built, roster from Open States |
| **Schools** | School District — Unified / Union High / Elementary | TIGERweb School layers 0/1/2; the tilings are mutually exclusive, so exactly one of Unified and the pair answers for any point |
| **Geography** | County | TIGERweb State_County, pre-built — the app's offline anchor |
| | County Subdivision | TIGERweb CouSub, live (Wisconsin's towns) |
| | Municipality | TIGERweb Places, live (cities and villages; unincorporated points say so) |
| | ZIP Code | TIGERweb ZCTA by state envelope, live |
| | Post Office | USGS National Map structures, nearest three |

Everything beyond these is this instance's own growth — county board supervisory districts first (the standing entry in the app's Data gaps panel), then precincts, police and fire districts, school zones — added layer by layer as Wisconsin's publishers are proven out, following the repo's [`docs/EXPANSION_GUIDE.md`](../docs/EXPANSION_GUIDE.md).

## Running it

```bash
# From the repo root — one server, every instance:
python3 -m http.server 8000    # then open http://localhost:8000/wi/
```

The gates, generated regions, engine composition and data pipeline are documented in [`wi/CLAUDE.md`](CLAUDE.md); the fleet-wide architecture in the repo root's [`CLAUDE.md`](../CLAUDE.md).

## Honesty rules

Officeholder data is never guessed: a vacant or unsourced seat degrades to the district number and the official body's own directory. Every layer carries a provenance row on [sources.html](https://districtry.com/wi/sources.html), and what the app *cannot* answer is recorded in its Data gaps panel rather than papered over. Not for legal or official use.

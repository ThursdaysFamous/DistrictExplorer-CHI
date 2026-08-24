<!-- ==== GENERATED:BEGIN metro-header ==== -->
# {{STATE_NAME}} District Explorer

**Click any point — or search an address — and see every civic district that contains it, and who represents you there.**
<!-- ==== GENERATED:END metro-header ==== -->

A single-file, dependency-light web app: one `index.html`, Leaflet for the map, no build step, no framework, no server-side code. Deploys as a static site to any static host ({{CANONICAL_URL}} via GitHub Pages out of the box).

**This repository was created from the District Explorer state-expansion template** — a generated artifact of the fleet's reference implementation, [`ThursdaysFamous/DistrictExplorer-CHI`](https://github.com/ThursdaysFamous/DistrictExplorer-CHI). It starts with five statewide layers any U.S. state can serve from national publishers, parameterized only by the state's FIPS code:

| Group | Layer | Source |
|---|---|---|
| **Political** | U.S. House District | U.S. Census TIGERweb boundary (pre-built, shipped with the app) + the public-domain [congress-legislators](https://github.com/unitedstates/congress-legislators) roster, refreshed weekly by CI |
| **Schools** | School District (Unified) | TIGERweb School layer, pre-built for the state |
| **Geography** | County | TIGERweb State_County, pre-built — the app's offline anchor |
| | County Subdivision | TIGERweb CouSub, live |
| | Municipality | TIGERweb Places, live |

Everything beyond these five is this fork's own growth: county boards, precincts, police and fire districts, school zones — added layer by layer as this state's publishers are proven out, following the reference repo's [`docs/EXPANSION_GUIDE.md`](https://github.com/ThursdaysFamous/DistrictExplorer-CHI/blob/main/docs/EXPANSION_GUIDE.md).

## Getting started (a fresh copy of the template)

```bash
# 1. Bootstrap: derive everything from the state itself (one TIGERweb pass)
python3 scripts/bootstrap_state.py \
  --state-fips 18 --state-name Indiana \
  --repo you/DistrictExplorer-IN --domain in.example.com \
  --brand-name "Indiana District Explorer"

# 2. Run it
python3 -m http.server 8000    # open http://localhost:8000/

# 3. Gates (the same battery CI runs)
python3 scripts/check_template_placeholders.py
python3 scripts/validate_index.py index.html
```

The bootstrap prints the registration checklist it cannot do itself — fleet registration in the reference repo, and the operator items (Pages + custom domain, `BOT_PR_TOKEN`, the Actions "allow PR creation" toggle, a GoatCounter site, real icons). Until it has run, CI fails by design on the placeholder gate.

## How this repo stays in sync with the fleet

The engine inside `index.html`/`sw.js` (fenced `ENGINE:BEGIN/END` blocks) is byte-identical across every District Explorer. It ships as a hash-verified release artifact from the reference repo, pinned in `engine.lock.json`; `.github/workflows/engine-bump.yml` answers each release with a validated PR, and every deploy re-splices and re-verifies the pinned bytes. Engine improvements made here are back-ported through the reference repo, never hand-edited in place — see `docs/ENGINE_SYNC.md`.

## Honesty rules

This is a public-facing civic tool that explicitly disclaims legal precision. Officeholder data is never guessed: where no verifiable roster source exists, cards link to the official body instead of inventing a name. Every scraped string renders sanitized. Roster changes always land as pull requests for human review.

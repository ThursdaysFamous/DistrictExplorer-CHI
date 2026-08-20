# Districtry rebrand — decision record & staged rollout

**What this is.** The record for the *Districtry* rebrand: the decisions that carried it, the
staged rollout plan, and the fix-list the package still owes before production adoption. The
reviewable package itself is deployed as an **unlisted preview at `/districtry/`** on the live
site (a new root directory ships automatically with the Pages deploy; `docs/` never ships, which
is why this file lives here and the preview does not).

**Hiddenness contract.** The preview is unlinked from the app, carries
`<meta name="robots" content="noindex, nofollow">` on every page, and stays out of
`sitemap.xml`. Deliberately **no** `robots.txt` `Disallow` — that would advertise the path while
preventing crawlers from ever reading the noindex. The repo is public, so this is soft-hidden:
the files are visible in the GitHub tree regardless. Accepted.

## Decisions of record

- **Name:** *Districtry* (district + directory) — never "Districtory". One indivisible lowercase
  word; instance tag suffix (`/ illinois`, `/ chicago`) in Barlow Condensed 400 at 80%.
- **Mark:** 5c — geometric lowercase *d* (ring + ascender, never typeset) over three translucent
  irregular polygons whose fills echo the map's layer encoding (brand violet #6d3fd1, data blue
  #1d5fd6, municipality magenta #b0316e). Multiply blends on light, screen on dark; flat
  one-polygon fallback below 24px. Full spec: `/districtry/Districtry Brand Spec.dc.html`.
- **Color, three tiers** (`/districtry/tokens/districtry.tokens.css`): **brand violet = chrome
  only** (buttons, links, pills, checked states — never map data); **chrome neutrals** = warm
  paper + inks; **data tier = map only** (blue #1d5fd6 selection/marker + per-layer colors).
  The current card system's `--card-accent #1d5fd6` *is* the data tier — the tokens keep the
  same hex on purpose; the rebrand moves interface chrome off blue so chrome and data never
  collide.
- **Type & spacing:** adopted from the bundled *Industry* design system — Barlow Condensed 600
  headings over Barlow body; card metrics keep the proven card-system values (16 / 14.5 /
  12.5px).
- **Positioning:** fleet-by-state, Illinois first; metro instances ride subdomains under one
  brand. Domain migration to districtry.com **is planned** (operator confirmed) and is the last,
  independent rollout phase.

## Provenance (package ↔ repo)

Package `Districtry_rebrand_refinement.zip`, rebuilt 2026-08-19 from this repo's ground truth
(sync record `github.md`, not committed — its content is this table):

| Deliverable | Built from |
|---|---|
| `Districtry App.dc.html` | `docs/design_handoff_card_system/Info Card Explorations.dc.html`, `docs/CARD_RENDER_API.md`, `sw.js`, `README.md`, `data/app/metro-outline.json` |
| `Districtry Brand Spec.dc.html` | card-handoff layer colors, `metros.json` |
| `Districtry Logo Wireframes.dc.html` | brand work; layer colors from the card handoff |
| `tokens/districtry.tokens.css` | card-handoff chrome grays + card metrics |

Not committed from the package: `icons/icon-192/512.png` and `og-image.png` (byte-identical
copies of the *current* brand, reference only), `data/app/metro-outline.json` (byte-identical
duplicate — the App canvas now fetches `../data/app/metro-outline.json` so its coverage map
tracks reality), `.thumbnail`, `github.md`.

## Functionality scope (operator decisions, 2026-08-20)

Everything the mockup shows that **already exists** in the app is *maintained* by the redesign —
verified existing: CARTO `light_all` basemap (identical tile URL, index.html:3255), the layer
toggle checkbox in the card header, the offices `<details>` accordion (`renderOfficeGroup`),
"Pin as parent" + relationship outlines, Copy link, hash permalinks, per-card
loading/empty/error states. **The single truly-new function is dark mode** (+ theme toggle,
`dark_all` basemap, dark icon variants, theme persistence) — zero dark-mode support exists
today; it is **deferred to its own approval** and is *not* part of Stage B or the base adoption.
The "N of 39 layers on" label is presentation of existing state — in scope as re-skin.

## Stage log

- **Stage A — SHIPPED (this change):** `/districtry/` microsite: landing page + the five design
  canvases (noindexed) + tokens + icons + OG card + manifest/head-snippet for later adoption.
  Purely additive — zero existing tracked files modified. Two package fixes applied: header stat
  60→69 counties (the mockup copied README's stale count), and the coverage fetch re-pointed at
  the live outline.
- **Stage B — PLANNED, not executed:** a working re-skinned copy of the real app at
  `/districtry-app.html` (root-level sibling, so every relative fetch resolves identically —
  zero path rewrites), produced by a committed transform script
  (`scripts/build_districtry_preview.py`) that applies an exactly-once-asserted substitution
  table to current `index.html`: strip GA (hostname gate would pass!) **and GoatCounter
  (ungated, index.html:2518)**, strip canonical/OG/JSON-LD/manifest-link/SW-registration, add
  noindex, retitle, swap favicon/theme-color, Barlow via Google Fonts (preview shortcut), and
  append a `<style id="districtry-skin">` override island (the blessed outside-the-fence
  pattern, ENGINE_SYNC.md) carrying the violet chrome + Barlow tokens. The masthead star SVG is
  **hidden, never removed** — `#star-path-header` is written by JS (index.html:2835). Known
  accepted gap: engine-fenced `METRO_NAME + " District Explorer"` strings still show the old
  name in dialogs — that is precisely the Phase-3 engine release. The script's substitution
  table doubles as the adoption checklist; refresh = re-run + commit.
- **Phase 3 — ROADMAP** (each step gated on explicit approval):
  1. Brand becomes worksheet data: add brand keys (product name, wordmark tag, palette tiers) to
     `metro-worksheet.json` + generator emission — no product-name key exists today.
  2. Engine release: parameterize the seven fenced `" District Explorer"` composition sites
     (index.html:3665, 3816, 3871, 3877, 4346, 4350, 4579); engine-v* + fan-out PRs to NYC/SF.
  3. Fork-local branding rows per `EXPANSION_GUIDE.md` §4.2 (head meta/OG/JSON-LD/theme-color/
     favicon, masthead mark/wordmark, `:root` palette values, analytics).
  4. `sources.html` hand-mirrored palette (lines 140–154) re-pointed.
  5. Assets + SW: replace root manifest/icons/og-image in place (SHELL_URLS-pinned filenames),
     bump `sw.cache_name` via the worksheet; head-snippet og:image made absolute.
  6. Tooling: `build_fonts.py` → self-hosted Barlow woff2s (no font CDN in production);
     `build_og_image.mjs` rebuilt from `OG Card.dc.html`.
  7. **Dark mode** — its own proposal and approval (greenfield engine work).
  8. **Domain migration, last and independent:** districtry.com — CNAME ×3 forks, Pages custom
     domains/DNS, `metros.json` URLs + `--sync-fleet` regen everywhere, GA hostname gate,
     GoatCounter site code, canonicals/og:url/JSON-LD, sitemap, search re-verification, redirect
     story for chidistricts.com, subdomain scheme (il./chicago.districtry.com — operator call
     for CHI-as-statewide).

## Known package flaws / adoption fix-list

- `pwa/head-snippet.html` uses a **relative** `og:image` — scrapers require an absolute URL;
  fix at adoption.
- `manifest.webmanifest` `start_url: ./index.html` assumes the manifest sits beside the app —
  correct at adoption, wrong anywhere else; the preview deliberately links no manifest.
- Mockup stats are hand-set snapshots and will drift (the 60→69 fix is already one instance);
  production surfaces must derive counts from the worksheet, never hardcode them.
- Dark-mode tokens exist in the tokens file; dark mode itself is out of scope until approved.
- The canvases need network to unpkg (React, SRI-pinned) — blank page offline/sandboxed; the
  landing page is framework-free so the microsite index always renders.

## Invariants for anyone touching this work

- Never place a file in root `data/app/` for the preview — `validate_index.py` fails the deploy
  on any JSON there that no sw.js cache list names.
- Never edit inside ENGINE or GENERATED fences for preview work; the Stage B skin is an appended
  override island.
- The preview stays out of `sitemap.xml` and is never linked from `index.html`/`sources.html`
  (linking from index.html would also drag its URLs into gate surfaces).
- Root filename collisions to avoid: `manifest.webmanifest`, `og-image.png`,
  `icons/icon-192/512.png` are SHELL_URLS-pinned — Districtry assets keep distinct names/paths
  until the adoption step swaps them in place.

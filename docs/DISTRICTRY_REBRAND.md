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
  word; instance tag suffix in Barlow Condensed 400 at 80%. **The tag is the TWO-LETTER
  code, lowercase — `districtry / il`** (operator-directed 2026-08-20, superseding the brand
  spec's spelled-out `/ illinois` example). Every future state uses its own code the same way;
  the canvas still shows the old form and owes this correction on the next sync.
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
- **Stage B — SHIPPED (2026-08-20):** the working re-skinned copy of the real app lives at
  `/districtry-app.html` (root-level sibling, so every relative fetch resolves identically —
  zero path rewrites), generated by `scripts/build_districtry_preview.py`, which applies an
  exactly-once-asserted substitution table to current `index.html`: strips GA (its hostname
  gate would pass on the preview URL!) **and GoatCounter (ungated)**, strips
  canonical/OG/JSON-LD/manifest-link/SW-registration, adds noindex, retitles, swaps
  favicon/theme-color, loads Barlow via Google Fonts (preview shortcut — adoption self-hosts
  via `build_fonts.py`), and appends a `<style id="districtry-skin">` override island (the
  blessed outside-the-fence pattern, ENGINE_SYNC.md) carrying the violet chrome + Barlow
  tokens; the point marker joins the data tier (`#1d5fd6`). The masthead star SVG is
  **hidden, never removed** — `#star-path-header` is written by JS. **The full Playwright
  smoke test passes with `BASE_URL` pointed at the preview file** — every behavior gate
  (boot, 39 layers, ground-truth classification, coverage hiding, permalink aliases, error
  isolation) green on the re-skin, which is the "every existing function is maintained" proof.
  Refresh after index.html moves: re-run the script and commit;
  `build_districtry_preview.py --check` detects staleness on demand (deliberately not in CI).
  **Open review items on the skin:** all three resolved 2026-08-20 — see "Skin review items"
  below. Still accepted as-is: engine-fenced `METRO_NAME + " District Explorer"` strings show
  the old name in dialogs, which is precisely the Phase-3 engine release.
  **Fix round (2026-08-20, post-deploy):** `.flag-stripe` — the Chicago flag's
  accent/white/accent bands above and below the map, that fork's signature device — rendered
  as meaningless violet bands under the token swap; the Districtry design carries no stripe,
  so the skin island now hides it.

## Footer elimination (operator-directed 2026-08-20 — IMPLEMENTED in the preview)

The redesign removes the document footer entirely: the map owns the left and bottom viewport
bounds (app-frame layout, desktop ≥901px; mobile keeps the stacked flow pending its own
design). Consequences, as built into `districtry-app.html` by the transform script:

- **FAQ → its own page**, `districtry-faq.html` (generated by the same script from the
  `.faq-section` markup verbatim, so the two can never drift within a generation; noindexed,
  tokens-styled, back-linked).
- **The footer's surviving content moves to a results-panel foot** (matching the canvas,
  which pins the disclaimer at the panel's bottom edge): the not-for-official-use
  disclaimer; the relocated `#footer-meta` (verified date — the boot script fills
  `#verified-date` by id, so the element MOVES, never duplicates); links to sources.html,
  the FAQ page, GitHub, sponsors, overberg.co; **the OSM geocoding attribution** (license
  requires it near the map — tile attribution stays on the Leaflet control); the relocated
  `#feedback-btn` (keeps the feedback-modal binding); and the relocated `metro-links-html`
  ENGINE fence (`#footer-metros` — sibling-metro links still inject at boot; fences pin
  content, not placement — the gaps-html masthead move is the precedent).
- The footer and in-page FAQ husks stay in the DOM `display: none` — nothing the boot
  script targets by id is ever deleted.
- Verified: full smoke test passes against the preview; every relocated id exists exactly
  once; map/panel fill viewport-minus-masthead exactly.
- **Adoption note (Phase 3):** on the real app this is fork-local markup/CSS except the two
  fence relocations (placement is fork-owned, so still no engine release) — but the FAQ
  page's head JSON-LD (FAQPage) and `sitemap.xml` entry become REQUIRED at adoption, since
  the production FAQ page must be indexable, unlike this preview.

## Canvas version history — CORRECTED (2026-08-20, second look)

An earlier revision of this section claimed the canvas had "iterated past the zip". It had
not: the Claude Design handoff bundle (uploaded 2026-08-20) is **byte-identical to the
original package** for every load-bearing file (App canvas, tokens, support.js, Industry
styles; same sync record 2026-08-19T20:52Z). There is exactly ONE canvas version. The
refinement rounds visible in the canvas chat (gradient border replacing the rejected dashed
line, dark-mode dot rings, merged card/toggle rebuild) are the history that PRODUCED the
2026-08-19 rebuild — they are IN the shipped `/districtry/` canvas, not after it. The
"5 pages" in the editor are the project's five .dc.html files, not new content.

## Canvas app-shell implementation (operator-directed "Implement Districtry App.dc.html", 2026-08-20 — SHIPPED in the preview)

The canvas's remaining unimplemented design landed in `/districtry-app.html` via the
transform script, same relocate-don't-delete discipline as the footer round:

1. **Three-zone coverage treatment** — the engine's single out-of-coverage wash is replaced
   AT ITS FORK-LOCAL CALL SITE (the scope-mask ENGINE fence is untouched;
   `coverageMaskRings` still gets set from `coverageOutlineRings`, preserving the engine's
   point-in-coverage test): gray outside Illinois, violet "Data coming — not yet sourced"
   wash on in-state unserved ground, soft violet glow + hairline on the state border
   (TIGERweb, fail-fast — an unreachable TIGERweb degrades to the old single-wash), and a
   map legend. Values are the canvas's own.
2. **Search relocates into the masthead** — the whole `.map-toolbar` moves verbatim (the
   geocoder binds `#geocode-form`/`#geocode-input`/… by id); `.search-extra` becomes an
   absolute dropdown under the header field.
3. **Header stat row** — "N counties · M layers · Sources", with N read from
   `docs/COUNTY_STATUS.md` and M from `metro-worksheet.json` at generation time, so a
   regeneration after a new county updates it.
4. **Panel header row** — `#point-chip` (coords + Share) relocates from the map's
   bottom-left to the top of the results panel; `position: relative` kept (it anchors the
   engine's share popover).

Not implemented, deliberately: the **Dark toggle** (dark mode remains deferred pending its
own approval) and the **live "N of 39 layers on" counter** (a live-state label needing a JS
hook into `state.layersOn`; the static stat row covers the header, the counter can join a
later round). Verified: full Playwright smoke test passes; every relocated id exists exactly
once; the coverage function schedules with an idle TIMEOUT so a busy main thread can't
starve it forever.

## Superseded delta list (kept for the record — all now resolved as above)

1. **Statewide coverage visualization** (operator-directed): soft light-violet gradient glow
   on the Illinois border — the dashed border was explicitly rejected — a light violet wash
   over in-state unserved counties labeled "Data coming — not yet sourced" (deliberately
   optimistic: *"the internal unserved counties are just areas that I haven't sourced the
   data for yet — I don't want to give the impression they won't be unlocked"*), gray
   "Outside Illinois" mask, and a map legend. The live app's scope-mask washes everything
   outside the 69-county ring identically; this design distinguishes three zones. Feasible
   (the app already has `metro-outline.json`, and TIGERweb serves the state boundary) but it
   is a map-semantics change, not a re-skin.
2. **Search moves into the header** (live app: floating overlay on the map — engine layout).
3. **Header stat row** ("N counties · 39 layers · Sources") + theme toggle placement.
4. **Results-panel header row**: coordinates + "N of 39 layers on" + Copy link at the top of
   the panel (live app: selected-point chip bottom-left on the map).
5. **Dark mode** iteration continues in the canvas (layer dots gained WCAG rings; operator
   noted the dark map is still hard to read) — remains the deferred functional addition.
6. **Regenerated package assets** (icons/OG/manifest/head-snippet) — refresh `/districtry/`
   from the canvas when the pin moves; when syncing, re-apply this repo's two fixes INTO the
   canvas (69 counties, live-outline fetch), which it still lacks.
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

## Usability round (operator review of the deployed preview, 2026-08-20)

Six findings from driving the live preview, all fixed in the transform script:

1. **Search field read as a grey box.** `.search-shell` carries a panel fill + drop shadow drawn
   to float over a basemap; in a header that reads as a grey slab. The shell is now transparent
   and the INPUT carries the affordance (white, hairline border, violet focus ring).
2. **Prompt text** is now "Search an Illinois address" — the app stopped being Chicago-only.
3. **Share popover opened off-screen.** It anchors `bottom: calc(100% + 10px)` — correct while
   the chip sat at the map's bottom-left, fatal once the chip became the panel's TOP row, where
   the card rendered above the viewport: open, invisible, unreachable. In the panel it opens
   downward, clamped to the panel width.
4. **Pills lost their emoji and became one segmented group** (hairline container, rules between
   items) rather than three separately-outlined pills. ADOPTION NOTE: the gaps label lives inside
   the `gaps-html` ENGINE fence — safe to edit in a copy that is never deploy-spliced, but in
   production that same edit is an engine release, or the label becomes a config string.
5. **The Layers button appeared to close the MAP.** `.results-col { display: flex }` (added with
   the panel foot) outranks the UA's `[hidden] { display: none }`, so setting the hidden
   attribute left the panel on screen while the grid collapsed to one column around it. Scoped
   to `:not([hidden])` — a reminder that `display` on a class silently defeats `hidden`.
6. **State names abbreviate to USPS codes** in geocoder results ("…, Springfield, IL, 62701")
   and in the map legend ("IL" / "Outside IL"). Unknown values pass through unchanged, so a
   geocoder answering with something unexpected prints what it said.

Self-inflicted regression caught in the same pass: the stat row was the segmented group's first
child, so `overflow: hidden` clipped its "Sources" link; stats and group are now siblings in one
right-aligned header cluster.

## Header/chrome round (operator review, 2026-08-20)

- **The stat row left the masthead for the results panel's header bar**: coords + Share on the
  left, `69 counties · 39 layers` flush to the page's right edge across from the Share button.
  The stats sit OUTSIDE the chip on purpose — the chip is hidden until a point is selected and
  the counts are true either way.
- **Both redundant "Sources" links removed** — the trailing link in the stat row and the one in
  the panel foot. The masthead pill is the single door; the OSM line that remains in the foot is
  a licence obligation, not a repeat.
- **The FAQ moved up into the pills** (`Common questions`), so all four "about the data" doors
  sit together instead of one hiding in the panel foot.
- **Instance tag is now the two-letter state code** (`districtry / il`) in the wordmark, the
  page title, and the FAQ page — see the rule under Decisions of record.

Regression caught by looking at the render rather than the diff: moving the chip into a new
panel-head wrapper broke `.results-col > .selected-point-chip`, which silently un-did BOTH the
chip's light restyle and the share-popover reposition (the popover would have gone back to
opening off-screen). Re-scoped to `.districtry-panel-head .selected-point-chip`. A child
combinator is a promise about depth, and moving markup breaks it quietly.

## Header nav treatment (design review, 2026-08-20)

The segmented bordered group was retired after an options review — seven treatments rendered
live in the real masthead and compared side by side (artifact
`ec042cef-798d-477d-ae86-da05b8a03469`). The complaint that started it was correct: a bordered
container put a second hard rectangle beside the search field and gave four secondary links a
toolbar's weight.

**Shipped: emphasis matched to stated priority.** `index.html`'s own comment records that the
gaps button was moved into the masthead *because it is the standing caveat on every answer this
app gives* — so flattening all four to equal weight contradicted the project's own doctrine.
The pill is now the shape of an action in this row: **"What data is missing?" wears one
permanently and inverts to a solid violet fill on hover/focus**; its three peers are bare text
that earn the same pill shape as a soft tint on approach. One family, two ranks.

Rejected, with reasons worth keeping: a tab rail (form would promise view-switching with an
active tab; these four open a modal, two pages and an external site); condensed uppercase (most
on-brand, but four shouted phrases for secondary links, and 130px wider than any alternative);
fully quiet text for all four (lightest, but under-signals the one item the project wants seen).

## Map legend rebuild (operator-directed, 2026-08-20)

The corner legend was a flat wrapping run of **loose** swatches and labels — nothing bound a
swatch to the label it defines — so at the 340px cap the wrap fell between the blue dot and
"Selected point", stranding a swatch from its own text. Seven treatments were rendered over the
live map and compared (artifact `58ce7ef8-c196-4ae2-86d9-ca854c426cfa`); the operator chose the
titled vertical list. Each row is now a grid whose swatch and label cannot be separated, so the
defect is gone **by construction** rather than by picking a lucky width; the row-gap is 2px, not
the shorthand 8px, because a why-line spaced as far from its own label as from the next row
belongs to neither. The legend also gained a `COVERAGE` kicker — nothing previously named what
the colours were a legend *of* — and a rule separating the three coverage zones from the point
marker, which are two different kinds of fact.

**The copy fix matters more than the layout.** "Data coming — not yet sourced" implied the violet
counties hold no data at all. They are not empty: measured empirically by selecting a point in
the Bureau County enclave, **the great majority of layers still answer there** — U.S. House, both
Illinois chambers, IL Supreme Court, county, municipality, ZIP, school districts and zones, and
the nearest-N station layers. What actually hides is that county's **own** local districts:
county board, board of review, judicial subcircuit, fire protection, park, library, precinct,
township and TIF. The swatch now reads **"Statewide layers only"** over a why-line — **"County
board and local districts not sourced yet"** — which is the honest distinction and the one a
reader in an unserved county actually needs. Deliberately **no count is printed**: which layers
answer varies by county, and a sandboxed measurement is no basis for a live figure.

**Adoption note (Phase 3):** this legend is created by the preview's own coverage script, so it
is preview-local today. If the three-zone treatment is adopted into production, the legend and
this copy travel with it, and the wording becomes a fork-owned string — worth a worksheet key so
NYC/SF can say "Statewide layers only" about their own states without an engine release.

## Skin review items — RESOLVED (2026-08-20)

The three items left open when Stage B shipped, each investigated before deciding. Two were the
same finding: **Chicago motifs that survived the re-skin because a token swap recolours a shape
without questioning it.**

1. **Warm accent — KEPT as a distinct hue, and the alternative disproven.** The open question was
   whether `--accent-warm` should simply become violet ("one hue for both slots"). It must not:
   the engine paints the **Public Safety group dot** with it (`.group-safety .dot`, index.html
   ~1612) beside Political (`--accent`), Schools (`#E8A324`) and Geography (`#5C8F6B`). Violet in
   both slots would render two of the four group dots identically — a categorical encoding
   collapsing, not a taste call. It is also `--focus-ring`, where contrast *against* violet
   controls is the point. `#b0316e` stays: it is the mark's own third polygon, so the hue is
   on-brand without borrowing from the data tier (the police/fire reds are map colours and stay
   map colours). Measured after the change: the four dots are four distinct hues.
   `--accent-warm-deep` is referenced **nowhere** in the engine today; the override is kept only
   so no Chicago flag red survives anywhere in the cascade.
2. **Empty state — the Chicago flag star retired.** A six-pointed star is that city's emblem;
   recoloured violet it was an off-brand city motif sitting in a Districtry app. It is now the 5c
   mark drawn as a quiet outline. The `#star-path-empty` element **stays in the DOM, hidden** —
   the boot script writes its `d` by id and would throw on a missing node (the same discipline as
   the masthead star).
3. **Selection marker — now the canvas's own answer.** The marker kept the star *shape* while
   only its fill moved to data blue, so a Chicago emblem was still marking "your point". The
   design canvas had already answered this: a circle with a white ring. It is now
   `<circle r="17" fill="#1d5fd6" stroke="#fff">`. One transform owns shape **and** colour; the
   earlier fill-only swap was deleted so two transforms cannot disagree about what the marker is.
   *(This is the BASE marker. The hierarchy that overrides it was settled separately — see*
   *"Marker hierarchy" below, which supersedes the badge bullet and the open question in this*
   *section.)*

**The marker is a hierarchy, and only its first branch was re-skinned.** `selectPointMarker()`
walks four cases: inside Chicago → the base marker (now the circle); on Lake Michigan → the Water
Taxi seal; inside an Illinois county → **that county's seal** where one ships (9 counties) or a
**county-name badge** otherwise; outside Illinois → the base marker. Two consequences were found
by reading that chain:

- **The county name badge hardcoded `#0B5394` — the Chicago flag deep blue — inside a JS string**,
  where no token swap could reach it. Exactly the same class of survival as the flag stripe and
  the star: a city colour outliving the re-skin because it was written as a literal, not a token.
  Moved to the data-tier `#1d5fd6` so it matches the circle the legend describes, and its
  system-font stack moved to Barlow. **SUPERSEDED the same day** — the badge is retired
  outright, so both of those transforms were deleted; see "Marker hierarchy" below.
- **Two relationship-legend swatches (`.rel-sw-in`, `.rel-sw-cross`) carried the same literal.**
  These are illustrative — the outlines the map actually draws take each layer's own colour,
  darkened — so as Chicago blue they demonstrated a hue this app never draws. Now the data-tier
  blue, sampling the tier they illustrate.

**The county seals themselves are KEPT, and the open question is the operator's.** *(Answered —*
*see "Marker hierarchy" below. The paragraph is kept for the reasoning that framed the question.)* They are each
county's own emblem, not Chicago branding, and for a state-then-national product showing the seal
of the county under your point is arguably an asset — they also carry researched licensing
(`icons/source/README.md`, `docs/COUNTY_SEALS_REVIEW.md`). But note the tension the new legend
makes visible: it says "● Selected point", which is true inside Chicago and outside Illinois,
while in the rest of Illinois the marker is a seal or a name pill. The design canvas's own answer
was a single circle everywhere. Retiring or keeping the seal/badge branch is a **product** call,
not a re-skin one, so it is flagged rather than taken.

Three `#0B5394` uses remain in the preview and are correctly out of scope: the `:root` definition
(overridden by the skin), a `var(--accent-deep, #0B5394)` fallback that never applies, and the
police-district / early-voting **map layer** colours — data tier, which the three-tier rule keeps.
The Districtry token set itself retains `#0b5394` as `--layer-zip`.

**Related finding, NOT changed:** the water-taxi marker (`icons/water-taxi.png`, swapped in when a
point lands on Lake Michigan) is a third Chicago motif — the Chicago Water Taxi seal. It is a
deliberate easter egg rather than chrome, so retiring or replacing it is a product call, not a
re-skin one. Flagged here rather than silently changed.

## Marker hierarchy — operator decision (2026-08-20)

The question flagged above came back answered in three parts: **retire the county-name badge in
favour of the default circle, restore the Chicago flag star for the city in its original colour,
and leave the seal counties alone.** The re-skin had been treating the four branches as one
question with one answer; the decision splits them by what each actually says.

The shipped hierarchy in `selectPointMarker()`, in the order the function walks it:

| Where the point lands | Marker | Why |
|---|---|---|
| Inside Chicago | **Six-pointed flag star, `#C8102E`** | The city's own emblem, for the city. What was wrong was using it as the default for all of Illinois — not using it at all. |
| Lake Michigan | Water Taxi seal | Unchanged; still the flagged easter egg (below). |
| An Illinois county **with** a shipped seal (9) | That county's seal | Unchanged. Each county's own emblem, licence-researched. |
| Anywhere else — an Illinois county with no seal, or outside Illinois | **Circle, `#1d5fd6`** | The canvas's own answer, and now the genuine default. |

Three consequences worth recording:

- **`makeCountyBadgeDivIcon` is now dead code in the preview** — the definition survives (it is
  engine text the transform script does not delete) but **zero call sites remain**. Both branches
  that reached it are gone: the seal branch sets an icon only `if (ok)`, and the no-seal branch is
  deleted entirely. The two transforms that had recoloured the badge went with it — a colour fix
  on a shape that can no longer render is drift waiting to happen.
- **The engine's early return had to be split.** `if (!live() || inCity) return;` conflated "the
  selection is stale" with "Chicago needs no override", which is precisely why the base icon was
  doing double duty as both *Chicago's marker* and *everywhere else's*. It is now
  `if (!live()) return;` followed by `if (inCity) { marker.setIcon(chiFlagStarDivIcon); return; }`,
  so the two facts are separate. `chiFlagStarDivIcon` is defined beside the base icon and reuses
  the engine's `starPath()`, already in scope.
- **The legend's "● Selected point" is now a simplification rather than a near-falsehood.** It is
  literally true for the great majority of Illinois — every county without a seal, which is 60 of
  the 69 served — and the two exceptions (Chicago's star, the nine seals) are self-evident on
  sight. Before this change the pill rendered across most of the state, so the legend disagreed
  with the map nearly everywhere it was read.

Verified in Chromium against the built preview: Chicago Loop → `STAR` fill `#C8102E`;
Bureau, Madison and Champaign (no seal) → `CIRCLE` fill `#1d5fd6`; a point in Indiana → `CIRCLE`.
The seal branch is **not reachable in this sandbox** — `chicagoCoverage` awaits
`loadCommunityAreas()` against Socrata, which is blocked here and never settles, so branches 2–4
never run locally. That is pre-existing and unrelated to the change (identical before it), so
correctness on the seal path was established by diffing the hierarchy instead: the seal call site
is byte-identical apart from losing its `: makeCountyBadgeDivIcon(name)` alternative.

## Dark mode (operator-approved 2026-08-20 — the one function this re-skin ADDS)

Dark mode was the single item held back when Stage B shipped: everything else in the
redesign already existed in the app and was *maintained*, while this was genuinely new and
so waited for its own approval. It now ships in the preview, and only in the preview —
`index.html` is untouched, as it has been for every round of this work.

**The palette was not invented here.** `districtry/tokens/districtry.tokens.css` has carried a
complete `[data-theme="dark"]` block since the package landed, and `Districtry App.dc.html`
already implemented the control, the persistence key, the basemap swap and the tile filter.
This change wires that decided design to the real app's token names; where the canvas and the
app disagreed, the canvas won on appearance and the app won on structure.

### What it does

| Surface | Light | Dark |
|---|---|---|
| Chrome tokens | paper `#f4f2ee` / panel `#fff` / ink `#17161c` | `#15131b` / `#201d29` / `#ece9f4` |
| Brand | `--accent #6d3fd1`, `--accent-deep #5730ab` | `#a78bfa`, **`#c4b0ff`** |
| Warm slot (Safety dot + focus ring) | `#b0316e` | `#e879b9` |
| Card data tier | `--card-accent #1d5fd6` | `#6ea8ff` |
| Basemap | CARTO `light_all` | CARTO `dark_all` + `brightness(1.35) saturate(.92)` |
| Selection marker | circle `#1d5fd6` | circle `#6ea8ff` (Chicago's flag star stays flag red) |
| Coverage wash | grey outside IL, violet "data coming" | near-black outside IL, lifted violet |

"Deep" means **more contrast against the ground, not darker** — on a dark ground that is
*lighter*. Inverting that one word is why dark-mode links so often come out unreadable.

### The decisions worth recording

- **Default is the OS preference; an explicit choice wins and persists.** The canvas hard-defaults
  to light; a reader whose machine already says "dark" should not have to say it again, so the
  fallback follows `prefers-color-scheme` and only a click writes `districtry-theme` to
  `localStorage`. While no choice is on record the page keeps following the OS live. One line to
  reverse if the operator prefers a hard light default for a design-review preview.
- **The toggle is a control, not a fifth door.** It sits at the end of the masthead pill row behind
  a hairline, and it is **text-only** — the standing instruction for that row is that its pills
  carry no icons, and a sun/moon glyph would walk that back. The label names what the button
  *does* ("Dark" while light), which is also the canvas's own semantics.
- **Set before first paint.** The theme attribute is written by a blocking inline script in the
  head, not by the app boot. Deferring one attribute is a flash of the wrong ground on every load.
- **The FAQ page shares the key.** It already linked the token sheet, so it needed only the same
  boot script and a toggle; a choice made on the map carries to it and back.

### What a token swap could not reach — again

The recurring defect of this whole project is a **colour written as a literal rather than a token**,
and dark mode is where every remaining one becomes visible at once. Four classes needed explicit
rules:

1. **The UA's own controls.** `color-scheme: dark` on the root. Without it the 39 layer checkboxes
   stayed bright white squares on the dark cards — the single most visible thing wrong with the
   first dark build, and invisible to any amount of CSS aimed at the app's own selectors.
2. **The mark's blend mode is an inline `style` attribute**, which no selector outranks, so the
   three polygons stayed `multiply` and vanished into the dark ground leaving a bare "d".
   `!important` is the correct tool for exactly this case, and is used only here.
3. **Leaflet's chrome and the engine's white surfaces** — popups, tooltips, the zoom bar, the
   attribution strip, the share popover, the hover card, every `#fff`/`#EEF4F7` hover. Leaflet's
   CSS is inlined in this app, so all of it is ordinary text in one stylesheet.
4. **The map's own data.** Forty-odd layer stroke colours are JS literals picked for a light
   basemap. Rather than fork the palette — which would break both the card-to-overlay tie and the
   categorical encoding — the overlay pane is lifted as a whole with
   `brightness(1.45) saturate(1.06)`, a hue-preserving colour matrix, so every layer keeps its
   identity *and* its relationships. It is deliberately **not** paused during pan the way the
   highlight drop-shadow is (`.map-panning`): a colour matrix is cheap where a per-frame
   drop-shadow rasterisation is not, and flipping it mid-pan would flash the whole map.
   **Known limit:** a lift cannot rescue near-black. `#14181C` and `#06375E` stay hard to see on a
   dark basemap. The honest fix is per-layer dark colours in the layer definitions, which is a
   data-tier change with its own review — not a re-skin. The one near-black that *is* handled is
   the pinned-parent outline, which inverts to near-white because it is chrome, not a layer.

### Two things fixed on the way past

Both found by auditing what a token swap cannot reach, both light-mode bugs that predate this
change:

- **`--faint` was referenced and never defined.** The map legend has used it for its "COVERAGE"
  kicker and the why-line since the legend shipped, so both silently fell back to inheriting
  `--slate` and rendered at full label weight. Defined now; the legend's intended hierarchy
  (kicker and why-line quieter than the labels they qualify) appears for the first time.
- **Three Chicago-flag literals were still in the hover states of violet buttons** — `#08406e` on
  the search and metro-portal buttons, `#094377` on the feedback primary, `rgba(11,83,148,…)` on
  the share-copy button — so each flashed Chicago navy on approach. Same class as the flag stripe
  and the star.

Fifteen `rgba()` tint literals at their *winning* call sites became tokens (`--dst-brand-tint`,
`--dst-ink-tint`, `--dst-shadow`, …) so the dark block has something to override. Light values are
the ones already in force, so light mode is unchanged by the refactor.

### How it was verified

Behaviour, in real Chromium: OS-light-no-choice → light; OS-dark-no-choice → dark with the
attribute already set before body paint; the toggle flips, persists, and survives reload against a
contrary OS setting; tiles swap to `dark_all`; `theme-color` follows; the choice carries between
the app and the FAQ page. No non-network console errors in either theme (the `ERR_CONNECTION_RESET`
lines are the sandbox's blocked live APIs, identical in both).

Appearance, by **pixel-diffing light mode against the shipped build**: on a clean load exactly two
regions differ — the masthead pill row (the new toggle, and the four pills shifting left to make
room) and the legend's kicker and why-line (the `--faint` fix). Nothing else in light mode moved,
which is what "maintain existing functionality" has to mean in practice. That diff also caught a
regression worth naming: the toggle was **1px taller** than its neighbours because a `<button>`
defaults to `line-height: normal` where the row's links inherit `12.5px`, and it pushed the whole
app down a pixel. Matched, so adding a control to that row now costs no layout at all.

**Not verified here:** the real CARTO basemaps. The sandbox cannot reach the tile CDN, so both
themes were driven against synthesised flat tiles at CARTO's own ground colours — good enough to
judge overlay readability, not a substitute for looking at the deployed page.

## Per-layer dark map colours (2026-08-20, second dark-mode round)

Dark mode shipped with a **stopgap on the map**: a `brightness(1.45) saturate(1.06)`
filter over the whole overlay pane, with a note that near-black layer colours would
survive it and that the honest fix was per-layer dark colours. This is that fix. The
filter is retired.

### The problem, measured

The layer palette is 59 colour literals chosen against a light basemap. Measured against
CARTO `dark_all`'s ground (`#1a1a1a`, which the app's own tile filter lifts to about
`#232323`):

- **28 of 37 stroke colours fall below 3:1**, the ratio WCAG 1.4.11 asks of a non-text
  boundary.
- **Four sit under 1.5:1** — `#14181C` (1.14), `#06375E` (1.28), `#7A0A1C` (1.41),
  `#7A0B1E` (1.42). That is not "dim", that is gone.
- On the *light* ground the same palette's worst case is 3.38:1. It was never a bad
  palette; it simply does not transfer.

A brightness multiply cannot fix the bottom of that list — `#14181C × 1.45` is still
near-black — which is exactly why the stopgap was labelled one.

### Why the obvious fix was rejected

The first attempt lifted each colour by the **minimum needed to clear 3:1**, preserving
hue. Every colour passed. The palette broke anyway:

- **314 of 703 pairs moved closer together**, and **66 landed inside dE 0.05** — close
  enough to read as the same colour.
- U.S. House District and County both became the same grey. City Ward and County Board
  District became the same blue. Post Office and Judicial Subcircuit the same violet.

The reason is worth writing down, because it is not obvious: **in the light palette a
great deal of the categorical separation IS lightness.** Navy vs mid-blue vs sky are one
hue family distinguished by how dark they are. Push them all to one contrast target and
the encoding collapses, hue preserved or not.

### What shipped instead

One **order-preserving affine remap** of OKLCH lightness across the whole palette, hue
untouched, chroma lifted ×1.25 to buy back the separation that compressing lightness
costs. Parameters `L 0.54–0.92, chroma ×1.25`, chosen by sweeping for the fewest
collisions subject to every stroke clearing 3:1.

Monotonic matters twice over: relative order between layers survives, and every
**within-layer** relationship survives by construction — a stroke darker than its fill
stays darker than its fill (measured: 0 flips).

**The bar is a measurement, not a taste call.** The dark palette is held against the light
palette's own record:

| | worst contrast | pairs inside dE 0.05 | p5 dE |
|---|---|---|---|
| light palette, light ground | 3.38 | 25 | 0.056 |
| light palette, **dark** ground | **1.14** | 25 | 0.056 |
| derived dark palette, dark ground | **3.10** | **24** | 0.052 |

It is *no more* collision-prone than the palette it derives from — marginally less — and
it fixes all 28 contrast failures. Derivation lives in `dark_map_palette()` in
`scripts/build_districtry_preview.py`; the 59-entry table is emitted into the preview so
it is inspectable and hand-adjustable.

### How it reaches the map without an engine edit

`baseStyleFor()` is the engine's single funnel for every path it paints, and
`moduleColor()` is the single source for the card accent, the sidebar dot and the hover
swatch. Both read `mod.overlay.style` directly. So the palette is installed as **getters on
the layer style objects** — `Object.defineProperty` with a getter that returns light or
dark, and a setter so any assignment degrades to plain data rather than throwing on a
read-only property. Every downstream read becomes theme-correct with no engine edit and no
second copy of the state to keep in sync. One install pass at the end of the script covers
all 43 polygon layers, the two nearest-N point layers' `mod.color`, and the School Location
type table.

The getter is on the **paint path**, so the theme is cached in a variable rather than read
off the DOM: `baseStyleFor()` reads two colours per path and a full repaint runs over every
path of every active layer. A `getAttribute` in there would put a document access inside
the loop this repo has already optimised twice (P7, P8).

Repainting on a flip goes through the engine's own `updateLayerHighlight()`, which already
handles all three cases (a matched region, no selection, a per-feature-styled layer) and
re-derives each from `baseStyleFor()`. `highlightApplied` is cleared first to force the full
sweep — the P7 fast path repaints only the two paths whose match role changed, and here
every path's colour moved.

### The highlight was pointing the wrong way

`highlightStyleFor()` builds the selected region's outline as
`darkenHexColor(moduleColor(mod), …)` — "the layer's own colour, shifted away from it so
the match pops". **Darken is right on light paper and exactly backwards on a dark map**,
where a darker outline recedes into the ground instead of standing out. This is the same
error as `--accent-deep`, one layer down.

`darkenHexColor` is a *fenced* engine function, but a function declaration's binding is
writable, so fork-local code rebinds it to shift toward white in dark mode — no fence edit.
Measured on the shipped build: U.S. House paints `#696F76` with its highlight at `#9EA1A6`
(3.10 → 6.06:1); IL Senate `#9B7CFD` with `#BEAAFE` (5.01 → 7.76:1). At adoption the honest
fix is for the engine to shift away from the *ground* rather than toward black.

### Verification

Driven in Chromium: flipping the theme repaints every stroke and all 37 card accents, with
**no colour surviving the flip** in either direction, and no page errors. Light mode was
pixel-diffed against the shipped build and differs in **one band of 687 pixels — the
generation stamp, because the source SHA changed.** Nothing else in light mode moved, which
is what the getter design is for: in light the getter returns the original literal.

Gates: `build_districtry_preview.py --check`, `validate_index.py`,
`generate_metro_files.py --check`, `check_engine_parity.py` and the full smoke test all
pass; `index.html`, `sw.js`, `sources.html` and `data/` untouched.

**Still not verified here:** the real CARTO tiles, for the same sandbox reason as before —
the `#232323` ground the whole derivation targets is CARTO's published dark_all land colour
with the app's own tile filter applied, not a sampled pixel.

**Left alone, deliberately:** the two nearest-N point layers paint `circleMarker`s from
colours captured in the factory closure, so their pins keep the light colours; their fills
(`#41B6E6`, and the fire red) are bright enough on dark that this reads as a non-problem
rather than a debt. The hover popup's `hoverDotIsInvisible()` fallback still assumes a
too-LIGHT dot is the failure case; in dark that assumption inverts, but the dot ring keeps
it legible.

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

# Development-process assessment — the fleet, the rebrand, and the single-repo decision

**What this is.** The decision record for reviewing how this fleet is developed and deployed —
single-file no-build apps, a byte-identical fenced engine distributed by hash-verified releases
and fan-out bump PRs, worksheet-generated regions, a generated template repo, one repo per
metro — measured against the districtry rebrand (`docs/DISTRICTRY_REBRAND.md`), with the
recommended alternative and its staged rollout. Every number below was **measured on
2026-08-24** and will drift; where a live count matters, read it from the tool named beside it,
never from this file (the repo's own standing rule).

**Decision of record (operator, 2026-08-24):** the fleet consolidates into **one repo and one
site** — `districtry.com`, a landing page listing states, each instance at a path (`/il`),
each state's data foldered under its instance. This supersedes the "metro instances ride
subdomains" positioning note in `docs/DISTRICTRY_REBRAND.md`. The staged rollout is R1–R6
below; each stage is individually gated on operator approval.

## Verdict

The current process is excellent at what it was built for — stopping engine drift between
forks — and now spends most of its energy on its own plumbing. The rebrand is the stress test
that exposes this: brand identity is scattered literals across 6 repos (98 files contain
`chidistricts`), 7 brand strings sit inside ENGINE fences and therefore owe a release onto a
channel whose consumers run 3 versions behind, and the redesign had to be built as a
2,433-line string-substitution shadow app (`scripts/build_districtry_preview.py`) because
`index.html` cannot be parameterized. The fix keeps the runtime philosophy — one hand-readable
file per instance, no framework, static hosting — and changes the authoring direction: source
becomes split fragments plus worksheet/brand data, `index.html` becomes composed, byte-gated
output, and the fork repos collapse into paths of one repo.

## Pros of the current manner

1. **Parity-by-construction works where it is mechanized.** The engine is byte-identical
   across all five app repos (55 fences: 53 in `index.html` + 2 in `sw.js`; 26 hash-verified
   immutable releases, v1.0.0–v1.0.25); `docs/ENGINE_SYNC.md` is md5-identical fleet-wide
   today. The founding incident was real and is cured: "same prompt ≠ same code" — the same
   prose prompt once produced two different metro-links footers.
2. **Zero-dependency runtime.** No framework churn, no supply chain, any static host works,
   offline-durable SW model, a hand-readable served page. It has survived 26 engine releases
   and growth to 89 counties without a rewrite.
3. **Exceptional verification culture.** Eight PR gates plus the retention, link, and
   freshness gates and a real-Chromium smoke test; every incident becomes a machine check
   ("machinery you have never seen fail is machinery you do not know works" — and all three
   mechanization drills were fired).
4. **Safety properties are enforced, not aspirational.** Officeholder data is never guessed;
   roster changes always land as human-reviewed PRs; external strings always sanitized.
5. **Per-fork facts live once.** `metro-worksheet.json` + 14 GENERATED regions; a state fork
   seeds in a day via the template; the Template repo is 100% bot-pushed behind a
   prove-before-push e2e battery.
6. **The process is self-documenting.** Costs are known, bounded, and recorded — an
   institutional memory most projects never have.

## Cons of the current manner

1. **The human merge-button bottleneck.** The pipeline is mechanized up to the merge and
   manual at it. NYC and SF sit **3 engine releases behind at HEAD** (`engine.lock.json`
   v1.0.22 against CHI's v1.0.25) as the steady state, and roughly **70% of each fork's
   recent history is fleet plumbing** (bumps, ports, de-Chicago-ifying), not metro work.
2. **Release ceremony with a recorded failure catalog.** Two manual workflow dispatches per
   release (tag creation cannot fire the release job — GitHub suppresses recursive triggers);
   a release/deploy race that cost manual re-runs twice (v1.0.17, v1.0.18); a new ENGINE
   block breaks the reference fork's own deploy by design ("not shippable in one PR", learned
   at v1.0.19); fences cannot be deleted (the tombstone convention plus a fleet-wide
   pre-clean, v1.0.13); v1.0.16→18 took three releases in one week for one feature with a
   byte-identical bundle all three times and both siblings' bump PRs failing twice; the
   sibling repo list lives in **four places** (SF missed the v1.0.6 fan-out over exactly
   this).
3. **The single file is simultaneously source and output.** 25,950 lines carrying three
   overlapping fence vocabularies (55 ENGINE + 14 GENERATED regions repo-wide + 36 TEMPLATE
   spans); every new line must be consciously classified in the PR that adds it
   (`build_state_template.py` is STRICT); the file cannot be read into a session and is
   navigated by grep anchor. Meanwhile the engine fraction has diluted from ~60% to **23%**
   of `index.html` — heavy machinery guarding a shrinking share.
4. **Sync-by-process residue keeps drifting.** `validate_index.py` exists in four distinct
   versions across the fleet (969/434/434/660 lines); `smoke_test.mjs` likewise in four; the
   Playwright install ladder is copy-pasted into four workflow files across three repos;
   `docs/ENGINE_SYNC.md` drifted 164 lines (its inventory said 50 blocks while the fences
   held 53) before anything enforced it — the doc about drift drifted.
5. **Load-bearing docs drift measurably today.** `CLAUDE.md` says `index.html` is ~21,000
   lines; it is 25,950. Three hand-kept artifacts became generated regions only *after* each
   one drifted (the ENGINE inventory, `docs/COUNTY_STATUS.md`, the verified date).
6. **The "no build step" rationale is asserted, not argued.** Its original justification —
   `file://` support — was explicitly retired on 2026-07-09 (`docs/OPTIMIZATION_PLAYBOOK.md`,
   owner decisions), and the project already *has* a build: deploy-time engine splicing
   (`scripts/apply_engine.py`), the worksheet generators, the template builder, the preview
   transform. What it lacks is a bundler or framework, which nothing here wants. The costs
   above are the price of not admitting the build exists.

## Why the rebrand is the stress test

- **Brand is scattered literals, not data.** 20 `"District Explorer"` occurrences in
  `index.html` (7 inside ENGINE fences — `permalink` ×2, `geolocation` ×2, `metro-portal` ×2,
  `geocoder-search` ×1), **25 more across the three SEO landing pages and `sources.html`
  that the Phase-3 roadmap does not mention** (and the landing pages sit outside
  `validate_card_links.py`'s authored surface), the SW cache name is literally
  `district-explorer-shell-v51`, plus the GA hostname gate, the GoatCounter endpoint, 13
  canonical/OG/JSON-LD URLs, `sitemap.xml`, `robots.txt`, three CNAMEs, `metros.json`, and 17
  references in the overberg site — `chidistricts` in 98 files across all six repos. The
  worksheet has **no brand key**, while the state template already parameterizes
  `{{BRAND_NAME}}`. Under the current process the rename is fleet-wide grep-and-hope — the
  exact class of work the process is worst at.
- **The seven fenced strings owe an engine release** onto a channel already three behind,
  with two more honest engine fixes queued behind it (highlight scaling; `darkenHexColor`
  shifting away from the ground). The rebrand roadmap's own line numbers for those seven
  sites are already stale — a small proof of the navigation problem.
- **The redesign is being done twice.** Because `index.html` cannot be parameterized, the
  preview is a shadow build: 43 exactly-once substitution tripwires over a
  constantly-changing file, a 966-line CSS override island, ~669 lines of injected JS,
  `Object.defineProperty` getters over live engine style objects, and a fenced engine
  function rebound at runtime — deliberately ungated ("the preview is allowed to go stale"),
  committed as a second 1.35 MB app copy in a repo whose own rules say build artifacts are
  never committed, with copy that has already forked from the app by design. At adoption,
  every one of those 43 substitutions must be redone as real changes; the script's own
  docstring calls its table "the adoption checklist."
- **The brand model stopped matching the repo model.** districtry is positioned
  fleet-by-state (`districtry / il`); the fleet is metro-first forks. WI — "the first state
  through the template route" — is un-bootstrapped (88 placeholder findings) and behind the
  #474 fingerprint fix, and the rebrand work itself recorded the fleet-knowledge failure: a
  commit asserting "THERE IS NO WISCONSIN FORK" an hour before the record corrected it, and
  the reference-fork fingerprint tripping on the fleet's own `wi.chidistricts.com`.

## The alternative: one repo, one site, composed instances

**Feasibility, verified before deciding:**

- *Path-relocatable today.* `index.html` contains zero root-relative URL references; every
  fetch and `SHELL_URLS` entry is `./`-relative; the SW registers relatively and resolves
  against `self.registration.scope`. An instance serves from `/il/` with essentially no path
  rewrites, and each instance's SW scopes to its own folder, so per-state offline caching
  works unchanged.
- *Size headroom is ample.* CHI's published tree is ~30 MB after the deploy excludes; NYC and
  SF add single-digit MB. Even at ~15 MB of app data per mature state, a 50-state site sits
  inside GitHub Pages' 1 GB soft cap, with "move heavy data out" as a distant escape hatch.
- *The composer already half-exists.* `build_state_template.py`'s `segment()` parses
  `index.html` into an ordered, fully-classified segment list in CI today (STRICT: every line
  already has exactly one bucket), and `build_engine_artifact.py` already runs a round-trip
  byte-fidelity gate. Splitting the file into ordered fragments and making concatenation the
  canonical direction is those two mechanisms pointed the other way, gated by `cmp` against
  the committed output.

**Target layout** (recommend renaming this repo to `districtry`, keeping history, issues,
secrets, and Actions configuration; GitHub redirects old repo URLs):

```
/index.html            landing page: the brand, the state list, coverage
/il/                   index.html (composed), sw.js, sources.html, data/app/, landing pages
/nyc/  /sf/            same shape (URL = instance tag; a future NY-state instance can be /ny)
/wi/                   bootstrapped from the template AS A FOLDER (the template repo retires)
engine/                engine source fragments — ONE copy; parity by there being one file
metros/<id>/           fragments, worksheet, scrapers per instance
scripts/               one validate_index, one smoke_test, one composer — the ×4 drift ends
.github/workflows/     roster scrapers consolidated to matrix/manifest-driven runners
```

**What this retires outright:** the engine release channel (tags, locks, fan-out dispatch,
bump PRs, the 3-behind steady state), `ENGINE_DISPATCH_TOKEN`, fences as editing constraints,
the Template repo and its push pipeline (a new state = a folder + bootstrap, not a repo), the
four sibling registries, the four-version script drift, cross-repo `fleet_status.py` checks
(reduced to a deployed-site checker), and `build_districtry_preview.py` plus the committed
preview (the skin becomes the real skin of the new tree). One domain, one sitemap, one
analytics property, one CI, one PR stream.

**What is preserved (the non-negotiables, unchanged):** one hand-readable composed HTML file
*per instance*; no framework, no bundler, ES5; static hosting; the SW offline model per
instance; the honesty rules; roster changes as human-reviewed PRs (now one review queue
instead of three); provenance and auditability (the compose→cmp byte gate replaces
hash-verified releases as the parity proof).

**Costs and calls, named honestly:**

1. **Redirects.** GitHub Pages cannot 301. `chidistricts.com` → `districtry.com/il` needs
   meta-refresh + `rel=canonical` shells in the old repos (the standard Pages pattern), or a
   CDN in front of the old domains for true 301s. SEO transfer via meta-refresh is slower;
   plan search re-verification either way.
2. **Metro paths.** `/nyc` and `/sf` now — the path is the instance tag. If a NY-state
   instance ever exists it takes `/ny` and links or absorbs `/nyc`.
3. **Scraper-workflow consolidation becomes urgent.** 63 per-county workflows for one state
   cannot be copied per state; fold them into a few matrix-driven runners over a manifest,
   staggered. Part of the reorg, and a win on its own.
4. **Single-site blast radius.** One bad merge touches every instance. Mitigations: Pages
   deploys are atomic; path-filtered CI (changed instances smoke on PRs, full battery on
   main); the reorg runs on a branch while chidistricts.com serves untouched until cutover.
5. **Old repos.** NYC/SF import with history (git subtree) or archive read-only; the Template
   repo retires; WI's repo retires in favour of `/wi`; overberg updates its links and embed
   at cutover.

## Staged rollout (each stage gated on operator approval)

| Stage | Work | Gate |
|---|---|---|
| **R1 — Brand-as-data** | Opt-in `brand` key in `metro-worksheet.json` + schema (product name, instance tag, app name, OG block, palette tiers, theme color, favicon, analytics incl. the GA hostname gate and GoatCounter URL); opt-in GENERATED regions for head-brand, head-analytics, and the `sources.html` palette; `explorer_name` in `metros.json` | `generate_metro_files.py --check`; running the new generator over NYC/SF checkouts produces **zero diff** (opt-in means inert — the recorded v1.0.16 lesson); `build_state_template.py --check` |
| **R2 — In-place reorg to `/il`** | Retire the template and engine-release channels (R2.1); move the app to `il/` behind a redirect stub (R2.3); chidistricts.com keeps working throughout. **The composer moved to R3 by operator decision** — see the note below | the full existing gate battery + smoke against `/il/`, plus a Chromium check of the redirect and SW transition |
| **R3 — Composer, then import SF and NYC** | The composer inversion opens R3 (deferred from R2, below). Then each fork as `metros/<id>/` + `/sf/`, `/nyc/`; their divergent validate/smoke copies (585–891 lines each) reconcile into the one script set — real porting work, budgeted as such; scraper workflows move and consolidate to matrix runners; old repos freeze behind a no-new-merges window | per-instance smoke; a no-op proof (the composed instance byte-equals the fork's deployed HEAD minus intended deletions); the retention gate re-baselined |
| **R4 — Landing page + districtry skin** | `/` becomes the state-list landing (brand package, coverage); instances take the skin from worksheet brand keys; the preview machinery retires; a new state bootstraps as its own folder when ready | smoke + validate + link gates + a leftover-brand grep |
| **R5 — Domain cutover** | CNAME → districtry.com, DNS, one sitemap, analytics keys, redirect shells in the old repos/domains, search re-verification | `validate_card_links.py` + live probes + redirect checks |
| **R6 — Retire machinery** | Engine releases/locks/fan-out, the Template repo, cross-repo fleet_status, per-fork doc copies; archive NYC/SF/Template/WI with pointer READMEs | grep for dead references; docs regenerated |

Rebrand timing simplifies under this ordering: **chidistricts.com is never rebranded in
place** — districtry ships as the identity of the new tree, and the old domains redirect at
R5. (Re-confirmed by the operator on 2026-08-24, after acquiring districtry.com: the domain
cutover stays last and independent. The cost is two canonical moves for the Illinois app —
root→`/il/` now, host→districtry.com at R5 — and that is accepted, because each is small and
separately verifiable where a combined move would land DNS, a Pages custom domain, redirect
shells on the old domains and search re-verification all before the fleet is consolidated.)

### The SEO surface, now carried by the whole fleet (2026-08-24)

Search Console drove a copy change in the Illinois app that is now carried fleet-wide, and
finishing it exposed a gap in the one page nobody had audited.

**What it is.** `/il/` shipped it first (DistrictExplorer-CHI#401): a **question-led title** —
the query phrasing searchers actually type, with the brand as the *trailing, swappable* half —
a description naming "address or ZIP", the FAQ on its own page, and three per-cluster landing
pages. `/ny/` and `/ca/` now carry the same title composition, the same ZIP-aware description,
and a lead **"What district am I in?"** FAQ entry naming that city's own districts. `/ca/` had
the `.faq-section` styles and no FAQ section at all — a doubled `flag-stripe` sat where one
belonged — so it gains a seven-entry section and its first `FAQPage` JSON-LD, keyed to its
post-cutover `districtry.com/ca/#website`. Its counts (11 supervisor districts, 10 police
districts, 41 neighborhoods) are read off its own shipped `data/app`, not recalled.

**Why the sibling titles still say "… District Explorer".** The cutover moved the domain, not
the wordmark: `ny/` and `ca/` still carry their own product names, so the SEO change kept them
rather than half-rebranding a live page. The composition is built so that swap is a suffix
edit and nothing more — when the wordmark lands, only the trailing half changes, and the
question phrasing that earns the ranking is untouched.

**The root landing page was the gap nobody had looked at.** It shipped with a brand-led title,
no structured data, no social image and no `robots` — the one page naming the whole fleet was
the one page search engines were told least about — while the 1200x630 brand card built for it
(`districtry/og-districtry.png`) sat in the tree unreferenced, so every share of districtry.com
rendered as a bare text card. It is GENERATED, so the fix lives in
`scripts/build_landing_page.py`: question-led title, ZIP-aware description, `og:image` /
`twitter:image` pointing at a promoted `/og-image.png`, `summary_large_image`, explicit robots,
and a `WebSite` + `Organization` + `ItemList` graph built **from the same `metros.json` list the
page renders**, so the graph cannot drift from the instances it names.

**Landing pages now exist for all three instances.** `/il/` had three; `/ny/` gained
`council-district.html` and `community-board.html`, `/ca/` gained `supervisor-district.html`
— chosen by query evidence rather than symmetry (the export shows NYC council-district and
community-board phrasings and SF supervisor-district ones; nothing justified a fourth). Each
carries its own instance's palette, fonts, favicon and analytics — **CA has no Google tag**, so
its page takes CA's cookieless counter rather than inheriting one that would report to the
wrong property — and deep-links with that app's real layer id (`council`, `community-district`,
`supervisor-district`), checked against the registry: the first draft guessed `supervisor` and
would have opened the map with no layer on. All three are in `sitemap.xml`.

**What the fleet still owes this surface:**

1. **Per-URL redirects from the old hosts — DONE for the four that were broken, with a
   caveat.** The operator's 2026-08-24 GSC export (archived at
   `docs/search-baseline/2026-08-24-chidistricts-gsc.md`) names exactly seven indexed URLs.
   Squarespace forwards the old hosts **with the path intact**, so the root and both
   subdomains were already fine; the four Illinois pages 404'd because their paths moved
   under `/il/` in R2.3 and nothing held the old ones — 126 impressions landing on nothing.
   Root-level redirect shells now catch them. **They are meta-refresh + canonical, not 301s**,
   because GitHub Pages cannot issue a 301; that is the strongest substitute available at this
   origin. Put a CDN/proxy in front and they can be deleted in favour of real 301s. Two
   remaining nits, both operator-side at Squarespace: the forwards target
   **`http://www.districtry.com`**, so every redirected visitor takes two extra hops
   (http→https, www→apex) — point them at `https://districtry.com` instead.
2. **Re-request indexing** for the moved URLs and the new pages, and keep the question-led
   composition when titles become worksheet-emitted. The `districtry.com` property is new and
   starts empty: run **Change of Address** from the old property, and keep the old one
   verified — a GSC property cannot be renamed and its history never moves, which is why the
   baseline above is committed rather than left in the console.
3. **A link gate for the new pages.** `validate_card_links.py` extracts its surface from
   authored HTML; confirm it reaches `ny/` and `ca/` now that they carry authored pages.

### The composer, deferred to R3 (operator decision, 2026-08-24)

The composer inversion was scoped into R2 and moved to the head of R3. **R2.1 is what changed
the calculus**: the composer's headline benefit was that fence edits would stop being
overwritten, and retiring the deploy-time splice delivered exactly that on its own — a fence
edit already reaches production today. What remains is per-instance code organization, which
pays off when there is more than one instance to organize; building it at the head of R3 means
one composer serves three instances instead of one, and gives NYC and SF a defined place to
land rather than a place retrofitted after they arrive. Against that, the standing cost is a
dual representation — every line of a 26,000-line file committed twice, once as fragments and
once as composed output — which is worth paying once, for three instances, rather than now,
for one.

**Consequence worth protecting:** the 33 `TEMPLATE:BEGIN` spans in `il/index.html` (plus those
in `il/sw.js`, `il/sources.html` and several scripts) are now inert — the builder that read
them was deleted in R2.1 — but they are **not** dead weight to be swept up. They are a
hand-authored, semantically meaningful segmentation of the app file, which is precisely the
fragment-boundary information the composer needs. Leave them where they are; R3 reclaims them.

## Stage log

- **R5 (part 2) — SHIPPED (2026-08-24): one privacy page for the whole site, generated by
  MEASURING the apps.** The privacy page shipped at `il/privacy.html` on a site that serves
  three apps. NYC and SF had none at all, and the front door linked Illinois's — so a reader on
  `/ny/` was either told nothing about how the page they were on behaves, or told about a
  different one. It now lives at `/privacy.html`, and all three apps plus their five sub-pages
  link it.
  **It is generated from the apps themselves, not from the worksheets, and that distinction was
  forced by the data.** `ny/` and `ca/` carry EMPTY `brand.analytics` blocks while their shipped
  HTML runs GoatCounter — and NYC's runs Google Analytics as well, into Chicago's own property.
  A generator trusting the worksheet would have published that two of the three apps have no
  analytics, which is the worst class of error a privacy page can make. So every per-app fact is
  a regex over the file a reader is actually served.
  **The measurement immediately proved the old page could not simply be copied.** It claimed
  "some large statewide layers ask the server about your exact selected point" — five call sites
  in Illinois, ZERO in the other two. Copying it across would have published a false confession
  twice; deleting the sentence would have hidden a true one once. The page now states it per
  app, in a table whose every cell is measured: analytics, browser-storage keys, address-search
  provider, and whether any layer sends a point to a server. **SF runs no Google Analytics at
  all and Illinois is the only app that stores a theme** — differences a single flattened
  paragraph would have had to lie about in one direction or the other.
  **Two classes of claim, treated differently by the build.** Sentences asserted FLEET-WIDE — the
  analytics event vocabulary and the two-decimal coordinate rounding, both engine code — are
  GATED as identical across the three apps; if one ever diverges the build FAILS rather than
  publishing a sentence true of two apps out of three. Everything that genuinely differs gets a
  row. The rounding gate is the load-bearing one: the rounding IS the privacy claim, and
  widening it silently is exactly what a generated page must make impossible.
  **The relative link is its own hazard, and has its own gate.** Moving the page to the root
  turned every in-app link into a `../` hop, and `validate_card_links.py` probes ABSOLUTE urls —
  a relative href is not its subject at all, so a wrong number of dots would have been a 404 no
  gate could see. `landing_test.mjs` — now the gate for the root's generated pages rather than
  the landing page alone — asserts that every app in `metros.json` links the page and that the
  link resolves, that the table carries a row per app, that both themes paint their own ground,
  and that a dark choice made in an app survives the hop. The deploy additionally refuses to
  publish a tree with no root `privacy.html`, because that one missing file is a 404 on all
  three apps at once.

- **R3 (part 3) — SHIPPED (2026-08-24): the imported automation moved to the root, and the
  check that found it was itself half-blind.** Numbered R3 because it finishes R3 part 1's
  marked trap; it ships after R4 because that is when the check that could see it existed.
  R3 part 1 imported `ny/` and `ca/` with their `.github/workflows/` attached and wrote a
  README in each saying the files were inert and were kept as the definition of the refreshes
  that would one day move. **They stayed inert for as long as nothing measured them**, and the
  README's stated reason for leaving them — that the refreshes still ran in the fork
  repositories, which were still live — stopped being true at R5, when both domains were
  forwarded here. From then until now, NYC's and SF's officeholder data had no refresh
  mechanism anywhere that serves a reader.
  **Ten workflows were inert, not six.** The inert check shipped with `fleet_status` reads each
  worksheet's workflow inventory and asks whether the file exists in the root
  `.github/workflows/`. A workflow file carries nothing that says which instance it serves, so
  a name is all that check can ask — and `update-congress-roster.yml` and `validate-sources.yml`
  were inventoried by all three instances. Chicago's copies sat at the root, so NYC's and SF's
  four claims on those names resolved to a file that exists, and four frozen refreshes were
  reported healthy by the very check written to find frozen refreshes. **A shared basename is a
  failure of the inventory, not a detail**: at the root only one file can hold a name, so at
  most one instance claiming it can be right. `fleet_status` now says so before it runs the
  inert check, and the guard was verified by putting the pre-rename inventory back and watching
  it name both collisions.
  **What moved.** Ten workflows, rewritten with instance-aware paths — `<tag>/scripts/…`,
  `<tag>/data/app/…`, `validate_index.py <tag>/index.html`, and a `bot/<tag>-…` PR branch that
  cannot clash with another instance's — and renamed with a `<tag>-` prefix, which is what makes
  the inventory unambiguous rather than merely tidy. Each instance's `validate-sources` also
  takes an instance-scoped tracking-issue title; three workflows sharing one title would have
  had them overwriting each other's issue body every month. Chicago's title is deliberately
  untouched: it has an open issue that a rename would orphan.
  **What was deleted rather than moved**, because the monorepo's own root workflows already do
  the job for every instance: each fork's `deploy-pages.yml` (the root job publishes the whole
  tree), `smoke-test.yml` (the root job runs all three `validate_index` and all three
  `smoke_test.mjs`), and `engine-bump.yml` (it consumed a `repository_dispatch` from a release
  channel retired at R2.1).
  **The second half-blind gate, found by fixing the first.** `validate_workflow_deps.py` — the
  gate that exists because five roster refreshes once shipped dead on arrival — matched only
  `python3 scripts/X.py`. Relocating these ten made them invoke `python3 ny/scripts/X.py`, which
  that pattern does not match, so the ten newest subjects of the fleet's dependency gate would
  have been silently skipped while it printed OK. It now derives the instance prefixes from
  `generate_metro_files.INSTANCES` and resolves each entry point's import closure against **its
  own** `scripts/` directory, so a sibling import inside `ny/scripts/` cannot be walked into
  Chicago's tree, where several of the same module names exist. Coverage went from 253 entry
  points to 277; the failure path was verified by pointing a relocated workflow at a
  non-existent script and watching it fail.
  **Still open, and operator-side:** the fork repositories' own copies of these schedules. They
  are outside this repo, they now refresh a tree nothing serves, and turning them off is a
  Settings action rather than a commit.

- **R4 (part 1) — SHIPPED (2026-08-24): the root becomes the fleet's front door.**
  "One repo, one site" only pays off if the site has a door. R2.3 left the root a redirect stub;
  it is now the districtry landing page — the mark, the wordmark, and the places the fleet
  answers for — with the drift gate, the link gate and a browser gate all pointed at it.
  **It is GENERATED, and that is the whole argument rather than a convenience.** This record's
  central finding was that brand identity had decayed into scattered literals; a hand-written
  front door whose state list is HTML would have reproduced that on day one of the fix. Every
  fact comes from a file that already owns it — `metros.json` for the places, the districtry
  token file for the palette (light AND dark, extracted BY NAME so a rename fails the build
  instead of emitting a broken custom property), `favicon.svg` inlined as a data URI, and the
  self-hosted Barlow CSS. Adding a state is a manifest entry and a regenerate; restyling is a
  token edit and a regenerate. `metros.json` gained three landing fields (`tag`, `landing_name`,
  `blurb`) and gained them safely, because `sync_fleet` projects a whitelist — they cannot reach
  an app's worksheet. `landing_name` exists because the two names genuinely differ: the Illinois
  instance is listed as **Illinois** since it serves 89 counties, while its metro `label` stays
  **Chicago** for the app's own sibling-metro portal.
  **THE FORWARDING GUARD IS THE PART THAT MATTERED, and it nearly got missed.** Before R2.3 the
  app served from this origin's root, so every share link and embed snippet it ever handed out
  was built from the root URL — `/?utm_source=share&utm_medium=link#point=…` and the `iframe`
  equivalent — and those sit in other people's pages and bookmarks where they cannot be recalled.
  Replacing the redirect stub with a landing page would have answered every one of them with a
  page about Illinois instead of the map they asked for. So the root still forwards any URL
  carrying app parameters, query and hash intact, and renders the landing page only for a bare
  visit. That guard is invisible to a diff and would survive its own drift check while broken,
  which is why `scripts/landing_test.mjs` asserts it in a real browser BOTH ways — an app link
  forwards, a plain visit and an unrelated campaign query do not — and runs in CI beside the
  three instance smoke tests.
  **THAT TEST'S FIRST DRAFT PASSED LOCALLY FOR THE WORST POSSIBLE REASON, AND CI CAUGHT IT.**
  It compared the post-forward URL byte-for-byte against what was sent, which is not a test of
  the guard at all: once `/il/` is reached the APP boots and calls `syncUrlHash()`, rewriting the
  hash into its own canonical form — 5-decimal coordinates, an appended `&zoom=`. The comparison
  held locally only because this sandbox cannot reach the Leaflet CDN, so the app never booted
  and never rewrote anything. CI reached the CDN, the app booted, and two checks failed **on a
  guard that was working perfectly.** The sandbox's known and documented limitation had turned
  into a silent source of false confidence — the same shape as the three path bugs above, a check
  that is green because something upstream of it never ran. The fix is to STUB `/il/` so neither
  the app nor the network is in the measurement, and **the stub is itself asserted** (the page
  title must be the stub's) rather than assumed, because a route pattern that quietly stopped
  matching would put the app right back in. Proven against both realistic regressions: a guard
  that drops the hash fails three checks, one that stops recognising permalinks fails two.
  **A third instance of the R2.3 path class turned up on the way.** `build_fonts.py` still aimed
  at a repo-root `fonts/` that nothing read, having been correct only while the Illinois app WAS
  the root; running it would have left `il/fonts/` untouched. Nothing caught it because it is an
  occasional operator step, not CI — the same shape as `vendor_leaflet.sh` reading the redirect
  stub. It is target-aware now (`il` → `il/fonts/`, `landing` → `fonts/`), which is also how the
  landing page got its four self-hosted Barlow faces — trimmed to exactly the weights the page
  sets, because a weight it never uses is dead bytes in the published tree.
  The link gate gained the page for the reason `sources.html` once did: every link on it is a
  link a reader clicks, and it is now the most prominent authored surface on the site. The
  sitemap gained the root, which had been deliberately absent while it was a `noindex` stub.
  Verified: 15 browser checks green — the page renders, all three places list with their tags,
  Barlow actually loads (not a silent system-ui fallback), permalinks forward with their hash,
  embed URLs forward with query AND hash, a share link forwards, an unrelated `utm_source`
  does NOT, and the page boots with no console errors; light, dark and 390px reviewed by
  screenshot; both drift-gate negatives fire (a hand-edited page, and a new metro missing its
  landing fields); all three sibling destinations probed live at 200; the assemble step
  re-simulated so `fonts/` publishes and the generated font CSS does not.
  **Deliberately absent, and worth stating so a later pass does not read it as an oversight:**
  no analytics (the stub carried none, the brand block's analytics keys are per-instance, and
  adding a tracker to a new surface is not a build-step decision), and no coverage map (it would
  need Leaflet plus one instance's boundary data, and a fleet page loading Illinois geometry
  tells a lie about the other two).
- **R4 (part 2) — SHIPPED (2026-08-24): the app wears the skin, dark mode ships, and the
  redesign stops being built twice.** `build_districtry_preview.py` (2,440 lines) and
  `districtry-app.html` (27,331 lines) are DELETED. This record's sharpest complaint was that the
  redesign was being done twice because `index.html` could not be parameterised; it is done once
  now, and the second copy is gone.
  **The adoption was measured before it was attempted.** Diffing the app against the preview put
  36 of 39 hunks OUTSIDE every ENGINE fence, which is what made the skin metro-local: SF and NYC
  compose the same engine and are untouched, and both smoke tests pass unchanged. Of the three
  fence-touching hunks, two were brand literals that had no business being in an engine block at
  all, and became data.
  **THE SEVEN FENCED STRINGS UNLOCKED, and that is the assessment's own prediction closing.**
  They composed the product name inline as `METRO_NAME + " District Explorer"`. A new
  `brand-names` engine block reads `METRO_BRAND` instead, typeof-guarded — which is not defensive
  habit but the mechanism: SF and NYC carry no brand block, so every one of the seven resolves to
  exactly the bytes it did before. R1 shipped `METRO_BRAND` unconsumed and the schema said
  "Optional until a rebrand consumes it." Proven per instance through the UI, since the embed
  snippet's `title=` attribute IS the resolved name: il "districtry Illinois", sf "San Francisco
  District Explorer", nyc "New York City District Explorer".
  **What the preview got wrong for production, and only adoption could find.** Its CSS hides the
  document footer — where three elements the boot script binds BY ID live — so taking the CSS
  without the relocation transform would have retired the verified date, the feedback button and
  the fleet links in one rule, silently, with every gate green. And it hides the in-page FAQ in
  favour of a page that never shipped and referenced assets that do not resolve from `il/`; that
  hide is not adopted, because the in-page FAQ is what is live and indexed today.
  **Dark mode is the one function the redesign ADDS**, and its map palette is DERIVED — an
  order-preserving OKLCH remap, not a contrast lift, which was measured and rejected because it
  collapses the categorical encoding. The preview inlined the computed result; that would have
  been right on the day and wrong the day a layer colour changes, so it ships as
  `build_dark_map_palette.py` over a GENERATED region with a `--check`. **Its smoke gate earned
  itself immediately**: the assertion that a live overlay repaints from the derived palette FAILED
  on first run (`#2E8C6A -> #2E8C6A`) because the theme-aware colour getters sit in a different
  hunk than the controller. Without it the app ships looking dark with every district boundary
  still light. It now reads `#2E8C6A -> #62DAAC`.
  Verified: full static battery, all three instances' `validate_index`, all four browser surfaces,
  the marker hierarchy in both directions (Chicago draws its star, Kankakee draws the circle), the
  fleet switch filling from `METRO_EXPLORERS`, and the relocated footer elements still binding.
  **Deferred, not abandoned:** the FAQ's own page, and SF/NYC adopting the skin — which is R5's
  business, since they are not published until their domains move.

- **R3 (part 2) — SHIPPED (2026-08-24): the tooling reconciliation, and the two defects it
  exposed.** Part 1 unified the engine; this unifies what runs *around* it. `generate_metro_files.py`
  became instance-aware (one script, 33 generated regions across three worksheets, replacing three
  copies), the five dead engine-channel scripts left in `sf/scripts` and `nyc/scripts` are deleted,
  and the smoke workflow now gates **every instance** instead of `il` alone.
  **An ungated folder is worse than an ungated repo.** While SF and NYC were separate repos they
  had their own CI; as folders they merge through this repo's workflow, and until this change
  nothing in it looked at them. Turning that gate on immediately found what it was for: both
  imported smoke tests read `data/app/coverage-gaps.json` and `metro-worksheet.json` **relative to
  the process CWD** — correct when you ran them from their own repo root, `ENOENT` here. All three
  now anchor their disk reads to the script file, so a smoke test runs from any directory. The
  negative case is exercised too: one broken instance turns the whole step red, and the two
  healthy ones still report.
  **The second defect is the one worth remembering, because a guard went quiet about its own
  configuration.** `vendor_leaflet.sh` — which exists so the sandboxed browser can boot at all —
  read the repo-root `index.html`, which R2.3 turned into a redirect stub. It found no Leaflet
  URL, printed a soft note, and `exit 0`. The smoke test then died 45 seconds later at
  `page.waitForFunction: Timeout`, which is precisely the symptom CLAUDE.md tells you **not** to
  chase into app code — so the misleading diagnosis was pre-installed. Two changes: it fails hard
  (exit 1, naming the instance) when an app file is missing or carries no Leaflet URL, while an
  unreachable CDN stays best-effort as designed; and the three byte-identical per-fork copies
  collapse into one instance-aware script. Those copies were **genuinely** non-redundant while the
  instances were separate repos — each self-located into its own tree — and became pure
  duplication the moment one root, one SessionStart hook, and one script that knows the instance
  table could do the job. `sf/.claude/settings.json` goes with them: a Chicago-domain copy that
  fired for nobody and pointed at a script that no longer exists.
  **What deliberately did NOT get unified.** Each instance keeps its own `validate_index.py`,
  `smoke_test.mjs` and `validate_sources.py`. They differ by 595–1,473 lines because they
  *describe different cities* — that is legitimate difference, not drift, and merging them would
  trade a real distinction for a false economy. The rule the whole stage runs on: unify what is
  the same, gate what is different.
  Verified: all three smoke tests pass at `/il/`, `/sf/` and `/nyc/` from an unrelated working
  directory; all three `validate_index.py` pass from the repo root; `generate_metro_files.py
  --check` (33 regions / 3 instances), `compose_app.py --check` (6 files / 3 instances),
  `check_engine_parity.py`, `build_coverage_gaps.py --check`, `build_county_status.py --check`,
  `validate_workflow_deps.py` all green; the composite CI step simulated locally in both
  directions.
  **Known debt, not fixed here:** each fork's gaps panel still links source submissions to its
  own `DistrictExplorer-SF`/`-NYC` issue tracker (`repo_issues` in its worksheet). Correct today,
  wrong the moment R6 archives those repos — retarget it there, with the domain cutover.

- **THE DEPLOY BROKE ON THE R3 PART-1 MERGE AND EVERY GATE STAYED GREEN (2026-08-24).** Fixed in
  the same change as part 2. The site simply stopped publishing after #481: three consecutive
  green PR runs, a merge, and then a red `assemble` job nobody was looking at. Worth recording in
  full, because the cause, the blind spot and the fix are three different lessons.
  **The cause is six lines of comment.** Part 1 added an explanation of why `sf/` and `nyc/` are
  excluded from the published tree — written *between* two backslash-continued lines of the
  deploy's `rsync` invocation. Bash joins a continuation **before** it looks for comments, so the
  comment does not annotate the command, it **terminates** it: `rsync` ran with its excludes and
  no source or destination, exited 1 on a usage error, and every line after the comment was
  parsed as a separate command (`--exclude=sf: command not found`). The construct is invisible on
  review — it reads exactly like a well-commented command, YAML parses it, and nothing lints a
  `run:` body.
  **The blind spot is structural and is the more useful half.** `assemble` runs on `push` to main
  and `workflow_dispatch` only, so the one step that turns a commit into a website is the one
  step this repo's PR gates never execute. Everything a PR checks — layers, rosters, engine
  parity, generated regions, the real-Chromium behaviour test — checks the *committed tree*, and
  the committed tree was perfect. **A gate that runs only after the merge is not a gate on the
  merge.**
  **Three guards now, where there were none.** `scripts/validate_shell_continuations.py` fails on
  a comment inside any backslash continuation in any `.yml`/`.yaml`/`.sh` — the rule needs no
  shell parser because the construct is *always* wrong — and it is wired into `smoke-test.yml`,
  so it reaches the PR. The excludes moved into an `EXCLUDES` array, where an explanation has
  somewhere safe to live. And the assemble step now asserts its own output: no `il/index.html`,
  no root redirect stub, or an unpublished instance leaking into `_site/` each fail with a named
  `::error::` instead of an rsync usage dump.
  Verified: the actual step body was extracted from the YAML (not retyped) and run against the
  real repo through an `rsync` stand-in that fails identically on a usage error — 337 files, both
  index assertions pass, `sf`/`nyc`/`engine` absent. Three negative cases each fire: rsync with
  no source/dest exits non-zero, a dropped `sf` exclude reports `sf leaked into the published
  tree`, and a missing `il/index.html` reports itself. The new lint was proven in both directions
  by reintroducing the exact bug. A sweep of all 88 shell-bearing files found no other instance.
  **Residual gap, deliberately not closed here:** `assemble` still does not run on pull requests,
  so a *different* kind of break in it would still land on main first. Running it per-PR means
  duplicating the Playwright job on every PR; the honest options are a paths-filtered trigger or
  extracting the assemble into a script both workflows call. Decide it at R5, when the deploy
  changes anyway to publish `sf/` and `nyc/`.

- **R3 (part 1) — SHIPPED (2026-08-24): one engine, three instances, one origin.**
  `engine/` now holds one copy of each of the 55 engine blocks and every instance's
  `index.html`/`sw.js` is composed from it (`scripts/compose_app.py`, gated in CI and at
  deploy). Parity stops being a claim a checker makes about three repositories and becomes a
  property of the layout: an instance cannot drift from a file it does not have. SF and NYC are
  imported with their history as `sf/` and `nyc/`.
  **The composer is deliberately small, and its first draft was not.** That draft also split
  each instance's local text into fragment files — ~26,000 duplicated lines per instance for a
  guarantee splicing already gives, and it put the composer in a fight with
  `generate_metro_files.py` over who writes a GENERATED region. Sharing only the ENGINE fences
  costs a fifth as much (408 KB), keeps exactly one writer per line, and dissolves the ordering
  question: every generated region lives outside every fence.
  **Importing paid for the composer immediately, twice.** Both forks were pinned three engine
  releases behind; composing delivered the v1.0.22→v1.0.25 bump that the release channel never
  managed to land, and their own changelogs' adoption notes were then worked through by hand —
  v1.0.24's one out-of-fence line (the point chip moves to the engine's `buildShareControl()`,
  the fork-level `embedBaseUrl`/`buildEmbedCode` deleted) and v1.0.25's data-shape change
  (`coverage-gaps.json` regenerated so `why` replaces `blocker`, without which each fork's
  gaps panel would explain half of what it used to).
  **CONSOLIDATION CREATES A BUG, AND FINDING IT FIRST IS THE POINT.** CacheStorage is per
  ORIGIN, and the engine's `activate` handler deleted every cache that was not its own —
  correct while an origin held one app, mutual destruction the moment it holds two. Three
  instances would have wiped each other's precached boundary geometry on every cross-instance
  visit. The sweep now retires only this instance's own superseded versions, identified by its
  cache name minus the version suffix. **Honest caveat:** an attempt to demonstrate the old
  handler evicting a sibling end-to-end did not reliably trigger the other instance's
  activation, so that half rests on reading the code — the filter deletes any key that is not
  `CACHE_NAME`, and the keys are the whole origin's — rather than on a reproduced wipe. The fix
  itself is verified in the browser.
  Verified: **each fork's OWN smoke test passes in full at its new path** (SF at `/sf/` —
  supervisor district, neighborhood, police district, all three legislative chambers with
  roster joins; NYC at `/nyc/` — borough, judicial district, municipal court, a point move
  across boroughs, the honest mid-river empty state), then all three driven in one browser
  profile: each caches its own shell, all three caches coexist, all three workers hold their
  own scope.
  **Importing is not publishing.** `sf/` and `nyc/` are excluded from the Pages deploy: each
  still serves from its own domain and carries its own canonical, and publishing here first
  would put a second live copy of each app on this origin. Removing that exclude is the switch
  that makes them live, and it belongs with their domain cutover (R5).
  **A trap the import created, and marked rather than left:** the fork trees brought their
  `.github/workflows/` with them, 16 files now sitting at `sf/.github/` and `nyc/.github/`
  where GitHub cannot see them — inert, but indistinguishable from live to anyone reading the
  tree. Each directory now carries a README saying so, why they are kept (they are the
  definition of the refreshes that must be rewritten with instance-aware paths when the
  automation moves), and where those refreshes actually run today: still in the fork
  repositories, deliberately, because running both would open two competing PRs against the
  same roster files.
  **Superseded by R3 part 3 (2026-08-24):** those ten refreshes have moved to the root with
  instance-aware paths, and the "they still run in the fork repositories" reason stopped
  holding at R5, when both fork domains were forwarded here. The count in this paragraph is
  also the count of FILES, not of frozen refreshes — six of the sixteen were duplicates of root
  jobs and were deleted rather than moved.
  **Measured, for the tooling reconciliation that remains:** `check_engine_parity.py` is
  byte-identical across all three instances (it rode the engine channel) and can simply be
  deduped. `generate_metro_files.py` differs by 370 lines, but SF's and NYC's copies are
  identical to each other — the same version-lag shape the engine blocks had. The rest are
  genuinely fork-specific rather than drifted: `validate_index.py` (595/635 lines apart),
  `smoke_test.mjs` (897/723) and `validate_sources.py` (1150/1473) encode each instance's own
  ground truth, layer set and source manifest. **So "unify the tooling" is the wrong goal for
  most of them** — the right one is a shared gate that takes the instance as a parameter, with
  each instance keeping its own facts.

  **Still open in R3:** the per-instance tooling. Each instance still carries its own
  `scripts/`, `metro-worksheet.json`, `docs/` and `schema/`; the shared gate scripts still know
  only about `il`. Reconciling those — the 585–891 divergent lines this assessment predicted —
  is the remaining work, and it is genuine porting rather than mechanical rewriting.

- **R2.3 — SHIPPED (2026-08-24): the Illinois app moved to `il/` and serves at `/il/`.**
  The structural half of "one repo, one site": the app is now an instance folder, the root is a
  redirect stub, and the shape that `/nyc/` and `/sf/` will land in exists. Moved under `il/`:
  `index.html`, `sw.js`, `sources.html`, the four landing pages, `manifest.webmanifest`,
  `og-image.png`, `icons/`, `fonts/`, `data/` and the two generated preview pages. Left at the
  root: `metro-worksheet.json`, `metros.json`, `sitemap.xml`, `robots.txt`, `CNAME`, the
  IndexNow key, `scripts/`, `docs/`, `districtry/`.
  **No symlinks anywhere, and that is a finding rather than a preference.** Both a
  `data → il/data` shim and root `index.html`/`sw.js` shims were considered and rejected on
  measurements: git does not traverse a symlink, so 60 roster workflows' `git diff --quiet`
  gate would have gone green-but-silent; and a root `index.html` symlink is incompatible with a
  redirect stub, since Pages would dereference it and publish a duplicate app at the root.
  So every path is explicit — 186 `data` joins across 140 scripts, 283 lines across 66
  workflows, and the gate scripts' own constants.
  **The root transition is designed around two measured facts.** Navigations were already
  network-first, so no returning visitor is ever served a stale app — the stub reaches them on
  their first online visit whether or not the worker has updated. But CacheStorage is
  per-ORIGIN, so a root worker and an `/il/` worker can delete each other's caches. Hence: the
  root `sw.js` is a kill switch with **no fetch handler at all** (a worker without one is
  skipped for navigations, which also makes the offline redirect loop structurally impossible),
  it deletes only the exact legacy cache name rather than sweeping a prefix, the stub
  unregisters only the registration whose scope is the origin root, and the instance's cache
  was renamed to `districtry-il-shell-v1` so the two can never name each other's storage. The
  stub preserves **query and hash** — the hash is the permalink, the query is the tagging every
  already-copied embed snippet still sends to the old root URL.
  **Three scripts needed real fixes, not path rewrites.** `check_roster_retention.py` reads its
  baseline with `git show <base>:<path>`, which cannot follow a move, so it now tries both
  layouts — without that, every PR *after* the move (not the move itself) would have failed
  with the wrong diagnosis. `validate_index.py` gained a `SCRIPT_ROOT` for the two repo-level
  assets it reaches through the index's own directory. `fleet_status.py` gained a per-instance
  path prefix for the remote fetch of Chicago's own gaps file.
  Verified: all 19 generated regions, `validate_index.py`, both fence lints, coverage-gaps,
  county-status, backfilled seats, `validate_workflow_deps.py`, the link gate's surface (1,298
  URLs), the preview freshness check, **the full Playwright smoke test against
  `http://localhost:8126/il/`**, and a purpose-written Chromium check of the transition itself:
  bare `/` redirects, a hash permalink survives, a query+hash embed URL survives with the query
  intact, and — the one that would have been silent — **the `/il/` worker survives a root
  visit**. The retention gate was run across the layout change specifically and compared all
  222 roster files; without the fallback it would have compared zero.

- **R2.1 — SHIPPED (2026-08-24): the template and engine-release channels retired.**
  The operator archived the Template and WI repos and confirmed the NYC/SF consolidation, which
  made two pieces of machinery not merely redundant but actively wrong: the template gate and
  its weekly push now target an archived repo, and **the Pages deploy was still splicing a
  hash-pinned engine bundle over the tree**, so any fence edit made in this repo would have been
  silently overwritten at deploy time — the exact trap the composer stage would have walked into.
  Deleted: `release-engine.yml`, `create-engine-tag.yml`, `engine-parity.yml`,
  `update-state-template.yml`, `scripts/{apply_engine,build_engine_artifact,build_state_template,bootstrap_state,check_template_placeholders}.py`,
  `templates/state/` and `engine.lock.json` (33 files). `smoke-test.yml` loses the template gate;
  `deploy-pages.yml` loses the fetch/verify/splice pair and now runs the merge gate and fence
  lint **on exactly the bytes being published**. `check_engine_parity.py` stays as the fence
  lint. NYC and SF simply stop receiving bumps until R3 imports them — no breakage, they freeze.
  **A finding that changed the R2.3 plan before it was written:** the audit of all 72 workflows
  found 60 roster refreshes gate their PR step on `git diff --quiet -- data/app/`, which through
  a planned `data → il/data` symlink would exit 0 against an index holding `il/data/app/...` —
  every refresh would go **green while silently never opening a PR again**, a failure no gate
  and no health check would catch. The symlink shim is abandoned; the `/il/` move rewrites the
  62 workflows' paths explicitly. Verified: fence lint, `validate_workflow_deps.py` (247 entry
  points), the 19 generated regions, `validate_index.py` and the preview freshness check all
  green after the deletion.

- **R1 — SHIPPED (2026-08-24).** The worksheet gained an opt-in `brand` key (app name,
  tagline, theme color, favicon, head/OG/twitter strings, analytics — GA id + hostname gate +
  GoatCounter endpoint) and the generator now owns seven brand-bearing GENERATED regions:
  `head-analytics`, `head-brand`, `head-theme`, `brand-palette`, `masthead-brand`,
  `goatcounter` in index.html and `sources-palette` on the sources page, plus a `METRO_BRAND`
  emission in the metro-config region (typeof-guard rule recorded there) and `explorer_name`
  plumbing through metros.json → `--sync-fleet` → `METRO_EXPLORERS`. Five of the seven new
  regions rendered **byte-identical** to the hand-written content they replaced (the
  faithful-rendering proof); the only content deltas were the palette comment alignment
  (whitespace) and the new `METRO_BRAND` var. The `brand-palette` region also closed a live
  two-copies risk: the worksheet's `palette` values and index.html's `:root` accents were two
  hand-kept copies of one fact. Inertness was proven, not assumed: the old and new generator
  produce **zero-diff output over copies of NYC, SF, Template and WI** (the v1.0.16 rule —
  a fork that has not opted in sees no change at all). The template stays PRE-BRAND by
  design: `build_state_template.py` unwraps the brand regions on emission (markers stripped,
  interiors substituted exactly as before), so the emitted template tree differs only by the
  palette whitespace plus the two engine-channel scripts carried verbatim — upgrading the
  template itself to brand-as-data belongs to the WI pilot (R-stage 3 prerequisite), not R1.
  Verified: all 19 generated regions `--check` clean, `validate_index.py`,
  `check_engine_parity.py`, `build_state_template.py --check`, and the full Playwright smoke
  test green; the districtry preview's 43 exactly-once transforms all survived (the preview
  was regenerated per its documented flow, not left stale).

## Alternatives considered

- **Brand-as-data only, stop there.** Cheapest; fully unblocks the rebrand; leaves the fork
  tax and the drift residue untouched. The fallback if consolidation appetite fades.
- **Per-metro subdomains with generated deploy repos** (the earlier draft of this record):
  source consolidates, but NYC/SF remain bot-pushed artifact repos because Pages serves one
  site per repo. Superseded by the path-based single site, which dissolves the constraint
  that forced deploy repos to exist — and makes the URL the wordmark.
- **Generated forks with scrapers left in fork repos.** Rejected: preserves triplicated
  infrastructure and creates a clobber race between bot pushes and fork-side roster PRs.
- **A bundler or framework.** Rejected: violates the recorded constraints and solves nothing
  the composer does not; the runtime is fine.

## Top risks

- Composer whitespace/final-newline bugs — loud by construction (the byte gate), first-draft
  class.
- Fragment mis-ordering when importing a fork — NYC's ENGINE block order differs from CHI's
  (verified), so each instance's manifest derives from *its own* file, never CHI's.
- The validate/smoke reconciliation in R3 being underestimated — it is porting work, not
  mechanical; SF fully before NYC, or NYC fully before SF, never both at once.
- Redirect-era SEO — meta-refresh transfers slower than 301s; decide early whether the old
  domains get a CDN front.

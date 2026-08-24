# Development-process assessment — the fleet, the rebrand, and the single-repo decision

**What this is.** The decision record for reviewing how this fleet is developed and deployed —
single-file no-build apps, a byte-identical fenced engine distributed by hash-verified releases
and fan-out bump PRs, worksheet-generated regions, a generated template repo, one repo per
metro — measured against the Districtry rebrand (`docs/DISTRICTRY_REBRAND.md`), with the
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
- **The brand model stopped matching the repo model.** Districtry is positioned
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
| **R2 — In-place reorg to `/il`** | The composer inversion lands with the move: engine fragments + `metros/il/`; composed `/il/index.html`; root serves a redirect stub to `/il/` for now; chidistricts.com keeps working throughout; the seven fenced brand strings become ordinary edits (no release channel needed) | compose→cmp byte-identity in CI; the full existing gate battery + smoke against `/il/` |
| **R3 — Import SF, then NYC** | Each as `metros/<id>/` + `/sf/`, `/nyc/`; their divergent validate/smoke copies (585–891 lines each) reconcile into the one script set — real porting work, budgeted as such; scraper workflows move and consolidate to matrix runners; old repos freeze behind a no-new-merges window | per-instance smoke; a no-op proof (the composed instance byte-equals the fork's deployed HEAD minus intended deletions); the retention gate re-baselined |
| **R4 — Landing page + Districtry skin** | `/` becomes the state-list landing (brand package, coverage); instances take the skin from worksheet brand keys; the preview machinery retires; WI bootstraps as `/wi` when ready | smoke + validate + link gates + a leftover-brand grep |
| **R5 — Domain cutover** | CNAME → districtry.com, DNS, one sitemap, analytics keys, redirect shells in the old repos/domains, search re-verification | `validate_card_links.py` + live probes + redirect checks |
| **R6 — Retire machinery** | Engine releases/locks/fan-out, the Template repo, cross-repo fleet_status, per-fork doc copies; archive NYC/SF/Template/WI with pointer READMEs | grep for dead references; docs regenerated |

Rebrand timing simplifies under this ordering: **chidistricts.com is never rebranded in
place** — Districtry ships as the identity of the new tree, and the old domains redirect at
R5.

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

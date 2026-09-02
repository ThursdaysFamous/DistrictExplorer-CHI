# Why Wisconsin was faster than Illinois — the county-level record

**What this is.** A measured comparison of the two hardest build problems this fleet has
taken on: Illinois's 91 (of 102) counties, added one at a time over about two months, and
Wisconsin's 72 (of 72), whose county-board *geometry* shipped complete in a single build
while its *rosters* are still closing out county by county. This is a retrospective, not a
build log — it draws on the county-by-county record already kept in the root `CLAUDE.md`,
`wi/CLAUDE.md`, `docs/EXPANSION_GUIDE.md`, `docs/COUNTY_STATUS.md`,
`wi/data/app/coverage-gaps.json`, and the two states' own scripts. Numbers below are measured
as of 2026-09-02 and will drift; where a live count matters, read it from the file named
beside it, never from this paragraph. A public-facing version of this same argument, written
for a general reader with the file paths sanded off, lives at
`docs/STORY_WISCONSIN_VS_ILLINOIS.md`.

**Verdict.** Wisconsin was not faster because the builder or the process improved between the
two efforts, though that happened too. It was faster mainly because it asked a genuinely
different question, in a state whose government answers a piece of it centrally. Illinois's
per-county grind was never optional — the state simply has no equivalent of what Wisconsin's
legislature built for exactly one purpose. Where the two states' problems are actually
alike — naming the *person* who holds a seat, not just drawing the seat's lines — Wisconsin's
per-county cost has been just as real. It is only organized so that it doesn't multiply the
size of the repository every time one more county closes.

## The headline numbers

- **Illinois: 91 of 102 counties served**, each added through its own investigation — a
  bespoke scraper, a bespoke builder, its own weekly GitHub Actions workflow, and in most
  cases its own multi-source proof that the geometry is real (`docs/COUNTY_STATUS.md`).
  Eleven counties remain, each with a distinct, named blocker (see below). This took about
  two months — the project itself is two and a half months old.
- **Wisconsin: all 72 counties' board-district *boundaries*** shipped in a single build, from
  a single statewide feed (`wi/scripts/build_wi_supervisory_districts.py`). The *rosters* —
  who holds each seat — were a separate problem entirely, and one that had to be solved a
  county at a time. **It finished on 2026-09-02: all 72 counties now carry named
  supervisors**, 1,591 seats of which 1,572 are named and 17 the counties themselves mark
  vacant (`wi/data/app/county-board-members.json`), and the standing `county-officials` gap
  is retired. The last stretch is the shape worth seeing: Ashland, Douglas, Florence, Forest,
  Iron and Sawyer closed in PRs #672–#674, Barron and Lincoln on 2026-09-02, and before them
  Langlade, Menominee, Chippewa, St. Croix, Marathon, Pierce, Clark, Pepin, Oconto, Door,
  Jackson and Waupaca — one county per PR, all the way down.
- Wisconsin's whole instance — 31 layers across four phases — went from nothing to
  "statewide and mostly complete" in three days, 2026-08-25 through 2026-08-27
  (`wi/CLAUDE.md`). Illinois has been adding counties for about two months and is still
  closing its last 11.

## Cause 1: build order is architecture, not effort

Illinois began as a single city. Its very first layers — ward, precinct, later county board,
judicial subcircuit, fire/park/library district — had no national or state publisher to lean
on, because they are Chicago- or county-specific concepts. Every one of them had to be
discovered and sourced from scratch, county by county, as the coverage ring grew outward.
There was no head start available to take.

Wisconsin began as a full state. On day one (2026-08-25) it shipped twelve layers wherever a
federal or state publisher already tiled the *entire* state — Congress, the state Senate and
Assembly, County, the TIGER school-district tilings, County Subdivision, City or Village,
ZCTA, Post Office, and the nearest-station Police/Fire pair. None of that required visiting a
single county website. `docs/EXPANSION_GUIDE.md` states the rule this taught in Part 0.2,
after the fleet had lived both ways:

> **Prefer statewide-first for a new state.** Wisconsin reached twelve honest layers in a day
> from national and state publishers, then earned depth where publishers existed; Illinois
> spent its first year as one city and is still filling counties.

This is an architectural difference, not a work-ethic one. Illinois could not have chosen
statewide-first — it was never a state instance to begin with; it grew into one dispatch
table at a time. Wisconsin got to choose, because by 2026-08-25 the fleet already knew
which choice was faster.

## Cause 2: one law, versus no law, for the single hardest layer

County-board district geometry was the single most expensive, most bespoke problem in
Illinois's 91-county grind: vector-PDF content-stream parsing and georeferencing (Jackson),
TLS chains missing their intermediate certificate (Coles, Gallatin, Vermilion), a paid GIS
licence negotiated in writing (Jo Daviess), three different election-results vendors swept
county by county because no county GIS existed at all (Clark, Crawford, Mercer, Edgar,
Franklin, Clinton, and others), and, for several counties, nothing but a clerk's plain
sentence that no map exists.

Wisconsin's equivalent problem is, for 71 of its 72 counties, one HTTP request. Wisconsin
statute requires it:

> Wisconsin is the one state in this fleet whose county board districts have a STATEWIDE
> publisher. Wis. Stat. 5.15(4)(br)1 makes every county submit its current supervisory
> district boundaries to the Legislative Technology Services Bureau twice a year (15 January
> and 15 July), and LTSB publishes the aggregate as an open ArcGIS feature service. So the
> 72-county answer that costs Illinois one build per county costs Wisconsin one fetch.
> — `wi/scripts/build_wi_supervisory_districts.py:8-13`

Illinois has no analog of the Legislative Technology Services Bureau for county board maps.
No Secretary of State or State Board of Elections office aggregates what Illinois's 102
county boards look like. Each county independently decides whether, how, and where to
publish — which is the entire reason Illinois's build became 91 separate detective stories
instead of one.

**This is a real institutional shortcut, not a magic one — the build still doesn't trust it
blindly.** The same script's own comment records that LTSB "republishes what a county CLERK
sent it, and a defective submission stays defective." Its July 2026 file merged two of
Trempealeau County's districts into one (LTSB's "17" silently covers the county's own 15 and
17 together) — caught by a ward-reconciliation gate and a seat-count mismatch, not by
trusting the state's own aggregate. Trempealeau alone is built from the county's own service;
the other 71 counties come from LTSB. The fleet's shipped total is 1,590 districts: 1,589
straight from LTSB's July 2026 submission window, plus Trempealeau's real 17 swapped in for
LTSB's merged 16. Centralization removed 71 counties' worth of archaeology. It did not remove
the need to check the state's own homework.

## What did *not* get easier: naming the person, not the district

Wisconsin publishes no statewide roster of *who* holds each supervisory seat — only the state
publishes the *lines*. The `county-officials` gap record put it plainly while it stood, and
it is quoted here in the past tense because it was retired on 2026-09-02:

> Wisconsin publishes every county's district lines in one file but no statewide roster of
> the people in them. Sixty-six counties' district-keyed lists can be obtained, and those
> ship; the rest publish maps, PDFs, or nothing readable.

**That gap closing does not soften the point; it is the point.** The lines took one fetch.
The people took every county in the state, individually, over about a week of one-county
PRs — and the last six were the hardest precisely because no statewide source existed to
fall back on. Getting there required a roster problem every bit as heterogeneous as
Illinois's:
`wi/CLAUDE.md` lists 41 plain board pages, three counties' own directories (Clark, Pierce,
Marathon), a district table (St. Croix), board-page "h-cards" (Chippewa), a joint
county/town board (Menominee), two counties' board tables (Langlade, Barron), three
counties' own GIS layers (Milwaukee, Racine, Lincoln), an Internet Archive rescue (Fond du
Lac), a constituent directory (Dodge), two directory PDFs (Kenosha, Adams), one framed table
(Columbia), and nine robots.txt-frozen snapshots dated and carried forward rather than
re-scraped. The six that held out longest — Ashland, Douglas, Florence, Forest, Iron and
Sawyer — were an honest standing gap for as long as they were unread, named in the panel
rather than guessed at, and they closed only when each one's source was tracked down.

The difference from Illinois isn't that Wisconsin's roster problem is easier. It's purely
organizational. All of that heterogeneity lives inside **one** Python file's per-county
lookup table and **one** weekly workflow, `update-wi-county-board-roster.yml`
(`.claude/skills/roster-pipeline/SKILL.md:224-229` confirms Wisconsin and Iowa deliberately
do not use Illinois's per-county pattern). Illinois's convention, set early and never
revisited at scale, is a dedicated scraper, builder, and workflow file **per county** — 53
separate `update-<county>-county-board-roster.yml` files sit in `.github/workflows/` today
(counted directly against the live directory, 2026-09-02). Adding a Wisconsin county to the
roster is one dictionary entry and a re-run — which is how all 72 of them landed. Adding
Illinois's county #92 is three new files, a new cron slot, and a new PR. Same quantity of
real-world messiness; radically different cost per county added, and the difference compounds
across a whole state.

## Cause 3: Wisconsin started from the answer key

By 2026-08-25, Illinois had already paid — the hard way, in production, one county at a
time — for the worksheet/engine/generated-region machinery, the `county-n-plus-1` and
`roster-pipeline` skills, and a growing list of lessons the docs now state as flat rules
instead of live discoveries: a site refusing every request is not the same claim as a county
refusing (rediscovered independently in Illinois's Knox, Johnson, and Perry, and again in
Wisconsin's Lincoln County, whose real GIS host sits on an address linked from nowhere on the
site that blocks this client); a robots.txt disallow governs retrieval, never what already-
public information may be shown; a floor is a measurement of what a source publishes, never a
target for it. Wisconsin's builders cite these as settled facts. Illinois's builders are where
most of them were first paid for.

## A concrete pair

**Jackson County, Illinois** needed a bespoke pipeline invented for it alone: its adopted
board map exists only as a vector PDF, so the build reads the seven district polygons as
filled path objects straight out of the PDF's content stream, georeferences them to
EPSG:3436 by matching aspect ratio to four decimal places, and resolves three
split-precinct census blocks against a certified canvass — four independent gates, built for
one county, because nothing about that county's map was reusable anywhere else.

**Barron County, Wisconsin** shipped the same day a link that had been sitting in plain sight
for a week was finally followed. Its geometry had been in LTSB's feed the whole time.
Its official `.gov` page names only two people in 75 KB of prose — but that same page links
the real roster twice, as "Individual Contact Information for County Board Supervisors." The
county's front door had already been corrected on 2026-08-26; the link on it went unfollowed
until 2026-09-02. As `wi/CLAUDE.md` puts it: "finding the host that serves a board page is not
reading it." Once read, it was an ordinary district-table scrape — no harder than any other
county's roster page. Same category of problem as Jackson — find and read the county's own
roster page — wildly different cost, because the geometry underneath it
required zero invention.

## The honest caveat

Three different effects are easy to collapse into one story, and shouldn't be:

1. **A genuine, state-specific institutional advantage** (Wisconsin's LTSB filing law), which
   solved exactly one recurring problem — county-board geometry — completely, statewide, for
   free.
2. **A generic "second state built with a mature toolkit" effect**, which would have made
   Wisconsin faster than Illinois's *first month* even if Wisconsin's government were every
   bit as fragmented as Illinois's. Some of this speed is not about Wisconsin at all.
3. **Measurement asymmetry, which flatters Wisconsin and is this project's own doing.**
   Wisconsin's county coverage is a hand-curated, twice-corrected, second-witnessed table;
   Illinois's is substantially an automated sweep that permutes a county's domain from its
   clerk's e-mail address. Those two instruments have opposite error profiles, and this repo
   documents the consequence: on 2026-08-29 SIX of the 72 Wisconsin county URLs were found
   wrong, each having passed an earlier status-code sweep, and the wrong-URL signatures were
   exactly the ones that certify an Illinois county dark — GoDaddy parking landers (Kewaunee,
   Rusk), HTTP 503 (Barron, Shawano), mail-only no-A-record domains (Columbia, Crawford,
   Sauk). **Measured Illinois-style, Wisconsin would have reported six to eight dark
   counties.** Pulaski, IL is the proof from the other direction: its record read "the
   county's website cannot be reached from here" for weeks because the permutation lands on
   `pulaskicountyil.gov`, which carries only mail, while the county publishes a full site at
   `pulaskicountyil.net`. Before treating any IL-vs-WI coverage contrast as a fact about the
   two states, check whether it is a fact about the two instruments.

A hypothetical Illinois with its own LTSB would not have matched Wisconsin's overall pace —
it would still lack a statewide roster (as Wisconsin does), and it would still need per-county
work for precincts, municipal wards, and the fire/park/library-district layer that Wisconsin's
smaller layer count doesn't carry at all. Illinois also has 30 more counties to begin with —
102 against 72, a 42% larger frontier before any institutional difference is counted. The LTSB
law explains why Wisconsin's single hardest layer collapsed to one fetch. It does not, by
itself, explain the whole gap.

## Where Illinois stands today

Eleven counties remain in the researched-but-unserved frontier, each with a distinct,
already-measured blocker (`docs/COUNTY_STATUS.md`):

| County | Blocker |
|---|---|
| Bureau | no board-district map published anywhere |
| Champaign | GIS consortium licence (`champaign-piatt-ccgisc-license`, shared with Piatt) |
| Christian | no board-district map published |
| Fayette | no board-district geometry published |
| Ford | 2021 remap left "to be determined" after the census delay |
| Henderson | no reachable county website |
| Jasper | no board-district map published |
| Lawrence | no board-district map published |
| Marion | no board-district map published |
| Piatt | same GIS consortium licence as Champaign |
| Pope | no board-district map published |

Eleven counties, eight distinct failure modes between them. That variety is itself the
Illinois story in miniature: there is no single fix, because there is no single office to
fix. Closing them is exactly the same kind of one-clerk-at-a-time work the first 91 required,
which is why it is being done by hand rather than automated away.

## The forward-looking lesson

`docs/EXPANSION_GUIDE.md` Part 0.2 now states "prefer statewide-first" as a rule for every
future state, and Iowa — the fleet's second state, arriving 2026-08-27 with, per the root
`CLAUDE.md`, "zero national-tier layers to lean on at any point" that Wisconsin's original
four could — reached all 99 counties following the same order. That is two data points
for the architectural claim, not one.

**Iowa also sharpens what the institutional claim actually is, and it is not "a statewide
file exists."** Iowa has one: the Iowa Legislature publishes a `CountySupervisorDistricts`
layer, and it is that instance's only statewide source for the concept. But Jones County has
**zero rows in it** — measured both by name and by its own FIPS, so not a naming mismatch —
and the county therefore carries no supervisor-district card at all (`jones-county-supervisor`,
the instance's single county gap). Wisconsin's aggregate has no such hole because Wisconsin's
is not merely *maintained*, it is *filed*: a statute obliges all 72 counties, twice a year,
and a county missing from LTSB's file would be a county out of compliance. **A maintained
aggregate is a courtesy and can be short a county; a compelled one is a duty and shows up
when it isn't.** So the question to ask of the next state is not whether some agency publishes
a layer, but whether anything obliges every county to be in it — a fact about that state's
government, discovered the same way Wisconsin's was, by reading one statute rather than by
assuming the pattern repeats.

## Sources

- `docs/COUNTY_STATUS.md` — Illinois served/frontier counts and per-county blockers
- `wi/scripts/build_wi_supervisory_districts.py` — LTSB source, Trempealeau correction, gates
- `wi/data/app/coverage-gaps.json` (`county-officials` entry) — the 6-county roster gap
- `docs/EXPANSION_GUIDE.md` Part 0.2 — the statewide-first vs. metro-first table and rule
- `.claude/skills/roster-pipeline/SKILL.md` §10 — the per-county-triple vs. one-file contrast
- `wi/CLAUDE.md` — Wisconsin's phase history, layer list, and roster-source inventory
- Root `CLAUDE.md` — Illinois's county-by-county build record
- `.github/workflows/` — live directory listing (53 Illinois per-county roster workflows vs. 1 Wisconsin)

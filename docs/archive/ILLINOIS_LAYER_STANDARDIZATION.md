# Illinois Layer Standardization — the governance taxonomy behind the roster

Status: **decision record + full-roster audit (2026-07-27) — the pre-county-expansion pass.**
Owner: CHI (fork-level). This pass changes **no app code**; it fixes the ruleset the next
expansions are built and reviewed against, and records its candidates in the guidebook backlog.
Cross-refs: `docs/COUNTY_LAYER_CONSOLIDATION.md` (the dispatcher and rules 4–5 this
generalizes), `docs/STATEWIDE_EXPANSION_PLAYBOOK.md` (§4's FREE / DERIVE / PER-COUNTY source
classes), `docs/MUNICIPAL_COUNCILS_PLAYBOOK.md` (the municipal instantiation and source
ladder), `docs/DATA_LAYER_GUIDEBOOK.md` (the fleet inventory; this pass's candidates live in
its backlog), `docs/METRO_EXPANSION_PLAYBOOK.md` §3 step 4 (the at-large rule this doc
promotes to a fork axiom).

## 0. Why this exists

The app is about to grow past the seven-county metro. Before it does, this is the deliberate
pass over every layer we currently surface, asking the same four questions of each: **what is
its purpose (what question does it answer), what level of governance is it, what function
within that governance, and how is its data sourced for a person standing at an arbitrary
Illinois point?** The goal is that a user anywhere in Illinois gets a seamless experience —
the *concepts* stay constant, and what varies by location is which instance answers, at what
honest depth.

**The county-expansion invariant** (the conclusion of the pass, stated first):

> Expanding to another Illinois county changes **which dispatch entries and roster rows
> exist — never which layers exist.** A new county lands as: entries on the consolidated
> concept layers, roster rows joined into the statewide identity layers, and a coverage
> outline. The toggle roster does not grow. A brand-new layer is justified only by a
> **governance function no current concept covers**, and it launches consolidated
> (`COUNTY_LAYER_CONSOLIDATION.md` rule 2b).

Chicago is not a special case under this model — it is the **reference instance** of each
concept: `ward` is the districted municipal council instance, `ward-precinct` is the
municipal-election-authority precinct instance, CPS zones are one district's attendance
instance. Where Chicago has a concept nobody else has (CCPSA councils, community areas), that
is recorded, not generalized; where everyone else has a concept in a different *shape* (an
at-large village board instead of 50 wards), the shape difference is handled by the axes
below, not by a new layer.

## 1. The classification axes

### 1.1 Level of governance

Federal · State (incl. the elected judiciary) · County · Township · Municipal · School
district · Special-purpose district (fire, park, library, water reclamation, TIF…) ·
Election administration (the authority that runs voting, distinct from any one government) ·
Reference / amenity (no governance at all — honest context).

### 1.2 Function within governance

- **Representation** — who represents you on a body (legislative seat, board district,
  elected judge, elected oversight).
- **Whole-unit office** — an officer elected by the entire unit (mayor, county clerk,
  township supervisor, at-large trustee).
- **Service / taxing jurisdiction** — which body taxes and serves this point (fire
  protection, park, library, water reclamation, TIF increment).
- **Service assignment** — which facility serves this point (attendance zones, police
  beat/district as patrol areas, polling place).
- **Election administration** — precinct and voting-site machinery.
- **Reference** — identity and context (ZIP, community area, nearest amenities).

One deliberate out-of-scope class: **party offices** (precinct committeeperson, ward/township
committeeman). Elected, but internal to party structure — the fleet precedent is NYC's
District Leader / State Committee entry: *recommend never* (`DATA_LAYER_GUIDEBOOK.md`
backlog).

### 1.3 Election geometry — the axis that decides surfacing

This is the user-visible crux of county-to-county commonality: Chicago's council is elected
by ward; most municipal councils are elected at-large; some suburbs elect by ward; commission
counties elect their boards county-wide. The body is the same *concept* everywhere — the
**election geometry** is what varies, and it alone decides the surface:

| Election geometry | Surfacing rule | Shipped precedents |
|---|---|---|
| **DISTRICTED** — seats elected by sub-geography | A polygon concept layer (Pattern B, §2); the card names *your* representative | `ward`, `county-board`, `school-board` (ERSB), `judicial-subcircuit`, `ccbr` |
| **AT-LARGE** — whole-unit electorate | Roster rows on the unit's **identity card** (Pattern A); never a polygon layer — an at-large body adds zero point-discrimination | mayor + trustees on `municipality`; clerk on `county`; MWRD's nine at-large commissioners = link row |
| **APPOINTED** — no electorate | Labeled rows / links only, never presented as elected | CPS network chiefs ("chief in dataset props", labeled); NYC community-board chair precedent |
| **NONE / ADMINISTRATIVE** — no officer at all | Identity + honest official links | precincts, ZIP, TIF, attendance zones |

The at-large rule already existed as fleet doctrine (`METRO_EXPANSION_PLAYBOOK.md` §3 step 4:
"a citywide polygon adds zero point-discrimination"); this pass promotes it to the fork's
standing axiom because Illinois expansion will hit it constantly — at-large village boards,
commission-county boards, every non-Chicago school board.

### 1.4 Sourcing dimension ≠ dispatch dimension

`COUNTY_LAYER_CONSOLIDATION.md` proved these are different questions; the pass names the
three dispatch dimensions now in use so future concepts pick deliberately:

- **Dispatch by county** — disjoint per-county footprints, one concept toggle
  (`registerCountyLayer`): `county-board`, `judicial-subcircuit`, `fire-district`,
  `park-district`, `library-district`, `county-precinct`.
- **Dispatch by municipality (place GEOID)** — one statewide tiling, county-*sourced* rosters
  joined per place: `municipality` officials (and the future suburban-ward tier, `subOf
  municipality`, dispatched per publishing source).
- **Dispatch by election authority** — see §4.2. Illinois voting is administered by ~108
  authorities: county clerks (101, already scraped weekly from ISBE for the `county` card),
  a few municipal boards of election commissioners (Chicago's is one), and Peoria's appointed
  commission. `ward-precinct` (Chicago BOE) vs `county-precinct` (clerks) is this dimension
  already in production — the split is principled, not ad hoc.
- **No dispatch** — a single statewide source: the TIGERweb identity layers, the chamber
  layers, `zip-code`.

## 2. The three surfacing patterns

- **Pattern A — identity layer + whole-unit officers on its card.** The polygon answers
  "which unit am I in"; the card carries every officer elected unit-wide. `county` (+ clerk),
  `municipality` (+ mayor/president, at-large board, clerk/treasurer), `township` (identity
  today; officers are a recorded candidate, §4.5).
- **Pattern B — districted-body concept layer.** One toggle per concept, dispatched per
  source; the card names your seat-holder. `ward`, `county-board`, `school-board`,
  `judicial-subcircuit`, `ccbr`, plus the service/taxing district layers (fire/park/library —
  districted *jurisdictions*, whatever their board's election mode).
- **Pattern C — nearest-N amenity.** No containment exists; honest straight-line proximity
  (`police-station`, `fire-station`, `post-office`, `library`, `school-site`, `early-voting`).

**The worked example (the motivating case).** "A city has a mayor and a council" resolves
differently by election geometry, with zero new layers:

| Place | Head of government | Governing body | Where it surfaces |
|---|---|---|---|
| Chicago | Mayor — **currently missing, finding §4.1** | 50 alderpersons by ward | body: `ward` layer (Pattern B); head: `municipality` card (Pattern A) once §4.1 ships |
| Berwyn (Cook) | Mayor on `municipality` card | 8 alderpersons, ward-badged rows; *your* ward = Tier B follow-up | Pattern A now; Pattern B (`subOf municipality`) when ward polygons land |
| Alsip (Cook) | Village President on card | 6 at-large trustees on card | Pattern A only — at-large, correctly no polygon |
| Diamond (Will) | President | commission-form board | Pattern A only |

That is the model working as designed — the remaining asymmetry is Chicago's own head-of-
government row (§4.1).

## 3. The 39-layer audit

Every registered layer, classified. "Statewide story" = what expansion does to it under the
invariant (DONE = already statewide; ENTRY = new counties join as dispatch entries; ROSTER =
new counties join as roster rows; GATED = honest instance of a general concept, generalized
through a different concept/card; UNIQUE = recorded Chicago/Cook-only, no generalization).

### Political (11)

| id | Answers | Level | Function | Elected by | Statewide story |
|---|---|---|---|---|---|
| `congress` | your U.S. House rep | Federal | representation | district (17) | DONE |
| `il-senate` | your state senator | State | representation | district (59) | DONE |
| `il-house` | your state rep | State | representation | district (118) | DONE |
| `il-supreme-court` | your Supreme Court district | State (judicial) | representation | district (5) | DONE · candidate: Appellate District card row — the five appellate districts share this exact map (Ill. Const. art. VI; PA 102-0011 redrew both) — a card row, never a second layer (§4.9) |
| `judicial-subcircuit` | your resident-judge subcircuit | State (judicial), county-organized | representation | subcircuit (PA 102-0693; structurally n/a in some circuits — Kendall precedent) | ENTRY per subcircuit county · statewide `judicial-circuit` DERIVE stays blocked (recorded) |
| `county-board` | your county-board district + member | County | representation | district in all 7 metro counties; **downstate: commission counties (17) elect 3 commissioners county-wide** | ENTRY where districted · **at-large counties → county-card roster rows, no polygon** (§4.3) |
| `ccbr` | your Board of Review district | County | representation (tax appeals) | district (3) — **elected only in Cook** (35 ILCS 200/5-5); elsewhere appointed/ex officio | UNIQUE · other counties: at most a labeled link row on the `county` card |
| `school-board` | your ERSB district + member | School district | representation | district — **Chicago is the only districted-elected school board in IL** | UNIQUE as a polygon · everywhere else the board is whole-district-elected → Pattern A on the school-district cards (§4.4) |
| `ward` | your alderperson | Municipal | representation | ward (50) | GATED — the reference instance of "districted municipal council"; suburban instance = Tier B ward polygons `subOf municipality` (recorded); at-large councils stay on the `municipality` card |
| `ward-precinct` | your Chicago precinct | Election administration | election admin | n/a | GATED — the municipal-election-authority instance of "voting precinct"; dispatch dimension is the authority (§4.2) |
| `early-voting` | nearest early-voting/drop-box sites | Election administration | election admin | n/a | GATED — Chicago BOE sites only today; expansion = per-authority site files (§4.2) |

### Safety (7)

| id | Answers | Level | Function | Elected by | Statewide story |
|---|---|---|---|---|---|
| `police-district` | your CPD district + station | Municipal (city dept) | service assignment | n/a (command staff, labeled) | GATED — Chicago instance of "who polices this point"; the general concept is per-municipality (one PD per muni as a rule, sheriff for unincorporated) → candidate card rows, never fake geography (§4.6) |
| `police-beat` | your CPD beat | Municipal (city dept) | service assignment | n/a | UNIQUE (`subOf police-district`) — suburbs publish no beat geometry |
| `ccpsa-district-council` | your elected police-oversight council | Municipal | representation (oversight) | district (22, shares CPD geometry) | UNIQUE — Chicago's ECPS ordinance has no analog (fleet matrix records the same for NYC/SF) |
| `fire-district` | which fire protection district taxes/serves you | Special district | service/taxing | FPD trustees typically appointed (70 ILCS 705; elected where referendum-opted) — card depth follows the county source | ENTRY · municipal fire departments deliberately excluded — the municipality itself provides that service (§4.7) |
| `dupage-county-special-police` | township special-police tax area | Township-level special district | service/taxing | n/a (funds elected Sheriff's patrol) | single-county — converts to a concept entry only if a second county publishes an analog tiling |
| `police-station` | nearest stations | amenity | reference | n/a | DONE-capable — USGS national source; widens with the bbox |
| `fire-station` | nearest stations | amenity | reference | n/a | DONE-capable — same |

### Schools (9)

| id | Answers | Level | Function | Elected by | Statewide story |
|---|---|---|---|---|---|
| `school-district-unified` / `-secondary` / `-elementary` | which school district serves/taxes you | School district | service/taxing + governance identity | board elected whole-district (Chicago's districted ERSB is the shipped exception) | DONE (identity) · enrichment candidate: at-large boards/superintendent contact ride these cards, Pattern A (§4.4) |
| `cps-network` / `cps-hs-network` | your CPS admin network + chief | School district (internal admin) | administration | n/a (appointed, labeled) | UNIQUE — sub-district admin regions exist only in mega-districts (NYC CSD precedent) |
| `cps-elementary` / `cps-middle` / `cps-high` | your zoned school | School district | service assignment | n/a | GATED — one district's instance of "attendance boundary"; other districts publish per-district or not at all → per-district opt-in class, never a statewide claim (§4.4) |
| `school-site` | nearest schools | amenity | reference | n/a | Chicago-sourced today · statewide source candidates recorded (ISBE directory / NCES EDGE), unevaluated |

### Geography (12)

| id | Answers | Level | Function | Elected by | Statewide story |
|---|---|---|---|---|---|
| `county` | your county + clerk | County | identity + whole-unit offices | clerk elected county-wide | DONE · enrichment path: the other countywide elected officers (sheriff, treasurer, state's attorney, circuit clerk, coroner, auditor, recorder…) are Pattern A rows — per-county under rule 4, no keyed statewide source verified (§4.5) · commission-county boards also land here (§4.3) |
| `township` | your township / county subdivision | Township | identity (+ future offices) | supervisor, clerk, assessor, highway commissioner, 4 trustees — all township-wide (60 ILCS 1) | DONE (identity) · officer rosters are a recorded candidate via the same clerk yearbooks as municipal (§4.5); Chicago's structural empty (townships abolished 1902) already honest |
| `municipality` | your municipality + its government | Municipal | identity + whole-unit offices | mayor/president municipal-wide; board at-large **or** by ward (roster carries `district` per member) | DONE (identity) · ROSTER per county (Cook+Will live; 5 specified) · Chicago head/officers gap = §4.1 |
| `county-precinct` | your voting precinct (+ polling place where published) | Election administration | election admin | n/a | ENTRY per authority (§4.2) · Kendall's polling-place join is the model enrichment |
| `park-district` | which park district taxes/serves you | Special district | service/taxing | elected commissioners (70 ILCS 1205) — card depth follows county source | ENTRY · McHenry recorded gap (publishes facilities, not districts) |
| `library-district` | which library body taxes/serves you | Special district | service/taxing | district trustees elected (75 ILCS 16); municipal library-fund boards appointed | ENTRY · municipal-fund rows follow the complete-tiling rule (§4.7) |
| `mwrd` | in/out of the MWRD | Special district | service/taxing | nine commissioners at-large (the at-large rule: link row, no sub-geometry) | Cook body UNIQUE, but the **concept class** (sanitary / water-reclamation districts) has collar analogs → conversion trigger recorded (§4.8) |
| `tif-district` | your TIF increment district | Municipal finance overlay | service/taxing | none | Cook today · Kendall's `TIF_Districts` service is the recorded second-county conversion trigger |
| `community-area` | your Chicago community area | Reference | reference | none | UNIQUE — Chicago's statistical geography; no analog, correctly city-only |
| `zip-code` | your ZCTA | Reference | reference | none | DONE |
| `post-office` | nearest post offices | amenity | reference | n/a | DONE-capable — USGS national source |
| `library` | nearest library branches | amenity | reference | n/a | Chicago (CPL) sourced · statewide candidate (Illinois State Library public-library directory), unevaluated; `library-district` already answers the governance half everywhere sourced |

## 4. Commonality findings — county to county

The substance of the pass: where the same governance concept recurs in different shapes, and
the standard answer for each. Items marked **candidate** are recorded in the guidebook
backlog, not commitments.

### 4.1 Municipal government (the motivating example) — model correct, one asymmetry

The `municipality`-card design already handles districted-vs-at-large councils correctly
(§2's worked example): the roster's per-member `district` field, the ward badges, and the
Tier B geometry follow-up mean **no new layer is ever needed for any council shape**. The
pass found one real asymmetry: **a Berwyn resident sees their mayor; a Chicago resident does
not.** Chicago is rightly excluded from the *board* section (its council is the `ward`
layer), but its whole-unit officers — Mayor, City Clerk, City Treasurer — are exactly the
Pattern A rows every suburb now gets, and no surface carries them (verified: the only "mayor"
references in `index.html` are a ward-lookup URL and a CCBR history comment). The Cook DOEO
source covers the Clerk's suburban jurisdictions only. **Candidate:** a hand-verified
`1714000` entry (head + officers, no board section; the `school-board-members.json`
precedent), with a pointer row to the Ward layer for the council.

### 4.2 Election administration dispatches by authority, not by county

`ward-precinct` vs `county-precinct` is not a Chicago quirk — it is the general rule
surfacing for the first time: **the election authority is the dispatch dimension for every
election-administration concept** (precincts, polling places, early-voting sites). ISBE's
election-authority directory — already scraped weekly for the `county` card — is the keyed
roster of authorities. Consequences recorded now: when expansion reaches another
municipal-commission city (Rockford/Bloomington class), its precincts join as an authority
entry exactly as Chicago's did, coverage-carved out of the county entry the way
`suburbanCookCoverage` already carves Chicago out of Cook; and `early-voting` generalizes as
per-authority site files (hand-curated per election, the shipped Chicago class) — a collar-
clerk tranche is the natural first increment. **Candidate**, not scheduled.

### 4.3 County boards: districted in the metro, at-large downstate

All seven metro counties elect by district, so `county-board` is uniformly Pattern B today.
Downstate, the 17 commission counties elect three commissioners county-wide, and some
township counties elect their boards at-large — there the at-large rule applies: **board
roster rows on the `county` card, no polygon, no toggle change.** Decide districted-vs-
at-large per county at expansion time (rule 4 already forces the officeholder decision in the
same change; this adds the geometry decision to the same checklist).

### 4.4 School governance: one districted exception, statewide at-large rule

Every Illinois school district has an elected board; Chicago's ERSB is the only districted
one, and it already ships as the `school-board` polygon. Everywhere else the board is
whole-district-elected → Pattern A: **board/superintendent/contact enrichment belongs on the
`school-district-*` identity cards** (ISBE's directory is the plausible keyed source —
candidate, unevaluated; never guess names). Attendance zones (`cps-*`) and admin networks are
intra-district structure: the former generalize only as **per-district opt-ins** where a
district publishes boundaries (the suburban-ward shape: per-source, `subOf` its district),
the latter effectively don't generalize (mega-district phenomenon). No new school layers at
county expansion — a new county changes *nothing* in the schools group except which districts
the statewide cards resolve.

### 4.5 The whole-unit officer rosters are one recurring pattern — and often one source

`county` clerk (shipped) → the remaining countywide officers; `municipality` head/board
(shipped for Cook+Will) → the five specified counties; `township` officers (nothing yet).
These are all Pattern A rows fed per county under rule 4, and — the practical find — **the
same county-clerk yearbooks already specified for municipal officials also print township
officers** (Kane's Government Guide, Kendall's and McHenry's yearbooks, Will's directory
class). **Candidate:** when those five municipal scrapers are built, capture the township
sections in the same pass (verify depth at build time; TOI link stays the statewide floor).
Countywide officers beyond the clerk have no verified keyed statewide source — per-county at
expansion, honesty floor = link to the county.

### 4.6 "Who polices this point" — the honest generalization of the police layers

`police-district`/`police-beat` are Chicago's instance of a concept every point has: an
incorporated point is policed by its municipal PD (rarely with published sub-geography); an
unincorporated point by the elected county Sheriff. The generalization is **not** a boundary
layer — it is (a) a **candidate** law-enforcement row on the `municipality` card (keyed
statewide source unevaluated; ILETSB's agency roster is the one sighted class) and a Sheriff
row among the county officers of §4.5, plus (b) the already-metro-wide `police-station`
nearest-N. `ccpsa-district-council` stays recorded Chicago-unique. Never draw a department
boundary no agency publishes.

### 4.7 Special-district tilings: the municipal-row rule, stated once

The shipped fire/park/library decisions imply a rule this pass makes explicit, because every
new county will re-pose it: **a municipal service row belongs in a special-district concept
layer only where the county's tiling records that class of municipal body completely;
partial/lone municipal rows are excluded.** Precedents: Kendall's library tiling keeps its
municipal city-library funds (it records *every* library taxing body — the Cook L19+L20
shape) while McHenry's lone Crystal Lake row is excluded; municipal fire rows are excluded in
McHenry and Kendall (fire concept = independent FPDs; a municipal fire department is the
municipality, already surfaced as such). A partial inclusion lies by omission — a lone city
row implies every other city has no library fund.

### 4.8 Single-county layers carry pre-registered conversion triggers

Per the consolidation rule, a dedicated layer converts to a dispatched concept when its
second county ships: `tif-district` → Kendall's `TIF_Districts` service (already recorded);
**`mwrd` → refined here**: the MWRD *body* is unique, but the *concept class* — sanitary /
water-reclamation taxing districts — has collar analogs (e.g. Lake's North Shore WRD,
Kane/Kendall's Fox Metro WRD) and Cook's Clerk catalog carries an unwired Sanitary tiling
(L12, recorded). If a second county's sanitary tiling is ever evaluated and shipped, `mwrd`
becomes the Cook entry of a `sanitary-district` concept rather than staying dedicated —
board election/appointment varies by statute, so card depth follows each source (rule 4).
`dupage-county-special-police` has no second-county analog sighted; it stays dedicated.

### 4.9 Judiciary: complete in the metro; two cheap statewide notes

Subcircuits are done for the metro (Kendall structurally n/a); the statewide `judicial-
circuit` DERIVE remains blocked on an authoritative county→circuit source (recorded — do not
hand-encode). Two candidates that add **card rows, not layers**: the five **Appellate
Districts** share the Supreme Court district map exactly (Ill. Const. art. VI; PA 102-0011) —
a row on the `il-supreme-court` card covers appellate representation statewide for free; and
the **Regional Superintendent of Schools** (~35 elected multi-county ROE regions) is a
DERIVE-class candidate (county→region table + ISBE directory; verify the suburban-Cook ISC
and Chicago carve-outs before believing it — same source-risk class as the circuit table).

### 4.10 Amenities: national sources generalize, city sources get candidates

`police-station` / `fire-station` / `post-office` ride USGS National Map layers — statewide
is a bbox widening, nothing else. `school-site` (CPD-org ArcGIS) and `library` (CPL Socrata)
are city-sourced; statewide candidate sources are recorded (§3), unevaluated. `early-voting`
is §4.2's per-authority story.

## 5. What a user sees, standing where (the seamlessness matrix)

The location-relevance system already produces the right *shape* everywhere — layers hide
outside coverage rather than erroring. What varies is depth, and each step down is a recorded
gap or candidate above, not an accident:

| Standing in… | Resolves today | Honest gaps at that spot |
|---|---|---|
| **Chicago** | full stack: statewide set + ward/ward-precinct, CPD district/beat, CCPSA, ERSB, CPS zones + networks, community area, city amenities, early voting, Cook set (ccbr/mwrd/tif, fire/park/library where the Clerk tilings apply) | **no head-of-government row** (§4.1); `county-precinct` correctly hidden (BOE precincts are `ward-precinct`) |
| **Suburban Cook** | statewide set + county-board/subcircuit/ccbr/mwrd/tif + fire/park/library + suburban precincts + municipal officials (full body, DOEO) + suburban wards *pending Tier B* | your *specific* alderperson where ward-elected (Tier B geometry, recorded); early voting (§4.2) |
| **Collar counties** | statewide set + county-board (+rosters), subcircuit (except Kendall, n/a), fire/park/library per recorded entries, precincts (+Kendall polling places), municipal officials at each county's honest depth (Will full; DuPage/Kane/McHenry mayor-level and Lake contact-only — specified, unbuilt) | the five municipal-officials builds; McHenry park gap; early voting (§4.2) |
| **Downstate (beyond the metro)** | the statewide set: congress, il-senate/il-house, il-supreme-court, county (+clerk), township, municipality (identity), school districts ×3, ZIP | everything PER-COUNTY hides until sourced (correct behavior); municipal/township/county-officer rosters are link-only; input-shell note below |
| **Outside Illinois** | nothing claims to apply (negative-point ground truth) | — |

**Input-shell caveat:** map clicks resolve statewide already, but the bounded type-ahead
geocoder and `PERMALINK_GATE` still stop at the greater-metro envelope — widening them (and
the METRO_NAME/branding audit) is the recorded rebrand-pass item
(`STATEWIDE_EXPANSION_PLAYBOOK.md` §7 Phase 0/1 status), sequenced with, not inside, this
pass.

## 6. Recorded candidates (mirrored into the guidebook backlog)

1. Chicago citywide officers (Mayor/Clerk/Treasurer) on the `municipality` card — §4.1.
2. Election-authority dispatch for precinct/early-voting concepts; collar-clerk early-voting
   tranche — §4.2.
3. Commission-county / at-large county boards → `county` card rows, no polygon — §4.3.
4. `school-district-*` card enrichment (at-large boards; ISBE directory) — §4.4.
5. Township officers via the municipal clerk-yearbook scrapes (capture at build time;
   verify depth) — §4.5.
6. Countywide elected officers beyond the clerk (per-county, rule 4) — §4.5.
7. Law-enforcement row on `municipality` (+ Sheriff among county officers) — §4.6.
8. `mwrd` → `sanitary-district` concept conversion trigger (second-county tiling) — §4.8.
9. Appellate District row on `il-supreme-court`; ROE regional superintendent
   (DERIVE-class, verify carve-outs) — §4.9.
10. Statewide sources for `school-site` / `library` points — §4.10.

## 7. The expansion checklists

### 7.1 When county N+1 ships (all of this in one change-set, per rules 4–5)

1. Coverage outline (TIGER county boundary → pre-built outline file).
2. `county-board`: districted → dispatch entry + officeholder story; **at-large → county-card
   roster rows** (§4.3). Decide which, record which.
3. `judicial-subcircuit`: entry if the county's circuit has subcircuits under PA 102-0693;
   structurally n/a otherwise (Kendall precedent — record it).
4. `fire-district` / `park-district` / `library-district`: entries per available tilings;
   municipal rows per the §4.7 complete-tiling rule; gaps recorded (McHenry-park precedent).
5. `county-precinct`: entry keyed to the county's election authority; polling-place join
   where published; carve out any municipal election commission the county contains (§4.2).
6. `tif-district` (post-conversion): entry where the county publishes a tiling.
7. Municipal officials: the county's rung on the five-rung ladder
   (`MUNICIPAL_COUNCILS_PLAYBOOK.md`), keyed by place GEOID; township sections captured in
   the same scrape where the source prints them (§4.5).
8. County officers: clerk row is automatic (ISBE, statewide); further officers per rule 4.
9. Statewide layers (`county`, `township`, `municipality`, `school-district-*`, chambers,
   `zip-code`): **nothing to do** — they already resolve there.
10. Gates: worksheet entries + `generate_metro_files.py`, `validate_index.py`,
    `validate_sources.py` manifest rows, guidebook coverage-map/inventory/matrix update,
    smoke-test ground truth if the county adds an anchor.

**Layer-count check: unchanged.** If a step wants a new toggle, it must name the governance
function no existing concept covers — then it launches consolidated (rule 2b).

### 7.2 When a new concept is proposed (any county, any time)

1. Which level + function (§1.1–1.2)? If it duplicates an existing concept at the same level,
   it is an entry or a card row on that concept, full stop.
2. Which election geometry (§1.3)? Districted → consolidated concept layer. At-large →
   identity-card rows. Appointed → labeled links. Party office → out of scope.
3. Which dispatch dimension (§1.4) — county, place GEOID, election authority, or none?
4. Officeholder story in the same change (rule 4), honesty floor = link, gap recorded.
5. Guidebook row + this doc's audit table updated in the same change.

## 8. Cross-references

- `docs/COUNTY_LAYER_CONSOLIDATION.md` — the dispatcher mechanics; rules 2b/4/5 this doc
  builds its checklists on.
- `docs/MUNICIPAL_COUNCILS_PLAYBOOK.md` — the municipal Pattern A build + five-rung ladder;
  Tier B suburban wards.
- `docs/STATEWIDE_EXPANSION_PLAYBOOK.md` — FREE/DERIVE/PER-COUNTY source classes; the
  relevance-hiding capability; the rebrand-pass shell items.
- `docs/DATA_LAYER_GUIDEBOOK.md` — fleet inventory + the backlog holding §6's candidates.
- `docs/METRO_EXPANSION_PLAYBOOK.md` §3 step 4 — the at-large rule's fleet origin.

# ASK_DRAFTS.md — outbound asks, drafted and awaiting a send

`docs/EXPANSION_GUIDE.md`: *"The ask is a route, not a last resort… Draft asks in
batches, send them, and **record the send date**; a silent ask is not a closed one."*
Until now the drafts themselves lived in the operator's mail client and only their
*existence* was recorded, in gap records reading `NOT YET ASKED — DRAFTED`. That made
the wording unreviewable and the batch uncountable. This file is the drafts.

## How this file is used

1. **The operator sends. Nothing here is sent automatically, and no draft is sent by
   the agent that wrote it.** An e-mail to a named public official is outward-facing and
   irreversible; it goes when a person decides it goes.
2. **Record the send date the day it goes, never before** — in the relevant gap record
   in `docs/DATA_LAYER_GUIDEBOOK.md`, changing `NOT YET ASKED — DRAFTED` to
   `ASKED <date>`. This is the Scott rule, and it exists because two ask ledgers in this
   repo once said "held" about e-mails that had already been sent.
3. **Follow up at ~3 weeks, again 2 weeks later, and only then record the route
   UNRESPONSIVE** — which is a different claim from "no source exists". A follow-up is a
   **recovery mechanism, not a nudge**: one county Clerk answered the question that
   unblocked a whole build only on the third attempt, because her spam folder ate the
   first two.
4. **A clean, citable NO is a good outcome.** It closes a question for good and is worth
   as much as a yes. Say so in the ask, so declining is easy.
5. Replace `<YOUR NAME>` / `<YOUR E-MAIL>` with the sender's own. They are deliberately
   not written into this file, which is public.

## What is NOT here, and why

**The Iowa county-officer tranche is withdrawn, not held.** Fifteen counties were drafted
and filled (19 questions across them) and **none was ever sent**. They are gone from this
file because the operator is reviewing Iowa's county sites **by hand**, the exercise that
worked for Wisconsin — and a hand review reaches precisely the pages that stopped the
probe. Six of the fifteen were blocked by a site that **refuses this client** or sits
**behind a challenge**, which is an access control this project does not route around and
a person opening the page in a browser closes for free. Sending the batch first would ask
fifteen county auditors for details the review is about to read off their own sites.

**The treasurer-address batch is not here because the route was built.** An earlier edition
of this section held a 48-county ask pending `iowatreasurers.org`, calling that route
"unbuilt". It was built on 2026-08-29 and it works, with two gates the sweep proved
necessary: the site serves **another county's complete, plausible page with no error and no
404** for eleven of its ninety-nine ids, so the page must identify as the county AND the
address's domain must fit it; and no NAME is ever read from it. Between that and the
counties' own sites, 346 officer e-mail addresses ship. The residue — 34 treasurers and 11
sheriffs — is the manual review's, not an ask's.

**What stays here is institutional.** Asks 3, 4 and 5 go to a state agency, not a county:
none is a question a county-site review can answer, and each is a single question with a
citable yes or no at the end of it.

---

## Ask 1 — Iowa county officers — **WITHDRAWN 2026-09-03, never sent**

Drafted 2026-08-29 as a template plus fifteen filled per-county e-mails: one to each
county auditor, asking for a single missing officer e-mail address or for which of two
published names currently holds an office. **It was never sent, and the ledger says so
rather than forgetting it existed** — a withdrawn ask and an unanswered one are different
claims, and only one of them means a source refused.

Withdrawn because the operator is reviewing Iowa's county sites by hand (see *What is NOT
here* above). The questions themselves are unchanged and are recorded where a person
doing that review will meet them: the per-county reasons in
`ia/scripts/.cache/ia_county_officer_emails.json` (site published none readable / refuses
this client / sits behind a challenge), and the five counties where two directories name
different people and the card therefore names **neither** — Davis (sheriff), Henry and
Keokuk (county attorney), Humboldt and Jasper (recorder).

**If the review does not close them, redraft from what it measured** rather than restoring
this text: a page that has been read by a person is a different starting point from one
that was only probed.

---

## Ask 2 — White County, Illinois: the one clerk address in 102 without one

`il-county-clerks.json` carries a name, address and phone for all 101 counties and an
e-mail for 100. White County (Clerk Kayci Heil) is the single gap.

> **Subject:** An e-mail address for the White County Clerk's office
>
> Dear Clerk Heil,
>
> I run districtry (https://districtry.com/il/), a free, non-commercial site that shows
> Illinoisans which civic districts cover any point in the state and who represents them
> there. It lists every Illinois county clerk's office, and White County's entry is the
> only one of 101 with no e-mail address — I have your office's name, address and phone
> from the published county-clerk directory, but no address to go with them.
>
> If your office has an address it is content to have listed publicly, a one-line reply
> is all I need. If you would rather it not be listed, please just say so and I will
> record that and stop asking.
>
> I never publish home addresses or personal contact details of any kind.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

---

## Ask 3 — Iowa HSEMD: statewide NG911 service boundaries

Iowa's Homeland Security & Emergency Management Department runs a 911 program that
requires counties to submit PSAP / Fire / Law / EMS service boundaries to a state GIS
standard. No open statewide aggregate was found on the state's ArcGIS organization in the
research pass — only county-local layers (Linn, Scott). Wisconsin's equivalent layer is
shipped; Iowa's is the fleet's largest missing safety fabric.

> **Subject:** Are Iowa's NG911 service boundaries available as a statewide layer?
>
> Dear HSEMD 911 Program,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows
> Iowans which civic districts cover any point in the state. It already carries the
> state's precincts, supervisor districts, school districts and judicial districts from
> the Legislature's and the Department of Education's own published services.
>
> I understand the NG911 program has counties submit PSAP, Law, Fire and EMS service
> boundaries to a state standard. I could not find a statewide aggregate of those
> published openly — only county-local layers such as Linn's and Scott's. Is there a
> statewide layer available for public reuse, and if so where?
>
> If it exists but is not public, or is public under terms that would not permit
> redistribution, that is a completely acceptable answer — I would simply record it and
> not use the data. I would rather know than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

---

## Ask 4 — Iowa Secretary of State: a current polling-place edition

The state's published `IowaPollingPlaces` item is a 2024-08 vintage. A per-election
current edition is what a polling-place layer would need before it could ship under the
fleet's display contract (the election named, provisional wording before certification).

> **Subject:** Is there a current edition of the statewide polling-place file?
>
> Dear Elections Division,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows
> Iowans which civic districts cover any point in the state. It already carries Iowa's
> precincts from the Legislature's own published service.
>
> The statewide polling-place dataset I can find is stamped August 2024. Is a current
> per-election edition published anywhere, or is the 2024 file the most recent one
> intended for public use?
>
> If polling places are only authoritative on the county's own notice and a statewide
> file should not be relied on for a given election, please tell me that — it is the kind
> of caveat I would want to put on the page, and it would stop me shipping something
> misleading.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

---

## Ask 5 — Iowa Department of Education: the `CommColleges2020` licence

`CommColleges2020` carries `licenseInfo: "internal use only"`. **No geometry from it is
redistributed** — `build_ia_community_colleges.py` reads three aggregate columns
(`CCname`, `NumberofDirectorDistricts`, `SUM_TotalPop20`) at build time purely to gate
its own output against a second witness. That is defensible and it is exactly the kind of
thing this project resolves rather than assumes.

> **Subject:** Reading three columns from CommColleges2020 as a build-time check
>
> Dear GIS team,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows
> Iowans which civic districts cover any point in the state. It ships Iowa's 15 community
> college merged areas, using the geometry from your published `CC_2026update` service
> and the director districts from `CC_DirectorDistricts_FINAL`.
>
> To check that build against a second source, my script reads three aggregate values —
> college name, number of director districts, and 2020 population — from
> `CommColleges2020`, whose item is marked "internal use only". No geometry or row-level
> data from that layer is copied, stored or published; the values are compared and
> discarded, and the build refuses to write if they disagree.
>
> I would like to know whether that use is acceptable to you. If it is not, I will drop
> that check and find another witness — please just say so.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

---

## Ask 6 — Jo Daviess County, Illinois: display permission under the site's new domain

> **SENT 2026-08-29.** Replied on the original thread (*"County board district boundaries —
> public release, or a digital data order?"*) to **jkratcha@**, cc **dlascala@**, **gis@**
> and **akaiser@** — the operator kept the County Administrator on, so the "and the
> county" half went with it. Awaiting a reply.
>
> **Follow up 2026-09-19**, and again **2026-10-03**, before recording the route unresponsive —
> which would be a claim about this ask, never about the permission. The existing
> authorization was given for this site and has not been withdrawn, so the display
> continues meanwhile.

**This is the only ask in this file that is not about getting data.** The data is already
here, lawfully: `il/data/app/jo-daviess-county-board-districts.json` is built from the
county's own board-district shapefile, purchased 2026-08-17 under Jo Daviess County GIS
Digital Data License Agreement **#008382** ($33.50, invoice 008382), and displayed under
a separate written authorization from IT/GIS Director **Joe Kratcha** the same day. That
authorization is what makes the file publishable, and it names one thing:

> "…granting you permission to display the requested Jo Daviess County Board District
> boundaries to be provided in shapefile format on your website: **chidistricts.com** for
> public viewing." — e-mail of 2026-08-17 13:49Z

**The site has since been renamed.** chidistricts.com is now districtry.com; the old
domain 301-redirects to the new one and it is the same site, same operator, same use.
Nothing about the display changed — but the permission names a domain, and the honest
reading is that a permission naming a domain says what it says. `LICENSE-DATA.md` records
exactly that and excludes this one file from the project's ODbL grant, so nothing sweeps
the county's data into an open licence. **This ask closes that gap** — and on the day it
was sent, `LICENSE-DATA.md` stopped saying the permission "has not been re-sought" and
started naming the date it was, because a published legal statement that is a day stale is
the kind of inaccuracy this project treats as a bug.

Nothing is blocked on the answer and the county is not being asked to reconsider anything
it already decided — which is worth saying plainly in the mail, because an office that
reads this as "re-litigate the licence" is more likely to say nothing at all than to say
no.

### Recipients

| WRITE TO                                   | WHO                                            | WHY THIS ADDRESS                                                                     |
|--------------------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------|
| `jkratcha@jodaviesscountyil.gov`           | Joe Kratcha, IT/GIS Director                     | He wrote the 2026-08-17 authorization, so he is the person who can say whether it travelled. The county directory still lists him in post. |
| `dlascala@jodaviesscountyil.gov` (cc)      | Diane LaScala, GIS                               | Quoted, invoiced and delivered the shapefile; closed the original thread. |
| `gis@jodaviesscountyil.gov` (cc)           | GIS/IT department mailbox                        | The address the original ask went to, and the one the county publishes. Keeps the request in the office record rather than one inbox. |
| `akaiser@jodaviesscountyil.gov` (cc)       | Angela Kaiser, County Administrator               | The "and the county" half: a licence amendment is an administrative record, not only a GIS one. **Optional** — she was never on this thread, and adding an administrator to a routine confirmation can make it read as an escalation, which is the failure mode this ask is written to avoid. Drop her if a quiet yes is likelier without her. |

**The original 2026-08-17 thread exists and a reply on it is the route** — subject
*"County board district boundaries — public release, or a digital data order?"*, eleven
messages, ending 2026-08-17 18:43Z. Replying there carries the licence number, the
delivery and Kratcha's own wording as context, which is worth more than any restatement
below. The thread also supplies the personal addresses the county's public directory does
not: **jkratcha@jodaviesscountyil.gov** (Kratcha) and **dlascala@jodaviesscountyil.gov**
(Diane LaScala, who quoted, invoiced and delivered the files, and who closed the thread).

CORRECTION, 2026-08-29. An earlier version of this section said LaScala was "no longer
listed in the county directory" and warned against addressing her by name. **That was an
inference from an absence, and it was wrong.** The county's public directory lists 41
addresses and carries neither `dlascala@` nor `jkratcha@` — it publishes office mailboxes
and department heads, not GIS staff — so it is not evidence about anybody's employment,
and the thread shows her active in the role twelve days before that claim was written.
A directory that does not list someone has not said they left.

> **Subject:** Jo Daviess board districts — same site, new domain (licence #008382)
>
> Dear Joe Kratcha,
>
> Last August your office sold me a copy of the county's board-district shapefile under
> Digital Data License Agreement #008382, and you kindly followed it with written
> authorization to display those boundaries on my website, chidistricts.com, for public
> viewing. I have honoured both: the shapefile itself has never been republished or
> passed on, the site shows only a simplified display copy, and Jo Daviess County GIS is
> credited by name on the card every time a visitor lands in one of your districts.
>
> I am writing about one small thing. **The site has been renamed.** chidistricts.com is
> now **districtry.com** — the same site, run by the same person, doing the same thing;
> the old address redirects to the new one. Your authorization names chidistricts.com
> specifically, so rather than quietly assume it carries over, I would like to ask you to
> confirm it.
>
> **A one-line reply saying the 2026-08-17 authorization applies to districtry.com is all
> I need.** If your office would prefer to issue a fresh authorization naming the new
> domain, or to have me complete a form, I am glad to do whichever is easier for you.
>
> Nothing has changed about the use itself, and to be explicit about what it is and is
> not:
>
> - The boundaries are shown on a free public map. Nothing is sold, there is no
>   advertising, and there is no charge to anyone for anything.
> - **The shapefile is not redistributed.** It has never been committed to the project's
>   public code repository and is not downloadable from the site — only a simplified
>   version for on-screen display, as your authorization contemplates.
> - The county is credited as the source wherever those boundaries appear.
> - The project as a whole was recently given an open licence, and I specifically
>   **excluded** your county's data from it, so that nothing there can be read as
>   re-licensing material that belongs to Jo Daviess County. That exclusion names licence
>   #008382 and your authorization directly.
>
> If your office would rather the boundaries came down, please just say so and I will
> remove them — the page will point readers to the county's own board page instead. I
> would much rather have a clear no on record than leave an unanswered question sitting
> under a live map.
>
> Thank you again for the help last summer; it made Jo Daviess one of the few counties in
> this part of the state whose actual board districts a resident can look up.
>
> With thanks,
> <YOUR NAME>
> <YOUR E-MAIL>

### On a yes, or a no

* **Yes** → record the date and the wording in `docs/DATA_LAYER_GUIDEBOOK.md`'s Jo Daviess
  entry, and update every place that records the domain gap: the §3 note in
  `LICENSE-DATA.md`; the `license` string in the payload
  `scripts/build_jodaviess_board_districts.py` writes (the data file re-ships only when
  the operator re-runs the builder against the offline shapefile — never hand-edit the
  JSON); the data-file note in `metro-worksheet.json`, which regenerates the note in
  `scripts/validate_index.py` (run `python3 scripts/generate_metro_files.py`); the
  hand-kept manifest note in `scripts/validate_sources.py`; and the card's fixed credit
  literal in `il/index.html` if the wording changes. (Corrected 2026-09-02: this bullet
  used to name `SOURCE_LABEL` as the string that reaches the card; the card renders a
  fixed literal and reads nothing from the file, and the 2026-08-31 yes was written to
  the `license` string, not to `SOURCE_LABEL`.)
* **No, or take it down** → the file comes out of `il/data/app/`, the dispatch entry goes,
  and the gap record `jo-daviess-county-board-districts` reopens citing the withdrawal.
  That is a real outcome and the ask should not pretend otherwise.
* **Silence** → follow up at ~3 weeks and again 2 weeks later, per this file's cadence,
  before recording the route unresponsive. The display continues meanwhile: the existing
  authorization was given for this site and has not been withdrawn.

---

## Ask 7 — Wisconsin Legislative Reference Bureau: the Blue Book's reuse terms

**This ask is about a source already in production, which is why it is worth sending.**
`wi-county-officers.json` — 72 counties x 7 offices — and `wi-county-clerks.json` are
built weekly from the *Wisconsin Blue Book*'s own county-officer tables, fetched from
`docs.legis.wisconsin.gov/misc/lrb/blue_book/2025_2026/210_officials_and_employees.pdf`.
The Blue Book's front matter reads **"(c)2025 Joint Committee on Legislative
Organization, Wisconsin Legislature. All rights reserved."**, and the volume is sold
through the Legislature's Document Sales Unit.

Measured 2026-09-02, and this is the reason for the ask: **there is no recorded
reasoning anywhere in this repo for why that notice does not apply.** Zero mentions of
copyright, licence or attribution in `wi_county_clerk_scraper.py`,
`build_wi_county_clerk_roster.py` or `build_wi_county_officer_roster.py`; nothing in
`LICENSE-DATA.md`; and the worksheet's own source block calls it "a state publication",
which is an assumption rather than a finding. Under this project's own rules an "All
rights reserved" string is not automatically a refusal — it was the text of a REQUIRED
NOTICE for Des Moines's ward layer and a real block for Piatt County's GIS — so it has to
be established, not inferred. It has been shipping unestablished.

A second reason to ask now: section `190_population_and_political_divisions` carries
per-municipality data this project would use if the terms allow — year of incorporation
for every city and village, each municipality's county (multi-county memberships
included), county seats, and the Department of Administration's own current population
estimates. None of it is shipped today.

**Recipient:** `lrb-reference-services@legis.wisconsin.gov`, the Bureau's published
reference desk and the Blue Book's own service address. `lrb.legal@legis.wisconsin.gov`
is also published; it is deliberately NOT cc'd, because cc-ing legal staff who were
never on the thread reads as an escalation — the draft instead invites the Bureau to
route it there itself.

> **Subject:** Reuse terms for Blue Book reference tables
>
> Dear Reference Services,
>
> I run districtry (https://districtry.com/wi/), a free, non-commercial site that shows
> Wisconsinites which civic districts cover any point in the state and who represents
> them there.
>
> The site currently names each county's clerk, board chair, executive, sheriff,
> district attorney, treasurer, clerk of circuit court, coroner and register of deeds.
> Those names come from the 2025-2026 Blue Book's county-officer tables, refreshed
> weekly and shown with the date of the Blue Book's own April 2025 snapshot and a link
> back to the Bureau. Only the officeholder facts are used; no part of the volume is
> republished, and the PDF is not redistributed.
>
> I want to be sure that use is acceptable to you, and to ask about one extension. The
> Blue Book's population and political subdivisions section carries the year each city
> and village was incorporated, which counties each municipality lies in, and the county
> seats. I would like to show those on the corresponding cards, credited to the Blue
> Book in the same way.
>
> I am asking because the volume's front matter reserves all rights, and I would rather
> have your answer than my assumption. If either use needs a different form of credit,
> or a licence, or if the answer is simply no, please just tell me — a clear no is a
> genuinely useful answer, and I will record it and act on it.
>
> If this is really a question for the Bureau's legal staff, I am happy to be redirected
> rather than have you forward it.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### What each answer means

* **Yes, both** → record `ANSWERED <date>` with the wording, note the credit form the
  Bureau asks for, and the section `190` fields become a build (the county card gains a
  county seat, the municipality card a year of incorporation).
* **Yes to what ships, no to the extension** → the existing use is settled and written
  down for the first time; the extension closes for good.
* **No** → this is a real outcome and the ask must not pretend otherwise: the county
  officers and clerks are the Blue Book's, so a no means finding another source for
  them or dropping them, and the county card's officer rows come out. Both roster files
  and the weekly workflow would be affected.
* **Silence** → follow up at ~3 weeks and again 2 weeks later, per this file's cadence,
  before recording the route unresponsive. The existing display continues meanwhile;
  nothing has been withdrawn.

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

> **SENT 2026-08-29 — ANSWERED YES 2026-08-31. THIS ASK IS CLOSED.** Replied on the
> original thread (*"County board district boundaries — public release, or a digital data
> order?"*) to **jkratcha@**, cc **dlascala@**, **gis@** and **akaiser@** — the operator
> kept the County Administrator on, so the "and the county" half went with it.
>
> The IT/GIS Director answered two days later: *"I confirm you are authorized to use the
> Jo Daviess County Board district shapefiles provided under GIS Digital Data License
> Agreement #008328 on the new districtry.com website as noted below in your email."*
> The permission now names the domain the site actually uses. It is quoted in full, with
> the #008328/#008382 digit transposition explained rather than tidied away, in
> `LICENSE-DATA.md` §3 — **that file, not this one, is the record.** No follow-up is due;
> the 2026-09-19 and 2026-10-03 dates this block used to carry are retired.

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

> **SENT 2026-09-03.** Sent by the operator from his own mailbox to
> **lrb-reference-services@legis.wisconsin.gov**, the Bureau's published reference desk.
>
> **Follow up 2026-09-24**, and again **2026-10-08**, before recording the route
> unresponsive — which would be a claim about this ask, never about the terms. Silence is
> not permission any more than it is a refusal.
>
> **WHAT IT GATES IS NARROW.** Only the two builds already shipping off the Blue Book
> (`wi-county-officers.json`, `wi-county-clerks.json`) and whether section 190's
> county-seat and incorporation-year tables can be added. Nothing else in Wisconsin waits
> on it, and the existing use continues meanwhile — the ask exists because no reasoning
> for it was ever recorded, not because a problem was found.

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

---

## Ask 8 — Iowa Secretary of State: a statewide list of city clerks

**This is the ask Iowa never made, and Wisconsin's whole municipal tier rests on its
counterpart.** Wisconsin ships a clerk for all 608 of its cities and villages because ONE
publisher — the Wisconsin Elections Commission — holds all 1,848 municipalities in one file,
and it arrived in reply to a single e-mail, answered in 22 minutes. Iowa's structural
counterpart is the Secretary of State: city elections run under Iowa Code ch. 376 through the
county commissioners of elections, so a list of who to contact in each city has to exist
somewhere in that chain.

Measured first, 2026-09-03, so the ask is not for something already published: `sos.iowa.gov`
answers 200 to a browser request, and neither its **Schools & Cities** page (which explains
city and school elections to voters) nor its **Research & Data** page links a clerk directory
or any document of that kind. The Iowa League of Cities publishes every city's phone and
website and names no person. No county publishes its cities' officials as map data.

*Practical note for sending — CORRECTED 2026-09-04, and the correction is the useful part.*
This section previously read that the contact page "publishes a form and three phone numbers rather
than an e-mail address, so this may need to go through the form." **It publishes an address, and the
Elections Division has its own:** `elections@sos.iowa.gov`, alongside `sos@sos.iowa.gov` and
`business.services@sos.iowa.gov`. They were missed because they are **Cloudflare-obfuscated** —
rendered as `[email protected]` with the real value in a `data-cfemail` attribute — which is the same
trick `ia/scripts/ia_county_auditor_scraper.py` already decodes for the county auditors' addresses.
A plain read of the page finds no address; a decode finds three. The site had also been rebuilt since
the ask was written: the recorded `/about/contact.html` and `/elections/index.html` paths now answer
404, and the live page is `/contact-us`.

**DRAFTED IN THE OPERATOR'S MAILBOX 2026-09-04**, addressed to `elections@sos.iowa.gov`. Not sent —
rule 1 stands, and the ledger stays `NOT YET ASKED — DRAFTED` until the day it goes.

> **Subject:** Is there a statewide list of Iowa city clerks?
>
> Dear Elections Division,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows
> Iowans which civic districts cover any point in the state and who represents them there.
> It already carries Iowa's precincts, supervisor districts, school districts, community
> colleges and judicial districts from the Legislature's and the Department of Education's
> own published services, and all six elected county offices in all 99 counties.
>
> The one level it cannot answer for is the city. It knows all 939 of Iowa's incorporated
> places and carries an office phone and website for each, from the Iowa League of Cities'
> own directory — but outside Des Moines and Waterloo, which publish their council members
> themselves, it cannot name a single mayor, council member or clerk, because I can find no
> statewide source. Is there a list of Iowa's city clerks — names and
> office contact details — held anywhere in your office or by the county commissioners of
> elections, in any form you would be willing to share? A spreadsheet or a PDF is perfectly
> usable; it does not need to be a published dataset.
>
> If no such list exists, or exists but is not something you can share, that is a completely
> acceptable answer — I would record it and stop looking, and the site would keep pointing
> readers at the city's own website instead. I would rather know than guess, and I never
> publish a name I cannot source.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### What each answer means

* **A list arrives** — Iowa's City card can name a clerk in every city that has one, the way
  Wisconsin's does, and the `ia-municipal-officeholders` gap record closes.
* **"We do not hold that"** — a clean, citable no. The gap record's blocker gains a fourth
  measured route and the remaining ones are the per-city ladder and the per-city GIS route
  (Des Moines and Waterloo both already publish their council members in band), plus the
  sixteen cities of 939 whose own pages a sweep found machine-readable on 2026-09-04.
* **"The county auditors would have it"** — that is a pointer, and a good one: it turns 99
  asks into a route this project already has the addresses for, since all 99 auditors ship in
  `ia/data/app/ia-county-auditors.json` with an e-mail apiece.

---

# Illinois — the asks that were drafted and never written down (added 2026-09-03)

This file's own opening says why this section exists: *"Until now the drafts themselves
lived in the operator's mail client and only their existence was recorded, in gap records
reading `NOT YET ASKED — DRAFTED`. That made the wording unreviewable and the batch
uncountable."* That is still true of four Illinois asks. Their gap records say a reply is
drafted; no draft exists anywhere a person can read. They are written out below.

**Addresses come from `data/app/il-county-clerks.json`**, refreshed weekly from ISBE and
re-run 2026-09-03, rather than from a list copied into this document.

**One correction that predates these drafts.** Fayette County's clerk changed while the
clerk refresh was frozen: the shipped card named Jessica Barker for eleven days after the
county swore in **Kara Dugan** (`kdugan@fayettecountyillinois.gov`). Any Illinois ask
addressed to Barker is addressed to someone who has left. Fayette has no open ask today,
but the same freeze covered every county, so check a recipient against the current roster
before sending rather than against a draft written in August.

**And one to verify before sending.** The Christian County gap record names the clerk
"Kandi Badman"; the ISBE roster names **Jodie Badman**. The roster is the fresher source
and is used below, but confirm the name before the envelope goes out — getting a public
official's name wrong is the cheapest possible way to lose a reader.

---

## Ask 9 — Bureau County: permission the licence does not grant, or the free route instead

> **NOT YET ASKED — DRAFTED.** GIS Technician Christine Anderson sent a signed-user
> agreement and a $150 invoice on **2026-08-12**; nothing has been sent back since, so this
> has been sitting for three weeks. The operator read both PDFs on 13 Aug: the invoice is
> honest cost recovery, and the agreement's *Protection of Proprietary Rights* clause
> forbids redistribution of the data "or products derived therefrom outside of licensee's
> organization" — which is exactly what a public `bureau-county-board-districts.json` is.
> Signing as written is off the table at any price. The clause's own tail ("without
> permission from Bureau County GIS") is a valve, and this asks for it.
>
> **Do not pay the invoice before the answer arrives.** The money is not the obstacle and
> paying first would buy a file this project could not then publish.

**To:** Christine Anderson, GIS Technician, Bureau County Assessor's Office —
`canderson@bureaucounty-il.gov`
**Cc:** `ccao@bureaucounty-il.gov`, and County Clerk Matthew Eggers
`countyclerk@bureaucounty-il.gov` (who opened the thread)
**Subject:** Re: Request: 2021 county board redistricting plan — one question about the licence

> Dear Ms. Anderson,
>
> Thank you for the user agreement and the invoice — and for finding the shapefile in the
> first place. I want to be straightforward about one clause before I sign anything,
> because I think the agreement was written for a different kind of user than me.
>
> I run districtry (https://districtry.com/il/), a free, non-commercial site that shows
> Illinois residents which civic districts contain any point they click, and who
> represents them there. It is not a data product and nothing on it is sold. But it does
> work by publishing simplified boundary outlines to each visitor's browser, and the
> agreement's Protection of Proprietary Rights clause forbids redistribution of the
> datasets "or products derived therefrom outside of licensee's organization". A public
> map of Bureau County's board districts is precisely such a derived product, so I cannot
> sign the agreement as written and then do the one thing I need the file for.
>
> The clause says "without permission from Bureau County GIS", so my question is simply
> whether the county is willing to give that permission for this use. Concretely, I would
> like to publish a simplified outline of the eighteen board districts, credited to Bureau
> County GIS, with a note that the boundaries are simplified for display and that your
> office is authoritative. Every obligation the agreement otherwise imposes — crediting
> the source, describing modifications — this site already does on every card.
>
> If that is not something the county wants to grant, that is a complete answer and I will
> stop asking. In that case there is a second route that costs your office almost nothing
> and needs no licence at all: a plain list of which voting precincts (or census blocks)
> make up each of the eighteen districts. That is a public record rather than a GIS
> product, and several Illinois counties have answered exactly that way — I rebuild the
> boundaries myself from published census geography and the county's file never leaves
> your office.
>
> Either answer closes the question, and I would rather have a clear no than leave it
> open. Thank you for your time.
>
> <YOUR NAME>
> <YOUR E-MAIL> · https://districtry.com/il/

---

## Ask 10 — Clark County: direct contact for the board, and which building serves each precinct

> **NOT YET ASKED — DRAFTED**, two questions on one thread. Clerk Lee already answered this
> project once, in a single sentence that unblocked the whole county ("The County Board is
> elected by districts. I do not have maps available"), so she is a proven responder and
> the ask should be correspondingly short. Both gap records — `clark-board-contact` and
> `clark-precinct-polling` — get their ASKED date when this goes, never before.

**To:** Laura H. Lee, County Clerk & Recorder, Clark County — `clerk@clarkcounty.illinois.gov`
**Subject:** Two small follow-ups now that Clark County is on the map

> Dear Clerk Lee,
>
> Thank you again for your reply in August. Knowing the board is elected by districts let
> me build Clark County's twelve districts from your office's own certified canvasses, and
> the county has been live on districtry (https://districtry.com/il/) since then —
> a resident can click their address and see their board district, their member and their
> precinct.
>
> Two small things would finish it, and a one-line answer to either is plenty.
>
> First, the board members' cards currently show the courthouse switchboard, because that
> is the only number published. If the county has a direct phone number or e-mail for
> individual board members that it is content to see listed publicly, I would list it. If
> the switchboard genuinely is the route to a board member, that is a fine answer too and
> I will say so on the card instead of leaving it ambiguous.
>
> Second, the precinct cards name a resident's precinct but not where they vote. If your
> office has a list of polling places by precinct — a page, a PDF, a spreadsheet, anything
> already prepared — I would add it. I do not need anything made specially.
>
> No rush on either; both are improvements rather than corrections. Thank you.
>
> <YOUR NAME>
> <YOUR E-MAIL> · https://districtry.com/il/

---

## Ask 11 — CCGISC: the licence question behind two whole counties

> **NOT YET ASKED — DRAFTED.** Champaign and Piatt are the only two Illinois counties this
> project records as blocked for a LEGAL rather than a technical reason: the Champaign
> County GIS Consortium sells the data under terms that forbid copying, public display and
> rehosting, and Piatt additionally asserts "All Rights Reserved" over its GIS. Both
> clerks have been asked directly and neither route reached the data — this is the ask
> that goes to the party that can actually say yes.
>
> **The recipient is the one thing not settled here.** CCGISC's own current contact should
> be confirmed from ccgisc.org before sending; the clerks below are cc'd because both have
> corresponded with this project already and can vouch that the request is what it says.

**To:** the Champaign County GIS Consortium — *confirm the current address from ccgisc.org*
**Cc:** Aaron O. Ammons, Champaign County Clerk — `elections@champaigncountyclerkil.gov`;
Jennifer Harper, Piatt County Clerk — `countyclerk@piatt.gov`
**Subject:** Permission to display CCGISC county board and precinct boundaries on a free civic map

> Dear CCGISC,
>
> I run districtry (https://districtry.com/il/), a free, non-commercial site that lets an
> Illinois resident click their address and see every civic district that contains it and
> who represents them there. It covers 91 of Illinois's 102 counties. Champaign and Piatt
> are two of the eleven it cannot cover, and they are the only two held back by a licence
> rather than by missing data.
>
> Both counties' clerks have been helpful and both pointed here: the county board district
> and voting precinct boundaries are consortium data, and the terms I have seen permit
> personal, transitory viewing while prohibiting copying, public display and hosting on
> another server. I have not copied or republished anything, and I am not asking you to
> change your licence.
>
> What I am asking is narrower: permission to display a simplified outline of the county
> board districts and voting precincts of Champaign and Piatt counties on this site,
> credited to the Champaign County GIS Consortium, with a note that the boundaries are
> simplified for display and that CCGISC is authoritative. No parcel data, no attributes,
> no bulk download, and no redistribution of the consortium's files — the site publishes
> only the outline it draws.
>
> If the answer is no, that is genuinely useful and I will record it plainly: the two
> counties' cards will tell residents that the boundaries exist and are licensed, rather
> than implying nobody has them. If a narrower permission is easier to grant than the one
> I have described, I would rather have that than nothing.
>
> Thank you for considering it.
>
> <YOUR NAME>
> <YOUR E-MAIL> · https://districtry.com/il/

---

## Ask 12 — the four second follow-ups that are now due

> **This file's rule 3 is "follow up at ~3 weeks, again 2 weeks later, and only then record
> the route UNRESPONSIVE."** Four Illinois asks have had exactly ONE follow-up and are past
> the second interval. None of them may be called unresponsive yet, and the reason is
> written into that rule: a follow-up is a recovery mechanism, not a nudge — Clay County's
> clerk answered the question that unblocked a whole build only on the third attempt,
> because her spam folder had eaten the first two.
>
> Send these as replies on their existing threads, so the history travels with them.

| County | Recipient | Asked | 1st follow-up | Owed |
|---|---|---|---|---|
| Ford | Kelsie Vaughn, `clerk@fordcounty.illinois.gov` | 3 Aug | 16 Aug | 2nd follow-up |
| Christian | Jodie Badman, `elections@christiancountyil.com` | 5 Aug (+ the Taylorville 9 question 21 Aug) | 16 Aug | 2nd follow-up |
| Piatt | Jennifer Harper, `countyclerk@piatt.gov` | 3 Aug | 16 Aug | 2nd follow-up |
| Knox | Scott G. Erickson, `serickson@knoxcountyil.gov` | 5 Aug | 16 and 24 Aug | already two — record UNRESPONSIVE if this one is silent |

Each follow-up restates the ONE question and offers a no. The Ford one, as the shape:

> Dear Clerk Vaughn,
>
> I am following up once more on my notes of 3 and 16 August about Ford County's board
> districts — I know these land in a busy inbox, and I would rather ask again than assume
> an answer.
>
> There is only one thing I need, and either answer finishes it. The county's published
> district map is titled 2011 but was re-uploaded in November 2021, so I cannot tell which
> plan is currently in force. And Patton 3 appears under both District 1 and District 3,
> which reads as the precinct being split between them.
>
> If you can tell me which plan the county elects under today, and how Patton 3 divides, I
> can add Ford County to districtry (https://districtry.com/il/) — a free, non-commercial
> site that shows Illinois residents their districts and representatives. If the map is
> not something your office maintains, saying so is a complete answer and I will stop
> asking.
>
> Thank you for your time.
>
> <YOUR NAME>
> <YOUR E-MAIL> · https://districtry.com/il/

**Knox is the one to watch.** It has had two follow-ups already, so a third silence is the
point at which `knox-precinct-geometry` records the ROUTE as unresponsive — a claim about
this ask, never about the county. Note also that Knox's own board-members page turned out
to be readable after all (2026-09-03), so the county is less dark than its record implied;
the precinct question is the part still genuinely open.

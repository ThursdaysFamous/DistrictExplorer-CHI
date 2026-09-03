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

**Do not send a treasurer-address ask yet — 48 counties' worth.** A source that may close
most of it is unbuilt: `iowatreasurers.org` publishes a per-county treasurer page at
`index.php?module=treashome&idCounty=<N>` carrying e-mail addresses, and this project's
own record calls that site "a payment portal that names nobody", which is **wrong**. It is
not a quick win either, and both reasons are measured:

* **Its key is unreliable.** `idCounty=51` and `idCounty=77` return the *same* county
  (byte-identical Jefferson County addresses), so the id is not a 1..99 alphabetical
  index and nothing may be keyed on it until that is understood.
* **It disagrees with ISAC about who the treasurer is.** `idCounty=1` (Adair) names
  *Marilee Kerber*; the shipped roster, from ISAC, names *Brenda Wallace*. That is a
  divergence to resolve, not a tiebreak to guess.

Asking 48 counties for an address that turns out to be published would spend the
operator's credibility with county offices on a question they can already answer by
sending a link. Build or rule out that route first; whatever it cannot close becomes a
batch here, using the same template as Ask 1.

---

## Ask 1 — Iowa county officers: one missing address or name

**15 recipients** (below). Each county gets **one** e-mail even where two things are
missing. The recipient is the county **auditor**, whose address this project holds for
all 99 counties and who is the county's own records and elections officer (Iowa Code
§47.2) — not a guessed `treasurer@` or `sheriff@` address, which is precisely what the
honesty rules forbid inventing.

Every one of these was probed first: the county's own site was read for a published
address, and an address shipped only where the officeholder's own name vouched for it or
its form made it an office mailbox. **A page window is not a witness** — the first draft
of that probe returned a *deputy's* personal address in 4 of 7 counties.

> **Subject:** A missing contact detail for <COUNTY> County
>
> Dear <AUDITOR NAME>,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows
> Iowans which civic districts cover any point in the state and who represents them
> there. It already lists <COUNTY> County's auditor, treasurer, recorder, sheriff,
> county attorney and board of supervisors, from your county's own site, the Iowa State
> Association of Counties' directory and the state associations' published rosters.
>
> One thing I could not find published anywhere is **<THE MISSING THING>**. If there is
> an address your office is content to have listed publicly, a one-line reply is all I
> need.
>
> If you would rather it not be listed, please just say so — I will record that and stop
> asking, and the card will keep pointing readers to the county's own page instead. A no
> is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or
> personal contact details of any kind, and where a source is unclear about who holds an
> office I leave the name off rather than guess it.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Recipients

| COUNTY        | AUDITOR              | WRITE TO                         | ASKING FOR                                 | WHY NOT PUBLISHED                   |
|---------------|----------------------|----------------------------------|--------------------------------------------|-------------------------------------|
| Cass          | Kathy Somers         | auditor@casscoia.us              | sheriff's e-mail                           | site published none we could read   |
| Davis         | Kristi Goodson       | auditor@daviscountyiowa.org      | the name of the sheriff                    | two publishers disagree on the name |
| Hardin        | Jolene Pieters       | jpieters@hardincountyia.gov      | sheriff's e-mail                           | site refuses this client            |
| Henry         | Robin Detrick        | rdetrick@henrycountyiowa.us      | the name of the county attorney            | two publishers disagree on the name |
| Humboldt      | Trish Erickson       | terickson@humboldtcountyia.org   | sheriff's e-mail; the name of the recorder | site published none we could read   |
| Jasper        | Jenna Jennings       | jjennings@jaspercounty.iowa.gov  | the name of the recorder                   | two publishers disagree on the name |
| Johnson       | Julie Persons        | elections@johnsoncountyiowa.gov  | sheriff's e-mail                           | site published none we could read   |
| Keokuk        | Christy Bates        | auditor@keokukcountyia.com       | the name of the county attorney            | two publishers disagree on the name |
| Linn          | Todd Taylor          | todd.taylor@linncountyiowa.gov   | sheriff's e-mail                           | site published none we could read   |
| Mitchell      | Rachel Foster        | rfoster@mitchellcoia.us          | sheriff's e-mail                           | site published none we could read   |
| Osceola       | Rochelle Van Tilburg | rvantilburg@osceolacoia.org      | sheriff's e-mail                           | site sits behind a challenge        |
| Palo Alto     | Carmen Moser         | cmoser@paloaltocounty.iowa.gov   | sheriff's e-mail                           | site sits behind a challenge        |
| Pottawattamie | Mary Ann Hanusa      | elections@pottcounty-ia.gov      | sheriff's e-mail                           | site refuses this client            |
| Van Buren     | Lisa Plecker         | lplecker@vanburencounty.iowa.gov | sheriff's e-mail                           | site published none we could read   |
| Washington    | Tamera Stewart       | tstewart@co.washington.ia.us     | sheriff's e-mail                           | site published none we could read   |

Fill `<THE MISSING THING>` from the **Asking for** column, e.g. *"an e-mail address for
Sheriff <name>"* or *"which of two people currently holds the office of county
recorder — two published directories name different people"*. For the four counties
whose row reads *two publishers disagree on the name*, name both people and ask which is
correct; that is a smaller, easier question than an open one.

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

## Tranche 1 — the 15 county asks, filled and ready to send

Generated from the shipped rosters and the 2026-08-29 probe, so every name, number and reason below is the one the site actually holds. Fill `<YOUR NAME>` and `<YOUR E-MAIL>`, then send. **Record the send date in `ia/WATCH.md` the day it goes, not before.**

### Cass County — Kathy Somers <auditor@casscoia.us>

> **Subject:** An e-mail address for the Cass County Sheriff's Office
>
> Dear Kathy Somers,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Cass County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff John Westering.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Cass County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Davis County — Kristi Goodson <auditor@daviscountyiowa.org>

> **Subject:** Two directories name different people for Davis County
>
> Dear Kristi Goodson,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Davis County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **Which of two people is your sheriff.** The Iowa State Association of Counties' member directory names **Zachary Dunlavy**; the Sheriffs' own statewide directory names **Dave Davis**. Rather than pick one, I currently show no name at all for that office.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Hardin County — Jolene Pieters <jpieters@hardincountyia.gov>

> **Subject:** An e-mail address for the Hardin County Sheriff's Office
>
> Dear Jolene Pieters,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Hardin County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff David McDaniel.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Hardin County, and the county's website refuses automated requests, so I could not check it.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Henry County — Robin Detrick <rdetrick@henrycountyiowa.us>

> **Subject:** A couple of questions about Henry County's officer list
>
> Dear Robin Detrick,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Henry County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There are 2 things I could not establish from any of them:
>
> - **Which of two people is your county attorney.** The Iowa State Association of Counties' member directory names **Darin Stater**; the County Attorneys' own statewide directory names **Becky Wilson**. Rather than pick one, I currently show no name at all for that office.
> - **How many supervisors Henry County has, and who they are.** The directory I read lists 4. Iowa Code §331.201 provides for three or five, so rather than publish a board I am unsure of, the site currently shows none for Henry County.
>
> A short reply to any of these would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Humboldt County — Trish Erickson <terickson@humboldtcountyia.org>

> **Subject:** A couple of questions about Humboldt County's officer list
>
> Dear Trish Erickson,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Humboldt County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There are 3 things I could not establish from any of them:
>
> - **An e-mail address for Sheriff Dean Kruger.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Humboldt County, and I could not find one published on the county's website.
> - **Which of two people is your recorder.** The Iowa State Association of Counties' member directory names **Diane Amundson**; the Recorders' own statewide directory names **Nicole Niemeyer**. Rather than pick one, I currently show no name at all for that office.
> - **How many supervisors Humboldt County has, and who they are.** The directory I read lists 6. Iowa Code §331.201 provides for three or five, so rather than publish a board I am unsure of, the site currently shows none for Humboldt County.
>
> A short reply to any of these would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Jasper County — Jenna Jennings <jjennings@jaspercounty.iowa.gov>

> **Subject:** Two directories name different people for Jasper County
>
> Dear Jenna Jennings,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Jasper County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **Which of two people is your recorder.** The Iowa State Association of Counties' member directory names **Denise Allan**; the Recorders' own statewide directory names **Joseph Otto**. Rather than pick one, I currently show no name at all for that office.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Johnson County — Julie Persons <elections@johnsoncountyiowa.gov>

> **Subject:** An e-mail address for the Johnson County Sheriff's Office
>
> Dear Julie Persons,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Johnson County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Brad Kunkel.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Johnson County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Keokuk County — Christy Bates <auditor@keokukcountyia.com>

> **Subject:** A couple of questions about Keokuk County's officer list
>
> Dear Christy Bates,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Keokuk County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There are 2 things I could not establish from any of them:
>
> - **An e-mail address for Sheriff Casey Hinnah.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Keokuk County, and I could not find one published on the county's website.
> - **Which of two people is your county attorney.** The Iowa State Association of Counties' member directory names **Amber Thompson**; the County Attorneys' own statewide directory names **Maddison Denny**. Rather than pick one, I currently show no name at all for that office.
>
> A short reply to any of these would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Linn County — Todd Taylor <todd.taylor@linncountyiowa.gov>

> **Subject:** An e-mail address for the Linn County Sheriff's Office
>
> Dear Todd Taylor,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Linn County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Brian Gardner.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Linn County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Mitchell County — Rachel Foster <rfoster@mitchellcoia.us>

> **Subject:** An e-mail address for the Mitchell County Sheriff's Office
>
> Dear Rachel Foster,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Mitchell County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Gregory Beaver.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Mitchell County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Osceola County — Rochelle Van Tilburg <rvantilburg@osceolacoia.org>

> **Subject:** An e-mail address for the Osceola County Sheriff's Office
>
> Dear Rochelle Van Tilburg,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Osceola County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Kevin Wollmuth.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Osceola County, and the county's website sits behind a challenge page I do not try to work around.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Palo Alto County — Carmen Moser <cmoser@paloaltocounty.iowa.gov>

> **Subject:** An e-mail address for the Palo Alto County Sheriff's Office
>
> Dear Carmen Moser,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Palo Alto County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff John King.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Palo Alto County, and the county's website sits behind a challenge page I do not try to work around.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Pottawattamie County — Mary Ann Hanusa <elections@pottcounty-ia.gov>

> **Subject:** An e-mail address for the Pottawattamie County Sheriff's Office
>
> Dear Mary Ann Hanusa,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Pottawattamie County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Andy Brown.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Pottawattamie County, and the county's website refuses automated requests, so I could not check it.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Van Buren County — Lisa Plecker <lplecker@vanburencounty.iowa.gov>

> **Subject:** An e-mail address for the Van Buren County Sheriff's Office
>
> Dear Lisa Plecker,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Van Buren County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Brad Hudson.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Van Buren County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
>
> Thank you for your time,
> <YOUR NAME>
> <YOUR E-MAIL>

### Washington County — Tamera Stewart <tstewart@co.washington.ia.us>

> **Subject:** An e-mail address for the Washington County Sheriff's Office
>
> Dear Tamera Stewart,
>
> I run districtry (https://districtry.com/ia/), a free, non-commercial site that shows Iowans which civic districts cover any point in the state and who represents them there. For Washington County it names the county's elected officers from your county's own website, the Iowa State Association of Counties' member directory, and the state associations' published rosters.
>
> There is one thing I could not establish from any of them:
>
> - **An e-mail address for Sheriff Jared Schneider.** I have the name and a phone number, but the Iowa State Sheriffs' & Deputies' Association directory I read carries no address for Washington County, and I could not find one published on the county's website.
>
> A short reply on that would be a real help — and if you would rather any of it not be listed, please just say so.
> I will record that and stop asking, and the page will keep pointing readers to the county's own site instead. A no is genuinely a useful answer.
>
> Two things I do not do, in case they are a concern: I never publish home addresses or personal contact details of any kind, and where sources disagree about who holds an office I leave the name off rather than guess.
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

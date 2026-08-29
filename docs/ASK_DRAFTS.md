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

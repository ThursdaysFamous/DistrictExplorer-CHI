# Wisconsin Elections Commission — polling-place file (build input)

`Polling Place Listing (3).xlsx` is the file the Commission sent this project
directly. It is committed here because **there is no URL to fetch it from.**
The Commission's Jodi Vitcenda wrote, 2026-08-27 (help-desk ticket 123582):

> The list ... is posted on the elections.wi.gov/elections portion of the site
> ... I can't provide any direct links for the attachments at this time, as it
> isn't published there for November yet, but that is where it would be.

So the file is **provisional**: it is the Commission's working list for the
3 November 2026 General Election, months before the published edition. Every
card built from it says so in the reader's own sentence, and
`wi/scripts/build_wi_polling_places.py` carries the whole arrangement.

**Re-pull on 17 September 2026** (`wi/WATCH.md`): that is the statutory
deadline by which municipal clerks must have published their polling places
for the November election, and the Commission's own published file should
exist at `elections.wi.gov/elections` from about then. Replace this file,
rebuild, and clear the provisional flag.

## What is deliberately NOT here

The same reply attached `In-Person Absentee Voting Locations (1).xlsx`. It is
**not committed and not shipped**, for two measured reasons:

1. **It is not a statewide answer.** It carries 34 municipalities out of
   Wisconsin's 1,846 — 1.8% — and its own first line says so: "This list is
   not an exhaustive list, clerks are not required to share with the WEC the
   locations and times they offer In-Person Absentee Voting." A card built on
   it would tell a reader in Madison that Madison has no early voting.
2. **Two of the 34 entries are a clerk's private home** ("... Town Clerk's
   Home", "... Village Deputy Clerk's Home", both at the same residential
   address). The Commission may publish that; mirroring it into a public git
   repository indefinitely is a different act, and this project does not make
   it.

The measurement is recorded in `docs/DATA_LAYER_GUIDEBOOK.md` instead, which
is what a gap record is for.

## Privacy check on what IS here

The polling file's 3,623 rows carry no residential address. 141 rows are typed
`Private`, which means a privately **owned** building — senior centres, clubs,
museums, a Masonic centre — not a residence; the only row whose name even
contains "residence" is St. Camillus Independent Living West in Wauwatosa, a
public-access retirement community. Re-run that check on any replacement file.

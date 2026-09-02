---
name: outbound-ask
description: Draft, hold, send-record and close an outbound e-mail to a named public office — a county clerk, auditor, GIS desk or state agency — asking for one missing detail, a name tiebreak, a dataset, or a licence confirmation, and keep the ask's state (drafted, sent, followed up, answered, unresponsive) honest across the ledgers. Use it for "draft an ask for Ford County, nothing publishes the map", "the Jo Daviess reply came in, record the yes", "three weeks on the Iowa auditor tranche, write the follow-ups", "Pope still hasn't answered, mark it unresponsive", "I sent the tranche 1 e-mails today", "two directories disagree on District 4, ask the county which", "put NOT YET ASKED — DRAFTED on Christian's gap record", "is Bureau worth an ask or is it measured shut". Nothing here is ever sent by the agent. Not for probing a source (county-n-plus-1), press outreach, or a PR.
---

# An ask to a public office

An e-mail to a named official is outward-facing and irreversible, and its
state has been got wrong in this repo in every way a gate cannot see: a
ledger read NOT YET ASKED for a month after three sends, two ledgers said
"held" about mail already gone, a draft inferred a departure from a
directory's silence, and `docs/ASK_DRAFTS.md` — four days old — already reads
"Awaiting a reply" beside a yes recorded in seven other files. `CLAUDE.md`
carries the honesty rules, the Jo Daviess licence story, the Clay spam-folder
lesson and the vendor-sweep rule; `docs/EXPANSION_GUIDE.md` §5.1 states that
the ask is a route, not a last resort. This carries the protocol and where
each state is written down.

## 1. An ask is the residue of a probe, never a first move

Read the unit's own site first; accept an address only when the officeholder's
own name vouches for it or its form is an office mailbox — a page window is
not a witness, and the first probe of one tranche returned a deputy's
personal address in four of seven counties. Re-run the probe before
re-sending an old draft: a redesigned site often starts publishing the thing.
Then check whether someone ELSE already publishes it — a state site, a results
vendor, the clerk domain in `il/data/app/il-county-clerks.json` — because
asking forty-eight counties for an address that turns out to be published
spends the operator's credibility on a question they can answer with a link.
`docs/ASK_DRAFTS.md` §"What is NOT here, and why" records one such ask being
HELD, with the two measured reasons; do not send it past them.

## 2. Pick the recipient by who owns the record

In Iowa that is the county auditor, never a guessed treasurer@ or sheriff@.
One e-mail per county even where two things are missing. For a permission or
licence question, REPLY ON THE ORIGINAL THREAD to the person who wrote the
authorization and cc the published office mailbox so it lands in the office's
record; cc-ing an administrator who was never on the thread is optional and
can read as an escalation.

## 3. Write to the template shape

Ask 1 in `docs/ASK_DRAFTS.md` is the skeleton: a subject naming the ONE thing;
who you are, the instance URL, free and non-commercial; what already ships for
this unit and from which named sources; the one thing not found and WHY it is
missing; a request for a one-line reply; and an explicit line that a "no" is a
genuinely useful answer, so declining is easy. Two things never go in: a home
address or personal contact detail, and a guessed name — leave it off. Sign
with the literal placeholders `<YOUR NAME>` / `<YOUR E-MAIL>`; they are
deliberately never filled in that public file.

Three variants: two publishers disagree on a NAME → name both people and ask
which is correct, a smaller question than an open one; a permission
confirmation → say plainly it is not a re-litigation and nothing is blocked
on it, state what is and is not done (not redistributed, credited on the card,
excluded from the project's own data grant), offer a fresh authorization or a
form, and offer take-down as a real outcome; a dataset or licence question to
an agency → say a "not public / not redistributable" answer is fully
acceptable and will be recorded.

## 4. Never send

The operator sends. Nothing is sent automatically and no draft is sent by
the agent that wrote it. A new draft is a new `## Ask N —` section in
`docs/ASK_DRAFTS.md`, or a `### <Unit> — <Recipient> <address>` block under a
tranche heading.

## 5. Record DRAFTED where the gap lives

The unit's gap record in `docs/DATA_LAYER_GUIDEBOOK.md` carries the state in
its `blocker` text: `NOT YET ASKED — DRAFTED`. The ledger differs by instance:
Iowa's send dates go in `ia/WATCH.md`; a Wisconsin ask lives only in the
guidebook. Write the state where the next reader of THAT unit will look.

## 6. On send — the same day, never before

That is the Scott rule (distinct from `CLAUDE.md`'s "Scott reasoning", which is
about primary returns naming nominees): change `NOT YET ASKED — DRAFTED` to
`ASKED <date>` in the gap record; add a `> **SENT <date>.**` block at the top
of the ask in `docs/ASK_DRAFTS.md` with the two follow-up dates and who was
actually addressed and cc'd; and fix, in the SAME commit, any published
statement the send makes stale — `LICENSE-DATA.md` once said a permission
"has not been re-sought" the day after it was, and a published legal
statement a day stale is a bug here.

## 7. Follow up, then say UNRESPONSIVE — which is not "no source"

At ~3 weeks, again ~2 weeks later, and only then record the route
UNRESPONSIVE — a different claim from "no source exists". A follow-up is a
recovery mechanism, not a nudge. For a permission ask, UNRESPONSIVE is a claim
about the ask and never about the permission: the existing authorization
stands and the display continues.

## 8. On a reply — every surface, the same day

YES → the date and wording in the unit's guidebook entry, then every place the
gap was written: for Jo Daviess that was `LICENSE-DATA.md` §3 and
`SOURCE_LABEL` in `scripts/build_jodaviess_board_districts.py`, which ships
into the data file and renders on the card, plus the worksheet and the
validators. NO or take it down → the file leaves `il/data/app/`, the dispatch
entry goes, and the gap record reopens citing the withdrawal; that is a real
outcome and the ask should not pretend otherwise. Quote a reply as written,
typo included, and say which figure is the typo. And update the ask's own
SENT block in `docs/ASK_DRAFTS.md` — the one surface the Jo Daviess yes was
not written to.

## 9. Nevers

- Never send, and never let a draft imply the agent will.
- Never record a send date before the day it goes; never leave one unrecorded on that day.
- Never infer from an absence — a directory that omits someone has not said they left.
- Never write a home address into the repo, even when a clerk's reply carries one.
- Never write "the county publishes no X" to the person who maintains the source without having searched.
- Never ask for something a state site or vendor already publishes.

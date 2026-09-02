---
name: press-outreach
description: Prepare, verify and ledger a press wave from docs/PRESS_LIST.md — the generated reading of docs/press-list.json — under the same discipline as the county asks: the operator sends, the send date is recorded the day it goes and never before, one follow-up ever, and the gates run the morning of the wave. Use it for "prepare wave 3", "update the press list", "add the Tribune and write its opening line", "verify the addresses before the regional wave", "we sent wave 1 today, fill the ledger", "the Southern Illinoisan replied", "which UTM for the Wisconsin pitches", "is the DMARC check done". Nothing here is ever sent by the agent, and PRESS_LIST.md is never hand-edited. Not for an ask to a public office (outbound-ask), a data question, or a PR (steward).
---

# A press wave

`docs/PRESS_LIST.md` is GENERATED from `docs/press-list.json` by
`scripts/build_press_list.py`; a hand edit fails its `--check`. Its own
"How this file is used" adopts the ask protocol wholesale, and its "Send
mechanics" and "What could go wrong" sections are the operator's plan — read
them there. This is the order of the work and the three traps the file itself
names: a send recorded before it happens, a duplicate room under two names,
and a wave sent on a list nobody re-verified.

## 1. The list is data; the page is a reading of it

Add or change an outlet in `docs/press-list.json` — send address, purpose,
source URL and the verbatim snippet that vouches for the address, wave, tier
— then:

```bash
python3 scripts/build_press_list.py            # regenerate docs/PRESS_LIST.md
python3 scripts/build_press_list.py --check    # the drift gate
```

An inbox whose `purpose` is not a news desk stays on the list (it is the only
route in) and the row says so; a release sent to it as though it were a city
desk is a misfire — write those as a short personal note.

## 2. Verify before every wave, never from memory

```bash
python3 scripts/verify_press_list.py           # re-fetches every cited page
```

It checks the address is still published where it was cited — decoding
Cloudflare's e-mail obfuscation rather than reading it as absence, and
reporting a page that will not load as FETCH_FAILED, which is not the same
verdict as NOT_ON_PAGE (newsroom CDNs refuse datacenter clients constantly).
Then, the morning of the wave: `python3 scripts/validate_index.py il/index.html`,
`python3 scripts/validate_card_links.py`, and the smoke test for the instance
the wave points at; hand-check three to five real addresses in the wave's
footprint. An editor types their own address first, and that is where it
breaks.

## 3. De-dupe by ADDRESS, not by outlet name

The list carries the same room twice under different names (a weekly and its
merged sibling; a documenters project under two banners). Two pitches from one
sender in ten days to one tips inbox is a spam report. Build the wave's send
set by address and diff it against every earlier wave's.

## 4. The letter

Plain text, under 200 words, no attachments, the release as a link. Deep-link
every pitch to the reader's own turf with the permalink form the file gives —
query first, hash last — carrying `utm_campaign=districtry-launch`,
`utm_medium=email` and the wave's own `utm_source`. No tracking pixel, no read
receipt, no link-wrapping service: the privacy page names every recipient of a
reader's data, and a pitch that opens with that claim cannot carry an invisible
tracker. Send to the desk or tips inbox the outlet publishes; a named
reporter is the byline to address the first line to, not the To: field.
Personalise in the three places the file says pay and nowhere else. Put the
not-a-government-service line in the body, not only the release. State
plainly what the interface's language support is to the language press. Close
with the three-item offer. Never an embargo, never an exclusive, never a
claimed affiliation.

## 5. Send windows and volume

Tuesday to Thursday, 6:30–8:00 in the RECIPIENT's local time — wave 4 crosses
three time zones, so schedule rather than batch. Never Friday afternoon, never
a holiday-shortened week. Under about 40 a day, no more than ~25 in any hour.
Before wave 1: SPF, DKIM and DMARC all passing for the sending domain, and a
test message landing in a Gmail, an Outlook and a Yahoo inbox — deliverability
failure is silent, and a spam-foldered campaign reads as "nobody was
interested".

## 6. The ledger — the same rule as the asks, for the same reason

The operator sends. Fill the send-ledger row at the foot of the page the day
the pitch goes — address used, wave, date, follow-up due — never in advance;
two ask ledgers in this repo once said "held" about mail already sent. ONE
follow-up, at 6–8 business days, in the same thread, three sentences, carrying
something NEW (a county that shipped since, a gap that closed, a link to that
outlet's turf); after it, stop. A clean no is recorded — it closes an outlet
for good. Hold the wire and association sends until the local wave has had
its window; a pickup first makes the local editor see the story as covered.

## 7. Nevers

- Never send; never hand-edit `docs/PRESS_LIST.md`.
- Never record a send before the day it goes; never a second follow-up.
- Never BCC, CC, or a mailing-list tool; never a pixel or a wrapped link.
- Never a pitch on a list `scripts/verify_press_list.py` has not re-checked that week.
- Never a mail-merge token unproofed — the county merge in the regional wave is the most valuable and the most fragile part of the send.

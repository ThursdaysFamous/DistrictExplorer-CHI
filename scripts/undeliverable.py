"""Addresses this repo publishes nowhere, because mail to them cannot arrive.

WHY THIS IS SHARED RATHER THAN PER-BUILDER. build_county_clerk_roster.py has
carried a KNOWN_UNDELIVERABLE list since 2026-07-31, when a letter to White
County's published clerk address hard-bounced after five days — the card had
been telling a reader "write to your clerk here" while nothing they sent could
arrive. That is the honesty rule failing quietly, and it turned out not to be
one county's problem: an MX sweep of every shipped address on 2026-09-04 (3,336
addresses, 768 domains, 0 network skips, every finding confirmed on a second
independent resolver) found nineteen more across three instances.

WHAT A FINDING HERE IS, EXACTLY. The domain does not resolve at all — no MX, no
A, no AAAA, NXDOMAIN. That is the only DNS evidence strong enough to withhold
on. A domain that resolves but publishes no MX has an IMPLICIT MX at its A
record (RFC 5321 §5.1) and is NOT here; validate_card_links.py reports those
separately as unverified, because only sending settles them.

THE CORRECTION IS NEVER APPLIED. Every one of these is one character from a
domain that does resolve — warrecountyil.gov/warrencountyil.gov,
yahoo.ocm/yahoo.com — and the obvious fix was measured live for all of them.
That is evidence for the DIAGNOSIS and nothing more. Douglas County settled
this in Illinois: its yearbook printed `douglascountuil.gov` and the builder
dropped the address rather than "silently correcting a character in someone's
contact detail". Officeholder data is never guessed, and a contact detail is
officeholder data.

WHAT STILL SHIPS. Only the address is withheld. The name, office, phone, party
and page URL are untouched, so every contact route that works survives and the
card simply stops offering one that does not. No app change is needed — each
card renders its e-mail row only when the field is present.

WHAT DOES NOT BELONG HERE: A CORRECT ADDRESS WHOSE ROUTE IS BROKEN. Every
entry below is a MISTYPED ADDRESS, and that is what makes the list safe — the
moment a source publishes the right one the entry stops matching and says so.
A correct address on a domain whose MX host does not resolve is a different
thing: the county can fix its DNS tomorrow without the address changing by a
character, so an entry here would never retire and would go on withholding a
working contact. Those are REPORTED by validate_card_links.py and left to the
monthly issue — `auditor@harrisoncountyia.org` is one today (its MX names
mail.harrisoncountyia.org, which is NXDOMAIN on both resolvers).

RETIRING AN ENTRY. When the source publishes something different, this list
stops matching and report_unmatched() prints a RETIRE line naming the stale
entry. Delete it then. If an address is ever reported working rather than
re-addressed, verify by SENDING — never by assuming, which is the limit the
White County bounce recorded from the other direction: its DNS was healthy the
whole time.
"""

# address (lower-case) -> (scope, the measurement that justifies withholding it)
#
# SCOPE IS THE data/app FILE THE ADDRESS SHIPS IN, and it is what makes the
# RETIRE audit honest: a builder that re-audited the whole list would report
# twelve other instances' entries as stale on every run, which is noise that
# teaches a reader to ignore the line. Each builder audits its own file.
UNDELIVERABLE = {
    # ---- Illinois: municipal-officials.json, carried from county clerk
    #      directories exactly as each clerk published them.
    "lwilson@cityofalton.il.gov": (
        "municipal-officials.json",
        "cityofalton.il.gov is NXDOMAIN (measured 2026-09-04, Google and "
        "Cloudflare DoH). The city is at cityofaltonil.gov."),
    "jsisti@villageofgrandvew.gov": (
        "municipal-officials.json",
        "villageofgrandvew.gov is NXDOMAIN (2026-09-04) — 'grandvew' for "
        "'grandview'. The village's own domain resolves and carries MX."),
    "grandview@villaegofgrandview.gov": (
        "municipal-officials.json",
        "villaegofgrandview.gov is NXDOMAIN (2026-09-04) — 'villaeg' for "
        "'village'. A SECOND typo of the same village's domain, published "
        "beside the first, which is why this list is keyed by address."),
    "eeeten@gmail.org": (
        "municipal-officials.json",
        "gmail.org is NXDOMAIN (2026-09-04) — almost certainly gmail.com, and "
        "a personal mailbox is exactly where a guessed correction would do the "
        "most harm."),
    "etajenhorst@hormil.xom": (
        "municipal-officials.json",
        "hormIL.XOM is NXDOMAIN (2026-09-04) — '.xom' is not a TLD."),
    "trusteechristofilakos@vilageofjerome.com": (
        "municipal-officials.json",
        "vilageofjerome.com is NXDOMAIN (2026-09-04) — 'vilage' for 'village'."),
    "mmcdonald@offallon.org": (
        "municipal-officials.json",
        "offallon.org is NXDOMAIN (2026-09-04). O'Fallon publishes on a "
        "different domain; this one has no DNS record of any kind."),
    "brichbark@southerview.us": (
        "municipal-officials.json",
        "southerview.us is NXDOMAIN (2026-09-04) — the village is Southern "
        "View."),
    "sstillwell@sugargroveil.org": (
        "municipal-officials.json",
        "sugargroveil.org is NXDOMAIN (2026-09-04)."),

    # ---- Illinois: county board rosters, scraped from each county's own page.
    "twinkler@warrecountyil.gov": (
        "warren-county-board-members.json",
        "warrecountyil.gov is NXDOMAIN (2026-09-04) — a dropped 'n'. The "
        "county's real domain resolves and carries MX, so this is the county's "
        "own typo on its own page."),
    "doug.bening@washingtonco.illnois.gov": (
        "washington-county-board-members.json",
        "washingtonco.illnois.gov is NXDOMAIN (2026-09-04) — 'illnois' for "
        "'illinois'."),

    # ---- Iowa: ia-county-officers.json.
    "fpowless@monroecounty.iowa": (
        "ia-county-officers.json",
        "monroecounty.iowa is NXDOMAIN (2026-09-04) — the domain is "
        "monroecounty.iowa.gov, which Monroe's recorder and sheriff both use. "
        "STALE RATHER THAN MISREAD: run against the source today "
        "(iowatreasurers.org, county 68) the scraper produces the complete "
        "address, classified 'witnessed'. So this entry exists to stop a dead "
        "address shipping until the next weekly rebuild, and it retires itself "
        "the moment that rebuild writes the full domain."),

    # ---- Wisconsin: county-board-members.json. Both are PERSONAL mailboxes a
    #      county publishes as the way to reach that supervisor, which is
    #      normal there (Florence publishes six of eleven on consumer domains)
    #      — so neither is a county-domain problem, just a mistyped address.
    "jeromekremp@yahoo.ocm": (
        "county-board-members.json",
        "yahoo.ocm is NXDOMAIN (2026-09-04) — '.ocm' is not a TLD. Clark "
        "County, District 25."),
    "jmills@florwi.org": (
        "county-board-members.json",
        "florwi.org is NXDOMAIN (2026-09-04): no SOA, NS, A or MX. Florence "
        "County. Recorded on 2026-09-03 as an address that 'routes mail fine' "
        "— that claim was never measured and was wrong."),
}


# Every address withhold() is ASKED about, so report_unmatched() needs nothing
# threaded through a builder. A caller that forgets to collect its own list is
# exactly how a re-audit goes quietly vacuous.
_SEEN = set()


def withhold(email, where=""):
    """(address_to_ship, note) — the address, or None when it cannot receive.

    `where` is printed with any drop so a weekly run says which record lost an
    address rather than only that one did.
    """
    if not email:
        return email, None
    _SEEN.add(email.strip().lower())
    entry = UNDELIVERABLE.get(email.strip().lower())
    if entry is None:
        return email, None
    _scope, reason = entry
    import sys
    print("undeliverable: dropped %s%s — %s"
          % (email, (" from %s" % where) if where else "", reason),
          file=sys.stderr)
    return None, reason


def report_unmatched(scope):
    """Print a RETIRE line for every entry in `scope` no source published.

    `scope` is the data/app file this builder writes; the addresses the run
    encountered are whatever withhold() was asked about. An entry nothing
    matches describes an address no longer in any source, which makes it a
    fact about the past sitting in a live list.
    """
    import sys
    mine = {a for a, (sc, _r) in UNDELIVERABLE.items() if sc == scope}
    stale = sorted(mine - _SEEN)
    for addr in stale:
        print("undeliverable: RETIRE %s — no source published it this run, so "
              "the entry is stale and should be deleted" % addr, file=sys.stderr)
    return stale

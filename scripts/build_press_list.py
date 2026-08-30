#!/usr/bin/env python3
"""Generate docs/PRESS_LIST.md from docs/press-list.json.

Same convention as build_county_status.py: the JSON is the data, the markdown is a READING of
it, and the markdown is never hand-edited. `--check` fails if the two have drifted.

Why this is generated rather than written: a press list is a pile of facts that go stale
independently — an address is retired, a weekly changes hands, a desk is folded into another.
Hand-keeping the prose and the data in agreement is exactly the drift this repo generates files
to prevent. Re-verify with scripts/verify_press_list.py, which re-fetches every cited page.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "press-list.json"
OUT = ROOT / "docs" / "PRESS_LIST.md"

STATE_MARK = {
    "CONFIRMED": "confirmed",
    "UNRECHECKED": "**unrechecked**",
    "PARTIAL": "**partial**",
    "NOT_FOUND": "**not found**",
    "UNKNOWN": "**unknown**",
}


def esc(s):
    """Markdown-table-safe: a pipe inside a cell silently splits the row."""
    return re.sub(r"\s+", " ", (s or "").replace("|", "\\|")).strip()


def render(d):
    L = []
    a = L.append
    n_out = len(d["outlets"])
    n_send = sum(1 for o in d["outlets"] if o["send_to"])
    n_conf = sum(1 for o in d["outlets"] if o["send_to"] and o["send_to"]["state"] == "CONFIRMED")
    n_t1 = sum(1 for o in d["outlets"] if o["tier"] == 1)

    a("# districtry launch — press list")
    a("")
    a("<!-- ==== GENERATED FILE — DO NOT HAND-EDIT ==== -->")
    a("<!-- Emitted by scripts/build_press_list.py from docs/press-list.json.")
    a("     Regenerate:  python3 scripts/build_press_list.py")
    a("     Drift gate:  python3 scripts/build_press_list.py --check")
    a("     Re-verify:   python3 scripts/verify_press_list.py -->")
    a("")
    a(f"**{n_out} newsrooms and desks; {n_send} carry a send address, {n_conf} of those "
      f"mechanically confirmed on the page that publishes them. {n_t1} are tier 1.**")
    a("")
    a(f"Compiled {d['verified_date']} for the launch release. Press contact "
      f"`{d['release']['press_contact']}` / {d['release']['press_phone']}; the volunteer ask goes "
      f"to `{d['release']['volunteer_contact']}`.")
    a("")

    a("## How this file is used")
    a("")
    a("The same rules `docs/ASK_DRAFTS.md` sets for outbound asks apply here, for the same reason:")
    a("")
    a("1. **The operator sends. Nothing here is sent automatically, and no pitch is sent by the "
      "agent that compiled the list.** A cold e-mail to a newsroom is outward-facing and cannot "
      "be recalled; it goes when a person decides it goes.")
    a("2. **Record the send date the day it goes, never before**, in the ledger at the foot of "
      "this file. An unsent row and a sent-but-unanswered row are different states and must not "
      "look alike.")
    a("3. **One follow-up, at 6–8 business days, in the same thread, carrying something new.** "
      "Then stop. A newsroom that did not bite is a closed question, not a queue.")
    a("4. **One address per message. No BCC, no mailing-list tool.** A visible blast to thirty "
      "tips inboxes is a filter event, and it is also the thing that makes a sender a spammer "
      "rather than a correspondent.")
    a("5. **A clean no is a good outcome** and worth recording — it closes an outlet for good.")
    a("")

    a("## How each address got here")
    a("")
    a("Two independent steps, because a wrong address does not merely fail — it burns the pitch "
      "and, if it bounces to a shared desk, the sender's name with it.")
    a("")
    a("* **Researched under a no-guessing rule.** The agents that compiled this were forbidden "
      "from inferring an address from a pattern — no `tips@`, no `news@`, nothing reconstructed "
      "from a domain. Every address had to be read on a page the agent actually fetched, and "
      "returned with that page's URL and a verbatim snippet showing it published there.")
    a("* **Then re-checked mechanically.** `scripts/verify_press_list.py` re-fetches every cited "
      "page and looks for the address on it, decoding Cloudflare `data-cfemail` obfuscation and "
      "PDF text along the way — both of which had already produced false misses here, and one of "
      "which (Cloudflare) is the same trick that once silently emptied seven county e-mail "
      "addresses out of this project's own data.")
    a("")
    a("So the **State** column is a measurement, not a confidence:")
    a("")
    a("| State | Means |")
    a("|---|---|")
    a("| `confirmed` | the address was found on the page cited for it |")
    a("| `unrechecked` | that page refuses this network (Akamai/Cloudflare 403, a TLS failure). "
      "**This is a fact about the host, not a doubt about the address** — the same inversion "
      "`validate_card_links.py` uses for its `EXPECTED_UNREACHABLE` hosts. Confirm in a browser "
      "before sending. |")
    a("")
    a("Rows with **no send address at all** are listed separately. They are not failures: a "
      "newsroom that publishes only a form is answered through its form, and several sites here "
      "sit behind a captcha or a managed challenge that nothing in this repo will route around.")
    a("")

    a("## Where the release goes, and in what order")
    a("")
    a("Every link is tagged `utm_campaign=" + d["utm"]["campaign"] + "` and "
      "`utm_medium=" + d["utm"]["medium"] + "`, with a per-wave `utm_source`, so the whole push "
      "totals as one campaign while each room splits out. That tagging is the only attribution "
      "that will ever exist for most of these sends — and it is checked: the app reads `utm_*` "
      "before the hash router strips them (`il/index.html`), and a `utm_source` other than "
      "`share`/`embed` renders the landing page rather than forwarding, so a Wisconsin editor "
      "clicking a root link is not silently dropped into the Illinois app.")
    a("")
    for i, w in enumerate(d["waves"], 1):
        a(f"### {esc(w['name'])}")
        a("")
        a(f"*{esc(w['when'])}*")
        a("")
        a(f"**Subject:** {esc(w['subject_line'])} ({len(w['subject_line'])} chars)")
        a("")
        a(f"**Opens:** {esc(w['lede'])}")
        a("")
        a(f"**Who:** {esc(w['who'])}")
        a("")
        a(f"**Why this order:** {esc(w['rationale'])}")
        a("")

    a("## The list")
    a("")
    labels = {r["key"]: r for r in d["regions"]}
    for r in d["regions"]:
        rows = [o for o in d["outlets"] if o["region"] == r["key"] and o["send_to"]]
        if not rows:
            continue
        a(f"### {r['label']} — {len(rows)} ({sum(1 for o in rows if o['tier'] == 1)} tier-1)")
        a("")
        a(f"Tag these `utm_source={r['utm_source']}`.")
        a("")
        a("| # | Outlet | What they are | Send to | State | Lead with |")
        a("|---|---|---|---|---|---|")
        for o in sorted(rows, key=lambda x: (x["tier"], x["name"])):
            s = o["send_to"]
            name = esc(o["name"])
            if o["also_known_as"]:
                name += " <br>*(also " + esc(", ".join(o["also_known_as"])) + " — one inbox)*"
            a(f"| {o['tier']} | [{name}]({o['homepage']}) | {esc(o['medium'])} | "
              f"`{s['value']}` <br>[source]({s['source_url']}) | {STATE_MARK.get(s['state'], s['state'])} | "
              f"{esc(o['angle'])} |")
        a("")

    noaddr = [o for o in d["outlets"] if not o["send_to"]]
    if noaddr:
        a("### No published address — reach these another way")
        a("")
        a("| Outlet | Region | Route | Why |")
        a("|---|---|---|---|")
        for o in sorted(noaddr, key=lambda x: (x["region"], x["name"])):
            route = o["forms"][0] if o["forms"] else o["homepage"]
            why = esc(o["notes"])[:240]
            a(f"| [{esc(o['name'])}]({o['homepage']}) | {labels[o['region']]['label']} | "
              f"[form / contact page]({route}) | {why} |")
        a("")

    a("## Bylines worth addressing a pitch to")
    a("")
    a("The plan's rule stands: **send to the desk, name the reporter in the first line.** A "
      "personal address is listed only where the outlet publishes it on its own staff page, and "
      "a desk address outlives any reporter's move between now and the send.")
    a("")
    a("| Outlet | Reporter | Beat |")
    a("|---|---|---|")
    for o in d["outlets"]:
        for b in o["bylines"]:
            if not b.get("name"):
                continue
            a(f"| {esc(o['name'])} | {esc(b['name'])} | {esc(b.get('beat', ''))} |")
    a("")

    a("## Send mechanics")
    a("")
    for m in d["mechanics"]:
        a(f"- {esc(m)}")
    a("")
    a("## What could go wrong")
    a("")
    for r in d["risks"]:
        a(f"- {esc(r)}")
    a("")

    a("## Send ledger")
    a("")
    a("Fill a row the day a pitch goes out — **never in advance**. `docs/ASK_DRAFTS.md` exists "
      "because two ask ledgers in this repo once said *held* about e-mails that had already been "
      "sent; a press list is the same failure waiting to happen, with strangers on the other end.")
    a("")
    a("| Outlet | Address used | Wave | Sent | Follow-up due | Reply | Outcome |")
    a("|---|---|---|---|---|---|---|")
    a("| | | | | | | |")
    a("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the file has drifted")
    args = ap.parse_args()
    text = render(json.load(open(DATA, encoding="utf-8")))
    if args.check:
        if not OUT.exists():
            print("FAIL: docs/PRESS_LIST.md is missing; run scripts/build_press_list.py")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print("FAIL: docs/PRESS_LIST.md is stale; run scripts/build_press_list.py")
            return 1
        print("OK: docs/PRESS_LIST.md matches docs/press-list.json")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

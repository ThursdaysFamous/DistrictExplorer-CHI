#!/usr/bin/env python3
"""Re-check that every address in docs/press-list.json is still published where it was cited.

Run this before a send. Newsroom inboxes get retired and contact pages get rebuilt, and a press
list is exactly the kind of file that looks fine long after it has stopped being true.

The research agents were required to return a source URL and a verbatim snippet for every
address. That is a *string* claim, not a judgement call, so it is checked by fetching the page
and looking for the address rather than by asking a second model whether it believes the first.

Three things make the check honest rather than merely strict:

  * Cloudflare e-mail obfuscation is DECODED, not treated as absence. `data-cfemail` is a hex
    string XOR-ed with its own first byte; a newsroom behind it publishes its address perfectly
    well, it just does not ship it as literal text. (This repo already learned that the hard way
    when browncoil.org switched it on and seven county e-mails silently became empty strings.)
  * Common human obfuscations (name [at] domain, name (at) domain) are normalised.
  * A page that will not load is FETCH_FAILED, which is NOT the same verdict as NOT_ON_PAGE.
    Refusing a datacenter client is something newsroom CDNs do constantly and says nothing about
    whether the address is real.
"""
import concurrent.futures
import html
import json
import re
import subprocess
import zlib
import sys

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def decode_cfemail(hexstr):
    """Cloudflare's obfuscation: hex bytes XOR-ed with the first byte."""
    try:
        data = bytes.fromhex(hexstr)
    except ValueError:
        return ""
    key = data[0]
    return "".join(chr(b ^ key) for b in data[1:])


def fetch(url):
    try:
        # Bytes, not text: plenty of small-paper sites still serve latin-1 or a mislabelled
        # charset, and a decode error there is not a verdict about the address.
        p = subprocess.run(
            ["curl", "-sSL", "--max-time", "45", "--compressed",
             "-A", UA, "-w", "\n__HTTP_STATUS__%{http_code}", url],
            capture_output=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace").strip().splitlines()
        return None, (err or ["curl error"])[-1][:120]
    raw = p.stdout
    status = ""
    m = re.search(rb"__HTTP_STATUS__(\d+)\s*$", raw)
    if m:
        status = m.group(1).decode()
        raw = raw[: m.start()]
    if status and not status.startswith("2"):
        return None, "HTTP " + status
    return raw, status or "200"


def pdf_text(raw):
    """A masthead is often only in the printed edition, and a PDF's text lives in compressed
    streams — so a PDF read as HTML looks exactly like an address that is not there."""
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            chunks.append(zlib.decompress(m.group(1)))
        except Exception:
            pass
    blob = b" ".join(chunks)
    runs = b" ".join(re.findall(rb"\((?:[^()\\]|\\.)*\)", blob)).decode("latin-1")
    return re.sub(r"[()]", "", runs)


def normalise(raw):
    """Everything an address could be hiding behind, flattened into one searchable blob.
    `raw` is bytes, so a PDF still has its real streams to decompress."""
    text = html.unescape(raw.decode("utf-8", "replace"))
    if raw.lstrip().startswith(b"%PDF") or b"endstream" in raw[:400000]:
        text += " " + pdf_text(raw)
    # Cloudflare-protected addresses, both the attribute form and the /cdn-cgi/l/email-protection#
    # link form, decoded back to the address the newsroom actually published.
    for hx in re.findall(r'data-cfemail="([0-9a-fA-F]+)"', text):
        text += " " + decode_cfemail(hx)
    for hx in re.findall(r'/cdn-cgi/l/email-protection#([0-9a-fA-F]+)', text):
        text += " " + decode_cfemail(hx)
    low = text.lower()
    # name [at] domain [dot] com -> name@domain.com
    low = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", low)
    low = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", low)
    low = re.sub(r"\s+at\s+(?=[a-z0-9.-]+\.[a-z]{2,}\b)", "@", low)
    return low


def check(job, page_cache):
    addr = (job["address"] or "").strip()
    url = (job["source_url"] or "").strip()
    out = dict(job)
    if not url.startswith("http"):
        out["verdict"] = "NO_SOURCE_URL"
        out["detail"] = "no fetchable source url was cited"
        return out
    if url not in page_cache:
        page_cache[url] = fetch(url)
    body, status = page_cache[url]
    if body is None:
        out["verdict"] = "FETCH_FAILED"
        out["detail"] = status
        return out
    blob = normalise(body)
    if job["kind"] == "form":
        # A form's "address" IS a url; the claim is only that it loads.
        out["verdict"] = "ON_PAGE"
        out["detail"] = "form url loads (HTTP " + str(status) + ")"
        return out
    if addr.lower() in blob:
        out["verdict"] = "ON_PAGE"
        out["detail"] = "found on cited page"
        return out
    # Same mailbox, different host casing/subdomain is still a real find worth reporting apart
    # from a flat miss, because it usually means the page moved rather than the address being wrong.
    local = addr.split("@")[0].lower()
    if local and len(local) > 3 and local in blob:
        out["verdict"] = "PARTIAL"
        out["detail"] = "local-part '" + local + "' appears but full address does not"
        return out
    out["verdict"] = "NOT_ON_PAGE"
    out["detail"] = "address absent from the page cited for it"
    return out


def load_jobs():
    """Every address claim in docs/press-list.json, with the page cited for it."""
    import pathlib
    data = json.load(open(pathlib.Path(__file__).resolve().parent.parent
                          / "docs" / "press-list.json", encoding="utf-8"))
    jobs = []
    for o in data["outlets"]:
        s = o.get("send_to")
        if s:
            jobs.append({"outlet": o["name"], "address": s["value"], "kind": "email",
                         "purpose": s.get("purpose", ""), "source_url": s.get("source_url", ""),
                         "was": s.get("state", "")})
        for a in o.get("alternates", []):
            jobs.append({"outlet": o["name"], "address": a["value"], "kind": "email",
                         "purpose": a.get("purpose", ""), "source_url": a.get("source_url", ""),
                         "was": a.get("state", "")})
    return jobs


def main(path=None):
    jobs = json.load(open(path)) if path else load_jobs()
    cache = {}
    results = []
    # Modest parallelism: these are other people's newsrooms, not an API.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(lambda j: check(j, cache), jobs):
            results.append(r)
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    if path:                       # only leave a report behind when one was asked for
        json.dump(results, open(path.replace(".json", "") + ".checked.json", "w"), indent=1)
    print("checked", len(results), "addresses across", len(cache), "pages")
    for k in sorted(counts):
        print(f"  {counts[k]:4d}  {k}")
    # A REGRESSION is an address that used to be found on its page and now is not: the newsroom
    # retired the inbox, or moved the page. That is the whole reason to re-run this before a send.
    regressed = [r for r in results
                 if r.get("was") == "CONFIRMED" and r["verdict"] in ("NOT_ON_PAGE", "PARTIAL")]
    for r in regressed:
        print(f"  REGRESSED  {r['outlet']}: {r['address']} -> {r['detail']}")
    print(f"\n{len(regressed)} address(es) stopped being published where they were cited.")
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))

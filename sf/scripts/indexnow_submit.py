#!/usr/bin/env python3
"""Ping IndexNow so participating search engines recrawl within minutes.

IndexNow (https://www.indexnow.org/) lets a site tell search engines a URL
changed instead of waiting for organic discovery. It notifies Bing, Yandex,
Seznam, and Naver from a single submission — it does NOT feed Google, which
still relies on Search Console + its own crawl.

Ownership is proven by hosting the key as a plain-text file at the site root:

    https://chidistricts.com/6ce8d9c81c2e4b0b914e34fd134ed36e.txt

The key is a PUBLIC ownership token, not a secret — publishing it is the whole
point of the protocol, so it lives in the repo and deploys with the site.

Usage (run only AFTER a deploy where the key file is already live):

    python3 scripts/indexnow_submit.py                       # submit the homepage
    python3 scripts/indexnow_submit.py https://chidistricts.com/ https://chidistricts.com/other

Good times to run it: the first time the key file goes live (initial indexing),
and after any deploy that changes page content (e.g. a weekly roster refresh).
Exits non-zero if IndexNow rejects the submission.
"""
import json
import sys
import urllib.request

KEY = "6ce8d9c81c2e4b0b914e34fd134ed36e"
HOST = "chidistricts.com"
ENDPOINT = "https://api.indexnow.org/indexnow"  # shared endpoint: fans out to all IndexNow engines

def main():
    urls = sys.argv[1:] or ["https://%s/" % HOST]
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": "https://%s/%s.txt" % (HOST, KEY),
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            # IndexNow returns 200 (accepted) or 202 (accepted, pending validation).
            print("IndexNow %s %s — submitted %d URL(s):" % (resp.status, resp.reason, len(urls)))
            for u in urls:
                print("  " + u)
    except urllib.error.HTTPError as e:
        # 403 = key not found/valid at keyLocation; 422 = URL/host mismatch; 429 = too many.
        print("IndexNow rejected the submission: %s %s\n%s" % (e.code, e.reason, e.read().decode("utf-8", "replace")), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

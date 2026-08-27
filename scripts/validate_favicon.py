#!/usr/bin/env python3
"""The home page must declare a favicon Google can actually fetch.

WHY THIS EXISTS. districtry.com showed the generic globe beside its Google
result while every page carried a perfectly good mark, because that mark was
inlined as a `data:` URI. Google's requirement is blunt — "Googlebot-Image must
be able to crawl the favicon file" — and there is no file to crawl in a data:
URI. `/favicon.ico`, the fallback every browser requests unprompted, 404'd as
well, so there was nothing to find by either route.

Nothing caught it. The pages were valid, the mark rendered in every browser
tab, and no gate asks whether an external crawler could reach it.

WHAT IT CHECKS, on each root page a reader or a crawler can land on:
  1. at least one rel="icon"/apple-touch-icon whose href is a real path, not a
     data: URI and not empty;
  2. that path resolves to a file that exists in the repo;
  3. the file is a format Google accepts and, for PNG, is square and at least
     48px — Google's documented recommendation;
  4. /favicon.ico exists at the root, because browsers request it whether or
     not any page names it.

Google applies one favicon PER HOSTNAME, read from the home page, so the root
pages are the surface that matters; the apps under /il/ etc. inherit it and are
deliberately not scanned.

    python3 scripts/validate_favicon.py
"""
import os
import re
import struct
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "privacy.html", "sponsorship.html"]
OK_EXT = {".ico", ".png", ".svg", ".gif", ".jpg", ".jpeg", ".webp"}
MIN_PX = 48          # Google recommends 48x48 or larger
LINK_RE = re.compile(
    r'<link\b[^>]*\brel="(icon|shortcut icon|apple-touch-icon|apple-touch-icon-precomposed)"[^>]*>',
    re.I)
HREF_RE = re.compile(r'\bhref="([^"]*)"', re.I)


def fail(msg):
    print("validate-favicon: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def png_size(path):
    with open(path, "rb") as f:
        d = f.read(24)
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", d[16:24])


def main():
    problems = []
    crawlable_total = 0

    for page in PAGES:
        path = os.path.join(REPO_ROOT, page)
        if not os.path.exists(path):
            problems.append("%s is missing" % page)
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()

        hrefs = []
        for m in LINK_RE.finditer(html):
            h = HREF_RE.search(m.group(0))
            hrefs.append(h.group(1) if h else "")

        if not hrefs:
            problems.append("%s declares no favicon at all" % page)
            continue

        crawlable = [h for h in hrefs if h and not h.lower().startswith("data:")]
        if not crawlable:
            problems.append(
                "%s declares %d favicon link(s) and every one is a data: URI — "
                "Googlebot-Image cannot crawl a data: URI, so this page has no "
                "favicon as far as Search is concerned" % (page, len(hrefs)))
            continue
        crawlable_total += len(crawlable)

        for h in crawlable:
            rel = h.split("?")[0].split("#")[0].lstrip("/")
            fp = os.path.join(REPO_ROOT, rel)
            if not os.path.exists(fp):
                problems.append("%s names %s, which does not exist in the repo"
                                % (page, h))
                continue
            ext = os.path.splitext(fp)[1].lower()
            if ext not in OK_EXT:
                problems.append("%s names %s — %s is not a favicon format Google accepts"
                                % (page, h, ext or "(no extension)"))
            if ext == ".png":
                sz = png_size(fp)
                if not sz:
                    problems.append("%s: %s has a .png name but is not a PNG" % (page, h))
                elif sz[0] != sz[1]:
                    problems.append("%s: %s is %dx%d — a favicon must be square"
                                    % (page, h, sz[0], sz[1]))
                elif sz[0] < MIN_PX:
                    problems.append("%s: %s is %dpx — Google recommends at least %dpx"
                                    % (page, h, sz[0], MIN_PX))

    ico = os.path.join(REPO_ROOT, "favicon.ico")
    if not os.path.exists(ico):
        problems.append("there is no /favicon.ico at the repo root — browsers "
                        "request it whether or not a page names it, and it is "
                        "the fallback Google falls back to")

    if problems:
        fail("%d problem(s):\n  - %s" % (len(problems), "\n  - ".join(problems)))
    print("validate-favicon: OK — %d root page(s) each declare a crawlable "
          "favicon (%d link(s) total), and /favicon.ico is present"
          % (len(PAGES), crawlable_total))


if __name__ == "__main__":
    main()

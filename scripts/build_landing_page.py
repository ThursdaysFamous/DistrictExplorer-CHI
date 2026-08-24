#!/usr/bin/env python3
"""Build the root landing page — the fleet's front door (R4, docs/DEV_PROCESS_ASSESSMENT.md).

WHY THIS EXISTS. "One repo, one site" only pays off if the site has a front
door. R2.3 moved the Illinois app to /il/ and left the root a redirect stub; R3
brought SF and NYC in as folders. This is the page that finally makes the root
mean something: the brand, and the list of places the fleet answers for.

IT IS GENERATED, AND THAT IS THE POINT. The rebrand assessment's central finding
was that brand identity had become scattered literals — 98 files carrying
`chidistricts`, seven strings locked inside engine fences, a redesign built twice
because index.html could not be parameterised. A hand-written landing page whose
state list is HTML would reproduce that failure on day one of the fix. So every
fact on this page comes from a file that already owns it:

    metros.json                            the fleet list — name, tag, blurb, url
    districtry/tokens/districtry.tokens.css the design tokens (light + dark)
    districtry/icons/favicon.svg           the mark, inlined as a data URI
    fonts/barlow-fontface.css              self-hosted Barlow (build_fonts.py landing)

Adding a state to the fleet is a metros.json entry and a regenerate. Restyling
is a token edit and a regenerate. Neither is an edit to this page.

THE FORWARDING GUARD IS NOT OPTIONAL. Before R2.3 the app lived AT the root, and
every share link and embed snippet it handed out was built from the root URL:

    https://chidistricts.com/?utm_source=share&utm_medium=link#point=41.88,-87.63&layers=ward
    <iframe src="https://chidistricts.com/?utm_source=embed&utm_medium=iframe#point=...">

Those are in other people's pages and bookmarks and cannot be recalled. The
redirect stub forwarded them; a landing page that simply replaced it would turn
every one of them into a page about Illinois instead of the map they asked for.
So the root still forwards ANY url carrying app parameters — a #point=/#layers=
permalink, or the share/embed campaign tags — and renders the landing page only
for a bare visit. The guard runs in <head> before the body paints, so a
forwarded visit never flashes this page.

WHAT IS DELIBERATELY ABSENT. No analytics: the root stub carried none, the brand
block's analytics keys are per-instance (ga_hostname is a specific app's host),
and adding a tracker to a new surface is not a build-step decision. No coverage
map: it would need Leaflet plus an instance's own boundary data, and a fleet page
that loads one instance's geometry is telling a lie about the other two.

    python3 scripts/build_landing_page.py            # write index.html
    python3 scripts/build_landing_page.py --check    # drift gate; exit 1 on diff
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import urllib.parse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO_ROOT, "metros.json")
TOKENS = os.path.join(REPO_ROOT, "districtry", "tokens", "districtry.tokens.css")
FAVICON = os.path.join(REPO_ROOT, "districtry", "icons", "favicon.svg")
# The 5c mark is lifted from the app rather than restated, so the geometry has
# one source. The favicon above is the SIMPLIFIED one-polygon fallback the brand
# spec calls for below 24px — right for a browser tab, wrong for the front door,
# which is why the two are different files doing different jobs.
MARK_SOURCE = os.path.join(REPO_ROOT, "il", "index.html")

# Each instance's worksheet, for the layer count on its card. A card that states
# a number must read it from the thing that owns it; a hand-typed count is the
# drift this repo keeps writing generators to avoid.
#
# KEYED BY INSTANCE TAG — the folder, which is the URL, which is the state code
# on the card. R5 renamed sf/ -> ca/ and nyc/ -> ny/ (the tag is the STATE, not
# the metro: metros.json still calls them 'sf' and 'nyc' by id), and this table
# is the one place that pairs a tag with a file, so it moves with them.
INSTANCE_WORKSHEET = {
    "il": "metro-worksheet.json",
    "ca": "ca/metro-worksheet.json",
    "ny": "ny/metro-worksheet.json",
}
FONTFACE = os.path.join(REPO_ROOT, "fonts", "barlow-fontface.css")
OUT = os.path.join(REPO_ROOT, "index.html")

# The canonical host TODAY. R5 moves this to districtry.com along with
# metros.json's urls; both are data, so that cutover is an edit here plus a
# regenerate, never a rewrite of the page.
CANONICAL = "https://districtry.com/"

# The rename notice. Data, not markup, so retiring it is deleting a constant
# rather than editing a page — set NOTICE to None when it has served its time.
# It is deliberately plain about what happened and what it means for a reader
# who typed the old name, because that is the only reason they are reading it.
NOTICE = {
    "heading": "chidistricts.com is now districtry.com",
    "body": ("Same map, same data, same answers — a new name, because it now covers "
             "more than Chicago and more than one state. Illinois lives at "
             "districtry.com/il, and every link below goes straight there."),
}

# Where a forwarded visit goes. The Illinois app is what lived at this root
# before R2.3, so it is the only instance whose old links can be in the wild.
FORWARD_TO = "/il/"

# Tokens this page actually sets. Naming them explicitly makes the token file a
# CHECKED dependency: rename one upstream and this build fails by name instead
# of emitting a page with a broken custom property.
LIGHT_TOKENS = [
    "brand-600", "brand-700", "brand-tint", "brand-border",
    "paper", "surface", "ink", "ink-3", "muted", "faint", "border",
    "font-heading", "font-heading-weight", "font-body",
    "radius-card", "shadow-card",
]
DARK_TOKENS = [
    "brand-tint", "brand-border",
    "paper", "surface", "ink", "ink-3", "muted", "faint", "border",
    "shadow-card",
]
# The dark block re-points --brand rather than --brand-600/700, so the page's
# link colours take these two explicitly.
DARK_EXTRA = {"brand-600": "brand", "brand-700": "brand"}


def fail(msg):
    print("build-landing-page: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read(path, what):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return f.read()
    except OSError as e:
        fail("cannot read %s (%s): %s" % (os.path.relpath(path, REPO_ROOT), what, e))


def parse_token_block(css, selector, path):
    """Return {name: value} for one CSS rule's custom properties."""
    m = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S)
    if not m:
        fail("%s has no %s block" % (os.path.relpath(path, REPO_ROOT), selector))
    return dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", m.group(1)))


def token_css(names, table, where, extra=None, indent="  "):
    out = []
    for n in names:
        if n not in table:
            fail("token --%s is missing from the %s block — renamed upstream?" % (n, where))
        out.append("%s--%s: %s;" % (indent, n, table[n].strip()))
    for alias, src in sorted((extra or {}).items()):
        if src not in table:
            fail("token --%s is missing from the %s block" % (src, where))
        out.append("%s--%s: %s;" % (indent, alias, table[src].strip()))
    return "\n".join(out)


def load_mark():
    """The 5c mark, taken from the app and made theme-aware.

    Two adaptations, both from the brand spec: the polygons MULTIPLY on a light
    ground and SCREEN on a dark one (the app only ever paints light, so it
    hardcodes multiply), and the ring-and-ascender takes currentColor so the
    ink follows the theme instead of staying near-black on a dark page.
    """
    src = read(MARK_SOURCE, "the app, for the 5c mark")
    i = src.find('<svg class="districtry-mark"')
    if i < 0:
        fail("the app no longer carries a districtry-mark SVG to lift")
    svg = src[i:src.index("</svg>", i) + len("</svg>")]
    n = svg.count('style="mix-blend-mode:multiply"')
    if n != 3:
        fail("expected the mark's 3 blended polygons, found %d" % n)
    svg = svg.replace('style="mix-blend-mode:multiply"', 'class="mk-blend"')
    if svg.count('stroke="#17161c"') != 2:
        fail("expected the mark's 2 ink strokes (ring + ascender)")
    svg = svg.replace('stroke="#17161c"', 'stroke="currentColor"')
    return svg.replace('<svg class="districtry-mark"', '<svg class="logo-mark"')


def instance_layer_count(tag):
    rel = INSTANCE_WORKSHEET.get(tag)
    if not rel:
        fail("no worksheet mapped for instance %r — add it to INSTANCE_WORKSHEET "
             "so its card can state a layer count" % tag)
    try:
        w = json.loads(read(os.path.join(REPO_ROOT, rel), "the %s worksheet" % tag))
    except ValueError as e:
        fail("%s is not valid JSON: %s" % (rel, e))
    n = len(w.get("layers") or [])
    if not n:
        fail("%s lists no layers" % rel)
    return n


def load_metros():
    try:
        manifest = json.loads(read(MANIFEST, "the fleet manifest"))
    except ValueError as e:
        fail("metros.json is not valid JSON: %s" % e)
    metros = manifest.get("metros")
    if not metros:
        fail("metros.json carries no metros")
    for m in metros:
        for key in ("tag", "landing_name", "blurb", "url"):
            if not m.get(key):
                fail("metro %r has no %r — the landing page is generated from "
                     "these fields, so a new metro must carry them"
                     % (m.get("id", "?"), key))
    return metros


def render_notice():
    if not NOTICE:
        return ""
    return (
        '    <aside class="notice" aria-labelledby="notice-h">\n'
        '      <p id="notice-h" class="notice-h">%s</p>\n'
        '      <p class="notice-b">%s</p>\n'
        '    </aside>\n'
        % (html.escape(NOTICE["heading"]), html.escape(NOTICE["body"]))
    )


def render_cards(metros):
    rows = []
    for m in metros:
        rows.append(
            '      <a class="card" href="%s">\n'
            '        <span class="card-word">districtry<span class="card-tag"> / %s</span></span>\n'
            '        <b>%s</b>\n'
            '        <span class="blurb">%s</span>\n'
            '        <span class="card-stat">%d layers</span>\n'
            '      </a>'
            % (html.escape(m["url"], quote=True),
               html.escape(m["tag"]),
               html.escape(m["landing_name"]),
               html.escape(m["blurb"]),
               instance_layer_count(m["tag"]))
        )
    return "\n".join(rows)


def _landing_jsonld(metros, title, desc):
    """The root's structured data, built from the same metros list the page renders.

    Every instance page carries a WebSite + Organization graph; the root carried
    none, so the one page naming the whole fleet was the one page search engines
    were told nothing about. The ItemList is the instances in the order a reader
    sees them, so the graph and the visible list cannot disagree.
    """
    items = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "name": m.get("landing_name") or m.get("label"),
            "url": m["url"],
        }
        for i, m in enumerate(metros)
    ]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": CANONICAL + "#website",
                "url": CANONICAL,
                "name": "districtry",
                "description": desc,
                "inLanguage": "en-US",
                "publisher": {"@id": CANONICAL + "#publisher"},
            },
            {
                "@type": "Organization",
                "@id": CANONICAL + "#publisher",
                "name": "Overberg",
                "url": "https://overberg.co",
            },
            {
                "@type": "ItemList",
                "name": "districtry instances",
                "itemListOrder": "https://schema.org/ItemListUnordered",
                "numberOfItems": len(items),
                "itemListElement": items,
            },
        ],
    }
    return json.dumps(graph, indent=2, ensure_ascii=False)


def build():
    metros = load_metros()
    tokens_css = read(TOKENS, "the design tokens")
    light = parse_token_block(tokens_css, ":root", TOKENS)
    dark = parse_token_block(tokens_css, '[data-theme="dark"]', TOKENS)

    favicon = read(FAVICON, "the brand mark").strip()
    if not favicon.startswith("<svg"):
        fail("favicon.svg does not start with <svg — is it still an SVG?")
    favicon_uri = "data:image/svg+xml," + urllib.parse.quote(favicon, safe="")

    fontface = read(FONTFACE, "the self-hosted font CSS").rstrip("\n")
    if "@font-face" not in fontface:
        fail("fonts/barlow-fontface.css carries no @font-face — regenerate it with "
             "`python3 scripts/build_fonts.py landing > fonts/barlow-fontface.css`")

    # The question leads and the brand trails — the composition the instance
    # pages carry (docs/DEV_PROCESS_ASSESSMENT.md, "The SEO surface"). Search
    # Console shows the demand is phrased as a question ("what district am i
    # in"), and a brand nobody is searching for yet cannot earn the click.
    title = "What district am I in? Find your district — districtry"
    desc = ("Pick your state, then enter an address or ZIP — districtry shows every "
            "civic district that covers that point on the map, and the people who hold "
            "those seats. Free, no login.")

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%(title)s</title>
<meta name="description" content="%(desc)s" />
<link rel="canonical" href="%(canonical)s" />
<meta name="theme-color" content="%(brand)s" />
<link rel="icon" href="%(favicon)s" type="image/svg+xml" />
<meta name="robots" content="index, follow" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="districtry" />
<meta property="og:title" content="%(title)s" />
<meta property="og:description" content="%(desc)s" />
<meta property="og:url" content="%(canonical)s" />
<meta property="og:image" content="%(canonical)sog-image.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="districtry — every district that covers a point, and who represents it." />
<meta property="og:locale" content="en_US" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="%(title)s" />
<meta name="twitter:description" content="%(desc)s" />
<meta name="twitter:image" content="%(canonical)sog-image.png" />
<script type="application/ld+json">
%(jsonld)s
</script>
<!-- GENERATED by scripts/build_landing_page.py from metros.json + the districtry
     tokens. Do NOT hand-edit: `--check` fails the build. Add a state to
     metros.json and regenerate. -->
<script>
/* FORWARD ANY OLD APP LINK, RENDER THE LANDING PAGE FOR EVERYTHING ELSE.

   Before R2.3 the Illinois app served from this root, and every share link and
   embed snippet it produced was built from the root URL — those are in other
   people's pages and bookmarks and cannot be recalled. A landing page that
   simply replaced the redirect stub would answer all of them with a page about
   Illinois instead of the map they asked for. So: a url carrying app
   parameters still forwards, carrying query AND hash exactly as the stub did.

   The two service-worker lines run on EVERY visit, forwarded or not, and stay
   narrow for the reasons R2.3 recorded: unregister only the registration scoped
   to this origin's root (an unfiltered sweep would kill the /il/ app's own
   worker), and delete only the exact legacy cache name (CacheStorage is
   per-ORIGIN, so a prefix sweep would wipe an instance's ~30 MB precache).

   This runs in <head> before the body paints, so a forwarded visit never
   flashes the landing page. */
(function () {
  try {
    if ("serviceWorker" in navigator && navigator.serviceWorker.getRegistrations) {
      navigator.serviceWorker.getRegistrations().then(function (regs) {
        regs.forEach(function (r) {
          if (r.scope === location.origin + "/") { r.unregister(); }
        });
      })["catch"](function () {});
    }
    if (window.caches && caches.delete) { caches.delete("district-explorer-shell-v51"); }
  } catch (e) { /* cleanup must never block a forward */ }

  var hash = location.hash, query = location.search;
  var isPermalink = /(?:^|[#&])(?:point|layers|zoom)=/.test(hash);
  var isTaggedShare = /[?&]utm_source=(?:share|embed)\\b/.test(query);
  if (isPermalink || isTaggedShare) {
    location.replace("%(forward)s" + query + hash);
  }
})();
</script>
<style>
%(fontface)s

:root {
  color-scheme: light dark;
%(light)s
}
@media (prefers-color-scheme: dark) {
  :root {
%(dark)s
  }
}

* { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh;
  background: var(--paper); color: var(--ink);
  font: 400 16px/1.55 var(--font-body);
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 940px; margin: 0 auto; padding: 56px 24px 72px; }

/* The logo lockup: the 5c mark beside the wordmark, at a size the mark is
   actually drawn for. The brand spec's blend rule is a REAL rule, not
   decoration — the three polygons read as overlapping translucent districts
   only if they multiply on a light ground and screen on a dark one; keep
   multiply on dark and they go muddy and near-black. */
header.mast { display: flex; align-items: center; gap: 14px; }
.logo-mark { width: 64px; height: 64px; flex: 0 0 auto; color: var(--ink); }
.logo-mark .mk-blend { mix-blend-mode: multiply; }
@media (prefers-color-scheme: dark) {
  .logo-mark .mk-blend { mix-blend-mode: screen; }
}
.wordmark {
  font: var(--font-heading-weight) 52px/1 var(--font-heading);
  letter-spacing: .005em; color: var(--ink);
}

h1 {
  font: 400 26px/1.3 var(--font-heading);
  color: var(--ink-3); margin: 22px 0 0; max-width: 34em;
}
.lede { color: var(--muted); margin: 14px 0 0; max-width: 40em; font-size: 15px; }

.notice {
  margin: 26px 0 0; padding: 14px 18px 15px;
  background: var(--brand-tint); border: 1px solid var(--brand-border);
  border-radius: var(--radius-card);
}
.notice-h {
  margin: 0 0 5px; font: var(--font-heading-weight) 17px/1.25 var(--font-heading);
  color: var(--ink);
}
.notice-b { margin: 0; font-size: 14.5px; line-height: 1.5; color: var(--ink-3); max-width: 52em; }

h2 {
  font: var(--font-heading-weight) 15px/1 var(--font-heading);
  letter-spacing: .09em; text-transform: uppercase;
  color: var(--faint); margin: 44px 0 14px;
}
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.card {
  display: block; text-decoration: none; color: var(--ink);
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-card); box-shadow: var(--shadow-card);
  padding: 16px 18px 18px;
}
.card:hover, .card:focus-visible { border-color: var(--brand-border); }
.card:focus-visible { outline: 2px solid var(--brand-600); outline-offset: 2px; }
.card-word {
  display: block; font: var(--font-heading-weight) 13px/1 var(--font-heading);
  color: var(--faint); letter-spacing: .01em; margin-bottom: 9px;
}
.card-tag { font-weight: 400; }
.card b { display: block; font: var(--font-heading-weight) 21px/1.15 var(--font-heading); margin-bottom: 6px; }
.blurb { display: block; font-size: 14px; line-height: 1.5; color: var(--ink-3); }
.card-stat {
  display: inline-block; margin-top: 11px; padding: 3px 9px 4px;
  background: var(--brand-tint); border: 1px solid var(--brand-border);
  border-radius: 999px; font-size: 12px; color: var(--ink-3);
}

.does { display: grid; grid-template-columns: repeat(auto-fit, minmax(255px, 1fr)); gap: 22px 26px; }
.does b { display: block; font: var(--font-heading-weight) 17px/1.25 var(--font-heading); margin-bottom: 5px; }
.does p { margin: 0; font-size: 14px; line-height: 1.55; color: var(--ink-3); }

footer { margin-top: 52px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 13.5px; color: var(--muted); }
footer a { color: var(--brand-600); }
footer a:hover { color: var(--brand-700); }
footer p { margin: 0 0 8px; max-width: 46em; }
/* The front door had no links at all — no way to reach the privacy page
   or the source from the page most visitors land on first. */
footer .foot-links { margin-top: 12px; }

@media (max-width: 560px) {
  .wrap { padding: 36px 18px 56px; }
  .wordmark { font-size: 38px; }
  .logo-mark { width: 48px; height: 48px; }
  h1 { font-size: 22px; }
}
</style>
</head>
<body>
  <div class="wrap">
    <header class="mast">
      %(mark)s
      <span class="wordmark">districtry</span>
    </header>

    <h1>Every district that covers a point, and who represents it.</h1>
    <p class="lede">%(desc)s</p>

%(notice)s
    <h2>Choose a place</h2>
    <div class="cards">
%(cards)s
    </div>

    <h2>What it does</h2>
    <div class="does">
      <div>
        <b>Every district, not the one you asked for</b>
        <p>Pick a point and it reports every civic boundary that contains it at once —
           legislative, judicial, policing, schools, and the local special districts most
           tools leave out.</p>
      </div>
      <div>
        <b>The people, where they can be verified</b>
        <p>It names who holds each seat when a published roster says so, and links the
           official body when none does. It never guesses an officeholder.</p>
      </div>
      <div>
        <b>It shows its work</b>
        <p>Every layer names the publisher its boundary came from and where its names come
           from. What nobody publishes is listed too, rather than quietly missing.</p>
      </div>
    </div>

    <footer>
      <p>districtry is a public civic reference built from official published
         boundaries and rosters. It is not a legal record of any district line,
         and it never guesses at who holds a seat — where no verifiable roster
         exists, it links the official body instead.</p>
      <p>Each place above names its own sources on its sources page.</p>
      <p class="foot-links"><a href="privacy.html">Privacy</a> ·
         <a href="https://github.com/ThursdaysFamous/districtry" target="_blank" rel="noopener">Source on GitHub</a></p>
    </footer>
  </div>
</body>
</html>
""" % {
        "title": html.escape(title, quote=True),
        "desc": html.escape(desc, quote=True),
        "jsonld": _landing_jsonld(metros, title, desc),
        "canonical": CANONICAL,
        "forward": FORWARD_TO,
        "brand": light["brand-600"].strip(),
        "favicon": html.escape(favicon_uri, quote=True),
        "fontface": fontface,
        "light": token_css(LIGHT_TOKENS, light, ":root"),
        "dark": token_css(DARK_TOKENS, dark, '[data-theme="dark"]', DARK_EXTRA,
                          indent="    "),
        "cards": render_cards(metros),
        "mark": load_mark(),
        "notice": render_notice(),
    }


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="verify the committed index.html matches; exit 1 on drift")
    args = ap.parse_args()

    rendered = build()

    if args.check:
        try:
            with open(OUT, encoding="utf-8", newline="") as f:
                current = f.read()
        except OSError as e:
            fail("cannot read index.html: %s" % e)
        if current != rendered:
            for dl in list(difflib.unified_diff(
                    current.splitlines(), rendered.splitlines(),
                    fromfile="committed index.html", tofile="regenerated",
                    lineterm="", n=1))[:40]:
                print("  " + dl, file=sys.stderr)
            fail("index.html has drifted from metros.json + the districtry tokens. "
                 "Edit the DATA and regenerate; never hand-edit the landing page.")
        print("build-landing-page: OK — index.html matches metros.json (%d place(s)) "
              "and the districtry tokens" % len(load_metros()))
        return

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(rendered)
    print("build-landing-page: wrote index.html — %d place(s), %d bytes"
          % (len(load_metros()), len(rendered)))


if __name__ == "__main__":
    main()

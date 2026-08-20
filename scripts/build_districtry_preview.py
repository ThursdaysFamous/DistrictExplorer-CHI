#!/usr/bin/env python3
"""Build districtry-app.html — the Stage B unlisted Districtry re-skin preview.

Reads index.html, applies an ordered substitution table, writes
districtry-app.html at the repo root (a ROOT-LEVEL sibling on purpose: every
relative fetch — data/app/*.json, fonts/, icons/, ./sources.html — resolves
identically to index.html, so the diff between the two files is ONLY the
re-skin). The script NEVER writes index.html.

Every transform must match EXACTLY ONCE or the build fails loudly, naming the
pattern — upstream drift breaks this script, never silently ships a
half-skinned preview. Refresh after index.html moves:

    python3 scripts/build_districtry_preview.py && git add districtry-app.html

--check regenerates (reusing the committed file's generation stamp so the
comparison is byte-stable) and diffs against the committed copy. It is NOT
wired into CI — the preview is allowed to go stale; this just makes staleness
detectable on demand.

Scope (docs/DISTRICTRY_REBRAND.md): a pure re-skin. Every existing behavior
rides along by construction — pin-as-parent, copy-link, offices accordions,
the CARTO basemap, permalinks. Dark mode is deliberately NOT added (deferred
pending its own approval). The engine-fenced "METRO_NAME + ' District
Explorer'" strings still show the old name in dialogs — that is the Phase 3
engine release, accepted here. The skin lands as an appended override island
(the blessed outside-the-fence pattern, docs/ENGINE_SYNC.md) — no ENGINE or
GENERATED interior is edited, so this table doubles as the adoption
checklist.

Do NOT run validate_index.py against the output — it validates
worksheet-coupled invariants against whatever file it is handed and the
preview intentionally diverges (no manifest link, no SW registration).
"""

import io
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO_ROOT, "index.html")
OUT = os.path.join(REPO_ROOT, "districtry-app.html")
FAQ_OUT = os.path.join(REPO_ROOT, "districtry-faq.html")

STAMP_RE = re.compile(r'<span class="preview-stamp">([^<]*)</span>')

# The 5c mark, light variant (multiply blends), sized by the skin island.
# Inserted AFTER the hidden .masthead-star svg — never in its place:
# index.html's boot script writes #star-path-header by id and would throw on a
# missing element.
MARK_SVG = (
    '<svg class="districtry-mark" viewBox="0 0 96 96" aria-hidden="true">'
    '<g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.55"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.5"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.45"></polygon></g>'
    '<circle cx="42" cy="60" r="17" fill="none" stroke="#17161c" stroke-width="11"></circle>'
    '<line x1="59" y1="16" x2="59" y2="82.5" stroke="#17161c" stroke-width="11"></line>'
    "</svg>"
)

# Barlow rides Google Fonts here as a PREVIEW-ONLY shortcut (no committed font
# binaries before the direction is approved). Production adoption self-hosts:
# edit build_fonts.py's GFONTS_URL to the Barlow families, re-run, re-paste
# the emitted @font-face block — its documented workflow.
FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600'
    "&family=Barlow:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">\n"
)

# The skin: token re-points + the handful of chrome literals the tokens can't
# reach. Three-tier discipline — violet is chrome, the data tier keeps its
# blue (--card-accent/#1d5fd6 and every map layer color are untouched).
# Warm-accent mapping (#b0316e magenta, derived deep #8f2659) and the
# resulting magenta focus ring are explicit REVIEW ITEMS.
SKIN_ISLAND = """<style id="districtry-skin">
  /* ==== Districtry re-skin island (Stage B preview) ====
     Appended AFTER the engine styles so same-specificity rules win the
     cascade — no fence interior edited. At adoption this island is the
     fork-local restyle; see docs/DISTRICTRY_REBRAND.md. */
  :root {
    --accent: #6d3fd1;        /* brand-600 — chrome only, never map data */
    --accent-deep: #5730ab;   /* brand-700 — text/links on light */
    --accent-warm: #b0316e;   /* mark magenta — REVIEW: distinct 2nd hue */
    --accent-warm-deep: #8f2659; /* derived — REVIEW: no token exists */
    --ink: #17161c;
    --slate: #4b5563;
    --slate-soft: #9aa3b2;
    --paper: #f4f2ee;
    --panel: #ffffff;
    --line: #e8e7ef;
    --line-strong: #c9c5d4;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body: 'Barlow', 'Inter Fallback', -apple-system, BlinkMacSystemFont, sans-serif;
    /* --font-mono unchanged: IBM Plex Mono stays self-hosted */
  }
  /* card chrome only — --card-accent/--card-link ARE the data tier, kept */
  .layer-block {
    --card-border: #e8e7ef;
    --card-row-border: #f1f0f6;
    --card-sep: #c9c5d4;
    --card-section-bg: #f8f7fc;
  }
  /* the Chicago flag-stripe motif is that fork's signature device — recolored
     by the token swap it reads as meaningless violet bands, and the Districtry
     design carries no stripe, so the preview hides it */
  .flag-stripe { display: none; }
  /* masthead goes light (the approved app-shell direction) */
  header.masthead { background: var(--panel); color: var(--ink); border-bottom: 1px solid var(--line); }
  .masthead-star { display: none; }
  .districtry-mark { width: 38px; height: 38px; flex: none; }
  .title-text { font-weight: 600; text-transform: lowercase; letter-spacing: 0.005em; }
  .title-metro { color: var(--slate-soft); font-weight: 400; }
  h1.title small { color: var(--slate); }
  .preview-stamp { display: block; margin-top: 4px; font-size: 11px; color: var(--slate-soft); }
  .masthead-actions .footer-link-btn {
    color: var(--accent-deep);
    background: rgba(109, 63, 209, 0.08);
    border-color: rgba(109, 63, 209, 0.35);
  }
  .masthead-actions .footer-link-btn:hover,
  .masthead-actions .footer-link-btn:focus-visible {
    color: var(--accent-deep);
    background: rgba(109, 63, 209, 0.16);
    border-color: var(--accent);
  }
  .masthead-action-link { color: var(--slate); background: rgba(23, 22, 28, 0.03); border-color: var(--line); }
  .masthead-action-link:hover,
  .masthead-action-link:focus-visible { color: var(--ink); background: rgba(23, 22, 28, 0.06); border-color: var(--line-strong); }
  /* chrome tints the engine hardcodes as Chicago-flag rgba()s */
  .selected-point-chip .copy-link-btn:hover { background: rgba(109, 63, 209, 0.12); }
  .footer-disclaimer { background: rgba(176, 49, 110, 0.14); }
  .footer-sources a:hover,
  .footer-metros a:hover { background: rgba(109, 63, 209, 0.2); }
  /* ==== footer elimination (operator-directed, 2026-08-20) ====
     The redesign gives the map the left and bottom viewport bounds: no
     document footer, no in-page FAQ (it moves to districtry-faq.html).
     Both sections are HIDDEN, never removed — the boot script fills
     #verified-date and binds #feedback-btn / #footer-metros by id, so the
     load-bearing elements are RELOCATED into the results-panel foot by the
     transforms and only the husks stay hidden here. */
  .faq-section, footer.site-footer { display: none; }
  @media (min-width: 901px) {
    html, body { height: 100%; }
    body { display: flex; flex-direction: column; }
    header.masthead { flex: none; }
    main.layout { flex: 1 1 auto; min-height: 0; max-width: none; margin: 0; width: 100%; }
    .map-col { height: 100%; min-height: 0; }
    #map { height: 100%; min-height: 0; }
    .results-col { max-height: none; height: 100%; }
  }
  /* the panel foot — the footer's surviving content, per the app-shell canvas
     (disclaimer as a small line at the panel's bottom edge) */
  .results-col { display: flex; flex-direction: column; }
  .results-col > * { flex: none; }
  .districtry-panel-foot {
    margin-top: auto;
    padding: 10px 2px 0;
    border-top: 1px solid var(--line);
    font-size: 11px;
    line-height: 1.5;
    color: var(--slate-soft);
  }
  .districtry-panel-foot p { margin: 0 0 6px; }
  .districtry-panel-foot .footer-meta { font-size: 11px; color: var(--slate-soft); margin: 0 0 6px; }
  .dpf-links { display: flex; flex-wrap: wrap; gap: 2px 12px; margin: 0 0 8px; }
  .dpf-links a { color: var(--accent-deep); text-decoration: none; }
  .dpf-links a:hover { text-decoration: underline; }
  .districtry-panel-foot .footer-link-btn {
    font-size: 11.5px;
    padding: 4px 10px;
    margin: 0 0 6px;
    color: var(--accent-deep);
    background: transparent;
    border: 1px solid rgba(109, 63, 209, 0.35);
    border-radius: 7px;
    cursor: pointer;
  }
  .districtry-panel-foot .footer-link-btn:hover { background: rgba(109, 63, 209, 0.08); }
  .districtry-panel-foot .footer-metros { font-size: 11px; }
  .districtry-panel-foot .footer-metros a { color: var(--accent-deep); }
</style>
"""

# The FAQ's new standalone home. The extracted .faq-section markup is spliced
# in verbatim so the two copies (hidden husk in the app page, live page here)
# can never say different things within one generation.
FAQ_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>districtry / illinois — common questions (unlisted preview)</title>
<link rel="icon" type="image/svg+xml" href="districtry/icons/favicon.svg">
<link rel="stylesheet" href="districtry/tokens/districtry.tokens.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body { margin: 0; background: var(--paper); color: var(--ink); font: 400 15px/1.6 var(--font-body); }
  .wrap { max-width: 760px; margin: 0 auto; padding: 32px 24px 64px; }
  .mast { display: flex; align-items: baseline; gap: 8px; padding-bottom: 18px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
  .mast .wordmark { font: var(--font-heading-weight) 28px/1 var(--font-heading); letter-spacing: .005em; color: var(--ink); text-decoration: none; }
  .mast .tag { font: 400 22px/1 var(--font-heading); color: var(--faint); }
  .back { font-size: 13px; }
  .back a { color: var(--brand); text-decoration: none; }
  .faq-section h2 { font: var(--font-heading-weight) 26px/1.2 var(--font-heading); margin: 22px 0 10px; }
  .faq-section details { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-card); box-shadow: var(--shadow-card); margin: 0 0 10px; padding: 0 16px; }
  .faq-section summary { cursor: pointer; font-weight: 600; padding: 12px 0; list-style-position: inside; }
  .faq-section p { margin: 0 0 14px; color: var(--ink-3); }
  footer { margin-top: 28px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 11.5px; color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <div class="mast">
    <a class="wordmark" href="districtry-app.html">districtry</a>
    <span class="tag">/ illinois</span>
    <span class="tag">/ faq</span>
  </div>
  <p class="back"><a href="districtry-app.html">← Back to the map</a></p>
  __FAQ_SECTION__
  <footer>Unlisted re-skin preview. <strong>Not for legal or official use.</strong> Boundary and roster
  data come from public sources that disclaim legal precision. __STAMP__</footer>
</div>
</body>
</html>
"""


def sub_once(html, pattern, replacement, label, regex=False):
    if regex:
        matches = pattern.findall(html)
        n = len(matches)
    else:
        n = html.count(pattern)
    if n != 1:
        sys.exit(
            "build-districtry-preview: FAIL — pattern for %r matched %d times "
            "(need exactly 1). index.html has drifted past this transform; fix "
            "the table before regenerating." % (label, n)
        )
    if regex:
        return pattern.sub(replacement.replace("\\", "\\\\"), html, count=1)
    return html.replace(pattern, replacement, 1)


def build(stamp_text):
    html = io.open(SRC, encoding="utf-8").read()

    # -- strip analytics: GA is hostname-gated and the gate would PASS on the
    #    preview URL; GoatCounter is ungated and would count preview visits.
    html = sub_once(
        html,
        re.compile(r"<!-- Google tag \(gtag\.js\).*?</script>\n", re.S),
        "<!-- analytics stripped: unlisted preview -->\n",
        "GA block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<script data-goatcounter="[^"]*"\s*\n\s*async src="//gc\.zgo\.at/count\.js"></script>\n', re.S),
        "",
        "GoatCounter",
        regex=True,
    )

    # -- retitle + unlist. Canonical/OG/twitter/JSON-LD are stripped outright:
    #    a noindexed preview must not declare a canonical at the live site,
    #    and a leaked URL should unfurl as nothing.
    html = sub_once(
        html,
        re.compile(r"<title>[^<]*</title>"),
        "<title>districtry / illinois — working preview (unlisted)</title>",
        "title",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<meta name="description" content="[^"]*" />', re.S),
        '<meta name="description" content="Unlisted working preview of the Districtry re-skin. '
        'The live product is chidistricts.com." />',
        "meta description",
        regex=True,
    )
    html = sub_once(
        html,
        '<meta name="robots" content="index, follow" />',
        '<meta name="robots" content="noindex, nofollow" />',
        "robots",
    )
    html = sub_once(
        html,
        '<link rel="canonical" href="https://chidistricts.com/" />\n',
        "",
        "canonical",
    )
    html = sub_once(
        html,
        re.compile(r"<!-- Open Graph / social share previews.*?og:locale\" content=\"en_US\" />\n", re.S),
        "",
        "OG block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<!-- Twitter / X card -->.*?twitter:image" content="[^"]*" />\n', re.S),
        "",
        "twitter block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r"<!-- Structured data: help search engines understand what this tool is -->.*?FAQPage.*?</script>\n", re.S),
        "",
        "JSON-LD blocks",
        regex=True,
    )

    # -- no manifest (a preview must not be installable), new theme color,
    #    real favicon file from the Stage A asset dir.
    html = sub_once(html, '<link rel="manifest" href="manifest.webmanifest">\n', "", "manifest link")
    html = sub_once(
        html,
        '<meta name="theme-color" content="#0b3d91">',
        '<meta name="theme-color" content="#6d3fd1">',
        "theme-color",
    )
    html = sub_once(
        html,
        re.compile(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml,[^"]*" />', re.S),
        '<link rel="icon" type="image/svg+xml" href="districtry/icons/favicon.svg" />',
        "favicon",
        regex=True,
    )

    # -- fonts: swap the self-hosted Big Shoulders/Inter faces for a Google
    #    Fonts Barlow link, KEEPING the IBM Plex Mono faces (the tokens define
    #    no mono replacement and the app's mono is load-bearing).
    fonts_block_re = re.compile(
        r"/\* ==== SELF-HOSTED FONTS:BEGIN.*?SELF-HOSTED FONTS:END ==== \*/", re.S
    )
    blocks = fonts_block_re.findall(html)
    if len(blocks) != 1:
        sys.exit("build-districtry-preview: FAIL — SELF-HOSTED FONTS block matched %d times" % len(blocks))
    mono_faces = [
        face
        for face in re.findall(r"@font-face \{.*?\}", blocks[0], re.S)
        if "IBM Plex Mono" in face
    ]
    if len(mono_faces) != 4:
        sys.exit(
            "build-districtry-preview: FAIL — expected 4 IBM Plex Mono @font-face rules, found %d"
            % len(mono_faces)
        )
    html = fonts_block_re.sub(
        lambda _m: "/* Districtry preview: Barlow via Google Fonts <link> in <head>; mono kept self-hosted */\n"
        + "\n".join(mono_faces),
        html,
        count=1,
    )
    html = sub_once(html, "\n<style>\n", "\n" + FONT_LINKS + "<style>\n", "font links before <style>")

    # -- masthead: hide (never remove) the Chicago star, add the 5c mark,
    #    swap the wordmark, stamp the generation provenance into the subtitle.
    html = sub_once(
        html,
        '<path fill="var(--accent-warm)" id="star-path-header"></path>\n        </svg>',
        '<path fill="var(--accent-warm)" id="star-path-header"></path>\n        </svg>\n        ' + MARK_SVG,
        "mark insert",
    )
    html = sub_once(
        html,
        '<span class="title-text">Chicago District Explorer</span>',
        '<span class="title-text">districtry <span class="title-metro">/ illinois</span></span>',
        "wordmark",
    )
    html = sub_once(
        html,
        "<small>Click the map or search an address to see every district that covers it, and who represents it.</small>",
        "<small>Click the map or search an address to see every district that covers it, and who represents it."
        '<span class="preview-stamp">' + stamp_text + "</span></small>",
        "generation stamp",
    )

    # -- point marker joins the data tier (tokens: --data-500 is "selected
    #    boundary, point marker"). Shape stays the star — a shape change is a
    #    design call for adoption, not a re-skin.
    html = sub_once(html, 'fill="#C8102E"', 'fill="#1d5fd6"', "point-marker fill")

    # -- a preview page must be inert: no service-worker registration (it
    #    would install the production SW for a reviewer who only ever visits
    #    the preview).
    html = sub_once(
        html,
        '<script>\n  if ("serviceWorker" in navigator) {\n    navigator.serviceWorker.register("sw.js");\n  }\n</script>\n',
        "<!-- SW registration stripped: unlisted preview -->\n",
        "SW registration",
    )

    # -- footer elimination. The document footer and in-page FAQ are hidden by
    #    the skin island; their load-bearing elements are CUT from the hidden
    #    footer and relocated into a new results-panel foot, so the boot
    #    script's getElementById targets (#verified-date via #footer-meta,
    #    #feedback-btn, #footer-metros) each still exist exactly once, live.
    meta_re = re.compile(r'[ ]*<div class="footer-meta" id="footer-meta">.*?</div>\n', re.S)
    metas = meta_re.findall(html)
    if len(metas) != 1:
        sys.exit("build-districtry-preview: FAIL — #footer-meta matched %d times" % len(metas))
    footer_meta = metas[0].strip()
    html = meta_re.sub("", html, count=1)

    feedback_btn = '<button type="button" id="feedback-btn" class="footer-link-btn">💬 Report a bug or leave a comment</button>'
    html = sub_once(html, "      " + feedback_btn + "\n", "", "feedback button cut")

    metros_re = re.compile(
        r"[ ]*<!-- ==== ENGINE:BEGIN metro-links-html ==== -->\n.*?<!-- ==== ENGINE:END metro-links-html ==== -->\n",
        re.S,
    )
    metros = metros_re.findall(html)
    if len(metros) != 1:
        sys.exit("build-districtry-preview: FAIL — metro-links-html fence matched %d times" % len(metros))
    # Fences pin content, not placement — the repo's own gaps-html masthead
    # move is the precedent for relocating a fence block verbatim.
    metro_links = metros[0].strip()
    html = metros_re.sub("", html, count=1)

    panel_foot = (
        '<div class="districtry-panel-foot" id="districtry-panel-foot">\n'
        "      <p><strong>Not for legal or official use.</strong> Boundary and roster data come from public\n"
        "      sources that disclaim legal precision — confirm with the relevant government office before\n"
        "      relying on them for anything official.</p>\n"
        "      " + footer_meta + "\n"
        '      <div class="dpf-links">\n'
        '        <a href="./sources.html">Sources &amp; data layers</a>\n'
        '        <a href="./districtry-faq.html">Common questions</a>\n'
        '        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">Geocoding © OpenStreetMap contributors</a>\n'
        '        <a href="https://github.com/ThursdaysFamous/DistrictExplorer-CHI" target="_blank" rel="noopener">GitHub</a>\n'
        '        <a href="https://github.com/sponsors/ThursdaysFamous" target="_blank" rel="noopener">💛 Support this project</a>\n'
        '        <a href="https://overberg.co" target="_blank" rel="noopener">overberg.co</a>\n'
        "      </div>\n"
        "      " + feedback_btn + "\n"
        "      " + metro_links + "\n"
        "    </div>"
    )
    html = sub_once(
        html,
        '<div id="groups-root" hidden></div>\n  </section>',
        '<div id="groups-root" hidden></div>\n    ' + panel_foot + "\n  </section>",
        "panel foot insert",
    )

    # -- the FAQ moves to its own page; the in-page section stays as a hidden
    #    husk (CSS) and its markup is extracted verbatim for the new page.
    faq_re = re.compile(r'<section class="faq-section" aria-labelledby="faq-heading">.*?</section>', re.S)
    faqs = faq_re.findall(html)
    if len(faqs) != 1:
        sys.exit("build-districtry-preview: FAIL — faq-section matched %d times" % len(faqs))
    faq_html = FAQ_PAGE_TEMPLATE.replace("__FAQ_SECTION__", faqs[0]).replace("__STAMP__", stamp_text)

    # -- the skin island, last in <head> so it wins the cascade.
    html = sub_once(html, "</head>", SKIN_ISLAND + "</head>", "skin island")

    return html, faq_html


def main():
    check = "--check" in sys.argv[1:]
    if check:
        if not os.path.exists(OUT) or not os.path.exists(FAQ_OUT):
            sys.exit("build-districtry-preview: FAIL — --check but a committed output is missing")
        committed = io.open(OUT, encoding="utf-8").read()
        committed_faq = io.open(FAQ_OUT, encoding="utf-8").read()
        m = STAMP_RE.search(committed)
        if not m:
            sys.exit("build-districtry-preview: FAIL — committed preview has no generation stamp")
        regenerated, regenerated_faq = build(m.group(1))
        if regenerated != committed or regenerated_faq != committed_faq:
            sys.exit(
                "build-districtry-preview: STALE — regenerating from the current index.html "
                "differs from the committed districtry-app.html/districtry-faq.html. "
                "Re-run without --check and commit."
            )
        print("build-districtry-preview: OK — committed preview + FAQ page match a fresh build")
        return

    sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    date = subprocess.check_output(["date", "-u", "+%Y-%m-%d"], text=True).strip()
    stamp = "districtry re-skin preview (unlisted) — generated from index.html @ %s on %s" % (sha, date)
    html, faq_html = build(stamp)
    io.open(OUT, "w", encoding="utf-8").write(html)
    io.open(FAQ_OUT, "w", encoding="utf-8").write(faq_html)
    print(
        "build-districtry-preview: OK — wrote %s (%d bytes) + %s (%d bytes, stamp: %s)"
        % (
            os.path.relpath(OUT, REPO_ROOT),
            len(html.encode("utf-8")),
            os.path.relpath(FAQ_OUT, REPO_ROOT),
            len(faq_html.encode("utf-8")),
            stamp,
        )
    )


if __name__ == "__main__":
    main()

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
import json
import math
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
# ---------------------------------------------------------------------------
# The dark map palette, DERIVED rather than hand-picked.
#
# The layer palette is ~59 literals chosen against a light basemap, and it does
# not transfer: measured against CARTO dark_all's ground (#1a1a1a, which the
# app's own tile filter lifts to about #232323), 28 of 37 stroke colours fall
# below the 3:1 that WCAG 1.4.11 asks of a non-text boundary, and four —
# #14181C, #06375E, #7A0A1C, #7A0B1E — sit under 1.5:1, which is to say gone.
#
# The obvious fix is the wrong one. Lifting each colour by the MINIMUM needed to
# clear 3:1 collapses the palette, because in the light set a great deal of the
# categorical separation IS lightness: measured, 314 of 703 pairs move closer
# and 66 land inside dE 0.05 of each other (U.S. House and County both become
# the same grey; City Ward and County Board District the same blue). Hue was
# preserved and the encoding still broke.
#
# So the transform is an ORDER-PRESERVING remap instead: one monotonic affine
# map on OKLCH lightness across the whole palette, hue untouched, chroma lifted
# 1.25x to buy back the separation that compressing lightness costs. Monotonic
# means every within-layer relationship survives by construction — a stroke
# darker than its fill stays darker than its fill.
#
# The bar it is held to is not "looks nice" but a measurement against the light
# palette's own record: the light set has 25 pairs inside dE 0.05 and a p5 dE of
# 0.056; this dark set has 24 and 0.052. It is no more collision-prone than the
# palette it derives from, and every stroke clears 3.10:1.
DARK_L_LO, DARK_L_HI, DARK_CHROMA = 0.54, 0.92, 1.25


def _srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin_to_srgb(c):
    c = max(0.0, min(1.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return int(round(max(0.0, min(1.0, v)) * 255))


def _to_oklab(hexs):
    r, g, b = [_srgb_to_lin(int(hexs[i:i + 2], 16)) for i in (1, 3, 5)]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s_ = [x ** (1 / 3) if x > 0 else 0.0 for x in (l, m, s_)]
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s_,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s_,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s_)


def _from_oklab(L, a, b):
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
            -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
            -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)


def _in_gamut(L, a, b):
    return all(-0.0005 <= c <= 1.0005 for c in _from_oklab(L, a, b))


def _hex(L, a, b):
    r, g, bl = _from_oklab(L, a, b)
    return "#%02X%02X%02X" % (_lin_to_srgb(r), _lin_to_srgb(g), _lin_to_srgb(bl))


def _oklch(hexs):
    L, a, b = _to_oklab(hexs)
    return L, math.hypot(a, b), math.atan2(b, a)


def _lch_to_lab(L, C, H):
    return L, C * math.cos(H), C * math.sin(H)


def dark_map_palette(index_html):
    """Every layer stroke/fill literal in index.html -> its dark counterpart."""
    strokes = re.findall(r'\bcolor:\s*"(#[0-9A-Fa-f]{6})"', index_html)
    fills = re.findall(r'fillColor:\s*"(#[0-9A-Fa-f]{6})"', index_html)
    palette = sorted({c.upper() for c in strokes + fills})
    if not palette:
        sys.exit("build-districtry-preview: FAIL — found no layer colours to derive a dark palette from")
    ls = [_oklch(c)[0] for c in palette]
    lo, hi = min(ls), max(ls)
    span = (hi - lo) or 1.0
    out = {}
    for c in palette:
        L, C, H = _oklch(c)
        Ln = DARK_L_LO + (L - lo) * (DARK_L_HI - DARK_L_LO) / span
        Cn = C * DARK_CHROMA
        while Cn > 0 and not _in_gamut(*_lch_to_lab(Ln, Cn, H)):
            Cn -= 0.004
        out[c] = _hex(*_lch_to_lab(Ln, Cn, H))
    return out


MARK_SVG = (
    '<svg class="districtry-mark" viewBox="0 0 96 96" aria-hidden="true">'
    '<g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.55"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.5"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.45"></polygon></g>'
    '<circle cx="42" cy="60" r="17" fill="none" stroke="#17161c" stroke-width="11"></circle>'
    '<line x1="59" y1="16" x2="59" y2="82.5" stroke="#17161c" stroke-width="11"></line>'
    "</svg>"
)

# The 5c mark as a quiet outline, for the empty state where the Chicago flag
# star used to sit. Same construction as MARK_SVG, drawn in the chrome inks
# rather than at full saturation so it reads as a placeholder, not a logo.
EMPTY_MARK_SVG = (
    '<svg class="districtry-empty-mark" viewBox="0 0 96 96" aria-hidden="true">'
    '<g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.20"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.18"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.16"></polygon></g>'
    '<circle cx="42" cy="60" r="17" fill="none" stroke="#9aa3b2" stroke-width="9"></circle>'
    '<line x1="59" y1="16" x2="59" y2="82.5" stroke="#9aa3b2" stroke-width="9"></line>'
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
    /* The warm accent is NOT decoration: the engine paints the Public Safety
       group dot with it (index.html .group-safety .dot), beside Political
       (--accent), Schools (#E8A324) and Geography (#5C8F6B). Setting it to
       violet — the "one hue for both slots" idea — would make two of the four
       group dots identical, so a distinct hue is required, not preferred. It
       is also the focus ring, where contrast AGAINST violet controls is the
       point. #b0316e is the mark's own third polygon, so the hue is on-brand
       without borrowing from the data tier (police/fire reds are map colors). */
    --accent-warm: #b0316e;   /* mark magenta — group dot + focus ring */
    --accent-warm-deep: #8f2659; /* derived; unreferenced by the engine today,
       overridden anyway so no Chicago flag red survives in the cascade */
    --ink: #17161c;
    --slate: #4b5563;
    --slate-soft: #9aa3b2;
    --paper: #f4f2ee;
    --panel: #ffffff;
    --line: #e8e7ef;
    --line-strong: #c9c5d4;
    /* --faint was referenced by the map legend from the day it shipped and
       never defined, so the kicker and the why-line silently fell back to
       inheriting --slate. Defining it is the fix; the dark block below needs
       a counterpart for it anyway. */
    --faint: #9aa3b2;
    /* Tints, as tokens rather than the fifteen rgba() literals they replace at
       their WINNING call sites. Light values are the ones already in force, so
       light mode is unchanged; dark needs violet lifted off a dark ground, and
       a literal cannot do that. */
    --dst-brand-tint: rgba(109, 63, 209, 0.10);
    --dst-brand-tint-soft: rgba(109, 63, 209, 0.07);
    --dst-brand-line: rgba(109, 63, 209, 0.30);
    --dst-focus-tint: rgba(109, 63, 209, 0.14);
    --dst-ink-tint: rgba(23, 22, 28, 0.03);
    --dst-ink-tint-strong: rgba(23, 22, 28, 0.06);
    --dst-shadow: rgba(23, 22, 28, 0.14);
    --dst-shadow-soft: rgba(23, 22, 28, 0.06);
    --dst-sunken: #ffffff;
    --dst-raised: #ffffff;
    --dst-raised-hover: #EEF4F7;
    /* The UA paints checkboxes, scrollbars and text-field interiors itself and
       will not read a token to do it. Without this the 39 layer checkboxes
       stayed bright white squares on the dark cards — the single most visible
       thing wrong with the first dark build. */
    color-scheme: light;
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
  /* ==== empty state: the Chicago flag star retires ====
     The six-pointed star is that city's emblem; recoloured violet it was
     simply an off-brand Chicago motif sitting in a Districtry app. The path
     element STAYS in the DOM (hidden) because the boot script writes its `d`
     by id and would throw on a missing node — the same discipline as the
     masthead star — and the 5c mark is drawn beside it. */
  .empty-state .star-outline { display: none; }
  .empty-state .districtry-empty-mark { width: 76px; height: 76px; margin: 0 auto 4px; display: block; opacity: 0.9; }
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
  .masthead-action-link { color: var(--slate); background: var(--dst-ink-tint); border-color: var(--line); }
  .masthead-action-link:hover,
  .masthead-action-link:focus-visible { color: var(--ink); background: var(--dst-ink-tint-strong); border-color: var(--line-strong); }
  /* chrome tints the engine hardcodes as Chicago-flag rgba()s */
  .selected-point-chip .copy-link-btn:hover { background: var(--dst-brand-tint); }
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
     (disclaimer as a small line at the panel's bottom edge).
     :not([hidden]) is LOAD-BEARING, not decoration: a bare `.results-col
     { display: flex }` outranks the UA's `[hidden] { display: none }`, so
     the Layers button set the hidden attribute and the panel stayed put
     while the grid collapsed to one column — the map appeared to close
     instead of the panel. */
  .results-col:not([hidden]) { display: flex; flex-direction: column; }
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
    border: 1px solid var(--dst-brand-line);
    border-radius: 7px;
    cursor: pointer;
  }
  .districtry-panel-foot .footer-link-btn:hover { background: var(--dst-brand-tint-soft); }
  .districtry-panel-foot .footer-metros { font-size: 11px; }
  .districtry-panel-foot .footer-metros a { color: var(--accent-deep); }
  /* ==== canvas app-shell layout (operator-directed: "Implement Districtry
     App.dc.html", 2026-08-20) ==== */
  /* search moves from floating-over-map into the masthead. The shell's own
     surface (panel fill + drop shadow) was drawn to float over a basemap; in
     a header it reads as a grey box around the field, so the shell goes
     invisible and the INPUT carries the affordance. */
  .masthead .map-toolbar { position: static; transform: none; flex: 1 1 320px; max-width: 560px; }
  .masthead .search-shell { position: relative; box-shadow: none; background: transparent; border-color: transparent; padding: 0; }
  .masthead .search-row input[type="text"] {
    background: var(--dst-sunken);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
  }
  .masthead .search-row input[type="text"]:focus-visible {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--dst-focus-tint);
  }
  .masthead .search-row input[type="text"]::placeholder { color: var(--slate-soft); }
  .masthead .search-row button { background: var(--accent); border-radius: 8px; }
  .masthead .search-row button:hover { background: var(--accent-deep); }
  /* Three more Chicago-flag literals found while auditing what a token swap
     cannot reach: the engine hardcodes #08406e / #094377 / rgba(11,83,148,…)
     as the HOVER state of three violet buttons, so each flashed Chicago navy
     on approach. Same class as the flag stripe and the star — a city color
     written as a literal, not a token. */
  .metro-portal-go:hover,
  .feedback-actions .btn-primary:hover { background: var(--accent-deep); }
  .share-copy-btn:hover { background: var(--dst-brand-tint-soft); }
  .masthead .search-extra {
    position: absolute;
    top: calc(100% + 6px);
    left: -1px;
    right: -1px;
    background: var(--panel);
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    box-shadow: 0 8px 24px var(--dst-shadow);
    padding: 8px;
    z-index: 900;
  }
  .masthead .search-shell:not(:hover):not(:focus-within):not(.expanded) .search-extra { padding: 0; border-width: 0; }
  /* The four "about the data" doors (operator-directed, two rounds): emoji
     dropped, and the row is no longer a bordered segmented box — that put a
     second hard rectangle beside the search field and gave four secondary
     links a toolbar's weight.

     The pill is the shape of an action here. "What data is missing?" wears
     one permanently and inverts to a solid fill on hover, because the repo's
     own note records that this button was promoted into the masthead as the
     standing caveat on every answer the app gives; its three peers are bare
     text that earn the same pill shape on approach. Hierarchy that matches
     the stated priority instead of flattening it. */
  .masthead-actions {
    border: none;
    background: none;
    overflow: visible;
    gap: 6px;
    align-items: center;
  }
  .masthead-action-link {
    border: 1px solid transparent;
    background: transparent;
    color: var(--slate);
    font-weight: 500;
    font-size: 12.5px;
    padding: 7px 13px;
    border-radius: 999px;
    letter-spacing: 0;
    transform: none;
    transition: background .15s ease, color .15s ease;
  }
  .masthead-action-link:hover,
  .masthead-action-link:focus-visible {
    background: var(--dst-brand-tint);
    color: var(--accent-deep);
    border-color: transparent;
    text-decoration: none;
    transform: none;
  }
  .masthead-actions .footer-link-btn {
    border: 1px solid var(--dst-brand-line);
    background: var(--dst-brand-tint-soft);
    color: var(--accent-deep);
    font-weight: 600;
    font-size: 12.5px;
    padding: 7px 14px;
    border-radius: 999px;
    margin-right: 6px;
    letter-spacing: 0;
    transform: none;
    transition: background .15s ease, color .15s ease, border-color .15s ease;
  }
  .masthead-actions .footer-link-btn:hover,
  .masthead-actions .footer-link-btn:focus-visible {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
    text-decoration: none;
    transform: none;
  }
  /* panel header bar: coords + Share on the left, the counts flush right —
     across from the Share button, at the page's own right edge. */
  .districtry-panel-head {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0 12px;
    margin: 0 0 12px;
    border-bottom: 1px solid var(--line);
    min-height: 30px;
  }
  .districtry-stats {
    margin-left: auto;
    font-size: 12px;
    color: var(--slate-soft);
    white-space: nowrap;
  }
  /* the selected-point chip becomes the results panel's header row (keep
     position:relative — it anchors the engine's share popover) */
  .districtry-panel-head .selected-point-chip {
    background: var(--panel);
    color: var(--ink);
    box-shadow: none;
    border-radius: 0;
    padding: 0;
    margin: 0;
  }
  .districtry-panel-head .selected-point-chip .copy-link-btn { color: var(--accent-deep); border-color: var(--dst-brand-line); }
  /* The share popover opens UPWARD off the chip because the chip used to sit
     at the map's bottom-left. Anchored at the panel's TOP that put the card
     above the viewport — open, unreachable, invisible. In the panel it opens
     downward and is clamped to the panel's width. */
  .districtry-panel-head .selected-point-chip .share-popover {
    top: calc(100% + 8px);
    bottom: auto;
    left: 0;
    right: 0;
    width: auto;
    max-width: none;
  }
  /* three-zone coverage treatment */
  .dst-glow { filter: blur(7px); }
  /* ==== map legend (operator-directed rebuild, 2026-08-20) ====
     Was a flat wrapping run of LOOSE swatches and labels, so a wrap could
     fall between a swatch and the label it defines — the blue dot ended one
     line and "Selected point" began the next. Each row is now a grid whose
     swatch and label cannot be separated, and the rows are stacked, so the
     defect is gone by construction rather than by picking a lucky width. */
  .districtry-map-legend .dml-items {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  .districtry-map-legend {
    display: block;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 1px 3px var(--dst-shadow-soft);
    font-size: 11.5px;
    color: var(--slate);
  }
  .districtry-map-legend .dml-mini { display: none; }
  .districtry-map-legend summary.dml-kicker::-webkit-details-marker { display: none; }
  .districtry-map-legend summary.dml-kicker {
    list-style: none;
    display: block;
    font-family: var(--font-display);
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--faint);
    /* 6, not 1: the kicker used to be a flex item of the legend card and took a
       5px `gap` from it. Now that .dml-items owns the flex column the summary
       sits outside it, so the gap has to be spelled out — without this the
       desktop legend tightens by 5px, which a pixel-diff catches and an eye
       does not. */
    margin-bottom: 6px;
  }
  /* swatch and label ride one grid row — a wrap can never split the pair */
  .districtry-map-legend .dml-item {
    display: grid;
    grid-template-columns: 10px auto;
    align-items: center;
    /* row-gap 2px, not 8: a shorthand gap would space the why-line as far from
       the label it belongs to as from the next legend row, leaving it
       visually orphaned between the two. */
    gap: 2px 8px;
  }
  .districtry-map-legend .dml-label { white-space: nowrap; }
  /* the "why" line under the partial-coverage swatch: the wash does NOT mean
     the county is empty — statewide layers answer there. It means this county's
     own districts are not sourced yet, which is the honest distinction. */
  .districtry-map-legend .dml-sub {
    grid-column: 2;
    margin-bottom: 3px;
    font-size: 10.5px;
    line-height: 1.35;
    color: var(--faint);
    max-width: 25ch;
    white-space: normal;
  }
  .districtry-map-legend .dml-rule { width: 100%; height: 1px; background: var(--line); margin: 3px 0 2px; }
  .districtry-map-legend .dml-glow { width: 9px; height: 9px; border-radius: 50%; flex: none; box-shadow: 0 0 5px 2.5px #ad8cee; }
  .districtry-map-legend .dml-sw { width: 9px; height: 9px; border-radius: 2px; flex: none; }
  .districtry-map-legend .dml-pending { background: #8a62e0; opacity: 0.25; }
  .districtry-map-legend .dml-out { background: #8d8a97; opacity: 0.55; }
  .districtry-map-legend .dml-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; background: #1d5fd6; }

  /* The chooser's own control. Hidden on desktop, where the panel scrolls
     independently and 39 rows cost nothing, and hidden whenever nothing is on,
     because there is then no shorter state to offer. */
  .dst-layer-toggle {
    display: none;
    width: 100%;
    margin: 14px 0 4px;
    padding: 13px 14px;
    min-height: 44px;
    font: 600 13px var(--font-body);
    color: var(--accent-deep);
    background: var(--dst-brand-tint-soft);
    border: 1px solid var(--dst-brand-line);
    border-radius: 8px;
    cursor: pointer;
    text-align: center;
  }
  .dst-layer-toggle:hover,
  .dst-layer-toggle:focus-visible { background: var(--dst-brand-tint); }
  .dst-layer-toggle[hidden] { display: none !important; }
  /* ==== the phone layout (mobile review, 2026-08-21) ====================
     Everything above this point is the desktop composition. Until now the
     re-skin's LAYOUT lived entirely in one @media (min-width: 901px) while its
     CHROME applied at every width, so a wide-screen composition was simply
     stacked onto a narrow one. Measured on a 375x667 phone: the masthead took
     247px (37% of the viewport), the first result card sat at y=847, and the
     map column — which the engine makes position:sticky below 900px — pinned
     500px of 667, leaving a 167px slot to read a 3,780px document through.

     The engine owns the sticky map, the 48vh height and this breakpoint (they
     are inside styles-core / styles-app fences and shared with the NYC and SF
     forks). Everything below is fork-local, overriding from OUTSIDE those
     fences at higher specificity — the blessed pattern, no engine release. */
  @media (max-width: 900px) {
    /* -- A. the coverage legend stops being pinned furniture ---------------
       .map-bottom-left is inside the sticky map column, so anything tall in it
       is on screen for the entire page. The engine reflowed that corner into a
       "slim static toolbar" on purpose — its own comment says a 48vh map is too
       short to float things over — and the legend had turned the slim strip
       into a 160px block. Closed, it is a chip beside the hover toggle. */
    .districtry-map-legend { padding: 5px 10px; }
    .districtry-map-legend summary.dml-kicker {
      display: flex;
      align-items: center;
      gap: 9px;
      margin-bottom: 0;
      min-height: 34px;
      cursor: pointer;
    }
    .districtry-map-legend .dml-mini { display: inline-flex; align-items: center; gap: 5px; }
    .districtry-map-legend[open] .dml-mini { display: none; }
    .districtry-map-legend .dml-items { padding: 6px 0 4px; }
    /* -- the map gives back 60px (operator-directed, 2026-08-21) ---------
       The engine sets #map to 48vh with a min-height of 340px. On a 375x667
       phone 48vh is 320, so the FLOOR is what binds — the shortest screens,
       where the space is scarcest, are the ones held to the tallest map. Even
       with A and B the first result card cleared the fold there by only 43px:
       its top edge, not its content.

       42vh / 260 was chosen off a measured ladder (48vh/340 -> card at y=624;
       42vh/260 -> 564; 38vh/240 -> 537). It is an override from OUTSIDE the
       styles-core fence that sets it, so it costs no engine release and does
       not reach the NYC or SF forks. Shortening the app's primary surface is a
       design decision, not a cleanup, which is why it was asked rather than
       assumed. */
    #map { height: 42vh; min-height: 260px; }

    /* -- C. lead with the answers (operator-approved) ---------------------
       39 cards stack vertically on a phone and the ones the reader has not
       picked dominate: with two layers on, 37 unanswered rows sit between
       them and the panel foot.

       C was approved as "show only the layers that answered". Implemented
       literally it would have been a REGRESSION, and the measurement is why:
       state.layersOn starts EMPTY — 39 cards, 0 checked, verified on a clean
       load — so a first-time visitor has no answers yet and would have met an
       empty panel. The layer list is not clutter in front of the app, it IS
       the way in.

       So the collapse is conditional: it applies only when the reader has at
       least one layer on, which is exactly when there is something to lead
       with. With none on, the chooser is the whole panel, as before.

       :has() does the hiding, so a card reappears the instant its box is
       ticked with no state to keep in sync. The engine's own error/empty-state
       rules already rely on :has(), so support is established here. */
    .results-col.dst-collapsed .layer-block:not(:has(input[type="checkbox"]:checked)) { display: none; }
    .results-col.dst-collapsed .group-section:not(:has(input[type="checkbox"]:checked)) { display: none; }
    .dst-layer-toggle { display: block; }

    /* -- B. a masthead in the shape of a phone ---------------------------
       The tagline and the preview stamp are explanation, and the empty state
       already carries the same sentence where a reader will actually meet it.
       The four "about the data" doors move into the results panel (see
       dstPlaceDoors) — they cannot fit on one row at 375px, and wrapped they
       cost 65px of permanently visible header. The theme toggle stays, lifted
       out of flow into the wordmark row so it costs no height at all. */
    h1.title small { display: none; }
    header.masthead { position: relative; }
    .masthead-actions {
      position: absolute;
      top: 10px;
      right: 14px;
      width: auto;
      padding-top: 0;
      margin: 0;
      gap: 0;
    }
    .districtry-toggle-sep { display: none; }
    /* -- tap targets. Every pill measured 29px against Apple's 44 and
       Material's 48dp; the row was sized for a mouse. */
    .districtry-theme-toggle,
    .masthead-action-link,
    .masthead-actions .footer-link-btn {
      min-height: 44px;
      display: inline-flex;
      align-items: center;
      padding-top: 0;
      padding-bottom: 0;
    }
    .masthead .search-row button { min-height: 44px; }
    .masthead .search-row input[type="text"] { min-height: 44px; }
    .locate-btn, .kbd-select-btn { min-height: 44px; }
    /* the doors, relocated: the first thing in the results panel rather than
       the last thing in the header. "What data is missing?" keeps its solid
       pill — the repo's own note records it as the standing caveat on every
       answer the app gives, so it should not be demoted by the move. */
    .districtry-doors {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 0 0 10px;
      margin: 0 0 10px;
      border-bottom: 1px solid var(--line);
    }
    .districtry-doors .masthead-action-link,
    .districtry-doors .footer-link-btn { min-height: 44px; }
  }
  /* ==== dark mode (operator-approved 2026-08-20 — the one function this
     re-skin ADDS rather than maintains) ====================================
     The design package decided the palette; this block wires it to the real
     app's token names. Everything is scoped to [data-theme="dark"] on <html>,
     which a head script sets before first paint, so there is no flash and no
     media query to keep in sync with the toggle.

     Three things needed explicit rules rather than a token swap, and they are
     the same lesson this preview keeps re-learning: a COLOR LITERAL IS
     INVISIBLE TO A TOKEN SWAP. The engine's white card/popover/tooltip
     surfaces, Leaflet's own chrome, and the map's per-layer stroke colors are
     all literals — each is handled below, and none of them by editing a
     fence. */
  :root[data-theme="dark"] {
    --accent: #a78bfa;
    /* "deep" means MORE CONTRAST AGAINST THE GROUND, not darker — on a dark
       ground that is lighter. Inverting this is why dark-mode links so often
       come out unreadable. */
    --accent-deep: #c4b0ff;
    /* the warm slot keeps its job (Public Safety group dot + focus ring) and
       its hue: #e879b9 is the design package's own dark value for the mark's
       third polygon, so the four group dots stay four distinct hues. */
    --accent-warm: #e879b9;
    --accent-warm-deep: #f0a3cf;
    --ink: #ece9f4;
    --slate: #b6b1c4;
    --slate-soft: #746e86;
    --faint: #746e86;
    --paper: #15131b;
    --panel: #201d29;
    --line: rgba(236, 233, 244, 0.10);
    --line-strong: rgba(236, 233, 244, 0.22);
    --ok: #5fd39b;
    --warn: #e0a33a;
    --err: #f2836f;
    --dst-brand-tint: rgba(167, 139, 250, 0.18);
    --dst-brand-tint-soft: rgba(167, 139, 250, 0.13);
    --dst-brand-line: rgba(167, 139, 250, 0.42);
    --dst-focus-tint: rgba(167, 139, 250, 0.24);
    --dst-ink-tint: rgba(236, 233, 244, 0.05);
    --dst-ink-tint-strong: rgba(236, 233, 244, 0.09);
    --dst-shadow: rgba(0, 0, 0, 0.55);
    --dst-shadow-soft: rgba(0, 0, 0, 0.4);
    --dst-sunken: #15131b;
    --dst-raised: #262331;
    --dst-raised-hover: #322e40;
    color-scheme: dark;
  }
  /* ---- the mark: multiply is a light-ground blend. On a dark ground the
     same three translucent polygons must SCREEN, and the "d" glyph inverts. */
  /* !important because the blend is an INLINE style attribute on each <g>
     (multiply is right on light paper), and inline beats every selector —
     this is the one case the keyword is the correct tool, not a shortcut.
     Without it the three polygons stayed multiply and vanished into the dark
     ground, leaving a bare "d". */
  :root[data-theme="dark"] .districtry-mark g,
  :root[data-theme="dark"] .districtry-empty-mark g { mix-blend-mode: screen !important; }
  :root[data-theme="dark"] .districtry-mark g:nth-of-type(1) polygon,
  :root[data-theme="dark"] .districtry-empty-mark g:nth-of-type(1) polygon { fill: #a78bfa; }
  :root[data-theme="dark"] .districtry-mark g:nth-of-type(2) polygon,
  :root[data-theme="dark"] .districtry-empty-mark g:nth-of-type(2) polygon { fill: #6ea8ff; }
  :root[data-theme="dark"] .districtry-mark g:nth-of-type(3) polygon,
  :root[data-theme="dark"] .districtry-empty-mark g:nth-of-type(3) polygon { fill: #e879b9; }
  :root[data-theme="dark"] .districtry-mark circle,
  :root[data-theme="dark"] .districtry-mark line { stroke: #ece9f4; }
  :root[data-theme="dark"] .districtry-empty-mark circle,
  :root[data-theme="dark"] .districtry-empty-mark line { stroke: #746e86; }
  /* ---- result cards. The card system is its own palette (--card-*), so it
     needs its own inversion; --card-accent/--card-link ARE the data tier and
     take the design package's dark data ramp rather than the chrome violet. */
  :root[data-theme="dark"] .layer-block {
    --card-accent: #6ea8ff;
    --card-link: #8db9ff;
    --card-link-hover: #b6d2ff;
    --card-ink: #ece9f4;
    --card-ink-2: #d4d0e0;
    --card-body-ink: #b6b1c4;
    --card-muted: #9a94ab;
    --card-detail-ink: #a9a3ba;
    --card-hint: #746e86;
    --card-sep: rgba(236, 233, 244, 0.22);
    --card-badge-bg: rgba(110, 168, 255, 0.18);
    --card-pill-bg: rgba(110, 168, 255, 0.10);
    --card-section-bg: #262331;
    --card-border: rgba(236, 233, 244, 0.10);
    --card-row-border: rgba(236, 233, 244, 0.06);
    --card-btn-border: rgba(110, 168, 255, 0.34);
    background: #201d29;
    border-color: rgba(236, 233, 244, 0.10);
    /* No color-mix on the stripe any more. --layer-accent is set from
       moduleColor(), which reads the layer's style object — now theme-aware —
       so the stripe carries the layer's real dark colour and matches the
       overlay exactly rather than approximating it with a different lift. */
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4),
      0 3px 14px -4px color-mix(in srgb, var(--layer-accent, var(--card-accent)) 30%, transparent);
  }
  :root[data-theme="dark"] .layer-block-head { background: #262331; }
  :root[data-theme="dark"] .layer-card-body .retry-btn,
  :root[data-theme="dark"] .card-footer .pin-parent-btn,
  :root[data-theme="dark"] .school-chip,
  :root[data-theme="dark"] .school-show-all { background: #262331; }
  :root[data-theme="dark"] .card-footer .pin-parent-btn:hover { background: #322e40; }
  :root[data-theme="dark"] .school-chip { border-color: rgba(236, 233, 244, 0.22); }
  :root[data-theme="dark"] .school-chip-dot { background: #4b4757; }
  /* error + empty states: #7c2d12 on #201d29 is unreadable, and the states
     are the one place a card MUST be legible. */
  [data-theme="dark"] .layer-block:has(> .layer-card-body.state-error) { border-left-color: #f97316; }
  [data-theme="dark"] .layer-block:has(> .layer-card-body.state-empty) { border-left-color: #4b4757; }
  [data-theme="dark"] .layer-card-body.state-error { color: #fdba74; }
  /* ---- app chrome the engine hardcodes as white/near-white surfaces */
  [data-theme="dark"] .map-col { background: #1c1a24; }
  [data-theme="dark"] .hover-toggle-btn,
  [data-theme="dark"] .pin-parent-btn,
  [data-theme="dark"] .rel-legend,
  [data-theme="dark"] .rel-unpin-btn { background: var(--dst-raised); }
  [data-theme="dark"] .hover-toggle-btn { border-color: rgba(236, 233, 244, 0.22); box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5); }
  [data-theme="dark"] .pin-parent-btn { border-color: rgba(110, 168, 255, 0.4); }
  [data-theme="dark"] .rel-unpin-btn { color: #f2a2a2; border-color: rgba(242, 162, 162, 0.4); }
  [data-theme="dark"] .rel-unpin-btn:hover { background: #3a2a30; }
  [data-theme="dark"] #geocode-results button:hover,
  [data-theme="dark"] #geocode-results button:focus-visible,
  [data-theme="dark"] .locate-btn:hover,
  [data-theme="dark"] .kbd-select-btn:hover,
  [data-theme="dark"] .metro-portal-stay:hover,
  [data-theme="dark"] .share-popover-close:hover,
  [data-theme="dark"] .feedback-actions .btn-secondary:hover,
  [data-theme="dark"] .pin-parent-btn:hover,
  [data-theme="dark"] .hover-toggle-btn:hover { background: var(--dst-raised-hover); }
  [data-theme="dark"] .share-popover { background: var(--panel); border-color: rgba(236, 233, 244, 0.14); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6); }
  [data-theme="dark"] .share-popover-url,
  [data-theme="dark"] .share-popover-embed { background: var(--dst-sunken); border-color: rgba(236, 233, 244, 0.16); color: var(--slate); }
  [data-theme="dark"] .layer-toggle-btn,
  [data-theme="dark"] .search-shell,
  [data-theme="dark"] .map-tile-banner { box-shadow: 0 4px 18px rgba(0, 0, 0, 0.55); }
  /* the pinned-parent outline is deliberately near-black (#14181C) so it reads
     as neutral over a light basemap; over a dark one it is simply gone. */
  [data-theme="dark"] .rel-parent-outline { stroke: #ece9f4; }
  [data-theme="dark"] .rel-sw-parent { border-top-color: #ece9f4; }
  [data-theme="dark"] .rel-sw-in { border-top-color: #6ea8ff; }
  [data-theme="dark"] .rel-sw-cross { border-top-color: #6ea8ff; }
  /* ---- the hover popup is its own small design and all of it is literal */
  [data-theme="dark"] .hover-popup .leaflet-popup-content-wrapper {
    background: var(--panel);
    color: var(--ink);
    border-color: rgba(236, 233, 244, 0.12);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.7), 0 1px 3px rgba(0, 0, 0, 0.5);
  }
  [data-theme="dark"] .hover-popup .leaflet-popup-tip {
    background: var(--panel);
    border-right-color: rgba(236, 233, 244, 0.12);
    border-bottom-color: rgba(236, 233, 244, 0.12);
  }
  [data-theme="dark"] .hover-popup.hover-below .leaflet-popup-tip {
    border-left-color: rgba(236, 233, 244, 0.12);
    border-top-color: rgba(236, 233, 244, 0.12);
  }
  [data-theme="dark"] .hover-row { border-bottom-color: rgba(236, 233, 244, 0.07); }
  [data-theme="dark"] .hover-dot-ring { background: var(--panel); border-color: rgba(236, 233, 244, 0.3); }
  [data-theme="dark"] .hover-row-label,
  [data-theme="dark"] .hover-poi-addr-text { color: #9a94ab; }
  [data-theme="dark"] .hover-row-who,
  [data-theme="dark"] .hover-poi-name,
  [data-theme="dark"] .hover-has-poi .hover-row-own .hover-row-who { color: var(--ink); }
  [data-theme="dark"] .hover-has-poi .hover-row-who,
  [data-theme="dark"] .hover-has-poi .hover-row-own .hover-row-label { color: var(--slate); }
  [data-theme="dark"] .hover-foot { border-top-color: rgba(236, 233, 244, 0.1); color: var(--faint); }
  [data-theme="dark"] .hover-pin-eye { background: var(--panel); }
  [data-theme="dark"] .hover-pin-sm { background: var(--faint); }
  /* ---- Leaflet's own chrome (leaflet.css is inlined in this app, so these
     are ordinary literals in the same stylesheet, not a third-party file) */
  [data-theme="dark"] .leaflet-container { background: #15131b; }
  [data-theme="dark"] .leaflet-tile { filter: brightness(1.35) saturate(0.92); }
  [data-theme="dark"] .leaflet-bar a { background-color: var(--dst-raised); color: var(--ink); border-bottom-color: rgba(236, 233, 244, 0.12); }
  [data-theme="dark"] .leaflet-bar a:hover,
  [data-theme="dark"] .leaflet-bar a:focus { background-color: var(--dst-raised-hover); color: var(--ink); }
  [data-theme="dark"] .leaflet-bar a.leaflet-disabled { background-color: var(--panel); color: #5b5668; }
  [data-theme="dark"] .leaflet-touch .leaflet-bar,
  [data-theme="dark"] .leaflet-touch .leaflet-control-layers { border-color: rgba(236, 233, 244, 0.18); }
  [data-theme="dark"] .leaflet-container .leaflet-control-attribution { background: rgba(21, 19, 27, 0.82); color: #9a94ab; }
  [data-theme="dark"] .leaflet-control-attribution a { color: var(--slate); }
  [data-theme="dark"] .leaflet-tooltip { background-color: var(--dst-raised); border-color: rgba(236, 233, 244, 0.14); color: var(--ink); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5); }
  [data-theme="dark"] .leaflet-tooltip-top:before { border-top-color: var(--dst-raised); }
  [data-theme="dark"] .leaflet-tooltip-bottom:before { border-bottom-color: var(--dst-raised); }
  [data-theme="dark"] .leaflet-tooltip-left:before { border-left-color: var(--dst-raised); }
  [data-theme="dark"] .leaflet-tooltip-right:before { border-right-color: var(--dst-raised); }
  [data-theme="dark"] .leaflet-popup-content-wrapper,
  [data-theme="dark"] .leaflet-popup-tip { background: var(--panel); color: var(--ink); }
  [data-theme="dark"] .leaflet-div-icon { background: var(--panel); border-color: rgba(236, 233, 244, 0.3); }
  /* ---- the map's own data is NOT restyled from here. It used to be: a
     brightness+saturate lift on the whole overlay pane, which was a stopgap and
     a poor one — a multiply cannot rescue a near-black, so the four worst layer
     colours stayed invisible under it. Each layer now carries a real derived
     dark colour instead (DST_DARK_MAP_COLORS, installed as getters on the layer
     style objects), so the pane is left alone. */
  /* the selection marker joins the dark data ramp. The circle selector cannot
     touch Chicago's flag star, which is a <path> and stays flag red. */
  [data-theme="dark"] .chi-star-marker circle { fill: #6ea8ff; }
  /* ---- masthead + panel chrome that reads off the tint tokens above */
  [data-theme="dark"] header.masthead { background: var(--panel); border-bottom-color: var(--line); }
  [data-theme="dark"] .masthead .search-row input[type="text"] { background: var(--dst-sunken); color: var(--ink); }
  [data-theme="dark"] .masthead .search-extra { background: var(--panel); border-color: var(--line-strong); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55); }
  [data-theme="dark"] .districtry-map-legend { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.45); }
  [data-theme="dark"] .districtry-map-legend .dml-glow { box-shadow: 0 0 5px 2.5px #a78bfa; }
  [data-theme="dark"] .districtry-map-legend .dml-pending { background: #a78bfa; }
  /* the out-of-Illinois wash is a DARKENING in dark mode, so its swatch is a
     near-black chip that needs a hairline to be visible on the panel at all */
  [data-theme="dark"] .districtry-map-legend .dml-out { background: #0b0a10; opacity: 1; box-shadow: inset 0 0 0 1px rgba(236, 233, 244, 0.25); }
  [data-theme="dark"] .districtry-map-legend .dml-dot { background: #6ea8ff; }
  /* ---- the toggle itself */
  .districtry-theme-toggle {
    border: 1px solid transparent;
    background: transparent;
    color: var(--slate);
    font-family: inherit;
    font-weight: 500;
    font-size: 12.5px;
    /* the pills beside it inherit line-height 12.5px from the row; a button's
       UA default is `normal`, which made this one 30px against their 28.5px
       and pushed the whole app down a pixel. Matched, so adding a control to
       the row costs no layout. */
    line-height: 12.5px;
    padding: 7px 13px;
    border-radius: 999px;
    cursor: pointer;
    transition: background .15s ease, color .15s ease;
  }
  .districtry-theme-toggle:hover,
  .districtry-theme-toggle:focus-visible {
    background: var(--dst-brand-tint);
    color: var(--accent-deep);
  }
  /* a hairline before it: the four pills to its left are doors to content;
     this is a control, and the rule says so without adding another box. */
  .districtry-toggle-sep {
    width: 1px;
    height: 18px;
    background: var(--line-strong);
    margin: 0 2px;
    flex: none;
  }
</style>
"""


# Installed at the very end of the script, where every registerLayer() call has
# already run. GETTERS, not a swap: baseStyleFor() — the engine's single funnel
# for every path it paints — and moduleColor() — the card accent, the sidebar
# dot, the hover swatch — both read mod.overlay.style directly, so making the
# property itself theme-aware makes every one of those reads correct with no
# engine edit and no second copy of the state to keep in sync.
DARK_PALETTE_INSTALL_JS = """  /* ==== per-layer dark map palette ==================================== */
  function dstDarkColor(hex) {
    if (typeof hex !== "string") return hex;
    return DST_DARK_MAP_COLORS[hex.toUpperCase()] || hex;
  }
  function dstThemeColorProp(obj, key) {
    if (!obj) return;
    var light = obj[key];
    if (typeof light !== "string" || light.charAt(0) !== "#") return;
    var dark = dstDarkColor(light);
    if (dark === light) return;
    Object.defineProperty(obj, key, {
      get: function () { return dstDark ? dark : light; },
      /* a setter too, so an assignment anywhere degrades to plain data instead
         of throwing on a getter-only property in strict mode */
      set: function (v) { light = v; dark = dstDarkColor(v); },
      enumerable: true,
      configurable: true
    });
  }
  (function () {
    for (var i = 0; i < layers.length; i++) {
      var mod = layers[i];
      var st = mod.overlay && mod.overlay.style;
      if (st) { dstThemeColorProp(st, "color"); dstThemeColorProp(st, "fillColor"); }
      /* nearest-N point layers carry no flat style object; mod.color is what
         moduleColor() falls back to for their card accent */
      if (mod.color) dstThemeColorProp(mod, "color");
    }
    /* the School Location layer colour-codes every footprint from this table */
    if (typeof SCHOOL_CAT_META === "object" && SCHOOL_CAT_META) {
      for (var k in SCHOOL_CAT_META) {
        if (Object.prototype.hasOwnProperty.call(SCHOOL_CAT_META, k)) {
          dstThemeColorProp(SCHOOL_CAT_META[k], "color");
        }
      }
    }
  })();
  /* The selection highlight is "the layer's own colour, shifted away from it so
     the matched region pops". The engine spells that DARKEN, which is right on
     light paper and exactly backwards on a dark map, where a darker outline
     recedes into the ground instead of standing out. Rebound rather than
     edited: darkenHexColor is a FENCED engine function, but a function
     declaration's binding is writable from fork-local code, so this costs no
     fence edit. At adoption the honest fix is for the engine to shift away from
     the GROUND rather than toward black. */
  var dstEngineDarken = darkenHexColor;
  darkenHexColor = function (hex, amount) {
    if (!dstDark) return dstEngineDarken(hex, amount);
    var m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(hex || "");
    if (!m) return hex;
    var h = m[1];
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var num = parseInt(h, 16);
    var up = function (c) { return Math.round(c + (255 - c) * amount); };
    return "#" + (0x1000000 + up((num >> 16) & 255) * 0x10000 +
                  up((num >> 8) & 255) * 0x100 + up(num & 255)).toString(16).slice(1);
  };
"""


MOBILE_LAYOUT_JS = """  /* ==== C: lead with the answers ======================================
     Collapse the layers the reader has not picked, but ONLY when they have
     picked something — see the CSS above for why an unconditional version
     would have handed a first-time visitor an empty panel. */
  function dstLayerCounts() {
    var root = document.getElementById("groups-root");
    if (!root) return null;
    return {
      all: root.querySelectorAll(".layer-block").length,
      on: root.querySelectorAll('input[type="checkbox"]:checked').length
    };
  }
  function dstSyncLayerChooser() {
    var col = document.querySelector(".results-col");
    var btn = document.querySelector(".dst-layer-toggle");
    var counts = dstLayerCounts();
    if (!col || !btn || !counts) return;
    /* nothing on -> nothing to collapse to, so the control has no meaning */
    if (!counts.on) {
      col.classList.remove("dst-collapsed");
      btn.hidden = true;
      return;
    }
    btn.hidden = false;
    var collapsed = col.classList.contains("dst-collapsed");
    btn.textContent = collapsed
      ? "Show all " + counts.all + " layers"
      : "Show only my " + counts.on + (counts.on === 1 ? " layer" : " layers");
    btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  }
  (function () {
    var root = document.getElementById("groups-root");
    var col = document.querySelector(".results-col");
    if (!root || !col) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dst-layer-toggle";
    btn.hidden = true;
    root.parentNode.insertBefore(btn, root.nextSibling);
    btn.addEventListener("click", function () {
      col.classList.toggle("dst-collapsed");
      dstSyncLayerChooser();
    });
    /* a tick anywhere in the list changes both counts and, when it is the
       first one, whether the control means anything at all */
    root.addEventListener("change", function (e) {
      if (e.target && e.target.type === "checkbox") {
        /* the first layer a reader turns on is the moment there is something
           to lead with, so that is when the panel collapses to it */
        if (!col.classList.contains("dst-collapsed") && dstLayerCounts().on === 1 && dstIsPhone()) {
          col.classList.add("dst-collapsed");
        }
        dstSyncLayerChooser();
      }
    });
    /* a permalink arrives with layers already on: lead with them */
    if (dstIsPhone() && (dstLayerCounts() || {}).on) col.classList.add("dst-collapsed");
    dstSyncLayerChooser();
  })();
  /* ==== phone layout (mobile review, 2026-08-21) ======================== */
  function dstIsPhone() {
    return !!(window.matchMedia && window.matchMedia("(max-width: 900px)").matches);
  }
  /* The legend is authored open, which is what desktop wants. On a phone it is
     pinned inside the sticky map column, so it starts closed. Driven here
     rather than in CSS because `open` is an attribute, not a style. */
  function dstSyncLegendDisclosure() {
    var legend = document.querySelector(".districtry-map-legend");
    if (!legend) return;
    if (dstIsPhone()) legend.removeAttribute("open");
    else legend.setAttribute("open", "");
  }
  /* The four "about the data" doors move between the masthead and the top of
     the results panel as the viewport crosses the breakpoint. They are moved,
     never duplicated: two copies of #gaps-btn would break the engine's
     getElementById binding. Order is preserved by re-inserting before the
     theme toggle's separator on the way back. */
  function dstPlaceDoors() {
    var actions = document.querySelector(".masthead-actions");
    var foot = document.querySelector(".districtry-panel-foot");
    if (!actions || !foot) return;
    var doors = document.querySelector(".districtry-doors");
    if (dstIsPhone()) {
      if (!doors) {
        doors = document.createElement("div");
        doors.className = "districtry-doors";
        /* The panel FOOT, not the panel head. Measured: the four doors are a
           107px block at 375px, and at the top of the panel they sit between
           the reader's coordinates and the reader's answer — on a 393x852
           phone that is the difference between 48px of the first card showing
           and 155px of it. The cost is real and named: "What data is missing?"
           loses on mobile the promoted position it was deliberately given in
           the masthead. */
        foot.insertBefore(doors, foot.firstChild);
      }
      var move = actions.querySelectorAll("#gaps-btn, .masthead-action-link");
      for (var i = 0; i < move.length; i++) doors.appendChild(move[i]);
    } else if (doors) {
      var sep = actions.querySelector(".districtry-toggle-sep");
      var back = doors.querySelectorAll("#gaps-btn, .masthead-action-link");
      for (var j = 0; j < back.length; j++) actions.insertBefore(back[j], sep);
      doors.parentNode.removeChild(doors);
    }
  }
  function dstApplyPhoneLayout() {
    dstPlaceDoors();
    dstSyncLegendDisclosure();
    /* crossing INTO the phone layout with layers already on should lead
       with them; crossing out leaves the class harmless (the CSS that
       reads it is inside the mobile media query). */
    var col = document.querySelector(".results-col");
    var counts = dstLayerCounts();
    if (col && counts && dstIsPhone() && counts.on) col.classList.add("dst-collapsed");
    dstSyncLayerChooser();
  }
  dstApplyPhoneLayout();
  if (window.matchMedia) {
    var dstPhoneMQ = window.matchMedia("(max-width: 900px)");
    if (dstPhoneMQ.addEventListener) dstPhoneMQ.addEventListener("change", dstApplyPhoneLayout);
    else if (dstPhoneMQ.addListener) dstPhoneMQ.addListener(dstApplyPhoneLayout);
  }
"""

# The theme is decided BEFORE FIRST PAINT, which is the whole reason this is a
# blocking inline script in the head rather than part of the app boot: deferring
# one attribute is a flash of the wrong ground on every single load. An explicit
# choice wins and is remembered; with none on record the OS preference decides,
# because a reader whose machine already says "dark" should not have to say it
# again.
THEME_BOOT_JS = """<script>
  (function () {
    var t = "light";
    try {
      var stored = localStorage.getItem("districtry-theme");
      if (stored === "dark" || stored === "light") t = stored;
      else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) t = "dark";
    } catch (e) { /* blocked storage (private mode) — light is the safe ground */ }
    document.documentElement.setAttribute("data-theme", t);
  })();
</script>
"""

# CSS handles every surface that reads a token. This owns the four it cannot:
# the basemap tiles, the coverage wash (drawn once in JS at idle, so it is
# RESTYLED rather than re-drawn), the browser chrome color, and the toggle's own
# label. Inserted at the fork-local tile-layer site so it closes over baseTiles.
THEME_CONTROLLER_JS = """
  /* ==== theme controller (preview-only) ================================== */
  /* The dark counterpart of every layer stroke/fill in the app, derived at
     build time — see dark_map_palette() above for the method and for why the
     obvious minimum-lift was measured and rejected. */
  var DST_DARK_MAP_COLORS = __DARK_PALETTE__;
  var districtryCoverageLayers = {};
  var districtryTileKind = "light_all";
  function styleDistrictryCoverage(dark) {
    /* values are the design canvas's own (Districtry App.dc.html
       styleOverlays): outside-Illinois DARKENS on a dark ground where it
       greys on a light one, and the violet "data coming" wash lifts. */
    var c = districtryCoverageLayers;
    if (c.outMask) {
      c.outMask.setStyle({
        fillColor: dark ? "#08070c" : "#8d8a97",
        fillOpacity: c.fallbackMask ? (dark ? 0.32 : 0.35) : (dark ? 0.38 : 0.42)
      });
    }
    if (c.pending) c.pending.setStyle({ fillColor: dark ? "#a78bfa" : "#8a62e0", fillOpacity: dark ? 0.10 : 0.08 });
    if (c.glow) c.glow.setStyle({ color: dark ? "#a78bfa" : "#ad8cee", opacity: dark ? 0.55 : 0.6 });
    if (c.stateLine) c.stateLine.setStyle({ color: dark ? "#a78bfa" : "#ad8cee" });
  }
  /* Cached, and deliberately so: the layer-colour getters below sit on the
     PAINT path — baseStyleFor() reads two of them per path, and a full repaint
     runs over every path of every active layer. Reading an attribute off the
     DOM there would put a document access inside the loop this repo has twice
     optimised (P7, P8). The flag is refreshed by applyDistrictryTheme, which is
     the only thing that changes the theme. */
  var dstDark = document.documentElement.getAttribute("data-theme") === "dark";
  function districtryTheme() {
    return dstDark ? "dark" : "light";
  }
  /* A theme flip moves every layer colour, so every painted path and every
     rendered card accent is stale. Repaint through the ENGINE'S OWN paths
     rather than reimplementing them: updateLayerHighlight() already handles
     the three cases (a matched region, no selection, a per-feature-styled
     layer) and re-derives each from baseStyleFor(), which now reads the
     theme-aware colours. Hoisted, so applyDistrictryTheme above can call it. */
  function dstRepaintLayers() {
    if (typeof layers === "undefined" || !layers || !layers.length) return;
    for (var i = 0; i < layers.length; i++) {
      var mod = layers[i];
      /* the card accent + dot, for every card on screen, active or not */
      var cb = document.getElementById("toggle-" + mod.id);
      var block = cb && cb.closest ? cb.closest(".layer-block") : null;
      if (block) block.style.setProperty("--layer-accent", moduleColor(mod));
      var rt = layerRuntime && layerRuntime[mod.id];
      if (!rt || !rt.overlayLayer) continue;
      /* force the full sweep: the P7 fast path repaints only the two paths
         whose match role changed, and here every path's colour moved */
      rt.highlightApplied = false;
      updateLayerHighlight(mod);
    }
  }
  function applyDistrictryTheme(theme, remember) {
    var dark = theme === "dark";
    dstDark = dark;
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    if (remember) {
      try { localStorage.setItem("districtry-theme", dark ? "dark" : "light"); } catch (e) {}
    }
    var kind = dark ? "dark_all" : "light_all";
    if (kind !== districtryTileKind) {
      districtryTileKind = kind;
      baseTiles.setUrl("https://{s}.basemaps.cartocdn.com/" + kind + "/{z}/{x}/{y}{r}.png");
    }
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", dark ? "#15131b" : "#6d3fd1");
    styleDistrictryCoverage(dark);
    dstRepaintLayers();
    var btn = document.querySelector(".districtry-theme-toggle");
    if (btn) {
      /* the label names what the button DOES, not the state it is in */
      btn.textContent = dark ? "Light" : "Dark";
      btn.setAttribute("aria-label", dark ? "Switch to the light theme" : "Switch to the dark theme");
    }
  }
  (function () {
    var btn = document.querySelector(".districtry-theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        applyDistrictryTheme(districtryTheme() === "dark" ? "light" : "dark", true);
      });
    }
    /* the head script already set the attribute; this hands the same decision
       to the surfaces CSS cannot reach — the tiles above all — without
       remembering a choice the reader has not made */
    applyDistrictryTheme(districtryTheme(), false);
    /* and while no choice is on record, keep following the OS */
    var mq = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
    if (mq && mq.addEventListener) {
      mq.addEventListener("change", function (e) {
        var chosen = null;
        try { chosen = localStorage.getItem("districtry-theme"); } catch (err) {}
        if (chosen !== "dark" && chosen !== "light") applyDistrictryTheme(e.matches ? "dark" : "light", false);
      });
    }
  })();
"""


# The canvas's three-zone coverage treatment, replacing the engine's single
# out-of-coverage wash AT ITS FORK-LOCAL CALL SITE (the whenIdle line is fork
# code; the scope-mask ENGINE fence is untouched). Contract preserved:
# coverageMaskRings is still set from coverageOutlineRings(feats), so the
# engine's point-in-coverage test keeps working. Decorative like the original:
# every failure path skips silently. Values are the canvas's (Districtry
# App.dc.html initMap): gray outside Illinois, violet "data coming" wash on
# in-state unserved ground, glow + hairline on the state border.
COVERAGE_JS = """  function drawDistrictryCoverage() {
    var stateUrl = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/0/query?where=" +
      encodeURIComponent("STUSAB='IL'") + "&outFields=NAME&returnGeometry=true&geometryPrecision=3&outSR=4326&f=geojson";
    var covP = loadMetroOutline().catch(function () { return null; });
    // decorative: fail fast (one retry, short timeout) so an unreachable
    // TIGERweb degrades to the single-wash fallback quickly
    var stP = fetchJSONWithRetry(stateUrl, { timeoutMs: 6000 }, 1).catch(function () { return null; });
    Promise.all([covP, stP]).then(function (res) {
      var covGeo = res[0], stGeo = res[1];
      var covFeats = (covGeo && covGeo.features) || [];
      if (!covFeats.length) return;
      var outline = coverageOutlineRings(covFeats);
      if (!outline || !outline.length) {
        outline = [];
        for (var i = 0; i < covFeats.length; i++) {
          var geom = covFeats[i].geometry;
          if (!geom) continue;
          var polys = geom.type === "Polygon" ? [geom.coordinates]
                    : geom.type === "MultiPolygon" ? geom.coordinates : [];
          for (var p = 0; p < polys.length; p++) {
            for (var r = 0; r < polys[p].length; r++) outline.push(polys[p][r]);
          }
        }
      }
      coverageMaskRings = outline;
      var covLatLng = [];
      for (var j = 0; j < outline.length; j++) {
        var src = outline[j], ring = [];
        for (var v = 0; v < src.length; v++) ring.push([src[v][1], src[v][0]]);
        covLatLng.push(ring);
      }
      var world = [[-89, -720], [89, -720], [89, 720], [-89, 720]];
      var stateRing = null;
      if (stGeo && stGeo.features && stGeo.features[0] && stGeo.features[0].geometry) {
        var g = stGeo.features[0].geometry;
        var raw = null;
        if (g.type === "Polygon") raw = g.coordinates[0];
        else if (g.type === "MultiPolygon") {
          for (var m = 0; m < g.coordinates.length; m++) {
            if (!raw || g.coordinates[m][0].length > raw.length) raw = g.coordinates[m][0];
          }
        }
        if (raw && raw.length > 3) {
          stateRing = [];
          for (var s = 0; s < raw.length; s++) stateRing.push([raw[s][1], raw[s][0]]);
        }
      }
      if (stateRing) {
        districtryCoverageLayers.outMask = L.polygon([world, stateRing], { pane: "scope-mask", stroke: false, fillColor: "#8d8a97", fillOpacity: 0.42, interactive: false }).addTo(map);
        districtryCoverageLayers.pending = L.polygon([stateRing].concat(covLatLng), { pane: "scope-mask", stroke: false, fillColor: "#8a62e0", fillOpacity: 0.08, interactive: false }).addTo(map);
        var closed = stateRing.concat([stateRing[0]]);
        districtryCoverageLayers.glow = L.polyline(closed, { pane: "scope-mask", className: "dst-glow", color: "#ad8cee", weight: 9, opacity: 0.6, interactive: false }).addTo(map);
        districtryCoverageLayers.stateLine = L.polyline(closed, { pane: "scope-mask", color: "#ad8cee", weight: 1.5, opacity: 0.9, interactive: false }).addTo(map);
      } else {
        districtryCoverageLayers.outMask = L.polygon([world].concat(covLatLng), { pane: "scope-mask", stroke: false, fillColor: "#8d8a97", fillOpacity: 0.35, interactive: false }).addTo(map);
        districtryCoverageLayers.fallbackMask = true;
      }
      /* the wash draws at idle, long after boot — in dark mode it would
         otherwise paint its light-ground colors and stay that way until the
         next toggle */
      styleDistrictryCoverage(districtryTheme() === "dark");
      var host = document.querySelector(".map-bottom-left");
      if (host && !document.querySelector(".districtry-map-legend")) {
        /* A <details>, not a <div>: on desktop it is open and looks exactly as
           it did (marker hidden, summary styled as the kicker); below 900px the
           engine drops this whole corner into a static strip INSIDE the sticky
           map column, so an open 143px legend is pinned to the screen for the
           whole page. Closed it is a ~32px chip, and the "why" line survives one
           tap away rather than being cut. */
        var legend = document.createElement("details");
        legend.className = "districtry-map-legend";
        legend.open = true;
        legend.innerHTML = '<summary class="dml-kicker">Coverage' +
            '<span class="dml-mini" aria-hidden="true">' +
              '<span class="dml-glow"></span><span class="dml-sw dml-pending"></span>' +
              '<span class="dml-sw dml-out"></span><span class="dml-dot"></span>' +
            '</span></summary>' +
          '<div class="dml-items">' +
          '<span class="dml-item"><span class="dml-glow"></span>' +
            '<span class="dml-label">IL</span></span>' +
          '<span class="dml-item"><span class="dml-sw dml-pending"></span>' +
            '<span class="dml-label">Statewide layers only</span>' +
            '<span class="dml-sub">County board and local districts not sourced yet</span></span>' +
          '<span class="dml-item"><span class="dml-sw dml-out"></span>' +
            '<span class="dml-label">Outside IL</span></span>' +
          '<span class="dml-rule"></span>' +
          '<span class="dml-item"><span class="dml-dot"></span>' +
            '<span class="dml-label">Selected point</span></span>' +
          '</div>';
        host.insertBefore(legend, host.firstChild);
        dstSyncLegendDisclosure();
      }
    }).catch(function () { /* decorative — skip the wash, never surface an error */ });
  }
  // still off the boot critical path, but with an idle TIMEOUT — plain
  // requestIdleCallback can be starved indefinitely while tiles and layer
  // fetches keep the loop busy, and a coverage wash that may never draw is
  // worse than one that costs a frame
  if (window.requestIdleCallback) {
    window.requestIdleCallback(drawDistrictryCoverage, { timeout: 4000 });
  } else {
    setTimeout(drawDistrictryCoverage, 800);
  }
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
<title>districtry / il — common questions (unlisted preview)</title>
<link rel="icon" type="image/svg+xml" href="districtry/icons/favicon.svg">
<link rel="stylesheet" href="districtry/tokens/districtry.tokens.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
__THEME_BOOT__<style>
  /* the linked token sheet already carries the [data-theme="dark"] palette, so
     this page needs only the boot script above and a toggle of its own —
     a reader who picks dark on the map should not arrive here in daylight */
  :root { color-scheme: light; }
  :root[data-theme="dark"] { color-scheme: dark; }
  body { margin: 0; background: var(--paper); color: var(--ink); font: 400 15px/1.6 var(--font-body); }
  .wrap { max-width: 760px; margin: 0 auto; padding: 32px 24px 64px; }
  .mast { display: flex; align-items: baseline; gap: 8px; padding-bottom: 18px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
  .mast .wordmark { font: var(--font-heading-weight) 28px/1 var(--font-heading); letter-spacing: .005em; color: var(--ink); text-decoration: none; }
  .mast .tag { font: 400 22px/1 var(--font-heading); color: var(--faint); }
  .back { font-size: 13px; }
  .faq-theme-toggle {
    margin-left: auto;
    border: 1px solid transparent;
    background: transparent;
    color: var(--muted);
    font: 500 12.5px var(--font-body);
    padding: 6px 12px;
    border-radius: 999px;
    cursor: pointer;
  }
  .faq-theme-toggle:hover,
  .faq-theme-toggle:focus-visible { background: var(--brand-tint); color: var(--brand); }
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
    <span class="tag">/ il</span>
    <span class="tag">/ faq</span>
    <button type="button" class="faq-theme-toggle" aria-label="Switch to the dark theme">Dark</button>
  </div>
  <p class="back"><a href="districtry-app.html">← Back to the map</a></p>
  __FAQ_SECTION__
  <footer>Unlisted re-skin preview. <strong>Not for legal or official use.</strong> Boundary and roster
  data come from public sources that disclaim legal precision. __STAMP__</footer>
</div>
<script>
  (function () {
    var btn = document.querySelector(".faq-theme-toggle");
    function paint() {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      btn.textContent = dark ? "Light" : "Dark";
      btn.setAttribute("aria-label", dark ? "Switch to the light theme" : "Switch to the dark theme");
    }
    btn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("districtry-theme", next); } catch (e) {}
      paint();
    });
    paint();
  })();
</script>
</body>
</html>
"""


# Geocoder labels carry the state in full; the preview abbreviates to the USPS
# code. Unknown values pass through unchanged — a geocoder that answers with
# something unexpected should print what it said, not swallow it.
STATE_CODE_JS = """  var US_STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "Puerto Rico": "PR"
  };
  function stateCode(name) {
    if (!name) return name;
    return US_STATE_CODES[name] || name;
  }
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
        "<title>districtry / il — working preview (unlisted)</title>",
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
        '<span class="title-text">districtry <span class="title-metro">/ il</span></span>',
        "wordmark",
    )
    html = sub_once(
        html,
        "<small>Click the map or search an address to see every district that covers it, and who represents it.</small>",
        "<small>Click the map or search an address to see every district that covers it, and who represents it."
        '<span class="preview-stamp">' + stamp_text + "</span></small>",
        "generation stamp",
    )

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
        # No Sources link here: the masthead pill already carries that door,
        # and the OSM attribution below is a licence obligation, not a repeat.
        '      <div class="dpf-links">\n'
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

    # -- canvas app-shell layout ("Implement Districtry App.dc.html").
    #    (a) The search toolbar RELOCATES from floating-over-the-map into the
    #    masthead (the geocoder binds #geocode-form/#geocode-input/… by id, so
    #    the block moves verbatim, never duplicates).
    toolbar_re = re.compile(r'[ ]*<div class="map-toolbar">.*?\n    </div>\n', re.S)
    toolbars = toolbar_re.findall(html)
    if len(toolbars) != 1:
        sys.exit("build-districtry-preview: FAIL — map-toolbar matched %d times" % len(toolbars))
    toolbar = toolbars[0].strip()
    html = toolbar_re.sub("", html, count=1)
    html = sub_once(html, "</h1>", "</h1>\n    " + toolbar, "toolbar into masthead")

    #    (b) The header stat row, counts read from the repo's own generated
    #    surfaces at build time so a new county updates it on regeneration.
    county_count = "69"
    try:
        status = io.open(os.path.join(REPO_ROOT, "docs", "COUNTY_STATUS.md"), encoding="utf-8").read()
        m2 = re.search(r"\*\*(\d+) of \d+ Illinois counties are served\*\*", status)
        if m2:
            county_count = m2.group(1)
    except OSError:
        pass
    layer_count = "39"
    try:
        worksheet = json.load(io.open(os.path.join(REPO_ROOT, "metro-worksheet.json"), encoding="utf-8"))
        layer_count = str(len(worksheet.get("layers", []))) or layer_count
    except (OSError, ValueError):
        pass
    #    The FAQ joins the masthead pills (operator-directed) — it was a link
    #    buried in the panel foot, which is no place for one of the four
    #    "about the data" doors.
    html = sub_once(
        html,
        '<a class="masthead-action-link" href="https://overberg.co/why/"',
        '<a class="masthead-action-link" href="./districtry-faq.html">Common questions</a>\n'
        '      <a class="masthead-action-link" href="https://overberg.co/why/"',
        "FAQ pill",
    )

    #    (c) The selected-point chip and the stat row become the results
    #    panel's header bar: coords + Share on the left, counts flush to the
    #    page's right edge across from them. The stats live OUTSIDE the chip
    #    because the chip is hidden until a point is selected and the counts
    #    are true either way.
    chip = '<div class="selected-point-chip" id="point-chip" hidden></div>'
    html = sub_once(html, "      " + chip + "\n", "", "point chip cut")
    html = sub_once(
        html,
        '<div id="main-content" tabindex="-1"></div>',
        '<div class="districtry-panel-head">\n      '
        + chip
        + '\n      <span class="districtry-stats">'
        + county_count + " counties · " + layer_count + " layers</span>\n"
        + "    </div>\n"
        + '    <div id="main-content" tabindex="-1"></div>',
        "panel head (chip + stats)",
    )

    #    (b2) Search field: Illinois-wide prompt (the app is no longer a
    #    Chicago-only tool), and the three "about the data" pills lose their
    #    emoji. NOTE for adoption: the gaps label lives INSIDE the gaps-html
    #    ENGINE fence. Editing it is safe here only because this copy is never
    #    deploy-spliced — in production that same edit is an engine release
    #    (or the label becomes a config string).
    html = sub_once(
        html,
        'placeholder="Search a Chicago address…"',
        'placeholder="Search an Illinois address"',
        "search placeholder",
    )
    for emoji_label, plain in (
        ("🧩 What data is missing?", "What data is missing?"),
        ("📚 Sources &amp; data layers", "Sources &amp; data layers"),
        ("💡 Why this exists", "Why this exists"),
    ):
        html = sub_once(html, ">" + emoji_label + "<", ">" + plain + "<", "pill label " + plain)

    #    (b2) Dark mode joins the pill row as a CONTROL, not a fifth door. A
    #    hairline separates it from the four "about the data" links, and it is
    #    text-only because the operator's standing instruction for this row is
    #    that its pills carry no icons — a sun/moon glyph would walk that back.
    #    The label names what the button DOES ("Dark" while light), which is
    #    also the design canvas's own semantics.
    html = sub_once(
        html,
        ">Why this exists</a>",
        ">Why this exists</a>\n"
        '      <span class="districtry-toggle-sep" aria-hidden="true"></span>\n'
        '      <button type="button" class="districtry-theme-toggle" '
        'aria-label="Switch to the dark theme">Dark</button>',
        "theme toggle button",
    )

    #    ...and the controller that owns what CSS cannot: tiles, the coverage
    #    wash, the chrome color. Anchored on the fork-local tile-layer site so
    #    it closes over baseTiles and map.
    html = sub_once(
        html,
        "  }).addTo(map);\n\n  /* ---------- base-map tile-failure notice (R6) ----------",
        "  }).addTo(map);\n" + THEME_CONTROLLER_JS.replace(
            "__DARK_PALETTE__",
            json.dumps(dark_map_palette(html), indent=None, sort_keys=True),
        ) +
        "\n  /* ---------- base-map tile-failure notice (R6) ----------",
        "theme controller",
    )

    #    (b4) The School Location chips mix each type's colour toward a dark ink
    #    to make readable text. meta.color is theme-aware via the palette getters
    #    below, but the INK ANCHOR is a literal — on a dark chip it darkens the
    #    label instead of lightening it. Fork-local line; same "deep means more
    #    contrast, not darker" correction as --accent-deep.
    html = sub_once(
        html,
        '"color-mix(in srgb, " + meta.color + " 55%, #1f2937)"',
        '"color-mix(in srgb, " + meta.color + " 55%, " + (dstDark ? "#f3f4f6" : "#1f2937") + ")"',
        "school chip ink anchor",
    )

    #    the exports object is assigned OUTSIDE the exports fence (the window
    #    property is fork-branded), so extending it here touches no engine text.
    html = sub_once(
        html,
        "  window.ChiExplorer = EXPLORER_EXPORTS;",
        "  window.ChiExplorer = EXPLORER_EXPORTS;\n"
        "  // preview-only: lets a check drive the theme without a click\n"
        "  EXPLORER_EXPORTS.setTheme = applyDistrictryTheme;\n"
        "  EXPLORER_EXPORTS.getTheme = districtryTheme;\n"
        + DARK_PALETTE_INSTALL_JS
        + MOBILE_LAYOUT_JS,
        "theme exports + dark map palette",
    )

    #    (b3) Geocoder results name the state in full ("…, Springfield,
    #    Illinois, 62701"). The app answers statewide and will answer in more
    #    states, so the label carries the USPS code instead. photonLabel sits
    #    outside every ENGINE fence, so this is a fork-local edit.
    html = sub_once(
        html,
        "    if (p.state) parts.push(p.state);\n",
        "    if (p.state) parts.push(stateCode(p.state));\n",
        "photon state code",
    )
    html = sub_once(
        html,
        "  function photonLabel(p) {\n",
        STATE_CODE_JS + "  function photonLabel(p) {\n",
        "state code helper",
    )

    #    (d) The three-zone coverage treatment replaces the engine wash at its
    #    fork-local call site (the scope-mask ENGINE fence itself is untouched;
    #    coverageMaskRings stays set — see COVERAGE_JS).
    html = sub_once(
        html,
        "  whenIdle(function () { drawOutOfScopeMask(loadMetroOutline); });\n",
        COVERAGE_JS,
        "three-zone coverage",
    )

    # -- the FAQ moves to its own page; the in-page section stays as a hidden
    #    husk (CSS) and its markup is extracted verbatim for the new page.
    faq_re = re.compile(r'<section class="faq-section" aria-labelledby="faq-heading">.*?</section>', re.S)
    faqs = faq_re.findall(html)
    if len(faqs) != 1:
        sys.exit("build-districtry-preview: FAIL — faq-section matched %d times" % len(faqs))
    faq_html = (
        FAQ_PAGE_TEMPLATE.replace("__FAQ_SECTION__", faqs[0])
        .replace("__STAMP__", stamp_text)
        .replace("__THEME_BOOT__", THEME_BOOT_JS)
    )

    # -- empty state: the Chicago star stays in the DOM (JS writes its `d`)
    #    but is hidden by the skin; the districtry mark is drawn beside it.
    html = sub_once(
        html,
        '<path fill="none" stroke="var(--accent-deep)" stroke-width="4" id="star-path-empty"></path>\n      </svg>',
        '<path fill="none" stroke="var(--accent-deep)" stroke-width="4" id="star-path-empty"></path>\n      </svg>\n      '
        + EMPTY_MARK_SVG,
        "empty-state mark",
    )

    # -- the BASE selection marker becomes the canvas's own answer: a
    #    data-tier circle with a white ring. This is what a point gets
    #    everywhere the hierarchy does not override it — every Illinois county
    #    without a shipped seal, and anywhere outside Illinois. The city and
    #    the seal counties override it below.
    html = sub_once(
        html,
        '\'<path d="\' + starPath(50, 50, 46, 19) + \'" fill="#C8102E" stroke="#ffffff" stroke-width="4"/>\' +',
        '\'<circle cx="50" cy="50" r="17" fill="#1d5fd6" stroke="#ffffff" stroke-width="6"/>\' +',
        "selection marker",
    )

    # -- ...and keep the Chicago flag star for Chicago itself, in flag red.
    #    The city's own emblem is right for the city; what was wrong was using
    #    it as the DEFAULT for the whole state. Defined next to the base icon so
    #    both read as one decision, and it reuses starPath(), already in scope.
    html = sub_once(
        html,
        "    iconSize: [34, 34],\n    iconAnchor: [17, 17]\n  });\n",
        "    iconSize: [34, 34],\n    iconAnchor: [17, 17]\n  });\n\n"
        "  // Chicago keeps its flag star, in flag red — the city's emblem for\n"
        "  // the city, rather than for every point in Illinois.\n"
        "  var chiFlagStarDivIcon = L.divIcon({\n"
        '    className: "chi-star-marker",\n'
        "    html: '<svg viewBox=\"0 0 100 100\" width=\"34\" height=\"34\" style=\"filter:drop-shadow(0 2px 3px rgba(0,0,0,0.45))\">' +\n"
        "          '<path d=\"' + starPath(50, 50, 46, 19) + '\" fill=\"#C8102E\" stroke=\"#ffffff\" stroke-width=\"4\"/>' +\n"
        '          "</svg>",\n'
        "    iconSize: [34, 34],\n"
        "    iconAnchor: [17, 17]\n"
        "  });\n",
        "chicago flag star icon",
    )

    # -- branch 1 of the hierarchy: inside the city, set the flag star. The
    #    engine returned early here (keeping whatever the default was), which
    #    is why the base icon had been doing double duty as both "Chicago" and
    #    "everywhere else".
    html = sub_once(
        html,
        "      if (!live() || inCity) return;",
        "      if (!live()) return;\n"
        "      if (inCity) { marker.setIcon(chiFlagStarDivIcon); return; }",
        "chicago star branch",
    )

    # -- branch 3: a county WITH a shipped seal keeps its seal; a county
    #    without one now keeps the default circle instead of a name badge.
    html = sub_once(
        html,
        "          if (sealUrl) {\n"
        "            whenSealImgReady(sealUrl, function (ok) {\n"
        "              if (!live()) return;\n"
        "              marker.setIcon(ok ? makeCountySealDivIcon(sealUrl, name) : makeCountyBadgeDivIcon(name));\n"
        "            });\n"
        "          } else {\n"
        "            marker.setIcon(makeCountyBadgeDivIcon(name));\n"
        "          }",
        "          if (sealUrl) {\n"
        "            whenSealImgReady(sealUrl, function (ok) {\n"
        "              if (!live()) return;\n"
        "              if (ok) marker.setIcon(makeCountySealDivIcon(sealUrl, name));\n"
        "            });\n"
        "          }",
        "county badge retired",
    )

    # -- relationship-legend swatches: two more Chicago-flag-blue literals.
    #    These are ILLUSTRATIVE — the outlines the map actually draws take each
    #    layer's own colour, darkened (see the pin-relationship block), so the
    #    swatch only demonstrates solid=inside vs dashed=crossing. Left as
    #    Chicago blue they showed a hue this app never draws; moved to the
    #    data-tier blue they at least sample the tier they illustrate.
    html = sub_once(
        html,
        ".rel-sw-in { border-top: 3px solid #0B5394; }",
        ".rel-sw-in { border-top: 3px solid #1d5fd6; }",
        "rel swatch (inside)",
    )
    html = sub_once(
        html,
        ".rel-sw-cross { border-top: 3px dashed #0B5394; }",
        ".rel-sw-cross { border-top: 3px dashed #1d5fd6; }",
        "rel swatch (crossing)",
    )

    # -- the skin island, last in <head> so it wins the cascade, and the
    #    theme boot script immediately after it (it needs the island's rules
    #    already parsed, and it must run before the first paint).
    html = sub_once(html, "</head>", SKIN_ISLAND + "</head>", "skin island")
    html = sub_once(html, "</head>", THEME_BOOT_JS + "</head>", "theme boot")

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

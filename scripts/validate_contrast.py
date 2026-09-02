#!/usr/bin/env python3
"""
Every text colour the brand paints, measured against the ground it sits on.

WHY THIS EXISTS. districtry/tokens/districtry.tokens.css is the ONE source of
the brand surface, and build_brand_tokens.py makes that true: every consumer's
values are gated as identical to it. But identical to WHAT was never measured.
The palette carries 54 aria attributes' worth of care in the app, 17
focus-visible rules and a reduced-motion query — and not one number saying
that the text a reader must read is legible against the ground it is painted
on. For a public civic tool whose standing rule is that a claim gets measured
rather than asserted, an unmeasured legibility claim is the shape of thing
this repo refuses everywhere else.

It was not an idle gap. Measured on the day this was written (2026-09-02):

  --faint  light  #9aa3b2  on --surface #ffffff   2.54:1   footer meta at 11px,
                                                           placeholders, menu
                                                           labels, the landing
                                                           page's own h2
  --faint  dark   #746e86  on --surface #201d29   3.40:1
  --muted  light  #6b7280  on --paper   #f4f2ee   4.32:1
  #fff     dark            on --brand   #a78bfa   2.72:1   the search button,
                                                           every primary CTA
  #fff     dark            on --brand-700 #c4b0ff 1.91:1   its hover, .cta,
                                                           every pressed state
  #fff     dark            on --ink     #ece9f4   1.20:1   the SKIP LINK —
                                                           fixed in this change

against the 4.5:1 that WCAG 1.4.3 asks of body text and the 3:1 it asks of
large text and UI parts (1.4.11). Light --faint clears NEITHER — it is below
the bar for text a reader is not even expected to read closely — and the dark
tier's button faces are the polarity inversion the sub-page shell's own
comments describe: "deep" means more contrast against the ground, which on a
dark ground is LIGHTER, and the engine paints white text on it.

WHAT THIS DOES. Reads the token file — both tiers, the dark one composed over
the light one exactly as the cascade does it, since [data-theme="dark"]
redefines 25 tokens and inherits the rest — and tests an explicit table of
(foreground, background, role) PAIRS: the pairs the product actually paints,
mapped from every CSS surface (the app's style blocks under engine/index.html/,
the sub-page shell, and the CSS the four root-page builders emit), never a
cartesian product. A translucent value is composited over its ground before
measuring, because rgba(236,233,244,0.1) is not a colour until it is on
something. Each role carries the floor WCAG sets for it.

WHY A PAIR TABLE AND NOT THE CSS. The cascade decides what text sits on, and
no regex over 1,000 lines of skin can follow `color:` through inheritance to
the background four ancestors up. So the pairs are STATED, with the selector
that proves each one, and the table is the claim — the same shape as
build_brand_tokens.py's ALIASES: a row is an assertion that this text is
painted on this ground, and the gate is what makes it a measurement rather
than a hope. A new text colour ships by adding its row.

WHAT THE TABLE COVERS, AND WHAT IT DOES NOT — measured, not assumed. The five
CSS surfaces (engine/index.html/styles-*.txt, engine/shared/styles-subpage.txt
and the CSS the four root-page builders emit) were mapped rule by rule on
2026-09-02: 291 distinct (foreground, background, role, tier) pairs, 120 of
them driven by brand tokens — those are the rows above — and 105 literal
colour values the token file does not own: the engine's --card-* palette
(styles-card-v2: #111827 on #fff, --card-link #1a56c4, and their dark
counterparts in the skin), the pre-rebrand navy the hover popup and the
footer still declare (#08406e, #0B5394, #C9D4DB — much of it dead under the
skin's cascade, some of it live), Leaflet's own popup chrome (#333 on white),
the three gap-kind indicators, and --layer-accent, which is set INLINE per
card at runtime and no static gate can read. This gate measures the brand.
The card palette is the next gate's subject, and until it exists the one
place the repo has measured it is a comment in styles-hover-responsive.txt,
which records "#8b93a1 measures 3.09:1 and fails AA" as the reason its labels
are #6b7280 — by hand, once, for one file. Opacity on text (.locate-btn:disabled
at 0.6, .rel-note at 0.7) and color-mix() grounds (.disclaimer, the sub-page
pill hover) are likewise noted and not measured. The TEMPLATE style blocks an
instance's index.html carries between the fences (Illinois's .empty-state-lede,
its school chips) sit outside those five surfaces and were not mapped as a
whole; the one faint pair a completeness critic found in them is in the table.

WHAT IT DOES WITH A SHORTFALL. A pair under its floor FAILS, unless it is
recorded in ACCEPTED_SHORTFALLS with the MEASURED ratio, a reason and a date
— the posture check_roster_retention.py takes with ACCEPTED_DROPS and
validate_card_links.py with EXPECTED_UNREACHABLE. An accepted entry is not a
silence: every run prints it, it FAILS if the ratio moves in either direction
(a fix must retire the entry; a regression must not hide behind it), and it
fails if the pair it names stops being tested. An entry recorded at
introduction with no decision is marked so, and stays visible until someone
either fixes the token or writes down why not.

Stdlib only.

    python3 scripts/validate_contrast.py            # gate: exit 1 on any failure
    python3 scripts/validate_contrast.py --report   # every pair, both tiers
"""

import argparse
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(REPO_ROOT, "districtry", "tokens", "districtry.tokens.css")

# WCAG 2.x floors by role. `text` is 1.4.3 (AA, normal-size text); `large`
# is the same criterion's relaxation for text >= 24px, or >= 18.66px bold;
# `ui` is 1.4.11 (non-text contrast) for the parts of a component a reader
# must perceive to use it — a button face, an input's border, a focus ring.
# `decorative` is measured and printed and never gated: card rules, row
# dividers and the empty-state stripe carry no information a reader needs,
# and 1.4.11 says so in as many words.
FLOORS = {"text": 4.5, "large": 3.0, "ui": 3.0, "decorative": None}

# (foreground token, background token, role, where it is painted).
#
# Tokens are CANONICAL names from the token file. The app's alias vocabulary
# maps through build_brand_tokens.ALIASES (--slate-soft is faint, --panel is
# surface, --accent-deep is brand-700); the root pages use these names
# directly. "#fff" is the one literal the skin paints as text — a primary
# button's face — and it is listed because the token file cannot see it.
#
# The `where` column is the evidence: a selector that paints this pair, from
# the surface named. Keep it honest — a row nothing paints is a row that
# should go, and a colour painted with no row here is a colour this gate is
# not measuring.
PAIRS = [
    # — body text on the grounds —
    ("ink",        "surface",    "text", "cards, panels, masthead: header.masthead, .layer-block, .share-popover (skin); the sub-page shell's .answer-card body"),
    ("ink",        "paper",      "text", "app ground: body (styles-app); every root page's body"),
    ("ink",        "surface-2",  "text", "section heads: .layer-block-head (skin; dark literal #262331 == --surface-2 dark)"),
    ("ink",        "brand-tint", "text", "privacy.html .k / .tldr; landing .notice-h; landing .pill (build_landing_page, build_privacy_page)"),
    ("ink",        "border",     "text", ".gap-suggest:hover — text with the border colour as its ground (styles-hover-responsive)"),
    ("ink-2",      "surface",    "text", "history.html .tile-l (build_history_page)"),
    ("ink-2",      "paper",      "text", "history.html .intro, .entry p, code (build_history_page)"),
    ("ink-3",      "surface",    "text", "h1.title small, .masthead-action-link, .share-popover-note (skin, as --slate); the gaps panel's .gap-area, .gap-detail, .gaps-credit (styles-footer); the source-unavailable notice renderSourceUnavailable paints from JS"),
    ("ink-3",      "paper",      "text", "sub-page details body, landing h1 at <=560px, .kbd-select-btn (shell, root, styles-app)"),
    ("ink-3",      "surface-2",  "text", "privacy.html thead th at 12px (build_privacy_page)"),
    ("ink-3",      "brand-tint", "text", "landing .notice-b, footer .support (build_landing_page)"),
    ("ink-3",      "border",     "text", ".gap-badge at 10px — text on the border colour (styles-hover-responsive)"),
    ("muted",      "surface",    "text", "privacy .masthead h1 small, .which, .footer-inner; coverage-map attribution at 10px"),
    ("muted",      "paper",      "text", "landing .lede, .coverage-caption, .not-yet-list; history .kicker and its scheduled-jobs th at 12px"),
    ("muted",      "brand-tint", "text", "landing #notice-dismiss at 11.5px; coverage-map .legend a:hover .mt"),

    # — the quiet tier: small labels, meta, placeholders — still TEXT —
    ("faint",      "surface",    "text", ".dst-metro-menu-label 10px, .footer-meta 11px, .title-metro, .hover-foot (skin, as --slate-soft); .empty-state-lede 12.5px (il TEMPLATE block); privacy td small 12px; coverage-map .legend h3 11px; landing .pill-n at rest"),
    ("faint",      "paper",      "text", "landing h2 at 15px, .cta-note 13px, .search-input::placeholder (build_landing_page, shell)"),
    ("faint",      "brand-tint", "text", "landing .pill:hover .pill-n at 12px (build_landing_page)"),

    # — links and accents as text —
    ("brand-700",  "surface",    "text", "links: .dpf-links a, .dpf-support a, .sibling-result-hint, footer.site-footer a (skin, shell; as --accent-deep)"),
    ("brand-700",  "paper",      "text", "links on the app ground, every root page's `a`, .locate-btn, .btn-secondary"),
    ("brand-700",  "brand-tint", "text", ".dst-metro-menu a:focus-visible; privacy .masthead-actions a:hover; landing footer .support a:hover"),
    ("brand",      "surface",    "text", "coverage-map attribution links at 10px; .dst-wordmark-link:hover (skin, as --accent)"),
    ("brand",      "paper",      "text", "landing footer a; sub-page summary::after glyph at 24px"),
    ("brand",      "brand-tint", "text", "landing footer .support a (build_landing_page)"),

    # — error state —
    ("error-ink",  "surface",    "text", ".layer-card-body.state-error (skin; dark literal #fdba74 == --error-ink dark)"),
    ("error",      "surface",    "text", "landing .search-status.err at 13.5px (build_landing_page)"),
    ("error",      "surface",    "ui",   ".layer-block.state-error border-left (skin; dark literal #f97316 == --error dark)"),

    # — literal white as text: the engine's button faces, on every accent —
    # The token file cannot see these; they are listed because the dark tier
    # lifts every accent to a tint chosen so LINKS read on a dark ground, and
    # the same tokens are BUTTON FACES under white text (the polarity
    # inversion the sub-page reader named). build_landing_page.py already
    # flips its own button to --paper text in dark, and records why.
    ("#fff",       "brand",      "text", ".search-row button (styles-core colour, skin ground), .masthead-actions a.is-primary:hover, .footer-link-btn:hover"),
    ("#fff",       "brand-700",  "text", ".cta (shell), .search-row button:hover, .btn-primary:hover — NOT the pressed/pinned toggles in dark: the skin's later [data-theme=dark] .hover-toggle-btn / .pin-parent-btn rules repaint those on --dst-raised"),
    ("#fff",       "brand-warm", "text", ".stub-badge at 10px (styles-hover-responsive)"),
    ("paper",      "brand",      "text", "landing .search-button in dark — the flip that HOLDS: build_landing_page records white on #a78bfa = 2.72 and paints --paper instead"),
    ("paper",      "brand-700",  "text", "landing .search-button:hover in dark"),
    ("paper",      "ink",        "text", ".skip-link (styles-core; the root pages' skip links already paint this pair) — focus-only, and the one masthead element the skin does not restyle"),

    # — UI parts a reader must perceive to use (1.4.11) —
    ("brand-warm", "paper",      "ui",   "--focus-ring: 3px solid var(--accent-warm) on the app ground and every sub-page summary"),
    ("brand-warm", "surface",    "ui",   "focus ring on a card or the masthead; .group-safety .dot"),
    ("brand",      "surface",    "ui",   "focused input border: .masthead .search-row input:focus; .group-political .dot; landing outline rings"),
    ("data-500",   "surface",    "ui",   "legend dot / selected-boundary swatch: .dml-dot (skin)"),
    ("border",     "surface",    "ui",   "the masthead search input's RESTING border: its interior is --dst-sunken, white on the white masthead in light, so the 1px --line border is the field's only boundary — 1.4.11's text-input case"),

    # — decorative: measured, printed, never gated —
    # border-dot outlines LABELLED controls (.dst-metro-btn, .masthead-actions
    # a, .hover-toggle-btn, as --line-strong); 1.4.11 holds a boundary to 3:1
    # only where it is what identifies the component, and these carry text.
    ("border-dot", "surface",    "decorative", "outlined labelled controls: .masthead-actions a (shell), .hover-toggle-btn, .school-chip (skin; as --line-strong — .dst-metro-btn has border: 0)"),
    ("border",     "paper",      "decorative", "landing .search-card, sub-page details rules"),
    ("border-soft","surface",    "decorative", "row rules; privacy th/td rules"),
    ("empty",      "surface",    "decorative", "empty-state stripe: .layer-block.state-empty border-left"),
]

# A shortfall someone has looked at. Keyed (fg, bg, tier); `measured` is the
# ratio on the day it was recorded, to two decimals, and the gate FAILS if the
# live value differs — a fix retires the entry, a regression cannot shelter
# under it. `decided` is False for the ones recorded at introduction: they are
# measured, visible on every run, and awaiting either a token change or a
# written reason. Nothing here is a threshold being lowered; the floor is the
# floor, and this is the list of places the palette is known not to meet it.
ACCEPTED_SHORTFALLS = {
    # --faint: one token, one decision, six grounds. For it to clear 4.5:1 on
    # the paper ground it must become #696f79, which is DARKER than --muted
    # #6b7280 — the quiet tier cannot stay quiet and meet AA on every ground.
    # The decision is which: darken the ramp, or move the 10-15px text off
    # --faint (menu labels, footer meta, placeholders, the landing page's own
    # h2) onto --muted / --ink-3 and keep --faint for large text and decoration.
    ("faint", "surface", "light"): dict(
        measured=2.54, decided=False, date="2026-09-02",
        reason="#9aa3b2, luminance 0.363 against a 0.183 ceiling for 4.5:1 on "
               "white; recorded at the gate's introduction — the token predates it"),
    ("faint", "paper", "light"): dict(
        measured=2.28, decided=False, date="2026-09-02",
        reason="same token on the app ground, whose ceiling is 0.159 — this is "
               "the landing page's h2 at 15px"),
    ("faint", "brand-tint", "light"): dict(
        measured=2.15, decided=False, date="2026-09-02",
        reason="same token on the landing page's pill tint at 12px"),
    ("faint", "surface", "dark"): dict(
        measured=3.40, decided=False, date="2026-09-02",
        reason="#746e86 clears the 3:1 large-text bar and not the 4.5:1 text bar"),
    ("faint", "paper", "dark"): dict(
        measured=3.78, decided=False, date="2026-09-02",
        reason="same token on the dark app ground"),
    ("faint", "brand-tint", "dark"): dict(
        measured=2.96, decided=False, date="2026-09-02",
        reason="same token on the dark pill tint — under even the 3:1 bar"),
    # --muted misses by a step on the two tinted grounds and clears --surface.
    ("muted", "paper", "light"): dict(
        measured=4.32, decided=False, date="2026-09-02",
        reason="#6b7280 (luminance 0.167) on the paper ground, whose ceiling for "
               "4.5:1 is 0.159; #686f7c clears both grounds (4.54 on paper) — a "
               "one-step darkening"),
    ("muted", "brand-tint", "light"): dict(
        measured=4.08, decided=False, date="2026-09-02",
        reason="same token on the landing page's pill tint, at 11.5px"),
    # White on the dark accents: the polarity inversion. The dark tier lifts
    # every accent to a tint chosen so LINKS read on a dark ground, and the
    # engine paints the same tokens as BUTTON FACES under literal #fff. The
    # fix exists in-repo — build_landing_page.py flips its button to --paper
    # text in dark and records why — and porting it to styles-core's button
    # rules is a visible change on every instance's dark mode, so it is
    # recorded here rather than made.
    ("#fff", "brand", "dark"): dict(
        measured=2.72, decided=False, date="2026-09-02",
        reason="white on --accent #a78bfa: the search button, the primary "
               "masthead action, the footer-link hover — --paper on the same "
               "ground reads ~6.8:1"),
    ("#fff", "brand-700", "dark"): dict(
        measured=1.91, decided=False, date="2026-09-02",
        reason="white on --accent-deep #c4b0ff: the search button's HOVER, the "
               "sub-page .cta, the primary button's hover — 'deep' "
               "means more contrast against the ground, which on a dark ground "
               "is LIGHTER, and white text on it is the worst pair in the palette"),
    ("#fff", "brand-warm", "dark"): dict(
        measured=2.67, decided=False, date="2026-09-02",
        reason="white on --accent-warm #e879b9 in the hover popup's .stub-badge at 10px"),
    # The one 1.4.11 case that is genuinely arguable: a text input whose
    # interior matches its ground has only its border to say where it is.
    ("border", "surface", "light"): dict(
        measured=1.23, decided=False, date="2026-09-02",
        reason="the masthead search input's resting border, #e8e7ef on white; "
               "the field also carries a placeholder and a search button, which "
               "is the reading under which 1.4.11 exempts the boundary — "
               "recorded so the decision is a written one"),
    ("border", "surface", "dark"): dict(
        measured=1.31, decided=False, date="2026-09-02",
        reason="same border, rgba(236,233,244,0.1) composited over #201d29"),
}

problems = []
warnings = []


def fail(msg):
    print("validate-contrast: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def token_block(css, selector):
    """The same shape build_brand_tokens.py reads, so the two cannot disagree
    about what a block is."""
    m = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S)
    if not m:
        fail("no %r block in %s" % (selector, os.path.relpath(TOKENS, REPO_ROOT)))
    return {k: v.strip() for k, v in
            re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", m.group(1))}


def resolve(table, name, depth=0):
    """Follow var() indirection to a colour. The token file uses one level
    (--brand is var(--brand-600)); allowing a few more costs nothing and
    means a future ramp alias cannot silently read as unresolved."""
    if depth > 5:
        return None
    v = table.get("--" + name)
    if v is None:
        return None
    m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v.strip())
    return resolve(table, m.group(1)[2:], depth + 1) if m else v


def parse_color(v):
    """-> (r, g, b, a) with channels 0-255 and alpha 0-1. Hex in 3, 4, 6 or 8
    digits; rgb()/rgba() with commas. Anything else is a colour this gate
    cannot measure, which is a failure rather than a skip."""
    s = v.strip().lower()
    if s.startswith("#"):
        h = s[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
            return None
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255.0 if len(h) == 8 else 1.0
        return (r, g, b, a)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", s)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",") if p.strip()]
        if len(parts) not in (3, 4):
            return None
        try:
            r, g, b = (float(p) for p in parts[:3])
            a = float(parts[3]) if len(parts) == 4 else 1.0
        except ValueError:
            return None
        return (r, g, b, a)
    return None


def composite(fg, bg):
    """Source-over: what the eye sees when a translucent colour sits on an
    opaque one. The result is opaque by construction."""
    r, g, b, a = fg
    R, G, B, _ = bg
    return (r * a + R * (1 - a), g * a + G * (1 - a), b * a + B * (1 - a), 1.0)


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(c):
    """WCAG relative luminance: the sRGB transfer function per channel, then
    the Rec. 709 weights. This is the same _srgb_to_lin that
    build_dark_map_palette.py uses on the way into OKLCH."""
    return 0.2126 * _lin(c[0]) + 0.7152 * _lin(c[1]) + 0.0722 * _lin(c[2])


def contrast(fg, bg):
    """(L1 + 0.05) / (L2 + 0.05), lighter over darker. A RATIO of two
    colours — a single colour has no contrast, which is the mistake a
    reference this gate was measured against had made."""
    l1, l2 = luminance(fg), luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def tiers(css):
    """Light is :root as written. Dark is :root with the [data-theme="dark"]
    block laid over it — the cascade's own answer, so a token the dark block
    does not redefine (every --brand-N00 step, --border-soft's partner
    --surface-2's neighbours) keeps its light value here exactly as it does
    in the browser."""
    light = token_block(css, ":root")
    dark = dict(light)
    dark.update(token_block(css, '[data-theme="dark"]'))
    return {"light": light, "dark": dark}


def colour_of(table, name, ground):
    """Resolve a token (or a literal) to an opaque colour on `ground`."""
    raw = name if name.startswith("#") or name.startswith("rgb") else resolve(table, name)
    if raw is None:
        return None, "no token --%s" % name
    c = parse_color(raw)
    if c is None:
        return None, "--%s is %r, which this gate cannot parse" % (name, raw)
    if c[3] < 1.0 and ground is not None:
        c = composite(c, ground)
    return c, None


def measure(table, tier):
    """-> list of rows: (fg, bg, role, ratio, floor, status, where)."""
    rows = []
    paper, err = colour_of(table, "paper", None)
    if err:
        fail("%s tier: %s" % (tier, err))
    for fg, bg, role, where in PAIRS:
        # a translucent GROUND (dark --brand-tint is rgba) sits on paper
        ground, err = colour_of(table, bg, paper)
        if err:
            problems.append("%s tier: background %s" % (tier, err))
            continue
        fore, err = colour_of(table, fg, ground)
        if err:
            problems.append("%s tier: foreground %s" % (tier, err))
            continue
        ratio = round(contrast(fore, ground), 2)
        floor = FLOORS[role]
        status = "ok"
        if floor is not None and ratio < floor:
            status = "short"
        rows.append((fg, bg, role, ratio, floor, status, where))
    return rows


def judge(rows_by_tier):
    """Apply ACCEPTED_SHORTFALLS. Every accepted entry must name a pair that
    is still tested and still short by exactly the recorded amount."""
    seen = set()
    for tier, rows in rows_by_tier.items():
        for fg, bg, role, ratio, floor, status, where in rows:
            key = (fg, bg, tier)
            acc = ACCEPTED_SHORTFALLS.get(key)
            if status == "short":
                if acc is None:
                    problems.append(
                        "%s: %s on %s (%s) is %.2f:1, floor %.1f — %s"
                        % (tier, fg, bg, role, ratio, floor, where))
                else:
                    seen.add(key)
                    if abs(acc["measured"] - ratio) > 0.005:
                        problems.append(
                            "%s: %s on %s is %.2f:1 but ACCEPTED_SHORTFALLS records "
                            "%.2f — the palette moved; re-measure and re-decide, or "
                            "retire the entry" % (tier, fg, bg, ratio, acc["measured"]))
                    else:
                        warnings.append(
                            "%s: %s on %s (%s) %.2f:1 < %.1f — accepted %s%s: %s"
                            % (tier, fg, bg, role, ratio, floor, acc["date"],
                               "" if acc["decided"] else ", NOT YET DECIDED",
                               acc["reason"]))
            elif acc is not None:
                seen.add(key)
                problems.append(
                    "%s: %s on %s now measures %.2f:1 and clears its floor — retire "
                    "its ACCEPTED_SHORTFALLS entry (recorded %.2f)"
                    % (tier, fg, bg, ratio, acc["measured"]))
    for key in ACCEPTED_SHORTFALLS:
        if key not in seen:
            problems.append(
                "ACCEPTED_SHORTFALLS names %s on %s (%s), which no PAIRS row tests "
                "— an accepted shortfall must stay measured" % key)


def report(rows_by_tier):
    for tier, rows in rows_by_tier.items():
        print("\n%s tier" % tier.upper())
        print("  %-11s %-11s %-11s %7s %6s  %s" % ("fg", "bg", "role", "ratio", "floor", "status"))
        for fg, bg, role, ratio, floor, status, where in rows:
            fl = "%.1f" % floor if floor is not None else "—"
            print("  %-11s %-11s %-11s %6.2f:1 %6s  %s" % (fg, bg, role, ratio, fl, status))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="print every pair's ratio in both tiers")
    ap.add_argument("--check", action="store_true",
                    help="accepted for symmetry with the other gates; the bare run is the check")
    args = ap.parse_args()

    css = read(TOKENS)
    rows_by_tier = {tier: measure(table, tier) for tier, table in tiers(css).items()}
    judge(rows_by_tier)

    if args.report:
        report(rows_by_tier)
        print()

    for w in warnings:
        print("  ~ " + w)
    if problems:
        for p in problems:
            print("  - " + p, file=sys.stderr)
        fail("%d pair(s) below floor or mis-recorded" % len(problems))

    n_pairs = len(PAIRS)
    n_gated = sum(1 for _fg, _bg, role, _w in PAIRS if FLOORS[role] is not None)
    n_acc = len(ACCEPTED_SHORTFALLS)
    n_open = sum(1 for a in ACCEPTED_SHORTFALLS.values() if not a["decided"])
    print("validate-contrast: OK — %d pair(s) measured in 2 tiers, %d gated; "
          "%d accepted shortfall(s)%s"
          % (n_pairs, n_gated, n_acc,
             ", %d awaiting a decision" % n_open if n_open else ""))


if __name__ == "__main__":
    main()

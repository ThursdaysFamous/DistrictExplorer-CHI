#!/usr/bin/env python3
"""
districtry/tokens/districtry.tokens.css is the ONE source of the brand surface.

WHY THIS EXISTS. The fleet was carrying one palette under two vocabularies and
four hand-kept copies. The apps and the twelve instance sub-pages speak
--accent/--slate/--panel; the root pages (the landing page and privacy.html)
speak --brand-*/--ink-3/--surface, because those two are generated from the
design-token file and the others were typed. Measured across both tiers, the
neutral chrome was already IDENTICAL in both vocabularies — the same six colours
under two sets of names — so this was never two designs. It was one design with
nothing asserting it stayed one.

And it had already stopped. Three divergences were live when this was written:

  --accent-deep dark   app #c4b0ff   root pages #a78bfa   (a visible link colour)
  --accent-warm        app #b0316e   root pages had none
  font stacks          app carries 'Barlow Fallback'; the root pages do not

plus four the sub-page shell introduced the day it was written, by restating
the dark tier from memory: --accent-warm #fd88b8 against the app's #e879b9,
--slate-soft #8f8a9e against #746e86, and both --line values off by 0.02 alpha.
That shell exists BECAUSE thirteen hand-kept copies drifted. It drifted on day
one. Restating a palette is not a thing to do carefully; it is a thing not to do.

WHAT THIS DOES. Two jobs, one source:

  GENERATE  engine/shared/tokens-brand.txt — the sub-page palette, emitted in
            the app's vocabulary from the canonical values, and spliced into
            every sub-page by compose_app.py. Nobody types these again.
  CHECK     every other consumer against the same source, through the ALIASES
            table below: the app's own skin, each instance worksheet's palette
            keys, and the two generated root pages. A consumer keeps its own
            names — renaming --accent to --brand-600 across three 21,000-line
            apps would touch thousands of call sites and change nothing a reader
            sees — but it may not keep its own VALUES.

WHY NOT ONE VOCABULARY. Because the names are not the problem and never were.
--accent/--panel are an application's semantics; --brand-600/--surface are a
design system's ramp. Both are correct in their own document. The defect was
that two documents disagreed about what colour --accent-deep is in dark mode,
and that is what an alias table plus a gate fixes.

ORDER OF OPERATIONS: this script, then compose_app.py (which splices what this
emits), then generate_metro_files.py. --check is order-independent.

    python3 scripts/build_brand_tokens.py           # regenerate + report
    python3 scripts/build_brand_tokens.py --check   # drift gate; exit 1 on any
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(REPO_ROOT, "districtry", "tokens", "districtry.tokens.css")
SHELL_BLOCK = os.path.join(REPO_ROOT, "engine", "shared", "tokens-brand.txt")
APP_SKIN = os.path.join(REPO_ROOT, "engine", "index.html", "styles-districtry-skin.txt")

# app vocabulary -> canonical token. Every row is a claim that these two names
# mean the same colour, and --check is what makes it a claim rather than a hope.
ALIASES = [
    ("--accent",           "brand"),
    ("--accent-deep",      "brand-700"),
    ("--accent-warm",      "brand-warm"),
    ("--accent-warm-deep", "brand-warm-deep"),
    ("--ink",              "ink"),
    ("--slate",            "ink-3"),
    ("--slate-soft",       "faint"),
    ("--paper",            "paper"),
    ("--panel",            "surface"),
    ("--line",             "border"),
    ("--line-strong",      "border-dot"),
]

# The neutral six the app's skin restates. The accents are already generated
# into the app from the worksheet (GENERATED brand-palette), so they are checked
# against the worksheet below instead of here.
APP_SKIN_CHECKED = ["--ink", "--slate", "--slate-soft", "--paper", "--panel",
                    "--line", "--line-strong"]

# The fallback face, by its canonical text. Four surfaces carry a copy — the
# shared shell, the three apps, and (via build_landing_page.FALLBACK_FACE) the
# two root pages — and the overrides are computed numbers, so a copy that drifts
# is a copy that stops holding the metrics without looking wrong.
FACE_RE = re.compile(
    r"@font-face\s*\{[^}]*font-family:\s*'Barlow Fallback'[^}]*\}", re.S)
FACE_CARRIERS = ["engine/shared/styles-subpage.txt",
                 "il/index.html", "ny/index.html", "ca/index.html",
                 "index.html", "privacy.html"]

WORKSHEET_PALETTE = [("accent", "brand"), ("accent_deep", "brand-700"),
                     ("accent_warm", "brand-warm"),
                     ("accent_warm_deep", "brand-warm-deep")]

# The font stacks, stated once. The app's body stack names 'Barlow Fallback' —
# a metric-matched local face that stops the layout shifting while the webfont
# loads — and every other surface had quietly dropped it.
FONTS = [("--font-display", "font-heading"), ("--font-body", "font-body")]
# Mono is the one stack the token file does not carry: it is a system list with
# no webfont behind it, so there is nothing for a design system to own.
FONT_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

problems = []


def fail(msg):
    print("build-brand-tokens: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def norm(v):
    """Compare colours by content, not by typing. `rgba(236, 233, 244, 0.10)`
    and `rgba(236,233,244,0.1)` are the same colour and two files spell it two
    ways; a gate that called that a drift would be reporting whitespace."""
    v = re.sub(r"\s+", "", v.strip().lower()).rstrip(";")
    v = re.sub(r"(\d)0+(?=[,)])", r"\1", v) if v.startswith("rgba") else v
    return v


def token_block(css, selector):
    m = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S)
    if not m:
        fail("no %r block in %s" % (selector, os.path.relpath(TOKENS, REPO_ROOT)))
    return {k: v.strip() for k, v in
            re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", m.group(1))}


def resolve(table, name):
    """One level of var() indirection — --brand is `var(--brand-600)`."""
    v = table.get("--" + name)
    if v is None:
        return None
    m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v.strip())
    return table.get(m.group(1), v) if m else v


def render(light, dark):
    L = ["/* GENERATED by scripts/build_brand_tokens.py from",
         "   districtry/tokens/districtry.tokens.css — do not hand-edit. The",
         "   values are the design system's; the NAMES are the app's, so a",
         "   sub-page and the app it hangs off use one vocabulary. Rerun the",
         "   script, then compose_app.py. */",
         ":root {"]
    for prop, tok in ALIASES:
        L.append("  %s: %s;" % (prop, resolve(light, tok)))
    for prop, tok in FONTS:
        L.append("  %s: %s;" % (prop, resolve(light, tok)))
    L += ["  --font-mono: %s;" % FONT_MONO,
          "  --focus-ring: 3px solid var(--accent-warm);",
          "}",
          "/* The dark tier is reached FROM the app, which has a theme toggle; the",
          "   boot script in <head> sets data-theme before first paint from the",
          "   same localStorage key the app writes. */",
          ':root[data-theme="dark"] {']
    for prop, tok in ALIASES:
        v = resolve(dark, tok)
        if v is not None:
            L.append("  %s: %s;" % (prop, v))
    L.append("}")
    return "\n".join(L) + "\n"


def check_app_skin(light, dark):
    css = read(APP_SKIN)
    # the skin's own :root and its dark counterpart, as written
    for label, selector, table in (("light", ":root", light),
                                   ("dark", ':root[data-theme="dark"]', dark)):
        m = re.search(re.escape(selector) + r"\s*\{(.*?)\n  \}", css, re.S)
        if not m:
            problems.append("app skin: no %s palette block found" % label)
            continue
        got = {k: v.strip() for k, v in
               re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", m.group(1))}
        for prop in APP_SKIN_CHECKED:
            tok = dict(ALIASES)[prop]
            want = resolve(table, tok)
            if prop not in got:
                continue          # the dark block legitimately omits some
            if want is None or norm(got[prop]) != norm(want):
                problems.append(
                    "app skin %s: %s is %s, the token file says --%s is %s"
                    % (label, prop, got[prop], tok, want))


def check_fallback_face():
    """Every surface that NAMES 'Barlow Fallback' in its body stack must also
    define it, identically. Naming a family nobody defines is not an error
    anywhere — the stack just falls through — which is exactly why eleven
    surfaces did it for months without a symptom louder than a reflow."""
    seen = {}
    for rel in FACE_CARRIERS:
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(path):
            problems.append("%s: missing, but listed as a fallback-face carrier" % rel)
            continue
        m = FACE_RE.search(read(path))
        if not m:
            problems.append("%s: names 'Barlow Fallback' in --font-body but never "
                            "defines the face" % rel)
            continue
        seen[rel] = re.sub(r"\s+", " ", m.group(0)).strip()
    if len(set(seen.values())) > 1:
        for rel, txt in sorted(seen.items()):
            problems.append("fallback face differs in %s: %s" % (rel, txt[:90]))


def check_worksheets(light):
    for tag in ("", "ny", "ca"):
        rel = os.path.join(tag, "metro-worksheet.json") if tag else "metro-worksheet.json"
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(path):
            continue
        pal = json.load(open(path, encoding="utf-8")).get("palette", {})
        for key, tok in WORKSHEET_PALETTE:
            want = resolve(light, tok)
            if key in pal and want and norm(pal[key]) != norm(want):
                problems.append("%s: palette.%s is %s, --%s is %s"
                                % (rel, key, pal[key], tok, want))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    css = read(TOKENS)
    light = token_block(css, ":root")
    dark = token_block(css, '[data-theme="dark"]')
    for _prop, tok in ALIASES:
        if resolve(light, tok) is None:
            fail("--%s is missing from the token file's :root — renamed upstream?" % tok)

    body = render(light, dark)
    current = read(SHELL_BLOCK) if os.path.exists(SHELL_BLOCK) else None

    check_app_skin(light, dark)
    check_worksheets(light)
    check_fallback_face()

    if args.check:
        if current != body:
            problems.insert(0, "engine/shared/tokens-brand.txt does not match the "
                               "token file — rerun scripts/build_brand_tokens.py")
        if problems:
            for p in problems:
                print("  - " + p, file=sys.stderr)
            fail("%d consumer(s) disagree with districtry/tokens/districtry.tokens.css"
                 % len(problems))
        print("build-brand-tokens: OK — %d alias(es) agree across the shell, the app "
              "skin and %d worksheet(s); the fallback face is identical on %d "
              "surface(s)" % (len(ALIASES), 3, len(FACE_CARRIERS)))
        return

    if problems:
        for p in problems:
            print("  - " + p, file=sys.stderr)
        fail("%d consumer(s) disagree; fix them or the token file, then rerun"
             % len(problems))
    os.makedirs(os.path.dirname(SHELL_BLOCK), exist_ok=True)
    with open(SHELL_BLOCK, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    print("build-brand-tokens: wrote engine/shared/tokens-brand.txt — %d alias(es) "
          "from districtry/tokens/districtry.tokens.css" % len(ALIASES))


if __name__ == "__main__":
    main()

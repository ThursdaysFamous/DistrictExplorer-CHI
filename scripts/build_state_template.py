#!/usr/bin/env python3
"""Emit the state-expansion template tree from this repo's live tree.

CHI-ONLY (like fleet_status.py): sibling forks and the template repo itself do
not carry this script. The template repo is a GENERATED ARTIFACT — it is
rebuilt from Chicago's working tree by .github/workflows/update-state-template.yml
and force-refreshed on every engine release, so it can never rot the way a
hand-cut skeleton would. Never hand-edit the template repo; edit CHI (or the
payloads under templates/state/) and rebuild.

How a file gets into the template (docs/EXPANSION_GUIDE.md §4.10):

  * KEEP_VERBATIM — copied byte-for-byte (fonts, the engine-channel scripts,
    engine.lock.json, docs/ENGINE_SYNC.md, ...).
  * PROCESSED — the file carries `TEMPLATE:BEGIN/END <name>` span markers
    (comment lines, inert in CHI). Each span has a disposition here:
      keep            carry the span, applying the file's substitution table
                      to its unfenced lines
      drop            emit nothing but any ENGINE/GENERATED fences the span
                      encloses (in document order)
      replace         emit a payload file's content instead (such a span must
                      not enclose fences)
    index.html and sw.js are STRICT: every non-blank line must sit inside a
    TEMPLATE span, an ENGINE fence, a GENERATED region, or be a METRO marker —
    an unclassified line fails the build, which is the anti-rot property (new
    CHI code must be consciously classified in the PR that adds it). Other
    processed files default unclassified content to keep.
  * PLACED — authored payloads from templates/state/ (workflows, docs,
    manifest, icons, the starter modules).
  * SYNTHESIZED — metro-worksheet.json (template-worksheet.json + the fleet
    list from metros.json), .claude/settings.json (generic transform), the
    doc pointer stubs, data/app/README.md.

After emitting, the builder runs generate_metro_files.py --root <out> so every
GENERATED region reflects the template worksheet, then self-checks: fence
fidelity (the template's ENGINE blocks byte-equal CHI's), token inventory
(emitted {{TOKENS}} == templates/state/template-tokens.json exactly),
substitution-table hit counts (an entry that stops matching fails, so the
table cannot rot), and a reference-city fingerprint sweep over everything
except the engine-channel files and fenced/generated content.

Usage:
    python3 scripts/build_state_template.py --out DIR    # emit the tree
    python3 scripts/build_state_template.py --check      # hermetic CI gate
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPTS)
TPL = os.path.join(REPO, "templates", "state")
sys.path.insert(0, SCRIPTS)

from check_engine_parity import MARKER_RE as ENGINE_RE, extract_blocks  # noqa: E402
from generate_metro_files import GENERATED_RE  # noqa: E402

TEMPLATE_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--|#|//)?[ \t]*==== TEMPLATE:(BEGIN|END) ([a-z0-9][a-z0-9-]*) ====[ \t]*(?:\*/|-->)?[ \t]*$"
)
METRO_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--)[ \t]*==== METRO:(BEGIN|END) ([a-z0-9][a-z0-9-]*) ====[ \t]*(?:\*/|-->)[ \t]*$"
)
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

ERRORS = []


def err(msg):
    ERRORS.append(msg)


def payload(relpath):
    """Read a payload file from templates/state/."""
    path = os.path.join(TPL, relpath)
    with open(path, encoding="utf-8") as f:
        return f.read().rstrip("\n")


# ---------------------------------------------------------------------------
# Configuration: what the template is made of
# ---------------------------------------------------------------------------

KEEP_VERBATIM = [
    "fonts",
    "schema/metro-worksheet.schema.json",
    "docs/ENGINE_SYNC.md",
    "engine.lock.json",
    ".gitignore",
    ".nojekyll",
    "scripts/apply_engine.py",
    "scripts/check_engine_parity.py",
    "scripts/generate_metro_files.py",
    "scripts/vendor_leaflet.sh",
    "scripts/check_roster_retention.py",
    "scripts/build_congress_roster.py",
    "scripts/requirements.txt",
    "scripts/bootstrap_state.py",
    "scripts/check_template_placeholders.py",
]

# Engine-channel files: byte-identical to CHI BY CONTRACT (they ship from the
# engine release, or pin it), so the fingerprint sweep must not ask them to be
# localized — localizing them is what's forbidden.
ENGINE_CHANNEL = {
    "docs/ENGINE_SYNC.md",
    "engine.lock.json",
    "schema/metro-worksheet.schema.json",
    "scripts/apply_engine.py",
    "scripts/check_engine_parity.py",
    "scripts/generate_metro_files.py",
}

# Per-file substitutions: (kind, pattern, replacement, min_hits).
# kind "lit" = plain-string replace; "re" = regex (MULTILINE). Applied only to
# unfenced remnant lines. A table entry matching fewer than min_hits times
# FAILS the build — the table cannot silently rot as CHI changes.
SUBS = {
    "index.html": [
        ("lit", "https://chidistricts.goatcounter.com/count", "{{GOATCOUNTER_URL}}", 1),
        ("lit", 'content="#0b3d91"', 'content="{{THEME_COLOR}}"', 1),
        ("re", r'href="data:image/svg\+xml,[^"]*"', 'href="{{FAVICON_DATA_URI}}"', 1),
        ("re", r'^<link rel="dns-prefetch" href="https://data\.cityofchicago\.org">\n', "", 1),
        ("lit", "#41B6E6", "{{PALETTE_ACCENT}}", 1),
        ("lit", "#0B5394", "{{PALETTE_ACCENT_DEEP}}", 1),
        ("lit", "#C8102E", "{{PALETTE_ACCENT_WARM}}", 2),
        ("lit", "#9C0B24", "{{PALETTE_ACCENT_WARM_DEEP}}", 1),
        ("lit", "---- Chicago flag palette ----", "---- brand palette (bootstrap fills from metro-worksheet.json) ----", 1),
        ("lit", ">Chicago District Explorer</span>", ">{{BRAND_NAME}}</span>", 1),
        ("lit", "Map of Chicago.", "Map of {{STATE_NAME}}.", 1),
        ("lit", "a Chicago address", "a {{STATE_NAME}} address", 2),
        ("re", r'(<p class="empty-state-lede">).*(</p>)', r"\1{{EMPTY_STATE_LEDE}}\2", 1),
        ("re", r'^\s*<a href="https://overberg\.co"[^\n]*</a>\n', "", 1),
        ("re", r'^\s*<a href="https://github\.com/sponsors/[^\n]*</a>\n', "", 1),
        ("lit", "https://github.com/ThursdaysFamous/DistrictExplorer-CHI", "{{REPO_URL}}", 1),
        ("lit", "Chicago-owned and additive", "Fork-owned and additive", 1),
        ("lit", "Chicago-owned masthead action row", "Fork-owned masthead action row", 1),
        ("lit", "Chicago-specific: the masthead action row", "Fork-owned: the masthead action row", 1),
        ("lit", "Chicago-specific: the SEO/orientation lede", "Fork-owned: the orientation lede", 1),
        ("lit", "ChiExplorer", "{{EXPORTS_NAME}}", 3),
        ("lit", "lat=41.88&lon=-87.63", "lat={{GEOCODER_BIAS_LAT}}&lon={{GEOCODER_BIAS_LON}}", 1),
        ("lit", "* Chicago, attributed.", "* the home area, attributed.", 1),
        ("lit", "Chicago's centre", "the metro centre", 1),
        ("lit", "the Chicago bias/bbox", "the home bias/bbox", 1),
    ],
    "sources.html": [
        ("lit",
         "https://github.com/ThursdaysFamous/DistrictExplorer-CHI/blob/main/docs/SOURCE_CREDITS.md",
         "{{REPO_URL}}/blob/main/docs/SOURCE_CREDITS.md", 1),
        ("lit", "https://github.com/ThursdaysFamous/DistrictExplorer-CHI", "{{REPO_URL}}", 1),
        ("lit", "https://chidistricts.com/sources.html", "{{CANONICAL_URL}}sources.html", 1),
        ("lit", "https://chidistricts.com/og-image.png", "{{CANONICAL_URL}}og-image.png", 1),
        ("lit", "Chicago District Explorer", "{{BRAND_NAME}}", 3),
        ("re", r'^\s*<a href="https://overberg\.co"[^\n]*</a>\n', "", 1),
        ("re", r'^\s*<a href="https://github\.com/sponsors/[^\n]*</a>\n', "", 1),
    ],
    "scripts/smoke_test.mjs": [
        # the share-control boot URL seeds OFFLINE[0]'s CHI id; harmless if
        # unknown (the boot parse drops it) but rewritten for cleanliness
        ("lit", "&layers=school-board", "&layers=county", 1),
    ],
    "scripts/validate_sources.py": [
        ("lit", "DistrictExplorer-CHI source validator (+https://chidistricts.com)",
         "District Explorer source validator (+{{CANONICAL_URL}})", 1),
        ("lit", "* Chicago Data Portal (Socrata) datasets are versioned by year. The CPS",
         "* Socrata portal datasets can be versioned by year. The reference fork's CPS", 1),
    ],
    "scripts/build_metro_outline.py": [
        ("lit", "DistrictExplorer-CHI metro-outline builder", "District Explorer metro-outline builder", 1),
        ("lit", "It used to be driven by the Chicago school\nboard tiling",
         "In the reference fork it was once driven by a city-limits\ntiling", 1),
        ("lit", "against Chicago's 32", "against the city's 32", 1),
        ("lit", "a hole in the Chicago\n    metro", "a hole in the\n    served metro", 1),
    ],
    "scripts/validate_card_links.py": [
        ("lit", "every chicagopolice.org URL refuse", "every URL on some CDN-fronted hosts refuses", 1),
        ("lit", "reported chicagopolice.org and dupagecounty.gov as having no DNS record",
         "reported two live reference-fork hosts as having no DNS record", 1),
        ("lit", "chicagopolice.org is cited\n    22 times, and 22",
         "the reference fork cites one host\n    22 times, and 22", 1),
    ],
    "scripts/indexnow_submit.py": [
        ("lit", "https://chidistricts.com/6ce8d9c81c2e4b0b914e34fd134ed36e.txt",
         "{{CANONICAL_URL}}<KEY>.txt", 1),
        ("lit", "https://chidistricts.com/ https://chidistricts.com/other",
         "{{CANONICAL_URL}} {{CANONICAL_URL}}other", 1),
    ],
    ".github/workflows/deploy-pages.yml": [
        ("lit", "in the Chicago fork", "in the reference fork", 1),
    ],
    "robots.txt": [
        ("lit", "https://chidistricts.com/sitemap.xml", "{{CANONICAL_URL}}sitemap.xml", 1),
    ],
}

SW_VERSION_HISTORY = (
    "// (Shell version history — grow this comment as the shell changes; the\n"
    "// template starts at -v1: the app shell, icons, and the starter data\n"
    "// files bootstrap_state.py builds.)"
)

# Span dispositions per processed file. "keep"/"drop", or ("replace", text).
def dispositions():
    return {
        "index.html": {
            "head-open": "keep",
            "head-analytics": "drop",
            "head-meta": ("replace", payload("payloads/head-meta.html")),
            "head-jsonld": "drop",
            "head-assets": "keep",
            "palette": "keep",
            "styles-school-chips": "drop",
            "styles-masthead-actions": "keep",
            "styles-faq": "drop",
            "body-shell": "keep",
            "body-why-link": "drop",
            "body-main": "keep",
            "body-faq": "drop",
            "body-footer": "keep",
            "core-config": "keep",
            "marker-water-taxi-icon": "drop",
            "core-when-idle": "keep",
            "marker-water-taxi-preload": "drop",
            "marker-county-seals": "drop",
            "core-utils": "keep",
            "select-point-marker": ("replace", payload("payloads/select-point-marker.js")),
            "core-selection": "keep",
            "core-registry": "keep",
            "thread-1-geography": "drop",
            "thread-2-safety": "drop",
            "thread-3-schools": "drop",
            "thread-4-political": "drop",
            "starter-modules": ("replace", payload("starter-modules.js")),
            "tail-fences": "keep",
            "sidebar-rank": ("replace", payload("payloads/sidebar-rank.js")),
            "tail-boot": "keep",
            "wash-comment": ("replace", payload("payloads/wash-comment.js")),
            "tail-close": "keep",
        },
        "sw.js": {
            "sw-version-history": ("replace", SW_VERSION_HISTORY),
        },
        "sources.html": {
            "sources-analytics": "drop",
            "sources-jsonld": "drop",
        },
        "scripts/smoke_test.mjs": {
            "smoke-fork-constants": ("replace", payload("payloads/smoke-fork-constants.js")),
            # CHI-scenario checks, wrapped by the second smoke marker pass;
            # resolved dynamically below so a new smoke-* span in CHI fails
            # the build (conscious classification) instead of leaking through.
        },
        "scripts/validate_sources.py": {
            "sources-manifest": ("replace", payload("payloads/sources-manifest.py")),
            "sources-ward-manifest": ("replace", payload("payloads/sources-ward-manifest.py")),
        },
        "scripts/validate_card_links.py": {
            "card-links-host-tables": ("replace", payload("payloads/card-links-host-tables.py")),
        },
        "scripts/indexnow_submit.py": {
            "indexnow-host": ("replace", payload("payloads/indexnow-host.py")),
        },
        "scripts/build_metro_outline.py": {
            "outline-county-config": ("replace", payload("payloads/outline-county-config.py")),
            "outline-anchors": ("replace", payload("payloads/outline-anchors.py")),
        },
        ".github/workflows/deploy-pages.yml": {},
        "robots.txt": {},
    }


# Any smoke-test span named smoke-<something> (other than smoke-fork-constants)
# is a CHI-specific scenario check: dropped from the template wholesale.
SMOKE_CHI_SPAN = re.compile(r"^smoke-(?!fork-constants$)[a-z0-9-]+$")

STRICT_FILES = {"index.html", "sw.js"}

PLACEMENTS = {
    ".github/workflows/engine-bump.yml": "workflows/engine-bump.yml",
    ".github/workflows/template-gates.yml": "workflows/template-gates.yml",
    ".github/workflows/update-congress-roster.yml": "workflows/update-congress-roster.yml",
    "CLAUDE.md": "docs/CLAUDE.md",
    "README.md": "docs/README.md",
    "WATCH.md": "docs/WATCH.md",
    "manifest.webmanifest": "payloads/manifest.webmanifest",
}

BINARY_PLACEMENTS = {
    "icons/icon-192.png": "payloads/icon-192.png",
    "icons/icon-512.png": "payloads/icon-512.png",
}

DOC_STUBS = {
    "EXPANSION_GUIDE.md": "the deployment guide for every kind of growth — Part 2 is the county recipe this fork will live in; §4.10 is the state-template route this repo was created from",
    "BUILD_PLAYBOOK_1.md": "the layer-module contract and the reference build log",
    "OPTIMIZATION_PLAYBOOK.md": "measured performance tasks and their evidence",
    "REDISTRICTING_RUNBOOK.md": "what to do when a boundary changes (WATCH.md is when to look)",
    "MECHANIZATION_PLAYBOOK.md": "the engine-artifact / worksheet-generator / reverse-parity machinery record",
    "METRO_EXPANSION_PLAYBOOK.md": "the archived pre-consolidation porting playbook",
}

GENERIC_ALLOWED_DOMAINS = [
    "tigerweb.geo.census.gov",
    "nominatim.openstreetmap.org",
    "photon.komoot.io",
    "unitedstates.github.io",
    "a.basemaps.cartocdn.com",
    "b.basemaps.cartocdn.com",
    "c.basemaps.cartocdn.com",
    "d.basemaps.cartocdn.com",
    "cdnjs.cloudflare.com",
    "unpkg.com",
    "cdn.jsdelivr.net",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "registry.npmjs.org",
    "cdn.playwright.dev",
    "playwright.download.prss.microsoft.com",
]


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

def segment(text, path):
    """Split file text into top-level segments:
    ("plain", None, [lines]) | ("engine"/"generated", name, [lines incl markers])
    | ("span", name, [subsegments]).
    TEMPLATE markers delimit spans and are NOT included in any segment (they
    never reach the output). Fences inside a span become subsegments."""
    lines = text.split("\n")
    segs = []
    plain = []
    span = None  # [name, subsegs, plainbuf]

    def flush(target, buf):
        if buf:
            target.append(("plain", None, buf[:]))
            del buf[:]

    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        m_t = TEMPLATE_RE.match(ln)
        if m_t:
            op, name = m_t.group(1), m_t.group(2)
            if op == "BEGIN":
                if span:
                    err("%s:%d: nested TEMPLATE span %r inside %r" % (path, i + 1, name, span[0]))
                    return segs
                flush(segs, plain)
                span = [name, [], []]
            else:
                if not span or span[0] != name:
                    err("%s:%d: TEMPLATE:END %r without matching BEGIN" % (path, i + 1, name))
                    return segs
                flush(span[1], span[2])
                segs.append(("span", span[0], span[1]))
                span = None
            i += 1
            continue
        m_f = ENGINE_RE.match(ln) or GENERATED_RE.match(ln)
        if m_f:
            kind = "engine" if ENGINE_RE.match(ln) else "generated"
            fence_re = ENGINE_RE if kind == "engine" else GENERATED_RE
            if m_f.group(1) != "BEGIN":
                err("%s:%d: stray %s END marker" % (path, i + 1, kind.upper()))
                return segs
            name = m_f.group(2)
            block = [ln]
            i += 1
            closed = False
            while i < n:
                ln2 = lines[i]
                if TEMPLATE_RE.match(ln2):
                    err("%s:%d: TEMPLATE marker inside %s fence %r" % (path, i + 1, kind, name))
                    return segs
                block.append(ln2)
                m2 = fence_re.match(ln2)
                i += 1
                if m2 and m2.group(1) == "END" and m2.group(2) == name:
                    closed = True
                    break
            if not closed:
                err("%s: unterminated %s fence %r" % (path, kind, name))
                return segs
            if span:
                flush(span[1], span[2])
                span[1].append((kind, name, block))
            else:
                flush(segs, plain)
                segs.append((kind, name, block))
            continue
        (span[2] if span else plain).append(ln)
        i += 1
    if span:
        err("%s: unterminated TEMPLATE span %r" % (path, span[0]))
    flush(segs, plain)
    return segs


def apply_subs(text, path, counters):
    for idx, (kind, pat, repl, _min) in enumerate(SUBS.get(path, [])):
        key = (path, idx)
        if kind == "lit":
            hits = text.count(pat)
            if hits:
                text = text.replace(pat, repl)
        else:
            text, hits = re.subn(pat, repl, text, flags=re.MULTILINE)
        counters[key] = counters.get(key, 0) + hits
    return text


def emit_file(path, dispo, counters):
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        text = f.read()
    if "\r" in text:
        err("%s: CR/CRLF line endings" % path)
    segs = segment(text, path)
    strict = path in STRICT_FILES
    out = []

    def emit_plain(lines_):
        chunk = "\n".join(lines_)
        out.append(apply_subs(chunk, path, counters))

    for kind, name, body in segs:
        if kind in ("engine", "generated"):
            out.append("\n".join(body))
        elif kind == "plain":
            bad = [l for l in body if l.strip() and not METRO_RE.match(l)]
            if strict and bad:
                err("%s: unclassified line outside every span/fence: %r" % (path, bad[0][:100]))
            emit_plain(body)
        else:  # span
            d = dispo.get(name)
            if d is None and path == "scripts/smoke_test.mjs" and SMOKE_CHI_SPAN.match(name):
                d = "drop"
            if d is None:
                err("%s: TEMPLATE span %r has no disposition in build_state_template.py" % (path, name))
                continue
            if d == "keep":
                for k2, n2, b2 in body:
                    if k2 in ("engine", "generated"):
                        out.append("\n".join(b2))
                    else:
                        emit_plain(b2)
            elif d == "drop":
                fences = [b2 for k2, _n2, b2 in body if k2 in ("engine", "generated")]
                for b2 in fences:
                    out.append("\n".join(b2))
            else:  # ("replace", text)
                if any(k2 in ("engine", "generated") for k2, _n, _b in body):
                    err("%s: replace span %r encloses a fence" % (path, name))
                out.append(d[1])
    joined = "\n".join(p for p in out if p != "")
    # collapse runs of 3+ blank lines left by drops
    joined = re.sub(r"\n{4,}", "\n\n\n", joined)
    if not joined.endswith("\n"):
        joined += "\n"
    return joined


# ---------------------------------------------------------------------------
# Synthesized files
# ---------------------------------------------------------------------------

def synth_worksheet():
    with open(os.path.join(TPL, "template-worksheet.json"), encoding="utf-8") as f:
        w = json.load(f)
    with open(os.path.join(REPO, "metros.json"), encoding="utf-8") as f:
        fleet = json.load(f)["metros"]
    explorers = [{k: m[k] for k in ("id", "label", "url", "emoji", "bbox") if k in m} for m in fleet]
    gate = w["permalink_gate"]
    explorers.append({
        "id": w["this_metro"],
        "label": w["metro_name"],
        "url": w["domains"]["canonical"],
        "emoji": "📍",
        "bbox": {"minLng": gate["minLng"], "minLat": gate["minLat"],
                 "maxLng": gate["maxLng"], "maxLat": gate["maxLat"]},
    })
    w["metro_explorers"] = explorers
    return json.dumps(w, ensure_ascii=False, indent=2) + "\n"


def synth_settings():
    with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
        s = json.load(f)
    out = {
        "permissions": {"allow": ["Bash(python3 scripts/validate_index.py *)"]},
        "hooks": s.get("hooks", {}),
        "sandbox": {"enabled": True, "allowedDomains": GENERIC_ALLOWED_DOMAINS},
    }
    return json.dumps(out, ensure_ascii=False, indent=2) + "\n"


def synth_stub(name, desc):
    return (
        "# %s — lives in the reference repo\n\n"
        "This fork does not carry its own copy. The fleet-wide original is\n"
        "**%s** in the reference repo:\n"
        "https://github.com/ThursdaysFamous/DistrictExplorer-CHI/blob/main/docs/%s\n\n"
        "(%s.)\n" % (name[:-3], name, name, desc)
    )


DATA_APP_README = (
    "# data/app\n\n"
    "Runtime-fetched data files. Empty until `scripts/bootstrap_state.py` runs —\n"
    "it builds the starter files (metro-outline, state-counties, congress\n"
    "districts + roster, unified school districts, coverage-gaps) from TIGERweb\n"
    "and congress-legislators. Every file here must be listed in\n"
    "`metro-worksheet.json`'s `data_files` and in exactly one of `sw.js`'s two\n"
    "cache lists (`validate_index.py` enforces both).\n"
)


# ---------------------------------------------------------------------------
# Build + self-checks
# ---------------------------------------------------------------------------

def build(outdir):
    tree = {}
    counters = {}

    for item in KEEP_VERBATIM:
        src = os.path.join(REPO, item)
        if not os.path.exists(src):
            err("keep-verbatim source missing: %s" % item)
            continue
        if os.path.isdir(src):
            for root, _dirs, files in os.walk(src):
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, REPO)
                    with open(full, "rb") as f:
                        tree[rel] = f.read()
        else:
            with open(src, "rb") as f:
                tree[item] = f.read()

    dispo = dispositions()
    for path in list(SUBS.keys()):
        if path not in dispo:
            dispo[path] = {}
    for path, d in dispo.items():
        if not os.path.exists(os.path.join(REPO, path)):
            err("processed source missing: %s" % path)
            continue
        tree[path] = emit_file(path, d, counters)

    # validate_index.py: clean outside its GENERATED region; carried verbatim,
    # then regenerated below against the template worksheet.
    with open(os.path.join(REPO, "scripts", "validate_index.py"), "rb") as f:
        tree["scripts/validate_index.py"] = f.read()

    for target, src in PLACEMENTS.items():
        tree[target] = payload(src) + "\n"
    for target, src in BINARY_PLACEMENTS.items():
        with open(os.path.join(TPL, src), "rb") as f:
            tree[target] = f.read()

    tree["metro-worksheet.json"] = synth_worksheet()
    tree[".claude/settings.json"] = synth_settings()
    for name, desc in DOC_STUBS.items():
        tree["docs/" + name] = synth_stub(name, desc)
    tree["data/app/README.md"] = DATA_APP_README

    # substitution hit-count guard
    for path, entries in SUBS.items():
        for idx, (_k, pat, _r, minhits) in enumerate(entries):
            hits = counters.get((path, idx), 0)
            if hits < minhits:
                err("substitution rot: %s entry %d (%r) matched %d < %d times"
                    % (path, idx, str(pat)[:60], hits, minhits))

    # write out
    for rel, content in sorted(tree.items()):
        full = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        kwargs = {} if isinstance(content, bytes) else {"encoding": "utf-8", "newline": "\n"}
        with open(full, mode, **kwargs) as f:
            f.write(content)
    # vendor_leaflet.sh must stay executable (SessionStart hook runs it)
    for rel in ("scripts/vendor_leaflet.sh",):
        full = os.path.join(outdir, rel)
        if os.path.exists(full):
            os.chmod(full, 0o755)
    return tree


def run_generator(outdir):
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "generate_metro_files.py"), "--root", outdir],
        capture_output=True, text=True)
    if proc.returncode != 0:
        err("generate_metro_files.py --root failed:\n%s%s" % (proc.stdout, proc.stderr))
        return
    proc = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "generate_metro_files.py"), "--root", outdir, "--check"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        err("generator --check unstable in the emitted tree:\n%s%s" % (proc.stdout, proc.stderr))


def check_fences(outdir):
    for fname in ("index.html", "sw.js"):
        with open(os.path.join(REPO, fname), encoding="utf-8") as f:
            ours = extract_blocks(f.read(), fname)
        with open(os.path.join(outdir, fname), encoding="utf-8") as f:
            theirs = extract_blocks(f.read(), fname)
        if set(ours) != set(theirs):
            err("%s: fence set differs: missing %s / extra %s"
                % (fname, sorted(set(ours) - set(theirs)), sorted(set(theirs) - set(ours))))
            continue
        for name in ours:
            if ours[name] != theirs[name]:
                err("%s: ENGINE block %r bytes differ from CHI's" % (fname, name))


def is_text(content):
    return isinstance(content, str)


def strip_protected(path, content):
    """Remove fenced/generated bodies (and the worksheet's metro_explorers)
    before the fingerprint sweep — those legitimately carry reference-fork
    vocabulary."""
    if path == "metro-worksheet.json":
        w = json.loads(content)
        w.pop("metro_explorers", None)
        return json.dumps(w)
    out = []
    skip_re = None
    for ln in content.split("\n"):
        if skip_re:
            m = skip_re.match(ln)
            if m and m.group(1) == "END":
                skip_re = None
            continue
        m_e = ENGINE_RE.match(ln)
        m_g = GENERATED_RE.match(ln)
        if m_e and m_e.group(1) == "BEGIN":
            skip_re = ENGINE_RE
            continue
        if m_g and m_g.group(1) == "BEGIN":
            skip_re = GENERATED_RE
            continue
        out.append(ln)
    return "\n".join(out)


def check_tokens_and_fingerprints(outdir, tree):
    with open(os.path.join(TPL, "template-tokens.json"), encoding="utf-8") as f:
        reg = json.load(f)
    declared = set(reg["tokens"])
    fingerprints = [fp.lower() for fp in reg["fingerprints"]]

    # the shipped checker embeds its own copies of the sentinel/fingerprint
    # lists (it must be standalone in the fork) — assert they match the
    # registry so the two can never drift
    import ast
    with open(os.path.join(SCRIPTS, "check_template_placeholders.py"), encoding="utf-8") as f:
        checker_ast = ast.parse(f.read())
    embedded = {}
    for node in checker_ast.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("SENTINELS", "FINGERPRINTS"):
            embedded[node.targets[0].id] = ast.literal_eval(node.value)
    if sorted(embedded.get("SENTINELS", [])) != sorted(reg["sentinels"]):
        err("check_template_placeholders.py SENTINELS drifted from template-tokens.json")
    if sorted(embedded.get("FINGERPRINTS", [])) != sorted(reg["fingerprints"]):
        err("check_template_placeholders.py FINGERPRINTS drifted from template-tokens.json")

    found = set()
    for rel, content in sorted(tree.items()):
        if not is_text(content):
            continue
        # re-read from disk so generator-rewritten regions are covered
        with open(os.path.join(outdir, rel), encoding="utf-8") as f:
            text = f.read()
        found.update(TOKEN_RE.findall(text))
        if rel in ENGINE_CHANNEL:
            continue
        swept = strip_protected(rel, text)
        low = swept.lower()
        for fp in fingerprints:
            if fp in low:
                line_no = next((i + 1 for i, l in enumerate(swept.split("\n")) if fp in l.lower()), "?")
                err("fingerprint %r survives in %s (first at stripped-line %s)" % (fp, rel, line_no))
    if found - declared:
        err("emitted tokens missing from template-tokens.json: %s" % sorted(found - declared))
    if declared - found:
        err("declared tokens never emitted: %s" % sorted(declared - found))


def node_check(outdir):
    proc = subprocess.run(["node", "--check", os.path.join(outdir, "sw.js")],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        err("node --check sw.js failed:\n%s" % proc.stderr[-2000:])
    # smoke_test.mjs carries raw {{TOKENS}} (some in numeric positions), so
    # syntax-check a token-filled copy, exactly as bootstrap will produce.
    with open(os.path.join(outdir, "scripts", "smoke_test.mjs"), encoding="utf-8") as f:
        smoke = TOKEN_RE.sub("0", f.read())
    tmp = os.path.join(outdir, "scripts", "_smoke_tokcheck.mjs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(smoke)
    proc = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if proc.returncode != 0:
        err("node --check smoke_test.mjs (token-filled) failed:\n%s" % proc.stderr[-2000:])
    # index.html's inline script: extract and syntax-check with tokens filled
    with open(os.path.join(outdir, "index.html"), encoding="utf-8") as f:
        html = f.read()
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    body = max(scripts, key=len) if scripts else ""
    body = TOKEN_RE.sub("0", body)
    tmp = os.path.join(outdir, "_inline_check.js")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(body)
    proc = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    os.unlink(tmp)
    if proc.returncode != 0:
        err("index.html inline script fails node --check after token fill:\n%s" % proc.stderr[-2000:])
    for rel in ("scripts/validate_sources.py", "scripts/validate_card_links.py",
                "scripts/indexnow_submit.py", "scripts/bootstrap_state.py",
                "scripts/check_template_placeholders.py", "scripts/build_congress_roster.py"):
        src = os.path.join(outdir, rel)
        with open(src, encoding="utf-8") as f:
            text = TOKEN_RE.sub("00", f.read())
        tmp = src + "._tokcheck.py"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        proc = subprocess.run([sys.executable, "-m", "py_compile", tmp],
                              capture_output=True, text=True)
        os.unlink(tmp)
        if proc.returncode != 0:
            err("py_compile %s failed:\n%s" % (rel, proc.stderr[-1500:]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="emit the template tree into this directory")
    ap.add_argument("--check", action="store_true",
                    help="emit to a temp dir, run every self-check, exit non-zero on failure")
    args = ap.parse_args()
    if bool(args.out) == bool(args.check):
        ap.error("exactly one of --out or --check")

    outdir = args.out or tempfile.mkdtemp(prefix="state-template-")
    if args.out and os.path.exists(outdir) and os.listdir(outdir):
        # refuse to merge into a dirty target: the template is a full artifact
        for entry in os.listdir(outdir):
            if entry != ".git":
                print("refusing to write into non-empty %s (found %r)" % (outdir, entry),
                      file=sys.stderr)
                sys.exit(1)

    tree = build(outdir)
    if not ERRORS:
        run_generator(outdir)
    if not ERRORS:
        check_fences(outdir)
        check_tokens_and_fingerprints(outdir, tree)
        node_check(outdir)

    if args.check:
        shutil.rmtree(outdir, ignore_errors=True)
    if ERRORS:
        print("build-state-template: FAIL — %d problem(s):" % len(ERRORS), file=sys.stderr)
        for e in ERRORS:
            print("  * " + e, file=sys.stderr)
        sys.exit(1)
    n_files = len(tree)
    print("build-state-template: OK — %d files%s" % (
        n_files, "" if args.check else " -> " + outdir))


if __name__ == "__main__":
    main()

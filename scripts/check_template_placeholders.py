#!/usr/bin/env python3
"""The placeholder / localization gate for a state-template fork.

Fails while the repo still carries anything a fresh template copy ships with:
  * {{UPPER_SNAKE}} placeholder tokens,
  * the template's sentinel values (newstate / Newstate / newstate.example /
    StateExplorer / the epoch verified-date),
  * reference-fork fingerprints (chidistricts, cityofchicago, chicago, ...) —
    the localization sweep EXPANSION_GUIDE §4.4.2 used to run by hand, as a
    day-one CI gate instead of an after-the-fact grep.

`scripts/bootstrap_state.py` is what makes this pass: it fills every token and
sentinel from the real state's facts. After bootstrap, keep this gate wired in
CI — it is a standing guard against reference-fork vocabulary sneaking back in
through cribbed code.

Skipped by design (never "localize" these):
  * ENGINE-channel files — byte-identical fleet-wide by contract
    (docs/ENGINE_SYNC.md, the shared scripts, the schema, engine.lock.json);
  * ENGINE fence bodies and GENERATED region bodies (the worksheet's
    metro_explorers legitimately names every fleet member, and generated
    regions are its projection);
  * binary files, fonts, icons, .git, node_modules, data/source;
  * this file itself (it must name the sentinels to find them).

Exit 0 = clean; exit 1 = findings (each printed as path:line: what).
"""

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
ENGINE_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--)[ \t]*==== ENGINE:(BEGIN|END) ([a-z0-9][a-z0-9-]*) ====[ \t]*(?:\*/|-->)[ \t]*$"
)
GENERATED_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--|#|//)?[ \t]*==== GENERATED:(BEGIN|END) ([a-z0-9][a-z0-9-]*) ====[ \t]*(?:\*/|-->)?[ \t]*$"
)

# Kept in lockstep with templates/state/template-tokens.json in the reference
# repo — its template build asserts these two lists match the registry.
SENTINELS = [
    "newstate",
    "Newstate",
    "newstate.example",
    "newstate-owner",
    "StateExplorer",
    "January 1, 2000",
]
FINGERPRINTS = [
    "chidistricts",
    "cityofchicago",
    "chiexplorer",
    "chicago",
]

SKIP_FILES = {
    "docs/ENGINE_SYNC.md",
    "engine.lock.json",
    "schema/metro-worksheet.schema.json",
    "scripts/apply_engine.py",
    "scripts/check_engine_parity.py",
    "scripts/generate_metro_files.py",
    "scripts/check_template_placeholders.py",
    "engine.bundle.js",
    "engine.manifest.json",
}
# data/ is skipped WHOLESALE: bootstrap-built boundary files and rosters are
# real-world civic data, and the real world legitimately contains the
# reference fork's vocabulary — the first Indiana e2e run failed on the
# School City of EAST CHICAGO, Indiana. The sweep polices authored code and
# prose; data answers to its own gates (validate_index's counts, the roster
# retention gate), never to a place-name blacklist.
SKIP_DIRS = {".git", "node_modules", "fonts", "data", "dist",
             ".claude/worktrees", "scripts/vendor", "__pycache__"}
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2",
                 ".zip", ".pdf", ".pyc")


def iter_files():
    for root, dirs, files in os.walk(REPO):
        rel_root = os.path.relpath(root, REPO)
        if rel_root == ".":
            rel_root = ""
        dirs[:] = [d for d in dirs
                   if os.path.join(rel_root, d).replace("\\", "/") not in SKIP_DIRS
                   and d not in (".git", "node_modules", "__pycache__")]
        for fn in files:
            rel = os.path.join(rel_root, fn).replace("\\", "/") if rel_root else fn
            if rel in SKIP_FILES or rel.endswith(SKIP_SUFFIXES):
                continue
            yield rel


def visible_lines(rel, text):
    """(line_no, line) pairs outside ENGINE/GENERATED bodies; for the
    worksheet, metro_explorers is dropped before scanning."""
    if rel == "metro-worksheet.json":
        try:
            w = json.loads(text)
            w.pop("metro_explorers", None)
            text = json.dumps(w, indent=1)
        except ValueError:
            pass
        return list(enumerate(text.split("\n"), 1))
    out = []
    skip = None
    for no, ln in enumerate(text.split("\n"), 1):
        if skip is not None:
            m = skip.match(ln)
            if m and m.group(1) == "END":
                skip = None
            continue
        m_e = ENGINE_RE.match(ln)
        m_g = GENERATED_RE.match(ln)
        if m_e and m_e.group(1) == "BEGIN":
            skip = ENGINE_RE
            continue
        if m_g and m_g.group(1) == "BEGIN":
            skip = GENERATED_RE
            continue
        out.append((no, ln))
    return out


def main():
    findings = []
    worksheet_dirty = False
    for rel in sorted(iter_files()):
        try:
            with open(os.path.join(REPO, rel), encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        for no, ln in visible_lines(rel, text):
            for m in TOKEN_RE.finditer(ln):
                findings.append("%s:%d: unreplaced token %s" % (rel, no, m.group(0)))
            for s in SENTINELS:
                if s in ln:
                    findings.append("%s:%d: template sentinel %r" % (rel, no, s))
                    if rel == "metro-worksheet.json":
                        worksheet_dirty = True
            low = ln.lower()
            for fp in FINGERPRINTS:
                if fp in low:
                    findings.append("%s:%d: reference-fork fingerprint %r" % (rel, no, fp))
    if findings:
        print("check-template-placeholders: FAIL — %d finding(s):" % len(findings))
        for fnd in findings[:200]:
            print("  * " + fnd)
        if len(findings) > 200:
            print("  ... and %d more" % (len(findings) - 200))
        if worksheet_dirty:
            print("\nThis repo has not been bootstrapped yet. Run:")
            print("  python3 scripts/bootstrap_state.py --state-fips NN --state-name <Name> \\")
            print("      --repo <owner/repo> --domain <host> --brand-name '<Name> District Explorer'")
        sys.exit(1)
    print("check-template-placeholders: OK — no tokens, sentinels, or reference-fork fingerprints")


if __name__ == "__main__":
    main()

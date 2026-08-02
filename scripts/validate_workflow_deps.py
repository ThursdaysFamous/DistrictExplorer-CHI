#!/usr/bin/env python3
"""Merge gate: every script a workflow runs must import under the dependencies
that workflow actually installs.

WHY THIS EXISTS. On 2026-08-02 the five derived-boundary counties' weekly roster
refreshes — Cass, De Witt, Marshall, Mason and Washington — were all dead on
arrival, and had been since the day they shipped. Each roster builder imports
its district composition from the matching *_board_districts.py module, for the
weekly drift check that compares the scraped roster against the boundary's
composition. That is the right design. But those district modules imported
shapely AT MODULE SCOPE, so importing a plain tuple of township names dragged in
the geometry stack — which the roster jobs correctly do not install, because
they do no geometry:

    ModuleNotFoundError: No module named 'shapely'

Nothing caught it. The scrapers were fine, the builders were fine, the data was
fine, every local run was fine (a developer machine has shapely), and
validate_index.py passed — because the failure lived in the seam between a
script's import graph and its workflow's pip line, which no gate looked at. It
took manually dispatching six never-run workflows to find, and only because five
of them failed identically in the same minute.

WHAT IT CHECKS. For each workflow: read the packages its `pip install` lines
declare, then for every `python3 scripts/X.py` it runs, walk X's transitive
MODULE-SCOPE imports through other scripts/ modules and collect every
third-party module that closure needs. Anything not declared is an error.

Module scope is the whole point: an import inside a function is lazy and costs
the caller nothing, which is exactly how the five builders were repaired. This
gate is what keeps them that way, and what stops the next roster builder from
reaching for a heavy module at the top of a file.

Stdlib only, so it runs in smoke-test.yml before any dependency is installed.

Usage:
    python3 scripts/validate_workflow_deps.py
"""

import ast
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

# pip name -> module name, where they differ. Extend as the fleet grows; an
# unmapped package is assumed to import under its own name.
IMPORT_NAME = {
    "beautifulsoup4": "bs4",
    "pillow": "PIL",
    "python-dateutil": "dateutil",
    "pyyaml": "yaml",
}

# Modules the runner always has, or that are vendored/optional by design.
ALWAYS_AVAILABLE = {"setuptools", "pip", "pkg_resources"}

PIP_RE = re.compile(r"pip3?\s+install\s+([^\n]*)")
RUN_RE = re.compile(r"python3?\s+(scripts/[A-Za-z0-9_]+\.py)")

failures = []


def fail(msg):
    failures.append(msg)


def declared_packages(text):
    """Import names a workflow's pip lines make available.

    Handles the -c/-r distinction that matters here: `-c file` is a CONSTRAINTS
    file (pins versions, installs nothing), so the packages are the names that
    follow it; `-r file` installs the file's whole contents.
    """
    names = set()
    for line in PIP_RE.findall(text):
        tokens = line.replace("\\", " ").split()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ("-r", "--requirement"):
                i += 1
                if i < len(tokens):
                    names |= read_requirements(tokens[i])
            elif tok in ("-c", "--constraint"):
                i += 1                       # skip the constraints file itself
            elif tok.startswith("-"):
                pass                         # -U, --quiet, …
            else:
                names.add(normalize(tok))
            i += 1
    return names


def read_requirements(rel_path):
    path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(path):
        fail("workflow installs -r %s, which does not exist" % rel_path)
        return set()
    out = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line and not line.startswith("-"):
                out.add(normalize(line))
    return out


def normalize(spec):
    """'beautifulsoup4==4.12.3' -> 'bs4'."""
    name = re.split(r"[<>=!~\[]", spec)[0].strip().lower()
    return IMPORT_NAME.get(name, name.replace("-", "_"))


def module_scope_imports(path):
    """Top-level imports only — a function-local import is lazy by design."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    mods = set()
    for node in tree.body:                   # body, not walk: module scope only
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
        elif isinstance(node, (ast.If, ast.Try)):
            # `try: import pypdf / except ImportError:` is a declared-optional
            # dependency, and `if TYPE_CHECKING:` never runs. Neither is a hard
            # requirement, so neither is checked.
            continue
    return mods


def closure(entry):
    """Every scripts/ module reachable from entry via module-scope imports."""
    seen, stack, third_party = set(), [entry], set()
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(SCRIPTS_DIR, name + ".py")
        if not os.path.exists(path):
            continue
        for mod in module_scope_imports(path):
            if mod in sys.stdlib_module_names or mod in ALWAYS_AVAILABLE:
                continue
            if os.path.exists(os.path.join(SCRIPTS_DIR, mod + ".py")):
                stack.append(mod)            # local module: keep walking
            else:
                third_party.add(mod)
    return seen, third_party


def main():
    if not os.path.isdir(WORKFLOW_DIR):
        print("validate-workflow-deps: no .github/workflows — nothing to check")
        return 0

    checked = 0
    for fname in sorted(os.listdir(WORKFLOW_DIR)):
        if not fname.endswith((".yml", ".yaml")):
            continue
        with open(os.path.join(WORKFLOW_DIR, fname), encoding="utf-8") as f:
            text = f.read()
        entries = sorted(set(RUN_RE.findall(text)))
        if not entries:
            continue
        declared = declared_packages(text)
        for rel in entries:
            entry = os.path.basename(rel)[:-3]
            if not os.path.exists(os.path.join(SCRIPTS_DIR, entry + ".py")):
                fail("%s runs %s, which does not exist" % (fname, rel))
                continue
            reached, needed = closure(entry)
            missing = sorted(needed - declared)
            checked += 1
            if missing:
                via = sorted(m for m in reached if m != entry)
                fail("%s runs %s, whose module-scope imports need %s — not "
                     "installed by that workflow. Import closure: %s. Either "
                     "add the package to the workflow's pip line, or (usually "
                     "right) move the import inside the function that uses it."
                     % (fname, rel, ", ".join(missing),
                        ", ".join(via) or "(no local imports)"))

    if failures:
        print("validate-workflow-deps: FAIL")
        for msg in failures:
            print("  - %s" % msg)
        return 1
    print("validate-workflow-deps: OK — %d workflow entry point(s) import "
          "cleanly under their own declared dependencies" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())

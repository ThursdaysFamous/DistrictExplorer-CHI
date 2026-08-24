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
declare, then for every `python3 <instance>/scripts/X.py` it runs, walk X's
transitive MODULE-SCOPE imports through other modules in THAT instance's
scripts/ directory and collect every third-party module that closure needs.
Anything not declared is an error. The instance prefix matters twice over: it
is how a relocated ny/ or ca/ refresh gets checked at all, and it is what keeps
a sibling import inside ny/scripts/ from being resolved against Chicago's
root scripts/, where several of the same names exist.

Module scope is the whole point: an import inside a function is lazy and costs
the caller nothing, which is exactly how the five builders were repaired. This
gate is what keeps them that way, and what stops the next roster builder from
reaching for a heavy module at the top of a file.

WHAT IT DOES NOT CATCH, stated plainly so nobody over-trusts a green line. It is
a static import check, not a run:

  * A dependency needed at RUNTIME by a function-local import. Skipping those is
    deliberate — the repair above turned five hard failures into lazy imports —
    but it means a genuinely missing package inside a function still fails only
    when that path executes. Dispatching the workflow remains the real proof.
  * Imports built at runtime (importlib with a computed name, __import__).
  * Anything past the import: a missing binary, a bad token, a blocked source.

So this closes the specific hole that let five refreshes ship broken; it does not
make dispatching a new workflow optional (EXPANSION_GUIDE §2.5.1).

Stdlib only, so it runs in smoke-test.yml before any dependency is installed.

Usage:
    python3 scripts/validate_workflow_deps.py
"""

import ast
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

# EVERY INSTANCE'S SCRIPTS, NOT JUST CHICAGO'S. This gate matched only
# `python3 scripts/X.py` for as long as there was only one scripts/ directory.
# When ny/ and ca/ were imported as folders they brought their own, and on
# 2026-08-24 their ten refreshes moved into the root .github/workflows and
# started invoking `python3 ny/scripts/X.py` — which the old pattern did not
# match, so those ten workflows would have been silently UNCHECKED by the one
# gate that exists to catch a workflow running a script it has not installed
# the dependencies for. A gate that quietly skips its newest subjects is worse
# than no gate: it reports OK. The path table is IMPORTED from the generator
# for the same reason fleet_status.py imports it — a second copy of "where does
# ny/ keep its scripts" is the drift this file exists to catch.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from generate_metro_files import INSTANCES  # noqa: E402
except ImportError:  # pragma: no cover
    INSTANCES = {"il": {"scripts": "scripts"}}

SCRIPTS_DIRS = {
    inst["scripts"]: os.path.join(REPO_ROOT, inst["scripts"])
    for inst in INSTANCES.values()
}

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
RUN_RE = re.compile(
    r"python3?\s+((?:%s)/[A-Za-z0-9_]+\.py)"
    % "|".join(re.escape(d) for d in sorted(SCRIPTS_DIRS, key=len, reverse=True)))

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


def module_scope_imports(path, include_local=False):
    """Imports a module costs its importer.

    Module scope by default: a function-local import is lazy, and costs an
    importer nothing. But for the ENTRY POINT — the .py the workflow actually
    executes — its own functions do run, so `include_local` folds those in too.
    That distinction is the whole difference between the two failures found on
    2026-08-02: the roster builders import a districts MODULE for a constant and
    must not pay for its geometry (lazy is correct), while Mason's watcher RUNS
    build_mason_board_districts.py --check, whose main() needs shapely for real
    and whose workflow installed only requests.
    """
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    mods = set()
    nodes = ast.walk(tree) if include_local else tree.body
    for node in nodes:
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    if include_local:
        # `try: import pypdf / except ImportError:` is a declared-optional
        # dependency and `if TYPE_CHECKING:` never runs, so neither is a hard
        # requirement. ast.walk() would have swept both in.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Try, ast.If)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Import):
                        mods -= {a.name.split(".")[0] for a in sub.names}
                    elif isinstance(sub, ast.ImportFrom) and sub.module:
                        mods.discard(sub.module.split(".")[0])
    return mods


def closure(entry, scripts_dir):
    """Every module in `scripts_dir` reachable from entry via module-scope imports.

    The entry point is read with its function-local imports included, because
    running a script runs its functions; everything it merely imports is read at
    module scope only.

    `scripts_dir` is the instance's own directory: a sibling import inside
    ny/scripts/ resolves against ny/scripts/, never against Chicago's root
    scripts/, so a name that exists in both cannot be walked into the wrong
    tree.
    """
    seen, stack, third_party = set(), [entry], set()
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(scripts_dir, name + ".py")
        if not os.path.exists(path):
            continue
        for mod in module_scope_imports(path, include_local=(name == entry)):
            if mod in sys.stdlib_module_names or mod in ALWAYS_AVAILABLE:
                continue
            if os.path.exists(os.path.join(scripts_dir, mod + ".py")):
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
            scripts_dir = SCRIPTS_DIRS[os.path.dirname(rel)]
            if not os.path.exists(os.path.join(scripts_dir, entry + ".py")):
                fail("%s runs %s, which does not exist" % (fname, rel))
                continue
            reached, needed = closure(entry, scripts_dir)
            missing = sorted(needed - declared)
            checked += 1
            if missing:
                via = sorted(m for m in reached if m != entry)
                fail("%s runs %s, which needs %s — not installed by that "
                     "workflow. Import closure: %s. Two different fixes: if the "
                     "module needs it to RUN, add the package to that "
                     "workflow's pip line; if it is only pulled in because some "
                     "module in the closure imports it at module scope for a "
                     "constant, move that import inside the function that uses "
                     "it instead."
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

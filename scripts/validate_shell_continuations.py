#!/usr/bin/env python3
"""Fail on a `#` comment sitting inside a backslash line-continuation.

WHY THIS EXISTS. On 2026-08-24 the Pages deploy stopped publishing and every
gate stayed green. The cause was six lines of explanatory comment written in the
middle of the deploy's rsync invocation:

    rsync -a \\
      --exclude='package-lock.json' \\
      # Imported instances are NOT published yet. …
      --exclude='sf' \\
      ./ _site/

Bash joins a backslash continuation BEFORE it looks for comments, so the comment
does not annotate the command — it TERMINATES it. rsync ran with its excludes
and no source or destination, exited 1 on a usage error, and everything after
the comment was parsed as a separate command (`--exclude=sf: command not found`).

The failure mode is what makes this worth a gate rather than a lesson. The
construct is invisible on review: it reads exactly like a well-commented
command, YAML parses it fine, shellcheck is not run on `run:` bodies, and the
break only appears at execution — in a deploy job, which is the one place this
repo's PR gates do not reach, because deploy runs on main AFTER the merge.

WHAT IT CHECKS. Every .yml/.yaml/.sh in the tree, line by line: if a line ends
with a backslash continuation and the NEXT line's first non-whitespace character
begins a comment, that is the bug. That is the whole rule — it needs no shell
parser, because the construct is always wrong. A comment belongs above the
command or inside a variable, never between two of its continued lines.

    python3 scripts/validate_shell_continuations.py
"""

import pathlib
import sys

SKIP_PARTS = (".git", "node_modules", "__pycache__")
SUFFIXES = (".yml", ".yaml", ".sh")


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    hits, scanned = [], 0

    for path in sorted(root.rglob("*")):
        if path.suffix not in SUFFIXES or not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        rel = path.relative_to(root)
        for i in range(len(lines) - 1):
            if not lines[i].rstrip().endswith("\\"):
                continue
            nxt = lines[i + 1].lstrip()
            if nxt.startswith("#"):
                hits.append((rel, i + 2, nxt[:72]))

    if hits:
        print("validate-shell-continuations: FAIL — a comment sits inside a "
              "backslash line-continuation. Bash joins the continuation first, "
              "so the comment TERMINATES the command rather than annotating it. "
              "Move it above the command.", file=sys.stderr)
        for rel, line, text in hits:
            print("  %s:%d  %s" % (rel, line, text), file=sys.stderr)
        return 1

    print("validate-shell-continuations: OK — %d file(s) scanned, no comment "
          "inside a line continuation" % scanned)
    return 0


if __name__ == "__main__":
    sys.exit(main())

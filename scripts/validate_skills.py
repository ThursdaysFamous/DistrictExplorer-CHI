#!/usr/bin/env python3
"""
Every skill under .claude/skills/ names real files, real sections, real flags.

WHY THIS EXISTS. A skill is prose an agent loads at the moment it starts a
kind of task, and prose that names scripts, tables, sections and flags is a
copy of facts that live elsewhere — exactly the drift class this repo gates
everywhere else. The steward skill's own preamble says why it carries only
what CLAUDE.md does not: two documents stating one convention is how
ENGINE_SYNC.md drifted 164 lines from the fences it described. A skill that
tells an agent to run `scripts/build_foo.py --check` after the script is
renamed, or to open §2.5.1 for a checklist that moved to §3.5.1 in a rewrite
(which is where CLAUDE.md's own reference to the first-island checklist still
points), is worse than no skill: it sends the agent somewhere confident and
wrong. This is the gate that keeps a skill's pointers pointing at things.

WHAT IT CHECKS, per SKILL.md:

  frontmatter   `name` equals the directory name; `description` is present
                and under DESCRIPTION_MAX characters — the description is the
                triggering surface and the harness truncates long ones.
  paths         every backticked repo path exists: `scripts/x.py`,
                `docs/X.md`, `il/data/app/x.json`, `.github/workflows/x.yml`,
                `wi/scripts/x.py` … A token carrying a placeholder
                (`<county>`, `*`, `…`) is a pattern, not a path, and is skipped.
  sections      every `§N.N` / `§N.N.N` resolves to a `## N.N` or `### N.N.N`
                heading in docs/EXPANSION_GUIDE.md, the one document that
                numbers its sections that way.
  flags         every `--flag` that follows a `scripts/x.py` on the same line
                appears in that script's source — the cheapest possible proof
                that argparse still accepts it.
  identifiers   every backticked ALL_CAPS name (`DISPATCH_COUNTY_FIPS`,
                `EXPECT_MEMBERS`, `KINDS`, a workflow's `EXCLUDES`) appears in
                at least one file the same skill names — in a sentence, a
                backtick or a bash block. A table a skill tells an agent to
                edit must still exist somewhere the skill points.
  negatives     a path named in order to say it is NOT there ("not
                `il/scripts/`", "`data/app` does not exist") is read as the
                warning it is, not as a claim.

It does not judge the prose. Stdlib only.

    python3 scripts/validate_skills.py            # gate: exit 1 on any failure
    python3 scripts/validate_skills.py --check    # same; the bare run is the check
"""

import argparse
import glob
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "skills")
GUIDE = os.path.join(REPO_ROOT, "docs", "EXPANSION_GUIDE.md")

# The harness shows the first ~1,000 characters of a description in the skill
# list; a longer one is the part of the trigger surface nobody reads.
DESCRIPTION_MAX = 1024

# A backticked token is a repo path when it starts in one of these roots or
# carries a path separator and a known extension. Placeholders make it a
# pattern (a `<county>_board_scraper.py` names a family, not a file).
PATH_ROOTS = ("scripts/", "docs/", "engine/", "il/", "ny/", "ca/", "wi/", "ia/",
              ".claude/", ".github/", "districtry/", "data/")
PATH_EXT = (".py", ".md", ".json", ".yml", ".yaml", ".mjs", ".js", ".html",
            ".txt", ".css", ".sh")
PLACEHOLDER = re.compile(r"[<>*…{}]|\.\.\.|\$\{")
FLAG_AFTER_SCRIPT = re.compile(r"(scripts/[\w./-]+\.py)([^\n`]*)")
FLAG = re.compile(r"(?<![\w-])(--[a-z][\w-]*)")
SECTION = re.compile(r"§\s?(\d+(?:\.\d+){1,2})\b")
IDENT = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")

problems = []


def fail(msg):
    print("validate-skills: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    key = None
    for line in m.group(1).split("\n"):
        km = re.match(r"([a-z_]+):\s*(.*)$", line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            fm[key] = val.lstrip(">|").strip()
        elif key and line.startswith(" "):
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, text[m.end():]


def guide_headings():
    out = set()
    for line in read(GUIDE).split("\n"):
        m = re.match(r"#{2,3}\s+(\d+(?:\.\d+){1,2})\b", line)
        if m:
            out.add(m.group(1))
    return out


def backticked(text):
    return re.findall(r"`([^`\n]+)`", text)


NEGATIVE = re.compile(r"(?:\bnot\s+|\bno\s+|\bnever\s+)`[^`]+`|`[^`]+`(?:\s+does\s+not\s+exist|\s+is\s+not\b|\s+no\s+longer\b)")


def negative_refs(text):
    """Paths a skill names in order to say they are NOT there — the steward's
    "`scripts/smoke_test.mjs`, not `il/scripts/`", the county skill's "the
    root `data/app` does not exist". A gate that failed on those would be
    asking the prose to stop warning about the wrong path."""
    out = set()
    for m in NEGATIVE.finditer(text):
        out.update(re.findall(r"`([^`]+)`", m.group(0)))
    return out


# Tokens that read as identifiers and are not ours to find: a runtime's own
# error codes, quoted because that is what the terminal prints.
NOT_OURS = {"MODULE_NOT_FOUND", "ERR_CONNECTION_RESET", "ENOENT"}


def is_path(tok):
    if PLACEHOLDER.search(tok) or " " in tok.strip():
        return False
    return tok.startswith(PATH_ROOTS) or ("/" in tok and tok.endswith(PATH_EXT))


def check_skill(skill_dir, headings):
    name = os.path.basename(skill_dir)
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        problems.append("%s: no SKILL.md" % name)
        return 0
    text = read(path)
    fm, body = frontmatter(text)
    if fm is None:
        problems.append("%s: no YAML frontmatter" % name)
        return 0
    if fm.get("name") != name:
        problems.append("%s: frontmatter name is %r, directory is %r"
                        % (name, fm.get("name"), name))
    desc = fm.get("description", "")
    if not desc:
        problems.append("%s: no description — nothing to trigger on" % name)
    elif len(desc) > DESCRIPTION_MAX:
        problems.append("%s: description is %d characters; the harness shows about %d"
                        % (name, len(desc), DESCRIPTION_MAX))

    checked = 0
    negatives = negative_refs(body)
    files_named = set()       # every existing file the skill points at
    # a script named anywhere — a bash block, a sentence, a backtick — is a
    # file the skill points at, and where its identifiers may live
    for spath, _rest in FLAG_AFTER_SCRIPT.findall(body):
        if os.path.isfile(os.path.join(REPO_ROOT, spath)):
            files_named.add(spath)
    for tok in backticked(text):
        tok = tok.strip()
        if is_path(tok):
            rel = tok.split()[0].rstrip(",;:")
            if tok in negatives:
                continue
            checked += 1
            full = os.path.join(REPO_ROOT, rel)
            if not os.path.exists(full):
                problems.append("%s: names `%s`, which does not exist" % (name, rel))
            elif os.path.isfile(full):
                files_named.add(rel)
    # flags on the same line as a script, anywhere in the body (not only in backticks)
    for spath, rest in FLAG_AFTER_SCRIPT.findall(body):
        full = os.path.join(REPO_ROOT, spath)
        if not os.path.exists(full):
            continue
        src = read(full)
        for flag in FLAG.findall(rest):
            checked += 1
            if flag not in src:
                problems.append("%s: says `%s %s`, but the script never mentions %s"
                                % (name, spath, flag, flag))
    # section references
    for sec in SECTION.findall(body):
        checked += 1
        if sec not in headings:
            problems.append("%s: cites §%s, which is not a heading in docs/EXPANSION_GUIDE.md"
                            % (name, sec))
    # ALL_CAPS identifiers must live in some file the skill names — a table it
    # tells an agent to edit (EXPECT_MEMBERS, an EXCLUDES list in a workflow)
    # has to still exist somewhere the skill points.
    sources = ""
    for rel in files_named:
        sources += read(os.path.join(REPO_ROOT, rel))
    for tok in backticked(body):
        tok = tok.strip()
        if IDENT.match(tok) and tok not in NOT_OURS:
            checked += 1
            if tok not in sources:
                problems.append("%s: names `%s`, which appears in none of the %d file(s) "
                                "the skill points at" % (name, tok, len(files_named)))
    return checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="accepted for symmetry with the other gates; the bare run is the check")
    ap.parse_args()

    if not os.path.isdir(SKILLS_DIR):
        fail("no %s" % os.path.relpath(SKILLS_DIR, REPO_ROOT))
    headings = guide_headings()
    skills = sorted(d for d in glob.glob(os.path.join(SKILLS_DIR, "*")) if os.path.isdir(d))
    if not skills:
        fail("no skills under .claude/skills/")
    total = 0
    for d in skills:
        total += check_skill(d, headings)

    if problems:
        for p in problems:
            print("  - " + p, file=sys.stderr)
        fail("%d pointer(s) in %d skill(s) point at nothing" % (len(problems), len(skills)))
    print("validate-skills: OK — %d skill(s), %d pointer(s) resolve (paths, §sections, "
          "flags, identifiers)" % (len(skills), total))


if __name__ == "__main__":
    main()

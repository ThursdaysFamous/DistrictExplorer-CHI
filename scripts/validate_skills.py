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
pointed until this gate found it), is worse than no skill: it sends the agent
somewhere confident and wrong. This is the gate that keeps a skill's pointers
pointing at things.

WHAT IT CHECKS, per SKILL.md:

  frontmatter   `name` equals the directory name; `description` is present
                and at most DESCRIPTION_MAX characters — the description is
                the triggering surface and the harness truncates long ones.
                Quoted, folded (`>`, `>-`) and literal (`|`) scalars are
                read as YAML reads them; CRLF and a BOM are tolerated.
  paths         every repo path the skill names exists — in a backtick span
                (`scripts/x.py`, `docs/X.md`, `il/data/app/x.json`,
                `wi/scripts/x.py` …), in a multi-word span (`python3
                scripts/x.py --check`), or as a script named anywhere in the
                body, a fenced block included. A line-number or sentence
                suffix (`scripts/x.py:42`, `scripts/x.py.`) is stripped
                first. A token carrying a placeholder (`<county>`, `*`, `…`,
                `$VAR`) is a pattern, not a path; a URL, a `~` or absolute
                path is not a repo path; nothing outside the repo root is
                ever tested.
  sections      every `§N.N` / `§N.N.N` resolves to a numbered heading in
                docs/EXPANSION_GUIDE.md — or, when a backticked `docs/X.md`
                immediately precedes the §, in THAT document.
  flags         every `--flag` in the command that names a `scripts/x.py`
                (or `<tag>/scripts/x.py` — the instance prefix is part of
                the path) appears in that script's source — the cheapest
                possible proof that argparse still accepts it. A command
                ends at a newline (backslash continuations join), a
                backtick, a shell separator, or the next script mentioned,
                so two scripts on one line each get their own flags.
  identifiers   every ALL_CAPS name with an underscore (`DISPATCH_COUNTY_FIPS`,
                `EXPECT_MEMBERS`), wherever it appears — a sentence, a
                backtick, a fenced block — occurs as a WHOLE WORD in at least
                one file the same skill names; a named directory contributes
                its top-level files. A table a skill tells an agent to edit
                must still exist somewhere the skill points. A capitalised
                word with no underscore (`EXCLUDES`, `ISBE`, `KINDS`) is
                acronym-shaped and is not checked. Names that are a
                runtime's or a CI host's, not ours (NOT_OURS), are skipped.
  flags         (continued) — and harvested only from text that is a
                command: a fenced block, an inline code span, or a line that
                starts with python3 / node / bash. Prose that names a script
                and later says `git diff --stat` does not charge --stat to
                the script; the script's existence is still checked.
  negatives     a path named in order to say it is NOT there ("not
                `il/scripts/`", "`data/app` (which does not exist)", "the
                root `data/app` was removed") is read as the warning it is,
                not as a claim: a negation cue in the same sentence excuses
                it, unless the cue is "not optional"-shaped.

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

# A token is a repo path when it starts in one of these roots or carries a
# path separator and a known extension. Placeholders make it a pattern (a
# `<county>_board_scraper.py` names a family, not a file).
PATH_ROOTS = ("scripts/", "docs/", "engine/", "il/", "ny/", "ca/", "wi/", "ia/", "mi/",
              ".claude/", ".github/", "districtry/", "data/", "schema/")
PATH_EXT = (".py", ".md", ".json", ".yml", ".yaml", ".mjs", ".js", ".html",
            ".txt", ".css", ".sh")
PLACEHOLDER = re.compile(r"[<>*…{}]|\.\.\.|\$")
# `scripts/x.py:42`, `scripts/x.py.`, `scripts/x.py)` — a citation suffix, not
# part of the name.
SUFFIX = re.compile(r"(?::\d+(?:[-–]\d+)?)?[.,;:)\]]*$")

SCRIPT = r"((?:[\w-]+/)*scripts/[\w./-]+\.py)"
# The REST of a command after a script: stops at a newline (a backslash
# continuation joins the next line — that alternative comes FIRST so the
# backslash is not eaten as an ordinary character), a backtick, a shell
# separator, or the next script mention, so flags cannot leak between two
# commands on a line.
FLAG_AFTER_SCRIPT = re.compile(
    SCRIPT + r"((?:(?!(?:[\w-]+/)*scripts/[\w./-]+\.py)(?!\s*(?:&&|\|\||;|\|)(?:\s|$))(?:\\\n|[^\n`]))*)")
# A script mention preceded by one of these is a URL, an absolute path, a
# `$VAR/` prefix or a `./` — not a repo-relative path.
NOT_A_REPO_PREFIX = ("/", ".", "~", "$", ":")
FLAG = re.compile(r"(?<![\w-])(--[a-z][\w-]*)")
# Flags are harvested only from text that IS a command: a fenced block, an
# inline code span, or a line that starts like one. Prose that names a
# script and later says `git diff --stat` is not charging --stat to it.
COMMAND_LINE = re.compile(r"^\s*(?:\$\s*)?(?:[A-Z_][A-Z0-9_]*=\S+\s+)*(?:python3?|node|bash|sh)\b")
FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]+`")
SECTION = re.compile(r"§\s?(\d+(?:\.\d+){1,2})\b")
# A backticked doc named right before a § re-targets that reference.
DOC_BEFORE_SECTION = re.compile(r"`(docs/[\w./-]+\.md)`[\s,(]{0,6}§")
IDENT = re.compile(r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9]*_[A-Z0-9_]+)(?![A-Za-z0-9_])")
HEADING = re.compile(r"#{1,6}\s+(\d+(?:\.\d+){1,2})\b")

# Negation cues: a path in the same sentence as one of these is named to
# say it is NOT there. "not optional", "not the same", "not enough", "not
# only" are the shapes that use the word without negating the path.
NEGATION = re.compile(
    r"\b(?:not|no|never|isn['’]t|don['’]t|doesn['’]t|gone|removed|retired|deleted|absent|"
    r"no longer|does not exist|nonexistent|missing|nothing)\b", re.I)
NEGATION_UNLESS = re.compile(r"^\s+(?:optional|the same|enough|only|to be|all)\b", re.I)
# "don't write to `x`", "there is no longer a `x`", "`x` (which does not
# exist)", "`x` was removed" all fit in forty characters either side; a wider
# window reads "`x` sits in a TEMPLATE region, not a generated one" as a
# claim that `x` is gone.
NEGATION_WINDOW = 40

# Names that read as identifiers and are not ours to find: a runtime's own
# error codes, the CI host's environment, an egress proxy's variable, quoted
# because that is what the terminal or the workflow prints.
NOT_OURS = {
    "MODULE_NOT_FOUND", "ERR_CONNECTION_RESET", "ENOENT", "ETIMEDOUT", "ECONNRESET",
    "ECONNREFUSED", "EACCES", "ERR_", "GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_TOKEN",
    "GITHUB_STEP_SUMMARY", "GH_TOKEN", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
    "BASE_URL", "ALL_CAPS", "PLAYWRIGHT_BROWSERS_PATH", "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD",
    "UTF_8", "NOT_YET",
}

problems = []
_headings_cache = {}


def fail(msg):
    print("validate-skills: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def read_text_or_empty(path):
    """A file a skill points at may be binary (an icon in a named directory);
    it then contributes nothing to the identifier search."""
    try:
        return read(path)
    except UnicodeDecodeError:
        return ""


def frontmatter(text):
    """-> (dict, body). Enough YAML for a skill's frontmatter: `key: value`,
    quoted scalars, folded (`>`, `>-`, `>+`) and literal (`|`) block scalars
    with space- or tab-indented continuation lines. Folded lines join with
    single spaces, which is how YAML folds them and what the harness sees."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    key = None
    for line in m.group(1).split("\n"):
        km = re.match(r"([a-z_]+):\s*(.*)$", line)
        if km and not line[:1].isspace():
            key, val = km.group(1), km.group(2).strip()
            val = re.sub(r"^[>|][-+]?\d*\s*$", "", val)   # block-scalar indicator alone
            fm[key] = val
        elif key is not None and (line[:1].isspace() or line == ""):
            if line.strip():
                fm[key] = (fm[key] + " " + line.strip()).strip()
    for k, v in fm.items():
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
            if v and fm[k][0] == '"':
                v = v.replace('\\"', '"').replace("\\\\", "\\")
            fm[k] = v
    return fm, text[m.end():]


def headings_of(rel):
    """Numbered headings of one markdown doc, cached per path."""
    if rel not in _headings_cache:
        path = os.path.join(REPO_ROOT, rel)
        out = set()
        if os.path.isfile(path):
            for line in read(path).split("\n"):
                hm = HEADING.match(line)
                if hm:
                    out.add(hm.group(1))
        _headings_cache[rel] = out
    return _headings_cache[rel]


def guide_headings():
    return headings_of(os.path.relpath(GUIDE, REPO_ROOT))


def backticked(text):
    return re.findall(r"`([^`\n]+)`", text)


def sentences(text):
    """The units negation is decided in: a paragraph's lines joined, then
    split at sentence ends; each list bullet its own unit."""
    out = []
    for para in re.split(r"\n\s*\n", text):
        for chunk in re.split(r"\n(?=\s*(?:[-*]|\d+\.)\s)", para):
            joined = " ".join(l.strip() for l in chunk.split("\n"))
            out.extend(s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z`(\"'])", joined) if s)
    return out


def negated_paths(text):
    """Paths a skill names in order to say they are NOT there — the steward's
    "`scripts/smoke_test.mjs`, not `il/scripts/`", the county skill's "the
    root `data/app` does not exist". A gate that failed on those would be
    asking the prose to stop warning about the wrong path."""
    out = set()
    for sent in sentences(text):
        for m in re.finditer(r"`([^`]+)`", sent):
            tok = m.group(1).strip()
            lo, hi = max(0, m.start() - NEGATION_WINDOW), m.end() + NEGATION_WINDOW
            window = sent[lo:hi]
            for cue in NEGATION.finditer(window):
                if NEGATION_UNLESS.match(window[cue.end():]):
                    continue
                for piece in tok.split():
                    out.add(clean_path(piece))
                break
    return out


def clean_path(tok):
    return SUFFIX.sub("", tok.strip())


def is_path(tok):
    t = clean_path(tok)
    if not t or PLACEHOLDER.search(t):
        return False
    if "://" in t or "@" in t or t.startswith(("~", "/", "www.")):
        return False
    return t.startswith(PATH_ROOTS) or ("/" in t and t.endswith(PATH_EXT))


def repo_file(rel):
    """Absolute path for a repo-relative name, or None if it escapes the root."""
    full = os.path.normpath(os.path.join(REPO_ROOT, rel))
    if full != REPO_ROOT and not full.startswith(REPO_ROOT + os.sep):
        return None
    return full


def check_skill(skill_dir):
    name = os.path.basename(skill_dir)
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        problems.append("%s: no SKILL.md" % name)
        return 0
    text = read(path).replace("\r\n", "\n").lstrip("﻿")
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
    reported = set()
    # negation is decided over the description and the body — the prose —
    # never over raw frontmatter lines, where a skill's own directory name
    # ("…-missing-…") would read as a cue
    negatives = negated_paths(desc + "\n\n" + body)
    files_named = set()       # every existing file the skill points at
    # the spans of the body that are commands: fenced blocks and inline code
    command_spans = [(m.start(), m.end()) for m in FENCE.finditer(body)]
    command_spans += [(m.start(), m.end()) for m in INLINE_CODE.finditer(body)]

    def in_command(pos):
        if any(a <= pos < b for a, b in command_spans):
            return True
        line_start = body.rfind("\n", 0, pos) + 1
        return bool(COMMAND_LINE.match(body[line_start:pos + 1]))

    def note_path(rel, how):
        nonlocal checked
        checked += 1
        full = repo_file(rel)
        if full is None:
            return
        if not os.path.exists(full):
            # a path named in order to say it is NOT there is excused from
            # existing; one that exists still counts as a file the skill
            # points at, whatever the sentence around it says
            if rel in negatives:
                return
            if (name, rel) not in reported:
                reported.add((name, rel))
                problems.append("%s: names `%s`%s, which does not exist" % (name, rel, how))
        elif os.path.isfile(full):
            files_named.add(rel)
        elif os.path.isdir(full):
            for entry in sorted(os.listdir(full)):
                if os.path.isfile(os.path.join(full, entry)):
                    files_named.add(os.path.join(rel, entry))

    # paths: every backticked span, every whitespace-separated piece of it
    for tok in backticked(text):
        for piece in tok.split():
            if is_path(piece):
                note_path(clean_path(piece), "")
    # the same for a script named bare in prose or a fenced block — its
    # existence is checked whether or not its flags are
    # commands: a script named anywhere in the body — a fenced block, a
    # sentence — is a file the skill points at, and its flags are checked
    # against that script's own source
    for m in FLAG_AFTER_SCRIPT.finditer(body):
        spath, rest = m.group(1), m.group(2)
        if m.start() > 0 and body[m.start() - 1] in NOT_A_REPO_PREFIX:
            continue
        rel = clean_path(spath)
        if PLACEHOLDER.search(rel):
            continue
        note_path(rel, " (in a command)")
        full = repo_file(rel)
        if full is None or not os.path.isfile(full) or not in_command(m.start()):
            continue
        src = read(full)
        for flag in FLAG.findall(rest):
            checked += 1
            if flag not in src:
                problems.append("%s: says `%s %s`, but the script never mentions %s"
                                % (name, rel, flag, flag))
    # section references — the guide's, unless a doc is named right before
    for m in SECTION.finditer(body):
        checked += 1
        sec = m.group(1)
        before = body[max(0, m.start() - 120):m.start() + 1]
        dm = DOC_BEFORE_SECTION.search(before)
        doc = dm.group(1) if dm and before.endswith("§") and dm.end() == len(before) else None
        target = doc or os.path.relpath(GUIDE, REPO_ROOT)
        if sec not in headings_of(target):
            problems.append("%s: cites §%s, which is not a heading in %s" % (name, sec, target))
    # ALL_CAPS identifiers must live in some file the skill names — a table it
    # tells an agent to edit (EXPECT_MEMBERS, an EXCLUDES list in a workflow)
    # has to still exist somewhere the skill points.
    sources = "\n".join(read_text_or_empty(os.path.join(REPO_ROOT, rel))
                        for rel in sorted(files_named))
    # a capitalised stem inside a path (`docs/ASK_DRAFTS.md`) is the path's,
    # not an identifier — blank paths before harvesting
    prose = re.sub(r"[\w./-]*/[\w./-]+", " ", body)
    for tok in sorted(set(IDENT.findall(prose))):
        if tok in NOT_OURS or any(tok.startswith(p) for p in NOT_OURS if p.endswith("_")):
            continue
        checked += 1
        if not re.search(r"(?<![A-Za-z0-9_])" + re.escape(tok) + r"(?![A-Za-z0-9_])", sources):
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
    if not guide_headings():
        fail("no numbered headings in %s" % os.path.relpath(GUIDE, REPO_ROOT))
    skills = sorted(d for d in glob.glob(os.path.join(SKILLS_DIR, "*")) if os.path.isdir(d))
    if not skills:
        fail("no skills under .claude/skills/")
    total = 0
    for d in skills:
        total += check_skill(d)

    if problems:
        for p in problems:
            print("  - " + p, file=sys.stderr)
        fail("%d pointer(s) in %d skill(s) point at nothing" % (len(problems), len(skills)))
    print("validate-skills: OK — %d skill(s), %d pointer(s) resolve (paths, §sections, "
          "flags, identifiers)" % (len(skills), total))


if __name__ == "__main__":
    main()

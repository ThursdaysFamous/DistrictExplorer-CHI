#!/usr/bin/env python3
"""
Retention gate: catch a roster field that quietly stops being published.

WHY THIS EXISTS. Every roster builder in this repo guards a COUNT — "Boone must
seat 12", "Brown must seat 7" — and every one of those guards passed on
2026-08-08 while Brown County's seven published e-mail addresses were one
commit away from being deleted. browncoil.org had switched on Cloudflare's
e-mail obfuscation, so every `mailto:` became `data-cfemail`; the parser read
`mailto:` only and returned seven members with no e-mail at all. Seven rows in,
seven rows out, guard satisfied, contact silently gone from a tool whose entire
purpose is telling residents how to reach their board.

THE GUARDS MEASURED THE WRONG THING. Counting rows says nothing about whether
the rows still carry what they carried yesterday. Thirty of the forty-three
builders do additionally floor a field or two (MIN_EMAILS, MIN_PHONES), which
is better — but each floor is hand-set per county, thirteen builders have none
at all, and NO floor anywhere covers a field nobody thought to name. A new
field ships unguarded by construction.

So this check does not live in the builders. It compares the roster files in
the working tree against the same files at a git ref — usually the PR's base —
and asks one question of every field it finds: does it still appear on about as
many records as it did before? The shipped file is the baseline, so a field
gains protection the moment it first ships, with nothing to configure and no
per-county tuning to drift.

WHAT IT FAILS ON
  * A field that was on >= MIN_PRESENT records and is now on NONE. This is the
    Brown shape, and the one this check was written for.
  * A field that lost at least HALF its records AND at least MIN_ABSOLUTE_DROP
    of them. Turnover moves these numbers by ones and twos; a parser that
    stopped seeing a column moves them by tens.
  * The record count itself collapsing by half — the builders' own province,
    re-checked here for the files whose builder has no floor.

WHAT IT DELIBERATELY IGNORES
  * New files and new fields (nothing to compare against).
  * Small drops. A member leaves, a county drops one phone number: that is the
    world changing, not the pipeline breaking.
  * Files absent from the base ref.

ACCEPTING A REAL DROP. A consolidated election can legitimately empty a column
for a while. Record it in ACCEPTED_DROPS with a reason and a date rather than
loosening a threshold for everyone — same posture as validate_sources.py's
`blocked` flag, and it prints a line every run so an entry cannot rot quietly.

Usage:
    python3 scripts/check_roster_retention.py                  # vs HEAD
    python3 scripts/check_roster_retention.py --base origin/main
    python3 scripts/check_roster_retention.py --report r.md
"""

import argparse
import collections
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

# A field on a single record is one person's phone number; losing it is
# turnover. Two is where "the source stopped saying this" becomes the more
# likely reading than "two people happened to leave" — it is what makes a
# two-role file like lake-county-board-roles.json protected at all.
MIN_PRESENT = 2
# A halving only fails if it is also this many records, so a 3 -> 1 wobble on a
# tiny board does not cry wolf.
MIN_ABSOLUTE_DROP = 3
RECORD_COLLAPSE_RATIO = 0.5

# ---------------------------------------------------------------------------
# Measured, dated exceptions. Key: "<file>:<field>". Value: why, and when it was
# accepted. Keep these rare — each one is a field this check has stopped
# watching, which is exactly what it exists to prevent.
# ---------------------------------------------------------------------------
ACCEPTED_DROPS = {}


def records_in(payload):
    """Every dict that looks like a person/place record — one with a name.

    Shape-agnostic on purpose: these files are keyed by district, by county
    slug, by GEOID and by nothing at all, and several nest members two levels
    down. Anything with a `name` is a record, which matched all 58 roster-shaped
    files in data/app when this was calibrated.
    """
    found = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("name"), str):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return found


def coverage(payload):
    """field -> how many records carry a non-empty value. Plus the record count."""
    recs = records_in(payload)
    counts = collections.Counter()
    for rec in recs:
        for key, value in rec.items():
            if value in (None, "", [], {}):
                continue
            counts[key] += 1
    return counts, len(recs)


# A file pooling more than this many independent sources is checked whole
# rather than per group. Below it, each top-level key is its own source and
# gets its own check; above it (municipal-officials.json pools ~1,500
# municipalities) per-group thresholds would fire on every village that
# reshuffles a page, and the file-level view still shows a systemic loss.
MAX_GROUPS_FOR_PER_GROUP = 200
# A group needs at least this many records before a vanished field there means
# more than one person's details changing.
MIN_GROUP_RECORDS = 3


def groups_of(payload):
    """{group label -> sub-payload} for a file keyed by county/district, else {}.

    THIS IS THE FIX FOR THE CASE THAT PROMPTED THE WHOLE CHECK. Pooled across a
    file, Brown's seven e-mails vanishing reads as 40 -> 33 in
    il-county-commissioners.json — an 18% dip, under every sane threshold, and
    the first version of this script passed it. Ten counties share that file and
    each is a separate source that can break on its own, so each is measured on
    its own.
    """
    if not isinstance(payload, dict):
        return {}
    groups = {key: value for key, value in payload.items()
              if isinstance(value, (dict, list)) and records_in(value)}
    if not groups or len(groups) > MAX_GROUPS_FOR_PER_GROUP:
        return {}
    return groups


def git_show(ref, rel_path):
    """The file's content at `ref`, or None if it is not there."""
    try:
        out = subprocess.run(["git", "show", "%s:%s" % (ref, rel_path)],
                             cwd=REPO_ROOT, capture_output=True, check=False)
    except OSError as e:
        raise SystemExit("check-roster-retention: cannot run git (%s)" % e)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout.decode("utf-8"))
    except ValueError:
        return None


def compare(name, old, new):
    """Findings for one file. Each is (severity, message)."""
    out = []
    old_counts, old_recs = coverage(old)
    new_counts, new_recs = coverage(new)

    if old_recs >= MIN_ABSOLUTE_DROP and new_recs < old_recs * RECORD_COLLAPSE_RATIO:
        out.append(("FAIL", "record count fell %d -> %d (more than half). The "
                            "builder's own count guard should have caught this — "
                            "check that it ran." % (old_recs, new_recs)))

    for field, was in sorted(old_counts.items()):
        now = new_counts.get(field, 0)
        if now >= was:
            continue
        accepted = ACCEPTED_DROPS.get("%s:%s" % (name, field))
        lost = was - now
        if now == 0 and was >= MIN_PRESENT:
            msg = ("`%s` VANISHED — was on %d of %d records, now on none. This is "
                   "the shape of a source that changed how it publishes the field, "
                   "not of people leaving. Check the page before accepting it."
                   % (field, was, old_recs))
            out.append(("OK-accepted" if accepted else "FAIL",
                        msg + (" ACCEPTED: %s" % accepted if accepted else "")))
        elif lost >= MIN_ABSOLUTE_DROP and now <= was * 0.5:
            msg = ("`%s` lost %d of %d records (now %d) — at least half. Turnover "
                   "moves these by ones and twos." % (field, lost, was, now))
            out.append(("OK-accepted" if accepted else "FAIL",
                        msg + (" ACCEPTED: %s" % accepted if accepted else "")))

    # Per-source pass: one broken county inside a shared file is invisible in
    # the totals above, which is exactly how the first draft of this script
    # waved Brown through.
    old_groups, new_groups = groups_of(old), groups_of(new)
    for label, old_sub in sorted(old_groups.items()):
        new_sub = new_groups.get(label)
        if new_sub is None:
            continue                      # the group left the file: not this check's call
        sub_old, sub_old_recs = coverage(old_sub)
        sub_new, _ = coverage(new_sub)
        if sub_old_recs < MIN_GROUP_RECORDS:
            continue
        for field, was in sorted(sub_old.items()):
            if sub_new.get(field, 0) or was < MIN_PRESENT:
                continue
            accepted = ACCEPTED_DROPS.get("%s:%s:%s" % (name, label, field)) \
                or ACCEPTED_DROPS.get("%s:%s" % (name, field))
            msg = ("`%s` VANISHED for %s — was on %d of that group's %d records, "
                   "now on none, while the rest of the file is unchanged. That is "
                   "one source changing how it publishes, which the file-wide "
                   "totals hide." % (field, label, was, sub_old_recs))
            out.append(("OK-accepted" if accepted else "FAIL",
                        msg + (" ACCEPTED: %s" % accepted if accepted else "")))
    return out, old_recs, new_recs


def main():
    ap = argparse.ArgumentParser(
        description="Fail when a roster field stops being published.")
    ap.add_argument("--base", default="HEAD",
                    help="git ref to compare against (default HEAD)")
    ap.add_argument("--report", metavar="PATH", help="also write a markdown report")
    args = ap.parse_args()

    findings, checked, skipped = [], 0, []
    for path in sorted(os.listdir(APP_DATA_DIR)):
        if not path.endswith(".json"):
            continue
        rel = os.path.join("data", "app", path)
        full = os.path.join(APP_DATA_DIR, path)
        try:
            with open(full, encoding="utf-8") as f:
                new = json.load(f)
        except (ValueError, OSError):
            continue
        if not records_in(new):
            continue                      # geometry-only file: nothing to retain
        old = git_show(args.base, rel)
        if old is None:
            skipped.append(path)          # new file, or absent at the base ref
            continue
        checked += 1
        rows, old_recs, new_recs = compare(path, old, new)
        for sev, msg in rows:
            findings.append((sev, path, msg))

    fails = [f for f in findings if f[0] == "FAIL"]
    accepted = [f for f in findings if f[0] == "OK-accepted"]

    lines = ["# Roster field retention", "",
             "Compared %d roster files against `%s`." % (checked, args.base)]
    if skipped:
        lines.append("New since that ref (nothing to compare): %s."
                     % ", ".join("`%s`" % s for s in skipped))
    lines.append("")
    if fails:
        lines += ["## FAIL (%d)" % len(fails), ""]
        lines += ["- **%s** — %s" % (p, m) for _, p, m in fails] + [""]
    if accepted:
        lines += ["## Accepted drops (%d)" % len(accepted), "",
                  "Recorded in `ACCEPTED_DROPS`. Each is a field this check has "
                  "stopped watching — re-read them now and then.", ""]
        lines += ["- **%s** — %s" % (p, m) for _, p, m in accepted] + [""]
    if not fails and not accepted:
        lines += ["Every field still appears on about as many records as before.", ""]
    report = "\n".join(lines).rstrip() + "\n"

    sys.stdout.write(report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)

    if fails:
        print("check-roster-retention: FAIL — %d field(s) stopped being published"
              % len(fails), file=sys.stderr)
        sys.exit(1)
    print("check-roster-retention: OK — %d roster files, no field lost its records"
          % checked)


if __name__ == "__main__":
    main()

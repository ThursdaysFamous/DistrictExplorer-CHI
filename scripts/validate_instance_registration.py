#!/usr/bin/env python3
"""
Registration gate: an instance must be registered EVERYWHERE, not almost.

WHY THIS EXISTS. Adding a state to this fleet is not one edit. The instance is
a folder, and a dozen other places have to learn its tag: the generator's
INSTANCES table, the fleet manifest, four hand-kept tables in four builders,
and three literal five-line lists inside .github/workflows/smoke-test.yml. Five
consumers DISCOVER the fleet instead (check_roster_retention.py,
validate_card_links.py, build_dark_map_palette.py, validate_workflow_deps.py,
fleet_status.py) and need nothing; the rest are lists somebody wrote once.

Nothing measured that they agree, and twice the miss shipped:

  * validate_card_links.py's APP_DATA_DIRS named four instances out of five in
    the very commit whose comment said a new county is covered with nothing to
    update. 303 URLs, 52 of them authored, where a dead link would have stayed
    green forever.
  * check_roster_retention.py pointed at il/data/app alone, so a bot PR that
    stripped `party`, `capitolOffice` and `districtOffice` from all 213 New
    York legislators passed with "222 roster files, no field lost its records".

Both were found by hand, weeks apart, and both are the same failure: a gate
whose SURFACE is a hand-kept list, checked against nothing. Those two were
fixed by making them discover. The tables below cannot discover — a worksheet
path and a compose target are per-instance facts, not derivable — so they are
checked instead.

WHAT IS CANONICAL. The TREE, not any table: a top-level directory carrying both
an index.html and a data/app/ IS an instance, which is the same rule
validate_card_links.py discovers by. That direction matters. Taking the
generator's INSTANCES as truth would make this gate agree with itself about a
sixth instance nobody registered — the folder is the thing that exists, and
every table is a claim about it.

WHAT IT DOES NOT CHECK. That a registered instance is CORRECT — that its
worksheet path resolves, its compose targets are right, its smoke test passes.
Other gates own those. This one asks only: does every surface know the
instance is there?

Usage:
    python3 scripts/validate_instance_registration.py
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(".github", "workflows", "smoke-test.yml")

problems = []


def fail(msg):
    problems.append(msg)


def read(rel):
    with open(os.path.join(REPO_ROOT, rel), encoding="utf-8") as f:
        return f.read()


def discovered_instances():
    """Every top-level directory that IS an instance — index.html + data/app/.

    The same rule validate_card_links.py uses to find the surfaces it probes,
    and deliberately NOT generate_metro_files.INSTANCES: that table is one of
    the things being checked, so trusting it here would let a sixth instance
    folder sit unregistered while this gate reported agreement.
    """
    found = set()
    for name in sorted(os.listdir(REPO_ROOT)):
        full = os.path.join(REPO_ROOT, name)
        if not os.path.isdir(full) or name.startswith("."):
            continue
        if (os.path.isfile(os.path.join(full, "index.html"))
                and os.path.isdir(os.path.join(full, "data", "app"))):
            found.add(name)
    return found


def table_tags(module, attr):
    """The instance tags named by a builder's hand-kept table.

    Imported rather than parsed: these are plain literals today, but a table
    that grows a comprehension should still be readable, and importing is what
    the consumer itself does.
    """
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    try:
        mod = __import__(module)
        value = getattr(mod, attr)
    except Exception as e:                       # noqa: BLE001 - reported, not raised
        fail("cannot read %s.%s (%s) — this gate cannot tell whether a new "
             "instance is registered there" % (module, attr, e))
        return None
    finally:
        sys.path.pop(0)
    if isinstance(value, dict):
        return set(value)
    if isinstance(value, (list, tuple)):
        return {v[0] if isinstance(v, (list, tuple)) else v for v in value}
    fail("%s.%s is a %s — this gate does not know how to read it"
         % (module, attr, type(value).__name__))
    return None


# Each row: (label, tags, where to fix it). A table missing an instance names
# the file and the symbol, because "wi is not registered" without an address
# sends the reader to grep.
def check_tables(expected):
    for module, attr in (("generate_metro_files", "INSTANCES"),
                         ("build_history_page", "INSTANCES"),
                         ("build_landing_page", "INSTANCE_WORKSHEET"),
                         ("build_manifests", "INSTANCES"),
                         ("compose_app", "INSTANCES")):
        tags = table_tags(module, attr)
        if tags is None:
            continue
        missing = expected - tags
        extra = tags - expected
        if missing:
            fail("scripts/%s.py's %s does not name %s — add the instance there, "
                 "beside the ones already listed" % (module, attr, sorted(missing)))
        if extra:
            fail("scripts/%s.py's %s names %s, which is not an instance in this "
                 "tree (no <tag>/index.html + <tag>/data/app/). A retired "
                 "instance leaves its table entry behind."
                 % (module, attr, sorted(extra)))


def check_manifest(expected):
    """metros.json is the fleet's own list, and the landing page renders it."""
    try:
        payload = json.loads(read("metros.json"))
    except (ValueError, OSError) as e:
        fail("cannot read metros.json (%s)" % e)
        return
    entries = payload["metros"] if isinstance(payload, dict) and "metros" in payload \
        else payload
    if isinstance(entries, dict):
        entries = list(entries.values())
    tags = {e.get("tag") for e in entries if isinstance(e, dict) and e.get("tag")}
    missing = expected - tags
    extra = tags - expected
    if missing:
        fail("metros.json has no entry tagged %s — the fleet manifest drives the "
             "landing page, the coverage map and the privacy page, so an "
             "unlisted instance is invisible on all three" % sorted(missing))
    if extra:
        fail("metros.json is tagged %s, which is not an instance in this tree"
             % sorted(extra))


# The three per-instance command lists in the CI workflow. Each is five literal
# lines today; a sixth instance needs all three edited, and a missed one means
# that instance simply is not tested while the job stays green.
WORKFLOW_LISTS = (
    ("the per-instance static gate",
     r"validate_index\.py\s+(\w+)/index\.html", None),
    ("the per-instance browser smoke test",
     r"BASE_URL=\S*localhost:8000/(\w+)/", None),
    # Illinois is the bare invocation with no --out, so it is supplied rather
    # than matched: a pattern loose enough to catch it would also catch the
    # --check line above it.
    ("the per-instance coverage-gaps check",
     r"--out (\w+)/data/app/coverage-gaps\.json", "il"),
)


def check_workflow(expected):
    try:
        src = read(WORKFLOW)
    except OSError as e:
        fail("cannot read %s (%s)" % (WORKFLOW, e))
        return
    for label, pattern, implied in WORKFLOW_LISTS:
        tags = set(re.findall(pattern, src))
        if implied:
            tags.add(implied)
        missing = expected - tags
        if missing:
            fail("%s does not run %s for %s — the job would stay green without "
                 "ever testing %s" % (WORKFLOW, label, sorted(missing),
                                      "them" if len(missing) > 1 else "it"))
        extra = tags - expected
        if extra:
            fail("%s runs %s for %s, which is not an instance in this tree"
                 % (WORKFLOW, label, sorted(extra)))


def main():
    expected = discovered_instances()
    if len(expected) < 2:
        # A gate that verifies nothing passes forever; this is the shape of a
        # wrong working directory, and it looks exactly like success otherwise.
        print("validate-instance-registration: FAIL — found %d instance "
              "director%s in %s (expected at least 2). Nothing was verified; "
              "run this from the repo root."
              % (len(expected), "y" if len(expected) == 1 else "ies", REPO_ROOT),
              file=sys.stderr)
        sys.exit(1)

    check_tables(expected)
    check_manifest(expected)
    check_workflow(expected)

    if problems:
        for p in problems:
            print("FAIL: %s" % p, file=sys.stderr)
        print("validate-instance-registration: FAIL — %d surface(s) disagree "
              "with the %d instance(s) in the tree (%s)"
              % (len(problems), len(expected), ", ".join(sorted(expected))),
              file=sys.stderr)
        sys.exit(1)

    print("validate-instance-registration: OK — %d instance(s) (%s) registered "
          "in 5 table(s), metros.json and %d workflow list(s)"
          % (len(expected), ", ".join(sorted(expected)), len(WORKFLOW_LISTS)))


if __name__ == "__main__":
    main()

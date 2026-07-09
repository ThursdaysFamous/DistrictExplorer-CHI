#!/usr/bin/env python3
"""
Post-rewrite sanity gate for index.html.

The weekly roster workflows regenerate object literals inside the ~400 KB
index.html by regex-splicing (scripts/build_il_roster.py, build_cpd_roster.py)
and open a PR. Those builders validate their *input* (they refuse an
incomplete roster) but nothing checked that the *output* file is still a
working page — a mis-anchored replacement can silently drop code, and a bad
escape can corrupt an embedded blob. This script is that check: run it after
any rewrite and before opening a PR.

Checks (all must pass; exits non-zero on the first failure):
  1. The main inline <script> still parses (`node --check`) — catches syntax
     death from a malformed splice.
  2. registerLayer( appears at least as many times as expected — catches a
     regex overmatch that deletes whole layer modules.
  3. Every `var X = JSON.parse('...')` embedded dataset still round-trips
     through JSON.parse — catches a broken string escape in a data blob.
  4. The roster/data variables the builders rewrite are still present.

Usage:
    python3 scripts/validate_index.py [path/to/index.html]
"""

import json
import os
import re
import subprocess
import sys
import tempfile

# Floor, not a moving target: 1 function definition + 11 direct registerLayer()
# calls + 3 factory bodies. New layers only raise this; a drop means modules
# were lost.
MIN_REGISTER_LAYER = 15

REQUIRED_VARS = [
    "SCHOOL_BOARD_DISTRICTS_GEOJSON",
    "IL_SUPREME_COURT_DISTRICTS_GEOJSON",
    "CCBR_DISTRICTS_GEOJSON",
    "IL_SENATE_MEMBERS",
    "IL_HOUSE_MEMBERS",
    "CPD_DISTRICT_INFO",
]


def fail(msg):
    print("validate_index: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def js_unescape_single_quoted(s):
    # reverse of the builders' single-quoted-literal escaping
    return s.replace("\\/", "/").replace("\\'", "'").replace("\\\\", "\\")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    if not os.path.exists(path):
        fail("no such file: " + path)
    html = open(path).read()

    # 1. main inline script parses
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    if not scripts:
        fail("no inline <script> blocks found")
    main_script = max(scripts, key=len)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
        tf.write(main_script)
        js_path = tf.name
    try:
        proc = subprocess.run(["node", "--check", js_path], capture_output=True, text=True)
    finally:
        os.unlink(js_path)
    if proc.returncode != 0:
        fail("inline script failed `node --check`:\n" + (proc.stderr or proc.stdout))

    # 2. no modules lost
    n = len(re.findall(r"registerLayer\(", html))
    if n < MIN_REGISTER_LAYER:
        fail("registerLayer( count %d < expected floor %d — a module was likely deleted" % (n, MIN_REGISTER_LAYER))

    # 3. embedded data blobs still parse
    for m in re.finditer(r"var (\w+) = JSON\.parse\('(.*)'\);", html):
        name = m.group(1)
        try:
            json.loads(js_unescape_single_quoted(m.group(2)))
        except Exception as e:
            fail("embedded blob %s no longer parses as JSON: %s" % (name, e))

    # 4. rewrite targets still present
    missing = [v for v in REQUIRED_VARS if ("var " + v + " =") not in html]
    if missing:
        fail("expected variable(s) missing after rewrite: %s" % missing)

    print(
        "validate_index: OK — inline script parses, %d registerLayer( calls, "
        "all embedded blobs parse, all rewrite targets present" % n
    )


if __name__ == "__main__":
    main()

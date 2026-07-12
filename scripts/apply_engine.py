#!/usr/bin/env python3
"""
Apply the pinned engine release into this fork (docs/MECHANIZATION_PLAYBOOK.md,
Conversion 1 — the consume side of scripts/build_engine_artifact.py).

Reads engine.lock.json:

    { "engine_version": "engine-vX.Y.Z", "sha256": "…",
      "source_repo": "ThursdaysFamous/DistrictExplorer-CHI" }

then takes engine.bundle.js + engine.manifest.json (downloading them from the
pinned GitHub release when they are not already on disk — CI downloads them
first with `gh release download` + `sha256sum --check`), verifies everything,
and splices each ENGINE block back into index.html and sw.js between its
existing fences. The fences stay: they are assembly markers.

Fails hard (exit 1, nothing written) on:
  - sha256 mismatch between the bundle and the lockfile pin,
  - manifest that disagrees with the lockfile (version or sha256),
  - bundle whose block names/order or per-block byte lengths disagree with
    the manifest,
  - a manifest block missing from the target file, or a fenced block in the
    target file the manifest does not know (fence-count mismatch),
  - malformed fences anywhere,
  - a target with CR/CRLF line endings (the splice is defined on LF-only
    files and must never rewrite bytes outside the fences).

Both target files are spliced in memory and self-checked (re-extracting the
result must reproduce the bundle bodies exactly) before either is written, so
a failure never leaves the tree half-applied.

This script ships as a release asset alongside the bundle — the release is the
distribution channel for shared scripts. It imports the fence parser from
scripts/check_engine_parity.py (one parser, never forked), which every fork
already carries as part of the shared engine.

Usage (from the repo root; all paths have working defaults):
    python3 scripts/apply_engine.py
        [--lock engine.lock.json] [--bundle engine.bundle.js]
        [--manifest engine.manifest.json] [--index index.html] [--sw sw.js]
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_engine_parity import MARKER_RE, extract_blocks  # noqa: E402  (shared parser — do not fork)


def fail(msg):
    print("apply-engine: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def read_lock(path):
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
    except (OSError, ValueError) as e:
        fail("cannot read lockfile %s: %s" % (path, e))
    for key in ("engine_version", "sha256", "source_repo"):
        if not lock.get(key):
            fail("lockfile %s is missing %r" % (path, key))
    return lock


def download_asset(lock, asset, dest):
    url = "https://github.com/%s/releases/download/%s/%s" % (
        lock["source_repo"], lock["engine_version"], asset)
    print("apply-engine: downloading %s" % url)
    req = urllib.request.Request(url, headers={"User-Agent": "district-explorer-apply-engine"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except OSError as e:
        fail("could not download %s: %s" % (url, e))
    with open(dest, "wb") as f:
        f.write(data)


def splice(text, bodies):
    """Replace the interior of every fenced block in `text` with the body from
    `bodies` ({name: body}); marker lines and everything outside the fences are
    preserved verbatim (the walk is on text.split("\\n"), so it never rewrites
    bytes it does not own). Returns (new_text, changed_names, spliced_names) —
    changed_names is byte-accurate (old interior lines vs new interior lines),
    spliced_names lets callers assert every expected fence was actually seen.
    Raises ValueError if the line walk sees an END without its BEGIN, which a
    pre-validated file can only produce via a non-LF line separator glued to a
    marker line. build_engine_artifact.py reuses this same splicer for its
    byte-fidelity round-trip gate — one splicer, never forked."""
    out = []
    changed = []
    spliced = []
    cur_name = None
    cur_old = None
    for line in text.split("\n"):
        m = MARKER_RE.match(line)
        if m:
            kind, name = m.groups()
            if kind == "BEGIN":
                out.append(line)
                cur_name, cur_old = name, []
                continue
            if cur_name is None:
                raise ValueError(
                    "ENGINE:END %s without a BEGIN during splice — a non-LF line "
                    "separator is hiding a marker line" % name)
            new_lines = bodies[cur_name].split("\n")
            out.extend(new_lines)
            if new_lines != cur_old:
                changed.append(cur_name)
            spliced.append(cur_name)
            out.append(line)
            cur_name, cur_old = None, None
        elif cur_name is not None:
            cur_old.append(line)
        else:
            out.append(line)
    return "\n".join(out), changed, spliced


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lock", default="engine.lock.json", help="lockfile pinning version + sha256")
    ap.add_argument("--bundle", default="engine.bundle.js", help="engine bundle (downloaded if absent)")
    ap.add_argument("--manifest", default="engine.manifest.json", help="engine manifest (downloaded if absent)")
    ap.add_argument("--index", default="index.html", help="target index.html to splice into")
    ap.add_argument("--sw", default="sw.js", help="target sw.js to splice into")
    args = ap.parse_args()

    lock = read_lock(args.lock)
    for asset, path in ((os.path.basename(args.bundle), args.bundle),
                        (os.path.basename(args.manifest), args.manifest)):
        if not os.path.exists(path):
            download_asset(lock, asset, path)

    # 1. The lockfile sha256 is the load-bearing integrity check.
    with open(args.bundle, "rb") as f:
        bundle_bytes = f.read()
    sha = hashlib.sha256(bundle_bytes).hexdigest()
    if sha != lock["sha256"]:
        fail("bundle sha256 mismatch:\n  lockfile pins %s\n  %s is     %s"
             % (lock["sha256"], args.bundle, sha))

    # 2. The manifest must describe exactly this bundle and this pin.
    try:
        with open(args.manifest, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as e:
        fail("cannot read manifest %s: %s" % (args.manifest, e))
    if manifest.get("sha256") != lock["sha256"]:
        fail("manifest sha256 %s does not match lockfile pin %s"
             % (manifest.get("sha256"), lock["sha256"]))
    if manifest.get("engine_version") != lock["engine_version"]:
        fail("manifest was built for %s but the lockfile pins %s"
             % (manifest.get("engine_version"), lock["engine_version"]))
    entries = manifest.get("blocks")
    if not entries:
        fail("manifest has no blocks list")

    # 3. The bundle must parse back to exactly what the manifest declares.
    try:
        parsed = extract_blocks(bundle_bytes.decode("utf-8"), args.bundle)
    except (ValueError, UnicodeDecodeError) as e:
        fail("bundle does not parse: %s" % e)
    if list(parsed) != [e["name"] for e in entries]:
        fail("bundle block names/order disagree with the manifest")
    for entry in entries:
        got = len(parsed[entry["name"]].encode("utf-8"))
        if got != entry["bytes"]:
            fail("block %r is %d bytes but the manifest says %d"
                 % (entry["name"], got, entry["bytes"]))

    # 4. Map manifest blocks onto the target files.
    targets = {"index.html": args.index, "sw.js": args.sw}
    per_file = {}
    for entry in entries:
        if entry["file"] not in targets:
            fail("manifest block %r belongs to unknown file %r" % (entry["name"], entry["file"]))
        per_file.setdefault(entry["file"], {})[entry["name"]] = parsed[entry["name"]]

    # 5. Splice every file in memory first; write only when all succeed.
    results = []
    for fname, bodies in per_file.items():
        path = targets[fname]
        try:
            # newline="" — no universal-newline translation: this script owns
            # only the fence interiors and must never rewrite the rest of the
            # file (a CRLF target would otherwise come out LF-normalized on
            # every line).
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
        except OSError as e:
            fail("cannot read target %s: %s" % (path, e))
        if "\r" in text:
            fail("%s contains CR/CRLF line endings — the engine splice is defined on "
                 "LF-only files; normalize the file's line endings first" % path)
        try:
            existing = extract_blocks(text, path)
        except ValueError as e:
            fail(str(e))
        missing = [n for n in bodies if n not in existing]
        extra = [n for n in existing if n not in bodies]
        if missing:
            fail("%s is missing ENGINE block(s) the manifest requires: %s"
                 % (path, ", ".join(missing)))
        if extra:
            fail("fence-count mismatch: %s has ENGINE block(s) the manifest does not know: %s"
                 % (path, ", ".join(extra)))
        try:
            new_text, changed, spliced = splice(text, bodies)
        except ValueError as e:
            fail("%s: %s" % (path, e))
        not_spliced = [n for n in bodies if n not in spliced]
        if not_spliced:
            fail("%s: block(s) %s were never reached by the splice — a non-LF line "
                 "separator is hiding their marker lines" % (path, ", ".join(not_spliced)))
        if extract_blocks(new_text, path) != bodies:
            fail("internal error: re-extracting %s after splice does not reproduce the bundle" % path)
        results.append((path, new_text, len(bodies), len(changed)))

    for path, new_text, n_blocks, changed in results:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        print("apply-engine: %s — %d blocks spliced (%d updated, %d already current)"
              % (path, n_blocks, changed, n_blocks - changed))
    print("apply-engine: OK — %s (%s) applied" % (lock["engine_version"], lock["sha256"][:12]))


if __name__ == "__main__":
    main()

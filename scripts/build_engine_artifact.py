#!/usr/bin/env python3
"""
Build the distributable engine artifact (docs/MECHANIZATION_PLAYBOOK.md, Conversion 1).

Extracts every fenced ENGINE block from index.html and sw.js (the fences are
the assembly markers — see docs/ENGINE_SYNC.md) and concatenates them, in
document order (index.html first, then sw.js), into:

    engine.bundle.js      — the blocks, each re-wrapped in its own
                            /* ==== ENGINE:BEGIN/END name ==== */ markers, so
                            the bundle is parsed back with the exact same fence
                            parser that produced it. It is a fenced container,
                            NOT an executable script (some blocks are CSS/HTML).
    engine.manifest.json  — engine_version, source_repo, sha256 of the bundle,
                            and the ordered block list with per-block source
                            file + body byte length.

Both outputs are byte-deterministic — no timestamps, sorted JSON keys — so the
same tree always builds to the same sha256, which is what engine.lock.json pins
and what apply_engine.py / `sha256sum --check` verify at deploy time.

This script runs in CHI only (the reference implementation publishes; forks
consume via scripts/apply_engine.py). The fence parser is imported from
scripts/check_engine_parity.py — one parser, never forked.

Usage:
    python3 scripts/build_engine_artifact.py --out dist/ [--version engine-vX.Y.Z]

--version defaults to the engine_version pinned in engine.lock.json when that
file exists (so a local rebuild is comparable to the pin), else a -dev stamp.
Prints the bundle sha256; exits non-zero on malformed fences, a source file
that does not round-trip byte-identically through the fence parser (non-LF
line separators or empty fence pairs — the artifact would silently rewrite
them on apply), or a bundle that fails its own parse-back self-check.
"""

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_engine_parity import extract_blocks  # noqa: E402  (shared parser — do not fork)
from apply_engine import splice  # noqa: E402  (shared splicer — do not fork)

SOURCE_REPO = "ThursdaysFamous/DistrictExplorer-CHI"
BUNDLE_NAME = "engine.bundle.js"
MANIFEST_NAME = "engine.manifest.json"
# Document order is the deterministic bundle order: every block of index.html
# in order of appearance, then every block of sw.js.
ENGINE_FILES = ["index.html", "sw.js"]


def fail(msg):
    print("build-engine-artifact: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def collect_blocks(root):
    """Return [(file, name, body)] in document order across ENGINE_FILES."""
    ordered = []
    seen = {}
    for fname in ENGINE_FILES:
        path = os.path.join(root, fname)
        try:
            # newline="" — read the exact bytes; the fidelity gate below must
            # compare against the file as committed, not a translated view.
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
        except OSError as e:
            fail("cannot read %s: %s" % (path, e))
        if "\r" in text:
            fail("%s contains CR/CRLF line endings — engine files must be LF-only" % fname)
        try:
            blocks = extract_blocks(text, fname)  # insertion order == document order
        except ValueError as e:
            fail(str(e))
        if not blocks:
            fail("%s contains no ENGINE blocks — fences were deleted?" % fname)
        # Byte-fidelity gate: splicing the extracted bodies straight back into
        # the source must reproduce it byte-for-byte, or the artifact would
        # silently rewrite the file on apply. This rejects the two inputs the
        # fence parser cannot represent faithfully: a non-LF line separator
        # (U+2028/U+2029/NEL/...) inside a block body, and an empty fence pair
        # (BEGIN immediately followed by END).
        try:
            reconstructed, _changed, spliced = splice(text, blocks)
        except ValueError as e:
            fail("%s: %s" % (fname, e))
        if set(spliced) != set(blocks) or reconstructed != text:
            fail("%s does not round-trip byte-identically through the fence parser — an "
                 "ENGINE block contains a non-LF line separator (U+2028/U+2029/NEL/...) or "
                 "an empty fence pair; rewrite the block as plain LF lines" % fname)
        for name, body in blocks.items():
            # extract_blocks guards per-file duplicates; the manifest maps
            # name -> file, so names must also be unique ACROSS files.
            if name in seen:
                fail("ENGINE block %r appears in both %s and %s — block names must be globally unique"
                     % (name, seen[name], fname))
            seen[name] = fname
            ordered.append((fname, name, body))
    return ordered


def render_bundle(ordered):
    parts = []
    for _fname, name, body in ordered:
        parts.append("/* ==== ENGINE:BEGIN %s ==== */\n%s\n/* ==== ENGINE:END %s ==== */"
                     % (name, body, name))
    return "\n".join(parts) + "\n"


def default_version(root):
    lock_path = os.path.join(root, "engine.lock.json")
    if os.path.exists(lock_path):
        try:
            with open(lock_path, encoding="utf-8") as f:
                return json.load(f)["engine_version"]
        except (ValueError, KeyError, OSError) as e:
            fail("engine.lock.json exists but is unusable for --version default: %s" % e)
    return "engine-v0.0.0-dev"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root containing index.html and sw.js (default: .)")
    ap.add_argument("--out", default="dist", help="output directory for the bundle + manifest (default: dist)")
    ap.add_argument("--version", default=None,
                    help="engine version to stamp into the manifest (default: engine.lock.json pin, else engine-v0.0.0-dev)")
    args = ap.parse_args()

    version = args.version or default_version(args.root)
    ordered = collect_blocks(args.root)
    bundle = render_bundle(ordered)

    # Parse-back self-check: the bundle must yield byte-identical bodies with
    # the same parser apply_engine.py uses, or the artifact is unusable.
    reparsed = extract_blocks(bundle, BUNDLE_NAME)
    if list(reparsed) != [name for _f, name, _b in ordered]:
        fail("bundle parse-back changed block order/names — parser and renderer disagree")
    for _fname, name, body in ordered:
        if reparsed[name] != body:
            fail("bundle parse-back changed the body of block %r — parser and renderer disagree" % name)

    bundle_bytes = bundle.encode("utf-8")
    sha = hashlib.sha256(bundle_bytes).hexdigest()
    manifest = {
        "engine_version": version,
        "source_repo": SOURCE_REPO,
        "bundle": BUNDLE_NAME,
        "sha256": sha,
        "block_count": len(ordered),
        "blocks": [
            {"name": name, "file": fname, "bytes": len(body.encode("utf-8"))}
            for fname, name, body in ordered
        ],
    }

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, BUNDLE_NAME), "wb") as f:
        f.write(bundle_bytes)
    with open(os.path.join(args.out, MANIFEST_NAME), "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    per_file = {}
    for fname, _name, _body in ordered:
        per_file[fname] = per_file.get(fname, 0) + 1
    print("build-engine-artifact: OK — %s (%s)" % (version,
          ", ".join("%d blocks from %s" % (per_file[f], f) for f in ENGINE_FILES)))
    print("  %s  (%d bytes)" % (os.path.join(args.out, BUNDLE_NAME), len(bundle_bytes)))
    print("  %s" % os.path.join(args.out, MANIFEST_NAME))
    print("sha256: %s" % sha)


if __name__ == "__main__":
    main()

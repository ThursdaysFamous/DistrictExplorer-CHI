#!/usr/bin/env bash
# Regenerates www/, the Capacitor webDir, from the repo's real source files.
# Capacitor 8+ refuses to use the repo root itself as webDir, so this copy
# step exists purely to satisfy that constraint -- index.html stays the one
# source of truth; www/ is disposable and gitignored, run this before every
# `npx cap sync` (see docs/MOBILE_APP_RUNBOOK.md).
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf www
mkdir -p www
cp index.html manifest.webmanifest sw.js www/
cp -r icons www/icons

#!/usr/bin/env bash
# Vendor Leaflet locally for the headless smoke test.
#
# Why this exists: index.html loads Leaflet from cdnjs.cloudflare.com. In the
# Claude Code web/sandbox environment the browser (Playwright's Chromium) cannot
# reach that CDN — it does not use the agent HTTPS proxy, so every request resets
# (ERR_CONNECTION_RESET → "L is not defined" → the app never boots). curl *can*
# reach the CDN through the proxy, so we fetch Leaflet here and let
# scripts/smoke_test.mjs serve it same-origin via page.route(). Production and
# GitHub Actions CI are unaffected: they hit the real CDN and never see this dir
# (it is gitignored and absent unless this script has run).
#
# Best-effort: never fails the caller. If the CDN is unreachable the smoke test
# just falls back to loading Leaflet from the CDN as it always has.
set -u

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
index="$repo_root/index.html"
out="$repo_root/scripts/vendor/leaflet"

# Mirror the exact URLs the app requests, so the vendored copy can never drift
# from index.html's pinned Leaflet version.
mapfile -t urls < <(grep -oE 'https://cdnjs\.cloudflare\.com/[^"]*leaflet\.(js|css)' "$index" | sort -u)
if [ "${#urls[@]}" -eq 0 ]; then
  echo "vendor_leaflet: no Leaflet CDN URL found in index.html; skipping." >&2
  exit 0
fi

mkdir -p "$out"
for url in "${urls[@]}"; do
  name="${url##*/}"   # leaflet.js / leaflet.css
  if curl -fsS --max-time 30 -o "$out/$name" "$url"; then
    echo "vendor_leaflet: fetched $name ($(wc -c <"$out/$name") bytes)"
  else
    echo "vendor_leaflet: could not fetch $url — smoke test will fall back to CDN." >&2
    rm -f "$out/$name"
  fi
done

exit 0

#!/usr/bin/env python3
"""Build districtry-app.html — the Stage B unlisted Districtry re-skin preview.

Reads index.html, applies an ordered substitution table, writes
districtry-app.html at the repo root (a ROOT-LEVEL sibling on purpose: every
relative fetch — data/app/*.json, fonts/, icons/, ./sources.html — resolves
identically to index.html, so the diff between the two files is ONLY the
re-skin). The script NEVER writes index.html.

Every transform must match EXACTLY ONCE or the build fails loudly, naming the
pattern — upstream drift breaks this script, never silently ships a
half-skinned preview. Refresh after index.html moves:

    python3 scripts/build_districtry_preview.py && git add districtry-app.html

--check regenerates (reusing the committed file's generation stamp so the
comparison is byte-stable) and diffs against the committed copy. It is NOT
wired into CI — the preview is allowed to go stale; this just makes staleness
detectable on demand.

Scope (docs/DISTRICTRY_REBRAND.md): a pure re-skin. Every existing behavior
rides along by construction — pin-as-parent, copy-link, offices accordions,
the CARTO basemap, permalinks. Dark mode is deliberately NOT added (deferred
pending its own approval). The engine-fenced "METRO_NAME + ' District
Explorer'" strings still show the old name in dialogs — that is the Phase 3
engine release, accepted here. The skin lands as an appended override island
(the blessed outside-the-fence pattern, docs/ENGINE_SYNC.md) — no ENGINE or
GENERATED interior is edited, so this table doubles as the adoption
checklist.

Do NOT run validate_index.py against the output — it validates
worksheet-coupled invariants against whatever file it is handed and the
preview intentionally diverges (no manifest link, no SW registration).
"""

import io
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO_ROOT, "index.html")
OUT = os.path.join(REPO_ROOT, "districtry-app.html")
FAQ_OUT = os.path.join(REPO_ROOT, "districtry-faq.html")

STAMP_RE = re.compile(r'<span class="preview-stamp">([^<]*)</span>')

# The 5c mark, light variant (multiply blends), sized by the skin island.
# Inserted AFTER the hidden .masthead-star svg — never in its place:
# index.html's boot script writes #star-path-header by id and would throw on a
# missing element.
MARK_SVG = (
    '<svg class="districtry-mark" viewBox="0 0 96 96" aria-hidden="true">'
    '<g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.55"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.5"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.45"></polygon></g>'
    '<circle cx="42" cy="60" r="17" fill="none" stroke="#17161c" stroke-width="11"></circle>'
    '<line x1="59" y1="16" x2="59" y2="82.5" stroke="#17161c" stroke-width="11"></line>'
    "</svg>"
)

# The 5c mark as a quiet outline, for the empty state where the Chicago flag
# star used to sit. Same construction as MARK_SVG, drawn in the chrome inks
# rather than at full saturation so it reads as a placeholder, not a logo.
EMPTY_MARK_SVG = (
    '<svg class="districtry-empty-mark" viewBox="0 0 96 96" aria-hidden="true">'
    '<g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.20"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.18"></polygon></g>'
    '<g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.16"></polygon></g>'
    '<circle cx="42" cy="60" r="17" fill="none" stroke="#9aa3b2" stroke-width="9"></circle>'
    '<line x1="59" y1="16" x2="59" y2="82.5" stroke="#9aa3b2" stroke-width="9"></line>'
    "</svg>"
)

# Barlow rides Google Fonts here as a PREVIEW-ONLY shortcut (no committed font
# binaries before the direction is approved). Production adoption self-hosts:
# edit build_fonts.py's GFONTS_URL to the Barlow families, re-run, re-paste
# the emitted @font-face block — its documented workflow.
FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600'
    "&family=Barlow:wght@400;500;600;700&display=swap\" rel=\"stylesheet\">\n"
)

# The skin: token re-points + the handful of chrome literals the tokens can't
# reach. Three-tier discipline — violet is chrome, the data tier keeps its
# blue (--card-accent/#1d5fd6 and every map layer color are untouched).
# Warm-accent mapping (#b0316e magenta, derived deep #8f2659) and the
# resulting magenta focus ring are explicit REVIEW ITEMS.
SKIN_ISLAND = """<style id="districtry-skin">
  /* ==== Districtry re-skin island (Stage B preview) ====
     Appended AFTER the engine styles so same-specificity rules win the
     cascade — no fence interior edited. At adoption this island is the
     fork-local restyle; see docs/DISTRICTRY_REBRAND.md. */
  :root {
    --accent: #6d3fd1;        /* brand-600 — chrome only, never map data */
    --accent-deep: #5730ab;   /* brand-700 — text/links on light */
    /* The warm accent is NOT decoration: the engine paints the Public Safety
       group dot with it (index.html .group-safety .dot), beside Political
       (--accent), Schools (#E8A324) and Geography (#5C8F6B). Setting it to
       violet — the "one hue for both slots" idea — would make two of the four
       group dots identical, so a distinct hue is required, not preferred. It
       is also the focus ring, where contrast AGAINST violet controls is the
       point. #b0316e is the mark's own third polygon, so the hue is on-brand
       without borrowing from the data tier (police/fire reds are map colors). */
    --accent-warm: #b0316e;   /* mark magenta — group dot + focus ring */
    --accent-warm-deep: #8f2659; /* derived; unreferenced by the engine today,
       overridden anyway so no Chicago flag red survives in the cascade */
    --ink: #17161c;
    --slate: #4b5563;
    --slate-soft: #9aa3b2;
    --paper: #f4f2ee;
    --panel: #ffffff;
    --line: #e8e7ef;
    --line-strong: #c9c5d4;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body: 'Barlow', 'Inter Fallback', -apple-system, BlinkMacSystemFont, sans-serif;
    /* --font-mono unchanged: IBM Plex Mono stays self-hosted */
  }
  /* card chrome only — --card-accent/--card-link ARE the data tier, kept */
  .layer-block {
    --card-border: #e8e7ef;
    --card-row-border: #f1f0f6;
    --card-sep: #c9c5d4;
    --card-section-bg: #f8f7fc;
  }
  /* the Chicago flag-stripe motif is that fork's signature device — recolored
     by the token swap it reads as meaningless violet bands, and the Districtry
     design carries no stripe, so the preview hides it */
  .flag-stripe { display: none; }
  /* ==== empty state: the Chicago flag star retires ====
     The six-pointed star is that city's emblem; recoloured violet it was
     simply an off-brand Chicago motif sitting in a Districtry app. The path
     element STAYS in the DOM (hidden) because the boot script writes its `d`
     by id and would throw on a missing node — the same discipline as the
     masthead star — and the 5c mark is drawn beside it. */
  .empty-state .star-outline { display: none; }
  .empty-state .districtry-empty-mark { width: 76px; height: 76px; margin: 0 auto 4px; display: block; opacity: 0.9; }
  /* masthead goes light (the approved app-shell direction) */
  header.masthead { background: var(--panel); color: var(--ink); border-bottom: 1px solid var(--line); }
  .masthead-star { display: none; }
  .districtry-mark { width: 38px; height: 38px; flex: none; }
  .title-text { font-weight: 600; text-transform: lowercase; letter-spacing: 0.005em; }
  .title-metro { color: var(--slate-soft); font-weight: 400; }
  h1.title small { color: var(--slate); }
  .preview-stamp { display: block; margin-top: 4px; font-size: 11px; color: var(--slate-soft); }
  .masthead-actions .footer-link-btn {
    color: var(--accent-deep);
    background: rgba(109, 63, 209, 0.08);
    border-color: rgba(109, 63, 209, 0.35);
  }
  .masthead-actions .footer-link-btn:hover,
  .masthead-actions .footer-link-btn:focus-visible {
    color: var(--accent-deep);
    background: rgba(109, 63, 209, 0.16);
    border-color: var(--accent);
  }
  .masthead-action-link { color: var(--slate); background: rgba(23, 22, 28, 0.03); border-color: var(--line); }
  .masthead-action-link:hover,
  .masthead-action-link:focus-visible { color: var(--ink); background: rgba(23, 22, 28, 0.06); border-color: var(--line-strong); }
  /* chrome tints the engine hardcodes as Chicago-flag rgba()s */
  .selected-point-chip .copy-link-btn:hover { background: rgba(109, 63, 209, 0.12); }
  .footer-disclaimer { background: rgba(176, 49, 110, 0.14); }
  .footer-sources a:hover,
  .footer-metros a:hover { background: rgba(109, 63, 209, 0.2); }
  /* ==== footer elimination (operator-directed, 2026-08-20) ====
     The redesign gives the map the left and bottom viewport bounds: no
     document footer, no in-page FAQ (it moves to districtry-faq.html).
     Both sections are HIDDEN, never removed — the boot script fills
     #verified-date and binds #feedback-btn / #footer-metros by id, so the
     load-bearing elements are RELOCATED into the results-panel foot by the
     transforms and only the husks stay hidden here. */
  .faq-section, footer.site-footer { display: none; }
  @media (min-width: 901px) {
    html, body { height: 100%; }
    body { display: flex; flex-direction: column; }
    header.masthead { flex: none; }
    main.layout { flex: 1 1 auto; min-height: 0; max-width: none; margin: 0; width: 100%; }
    .map-col { height: 100%; min-height: 0; }
    #map { height: 100%; min-height: 0; }
    .results-col { max-height: none; height: 100%; }
  }
  /* the panel foot — the footer's surviving content, per the app-shell canvas
     (disclaimer as a small line at the panel's bottom edge).
     :not([hidden]) is LOAD-BEARING, not decoration: a bare `.results-col
     { display: flex }` outranks the UA's `[hidden] { display: none }`, so
     the Layers button set the hidden attribute and the panel stayed put
     while the grid collapsed to one column — the map appeared to close
     instead of the panel. */
  .results-col:not([hidden]) { display: flex; flex-direction: column; }
  .results-col > * { flex: none; }
  .districtry-panel-foot {
    margin-top: auto;
    padding: 10px 2px 0;
    border-top: 1px solid var(--line);
    font-size: 11px;
    line-height: 1.5;
    color: var(--slate-soft);
  }
  .districtry-panel-foot p { margin: 0 0 6px; }
  .districtry-panel-foot .footer-meta { font-size: 11px; color: var(--slate-soft); margin: 0 0 6px; }
  .dpf-links { display: flex; flex-wrap: wrap; gap: 2px 12px; margin: 0 0 8px; }
  .dpf-links a { color: var(--accent-deep); text-decoration: none; }
  .dpf-links a:hover { text-decoration: underline; }
  .districtry-panel-foot .footer-link-btn {
    font-size: 11.5px;
    padding: 4px 10px;
    margin: 0 0 6px;
    color: var(--accent-deep);
    background: transparent;
    border: 1px solid rgba(109, 63, 209, 0.35);
    border-radius: 7px;
    cursor: pointer;
  }
  .districtry-panel-foot .footer-link-btn:hover { background: rgba(109, 63, 209, 0.08); }
  .districtry-panel-foot .footer-metros { font-size: 11px; }
  .districtry-panel-foot .footer-metros a { color: var(--accent-deep); }
  /* ==== canvas app-shell layout (operator-directed: "Implement Districtry
     App.dc.html", 2026-08-20) ==== */
  /* search moves from floating-over-map into the masthead. The shell's own
     surface (panel fill + drop shadow) was drawn to float over a basemap; in
     a header it reads as a grey box around the field, so the shell goes
     invisible and the INPUT carries the affordance. */
  .masthead .map-toolbar { position: static; transform: none; flex: 1 1 320px; max-width: 560px; }
  .masthead .search-shell { position: relative; box-shadow: none; background: transparent; border-color: transparent; padding: 0; }
  .masthead .search-row input[type="text"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
  }
  .masthead .search-row input[type="text"]:focus-visible {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(109, 63, 209, 0.14);
  }
  .masthead .search-row input[type="text"]::placeholder { color: var(--slate-soft); }
  .masthead .search-row button { background: var(--accent); border-radius: 8px; }
  .masthead .search-row button:hover { background: var(--accent-deep); }
  .masthead .search-extra {
    position: absolute;
    top: calc(100% + 6px);
    left: -1px;
    right: -1px;
    background: var(--panel);
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    box-shadow: 0 8px 24px rgba(23, 22, 28, 0.14);
    padding: 8px;
    z-index: 900;
  }
  .masthead .search-shell:not(:hover):not(:focus-within):not(.expanded) .search-extra { padding: 0; border-width: 0; }
  /* The four "about the data" doors (operator-directed, two rounds): emoji
     dropped, and the row is no longer a bordered segmented box — that put a
     second hard rectangle beside the search field and gave four secondary
     links a toolbar's weight.

     The pill is the shape of an action here. "What data is missing?" wears
     one permanently and inverts to a solid fill on hover, because the repo's
     own note records that this button was promoted into the masthead as the
     standing caveat on every answer the app gives; its three peers are bare
     text that earn the same pill shape on approach. Hierarchy that matches
     the stated priority instead of flattening it. */
  .masthead-actions {
    border: none;
    background: none;
    overflow: visible;
    gap: 6px;
    align-items: center;
  }
  .masthead-action-link {
    border: 1px solid transparent;
    background: transparent;
    color: var(--slate);
    font-weight: 500;
    font-size: 12.5px;
    padding: 7px 13px;
    border-radius: 999px;
    letter-spacing: 0;
    transform: none;
    transition: background .15s ease, color .15s ease;
  }
  .masthead-action-link:hover,
  .masthead-action-link:focus-visible {
    background: rgba(109, 63, 209, 0.10);
    color: var(--accent-deep);
    border-color: transparent;
    text-decoration: none;
    transform: none;
  }
  .masthead-actions .footer-link-btn {
    border: 1px solid rgba(109, 63, 209, 0.30);
    background: rgba(109, 63, 209, 0.07);
    color: var(--accent-deep);
    font-weight: 600;
    font-size: 12.5px;
    padding: 7px 14px;
    border-radius: 999px;
    margin-right: 6px;
    letter-spacing: 0;
    transform: none;
    transition: background .15s ease, color .15s ease, border-color .15s ease;
  }
  .masthead-actions .footer-link-btn:hover,
  .masthead-actions .footer-link-btn:focus-visible {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
    text-decoration: none;
    transform: none;
  }
  /* panel header bar: coords + Share on the left, the counts flush right —
     across from the Share button, at the page's own right edge. */
  .districtry-panel-head {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0 12px;
    margin: 0 0 12px;
    border-bottom: 1px solid var(--line);
    min-height: 30px;
  }
  .districtry-stats {
    margin-left: auto;
    font-size: 12px;
    color: var(--slate-soft);
    white-space: nowrap;
  }
  /* the selected-point chip becomes the results panel's header row (keep
     position:relative — it anchors the engine's share popover) */
  .districtry-panel-head .selected-point-chip {
    background: var(--panel);
    color: var(--ink);
    box-shadow: none;
    border-radius: 0;
    padding: 0;
    margin: 0;
  }
  .districtry-panel-head .selected-point-chip .copy-link-btn { color: var(--accent-deep); border-color: rgba(109, 63, 209, 0.35); }
  /* The share popover opens UPWARD off the chip because the chip used to sit
     at the map's bottom-left. Anchored at the panel's TOP that put the card
     above the viewport — open, unreachable, invisible. In the panel it opens
     downward and is clamped to the panel's width. */
  .districtry-panel-head .selected-point-chip .share-popover {
    top: calc(100% + 8px);
    bottom: auto;
    left: 0;
    right: 0;
    width: auto;
    max-width: none;
  }
  /* three-zone coverage treatment */
  .dst-glow { filter: blur(7px); }
  /* ==== map legend (operator-directed rebuild, 2026-08-20) ====
     Was a flat wrapping run of LOOSE swatches and labels, so a wrap could
     fall between a swatch and the label it defines — the blue dot ended one
     line and "Selected point" began the next. Each row is now a grid whose
     swatch and label cannot be separated, and the rows are stacked, so the
     defect is gone by construction rather than by picking a lucky width. */
  .districtry-map-legend {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 1px 3px rgba(23, 22, 28, 0.06);
    font-size: 11.5px;
    color: var(--slate);
  }
  .districtry-map-legend .dml-kicker {
    font-family: var(--font-display);
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--faint);
    margin-bottom: 1px;
  }
  /* swatch and label ride one grid row — a wrap can never split the pair */
  .districtry-map-legend .dml-item {
    display: grid;
    grid-template-columns: 10px auto;
    align-items: center;
    /* row-gap 2px, not 8: a shorthand gap would space the why-line as far from
       the label it belongs to as from the next legend row, leaving it
       visually orphaned between the two. */
    gap: 2px 8px;
  }
  .districtry-map-legend .dml-label { white-space: nowrap; }
  /* the "why" line under the partial-coverage swatch: the wash does NOT mean
     the county is empty — statewide layers answer there. It means this county's
     own districts are not sourced yet, which is the honest distinction. */
  .districtry-map-legend .dml-sub {
    grid-column: 2;
    margin-bottom: 3px;
    font-size: 10.5px;
    line-height: 1.35;
    color: var(--faint);
    max-width: 25ch;
    white-space: normal;
  }
  .districtry-map-legend .dml-rule { width: 100%; height: 1px; background: var(--line); margin: 3px 0 2px; }
  .districtry-map-legend .dml-glow { width: 9px; height: 9px; border-radius: 50%; flex: none; box-shadow: 0 0 5px 2.5px #ad8cee; }
  .districtry-map-legend .dml-sw { width: 9px; height: 9px; border-radius: 2px; flex: none; }
  .districtry-map-legend .dml-pending { background: #8a62e0; opacity: 0.25; }
  .districtry-map-legend .dml-out { background: #8d8a97; opacity: 0.55; }
  .districtry-map-legend .dml-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; background: #1d5fd6; }
</style>
"""

# The canvas's three-zone coverage treatment, replacing the engine's single
# out-of-coverage wash AT ITS FORK-LOCAL CALL SITE (the whenIdle line is fork
# code; the scope-mask ENGINE fence is untouched). Contract preserved:
# coverageMaskRings is still set from coverageOutlineRings(feats), so the
# engine's point-in-coverage test keeps working. Decorative like the original:
# every failure path skips silently. Values are the canvas's (Districtry
# App.dc.html initMap): gray outside Illinois, violet "data coming" wash on
# in-state unserved ground, glow + hairline on the state border.
COVERAGE_JS = """  function drawDistrictryCoverage() {
    var stateUrl = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/0/query?where=" +
      encodeURIComponent("STUSAB='IL'") + "&outFields=NAME&returnGeometry=true&geometryPrecision=3&outSR=4326&f=geojson";
    var covP = loadMetroOutline().catch(function () { return null; });
    // decorative: fail fast (one retry, short timeout) so an unreachable
    // TIGERweb degrades to the single-wash fallback quickly
    var stP = fetchJSONWithRetry(stateUrl, { timeoutMs: 6000 }, 1).catch(function () { return null; });
    Promise.all([covP, stP]).then(function (res) {
      var covGeo = res[0], stGeo = res[1];
      var covFeats = (covGeo && covGeo.features) || [];
      if (!covFeats.length) return;
      var outline = coverageOutlineRings(covFeats);
      if (!outline || !outline.length) {
        outline = [];
        for (var i = 0; i < covFeats.length; i++) {
          var geom = covFeats[i].geometry;
          if (!geom) continue;
          var polys = geom.type === "Polygon" ? [geom.coordinates]
                    : geom.type === "MultiPolygon" ? geom.coordinates : [];
          for (var p = 0; p < polys.length; p++) {
            for (var r = 0; r < polys[p].length; r++) outline.push(polys[p][r]);
          }
        }
      }
      coverageMaskRings = outline;
      var covLatLng = [];
      for (var j = 0; j < outline.length; j++) {
        var src = outline[j], ring = [];
        for (var v = 0; v < src.length; v++) ring.push([src[v][1], src[v][0]]);
        covLatLng.push(ring);
      }
      var world = [[-89, -720], [89, -720], [89, 720], [-89, 720]];
      var stateRing = null;
      if (stGeo && stGeo.features && stGeo.features[0] && stGeo.features[0].geometry) {
        var g = stGeo.features[0].geometry;
        var raw = null;
        if (g.type === "Polygon") raw = g.coordinates[0];
        else if (g.type === "MultiPolygon") {
          for (var m = 0; m < g.coordinates.length; m++) {
            if (!raw || g.coordinates[m][0].length > raw.length) raw = g.coordinates[m][0];
          }
        }
        if (raw && raw.length > 3) {
          stateRing = [];
          for (var s = 0; s < raw.length; s++) stateRing.push([raw[s][1], raw[s][0]]);
        }
      }
      if (stateRing) {
        L.polygon([world, stateRing], { pane: "scope-mask", stroke: false, fillColor: "#8d8a97", fillOpacity: 0.42, interactive: false }).addTo(map);
        L.polygon([stateRing].concat(covLatLng), { pane: "scope-mask", stroke: false, fillColor: "#8a62e0", fillOpacity: 0.08, interactive: false }).addTo(map);
        var closed = stateRing.concat([stateRing[0]]);
        L.polyline(closed, { pane: "scope-mask", className: "dst-glow", color: "#ad8cee", weight: 9, opacity: 0.6, interactive: false }).addTo(map);
        L.polyline(closed, { pane: "scope-mask", color: "#ad8cee", weight: 1.5, opacity: 0.9, interactive: false }).addTo(map);
      } else {
        L.polygon([world].concat(covLatLng), { pane: "scope-mask", stroke: false, fillColor: "#8d8a97", fillOpacity: 0.35, interactive: false }).addTo(map);
      }
      var host = document.querySelector(".map-bottom-left");
      if (host && !document.querySelector(".districtry-map-legend")) {
        var legend = document.createElement("div");
        legend.className = "districtry-map-legend";
        legend.innerHTML = '<span class="dml-kicker">Coverage</span>' +
          '<span class="dml-item"><span class="dml-glow"></span>' +
            '<span class="dml-label">IL</span></span>' +
          '<span class="dml-item"><span class="dml-sw dml-pending"></span>' +
            '<span class="dml-label">Statewide layers only</span>' +
            '<span class="dml-sub">County board and local districts not sourced yet</span></span>' +
          '<span class="dml-item"><span class="dml-sw dml-out"></span>' +
            '<span class="dml-label">Outside IL</span></span>' +
          '<span class="dml-rule"></span>' +
          '<span class="dml-item"><span class="dml-dot"></span>' +
            '<span class="dml-label">Selected point</span></span>';
        host.insertBefore(legend, host.firstChild);
      }
    }).catch(function () { /* decorative — skip the wash, never surface an error */ });
  }
  // still off the boot critical path, but with an idle TIMEOUT — plain
  // requestIdleCallback can be starved indefinitely while tiles and layer
  // fetches keep the loop busy, and a coverage wash that may never draw is
  // worse than one that costs a frame
  if (window.requestIdleCallback) {
    window.requestIdleCallback(drawDistrictryCoverage, { timeout: 4000 });
  } else {
    setTimeout(drawDistrictryCoverage, 800);
  }
"""

# The FAQ's new standalone home. The extracted .faq-section markup is spliced
# in verbatim so the two copies (hidden husk in the app page, live page here)
# can never say different things within one generation.
FAQ_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>districtry / il — common questions (unlisted preview)</title>
<link rel="icon" type="image/svg+xml" href="districtry/icons/favicon.svg">
<link rel="stylesheet" href="districtry/tokens/districtry.tokens.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body { margin: 0; background: var(--paper); color: var(--ink); font: 400 15px/1.6 var(--font-body); }
  .wrap { max-width: 760px; margin: 0 auto; padding: 32px 24px 64px; }
  .mast { display: flex; align-items: baseline; gap: 8px; padding-bottom: 18px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
  .mast .wordmark { font: var(--font-heading-weight) 28px/1 var(--font-heading); letter-spacing: .005em; color: var(--ink); text-decoration: none; }
  .mast .tag { font: 400 22px/1 var(--font-heading); color: var(--faint); }
  .back { font-size: 13px; }
  .back a { color: var(--brand); text-decoration: none; }
  .faq-section h2 { font: var(--font-heading-weight) 26px/1.2 var(--font-heading); margin: 22px 0 10px; }
  .faq-section details { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-card); box-shadow: var(--shadow-card); margin: 0 0 10px; padding: 0 16px; }
  .faq-section summary { cursor: pointer; font-weight: 600; padding: 12px 0; list-style-position: inside; }
  .faq-section p { margin: 0 0 14px; color: var(--ink-3); }
  footer { margin-top: 28px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 11.5px; color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <div class="mast">
    <a class="wordmark" href="districtry-app.html">districtry</a>
    <span class="tag">/ il</span>
    <span class="tag">/ faq</span>
  </div>
  <p class="back"><a href="districtry-app.html">← Back to the map</a></p>
  __FAQ_SECTION__
  <footer>Unlisted re-skin preview. <strong>Not for legal or official use.</strong> Boundary and roster
  data come from public sources that disclaim legal precision. __STAMP__</footer>
</div>
</body>
</html>
"""


# Geocoder labels carry the state in full; the preview abbreviates to the USPS
# code. Unknown values pass through unchanged — a geocoder that answers with
# something unexpected should print what it said, not swallow it.
STATE_CODE_JS = """  var US_STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "Puerto Rico": "PR"
  };
  function stateCode(name) {
    if (!name) return name;
    return US_STATE_CODES[name] || name;
  }
"""


def sub_once(html, pattern, replacement, label, regex=False):
    if regex:
        matches = pattern.findall(html)
        n = len(matches)
    else:
        n = html.count(pattern)
    if n != 1:
        sys.exit(
            "build-districtry-preview: FAIL — pattern for %r matched %d times "
            "(need exactly 1). index.html has drifted past this transform; fix "
            "the table before regenerating." % (label, n)
        )
    if regex:
        return pattern.sub(replacement.replace("\\", "\\\\"), html, count=1)
    return html.replace(pattern, replacement, 1)


def build(stamp_text):
    html = io.open(SRC, encoding="utf-8").read()

    # -- strip analytics: GA is hostname-gated and the gate would PASS on the
    #    preview URL; GoatCounter is ungated and would count preview visits.
    html = sub_once(
        html,
        re.compile(r"<!-- Google tag \(gtag\.js\).*?</script>\n", re.S),
        "<!-- analytics stripped: unlisted preview -->\n",
        "GA block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<script data-goatcounter="[^"]*"\s*\n\s*async src="//gc\.zgo\.at/count\.js"></script>\n', re.S),
        "",
        "GoatCounter",
        regex=True,
    )

    # -- retitle + unlist. Canonical/OG/twitter/JSON-LD are stripped outright:
    #    a noindexed preview must not declare a canonical at the live site,
    #    and a leaked URL should unfurl as nothing.
    html = sub_once(
        html,
        re.compile(r"<title>[^<]*</title>"),
        "<title>districtry / il — working preview (unlisted)</title>",
        "title",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<meta name="description" content="[^"]*" />', re.S),
        '<meta name="description" content="Unlisted working preview of the Districtry re-skin. '
        'The live product is chidistricts.com." />',
        "meta description",
        regex=True,
    )
    html = sub_once(
        html,
        '<meta name="robots" content="index, follow" />',
        '<meta name="robots" content="noindex, nofollow" />',
        "robots",
    )
    html = sub_once(
        html,
        '<link rel="canonical" href="https://chidistricts.com/" />\n',
        "",
        "canonical",
    )
    html = sub_once(
        html,
        re.compile(r"<!-- Open Graph / social share previews.*?og:locale\" content=\"en_US\" />\n", re.S),
        "",
        "OG block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r'<!-- Twitter / X card -->.*?twitter:image" content="[^"]*" />\n', re.S),
        "",
        "twitter block",
        regex=True,
    )
    html = sub_once(
        html,
        re.compile(r"<!-- Structured data: help search engines understand what this tool is -->.*?FAQPage.*?</script>\n", re.S),
        "",
        "JSON-LD blocks",
        regex=True,
    )

    # -- no manifest (a preview must not be installable), new theme color,
    #    real favicon file from the Stage A asset dir.
    html = sub_once(html, '<link rel="manifest" href="manifest.webmanifest">\n', "", "manifest link")
    html = sub_once(
        html,
        '<meta name="theme-color" content="#0b3d91">',
        '<meta name="theme-color" content="#6d3fd1">',
        "theme-color",
    )
    html = sub_once(
        html,
        re.compile(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml,[^"]*" />', re.S),
        '<link rel="icon" type="image/svg+xml" href="districtry/icons/favicon.svg" />',
        "favicon",
        regex=True,
    )

    # -- fonts: swap the self-hosted Big Shoulders/Inter faces for a Google
    #    Fonts Barlow link, KEEPING the IBM Plex Mono faces (the tokens define
    #    no mono replacement and the app's mono is load-bearing).
    fonts_block_re = re.compile(
        r"/\* ==== SELF-HOSTED FONTS:BEGIN.*?SELF-HOSTED FONTS:END ==== \*/", re.S
    )
    blocks = fonts_block_re.findall(html)
    if len(blocks) != 1:
        sys.exit("build-districtry-preview: FAIL — SELF-HOSTED FONTS block matched %d times" % len(blocks))
    mono_faces = [
        face
        for face in re.findall(r"@font-face \{.*?\}", blocks[0], re.S)
        if "IBM Plex Mono" in face
    ]
    if len(mono_faces) != 4:
        sys.exit(
            "build-districtry-preview: FAIL — expected 4 IBM Plex Mono @font-face rules, found %d"
            % len(mono_faces)
        )
    html = fonts_block_re.sub(
        lambda _m: "/* Districtry preview: Barlow via Google Fonts <link> in <head>; mono kept self-hosted */\n"
        + "\n".join(mono_faces),
        html,
        count=1,
    )
    html = sub_once(html, "\n<style>\n", "\n" + FONT_LINKS + "<style>\n", "font links before <style>")

    # -- masthead: hide (never remove) the Chicago star, add the 5c mark,
    #    swap the wordmark, stamp the generation provenance into the subtitle.
    html = sub_once(
        html,
        '<path fill="var(--accent-warm)" id="star-path-header"></path>\n        </svg>',
        '<path fill="var(--accent-warm)" id="star-path-header"></path>\n        </svg>\n        ' + MARK_SVG,
        "mark insert",
    )
    html = sub_once(
        html,
        '<span class="title-text">Chicago District Explorer</span>',
        '<span class="title-text">districtry <span class="title-metro">/ il</span></span>',
        "wordmark",
    )
    html = sub_once(
        html,
        "<small>Click the map or search an address to see every district that covers it, and who represents it.</small>",
        "<small>Click the map or search an address to see every district that covers it, and who represents it."
        '<span class="preview-stamp">' + stamp_text + "</span></small>",
        "generation stamp",
    )

    # -- a preview page must be inert: no service-worker registration (it
    #    would install the production SW for a reviewer who only ever visits
    #    the preview).
    html = sub_once(
        html,
        '<script>\n  if ("serviceWorker" in navigator) {\n    navigator.serviceWorker.register("sw.js");\n  }\n</script>\n',
        "<!-- SW registration stripped: unlisted preview -->\n",
        "SW registration",
    )

    # -- footer elimination. The document footer and in-page FAQ are hidden by
    #    the skin island; their load-bearing elements are CUT from the hidden
    #    footer and relocated into a new results-panel foot, so the boot
    #    script's getElementById targets (#verified-date via #footer-meta,
    #    #feedback-btn, #footer-metros) each still exist exactly once, live.
    meta_re = re.compile(r'[ ]*<div class="footer-meta" id="footer-meta">.*?</div>\n', re.S)
    metas = meta_re.findall(html)
    if len(metas) != 1:
        sys.exit("build-districtry-preview: FAIL — #footer-meta matched %d times" % len(metas))
    footer_meta = metas[0].strip()
    html = meta_re.sub("", html, count=1)

    feedback_btn = '<button type="button" id="feedback-btn" class="footer-link-btn">💬 Report a bug or leave a comment</button>'
    html = sub_once(html, "      " + feedback_btn + "\n", "", "feedback button cut")

    metros_re = re.compile(
        r"[ ]*<!-- ==== ENGINE:BEGIN metro-links-html ==== -->\n.*?<!-- ==== ENGINE:END metro-links-html ==== -->\n",
        re.S,
    )
    metros = metros_re.findall(html)
    if len(metros) != 1:
        sys.exit("build-districtry-preview: FAIL — metro-links-html fence matched %d times" % len(metros))
    # Fences pin content, not placement — the repo's own gaps-html masthead
    # move is the precedent for relocating a fence block verbatim.
    metro_links = metros[0].strip()
    html = metros_re.sub("", html, count=1)

    panel_foot = (
        '<div class="districtry-panel-foot" id="districtry-panel-foot">\n'
        "      <p><strong>Not for legal or official use.</strong> Boundary and roster data come from public\n"
        "      sources that disclaim legal precision — confirm with the relevant government office before\n"
        "      relying on them for anything official.</p>\n"
        "      " + footer_meta + "\n"
        # No Sources link here: the masthead pill already carries that door,
        # and the OSM attribution below is a licence obligation, not a repeat.
        '      <div class="dpf-links">\n'
        '        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">Geocoding © OpenStreetMap contributors</a>\n'
        '        <a href="https://github.com/ThursdaysFamous/DistrictExplorer-CHI" target="_blank" rel="noopener">GitHub</a>\n'
        '        <a href="https://github.com/sponsors/ThursdaysFamous" target="_blank" rel="noopener">💛 Support this project</a>\n'
        '        <a href="https://overberg.co" target="_blank" rel="noopener">overberg.co</a>\n'
        "      </div>\n"
        "      " + feedback_btn + "\n"
        "      " + metro_links + "\n"
        "    </div>"
    )
    html = sub_once(
        html,
        '<div id="groups-root" hidden></div>\n  </section>',
        '<div id="groups-root" hidden></div>\n    ' + panel_foot + "\n  </section>",
        "panel foot insert",
    )

    # -- canvas app-shell layout ("Implement Districtry App.dc.html").
    #    (a) The search toolbar RELOCATES from floating-over-the-map into the
    #    masthead (the geocoder binds #geocode-form/#geocode-input/… by id, so
    #    the block moves verbatim, never duplicates).
    toolbar_re = re.compile(r'[ ]*<div class="map-toolbar">.*?\n    </div>\n', re.S)
    toolbars = toolbar_re.findall(html)
    if len(toolbars) != 1:
        sys.exit("build-districtry-preview: FAIL — map-toolbar matched %d times" % len(toolbars))
    toolbar = toolbars[0].strip()
    html = toolbar_re.sub("", html, count=1)
    html = sub_once(html, "</h1>", "</h1>\n    " + toolbar, "toolbar into masthead")

    #    (b) The header stat row, counts read from the repo's own generated
    #    surfaces at build time so a new county updates it on regeneration.
    county_count = "69"
    try:
        status = io.open(os.path.join(REPO_ROOT, "docs", "COUNTY_STATUS.md"), encoding="utf-8").read()
        m2 = re.search(r"\*\*(\d+) of \d+ Illinois counties are served\*\*", status)
        if m2:
            county_count = m2.group(1)
    except OSError:
        pass
    layer_count = "39"
    try:
        worksheet = json.load(io.open(os.path.join(REPO_ROOT, "metro-worksheet.json"), encoding="utf-8"))
        layer_count = str(len(worksheet.get("layers", []))) or layer_count
    except (OSError, ValueError):
        pass
    #    The FAQ joins the masthead pills (operator-directed) — it was a link
    #    buried in the panel foot, which is no place for one of the four
    #    "about the data" doors.
    html = sub_once(
        html,
        '<a class="masthead-action-link" href="https://overberg.co/why/"',
        '<a class="masthead-action-link" href="./districtry-faq.html">Common questions</a>\n'
        '      <a class="masthead-action-link" href="https://overberg.co/why/"',
        "FAQ pill",
    )

    #    (c) The selected-point chip and the stat row become the results
    #    panel's header bar: coords + Share on the left, counts flush to the
    #    page's right edge across from them. The stats live OUTSIDE the chip
    #    because the chip is hidden until a point is selected and the counts
    #    are true either way.
    chip = '<div class="selected-point-chip" id="point-chip" hidden></div>'
    html = sub_once(html, "      " + chip + "\n", "", "point chip cut")
    html = sub_once(
        html,
        '<div id="main-content" tabindex="-1"></div>',
        '<div class="districtry-panel-head">\n      '
        + chip
        + '\n      <span class="districtry-stats">'
        + county_count + " counties · " + layer_count + " layers</span>\n"
        + "    </div>\n"
        + '    <div id="main-content" tabindex="-1"></div>',
        "panel head (chip + stats)",
    )

    #    (b2) Search field: Illinois-wide prompt (the app is no longer a
    #    Chicago-only tool), and the three "about the data" pills lose their
    #    emoji. NOTE for adoption: the gaps label lives INSIDE the gaps-html
    #    ENGINE fence. Editing it is safe here only because this copy is never
    #    deploy-spliced — in production that same edit is an engine release
    #    (or the label becomes a config string).
    html = sub_once(
        html,
        'placeholder="Search a Chicago address…"',
        'placeholder="Search an Illinois address"',
        "search placeholder",
    )
    for emoji_label, plain in (
        ("🧩 What data is missing?", "What data is missing?"),
        ("📚 Sources &amp; data layers", "Sources &amp; data layers"),
        ("💡 Why this exists", "Why this exists"),
    ):
        html = sub_once(html, ">" + emoji_label + "<", ">" + plain + "<", "pill label " + plain)

    #    (b3) Geocoder results name the state in full ("…, Springfield,
    #    Illinois, 62701"). The app answers statewide and will answer in more
    #    states, so the label carries the USPS code instead. photonLabel sits
    #    outside every ENGINE fence, so this is a fork-local edit.
    html = sub_once(
        html,
        "    if (p.state) parts.push(p.state);\n",
        "    if (p.state) parts.push(stateCode(p.state));\n",
        "photon state code",
    )
    html = sub_once(
        html,
        "  function photonLabel(p) {\n",
        STATE_CODE_JS + "  function photonLabel(p) {\n",
        "state code helper",
    )

    #    (d) The three-zone coverage treatment replaces the engine wash at its
    #    fork-local call site (the scope-mask ENGINE fence itself is untouched;
    #    coverageMaskRings stays set — see COVERAGE_JS).
    html = sub_once(
        html,
        "  whenIdle(function () { drawOutOfScopeMask(loadMetroOutline); });\n",
        COVERAGE_JS,
        "three-zone coverage",
    )

    # -- the FAQ moves to its own page; the in-page section stays as a hidden
    #    husk (CSS) and its markup is extracted verbatim for the new page.
    faq_re = re.compile(r'<section class="faq-section" aria-labelledby="faq-heading">.*?</section>', re.S)
    faqs = faq_re.findall(html)
    if len(faqs) != 1:
        sys.exit("build-districtry-preview: FAIL — faq-section matched %d times" % len(faqs))
    faq_html = FAQ_PAGE_TEMPLATE.replace("__FAQ_SECTION__", faqs[0]).replace("__STAMP__", stamp_text)

    # -- empty state: the Chicago star stays in the DOM (JS writes its `d`)
    #    but is hidden by the skin; the districtry mark is drawn beside it.
    html = sub_once(
        html,
        '<path fill="none" stroke="var(--accent-deep)" stroke-width="4" id="star-path-empty"></path>\n      </svg>',
        '<path fill="none" stroke="var(--accent-deep)" stroke-width="4" id="star-path-empty"></path>\n      </svg>\n      '
        + EMPTY_MARK_SVG,
        "empty-state mark",
    )

    # -- selection marker: the six-pointed Chicago star becomes the canvas's
    #    own answer — a data-tier circle with a white ring. One transform now
    #    owns shape AND colour; the earlier fill-only swap was removed so the
    #    two cannot disagree about what the marker is.
    html = sub_once(
        html,
        '\'<path d="\' + starPath(50, 50, 46, 19) + \'" fill="#C8102E" stroke="#ffffff" stroke-width="4"/>\' +',
        '\'<circle cx="50" cy="50" r="17" fill="#1d5fd6" stroke="#ffffff" stroke-width="6"/>\' +',
        "selection marker",
    )

    # -- the skin island, last in <head> so it wins the cascade.
    html = sub_once(html, "</head>", SKIN_ISLAND + "</head>", "skin island")

    return html, faq_html


def main():
    check = "--check" in sys.argv[1:]
    if check:
        if not os.path.exists(OUT) or not os.path.exists(FAQ_OUT):
            sys.exit("build-districtry-preview: FAIL — --check but a committed output is missing")
        committed = io.open(OUT, encoding="utf-8").read()
        committed_faq = io.open(FAQ_OUT, encoding="utf-8").read()
        m = STAMP_RE.search(committed)
        if not m:
            sys.exit("build-districtry-preview: FAIL — committed preview has no generation stamp")
        regenerated, regenerated_faq = build(m.group(1))
        if regenerated != committed or regenerated_faq != committed_faq:
            sys.exit(
                "build-districtry-preview: STALE — regenerating from the current index.html "
                "differs from the committed districtry-app.html/districtry-faq.html. "
                "Re-run without --check and commit."
            )
        print("build-districtry-preview: OK — committed preview + FAQ page match a fresh build")
        return

    sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    date = subprocess.check_output(["date", "-u", "+%Y-%m-%d"], text=True).strip()
    stamp = "districtry re-skin preview (unlisted) — generated from index.html @ %s on %s" % (sha, date)
    html, faq_html = build(stamp)
    io.open(OUT, "w", encoding="utf-8").write(html)
    io.open(FAQ_OUT, "w", encoding="utf-8").write(faq_html)
    print(
        "build-districtry-preview: OK — wrote %s (%d bytes) + %s (%d bytes, stamp: %s)"
        % (
            os.path.relpath(OUT, REPO_ROOT),
            len(html.encode("utf-8")),
            os.path.relpath(FAQ_OUT, REPO_ROOT),
            len(faq_html.encode("utf-8")),
            stamp,
        )
    )


if __name__ == "__main__":
    main()

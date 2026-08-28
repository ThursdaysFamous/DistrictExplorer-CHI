#!/usr/bin/env node
// Renders the shared districtry OG card ("districtry/OG Card.dc.html") for
// one instance, with that instance's own state/metro label substituted in.
//
// Usage:
//   node scripts/build_og_image.mjs <instance> "<label>"
//   node scripts/build_og_image.mjs ia iowa
//   node scripts/build_og_image.mjs wi wisconsin
//
// WHY THIS EXISTS. districtry/OG Card.dc.html is the real design source —
// SVG shapes, exact colors, Barlow/Barlow Condensed type — but it hardcodes
// "illinois" as the label and there was no renderer, so every instance after
// Illinois either reused that PNG verbatim (Wisconsin: its live og-image.png
// says "illinois") or hand-approximated a new one in a raster library
// (Iowa's first pass, drawn with system fonts, not the real brand type).
// This is the renderer: same layout and assets as the .dc.html card, minus
// its Claude-Design-canvas scaffolding (<x-dc>, support.js), with the label
// as a parameter and Google Fonts swapped for the instance's own self-hosted
// woff2 files so it needs no network access — the same reason every other
// page in this fleet self-hosts its fonts.
//
// Rare operator step, not wired into CI — the same "run it, commit the
// output" posture as scripts/build_embedded_boundaries.py. Re-run it for an
// instance whenever districtry/OG Card.dc.html's design changes.

import { chromium } from "playwright";
import { writeFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

const [, , instance, label] = process.argv;
if (!instance || !label) {
  console.error('usage: node scripts/build_og_image.mjs <instance> "<label>"');
  process.exit(1);
}

const fontsDir = join(REPO_ROOT, instance, "fonts");
const fontFace = (family, weight, file) => `
@font-face {
  font-family: '${family}';
  font-style: normal;
  font-weight: ${weight};
  src: url('file://${join(fontsDir, file)}') format('woff2');
}`;

// Layout, shapes, colors and copy match districtry/OG Card.dc.html's #og-card
// div exactly (its <x-dc> canvas wrapper and data-dc-script are editor
// scaffolding, not part of the rendered card, so they're dropped here).
const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
${fontFace("Barlow Condensed", 600, "barlow-condensed-600-latin.woff2")}
${fontFace("Barlow Condensed", 400, "barlow-condensed-400-latin.woff2")}
${fontFace("Barlow", 500, "barlow-500-latin.woff2")}
${fontFace("Barlow", 400, "barlow-400-latin.woff2")}
body{margin:0}
</style></head>
<body>
<div id="og-card" style="width:1200px;height:630px;background:#f4f2ee;display:flex;align-items:center;gap:70px;padding:0 90px;box-sizing:border-box;overflow:hidden;position:relative">
  <svg width="330" height="330" viewBox="0 0 96 96" style="flex:none">
    <g style="mix-blend-mode:multiply"><polygon points="51.5,63.2 12.4,55.7 11.5,18.6 42.7,5.0 72.7,35.3" fill="#6d3fd1" fill-opacity="0.55"></polygon></g>
    <g style="mix-blend-mode:multiply"><polygon points="54.1,81.9 34.6,47.9 56.5,19.3 87.5,28.1 83.8,71.0" fill="#1d5fd6" fill-opacity="0.5"></polygon></g>
    <g style="mix-blend-mode:multiply"><polygon points="13.7,64.5 27.6,31.2 62.7,37.6 70.3,66.9 33.9,89.0" fill="#b0316e" fill-opacity="0.45"></polygon></g>
    <circle cx="42" cy="60" r="17" fill="none" stroke="#17161c" stroke-width="11"></circle>
    <line x1="59" y1="16" x2="59" y2="82.5" stroke="#17161c" stroke-width="11"></line>
  </svg>
  <div style="display:flex;flex-direction:column;gap:22px;min-width:0">
    <div style="display:flex;align-items:baseline;gap:16px">
      <span style="font:600 104px/1 'Barlow Condensed',sans-serif;color:#17161c;letter-spacing:.005em">districtry</span>
      <span style="font:400 82px/1 'Barlow Condensed',sans-serif;color:#9aa3b2">/ ${label}</span>
    </div>
    <div style="font:500 40px/1.25 Barlow,sans-serif;color:#374151;text-wrap:pretty">They're your Districts. Now in one place.</div>
    <div style="font:400 24px/1 Barlow,sans-serif;color:#9aa3b2">districtry.com</div>
  </div>
</div>
</body></html>`;

const tmpFile = join("/tmp", `og-card-${instance}.html`);
writeFileSync(tmpFile, html);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.goto("file://" + tmpFile);
await page.evaluate(() => document.fonts.ready); // wait for @font-face, not a fixed timeout
const outPath = join(REPO_ROOT, instance, "og-image.png");
await page.locator("#og-card").screenshot({ path: outPath });
await browser.close();
console.log("build-og-image: wrote " + outPath + " (label: " + label + ")");

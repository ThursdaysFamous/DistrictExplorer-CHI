// Build the social-share card (og-image.png, 1200x630) rendered by headless
// Chromium via Playwright. Rare operator step — run only when the wordmark,
// tagline, or brand palette changes, then commit the regenerated PNG:
//
//   npm install playwright@1.56.1     # browsers are pre-installed in CI/web
//   node scripts/build_og_image.mjs
//
// The card is self-contained (no web fonts — social crawlers render it once,
// server-side, so it must not depend on network assets). Palette mirrors the
// Chicago-flag values in index.html's :root; the star is the same 6-pointed
// flag star used by the favicon. Output is written to ./og-image.png and is
// referenced as an absolute https URL by the Open Graph / Twitter tags in
// index.html. 1200x630 at deviceScaleFactor 1 so the pixels match the declared
// og:image:width / og:image:height exactly.
import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const STAR =
  "M600,60 L633,205 L780,168 L668,270 L780,372 L633,335 L600,480 " +
  "L567,335 L420,372 L532,270 L420,168 L567,205 Z";

const HTML = `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin: 0; box-sizing: border-box; }
  html, body { width: 1200px; height: 630px; }
  body {
    background: #14181C; color: #fff; overflow: hidden; position: relative;
    font-family: "Liberation Sans", "Helvetica Neue", Arial, sans-serif;
  }
  /* Chicago-flag stripe motif (light blue / white / light blue) */
  .stripe { position: absolute; left: 0; right: 0; height: 18px;
    background: linear-gradient(to bottom, #41B6E6 0 30%, #fff 30% 70%, #41B6E6 70% 100%); }
  .stripe.top { top: 0; } .stripe.bottom { bottom: 0; }
  .wrap { position: absolute; inset: 18px 0; display: flex; align-items: center; padding: 0 84px; gap: 56px; }
  .star { width: 220px; height: 220px; flex: none; filter: drop-shadow(0 6px 18px rgba(200,16,46,.35)); }
  .title { font-size: 92px; font-weight: 800; line-height: 0.94; letter-spacing: -1.5px;
    text-transform: uppercase; }
  .title .lo { color: #41B6E6; }
  .tag { margin-top: 26px; font-size: 34px; font-weight: 500; color: #D3DCE2; max-width: 640px; line-height: 1.25; }
  .chips { margin-top: 26px; font-size: 21px; letter-spacing: .3px; color: #93A0A9; }
  .url { position: absolute; bottom: 44px; right: 84px; font-size: 26px; font-weight: 700;
    letter-spacing: .5px; color: #41B6E6; }
</style></head><body>
  <div class="stripe top"></div>
  <div class="wrap">
    <svg class="star" viewBox="0 0 1200 540"><path d="${STAR}" fill="#C8102E"/></svg>
    <div>
      <div class="title">Chicago<br><span class="lo">District Explorer</span></div>
      <div class="tag">Which districts cover this address — and who represents you?</div>
      <div class="chips">Wards · Police districts · Community areas · Congress · State · County · School zones</div>
    </div>
  </div>
  <div class="stripe bottom"></div>
  <div class="url">chidistricts.com</div>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await page.setContent(HTML, { waitUntil: "networkidle" });
const buf = await page.screenshot({ type: "png", clip: { x: 0, y: 0, width: 1200, height: 630 } });
writeFileSync("og-image.png", buf);
await browser.close();
console.log("wrote og-image.png (1200x630,", buf.length, "bytes)");

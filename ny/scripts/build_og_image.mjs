// Build the social-share card (og-image.png, 1200x630) rendered by headless
// Chromium via Playwright. Rare operator step — run only when the wordmark,
// tagline, or brand palette changes, then commit the regenerated PNG:
//
//   npm install playwright@1.56.1     # browsers are pre-installed in CI/web
//   node scripts/build_og_image.mjs
//
// The card is self-contained (no web fonts — social crawlers render it once,
// server-side, so it must not depend on network assets). Palette mirrors the
// New York City flag values in index.html's :root; the emblem is the city
// flag's blue/white/orange vertical tricolor. Output is written to
// ./og-image.png and referenced as an absolute https URL by the Open Graph /
// Twitter tags in index.html. 1200x630 at deviceScaleFactor 1 so the pixels
// match the declared og:image:width / og:image:height exactly.
import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const HTML = `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin: 0; box-sizing: border-box; }
  html, body { width: 1200px; height: 630px; }
  body {
    background: #14181C; color: #fff; overflow: hidden; position: relative;
    font-family: "Liberation Sans", "Helvetica Neue", Arial, sans-serif;
  }
  /* NYC-flag tricolor motif (blue / white / orange) */
  .stripe { position: absolute; left: 0; right: 0; height: 18px; display: flex; }
  .stripe span { flex: 1; }
  .stripe .b { background: #12305C; } .stripe .w { background: #fff; } .stripe .o { background: #FF6319; }
  .stripe.top { top: 0; } .stripe.bottom { bottom: 0; }
  .wrap { position: absolute; inset: 18px 0; display: flex; align-items: center; padding: 0 80px; gap: 56px; }
  .flag { width: 188px; height: 132px; flex: none; display: flex; border-radius: 10px; overflow: hidden;
    box-shadow: 0 8px 22px rgba(0,0,0,.45); border: 1px solid rgba(255,255,255,.12); }
  .flag span { flex: 1; }
  .flag .b { background: #12305C; } .flag .w { background: #fff; } .flag .o { background: #FF6319; }
  .title { font-size: 76px; font-weight: 800; line-height: 0.96; letter-spacing: -1.5px; text-transform: uppercase; }
  .title .lo { color: #4A90D9; }
  .tag { margin-top: 24px; font-size: 33px; font-weight: 500; color: #D3DCE2; max-width: 660px; line-height: 1.25; }
  .chips { margin-top: 24px; font-size: 20px; letter-spacing: .3px; color: #93A0A9; }
  .url { position: absolute; bottom: 44px; right: 80px; font-size: 26px; font-weight: 700;
    letter-spacing: .5px; color: #4A90D9; }
</style></head><body>
  <div class="stripe top"><span class="b"></span><span class="w"></span><span class="o"></span></div>
  <div class="wrap">
    <div class="flag"><span class="b"></span><span class="w"></span><span class="o"></span></div>
    <div>
      <div class="title">New York City<br><span class="lo">District Explorer</span></div>
      <div class="tag">Which districts cover this address — and who represents you?</div>
      <div class="chips">Council districts · Community boards · NYPD precincts · School districts · State · Congress</div>
    </div>
  </div>
  <div class="stripe bottom"><span class="b"></span><span class="w"></span><span class="o"></span></div>
  <div class="url">nyc.chidistricts.com</div>
</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await page.setContent(HTML, { waitUntil: "networkidle" });
const buf = await page.screenshot({ type: "png", clip: { x: 0, y: 0, width: 1200, height: 630 } });
writeFileSync("og-image.png", buf);
await browser.close();
console.log("wrote og-image.png (1200x630,", buf.length, "bytes)");

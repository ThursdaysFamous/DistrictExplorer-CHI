// Behaviour gate: every page in the sitemap carries the same brand and the same
// standing links — run in CI by smoke-test.yml.
//
// WHY THIS EXISTS. On 2026-08-24 three published pages were found still serving
// the pre-rebrand skin — ny/council-district.html, ny/community-board.html and
// ca/supervisor-district.html were on Inter and Big Shoulders, with no theme
// boot and no mark, while Illinois's three equivalents had all of it. They had
// survived two consecutive stages whose entire subject was the rebrand.
//
// Nothing caught them because nothing COMPARED them. compose_app.py checks the
// apps, generate_metro_files.py checks generated regions, validate_card_links.py
// checks that links resolve — and not one of them asks whether two published
// documents look like the same product. The pages were found by a throwaway
// script that drove all seventeen urls and printed a row each; this is that
// script, kept.
//
// IT DERIVES ITS SURFACE, IT DOES NOT CARRY A LIST. The pages come from
// sitemap.xml and the expectations from the tree — a page is expected to link
// its instance's sources page when that instance HAS one, and never to link
// itself. So a new page is covered the day it ships, and a correct change (a
// fourth instance, a retired sub-page) cannot fail it. That distinction is the
// difference between a gate and a tripwire: SF's smoke test asserted its brand
// name as a literal and failed the rebrand, which is the failure mode to avoid.
//
//   node scripts/page_consistency_test.mjs      # BASE_URL defaults to :8000
import { chromium } from "playwright";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

// The sandbox's headless Chromium cannot reach cdnjs, so the three map pages
// would fail the console check on "L is not defined" — an environment fact, not
// a page defect. The smoke tests already solve this by serving the vendored copy
// same-origin; this does the same rather than exempting the pages, so the gate
// tests the real thing everywhere. Absent (production, GitHub Actions) the
// browser loads Leaflet from the CDN exactly as a reader does.
const VENDOR = join(ROOT, "scripts", "vendor", "leaflet");
const LEAFLET = existsSync(join(VENDOR, "leaflet.js")) && existsSync(join(VENDOR, "leaflet.css"))
  ? { js: readFileSync(join(VENDOR, "leaflet.js")), css: readFileSync(join(VENDOR, "leaflet.css")) }
  : null;
if (LEAFLET) console.log("  (serving Leaflet from scripts/vendor/leaflet — CDN unreachable in this env)");
const BASE = (process.env.BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const WHY = "https://overberg.co/why/";

const paths = [...readFileSync(join(ROOT, "sitemap.xml"), "utf8")
  .matchAll(/<loc>([^<]+)<\/loc>/g)]
  .map((m) => m[1].replace(/^https?:\/\/[^/]+/, ""));

const failures = [];
const probed = new Map();
function check(page, name, ok, detail) {
  if (!ok) failures.push(`${page} — ${name}${detail ? ": " + detail : ""}`);
  return ok;
}

// Luminance rather than the data-theme attribute: the attribute is only set
// when a reader has actually chosen a theme, so a fresh visit legitimately has
// none. What must hold on every page either way is that it paints the ground
// its viewer asked for.
const lum = (rgb) => {
  const [r, g, b] = (rgb.match(/\d+/g) || [255, 255, 255]).map(Number);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

const browser = await chromium.launch();
try {
  for (const path of paths) {
    const seg = path.replace(/^\/|\/$/g, "").split("/");
    const tag = seg.length > 1 ? seg[0] : null;       // null for the root pages
    const file = path.endsWith("/") ? "index.html" : seg[seg.length - 1];

    for (const scheme of ["light", "dark"]) {
      const ctx = await browser.newContext({ colorScheme: scheme, serviceWorkers: "block" });
      const p = await ctx.newPage();
      if (LEAFLET) {
        await p.route("**/cdnjs.cloudflare.com/**/leaflet.js", (r) =>
          r.fulfill({ status: 200, contentType: "application/javascript", body: LEAFLET.js }));
        await p.route("**/cdnjs.cloudflare.com/**/leaflet.css", (r) =>
          r.fulfill({ status: 200, contentType: "text/css", body: LEAFLET.css }));
      }
      const errs = [];
      p.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
      p.on("pageerror", (e) => errs.push(String(e)));
      const resp = await p.goto(BASE + path, { waitUntil: "domcontentloaded" });
      await p.waitForTimeout(250); // let the theme boot and any inline script run
      check(path, `loads (${scheme})`, resp.status() === 200, `HTTP ${resp.status()}`);

      const info = await p.evaluate(() => ({
        font: getComputedStyle(document.body).fontFamily.split(",")[0].replace(/['"]/g, ""),
        bg: getComputedStyle(document.body).backgroundColor,
        mark: !!document.querySelector(".districtry-mark, .logo-mark"),
        canonical: !!document.querySelector("link[rel=canonical]"),
        ogTitle: !!document.querySelector('meta[property="og:title"]'),
        links: [...document.querySelectorAll("a[href]")].map((a) => a.getAttribute("href") || ""),
      }));

      check(path, `brand typeface (${scheme})`, info.font === "Barlow", info.font);
      check(path, `paints a ${scheme} ground`, (lum(info.bg) < 90) === (scheme === "dark"), info.bg);
      check(path, `carries the mark (${scheme})`, info.mark);
      check(path, "canonical", info.canonical);
      check(path, "og:title", info.ogTitle);

      // GoatCounter cannot be reached from a sandbox and its failure is not a
      // page defect — it reproduces identically on every page including ones
      // nobody touched.
      const real = errs.filter((e) => !/gc\.zgo\.at|ERR_CONNECTION_RESET/.test(e));
      check(path, `no console errors (${scheme})`, real.length === 0, real.slice(0, 2).join(" | "));

      if (scheme !== "light") { await ctx.close(); continue; }

      // --- the standing links, expected from the TREE rather than a list ----
      const want = [];
      if (tag) {
        if (file !== "sources.html" && existsSync(join(ROOT, tag, "sources.html"))) want.push("sources.html");
        if (file !== "faq.html" && existsSync(join(ROOT, tag, "faq.html"))) want.push("faq.html");
      }
      want.push("privacy");
      want.push(WHY);
      for (const w of want) {
        const has = w === "privacy"
          ? info.links.some((h) => /(^|\/)privacy\.html$/.test(h))
          : info.links.some((h) => h.endsWith(w));
        check(path, `links ${w}`, has || (w === "privacy" && file === "privacy.html"));
      }

      // --- every relative link resolves, each distinct url probed ONCE -------
      for (const h of info.links.filter((x) => x && !/^(https?:|mailto:|#)/.test(x))) {
        const abs = new URL(h, BASE + path).href;
        if (!probed.has(abs)) probed.set(abs, (await p.request.get(abs)).status());
        check(path, `link ${h}`, probed.get(abs) === 200, `HTTP ${probed.get(abs)}`);
      }
      await ctx.close();
    }
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(`\n${failures.length} consistency failure(s):`);
  for (const f of failures) console.error("  - " + f);
  process.exit(1);
}
console.log(`All ${paths.length} sitemap page(s) consistent — brand, metadata, standing links, no dead links.`);

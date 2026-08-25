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

// WCAG relative luminance + contrast, for the check below. This is a different
// calculation from `lum` above and both are wanted: `lum` answers "is this
// ground dark or light", which wants a cheap perceptual number, and this
// answers "can the text on it be read", which is a defined ratio with a
// defined threshold.
const rel = (rgb) => {
  const [r, g, b] = (rgb.match(/\d+/g) || [255, 255, 255]).map(Number);
  const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
};
const contrast = (fg, bg) => {
  const a = rel(fg), b = rel(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
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
        // The bars, measured rather than assumed. This page's whole subject is
        // whether two documents look like the same product, and it was passing
        // twelve pages whose header was a near-white bar carrying #fff text.
        bars: [["header", "header.masthead, .masthead, header"],
               ["footer", "footer.site-footer, footer"]].map(([role, sel]) => {
          const el = document.querySelector(sel);
          if (!el) return { role, missing: true };
          // Only what a reader SEES. getComputedStyle happily returns colours
          // for a display:none element, and the first draft of this check
          // failed all three apps on their footers — which the app skin hides,
          // because the links moved to the masthead. A contrast finding on an
          // invisible bar is noise, and noise is how a gate stops being read.
          if (!el.getClientRects().length) return { role, missing: true };
          const txt = el.querySelector("h1, h2, p, a") || el;
          return { role, bg: getComputedStyle(el).backgroundColor,
                   fg: getComputedStyle(txt).color };
        }),
        // The search box against the map, measured as rectangles. An app page
        // puts its search in the masthead toolbar BESIDE the layer pills; NY
        // and SF shipped it floating over the map instead, because the CSS for
        // both placements is shared and identical (`.masthead .map-toolbar {
        // position: static }` — a DESCENDANT selector) while the markup that
        // decides which one applies is per-instance, and only Chicago's was
        // ever moved. Nothing compared them, so it came back.
        //
        // Geometry, not markup: "is the toolbar inside the masthead" would pass
        // a toolbar that is inside the masthead and still painted over the map
        // by a position rule, and it would fail a future layout that solves
        // this a different and perfectly good way. What must never be true is
        // that the search covers the thing you are meant to click.
        search: (() => {
          const box = document.querySelector(".search-shell") ||
                      document.getElementById("geocode-input");
          const map = document.getElementById("map");
          if (!box || !map) return null;          // sub-pages have neither
          const a = box.getBoundingClientRect(), m = map.getBoundingClientRect();
          const over = !(a.right <= m.left || a.left >= m.right ||
                         a.bottom <= m.top || a.top >= m.bottom);
          return { over, box: [Math.round(a.top), Math.round(a.left)],
                   map: [Math.round(m.top), Math.round(m.left)] };
        })(),
        // The app's two standing footer facts, measured as pixels: the date
        // the data was last verified, and the way to report a problem with it.
        // The skin hides `footer.site-footer` (the links moved to the
        // masthead), so an app that leaves these inside that husk RENDERS them
        // and shows them to nobody. Chicago relocated them into the
        // results-panel foot at the redesign; NY and SF did not, and shipped
        // for weeks with an invisible verified date and no reachable feedback
        // button — past every gate in this repo, because parity of the SHARED
        // engine was checked and parity of what a reader can SEE was not.
        // Anchored to the map so sub-pages (which have neither) skip it.
        appFoot: (() => {
          if (!document.getElementById("map")) return null;
          const seen = (el) => !!el && el.getClientRects().length > 0 &&
                               getComputedStyle(el).visibility !== "hidden";
          return { date: seen(document.getElementById("verified-date")),
                   feedback: seen(document.getElementById("feedback-btn")) };
        })(),
        canonical: !!document.querySelector("link[rel=canonical]"),
        ogTitle: !!document.querySelector('meta[property="og:title"]'),
        links: [...document.querySelectorAll("a[href]")].map((a) => a.getAttribute("href") || ""),
      }));

      check(path, `brand typeface (${scheme})`, info.font === "Barlow", info.font);
      check(path, `paints a ${scheme} ground`, (lum(info.bg) < 90) === (scheme === "dark"), info.bg);
      check(path, `carries the mark (${scheme})`, info.mark);

      if (info.search) {
        check(path, `search sits beside the map, not on it (${scheme})`,
              !info.search.over,
              `search@${info.search.box} overlaps map@${info.search.map}`);
      }

      if (info.appFoot) {
        check(path, `verified date is visible to a reader (${scheme})`, info.appFoot.date);
        check(path, `feedback button is reachable (${scheme})`, info.appFoot.feedback);
      }

      // A surface is never a text token. `background: var(--ink)` reads as a
      // deliberate dark bar in light mode and is a coincidence — --ink is the
      // TEXT colour, so in dark mode it flips and the bar turns near-white with
      // white text on it. Twelve of thirteen sub-pages shipped that way,
      // measured at 1.20:1 against WCAG AA's 4.5:1, past every gate in this
      // repo including this one. 4.5 is the body-text threshold; a masthead
      // title is large text, whose bar is 3:1, so the stricter number is used
      // deliberately — nothing here needs to sit between them.
      for (const bar of info.bars) {
        if (bar.missing) continue;
        if (/rgba\(0, 0, 0, 0\)|transparent/.test(bar.bg)) continue;  // inherits the ground
        const c = contrast(bar.fg, bar.bg);
        check(path, `${bar.role} text is readable on its own bar (${scheme})`,
              c >= 4.5, `${c.toFixed(2)}:1 — ${bar.fg} on ${bar.bg}`);
      }
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

// Behaviour gate for the root landing page (R4) — run in CI by smoke-test.yml.
//
// WHY THIS IS A GATE AND NOT A SCRATCH SCRIPT. The page itself is generated and
// drift-checked by build_landing_page.py, which proves it matches metros.json.
// It cannot prove the page still WORKS, and the part that matters most is
// invisible to a diff: the forwarding guard.
//
// Before R2.3 the Illinois app served from this origin's root, so every share
// link and embed snippet it handed out was built from the root URL —
//
//   https://chidistricts.com/?utm_source=share&utm_medium=link#point=41.88,-87.63
//   <iframe src="https://chidistricts.com/?utm_source=embed&utm_medium=iframe#point=...">
//
// — and those live in other people's pages and bookmarks and cannot be recalled.
// The guard is what keeps them reaching the map instead of a page about
// Illinois. A regex typo or a changed FORWARD_TO would break every one of them
// silently, on a page that still looks perfect and still passes its drift
// check. So the forward is asserted here, in a real browser, both ways: an app
// link forwards with its query AND hash intact, and a plain visit does not.
//
//   node scripts/landing_test.mjs          # BASE_URL defaults to :8131
import { chromium } from "playwright";

const BASE = process.env.BASE_URL || "http://localhost:8131";
const failures = [];
function check(name, ok, detail) {
  console.log(`  ${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
  if (!ok) failures.push(name);
}

const browser = await chromium.launch();
try {
  // --- 1. a bare visit renders the landing page, and does NOT forward -------
  {
    const ctx = await browser.newContext({ serviceWorkers: "block" });
    const page = await ctx.newPage();
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(400);
    const url = page.url();
    check("bare / stays on the landing page", new URL(url).pathname === "/", url);

    const wordmark = await page.textContent(".wordmark").catch(() => null);
    check("wordmark renders", wordmark === "districtry", JSON.stringify(wordmark));

    const cards = await page.$$eval(".card", (els) =>
      els.map((e) => ({
        href: e.getAttribute("href"),
        name: e.querySelector("b")?.textContent,
        tag: e.querySelector(".card-tag")?.textContent?.trim(),
      })));
    check("every fleet place is listed", cards.length === 3, JSON.stringify(cards.map(c => c.name)));
    check("Illinois card points at /il/",
      cards.some((c) => c.name === "Illinois" && /\/il\/$/.test(c.href)),
      cards.find((c) => c.name === "Illinois")?.href);
    check("cards carry their instance tag",
      cards.every((c) => /^\/ (il|nyc|sf)$/.test(c.tag || "")),
      JSON.stringify(cards.map((c) => c.tag)));

    // Barlow must actually be applied, not silently falling back to system-ui.
    const font = await page.evaluate(() =>
      getComputedStyle(document.querySelector(".wordmark")).fontFamily);
    check("wordmark uses Barlow Condensed", /Barlow Condensed/.test(font), font);
    const loaded = await page.evaluate(async () => {
      await document.fonts.ready;
      return [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family + " " + f.weight);
    });
    check("a self-hosted face actually loaded", loaded.length > 0, JSON.stringify(loaded));
    await ctx.close();
  }

  // --- 2-4. old app links forward, carrying query AND hash ----------------
  //
  // /il/ IS STUBBED, and that is the point of this block. The guard's whole job
  // is to hand the instance the exact query+hash it was given; what the app then
  // does with that hash is the app's business, and it does plenty — booting, it
  // calls syncUrlHash() and rewrites location.hash into its own canonical form
  // (5-decimal coordinates, an appended &zoom=). Asserting the post-boot URL
  // therefore tests the APP's normalisation, not the guard.
  //
  // The first draft did exactly that and passed locally for the worst possible
  // reason: the sandbox cannot reach the Leaflet CDN, so the app never booted,
  // never rewrote the hash, and the byte comparison held. CI reached the CDN,
  // the app booted, and two checks failed on a guard that was working perfectly.
  // Stubbing the destination removes both the app and the network from the
  // measurement, so this asserts one thing and asserts it the same way
  // everywhere.
  for (const [name, query, hash] of [
    ["permalink", "", "#point=41.88250,-87.62850&layers=ward,school-board"],
    ["embed url", "?utm_source=embed&utm_medium=iframe", "#point=41.99,-87.66"],
    ["share link", "?utm_source=share&utm_medium=link", "#point=41.9,-87.6"],
    ["bare campaign tag", "?utm_source=share&utm_medium=link", ""],
  ]) {
    const ctx = await browser.newContext({ serviceWorkers: "block" });
    const page = await ctx.newPage();
    await page.route("**/il/**", (r) =>
      r.fulfill({ status: 200, contentType: "text/html", body: "<!doctype html><title>il stub</title>" }));
    await page.goto(BASE + "/" + query + hash, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(400);
    const u = new URL(page.url());
    // Assert the stub actually served, never assume it: if the route pattern
    // stopped matching, the REAL app would load and rewrite the hash, and this
    // block would quietly go back to testing the app's normalisation.
    const title = await page.title();
    check(`${name} lands on the stub (not the live app)`, title === "il stub", title);
    check(`${name} forwards to /il/`, u.pathname === "/il/", page.url());
    check(`${name} keeps its query verbatim`, u.search === query, JSON.stringify(u.search));
    check(`${name} keeps its hash verbatim`, u.hash === hash, JSON.stringify(u.hash));
    await ctx.close();
  }

  // --- 5. an UNRELATED query must NOT forward (it is not an app link) ------
  {
    const ctx = await browser.newContext({ serviceWorkers: "block" });
    const page = await ctx.newPage();
    await page.goto(BASE + "/?utm_source=newsletter", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);
    check("an unrelated campaign query stays on the landing page",
      new URL(page.url()).pathname === "/", page.url());
    await ctx.close();
  }

  // --- 6. no console errors on the landing page ---------------------------
  {
    const ctx = await browser.newContext({ serviceWorkers: "block" });
    const page = await ctx.newPage();
    const errs = [];
    page.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
    page.on("pageerror", (e) => errs.push(String(e)));
    await page.goto(BASE + "/", { waitUntil: "load" });
    await page.waitForTimeout(500);
    check("landing page boots with no console errors", errs.length === 0, errs.slice(0, 2).join(" | "));
    await ctx.close();
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(`\n${failures.length} landing check(s) failed: ${failures.join(", ")}`);
  process.exit(1);
}
console.log("\nAll landing-page checks passed.");

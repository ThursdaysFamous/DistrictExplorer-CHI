// Measure which layers send the READER'S SELECTED POINT to a server — in a
// real browser, because nothing else can see it.
//
// WHY THIS EXISTS. `scripts/build_privacy_page.py` publishes, per app, how many
// layers ask a government server about your exact selected point rather than
// downloading a boundary set and testing the point in your browser. It measured
// that by counting `loadArcGISPointGeoJSON(` call sites, and the figure was
// wrong: Illinois published 10 against a true 19, and New York City published
// "None." against a true 4 — an app telling readers nothing about their click
// left the browser while four of its layers sent it.
//
// NO STATIC READ CAN BE RIGHT, AND THAT IS MEASURED RATHER THAN ASSUMED. Two
// separate defects put the answer out of a regex's reach:
//
//   * A REGISTRATION FACTORY serves as many layers as it is CALLED, from one
//     source occurrence, so counting occurrences is wrong in both directions:
//     Illinois's CPS factories each build one loader for three layers and for
//     two, while San Francisco defines two it never calls for a layer at all.
//
//   * `registerCountyLayer` CLOSES OVER its entries. The spec it hands to
//     `registerLayer` never references them, so even a full walk of the
//     registered module's object graph cannot see Illinois's `ward` (whose
//     loader is the Chicago entry's `loadGeometry`) or `county-board` (whose
//     Cook entry carries an explicit ArcGIS `.atPoint`). Both send the point.
//
// SO THE MEASUREMENT IS BEHAVIOURAL — AND "BEHAVIOURAL" MEANS THE HOOK FIRES,
// NOT THAT A LOADER CARRIES ONE. This file's first version inspected each
// layer's loaders for a `.atPoint` property and counted the layers that had
// one. THAT OVERCOUNTS, because carrying the hook is necessary and not
// sufficient: `.atPoint` is invoked in exactly ONE place in every instance,
// inside `queryFeatureAt`, and a layer whose query does not route through
// `queryFeatureAt` never fires it. `registerNearestPointLayer.query` calls
// `opts.loader()` directly, and several NYC and SF layers call their load
// function directly too — so a layer can hold a `makeCachedLoader` result,
// carry the Socrata hook, and never send a point anywhere. Published on the
// privacy page, that reads as an app confessing to a transmission it does not
// make.
//
// So each app is booted in Chromium, every observed `.atPoint` is REPLACED
// with a recorder, every layer is switched on, a point inside the instance's
// own coverage is selected, and the hooks that actually FIRE are counted. A
// layer whose query never ran is reported UNKNOWN rather than counted as a no:
// silence is not evidence of not sending.
//
// AND EVERY MEASURED LOADER IS PINNED UNCACHED, because otherwise the number
// is a race. `queryFeatureAt` answers locally the moment `load.cached()` has a
// value, so a layer only reaches its hook while the full boundary set is still
// downloading. Measured 2026-09-05: with the government APIs unreachable
// nothing caches and Illinois reports 19; on a CI runner that can reach them,
// the same commit reported 9. The uncached state is both the deterministic one
// and the one the privacy page is describing — a reader's first click on a
// fresh load — so the probe pins it rather than sampling whichever way the
// download raced.
//
// AND IT RECONCILES ITSELF, which is what keeps a future hiding place from
// silently reading as zero. Every `.atPoint` assignment site in the shipped
// source is reported as either FIRED or never fired; an observed hook whose
// body is NOT in the source means the probe's own injection or parse has
// broken, and that is a hard failure rather than a smaller number. A layer
// whose query never ran is counted in `layers_unexercised` and named, because
// a probe that quietly reports "does not send" for a layer it never asked is
// the same defect one level up.
//
// The result is written to point-transmission.json at the repo root, which
// `build_privacy_page.py` reads. That generator stays stdlib-only — it cannot
// boot a browser inside a CI step that has none — so it re-derives a
// FINGERPRINT from each shipped index.html and refuses to publish when the
// fingerprint has moved since this probe last ran.
//
//     node scripts/probe_point_transmission.mjs            # measure and write
//     node scripts/probe_point_transmission.mjs --check    # drift gate; exit 1
//
// Serve the repo first (python3 -m http.server 8000); BASE_URL overrides.

import { chromium } from "playwright";
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "point-transmission.json");
// Normalised to exactly one trailing slash. CI passes BASE_URL with none and
// scripts/smoke_test.mjs's callers pass one; concatenating either verbatim is
// how landing_test.mjs learned to fail every assertion on "localhost:8000//".
const BASE = (process.env.BASE_URL || "http://localhost:8000").replace(/\/+$/, "") + "/";
const CHECK = process.argv.includes("--check");
const BOOT_TIMEOUT = 45000;
const SETTLE_MS = 6000;   // time for every layer's query to reach its loader

// The point to select. Each instance's own worksheet anchor is used because it
// is chosen to be INSIDE that instance's coverage — a point outside it would
// suppress coverage-gated layers, which would then read as "does not send".
function anchorOf(tag) {
  const rel = tag === "il" ? "metro-worksheet.json" : join(tag, "metro-worksheet.json");
  const w = JSON.parse(readFileSync(join(ROOT, rel), "utf8"));
  const a = w.anchor_point;
  if (!a || typeof a.lat !== "number" || typeof a.lng !== "number")
    problem(`${tag}: no usable anchor_point in its worksheet`);
  return a || { lat: 0, lng: 0 };
}

// EXTRA POINTS, because coverage gating is real. A layer that declares
// `coverage(point)` is not queried outside it, and a probe that selects one
// point would report "does not send" for a layer it never asked. Illinois's
// elementary and high-school district layers declare
// `outsideChicagoSchoolCoverage` and are hidden inside the city, which is
// exactly where the worksheet anchor is — so the anchor alone leaves both
// unexercised. Evanston is an elementary + high-school PAIR (District 65 and
// Township 202) rather than unified territory, so it exercises both.
//
// Anything still unexercised after every point here is REPORTED, never counted
// as a no: this list is a way to reduce the unknowns, not to hide them.
const EXTRA_POINTS = {
  il: [{ lat: 42.0451, lng: -87.6877, note: "Evanston — elementary D65 + high-school D202, outside Chicago" }],
};

// An instance is a top-level directory with its own index.html and data/app —
// the same rule validate_card_links.py and validate_instance_registration.py
// discover by, so a seventh state is measured the day it lands with nothing
// here to edit. Illinois keeps its scripts at the repo root (the R2.3
// asymmetry), which is the only reason this needs a branch at all.
function instances() {
  return readdirSync(ROOT)
    .filter((d) => {
      try {
        return statSync(join(ROOT, d)).isDirectory() &&
          existsSync(join(ROOT, d, "index.html")) &&
          existsSync(join(ROOT, d, "data", "app"));
      } catch { return false; }
    })
    .sort();
}

function vendorDir(tag) {
  // The SessionStart hook vendors Leaflet per instance for sandboxes whose
  // Chromium cannot reach cdnjs; absent (production, GitHub Actions) the
  // browser loads it from the CDN exactly as a reader's would.
  return tag === "il"
    ? join(ROOT, "scripts", "vendor", "leaflet")
    : join(ROOT, tag, "scripts", "vendor", "leaflet");
}

const fail = [];
function problem(msg) { console.log("  FAIL  " + msg); fail.push(msg); }

// Normalise whitespace so a function body observed at runtime can be matched
// against the source it was written in, whatever its indentation.
const flat = (s) => s.replace(/\s+/g, " ").trim();

async function measure(browser, tag) {
  const src = readFileSync(join(ROOT, tag, "index.html"), "utf8");
  const flatSrc = flat(src);

  // Every `<name>.atPoint = function` in the shipped source. These are the
  // sites a layer can possibly reach; the runtime says which actually are.
  const sites = [...src.matchAll(/(\w+)\.atPoint\s*=\s*function/g)].map((m) => m[1]);

  // The generated area-rank list is every registered layer id, in the app file
  // itself — so the fingerprint moves when a layer is added, removed or
  // renamed, including one registered through a factory whose call site never
  // changes.
  const rankBlock = src.match(/var LAYER_AREA_RANK = \[([\s\S]*?)\n\s*\];/);
  const layerIds = rankBlock ? [...rankBlock[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]).sort() : [];
  if (!layerIds.length) problem(`${tag}: could not read LAYER_AREA_RANK from its index.html`);

  const ctx = await browser.newContext({ serviceWorkers: "block" });
  const page = await ctx.newPage();

  const dir = vendorDir(tag);
  for (const [file, type] of [["leaflet.js", "application/javascript"],
                              ["leaflet.css", "text/css"],
                              ["maplibre-gl.min.js", "application/javascript"]]) {
    if (existsSync(join(dir, file))) {
      const body = readFileSync(join(dir, file));
      await page.route(`**/cdnjs.cloudflare.com/**/${file}`,
        (r) => r.fulfill({ status: 200, contentType: type, body }));
    }
  }

  // The two injections. Both are additive one-liners into the app's own single
  // IIFE — nothing existing is rewritten, so what boots is the shipped app.
  let injectedRegistry = 0, injectedCounty = 0;
  await page.route(`**/${tag}/`, async (route) => {
    const res = await route.fetch();
    let body = await res.text();
    body = body.replace(/(\n(\s*)var entries = opts\.entries \|\| opts\.counties;)/g, (m, whole, indent) => {
      injectedCounty++;
      return m + `\n${indent}(window.__dxCountyEntries = window.__dxCountyEntries || [])` +
             `.push({ id: opts.id, entries: entries });`;
    });
    body = body.replace(/window\.\w*Explorer = EXPLORER_EXPORTS;/g, (m) => {
      injectedRegistry++;
      return m + "\n  EXPLORER_EXPORTS.__probeLayers = layers;";
    });
    route.fulfill({ response: res, body });
  });

  await page.goto(BASE + tag + "/", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => {
    for (const k of Object.keys(window))
      if (/Explorer$/.test(k) && window[k] && window[k].__probeLayers) return true;
    return false;
  }, null, { timeout: BOOT_TIMEOUT });

  if (!injectedRegistry) problem(`${tag}: the layer-registry injection matched nothing — the exports assignment has been renamed`);
  const countySites = (src.match(/var entries = opts\.entries \|\| opts\.counties;/g) || []).length;
  if (countySites !== injectedCounty)
    problem(`${tag}: registerCountyLayer injection matched ${injectedCounty} of ${countySites} sites`);

  const points = [anchorOf(tag), ...(EXTRA_POINTS[tag] || [])];
  const observed = await page.evaluate(async ({ points, settle }) => {
    const ns = Object.keys(window).find((k) => /Explorer$/.test(k) && window[k] && window[k].__probeLayers);
    const api = window[ns];
    const layers = api.__probeLayers;
    const byId = {};
    for (const c of (window.__dxCountyEntries || [])) (byId[c.id] = byId[c.id] || []).push(...c.entries);

    // Find every loader each layer holds, INCLUDING the ones a
    // registerCountyLayer entry closes over. Functions are leaves: the hook is
    // a property ON the loader, so there is never a reason to descend into one.
    function walk(node, seen, out, depth) {
      if (depth > 6 || node == null) return;
      if (typeof node === "function") { if (typeof node.atPoint === "function") out.push(node); return; }
      if (typeof node !== "object" || seen.has(node)) return;
      seen.add(node);
      if (Array.isArray(node)) { node.forEach((v) => walk(v, seen, out, depth + 1)); return; }
      for (const k of Object.keys(node)) {
        if (k === "_map" || k === "_container" || k === "map") continue;   // Leaflet's, not ours
        let v; try { v = node[k]; } catch { continue; }
        walk(v, seen, out, depth + 1);
      }
    }

    const fired = new Set();        // loader tokens whose .atPoint actually ran
    const queried = new Set();      // layer ids whose query() was invoked
    const holders = new Map();      // layer id -> loader tokens it holds
    const bodies = new Map();       // loader token -> the hook's source text
    const tokenOf = new WeakMap();
    let token = 0;

    for (const m of layers) {
      const loaders = [];
      walk(m, new Set(), loaders, 0);
      for (const e of (byId[m.id] || [])) walk(e, new Set(), loaders, 0);
      const mine = [];
      for (const load of loaders) {
        if (!tokenOf.has(load)) {
          const t = ++token;
          tokenOf.set(load, t);
          bodies.set(t, Function.prototype.toString.call(load.atPoint));
          // REPLACE the hook with a recorder. Resolving EMPTY is the app's own
          // "the point query found nothing" path, which defers to the full set,
          // so no card is made wrong by being measured.
          load.atPoint = function () {
            fired.add(t);
            return Promise.resolve({ type: "FeatureCollection", features: [] });
          };
          // AND PIN THE LOADER UNCACHED, which is the difference between a
          // measurement and a coin toss. queryFeatureAt short-circuits on
          // `load.cached()` and never reaches the hook once the full boundary
          // set has arrived, so whether a layer "sends" would otherwise depend
          // on whether a multi-megabyte download beat the click. It does not
          // reproduce: with the government APIs unreachable nothing caches and
          // every hook fires, and with them reachable Illinois measured 9 of
          // its 19 — same code, same commit, two answers.
          //
          // The uncached state is also the one the page is describing. A
          // reader's first click on a fresh load is exactly this, and the
          // page's own prose says so ("one district can answer immediately
          // while the full layer downloads"). So the question this probe asks
          // is "when the set is not yet cached, does this layer's query send
          // the point" — which has one answer, not a distribution.
          load.cached = function () { return null; };
        }
        mine.push(tokenOf.get(load));
      }
      holders.set(m.id, mine);

      // Record that a layer was actually ASKED. Without this, a layer supp-
      // ressed by coverage reads exactly like one that does not send.
      if (typeof m.query === "function") {
        const original = m.query;
        m.query = function () { queried.add(m.id); return original.apply(this, arguments); };
      }
    }

    // Switch everything on, THEN select: each layer is live when the selection
    // dispatches its query. Every point is selected in turn and the recorders
    // accumulate, so a layer only has to be in coverage at ONE of them.
    for (const box of document.querySelectorAll('input[type="checkbox"][id^="toggle-"]'))
      if (!box.checked) box.click();
    for (const pt of points) {
      api.setSelectedPoint(pt.lat, pt.lng);
      await new Promise((r) => setTimeout(r, settle));
    }

    return {
      layers: layers.map((m) => ({
        id: m.id,
        holds: (holders.get(m.id) || []).length,
        queried: queried.has(m.id),
        sends: (holders.get(m.id) || []).some((t) => fired.has(t)),
      })),
      firedBodies: [...fired].map((t) => bodies.get(t)),
      allBodies: [...bodies.values()],
    };
  }, { points: points.map((p) => ({ lat: p.lat, lng: p.lng })), settle: SETTLE_MS });
  await ctx.close();

  const sending = observed.layers.filter((o) => o.sends).map((o) => o.id).sort();
  // Asked, holds a hook, did not fire it: a real measurement — its query does
  // not route through queryFeatureAt, which is the ONLY place the hook is
  // invoked. This is the set the first version of this probe counted as
  // sending, and is why it overcounted.
  const holdsButSilent = observed.layers
    .filter((o) => o.holds && o.queried && !o.sends).map((o) => o.id).sort();
  // Holds a hook and was never asked — not evidence either way, so it is named
  // rather than quietly counted as a no.
  const unexercised = observed.layers
    .filter((o) => o.holds && !o.queried && !o.sends).map((o) => o.id).sort();

  // RECONCILE. Every hook body seen at runtime must be findable in the shipped
  // source; one that is not means this probe read something the app does not
  // contain, and no number it produces can be trusted.
  for (const b of observed.allBodies.map(flat))
    if (!flatSrc.includes(b))
      problem(`${tag}: observed an .atPoint body that is not in the shipped source — ${b.slice(0, 90)}`);

  const firedDistinct = new Set(observed.firedBodies.map(flat)).size;
  if (firedDistinct > sites.length)
    problem(`${tag}: ${firedDistinct} distinct hooks fired against ${sites.length} declared in the source`);

  return {
    layers_sending_point: sending.length,
    layers: sending,
    layers_holding_hook_but_silent: holdsButSilent,
    layers_unexercised: unexercised,
    atpoint_sites: [...sites].sort(),
    atpoint_hooks_fired: firedDistinct,
    layer_ids: layerIds,
  };
}

const browser = await chromium.launch();
const apps = {};
for (const tag of instances()) {
  process.stdout.write(`  ${tag} … `);
  apps[tag] = await measure(browser, tag);
  const a = apps[tag];
  console.log(`${a.layers_sending_point} of ${a.layer_ids.length} layers send the point ` +
              `(${a.atpoint_hooks_fired} of ${a.atpoint_sites.length} .atPoint hooks fired)`);
  if (a.layers_sending_point) console.log(`        sends: ${a.layers.join(", ")}`);
  if (a.layers_holding_hook_but_silent.length)
    console.log(`        holds a hook and never fires it: ${a.layers_holding_hook_but_silent.join(", ")}`);
  if (a.layers_unexercised.length)
    console.log(`        UNEXERCISED (holds a hook, query never ran): ${a.layers_unexercised.join(", ")}`);
}
await browser.close();

const payload = {
  _comment: [
    "MEASURED, NOT HAND-KEPT. Regenerate with:  node scripts/probe_point_transmission.mjs",
    "Which layers ask a government server about the reader's exact selected point,",
    "rather than downloading a boundary set and testing the point in the browser.",
    "scripts/build_privacy_page.py publishes layers_sending_point per app and",
    "refuses to run if atpoint_sites or layer_ids have moved since this was written.",
  ],
  apps,
};

const rendered = JSON.stringify(payload, null, 2) + "\n";
if (CHECK) {
  if (!existsSync(OUT)) problem(`${OUT} is missing — run the probe without --check`);
  else if (readFileSync(OUT, "utf8") !== rendered)
    problem("point-transmission.json is stale — an app changed what it sends. " +
            "Re-run: node scripts/probe_point_transmission.mjs, then " +
            "python3 scripts/build_privacy_page.py");
  if (fail.length) { console.log(`\n${fail.length} problem(s).`); process.exit(1); }
  console.log("\npoint-transmission.json matches what the apps actually do.");
} else {
  if (fail.length) { console.log(`\n${fail.length} problem(s) — refusing to write.`); process.exit(1); }
  writeFileSync(OUT, rendered);
  console.log(`\nwrote ${OUT}`);
}

// Measure which layers send the READER'S SELECTED POINT to a server — in a
// real browser, because nothing else can see it.
//
// WHY THIS EXISTS. `scripts/build_privacy_page.py` publishes, per app, how many
// layers ask a government server about your exact selected point rather than
// downloading a boundary set and testing the point in your browser. It measured
// that by counting `loadArcGISPointGeoJSON(` call sites, and on 2026-09-05 that
// figure was wrong for three of the six apps: Illinois published 10 against a
// true 20, and New York City and San Francisco published "None." against a true
// 9 and 3. Two apps were telling readers nothing left their browser when nine
// layers and three layers did.
//
// NO STATIC READ CAN BE RIGHT, AND THAT IS MEASURED RATHER THAN ASSUMED. Two
// separate defects put the answer out of a regex's reach:
//
//   * A REGISTRATION FACTORY serves as many layers as it is CALLED, from one
//     source occurrence. `makeCachedLoader` (which attaches the Socrata
//     point hook) is called 7, 8 and 5 times in il/ny/ca against true counts of
//     8, 9 and 3 — wrong in BOTH directions, because Illinois's CPS factories
//     each build one loader for three and two layers while San Francisco
//     defines two factories it never calls for a registered layer.
//
//   * `registerCountyLayer` CLOSES OVER its entries. The spec it hands to
//     `registerLayer` never references them, so even a full walk of the
//     registered module's object graph cannot see Illinois's `ward` (whose
//     loader is the Chicago entry's `loadGeometry`) or `county-board` (whose
//     Cook entry carries an explicit ArcGIS `.atPoint`). Both send the point.
//
// SO THE MEASUREMENT IS BEHAVIOURAL. Each app is booted in Chromium with two
// one-line injections — the layer registry onto the debug namespace, and
// `registerCountyLayer`'s entries onto `window` — and every loader the layers
// hold is inspected for the `.atPoint` hook. `queryFeatureAt` calls that hook
// whenever the full boundary set is not yet cached, so a loader carrying it
// transmits the selected point.
//
// AND IT RECONCILES ITSELF, which is what keeps a future hiding place from
// silently reading as zero. Every `.atPoint` assignment site in the shipped
// source must be either REACHED by an observed layer or reported as unreached;
// an observed hook whose body is NOT in the source means the probe's own
// injection or parse has broken, and that is a hard failure rather than a
// smaller number. Today six of six sites are reached in Illinois, and the three
// unreached ones across wi/ia/mi are all the engine's `makeCachedLoader`,
// carried by every instance and used for a layer by only three.
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

  const observed = await page.evaluate(() => {
    const ns = Object.keys(window).find((k) => /Explorer$/.test(k) && window[k] && window[k].__probeLayers);
    const layers = window[ns].__probeLayers;
    const byId = {};
    for (const c of (window.__dxCountyEntries || [])) (byId[c.id] = byId[c.id] || []).push(...c.entries);

    // Walk everything a layer module holds. Functions are leaves — the hook is
    // a property ON the loader, so there is never a reason to descend into one.
    function walk(node, seen, out, depth) {
      if (depth > 6 || node == null) return;
      if (typeof node === "function") {
        if (typeof node.atPoint === "function")
          out.push(Function.prototype.toString.call(node.atPoint));
        return;
      }
      if (typeof node !== "object" || seen.has(node)) return;
      seen.add(node);
      if (Array.isArray(node)) { node.forEach((v) => walk(v, seen, out, depth + 1)); return; }
      for (const k of Object.keys(node)) {
        if (k === "_map" || k === "_container" || k === "map") continue;  // Leaflet's, not ours
        let v; try { v = node[k]; } catch { continue; }
        walk(v, seen, out, depth + 1);
      }
    }
    return layers.map((m) => {
      const hooks = [];
      walk(m, new Set(), hooks, 0);
      for (const e of (byId[m.id] || [])) walk(e, new Set(), hooks, 0);
      return { id: m.id, hooks };
    });
  });
  await ctx.close();

  const sending = observed.filter((o) => o.hooks.length).map((o) => o.id).sort();

  // RECONCILE. Every hook body observed at runtime must be findable in the
  // shipped source; one that is not means this probe read something the app
  // does not contain, and no number it produces can be trusted.
  const bodies = new Set();
  for (const o of observed) for (const h of o.hooks) bodies.add(flat(h));
  for (const b of bodies)
    if (!flatSrc.includes(b))
      problem(`${tag}: observed an .atPoint body that is not in the shipped source — ${b.slice(0, 90)}`);

  // A site the source declares but no layer reaches is REPORTED, not absorbed:
  // today that is the engine's own `makeCachedLoader` in the three instances
  // with no Socrata-backed layer. If the two numbers ever meet, every hook the
  // app defines is in use; if a reached one goes quiet, this figure drops and
  // the drift gate below makes someone look.
  const unreached = sites.length - bodies.size;
  if (unreached < 0)
    problem(`${tag}: ${bodies.size} distinct hooks observed against ${sites.length} in the source ` +
            `— a loader is reaching a hook the source does not declare`);

  return {
    layers_sending_point: sending.length,
    layers: sending,
    atpoint_sites: [...sites].sort(),
    atpoint_hooks_reached: bodies.size,
    atpoint_hooks_unreached: Math.max(unreached, 0),
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
              `(${a.atpoint_hooks_reached} of ${a.atpoint_sites.length} .atPoint hooks reached)`);
  if (a.layers_sending_point) console.log(`        ${a.layers.join(", ")}`);
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

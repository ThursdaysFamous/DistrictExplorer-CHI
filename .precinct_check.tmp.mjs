// One-off check of the precinct tranche: route-mock each county's live GIS
// payload (captured minutes ago) and click a point in each county with the
// county-precinct layer on; assert the card names the precinct and, where
// the tranche added it, the polling place / township.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const BASE = "http://localhost:8000/";
const VENDOR = path.resolve("scripts/vendor/leaflet");
const MOCK = "/tmp/claude-0/-home-user-DistrictExplorer-CHI/f8104986-5177-501f-94ce-9c97948b9ae2/scratchpad/mock";

const ROUTES = [
  [/gis\.mcleancountyil\.gov.*PollingPlaces\/MapServer\/1\/query/, "mclean_prec.json"],
  [/gis\.mcleancountyil\.gov.*PollingPlaces\/MapServer\/0\/query/, "mclean_poll.json"],
  [/Logan_County_Districts_and_Zoning\/FeatureServer\/40\/query/, "logan_prec.json"],
  [/ApprovedPrecincts20231012\/FeatureServer\/0\/query/, "sangamon_prec.json"],
  [/ElectionPollingAndPrecincts\/FeatureServer\/0\/query/, "sangamon_poll.json"],
  [/tigerWMS_Census2020\/MapServer\/58\/query/, "carroll_prec.json"],
  [/KaneCo_IL_ElectionsPrecincts\/FeatureServer\/1\/query/, "kane_prec.json"],
  [/KaneCo_IL_Elections_PollingPlaces\/FeatureServer\/1\/query/, "kane_poll.json"],
  [/data\.macoupincountyil\.gov\/resource\/ab79-cnsh/, "macoupin_prec.json"],
  [/data\.macoupincountyil\.gov\/resource\/rc5v-ajnf/, "macoupin_poll.json"],
];

// (lat, lng, county label, extra assertions)
const POINTS = [
  [40.4842, -88.9937, "McLean (Bloomington)", [/Polling place/, /County Board District/]],
  [40.1481, -89.3649, "Logan (Lincoln)", [/Polling place/]],
  [39.7817, -89.6501, "Sangamon (Springfield)", [/Polling place/]],
  [42.0664, -89.9800, "Carroll (Mt. Carroll)", [/Polling place/]],
  [41.8886, -88.3054, "Kane (Geneva)", [/Township/, /Polling place \(/]],
  [39.2778, -89.8818, "Macoupin (Carlinville)", [/Polling place/]],
];

const browser = await chromium.launch();
const context = await browser.newContext({ serviceWorkers: "block" });
const page = await context.newPage();

if (fs.existsSync(VENDOR)) {
  await page.route("**/cdnjs.cloudflare.com/**/leaflet.js", (r) =>
    r.fulfill({ status: 200, contentType: "application/javascript",
      body: fs.readFileSync(path.join(VENDOR, "leaflet.js")) }));
  await page.route("**/cdnjs.cloudflare.com/**/leaflet.css", (r) =>
    r.fulfill({ status: 200, contentType: "text/css",
      body: fs.readFileSync(path.join(VENDOR, "leaflet.css")) }));
}
for (const [pattern, file] of ROUTES) {
  await page.route(pattern, (r) => r.fulfill({
    status: 200, contentType: "application/json",
    body: fs.readFileSync(path.join(MOCK, file)),
  }));
}

let allOk = true;
for (const [lat, lng, label, extras] of POINTS) {
  await page.goto(`${BASE}#point=${lat},${lng}&layers=county-precinct`,
    { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => !!window.ChiExplorer, null, { timeout: 60000 });
  try {
    await page.waitForFunction(() => {
      const el = document.getElementById("card-county-precinct");
      return el && !el.querySelector(".loading-row") &&
        (el.querySelector(".card-flush") || el.querySelector(".state-empty") ||
         el.classList.contains("state-empty") || el.classList.contains("state-error") ||
         el.querySelector(".state-error"));
    }, null, { timeout: 300000 });
  } catch (e) {
    console.log("FAIL " + label + " — card never settled");
    allOk = false;
    continue;
  }
  const res = await page.evaluate(() => {
    const el = document.getElementById("card-county-precinct");
    const block = el && el.closest(".layer-block");
    const pill = block && block.querySelector(".card-id-pill:not([hidden])");
    return {
      text: ((pill ? pill.textContent + " " : "") + (el ? el.innerText : "")).replace(/\s+/g, " ").trim(),
      error: !!(el && (el.classList.contains("state-error") || el.querySelector(".state-error"))),
    };
  });
  let ok = !res.error && /Precinct\s+\S/.test(res.text);
  for (const re of extras) {
    if (!re.test(res.text)) ok = false;
  }
  console.log((ok ? "PASS " : "FAIL ") + label + " | " + res.text.slice(0, 200));
  if (!ok) allOk = false;
}
await browser.close();
process.exit(allOk ? 0 : 1);

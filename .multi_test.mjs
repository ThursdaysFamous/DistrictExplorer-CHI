import { chromium } from "playwright";
const B = "http://localhost:8128/";
const b = await chromium.launch();
const fails = [];
const ok=(n,c,d="")=>{console.log(`  ${c?"PASS":"FAIL"}  ${n}${d?"  — "+d:""}`); if(!c)fails.push(n);};
const ctx = await b.newContext();

async function visit(path){
  const p = await ctx.newPage();
  await p.goto(B+path, {waitUntil:"load"});
  await p.waitForFunction(()=>navigator.serviceWorker.controller!==null||performance.now()>9000,null,{timeout:14000}).catch(()=>{});
  await p.waitForTimeout(2500);
  return p;
}
const keys = async (p)=>p.evaluate(()=>caches.keys());
const scopes = async (p)=>p.evaluate(async()=>(await navigator.serviceWorker.getRegistrations()).map(r=>new URL(r.scope).pathname));

const pil = await visit("il/");
const afterIL = { caches: await keys(pil), scopes: await scopes(pil) };
ok("/il/ registers its own worker", afterIL.scopes.includes("/il/"), JSON.stringify(afterIL.scopes));
ok("/il/ populated a cache", afterIL.caches.some(k=>k.includes("districtry-il")), JSON.stringify(afterIL.caches));

const psf = await visit("sf/");
const afterSF = { caches: await keys(psf), scopes: await scopes(psf) };
ok("/sf/ registers its own worker", afterSF.scopes.includes("/sf/"), JSON.stringify(afterSF.scopes));
ok("/sf/ populated a cache", afterSF.caches.some(k=>k.includes("-sf-")), JSON.stringify(afterSF.caches));
ok("THE KEY ONE: /il/'s cache SURVIVED the /sf/ visit",
   afterSF.caches.some(k=>k.includes("districtry-il")), JSON.stringify(afterSF.caches));

// go back to /il/ and confirm sf's cache survives in turn
const pil2 = await visit("il/");
const back = await keys(pil2);
ok("and /sf/'s cache survives going back to /il/", back.some(k=>k.includes("-sf-")), JSON.stringify(back));
ok("both workers coexist", (await scopes(pil2)).filter(s=>s==="/il/"||s==="/sf/").length===2, JSON.stringify(await scopes(pil2)));

await b.close();
console.log(fails.length?"\nFAILURES: "+fails.join("; "):"\nBoth instances coexist on one origin.");
process.exit(fails.length?1:0);

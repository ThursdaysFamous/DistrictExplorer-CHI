import { chromium } from "playwright";
const BASE = "http://localhost:8126/";
const b = await chromium.launch();
const fails = [];
const ok = (n, c, d="") => { console.log(`  ${c?"PASS":"FAIL"}  ${n}${d?"  — "+d:""}`); if(!c) fails.push(n); };

// 1. bare root redirects to /il/
{ const ctx = await b.newContext(); const p = await ctx.newPage();
  await p.goto(BASE, {waitUntil:"domcontentloaded"});
  await p.waitForURL(u => u.pathname.startsWith("/il/"), {timeout:10000}).catch(()=>{});
  ok("bare / redirects to /il/", new URL(p.url()).pathname === "/il/", p.url()); await ctx.close(); }

// 2. hash permalink survives
{ const ctx = await b.newContext(); const p = await ctx.newPage();
  await p.goto(BASE + "#point=41.88250,-87.62850&layers=ward", {waitUntil:"domcontentloaded"});
  await p.waitForURL(u => u.pathname.startsWith("/il/"), {timeout:10000}).catch(()=>{});
  const u = new URL(p.url());
  ok("hash permalink preserved", u.pathname==="/il/" && u.hash === "#point=41.88250,-87.62850&layers=ward", u.hash); await ctx.close(); }

// 3. query + hash (the embed snippet shape) both survive, query before hash
{ const ctx = await b.newContext(); const p = await ctx.newPage();
  await p.goto(BASE + "?utm_source=embed&utm_medium=iframe#point=41.9,-87.6", {waitUntil:"domcontentloaded"});
  await p.waitForURL(u => u.pathname.startsWith("/il/"), {timeout:10000}).catch(()=>{});
  const u = new URL(p.url());
  ok("query+hash preserved", u.pathname==="/il/" && u.search==="?utm_source=embed&utm_medium=iframe" && u.hash==="#point=41.9,-87.6", u.search+u.hash); await ctx.close(); }

// 4. root SW registers, unregisters itself, and does NOT kill the /il/ worker
{ const ctx = await b.newContext(); const p = await ctx.newPage();
  await p.goto(BASE + "il/", {waitUntil:"load"});
  await p.waitForFunction(() => navigator.serviceWorker.controller !== null || performance.now() > 8000, null, {timeout:12000}).catch(()=>{});
  const before = await p.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).map(r=>r.scope));
  // now simulate an old visitor landing on root (stub runs its cleanup)
  const p2 = await ctx.newPage();
  await p2.goto(BASE, {waitUntil:"domcontentloaded"});
  await p2.waitForURL(u=>u.pathname.startsWith("/il/"), {timeout:10000}).catch(()=>{});
  await p2.waitForTimeout(1500);
  const after = await p2.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).map(r=>r.scope));
  ok("/il/ SW registered", before.some(s=>s.endsWith("/il/")), JSON.stringify(before));
  ok("/il/ SW SURVIVES a root visit", after.some(s=>s.endsWith("/il/")), JSON.stringify(after));
  ok("no root-scope SW left behind", !after.some(s=>new URL(s).pathname==="/"), JSON.stringify(after));
  await ctx.close(); }

await b.close();
console.log(fails.length ? "\nFAILURES: "+fails.join("; ") : "\nAll redirect/SW checks passed.");
process.exit(fails.length ? 1 : 0);

import { chromium } from "playwright";
const B="http://localhost:8129/"; const b=await chromium.launch(); const ctx=await b.newContext();
async function visit(p0){const p=await ctx.newPage();await p.goto(B+p0,{waitUntil:"load"});
  await p.waitForFunction(()=>navigator.serviceWorker.controller!==null||performance.now()>9000,null,{timeout:14000}).catch(()=>{});
  await p.waitForTimeout(2500);return p;}
const pil=await visit("il/"); const a=await pil.evaluate(()=>caches.keys());
const psf=await visit("sf/"); const c=await psf.evaluate(()=>caches.keys());
console.log("  after /il/:", JSON.stringify(a));
console.log("  after /sf/:", JSON.stringify(c));
console.log(c.some(k=>k.includes("districtry-il")) ? "  il cache SURVIVED (bug absent)" : "  il cache WIPED by the /sf/ visit (bug reproduced)");
await b.close();

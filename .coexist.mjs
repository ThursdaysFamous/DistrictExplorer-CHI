import { chromium } from "playwright";
const B="http://localhost:8130/"; const b=await chromium.launch(); const ctx=await b.newContext();
const fails=[]; const ok=(n,c,d="")=>{console.log(`  ${c?"PASS":"FAIL"}  ${n}${d?"  — "+d:""}`);if(!c)fails.push(n);};
async function visit(path,wantCache){
  const p=await ctx.newPage(); await p.goto(B+path,{waitUntil:"load"});
  // wait until this instance's OWN cache exists (not just controller!=null)
  await p.waitForFunction(async(frag)=>{
    const k=await caches.keys(); return k.some(x=>x.includes(frag));
  }, wantCache, {timeout:25000}).catch(()=>{});
  await p.waitForTimeout(1200); return p;
}
const pil=await visit("il/","districtry-il");
const a=await pil.evaluate(()=>caches.keys());
ok("/il/ cached", a.some(k=>k.includes("districtry-il")), JSON.stringify(a));
const psf=await visit("sf/","-sf-");
const c=await psf.evaluate(()=>caches.keys());
ok("/sf/ cached", c.some(k=>k.includes("-sf-")), JSON.stringify(c));
ok("/il/ cache SURVIVES the /sf/ visit", c.some(k=>k.includes("districtry-il")), JSON.stringify(c));
const pil2=await visit("il/","districtry-il");
const d=await pil2.evaluate(()=>caches.keys());
ok("/sf/ cache SURVIVES going back to /il/", d.some(k=>k.includes("-sf-")), JSON.stringify(d));
await b.close();
console.log(fails.length?"\nFAILURES: "+fails.join("; "):"\nBoth instances coexist; neither evicts the other.");
process.exit(fails.length?1:0);

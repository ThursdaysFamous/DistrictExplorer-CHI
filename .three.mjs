import { chromium } from "playwright";
const B="http://localhost:8134/"; const b=await chromium.launch(); const ctx=await b.newContext();
const fails=[]; const ok=(n,c,d="")=>{console.log(`  ${c?"PASS":"FAIL"}  ${n}${d?"  — "+d:""}`);if(!c)fails.push(n);};
async function visit(path,frag){const p=await ctx.newPage();await p.goto(B+path,{waitUntil:"load"});
  await p.waitForFunction(async(f)=>{const k=await caches.keys();return k.some(x=>x.includes(f));},frag,{timeout:30000}).catch(()=>{});
  await p.waitForTimeout(1200);return p;}
const want={il:"districtry-il", sf:"-sf-", nyc:"nyc-district"};
let last;
for (const id of ["il","sf","nyc"]) { last = await visit(id+"/", want[id]);
  const k = await last.evaluate(()=>caches.keys());
  ok(`/${id}/ cached its own`, k.some(x=>x.includes(want[id])), JSON.stringify(k)); }
const finalKeys = await last.evaluate(()=>caches.keys());
const scopes = await last.evaluate(async()=>(await navigator.serviceWorker.getRegistrations()).map(r=>new URL(r.scope).pathname));
ok("ALL THREE caches coexist after visiting all three",
   ["districtry-il","-sf-","nyc-district"].every(f=>finalKeys.some(k=>k.includes(f))), JSON.stringify(finalKeys));
ok("all three workers coexist", ["/il/","/sf/","/nyc/"].every(s=>scopes.includes(s)), JSON.stringify(scopes));
await b.close();
console.log(fails.length?"\nFAILURES: "+fails.join("; "):"\nThree instances, one origin, no eviction.");
process.exit(fails.length?1:0);

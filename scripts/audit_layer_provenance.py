"""Per-layer provenance, derived by FOLLOWING THE CODE.

layer -> its loader name -> that loader's definition -> the dataset it fetches.
Nothing is inferred from proximity; a fact reported here is one the app would
actually request.
"""
import json, os, re, sys

RAW_DIRS = []

def blocks(src):
    out = {}
    for m in re.finditer(r"\bregister[A-Za-z]*\(\s*\{", src):
        i = m.end() - 1
        depth, j = 0, i
        while j < len(src):
            if src[j] == "{": depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        body = src[i:j + 1]
        idm = re.search(r'\bid:\s*["\']([a-z0-9-]+)["\']', body)
        if idm and idm.group(1) not in out:
            out[idm.group(1)] = body
    return out

def fn_body(src, name):
    # `var loadX = makeCached(function () {...})` is the house form, so anchor on
    # the NAME and take the first brace after it — not on a `function` keyword
    # that may sit inside a wrapper call.
    m = re.search(r"(?:function\s+%s\s*\(|(?:var|const|let)\s+%s\s*=)"
                  % (re.escape(name), re.escape(name)), src)
    if not m:
        return ""
    # BOUNDED. `find("{")` with no limit will happily return a brace hundreds of
    # lines later and hand back a body belonging to something else entirely —
    # the same read-past-the-end bug that made the first probe report one host
    # for two unrelated layers. A real body opens within a few characters of the
    # declaration; anything further away is not this function's.
    i = src.find("{", m.end() - 1)
    if i < 0 or i - m.end() > 40:
        return ""
    depth, j = 0, i
    while j < len(src):
        if src[j] == "{": depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0: break
        j += 1
    return src[i:j + 1]

def datasets(text):
    out = []
    for u in re.findall(r'"(https?://[^"]+)"|\'(https?://[^\']+)\'', text):
        u = u[0] or u[1]
        out.append(u)
    for r in re.findall(r'\b([a-z0-9]{4}-[a-z0-9]{4})\b', text):
        out.append("socrata:" + r)
    for f in re.findall(r'data/app/([a-z0-9.-]+\.json)', text):
        out.append("shipped:" + f)
        # A shipped file is a DEAD END unless its upstream is recoverable. It
        # is: the raw pull kept beside the builder is named for the dataset it
        # came from (sf-supervisor-districts-hcgx-vtsb.geojson), so the id that
        # actually produced the geometry is on disk rather than in someone's
        # memory of it.
        stem = f[:-5]
        for d in RAW_DIRS:
            if not os.path.isdir(d):
                continue
            for raw in os.listdir(d):
                rm = re.match(r"(.+)-([a-z0-9]{4}-[a-z0-9]{4})\.(?:geo)?json$", raw)
                if rm and (rm.group(1).endswith(stem) or stem.endswith(rm.group(1))):
                    out.append("upstream:" + rm.group(2))
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); uniq.append(x)
    return uniq

tag = sys.argv[1]
RAW_DIRS[:] = ["%s/data/source/raw" % tag, "data/source/raw"]
src = open("%s/index.html" % tag, encoding="utf-8").read()
ws = json.load(open(("%s/metro-worksheet.json" % tag) if tag != "il" else "metro-worksheet.json"))
B = blocks(src)
report = {}
for l in ws["layers"]:
    lid = l["id"]
    body = B.get(lid, "")
    body_head = ""
    if body:
        k = src.find(body)
        body_head = src[max(0, k - 60):k]
    # ANY key whose name starts with `load`. The first pass matched only
    # `loader:`/`load:` and so reported "no dataset" for every legislative
    # chamber — those use the chamber factory's `loadDistricts:` and
    # `loadRoster:` keys. A layer silently missing from a provenance report is
    # the failure this whole exercise is trying to avoid.
    loaders = re.findall(r"\b(load[A-Za-z]*|loader)\s*:\s*([A-Za-z_$][\w$]*)", body)
    loaders = [n for _k, n in loaders]
    ev = []
    # A factory may take its dataset as a PROPERTY rather than a loader —
    # `registerNycZone({ id: "hs-zone", datasetId: "ruu9-egea" })` — in which
    # case there is no load* key to follow and the id is sitting in plain sight.
    for did in re.findall(r'\bdatasetId:\s*["\']([a-z0-9]{4}-[a-z0-9]{4})["\']', body):
        ev.append(("datasetId", "socrata:" + did))
    # An INLINE factory call in the loader slot — `loader: makeCachedLoader("pri4-ifjk")`
    # — never names a function to follow, so the id has to be read where it is
    # written. Reported as "derived-by:registerPolygonLayer" until this hop
    # existed, which is a non-answer dressed as one.
    for did in re.findall(r'\b(?:loader|load)\s*:\s*[A-Za-z_$][\w$]*\(\s*["\']([a-z0-9]{4}-[a-z0-9]{4})["\']', body):
        ev.append(("inline-factory", "socrata:" + did))
    # And a factory may DERIVE its geometry from another layer's — the borough
    # office layers draw the borough boundaries and differ only by role. Record
    # what they actually reuse rather than reporting nothing.
    fm = re.search(r"\bregister([A-Za-z]+)\(", body_head or "")
    for fn in dict.fromkeys(loaders):
        body_fn = fn_body(src, fn)
        # A loader is often a one-liner that hands a Socrata id to a factory —
        # `var loadX = makeCachedLoader("rwdu-9wb2")` — in which case there is no
        # brace body to read at all. Take the whole declaration line instead.
        if not body_fn:
            # To the terminating `;`, NOT to end-of-line: a factory call is
            # often written across several lines with the dataset id on the
            # second, which a line-bounded read reports as "no dataset found"
            # while the id sits one line below.
            m = re.search(r"(?:var|const|let)\s+%s\s*=[\s\S]{0,600}?;" % re.escape(fn), src)
            body_fn = m.group(0) if m else ""
        # One more hop: a loader that builds its url from a named constant
        # (USGS_POST_OFFICE_LAYER) names the constant, not the endpoint. Resolve
        # any ALL-CAPS identifier it mentions to that constant's own value.
        for const in set(re.findall(r"\b([A-Z][A-Z0-9_]{4,})\b", body_fn)):
            cm = re.search(r"\b%s\s*=\s*[\"\'](https?://[^\"\']+)[\"\']" % re.escape(const), src)
            if cm:
                # QUOTED: datasets() reads url literals out of quotes, so a
                # bare append is invisible to it — the resolution worked and
                # the result was dropped one line later.
                body_fn += '\n"%s"' % cm.group(1)
        found = datasets(body_fn)
        if not found:
            # One level deeper: a loader that only composes OTHER loaders
            # (Promise.all([loadNysedLayerPaged(2, ...), ...])) holds no dataset
            # of its own. Follow the helpers it calls rather than reporting the
            # layer as sourceless.
            for helper in dict.fromkeys(re.findall(r"\b(load[A-Za-z]\w*)\s*\(", body_fn)):
                if helper == fn:
                    continue
                hb = fn_body(src, helper)
                if not hb:
                    hm = re.search(r"(?:var|const|let)\s+%s\s*=[\s\S]{0,600}?;" % re.escape(helper), src)
                    hb = hm.group(0) if hm else ""
                for const in set(re.findall(r"\b([A-Z][A-Z0-9_]{4,})\b", hb)):
                    cm = re.search(r"\b%s\s*=\s*[\"\'](https?://[^\"\']+)[\"\']" % re.escape(const), src)
                    if cm:
                        hb += '\n"%s"' % cm.group(1)
                found += datasets(hb)
        ev += [(fn, d) for d in found]
    factory = fm.group(1) if fm else ""
    if not ev and factory:
        ev.append(("factory", "derived-by:register" + factory))
    report[lid] = {"loaders": list(dict.fromkeys(loaders)), "factory": factory, "datasets": ev}
    top = [d for _, d in ev if not d.startswith("socrata:") or True][:2]
    print("%-26s loaders=%-38s %s" % (lid, ",".join(report[lid]["loaders"])[:36] or "—",
                                      " | ".join(x[:64] for x in top) or "— (no dataset found)"))
json.dump(report, open("/tmp/claude-0/-home-user-DistrictExplorer-CHI/d70aac26-6aa4-5bcc-adce-8e7004651d1f/scratchpad/prov-%s.json" % tag, "w"), indent=1)

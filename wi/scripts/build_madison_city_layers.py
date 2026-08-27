#!/usr/bin/env python3
"""
Build the three Madison city-scoped files for phase 4 PR 4
(docs/WI_PHASE4_PLAN.md — the tid-district layer's SECOND city, plus the
registered-association layer and the coverage outline both ride on):

  data/app/madison-tid-districts.json      the city's ACTIVE Tax
                                           Incremental Districts, 14 at
                                           first build (TID 36-54)
  data/app/madison-neighborhood-assocs.json  the city's 116 ACTIVE
                                           registered associations
  data/app/madison-outline.json            the city's corporate limits,
                                           dissolved from the city's OWN
                                           ward fabric — madisonCoverage's
                                           ground

LICENCE (step zero, captured 2026-08-27): the layers publish through the
city's open-data program (data-cityofmadison.opendata.arcgis.com
catalogues Public/OPEN_DATA and Public/OPEN_DATA_PLANNING); the city's
Data Policy (cityofmadison.com/policy/data) is a reference-use disclaimer
— no warranty, no redistribution ban, IP claims only where a page "will
so indicate", and these layers indicate only the attribution line "City
of Madison, Wisconsin", which sources.html carries.

THE TIF BUILD IS A THREE-SURFACE AGREEMENT, because the first measurement
(2026-08-27) found the city's two surfaces disagreeing three ways and the
state settling every case:

  * the GIS layer (OPEN_DATA_PLANNING/8) holds 25 rows of TWO CONCEPTS:
    16 district polygons and 9 "half-mile rule" planning buffers, all
    TIF_STATUS 'A' — HALFMILERULE is the flag that separates them, and a
    status filter alone would ship buffers as districts (one buffer even
    carries a real TIF_NO, 39). The Milwaukee status-flag lesson evolves
    here: the flag that matters is the one separating CONCEPTS.
  * the city's own TIF program page (Economic Development) lists districts
    the layer does not know about and vice versa: the layer carries TID 39
    and 47, which the program page omits; the page carries TID 55 (Voit
    Farm), which the layer has not drawn.
  * Wisconsin DOR's certified annual Active-TID workbook (tid100wi-<year>)
    is the authority, and it agrees with the PROGRAM PAGE exactly: 15
    active City of Madison TIDs — 39 and 47 CLOSED (early, their
    unexpired max-life dates in the layer notwithstanding: TIDs routinely
    terminate ahead of schedule, which is why a date is never the filter),
    55 ACTIVE with no published geometry.

  So the shipped set is layer ∩ DOR — 14 districts — with the two stale
  layer rows DROPPED against a pinned list (a new stale row fails the
  build for a human look) and TID 55 recorded as the data-quality gap
  `madison-tid-undrawn` rather than silently absent: a reader inside
  Voit Farm would otherwise be told they are in no TID, which is false.
  Display names come from the program page (the department that runs the
  program; the layer spells TID 50 "State St" where the program says
  "State and Lake", and calls TID 54 "TID 54 Northside" where the program
  says "Pennsylvania Ave"); the layer's own TIF_NAME ships as NAME_RAW.
  CREATED is DOR's certified Base Yr (the layer's CREATION_DATE is null
  for the three newest districts).

THE ASSOCIATION LAYER COLLECTS OVERLAPS BY DESIGN: the city registers
neighborhood, condominium, resident, homeowners, business and
property-owners associations in ONE layer, and they genuinely nest —
five condo/resident polygons sit wholly inside a neighborhood
association's, one business association is 95% inside another, and two
neighborhood associations overlap each other (measured 2026-08-27). The
app module therefore collects EVERY containing feature (the NG911
pattern), and this builder ships each feature's CLASSIFICA so the card
can say what kind of association each row is. Only STATUS 'Active' rows
ship (116 of 141 — the city's own flag; the 25 Inactive are lapsed
registrations). Names carry trailing whitespace in the source and are
trimmed with the raw value kept.

THE OUTLINE IS THE CITY'S OWN FABRIC: madisonCoverage needs the corporate
limits, and the city's ward layer (OPEN_DATA/11) tiles the city exactly —
its union IS the boundary, enclaves (Maple Bluff, Shorewood Hills, town
islands) excluded as holes. Dissolved with shapely's unary_union and
lightly simplified for the small coverage file.

An OPERATOR rebuild; the monthly source report watches the endpoints and
WATCH.md carries the DOR annual-edition trigger.
"""

import io
import json
import os
import re
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA = os.path.join(REPO_ROOT, "data", "app")

BASE = "https://maps.cityofmadison.com/arcgis/rest/services/Public"
TIF_LAYER = BASE + "/OPEN_DATA_PLANNING/MapServer/8"
NA_LAYER = BASE + "/OPEN_DATA/MapServer/12"
WARD_LAYER = BASE + "/OPEN_DATA/MapServer/11"
PROGRAM_PAGE = "https://www.cityofmadison.com/dpced/economic-development/tif"
DOR_XLSX = "https://www.revenue.wi.gov/SLFReportstif/tid100wi-%d.xlsx"

# Layer rows that are NOT active districts, each pinned with the reason.
# A drop this list does not name fails the build — a newly-stale layer row
# gets a human look, never a silent drop.
KNOWN_CLOSED_IN_LAYER = {
    "39": "closed per DOR and the city's program page; the layer still draws it",
    "47": "closed per DOR and the city's program page; the layer still draws it",
}
# Active districts the layer has not drawn — recorded as the gap
# madison-tid-undrawn, printed every build, and expected to EMPTY when the
# city draws them (at which point this pin fails the build so the gap
# record gets retired in the same change).
KNOWN_UNDRAWN = {"55"}

MADISON_BBOX = (-89.65, 42.95, -89.15, 43.25)  # lng/lat envelope, sanity gate


def fetch(url, tries=6, timeout=120):
    last = None
    for _ in range(tries):
        try:
            return subprocess.run(
                ["curl", "-sSL", "--fail", "--max-time", str(timeout),
                 "-H", "User-Agent: districtry/1.0 (+https://districtry.com/wi/)",
                 url],
                check=True, capture_output=True).stdout
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise last


def fetch_geojson(layer, out_fields="*"):
    url = (layer + "/query?where=1%3D1&outFields=" + out_fields
           + "&outSR=4326&f=geojson")
    doc = json.loads(fetch(url))
    if doc.get("type") != "FeatureCollection" or not doc.get("features"):
        raise SystemExit("%s did not answer a FeatureCollection" % layer)
    return doc


def check_bbox(features, what):
    for f in features:
        stack = [f["geometry"]["coordinates"]]
        while stack:
            v = stack.pop()
            if isinstance(v[0], (int, float)):
                lng, lat = v[0], v[1]
                if not (MADISON_BBOX[0] < lng < MADISON_BBOX[2]
                        and MADISON_BBOX[1] < lat < MADISON_BBOX[3]):
                    raise SystemExit(
                        "%s: coordinate (%s, %s) outside the Madison envelope "
                        "— outSR ignored?" % (what, lng, lat))
            else:
                stack.extend(v)


def program_page_tids():
    """The Economic Development page's 'Current TIF Plans and Maps' set —
    {number: name}. The accordion lists one 'TID <n> - <name>' heading per
    current district."""
    html = fetch(PROGRAM_PAGE).decode("utf-8", "replace")
    import html as html_mod
    text = html_mod.unescape(html)
    pairs = {}
    for m in re.finditer(r"TID\s+(\d+)\s*[-–]\s*([^<]{2,60}?)\s*(?=<)", text):
        no, name = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        pairs.setdefault(no, name)
    if len(pairs) < 10:
        raise SystemExit("program page yielded only %d TID headings — its "
                         "markup moved; re-measure" % len(pairs))
    return pairs


def dor_active_madison():
    """Wisconsin DOR's certified Active-TID workbook: the City of Madison
    rows of the newest published edition. Returns {tid_no: base_year}."""
    year = date.today().year
    raw = None
    for y in (year, year - 1):
        try:
            raw = fetch(DOR_XLSX % y)
            got_year = y
            break
        except Exception:
            continue
    if raw is None:
        raise SystemExit("no DOR active-TID workbook found for %d or %d"
                         % (year, year - 1))
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(io.BytesIO(raw))
    ss = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall(M + "si"):
        ss.append("".join(t.text or "" for t in si.iter(M + "t")))
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    out = {}
    for row in sheet.iter(M + "row"):
        vals = {}
        for c in row:
            col = re.match(r"[A-Z]+", c.get("r")).group(0)
            v = c.find(M + "v")
            if v is None:
                continue
            val = v.text
            if c.get("t") == "s":
                val = ss[int(val)]
            vals[col] = val
        # columns: A CoMun, B County, C TVC, D Municipality, E TID, G Base Yr
        if ((vals.get("D") or "").strip() == "MADISON"
                and (vals.get("C") or "").strip() == "CITY"
                and (vals.get("B") or "").strip() == "DANE"):
            out[(vals.get("E") or "").strip()] = (vals.get("G") or "").strip()
    if len(out) < 5:
        raise SystemExit("DOR %d workbook yielded only %d Madison rows — its "
                         "column layout moved; re-measure" % (got_year, len(out)))
    print("DOR %d edition: %d active City of Madison TIDs" % (got_year, len(out)),
          file=sys.stderr)
    return out


def build_tif():
    doc = fetch_geojson(TIF_LAYER,
                        "TIF_NO,TIF_NAME,TIF_STATUS,HALFMILERULE")
    feats = doc["features"]
    # HALFMILERULE separates the layer's two concepts: 0 = district, 1 =
    # planning buffer. Only the flag decides — see the docstring.
    districts = [f for f in feats if f["properties"].get("HALFMILERULE") == 0]
    buffers = len(feats) - len(districts)
    layer_nos = {}
    for f in districts:
        no = str(f["properties"].get("TIF_NO") or "")
        if not no or no == "0":
            raise SystemExit("a HALFMILERULE=0 row carries no TIF_NO — the "
                             "concept flag no longer separates the layer")
        if no in layer_nos:
            raise SystemExit("TID %s appears twice among HALFMILERULE=0 rows" % no)
        if (f["properties"].get("TIF_STATUS") or "").strip() != "A":
            raise SystemExit("TID %s is not status A in the layer" % no)
        layer_nos[no] = f

    program = program_page_tids()
    dor = dor_active_madison()

    # the two authorities of record must agree with each other exactly
    if set(program) != set(dor):
        raise SystemExit(
            "the city's TIF program page and DOR's active list disagree "
            "(page-only: %s; DOR-only: %s) — re-measure before shipping"
            % (sorted(set(program) - set(dor)), sorted(set(dor) - set(program))))

    stale = set(layer_nos) - set(dor)
    if stale != set(KNOWN_CLOSED_IN_LAYER):
        raise SystemExit(
            "layer-only TIDs %s do not match the pinned closed list %s — a "
            "district closed (or reopened) since the last measurement; "
            "re-verify against DOR and update the pin"
            % (sorted(stale), sorted(KNOWN_CLOSED_IN_LAYER)))
    undrawn = set(dor) - set(layer_nos)
    if undrawn != KNOWN_UNDRAWN:
        raise SystemExit(
            "active TIDs missing from the layer %s do not match the pinned "
            "undrawn list %s — the city drew (or dropped) geometry; update "
            "the pin AND the madison-tid-undrawn gap record in the same change"
            % (sorted(undrawn), sorted(KNOWN_UNDRAWN)))
    for no, reason in KNOWN_CLOSED_IN_LAYER.items():
        print("dropping layer TID %s: %s" % (no, reason), file=sys.stderr)
    for no in sorted(KNOWN_UNDRAWN):
        print("TID %s (%s) is ACTIVE per DOR and the program page but has no "
              "published geometry — gap madison-tid-undrawn" % (no, program[no]),
              file=sys.stderr)

    out_feats = []
    renames = []
    for no in sorted((set(layer_nos) & set(dor)), key=int):
        f = layer_nos[no]
        raw_name = re.sub(r"\s+", " ", str(f["properties"].get("TIF_NAME") or "")).strip()
        name = program[no]
        if raw_name and raw_name.lower() != name.lower():
            renames.append((no, raw_name, name))
        props = {"TID": no, "NAME": name, "CREATED": dor[no], "CITY": "Madison"}
        if raw_name and raw_name != name:
            props["NAME_RAW"] = raw_name
        out_feats.append({"type": "Feature", "properties": props,
                          "geometry": f["geometry"]})
    check_bbox(out_feats, "madison-tid-districts")
    if len(out_feats) < 12:
        raise SystemExit("only %d Madison TIDs survived the gates — floor 12"
                         % len(out_feats))
    for no, raw, cur in renames:
        print("TID %s ships the program page's name %r (layer says %r)"
              % (no, cur, raw), file=sys.stderr)
    return ({"type": "FeatureCollection", "features": out_feats},
            len(feats), buffers)


def build_na():
    doc = fetch_geojson(NA_LAYER, "NA_ID,NEIGHB_NAME,STATUS,CLASSIFICA,Web")
    feats = doc["features"]
    out_feats = []
    classes = {}
    for f in feats:
        p = f["properties"]
        if (p.get("STATUS") or "").strip() != "Active":
            continue
        name = re.sub(r"\s+", " ", str(p.get("NEIGHB_NAME") or "")).strip()
        cls = re.sub(r"\s+", " ", str(p.get("CLASSIFICA") or "")).strip()
        web = (p.get("Web") or "").strip()
        if not name or not cls:
            raise SystemExit("an Active association row lacks a name or "
                             "classification (NA_ID %s)" % p.get("NA_ID"))
        if web and not web.startswith("https://www.cityofmadison.com/"):
            raise SystemExit("association %r links %r — not the city's own "
                             "profile pattern; re-measure" % (name, web))
        classes[cls] = classes.get(cls, 0) + 1
        props = {"NAME": name, "CLASS": cls, "CITY": "Madison"}
        if web:
            props["WEB"] = web
        out_feats.append({"type": "Feature", "properties": props,
                          "geometry": f["geometry"]})
    check_bbox(out_feats, "madison-neighborhood-assocs")
    if len(out_feats) < 100:
        raise SystemExit("only %d Active associations — floor 100 (the city "
                         "registered 116 at first build)" % len(out_feats))
    print("associations by class: %s"
          % ", ".join("%s %d" % kv for kv in sorted(classes.items())),
          file=sys.stderr)
    return {"type": "FeatureCollection", "features": out_feats}, len(feats)


def build_outline():
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    doc = fetch_geojson(WARD_LAYER, "WARD")
    n = len(doc["features"])
    if n < 100:
        raise SystemExit("only %d city wards — the fabric shrank, re-measure" % n)
    union = unary_union([shape(f["geometry"]) for f in doc["features"]])
    union = union.simplify(0.0002)
    if union.geom_type == "Polygon":
        parts = 1
    elif union.geom_type == "MultiPolygon":
        parts = len(union.geoms)
    else:
        raise SystemExit("wards union is a %s, not a polygon" % union.geom_type)
    feat = {"type": "Feature",
            "properties": {"NAME": "City of Madison",
                           "SOURCE": "union of the city's own ward fabric "
                                     "(Public/OPEN_DATA/MapServer/11)"},
            "geometry": mapping(union)}
    check_bbox([feat], "madison-outline")
    print("madison-outline: %d ward(s) dissolved to %d part(s)" % (n, parts),
          file=sys.stderr)
    return {"type": "FeatureCollection", "features": [feat]}


def main():
    tif, tif_rows, tif_buffers = build_tif()
    na, na_rows = build_na()
    outline = build_outline()
    for fname, doc in (("madison-tid-districts.json", tif),
                       ("madison-neighborhood-assocs.json", na),
                       ("madison-outline.json", outline)):
        path = os.path.join(APP_DATA, fname)
        with open(path, "w") as f:
            json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
            f.write("\n")
        print("wrote %s — %d feature(s)" % (os.path.relpath(path, REPO_ROOT),
                                            len(doc["features"])),
              file=sys.stderr)
    print("madison city tier: %d of %d TIF rows ship (%d half-mile buffers "
          "and %d stale district rows dropped, %d active district undrawn), "
          "%d of %d association rows ship (Active only), outline from the "
          "city's own wards" % (len(tif["features"]), tif_rows, tif_buffers,
                                len(KNOWN_CLOSED_IN_LAYER), len(KNOWN_UNDRAWN),
                                len(na["features"]), na_rows),
          file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Ship library-district boundaries for six Illinois counties that publish none.

WHOSE BOUNDARY THIS IS, AND WHY THAT SENTENCE COMES FIRST. The source is the
Illinois Broadband Office / Connected Nation `IL_Boundary_Layers` service,
layer 11 "Library Districts" — 642 polygons for the whole state, public and
token-free. The publisher is a BROADBAND CONTRACTOR, not a county and not the
districts: `copyrightText` is empty, the item description is empty, the layer
is not named in its own service documentation, and every attribute besides
`Library` and `LibraryType` is a broadband service metric. That is a real
published boundary with a weak provenance line, which under this project's
rules is an operator decision rather than a default; it was recorded in
docs/DATA_LAYER_GUIDEBOOK.md's backlog on 2026-08-20, measured further on
2026-09-04, and the decision to ship was taken 2026-09-05. Every card built on
this file NAMES the publisher, because a reader is entitled to know that the
line they are being shown was drawn by a broadband planner rather than filed
by the library.

WHAT MAKES IT TRUSTWORTHY IS THAT IT IS RIGHT WHERE SOMEONE ELSE'S RECORD SAYS
IT SHOULD BE, and this builder GATES on that rather than describing it:

  * CARROLL IS THE WITNESS. The county Clerk's own tax report names seven
    library tax lines — Savanna, Mount Carroll, Chadwick, Milledgeville, York
    Township, Lanark and Pearl City — recorded in this repo's own gap record
    before this layer was found. The layer returns exactly those seven, and
    the builder REFUSES TO WRITE if it ever stops doing so. The eighth polygon
    touching Carroll is a 0.01 km2 sliver of Hanover Township Library, whose
    body sits in Jo Daviess.
  * IT IS RIGHT ON THE NEGATIVES, which is the check a wrong layer fails.
    Shannon village and Lake Carroll land in NO library district, and the
    Clerk's tax codes independently agree that Shannon's code carries no
    library line. Both are probes below.
  * BOONE IS THE SECOND WITNESS AND IS NOT BUILT HERE. Boone's own library
    boundaries ship from the county's tax roll (build_parcel_fabric_districts.py),
    so it is a control rather than a customer: the two publishers name the same
    three bodies, and the contractor's polygons agree with the county's at
    60-85% IoU. Its `City` typing of Ida Public Library is CORRECT and the
    county proves it — Ida's 18 tax codes (LYBV) are identical to the City of
    Belvidere's (VCBV), so Ida is a municipal library whose area is the city.

THE TYPE IS SHIPPED, NOT HIDDEN. `LibraryType` is the real Illinois governance
vocabulary — District, City, Village, Township, Town, and two `(contracting)`
variants — and the distinction matters to a reader: a library DISTRICT is a
taxing body you live inside, while a municipal library's boundary is simply
the municipality and it levies nothing of its own. A layer compiled only for
broadband arithmetic would not need to separate them.

CLIPPED TO THE COUNTY, DELIBERATELY. Each entry is county-scoped, so its
overlay should draw what the entry speaks for. No ground loses an answer: a
district straddling a county line ships its slice in EACH county's file, so
Pearl City appears in both Carroll's and Stephenson's and a reader on either
side is answered. What clipping avoids is one polygon shipped six times and an
overlay that draws a district into a county this entry does not gate.

Usage:
    python3 scripts/build_statewide_library_districts.py
    python3 scripts/build_statewide_library_districts.py --check
"""

import argparse
import json
import os
import sys

import requests
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(os.path.dirname(HERE), "il", "data", "app")

SERVICE = ("https://services.arcgis.com/R0IGaIgf2sox9aCY/arcgis/rest/services/"
           "IL_Boundary_Layers/FeatureServer/11")
SOURCE_LABEL = "Illinois Broadband Office / Connected Nation"
PAGE = 2000                  # the service's own maxRecordCount
MIN_STATEWIDE = 600          # 642 today; a floor, not an equality — the
                             # publisher may add a library without breaking us
SIMPLIFY_M = 5.0             # invisible at any zoom this map allows. 10 m was
                             # tried first and rejected on measurement: it ate 3.7%
                             # of Pearl City's Carroll slice, which is a long thin
                             # reach over the county line and exactly the shape a
                             # coarse tolerance destroys. 5 m costs ~40 KB across
                             # the six files and keeps every district inside the
                             # retention gate.

# A BORDER SLIVER IS RULED OUT BY SHAPE, NOT BY AREA, and that distinction was
# forced by measurement rather than chosen. Two independently drawn layers — a
# contractor's library polygon and the census county outline — disagree by tens
# of metres along a shared county line, which manufactures thin intersections
# that are not reach into the county. Sorting the six counties' intersections by
# AREA gives no natural break at all: they run continuously from 257 m2 upward,
# so any area floor is a number picked to make some gate pass. Sorting them by
# how far they reach INWARD from the county line splits them cleanly. Exactly
# three never reach 10 m inside — Winnebago PLD in Stephenson (257 m2),
# Farmersville-Waggoner in Sangamon (3,444 m2) and Hanover Township in Carroll
# (11,806 m2), each a body seated in a neighbouring county — and every other
# intersection reaches at least 10 m in. Ten metres is the simplification
# tolerance, i.e. the resolution below which this file makes no claim anyway.
SLIVER_REACH_M = 10.0

# Simplification eats a larger FRACTION of a small high-perimeter shape than of
# a large one, so a bare fraction test fires on a sliver while missing a real
# loss on a big district. Fail only when the fraction AND the absolute area both
# say real ground went missing — the rule build_parcel_fabric_districts.py
# already carries for the same reason.
MIN_AREA_RETAINED = 0.98
MIN_AREA_LOST_M2 = 25000.0

DEG = 1.0 / 111320.0
M2_PER_DEG2 = (111320.0 ** 2) * 0.766   # ~40.5N; used only for the sliver floor

# Carroll's seven, from the County Clerk's own Tax Code by District Listing as
# recorded in this repo's gap record BEFORE this layer was found. This is the
# gate, not a comment: if the layer stops returning exactly these, the build
# stops.
CARROLL_CLERK_LIBRARIES = {
    "Savanna Public Library District",
    "Mount Carroll District Library",
    "Chadwick Public Library District",
    "Milledgeville Public Library",
    "York Township Public Library",
    "Lanark Public Library",
    "Pearl City Public Library District",
}

# Each probe is (lat, lng, expected library or None). The negatives matter more
# than the positives: a layer that covers everything would pass every positive.
COUNTIES = [
    {"slug": "carroll", "label": "Carroll County", "expect": 7,
     "clerk_names": CARROLL_CLERK_LIBRARIES,
     "probes": [(42.0942, -89.9787, "Mount Carroll District Library"),
                (42.1522, -89.7401, None),   # Shannon village — the Clerk's
                (42.1631, -89.8664, None)]}, # tax codes agree: no library line
    {"slug": "lee", "label": "Lee County", "expect": 11,
     "probes": [(41.8389, -89.4795, "Dixon Public Library"),
                (41.7114, -89.3290, "Pankhurst Memorial Library")]},
    {"slug": "randolph", "label": "Randolph County", "expect": 9,
     "probes": [(37.9134, -89.8221, "Chester Public Library"),
                (38.1236, -89.7018, "Sparta Public Library")]},
    {"slug": "sangamon", "label": "Sangamon County", "expect": 16,
     "probes": [(39.7817, -89.6501, "Lincoln Library"),
                (39.6739, -89.7018, "Chatham Area Public Library District")]},
    {"slug": "st-clair", "label": "St. Clair County", "expect": 19,
     "probes": [(38.5200, -89.9840, "Belleville Public Library"),
                (38.5706, -90.1798, "Cahokia Public Library District")]},
    {"slug": "stephenson", "label": "Stephenson County", "expect": 5,
     "probes": [(42.2967, -89.6212, "Freeport Public Library"),
                (42.3792, -89.8226, "Lena Community District Library")]},
]


def fail(msg):
    print("build-statewide-library-districts: FAIL — " + msg, file=sys.stderr)
    sys.exit(1)


def clean(g):
    """Repair a geometry and keep only its polygonal parts."""
    if not g.is_valid:
        g = make_valid(g)
    if not g.is_valid:
        g = g.buffer(0)
    if g.geom_type == "GeometryCollection":
        polys = [p for p in g.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        g = unary_union(polys) if polys else g
    return g


def fetch_layer():
    """Every page, refusing rather than truncating.

    The service caps at 2,000 and flags `exceededTransferLimit` on a 200, which
    is the same silent-truncation shape the USGS structures loader shipped with
    for weeks. 642 fits in one page today; the paging is here so that stops
    being load-bearing.
    """
    feats, offset = [], 0
    while True:
        page = requests.get(SERVICE + "/query", params={
            "where": "1=1", "outFields": "Library,LibraryType", "outSR": 4326,
            "f": "geojson", "geometryPrecision": 6,
            "resultRecordCount": PAGE, "resultOffset": offset,
        }, timeout=300).json()
        got = page.get("features") or []
        feats += got
        more = page.get("exceededTransferLimit") or \
            (page.get("properties") or {}).get("exceededTransferLimit")
        if not (more and got):
            break
        offset += len(got)
    if len(feats) < MIN_STATEWIDE:
        fail("statewide layer returned %d features, expected at least %d"
             % (len(feats), MIN_STATEWIDE))
    return feats


def county_outline(slug):
    path = os.path.join(APP_DIR, "%s-county-outline.json" % slug)
    if not os.path.exists(path):
        fail("no shipped outline for %s (%s)" % (slug, path))
    with open(path, encoding="utf-8") as fh:
        return clean(unary_union([shape(f["geometry"])
                                  for f in json.load(fh)["features"]]))


def build_county(cfg, libs, tree, verbose=True):
    outline = county_outline(cfg["slug"])
    inland = outline.boundary.buffer(SLIVER_REACH_M * DEG)
    kept, dropped = [], []
    for idx in tree.query(outline):
        name, ltype, geom = libs[idx]
        if not geom.intersects(outline):
            continue
        clip = clean(geom.intersection(outline))
        if clip.is_empty or clip.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        m2 = clip.area * M2_PER_DEG2
        if clean(clip.difference(inland)).is_empty:
            dropped.append((name, m2))
            continue
        if not name or not str(name).strip():
            fail("%s: a polygon has no Library name" % cfg["slug"])
        if not ltype or not str(ltype).strip():
            # one untyped row exists statewide (Sandoval Public Library); it is
            # named rather than silently shipped with a blank governance type
            print("  NOTE %s: %r has no LibraryType and ships without one"
                  % (cfg["slug"], name))
        simple = clip.simplify(SIMPLIFY_M * DEG, preserve_topology=True)
        if simple.is_empty or simple.geom_type not in ("Polygon", "MultiPolygon"):
            simple = clip
        lost_m2 = (clip.area - simple.area) * M2_PER_DEG2
        if simple.area < MIN_AREA_RETAINED * clip.area and lost_m2 > MIN_AREA_LOST_M2:
            fail("%s: simplifying %r lost %.1f%% of its area (%.0f m2)"
                 % (cfg["slug"], name, 100.0 * (1 - simple.area / clip.area), lost_m2))
        kept.append((str(name).strip(), (str(ltype).strip() if ltype else None), simple))

    kept.sort(key=lambda k: k[0])
    if len(kept) != cfg["expect"]:
        fail("%s: %d libraries, expected %d (got: %s)"
             % (cfg["slug"], len(kept), cfg["expect"], [k[0] for k in kept]))

    # THE CLERK GATE. Only Carroll has a county-published list to check against,
    # and it is the reason this source is trusted at all — so it is enforced
    # rather than remembered.
    if cfg.get("clerk_names"):
        got = {n for n, _, _ in kept}
        if got != cfg["clerk_names"]:
            fail("%s: the layer no longer matches the County Clerk's own tax "
                 "lines. missing %s; unexpected %s"
                 % (cfg["slug"], sorted(cfg["clerk_names"] - got), sorted(got - cfg["clerk_names"])))

    # Separate service areas must not overlap each other inside one county.
    for i, (na, _, ga) in enumerate(kept):
        for nb, _, gb in kept[i + 1:]:
            if not ga.intersects(gb):
                continue
            ov = clean(ga.intersection(gb)).area * M2_PER_DEG2
            if ov > MIN_AREA_LOST_M2:
                fail("%s: %r and %r overlap by %.0f m2 — two library service "
                     "areas cannot both contain the same ground" % (cfg["slug"], na, nb, ov))

    feats = []
    for name, ltype, geom in kept:
        gm = json.loads(json.dumps(mapping(geom)))

        def rnd(c):
            return round(c, 5) if isinstance(c, (int, float)) else [rnd(x) for x in c]
        gm["coordinates"] = rnd(gm["coordinates"])
        props = {"library": name}
        if ltype:
            props["type"] = ltype
        feats.append({"type": "Feature", "properties": props, "geometry": gm})
    fc = {"type": "FeatureCollection", "features": feats}

    for lat, lng, want in cfg["probes"]:
        pt = Point(lng, lat)
        hits = [f["properties"]["library"] for f in feats
                if shape(f["geometry"]).contains(pt)]
        got = hits[0] if hits else None
        if verbose:
            print("  probe %.4f,%.4f -> %-40s [%s]"
                  % (lat, lng, got or "no library district", "ok" if got == want else "FAIL"))
        if got != want:
            fail("%s: probe %.4f,%.4f expected %r, got %r"
                 % (cfg["slug"], lat, lng, want, got))

    if verbose and dropped:
        print("  border slivers dropped (never reach %.0f m inside the county; "
              "each body is seated in a neighbouring county): %s"
              % (SLIVER_REACH_M, ", ".join("%s %.0f m2" % (n, m) for n, m in dropped)))
    return fc


def run(check):
    feats = fetch_layer()
    print("build-statewide-library-districts: %d polygons from %s layer 11 (%s)"
          % (len(feats), "IL_Boundary_Layers", SOURCE_LABEL))
    libs = []
    for f in feats:
        if not f.get("geometry"):
            continue
        g = clean(shape(f["geometry"]))
        if g.is_empty or g.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        libs.append((f["properties"].get("Library"),
                     f["properties"].get("LibraryType"), g))
    tree = STRtree([g for _, _, g in libs])

    stale = []
    for cfg in COUNTIES:
        print("%s:" % cfg["slug"])
        fc = build_county(cfg, libs, tree)
        payload = json.dumps(fc, separators=(",", ":"))
        out = os.path.join(APP_DIR, "%s-library-districts.json" % cfg["slug"])
        types = sorted({f["properties"].get("type") or "(untyped)" for f in fc["features"]})
        if check:
            if not os.path.exists(out):
                stale.append(cfg["slug"] + " (missing)")
            else:
                with open(out, encoding="utf-8") as fh:
                    if fh.read() != payload:
                        stale.append(cfg["slug"])
            print("  %d libraries (%s)" % (len(fc["features"]), ", ".join(types)))
        else:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(payload)
            print("  wrote data/app/%s-library-districts.json (%d libraries, %.0f KB; %s)"
                  % (cfg["slug"], len(fc["features"]), len(payload) / 1024.0, ", ".join(types)))
    if check:
        if stale:
            fail("shipped file(s) differ from a fresh build: " + ", ".join(stale))
        print("build-statewide-library-districts: OK — all %d shipped file(s) match "
              "a fresh build of the published layer" % len(COUNTIES))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare against the shipped files")
    run(ap.parse_args().check)


if __name__ == "__main__":
    main()

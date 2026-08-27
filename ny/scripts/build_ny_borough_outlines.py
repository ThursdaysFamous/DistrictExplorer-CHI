#!/usr/bin/env python3
"""
Build data/app/<slug>-county-outline.json for New York City's five boroughs —
the per-borough containment tests the Data gaps panel uses to lead with the
gaps that apply WHERE THE READER CLICKED.

WHY THIS EXISTS, AND WHAT WAS BROKEN WITHOUT IT: the gaps panel's whole point
is location awareness — a gap names slugs, the engine loads
`data/app/<slug>-county-outline.json` for each and tests the selected point
against them (the ENGINE coverage-gaps block's `appliesHere`). Illinois ships
101 such outlines and Wisconsin 72, so their panels open with "Where you
clicked". NYC shipped NONE and tagged all three of its gaps with an empty
counties array, so no gap could ever match and the section could never appear.
Recorded in docs/DATA_LAYER_GUIDEBOOK.md on 2026-08-27 as owed work, alongside
the engine half of the same bug, which shipped fleet-wide that day.

BOROUGHS ARE COUNTIES, AND THE SLUG USES THE BOROUGH NAME. Each of the five
boroughs is coextensive with a New York State county — Manhattan is New York
County, Brooklyn is Kings, Staten Island is Richmond — so the fleet's
"county outline" concept applies exactly. The SLUG is the borough name
regardless, because that is the word a reader uses, the word the app's own
borough layer prints, and the word a maintainer tagging a gap would reach for:
`["brooklyn"]` reads as a place and `["kings"]` reads as a puzzle. The county
name and FIPS ride in each file's properties so the identification is never
lost.

THE SOURCE IS THE FILE THE APP ALREADY SHIPS. `borough-boundaries.json` is the
same five polygons the borough card renders, already shipped and already
gated, so the outlines are SLICED from it rather than fetched. That is not
merely cheaper: it makes a disagreement between an outline and the borough
card structurally impossible.

SIMPLIFICATION IS THE POINT, NOT A DETAIL. The shipped boroughs run 34-98 KB
apiece — a panel probing all five would pull ~300 KB to answer a yes/no
question. At 25 m (the tolerance Illinois's and Wisconsin's outlines carry)
they collapse by well over an order of magnitude with no effect on an answer
whose whole job is "is this point in this borough".

FOUR GATES, and the middle two are the ones that matter — they prove
simplification did not move a line far enough to change an answer:

  1. exactly 5 boroughs in, 5 files out, slugs unique;
  2. SELF-CONTAINMENT: each borough's interior probe point — derived from its
     ORIGINAL geometry, never from the simplified ring — must still land
     inside its own simplified outline;
  3. EXCLUSIVITY: that same point must land inside NO OTHER borough's
     simplified outline. A ring that swallowed a neighbour fails here, which a
     per-borough area check alone would miss;
  4. area drift under 0.5% per borough.

Usage:
    python3 ny/scripts/build_ny_borough_outlines.py
    python3 ny/scripts/build_ny_borough_outlines.py --check
"""

import json
import math
import os
import re
import sys

INSTANCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
SOURCE = os.path.join(APP_DATA_DIR, "borough-boundaries.json")

EXPECT_BOROUGHS = 5
SIMPLIFY_TOLERANCE_M = 25
MAX_AREA_DRIFT = 0.005          # 0.5%
NYC_LAT = 40.7                  # for the longitude compression below


def slug_of(name):
    """"Staten Island" -> "staten-island"; the convention Illinois's and
    Wisconsin's outline files already use, so a gap's `counties` entry reads
    the same in any instance."""
    base = str(name).strip().lower().replace(".", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def simplify(ring, tolerance_m=SIMPLIFY_TOLERANCE_M):
    """Douglas-Peucker, the same algorithm and tolerance the other instances'
    outlines carry. Distances are metres, with longitude compressed by
    cos(latitude) so the tolerance means the same thing on both axes."""
    if len(ring) < 3:
        return ring
    tol = tolerance_m / 111320.0
    scale = math.cos(math.radians(NYC_LAT))

    def perp(p, a, b):
        ax, ay = a[0] * scale, a[1]
        bx, by = b[0] * scale, b[1]
        px, py = p[0] * scale, p[1]
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    keep = {0, len(ring) - 1}
    stack = [(0, len(ring) - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        worst, wi = 0.0, None
        for k in range(i + 1, j):
            d = perp(ring[k], ring[i], ring[j])
            if d > worst:
                worst, wi = d, k
        if worst > tol and wi is not None:
            keep.add(wi)
            stack.append((i, wi))
            stack.append((wi, j))
    out = [ring[i] for i in sorted(keep)]
    if out[0] != out[-1]:
        out.append(list(out[0]))
    # A ring that collapses below a triangle is not a ring; keep the original.
    return out if len(out) >= 4 else ring


def rings_of_geometry(geom):
    t = geom.get("type")
    if t == "Polygon":
        return [list(r) for r in geom["coordinates"]]
    if t == "MultiPolygon":
        return [list(r) for poly in geom["coordinates"] for r in poly]
    raise SystemExit("unexpected geometry type %r" % t)


def ring_area(ring):
    """Unsigned shoelace area in square degrees — a relative measure, used only
    to compare a ring against its own simplified self."""
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) / 2.0


def total_area(geom):
    return sum(ring_area(r) for r in rings_of_geometry(geom))


def simplify_geometry(geom):
    if geom["type"] == "Polygon":
        return {"type": "Polygon",
                "coordinates": [simplify(r) for r in geom["coordinates"]]}
    return {"type": "MultiPolygon",
            "coordinates": [[simplify(r) for r in poly]
                            for poly in geom["coordinates"]]}


def point_in_ring(pt, ring):
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def point_in_geometry(pt, geom):
    """Even-odd across every ring: a point in a hole cancels back out, which is
    what a borough with an interior water body needs."""
    hits = 0
    for ring in rings_of_geometry(geom):
        if point_in_ring(pt, ring):
            hits += 1
    return hits % 2 == 1


def probe_point(geom):
    """An interior point of the ORIGINAL geometry, found deterministically: the
    bounding-box centre when it lands inside, otherwise the first hit on a
    coarse lattice scanned in a fixed order. Staten Island and Queens are
    concave enough that a centroid is not guaranteed to be inside."""
    rings = rings_of_geometry(geom)
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    mid = ((lo_x + hi_x) / 2.0, (lo_y + hi_y) / 2.0)
    if point_in_geometry(mid, geom):
        return mid
    for n in (11, 31, 71):
        for i in range(1, n):
            for j in range(1, n):
                pt = (lo_x + (hi_x - lo_x) * i / n, lo_y + (hi_y - lo_y) * j / n)
                if point_in_geometry(pt, geom):
                    return pt
    raise SystemExit("no interior point found — the geometry is not a polygon?")


def build():
    with open(SOURCE) as f:
        src = json.load(f)
    feats = src["features"]
    if len(feats) != EXPECT_BOROUGHS:
        raise SystemExit("borough-boundaries.json has %d features, expected %d"
                         % (len(feats), EXPECT_BOROUGHS))

    out, seen = {}, set()
    for feat in feats:
        props = feat["properties"]
        name = props["boroname"]
        slug = slug_of(name)
        if slug in seen:
            raise SystemExit("two boroughs slug to %r" % slug)
        seen.add(slug)
        original = feat["geometry"]
        simple = simplify_geometry(original)

        drift = abs(total_area(simple) - total_area(original)) / total_area(original)
        if drift > MAX_AREA_DRIFT:
            raise SystemExit("%s: simplify moved %.2f%% of the area (limit %.1f%%)"
                             % (name, drift * 100, MAX_AREA_DRIFT * 100))

        out[slug] = {
            "name": name,
            "probe": probe_point(original),
            "drift": drift,
            "geojson": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"borough": name,
                                   "county": props["county"] + " County",
                                   "countyfips": props["countyfips"]},
                    "geometry": simple,
                }],
            },
        }

    # SELF-CONTAINMENT and EXCLUSIVITY, on the SIMPLIFIED rings.
    for slug, rec in out.items():
        geom = rec["geojson"]["features"][0]["geometry"]
        if not point_in_geometry(rec["probe"], geom):
            raise SystemExit("%s: its own interior point fell outside its simplified "
                             "outline — the tolerance moved a real line" % rec["name"])
        for other, orec in out.items():
            if other == slug:
                continue
            ogeom = orec["geojson"]["features"][0]["geometry"]
            if point_in_geometry(rec["probe"], ogeom):
                raise SystemExit("%s's interior point also lands inside %s — a "
                                 "simplified ring swallowed a neighbour"
                                 % (rec["name"], orec["name"]))
    return out


def main():
    check_only = "--check" in sys.argv[1:]
    built = build()
    total, stale = 0, []
    for slug, rec in sorted(built.items()):
        path = os.path.join(APP_DATA_DIR, "%s-county-outline.json" % slug)
        body = json.dumps(rec["geojson"], separators=(",", ":"))
        total += len(body)
        if check_only:
            try:
                with open(path) as f:
                    if json.load(f) != rec["geojson"]:
                        stale.append(slug)
            except (OSError, ValueError):
                stale.append(slug)
        else:
            with open(path, "w") as f:
                f.write(body)
    if check_only:
        if stale:
            print("build-ny-borough-outlines: FAIL — stale or missing: %s"
                  % ", ".join(stale), file=sys.stderr)
            return 1
        print("build-ny-borough-outlines: OK — %d outlines match the shipped borough "
              "fabric (%d KB total, %d m tolerance)"
              % (len(built), total // 1024, SIMPLIFY_TOLERANCE_M))
        return 0
    print("build-ny-borough-outlines: wrote %d outlines (%d KB total, %d m tolerance, "
          "worst area drift %.3f%%)"
          % (len(built), total // 1024, SIMPLIFY_TOLERANCE_M,
             max(r["drift"] for r in built.values()) * 100))
    return 0


if __name__ == "__main__":
    sys.exit(main())

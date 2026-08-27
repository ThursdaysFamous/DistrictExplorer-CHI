#!/usr/bin/env python3
"""
Build data/app/san-francisco-county-outline.json — the containment test the
Data gaps panel uses to lead with the gaps that apply WHERE THE READER CLICKED.

WHY THIS EXISTS, AND WHAT WAS BROKEN WITHOUT IT: the gaps panel's whole point
is location awareness — a gap names slugs, the engine loads
`data/app/<slug>-county-outline.json` for each and tests the selected point
against them (the ENGINE coverage-gaps block's `appliesHere`). Illinois ships
101 such outlines and Wisconsin 72, so their panels open with "Where you
clicked". San Francisco shipped NONE and tagged all three of its gaps with an
empty counties array, so no gap could ever match and the section could never
appear. Recorded in docs/DATA_LAYER_GUIDEBOOK.md on 2026-08-27 as owed work,
alongside the engine half of the same bug, which shipped fleet-wide that day.

ONE COUNTY, WHICH IS THE WHOLE INSTANCE. San Francisco is a consolidated city
and county, so this file is a single outline and every point the app answers
for is inside it. That is not a reason to skip it: without the file the panel
cannot say "here" about anything, and with it all three of this instance's
gaps correctly read as applying wherever a reader clicks — which is the true
answer, since all three are citywide.

THE SOURCE IS THE FILE THE APP ALREADY SHIPS. The eleven supervisor districts
partition the city exactly, and they are already shipped and already gated, so
the outline is their UNION rather than a fetch. That makes a disagreement
between this outline and the supervisor card structurally impossible — the
same two-surfaces rule the other instances apply to counties.

THE UNION IS REAL GEOMETRY, NOT EDGE-CANCELLATION. Wisconsin's dissolve chains
rings by cancelling shared segments, which needs the neighbours' coordinates to
match EXACTLY; the root repo's own requirements.txt records that approach
leaving a spurious 3-segment ring on precinct data. shapely's unary_union does
the real thing, and is already pinned at 2.1.2 in two of this repo's
requirements files — this adds the same pin here rather than a new dependency
to the fleet.

FOUR GATES:

  1. exactly 11 districts in, exactly 1 outline out;
  2. COVERAGE: every district's own interior probe point — derived from its
     ORIGINAL geometry, never from the simplified ring — must land inside the
     simplified outline. This is the gate that matters: it proves the union
     kept every district and that simplification did not clip one off;
  3. the union is a single connected body plus its islands, never an empty or
     degenerate geometry;
  4. area drift under 0.5% between the raw union and the simplified one.

Usage:
    python3 ca/scripts/build_sf_county_outline.py
    python3 ca/scripts/build_sf_county_outline.py --check
"""

import json
import math
import os
import sys

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

INSTANCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
SOURCE = os.path.join(APP_DATA_DIR, "supervisor-districts.json")
SLUG = "san-francisco"
OUT = os.path.join(APP_DATA_DIR, "%s-county-outline.json" % SLUG)

EXPECT_DISTRICTS = 11
SIMPLIFY_TOLERANCE_M = 25
MAX_AREA_DRIFT = 0.005          # 0.5%
SF_LAT = 37.77                  # for the longitude compression below


def simplify(ring, tolerance_m=SIMPLIFY_TOLERANCE_M):
    """Douglas-Peucker, the same algorithm and tolerance the other instances'
    outlines carry. Distances are metres, with longitude compressed by
    cos(latitude) so the tolerance means the same thing on both axes."""
    if len(ring) < 3:
        return ring
    tol = tolerance_m / 111320.0
    scale = math.cos(math.radians(SF_LAT))

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
    return out if len(out) >= 4 else ring


def rings_of_geometry(geom):
    t = geom.get("type")
    if t == "Polygon":
        return [list(r) for r in geom["coordinates"]]
    if t == "MultiPolygon":
        return [list(r) for poly in geom["coordinates"] for r in poly]
    raise SystemExit("unexpected geometry type %r" % t)


def ring_area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) / 2.0


def total_area(geom):
    return sum(ring_area(r) for r in rings_of_geometry(geom))


def simplify_geometry(geom):
    if geom["type"] == "Polygon":
        return {"type": "Polygon",
                "coordinates": [simplify(list(r)) for r in geom["coordinates"]]}
    return {"type": "MultiPolygon",
            "coordinates": [[simplify(list(r)) for r in poly]
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
    hits = sum(1 for r in rings_of_geometry(geom) if point_in_ring(pt, r))
    return hits % 2 == 1


def probe_point(geom):
    """An interior point of the ORIGINAL geometry, found deterministically."""
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
    if len(feats) != EXPECT_DISTRICTS:
        raise SystemExit("supervisor-districts.json has %d features, expected %d"
                         % (len(feats), EXPECT_DISTRICTS))

    probes = [(f["properties"].get("district"), probe_point(f["geometry"]))
              for f in feats]

    union = unary_union([shape(f["geometry"]) for f in feats])
    if union.is_empty:
        raise SystemExit("the union of the supervisor districts is empty")
    raw = mapping(union)
    if raw["type"] not in ("Polygon", "MultiPolygon"):
        raise SystemExit("the union is a %s, not a polygon" % raw["type"])
    simple = simplify_geometry(raw)

    drift = abs(total_area(simple) - total_area(raw)) / total_area(raw)
    if drift > MAX_AREA_DRIFT:
        raise SystemExit("simplify moved %.2f%% of the area (limit %.1f%%)"
                         % (drift * 100, MAX_AREA_DRIFT * 100))

    # THE GATE THAT MATTERS: the outline must contain every district it was
    # built from. A union that dropped one, or a tolerance that clipped one
    # off, fails here rather than shipping a panel that says "not here".
    for district, pt in probes:
        if not point_in_geometry(pt, simple):
            raise SystemExit("district %s's own interior point falls outside the "
                             "simplified outline" % district)

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"county": "San Francisco County",
                           "countyfips": "06075",
                           "note": "City and County of San Francisco — the union "
                                   "of the eleven supervisor districts the app ships"},
            "geometry": simple,
        }],
    }, drift


def main():
    check_only = "--check" in sys.argv[1:]
    geojson, drift = build()
    body = json.dumps(geojson, separators=(",", ":"))
    # Compare the SERIALIZED form: shapely hands back coordinate TUPLES and a
    # reloaded file has LISTS, so a structural comparison of the two is never
    # equal and --check would fail on a file it had just written.
    written = json.loads(body)
    if check_only:
        try:
            with open(OUT) as f:
                current = json.load(f)
        except (OSError, ValueError):
            current = None
        if current != written:
            print("build-sf-county-outline: FAIL — %s is stale or missing" % OUT,
                  file=sys.stderr)
            return 1
        print("build-sf-county-outline: OK — 1 outline matches the shipped "
              "supervisor districts (%d KB, %d m tolerance)"
              % (len(body) // 1024, SIMPLIFY_TOLERANCE_M))
        return 0
    with open(OUT, "w") as f:
        f.write(body)
    print("build-sf-county-outline: wrote 1 outline (%d KB, %d m tolerance, "
          "area drift %.3f%%, all %d districts contained)"
          % (len(body) // 1024, SIMPLIFY_TOLERANCE_M, drift * 100, EXPECT_DISTRICTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())

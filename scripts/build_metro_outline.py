#!/usr/bin/env python3
"""
Metro Outline Builder (the scope mask's coverage geometry)
==========================================================
Builds data/app/metro-outline.json — ONE dissolved polygon of the seven
counties the app actually serves (Cook, DuPage, Will, Lake, Kane, McHenry,
Kendall) — from Census TIGERweb.

Why this exists: the out-of-scope wash (index.html, ENGINE `scope-mask`) marks
where the app's full coverage ends. It used to be driven by the Chicago school
board tiling, i.e. the CITY limits, which greyed out all six collar counties
and suburban Cook. That understated coverage badly: a collar point resolves
17-21 of the 39 layers (county board, precincts, judicial subcircuits, fire /
park / library districts, municipal officials with named officeholders, the
legislative trio, township, ZIP, school districts) against Chicago's 32. The
honest boundary is the metro edge, beyond which only the statewide layers
answer.

It also removes a boot cost: the old call downloaded and parsed the full
20-district school-board GeoJSON on every load — 669 ms in PSI's critical chain
(docs/OPTIMIZATION_PLAYBOOK.md) — to paint a decorative wash. This file is one
small pre-dissolved feature.

WHY A BUILD STEP RATHER THAN THE EXISTING COUNTY OUTLINES: the app's in-browser
dissolve cancels an interior border only when the two neighbours' rings share
EXACT coordinates. data/app/*-county-outline.json were simplified
independently, so they don't — DuPage and Kendall share 2 vertices where a real
border runs — and Cook has no outline file at all. A single TIGERweb query
returns topologically consistent geometry (Cook/DuPage share 2,034 exact
vertices), which is what makes the dissolve sound.

The dissolve mirrors the app's `coverageOutlineRings` exactly: a segment walked
by two features is an interior border and is dropped; survivors chain back into
closed rings. Doing it here means the browser ships one feature with no interior
edges left to cancel.

Usage:
    python3 build_metro_outline.py                 # writes data/app/metro-outline.json
    python3 build_metro_outline.py --check         # verify the shipped file, write nothing
"""

import argparse
import json
import math
import os
import sys

import requests

TIGERWEB = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
            "State_County/MapServer/1/query")
# Cook, DuPage, Will, Lake, Kane, McHenry, Kendall — the seven the app serves.
METRO_COUNTY_FIPS = ("031", "043", "197", "097", "089", "111", "093")
STATE_FIPS = "17"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "data", "app", "metro-outline.json")

HEADERS = {"User-Agent": "DistrictExplorer-CHI metro-outline builder"}
REQUEST_TIMEOUT = 180

# 25 m: the wash is a coverage hint, not a boundary claim, and at metro zoom
# this is sub-pixel. Validation below runs on the SIMPLIFIED rings, so a
# tolerance that ever moved the edge past an anchor would fail the build.
SIMPLIFY_TOLERANCE_M = 25

# Points that MUST fall inside the dissolved outline (one per county) and
# outside it. A dissolve that silently drops a county still closes its rings,
# so ring-closure alone is not proof — these are.
INSIDE = {
    "Chicago (Cook)": (41.8825, -87.6285),
    "Wheaton (DuPage)": (41.8661, -88.1070),
    "Joliet (Will)": (41.5250, -88.0817),
    "Waukegan (Lake)": (42.3636, -87.8448),
    "Aurora (Kane)": (41.7606, -88.3201),
    "Woodstock (McHenry)": (42.3147, -88.4487),
    "Yorkville (Kendall)": (41.6411, -88.4473),
}
OUTSIDE = {
    "Rockford (Winnebago)": (42.2711, -89.0940),
    "Springfield (Sangamon)": (39.7817, -89.6501),
    "Milwaukee (WI)": (43.0389, -87.9065),
    "DeKalb (DeKalb)": (41.9295, -88.7504),
    "Kankakee (Kankakee)": (41.1200, -87.8612),
}


def fetch_counties():
    where = "STATE='%s' AND COUNTY IN (%s)" % (
        STATE_FIPS, ",".join("'%s'" % c for c in METRO_COUNTY_FIPS))
    resp = requests.get(TIGERWEB, headers=HEADERS, timeout=REQUEST_TIMEOUT, params={
        "where": where,
        "outFields": "NAME,GEOID",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    })
    resp.raise_for_status()
    feats = (resp.json() or {}).get("features") or []
    if len(feats) != len(METRO_COUNTY_FIPS):
        print("FATAL: TIGERweb returned %d counties, expected %d — the query or the "
              "service changed" % (len(feats), len(METRO_COUNTY_FIPS)), file=sys.stderr)
        sys.exit(1)
    return feats


def rings_of(feature):
    geom = feature.get("geometry") or {}
    if geom.get("type") == "Polygon":
        return list(geom.get("coordinates") or [])
    if geom.get("type") == "MultiPolygon":
        return [r for poly in (geom.get("coordinates") or []) for r in poly]
    return []


def dissolve(features):
    """Drop every segment walked twice (an interior border), chain the rest.

    Mirrors index.html's coverageOutlineRings so the shipped file is exactly
    what the browser would have computed — one algorithm, two places, and the
    validation below proves this one.
    """
    counts, seg_pts = {}, {}
    for feat in features:
        for ring in rings_of(feat):
            for i in range(len(ring) - 1):
                a, b = tuple(ring[i][:2]), tuple(ring[i + 1][:2])
                if a == b:
                    continue
                key = (a, b) if a < b else (b, a)
                counts[key] = counts.get(key, 0) + 1
                seg_pts[key] = (a, b)

    adj = {}
    for key, n in counts.items():
        if n != 1:
            continue  # interior border — both neighbours walked it
        a, b = seg_pts[key]
        adj.setdefault(a, []).append((key, b))
        adj.setdefault(b, []).append((key, a))

    used, rings = set(), []
    for seed, n in counts.items():
        if n != 1 or seed in used:
            continue
        start, cur = seg_pts[seed][0], seg_pts[seed][1]
        used.add(seed)
        ring = [list(start), list(cur)]
        while cur != start:
            nxt = None
            for key, pt in adj.get(cur, ()):
                if key not in used:
                    nxt = (key, pt)
                    break
            if nxt is None:
                print("FATAL: open chain while dissolving — the counties do not tile "
                      "cleanly (a source change?)", file=sys.stderr)
                sys.exit(1)
            used.add(nxt[0])
            cur = nxt[1]
            ring.append(list(cur))
        rings.append(ring)
    return rings


def simplify(ring, tolerance_m=SIMPLIFY_TOLERANCE_M):
    """Douglas-Peucker. County borders are survey-grid straight lines and the
    east edge is the state line in Lake Michigan (not the shoreline), so this
    collapses ~2,665 vertices to ~60 with no visible change to a wash whose
    whole job is to say "coverage ends here". Distances are metres, with
    longitude compressed by cos(latitude) so the tolerance means the same thing
    on both axes."""
    if len(ring) < 3:
        return ring
    tol = tolerance_m / 111320.0
    scale = math.cos(math.radians(42.0))

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
        out.append(out[0])  # a ring must close
    return out


def point_in_rings(lat, lng, rings):
    """Even-odd test against every ring, matching the app's pointInGeometry."""
    inside = False
    for ring in rings:
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[i + 1][0], ring[i + 1][1]
            if (y1 > lat) != (y2 > lat):
                if lng < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                    inside = not inside
    return inside


def validate(rings):
    problems = []
    for label, (lat, lng) in sorted(INSIDE.items()):
        if not point_in_rings(lat, lng, rings):
            problems.append("%s should be INSIDE the metro outline and is not" % label)
    for label, (lat, lng) in sorted(OUTSIDE.items()):
        if point_in_rings(lat, lng, rings):
            problems.append("%s should be OUTSIDE the metro outline and is not" % label)
    return problems


def build_geojson(rings):
    # Largest ring first so the outer boundary leads; the app fills even-odd, so
    # enclosed rings read as holes either way.
    ordered = sorted(rings, key=len, reverse=True)
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Chicago metro coverage (7 counties)"},
            "geometry": {"type": "Polygon", "coordinates": ordered},
        }],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--check", action="store_true",
                    help="validate the shipped file instead of rebuilding")
    args = ap.parse_args()

    if args.check:
        with open(args.out) as f:
            shipped = json.load(f)
        rings = shipped["features"][0]["geometry"]["coordinates"]
        problems = validate(rings)
        for p in problems:
            print("FAIL: %s" % p, file=sys.stderr)
        if problems:
            sys.exit(1)
        print("metro-outline: OK — %d ring(s), %d vertices, all %d inside / %d outside "
              "anchors correct" % (len(rings), sum(len(r) for r in rings),
                                   len(INSIDE), len(OUTSIDE)), file=sys.stderr)
        return

    rings = [simplify(r) for r in dissolve(fetch_counties())]
    problems = validate(rings)
    for p in problems:
        print("FATAL: %s" % p, file=sys.stderr)
    if problems:
        print("FATAL: refusing to write an outline that misplaces its anchors",
              file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w") as f:
        json.dump(build_geojson(rings), f, separators=(",", ":"))
        f.write("\n")
    size = os.path.getsize(args.out)
    print("wrote %s: %d ring(s), %d vertices, %.1f KB"
          % (args.out, len(rings), sum(len(r) for r in rings), size / 1024.0),
          file=sys.stderr)


if __name__ == "__main__":
    main()

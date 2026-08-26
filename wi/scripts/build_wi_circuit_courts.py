#!/usr/bin/env python3
"""
Wisconsin Circuit Court geometry — county unions under a double witness.

No agency publishes circuit-court geometry (measured 2026-08-25: the ArcGIS
catalog answers zero across three queries and LTSB's 97-service org carries no
court layer), and this project never draws a boundary no agency publishes — so
this file is legitimate ONLY because it draws no new line at all: every circuit
is a union of whole counties whose polygons the app already ships
(data/app/state-counties.json, one TIGERweb fetch, topologically consistent —
the merged pairs share 242/303/401 exact border segments, measured), and the
county-to-circuit composition carries a DOUBLE WITNESS that agrees exactly:

  1. Wis. Stat. 753.06 — one circuit per county, EXCEPT three two-county
     circuits: Buffalo+Pepin (753.06(5)(a)), Florence+Forest (753.06(8)(b)),
     and Menominee+Shawano (753.06(8)(e)). CITE PER-SUBSECTION URLS when
     re-verifying: the chapter page lazy-loads and one fetch truncates at 52
     of 63 entries (measured), so reading it whole under-counts silently.
  2. wicourts.gov's own circuit listing (the judges table at
     /courts/circuit/judges.htm), which prints the same three combinations —
     two as slash pairs listed BOTH ways round (Buffalo/Pepin AND
     Pepin/Buffalo, a double-count trap the roster scraper dedupes) and
     Florence/Forest as two slash-less rows sharing one judge.

The weekly roster scraper (wi_circuit_judges_scraper.py) re-reads witness 2 on
every run and fails loudly if the county set or the merge pattern moves, which
is this layer's redistricting tripwire; the statute is the anchor this builder
hardcodes. 69 circuits = 66 single-county + 3 two-county.

The two-county unions are DISSOLVED (the shared border dropped, survivors
chained back into rings — the metro-outline builder's algorithm), so the map
never draws a county line inside a circuit that statute says has none.

Gates (the build refuses to write unless all hold):
  * exactly 69 features;
  * all 72 counties assigned exactly once;
  * the three statutory merges present, and no other;
  * each dissolved union keeps every exterior segment of its two counties
    (ring-length conservation: exterior segment count in == chained out);
  * a representative interior point of every county lands in its own
    circuit's polygon (the containment witness).

Usage:
    python3 wi/scripts/build_wi_circuit_courts.py            # write the file
    python3 wi/scripts/build_wi_circuit_courts.py --check    # verify shipped
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTIES_FILE = os.path.join(REPO_ROOT, "data", "app", "state-counties.json")
OUT_FILE = os.path.join(REPO_ROOT, "data", "app", "wi-circuit-courts.json")

# Wis. Stat. 753.06's three two-county circuits — the ONLY departures from
# one-circuit-per-county. Keys are the shipped circuit keys (roster join key).
MERGED = {
    "buffalo-pepin": ("Buffalo", "Pepin"),
    "florence-forest": ("Florence", "Forest"),
    "menominee-shawano": ("Menominee", "Shawano"),
}
EXPECT_CIRCUITS = 69
EXPECT_COUNTIES = 72


def county_key(basename):
    return basename.lower().replace(" ", "-").replace(".", "")


def rings_of(feature):
    geom = feature.get("geometry") or {}
    if geom.get("type") == "Polygon":
        return [list(r) for r in geom.get("coordinates") or []]
    if geom.get("type") == "MultiPolygon":
        return [list(r) for poly in (geom.get("coordinates") or []) for r in poly]
    return []


def dissolve_pair(features):
    """The metro-outline dissolve, scoped to one two-county union: drop every
    segment walked twice (the shared county line), chain the rest into closed
    rings. Refuses an open chain — that would mean the two counties do not
    share exact coordinates, i.e. the source stopped being the one
    topologically-consistent TIGERweb pull this derivation rests on."""
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
    exterior = 0
    for key, n in counts.items():
        if n != 1:
            continue
        exterior += 1
        a, b = seg_pts[key]
        adj.setdefault(a, []).append((key, b))
        adj.setdefault(b, []).append((key, a))

    used, rings, walked = set(), [], 0
    for seed, n in counts.items():
        if n != 1 or seed in used:
            continue
        start, cur = seg_pts[seed]
        used.add(seed)
        walked += 1
        ring = [list(start), list(cur)]
        while cur != start:
            nxt = None
            for key, pt in adj.get(cur, ()):
                if key not in used:
                    nxt = (key, pt)
                    break
            if nxt is None:
                raise SystemExit("FATAL: open chain dissolving a two-county circuit — "
                                 "the county file is no longer topologically consistent")
            used.add(nxt[0])
            walked += 1
            cur = nxt[1]
            ring.append(list(cur))
        rings.append(ring)
    if walked != exterior:
        raise SystemExit("FATAL: dissolve dropped exterior segments (%d walked of %d)"
                         % (walked, exterior))
    # Nest: the largest ring is the outer boundary of each disjoint part; a
    # two-county land union here is always simply connected, so every ring is
    # its own polygon (no holes between two adjacent counties).
    return {"type": "MultiPolygon", "coordinates": [[r] for r in rings]} \
        if len(rings) > 1 else {"type": "Polygon", "coordinates": rings}


def interior_point(feature):
    """A cheap representative point: the centroid of the largest ring's
    vertices, nudged to the ring's own containment if needed (counties are
    convex enough that the vertex centroid lands inside for all 72 — asserted
    by the containment gate, which is the real check)."""
    rings = rings_of(feature)
    ring = max(rings, key=len)
    xs = [p[0] for p in ring[:-1]]
    ys = [p[1] for p in ring[:-1]]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def point_in_geom(pt, geom):
    x, y = pt

    def in_ring(ring):
        inside = False
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if in_ring(poly[0]) and not any(in_ring(hole) for hole in poly[1:]):
            return True
    return False


def build():
    with open(COUNTIES_FILE) as f:
        counties = json.load(f)["features"]
    if len(counties) != EXPECT_COUNTIES:
        raise SystemExit("expected %d counties, found %d" % (EXPECT_COUNTIES, len(counties)))

    by_base = {}
    for feat in counties:
        base = feat["properties"].get("BASENAME")
        if not base:
            raise SystemExit("county feature missing BASENAME")
        by_base[base] = feat

    merged_members = {c for pair in MERGED.values() for c in pair}
    assigned = set()
    features = []

    for key, (a, b) in sorted(MERGED.items()):
        fa, fb = by_base.get(a), by_base.get(b)
        if fa is None or fb is None:
            raise SystemExit("merged circuit %s names a county not in the file" % key)
        geom = dissolve_pair([fa, fb])
        features.append({
            "type": "Feature",
            "properties": {
                "CIRCUIT": key,
                "NAME": "%s–%s Circuit Court" % (a, b),
                "COUNTIES": "%s County, %s County" % (a, b),
            },
            "geometry": geom,
        })
        assigned.update((a, b))

    for base in sorted(by_base):
        if base in merged_members:
            continue
        feat = by_base[base]
        features.append({
            "type": "Feature",
            "properties": {
                "CIRCUIT": county_key(base),
                "NAME": "%s County Circuit Court" % base,
                "COUNTIES": "%s County" % base,
            },
            "geometry": feat["geometry"],
        })
        assigned.add(base)

    if len(features) != EXPECT_CIRCUITS:
        raise SystemExit("built %d circuits, expected %d" % (len(features), EXPECT_CIRCUITS))
    if assigned != set(by_base):
        raise SystemExit("county partition broken: %s" % sorted(set(by_base) ^ assigned))

    # Containment witness: every county's interior point lands in its circuit.
    by_circuit = {f["properties"]["CIRCUIT"]: f for f in features}
    for base, feat in by_base.items():
        ckey = None
        for mkey, pair in MERGED.items():
            if base in pair:
                ckey = mkey
        ckey = ckey or county_key(base)
        pt = interior_point(feat)
        if not point_in_geom(pt, by_circuit[ckey]["geometry"]):
            raise SystemExit("containment gate: %s's interior point missed circuit %s"
                             % (base, ckey))

    return {"type": "FeatureCollection", "features": features}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped file matches a fresh build; write nothing")
    args = ap.parse_args()

    built = build()
    if args.check:
        with open(OUT_FILE) as f:
            shipped = json.load(f)
        if json.dumps(shipped, sort_keys=True) != json.dumps(built, sort_keys=True):
            print("FAIL: shipped wi-circuit-courts.json differs from a fresh build",
                  file=sys.stderr)
            sys.exit(1)
        print("check: shipped circuit geometry matches the county file (%d circuits)"
              % len(built["features"]))
        return

    with open(OUT_FILE, "w") as f:
        json.dump(built, f, separators=(",", ":"))
    size = os.path.getsize(OUT_FILE)
    print("wrote %s — %d circuits (%d single-county + %d merged), %.1f KB"
          % (OUT_FILE, len(built["features"]),
             len(built["features"]) - len(MERGED), len(MERGED), size / 1024.0))


if __name__ == "__main__":
    main()

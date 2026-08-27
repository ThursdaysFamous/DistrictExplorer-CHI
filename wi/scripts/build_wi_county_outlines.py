#!/usr/bin/env python3
"""
Build data/app/<slug>-county-outline.json for all 72 Wisconsin counties — the
per-county containment tests the Data gaps panel uses to lead with the gaps
that apply WHERE THE READER CLICKED.

WHY THIS EXISTS, AND WHAT WAS BROKEN WITHOUT IT: the gaps panel's whole point
is location awareness — a gap names county slugs, the engine loads
`data/app/<slug>-county-outline.json` for each and tests the selected point
against them (the ENGINE coverage-gaps block's `appliesHere`). Illinois ships
101 such outlines and tags 100 of its 101 gaps with counties, so its panel
opens with "Where you clicked". Wisconsin shipped NONE and tagged every one of
its ten gaps with an empty counties array, so no gap could ever match: the
"Where you clicked" section never appeared, and — measured 2026-08-27 in a real
browser at Milwaukee City Hall — the panel told a reader who HAD clicked
"Click a spot on the map first", because the lede's mappable/point branches
both fall through when nothing is taggable. The panel was honest about the
gaps and wrong about the reader.

THE SOURCE IS THE FILE THE APP ALREADY SHIPS. Illinois builds its outlines
from TIGERweb per county (scripts/build_county_outline.py, a live fetch plus
hand-listed anchors per county). Wisconsin does not need that fetch: the
county card already renders `data/app/state-counties.json` — the same 72
TIGERweb counties, already shipped, already gated — so the outlines are SLICED
from it. That is not merely cheaper; it makes a disagreement between the
outline and the county card structurally impossible, the two-surfaces rule
this project applies to counties elsewhere.

SIMPLIFICATION IS SHARED, NEVER FORKED: `simplify` comes from this
instance's own wi/scripts/build_metro_outline.py (Douglas-Peucker, 25 m — the
same tolerance Illinois's outlines carry), imported rather than copied so a
county outline and the metro outline can never disagree about what a boundary
is.

FOUR GATES, and the middle two are the ones that matter — they prove
simplification did not move a line far enough to change an answer:

  1. exactly 72 counties in, 72 files out, slugs unique;
  2. SELF-CONTAINMENT: each county's interior probe point — derived from its
     ORIGINAL geometry, never from the simplified ring — must still land inside
     its own simplified outline;
  3. EXCLUSIVITY: that same point must land inside NO OTHER county's simplified
     outline. A ring that swallowed a neighbour's territory fails here, which a
     per-county area check alone would miss;
  4. area drift under 0.5% per county.

Usage:
    python3 wi/scripts/build_wi_county_outlines.py
    python3 wi/scripts/build_wi_county_outlines.py --check   # CI drift gate
"""

import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA_DIR = os.path.join(INSTANCE_ROOT, "data", "app")
COUNTIES_FILE = os.path.join(APP_DATA_DIR, "state-counties.json")

# THIS INSTANCE'S copy of the shared machinery, never the root repo's: an
# instance's scripts resolve against their own directory (the rule
# validate_workflow_deps.py enforces, and the reason a cross-instance
# sys.path insert here failed CI). Wisconsin carries its own
# build_metro_outline with the same Douglas-Peucker and the same 25 m
# tolerance; importing it means a county outline and this instance's metro
# outline can never disagree about what a boundary is.
from build_metro_outline import (  # noqa: E402  (shared machinery — do not fork)
    SIMPLIFY_TOLERANCE_M, point_in_rings, simplify,
)

EXPECT_COUNTIES = 72
MAX_AREA_DRIFT = 0.005   # 0.5% — a simplify that moves more than this is broken


def slug_of(name):
    """"St. Croix County" -> "st-croix"; the convention Illinois's outline
    files already use (lowercase, periods dropped, spaces hyphenated), so a
    gap's `counties` entry reads the same in either instance."""
    base = re.sub(r"\s+County$", "", str(name)).strip().lower()
    base = base.replace(".", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def rings_of_geometry(geom):
    """Every linear ring in a Polygon or MultiPolygon, as [[lng, lat], ...]."""
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


def simplify_geometry(geom):
    """Simplify every ring in place, preserving Polygon/MultiPolygon shape."""
    t = geom["type"]
    if t == "Polygon":
        return {"type": "Polygon",
                "coordinates": [simplify(r) for r in geom["coordinates"]]}
    return {"type": "MultiPolygon",
            "coordinates": [[simplify(r) for r in poly]
                            for poly in geom["coordinates"]]}


def probe_point(geom):
    """An interior point of the ORIGINAL geometry, found deterministically: the
    bounding-box centre when it lands inside, otherwise the first hit on a
    coarse lattice scanned in a fixed order. Concave counties (Door's peninsula,
    the river-bend counties) are exactly why the centroid alone will not do."""
    rings = rings_of_geometry(geom)
    lngs = [p[0] for r in rings for p in r]
    lats = [p[1] for r in rings for p in r]
    lo_lng, hi_lng, lo_lat, hi_lat = min(lngs), max(lngs), min(lats), max(lats)
    mid = ((lo_lat + hi_lat) / 2.0, (lo_lng + hi_lng) / 2.0)
    if point_in_rings(mid[0], mid[1], rings):
        return mid
    steps = 21
    for i in range(1, steps):
        for j in range(1, steps):
            lat = lo_lat + (hi_lat - lo_lat) * i / float(steps)
            lng = lo_lng + (hi_lng - lo_lng) * j / float(steps)
            if point_in_rings(lat, lng, rings):
                return (lat, lng)
    raise SystemExit("no interior point found — geometry is degenerate")


def build():
    with open(COUNTIES_FILE, encoding="utf-8") as f:
        counties = json.load(f)["features"]
    if len(counties) != EXPECT_COUNTIES:
        raise SystemExit("state-counties.json carries %d counties, expected %d "
                         "— the county fabric moved; re-measure before "
                         "rebuilding outlines" % (len(counties), EXPECT_COUNTIES))

    built = {}
    probes = {}
    for feat in counties:
        props = feat.get("properties") or {}
        name = props.get("NAME")
        slug = slug_of(name)
        if not slug:
            raise SystemExit("county %r produced an empty slug" % name)
        if slug in built:
            raise SystemExit("slug %r is claimed by two counties — the naming "
                             "convention collides; fix slug_of" % slug)
        original = feat["geometry"]
        probes[slug] = probe_point(original)
        simplified = simplify_geometry(original)

        before = sum(ring_area(r) for r in rings_of_geometry(original))
        after = sum(ring_area(r) for r in rings_of_geometry(simplified))
        drift = abs(after - before) / before if before else 0.0
        if drift > MAX_AREA_DRIFT:
            raise SystemExit("%s: simplification moved %.3f%% of the county's "
                             "area (ceiling %.1f%%) — the ring is no longer the "
                             "county" % (slug, drift * 100, MAX_AREA_DRIFT * 100))

        built[slug] = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"NAME": name, "GEOID": props.get("GEOID")},
                "geometry": simplified,
            }],
        }

    # ---- gate 2 + 3: every probe point lands in its own county and no other --
    rings_by_slug = {s: rings_of_geometry(fc["features"][0]["geometry"])
                     for s, fc in built.items()}
    for slug, (lat, lng) in probes.items():
        if not point_in_rings(lat, lng, rings_by_slug[slug]):
            raise SystemExit("%s: its own interior point (%.5f, %.5f) fell "
                             "OUTSIDE the simplified outline — simplification "
                             "broke containment" % (slug, lat, lng))
        for other, rings in rings_by_slug.items():
            if other == slug:
                continue
            if point_in_rings(lat, lng, rings):
                raise SystemExit("%s's interior point (%.5f, %.5f) also lands "
                                 "inside %s — a simplified ring swallowed a "
                                 "neighbour" % (slug, lat, lng, other))
    return built


def payload(fc):
    return json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the shipped outlines, write nothing")
    args = ap.parse_args()

    built = build()
    total = 0
    stale = []
    for slug in sorted(built):
        path = os.path.join(APP_DATA_DIR, "%s-county-outline.json" % slug)
        body = payload(built[slug])
        total += len(body)
        if args.check:
            if not os.path.exists(path):
                stale.append("%s-county-outline.json is missing" % slug)
            else:
                with open(path, encoding="utf-8") as f:
                    if f.read() != body:
                        stale.append("%s-county-outline.json differs from the "
                                     "county fabric" % slug)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)

    if args.check:
        if stale:
            for s in stale[:8]:
                print("  %s" % s, file=sys.stderr)
            raise SystemExit("build-wi-county-outlines: FAIL — %d outline(s) "
                             "stale; regenerate with "
                             "wi/scripts/build_wi_county_outlines.py" % len(stale))
        print("build-wi-county-outlines: OK — %d outlines match the shipped "
              "county fabric (%.0f KB total, %d m tolerance)"
              % (len(built), total / 1024.0, SIMPLIFY_TOLERANCE_M))
        return
    print("build-wi-county-outlines: wrote %d outlines from state-counties.json "
          "— %.0f KB total, %d m tolerance; every county's interior point lands "
          "in its own outline and no other"
          % (len(built), total / 1024.0, SIMPLIFY_TOLERANCE_M), file=sys.stderr)


if __name__ == "__main__":
    main()

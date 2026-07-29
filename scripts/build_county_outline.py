#!/usr/bin/env python3
"""
Build data/app/<slug>-county-outline.json — the coverage outline a county's
dispatch entries test against (docs/EXPANSION_GUIDE.md §2.5 step 1).

Why this exists: the seven metro counties' outlines were each produced by a
one-off run, so the first thing a new county needed was a procedure nobody had
written down. This makes step 1 of the county-N+1 checklist reproducible — and
reuses build_metro_outline.py's TIGERweb fetch, Douglas-Peucker simplify and
point-in-rings test rather than forking them, so a county outline and the metro
outline can never disagree about what a boundary is.

The outline is a coverage TEST, not a drawn boundary: `<county>CountyCoverage`
asks "is this point in the county", so vertex-exact fidelity buys nothing and
costs bytes on every first toggle. Simplification is the same 25 m tolerance the
metro outline uses. What IS load-bearing is that the result still answers
correctly near the edge, so every build validates against anchors — points that
must be inside and points just across each neighbouring county line that must be
outside — and refuses to write when any of them lands wrong.

Usage:
    python3 scripts/build_county_outline.py lasalle kankakee
    python3 scripts/build_county_outline.py --check lasalle   # verify, write nothing
    python3 scripts/build_county_outline.py --list            # known counties
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests  # noqa: E402
from build_metro_outline import (  # noqa: E402  (shared machinery — do not fork)
    HEADERS, REQUEST_TIMEOUT, SIMPLIFY_TOLERANCE_M, STATE_FIPS, TIGERWEB,
    point_in_rings, rings_of, simplify,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")

# county slug -> FIPS, display name, and the anchors that prove the built ring
# still answers correctly. `inside` points sit well within the county; `outside`
# points sit just across a line the outline must not swallow — each names the
# neighbour it belongs to, so a failure says which edge moved.
COUNTIES = {
    "lasalle": {
        "fips": "099",
        "name": "LaSalle County",
        "inside": [
            (41.3517, -88.8454, "Ottawa (county seat)"),
            (41.1206, -88.8351, "Streator"),
            (41.3273, -89.1290, "Peru"),
            (41.5473, -89.1176, "Mendota"),
        ],
        "outside": [
            (41.4295, -88.2120, "Morris — Grundy County"),
            (41.3670, -89.4640, "Princeton — Bureau County"),
            (41.7606, -88.8570, "DeKalb County"),
            (40.7480, -88.6320, "Pontiac — Livingston County"),
        ],
    },
    "kankakee": {
        "fips": "091",
        "name": "Kankakee County",
        # Coordinates verified by geocoding each place rather than recalled — the
        # first draft put "Herscher" a full county south of the real town and the
        # anchor check caught it, which is exactly what it is for.
        "inside": [
            (41.1254, -87.8487, "Kankakee (county seat)"),
            (41.2502, -87.8326, "Manteno"),
            (41.1647, -87.6625, "Momence"),
            (41.0495, -88.0962, "Herscher"),
        ],
        "outside": [
            (41.3328, -87.7898, "Peotone — Will County"),
            (40.7761, -87.7364, "Watseka — Iroquois County"),
            (41.1600, -87.4400, "Newton County, Indiana"),
            (41.0100, -88.2900, "Livingston County"),
        ],
    },
}


def fetch_county(fips):
    resp = requests.get(TIGERWEB, headers=HEADERS, timeout=REQUEST_TIMEOUT, params={
        "where": "STATE='%s' AND COUNTY='%s'" % (STATE_FIPS, fips),
        "outFields": "NAME,GEOID",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    })
    resp.raise_for_status()
    feats = (resp.json() or {}).get("features") or []
    if len(feats) != 1:
        raise RuntimeError("TIGERweb returned %d features for county %s, expected 1"
                           % (len(feats), fips))
    return feats[0]


def build_rings(feature):
    """Simplify every ring, keeping the multi-ring structure TIGER returned."""
    out = []
    for ring in rings_of(feature):
        s = simplify(ring, SIMPLIFY_TOLERANCE_M)
        if s[0] != s[-1]:
            s.append(s[0])
        if len(s) >= 4:
            out.append(s)
    if not out:
        raise RuntimeError("simplification produced no usable ring")
    return out


def validate(rings, cfg):
    """Anchors are checked on the SIMPLIFIED rings — the bytes that ship."""
    problems = []
    for lat, lng, label in cfg["inside"]:
        if not point_in_rings(lat, lng, rings):
            problems.append("%s should be INSIDE %s and is not" % (label, cfg["name"]))
    for lat, lng, label in cfg["outside"]:
        if point_in_rings(lat, lng, rings):
            problems.append("%s should be OUTSIDE %s and is not" % (label, cfg["name"]))
    return problems


def geojson_for(rings, cfg):
    geom = ({"type": "Polygon", "coordinates": rings} if len(rings) == 1
            else {"type": "MultiPolygon", "coordinates": [[r] for r in rings]})
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"name": cfg["name"]}, "geometry": geom}],
    }


def run(slug, check_only):
    cfg = COUNTIES[slug]
    out_path = os.path.join(APP_DATA_DIR, "%s-county-outline.json" % slug)
    rings = build_rings(fetch_county(cfg["fips"]))
    problems = validate(rings, cfg)
    if problems:
        for p in problems:
            print("  FAIL: %s" % p, file=sys.stderr)
        print("FATAL: refusing to write an outline that misplaces its anchors",
              file=sys.stderr)
        return False

    payload = json.dumps(geojson_for(rings, cfg), separators=(",", ":"))
    verts = sum(len(r) for r in rings)
    if check_only:
        if not os.path.exists(out_path):
            print("  %s: MISSING (%s)" % (slug, out_path), file=sys.stderr)
            return False
        with open(out_path) as f:
            shipped = f.read()
        if shipped != payload:
            print("  %s: shipped file differs from a fresh build (%d vs %d bytes)"
                  % (slug, len(shipped), len(payload)), file=sys.stderr)
            return False
        print("  %s: OK — matches a fresh build (%d ring(s), %d vertices, %d bytes)"
              % (slug, len(rings), verts, len(shipped)))
        return True

    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(payload)
    print("  %s -> data/app/%s-county-outline.json — %d ring(s), %d vertices, %d bytes, "
          "%d inside / %d outside anchors hold"
          % (slug, slug, len(rings), verts, len(payload),
             len(cfg["inside"]), len(cfg["outside"])))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("counties", nargs="*", help="county slugs (default: all known)")
    ap.add_argument("--check", action="store_true", help="verify shipped files, write nothing")
    ap.add_argument("--list", action="store_true", help="list known county slugs")
    args = ap.parse_args()

    if args.list:
        for slug, cfg in sorted(COUNTIES.items()):
            print("  %-10s %s (FIPS %s)" % (slug, cfg["name"], cfg["fips"]))
        return

    targets = args.counties or sorted(COUNTIES)
    unknown = [t for t in targets if t not in COUNTIES]
    if unknown:
        print("unknown county slug(s): %s; known: %s"
              % (unknown, sorted(COUNTIES)), file=sys.stderr)
        sys.exit(1)

    ok = True
    for slug in targets:
        try:
            ok = run(slug, args.check) and ok
        except Exception as e:
            print("  %s: FAILED — %s" % (slug, e), file=sys.stderr)
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

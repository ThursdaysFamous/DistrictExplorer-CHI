#!/usr/bin/env python3
"""
Metro Outline Builder (the scope mask's coverage geometry)
==========================================================
Builds data/app/metro-outline.json — the dissolved outline of the counties the
app actually serves — from Census TIGERweb. "Serves" means at least one
county-specific layer answers there, which as of 2026-07-30 is 24 counties: the
19 with their own dispatch entries, plus the five secondary counties of shipped
judicial circuits. It is deliberately ONE connected region: a county joins only
once it touches the ones already served.

THE COUNTY LIST HERE IS A CLAIM ABOUT COVERAGE, SO IT HAS TO TRACK THE LAYERS.
Research passes 2 and 3 shipped LaSalle, Kankakee, Boone and Grundy layers
without revisiting this list, and the wash went on greying out all four — it
told a Kankakee user "beyond here only the statewide layers answer" while five
Kankakee layers were answering. Nothing failed, because the anchors only assert
the counties already listed. So: **when a county gains a dispatch entry, add it
here and give it an INSIDE anchor in the same change** (§2.5 step 1). The
OUTSIDE list is the other half of that guard — a county named there can never
be quietly served, because shipping it would fail this build.

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
edges left to cancel. Disjoint regions would fall out of the same walk — each
closed ring is chained independently — but see METRO_COUNTY_FIPS: the served area
is kept connected on purpose, so that path stays unexercised.

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
# The counties the app serves: the original seven (Cook, DuPage, Will, Lake,
# Kane, McHenry, Kendall), then LaSalle, Kankakee, Boone and Grundy from research
# passes 2-3, then Winnebago, the Livingston -> McLean -> Logan -> Sangamon ->
# Macoupin bridge, and the Metro East (Madison, St. Clair) it was built to reach.
#
# THE LAST FIVE ARE NOT COUNTIES WITH THEIR OWN LAYERS — they are the SECONDARY
# counties of shipped judicial circuits: Bond sits in Madison's 3rd, and Jersey,
# Greene, Morgan and Scott in Sangamon's 7th. A resident there gets a real
# county-specific card (their judicial subcircuit), so the wash saying "beyond
# here only the statewide layers answer" was false for them in the other
# direction from the 2026-07-30 fix: not a served county greyed out by a stale
# list, but a served county nobody had thought to list, because coverage arrived
# through a layer keyed to a CIRCUIT rather than to a county.
#
# That is what this list means now, stated plainly: it is every county where at
# least one county-specific layer answers — not every county with its own
# dispatch entry. All five are contiguous with the served area, so the ring
# stays single.
#
# ONE RING IS A DELIBERATE CONSTRAINT, not a coincidence: a detached county would
# make the served area a set of islands, and the operator's call is that coverage
# grows as a connected region. The Livingston -> McLean -> Logan -> Sangamon ->
# Macoupin bridge exists for exactly that reason — built one contiguous county at
# a time, it carried the served area from the Wisconsin line to the Metro East
# without Madison and St. Clair ever being an island.
#
# group_rings() below nests rings correctly and emits a MultiPolygon if this ever
# does become disjoint — that machinery is in place, it is just not exercised yet.
METRO_COUNTY_FIPS = ("031", "043", "197", "097", "089", "111", "093",
                     "099", "091", "007", "063", "201", "105", "113", "107", "167", "117",
                     "119", "163", "037", "141",
                     # judicial-subcircuit secondary counties (see below)
                     "005", "083", "061", "137", "171")
STATE_FIPS = "17"

# Every county slug the app can dispatch a layer on -> its Census FIPS. This is
# the lookup that makes the county list above CHECKABLE rather than merely
# curated: scripts/validate_index.py reads both, scans index.html for the
# per-county dispatch entries it actually registers, and fails the merge gate if
# a county gained layers without being added to METRO_COUNTY_FIPS.
#
# That check exists because the alternative did not work. Until 2026-07-30 the
# only guard was the OUTSIDE anchor list, which catches a county only if someone
# had already thought to name it — so LaSalle, Kankakee, Boone and Grundy shipped
# layers and stayed greyed out for two research passes with nothing failing.
# Anchors verify the geometry; this verifies the LIST, which is a different job.
#
# METRO_COUNTY_FIPS may be a strict superset of these values: it also carries
# counties served only through a circuit-keyed layer (the judicial-subcircuit
# secondary counties), which have no dispatch entry of their own.
DISPATCH_COUNTY_FIPS = {
    "cook": "031", "dupage": "043", "will": "197", "lake": "097",
    "kane": "089", "mchenry": "111", "kendall": "093",
    "lasalle": "099", "kankakee": "091", "boone": "007", "grundy": "063",
    "winnebago": "201", "livingston": "105", "mclean": "113", "logan": "107",
    "sangamon": "167", "macoupin": "117", "madison": "119", "st-clair": "163",
    "dekalb": "037", "ogle": "141",
}

_UNLISTED = sorted(set(DISPATCH_COUNTY_FIPS.values()) - set(METRO_COUNTY_FIPS))
assert not _UNLISTED, (
    "DISPATCH_COUNTY_FIPS names county FIPS %s that METRO_COUNTY_FIPS omits — a "
    "county cannot be served and outside the coverage ring at the same time"
    % _UNLISTED)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "data", "app", "metro-outline.json")
WORKSHEET = os.path.join(REPO_ROOT, "metro-worksheet.json")

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
    "Ottawa (LaSalle)": (41.3456, -88.8426),
    "Kankakee (Kankakee)": (41.1200, -87.8612),
    "Belvidere (Boone)": (42.2639, -88.8443),
    "Morris (Grundy)": (41.3564, -88.4237),
    "Rockford (Winnebago)": (42.2714, -89.0940),
    "Pontiac (Livingston)": (40.8809, -88.6298),
    "Bloomington (McLean)": (40.4798, -88.9939),
    "Lincoln (Logan)": (40.1481, -89.3637),
    "Springfield (Sangamon)": (39.7990, -89.6440),
    "Carlinville (Macoupin)": (39.2798, -89.8818),
    "Edwardsville (Madison)": (38.8114, -89.9532),
    "Belleville (St. Clair)": (38.5136, -89.9842),
    "Sycamore (DeKalb)": (41.9889, -88.6868),
    "Oregon (Ogle)": (42.0148, -89.3323),
    # judicial-subcircuit secondary counties
    "Greenville (Bond, 3rd Circuit)": (38.8923, -89.4131),
    "Jerseyville (Jersey, 7th Circuit)": (39.1200, -90.3284),
    "Carrollton (Greene, 7th Circuit)": (39.3023, -90.4071),
    "Jacksonville (Morgan, 7th Circuit)": (39.7344, -90.2288),
    "Winchester (Scott, 7th Circuit)": (39.6297, -90.4563),
}
OUTSIDE = {
    # Waterloo (Monroe) and Carlyle (Clinton) sit just past the new southern and
    # eastern edges, so the Metro East is shown to have MOVED the boundary rather
    # than merely widened an untested interior — and either would fail the build
    # if a future county list quietly swallowed a neighbour.
    "Waterloo (Monroe)": (38.3359, -90.1498),
    "Carlyle (Clinton)": (38.6103, -89.3726),
    # Fayette and Pike border the newly added subcircuit counties but are in no
    # shipped circuit, so they must stay outside — the guard that keeps "a
    # circuit's secondary counties" from quietly becoming "everything nearby".
    "Vandalia (Fayette)": (38.9606, -89.0937),
    "Pittsfield (Pike)": (39.6078, -90.8051),
    "Milwaukee (WI)": (43.0389, -87.9065),
    # DeKalb used to sit here, described as "enclosed on three sides by served
    # counties and the one border-ring county with no locatable GIS". The second
    # half was wrong — the county runs a full ArcGIS Online org, it was simply
    # never found — and the day it gained dispatch entries this line failed the
    # build and forced the county list to be updated with it. That is the guard
    # doing its job, so the role is handed to the next counties out.
    #
    # Ogle followed DeKalb once its reapportionment resolution turned up, so the
    # frontier moves one county west and north again. Lee, Stephenson, Carroll
    # and Whiteside now ring the served area; each is a recorded gap.
    "Dixon (Lee)": (41.8425, -89.4814),
    "Freeport (Stephenson)": (42.2967, -89.6212),
    "Mount Carroll (Carroll)": (42.0949, -89.9777),
    "Sterling (Whiteside)": (41.7883, -89.6954),
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


def group_rings(rings):
    """Nest each ring under the ring that encloses it — outers, then their holes.

    Needed from pass 4 on, when the served area stopped being one region. A
    two-ring Polygon means "ring 2 is a HOLE in ring 1", so emitting the detached
    Madison/St. Clair region that way would have claimed a hole in the Chicago
    metro. The wash renders identically either way (it flattens every ring into a
    cut-out), which is precisely why this had to be reasoned about rather than
    eyeballed: the bug would be invisible on the map and wrong to anything that
    ever runs a containment test — including the app's own pointInGeometry, which
    would answer False for every point in Madison County.
    """
    ordered = sorted(rings, key=len, reverse=True)
    polys = []  # [outer, hole, hole, ...]
    for ring in ordered:
        lng, lat = ring[0][0], ring[0][1]
        for poly in polys:
            if point_in_rings(lat, lng, [poly[0]]):
                poly.append(ring)  # enclosed -> a hole in that outer
                break
        else:
            polys.append([ring])
    return polys


def check_envelopes(rings):
    """The input shell must reach at least as far as the data does.

    METRO_BBOX (geocoder viewbox + the geolocate gate) and PERMALINK_GATE (the
    #point= sanity bound) are hand-set values in metro-worksheet.json that
    describe "where we serve" — and they do not move when a county is added, so
    they go stale silently and in a way no other gate sees. That has now bitten
    three times: LaSalle and Kankakee fell outside METRO_BBOX from research pass
    2 onward, Rockford's permalink was being dropped until pass 4 widened the
    gate, and Bloomington's was dropped again one county later.

    The failure is invisible because it is a REJECTION: a shared #point= link
    silently loses its point, and "Use my location" in a served county reports
    the user is outside the covered area. Nothing errors. So this turns it into a
    build failure — add a county whose geometry pokes outside either envelope and
    the outline build stops until the worksheet is widened to match.

    Checked against the SIMPLIFIED rings, i.e. the geometry actually shipped.
    """
    xs = [p[0] for ring in rings for p in ring]
    ys = [p[1] for ring in rings for p in ring]
    env = {"minLng": min(xs), "maxLng": max(xs), "minLat": min(ys), "maxLat": max(ys)}
    try:
        with open(WORKSHEET, encoding="utf-8") as f:
            worksheet = json.load(f)
    except (IOError, ValueError) as exc:
        return ["could not read metro-worksheet.json (%s)" % exc]

    problems = []
    for key in ("metro_bbox", "permalink_gate"):
        box = worksheet.get(key)
        if not box:
            problems.append("metro-worksheet.json has no %s" % key)
            continue
        for edge, cmp_ in (("minLng", "gt"), ("minLat", "gt"), ("maxLng", "lt"), ("maxLat", "lt")):
            if edge not in box:
                problems.append("%s is missing %s" % (key, edge))
                continue
            too_tight = box[edge] > env[edge] if cmp_ == "gt" else box[edge] < env[edge]
            if too_tight:
                problems.append(
                    "%s.%s is %.4f but the served area reaches %.4f — widen it, or a "
                    "point there is silently rejected" % (key, edge, box[edge], env[edge]))
    return problems


def build_geojson(rings):
    polys = group_rings(rings)
    geometry = ({"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1
                else {"type": "MultiPolygon", "coordinates": polys})
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "%d-county coverage area" % len(METRO_COUNTY_FIPS)},
            "geometry": geometry,
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
        # rings_of() flattens Polygon and MultiPolygon alike, so the anchor test
        # reads the file the same way whether or not the served area is one region.
        rings = rings_of(shipped["features"][0])
        problems = validate(rings) + check_envelopes(rings)
        for p in problems:
            print("FAIL: %s" % p, file=sys.stderr)
        if problems:
            sys.exit(1)
        print("metro-outline: OK — %d ring(s), %d vertices, all %d inside / %d outside "
              "anchors correct" % (len(rings), sum(len(r) for r in rings),
                                   len(INSIDE), len(OUTSIDE)), file=sys.stderr)
        return

    rings = [simplify(r) for r in dissolve(fetch_counties())]
    problems = validate(rings) + check_envelopes(rings)
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

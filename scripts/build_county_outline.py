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
    DISPATCH_COUNTY_FIPS, HEADERS, REQUEST_TIMEOUT, SIMPLIFY_TOLERANCE_M,
    STATE_FIPS, TIGERWEB, point_in_rings, rings_of, simplify,
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
    # Boone and Grundy: both border-ring counties (the ring is Boone, DeKalb,
    # Grundy, Kankakee, LaSalle). Anchor coordinates geocoded, not recalled.
    "boone": {
        "fips": "007",
        "name": "Boone County",
        "inside": [
            (42.2580, -88.8417, "Belvidere (county seat)"),
            (42.3684, -88.8220, "Poplar Grove"),
            (42.3994, -88.7406, "Capron"),
        ],
        "outside": [
            (42.2714, -89.0940, "Rockford — Winnebago County"),
            (42.2501, -88.6081, "Marengo — McHenry County"),
            (42.0972, -88.6929, "Genoa — DeKalb County"),
        ],
    },
    "grundy": {
        "fips": "063",
        "name": "Grundy County",
        "inside": [
            (41.3574, -88.4215, "Morris (county seat)"),
            (41.2878, -88.2855, "Coal City"),
            (41.4553, -88.2617, "Minooka"),
        ],
        "outside": [
            (41.0945, -88.4251, "Dwight — Livingston County"),
            (41.3107, -88.6091, "Seneca — LaSalle County"),
            (41.1254, -87.8487, "Kankakee — Kankakee County"),
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
    # Research pass 4 — the first counties that are NOT contiguous with the metro.
    # Every anchor below was geocoded and its returned county/state read back, not
    # recalled; the "Madison County" and "St. Clair County" names each exist in
    # several states, and DeKalb already showed how far a same-name trap can get.
    "winnebago": {
        "fips": "201",
        "name": "Winnebago County",
        "inside": [
            (42.2714, -89.0940, "Rockford (county seat)"),
            (42.3200, -89.0582, "Loves Park"),
            (42.4931, -89.0368, "South Beloit"),
            (42.3139, -89.3594, "Pecatonica"),
        ],
        "outside": [
            (42.2580, -88.8417, "Belvidere — Boone County"),
            (42.1270, -89.2557, "Byron — Ogle County"),
            (42.2967, -89.6212, "Freeport — Stephenson County"),
            (42.5083, -89.0318, "Beloit — Rock County, Wisconsin"),
        ],
    },
    # The first bridge county toward the Metro East. It publishes no GIS at all,
    # so its board districts are built from TIGER townships
    # (build_livingston_board_districts.py); this outline is still a plain TIGER
    # county boundary like every other, and gates the dispatch entry.
    "livingston": {
        "fips": "105",
        "name": "Livingston County",
        "inside": [
            (40.8809, -88.6298, "Pontiac (county seat)"),
            (41.0945, -88.4251, "Dwight"),
            (40.7473, -88.5148, "Fairbury"),
            (40.8781, -88.8612, "Flanagan"),
        ],
        "outside": [
            (41.1206, -88.8351, "Streator — LaSalle County"),
            (41.3574, -88.4215, "Morris — Grundy County"),
            (41.1254, -87.8487, "Kankakee — Kankakee County"),
            (40.4842, -88.9937, "Bloomington — McLean County"),
        ],
    },
    "mclean": {
        "fips": "113",
        "name": "McLean County",
        "inside": [
            (40.4798, -88.9939, "Bloomington (county seat)"),
            (40.5093, -88.9844, "Normal"),
            (40.6414, -88.7834, "Lexington"),
            (40.3520, -88.7642, "Le Roy"),
        ],
        "outside": [
            (40.8809, -88.6298, "Pontiac — Livingston County"),
            (40.1526, -88.9607, "Clinton — DeWitt County"),
            (40.1481, -89.3637, "Lincoln — Logan County"),
            (40.4653, -88.3759, "Gibson City — Ford County"),
            (40.7213, -89.2727, "Eureka — Woodford County"),
        ],
    },
    "logan": {
        "fips": "107",
        "name": "Logan County",
        "inside": [
            (40.1481, -89.3637, "Lincoln (county seat)"),
            (40.0109, -89.2823, "Mount Pulaski"),
            (40.2597, -89.2332, "Atlanta"),
            (40.0207, -89.4822, "Elkhart"),
        ],
        "outside": [
            (40.4798, -88.9939, "Bloomington — McLean County"),
            (40.0117, -89.8482, "Petersburg — Menard County"),
            (40.3725, -89.5473, "Delavan — Tazewell County"),
            (40.1526, -88.9607, "Clinton — DeWitt County"),
            (39.5487, -89.2942, "Taylorville — Christian County"),
        ],
    },
    "sangamon": {
        "fips": "167",
        "name": "Sangamon County",
        "inside": [
            (39.7990, -89.6440, "Springfield (county seat, state capital)"),
            (39.6762, -89.7045, "Chatham"),
            (39.7495, -89.5318, "Rochester"),
            (39.5917, -89.5804, "Pawnee"),
        ],
        "outside": [
            (40.1481, -89.3637, "Lincoln — Logan County"),
            (40.0117, -89.8482, "Petersburg — Menard County"),
            (39.5487, -89.2942, "Taylorville — Christian County"),
            (39.7344, -90.2288, "Jacksonville — Morgan County"),
            (39.5009, -89.7679, "Virden — Macoupin County"),
        ],
    },
    "macoupin": {
        "fips": "117",
        "name": "Macoupin County",
        "inside": [
            (39.2798, -89.8818, "Carlinville (county seat)"),
            (39.1267, -89.8163, "Gillespie"),
            (39.0122, -89.7885, "Staunton"),
            (39.4459, -89.7782, "Girard"),
        ],
        "outside": [
            (39.7990, -89.6440, "Springfield — Sangamon County"),
            (39.1769, -89.6556, "Litchfield — Montgomery County"),
            (39.1200, -90.3284, "Jerseyville — Jersey County"),
            (38.8114, -89.9532, "Edwardsville — Madison County"),
        ],
    },
    "madison": {
        "fips": "119",
        "name": "Madison County",
        "inside": [
            (38.8114, -89.9532, "Edwardsville (county seat)"),
            (38.8909, -90.1843, "Alton"),
            (38.7014, -90.1487, "Granite City"),
            (38.7396, -89.6715, "Highland"),
        ],
        "outside": [
            (38.5136, -89.9842, "Belleville — St. Clair County"),
            (38.8923, -89.4131, "Greenville — Bond County"),
            (39.2798, -89.8818, "Carlinville — Macoupin County"),
            (39.1200, -90.3284, "Jerseyville — Jersey County"),
            (38.6254, -90.1900, "St. Louis, Missouri (across the river)"),
        ],
    },
    "st-clair": {
        "fips": "163",
        "name": "St. Clair County",
        "inside": [
            (38.5136, -89.9842, "Belleville (county seat)"),
            (38.6269, -90.1597, "East St. Louis"),
            (38.5923, -89.9112, "O'Fallon"),
            (38.4903, -89.7932, "Mascoutah"),
        ],
        "outside": [
            (38.8114, -89.9532, "Edwardsville — Madison County"),
            (38.3359, -90.1498, "Waterloo — Monroe County"),
            (38.6103, -89.3726, "Carlyle — Clinton County"),
            (38.3435, -89.3810, "Nashville — Washington County"),
            (38.6254, -90.1900, "St. Louis, Missouri (across the river)"),
        ],
    },
    # DeKalb closes the notch the ring had been wrapped around since pass 2:
    # Boone to the north, McHenry at the north-east corner, Kane to the east,
    # Kendall to the south-east and LaSalle to the south were all already served.
    # Only the western edge (Ogle, Lee) is a genuine frontier, so those two get
    # the OUTSIDE anchors that matter.
    "dekalb": {
        "fips": "037",
        "name": "DeKalb County",
        "inside": [
            (41.9889, -88.6868, "Sycamore (county seat)"),
            (41.8903, -88.7714, "DeKalb"),
            (41.6459, -88.6217, "Sandwich"),
            (42.0972, -88.6929, "Genoa"),
            (41.7717, -88.7737, "Waterman"),
        ],
        "outside": [
            (41.9239, -89.0687, "Rochelle — Ogle County"),
            (41.8425, -89.4814, "Dixon — Lee County"),
            (42.2580, -88.8417, "Belvidere — Boone County"),
            (41.8922, -88.4723, "Elburn — Kane County"),
            (41.6629, -88.5367, "Plano — Kendall County"),
            (41.5895, -88.9220, "Earlville — LaSalle County"),
            (42.2501, -88.6081, "Marengo — McHenry County"),
        ],
    },
    # Ogle joins on its eastern edge (Boone, Winnebago) and its south-east
    # (DeKalb, LaSalle). Lee, Stephenson, Carroll and Whiteside are the frontier
    # now, so those four carry the OUTSIDE anchors that matter.
    "ogle": {
        "fips": "141",
        "name": "Ogle County",
        "inside": [
            (42.0148, -89.3323, "Oregon (county seat)"),
            (41.9239, -89.0687, "Rochelle"),
            (42.1270, -89.2557, "Byron"),
            (41.9861, -89.5793, "Polo"),
            (42.0503, -89.4312, "Mount Morris"),
            (42.1262, -89.5791, "Forreston"),
        ],
        "outside": [
            (41.8425, -89.4814, "Dixon — Lee County"),
            (42.2967, -89.6212, "Freeport — Stephenson County"),
            (42.0949, -89.9777, "Mount Carroll — Carroll County"),
            (41.7883, -89.6954, "Sterling — Whiteside County"),
            (42.2714, -89.0940, "Rockford — Winnebago County"),
            (42.2580, -88.8417, "Belvidere — Boone County"),
            (41.9889, -88.6868, "Sycamore — DeKalb County"),
            (41.5473, -89.1176, "Mendota — LaSalle County"),
        ],
    },
    # Stephenson sits on the Wisconsin line; its southern and eastern neighbours
    # (Ogle, Winnebago) are served, so Carroll, Jo Daviess and the state line
    # carry the OUTSIDE anchors that matter.
    "stephenson": {
        "fips": "177",
        "name": "Stephenson County",
        "inside": [
            (42.2967, -89.6212, "Freeport (county seat)"),
            (42.3805, -89.8221, "Lena"),
            (42.4680, -89.6449, "Orangeville"),
            (42.2653, -89.8260, "Pearl City"),
            (42.4927, -89.7918, "Winslow"),
            (42.4225, -89.4137, "Davis"),
        ],
        "outside": [
            (42.2714, -89.0940, "Rockford — Winnebago County"),
            (42.1270, -89.2557, "Byron — Ogle County"),
            (42.0949, -89.9777, "Mount Carroll — Carroll County"),
            (42.4157, -90.4295, "Galena — Jo Daviess County"),
            (42.0945, -90.1568, "Savanna — Carroll County"),
        ],
    },
    # Carroll reaches the Mississippi, so its western neighbour is Iowa rather
    # than another Illinois county — the state line is the anchor that matters
    # there, and Jo Daviess, Stephenson, Ogle and Whiteside ring the rest.
    "carroll": {
        "fips": "015",
        "name": "Carroll County",
        "inside": [
            (42.0949, -89.9777, "Mount Carroll (county seat)"),
            (42.0945, -90.1568, "Savanna"),
            (42.1021, -89.8330, "Lanark"),
            (41.9589, -90.0993, "Thomson"),
            (41.9634, -89.7746, "Milledgeville"),
            (42.1547, -89.7398, "Shannon"),
        ],
        "outside": [
            (42.4157, -90.4295, "Galena — Jo Daviess County"),
            (42.2967, -89.6212, "Freeport — Stephenson County"),
            (42.0503, -89.4312, "Mount Morris — Ogle County"),
            (41.7883, -89.6954, "Sterling — Whiteside County"),
            (42.2587, -90.4231, "Bellevue, Iowa (across the Mississippi)"),
        ],
    },
    # Lee and Whiteside close the north-western frontier. Every anchor below is
    # DERIVED, not recalled: each `inside` point is the centroid of that place's
    # largest TIGER ring, tested against the county's own TIGER outline, and each
    # `outside` point is the place in the named neighbour whose centroid sits
    # nearest the shared border while testing outside this county. Anchors
    # written from memory put two Stephenson villages in the wrong townships;
    # they are computed now.
    "lee": {
        "fips": "103",
        "name": "Lee County",
        "inside": [
            (41.8493, -89.4876, "Dixon (county seat)"),
            (41.7280, -89.3784, "Amboy"),
            (41.8652, -89.2225, "Ashton"),
            (41.6870, -88.9814, "Paw Paw"),
            (41.6444, -89.2312, "Sublette"),
            (41.7966, -89.6021, "Nelson"),
        ],
        # Rochelle is NOT an inside anchor: it straddles the Ogle line and its
        # centroid falls in Ogle, which is why it appears below instead.
        "outside": [
            (41.9154, -89.0599, "Rochelle — Ogle County"),
            (41.7661, -88.8748, "Shabbona — DeKalb County"),
            (41.5858, -88.9176, "Earlville — LaSalle County"),
            (41.5558, -89.4632, "Ohio — Bureau County"),
            (41.6073, -89.6880, "Deer Grove — Whiteside County"),
        ],
    },
    # Rock Island is the first served county on the Mississippi and the first
    # whose neighbours include another STATE — the Iowa Quad Cities sit across
    # the river, outside every layer the app answers. Its outside anchors are
    # therefore Illinois-only by construction (the derivation picks places in
    # neighbouring Illinois counties); the river edge is tested by the inside
    # anchors that hug it, Andalusia and Rock Island itself.
    "rock-island": {
        "fips": "161",
        "name": "Rock Island County",
        "inside": [
            (41.4852, -90.5742, "Rock Island (county seat)"),
            (41.4975, -90.4925, "Moline"),
            (41.5152, -90.4075, "East Moline"),
            (41.4430, -90.7209, "Andalusia"),
            (41.6127, -90.3308, "Port Byron"),
            (41.3310, -90.6724, "Reynolds"),
        ],
        "outside": [
            (41.7902, -90.2160, "Albany — Whiteside County"),
            (41.5048, -90.3159, "Cleveland — Henry County"),
            (41.3054, -90.4931, "Sherrard — Mercer County"),
        ],
    },
    "whiteside": {
        "fips": "195",
        "name": "Whiteside County",
        "inside": [
            (41.8090, -89.9686, "Morrison (county seat)"),
            (41.8024, -89.6993, "Sterling"),
            (41.7743, -89.6882, "Rock Falls"),
            (41.8632, -90.1557, "Fulton"),
            (41.6751, -89.9343, "Prophetstown"),
            (41.6598, -90.0783, "Erie"),
        ],
        "outside": [
            (41.9633, -89.7719, "Milledgeville — Carroll County"),
            (41.9857, -89.5812, "Polo — Ogle County"),
            (41.7966, -89.6021, "Nelson — Lee County"),
            (41.5558, -89.5920, "Walnut — Bureau County"),
            (41.5217, -89.9129, "Hooppole — Henry County"),
            (41.6101, -90.1763, "Hillsdale — Rock Island County"),
        ],
    },
}


# The two tables must agree about what a county's FIPS is. build_metro_outline's
# DISPATCH_COUNTY_FIPS is authoritative (validate_index.py checks the app
# against it); this catches a typo here before it produces a correct-LOOKING
# outline for the wrong county — the class of error the DeKalb-Georgia near-miss
# would have been.
_CONFLICTS = sorted(
    "%s: this table says %s, DISPATCH_COUNTY_FIPS says %s"
    % (slug, spec["fips"], DISPATCH_COUNTY_FIPS[slug])
    for slug, spec in COUNTIES.items()
    if slug in DISPATCH_COUNTY_FIPS and spec["fips"] != DISPATCH_COUNTY_FIPS[slug])
assert not _CONFLICTS, "county FIPS disagree — " + "; ".join(_CONFLICTS)


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

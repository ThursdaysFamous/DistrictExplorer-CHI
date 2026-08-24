#!/usr/bin/env python3
"""One-command bootstrap for a brand-new state fork of District Explorer.

Run this ONCE, right after creating a repository from the state template:

    python3 scripts/bootstrap_state.py \\
        --state-fips 18 --state-name Indiana \\
        --repo owner/DistrictExplorer-IN --domain in.example.com \\
        --brand-name "Indiana District Explorer" \\
        [--exports-name InExplorer] [--goatcounter-url URL] \\
        [--portal-host data.example.gov] \\
        [--palette '#4A90D9,#2C5F9E,#D97706,#B45309']

What it does, in order (every network fetch is staged in memory and NOTHING
is written until every fetch has succeeded):

  1. Fetches the state polygon, every county, the U.S. House districts and
     the unified school districts from Census TIGERweb (layer indexes are
     discovered from each service's own layer list, never hardcoded blind).
  2. Writes the four pre-built boundary files under data/app/, plus
     data/state/state.json + counties.json, then builds the congressional
     roster via scripts/build_congress_roster.py (which reads state.json).
  3. Derives the fork's facts — bbox, center, permalink gate, an anchor
     point inside the most-populous county, its expected classifications,
     and a negative point just outside the state — verifying each with its
     own ray-cast point-in-polygon against the downloaded geometry.
  4. Seeds data/app/coverage-gaps.json with one honest starter record.
  5. Rewrites metro-worksheet.json (all template stand-in values replaced),
     fills every placeholder token across the tree, and replaces the
     template stand-ins spliced into scripts/indexnow_submit.py and
     scripts/validate_sources.py (a fresh IndexNow key is generated here).
  6. Regenerates every GENERATED region and runs the gate battery:
     generate_metro_files --check, check_template_placeholders,
     validate_index, check_engine_parity, node --check on the smoke test.

Maintenance modes (run any time later; both read data/state/state.json):

    python3 scripts/bootstrap_state.py --refresh-congress-roster
    python3 scripts/bootstrap_state.py --refresh-boundaries

--refresh-congress-roster rebuilds data/app/congress-roster.json and
re-validates. --refresh-boundaries re-fetches the four TIGERweb-derived
files, re-tightens the worksheet's feature-count bounds, re-verifies the
anchor and negative points against the fresh geometry (re-deriving them if
a redistricting moved a line under them), regenerates and re-validates.

Stdlib only. Works from the repo root or from scripts/ (paths resolve from
this file). Every count guard prints what it actually got.
"""

import argparse
import datetime
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPTS_DIR)
APP_DIR = os.path.join(REPO, "data", "app")
STATE_DIR = os.path.join(REPO, "data", "state")
WORKSHEET_PATH = os.path.join(REPO, "metro-worksheet.json")

TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
STATE_COUNTY_SERVICE = TIGERWEB + "State_County/MapServer"
LEGISLATIVE_SERVICE = TIGERWEB + "Legislative/MapServer"
SCHOOL_SERVICE = TIGERWEB + "School/MapServer"

# FIPS -> USPS for the 50 states, DC, and the inhabited territories.
FIPS_TO_USPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
    "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI",
}

# ---------------------------------------------------------------------------
# Template stand-in vocabulary. These strings are CONSTRUCTED rather than
# written literally because scripts/check_template_placeholders.py scans this
# very file after bootstrap — a raw literal here would fail the gate it exists
# to satisfy. (Same reason the token helper below assembles the {{...}} form.)
# ---------------------------------------------------------------------------
SENT_SLUG = "new" + "state"                    # the template's metro slug
SENT_NAME = SENT_SLUG.capitalize()             # its display name
SENT_DOMAIN = SENT_SLUG + ".example"           # its canonical host
SENT_PORTAL = "data." + SENT_DOMAIN            # its Socrata portal host
SENT_OWNER = SENT_SLUG + "-owner"              # its GitHub owner
SENT_REPO_NAME = SENT_SLUG + "-repo"           # its GitHub repo name
SENT_EXPORTS = "State" + "Explorer"            # its debug namespace
SENT_DATE = "January 1, " + "2000"             # its verified-date epoch
SENT_INDEXNOW_KEY = "0" * 32                   # the scaffold's IndexNow key


def tok(name):
    """The doubled-brace placeholder form of a token name, assembled at
    runtime so no token literal appears in this file."""
    return "{{" + name + "}}"


def fail(msg):
    sys.stderr.write("bootstrap-state: FATAL — %s\n" % msg)
    sys.exit(1)


def info(msg):
    print("bootstrap-state: %s" % msg)


# ---------------------------------------------------------------------------
# HTTP (stdlib urllib; the environment's proxy configuration applies as-is)
# ---------------------------------------------------------------------------

def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers={
        "User-Agent": "District Explorer state-fork bootstrap (stdlib urllib)"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url, tries=3):
    """GET url as JSON with retries + backoff. An HTTP-200 Esri error envelope
    ({"error": {...}}) counts as a failure — ArcGIS answers 200 for throttling
    and bad parameters, and caching that would ship an empty layer."""
    delay = 2
    last = None
    for attempt in range(1, tries + 1):
        try:
            payload = json.loads(http_get(url).decode("utf-8"))
            if isinstance(payload, dict) and "error" in payload:
                raise RuntimeError("HTTP-200 JSON error envelope: %r"
                                   % (payload["error"],))
            return payload
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 — every failure retries alike
            last = exc
            if attempt < tries:
                info("fetch failed (%s/%s) for %s — %s; retrying in %ss"
                     % (attempt, tries, url, exc, delay))
                time.sleep(delay)
                delay *= 2
    fail("giving up on %s after %d tries: %s" % (url, tries, last))


def query_geojson(service, layer_idx, fips, out_fields, label, precision=5):
    where = urllib.parse.quote("STATE='%s'" % fips)
    url = ("%s/%d/query?where=%s&outFields=%s&outSR=4326&f=geojson"
           "&geometryPrecision=%d"
           % (service, layer_idx, where, urllib.parse.quote(out_fields),
              precision))
    data = fetch_json(url)
    feats = data.get("features")
    if not isinstance(feats, list):
        fail("%s returned no features array (got keys %s)"
             % (label, sorted(data.keys())))
    info("%s: fetched %d feature(s) from %s layer %d"
         % (label, len(feats), service.rsplit("/", 2)[-2], layer_idx))
    return data


def query_attributes(service, layer_idx, fips, out_fields):
    where = urllib.parse.quote("STATE='%s'" % fips)
    url = ("%s/%d/query?where=%s&outFields=%s&returnGeometry=false&f=json"
           % (service, layer_idx, where, urllib.parse.quote(out_fields)))
    data = fetch_json(url)
    return [f.get("attributes") or {} for f in data.get("features") or []]


def service_layer_index(service, want, label):
    """Discover a layer index from the service's own layer list — the first
    layer whose name satisfies `want` (a predicate on the lowercased name)."""
    meta = fetch_json(service + "?f=json")
    for layer in meta.get("layers") or []:
        name = str(layer.get("name") or "")
        if want(name.lower()):
            info("%s: using layer %s (%r)" % (label, layer.get("id"), name))
            return int(layer["id"])
    fail("%s: no matching layer in %s — the service's layer list changed"
         % (label, service))


def layer_field_names(service, layer_idx):
    meta = fetch_json("%s/%d?f=json" % (service, layer_idx))
    return [str(f.get("name") or "") for f in meta.get("fields") or []]


# ---------------------------------------------------------------------------
# Geometry (own ray-cast point-in-polygon; no dependencies)
# ---------------------------------------------------------------------------

def polygon_sets(geometry):
    """[[ring, ...], ...] — one ring-list per polygon, holes included."""
    if not geometry:
        return []
    gtype = geometry.get("type")
    if gtype == "Polygon":
        return [geometry.get("coordinates") or []]
    if gtype == "MultiPolygon":
        return geometry.get("coordinates") or []
    return []


def ring_crossings(lng, lat, ring):
    """Ray-cast crossing count for one linear ring ([lng, lat] vertices)."""
    crossings = 0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if (y1 > lat) != (y2 > lat):
            x_at = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lng < x_at:
                crossings += 1
    return crossings


def point_in_geometry(lat, lng, geometry):
    """Even-odd point-in-polygon over a GeoJSON (Multi)Polygon: inside a
    polygon iff the total crossing count over its rings (outer + holes) is
    odd; inside the geometry iff inside any of its polygons."""
    for rings in polygon_sets(geometry):
        crossings = 0
        for ring in rings:
            crossings += ring_crossings(lng, lat, ring)
        if crossings % 2 == 1:
            return True
    return False


def geometry_bbox(geometry):
    min_lng = min_lat = float("inf")
    max_lng = max_lat = float("-inf")
    for rings in polygon_sets(geometry):
        for ring in rings:
            for pt in ring:
                min_lng = min(min_lng, pt[0])
                max_lng = max(max_lng, pt[0])
                min_lat = min(min_lat, pt[1])
                max_lat = max(max_lat, pt[1])
    if min_lng > max_lng:
        fail("geometry has no coordinates to take a bbox of")
    return min_lng, min_lat, max_lng, max_lat


def feature_containing(geojson, lat, lng):
    """First feature whose geometry contains the point (bbox reject first)."""
    for feat in geojson.get("features") or []:
        geom = feat.get("geometry")
        if not geom:
            continue
        bb = feat.get("__bbox")
        if bb is None:
            bb = geometry_bbox(geom)
            feat["__bbox"] = bb
        if lng < bb[0] or lng > bb[2] or lat < bb[1] or lat > bb[3]:
            continue
        if point_in_geometry(lat, lng, geom):
            return feat
    return None


def strip_bbox_cache(geojson):
    for feat in geojson.get("features") or []:
        feat.pop("__bbox", None)


def largest_outer_ring(geometry):
    best, best_len = None, -1
    for rings in polygon_sets(geometry):
        if rings and len(rings[0]) > best_len:
            best, best_len = rings[0], len(rings[0])
    return best or []


def interior_point(feature, hint_lat=None, hint_lng=None):
    """A point inside the feature: the caller's hint (e.g. the Census interior
    point) if it verifies, else the largest ring's vertex mean, else a coarse
    grid scan over the bbox. Always verified by point_in_geometry."""
    geom = feature.get("geometry")
    if hint_lat is not None and hint_lng is not None:
        if point_in_geometry(hint_lat, hint_lng, geom):
            return hint_lat, hint_lng
    ring = largest_outer_ring(geom)
    if ring:
        mean_lng = sum(p[0] for p in ring) / len(ring)
        mean_lat = sum(p[1] for p in ring) / len(ring)
        if point_in_geometry(mean_lat, mean_lng, geom):
            return mean_lat, mean_lng
    bb = geometry_bbox(geom)
    for divisions in (11, 23, 47):
        for i in range(1, divisions):
            for j in range(1, divisions):
                lat = bb[1] + (bb[3] - bb[1]) * i / divisions
                lng = bb[0] + (bb[2] - bb[0]) * j / divisions
                if point_in_geometry(lat, lng, geom):
                    return lat, lng
    return None


def props_ci(props, *names):
    """Case-insensitive property lookup, first match wins."""
    lowered = {str(k).lower(): v for k, v in (props or {}).items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


# ---------------------------------------------------------------------------
# Congressional district codes
# ---------------------------------------------------------------------------

def district_code(props):
    """The raw district code ("07", "00" at-large, "ZZ" water) — the CD###
    field TIGERweb renames each Congress, else BASENAME."""
    for key, value in (props or {}).items():
        if re.match(r"^CD\d*(FP)?$", str(key), re.IGNORECASE):
            if value not in (None, ""):
                return str(value)
    base = props_ci(props, "BASENAME")
    return None if base in (None, "") else str(base)


def numeric_district(props):
    """"07" -> "7", "00" -> "0" (the roster's at-large key); None for ZZ."""
    code = district_code(props)
    if code is not None and code.isdigit():
        return str(int(code))
    return None


# ---------------------------------------------------------------------------
# JSON writers
# ---------------------------------------------------------------------------

def normalized_collection(geojson, sort_key):
    feats = []
    for feat in geojson.get("features") or []:
        feats.append({
            "type": "Feature",
            "properties": feat.get("properties") or {},
            "geometry": feat.get("geometry"),
        })
    feats.sort(key=sort_key)
    return {"type": "FeatureCollection", "features": feats}


def write_json(path, data, compact=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    info("wrote %s" % os.path.relpath(path, REPO))


# ---------------------------------------------------------------------------
# The TIGERweb download set (shared by full bootstrap and --refresh-boundaries)
# ---------------------------------------------------------------------------

def fetch_boundary_set(fips, state_name):
    """All four TIGERweb layers, staged in memory. Returns a dict of the
    downloaded collections plus the derived counts. Nothing is written here —
    the caller writes only after this returns, so a mid-run failure leaves the
    tree untouched (all-or-nothing)."""
    states_idx = service_layer_index(
        STATE_COUNTY_SERVICE, lambda n: n == "states", "state outline")
    counties_idx = service_layer_index(
        STATE_COUNTY_SERVICE, lambda n: n == "counties", "counties")
    congress_idx = service_layer_index(
        LEGISLATIVE_SERVICE, lambda n: "congressional" in n, "U.S. House")
    school_idx = service_layer_index(
        SCHOOL_SERVICE, lambda n: "unified" in n, "unified school districts")

    state_fc = query_geojson(STATE_COUNTY_SERVICE, states_idx, fips,
                             "GEOID,NAME,STATE", "state outline")
    if len(state_fc["features"]) != 1:
        fail("state outline: expected exactly 1 feature for STATE='%s', got %d"
             % (fips, len(state_fc["features"])))
    state_feat = state_fc["features"][0]
    fetched_name = props_ci(state_feat.get("properties"), "NAME")
    if fetched_name and str(fetched_name).lower() != state_name.lower():
        info("NOTE — TIGERweb names STATE='%s' %r; you passed --state-name %r"
             % (fips, fetched_name, state_name))

    counties = query_geojson(STATE_COUNTY_SERVICE, counties_idx, fips,
                             "GEOID,NAME,BASENAME,STATE,COUNTY", "counties")
    n_counties = len(counties["features"])
    if n_counties < 1:
        fail("counties: got 0 features for STATE='%s' (guard: >= 1)" % fips)
    info("counties: %d feature(s) (guard: >= 1)" % n_counties)

    congress = query_geojson(LEGISLATIVE_SERVICE, congress_idx, fips,
                             "*", "U.S. House districts")
    # Keep only the compact identity properties (the CD### code field, NAME,
    # BASENAME, GEOID, STATE) — the reference fork's file shape.
    for feat in congress["features"]:
        props = feat.get("properties") or {}
        kept = {}
        for key, value in props.items():
            if re.match(r"^CD\d*(FP)?$", str(key), re.IGNORECASE) or \
               str(key).upper() in ("NAME", "BASENAME", "GEOID", "STATE"):
                kept[key] = value
        feat["properties"] = kept
    n_congress = len(congress["features"])
    house_districts = sum(
        1 for f in congress["features"]
        if numeric_district(f.get("properties")) is not None)
    if house_districts < 1:
        fail("U.S. House: %d feature(s) but no numeric district code among "
             "them — cannot size the delegation" % n_congress)
    info("U.S. House: %d feature(s), %d numbered district(s) "
         "(water/undefined pseudo-districts like ZZ ship but don't count)"
         % (n_congress, house_districts))

    schools = query_geojson(SCHOOL_SERVICE, school_idx, fips,
                            "GEOID,NAME,STATE", "unified school districts")
    n_schools = len(schools["features"])
    if n_schools == 0:
        fail("unified school districts: 0 features for STATE='%s'. This "
             "state has no unified (K-12) school districts, so the starter "
             "school layer cannot ship — swap school-district-unified for "
             "the elementary + secondary tilings (TIGERweb School layers 1 "
             "and 2) before bootstrapping; an empty layer is never shipped."
             % fips)
    info("unified school districts: %d feature(s) (guard: >= 1)" % n_schools)

    # County population + Census interior points, for the anchor derivation.
    # Optional: a vintage without POP100 falls back to the state's center.
    county_attrs = []
    try:
        field_names = set(
            n.upper() for n in layer_field_names(STATE_COUNTY_SERVICE,
                                                 counties_idx))
        wanted = ["GEOID"]
        pop_field = next((f for f in ("POP100", "POP") if f in field_names),
                         None)
        if pop_field:
            wanted.append(pop_field)
        for f in ("INTPTLAT", "INTPTLON", "CENTLAT", "CENTLON"):
            if f in field_names:
                wanted.append(f)
        county_attrs = query_attributes(STATE_COUNTY_SERVICE, counties_idx,
                                        fips, ",".join(wanted))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — attrs are an optional refinement
        info("county attribute query failed (%s) — falling back to the "
             "state-center anchor rule" % exc)

    return {
        "state_feature": state_feat,
        "counties": counties,
        "congress": congress,
        "schools": schools,
        "county_attrs": county_attrs,
        "n_counties": n_counties,
        "n_congress": n_congress,
        "n_schools": n_schools,
        "house_districts": house_districts,
    }


# ---------------------------------------------------------------------------
# Derivations
# ---------------------------------------------------------------------------

def floor2(v):
    # pre-round to dodge float artifacts (10.05 * 100 == 1005.0000000000001)
    return math.floor(round(v * 100, 6)) / 100.0


def ceil2(v):
    return math.ceil(round(v * 100, 6)) / 100.0


def derive_bboxes(state_geometry):
    raw = geometry_bbox(state_geometry)
    pad = 0.05  # small outward pad before rounding outward to 2dp
    bbox = {
        "minLng": floor2(raw[0] - pad), "minLat": floor2(raw[1] - pad),
        "maxLng": ceil2(raw[2] + pad), "maxLat": ceil2(raw[3] + pad),
    }
    gate_pad = 0.15  # the permalink sanity gate: the bbox, padded outward
    gate = {
        "minLat": floor2(bbox["minLat"] - gate_pad),
        "maxLat": ceil2(bbox["maxLat"] + gate_pad),
        "minLng": floor2(bbox["minLng"] - gate_pad),
        "maxLng": ceil2(bbox["maxLng"] + gate_pad),
    }
    return bbox, gate


def derive_center(state_geometry, bbox):
    lat = round((bbox["minLat"] + bbox["maxLat"]) / 2, 4)
    lng = round((bbox["minLng"] + bbox["maxLng"]) / 2, 4)
    if point_in_geometry(lat, lng, state_geometry):
        return lat, lng
    ring = largest_outer_ring(state_geometry)
    if ring:
        lat = round(sum(p[1] for p in ring) / len(ring), 4)
        lng = round(sum(p[0] for p in ring) / len(ring), 4)
    return lat, lng


def candidate_counties(bundle, center):
    """County features in anchor-candidacy order: by population (descending)
    when TIGERweb published one, else the county containing the state's
    center first, then the rest."""
    counties = bundle["counties"]["features"]
    by_geoid = {}
    for feat in counties:
        geoid = props_ci(feat.get("properties"), "GEOID")
        if geoid is not None:
            by_geoid[str(geoid)] = feat

    attrs_by_geoid = {}
    have_pop = False
    for attrs in bundle["county_attrs"]:
        lowered = {str(k).lower(): v for k, v in attrs.items()}
        geoid = lowered.get("geoid")
        if geoid is None:
            continue
        pop = lowered.get("pop100", lowered.get("pop"))
        try:
            pop = int(pop)
            have_pop = True
        except (TypeError, ValueError):
            pop = None
        hint_lat = hint_lng = None
        for lat_key, lng_key in (("intptlat", "intptlon"),
                                 ("centlat", "centlon")):
            try:
                hint_lat = float(lowered[lat_key])
                hint_lng = float(lowered[lng_key])
                break
            except (KeyError, TypeError, ValueError):
                hint_lat = hint_lng = None
        attrs_by_geoid[str(geoid)] = {"pop": pop, "hint": (hint_lat, hint_lng)}

    def hint_for(feat):
        geoid = str(props_ci(feat.get("properties"), "GEOID"))
        return attrs_by_geoid.get(geoid, {}).get("hint", (None, None))

    if have_pop:
        ordered = sorted(
            counties,
            key=lambda f: -(attrs_by_geoid.get(
                str(props_ci(f.get("properties"), "GEOID")), {}).get("pop")
                or 0))
        reason = "most populous first (TIGERweb population field)"
    else:
        containing = feature_containing(bundle["counties"], center[0],
                                        center[1])
        ordered = ([containing] if containing else []) + \
            [f for f in counties if f is not containing]
        reason = "county containing the state's center first (no population field)"
    return ordered, hint_for, reason


def derive_anchor(bundle, center):
    """(lat, lng, county_name, note, expected{layer: value}) — the first
    candidate county whose interior point classifies against all three
    same-origin starter layers. Coordinates are rounded to 5dp FIRST and
    verified after rounding, because the smoke test replays them at 5dp."""
    ordered, hint_for, reason = candidate_counties(bundle, center)
    for rank, feat in enumerate(ordered):
        hint_lat, hint_lng = hint_for(feat)
        pt = interior_point(feat, hint_lat, hint_lng)
        if pt is None:
            continue
        lat, lng = round(pt[0], 5), round(pt[1], 5)
        expected = classify_anchor(bundle, lat, lng)
        if expected is None:
            continue
        county_name = str(props_ci(feat.get("properties"), "NAME") or
                          props_ci(feat.get("properties"), "BASENAME"))
        if rank == 0 and reason.startswith("most"):
            note = ("inside %s — the state's most populous county"
                    % county_name)
        else:
            note = "inside %s" % county_name
        info("anchor: %.5f,%.5f (%s; candidate order: %s)"
             % (lat, lng, note, reason))
        return lat, lng, county_name, note, expected
    fail("no county interior point classified against all three starter "
         "layers — the unified-school tiling may not cover the candidate "
         "counties; inspect the downloaded data/app files")


def classify_anchor(bundle, lat, lng):
    """The anchor's expected card identifiers, one per starter anchor layer.

    Form follows what each card actually renders (scripts/smoke_test.mjs
    extracts the token after the word "District" from the card and compares
    it with ===): the U.S. House card renders a "District N" header pill, so
    its expected value is the bare district number as a string, no leading
    zeros ("7"; at-large "0" — the roster's own key form). The county and
    unified-school cards identify by NAME — the same value their hover popup
    and compact header show — so their expected value is that name verbatim
    (e.g. "Marion County"); a name is not a "District N" string, so it is
    recorded exactly as displayed rather than force-fitted to the number
    form."""
    county = feature_containing(bundle["counties"], lat, lng)
    congress = feature_containing(bundle["congress"], lat, lng)
    school = feature_containing(bundle["schools"], lat, lng)
    if not (county and congress and school):
        return None
    district = numeric_district(congress.get("properties"))
    if district is None:  # inside the ZZ water pseudo-district — no anchor
        return None
    county_name = props_ci(county.get("properties"), "NAME")
    school_name = props_ci(school.get("properties"), "NAME")
    if not county_name or not school_name:
        return None
    return {
        "county": str(county_name),
        "us-house": district,
        "school-district-unified": str(school_name),
    }


def derive_negative_point(bundle, bbox, gate):
    """A point OUTSIDE the state polygon but near it — and INSIDE the
    permalink gate, because the smoke test selects it through a #point=
    permalink and the boot parse drops any point beyond PERMALINK_GATE (the
    check needs the honest empty card, not a rejected permalink). Verified
    against the outline AND against every feature of all three district
    files (outside the state implies outside its STATE-filtered layers, but
    the explicit sweep guards against vintage skew). 5dp, verified after
    rounding."""
    state_geom = bundle["state_feature"]["geometry"]
    mid_lat = round((bbox["minLat"] + bbox["maxLat"]) / 2, 5)
    mid_lng = round((bbox["minLng"] + bbox["maxLng"]) / 2, 5)
    candidates = []
    # bbox corners first — a state almost never reaches its own bbox corner —
    # then the mid-edge points, at small outward steps that stay in the gate.
    for step in (0.03, 0.06):
        lo_lat = round(bbox["minLat"] - step, 5)
        hi_lat = round(bbox["maxLat"] + step, 5)
        lo_lng = round(bbox["minLng"] - step, 5)
        hi_lng = round(bbox["maxLng"] + step, 5)
        candidates += [
            (hi_lat, lo_lng, "off the northwest corner of"),
            (hi_lat, hi_lng, "off the northeast corner of"),
            (lo_lat, lo_lng, "off the southwest corner of"),
            (lo_lat, hi_lng, "off the southeast corner of"),
            (mid_lat, lo_lng, "just west of"),
            (mid_lat, hi_lng, "just east of"),
            (lo_lat, mid_lng, "just south of"),
            (hi_lat, mid_lng, "just north of"),
        ]
    # Last resort: a grid scan of the band between the bbox and the gate.
    # TIGER polygons legally extend into territorial waters (Lake Michigan
    # belongs to its states), so nothing here assumes "offshore = outside" —
    # every candidate faces the ray-cast below.
    band = []
    for i in range(1, 24):
        t = i / 24.0
        lat_span = bbox["maxLat"] - bbox["minLat"]
        lng_span = bbox["maxLng"] - bbox["minLng"]
        band += [
            (round(bbox["maxLat"] + 0.04, 5),
             round(bbox["minLng"] + lng_span * t, 5), "just north of"),
            (round(bbox["minLat"] - 0.04, 5),
             round(bbox["minLng"] + lng_span * t, 5), "just south of"),
            (round(bbox["minLat"] + lat_span * t, 5),
             round(bbox["minLng"] - 0.04, 5), "just west of"),
            (round(bbox["minLat"] + lat_span * t, 5),
             round(bbox["maxLng"] + 0.04, 5), "just east of"),
        ]
    for lat, lng, side in candidates + band:
        # strictly inside the permalink gate, with margin for the strict
        # inequality in the boot parse
        if not (gate["minLat"] + 0.01 < lat < gate["maxLat"] - 0.01 and
                gate["minLng"] + 0.01 < lng < gate["maxLng"] - 0.01):
            continue
        if point_in_geometry(lat, lng, state_geom):
            continue
        if feature_containing(bundle["counties"], lat, lng):
            continue
        if feature_containing(bundle["congress"], lat, lng):
            continue
        if feature_containing(bundle["schools"], lat, lng):
            continue
        return lat, lng, side
    fail("could not find a negative point that is outside the state yet "
         "inside the permalink gate and misses every starter geometry — "
         "inspect the outline and the gate padding")


# ---------------------------------------------------------------------------
# File emission
# ---------------------------------------------------------------------------

def geoid_key(feat):
    return str(props_ci(feat.get("properties"), "GEOID") or "")


def write_boundary_files(bundle, state_name):
    for fc in (bundle["counties"], bundle["congress"], bundle["schools"]):
        strip_bbox_cache(fc)
    outline = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "%s state outline" % state_name},
            "geometry": bundle["state_feature"]["geometry"],
        }],
    }
    write_json(os.path.join(APP_DIR, "metro-outline.json"), outline)
    write_json(os.path.join(APP_DIR, "state-counties.json"),
               normalized_collection(bundle["counties"], geoid_key))
    write_json(os.path.join(APP_DIR, "congress-districts.json"),
               normalized_collection(bundle["congress"], geoid_key))
    write_json(os.path.join(APP_DIR, "school-districts-unified.json"),
               normalized_collection(bundle["schools"], geoid_key))


def write_state_config(bundle, args, usps):
    counties = []
    for feat in sorted(bundle["counties"]["features"], key=geoid_key):
        props = feat.get("properties") or {}
        counties.append({
            "name": str(props_ci(props, "NAME") or ""),
            "fips3": str(props_ci(props, "COUNTY") or ""),
            "geoid": str(props_ci(props, "GEOID") or ""),
        })
    write_json(os.path.join(STATE_DIR, "counties.json"), counties,
               compact=False)
    state = {
        "fips": args.state_fips,
        "usps": usps,
        "name": args.state_name,
        "house_districts": bundle["house_districts"],
    }
    write_json(os.path.join(STATE_DIR, "state.json"), state, compact=False)
    return state


def seed_coverage_gaps(state_name):
    """One honest starter record (the gaps panel requires >= 1 rendered
    group, and an empty inventory would claim the fork answers everything).
    Shape matches the reference fork's file exactly: an object keyed by gap
    id; each record carries id/kind/concept/area/layer/counties/summary/why/
    wanted, with kind one of no-source | blocked | data-quality."""
    gap_id = "county-officials"
    gaps = {
        gap_id: {
            "id": gap_id,
            "kind": "no-source",
            "concept": "County board districts",
            "area": "%s — statewide" % state_name,
            "layer": "county",
            "counties": [],
            "summary": "County board districts aren't built for this fork "
                       "yet; the County card names your county but no "
                       "members.",
            "why": "This fork ships the five starter layers a national "
                   "publisher can answer. County board districts and "
                   "rosters are a per-county build against each county's "
                   "own published map and member list, and none has been "
                   "built yet.",
            "wanted": "Any county's official board-district map (GIS layer, "
                      "vector PDF, or certified election results naming "
                      "whole precincts) plus its member roster page — one "
                      "county is enough to start.",
        },
    }
    write_json(os.path.join(APP_DIR, "coverage-gaps.json"), gaps)
    return gaps


# ---------------------------------------------------------------------------
# Worksheet rewrite
# ---------------------------------------------------------------------------

def slug_for(state_name):
    slug = re.sub(r"[^a-z0-9]+", "-", state_name.lower()).strip("-")
    if not re.match(r"^[a-z0-9-]+$", slug or ""):
        fail("could not derive a slug from state name %r" % state_name)
    return slug


def sweep_strings(node, replacements):
    """Ordered substring replacement over every string in a JSON tree."""
    if isinstance(node, str):
        for old, new in replacements:
            node = node.replace(old, new)
        return node
    if isinstance(node, list):
        return [sweep_strings(item, replacements) for item in node]
    if isinstance(node, dict):
        return {k: sweep_strings(v, replacements) for k, v in node.items()}
    return node


def rewrite_worksheet(facts):
    with open(WORKSHEET_PATH, encoding="utf-8") as f:
        w = json.load(f)

    # The template's own $comment names its stand-in values and the schema
    # (additionalProperties: false) rejects it — it never survives bootstrap.
    w.pop("$comment", None)

    w["this_metro"] = facts["slug"]
    w["metro_name"] = facts["state_name"]
    w["metro_bbox"] = facts["bbox"]
    w["metro_center"] = [facts["center"][0], facts["center"][1]]
    w["permalink_gate"] = facts["gate"]
    w["socrata_host"] = "https://" + facts["portal_host"]
    w["repo_issues"] = "https://github.com/%s/issues/new" % facts["repo"]
    w["feedback_subject"] = facts["brand"] + " feedback"
    w["domains"] = {"canonical": facts["canonical_url"]}
    w["exports_name"] = facts["exports_name"]
    w["verified_date"] = facts["verified_date"]
    if facts.get("palette"):
        w["palette"] = facts["palette"]

    w["anchor_point"] = {
        "lat": facts["anchor"][0], "lng": facts["anchor"][1],
        "note": facts["anchor_note"],
    }
    w["anchors"] = [
        {"layer": "county", "expected": facts["expected"]["county"]},
        {"layer": "us-house", "expected": facts["expected"]["us-house"]},
        {"layer": "school-district-unified",
         "expected": facts["expected"]["school-district-unified"]},
    ]
    w["negative_point"] = {
        "lat": facts["negative"][0], "lng": facts["negative"][1],
        "note": facts["negative_note"],
    }

    tighten_worksheet_bounds(w, facts)

    w["geocoder"] = {
        "address": "Photon (%s-bounded type-ahead)" % facts["state_name"],
        "unbounded": "Photon (whole-coverage, sibling-metro lookup)",
        "poi": "Nominatim (office-address pin lookup, %s-bounded, "
               "serial >=1s queue)" % facts["state_name"],
    }

    # Replace the template's own placeholder entry in the fleet list with
    # this fork's real entry; every other (real fleet) entry is kept as-is.
    entry = {
        "id": facts["slug"], "label": facts["state_name"],
        "url": facts["canonical_url"], "emoji": "📍",
        "bbox": dict(facts["gate"]),
    }
    explorers = w.get("metro_explorers") or []
    replaced = False
    for i, item in enumerate(explorers):
        if item.get("id") in (SENT_SLUG, facts["slug"]):
            explorers[i] = entry
            replaced = True
            break
    if not replaced:
        explorers.append(entry)
    w["metro_explorers"] = explorers

    # Sweep any remaining template stand-ins out of the worksheet's strings
    # (e.g. the layers' "applies" lines) — everything except the fleet list,
    # which legitimately names other forks.
    keep_explorers = w.pop("metro_explorers")
    w = sweep_strings(w, facts["replacements"])
    w["metro_explorers"] = keep_explorers

    with open(WORKSHEET_PATH, "w", encoding="utf-8") as f:
        json.dump(w, f, ensure_ascii=False, indent=2)
        f.write("\n")
    info("rewrote metro-worksheet.json")


def tighten_worksheet_bounds(w, facts):
    """min = max = the real downloaded feature count for every pre-built
    geometry file; roster minimums to the real delegation/gap sizes."""
    geometry_counts = {
        "metro-outline.json": 1,
        "state-counties.json": facts["n_counties"],
        "congress-districts.json": facts["n_congress"],
        "school-districts-unified.json": facts["n_schools"],
    }
    for entry in w["data_files"]["geometry"]:
        count = geometry_counts.get(entry["file"])
        if count is not None:
            entry["min_features"] = count
            entry["max_features"] = count
    roster_minimums = {
        "congress-roster.json": facts["house_districts"],
        "coverage-gaps.json": facts["n_gaps"],
    }
    for entry in w["data_files"]["rosters"]:
        minimum = roster_minimums.get(entry["file"])
        if minimum is not None:
            entry["min_keys"] = minimum


# ---------------------------------------------------------------------------
# Tree-wide token fill + stand-in sweep
# ---------------------------------------------------------------------------

# Mirrors scripts/check_template_placeholders.py: what that gate skips, this
# fill skips (engine-channel files are byte-identical fleet-wide by contract
# and must never be localized; data/ is real-world civic data and is never
# rewritten; fence/generated bodies are skipped so the sweep can't break
# engine parity — GENERATED bodies are regenerated anyway).
SKIP_FILES = {
    "docs/ENGINE_SYNC.md",
    "engine.lock.json",
    "schema/metro-worksheet.schema.json",
    "scripts/apply_engine.py",
    "scripts/check_engine_parity.py",
    "scripts/generate_metro_files.py",
    "scripts/check_template_placeholders.py",
    "engine.bundle.js",
    "engine.manifest.json",
    "metro-worksheet.json",  # rewritten explicitly above
}
SKIP_DIRS = {".git", "node_modules", "fonts", "data", "dist",
             ".claude/worktrees", "scripts/vendor", "__pycache__"}
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2",
                 ".zip", ".pdf", ".pyc")

ENGINE_FENCE_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--)[ \t]*==== ENGINE:(BEGIN|END) [a-z0-9][a-z0-9-]* ===="
    r"[ \t]*(?:\*/|-->)[ \t]*$")
GENERATED_FENCE_RE = re.compile(
    r"^[ \t]*(?:/\*|<!--|#|//)?[ \t]*==== GENERATED:(BEGIN|END) "
    r"[a-z0-9][a-z0-9-]* ====[ \t]*(?:\*/|-->)?[ \t]*$")


def iter_tree_files():
    for root, dirs, files in os.walk(REPO):
        rel_root = os.path.relpath(root, REPO)
        if rel_root == ".":
            rel_root = ""
        dirs[:] = [
            d for d in dirs
            if os.path.join(rel_root, d).replace("\\", "/") not in SKIP_DIRS
            and d not in (".git", "node_modules", "__pycache__")
        ]
        for name in files:
            rel = (os.path.join(rel_root, name) if rel_root else name)
            rel = rel.replace("\\", "/")
            if rel in SKIP_FILES or rel.endswith(SKIP_SUFFIXES):
                continue
            yield rel


def rewrite_outside_fences(text, line_rewrite):
    """Apply line_rewrite to every line OUTSIDE ENGINE fences and GENERATED
    regions (their bodies are contract-fixed / regenerated)."""
    out = []
    closing = None
    changed = False
    for line in text.split("\n"):
        if closing is not None:
            m = closing.match(line)
            if m and m.group(1) == "END":
                closing = None
            out.append(line)
            continue
        m_engine = ENGINE_FENCE_RE.match(line)
        m_generated = GENERATED_FENCE_RE.match(line)
        if m_engine and m_engine.group(1) == "BEGIN":
            closing = ENGINE_FENCE_RE
            out.append(line)
            continue
        if m_generated and m_generated.group(1) == "BEGIN":
            closing = GENERATED_FENCE_RE
            out.append(line)
            continue
        new = line_rewrite(line)
        if new != line:
            changed = True
        out.append(new)
    return "\n".join(out), changed


def fill_tree(token_map, replacements):
    token_pairs = [(tok(name), value) for name, value in token_map.items()]

    def line_rewrite(line):
        for old, new in token_pairs:
            if old in line:
                line = line.replace(old, new)
        for old, new in replacements:
            if old in line:
                line = line.replace(old, new)
        return line

    touched = []
    for rel in sorted(iter_tree_files()):
        path = os.path.join(REPO, rel)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        new_text, changed = rewrite_outside_fences(text, line_rewrite)
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_text)
            touched.append(rel)
    info("filled tokens / template stand-ins in %d file(s)" % len(touched))
    return touched


def set_indexnow_key(domain):
    """scripts/indexnow_submit.py ships with a scaffold HOST + all-zero KEY;
    HOST is covered by the tree sweep, the KEY gets a fresh uuid4 here."""
    path = os.path.join(SCRIPTS_DIR, "indexnow_submit.py")
    key = uuid.uuid4().hex
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        info("NOTE — scripts/indexnow_submit.py not found; no IndexNow key "
             "was generated")
        return None
    needle = '"%s"' % SENT_INDEXNOW_KEY
    if needle not in text:
        info("NOTE — scripts/indexnow_submit.py carries no scaffold key; "
             "leaving it untouched")
        return None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(needle, '"%s"' % key, 1))
    info("IndexNow key generated: %s (serve %s.txt at https://%s/)"
         % (key, key, domain))
    return key


# ---------------------------------------------------------------------------
# Subprocess gates
# ---------------------------------------------------------------------------

def run_step(argv, what, required=True):
    info("running: %s" % " ".join(argv))
    proc = subprocess.run(argv, cwd=REPO)
    if proc.returncode != 0:
        if required:
            fail("%s failed (exit %d)" % (what, proc.returncode))
        info("NOTE — %s failed (exit %d); continuing" % (what,
                                                         proc.returncode))
        return False
    return True


def run_gate(gate_failures, argv, what):
    """Gate-battery step: failures are COLLECTED, not fatal mid-battery, so
    every gate reports and the final report still prints; the bootstrap then
    exits non-zero naming every failed gate."""
    if not run_step(argv, what, required=False):
        gate_failures.append(what)


def build_congress_roster(house_districts):
    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "build_congress_roster.py")],
             "build_congress_roster.py")
    roster_path = os.path.join(APP_DIR, "congress-roster.json")
    with open(roster_path, encoding="utf-8") as f:
        roster = json.load(f)
    if len(roster) < house_districts:
        fail("congress-roster.json resolved %d/%d districts"
             % (len(roster), house_districts))
    info("congress roster: %d district(s) (guard: >= %d)"
         % (len(roster), house_districts))


def run_gate_battery():
    # The regeneration itself must succeed (everything downstream reads its
    # output); the verification gates then all run, collecting failures.
    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "generate_metro_files.py")],
             "generate_metro_files.py (regenerate)")
    gate_failures = []
    run_gate(gate_failures,
             [sys.executable, os.path.join(SCRIPTS_DIR,
                                           "generate_metro_files.py"),
              "--check"],
             "generate_metro_files.py --check")
    run_gate(gate_failures,
             [sys.executable,
              os.path.join(SCRIPTS_DIR, "check_template_placeholders.py")],
             "check_template_placeholders.py")
    run_gate(gate_failures,
             [sys.executable, os.path.join(SCRIPTS_DIR, "validate_index.py"),
              "index.html"],
             "validate_index.py")
    run_gate(gate_failures,
             [sys.executable,
              os.path.join(SCRIPTS_DIR, "check_engine_parity.py"),
              "index.html"],
             "check_engine_parity.py (index.html)")
    run_gate(gate_failures,
             [sys.executable,
              os.path.join(SCRIPTS_DIR, "check_engine_parity.py"), "sw.js"],
             "check_engine_parity.py (sw.js)")
    node = None
    for candidate in ("node", "nodejs"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True,
                           check=True)
            node = candidate
            break
        except (OSError, subprocess.CalledProcessError):
            continue
    if node:
        run_gate(gate_failures,
                 [node, "--check",
                  os.path.join(SCRIPTS_DIR, "smoke_test.mjs")],
                 "node --check smoke_test.mjs")
    else:
        info("node not available — skipping the smoke test syntax check "
             "(CI runs the full behaviour gate)")
    return gate_failures


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------

def print_report(facts, goatcounter_defaulted, indexnow_key):
    line = "=" * 72
    print("\n" + line)
    print("BOOTSTRAP COMPLETE — %s (%s, FIPS %s)"
          % (facts["brand"], facts["state_name"], facts["fips"]))
    print(line)
    print("Built (data/app/):")
    print("  metro-outline.json               1 feature (state outline)")
    print("  state-counties.json              %d counties" % facts["n_counties"])
    print("  congress-districts.json          %d features (%d numbered districts)"
          % (facts["n_congress"], facts["house_districts"]))
    print("  school-districts-unified.json    %d unified school districts"
          % facts["n_schools"])
    print("  congress-roster.json             %d U.S. House members"
          % facts["house_districts"])
    print("  coverage-gaps.json               %d starter gap record(s)"
          % facts["n_gaps"])
    print("  data/state/state.json + counties.json (config for the weekly "
          "roster refresh)")
    print("Derived:")
    print("  bbox    %(minLng)s..%(maxLng)s lng, %(minLat)s..%(maxLat)s lat"
          % facts["bbox"])
    print("  center  %.4f, %.4f   permalink gate ~0.15 deg beyond the bbox"
          % (facts["center"][0], facts["center"][1]))
    print("  anchor  %.5f,%.5f (%s)"
          % (facts["anchor"][0], facts["anchor"][1], facts["anchor_note"]))
    for layer in ("county", "us-house", "school-district-unified"):
        print("          %-24s -> %r" % (layer, facts["expected"][layer]))
    print("  negative point %.5f,%.5f (%s)"
          % (facts["negative"][0], facts["negative"][1],
             facts["negative_note"]))
    if goatcounter_defaulted:
        print("\n*** ANALYTICS WILL SILENTLY NO-OP UNTIL YOU ACT: no "
              "--goatcounter-url was given, so the app points at\n    %s\n"
              "    CREATE that GoatCounter site (goatcounter.com) or pass "
              "your own URL and re-run —\n    trackEvent fails silently "
              "against a site that does not exist." % facts["goatcounter"])
    print("\nWHAT THIS SCRIPT CANNOT DO — reference-fork (CHI) side:")
    print("  * Add this fork to metros.json in the reference repo, then run "
          "generate_metro_files.py --sync-fleet")
    print("    + regenerate in EVERY fleet fork (a regeneration PR per fork) "
          "so their metro switchers list this one.")
    print("  * Add this repo to release-engine.yml's fan-out list so engine "
          "releases open bump PRs here.")
    print("  * Add the deployed URL to engine-parity.yml's compared-site "
          "block (reference repo only).")
    print("  * Add this fork's row to DATA_LAYER_GUIDEBOOK.md's coverage map "
          "and its gaps block (the weekly fleet run diffs both).")
    print("\nWHAT THIS SCRIPT CANNOT DO — operator side:")
    print("  * ENGINE_DISPATCH_TOKEN / BOT_PR_TOKEN repo secrets (PATs with "
          "Contents + Pull requests read/write) so")
    print("    engine bumps and the weekly roster refresh can open PRs that "
          "run CI.")
    print("  * GitHub Pages: source = GitHub Actions, custom domain %s, and "
          "a CNAME file if you deploy from a branch." % facts["domain"])
    print("  * Actions settings: turn ON 'Allow GitHub Actions to create "
          "and approve pull requests'.")
    print("  * Create the GoatCounter site named above (or none — analytics "
          "then stays a silent no-op).")
    print("  * Real icons (icons/icon-192.png, icon-512.png) and an "
          "og-image — the template ships placeholders.")
    if indexnow_key:
        print("  * Serve the IndexNow key file at the site root: "
              "https://%s/%s.txt containing exactly that key."
              % (facts["domain"], indexnow_key))
    else:
        print("  * IndexNow: no key was generated (scaffold not found) — "
              "set one in scripts/indexnow_submit.py by hand.")
    print(line)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def load_state_config():
    path = os.path.join(STATE_DIR, "state.json")
    if not os.path.exists(path):
        fail("data/state/state.json not found — run the full bootstrap first")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def refresh_congress_roster():
    state = load_state_config()
    info("refreshing the U.S. House roster for %s (%s district(s))"
         % (state.get("name"), state.get("house_districts")))
    build_congress_roster(int(state["house_districts"]))
    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "validate_index.py"), "index.html"],
             "validate_index.py")
    info("roster refresh complete")


def refresh_boundaries():
    state = load_state_config()
    fips, name = state["fips"], state["name"]
    info("re-fetching the four TIGERweb-derived files for %s (FIPS %s)"
         % (name, fips))
    bundle = fetch_boundary_set(fips, name)
    write_boundary_files(bundle, name)

    with open(WORKSHEET_PATH, encoding="utf-8") as f:
        w = json.load(f)

    tighten_worksheet_bounds(w, {
        "n_counties": bundle["n_counties"],
        "n_congress": bundle["n_congress"],
        "n_schools": bundle["n_schools"],
        "house_districts": bundle["house_districts"],
        # the gap inventory is untouched in this mode — keep its floor
        "n_gaps": next((r["min_keys"] for r in w["data_files"]["rosters"]
                        if r["file"] == "coverage-gaps.json"), 1),
    })

    # Re-verify the recorded ground truth against the fresh geometry: a
    # redistricting can move a line under the anchor or negative point.
    anchor = w["anchor_point"]
    expected = classify_anchor(bundle, anchor["lat"], anchor["lng"])
    if expected is None:
        info("NOTE — the recorded anchor no longer classifies against all "
             "three layers; deriving a fresh one")
        bbox, _gate = derive_bboxes(bundle["state_feature"]["geometry"])
        center = derive_center(bundle["state_feature"]["geometry"], bbox)
        lat, lng, _county, note, expected = derive_anchor(bundle, center)
        w["anchor_point"] = {"lat": lat, "lng": lng, "note": note}
    old_expected = {a["layer"]: a["expected"] for a in w["anchors"]}
    if old_expected != expected:
        info("anchor classifications changed: %r -> %r"
             % (old_expected, expected))
    w["anchors"] = [{"layer": layer, "expected": expected[layer]}
                    for layer in ("county", "us-house",
                                  "school-district-unified")]

    neg = w["negative_point"]
    neg_bad = (point_in_geometry(neg["lat"], neg["lng"],
                                 bundle["state_feature"]["geometry"]) or
               feature_containing(bundle["counties"], neg["lat"], neg["lng"])
               or feature_containing(bundle["congress"], neg["lat"],
                                     neg["lng"])
               or feature_containing(bundle["schools"], neg["lat"],
                                     neg["lng"]))
    if neg_bad:
        info("NOTE — the recorded negative point now hits a boundary; "
             "deriving a fresh one")
        bbox, gate = derive_bboxes(bundle["state_feature"]["geometry"])
        lat, lng, side = derive_negative_point(bundle, bbox, gate)
        w["negative_point"] = {
            "lat": lat, "lng": lng,
            "note": "%s %s — outside the state and every starter layer"
                    % (side, name),
        }

    with open(WORKSHEET_PATH, "w", encoding="utf-8") as f:
        json.dump(w, f, ensure_ascii=False, indent=2)
        f.write("\n")
    info("re-tightened worksheet bounds "
         "(counties %d, congress %d, schools %d)"
         % (bundle["n_counties"], bundle["n_congress"], bundle["n_schools"]))

    if int(state["house_districts"]) != bundle["house_districts"]:
        info("house_districts changed %s -> %s — updating state.json and "
             "rebuilding the roster"
             % (state["house_districts"], bundle["house_districts"]))
        state["house_districts"] = bundle["house_districts"]
        write_json(os.path.join(STATE_DIR, "state.json"), state,
                   compact=False)
        build_congress_roster(bundle["house_districts"])

    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "generate_metro_files.py")],
             "generate_metro_files.py (regenerate)")
    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "generate_metro_files.py"),
              "--check"],
             "generate_metro_files.py --check")
    run_step([sys.executable,
              os.path.join(SCRIPTS_DIR, "validate_index.py"), "index.html"],
             "validate_index.py")
    info("boundary refresh complete")


# ---------------------------------------------------------------------------
# Full bootstrap
# ---------------------------------------------------------------------------

def build_favicon(accent_hex):
    """Inline SVG data URI — accent circle + white five-point star — encoded
    the way the template's placeholder examples are (only <, > and #)."""
    cx, cy = 32.0, 33.0
    points = []
    for i in range(10):
        radius = 15.0 if i % 2 == 0 else 6.0
        angle = math.radians(-90 + i * 36)
        points.append("%.1f,%.1f" % (cx + radius * math.cos(angle),
                                     cy + radius * math.sin(angle)))
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
           "<circle cx='32' cy='32' r='30' fill='%s'/>"
           "<polygon points='%s' fill='#FFFFFF'/>"
           "</svg>" % (accent_hex, " ".join(points)))
    encoded = svg.replace("<", "%3C").replace(">", "%3E").replace("#", "%23")
    return "data:image/svg+xml," + encoded


def parse_palette(raw):
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        fail("--palette needs 4 comma-separated hex colors "
             "(accent,deep,warm,warmdeep); got %d" % len(parts))
    colors = []
    for part in parts:
        hexpart = part[1:] if part.startswith("#") else part
        if not re.match(r"^[0-9A-Fa-f]{6}$", hexpart):
            fail("--palette color %r is not a 6-digit hex color" % part)
        colors.append("#" + hexpart.upper())
    return dict(zip(("accent", "accent_deep", "accent_warm",
                     "accent_warm_deep"), colors))


def full_bootstrap(args):
    fips = args.state_fips
    usps = FIPS_TO_USPS.get(fips)
    if not usps:
        fail("--state-fips %r is not a known state/territory FIPS code"
             % fips)
    if not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", args.repo):
        fail("--repo must be owner/name; got %r" % args.repo)
    domain = args.domain.strip().lower().rstrip("/")
    if not re.match(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$", domain) \
            or "/" in domain or ":" in domain:
        fail("--domain must be a bare hostname (no scheme, no path); "
             "got %r" % args.domain)
    slug = slug_for(args.state_name)
    exports_name = args.exports_name or (
        "".join(w.capitalize()
                for w in re.findall(r"[A-Za-z0-9]+", args.state_name))
        + "Explorer")
    if not re.match(r"^[A-Za-z][A-Za-z0-9]*$", exports_name):
        fail("exports name %r must match ^[A-Za-z][A-Za-z0-9]*$"
             % exports_name)
    portal_host = (args.portal_host or "data.invalid").strip().rstrip("/")
    portal_host = re.sub(r"^https?://", "", portal_host)
    palette = parse_palette(args.palette) if args.palette else None

    # Template palette default holds when --palette is not given; read the
    # worksheet's current palette so THEME_COLOR always names a real color.
    with open(WORKSHEET_PATH, encoding="utf-8") as f:
        current_palette = json.load(f).get("palette") or {}
    effective_palette = palette or {
        "accent": current_palette.get("accent", "#4A90D9"),
        "accent_deep": current_palette.get("accent_deep", "#2C5F9E"),
        "accent_warm": current_palette.get("accent_warm", "#D97706"),
        "accent_warm_deep": current_palette.get("accent_warm_deep",
                                                "#B45309"),
    }

    goatcounter_defaulted = args.goatcounter_url is None
    goatcounter = args.goatcounter_url or (
        "https://%s.goatcounter.com/count" % domain.split(".")[0])

    today = datetime.date.today()
    verified_date = "%s %d, %d" % (today.strftime("%B"), today.day,
                                   today.year)

    # ---- 1-4. every network fetch, staged before any write ----------------
    bundle = fetch_boundary_set(fips, args.state_name)
    state_geom = bundle["state_feature"]["geometry"]
    bbox, gate = derive_bboxes(state_geom)
    center = derive_center(state_geom, bbox)
    anchor_lat, anchor_lng, _anchor_county, anchor_note, expected = \
        derive_anchor(bundle, center)
    neg_lat, neg_lng, neg_side = derive_negative_point(bundle, bbox, gate)
    negative_note = ("%s %s — outside the state and every starter layer"
                     % (neg_side, args.state_name))
    info("negative point: %.5f,%.5f (%s)" % (neg_lat, neg_lng, negative_note))

    # ---- writes -----------------------------------------------------------
    write_boundary_files(bundle, args.state_name)
    write_state_config(bundle, args, usps)
    build_congress_roster(bundle["house_districts"])
    gaps = seed_coverage_gaps(args.state_name)

    canonical_url = "https://%s/" % domain
    replacements = [
        # Order matters: the portal stand-in embeds the domain stand-in, the
        # repo stand-ins embed the slug, the brand embeds the display name.
        (SENT_PORTAL, portal_host),
        (canonical_sentinel(), canonical_url),
        (SENT_DOMAIN, domain),
        (SENT_OWNER + "/" + SENT_REPO_NAME, args.repo),
        (SENT_OWNER, args.repo.split("/")[0]),
        (SENT_REPO_NAME, args.repo.split("/")[1]),
        (SENT_NAME + " District Explorer", args.brand_name),
        (SENT_NAME, args.state_name),
        (SENT_SLUG, slug),
        (SENT_EXPORTS, exports_name),
        (SENT_DATE, verified_date),
    ]

    facts = {
        "fips": fips, "usps": usps, "state_name": args.state_name,
        "slug": slug, "brand": args.brand_name, "repo": args.repo,
        "domain": domain, "canonical_url": canonical_url,
        "exports_name": exports_name, "portal_host": portal_host,
        "goatcounter": goatcounter, "verified_date": verified_date,
        "palette": palette, "bbox": bbox, "gate": gate, "center": center,
        "anchor": (anchor_lat, anchor_lng), "anchor_note": anchor_note,
        "expected": expected, "negative": (neg_lat, neg_lng),
        "negative_note": negative_note,
        "n_counties": bundle["n_counties"],
        "n_congress": bundle["n_congress"],
        "n_schools": bundle["n_schools"],
        "house_districts": bundle["house_districts"],
        "n_gaps": len(gaps),
        "replacements": replacements,
    }

    rewrite_worksheet(facts)

    token_map = {
        "STATE_NAME": args.state_name,
        "STATE_FIPS": fips,
        "BRAND_NAME": args.brand_name,
        "CANONICAL_HOST": domain,
        "CANONICAL_URL": canonical_url,
        "REPO_URL": "https://github.com/" + args.repo,
        "EXPORTS_NAME": exports_name,
        "GOATCOUNTER_URL": goatcounter,
        "THEME_COLOR": args.theme_color or effective_palette["accent_deep"],
        "FAVICON_DATA_URI": build_favicon(effective_palette["accent"]),
        "PALETTE_ACCENT": effective_palette["accent"],
        "PALETTE_ACCENT_DEEP": effective_palette["accent_deep"],
        "PALETTE_ACCENT_WARM": effective_palette["accent_warm"],
        "PALETTE_ACCENT_WARM_DEEP": effective_palette["accent_warm_deep"],
        "GEOCODER_BIAS_LAT": "%.2f" % center[0],
        "GEOCODER_BIAS_LON": "%.2f" % center[1],
        "PORTAL_HOST": portal_host,
        "EMPTY_STATE_LEDE": "See your county, county subdivision, "
                            "municipality, unified school district, and "
                            "U.S. House district — plus who represents you.",
    }
    indexnow_key = set_indexnow_key(domain)
    fill_tree(token_map, replacements)

    gate_failures = run_gate_battery()
    print_report(facts, goatcounter_defaulted, indexnow_key)
    if gate_failures:
        fail("bootstrap finished but %d gate(s) FAILED — scroll up for each "
             "gate's own report: %s"
             % (len(gate_failures), "; ".join(gate_failures)))
    info("every gate passed")


def canonical_sentinel():
    return "https://" + SENT_DOMAIN + "/"


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state-fips", help="two-digit state FIPS (e.g. 18)")
    parser.add_argument("--state-name", help="the state's name (e.g. Indiana)")
    parser.add_argument("--repo", help="GitHub owner/name of this fork")
    parser.add_argument("--domain",
                        help="canonical bare hostname (e.g. in.example.com)")
    parser.add_argument("--brand-name",
                        help='product name (e.g. "Indiana District Explorer")')
    parser.add_argument("--exports-name",
                        help="window debug namespace (default: "
                             "<StateName>Explorer)")
    parser.add_argument("--goatcounter-url",
                        help="GoatCounter count endpoint (default: derived, "
                             "with a loud reminder to create the site)")
    parser.add_argument("--portal-host",
                        help="open-data portal hostname (default: "
                             "data.invalid — keeps the smoke test's "
                             "failure-injection inert)")
    parser.add_argument("--theme-color",
                        help="PWA theme-color hex (default: the palette's "
                             "deep accent)")
    parser.add_argument("--palette",
                        help="accent,deep,warm,warmdeep hex CSV overriding "
                             "the template palette")
    parser.add_argument("--refresh-congress-roster", action="store_true",
                        help="maintenance: rebuild congress-roster.json + "
                             "validate")
    parser.add_argument("--refresh-boundaries", action="store_true",
                        help="maintenance: re-fetch the TIGERweb files, "
                             "re-tighten bounds, regenerate + validate")
    args = parser.parse_args()

    if args.refresh_congress_roster and args.refresh_boundaries:
        fail("pick one maintenance mode at a time")
    if args.refresh_congress_roster:
        refresh_congress_roster()
        return
    if args.refresh_boundaries:
        refresh_boundaries()
        return

    missing = [name for name in
               ("state_fips", "state_name", "repo", "domain", "brand_name")
               if not getattr(args, name)]
    if missing:
        fail("full bootstrap needs --%s (or use a --refresh-* mode)"
             % ", --".join(m.replace("_", "-") for m in missing))
    args.state_fips = args.state_fips.zfill(2)
    full_bootstrap(args)


if __name__ == "__main__":
    main()

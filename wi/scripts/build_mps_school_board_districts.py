#!/usr/bin/env python3
"""
Build data/app/mps-school-board-districts.json — the eight Milwaukee Public
Schools board districts, the fleet's second elected-school-board geometry
(the reference instance's ERSB is the precedent) and Wisconsin's first
city-scoped layer.

WHY MPS AND ONLY MPS: Wisconsin school boards are mostly elected AT LARGE;
statute names the districted minority exactly — MPS (ch. 119, eight numbered
districts plus one at-large director) and Racine Unified (s. 120.42(1)(d)2).
RUSD publishes its nine election districts only as ArcMap-generated PDFs, so
it stays a measured gap (`rusd-school-board`); MPS publishes real geometry.

TWO CITY SURFACES, EACH DOING THE JOB IT'S GOOD AT:

  * The city's ArcGIS layer (AGO/MPS_School_Districts/MapServer/1) serves
    the geometry REPROJECTED — outSR=4326 asks the city's own server to
    carry NAD27 Wisconsin South (the shapefile's datum) to WGS84 with its
    own transformation, rather than this builder approximating a datum
    shift. THE HOST IS MEASURED FLAKY (drops roughly 1 in 4-8 requests with
    TCP resets), which is why it is fetched at BUILD TIME with retries and
    never at runtime.
  * The CKAN shapefile (data.milwaukee.gov, CC-BY, stable host) is the
    WITNESS: its DBF must carry exactly districts 1-8, and each district's
    share of the total area — computed independently in the shapefile's own
    native plane and in the fetched WGS84 geometry — must agree, so a stale
    or partial fetch can never ship. (Shares, not absolute areas: the two
    live in different coordinate systems, and the RATIO is what both must
    agree on.)

The districts were adopted 2022-02-25 (the district's own directors page
states it) and redraw after each decennial census — WATCH.md carries the
row. An OPERATOR rebuild, not a weekly one.
"""

import io
import json
import math
import os
import struct
import subprocess
import sys
import time
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT_PATH = os.path.join(REPO_ROOT, "data", "app", "mps-school-board-districts.json")

REST = ("https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/AGO"
        "/MPS_School_Districts/MapServer/1/query"
        "?where=1%3D1&outFields=SCHOOL&outSR=4326&geometryPrecision=6&f=geojson")
CKAN_SHP = ("https://data.milwaukee.gov/dataset/98565acf-5652-4a14-bcab-78a48b2fce8b"
            "/resource/bdb7cf59-cd28-48bf-be11-926dad6cd1ba/download/mps_schoolboard.zip")

EXPECT = [str(n) for n in range(1, 9)]
# Milwaukee's rough envelope; a coordinate outside it means outSR was ignored
BBOX = {"min_lat": 42.8, "max_lat": 43.3, "min_lng": -88.2, "max_lng": -87.8}


def fetch(url, binary=False, tries=8, timeout=60):
    """curl, not urllib, and retried. Two measured reasons: the milwaukeemaps
    host resets ~1 in 4-8 connections (fetched at build time only, never by
    the app), and CKAN's download 302s to a presigned S3 URL that urllib's
    redirect-following gets a 403 from where curl's does not — the
    supervisory builder's _curl convention, applied here."""
    last = None
    for _ in range(tries):
        try:
            out = subprocess.run(
                ["curl", "-sSL", "--fail", "--max-time", str(timeout),
                 "-H", "User-Agent: districtry/1.0 (+https://districtry.com/wi/)", url],
                check=True, capture_output=True).stdout
            return out if binary else out.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 — the measured flaky host
            last = e
            time.sleep(2)
    raise last


def ring_area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return a / 2.0


def geom_area(geom, scale_x=1.0):
    """Shoelace over a (Multi)Polygon; scale_x corrects longitude shrink for
    WGS84 input so SHARES are comparable with a plane-coordinate source."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    total = 0.0
    for poly in polys:
        total += abs(ring_area([[x * scale_x, y] for x, y in poly[0]]))
        for hole in poly[1:]:
            total -= abs(ring_area([[x * scale_x, y] for x, y in hole]))
    return total


def shp_areas(zip_bytes):
    """District -> area in the shapefile's own native plane units, read
    straight from the .shp record polygons (rings per record; the DBF rows
    pair by record order)."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    dbf = z.read(next(n for n in z.namelist() if n.lower().endswith(".dbf")))
    shp = z.read(next(n for n in z.namelist() if n.lower().endswith(".shp")))
    n_rec = struct.unpack("<I", dbf[4:8])[0]
    hdr_len = struct.unpack("<H", dbf[8:10])[0]
    rec_len = struct.unpack("<H", dbf[10:12])[0]
    fields = []
    off = 32
    while dbf[off] != 0x0D:
        fields.append((dbf[off:off + 11].split(b"\x00")[0].decode(), dbf[off + 16]))
        off += 32
    rows = []
    pos = hdr_len
    for _ in range(n_rec):
        rec = dbf[pos:pos + rec_len]
        pos += rec_len
        o = 1
        row = {}
        for name, flen in fields:
            row[name] = rec[o:o + flen].decode("latin1").strip()
            o += flen
        rows.append(row)

    areas = []
    pos = 100
    while pos < len(shp):
        length = struct.unpack(">I", shp[pos + 4:pos + 8])[0] * 2
        shape_type = struct.unpack("<i", shp[pos + 8:pos + 12])[0]
        if shape_type != 5:
            raise SystemExit("shapefile record is type %d, expected 5 (Polygon)" % shape_type)
        num_parts = struct.unpack("<i", shp[pos + 44:pos + 48])[0]
        num_points = struct.unpack("<i", shp[pos + 48:pos + 52])[0]
        parts = struct.unpack("<%di" % num_parts, shp[pos + 52:pos + 52 + 4 * num_parts])
        pts_off = pos + 52 + 4 * num_parts
        pts = struct.unpack("<%dd" % (num_points * 2),
                            shp[pts_off:pts_off + 16 * num_points])
        rings = []
        for pi in range(num_parts):
            s = parts[pi]
            e = parts[pi + 1] if pi + 1 < num_parts else num_points
            rings.append([[pts[2 * j], pts[2 * j + 1]] for j in range(s, e)])
        # outer rings are clockwise in shapefiles (negative shoelace); holes
        # counter-clockwise — signed sum nets holes out
        area = abs(sum(ring_area(r) for r in rings))
        areas.append(area)
        pos += 8 + length
    if len(areas) != len(rows):
        raise SystemExit("shapefile carries %d shapes against %d DBF rows"
                         % (len(areas), len(rows)))
    return {row["SCHOOL"]: a for row, a in zip(rows, areas)}


def main():
    gj = json.loads(fetch(REST))
    feats = gj.get("features") or []
    if len(feats) != 8:
        raise SystemExit("city layer served %d districts, expected 8" % len(feats))
    by_district = {}
    for f in feats:
        d = str(f["properties"].get("SCHOOL"))
        if d in by_district:
            raise SystemExit("district %s served twice" % d)
        by_district[d] = f
    if sorted(by_district) != EXPECT:
        raise SystemExit("districts %s, expected 1-8" % sorted(by_district))
    for d, f in by_district.items():
        polys = (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon"
                 else [f["geometry"]["coordinates"]])
        lng, lat = polys[0][0][0]
        if not (BBOX["min_lat"] <= lat <= BBOX["max_lat"] and
                BBOX["min_lng"] <= lng <= BBOX["max_lng"]):
            raise SystemExit("district %s starts at (%s,%s) — outside Milwaukee; "
                             "outSR was ignored" % (d, lat, lng))

    # the CKAN shapefile witness: same districts, same area SHARES
    witness = shp_areas(fetch(CKAN_SHP, binary=True))
    if sorted(witness) != EXPECT:
        raise SystemExit("CKAN shapefile carries districts %s, expected 1-8"
                         % sorted(witness))
    mid_lat = 43.05
    scale = math.cos(math.radians(mid_lat))
    got = {d: geom_area(f["geometry"], scale_x=scale) for d, f in by_district.items()}
    tot_g, tot_w = sum(got.values()), sum(witness.values())
    for d in EXPECT:
        share_g = got[d] / tot_g
        share_w = witness[d] / tot_w
        if abs(share_g - share_w) > 0.005:
            raise SystemExit("district %s is %.3f%% of the city on the REST layer "
                             "but %.3f%% in the CKAN shapefile — the two surfaces "
                             "disagree; read the change before shipping"
                             % (d, 100 * share_g, 100 * share_w))

    out = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": by_district[d]["geometry"],
         "properties": {"DISTRICT": d}} for d in EXPECT]}
    compact = json.dumps(out, separators=(",", ":"))
    with open(OUT_PATH, "w") as f:
        f.write(compact)
    print("mps-school-board-districts -> data/app/%s: 8 districts, area shares "
          "witnessed against the CKAN shapefile (max diff %.4f%%), %d bytes"
          % (os.path.basename(OUT_PATH),
             100 * max(abs(got[d] / tot_g - witness[d] / tot_w) for d in EXPECT),
             len(compact)))


if __name__ == "__main__":
    sys.exit(main())

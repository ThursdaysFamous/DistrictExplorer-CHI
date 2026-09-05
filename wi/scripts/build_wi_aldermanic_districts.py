#!/usr/bin/env python3
"""
Build data/app/aldermanic-districts.json — every aldermanic (and village
trustee) district Wisconsin's ward fabric can honestly compose, dissolved
from LTSB's statewide municipal ward layer.

WHY A DISSOLVE, AND ON WHICH KEY. No Wisconsin publisher ships a statewide
aldermanic-district layer, but the state's ward layer carries each ward's
district assignment in ALDERID (Wis. Stat. 5.15(4)(br) filings, Jan/Jul).
The dissolve key is **COUSUBFP + ALDERID — never ALDER_FIPS**: ALDER_FIPS is
county-qualified, and 25 coded municipalities cross county lines, so keying
on it would split those cities' districts in two at the county line. An
incorporated place's COUSUBFP is statewide-unique (measured: no name
collision among coded C/V municipalities), which is exactly what lets the
dissolve merge a cross-county city back together.

MEASURED 2026-08-26 (July 2026 filing): 7,161 wards, 2,580 coded; 2,576 of
those in cities and villages (the other 4 are the Town of Mercer, Iron
County — a town elects no alderpersons, so the CTV gate drops them and this
builder prints them); 867 distinct district keys across 165 municipalities.
THE STATE'S OWN PRE-DISSOLVE AGREES: LTSB's BAS_Live_Collection_Alderpersons
layer (the mid-collection working set, currently the JANUARY session) holds
the same 867 C/V keys, key for key, across a different filing edition — a
two-edition witness this builder re-runs on every build. That BAS layer is
not the source (no stated terms, mutates mid-collection); the licensed AGOL
ward layer is.

THE PER-CITY COMPLETENESS GATE — the reason this file is not a one-liner.
Fourteen municipalities mix '00' placeholders with real district ids, and
the mix splits two ways, measured by uncoded-ward count and area share:

  * TEN ARE INCOMPLETE SUBMISSIONS and are EXCLUDED, each on the record in
    EXCLUDED below (uncoded share 9.4%-99.9% of the city's area). Appleton
    is the flagship: Outagamie County submits all 50 of its Appleton wards
    uncoded, only the Calumet/Winnebago fringes carry ids, and the city's
    own GIS publishes no aldermanic layer either (its pubserver's full
    service list and a portal-wide "alder" search both answer empty,
    measured 2026-08-26) — two dead routes, so the gap record stands.
    Bellevue is the INVERSE error and the reason the gate cuts both ways: a
    village with ONE spuriously coded ward (99.9% uncoded) would otherwise
    ship a single sliver posing as a trustee district.
  * FOUR ARE THE SLIVER SHAPE and SHIP WITH A HOLE: exactly one uncoded
    ward, 0.0%-1.4% of the city's area (Delavan, De Pere, Green Bay,
    Howard). Inside that sliver the card honestly answers no-district; the
    builder pins each and fails if a second uncoded ward ever appears.

An OPERATOR rebuild after each Jan-15 / Jul-15 filing window, exactly like
the supervisory build this file leans on (fetch/validate/mapshaper are
imported from it). A count change at a window is expected news — read it,
then move the EXPECT constants deliberately.

Usage:
    python3 wi/scripts/build_wi_aldermanic_districts.py
    python3 wi/scripts/build_wi_aldermanic_districts.py --check   # gates only
"""

import json
import os
import random
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from build_wi_supervisory_districts import (  # noqa: E402
    _curl, fetch_layer, _model, _districts_at, MAPSHAPER, STATE_BBOX, WARDS)

REPO_ROOT = os.path.dirname(SCRIPT_DIR)
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
OUT_NAME = "aldermanic-districts.json"

BAS_ALDERS = ("https://mapservices.legis.wisconsin.gov/arcgis/rest/services"
              "/BAS_Collection/BAS_Live_Collection_Alderpersons/FeatureServer/0")

EXPECT_CODED_WARDS = 2580      # all coded wards, towns included
EXPECT_TOWN_CODED = 4          # the Town of Mercer anomaly, Iron County
EXPECT_DISTRICT_KEYS = 867     # distinct COUSUBFP+ALDERID over C/V, AS FILED
EXPECT_MUNICIPALITIES = 165    # C/V municipalities with any coded ward
EXPECT_COMPOSED_WARDS = 50     # Appleton's uncoded Outagamie wards, composed below
EXPECT_TOTAL_KEYS = 878        # 867 filed + Appleton's 11 the state does not file

# The NINE measurably incomplete submissions: COUSUBFP -> (name, uncoded
# wards, uncoded share of the municipality's ward area). Computed fresh from
# the fetch every run and gated against this list — a change is a filing
# window doing its job, and the operator moves the entry with eyes open.
# Appleton left this list on 2026-09-05 through LOCAL_COMPOSITION below; its
# county still files every ward uncoded, and the city itself now supplies the
# assignment. THE OTHER NINE ARE MEASURED SHUT ON THAT SAME ROUTE: Appleton is
# the only one of the ten whose polling places are one-per-district (15 wards
# groups, 15 districts). The rest consolidate — Berlin, Brillion, Cuba City,
# Durand and Edgerton vote at a SINGLE place, Bellevue and Kaukauna at two,
# New London and Port Washington at three — so no ward-to-place grouping can
# name a district there, whatever their own pages say.
EXCLUDED = {
    "06350": ("Bellevue", 11, 0.999),
    "06925": ("Berlin", 6, 0.874),
    "09725": ("Brillion", 2, 0.094),
    "17950": ("Cuba City", 1, 0.158),
    "21225": ("Durand", 1, 0.274),
    "22575": ("Edgerton", 8, 0.873),
    "38800": ("Kaukauna", 17, 0.998),
    "56925": ("New London", 3, 0.429),
    "64450": ("Port Washington", 1, 0.318),
}
# The four sliver-hole cities: ship, with exactly one uncoded ward each.
SLIVER_OK = {"19450": "Delavan", "19775": "De Pere",
             "31000": "Green Bay", "35950": "Howard"}

# ---------------------------------------------------------------------------
# LOCAL COMPOSITION — a municipality whose COUNTY files its wards uncoded and
# whose OWN election authority publishes which district each ward votes in.
#
# APPLETON, ADDED 2026-09-05, is the first and (measured) the only one of the
# ten excluded municipalities this route reaches. Outagamie County submits all
# 50 of its Appleton wards uncoded and has done through four filings; only the
# Calumet and Winnebago fringes carry ids. The city's own ArcGIS org was
# enumerated in full — 72 services, no aldermanic layer — which confirms the
# 2026-08-26 record by a second route and is why nothing here reads a city
# boundary file: there is not one.
#
# WHAT THERE IS is the CITY CLERK's own polling-locations page, which prints
# "District N: <polling place>" and under it the wards that vote there. That is
# the election authority stating the composition, and it is corroborated by TWO
# OTHER PUBLISHERS plus a second edition of the clerk's own assignment.
#
# THE COUNT WAS WRITTEN AS FOUR UNTIL 2026-09-05 AND THAT WAS ONE TOO MANY.
# Items 1 and 2 below are the SAME FACT through a second channel: the Elections
# Commission publishes what each municipality reports, so its ward-to-place file
# IS the Appleton clerk's assignment, machine-readable and already in this repo.
# That makes it the best gate here and NOT an independent voice, and the
# difference matters — three sources agreeing is a weaker claim than four, and
# the record should say the weaker true one.
#
#   1. THE STATE'S POLLING FILE, already shipped in this repo
#      (wi/data/app/{outagamie,calumet,winnebago}-polling-places.json, from the
#      Elections Commission). Appleton's 60 wards group into exactly 15 polling
#      places, one per district, and that grouping reproduces the clerk page's
#      15 ward lists EXACTLY on the 57 wards the page names. This is the gate
#      below: it needs no network and fails if either side moves. SAME SOURCE
#      as the page, second channel — a cross-CHANNEL check, which still catches
#      a mis-transcription, a stale page and a re-warding, and does not catch
#      the clerk being wrong.
#   2. IT ALSO PLACES THE THREE THE PAGE OMITS, which is why it earns its place
#      even without being independent. Wards 51, 59 and 60 are recent annexation
#      slivers (0.025%, 0.714% and 0.012% of the city's area) that the clerk's
#      page does not list; the state's file puts 51 at St Matthew (District 10),
#      59 at Celebration Ministry (District 13) and 60 at First English Lutheran
#      (District 7). They are marked FROM_POLLING_FILE below.
#   3. LTSB'S OWN TEN CODED WARDS — the COUNTIES' filing, a different publisher
#      entirely — agree with the page on all ten (13/14/15→05, 25→08, 33/34→11,
#      44/45/46/47→15). Gated below. This is the one that would catch the clerk
#      being wrong, and it covers ten wards of sixty.
#   4. CENSUS 2020 POPULATION BALANCES: 75,862 across the fifteen, ideal 5,057,
#      worst deviation 6.3% (D4 -6.3%, D12 +3.2%). A plan drawn to a census
#      balances on that census — the Vermilion measurement, applied to a city.
#      Independent of every publisher above, and the check that would catch a
#      composition that was internally consistent and simply not the plan.
#
# A FIFTH SOURCE DISAGREES ON EXACTLY TWO WARDS AND IS RECORDED RATHER THAN
# USED. The city's own parcel service (My_Property_Data_Publish_V2, the data
# behind its "Find your Alderperson" app) carries Aldermanic_Ward and
# Aldermanic_District per parcel. Tallied inside each LTSB ward polygon, 33,570
# parcels agree with the composition on 55 of the 57 wards it covers — and put
# ward 25 in District 11 and ward 33 in District 8, the transpose of what the
# clerk's page and LTSB both say. The parcel field is measurably the PREVIOUS
# ward plan: it knows nothing of wards 48-59, which the other three sources all
# carry, and 1,741 of 20,000 parcels sit in an LTSB ward whose number it does
# not use. So this is a stale layer, not a live disagreement — but it is written
# down, because "two publishers disagree" is never resolved by preference here.
LOCAL_COMPOSITION = {
    "02375": {
        "name": "Appleton",
        "seats": 15,
        # appletonwi.gov/government/departments/clerk/elections/polling_locations.php
        # read 2026-09-05. FOUR OF THE FIFTEEN HEADINGS USE A NON-BREAKING SPACE
        # ("District\xa010:"), which a plain `District (\d+):` read drops in
        # silence — it returns eleven districts and forty-two wards and looks
        # like an incomplete page rather than a parser bug.
        "source_url": ("https://www.appletonwi.gov/government/departments/clerk"
                       "/elections/polling_locations.php"),
        "read_on": "2026-09-05",
        "districts": {
            "01": [1, 2],
            "02": [3, 4, 5, 6, 48],
            "03": [7, 8, 9],
            "04": [10, 11, 12, 52],
            "05": [13, 14, 15, 16],
            "06": [17, 18, 19, 49, 50],
            "07": [20, 21, 22, 54, 60],       # 60 from the state's polling file
            "08": [23, 24, 25, 55],
            "09": [26, 27, 56],
            "10": [28, 29, 30, 51],           # 51 from the state's polling file
            "11": [31, 32, 33, 34, 57],
            "12": [35, 36, 37],
            "13": [38, 39, 40, 41, 53, 58, 59],  # 59 from the state's polling file
            "14": [42, 43],
            "15": [44, 45, 46, 47],
        },
        # the three the clerk's page does not name; the state's file places them
        "from_polling_file": {51: "10", 59: "13", 60: "07"},
        # ward -> polling place, as the shipped WEC files carry it. The gate
        # asserts the composition above partitions the wards exactly the way
        # these places do — a district is one polling place in Appleton and the
        # clerk's page says which, so the two must agree ward for ward.
        "polling_counties": ("outagamie", "calumet", "winnebago"),
        "polling_key": "C|APPLETON|",
    },
}

# 9% (the supervisory build's retain) measured 99.675% agreement here — city
# districts are small, so the same retain cuts proportionally deeper; 25%
# clears the 99.9% bar with the file still compact.
SIMPLIFY = "25%"
PRECISION = "0.000001"
UNCODED = ("", "00", "0000")


def is_coded(alderid):
    return (alderid or "").strip() not in UNCODED


def apply_local_composition(attr_feats):
    """Give each locally-composed municipality's wards the district its own
    election authority publishes, and GATE that assignment three ways before
    a single polygon is drawn.

    Returns (n_wards_composed, {cousubfp: n_districts}).
    """
    by_mun = {}
    for f in attr_feats:
        p = f["properties"]
        if p.get("COUSUBFP") in LOCAL_COMPOSITION and p.get("CTV") in ("C", "V"):
            by_mun.setdefault(p["COUSUBFP"], []).append(f)
    if set(by_mun) != set(LOCAL_COMPOSITION):
        raise RuntimeError("LOCAL_COMPOSITION names %s; the ward layer carries %s"
                           % (sorted(LOCAL_COMPOSITION), sorted(by_mun)))
    composed, shipped = 0, {}
    for cousub, spec in sorted(LOCAL_COMPOSITION.items()):
        feats = by_mun[cousub]
        ward_to_dist = {}
        for dist, wards in spec["districts"].items():
            for w in wards:
                if w in ward_to_dist:
                    raise RuntimeError("%s: ward %d is in two districts (%s, %s)"
                                       % (spec["name"], w, ward_to_dist[w], dist))
                ward_to_dist[w] = dist
        if len(spec["districts"]) != spec["seats"]:
            raise RuntimeError("%s: %d districts composed for a %d-seat council"
                               % (spec["name"], len(spec["districts"]), spec["seats"]))

        # 1. EVERY ward, or none. A partial composition would ship some of a
        #    city's districts as if they were all of them, which is the exact
        #    failure the per-city completeness gate exists to prevent.
        have = set()
        for f in feats:
            try:
                have.add(int(f["properties"]["WARDID"]))
            except (TypeError, ValueError):
                raise RuntimeError("%s: a ward with no numeric WARDID (%r)"
                                   % (spec["name"], f["properties"].get("WARDID")))
        missing = sorted(have - set(ward_to_dist))
        extra = sorted(set(ward_to_dist) - have)
        if missing or extra:
            raise RuntimeError(
                "%s: the composition and the ward layer disagree about which wards "
                "exist — %d in the layer and not composed (%s), %d composed and not "
                "in the layer (%s). A re-warding has happened; re-read the source."
                % (spec["name"], len(missing), missing[:8], len(extra), extra[:8]))

        # 2. IT MUST AGREE WITH EVERY WARD THE STATE DOES CODE. The county files
        #    a handful of these wards with real ids; those are an independent
        #    edition of the same fact and a disagreement means one of the two is
        #    describing a different plan.
        for f in feats:
            p = f["properties"]
            if not is_coded(p.get("ALDERID")):
                continue
            w = int(p["WARDID"])
            if ward_to_dist[w] != p["ALDERID"].strip():
                raise RuntimeError(
                    "%s: ward %d — the state files district %s, the city's own "
                    "source composes it into %s. Two publishers disagree; this "
                    "build does not prefer one."
                    % (spec["name"], w, p["ALDERID"].strip(), ward_to_dist[w]))

        # 3. THE STATE'S POLLING FILE MUST PARTITION THE WARDS THE SAME WAY.
        #    Appleton votes one place per district and its clerk's page says
        #    which; so the grouping the Elections Commission publishes has to be
        #    the composition, group for group. This reads files already in this
        #    repo — no network, and it fires on every build.
        places = {}
        for county in spec["polling_counties"]:
            path = os.path.join(APP_DATA_DIR, "%s-polling-places.json" % county)
            if not os.path.exists(path):
                raise RuntimeError("%s: %s is not in the tree, so the polling-place "
                                   "witness cannot run" % (spec["name"], path))
            with open(path) as fh:
                for key, val in json.load(fh).items():
                    if not key.startswith(spec["polling_key"]):
                        continue
                    if not isinstance(val, dict) or "name" not in val:
                        continue
                    places[int(key.split("|")[2])] = val["name"]
        if set(places) != have:
            raise RuntimeError(
                "%s: the polling file names %d wards and the ward layer %d "
                "(only-in-polling %s, only-in-layer %s)"
                % (spec["name"], len(places), len(have),
                   sorted(set(places) - have)[:6], sorted(have - set(places))[:6]))
        by_place, by_dist = {}, {}
        for w, place in places.items():
            by_place.setdefault(place, set()).add(w)
            by_dist.setdefault(ward_to_dist[w], set()).add(w)
        if sorted(by_place.values(), key=sorted) != sorted(by_dist.values(), key=sorted):
            raise RuntimeError(
                "%s: the state's %d polling places do not partition the wards the "
                "way the %d composed districts do — places %s vs districts %s"
                % (spec["name"], len(by_place), len(by_dist),
                   sorted(map(sorted, by_place.values())),
                   sorted(map(sorted, by_dist.values()))))

        for f in feats:
            p = f["properties"]
            w = int(p["WARDID"])
            if not is_coded(p.get("ALDERID")):
                composed += 1
            p["ALDERID"] = ward_to_dist[w]
        shipped[cousub] = len(spec["districts"])
    return composed, shipped


def classify(attr_feats):
    """Group ward attributes by municipality; return (shipped keys by
    municipality, computed exclusions, computed slivers, town-coded count)."""
    mun = {}
    town_coded = 0
    for f in attr_feats:
        p = f["properties"]
        if is_coded(p.get("ALDERID")) and p.get("CTV") == "T":
            town_coded += 1
            continue
        if p.get("CTV") not in ("C", "V"):
            continue
        m = mun.setdefault(p["COUSUBFP"], {
            "name": p["MCD_NAME"], "ctv": p["CTV"], "coded": 0, "uncoded": 0,
            "coded_area": 0.0, "uncoded_area": 0.0, "districts": set()})
        area = p.get("Shape__Area") or 0.0
        if is_coded(p.get("ALDERID")):
            m["coded"] += 1
            m["coded_area"] += area
            m["districts"].add(p["ALDERID"].strip())
        else:
            m["uncoded"] += 1
            m["uncoded_area"] += area
    coded_mun = {k: m for k, m in mun.items() if m["coded"]}

    excluded, slivers = {}, {}
    for k, m in sorted(coded_mun.items()):
        if not m["uncoded"]:
            continue
        share = m["uncoded_area"] / (m["coded_area"] + m["uncoded_area"])
        if m["uncoded"] == 1 and share < 0.05:
            slivers[k] = m["name"]
        else:
            excluded[k] = (m["name"], m["uncoded"], round(share, 3))
    return coded_mun, excluded, slivers, town_coded


def bas_witness(ltsb_keys):
    """The state's own pre-dissolved layer, a different filing edition, must
    carry exactly the keys the state's WARD layer carries.

    IT IS COMPARED AGAINST THE STATE'S OWN KEYS AND NOT AGAINST WHAT SHIPS.
    Exclusions were always OUR honesty call rather than a disagreement about the
    coding, so they were folded back in; local composition is the same shape one
    step further — Appleton's fifteen districts are the CITY's statement and BAS
    has never carried eleven of them, so comparing against the shipped set would
    fail a witness that is working perfectly."""
    feats = fetch_layer(BAS_ALDERS, "COUSUBFP,CTV,ALDERID", geometry=False)
    bas = set()
    for f in feats:
        p = f["properties"]
        if p.get("CTV") in ("C", "V") and is_coded(p.get("ALDERID")):
            bas.add((p["COUSUBFP"], p["ALDERID"].strip()))
    ours = ltsb_keys
    if bas != ours:
        raise RuntimeError(
            "BAS witness disagrees: %d keys only in BAS (e.g. %s), %d only here (e.g. %s) — "
            "a filing edition moved; re-measure and move the EXPECT constants deliberately"
            % (len(bas - ours), sorted(bas - ours)[:4],
               len(ours - bas), sorted(ours - bas)[:4]))
    return len(bas)


def validate(source_wards, result_districts, samples=4000, seed=2026):
    """In-state sample points: wherever a full-precision coded ward answers,
    the dissolved+simplified district must answer with the same key. Tests
    the dissolve and the simplification in one measure."""
    src = _model(source_wards, "KEY")
    new = _model(result_districts, "KEY")
    rng = random.Random(seed)
    pts = []
    while len(pts) < samples:
        pt = (rng.uniform(STATE_BBOX["minLng"], STATE_BBOX["maxLng"]),
              rng.uniform(STATE_BBOX["minLat"], STATE_BBOX["maxLat"]))
        hits = _districts_at(src, pt)
        if hits:
            pts.append((pt, hits))
    agree = 0
    for pt, o_hits in pts:
        s_hits = _districts_at(new, pt)
        if len(o_hits) == 1 and s_hits == o_hits:
            agree += 1
        elif len(o_hits) > 1:
            agree += 1  # a source self-overlap has no single right answer
    pct = 100.0 * agree / samples
    if pct < 99.9:
        return False, "point agreement only %.3f%% (need >= 99.9%%)" % pct
    return True, "%d/%d (%.3f%%) in-district point agreement" % (agree, samples, pct)


def main():
    check_only = "--check" in sys.argv[1:]

    attrs = fetch_layer(
        WARDS, "WARDID,COUSUBFP,MCD_NAME,CTV,ALDERID,Shape__Area", geometry=False)
    coded_total = sum(1 for f in attrs if is_coded(f["properties"].get("ALDERID")))
    if coded_total != EXPECT_CODED_WARDS:
        raise RuntimeError("ward layer carries %d coded wards, expected %d — a filing "
                           "window moved; re-measure before moving the constant"
                           % (coded_total, EXPECT_CODED_WARDS))
    # The STATE's own keys, taken before anything local is applied: this is what
    # the BAS witness compares against, so a locally composed district can never
    # make the two-edition check pass or fail on its own account.
    ltsb_keys = set()
    for f in attrs:
        p = f["properties"]
        if p.get("CTV") in ("C", "V") and is_coded(p.get("ALDERID")):
            ltsb_keys.add((p["COUSUBFP"], p["ALDERID"].strip()))
    if len(ltsb_keys) != EXPECT_DISTRICT_KEYS:
        raise RuntimeError("%d district keys in the state's filing, expected %d"
                           % (len(ltsb_keys), EXPECT_DISTRICT_KEYS))
    composed_wards, composed_mun = apply_local_composition(attrs)
    if composed_wards != EXPECT_COMPOSED_WARDS:
        raise RuntimeError("local composition assigned %d uncoded wards, expected %d — "
                           "a county has started (or stopped) filing them"
                           % (composed_wards, EXPECT_COMPOSED_WARDS))
    coded_mun, excluded, slivers, town_coded = classify(attrs)
    if town_coded != EXPECT_TOWN_CODED:
        raise RuntimeError("%d coded TOWN wards (expected %d — the Mercer anomaly); "
                           "a town cannot elect alderpersons, re-read the filing"
                           % (town_coded, EXPECT_TOWN_CODED))
    if len(coded_mun) != EXPECT_MUNICIPALITIES:
        raise RuntimeError("%d municipalities carry coded wards, expected %d"
                           % (len(coded_mun), EXPECT_MUNICIPALITIES))
    all_keys = set()
    for k, m in coded_mun.items():
        all_keys |= {(k, d) for d in m["districts"]}
    if len(all_keys) != EXPECT_TOTAL_KEYS:
        raise RuntimeError("%d district keys after composition, expected %d"
                           % (len(all_keys), EXPECT_TOTAL_KEYS))

    if {k: v for k, v in excluded.items()} != EXCLUDED:
        raise RuntimeError(
            "computed exclusions differ from the pinned list:\n  computed: %s\n  pinned:   %s\n"
            "A county completed (or broke) a submission — re-measure, then move EXCLUDED."
            % (json.dumps(excluded, sort_keys=True), json.dumps(EXCLUDED, sort_keys=True)))
    if {k: v for k, v in slivers.items()} != SLIVER_OK:
        raise RuntimeError("computed sliver-hole cities differ from SLIVER_OK: %s vs %s"
                           % (sorted(slivers), sorted(SLIVER_OK)))

    shipped_mun = {k: m for k, m in coded_mun.items() if k not in EXCLUDED}
    shipped_keys = {(k, d) for k, m in shipped_mun.items() for d in m["districts"]}
    excluded_keys = all_keys - shipped_keys
    n_bas = bas_witness(ltsb_keys)
    print("gates: %d coded wards + %d locally composed -> %d districts across %d "
          "municipalities shipped (%d districts in %d incomplete municipalities "
          "excluded; %d sliver holes; %d locally composed: %s; %d Mercer town wards "
          "dropped); BAS witness agrees on all %d of the state's own keys"
          % (coded_total, composed_wards, len(shipped_keys), len(shipped_mun),
             len(excluded_keys), len(EXCLUDED), len(SLIVER_OK), len(composed_mun),
             ", ".join("%s %d" % (LOCAL_COMPOSITION[k]["name"], n)
                       for k, n in sorted(composed_mun.items())),
             town_coded, n_bas),
          file=sys.stderr)
    if check_only:
        return

    # Geometry fetch: every coded C/V ward, PLUS every ward of a locally
    # composed municipality — those are uncoded on the server, so the id filter
    # alone fetches none of them and the count gate below fires (measured: it
    # did, 2,545 against 2,595, which is the gate doing its job). WARDID comes
    # back too because apply_local_composition keys on it, and it runs a SECOND
    # time here rather than trusting the attribute pass: the same three gates,
    # against the features actually about to be dissolved.
    where = ("CTV IN ('C','V') AND (ALDERID IS NOT NULL AND "
             "ALDERID NOT IN ('00','0000','')%s)"
             % "".join(" OR COUSUBFP = '%s'" % k for k in sorted(LOCAL_COMPOSITION)))
    wards = fetch_layer(WARDS, "WARDID,COUSUBFP,MCD_NAME,CTV,ALDERID", where=where)
    apply_local_composition(wards)
    wards = [w for w in wards if w["properties"]["COUSUBFP"] in shipped_mun
             and is_coded(w["properties"].get("ALDERID"))]
    expect_ward_n = sum(m["coded"] for m in shipped_mun.values())
    if len(wards) != expect_ward_n:
        raise RuntimeError("geometry fetch returned %d coded wards, attributes said %d"
                           % (len(wards), expect_ward_n))
    for w in wards:
        p = w["properties"]
        w["properties"] = {
            "KEY": p["COUSUBFP"] + "-" + p["ALDERID"].strip(),
            "COUSUBFP": p["COUSUBFP"],
            "MCD_NAME": p["MCD_NAME"],
            "CTV": p["CTV"],
            "ALDERID": p["ALDERID"].strip(),
        }

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "wards-src.geojson")
        with open(src_path, "w") as f:
            json.dump({"type": "FeatureCollection", "features": wards}, f)
        out_tmp = os.path.join(tmp, "alder.geojson")
        subprocess.run(
            ["npx", "-y", MAPSHAPER, src_path,
             "-dissolve2", "KEY", "copy-fields=COUSUBFP,MCD_NAME,CTV,ALDERID",
             "-simplify", "visvalingam", "keep-shapes", SIMPLIFY,
             "-o", "precision=" + PRECISION, "format=geojson", out_tmp],
            check=True, cwd=REPO_ROOT)
        with open(out_tmp) as f:
            dissolved = json.load(f)

    feats = dissolved["features"]
    if len(feats) != len(shipped_keys):
        raise RuntimeError("dissolve produced %d districts, expected %d"
                           % (len(feats), len(shipped_keys)))
    out_keys = {(f["properties"]["COUSUBFP"], f["properties"]["ALDERID"]) for f in feats}
    if out_keys != shipped_keys:
        raise RuntimeError("dissolved key set differs from the plan (e.g. %s)"
                           % sorted(shipped_keys ^ out_keys)[:4])

    ok, msg = validate(wards, feats)
    if not ok:
        raise RuntimeError("validation failed: %s" % msg)

    feats.sort(key=lambda f: (f["properties"]["COUSUBFP"],
                              f["properties"]["ALDERID"]))
    compact = json.dumps({"type": "FeatureCollection", "features": feats},
                         separators=(",", ":"), ensure_ascii=False)
    out_path = os.path.join(APP_DATA_DIR, OUT_NAME)
    with open(out_path, "w") as f:
        f.write(compact)
    print("aldermanic-districts -> data/app/%s: %d districts, %d municipalities; %s; "
          "%d bytes (%s retain, 6dp)"
          % (OUT_NAME, len(feats), len(shipped_mun), msg, len(compact), SIMPLIFY),
          file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build Jefferson County's 13 board districts by dissolving its own precincts.

WHY THIS IS A DISSOLVE AND NOT A FETCH. Jefferson publishes no boundary of any
kind. Asked on 5 Aug 2026 for both the board districts and the precincts,
County Clerk Joe Davis sent the precinct shapefile on 6 Aug and said nothing
about the districts. `jefferson-county-board` recorded that as an incomplete
answer rather than a refusal, and named the cheap route back:

    "the precincts are now in hand, so a plain LIST of which precincts make up
     each district would be enough to draw the boundaries exactly, with no new
     geometry needed from the county at all."

Re-asked on that basis, and on 7 Aug he sent exactly that — "County Board
Districts (Approved by County Board November 22, 2021)", one line per district
naming its precincts. This script is that list applied to the precinct geometry
already shipped, so the boundaries are the county's own lines throughout: its
precincts, combined the county's own way.

THE LIST ACCOUNTS FOR EVERY PRECINCT, EXACTLY ONCE. All 33 shipped precincts are
named, none is named that does not exist, and only one is split between two
districts. Those three facts are asserted below rather than assumed — a future
list that drops a precinct or invents one fails the build.

THE ONE SPLIT, AND THE ONE INFERENCE IN THIS FILE. The chart puts "Shiloh 4 west
of 34th Street" in District 10 and "Shiloh 4 east of 34th Street" in District 11.
34th Street in Mt. Vernon is a straight north-south street on the city grid, and
the cut is made at its longitude:

  * SOURCE IS TIGER/LINE, deliberately. The Census Bureau's Transportation layer
    puts 34th St at longitude -88.93327 where it meets Shiloh 4. That is a
    public-domain federal dataset. OpenStreetMap agrees (its "North 34th Street"
    runs -88.93334..-88.93327) and was used to CORROBORATE the number, not to
    supply it: OSM is ODbL, and a shipped civic boundary derived from it would
    carry share-alike obligations this project has not taken on. One coordinate
    read from TIGER carries none.

  * AND THE COUNTY'S OWN LINE AGREES, established 2026-08-10. The county's
    published precinct legal descriptions define Shiloh 3 as "south of Broadway
    and east of 34th Street", so the county itself uses this street as a
    boundary — and the Shiloh 3 edge in the county's shapefile runs from
    (-88.933129, 38.299878) up to (-88.933578, 38.314337), a straight line whose
    midpoint sits about SEVEN METRES from the TIGER longitude used here. Two
    independent sources and the county's own geometry all put the cut in the
    same place, so it is not moved: the county's two-point edge leans 39 m west
    over its length, which is digitising noise in a file whose median boundary
    error is 35 m, and chasing that lean would be fitting the noise.

  * WHERE IT IS EXACT, AND WHERE IT IS NOT. 34th Street is mapped from the south
    edge of Shiloh 4 up to about latitude 38.3211, which is roughly three
    quarters of the way up the precinct. North of that the street stops and this
    cut CONTINUES ITS ALIGNMENT as a meridian. That extension covers about a
    quarter of Shiloh 4 — 0.05% of the county — and it is not empty ground: it
    holds the Chesterfield Village, Webster Hill and Kingsridge subdivisions.
    Only Districts 10 and 11 are affected and both say so on the card.

    THE COUNTY WAS ASKED AND ANSWERED, AND THE ANSWER DOES NOT REACH THIS FAR.
    Clerk Davis was asked on 2026-08-07 where the line runs north of the
    pavement, and on 2026-08-10 replied by pointing at the precinct legal
    descriptions above — a page this project had not found, and a real gain:
    it is the first PUBLIC source for anything geographic in Jefferson County,
    it is what scripts/build_jefferson_precincts.py now checks all 33 precincts
    against, and it settles that "34th Street" is a line the county draws. What
    it does not do is say where that line goes once the street stops. So the
    projection stands, the boundaryNote stands, and nothing here is presented
    as more settled than it is.

    THE THREAD IS CLOSED, 2026-08-11, by decision rather than by an answer.
    The shipped geometry was reviewed and accepted as accurate, so the yes/no
    that was drafted back to Clerk Davis was withdrawn unsent and nothing is
    outstanding with that office. The boundaryNote is NOT retired with it: it
    describes how this stretch of line was drawn, which is still true, and a
    reader deciding whether to trust it is owed that whether or not anyone is
    still asking the county. Closing an ask and deleting a caveat are different
    acts, and only the first one happened.

    This is the honest shape of the uncertainty: exact for three quarters of the
    boundary, a straight projection for the rest. LaSalle is the precedent for
    the coarser alternative — its split precincts ship wholly on their majority
    side with the card saying so — and this is strictly better than that.

WHY THE DISSOLVE IS REPAIRED, added 2026-08-10 after a reader reported "strange
artifacts" in these boundaries. They were real, and a plain unary_union of the
precincts could not have avoided them:

  * 108 SLIVER HOLES. The worst was 7,545 m long and 124 m wide, sitting inside
    District 8; District 7 had 64 of them along one township line. A hole is
    STROKED, so each one drew a dark line across the middle of a filled
    district — which is exactly what the reader saw.
  * FIVE SPURIOUS PARTS. District 7 rendered as two disconnected blocks and
    District 5 as two more, because a crack ran the full width between two of
    their own precincts. Four others carried 20–1,850 m2 specks of dust that
    drew as detached dots.
  * 28 OVERLAPPING PAIRS, the worst 33,126 m2, because the county's own
    precincts overlap each other and dissolving pooled those overlaps.

THE CAUSE IS ONE STEP UPSTREAM, and it is worth naming because the docstring of
build_jefferson_precincts.py got it wrong. That builder repairs the county's
unmatched precinct edges and then simplifies each precinct, claiming "a shared
edge stays shared because both neighbours simplify the SAME linework with the
same tolerance and Douglas-Peucker is deterministic". DP is deterministic on
identical INPUT, and two neighbouring rings are not identical input: they share a
sub-path but differ everywhere else, and which vertices DP keeps on that shared
sub-path depends on the whole ring. So shared edges diverge by up to a tolerance
or two, which is precisely the residue that file reports as reopened. Invisible
in the precinct layer — a hairline between two precincts draws as nothing — and
glaring once precincts are merged into districts.

resolve_tiling() repairs the dissolve, and its three passes are documented
there. Jefferson is the only dissolve in the fleet that needs it: every other
county-board file built the same way has holes of at most 191 m2, because their
source precincts arrived edge-matched and never went through a repair-then-
simplify.

AND THEN THE SAME READER LOOKED CLOSER, TWICE MORE. Each round left something
smaller standing, and each thing standing had a different cause, so all three
are recorded rather than folded together.

ROUND TWO — "jagged lines and a spike" on District 10's southern edge. Also
real, also not fixable here, and the reason the precinct file WAS re-cut after
all (this docstring said it would not be; that was written before the report).
Two faults, both in build_jefferson_precincts.py and both documented there:
SIMPLIFY_TOLERANCE_M was 10 m, on the wrong side of a cliff — it cannot remove a
zig-zag whose amplitude is the 30 m Voronoi sampling step, so all 3,057 zig-zag
vertices survived — and simplification at any tolerance keeps an isolated spike
by construction, including one 33 m south of a straight township line on ground
the county never drew. 15 m plus an explicit despike pass fixed both, and these
districts inherited the fix: 2,458 vertices to 688, 1,521 zig-zag vertices to 16.

ROUND THREE — a line standing INSIDE District 10, rising out of its southern
edge. Two separate causes, both in this file, both at the 34th Street cut, and
both fixed here:

  * A 9 m wide, 408 m tall slice of Shiloh 4 fell east of the TIGER meridian but
    SOUTH OF BROADWAY, where the county's own description says there is no
    Shiloh 4 east of 34th Street at all — that ground is Shiloh 3. It was
    District 11 territory standing inside District 10. The split block now
    returns any part stranded below Shiloh 3's northern edge to the west side.
  * A 7 m wide, 190 m deep SLOT between Shiloh 3 and Shiloh 4, both walls
    District 10, which resolve_tiling's reach rule declined because the slot's
    mouth opens onto the District 5 township line and the reach rule is blind to
    shape. Pass 2b adds the shape test: a crack whose outline one district holds
    90% of is surrounded by it, not shared with a neighbour.

District 10 ended at 14 vertices, from 129 before any of this.

ROUND FOUR — four clicks near district borders, each answering "This point
isn't inside any district in this layer." All four landed in inter-district
hairlines: the reach rule claims only ground no other district could want, so
cracks BETWEEN two districts stayed unowned. On the numbers that looked
defensible — 0.0235% of the county, one click in four thousand — and on the
screen it is simply a false answer, because the point IS in a district and the
county's file merely has a crack there. That is the same sentence
build_jefferson_precincts.py uses to justify closing these one layer down, so
they are closed at both layers now: close_reopened() there, pass 2b here.
Jefferson tiles 100.0000% at precinct and district level, and every one of the
four points answers.

Usage:
    python3 scripts/build_jefferson_board_districts.py            # write data/app/
    python3 scripts/build_jefferson_board_districts.py --check    # drift gate
"""

import argparse
import json
import math
import os
import sys

try:
    from shapely.geometry import box, shape, mapping, MultiPolygon, Polygon
    from shapely.ops import unary_union
except ImportError:  # pragma: no cover
    sys.exit("shapely is required: pip install -c scripts/requirements.txt shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECINCTS = os.path.join(REPO_ROOT, "il", "data", "app", "jefferson-precincts.json")
OUTLINE = os.path.join(REPO_ROOT, "il", "data", "app", "jefferson-county-outline.json")
OUT_PATH = os.path.join(REPO_ROOT, "il", "data", "app",
                        "jefferson-county-board-districts.json")

SOURCE_NOTE = ("Jefferson County Clerk & Recorder Joe Davis, \"County Board "
               "Districts (Approved by County Board November 22, 2021)\", "
               "supplied by e-mail 2026-08-07")
CUT_SOURCE = ("US Census Bureau TIGER/Line Transportation, layer 8 (Local "
              "Roads), feature \"34th St\" at Mt. Vernon, IL — public domain")

COORD_PRECISION = 6
EXPECTED_DISTRICTS = 13
EXPECTED_PRECINCTS = 33

# 34th Street's longitude where it bounds Shiloh 4 (see the docstring). The
# street runs north only to about SPLIT_STREET_TOP_LAT; above that this cut is
# the street's alignment projected, which is the single inference in this file.
SHILOH_4_CUT_LON = -88.93327
SPLIT_STREET_TOP_LAT = 38.32106

# The county's approved composition, transcribed from SOURCE_NOTE. Precinct names
# are as data/app/jefferson-precincts.json names them (the county's own export),
# with the chart's "Mt. Vernon N" written the county's shorter way, "Mt V N".
# A precinct paired with a side ("west"/"east") is split by SHILOH_4_CUT_LON.
COMPOSITION = {
    1:  ["Casner", "Grand Prairie", "Rome 2"],
    2:  ["Farrington", "Field", "Rome 1"],
    3:  ["Shiloh 1", "Shiloh 2", "Mt V 7"],
    4:  ["Mt V 2", "Webber 2"],
    5:  ["Blissville", "McClellan", "Shiloh 5"],
    6:  ["Dodds 1", "Dodds 2"],
    7:  ["Bald Hill", "Elk Prairie", "Spring Garden 1", "Spring Garden 2"],
    8:  ["Moores Prairie", "Pendleton", "Webber 1"],
    9:  ["Mt V 3", "Mt V 5"],
    10: ["Shiloh 3", ("Shiloh 4", "west")],
    11: ["Mt V 8", "Mt V 9", ("Shiloh 4", "east")],
    12: ["Mt V 1", "Mt V 4"],
    13: ["Mt V 6", "Mt V 10"],
}
# Districts whose geometry depends on the projected part of the cut. Their cards
# carry the caveat; nothing else in the county does.
SPLIT_DISTRICTS = (10, 11)
# The precinct that holds the ground east of 34th Street south of Broadway, per
# the county's published description. It is what the split is checked against so
# the cut cannot strand a slice of Shiloh 4 down there; see the split block.
SPLIT_NEIGHBOUR = "Shiloh 3"
MAX_STRANDED_M2 = 20000.0

# Two districts holding one precinct each would be a transcription slip, not a
# board. The real minimum is District 4 and several others at 2.
MIN_PRECINCTS_PER_DISTRICT = 2

# --- making the districts a partition of the county -------------------------
# See "WHY THE DISSOLVE IS REPAIRED" in the module docstring. These are the
# knobs of that repair, and every one of them has a ceiling asserted below it so
# a future export that needs MORE repair fails the build instead of being
# quietly patched.
LAT = 38.3                              # county mid-latitude, for metre maths
# How far a district may reach into unowned ground. Only ground with exactly ONE
# district within this distance is claimed, so the number is a reach and not a
# tolerance: it has to exceed the widest crack (124 m as shipped) without being
# so wide that a district could stretch across a neighbour — which it cannot do
# in any case, because a second district in reach leaves the ground unowned.
GAP_REACH_M = 150.0
# A detached fragment smaller than this is drafting dust, not territory: the
# largest is 43 m across. Dropped, and the total dropped is asserted.
DUST_M2 = 5000.0
# A crack at or under this size goes WHOLE to the district holding the most of
# its outline; anything larger is split between its neighbours instead, because
# the two biggest are lattices spanning 9 and 14 km and handing one of those to
# a single district would run a ribbon of it along other districts' borders.
WHOLE_CRACK_MAX_M2 = 20000.0
# How far into a split crack each bordering district reaches. Comfortably more
# than half the widest crack, so nothing is left over.
CRACK_HALF_WIDTH_M = 40.0
# Ceilings. The repair is meant to be a hairline correction; if it ever has real
# work to do, that is a changed export and a human should look at it.
MAX_OVERLAP_RESOLVED_PCT = 0.05         # of the county
MAX_HOLES_FILLED_PCT = 0.02
MAX_DUST_DROPPED_PCT = 0.005
MIN_COUNTY_COVERED_PCT = 99.99
# The repair's whole footprint against the unrepaired dissolve, and the finished
# districts' agreement with the county outline itself.
# The repair's whole footprint against the raw dissolve. It rose to 0.051% when
# pass 2b started closing the inter-district cracks as well: that ground is
# exactly the residue the precinct file reports as reopened, so the two numbers
# are the same fact seen from either end.
MAX_REPAIR_FOOTPRINT_PCT = 0.10
# The county's own precincts sit ~0.08% of the county's area outside the TIGER
# county outline; the districts inherit that and are not trimmed to it.
MAX_OUTLINE_OVERSHOOT_PCT = 0.15
# What rounding to COORD_PRECISION can re-create along a shared edge. The
# shipped worst is 74 m2, against 33,126 m2 before the repair existed.
MAX_ROUNDED_OVERLAP_M2 = 500.0


def parts_of(geom):
    if geom.is_empty:
        return []
    return list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]


def resolve_tiling(raw, outline):
    """Turn 13 overlapping, cracked dissolves into 13 disjoint districts.

    Three passes, each conservative in a different direction, and none of them
    invents a boundary the county did not draw:

    1. DOUBLE-CLAIMED GROUND goes to the lower-numbered district. The county's
       own precincts overlap each other in 28 places, so their dissolves do
       too. Any tie-break here is arbitrary — the ground is claimed twice in the
       source — so this one is chosen for being deterministic and states itself
       plainly rather than for being clever.
    2. UNOWNED CRACKS go to the district that is the ONLY one within reach. This
       is the pass that does the visible work, and it is provably safe: ground
       with a single district within GAP_REACH_M cannot belong to any other. A
       crack between two DIFFERENT districts has two districts in reach, so it
       stays unowned and stays a hairline — invisible, because only one district
       is ever drawn filled at a time.
    3. WHAT IS LEFT is tidied: an interior ring that contains no other
       district's ground is unowned land this district encloses, so it is
       filled; a detached fragment under DUST_M2 is dropped. A ring that DOES
       contain another district — a real enclave — is kept, so the rule survives
       a future map where one district surrounds another.

    Returns (districts, report).
    """
    metres = 111320.0 * math.cos(math.radians(LAT))
    reach = GAP_REACH_M / metres
    weld = 1e-7          # ~1 cm, so a claimed crack OVERLAPS rather than merely
                         # abuts; abutting rings do not merge under unary_union
    county = outline.area

    def make_disjoint(geoms):
        out, taken, lost = {}, None, 0.0
        for key in sorted(geoms):
            geom = geoms[key]
            if taken is not None:
                clipped = geom.difference(taken)
                lost += geom.area - clipped.area
                geom = clipped
            if not geom.is_valid:
                geom = geom.buffer(0)
            out[key] = geom
            taken = geom if taken is None else unary_union([taken, geom])
        return out, lost

    # 1 — disjointness.
    disjoint, overlap_area = make_disjoint(raw)

    # 2 — unowned cracks.
    residue = outline.difference(unary_union(list(disjoint.values())))
    grown = {}
    for district, geom in disjoint.items():
        others = unary_union([g.buffer(reach) for d, g in disjoint.items()
                              if d != district])
        own = residue.intersection(geom.buffer(reach)).difference(others)
        if own.is_empty:
            grown[district] = geom
            continue
        # The weld is what makes the claimed crack MERGE with the district
        # rather than sit against it — abutting rings do not merge under
        # unary_union. It grows the claim by a centimetre, which can graze the
        # neighbouring claim where two districts' cracks meet, so disjointness
        # is re-imposed below rather than argued about here.
        grown[district] = unary_union([geom, own.buffer(weld)])

    # 2b — EVERY REMAINING CRACK, because "no district" is the wrong answer.
    #
    # The reach rule above is exact and conservative: it claims only ground no
    # other district could want. What it leaves is the hairlines BETWEEN two
    # different districts, and leaving those unowned looked defensible on the
    # numbers — 0.0235% of the county, one click in four thousand — right up
    # until a reader found three of them by clicking near borders and got "This
    # point isn't inside any district in this layer." That answer is false. The
    # point IS in a district; the county's file merely has a crack there, which
    # is the same sentence build_jefferson_precincts.py uses to justify closing
    # these one layer down. Closing them here is the same call, made again.
    #
    # A crack goes to the district holding the largest share of its outline.
    # That is nearest-boundary in the form this geometry allows, and it costs a
    # boundary shift of at most the crack's width — tens of metres, inside the
    # 34 m median the precinct repair already discloses — against a wrong answer
    # for anyone who clicks there.
    #
    # BIG PIECES ARE SPLIT INSTEAD OF GIVEN AWAY. Two of the cracks are lattices
    # spanning 9 and 14 km and touching four districts and three; handing either
    # wholly to one district would run a 12 m ribbon of it along boundaries two
    # OTHER districts share, which is a wrong answer of a worse kind than the
    # one being fixed. Above WHOLE_CRACK_MAX_M2 each bordering district instead
    # takes the part within CRACK_HALF_WIDTH_M of itself, in order of how much
    # of the outline it holds. Buffering a straight edge gives a straight
    # parallel line, so this adds no zig-zag.
    remaining = outline.difference(unary_union(list(grown.values())))
    for piece in parts_of(remaining):
        perimeter = piece.exterior.length
        if perimeter <= 0:
            continue
        shares = sorted(
            ((piece.exterior.intersection(geom.buffer(weld * 30)).length / perimeter, district)
             for district, geom in grown.items()
             if piece.exterior.intersects(geom.buffer(weld * 30))), reverse=True)
        if not shares:
            continue
        if piece.area * metres * 111320.0 <= WHOLE_CRACK_MAX_M2:
            owner = shares[0][1]
            grown[owner] = unary_union([grown[owner], piece.buffer(weld)])
            continue
        half = CRACK_HALF_WIDTH_M / metres
        for _, district in shares:
            part = piece.intersection(
                grown[district].buffer(half, join_style=2, quad_segs=1))
            if part.is_empty:
                continue
            grown[district] = unary_union([grown[district], part.buffer(weld)])
            piece = piece.difference(part)
            if piece.is_empty:
                break

    # The welds are centimetres wide, so this second pass moves nothing worth
    # reporting; only the first pass's overlap is the county's own double claim.
    grown, _weld_overlap = make_disjoint(grown)

    # 3 — tidy.
    out, filled_area, dust_area, kept_holes = {}, 0.0, 0.0, 0
    for district, geom in grown.items():
        elsewhere = unary_union([g for d, g in grown.items() if d != district])
        kept = []
        for part in parts_of(geom):
            if part.area * metres * 111320.0 < DUST_M2:
                dust_area += part.area
                continue
            rings = []
            for ring in part.interiors:
                hole = Polygon(ring)
                # A hole's rim always grazes its neighbours, so "another district
                # is in here" has to mean real ground, not a rim: one square
                # metre, the same floor the overlap check uses. Anything above it
                # keeps its ring, which is also what keeps this pass from
                # swallowing a neighbour and undoing the disjointness above.
                shared = (hole.intersection(elsewhere).area * metres * 111320.0
                          if hole.is_valid else 0.0)
                if shared > 1.0:
                    rings.append(ring)      # a real enclave: another district lives there
                    kept_holes += 1
                else:
                    filled_area += hole.area
            kept.append(Polygon(part.exterior, rings))
        if not kept:
            sys.exit("District %d has no part left after dropping dust — that is "
                     "not dust, that is the district" % district)
        out[district] = kept[0] if len(kept) == 1 else MultiPolygon(kept)

    # No third disjointness pass, deliberately: one after the tidy would clip
    # the filled rings back open as 5-metre specks, which is how the first
    # version of this function ended up shipping four of them. The tidy cannot
    # break disjointness on its own, because a ring holding another district's
    # ground is kept rather than filled.
    covered = unary_union(list(out.values()))
    report = {
        "overlap_pct": overlap_area / county * 100.0,
        "filled_pct": filled_area / county * 100.0,
        "dust_pct": dust_area / county * 100.0,
        "covered_pct": covered.intersection(outline).area / county * 100.0,
        "kept_holes": kept_holes,
        "parts": sum(len(parts_of(g)) for g in out.values()),
        "holes": sum(len(p.interiors) for g in out.values() for p in parts_of(g)),
    }
    if report["overlap_pct"] > MAX_OVERLAP_RESOLVED_PCT:
        sys.exit("the districts claim %.4f%% of the county twice (max %.2f%%) — "
                 "that is more than drafting overlap, so the composition list "
                 "or the precinct file needs re-reading" % (report["overlap_pct"],
                                                            MAX_OVERLAP_RESOLVED_PCT))
    if report["filled_pct"] > MAX_HOLES_FILLED_PCT:
        sys.exit("filling enclosed cracks moved %.4f%% of the county (max %.2f%%)"
                 % (report["filled_pct"], MAX_HOLES_FILLED_PCT))
    if report["dust_pct"] > MAX_DUST_DROPPED_PCT:
        sys.exit("dropping detached fragments would lose %.4f%% of the county "
                 "(max %.3f%%) — those fragments are territory, not dust"
                 % (report["dust_pct"], MAX_DUST_DROPPED_PCT))
    if report["covered_pct"] < MIN_COUNTY_COVERED_PCT:
        sys.exit("the 13 districts tile only %.4f%% of Jefferson (need >= %.2f%%)"
                 % (report["covered_pct"], MIN_COUNTY_COVERED_PCT))
    # Pairwise disjointness is by construction, so this is checking arithmetic,
    # not policy: GEOS leaves specks of ~1e-20 deg2 behind a difference, and the
    # honest question is whether any pair still shares GROUND. One square metre
    # is four orders of magnitude below the smallest thing anyone can click.
    keys, worst, worst_pair = sorted(out), 0.0, None
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            shared = out[keys[i]].intersection(out[keys[j]]).area * metres * 111320.0
            if shared > worst:
                worst, worst_pair = shared, (keys[i], keys[j])
    if worst > 1.0:
        sys.exit("Districts %d and %d still share %.1f m2 after the repair"
                 % (worst_pair[0], worst_pair[1], worst))
    report["worst_overlap_m2"] = worst
    return out, report


def round_geom(geom):
    def fix(coords):
        if isinstance(coords[0], (float, int)):
            return [round(coords[0], COORD_PRECISION), round(coords[1], COORD_PRECISION)]
        return [fix(c) for c in coords]
    geo = mapping(geom)
    return {"type": geo["type"], "coordinates": fix(geo["coordinates"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and fail on drift; writes nothing")
    args = parser.parse_args()

    with open(PRECINCTS) as handle:
        data = json.load(handle)
    precincts = {}
    for feature in data["features"]:
        name = feature["properties"]["name"]
        geom = shape(feature["geometry"])
        precincts[name] = geom if geom.is_valid else geom.buffer(0)
    if len(precincts) != EXPECTED_PRECINCTS:
        sys.exit("expected %d shipped precincts, found %d"
                 % (EXPECTED_PRECINCTS, len(precincts)))

    # --- the list must account for every precinct, exactly once -------------
    named, split_names = {}, set()
    for district, members in COMPOSITION.items():
        for member in members:
            name, side = member if isinstance(member, tuple) else (member, None)
            named.setdefault(name, []).append(district)
            if side:
                split_names.add(name)
    missing = sorted(set(precincts) - set(named))
    invented = sorted(set(named) - set(precincts))
    if missing or invented:
        sys.exit("the county's district list and the shipped precincts disagree.\n"
                 "  shipped but in no district: %s\n"
                 "  in a district but not shipped: %s\n  %s"
                 % (missing, invented, SOURCE_NOTE))
    doubled = sorted(n for n, ds in named.items() if len(ds) > 1)
    if sorted(split_names) != doubled:
        sys.exit("precinct(s) %s appear in more than one district but are not "
                 "marked as split, or vice versa (marked split: %s)"
                 % (doubled, sorted(split_names)))
    if len(COMPOSITION) != EXPECTED_DISTRICTS:
        sys.exit("expected %d districts, the list has %d"
                 % (EXPECTED_DISTRICTS, len(COMPOSITION)))

    # --- the one split ------------------------------------------------------
    pieces = {}
    for name in split_names:
        whole = precincts[name]
        minx, miny, maxx, maxy = whole.bounds
        pad = 0.01
        west = whole.intersection(box(minx - pad, miny - pad, SHILOH_4_CUT_LON, maxy + pad))
        east = whole.intersection(box(SHILOH_4_CUT_LON, miny - pad, maxx + pad, maxy + pad))
        if west.is_empty or east.is_empty:
            sys.exit("%s: the cut at longitude %.5f leaves one side empty — the "
                     "precinct no longer straddles 34th Street, so the county's "
                     "split description needs re-reading.\n  %s"
                     % (name, SHILOH_4_CUT_LON, CUT_SOURCE))
        lost = abs((west.area + east.area) - whole.area) / whole.area
        if lost > 1e-9:
            sys.exit("%s: cutting lost %.3g of the precinct's area" % (name, lost))

        # SOUTH OF BROADWAY THERE IS NO SHILOH 4 EAST OF 34th STREET. That ground
        # is Shiloh 3, by the county's own published description — "south of
        # Broadway (aka Illinois Route 15) and east of 34th Street". So anything
        # the cut strands down there is not territory, it is the few metres by
        # which the TIGER meridian and the county's own Shiloh 3 edge disagree,
        # and it belongs on the west side, which is the district Shiloh 3 is in.
        #
        # Left alone it shipped as a 9 m wide, 408 m tall slice of District 11
        # standing inside District 10, which drew as a line rising out of
        # District 10's southern edge — reported by a reader on 2026-08-10, and
        # the third and last of that report's artifacts.
        #
        # The test is per connected PART and uses the neighbour's own northern
        # extent, so it cannot touch the real east lobe (which reaches 1.1 km
        # further north) and needs no latitude hardcoded.
        broadway = precincts[SPLIT_NEIGHBOUR].bounds[3]
        stranded = [p for p in parts_of(east) if p.bounds[3] < broadway]
        if stranded:
            strays = unary_union(stranded)
            metres = 111320.0 * math.cos(math.radians(LAT))
            strand_m2 = strays.area * metres * 111320.0
            if strand_m2 > MAX_STRANDED_M2:
                sys.exit("%s: the cut strands %.0f m2 east of 34th Street but south "
                         "of %s's northern edge (max %.0f m2). At that size it is "
                         "not a datum mismatch and the split needs re-reading.\n  %s"
                         % (name, strand_m2, SPLIT_NEIGHBOUR, MAX_STRANDED_M2, CUT_SOURCE))
            east = east.difference(strays)
            west = unary_union([west, strays])
            print("  note: %d stranded piece(s) east of the cut but south of %s "
                  "(%.0f m2) returned to the west side"
                  % (len(stranded), SPLIT_NEIGHBOUR, strand_m2))

        pieces[(name, "west")], pieces[(name, "east")] = west, east
        if whole.bounds[3] <= SPLIT_STREET_TOP_LAT:
            sys.exit("%s no longer extends north of 34th Street's mapped end — "
                     "the projected part of this cut may no longer be needed, "
                     "which is good news worth re-reading the geometry for" % name)

    # --- dissolve -----------------------------------------------------------
    raw, labels_of = {}, {}
    for district in sorted(COMPOSITION):
        parts, labels = [], []
        for member in COMPOSITION[district]:
            name, side = member if isinstance(member, tuple) else (member, None)
            parts.append(pieces[(name, side)] if side else precincts[name])
            labels.append("%s (%s of 34th St)" % (name, side) if side else name)
        if len(parts) < MIN_PRECINCTS_PER_DISTRICT:
            sys.exit("District %d has only %d precinct(s)" % (district, len(parts)))
        geom = unary_union(parts)
        raw[district] = geom if geom.is_valid else geom.buffer(0)
        labels_of[district] = labels

    # --- repair the tiling --------------------------------------------------
    with open(OUTLINE) as handle:
        outline = shape(json.load(handle)["features"][0]["geometry"])
    if not outline.is_valid:
        outline = outline.buffer(0)
    resolved, repair = resolve_tiling(raw, outline)

    features = []
    for district in sorted(resolved):
        props = {"district": district, "name": "District %d" % district,
                 "precincts": labels_of[district]}
        if district in SPLIT_DISTRICTS:
            props["boundaryNote"] = (
                "Within Shiloh 4 this district's edge follows 34th Street. North "
                "of where 34th Street ends the line follows the street's "
                "alignment projected north — the County Clerk's published "
                "precinct descriptions use 34th Street as a boundary but do not "
                "say where it runs past the pavement.")
        features.append({"type": "Feature", "properties": props,
                         "geometry": round_geom(resolved[district])})

    # The districts must be the same ground as the precincts, give or take the
    # repair. Before the repair existed this was an equality at 0.01%; it cannot
    # be one now, because closing the cracks deliberately ADDS ground the
    # precincts left unowned. So it becomes a ceiling on the repair's footprint,
    # and the equality moves to the county outline, which is what the districts
    # are now supposed to tile.
    whole_county = unary_union(list(precincts.values()))
    dissolved = unary_union([shape(f["geometry"]) for f in features])
    drift = whole_county.symmetric_difference(dissolved).area / whole_county.area * 100
    if drift > MAX_REPAIR_FOOTPRINT_PCT:
        sys.exit("the 13 districts differ from the 33 precincts by %.4f%% (max "
                 "%.2f%%) — the repair is meant to close hairline cracks, so "
                 "that much movement is a changed export" % (drift,
                                                             MAX_REPAIR_FOOTPRINT_PCT))
    # The districts' agreement with the OUTLINE is asserted one way only, as
    # coverage, inside resolve_tiling. A symmetric difference would be the wrong
    # test and would never pass: the county's own precincts sit 0.08% of the
    # county OUTSIDE the TIGER outline, because the two are different vintages
    # of the same border. Where they disagree the county's file is the county's,
    # so the districts follow it out there rather than being trimmed to TIGER.
    # resolve_tiling proved the districts disjoint to within a square metre, but
    # what SHIPS is rounded to COORD_PRECISION — about 10 cm — and rounding two
    # sides of a kilometre-long shared edge in opposite directions re-creates a
    # little overlap. This is the check on the file rather than on the algebra.
    shipped = [(f["properties"]["district"], shape(f["geometry"])) for f in features]
    metres = 111320.0 * math.cos(math.radians(LAT))
    worst, worst_pair = 0.0, None
    for i in range(len(shipped)):
        for j in range(i + 1, len(shipped)):
            area = shipped[i][1].intersection(shipped[j][1]).area * metres * 111320.0
            if area > worst:
                worst, worst_pair = area, (shipped[i][0], shipped[j][0])
    if worst > MAX_ROUNDED_OVERLAP_M2:
        sys.exit("after rounding to %d decimals Districts %d and %d overlap by "
                 "%.0f m2 (max %.0f) — more than rounding can explain"
                 % (COORD_PRECISION, worst_pair[0], worst_pair[1], worst,
                    MAX_ROUNDED_OVERLAP_M2))

    overshoot = dissolved.difference(outline).area / outline.area * 100
    if overshoot > MAX_OUTLINE_OVERSHOOT_PCT:
        sys.exit("the districts extend %.4f%% of the county's area beyond the "
                 "county outline (max %.2f%%) — that is more than the two "
                 "borders' vintages differ by, so check SOURCE_EPSG and the "
                 "outline before shipping" % (overshoot, MAX_OUTLINE_OVERSHOOT_PCT))

    payload = json.dumps({"type": "FeatureCollection", "features": features},
                         sort_keys=True, separators=(",", ":")) + "\n"

    print("Jefferson: %d board districts dissolved from %d precincts"
          % (len(features), len(precincts)))
    print("  every precinct used exactly once; 1 split (%s) cut at lon %.5f"
          % (", ".join(sorted(split_names)), SHILOH_4_CUT_LON))
    print("  districts differ from the raw precinct union by %.4f%% (that is the "
          "repair) and sit %.4f%% outside the TIGER outline (that is the source)"
          % (drift, overshoot))
    print("  worst overlap between two districts as shipped: %.0f m2 (rounding)" % worst)
    print("  repair: %d part(s) for %d districts, %d interior ring(s) left, "
          "%d real enclave(s)"
          % (repair["parts"], len(features), repair["holes"], repair["kept_holes"]))
    print("          double-claimed %.4f%% of the county resolved to the lower "
          "district; enclosed cracks filled %.4f%%; dust dropped %.5f%%"
          % (repair["overlap_pct"], repair["filled_pct"], repair["dust_pct"]))
    print("          the 13 districts now tile %.4f%% of Jefferson"
          % repair["covered_pct"])
    print("  source: %s" % SOURCE_NOTE)
    print("  cut:    %s" % CUT_SOURCE)

    existing = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as handle:
            existing = handle.read()
    if args.check:
        if existing != payload:
            sys.exit("DRIFT: %s does not match a fresh build"
                     % os.path.relpath(OUT_PATH, REPO_ROOT))
        print("  --check OK — matches a fresh build")
        return
    with open(OUT_PATH, "w") as handle:
        handle.write(payload)
    print("  wrote %s (%s bytes)"
          % (os.path.relpath(OUT_PATH, REPO_ROOT), "{:,}".format(len(payload))))


if __name__ == "__main__":
    main()

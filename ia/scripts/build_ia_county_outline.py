#!/usr/bin/env python3
"""
Build data/app/<slug>-county-outline.json for one or more Iowa counties — the
per-county boundary a Data-gaps entry's `counties` list points a reader's map
highlight at (scripts/build_coverage_gaps.py's schema requires one of these
per listed county slug).

Unlike the Illinois fleet's scripts/build_county_outline.py, this needs no
live fetch or simplification pass: every Iowa county's boundary is already
shipped, at the same precision the rest of this app uses, in
data/app/state-counties.json (ia/scripts/build_state_counties.py). This
script only extracts one county's feature from that file and writes it
standalone, so a gap's outline can never disagree with the county layer's own
boundary.

Usage:
    python3 ia/scripts/build_ia_county_outline.py jones
    python3 ia/scripts/build_ia_county_outline.py jones story   # multiple
"""

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ia/
APP_DATA_DIR = os.path.join(REPO_ROOT, "data", "app")
STATE_COUNTIES = os.path.join(APP_DATA_DIR, "state-counties.json")


def main():
    slugs = [s.lower() for s in sys.argv[1:]]
    if not slugs:
        raise SystemExit("usage: build_ia_county_outline.py <slug> [<slug> ...]")

    with open(STATE_COUNTIES) as f:
        sc = json.load(f)
    by_slug = {}
    for feat in sc["features"]:
        p = feat["properties"]
        basename = p.get("BASENAME") or (p.get("NAME") or "").replace(" County", "")
        slug = basename.lower().replace(" ", "").replace("'", "")
        by_slug[slug] = feat

    for slug in slugs:
        feat = by_slug.get(slug)
        if feat is None:
            raise SystemExit(
                "no county in state-counties.json matches slug %r (known: %s)"
                % (slug, sorted(by_slug))
            )
        p = feat["properties"]
        out = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"NAME": p["NAME"], "GEOID": p["GEOID"]},
                "geometry": feat["geometry"],
            }],
        }
        out_path = os.path.join(APP_DATA_DIR, "%s-county-outline.json" % slug)
        compact = json.dumps(out, separators=(",", ":"))
        with open(out_path, "w") as f:
            f.write(compact)
        print("wrote %s (%s, %d bytes)" % (out_path, p["NAME"], len(compact)), file=sys.stderr)


if __name__ == "__main__":
    main()

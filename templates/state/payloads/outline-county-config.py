# STATE-TEMPLATE SCAFFOLD — the coverage-ring county lists, empty on day one.
# bootstrap_state.py builds the initial metro-outline.json (the whole state)
# directly from TIGERweb; this script takes over when the fork begins
# COUNTY-KEYED growth (a layer that answers in some counties and not others,
# EXPANSION_GUIDE Part 2) — from then on, every served county's 3-digit FIPS
# joins METRO_COUNTY_FIPS, every county with a dispatch entry joins
# DISPATCH_COUNTY_FIPS, and the outline is REGENERATED here, never patched.
# BOTH must stay plain literal assignments at module top: validate_index.py
# reads them via ast.literal_eval without importing.
METRO_COUNTY_FIPS = ()
STATE_FIPS = "{{STATE_FIPS}}"
DISPATCH_COUNTY_FIPS = {}
  // Sidebar order (docs/EXPANSION_GUIDE.md Part 5 "Sidebar placement
  // standard"): representation first, then services, then geography broad ->
  // specific. validate_index.py asserts this list matches the registered id
  // set 1:1 (as it does for LAYER_AREA_RANK) — extend it with every layer added.
  var LAYER_SIDEBAR_RANK = ["us-house", "school-district-unified", "county", "county-subdivision", "municipality"];

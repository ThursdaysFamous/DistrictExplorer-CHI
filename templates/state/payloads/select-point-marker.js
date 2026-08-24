  /* ---------- selection marker: the template keeps the default star marker
   * everywhere. Forks can grow a containment-aware marker here — the CHI
   * reference implementation swaps the star for a landmark seal on open water
   * and the containing county's seal/badge outside the core city, testing its
   * own cached geometry most specific first, with every async hop stale-guarded
   * by `seq` + marker identity and every load failure silently keeping the
   * current marker. Signature matches the kept call site in setSelectedPoint:
   * selectPointMarker(state.selectedPoint, state.sequence, selectedMarker). ---------- */
  function selectPointMarker(point, seq, marker) { /* default marker everywhere */ }

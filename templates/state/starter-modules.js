  /* =========================================================================
   * STARTER MODULES — the state template's day-one layer set (FREE tier,
   * docs/EXPANSION_GUIDE.md §3.3/§4.10): five layers any U.S. state serves
   * from national publishers — Census TIGERweb boundaries plus the
   * public-domain unitedstates/congress-legislators roster — parameterized
   * by state FIPS. Nothing here is state-specific beyond that one token;
   * grow this fork per docs/EXPANSION_GUIDE.md §4.3 (statewide growth) and
   * Part 2 (the per-county build) — see the GROWING THIS FORK crib block at
   * the end of this section.
   * ======================================================================= */

  // The one state fact every TIGERweb where-clause reads. bootstrap_state.py
  // fills the token (two-digit FIPS, zero-padded);
  // scripts/check_template_placeholders.py fails CI while it survives.
  var STATE_FIPS = "{{STATE_FIPS}}";

  /* ---------- state outline (out-of-scope wash) ----------
   * Dissolved from TIGERweb State_County by bootstrap_state.py into ONE
   * polygon. The kept BOOT tail calls drawOutOfScopeMask(loadMetroOutline)
   * at idle, so this loader must exist under exactly this name. ---------- */
  var loadMetroOutline = makeCached(function () {
    return fetchJSONWithRetry("data/app/metro-outline.json", {}, 2);
  });

  /* ---------- Census TIGERweb loaders ----------
   * Cribbed from the CHI reference implementation's Legislative-MapServer
   * loader, generalized to take a full service path + layer index so one
   * helper serves every TIGERweb service the starter layers read. ---------- */
  var TIGERWEB_SERVICES = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/";

  function loadTigerLayer(servicePath, layerIndex, outFields, label) {
    // CHI-compat single-argument form: the ENGINE chamber factory's fallback
    // calls loadTigerLayer(opts.layerIndex) against the Legislative MapServer
    // when a registration passes no loadDistricts — keep that contract alive
    // so a grown chamber layer can lean on it (see the crib block below).
    if (typeof servicePath === "number" && layerIndex === undefined) {
      layerIndex = servicePath;
      servicePath = TIGERWEB_SERVICES + "Legislative/MapServer";
      outFields = "*";
      label = "Legislative layer " + layerIndex;
    }
    var url = servicePath + "/" + layerIndex + "/query" +
      "?where=" + encodeURIComponent("STATE='" + STATE_FIPS + "'") +
      "&outFields=" + (outFields || "*") + "&outSR=4326&f=geojson&geometryPrecision=5";
    return fetchJSONWithRetry(url, { timeoutMs: REMOTE_GEOJSON_TIMEOUT_MS }, 2)
      .then(function (geojson) {
        // Esri REST can answer HTTP 200 with a JSON error envelope (throttling,
        // bad params) carrying no features; without this guard makeCached would
        // pin that useless response for the whole session and the layer would
        // stay dead with no Retry path. Treat it as a failure, exactly as the
        // CHI reference loaders do.
        if (!hasUsableGeometry(geojson)) {
          throw new Error("TIGERweb " + (label || servicePath + "/" + layerIndex) +
            " returned no usable geometry");
        }
        return geojson;
      });
  }

  // Statewide loader with the point-first hook (queryFeatureAt): TIGERweb
  // answers "which feature holds this point" in one small spatial query, so a
  // first click never waits on a multi-MB statewide download — the full set
  // keeps loading behind it for the overlay, the highlight, and later clicks.
  // Same layer, same outFields, same STATE filter either way.
  function tigerStatewideLoader(servicePath, layerIndex, outFields, label) {
    var load = makeCached(function () {
      return loadTigerLayer(servicePath, layerIndex, outFields, label);
    });
    load.atPoint = function (point) {
      return loadArcGISPointGeoJSON(servicePath + "/" + layerIndex, point, outFields,
        "STATE='" + STATE_FIPS + "'");
    };
    return load;
  }

  /* ---------- 1. County — the fork's offline anchor ----------
   * Geometry is pre-built at bootstrap (TIGERweb State_County layer 1,
   * STATE-filtered, written to data/app/state-counties.json) and served
   * same-origin + service-worker cached, so this layer answers even when
   * every third-party host is down. Identity-only card: growing it with a
   * clerk/board roster is this fork's first expansion (EXPANSION_GUIDE
   * Part 2). ---------- */
  var loadStateCounties = makeCached(function () {
    return fetchJSONWithRetry("data/app/state-counties.json", {}, 2);
  });

  registerPolygonLayer({
    id: "county",
    group: "geography",
    label: "County",
    loader: loadStateCounties,
    // solid, slightly heavier stroke — the broadest local boundary on the map
    style: { color: "#444B54", weight: 2, fillColor: "#6B7280", fillOpacity: 0.04 },
    fields: [
      // hoverName derives from these same keys (hover-parity by construction):
      // TIGER NAME is the full "Cook County", BASENAME the bare "Cook" fallback.
      { name: "name", label: "County", keys: ["name", "basename"], primary: true },
      { name: "geoid", label: "FIPS", keys: ["geoid"] }
    ],
    compact: true, compactMetaField: "geoid" // 4b name-only card
  });

  /* ---------- 2. County Subdivision — live TIGERweb ----------
   * Cribbed from the CHI reference township module minus its per-county
   * officials join: the card names the subdivision only (honesty rules — no
   * roster source, no guessed officeholder). TIGER NAME carries the honest
   * civil-division type suffix ("Homer township", "Carbondale city"); in
   * states with no township government the subdivisions are UTs/CCDs and the
   * suffix says so. ---------- */
  var loadCountySubdivisions = tigerStatewideLoader(
    TIGERWEB_SERVICES + "Places_CouSub_ConCity_SubMCD/MapServer", 1,
    "GEOID,NAME,BASENAME,STATE,COUNTY,LSADC", "county subdivisions");

  registerLayer({
    id: "county-subdivision",
    group: "geography",
    label: "County Subdivision",
    overlay: {
      load: loadCountySubdivisions,
      // long-dash brown — reads apart from Municipality's tight magenta dots
      style: { color: "#7A5C3E", weight: 1.5, fillColor: "#A98B6C", fillOpacity: 0.05, dashArray: "7 3" }
    },
    hoverName: function (feature) {
      var name = findPropCI(feature.properties || {}, ["name"]);
      return name != null ? String(name) : null;
    },
    query: function (point, seq) {
      // point-first (queryFeatureAt): one subdivision polygon instead of the
      // statewide download gating the first click
      return queryFeatureAt(loadCountySubdivisions, point).then(function (feature) {
        if (!feature) return null;
        var props = feature.properties || {};
        return {
          seq: seq,
          name: findPropCI(props, ["name"]),
          geoid: findPropCI(props, ["geoid"])
        };
      });
    },
    render: function (result) {
      var wrap = cardEl("div", "card-flush");
      wrap.appendChild(renderBodyIntro({
        title: result.name != null ? String(result.name) : "Unknown subdivision",
        note: result.geoid != null ? "GEOID " + String(result.geoid) : null
      }));
      return wrap;
    }
  });

  /* ---------- 3. Municipality — live TIGERweb ----------
   * Cribbed from the CHI reference municipality module minus its
   * municipal-officials join. Incorporated places only: a point outside every
   * place gets the engine's null-result card, which here honestly means
   * "unincorporated" — never suppressed, never guessed at. ---------- */
  var loadPlaces = tigerStatewideLoader(
    TIGERWEB_SERVICES + "Places_CouSub_ConCity_SubMCD/MapServer", 4,
    "GEOID,NAME,BASENAME,STATE,LSADC", "incorporated places");

  registerLayer({
    id: "municipality",
    group: "geography",
    label: "Municipality",
    overlay: {
      load: loadPlaces,
      // tight magenta dots; an empty card here honestly means "unincorporated"
      style: { color: "#B0316E", weight: 1.5, fillColor: "#D06A9C", fillOpacity: 0.05, dashArray: "2 3" }
    },
    hoverName: function (feature) {
      var name = findPropCI(feature.properties || {}, ["name"]);
      return name != null ? String(name) : null;
    },
    query: function (point, seq) {
      // point-first (queryFeatureAt): one place polygon instead of the
      // statewide incorporated-places download
      return queryFeatureAt(loadPlaces, point).then(function (feature) {
        if (!feature) return null; // unincorporated — the engine renders the honest empty card
        var props = feature.properties || {};
        return {
          seq: seq,
          name: findPropCI(props, ["name"]),
          geoid: findPropCI(props, ["geoid"])
        };
      });
    },
    render: function (result) {
      var wrap = cardEl("div", "card-flush");
      wrap.appendChild(renderBodyIntro({
        title: result.name != null ? String(result.name) : "Unknown municipality",
        note: result.geoid != null ? "FIPS " + String(result.geoid) : null
      }));
      return wrap;
    }
  });

  /* ---------- 4. School District (Unified) ----------
   * Geometry pre-built at bootstrap (TIGERweb School layer 0, STATE-filtered,
   * written to data/app/school-districts-unified.json) and served
   * same-origin — the CHI reference module verbatim with its live loader
   * swapped for the pre-built file. TIGER's school tilings are mutually
   * exclusive: unified (K-12) territory never overlaps the elementary +
   * secondary pairs, so in a state that isn't fully unified a point inside a
   * paired district honestly reads "no result" here until this fork grows the
   * other two tilings (School layers 1 and 2 — EXPANSION_GUIDE §4.3). ---------- */
  var loadSchoolDistrictsUnified = makeCached(function () {
    return fetchJSONWithRetry("data/app/school-districts-unified.json", {}, 2);
  });

  registerPolygonLayer({
    id: "school-district-unified",
    group: "schools",
    label: "School District (Unified)",
    loader: loadSchoolDistrictsUnified,
    style: { color: "#2F6B3A", weight: 1.5, fillColor: "#4C8F59", fillOpacity: 0.05, dashArray: "8 3" },
    fields: [
      { name: "name", label: "District", keys: ["name"], primary: true },
      { name: "geoid", label: "GEOID", keys: ["geoid"] }
    ],
    compact: true, compactMetaField: "geoid" // 4b name-only card
  });

  /* ---------- 5. U.S. House — boundary + roster join ----------
   * The CHI reference congress module: pre-built TIGERweb Legislative layer 0
   * geometry (data/app/congress-districts.json, this state only) joined by
   * district number to a same-origin roster (data/app/congress-roster.json —
   * built by bootstrap_state.py from the public-domain
   * unitedstates/congress-legislators dataset and refreshed weekly by
   * update-congress-roster.yml). The ENGINE chamber factory renders the card:
   * representative + party badge + profile link, then the district and D.C.
   * offices behind one details group. A roster-fetch failure degrades to the
   * district number + directory link — never an invented name. ---------- */
  var loadCongressDistricts = makeCached(function () {
    return fetchJSONWithRetry("data/app/congress-districts.json", {}, 2);
  });
  var loadCongressRoster = makeCached(function () {
    return fetchJSONWithRetry("data/app/congress-roster.json", {}, 2);
  });
  // TIGERweb's numbered-district field renames each Congress (CD119FP,
  // CD118FP, …) — newest first; extractDistrictNumber adds a name-field
  // regex fallback behind these.
  var CONGRESS_DISTRICT_FIELDS = ["cd119fp", "cd118fp", "cdfp", "cd"];

  registerIlgaChamber({
    id: "us-house",
    label: "U.S. House",
    layerIndex: 0, // fallback only — loadDistricts (pre-built) is used when present
    loadDistricts: loadCongressDistricts,
    districtFields: CONGRESS_DISTRICT_FIELDS,
    loadRoster: loadCongressRoster,
    memberLabel: "Representative", capitolLabel: "D.C. Office",
    profileLabel: "Official website", directoryLabel: "U.S. House directory",
    directoryUrl: "https://www.house.gov/representatives",
    style: { color: "#14181C", weight: 2, fillColor: "#41B6E6", fillOpacity: 0.05, dashArray: "8 3" }
  });

  /* =========================================================================
   * GROWING THIS FORK — factory crib sheet
   * Every factory named below is ENGINE (byte-identical across forks) and is
   * already in this file — one commented example each. The procedure (source
   * ladder, roster rules, worksheet + sources.html row per layer) lives in
   * docs/EXPANSION_GUIDE.md §4.3 and Part 2; the CHI reference repo holds a
   * working example of each (plus registerCpsNetwork-style admin-region
   * cards, which are portal-specific).
   * ======================================================================= */

  // registerPolygonLayer — any single-source boundary set (judicial circuits,
  // a county's board districts, park districts). See §4.3 / Part 2:
  // registerPolygonLayer({
  //   id: "judicial-circuit", group: "political", label: "Judicial Circuit",
  //   loader: makeCached(function () { return fetchJSONWithRetry("data/app/judicial-circuits.json", {}, 2); }),
  //   style: { color: "#4A2E8C", weight: 1.5, fillColor: "#4A2E8C", fillOpacity: 0.05 },
  //   fields: [{ name: "name", label: "Circuit", keys: ["name"], primary: true }]
  // });

  // registerIlgaChamber — a legislative chamber joined to a district-keyed
  // roster ({ "12": { name, party?, url?, districtOffice?, capitolOffice? } }).
  // No loadDistricts -> live TIGERweb Legislative fallback by layerIndex
  // (1 = state senate SLDU, 2 = state house SLDL). See §4.3 / Part 2:
  // registerIlgaChamber({
  //   id: "state-senate", label: "State Senate District", layerIndex: 1,
  //   districtFields: ["sldust", "sldu"], directoryUrl: "https://example.gov/senate/members",
  //   loadRoster: makeCached(function () { return fetchJSONWithRetry("data/app/state-senate-members.json", {}, 2); }),
  //   style: { color: "#4A2E8C", weight: 2, fillColor: "#4A2E8C", fillOpacity: 0.05, dashArray: "1 5" }
  // });

  // registerNearestPointLayer — nearest-N amenity points (fire stations,
  // libraries) by straight-line distance over a Point FeatureCollection:
  // registerNearestPointLayer({
  //   id: "fire-station", group: "safety", label: "Fire Station", count: 3, color: "#B02E2E", fill: "#D06A6A",
  //   loader: makeCached(function () { return fetchJSONWithRetry("data/app/fire-stations.json", {}, 2); }),
  //   line: function (props) { return props.name + " — " + props.address; }
  // });

  // registerSchoolZone — per-level school attendance zones from a Socrata
  // portal (set SOCRATA_HOST in the metro-config region first). See Part 2:
  // registerSchoolZone({
  //   id: "es-zone", label: "Elementary Attendance Zone", datasetId: "abcd-1234",
  //   style: { color: "#2F6B3A", weight: 1.5, fillColor: "#4C8F59", fillOpacity: 0.05 },
  //   nameKeys: ["school_nam", "school_name"], idKeys: ["school_id"]
  // });

# STATE-TEMPLATE SCAFFOLD — the freshness gate's source manifest, seeded with
# the five starter layers' sources. Every layer this fork adds gets its rows
# here in the same change (CLAUDE.md's conventions; the reference repo's
# validate_sources.py shows a mature manifest's full shape, including
# year-search patterns and the `blocked` inversion).
SOCRATA_DOMAIN = "data.newstate.example"  # this fork's Socrata portal, if it adopts one
CATALOG_API = "https://api.us.socrata.com/api/catalog/v1"

# Socrata dataset ids the app hardcodes (none in the starter set).
SOCRATA = []

# Same-origin data/app files and the upstream source each was built from.
PROVENANCE = [
    {
        "layer": "us-house",
        "app_file": "congress-districts.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0",
        "note": "Congressional districts pre-built from TIGERweb by bootstrap_state.py; redraws each decennial cycle (WATCH.md).",
    },
    {
        "layer": "us-house",
        "app_file": "congress-roster.json",
        "source_url": "https://unitedstates.github.io/congress-legislators/legislators-current.json",
        "note": "Delegation roster from the public-domain congress-legislators project; refreshed weekly by update-congress-roster.yml.",
    },
    {
        "layer": "county",
        "app_file": "state-counties.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1",
        "note": "County polygons pre-built from TIGERweb by bootstrap_state.py.",
    },
    {
        "layer": "school-district-unified",
        "app_file": "school-districts-unified.json",
        "source_url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0",
        "note": "Unified school districts pre-built from TIGERweb by bootstrap_state.py.",
    },
]

# Live endpoints the app queries at runtime.
ENDPOINTS = [
    {
        "layer": "county-subdivision",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/1/query?where=STATE%3D%27{{STATE_FIPS}}%27&returnCountOnly=true&f=json",
    },
    {
        "layer": "municipality",
        "url": "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query?where=STATE%3D%27{{STATE_FIPS}}%27&returnCountOnly=true&f=json",
    },
]
# data/app

Runtime-fetched data files. Empty until `scripts/bootstrap_state.py` runs —
it builds the starter files (metro-outline, state-counties, congress
districts + roster, unified school districts, coverage-gaps) from TIGERweb
and congress-legislators. Every file here must be listed in
`metro-worksheet.json`'s `data_files` and in exactly one of `sw.js`'s two
cache lists (`validate_index.py` enforces both).

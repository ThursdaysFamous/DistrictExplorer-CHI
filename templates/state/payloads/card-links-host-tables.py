# STATE-TEMPLATE SCAFFOLD — per-host link-gate exceptions, empty on day one.
# EXPECTED_UNREACHABLE inverts the check for hosts MEASURED as refusing
# automated clients (reachable-again becomes the WARN); NO_ROOT_DOCUMENT
# suppresses the redirected-to-root heuristic for hosts whose "/" serves
# nothing by design. Add entries only from a measured block, never a guess —
# the reference repo's validate_card_links.py shows earned entries.
EXPECTED_UNREACHABLE = {}
NO_ROOT_DOCUMENT = set()
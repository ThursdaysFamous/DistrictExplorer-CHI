#!/usr/bin/env python3
"""A verification bundle for the servers that omit their intermediate — the COLES PATTERN.

WHAT THE PATTERN IS. A server that sends only its LEAF certificate and leaves
out the intermediate that signed it produces a chain no plain client can
complete: requests, curl and urllib all stop at "unable to get local issuer
certificate". A browser papers over it by fetching the missing issuer from the
certificate's own Authority Information Access extension, so the site loads
perfectly for a person and reads as DEAD to every automated sweep. That single
misreading has cost this project four counties: Coles (found 2026-08-17, shipped
as the 64th), Vermilion and Gallatin (2026-08-21, Gallatin shipped the same
afternoon as the 76th), and Knox's GIS server (2026-08-22), whose record said
the county "refuses every request" when what refused was its website.

WHY THIS IS SHARED CODE. Every one of those hosts is behind the SAME GoDaddy
intermediate, so the hash below was on its way to being pasted into a second
scraper. A pinned hash that exists in two files is a pin that drifts; this is
the one copy.

WHAT IT NEVER DOES. It does not disable verification and nothing built on it
may. The download is over plain HTTP BY DESIGN — that is the AIA URI the
certificate itself publishes — and is safe because the bytes are pinned by hash
here and because the caller's requests still verify the whole chain against
certifi's roots plus this one extra anchor. If a county fixes its chain this
keeps working (a spare trust anchor is harmless). If a county moves to a
different CA the pin fails LOUDLY, which is the state a human can act on.
"""

import base64
import hashlib
import tempfile
import urllib.request

# The AIA caIssuers URI printed inside these counties' own leaf certificates,
# and the SHA-256 of the certificate it serves. Pinned so the download cannot
# be substituted.
INTERMEDIATE_URL = "http://certificates.godaddy.com/repository/gdig2.crt"
INTERMEDIATE_SHA256 = (
    "973a41276ffd01e027a2aad49e34c37846d3e976ff6a620b6712e33832041aa6")
INTERMEDIATE_SUBJECT_CN = "Go Daddy Secure Certificate Authority - G2"

TIMEOUT = 60


def ca_bundle(label):
    """certifi's roots + the intermediate these servers omit.

    Returns the path to a temp file the caller is responsible for deleting.
    certifi rather than the system store so callers trust exactly what every
    other scraper in this repo trusts (it is requests' own store).

    `label` names the caller in the failure message, because the thing a human
    needs to know first is WHICH county's certificate authority moved.
    """
    import certifi

    der = urllib.request.urlopen(INTERMEDIATE_URL, timeout=TIMEOUT).read()
    got = hashlib.sha256(der).hexdigest()
    if got != INTERMEDIATE_SHA256:
        raise SystemExit(
            "%s: the intermediate at %s hashed %s, expected %s — the certificate\n"
            "authority may have changed. Do NOT loosen this check; re-read the\n"
            "leaf's AIA extension and update the pin deliberately."
            % (label, INTERMEDIATE_URL, got, INTERMEDIATE_SHA256))
    body = base64.encodebytes(der).decode("ascii")
    pem = "-----BEGIN CERTIFICATE-----\n%s-----END CERTIFICATE-----\n" % body
    bundle = tempfile.NamedTemporaryFile(suffix=".pem", mode="w", delete=False)
    with open(certifi.where(), "r") as roots:
        bundle.write(roots.read())
    bundle.write("\n# %s (AIA-supplied; the server omits it)\n"
                 % INTERMEDIATE_SUBJECT_CN)
    bundle.write(pem)
    bundle.close()
    return bundle.name

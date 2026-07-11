"""Auth/API responses must not be cacheable (excellence sprint C3):
session data, evidence records, and account payloads are private.

Also covers the API Content-Security-Policy (excellence sprint E-csp):
the JSON API returns no HTML and loads no subresources, so it locks
everything down with default-src 'none'.
"""
import http.client
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_security_headers_include_no_store_cache_control():
    from app.api import _SECURITY_HEADERS
    assert _SECURITY_HEADERS.get("Cache-Control") == "no-store", (
        "API responses carry private account/evidence data — must be no-store"
    )


def test_security_headers_include_locked_down_csp():
    from app.api import _SECURITY_HEADERS
    csp = _SECURITY_HEADERS.get("Content-Security-Policy")
    assert csp is not None, "API responses must carry a Content-Security-Policy"
    # JSON API loads no subresources — default-src 'none' is the correct baseline.
    assert "default-src 'none'" in csp, csp
    assert "frame-ancestors 'none'" in csp, csp
    assert "base-uri 'none'" in csp, csp


def test_csp_header_is_delivered_on_live_api_response():
    """Assert the CSP header actually reaches the client, not just the dict.

    Spins up the real _Handler on an ephemeral port and hits the
    unauthenticated /api/health endpoint (it swallows all backend errors,
    so it responds even without a DB or sources.json present).
    """
    from app.api import _Handler, _SECURITY_HEADERS

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        resp.read()
        delivered = resp.getheader("Content-Security-Policy")
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert delivered == _SECURITY_HEADERS["Content-Security-Policy"], (
        f"CSP header not delivered on API response: {delivered!r}"
    )

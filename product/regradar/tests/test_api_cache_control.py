"""Auth/API responses must not be cacheable (excellence sprint C3):
session data, evidence records, and account payloads are private."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_security_headers_include_no_store_cache_control():
    from app.api import _SECURITY_HEADERS
    assert _SECURITY_HEADERS.get("Cache-Control") == "no-store", (
        "API responses carry private account/evidence data — must be no-store"
    )

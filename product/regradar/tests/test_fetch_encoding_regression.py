"""
Regression: fetch_text_bounded_status crashed with RuntimeError on any
response without a charset in Content-Type — app/adapters/base.py.

The encoding fallback read ``response.apparent_encoding``, which re-reads
``response.content``; on a streamed response whose body was already consumed
by read_bytes_bounded, requests raises RuntimeError("The content for this
response was already consumed"). Every application/rss+xml / signed-blob
fetch (bis.org BCBS feed, UN consolidated sanctions XML) died on the Tier-1
path with FAILED/0 chars in the 2026-07 candidate sweep.

No live network calls — the guarded GET is mocked with a minimal fake
response object that enforces the real requests semantics.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters import base as adapters_base


class _FakeStreamedResponse:
    """Minimal stand-in reproducing requests' consumed-stream semantics."""

    def __init__(self, body: bytes, content_type: str, encoding: str | None):
        self._body = body
        self.status_code = 200
        self.headers = {"Content-Type": content_type}
        self.encoding = encoding
        self.url = "https://www.bis.org/doclist/bcbspubls.rss"
        self._consumed = False

    def iter_content(self, chunk_size):  # noqa: ARG002
        self._consumed = True
        yield self._body

    @property
    def apparent_encoding(self):
        if self._consumed:
            raise RuntimeError("The content for this response was already consumed")
        return "utf-8"

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


def _fetch_with(body: bytes, content_type: str, encoding: str | None):
    fake = _FakeStreamedResponse(body, content_type, encoding)
    with patch.object(adapters_base, "_guarded_get", return_value=fake):
        return adapters_base.fetch_text_bounded_status(
            "https://www.bis.org/doclist/bcbspubls.rss",
            headers={},
            timeout=5,
        )


def test_no_charset_response_decodes_instead_of_crashing():
    """application/rss+xml carries no charset → response.encoding is None.
    Before the fix this raised RuntimeError; now it must decode."""
    status, text = _fetch_with(
        b'<?xml version="1.0" encoding="utf-8"?><rss><channel><title>ok</title></channel></rss>',
        "application/rss+xml",
        None,
    )
    assert status == 200
    assert text is not None
    assert "<title>ok</title>" in text


def test_charset_response_still_uses_declared_encoding():
    status, text = _fetch_with(b"caf\xc3\xa9", "text/xml; charset=utf-8", "utf-8")
    assert status == 200
    assert text == "café"


def test_detect_encoding_never_raises_on_empty_or_binary():
    assert adapters_base._detect_encoding(b"") is None
    # arbitrary binary — result may be any guess or None, but never an exception
    adapters_base._detect_encoding(bytes(range(256)) * 10)

"""
G1-fetch bug-fix regression tests.

Covers two adapter defects:
  1. CBUAE Rulebook revision-updates extraction crashed with
     `NameError: name 'response' is not defined` on the successful path.
  2. Minfin <sitemapindex> handling concatenated sub-sitemap URLs in file
     order without re-sorting across sub-sitemaps, so the most
     recently-modified section could be pushed past the top-N cut.

Both tests use local fixtures / mocks only. No live network calls.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters import uae_cbuae_rulebook
from app.adapters.minfin import MinfinAdapter


# ---------------------------------------------------------------------------
# Bug 1: CBUAE rulebook update extraction NameError on the success path
# ---------------------------------------------------------------------------

_CBUAE_LISTING_HTML = """
<html>
  <body>
    <table>
      <tr>
        <td>
          <a href="/en/rulebook/central-bank-law-2026">
            Central Bank Law Revision 2026
          </a>
        </td>
        <td>14 June 2026</td>
      </tr>
    </table>
  </body>
</html>
"""


def test_cbuae_extract_success_path_returns_http_status_without_nameerror():
    """
    A 200 response with one update row must return extraction_status='ok'
    and echo the real HTTP status. Before the fix this raised NameError
    (undefined `response`) on the final return.
    """
    with patch.object(
        uae_cbuae_rulebook,
        "fetch_text_bounded_status",
        return_value=(200, _CBUAE_LISTING_HTML),
    ):
        result = uae_cbuae_rulebook.extract_cbuae_rulebook_update_items(
            "https://rulebook.centralbank.ae/en/view-revision-updates"
        )

    assert result["http_status"] == 200
    assert result["extraction_status"] == "ok"
    assert result["item_count"] >= 1
    assert result["items"], "expected at least one extracted update row"


# ---------------------------------------------------------------------------
# Bug 2: Minfin sitemapindex must re-sort URLs by lastmod across sub-sitemaps
# ---------------------------------------------------------------------------

_SITEMAP_INDEX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://minfin.gov.ru/sub1.xml</loc></sitemap>
  <sitemap><loc>https://minfin.gov.ru/sub2.xml</loc></sitemap>
</sitemapindex>
"""

# sub1 holds only OLD pages; sub2 holds the newest page.
_SUB1_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://minfin.gov.ru/old-a</loc><lastmod>2020-01-01</lastmod></url>
  <url><loc>https://minfin.gov.ru/old-b</loc><lastmod>2019-01-01</lastmod></url>
</urlset>
"""

_SUB2_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://minfin.gov.ru/new-2025</loc><lastmod>2025-06-01</lastmod></url>
</urlset>
"""


def test_minfin_sitemapindex_resorts_newest_across_sub_sitemaps():
    """
    With sub1 (old pages) listed before sub2 (newest page), the newest page
    must rank FIRST across the combined result. Before the fix, sub-sitemaps
    were concatenated in file order and the 2025 page ended up last.
    """
    _INDEX_URL = "https://minfin.gov.ru/sitemap.xml"

    def _fake_fetch_bytes(url, **_kwargs):
        return {
            _INDEX_URL: _SITEMAP_INDEX_XML,
            "https://minfin.gov.ru/sub1.xml": _SUB1_XML,
            "https://minfin.gov.ru/sub2.xml": _SUB2_XML,
        }[url]

    adapter = MinfinAdapter()
    with patch(
        "app.adapters.minfin.fetch_bytes_bounded", side_effect=_fake_fetch_bytes
    ):
        urls = adapter._get_recent_urls()

    assert urls[0] == "https://minfin.gov.ru/new-2025", (
        f"newest page must be first, got order: {urls}"
    )
    assert set(urls) == {
        "https://minfin.gov.ru/new-2025",
        "https://minfin.gov.ru/old-a",
        "https://minfin.gov.ru/old-b",
    }


def test_minfin_extract_urls_urlset_still_sorted_desc():
    """The plain <urlset> path must keep its newest-first ordering."""
    root = ET.fromstring(
        b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://minfin.gov.ru/a</loc><lastmod>2021-01-01</lastmod></url>
          <url><loc>https://minfin.gov.ru/b</loc><lastmod>2024-01-01</lastmod></url>
        </urlset>
        """
    )
    urls = MinfinAdapter()._extract_urls(root)
    assert urls == ["https://minfin.gov.ru/b", "https://minfin.gov.ru/a"]

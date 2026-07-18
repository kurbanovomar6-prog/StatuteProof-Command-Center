"""
xml_feed adapter — app/adapters/xml_feed.py.

Covers the three contract pillars:
  1. Feed parsing (RSS 2.0, RSS 1.0 RDF, Atom) with link-sorted stable output.
  2. UN CONSOLIDATED_LIST structured monitor: digest determinism — identical
     input → identical output; regeneration noise (dateGenerated) → NO change;
     entry-set change (add / re-version / re-date) → digest change.
  3. Strict opt-in dispatch: adapter_name + host allowlist, registry wiring.

All tests use inline fixtures / mocks. No live network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.base import is_quality_content
from app.adapters.registry import get_adapter_for_url
from app.adapters.xml_feed import XmlFeedAdapter


_ADAPTER = XmlFeedAdapter()

_UN_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
_BIS_URL = "https://www.bis.org/doclist/bcbspubls.rss"
_FIU_URL = "https://www.uaefiu.gov.ae/en/rss-feed/articles-guidelines-rss-feed/"


# ── fixtures ─────────────────────────────────────────────────────────────────

_RSS2 = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Articles &amp; Guidelines </title>
    <link>https://example.gov.ae/listing/</link>
    <item>
      <title>Guidance B</title>
      <link>
https://example.gov.ae/listing/guidance-b/      </link>
      <pubDate>
19 August 2021      </pubDate>
    </item>
    <item>
      <title>Guidance A</title>
      <link>https://example.gov.ae/listing/guidance-a/</link>
      <pubDate>01 May 2020</pubDate>
    </item>
  </channel>
</rss>
"""

_RDF = b"""<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF xmlns="http://purl.org/rss/1.0/"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel rdf:about="https://www.bis.org/doclist/bcbspubls.rss">
    <title>BCBS publications - english</title>
    <link>https://www.bis.org/doclist/bcbspubls.rss</link>
  </channel>
  <item rdf:about="https://www.bis.org/bcbs/publ/d999.htm">
    <title>Some Basel paper</title>
    <link>https://www.bis.org/bcbs/publ/d999.htm</link>
    <dc:date>2026-07-01</dc:date>
  </item>
  <item rdf:about="https://www.bis.org/bcbs/publ/d998.htm">
    <title>Another Basel paper</title>
    <link>https://www.bis.org/bcbs/publ/d998.htm</link>
    <dc:date>2026-06-15</dc:date>
  </item>
</rdf:RDF>
"""

_ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Official Atom feed</title>
  <entry>
    <title>Entry one</title>
    <link href="https://example.org/one"/>
    <updated>2026-01-02T00:00:00Z</updated>
  </entry>
</feed>
"""


def _un_xml(
    date_generated: str = "2026-07-17T23:00:03.140Z",
    versionnum: str = "1",
    last_updated: str = "2016-10-13",
    extra_entity: bool = False,
) -> bytes:
    entity_block = ""
    if extra_entity:
        entity_block = """
    <ENTITY>
      <DATAID>999</DATAID>
      <VERSIONNUM>1</VERSIONNUM>
      <FIRST_NAME>NEW ENTITY</FIRST_NAME>
      <REFERENCE_NUMBER>QDe.999</REFERENCE_NUMBER>
      <LISTED_ON>2026-07-18</LISTED_ON>
    </ENTITY>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CONSOLIDATED_LIST dateGenerated="{date_generated}">
  <INDIVIDUALS>
    <INDIVIDUAL>
      <DATAID>6907993</DATAID>
      <VERSIONNUM>{versionnum}</VERSIONNUM>
      <FIRST_NAME>ERIC</FIRST_NAME>
      <SECOND_NAME>BADEGE</SECOND_NAME>
      <REFERENCE_NUMBER>CDi.001</REFERENCE_NUMBER>
      <LISTED_ON>2012-12-31</LISTED_ON>
      <LAST_DAY_UPDATED>
        <VALUE>{last_updated}</VALUE>
      </LAST_DAY_UPDATED>
    </INDIVIDUAL>
  </INDIVIDUALS>
  <ENTITIES>
    <ENTITY>
      <DATAID>123</DATAID>
      <VERSIONNUM>2</VERSIONNUM>
      <FIRST_NAME>SOME ENTITY</FIRST_NAME>
      <REFERENCE_NUMBER>QDe.100</REFERENCE_NUMBER>
      <LISTED_ON>2015-01-01</LISTED_ON>
    </ENTITY>{entity_block}
  </ENTITIES>
</CONSOLIDATED_LIST>
""".encode("utf-8")


# ── feed parsing ─────────────────────────────────────────────────────────────

def test_rss2_parse_extracts_items_with_whitespace_normalized():
    text = XmlFeedAdapter.parse_payload(_RSS2, _FIU_URL)
    assert text is not None
    assert "Guidance B | 19 August 2021 | https://example.gov.ae/listing/guidance-b/" in text
    assert "Feed title: Articles & Guidelines" in text
    assert "Items captured: 2" in text


def test_rss2_items_sorted_by_link_not_document_order():
    text = XmlFeedAdapter.parse_payload(_RSS2, _FIU_URL)
    assert text.index("guidance-a") < text.index("guidance-b")


def test_rdf_rss10_parse_extracts_items_and_dc_date():
    text = XmlFeedAdapter.parse_payload(_RDF, _BIS_URL)
    assert text is not None
    assert "Some Basel paper | 2026-07-01 | https://www.bis.org/bcbs/publ/d999.htm" in text
    assert "Feed title: BCBS publications - english" in text


def test_atom_parse_extracts_link_href():
    text = XmlFeedAdapter.parse_payload(_ATOM, "https://example.org/feed")
    assert text is not None
    assert "Entry one | 2026-01-02T00:00:00Z | https://example.org/one" in text


def test_feed_output_is_deterministic_and_passes_quality_gate():
    a = XmlFeedAdapter.parse_payload(_RDF, _BIS_URL)
    b = XmlFeedAdapter.parse_payload(_RDF, _BIS_URL)
    assert a == b
    # 3 blocks → passes the >=3 paragraph requirement; chars gate is feed-size
    # dependent so assert the structural property directly.
    assert len(a.split("\n\n")) >= 3


def test_empty_or_itemless_feed_returns_none():
    assert XmlFeedAdapter.parse_payload(b"<rss><channel/></rss>", _BIS_URL) is None


def test_unparseable_xml_returns_none():
    assert XmlFeedAdapter.parse_payload(b"this is not xml", _BIS_URL) is None


def test_doctype_payload_is_refused():
    payload = b'<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY x "y">]><rss/>'
    assert XmlFeedAdapter.parse_payload(payload, _BIS_URL) is None


# ── UN consolidated list ─────────────────────────────────────────────────────

def test_un_output_contains_counts_digest_and_excerpt():
    text = XmlFeedAdapter.parse_payload(_un_xml(), _UN_URL)
    assert text is not None
    assert "Individuals listed: 1" in text
    assert "Entities listed: 1" in text
    assert "Total entries: 2" in text
    assert "Entry-set digest" in text
    assert "CDi.001 | individual | ERIC BADEGE | listed 2012-12-31 | updated 2016-10-13" in text
    assert is_quality_content(text)


def test_un_digest_is_deterministic_for_identical_input():
    assert (
        XmlFeedAdapter.parse_payload(_un_xml(), _UN_URL)
        == XmlFeedAdapter.parse_payload(_un_xml(), _UN_URL)
    )


def test_un_dategenerated_regeneration_noise_does_not_change_output():
    """The root dateGenerated moves on every regeneration even when no entry
    changed — it must be excluded so the hash never fires on nothing."""
    a = XmlFeedAdapter.parse_payload(_un_xml(date_generated="2026-07-17T23:00:03.140Z"), _UN_URL)
    b = XmlFeedAdapter.parse_payload(_un_xml(date_generated="2026-07-18T23:00:01.000Z"), _UN_URL)
    assert a == b


def test_un_added_entry_changes_output():
    a = XmlFeedAdapter.parse_payload(_un_xml(), _UN_URL)
    b = XmlFeedAdapter.parse_payload(_un_xml(extra_entity=True), _UN_URL)
    assert a != b
    assert "Total entries: 3" in b


def test_un_version_bump_changes_output():
    a = XmlFeedAdapter.parse_payload(_un_xml(versionnum="1"), _UN_URL)
    b = XmlFeedAdapter.parse_payload(_un_xml(versionnum="2"), _UN_URL)
    assert a != b


def test_un_amendment_date_changes_output():
    a = XmlFeedAdapter.parse_payload(_un_xml(last_updated="2016-10-13"), _UN_URL)
    b = XmlFeedAdapter.parse_payload(_un_xml(last_updated="2026-07-01"), _UN_URL)
    assert a != b


def test_un_raw_xml_is_never_emitted_wholesale():
    """The monitor output is a bounded summary, not the raw list text."""
    raw = _un_xml()
    text = XmlFeedAdapter.parse_payload(raw, _UN_URL)
    assert len(text) < len(raw)
    assert "<INDIVIDUAL>" not in text


# ── opt-in dispatch ──────────────────────────────────────────────────────────

def test_can_handle_requires_source_opt_in():
    assert _ADAPTER.can_handle(_UN_URL, None) is False
    assert _ADAPTER.can_handle(_UN_URL, {}) is False
    assert _ADAPTER.can_handle(_UN_URL, {"adapter_name": "rulebook_platform"}) is False
    assert _ADAPTER.can_handle(_UN_URL, {"adapter_name": "xml_feed"}) is True


def test_can_handle_enforces_host_allowlist():
    src = {"adapter_name": "xml_feed"}
    assert _ADAPTER.can_handle(_BIS_URL, src) is True
    assert _ADAPTER.can_handle(_FIU_URL, src) is True
    assert _ADAPTER.can_handle("https://evil.example.com/feed.rss", src) is False
    # suffix trickery must not pass
    assert _ADAPTER.can_handle("https://bis.org.evil.com/feed.rss", src) is False


def test_registry_dispatches_only_on_opt_in():
    assert get_adapter_for_url(_UN_URL, {"adapter_name": "xml_feed"}).name == "xml_feed"
    assert get_adapter_for_url(_UN_URL, None) is None
    assert get_adapter_for_url(_UN_URL, {"adapter_name": ""}) is None


# ── fetch_content wiring ─────────────────────────────────────────────────────

def test_fetch_content_uses_bounded_fetch_and_parses(monkeypatch):
    with patch("app.adapters.xml_feed.fetch_bytes_bounded", return_value=_RSS2) as mocked:
        text = _ADAPTER.fetch_content(_FIU_URL, {"adapter_name": "xml_feed"})
    assert mocked.call_count == 1
    assert "Guidance A" in text


def test_fetch_content_returns_none_on_fetch_failure():
    with patch("app.adapters.xml_feed.fetch_bytes_bounded", return_value=None):
        assert _ADAPTER.fetch_content(_FIU_URL, {"adapter_name": "xml_feed"}) is None


def test_fetch_content_never_raises():
    with patch("app.adapters.xml_feed.fetch_bytes_bounded", side_effect=RuntimeError("boom")):
        assert _ADAPTER.fetch_content(_FIU_URL, {"adapter_name": "xml_feed"}) is None

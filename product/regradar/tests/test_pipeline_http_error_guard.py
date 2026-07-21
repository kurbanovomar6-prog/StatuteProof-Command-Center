"""Regression: a rendered HTTP error page must never become a sealed baseline.

`fetch_page` RAISES on a hard access block (401/403/451), but a 404/500/503
whose body Playwright renders into a large templated page returns normally.
That body is >1500 chars, so `looks_like_error_page` (capped at
`_ERROR_PAGE_MAX_CHARS`) cannot catch it — without a transport-status check the
error template would be hashed and sealed, poisoning the source (the eventual
recovery would then alert as CHANGED).

`run_pipeline` at the generic-scraper tier now passes a `status_out` capture to
`fetch_page` and drops any run whose captured HTTP status is >= 400 as a
QUALITY_DROP / HTTP_ERROR. A 200 with real content still seals normally.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.text_normalization import normalize_for_change_hash, stable_content_hash

# A body comfortably larger than _ERROR_PAGE_MAX_CHARS (1500) so the char-capped
# error-page/bot-wall text guards cannot catch it — only the status can.
_BIG_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(80))
assert len(_BIG_TEXT) > 1500
_HTML = "<html><body>irrelevant — extract is patched</body></html>"

_SOURCE = {
    "name": "HTTP Error Guard Source",
    "url": "https://example.gov.ae/http-error-guard",
    "jurisdiction": "AE",
    "category": "financial_regulator",
    "enabled": True,
}


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    import app.source_runs as sr

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _fetch_stub(http_status: int | None):
    """Mimic fetch_page: populate the caller-owned status_out, return HTML."""

    def _fetch(url, *, status_out=None, allow_proxy=False):
        if status_out is not None and http_status is not None:
            status_out["http_status"] = http_status
        return _HTML

    return _fetch


def _read_trail_records(tmp_path) -> list:
    import app.source_runs as sr

    if not sr._RUN_FILE.exists():
        return []
    return [json.loads(ln) for ln in sr._RUN_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _sealed_record_paths(tmp_path) -> list[Path]:
    return sorted((tmp_path / "evidence").glob("*/*/*/evidence-record.json"))


def _run_live(http_status: int | None, isolated_dirs):
    from app.pipeline import init_pipeline, run_pipeline_for_source

    init_pipeline(0)
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", False), patch(
        "app.pipeline.fetch_page", side_effect=_fetch_stub(http_status)
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ), patch(
        "app.pipeline.save_document", return_value=None
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": _BIG_TEXT, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value=None
    ):
        return run_pipeline_for_source(_SOURCE)


@pytest.mark.parametrize("http_status", [404, 500, 503])
def test_rendered_http_error_page_is_quality_drop_not_baseline(isolated_dirs, http_status):
    result = _run_live(http_status, isolated_dirs)

    # The run is a quality_drop and never seals the error template.
    assert result.get("status") == "quality_drop"
    assert result.get("failure_code") == "HTTP_ERROR"
    assert result.get("http_status") == http_status
    assert result.get("changed") is not True
    assert result.get("canonical_evidence_sealed") is not True
    assert _sealed_record_paths(isolated_dirs) == []

    # A durable, baseline-safe trail record is written (no usable hash).
    records = _read_trail_records(isolated_dirs)
    drops = [
        r
        for r in records
        if r.get("change_status") == "QUALITY_DROP" and r.get("failure_code") == "HTTP_ERROR"
    ]
    assert len(drops) == 1, (
        "an HTTP-error run must leave exactly one durable HTTP_ERROR quality-drop "
        f"trail record (got: {[r.get('change_status') for r in records]})"
    )
    drop = drops[0]
    assert drop.get("normalized_hash") is None and drop.get("content_hash") is None
    assert drop.get("access_status") == "error_page"


def test_http_200_with_real_content_still_seals_normally(isolated_dirs):
    result = _run_live(200, isolated_dirs)

    # A 200 does not trip the >=400 guard — normal processing proceeds and the
    # first-seen baseline auto-seals.
    assert result.get("failure_code") != "HTTP_ERROR"
    assert result.get("status") != "quality_drop"
    assert result.get("canonical_evidence_sealed") is True
    sealed = _sealed_record_paths(isolated_dirs)
    assert len(sealed) == 1, f"exactly one canonical record expected, got {sealed}"
    record = json.loads(sealed[0].read_text(encoding="utf-8"))
    assert record.get("record_status") == "complete"


def test_absent_status_does_not_trip_guard(isolated_dirs):
    # Defensive: if a fetch path leaves status_out unpopulated (e.g. adapter
    # content), the guard must not fire — no int status means no drop.
    result = _run_live(None, isolated_dirs)

    assert result.get("failure_code") != "HTTP_ERROR"
    assert result.get("status") != "quality_drop"
    assert result.get("canonical_evidence_sealed") is True

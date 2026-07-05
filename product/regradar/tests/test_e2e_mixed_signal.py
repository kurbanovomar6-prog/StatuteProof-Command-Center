"""Verification-gate e2e: EN + AR + PDF sources through the full pipeline
in an isolated base dir (never the real trail).

Per source: baseline run (FIRST_SEEN, no alert) → genuine change run
(CHANGED, truthful severity, detected facts in the alert payload) →
identical re-run (UNCHANGED heartbeat, zero new alerts).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

_EN_BASE = "\n\n".join(
    [f"Standing supervisory paragraph {i} describing existing procedures." for i in range(25)]
)
_EN_CHANGE = (
    "Circular No. 3 of 2026: licensed payment firms must file the annual "
    "AML return no later than 30 September 2026. A penalty of AED 100,000 applies."
)

_AR_BASE = "\n\n".join([f"فقرة إشرافية قائمة رقم {i} تصف الإجراءات الحالية للمنشآت المالية." for i in range(25)])
_AR_CHANGE = "صدر تعميم جديد: يجب على المنشآت المرخصة سداد غرامة قدرها ٢٥٠٬٠٠٠ درهم عند مخالفة ترخيص مزاولة النشاط."

_PDF_BASE = "\n\n".join(
    ["Virtual Assets Regulatory Authority Compliance and Risk Management Rulebook 19 May 2025"]
    + [f"Part {i} — governance and control requirements text." for i in range(1, 20)]
)
_PDF_CHANGE = (
    "Amendment: Article (14) is replaced. VASPs holding a category 1 licence "
    "must appoint a compliance officer resident in the UAE. Penalty for "
    "non-compliance: suspension of the licence."
)

_SOURCES = [
    ("en-html", {"name": "E2E EN Source", "url": "https://example.gov.ae/en-e2e",
                 "jurisdiction": "AE", "category": "aml", "enabled": True},
     _EN_BASE, _EN_BASE + "\n\n" + _EN_CHANGE, "HIGH"),
    ("ar-html", {"name": "E2E AR Source", "url": "https://example.gov.ae/ar-e2e",
                 "jurisdiction": "AE", "category": "central_bank", "enabled": True},
     _AR_BASE, _AR_BASE + "\n\n" + _AR_CHANGE, "HIGH"),
    ("pdf", {"name": "E2E PDF Source", "url": "https://example.gov.ae/rulebook.pdf",
             "jurisdiction": "AE", "category": "virtual_assets", "enabled": True},
     _PDF_BASE, _PDF_BASE + "\n\n" + _PDF_CHANGE, "HIGH"),
]


@pytest.fixture
def isolated_trail(tmp_path, monkeypatch):
    import app.source_runs as sr

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots", raising=False)
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _run(source: dict, text: str, sends: list, db: dict):
    from app.pipeline import init_pipeline, run_pipeline_for_source

    init_pipeline(0)
    url = source["url"]

    def _save(url: str, content: str, content_hash: str, **_kw):  # noqa: A002
        db[url] = {"content": content, "content_hash": content_hash}

    with patch("app.pipeline.fetch_page", return_value="<html>e2e</html>"), \
         patch("app.pipeline.extract_best_text", return_value={"text": text, "method": "e2e"}), \
         patch("app.pipeline.get_latest_document", side_effect=lambda u: db.get(u)), \
         patch("app.pipeline.save_document", side_effect=_save), \
         patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), \
         patch("app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        result = run_pipeline_for_source(source)
    # keep the derived index aligned like save_document does on change
    if result.get("changed") and result.get("normalized_hash"):
        db[url] = {"content": text, "content_hash": result["normalized_hash"]}
    return result


@pytest.mark.parametrize("sid,source,base,changed,expected_risk", _SOURCES)
def test_mixed_source_lifecycle(isolated_trail, sid, source, base, changed, expected_risk):
    import app.source_runs as sr

    sends: list = []
    db: dict = {}

    r1 = _run(source, base, sends, db)
    assert r1.get("is_new") is True, f"first run must baseline: {r1.get('status')}"
    assert sends == [], "baseline must never alert"

    r2 = _run(source, changed, sends, db)
    assert r2.get("changed") is True
    assert r2.get("is_new") is not True
    assert r2["risk_level"] == expected_risk, r2.get("risk_reason")
    assert len(sends) == 1, "genuine change must alert exactly once"
    facts = {f["kind"] for f in sends[0].get("detected_facts", [])}
    assert facts, "alert payload must carry detected facts"

    r3 = _run(source, changed, sends, db)
    assert r3.get("changed") is False, "identical re-run must be UNCHANGED"
    assert len(sends) == 1, "re-run must send zero new alerts"

    trail = sr._RUN_FILE.read_text(encoding="utf-8")
    assert trail.count('"change_status"') >= 2, "trail must record the lifecycle"


def test_error_page_never_baselines(isolated_trail):
    sends: list = []
    db: dict = {}
    source = {"name": "E2E Err Source", "url": "https://example.gov.ae/err-e2e",
              "jurisdiction": "AE", "category": "aml", "enabled": True}
    err = ("The web server reported a bad gateway error. Please try again in "
           "a few minutes. Cloudflare Ray ID: abc123 • Performance & security by Cloudflare")

    r1 = _run(source, err, sends, db)
    assert r1.get("status") == "error_page"
    assert sends == []

    r2 = _run(source, _EN_BASE, sends, db)
    assert r2.get("is_new") is True, "recovery after error page is a fresh baseline"
    assert sends == [], "recovery must not alert"

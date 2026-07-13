"""mark_alert_sent must NEVER silently drop an unparseable evidence-trail line.

Regression: the whole-file rewrite parsed each line and ``continue``d on a
JSONDecodeError, then rewrote the trail from the parsed rows only — permanently
erasing a crash-truncated line on the next confirmed alert send. The evidence
trail is the product's legal asset, so corrupt lines must be preserved verbatim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import source_runs as sr


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    sr._CACHE_VALID = False


def test_corrupt_line_survives_mark_alert_sent(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    good = json.dumps({"source_id": "S1", "run_id": "R1", "alert_sent": False})
    corrupt = '{"source_id": "S0", "run_id": "R0", "alert_sent": fal'  # truncated line
    sr._RUN_FILE.write_text(good + "\n" + corrupt + "\n", encoding="utf-8")

    result = sr.mark_alert_sent("S1", "R1", alert_sent=True)
    assert result is True

    lines = [ln for ln in sr._RUN_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    # The corrupt line is preserved verbatim, not erased.
    assert corrupt in lines
    # The good record was updated.
    parsed = [json.loads(ln) for ln in lines if ln != corrupt]
    updated = next(r for r in parsed if r["run_id"] == "R1")
    assert updated["alert_sent"] is True


def test_no_match_leaves_file_untouched(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    good = json.dumps({"source_id": "S1", "run_id": "R1", "alert_sent": False})
    corrupt = '{"broken": '
    original = good + "\n" + corrupt + "\n"
    sr._RUN_FILE.write_text(original, encoding="utf-8")

    # No matching (source_id, run_id) -> returns False and does NOT rewrite.
    result = sr.mark_alert_sent("SX", "RX", alert_sent=True)
    assert result is False
    assert sr._RUN_FILE.read_text(encoding="utf-8") == original

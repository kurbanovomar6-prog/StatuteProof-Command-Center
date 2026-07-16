import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_assessment import create_assessment
from app.source_health_timeline import (
    build_operator_source_health_report,
    build_evidence_review_history,
    build_source_timeline,
    source_health_customer_message,
)


def _write_sources(base: Path) -> None:
    (base / "sources.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "AE-test-source",
                    "name": "Official Test Source",
                    "url": "https://regulator.example/source",
                    "jurisdiction": "AE",
                    "category": "AML/CFT",
                    "enabled": True,
                    "status": "active",
                },
                {
                    "source_id": "AE-remediation-source",
                    "name": "Remediation Source",
                    "url": "https://regulator.example/remediation",
                    "jurisdiction": "AE",
                    "category": "financial_regulator",
                    "enabled": True,
                    "status": "remediation",
                    "notes": "Selector changed; under extraction remediation.",
                },
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_run(base: Path, *, run_id: str, source_id: str = "AE-test-source", change_status: str = "UNCHANGED", normalized_hash: str = "a" * 64) -> dict:
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-16" / "AE" / source_id / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    proof_path.write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    normalized_path.write_text("official regulatory text", encoding="utf-8")
    record = {
        "run_id": run_id,
        "timestamp_utc": f"2026-06-16T09:0{len(run_id)}:00+00:00",
        "market": "AE",
        "jurisdiction": "AE",
        "source_id": source_id,
        "source_name": "Official Test Source" if source_id == "AE-test-source" else "Remediation Source",
        "category": "AML/CFT",
        "official_url": f"https://regulator.example/{source_id}",
        "final_url": f"https://regulator.example/{source_id}",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": change_status,
        "extracted_chars": 2400,
        "normalized_chars": 2400,
        "normalized_hash": normalized_hash,
        "content_hash": normalized_hash,
        "raw_hash": "b" * 64,
        "snapshot_normalized_path": str(normalized_path.relative_to(base)),
        "proof_block_path": str(proof_path.relative_to(base)),
        "diff_json_path": str((snapshot_dir / "diff.json").relative_to(base)) if change_status == "CHANGED" else None,
    }
    if change_status == "CHANGED":
        (snapshot_dir / "diff.json").write_text(json.dumps({"meaningful_change_detected": True}), encoding="utf-8")
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    with runs_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


class SourceHealthTimelineTests(unittest.TestCase):
    def test_source_timeline_returns_real_events_from_source_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base, run_id="run-1", change_status="FIRST_SEEN")
            _write_run(base, run_id="run-2", change_status="CHANGED", normalized_hash="c" * 64)

            timeline = build_source_timeline("AE-test-source", base_dir=base)
            event_types = {event["event_type"] for event in timeline["events"]}

            self.assertTrue(timeline["ok"])
            self.assertEqual(timeline["source_id"], "AE-test-source")
            self.assertIn("MONITOR_RUN", event_types)
            self.assertIn("EVIDENCE_SAVED", event_types)
            self.assertIn("HASH_DRIFT", event_types)
            self.assertNotIn("SAMPLE", json.dumps(timeline))
            self.assertIn("review required", timeline["events"][-1]["customer_safe_message"].lower())

    def test_source_timeline_empty_state_is_honest(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)

            timeline = build_source_timeline("AE-test-source", base_dir=base)

            self.assertTrue(timeline["ok"])
            self.assertEqual(timeline["events"], [])
            self.assertEqual(timeline["source_health_status"], "NO_HISTORY")
            self.assertIn("No monitoring history", timeline["message"])

    def test_remediation_source_emits_remediation_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)

            timeline = build_source_timeline("AE-remediation-source", base_dir=base)

            self.assertEqual(timeline["source_health_status"], "REMEDIATION_REQUIRED")
            self.assertEqual(timeline["events"][0]["event_type"], "REMEDIATION_STARTED")
            self.assertIn("remediation", timeline["events"][0]["customer_safe_message"].lower())
            self.assertIn("Selector changed", timeline["events"][0]["remediation_reason"])

    def test_evidence_review_history_includes_assessment_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            run = _write_run(base, run_id="run-1", change_status="CHANGED")
            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="policy_review",
                internal_note="Review policy owner impact.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                base_dir=base,
            )

            history = build_evidence_review_history(run["run_id"], base_dir=base)
            event_types = [event["event_type"] for event in history["events"]]

            self.assertTrue(history["ok"])
            self.assertEqual(history["evidence_record_id"], run["run_id"])
            self.assertIn("EVIDENCE_SAVED", event_types)
            self.assertIn("ASSESSED", event_types)
            self.assertEqual(history["latest_assessment"]["assessment_id"], assessment["assessment_id"])
            self.assertIn("Review policy", history["events"][-1]["assessment_note_preview"])

    def test_customer_messages_are_safe_and_not_legal_advice(self):
        self.assertIn("latest extraction passed", source_health_customer_message("MONITOR_OK"))
        self.assertIn("Review required", source_health_customer_message("HASH_DRIFT"))
        for status in ["MONITOR_OK", "HASH_DRIFT", "REMEDIATION_REQUIRED", "NO_HISTORY"]:
            message = source_health_customer_message(status)
            self.assertNotIn("guaranteed", message.lower())
            self.assertNotIn("legal advice", message.lower())

    def test_operator_health_report_flags_three_consecutive_failed_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base, run_id="run-1", change_status="UNCHANGED")
            _write_run(base, run_id="run-2", change_status="FAILED")
            _write_run(base, run_id="run-3", change_status="FAILED")
            _write_run(base, run_id="run-4", change_status="FAILED")

            report = build_operator_source_health_report(base_dir=base, failed_threshold=3)

            self.assertTrue(report["ok"])
            self.assertEqual(report["operator_only"], True)
            self.assertEqual(report["external_send"], False)
            self.assertEqual(report["customer_delivery"], False)
            self.assertEqual(report["sources_requiring_operator_review"], 1)
            self.assertEqual(report["alerts"][0]["source_id"], "AE-test-source")
            self.assertEqual(report["alerts"][0]["consecutive_failed_runs"], 3)
            self.assertEqual(report["alerts"][0]["operator_status"], "OPERATOR_REVIEW_REQUIRED")

    def test_operator_health_report_separates_disabled_historical_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            sources = json.loads((base / "sources.json").read_text(encoding="utf-8"))
            sources.append(
                {
                    "source_id": "AE-disabled-source",
                    "name": "Disabled Historical Source",
                    "url": "https://regulator.example/disabled",
                    "jurisdiction": "AE",
                    "enabled": False,
                    "status": "disabled_external_access",
                    "monitoring_mode": "remediation",
                }
            )
            (base / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
            _write_run(base, run_id="run-1", source_id="AE-disabled-source", change_status="FAILED")
            _write_run(base, run_id="run-2", source_id="AE-disabled-source", change_status="FAILED")
            _write_run(base, run_id="run-3", source_id="AE-disabled-source", change_status="FAILED")

            report = build_operator_source_health_report(base_dir=base, failed_threshold=3)

            self.assertEqual(report["sources_requiring_operator_review"], 0)
            self.assertEqual(report["historical_sources_requiring_operator_review"], 1)
            self.assertEqual(report["alerts"], [])
            self.assertEqual(report["historical_alerts"][0]["source_id"], "AE-disabled-source")
            self.assertEqual(report["historical_alerts"][0]["operator_status"], "DISABLED_SOURCE_HISTORY")


if __name__ == "__main__":
    unittest.main()


# ── access-block honesty: a WAF/geo 403 surfaces as ACCESS_BLOCKED, not FAILED ──

from app.source_health_timeline import _source_health_status  # noqa: E402


def test_health_status_reports_waf_block_as_access_blocked():
    """A run the monitor flagged as a hard block (monitor_access_status='blocked',
    which _persist_failure_record writes alongside change_status='FAILED') must
    surface as ACCESS_BLOCKED — its own honest state — not a generic FAILED."""
    blocked_run = {
        "change_status": "FAILED",
        "access_status": "failed",
        "monitor_access_status": "blocked",
        "error": "PermissionError: HTTP 403 — access blocked (WAF/geo) for https://rulebook.centralbank.ae/x",
    }
    assert _source_health_status(blocked_run) == "ACCESS_BLOCKED"


def test_health_status_generic_failure_stays_failed():
    """A genuine extraction/timeout failure (no block signal) must stay FAILED —
    the block path must not swallow ordinary failures."""
    failed_run = {
        "change_status": "FAILED",
        "access_status": "failed",
        "monitor_access_status": "error",
    }
    assert _source_health_status(failed_run) == "FAILED"


def test_health_status_healthy_run_is_monitor_ok():
    ok_run = {"change_status": "UNCHANGED", "access_status": "ok", "extraction_quality": "OK"}
    assert _source_health_status(ok_run) == "MONITOR_OK"


# ── source_change_frequency: factual reviewer aid, legal-safe ───────────────────

from datetime import datetime, timedelta, timezone  # noqa: E402
from app.source_health_timeline import source_change_frequency  # noqa: E402


def _run(days_ago, status="CHANGED"):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"timestamp_utc": ts, "change_status": status}


def test_change_frequency_flags_unusual_recent_activity():
    # 4 changes in the last 30 days on top of a long, quiet history → unusual.
    runs = [_run(2), _run(9), _run(16), _run(25)] + [_run(d, "UNCHANGED") for d in range(40, 400, 10)] + [_run(360)]
    freq = source_change_frequency(runs)
    assert freq["changes_last_30d"] == 4
    assert freq["total_changes_observed"] == 5
    assert freq["avg_changes_per_month"] > 0
    assert freq["unusual_recent_activity"] is True


def test_change_frequency_empty_is_zero_and_not_unusual():
    freq = source_change_frequency([])
    assert freq["changes_last_30d"] == 0
    assert freq["total_changes_observed"] == 0
    assert freq["unusual_recent_activity"] is False


def test_change_frequency_note_is_legal_safe():
    """The reviewer aid must stay descriptive — no forbidden claims, no
    compliance-action / applicability language ('you must', 'required action')."""
    note = source_change_frequency([_run(3), _run(10), _run(20)])["note"].lower()
    for banned in ["you must", "guarantee", "prevent", "required action", "must comply", "applicable to you"]:
        assert banned not in note
    assert "descriptive statistics" in note

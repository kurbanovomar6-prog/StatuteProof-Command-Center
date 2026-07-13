"""END-TO-END proof that the deadline-reminder human-review gate actually fires.

This is the test that WOULD HAVE CAUGHT the bug: the gate looked up the review
by the deadline's evidence_record_id (a run_id), but canonical reviews key on the
derived canonical record_id (evr_<source>_<run>). The unit tests monkeypatched
the review lookup, so they passed while the real production path would NEVER fire
a reminder. This test uses the REAL evidence-record + review path (no mocks).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import deadline_radar as dr  # noqa: E402
from app.evidence_records import (  # noqa: E402
    create_canonical_evidence_record,
    record_canonical_evidence_review,
)

DEADLINE = date(2026, 9, 1)
SOURCE_ID = "AE-dfsa-aml"
RUN_ID = "run-e2e-001"
TS = "2026-08-01T10:00:00Z"


def _build_canonical_record(base: Path) -> dict:
    text = "New effective date: 1 September 2026 for the amended CDD rule."
    run_dir = base / "data" / "source_snapshots" / TS[:10] / "AE" / SOURCE_ID / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "normalized.txt").write_text(text, encoding="utf-8")
    (run_dir / "raw.txt").write_text(f"<main>{text}</main>", encoding="utf-8")
    (run_dir / "metadata.json").write_text("{}", encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    run = {
        "run_id": RUN_ID,
        "timestamp_utc": TS,
        "market": "AE",
        "source_id": SOURCE_ID,
        "source_name": "DFSA AML",
        "category": "regulatory",
        "official_url": "https://dfsa.example/aml",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": hashlib.sha256(text.encode()).hexdigest(),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }
    return create_canonical_evidence_record(run, base_dir=base)


def _seed_deadline(base: Path) -> None:
    dr.record_deadline(
        evidence_record_id=RUN_ID,  # the deadline stores the RUN_ID
        deadline_date=DEADLINE.isoformat(),
        deadline_kind="effective",
        extracted_from_diff_excerpt="effective from 1 September 2026",
        source_id=SOURCE_ID,
        regulator="DFSA",
        source_name="DFSA AML",
        official_url="https://dfsa.example/aml",
        base_dir=base,
    )


def test_reminder_fires_after_real_canonical_approval(tmp_path):
    record = _build_canonical_record(tmp_path)
    _seed_deadline(tmp_path)
    sent: list[str] = []

    # Before approval: the reminder is held (default require_review_approval=True).
    held = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert held["sent"] == []
    assert held["skipped_unreviewed"] == 1
    assert sent == []

    # Approve the parent canonical record through the REAL review path...
    record_canonical_evidence_review(
        record["record_id"], decision="approved", reviewer="MLRO Alice",
        note="Reviewed against source.", base_dir=tmp_path,
    )

    # ...now the SAME deadline reminder must fire — proving the run_id -> canonical
    # record_id resolution actually links the deadline to its approved evidence.
    fired = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert [s["lead_stage"] for s in fired["sent"]] == [7]
    assert len(sent) == 1


def test_reminder_stays_held_when_record_rejected(tmp_path):
    record = _build_canonical_record(tmp_path)
    _seed_deadline(tmp_path)
    record_canonical_evidence_review(
        record["record_id"], decision="rejected", reviewer="MLRO Alice",
        note="Not relevant.", base_dir=tmp_path,
    )
    sent: list[str] = []
    result = dr.send_due_reminders(
        as_of=DEADLINE - timedelta(days=7), base_dir=tmp_path,
        send_fn=lambda c, t: sent.append(t) or True, recipients=["1"],
    )
    assert result["sent"] == []
    assert result["skipped_unreviewed"] == 1
    assert sent == []

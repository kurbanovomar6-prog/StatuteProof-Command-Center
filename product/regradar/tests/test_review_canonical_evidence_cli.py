import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_PATH = REPO_ROOT / "tools" / "review_canonical_evidence.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("review_canonical_evidence", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_record(base: Path) -> dict:
    record_dir = base / "evidence" / "dfsa" / "AE-dfsa-cli" / "run-1"
    record_dir.mkdir(parents=True, exist_ok=True)
    current_text = "Current official DFSA text"
    previous_text = "Previous official DFSA text"
    current_path = record_dir / "current.normalized.txt"
    previous_path = record_dir / "previous.normalized.txt"
    raw_path = record_dir / "raw.html"
    snapshot_path = record_dir / "snapshot.html"
    metadata_path = record_dir / "metadata.json"
    diff_path = record_dir / "diff.txt"
    current_path.write_text(current_text, encoding="utf-8")
    previous_path.write_text(previous_text, encoding="utf-8")
    raw_path.write_text("<main>Current official DFSA text</main>", encoding="utf-8")
    snapshot_path.write_text("<html><main>Current official DFSA text</main></html>", encoding="utf-8")
    metadata_path.write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    diff_path.write_text("- Previous official DFSA text\n+ Current official DFSA text\n", encoding="utf-8")

    import hashlib

    current_hash = hashlib.sha256(current_text.encode("utf-8")).hexdigest()
    previous_hash = hashlib.sha256(previous_text.encode("utf-8")).hexdigest()
    record = {
        "schema_version": "2.0",
        "record_id": "evr_cli_001",
        "record_status": "complete",
        "source": {
            "source_id": "AE-dfsa-cli",
            "regulator": "DFSA",
            "official_url": "https://www.dfsa.ae/example",
            "source_name": "DFSA CLI Test",
        },
        "run": {"run_id": "run-1", "timestamp": "2026-06-21T00:00:00Z", "status": "CHANGED"},
        "content": {
            "previous_hash": f"sha256:{previous_hash}",
            "current_hash": f"sha256:{current_hash}",
            "raw_content_path": "evidence/dfsa/AE-dfsa-cli/run-1/raw.html",
            "normalized_current_path": "evidence/dfsa/AE-dfsa-cli/run-1/current.normalized.txt",
            "normalized_previous_path": "evidence/dfsa/AE-dfsa-cli/run-1/previous.normalized.txt",
        },
        "change": {
            "diff_path": "evidence/dfsa/AE-dfsa-cli/run-1/diff.txt",
            "summary": "Fixture diff.",
            "lines_added": 1,
            "lines_removed": 1,
        },
        "files": {
            "snapshot_path": "evidence/dfsa/AE-dfsa-cli/run-1/snapshot.html",
            "raw_path": "evidence/dfsa/AE-dfsa-cli/run-1/raw.html",
            "normalized_path": "evidence/dfsa/AE-dfsa-cli/run-1/current.normalized.txt",
            "previous_path": "evidence/dfsa/AE-dfsa-cli/run-1/previous.normalized.txt",
            "metadata_path": "evidence/dfsa/AE-dfsa-cli/run-1/metadata.json",
            "diff_path": "evidence/dfsa/AE-dfsa-cli/run-1/diff.txt",
        },
        "integrity": {
            "hash_verified": True,
            "integrity_status": "VERIFIED",
            "verified_at": "2026-06-21T00:01:00Z",
        },
        "review": {
            "human_review_required": True,
            "review_status": "pending",
            "review_reason": "Customer-facing brief requires human review.",
        },
    }
    (record_dir / "evidence-record.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def test_review_canonical_evidence_cli_lists_pending_records(tmp_path, capsys):
    tool = _load_tool()
    _write_record(tmp_path)

    code = tool.main(["list", "--base-dir", str(tmp_path)])

    assert code == 0
    output = capsys.readouterr().out
    assert "evr_cli_001" in output
    assert "pending" in output


def test_review_canonical_evidence_cli_approves_record_append_only(tmp_path, capsys):
    tool = _load_tool()
    _write_record(tmp_path)

    code = tool.main(
        [
            "review",
            "--base-dir",
            str(tmp_path),
            "--record-id",
            "evr_cli_001",
            "--decision",
            "approved",
            "--reviewer",
            "Evidence Trail",
            "--note",
            "Verified paths and hashes.",
        ]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "approved" in output
    review_file = tmp_path / "data" / "evidence_reviews" / "canonical_evidence_reviews.jsonl"
    assert review_file.exists()
    assert "Verified paths and hashes" in review_file.read_text(encoding="utf-8")

import hashlib
import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_PATH = REPO_ROOT / "tools" / "generate_canonical_evidence.py"
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate_canonical_evidence_records.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("generate_canonical_evidence", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_canonical_evidence_records", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_run(base: Path, *, run_id: str, source_id: str, status: str = "FIRST_SEEN") -> dict:
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / source_id / run_id
    normalized_hash = _write(snapshot_dir / "normalized.txt", f"Official text for {source_id} {run_id}")
    _write(snapshot_dir / "raw.txt", f"<main>Official text for {source_id} {run_id}</main>")
    _write(snapshot_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(snapshot_dir / "proof.json", json.dumps({"proof_quality": "GOOD"}, sort_keys=True))
    run = {
        "run_id": run_id,
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "market": "AE",
        "source_id": source_id,
        "source_name": f"Source {source_id}",
        "category": "regulatory",
        "official_url": f"https://regulator.example/{source_id}",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": status,
        "normalized_hash": normalized_hash,
        "snapshot_raw_path": str((snapshot_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((snapshot_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((snapshot_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((snapshot_dir / "proof.json").relative_to(base)),
    }
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    with runs_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(run, sort_keys=True) + "\n")
    return run


def test_generate_canonical_evidence_dry_run_writes_report_without_records(tmp_path):
    tool = _load_tool()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")

    code = tool.main(["--base-dir", str(tmp_path), "--limit", "1"])

    assert code == 0
    assert not (tmp_path / "evidence").exists()
    reports = sorted((tmp_path / "reports").glob("canonical_evidence_generation_*.md"))
    assert len(reports) == 1
    report = reports[0].read_text(encoding="utf-8")
    assert "Mode: dry-run" in report
    assert "would_create" in report
    assert "AE-dfsa-cli" in report


def test_generate_canonical_evidence_write_creates_valid_canonical_record(tmp_path):
    tool = _load_tool()
    run = _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")

    code = tool.main(["--base-dir", str(tmp_path), "--source-id", "AE-dfsa-cli", "--limit", "1", "--write"])

    assert code == 0
    record_path = tmp_path / "evidence" / "dfsa" / "AE-dfsa-cli" / "run-1" / "evidence-record.json"
    assert record_path.exists()
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["record_status"] == "complete"
    assert record["record_id"].endswith(run["run_id"])
    assert record["review"]["review_status"] == "pending"
    report = next((tmp_path / "reports").glob("canonical_evidence_generation_*.md")).read_text(encoding="utf-8")
    assert "Mode: write" in report
    assert "created" in report


def test_generate_canonical_evidence_skips_blocked_statuses(tmp_path):
    tool = _load_tool()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli", status="FAILED")

    code = tool.main(["--base-dir", str(tmp_path), "--limit", "1", "--write"])

    assert code == 0
    assert not (tmp_path / "evidence").exists()
    report = next((tmp_path / "reports").glob("canonical_evidence_generation_*.md")).read_text(encoding="utf-8")
    assert "not_eligible" in report
    assert "FAILED" in report


def test_generate_canonical_evidence_requires_explicit_write_for_artifacts(tmp_path):
    tool = _load_tool()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")

    code = tool.main(["--base-dir", str(tmp_path), "--source-id", "AE-dfsa-cli", "--limit", "1", "--dry-run"])

    assert code == 0
    assert not (tmp_path / "evidence").exists()


def test_generate_canonical_evidence_filters_by_run_id(tmp_path):
    tool = _load_tool()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")
    _write_run(tmp_path, run_id="run-2", source_id="AE-dfsa-cli")

    code = tool.main(["--base-dir", str(tmp_path), "--run-id", "run-1", "--limit", "10", "--write"])

    assert code == 0
    assert (tmp_path / "evidence" / "dfsa" / "AE-dfsa-cli" / "run-1" / "evidence-record.json").exists()
    assert not (tmp_path / "evidence" / "dfsa" / "AE-dfsa-cli" / "run-2" / "evidence-record.json").exists()
    report = next((tmp_path / "reports").glob("canonical_evidence_generation_*.md")).read_text(encoding="utf-8")
    assert "run-1" in report
    assert "run-2" not in report


def test_canonical_evidence_validator_accepts_generated_records(tmp_path, capsys):
    tool = _load_tool()
    validator = _load_validator()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")
    assert tool.main(["--base-dir", str(tmp_path), "--run-id", "run-1", "--write"]) == 0

    assert validator.main(["--base-dir", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Canonical evidence records validation PASSED" in output
    assert "records=1" in output


def test_canonical_evidence_validator_rejects_hash_mismatch(tmp_path, capsys):
    tool = _load_tool()
    validator = _load_validator()
    _write_run(tmp_path, run_id="run-1", source_id="AE-dfsa-cli")
    assert tool.main(["--base-dir", str(tmp_path), "--run-id", "run-1", "--write"]) == 0
    record_path = tmp_path / "evidence" / "dfsa" / "AE-dfsa-cli" / "run-1" / "evidence-record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["content"]["current_hash"] = "sha256:" + "0" * 64
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    assert validator.main(["--base-dir", str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "Canonical evidence records validation FAILED" in output
    assert "current_hash" in output

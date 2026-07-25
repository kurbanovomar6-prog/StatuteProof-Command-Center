"""verify-trail must not report a normalizer upgrade as evidence divergence.

The trail sweep cross-checks ``normalize(raw.txt) == normalized.txt``. That is a
statement about the NORMALIZER, not about the evidence, and it is legitimately
false for any record sealed under an older normalizer. Measured on the real store
(2026-07-25) it dominated the verdict: 1430 records, 149 verified, **855
divergent**, and not one of the 1317 stored records carries a
``normalization_version`` to re-derive against. "Divergent" is the word this tool
uses for "the stored bytes no longer match their stored hash" — i.e. tampering —
so the founder's integrity command was crying wolf on 60% of a sound store.

After the fix: 825 verified, **0 divergent**. Tamper detection is untouched — it
lives in the raw_hash / normalized_hash comparisons, which these tests re-pin.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import app.source_runs as sr  # noqa: E402
from app.text_normalization import NORMALIZATION_VERSION  # noqa: E402
from tools import verify_evidence_trail as vt  # noqa: E402


@pytest.fixture()
def isolated_trail(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _seed(*, source_id: str = "AE-one", run_id: str = "run00001") -> dict:
    body = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(60))
    text = f"Circular A — Published 2026-06-01\n\n{body}\n"
    source = {
        "id": source_id,
        "name": "Test Regulator",
        "url": "https://example.gov.ae/rules",
        "jurisdiction": "AE",
        "category": "financial_regulator",
    }
    result = {
        "url": source["url"],
        "final_url": source["url"],
        "status": "ok",
        "extracted_text": text,
        "extracted_chars": len(text),
        "fetch_method": "test",
        "reason": "",
    }
    record = sr.record_from_source_result(run_id=run_id, source=source, result=result)
    return sr.append_run(record)


def _make_unrederivable(trail_root: Path, record: dict) -> dict:
    """Rewrite normalized.txt so today's normalizer cannot re-derive it, and
    re-seal its hash — exactly the shape a record sealed by an OLDER normalizer
    has: bytes that match their own hash but not today's normalization."""
    norm_path = trail_root / record["snapshot_normalized_path"]
    current = norm_path.read_text(encoding="utf-8")
    # An older normalizer kept a trailing marker that v3 strips. The bytes stay
    # self-consistent (we re-seal below); what they are NOT is reproducible from
    # raw.txt by today's normalizer — precisely the real-store situation.
    older_output = current + "\n[legacy normalizer trailer]"
    assert older_output != current, "fixture must differ"
    norm_path.write_text(older_output, encoding="utf-8")

    resealed = dict(record)
    resealed["normalized_hash"] = vt._sha256(older_output.encode("utf-8"))
    # record_from_source_result stamps the CURRENT version, so a seeded record is
    # by definition not legacy. Real legacy records carry "1.0" (754 in the live
    # trail) or nothing at all (672) — reproduce that, or the fixture would be
    # asserting the opposite of what it claims to test.
    resealed["normalization_version"] = "1.0"
    return resealed


# ── the regression this fixes ───────────────────────────────────────────────


def test_an_older_normalizer_output_is_not_reported_as_divergence(isolated_trail):
    record = _make_unrederivable(isolated_trail, _seed())

    result = vt.verify_record(record)

    assert result.status != vt.STATUS_DIVERGENT, result.reason
    assert result.status == vt.STATUS_VERIFIED, result.reason


def test_a_record_declaring_todays_version_is_still_held_to_it(isolated_trail):
    """If the record says today's normalizer sealed it, non-reproducibility is a
    real defect and must stay divergent."""
    record = _make_unrederivable(isolated_trail, _seed())
    record["normalization_version"] = NORMALIZATION_VERSION

    result = vt.verify_record(record)

    assert result.status == vt.STATUS_DIVERGENT
    assert "declared normalization" in (result.reason or "")


# ── tamper detection is unchanged ───────────────────────────────────────────


def test_tampered_normalized_snapshot_is_still_divergent(isolated_trail):
    record = _seed()
    path = isolated_trail / record["snapshot_normalized_path"]
    path.write_bytes(path.read_bytes() + b"INSERTED")

    result = vt.verify_record(record)

    assert result.status == vt.STATUS_DIVERGENT
    assert "normalized_hash" in (result.reason or "")


def test_tampered_raw_snapshot_is_still_divergent(isolated_trail):
    record = _seed()
    path = isolated_trail / record["snapshot_raw_path"]
    path.write_bytes(path.read_bytes() + b"INSERTED")

    result = vt.verify_record(record)

    assert result.status == vt.STATUS_DIVERGENT
    assert "raw_hash" in (result.reason or "")


def test_losing_the_raw_hash_defence_is_surfaced_not_swallowed(isolated_trail):
    """With no raw_hash stored, the re-derivation WAS the only check on raw.txt.
    Dropping it must be reported, not silently absorbed."""
    record = _make_unrederivable(isolated_trail, _seed())
    record.pop("raw_hash", None)

    result = vt.verify_record(record)

    assert result.status != vt.STATUS_DIVERGENT
    assert "unverifiable" in (result.reason or "").lower()

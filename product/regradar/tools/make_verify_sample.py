"""Re-emit a stored CHANGED evidence run as a public Verify-page sample.

Provenance (honest, load-bearing): the emitted assets are a byte-for-byte copy
of a GENUINELY CAPTURED run from the local evidence store — raw.txt,
current.normalized.txt, and diff.txt are copied unmodified, and every value in
the emitted record.json is either copied from the stored evidence-record.json /
stored files or computed from those exact bytes by the product's own sealing
functions. Nothing is invented. The only transformation is schema uplift: the
stored legacy record predates the diff_hash/record_hash self-seal, so this tool
adds the sealed fields exactly as the current writer
(:func:`app.evidence_records.create_canonical_evidence_record`) would emit them:

  content.raw_hash    = sha256(raw.txt)
  content.captured_at = run.timestamp        (sealed copy of the display field)
  content.source_url  = source.official_url  (sealed copy of the display field)
  content.diff_hash   = sha256(diff.txt)
  record_hash         = sha256:canonical_record_hash(content)
  record_hash_method  = RECORD_HASH_METHOD

Before writing anything, the tool runs :func:`app.public_verify.verify_submission`
over the exact bytes it is about to ship and REFUSES to write unless the record
verifies with EVERY check passing — the sample can never drift from the real
verification path.

READ-ONLY over the evidence store: it never writes into evidence/.

Usage:
    python3 tools/make_verify_sample.py <evidence-run-dir> <output-dir>
    e.g.
    python3 tools/make_verify_sample.py \
        evidence/difc/AE-difc-laws-and-regulations/AE-20260530T120622Z-21527790 \
        web/public/sample-record-changed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path bootstrap — make app/ importable when run directly from the repo
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent
_PRODUCT_DIR = _TOOLS_DIR.parent  # .../product/regradar
if str(_PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(_PRODUCT_DIR))

import hashlib  # noqa: E402

from app.public_verify import verify_submission  # noqa: E402
from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash  # noqa: E402


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2

    evidence_dir = Path(argv[1])
    output_dir = Path(argv[2])

    record_path = evidence_dir / "evidence-record.json"
    raw_path = evidence_dir / "raw.txt"
    normalized_path = evidence_dir / "current.normalized.txt"
    diff_path = evidence_dir / "diff.txt"
    for path in (record_path, raw_path, normalized_path, diff_path):
        if not path.is_file():
            print(f"REFUSED: required input missing: {path}")
            return 1

    record = json.loads(record_path.read_text(encoding="utf-8"))
    raw_bytes = raw_path.read_bytes()
    normalized_bytes = normalized_path.read_bytes()
    diff_bytes = diff_path.read_bytes()

    run = record.get("run") or {}
    source = record.get("source") or {}
    if run.get("status") != "CHANGED":
        print(f"REFUSED: run.status is {run.get('status')!r}, expected 'CHANGED'.")
        return 1

    # Schema uplift — exactly the fields the current writer seals, all copied
    # from or computed over the stored capture artifacts (nothing invented).
    content = dict(record["content"])
    content["raw_hash"] = f"sha256:{_sha256_bytes(raw_bytes)}"
    content["captured_at"] = run["timestamp"]
    content["source_url"] = source["official_url"]
    content["diff_hash"] = f"sha256:{_sha256_bytes(diff_bytes)}"
    record["content"] = content
    record["record_hash"] = f"sha256:{canonical_record_hash(content)}"
    record["record_hash_method"] = RECORD_HASH_METHOD

    # Self-verify the EXACT bytes about to ship through the product's own
    # public verification path; refuse to write on anything but all-pass.
    envelope = verify_submission(
        record,
        raw=raw_bytes.decode("utf-8"),
        normalized=normalized_bytes.decode("utf-8"),
        diff=diff_bytes.decode("utf-8"),
    )
    checks = envelope.get("checks", [])
    all_pass = bool(checks) and all(c.get("status") == "pass" for c in checks)
    print(f"verified={envelope.get('verified')}")
    for check in checks:
        print(f"  {check.get('status'):<8} {check.get('name')}: {check.get('detail')}")
    if not (envelope.get("verified") is True and all_pass):
        print("REFUSED: the re-sealed record did not pass every check; nothing written.")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    # Same serialization as the canonical writer (evidence_records.py).
    (output_dir / "record.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "raw.txt").write_bytes(raw_bytes)
    (output_dir / "normalized.txt").write_bytes(normalized_bytes)
    (output_dir / "diff.txt").write_bytes(diff_bytes)
    print(f"Wrote record.json, raw.txt, normalized.txt, diff.txt to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

---
name: evidence-readiness-review
description: Use for checking whether StatuteProof source runs produce complete evidence artifacts, hashes, proof paths, diffs, statuses, and append-only records.
---

# Evidence Readiness Review

## Purpose
Verify whether a source run is audit-ready enough to support a human-reviewed compliance brief.

## When to use
Use for evidence dry-run review, source readiness pass, proof artifact checks, JSONL history checks, or audit-binder readiness.

## When not to use
Do not use to fetch live sources unless the user has approved the exact safe command. Do not approve customer delivery.

## Required inputs
- Source id or source registry path.
- Run record path, usually product/regradar/data/source_runs/source_runs.jsonl.
- Snapshot directory.
- Expected run status.

## Step-by-step procedure
1. Locate the latest run record for source_id.
2. Check source_id, source_name, official_url, final_url, timestamp_utc, run_id, market, category.
3. Check access_status, fetch_method, extraction_quality, extracted_chars, raw_chars, normalized_chars.
4. Check raw_hash, normalized_hash, content_hash, pdf_text_hash if relevant.
5. Check snapshot_raw_path, snapshot_normalized_path, snapshot_metadata_path, proof_block_path.
6. For CHANGED records, check diff_json_path and diff_md_path.
7. Confirm FAILED never becomes UNCHANGED.
8. Check append-only behavior and concurrent-write risk.
9. Record limitations and manual review requirements.

## Output format
- PASS / HOLD.
- Missing fields.
- Evidence artifacts found.
- Status classification result.
- Risk to customer-facing use.
- Exact next fix or dry-run command.

## Safety rules
- Never fabricate evidence.
- Never write monitoring history during a review unless explicitly asked.
- Do not expose raw client data or secrets.

## StatuteProof-specific constraints
No brief may be drafted unless evidence_record_status is complete or the limitation is explicit and human-reviewed.

## Example invocation
"Use evidence-readiness-review on the latest VARA run and tell me if proof is complete."

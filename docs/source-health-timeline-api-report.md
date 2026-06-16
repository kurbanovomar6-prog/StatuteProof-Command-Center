# Source Health Timeline API Report

Date: 2026-06-16

## Implemented

Added backend timeline aggregation in `product/regradar/app/source_health_timeline.py`.

The helper reads only recorded artifacts:

- source runs from `data/source_runs/source_runs.jsonl`;
- source registry metadata from `sources.json`;
- Acknowledge & Assess records from `data/evidence_assessments/assessments.jsonl`.

## API Endpoints

Added protected API routes:

- `GET /api/sources/timeline?source_id=...`
- `GET /api/evidence/review-history?evidence_record_id=...`

Extended `GET /api/sources/status` with:

- `last_evidence_at`;
- `normalized_hash`;
- `proof_block_path`;
- `timeline_event_count`;
- `remediation_reason`.

## Event Coverage

Timeline can now emit:

- `MONITOR_RUN`;
- `EVIDENCE_SAVED`;
- `BASELINE_COMPLETE` when certification metadata exists;
- `HASH_STABLE`;
- `HASH_DRIFT`;
- `SOURCE_HEALTH_OK`;
- `QUALITY_DROP`;
- `REMEDIATION_STARTED`;
- `ASSESSED`.

## Honest Fallback

When no recorded data exists, the endpoint returns an empty event list with:

- `source_health_status: NO_HISTORY`;
- `message: No monitoring history has been recorded yet.`

No fake timeline events or demo history are generated.

## Limits

This is not a full trend analytics system. It does not backfill old records, create export-created events, or infer regulatory impact.

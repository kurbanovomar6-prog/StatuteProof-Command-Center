# Source Health Timeline Current State

Date: 2026-06-16

## Where Source Run History Exists

Source run history exists in `product/regradar/data/source_runs/source_runs.jsonl`. It is append-only JSONL and contains saved monitor/evidence run fields such as `run_id`, `source_id`, `timestamp_utc`, `change_status`, `access_status`, `extraction_quality`, hashes, snapshot paths, proof paths, and diff paths.

## Where Evidence Records Exist

Evidence records are the saved source run rows exposed by `GET /api/evidence`. Proof-backed records carry `proof_block_path`, `normalized_hash`, snapshot paths, and optionally diff paths.

## Where Assessment / Review Records Exist

Acknowledge & Assess records exist in `product/regradar/data/evidence_assessments/assessments.jsonl`, created through `app.evidence_assessment.create_assessment`. They are linked to saved evidence by `evidence_record_id`, which maps to a source run `run_id`.

## APIs Already Exposed

Existing protected APIs:

- `GET /api/sources/status`
- `GET /api/evidence`
- `GET /api/evidence/review`
- `POST /api/evidence/assess`
- `GET|POST /api/evidence/export`

Missing APIs:

- per-source source-health timeline;
- evidence review-history event list.

## Frontend Already Shows

Sources page shows live API status, last checked, source-health label, extraction quality, and remediation/not-started state.

Evidence page shows live evidence records, proof paths, hashes, source-health status, Acknowledge & Assess form, and audit-pack export.

## What Is Missing

- A chronological history per source.
- Review history attached to evidence records.
- Customer-safe explanations for hash drift, remediation, and no-history states.
- Event counts and timeline affordance in the Sources page.
- Evidence created / assessment saved / export action history in the Evidence page.

## Exact Implementation Path

1. Add a backend `source_health_timeline` helper that aggregates source runs, registry metadata, and assessment records.
2. Add `GET /api/sources/timeline?source_id=...`.
3. Add `GET /api/evidence/review-history?evidence_record_id=...`.
4. Add frontend API helpers.
5. Add a Sources page timeline drawer/panel using live API data only.
6. Add an Evidence page Review History section per evidence record.
7. Add tests and a validator that block fake timeline/mock history.

# Source Health Timeline + Review History Final Report

Date: 2026-06-16

## 1. Timeline Backend / API Status

Implemented.

Added `product/regradar/app/source_health_timeline.py` and protected API routes:

- `GET /api/sources/timeline?source_id=...`
- `GET /api/evidence/review-history?evidence_record_id=...`

Extended `GET /api/sources/status` with timeline/evidence visibility fields:

- `last_evidence_at`
- `normalized_hash`
- `proof_block_path`
- `timeline_event_count`
- `remediation_reason`

## 2. Sources Page Timeline Status

Implemented.

Sources page now shows last evidence timestamp, short normalized hash, remediation reason, timeline event count, and a `View timeline` action. Timeline events are loaded from the API and show source-health, proof, hash, diff, remediation, and assessment context when recorded.

## 3. Evidence Page Review History Status

Implemented.

Evidence cards now load review history from the API and show evidence-saved, hash stable/drift, and assessment events. Saving an Acknowledge & Assess record refreshes review history immediately.

## 4. Acknowledge & Assess Integration Status

Implemented.

Assessment events are linked by `evidence_record_id` and `source_id`. The assessment guard remains intact: no assessment without saved evidence/proof.

## 5. Remediation Visibility Status

Implemented.

Remediation sources can emit a `REMEDIATION_STARTED` timeline event from `sources.json` registry metadata and show remediation reason in the source row and timeline.

## 6. Hash Drift / Source-Health Visibility Status

Implemented.

Hash drift is shown as `HASH_DRIFT` with customer-safe wording: review required before customer alert. It is not framed as a regulatory conclusion.

## 7. Tests Added / Updated

Added `product/regradar/tests/test_source_health_timeline.py`.

Coverage includes:

- source timeline aggregation from source run records;
- honest empty timeline state;
- remediation timeline event;
- evidence review history with assessment link;
- safe source-health messages.

Full suite result: `217 passed, 5 warnings`.

## 8. Validators Added / Updated

Added `tools/validate_source_health_timeline.py`.

Validator checks:

- timeline helper exists;
- timeline/review-history API routes exist;
- Sources page exposes timeline/last evidence/source health;
- Evidence page exposes review history/assessment status;
- no fake timeline markers;
- remediation/hash drift/no-history messaging exists;
- Acknowledge & Assess remains evidence-guarded.

## 9. What Is Now More Trustworthy

MLRO users can now see:

- current source state;
- recorded monitoring events;
- saved proof/hash history;
- hash drift/source-health risk;
- remediation state;
- human review/assessment history.

This directly reduces the false-confidence risk from showing only “current status.”

## 10. What Still Remains

Future work:

- 7/30/90-day source reliability trend;
- global review queue filters by source, reviewer, and impact level;
- persisted audit-export-created events;
- production PDF export;
- production email provider configuration.

## 11. $199 Pilot Impact

Improves $199 founder-led pilot readiness. A prospect can now see real monitoring history and review history, not only current source status.

## 12. $399 / $749 Impact

Improves readiness but still partial. Higher tiers still need production delivery, PDF export, reliability trend views, and workflow filtering.

## 13. Next Exact Product Task

Build the global review queue: filter saved evidence by unassessed / assessed / impact level / source-health risk, and add one-click audit-pack export per reviewed item.

## 14. Next Exact Sales Task

Run one controlled MLRO demo using a real source timeline plus an Acknowledge & Assess record. Ask whether the timeline/review-history view is enough for their compliance file or what evidence field is missing.

## Validation Result

Passed:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_source_health_timeline.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`
- `npm run build`
- `npm run lint` with one pre-existing warning in `DashboardPreview.jsx`
- `node scripts/validate-routes.mjs`

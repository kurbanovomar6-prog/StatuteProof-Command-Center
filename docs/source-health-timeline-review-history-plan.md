# Source Health Timeline + Review History Plan

Date: 2026-06-16

## 1. Current Product State

StatuteProof has crossed the UAE 50-source threshold and currently reports 66 enabled UAE official-source endpoints, 62 readiness-supported sources, and 4 remediation sources. The MVP-T trust sprint added safe email test-mode delivery, Markdown/HTML audit-pack export, and Acknowledge & Assess for saved evidence records only.

The remaining trust gap is historical visibility: a paying MLRO can see current status, but not enough of the monitoring history, evidence history, remediation periods, hash drift, or human review history in one place.

## 2. Current Data Sources

Expected runtime data sources:

- `product/regradar/data/source_runs/source_runs.jsonl` for monitor/evidence run records.
- Proof artifacts referenced by source run records, usually via `proof_block_path`.
- Diff artifacts referenced by source run records, usually via `diff_json_path` and `diff_md_path`.
- Assessment records created by the MVP-T sprint under `product/regradar/data/evidence_assessments/assessments.jsonl`.
- Source registry metadata from `product/regradar/sources.json`.
- Existing status and readiness data exposed through source status APIs.

## 3. What Timeline Should Show

The source-health timeline should show only recorded events:

- monitor runs;
- evidence saved;
- baseline/certified evidence signals when present in run metadata;
- hash stable or hash drift signals;
- source-health OK or source-health issue events;
- remediation-required/remediation-status events from registry metadata;
- Acknowledge & Assess events linked to evidence/source runs;
- audit export events only if export records exist in the future.

If no data exists, the API and UI must show an honest empty state: no mock history and no implication that monitoring occurred before records existed.

## 4. What Review History Should Show

Evidence review history should show:

- evidence record created;
- proof/hash fields available;
- diff fields if available;
- Acknowledge & Assess status;
- impact level, reviewer, timestamp, and note preview when an assessment exists;
- export availability/action without pretending an export was previously created.

## 5. Frontend Pages To Update

- Sources page: add per-source timeline affordance, current last checked/evidence/hash fields, remediation reason, and timeline event count.
- Evidence page: add Review History section for each evidence record and surface assessment state beside proof/hash data.

## 6. Backend/API Changes Needed

Implement project-consistent API support:

- source timeline helper module aggregating source runs, registry remediation state, hash/source-health events, and linked assessments;
- evidence review history helper using source run + assessment records;
- API endpoints for per-source timeline and per-evidence review history;
- honest empty-state payloads when no records exist.

## 7. Tests And Validators Needed

Add tests for:

- timeline aggregation from real source run records;
- empty timeline behavior;
- remediation event visibility;
- hash drift/source-health event visibility;
- evidence review history including Acknowledge & Assess records;
- no fake/mock timeline events.

Add `tools/validate_source_health_timeline.py` to check:

- backend timeline helpers/routes exist;
- Sources and Evidence pages reference timeline/review history/source health;
- remediation/hash drift messaging exists;
- unsafe customer-facing claims are absent.

## 8. Future Work

This sprint will not implement:

- full visual source-health time-series charts;
- production PDF export;
- real email sending;
- synthetic backfill of old history;
- legal advice, compliance certification, or guaranteed coverage language.

## 9. Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_source_health_timeline.py`
- existing UAE/source/parser/workspace/skills validators
- frontend build/lint/routes if frontend files changed
- `git diff --check`

## 10. Commit Policy

Stage only files touched by this task. Do not stage runtime junk, secrets, unrelated evidence artifacts, or local outbox data. Commit only after tests and validators pass with:

`feat: add source health timeline and review history`

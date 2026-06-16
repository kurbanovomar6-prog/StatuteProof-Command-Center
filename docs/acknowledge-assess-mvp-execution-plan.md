# Acknowledge & Assess MVP Execution Plan

Date: 2026-06-16

## Verdict

Spec only in this hardening pass. Do not fake the workflow in UI.

The feature is commercially important, but a real implementation needs backend persistence, API tests, frontend state, and audit export behavior. Adding a decorative button now would be worse than leaving a precise implementation plan.

## MVP User Story

When a regulatory update is reviewed, the MLRO can:

1. open an evidence-backed alert;
2. view source URL, diff, proof path, normalized hash, and source-health status;
3. click "Acknowledge & Assess";
4. write an internal impact note;
5. choose impact level: no impact, monitor, policy review, escalate, external counsel review;
6. save a locked assessment record;
7. export or view the audit record later.

## Data Model

Suggested local JSONL model:

`product/regradar/data/assessments/assessment_records.jsonl`

Required fields:

- `assessment_id`
- `source_id`
- `source_name`
- `evidence_run_id`
- `proof_path`
- `diff_path`
- `normalized_hash`
- `source_health_status`
- `reviewer_user_id`
- `reviewer_name`
- `impact_level`
- `impact_note`
- `next_action`
- `status`
- `created_at_utc`
- `updated_at_utc`
- `legal_disclaimer`
- `sample_or_demo`

## API Plan

Backend endpoints:

- `POST /api/evidence/{run_id}/acknowledge`
- `POST /api/evidence/{run_id}/assess`
- `GET /api/assessments/{assessment_id}`
- `GET /api/evidence/{run_id}/assessment`
- `GET /api/assessments/{assessment_id}/export.md`

Rules:

- no assessment from no-save preview;
- proof path required;
- normalized hash required;
- source-health status required;
- closed records are append-only, with amendment records for later changes.

## Frontend Plan

Add to `EvidencePage` or alert detail panel:

- "Acknowledge & Assess" button enabled only when `proof_path` exists;
- source proof card;
- impact-level segmented control;
- internal note textarea;
- save button;
- export Markdown link after save.

Disabled state:

"Assessment requires saved evidence and proof path."

## Tests

Add tests for:

1. no-save preview cannot create assessment;
2. missing proof path blocks assessment;
3. assessment writes append-only JSONL row;
4. export includes source URL, proof path, normalized hash, impact note, and disclaimer;
5. frontend disables action for preview-only evidence;
6. forbidden legal copy is not present.

## Legal-Safe Copy

Allowed:

- "Acknowledge & Assess"
- "Document internal review"
- "Human review required"
- "Monitoring intelligence only. Not legal advice."
- "External counsel review"

Forbidden:

- "Legal determination"
- "Compliance certified"
- "Regulator-approved"
- "Guaranteed compliant"

## Next Implementation Task

Implement backend assessment persistence and tests first. Then add the frontend panel. Do not ship customer-visible assessment buttons until both backend and frontend tests pass.

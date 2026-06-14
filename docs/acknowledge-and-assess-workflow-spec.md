# Acknowledge & Assess Workflow Spec

## 1. Why This Matters

StatuteProof should not only detect source changes. A compliance buyer needs an auditable workflow showing that a human reviewed the update, assessed the impact, and preserved the evidence trail.

The target MLRO reaction should be:

“I can prove what changed, when we saw it, who reviewed it, and what we decided to do next.”

## 2. MVP Workflow

1. Update detected.
2. Evidence created with source URL, raw/normalized content, hash, proof path, and diff.
3. Risk score assigned by existing risk pipeline.
4. Human review required.
5. MLRO clicks “Acknowledge & Assess.”
6. MLRO writes an impact note.
7. StatuteProof locks the review record.
8. Exportable Markdown/PDF audit record is generated.
9. “Monitoring intelligence only. Not legal advice.” disclaimer is included.

## 3. Locked Audit Record Fields

Minimum fields:

- `review_id`
- `evidence_record_id`
- `source_id`
- `source_name`
- `official_url`
- `normalized_hash`
- `diff_path`
- `proof_path`
- `risk_score`
- `risk_label`
- `reviewer_user_id`
- `reviewer_name`
- `reviewed_at`
- `impact_note`
- `assessment_status`
- `next_action`
- `human_review_required`
- `legal_disclaimer`
- `created_at`
- `updated_at`

## 4. Assessment Statuses

| Status | Meaning |
|---|---|
| `acknowledged` | Reviewer has seen the update. |
| `needs_policy_review` | Internal policy/procedure review required. |
| `needs_legal_review` | Qualified legal/compliance review required. |
| `no_action_required` | Reviewer documented why no internal action is needed. |
| `action_owner_assigned` | Reviewer assigned operational follow-up. |
| `closed` | Review completed with locked notes. |

## 5. API Proposal

MVP endpoints:

- `POST /api/evidence/{evidence_id}/acknowledge`
- `POST /api/evidence/{evidence_id}/assess`
- `GET /api/reviews/{review_id}`
- `GET /api/evidence/{evidence_id}/review`
- `GET /api/reviews/{review_id}/export.md`

Future endpoints:

- `GET /api/reviews/{review_id}/export.pdf`
- `POST /api/reviews/{review_id}/assign`
- `POST /api/reviews/{review_id}/close`
- `GET /api/audit-log`

## 6. UI Proposal

Evidence page:

- Add “Acknowledge & Assess” button only when evidence/proof exists.
- Show disabled state when evidence is preview-only/no-save.
- Show evidence hash, official URL, diff summary, and proof path before the note field.

Brief page:

- Show assessment status next to each evidence-backed item.
- Require human review before any customer delivery/export.

Dashboard:

- Show “Updates awaiting assessment.”
- Show source health alerts separately from regulatory update alerts.

## 7. Legal-Safe Copy

Allowed:

- “Acknowledge & Assess”
- “Document internal review”
- “Human review required”
- “Monitoring intelligence only. Not legal advice.”
- “Attach your internal impact note”

Forbidden:

- “Legal determination”
- “Compliance certified”
- “Regulator-approved”
- “Guaranteed compliant”

## 8. Audit Trail Requirements

- Append-only review record after closure.
- Evidence hash and proof path locked into the review.
- Reviewer identity and timestamp captured.
- Edits after closure require a new amendment record.
- Export must label sample/demo records clearly.
- No review record can be created from no-save preview alone.

## 9. What Not To Build Yet

Do not build in this strategy task:

- full workflow engine;
- customer notifications;
- legal advice generation;
- automatic policy decisions;
- real-time collaboration;
- PDF styling beyond a simple export;
- external GRC integrations.

## 10. Next MVP Task

Implement Acknowledge & Assess for saved evidence records only:

1. data model;
2. API endpoints;
3. UI button with disabled preview-only state;
4. Markdown export;
5. tests proving no-save previews cannot create locked review records.

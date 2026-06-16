# Evidence Page Review History UI Report

Date: 2026-06-16

## Implemented

Updated `product/regradar/web/src/components/app/EvidencePage.jsx` with a Review History section for each saved evidence record.

Each evidence card now loads:

- `GET /api/evidence/review-history?evidence_record_id=...`

Review History shows:

- evidence-saved event;
- hash stable/hash drift event when recorded;
- Acknowledge & Assess event when present;
- impact level;
- assessment note preview;
- timestamp;
- customer-safe event message.

## Acknowledge & Assess Integration

When an assessment is saved, the Evidence card refreshes review history so the assessment appears immediately in the event list.

The workflow remains scoped to saved evidence records only. Records without proof still cannot be assessed.

## Honest Empty State

If no review history is available, the UI says:

`No review history has been recorded yet. Use Acknowledge & Assess after confirming this saved evidence record.`

## What Remains

Review history is per-card and event-based. It does not yet provide global filtering by reviewer, impact level, or review status.

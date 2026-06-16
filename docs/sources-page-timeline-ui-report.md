# Sources Page Timeline UI Report

Date: 2026-06-16

## Implemented

Updated `product/regradar/web/src/components/app/SourcesPage.jsx` to show source-history signals in the authenticated source map.

Each live source row now shows:

- current readiness status;
- extraction quality;
- last checked timestamp;
- last evidence timestamp;
- short normalized hash;
- source-health label;
- remediation reason when the source is under remediation;
- timeline event count;
- `View timeline` action.

## Timeline Panel

The timeline panel loads `GET /api/sources/timeline?source_id=...` and shows recorded events only.

Visible event details include:

- event type;
- timestamp;
- customer-safe message;
- source-health status;
- short hash;
- proof path;
- diff path;
- remediation reason;
- assessment note preview.

## Honest Empty State

If a source has no recorded timeline events, the UI says:

`No monitoring history has been recorded yet.`

It also states that no sample timeline events are shown in the authenticated view.

## What Remains

No chart or 7/30/90-day trend view yet. This is a traceable event timeline, not a source reliability dashboard.

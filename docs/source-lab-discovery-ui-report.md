# Source Lab Discovery UI Report

## UI Change

Updated `product/regradar/web/src/components/app/SourceLabPage.jsx`.

Added:

- “Discover endpoints” button;
- “Discovery mode” panel;
- sitemap/feed/document/same-domain candidate counts;
- top recommended activation path candidates;
- adapter family and confidence display;
- noise risk and source-health risk display.

## Backend Endpoint

Added:

- `POST /api/custom-sources/discover`

This endpoint:

- requires auth;
- rate-limits like Source Lab;
- runs no-save discovery only;
- returns `evidence_written: false`;
- returns `evidence_level: PREVIEW_ONLY`;
- returns `can_activate_monitoring: false`.

## Safety

The UI does not activate sources and does not claim evidence. It only helps the operator pick the next no-save Source Lab attempt.

## Remaining UI Work

Future iteration:

- click a discovered endpoint to prefill the Source Lab form;
- one-click “Try recommended adapter” from discovery results;
- source work queue write with review gates.


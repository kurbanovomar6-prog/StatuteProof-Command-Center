# Mock Data Removal Report

Date: 2026-06-16

## Scope

This sprint targeted authenticated customer trust surfaces where mock data could be mistaken for live monitoring data.

## Changed

- `DashboardHome.jsx`
  - Removed `MOCK_ALERTS` dependency.
  - Removed sample signal table from the authenticated dashboard.
  - Replaced sample alert/brief preview with honest review-queue and delivery-readiness empty states.
  - Updated stale `13 / 9 / 4` copy to current `66 / 62 / 4` truth.

- `SourcesPage.jsx`
  - Removed `MOCK_SOURCES` dependency.
  - Switched source map to live `GET /api/sources/status`.
  - Added honest loading, API error, no-match, last-checked, health, and remediation states.

- `EvidencePage.jsx`
  - Removed built-in sample evidence records from the authenticated evidence workspace.
  - Removed silent fallback to sample data when the evidence API is unavailable.
  - Added live-only empty/error states.

## Still Sample-Labeled

The following authenticated pages still use sample/demo data intentionally and label it as such:

- `AlertsPage.jsx`
- `ReportsPage.jsx`
- `AIBriefPage.jsx`

These remain preview/demo surfaces, not live customer alert delivery surfaces.

## Validation

- `tools/validate_mvp_trust_workflow.py` blocks `MOCK_ALERTS` in Dashboard, `MOCK_SOURCES` in Sources, and silent Evidence fallback.
- Frontend build passed.
- Frontend lint passed with one pre-existing TanStack/React Compiler warning in `DashboardPreview.jsx`.

## Verdict

Partial but meaningful. The highest-risk authenticated customer surfaces no longer present unlabeled or silently substituted mock evidence/source data.


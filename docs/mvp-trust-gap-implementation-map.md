# MVP-T Trust Gap Implementation Map

Date: 2026-06-16

## 1. Where Mock/Sample Data Appears

Authenticated app surfaces using sample/mock data today:

- `DashboardHome.jsx`
  - Imports `MOCK_ALERTS` and `COVERAGE_MARKETS`.
  - Shows sample brief/review cards from `appMockData.js`.
  - Uses the real `/api/sources/status` endpoint for source status widgets, but still uses static readiness constants and sample alerts.

- `SourcesPage.jsx`
  - Imports `MOCK_SOURCES`.
  - Renders source rows from frontend sample data plus local custom sources.
  - Does not primarily use `/api/sources/status`, even though a real endpoint exists.

- `EvidencePage.jsx`
  - Has clearly labeled `SAMPLE_EVIDENCE_RECORDS`.
  - Attempts `/api/evidence`, but silently falls back to sample data on failure.
  - This is safer than unlabeled mock data, but still risky for authenticated customer workspaces.

- `AlertsPage.jsx`, `ReportsPage.jsx`, `AIBriefPage.jsx`
  - Use `MOCK_ALERTS` / `MOCK_REPORTS`.
  - Most copy labels these as sample/demo previews, but these should remain clearly demo-only until backed by approved alert/evidence APIs.

## 2. Where Real Evidence/Source Data Exists

Backend endpoints already present:

- `GET /api/sources/status`
  - Requires auth.
  - Merges enabled sources with latest source run records.
  - Returns `source_id`, `name`, `category`, `url`, `status`, `change_status`, `last_run_at`, `access_status`, and `extraction_quality`.

- `GET /api/sources/readiness`
  - Existing readiness endpoint.

- `GET /api/evidence`
  - Requires auth.
  - Reads `data/source_runs/source_runs.jsonl`.
  - Returns evidence-like source run records, but currently omits proof paths and official URLs that Acknowledge & Assess needs.

- Source run/evidence storage:
  - `app/source_runs.py`
  - `app/proof.py`
  - `data/source_runs/source_runs.jsonl`
  - `data/source_snapshots/...`

## 3. Email Delivery Current State

Current delivery implementation is mostly Telegram-focused:

- `app/user_delivery.py`
  - Sends sample brief to connected Telegram.
  - Persists delivery log rows in SQLite.

- `app/alert_routing.py`
  - Builds reviewed alert previews from approved alert drafts.
  - Sends preview alerts to Telegram only.

- `app/weekly_brief.py`
  - Generates reviewed weekly brief Markdown/HTML from human-approved alert drafts.
  - Does not send email.

Trust gap:

- There is no safe email test-mode outbox that renders a reviewed brief into an email payload without sending externally.

Implementation direction:

- Add a local outbox/email test-mode module.
- Reuse `weekly_brief` rendering where possible.
- Persist a delivery status record and local payload file.
- Do not use SMTP or external sending in this sprint.

## 4. PDF / Export Current State

Current export-like behavior:

- `weekly_brief.py` writes Markdown and HTML weekly brief files.
- `docs/post-50-mlro-audit-pack-sample.md` exists as a demo artifact.
- No evidence-record-centered audit export exists.
- No PDF export is implemented.

Implementation direction:

- Implement Markdown/HTML audit-pack export first.
- Include proof/hash/disclaimer and assessment data when present.
- Document PDF as a next step rather than faking it.

## 5. Acknowledge & Assess Current State

Current review workflow:

- `alert_review.py` supports human review of alert draft artifacts.
- It records review status, reviewer, note, proof path, and diff path for alert drafts.

Missing:

- No evidence-record-centered assessment model.
- No API endpoint for evidence acknowledgement/assessment.
- No UI action on Evidence page.
- No export of assessment records.

Implementation direction:

- Add a small filesystem-backed assessment module for saved evidence records only.
- Use source run IDs/evidence IDs as the linked record.
- Validate proof/hash existence before creating assessment.
- Add API endpoints and frontend Evidence page panel if feasible.

## 6. Brief Rendering Current State

- `weekly_brief.py` renders reviewed weekly briefs in Markdown/HTML.
- It already includes a strong disclaimer and sample/demo labeling.
- It only includes human-approved local alert drafts.

Implementation direction:

- Keep weekly brief safety rules.
- Add safe email test-mode around existing rendering rather than changing weekly brief semantics.

## 7. Source Health Timeline Current State

Current source visibility:

- `/api/sources/status` returns latest run status and `last_run_at`.
- Dashboard consumes the endpoint for widgets.
- Sources page is still driven by sample source rows.

Missing:

- Source cards do not reliably show real last checked/source-health/remediation state.
- No visible timeline yet; this sprint should at least make latest health/last-checked visible.

Implementation direction:

- Switch Sources page to `/api/sources/status`.
- Render honest empty state if API unavailable or no runs exist.
- Preserve explicit demo/sample labels only for public/demo pages.

## 8. Exact Implementation Order

1. Add tests for:
   - Acknowledge & Assess saved-evidence guard.
   - Audit export disclaimer/proof/hash inclusion.
   - Email test-mode local outbox and delivery status.
   - Frontend mock-data guard for authenticated app pages.

2. Implement backend modules:
   - `evidence_assessment.py`
   - `audit_export.py`
   - `email_delivery.py` or safe local outbox helper.

3. Wire API endpoints:
   - Evidence assessment endpoints.
   - Audit export endpoint.
   - Safe email test-mode endpoint if small enough.

4. Update frontend:
   - Evidence page: no silent fallback, Acknowledge & Assess panel for live evidence.
   - Sources page: use real source status API and show last checked/source health.
   - Dashboard: remove or clearly isolate sample alert widgets from customer truth surfaces.

5. Create reports and run full validation.


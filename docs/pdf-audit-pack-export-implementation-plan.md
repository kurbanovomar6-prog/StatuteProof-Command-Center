# PDF Audit Pack Export Implementation Plan

Date: 2026-06-16

## Current State

StatuteProof has evidence-backed Markdown and HTML audit-pack export for saved source-run evidence records. Acknowledge & Assess records can be linked to those exports. The product truth remains 66 enabled UAE sources / 62 readiness-supported / 4 remediation.

PDF export is not currently implemented or claimed. The current plan/pricing contract marks `pdf_export` as false for UAE Monitor and Consultant plans.

## Existing Markdown / HTML Audit Export Flow

- `product/regradar/app/audit_export.py` renders audit packs through `render_audit_pack_markdown(...)` and `render_audit_pack_html(...)`.
- `write_audit_pack(...)` writes `.md`, `.html`, and `.json` metadata files under `product/regradar/reports/audit_packs/` or the supplied test `base_dir`.
- `product/regradar/app/api.py` exposes `/api/evidence/export` and currently returns `format: md_html` with `pdf_available: false`.
- Frontend Evidence and Reports pages call `evidence.exportAuditPack(...)` and describe the export as Markdown/HTML only.

## Target PDF Behavior

Add a real PDF format generated from the existing HTML renderer. The PDF must be generated from real evidence records only, include proof/hash/source metadata and the legal disclaimer, and fail visibly if rendering fails.

Supported behavior:

- Existing Markdown/HTML export remains available.
- `POST /api/evidence/export` accepts `format: "pdf"` or defaults to Markdown/HTML.
- PDF output writes a real `.pdf` file under the same audit-pack artifact tree.
- API response returns `format: "pdf"`, `pdf_available: true`, `pdf_path`, `metadata_path`, `evidence_record_id`, and a customer-safe message.

## Dependency Strategy

Use Python Playwright print-to-PDF. It is already present in `product/regradar/requirements.txt` and importable in the local environment. Do not add new PDF dependencies.

If the local browser runtime is unavailable, the implementation must raise a clear `RuntimeError` and the API must return an honest failure. It must not return fake success.

## Files Likely To Change

- `product/regradar/app/audit_export.py`
- `product/regradar/app/api.py`
- `product/regradar/app/plan.py`
- `product/regradar/tests/test_mvp_trust_workflow.py`
- `product/regradar/tests/test_pdf_audit_export.py`
- `product/regradar/web/src/api.js`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/app/ReportsPage.jsx`
- `product/regradar/web/src/components/app/ReviewQueuePage.jsx` if useful
- `product/regradar/web/src/components/PricingPage.jsx`
- `product/regradar/web/src/components/app/BillingPage.jsx`
- `product/regradar/web/src/components/app/ChoosePlanPage.jsx`
- `product/regradar/web/src/data/planCapabilities.js`
- `tools/validate_pdf_audit_export.py`
- `tools/validate_plan_pricing_consistency.py`
- `tools/validate_mvp_trust_workflow.py` if needed

## Tests / Validators

Add tests for:

- real `.pdf` file creation;
- PDF metadata response fields;
- proof/hash/source/disclaimer inclusion in generation metadata;
- demo export label;
- Markdown/HTML export preservation;
- API failure behavior for invalid evidence;
- plan/pricing consistency when PDF export is enabled.

Add `tools/validate_pdf_audit_export.py` to block fake PDF claims, forbidden legal overclaims, and frontend/API mismatches.

## Future Work Not Included

- Production email delivery.
- Court/legal certification wording.
- Bulk PDF binders across multiple evidence records.
- Digital signatures or tamper-evident PDF signing.
- Multi-user/RBAC export permissions.

## Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_pdf_audit_export.py`
- existing trust/source/plan validators
- `git diff --check`
- frontend build/lint/routes

## Commit Policy

Stage only files touched by this PDF export task. Do not stage runtime artifacts, generated PDFs, local outbox files, secrets, or unrelated changes. Commit with:

`git commit -m "feat: add PDF audit pack export"`

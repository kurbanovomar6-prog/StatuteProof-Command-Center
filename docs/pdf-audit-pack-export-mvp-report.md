# PDF / Audit Pack Export MVP Report

Date: 2026-06-16

## Implemented

Implemented Markdown/HTML audit-pack export, not PDF.

- Backend module: `product/regradar/app/audit_export.py`
- API endpoints:
  - `GET /api/evidence/export?evidence_record_id=...`
  - `POST /api/evidence/export`
- Frontend access: Evidence page "Export audit pack"

## Export Includes

- source name;
- source ID;
- official URL;
- monitoring/check timestamp;
- change status;
- source-health status;
- extraction quality;
- proof path;
- diff path;
- normalized hash;
- raw hash;
- linked Acknowledge & Assess record when present;
- legal disclaimer.

## PDF Status

PDF was not implemented in this sprint. The MVP produces Markdown and HTML files because that is safer and avoids pretending PDF exists before a reliable print/render pipeline is validated.

## Tests

Added tests proving:

- export includes proof path;
- export includes normalized hash;
- export includes assessment details;
- export includes disclaimer;
- demo export includes `SAMPLE / DEMO - NOT CUSTOMER DATA`;
- real export does not include sample/demo label.

## Verdict

Audit-pack export MVP is complete as Markdown/HTML. PDF remains a next step.


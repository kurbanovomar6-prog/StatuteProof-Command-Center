# Weak-Family Completion Adapter Implementation Report

Date: 2026-06-19

## Implemented / Used

- Reused `pdf_document`, `pdf_listing`, `difc_legal_database`, `adgm_fsra_listing`, `static_html`, `document_listing`, and source-specific queue activation specs.
- Updated `tools/uae50_activate.py` so activation can use `--fetch-method auto` without forcing Playwright for every source. This matters for official PDFs and static document pages where plain fetch is the safer path.
- Added source-quality policy coverage in `product/regradar/tests/test_source_quality_policy.py` for source IDs, no-save boundaries, repeat-baseline gates, and active-source metadata.

## Held Adapter Work

- SCA needs a dedicated, permission-safe document/download adapter. Current official routes are blocked, robots-disallowed, or produce unsupported download flows under the project fetch policy.
- UAE FIU needs a public-fetch-compatible media/document adapter only if the official site permits stable public access under the project user agent. The current direct media PDFs returned 403 to project fetches.
- EOCN/UAEIEC needs a permission-safe strategy before designation-list or sanctions pages can be monitored without high noise or robots conflicts.

## Legal / Product Gate

No customer-facing copy claims complete UAE coverage, complete family coverage, legal advice, guaranteed compliance, perfect parsing, or regulator certification.

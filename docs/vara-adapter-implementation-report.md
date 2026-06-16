# VARA Adapter Implementation Report

Date: 2026-06-16

## Implemented

- Added direct PDF source-intake support for `source_type: pdf`, `adapter_family: pdf_document`, or `.pdf` URLs.
- Direct PDF intake now uses the existing document extractor:
  - `fetch_document(url)`
  - `extract_pdf_text(bytes)`
- Direct PDF DOM investigation is represented as `detected_page_type: pdf_document`.
- Shallow/scanned PDFs are held as `PDF_EXTRACTION_NEEDED` rather than misclassified as nav-shell.
- Added VARA tests for:
  - direct PDF extraction uses extracted text, not raw `%PDF`;
  - shallow PDF blocks activation;
  - Review Queue can include saved VARA PDF evidence;
  - audit-pack export works for saved VARA PDF evidence.

## Files Changed

- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_vara_source_depth.py`
- `tools/validate_vara_source_depth.py`

## Source Groups Helped

- VARA direct official rulebook PDFs.
- Any future official direct PDF source using Source Lab.

## Remaining Blockers

- Some accessible VARA PDFs score 58/59 because PDF text has limited heading/paragraph structure. They remain held until quality scoring or extraction structuring improves safely.
- DIFC selector/access remediation remains a separate weak-zone task.

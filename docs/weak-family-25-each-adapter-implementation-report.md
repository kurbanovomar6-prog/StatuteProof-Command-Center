# Weak-Family 25-Each Adapter Implementation Report

Date: 2026-06-18

## Implemented

### FTA Tax Listing Adapter

Added `fta_tax_listing` for official `tax.gov.ae` listing pages. The adapter:

- Targets the FTA `.commonTableNew` listing structure.
- Extracts item titles, dates, categories, and official document links.
- Keeps FTA ASP.NET page content even when the page wraps content inside a `form`.
- Rejects nav-shell-only output when no meaningful listing rows exist.

### FTA Fetch Safety

Added a narrow `prefer_requests_on_low_content` fallback for `fta_tax_listing`. This is limited to the FTA structured listing adapter because the raw server HTML contains the official listing rows while generic visible-text extraction may see only shell text.

### Quality Terms

Expanded regulatory-density scoring to include tax-specific terms such as VAT, excise, corporate tax, taxable, refund, clarification, decree, cabinet, ministerial, and procedure.

### FIU/EOCN Legal Listing Terms

Expanded `fiu_eocn_document_listing` tokens so legal decisions and AML/CFT law pages are not incorrectly treated as low-value listings.

## Tests Added

- FTA legislation listing extracts document rows.
- FTA nav-shell fixture is rejected.
- FTA source-intake preview can pass without writing evidence.
- FIU/EOCN legal decisions are extracted from law/regulation listings.
- Activation writer preserves required source metadata including normalized text path, baseline fields, `MONITOR_OK`, and legal-safe notes.

## Not Implemented

- SCA Office/download document parsing.
- FTA listing pagination/filter crawling.
- SCA 25-source activation.
- FIU/EOCN 25-source activation.
- DIFC/ADGM/VARA/MoE 25-source activation.

## Verdict

The adapter work was sufficient to prove FTA listing structure and activate 25 direct FTA PDF endpoints. It was not sufficient to honestly bring every weak family to 25.

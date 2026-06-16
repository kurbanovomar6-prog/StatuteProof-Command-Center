# PDF Export Status

Date: 2026-06-16

## Current Status

StatuteProof now exports audit packs as PDF, Markdown, and HTML for saved evidence records.

## Implementation

PDF generation uses Python Playwright print-to-PDF from the existing audit-pack HTML renderer. The implementation writes:

- `.pdf`
- `.md`
- `.html`
- `.json` metadata

The export includes source URL, proof path, raw/normalized hashes, source-health status, linked Acknowledge & Assess details when present, and the legal boundary disclaimer.

## Customer-Safe Wording Now

Allowed:

- "PDF audit pack export is available for saved evidence records."
- "PDF audit packs support internal compliance review files."
- "Monitoring intelligence only. Not legal advice."

Forbidden:

- "Court-admissible evidence package."
- "Legal advice."
- "Guaranteed compliance."
- "Never miss updates."
- "Perfect parsing."

## Remaining Work

- Production email delivery remains test-mode/local-outbox only.
- Digitally signed or tamper-evident PDFs are not implemented.
- Bulk evidence PDF binders are not implemented.

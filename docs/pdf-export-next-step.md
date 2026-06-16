# PDF Export Next Step

Date: 2026-06-16

## Current Status

StatuteProof currently exports audit packs as Markdown and HTML. Real PDF export is not implemented and is not claimed.

## Why PDF Was Not Added In This Sprint

The ideal-product sprint prioritized trust-critical authenticated UI and the Global Review Queue:

- remove authenticated mock data;
- API-drive source truth;
- reconcile plan/pricing;
- add onboarding readiness disclosure;
- build real evidence-backed Review Queue.

Adding PDF generation safely requires validating the local browser/runtime path, deterministic rendering, file storage, and tests that prove the generated file exists and includes source URL, proof/hash metadata, assessment status, and disclaimer.

## Recommended Implementation Path

1. Use Playwright print-to-PDF only if the project runtime already supports it reliably.
2. Generate PDF from the existing audit-pack HTML renderer, not from a separate template.
3. Add `format=pdf` to the existing audit export endpoint.
4. Store generated PDFs under the same audit-export artifact tree as Markdown/HTML.
5. Include:
   - source name;
   - official URL;
   - evidence record ID;
   - proof path;
   - raw/normalized hash;
   - diff path if available;
   - assessment impact/note if present;
   - disclaimer: Monitoring intelligence only. Not legal advice.
6. Add tests that verify:
   - a PDF file is created;
   - the endpoint reports `pdf_available: true`;
   - Markdown/HTML remains available;
   - demo exports are labeled SAMPLE / DEMO;
   - real exports never show fake data.

## Customer-Safe Wording Until Implemented

Allowed:

- "Markdown/HTML audit pack export is available."
- "PDF export is not enabled in this MVP."

Forbidden:

- "PDF export included."
- "Inspection-ready PDF binder."
- "Court-admissible evidence package."

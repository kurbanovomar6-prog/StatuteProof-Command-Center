# DIFC Current State Audit

Date: 2026-06-16

## Current Truth

- Public truth before this remediation cycle: **72 enabled UAE sources / 68 readiness-supported / 4 remediation**.
- DIFC readiness-supported count before this cycle: **0 active DIFC-specific legal sources**.

## Sources In `sources.json`

| Source ID | Status | Enabled | URL | Current blocker |
| --- | --- | --- | --- | --- |
| `AE-difc-laws-and-regulations` | `remediation` | true | `https://www.difc.com/business/laws-and-regulations/` | Meaningful text exists, but source remains under registry hold and generic extraction does not produce activation-ready evidence. |
| `AE-difc-legislation` | `disabled_navigation_only` | false | `https://www.difc.ae/business/laws-regulations/legislation/` | Stale route / historical 0-character navigation-only extraction. |

## Candidates In Work Queue / Candidate Files

| Candidate | URL | Existing queue status | Observed issue |
| --- | --- | --- | --- |
| `AE-difc-laws-regulations` | `https://www.difc.com/business/laws-and-regulations/` | blocked | Generic policy detection reported access-control language. |
| `AE-difc-legal-database` | `https://www.difc.com/business/laws-and-regulations/legal-database/` | candidate | Official index is large and public, but generic document listing misses useful DIFC law/PDF pairings. |
| `AE-difc-consultation-papers` | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | candidate | Thin/static listing; needs specific extraction review before evidence. |
| `AE-difc-data-protection` | `https://www.difc.com/business/laws-and-regulations/data-protection/` | candidate | Current URL returns 404; should be replaced by Commissioner of Data Protection routes if used. |
| `AE-difc-legislation` | `https://www.difc.ae/business/laws-regulations/legislation/` | candidate/disabled | Stale `difc.ae` route; hold unless a current official equivalent is verified. |

## Commercial Usefulness

- DIFC legal database coverage is high-value for DIFC firms, legal counsel, compliance consultants, and DFSA-adjacent compliance buyers.
- Data Protection Law and Digital Assets Law are particularly useful because they map to privacy/compliance and digital-asset buyer concerns.
- DIFC coverage must remain visibly scoped; StatuteProof must not claim complete DIFC or UAE regulatory coverage.

## Exact Blocker Type

1. Generic access-policy false positives on public pages containing terms such as "DIFC Client Portal".
2. Generic document-listing extraction misses DIFC law-title/PDF-link pairings.
3. Some detail pages are short legal metadata pages that require item extraction rather than static page extraction.
4. Stale `difc.ae` paths remain unsuitable.

## Likely Fix Path

- Add a source-specific DIFC legal database adapter that extracts legal entries and adjacent PDF/detail links from public `difc.com` pages.
- Narrow access-policy classification so public pages with substantial extracted content are not blocked merely because they reference a client portal in context.
- Add fixture tests for DIFC legal listing extraction, PDF title/link pairing, nav-shell/access-blocking, evidence Review Queue compatibility, and audit export compatibility.

## Post-Remediation Result

This plan was executed in the same sprint. The final result is **79 enabled / 76 readiness-supported / 3 remediation**, with 8 proof-backed DIFC legal/data-protection sources activated. See `docs/difc-remediation-final-report.md` for final source list, proof paths, and held-source reasons.

# Weak-Zone Elimination No-Save Retest Report

Date: 2026-06-16

## Scope

- Primary candidates tested: **31**.
- Near-threshold retests: **7**.
- CBUAE drift retests: **3**.
- Total no-save candidates tested in this run: **41 candidate/config checks** across VARA, CBUAE, DFSA/DIFC, ADGM alternate, and UAE FIU weak zones.

## Strong No-Save Passes

| Source ID | Regulator | Adapter | Quality | Result |
| --- | --- | --- | ---: | --- |
| `AE-vara-rulebook-updates` | VARA | `vara_pdf_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-vara-compliance-risk-rulebook` | VARA | `static_html` | 62 | Held: mass-monitor dry-run produced `QUALITY_DROP` and hash drift. |
| `AE-cbuae-amlcft-rulebook` | CBUAE | `static_html` | 61 | Held: static extraction drifted; stable doc-list variant activated instead. |
| `AE-cbuae-amlcft-entire-section` | CBUAE | `static_html` | 63 | Held: static extraction drifted; stable doc-list variant activated instead. |
| `AE-cbuae-consumer-protection-rulebook` | CBUAE | `static_html` | 61 | Held: static extraction drifted; stable doc-list variant activated instead. |
| `AE-dfsa-consultation-current` | DFSA | `dfsa_notice_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-dfsa-enforcement-decisions-current` | DFSA | `dfsa_notice_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-dfsa-regulatory-actions-current` | DFSA | `dfsa_notice_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-cbuae-retail-payment-services-rulebook` | CBUAE | `cbuae_document_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-dfsa-consultation-paper-165` | DFSA | `dfsa_notice_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-dfsa-notice-supervisory-review` | DFSA | `dfsa_notice_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-cbuae-amlcft-rulebook-doclist` | CBUAE | `cbuae_document_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-cbuae-amlcft-entire-section-doclist` | CBUAE | `cbuae_document_listing` | 65 | Activated after evidence/baseline/dry-run. |
| `AE-cbuae-consumer-protection-rulebook-doclist` | CBUAE | `cbuae_document_listing` | 65 | Activated after evidence/baseline/dry-run. |

## Held / Blocked Summary

- VARA direct PDF URLs remain held because the current Playwright fetch path returns shallow/no text for direct PDFs.
- VARA compliance/risk static extraction is held due hash drift and quality drop in mass-monitor dry-run.
- CBUAE public `centralbank.ae` website paths remain access-blocked; official `rulebook.centralbank.ae` alternates are usable.
- DFSA/DIFC: DFSA current pages improved; DIFC pages remain access/selector blocked.
- ADGM alternate components remain mostly below quality threshold or nav-shell under tested selectors.
- UAE FIU remaining pages are either shallow route aliases, duplicates, or noisy press-update pages.

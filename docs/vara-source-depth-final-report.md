# VARA Source Depth Final Report

Date: 2026-06-16

## 1. VARA Sources Before / After

- Before: 3 readiness-supported VARA sources.
- After: 9 readiness-supported VARA sources.
- Current public truth after this sprint: **72 enabled UAE sources / 68 readiness-supported / 4 remediation**.

## 2. Candidates Researched

- Page/rulebook official candidates: 13
- Direct official PDF candidates: 10
- Total controlled candidates investigated/tested: 23

## 3. Candidates No-Save Tested

23 total:

- 13 official rulebook/page endpoints.
- 10 direct official current-version PDF endpoints.

## 4. Strong No-Save Passes

6 direct PDF candidates passed strict no-save with `can_save_evidence=true`.

## 5. Evidence Saved

6 sources saved proof/evidence.

## 6. Baseline Complete

6 sources completed 2/2 baseline runs.

## 7. MONITOR_OK Count

6 sources returned `MONITOR_OK` in scoped mass-monitor dry-run.

## 8. Newly Activation-Ready VARA Sources

- `AE-vara-compliance-risk-rulebook-pdf`
- `AE-vara-technology-information-rulebook-pdf`
- `AE-vara-va-issuance-rulebook-pdf`
- `AE-vara-broker-dealer-rulebook-pdf`
- `AE-vara-lending-borrowing-rulebook-pdf`
- `AE-vara-va-regulations-2023-pdf`

## 9. Sources Held And Why

- `AE-vara-company-rulebook-pdf`: accessible but quality 59 / `can_save_evidence=false`.
- `AE-vara-custody-services-rulebook-pdf`: accessible but quality 59 / `can_save_evidence=false`.
- `AE-vara-exchange-services-rulebook-pdf`: accessible but quality 58 / `can_save_evidence=false`.
- `AE-vara-market-conduct-rulebook-pdf`: accessible but quality 58 / `can_save_evidence=false`.
- Stale `www.vara.ae/en/regulatory-framework/...` aliases: held because `rulebooks.vara.ae` is the safer official extraction path.

## 10. Adapter / Parser Improvements

- Direct PDF Source Lab now extracts PDF text using `document_extractor.fetch_document()` and `extract_pdf_text()`.
- Raw `%PDF` bytes are no longer normalized as monitorable text.
- Shallow/scanned direct PDFs are held as PDF extraction remediation rather than being misclassified as nav-shell.

## 11. Tests Added

Added `product/regradar/tests/test_vara_source_depth.py` covering:

- direct PDF extraction from extracted text;
- shallow PDF blocking;
- Review Queue compatibility for saved VARA PDF evidence;
- audit-pack export compatibility for saved VARA PDF evidence.

## 12. Validators Added / Updated

Added:

- `tools/validate_vara_source_depth.py`

Updated:

- `tools/validate_uae_source_pack.py`
- `tools/validate_plan_pricing_consistency.py`

## 13. Commercial Impact

VARA is no longer just a light presence. The pack now has official, direct, proof-backed VARA rulebook PDF monitoring for core VASP compliance domains. This improves the $399 UAE Monitor story for VASP-adjacent buyers, while still not claiming complete VARA coverage.

## 14. Remaining VARA Blockers

- Company, custody, exchange, and market conduct PDFs are accessible but held by strict quality gate.
- No claim of complete VARA coverage is safe.
- Future work should improve PDF structure scoring or add source-specific section extraction without weakening gates.

## 15. Current Public Source Truth After

**72 enabled UAE sources / 68 readiness-supported / 4 remediation**.

## 16. $199 Readiness Impact

Stronger. The founder-led pilot can now show a VARA-specific VASP compliance source path with evidence, baseline, Review Queue, and audit export.

## 17. $399 Readiness Impact

Meaningfully improved, especially for VARA/VASP prospects. Still partial for broad self-serve because DIFC remediation, real production email sending, and reliability trend charts remain unfinished.

## 18. Next Exact Product Task

Remediate DIFC selector/access coverage and activate official DIFC legal/regulatory sources only if proof, baseline, source-health, and gates pass.

## 19. Next Exact Sales Task

Run a $199 pilot demo for a VARA/VASP prospect using one newly activated VARA PDF source, Review Queue, Acknowledge & Assess, PDF audit pack, and email readiness status. Ask whether the monitored VARA rulebook set matches their compliance file needs.

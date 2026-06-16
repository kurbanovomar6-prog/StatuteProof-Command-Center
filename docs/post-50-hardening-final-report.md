# Post-50 Hardening Final Report

Date: 2026-06-16

## 1. Current Truth Before / After

Before: 66 enabled UAE sources / 62 readiness-supported / 4 remediation.

After: 66 enabled UAE sources / 62 readiness-supported / 4 remediation.

No new source was added because all non-CBUAE strong passes were either duplicates of existing active URLs or failed evidence/monitor stability requirements.

## 2. Source Distribution Before / After

Distribution did not change:

| Group | Before | After |
| --- | ---: | ---: |
| CBUAE | 27 | 27 |
| ADGM/FSRA | 10 | 10 |
| DFSA | 8 | 8 |
| FIU/EOCN/AML | 7 | 7 |
| SCA | 4 | 4 |
| VARA | 3 | 3 |
| Federal/Legislation/Tax | 3 | 3 |

## 3. CBUAE Concentration Risk

CBUAE concentration remains **43.5%** of readiness-supported sources.

Verdict: medium-high concentration risk for broad UAE demos, acceptable for CBUAE/AML/payments-heavy prospects.

## 4. Diversification Progress

- 33 non-CBUAE candidate/config checks were run.
- 5 strong no-save passes were found.
- 0 new non-CBUAE sources were activated.
- 2 candidates were evidence/baseline certified but held as duplicate active URLs.
- 1 DFSA held source was reinvestigated and remains held because monitor hash drift persists.

## 5. Weak Zones Improved

- Public copy now reflects 66/62/4 instead of old 13/9 or 19/15 counts.
- Source coverage table now says sample rows are not the full registry.
- DFSA hash drift was narrowed to a save-path versus monitor-path normalized hash mismatch.
- Duplicate active URL risk was caught for ADGM legal framework rules and SCA circulars.

## 6. Weak Zones Remaining

- VARA direct PDF/rulebook extraction.
- DIFC listing/table/access-safe selectors.
- ADGM alternate media/data-protection/listing components.
- DFSA AML/CTF root deterministic monitor path.
- FIU shallow/duplicate route cleanup.

## 7. DFSA Hash Drift Result

Held.

`AE-dfsa-aml-ctf-sanctions` has stable evidence hash `d66b892...`, but mass-monitor dry-run returns `468409...` and `change_detected=true` when compared against the evidence hash. It must not be activated yet.

## 8. Customer-Facing Truth Update Result

Updated frontend copy and docs to use:

- 66 enabled UAE official-source endpoints.
- 62 readiness-supported after proof and baseline gates.
- 4 under extraction remediation.
- Monitoring intelligence only. Not legal advice.

## 9. Acknowledge & Assess Status

Spec only.

Implementation was not added in this pass because a real version needs backend persistence, API tests, frontend state, and export behavior. A fake button would be misleading.

## 10. Audit Pack / Demo Artifact Status

Created:

- `docs/post-50-proof-backed-demo-script.md`
- `docs/post-50-mlro-audit-pack-sample.md`

Both are labeled SAMPLE / DEMO / NOT LEGAL ADVICE.

## 11. Validators Updated

No validator code change was required in this pass. Existing validators already protect:

- 66/62/4 truth;
- no fake 60 validated claim;
- no legal advice or guarantee claim;
- UAE 50 activation-ready proof/baseline gates;
- parser promise boundaries.

## 12. Validation Result

Passed.

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q` -> 206 passed
- source discovery, source activation, mass-source activation, mass-monitoring, batch-onboarding, UAE source pack, UAE 50 working-source, parser quality, workspace, and Codex skills validators
- frontend `npm run build`
- frontend `npm run lint` -> 0 errors, 1 existing TanStack Table warning
- frontend route validation
- `git diff --check`

## 13. Demo-Ready?

Yes, with concentration caveat.

## 14. $199 Pilot-Ready?

Yes, for a narrow pilot with source readiness review and manual activation.

## 15. $399 UAE Monitor-Ready?

Partial. It is credible for CBUAE/AML/payments-heavy prospects, but broader UAE Monitor positioning needs more VARA, DIFC, and ADGM alternate coverage.

## 16. Next Exact Task

Implement direct official PDF extraction for VARA rulebooks and a DIFC listing/table adapter with fixtures. Then retest 20 non-CBUAE candidates and activate only non-duplicate proof-backed sources.

# Commercial Product Reality Summary

Date: 2026-06-16

## What StatuteProof Really Does Today

StatuteProof monitors selected public official or officially linked UAE regulatory sources, extracts and normalizes text, stores hashes/proof artifacts, compares changes deterministically, and exposes source readiness, source-health, evidence, and remediation status. It is strongest as an evidence-backed official-source monitoring and review support system, not as a legal-advice engine.

## What Is Real

- 66 enabled UAE official-source endpoints in `sources.json`.
- 62 readiness-supported active UAE sources.
- 4 enabled UAE sources under extraction remediation.
- Source activation gates exist: no-save preview, evidence save, repeat baseline, mass-monitor dry-run, and review gates.
- Validators block fake 50-source claims and forbidden legal/compliance language.
- Proof-backed demo artifacts exist and are labeled sample/demo/not legal advice.
- Parser/adapters now cover static HTML, custom elements, listings, tables, PDF/document listings, source-specific SCA/DFSA/ADGM/FIU/EOCN/CBUAE patterns, and safe failure statuses.

## What Is Demo / Spec Only

- Acknowledge & Assess is a spec, not implemented workflow.
- Audit-pack export is a demo/sample artifact, not a productized customer export.
- Some dashboard/app data still has mock/sample flows in parts of the frontend.
- Manual pilot activation and admin approval workflow are not fully productized.
- Customer delivery/notification flows should remain off until a reviewed pilot process exists.

## What Is Not Implemented Yet

- Full MLRO review queue with locked audit records.
- Source-health timeline and customer-visible remediation history.
- Rendered screenshot/WARC evidence for JS-heavy pages.
- Production-grade multi-tenant persistence and team roles.
- Automatic legal obligation interpretation. This should remain out of scope.

## What Must Not Be Claimed

- No legal advice.
- No compliance certification.
- No guaranteed completeness.
- No regulator partnership/certification.
- No "never miss updates."
- No "perfect parsing."
- No "any website can be parsed."
- No "all 66 sources are validated"; safe wording is 66 enabled, 62 readiness-supported, 4 remediation.

## Current Source Distribution

Canonical post-50 distribution:

| Group | Readiness-supported count | Share |
| --- | ---: | ---: |
| CBUAE | 27 | 43.5% |
| ADGM/FSRA | 10 | 16.1% |
| DFSA | 8 | 12.9% |
| UAE FIU / EOCN / AML | 7 | 11.3% |
| SCA | 4 | 6.5% |
| VARA | 3 | 4.8% |
| Federal / legislation / tax | 3 | 4.8% |

## Strongest Areas

- CBUAE rulebooks, AML/CFT, payments, open finance, and consumer protection.
- DFSA AML/rulebook/consultation/enforcement coverage.
- ADGM/FSRA rulebooks, financial crime, guidance, consultations, enforcement.
- UAE FIU/EOCN AML/CFT and sanctions-oriented sources.
- SCA AML/CFT, circulars, FATCA/CRS, corporate governance, and regulations.

## Weakest Areas

- VARA direct rulebook/PDF extraction is thin for a VASP-heavy sales motion.
- DIFC laws/regulations remain under remediation or selector/access uncertainty.
- CBUAE is overrepresented, which can make the pack look inflated if sold as balanced UAE-wide coverage.
- Acknowledge & Assess is not implemented, so the product risks looking like a monitor instead of an MLRO workflow.

## Current Commercial Readiness

- Internal demo: ready.
- MLRO prospect demo: ready with explicit concentration caveat.
- $199 founding pilot: ready for controlled, founder-led pilots.
- $399 UAE Monitor: partially ready; strongest for CBUAE/AML/payments-heavy prospects, not yet a fully balanced UAE monitor.

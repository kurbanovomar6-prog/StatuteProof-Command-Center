# Parser And Source Lab 10/10 Review

Date: 2026-06-14

## Executive Verdict

Parser score: 7.9/10.

Source Lab score: 8.5/10.

The parser/source-intake system is real and materially safer than a generic scraper. It blocks unsafe URLs, separates no-save preview from evidence and activation, detects nav-shell/hash-collision/shallow extraction cases, returns quality and remediation data, and has targeted tests. It is not 10/10 because hard-source adapters, DFSA baseline, screenshot/rendered-DOM evidence, OCR-needed PDF detection, and long-run stability history are still missing.

## What Works

- `validate_public_url()` blocks localhost, private IP, file URLs, and credential-bearing URLs.
- `run_source_intake()` returns provider, extraction method, normalized hash, normalized preview, quality score, evidence level, activation readiness, failure reason, and remediation hint.
- `build_source_lab_contract()` prevents one no-save pass from becoming monitoring-ready.
- `source_quality.py` applies penalties for nav-shell, hash collision, selector timeout, shallow content, missing proof, missing canonical URL, policy warnings, and shallow PDF text.
- `source_certification.py` separates `TEST_PASSED`, `BASELINE_PENDING`, and `MONITORING_CERTIFIED`.
- Source Lab UI displays no-save state, quality score, provider, normalized length/hash, evidence level, activation readiness, baseline, warnings, and normalized preview.
- Tests cover URL safety, nav shell, hash collision, provider metadata, no-save/evidence split, and plan/auth contracts.

## P0 Bugs

| ID | Problem | Status |
| --- | --- | --- |
| PARSER-001 | DFSA configured URLs/selectors still produce nav-shell/404 or fail remediation-exit gates. | Open. DFSA remains remediation. |
| PARSER-002 | Source readiness constants are duplicated across docs/frontend/validator. | Open. Current truth is correct but drift risk remains. |

## P1 Improvements

- Add generated source-readiness summary artifact from `sources.json` plus readiness review facts.
- Make Sources page use `/api/sources/status` or `/api/sources/readiness` as primary data.
- Add rendered DOM and screenshot evidence for Playwright fetches.
- Add scanned PDF/OCR-needed detection and remediation hint.
- Add API/browser tests for Source Lab required fields and plan gating.
- Add evidence artifact validator for proof/diff/snapshot paths.

## Missing Tests

- Browser Source Lab flow: required fields, legal checkbox, no-save result, save gate, activation disabled.
- Browser auth/plan flow.
- Validator check that sample brief files include `SAMPLE / FAKE` and proof references.
- Validator check that tracked runtime alert queue JSON is not committed.
- Screenshot/rendered DOM evidence once implemented.

## Safe Fixes This Run

- Add docs/workflows and review reports.
- Fix stale UI comment.
- Add validator checks for proof-backed sample labels and tracked runtime data if scoped.
- Do not change DFSA readiness or source registry without strict evidence.

## Later Improvements

- Dedicated DFSA migration/no-save/baseline task.
- Source-specific adapters for DFSA enforcement, AML/MLRO notices, DIFC, and FIU homepage/reference-source decisions.
- Browser evidence artifacts and WARC/timestamp options.
- Full API-backed source map and customer-facing readiness portal.

## Agents / Skills Applied

- Source Monitor: source IDs, source status, remediation labels.
- Evidence Trail: proof/no-save/baseline distinction.
- Code Architect: parser/API contract review.
- QA/Critic: false-ready and UI mapping review.
- Legal Language: customer-facing labels and claims.
- `source-monitoring-review`, `custom-source-parser`, `evidence-readiness-review`, `systematic-debugging`, and `test-driven-development`.

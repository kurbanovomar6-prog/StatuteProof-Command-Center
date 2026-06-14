# Source Discovery Engine Final Report

Date: 2026-06-15

## 1. Executive Verdict

StatuteProof now has a structured Source Discovery Engine that can inspect official public URLs before parsing, surface endpoint candidates, recommend adapter families, classify failure reasons, and feed Source Lab remediation UI. This moves the system closer to repeatable large-scale source onboarding, but it does not make 50 sources working yet.

## 2. Source Discovery Engine

Implemented: yes

Discovery methods implemented:

1. Robots.txt sitemap extraction.
2. Sitemap index/urlset parsing.
3. RSS/Atom feed link discovery and parsing.
4. Document/PDF link discovery.
5. Same-domain link graph discovery with max-link limits.
6. Metadata/canonical/title extraction.
7. DOM investigation handoff.
8. Table/listing/rulebook/register candidate classification.
9. Playwright network/XHR response classification support.
10. Candidate scoring and inactive work-queue candidate generation.

## 3. Auto DOM Integration

Improved: yes

`discover-source` and `source-discovery-lab` now use structured discovery output and DOM investigation results to identify adapter family, selector hints, no-save eligibility, risk fields, and remediation hints.

## 4. Candidate Generator

Created: yes

Generated candidates are inactive by default and include source monitor, evidence trail, QA, legal language, product manager, code architect, and final activation gate placeholders.

## 5. Quality Gate

Improved: yes

The quality gate now carries explicit discovery failure codes and better handling for public pages that contain login links or recaptcha scripts in chrome. False login/captcha blocking was fixed with tests.

Off-domain documents found directly on an official source page are now modeled as `officially_linked` manual-review candidates, not as active or evidence-ready sources.

## 6. Source Lab UI

Improved: yes

Source Lab now includes Discovery mode with endpoint counts, recommended activation paths, adapter recommendation, confidence, noise risk, source-health risk, and inactive-by-default wording.

## 7. Tests Added

Test cases added: 11

Coverage includes robots/sitemap/feed parsing, document discovery, off-domain officially linked document handling, network response classification, candidate generation, discovery report contract, and policy warning false positives.

## 8. Live Validation

- Live discovery targets tested: 8
- No-save checks run: 4
- Preview-accessible no-save results: 2
- Save-eligible results: 0
- Saved evidence count: 0
- Baseline-complete count: 0
- Activation-ready count: 0

## 9. sources.json Decision

Changed: no

No new source passed proof, repeat baseline, and all agent gates in this sprint.

## 10. Public Truth Before / After

Before: 13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.

After: 13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.

## 11. What Can Be Claimed Now

- StatuteProof has a Source Discovery Engine for official/public source onboarding.
- Source Lab can discover candidate endpoints and recommend an activation path before evidence save.
- Candidate endpoints remain inactive until no-save, proof, repeat baseline, and review gates pass.

## 12. What Cannot Be Claimed

- 50 working sources.
- 60 validated sources.
- Any website can be parsed.
- Perfect parsing.
- 95% of all websites.
- Legal advice.
- Guaranteed compliance.
- Regulator certification or partnership.

## 13. Remaining Blockers

- SCA still needs robust item-level table/listing extraction.
- EOCN/FIU laws/publication listing extraction is shallow and must be improved.
- DFSA officially linked S3 PDFs require provenance review and document evidence handling.
- CBUAE and UAE FIU public pages returned 403 in scoped discovery and need alternative official endpoints.
- VARA tested rulebook/framework URLs returned 404 and need current URL rediscovery.
- New sources require saved proof and repeat baselines before activation.

## 14. Next Exact Task

Build and validate SCA + EOCN/FIU item-level listing adapters, then run no-save and saved-baseline checks only for candidates that pass the improved adapter gate.

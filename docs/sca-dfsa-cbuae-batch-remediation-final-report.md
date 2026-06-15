# SCA / DFSA / CBUAE Batch Remediation Final Report

Date: 2026-06-15

## 1. Executive Verdict

The sprint improved the system and implemented the safe batch activation runner, but it did not activate new sources.

Public truth remains:

13 enabled UAE sources / 9 readiness-supported / 4 remediation.

## 2. Did SCA Improve?

Yes.

Improvements:

- SCA discovery now filters generic official pages such as About/Services.
- SCA doubled path artifacts are normalized.
- SCA regulatory pages such as AML/CFT, circulars/rules, market rules, and register candidates are preserved.
- SCA tests were added.

Still not ready:

- `AE-sca-latest-regulations` no-save failed with quality 45.
- `AE-sca-aml-cft` no-save failed with quality 55.
- No SCA evidence was saved.

## 3. Did DFSA Improve?

Yes, partially.

Improvements:

- Auto DOM Investigator now recognizes DFSA summary blocks and suggests `dfsa_notice_listing` for suitable summary fixtures.
- DFSA summary fixture test added.

Still not ready:

- Live DFSA AML/MLRO no-save failed with `NAV_SHELL_ONLY`.
- Live DFSA rulebook homepage no-save failed with `NAV_SHELL_ONLY`.
- Next work should use precise endpoints, not generic parent/homepage URLs.

## 4. Did CBUAE Improve?

Yes, at access classification level.

Improvements:

- HTTP 403 now maps to access/source-health remediation with safe alternate-discovery guidance.
- CBUAE 403 test added.

Still not ready:

- Live CBUAE no-save failed with `NAV_SHELL_ONLY`.
- No CBUAE evidence was saved.

## 5. Batch Runner Implemented

Yes.

Added:

- `product/regradar/app/mass_source_activation_runner.py`
- `mass-source-activate` CLI in `product/regradar/run.py`
- Runner validation in `tools/validate_mass_source_activation_pipeline.py`

Default behavior:

- `--no-save-only`
- no evidence save;
- no `sources.json` update;
- no customer delivery;
- no monitoring activation.

## 6. Tests Added Count

7 new tests:

- 2 source discovery tests;
- 1 DOM investigator test;
- 4 batch runner tests.

## 7. Live Validation Targets Tested Count

6 targets:

1. SCA latest regulations;
2. SCA AML/CFT;
3. SCA circulars/rules discovery-only;
4. DFSA AML/MLRO;
5. DFSA rulebook;
6. CBUAE regulations.

## 8. No-Save Passed Count

0 strong passes.

## 9. Saved Evidence Count

0.

## 10. Activation-Ready New Sources Count

0.

## 11. `sources.json` Changed?

No.

## 12. Public Truth Before / After

Before:

13 enabled / 9 readiness-supported / 4 remediation.

After:

13 enabled / 9 readiness-supported / 4 remediation.

## 13. What Can Be Claimed Now

Allowed:

“StatuteProof has a safe batch source activation runner that can process queued official-source candidates in discovery/no-save mode, update queue status, and keep failed or incomplete sources out of active monitoring.”

Allowed:

“SCA discovery filtering, DFSA summary detection, and CBUAE access-block classification improved, but no new SCA/DFSA/CBUAE source is active yet.”

## 14. What Cannot Be Claimed

Forbidden:

- “50 working sources”
- “60 validated sources”
- “SCA/DFSA/CBUAE are fully monitored”
- “Any website can be parsed”
- “Perfect parsing”
- “Guaranteed compliance”
- “Legal advice”
- “Official regulator certified”

## 15. Remaining Blockers

- SCA item-level extraction still fails live no-save quality threshold.
- DFSA needs precise URLs and adapters:
  - `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`
  - `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`
- CBUAE needs accessible official alternate endpoints, not WAF bypass.
- Runner does not yet perform repeat-baseline automation.

## 16. Next Exact Task

Add SCA circulars/rules to `mass_source_activation_queue.json` as an inactive candidate, run no-save with `sca_listing` and item-level selectors, then remediate DFSA precise AML/MLRO notices and Thomson Reuters rulebook module URLs.

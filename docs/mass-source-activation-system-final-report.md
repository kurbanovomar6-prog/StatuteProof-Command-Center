# Mass Source Activation System Final Report

Date: 2026-06-15

## Executive Verdict

The system is safer and closer to mass source activation, but it has not reached 50 working sources.

Public source truth before: 13 enabled UAE sources / 9 readiness-supported / 4 remediation.

Public source truth after: 13 enabled UAE sources / 9 readiness-supported / 4 remediation.

## What Was Audited

- Source Discovery Engine.
- Auto DOM Investigator.
- Adapter registry/platform.
- Source Lab no-save flow.
- Evidence/proof and source runs.
- Repeat baseline/certification logic.
- Diff/hash flow.
- Activation readiness logic.
- Source Lab UI/API flow.
- Existing UAE 50-source work queue.
- Validators.
- Legacy/duplicate source-monitoring code candidates.

## What Was Improved

- Added general mass source activation state machine:
  - `product/regradar/app/mass_source_activation.py`
- Added mass activation queue:
  - `product/regradar/config/mass_source_activation_queue.json`
- Added focused tests:
  - `product/regradar/tests/test_mass_source_activation.py`
- Added validator:
  - `tools/validate_mass_source_activation_pipeline.py`
- Corrected stale CLI help for `discover-source` in `product/regradar/run.py`.
- Added audit/architecture/final review docs for the mass activation system.

## Code Removed

None.

No suspicious code was deleted because `source_connector` and other legacy-looking modules still have references or runtime risk. They are documented for later refactor/deprecation review.

## Mass Source Activation Score

Before: 7.2/10.

After: 8.0/10.

Reason for improvement: the system now has a general queue-level state machine and validator, not just UAE-specific validation. It still needs source-specific adapters and stronger discovery relevance filtering to support high-volume activation.

## New Blockers Found

1. Discovery link graph can surface official but low-value pages, such as About/Services, which creates noise risk in batch onboarding.
2. ADGM no-save extraction can produce meaningful content but still fall below save quality gate.
3. CBUAE tested endpoint returned HTTP 403.
4. VARA tested framework URL returned HTTP 404.
5. DFSA AML/MLRO discovery found candidates but DOM type remained unknown.

## Blockers Fixed

1. Missing general mass activation state machine.
2. Missing general mass activation queue.
3. Missing general mass activation validator.
4. Missing tests for activation state boundaries.
5. Stale `discover-source` CLI help text.

## Remaining Blockers

- Source-specific SCA listing/table extraction needs stronger item-level filtering.
- DFSA selector/module remediation remains needed.
- CBUAE needs access-safe official endpoint discovery for 403 cases.
- VARA framework URL needs rediscovery.
- Proof/baseline automation exists but still needs scoped batch runner wiring before high-volume source activation.

## Live Validation Summary

- Live validation targets tested: 5.
- No-save attempted: 1.
- Strong no-save passed: 0.
- Saved evidence count: 0.
- Activation-ready new sources: 0.

No live validation result changed `sources.json` or public source truth.

## Customer-Safe Claim Now

Allowed:

“StatuteProof has a source discovery, DOM investigation, adapter, no-save, evidence, baseline, and agent-gated activation pipeline. Public source truth remains 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.”

## Claims Still Forbidden

- “50 working sources”
- “60 validated sources”
- “Any website can be parsed”
- “Perfect parsing”
- “95% of websites” as public copy
- “Guaranteed compliance”
- “Legal advice”
- “Official regulator certified”

## Did We Reach 50 Working Sources?

No.

Why not:

- This sprint hardened the activation system; it did not run proof/baseline activation for 50 sources.
- Live checks found real blockers: noisy discovery, ADGM quality threshold, CBUAE 403, VARA 404, DFSA unknown DOM type.
- No source can be counted as working without proof, repeat baseline, and gates.

## Next Exact Task

Run a source-specific remediation sprint for SCA + DFSA + CBUAE:

- tighten SCA discovery relevance filters and table/listing extraction;
- find DFSA AML/MLRO selectors on the resolved `/summary` endpoint;
- discover CBUAE official alternate endpoints that avoid HTTP 403 while remaining public and permitted;
- run no-save only, then save evidence only for strong passes.

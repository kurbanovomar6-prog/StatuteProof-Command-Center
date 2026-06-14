# Source Activation Current System Audit

Date: 2026-06-15

## 1. Current Score

Current source activation platform score: **7.8/10**.

It is materially stronger than the early Source Lab, but not yet a high-throughput activation factory.

## 2. What Already Works

- Source Lab can run no-save checks and saved evidence checks.
- No-save is clearly separated from evidence and monitoring activation.
- Source certification requires baseline discipline.
- Adapter platform exists with generic `custom_element`, `listing`, and `table` families.
- Early source-specific adapters exist for SCA, DFSA rulebook, CBUAE document listings, FIU/EOCN document listings, and VARA PDF listings.
- Parser quality validator blocks unsafe claims and checks Source Lab contract fields.
- UAE 50-source validator blocks fake activation-ready states.

## 3. What Blocks Mass Source Onboarding

- No automatic DOM investigation module exists yet.
- Selector recommendation is still manual.
- Source-specific adapters are limited and fixture-tested but not live-proven.
- Failure reasons are useful but not consistently coded into machine-readable failure codes.
- No single CLI workflow runs investigate -> no-save -> save -> repeat baseline -> gates.
- Source Lab UI does not yet show DOM investigation, selector confidence, or adapter recommendations.
- Work queue gates exist but are not uniformly complete for every candidate.

## 4. Missing Adapter Families

Implemented or partially implemented:

- custom element
- listing
- table
- SCA listing
- DFSA rulebook
- CBUAE document listing
- FIU/EOCN document listing
- VARA PDF listing

Missing or incomplete:

- static HTML/article adapter as explicit family
- Playwright selector adapter as explicit adapter metadata family
- PDF document adapter
- PDF listing adapter as generic family
- register adapter
- sitemap/RSS adapter
- public JSON/API adapter
- screenshot/rendered DOM evidence adapter
- ADGM/FSRA source-specific listing adapter
- DFSA AML/MLRO and enforcement adapters

## 5. Missing DOM Investigation Logic

Needed:

- classify page type from rendered DOM;
- propose `wait_selector`, `content_selector`, and `item_selector`;
- detect PDF links, tables, listing cards, custom elements, shadow DOM hints, lazy-loaded content;
- identify nav/footer/search chrome;
- explain selector choice;
- score nav-shell, noise, and source-health risk;
- map failures into structured remediation hints.

## 6. Missing Quality Gates

Existing gates cover many cases, but need stronger structured fields:

- `official_status`
- `access_status`
- `meaningful_content`
- `shallow_content`
- `duplicate_hash`
- `noise_risk`
- `source_health_risk`
- `can_save_evidence`
- `failure_code`

## 7. Missing Evidence / Baseline Automation

The evidence system exists, but an activation factory needs a scoped command or workflow that coordinates:

1. no-save pass;
2. saved proof;
3. repeat baseline;
4. stability/diff explanation;
5. agent gates;
6. activation decision.

This sprint should add groundwork, not broad live automation.

## 8. Missing UI Remediation Controls

Source Lab should expose:

- DOM investigation result;
- recommended adapter and selectors;
- extracted preview;
- quality/noise/source-health risk;
- failure code and remediation hint;
- actions for retry with JS, listing/PDF listing adapter, mark remediation, and save baseline.

Buttons must not fake backend functionality.

## 9. P0 / P1 / P2 Fixes

P0:

- Add Auto DOM Investigator with fixture coverage.
- Add structured failure codes before save.
- Add validator for source activation platform invariants.
- Keep public truth unchanged unless proven.

P1:

- Add explicit missing adapter families where safe.
- Improve Source Lab remediation UI fields.
- Add CLI command for DOM investigation.

P2:

- Add baseline automation command.
- Add screenshot/rendered DOM evidence layer.
- Add live source-specific remediation for SCA/DFSA/CBUAE.

## 10. Files To Change

- `product/regradar/app/dom_investigator.py`
- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/run.py`
- `product/regradar/app/api.py`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/tests/`
- `tools/validate_source_activation_pipeline.py`
- documentation under `docs/`

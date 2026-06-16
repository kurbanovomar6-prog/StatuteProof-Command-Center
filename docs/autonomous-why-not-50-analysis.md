# Autonomous Why-Not-50 Analysis

Date: 2026-06-15

## 1. What Blocks 50?

The repo now has enough candidate volume, but not enough proof-backed strong passes. The blocker is source-specific extraction on JS-heavy or stale official pages, not discovery.

Current truth: 36 enabled / 32 readiness-supported / 4 remediation. Reaching 50 requires 18 more proof-backed, baseline-stable, gate-passing sources.

## 2. Highest Activation Potential

1. ADGM alternate listing/media/data-protection pages if the correct component/item selector or replacement URL is found.
2. VARA official rulebook/PDF endpoints if current nav-shell/stale paths are replaced with stable public document URLs.
3. DFSA/DIFC only where stable listing selectors are accessible without bypassing protections.
4. CBUAE non-rulebook public endpoints only if official alternates are accessible; the rulebook revision-update alternate has now been activated.

## 3. Missing Adapter / Selector Work

- SCA market rules still need a decision on whether they are separate sources or better covered by SCA regulations listing / ADX / DFM linked endpoints.
- ADGM RA notices and AML quick guides currently resolve to a 404 page shell.
- ADGM media/listing/data-protection regulatory-actions pages have content but current item selectors still collapse to nav/noise.
- FIU mutual-evaluation route duplicates active FIU typology output.
- FIU annual-reports route duplicates the activated publications-hub output.
- VARA rulebook/framework/public-register URLs still return nav-shell/stale paths under tested selectors.

## 4. Repeating DOM Problem

`adgm-page` and generic `listing` can detect a container, but still extract page chrome or a 404 shell. The DOM investigator must treat page title 404 and very short focused custom-element output as hard remediation signals.

## 5. Slowest Evidence Step

Playwright-based evidence runs take time but are not the main blocker. The main blocker is reaching strong no-save with a selector that extracts meaningful, stable content.

## 6. Validator Blockers

Validators correctly block fake readiness. New `validate_batch_onboarding.py` now blocks scoreboard/source registry divergence.

## 7. Technical Debt Hurting Us

- Truth still appears in several docs/config files and must be synchronized after every activation.
- Scoreboard exists, but no first-class runner writes all no-save/baseline updates back into it.
- DOM investigator over-recommends custom elements on ADGM 404 shells.

## 8. Open-Source Ideas To Review Next

- Playwright request/response capture patterns for JS-heavy listings.
- changedetection.io/browsertrix ideas for source-health status and selector drift.
- Scrapy/Crawlee patterns for paginated listing extraction.

## 9. Next Highest-Leverage Move

Fix DOM investigation and source-specific selectors or replacement URLs for ADGM Listing Authority / ADGM RA pages, then find official VARA PDF/rulebook endpoints that do not collapse to nav-shell.

## 10. Can The System Batch-Onboard Yet?

Partial. It can batch no-save-test and classify candidates. It cannot yet batch-activate without operator review because JS-heavy sources still require source-specific selectors and duplicate hash review.

## 11. What Blocks Batch-Onboarding?

- No-save conversion remains low on JS-heavy pages.
- Scoreboard updates are still partly manual.
- Source-specific adapters are needed for each regulator family.

## 12. Next Prompt

Use `docs/autonomous-next-execution-prompt.md`.

# Autonomous Why-Not-50 Analysis

Date: 2026-06-15

## 1. What Blocks 50?

The repo now has enough candidate volume, but not enough proof-backed strong passes. The blocker is source-specific extraction on JS-heavy or stale official pages, not discovery.

Current truth: 26 enabled / 22 readiness-supported / 4 remediation. Reaching 50 requires 24 more proof-backed, baseline-stable, gate-passing sources.

## 2. Highest Activation Potential

1. SCA pages that are near the existing `sca_listing` pattern.
2. ADGM/FSRA and Registration Authority pages if the correct component/URL is found.
3. UAE FIU pages where duplicate route aliases can be replaced with direct document/detail URLs.
4. VARA/CBUAE/DFSA only where stable public endpoints are accessible without bypassing protections.

## 3. Missing Adapter / Selector Work

- SCA FATCA/CRS needs richer document context to move from q=59 to q>=60.
- SCA corporate governance and market rules need a decision on whether they are separate sources or better covered by SCA regulations listing / ADX / DFM linked endpoints.
- ADGM RA notices and AML quick guides currently resolve to a 404 page shell.
- ADGM Listing Authority rules page has a real page title but current `adgm-page` extraction returns only heading/nav.
- FIU mutual-evaluation route duplicates active FIU typology output.

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

Fix DOM investigation and source-specific selectors for ADGM Listing Authority / ADGM RA pages, and separately raise SCA FATCA/CRS from q=59 to q>=60 with richer document-context extraction.

## 10. Can The System Batch-Onboard Yet?

Partial. It can batch no-save-test and classify candidates. It cannot yet batch-activate without operator review because JS-heavy sources still require source-specific selectors and duplicate hash review.

## 11. What Blocks Batch-Onboarding?

- No-save conversion remains low on JS-heavy pages.
- Scoreboard updates are still partly manual.
- Source-specific adapters are needed for each regulator family.

## 12. Next Prompt

Use `docs/autonomous-next-execution-prompt.md`.

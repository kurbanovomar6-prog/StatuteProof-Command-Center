# UAE 50 Sources JSON Change Log

Date: 2026-06-15

## Registry Change

`sources.json` changed: yes.

Before this cycle:

- 16 enabled UAE sources.
- 12 readiness-supported.
- 4 remediation.

After this cycle (2026-06-15 batch 1):

- 19 enabled UAE sources.
- 15 readiness-supported.
- 4 remediation.

## Activation Cycle — 2026-06-15 (batch 2, continuous activation sprint)

`sources.json` changed: yes.

Before batch 2: 19 enabled / 15 readiness-supported / 4 remediation.
After batch 2: **20 enabled / 16 readiness-supported / 4 remediation**.

### Source Added (batch 2)

4. `AE-adgm-fsra-guidance-policy` — ADGM FSRA Guidance and Policy Statements
   - URL: https://www.adgm.com/legal-framework/guidance-and-policy-statements
   - Adapter: custom_element (adgm-page selector)
   - No-save: q=65, CONFIRMED_ACCESSIBLE, noise_risk=low
   - Evidence: 2 saved runs, MONITORING_CERTIFIED, hash stable (704c83...)
   - Dry-run: hash matches baseline, no drift
   - Gates: all 6 emulated manually — PASS
   - Proof: data/source_snapshots/2026-06-15/AE/AE-adgm-fsra-guidance-policy/intake-20260615T143126Z/proof.json

### Source Rejected (batch 2)

- `AE-vara-news` (https://www.vara.ae/en/news/) — strong no-save in batch (pdf_listing q=65) but
  evidence save failed both times (wait_for_selector 'main' timeout → NEEDS_SELECTOR_REVIEW q=5).
  False positive from batch probe. Marked remediation. Not activated.

### Batch summary (batch 2, 49 sources tested)

- Tested: 49 | Strong no-save passes: 6 | Of those, already enabled: 4 | New: 2
- New genuinely activatable: 1 (ADGM guidance policy) | Failed evidence gate: 1 (VARA news)
- Failures: NAV_SHELL_ONLY 32, ACCESS_BLOCKED 3, SHALLOW_CONTENT 2, LISTING_ADAPTER_REQUIRED 1, TABLE_ADAPTER_REQUIRED 1, unknown 4

### Batch 1 Sources Added

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-adgm-fsra-consultations`

### Existing Source Updated (batch 1)

`AE-dfsa-aml-rulebook-module` remains active, but its proof path and normalized hash were updated after selector-path parity was fixed and two consecutive saved baseline runs produced the same new hash.

## Sources Not Added (any batch)

No no-save-only, one-run-only, high-noise, high-health-risk, nav-shell, blocked, false-positive, or generic sources were added.

## Why Safe

All activated sources have strong no-save results, saved proof paths, repeat baseline completion (MONITORING_CERTIFIED), stable hashes confirmed by dry-run, and all 6 required agent gates passing. VARA news was rejected despite initial batch pass because evidence save consistently failed — demonstrating the evidence gate works correctly as an anti-false-positive control.

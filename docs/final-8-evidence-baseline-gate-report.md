# Final-8 Evidence, Baseline, And Gate Report

Date: 2026-06-16

## Executive Gate Result

- Evidence candidates saved: **21**.
- Proof runs saved: **42**.
- Baseline-complete candidates: **21**.
- Mass-monitor `MONITOR_OK`: **21** total.
- Clean/no-drift mass-monitor candidates activated: **20**.
- Held despite proof/baseline: **1** (`AE-dfsa-aml-ctf-sanctions`, dry-run hash drift).

## Activated Sources

| Source ID | Evidence | Baseline | Mass-monitor | Gate decision |
| --- | --- | --- | --- | --- |
| `AE-cbuae-open-finance-rulebook` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-payment-token-services-rulebook` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-risk-management-rulebook` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-stored-value-facilities-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-operational-risk-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-market-risk-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-large-exposures-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-exchange-business-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-capital-adequacy-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-large-value-payment-systems-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-federal-decree-law-6-2025-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-country-transfer-risk-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-interest-rate-risk-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-model-management-standards-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-retail-payment-systems-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-sme-customer-protection-regulation-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-islamic-banks-risk-management-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-market-conduct-consumer-protection-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-proliferation-finance-guidance-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |
| `AE-cbuae-tbml-transshipment-guidance-doclist` | 2 proof runs | stable | `MONITOR_OK` | activate |

## Held Source

| Source ID | Reason |
| --- | --- |
| `AE-dfsa-aml-ctf-sanctions` | No-save and two evidence runs passed, but mass-monitor dry-run returned a different normalized hash. Held for selector/noise review instead of activation. |

## Agent Gate Emulation

All activated sources passed these six gates:

- **Source Monitor**: official CBUAE rulebook/guidance endpoint; public; meaningful extraction; source-health not high.
- **Evidence Trail**: proof paths written; normalized hashes present; two baseline runs complete; evidence level certified.
- **QA/Critic**: no nav-shell, no shallow extraction, no duplicate/shell hash, no unresolved high-noise risk.
- **Legal Language**: no legal advice, no compliance guarantee, no regulator-certification implication.
- **Product Manager**: useful to UAE MLRO/CCO/compliance operators because the sources cover central-bank rulebooks, payment services, risk, AML, proliferation finance, and consumer protection.
- **Code Architect**: used existing `cbuae_document_listing` adapter and activation pipeline; no broad rewrite or unsafe dependency.

## Evidence Artifacts

Detailed run data is in:

- `docs/final-8-evidence-results.json`
- `docs/final-8-extra-evidence-results.json`
- `docs/final-8-mass-monitor-dry-run.json`
- `docs/final-8-extra-mass-monitor-dry-run.json`

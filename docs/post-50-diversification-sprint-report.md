# Post-50 Diversification Sprint Report

Date: 2026-06-16

## Executive Verdict

Diversification was materially investigated, but the sprint did not safely add new non-CBUAE sources. The strongest non-CBUAE candidates either reconfirmed already active sources, failed evidence save, or exposed duplicate/stability blockers.

This is a good hardening result: the system did not inflate source count with duplicate URLs.

## Candidates Tested

| Batch | Tested | Strong no-save | Result |
| --- | ---: | ---: | --- |
| VARA | 8 | 1 | Strong pass reconfirmed already active VARA root PDF listing; nested rulebook/framework pages remain nav-shell. |
| DFSA | 6 | 1 | `AE-dfsa-aml-mlro-notices` passed no-save, but evidence save failed selector reproducibility. |
| ADGM/FSRA | 7 | 2 | Strong passes reconfirmed already active ADGM root/rules URLs; no new unique source activated. |
| DIFC | 5 | 0 | Access/selector issues remain: listing/table adapters required and one access-blocked path. |
| UAE FIU | 3 | 0 | Remaining FIU routes are nav-shell aliases of already activated hubs. |
| SCA | 4 | 1 | Strong pass reconfirmed already active SCA circulars URL. |
| Total | 33 | 5 | 0 new non-CBUAE activations. |

## Strong No-Save Passes

| Source ID | Verdict |
| --- | --- |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | Already active; do not duplicate. |
| `AE-dfsa-aml-mlro-notices` | No-save strong, evidence save failed selector reproducibility; hold. |
| `AE-abu-dhabi-global-market-adgm` | Already active; do not duplicate. |
| `AE-adgm-legal-framework-rules` | Strong, evidence saved, mass-monitor OK, but duplicate URL of active `AE-adgm-fsra-rulebooks`; do not duplicate. |
| `AE-sca-circulars` | Strong, evidence saved, mass-monitor OK, but duplicate URL of active `AE-sca-circulars-rules-procedures`; do not duplicate. |

## Evidence / Baseline

Evidence and repeat baselines were saved for:

- `AE-adgm-legal-framework-rules`
- `AE-sca-circulars`
- `AE-dfsa-aml-ctf-sanctions` fresh drift investigation baseline

No new source was activated because:

- ADGM and SCA candidates duplicate existing active source URLs.
- DFSA held source still has monitor-path hash drift.
- DFSA MLRO notice path cannot reproduce evidence save selector.

## Distribution Before / After

No registry activation occurred in this diversification sprint.

| Group | Before | After |
| --- | ---: | ---: |
| CBUAE | 27 | 27 |
| ADGM/FSRA | 10 | 10 |
| DFSA | 8 | 8 |
| FIU/EOCN/AML | 7 | 7 |
| SCA | 4 | 4 |
| VARA | 3 | 3 |
| Federal/Legislation/Tax | 3 | 3 |

CBUAE concentration remains **43.5%**.

## Remaining Blockers

- VARA direct rulebook/framework URLs produce nav-shell; direct official PDF extraction is still the best next path.
- DIFC needs a source-specific listing/table adapter and access-safe alternate endpoint research.
- DFSA AML/CTF root has stable evidence but monitor-path hash drift.
- DFSA MLRO notice child URL passes no-save but evidence save selector currently fails.
- ADGM alternate pages still need component-specific selectors or replacement URLs.
- FIU leftovers are mostly shell or duplicate aliases.

## Next Diversification Move

Build direct official PDF extraction for VARA rulebooks and a DIFC table/listing adapter using local fixtures first. Do not activate duplicate source IDs for URLs already active under better canonical IDs.

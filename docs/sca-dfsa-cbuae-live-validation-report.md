# SCA / DFSA / CBUAE Live Validation Report

Date: 2026-06-15

## Scope

Controlled live validation only.

Rules followed:

- no broad monitoring;
- no all-source monitor command;
- no customer messages;
- no Telegram/email;
- no `sources.json` update;
- no evidence save;
- no activation-ready promotion.

## Results

| Target | Mode | Result | Quality | Failure Code | Saved Evidence | Activation-Ready |
|---|---|---:|---:|---|---:|---:|
| `AE-sca-latest-regulations` | runner `no-save-only` | remediation | 45 | `LISTING_ADAPTER_REQUIRED` | 0 | 0 |
| `AE-sca-aml-cft` | runner `no-save-only` | remediation | 55 | `NAV_SHELL_ONLY` | 0 | 0 |
| `AE-dfsa-aml-mlro-notices` | runner `no-save-only` | remediation | 0 | `NAV_SHELL_ONLY` | 0 | 0 |
| `AE-dfsa-rulebook-thomsonreuters` | runner `no-save-only` | remediation | 0 | `NAV_SHELL_ONLY` | 0 | 0 |
| `AE-cbuae-regulations` | runner `no-save-only` | remediation | 0 | `NAV_SHELL_ONLY` | 0 | 0 |
| SCA circulars/rules URL | discovery-only | candidate | n/a | none | 0 | 0 |

## Queue Updates

Updated only:

- `product/regradar/config/mass_source_activation_queue.json`

No source reached proof-backed or activation-ready state.

## Why Public Truth Did Not Change

Every tested source remained preview/remediation/candidate. No saved evidence, repeat baseline, or full agent gates passed.

Public truth remains:

13 enabled UAE sources / 9 readiness-supported / 4 remediation.

## Next Remediation Signal

The strongest next candidate is SCA circulars/rules discovery because it returns a public candidate with listing signals and better filtered recommended paths. It still needs a no-save runner queue entry and item-level extraction test before evidence save.

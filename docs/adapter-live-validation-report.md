# Adapter Live Validation Report

Date: 2026-06-14

## 1. Scope

Scoped live checks only. No broad monitoring. No evidence save. No customer delivery.

Commands used the Source Lab no-save path with explicit adapter metadata.

## 2. Results

| Source | Adapter | No-save result | Normalized length | Hash | Quality | Evidence level | Decision |
|---|---|---:|---:|---|---|---|---|
| ADGM/FSRA financial crime prevention | `custom_element` | `CONFIRMED_ACCESSIBLE` | 4,819 | `d8f2bf4e637d80fd029c7e68ae3e5ad255ca551ac88c1259041baac6e288aed8` | LIMITED / 51 | PREVIEW_ONLY | Can save for validation; baseline required. |
| ADGM/FSRA rules and regulations | `custom_element` | `CONFIRMED_ACCESSIBLE` | 1,876 | `2a22baa9eb55d54c9d43edd714406e8b93c8f0eb1ca0e1e1c03e475d9a6eb2c4` | LIMITED / 48 | PREVIEW_ONLY | Can save for validation; baseline required. |
| SCA latest regulations | `listing` | `BLOCKED` | 906 | `dc0c22e70fbf6c87379deb03ec3b2a7a76d28eb021c047457642df9968a3ecb3` | POOR / 23 | PREVIEW_ONLY | Keep remediation. |

## 3. ADGM Details

Both ADGM pages used:

- `--js`
- `--wait-for-selector "adgm-page > span"`
- `--adapter-family custom_element`
- adapter config: `{"content_selector":"adgm-page > span"}`

Observed:

- adapter_used: true
- nav_shell_detected: false
- hash_collision: false
- can_save_for_validation: true
- can_activate_monitoring: false
- activation_readiness: BASELINE_REQUIRED

This is the correct no-save behavior.

## 4. SCA Details

SCA latest regulations used:

- `--js`
- `--wait-for-selector "[data-icms-list]"`
- `--adapter-family listing`

Observed:

- adapter_used: false
- listing item_count: 0
- nav_shell_detected: false on second run
- policy_warnings included `captcha` and `login`
- readiness_status: BLOCKED
- can_activate_monitoring: false

Decision:

- Keep SCA latest regulations in remediation.
- Investigate rendered DOM/shadow/data source before attempting save mode.

## 5. Customer-Facing Impact

None.

The live checks were no-save previews and do not change:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

## 6. Next Exact Task

Build an SCA-specific rendered-listing investigation that captures the actual item structure or official public data source without bypassing access controls.

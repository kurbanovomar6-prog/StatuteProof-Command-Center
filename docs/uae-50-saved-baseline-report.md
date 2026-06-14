# UAE 50 Saved Baseline Report

## Executive Result

Scoped repeat saved baselines run in this sprint: **3**.

Successful repeat saved baselines: **3**.

New activation-ready candidates after agent gates: **2**.

Sources still held after baseline: **1**.

No broad monitoring, customer delivery, Telegram/email, or all-source run was performed.

## Repeat Baseline Results

| source_id | baseline | evidence level | normalized hash | decision | latest proof path |
| --- | --- | --- | --- | --- | --- |
| AE-adgm-fsra-financial-crime-prevention | 2/2 | CERTIFIED_EVIDENCE | fa442e94df6d70a8ecff211b9c8e35ee8cddc1120b119894c708d0cdbbfdeaf6 | activation-ready candidate | data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T154830Z/proof.json |
| AE-adgm-fsra-rulebooks | 2/2 | CERTIFIED_EVIDENCE | 81d1ce45e63342981a67e89149852d9d5f9b463669459c1cc9a7b7e1725924e0 | activation-ready candidate | data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T154850Z/proof.json |
| AE-sca-latest-regulations | 2/2 | CERTIFIED_EVIDENCE | 5b0c842d72fe971eee44d206f8a664e0adafeacf1f22a0b49af9ba2f4b106beb | remediation: high source-health/listing risk | data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T154911Z/proof.json |

## Evidence Trail Review

- Proof paths exist for all three repeat baselines.
- Normalized hashes remained stable across both saved runs.
- No nav-shell or hash collision was reported for the three repeat saved runs.
- Evidence artifacts remain local/ignored according to project policy and were not force-added.

## Activation Boundary

A completed parser certification does not by itself change public source truth. The work queue requires Source Monitor, Evidence Trail, QA/Critic, Legal Language, Code Architect, and Product Manager gates before a source counts toward the 50 working-source pack.

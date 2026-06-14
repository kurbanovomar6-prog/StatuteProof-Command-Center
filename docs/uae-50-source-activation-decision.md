# UAE 50 Source Activation Decision

## Executive Decision

Do not update `product/regradar/sources.json` in this sprint.

Reason: only **2** sources reached activation-ready candidate status under the new agent-gated queue. The target is 50 working official sources, so the truthful action is to record progress and continue source-specific remediation.

## Activation-Ready Candidates

| source_id | regulator | noise | health | proof path | reason |
| --- | --- | --- | --- | --- | --- |
| AE-adgm-fsra-financial-crime-prevention | ADGM/FSRA | low | medium | data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T154830Z/proof.json | All required gate fields pass for candidate activation; sources.json still requires explicit registry-change approval. |
| AE-adgm-fsra-rulebooks | ADGM/FSRA | medium | medium | data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T154850Z/proof.json | All required gate fields pass for candidate activation; sources.json still requires explicit registry-change approval. |

## Baseline-Complete But Held

| source_id | regulator | noise | health | status | reason |
| --- | --- | --- | --- | --- | --- |
| AE-sca-latest-regulations | SCA | medium | high | remediation | Proof exists, but unresolved high noise/source-health risk blocks activation. |

## Public Source Truth

Unchanged:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## Allowed Wording

- “Two ADGM candidates reached activation-ready candidate status after local proof and repeat baseline checks.”
- “SCA latest regulations has proof-backed baselines but remains under source-health remediation.”
- “The public source count has not changed.”

## Forbidden Wording

- “50 working UAE sources.”
- “60 validated sources.”
- “ADGM/SCA default pack is live.”
- “Regulator-certified monitoring.”

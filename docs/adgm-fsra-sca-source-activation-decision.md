# ADGM/FSRA + SCA Source Activation Decision

## 1. Decision

Do not activate ADGM/FSRA or SCA candidates in `sources.json` yet.

Three candidates now have local proof-backed saved evidence attempts, but each still needs a repeat baseline before activation review. One candidate failed save mode and stays in remediation.

Current public source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## 2. Evidence-Confirmed Candidates

Evidence-confirmed here means local proof/snapshot artifacts exist and normalized hashes were recorded. It does not mean monitoring-ready.

| Source ID | Evidence status | Proof path | Activation decision |
|---|---|---|---|
| `AE-adgm-fsra-financial-crime-prevention` | Evidence exists, but first certification report was generated before duplicate-run certification fix | `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T151800Z/proof.json` | Repeat saved baseline required before activation review. |
| `AE-adgm-fsra-rulebooks` | Evidence confirmed locally | `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T151916Z/proof.json` | Repeat saved baseline required before activation review. |
| `AE-sca-latest-regulations` | Evidence confirmed locally | `data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T153028Z/proof.json` | Repeat baseline plus listing-noise filter required. |

## 3. Still Preview / Remediation

| Source ID | Status | Reason |
|---|---|---|
| `AE-sca-aml-cft` | Remediation | Save-mode extraction returned only `Previous / Next`; no proof artifact was created. |

## 4. Sources Needing Second Baseline Run

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-sca-latest-regulations`

These should be rerun after the certification deduplication fix. If hashes remain stable, proof paths exist, and quality remains acceptable, they can move to activation review. They still should not become customer-visible ready automatically.

## 5. Sources Needing Noise Filters Before Activation

| Source ID | Filter needed |
|---|---|
| `AE-sca-latest-regulations` | Listing-row normalization: title, decision number, year, detail URL if available. Avoid whole-page chrome diffs. |
| `AE-adgm-fsra-rulebooks` | Link/index normalization for rulebook modules and official external rulebook references. |

`AE-adgm-fsra-financial-crime-prevention` has the lowest noise risk among this group, but still requires repeat baseline and source-health review because it relies on ADGM custom elements.

## 6. Can Public Source Truth Change?

No.

The public source truth cannot change from:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation**

because:

- no `sources.json` activation occurred;
- no candidate completed repeat baseline after the certification fix;
- SCA AML/CFT failed save mode;
- SCA latest regulations remains shallow/listing-only;
- founder/source-monitor approval has not been recorded for customer-visible readiness expansion.

## 7. Allowed Wording

- “Selected ADGM/SCA candidates have local proof-backed baseline attempts.”
- “Three candidates are baseline-pending; one SCA AML/CFT candidate remains under selector remediation.”
- “No customer-facing source count has changed.”

## 8. Forbidden Wording

- “ADGM/SCA sources are monitoring-ready.”
- “SCA AML/CFT is evidence-confirmed.”
- “40+ UAE sources monitored.”
- “60 validated UAE sources.”
- “StatuteProof now monitors ADGM and SCA by default.”

## 9. Exact Next Task

Run a repeat saved baseline only for:

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-sca-latest-regulations`

Then review whether each has two distinct successful evidence runs after the certification deduplication fix.

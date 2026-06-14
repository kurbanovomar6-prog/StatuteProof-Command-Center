# Source Registry Expansion Change Report

## 1. Decision

`product/regradar/sources.json` was not changed in this run.

The source expansion work created a separate research/configuration candidate file:

`product/regradar/config/uae_source_candidates.json`

## 2. Why No Active Registry Change Was Made

The task discovered 60 official or officially linked UAE source candidates and ran a small no-save validation batch. The results are useful, but not enough to safely add or enable dozens of sources in the active monitoring registry.

Reasons:

- Most candidates are not yet no-save tested.
- Two DFSA candidates passed no-save accessibility but still have `PREVIEW_ONLY` evidence and baseline requirements.
- Several generic checks produced nav-shell, access-warning, or blocked results.
- Existing active source truth must remain 13 enabled / 9 readiness-supported / 4 remediation.
- Adding untested sources to `sources.json` would risk fake coverage and customer-facing overclaim.

## 3. Old Count Vs New Count

| Registry | Enabled UAE | Readiness-supported | Remediation | Candidate-only |
|---|---:|---:|---:|---:|
| Before this run | 13 | 9 | 4 | 0 |
| After this run | 13 | 9 | 4 | 60 |

The 60 candidate-only endpoints are not active sources.

## 4. Candidate Registry

Candidate-only file:

`product/regradar/config/uae_source_candidates.json`

It includes:

- 60 candidates;
- 40 top-priority candidates;
- 6 rejected/no-garbage examples;
- official status;
- source type;
- jurisdiction;
- buyer relevance;
- initial status;
- parsing risk;
- candidate pack assignment.

## 5. What Would Justify A Future `sources.json` Change

A future registry migration can add candidates as disabled/candidate/remediation/readiness-supported only after:

1. candidate discovery report exists;
2. no-garbage policy passes;
3. no-save Source Lab report exists;
4. URL is stable and reachable;
5. selector/content extraction is meaningful;
6. nav-shell and hash-collision checks pass;
7. source status does not imply evidence-confirmed or monitoring-ready without proof/baseline;
8. Source Monitor, Evidence Trail, QA, and Legal Language gates approve the customer-facing wording.

## 6. Recommended First Registry Migration

Do not migrate all 60 candidates at once.

First migration should focus on:

- `AE-dfsa-rulebook-thomsonreuters`
- `AE-dfsa-aml-mlro-notices`
- possibly a source-specific VARA enforcement selector/adapter;
- one ADGM/FSRA rulebook/guidance page after no-save validation;
- one SCA law/decision page after selector remediation;
- EOCN sanctions/TFS exact subpage after official URL discovery.

Each should enter the registry with conservative status and no evidence-confirmed claim until saved proof and baseline requirements are complete.

## 7. Customer-Facing Impact

No public source count should change from this run.

Allowed:

“60 official UAE source candidates mapped for validation.”

Forbidden:

“60 validated sources.”

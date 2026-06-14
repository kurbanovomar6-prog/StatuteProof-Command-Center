# ADGM/FSRA + SCA Saved-Evidence Baseline Report

## 1. Executive Verdict

Four scoped saved Source Lab checks were run. Three created local proof/snapshot artifacts. One SCA source failed in save mode and created no proof.

No broad monitoring was run. No customer delivery was triggered. `sources.json` was not changed.

Current public source truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

| Metric | Count |
|---|---:|
| Saved checks run | 4 |
| Proof artifacts created | 3 |
| Evidence-confirmed local candidates | 3 |
| Monitoring-ready candidates | 0 |
| Candidates needing repeat baseline | 3 |
| Candidates needing selector/adapter remediation | 1 |

## 2. Important QA Finding

The first saved run exposed a certification counting bug: the Source Lab evidence writer built the certification report from `latest_runs()` plus the newly appended run, causing a single saved run to appear twice in the certification history.

Fix applied in code:

- `product/regradar/app/source_intake.py` now builds source certification from distinct source history after append.
- `product/regradar/app/source_certification.py` now deduplicates successful runs by run id / proof path / timestamp.
- A regression test was added in `product/regradar/tests/test_parser_benchmark_suite.py`.

Impact:

- The first proof artifact remains useful as evidence, but its generated `certification_report.json` must not be used as an activation decision by itself.
- Later saved runs correctly remained `BASELINE_PENDING` with `baseline_runs_completed = 1`.

## 3. Saved Check Results

| Source ID | URL | Selector | Saved result | Evidence level | Baseline | Proof path | Activation |
|---|---|---|---|---|---|---|---|
| `AE-adgm-fsra-financial-crime-prevention` | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | `adgm-page > span` | Saved successfully | `FULL_EVIDENCE` | 1 / 2 after QA correction | `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T151800Z/proof.json` | Not monitoring-ready. |
| `AE-adgm-fsra-rulebooks` | `https://www.adgm.com/legal-framework/rules-and-regulations` | `adgm-page > span` | Saved successfully | `FULL_EVIDENCE` | 1 / 2 | `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T151916Z/proof.json` | Not monitoring-ready. |
| `AE-sca-aml-cft` | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `[data-icms-list]` | Failed save-mode quality gate | `PREVIEW_ONLY` | 0 / 2 | none | Remediation. |
| `AE-sca-latest-regulations` | `https://www.sca.gov.ae/en/regulations/regulations` | `[data-icms-list]` | Saved successfully | `FULL_EVIDENCE` | 1 / 2 | `data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T153028Z/proof.json` | Not monitoring-ready. |

## 4. Per-Source Details

### `AE-adgm-fsra-financial-crime-prevention`

- Normalized length: 4,788.
- Normalized hash: `fa442e94df6d70a8ecff211b9c8e35ee8cddc1120b119894c708d0cdbbfdeaf6`.
- Quality score / label: 59 / LIMITED.
- Readiness status: `CONFIRMED_ACCESSIBLE`.
- Evidence level: `FULL_EVIDENCE`.
- Activation readiness: baseline required.
- Normalized preview: “Operating in ADGM / Financial & Cybercrime Prevention / Financial & Cyber Crime Prevention / Developing sound practices in AML/TFS and cybercrime prevention compliance…”

Evidence paths:

- Normalized text: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T151800Z/normalized.txt`
- Raw text: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T151800Z/raw.txt`
- Metadata: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-financial-crime-prevention/intake-20260614T151800Z/metadata.json`

### `AE-adgm-fsra-rulebooks`

- Normalized length: 1,849.
- Normalized hash: `81d1ce45e63342981a67e89149852d9d5f9b463669459c1cc9a7b7e1725924e0`.
- Quality score / label: 56 / LIMITED.
- Readiness status: `CONFIRMED_ACCESSIBLE`.
- Evidence level: `FULL_EVIDENCE`.
- Activation readiness: `BASELINE_REQUIRED`.
- Normalized preview: “ADGM Regulations and Rules / Legal Framework / ADGM published its first set of commercial rules and regulations…”

Evidence paths:

- Normalized text: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T151916Z/normalized.txt`
- Raw text: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T151916Z/raw.txt`
- Metadata: `data/source_snapshots/2026-06-14/AE/AE-adgm-fsra-rulebooks/intake-20260614T151916Z/metadata.json`

### `AE-sca-aml-cft`

- Saved proof created: no.
- Readiness status: `NAV_SHELL_ONLY`.
- Evidence level: `PREVIEW_ONLY`.
- Normalized length: 13.
- Normalized hash: `0226639ff72d78f73f430b5d4cba48ea5ab3b9cfc9d4af7c065a9b483e39e5d8`.
- Preview: `Previous / Next`.
- Failure reason: saved-mode extraction returned carousel/navigation text only.
- Remediation hint: investigate a more stable post-render selector or SCA item/list adapter before retrying save mode.

### `AE-sca-latest-regulations`

- Normalized length: 536.
- Normalized hash: `5b0c842d72fe971eee44d206f8a664e0adafeacf1f22a0b49af9ba2f4b106beb`.
- Quality score / label: 49 / LIMITED.
- Readiness status: `CONFIRMED_ACCESSIBLE`.
- Evidence level: `FULL_EVIDENCE`.
- Activation readiness: `BASELINE_REQUIRED`.
- Normalized preview: “Latest Regulations / The Chairman of the Authority’s Board of Directors’ Decision No. (11/ Chairman) of 2026…”

Evidence paths:

- Normalized text: `data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T153028Z/normalized.txt`
- Raw text: `data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T153028Z/raw.txt`
- Metadata: `data/source_snapshots/2026-06-14/AE/AE-sca-latest-regulations/intake-20260614T153028Z/metadata.json`

## 5. Source Registry Decision

Do not update `product/regradar/sources.json` in this sprint.

Reason:

- All successful saved sources still have only one usable baseline run.
- SCA latest regulations is shallow/listing-only and needs row-level normalization before activation.
- SCA AML/CFT failed save mode and needs selector/adapter remediation.
- Public source truth must not change from baseline-pending candidates.

## 6. Customer-Facing Wording

Allowed:

- “Three ADGM/SCA candidate sources now have local proof-backed baseline attempts.”
- “Saved evidence exists for selected ADGM/SCA candidates, but repeat baseline and activation checks are still required.”
- “SCA AML/CFT remains under selector remediation.”

Forbidden:

- “ADGM/SCA monitoring-ready.”
- “SCA AML/CFT evidence confirmed.”
- “40+ sources monitored.”
- “60 validated sources.”
- “Public source count expanded.”

## 7. Next Exact Task

Run one repeat saved baseline only for the three proof-backed candidates after the certification-deduplication fix, then decide whether any can move to candidate activation review.

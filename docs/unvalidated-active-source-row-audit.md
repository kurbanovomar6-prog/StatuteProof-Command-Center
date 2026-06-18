# Unvalidated Active Source Row Audit

Date: 2026-06-18

## Decision

RESOLVED after eight-row truth repair on 2026-06-18.

The dirty 87/86/1 claim was not accepted. After no-save checks, evidence saves, repeat baselines, and mass-monitor dry-run:

- 2 ADGM rows became proof-backed monitoring-active sources.
- 6 rows were demoted to `enabled:false` / `status:candidate`.
- Final repaired truth: 81 enabled UAE sources / 80 monitoring-active / 1 remediation.
- No unvalidated FTA/ADGM dirty row remains active.

The original blocking audit is preserved below for traceability.

## Original Blocking Decision

BLOCK activation expansion until the current dirty registry state is resolved.

The committed verified source truth at `HEAD` is:

- 79 enabled UAE sources
- 78 readiness-supported / monitoring-ready sources
- 1 remediation source

The current dirty worktree `sources.json` reports:

- 87 enabled UAE sources
- 86 `status: active`
- 1 remediation source

That dirty 87/86/1 count is not evidence-backed. Eight newly added rows are marked `enabled:true` and `status:active` but lack the required activation fields.

## Blocking Rule

A source cannot remain active unless it has:

- stable `source_id`
- `proof_path`
- `normalized_hash`
- repeat baseline metadata
- mass-monitor `MONITOR_OK` or approved equivalent
- review-gate notes / evidence trail

The eight dirty rows below do not meet that standard.

## Unvalidated Dirty Active Rows

| # | Name | URL | Current dirty status | Missing activation fields | Required action |
|---:|---|---|---|---|---|
| 1 | Federal Tax Authority — All Tax Legislation | `https://tax.gov.ae/en/legislation.aspx` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 2 | Federal Tax Authority — VAT Guides and References | `https://tax.gov.ae/en/taxes/vat/guides.references.aspx` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 3 | Federal Tax Authority — Corporate Tax Guides and References | `https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 4 | Federal Tax Authority — Media Centre | `https://tax.gov.ae/en/media.centre.aspx` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 5 | Federal Tax Authority — Corporate Tax Legislation | `https://tax.gov.ae/en/legislation/corporate-tax.aspx` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 6 | ADGM FSRA Supervision Circulars | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 7 | ADGM FSRA Regulatory Alerts | `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/enforcement/regulatory-alerts` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |
| 8 | ADGM Data Protection Regulations 2021 — Official PDF | `https://www.adgm.com/documents/office-of-data-protection/resources/adgm-data-protection-regulations-2021-updated.pdf` | `enabled:true`, `status:active` | `source_id`, `proof_path`, `normalized_hash`, `baseline_runs_completed`, `last_monitor_status` | Move to candidate/remediation or run full activation pipeline. |

## Customer-Facing Copy Risk

The dirty frontend changes also upgrade several coverage cards to `Strong` / `Good` based on these unvalidated rows. That is unsafe until the rows pass evidence gates.

Examples of risky current dirty claims:

- FTA / Tax shown as materially improved while FTA rows lack proof and source IDs.
- ADGM / FSRA shown as stronger based on three rows lacking proof and source IDs.
- Data Protection shown as stronger based partly on an ADGM PDF row lacking proof and source ID.

These may become true after validation, but they are not safe as current public claims.

## Required Unblock Path

Choose one of two safe paths:

1. **Demote first, then expand.**
   - Move the eight rows out of `status:active`.
   - Put them into candidate/remediation queue with stable proposed `source_id`s.
   - Restore public truth to the last verified count.
   - Then start the 1,000-source universe mapping sprint.

2. **Validate the eight rows first.**
   - Assign stable `source_id`s.
   - Run no-save Source Lab checks.
   - Save proof only for strong passes.
   - Run repeat baseline twice.
   - Run mass-monitor dry-run.
   - Require `MONITOR_OK`.
   - Update registry only for rows that pass all gates.

## Final Gate Verdict

Do not continue the 1,000-source activation sprint on top of this dirty registry state.

The next safe task is:

**Validate or demote the eight unvalidated FTA/ADGM active rows, then rerun source truth validators.**

Monitoring intelligence only. Not legal advice. No complete UAE coverage claim.

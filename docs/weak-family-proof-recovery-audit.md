# StatuteProof Weak Family Proof Recovery Audit

Date: 2026-06-21

## Verdict

PASS, narrow improvement.

Chosen family: UAE FIU.

This sprint did not activate new UAE FIU sources and did not claim FIU circulars
are monitored. It improved proof readiness by creating one new hash-verifiable
canonical evidence record for a high-value UAE FIU typology-report change and
linking the matching alert queue item to that record.

## Agent Runtime

- Agents launched: 0
- Agent launch failures: 4
- Failure message: `collab spawn failed: agent thread limit reached`
- Fallback used: yes, Codex local fallback

No agent packet is claimed as real. The packet below is Codex local fallback.

## Codex Fallback Packet

- verdict: PASS
- chosen family: UAE FIU
- family_score_before: 5.8/10
- family_score_after: 6.2/10
- evidence found: 8 UAE FIU source rows; 6 fresh-alert; 1 candidate; 1 remediation; 37 saved FIU source runs; 4 queued FIU alerts; 1 existing FIU canonical record before this sprint.
- files inspected: `product/regradar/sources.json`, `product/regradar/data/source_runs/source_runs.jsonl`, `product/regradar/data/alert_queue/`, `product/regradar/evidence/`, `tools/generate_canonical_evidence.py`, `product/regradar/reports/verified_monitoring_digest_latest.md`.
- commands run: clean gate validators, canonical evidence dry-run/write, canonical validator, digest generator/validator, risk brief gate check.
- methods attempted: family selection, source row audit, source run audit, alert queue audit, canonical evidence dry-run, single-run canonical evidence write, alert evidence link, digest regeneration, risk gate check.
- blockers found: FIU circulars remain candidate/held; FIU homepage remains remediation; new typology evidence is pending review and not brief-input eligible.
- unsafe methods rejected: broad crawling, bypassing access controls, activating `AE-uaefiu-circulars` from old/no-save evidence, claiming complete FIU coverage, claiming customer-ready evidence-backed delivery.
- safe alternatives remaining: founder/operator review of the new typology evidence; parser review of FIU typology removal diff; proof-backed investigation of public FIU circulars/direct documents.
- exact source IDs inspected: `AE-uae-financial-intelligence-unit-uaefiu`, `AE-uaefiu-circulars`, `AE-uaefiu-typology-reports`, `AE-uaefiu-aml-cft-laws`, `AE-uaefiu-publications-hub`, `AE-uaefiu-annual-reports`, `AE-uaefiu-press-releases`, `AE-uaefiu-system-guides`.
- exact source IDs changed: none.
- exact source IDs held: all UAE FIU source rows; no monitoring mode was strengthened.
- customer claim impact: selected UAE FIU publications/typology monitoring is a little more defensible for an operator demo; FIU circulars and complete FIU coverage remain forbidden claims.
- prompt for next agent: Evidence Trail should verify the new typology record, then Risk + Brief Pipeline should keep it blocked until human review approves the exact hash.
- stop/continue recommendation: continue with founder review and parser review before using this item in any pilot brief.

## Current Source Rows

| Source ID | Mode | Status | Alert eligible | Monitor status | Baseline | Proof/hash | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-uae-financial-intelligence-unit-uaefiu` | remediation | remediation | false | none | none | no | Held; homepage remains too shallow/remediation. |
| `AE-uaefiu-circulars` | candidate | active | false | none | none | no | Held; do not claim circulars monitored. |
| `AE-uaefiu-typology-reports` | fresh_alert | active | true | MONITOR_OK | 5/2 | yes | Used for new canonical evidence record. |
| `AE-uaefiu-aml-cft-laws` | fresh_alert | active | true | MONITOR_OK | 3/2 | yes | Held unchanged. |
| `AE-uaefiu-publications-hub` | fresh_alert | active | true | MONITOR_OK | 3/2 | yes | Held; parser/noise caution remains. |
| `AE-uaefiu-annual-reports` | fresh_alert | active | true | MONITOR_OK | 2/2 | yes | Held unchanged. |
| `AE-uaefiu-press-releases` | fresh_alert | active | true | MONITOR_OK | 2/2 | yes | Held unchanged. |
| `AE-uaefiu-system-guides` | fresh_alert | active | true | MONITOR_OK | 2/2 | yes | Existing canonical evidence remains pending. |

## Saved Source Runs

- UAE FIU saved source runs inspected: 37
- Key eligible run used: `AE-uaefiu-typology-reports` / `intake-20260619T150224Z`
- Run status: `CHANGED`
- Extraction quality: `GOOD`
- Normalized hash: `808058c1873dd85c459bd6313bd9c5b7f281fc6d4e58c1a657a74c3b496de632`
- Diff summary in digest: `0 added, 1 removed, 0 changed chunks; 99 unchanged.`

## Queued Alerts

| Alert | Source ID | Run ID | Evidence link after sprint | Delivery |
| --- | --- | --- | --- | --- |
| `20260611T223303-AE-uae-financial-intelligence-unit-uaefiu-AE-20260.json` | `AE-uae-financial-intelligence-unit-uaefiu` | `AE-20260611T222827Z-db5a1dea` | none | blocked |
| `20260615T173740-AE-uaefiu-typology-reports-intake-2-6f97.json` | `AE-uaefiu-typology-reports` | `intake-20260615T173740Z` | none | blocked |
| `20260619T150224-AE-uaefiu-typology-reports-intake-2-d3a0.json` | `AE-uaefiu-typology-reports` | `intake-20260619T150224Z` | `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z` | blocked |
| `20260619T150259-AE-uaefiu-publications-hub-intake-2-e968.json` | `AE-uaefiu-publications-hub` | `intake-20260619T150259Z` | none | blocked |

## Canonical Evidence

Before this sprint:

- `evr_AE-uaefiu-system-guides_intake-20260620T102113Z`
- Status: pending
- Latest external review: none
- Brief eligibility: blocked

Created in this sprint:

- Record ID: `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`
- Path: `product/regradar/evidence/uae-fiu/AE-uaefiu-typology-reports/intake-20260619T150224Z/evidence-record.json`
- Record status: complete
- Run status: CHANGED
- Integrity: VERIFIED
- Hash verified: true
- Current hash: `sha256:808058c1873dd85c459bd6313bd9c5b7f281fc6d4e58c1a657a74c3b496de632`
- Review status: pending
- Latest external review: none
- Brief eligibility: blocked, as expected

Risk gate result:

```text
eligible=False
blocked_reason=Canonical evidence record review_status must be approved or not_required before customer brief use; got 'pending'.
```

## Family Readiness

Score before: 5.8/10.

Score after: 6.2/10.

Why it improved:

- UAE FIU now has a high-value typology-report alert linked to a complete,
  hash-verifiable canonical evidence record.
- The digest now reports 2 canonical evidence linked alerts overall, up from 1.
- The new linked alert remains blocked until human review, so the improvement
  strengthens evidence readiness without weakening delivery gates.

What still blocks 7/10:

- `AE-uaefiu-circulars` remains candidate/held.
- The FIU homepage remains remediation.
- The new typology evidence is pending review.
- Parser/noise review is still needed before interpreting the removal as a
  regulatory change.

What blocks 8/10:

- No founder-approved UAE FIU evidence-backed brief cycle exists.
- Most FIU queued alerts still lack canonical evidence.
- Complete FIU family coverage is not proven and must not be claimed.

What cannot be fixed in code alone:

- Buyer trust from a real MLRO/design partner.
- Official confirmation that the FIU website exposes every circular/notice in a
  stable public endpoint.
- Legal review of any customer-facing interpretation.

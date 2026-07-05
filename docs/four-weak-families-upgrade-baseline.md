# Four Weak UAE Families Upgrade Baseline

Date: 2026-06-21

Scope: ADGM/FSRA, DIFC, UAE FIU, and SCA. This is an operator source-readiness artifact, not a customer coverage claim.

## Agent Runtime

- Agents launched: 0
- Agent failures: 1
- Exact failure: `collab spawn failed: agent thread limit reached`
- Fallback used: yes, Codex local fallback

## Baseline Table

| Family | Score before | Fresh-alert before | Evidence-linked alerts before | Canonical records before | Main blocker | Best upgrade path | Safe claim | Forbidden claim |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| ADGM/FSRA | 6.8 | 10 | 2 | 2 | Three candidate rows unresolved | Resolve a candidate only if proof/baseline/MONITOR_OK pass; otherwise add evidence/linkage | Selected ADGM/FSRA rulebook/guidance/circular monitoring | Complete ADGM/FSRA coverage |
| DIFC | 6.5 | 10 | 1 | 1 | Legal Database listing not fresh-alert proven | Activate official Legal Database listing only if proof/baseline/MONITOR_OK pass | Selected DIFC laws/data-protection/legal notice monitoring | Complete DIFC legal database coverage |
| UAE FIU | 6.3 | 6 | 1 | 2 | Circulars candidate resolves to general publications index | Review typology/system-guide evidence; do not claim circulars without a distinct official endpoint | Selected FIU publications/typologies/system guides | UAE FIU circulars monitored |
| SCA | 5.8 | 5 | 1 | 3 | SCA AML/CFT parser/noise warning and weak direct endpoint depth | Activate direct regulations listing only if proof/baseline/MONITOR_OK pass; keep root portal unclaimed | Selected SCA direct endpoints only | SCA root portal monitoring or full SCA coverage |

## Source Truth Before This Pass

- Enabled UAE source records: 246
- Fresh-alert eligible: 177
- Evidence-library only: 61
- Candidate: 5
- Remediation: 3
- Canonical evidence records: 25
- Verified monitoring digest linked alerts: 10
- Customer delivery: false

## No-Fake Improvement Rules

- No score increase for no-save preview only.
- No score increase for report-only changes.
- No fresh-alert activation without proof path, normalized hash, repeat baseline, and monitor validation.
- No broad family claim even when one selected source improves.

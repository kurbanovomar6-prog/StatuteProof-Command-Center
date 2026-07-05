# Full UAE Source Family Upgrade Baseline

Date: 2026-06-21

This baseline records the state before the full weak-family upgrade pass. It is
an operator artifact, not a customer coverage claim.

## Runtime Truth

- Worktree clean before start: no.
- Agent launch result: failed. Four second-method fresh-agent launches returned
  `collab spawn failed: agent thread limit reached`; Codex continued as local
  fallback.
- Enabled UAE source records: 241.
- Fresh-alert eligible: 172.
- Evidence-library only: 61.
- Candidate: 5.
- Remediation: 3.
- Canonical evidence records before this pass: 13.
- Evidence-linked queued alerts before this pass: 3.
- Customer delivery: false.

## Baseline Table

| Family | Before | Fresh-alert | Evidence-linked alerts | Canonical records | Main blocker | Best next upgrade | Safe claim | Forbidden claim |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| DFSA | 6.9 | 16 | 3 | 4 | Several high-signal alerts still lacked canonical evidence and review. | Add evidence links for consultation and enforcement alerts, then founder-review. | Selected DFSA rulebook, AML, consultation, enforcement monitoring. | Complete DFSA coverage. |
| UAE FIU | 6.3 | 6 | 1 | 2 | FIU circulars/notices remain candidate/held; evidence remains pending review. | Founder-review typology/system-guide evidence; only reopen circulars if new official endpoint appears. | Selected FIU publications, typologies, AML/CFT laws, and system guides. | FIU circulars monitored or complete FIU coverage. |
| DIFC | 6.0 | 10 | 0 | 0 | DIFC had selected source coverage but no canonical evidence-linked alert. | Add canonical evidence for data-protection regulation alert. | Selected DIFC laws/data-protection/legal notice monitoring. | Complete DIFC legal database coverage. |
| ADGM/FSRA | 6.0 | 10 | 0 | 0 | ADGM/FSRA had relevant alerts but no canonical evidence-linked proof examples; candidates unresolved. | Add canonical evidence for financial-crime and rulebook alerts; keep candidates scoped. | Selected ADGM/FSRA rulebook, consultation, enforcement, circular monitoring. | Complete ADGM/FSRA coverage. |
| SCA | 5.2 | 5 | 1 | 2 | SCA AML/CFT parser review remains unresolved; direct endpoints are narrow. | Add canonical evidence for circulars/rules/procedures alert and keep AML/CFT parser warning visible. | Selected SCA direct endpoints only. | SCA root portal monitoring or full SCA coverage. |
| MoF | 4.0 | 3 | 0 | 3 | Thin source family; no matching fresh-alert queue item for current canonical records. | Founder-review existing MoF evidence or add a proof-backed official listing source if found. | Three selected MoF official sources plus evidence-library homepage. | Broad MoF coverage. |
| MoJ/Gazette | 1.0 | 0 | 0 | 0 | Gazette/e-Laws remain access/remediation gaps. | Find safe official public mirror/feed/API or keep blocked. | Disclosed gap only. | UAE legislation/gazette monitoring readiness. |


# Weak UAE Family Upgrade Baseline

Date: 2026-06-21

This is an operator baseline for the weak-family upgrade sprint. It is not a
customer coverage claim.

## Clean Gate

- Worktree clean before start: no.
- Existing dirty files were present before this sprint, including Telegram,
  source-truth, report, digest, and 8/10 readiness files.
- Agent council launch: failed. Four fresh-agent launches returned
  `agent thread limit reached`; Codex continued as local fallback.
- Preflight before implementation: passed.

## Baseline Family Table

| Family | Score before | Main blocker | Best upgrade path | Safe claim | Forbidden claim |
| --- | ---: | --- | --- | --- | --- |
| DFSA | 6.5 | DFSA has 9 queued alerts and only one prior canonical evidence example; high-signal alerts were not evidence-linked. | Generate canonical evidence for a high-signal MLRO/financial-crime alert and link the exact matching alert. | Selected DFSA rulebook, AML, consultation, enforcement monitoring. | Complete DFSA coverage. |
| UAE FIU | 6.3 | FIU circulars/notices remain candidate/held; typology evidence is linked but pending review. | Founder/operator review of existing typology evidence; do not reopen circulars unless a new official endpoint appears. | Selected FIU publications, typologies, AML/CFT laws, and system guides. | UAE FIU circulars monitored or complete FIU coverage. |
| DIFC | 6.0 | Selected sources exist, but complete DIFC legal database/listing coverage is not proven. | Proof-backed legal/listing adapter only if safe official extraction and repeat baseline pass. | Selected DIFC laws/data-protection/legal notice monitoring. | Complete DIFC legal database coverage. |
| ADGM/FSRA | 6.0 | Candidate rows remain unresolved; several alerts lack canonical evidence links. | Resolve candidates or generate canonical evidence for ADGM circular/guidance/rulebook alerts. | Selected ADGM/FSRA rulebook, consultation, enforcement, circular monitoring. | Complete ADGM/FSRA coverage. |
| SCA | 5.2 | AML/CFT large diff remains parser-review risk; direct endpoints are narrow. | Classify SCA AML/CFT diff as material/noise/reflow and improve direct endpoint depth. | Selected SCA direct endpoints only. | SCA root portal monitoring or full SCA coverage. |
| MoF | 4.0 | Thin family with three fresh-alert sources and one evidence-library homepage. | Add proof-backed official MoF document/listing source or canonical evidence for an existing source. | Three selected MoF official sources plus evidence-library homepage. | Broad MoF coverage. |
| MoJ/Gazette | 1.0 | Gazette/e-Laws remain access/remediation gaps. | Only safe official mirror/feed/API/document library research; otherwise keep disclosed gap. | Disclosed gap only. | UAE legislation/gazette monitoring readiness. |

## Chosen Family

Chosen family: DFSA.

Reason:

- Buyer relevance is high for DFSA compliance teams and MLROs.
- `AE-dfsa-financial-crime-mlro-letters` already had a safe official public URL,
  GOOD adapter extraction, repeat baseline, proof artifacts, normalized hash,
  and `MONITOR_OK`.
- A matching queued alert existed for the exact `source_id` and `run_id`.
- The dry-run canonical evidence generator returned `would_create=1`.
- This path improves evidence readiness without adding a fake source, changing
  source counts, or claiming complete DFSA coverage.

Rejected first for this sprint:

- UAE FIU: circulars were already held; no new official endpoint was found in
  this sprint.
- DIFC: likely valuable, but a safer immediate proof-backed gain existed in DFSA.
- ADGM/FSRA: good next target, but candidates need more parser/source review.
- SCA: parser classification is important, but the DFSA evidence-link path was
  lower risk.
- MoF: weaker commercial priority for MLRO outreach.
- MoJ/Gazette: still unsafe unless a public official alternative is found.


# Agent Council Orchestration Plan

Date: 2026-06-19

## Current Agent Roster

StatuteProof already has ten core roles in `AGENTS.md`, `.claude/agents/`, and `agents/`:

1. Chief of Staff
2. Product Manager
3. Code Architect
4. QA / Critic
5. Legal Language
6. Source Monitor
7. Evidence Trail
8. Risk + Brief Pipeline
9. ICP Lead Research
10. Outreach Writer

These remain the core council roles. New worker roles may be added as implementation helpers, but they do not replace Source Monitor, Evidence Trail, QA, Legal Language, or Product Manager gates.

## Deprecated Rule

The old "10 agents maximum" rule is deprecated for orchestration planning. It should no longer block adding bounded worker roles such as Adapter Worker, Validator Worker, Test Fixture Worker, Source Discovery Worker, Security/Tooling Auditor, or Browser/Access Investigator.

## Rules That Remain Mandatory

- No customer-facing copy is finalized without Legal Language review.
- No delivery or commit bypasses QA / Critic.
- No brief is drafted without complete evidence records.
- Evidence Trail blocks incomplete proof, hash, baseline, or evidence-record chains.
- Source Monitor owns public/official/access status and source-health blockers.
- Product Manager decides sellability after QA and Legal review.
- Outreach Writer cannot send or finalize outreach before Product, Legal, and ICP approval.
- No agent may claim legal advice, complete UAE coverage, guaranteed compliance, perfect parsing, regulator certification, all-source coverage, or "never miss updates."

## Current Project Blockers

Current truth from the June 19 fresh-signal reports:

- 238 enabled UAE sources.
- 168 fresh-alert eligible sources.
- 61 evidence-library sources.
- 6 candidate sources.
- 3 remediation-mode sources.

The council must treat these as source-state facts, not marketing claims.

Known blockers:

- Customer-facing copy and some UI data still risk implying broader monitoring than the fresh-alert model supports.
- Existing validators check registry fields more than complete run/evidence history.
- Production canonical `evidence-record.json` / `evidence_record_status=complete` is not yet established for customer briefs.
- Several source families remain below Strong Fresh Signal: VARA, DFSA, DIFC, ADGM/FSRA, UAE FIU, SCA, MoJ/Gazette, and MoF.
- Weak-family growth depends on specific adapters and public endpoint research, not more generic URLs.

## Desired Council Workflow

1. Chief of Staff creates or accepts a task in the shared task board.
2. Source Monitor defines the official-source scope and access/fetch blocker.
3. Code Architect designs or implements the smallest safe technical change.
4. Evidence Trail verifies proof paths, normalized paths, hashes, baselines, and complete evidence records.
5. QA / Critic red-teams source state, tests, validators, and claim risk.
6. Legal Language reviews any customer-facing wording or status label.
7. Product Manager decides whether the task supports a pilot, source family, or sales claim.
8. Outreach Writer acts only after ICP, Product, and Legal approve safe evidence-backed claims.

Agents may propose next tasks to one another, but task status changes must be recorded in the task board and must respect blocking gates.

## Approval Gates

- Source activation gate: Source Monitor -> Code Architect -> Evidence Trail -> QA -> Legal if customer-facing -> Product if sellability changes.
- Evidence/brief gate: Evidence Trail -> Risk + Brief Pipeline -> QA -> Legal -> Product.
- Customer copy gate: Product -> Legal -> QA.
- Outreach gate: ICP Lead Research -> Product -> Legal -> Outreach Writer -> QA.
- Tooling gate: Security/Tooling Auditor -> Code Architect -> QA -> Chief of Staff.

## Safety Boundaries

- No hidden automation.
- No broad agent-pack import without review.
- No daemon, hooks, MCP memory auto-sync, or full Ruflo install without explicit founder approval.
- No source activation from no-save tests.
- No evidence-library or remediation source counted as fresh-alert monitoring.
- No private portal, login, CAPTCHA, paywall, or access-control bypass.
- No unrelated staging.

## Ruflo / Tooling Intake Policy

Ruflo can be used as an inspiration source and possibly a future orchestration layer, but full mode is not approved now. The safe path is:

- Audit external tooling in a temp directory.
- Review install scripts, hooks, MCP settings, package scripts, and prompt files.
- Copy only selected role/workflow ideas after attribution and safety review.
- Prefer existing Codex subagents and this task board before enabling Ruflo daemon/hooks/MCP memory.

## What Will Not Be Automated

- Legal advice.
- Compliance certification.
- Complete UAE coverage claims.
- Source activation without proof/baseline/MONITOR_OK.
- Customer outreach sending.
- Cloudflare/DigitalOcean deployment.
- Secret handling.
- Access-control bypass.

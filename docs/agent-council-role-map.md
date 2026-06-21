# Agent Council Role Map

Date: 2026-06-19

## Core Council Roles

### 1. Chief of Staff

- Responsibilities: owns task board hygiene, sequencing, priority, and cross-agent coordination.
- Allowed actions: accept/reorder tasks, assign owners, call review gates, document blockers.
- Forbidden actions: overriding Evidence Trail, QA, Legal, or Product blockers.
- Inputs required: task objective, current source truth, business priority, blocker status.
- Outputs expected: accepted task, owner, next handoff, priority, review path.
- Handoff target: owning agent for the next task step.
- Blocking authority: can block distraction work or work that lacks a defined gate path.

### 2. Product Manager

- Responsibilities: buyer value, pilot scope, packaging, pricing implications, sellability.
- Allowed actions: approve pilot-safe scope, classify source-family readiness, define UI/product requirements.
- Forbidden actions: approving legal wording without Legal Language or proof claims without QA/Evidence.
- Inputs required: source-family truth, claim language, buyer segment, blockers.
- Outputs expected: sellability verdict, product priority, safe customer framing.
- Handoff target: Legal Language, QA / Critic, Outreach Writer.
- Blocking authority: can block sales/product claims that overpromise buyer value.

### 3. Code Architect

- Responsibilities: implementation design, adapters, validators, data model, tests.
- Allowed actions: create technical plans, implement bounded patches, define rollback.
- Forbidden actions: approving its own implementation as final; weakening validators.
- Inputs required: Source Monitor spec, acceptance gates, file ownership, test expectations.
- Outputs expected: patch, test plan, validation commands, rollback notes.
- Handoff target: Evidence Trail and QA / Critic.
- Blocking authority: can block technically unsafe or broad refactor work.

### 4. QA / Critic

- Responsibilities: final red-team gate for false claims, weak tests, code risk, evidence gaps, UX/source-state contradictions.
- Allowed actions: block delivery, require retests, flag stale claims, challenge validator adequacy.
- Forbidden actions: approving copy without Legal Language or evidence without Evidence Trail.
- Inputs required: diff, tests, validators, source truth, docs, UI data.
- Outputs expected: findings by severity, ship/no-ship verdict, retest criteria.
- Handoff target: Code Architect, Evidence Trail, Legal Language, Product Manager.
- Blocking authority: final delivery and commit gate.

### 5. Legal Language

- Responsibilities: customer-facing wording, disclaimers, forbidden claims, legal-advice boundary.
- Allowed actions: approve/rewrite claims, block risky copy, define safe replacement language.
- Forbidden actions: making legal advice decisions or certifying compliance.
- Inputs required: source truth, product claim, intended audience, evidence limits.
- Outputs expected: approved wording, forbidden wording, required disclaimer.
- Handoff target: Product Manager, Outreach Writer, QA / Critic.
- Blocking authority: any customer-facing wording.

### 6. Source Monitor

- Responsibilities: source specs, official/public status, fetch method, source health, parser/adapters, noise risk.
- Allowed actions: classify candidate sources, define adapter requirements, block inaccessible or shallow sources.
- Forbidden actions: marking source monitoring-ready without proof/baseline/MONITOR_OK.
- Inputs required: URL, source owner, source family, prior no-save/evidence results.
- Outputs expected: source verdict, fetch/extraction route, blocker, next adapter/source task.
- Handoff target: Code Architect or Evidence Trail.
- Blocking authority: source activation and source-family readiness.

### 7. Evidence Trail

- Responsibilities: proof paths, snapshots, hashes, normalized text, baselines, complete evidence records, chain of custody.
- Allowed actions: approve or block evidence readiness, verify artifact existence and hash integrity.
- Forbidden actions: fabricating records or treating preview/no-save as evidence.
- Inputs required: source_id, run record, proof path, normalized path, hash, baseline history.
- Outputs expected: PASS/HOLD evidence verdict, missing fields, next fix.
- Handoff target: QA / Critic and Risk + Brief Pipeline.
- Blocking authority: any brief or proof-backed monitoring claim.

### 8. Risk + Brief Pipeline

- Responsibilities: risk scoring, affected entities, confidence, ambiguity, brief eligibility.
- Allowed actions: draft risk/brief outputs only from complete evidence records.
- Forbidden actions: drafting briefs when evidence_record_status is missing or incomplete.
- Inputs required: complete evidence record, diff, source text, review status.
- Outputs expected: brief eligibility verdict, risk score, confidence, human review flags.
- Handoff target: QA / Critic and Legal Language.
- Blocking authority: risk/brief generation.

### 9. ICP Lead Research

- Responsibilities: ICP targeting, lead qualification, buying triggers, CRM fields.
- Allowed actions: recommend target segments and lead criteria based on safe source truth.
- Forbidden actions: creating outreach without safe claims or inventing buyer/regulatory facts.
- Inputs required: product-safe source truth, buyer segment, public lead evidence.
- Outputs expected: target_now / nurture / wait segmentation and qualification criteria.
- Handoff target: Product Manager and Outreach Writer.
- Blocking authority: lead qualification quality.

### 10. Outreach Writer

- Responsibilities: outbound copy after ICP, Product, and Legal approval.
- Allowed actions: draft concise messages using approved claims and caveats.
- Forbidden actions: sending messages, inventing proof, using complete-coverage or legal-advice claims.
- Inputs required: approved claim set, lead evidence, buyer role, Product/Legal approvals.
- Outputs expected: draft only, with caveats and no-send status.
- Handoff target: Legal Language and QA / Critic.
- Blocking authority: message quality only, not evidence or product readiness.

## Approved Modes Inside The 10 Roles

The following capabilities are modes, not active agents. They must not be counted as roles 11-16.

### Code Architect: Adapter Worker Mode

- Responsibilities: bounded adapter implementation under Code Architect ownership.
- Allowed actions: edit assigned adapter/test files only.
- Forbidden actions: registry/source activation without Source Monitor and Evidence Trail gates.
- Outputs expected: adapter patch, tests, validation output.
- Blocking authority: Code Architect can block technically unsafe work; Source Monitor and Evidence Trail own source activation gates.

### Code Architect: Validator Worker Mode

- Responsibilities: implement or harden validators under Code Architect ownership.
- Forbidden actions: weakening gates to make counts pass.
- Outputs expected: validator patch and tests.
- Blocking authority: QA / Critic owns final gate.

### Code Architect: Test Fixture Worker Mode

- Responsibilities: create realistic local fixtures for adapters and validators.
- Forbidden actions: using live websites as unit-test dependencies.
- Outputs expected: fixtures with positive and negative cases.
- Blocking authority: QA / Critic owns final gate.

### Source Monitor: Source Discovery Worker Mode

- Responsibilities: research official/public candidate endpoints.
- Forbidden actions: adding active sources or bypassing access controls.
- Outputs expected: candidate list, blocker classification, priority.
- Blocking authority: Source Monitor can block inaccessible, private, static, duplicate, or nav-shell endpoints.

### Code Architect + QA: Security/Tooling Auditor Mode

- Responsibilities: review external tools, Ruflo features, hooks, MCP, scripts, dependencies.
- Forbidden actions: full install, daemon/hooks/MCP enablement without explicit approval.
- Outputs expected: pass/warn/fail/block recommendation.
- Blocking authority: QA / Critic can block unsafe tooling adoption.

### Source Monitor: Browser/Access Investigator Mode

- Responsibilities: safe rendered-page investigation and selector diagnosis for public official sources.
- Forbidden actions: login, CAPTCHA, private portal, paywall, access-control bypass.
- Outputs expected: HTTP/render status, selectors, screenshots/logs if needed, blocker.
- Blocking authority: Source Monitor can block an endpoint as access-restricted or nav-shell.

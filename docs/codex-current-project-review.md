# Codex Current StatuteProof Project Review

## 1. Executive Summary
StatuteProof today is a real UAE regulatory monitoring workspace, not just a planning folder. The strongest implementation is in `product/regradar/`: it has official-source fetching, text extraction, normalization, SHA-256 hashing, old-vs-new comparison, JSONL source-run history, snapshots, proof files, diff artifacts, alert review, weekly brief rendering, auth/profile persistence, and a React frontend. It is not yet customer-facing ready because the dashboard still uses significant mock data, current enabled source count and docs disagree, and the next proof milestone is a fresh current evidence readiness pass.

## 2. Workspace Map
- Command Center root: operating layer for plans, agents, skills, workflows, docs, prompts, examples, checklists, and tools.
- `product/`: implementation layer, including older app/deployment files plus the newer `product/regradar` product.
- `agents/`: human-readable 10-agent roster. No 11th active agent added.
- `skills/`: existing Claude-style review skills.
- `.claude/`: Claude agents and skills.
- `.agents/skills/`: Codex-native repo skills added by this pass.
- `workflows/`: source spec, evidence dry run, monitoring-to-brief, outreach, landing review, council review.
- `docs/`: evidence, source monitoring, legal safety, risk, migration, GTM, review reports.
- `examples/`: sample evidence/brief/outreach artifacts.
- `tools/`: workspace validators and packaging scripts.

## 3. Product Code Reality
- Real parser exists: yes, via `app/scraper.py`, `app/extractors.py`, `app/parser.py`, document/PDF extraction helpers, and adapters.
- Real normalizer exists: yes, `app/text_normalization.py`.
- Real hashing exists: yes, `stable_content_hash`, `stable_normalized_hash`, raw SHA-256 hashes.
- Real diff exists: yes, `app/diff.py` and durable `app/chunk_diff.py` artifacts.
- Real evidence records exist: yes, JSONL source runs, snapshots, proof.json, diff files.
- Real risk scoring exists: yes, deterministic keyword classifier in `app/risk.py`.
- Real brief generation exists: yes, `app/ai_brief.py` with fallback and `app/weekly_brief.py` for reviewed weekly briefs.
- Real frontend exists: yes, React/Vite in `product/regradar/web`.
- Real dashboard exists: partly. App shell/pages exist, but source coverage, alert previews, and reports are heavily sample-driven.
- Registration/login exists: yes, backend auth helpers and frontend auth pages exist.

## 4. What Is Real
- 150 source entries in `product/regradar/sources.json`.
- 13 enabled UAE sources in current `sources.json`.
- 176 JSONL source run records in `data/source_runs/source_runs.jsonl`.
- 2026-06-11 source snapshots for many UAE source IDs.
- Proof artifacts for recent source runs.
- Diff artifacts for changed source runs.
- Alert queue and human review workflow.
- Weekly brief renderer with full disclaimer and QA/legal gates.
- Auth/session/profile implementation using SQLite.
- React app with landing, login, register, onboarding, dashboard shell, sources, alerts, reports, integrations, and settings pages.

## 5. What Is Mock / Sample / Planned
- `product/regradar/web/src/data/appMockData.js` powers much of the dashboard experience.
- Landing evidence/demo section uses SAMPLE / FAKE data.
- Some docs still state 9 or 16 enabled sources while current file shows 13 enabled UAE sources.
- Dashboard evidence cards are not yet clearly backed by live `source_runs.jsonl` APIs.
- Audit binder/export is planned, not implemented as a customer workflow.
- Custom source monitoring exists as source-test/add-source pieces, but needs a safe product spec and UX gating.

## 6. Current Product Readiness
- Parsing: 7/10.
- Evidence trail: 7/10.
- Risk brief: 6.5/10.
- Dashboard: 5/10.
- Website: 6.5/10.
- Onboarding/auth: 6.5/10.
- Customer-facing readiness: 4.5/10.

## 7. Biggest Blockers
- CRITICAL: Dashboard still uses sample/mock data for core source, alert, and report states.
- CRITICAL: No fresh current evidence readiness report for the current enabled UAE source pack.
- HIGH: Current enabled source count is 13, while prior docs/user expectation mention 16 and older docs mention 9.
- HIGH: Deployment path is split between older product root and `product/regradar` API/frontend.
- HIGH: Evidence spec and runtime artifacts do not fully match.
- MEDIUM: `SOURCE_STRUCTURE_CHANGED` is specified but not implemented.
- MEDIUM: Generated artifacts, DBs, node_modules, dist, and zip file exist inside the workspace.
- LOW: Some legacy RegRadar/multi-market language remains.

## 8. What Not To Build Yet
- Full dashboard rewrite before evidence readiness.
- All regulators or all markets.
- Complex n8n/runtime automation.
- Legal advice engine.
- Auto-send customer briefs.
- New agent framework or 11th agent.
- Billing before pilot proof.

## 9. Immediate Next Step
Run a current 13-enabled-source evidence readiness pass without customer delivery, then reconcile whether the source pack should be 13 or 16 before changing website claims.

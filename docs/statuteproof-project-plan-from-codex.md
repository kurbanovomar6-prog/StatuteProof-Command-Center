# StatuteProof Project Plan

## 1. Product Vision
Build official-source UAE regulatory monitoring for MLROs, CCOs, compliance managers, and regulated fintech/VASP teams. The product should fetch official sources, normalize content, hash it, compare old and new versions, preserve evidence, show diffs, score risk, and generate human-reviewed compliance briefs without giving legal advice.

## 2. Current MVP Goal
The next milestone is evidence readiness for the current UAE source pack: a clean current source readiness pass, a first clean evidence dry run, a sample brief backed by proof, and a proof-first homepage/dashboard that shows evidence before claims.

## 3. 7-Day Plan
Day 1: Evidence readiness pass. Files: `sources.json`, `source_runs.jsonl`, snapshots. Output: current source status table. Success: each enabled UAE source has latest status, proof path, limitation. Responsible agent: Source Monitor + Evidence Trail.

Day 2: Fix evidence gaps only. Files: `source_runs.py`, `proof.py`, source-specific adapters if needed. Output: one clean proof artifact for each passable source. Success: no FAILED source is presented as monitored. Responsible agent: Evidence Trail + Code Architect.

Day 3: One safe current evidence dry run. Files: one approved source, snapshots, report. Output: dry-run report. Success: FIRST_SEEN/UNCHANGED/CHANGED classified correctly, no customer delivery. Responsible agent: Source Monitor + QA.

Day 4: Sample brief from approved evidence. Files: `ai_brief.py`, `weekly_brief.py`, alert review data. Output: SAMPLE / DEMO brief. Success: legal-safe, human-reviewed, evidence linked. Responsible agent: Risk + Brief Pipeline + Legal Language.

Day 5: Proof-first homepage upgrade. Files: React homepage components. Output: first viewport shows source proof/audit trail. Success: MLRO sees what was checked, when, hash, diff, limitation, CTA. Responsible agent: Product Manager + Legal Language.

Day 6: Dashboard live evidence spec. Files: API/dashboard components. Output: implementation spec or narrow endpoint. Success: dashboard can show latest source runs without mock ambiguity. Responsible agent: Code Architect.

Day 7: Pilot readiness review. Files: docs, reports, frontend screenshots. Output: GO/HOLD decision for manual MVP. Success: next sales action is based on evidence, not aspiration. Responsible agent: QA / Critic + Chief of Staff.

## 4. 30-Day Plan
Week 1: Prove current UAE source pack evidence readiness and produce one clean dry-run report.
Week 2: Connect homepage/dashboard to current evidence status and remove confusing mock claims.
Week 3: Implement safe custom source monitoring flow for public official URLs and source readiness review offer.
Week 4: Prepare founding pilot package: source coverage table, sample brief, evidence bundle, legal-safe website, and manual review workflow.

## 5. Core Product Modules
- Source registry: `sources.json`, enabled/status/category/jurisdiction/source IDs.
- Parser/fetcher: requests + Playwright + adapters + PDF/document extraction.
- Normalization: conservative regulatory-text cleanup.
- Hashing: SHA-256 of normalized/stable text plus raw hash.
- Diff: paragraph and chunk-level old-vs-new comparison.
- Evidence record: JSONL run, snapshots, metadata, proof block, diff paths.
- Risk classifier: deterministic HIGH/MEDIUM/LOW keyword classifier.
- Brief generator: Claude Haiku optional with fallback and human-review gate.
- Dashboard: source coverage, alerts, briefs, settings; currently partly mock.
- Custom source monitoring: public URL test, source readiness, human approval.
- User accounts: registration/login/session/profile in SQLite.
- Source readiness review: lead magnet and pilot qualification workflow.
- Export/audit binder: planned evidence bundle export.

## 6. Website/App Plan
Homepage: proof-first hero with source checked, timestamp, hash, diff, limitation, CTA.
Register: create pilot workspace, not instant production claim.
Login: existing flow retained.
Onboarding: collect profile, markets, sources, alert threshold.
Dashboard: latest source run status from real evidence.
Sources page: enabled sources, extraction quality, limitations, last checked.
Add custom source: public URL safety-gated source test.
Evidence record page: raw/normalized hash, official URL, snapshots, proof quality.
Diff viewer: durable diff from latest CHANGED run.
Briefs page: human-reviewed briefs only.
Settings: profile, delivery preferences, Telegram pairing.
Billing: later, after pilot validation.

## 7. Revenue Plan
Pilot-first: offer Source Readiness Review, then founding pilot. Initial packs: UAE VASP pack and compliance consultant pack. Sell proof of monitoring and audit trail, not legal conclusions.

## 8. Go-To-Market Plan
Target MLRO/CCO at VARA VASPs, UAE fintech/payment firms, DFSA/ADGM firms, and compliance consultants. Outreach should offer a source readiness review for their current manual watchlist and show an example evidence card.

## 9. What Must Be Proven Before Selling
- Current source readiness report.
- Clean evidence record from an official source.
- Sample brief clearly linked to evidence.
- Legal-safe language and disclaimers.
- Screenshot/demo showing proof and diff.
- Source coverage table with limitations.

## 10. Next Coding Task
Add a read-only evidence status endpoint that returns latest enabled UAE source runs from `source_runs.jsonl` for dashboard display, after the evidence readiness pass defines the exact fields.

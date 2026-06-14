# Independent StatuteProof Project Review

Date: 2026-06-11
Scope: `/Users/kurbnovomar/StatuteProof-Command-Center`, with actual product code under `product/`.
Method: read-only project audit plus creation of this report. No live monitoring, customer delivery, dependency install, or secret printing was performed.

## 1. Executive Verdict

Overall score: 6.4/10.

Classification: ready for internal dry run.

StatuteProof is a real product workspace with real regulatory monitoring code, source fetching, normalization, hashing, JSONL source-run history, snapshots, proof files, diff artifacts, alert review, weekly brief rendering, auth, profile persistence, and a substantial React frontend. It is not ready for a customer-facing pilot yet. The biggest gap is not "no product"; the biggest gap is proof discipline: the current repo lacks a dated first safe evidence dry-run report, the frontend still relies heavily on sample/mock data, deployment entrypoints are split between an older NiceGUI app and the newer Regradar API/frontend, and the implementation does not fully match the Command Center evidence spec.

## 2. What StatuteProof Is Today

StatuteProof today is a working B2B regulatory-monitoring prototype with two layers:

- A Command Center operating layer: agents, skills, workflows, checklists, legal-safety docs, source-monitoring specs, evidence specs, and GTM docs.
- A product implementation layer: `product/regradar/` contains the main monitoring pipeline, source registry, JSONL run history, snapshots, tests, API server, and React frontend.

The actual implementation is stronger than a slideware MVP. It has real code for fetching pages, extracting text, normalizing content, hashing, comparing runs, writing snapshots, producing proof blocks, creating alert drafts, reviewing alerts, routing previews, and rendering weekly briefs.

It is also uneven. Some docs still describe the old CIS-focused RegRadar product, not UAE StatuteProof. The active frontend is not yet fully wired to live evidence data. The deployment root still points at an older NiceGUI/Celery app. Evidence data exists, but the current Command Center spec and runtime artifact format are not the same.

## 3. Workspace Structure

Command Center root:

- `README.md`, `START_HERE.md`, `CLAUDE.md`, `AGENTS.md`, `TOOL_ROUTER.md`, `STATUTEPROOF_CONTEXT.md` define positioning, safety rules, routing, and the 10-agent operating model.
- `agents/` and `.claude/agents/` define the 10 roles. No 11th active agent was found or created.
- `skills/` contains review skills for outreach, UI, design, conversion, and council workflow.
- `.claude/skills/` contains `evidence-audit`, `risk-brief-review`, and `weekly-founder-plan`.
- `workflows/` contains the manual source spec, evidence dry run, monitoring-to-brief, outreach, landing review, and agent council workflows.
- `docs/` contains source, evidence, risk, legal, outreach, MVP, migration, and design standards.
- `product/` is the implementation layer.

Product structure:

- `product/regradar/app/` is the real monitoring/backend logic.
- `product/regradar/web/` is the React frontend.
- `product/regradar/data/source_runs/source_runs.jsonl` contains 132 run records.
- `product/regradar/data/source_snapshots/` contains raw and normalized snapshots.
- `product/regradar/sources.json` contains 150 source entries, 16 enabled UAE entries.
- `product/regradar/tests/` contains focused tests for normalization, proof/diff, alert review, weekly brief, and relevance.
- `product/` also contains an older deployment/app layer (`main.py`, `entrypoint.sh`, Celery, NiceGUI, root Dockerfile) that is not clearly aligned with the newer React/API product.

## 4. Technical Architecture

Scraper: `product/regradar/app/scraper.py` implements requests-first fetching and Playwright fallback. The current code uses one shared browser per process and creates one isolated context/page per Playwright fetch.

Normalization: `product/regradar/app/text_normalization.py` removes boilerplate, volatile timestamps, duplicate lines, and whitespace noise. It exposes `normalize_for_change_hash()`, `stable_content_hash()`, and `stable_normalized_hash()`.

Hashing: SQLite change detection now uses `stable_content_hash()` consistently between `pipeline.py` and `db.py`. JSONL evidence uses `stable_normalized_hash()` for normalized evidence and `stable_content_hash()` for the secondary content hash.

Diff: `app/diff.py` provides paragraph-level diffs for SQLite pipeline changes. `app/chunk_diff.py` creates durable normalized snapshot diff artifacts for JSONL evidence.

Source runs: `app/source_runs.py` writes JSONL run records and snapshot files. It classifies `FIRST_SEEN`, `UNCHANGED`, `CHANGED`, `FAILED`, and `QUALITY_DROP`. It does not implement `SOURCE_STRUCTURE_CHANGED`.

Proof/evidence: `app/proof.py` builds proof blocks with URL, timestamps, hashes, snapshot paths, diff paths, extraction quality, and a short disclaimer.

Risk classifier: `app/risk.py` is deterministic and keyword-based. It now detects Arabic text and returns `MEDIUM` with manual-review rationale instead of false `LOW`.

AI brief: `app/ai_brief.py` uses Claude Haiku, has thin-content guards, quality checks, retry on weak output, and detects `max_tokens` truncation. `app/ai.py`, used by `pipeline.py`, still does not check `message.stop_reason == "max_tokens"`.

Alert review: `app/alert_review.py` supports human statuses and blocks urgent approval for incomplete proof, low confidence, review risk, incomplete diff, and legislation-source adapter issues.

Frontend: `product/regradar/web/` has a real React landing page, auth/register/login screens, onboarding, dashboard shell, source map, alert previews, integrations, settings, and brief previews. Much of the dashboard data is still sample/mock data.

Deployment: Deployment is confused. Root Docker/Railway points to `product/main.py` and `entrypoint.sh web`, while the modern Regradar frontend expects `python run.py api` on port 5001. This needs a deployment decision before customer use.

## 5. Parsing / Monitoring Reality Check

Real parser exists: yes. Evidence: `app/extractors.py`, `app/parser.py`, `app/scraper.py`, `app/document_extractor.py`.

Real monitoring exists: yes. Evidence: `app/monitor.py`, `app/pipeline.py`, `app/source_readiness.py`, `run.py` commands.

Real snapshots exist: yes. Evidence: `product/regradar/data/source_snapshots/2026-05-30/AE/.../raw.txt` and `normalized.txt`.

Real source runs exist: yes. Evidence: `data/source_runs/source_runs.jsonl` has 132 records.

Real adapters exist: partially. Evidence: `app/adapters/uae_cbuae_rulebook.py` and `app/adapters/uae_fsra_circulars.py`; older CIS adapters also remain.

Dry-run command exists: partially. `run.py` exposes `test-source`, `source-readiness`, `source-history`, and `source-diff`; the workflow says `python3 -m app.pipeline --source ... --dry-run`, but `app.pipeline` is not a CLI in the inspected code. Root docs and actual CLI do not fully match.

Exact file evidence:

- Fetching: `product/regradar/app/scraper.py`
- Normalization: `product/regradar/app/text_normalization.py`
- Hashing: `product/regradar/app/text_normalization.py`, `product/regradar/app/db.py`, `product/regradar/app/source_runs.py`
- Comparison: `product/regradar/app/pipeline.py`, `product/regradar/app/source_runs.py`
- Diff: `product/regradar/app/diff.py`, `product/regradar/app/chunk_diff.py`
- Evidence: `product/regradar/app/proof.py`, `product/regradar/data/source_runs/source_runs.jsonl`
- Review: `product/regradar/app/alert_review.py`

## 6. Evidence Trail Readiness

Score: 7/10.

Strengths:

- JSONL run history exists and is append-oriented.
- Raw and normalized snapshots are preserved for many runs.
- Run IDs and UTC timestamps are stored.
- `raw_hash`, `normalized_hash`, `content_hash`, and PDF hash fields exist.
- Proof files exist for 24 records.
- Diff artifacts exist for changed normalized snapshots.
- `FAILED` is not treated as `UNCHANGED` in `classify_change()`.

Weaknesses:

- JSONL locking protects only the final append, not the whole read-classify-write-artifact transaction. Concurrent workers can still classify against stale previous state.
- Runtime evidence format does not match root `docs/evidence-record-spec.md`: no `evidence-record.json`, no `sha256:` prefix, no `previous.normalized.txt` naming, and `proof.json` has a short disclaimer.
- Only 24 of 132 source runs have `proof_block_path`.
- Only 1 of 132 records has `diff_json_path`, although 18 are `CHANGED`.
- `SOURCE_STRUCTURE_CHANGED` is specified in Command Center docs but not supported in runtime code.
- `product/regradar/regradar.db` exists in the migrated workspace despite migration docs saying live DB files were excluded.

## 7. Risk + Brief Pipeline Readiness

Score: 6.5/10.

The rule-based classifier is deterministic and not in the change-detection path. That is correct. It handles simple English risk signals and now avoids false `LOW` for Arabic content by returning `MEDIUM` and requiring manual review.

The AI brief layer is materially better than a generic prompt. It asks for affected entities, licence scope, obligations, implementation deadline, regulatory body, change type, confidence, review requirement, and monitoring note. It has thin-content guardrails and a quality retry.

The weak point is still reliability. `app/risk.py` remains keyword-based and will over-trigger on source navigation or compliance glossary text if extraction/diff includes boilerplate. `app/ai.py`, the AI wrapper used by the main `pipeline.py`, does not detect `max_tokens` truncation. Brief generation is not yet visibly tied to a complete evidence-record schema in the way the Command Center workflow requires.

The weekly brief renderer is legal-safer: it uses human-approved alerts only, includes a full multi-sentence disclaimer, runs a forbidden-phrase scan, and has a QA gate. This is good enough for internal reviewed outputs, not unattended customer delivery.

## 8. Website / Landing Page Review

Score: 6.5/10.

The landing page is targeted at UAE compliance teams and uses evidence-first language. It clearly mentions official UAE sources, human review, source proof, limitations, and source readiness. The CTA is better than generic SaaS: "Create pilot workspace" and the pricing table includes a free "Source Readiness Review".

Problems:

- The first viewport claim "9 validated UAE financial sources" is too strong unless backed by a live source health page. Actual `sources.json` has 16 enabled AE sources, and frontend data has sample/source-readiness rows.
- The hero mockup includes concrete-looking alerts such as "New licensing requirements detected" without a visible SAMPLE label in the mockup itself.
- The homepage still sells a workspace before it proves the evidence trail with a real source proof example.
- MLRO pain is present, but not sharp enough. The strongest pain is "show me the audit trail for what we checked, when, and what changed"; this should dominate the homepage.

## 9. Dashboard / Product UX Review

Score: 5.5/10.

What exists:

- Source map page with validation request workflow.
- Dashboard shell, sidebar, topbar, onboarding, settings, alerts, integrations, and brief preview pages.
- Login/register flow uses backend auth endpoints.
- Profile persistence exists.
- Telegram pairing and manual preview delivery exist.

What is not ready:

- Source coverage table is sample-driven, not live from `source_runs.jsonl`.
- Evidence record cards are not clearly connected to real proof files.
- Diff viewer is not a first-class dashboard view.
- Risk badges are mostly sample frontend data.
- Weekly brief view is not clearly backed by live approved alert records in the UI.
- Audit binder/export is not present as a user-facing workflow.
- The UI honestly labels many areas as sample/preview, but a customer could still confuse mock dashboard states with production monitoring.

## 10. Legal Safety Review

Unsafe or risky claims found:

- `product/README.md` describes an "Autonomous Regulatory Intelligence Platform" with "all without human intervention." This conflicts with the current human-review positioning.
- The landing hero says "9 validated UAE financial sources" without visible live proof in the same viewport.
- Sample mockup text says "New licensing requirements detected" and "VASP rulebook update detected" without a clear SAMPLE label inside the mockup.
- Some legacy docs discuss broad multi-market coverage and Telegram dispatch in ways that are not the current UAE MLRO wedge.

Replacements:

- Replace "Autonomous Regulatory Intelligence Platform" with "Official-source regulatory monitoring with evidence-backed compliance briefs."
- Replace "all without human intervention" with "with human review before customer-facing delivery."
- Replace "9 validated UAE financial sources" with "Selected UAE source layers tested for access, extraction quality, and limitations."
- Add visible "SAMPLE / DEMO - NOT CUSTOMER DATA" labels to dashboard mock alerts.

No direct "AI lawyer", regulator partnership, or guaranteed compliance claim was found in the inspected customer-facing React hero copy. The standard short disclaimer appears in the hero. Weekly brief has the full disclaimer.

## 11. Security / Secrets / Data Review

Findings:

- `.env` files were not found under `product/`.
- Real `telegram_clients.json` was not found; only `telegram_clients.example.json` exists.
- `product/regradar/regradar.db` exists. This contradicts migration docs that say live DB files were excluded. It may be a local/generated DB, but it should not be in a shareable product workspace without inspection and tracking review.
- `product/.swarm/memory.db` exists. This is unrelated to the current StatuteProof product and should not be part of a clean product artifact.
- `product/regradar/web/node_modules/` exists. Root migration docs said `node_modules` was excluded; it is currently present.
- `product/regradar/web/dist/` exists. Build artifacts are present.
- `.cache/pdfs/` exists under `product/`, with cached PDFs. These may be public documents, but they are still generated artifacts and should be reviewed before commit/release.

Safe migration status: not clean enough for external sharing. Secrets look mostly excluded, but database/generated artifacts are present and must be reviewed before any push or demo package.

## 12. Tests / Validation Review

Tests found:

- `product/regradar/tests/test_text_normalization.py`
- `product/regradar/tests/test_chunk_diff_and_proof.py`
- `product/regradar/tests/test_alert_drafts.py`
- `product/regradar/tests/test_alert_review.py`
- `product/regradar/tests/test_client_relevance.py`
- `product/regradar/tests/test_weekly_brief.py`
- `product/tests/test_compliance_engine.py`

Validators/tools found:

- `product/regradar/scripts/validate_uae_sources.py`
- `product/regradar/tools/validate_uae_sources.py`
- `product/regradar/tools/validate_under_validation_stability.py`
- `product/regradar/tools/validate_adgm_fsra_html_item_level.py`
- `product/regradar/tools/validate_adgm_fsra_html_proof_diff.py`

What was checked:

- `python3 run.py --help` was attempted as a safe help command. It exits with code 2 because `--help` is not implemented, but it prints the available command list.

What is missing:

- No current first evidence dry-run report exists in `docs/`.
- No schema files exist for the `.claude/skills` references to `schemas/evidence-record.schema.json` and `schemas/risk-brief-output.schema.json`.
- No test seen for `FAILED != UNCHANGED`.
- No test seen for `SOURCE_STRUCTURE_CHANGED` because the status is not implemented.
- No test seen for end-to-end "source run -> proof -> alert draft -> review -> weekly brief".
- No frontend test coverage was found.

What should be run next:

- One safe source test only, after confirmation.
- The `FAILED != UNCHANGED` invariant check.
- Focused unit tests for normalization, source_runs, proof, alert_review, and weekly_brief.
- Frontend build after source/evidence UI wiring, not before.

## 13. Current Strengths

1. Real source fetching exists with requests and Playwright fallback.
2. Real normalization and SHA-256 hashing exist.
3. LLM is not used for change detection.
4. `FAILED` is classified before hash comparison.
5. JSONL source run history exists with 132 real records.
6. Raw and normalized snapshots exist.
7. Proof blocks and diff artifacts exist.
8. Weekly brief renderer includes full legal disclaimer.
9. Alert review has human approval states and safety checks.
10. Frontend has a coherent UAE-first product surface with auth, onboarding, source map, alerts, and brief previews.

## 14. Current Weaknesses

CRITICAL: Deployment is split between old `product/main.py` NiceGUI/Celery and newer `product/regradar/run.py api` plus React frontend. Customer deployment path is not clear.

CRITICAL: Dashboard remains sample/mock driven for core evidence and source health. A customer-facing demo could imply live monitoring that is not actually connected.

HIGH: No current first evidence dry-run report exists in `docs/`, despite the operating docs making this the first proof milestone.

HIGH: Evidence artifact format does not match the canonical Command Center evidence spec.

HIGH: `SOURCE_STRUCTURE_CHANGED` is specified but not implemented.

HIGH: Databases/generated artifacts exist in `product/` (`regradar.db`, `.swarm/memory.db`, `node_modules`, `dist`, cached PDFs), creating release hygiene and potential data-risk issues.

MEDIUM: JSONL locking is incomplete because classification/artifact writes occur before the append lock.

MEDIUM: `sources.json` contains `duplicate_url` statuses, but `app/sources.py` does not allow that status, so those entries are skipped by the loader.

MEDIUM: Risk scoring is still shallow for English content and can false-trigger on boilerplate if extraction is noisy.

LOW: CLI lacks normal `--help` behavior.

## 15. Is The Product Actually Useful To An MLRO?

Yes, but only after proof is made visible and current. An MLRO does not need another "AI compliance" dashboard. An MLRO may care if StatuteProof can show: this official VARA/CBUAE/DFSA page was checked at this UTC time, this exact normalized text was hashed, this changed compared with the previous version, here is the diff, here are the limitations, and no brief goes out before human review.

What would make an MLRO care:

- A real source readiness report for their exact source list.
- A visible evidence record with URL, timestamp, hash, raw snapshot, normalized text, diff, and status.
- A weekly "checked X sources, Y unchanged, Z changed/failed" audit trail.
- Honest limitations near every coverage claim.

What would make them not care:

- Mock alerts.
- Broad "AI" messaging.
- Claims about validated sources without showing source proof.
- A dashboard that looks polished but cannot open the underlying evidence.

## 16. Top 10 Improvements

1. Wire one live evidence record into the dashboard.
   Why an MLRO cares: proves the audit trail is real.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

2. Create the first current evidence dry-run report.
   Why an MLRO cares: shows one source can be monitored end to end today.
   Build difficulty: EASY.
   Revenue impact: HIGH.

3. Add a live source health endpoint/table from JSONL latest runs.
   Why an MLRO cares: shows what was checked and what failed.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

4. Implement `SOURCE_STRUCTURE_CHANGED`.
   Why an MLRO cares: separates site breakage from regulatory change.
   Build difficulty: MEDIUM.
   Revenue impact: MEDIUM.

5. Align runtime proof artifacts with the evidence spec.
   Why an MLRO cares: makes records audit-ready and explainable.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

6. Add a first-class diff viewer.
   Why an MLRO cares: lets them inspect what changed without trusting a summary.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

7. Replace mock source rows with latest real run data.
   Why an MLRO cares: avoids trust loss from sample data.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

8. Clean product artifacts before release.
   Why an MLRO cares: security and professionalism.
   Build difficulty: EASY.
   Revenue impact: MEDIUM.

9. Make deployment point to one product surface.
   Why an MLRO cares: reliability during pilot.
   Build difficulty: MEDIUM.
   Revenue impact: HIGH.

10. Add tests for failed fetch, quality drop, proof completeness, and hash reproducibility.
    Why an MLRO cares: reduces silent monitoring failure.
    Build difficulty: MEDIUM.
    Revenue impact: MEDIUM.

## 17. Single Highest-Impact Homepage Change

Replace the dashboard mockup emphasis with a real "Evidence Record Preview" section above the fold or immediately below it: official URL, last checked UTC, run status, normalized hash, extraction quality, diff summary, and limitations. CTA: "Request a free source readiness review." This would move the page from "nice compliance SaaS" to "this solves my audit-trail problem."

## 18. What Not To Build Yet

- Full dashboard rewrite.
- All regulators.
- Complex n8n automation.
- Legal advice engine.
- Auto-send briefs.
- Multi-agent runtime.
- Billing before pilot validation.
- Enterprise SSO.
- Mobile app.
- Vector search over regulations.
- Broad multi-market expansion beyond the UAE wedge.

## 19. Next 7-Day Execution Plan

Day 1:
Objective: establish one current safe evidence baseline.
Files/areas involved: `product/regradar/run.py`, `app/source_tester.py`, `app/source_runs.py`, `data/source_runs/`.
Output: one dry-run report draft.
Success criteria: one official source test completed without AI, Telegram, or customer delivery.
Responsible agent: Source Monitor Agent.

Day 2:
Objective: audit the evidence artifact from Day 1.
Files/areas involved: `data/source_runs/source_runs.jsonl`, `data/source_snapshots/...`, `app/proof.py`.
Output: evidence audit section with PASS/BLOCK.
Success criteria: raw, normalized, hash, timestamp, official URL, run ID, and proof paths verified.
Responsible agent: Evidence Trail Agent.

Day 3:
Objective: verify `FAILED != UNCHANGED` and quality status behavior.
Files/areas involved: `app/source_runs.py`, `tests/`.
Output: documented invariant result and missing-test list.
Success criteria: failed case returns `FAILED`; no failed run can become `UNCHANGED`.
Responsible agent: QA / Critic Agent.

Day 4:
Objective: review the risk and brief layer against the Day 1 evidence.
Files/areas involved: `app/risk.py`, `app/ai_brief.py`, `app/weekly_brief.py`.
Output: internal SAMPLE / FAKE brief only if evidence is complete.
Success criteria: no legal advice, no invented affected entities, human review flag present.
Responsible agent: Risk + Brief Pipeline Agent.

Day 5:
Objective: legal-safety review of homepage and sample brief language.
Files/areas involved: `web/src/components/Hero.jsx`, `web/src/data/appMockData.js`, brief draft.
Output: unsafe-claim list and exact replacements.
Success criteria: sample labels visible, source claims qualified, full disclaimer where needed.
Responsible agent: Legal Language Agent.

Day 6:
Objective: decide the pilot wedge and homepage conversion fix.
Files/areas involved: `docs/statuteproof-mvp-plan.md`, `web/src/components/Hero.jsx`, `web/src/components/Pricing.jsx`.
Output: one-page source readiness review offer.
Success criteria: MLRO can understand the offer in 30 seconds.
Responsible agent: Product Manager Agent.

Day 7:
Objective: founder execution review.
Files/areas involved: dry-run report, evidence audit, legal review, QA notes.
Output: go/no-go decision for manual MVP.
Success criteria: either "ready for manual MVP" with evidence attached, or explicit blockers named.
Responsible agent: Chief of Staff / QA Critic.

## 20. Smallest Safe Next Task

Task name: prepare and run one safe evidence dry run.

Why this first: the project is only credible if one current official-source run can produce verifiable evidence without AI, Telegram, customer delivery, or broad monitoring.

Files involved:

- `product/regradar/run.py`
- `product/regradar/app/source_tester.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/data/source_runs/source_runs.jsonl`
- `product/regradar/data/source_snapshots/`
- `docs/first-evidence-dry-run-report.md`

Safe command:

```bash
cd product/regradar
python3 run.py test-source https://www.dfsa.ae/rules-and-standards
```

This command should be confirmed before running because it fetches one public official URL.

Acceptance criteria:

- One official source URL tested.
- No AI call.
- No Telegram send.
- No customer delivery.
- Result records access status, extraction quality, extracted chars, fetch method, and limitations.
- Evidence report written under `docs/`.
- `FAILED != UNCHANGED` invariant documented.

Rollback notes:

- If the command writes no history, no rollback needed.
- If a test writes a run record, keep it as internal dry-run evidence and label the report as internal.
- Do not modify `sources.json`.
- Do not delete historical source runs.

## 21. Next Claude Prompt

Copy and paste this prompt next:

```text
Use the StatuteProof Source Monitor Agent, Evidence Trail Agent, Risk + Brief Pipeline Agent, Legal Language Agent, and QA / Critic Agent conceptually and sequentially.

Task: prepare and run the first safe evidence dry run for StatuteProof.

Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not edit sources.json.
Do not run broad live monitoring.
Do not call AI.
Do not send Telegram.
Do not send email.
Do not deliver anything to customers.
Do not print .env values, API keys, tokens, Telegram IDs, or client data.
Do not create new agents.
Do not provide legal advice.

Steps:
1. Read CLAUDE.md, AGENTS.md, TOOL_ROUTER.md, workflows/03-evidence-dry-run.md, docs/evidence-record-spec.md, and product/regradar/AGENTS.md.
2. Choose one safe official UAE source URL for a single test. Prefer DFSA rules and standards if present in sources.json.
3. Before fetching, state the exact command and ask for confirmation because it will fetch one public official URL.
4. After confirmation, run only one safe source test.
5. Verify whether the result includes access status, fetch method, extracted chars, extraction quality, normalized/hash evidence if written, and limitations.
6. Verify FAILED != UNCHANGED using classify_change().
7. Do not generate a customer brief. If evidence is complete, create only an internal SAMPLE / FAKE brief note or say that brief generation is blocked.
8. Write docs/first-evidence-dry-run-report.md with:
   - source URL
   - command run
   - result summary
   - evidence paths, if any
   - hash fields, if any
   - run status
   - limitations
   - FAILED != UNCHANGED result
   - Legal Language review
   - QA / Critic PASS or BLOCK verdict
9. Final output: report path, PASS/BLOCK, biggest blocker, and next safe task.
```

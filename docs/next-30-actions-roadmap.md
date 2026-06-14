# StatuteProof Next 30 Actions Roadmap

Date: 2026-06-14

## Top 5 Highest-Leverage Actions

1. Run the approved DFSA source-model migration/no-save/baseline task.
2. Browser-test auth/session behavior with API + Vite before any customer demo.
3. Convert the proof-backed VARA demo artifact into a reviewed, non-delivered weekly brief preview.
4. Build founder/admin manual activation workflow for paid pilots.
5. Generate one canonical source-readiness summary consumed by validators and frontend.

## P0 Sprint Update

Completed in the P0 execution sprint:

- Canonical source-readiness truth resolved to 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.
- DFSA source model decision documented; DFSA remains under remediation pending approved registry migration, no-save checks, and saved baseline.
- First proof-backed sample/demo brief created from a real VARA evidence/proof/diff artifact.
- Auth session cookie behavior fixed for local HTTP while keeping production secure by default.
- Paid plan intent now returns `pending_manual_activation`; active capabilities remain Source Readiness Review until manual activation.
- Weekly brief tests updated to the current legal-safe disclaimer and no-detected-change wording.

Still open:

- DFSA cannot leave remediation.
- Browser auth smoke is still required before a customer demo.
- Manual activation needs a founder/admin workflow before first paid pilot.
- A generated source-readiness summary should replace duplicated frontend constants.

## A. Immediate P0 - Before Any Customer Demo

| # | Action | Why it matters | Files/modules involved | Owner/agent | Difficulty | Validation command | Acceptance criteria | Risk if skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Source-readiness truth reconciliation | Prevents false claims and confused demos. | `sources.json`, frontend source tables, `validate_parser_quality.py`, readiness docs | Product Manager, Source Monitor, Legal, QA | Medium | `python3 tools/validate_parser_quality.py` | One canonical count, remediation IDs, and validator agree. Status: completed at 13/9/4. | Customer sees inconsistent claims. |
| 2 | DFSA source model decision | Current DFSA URLs are not ready and should not be sold as ready. | `sources.json`, DFSA reports, Source Lab CLI | Source Monitor, Evidence Trail | Medium | Two no-save `source-lab` runs only | Exact DFSA source IDs/URLs/selectors are approved or held in remediation. Status: decision documented; registry/baseline still open. | DFSA overclaim or bad source activation. |
| 3 | First proof-backed demo brief | Demo needs one real evidence artifact, not only sample UI. | `source_runs.py`, `alert_drafts.py`, `weekly_brief.py`, evidence docs | Evidence Trail, QA, Legal | Medium | Targeted proof/brief commands; no delivery | One reviewed artifact with proof, diff, disclaimer, and sample/live boundary. Status: sample artifact created; reviewed weekly preview still open. | Demo feels polished but not proven. |
| 4 | Auth browser QA | Login/register must work before app demo. | `api.py`, `auth.py`, Vite proxy, auth pages | QA, Code Architect | Medium | Browser test + `npm run build` if changed | Register, login, refresh, logout work locally and production-like. Status: cookie contract fixed/tested; browser smoke still open. | Live demo login failure. |
| 5 | Plan intent vs activation state | Paid plan should not look activated by mere selection. | `plan.py`, billing/choose-plan pages | Product Manager, Code Architect, Legal | Medium | Plan tests + browser smoke | Paid selection says pending manual activation until approved. Status: backend/UI contract fixed; founder activation workflow still open. | Billing trust issue. |
| 6 | Pre-demo sample/live script | Avoids accidental overclaim when showing sample pages. | `EvidencePage.jsx`, `AIBriefPage.jsx`, `AlertsPage.jsx`, demo docs | QA, Legal | Low | Manual checklist | Demo script names which pages are live API versus sample/demo. | Buyer misreads sample data as live proof. |
| 7 | Evidence page stale comment fix | Prevents future agents from assuming no API exists. | `EvidencePage.jsx` | Code Architect | Low | `npm run build` if frontend validation run | Header comment matches current API reality. | Future work follows stale assumption. |
| 8 | README project location fix | Prevents wrong worktree/path usage. | `README.md` | Chief of Staff | Low | `git diff --check` | README points to `product/regradar/`. | Agents edit wrong location. |

## B. P1 - Before First Paid Founding Pilot

| # | Action | Why it matters | Files/modules involved | Owner/agent | Difficulty | Validation command | Acceptance criteria | Risk if skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | Manual pilot activation model | Needed for controlled billing and source scope. | `plan.py`, `db.py`, billing pages | Product Manager, Code Architect | Medium | Python plan tests, route validation | Plans support `pending_manual_activation` and approved active state. | Customer thinks payment/monitoring is live prematurely. |
| 10 | Persist legal acknowledgement | Registration should record acceptance of monitoring/legal boundary. | `RegisterPage.jsx`, `auth.py`, `db.py` | Legal, Code Architect | Medium | Auth tests | Acknowledgement version/time stored for new users. | Weak audit trail for legal boundary. |
| 11 | Source Lab save/baseline UX hardening | Custom source users need exact next state after save. | `SourceLabPage.jsx`, `api.py`, `source_intake.py` | Product Manager, QA | Medium | Source Lab tests + browser smoke | Save says validation queued, not active; baseline requirements visible. | User thinks custom source is monitored. |
| 12 | API-backed Sources page | Source page should reflect current source status, not only mock rows. | `SourcesPage.jsx`, `api.js`, `/api/sources/status` | Code Architect, Source Monitor | Medium | Route validation + API smoke | Table can show live API status with clear fallback. | Source map drifts from registry. |
| 13 | Source count single data module | Eliminates duplicated source counts in frontend. | frontend data/components | Code Architect | Medium | New consistency test | Homepage, pricing, dashboard, source table share one summary. | Count drift returns. |
| 14 | Evidence artifact validator | Increases trust in proof paths and append-only evidence. | `source_runs.py`, `proof.py`, new tool | Evidence Trail | Medium | New validator + proof tests | Validates proof paths, hashes, diffs, and snapshot existence. | Broken proof artifacts go unnoticed. |
| 15 | Delivery safety confirmation | Prevents accidental Telegram/customer messages. | `IntegrationsPage.jsx`, `api.py`, `user_delivery.py` | QA, Legal | Low/Medium | Delivery endpoint tests | Test sends require explicit confirmation and demo warnings. | Accidental message during demo. |
| 16 | Password reset decision | Either implement or keep clearly disabled. | auth pages/API | Product Manager, Code Architect | Medium | Auth tests | User-facing auth flow has no misleading reset CTA. | Buyer sees unfinished auth. |
| 17 | Stale-doc archiving | Keeps future agents from following superseded specs. | older docs | Chief of Staff, QA | Low | `git diff --check` | Historical docs have superseded headers or archive index. | Old instructions reintroduce stale claims. |

## C. P2 - Before UAE Monitor $399

| # | Action | Why it matters | Files/modules involved | Owner/agent | Difficulty | Validation command | Acceptance criteria | Risk if skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | Evidence baseline for included sources | UAE Monitor needs real source history. | source readiness/run commands, data policies | Source Monitor, Evidence Trail | High | Targeted source readiness runs only | Included sources have proof-backed baseline history. | $399 scope lacks proof. |
| 19 | DFSA baseline after model update | DFSA must not leave remediation on a no-save test alone. | `sources.json`, source lab, source runs | Source Monitor | High | Two or more evidence runs | DFSA has meaningful unique content, proof, baseline, and no shell/collision. | DFSA false-ready risk. |
| 20 | UAE FIU homepage remediation | Clarifies homepage vs circular/publication source. | `sources.json`, FIU docs, Source Lab | Source Monitor | Medium | Targeted no-save/source runs | FIU homepage either removed/limited or remediated with selector. | Duplicate/shallow FIU story. |
| 21 | Rendered DOM/screenshot evidence | Important for JS sources and audit confidence. | `scraper.py`, `source_runs.py`, proof schema | Evidence Trail, Code Architect | High | Parser tests + evidence validator | Playwright sources can store rendered HTML/screenshot paths. | JS-source proof remains text-only. |
| 22 | PDF scanned/OCR-needed detection | Avoids false confidence on image PDFs. | `providers/pdf_extraction.py`, `source_intake.py` | Source Monitor | Medium | PDF fixture tests | Shallow/scanned PDFs return clear OCR-needed remediation. | PDF extraction silently misses text. |
| 23 | Parser benchmark corpus | Moves parser from good to reliable. | `tests/fixtures`, parser tests | QA, Source Monitor | Medium | `pytest test_parser_benchmark_suite.py` | Fixtures cover HTML, JS, PDF, nav-shell, table, multilingual, shallow. | Score stays anecdotal. |
| 24 | Review queue production path | Human review must be robust for paid monitoring. | alert queue/review/brief pages | Risk + Brief, QA | Medium | Alert review tests | Review states, reasons, and delivery decisions are visible and testable. | Alerts shipped without review clarity. |
| 25 | Retention policy implementation | Paid plans promise retention durations. | plan, data storage, docs | Product Manager, Code Architect | Medium | Retention tests | Retention behavior matches plan promises or is explicitly manual. | Pricing promises exceed implementation. |

## D. P3 - Before Consultant / Enterprise

| # | Action | Why it matters | Files/modules involved | Owner/agent | Difficulty | Validation command | Acceptance criteria | Risk if skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 26 | Multi-workspace model | Consultants need multiple clients. | auth/profile/db/frontend | Code Architect, Product Manager | High | Integration tests | Workspaces isolate data and source scope. | Consultant plan cannot be sold honestly. |
| 27 | Team roles | CCO/MLRO/legal reviewers need permissions. | auth/db/app shell | Code Architect, QA | High | Auth/role tests | Owner/admin/reviewer/read-only roles work. | Audit/control concerns. |
| 28 | Audit binder export | Enterprise buyers expect exportable proof. | reports/export modules | Evidence Trail, Product Manager | Medium/High | Export tests | Evidence bundle exports with manifest and disclaimers. | Roadmap feature remains vague. |
| 29 | Security/trust page | Regulated buyers need security posture clarity. | frontend legal/trust page, ops docs | Legal, Product Manager | Medium | Build/route validation | Honest security page with no false certifications. | Buyer trust gap. |
| 30 | Deployment/rollback runbook | Reduces production risk. | deployment docs/scripts | Code Architect, QA | Medium | Dry-run checklist | Deploy/rollback steps verified without secrets exposure. | Fragile release process. |
| 31 | Admin manual activation console | Manual pilot operations need auditability. | admin UI/API/db | Product Manager, Code Architect | High | Admin tests | Founder can approve source/plan activation with audit log. | Manual state managed outside product. |

## E. Long-Term 10/10 Parser / Source System

| # | Action | Why it matters | Files/modules involved | Owner/agent | Difficulty | Validation command | Acceptance criteria | Risk if skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 32 | Source-specific adapters for hard regulators | DFSA/ADGM/FIU may need precise structure handling. | adapters, source registry | Source Monitor, Code Architect | High | Adapter fixture tests | Hard sources extract item-level regulatory text. | Generic parser remains brittle. |
| 33 | Adaptive monitoring schedule | Reduces noise and load while preserving evidence. | scheduler/source history | Source Monitor | Medium | Scheduler tests | Schedules reflect source change frequency and priority. | Inefficient/noisy monitoring. |
| 34 | WARC capture option | Stronger evidence for web-source state. | proof/evidence providers | Evidence Trail | Medium/High | Evidence validator | Optional WARC path stored and referenced. | Proof less complete for audits. |
| 35 | External timestamping option | Improves tamper-evidence story. | proof/evidence pipeline | Evidence Trail | Medium | Timestamp tests | External timestamp metadata can be attached without blocking core flow. | Local hashes only. |
| 36 | 30-day source stability report | Converts pilot into revenue proof. | source_runs/reporting | Product Manager, Source Monitor | Medium | Report generator tests | Shows uptime, failures, quality drops, changes, and limitations. | Harder to justify paid plan. |
| 37 | Customer-facing source readiness portal | Shows exactly what is included and limited. | app sources/evidence pages | Product Manager, Legal | Medium | Browser QA | Users see source status, last proof, limitations, and next action. | Trust relies on sales conversation only. |
| 38 | Production-grade persistence | Needed for multi-tenant paid use. | database/storage | Code Architect, Security | High | Migration/integration tests | Source runs, evidence, reviews, plans are durable and isolated. | Filesystem pilot storage limits growth. |
| 39 | Full pre-release gate automation | Prevents regressions. | tools/validators/CI | QA | Medium | One validation script | Parser, claims, routes, frontend, skills, workspace checks run together. | Manual gates become inconsistent. |
| 40 | Pilot feedback loop | Product-market fit depends on actual MLRO workflows. | docs/product/process | Product Manager | Low | Research synthesis doc | Every pilot produces objections, missing workflows, and willingness-to-pay notes. | Product improves without buyer evidence. |

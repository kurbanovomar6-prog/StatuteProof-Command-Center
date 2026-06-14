# StatuteProof Next Execution Prompts

Date: 2026-06-14

Use these prompts one at a time. Do not combine source modeling, evidence baselines, billing, and deployment in a single run.

## 1. DFSA Source Model Update Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, modify Cloudflare/DigitalOcean, expose secrets, run all sources, send messages, or write evidence.

Goal: resolve the DFSA source model before changing customer-facing readiness counts.

Read:
- product/regradar/sources.json
- docs/dfsa-selector-investigation-report.md
- docs/dfsa-live-source-lab-verification-report.md
- docs/bug-and-logic-error-register.md

Decide and document:
1. Should AE-dfsa-notices mean enforcement regulatory actions, AML/MLRO notices, or another DFSA public notice page?
2. Should DFSA Rulebook use the Thomson Reuters rulebook page found in the selector investigation?
3. Should AML/MLRO notices be a separate source ID?
4. Exact source IDs, URLs, wait_for_selector, content_selector, expected_min_length, and source_type.

Create docs/dfsa-source-model-decision.md.

Do not edit sources.json unless the model is explicitly supported by no-save Source Lab results already in docs.

Validation:
- git diff --check
- python3 tools/validate_parser_quality.py

Commit only docs if no source config changes:
git add docs/dfsa-source-model-decision.md
git commit -m "docs: define DFSA source model"
git push origin main
```

## 2. DFSA Evidence Save / Baseline Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar.

Do not run all sources, broad monitoring, customer delivery, Telegram/email, or LLM change decisions.

Precondition: docs/dfsa-source-model-decision.md exists and names approved DFSA URLs/selectors.

Goal: run only the approved DFSA sources through no-save Source Lab checks, then evidence save/baseline only if strict criteria pass.

For each DFSA source:
1. Run no-save Source Lab with approved URL/selectors.
2. Capture provider, normalized_length, normalized_hash, quality, readiness, activation_readiness, evidence_level, nav_shell, collision, warnings, failure_reason, remediation_hint, preview.
3. If and only if both no-save checks are meaningful, unique, non-shell, and quality GOOD/ACCEPTABLE, run controlled evidence save/baseline as specified by Source Monitor and Evidence Trail.

Create/update docs/dfsa-evidence-baseline-report.md.

Validation:
- python3 -m pytest tests/test_source_intake.py
- python3 ../tools/validate_parser_quality.py from project root if path permits
- git diff --check

Commit only approved config/report changes:
git commit -m "fix: baseline DFSA source readiness after selector verification"
git push origin main
```

## 3. UAE FIU Shallow Source Remediation Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, run all sources, send messages, or change DFSA.

Goal: resolve whether AE-uae-financial-intelligence-unit-uaefiu should remain as a homepage remediation source, be replaced by UAE FIU circulars/publications, or be removed/disabled from the customer-visible pack.

Read:
- product/regradar/sources.json
- docs/current-uae-source-readiness-validation-report.md
- docs/parser-ideal-system-final-report.md
- product/regradar/app/source_intake.py

Run only no-save Source Lab tests for UAE FIU candidate public pages. Do not save evidence.

Create docs/uaefiu-source-remediation-report.md with exact recommendation and customer-facing wording.

Validation:
- python3 tools/validate_parser_quality.py
- git diff --check

Commit report/config only if validation passes.
```

## 4. First Real Evidence-Backed Sample Brief Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, run all sources, send messages, or use LLMs to decide whether content changed.

Goal: create one real evidence-backed demo artifact from a safe non-DFSA source such as VARA enforcement or CBUAE regulations.

Read:
- product/regradar/app/source_runs.py
- product/regradar/app/alert_drafts.py
- product/regradar/app/alert_review.py
- product/regradar/app/weekly_brief.py
- docs/current-uae-source-readiness-validation-report.md

Use only one source. Create proof/diff if supported by existing evidence history. If not enough history exists, document the gap instead of fabricating a changed update.

Create docs/first-evidence-backed-demo-brief-report.md.

Validation:
- python3 -m pytest product/regradar/tests/test_chunk_diff_and_proof.py
- python3 -m pytest product/regradar/tests/test_alert_review.py
- python3 -m pytest product/regradar/tests/test_weekly_brief.py
- python3 tools/validate_parser_quality.py
- git diff --check

Commit only report/artifact code changes that are safe. Do not commit generated source snapshots unless explicitly approved.
```

## 5. Source Lab Customer Flow Hardening Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, run live broad monitoring, or change parser truth counts.

Goal: harden Source Lab and Sources custom source flow so users cannot confuse no-save preview, saved-for-validation, evidence confirmed, and monitoring-ready.

Read:
- product/regradar/web/src/components/app/SourceLabPage.jsx
- product/regradar/web/src/components/app/SourcesPage.jsx
- product/regradar/app/api.py
- product/regradar/app/source_intake.py
- docs/bug-and-logic-error-register.md

Implement small changes only:
- Route Add custom source to Source Lab or remove weaker duplicate modal.
- Ensure can_save_for_validation and can_activate_monitoring are shown accurately.
- Ensure "no-save" cannot read as evidence confirmed.

Validation:
- cd product/regradar/web && npm run build && npm run lint
- node product/regradar/web/scripts/validate-routes.mjs from root if supported
- python3 tools/validate_parser_quality.py
- git diff --check

Commit:
git commit -m "fix: harden Source Lab custom source flow"
git push origin main
```

## 6. Billing / Manual Pilot Activation Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not connect Stripe, process payments, deploy, or change production infrastructure.

Goal: separate plan selection intent from manual activation.

Read:
- product/regradar/app/plan.py
- product/regradar/app/db.py
- product/regradar/app/api.py
- product/regradar/web/src/components/app/ChoosePlanPage.jsx
- product/regradar/web/src/components/app/BillingPage.jsx
- docs/bug-and-logic-error-register.md

Implement:
- Plan status values: evidence_preview, trial_active, trial_expired, pending_manual_activation, active.
- Paid plan selection records intent and shows pending manual activation.
- No copy implies payment processed or monitoring activated.

Add tests for plan state.

Validation:
- python3 -m pytest product/regradar/tests -q
- cd product/regradar/web && npm run build && npm run lint
- python3 tools/validate_workspace.py
- git diff --check

Commit:
git commit -m "fix: separate plan intent from manual activation"
git push origin main
```

## 7. Pre-Demo QA / Legal / Source-Monitor Gate Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, run all sources, send messages, expose secrets, or change source counts.

Goal: run a final pre-demo gate using Source Monitor, Evidence Trail, QA/Critic, and Legal Language perspectives.

Inspect:
- homepage
- pricing
- login/register
- dashboard
- sources
- Source Lab
- evidence
- briefs
- billing/settings
- docs/statuteproof-mega-audit-final-report.md
- docs/bug-and-logic-error-register.md

Create docs/pre-demo-gate-report.md with pass/fail per gate and blockers.

Validation:
- product frontend build/lint if frontend touched
- python3 tools/validate_parser_quality.py
- python3 tools/validate_workspace.py
- git diff --check

Commit report only if no code changes:
git commit -m "docs: add pre-demo StatuteProof gate report"
git push origin main
```

## 8. Deployment Readiness Audit Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy, modify Cloudflare, modify DigitalOcean, print secrets, or cat .env.

Goal: audit deployment readiness and produce a no-deploy runbook.

Read:
- docs/actual-hosting-location-audit.md
- product/regradar/docs/*deployment*
- product/regradar/app/api.py
- product/regradar/web/vite.config.js
- .gitignore

Check build commands, API start command, static asset assumptions, session cookie/CORS implications, runtime data paths, backup needs, rollback path, and secret handling.

Create docs/deployment-readiness-mega-audit.md.

Validation:
- git diff --check
- python3 tools/validate_workspace.py

Commit docs only.
```

## 9. First Customer Pilot Checklist Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not deploy or contact prospects/customers.

Goal: create the exact readiness checklist for a manual $199 Founding Pilot.

Read:
- docs/statuteproof-mega-audit-final-report.md
- docs/next-30-actions-roadmap.md
- product/regradar/web/src/data/planCapabilities.js
- product/regradar/app/plan.py

Create docs/founding-pilot-readiness-checklist.md with:
- what can be promised
- what cannot be promised
- required evidence before activation
- source scope selection
- onboarding questions
- manual billing steps
- legal disclaimers
- go/no-go criteria

Validation:
- git diff --check

Commit docs only.
```

## 10. Parser Benchmark Improvement Prompt

```text
Work only inside /Users/kurbnovomar/StatuteProof-Command-Center.

Do not run live websites except explicit approved no-save checks. Do not install huge dependencies.

Goal: expand parser benchmark tests using local fixtures only.

Read:
- product/regradar/tests/test_parser_benchmark_suite.py
- product/regradar/tests/test_source_intake.py
- product/regradar/app/source_intake.py
- product/regradar/app/providers/html_extraction.py
- product/regradar/app/providers/pdf_extraction.py

Add local fixtures for:
- good regulatory HTML
- JS-shell-like HTML
- nav shell
- table-heavy source
- shallow source
- PDF text source
- scanned/OCR-needed PDF fixture if feasible
- multilingual/Arabic text signal

Validation:
- python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py product/regradar/tests/test_source_intake.py -q
- python3 tools/validate_parser_quality.py
- git diff --check

Commit:
git commit -m "test: expand parser benchmark fixtures"
git push origin main
```

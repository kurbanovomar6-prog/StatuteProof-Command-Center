# VARA Source Depth Implementation Plan

Date: 2026-06-16

## Current VARA State

Current public source truth remains **66 enabled UAE sources / 62 readiness-supported / 4 remediation**.

VARA coverage is commercially thin compared with CBUAE. The active/readiness-supported VARA layer currently appears to include:

- `AE-dubai-virtual-assets-regulatory-authority-vara` — VARA homepage, active but broad and less valuable than direct regulatory documents.
- `AE-vara-enforcement` — VARA enforcement page, active.
- `AE-vara-rulebook-updates` — VARA rulebook revision updates on `rulebooks.vara.ae`, active and proof-backed.

Known weaker VARA candidates in the queue include framework/rulebook pages on `www.vara.ae` that previously returned stale paths, JS shell output, or domain-stop failures. The useful path is likely direct official rulebook/PDF endpoints or the `rulebooks.vara.ae` official rulebook application.

## Why VARA Depth Matters Commercially

VARA-regulated VASPs are a natural buyer type for StatuteProof, but three VARA sources do not feel like deep coverage. A serious VASP MLRO will expect monitoring of official framework/rulebook documents, activity-specific rulebooks, AML/CFT obligations, market conduct, technology/risk controls, issuance rules, and enforcement/admin orders where official and public.

The goal is not to claim complete VARA coverage. The goal is to add proof-backed, stable official VARA rulebook/document monitoring and show limitations honestly.

## Known VARA Blockers

- `www.vara.ae/en/regulatory-framework/` and subpaths have previously produced stale, JS shell, not-found, or shallow output.
- Direct PDF/rulebook URLs are not yet mapped as activation-ready endpoints.
- Generic pages risk being marketing or navigation shells instead of monitorable regulatory text.
- Direct PDF extraction must reject shallow/scanned PDFs and HTML not-found shells masquerading as document URLs.
- No no-save result may be counted as evidence or monitoring-ready.

## Candidate VARA Official URLs / PDFs / Rulebooks To Investigate

Initial research targets:

- `https://rulebooks.vara.ae/`
- `https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day`
- `https://www.vara.ae/en/regulatory-framework/`
- `https://www.vara.ae/en/regulatory-framework/rulebooks/`
- `https://www.vara.ae/en/regulatory-framework/company-rulebook/`
- `https://www.vara.ae/en/regulatory-framework/aml-cft-rulebook/`
- `https://www.vara.ae/en/enforcement/`
- official direct PDF/document links discovered from those pages only if public and unauthenticated.

Rejected by default unless they expose high-value regulatory updates:

- generic VARA homepage duplicates;
- news/marketing pages;
- public register pages with mainly entity data rather than regulatory-change monitoring value;
- private, login, CAPTCHA, paywall, or session-only endpoints.

## Expected Adapter / Parser Work

Likely implementation scope:

- improve `vara_pdf_listing` for official rulebook/revision pages if item extraction is weak;
- improve `pdf_document` metadata and shallow/not-found classification if direct PDF URLs are discovered;
- add VARA-specific tests around direct PDF text, title/source metadata, deterministic hash behavior, not-found shell rejection, and review/PDF export compatibility;
- add `tools/validate_vara_source_depth.py` to block fake VARA readiness and forbidden coverage claims.

No broad crawler will be built in this sprint.

## Evidence / Baseline / Gate Plan

For each candidate:

1. Verify official/public status.
2. Run no-save Source Lab first.
3. Save evidence only for strong no-save passes.
4. Run repeat baseline with at least two saved runs.
5. Run mass-monitor dry-run for activated candidates.
6. Require Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only when all gates pass.

HOLD sources with unresolved:

- no-save-only status;
- shallow/scanned PDF;
- nav-shell/not-found shell;
- duplicate hash;
- high unresolved noise risk;
- high unresolved source-health risk;
- proof/baseline/gate gaps.

## Validators To Run

Required:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_vara_source_depth.py`
- `python3 tools/validate_email_delivery_readiness.py`
- `python3 tools/validate_pdf_audit_export.py`
- `python3 tools/validate_no_authenticated_mock_data.py`
- `python3 tools/validate_plan_pricing_consistency.py`
- `python3 tools/validate_review_queue.py`
- `python3 tools/validate_source_health_timeline.py`
- `python3 tools/validate_mvp_trust_workflow.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

Frontend validation only if frontend files change.

## Commit Policy

If validation passes, stage only files from this VARA source-depth sprint and commit:

`feat: strengthen VARA official source depth`

Then push to `origin main`.

## What Will Not Be Touched

- No deploy.
- No Cloudflare or DigitalOcean changes.
- No secrets, `.env`, keychains, private accounts, or browser profiles.
- No real customer emails.
- No fake VARA activation, fake proof, fake hash, fake baseline, or no-save-only activation.
- No claims of complete VARA coverage, legal advice, guaranteed compliance, perfect parsing, regulator certification, or "never miss updates."

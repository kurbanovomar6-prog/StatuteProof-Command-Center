# DIFC Remediation Implementation Plan

Date: 2026-06-16

## Current State

- Current public truth: **72 enabled UAE sources / 68 readiness-supported / 4 remediation**.
- DIFC remains the most visible commercial weak zone after the VARA direct-PDF sprint.
- `AE-difc-laws-and-regulations` is enabled but under `remediation`.
- `AE-difc-legislation` is disabled/navigation-only from a stale `difc.ae` route.
- Existing reports say DIFC Laws and Regulations has meaningful extraction history, but it remains under registry hold pending Source Monitor and Evidence Trail review.

## Why DIFC Matters Commercially

DIFC firms, legal teams, DFSA-adjacent compliance teams, consultants, and regulated fintechs expect the product to distinguish DFSA rulebook coverage from DIFC legal-framework coverage. Without an honest DIFC layer, the $399 UAE Monitor remains weaker for DIFC/DFSA buyers even though CBUAE, VARA, ADGM/FSRA, and DFSA coverage are stronger.

## Known DIFC Blockers

- Historic `difc.ae` legislation route produced 0 extracted characters / navigation-only output.
- `difc.com` legal pages may require precise selectors to avoid global navigation and marketing chrome.
- Some official DIFC pages expose legal details and `Download PDF` links, but no current source-specific adapter exists for DIFC legal database pages.
- Existing DIFC source status must not be moved from remediation to active unless proof, repeat baseline, mass-monitor dry-run, and review gates pass.

## Official DIFC URLs / Endpoints To Investigate

Priority candidates:

1. `https://www.difc.com/business/laws-and-regulations/`
   - DIFC laws/regulations overview.
   - Current remediation source URL.
2. `https://www.difc.com/business/laws-and-regulations/legal-database/`
   - Official DIFC Legal Database index with laws, regulations, amendment laws, notices, federal laws, Dubai laws.
3. `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020`
   - High-value Data Protection Law detail page.
4. `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/digital-assets-law-difc-law-no-2-of-2024`
   - High-value Digital Assets Law detail page.
5. `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018`
   - High-value Companies Law detail page.
6. `https://www.difc.com/business/laws-and-regulations/consultation-papers/`
   - Consultation paper listing if public and stable.
7. `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection`
   - Official Data Protection Commissioner hub.
8. `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance`
   - Data Protection guidance listing and document links.
9. `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10`
   - Data Protection / AI-interoperability regulatory guidance page.
10. `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement`
   - Supervision/enforcement guidance if public and meaningful.

Reject or hold:

- login, portal, CAPTCHA, paywall, or private routes;
- generic news/marketing pages unless clearly regulatory-update relevant;
- stale `difc.ae` route if it still produces navigation-only output;
- sources whose extracted hash collides with navigation shell or already-active source content.

## Expected Selector / Access / Parser Work

- Add a DIFC legal/document-listing adapter only if generic adapters cannot extract meaningful legal entries.
- Extract useful titles around generic `Download PDF`, `More info`, or detail links.
- Keep legal database page output focused on laws/regulations/consultations, not global navigation.
- Classify access-blocked/not-found/nav-shell states honestly.
- Block shallow or duplicate-shell output.
- Preserve Source Lab no-save vs evidence vs activation-ready separation.

## Evidence / Baseline / Gate Plan

For each strong no-save pass:

1. Save evidence/proof only if official/public, meaningful, non-shell, non-duplicate, and low/controlled noise.
2. Run two saved baselines.
3. Run scoped mass-monitor dry-run.
4. Require `MONITOR_OK` or documented safe non-drift.
5. Gate through Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect.
6. Update `sources.json` only for fully activation-ready DIFC sources.

## Validators To Run

- `python3 tools/validate_difc_source_remediation.py`
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

If frontend copy/counts are touched:

- `npm run build`
- `npm run lint`
- `node scripts/validate-routes.mjs`
- `node scripts/pre-demo-smoke.mjs` if present

## Commit Policy

Commit only after validation passes.

Commit message:

`feat: remediate DIFC official source coverage`

Stage only files touched by this DIFC task. Do not stage runtime junk, `.env`, secrets, or unrelated files.

## What Will Not Be Touched

- No deployment.
- No Cloudflare/DigitalOcean changes.
- No private accounts or credentials.
- No production email sends.
- No legal advice or complete DIFC/UAE coverage claims.
- No weakened validators.

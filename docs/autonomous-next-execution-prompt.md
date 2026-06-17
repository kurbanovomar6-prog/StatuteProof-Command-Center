# Next Autonomous Execution Prompt

Continue the StatuteProof ideal-product hardening program after the DIFC remediation sprint.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 79 enabled UAE sources.
- 78 readiness-supported active sources.
- 1 under extraction remediation.
- 50-source minimum has been reached.
- DIFC coverage improved with 8 proof-backed official legal/data-protection sources.
- Complete DIFC coverage is not claimed.
- Monitoring intelligence only. Not legal advice.

Latest proven additions:

- VARA source-depth sprint activated 6 direct official VARA PDF/rulebook sources.
- DIFC remediation sprint activated 8 official DIFC legal/data-protection sources:
  - `AE-difc-laws-and-regulations`
  - `AE-difc-legal-database`
  - `AE-difc-data-protection-commissioner`
  - `AE-difc-data-protection-guidance`
  - `AE-difc-data-protection-regulation-10`
  - `AE-difc-data-protection-supervision-enforcement`
  - `AE-difc-data-protection-law-2020`
  - `AE-difc-companies-law-2018`
- All activated DIFC sources passed strong no-save, two proof/baseline runs, mass-monitor dry-run `MONITOR_OK`, and six review gates.
- `AE-difc-consultation-papers` and `AE-difc-digital-assets-law-2024` remain held below strict quality threshold.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, claim complete UAE/DIFC coverage, or claim legal advice/guaranteed compliance/perfect parsing/never-miss monitoring.

Next exact product task:

## Build 7/30/90-Day Source Reliability Charts

Goal:
Make the source-health timeline commercially useful by showing source reliability over 7, 30, and 90 day windows on Sources, Evidence, and dashboard surfaces.

Implementation requirements:

1. Aggregate existing source run history from `product/regradar/data/source_runs/source_runs.jsonl`.
2. Compute per-source reliability windows:
   - 7 days
   - 30 days
   - 90 days
3. For each window calculate:
   - total runs
   - `MONITOR_OK` count
   - quality drops
   - hash drift / content drift events
   - nav-shell/source-structure/access failures
   - latest successful check timestamp
   - latest failure timestamp
   - reliability percentage
   - customer-safe health label
4. Add backend helper/API consistent with existing architecture:
   - `GET /api/sources/:source_id/reliability`
   - `GET /api/sources/reliability-summary`
5. Frontend:
   - Add compact 7/30/90 reliability indicators to Sources page.
   - Add source reliability section to Evidence page/review history context.
   - Add an honest dashboard summary for source reliability.
   - Show empty state: "No reliability history recorded yet" when run history is missing.
6. Do not fabricate historical runs.
7. Do not imply legal/compliance status from reliability status.
8. Keep wording: "Source extraction reliability", not "regulatory compliance reliability".

Tests required:

- 7/30/90 window aggregation from fixture run history.
- Empty history returns honest empty state.
- Hash drift and quality drops reduce reliability.
- Remediation/source-health failures are visible.
- API returns customer-safe fields only.
- Frontend references 7/30/90 reliability and does not use fake history.

Validators required:

- Add `tools/validate_source_reliability_charts.py`.
- Validator must check backend helper/API, frontend visibility, no fake history, no overclaims, and source truth 79 / 78 / 1.

Run validation:

```bash
git status --short
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests -q
python3 tools/validate_source_reliability_charts.py
python3 tools/validate_difc_source_remediation.py
python3 tools/validate_vara_source_depth.py
python3 tools/validate_email_delivery_readiness.py
python3 tools/validate_pdf_audit_export.py
python3 tools/validate_no_authenticated_mock_data.py
python3 tools/validate_plan_pricing_consistency.py
python3 tools/validate_review_queue.py
python3 tools/validate_source_health_timeline.py
python3 tools/validate_mvp_trust_workflow.py
python3 tools/validate_uae_source_pack.py
python3 tools/validate_uae_50_working_sources.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

If frontend is touched:

```bash
cd product/regradar/web
npm run build
npm run lint
node scripts/validate-routes.mjs
node scripts/pre-demo-smoke.mjs
```

Remaining commercial blockers after DIFC:

1. 7/30/90-day source reliability charts.
2. Bulk review/export workflows.
3. Real production email sending is configured-safe but not live by default.
4. ADGM alternate components remain thinner than ideal.
5. DFSA held AML/CTF sanctions deterministic hash work remains.
6. Remaining held VARA/DIFC candidates below strict quality thresholds.

Final output must include reliability chart status, tests added, validators added, validation result, commit hash, clean git status, next exact product task, and next exact sales task.

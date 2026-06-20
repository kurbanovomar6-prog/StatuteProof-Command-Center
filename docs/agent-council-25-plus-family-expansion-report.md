# Agent Council 25+ Family Expansion Report

Date: 2026-06-20

## 1. Starting Source Truth

- Starting commit: `2d8d30e feat: harden source parser and adapter truth gates`
- Starting truth: 238 enabled UAE sources / 169 fresh-alert eligible / 61 evidence-library / 5 candidate / 3 remediation
- Worktree clean before start: yes

## 2. Ending Source Truth

- Ending truth: 239 enabled UAE sources / 170 fresh-alert eligible / 61 evidence-library / 5 candidate / 3 remediation
- Source-level MONITOR_OK: 224
- Sources with proof path: 230

## 3. Agents Launched

- Fresh CLI agents attempted: 4
- Usable handoff packets: 0
- Result: all four fresh CLI agents exited with provider limit output: `You've hit your limit · resets 4:50pm (Asia/Baku)`.
- Old stuck agents were not resumed or closed.
- Coordinator proceeded with local Source Monitor, Evidence Trail, Code Architect, and QA/Critic checks using controlled commands and validators.

## 4. Handoff Packets Exchanged

- Agent-to-agent packets exchanged: 0 usable packets due to fresh-agent provider limit.
- Local packets recorded in this report: SCA service-shell blocker, FIU circulars blocker, MoF financial legislation activation, MoJ/Gazette access blocker.

## 5. Families Reviewed

- SCA
- UAE FIU
- Ministry of Finance
- MoJ / UAE Legislation / Gazette

## 6. Families Reaching 25+

- None.
- No family was inflated with static, duplicate, no-save-only, service-shell, or one-run-only sources.

## 7. Families Still Below 25

- SCA: 5 fresh-alert, gap 20.
- UAE FIU: 5 fresh-alert, gap 20.
- Ministry of Finance: 2 fresh-alert, gap 23.
- MoJ / UAE Legislation / Gazette: 0 fresh-alert, gap 25.

## 8. Exhaustive Search Evidence Per Below-25 Family

- SCA: robots.txt checked for `www.sca.gov.ae` and `www.uaecma.gov.ae`; both allow public fetch. Sitemap checked: 1,597 locs, 789 English locs, 613 open-data/regulations/news-like locs, and 72 service locs. Many sitemap locs are service, static detail, news detail, video, or navigation surfaces and cannot be counted as fresh-alert.
- UAE FIU: existing public queue candidates tested no-save. Homepage, Awareness, and Publications/circulars did not pass. goAML/private routes remain blocked.
- Ministry of Finance: financial legislation and ESR pages tested no-save. Both strong-passed no-save through `pdf_listing`; only financial legislation was taken through proof/baseline/MONITOR_OK in this commit.
- MoJ/Gazette: queue/search truth still points to `elaws.moj.gov.ae` and `uaelegislation.gov.ae` blockers. No WAF/access-control bypass attempted.

## 9. Sources Tested No-Save

- Unique official/public candidate surfaces tested no-save: 13.
- SCA unique candidates: warnings beta, warnings canonical, telemarketing companies, regulation detail 194, circulars, homepage, latest regulations, news.
- UAE FIU candidates: homepage, Awareness, Publications/circulars.
- MoF candidates: financial legislation, ESR.

## 10. Sources Activated

- `AE-mof-financial-legislation`

## 11. Sources Rejected

- Rejected or held due to no strong activation gate: 9.
- SCA warnings/canonical: service-shell listing, now blocked as `NAV_SHELL_ONLY`.
- SCA telemarketing: applied adapter returned `NAV_SHELL_ONLY`; probe remained below save gate.
- SCA regulation detail 194: no strong pass; detail/static risk.
- SCA homepage: `NAV_SHELL_ONLY`.
- SCA latest regulations: no strong pass.
- SCA news: no strong pass; applied adapter `NAV_SHELL_ONLY`.
- UAE FIU homepage: `NAV_SHELL_ONLY`.
- UAE FIU Awareness: `NAV_SHELL_ONLY`.
- UAE FIU Publications/circulars: `NAV_SHELL_ONLY`.

## 12. Exact Blockers

- Fresh CLI agents unavailable due provider limit.
- SCA official open-data pages often expose service-directory rows before monitorable rows.
- SCA sitemap contains many official pages, but many are services, static details, media/news details, or video pages.
- FIU circulars candidate remains nav-shell/publications alias; no distinct public circular row source proven.
- MoJ/Gazette remains access/WAF/nav-shell blocked; no bypass attempted.
- Source snapshot proof still is not canonical customer evidence record.

## 13. Adapters Improved

- No new family-specific adapter was added.
- `source_intake.py` was hardened to detect structured listing service-shell prefixes.

## 14. Parser / Source-Intake Gates Improved

- Added `_is_structured_service_shell` for `listing` and `sca_listing` outputs.
- Structured listings with majority service-directory rows or service-row prefixes now become `NAV_SHELL_ONLY` instead of preview-passing as `CONFIRMED_ACCESSIBLE`.
- Added regression tests for all-service and service-prefix listing shells.

## 15. Validators Improved

- `tools/uae50_apply_activation.py` now writes validator-required fresh-alert fields for gated activations.
- Activation helper now preserves `wait_for_selector` and `content_selector`.
- Activation helper default customer alert policy now mentions noise suppression.
- `tools/validate_uae_coverage_claims.py` now checks exact monitoring-mode buckets for the current proof-backed truth: 239 enabled / 170 fresh-alert / 61 evidence-library / 5 candidate / 3 remediation.
- `tools/validate_plan_pricing_consistency.py` now enforces the current 170-source UAE Monitor limit across backend and frontend.
- `tools/validate_uae_source_pack.py` now preserves the current legacy candidate-pack truth: 239 enabled / 238 monitoring-active / 1 remediation.

## 16. Proof Runs Saved

- Source snapshot proof runs saved: 2.
- Proof paths:
  - `data/source_snapshots/2026-06-20/AE/AE-mof-financial-legislation/intake-20260620T092307Z/proof.json`
  - `data/source_snapshots/2026-06-20/AE/AE-mof-financial-legislation/intake-20260620T092317Z/proof.json`

## 17. MONITOR_OK Added

- MONITOR_OK added: 1.
- `AE-mof-financial-legislation` mass-monitor dry-run result: `MONITOR_OK`, unchanged normalized hash.

## 18. Canonical Evidence Records Added

- 0.
- Customer risk briefs remain blocked without canonical append-only evidence records.

## 19. Customer Claims Changed

- Yes.
- Fresh-alert count updated from 169 to 170.
- Enabled UAE count updated from 238 to 239.
- Source-level MONITOR_OK updated from 223 to 224.
- Proof-path count updated from 229 to 230.
- MoF family updated from 1 to 2 fresh-alert sources.

## 20. Claims Explicitly Not Made

- No complete UAE coverage claim.
- No complete SCA/FIU/MoF/MoJ family coverage claim.
- No legal advice claim.
- No guaranteed compliance claim.
- No regulator certification claim.
- No perfect parsing or never-miss claim.
- No all-source coverage claim.

## 21. Validation Results

- `python3 -m compileall -q product/regradar tools`: passed.
- `python3 -m pytest product/regradar/tests -q`: passed, 340 passed, 5 warnings.
- `python3 tools/validate_fresh_signal_sources.py`: passed, `fresh_alert_count=170`.
- `python3 tools/validate_source_monitoring_modes.py`: passed, `enabled_ae=239`, modes `fresh_alert=170`, `evidence_library=61`, `candidate=5`, `remediation=3`.
- `python3 tools/validate_daily_checkable_sources.py`: passed, `daily_checkable_fresh_alert=170`.
- `python3 tools/validate_uae_coverage_claims.py`: passed.
- `python3 tools/validate_plan_pricing_consistency.py`: passed.
- `python3 product/regradar/reports/validate_audit.py`: passed.
- `python3 tools/agent_council.py list`: passed.
- `python3 tools/validate_parser_quality.py`: passed.
- `python3 tools/validate_no_static_sources_as_alerts.py`: passed.
- `python3 tools/validate_no_unvalidated_active_sources.py`: passed.
- `python3 tools/validate_uae_source_pack.py`: passed.
- `python3 tools/validate_fresh_signal_25_per_family.py`: passed, with disclosed below-25 families.
- `git diff --check`: passed.

## 22. Frontend Validation Result

- `npm run build`: passed.
- `npm run lint`: passed with 1 existing React Compiler warning for TanStack Table in `DashboardPreview.jsx`.
- `node scripts/validate-routes.mjs`: passed.

## 23. Next Exact SCA Task

Run official SCA network/API discovery for open-data table rows exposed by `www.sca.gov.ae` without bypassing access controls. Focus first on `/en/open-data/warnings`, `/en/open-data/violations-and-violators`, `/en/open-data/licensed-companies`, and sitemap-listed live-data pages. Reject service shells and detail pages.

## 24. Next Exact UAE FIU Task

Search public `uaefiu.gov.ae/en/more/knowledge-centre/` subpaths and any robots/sitemap-disclosed feeds for circular/notice/guidance rows. Do not count `Publications/` aliases or goAML/private routes.

## 25. Next Exact MoF Task

Take `AE-mof-esr` through the same proof/baseline/MONITOR_OK gates if Product and QA agree it is not duplicate or static-detail-only.

## 26. Next Exact MoJ/Gazette Task

No-save test official public `moj.gov.ae` ASPX legislation pages and any official gazette/legislation alternatives that are accessible without WAF/login/CAPTCHA bypass.

## 27. Next Exact Evidence Task

Implement canonical append-only `evidence-record.json` generator and validator. Source snapshot proof must remain separate from customer risk-brief evidence.

## 28. Next Exact Product Task

Keep customer-facing copy on selected-source monitoring. Update MoF wording to say 2 proof-backed fresh-alert sources, not complete MoF coverage.

## 29. Next Exact Sales Task

Use only the safe claim: 170 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK, proof files, hashes, and baseline confirmation as of 2026-06-20. Do not claim complete UAE coverage.

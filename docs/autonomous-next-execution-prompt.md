# Next Autonomous Execution Prompt

You are my autonomous StatuteProof source activation CTO-engineer. Continue from the committed state after the EOCN News and SCA Regulations Listing activation cycle.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 26 enabled UAE sources.
- 22 readiness-supported active sources.
- 4 under extraction remediation.
- 50 has not been reached; 24 more proof-backed sources are needed.

Latest proven additions:

1. `AE-eocn-news-en` — `eocn_news_listing`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.
2. `AE-sca-regulations-listing` — `sca_listing`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim 50.

Next highest-leverage batch:

1. `AE-sca-fatca-crs` — near-pass q=59; improve SCA document/listing context or direct document extraction to reach q>=60 without weakening gates.
2. `AE-adgm-listing-rules` — real page title but `adgm-page` returns 70-char nav shell; inspect rendered DOM/XHR and find correct content selector.
3. `AE-adgm-ra-notices` and `AE-adgm-ra-aml-guides` — currently ADGM 404 shell; find correct official replacement URLs or mark stale.
4. `AE-uaefiu-aml-cft-laws` — NAV_SHELL_ONLY; find direct official document URLs or XHR endpoint without bypassing protections.
5. `AE-sca-corporate-governance` — two-item extraction but nav-shell classification; decide whether separate source or covered by SCA regulations listing.

Cycle requirements:

1. Run `git status --short`, inspect current truth, and do not continue if dirty changes are not from this task.
2. Add fixture tests before adapter changes.
3. Use Playwright DOM/XHR investigation for the top source group.
4. Save evidence only after strong no-save q>=60, not nav-shell, not shallow, unique hash, low/controlled noise, can_save=true.
5. Require two stable baseline runs and mass-monitor dry-run `MONITOR_OK`.
6. Emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only after all gates pass.
8. Update `uae_50_activation_scoreboard.json`, `uae_source_work_queue.json`, `uae_source_candidates.json`, truth docs, validators, and tests.
9. Run:

```bash
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests -q
python3 tools/validate_source_discovery_engine.py
python3 tools/validate_source_activation_pipeline.py
python3 tools/validate_mass_source_activation_pipeline.py
python3 tools/validate_mass_monitoring_runner.py
python3 tools/validate_batch_onboarding.py
python3 tools/validate_uae_source_pack.py
python3 tools/validate_uae_50_working_sources.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

Commit only after validation passes. Push to `origin main`.

Final output must include counts before/after, sources activated, tests added, validation result, commit hash, why fewer than 50, and next exact task.

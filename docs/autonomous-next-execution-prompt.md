# Next Autonomous Execution Prompt

Continue the StatuteProof UAE 50-source activation program from the committed state after activating `AE-sca-fatca-crs` and `AE-adgm-listing-rules`.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 28 enabled UAE sources.
- 24 readiness-supported active sources.
- 4 under extraction remediation.
- 50 has not been reached; 22 more proof-backed sources are needed.

Latest proven additions:

1. `AE-sca-fatca-crs` — `sca_listing`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.
2. `AE-adgm-listing-rules` — `adgm_fsra_listing`, q=62, two stable evidence runs, mass-monitor `MONITOR_OK`.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim 50.

Next highest-leverage batch:

1. `AE-uaefiu-aml-cft-laws` — NAV_SHELL_ONLY; investigate rendered DOM/XHR and direct official document URLs. Do not activate route aliases that duplicate `AE-uaefiu-typology-reports`.
2. `AE-adgm-ra-notices` and `AE-adgm-ra-aml-guides` — currently stale/404 shell; find correct official ADGM Registration Authority replacement URLs or mark stale with exact blocker.
3. `AE-sca-corporate-governance` — current extraction is too small; decide whether it is a distinct monitorable source or already covered by SCA regulations listing.
4. `AE-vara-rulebooks` — official rulebook/PDF source if current URL is accessible; use PDF listing adapter only after no-save is strong.
5. `AE-cbuae-publications` — use only official public alternate endpoints; do not bypass WAF/403.

Cycle requirements:

1. Run clean git gate before edits.
2. Add fixture tests before adapter changes.
3. Use Playwright DOM/XHR investigation for the top source group.
4. Save evidence only after strong no-save q>=60, not nav-shell, not shallow, unique hash, low/controlled noise, can_save=true.
5. Require two stable baseline runs and mass-monitor dry-run `MONITOR_OK`.
6. Emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only after all gates pass.
8. Update scoreboard, work queue, truth docs, validators, and tests.
9. Run full validation and commit/push only after validation passes.

Final output must include counts before/after, sources activated, tests added, validation result, commit hash, why fewer than 50, and next exact task.

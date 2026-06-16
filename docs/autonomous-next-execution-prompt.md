# Next Autonomous Execution Prompt

Continue the StatuteProof UAE 50-source activation program from the weak-zone remediation commit.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 36 enabled UAE sources.
- 32 readiness-supported active sources.
- 4 under extraction remediation.
- 50 has not been reached; 18 more proof-backed sources are needed.

Latest proven additions:

1. `AE-uaefiu-aml-cft-laws` — `listing` on `body`, q=62, two stable evidence runs, mass-monitor `MONITOR_OK`.
2. `AE-uaefiu-publications-hub` — `fiu_eocn_document_listing` on `body`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.
3. `AE-cbuae-rulebook-revision-updates` — `cbuae_document_listing` on official `rulebook.centralbank.ae`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim 50.

Next highest-leverage batch:

1. ADGM alternate listing/card replacement URLs or selectors:
   - `AE-adgm-dp-regulatory-actions`
   - `AE-adgm-media-announcements`
   - `AE-adgm-listing-announcements`
   - `AE-adgm-ra-notices`
   - `AE-adgm-ra-aml-guides`
   Current tested URLs still return nav-shell, stale selector, or page shell. Use official ADGM sitemap/link discovery and Playwright DOM/XHR only; no broad crawl.

2. VARA official PDF/rulebook endpoints:
   - `AE-vara-rulebooks-overview`
   - `AE-vara-aml-cft-rulebook`
   - `AE-vara-company-rulebook`
   - `AE-vara-public-register`
   - `AE-vara-news` only if it is regulatory update content, not marketing news.
   Current paths are nav-shell or stale. Look for official PDF/document URLs or stable rendered selectors.

3. DFSA/DIFC selectors:
   - `AE-dfsa-published-decisions`
   - `AE-dfsa-enforcement-regulatory-actions`
   - `AE-dfsa-consultation-papers`
   - `AE-difc-data-protection`
   - `AE-difc-legal-database`
   Current checks are nav-shell, selector stale, or access-blocked.

4. CBUAE non-rulebook alternates:
   - `AE-cbuae-publications`
   - `AE-cbuae-circulars`
   - `AE-cbuae-aml-cft`
   Keep ACCESS_BLOCKED if public access cannot be verified without bypassing protections.

Cycle requirements:

1. Run clean git gate before edits.
2. Add fixture tests before adapter changes.
3. Use Playwright DOM/XHR investigation for at least 15 candidates across at least 3 weak-zone batches.
4. Save evidence only after strong no-save q>=60, not nav-shell, not shallow, unique hash, low/controlled noise, can_save=true.
5. Require two stable baseline runs and mass-monitor dry-run `MONITOR_OK`.
6. Emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only after all gates pass.
8. Update scoreboard, work queue, truth docs, validators, and tests.
9. Run full validation and commit/push only after validation passes.

Do not stop after one source if more safe candidates can be processed.

Final output must include counts before/after, sources activated, tests added, validation result, commit hash, why fewer than 50, and next exact task.

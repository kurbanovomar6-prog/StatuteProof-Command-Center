# Next Autonomous Execution Prompt

Continue the StatuteProof UAE 50-source activation program from the committed state after the batch continuation that activated five new sources.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 33 enabled UAE sources.
- 29 readiness-supported active sources.
- 4 under extraction remediation.
- 50 has not been reached; 21 more proof-backed sources are needed.

Latest proven additions:

1. `AE-sca-corporate-governance` — `table`, q=60, two stable evidence runs, mass-monitor `MONITOR_OK`.
2. `AE-adgm-dp-guidance` — `custom_element`, q=62, two stable evidence runs, mass-monitor `MONITOR_OK`.
3. `AE-adgm-fsra-enforcement` — `custom_element`, q=62, two stable evidence runs, mass-monitor `MONITOR_OK`.
4. `AE-sca-aml-cft` — `sca_listing`, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.
5. `AE-dfsa-rulebook-thomsonreuters` — `dfsa_rulebook` with `article` selector, q=65, two stable evidence runs, mass-monitor `MONITOR_OK`.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim 50.

Next highest-leverage batch:

1. ADGM alternate listing/card selectors:
   - `AE-adgm-dp-regulatory-actions`
   - `AE-adgm-media-announcements`
   - `AE-adgm-listing-announcements`
   These pages contain rendered content but current selectors collapse to heading-only or global service/navigation links. Inspect custom elements and card/listing components with Playwright, then build a stricter ADGM announcement/listing adapter if needed.

2. UAE FIU SPA/XHR/direct document discovery:
   - `AE-uaefiu-aml-cft-laws`
   - `AE-uaefiu-laws-regulations`
   - `AE-uaefiu-publications`
   Current routes are NAV-shell or duplicate aliases. Use Playwright network capture and official document endpoints only. Do not bypass access controls.

3. VARA rulebook/PDF remediation:
   - `AE-vara-rulebooks-overview`
   - `AE-vara-aml-cft-rulebook`
   - `AE-vara-company-rulebook`
   Current routes are NAV-shell. Look for official PDF/document links or stable rendered selectors.

4. CBUAE official public alternates:
   - `AE-cbuae-circulars`
   - `AE-cbuae-publications`
   Keep ACCESS_BLOCKED if public access cannot be verified without bypassing protections.

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

Do not stop after one source if more safe candidates can be processed.

Final output must include counts before/after, sources activated, tests added, validation result, commit hash, why fewer than 50, and next exact task.

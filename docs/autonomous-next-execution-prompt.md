# Next Autonomous Execution Prompt

Continue the StatuteProof UAE 50-source activation program from the weak-zone elimination commit.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 46 enabled UAE sources.
- 42 readiness-supported active sources.
- 4 under extraction remediation.
- 50 has not been reached; 8 more proof-backed sources are needed.

Latest proven additions:

1. `AE-vara-rulebook-updates` — official VARA rulebook revision listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
2. `AE-dfsa-consultation-current` — current official DFSA consultation listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
3. `AE-dfsa-enforcement-decisions-current` — official DFSA enforcement decisions listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
4. `AE-dfsa-regulatory-actions-current` — official DFSA regulatory actions listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
5. `AE-cbuae-retail-payment-services-rulebook` — official CBUAE rulebook document listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
6. `AE-dfsa-consultation-paper-165` — official-linked DFSA Thomson Reuters consultation paper, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
7. `AE-dfsa-notice-supervisory-review` — official-linked DFSA Thomson Reuters supervisory review page, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
8. `AE-cbuae-amlcft-rulebook-doclist` — official CBUAE AML/CFT rulebook document listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
9. `AE-cbuae-amlcft-entire-section-doclist` — official CBUAE AML/CFT entire-section document listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.
10. `AE-cbuae-consumer-protection-rulebook-doclist` — official CBUAE consumer-protection document listing, q=65, two stable proof runs, mass-monitor `MONITOR_OK`.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim 50.

Next highest-leverage batch:

1. Direct official PDF extraction:
   - VARA PDF files under `rulebooks.vara.ae/sites/default/files/...`.
   - Current Playwright path returns shallow/no text for direct PDFs.
   - Implement a safe PDF fetch/extraction path or hold if PDFs are scanned/unsupported.

2. Remaining VARA official rulebook pages:
   - `AE-vara-aml-cft-controls`
   - `AE-vara-compliance-risk-rulebook` (held because mass-monitor dry-run produced `QUALITY_DROP` under static extraction)
   - VARA public register only if stable rows render publicly

3. CBUAE remaining rulebook pages:
   - Stored Value Facilities
   - Complaints Management
   - Open Finance / Payment Token / RPSCS pages if official rulebook endpoints are found

4. DIFC selector/access remediation:
   - DIFC data protection
   - DIFC consultation papers
   - DIFC laws/legal database only if public unauthenticated access works

5. ADGM alternate components:
   - Data Protection regulatory actions
   - Listing authority announcements
   - RA notices / AML quick guides replacement URLs

6. UAE FIU leftovers:
   - Press releases only if regulatory and not noisy
   - Strategic analysis/NRA direct document endpoints only if unique and not duplicate hub shells

Cycle requirements:

1. Run clean git gate before edits.
2. Add fixture tests before adapter behavior changes.
3. Test at least 20 candidates across at least 3 remaining weak-zone batches.
4. Save evidence only after strong no-save q>=60, not nav-shell, not shallow, unique hash, low/controlled noise, can_save=true.
5. Require two stable baseline runs and mass-monitor dry-run `MONITOR_OK` with no unresolved hash drift.
6. Emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only after all gates pass.
8. Update scoreboard, work queue, truth docs, validators, and tests.
9. Run full validation and commit/push only after validation passes.

Do not stop after one source if more safe candidates can be processed.

Final output must include counts before/after, sources activated, tests added, validation result, commit hash, why fewer than 50, and next exact task.

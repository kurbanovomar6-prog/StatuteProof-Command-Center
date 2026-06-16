# Next Autonomous Execution Prompt

Continue the StatuteProof UAE source hardening program after the post-50 hardening sprint.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 66 enabled UAE sources.
- 62 readiness-supported active sources.
- 4 under extraction remediation.
- 50-source minimum has been reached.
- Work queue has 50 activation-ready rows.

Latest proven additions and hardening:

- 20 proof-backed CBUAE/DFSA official rulebook and guidance sources were activated in the final-8 sprint.
- All activated sources passed strong no-save, two proof/baseline runs, mass-monitor dry-run `MONITOR_OK`, and six agent gates.
- Post-50 hardening tested 33 non-CBUAE candidate/config checks across VARA, DFSA, DIFC, ADGM/FSRA, UAE FIU, and SCA.
- 5 non-CBUAE strong no-save passes were found, but no new source was activated because the strong ADGM/SCA candidates duplicated already active URLs, DFSA MLRO evidence save was not reproducible, and DFSA AML/CTF root still drifts between evidence and monitor paths.
- `AE-dfsa-aml-ctf-sanctions` remains held: evidence hash `d66b892...`, monitor hash `468409...`, `change_detected=true` when the expected hash is set.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim "60 validated sources."

Next highest-leverage task:

1. **Diversify the 50+ pack beyond CBUAE concentration**
   - Implement direct official PDF extraction for VARA rulebook PDFs.
   - Retest VARA AML/CFT, company, market conduct, technology, transfer/settlement, and compliance/risk rulebooks using direct PDF URLs or official PDF listings, not nav-shell framework pages.
   - Activate only if proof/baseline/dry-run/gates pass.

2. **DIFC access/selector remediation**
   - Data protection.
   - Consultation papers.
   - Legal database.
   - Build fixture-backed listing/table extraction for pages that returned `LISTING_ADAPTER_REQUIRED` or `TABLE_ADAPTER_REQUIRED`.
   - Keep blocked if public unauthenticated access still fails.

3. **DFSA deterministic hash fix**
   - Build a fixture from the `AE-dfsa-aml-ctf-sanctions` evidence output and monitor output.
   - Make `dfsa_notice_listing` stable for root AML/CTF page ordering/chrome.
   - Do not activate until mass-monitor dry-run with `normalized_hash` returns `change_detected=false`.

4. **ADGM alternate components**
   - Data protection regulatory actions.
   - Listing authority announcements.
   - Media/regulatory announcements.
   - Build component-specific extraction only if content is meaningful and not page chrome.

5. **Operator UX**
   - Wire a generated source-readiness summary artifact so validators, docs, and frontend counts do not require manual constant edits.
   - Implement Acknowledge & Assess backend persistence and tests before any visible button.

Cycle requirements:

1. Run clean git gate before edits.
2. Add fixture tests before adapter behavior changes.
3. Do not activate no-save-only, one-run-only, drift, nav-shell, shallow, duplicate, or high-noise sources.
4. Save evidence only after strong no-save q>=60.
5. Require two stable baseline runs and mass-monitor dry-run `MONITOR_OK`.
6. Emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
7. Update `sources.json` only after all gates pass.
8. Update scoreboard, work queue, truth docs, validators, and tests.
9. Run full validation and commit/push only after validation passes.

Final output must include whether diversification improved, sources activated, tests added, validation result, commit hash, and remaining weak zones.

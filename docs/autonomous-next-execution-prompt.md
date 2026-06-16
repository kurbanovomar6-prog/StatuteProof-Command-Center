# Next Autonomous Execution Prompt

Continue the StatuteProof UAE source activation program after the final-8 sprint.

Work only inside `/Users/kurbnovomar/StatuteProof-Command-Center`.

Current verified truth:

- 66 enabled UAE sources.
- 62 readiness-supported active sources.
- 4 under extraction remediation.
- 50-source minimum has been reached.
- Work queue has 50 activation-ready rows.

Latest proven additions:

- 20 proof-backed CBUAE/DFSA official rulebook and guidance sources were activated in the final-8 sprint.
- All activated sources passed strong no-save, two proof/baseline runs, mass-monitor dry-run `MONITOR_OK`, and six agent gates.
- `AE-dfsa-aml-ctf-sanctions` was held despite evidence because mass-monitor dry-run detected hash drift.

Do not deploy, expose secrets, send customer messages, bypass login/CAPTCHA/paywalls, fake evidence, weaken validators, or claim "60 validated sources."

Next highest-leverage task:

1. **Diversify the 50+ pack beyond CBUAE concentration**
   - Implement direct official PDF extraction for VARA rulebook PDFs.
   - Retest VARA AML/CFT, company, market conduct, technology, transfer/settlement, and compliance/risk rulebooks.
   - Activate only if proof/baseline/dry-run/gates pass.

2. **DIFC access/selector remediation**
   - Data protection.
   - Consultation papers.
   - Legal database.
   - Keep blocked if public unauthenticated access still fails.

3. **ADGM alternate components**
   - Data protection regulatory actions.
   - Listing authority announcements.
   - Media/regulatory announcements.
   - Build component-specific extraction only if content is meaningful and not page chrome.

4. **Operator UX**
   - Wire a generated source-readiness summary artifact so validators, docs, and frontend counts do not require manual constant edits.
   - Add an admin review panel for `pending_validation` custom sources if frontend work is chosen.

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

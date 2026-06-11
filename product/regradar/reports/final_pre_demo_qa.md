# Final Pre-Demo QA

## 1. Verdict

Controlled pre-demo QA passed on build, compile, whitespace, claims grep, demo/fake wording grep, and active UAE-first web UI checks.

No P0 blocker was found in the active web app or API for a guided prospect demo.

The product is safe for a controlled, guided prospect demo if the operator avoids archived historical sample files and does not present automatic scheduled delivery as active. It is not yet ready for an unguided production launch.

Remaining P1 items:

- `DashboardHome.jsx` still contains stale wording: `Brief delivery` with `personalized routing is next step`, even though manual sample brief delivery and reviewed alert preview delivery now exist.
- `reports/source_readiness_vasp_crypto_sample.html` appears to be a stale generated artifact from before the latest responsive template polish. Regenerate it before using it with a prospect.
- Internal RegRadar naming remains in backend CLI/docstrings and one frontend data comment. It is not visible in the active web UI, but internal files should not be shown in a branded prospect demo.

## 2. Git state

Commands run:

```bash
git status
git log --oneline -15
```

Current branch:

- `main`
- Ahead of `origin/main` by 17 commits.

Latest commits inspected:

- `f2a3999 style(app): polish alert and brief preview copy`
- `cf2f2aa style(ui): fix auth and pilot workspace copy`
- `07fc4f6 feat(reports): add source readiness review generator`
- `ec168a0 fix(auth): harden client account endpoints`
- `0f67974 feat(auth): add reviewed alert routing preview`
- `802822f style(app): make demo workspace UAE-first`
- `b77bc3a style(app): clarify sample alert and brief previews`
- `ceb5669 feat(auth): add user Telegram sample brief delivery`
- `6e9c4b8 style(app): polish client workspace experience`
- `6bf9f90 feat(landing): add buyer source packs`
- `865d2ba feat(auth): add Telegram account pairing`
- `0a76eec style(landing): unify dark trust experience`
- `d03ab48 feat(auth): persist client profile settings`
- `5a46818 feat(auth): add real account foundation`
- `0fc6516 chore(sources): test ADGM FSRA HTML proof diff`

Untracked files existed before this report and were left untouched:

- `repopack-output.txt`
- `reports/current_state_qa_after_auth_d2_and_design_4a.md`
- `reports/full_site_app_qa_review.md`
- `reports/recap_last_5_hours.md`
- `reports/source_readiness_vasp_crypto_sample.html`
- `reports/statuteproof_professional_website_upgrade_plan.docx`
- `reports/statuteproof_professional_website_upgrade_plan.md`
- `reports/~$atuteproof_professional_website_upgrade_plan.docx`

This QA report is the only file created during this audit.

## 3. Validation results

Commands run:

```bash
python3 -m compileall app run.py -q
cd web && npm run build
git diff --check
```

Results:

- Backend compile: PASS
- Frontend build: PASS
- Diff whitespace check: PASS

Frontend build note:

- Vite build completed successfully.
- Existing Node warning observed: `[DEP0205] DeprecationWarning: module.register() is deprecated`.
- This is not a demo blocker.

## 4. Brand consistency

Command run:

```bash
grep -R "RegRadar\|Reg Radar\|Ruflo" web/src app scripts app/templates web/index.html requirements.txt run.py --exclude-dir=node_modules || true
```

Findings:

- No active client-facing web UI copy was found using `RegRadar`, `Reg Radar`, or `Ruflo`.
- One frontend data comment still references `RegRadar` in `web/src/data/watchlistOptions.js`.
- Multiple backend/internal modules, CLI help strings, docstrings, and `requirements.txt` still contain historical `RegRadar` naming.
- Binary `__pycache__` matches were also returned after compile.

Classification:

- Client-facing issue: none found in active web UI.
- Internal/historical acceptable: backend docstrings, CLI output, requirements text, pycache.
- Must fix before demo: only if showing CLI/backend internals to a prospect. Otherwise not a P0.

## 5. Demo/fake wording

Command run:

```bash
grep -R "demo workspace\|demo account\|any password\|fake workspace\|mock account\|next pilot step" web/src app/templates --exclude-dir=node_modules || true
```

Result:

- PASS. No direct matches.

Source inspection note:

- `DashboardHome.jsx` still has related stale copy with different casing/wording: `Next pilot step` and `personalized routing is next step`.
- This is not fake-account wording, but it is stale after Auth D1/D2 and should be polished.

## 6. UAE-first consistency

Command run:

```bash
grep -R "Turkey\|Kazakhstan\|Georgia\|Azerbaijan\|Saudi Arabia\|Armenia\|TCMB\|MASAK\|ARDFM\|National Bank KZ\|Matsne\|Revenue Service\|CBAR\|CBA Armenia\|SAMA\|CIS\|Caucasus" web/src app/templates reports/source_readiness_*.html reports/sample* --exclude-dir=node_modules || true
```

Findings:

- No non-UAE default demo data was found in active `web/src` app code.
- No non-UAE references were found in `reports/source_readiness_vasp_crypto_sample.html`.
- Matches were found in `reports/sample_compliance_brief_en.md`, which contains old illustrative Turkey/MASAK and Kazakhstan/ARDFM sample material.

Classification:

- Active client-facing issue: none found in the app.
- Archived/historical acceptable: `reports/sample_compliance_brief_en.md`.
- Demo caution: do not show or send the old sample compliance brief in a UAE-first StatuteProof prospect demo.

## 7. Claims safety

Command run:

```bash
grep -R "35 active\|complete UAE coverage\|all UAE regulators\|never miss\|guaranteed compliance\|real-time alerts\|production delivery active\|trusted by\|live client data\|delivered to your team\|personalized alerts active\|weekly briefs delivered\|automatic scheduled delivery is enabled" web/src app scripts app/templates reports/source_readiness_*.html --exclude-dir=node_modules || true
```

Result:

- PASS. No unsafe positive claims were found.

Notes:

- “Not legal advice” appears as safe disclaimer language where expected.
- Wording that explicitly says automatic scheduled delivery is not enabled is safe.

## 8. Source Readiness report check

Checked file:

- `reports/source_readiness_vasp_crypto_sample.html`

Confirmed:

- StatuteProof branding is present.
- Title is `Source Readiness Review`.
- Limitations are prominent.
- `SAMPLE — ILLUSTRATIVE ONLY` is present.
- `NOT REAL DATA — NOT A REAL REGULATORY CHANGE` is present.
- `Not legal advice` disclaimer is present.
- Print CSS exists via `@media print`.
- No unsafe claims were found.

Issue:

- The generated sample report appears stale relative to the latest responsive template polish. It still uses older responsive CSS around `@media (max-width: 820px)`.
- The committed template may be newer, but this sample artifact should be regenerated before prospect use.

## 9. Endpoint/security check

Inspected:

- `app/api.py`

Confirmed:

- Global Telegram settings endpoints now return 403 through `_disabled_endpoint()`:
  - `GET /api/settings/telegram`
  - `POST /api/settings/telegram`
  - `POST /api/settings/telegram/test`
- In-memory rate limiting exists.
- Register and login are rate-limited.
- Contact is public but rate-limited and truncates user input.
- Source-test is public but rate-limited.
- Telegram pair generation is rate-limited.
- Per-user Telegram test is rate-limited and requires auth.
- Sample brief delivery is rate-limited and requires auth.
- Reviewed preview alert send is rate-limited and requires auth.
- Profile endpoints require auth.
- Telegram pairing endpoints require auth.
- Delivery endpoints require auth.
- Delivery and Telegram user endpoints do not accept `user_id` or `chat_id` from frontend body as trust sources.
- No automatic delivery loop or scheduler was enabled.
- `send_telegram_alert()` global/admin behavior was not changed by the reviewed hardening.

Residual security limitations:

- Rate limiting is in-memory and resets on process restart.
- CSRF tokens are not implemented; the current MVP relies on `SameSite=Strict` cookie behavior.
- Secure cookie behavior still requires production HTTPS review.
- `source-test` remains public, though rate-limited.
- `contact` remains public, though rate-limited.
- Legacy global Telegram helper methods still exist in code but are not reachable through active routes.
- `do_POST` route matching still uses direct `self.path` comparisons in several branches; `do_PUT` has the safer `urlparse(self.path).path` fix.

## 10. Frontend page review

Reviewed by source inspection:

- `LoginPage.jsx`
- `RegisterPage.jsx`
- `Problem.jsx`
- Landing components by grep/source context
- `DashboardHome.jsx`
- `SourcesPage.jsx`
- `AlertsPage.jsx`
- `AIBriefPage.jsx`
- `ReportsPage.jsx`
- `IntegrationsPage.jsx`
- `SettingsPage.jsx`

Findings:

- Login/Register no longer present fake demo account/workspace copy.
- Login/Register now describe a real StatuteProof pilot workspace.
- Problem section uses the dark premium style and UAE-first positioning.
- Alerts page correctly frames approved alert routing as reviewed/manual preview delivery.
- AI Brief page correctly says sample brief delivery can be tested from Integrations and weekly brief delivery remains roadmap.
- Reports page uses sample/readiness language and does not claim generated production reports.
- Integrations copy accurately distinguishes real Telegram pairing/test/sample/manual preview capabilities from automatic scheduled delivery.
- Settings language options are cleaned up for UAE-first MVP; Arabic support is planned/disabled rather than pretending Russian/Both are current options.
- Sources page clearly states custom sources request validation and do not activate production monitoring automatically.

Remaining frontend issues:

- `DashboardHome.jsx` has stale delivery summary copy: `Brief delivery` / `personalized routing is next step`.
- `DashboardHome.jsx` includes `Next pilot step` wording. It is not unsafe, but it is less precise after D1/D2.
- Login page has a visible `Forgot?` control with no password reset flow. This is a P2 UX issue.
- Some generated/report artifacts still contain historical RegRadar/non-UAE examples and must not be used in the StatuteProof UAE-first demo.

## 11. P0/P1/P2 remaining issues

P0:

- None found for a controlled, guided prospect demo.

P1:

- Update `DashboardHome.jsx` stale delivery status copy to reflect current manual delivery capabilities.
- Regenerate `reports/source_readiness_vasp_crypto_sample.html` from the latest source readiness template before showing or sharing it.
- Keep archived `reports/sample_compliance_brief_en.md` out of the demo flow because it contains old non-UAE examples and RegRadar wording.

P2:

- Internal/backend `RegRadar` naming remains in docstrings, CLI strings, comments, and requirements text.
- Login `Forgot?` control is visible without a password reset feature.
- `do_POST` path matching could be normalized with `urlparse` for consistency.
- Legacy global Telegram helper methods remain in code even though public routes are disabled.
- In-memory rate limiting is suitable for MVP but not robust production abuse prevention.

## 12. Can we show this to a prospect?

Yes, for a controlled and guided prospect demo.

Conditions:

- Use the active web app, not CLI/backend/internal files.
- Do not show archived non-UAE sample reports.
- Regenerate the source readiness sample from the latest template before using it.
- Be explicit that automatic scheduled delivery and weekly scheduled briefs are not enabled yet.
- Present delivery as:
  - real account system;
  - real saved profile;
  - real Telegram pairing;
  - real sample brief delivery;
  - real manual reviewed alert preview delivery;
  - no automatic production delivery yet.

Not safe yet:

- Unguided public demo.
- Production pilot without further security hardening.
- Claims of complete UAE coverage, real-time monitoring, guaranteed compliance, automatic personalized alerts, or scheduled weekly briefs.

## 13. Recommended next action

Recommended next sprint:

Design E4 / Pre-Demo Final Copy Sweep

Scope:

- Fix `DashboardHome.jsx` stale delivery status copy.
- Regenerate the source readiness sample artifact from the latest template.
- Hide or clearly archive old `reports/sample_compliance_brief_en.md` from demo materials.
- Optionally remove or disable the visible `Forgot?` control until password reset exists.

After that, the strongest technical follow-up remains:

Auth E2 Security Hardening

Scope:

- CSRF tokens or origin checks.
- Production Secure cookie review.
- Persistent/distributed rate limiting.
- Public endpoint abuse controls for contact/source-test.
- Admin-only replacement for disabled global Telegram settings.

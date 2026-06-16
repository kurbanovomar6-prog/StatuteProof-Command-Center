# Post-50 Hardening Plan

Date: 2026-06-16

## 1. Current Truth

Current honest source truth after commit `0aebd3d`:

- 66 enabled UAE official-source endpoints.
- 62 readiness-supported sources.
- 4 sources remain under extraction remediation.
- The 50-source threshold has been reached, but the pack still needs balance and commercial hardening.

## 2. Source Distribution By Regulator

Current readiness-supported active UAE sources from `product/regradar/sources.json`:

| Group | Count | Share |
| --- | ---: | ---: |
| CBUAE | 27 | 43.5% |
| ADGM/FSRA | 10 | 16.1% |
| DFSA | 8 | 12.9% |
| FIU/EOCN/AML | 7 | 11.3% |
| SCA | 4 | 6.5% |
| VARA | 3 | 4.8% |
| Federal/Legislation/Tax | 3 | 4.8% |
| Total | 62 | 100.0% |

## 3. Concentration Risk

CBUAE is now strong but overrepresented. That is commercially useful for banks and payment firms, but a balanced UAE compliance product must also show credible coverage for virtual assets, DIFC/DFSA, ADGM/FSRA, AML/FIU/EOCN, SCA, and relevant federal law/tax sources.

Current concentration risk: medium-high for broad UAE MLRO demos. The system is demo-credible, but a prospect may reasonably ask why VARA and DIFC are thin compared with CBUAE.

## 4. Weak Zones Still Remaining

- VARA direct PDF extraction and static drift control.
- DIFC selector/access remediation for laws, notices, enforcement, and data-protection pages.
- ADGM alternate components: media, announcements, data protection regulatory actions, and listing announcements.
- DFSA AML/CFT sanctions held source with dry-run hash drift.
- FIU leftovers that are shallow or duplicate aliases of activated hubs.
- CBUAE main-site access remains weaker than the official rulebook endpoint path.

## 5. Customer-Facing Truth Update Plan

Allowed copy:

- "66 enabled UAE official-source endpoints."
- "62 readiness-supported after proof, baseline, source-health, noise, and review gates."
- "4 sources remain under extraction remediation."
- "Monitoring intelligence only. Not legal advice."
- "Source health and remediation status are shown transparently."
- "No source is marked ready without evidence and repeat baseline checks."

Forbidden copy remains:

- "60 validated sources."
- "perfect parsing."
- "never miss updates."
- "guaranteed compliance."
- "legal advice."
- "official regulator certified."
- "any website can be parsed."

## 6. Demo-Readiness Plan

The demo should show:

- current source coverage with transparent remediation status;
- one proof-backed source update with evidence path, normalized hash, and source-health status;
- one held/remediation example to prove StatuteProof does not fake readiness;
- a clear "Monitoring intelligence only. Not legal advice." boundary;
- an Acknowledge & Assess workflow plan or minimal implementation.

## 7. Audit Workflow Plan

Prepare the "Acknowledge & Assess" MVP around:

1. open evidence-backed alert;
2. view source, diff, proof, hash, and source-health status;
3. write internal impact note;
4. choose impact level: no impact, monitor, policy review, escalate, external counsel review;
5. save an assessment record;
6. export or inspect the audit record later.

If implementation scope is too large for this hardening pass, create an exact execution plan and a sample audit-pack artifact only.

## 8. Validation Plan

Run:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- source discovery, activation, mass-source activation, mass-monitor, batch-onboarding, UAE source pack, UAE 50 working-source, parser quality, workspace, and Codex skills validators where present
- `git diff --check`

If frontend changes are made, also run the frontend build, lint, route validation, and pre-demo smoke script if present.

## 9. Commit Policy

Only commit after validation passes. Stage only files from this task. Do not stage runtime junk, secrets, broad source snapshots, customer messages, or unrelated files.

Commit message if validation passes:

`feat: harden post-50 UAE monitoring pack`

## 10. What Not To Touch

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No `.env` printing or committing.
- No Telegram/email/customer messages.
- No private portals, CAPTCHA bypass, paywall bypass, or credentialed scraping.
- No fake source diversity.
- No source activation from no-save-only, one-run-only, shallow, duplicate, drifted, high-noise, or high-health-risk sources.

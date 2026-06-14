# StatuteProof Sites Visual Upgrade Review

Date: 2026-06-14

## Preview Method

- Sites used: no. The Sites plugin/tool was not available and was not listed as an install candidate.
- Production deployment: not performed.
- Cloudflare/DigitalOcean: not modified.
- Local preview used: `http://127.0.0.1:5174/`
- API used for authenticated app QA: existing local API on `http://127.0.0.1:5001`

## Desktop Visual QA

Checked routes:

- `/`
- `/pricing`
- `/source-readiness-review`
- `/login`
- `/register?plan=founding_pilot`
- `/app/dashboard`
- `/app/sources`
- `/app/source-lab`
- `/app/evidence`
- `/app/briefs`
- `/app/billing`

Findings:

- Homepage preserves the existing StatuteProof logo and octopus mark.
- Dark navy direction is preserved and strengthened with clearer surfaces, borders, spacing, and cyan accents.
- Header actions are visually distinct: Login is subtle, Register is secondary, Request Source Review is primary.
- Hero headline and subheadline use approved proof-first wording.
- Hero evidence card is clearly labeled `SAMPLE / DEMO - not a real regulatory update`.
- Homepage readiness language uses `13 enabled / 10 confirmed / 3 under extraction remediation` and avoids overstating the pack as fully confirmed.
- Homepage evidence and dashboard-preview source tables use `13 enabled / 10 confirmed / 3 under extraction remediation` and are clearly labeled sample/demo where illustrative.
- No public homepage source table shows stale readiness counts.
- Confirmed source identities match the current readiness report: UAE Ministry of Finance and UAE FIU Circulars are included; disabled aliases CBUAE Circulars and ADGM FSRA Rules are not shown as confirmed.
- Source transparency matrix now separates DIFC Laws readiness from DFSA Rulebook and DFSA Regulatory Notices remediation.
- Alert-profile/source-pack sections no longer imply DFSA, ADGM/FSRA rulebook layers, or the UAE FIU homepage are confirmed for monitoring before remediation/readiness review.
- Public evidence/demo cards were converted to dark navy surfaces.
- Public sample source-status counts are static sample/readiness-pack counts, not raw API totals.
- Pricing page uses the current honest packaging: Free Source Readiness Review, $199 Founding Pilot, $399 UAE Monitor, Consultant talk-to-us.
- Billing page states manual activation and no self-serve Stripe checkout.
- Dashboard shows source readiness, evidence health, review queue, plan state, and next actions.
- Dashboard no longer shows stale `Evidence Preview` or `Founding pilot` labels for the free readiness plan.
- Sources page explains validation before activation and routes `Add custom source` to `/app/source-lab`.
- Source Lab disables `Test Source` until required fields and public-source confirmation are complete.
- Source Lab exposes readiness status/result fields and blocks activation behind evidence/readiness gates.
- Evidence page uses live evidence records when the endpoint is available and labels them as live records.
- Brief previews are clearly sample/demo, with PDF export and delivery actions disabled behind activation/review gates.
- Source registry and generated/static readiness artifacts now align with the customer-facing 13 enabled / 10 confirmed / 3 under extraction remediation story.
- Login/register pages render as unauthenticated routes and preserve `/login` and `/register?plan=...` URLs.
- Unauthenticated `/app/dashboard` redirects to `/login`.

## Button And Route QA

Verified:

- Header Pricing -> `/pricing`
- Login -> `/login`
- Register -> `/register`
- Request Source Review -> `/source-readiness-review`
- Hero Request a free source readiness review -> `/source-readiness-review`
- Hero View sample evidence brief -> `/#evidence`
- Pricing Founding Pilot CTA -> `/register?plan=starter_pilot`
- Pricing UAE Monitor CTA -> `/register?plan=professional`
- Sources Add custom source -> `/app/source-lab`
- Protected `/app/dashboard` when unauthenticated -> `/login`
- Homepage sample evidence CTA -> `/#evidence`; retest confirmed the evidence table shows 13 enabled, 10 confirmed, 3 under extraction remediation, with no stale readiness count.
- Dashboard preview retest confirmed no old DFSA/UAE FIU confirmed demo rows and no raw API source total is shown as enabled coverage.
- Authenticated Sources retest confirmed DFSA Rulebook, DFSA Regulatory Notices, and UAE FIU Homepage render as `Needs remediation` / `Review`.
- Rendered identity scan confirmed no stale `CBUAE Circulars` or `ADGM FSRA Rules` confirmed rows on the homepage or `/app/sources`.

## Mobile QA

Mobile viewport inspection was not feasible in the available in-app browser surface because no viewport resizing capability was exposed. Responsive classes and mobile menu structure were preserved in code, but this run should be followed by a mobile viewport review in a browser with resize/device emulation.

## Legal-Safety QA

Checked for forbidden positive claims:

- No AI lawyer positioning found in the touched UI.
- No promise of compliance outcomes found.
- No prevent-fines promise as a promise.
- No regulator partnership or approval claim.
- No fake customer logos or testimonials added.
- Negative legal-boundary disclaimers remain present.

## Final Gate Results

- Legal Language gate: PASS.
- QA / Critic gate: PASS.
- Source Monitor gate: PASS.
- Source readiness consistency: PASS for public/app surfaces, metadata, static samples, source readiness reports, generator copy, and the three remediation source registry statuses.

## Final Validation Results

- `npm run lint` - passed with 0 errors and the known TanStack Table React compiler warning in `DashboardPreview.jsx`.
- `npm run build` - passed.
- `node scripts/validate-routes.mjs` - passed.
- `python -m compileall product/regradar` - not available because the `python` binary is missing on this machine.
- `python3 -m compileall product/regradar` - passed.
- `python3 tools/validate_workspace.py` - passed.
- `python3 tools/validate_codex_skills.py` - passed.
- `git diff --check` - passed.

## Remaining Visual Issues

- Mobile viewport still needs a direct visual review.
- Some older app sections outside the core upgrade, such as integrations/sample alerts/reports, can still receive additional polish.
- Browser screenshot file saving was not available through the in-app browser runtime, so visual notes are documented here rather than attached as committed image artifacts.
- Production deployment was not performed and `statuteproof.com` was not changed.

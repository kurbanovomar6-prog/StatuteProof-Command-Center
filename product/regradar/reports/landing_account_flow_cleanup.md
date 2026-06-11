# Landing Account Flow Cleanup

## 1. Verdict

Landing conversion now routes prospects into the real account flow:

Landing page → Create pilot workspace → Register → Onboarding → Dashboard.

The long public source readiness/contact form was removed from the visible landing page and replaced with an account-first CTA panel. Backend auth, profile, Telegram, delivery and source monitoring behavior were not changed.

## 2. Files changed

- `web/src/App.jsx`
- `web/src/components/Header.jsx`
- `web/src/components/Hero.jsx`
- `web/src/components/Contact.jsx`
- `web/src/components/Coverage.jsx`
- `web/src/components/SourceTransparencyMatrix.jsx`
- `web/src/components/BuyerSourcePacks.jsx`
- `web/src/components/Pricing.jsx`
- `web/src/components/AddYourSource.jsx`
- `web/src/components/auth/RegisterPage.jsx`
- `web/src/components/app/OnboardingPage.jsx`
- `web/src/data/mockData.js`
- `reports/landing_account_flow_cleanup.md`

## 3. Landing CTA changes

Header:

- Primary CTA is now `Create pilot workspace`.
- Secondary link remains `Sign in`.
- Both route to existing app views without React Router.

Hero:

- Primary CTA is now `Create pilot workspace`.
- Secondary CTA is now `Sign in`.

Other landing CTAs:

- Source transparency, buyer source packs, coverage and pricing CTAs now route to account creation.
- Old visible `Request Source Review` wording was removed from active landing CTAs.

## 4. Contact form replacement

`Contact.jsx` no longer renders the long public form.

It now renders a dark CTA panel:

- `Create your UAE source readiness workspace`
- account-first body copy;
- source readiness bullets;
- `Create pilot workspace` primary button;
- `Sign in` secondary button;
- clear not-legal-advice / source-validation disclaimer.

The backend `/api/contact` endpoint was not removed or changed.

## 5. Register/onboarding flow

Register:

- Keeps the short real account flow.
- Collects optional full name, work email, password, company and industry.
- Continues to use existing backend register/session behavior.

Onboarding:

- Continues to collect company, email, UAE market profile and industry focus.
- Now also collects UAE source layers of interest:
  - CBUAE
  - VARA
  - DFSA
  - ADGM / FSRA
  - UAE FIU
  - Ministry of Finance
  - UAE Legislation Portal
  - DIFC Laws
  - Ministry of Economy
  - FTA
  - Capital Market Authority / former SCA [Limited]
  - Other
- Saves source-layer selections through the existing backend profile `topics` field.
- No backend schema change was made.

## 6. Claims safety result

Stale CTA grep:

```bash
grep -R "Request Source Review\|Your Source Readiness Review request was received\|Get a free source readiness review" web/src --exclude-dir=node_modules || true
```

Result:

- PASS. No matches.

Unsafe claims grep:

```bash
grep -R "complete UAE coverage\|all UAE regulators\|real-time alerts\|guaranteed compliance\|production delivery active\|weekly briefs delivered\|legal advice" web/src --exclude-dir=node_modules || true
```

Result:

- Only safe `not legal advice` disclaimer language matched.
- No positive unsafe claim was added.

Pricing copy was also tightened so it does not imply automatic weekly or monthly delivery.

## 7. Validation result

Commands run:

```bash
cd web && npm run build
python3 -m compileall app run.py -q
git diff --check
```

Results:

- Frontend build: PASS
- Backend compile: PASS
- Diff whitespace check: PASS

Note:

- Vite still prints the existing Node deprecation warning for `module.register()`. Build succeeds.

## 8. Remaining follow-ups

- Public `/api/contact` remains available for future lead capture, but it is no longer the visible primary landing flow.
- Optional full name is collected in Register UI, but the current backend account schema does not persist a separate name field.
- Some inactive/legacy components still scroll to `#contact`; this now lands on the account CTA panel, not a form.
- No automatic delivery, scheduler, backend auth security change, source activation or source monitoring behavior was added.

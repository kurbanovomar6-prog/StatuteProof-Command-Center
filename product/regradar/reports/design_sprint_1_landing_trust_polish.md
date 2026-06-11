# Design Sprint 1 — Landing Trust & Visual Consistency Polish

## 1. Verdict

Design Sprint 1 unified the landing page around a darker, more consistent B2B RegTech trust experience. The changes focus on visual consistency, source transparency, and safer trust language.

No backend/auth files were touched.
Telegram pairing UI was not implemented.
No fake testimonials, logos, clients, or social proof were added.

## 2. Files changed

- `web/src/components/Header.jsx`
- `web/src/components/Hero.jsx`
- `web/src/components/WithoutWith.jsx`
- `web/src/components/HowItWorks.jsx`
- `web/src/components/Coverage.jsx`
- `web/src/components/TrustLayer.jsx`

## 3. Visual changes made

- Added a clear `Sign in` path to the desktop and mobile header while keeping the existing source review CTA.
- Changed the duplicate `The difference` badge in `WithoutWith` to `Workflow comparison`.
- Converted `HowItWorks` from a light section to a dark source-proof workflow section with dark panels and subtle cyan step badges.
- Converted `Coverage` into a dark `Source transparency` section with dark tables and safe status badges.
- Added the microcopy: `Mapped does not mean active. Sources enter client monitoring only after access, extraction and proof/diff validation.`
- Removed the white embedded card from `TrustLayer` and replaced it with a dark illustrative evidence-brief panel.
- Added small dashboard mockup annotations: `Source proof`, `Human review`, `Coverage status`, and `Limitations disclosed`.
- Replaced the mockup `TG Alert` badge with `Review gate` to avoid implying Telegram delivery maturity.

## 4. Claims safety result

- No fake testimonials added.
- No fake client logos added.
- No source coverage claims changed to active.
- No `35 active sources` claim added.
- No full UAE coverage claim added.
- No guaranteed compliance or never-miss claim added.
- No real-time alert claim added.
- No legal advice claim added.

The unsafe-claims grep returned no matches for the requested patterns.

## 5. What was deliberately not changed

- Backend auth was not touched.
- Profile persistence was not touched.
- Telegram pairing was not implemented.
- Telegram secrets and settings were not touched.
- Source monitoring behavior was not changed.
- Sources were not activated.
- Pricing numbers were not changed.
- No broad frontend rewrite was performed.

## 6. Remaining design recommendations

- Consider a later focused pass on mobile spacing after real device/browser review.
- Consider replacing illustrative dashboard mock data with a clearly labeled static screenshot once the product dashboard stabilizes.
- Consider a future verified outcomes section only when real pilot data can be used safely.

## 7. Validation result

- `cd web && npm run build` passed.
- `git diff --check` passed.
- Unsafe-claims grep passed with no matches.
- Local Vite server started successfully at `http://127.0.0.1:5173/`.
- In-app browser verification was attempted, but the `iab` browser backend was unavailable in this session.

# StatuteProof Sites Visual Upgrade Plan

Date: 2026-06-14

## 1. Current frontend framework

- App: `product/regradar/web`
- Framework: React 19 with Vite 8
- Styling: Tailwind CSS 4 plus shared custom classes in `src/index.css`
- Routing: view-state routing inside `src/App.jsx`; authenticated app page-state routing inside `src/components/app/AppShell.jsx`
- Icons: `lucide-react` is already installed and used throughout
- API proxy: Vite proxies `/api` to `http://127.0.0.1:5001`

## 2. Current route map

The app does not currently use React Router. Routes are view states:

- `/` should map to `landing`
- `/login` should map to `login`
- `/register` should map to `register`
- `/pricing` should map to `pricing`
- `/source-readiness-review` should map to `source-readiness-review`
- `/app/dashboard` should map to `app` with dashboard page
- `/app/sources` should map to `app` with sources page
- `/app/source-lab` should map to `app` with Source Lab page
- `/app/evidence` should map to `app` with Evidence page
- `/app/billing` should map to `app` with Billing page
- `/app/settings` should map to `app` with Settings page
- `/app/choose-plan` should map to `choose-plan`

Implementation plan: keep the current view-state architecture but add browser history/path synchronization so the required URLs work without adding a router dependency.

## 3. Pages to upgrade

- Public homepage: header, hero, problem, source coverage, evidence, pricing, footer
- Public pricing page
- Public source readiness review page
- Login page
- Register page
- Dashboard home
- App shell/sidebar/topbar
- Sources page and source-map custom source modal
- Source Lab page
- Evidence page
- Brief preview page
- Billing page

## 4. Visual design problems

- The visual language is dark and aligned with the brand, but still reads like generic Tailwind SaaS: centered hero, uniform rounded cards, repeated soft borders, and light hierarchy.
- The hero evidence card is useful but too small and not premium enough for a first-viewport trust signal.
- Source coverage tables use source-readiness wording inconsistently. The current parser/source registry story is 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.
- Pricing cards on the homepage still use old `mockData.js` prices and names (`$99`, `$249`, `$499`, `Profile Pilot`, `Custom Profile`) while the current honest pricing is Free / $199 / $399 / Talk to us.
- App tables are functional but plain; they need clearer badges, denser enterprise hierarchy, and stronger status grouping.
- Auth pages use a standard split-panel layout and do not show enough evidence/product specificity.
- Source Lab should become a standout product screen with a strong control panel, test gating, result analysis, and activation limits.

## 5. UX/navigation problems

- Required URLs do not consistently exist as browser paths because the app relies on state only.
- App subpages are not deep-linkable yet.
- Some CTAs navigate to generic registration even when the intended route is source readiness review, pricing, billing, or source lab.
- Footer legal links use `href="#"`, which is a dead link pattern.
- Login "Forgot password?" appears actionable despite no reset flow.
- Homepage secondary hero CTA routes to registration instead of the sample evidence/brief area.

## 6. Button/CTA problems

- Header primary button says "Request Review" instead of the specified "Request Source Review".
- Homepage pricing CTAs route generically and use stale plan names.
- Source Lab has only "Test"; it needs clear "Test Source", "Save Source", and disabled activation language.
- Billing upgrade CTAs are mailto links. They can remain manual, but copy must explicitly say manual activation after source readiness review.
- Disabled controls need clear labels/tooltips or explanatory text.

## 7. Inconsistent labels

- `Evidence Preview` vs. `Source Readiness Review` appears in fallback plan state.
- Prior active/validated source-status phrasing overclaims current source readiness.
- `13 enabled UAE sources under evidence-readiness review` is safe only when paired with the current registry count: 9 readiness-supported, 4 under extraction remediation.
- `Sample Alerts`, `Brief Previews`, and evidence cards should consistently say `SAMPLE / DEMO — not a real regulatory update`.

## 8. Sample/demo overclaim risks

- Sample evidence records use plausible source names and hashes. They must keep a prominent sample/demo badge near the top of every card and page.
- Brief previews can look customer-ready. Delivery actions must remain disabled or clearly marked preview-only unless backed by an approved integration flow.
- Source Lab no-save tests must not claim evidence records; only saved/scheduled monitoring runs create proof artifacts.
- Homepage/sample brief sections must not imply live customer delivery or regulator approval.

## 9. Exact files to change

Primary implementation files:

- `product/regradar/web/src/index.css`
- `product/regradar/web/src/App.jsx`
- `product/regradar/web/src/components/Header.jsx`
- `product/regradar/web/src/components/Hero.jsx`
- `product/regradar/web/src/components/Problem.jsx`
- `product/regradar/web/src/components/Coverage.jsx`
- `product/regradar/web/src/components/Pricing.jsx`
- `product/regradar/web/src/components/Footer.jsx`
- `product/regradar/web/src/components/PricingPage.jsx`
- `product/regradar/web/src/components/SourceReadinessReviewPage.jsx`
- `product/regradar/web/src/components/auth/LoginPage.jsx`
- `product/regradar/web/src/components/auth/RegisterPage.jsx`
- `product/regradar/web/src/components/app/AppShell.jsx`
- `product/regradar/web/src/components/app/AppSidebar.jsx`
- `product/regradar/web/src/components/app/AppTopbar.jsx`
- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/app/SourceLabPage.jsx`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/BillingPage.jsx`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/app/AIBriefPage.jsx`
- `product/regradar/web/src/data/mockData.js`
- `product/regradar/web/src/hooks/usePlan.js`

Docs to create:

- `docs/sites-visual-upgrade-review.md`
- `docs/sites-premium-visual-upgrade-report.md`

No parser, source-monitoring, evidence-writing, Cloudflare, DigitalOcean, or production deployment files should be changed.

## 10. Validation/build command

Run, in order where feasible:

- `npm run build` from `product/regradar/web`
- `npm run lint` from `product/regradar/web`
- `python3 -m compileall product/regradar/app product/regradar/run.py -q`
- `python3 tools/validate_workspace.py` if present
- `python3 tools/validate_codex_skills.py` if present

Expected risk: existing lint failures may remain in untouched or broad app files. If lint fails, document exact failures and fix touched-file issues where safe.

## 11. Preview plan using Sites or local browser

Sites is not available in the current Codex tool/plugin set and is not listed as an install candidate. Do not deploy to `statuteproof.com`, Cloudflare, or DigitalOcean.

Preview fallback:

1. Start API locally if needed: `python3 run.py api --port 5001` from `product/regradar`.
2. Start frontend locally: `npm run dev -- --host 127.0.0.1 --port 5173` from `product/regradar/web`.
3. Inspect with Codex browser or Playwright:
   - `/`
   - `/login`
   - `/register`
   - `/pricing`
   - `/source-readiness-review`
   - `/app/dashboard`
   - `/app/sources`
   - `/app/source-lab`
   - `/app/evidence`
   - `/app/billing`
4. Record desktop/mobile notes in `docs/sites-visual-upgrade-review.md`.

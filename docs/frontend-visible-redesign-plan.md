# StatuteProof visible redesign implementation plan

Date: 2026-06-21

## Design read

Reading this as a regulated B2B RegTech product for UAE MLROs, CCOs, compliance managers, and founder-operators. Public site should feel premium, trustworthy, evidence-first, and materially more distinct than generic dark SaaS. Dashboard should feel like a calm operational command center, not a landing page.

This is a Codex-only fallback sprint. Fresh Product Manager agent launch failed with `agent thread limit reached`, so no final report may claim agent packets were produced.

## Before screenshots

Baseline screenshots saved outside the repo:

- `/tmp/statuteproof-redesign-before/homepage-desktop-1440.png`
- `/tmp/statuteproof-redesign-before/homepage-mobile-390.png`
- `/tmp/statuteproof-redesign-before/login-desktop-1440.png`
- `/tmp/statuteproof-redesign-before/login-mobile-390.png`
- `/tmp/statuteproof-redesign-before/register-desktop-1440.png`
- `/tmp/statuteproof-redesign-before/register-mobile-390.png`
- `/tmp/statuteproof-redesign-before/source-readiness-desktop-1440.png`
- `/tmp/statuteproof-redesign-before/source-readiness-mobile-390.png`
- `/tmp/statuteproof-redesign-before/dashboard-desktop-1440-mocked.png`
- `/tmp/statuteproof-redesign-before/dashboard-mobile-390-mocked.png`
- `/tmp/statuteproof-redesign-before/review-queue-desktop-1440-mocked.png`
- `/tmp/statuteproof-redesign-before/review-queue-mobile-390-mocked.png`
- `/tmp/statuteproof-redesign-before/evidence-desktop-1440-mocked.png`
- `/tmp/statuteproof-redesign-before/evidence-mobile-390-mocked.png`

## Baseline problems to fix

- Homepage first viewport is credible but still visually close to the previous dark grid plus panel layout.
- Public site has too many repeated dark cards with similar hierarchy.
- Login/register pages use the same split dark grid panel and do not feel materially redesigned.
- Source readiness page is clearer than before, but still reads like a long centered form.
- Dashboard first viewport has useful content, but it still looks like stacked `sp-panel` cards rather than a true command center.
- Review queue and evidence pages rely on wide tables as primary UI, especially poor on mobile.
- Motion exists mostly as generic transitions, not as comprehension aid.

## Pages to redesign

1. Homepage first viewport and public hero.
2. Login and register pages.
3. Source readiness review page.
4. Dashboard home first screen.
5. Review queue canonical evidence section and mobile layout.
6. Evidence/brief workflow clarity surfaces where low-risk.

## Component strategy

- Keep React/Vite/Tailwind stack.
- Add a small set of global utility classes in `index.css`:
  - command-panel / command-strip
  - evidence-chain
  - metric-tile variants
  - subtle reveal / flow motion
  - mobile card/table alternates
- Do not introduce a new animation dependency.
- Keep the existing `sp-*` utilities for compatibility, but add stronger page-specific layout classes.

## Motion strategy

- Use only CSS transform/opacity transitions and lightweight keyframes.
- Use motion to show:
  - evidence chain progression
  - review state emphasis
  - hover/press feedback
- Respect `prefers-reduced-motion`.
- No parallax, no cursor mask, no decorative video-like effect in dashboard.

## Mobile strategy

- Every touched first screen must work at 390px.
- Dashboard and review surfaces get mobile-first stacked cards before tables.
- Large tables may remain on desktop, but mobile must not rely on horizontal scroll as the primary comprehension path.

## Legal copy strategy

- Keep "monitoring intelligence only" visible.
- Use "hash-verified source evidence" and "draft brief gates" rather than overclaiming customer-delivered evidence-backed briefs.
- State selected-source scope and no complete coverage claims.
- Do not imply Google/auth/source review confers compliance decisions.

## Exact files to touch

- `product/regradar/web/src/index.css`
- `product/regradar/web/src/components/Hero.jsx`
- `product/regradar/web/src/components/Header.jsx`
- `product/regradar/web/src/components/auth/LoginPage.jsx`
- `product/regradar/web/src/components/auth/RegisterPage.jsx`
- `product/regradar/web/src/components/SourceReadinessReviewPage.jsx`
- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/app/ReviewQueuePage.jsx`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/app/AIBriefPage.jsx`
- `docs/frontend-visible-redesign-report.md`
- `docs/frontend-ux-dashboard-hardening-report.md`

## Files not to touch

- Runtime database files.
- Raw evidence records.
- Source snapshots.
- Alert queue runtime files.
- `.env` or any secrets.
- Cloudflare/DigitalOcean/deployment config.
- Screenshots under `/tmp`.

## Risks

- Over-styling could make dashboard less usable.
- Over-claiming "evidence-backed" could weaken legal safety.
- Adding mobile card variants could duplicate content if not carefully scoped.
- Big component edits can break lazy-loaded routes.

## Rollback plan

- Revert only the files touched in this sprint.
- Keep reference intake and report docs if they accurately document blockers.
- If browser screenshots show insufficient visual delta, do not commit as a redesign.

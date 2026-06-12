# StatuteProof Website and App Gap Audit

**Date:** 2026-06-12  
**Scope:** Comparison of current statuteproof.com and local codebase vs. target product specification  
**Source of truth for current state:** Live site inspection (2026-06-12), frontend code at product/regradar/web/src/, backend at product/regradar/app/  
**Not legal advice. Internal planning document only.**

---

## How to Read This Table

- **Priority P0** = Blocks first pilot delivery or is a legal-safety gap. Must fix before any customer sees the product.
- **Priority P1** = Significantly reduces pilot value. Fix within first two weeks of implementation.
- **Priority P2** = Important for scale but not a blocker for first pilot.
- **Difficulty 1** = Simple config or copy change. **Difficulty 5** = Multi-day implementation.

---

| Feature | Current State | Gap Description | Priority | Difficulty | Notes |
|---------|--------------|-----------------|----------|------------|-------|
| **HOMEPAGE — HERO** | Single headline only visible on live site: "StatuteProof — Official-source regulatory intelligence for UAE financial firms". No subheadline, no CTAs, no body copy, no sample card visible. | Missing: subheadline, primary CTA ("Request a free UAE source readiness review"), secondary CTA ("View sample evidence-backed brief"), trust line, short disclaimer line, sample evidence alert card in hero. | P0 | 2 | Hero.jsx exists in codebase with more content. May be a deployment/build issue. Verify that built dist is what is deployed. |
| **HOMEPAGE — Sample Evidence Alert Card** | Not visible on live site. SampleBrief.jsx and EvidenceCard.jsx exist in codebase but appear not to be rendered in hero. | No visual proof of what an alert looks like in the hero section. This is the single highest-trust element missing from the homepage. SAMPLE/FAKE label required on any sample data. | P0 | 2 | Create/restore a SampleAlertCard component with clearly labeled SAMPLE/FAKE data. Add to homepage hero or immediately below hero. |
| **HOMEPAGE — Problem Section** | Problem.jsx exists in codebase. Not visible on live site. | Problem section missing from visible homepage content — a critical conversion element for MLRO persona. | P0 | 1 | Restore Problem.jsx to the homepage render order. |
| **HOMEPAGE — How It Works** | HowItWorks.jsx exists. Unclear if visible on live site. | Pipeline explanation is critical for compliance buyer trust. If not visible, restore. | P0 | 1 | Restore if missing. Update copy to match spec (4 steps, evidence-first language). |
| **HOMEPAGE — Source Coverage Preview** | Coverage.jsx exists with 9 commercial markets. UAE sources are listed. | Coverage component may not be showing actual current UAE source list (13 READY sources as of 2026-06-12). Status badges (Active/Limited/Not Active) must be accurate. | P0 | 2 | Update Coverage.jsx UAE source list to reflect current 13 READY sources. Disclosure of limitations must be visible. |
| **HOMEPAGE — Evidence Trail Section** | EvidenceCard.jsx and related components exist. Not clearly visible on live site. | Evidence trail section is a primary trust mechanism for the MLRO persona. Missing or invisible means the product appears to be just another aggregator. | P0 | 1 | Restore or create an Evidence Trail section explaining SHA-256, diff, timestamp. |
| **HOMEPAGE — Footer Disclaimer** | Footer.jsx exists. Footer disclaimer text unclear from live site inspection. | Short disclaimer ("For monitoring information only. Not legal advice.") must be visible in footer. Statutory/not-legal-advice language is a legal safety requirement. | P0 | 1 | Verify disclaimer text in Footer.jsx matches approved short disclaimer. Must mention not legal advice. |
| **HOMEPAGE — Human Review / Not Legal Advice Section** | Not confirmed visible on live site. | MLRO persona needs to see "human review required" language before they will engage with the product. | P1 | 1 | Add a dedicated section or block. Copy in spec Section 4. |
| **HOMEPAGE — Source Readiness Review CTA** | CTA exists in codebase but positioning unclear. Live site inspection showed very minimal content. | CTA must be prominent — primary CTA throughout the homepage. Currently buried or missing. | P0 | 1 | Ensure primary CTA "Request a free UAE source readiness review" appears in hero, mid-page, and before footer. |
| **HOMEPAGE — FAQ** | No FAQ component visible on live site or clearly in codebase. | 8-question FAQ addresses MLRO purchase objections. Missing = lost conversions for compliant-minded buyers. | P1 | 2 | Create FAQ section component. Copy in spec Section 4. |
| **HOMEPAGE — Pricing Preview** | Pricing.jsx exists. Prices have been updated recently per HANDOFF.md ($99/$249/$499 founding pilot). | Current pricing copy may reference old structure. Verify 4-tier layout (Free Review / Founding Pilot / VASP Pack / Consultant Pack) matches spec. No fake customer counts. | P1 | 1 | Review and update Pricing.jsx to match 4-tier structure in spec. |
| **REGISTRATION — Full Form** | No registration/sign-up functionality visible on live site. Auth module exists in app/auth.py but is single-user JWT. | Multi-user registration with email verification, org creation, role assignment, Terms of Service checkbox, and "not legal advice" acknowledgement checkbox — all missing. | P0 | 5 | Full auth system rebuild per Section 5 spec. Single largest implementation gap. |
| **REGISTRATION — Legal Acknowledgement Checkbox** | Not implemented. | Legal-safety requirement. Registration must not complete without user acknowledging reports are for information only, not legal advice. | P0 | 1 | Add as required checkbox to registration form. Store timestamp and boolean in DB. |
| **LOGIN — Multi-user** | Single-user login exists (API_USERNAME/API_PASSWORD_HASH from .env). | Cannot support pilot customers with their own credentials. Must have real user accounts with individual email+password. | P0 | 4 | Implement User model + login per Section 5. |
| **LOGIN — Password Reset** | Not implemented. | Users cannot recover accounts without admin intervention. Blocks self-serve pilot. | P0 | 3 | Implement forgot-password + reset-password flow with email + time-limited token. |
| **ONBOARDING FLOW — 6 Steps** | Not implemented. | Without onboarding, new users reach the dashboard with no context and no sources configured. Empty state without onboarding is disorienting. | P1 | 4 | Implement 6-step onboarding flow per Section 6. |
| **ORGANIZATION MODEL** | Not implemented. No multi-tenant org concept. | Required for pilot customers with multiple team members. | P0 | 4 | Implement Organization, Membership models per Section 18. |
| **DASHBOARD — Live Data** | DashboardPreview.jsx uses mock/demo data. Authenticated app alert feed, dashboard widgets, source status all demo-mode per HANDOFF.md. | Pilot customer sees fake numbers. Cannot demonstrate actual monitoring results. | P0 | 3 | Connect dashboard widgets to real API data. Source status from source_runs.jsonl. |
| **DASHBOARD — 8 Widgets** | Current dashboard structure unknown — HANDOFF.md references "AlertsPage, DashboardHome, Reports, Sources, Settings, Integrations" as authenticated app screens, mostly demo mode. | 8 specified widgets per Section 7 are not implemented with real data. | P1 | 3 | Wire real data to: Source Status Overview, Active Alerts, Recent Evidence, Briefs Ready, Review Queue, Source Health, Last Run Summary, Onboarding Checklist. |
| **SOURCES PAGE — Live Data** | SourceCoverageTable.jsx exists but wired to static data. Backend has source config in sources.json but no API serving it to frontend. | Sources page cannot show live monitoring status per source. | P0 | 3 | Add GET /api/v1/sources/status endpoint using source_runs.jsonl data. Connect to frontend. |
| **SOURCES PAGE — Status Badges** | Not fully implemented with 6 badge types. | FIRST_SEEN / UNCHANGED / CHANGED / FAILED / QUALITY_DROP / SOURCE_STRUCTURE_CHANGED badges with correct colors not all present. | P1 | 2 | Implement all 6 status badge types per Section 7 color spec. |
| **CUSTOM SOURCE ADD — 5-Step Flow** | AddYourSource.jsx exists but unclear if it's a real implementation or UI sketch. No backend custom source endpoint. | Custom source monitoring is a key differentiator for the Consultant Pack. Full flow not implemented. | P1 | 5 | Implement full custom source flow per Section 9 including test-fetch, legal ack, quality check. |
| **CUSTOM SOURCE — Legal Acknowledgement** | Not implemented. | Legal-safety requirement. Custom source add must include legal ack checkbox. | P0 | 1 | Add to custom source form. Block add without acceptance. |
| **CUSTOM SOURCE — Safety Checks (SSRF)** | Not implemented. | Backend must block SSRF attempts — custom source test cannot be used to fetch internal IPs, localhost, or metadata endpoints. | P0 | 2 | Add IP blocklist check and domain allowlist to custom source test endpoint. |
| **EVIDENCE RECORD PAGE — Authenticated** | No dedicated evidence record detail page. Evidence data exists in source run JSONL but no frontend display. | Pilot customer cannot view evidence records — a core product promise. | P0 | 3 | Create EvidenceDetailPage per Section 10. Wire to source_runs.jsonl data. |
| **DIFF VIEWER — Authenticated** | DiffViewer.jsx exists (component exists per file listing). Not clear if wired to real data. | Diff viewer is the technical proof element — must be wired to real diff data from chunk_diff.py output. | P1 | 3 | Wire DiffViewer.jsx to real diff.json artifacts from chunk_diff.py. Add quality warnings per Section 11. |
| **DIFF VIEWER — Quality Warnings** | Not implemented. | Legal-safety requirement: if diff quality is INCOMPLETE or UNKNOWN (e.g., UAE Legislation Portal aggregate changes), user must see a visible quality warning. No AI legal conclusions. | P0 | 1 | Add quality warning banner to DiffViewer based on diff_quality field. |
| **ALERTS PAGE — Review Actions** | AlertsPage exists but review actions are demo-mode per HANDOFF.md. | Cannot approve/reject/flag alerts from UI. Review is CLI-only (alert_review.py). | P1 | 3 | Implement review actions in UI with API endpoints. Gate high-risk approval behind note requirement. |
| **BRIEFS PAGE — Real Data** | Briefs appear as demo/mock in authenticated app. Weekly brief generator exists in CLI (weekly_brief.py) but not exposed via API or UI. | Pilot customer cannot view, approve, or export briefs from the dashboard. | P1 | 4 | Create briefs API endpoints + BriefsPage + BriefDetailView per Section 13. |
| **BRIEFS — Mandatory Disclaimer on Export** | Brief CLI generator includes disclaimer. Web export not implemented. | Legal-safety requirement. Brief export must include full disclaimer. Cannot block disclaimer from exports. | P0 | 1 | Enforce disclaimer_included check in brief export API. Include disclaimer text in PDF and Markdown exports. |
| **BRIEFS — No-Brief-Without-Evidence Gate** | Not implemented in UI. CLI has gates. | Brief cannot be marked APPROVED if evidence record is incomplete. Must enforce server-side. | P0 | 2 | Add server-side gate to brief approval endpoint. |
| **SOURCE READINESS REVIEW — Public Form** | Contact form exists. Source readiness review form may be the same Contact component. | Public form needs specific fields: company type, regulators of interest, legal acknowledgement. Current contact form may be too generic. | P1 | 2 | Update/extend contact/readiness form to include required fields per Section 14. |
| **SOURCE READINESS REVIEW — Dashboard Integration** | Not implemented. | Logged-in users cannot request or view their readiness review result in the dashboard. | P2 | 2 | Add SourceReadinessReview model and dashboard tab per Section 14. |
| **PRICING PAGE — 4 Tiers** | Pricing.jsx exists. Per HANDOFF.md prices were recently updated ($99/$249/$499). | Need to verify 4-tier structure (Free Check / Founding Pilot / UAE VASP Pack / Consultant Pack) matches spec. No fake social proof. | P1 | 1 | Review Pricing.jsx against Section 15 spec. Remove any fake logos or customer counts. |
| **PRICING PAGE — No Fake Social Proof** | Unknown — not visible from live site inspection. | Legal and credibility risk. Cannot display customer logos or testimonials that do not exist. | P0 | 1 | Audit Pricing.jsx for fake logos, invented customer counts, fabricated testimonials. Remove immediately if found. |
| **SETTINGS — Team Management** | Not implemented. No org model. | Required for any multi-user pilot. | P1 | 3 | Implement after org model is in place. Settings > Team page per Section 16. |
| **SETTINGS — Notification Preferences** | Not implemented. | Required for pilot customers to configure how they receive alerts. | P2 | 2 | Implement notification preferences per Section 16. |
| **SETTINGS — Audit Log** | Not implemented. | Required for compliance teams who need to show their review trail. "Who approved what, when" is critical for audit defense. | P1 | 2 | Implement Review model and org-level audit log per Section 16. |
| **BILLING — Manual Invoicing** | Not implemented in app. | Pilot customers need to see their plan and invoice history, even if billing is manual. | P2 | 1 | Add minimal billing page showing plan name, price, and "contact for invoice" CTA. |
| **LEGAL DISCLAIMERS — All Pages** | Footer disclaimer status unclear from live site inspection. Full disclaimer on sample brief unclear. | Legal-safety: disclaimer must be visible on homepage footer, sample brief page, every email, every exported document. | P0 | 1 | Audit every page, email template, and export for required disclaimer text. |
| **LEGAL DISCLAIMERS — Not Official Partner** | Unknown. | Must not claim to be official partner of VARA, CBUAE, DFSA, or any UAE regulator. | P0 | 1 | Audit all copy for any "official partner" or "certified by" language. Remove immediately if found. |
| **SECURITY PAGE** | Not present on live site or in codebase. | Trust page for technical/security-focused buyers. Required for DFSA/ADGM firm persona evaluation. | P2 | 2 | Create /security page per Section 24. Honest infrastructure description. No false certification claims. |
| **ABOUT/METHODOLOGY PAGE** | Not confirmed present. | Compliance buyers do due diligence on the team and methodology before committing. | P2 | 1 | Create /about page per Section 8. |
| **HOW IT WORKS PAGE** | Not confirmed as a separate page. May be a section on homepage only. | Some buyers need a dedicated page to evaluate methodology before requesting a pilot. | P2 | 2 | Create /how-it-works page per Section 3. |
| **EMAIL SYSTEM — Transactional** | HANDOFF.md references Telegram delivery for contact forms. No transactional email for registration/verification/invite. | No registration flow works without transactional email (verification, password reset, invite). | P0 | 3 | Integrate transactional email service (Resend recommended). Implement 10 email templates per Section 22. |
| **SAMPLE BRIEF PAGE — SAMPLE Label** | sample page exists at /samples/uae-fintech-source-readiness-snapshot.html per HANDOFF.md. | SAMPLE/FAKE label must be prominently visible near the top of the content. Not just in footer. Verify current implementation. | P0 | 1 | Verify SAMPLE label placement on sample page. Update if below the fold or small. |
| **SOURCE COVERAGE PAGE — Limitations Disclosure** | Coverage component shows 9 markets. Limitation notes exist per HANDOFF.md. | Dedicated /sources page with full limitation disclosure per source is not confirmed. QA/SA limitations must be disclosed per HANDOFF.md. | P1 | 2 | Create or update /sources page with per-source limitation disclosure per Section 3. |
| **NAVIGATION — Login/Register Links** | Not visible on live site (extremely minimal content shown). | Users cannot discover login/registration without navigation links. | P0 | 1 | Add login/register links to public navbar. |
| **NAVIGATION — Public Pages** | Navbar structure unclear from live site. | All 8 public pages must be discoverable from navigation per Section 3. | P1 | 1 | Update NavBar with correct public page links. |
| **API — Rate Limiting** | Rate limiter middleware exists (rate_limiter.py in codebase). | Custom source test endpoint and login must be rate-limited. Confirm rate limiting is configured on correct endpoints. | P0 | 1 | Verify rate limiting on /auth/login (5/15min) and custom source test (3/10min per org). |
| **API — Source Status Endpoint** | Not present. GET /regulations exists but not source status by source name with last run data. | Dashboard needs a dedicated /api/v1/sources/status endpoint. | P0 | 2 | Add endpoint reading source_runs.jsonl and returning per-source latest status. |
| **DEPLOYMENT — Frontend + Backend Connected** | HANDOFF.md confirms deployment not yet live. Static frontend + Python API must be deployed together. | /api/contact exists. Full API with auth, sources, evidence not deployed end-to-end. | P0 | 3 | Deploy per VPS runbook. Ensure all new endpoints are served under /api/v1/ path. |

---

## Summary Counts

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 26 | Blocks pilot delivery or is a legal-safety gap |
| P1 | 16 | Significantly reduces pilot value |
| P2 | 7 | Scale improvements |

## Top 5 Most Urgent Gaps

1. **Multi-user auth + org model** (P0, D5) — Without this, no pilot customer can have their own login.
2. **Transactional email system** (P0, D3) — Without this, registration, password reset, and invite flows cannot function.
3. **Dashboard wired to real data** (P0, D3) — Without this, pilot customer sees fake numbers.
4. **Evidence record and diff viewer wired to real data** (P0, D3) — Without this, the core product promise is invisible.
5. **Brief export with mandatory disclaimer** (P0, D1+D4) — Without this, a delivered brief has a legal-safety gap.

---

*Not legal advice. Internal planning document only.*

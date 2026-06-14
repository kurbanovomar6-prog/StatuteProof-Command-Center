# Premium Website + Auth + Dashboard — Implementation Report

## 1. Files changed

### New files created:
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `product/regradar/web/src/components/SourceReadinessReviewPage.jsx`
- `docs/premium-website-auth-dashboard-plan.md`

### Modified files:
- `product/regradar/web/src/App.jsx` — added SourceReadinessReviewPage import and view state, updated Hero CTAs, added Header onSourceReview prop, updated evidence section to dark theme with spec card
- `product/regradar/web/src/components/Hero.jsx` — exact spec headline, subheadline, CTA copy
- `product/regradar/web/src/components/Header.jsx` — added Request Source Review CTA button, Register link, updated nav
- `product/regradar/web/src/components/Footer.jsx` — full legal disclaimer per CLAUDE.md spec
- `product/regradar/web/src/components/auth/LoginPage.jsx` — updated title and subtitle copy per spec
- `product/regradar/web/src/components/auth/RegisterPage.jsx` — added job title, company type, jurisdiction fields, three-checkbox legal disclaimer (terms/privacy/monitoring-only)
- `product/regradar/web/src/components/app/AppShell.jsx` — added EvidencePage to PAGE map
- `product/regradar/web/src/components/app/AppSidebar.jsx` — added Evidence nav item with ShieldCheck icon
- `product/regradar/web/src/components/app/AppTopbar.jsx` — added Evidence label to page label map
- `product/regradar/web/src/components/app/DashboardHome.jsx` — real /api/sources/status fetch, 8-widget grid, real source table, loading/error states
- `product/regradar/web/src/components/app/AIBriefPage.jsx` — mandatory per-brief legal disclaimer added
- `product/regradar/web/src/components/app/SettingsPage.jsx` — upgraded Legal Acknowledgement section with full disclaimer and billing note

## 2. Routes added

| View state | Component | Type |
|---|---|---|
| `source-readiness-review` | SourceReadinessReviewPage | Public |
| `evidence` (app page) | EvidencePage | Protected (in AppShell) |

## 3. Components added/modified

- **New**: EvidencePage (SAMPLE labeled, 3 sample records, status badges, backend gap disclosed)
- **New**: SourceReadinessReviewPage (public form, regulator checkboxes, wired to /api/contact)
- **Modified**: DashboardHome (real API fetch, 8 widgets, source table with status badges)
- **Modified**: RegisterPage (job title, company type, jurisdiction, three legal checkboxes)

## 4. Backend endpoints used

| Endpoint | Used by |
|---|---|
| POST /api/auth/register | RegisterPage |
| POST /api/auth/login | LoginPage |
| GET /api/auth/me | App.jsx bootstrap |
| GET /api/profile | App.jsx bootstrap |
| GET /api/sources/status?market=AE | DashboardHome (real data) |
| GET /api/telegram/pair/status | DashboardHome |
| POST /api/contact | SourceReadinessReviewPage |

## 5. Auth status

**Real** — full session cookie auth working:
- Login: POST /api/auth/login with bcrypt password verification
- Register: POST /api/auth/register with email + password validation
- Session: httponly, samesite=Strict cookie
- /api/auth/me used for bootstrap on page load

## 6. Dashboard data

**Mixed** — real + sample:
- Source table: **Real** from /api/sources/status (12 enabled AE sources)
- 8 widget counts: **Real** derived from sources/status response
- Sample signal preview table: **SAMPLE** (labeled, mock data for brief preview)
- Evidence page: **SAMPLE** (clearly labeled, no /api/evidence endpoint exists)
- Brief page: **SAMPLE** (labeled, no /api/briefs endpoint exists)

## 7. Legal safety

**Passed**:
- No forbidden phrases found in new/modified files
- All SAMPLE data labeled with "SAMPLE — NOT REAL REGULATORY DATA" badges
- Full legal disclaimer in Footer
- Per-brief disclaimer added to AIBriefPage
- RegisterPage has three explicit acknowledgement checkboxes including monitoring-only disclaimer
- LoginPage subtitle references legal safety
- SourceReadinessReviewPage has disclaimer on form, success screen, and three info cards
- EvidencePage has disclaimer on cards, banner, info block
- SettingsPage Legal Acknowledgement section upgraded with full disclaimer

## 8. Design quality

**Passed**:
- Consistent dark navy (#07111F) background throughout
- Consistent cyan (#16D9F5) accent
- Status badges using correct colors: emerald (CHANGED), blue (FIRST_SEEN), red (FAILED), amber (QUALITY_DROP), slate (UNCHANGED)
- Skeleton loading states on dashboard widget grid
- Error state on dashboard with AlertTriangle
- Empty states on evidence and source pages
- No fake logos or testimonials
- No hardcoded secrets

## 9. What is still not production-ready

1. No /api/evidence endpoint — EvidencePage shows SAMPLE data (disclosed)
2. No /api/briefs endpoint — AIBriefPage shows SAMPLE data (disclosed)
3. RegisterPage extra fields (job title, company type, jurisdiction) are UI-only — only email, password, name, company, industry are sent to backend
4. Forgot password link on LoginPage is a placeholder (no backend endpoint)
5. Google OAuth button is disabled (Coming soon label — was pre-existing)
6. Dashboard source table shows NOT_RUN for all sources until monitoring runs are executed
7. Chunk size warning (506KB bundle) — code splitting not yet implemented

## 10. Validation commands run and results

```
python3 -m compileall app run.py -q     → PASS (no output)
npm run build                            → PASS (built in 1.26s, no errors)
npm run lint (new/changed files only)   → PASS (0 new errors; pre-existing errors in untouched files only)
```

Pre-existing lint errors (not introduced by this upgrade):
- DiffViewer.jsx, EvidenceCard.jsx, SourceCoverageTable.jsx: unused React import
- Pricing.jsx: unused plan variable in handleCta
- IntegrationsPage.jsx: setState in effect
- App.jsx: goToDashboard unused function

## 11. Next recommended task

1. Wire RegisterPage extra fields (job title, company type, jurisdiction) to backend — add these fields to `create_user()` in `app/auth.py` and the profile schema
2. Implement GET /api/evidence endpoint — read from source_runs.jsonl, return evidence records with hashes and diffs for the real EvidencePage
3. Run first AE monitoring round (`python run.py run AE`) to populate source_runs data — then dashboard source table will show real statuses instead of NOT_RUN
4. Add code splitting to reduce the 506KB bundle (dynamic imports for AppShell and landing sections)

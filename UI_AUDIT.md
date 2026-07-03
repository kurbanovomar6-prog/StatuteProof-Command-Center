# UI AUDIT — StatuteProof dashboard (2026-07-04)

Scope: authenticated app (`product/regradar/web/src/components/app/*` + shell). Screenshots: `audit-screens/before-*.png`.
Ranking: P0 = customer would distrust the product · P1 = looks amateur · P2 = cosmetic.

## P0 — trust-killers

1. **Permanent false "System status: degraded" banner on every page.** `AppTopbar.jsx:44` checks `d.status === 'ok'` but `/api/health` returns `{ok: true}` with no `status` field, so the amber warning never clears. A compliance officer's first impression of every screen is "the system is broken."
2. **"Monitoring active" badge is unconditional.** `DashboardHome.jsx:416-418` renders it whenever the sources API loads, with no freshness check against `last_run_at`. Sits directly under the (false) degraded banner — the two contradict each other on screen.
3. **Fake "live" pulsing dot.** `DashboardHome.jsx:50` (`sp-live-dot` on "Sources enabled" card) implies real-time monitoring; nothing behind it.
4. **Duplicate React keys drop/duplicate rows.** Console error "Encountered two children with the same key" on data pages. `ReviewQueuePage.jsx:280,454` and `ReportsPage.jsx:153` key rows by `evidence_record_id` / `record_id`, which repeat across intakes (before-review-queue.png shows two identical `AE-adgm-fsra-guidance-policy` rows). React may silently omit records in a compliance review queue.
5. **Status column contradicts itself in the same row.** Sources table shows amber "Needs remediation" next to green extraction "good" on all 59 QUALITY_DROP rows (`SourcesPage.jsx:92-97` maps 3 statuses onto one amber label with no explanation). No tooltip anywhere decodes any status.
6. **Raw machine enums shown to customers**: `QUALITY_DROP` (Reports/Evidence chips), `financial_regulator`/`aml` categories (`SourcesPage.jsx:492`), `local_outbox`/`test_mode` (`IntegrationsPage`), `pending`/`none` lowercase (`ReviewQueuePage.jsx:215`), `run_status || 'UNKNOWN'`.
7. **Raw ISO timestamps with microseconds** in customer-facing evidence UI: `ReportsPage.jsx:166,195` and `ReviewQueuePage.jsx:407,457` render `2026-07-03T20:48:14.379541+00:00` verbatim. No timezone consistency: other pages use `en-GB … UTC` (`SourcesPage.jsx:341`, `EvidencePage.jsx:50`, `DashboardHome.jsx:221,526` — the last one omits the year AND the timezone). Nothing shows Gulf Standard Time, the customer's timezone.

## P1 — looks amateur

8. **Emojis / text-marks as icons in app**: flag emoji `🇦🇪` hardcoded (`SourcesPage.jsx:112`, rendered :491); `⚠` (`SourcesPage.jsx:724,727`); `✓` (`IntegrationsPage.jsx:629`, `ChoosePlanPage.jsx:218` "Selected ✓", `SettingsPage.jsx:352` "Saved ✓"); arrow `→` in button copy (`OnboardingPage.jsx:429`).
9. **Two different accent cyans**: token `--accent: #19D3F3` (`index.css:100`) vs hardcoded `#16D9F5` in ~46 places across app components. Plus decorative use of emerald/amber/cyan/rose pills for non-status content (e.g. "Operator command center" in amber, `DashboardHome.jsx:405`).
10. **Status vocabulary explosion.** At least four overlapping sets: table legend (Readiness supported / Under validation / Needs adapter / Limited), filter row adds (Needs remediation / Monitoring not started / Partial / User source), Health column (MONITOR_OK / Evidence confirmed / Source health issue / Not yet started), dashboard badges (READINESS / QUALITY DROP / ACTIVATION PENDING / PROOF RECORDED / NEEDS REVIEW / BLOCKED). No shared component, no definitions.
11. **Sources and Review Queue tables overflow at 1440px** (before-sources.png: "Last evidence" and "Timeline" clipped; before-review-queue.png: decision buttons clipped). 9 columns, all `whitespace-nowrap`, no truncation strategy, no tabular numerals.
12. **Chip-spam headers on every page**: 4-5 defensive pills ("Approved records only / Profile matched / Manual preview / Not legal advice", "Saved evidence only / A&A linked / No fake rows") repeated as decoration; "No fake rows" reads as an admission, not reassurance.
13. **Dashboard hierarchy failure.** 12 stacked sections (hero + gate map + profile + 8 stat cards + pressure score + table + queue + 2 delivery cards + checklist + readiness + deadlines). The 8-card row duplicates the 4 attention cards. First-time answer to "what needs my attention?" is buried mid-page; screaming yellow "NEXT SAFEST ACTION" marketing card outranks real data.
14. **Copy tone**: "Operator command center", "Next safest action", "MLRO review command center", "command center" jargon; internal-operator language shown to customers.
15. **Raw internals as primary content**: mono record ids `evr_AE-adgm-…` + repo file paths (`evidence/adgm-fsra/…`) as the first cell in Review Queue (`ReviewQueuePage.jsx:210`); raw proof paths on Evidence cards (`EvidencePage.jsx:172`).

## P2 — cosmetic

16. Mixed border radii (`rounded-lg/xl/2xl/md`) and font sizes (`text-[10px]/[11px]/xs`) without a scale; `sp-mono` used for the word "Blocked" as display type (before-dashboard.png).
17. `Loader2` spinner-in-void for Sources table (`SourcesPage.jsx:458-463`) while dashboard uses skeletons — inconsistent loading language.
18. Sidebar workspace pill wraps awkwardly ("Source Readiness Review" over 2 lines, before-*.png bottom-left); topbar chip "Sources staged after validation" is unexplained jargon.
19. `console.warn` in `workspaceProfile.js:28` (only console call in src; tolerable but noisy).

## Missing states inventory

| Page | Loading | Empty | Error |
|---|---|---|---|
| DashboardHome | skeletons (partial) | n/a | inline text, no retry |
| Sources | spinner | text-only, no icon | text, no retry |
| Evidence | ? (verify) | present | present, no retry |
| Review Queue | present | present | present, no retry |
| Alerts | present | good (icon+text) | present, no retry |
| Briefs/Reports | present | present | mixed |

## What already works (do not break)

- Honest gating copy ("Delivery blocked by default", "Test mode", no sample data in authed views) — keep the substance, trim the repetition.
- Real data everywhere; no mock imports in app pages. Alerts empty state is the quality bar.
- Skeleton pattern exists (`sp-skeleton`), token block exists (`index.css:87+`) — needs adoption, not invention.

## Fix order (maps to Phase 2 commits)

1. P0-1/2/3 truth fixes (topbar health check, freshness-gated monitoring badge, remove fake live dot)
2. Shared primitives: `StatusBadge` (+tooltips), `formatTimestamp` (GST), `EmptyState`, `ErrorState`, skeleton adoption
3. P0-4 duplicate keys; P0-6/7 enum + timestamp cleanup across Evidence/ReviewQueue/Reports/Briefs/Integrations
4. Sources table restructure (fit 1440, one status vocabulary, no emoji flags)
5. Dashboard reorder (3 questions above the fold), copy pass, chip de-spam
6. Token alignment (single accent), emoji sweep, radius/type-scale normalization

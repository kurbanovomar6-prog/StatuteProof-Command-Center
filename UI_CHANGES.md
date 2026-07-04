# UI CHANGES — StatuteProof dashboard credibility pass (2026-07-04)

Screenshots: `audit-screens/before-*.png` → `audit-screens/after-*.png` (11 pages, 1440×900).
Defect numbers reference `UI_AUDIT.md`.

## Proof

- Tests before: 43/43 pass · Tests after: **43/43 pass** (3 files, Vitest)
- Production build after: **✓ built in 361ms**, main bundle 229.79 kB / 72.46 kB gzip (unchanged budget)
- Console errors: duplicate-key errors on Sources eliminated — **0 console errors across all 11 authenticated pages** (verified via Playwright sweep)
- Emojis/text-mark icons in app pages: **0 remaining** (`✓`, `⚠`, `→`, flag emoji all replaced or removed)

## Shared primitives (new, presentation-only)

`src/utils/time.js` (GST formatting, relative time, staleness), `src/components/app/ui/`:
`StatusBadge` (one status vocabulary, icon + label + tooltip explaining every status),
`TimeStamp` ("14 min ago" with "· 04 Jul 2026, 15:22 GST" on hover), `EmptyState`, `ErrorState` (with retry).
`index.css`: single accent token (`--accent` aligned to the one cyan actually used), tabular numerals in all tables.

## Per page

**Dashboard home** (before/after-dashboard.png) — closes P0-1, P0-2, P0-3, P1-13, P1-14:
false "System status: degraded" banner fixed (health check read a nonexistent field); unconditional
"Monitoring active" badge replaced with freshness badge derived from `last_run_at` (flags stale >48h);
fake pulsing "live" dot removed; duplicate 8-card stat row removed; yellow "NEXT SAFEST ACTION" marketing
card → neutral "Recommended next step" panel with a 4th real metric (evidence records); jargon pills
("Operator command center") removed; error state gained retry. Above the fold now answers: what is
monitored (116 enabled / 83 eligible + last check), what changed (changes needing review), what needs
attention (source-health flags, coverage limits, delivery gate).

**Sources** (before/after-sources.png) — closes P0-4 (21 API rows ship empty `source_id` → composite keys),
P0-5, P1-8, P1-10, P1-11: 9 nowrap columns → 7 fixed-width columns, fits 1440 with zero horizontal scroll;
contradictory Status+Health pair → one StatusBadge with remediation reason in the tooltip; flag emoji gone;
`financial_regulator` → "Financial regulator", `aml` → "AML"; phantom filter options (Limited/Partial/
Needs adapter) removed; skeleton rows replace spinner; icon empty state; GST timestamps.

**Review Queue** (before/after-review-queue.png) — closes P0-4, P0-6, P0-7, P1-11, P1-12: composite row
keys; raw `pending`/`none`/`CHANGED`/`MONITOR_OK` → labeled badges with tooltips; raw ISO timestamps →
GST; tables compress to viewport (verified: 1108px and 1142px content at 1440); "MLRO review command
center" and the "No fake rows" chip row replaced with one plain sentence.

**Evidence** — closes P0-6, P0-7: local badge component replaced by shared StatusBadge; `QUALITY_DROP`
health text → badge; detected-at now GST; category humanized; timeline event timestamps formatted.

**Reports** — closes P0-4, P0-7: composite keys; microsecond ISO timestamps → GST; status chips → badges;
chip row removed.

**Monitoring Briefs** — raw ISO "Queued" → GST; change-status chip → badge; chip row removed.

**Reviewed Alerts** — `HIGH/MEDIUM/LOW` chips → "High risk" (+ tooltip: assigned during human review);
filter labels sentence-cased; chip row removed. (Empty state was already the quality bar; untouched.)

**Integrations** — raw `test_mode`/`local_outbox` enums → labeled badges/text; last `✓` glyph → lucide Check.

**Settings / Choose plan / Onboarding / Sidebar** — "Saved ✓", "Selected ✓", trailing "→" removed from
buttons; sidebar plan pill no longer wraps; "Sources staged after validation" topbar jargon chip removed.

**PressureScore widget** — the invented 0-30 "Regulatory Pressure" aggregate (HIGH×3+MEDIUM×1) and its
progress bar removed; panel now shows plain counts of reviewed alerts by risk level (same API data).

## Remaining (accepted, with reason)

- Landing/marketing components (`src/components/*.jsx`) keep their `✓`/`→` text marks — out of dashboard scope.
- `SettingsPage` has a pre-existing unused `setEmailEnabled` lint error — predates this pass; not a visual defect.
- `console.warn` in `workspaceProfile.js:28` (catch-path only) left in place — error visibility, not noise.
- Source Lab got only the shared-token benefits; a deep pass wasn't needed for the top-3 pages bar.
- Backend payload oddities surfaced honestly but not fixable here: `QUALITY_DROP` rows with `extraction: good`,
  21 rows with empty `source_id`, `access_status: unknown` — presented decodably; root cause is backend scope.

## Tempted but did NOT build (scope rules)

- A "Tier A/B" column — tier exists in `sources.json` but the API doesn't return it; no invented data.
- Risk trend chart on the dashboard — no time-series endpoint exists.
- Auto-refresh/polling for freshness — new behavior, not presentation.
- Toast notification system, pagination for the sources table, theme toggle, global search — new features.
- Rewriting `alert_routing` status flow copy into a wizard — backend workflow, not visual layer.

// Deterministic API responses for the screenshot and a11y harness.
//
// Every screen is rendered against the SAME data every run, because a baseline
// that moves with the live registry is not a baseline — it fails on days when a
// source count changed and says nothing about the design.
//
// The numbers here deliberately match what the real registry reports today
// (140 enabled / 40 fresh-alert), so a screenshot never shows a headline the
// product could not actually produce.

const USER = {
  id: 1,
  email: 'mlro@example-bank.ae',
  full_name: 'Layla Haddad',
  company_name: 'Example Bank PJSC',
  email_verified: true,
  plan_name: 'evidence_preview',
  activated_plan: 'assurance',
}

const SOURCES = [
  {
    source_id: 'AE-cbuae-rulebook', name: 'CBUAE Rulebook',
    jurisdiction: 'AE', category: 'financial_regulator',
    status: 'MONITOR_OK', freshness: 'FRESH', last_run_age_days: 0,
    configured_status: 'MONITOR_OK', last_checked_at: '2026-07-26T04:00:00Z',
  },
  {
    source_id: 'AE-vara-rulebook', name: 'VARA Rulebook',
    jurisdiction: 'AE', category: 'virtual_assets',
    status: 'MONITOR_OK', freshness: 'FRESH', last_run_age_days: 1,
    configured_status: 'MONITOR_OK', last_checked_at: '2026-07-25T04:00:00Z',
  },
  {
    source_id: 'AE-dfsa-rulebook', name: 'DFSA Rulebook',
    jurisdiction: 'AE', category: 'financial_regulator',
    status: 'STALE', freshness: 'STALE', last_run_age_days: 34,
    configured_status: 'MONITOR_OK', last_checked_at: '2026-06-22T04:00:00Z',
  },
]

const ALERTS = [
  {
    alert_id: 'draft-cbuae-001', source_id: 'AE-cbuae-rulebook',
    source_name: 'CBUAE Rulebook', risk_level: 'HIGH', score: 82,
    change_type: 'REPORTING', confidence: 'MEDIUM',
    headline: 'Reporting form C-14 gains two new mandatory fields',
    detected_at: '2026-07-25T09:12:00Z', delivery_ready: true,
    status: 'APPROVED_FOR_URGENT',
  },
  {
    alert_id: 'draft-vara-002', source_id: 'AE-vara-rulebook',
    source_name: 'VARA Rulebook', risk_level: 'MEDIUM', score: 47,
    change_type: 'LICENSING', confidence: 'MEDIUM',
    headline: 'Custody licence renewal window shortened to 30 days',
    detected_at: '2026-07-24T14:40:00Z', delivery_ready: true,
    status: 'APPROVED_FOR_WEEKLY',
  },
]

// Path suffix -> body. Matched by `endsWith` on the pathname, longest first, so
// '/api/sources/status' wins over '/api/sources'.
export const API_FIXTURES = {
  '/api/auth/me': { ok: true, user: USER },
  // onboarding_completed is what App.jsx gates the whole shell on — without it
  // every screenshot is the 4-step setup wizard instead of the product.
  '/api/profile': {
    ok: true,
    onboarding_completed: true,
    company_name: 'Example Bank PJSC',
    markets: ['UAE'], industry: 'Banking',
    alert_threshold: 'MEDIUM', brief_language: 'en',
    weekly_brief_enabled: true, telegram_alerts_enabled: true,
    email_alerts_enabled: true, ai_enabled: false,
    topics: ['AML/CFT', 'Reporting'], custom_sources: [],
    profile: {
      onboarding_completed: true,
      company_name: 'Example Bank PJSC',
      markets: ['UAE'], industry: 'Banking',
    },
  },
  '/api/plan': {
    ok: true,
    plan: { name: 'assurance', activated: true, capabilities: { alerts: true, evidence: true, reports: true } },
  },
  '/api/sources/status': {
    ok: true, sources: SOURCES,
    counts: { total: 40, healthy: 2, stale: 1 },
    freshness_summary: { FRESH: 2, STALE: 1, NEVER_RUN: 0 },
  },
  '/api/sources/summary': { ok: true, enabled: 140, fresh_alert: 40, candidate: 36 },
  '/api/sources/timeline': { ok: true, timeline: [] },
  '/api/custom-sources': { ok: true, sources: [] },
  '/api/alerts/action-log': { ok: true, entries: [] },
  '/api/alerts/checklist': { ok: true, items: [] },
  '/api/alerts/decisions': { ok: true, decisions: [] },
  '/api/alerts/redline': { ok: true, redline: null },
  '/api/evidence': { ok: true, records: [] },
  '/api/evidence/review': { ok: true, records: [], counts: { pending: 0, approved: 0, rejected: 0 } },
  '/api/reviews/queue': { ok: true, items: [] },
  '/api/canonical-evidence': { ok: true, rows: [], counts: { pending: 0, approved: 0, rejected: 0 } },
  '/api/briefs': { ok: true, briefs: [] },
  '/api/reports/monthly-assurance': { ok: true, reports: [] },
  '/api/reports/coverage-certificate': { ok: true, certificate: null },
  '/api/calendar/effective-dates': { ok: true, dates: [] },
  '/api/audit-log': { ok: true, entries: [] },
  '/api/delivery/logs': { ok: true, logs: [] },
  '/api/delivery/email-status': { ok: true, status: 'local_outbox' },
  '/api/telegram/pair/status': { ok: true, connected: false },
  '/api/settings/telegram': { ok: true, settings: {} },
  '/api/team/members': {
    ok: true, org_id: 2,
    members: [
      { user_id: 1, email: 'mlro@example-bank.ae', role: 'owner', seated_at: '2026-07-01T00:00:00Z' },
      { user_id: 2, email: 'analyst@example-bank.ae', role: 'auditor', seated_at: '2026-07-20T00:00:00Z' },
    ],
  },
  '/api/admin/alert-review-queue': { ok: true, alerts: [], count: 0 },
  '/api/admin/accounts': { ok: true, accounts: [] },
  '/api/alerts': { ok: true, alerts: ALERTS },
  '/api/digest/assurance-preview': { ok: true, preview: null },
  '/api/evidence-room/shares': { ok: true, shares: [] },
}

export function bodyFor(pathname) {
  const keys = Object.keys(API_FIXTURES).sort((a, b) => b.length - a.length)
  const hit = keys.find(k => pathname.startsWith(k))
  // An unmocked endpoint returns a well-formed empty envelope rather than a
  // 404: a screenshot of an error state would be a screenshot of the harness,
  // not of the design.
  return hit ? API_FIXTURES[hit] : { ok: true }
}

export { USER }

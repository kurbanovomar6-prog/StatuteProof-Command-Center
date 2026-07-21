// Public Source Coverage headline counts.
//
// These numbers are shown on the public coverage page and MUST match the real
// product/regradar/sources.json. They are asserted against that file by
// sourceCounts.test.js — if sources.json drifts (a source is enabled, a mode
// changes, a candidate is promoted), that test fails and forces this file to be
// updated before the stale claim can ship. Do NOT edit these by feel; run the
// test, read the recomputed truth it prints, and reconcile.
//
//   enabled            = sources with enabled === true
//   readinessSupported = enabled AND monitoring_mode === 'fresh_alert' AND alert_eligible === true
//   candidate          = enabled AND monitoring_mode === 'candidate'
export const SOURCE_TRUTH = {
  // Whole-register count (UAE + international layer + 6 GCC divergence-feed
  // candidates added 2026-07-18). The backend audit reports the UAE-scope
  // subset (131) — two scopes, both true, labeled accordingly in the UI.
  // 2026-07-21: +1 enabled — CBUAE Enforcement (administrative/financial
  // sanctions) added in disclosed remediation (centralbank.ae is proxy-only,
  // HTTP 403 direct); it is NOT counted as fresh-alert, only disclosed.
  enabled: 140,
  // 2026-07-18 PROD-VANTAGE RE-MEASURE: 25 CBUAE rulebook + 10 www.dfsa.ae
  // sources demoted to remediation — both hosts return HTTP 403 to our
  // production monitoring egress on every fetch method (persistent since
  // 2026-07-11). Plus 3 individually-diagnosed persistent failers (UAE CMA
  // circulars, DIFC laws root listing, VARA 30-day revision view) demoted
  // pending production rebaselines. Two sources PASSED prod gates and were
  // promoted (DFSA AML rulebook module via dfsaen.thomsonreuters.com, VARA
  // Compliance & Risk Management Rulebook incl. AML/CFT Part III).
  // Honest count: 74 − 38 + 2 = 38. Unreachable-from-production sources are
  // disclosed, not counted — that is the pricing-page promise.
  // 2026-07-21: +1 — VARA Regulatory Notices and Enforcement Index promoted
  // candidate -> fresh_alert on enforcement-monitoring discovery (same host as
  // the MONITOR_OK VARA enforcement table; server-renders dated notices).
  readinessSupported: 41,
  // 2026-07-18: the VARA rulebook candidate passed prod gates and was promoted
  // to fresh_alert — candidate 10 → 9. Later the same day, the 21 enabled
  // sources that sat OUTSIDE the monitoring_mode vocabulary (mode missing)
  // were classified honestly: 16 register/listing monitors → evidence_library,
  // 5 genuinely alert-worthy but unvalidated listings → candidate (VARA
  // notices/enforcement index, FTA VAT public clarifications, DFSA news hub,
  // DFSA SEO letters, DFM regulatory circulars) — candidate 9 → 14.
  // 2026-07-21: −1 — the VARA regulatory-notices index was promoted out of
  // candidate to fresh_alert (see readinessSupported above).
  candidate: 35,
}

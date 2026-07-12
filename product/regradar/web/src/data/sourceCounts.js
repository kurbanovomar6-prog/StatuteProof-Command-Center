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
  enabled: 116,
  readinessSupported: 83,
  candidate: 8,
}

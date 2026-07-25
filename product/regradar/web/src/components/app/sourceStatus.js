// How a monitored source is described to the customer.
//
// Kept out of SourcesPage.jsx so the page file exports only its component —
// mixing helpers in breaks React Fast Refresh, and these are worth testing on
// their own anyway: they decide the word someone reads before concluding they
// are covered.

// Sources known to need remediation regardless of what a run reports.
const REMEDIATION_SOURCE_IDS = new Set([
  'AE-uae-legislation-portal',
  'AE-uae-financial-intelligence-unit-uaefiu',
  'AE-sca-regulations-listing',
])

export function statusFromApiSource(row) {
  if (REMEDIATION_SOURCE_IDS.has(row.source_id) || row.status === 'remediation') return 'Needs remediation'
  if (row.change_status === 'FAILED' || row.change_status === 'QUALITY_DROP') return 'Needs remediation'
  if (!row.last_run_at || row.change_status === 'NOT_RUN' || row.freshness === 'NEVER_RUN') return 'Monitoring not started'
  // A successful run long ago is not current monitoring. Without this a source
  // last checked 36 days ago fell through to "Readiness supported", which is the
  // reassuring word the customer reads before deciding they are covered.
  if (row.freshness === 'STALE' || row.freshness === 'UNKNOWN') return 'Check overdue'
  return 'Readiness supported'
}

// Days since the last recorded check, for display next to the status. The label
// alone cannot say HOW overdue a source is, and "overdue by 2 days" and "overdue
// by 3 months" are different facts for someone deciding whether to rely on it.
export function checkAgeLabel(row) {
  const age = row?.last_run_age_days
  if (typeof age !== 'number') return null
  if (age < 1) return 'checked today'
  const days = Math.round(age)
  return `checked ${days} day${days === 1 ? '' : 's'} ago`
}

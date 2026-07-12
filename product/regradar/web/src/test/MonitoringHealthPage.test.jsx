// Monitoring health is an OPERATIONAL surface: it must render per-source health
// derived honestly from recorded coverage evidence, flag stale / no-coverage
// sources rather than hide them or show them green, carry the monitoring-only
// disclaimer in every state, and recover from a load error.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MonitoringHealthPage from '../components/app/MonitoringHealthPage'

const HEALTH_PAYLOAD = {
  ok: true,
  db: 'connected',
  sources_active: 4,
  last_run_at: '2026-07-12T06:00:00Z',
  timestamp_utc: '2026-07-12T06:05:00Z',
}

// One source per health state so derivation is exercised end to end.
const CERT = {
  period_label: 'Last 30 days',
  generated_at_utc: '2026-07-12T00:00:00Z',
  negative_assurance_statement: 'Recorded checks only; every gap is disclosed.',
  summary: { sources_total: 4 },
  sources: [
    {
      // healthy: continuous, recent, no failures
      source_id: 'cbuae', source_name: 'CBUAE Rulebook', change_state: 'UNCHANGED',
      continuity_status: 'CONTINUOUS', successful_checks: 30, checks_in_period: 30,
      days_with_proof_hash: 30, expected_days: 30, gap_days: 0, last_check_gap_days: 0,
      degraded: false, last_check_utc: '2026-07-12T05:00:00Z', degraded_reasons: [],
    },
    {
      // no coverage: zero successful checks — must never read as healthy
      source_id: 'dfsa', source_name: 'DFSA Handbook', change_state: 'NO_PROOF',
      continuity_status: 'NO_COVERAGE', successful_checks: 0, checks_in_period: 0,
      days_with_proof_hash: 0, expected_days: 30, gap_days: 30, last_check_gap_days: 30,
      degraded: false, last_check_utc: '', degraded_reasons: [],
      gap_disclosure: 'No successful check was recorded for this source in the period.',
    },
    {
      // stale: partial continuity with day gaps
      source_id: 'vara', source_name: 'VARA Rulebook', change_state: 'UNCHANGED',
      continuity_status: 'PARTIAL', successful_checks: 20, checks_in_period: 25,
      days_with_proof_hash: 25, expected_days: 30, gap_days: 5, last_check_gap_days: 4,
      degraded: false, last_check_utc: '2026-07-08T05:00:00Z', degraded_reasons: [],
    },
    {
      // degraded: checks ran but some failed
      source_id: 'fsra', source_name: 'FSRA Handbook', change_state: 'CHANGED',
      continuity_status: 'PARTIAL', successful_checks: 25, checks_in_period: 30,
      days_with_proof_hash: 27, expected_days: 30, gap_days: 3, last_check_gap_days: 1,
      degraded: true, last_check_utc: '2026-07-11T05:00:00Z',
      degraded_reasons: ['Fetch failed: 403 from source on 2 runs'],
    },
  ],
  disclaimer_short: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

// The page calls two endpoints (/api/health and /api/reports/coverage-certificate),
// so the fetch mock routes by URL rather than returning one payload for all calls.
function mockRoutes({ coverageOk = true, coveragePayload } = {}) {
  const payload = coveragePayload || { status: 'ok', certificate: CERT }
  globalThis.fetch = vi.fn((url) => {
    const u = String(url)
    if (u.includes('/api/health')) {
      return Promise.resolve({ ok: true, json: async () => HEALTH_PAYLOAD })
    }
    return Promise.resolve({ ok: coverageOk, json: async () => payload })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('MonitoringHealthPage', () => {
  it('shows the monitoring-only disclaimer and honest framing before data loads', () => {
    mockRoutes()
    render(<MonitoringHealthPage />)
    // Disclaimer is legally load-bearing and present in every state, including loading.
    expect(
      screen.getByText(/not legal advice and not a guarantee of compliance/i),
    ).toBeInTheDocument()
    // Honest operational framing — never implies compliance.
    expect(screen.getByText(/not a compliance, legal, or regulatory status/i)).toBeInTheDocument()
  })

  it('renders per-source operational health derived from the recorded fields', async () => {
    mockRoutes()
    render(<MonitoringHealthPage />)

    // A continuously-covered source reads Healthy.
    expect(await screen.findByText('CBUAE Rulebook')).toBeInTheDocument()
    expect(screen.getAllByText('Healthy').length).toBeGreaterThan(0)
    // Stale and degraded sources render with their honest states.
    expect(screen.getByText('VARA Rulebook')).toBeInTheDocument()
    expect(screen.getAllByText('Stale').length).toBeGreaterThan(0)
    expect(screen.getByText('FSRA Handbook')).toBeInTheDocument()
    expect(screen.getAllByText('Degraded').length).toBeGreaterThan(0)
    // Degraded reasons surface, not just a status.
    expect(screen.getByText(/fetch failed: 403 from source/i)).toBeInTheDocument()
  })

  it('flags a no-coverage source honestly instead of hiding it or showing green', async () => {
    mockRoutes()
    render(<MonitoringHealthPage />)

    // The un-checked source is shown, not dropped...
    expect(await screen.findByText('DFSA Handbook')).toBeInTheDocument()
    // ...and labelled No coverage (badge + summary tile), never Healthy.
    expect(screen.getAllByText('No coverage').length).toBeGreaterThan(0)
    expect(
      screen.getByText(/no successful check was recorded for this source/i),
    ).toBeInTheDocument()
  })

  it('shows an error with retry and no source rows when coverage fails to load', async () => {
    mockRoutes({ coverageOk: false, coveragePayload: { message: 'Invalid period.' } })
    render(<MonitoringHealthPage />)

    await waitFor(() =>
      expect(screen.getByText(/could not load monitoring health/i)).toBeInTheDocument(),
    )
    expect(screen.getByText(/invalid period/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    // No per-source rows leak through on error.
    expect(screen.queryByText('CBUAE Rulebook')).not.toBeInTheDocument()
    // Disclaimer still present in the error state.
    expect(
      screen.getByText(/not legal advice and not a guarantee of compliance/i),
    ).toBeInTheDocument()
  })

  it('renders an empty state when no sources resolve for the period', async () => {
    mockRoutes({ coveragePayload: { status: 'ok', certificate: { ...CERT, sources: [] } } })
    render(<MonitoringHealthPage />)

    expect(
      await screen.findByText(/no monitored sources resolved for this period/i),
    ).toBeInTheDocument()
    expect(screen.queryByText('CBUAE Rulebook')).not.toBeInTheDocument()
  })
})

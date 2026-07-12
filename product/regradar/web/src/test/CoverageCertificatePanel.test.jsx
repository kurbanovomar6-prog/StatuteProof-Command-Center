// The coverage certificate is negative assurance: it must render exactly what
// was checked AND surface gaps / no-coverage honestly, and it must never drop
// its "not legal advice / no guarantee" framing.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CoverageCertificatePanel from '../components/app/CoverageCertificatePanel'

const CERT = {
  period_label: 'March 2026',
  generated_at_utc: '2026-03-31T00:00:00Z',
  negative_assurance_statement:
    'StatuteProof checked the sources below over the period; every gap is disclosed and no complete-coverage claim is made.',
  summary: {
    sources_total: 2,
    sources_changed: 1,
    sources_with_gaps: 1,
    sources_no_coverage: 1,
    total_successful_checks: 40,
    total_days_with_proof_hash: 20,
  },
  sources: [
    {
      source_id: 'cbuae', source_name: 'CBUAE Rulebook', change_state: 'CHANGED',
      successful_checks: 30, checks_in_period: 31, days_with_proof_hash: 20, expected_days: 31,
      gap_days: 0, last_check_utc: '2026-03-31T09:00:00Z', last_proof_hash: 'sha256:abcdef0123456789',
    },
    {
      source_id: 'dfsa', source_name: 'DFSA Handbook', change_state: 'NO_PROOF',
      successful_checks: 0, checks_in_period: 0, days_with_proof_hash: 0, expected_days: 31,
      gap_days: 31, last_check_utc: '', last_proof_hash: '',
      gap_disclosure: 'No successful check was recorded for this source in the period.',
    },
  ],
  disclaimer_short: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

function mockJson(payload, ok = true) {
  globalThis.fetch = vi.fn().mockResolvedValue({ ok, json: async () => payload })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CoverageCertificatePanel', () => {
  it('renders honest framing and the disclaimer before any fetch', () => {
    render(<CoverageCertificatePanel />)
    expect(screen.getByText(/coverage certificate/i)).toBeInTheDocument()
    expect(screen.getByText(/makes no claim of complete coverage/i)).toBeInTheDocument()
    expect(screen.getByText(/not legal advice and not a guarantee of compliance/i)).toBeInTheDocument()
    // No table until the user generates.
    expect(screen.queryByText('DFSA Handbook')).not.toBeInTheDocument()
  })

  it('surfaces gaps and no-coverage sources after generating', async () => {
    mockJson({ status: 'ok', certificate: CERT })
    render(<CoverageCertificatePanel />)

    fireEvent.click(screen.getByRole('button', { name: /generate certificate/i }))

    expect(await screen.findByText('DFSA Handbook')).toBeInTheDocument()
    // The negative-assurance statement is shown verbatim.
    expect(screen.getByText(/every gap is disclosed/i)).toBeInTheDocument()
    // The no-coverage source is flagged, not hidden (exact-case label matches the
    // chip + summary tile, not the lowercase disclaimer prose).
    expect(screen.getAllByText('No coverage').length).toBeGreaterThan(0)
    expect(
      screen.getByText(/no successful check was recorded for this source/i),
    ).toBeInTheDocument()
    // Changed source still renders.
    expect(screen.getByText('CBUAE Rulebook')).toBeInTheDocument()
  })

  it('shows an error and no certificate when the request fails', async () => {
    mockJson({ message: 'Invalid period.' }, false)
    render(<CoverageCertificatePanel />)

    fireEvent.click(screen.getByRole('button', { name: /generate certificate/i }))

    await waitFor(() => expect(screen.getByText(/invalid period/i)).toBeInTheDocument())
    expect(screen.queryByText('DFSA Handbook')).not.toBeInTheDocument()
  })

  it('surfaces a download failure even after a certificate is already loaded', async () => {
    // Generate (format=json) succeeds; the follow-up markdown download fails.
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', certificate: CERT }) })
      .mockResolvedValueOnce({ ok: false, json: async () => ({ message: 'Server busy.' }) })
    render(<CoverageCertificatePanel />)

    fireEvent.click(screen.getByRole('button', { name: /generate certificate/i }))
    expect(await screen.findByText('DFSA Handbook')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /markdown/i }))

    // The download error must be visible (it is not gated behind status==='error').
    await waitFor(() => expect(screen.getByText(/server busy/i)).toBeInTheDocument())
    // ...and the loaded certificate stays on screen.
    expect(screen.getByText('DFSA Handbook')).toBeInTheDocument()
  })
})

// The Auditor Evidence Room faces an EXAMINER: it must render exactly the
// frozen scope the server returned (sealed records, seals, period, coverage),
// carry the FULL standard disclaimer, and be honest — never optimistic — when
// a link is expired, revoked, or invalid (the API's single 404 shape).
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import RoomPage from '../components/RoomPage'

const ROOM = {
  shared_by: 'Acme Exchange FZE',
  period: { date_from: '2026-03-01', date_to: '2026-03-31' },
  created_at: '2026-07-01T10:00:00+00:00',
  expires_at: '2026-07-31T10:00:00+00:00',
  sources: [
    {
      source_id: 'official-cbuae',
      source_name: 'CBUAE Rulebook',
      regulator: 'CBUAE',
      official_url: 'https://example.gov/cbuae',
    },
  ],
  records: [
    {
      record_id: 'evr_official-cbuae_run-001',
      record_hash: 'sha256:aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899',
      normalized_hash: 'sha256:99887766554433221100ffeeddccbbaa99887766554433221100ffeeddccbbaa',
      timestamp: '2026-03-15T10:00:00Z',
      run_status: 'CHANGED',
      source_id: 'official-cbuae',
      source_name: 'CBUAE Rulebook',
      change_summary: 'Saved official-source snapshot changed against the previous normalized content.',
      diff_excerpt: '- old paragraph\n+ new paragraph',
    },
  ],
  record_count: 1,
  truncated: false,
  coverage: {
    sources_in_scope: 1,
    sources_with_records: 1,
    sources_without_records: 0,
    total_records: 1,
    changed_records: 1,
    first_capture: '2026-03-15T10:00:00Z',
    last_capture: '2026-03-15T10:00:00Z',
  },
  verification: {
    verify_url: '/verify',
    spec_url: '/api/verify-spec',
    note: 'Each record below carries the SHA-256 seal StatuteProof recorded at capture time.',
  },
  note: 'This is a read-only view of monitoring evidence that the account holder chose to share for regulatory review.',
  disclaimer: 'Monitoring intelligence only. Not legal advice.',
  legal_notice:
    'StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured.',
}

function mockFetch(payload, { ok = true, status = 200 } = {}) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('RoomPage', () => {
  it('renders the shared scope: records, seals, sources, and coverage', async () => {
    mockFetch({ ok: true, room: ROOM })
    render(<RoomPage token="test-token-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />)

    await waitFor(() => {
      expect(screen.getByText('Evidence shared for regulatory review')).toBeInTheDocument()
    })
    expect(screen.getByText(/Shared by/i)).toBeInTheDocument()
    expect(screen.getByText('Acme Exchange FZE')).toBeInTheDocument()
    // The sealed record with its hash (truncated display, full value in title).
    expect(screen.getAllByText('CBUAE Rulebook').length).toBeGreaterThan(0)
    const sealEl = screen.getByTitle(ROOM.records[0].record_hash)
    expect(sealEl).toBeInTheDocument()
    expect(sealEl.textContent).toContain('sha256:aabbccddeeff')
    // The normalized-content hash (what /verify checks) is shown per record.
    const normalizedEl = screen.getByTitle(ROOM.records[0].normalized_hash)
    expect(normalizedEl.textContent).toContain('sha256:998877665544')
    expect(screen.getByText('evr_official-cbuae_run-001')).toBeInTheDocument()
    expect(screen.getByText(/changed against the previous normalized content/)).toBeInTheDocument()
    // Period + expiry honesty.
    expect(screen.getByText(/2026-03-01/)).toBeInTheDocument()
    expect(screen.getByText('2026-07-31T10:00:00+00:00')).toBeInTheDocument()
    // Independent verification affordances.
    expect(screen.getByRole('link', { name: /open the public verifier/i })).toHaveAttribute('href', '/verify')
    expect(screen.getByRole('link', { name: /verification specification/i })).toHaveAttribute(
      'href',
      '/api/verify-spec',
    )
  })

  it('always carries the full standard disclaimer for the examiner', async () => {
    mockFetch({ ok: true, room: ROOM })
    render(<RoomPage token="test-token-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />)

    await waitFor(() => {
      expect(screen.getByText('Monitoring intelligence only. Not legal advice.')).toBeInTheDocument()
    })
    expect(
      screen.getByText(/does not guarantee compliance, prevent fines, or certify/i),
    ).toBeInTheDocument()
  })

  it('shows an honest not-available state for expired/revoked/invalid links', async () => {
    mockFetch(
      {
        ok: false,
        error: 'not_found',
        message: 'This evidence room link is not available. It may have expired or been revoked.',
      },
      { ok: false, status: 404 },
    )
    render(<RoomPage token="expired-token-aaaaaaaaaaaaaaaaaaaaaaaaaaaa" />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(screen.getByText('Link not available')).toBeInTheDocument()
    expect(
      screen.getByText(/It may have expired or been revoked/),
    ).toBeInTheDocument()
    // No optimistic content leaks into the error state.
    expect(screen.queryByText('CBUAE Rulebook')).not.toBeInTheDocument()
  })

  it('treats a missing token as not available without calling the API', async () => {
    globalThis.fetch = vi.fn()
    render(<RoomPage token="" />)

    await waitFor(() => {
      expect(screen.getByText('Link not available')).toBeInTheDocument()
    })
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })

  it('discloses gaps honestly when sources in scope have no records', async () => {
    mockFetch({
      ok: true,
      room: {
        ...ROOM,
        records: [],
        record_count: 0,
        coverage: { ...ROOM.coverage, total_records: 0, changed_records: 0, sources_without_records: 1 },
      },
    })
    render(<RoomPage token="test-token-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" />)

    await waitFor(() => {
      expect(screen.getByText(/No sealed records exist for this scope yet/)).toBeInTheDocument()
    })
    expect(screen.getByText(/Gaps are disclosed, not hidden/)).toBeInTheDocument()
  })
})

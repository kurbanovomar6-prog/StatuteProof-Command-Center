// Every reviewed alert must carry its proof: when a routing match binds to a
// sealed evidence record, "View proof" reveals the record id, the self-seal
// hash, the bounded diff excerpt, and the two verification actions. When no
// sealed record is linked, the card says so honestly — no fake seal, no
// invented linkage.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import AlertsPage from '../components/app/AlertsPage'
import AlertProofPanel from '../components/app/AlertProofPanel'

const SEAL = `sha256:${'ab'.repeat(32)}`

const SEALED_MATCH = {
  alert_id: 'draft-sealed01',
  title: 'CBUAE rulebook update',
  source_name: 'CBUAE Rulebook',
  market: 'AE',
  risk_level: 'MEDIUM',
  review_status: 'APPROVED_FOR_WEEKLY',
  matched: true,
  score: 65,
  delivery_ready: false,
  already_sent: false,
  not_ready_reasons: ['Telegram is not connected.'],
  executive_summary: 'Reviewed change to the reporting form.',
  diff_excerpt: '+ Firms must submit the return by 1 September 2026.',
  detected_at: '2026-07-10T09:00:00Z',
  source_url: 'https://example.gov/rulebook',
  proof: {
    evidence_record_id: 'evr_AE-cbuae-proof_run00001',
    record_hash: SEAL,
    run_id: 'run00001',
    diff_available: true,
    normalized_hash: `sha256:${'cd'.repeat(32)}`,
  },
}

const UNSEALED_MATCH = {
  ...SEALED_MATCH,
  alert_id: 'draft-orphan01',
  title: 'DFSA notice update',
  source_name: 'DFSA Notices',
  proof: null,
}

function mockPreviewFetch(matches) {
  globalThis.fetch = vi.fn((url) => {
    const target = String(url)
    if (target.includes('/api/delivery/preview')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, preview: { matches, profile_ready: true, not_ready_reasons: [] } }),
      })
    }
    if (target.includes('/api/alerts/action-log')) {
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, entries: [] }) })
    }
    return Promise.resolve({ ok: true, json: async () => ({ ok: true }) })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AlertProofPanel', () => {
  it('reveals the seal, record id, excerpt, and both verification links', async () => {
    // No structured redline from the API → the panel falls back to the raw
    // excerpt the alert already carries (rendered via AlertRedline).
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, redline: { available: false, blocks: [], note: '' } }),
      }),
    )
    render(<AlertProofPanel item={SEALED_MATCH} />)

    // Collapsed by default — the seal is not on screen yet.
    expect(screen.queryByText(/sealed evidence record/i)).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /view proof/i }))

    expect(screen.getByText('Sealed evidence record — re-check its hashes yourself.')).toBeInTheDocument()
    expect(screen.getByText('evr_AE-cbuae-proof_run00001')).toBeInTheDocument()
    // The seal renders shortened but carries the full hash as its title.
    expect(screen.getByTitle(SEAL)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText(SEALED_MATCH.diff_excerpt)).toBeInTheDocument()
    })

    const evidenceLink = screen.getByRole('link', { name: /open evidence record/i })
    expect(evidenceLink).toHaveAttribute('href', '/app/evidence')
    const verifyLink = screen.getByRole('link', { name: /verify independently/i })
    expect(verifyLink).toHaveAttribute('href', '/verify')
    expect(
      screen.getByText(/Open the evidence record .* then paste it into the public verifier/i),
    ).toBeInTheDocument()
  })

  it('uses in-app navigation for the evidence link when navigate is provided', () => {
    const navigate = vi.fn()
    render(<AlertProofPanel item={SEALED_MATCH} navigate={navigate} />)

    fireEvent.click(screen.getByRole('button', { name: /view proof/i }))
    fireEvent.click(screen.getByRole('link', { name: /open evidence record/i }))

    expect(navigate).toHaveBeenCalledWith('evidence')
  })

  it('shows the honest empty state when no sealed record is linked', () => {
    render(<AlertProofPanel item={UNSEALED_MATCH} />)

    expect(screen.getByText('No sealed record is linked to this alert.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /view proof/i })).not.toBeInTheDocument()
  })
})

describe('AlertsPage proof binding', () => {
  it('renders View proof only for the sealed match and the empty state for the orphan', async () => {
    mockPreviewFetch([SEALED_MATCH, UNSEALED_MATCH])
    render(<AlertsPage />)

    const sealedCard = (await screen.findByText('CBUAE rulebook update')).closest('article')
    const orphanCard = screen.getByText('DFSA notice update').closest('article')

    expect(within(sealedCard).getByRole('button', { name: /view proof/i })).toBeInTheDocument()
    expect(within(sealedCard).queryByText('No sealed record is linked to this alert.')).not.toBeInTheDocument()

    expect(within(orphanCard).getByText('No sealed record is linked to this alert.')).toBeInTheDocument()
    expect(within(orphanCard).queryByRole('button', { name: /view proof/i })).not.toBeInTheDocument()

    // The page-level legal framing stays present.
    expect(screen.getAllByText(/monitoring intelligence only\. not legal advice/i).length).toBeGreaterThan(0)
  })
})

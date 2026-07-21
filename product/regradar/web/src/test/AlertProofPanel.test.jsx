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

// What the backend actually returns for a non plan-eligible account: the text
// fields emptied, the official URL nulled, `proof` kept, and the plan_redacted
// marker set. The card must read the marker — not the emptiness.
const REDACTED_MATCH = {
  ...SEALED_MATCH,
  alert_id: 'draft-redact01',
  title: 'VARA rulebook update',
  source_name: 'VARA Rulebooks',
  executive_summary: '',
  business_action: '',
  diff_excerpt: null,
  source_url: null,
  plan_redacted: true,
  redacted_fields: ['executive_summary', 'business_action', 'diff_excerpt', 'source_url', 'url'],
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

  it('says the sealed text is withheld — never that no record exists — when the plan redacts it', async () => {
    // Backend redaction keeps `proof` (record id + seal) and nulls the paid
    // content. The panel must not fetch the redline (the API answers 402) and
    // must not imply the evidence trail is empty.
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 402, json: async () => ({ ok: false, reason: 'plan_required' }) }),
    )
    const redacted = { ...SEALED_MATCH, plan_redacted: true, diff_excerpt: null, source_url: null }
    render(<AlertProofPanel item={redacted} />)

    fireEvent.click(screen.getByRole('button', { name: /view proof/i }))

    expect(screen.getByText('evr_AE-cbuae-proof_run00001')).toBeInTheDocument()
    expect(screen.queryByText(/no sealed record is linked/i)).not.toBeInTheDocument()
    expect(screen.getByText(/withheld on your current plan/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(globalThis.fetch).not.toHaveBeenCalled()
    })
  })

  it('does not promise hash re-checking to the tier that cannot export the record', () => {
    // A plan_redacted user is by definition not plan-eligible: audit_export and
    // pdf_export are False, so /api/evidence/pack and export-download answer 403
    // and the diff answers 402 — there is no route to the record JSON the public
    // verifier needs. Saying "re-check its hashes yourself" here is a promise the
    // code cannot fulfil right now, so the redacted branch must name the gate.
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 402, json: async () => ({ ok: false, reason: 'plan_required' }) }),
    )
    const redacted = { ...SEALED_MATCH, plan_redacted: true, diff_excerpt: null, source_url: null }
    render(<AlertProofPanel item={redacted} />)

    fireEvent.click(screen.getByRole('button', { name: /view proof/i }))

    expect(screen.queryByText(/re-check its hashes yourself/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/paste it into the public verifier/i)).not.toBeInTheDocument()
    expect(screen.getByText(/requires an active plan/i)).toBeInTheDocument()
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

  it('says a redacted card is withheld — never that no summary was recorded — and offers the upgrade', async () => {
    // The falsy-fallback ("No executive summary recorded.") is indistinguishable
    // from the redacted state, so it asserts to the customer that monitoring
    // produced nothing for a change it did analyse. That is false, and it is the
    // always-visible card text, not the collapsed proof panel.
    mockPreviewFetch([REDACTED_MATCH])
    render(<AlertsPage />)

    const card = (await screen.findByText('VARA rulebook update')).closest('article')

    expect(within(card).queryByText('No executive summary recorded.')).not.toBeInTheDocument()
    expect(within(card).getByText(/withheld on your current plan/i)).toBeInTheDocument()

    const upgrade = within(card).getByRole('link', { name: /upgrade/i })
    expect(upgrade).toHaveAttribute('href', '/app/billing')
  })

  it('does not claim a seal on a redacted card that carries no sealed record', async () => {
    // `proof` is fail-soft by contract (app/alert_proof.py): a match can reach
    // the preview with proof=null, and the plan redaction deliberately leaves it
    // alone. The withholding copy must therefore not assert "its evidence record
    // is sealed" — the panel directly below says the opposite.
    mockPreviewFetch([{ ...REDACTED_MATCH, alert_id: 'draft-redact02', title: 'SCA rulebook update', proof: null }])
    render(<AlertsPage />)

    const card = (await screen.findByText('SCA rulebook update')).closest('article')

    expect(within(card).getByText('No sealed record is linked to this alert.')).toBeInTheDocument()
    expect(within(card).getByText(/withheld on your current plan/i)).toBeInTheDocument()
    expect(within(card).queryByText(/evidence record is sealed/i)).not.toBeInTheDocument()
  })
})

// The enforcement-monitoring capability is StatuteProof's top differentiator,
// but it is only ever surfaced from REAL data: the "Enforcement" badge and the
// "Enforcement" filter key off item.change_type === 'ENFORCEMENT', which the
// backend (app/alert_drafts.classify_change_type) sets from actual
// penalty/sanction/enforcement/revocation/suspension wording in the diff. A
// non-enforcement change must never show the badge or pass the filter — no
// heuristic guess, no overclaim.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import AlertsPage from '../components/app/AlertsPage'

const ENFORCEMENT_MATCH = {
  alert_id: 'draft-enf01',
  title: 'DFSA enforcement decision published',
  source_name: 'DFSA Enforcement',
  market: 'AE',
  risk_level: 'HIGH',
  change_type: 'ENFORCEMENT',
  review_status: 'APPROVED_FOR_WEEKLY',
  matched: true,
  score: 70,
  delivery_ready: false,
  already_sent: false,
  not_ready_reasons: ['Telegram is not connected.'],
  executive_summary: 'Reviewed change to a published enforcement decision.',
  detected_at: '2026-07-10T09:00:00Z',
  source_url: 'https://example.gov/enforcement',
  proof: null,
}

const NON_ENFORCEMENT_MATCH = {
  ...ENFORCEMENT_MATCH,
  alert_id: 'draft-cons01',
  title: 'CBUAE consultation opened',
  source_name: 'CBUAE Consultations',
  change_type: 'CONSULTATION',
  executive_summary: 'Reviewed change to a public consultation page.',
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

describe('AlertsPage enforcement surfacing', () => {
  it('shows the Enforcement badge only on a genuinely enforcement-classified alert', async () => {
    mockPreviewFetch([ENFORCEMENT_MATCH, NON_ENFORCEMENT_MATCH])
    render(<AlertsPage />)

    const enfCard = (await screen.findByText('DFSA enforcement decision published')).closest('article')
    const consCard = screen.getByText('CBUAE consultation opened').closest('article')

    expect(within(enfCard).getByText('Enforcement')).toBeInTheDocument()
    expect(within(consCard).queryByText('Enforcement')).not.toBeInTheDocument()
  })

  it('the Enforcement filter keeps enforcement alerts and drops non-enforcement ones', async () => {
    mockPreviewFetch([ENFORCEMENT_MATCH, NON_ENFORCEMENT_MATCH])
    render(<AlertsPage />)

    // Both cards visible before filtering.
    await screen.findByText('DFSA enforcement decision published')
    expect(screen.getByText('CBUAE consultation opened')).toBeInTheDocument()

    // Activate the Enforcement filter toggle (the filter-row control, not a card
    // badge). getByRole disambiguates it from the badge span.
    fireEvent.click(screen.getByRole('button', { name: 'Enforcement' }))

    expect(screen.getByText('DFSA enforcement decision published')).toBeInTheDocument()
    expect(screen.queryByText('CBUAE consultation opened')).not.toBeInTheDocument()

    // Toggling off restores the non-enforcement alert.
    fireEvent.click(screen.getByRole('button', { name: 'Enforcement' }))
    expect(screen.getByText('CBUAE consultation opened')).toBeInTheDocument()
  })

  it('surfaces the enforcement signal honestly on a plan-redacted card (change_type is not redacted)', async () => {
    // Plan redaction empties the paid text/URLs but leaves change_type intact, so
    // the badge still correctly says a monitored enforcement page changed without
    // revealing the withheld content.
    const redactedEnforcement = {
      ...ENFORCEMENT_MATCH,
      alert_id: 'draft-enf-redact01',
      title: 'SCA enforcement notice published',
      source_name: 'SCA Enforcement',
      executive_summary: '',
      business_action: '',
      source_url: null,
      plan_redacted: true,
    }
    mockPreviewFetch([redactedEnforcement])
    render(<AlertsPage />)

    const card = (await screen.findByText('SCA enforcement notice published')).closest('article')
    expect(within(card).getByText('Enforcement')).toBeInTheDocument()
    expect(within(card).getByText(/withheld on your current plan/i)).toBeInTheDocument()
  })
})

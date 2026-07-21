// First-session demonstration honesty. A brand-new free signup (evidence_preview
// plan, official_alerts:false, source_limit:0) lands on an EMPTY Alerts page and
// otherwise cannot experience the product's differentiating loop — an
// evidence-backed alert with a verifiable sealed diff — without a founder
// activating a plan. So the empty state renders ONE clearly-labelled SAMPLE card
// built from the real sealed DIFC record shipped at
// web/public/sample-record-changed/ (the same bytes /verify#sample loads), with:
//   - the word "Sample" and a "not your own monitored data" disclosure, so it is
//     impossible to mistake for the customer's own monitoring;
//   - a working "Verify this yourself" deep-link to /verify#sample;
//   - an honest next-step line, no promise of a channel/cadence the code lacks.
// An ACTIVATED account (official_alerts:true) never sees the sample — not when it
// has real alerts, and not when it is merely empty.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import AlertsPage from '../components/app/AlertsPage'

const FREE_PLAN = {
  plan_name: 'evidence_preview',
  active_plan_name: 'evidence_preview',
  status: 'evidence_preview',
  active_capabilities: { official_alerts: false, source_limit: 0, liveMonitoring: false },
  capabilities: { official_alerts: false, source_limit: 0 },
}

const ACTIVE_PLAN = {
  plan_name: 'professional',
  active_plan_name: 'professional',
  status: 'active',
  active_capabilities: { official_alerts: true, source_limit: 172, liveMonitoring: false },
  capabilities: { official_alerts: true, source_limit: 172 },
}

const REAL_MATCH = {
  alert_id: 'draft-real01',
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
  source_url: 'https://example.gov/rulebook',
  proof: null,
}

function mockApi({ plan, matches }) {
  globalThis.fetch = vi.fn((url) => {
    const target = String(url)
    if (target.includes('/api/plan')) {
      return Promise.resolve({ ok: true, json: async () => ({ ok: true, plan }) })
    }
    if (target.includes('/api/delivery/preview')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true, preview: { matches, profile_ready: true, not_ready_reasons: [] } }),
      })
    }
    return Promise.resolve({ ok: true, json: async () => ({ ok: true, entries: [] }) })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('first-session SAMPLE demonstration (free/unactivated account)', () => {
  it('renders exactly one clearly-labelled SAMPLE card with a working /verify#sample link', async () => {
    mockApi({ plan: FREE_PLAN, matches: [] })
    render(<AlertsPage />)

    const verifyLinks = await screen.findAllByRole('link', { name: /verify this yourself/i })
    expect(verifyLinks).toHaveLength(1)
    expect(verifyLinks[0]).toHaveAttribute('href', '/verify#sample')

    // The word "Sample" must be on screen (badge + explanatory label).
    expect(screen.getAllByText(/sample/i).length).toBeGreaterThan(0)

    // The explanatory label naming it a real sealed record from an official source.
    expect(
      screen.getByText(/a real sealed record from an official source/i),
    ).toBeInTheDocument()

    // The card is built from the REAL captured DIFC record, not fabricated text.
    expect(screen.getByText(/DIFC Laws and Regulations/)).toBeInTheDocument()
  })

  it('states in plain words that the sample is NOT the customer\'s own monitored data', async () => {
    mockApi({ plan: FREE_PLAN, matches: [] })
    render(<AlertsPage />)

    await screen.findByText(/a real sealed record from an official source/i)
    expect(screen.getByText(/not your own monitored data/i)).toBeInTheDocument()
  })

  it('shows an honest next-step line without promising a channel or cadence', async () => {
    mockApi({ plan: FREE_PLAN, matches: [] })
    render(<AlertsPage />)

    const nextStep = await screen.findByText(
      /your monitored sources appear here once your plan is activated/i,
    )
    expect(nextStep).toBeInTheDocument()
    // No delivery-channel promise the code cannot fulfil in the first session.
    expect(nextStep.textContent).not.toMatch(/telegram|e-?mail|inbox|every|never miss|guarantee/i)
  })
})

describe('the SAMPLE demonstration never reaches an activated account', () => {
  it('does not show the sample when an activated account has real alerts', async () => {
    mockApi({ plan: ACTIVE_PLAN, matches: [REAL_MATCH] })
    render(<AlertsPage />)

    // The real alert renders...
    await screen.findByText('CBUAE rulebook update')
    // ...and the sample demonstration does not.
    expect(screen.queryByRole('link', { name: /verify this yourself/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/a real sealed record from an official source/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/not your own monitored data/i)).not.toBeInTheDocument()
  })

  it('does not show the sample when an activated account is merely empty', async () => {
    mockApi({ plan: ACTIVE_PLAN, matches: [] })
    render(<AlertsPage />)

    // The honest activated empty state renders instead of the sample.
    await screen.findByText(/no reviewed alerts yet/i)
    expect(screen.queryByRole('link', { name: /verify this yourself/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/a real sealed record from an official source/i)).not.toBeInTheDocument()
  })
})

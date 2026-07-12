// A risk band must be legible to colour-blind and screen-reader users: it is
// always colour + TEXT LABEL + a one-line REVIEW-PRIORITY definition, framed as
// suggested review urgency and never as a legal severity / obligation. These
// tests lock that contract on the shared metadata and on the AlertsPage render.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import AlertsPage from '../components/app/AlertsPage'
import { RISK_BANDS, RISK_BAND_LEGEND, riskBand } from '../components/app/riskBands'

// Phrases a customer-facing band string must never contain. Mirrors the intent
// of the backend app/legal_safety guard for the frontend band copy: no legal
// conclusion, no obligation imperative, no compliance guarantee.
const FORBIDDEN = [
  'you must',
  'required action',
  'you are required',
  'ensure compliance',
  'guarantee compliance',
  'guaranteed compliance',
  'you are compliant',
  'stay compliant',
  'legal severity:',
]

function bandStrings() {
  const values = [RISK_BAND_LEGEND]
  for (const band of Object.values(RISK_BANDS)) {
    values.push(band.label, band.priority, band.color)
  }
  return values
}

describe('riskBands metadata', () => {
  it('pairs every band with a label, a token colour, and a review-priority line', () => {
    for (const key of ['HIGH', 'MEDIUM', 'LOW']) {
      const band = RISK_BANDS[key]
      expect(band.label).toBeTruthy()
      // Colour must come from a design token, never a hardcoded hex.
      expect(band.color).toMatch(/^var\(--risk-(high|medium|low)\)$/)
      expect(band.color).not.toMatch(/#[0-9a-f]{3,8}/i)
      // The definition is framed as review priority, not legal severity.
      expect(band.priority.toLowerCase()).toContain('priority:')
    }
    expect(RISK_BANDS.HIGH.priority).toBe('Priority: suggest same-day review')
  })

  it('riskBand() resolves case-insensitively and defaults to MEDIUM', () => {
    expect(riskBand('high')).toBe(RISK_BANDS.HIGH)
    expect(riskBand('LOW')).toBe(RISK_BANDS.LOW)
    expect(riskBand(undefined)).toBe(RISK_BANDS.MEDIUM)
    expect(riskBand('nonsense')).toBe(RISK_BANDS.MEDIUM)
  })

  it('every band string is legal-safe (no obligation / compliance claim)', () => {
    for (const value of bandStrings()) {
      const low = String(value).toLowerCase()
      for (const phrase of FORBIDDEN) {
        expect(low).not.toContain(phrase)
      }
    }
  })

  it('the legend frames priority as review urgency, not a legal conclusion', () => {
    expect(RISK_BAND_LEGEND.toLowerCase()).toContain('review urgency')
    expect(RISK_BAND_LEGEND.toLowerCase()).toContain('not a legal severity')
  })
})

const HIGH_MATCH = {
  alert_id: 'draft-band01',
  title: 'CBUAE rulebook update: monitored change detected — 2026-07-10 09:00 UTC',
  source_name: 'CBUAE Rulebook',
  market: 'AE',
  risk_level: 'HIGH',
  review_status: 'APPROVED_FOR_WEEKLY',
  matched: true,
  score: 72,
  delivery_ready: false,
  already_sent: false,
  not_ready_reasons: ['Telegram is not connected.'],
  executive_summary: 'Reviewed change to the reporting form.',
  source_url: 'https://example.gov/rulebook',
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
    return Promise.resolve({ ok: true, json: async () => ({ ok: true, entries: [] }) })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AlertsPage risk band render', () => {
  it('shows the colour + text label + review-priority definition and the legend', async () => {
    mockPreviewFetch([HIGH_MATCH])
    render(<AlertsPage />)

    const card = (await screen.findByText(/monitored change detected/i)).closest('article')
    // Text label beside the colour (colour is never the only signal).
    expect(within(card).getByText('High risk')).toBeInTheDocument()
    // The review-priority definition renders (visible and via aria-label).
    expect(within(card).getAllByText('Priority: suggest same-day review').length).toBeGreaterThan(0)
    expect(
      within(card).getByLabelText('High risk. Priority: suggest same-day review'),
    ).toBeInTheDocument()

    // The one-line legend defines the bands as review priority once on the page.
    expect(screen.getByText(RISK_BAND_LEGEND)).toBeInTheDocument()
  })
})

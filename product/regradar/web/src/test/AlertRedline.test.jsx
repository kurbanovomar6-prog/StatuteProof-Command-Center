// AlertRedline renders the added/removed lines of one alert's SEALED diff (the
// server parses the sealed artifact; nothing is re-diffed client-side), always
// with the monitoring framing + short disclaimer, and falls back honestly to
// the raw excerpt when no structured redline is available.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import AlertRedline from '../components/app/AlertRedline'

const REDLINE = {
  available: true,
  format: 'chunk_report',
  blocks: [
    { op: 'removed', lines: ['The threshold is AED 55,000.'], group: 1 },
    { op: 'added', lines: ['The threshold is AED 15,000.'], group: 1 },
  ],
  added_lines: 1,
  removed_lines: 1,
  truncated: false,
  partial: false,
  note: '',
  framing:
    'This is the text StatuteProof detected as changed in a monitored official source and sealed into a tamper-evident evidence record.',
  disclaimer: 'For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

function mockFetch(redline, { fail = false } = {}) {
  globalThis.fetch = vi.fn(() => {
    if (fail) return Promise.reject(new Error('network down'))
    return Promise.resolve({ ok: true, json: async () => ({ ok: true, redline }) })
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AlertRedline', () => {
  it('renders added and removed sealed lines with counts', async () => {
    mockFetch(REDLINE)
    render(<AlertRedline alertId="draft-x1" />)
    await waitFor(() => {
      expect(screen.getByText('The threshold is AED 15,000.')).toBeInTheDocument()
    })
    expect(screen.getByText('The threshold is AED 55,000.')).toBeInTheDocument()
    expect(screen.getByText(/What changed \(sealed redline\)/i)).toBeInTheDocument()
  })

  it('always renders the framing and short disclaimer with an available redline', async () => {
    mockFetch(REDLINE)
    render(<AlertRedline alertId="draft-x1" />)
    await waitFor(() => {
      expect(
        screen.getByText(/For monitoring information only\. Not legal advice and not a guarantee of compliance\./i),
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/detected as changed in a monitored official source/i)).toBeInTheDocument()
  })

  it('falls back to the raw excerpt when no redline is available', async () => {
    mockFetch({ ...REDLINE, available: false, blocks: [], note: 'No stored diff to render.' })
    render(<AlertRedline alertId="draft-x1" fallbackExcerpt="raw excerpt text" />)
    await waitFor(() => {
      expect(screen.getByText('raw excerpt text')).toBeInTheDocument()
    })
    expect(screen.getByText('No stored diff to render.')).toBeInTheDocument()
    expect(screen.queryByText(/sealed redline/i)).not.toBeInTheDocument()
  })

  it('falls back to the raw excerpt when the request fails', async () => {
    mockFetch(null, { fail: true })
    render(<AlertRedline alertId="draft-x1" fallbackExcerpt="raw excerpt text" />)
    await waitFor(() => {
      expect(screen.getByText('raw excerpt text')).toBeInTheDocument()
    })
  })

  it('discloses truncation honestly', async () => {
    mockFetch({ ...REDLINE, truncated: true })
    render(<AlertRedline alertId="draft-x1" />)
    await waitFor(() => {
      expect(screen.getByText(/redline is truncated/i)).toBeInTheDocument()
    })
  })

  it('frontend-only strings carry no forbidden claims', async () => {
    // The server constants are guarded at import (app/legal_safety); the two
    // strings authored only in the JSX bypass that gate, so guard them here
    // (legal-review process note, 2026-07-12).
    const FORBIDDEN = [
      'guarantee compliance',
      'prevent fines',
      'ai lawyer',
      '100% accurate',
      'never miss',
      'stay compliant automatically',
      'avoid all penalties',
      'proof of compliance',
    ]
    mockFetch({ ...REDLINE, truncated: true, partial: true, note: 'partial note' })
    const { container } = render(<AlertRedline alertId="draft-x1" />)
    await waitFor(() => {
      expect(screen.getByText(/redline is truncated/i)).toBeInTheDocument()
    })
    const text = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(text, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})

// Hero secondary CTA → public verifier. The link must reach /verify#sample
// (deep link that auto-loads the built-in REAL record), prefer SPA navigation
// via the onVerify prop, and carry no forbidden claims.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import Hero from '../components/Hero'

function mockFetch() {
  // Hero + MonitoringStatusBadge both poll /api/health on mount.
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: async () => ({ ok: true, sources_active: 6 }) }),
  )
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('Hero verify CTA', () => {
  it('renders the no-account verifier CTA linking to /verify#sample', () => {
    mockFetch()
    render(<Hero onCreateWorkspace={() => {}} onViewSample={() => {}} />)
    const link = screen.getByRole('link', { name: /verify a record in 60 seconds — no account/i })
    expect(link).toHaveAttribute('href', '/verify#sample')
  })

  it('prefers SPA navigation through onVerify when provided', () => {
    mockFetch()
    const onVerify = vi.fn()
    render(<Hero onCreateWorkspace={() => {}} onViewSample={() => {}} onVerify={onVerify} />)
    fireEvent.click(screen.getByRole('link', { name: /verify a record in 60 seconds/i }))
    expect(onVerify).toHaveBeenCalledTimes(1)
  })

  it('CTA copy carries no forbidden claims', () => {
    const FORBIDDEN = [
      'guarantee compliance',
      'proves compliance',
      'prevent fines',
      'never miss',
      'stay compliant automatically',
      'tamper-proof',
    ]
    mockFetch()
    const { container } = render(<Hero onCreateWorkspace={() => {}} onViewSample={() => {}} />)
    const text = container.textContent.toLowerCase()
    for (const phrase of FORBIDDEN) {
      expect(text, `forbidden phrase rendered: "${phrase}"`).not.toContain(phrase)
    }
  })
})

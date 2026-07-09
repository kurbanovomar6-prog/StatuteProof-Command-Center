// Eval finding N3 — the hero "Monitoring active" badge was a hardcoded
// static claim with a pulsing live-dot while no monitoring ran anywhere.
// The badge must reflect /api/health truthfully and fall back to an
// honest non-live wording when monitoring is stale, absent, or unknown.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import MonitoringStatusBadge from '../components/MonitoringStatusBadge'

function mockHealth(payload, ok = true) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    json: async () => payload,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('MonitoringStatusBadge', () => {
  it('shows Monitoring active only when last_run_at is fresh (<24h)', async () => {
    const fresh = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    mockHealth({ ok: true, last_run_at: fresh })
    render(<MonitoringStatusBadge />)
    await waitFor(() =>
      expect(screen.getByText(/monitoring active/i)).toBeInTheDocument(),
    )
  })

  it('shows honest fallback when last_run_at is stale', async () => {
    const stale = new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString()
    mockHealth({ ok: true, last_run_at: stale })
    render(<MonitoringStatusBadge />)
    await waitFor(() =>
      expect(
        screen.getByText(/monitoring configured — activation pending/i),
      ).toBeInTheDocument(),
    )
    expect(screen.queryByText(/monitoring active/i)).not.toBeInTheDocument()
  })

  it('shows honest fallback when last_run_at is null', async () => {
    mockHealth({ ok: true, last_run_at: null })
    render(<MonitoringStatusBadge />)
    await waitFor(() =>
      expect(
        screen.getByText(/monitoring configured — activation pending/i),
      ).toBeInTheDocument(),
    )
  })

  it('never claims active when health is unreachable', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('down'))
    render(<MonitoringStatusBadge />)
    await waitFor(() =>
      expect(
        screen.getByText(/monitoring configured — activation pending/i),
      ).toBeInTheDocument(),
    )
    expect(screen.queryByText(/monitoring active/i)).not.toBeInTheDocument()
  })
})

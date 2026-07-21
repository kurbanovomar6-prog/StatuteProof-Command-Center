// Founder admin panel — the founder sees the account roster and can activate a
// plan (with a confirm step); a non-founder account is answered 403 by the
// server and the page shows a plain "not available" state, never the roster.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AdminPage from '../components/app/AdminPage'

const ACCOUNTS = [
  {
    id: 7,
    email: 'customer@acme.io',
    email_verified: true,
    plan_name: 'professional',
    plan_display: 'UAE Monitor',
    activated_plan: 'evidence_preview',
    active_plan_display: 'Source Readiness Review',
    plan_intent_at: '2026-07-20T09:00:00Z',
    telegram_linked: false,
    created_at: '2026-07-01T09:00:00Z',
    needs_activation: true,
  },
]

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AdminPage', () => {
  it('shows the roster and activates a plan with a confirm step (founder)', async () => {
    const calls = []
    globalThis.fetch = vi.fn((url, options) => {
      const target = String(url)
      calls.push({ target, options })
      if (target.includes('/api/admin/accounts')) {
        return Promise.resolve({ ok: true, json: async () => ({ ok: true, accounts: ACCOUNTS }) })
      }
      if (target.includes('/api/admin/activate-plan')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ok: true, message: 'Activated UAE Monitor for customer@acme.io.' }),
        })
      }
      return Promise.resolve({ ok: true, json: async () => ({ ok: true }) })
    })

    render(<AdminPage />)

    // The roster renders the customer.
    await waitFor(() => {
      expect(screen.getByText('customer@acme.io')).toBeInTheDocument()
    })

    // Activation requires an explicit confirm step.
    fireEvent.click(screen.getByRole('button', { name: /^activate$/i }))
    expect(screen.getByText(/Activate .* for customer@acme.io\?/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^confirm$/i }))

    await waitFor(() => {
      expect(screen.getByText(/Activated UAE Monitor for customer@acme.io\./i)).toBeInTheDocument()
    })

    const activateCall = calls.find((c) => c.target.includes('/api/admin/activate-plan'))
    expect(activateCall).toBeTruthy()
    const body = JSON.parse(activateCall.options.body)
    expect(body).toMatchObject({ user_id: 7, plan_name: 'professional' })
  })

  it('shows a plain not-available state when the server answers 403 (non-founder)', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 403, json: async () => ({ ok: false, message: 'Not available.' }) }),
    )

    render(<AdminPage />)

    await waitFor(() => {
      expect(screen.getByText(/Admin tools are not available/i)).toBeInTheDocument()
    })
    // The roster must never render for a non-founder.
    expect(screen.queryByText('customer@acme.io')).not.toBeInTheDocument()
  })
})

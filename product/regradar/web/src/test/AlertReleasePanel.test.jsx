// The release panel fronts the gate between a drafted alert and every customer's
// inbox, so what is pinned here is mostly what it must REFUSE to do:
// never call a HIGH-risk approval "weekly only", never let a blocked approval
// through without a written reason, and never turn a 409 safety block into a
// generic error the operator would retry blindly.
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import AlertReleasePanel from '../components/app/AlertReleasePanel'

const mocks = vi.hoisted(() => ({
  queue: vi.fn(),
  review: vi.fn(),
}))

vi.mock('../api', () => ({
  admin: {
    alertReviewQueue: mocks.queue,
    reviewAlert: mocks.review,
  },
}))

const RISKY = {
  alert_id: 'draft-risky',
  source_id: 'AE-vara',
  source_name: 'VARA',
  risk_level: 'HIGH',
  confidence: 'LOW',
  status: 'DRAFT',
  safety_issues: ['proof_quality is INCOMPLETE', 'confidence is LOW'],
  delivery_if_approved: 'instant Telegram to every matched customer on the next cycle',
  last_review: null,
}

function err(status, payload) {
  const e = new Error(payload?.message || `HTTP ${status}`)
  e.status = status
  e.payload = payload
  return e
}

afterEach(() => { vi.clearAllMocks() })

describe('AlertReleasePanel', () => {
  it('states the real blast radius instead of the cadence label', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })

    render(<AlertReleasePanel />)

    expect(await screen.findByText(/instant telegram to every matched customer/i))
      .toBeInTheDocument()
    // "Weekly" would read as the safe option; digest_cadence routes on risk_level.
    expect(screen.queryByText(/weekly brief only/i)).not.toBeInTheDocument()
  })

  it('shows the safety issues the server reported', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })

    render(<AlertReleasePanel />)

    expect(await screen.findByText('proof_quality is INCOMPLETE')).toBeInTheDocument()
    expect(screen.getByText('confidence is LOW')).toBeInTheDocument()
  })

  it('turns a 409 into the override flow, not an error', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })
    mocks.review.mockRejectedValue(err(409, {
      code: 'safety_blocked',
      message: 'Approval blocked by safety checks.',
      safety_issues: ['proof_quality is INCOMPLETE'],
    }))

    render(<AlertReleasePanel />)
    fireEvent.click(await screen.findByRole('button', { name: /^approve$/i }))

    expect(await screen.findByRole('alertdialog')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('will not override without a written reason', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })
    mocks.review.mockRejectedValue(err(409, { safety_issues: ['x'] }))

    render(<AlertReleasePanel />)
    fireEvent.click(await screen.findByRole('button', { name: /^approve$/i }))
    await screen.findByRole('alertdialog')

    const override = screen.getByRole('button', { name: /override and approve/i })
    expect(override).toBeDisabled()

    fireEvent.change(screen.getByPlaceholderText(/why is this safe/i), {
      target: { value: 'Checked the regulator page by hand.' },
    })
    expect(override).toBeEnabled()
  })

  it('sends force with the reason when overriding', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })
    mocks.review
      .mockRejectedValueOnce(err(409, { safety_issues: ['x'] }))
      .mockResolvedValueOnce({ ok: true })

    render(<AlertReleasePanel />)
    fireEvent.click(await screen.findByRole('button', { name: /^approve$/i }))
    await screen.findByRole('alertdialog')
    fireEvent.change(screen.getByPlaceholderText(/why is this safe/i), {
      target: { value: 'Verified manually.' },
    })
    fireEvent.click(screen.getByRole('button', { name: /override and approve/i }))

    await waitFor(() => expect(mocks.review).toHaveBeenCalledTimes(2))
    expect(mocks.review).toHaveBeenLastCalledWith({
      alertId: 'draft-risky',
      action: 'approve_weekly',
      note: 'Verified manually.',
      force: true,
    })
  })

  it('renders nothing at all for a non-founder', async () => {
    mocks.queue.mockRejectedValue(err(403, { message: 'Not available.' }))

    const { container } = render(<AlertReleasePanel />)

    await waitFor(() => expect(container).toBeEmptyDOMElement())
  })

  it('reports a real failure as an error', async () => {
    mocks.queue.mockResolvedValue({ ok: true, alerts: [RISKY] })
    mocks.review.mockRejectedValue(err(500, { message: 'Internal error.' }))

    render(<AlertReleasePanel />)
    fireEvent.click(await screen.findByRole('button', { name: /^approve$/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/internal error/i)
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })
})

// The screen must not say "Check your email" when nothing was sent.
//
// Registration used to fire the verification mail into a thread whose result was
// discarded, so the success screen appeared regardless. A customer whose mail
// silently failed waited for a message that did not exist — and could not sign
// in, because login refuses an unverified account. The API now reports
// `verification_email_sent`; these tests pin that the screen repeats it rather
// than showing the reassuring version unconditionally.

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegisterPage from '../components/auth/RegisterPage'

vi.mock('../api', () => ({
  auth: {
    register: vi.fn(),
    googleStatus: vi.fn().mockResolvedValue({ available: false, message: 'Google not configured' }),
    resendVerification: vi.fn(),
    googleStartUrl: vi.fn().mockReturnValue('/api/auth/google/start?next=%2Fapp'),
  },
}))

const { auth } = await import('../api')

async function submitRegistration(user) {
  await user.type(screen.getByPlaceholderText(/^First$/i), 'Alice')
  await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'alice@acme.com')
  await user.type(screen.getByPlaceholderText(/min\. 8 characters/i), 'password123')
  await user.type(screen.getByPlaceholderText(/your organisation/i), 'Acme Compliance Ltd')
  const [terms, privacy, disclaimer] = screen.getAllByRole('checkbox')
  await user.click(terms)
  await user.click(privacy)
  await user.click(disclaimer)
  await user.click(screen.getByRole('button', { name: /create workspace/i }))
}

function renderRegister() {
  return render(<RegisterPage onRegister={() => {}} onSwitchToLogin={() => {}} />)
}

beforeEach(() => {
  vi.clearAllMocks()
  auth.googleStatus.mockResolvedValue({ available: false, message: 'Google not configured' })
})

describe('RegisterPage — verification email outcome', () => {
  it('says the email was sent when the server confirms it', async () => {
    auth.register.mockResolvedValue({
      ok: true, requires_verification: true, email: 'alice@acme.com',
      verification_email_sent: true,
      message: 'Account created. Check your inbox for the verification link.',
    })
    const user = userEvent.setup()
    renderRegister()

    await submitRegistration(user)

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument(),
    )
  })

  it('does NOT say "Check your email" when the send failed', async () => {
    auth.register.mockResolvedValue({
      ok: true, requires_verification: true, email: 'alice@acme.com',
      verification_email_sent: false,
      message: 'Your account was created, but we could not send the verification email. Use Resend below.',
    })
    const user = userEvent.setup()
    renderRegister()

    await submitRegistration(user)

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /email not sent/i })).toBeInTheDocument(),
    )
    expect(screen.queryByRole('heading', { name: /check your email/i })).toBeNull()
    // The account exists — the customer must be told to resend, not to re-register.
    expect(screen.getByRole('button', { name: /resend/i })).toBeInTheDocument()
  })

  it('reports an unknown outcome honestly instead of claiming success', async () => {
    auth.register.mockResolvedValue({
      ok: true, requires_verification: true, email: 'alice@acme.com',
      verification_email_sent: null,
      message: 'Your account was created. The verification email is still sending — if it has not arrived shortly, use Resend below.',
    })
    const user = userEvent.setup()
    renderRegister()

    await submitRegistration(user)

    await waitFor(() => expect(screen.getByText(/still sending/i)).toBeInTheDocument())
  })

  it('keeps the reassuring copy for an older API that omits the field', async () => {
    auth.register.mockResolvedValue({
      ok: true, requires_verification: true, email: 'alice@acme.com',
    })
    const user = userEvent.setup()
    renderRegister()

    await submitRegistration(user)

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument(),
    )
  })
})

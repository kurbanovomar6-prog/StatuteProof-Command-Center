import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '../components/auth/LoginPage'

// ── Mock the api module ───────────────────────────────────────────────────────
// All auth.* functions default to resolved promises; individual tests override.
vi.mock('../api', () => ({
  auth: {
    login: vi.fn(),
    googleStatus: vi.fn().mockResolvedValue({ available: false, message: 'Google not configured' }),
    resendVerification: vi.fn(),
    googleStartUrl: vi.fn().mockReturnValue('/api/auth/google/start?next=%2Fapp'),
  },
}))

// Pull the mock reference so tests can configure it.
const { auth } = await import('../api')

// ── Helpers ───────────────────────────────────────────────────────────────────
function buildVerificationError(email = 'user@test.com') {
  const err = new Error('Please verify your email before signing in.')
  err.requiresVerification = true
  err.email = email
  return err
}

function renderLogin(props = {}) {
  const onLogin = vi.fn()
  const onRegister = vi.fn()
  render(<LoginPage onLogin={onLogin} onRegister={onRegister} {...props} />)
  return { onLogin, onRegister }
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    auth.googleStatus.mockResolvedValue({ available: false, message: 'Google not configured' })
  })

  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders the sign-in heading', async () => {
    renderLogin()
    expect(screen.getByRole('heading', { name: /sign in to statuteproof/i })).toBeInTheDocument()
  })

  it('renders email and password inputs', async () => {
    renderLogin()
    expect(screen.getByPlaceholderText(/name@company\.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/your password/i)).toBeInTheDocument()
  })

  it('renders the sign-in submit button', async () => {
    renderLogin()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders the disclaimer footer', async () => {
    renderLogin()
    expect(screen.getByText(/monitoring intelligence only/i)).toBeInTheDocument()
  })

  // ── Successful login ───────────────────────────────────────────────────────

  it('calls onLogin with user data after successful login', async () => {
    const user = userEvent.setup()
    const fakeUser = { id: 1, email: 'user@test.com' }
    auth.login.mockResolvedValue({ ok: true, user: fakeUser })

    const { onLogin } = renderLogin()

    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'user@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(onLogin).toHaveBeenCalledWith(fakeUser))
  })

  it('disables the submit button while login is in flight', async () => {
    const user = userEvent.setup()
    let resolve
    auth.login.mockReturnValue(new Promise(r => { resolve = r }))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'user@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    resolve({ ok: true, user: { id: 1 } })
  })

  // ── Failed login ───────────────────────────────────────────────────────────

  it('shows an error message when credentials are wrong', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(new Error('Invalid email or password.'))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'bad@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'wrongpass')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument()
    )
  })

  // ── Email-verification enforcement (P0-7) ─────────────────────────────────

  it('shows the verification banner when login returns requiresVerification=true', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('alice@test.com'))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'alice@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByText(/email not yet verified/i)).toBeInTheDocument()
    )
  })

  it('shows the unverified email address in the verification banner', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('bob@example.org'))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'bob@example.org')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByText('bob@example.org')).toBeInTheDocument()
    )
  })

  it('does NOT show a generic error message when verification is needed', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('carol@test.com'))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'carol@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByText(/email not yet verified/i)).toBeInTheDocument()
    )
    // Generic error div must NOT appear
    expect(screen.queryByText(/could not sign in/i)).not.toBeInTheDocument()
  })

  it('shows the resend-verification button in the banner', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('dan@test.com'))

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'dan@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument()
    )
  })

  it('calls resendVerification when the resend button is clicked', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('eve@test.com'))
    auth.resendVerification.mockResolvedValue({ message: 'Email sent.' })

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'eve@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /resend verification email/i }))

    await waitFor(() =>
      expect(auth.resendVerification).toHaveBeenCalledWith('eve@test.com')
    )
  })

  it('shows confirmation message after resend succeeds', async () => {
    const user = userEvent.setup()
    auth.login.mockRejectedValue(buildVerificationError('frank@test.com'))
    auth.resendVerification.mockResolvedValue({ message: 'Verification email sent. Check your inbox.' })

    renderLogin()
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'frank@test.com')
    await user.type(screen.getByPlaceholderText(/your password/i), 'pass1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /resend verification email/i }))

    await waitFor(() =>
      expect(screen.getByText(/verification email sent/i)).toBeInTheDocument()
    )
  })

  // ── Password visibility toggle ─────────────────────────────────────────────

  it('toggles password visibility when the eye button is clicked', async () => {
    const user = userEvent.setup()
    renderLogin()

    const passwordInput = screen.getByPlaceholderText(/your password/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: /show password/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  // ── Register navigation ────────────────────────────────────────────────────

  it('calls onRegister when the Register link is clicked', async () => {
    const user = userEvent.setup()
    const { onRegister } = renderLogin()

    await user.click(screen.getByRole('button', { name: /register/i }))
    expect(onRegister).toHaveBeenCalledOnce()
  })
})

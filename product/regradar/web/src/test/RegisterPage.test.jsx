import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegisterPage from '../components/auth/RegisterPage'

// ── Mock the api module ───────────────────────────────────────────────────────
vi.mock('../api', () => ({
  auth: {
    register: vi.fn(),
    googleStatus: vi.fn().mockResolvedValue({ available: false, message: 'Google not configured' }),
    resendVerification: vi.fn(),
    googleStartUrl: vi.fn().mockReturnValue('/api/auth/google/start?next=%2Fapp'),
  },
}))

const { auth } = await import('../api')

// ── Helpers ───────────────────────────────────────────────────────────────────
async function fillRequiredFields(user) {
  await user.type(screen.getByPlaceholderText(/^First$/i), 'Alice')
  await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'alice@acme.com')
  await user.type(screen.getByPlaceholderText(/min\. 8 characters/i), 'password123')
  await user.type(screen.getByPlaceholderText(/your organisation/i), 'Acme Compliance Ltd')
}

async function acceptAllCheckboxes(user) {
  const [terms, privacy, disclaimer] = screen.getAllByRole('checkbox')
  await user.click(terms)
  await user.click(privacy)
  await user.click(disclaimer)
}

function renderRegister(props = {}) {
  const onRegister = vi.fn()
  const onLogin = vi.fn()
  render(<RegisterPage onRegister={onRegister} onLogin={onLogin} {...props} />)
  return { onRegister, onLogin }
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    auth.googleStatus.mockResolvedValue({ available: false, message: 'Google not configured' })
  })

  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders the create-workspace heading', () => {
    renderRegister()
    expect(
      screen.getByRole('heading', { name: /create your statuteproof workspace/i })
    ).toBeInTheDocument()
  })

  it('renders first-name, email, password, and company inputs', () => {
    renderRegister()
    expect(screen.getByPlaceholderText(/^First$/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/name@company\.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/min\. 8 characters/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/your organisation/i)).toBeInTheDocument()
  })

  it('renders three consent checkboxes', () => {
    renderRegister()
    expect(screen.getAllByRole('checkbox')).toHaveLength(3)
  })

  it('renders the monitoring-only disclaimer footer', () => {
    renderRegister()
    expect(screen.getByText(/monitoring intelligence only/i)).toBeInTheDocument()
  })

  // ── Validation ─────────────────────────────────────────────────────────────

  it('shows an error if checkboxes are not accepted before submit', async () => {
    const user = userEvent.setup()
    renderRegister()
    await fillRequiredFields(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(
        screen.getByText(/please accept the terms, privacy policy, and legal disclaimer/i)
      ).toBeInTheDocument()
    )
  })

  it('shows an error if first name is only whitespace', async () => {
    const user = userEvent.setup()
    renderRegister()

    // Type whitespace-only first name so the HTML `required` constraint passes
    // but `form.firstName.trim()` returns '' — the JS guard fires.
    await user.type(screen.getByPlaceholderText(/^First$/i), '   ')
    await user.type(screen.getByPlaceholderText(/name@company\.com/i), 'alice@acme.com')
    await user.type(screen.getByPlaceholderText(/min\. 8 characters/i), 'password123')
    await user.type(screen.getByPlaceholderText(/your organisation/i), 'Acme Ltd')
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.getByText(/first name is required/i)).toBeInTheDocument()
    )
  })

  // ── Successful registration → verification screen ─────────────────────────

  it('shows the "Check your email" screen after successful registration', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument()
    )
  })

  it('displays the registered email address in the verification screen', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.getByText('alice@acme.com')).toBeInTheDocument()
    )
  })

  it('does NOT call onRegister when requires_verification is true', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })

    const { onRegister } = renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeInTheDocument()
    )
    expect(onRegister).not.toHaveBeenCalled()
  })

  it('calls onRegister when registration returns a user directly (no verification required)', async () => {
    const user = userEvent.setup()
    const fakeUser = { id: 42, email: 'instant@acme.com' }
    auth.register.mockResolvedValue({ ok: true, user: fakeUser })

    const { onRegister } = renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() => expect(onRegister).toHaveBeenCalledWith(fakeUser))
  })

  // ── Verification screen: resend ────────────────────────────────────────────

  it('shows a resend button on the verification screen', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /resend verification email/i })
      ).toBeInTheDocument()
    )
  })

  it('calls resendVerification when the resend button is clicked', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })
    auth.resendVerification.mockResolvedValue({ message: 'Email sent.' })

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /resend verification email/i })
      ).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /resend verification email/i }))

    await waitFor(() =>
      expect(auth.resendVerification).toHaveBeenCalledWith('alice@acme.com')
    )
  })

  it('shows a success message after resend succeeds', async () => {
    const user = userEvent.setup()
    auth.register.mockResolvedValue({
      ok: true,
      requires_verification: true,
      email: 'alice@acme.com',
    })
    auth.resendVerification.mockResolvedValue({ message: 'Verification email sent. Check your inbox.' })

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /resend verification email/i })
      ).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /resend verification email/i }))

    await waitFor(() =>
      expect(screen.getByText(/verification email sent/i)).toBeInTheDocument()
    )
  })

  // ── Registration API error ─────────────────────────────────────────────────

  it('shows an error message when registration fails', async () => {
    const user = userEvent.setup()
    auth.register.mockRejectedValue(new Error('Email already registered.'))

    renderRegister()
    await fillRequiredFields(user)
    await acceptAllCheckboxes(user)
    await user.click(screen.getByRole('button', { name: /create workspace/i }))

    await waitFor(() =>
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument()
    )
  })

  // ── Password visibility toggle ─────────────────────────────────────────────

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    renderRegister()

    const passwordInput = screen.getByPlaceholderText(/min\. 8 characters/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: /show password/i }))
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: /hide password/i }))
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  // ── Login navigation ───────────────────────────────────────────────────────

  it('calls onLogin when the "Sign in" link is clicked', async () => {
    const user = userEvent.setup()
    const { onLogin } = renderRegister()

    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(onLogin).toHaveBeenCalledOnce()
  })
})

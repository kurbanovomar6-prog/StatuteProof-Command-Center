import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoginPage from '../components/auth/LoginPage'
import RegisterPage from '../components/auth/RegisterPage'
import SettingsPage from '../components/app/SettingsPage'

// The api module is imported by all three pages. Google status resolves to a
// stable value so the auth pages settle; profile/account calls are never
// triggered by a pure render.
vi.mock('../api', () => ({
  auth: {
    login: vi.fn(),
    register: vi.fn(),
    googleStatus: vi.fn().mockResolvedValue({ available: false, message: 'Google not configured' }),
    resendVerification: vi.fn(),
    googleStartUrl: vi.fn().mockReturnValue('/api/auth/google/start?next=%2Fapp'),
  },
  account: { exportData: vi.fn() },
  profile: { update: vi.fn() },
}))

describe('form input label association (accessibility)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('associates the login email and password inputs with their labels', () => {
    render(<LoginPage onLogin={vi.fn()} onRegister={vi.fn()} />)
    // getByLabelText only resolves when label and control are programmatically
    // associated (htmlFor/id or wrapping/aria-label).
    expect(screen.getByLabelText(/work email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
  })

  it('associates every register field control with its label', () => {
    render(<RegisterPage onRegister={vi.fn()} onLogin={vi.fn()} />)
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/work email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument()
    // Selects must be labelled too.
    expect(screen.getByLabelText(/job title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/company type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/primary jurisdiction/i)).toBeInTheDocument()
  })

  it('associates the settings workspace-name and brief-language controls with their labels', () => {
    render(<SettingsPage onResetWorkspace={vi.fn()} planState={null} />)
    expect(screen.getByLabelText(/workspace name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/brief language/i)).toBeInTheDocument()
  })
})

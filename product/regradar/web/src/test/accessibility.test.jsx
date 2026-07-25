// Automated accessibility checks on the screens a customer cannot avoid.
//
// web/testing.md lists accessibility second in its priority order and the repo
// had zero automated checks — no axe, no keyboard assertions beyond three
// getByLabelText calls. This is the floor, not the ceiling: axe catches missing
// labels, bad ARIA, and some contrast, and misses everything about whether the
// flow is actually usable with a keyboard or a screen reader.
//
// Scope is deliberate — the public surfaces that render without a session or a
// backend. Authenticated screens need a fixture that fakes auth AND the API, and
// a check that silently renders an error state would assert nothing.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'
import { axe } from 'vitest-axe'

import RegisterPage from '../components/auth/RegisterPage'
import LoginPage from '../components/auth/LoginPage'
import VerifyEmailPage from '../components/auth/VerifyEmailPage'
import LegalPage from '../components/LegalPage'

vi.mock('../api', () => ({
  auth: {
    register: vi.fn(),
    login: vi.fn(),
    googleStatus: vi.fn().mockResolvedValue({ available: false, message: 'Google not configured' }),
    resendVerification: vi.fn(),
    googleStartUrl: vi.fn().mockReturnValue('/api/auth/google/start?next=%2Fapp'),
    forgotPassword: vi.fn(),
  },
}))

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

async function expectNoViolations(ui) {
  const { container } = render(ui)
  const results = await axe(container)
  const summary = (results.violations || []).map(
    v => `${v.id} (${v.impact}) x${v.nodes.length}: ${v.help}`,
  )
  expect(summary, summary.join('\n')).toEqual([])
}

describe('accessibility — public screens', () => {
  it('register page has no axe violations', async () => {
    await expectNoViolations(<RegisterPage onRegister={() => {}} onSwitchToLogin={() => {}} />)
  })

  it('login page has no axe violations', async () => {
    await expectNoViolations(
      <LoginPage onLogin={() => {}} onSwitchToRegister={() => {}} onForgotPassword={() => {}} />,
    )
  })

  it('email verification page has no axe violations', async () => {
    await expectNoViolations(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)
  })

  it('legal page has no axe violations', async () => {
    await expectNoViolations(<LegalPage onBack={() => {}} />)
  })
})

// The one link every customer clicks.
//
// It used to point at /api/auth/verify-email, so it rendered raw JSON in the
// browser: {"ok": true, "verified": true, "message": "..."}. These tests pin that
// a person now sees a page, that a failed verification is not dressed up as a
// success, and that the single-use token is consumed exactly once.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { StrictMode } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import VerifyEmailPage from '../components/auth/VerifyEmailPage'

function setLocation(search) {
  Object.defineProperty(window, 'location', {
    value: { ...window.location, search },
    writable: true,
    configurable: true,
  })
}

beforeEach(() => {
  setLocation('?token=tok-123')
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function mockFetch(payload, { ok = true } = {}) {
  const spy = vi.fn().mockResolvedValue({ ok, json: async () => payload })
  vi.stubGlobal('fetch', spy)
  return spy
}

describe('VerifyEmailPage', () => {
  it('shows a human success page, not JSON', async () => {
    mockFetch({ ok: true, verified: true, message: 'Email verified. Please sign in to continue.' })
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    expect(await screen.findByText('Email verified')).toBeTruthy()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy()
  })

  it('sends the token from the URL to the verification endpoint', async () => {
    const spy = mockFetch({ ok: true, verified: true })
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    await waitFor(() => expect(spy).toHaveBeenCalled())
    expect(spy.mock.calls[0][0]).toContain('/api/auth/verify-email?token=tok-123')
  })

  it('calls the endpoint once — the token is single-use', async () => {
    const spy = mockFetch({ ok: true, verified: true })
    const { rerender } = render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)
    rerender(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
  })

  it('reports an expired link as a failure rather than a success', async () => {
    mockFetch({ ok: false, message: 'Verification link is invalid or has expired. Please request a new one.' }, { ok: false })
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    expect(await screen.findByText('Could not verify this link')).toBeTruthy()
    expect(screen.queryByText('Email verified')).toBeNull()
  })

  it('treats an already-verified re-click as success (mail scanners pre-fetch the link)', async () => {
    mockFetch({ ok: true, verified: true, message: 'Email already verified. Please sign in to continue.' })
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    expect(await screen.findByText('Email verified')).toBeTruthy()
  })

  it('explains a link with no token instead of calling the endpoint', async () => {
    setLocation('')
    const spy = mockFetch({ ok: true, verified: true })
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    expect(await screen.findByText('Could not verify this link')).toBeTruthy()
    expect(spy).not.toHaveBeenCalled()
  })

  it('does not claim success when the server is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    render(<VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />)

    expect(await screen.findByText('Could not verify this link')).toBeTruthy()
  })

  // Regression: under StrictMode the effect runs twice. The first version paired
  // the once-only ref guard with a cleanup that set a `cancelled` flag, so the
  // cleanup from pass one discarded the only in-flight response while pass two
  // returned early on the guard — the page sat on "Verifying your email…"
  // forever. The plain renderer above does NOT double-invoke, so only this
  // wrapper reproduces it. Caught by loading the real page against a 502.
  it('resolves under StrictMode, where the effect is invoked twice', async () => {
    const spy = mockFetch({ ok: false, message: 'Verification link is invalid or has expired.' }, { ok: false })
    render(
      <StrictMode>
        <VerifyEmailPage onSignIn={() => {}} onBack={() => {}} />
      </StrictMode>,
    )

    expect(await screen.findByText('Could not verify this link')).toBeTruthy()
    expect(screen.queryByText('Verifying your email…')).toBeNull()
    expect(spy).toHaveBeenCalledTimes(1)
  })
})

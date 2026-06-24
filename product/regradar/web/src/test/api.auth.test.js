import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { auth } from '../api'

// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * Build a minimal fetch Response-like object.
 * @param {object} body  – JSON payload
 * @param {number} status – HTTP status
 */
function mockResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────
describe('auth API helpers', () => {
  let fetchSpy

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, 'fetch')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ── auth.login ─────────────────────────────────────────────────────────────

  describe('auth.login', () => {
    it('resolves with the response body on 200', async () => {
      const payload = { ok: true, user: { id: 1, email: 'a@b.com' } }
      fetchSpy.mockResolvedValue(mockResponse(payload, 200))

      const result = await auth.login({ email: 'a@b.com', password: 'pw' })

      expect(result).toEqual(payload)
    })

    it('throws an Error with the server message on 401', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse({ message: 'Invalid email or password.' }, 401)
      )

      await expect(auth.login({ email: 'a@b.com', password: 'wrong' })).rejects.toThrow(
        'Invalid email or password.'
      )
    })

    it('attaches requiresVerification=true when the 403 body says so', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse(
          {
            ok: false,
            message: 'Please verify your email.',
            requires_verification: true,
            email: 'unverified@b.com',
          },
          403
        )
      )

      let caught
      try {
        await auth.login({ email: 'unverified@b.com', password: 'pw' })
      } catch (err) {
        caught = err
      }

      expect(caught).toBeDefined()
      expect(caught.requiresVerification).toBe(true)
      expect(caught.email).toBe('unverified@b.com')
    })

    it('does NOT attach requiresVerification on a plain 401', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse({ message: 'Bad credentials.' }, 401)
      )

      let caught
      try {
        await auth.login({ email: 'a@b.com', password: 'wrong' })
      } catch (err) {
        caught = err
      }

      expect(caught.requiresVerification).toBeFalsy()
    })

    it('falls back to an HTTP-status message when the body has no message', async () => {
      fetchSpy.mockResolvedValue(mockResponse({}, 500))

      await expect(auth.login({ email: 'a@b.com', password: 'pw' })).rejects.toThrow('HTTP 500')
    })

    it('sends credentials:include with the request', async () => {
      fetchSpy.mockResolvedValue(mockResponse({ ok: true, user: { id: 1 } }, 200))

      await auth.login({ email: 'a@b.com', password: 'pw' })

      expect(fetchSpy).toHaveBeenCalledWith(
        '/api/auth/login',
        expect.objectContaining({ credentials: 'include' })
      )
    })
  })

  // ── auth.register ──────────────────────────────────────────────────────────

  describe('auth.register', () => {
    it('resolves with requires_verification payload on 201', async () => {
      const payload = { ok: true, requires_verification: true, email: 'new@b.com' }
      fetchSpy.mockResolvedValue(mockResponse(payload, 201))

      const result = await auth.register({ email: 'new@b.com', password: 'pw123456' })

      expect(result.requires_verification).toBe(true)
      expect(result.email).toBe('new@b.com')
    })

    it('throws with the server message on 409 (duplicate email)', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse({ message: 'Email already registered.' }, 409)
      )

      await expect(
        auth.register({ email: 'dup@b.com', password: 'pw123456' })
      ).rejects.toThrow('Email already registered.')
    })
  })

  // ── auth.resendVerification ────────────────────────────────────────────────

  describe('auth.resendVerification', () => {
    it('resolves with message on success', async () => {
      const payload = { ok: true, message: 'Verification email sent. Check your inbox.' }
      fetchSpy.mockResolvedValue(mockResponse(payload, 200))

      const result = await auth.resendVerification('pending@b.com')

      expect(result.message).toMatch(/verification email sent/i)
    })

    it('POSTs to /api/auth/resend-verification with the email', async () => {
      fetchSpy.mockResolvedValue(mockResponse({ ok: true, message: 'Sent.' }, 200))

      await auth.resendVerification('pending@b.com')

      expect(fetchSpy).toHaveBeenCalledWith(
        '/api/auth/resend-verification',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'pending@b.com' }),
        })
      )
    })
  })

  // ── auth.googleStartUrl ────────────────────────────────────────────────────

  describe('auth.googleStartUrl', () => {
    it('returns the correct URL with next param encoded', () => {
      const url = auth.googleStartUrl('/app')
      expect(url).toBe('/api/auth/google/start?next=%2Fapp')
    })

    it('defaults next to /app when called with no argument', () => {
      const url = auth.googleStartUrl()
      expect(url).toContain('/api/auth/google/start')
      expect(url).toContain('next=')
    })
  })
})

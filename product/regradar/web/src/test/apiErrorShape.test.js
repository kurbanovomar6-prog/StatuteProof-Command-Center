// Components branch on `err.status` to tell "not permitted" from "it broke", and
// read `err.payload` for structured detail like a 409's safety_issues. Those two
// properties are a contract of authRequest, and nothing was pinning it.
//
// It mattered: authRequest used to attach neither, so every component test that
// mocked the api module and hand-built an error WITH a .status passed happily
// while the real branch was dead in the browser. TeamPanel's "only the workspace
// owner can add or remove people" message was unreachable in production for
// exactly that reason.
//
// This test drives the REAL api.js against a stubbed fetch, so it cannot be
// satisfied by a mock that is kinder than reality.
import { describe, it, expect, vi, afterEach } from 'vitest'

import { team, admin } from '../api'

function respondWith(status, body) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('authRequest error shape', () => {
  it('attaches the HTTP status so a caller can branch on 403', async () => {
    respondWith(403, { ok: false, message: 'Not permitted.' })

    const err = await team.members().then(() => null, e => e)

    expect(err).toBeInstanceOf(Error)
    expect(err.status).toBe(403)
    expect(err.message).toBe('Not permitted.')
  })

  it('carries the response payload so structured detail survives', async () => {
    respondWith(409, {
      ok: false,
      code: 'safety_blocked',
      message: 'Approval blocked by safety checks.',
      safety_issues: ['proof_quality is INCOMPLETE', 'confidence is LOW'],
    })

    const err = await admin
      .reviewAlert({ alertId: 'draft-1', action: 'approve_weekly' })
      .then(() => null, e => e)

    expect(err.status).toBe(409)
    expect(err.payload.safety_issues).toEqual([
      'proof_quality is INCOMPLETE',
      'confidence is LOW',
    ])
  })

  it('does not attach a status to a successful response', async () => {
    respondWith(200, { ok: true, members: [] })

    await expect(team.members()).resolves.toEqual({ ok: true, members: [] })
  })

  it('never puts a reviewer in the release request body', async () => {
    // The server rejects a supplied reviewer outright; the client must not be
    // the thing that discovers that.
    respondWith(200, { ok: true })

    await admin.reviewAlert({ alertId: 'draft-1', action: 'reject', note: 'no' })

    const [, options] = globalThis.fetch.mock.calls[0]
    expect(JSON.parse(options.body)).not.toHaveProperty('reviewer')
  })
})

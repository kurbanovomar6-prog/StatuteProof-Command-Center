import { useState, useEffect, useRef } from 'react'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

// The page the emailed verification link lands on.
//
// The link used to point straight at /api/auth/verify-email, so the one link every
// customer clicks rendered raw JSON — {"ok": true, "verified": true, ...} — in the
// browser. This page calls that same endpoint and shows a person the result.
//
// The API deliberately does NOT mint a session here (app/api_auth.py): a mailbox
// security scanner can pre-fetch an emailed GET link, and auto-issuing a cookie
// would hand that party a live session for the victim's account. So this page ends
// at "sign in", never at a logged-in state — the security property is preserved,
// only the presentation changes.

const STATUS = { PENDING: 'pending', OK: 'ok', FAILED: 'failed', NO_TOKEN: 'no_token' }

// Read once, at module scope of the render: whether a token is present is a
// property of the URL, not something an effect discovers, so it belongs in the
// initial state rather than in a synchronous setState inside useEffect.
function tokenFromLocation() {
  return new URLSearchParams(window.location.search).get('token') || ''
}

const NO_TOKEN_MESSAGE =
  'This link is missing its verification token. Open the link from your email exactly as it was sent.'

export default function VerifyEmailPage({ onSignIn, onBack }) {
  const [token] = useState(tokenFromLocation)
  const [status, setStatus] = useState(token ? STATUS.PENDING : STATUS.NO_TOKEN)
  const [message, setMessage] = useState(token ? '' : NO_TOKEN_MESSAGE)
  // Mail scanners pre-fetch links, and React StrictMode double-invokes effects.
  // The token is single-use, so a second call would consume nothing and could
  // report failure for a verification that already succeeded.
  const calledRef = useRef(false)

  useEffect(() => {
    if (!token || calledRef.current) return
    calledRef.current = true

    // No cancelled-flag here, and that is deliberate. StrictMode double-invokes
    // effects: the first pass starts the single allowed request, the cleanup would
    // mark it cancelled, and the second pass returns early on calledRef — so the
    // only response in flight gets discarded and the page sits on "Verifying…"
    // forever. Caught by loading the real page against a backend that answered 502;
    // the unit tests did not reproduce it because the test renderer does not
    // double-invoke the effect the way StrictMode does.
    //
    // calledRef already guarantees exactly one request, which is what the
    // single-use token requires. Setting state after unmount is a no-op in
    // React 18+, so there is nothing left for a cancel flag to protect.
    fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async response => {
        const data = await response.json().catch(() => ({}))
        if (data?.verified) {
          setStatus(STATUS.OK)
          setMessage(data.message || 'Email verified. Please sign in to continue.')
        } else {
          setStatus(STATUS.FAILED)
          setMessage(data?.message || 'Verification link is invalid or has expired. Please request a new one.')
        }
      })
      .catch(() => {
        setStatus(STATUS.FAILED)
        setMessage('We could not reach the server to verify this link. Check your connection and try again.')
      })
  }, [token])

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] p-8">
        {status === STATUS.PENDING && (
          <div className="flex items-center gap-3 text-[var(--text-secondary)]">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            <span>Verifying your email…</span>
          </div>
        )}

        {status === STATUS.OK && (
          <>
            <CheckCircle className="mb-4 h-8 w-8 text-emerald-400" aria-hidden="true" />
            <h1 className="mb-2 text-xl font-semibold text-[var(--text-primary)]">Email verified</h1>
            <p className="mb-6 text-sm text-[var(--text-secondary)]">{message}</p>
            <button
              type="button"
              onClick={onSignIn}
              className="w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-[var(--accent-contrast)]"
            >
              Sign in
            </button>
          </>
        )}

        {(status === STATUS.FAILED || status === STATUS.NO_TOKEN) && (
          <>
            <XCircle className="mb-4 h-8 w-8 text-rose-400" aria-hidden="true" />
            <h1 className="mb-2 text-xl font-semibold text-[var(--text-primary)]">Could not verify this link</h1>
            <p className="mb-6 text-sm text-[var(--text-secondary)]">{message}</p>
            <button
              type="button"
              onClick={onSignIn}
              className="w-full rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)]"
            >
              Go to sign in
            </button>
          </>
        )}

        <button
          type="button"
          onClick={onBack}
          className="mt-4 w-full text-center text-xs text-[var(--text-muted)] underline"
        >
          Back to statuteproof.com
        </button>
      </div>
    </main>
  )
}

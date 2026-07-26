import { useState } from 'react'
import { auth } from '../../api'

export default function ForgotPasswordPage({ onBack }) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      // The endpoint always returns a generic success (no account enumeration),
      // so we always show the same confirmation.
      await auth.forgotPassword(email)
      setSent(true)
    } catch (err) {
      setError(err.message || 'Could not send the reset link. Try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="sp-page-orbit flex min-h-dvh items-center px-4 py-12">
      <div className="relative z-10 mx-auto w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
      <h1 className="text-3xl font-semibold text-slate-950">Reset your password</h1>
      {sent ? (
        <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          If that email is registered, we've sent a password reset link. It is valid for 2 hours.
          Check your inbox (and spam).
        </div>
      ) : (
        <>
          <p className="mt-2 text-sm text-slate-600">
            Enter your account email and we'll send you a link to set a new password.
          </p>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-800">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                autoComplete="email"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
              />
            </label>
            {error && <p className="text-sm text-rose-600">{error}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60"
            >
              {submitting ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        </>
      )}
      <button onClick={onBack} className="mt-6 text-sm text-slate-500 hover:text-slate-900">
        ← Back to sign in
      </button>
      <p className="mt-8 text-xs text-slate-600">Monitoring intelligence only. Not legal advice.</p>
    </div>
    </div>
  )
}

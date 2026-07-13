import { useState } from 'react'
import { auth } from '../../api'

function tokenFromLocation() {
  if (typeof window === 'undefined') return ''
  return new URLSearchParams(window.location.search).get('token') || ''
}

export default function ResetPasswordPage({ onDone }) {
  const [token] = useState(tokenFromLocation)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      await auth.resetPassword(token, password)
      setDone(true)
    } catch (err) {
      setError(err.message || 'This reset link is invalid or has expired. Request a new one.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-6 py-12">
      <h1 className="text-3xl font-semibold text-slate-950">Set a new password</h1>
      {!token ? (
        <p className="mt-4 text-sm text-rose-600">
          This link is missing its reset token. Request a new password reset link.
        </p>
      ) : done ? (
        <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          Your password has been reset. Please sign in with your new password.
          <button onClick={onDone} className="mt-3 block font-semibold text-emerald-900 underline">
            Go to sign in
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-sm font-medium text-slate-800">
            New password
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="min. 8 characters"
              autoComplete="new-password"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
          </label>
          <label className="block text-sm font-medium text-slate-800">
            Confirm new password
            <input
              type="password"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
          </label>
          {error && <p className="text-sm text-rose-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60"
          >
            {submitting ? 'Setting…' : 'Set new password'}
          </button>
        </form>
      )}
      <p className="mt-8 text-xs text-slate-400">Monitoring intelligence only. Not legal advice.</p>
    </div>
  )
}

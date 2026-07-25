import { useEffect, useState } from 'react'
import { CheckCircle, Eye, EyeOff, FileCheck2, LockKeyhole, RadioTower } from 'lucide-react'
import { auth } from '../../api'

function AuthLayout({ children }) {
  const trustRows = [
    ['Evidence', 'hash + timestamp'],
    ['Briefs', 'draft until reviewed'],
    ['Scope', 'selected UAE sources'],
  ]

  return (
    <div className="sp-page-orbit flex min-h-dvh items-center px-4 py-10 text-[var(--text-primary)] selection:bg-[var(--trust-badge)]">
      <div className="relative z-10 mx-auto grid w-full max-w-6xl items-center gap-8 lg:grid-cols-[0.92fr_0.78fr]">
        <aside className="hidden lg:block">
          <a href="/" className="mb-10 flex items-center gap-3 hover:opacity-80 transition-opacity">
            <img src="/brand/regradar-logo-navbar.png" alt="" aria-hidden="true" className="h-10 w-auto" />
            <span className="text-2xl font-extrabold tracking-tight text-[var(--text-primary)]">
              Statute<span className="text-[var(--accent)]">Proof</span>
            </span>
          </a>

          <div className="max-w-xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-1.5 text-xs font-semibold text-[var(--accent-hover)]">
              <LockKeyhole className="h-3.5 w-3.5" />
              Evidence workspace access
            </div>
            <h2 className="text-4xl font-semibold leading-tight text-[var(--text-primary)]">
              Sign in to review source evidence before it becomes a brief.
            </h2>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-[var(--text-secondary)]">
              The account area separates source monitoring, canonical evidence review, draft brief
              preparation, and delivery approval.
            </p>
          </div>

          <div className="mt-8 max-w-lg rounded-3xl border border-[var(--border-muted)] bg-[var(--bg-surface)] p-5">
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
              <RadioTower className="h-4 w-4 text-[var(--accent)]" />
              Workspace boundary
            </div>
            <div className="grid gap-3">
              {trustRows.map(([label, value]) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-[var(--border-muted)] bg-[var(--bg-navy)] px-4 py-3 text-sm">
                  <span className="text-[var(--text-secondary)]">{label}</span>
                  <span className="font-semibold text-[var(--text-primary)]">{value}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-start gap-2 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-xs leading-relaxed text-amber-100/80">
              <FileCheck2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-200" />
              <span>No legal advice, no blanket source claim, and no customer delivery without gates.</span>
            </div>
          </div>
        </aside>

        <section className="sp-paper-panel w-full p-6 sm:p-8">
          {children}
        </section>
      </div>
    </div>
  )
}

export default function LoginPage({ onLogin, onRegister, onForgotPassword }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [verificationNeeded, setVerificationNeeded] = useState(false)
  const [verificationEmail, setVerificationEmail] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')
  const [googleStatus, setGoogleStatus] = useState({ loading: true, available: false, message: '' })

  useEffect(() => {
    let active = true
    auth.googleStatus()
      .then(data => {
        if (active) {
          setGoogleStatus({
            loading: false,
            available: Boolean(data.available),
            message: data.message || '',
          })
        }
      })
      .catch(() => {
        if (active) {
          setGoogleStatus({
            loading: false,
            available: false,
            message: 'Google sign-in is not configured for this environment.',
          })
        }
      })
    return () => { active = false }
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setVerificationNeeded(false)
    setResendMessage('')
    setLoading(true)
    try {
      const data = await auth.login({ email, password })
      onLogin(data.user)
    } catch (err) {
      if (err.requiresVerification) {
        setVerificationNeeded(true)
        setVerificationEmail(err.email || email)
        setError('')
      } else {
        setError(err.message || 'Could not sign in. Check your credentials and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    setResendLoading(true)
    setResendMessage('')
    try {
      const data = await auth.resendVerification(verificationEmail)
      setResendMessage(data.message || 'Verification email sent. Check your inbox.')
    } catch (err) {
      setResendMessage(err.message || 'Could not resend verification email. Please try again.')
    } finally {
      setResendLoading(false)
    }
  }

  function handleGoogleSignIn() {
    setError('')
    if (!googleStatus.available) {
      setError(googleStatus.message || 'Google sign-in is not configured for this environment.')
      return
    }
    window.location.assign(auth.googleStartUrl('/app'))
  }

  const inputCls = 'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 placeholder:text-slate-400 shadow-sm focus:border-cyan-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/10'
  const labelCls = 'block text-xs font-semibold text-slate-600 mb-1.5'

  return (
    <AuthLayout>
      <div className="mb-7">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-900 lg:hidden">
          <LockKeyhole className="h-3.5 w-3.5" />
          Evidence workspace access
        </div>
        <h1 className="text-3xl font-semibold leading-tight text-slate-950">Sign in to StatuteProof</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Review monitored sources, canonical evidence records, and draft brief gates.
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="login-email" className={labelCls}>Work email</label>
          <input
            id="login-email"
            type="email"
            placeholder="name@company.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className={inputCls}
            required
            autoComplete="email"
          />
        </div>

        <div>
          <div className="flex items-center justify-between gap-3">
            <label htmlFor="login-password" className={labelCls}>Password</label>
            {onForgotPassword && (
              <button
                type="button"
                onClick={onForgotPassword}
                className="text-xs font-medium text-slate-500 hover:text-slate-900"
              >
                Forgot password?
              </button>
            )}
          </div>
          <div className="relative">
            <input
              id="login-password"
              type={showPass ? 'text' : 'password'}
              placeholder="Your password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className={`${inputCls} pr-11`}
              required
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPass(v => !v)}
              className="absolute right-2.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              aria-label={showPass ? 'Hide password' : 'Show password'}
            >
              {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
            {error}
          </div>
        )}

        {verificationNeeded && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-semibold">Email not yet verified</p>
            <p className="mt-1 text-xs leading-relaxed">
              Check your inbox for a verification link sent to{' '}
              <span className="font-medium">{verificationEmail}</span>.
            </p>
            {resendMessage && (
              <p className="mt-2 text-xs text-emerald-700">{resendMessage}</p>
            )}
            <button
              type="button"
              onClick={handleResend}
              disabled={resendLoading}
              className="mt-2 text-xs font-semibold text-amber-800 underline hover:text-amber-700 disabled:opacity-60"
            >
              {resendLoading ? 'Sending...' : 'Resend verification email'}
            </button>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-semibold text-slate-400">or</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      <button
        type="button"
        disabled={googleStatus.loading || !googleStatus.available}
        onClick={handleGoogleSignIn}
        className={`flex min-h-12 w-full items-center justify-center gap-2.5 rounded-xl border py-3 text-sm font-semibold transition ${
          googleStatus.loading
            ? 'cursor-wait border-slate-200 bg-slate-50 text-slate-400'
            : googleStatus.available
              ? 'border-slate-300 bg-white text-slate-900 shadow-sm hover:border-cyan-400 hover:bg-cyan-50 hover:shadow-md active:scale-[0.99]'
              : 'cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400'
        }`}
      >
        {!googleStatus.loading && (
          <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        )}
        {googleStatus.loading
          ? 'Checking…'
          : googleStatus.available
            ? 'Continue with Google'
            : 'Continue with Google (not configured)'}
      </button>

      <p className="mt-6 text-center text-sm text-slate-600">
        No account?{' '}
        <button
          onClick={onRegister}
          className="font-bold text-cyan-800 hover:underline focus:outline-none"
        >
          Register
        </button>
      </p>

      <div className="mt-5 flex items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs leading-relaxed text-emerald-900">
        <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
        <span>Monitoring intelligence only. Not legal advice. Official source links included.</span>
      </div>
    </AuthLayout>
  )
}

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
    <div className="sp-page-orbit flex min-h-dvh items-center px-4 py-10 text-slate-200 selection:bg-[#16D9F5]/30">
      <div className="relative z-10 mx-auto grid w-full max-w-6xl items-center gap-8 lg:grid-cols-[0.92fr_0.78fr]">
        <aside className="hidden lg:block">
          <div className="mb-10 flex items-center gap-3">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-10 w-auto" />
            <span className="text-2xl font-extrabold tracking-tight text-white">
              Statute<span className="text-[#16D9F5]">Proof</span>
            </span>
          </div>

          <div className="max-w-xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
              <LockKeyhole className="h-3.5 w-3.5" />
              Evidence workspace access
            </div>
            <h2 className="text-4xl font-semibold leading-tight text-white">
              Sign in to review source evidence before it becomes a brief.
            </h2>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-slate-400">
              The account area separates source monitoring, canonical evidence review, draft brief
              preparation, and delivery approval.
            </p>
          </div>

          <div className="mt-8 max-w-lg rounded-3xl border border-slate-800 bg-slate-950/42 p-5">
            <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <RadioTower className="h-4 w-4 text-cyan-300" />
              Workspace boundary
            </div>
            <div className="grid gap-3">
              {trustRows.map(([label, value]) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-[#07111F]/72 px-4 py-3 text-sm">
                  <span className="text-slate-500">{label}</span>
                  <span className="font-semibold text-slate-100">{value}</span>
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

export default function LoginPage({ onLogin, onRegister }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
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
    setLoading(true)
    try {
      const data = await auth.login({ email, password })
      onLogin(data.user)
    } catch (err) {
      setError(err.message || 'Could not sign in. Check your credentials and try again.')
    } finally {
      setLoading(false)
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
  const labelCls = 'block text-xs font-bold uppercase tracking-wide text-slate-600 mb-1.5'

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
          <label className={labelCls}>Work email</label>
          <input
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
          <div className="flex justify-between gap-3">
            <label className={labelCls}>Password</label>
            <span className="text-xs font-medium text-slate-500" title="Password reset is not enabled yet.">
              Password reset unavailable
            </span>
          </div>
          <div className="relative">
            <input
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

      <div className="relative">
        <button
          type="button"
          disabled={googleStatus.loading || !googleStatus.available}
          onClick={handleGoogleSignIn}
          className={`flex min-h-12 w-full items-center justify-center gap-2 rounded-xl border py-3 text-sm font-semibold transition ${
            googleStatus.available
              ? 'border-slate-300 bg-white text-slate-900 hover:border-cyan-400 hover:bg-cyan-50'
              : 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
          }`}
        >
          <span className="font-bold">G</span>
          {googleStatus.loading ? 'Checking Google sign-in...' : 'Continue with Google'}
        </button>
        {!googleStatus.loading && !googleStatus.available && (
          <span className="absolute -top-2.5 right-3 rounded-md bg-slate-200 px-2 py-0.5 text-[10px] font-bold tracking-wide text-slate-500">
            Not configured
          </span>
        )}
      </div>

      <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-600">
        Use your verified work Google account. StatuteProof uses the verified email to create
        or find your account; no OAuth secret is exposed in the browser.
      </p>

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

import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { auth } from '../../api'

function AuthLayout({ children, quote }) {
  return (
    <div className="min-h-screen bg-[#07111F] flex text-slate-200 font-sans selection:bg-[#16D9F5]/30">
      {/* Left panel */}
      <div className="hidden lg:flex w-5/12 bg-[#0A1628] border-r border-slate-800 p-12 flex-col justify-between relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(#16D9F5 1px, transparent 1px), linear-gradient(90deg, #16D9F5 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        <div className="relative z-10">
          <div className="flex items-center gap-2.5">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-9 w-auto" />
            <span className="text-lg font-extrabold text-white tracking-tight">
              Statute<span className="text-[#16D9F5]">Proof</span>
            </span>
          </div>
        </div>

        <div className="relative z-10 max-w-sm">
          <div className="w-10 h-[3px] bg-[#16D9F5] rounded-full mb-6" />
          <h2 className="text-2xl font-bold text-white mb-6 leading-tight">{quote}</h2>
          <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/35 p-4 text-xs text-slate-400">
            <div className="flex justify-between gap-3">
              <span>Evidence</span>
              <span className="text-slate-200">hash + timestamp</span>
            </div>
            <div className="flex justify-between gap-3">
              <span>Briefs</span>
              <span className="text-slate-200">human-reviewed</span>
            </div>
            <div className="flex justify-between gap-3">
              <span>Scope</span>
              <span className="text-slate-200">UAE official sources</span>
            </div>
          </div>
        </div>
        <div />
      </div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-24 py-12 relative">
        <div className="w-full max-w-md mx-auto">{children}</div>
      </div>
    </div>
  )
}

export default function LoginPage({ onLogin, onRegister }) {
  const [email, setEmail]         = useState('')
  const [password, setPassword]   = useState('')
  const [showPass, setShowPass]   = useState(false)
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)

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

  const inputCls = (hasError) =>
    `w-full rounded-lg border ${hasError ? 'border-red-500/60' : 'border-slate-700'} bg-[#0A1628] px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:border-[#16D9F5] focus:outline-none focus:ring-1 focus:ring-[#16D9F5]/20 transition-colors`

  return (
    <AuthLayout quote="Official-source monitoring with evidence-backed compliance briefs for MLROs and compliance teams.">

      <h1 className="text-2xl font-bold text-white mb-2">Sign in to StatuteProof</h1>
      <p className="text-slate-400 text-sm mb-8">
        Review monitored sources, evidence records, and compliance briefs.
      </p>

      <form className="space-y-5" onSubmit={handleSubmit}>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
            Work Email
          </label>
          <input
            type="email"
            placeholder="name@company.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className={inputCls(false)}
            required
            autoComplete="email"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider">
              Password
            </label>
            <button
              type="button"
              disabled
              title="Password reset is not enabled yet."
              className="cursor-not-allowed text-xs text-slate-600"
            >
              Password reset pending
            </button>
          </div>
          <div className="relative">
            <input
              type={showPass ? 'text' : 'password'}
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className={`${inputCls(false)} pr-10`}
              required
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPass(v => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors focus:outline-none"
              aria-label={showPass ? 'Hide password' : 'Show password'}
            >
              {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {error && (
          <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2.5">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-5 py-2.5 text-sm font-semibold text-[#07111F] hover:bg-[#0EC8E4] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#16D9F5] disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="flex-1 h-px bg-slate-800" />
        <span className="text-xs text-slate-600">or</span>
        <div className="flex-1 h-px bg-slate-800" />
      </div>

      {/* Google OAuth placeholder */}
      <div className="relative">
        <button
          disabled
          className="w-full flex items-center justify-center gap-2 text-sm font-medium text-slate-600 border border-slate-800 py-2.5 rounded-lg cursor-not-allowed select-none"
        >
          <span className="font-bold text-slate-500">G</span>
          Continue with Google
        </button>
        <span className="absolute -top-2.5 right-3 text-[10px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded-sm tracking-wide">
          Coming soon
        </span>
      </div>

      <p className="mt-6 text-center text-sm text-slate-500">
        No account?{' '}
        <button
          onClick={onRegister}
          className="text-[#16D9F5] font-medium hover:underline focus:outline-none"
        >
          Register
        </button>{' '}
        <span className="text-slate-600">→</span>
      </p>

      <p className="mt-4 text-center text-xs text-slate-700 leading-relaxed">
        StatuteProof provides monitoring intelligence only. Not legal advice.
        Official source links included.
      </p>
    </AuthLayout>
  )
}

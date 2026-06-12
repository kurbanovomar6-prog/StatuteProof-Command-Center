import { useState } from 'react'
import { auth } from '../../api'

function AuthLayout({ children, quote }) {
  return (
    <div className="min-h-screen bg-[#07111F] flex text-slate-200 font-sans selection:bg-[#16D9F5]/30">
      <div className="hidden lg:flex w-5/12 bg-[#0A1628] border-r border-slate-800 p-12 flex-col justify-between relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{ backgroundImage: 'linear-gradient(#16D9F5 1px, transparent 1px), linear-gradient(90deg, #16D9F5 1px, transparent 1px)', backgroundSize: '40px 40px' }}
        />
        <div className="relative z-10">
          <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-10 w-auto" />
        </div>
        <div className="relative z-10 max-w-sm">
          <h2 className="text-3xl font-bold text-white mb-6 leading-tight">{quote}</h2>
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-[#16D9F5]" />
              <div className="w-1.5 h-1.5 rounded-full bg-[#16D9F5]" />
              <div className="w-1.5 h-1.5 rounded-full bg-[#16D9F5]" />
            </div>
            Enterprise B2B RegTech
          </div>
        </div>
        <div />
      </div>
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-24 py-12 relative">
        <div className="w-full max-w-md mx-auto">{children}</div>
      </div>
    </div>
  )
}

export default function LoginPage({ onLogin, onRegister }) {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await auth.login({ email, password })
      onLogin(data.user)
    } catch (err) {
      setError(err.message || 'Could not sign in.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout quote="Official-source monitoring with evidence-backed compliance briefs for MLROs and compliance teams.">
      <h1 className="text-2xl font-bold text-white mb-2">Sign in to your StatuteProof workspace</h1>
      <p className="text-slate-400 text-sm mb-8">
        Review monitored sources, evidence records, alerts, and weekly briefs.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
            Work Email
          </label>
          <input
            type="email"
            placeholder="name@company.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all"
            required
          />
        </div>
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wide">Password</label>
            <button type="button" className="text-xs text-[#16D9F5] hover:underline">Forgot?</button>
          </div>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold py-2.5 rounded-lg transition-colors mt-2"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      {error && (
        <div className="mt-4 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <div className="my-5 flex items-center gap-3">
        <div className="flex-1 h-px bg-slate-800" />
        <span className="text-xs text-slate-600">or</span>
        <div className="flex-1 h-px bg-slate-800" />
      </div>

      {/* Google OAuth — placeholder, not functional */}
      <div className="relative">
        <button
          disabled
          className="w-full flex items-center justify-center gap-2 text-sm font-medium text-slate-600 border border-slate-800 py-2.5 rounded-lg cursor-not-allowed select-none"
        >
          <span className="font-bold">G</span> Continue with Google
        </button>
        <span className="absolute -top-2.5 right-3 text-[10px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded-sm tracking-wide">
          Coming soon
        </span>
      </div>

      <p className="mt-5 text-center text-xs text-slate-600 leading-relaxed">
        StatuteProof supports compliance review and does not provide legal advice.
      </p>

      <div className="mt-5 text-center text-sm text-slate-400">
        No account yet?{' '}
        <button onClick={onRegister} className="text-[#16D9F5] font-medium hover:underline">
          Create workspace
        </button>
      </div>

      <p className="mt-3 text-center text-xs text-slate-600">No legal advice. Official source links included.</p>
    </AuthLayout>
  )
}

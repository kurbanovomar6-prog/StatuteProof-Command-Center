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

const INDUSTRIES = [
  'Fintech', 'Payments', 'Crypto / VASP', 'Banking',
  'Legal & Compliance', 'Tax / Reporting', 'Consulting', 'Other',
]

export default function RegisterPage({ onRegister, onLogin }) {
  const [form, setForm] = useState({ name: '', email: '', company: '', industry: 'Fintech', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await auth.register({
        full_name: form.name,
        email: form.email,
        password: form.password,
        company_name: form.company,
        industry: form.industry,
      })
      onRegister(data.user)
    } catch (err) {
      setError(err.message || 'Could not create workspace.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout quote="Built for UAE-first compliance teams that need source proof, validation status, and limitation notes.">
      <h1 className="text-2xl font-bold text-white mb-2">Create your StatuteProof pilot workspace</h1>
      <p className="text-slate-400 text-sm mb-8">
        Set up a secure account for your UAE source readiness profile.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
            Full name
          </label>
          <input
            type="text"
            placeholder="Your name"
            value={form.name}
            onChange={set('name')}
            className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
            Work Email
          </label>
          <input
            type="email"
            placeholder="name@company.com"
            value={form.email}
            onChange={set('email')}
            className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all"
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
              Company
            </label>
            <input
              type="text"
              placeholder="Company name"
              value={form.company}
              onChange={set('company')}
              className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
              Industry
            </label>
            <select
              value={form.industry}
              onChange={set('industry')}
              className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#16D9F5]/50 transition-all"
            >
              {INDUSTRIES.map(i => <option key={i}>{i}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
            Password
          </label>
          <input
            type="password"
            placeholder="Min. 8 characters"
            value={form.password}
            onChange={set('password')}
            className="w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all"
            required
            minLength={8}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold py-2.5 rounded-lg transition-colors mt-2"
        >
          {loading ? 'Creating workspace…' : 'Create workspace →'}
        </button>
      </form>

      {error && (
        <div className="mt-4 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <p className="mt-5 text-xs text-slate-600 text-center leading-relaxed">
        Founding pilot workspace. Your profile, source readiness status and Telegram connection are saved to your account.
        No legal advice. Official source links included.
      </p>
      <div className="mt-4 text-center text-sm text-slate-400 border-t border-slate-800 pt-4">
        Already have an account?{' '}
        <button onClick={onLogin} className="text-[#16D9F5] font-medium hover:underline">
          Sign in
        </button>
      </div>
    </AuthLayout>
  )
}

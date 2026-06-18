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
              <span>Readiness</span>
              <span className="text-slate-200">146 monitoring-active</span>
            </div>
            <div className="flex justify-between gap-3">
              <span>Activation</span>
              <span className="text-slate-200">manual after review</span>
            </div>
            <div className="flex justify-between gap-3">
              <span>Boundary</span>
              <span className="text-slate-200">not legal advice</span>
            </div>
          </div>
        </div>
        <div />
      </div>

      {/* Right panel — scrollable */}
      <div className="flex-1 flex flex-col justify-start px-8 sm:px-16 lg:px-20 py-10 overflow-y-auto">
        <div className="w-full max-w-md mx-auto">{children}</div>
      </div>
    </div>
  )
}

const JOB_TITLES = [
  'MLRO',
  'CCO',
  'Head of Compliance',
  'Compliance Manager',
  'Legal Counsel',
  'Founder',
  'Other',
]

const COMPANY_TYPES = [
  'VARA-licensed VASP',
  'UAE fintech',
  'DFSA-authorised firm',
  'ADGM FSRA-regulated firm',
  'Compliance consultancy',
  'Law firm',
  'Other',
]

const JURISDICTIONS = [
  'Dubai / VARA',
  'DIFC / DFSA',
  'ADGM / FSRA',
  'UAE Federal',
  'Multiple',
]

export default function RegisterPage({ onRegister, onLogin }) {
  const [form, setForm] = useState({
    firstName:    '',
    lastName:     '',
    email:        '',
    password:     '',
    company:      '',
    jobTitle:     'MLRO',
    companyType:  'VARA-licensed VASP',
    jurisdiction: 'Dubai / VARA',
  })
  const [showPass, setShowPass]                           = useState(false)
  const [termsAccepted, setTermsAccepted]                 = useState(false)
  const [privacyAccepted, setPrivacyAccepted]             = useState(false)
  const [disclaimerAcknowledged, setDisclaimerAcknowledged] = useState(false)
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!termsAccepted || !privacyAccepted || !disclaimerAcknowledged) {
      setError('Please accept the terms, privacy policy, and legal disclaimer to continue.')
      return
    }
    if (!form.firstName.trim()) {
      setError('First name is required.')
      return
    }

    setLoading(true)
    try {
      const data = await auth.register({
        full_name:    `${form.firstName.trim()} ${form.lastName.trim()}`.trim(),
        email:        form.email,
        password:     form.password,
        company_name: form.company,
        industry:     form.companyType,
        job_title:    form.jobTitle,
        company_type: form.companyType,
        jurisdiction: form.jurisdiction,
      })
      onRegister(data.user)
    } catch (err) {
      setError(err.message || 'Could not create workspace.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full rounded-lg border border-slate-700 bg-[#0A1628] px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:border-[#16D9F5] focus:outline-none focus:ring-1 focus:ring-[#16D9F5]/20 transition-colors'
  const selectCls = 'w-full rounded-lg border border-slate-700 bg-[#0A1628] px-4 py-2.5 text-sm text-slate-200 focus:border-[#16D9F5] focus:outline-none focus:ring-1 focus:ring-[#16D9F5]/20 transition-colors appearance-none'
  const labelCls = 'block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider'

  return (
    <AuthLayout quote="Official-source monitoring with evidence-backed compliance briefs for UAE financial teams.">

      <h1 className="text-2xl font-bold text-white mb-1">Create your StatuteProof workspace</h1>
      <p className="text-slate-400 text-sm mb-7">
        Access monitored sources, evidence records, and human-reviewed compliance briefs.
      </p>

      <form className="space-y-4" onSubmit={handleSubmit}>

        {/* Name row */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelCls}>First name *</label>
            <input
              type="text"
              placeholder="First"
              value={form.firstName}
              onChange={set('firstName')}
              className={inputCls}
              required
            />
          </div>
          <div>
            <label className={labelCls}>Last name</label>
            <input
              type="text"
              placeholder="Last"
              value={form.lastName}
              onChange={set('lastName')}
              className={inputCls}
            />
          </div>
        </div>

        {/* Work email */}
        <div>
          <label className={labelCls}>Work Email *</label>
          <input
            type="email"
            placeholder="name@company.com"
            value={form.email}
            onChange={set('email')}
            className={inputCls}
            required
            autoComplete="email"
          />
        </div>

        {/* Password */}
        <div>
          <label className={labelCls}>Password *</label>
          <div className="relative">
            <input
              type={showPass ? 'text' : 'password'}
              placeholder="Min. 8 characters"
              value={form.password}
              onChange={set('password')}
              className={`${inputCls} pr-10`}
              required
              minLength={8}
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

        {/* Company */}
        <div>
          <label className={labelCls}>Company name *</label>
          <input
            type="text"
            placeholder="Your organisation"
            value={form.company}
            onChange={set('company')}
            className={inputCls}
            required
          />
        </div>

        {/* Job title */}
        <div>
          <label className={labelCls}>Job title</label>
          <select value={form.jobTitle} onChange={set('jobTitle')} className={selectCls}>
            {JOB_TITLES.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        {/* Company type */}
        <div>
          <label className={labelCls}>Company type</label>
          <select value={form.companyType} onChange={set('companyType')} className={selectCls}>
            {COMPANY_TYPES.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        {/* Primary jurisdiction */}
        <div>
          <label className={labelCls}>Primary jurisdiction</label>
          <select value={form.jurisdiction} onChange={set('jurisdiction')} className={selectCls}>
            {JURISDICTIONS.map(j => <option key={j}>{j}</option>)}
          </select>
        </div>

        {/* Checkboxes */}
        <div className="space-y-3 pt-2">
          {[
            {
              id: 'terms',
              checked: termsAccepted,
              onChange: e => setTermsAccepted(e.target.checked),
              text: 'I agree to the StatuteProof Terms of Service.',
            },
            {
              id: 'privacy',
              checked: privacyAccepted,
              onChange: e => setPrivacyAccepted(e.target.checked),
              text: 'I agree to the StatuteProof Privacy Policy.',
            },
            {
              id: 'disclaimer',
              checked: disclaimerAcknowledged,
              onChange: e => setDisclaimerAcknowledged(e.target.checked),
              text: 'I understand StatuteProof provides monitoring intelligence and evidence-backed summaries only. It does not provide legal advice or determine compliance outcomes.',
            },
          ].map(({ id, checked, onChange, text }) => (
            <label key={id} className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={checked}
                onChange={onChange}
                className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-[#0A1628] text-[#16D9F5] focus:ring-[#16D9F5]/30 flex-shrink-0 accent-[#16D9F5]"
              />
              <span className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                {text}
              </span>
            </label>
          ))}
        </div>

        {error && (
          <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2.5">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-5 py-2.5 text-sm font-semibold text-[#07111F] hover:bg-[#0EC8E4] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#16D9F5] disabled:opacity-60 disabled:cursor-not-allowed mt-1"
        >
          {loading ? 'Creating workspace...' : 'Create workspace'}
        </button>
      </form>

      <p className="mt-5 text-xs text-slate-600 text-center leading-relaxed">
        StatuteProof provides monitoring intelligence only. Not legal advice.
        Official source links included.
      </p>

      <div className="mt-5 text-center text-sm text-slate-500 border-t border-slate-800 pt-5">
        Already have an account?{' '}
        <button
          onClick={onLogin}
          className="text-[#16D9F5] font-medium hover:underline focus:outline-none"
        >
          Sign in
        </button>{' '}
        <span className="text-slate-600">→</span>
      </div>
    </AuthLayout>
  )
}

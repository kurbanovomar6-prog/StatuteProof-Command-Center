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
            UAE-first regulatory monitoring intelligence
          </div>
        </div>
        <div />
      </div>
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-20 py-10 relative overflow-y-auto">
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
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    company: '',
    jobTitle: 'MLRO',
    companyType: 'VARA-licensed VASP',
    jurisdiction: 'Dubai / VARA',
  })
  const [termsAccepted, setTermsAccepted]     = useState(false)
  const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [disclaimerAcknowledged, setDisclaimerAcknowledged] = useState(false)
  const [error, setError]     = useState('')
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
        // industry maps to job title context for backend compatibility
        industry:     form.companyType,
      })
      onRegister(data.user)
    } catch (err) {
      setError(err.message || 'Could not create workspace.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all text-sm'
  const selectCls = 'w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all text-sm'
  const labelCls = 'block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide'

  return (
    <AuthLayout quote="Official-source monitoring with evidence-backed compliance briefs for UAE financial teams.">
      <h1 className="text-2xl font-bold text-white mb-1">Create your StatuteProof workspace</h1>
      <p className="text-slate-400 text-sm mb-6">
        Review monitored sources, evidence records, alerts, and weekly briefs.
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
          />
        </div>

        {/* Password */}
        <div>
          <label className={labelCls}>Password *</label>
          <input
            type="password"
            placeholder="Min. 8 characters"
            value={form.password}
            onChange={set('password')}
            className={inputCls}
            required
            minLength={8}
          />
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

        {/* Jurisdiction */}
        <div>
          <label className={labelCls}>Primary jurisdiction</label>
          <select value={form.jurisdiction} onChange={set('jurisdiction')} className={selectCls}>
            {JURISDICTIONS.map(j => <option key={j}>{j}</option>)}
          </select>
        </div>

        {/* Checkboxes */}
        <div className="space-y-3 pt-1">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={e => setTermsAccepted(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-[#0A1628] text-[#16D9F5] focus:ring-[#16D9F5]/30 flex-shrink-0"
            />
            <span className="text-xs text-slate-400 leading-relaxed">
              I agree to the StatuteProof Terms of Service.
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={privacyAccepted}
              onChange={e => setPrivacyAccepted(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-[#0A1628] text-[#16D9F5] focus:ring-[#16D9F5]/30 flex-shrink-0"
            />
            <span className="text-xs text-slate-400 leading-relaxed">
              I agree to the StatuteProof Privacy Policy.
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={disclaimerAcknowledged}
              onChange={e => setDisclaimerAcknowledged(e.target.checked)}
              className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-[#0A1628] text-[#16D9F5] focus:ring-[#16D9F5]/30 flex-shrink-0"
            />
            <span className="text-xs text-slate-400 leading-relaxed">
              I understand StatuteProof provides monitoring intelligence and evidence-backed summaries only.
              It does not provide legal advice or guarantee compliance.
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold py-2.5 rounded-lg transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Creating workspace…' : 'Create workspace'}
        </button>
      </form>

      {error && (
        <div className="mt-4 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      <p className="mt-5 text-xs text-slate-600 text-center leading-relaxed">
        StatuteProof supports compliance review and does not provide legal advice.
        Official source links included.
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

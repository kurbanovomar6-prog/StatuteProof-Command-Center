/**
 * SourceReadinessReviewPage — public page for requesting a source readiness review.
 *
 * Wired to POST /api/contact (the existing backend contact endpoint).
 * Does not silently fake submission — shows clear success/error states.
 *
 * Disclaimer: Not legal advice and does not determine regulatory obligations.
 */
import { useState } from 'react'
import { Shield, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react'

const REGULATORS = [
  'CBUAE',
  'VARA',
  'DFSA',
  'ADGM / FSRA',
  'UAE FIU',
  'DIFC',
  'UAE Legislation Portal',
  'UAE Ministry of Finance',
  'UAE Ministry of Economy',
  'Other',
]

const JOB_TITLES = [
  'MLRO', 'CCO', 'Head of Compliance', 'Compliance Manager',
  'Legal Counsel', 'Founder', 'Other',
]

const COMPANY_TYPES = [
  'VARA-licensed VASP', 'UAE fintech', 'DFSA-authorised firm',
  'ADGM FSRA-regulated firm', 'Compliance consultancy', 'Law firm', 'Other',
]

export default function SourceReadinessReviewPage({ onBack }) {
  const [form, setForm] = useState({
    email:          '',
    company:        '',
    jobTitle:       'MLRO',
    companyType:    'VARA-licensed VASP',
    regulators:     [],
    currentProcess: '',
    notes:          '',
  })
  const [status, setStatus]   = useState('idle') // idle | loading | success | error
  const [errorMsg, setErrorMsg] = useState('')

  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  function toggleRegulator(reg) {
    setForm(f => ({
      ...f,
      regulators: f.regulators.includes(reg)
        ? f.regulators.filter(r => r !== reg)
        : [...f.regulators, reg],
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErrorMsg('')
    if (!form.email.trim() || !form.company.trim()) {
      setErrorMsg('Work email and company name are required.')
      return
    }
    setStatus('loading')
    try {
      const res = await fetch('/api/contact', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name:     form.company,
          email:    form.email,
          company:  form.company,
          industry: form.companyType,
          message:  [
            `Job title: ${form.jobTitle}`,
            `Company type: ${form.companyType}`,
            `Regulators monitored: ${form.regulators.join(', ') || 'Not specified'}`,
            `Current monitoring process: ${form.currentProcess || 'Not specified'}`,
            `Additional notes: ${form.notes || 'None'}`,
            'Request type: Source Readiness Review',
          ].join('\n'),
          markets: form.regulators.join(', '),
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok && (data.ok || data.queued)) {
        setStatus('success')
      } else {
        setErrorMsg(data.message || 'Submission failed. Please try again.')
        setStatus('error')
      }
    } catch {
      setErrorMsg('Could not reach the server. Please try again later.')
      setStatus('error')
    }
  }

  const inputCls = 'w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all text-sm'
  const selectCls = 'w-full bg-[#0A1628] border border-slate-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#16D9F5]/50 focus:ring-1 focus:ring-[#16D9F5]/50 transition-all text-sm'
  const labelCls = 'block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide'

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-[#07111F] flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-3">Request received</h2>
          <p className="text-slate-400 mb-6 leading-relaxed">
            Your source readiness review request has been submitted. We will review your profile
            and source requirements and be in touch.
          </p>
          <p className="text-xs text-slate-600 mb-6 leading-relaxed">
            This is not legal advice and does not determine regulatory obligations.
          </p>
          <button
            onClick={onBack}
            className="inline-flex items-center gap-2 text-sm font-medium text-[#16D9F5] hover:underline"
          >
            <ArrowLeft className="w-4 h-4" /> Back to homepage
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#07111F] text-slate-200">

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#07111F]/90 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="flex items-center gap-2">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-8 w-auto" />
            <span className="text-base font-bold text-white">
              Statute<span className="text-[#16D9F5]">Proof</span>
            </span>
          </div>
          <div className="w-20" />
        </div>
      </header>

      <main className="pt-28 pb-20 px-4">
        <div className="max-w-2xl mx-auto">

          {/* Title */}
          <div className="text-center mb-10">
            <div className="sp-kicker mb-5">
              <Shield className="w-3.5 h-3.5" />
              Free Source Readiness Review
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">
              Request a source readiness review
            </h1>
            <p className="text-slate-400 leading-relaxed max-w-xl mx-auto">
              Tell us which UAE regulators your team monitors and how you currently track changes.
              We will review your source requirements and share a source readiness report.
            </p>
            <p className="text-xs text-slate-600 mt-3">
              This is not legal advice and does not determine regulatory obligations.
            </p>
            <div className="mx-auto mt-6 grid max-w-lg grid-cols-3 gap-2 text-center">
              {[
                ['226', 'UAE sources enabled'],
                ['225', 'monitoring-active'],
                ['7', 'licence profiles covered'],
              ].map(([value, label]) => (
                <div key={label} className="sp-panel-muted px-3 py-2">
                  <p className="sp-mono text-xl font-semibold text-white">{value}</p>
                  <p className="text-[11px] text-slate-500">{label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Form card */}
          <div className="sp-panel p-7 sm:p-10">
            <form className="space-y-5" onSubmit={handleSubmit}>

              {/* Email */}
              <div>
                <label className={labelCls}>Work email *</label>
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={form.email}
                  onChange={set('email')}
                  className={inputCls}
                  required
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

              {/* Regulators checkboxes */}
              <div>
                <label className={labelCls}>Regulators currently monitored (select all that apply)</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {REGULATORS.map(reg => (
                    <button
                      key={reg}
                      type="button"
                      onClick={() => toggleRegulator(reg)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        form.regulators.includes(reg)
                          ? 'bg-[#16D9F5]/10 border-[#16D9F5]/50 text-[#16D9F5]'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'
                      }`}
                    >
                      {reg}
                    </button>
                  ))}
                </div>
              </div>

              {/* Current monitoring process */}
              <div>
                <label className={labelCls}>Current monitoring process</label>
                <textarea
                  rows={3}
                  placeholder="How does your team currently track regulatory changes? (e.g. manual website checks, email alerts, subscription service)"
                  value={form.currentProcess}
                  onChange={set('currentProcess')}
                  className={`${inputCls} resize-none`}
                />
              </div>

              {/* Notes */}
              <div>
                <label className={labelCls}>Additional notes (optional)</label>
                <textarea
                  rows={2}
                  placeholder="Any specific source requirements or context for your review request"
                  value={form.notes}
                  onChange={set('notes')}
                  className={`${inputCls} resize-none`}
                />
              </div>

              {/* Error */}
              {(status === 'error' && errorMsg) && (
                <div className="flex items-start gap-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2.5">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  {errorMsg}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === 'loading' ? 'Submitting…' : 'Request source readiness review'}
              </button>

              {/* Disclaimer */}
              <p className="text-xs text-slate-600 text-center leading-relaxed">
                This is not legal advice and does not determine regulatory obligations.
                StatuteProof provides monitoring intelligence only and does not provide legal advice or
                determine compliance outcomes.
              </p>
            </form>
          </div>

          {/* What to expect */}
          <div className="mt-8 grid sm:grid-cols-3 gap-4">
            {[
              { title: 'Source map', body: 'We identify which official UAE sources are monitoring-active, on the roadmap, or have access restrictions — for your specific licence profile.' },
              { title: 'Honest about limits', body: 'We disclose sources that have access restrictions, geo-blocking, or extraction issues.' },
              { title: 'Not legal advice', body: 'This is monitoring intelligence only. Consult qualified professionals for legal and compliance decisions.' },
            ].map(item => (
              <div key={item.title} className="sp-panel p-4">
                <h3 className="text-sm font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}

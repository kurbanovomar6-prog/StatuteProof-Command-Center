/**
 * SourceReadinessReviewPage — public page for requesting a source readiness review.
 *
 * Wired to POST /api/contact (the existing backend contact endpoint).
 * Does not silently fake submission — shows clear success/error states.
 *
 * Disclaimer: Not legal advice and does not determine regulatory obligations.
 */
import { useState } from 'react'
import { Shield, CheckCircle, AlertTriangle, ArrowLeft, ClipboardCheck, FileSearch, Map, Send } from 'lucide-react'
import { SOURCE_QUALITY_SUMMARY } from '../data/sourceQualityAudit'

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

function formatSourceTruthDate(dateValue) {
  const [year, month, day] = String(dateValue).split('-')
  const monthNames = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
  }
  return `${Number(day)} ${monthNames[month] || month} ${year}`
}

const sourceTruthAsOf = formatSourceTruthDate(SOURCE_QUALITY_SUMMARY.auditDate)
const limitationsDisclosed = SOURCE_QUALITY_SUMMARY.candidate + SOURCE_QUALITY_SUMMARY.remediation

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

  const inputCls = 'min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 placeholder:text-slate-400 shadow-sm transition-all focus:border-cyan-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/10'
  const selectCls = 'min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 shadow-sm transition-all focus:border-cyan-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/10'
  const labelCls = 'mb-1.5 block text-xs font-bold uppercase tracking-wide text-slate-600'

  if (status === 'success') {
    return (
      <div className="sp-page-orbit flex min-h-dvh items-center justify-center px-4">
        <div className="sp-paper-panel w-full max-w-md p-8 text-center">
          <CheckCircle className="mx-auto mb-4 h-16 w-16 text-emerald-600" />
          <h2 className="mb-3 text-2xl font-semibold text-slate-950">Request received</h2>
          <p className="mb-6 leading-relaxed text-slate-600">
            Your source readiness review request has been submitted. We will review your profile
            and source requirements and be in touch.
          </p>
          <p className="mb-6 text-xs leading-relaxed text-slate-500">
            This is not legal advice and does not determine regulatory obligations.
          </p>
          <button
            onClick={onBack}
            className="inline-flex items-center gap-2 text-sm font-bold text-cyan-800 hover:underline"
          >
            <ArrowLeft className="h-4 w-4" /> Back to homepage
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="sp-page-orbit min-h-dvh text-slate-200">

      {/* Header */}
      <header className="fixed left-0 right-0 top-0 z-50 border-b border-slate-800/80 bg-[#06101D]/92 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <button
            onClick={onBack}
            className="flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm text-slate-400 transition-colors hover:bg-slate-800/60 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
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

      <main className="relative z-10 px-4 pb-20 pt-28">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
                <Shield className="h-3.5 w-3.5" />
                Free source readiness review
              </div>
              <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-white md:text-5xl">
                Bring your UAE source list. We return a monitored-source truth map.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-relaxed text-slate-400">
                We check whether each requested official source is public, technically accessible,
                fresh-alert eligible, evidence-library only, blocked, or still requiring remediation.
              </p>
              <p className="mt-3 text-xs text-slate-500">
                Monitoring intelligence only. This is not legal advice and does not determine regulatory obligations.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              {[
                [SOURCE_QUALITY_SUMMARY.totalEnabled, 'enabled UAE records', 'registry truth'],
                [SOURCE_QUALITY_SUMMARY.freshAlertEligible, 'fresh-alert eligible', 'selected sources'],
                [SOURCE_QUALITY_SUMMARY.evidenceLibraryOnly, 'evidence-library', 'not alert volume'],
                [limitationsDisclosed, 'limitations disclosed', 'candidate + remediation'],
              ].map(([value, label, note]) => (
                <div key={label} className="rounded-3xl border border-slate-800 bg-slate-950/45 p-4">
                  <p className="sp-mono text-3xl font-bold text-white">{value}</p>
                  <p className="mt-1 text-sm font-semibold text-slate-200">{label}</p>
                  <p className="mt-1 text-xs text-slate-500">{note}</p>
                </div>
              ))}
              <p className="text-xs text-slate-500 sm:col-span-4">
                Source registry snapshot as of {sourceTruthAsOf}. Counts are transparency data, not a coverage promise.
              </p>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[0.72fr_1fr]">
            <aside className="space-y-4">
              <div className="sp-paper-panel p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Map className="h-5 w-5 text-cyan-800" />
                  <h2 className="text-lg font-semibold text-slate-950">What you get back</h2>
                </div>
                <div className="space-y-3">
                  {[
                    ['Source map', 'Fresh-alert eligible, evidence-library, candidate, and remediation rows.'],
                    ['Blocker notes', 'Access restrictions, static pages, nav shells, and parser limitations.'],
                    ['Pilot fit', 'Which official sources can safely support your first monitored scope.'],
                  ].map(([title, body]) => (
                    <div key={title} className="rounded-2xl border border-slate-200 bg-white/72 p-4">
                      <p className="font-semibold text-slate-950">{title}</p>
                      <p className="mt-1 text-sm leading-relaxed text-slate-600">{body}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-3xl border border-amber-400/25 bg-amber-400/10 p-5">
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-300" />
                  <h2 className="text-sm font-semibold text-white">Important boundary</h2>
                </div>
                <p className="text-sm leading-relaxed text-amber-50/80">
                  Selecting a regulator tells us what your team checks today. It does not mean
                  StatuteProof claims a full regulator-wide source map.
                </p>
              </div>
            </aside>

            <div className="sp-paper-panel p-5 sm:p-7">
              <div className="mb-6 flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-900">
                    <ClipboardCheck className="h-3.5 w-3.5" />
                    Intake form
                  </div>
                  <h2 className="text-2xl font-semibold text-slate-950">Request source readiness review</h2>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">
                    Four sections: identity, licence profile, source areas, and current process.
                  </p>
                </div>
                <FileSearch className="hidden h-9 w-9 text-cyan-800 sm:block" />
              </div>

              <form className="space-y-6" onSubmit={handleSubmit}>
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <span className="sp-mono flex h-7 w-7 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">1</span>
                  <h3 className="text-sm font-bold text-slate-950">Who should receive the review?</h3>
                </div>

              {/* Email */}
              <div className="grid gap-4 sm:grid-cols-2">
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
              </div>
              </section>

              <section>
                <div className="mb-3 flex items-center gap-2">
                  <span className="sp-mono flex h-7 w-7 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">2</span>
                  <h3 className="text-sm font-bold text-slate-950">What profile should we map?</h3>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className={labelCls}>Job title</label>
                    <select value={form.jobTitle} onChange={set('jobTitle')} className={selectCls}>
                      {JOB_TITLES.map(t => <option key={t}>{t}</option>)}
                    </select>
                    <p className="mt-1 text-xs leading-relaxed text-slate-500">
                      MLRO = Money Laundering Reporting Officer. CCO = Chief Compliance Officer.
                    </p>
                  </div>

                  <div>
                    <label className={labelCls}>Company type</label>
                    <select value={form.companyType} onChange={set('companyType')} className={selectCls}>
                      {COMPANY_TYPES.map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                </div>
              </section>

              {/* Regulators checkboxes */}
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <span className="sp-mono flex h-7 w-7 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">3</span>
                  <h3 className="text-sm font-bold text-slate-950">Which official-source areas matter?</h3>
                </div>
                <p className="mb-3 text-xs leading-relaxed text-slate-500">
                  Select the areas your team checks today. We will return readiness status, not a full regulator map.
                </p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {REGULATORS.map(reg => (
                    <button
                      key={reg}
                      type="button"
                      onClick={() => toggleRegulator(reg)}
                      className={`min-h-10 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
                        form.regulators.includes(reg)
                          ? 'border-cyan-500 bg-cyan-50 text-cyan-900'
                          : 'border-slate-300 bg-white text-slate-600 hover:border-slate-500 hover:text-slate-950'
                      }`}
                    >
                      {reg}
                    </button>
                  ))}
                </div>
              </section>

              {/* Current monitoring process */}
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <span className="sp-mono flex h-7 w-7 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">4</span>
                  <h3 className="text-sm font-bold text-slate-950">How do you monitor today?</h3>
                </div>
                <div className="grid gap-4">
                  <div>
                    <label className={labelCls}>Current monitoring process</label>
                    <textarea
                      rows={3}
                      placeholder="Manual website checks, email alerts, regulator mailing lists, spreadsheet tracker..."
                      value={form.currentProcess}
                      onChange={set('currentProcess')}
                      className={`${inputCls} resize-none`}
                    />
                  </div>

                  <div>
                    <label className={labelCls}>Additional notes (optional)</label>
                    <textarea
                      rows={2}
                      placeholder="Specific sources, regulator families, or known gaps you want checked"
                      value={form.notes}
                      onChange={set('notes')}
                      className={`${inputCls} resize-none`}
                    />
                  </div>
                </div>
              </section>

              {/* Error */}
              {(status === 'error' && errorMsg) && (
                <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs text-rose-800">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
                  {errorMsg}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={status === 'loading'}
                className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 py-3 font-bold text-white shadow-lg shadow-slate-900/20 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {status === 'loading' ? 'Submitting…' : 'Request source readiness review'}
                <Send className="h-4 w-4" />
              </button>

              {/* Disclaimer */}
              <p className="text-center text-xs leading-relaxed text-slate-500">
                This is not legal advice and does not determine regulatory obligations.
                StatuteProof provides monitoring intelligence only and does not provide legal advice or
                determine compliance outcomes.
              </p>
            </form>
          </div>
        </div>
        </div>
      </main>
    </div>
  )
}

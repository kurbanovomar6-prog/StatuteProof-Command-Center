import { useState, useRef } from 'react'
import { ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react'
import { profile as profileApi } from '../../api'

const MARKETS = ['UAE', 'DIFC', 'ADGM', 'Other UAE source']
const INDUSTRIES = ['Fintech', 'Payments', 'Crypto / VASP', 'Banking', 'Legal & Compliance', 'Tax / Reporting', 'Consulting', 'Other']
const SOURCE_LAYERS = [
  'CBUAE',
  'VARA',
  'DFSA',
  'ADGM / FSRA',
  'UAE FIU',
  'Ministry of Finance',
  'UAE Legislation Portal',
  'DIFC Laws',
  'Ministry of Economy',
  'FTA',
  'Capital Market Authority / former SCA [Limited]',
  'Other',
]

function toggle(list, setList, item) {
  setList(list.includes(item) ? list.filter(i => i !== item) : [...list, item])
}

function loadSavedProfile() {
  try {
    return JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
  } catch {
    return {}
  }
}

export default function OnboardingPage({ navigate, currentUser }) {
  const saved = loadSavedProfile()

  const [step, setStep]         = useState(1)
  const [company, setCompany]   = useState(saved.company || '')
  const [email, setEmail]       = useState(saved.email || currentUser?.email || '')
  const [markets, setMarkets]   = useState(Array.isArray(saved.markets) ? saved.markets : [])
  const [industries, setIndustries] = useState(Array.isArray(saved.industries) ? saved.industries : saved.industry ? [saved.industry] : [])
  const [sourceLayers, setSourceLayers] = useState(Array.isArray(saved.topics) ? saved.topics : [])
  const [errors, setErrors]     = useState({})
  const [saving, setSaving]     = useState(false)
  const [submitError, setSubmitError] = useState('')

  const companyRef  = useRef(null)
  const emailRef    = useRef(null)
  const marketsRef  = useRef(null)
  const sourcesRef  = useRef(null)
  const industRef   = useRef(null)

  function validateStep(s) {
    const errs = {}
    if (s === 1) {
      if (!company.trim()) errs.company = 'Company name is required.'
      if (!email.trim())   errs.email   = 'Work email is required.'
    }
    if (s === 2) {
      if (markets.length === 0) errs.markets = 'Select at least one UAE market or free zone.'
      if (sourceLayers.length === 0) errs.sourceLayers = 'Select at least one UAE source layer.'
    }
    if (s === 3 && industries.length === 0) errs.industries = 'Select at least one industry.'
    return errs
  }

  function goNext() {
    const errs = validateStep(step)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      if (errs.company) { companyRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }); companyRef.current?.focus() }
      else if (errs.email) { emailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }); emailRef.current?.focus() }
      else if (errs.markets) { marketsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
      else if (errs.sourceLayers) { sourcesRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
      else if (errs.industries) { industRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
      return
    }
    setErrors({})
    setStep(s => s + 1)
  }

  async function handleComplete() {
    const errs = validateStep(step)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }
    setSaving(true)
    setSubmitError('')
    try {
      const data = await profileApi.update({
        company_name: company,
        industries,
        markets,
        topics: sourceLayers,
        onboarding_completed: true,
      })
      const p = data.profile
      localStorage.setItem('regradar_workspace_profile', JSON.stringify({
        company: p.company_name || '',
        email: '',
        industry: p.industries?.[0] || '',
        industries: p.industries || [],
        markets: p.markets || [],
        topics: p.topics || [],
        customSources: p.custom_sources || [],
        alertThreshold: p.alert_threshold || 'MEDIUM',
        briefLanguage: p.brief_language || 'en',
        weeklyBriefEnabled: Boolean(p.weekly_brief_enabled),
        aiEnabled: Boolean(p.ai_enabled),
        telegramAlertsEnabled: Boolean(p.telegram_alerts_enabled),
        emailAlertsEnabled: Boolean(p.email_alerts_enabled),
      }))
      localStorage.setItem('regradar_onboarding_complete', 'true')
      navigate()
    } catch (err) {
      setSubmitError(err.message || 'Could not save monitoring profile.')
    } finally {
      setSaving(false)
    }
  }

  const totalSteps = 4

  return (
    <div className="min-h-screen bg-[#07111F] flex flex-col items-center justify-center p-6 text-slate-200 font-sans selection:bg-[#16D9F5]/30">
      <div className="w-full max-w-2xl">

        {/* Logo */}
        <div className="mb-10 text-center">
          <div className="inline-flex mb-8">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-10 w-auto" />
          </div>
          <h1 className="text-3xl font-bold text-white mt-2 mb-2">Set up your monitoring profile</h1>
          <p className="text-slate-400">Step {step} of {totalSteps}</p>
        </div>

        {/* Card */}
        <div className="bg-[#0A1628] border border-slate-800 rounded-2xl p-8 md:p-12 shadow-2xl relative overflow-hidden">

          {/* Progress bar */}
          <div className="absolute top-0 left-0 w-full h-1 bg-slate-800">
            <div
              className="h-full bg-[#16D9F5] transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>

          {/* Step 1: Profile info */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-white mb-6">Your workspace profile</h2>

              <div ref={companyRef}>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
                  Company name *
                </label>
                <input
                  type="text"
                  placeholder="Your company"
                  value={company}
                  onChange={e => { setCompany(e.target.value); setErrors(er => ({ ...er, company: '' })) }}
                  className={`w-full bg-slate-900 border rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all ${errors.company ? 'border-rose-500/60' : 'border-slate-700'}`}
                />
                {errors.company && (
                  <p className="text-rose-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.company}
                  </p>
                )}
              </div>

              <div ref={emailRef}>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wide">
                  Work email *
                </label>
                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setErrors(er => ({ ...er, email: '' })) }}
                  className={`w-full bg-slate-900 border rounded-lg px-4 py-2.5 text-white placeholder:text-slate-600 focus:outline-none focus:border-[#16D9F5]/50 transition-all ${errors.email ? 'border-rose-500/60' : 'border-slate-700'}`}
                />
                {errors.email && (
                  <p className="text-rose-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.email}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 2: Markets and source layers */}
          {step === 2 && (
            <div className="space-y-8">
              <div ref={marketsRef}>
                <h2 className="text-xl font-bold text-white mb-2">Which UAE market profile applies?</h2>
                <p className="text-sm text-slate-400 mb-6">Select all that apply — at least one required.</p>
                <div className="flex flex-wrap gap-3">
                  {MARKETS.map(m => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => { toggle(markets, setMarkets, m); setErrors(er => ({ ...er, markets: '' })) }}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                        markets.includes(m)
                          ? 'bg-[#16D9F5]/10 border-[#16D9F5]/50 text-[#16D9F5]'
                          : errors.markets
                          ? 'bg-slate-900 border-rose-500/40 text-slate-400 hover:border-slate-600 hover:text-white'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                {errors.markets && (
                  <p className="text-rose-400 text-xs mt-3 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.markets}
                  </p>
                )}
              </div>

              <div ref={sourcesRef}>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">Source layers of interest</h3>
                <div className="flex flex-wrap gap-3">
                  {SOURCE_LAYERS.map(layer => (
                    <button
                      key={layer}
                      type="button"
                      onClick={() => { toggle(sourceLayers, setSourceLayers, layer); setErrors(er => ({ ...er, sourceLayers: '' })) }}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                        sourceLayers.includes(layer)
                          ? 'bg-[#16D9F5]/10 border-[#16D9F5]/50 text-[#16D9F5]'
                          : errors.sourceLayers
                          ? 'bg-slate-900 border-rose-500/40 text-slate-400 hover:border-slate-600 hover:text-white'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'
                      }`}
                    >
                      {layer}
                    </button>
                  ))}
                </div>
                {errors.sourceLayers && (
                  <p className="text-rose-400 text-xs mt-3 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.sourceLayers}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Industries */}
          {step === 3 && (
            <div ref={industRef}>
              <h2 className="text-xl font-bold text-white mb-2">What is your industry focus?</h2>
              <p className="text-sm text-slate-400 mb-6">Select all that apply — at least one required.</p>
              <div className="flex flex-wrap gap-3">
                {INDUSTRIES.map(ind => (
                  <button
                    key={ind}
                    type="button"
                    onClick={() => { toggle(industries, setIndustries, ind); setErrors(er => ({ ...er, industries: '' })) }}
                    className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                      industries.includes(ind)
                        ? 'bg-[#16D9F5]/10 border-[#16D9F5]/50 text-[#16D9F5]'
                        : errors.industries
                        ? 'bg-slate-900 border-rose-500/40 text-slate-400 hover:border-slate-600 hover:text-white'
                        : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white'
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
              {errors.industries && (
                <p className="text-rose-400 text-xs mt-3 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.industries}
                </p>
              )}
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div>
              <h2 className="text-xl font-bold text-white mb-6">Review your setup</h2>
              <div className="space-y-3">
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Workspace</div>
                  <div className="text-white font-medium">{company || '—'}</div>
                  <div className="text-slate-400 text-sm mt-0.5">{email}</div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Markets</div>
                  <div className="text-white font-medium">{markets.length ? markets.join(', ') : 'None selected'}</div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Source layers</div>
                  <div className="text-white font-medium">{sourceLayers.length ? sourceLayers.join(', ') : 'None selected'}</div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Industries</div>
                  <div className="text-white font-medium">{industries.length ? industries.join(', ') : 'None selected'}</div>
                </div>
              </div>

              <div className="mt-5 flex items-start gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <p className="text-emerald-400/90 text-sm">
                  Your profile helps determine which UAE source layers are relevant.
                  Only validated sources enter monitoring, and limitations are disclosed before pilot delivery.
                  You can update your settings any time from the dashboard.
                </p>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-10 flex justify-between items-center pt-6 border-t border-slate-800">
            {step > 1 ? (
              <button
                onClick={() => { setErrors({}); setStep(s => s - 1) }}
                className="text-slate-400 hover:text-white font-medium text-sm transition-colors"
              >
                Back
              </button>
            ) : <div />}

            {step < totalSteps ? (
              <button
                onClick={goNext}
                className="bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] px-6 py-2 rounded-lg font-bold transition-colors flex items-center gap-2"
              >
                Continue <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={saving}
                className="bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] px-6 py-2 rounded-lg font-bold transition-colors disabled:opacity-60"
              >
                {saving ? 'Saving profile…' : 'Create monitoring profile →'}
              </button>
            )}
          </div>
          {submitError && (
            <div className="mt-4 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
              {submitError}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import { useState, useRef } from 'react'
import { ArrowRight, ShieldCheck, AlertCircle, Lock } from 'lucide-react'
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
  'UAE Capital Market Authority (UAE CMA) [Limited]',
  'Other',
]

const SOURCE_READINESS_PREVIEW = {
  CBUAE: {
    status: 'In remediation — production access blocked',
    detail: '0 fresh-alert eligible CBUAE sources right now: rulebook.centralbank.ae returns HTTP 403 to our production monitoring infrastructure (since 11 July 2026). All 25 configured rulebook/regulatory sources are disclosed as in remediation and are not counted or sold as monitored until access is restored and re-verified from production.',
    tone: 'amber',
  },
  VARA: {
    status: 'Selected-source',
    detail: '3 fresh-alert eligible VARA sources (of 6 enabled), including the full Compliance & Risk Management Rulebook (incl. AML/CFT Part III) and selected publications. The 30-day revision-updates view is in remediation pending a production rebaseline. Selected-source depth, not complete VARA coverage.',
    tone: 'cyan',
  },
  DFSA: {
    status: 'Rulebook platform only — DFSA site blocked from production',
    detail: 'DFSA coverage currently runs on the Thomson Reuters rulebook platform (rulebook + AML/CTF module). The www.dfsa.ae site (consultations, enforcement, MLRO letters, annual reports) returns HTTP 403 to our production monitoring infrastructure (since 11 July 2026) — those 10 sources are in remediation and are not counted or sold as monitored.',
    tone: 'amber',
  },
  'ADGM / FSRA': {
    status: 'Good selected-source',
    detail: '9 fresh-alert eligible ADGM/FSRA sources (of 14 enabled) across legal/document listings and selected regulatory sources, with rulebook gaps disclosed.',
    tone: 'emerald',
  },
  'UAE FIU': {
    status: 'Not monitored',
    detail: 'No fresh-alert eligible FIU sources: the goAML/FIU portal is geo-blocked from our monitoring region, so it is not sold as monitored. Related AML/CFT laws and EOCN sanctions layers are covered under other regulators.',
    tone: 'amber',
  },
  'Ministry of Finance': {
    status: 'Narrow',
    detail: 'Useful for federal finance/tax-adjacent monitoring, but not a primary MLRO source layer.',
    tone: 'slate',
  },
  'UAE Legislation Portal': {
    status: 'Remediation',
    detail: 'High-value federal legislation source remains blocked by WAF/access issues and is not sold as monitored.',
    tone: 'amber',
  },
  'DIFC Laws': {
    status: 'Selected-source',
    detail: 'DIFC coverage includes selected fresh-alert eligible legal sources (legal database, legal notices, data protection, AML/CFT, ESR). The laws-and-regulations root listing is in remediation pending a production rebaseline review. End-to-end DIFC source scope is not claimed.',
    tone: 'cyan',
  },
  'Ministry of Economy': {
    status: 'Narrow',
    detail: 'Useful for selected AML/DNFBP and economy-related source checks; not broad compliance coverage.',
    tone: 'slate',
  },
  FTA: {
    status: 'Limited',
    detail: 'Tax source monitoring is limited and should be validated against your actual VAT/corporate-tax needs.',
    tone: 'amber',
  },
  'UAE Capital Market Authority (UAE CMA) [Limited]': {
    status: 'Limited but useful',
    detail: 'UAE CMA coverage includes AML/CFT, regulations listing, FATCA/CRS and corporate governance (5 fresh-alert eligible sources). The circulars/rules/procedures page is in remediation pending a production rebaseline after the July 2026 SCA→CMA site move.',
    tone: 'amber',
  },
}

const PREVIEW_TONE = {
  emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
  cyan: 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)]',
  amber: 'border-amber-400/20 bg-amber-400/10 text-amber-100',
  slate: 'border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-primary)]',
}

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
  // Company and email come from the registration profile and are read-only here —
  // they are edited later in Settings, not re-entered during onboarding.
  const company = saved.company || currentUser?.company_name || ''
  const email = currentUser?.email || saved.email || ''
  const [markets, setMarkets]   = useState(Array.isArray(saved.markets) ? saved.markets : [])
  const [industries, setIndustries] = useState(Array.isArray(saved.industries) ? saved.industries : saved.industry ? [saved.industry] : [])
  const [sourceLayers, setSourceLayers] = useState(Array.isArray(saved.topics) ? saved.topics : [])
  const [errors, setErrors]     = useState({})
  const [saving, setSaving]     = useState(false)
  const [submitError, setSubmitError] = useState('')

  const marketsRef  = useRef(null)
  const sourcesRef  = useRef(null)
  const industRef   = useRef(null)

  function validateStep(s) {
    const errs = {}
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
      if (errs.markets) { marketsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
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
      const payload = {
        industries,
        markets,
        topics: sourceLayers,
        onboarding_completed: true,
      }
      // Only send company_name when we actually have one, so the read-only
      // prefill can never overwrite the registration company with an empty value.
      if (company) payload.company_name = company
      const data = await profileApi.update(payload)
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
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[var(--bg-navy)] p-6 font-sans text-[var(--text-primary)] selection:bg-[var(--trust-badge)]">
      <div className="w-full max-w-2xl">

        {/* Logo */}
        <div className="mb-10 text-center">
          <div className="inline-flex mb-8">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-10 w-auto" />
          </div>
          <h1 className="text-3xl font-bold text-white mt-2 mb-2">Set up your monitoring profile</h1>
          <p className="text-[var(--text-secondary)]">Step {step} of {totalSteps}</p>
        </div>

        {/* Card */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-muted)] rounded-2xl p-8 md:p-12 shadow-2xl relative overflow-hidden">

          {/* Progress bar */}
          <div className="absolute top-0 left-0 w-full h-1 bg-[var(--bg-raised)]">
            <div
              className="h-full bg-[var(--accent)] transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>

          {/* Step 1: Profile info (read-only — carried over from registration) */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-white mb-2">Your workspace profile</h2>
              <p className="text-sm text-[var(--text-secondary)] mb-6">
                These come from your registration. You can change them later in Settings — no need to re-enter anything here.
              </p>

              <div>
                <span className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                  Company name
                </span>
                <div className="flex w-full items-center justify-between gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-4 py-2.5">
                  <span className="truncate text-white">{company || 'Not set'}</span>
                  <span className="inline-flex flex-shrink-0 items-center gap-1 text-[11px] text-[var(--text-muted)]">
                    <Lock className="h-3 w-3" /> Edit in Settings
                  </span>
                </div>
              </div>

              <div>
                <span className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
                  Work email
                </span>
                <div className="flex w-full items-center justify-between gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-4 py-2.5">
                  <span className="truncate text-white">{email || 'Not set'}</span>
                  <span className="inline-flex flex-shrink-0 items-center gap-1 text-[11px] text-[var(--text-muted)]">
                    <Lock className="h-3 w-3" /> Edit in Settings
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Markets and source layers */}
          {step === 2 && (
            <div className="space-y-8">
              <div ref={marketsRef}>
                <h2 className="text-xl font-bold text-white mb-2">Which UAE market profile applies?</h2>
                <p className="text-sm text-[var(--text-secondary)] mb-6">Select all that apply — at least one required.</p>
                <div className="flex flex-wrap gap-3">
                  {MARKETS.map(m => (
                    <button
                      key={m}
                      type="button"
                      aria-pressed={markets.includes(m)}
                      onClick={() => { toggle(markets, setMarkets, m); setErrors(er => ({ ...er, markets: '' })) }}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                        markets.includes(m)
                          ? 'bg-[var(--trust-badge)] border-[var(--trust-border)] text-[var(--accent)]'
                          : errors.markets
                          ? 'bg-[var(--bg-elevated)] border-rose-500/40 text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
                          : 'bg-[var(--bg-elevated)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
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
                <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">Source layers of interest</h3>
                <div className="mb-4 rounded-xl border border-[var(--trust-border)] bg-[var(--bg-elevated)] p-4">
                  <p className="text-sm font-semibold text-white">Source readiness preview</p>
                  <p className="mt-1 text-xs leading-relaxed text-[var(--text-secondary)]">
                    Source coverage is validated before activation. Some source groups are under remediation.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  {SOURCE_LAYERS.map(layer => (
                    <button
                      key={layer}
                      type="button"
                      aria-pressed={sourceLayers.includes(layer)}
                      onClick={() => { toggle(sourceLayers, setSourceLayers, layer); setErrors(er => ({ ...er, sourceLayers: '' })) }}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                        sourceLayers.includes(layer)
                          ? 'bg-[var(--trust-badge)] border-[var(--trust-border)] text-[var(--accent)]'
                          : errors.sourceLayers
                          ? 'bg-[var(--bg-elevated)] border-rose-500/40 text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
                          : 'bg-[var(--bg-elevated)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
                      }`}
                    >
                      {layer}
                    </button>
                  ))}
                </div>
                <div className="mt-4 grid gap-3">
                  {SOURCE_LAYERS.filter(layer => SOURCE_READINESS_PREVIEW[layer]).map(layer => {
                    const preview = SOURCE_READINESS_PREVIEW[layer]
                    return (
                      <div key={layer} className={`rounded-xl border p-3 ${PREVIEW_TONE[preview.tone] || PREVIEW_TONE.slate}`}>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-sm font-semibold">{layer}</p>
                          <span className="rounded-full border border-current/25 px-2 py-0.5 text-[10px] font-bold">
                            {preview.status}
                          </span>
                        </div>
                        <p className="mt-1 text-xs leading-relaxed opacity-80">{preview.detail}</p>
                      </div>
                    )
                  })}
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
              <p className="text-sm text-[var(--text-secondary)] mb-6">Select all that apply — at least one required.</p>
              <div className="flex flex-wrap gap-3">
                {INDUSTRIES.map(ind => (
                  <button
                    key={ind}
                    type="button"
                    aria-pressed={industries.includes(ind)}
                    onClick={() => { toggle(industries, setIndustries, ind); setErrors(er => ({ ...er, industries: '' })) }}
                    className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                      industries.includes(ind)
                        ? 'bg-[var(--trust-badge)] border-[var(--trust-border)] text-[var(--accent)]'
                        : errors.industries
                        ? 'bg-[var(--bg-elevated)] border-rose-500/40 text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
                        : 'bg-[var(--bg-elevated)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--border)] hover:text-white'
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
                <div className="bg-[var(--bg-elevated)] p-4 rounded-xl border border-[var(--border-muted)]">
                  <div className="text-xs text-[var(--text-muted)] mb-1">Workspace</div>
                  <div className="text-white font-medium">{company || '—'}</div>
                  <div className="text-[var(--text-secondary)] text-sm mt-0.5">{email}</div>
                </div>
                <div className="bg-[var(--bg-elevated)] p-4 rounded-xl border border-[var(--border-muted)]">
                  <div className="text-xs text-[var(--text-muted)] mb-1">Markets</div>
                  <div className="text-white font-medium">{markets.length ? markets.join(', ') : 'None selected'}</div>
                </div>
                <div className="bg-[var(--bg-elevated)] p-4 rounded-xl border border-[var(--border-muted)]">
                  <div className="text-xs text-[var(--text-muted)] mb-1">Source layers</div>
                  <div className="text-white font-medium">{sourceLayers.length ? sourceLayers.join(', ') : 'None selected'}</div>
                </div>
                <div className="bg-[var(--bg-elevated)] p-4 rounded-xl border border-[var(--border-muted)]">
                  <div className="text-xs text-[var(--text-muted)] mb-1">Industries</div>
                  <div className="text-white font-medium">{industries.length ? industries.join(', ') : 'None selected'}</div>
                </div>
              </div>

              <div className="mt-5 flex items-start gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <p className="text-emerald-400/90 text-sm">
                  Your profile helps determine which UAE source layers are relevant.
                  Only fresh-alert eligible sources can move toward monitoring, and limitations are disclosed before pilot delivery.
                  You can update your settings any time from the dashboard.
                </p>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-10 flex justify-between items-center pt-6 border-t border-[var(--border-muted)]">
            {step > 1 ? (
              <button
                onClick={() => { setErrors({}); setStep(s => s - 1) }}
                className="text-[var(--text-secondary)] hover:text-white font-medium text-sm transition-colors"
              >
                Back
              </button>
            ) : <div />}

            {step < totalSteps ? (
              <button
                onClick={goNext}
                className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] px-6 py-2 rounded-lg font-bold transition-colors flex items-center gap-2"
              >
                Continue <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={saving}
                className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] px-6 py-2 rounded-lg font-bold transition-colors disabled:opacity-60"
              >
                {saving ? 'Saving profile…' : 'Create monitoring profile'}
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

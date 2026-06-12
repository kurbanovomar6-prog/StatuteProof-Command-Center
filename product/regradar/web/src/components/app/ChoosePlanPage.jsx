import { useState } from 'react'
import { CheckCircle, Lock, ArrowRight, Sparkles } from 'lucide-react'

const PLANS = [
  {
    id: 'evidence_preview',
    name: 'Evidence Preview',
    price: 'Free',
    period: '7-day access',
    badge: null,
    highlight: false,
    desc: 'Explore the StatuteProof workspace with sample evidence records and source-readiness tools. No live monitoring.',
    cta: 'Continue with Evidence Preview',
    ctaStyle: 'secondary',
    features: [
      'Source readiness review (sample)',
      'Sample evidence records',
      'Sample brief preview',
      'Workspace access',
    ],
    locked: [
      'Live source monitoring',
      'Weekly MLRO brief',
      'Audit binder export',
    ],
  },
  {
    id: 'starter_pilot',
    name: 'Starter Pilot',
    price: '$299',
    period: '/ month',
    badge: null,
    highlight: false,
    desc: 'Up to 3 official UAE sources monitored. Evidence records, basic diff view, weekly source status summary.',
    cta: 'Select Starter Pilot',
    ctaStyle: 'secondary',
    features: [
      'Up to 3 official UAE sources',
      'Evidence records',
      'Basic diff view',
      'Weekly source status summary',
      '30-day evidence retention',
      '1 user',
    ],
    locked: [
      'Custom sources',
      'Audit binder export',
      'Multiple workspaces',
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    price: '$799',
    period: '/ month',
    badge: 'Recommended',
    highlight: true,
    desc: '13–16 official UAE sources — VARA, CBUAE, DFSA, ADGM/FSRA, UAE FIU and more. Full MLRO workflow.',
    cta: 'Select Professional',
    ctaStyle: 'primary',
    features: [
      '13–16 official UAE sources',
      'VARA / CBUAE / DFSA / ADGM / UAE FIU source pack',
      'Evidence records + full diff view',
      'Weekly MLRO brief',
      'High-risk review queue',
      '3 custom public sources',
      'PDF / Markdown export',
      '12-month evidence retention',
      '3 users',
    ],
    locked: [],
  },
  {
    id: 'consultant',
    name: 'Compliance Consultant',
    price: 'From $1,500',
    period: '/ month or custom',
    badge: null,
    highlight: false,
    desc: 'Multiple client workspaces, 25+ monitored sources, white-label reports, extended retention.',
    cta: 'Talk to us',
    ctaStyle: 'secondary',
    features: [
      'Multiple client workspaces',
      '25+ monitored sources',
      '10+ custom sources',
      'Audit binder export',
      'White-label weekly reports',
      'Team roles',
      'Custom source onboarding',
      'Extended evidence retention',
    ],
    locked: [],
  },
]

export default function ChoosePlanPage({ onContinue, selectPlan }) {
  const [selecting, setSelecting] = useState(null)
  const [selected, setSelected] = useState(null)
  const [confirmMsg, setConfirmMsg] = useState('')
  const [error, setError] = useState('')

  async function handleSelect(planId) {
    if (planId === 'evidence_preview') {
      onContinue()
      return
    }
    if (planId === 'consultant') {
      setConfirmMsg('Plan request noted. Our team will contact you to discuss your requirements and activate your workspace.')
      setSelected('consultant')
      return
    }
    setSelecting(planId)
    setError('')
    try {
      await selectPlan(planId)
      setSelected(planId)
      setConfirmMsg('Plan request saved. Our team will contact you to activate your founding pilot. No payment has been processed.')
    } catch {
      setError('Could not save plan selection. Please try again or continue with Evidence Preview.')
    } finally {
      setSelecting(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#07111F] text-slate-200 py-12 px-4">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-[#16D9F5] uppercase tracking-widest mb-4 bg-[#16D9F5]/10 border border-[#16D9F5]/20 px-3 py-1.5 rounded-full">
            <Sparkles className="w-3.5 h-3.5" />
            Choose your source monitoring plan
          </div>
          <h1 className="text-3xl font-bold text-white mb-3">
            Choose the plan that matches your UAE compliance footprint
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm leading-relaxed">
            Founding pilots are manually activated after source readiness review. No payment method is required now.
            Select a plan to record your intent — our team will contact you to confirm your source pack and activate your workspace.
          </p>
        </div>

        {/* Confirm message */}
        {confirmMsg && (
          <div className="mb-8 max-w-2xl mx-auto bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-emerald-300 text-sm text-center">
            <CheckCircle className="w-4 h-4 inline mr-2" />
            {confirmMsg}
            <div className="mt-3">
              <button
                onClick={onContinue}
                className="sp-btn-primary inline-flex items-center gap-2 text-sm"
              >
                Continue to workspace <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 max-w-2xl mx-auto bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-rose-300 text-sm text-center">
            {error}
          </div>
        )}

        {/* Plan cards */}
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
          {PLANS.map(p => (
            <div
              key={p.id}
              className={`rounded-xl border flex flex-col p-6 transition-all ${
                p.highlight
                  ? 'border-[#16D9F5]/40 bg-[#16D9F5]/5 shadow-[0_0_30px_rgba(22,217,245,0.08)]'
                  : 'border-slate-800 bg-[#0D1B2E]'
              } ${selected === p.id ? 'ring-2 ring-emerald-400/50' : ''}`}
            >
              {p.badge && (
                <div className="text-[10px] font-bold text-[#16D9F5] uppercase tracking-widest mb-2">
                  {p.badge}
                </div>
              )}
              <h3 className="font-bold text-lg text-white mb-1">{p.name}</h3>
              <div className="flex items-baseline gap-1 mb-3">
                <span className="text-3xl font-bold text-white">{p.price}</span>
                {p.period && <span className="text-xs text-slate-400">{p.period}</span>}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-5">{p.desc}</p>

              <ul className="space-y-2 mb-4 flex-1">
                {p.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs">
                    <CheckCircle className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${p.highlight ? 'text-[#16D9F5]' : 'text-emerald-400'}`} />
                    <span className="text-slate-300">{f}</span>
                  </li>
                ))}
                {p.locked.map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs opacity-50">
                    <Lock className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-slate-500" />
                    <span className="text-slate-500">{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSelect(p.id)}
                disabled={!!selecting || !!selected}
                className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 ${
                  p.ctaStyle === 'primary'
                    ? 'bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]'
                    : 'border border-slate-700 text-slate-300 hover:border-[#16D9F5]/40 hover:text-white'
                }`}
              >
                {selecting === p.id ? 'Saving…' : selected === p.id ? 'Selected ✓' : p.cta}
              </button>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-center text-xs text-slate-500 max-w-2xl mx-auto">
          Not legal advice. For monitoring information only. No payment is processed during plan selection.
          Billing is manually activated after source readiness review and founding pilot confirmation.
        </p>

        {/* Skip link */}
        {!selected && (
          <div className="text-center mt-4">
            <button
              onClick={onContinue}
              className="text-xs text-slate-500 hover:text-slate-300 underline"
            >
              Skip for now — continue with Evidence Preview
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

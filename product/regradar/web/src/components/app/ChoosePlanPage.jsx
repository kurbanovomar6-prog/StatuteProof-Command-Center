import { useState } from 'react'
import { CheckCircle, Lock, ArrowRight, Sparkles } from 'lucide-react'
import { clearPlanIntent, readPlanIntent } from '../../data/planIntent'

const PLANS = [
  {
    id: 'evidence_preview',
    name: 'Source Readiness Review',
    price: 'Free',
    period: '',
    badge: 'Start here',
    highlight: false,
    desc: 'See which UAE regulatory sources are fresh-alert eligible, limited, or blocked for your compliance profile before any monitoring commitment. No live monitoring.',
    cta: 'Start with Source Readiness Review',
    ctaStyle: 'secondary',
    subnote: 'Free • lowest commitment — no activation wait, no payment',
    features: [
      'Source readiness assessment',
      'Suggested UAE source pack',
      'Sample evidence record',
      'Sample brief preview',
      'Workspace access',
    ],
    locked: [
      'Live source monitoring',
      'Evidence records (live)',
      'Weekly source status summary',
      'Audit binder export',
    ],
  },
  {
    id: 'starter_pilot',
    name: 'Founding Pilot',
    price: '$199',
    period: '/ month',
    badge: null,
    highlight: false,
    desc: 'First paid plan for early users. Up to 3 official UAE sources, evidence records, basic diff view, and weekly source status summary. Manually activated after source readiness review.',
    cta: 'Request founding-pilot activation',
    ctaStyle: 'secondary',
    subnote: 'No payment now — we confirm your source pack first',
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
      'High-risk review queue',
      'Weekly MLRO brief',
      'Audit binder export — pilot roadmap',
    ],
  },
  {
    id: 'professional',
    name: 'UAE Monitor',
    price: '$399',
    period: '/ month',
    badge: 'Recommended',
    highlight: true,
    desc: 'Selected official UAE source scope after readiness review. Manual activation keeps source limits and evidence gates visible.',
    cta: 'Request UAE Monitor activation',
    ctaStyle: 'primary',
    subnote: 'No payment now — we confirm your source pack first',
    features: [
      'Validated official UAE source profile',
      'Selected VARA / DFSA / ADGM / SCA fresh-alert source pack',
      'Evidence records + full diff view',
      'High-risk review queue',
      'Weekly MLRO brief — Telegram (email: requires activation)',
      'Up to 2 custom sources — requires activation',
      'PDF audit pack + Markdown/HTML audit export',
      '180-day evidence retention',
      '2 users',
    ],
    locked: [],
  },
  {
    id: 'consultant',
    name: 'Compliance Consultant',
    price: 'Talk to us',
    period: '',
    badge: null,
    highlight: false,
    desc: 'Advisory firms managing multiple UAE-regulated clients. Custom source scope, extended retention, multi-workspace and white-label on the roadmap.',
    cta: 'Talk to us',
    ctaStyle: 'secondary',
    subnote: 'No payment now — we scope your requirements with you first',
    features: [
      'Custom source scope',
      'Custom evidence retention',
      'PDF audit pack + Markdown/HTML audit export',
      'Custom user count',
      'Multiple client workspaces — pilot roadmap',
      'White-label reports — pilot roadmap',
      'Team roles — pilot roadmap',
    ],
    locked: [],
  },
]

export default function ChoosePlanPage({ onContinue, selectPlan }) {
  const [selecting, setSelecting] = useState(null)
  const [selected, setSelected] = useState(null)
  const [confirmMsg, setConfirmMsg] = useState('')
  const [error, setError] = useState('')
  // 2.3: the plan picked on the public pricing page, carried through
  // registration + email verification via localStorage. Synchronous lazy
  // read — an effect would pop the banner/highlight in a frame late
  // (react review, finding 3).
  const [carriedIntent] = useState(() => {
    const stored = readPlanIntent()
    return PLANS.some((p) => p.id === stored) ? stored : ''
  })

  const clearCarriedIntent = clearPlanIntent

  async function handleSelect(planId) {
    if (planId === 'evidence_preview') {
      // A concrete choice was made — a stale carried intent must not
      // re-banner on a later visit (react review, finding 4).
      clearCarriedIntent()
      onContinue()
      return
    }
    setSelecting(planId)
    setError('')
    try {
      // The consultant tier is a real backend plan (app/plan.py PLAN_NAMES),
      // so it MUST record intent + page the founder exactly like the paid
      // tiers — otherwise the green confirmation is a claim of an action the
      // code never performed.
      await selectPlan(planId)
      setSelected(planId)
      setConfirmMsg(
        planId === 'consultant'
          ? 'Plan request saved. Our team will contact you to discuss your requirements and activate your workspace. No payment has been processed.'
          : 'Plan request saved. Our team will contact you to activate your founding pilot. No payment has been processed.',
      )
      clearCarriedIntent()
    } catch {
      setError('Could not save plan selection. Please try again or continue with the Source Readiness Review.')
    } finally {
      setSelecting(null)
    }
  }

  return (
    <div className="min-h-dvh bg-[var(--bg-navy)] px-4 py-12 text-[var(--text-primary)]">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--accent)] mb-4 bg-[var(--trust-badge)] border border-[var(--trust-border)] px-3 py-1.5 rounded-full">
            <Sparkles className="w-3.5 h-3.5" />
            Choose your source monitoring plan
          </div>
          <h1 className="text-3xl font-bold text-white mb-3">
            Choose the plan that matches your UAE compliance footprint
          </h1>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto text-sm leading-relaxed">
            Founding pilots are manually activated after source readiness review. No payment method is required now.
            Select a plan to record your intent — our team will contact you to confirm your source pack and activate your workspace.
          </p>
        </div>

        {/* What happens next — persistent, so the manual-activation flow is never a dead-end */}
        <div className="mb-8 max-w-3xl mx-auto rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
          <h2 className="text-sm font-semibold text-white mb-1">What happens after you choose</h2>
          <p className="text-xs text-[var(--text-secondary)] mb-4">
            StatuteProof plans are activated by our team — you will not be charged today.
          </p>
          <ol className="grid gap-3 sm:grid-cols-2">
            {[
              ['1', 'You request a plan here', 'No payment is taken now. This records your intent only.'],
              ['2', 'We review your sources', 'The StatuteProof team runs the source readiness review — usually within about 2 business days.'],
              ['3', 'A specialist emails you', 'A StatuteProof specialist emails you to confirm your source pack and any limits.'],
              ['4', 'We switch on monitoring', 'Live monitoring is activated by our team for the approved sources — no setup step you have to trigger.'],
            ].map(([num, title, detail]) => (
              <li key={num} className="flex gap-3">
                <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--trust-badge)] text-xs font-bold text-[var(--accent)]">
                  {num}
                </span>
                <div>
                  <p className="text-xs font-semibold text-[var(--text-primary)]">{title}</p>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-[var(--text-muted)]">{detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        {/* 2.3: acknowledge the plan carried over from the public pricing page */}
        {carriedIntent && !selected && !confirmMsg && (
          <div className="mb-8 max-w-2xl mx-auto rounded-xl border border-[var(--trust-border)] bg-[var(--trust-badge)] p-4 text-sm text-center text-[var(--text-primary)]">
            You chose{' '}
            <span className="font-semibold">
              {PLANS.find((p) => p.id === carriedIntent)?.name || carriedIntent}
            </span>{' '}
            on the pricing page — it is highlighted below. Confirm it to record
            your intent; we verify your source pack first and no payment is
            taken now.
          </div>
        )}

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
                  ? 'border-[var(--trust-border)] bg-[var(--trust-badge)] shadow-[0_0_30px_rgba(22,217,245,0.08)]'
                  : 'border-[var(--border-muted)] bg-[var(--bg-elevated)]'
              } ${selected === p.id ? 'ring-2 ring-emerald-400/50' : ''} ${
                !selected && carriedIntent === p.id ? 'ring-2 ring-[var(--accent)]/60' : ''
              }`}
            >
              {!selected && carriedIntent === p.id && (
                <div className="text-[10px] font-bold text-[var(--accent)] mb-2">
                  Your pick from the pricing page
                </div>
              )}
              {p.badge && !(carriedIntent === p.id && !selected) && (
                <div className="text-[10px] font-bold text-[var(--accent)] mb-2">
                  {p.badge}
                </div>
              )}
              <h3 className="font-bold text-lg text-white mb-1">{p.name}</h3>
              <div className="flex items-baseline gap-1 mb-3">
                <span className="text-3xl font-bold text-white">{p.price}</span>
                {p.period && <span className="text-xs text-[var(--text-secondary)]">{p.period}</span>}
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-5">{p.desc}</p>

              <ul className="space-y-2 mb-4 flex-1">
                {p.features.map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs">
                    <CheckCircle className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${p.highlight ? 'text-[var(--accent)]' : 'text-emerald-400'}`} />
                    <span className="text-[var(--text-primary)]">{f}</span>
                  </li>
                ))}
                {p.locked.map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs opacity-50">
                    <Lock className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-[var(--text-muted)]" />
                    <span className="text-[var(--text-muted)]">{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSelect(p.id)}
                disabled={!!selecting || !!selected}
                className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 ${
                  p.ctaStyle === 'primary'
                    ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)]'
                    : 'border border-[var(--border)] text-[var(--text-primary)] hover:border-[var(--trust-border)] hover:text-white'
                }`}
              >
                {selecting === p.id ? 'Saving…' : selected === p.id ? 'Selected' : p.cta}
              </button>
              {p.subnote && (
                <p className="mt-2 text-center text-[11px] leading-relaxed text-[var(--text-muted)]">{p.subnote}</p>
              )}
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-center text-xs text-[var(--text-secondary)] max-w-2xl mx-auto">
          Monitoring intelligence only. Not legal advice. Source readiness validation required before activation.
          No payment is processed during plan selection.
          Features marked "pilot roadmap" are not live by default. Billing is manually activated after source readiness review and founding pilot confirmation.
        </p>

        {/* Skip link */}
        {!selected && (
          <div className="text-center mt-4">
            <button
              onClick={onContinue}
              className="text-xs text-[var(--text-secondary)] hover:text-white underline"
            >
              Skip for now — continue with Source Readiness Review
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

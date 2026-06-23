import { useEffect, useState } from 'react'
import {
  ArrowRight,
  CheckCircle,
  Hash,
  LockKeyhole,
  RadioTower,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'

// ─── Rotating signal cards in hero panel ─────────────────────────────────────
const SIGNALS = [
  {
    regulator: 'VARA · Virtual Assets Rulebook',
    dot: 'green',
    what: 'VARA amended Chapter 3 of the Virtual Assets and Related Activities Regulations — capital adequacy thresholds revised for Category 3 licence holders.',
    risk: 'HIGH',
    riskNote: 'Mandatory compliance deadline applies. Affects licence renewal and ongoing capital reporting obligations.',
    consider: 'Your MLRO and CFO should review current capital adequacy against the amended thresholds before the next reporting window.',
  },
  {
    regulator: 'CBUAE · AML/CFT Guidelines',
    dot: 'green',
    what: 'CBUAE updated Section 4.2 of its AML/CFT Guidelines — customer due diligence requirements for non-resident customers strengthened.',
    risk: 'MEDIUM',
    riskNote: 'Affects onboarding procedures for non-resident clients. Remediation of existing customer files may be required.',
    consider: 'Review CDD workflows with your MLRO and assess whether existing customer files meet the revised standard.',
  },
  {
    regulator: 'DFSA · CP143 Consultation',
    dot: 'amber',
    what: 'DFSA issued CP143 — 34-page consultation on crypto token classification and disclosure requirements for DIFC-registered entities.',
    risk: 'HIGH',
    riskNote: 'Response deadline in 45 days. Proposed classification changes may affect your current product permissions.',
    consider: 'Assess whether a formal response submission is required and whether proposed changes affect your current authorisation scope.',
  },
  {
    regulator: 'FSRA · ADGM Guidance',
    dot: 'green',
    what: 'ADGM FSRA published updated guidance on virtual asset custody arrangements and segregation requirements.',
    risk: 'MEDIUM',
    riskNote: 'Relevant for all FSRA-regulated firms holding virtual assets on behalf of clients.',
    consider: 'Review current custody and segregation arrangements against the updated FSRA guidance with your legal adviser.',
  },
]

const chainSteps = [
  ['01', 'Source run', 'Official public source fetched and logged'],
  ['02', 'Evidence', 'SHA-256 hash + timestamp preserved'],
  ['03', 'Review', 'MLRO/CCO decision gate recorded'],
  ['04', 'Brief', 'Draft released only after approval'],
]

// Regulator name strip shown below headline
const REGULATOR_STRIP = ['CBUAE', 'DFSA', 'ADGM / FSRA', 'VARA', 'SCA', 'UAE FIU']

function EvidenceDossier() {
  const [idx, setIdx] = useState(0)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const id = setInterval(() => {
      setFading(true)
      setTimeout(() => {
        setIdx(i => (i + 1) % SIGNALS.length)
        setFading(false)
      }, 300)
    }, 5000)
    return () => clearInterval(id)
  }, [])

  const sig = SIGNALS[idx]
  const isHigh = sig.risk === 'HIGH'
  const dotClass =
    sig.dot === 'amber'
      ? 'inline-block h-2 w-2 rounded-full bg-amber-400'
      : 'sp-live-dot'

  return (
    <div className="sp-paper-panel sp-reveal relative overflow-hidden p-5 sm:p-6">
      <div className="absolute right-0 top-0 h-28 w-28 rounded-bl-[4rem] bg-cyan-200/55" />

      <div
        className="relative transition-opacity duration-300"
        style={{ opacity: fading ? 0 : 1 }}
      >
        {/* Header */}
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
            <span className={dotClass} />
            {sig.regulator}
          </div>
          <span className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-100 px-2.5 py-1 text-[11px] font-bold text-amber-900">
            <TriangleAlert className="h-3.5 w-3.5" />
            Sample
          </span>
        </div>

        {/* What changed */}
        <div className="mb-4 rounded-xl border border-slate-200 bg-white/80 px-4 py-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            What changed
          </p>
          <p className="text-sm font-medium leading-snug text-slate-900">{sig.what}</p>
        </div>

        {/* Risk level */}
        <div
          className={`mb-4 rounded-xl border px-4 py-3 ${
            isHigh ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div className="mb-1 flex items-center gap-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Risk level
            </p>
            <span
              className={`rounded-md px-2 py-0.5 text-[11px] font-bold ${
                isHigh ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800'
              }`}
            >
              {sig.risk}
            </span>
          </div>
          <p className="text-xs leading-snug text-slate-600">{sig.riskNote}</p>
        </div>

        {/* What to consider */}
        <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            What you should consider
          </p>
          <p className="text-xs leading-relaxed text-slate-700">{sig.consider}</p>
        </div>

        {/* Dot navigation + footnote */}
        <div className="flex items-center justify-between">
          <p className="text-[10px] leading-relaxed text-slate-400">
            Monitoring intelligence only. Not legal advice.
          </p>
          <div className="flex gap-1.5">
            {SIGNALS.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setFading(true)
                  setTimeout(() => {
                    setIdx(i)
                    setFading(false)
                  }, 200)
                }}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === idx ? 'w-4 bg-cyan-500' : 'w-1.5 bg-slate-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function ChainStrip() {
  return (
    <div className="mt-8 grid gap-3 md:grid-cols-4">
      {chainSteps.map(([num, title, detail], index) => (
        <div
          key={title}
          className="rounded-2xl border border-slate-800 bg-slate-950/45 p-4"
          style={{ animationDelay: `${index * 70}ms` }}
        >
          <p className="sp-mono text-xs font-bold text-cyan-300">{num}</p>
          <p className="mt-2 text-sm font-semibold text-white">{title}</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">{detail}</p>
        </div>
      ))}
    </div>
  )
}

export default function Hero({ onCreateWorkspace, onViewSample }) {
  return (
    <section className="sp-page-orbit px-4 pb-16 pt-24 lg:pb-20 lg:pt-28" id="top">
      <div className="relative z-10 mx-auto max-w-7xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
            <RadioTower className="h-3.5 w-3.5" />
            Selected-source UAE regulatory monitoring
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1.5 text-xs font-semibold text-slate-300">
            <LockKeyhole className="h-3.5 w-3.5 text-amber-300" />
            Customer delivery remains gated
          </div>
        </div>

        <div className="grid items-center gap-8 lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.8fr)]">
          <div className="sp-reveal sp-animate-fade-up">
            {/* Trust badge */}
            <span className="sp-badge-trust sp-animate-fade-up sp-delay-1 mb-5 inline-flex">
              Official UAE sources only
            </span>

            {/* Primary headline */}
            <h1 className="sp-display sp-animate-fade-up sp-delay-1 max-w-4xl text-5xl leading-[1.03] text-white md:text-6xl lg:text-7xl">
              VARA, DFSA, and CBUAE publish without warning. Your team finds out when it's too late.
            </h1>

            {/* Subheadline */}
            <p className="sp-animate-fade-up sp-delay-2 mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
              StatuteProof monitors 252 UAE official sources on a defined schedule, detects
              text changes the moment they appear, and delivers a structured brief with a source URL,
              diff, timestamp, and SHA-256 evidence record your audit trail can rely on.
            </p>

            {/* Pain point bullets */}
            <ul className="sp-animate-fade-up sp-delay-2 mt-6 max-w-xl space-y-2.5">
              {[
                'VARA issued an update. Your team learned about it from a LinkedIn post.',
                'Your board asked for the audit trail. Your spreadsheet has no timestamps.',
                'A DFSA consultation closes in 30 days. Nobody flagged the response deadline.',
              ].map(point => (
                <li key={point} className="flex items-start gap-2.5 text-sm leading-relaxed text-slate-300">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
                  {point}
                </li>
              ))}
            </ul>

            {/* Regulator strip */}
            <div className="sp-animate-fade-up sp-delay-2 mt-6 flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-medium text-slate-500 mr-1">
                Sources monitored include:
              </span>
              {REGULATOR_STRIP.map(name => (
                <span
                  key={name}
                  className="rounded-md border border-slate-700/70 bg-slate-900/50 px-2.5 py-1 text-[11px] font-semibold text-slate-300"
                >
                  {name}
                </span>
              ))}
            </div>

            {/* Trust metrics */}
            <div className="sp-animate-fade-up sp-delay-2 mt-7 grid max-w-2xl gap-2 sm:grid-cols-3">
              {[
                ['252', 'UAE official sources'],
                ['SHA-256', 'Hash per evidence run'],
                ['Human-review', 'MLRO/CCO delivery gate'],
              ].map(([stat, label]) => (
                <div key={stat} className="sp-glass rounded-2xl px-4 py-3">
                  <p className="sp-mono text-base font-bold text-cyan-300">{stat}</p>
                  <p className="mt-0.5 text-[11px] leading-snug text-slate-400">{label}</p>
                </div>
              ))}
            </div>

            {/* CTAs — updated labels */}
            <div className="sp-animate-fade-up sp-delay-3 mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onCreateWorkspace}
                className="sp-btn-primary justify-center px-6"
              >
                View source readiness <ArrowRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={onViewSample}
                className="sp-btn-secondary justify-center px-6"
              >
                View sample evidence record
              </button>
            </div>

            {/* Live indicator + disclaimer */}
            <div className="sp-animate-fade-up sp-delay-3 mt-5 flex flex-col gap-3">
              <div className="inline-flex items-center gap-2 text-sm font-medium text-emerald-300">
                <span className="sp-live-dot" />
                Monitoring active
              </div>
              <div className="flex items-start gap-2 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm leading-relaxed text-emerald-50/80">
                <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                <p>
                  We disclose source limits, failed extraction paths, and review gates before pilot
                  activation. Monitoring intelligence only; not legal advice.
                </p>
              </div>
            </div>
          </div>

          <EvidenceDossier />
        </div>

        <ChainStrip />

        <div className="mt-8 grid gap-3 border-t border-slate-800 pt-5 text-sm text-slate-400 md:grid-cols-3">
          <div className="flex items-start gap-2">
            <Hash className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
            <span>Every saved source-run proof is hash checked before canonical evidence use.</span>
          </div>
          <div className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
            <span>Human review separates monitoring signals from customer-facing draft briefs.</span>
          </div>
          <div className="flex items-start gap-2">
            <TriangleAlert className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
            <span>Selected-source scope. Not a full-country source map or compliance guarantee.</span>
          </div>
        </div>
      </div>
    </section>
  )
}

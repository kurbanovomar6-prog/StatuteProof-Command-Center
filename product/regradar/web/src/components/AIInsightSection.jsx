import { useEffect, useRef, useState } from 'react'
import { LockKeyhole, Zap, ListChecks, Info } from 'lucide-react'

// ─── Sample diff lines ───────────────────────────────────────────────────────
// Realistic CBUAE AML threshold change. Labeled SAMPLE throughout.
const DIFF_LINES = [
  { type: 'ctx',     text: '  Article 7 — Suspicious Transaction Reporting' },
  { type: 'ctx',     text: '  ─────────────────────────────────────────────' },
  { type: 'ctx',     text: '  7(1)  Licensed DNFBPs and financial institutions shall' },
  { type: 'ctx',     text: '        file a Suspicious Transaction Report (STR) with' },
  { type: 'ctx',     text: '        the UAE FIU upon detecting a suspicious transaction' },
  { type: 'ctx',     text: '        regardless of the transaction value.' },
  { type: 'ctx',     text: '' },
  { type: 'removed', text: '- 7(2)  In addition to Article 7(1), any single transaction' },
  { type: 'removed', text: '-       or series of linked transactions exceeding AED 55,000' },
  { type: 'removed', text: '-       shall require mandatory STR filing within 2 business' },
  { type: 'removed', text: '-       days of detection.' },
  { type: 'added',   text: '+ 7(2)  In addition to Article 7(1), any single transaction' },
  { type: 'added',   text: '+       or series of linked transactions exceeding AED 40,000' },
  { type: 'added',   text: '+       shall require mandatory STR filing within 2 business' },
  { type: 'added',   text: '+       days of detection.' },
  { type: 'ctx',     text: '' },
  { type: 'ctx',     text: '  7(3)  MLROs must maintain a written record of all STR' },
  { type: 'ctx',     text: '        decisions and the rationale for non-filing.' },
]

const ACTION_STEPS = [
  'Update transaction monitoring threshold in your AML system from AED 55,000 to AED 40,000',
  'Brief compliance officers and front-line staff on the revised threshold before the effective date',
  'Review transaction history for the past 90 days against the new threshold — identify any retrospective gaps',
  'File updated procedures and threshold documentation with your MLRO and preserve this evidence record',
]

// ─── Scroll-reveal hook ───────────────────────────────────────────────────────
function useInView(options = {}) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); obs.disconnect() } },
      { threshold: 0.12, ...options },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return [ref, inView]
}

// ─── Diff viewer panel ────────────────────────────────────────────────────────
function DiffPanel({ visible }) {
  return (
    <div
      className="flex flex-col h-full"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(18px)',
        transition: 'opacity 520ms cubic-bezier(0.16,1,0.3,1), transform 520ms cubic-bezier(0.16,1,0.3,1)',
        transitionDelay: '80ms',
      }}
    >
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/60 bg-slate-900/80 rounded-tl-xl rounded-tr-xl flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-400/80" />
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400/80" />
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
        </div>
        <div className="flex items-center gap-2">
          <span className="sp-live-dot" />
          <span className="text-[11px] font-semibold text-slate-400 font-mono">
            CBUAE · AML/CFT Guidelines · Rev 2025-01
          </span>
        </div>
        <span className="text-[10px] font-bold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded">
          SAMPLE
        </span>
      </div>

      {/* File path bar */}
      <div className="px-4 py-1.5 bg-slate-950/70 border-b border-slate-800/60 flex-shrink-0">
        <span className="text-[10px] font-mono text-slate-500">
          AML_CFT_Guidelines_v4.pdf · Article 7 · lines 142–158
        </span>
      </div>

      {/* Diff content */}
      <div className="overflow-y-auto flex-1 rounded-bl-xl rounded-br-xl" style={{ background: '#0a0f1a' }}>
        <table className="w-full border-collapse">
          <tbody>
            {DIFF_LINES.map((line, i) => {
              let rowBg = 'transparent'
              let textColor
              let lineNumColor = 'text-slate-700'

              if (line.type === 'removed') {
                rowBg = 'rgba(239,68,68,0.10)'
                textColor = 'text-red-300'
                lineNumColor = 'text-red-700'
              } else if (line.type === 'added') {
                rowBg = 'rgba(52,211,153,0.10)'
                textColor = 'text-emerald-300'
                lineNumColor = 'text-emerald-700'
              } else {
                textColor = 'text-slate-400'
              }

              return (
                <tr key={i} style={{ background: rowBg }}>
                  <td
                    className={`select-none px-3 py-[3px] text-right text-[10px] font-mono ${lineNumColor} w-8 border-r border-slate-800/50 align-top`}
                  >
                    {line.text ? i + 130 : ''}
                  </td>
                  <td
                    className={`px-3 py-[3px] text-[11px] font-mono leading-relaxed whitespace-pre-wrap break-all ${textColor}`}
                  >
                    {line.text || ' '}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── AI Analysis panel ────────────────────────────────────────────────────────
function AnalysisPanel({ visible }) {
  return (
    <div
      className="flex flex-col gap-3 h-full overflow-y-auto"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(18px)',
        transition: 'opacity 560ms cubic-bezier(0.16,1,0.3,1), transform 560ms cubic-bezier(0.16,1,0.3,1)',
        transitionDelay: '200ms',
      }}
    >
      {/* Risk badge row */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-red-500/15 border border-red-400/30 px-3 py-1.5 text-xs font-bold text-red-300">
            <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
            HIGH RISK
          </span>
          <span className="text-[10px] text-slate-500 font-mono">AML · DNFBP · Threshold change</span>
        </div>
        <span className="text-[10px] font-bold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded uppercase tracking-wide">
          Sample — for illustration
        </span>
      </div>

      {/* Section 1: What changed */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 px-4 py-3">
        <p className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
          What changed
        </p>
        <p className="text-sm font-medium leading-snug text-slate-100">
          Article 7(2) threshold for mandatory STR filing lowered from{' '}
          <span className="line-through text-red-400">AED 55,000</span> to{' '}
          <span className="text-emerald-300 font-semibold">AED 40,000</span>.
          All licensed DNFBPs and financial institutions are affected.
        </p>
      </div>

      {/* Section 2: Why it matters */}
      <div className="rounded-xl border border-cyan-500/15 bg-cyan-500/[0.05] px-4 py-3">
        <p className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-cyan-600">
          Why it matters
        </p>
        <p className="text-sm leading-relaxed text-slate-300">
          Transaction monitoring systems must be reconfigured before the effective date.
          Any transaction above AED 40,000 now triggers a mandatory STR obligation — a 27% reduction
          in the threshold. Failure to update constitutes a reportable compliance gap.
        </p>
      </div>

      {/* Section 3: What to do */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 px-4 py-3">
        <div className="mb-2.5 flex items-center gap-2">
          <ListChecks className="h-3.5 w-3.5 text-slate-400" />
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
            What to do
          </p>
        </div>
        <ol className="space-y-2">
          {ACTION_STEPS.map((step, i) => (
            <li key={i} className="flex items-start gap-2.5 text-xs leading-relaxed text-slate-300">
              <span className="mt-0.5 inline-flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500/15 border border-cyan-500/25 text-[9px] font-bold text-cyan-400">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Section 4: Urgency */}
      <div className="flex items-center gap-2 rounded-xl border border-amber-400/20 bg-amber-400/[0.07] px-4 py-2.5">
        <Zap className="h-3.5 w-3.5 flex-shrink-0 text-amber-400" />
        <p className="text-xs font-semibold text-amber-300">
          Effective 1 Jan 2025 — 23 days remaining at time of detection
        </p>
      </div>

      {/* Cryptographic evidence strip */}
      <div className="flex flex-col gap-1 rounded-xl border border-slate-800/80 bg-slate-950/60 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <LockKeyhole className="h-3 w-3 flex-shrink-0 text-slate-500" />
          <span className="font-mono text-[10px] text-slate-500 break-all">
            SHA-256: a3f8b2c4d1e9f07a…  · Captured: 2024-12-08 09:14:22 UTC
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-slate-600 pl-5">
            Source: CBUAE Official Portal · Run ID: ae-cbuae-aml-20241208-0914
          </span>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-[10px] leading-relaxed text-slate-600 text-center">
        Monitoring intelligence only. Not legal advice. Not a guarantee of compliance.
        Consult qualified professionals before making regulatory or operational decisions.
      </p>
    </div>
  )
}

// ─── Main section ─────────────────────────────────────────────────────────────
export default function AIInsightSection() {
  const [sectionRef, sectionInView] = useInView()

  return (
    <section
      ref={sectionRef}
      className="py-24"
      style={{ background: 'linear-gradient(180deg, #07111F 0%, #0a1628 60%, #07111F 100%)' }}
      id="ai-insight"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6">

        {/* Section header */}
        <div
          className="mb-12 text-center"
          style={{
            opacity: sectionInView ? 1 : 0,
            transform: sectionInView ? 'translateY(0)' : 'translateY(16px)',
            transition: 'opacity 480ms cubic-bezier(0.16,1,0.3,1), transform 480ms cubic-bezier(0.16,1,0.3,1)',
          }}
        >
          <span className="sp-badge-trust mb-4 inline-flex">
            AI change analysis
          </span>
          <h2 className="sp-heading mt-4 text-3xl font-bold text-white md:text-4xl">
            Not just "something changed" —<br className="hidden sm:block" />
            {' '}exactly what changed and what to do about it
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-slate-400">
            StatuteProof detects the change in the official source, stores a hash-verified evidence record,
            and runs AI analysis that tells your team what shifted, why it matters, and what action to take.
            Your compliance officer reviews and decides — the AI does not decide for you.
          </p>
        </div>

        {/* Split panel */}
        <div
          className="grid min-h-[560px] gap-4 lg:grid-cols-2"
          style={{
            opacity: sectionInView ? 1 : 0,
            transition: 'opacity 400ms ease',
            transitionDelay: '60ms',
          }}
        >
          {/* Left: diff viewer */}
          <div
            className="flex flex-col overflow-hidden rounded-xl border border-slate-700/50"
            style={{ background: '#070d18' }}
          >
            {/* Column label */}
            <div className="flex items-center gap-2 border-b border-slate-800/50 bg-slate-900/40 px-4 py-2 flex-shrink-0">
              <span className="text-[11px] font-bold uppercase tracking-widest text-slate-500">
                Source diff — what the official text shows
              </span>
            </div>
            <div className="flex-1 min-h-0">
              <DiffPanel visible={sectionInView} />
            </div>
          </div>

          {/* Right: AI analysis */}
          <div
            className="flex flex-col overflow-hidden rounded-xl border border-cyan-500/15 p-4"
            style={{
              background: 'linear-gradient(160deg, rgba(9,22,41,0.98) 0%, rgba(7,17,31,0.97) 100%)',
            }}
          >
            {/* Column label */}
            <div className="mb-3 flex items-center gap-2 flex-shrink-0">
              <span className="text-[11px] font-bold uppercase tracking-widest text-cyan-600">
                AI analysis output
              </span>
            </div>
            <AnalysisPanel visible={sectionInView} />
          </div>
        </div>

        {/* How it works strip */}
        <div
          className="mt-10 grid gap-3 sm:grid-cols-4"
          style={{
            opacity: sectionInView ? 1 : 0,
            transform: sectionInView ? 'translateY(0)' : 'translateY(12px)',
            transition: 'opacity 520ms cubic-bezier(0.16,1,0.3,1), transform 520ms cubic-bezier(0.16,1,0.3,1)',
            transitionDelay: '320ms',
          }}
        >
          {[
            ['01', 'Official source checked', 'Scheduled fetch from the regulator\'s own portal — no third-party feeds'],
            ['02', 'Change detected + hashed', 'Text diff computed; SHA-256 hash stored before anything else runs'],
            ['03', 'AI reads the diff', 'Model reads what changed and produces structured analysis — risk, meaning, actions'],
            ['04', 'Human reviews + delivers', 'Your MLRO or compliance officer approves before any brief leaves the system'],
          ].map(([num, title, detail]) => (
            <div
              key={num}
              className="rounded-xl border border-slate-800 bg-slate-950/45 p-4"
            >
              <p className="sp-mono text-xs font-bold text-cyan-400">{num}</p>
              <p className="mt-2 text-sm font-semibold text-white">{title}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">{detail}</p>
            </div>
          ))}
        </div>

        {/* Trust row */}
        <div
          className="mt-6 flex flex-wrap items-center justify-center gap-3"
          style={{
            opacity: sectionInView ? 1 : 0,
            transition: 'opacity 480ms ease',
            transitionDelay: '420ms',
          }}
        >
          {[
            'AI insight — not legal advice',
            'Human review required before delivery',
            'Cryptographic evidence per run',
            'Official sources only',
          ].map(badge => (
            <span key={badge} className="sp-badge-trust flex items-center gap-1.5">
              <Info className="h-3 w-3 opacity-60" />
              {badge}
            </span>
          ))}
        </div>

      </div>
    </section>
  )
}

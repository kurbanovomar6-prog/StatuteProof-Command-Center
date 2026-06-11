import { ArrowRight } from 'lucide-react'

const steps = [
  {
    n: '01',
    title: 'Official sources are checked and normalized.',
    desc: 'Configured official sources are checked on a defined schedule, then normalized into comparable snapshots with extraction quality recorded.',
  },
  {
    n: '02',
    title: 'Changes are compared against prior snapshots.',
    desc: 'Each run produces a delta status and a proof trail, so changed, unchanged, failed, and quality-drop states are visible before review.',
  },
  {
    n: '03',
    title: 'Reviewed briefs are delivered with source proof and limitations.',
    desc: 'Client-facing briefs are prepared only after relevance and review gates, with official URLs, timestamps, extraction notes, and limitations attached.',
  },
]

export default function HowItWorks() {
  return (
    <section className="py-20 bg-[#07111F]" id="how-it-works">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Source proof workflow
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">From official source to structured brief</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            A monitored update is useful only when your team can verify where it came from, what changed, and what limits apply.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {['FIRST_SEEN', 'UNCHANGED', 'CHANGED', 'QUALITY_DROP', 'FAILED'].map(status => (
            <span key={status} className="text-[10px] font-semibold tracking-wide bg-slate-950/50 border border-slate-800 text-slate-400 rounded-full px-3 py-1">
              {status}
            </span>
          ))}
        </div>

        <div className="flex flex-col md:flex-row items-start gap-0">
          {steps.map((step, i) => (
            <div key={step.n} className="flex flex-col md:flex-row items-start flex-1">
              <div className="flex-1 bg-[#0A1628] rounded-xl border border-slate-800 p-6 shadow-[0_18px_50px_rgba(0,0,0,0.18)] w-full">
                <div className="w-9 h-9 rounded-lg bg-cyan-400/10 border border-cyan-300/30 flex items-center justify-center mb-4">
                  <span className="text-cyan-200 text-xs font-bold">{step.n}</span>
                </div>
                <h3 className="font-semibold text-white mb-2 text-sm">{step.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
              </div>

              {i < steps.length - 1 && (
                <div className="hidden md:flex items-center px-2 pt-8 flex-shrink-0 text-cyan-300/40">
                  <ArrowRight className="w-5 h-5" />
                </div>
              )}
              {i < steps.length - 1 && (
                <div className="md:hidden w-px h-6 bg-slate-800 mx-auto my-1" />
              )}
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}

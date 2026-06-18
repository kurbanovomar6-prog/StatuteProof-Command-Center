import { MapPin, ScanLine, FileText, ShieldCheck } from 'lucide-react'

const STEPS = [
  {
    n: '01',
    icon: MapPin,
    title: 'We map your regulatory scope',
    desc: 'You tell us which UAE regulators apply to your licence type — DFSA, CBUAE, VARA, SCA, or others. We match those to the official sources we monitor and confirm which are active before your pilot begins.',
  },
  {
    n: '02',
    icon: ScanLine,
    title: 'We monitor the official sources',
    desc: 'StatuteProof checks each configured official source on a defined schedule and records a timestamped evidence snapshot every monitoring run. Source access status, extraction method, and quality score are logged on every check.',
  },
  {
    n: '03',
    icon: FileText,
    title: 'When something changes, you get a brief',
    desc: 'Detected changes produce a structured monitoring brief: what changed, which official source, when it was detected, and a risk tier. Briefs require human review by your compliance team before any compliance action is taken.',
  },
  {
    n: '04',
    icon: ShieldCheck,
    title: 'Your evidence trail is preserved',
    desc: 'Every monitoring run produces a cryptographic hash, a stored snapshot, and a diff record. Your compliance team can demonstrate that a source was tracked, when it was checked, and exactly what was captured.',
  },
]

export default function HowItWorks() {
  return (
    <section className="py-20 bg-[#07111F]" id="how-it-works">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-14">
          <span className="sp-kicker">
            How it works
          </span>
          <h2 className="text-3xl font-bold text-white mb-3 mt-4">
            From regulatory scope to evidence trail
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
            StatuteProof is built around one question your auditor will eventually ask: can you show what you were monitoring, when you checked it, and what it said?
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {STEPS.map((step) => {
            const Icon = step.icon
            return (
              <div
                key={step.n}
                className="sp-panel flex flex-col"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 rounded-lg bg-cyan-400/10 border border-cyan-300/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-cyan-300" />
                  </div>
                  <span className="text-[11px] font-bold text-cyan-400/60 tracking-widest">{step.n}</span>
                </div>
                <h3 className="font-semibold text-white text-sm mb-2 leading-snug">{step.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            )
          })}
        </div>

        <div className="mt-10 text-center">
          <p className="text-[11px] text-slate-500 max-w-2xl mx-auto leading-relaxed">
            StatuteProof monitoring briefs require human review before any compliance or regulatory action. Not legal advice.
          </p>
        </div>

      </div>
    </section>
  )
}

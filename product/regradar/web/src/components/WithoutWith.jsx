import { CheckCircle2, XCircle } from 'lucide-react'

const withoutItems = [
  'Manual review of regulator portals — weekly, at best',
  'Updates discovered through peers, newsletters, legal counsel, or clients',
  'No record of what was checked, when, or by whom',
  'No diff between last week and this week',
  'Relevance to your licence type assessed informally',
  'Compliance review begins reactively',
]

const withItems = [
  'Scheduled checks against 79 official UAE regulatory sources — no manual portal visits',
  'Timestamped evidence record for every source check: what was captured, when, by which source',
  'Detected changes flagged for your team with a clear before/after diff',
  'Structured monitoring brief with the official source URL and hash-verified evidence',
  'Alerts scoped to the regulators that apply to your licence type',
  'Human review required before any brief reaches your compliance team',
  'Weekly monitoring summary with limitations documented per source',
]

const workflow = [
  'Official source checked',
  'Change detected',
  'Evidence record stored',
  'Before/after diff created',
  'Brief drafted',
  'Scoped to your profile',
  'Human review',
  'Delivered to your team',
]

function BulletList({ items, tone }) {
  const Icon = tone === 'with' ? CheckCircle2 : XCircle
  const iconClass = tone === 'with' ? 'text-emerald-300' : 'text-rose-300'

  return (
    <ul className="space-y-3">
      {items.map(item => (
        <li key={item} className="flex items-start gap-3 text-sm leading-relaxed text-slate-300">
          <Icon className={`mt-0.5 h-4 w-4 flex-shrink-0 ${iconClass}`} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

export default function WithoutWith() {
  return (
    <section className="bg-[#07111F] py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Workflow comparison
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">The difference your team feels in the first week</h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            From manual portal checking to evidence-backed regulatory intelligence.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div className="rounded-2xl border border-rose-400/15 bg-slate-950/40 p-6 shadow-[0_18px_50px_rgba(0,0,0,0.22)]">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-rose-400/20 bg-rose-400/10">
                <XCircle className="h-5 w-5 text-rose-300" />
              </div>
              <h3 className="text-lg font-semibold text-white">Without StatuteProof</h3>
            </div>
            <BulletList items={withoutItems} tone="without" />
          </div>

          <div className="rounded-2xl border border-emerald-400/20 bg-cyan-400/[0.04] p-6 shadow-[0_18px_50px_rgba(0,0,0,0.22)]">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-400/25 bg-emerald-400/10">
                <CheckCircle2 className="h-5 w-5 text-emerald-300" />
              </div>
              <h3 className="text-lg font-semibold text-white">With StatuteProof</h3>
            </div>
            <BulletList items={withItems} tone="with" />
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950/35 px-4 py-4">
          <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2 text-xs text-slate-400">
            {workflow.map((step, index) => (
              <span key={step} className="inline-flex items-center gap-2">
                <span>{step}</span>
                {index < workflow.length - 1 && <span className="text-cyan-300/50">→</span>}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

import {
  ArrowRight,
  CheckCircle,
  FileCheck2,
  Hash,
  LockKeyhole,
  RadioTower,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'

const proofRows = [
  ['Source', 'VARA official notices'],
  ['Run status', 'CHANGED'],
  ['Normalized hash', 'sha256:7b1e4a8f...d92'],
  ['Review state', 'Human review required'],
]

const chainSteps = [
  ['01', 'Source run', 'Official public source checked'],
  ['02', 'Evidence', 'Snapshot + hash preserved'],
  ['03', 'Review', 'MLRO/founder decision logged'],
  ['04', 'Brief', 'Draft only until approved'],
]

function EvidenceDossier() {
  return (
    <div className="sp-paper-panel sp-reveal relative overflow-hidden p-5 sm:p-6">
      <div className="absolute right-0 top-0 h-28 w-28 rounded-bl-[4rem] bg-cyan-200/55" />
      <div className="relative">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="sp-mono text-[11px] font-bold uppercase tracking-wide text-slate-500">Canonical evidence preview</p>
            <h3 className="mt-2 max-w-xs text-2xl font-semibold leading-tight text-slate-950">
              A source change is not a customer brief yet.
            </h3>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-100 px-2.5 py-1 text-[11px] font-bold text-amber-900">
            <TriangleAlert className="h-3.5 w-3.5" />
            Sample
          </span>
        </div>

        <div className="mb-5 grid gap-2">
          {proofRows.map(([label, value]) => (
            <div key={label} className="grid grid-cols-[110px_1fr] gap-3 rounded-xl border border-slate-300/70 bg-white/72 px-3 py-2.5 text-sm">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
              <span className={label.includes('hash') ? 'sp-mono truncate font-semibold text-cyan-800' : 'font-semibold text-slate-900'}>
                {value}
              </span>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-300 bg-slate-950 p-4 text-white">
          <div className="mb-3 flex items-center gap-2">
            <FileCheck2 className="h-4 w-4 text-cyan-200" />
            <p className="text-sm font-semibold">Brief gate</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            {[
              ['Proof', 'verified', 'emerald'],
              ['Review', 'pending', 'amber'],
              ['Delivery', 'blocked', 'slate'],
            ].map(([label, value, tone]) => (
              <div key={label} className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
                <p className={`mt-1 text-sm font-bold ${
                  tone === 'emerald' ? 'text-emerald-300' : tone === 'amber' ? 'text-amber-300' : 'text-slate-300'
                }`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>

        <p className="mt-4 text-xs leading-relaxed text-slate-600">
          Interface sample only. It shows the chain of custody; it is not a real regulatory update,
          legal advice, or regulator approval.
        </p>
      </div>
    </div>
  )
}

function ChainStrip() {
  return (
    <div className="mt-8 grid gap-3 md:grid-cols-4">
      {chainSteps.map(([num, title, detail], index) => (
        <div key={title} className="rounded-2xl border border-slate-800 bg-slate-950/45 p-4" style={{ animationDelay: `${index * 70}ms` }}>
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
    <section className="sp-page-orbit px-4 pt-24 pb-16 lg:pt-28 lg:pb-20" id="top">
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
          <div className="sp-reveal">
            <h1 className="max-w-4xl text-4xl font-semibold leading-[1.03] text-white md:text-5xl lg:text-[4.55rem]">
              Official UAE source changes, captured as evidence before anyone calls them compliance.
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
              StatuteProof watches selected official UAE sources, preserves hash-verified source evidence,
              and keeps draft briefs behind human review and delivery gates.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button onClick={onCreateWorkspace} className="sp-btn-primary justify-center px-6">
                Request source review <ArrowRight className="h-4 w-4" />
              </button>
              <button type="button" onClick={onViewSample} className="sp-btn-secondary justify-center px-6">
                View sample evidence flow
              </button>
            </div>

            <div className="mt-7 grid max-w-2xl grid-cols-3 gap-2">
              {[
                ['241', 'enabled UAE source records'],
                ['172', 'fresh-alert eligible'],
                ['0', 'complete coverage claims'],
              ].map(([value, label]) => (
                <div key={label} className="rounded-2xl border border-slate-800 bg-slate-950/45 px-4 py-3">
                  <p className="sp-mono text-2xl font-bold text-white">{value}</p>
                  <p className="mt-1 text-[11px] leading-snug text-slate-500">{label}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-start gap-2 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm leading-relaxed text-emerald-50/80">
              <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
              <p>
                We disclose source limits, failed extraction paths, and review gates before pilot activation.
                Monitoring intelligence only; not legal advice.
              </p>
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

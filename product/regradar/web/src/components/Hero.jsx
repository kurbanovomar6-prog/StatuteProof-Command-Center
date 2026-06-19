import { ArrowRight, CheckCircle, Clock, FileCheck2, Hash, ShieldCheck, TriangleAlert } from 'lucide-react'

function SampleEvidenceCard() {
  const rows = [
    ['Source', 'VARA Enforcement Notices'],
    ['Status', 'CHANGED'],
    ['Risk', 'MEDIUM'],
    ['Evidence hash', 'sha256:7b1e4a8f...d92'],
    ['Diff available', 'Yes'],
    ['Proof saved', 'Snapshot + proof block'],
    ['Human review', 'Required before delivery'],
  ]

  return (
    <div className="sp-panel relative overflow-hidden p-5 text-sm">
      <div className="absolute left-0 top-0 h-full w-1 bg-cyan-300/70" />

      <div className="mb-5 flex flex-wrap items-start justify-between gap-3 pl-2">
        <div>
          <span className="sp-demo-badge">
            <TriangleAlert className="h-3 w-3" />
            SAMPLE / DEMO — not a real regulatory update
          </span>
          <h3 className="mt-4 text-lg font-semibold text-white">Evidence record preview</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">
            Shows the fields an MLRO reviews before a brief can be approved.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-md border border-blue-400/30 bg-blue-400/10 px-2.5 py-1 text-xs font-semibold text-blue-200">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-300" />
          CHANGED
        </span>
      </div>

      <div className="mb-4 rounded-lg border border-slate-800 bg-slate-950/35 p-4">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-white">VARA — Enforcement Notices</p>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
              <Clock className="h-3.5 w-3.5" />
              2026-06-10 09:14 UTC
            </p>
          </div>
          <span className="rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-1 text-xs font-semibold text-amber-200">
            Human review
          </span>
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label} className="rounded-md border border-slate-800 bg-[#07111F]/70 px-3 py-2">
              <p className="text-[11px] font-medium text-slate-500">{label}</p>
              <p className={`mt-0.5 truncate text-sm font-semibold ${label.includes('hash') ? 'sp-mono text-cyan-200' : 'text-slate-200'}`}>
                {value}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-3">
          <CheckCircle className="mb-2 h-4 w-4 text-emerald-300" />
          <p className="text-xs font-semibold text-emerald-100">Diff ready</p>
          <p className="mt-1 text-[11px] text-emerald-100/70">3 changed sections</p>
        </div>
        <div className="rounded-lg border border-cyan-400/20 bg-cyan-400/10 p-3">
          <FileCheck2 className="mb-2 h-4 w-4 text-cyan-200" />
          <p className="text-xs font-semibold text-cyan-100">Proof saved</p>
          <p className="mt-1 text-[11px] text-cyan-100/70">Timestamped record</p>
        </div>
        <div className="rounded-lg border border-slate-600/40 bg-slate-800/35 p-3">
          <Hash className="mb-2 h-4 w-4 text-slate-300" />
          <p className="text-xs font-semibold text-slate-200">Hash stored</p>
          <p className="mt-1 text-[11px] text-slate-500">Old/new compared</p>
        </div>
      </div>

      <div className="mt-4 border-t border-slate-800 pt-3 text-xs leading-relaxed text-slate-500">
        Sample data for interface review only. Not legal advice. Not regulator approval.
      </div>
    </div>
  )
}

export default function Hero({ onCreateWorkspace, onViewSample }) {
  return (
    <section className="relative overflow-hidden bg-[#07111F] px-4 pt-24 pb-16 lg:pt-28 lg:pb-20" id="top">

      {/* Background grid */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-80">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(#16D9F5 1px, transparent 1px), linear-gradient(90deg, #16D9F5 1px, transparent 1px)',
            backgroundSize: '44px 44px',
            backgroundPosition: 'center center',
          }}
        />
      </div>

      <div className="relative z-10 mx-auto grid max-w-7xl gap-10 lg:grid-cols-[minmax(0,0.92fr)_minmax(420px,0.78fr)] lg:items-center">
        <div className="max-w-3xl">
          <div className="sp-kicker mb-6">
            <ShieldCheck className="h-4 w-4" />
            Official-source monitoring for UAE compliance teams
          </div>

          <h1 className="max-w-4xl text-4xl font-semibold leading-[1.08] text-white md:text-5xl lg:text-6xl">
            UAE regulatory updates, captured with evidence before they become compliance surprises.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
            StatuteProof monitors official UAE regulatory sources, detects text changes, preserves
            timestamped evidence records, and prepares human-reviewed compliance briefs for MLROs
            and compliance teams.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button onClick={onCreateWorkspace} className="sp-btn-primary justify-center px-6">
              Request a free source readiness review <ArrowRight className="h-4 w-4" />
            </button>
            <button type="button" onClick={onViewSample} className="sp-btn-secondary justify-center px-6">
              View sample evidence brief
            </button>
          </div>

          <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
            {[
              ['238', 'UAE source records'],
              ['168', 'fresh-alert eligible'],
              ['Selected', 'licence profiles mapped'],
            ].map(([value, label]) => (
              <div key={label} className="sp-panel-muted px-4 py-3">
                <p className="sp-mono text-2xl font-semibold text-white">{value}</p>
                <p className="mt-1 text-xs leading-snug text-slate-500">{label}</p>
              </div>
            ))}
          </div>

          <p className="mt-5 max-w-2xl text-xs leading-relaxed text-slate-500">
            Monitoring intelligence only. Not legal advice. Source coverage, extraction quality,
            activation readiness, and failure reasons are disclosed before activation.
          </p>
        </div>

        <SampleEvidenceCard />
      </div>
    </section>
  )
}

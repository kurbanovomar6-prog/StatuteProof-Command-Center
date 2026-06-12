import { ArrowRight, ShieldCheck, Clock, Hash, CheckCircle } from 'lucide-react'

function SampleEvidenceCard() {
  return (
    <div className="max-w-lg mx-auto mt-10 bg-[#0D1B2E] border border-slate-700 rounded-xl p-5 text-sm shadow-xl shadow-black/30">
      {/* SAMPLE label row */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest bg-amber-400/10 border border-amber-400/20 px-2.5 py-1 rounded-full">
          SAMPLE — NOT REAL REGULATORY DATA
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-400">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
          CHANGED
        </span>
      </div>

      {/* Source / regulator */}
      <div className="border-b border-slate-800 pb-3 mb-3">
        <p className="text-base font-bold text-white">VARA Regulatory Framework</p>
        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
          <span>VARA</span>
          <span className="text-slate-700">·</span>
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> 2026-06-10 09:14 UTC</span>
        </div>
      </div>

      {/* Risk / affected */}
      <div className="flex gap-4 text-xs mb-3">
        <div>
          <p className="text-slate-500 mb-0.5">Risk</p>
          <p className="text-red-400 font-bold">HIGH</p>
        </div>
        <div>
          <p className="text-slate-500 mb-0.5">Affected</p>
          <p className="text-slate-200">VASP / MLRO / Compliance</p>
        </div>
      </div>

      {/* Hashes */}
      <div className="border-t border-slate-800 pt-3 mb-3 space-y-1.5 text-xs">
        <div className="flex items-center gap-2">
          <Hash className="w-3 h-3 text-slate-500 flex-shrink-0" />
          <span className="text-slate-500 w-20 flex-shrink-0">Old hash</span>
          <span className="font-mono text-slate-400">a3f8d9c2b1e7...</span>
        </div>
        <div className="flex items-center gap-2">
          <Hash className="w-3 h-3 text-blue-400 flex-shrink-0" />
          <span className="text-slate-500 w-20 flex-shrink-0">New hash</span>
          <span className="font-mono text-blue-400">7b1e4a8f3d92...</span>
        </div>
      </div>

      {/* Proof row */}
      <div className="flex items-center gap-4 text-xs mb-3">
        <div className="flex items-center gap-1 text-emerald-400">
          <CheckCircle className="w-3 h-3" />
          <span>Diff: Available</span>
        </div>
        <div className="flex items-center gap-1 text-emerald-400">
          <CheckCircle className="w-3 h-3" />
          <span>Snapshot: Saved</span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs">
        <span className="text-amber-400 font-semibold">Human review: Required</span>
        <span className="text-slate-600">Not legal advice</span>
      </div>
    </div>
  )
}

export default function Hero({ onCreateWorkspace, onSignIn }) {
  return (
    <section className="relative pt-24 pb-20 lg:pt-32 lg:pb-28 overflow-hidden flex flex-col items-center bg-[#07111F]">

      {/* Background grid */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(#16D9F5 1px, transparent 1px), linear-gradient(90deg, #16D9F5 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            backgroundPosition: 'center center',
          }}
        />
        {/* Subtle radial glow */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] opacity-[0.06]"
          style={{ background: 'radial-gradient(ellipse at center, #16D9F5 0%, transparent 70%)' }}
        />
      </div>

      <div className="max-w-4xl mx-auto px-6 relative z-10 w-full text-center">

        {/* Eyebrow badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700 text-[#16D9F5] text-[11px] font-semibold mb-7 uppercase tracking-[0.15em] relative overflow-hidden">
          <ShieldCheck className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="relative z-10">UAE Regulatory Monitoring</span>
          <span className="absolute inset-0 bg-[#16D9F5]/10 origin-left animate-rr-pulse-x" />
        </div>

        {/* Headline */}
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-[1.12] mb-6 tracking-tight">
          UAE regulatory updates, captured with evidence{' '}
          <span className="relative inline-block text-[#16D9F5]">
            before they become compliance surprises.
            <span className="absolute -bottom-1 left-0 right-0 h-[2px] bg-[#16D9F5]/60 rounded-full" />
          </span>
        </h1>

        {/* Subheadline */}
        <p className="text-lg md:text-xl text-slate-400 mb-8 leading-relaxed max-w-3xl mx-auto">
          StatuteProof monitors official UAE regulatory sources, detects text changes, preserves
          timestamped evidence records, and prepares human-reviewed compliance briefs for MLROs
          and compliance teams.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-4">
          <button
            onClick={onCreateWorkspace}
            className="inline-flex items-center justify-center gap-2 bg-[#16D9F5] hover:bg-[#0EC8E4] text-[#07111F] font-bold px-8 py-3 rounded-lg transition-colors shadow-[0_0_24px_rgba(22,217,245,0.22)] hover:shadow-[0_0_36px_rgba(22,217,245,0.45)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#16D9F5]"
          >
            Request a free source readiness review <ArrowRight className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onSignIn}
            className="inline-flex items-center justify-center gap-2 text-slate-200 border border-slate-700 hover:bg-slate-800 hover:border-slate-600 px-8 py-3 rounded-lg transition-colors font-semibold"
          >
            View sample evidence brief
          </button>
        </div>

        {/* Trust line */}
        <p className="text-xs text-slate-500 mb-1">
          Monitoring intelligence only — not legal advice.
        </p>
        <p className="text-xs text-slate-700 max-w-2xl mx-auto leading-relaxed">
          FTA, e-Laws, Official Gazette, and Capital Market Authority / former SCA have documented
          access limitations — disclosed before any pilot begins.
        </p>

        {/* Sample evidence alert card */}
        <SampleEvidenceCard />
      </div>
    </section>
  )
}

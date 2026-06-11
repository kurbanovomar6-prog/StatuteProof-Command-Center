import { ArrowRight, Bell, Search, Filter, Check, AlertTriangle, Shield, ShieldCheck } from 'lucide-react'

const DashboardMockup = () => (
  <div className="relative w-full max-w-[850px] mx-auto rounded-xl overflow-hidden shadow-2xl bg-slate-900 border border-slate-800/50 flex flex-col md:rotate-1 hover:rotate-0 transition-all duration-700 ease-out hover:shadow-cyan-900/20">
    <div className="pointer-events-none absolute left-5 top-14 z-20 hidden gap-2 md:flex">
      {['Source proof', 'Human review', 'Coverage status'].map(label => (
        <span key={label} className="rounded-full border border-cyan-300/25 bg-slate-950/80 px-3 py-1 text-[10px] font-semibold text-cyan-100 shadow-lg">
          {label}
        </span>
      ))}
    </div>
    <div className="pointer-events-none absolute bottom-5 right-5 z-20 hidden md:block">
      <span className="rounded-full border border-amber-300/25 bg-slate-950/85 px-3 py-1 text-[10px] font-semibold text-amber-200 shadow-lg">
        Limitations disclosed
      </span>
    </div>
    {/* Browser bar */}
    <div className="h-10 bg-slate-950 flex items-center px-4 border-b border-slate-800 flex-shrink-0">
      <div className="flex gap-2">
        <div className="w-3 h-3 rounded-full bg-slate-700" />
        <div className="w-3 h-3 rounded-full bg-slate-700" />
        <div className="w-3 h-3 rounded-full bg-slate-700" />
      </div>
      <div className="mx-auto flex gap-4 text-xs font-medium text-slate-500">
        <span className="text-[#16D9F5]">Monitoring</span>
        <span className="hover:text-slate-300 transition-colors cursor-pointer">Analytics</span>
        <span className="hover:text-slate-300 transition-colors cursor-pointer">Settings</span>
      </div>
    </div>

    <div className="flex bg-slate-900 h-[400px] sm:h-[480px]">
      {/* Left sidebar */}
      <div className="w-56 border-r border-slate-800 p-4 hidden sm:flex flex-col flex-shrink-0">
        <div className="h-8 bg-slate-800/50 rounded flex items-center px-3 gap-2 mb-6">
          <Search className="w-4 h-4 text-slate-500" />
          <span className="text-slate-500 text-xs">Search database...</span>
        </div>

        <div className="space-y-4 flex-1">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">System status</div>
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-400 bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Validated layer configured — 9 sources</span>
            </div>
          </div>

          <div className="pt-2">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">Jurisdictions</div>
            <div className="space-y-1">
              {[
                { name: 'UAE', count: '9 sources', active: true },
              ].map(j => (
                <div key={j.name} className={`flex items-center justify-between text-xs p-2 rounded transition-colors ${j.active ? 'text-slate-300 bg-slate-800/50' : 'text-slate-400 hover:bg-slate-800/30'}`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${j.active ? 'bg-[#16D9F5] shadow-[0_0_5px_#16D9F5]' : 'bg-slate-600'}`} />
                    {j.name}
                  </div>
                  <span className="text-slate-500">{j.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Change feed */}
      <div className="flex-1 p-5 overflow-y-auto flex flex-col gap-4 bg-[#0a0f18]">
        <div className="flex justify-between items-center mb-1">
          <h3 className="text-white font-semibold text-lg flex items-center gap-2">
            <Bell className="w-5 h-5 text-[#16D9F5]" />
            Change feed
          </h3>
          <Filter className="w-4 h-4 text-slate-500" />
        </div>

        {/* HIGH */}
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4 relative group hover:border-slate-600/80 transition-colors">
          <div className="absolute top-4 right-4 flex gap-2 items-center">
            <span className="flex items-center gap-1 px-2 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-medium rounded border border-emerald-500/20">
              <Check className="w-3 h-3" /> Review gate
            </span>
            <span className="px-2 py-1 bg-rose-500/10 text-rose-400 text-[10px] font-bold rounded uppercase border border-rose-500/20 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />High risk
            </span>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-slate-700 flex flex-shrink-0 items-center justify-center text-[10px] font-bold text-white leading-none text-center">CBUAE</div>
            <div className="flex-1 pr-40">
              <div className="text-xs text-slate-400 mb-1">Official source · 14 minutes ago</div>
              <div className="text-sm font-semibold text-white mb-3 group-hover:text-cyan-50 transition-colors">New licensing requirements detected</div>
              <div className="text-xs text-slate-300 bg-slate-900/80 p-3 rounded-md border border-cyan-900/30 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#16D9F5]" />
                <div className="flex items-center gap-2 mb-2 text-[#16D9F5] font-medium text-xs">
                  <Shield className="w-3.5 h-3.5" />
                  <span>Source proof: cbuae.gov.ae · Checked 14:32 · Extraction: Good</span>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <div>
                    <span className="block text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">Affected</span>
                    <span className="text-slate-300 font-medium bg-slate-800 px-2 py-0.5 rounded">VASPs, fintechs</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">Delta status</span>
                    <span className="text-rose-300 font-medium">CHANGED</span>
                  </div>
                </div>
                <p className="mt-3 text-slate-400 leading-relaxed border-t border-slate-800 pt-2">
                  <strong className="text-white font-medium">Action:</strong> Review licensing and reporting obligations.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* MEDIUM */}
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4 relative group hover:border-slate-600/80 transition-colors">
          <div className="absolute top-4 right-4">
            <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-[10px] font-bold rounded uppercase border border-amber-500/20">Medium risk</span>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-slate-700 flex flex-shrink-0 items-center justify-center text-[10px] font-bold text-white leading-none text-center">VARA</div>
            <div className="flex-1 pr-24">
              <div className="text-xs text-slate-400 mb-1">Official source · 2 hours ago</div>
              <div className="text-sm font-semibold text-white mb-2 group-hover:text-cyan-50 transition-colors">VASP rulebook update detected</div>
              <div className="text-xs text-slate-400">
                <strong className="text-white font-medium">Affected:</strong> VASPs and compliance teams.<br />
                <strong className="text-white font-medium">Action:</strong> Review profile relevance.
              </div>
            </div>
          </div>
        </div>

        {/* LOW */}
        <div className="bg-slate-800/20 border border-slate-800/50 rounded-lg p-4 relative opacity-70 hover:opacity-100 transition-opacity">
          <div className="absolute top-4 right-4">
            <span className="px-2 py-1 bg-slate-500/10 text-slate-400 text-[10px] font-bold rounded uppercase border border-slate-500/20">Low risk</span>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-slate-800 flex flex-shrink-0 items-center justify-center text-[10px] font-bold text-slate-400">DFSA</div>
            <div>
              <div className="text-xs text-slate-500 mb-1">Official source · Yesterday</div>
              <div className="text-sm font-medium text-slate-300">Rulebook page unchanged</div>
              <div className="text-xs text-slate-500 mt-1">
                <span className="text-slate-400">Status:</span> UNCHANGED ·{' '}
                <span className="text-slate-400">Action:</span> No alert issued
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)

export default function Hero({ onCreateWorkspace, onSignIn }) {
  return (
    <section className="relative pt-24 pb-20 lg:pt-32 lg:pb-32 overflow-hidden flex flex-col items-center bg-[#07111F]">

      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Subtle grid */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(#16D9F5 1px, transparent 1px), linear-gradient(90deg, #16D9F5 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            backgroundPosition: 'center center',
          }}
        />
      </div>

      {/* Hero copy */}
      <div className="max-w-7xl mx-auto px-6 relative z-10 w-full text-center mb-12">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700 text-[#16D9F5] text-[11px] font-semibold mb-6 uppercase tracking-widest relative overflow-hidden">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="relative z-10">Human-reviewed regulatory monitoring · UAE</span>
          <span className="absolute inset-0 bg-[#16D9F5]/10 origin-left animate-rr-pulse-x" />
        </div>

        {/* Headline */}
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-[1.15] mb-6 tracking-tight max-w-4xl mx-auto">
          Regulatory changes, reviewed before<br />
          <span className="text-[#16D9F5] relative inline-block">your team sees them.
            <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-[#16D9F5] rounded-full" />
          </span>
        </h1>

        {/* Description */}
        <p className="text-lg md:text-xl text-slate-400 mb-3 leading-relaxed max-w-2xl mx-auto">
          StatuteProof monitors official UAE regulatory sources and delivers source-backed compliance briefs —
          with human review, relevance filtering, and limitations disclosed before delivery.
        </p>
        <p className="text-sm text-slate-500 mb-8 max-w-4xl mx-auto leading-relaxed">
          9 validated UAE financial sources. Extraction quality documented per source. Honest about what cannot be monitored.
          <br />
          CBUAE · VARA · DFSA · ADGM/FSRA · UAE FIU and more — source transparency report included before every pilot.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={onCreateWorkspace}
            className="inline-flex items-center justify-center gap-2 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold px-8 py-3 rounded-lg transition-colors shadow-[0_0_20px_rgba(22,217,245,0.25)] hover:shadow-[0_0_30px_rgba(22,217,245,0.5)]"
          >
            Create pilot workspace <ArrowRight className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onSignIn}
            className="inline-flex items-center justify-center gap-2 text-white border border-slate-700 hover:bg-slate-800 hover:border-[#16D9F5]/40 px-8 py-3 rounded-lg transition-colors"
          >
            Sign in
          </button>
        </div>
        <p className="text-xs text-slate-600 mt-4 max-w-3xl mx-auto leading-relaxed">
          Monitoring information only. Not legal advice and not a guarantee of compliance.
        </p>
        <p className="text-xs text-slate-700 mt-2 max-w-3xl mx-auto leading-relaxed">
          FTA, e-Laws, Official Gazette, and Capital Market Authority / former SCA have documented
          access limitations — disclosed before any pilot begins.
        </p>
      </div>

      {/* Dashboard mockup */}
      <div className="w-full max-w-7xl px-6 relative z-10">
        <DashboardMockup />
      </div>
    </section>
  )
}

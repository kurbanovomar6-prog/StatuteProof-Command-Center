import { Globe, Monitor, Search, Map, Rss, FileText, Webhook, Languages, Wrench, ArrowRight } from 'lucide-react'

const METHODS = [
  { Icon: Globe,     title: 'Static HTML',      desc: 'Direct HTML page parsing — the fastest connection method.' },
  { Icon: Monitor,   title: 'JS rendering',     desc: 'Headless Chromium for SPA and React-based portals.' },
  { Icon: Search,    title: 'URL discovery',    desc: 'Checks 20+ regulatory URL patterns on the same domain.' },
  { Icon: Map,       title: 'Sitemap',          desc: 'Sitemap discovery for tracking newly published documents.' },
  { Icon: Rss,       title: 'RSS / Atom',       desc: 'Subscribes to official news and publication feeds.' },
  { Icon: FileText,  title: 'PDF & documents',  desc: 'Text extraction from official PDF documents.' },
  { Icon: Webhook,   title: 'Public APIs',      desc: 'Open endpoint detection for SPA government portals.' },
  { Icon: Languages, title: 'Language versions',desc: 'Auto-detects the best language copy of a source.' },
  { Icon: Wrench,    title: 'Custom adapter',   desc: 'Recommends a tailored solution when standard methods are insufficient.' },
]

export default function AddYourSource() {
  return (
    <section className="py-20 bg-[#0A1628]" id="custom-source">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700 text-[#16D9F5] text-[11px] font-semibold mb-5 uppercase tracking-widest">
            Custom source onboarding
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Your regulator not listed? We can test it.
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto leading-relaxed">
            If your regulator or legal portal is not listed, StatuteProof can test whether it can be monitored
            through HTML, PDF, RSS, sitemap or a custom adapter.
            Custom source requests are managed from your private dashboard after onboarding.
          </p>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mb-12">
          {METHODS.map(({ Icon, title, desc }) => (
            <div key={title} className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5 flex flex-col gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#16D9F5]/10 border border-[#16D9F5]/20 flex items-center justify-center flex-shrink-0">
                <Icon className="w-4 h-4 text-[#16D9F5]" />
              </div>
              <p className="text-sm font-semibold text-white">{title}</p>
              <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        <div className="bg-[#0D1B2E] border border-slate-800 rounded-2xl p-8 md:p-10">
          <div className="flex flex-col md:flex-row md:items-center gap-6 md:gap-10">
            <div className="flex-1">
              <p className="text-xs font-semibold text-[#16D9F5] uppercase tracking-widest mb-3">
                Honest by design
              </p>
              <p className="text-slate-300 text-sm leading-relaxed mb-4">
                Some sources require special access, in-country infrastructure, authentication or custom adapters.
                StatuteProof documents these limitations instead of hiding them.
                After onboarding, you can submit source review requests and add custom regulatory portals
                directly from your dashboard.
              </p>
              <div className="grid sm:grid-cols-3 gap-3">
                {[
                  { label: 'Geo-restricted sites',  note: 'Documented, not skipped' },
                  { label: 'JS-only portals',        note: 'Playwright or adapter flagged' },
                  { label: 'Auth-protected APIs',    note: 'Marked adapter_required' },
                ].map(({ label, note }) => (
                  <div key={label} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5">
                    <p className="text-xs font-medium text-white">{label}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{note}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex-shrink-0 flex flex-col items-center gap-2">
              <button
                onClick={() => document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' })}
                className="inline-flex items-center gap-2 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-bold px-6 py-3 rounded-xl text-sm transition-colors whitespace-nowrap"
              >
                Create pilot workspace
                <ArrowRight className="w-4 h-4" />
              </button>
              <p className="text-xs text-slate-500 text-center max-w-[200px]">
                Add sources from your dashboard after onboarding
              </p>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}

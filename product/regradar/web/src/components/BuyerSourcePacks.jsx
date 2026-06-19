import { ArrowRight, Layers3 } from 'lucide-react'

// coverage: 'strong' | 'good' | 'partial' | 'limited'
const PACKS = [
  {
    profile: 'VASP / Crypto',
    bestFor: 'Exchanges, brokers, custodians, token projects and VASP compliance teams',
    coverage: 'strong',
    layers: [
      { text: 'VARA rulebooks, revision updates and selected official listings', status: 'active' },
      { text: 'VARA Virtual Asset regulations and compliance rulebook PDFs', status: 'active' },
      { text: 'UAE FIU public sources excluding circulars, AML/CFT laws and typology reports', status: 'active' },
      { text: 'DIFC Laws covering digital asset activity', status: 'active' },
      { text: 'CBUAE Payment Token Services Regulation', status: 'active' },
    ],
    caveat: null,
  },
  {
    profile: 'Payments & Fintech',
    bestFor: 'Payment firms, stored value providers, fintech operators and compliance advisers',
    coverage: 'strong',
    layers: [
      { text: 'CBUAE regulations, notices and supervisory materials', status: 'active' },
      { text: 'UAE FIU AML/CFT publications and laws; circulars remain candidate', status: 'active' },
      { text: 'UAE Ministry of Finance policy updates', status: 'active' },
      { text: 'UAE Legislation Portal federal law updates', status: 'pending' },
    ],
    caveat: 'FTA clarifications require item-level review before activation.',
  },
  {
    profile: 'DIFC / DFSA',
    bestFor: 'DIFC regulated firms, funds, advisers, law firms and compliance consultants',
    coverage: 'strong',
    layers: [
      { text: 'DIFC Laws and Regulations — selected legal database sources', status: 'active' },
      { text: 'DIFC Data Protection — Commissioner, guidance and enforcement', status: 'active' },
      { text: 'DFSA Annual Reports and Annual AML Reports', status: 'active' },
      { text: 'DFSA consultation papers and enforcement decisions', status: 'active' },
      { text: 'DFSA Rulebook modules (Thomson Reuters platform)', status: 'active' },
    ],
    caveat: null,
  },
  {
    profile: 'ADGM / FSRA',
    bestFor: 'ADGM regulated firms, funds, securities teams and regulatory advisers',
    coverage: 'strong',
    layers: [
      { text: 'ADGM FSRA rules, regulations and guidance', status: 'active' },
      { text: 'ADGM FSRA supervision circulars and regulatory alerts', status: 'active' },
      { text: 'ADGM public consultations and waivers register', status: 'active' },
      { text: 'ADGM Registration Authority circulars', status: 'active' },
      { text: 'ADGM FSRA enforcement actions and listing authority rules', status: 'active' },
    ],
    caveat: 'FSRA rulebook on Thomson Reuters platform is not separately monitored — content is captured through ADGM official sources.',
  },
  {
    profile: 'AML / FIU',
    bestFor: 'MLROs, AML consultants, onboarding teams and regulated financial firms',
    coverage: 'strong',
    layers: [
      { text: 'UAE FIU publications hub; circulars remain candidate', status: 'active' },
      { text: 'UAE FIU typology reports and knowledge centre', status: 'active' },
      { text: 'UAE FIU AML/CFT laws and related decisions', status: 'active' },
      { text: 'Executive Office for AML/CFT — laws and news', status: 'active' },
      { text: 'Selected SCA, CBUAE and DFSA AML/CFT guidance', status: 'active' },
    ],
    caveat: null,
  },
  {
    profile: 'Tax / Corporate',
    bestFor: 'Finance teams, tax advisers, corporate service providers and legal teams',
    coverage: 'partial',
    layers: [
      { text: 'UAE Ministry of Finance policy updates', status: 'active' },
      { text: 'UAE Legislation Portal federal law updates', status: 'pending' },
      { text: 'FTA — all tax legislation listing', status: 'pending' },
      { text: 'FTA — VAT guides, references and clarifications', status: 'pending' },
      { text: 'FTA — Corporate Tax guides and media centre', status: 'pending' },
    ],
    caveat: 'FTA sub-pages are public candidates, but the current extraction returns nav-shell/title-only content. They are not counted as fresh-alert eligible until item-level extraction passes proof and baseline gates.',
  },
  {
    profile: 'Data Protection',
    bestFor: 'Privacy teams, DIFC/ADGM firms, legal teams and data protection leads',
    coverage: 'good',
    layers: [
      { text: 'DIFC Commissioner of Data Protection — guidance and enforcement', status: 'active' },
      { text: 'ADGM Office of Data Protection — regulations and guidance index', status: 'active' },
      { text: 'ADGM Data Protection Regulations 2021 (updated PDF)', status: 'active' },
      { text: 'UAE federal PDPL (TDRA / UAE Data Office)', status: 'geo_blocked' },
    ],
    caveat: 'DIFC and ADGM data protection sources are fresh-alert eligible where proof-backed. UAE federal PDPL site (TDRA) is geo-IP restricted from outside the UAE — documented, not hidden.',
  },
]

const COVERAGE_CONFIG = {
  strong:  { label: 'Strong selected-source', badge: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300', bar: 'bg-emerald-400', width: 'w-[92%]' },
  good:    { label: 'Good selected-source',   badge: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',         bar: 'bg-cyan-400',    width: 'w-[72%]' },
  partial: { label: 'Partial selected-source', badge: 'border-amber-400/25 bg-amber-400/10 text-amber-300',     bar: 'bg-amber-400',   width: 'w-[50%]' },
  limited: { label: 'Limited selected-source', badge: 'border-rose-400/25 bg-rose-400/10 text-rose-300',        bar: 'bg-rose-400',    width: 'w-[25%]' },
}

const LAYER_DOT = {
  active:      'bg-emerald-400',
  roadmap:     'bg-amber-400',
  pending:     'bg-amber-400',
  out_of_scope:'bg-slate-600',
  geo_blocked: 'bg-rose-400',
}

const LAYER_TEXT = {
  active:      'text-slate-300',
  roadmap:     'text-slate-400 italic',
  pending:     'text-slate-400',
  out_of_scope:'text-slate-500 line-through decoration-slate-700',
  geo_blocked: 'text-rose-400/80',
}

const LAYER_SUFFIX = {
  roadmap:     ' — roadmap',
  pending:     ' — pending item review',
  out_of_scope:' — outside current scope',
  geo_blocked: ' — geo-restricted',
}

export default function BuyerSourcePacks({ onCreateWorkspace }) {
  return (
    <section className="bg-[#07111F] py-20" id="source-packs">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        <div className="mb-12 max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <Layers3 className="h-4 w-4" />
            Source packs by licence type
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white">
            What's monitored for your regulatory profile
          </h2>
          <p className="text-slate-400">
            Each pack shows exactly which sources are fresh-alert eligible, which are on the roadmap,
            and where gaps exist — before you commit to a pilot.
          </p>
        </div>

        {/* Legend */}
        <div className="mb-6 flex flex-wrap items-center gap-4 text-xs text-slate-500">
          <span className="font-semibold uppercase tracking-wide">Key:</span>
          {[
            ['bg-emerald-400', 'Fresh-alert eligible'],
            ['bg-amber-400',   'Roadmap / pending'],
            ['bg-slate-600',   'Outside current scope'],
            ['bg-rose-400',    'Geo-restricted'],
          ].map(([dot, label]) => (
            <span key={label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${dot}`} />
              {label}
            </span>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {PACKS.map(pack => {
            const cfg = COVERAGE_CONFIG[pack.coverage]
            return (
              <article
                key={pack.profile}
                className="flex flex-col rounded-xl border border-slate-800 bg-[#0A1628] p-5 shadow-[0_18px_48px_rgba(0,0,0,0.24)]"
              >
                {/* Header */}
                <div className="mb-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-white">{pack.profile}</h3>
                    <span className={`flex-shrink-0 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${cfg.badge}`}>
                      {cfg.label}
                    </span>
                  </div>
                  {/* Coverage bar */}
                  <div className="mb-2 h-1 w-full rounded-full bg-slate-800">
                    <div className={`h-1 rounded-full ${cfg.bar} ${cfg.width} transition-all`} />
                  </div>
                  <p className="text-xs leading-relaxed text-slate-500">
                    <span className="font-semibold text-slate-400">Best for:</span> {pack.bestFor}
                  </p>
                </div>

                {/* Source layers */}
                <div className="mb-4 flex-1">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Source layers
                  </p>
                  <ul className="space-y-2">
                    {pack.layers.map(layer => (
                      <li key={layer.text} className="flex gap-2 text-xs leading-relaxed">
                        <span className={`mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full ${LAYER_DOT[layer.status] || 'bg-slate-600'}`} />
                        <span className={LAYER_TEXT[layer.status] || 'text-slate-300'}>
                          {layer.text}
                          {LAYER_SUFFIX[layer.status] ? (
                            <span className="text-slate-500">{LAYER_SUFFIX[layer.status]}</span>
                          ) : null}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Caveat note */}
                {pack.caveat && (
                  <div className="mb-4 rounded-lg border border-amber-400/15 bg-amber-400/5 px-3 py-2 text-[11px] leading-snug text-amber-200/80">
                    {pack.caveat}
                  </div>
                )}

                <button
                  type="button"
                  onClick={onCreateWorkspace}
                  className="inline-flex items-center justify-between gap-2 rounded-lg border border-cyan-400/25 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50 hover:bg-cyan-400/15"
                >
                  Get source readiness report for this profile
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </article>
            )
          })}
        </div>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/45 p-4 text-sm leading-relaxed text-slate-400">
          Source packs show the monitoring scope per licence type. Coverage ratings reflect the current number of
          active sources — not regulatory significance. Roadmap and pending sources are not delivered to clients
          until they pass proof-backed baseline checks. Geo-restricted sources are documented, not hidden.
        </div>
      </div>
    </section>
  )
}

import { ArrowRight, Layers3 } from 'lucide-react'

const PACKS = [
  {
    profile: 'VASP / Crypto',
    bestFor: 'Exchanges, brokers, custodians, token projects and VASP compliance teams',
    layers: [
      'VARA rulebooks and publications',
      'AML/CFT and sanctions sources',
      'UAE FIU publications',
      'relevant DIFC/ADGM digital asset materials',
    ],
  },
  {
    profile: 'Payments & Fintech',
    bestFor: 'Payment firms, stored value providers, fintech operators and compliance advisers',
    layers: [
      'CBUAE payments and rulebook materials',
      'AML/CFT guidance',
      'FTA / corporate tax updates',
      'UAE legislation layers',
    ],
  },
  {
    profile: 'DIFC / DFSA',
    bestFor: 'DIFC regulated firms, funds, advisers, law firms and compliance consultants',
    layers: [
      'DFSA rulebook remediation before activation',
      'DFSA consultation papers under validation',
      'DIFC Laws',
      'DIFC Data Protection guidance',
    ],
  },
  {
    profile: 'ADGM / FSRA',
    bestFor: 'ADGM regulated firms, funds, securities teams and regulatory advisers',
    layers: [
      'ADGM / FSRA main source readiness-supported with caveats',
      'FSRA rulebook outside readiness-supported scope until checks clear',
      'FSRA circulars under validation',
      'ADGM Data Protection guidance',
    ],
  },
  {
    profile: 'AML / FIU',
    bestFor: 'MLROs, AML consultants, onboarding teams and regulated financial firms',
    layers: [
      'UAE FIU publications',
      'Executive Office / sanctions',
      'Ministry of Economy AML/DNFBP guidance',
      'CBUAE AML/CFT materials',
    ],
  },
  {
    profile: 'Tax / Corporate',
    bestFor: 'Finance teams, tax advisers, corporate service providers and legal teams',
    layers: [
      'FTA public clarifications',
      'FTA guides',
      'Ministry of Finance tax updates',
      'UAE legislation layers',
    ],
  },
  {
    profile: 'Data Protection',
    bestFor: 'Privacy teams, DIFC/ADGM firms, legal teams and data protection leads',
    layers: [
      'DIFC Data Protection Commissioner materials',
      'ADGM Office of Data Protection guidance',
      'UAE Data Office / PDPL materials under validation',
    ],
  },
]

const STATUSES = [
  ['Readiness-supported', 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'],
  ['Under validation', 'border-amber-400/25 bg-amber-400/10 text-amber-300'],
  ['Needs remediation', 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200'],
]

export default function BuyerSourcePacks({ onCreateWorkspace }) {
  return (
    <section className="bg-[#07111F] py-20" id="source-packs">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <Layers3 className="h-4 w-4" />
            Buyer source packs
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white">
            Built around your regulatory profile
          </h2>
          <p className="text-slate-400">
            StatuteProof maps official source layers by licence type, then activates only sources that clear readiness checks.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {PACKS.map(pack => (
            <article
              key={pack.profile}
              className="flex min-h-[330px] flex-col rounded-xl border border-slate-800 bg-[#0A1628] p-5 shadow-[0_18px_48px_rgba(0,0,0,0.24)]"
            >
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white">{pack.profile}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  <span className="font-semibold text-slate-400">Best for:</span> {pack.bestFor}
                </p>
              </div>

              <div className="mb-5 flex-1">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Source layers
                </p>
                <ul className="space-y-2.5">
                  {pack.layers.map(layer => (
                    <li key={layer} className="flex gap-2 text-sm leading-relaxed text-slate-300">
                      <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#16D9F5]" />
                      <span>{layer}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                {STATUSES.map(([label, classes]) => (
                  <span key={label} className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${classes}`}>
                    {label}
                  </span>
                ))}
              </div>

              <button
                type="button"
                onClick={onCreateWorkspace}
                className="inline-flex items-center justify-between gap-2 rounded-lg border border-cyan-400/25 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50 hover:bg-cyan-400/15"
              >
                Build this source profile
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </article>
          ))}
        </div>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/45 p-4 text-sm leading-relaxed text-slate-400">
          Source packs are maps for buyer scoping. They do not imply every listed source layer is ready for monitoring.
        </div>
      </div>
    </section>
  )
}

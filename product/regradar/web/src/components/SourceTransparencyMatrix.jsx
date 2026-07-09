import { ArrowRight, FileSearch, ShieldCheck } from 'lucide-react'

const MATRIX_ROWS = [
  {
    category: 'Central bank / financial regulation',
    sourceCount: '25 fresh-alert eligible',
    statusTone: 'active',
    whatWeMonitor: 'CBUAE rulebook modules (AML/CFT, Consumer Protection, Open Finance, Payments, Risk Management), licensing updates, policy notices',
    limitation: null,
    whatThisMeans: 'CBUAE rule and guidance changes are tracked across individual rulebook modules — not just the main page.',
  },
  {
    category: 'Virtual assets (VARA)',
    sourceCount: '3 fresh-alert eligible',
    statusTone: 'active',
    whatWeMonitor: 'VARA licensing rules, selected official notices, rulebook PDFs, revision update history',
    limitation: null,
    whatThisMeans: 'VARA rulebook updates and selected official source changes are tracked; regulatory notices/enforcement pages still need adapter validation.',
  },
  {
    category: 'DIFC / DFSA',
    sourceCount: '21 fresh-alert eligible across DIFC/DFSA',
    statusTone: 'active',
    whatWeMonitor: 'DIFC laws, data protection, DFSA rulebook modules, consultation papers, enforcement decisions and annual reports',
    limitation: null,
    whatThisMeans: 'Selected DIFC/DFSA source monitoring covers laws, data protection, and DFSA listing sources; static detail pages remain evidence-library only.',
  },
  {
    category: 'ADGM / FSRA',
    sourceCount: '9 fresh-alert eligible',
    statusTone: 'active',
    whatWeMonitor: 'ADGM FSRA rules, guidance, waivers, supervision circulars, public consultations, Registration Authority circulars, data protection, enforcement',
    limitation: 'FSRA rulebook on the Thomson Reuters platform has restricted external access. The dedicated regulatory-alerts page is a candidate pending selector remediation.',
    whatThisMeans: 'ADGM regulatory scope is well covered through official ADGM pages, with gaps disclosed upfront instead of counted as active.',
  },
  {
    category: 'AML / FIU / sanctions',
    sourceCount: 'Selected-source AML depth',
    statusTone: 'active',
    whatWeMonitor: 'UAE FIU public sources excluding circulars, publications hub, typology reports, AML/CFT laws; Executive Office for AML/CFT (EOCN) laws and news; selected UAE CMA and CBUAE AML guidance',
    limitation: null,
    whatThisMeans: 'Selected-source AML monitoring is strong in some families, but FIU circulars and broader UAE CMA coverage is in progress.',
  },
  {
    category: 'Tax / corporate',
    sourceCount: 'FTA strong; MoF narrow',
    statusTone: 'partial',
    whatWeMonitor: 'Ministry of Finance publications and direct FTA tax PDFs. Broader FTA listing pages remain candidate sources.',
    limitation: 'Five FTA sub-pages failed 2026-06-18 no-save checks with nav-shell/title-only extraction. They need item-level extraction before activation.',
    whatThisMeans: 'FTA direct PDF monitoring is strong, while MoF remains narrow and federal legislation/gazette sources remain remediation or research.',
  },
  {
    category: 'Data protection',
    sourceCount: 'Selected-source depth',
    statusTone: 'caveat',
    whatWeMonitor: 'DIFC Commissioner of Data Protection, DIFC DP guidance and enforcement, ADGM Office of Data Protection, ADGM DP regulations and guidance index',
    limitation: 'UAE federal PDPL (TDRA / uaedp.gov.ae) is geo-IP restricted from outside the UAE — not currently monitorable.',
    whatThisMeans: 'DIFC and ADGM data protection are monitored through proof-backed sources. UAE federal PDPL access remains geo-restricted and is disclosed before any pilot.',
  },
  {
    category: 'Legislation / gazettes',
    sourceCount: '0 fresh-alert eligible',
    statusTone: 'caveat',
    whatWeMonitor: 'No MoJ/UAE legislation/gazette source is fresh-alert eligible today. Related Ministry of Economy documents are separate AML/DNFBP support sources.',
    limitation: 'Official Gazette (Al-Jaridah Al-Rasmiah) and UAE e-Laws Portal (elaws.moj.gov.ae) are geo-restricted outside the UAE.',
    whatThisMeans: 'Federal legislation/gazette monitoring is not sold as ready until an official accessible route passes proof and baseline gates.',
  },
]

const BADGE_STYLES = {
  active: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
  caveat: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',
  partial: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
}

const BADGE_LABELS = {
  active: 'Fresh-alert eligible',
  caveat: 'Active with caveats — see detail',
  partial: 'Partially active — geo-restricted sources not available',
}

function StatusBadge({ tone }) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold leading-snug ${BADGE_STYLES[tone] || BADGE_STYLES.caveat}`}>
      {BADGE_LABELS[tone] || tone}
    </span>
  )
}

export default function SourceTransparencyMatrix({ onCreateWorkspace }) {
  return (
    <section className="bg-[#0A1628] py-20" id="source-transparency-matrix">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 grid gap-8 lg:grid-cols-[1fr_360px] lg:items-end">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
              <FileSearch className="h-4 w-4" />
              What we monitor
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white">
              Which regulators. Which sources. What you get.
            </h2>
            <p className="max-w-3xl text-slate-400">
              Every sector below shows exactly which official sources are in scope, what content is configured for monitoring, and any known limitations — disclosed before activation.
            </p>
          </div>

          <div className="rounded-xl border border-cyan-400/20 bg-slate-950/45 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
              Pilot transparency
            </div>
            <p className="text-sm leading-relaxed text-slate-400">
              Every pilot includes a source-scope report showing which sources are fresh-alert eligible, which have caveats, and which are outside current scope.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#07111F] shadow-[0_20px_60px_rgba(0,0,0,0.28)]">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="border-b border-slate-800 bg-slate-950/60">
              <tr>
                {['Regulatory area', 'Sources', 'Status', 'What we monitor', 'What this means for you'].map(column => (
                  <th key={column} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MATRIX_ROWS.map(row => (
                <tr key={row.category} className="border-b border-slate-800/80 last:border-0">
                  <td className="px-4 py-4 align-top font-semibold text-slate-100 whitespace-nowrap">
                    {row.category}
                  </td>
                  <td className="px-4 py-4 align-top text-slate-400 text-xs">
                    {row.sourceCount}
                  </td>
                  <td className="px-4 py-4 align-top">
                    <div className="flex flex-col gap-2">
                      <StatusBadge tone={row.statusTone} />
                      {row.limitation && (
                        <p className="text-[11px] text-slate-500 leading-snug max-w-[200px]">
                          {row.limitation}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 align-top text-slate-400 text-xs max-w-[220px]">
                    {row.whatWeMonitor}
                  </td>
                  <td className="px-4 py-4 align-top text-slate-300 text-xs max-w-[220px]">
                    {row.whatThisMeans}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-8 rounded-2xl border border-cyan-400/20 bg-slate-950/55 p-6 sm:p-7">
          <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <h3 className="text-2xl font-bold text-white">
                Start with your UAE source profile
              </h3>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">
                Create a workspace to save your licence profile, map the official sources that matter for your firm, and review which sources are active before any pilot.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
              <button
                type="button"
                onClick={onCreateWorkspace}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-5 py-2.5 text-sm font-semibold text-[#07111F] transition-colors hover:bg-[#11c2db]"
              >
                Create workspace to review your source profile
                <ArrowRight className="h-4 w-4" />
              </button>
              <a
                href="#sample-brief"
                className="inline-flex items-center justify-center rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
              >
                See sample brief
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

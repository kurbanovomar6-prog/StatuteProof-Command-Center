import { ArrowRight, FileSearch, ShieldCheck } from 'lucide-react'

const MATRIX_ROWS = [
  {
    category: 'Central bank / financial regulation',
    sourceCount: '25 fresh-alert eligible',
    statusTone: 'active',
    whatWeMonitor: 'CBUAE rulebook modules (AML/CFT, consumer protection, Open Finance, payments, stored value, prudential risk), rulebook-wide revision updates',
    limitation: 'The main centralbank.ae domain is geo-IP filtered from outside the UAE — monitoring runs on the rulebook subdomain (rulebook.centralbank.ae).',
    whatThisMeans: 'CBUAE rule and guidance changes are tracked across individual rulebook modules — not just the main page.',
  },
  {
    category: 'Virtual assets (VARA)',
    sourceCount: '3 fresh-alert eligible of 5 enabled',
    statusTone: 'active',
    whatWeMonitor: 'VARA rulebook revision updates, news/circulars/regulatory publications, enforcement notices',
    limitation: 'Public register and the regulatory notices index are enabled but pending validation. Static rulebook PDFs are evidence snapshots, not change-monitored.',
    whatThisMeans: 'VARA rulebook and enforcement changes are tracked through selected official sources — this is not complete VARA coverage.',
  },
  {
    category: 'DIFC / DFSA',
    sourceCount: '21 fresh-alert eligible across DIFC/DFSA',
    statusTone: 'active',
    whatWeMonitor: 'DIFC laws, legal database, legal notices, data protection, AML/CFT and ESR pages; DFSA rulebook (official + Thomson Reuters modules incl. AML), consultations, enforcement, MLRO letters, annual reports',
    limitation: 'DFSA news hub, SEO letters and public register, plus the DIFC news hub and DIFC Courts directions, are enabled but pending validation.',
    whatThisMeans: 'Selected DIFC/DFSA source monitoring covers laws, rulebook, data protection and enforcement; pending sources are disclosed, not counted.',
  },
  {
    category: 'ADGM / FSRA',
    sourceCount: '9 fresh-alert eligible of 14 enabled',
    statusTone: 'active',
    whatWeMonitor: 'ADGM FSRA rules and regulations, guidance and policy statements, supervision circulars, financial/cyber crime prevention, Listing Authority rules, public consultations, ADGM Courts, data protection guidance',
    limitation: 'FSRA rulebook on the Thomson Reuters platform has restricted external access. Regulatory alerts, the waivers register and RA circulars are enabled as disclosed candidates.',
    whatThisMeans: 'ADGM regulatory scope is covered through official ADGM pages, with gaps disclosed upfront instead of counted as active.',
  },
  {
    category: 'AML / sanctions / FIU',
    sourceCount: 'Selected-source AML depth',
    statusTone: 'caveat',
    whatWeMonitor: 'EOCN / UAEIEC AML/CFT laws, news and UN sanctions/TFS updates; Ministry of Economy DNFBP AML suite (goAML, TFS, beneficial ownership); CBUAE AML/CFT rulebook; DFSA AML module and MLRO letters; UAE CMA AML/CFT page',
    limitation: 'The UAE FIU website (uaefiu.gov.ae) is geo-IP restricted from outside the UAE — no FIU source is fresh-alert eligible today.',
    whatThisMeans: 'AML monitoring runs through EOCN, CBUAE, MoE, DFSA and CMA official sources; the FIU access limitation is disclosed before any pilot.',
  },
  {
    category: 'Tax / corporate',
    sourceCount: 'MoF 7 fresh-alert; FTA candidate',
    statusTone: 'partial',
    whatWeMonitor: 'MoF publications, financial legislation, Corporate Tax, Domestic Minimum Top-up Tax, ESR, AEOI/FATCA/CRS, UAE financial framework. Six FTA listing sources are enabled and monitored ahead of the fresh-alert gate.',
    limitation: 'FTA listing sources remain candidate-stage until they pass the fresh-alert gate — no FTA source is counted as fresh-alert eligible today. Static FTA decision PDFs are evidence snapshots.',
    whatThisMeans: 'MoF tax-policy monitoring is proof-backed; FTA operational-tax alerting is disclosed as pending, not sold as ready.',
  },
  {
    category: 'Capital markets (UAE CMA)',
    sourceCount: '6 fresh-alert eligible',
    statusTone: 'active',
    whatWeMonitor: 'UAE CMA circulars/rules/procedures, regulations listing, AML/CFT, corporate governance, FATCA/CRS guidance, FinTech Regulatory Sandbox',
    limitation: 'Root portal and board-decisions listing are still being validated. The SCA→CMA site transition is under active watch; the circulars page was repointed to the new canonical URL in July 2026.',
    whatThisMeans: 'Selected CMA sources are proof-backed and monitored through the regulator’s site migration. The July 2026 SCA→CMA URL move was caught and re-verified; site migrations are monitored, though we do not promise every future URL change is captured — any miss is surfaced in the evidence log, not hidden.',
  },
  {
    category: 'Data protection',
    sourceCount: 'Selected-source depth',
    statusTone: 'caveat',
    whatWeMonitor: 'DIFC Commissioner of Data Protection, DIFC DP Regulation 10, guidance, supervision and enforcement; ADGM data protection guidance',
    limitation: 'UAE federal PDPL (TDRA / UAE Data Office) is not currently in monitored scope — no accessible fresh-alert route has been validated. The ADGM Office of Data Protection hub and TDRA media centre are enabled, pending validation.',
    whatThisMeans: 'DIFC and ADGM data protection are monitored through proof-backed sources. UAE federal PDPL is disclosed as not-yet-in-scope, before any pilot.',
  },
  {
    category: 'Legislation / gazettes',
    sourceCount: '0 fresh-alert eligible',
    statusTone: 'candidate',
    whatWeMonitor: 'MoJ media centre and news, plus the Dubai Legislation Portal laws search, are enabled as candidates pending validation. Related Ministry of Economy documents are separate AML/DNFBP support sources.',
    limitation: 'Official Gazette (Al-Jaridah Al-Rasmiah), UAE e-Laws Portal (elaws.moj.gov.ae), the UAE Legislation Portal and UAE Cabinet news are blocked from outside the UAE.',
    whatThisMeans: 'Federal legislation/gazette monitoring is not sold as ready until an official accessible route passes proof and baseline gates.',
  },
  {
    category: 'Markets / free zones / other federal',
    sourceCount: '0 fresh-alert eligible — candidates',
    statusTone: 'candidate',
    whatWeMonitor: 'DFM regulatory circulars, DMCC regulatory updates, JAFZA media centre, ICP news, TDRA media centre, MOCCAE media centre — all recently enabled as candidates',
    limitation: 'These sources are configured and monitored but not alert-eligible until they pass proof-backed baseline validation.',
    whatThisMeans: 'Free-zone and sector coverage is being expanded openly — candidate sources are disclosed here before they are ever sold as monitored.',
  },
]

const BADGE_STYLES = {
  active: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
  caveat: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',
  partial: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
  candidate: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
}

const BADGE_LABELS = {
  active: 'Fresh-alert eligible',
  caveat: 'Active with caveats — see detail',
  partial: 'Partially active — some sources blocked from outside the UAE',
  // A category with ZERO fresh-alert-eligible sources must never read as "active".
  candidate: 'Candidate — not yet fresh-alert eligible',
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

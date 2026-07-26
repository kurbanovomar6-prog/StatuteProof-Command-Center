import { ArrowRight, FileSearch, ShieldCheck } from 'lucide-react'

const MATRIX_ROWS = [
  {
    category: 'Central bank / financial regulation',
    sourceCount: '0 fresh-alert eligible — production access blocked',
    statusTone: 'remediation',
    whatWeMonitor: 'CBUAE rulebook modules (AML/CFT, consumer protection, Open Finance, payments, stored value, prudential risk) and rulebook-wide revision updates are configured — but not currently counted as monitored.',
    limitation: 'rulebook.centralbank.ae currently returns HTTP 403 to our production monitoring infrastructure on every fetch method (persistent since 11 July 2026). All 25 CBUAE sources are disclosed as in remediation and none is counted as fresh-alert eligible until access is restored and re-verified from production.',
    whatThisMeans: 'We do not count CBUAE sources we cannot reach from production. The configuration is ready; the access block is disclosed here instead of being papered over.',
  },
  {
    category: 'Virtual assets (VARA)',
    // 2026-07-25: 4 -> 3. The VARA Regulatory Notices and Enforcement Index was
    // promoted to fresh_alert on 2026-07-21 with no production baseline; that
    // promotion is reversed, so the honest count drops by one.
    sourceCount: '3 fresh-alert eligible of 6 enabled',
    statusTone: 'active',
    whatWeMonitor: 'VARA Compliance & Risk Management Rulebook full text (incl. AML/CFT Part III, promoted 18 July 2026 after two stable production runs), news/circulars/regulatory publications, enforcement notices',
    limitation: 'The 30-day rulebook revision-updates view is in remediation pending a production rebaseline (rulebook change coverage continues via the full-rulebook source). The public register is enabled but pending validation. Static rulebook PDFs are evidence snapshots, not change-monitored.',
    whatThisMeans: 'VARA rulebook and enforcement changes are tracked through selected official sources — this is not complete VARA coverage.',
  },
  {
    category: 'DIFC / DFSA',
    sourceCount: '11 fresh-alert eligible across DIFC/DFSA',
    statusTone: 'caveat',
    whatWeMonitor: 'DIFC legal database, legal notices, data protection, AML/CFT and ESR pages; DFSA rulebook on the Thomson Reuters platform (rulebook + AML/CTF module, the module promoted 18 July 2026 after passing production gates)',
    limitation: 'www.dfsa.ae currently returns HTTP 403 to our production monitoring infrastructure (persistent since 11 July 2026) — 10 DFSA-site sources (consultations, enforcement, MLRO letters, annual reports, laws/rules pages) are disclosed as in remediation and not counted. DFSA rulebook depth continues via dfsaen.thomsonreuters.com, which does work from production. The DIFC laws-and-regulations root listing is in remediation pending a production rebaseline review.',
    whatThisMeans: 'Selected DIFC/DFSA monitoring continues where production access is proven; DFSA-site sources blocked from production are disclosed here, not counted.',
  },
  {
    category: 'ADGM / FSRA',
    sourceCount: '9 fresh-alert eligible of 16 enabled',
    statusTone: 'active',
    whatWeMonitor: 'ADGM FSRA rules and regulations, guidance and policy statements, supervision circulars, financial/cyber crime prevention, Listing Authority rules, public consultations, ADGM Courts, data protection guidance',
    limitation: 'FSRA rulebook on the Thomson Reuters platform has restricted external access. Regulatory alerts, the waivers register and RA circulars are enabled as disclosed candidates.',
    whatThisMeans: 'ADGM regulatory scope is covered through official ADGM pages, with gaps disclosed upfront instead of counted as active.',
  },
  {
    category: 'AML / sanctions / FIU',
    sourceCount: 'Selected-source AML depth',
    statusTone: 'caveat',
    whatWeMonitor: 'EOCN / UAEIEC AML/CFT laws, news and UN sanctions/TFS updates; UAE CMA AML/CFT page; DFSA AML/CTF rulebook module (Thomson Reuters platform); VARA rulebook AML/CFT Part III',
    limitation: 'The UAE FIU website (uaefiu.gov.ae) is geo-IP restricted from outside the UAE — no FIU source is fresh-alert eligible today. The CBUAE AML/CFT rulebook sections and DFSA MLRO letters are in remediation because rulebook.centralbank.ae and www.dfsa.ae block our production monitoring infrastructure (HTTP 403 since 11 July 2026). The Ministry of Economy DNFBP AML suite is under source remediation — its earlier captures were a site-maintenance page, which our quality gate now rejects — and is not counted until re-baselined on real content.',
    whatThisMeans: 'AML monitoring runs through EOCN, CMA, the DFSA rulebook platform and the VARA rulebook; the FIU, CBUAE and DFSA-site access limitations and the MoE remediation are disclosed before any pilot, not discovered after it.',
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
    limitation: 'The circulars/rules/procedures page is in remediation: after the July 2026 SCA→CMA repoint, production runs are stuck comparing against the stale pre-repoint baseline until a production rebaseline is executed — disclosed, not counted. Root portal and board-decisions listing are still being validated.',
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
  // Neutral, not amber: "not yet eligible" must not read as "partially working".
  candidate: 'border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-secondary)]',
  // Access blocked from production — must read as "not currently delivered".
  remediation: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
}

const BADGE_LABELS = {
  active: 'Fresh-alert eligible',
  caveat: 'Active with caveats — see detail',
  partial: 'Partially active — some sources blocked from outside the UAE',
  // A category with ZERO fresh-alert-eligible sources must never read as "active".
  candidate: 'Candidate — not yet fresh-alert eligible',
  remediation: 'In remediation — access blocked from production; not counted',
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
    <section className="bg-[var(--bg-surface)] py-20" id="source-transparency-matrix">
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
            <p className="max-w-3xl text-[var(--text-secondary)]">
              Every sector below shows exactly which official sources are in scope, what content is configured for monitoring, and any known limitations — disclosed before activation.
            </p>
          </div>

          <div className="rounded-xl border border-cyan-400/20 bg-[var(--bg-navy)] p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
              Pilot transparency
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Every pilot includes a source-scope report showing which sources are fresh-alert eligible, which have caveats, and which are outside current scope.
            </p>
          </div>
        </div>

        <div className="min-w-0 overflow-x-auto rounded-xl border border-[var(--border-muted)] bg-[var(--bg-navy)] shadow-[0_20px_60px_rgba(0,0,0,0.28)]">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="border-b border-[var(--border-muted)] bg-[var(--bg-base)]">
              <tr>
                {['Regulatory area', 'Sources', 'Status', 'What we monitor', 'What this means for you'].map(column => (
                  <th key={column} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MATRIX_ROWS.map(row => (
                <tr key={row.category} className="border-b border-[var(--border-subtle)] last:border-0">
                  <td className="px-4 py-4 align-top font-semibold text-[var(--text-primary)] whitespace-nowrap">
                    {row.category}
                  </td>
                  <td className="px-4 py-4 align-top text-[var(--text-secondary)] text-xs">
                    {row.sourceCount}
                  </td>
                  <td className="px-4 py-4 align-top">
                    <div className="flex flex-col gap-2">
                      <StatusBadge tone={row.statusTone} />
                      {/* Trust-critical fine print: 12px minimum + AA-passing muted token. */}
                      {row.limitation && (
                        <p className="text-xs text-[var(--text-muted)] leading-snug max-w-[200px]">
                          {row.limitation}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 align-top text-[var(--text-secondary)] text-xs max-w-[220px]">
                    {row.whatWeMonitor}
                  </td>
                  <td className="px-4 py-4 align-top text-[var(--text-primary)] text-xs max-w-[220px]">
                    {row.whatThisMeans}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-8 rounded-2xl border border-cyan-400/20 bg-[var(--bg-navy)] p-6 sm:p-7">
          <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <h3 className="text-2xl font-bold text-white">
                Start with your UAE source profile
              </h3>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
                Create a workspace to save your licence profile, map the official sources that matter for your firm, and review which sources are active before any pilot.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
              <button
                type="button"
                onClick={onCreateWorkspace}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-[var(--ink)] transition-colors hover:bg-[var(--accent-hover)]"
              >
                Create workspace to review your source profile
                <ArrowRight className="h-4 w-4" />
              </button>
              <a
                href="#sample-brief"
                className="inline-flex items-center justify-center rounded-lg border border-[var(--border)] px-5 py-2.5 text-sm font-semibold text-[var(--text-secondary)] transition-colors hover:border-[var(--text-muted)] hover:text-white"
              >
                See a sample brief
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

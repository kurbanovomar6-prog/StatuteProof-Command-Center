import { ArrowRight } from 'lucide-react'

const ACTIVE_SOURCES = [
  { source: 'CBUAE Rulebook — revision updates',       publishes: 'Rulebook-wide revision history across CBUAE modules',                          note: 'Monitored on rulebook.centralbank.ae; the main centralbank.ae domain is geo-IP filtered from outside the UAE' },
  { source: 'CBUAE Rulebook — AML/CFT',                publishes: 'AML/CFT rulebook sections, document links, proliferation finance and TBML guidance', note: null },
  { source: 'CBUAE Rulebook — payments',               publishes: 'Payment Token Services, Retail Payment Services and Card Schemes, Stored Value Facilities, payment systems regulations', note: null },
  { source: 'CBUAE Rulebook — open finance + conduct', publishes: 'Open Finance Regulation, consumer protection, market conduct, SME customer protection', note: null },
  { source: 'CBUAE Rulebook — prudential risk',        publishes: 'Capital adequacy, market/operational/interest-rate risk, large exposures, model management, Islamic banks risk', note: null },
  { source: 'MoF publications + financial legislation', publishes: 'MoF publications and releases, financial legislation, UAE financial framework', note: null },
  { source: 'MoF tax policy pages',                     publishes: 'Corporate Tax, Domestic Minimum Top-up Tax, Economic Substance, AEOI/FATCA/CRS', note: 'FTA listing sources are enabled but remain candidate — see below' },
  { source: 'VARA Rulebook revision updates',          publishes: 'VARA rulebook module changes and revision history',                            note: null },
  { source: 'VARA News, Circulars and Publications',   publishes: 'VASP licensing news, circulars and regulatory publications',                   note: null },
  { source: 'VARA Enforcement Notices',                publishes: 'VASP enforcement actions and regulatory decisions',                            note: null },
  { source: 'ADGM FSRA Rules and Regulations',         publishes: 'FSRA rules, regulations, guidance and policy statements',                      note: null },
  { source: 'ADGM FSRA Supervision Circulars',         publishes: 'FSRA supervision circulars to regulated entities',                             note: null },
  { source: 'ADGM FSRA Financial + Cyber Crime',       publishes: 'FSRA financial and cyber crime prevention materials',                          note: null },
  { source: 'ADGM FSRA Listing Authority',             publishes: 'Listing Authority rules and guidance',                                         note: null },
  { source: 'ADGM Public Consultations',               publishes: 'FSRA consultation papers and policy proposals',                                note: null },
  { source: 'ADGM Courts',                             publishes: 'Courts legislation, procedures, forms, fees and guides',                       note: null },
  { source: 'ADGM Data Protection Guidance',           publishes: 'ADGM data protection guidance index',                                          note: 'Office of Data Protection hub is enabled, pending validation' },
  { source: 'EOCN / UAEIEC',                           publishes: 'AML/CFT laws and regulations, news, UN sanctions and TFS updates',             note: null },
  { source: 'DIFC Laws and Regulations',               publishes: 'DIFC legal database, laws and regulations, legal notices',                     note: null },
  { source: 'DIFC Data Protection',                    publishes: 'Commissioner materials, Regulation 10, guidance, supervision and enforcement', note: null },
  { source: 'DIFC Business — AML/CFT + ESR',           publishes: 'DIFC AML/CFT and economic substance pages',                                    note: null },
  { source: 'DFSA Rulebook',                           publishes: 'Official rulebook plus Thomson Reuters modules, including the AML module',     note: null },
  { source: 'DFSA Consultation Papers',                publishes: 'DFSA consultation papers — current',                                           note: null },
  { source: 'DFSA Enforcement',                        publishes: 'Published enforcement decisions and ongoing regulatory actions',               note: null },
  { source: 'DFSA Financial Crime + MLRO Letters',     publishes: 'Financial crime prevention notices, MLRO letters, innovation and testing licence updates', note: null },
  { source: 'DFSA Annual + AML Reports',               publishes: 'DFSA annual regulatory reports and annual AML reports',                        note: null },
  { source: 'Ministry of Economy — DNFBP AML',         publishes: 'AML, goAML registration, targeted financial sanctions, economic substance, auditing, business and competition regulation', note: null },
  { source: 'UAE CMA (formerly SCA)',                  publishes: 'Circulars/rules/procedures, regulations listing, AML/CFT, corporate governance, FATCA/CRS, fintech sandbox', note: 'Circulars page repointed to the CMA’s new canonical URL during the SCA→CMA site transition (July 2026)' },
]

const CAVEAT_SOURCES = [
  {
    source: 'UAE FIU (uaefiu.gov.ae)',
    why: 'The UAE FIU website is geo-IP restricted from outside the UAE and no FIU source is fresh-alert eligible today. Previously validated FIU pages are excluded from coverage claims until an accessible official route is re-verified. AML coverage continues through EOCN, CBUAE AML/CFT rulebook sections, Ministry of Economy DNFBP sources and DFSA/CMA AML sources.',
  },
  {
    source: 'FTA listing sources (tax.gov.ae)',
    why: 'Six FTA listing sources — all-tax legislation, Corporate Tax legislation, Corporate Tax and VAT guides, VAT public clarifications and the media centre — are enabled and monitored after a June 2026 extraction fix. They remain candidate-stage until they pass the same fresh-alert gate as other sources, so no FTA source is counted as fresh-alert eligible today. Static FTA decision PDFs are archived as evidence snapshots, not monitored for change.',
  },
  {
    source: 'UAE Capital Market Authority (UAE CMA)',
    why: 'UAE CMA has 6 proof-backed fresh-alert eligible sources, including the regulations listing and the circulars/rules/procedures page, which was repointed to the CMA’s new canonical URL during the SCA→CMA site transition in July 2026. The root portal and board-decisions listing are still being validated before we make broader capital-markets claims.',
  },
  {
    source: 'UAE Legislation Portal',
    why: 'This high-value federal legislation source is still being validated because access is currently blocked from outside the UAE. We do not sell it as monitored until there is a reliable, accessible route we have verified.',
  },
  {
    source: 'ADGM FSRA Rulebook (Thomson Reuters platform)',
    why: 'The ADGM FSRA rulebook on the Thomson Reuters platform (fsra.adgm.com) has restricted external access. FSRA regulatory content is captured through ADGM official sources such as rules and regulations, guidance notes, supervision circulars, and consultations. The dedicated regulatory-alerts page, the waivers register and Registration Authority circulars are enabled as disclosed candidates, pending validation.',
  },
]

const NOT_AVAILABLE_SOURCES = [
  {
    source: 'UAE FIU (uaefiu.gov.ae)',
    reason: 'Geo-IP restricted from outside the UAE. EOCN, CBUAE, Ministry of Economy and DFSA/CMA AML sources are monitored as alternatives.',
  },
  {
    source: 'CBUAE main domain (centralbank.ae)',
    reason: 'Geo-IP filtered from outside the UAE. The CBUAE rulebook subdomain (rulebook.centralbank.ae) is monitored instead — 25 fresh-alert eligible sources.',
  },
  {
    source: 'UAE Cabinet — news and decisions (uaecabinet.ae)',
    reason: 'Access blocked from outside the UAE.',
  },
  {
    source: 'UAE Official Gazette / Al-Jaridah Al-Rasmiah',
    reason: 'Access blocked from outside the UAE.',
  },
  {
    source: 'UAE e-Laws Portal (elaws.moj.gov.ae)',
    reason: 'Access blocked from outside the UAE.',
  },
  {
    source: 'UAE Data Office / TDRA (federal PDPL)',
    reason: 'Not currently in monitored scope — no accessible fresh-alert route has been validated. DIFC and ADGM data protection sources are monitored as alternatives.',
  },
]

const ROADMAP_SOURCES = [
  { source: 'FTA listing sources — fresh-alert promotion after candidate gate', profile: 'Tax advisers, corporate finance and legal teams' },
  { source: 'ADGM FSRA regulatory alerts, waivers register, RA circulars — enabled candidates', profile: 'ADGM regulated firms and securities teams' },
  { source: 'DFSA news hub, SEO letters, public register — enabled, pending validation', profile: 'DIFC regulated firms and advisers' },
  { source: 'VARA public register + regulatory notices index — enabled, pending validation', profile: 'VASPs and crypto compliance teams' },
  { source: 'DIFC news hub; DIFC Courts practice + registrar directions — enabled, pending validation', profile: 'DIFC firms, funds and law firms' },
  { source: 'MoJ media centre + news; Dubai Legislation Portal laws search — enabled, pending validation', profile: 'Legal and governance teams' },
  { source: 'DFM, DMCC, JAFZA, ICP, TDRA, MOCCAE — enabled, pending validation', profile: 'Listed companies, free-zone firms and sector teams' },
  { source: 'Insurance supervision; item-level sanctions screening list extraction', profile: 'Insurance, AML teams, VASPs, banks, payments firms' },
]

function StatusBadge({ tone, children }) {
  const styles = {
    active:   'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    caveat:   'border-cyan-400/20 bg-cyan-400/10 text-cyan-200',
    blocked:  'border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-secondary)]',
    roadmap:  'border-amber-400/20 bg-amber-400/10 text-amber-300',
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold ${styles[tone] || styles.blocked}`}>
      {children}
    </span>
  )
}

function SourceTable({ columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border-muted)] bg-[var(--bg-surface)]">
      <table className="w-full text-sm">
        <thead className="bg-[var(--bg-base)] border-b border-[var(--border-muted)]">
          <tr>
            {columns.map(column => (
              <th key={column.key} className="px-4 py-3 text-left text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.source} className="border-b border-[var(--border-subtle)] last:border-0">
              {columns.map(col => (
                <td key={col.key} className="px-4 py-3 align-top text-[var(--text-secondary)]">
                  {col.key === 'source'
                    ? <span className="font-medium text-[var(--text-primary)]">{row[col.key]}</span>
                    : row[col.key]
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Coverage({ onCreateWorkspace }) {
  return (
    <section className="py-20 bg-[var(--bg-navy)]" id="coverage">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Source transparency
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            What is monitored — and what is not
          </h2>
          <p className="text-[var(--text-secondary)] max-w-3xl mx-auto">
            StatuteProof discloses every source status before a pilot begins. Active sources have
            passed two proof-backed baseline runs. Sources with caveats are disclosed upfront.
            Access-blocked sources are documented — not hidden.
          </p>
          <p className="mt-3 text-sm text-[var(--text-secondary)] max-w-3xl mx-auto">
            <span className="font-semibold text-[var(--text-primary)]">Fresh-alert eligible</span> means a source we have
            reliably captured at least twice and can send you change alerts from.
          </p>
        </div>

        <div className="space-y-8">

          {/* Active sources */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Fresh-alert eligible coverage — {ACTIVE_SOURCES.length} grouped source layers</h3>
              <StatusBadge tone="active">Fresh-alert eligible</StatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source',    label: 'Source' },
                { key: 'publishes', label: 'What it covers' },
                { key: 'note',      label: 'Note' },
              ]}
              rows={ACTIVE_SOURCES.map(r => ({ ...r, note: r.note || '' }))}
            />
          </div>

          {/* Caveat sources */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Not separately monitored — covered via alternatives or pending review</h3>
              <StatusBadge tone="caveat">See note</StatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'why',    label: 'Why and what covers it instead' },
              ]}
              rows={CAVEAT_SOURCES}
            />
          </div>

          {/* Geo-blocked sources */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Access blocked from outside the UAE — not currently monitorable</h3>
              <StatusBadge tone="blocked">Not available</StatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'reason', label: 'Reason' },
              ]}
              rows={NOT_AVAILABLE_SOURCES}
            />
          </div>

          {/* Roadmap sources */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">On the validation track — enabled or planned, not yet alert-eligible</h3>
              <StatusBadge tone="roadmap">Pending / roadmap</StatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source',  label: 'Source' },
                { key: 'profile', label: 'Relevant for' },
              ]}
              rows={ROADMAP_SOURCES}
            />
          </div>

        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-muted)] rounded-xl p-6 mt-8 mb-6">
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            Source status reflects current technical accessibility — not regulatory significance.
            A source listed as access-blocked or pending does not reduce its legal importance.
            It means StatuteProof cannot currently monitor it reliably, and we document that
            before you rely on it.
          </p>
        </div>

        <div className="bg-[var(--bg-navy)] border border-cyan-400/20 rounded-xl p-6 text-center">
          <h3 className="text-white text-xl font-bold mb-2">Need to check a specific regulator or source?</h3>
          <p className="text-[var(--text-secondary)] text-sm mb-5">We'll review accessibility and scope before recommending a pilot configuration.</p>
          <button
            onClick={onCreateWorkspace}
            className="inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Get your free source readiness review <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </section>
  )
}

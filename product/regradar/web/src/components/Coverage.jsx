import { ArrowRight } from 'lucide-react'

const ACTIVE_SOURCES = [
  { source: 'CBUAE Main',                             publishes: 'Central bank notices, licensing and supervisory updates',                     note: null },
  { source: 'CBUAE Regulations',                      publishes: 'CBUAE regulations and standards listing',                                     note: 'Noise filter applied before alert delivery' },
  { source: 'CBUAE Rulebook — multiple modules',      publishes: 'AML/CFT, Consumer Protection, Open Finance, Payment Token, Risk Management',  note: null },
  { source: 'MoF + FTA direct tax PDFs',               publishes: 'MoF financial publications plus direct FTA tax PDF decisions, guides and clarifications', note: 'Broader FTA portal/listing extraction remains roadmap' },
  { source: 'VARA Main + Rulebook revision updates',  publishes: 'VASP licensing, rulebook updates, guidance notes, revision history',          note: null },
  { source: 'VARA Enforcement Notices',               publishes: 'VASP enforcement actions and regulatory decisions',                            note: null },
  { source: 'VARA Rulebook PDFs (6 modules)',         publishes: 'Compliance, Technology, VA Issuance, Broker-Dealer, Lending, Regulations',    note: null },
  { source: 'ADGM FSRA — Rules, Guidance, Waivers',  publishes: 'ADGM regulations, FSRA guidance notes, waivers and modifications register',   note: null },
  { source: 'ADGM FSRA Supervision Circulars',        publishes: 'FSRA supervision circulars to regulated entities',                            note: null },
  { source: 'ADGM Public Consultations',              publishes: 'FSRA consultation papers and policy proposals',                               note: null },
  { source: 'ADGM Registration Authority Circulars',  publishes: 'RA circulars on corporate, commercial and registration matters',               note: null },
  { source: 'ADGM FSRA Enforcement',                  publishes: 'FSRA enforcement actions and regulatory alerts',                               note: null },
  { source: 'ADGM Data Protection (hub + guidance)',  publishes: 'ADGM Data Protection Regulations 2021, guidance index, enforcement',          note: null },
  { source: 'UAE FIU Publications Hub',               publishes: 'FIU publications, typology reports, knowledge centre and public notices',      note: 'FIU circulars page is still being validated' },
  { source: 'UAE FIU AML/CFT Laws and Decisions',     publishes: 'AML/CFT laws and related Cabinet/Ministerial decisions',                      note: null },
  { source: 'Executive Office for AML/CFT',           publishes: 'AML/CFT laws, regulations and news from the EOCN',                           note: null },
  { source: 'DIFC Laws and Regulations',              publishes: 'DIFC legal database — laws, data protection rules',                           note: null },
  { source: 'DIFC Data Protection (Commissioner)',    publishes: 'DIFC DP Commissioner materials, supervision, guidance and enforcement',       note: null },
  { source: 'DFSA Rulebook Modules',                  publishes: 'DFSA rulebook modules via Thomson Reuters platform',                          note: null },
  { source: 'DFSA Consultation Papers',               publishes: 'DFSA consultation papers — current and closed',                              note: null },
  { source: 'DFSA Enforcement Decisions + Actions',   publishes: 'Published enforcement decisions and ongoing regulatory actions',               note: null },
  { source: 'DFSA Annual Reports',                    publishes: 'DFSA annual regulatory reports',                                              note: null },
  { source: 'DFSA Annual AML Reports',                publishes: 'DFSA annual AML and enforcement reports',                                     note: null },
  { source: 'UAE Ministry of Economy',                publishes: 'Commercial licensing and AML policy updates',                                 note: null },
  { source: 'UAE CMA selected sources',                publishes: 'Limited UAE CMA proof-backed sources, including sandbox and selected guidance',  note: 'Broader UAE CMA regulations listing is still being validated' },
]

const CAVEAT_SOURCES = [
  {
    source: 'UAE FIU Homepage',
    why: 'The FIU homepage is a landing page with no document list, so there is nothing to alert on. FIU annual reports, press releases, typology reports, AML/CFT laws, and the publications hub have fresh-alert coverage; the FIU circulars page is still being validated because we could not yet extract reliable text from it.',
  },
  {
    source: 'FTA Main Portal and listing pages (tax.gov.ae)',
    why: '25 direct official FTA tax PDFs are fresh-alert eligible. The FTA main portal and its listing/sub-pages are not separately counted as fresh-alert because we could not yet extract reliable text for each item on those pages, so they are still being validated.',
  },
  {
    source: 'UAE Capital Market Authority (UAE CMA)',
    why: 'UAE CMA has 6 active proof-backed fresh-alert eligible sources. Broader UAE CMA coverage is actively expanding and is still being validated before we make broader capital-markets claims.',
  },
  {
    source: 'UAE Legislation Portal',
    why: 'This high-value federal legislation source is still being validated because access is currently blocked. We do not sell it as monitored until there is a reliable, accessible route we have verified.',
  },
  {
    source: 'ADGM FSRA Rulebook (Thomson Reuters platform)',
    why: 'The ADGM FSRA rulebook on the Thomson Reuters platform (fsra.adgm.com) has restricted external access. FSRA regulatory content is captured through ADGM official sources such as rules and regulations, guidance notes, supervision circulars, enforcement, and consultations. The dedicated regulatory-alerts page is still being validated.',
  },
]

const NOT_AVAILABLE_SOURCES = [
  {
    source: 'UAE Official Gazette / Al-Jaridah Al-Rasmiah',
    reason: 'Access blocked from outside the UAE.',
  },
  {
    source: 'UAE e-Laws Portal (elaws.moj.gov.ae)',
    reason: 'Access blocked from outside the UAE.',
  },
  {
    source: 'UAE Data Office / TDRA (uaedp.gov.ae)',
    reason: 'Access blocked from outside the UAE. DIFC and ADGM data protection sources are monitored as alternatives.',
  },
]

const ROADMAP_SOURCES = [
  { source: 'FTA item-level portal/listing extraction beyond direct PDFs', profile: 'Tax advisers, corporate finance and legal teams' },
  { source: 'ADGM FSRA dedicated regulatory-alerts listing', profile: 'ADGM regulated firms and securities teams' },
  { source: 'DMCC regulatory notices',            profile: 'DMCC member firms and commodity traders' },
  { source: 'Insurance Authority supervision',    profile: 'Insurance, insurtech, law firms' },
  { source: 'UAE sanctions / AML screening list', profile: 'AML teams, VASPs, banks, payments firms' },
]

function StatusBadge({ tone, children }) {
  const styles = {
    active:   'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    caveat:   'border-cyan-400/20 bg-cyan-400/10 text-cyan-200',
    blocked:  'border-slate-500/25 bg-slate-500/10 text-slate-300',
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
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0A1628]">
      <table className="w-full text-sm">
        <thead className="bg-slate-950/40 border-b border-slate-800">
          <tr>
            {columns.map(column => (
              <th key={column.key} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.source} className="border-b border-slate-800/80 last:border-0">
              {columns.map(col => (
                <td key={col.key} className="px-4 py-3 align-top text-slate-400">
                  {col.key === 'source'
                    ? <span className="font-medium text-slate-100">{row[col.key]}</span>
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
    <section className="py-20 bg-[#07111F]" id="coverage">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Source transparency
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            What is monitored — and what is not
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto">
            StatuteProof discloses every source status before a pilot begins. Active sources have
            passed two proof-backed baseline runs. Sources with caveats are disclosed upfront.
            Access-blocked sources are documented — not hidden.
          </p>
          <p className="mt-3 text-sm text-slate-400 max-w-3xl mx-auto">
            <span className="font-semibold text-slate-200">Fresh-alert eligible</span> means a source we have
            reliably captured at least twice and can send you change alerts from.
          </p>
        </div>

        <div className="space-y-8">

          {/* Active sources */}
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Source monitoring examples — {ACTIVE_SOURCES.length} sources</h3>
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
              <h3 className="font-bold text-white">On the monitoring roadmap — not yet active</h3>
              <StatusBadge tone="roadmap">Roadmap</StatusBadge>
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

        <div className="bg-[#0A1628] border border-slate-800 rounded-xl p-6 mt-8 mb-6">
          <p className="text-sm text-slate-400 leading-relaxed">
            Source status reflects current technical accessibility — not regulatory significance.
            A source listed as access-blocked or pending does not reduce its legal importance.
            It means StatuteProof cannot currently monitor it reliably, and we document that
            before you rely on it.
          </p>
        </div>

        <div className="bg-slate-950/50 border border-cyan-400/20 rounded-xl p-6 text-center">
          <h3 className="text-white text-xl font-bold mb-2">Need to check a specific regulator or source?</h3>
          <p className="text-slate-400 text-sm mb-5">We'll review accessibility and scope before recommending a pilot configuration.</p>
          <button
            onClick={onCreateWorkspace}
            className="inline-flex items-center gap-2 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Get a free source readiness review <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </section>
  )
}

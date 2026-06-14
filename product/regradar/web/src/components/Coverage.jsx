import { ArrowRight } from 'lucide-react'

const READINESS_SUPPORTED_SOURCES = [
  { source: 'CBUAE Main', publishes: 'Central bank notices, licensing and supervisory material', extraction: 'HTML structured' },
  { source: 'CBUAE Regulations', publishes: 'CBUAE regulations listing and standards', extraction: 'HTML structured; counter-change noise filter needed before alert delivery' },
  { source: 'UAE Ministry of Finance', publishes: 'Financial policy notices and public ministry publications', extraction: 'HTML structured + PDF text' },
  { source: 'VARA Main', publishes: 'VASP licensing, rulebook updates, guidance notes', extraction: 'HTML / PDF' },
  { source: 'VARA Enforcement Notices', publishes: 'VASP enforcement actions and regulatory decisions', extraction: 'HTML structured' },
  { source: 'ADGM FSRA Main', publishes: 'ADGM regulations, FSRA notices, licensing updates', extraction: 'HTML structured; low character count caveat' },
  { source: 'UAE FIU Circulars', publishes: 'FIU publications, circulars and public notices', extraction: 'HTML structured' },
  { source: 'UAE Legislation Portal', publishes: 'Federal laws and decrees', extraction: 'HTML structured; aggregate page changes require adapter review for item-level alerts' },
  { source: 'UAE Ministry of Economy', publishes: 'Commercial licensing, AML policy', extraction: 'HTML structured' },
]

const REMEDIATION_SOURCES = [
  {
    source: 'DFSA Rulebook',
    issue: 'Current extraction reaches the DFSA navigation shell rather than unique regulatory page content.',
    remediation: 'Add a precise wait selector or adapter, then rerun evidence validation.',
  },
  {
    source: 'DFSA Regulatory Notices',
    issue: 'Latest run produced the same content hash as the DFSA Rules page, indicating a hash collision.',
    remediation: 'Extract actual notices content or mark one source limited until the adapter is fixed.',
  },
  {
    source: 'UAE FIU Homepage',
    issue: 'Homepage extraction is shallow and less useful than the FIU circulars/publications source.',
    remediation: 'Promote the circulars source as primary and demote the homepage to reference status.',
  },
  {
    source: 'DIFC Laws and Regulations',
    issue: 'Current registry keeps this source in remediation pending source-structure/access review.',
    remediation: 'Rerun Source Lab, verify meaningful hash-unique content, and keep held until Evidence Trail review clears it.',
  },
]

const LIMITED_SOURCES = [
  {
    source: 'Federal Tax Authority (FTA)',
    constraint: 'Direct portal access restricted. VAT and corporate tax monitoring require item-level source checks before activation. Disclosed where FTA is in scope.',
  },
  {
    source: 'Capital Market Authority / former SCA',
    constraint: 'Transitional following Federal Decree-Law No. 32 of 2025. Source URL and extraction method under review. Fallback via UAE Legislation Portal available. Disclosed before any pilot with capital markets scope.',
  },
  {
    source: 'UAE Legislation Portal item-level adapter',
    constraint: 'The portal is readiness-supported as a source, but homepage aggregate changes are not treated as customer-ready legal updates until item-level extraction is checked.',
  },
]

const INACTIVE_SOURCES = [
  {
    source: 'Official Gazette / Al-Jaridah Al-Rasmiah',
    status: 'Validation pending. Not included in any pilot scope until public accessibility is reviewed.',
  },
  {
    source: 'e-Laws / Ministry of Justice portal',
    status: 'Access-restricted. Not currently monitorable. Disclosed in source review.',
  },
]

const UNDER_VALIDATION = [
  { source: 'UAE Data Office / PDPL', why: 'Data protection obligations affect regulated fintech, DIFC/ADGM firms, and legal teams.', profile: 'DIFC/ADGM firms, legal teams, data protection leads' },
  { source: 'Executive Office for AML/CFT', why: 'AML/CFT guidance and national risk priorities affect supervised financial and VASP firms.', profile: 'AML consultants, VASPs, payments, banks' },
  { source: 'DMCC regulatory notices', why: 'Free zone notices may affect commodity, crypto, and corporate service providers.', profile: 'DMCC firms and consultants' },
  { source: 'Insurance Authority / insurance supervision', why: 'Insurance supervision affects carriers, brokers, insurtech, and legal advisers.', profile: 'Insurance, insurtech, law firms' },
  { source: 'CBUAE publications sub-page adapter', why: 'Improves precision for publication-level monitoring beyond broad page checks.', profile: 'Banks, payments, stored value providers' },
  { source: 'VARA publications sub-page adapter', why: 'Improves precision for rulebook, guidance, and publication-level VASP monitoring.', profile: 'VASPs, crypto exchanges, custodians' },
  { source: 'DFSA consultation papers', why: 'Consultations indicate future DIFC supervisory expectations.', profile: 'DIFC-regulated firms, legal teams' },
  { source: 'ADGM/FSRA consultation and notices', why: 'Consultations and notices affect ADGM firms before final rule changes.', profile: 'ADGM-regulated firms, funds, securities teams' },
  { source: 'DIFC Data Protection Commissioner', why: 'Privacy and data protection updates affect DIFC regulated and operating entities.', profile: 'DIFC firms, data protection leads, legal teams' },
  { source: 'UAE sanctions / AML-CFT sanctions list', why: 'Sanctions updates affect AML screening, onboarding, and ongoing monitoring.', profile: 'AML teams, VASPs, banks, payments firms' },
]

function SourceStatusBadge({ tone, children }) {
  const styles = {
    supported: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    validation: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
    limited: 'border-slate-500/25 bg-slate-500/10 text-slate-300',
    blocked: 'border-rose-400/20 bg-rose-400/10 text-rose-300',
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold ${styles[tone] || styles.limited}`}>
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
              {columns.map(column => (
                <td key={column.key} className="px-4 py-3 align-top text-slate-400">
                  {column.key === 'source'
                    ? <span className="font-medium text-slate-100">{row[column.key]}</span>
                    : row[column.key]
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
            StatuteProof starts with a UAE source pack under evidence-readiness review, then discloses
            readiness-supported, remediation, constrained, blocked, and under-validation sources separately.
            This is not presented as the entire UAE market.
          </p>
          <p className="text-xs text-slate-500 max-w-3xl mx-auto mt-3">
            Mapped does not mean monitoring-ready. Sources enter client monitoring only after access, extraction and proof/diff checks clear.
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Readiness-supported in the current registry — 9 sources</h3>
              <SourceStatusBadge tone="supported">Readiness-supported</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'publishes', label: 'What it publishes' },
                { key: 'extraction', label: 'Extraction' },
              ]}
              rows={READINESS_SUPPORTED_SOURCES}
            />
          </div>

          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Under extraction remediation — 4 sources</h3>
              <SourceStatusBadge tone="validation">Remediation</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'issue', label: 'Issue found' },
                { key: 'remediation', label: 'Remediation path' },
              ]}
              rows={REMEDIATION_SOURCES}
            />
          </div>

          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Limited / constrained — visible before pilot scope</h3>
              <SourceStatusBadge tone="limited">Limited</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'constraint', label: 'Constraint' },
              ]}
              rows={LIMITED_SOURCES}
            />
          </div>

          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Under validation — commercially relevant, not readiness-supported yet</h3>
              <SourceStatusBadge tone="validation">Under validation</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'why', label: 'Why it matters' },
                { key: 'profile', label: 'Client profile' },
              ]}
              rows={UNDER_VALIDATION.map(row => ({
                ...row,
                why: `${row.why} Status: Under validation. Not included in pilot scope until reviewed.`,
              }))}
            />
          </div>

          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Not readiness-supported / blocked — disclosed, not hidden</h3>
              <SourceStatusBadge tone="blocked">Blocked</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'status', label: 'Status' },
              ]}
              rows={INACTIVE_SOURCES}
            />
          </div>
        </div>

        <div className="bg-[#0A1628] border border-slate-800 rounded-xl p-6 mt-8 mb-6">
          <p className="text-sm text-slate-400 leading-relaxed">
            Source status reflects latest technical accessibility and extraction quality — not regulatory significance.
            A source being listed as limited or not readiness-supported does not reduce its legal importance. It means
            StatuteProof cannot currently monitor it reliably, and we will say so before you rely on it.
          </p>
        </div>

        <div className="bg-slate-950/50 border border-cyan-400/20 rounded-xl p-6 text-center">
          <h3 className="text-white text-xl font-bold mb-4">Need to verify a specific regulator or source?</h3>
          <button
            onClick={onCreateWorkspace}
            className="inline-flex items-center gap-2 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors"
          >
            Create workspace to review source readiness <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  )
}

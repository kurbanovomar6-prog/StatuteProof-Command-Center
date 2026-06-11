import { ArrowRight } from 'lucide-react'

const ACTIVE_SOURCES = [
  { source: 'Central Bank of the UAE (CBUAE)', publishes: 'Circulars, licensing notices, payment system regulations', extraction: 'HTML structured' },
  { source: 'Virtual Assets Regulatory Authority (VARA)', publishes: 'VASP licensing, rulebook updates, guidance notes', extraction: 'HTML / PDF' },
  { source: 'Dubai Financial Services Authority (DFSA)', publishes: 'DIFC firm regulations, rulebook notices', extraction: 'HTML structured' },
  { source: 'ADGM / FSRA', publishes: 'ADGM regulations, FSRA notices, licensing updates', extraction: 'HTML structured' },
  { source: 'UAE Financial Intelligence Unit (FIU)', publishes: 'AML/CFT guidance, typologies, circulars', extraction: 'HTML / PDF' },
  { source: 'Ministry of Finance', publishes: 'Federal financial notices, regulations', extraction: 'HTML structured' },
  { source: 'UAE Legislation Portal', publishes: 'Federal laws and decrees', extraction: 'HTML structured; aggregate page changes require adapter review for item-level alerts' },
  { source: 'DIFC Laws', publishes: 'Primary and subsidiary DIFC legislation', extraction: 'HTML structured' },
  { source: 'Ministry of Economy', publishes: 'Commercial licensing, AML policy', extraction: 'HTML structured' },
]

const LIMITED_SOURCES = [
  {
    source: 'Federal Tax Authority (FTA)',
    constraint: 'Direct portal access restricted. VAT and corporate tax monitoring available only where validated fallback sources support the profile. Disclosed where FTA is in scope.',
  },
  {
    source: 'Capital Market Authority / former SCA',
    constraint: 'Transitional following Federal Decree-Law No. 32 of 2025. Source URL and extraction method under review. Fallback via UAE Legislation Portal available. Disclosed before any pilot with capital markets scope.',
  },
  {
    source: 'UAE Legislation Portal item-level adapter',
    constraint: 'The portal is active as a source, but homepage aggregate changes are not treated as customer-ready legal updates until item-level extraction is validated.',
  },
]

const INACTIVE_SOURCES = [
  {
    source: 'Official Gazette / Al-Jaridah Al-Rasmiah',
    status: 'Validation pending. Not included in any pilot scope until confirmed accessible.',
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
  { source: 'CBUAE circulars/publications sub-page adapter', why: 'Improves precision for circular-level monitoring beyond broad page checks.', profile: 'Banks, payments, stored value providers' },
  { source: 'VARA publications sub-page adapter', why: 'Improves precision for rulebook, guidance, and publication-level VASP monitoring.', profile: 'VASPs, crypto exchanges, custodians' },
  { source: 'DFSA consultation papers', why: 'Consultations indicate future DIFC supervisory expectations.', profile: 'DIFC-regulated firms, legal teams' },
  { source: 'ADGM/FSRA consultation and notices', why: 'Consultations and notices affect ADGM firms before final rule changes.', profile: 'ADGM-regulated firms, funds, securities teams' },
  { source: 'DIFC Data Protection Commissioner', why: 'Privacy and data protection updates affect DIFC regulated and operating entities.', profile: 'DIFC firms, data protection leads, legal teams' },
  { source: 'UAE sanctions / AML-CFT sanctions list', why: 'Sanctions updates affect AML screening, onboarding, and ongoing monitoring.', profile: 'AML teams, VASPs, banks, payments firms' },
]

function SourceStatusBadge({ tone, children }) {
  const styles = {
    validated: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
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
            StatuteProof starts with a validated core source layer, then discloses constrained, blocked,
            and under-validation sources separately. This is not presented as the entire UAE market.
          </p>
          <p className="text-xs text-slate-500 max-w-3xl mx-auto mt-3">
            Mapped does not mean active. Sources enter client monitoring only after access, extraction and proof/diff validation.
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Active validated core layer — monitored, extraction quality verified</h3>
              <SourceStatusBadge tone="validated">Validated</SourceStatusBadge>
            </div>
            <SourceTable
              columns={[
                { key: 'source', label: 'Source' },
                { key: 'publishes', label: 'What it publishes' },
                { key: 'extraction', label: 'Extraction' },
              ]}
              rows={ACTIVE_SOURCES}
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
              <h3 className="font-bold text-white">Under validation — commercially relevant, not active yet</h3>
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
                why: `${row.why} Status: Under validation. Not included in pilot scope until validated.`,
              }))}
            />
          </div>

          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <h3 className="font-bold text-white">Not yet active / blocked — disclosed, not hidden</h3>
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
            Source status reflects live technical accessibility and extraction quality — not regulatory significance.
            A source being listed as Limited or Not Active does not reduce its legal importance. It means
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

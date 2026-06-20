const SOURCES = [
  {
    source_id: 'AE-central-bank-of-the-uae',
    regulator: 'CBUAE Main',
    coverageArea: 'Financial regulation & monetary policy',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-cbuae-regulations',
    regulator: 'CBUAE Regulations',
    coverageArea: 'CBUAE rules & standards',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-uae-ministry-of-finance',
    regulator: 'UAE Ministry of Finance',
    coverageArea: 'Federal tax & budget policy',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-dubai-virtual-assets-regulatory-authority-vara',
    regulator: 'VARA Main',
    coverageArea: 'Virtual assets regulation',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-vara-enforcement',
    regulator: 'VARA Enforcement Notices',
    coverageArea: 'VARA enforcement actions',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-abu-dhabi-global-market-adgm',
    regulator: 'ADGM FSRA Main',
    coverageArea: 'ADGM financial regulation',
    status: 'CAVEAT',
    caveat: 'Character count is low on some pages; disclosed before pilot activation',
  },
  {
    source_id: 'AE-uaefiu-circulars',
    regulator: 'UAE FIU Circulars',
    coverageArea: 'AML/CFT circulars & notices',
    status: 'PENDING',
    caveat: 'Circulars page remains candidate/nav-shell; FIU publications hub is separate',
  },
  {
    source_id: 'AE-difc-laws-and-regulations',
    regulator: 'DIFC Laws and Regulations',
    coverageArea: 'DIFC legal database',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-uae-legislation-portal',
    regulator: 'UAE Legislation Portal',
    coverageArea: 'UAE federal legislation',
    status: 'PENDING',
    caveat: 'WAF/access constraints; not fresh-alert eligible',
  },
  {
    source_id: 'AE-uae-ministry-of-economy',
    regulator: 'UAE Ministry of Economy',
    coverageArea: 'Corporate & commercial regulation',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-dfsa-annual-reports',
    regulator: 'DFSA Annual Reports',
    coverageArea: 'DFSA annual reports',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-dfsa-annual-aml-reports',
    regulator: 'DFSA Annual AML Reports',
    coverageArea: 'DFSA AML annual reports',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-uae-financial-intelligence-unit-uaefiu',
    regulator: 'UAE FIU Homepage',
    coverageArea: 'FIU homepage (covered via 4 sub-sources)',
    status: 'PENDING',
    caveat: null,
  },
]

const SOURCE_TRUTH = {
  enabled: 239,
  readinessSupported: 170,
  remediation: 3,
}

const LAST_CHECKED = '2026-06-18'

function StatusBadge({ status }) {
  if (status === 'ACTIVE') {
    return (
      <span className="inline-flex items-center rounded-md border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-200">
        Fresh-alert eligible
      </span>
    )
  }
  if (status === 'CAVEAT') {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-[11px] font-semibold text-cyan-200">
        <span>&#9888;</span> Limited — see caveat
      </span>
    )
  }
  return (
    <span className="inline-flex items-center rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[11px] font-semibold text-amber-200">
      Not yet available
    </span>
  )
}

export default function SourceCoverageTable() {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-800 bg-[#0D1B2E] shadow-[0_18px_60px_rgba(0,0,0,0.25)]">
      <div className="flex items-start justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div>
          <span className="rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
            SAMPLE / DEMO
          </span>
          <h3 className="mt-2 text-sm font-semibold text-white">UAE regulatory sources</h3>
          <p className="mt-1 text-xs text-slate-500">
            Official sources currently in scope for UAE monitoring.
          </p>
        </div>
        <div className="text-right text-xs">
          <p className="font-semibold text-cyan-200">{SOURCE_TRUTH.enabled} UAE source records tracked</p>
          <p className="text-emerald-200">{SOURCE_TRUTH.readinessSupported} fresh-alert eligible</p>
          <p className="text-amber-200">{SOURCE_TRUTH.remediation} under technical review</p>
        </div>
      </div>

      <div className="overflow-y-auto max-h-80">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-slate-950/80 text-slate-500">
              <th className="px-4 py-2 text-left font-medium">Regulatory source</th>
              <th className="px-4 py-2 text-left font-medium">Coverage area</th>
              <th className="px-4 py-2 text-left font-medium">Status</th>
              <th className="px-4 py-2 text-left font-medium">Last checked</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {SOURCES.map(s => (
              <tr key={s.source_id} className="hover:bg-slate-900/40">
                <td className="px-4 py-2.5">
                  <div className="font-medium text-slate-200">{s.regulator}</div>
                </td>
                <td className="px-4 py-2.5 text-slate-400">{s.coverageArea}</td>
                <td className="px-4 py-2.5">
                  <div className="flex flex-col gap-1">
                    <StatusBadge status={s.status} />
                    {s.caveat && (
                      <span className="text-[11px] text-slate-500 leading-snug max-w-[240px]">
                        {s.caveat}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2.5 text-slate-500">{LAST_CHECKED}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-800 px-4 py-2.5 text-xs text-slate-500">
        Fresh-alert eligible means we have at least two confirmed baseline evidence runs with stable content hashes. Sources under technical review are not delivered to clients.
      </div>
    </div>
  )
}

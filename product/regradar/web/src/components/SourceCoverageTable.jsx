const SOURCES = [
  { source_id: 'AE-central-bank-of-the-uae', regulator: 'CBUAE Main', jurisdiction: 'UAE Federal', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-cbuae-regulations', regulator: 'CBUAE Regulations', jurisdiction: 'UAE Federal', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-uae-ministry-of-finance', regulator: 'UAE Ministry of Finance', jurisdiction: 'UAE Federal', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-dubai-virtual-assets-regulatory-authority-vara', regulator: 'VARA Main', jurisdiction: 'Dubai / VARA', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-vara-enforcement', regulator: 'VARA Enforcement Notices', jurisdiction: 'Dubai / VARA', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-abu-dhabi-global-market-adgm', regulator: 'ADGM FSRA Main', jurisdiction: 'ADGM / FSRA', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-uaefiu-circulars', regulator: 'UAE FIU Circulars', jurisdiction: 'UAE Federal', tier: 1, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-difc-laws-and-regulations', regulator: 'DIFC Laws and Regulations', jurisdiction: 'DIFC / DFSA', tier: 1, status: 'REMEDIATION' },
  { source_id: 'AE-uae-legislation-portal', regulator: 'UAE Legislation Portal', jurisdiction: 'UAE Federal', tier: 2, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-uae-ministry-of-economy', regulator: 'UAE Ministry of Economy', jurisdiction: 'UAE Federal', tier: 2, status: 'READINESS_SUPPORTED' },
  { source_id: 'AE-dubai-financial-services-authority-dfsa', regulator: 'DFSA Rulebook', jurisdiction: 'DIFC / DFSA', tier: 1, status: 'REMEDIATION' },
  { source_id: 'AE-dfsa-notices', regulator: 'DFSA Regulatory Notices', jurisdiction: 'DIFC / DFSA', tier: 1, status: 'REMEDIATION' },
  { source_id: 'AE-uae-financial-intelligence-unit-uaefiu', regulator: 'UAE FIU Homepage', jurisdiction: 'UAE Federal', tier: 2, status: 'REMEDIATION' },
]

const SOURCE_TRUTH = {
  enabled: 66,
  readinessSupported: 62,
  remediation: 4,
}

function StatusBadge({ status }) {
  if (status === 'READINESS_SUPPORTED') {
    return (
      <span className="rounded-md border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-200">
        READINESS-SUPPORTED
      </span>
    )
  }
  return (
    <span className="rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[11px] font-semibold text-amber-200">
      REMEDIATION
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
          <h3 className="mt-2 text-sm font-semibold text-white">UAE source pack readiness</h3>
          <p className="mt-1 text-xs text-slate-500">Sample rows using current readiness framing. Full registry truth is shown at right.</p>
        </div>
        <div className="text-right text-xs">
          <p className="font-semibold text-cyan-200">{SOURCE_TRUTH.enabled} enabled</p>
          <p className="text-emerald-200">{SOURCE_TRUTH.readinessSupported} readiness-supported</p>
          <p className="text-amber-200">{SOURCE_TRUTH.remediation} under extraction remediation</p>
        </div>
      </div>
      <div className="overflow-y-auto max-h-72">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-slate-950/80 text-slate-500">
              <th className="px-4 py-2 text-left font-medium">Source</th>
              <th className="px-4 py-2 text-left font-medium">Jurisdiction</th>
              <th className="px-4 py-2 text-left font-medium">Tier</th>
              <th className="px-4 py-2 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {SOURCES.map(s => (
              <tr key={s.source_id} className="hover:bg-slate-900/40">
                <td className="px-4 py-2">
                  <div className="font-medium text-slate-200">{s.regulator}</div>
                  <div className="text-slate-400 font-mono text-xs">{s.source_id}</div>
                </td>
                <td className="px-4 py-2 text-slate-400">{s.jurisdiction}</td>
                <td className="px-4 py-2 text-slate-400">Tier {s.tier}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={s.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-slate-800 px-4 py-2 text-xs text-slate-500">
        Sample rows only. Remediation sources are not treated as ready until extraction quality is fixed and rerun.
      </div>
    </div>
  )
}

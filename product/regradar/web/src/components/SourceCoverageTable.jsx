import { SOURCE_TRUTH } from '../data/sourceCounts.js'

const SOURCES = [
  {
    source_id: 'AE-cbuae-rulebook-revision-updates',
    regulator: 'CBUAE Rulebook Revision Updates',
    coverageArea: 'Rulebook-wide revision history',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-cbuae-payment-token-services-rulebook',
    regulator: 'CBUAE Payment Token Services Regulation',
    coverageArea: 'Payment token / stablecoin rules',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-mof-publications-and-releases',
    regulator: 'MoF Publications and Releases',
    coverageArea: 'Federal finance & tax policy',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-vara-rulebook-updates',
    regulator: 'VARA Rulebook Revision Updates',
    coverageArea: 'Virtual assets rulebook changes',
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
    source_id: 'AE-adgm-fsra-rulebooks',
    regulator: 'ADGM FSRA Rules and Regulations',
    coverageArea: 'ADGM financial regulation',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-adgm-fsra-regulatory-alerts',
    regulator: 'ADGM FSRA Regulatory Alerts',
    coverageArea: 'FSRA regulatory alerts listing',
    status: 'CAVEAT',
    caveat: 'Enabled as candidate — listing extraction still being validated before alert eligibility',
  },
  {
    source_id: 'AE-dfsa-aml-rulebook-module',
    regulator: 'DFSA AML Rulebook Module',
    coverageArea: 'DFSA AML/CTF & sanctions module',
    status: 'ACTIVE',
    caveat: 'Repointed from a frozen-version URL to the canonical current-version page (July 2026)',
  },
  {
    source_id: 'AE-difc-laws-and-regulations',
    regulator: 'DIFC Laws and Regulations',
    coverageArea: 'DIFC legal database',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-sca-circulars-rules-procedures',
    regulator: 'UAE CMA Circulars, Rules and Procedures',
    coverageArea: 'Capital markets circulars',
    status: 'ACTIVE',
    caveat: 'Repointed to the CMA’s new canonical page during the SCA→CMA site transition (July 2026)',
  },
  {
    source_id: 'AE-moet-aml-170b7988',
    regulator: 'Ministry of Economy — AML',
    coverageArea: 'DNFBP AML obligations',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-eocn-news-en',
    regulator: 'EOCN News and Sanctions Updates',
    coverageArea: 'UN sanctions / TFS updates',
    status: 'ACTIVE',
    caveat: null,
  },
  {
    source_id: 'AE-fta-tax-legislation-listing',
    regulator: 'FTA — All Tax Legislation',
    coverageArea: 'Federal tax legislation listing',
    status: 'CAVEAT',
    caveat: 'Enabled as candidate after a June 2026 extraction fix — not alert-eligible until it passes the fresh-alert gate',
  },
  {
    source_id: 'AE-uae-financial-intelligence-unit-uaefiu',
    regulator: 'UAE FIU (uaefiu.gov.ae)',
    coverageArea: 'AML/CFT publications & typologies',
    status: 'PENDING',
    caveat: 'Geo-IP restricted from outside the UAE — disclosed, covered via EOCN/CBUAE/MoE alternatives',
  },
  {
    source_id: 'AE-uae-legislation-portal',
    regulator: 'UAE Legislation Portal',
    coverageArea: 'UAE federal legislation',
    status: 'PENDING',
    caveat: 'Access blocked from outside the UAE; not fresh-alert eligible',
  },
]

const LAST_CHECKED = '2026-07-12'

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
          <p className="font-semibold text-cyan-200">{SOURCE_TRUTH.enabled} enabled UAE source records</p>
          <p className="text-emerald-200">{SOURCE_TRUTH.readinessSupported} fresh-alert eligible</p>
          {/* The remainder (enabled − fresh) so the three lines reconcile to
              `enabled` and this never undercounts the pending set the
              transparency matrix discloses; {SOURCE_TRUTH.candidate} of these are
              in formal candidate monitoring mode. */}
          <p className="text-amber-200">
            {SOURCE_TRUTH.enabled - SOURCE_TRUTH.readinessSupported} enabled, pending fresh-alert validation
          </p>
        </div>
      </div>

      <div className="overflow-y-auto max-h-80">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-slate-950/80 text-slate-500">
              <th className="px-4 py-2 text-left font-medium">Regulatory source</th>
              <th className="px-4 py-2 text-left font-medium">Coverage area</th>
              <th className="px-4 py-2 text-left font-medium">Status</th>
              <th className="px-4 py-2 text-left font-medium">Status as of</th>
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
        Fresh-alert eligible means we have at least two confirmed baseline evidence runs with stable content hashes. Candidate and geo-restricted sources are not delivered to clients. Statuses reflect the source-register review of {LAST_CHECKED}.
      </div>
    </div>
  )
}

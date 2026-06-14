import { useState } from 'react'
import { Download, ExternalLink, BarChart3 } from 'lucide-react'
import { MOCK_REPORTS, MOCK_ALERTS } from '../../data/appMockData'
import { getWorkspaceProfile, filterReports } from '../../data/workspaceProfile'

const RISK_DARK = {
  HIGH:   'text-red-400   bg-red-500/15   border border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border border-amber-500/30',
  MIXED:  'text-blue-400  bg-blue-500/15  border border-blue-500/30',
  INFO:   'text-slate-400 bg-slate-700    border border-slate-600',
}

const REPORT_DETAIL = {
  r1: {
    summary: 'Sample source readiness review for a UAE VASP profile. Shows how mapped sources, validation status, limitations and review steps are presented before a pilot.',
    sections: ['Source map summary', 'Validation status', 'Known limitations', 'Pilot review steps'],
    alertIds: ['a1'],
  },
  r2: {
    summary: 'Sample CBUAE / AML brief preview for banks, payment firms, fintech teams and MLROs. Shows how source proof and review gates would appear before delivery routing is enabled.',
    sections: ['AML/CFT source layer', 'Profile relevance', 'Human review gate', 'Delivery readiness'],
    alertIds: ['a2'],
  },
  r3: {
    summary: 'Sample VARA rulebook update preview for VASP / crypto profiles. This is sample content and not a live client report.',
    sections: ['Rulebook update', 'VASP relevance', 'Document limitation note', 'Suggested internal review'],
    alertIds: ['a1'],
  },
  r4: {
    summary: 'DIFC / DFSA source transparency sample showing confirmed, remediation and limited source layers for a UAE pilot profile.',
    sections: ['DIFC / DFSA source map', 'Confirmed sources', 'Remediation sources', 'Limitations disclosed'],
    alertIds: ['a3'],
  },
  r5: {
    summary: 'ADGM / FSRA preview showing the confirmed main-source layer and circular/rulebook layers still under validation before activation.',
    sections: ['ADGM / FSRA main source', 'Circular/rulebook validation status', 'Proof/diff validation', 'Limitations disclosed'],
    alertIds: [],
  },
  r6: {
    summary: 'FTA public clarification watch sample for UAE tax and corporate profiles. Activation requires item-level source checks.',
    sections: ['FTA source map', 'Clarification watch', 'Item-level validation', 'Pilot setup requirement'],
    alertIds: ['a5'],
  },
  r7: {
    summary: 'UAE FIU typology brief preview for AML, MLRO, VASP and payment profiles. Human review gates any client delivery.',
    sections: ['FIU source proof', 'AML profile relevance', 'Human review gate', 'Delivery readiness'],
    alertIds: ['a4'],
  },
  r8: {
    summary: 'Proof/diff artifact sample showing the evidence structure used to support a reviewed UAE source brief.',
    sections: ['Source proof', 'Extraction method', 'Diff summary', 'Limitation note'],
    alertIds: [],
  },
}

export default function ReportsPage() {
  const profile     = getWorkspaceProfile()
  const baseReports = filterReports(MOCK_REPORTS, profile)

  const [selectedId, setSelectedId] = useState(baseReports[0]?.id || 'r1')
  const report = baseReports.find(r => r.id === selectedId) || baseReports[0]
  const detail = REPORT_DETAIL[selectedId] || (report ? REPORT_DETAIL[report.id] : null)
  const relatedAlerts = detail ? MOCK_ALERTS.filter(a => detail.alertIds.includes(a.id)) : []

  return (
    <div className="p-5 flex flex-col h-full">
      <div className="mb-4">
        <h1 className="text-lg font-bold text-white mb-1">Source Reports</h1>
        <p className="text-sm text-slate-400">
          {profile.markets.length > 0
            ? `Sample source reports for: ${profile.markets.join(', ')}`
            : 'Sample source reports — select markets in Settings to filter.'}
        </p>
      </div>

      <div className="mb-4 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Sample report outputs</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              These cards show report formats used in source readiness and pilot review. Generated client reports require pilot setup and approved routing.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Available sample', 'Generated manually', 'Requires pilot setup', 'Proof artifact'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 grid lg:grid-cols-[300px_1fr] gap-4 min-h-0">

        {/* Left: report list */}
        <div className="flex flex-col min-h-0 gap-2 overflow-y-auto">
          {baseReports.length === 0 && (
            <div className="text-center py-10 px-4">
              <p className="text-sm text-slate-400 mb-1">No reports for your selected profile yet.</p>
              <p className="text-xs text-slate-600">Add more markets in Settings → Monitoring profile.</p>
            </div>
          )}
          {baseReports.map(r => (
            <button
              key={r.id}
              onClick={() => setSelectedId(r.id)}
              className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                selectedId === r.id
                  ? 'border-cyan-500/30 bg-slate-900 ring-1 ring-cyan-500/20'
                  : 'border-slate-800 bg-slate-900 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[r.risk] || RISK_DARK.INFO}`}>{r.risk}</span>
                <span className="text-xs text-slate-500">{r.date}</span>
              </div>
              <p className="text-xs font-semibold text-white leading-snug mb-1.5">{r.title}</p>
              <p className="text-xs text-slate-500">{r.markets}</p>
              <span className="mt-2 inline-flex rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-200">
                {r.status}
              </span>
              {r.alerts > 0 && (
                <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                  <span className="text-slate-400">{r.alerts} alert{r.alerts !== 1 ? 's' : ''}</span>
                  {r.reviewItems > 0 && <span className="text-amber-400">{r.reviewItems} for review</span>}
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Right: report detail */}
        <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl flex flex-col min-h-0 overflow-hidden">
          {!report && (
            <div className="flex-1 flex items-center justify-center text-center px-6 py-12">
              <p className="text-sm text-slate-400">No report selected.</p>
            </div>
          )}
          {report && detail && (<>
          {/* Header */}
          <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-semibold text-white truncate">{report.title}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[report.risk] || RISK_DARK.INFO}`}>{report.risk}</span>
              <span className="text-xs text-slate-500">{report.date}</span>
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800 text-xs">

            {/* Summary */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-1.5">Summary</p>
              <p className="text-slate-300 leading-relaxed">{detail.summary}</p>
            </div>

            {/* Metadata */}
            <div className="px-5 py-4 grid grid-cols-3 gap-4">
              <div>
                <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Markets</p>
                <p className="text-slate-200 font-medium">{report.markets}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Sample items</p>
                <p className="text-slate-200 font-medium">{report.alerts}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Review items</p>
                <p className={`font-medium ${report.reviewItems > 0 ? 'text-amber-400' : 'text-slate-400'}`}>{report.reviewItems}</p>
              </div>
            </div>

            {/* Sections */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Report Sections</p>
              <div className="space-y-1.5">
                {detail.sections.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-300">
                    <span className="text-cyan-400 font-semibold flex-shrink-0">{i + 1}.</span>
                    {s}
                  </div>
                ))}
              </div>
            </div>

            {/* Related alerts */}
            {relatedAlerts.length > 0 && (
              <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Included sample previews</p>
                <div className="space-y-2">
                  {relatedAlerts.map(a => (
                    <div key={a.id} className="flex items-start gap-2.5 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full flex-shrink-0 ${RISK_DARK[a.risk]}`}>{a.risk}</span>
                      <div>
                        <p className="text-slate-200 font-medium">{a.title}</p>
                        <p className="text-slate-500 text-xs mt-0.5">{a.flag} {a.market} · {a.source}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Report provenance</p>
              {['Sample output', 'Source proof structure', 'Human review gate', 'Limitations disclosed'].map(e => (
                <div key={e} className="flex items-center gap-1.5 text-slate-400 mb-1">
                  <span className="text-emerald-400 font-bold">✓</span> {e}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="px-5 py-3.5 border-t border-slate-800 flex items-center gap-2 flex-shrink-0">
            <button className="flex items-center gap-1.5 text-xs font-medium text-slate-300 border border-slate-700 hover:border-slate-600 px-3 py-2 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" />
              Preview sample
            </button>
            <button
              type="button"
              disabled
              className="flex items-center gap-1.5 text-xs font-medium text-slate-500 border border-slate-700 bg-slate-800/70 px-3 py-2 rounded-lg cursor-not-allowed"
              title="Generated client reports require pilot setup."
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Share link
            </button>
            <span className="text-xs text-slate-500">Generated client reports require pilot setup.</span>
          </div>
          </>)}
        </div>
      </div>
    </div>
  )
}

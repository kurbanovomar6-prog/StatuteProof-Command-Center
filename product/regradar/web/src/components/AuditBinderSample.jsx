import { FileText, Lock, ExternalLink } from 'lucide-react'

// SAMPLE / FAKE — illustrative content only, not real regulatory data

const RUN_LOG = [
  {
    date: '2026-01-15',
    source: 'VARA Compliance Rulebook',
    regulator: 'VARA',
    status: 'CHANGED',
    hash: 'd8e9f4a2…',
    quality: 'GOOD',
  },
  {
    date: '2026-01-15',
    source: 'DFSA Rulebook Module COB',
    regulator: 'DFSA',
    status: 'UNCHANGED',
    hash: 'c3a7d1b9…',
    quality: 'GOOD',
  },
  {
    date: '2026-01-15',
    source: 'CBUAE AML/CFT Guidance',
    regulator: 'CBUAE',
    status: 'UNCHANGED',
    hash: 'f1e8c5a4…',
    quality: 'GOOD',
  },
  {
    date: '2026-01-14',
    source: 'EOCN News and Sanctions Updates',
    regulator: 'EOCN',
    status: 'FIRST_SEEN',
    hash: 'b2d6e3f7…',
    quality: 'GOOD',
  },
  {
    date: '2026-01-13',
    source: 'ADGM FSRA Supervision Circulars',
    regulator: 'ADGM FSRA',
    status: 'UNCHANGED',
    hash: 'a9c4b8e2…',
    quality: 'GOOD',
  },
]

const STATUS_STYLES = {
  CHANGED: 'border-amber-400/30 bg-amber-400/10 text-amber-300',
  UNCHANGED: 'border-slate-600/40 bg-slate-800/40 text-slate-400',
  FIRST_SEEN: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300',
}

const DIFF_LINES = [
  { type: 'context', text: ' 4.2.1 — Compliance Risk Management Framework' },
  { type: 'context', text: ' A VASP shall maintain a compliance risk management' },
  { type: 'context', text: ' framework that is commensurate with its risk profile.' },
  { type: 'removed', text: '- The framework shall be reviewed annually by senior management.' },
  { type: 'added',   text: '+ The framework shall be reviewed semi-annually by senior management' },
  { type: 'added',   text: '+ and the board of directors, with findings documented in writing.' },
  { type: 'context', text: '  A copy of the review record shall be retained for five years.' },
]

export default function AuditBinderSample() {
  return (
    <section className="bg-[#07111F] py-20" id="audit-binder">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        {/* Section header */}
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <FileText className="h-4 w-4" />
            SAMPLE / FAKE — demonstration only
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">What the audit binder export contains</h2>
          <p className="mx-auto max-w-3xl text-slate-400 text-sm leading-relaxed">
            Every StatuteProof workspace can export a complete evidence binder — a PDF containing
            the monitoring run log, change event records, SHA-256 hash chains, and MLRO response log
            entries for a selected period. The sample below shows the structure.
          </p>
        </div>

        {/* Document viewer wrapper */}
        <div className="mx-auto max-w-4xl">
          <div className="rounded-2xl border border-slate-700 bg-[#0A1628] shadow-[0_24px_70px_rgba(0,0,0,0.50)] overflow-hidden">

            {/* Viewer toolbar */}
            <div className="flex items-center justify-between border-b border-slate-700 bg-slate-950 px-5 py-3">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-rose-500/70" />
                <span className="h-3 w-3 rounded-full bg-amber-500/70" />
                <span className="h-3 w-3 rounded-full bg-emerald-500/70" />
              </div>
              <span className="font-mono text-xs text-slate-500">evidence-binder-Q1-2026.pdf</span>
              <div className="flex items-center gap-1.5">
                <span className="rounded border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold text-amber-300 uppercase tracking-wide">
                  SAMPLE / FAKE
                </span>
              </div>
            </div>

            {/* Document content — light "paper" look */}
            <div className="bg-white text-slate-900">

              {/* Document header */}
              <div className="border-b border-slate-200 px-8 py-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
                      StatuteProof Evidence Binder
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 leading-tight">
                      [Client Firm Name] — Monitoring Evidence Record
                    </h3>
                    <div className="mt-1 text-sm text-slate-500">
                      Period: 01 January 2026 – 31 March 2026
                    </div>
                  </div>
                  <div className="text-right text-xs text-slate-400 shrink-0">
                    <div className="font-mono">Exported: 2026-04-01</div>
                    <div className="mt-1">Run records: 91 days</div>
                    <div className="mt-1 font-bold text-amber-600 border border-amber-300 bg-amber-50 px-2 py-0.5 rounded">
                      SAMPLE / FAKE
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 1 — Monitoring Run Log */}
              <div className="px-8 py-6 border-b border-slate-200">
                <div className="mb-4 flex items-center gap-2">
                  <span className="h-5 w-5 rounded bg-slate-800 text-white text-[10px] font-bold flex items-center justify-center">1</span>
                  <h4 className="text-sm font-bold uppercase tracking-wide text-slate-700">
                    Monitoring Run Log
                  </h4>
                </div>
                <div className="min-w-0 overflow-x-auto">
                  <table className="w-full min-w-[420px] text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50">
                        {['Date', 'Source', 'Regulator', 'Status', 'Hash (truncated)', 'Extraction Quality'].map(h => (
                          <th key={h} className="py-2 px-3 text-left font-semibold text-slate-500 uppercase tracking-wide text-[10px]">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {RUN_LOG.map((row, i) => (
                        <tr
                          key={i}
                          className={`border-b border-slate-100 ${row.status === 'CHANGED' ? 'bg-amber-50' : ''}`}
                        >
                          <td className="py-2 px-3 font-mono text-slate-600">{row.date}</td>
                          <td className="py-2 px-3 font-medium text-slate-800">{row.source}</td>
                          <td className="py-2 px-3 text-slate-600">{row.regulator}</td>
                          <td className="py-2 px-3">
                            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${STATUS_STYLES[row.status]}`}>
                              {row.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 font-mono text-slate-500">{row.hash}</td>
                          <td className="py-2 px-3">
                            <span className="flex items-center gap-1 text-emerald-700 font-medium">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block" />
                              {row.quality}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Section 2 — Change Event Record */}
              <div className="px-8 py-6 border-b border-slate-200">
                <div className="mb-4 flex items-center gap-2">
                  <span className="h-5 w-5 rounded bg-slate-800 text-white text-[10px] font-bold flex items-center justify-center">2</span>
                  <h4 className="text-sm font-bold uppercase tracking-wide text-slate-700">
                    Change Event Record — VARA Compliance Rulebook
                  </h4>
                </div>

                <div className="grid sm:grid-cols-2 gap-4 mb-4">
                  <div className="space-y-3">
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-0.5">Source URL</div>
                      <div className="font-mono text-xs text-blue-700 flex items-center gap-1">
                        https://www.vara.ae/en/rulebook/compliance-risk-management
                        <ExternalLink className="h-3 w-3 text-slate-400 shrink-0" />
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-0.5">Change Detected</div>
                      <div className="font-mono text-xs text-slate-700">2026-01-15 07:23:41 UTC</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-0.5">Chain Status</div>
                      <div className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="text-xs font-bold text-emerald-700">INTACT</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-0.5">SHA-256 (before)</div>
                      <div className="font-mono text-xs text-slate-500 break-all">a3f5b2c1d4e6f789…</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-0.5">SHA-256 (after)</div>
                      <div className="font-mono text-xs text-slate-800 break-all font-semibold">d8e9f4a2b1c3d5e7…</div>
                    </div>
                  </div>
                </div>

                {/* Diff excerpt */}
                <div className="rounded-lg border border-slate-200 bg-slate-50 overflow-hidden">
                  <div className="border-b border-slate-200 bg-slate-100 px-4 py-2 flex items-center justify-between">
                    <span className="font-mono text-[10px] text-slate-500">vara-compliance-rulebook.txt — diff excerpt</span>
                    <span className="text-[10px] text-slate-400">SAMPLE — illustrative diff</span>
                  </div>
                  <pre className="p-4 text-[11px] leading-6 overflow-x-auto">
                    {DIFF_LINES.map((line, i) => (
                      <div
                        key={i}
                        className={
                          line.type === 'added'
                            ? 'bg-emerald-100 text-emerald-800'
                            : line.type === 'removed'
                            ? 'bg-red-100 text-red-700 line-through decoration-red-400'
                            : 'text-slate-500'
                        }
                      >
                        {line.text}
                      </div>
                    ))}
                  </pre>
                </div>
              </div>

              {/* Section 3 — MLRO Review Decision */}
              <div className="px-8 py-6 border-b border-slate-200">
                <div className="mb-4 flex items-center gap-2">
                  <span className="h-5 w-5 rounded bg-slate-800 text-white text-[10px] font-bold flex items-center justify-center">3</span>
                  <h4 className="text-sm font-bold uppercase tracking-wide text-slate-700">
                    MLRO Review Decision Log
                  </h4>
                </div>

                <div className="min-w-0 overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full min-w-[420px] text-xs border-collapse">
                    <tbody>
                      {[
                        ['Brief Delivered', '2026-01-15 09:14 UTC'],
                        ['Reviewed by', '[MLRO Name] — 2026-01-15 11:30 UTC'],
                        ['Decision', 'Policy update required — update AML monitoring thresholds'],
                        ['Action Reference', 'Internal memo ref: AML-2026-003'],
                        ['Status', 'CLOSED'],
                      ].map(([label, value]) => (
                        <tr key={label} className="border-b border-slate-100">
                          <td className="py-2.5 px-4 text-[10px] font-semibold uppercase tracking-wide text-slate-400 bg-slate-50 w-40 shrink-0">
                            {label}
                          </td>
                          <td className={`py-2.5 px-4 ${label === 'Status' ? 'font-bold text-emerald-700' : 'text-slate-700'}`}>
                            {value}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <p className="mt-3 text-[10px] text-slate-400 leading-relaxed">
                  The MLRO response log records who reviewed the brief, when they reviewed it, what decision was made,
                  and any internal action reference. This log is included in the binder export and is not editable after submission.
                </p>
              </div>

              {/* Document footer */}
              <div className="px-8 py-5 bg-slate-50 flex items-start gap-2.5">
                <Lock className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                <p className="text-[10px] leading-relaxed text-slate-500">
                  <span className="font-semibold text-slate-600">SAMPLE / FAKE — illustrative content only.</span>
                  {' '}StatuteProof monitoring intelligence only. Not legal advice. Hash verification available on request.
                  Verify all information against official source material and qualified legal or compliance counsel before acting.
                </p>
              </div>

            </div>
            {/* /Document content */}

          </div>
        </div>

        <p className="mx-auto mt-5 max-w-3xl text-center text-xs leading-relaxed text-slate-600">
          Audit binder exports are available on all paid plans. The binder is generated from your actual evidence records —
          not from a template. Content above is SAMPLE / FAKE and does not represent real regulatory data.
          StatuteProof monitoring intelligence only. Not legal advice.
        </p>
      </div>
    </section>
  )
}

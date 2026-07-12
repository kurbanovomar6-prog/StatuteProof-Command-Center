import { useState } from 'react'
import { Download, FileCheck2, ShieldCheck, TriangleAlert } from 'lucide-react'

import { reports } from '../../api'

function isoDay(d) {
  return d.toISOString().slice(0, 10)
}

function currentMonthStart() {
  const d = new Date()
  return isoDay(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1)))
}

// Change-state chip. NO_PROOF (nothing recorded in the period) is the honest
// "not checked" signal and is shown in rose; CHANGED in cyan; UNCHANGED-with-proof
// in emerald. These are recorded facts, never a compliance judgement.
function StateChip({ state }) {
  const map = {
    CHANGED: ['bg-cyan-500/12 text-cyan-200 border-cyan-400/25', 'Changed'],
    UNCHANGED: ['bg-emerald-500/10 text-emerald-200 border-emerald-400/20', 'Unchanged'],
    NO_PROOF: ['bg-rose-500/12 text-rose-200 border-rose-400/25', 'No coverage'],
  }
  const [cls, label] = map[state] || ['bg-slate-700/40 text-slate-300 border-slate-600/40', state || '—']
  return <span className={`inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium ${cls}`}>{label}</span>
}

function Tile({ label, value, tone = 'default' }) {
  const toneCls = tone === 'warn'
    ? 'text-amber-300'
    : tone === 'bad'
      ? 'text-rose-300'
      : 'text-white'
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2.5">
      <p className={`font-mono text-lg font-semibold tabular-nums ${toneCls}`}>{value}</p>
      <p className="mt-0.5 text-[11px] leading-tight text-slate-500">{label}</p>
    </div>
  )
}

function triggerDownload(text, filename, mime) {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Coverage certificate — negative-assurance viewer.
 *
 * Renders, for a chosen period, exactly what StatuteProof checked on each
 * monitored source and — honestly — where the recorded evidence has gaps. It
 * makes NO claim of complete coverage. The structured certificate is fetched as
 * JSON and rendered natively; Markdown / HTML downloads reuse the same endpoint.
 */
export default function CoverageCertificatePanel() {
  const [periodStart, setPeriodStart] = useState(currentMonthStart())
  const [periodEnd, setPeriodEnd] = useState(isoDay(new Date()))
  const [status, setStatus] = useState('idle') // idle | loading | loaded | error
  const [cert, setCert] = useState(null)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState('')

  async function generate() {
    setStatus('loading')
    setError('')
    setCert(null)
    try {
      const data = await reports.coverageCertificate({ periodStart, periodEnd, format: 'json' })
      if (data.status !== 'ok' || !data.certificate) {
        throw new Error(data.message || 'Could not build the coverage certificate.')
      }
      setCert(data.certificate)
      setStatus('loaded')
    } catch (err) {
      setError(err.message || 'Could not build the coverage certificate.')
      setStatus('error')
    }
  }

  async function download(format) {
    setDownloading(format)
    setError('')
    try {
      const data = await reports.coverageCertificate({ periodStart, periodEnd, format })
      if (data.status !== 'ok' || !data.report) {
        throw new Error(data.message || 'No report content returned.')
      }
      const report = data.report
      const ext = format === 'html' ? 'html' : 'md'
      const mime = format === 'html' ? 'text/html' : 'text/markdown'
      triggerDownload(report, `coverage-certificate-${periodStart}_${periodEnd}.${ext}`, mime)
    } catch (err) {
      setError(err.message || 'Could not download the certificate.')
    } finally {
      setDownloading('')
    }
  }

  const summary = cert?.summary || {}
  const sources = cert?.sources || []
  const isLoading = status === 'loading'
  // Generate and download share the panel; while either is in flight, lock the
  // generate control + date inputs so a new generate can't unmount an in-flight
  // download's buttons out from under it.
  const busy = isLoading || !!downloading

  return (
    <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
          <FileCheck2 className="h-4 w-4 text-cyan-300" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Coverage certificate</h2>
          <p className="mt-0.5 max-w-2xl text-xs leading-relaxed text-slate-400">
            Negative assurance — for the chosen period, exactly what was checked on each monitored
            source and where the recorded evidence has gaps. It makes no claim of complete coverage.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">From</span>
          <input
            type="date"
            value={periodStart}
            max={periodEnd}
            onChange={e => setPeriodStart(e.target.value)}
            disabled={busy}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none disabled:opacity-60"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">To</span>
          <input
            type="date"
            value={periodEnd}
            min={periodStart}
            onChange={e => setPeriodEnd(e.target.value)}
            disabled={busy}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none disabled:opacity-60"
          />
        </label>
        <button
          type="button"
          onClick={generate}
          disabled={isLoading}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-colors ${
            busy ? 'cursor-not-allowed bg-slate-800 text-slate-500' : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
          }`}
        >
          <FileCheck2 className="h-3.5 w-3.5" />
          {isLoading ? 'Building…' : 'Generate certificate'}
        </button>
      </div>

      {error && (
        <p className="mt-3 text-xs text-rose-300">{error}</p>
      )}

      {status === 'loaded' && cert && (
        <div className="mt-5 space-y-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <p className="text-sm font-semibold text-white">{cert.period_label || `${periodStart} — ${periodEnd}`}</p>
              <p className="mt-0.5 text-[11px] text-slate-500">
                Generated {cert.generated_at_utc || '—'} · negative assurance
              </p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-md border border-cyan-400/25 bg-cyan-500/10 px-2.5 py-1 text-[11px] font-medium text-cyan-200">
              <ShieldCheck className="h-3.5 w-3.5" /> Recorded evidence only
            </span>
          </div>

          {cert.negative_assurance_statement && (
            <p className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-3 text-xs leading-relaxed text-slate-300">
              {cert.negative_assurance_statement}
            </p>
          )}

          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
            <Tile label="Sources" value={summary.sources_total ?? 0} />
            <Tile label="Changed" value={summary.sources_changed ?? 0} />
            <Tile label="With gaps" value={summary.sources_with_gaps ?? 0} tone={summary.sources_with_gaps ? 'warn' : 'default'} />
            <Tile label="No coverage" value={summary.sources_no_coverage ?? 0} tone={summary.sources_no_coverage ? 'bad' : 'default'} />
            <Tile label="Checks" value={summary.total_successful_checks ?? 0} />
            <Tile label="Days w/ hash" value={summary.total_days_with_proof_hash ?? 0} />
          </div>

          {sources.length === 0 ? (
            <p className="rounded-lg border border-slate-800 bg-slate-950/40 px-4 py-4 text-xs text-slate-400">
              No monitored sources resolved for this period. Configure and enable sources, then generate again.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wide text-slate-500">
                    <th scope="col" className="px-3 py-2 font-semibold">Source</th>
                    <th scope="col" className="px-3 py-2 font-semibold">State</th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">Checks</th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">Days w/ hash</th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">Gap days</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Last check (UTC)</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Last proof hash</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map(s => {
                    const flagged = s.change_state === 'NO_PROOF' || s.gap_days > 0
                    return (
                      <tr
                        key={s.source_id}
                        className={`border-b border-slate-800/70 ${flagged ? 'bg-amber-500/[0.04]' : ''}`}
                      >
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1.5">
                            {flagged && <TriangleAlert className="h-3 w-3 flex-shrink-0 text-amber-400" aria-hidden="true" />}
                            <span className="font-medium text-slate-200">{s.source_name || s.source_id}</span>
                          </div>
                          {s.gap_disclosure && (
                            <p className="mt-0.5 text-[11px] leading-tight text-amber-300/80">{s.gap_disclosure}</p>
                          )}
                        </td>
                        <td className="px-3 py-2.5"><StateChip state={s.change_state} /></td>
                        <td className="px-3 py-2.5 text-right font-mono tabular-nums text-slate-300">
                          {s.successful_checks}/{s.checks_in_period}
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono tabular-nums text-slate-300">
                          {s.days_with_proof_hash}/{s.expected_days}
                        </td>
                        <td className={`px-3 py-2.5 text-right font-mono tabular-nums ${s.gap_days > 0 ? 'text-amber-300' : 'text-slate-400'}`}>
                          {s.gap_days}
                        </td>
                        <td className="px-3 py-2.5 text-slate-400">{s.last_check_utc || 'none recorded'}</td>
                        <td className="px-3 py-2.5 font-mono text-[11px] text-slate-500">
                          {s.last_proof_hash ? String(s.last_proof_hash).slice(0, 14) : 'none'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 border-t border-slate-800 pt-3">
            <span className="text-[11px] text-slate-500">Download:</span>
            <button
              type="button"
              onClick={() => download('markdown')}
              disabled={!!downloading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white disabled:opacity-60"
            >
              <Download className="h-3.5 w-3.5" />
              {downloading === 'markdown' ? 'Preparing…' : 'Markdown'}
            </button>
            <button
              type="button"
              onClick={() => download('html')}
              disabled={!!downloading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white disabled:opacity-60"
            >
              <Download className="h-3.5 w-3.5" />
              {downloading === 'html' ? 'Preparing…' : 'HTML (printable)'}
            </button>
          </div>
        </div>
      )}

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-500" />
        <p className="text-[11px] leading-relaxed text-slate-500">
          Every number is derived from real recorded source-run evidence; a source with no checks in
          the period is shown as no coverage, never hidden. For monitoring information only. Not legal
          advice and not a guarantee of compliance.
        </p>
      </div>
    </div>
  )
}

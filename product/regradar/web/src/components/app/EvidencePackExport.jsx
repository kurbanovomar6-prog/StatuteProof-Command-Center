import { useState } from 'react'
import { Download, PackageCheck, ShieldCheck } from 'lucide-react'

import { reports } from '../../api'

function isoDaysAgo(days) {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - days)
  return d.toISOString().slice(0, 10)
}

/**
 * Self-serve Evidence Pack export.
 *
 * A sealed, self-verifiable ZIP of the caller's own evidence for the chosen
 * source + period: each record's raw and normalized snapshots, the recorded
 * hashes, a machine manifest, and a standalone verify.py the customer can run
 * offline. Mirrors the proven RegulatorBinderExport download flow.
 *
 * @param {{ sources?: { id: string, name: string }[] }} props
 */
export default function EvidencePackExport({ sources = [] }) {
  const [sourceId, setSourceId] = useState('')
  const [dateFrom, setDateFrom] = useState(isoDaysAgo(90))
  const [dateTo, setDateTo] = useState(isoDaysAgo(0))
  const [status, setStatus] = useState('idle') // idle | working | success | empty | error
  const [message, setMessage] = useState('')

  const effectiveSourceId = sourceId || sources[0]?.id || ''
  const hasSources = sources.length > 0
  const isWorking = status === 'working'

  async function handleExport() {
    if (!effectiveSourceId) {
      setStatus('error')
      setMessage('Select a source to export.')
      return
    }
    setStatus('working')
    setMessage('')
    try {
      const { blob, filename } = await reports.evidencePack({
        sourceIds: [effectiveSourceId],
        dateFrom,
        dateTo,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      const kb = (blob.size / 1024).toFixed(1)
      setMessage(`Evidence pack downloaded — ${filename} (${kb} KB)`)
      setStatus('success')
    } catch (err) {
      if (err.empty) {
        setStatus('empty')
        setMessage('No recorded evidence for this source in the selected period.')
      } else {
        setStatus('error')
        setMessage(err.message || 'Could not export the evidence pack.')
      }
    }
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-slate-500/10">
          <PackageCheck className="h-4 w-4 text-slate-300" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Evidence pack</h2>
          <p className="mt-0.5 max-w-2xl text-xs leading-relaxed text-slate-400">
            A sealed ZIP of your own evidence for this source and period — raw and normalized
            snapshots, the recorded hashes, and a standalone verify.py you can run offline.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Source</span>
          <select
            value={effectiveSourceId}
            onChange={event => setSourceId(event.target.value)}
            disabled={!hasSources || isWorking}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none disabled:opacity-60"
          >
            {!hasSources && <option value="">No sources with evidence yet</option>}
            {sources.map(source => (
              <option key={source.id} value={source.id}>{source.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">From</span>
          <input
            type="date"
            value={dateFrom}
            max={dateTo}
            onChange={event => setDateFrom(event.target.value)}
            disabled={isWorking}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none disabled:opacity-60"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">To</span>
          <input
            type="date"
            value={dateTo}
            min={dateFrom}
            onChange={event => setDateTo(event.target.value)}
            disabled={isWorking}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none disabled:opacity-60"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleExport}
          disabled={isWorking || !hasSources}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-colors ${
            isWorking || !hasSources
              ? 'cursor-not-allowed bg-slate-800 text-slate-500'
              : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
          }`}
        >
          <PackageCheck className="h-3.5 w-3.5" />
          {isWorking ? 'Building pack…' : 'Export evidence pack'}
        </button>

        {status === 'success' && (
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-300">
            <Download className="h-3.5 w-3.5" />
            {message}
          </span>
        )}
        {status === 'empty' && <span className="text-xs text-amber-300">{message}</span>}
        {status === 'error' && <span className="text-xs text-rose-300">{message}</span>}
      </div>

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-500" />
        <p className="text-[11px] leading-relaxed text-slate-500">
          The pack contains only your recorded evidence records and lets anyone re-check the hashes
          offline. For monitoring information only. Not legal advice and not a guarantee of compliance.
        </p>
      </div>
    </div>
  )
}

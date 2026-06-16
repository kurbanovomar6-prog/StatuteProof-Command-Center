import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ExternalLink, Filter, Search, ShieldCheck } from 'lucide-react'

import { reviews } from '../../api'

const STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending review' },
  { value: 'assessed', label: 'Assessed' },
  { value: 'all', label: 'All records' },
]

const HEALTH_OPTIONS = [
  { value: '', label: 'All health' },
  { value: 'MONITOR_OK', label: 'Monitor OK' },
  { value: 'HASH_DRIFT', label: 'Hash drift' },
  { value: 'QUALITY_DROP', label: 'Quality drop' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'ACCESS_BLOCKED', label: 'Access blocked' },
]

const CHANGE_OPTIONS = [
  { value: '', label: 'All changes' },
  { value: 'CHANGED', label: 'Changed' },
  { value: 'FIRST_SEEN', label: 'First seen' },
  { value: 'UNCHANGED', label: 'Unchanged' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'QUALITY_DROP', label: 'Quality drop' },
]

const HEALTH_STYLE = {
  MONITOR_OK: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  HASH_DRIFT: 'border-amber-400/25 bg-amber-400/10 text-amber-200',
  QUALITY_DROP: 'border-amber-400/25 bg-amber-400/10 text-amber-200',
  FAILED: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
  ACCESS_BLOCKED: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
}

function StatusPill({ value, children }) {
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold ${HEALTH_STYLE[value] || 'border-slate-700 bg-slate-900 text-slate-300'}`}>
      {children || value || 'UNKNOWN'}
    </span>
  )
}

export default function ReviewQueuePage() {
  const [status, setStatus] = useState('pending')
  const [sourceHealthStatus, setSourceHealthStatus] = useState('')
  const [changeStatus, setChangeStatus] = useState('')
  const [search, setSearch] = useState('')
  const [queueData, setQueueData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    reviews.queue({
      market: 'AE',
      status,
      source_health_status: sourceHealthStatus,
      change_status: changeStatus,
      limit: 100,
    })
      .then(data => {
        if (active) setQueueData(data)
      })
      .catch(err => {
        if (active) setError(err.message || 'Could not load review queue.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [status, sourceHealthStatus, changeStatus])

  const filteredRows = useMemo(() => (queueData?.queue || []).filter(row => {
    const haystack = [
      row.source_name,
      row.source_id,
      row.official_url,
      row.change_status,
      row.source_health_status,
      row.impact_level,
      row.reviewer,
    ].join(' ').toLowerCase()
    return !search || haystack.includes(search.toLowerCase())
  }), [queueData, search])

  return (
    <div className="min-h-full space-y-5 bg-[#07111F] p-5 pb-10">
      <div>
        <h1 className="text-lg font-bold text-white mb-1">Review Queue</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Evidence records requiring MLRO review. Rows are built from saved source-run evidence and Acknowledge & Assess records only.
        </p>
      </div>

      <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">MLRO review command center</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Filter by pending/assessed status, source health, and change status. Hash drift is a source-health review signal, not a regulatory conclusion.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Saved evidence only', 'A&A linked', 'No fake rows', 'Not legal advice'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto_auto]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search source, hash status, reviewer"
              value={search}
              onChange={event => setSearch(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <select value={status} onChange={event => setStatus(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none">
            {STATUS_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <select value={sourceHealthStatus} onChange={event => setSourceHealthStatus(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none">
            {HEALTH_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <select value={changeStatus} onChange={event => setChangeStatus(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none">
            {CHANGE_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-8 text-sm text-slate-400">
          Loading review queue...
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 px-5 py-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
          <div>
            <p className="text-sm font-semibold text-rose-200">Could not load review queue.</p>
            <p className="mt-1 text-xs text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && filteredRows.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/35 px-6 py-12 text-center">
          <Filter className="mx-auto mb-3 h-8 w-8 text-slate-600" />
          <p className="text-sm font-semibold text-white">No pending reviews.</p>
          <p className="mx-auto mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Evidence records appear here after source runs are saved. Assessed records can be viewed by switching the status filter.
          </p>
        </div>
      )}

      {!loading && !error && filteredRows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0D1B2E]">
          <table className="sp-table min-w-[1050px]">
            <thead>
              <tr>
                {['Source', 'Change', 'Source health', 'Quality', 'Hash', 'Assessment', 'Reviewer', 'Actions'].map(header => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredRows.map(row => (
                <tr key={row.evidence_record_id} className="hover:bg-slate-800/35">
                  <td className="max-w-[280px]">
                    <p className="truncate font-semibold text-white">{row.source_name || row.source_id}</p>
                    <p className="mt-1 text-[11px] text-slate-500">{row.timestamp_utc || 'No timestamp'}</p>
                  </td>
                  <td>
                    <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold text-cyan-200">
                      {row.change_status || 'UNKNOWN'}
                    </span>
                  </td>
                  <td><StatusPill value={row.source_health_status} /></td>
                  <td className="text-slate-300">{row.extraction_quality || 'UNKNOWN'}</td>
                  <td className="sp-mono text-slate-400">{row.normalized_hash_short || 'not recorded'}</td>
                  <td>
                    {row.pending_review ? (
                      <span className="rounded-full border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold text-amber-200">Pending</span>
                    ) : (
                      <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-200">
                        {row.impact_level || row.assessment_status || 'Assessed'}
                      </span>
                    )}
                  </td>
                  <td className="text-slate-400">{row.reviewer || '—'}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <a href="/app/evidence" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200">Evidence</a>
                      {row.official_url && (
                        <a href={row.official_url} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-slate-300" title="Open official source">
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-500" />
        <p className="text-xs leading-relaxed text-slate-500">
          Monitoring intelligence only. Not legal advice. The queue helps record human review decisions; it does not determine legal obligations or compliance outcomes.
        </p>
      </div>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Ban, CheckCircle, ExternalLink, Filter, Search, ShieldCheck, XCircle } from 'lucide-react'

import { reviews } from '../../api'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import EmptyState from './ui/EmptyState'
import ErrorState from './ui/ErrorState'

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


export default function ReviewQueuePage() {
  const [status, setStatus] = useState('pending')
  const [sourceHealthStatus, setSourceHealthStatus] = useState('')
  const [changeStatus, setChangeStatus] = useState('')
  const [search, setSearch] = useState('')
  const [queueData, setQueueData] = useState(null)
  const [canonicalData, setCanonicalData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [canonicalLoading, setCanonicalLoading] = useState(true)
  const [error, setError] = useState('')
  const [canonicalError, setCanonicalError] = useState('')
  const [reviewNotes, setReviewNotes] = useState({})
  const [reviewState, setReviewState] = useState({})

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

  const loadCanonicalEvidence = () => {
    setCanonicalLoading(true)
    setCanonicalError('')
    let active = true
    reviews.canonicalEvidence()
      .then(data => { if (active) setCanonicalData(data) })
      .catch(err => { if (active) setCanonicalError(err.message || 'Could not load canonical evidence records.') })
      .finally(() => { if (active) setCanonicalLoading(false) })
    return () => { active = false }
  }

  useEffect(() => {
    let active = true
    setCanonicalLoading(true)
    reviews.canonicalEvidence()
      .then(data => {
        if (active) setCanonicalData(data)
      })
      .catch(err => {
        if (active) setCanonicalError(err.message || 'Could not load canonical evidence records.')
      })
      .finally(() => {
        if (active) setCanonicalLoading(false)
      })
    return () => { active = false }
  }, [])

  const canonicalRows = canonicalData?.records || []

  const submitCanonicalReview = async (recordId, decision) => {
    const note = (reviewNotes[recordId] || '').trim()
    if (!note) {
      setReviewState(prev => ({ ...prev, [recordId]: { status: 'error', message: 'Reviewer note required.' } }))
      return
    }
    setReviewState(prev => ({ ...prev, [recordId]: { status: 'saving', message: '' } }))
    try {
      const result = await reviews.reviewCanonicalEvidence({ record_id: recordId, decision, note })
      setReviewState(prev => ({
        ...prev,
        [recordId]: {
          status: 'ok',
          message: result.brief_eligible
            ? 'Review saved. Draft brief input gate is eligible.'
            : result.blocked_reason || 'Review saved. Brief gate remains blocked.',
        },
      }))
      setReviewNotes(prev => ({ ...prev, [recordId]: '' }))
      loadCanonicalEvidence()
    } catch (err) {
      setReviewState(prev => ({ ...prev, [recordId]: { status: 'error', message: err.message || 'Could not save review.' } }))
    }
  }

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
            <h2 className="text-sm font-semibold text-white">MLRO review</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Filter by review status, source health, and change status. Rows are built only from
              saved evidence records; hash drift is a source-health signal, not a regulatory conclusion.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
        <div className="mb-3 flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Canonical evidence review</h2>
            <p className="mt-1 max-w-3xl text-xs leading-relaxed text-slate-400">
              Append-only review decisions for canonical evidence records. Approval can unlock draft-only brief inputs; customer delivery remains separately blocked.
            </p>
          </div>
          {canonicalData?.counts && (
            <div className="flex flex-wrap gap-2 text-[11px] font-semibold">
              <span className="rounded-full border border-amber-400/25 bg-amber-400/10 px-2 py-1 text-amber-200">Pending {canonicalData.counts.pending}</span>
              <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-1 text-emerald-200">Approved {canonicalData.counts.approved}</span>
              <span className="rounded-full border border-rose-400/25 bg-rose-400/10 px-2 py-1 text-rose-200">Rejected {canonicalData.counts.rejected}</span>
              <span className="rounded-full border border-slate-600 bg-slate-900 px-2 py-1 text-slate-300">Blocked {canonicalData.counts.blocked}</span>
            </div>
          )}
        </div>

        {canonicalLoading && <p className="text-sm text-slate-400">Loading canonical evidence records...</p>}
        {!canonicalLoading && canonicalError && (
          <ErrorState
            title="Could not load canonical evidence records."
            detail={canonicalError}
            onRetry={loadCanonicalEvidence}
            className="rounded-lg border border-slate-800 bg-slate-950/35"
          />
        )}
        {!canonicalLoading && !canonicalError && canonicalRows.length === 0 && (
          <EmptyState
            icon={CheckCircle}
            title="No canonical evidence records yet."
            className="rounded-lg border border-slate-800 bg-slate-950/35"
          >
            Canonical records appear after monitoring runs save evidence for
            review. Run a source check or adjust filters above.
          </EmptyState>
        )}
        {!canonicalLoading && !canonicalError && canonicalRows.length > 0 && (
          <div>
            <div className="grid gap-3 lg:hidden">
              {canonicalRows.map((row, rowIndex) => {
                const state = reviewState[row.record_id]
                const isSaving = state?.status === 'saving'
                return (
                  <article key={`${row.record_id}-${rowIndex}`} className="sp-mobile-card">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="sp-mono truncate text-xs text-slate-300">{row.record_id}</p>
                        <p className="mt-1 text-sm font-semibold text-white">{row.source_id || 'Unknown source'}</p>
                        <p className="text-xs text-slate-500">{row.regulator || 'Unknown regulator'} · {row.run_status || 'UNKNOWN'}</p>
                      </div>
                      <StatusBadge code={row.record_review_status || 'pending'} />
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Record path</p>
                      <p className="mt-1 break-all text-xs text-slate-400">{row.record_path}</p>
                    </div>
                    <div className="mt-3">
                      <label className="mb-1.5 block text-xs font-semibold text-slate-400">Reviewer note</label>
                      <input
                        type="text"
                        value={reviewNotes[row.record_id] || ''}
                        onChange={event => setReviewNotes(prev => ({ ...prev, [row.record_id]: event.target.value }))}
                        placeholder="Required before decision"
                        className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
                      />
                      {state?.message && (
                        <p className={`mt-1 text-[11px] ${state.status === 'error' ? 'text-rose-300' : 'text-emerald-300'}`}>{state.message}</p>
                      )}
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => submitCanonicalReview(row.record_id, 'approved')}
                        className="rounded-lg border border-emerald-400/25 bg-emerald-400/10 px-3 py-2 text-xs font-semibold text-emerald-200 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => submitCanonicalReview(row.record_id, 'rejected')}
                        className="rounded-lg border border-rose-400/25 bg-rose-400/10 px-3 py-2 text-xs font-semibold text-rose-200 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Reject
                      </button>
                      <button
                        type="button"
                        disabled={isSaving}
                        onClick={() => submitCanonicalReview(row.record_id, 'blocked')}
                        className="rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-xs font-semibold text-slate-300 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Block
                      </button>
                    </div>
                  </article>
                )
              })}
            </div>

            <div className="hidden overflow-x-auto rounded-lg border border-slate-800 lg:block">
              <table className="sp-table w-full">
              <thead>
                <tr>
                  {['Record', 'Source', 'Run', 'Record review', 'Latest decision', 'Reviewer note', 'Decision'].map(header => (
                    <th key={header}>{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {canonicalRows.map((row, rowIndex) => {
                  const state = reviewState[row.record_id]
                  const isSaving = state?.status === 'saving'
                  return (
                    <tr key={`${row.record_id}-${rowIndex}`} className="hover:bg-slate-800/35">
                      <td className="max-w-[220px]">
                        <p className="sp-mono truncate text-xs text-slate-300" title={row.record_id}>{row.record_id}</p>
                        <p className="mt-1 truncate text-[11px] text-slate-500" title={row.record_path}>{row.record_path}</p>
                      </td>
                      <td>
                        <p className="font-semibold text-white">{row.source_id || 'Unknown source'}</p>
                        <p className="mt-1 text-[11px] text-slate-500">{row.regulator || 'Unknown regulator'}</p>
                      </td>
                      <td>
                        <StatusBadge code={row.run_status || 'NOT_RUN'} />
                      </td>
                      <td><StatusBadge code={row.record_review_status || 'pending'} /></td>
                      <td><StatusBadge code={row.latest_review_decision || 'none'} /></td>
                      <td className="min-w-[180px]">
                        <input
                          type="text"
                          value={reviewNotes[row.record_id] || ''}
                          onChange={event => setReviewNotes(prev => ({ ...prev, [row.record_id]: event.target.value }))}
                          placeholder="Reviewer note required"
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
                        />
                        {state?.message && (
                          <p className={`mt-1 text-[11px] ${state.status === 'error' ? 'text-rose-300' : 'text-emerald-300'}`}>{state.message}</p>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            title="Approve canonical evidence for draft brief inputs"
                            disabled={isSaving}
                            onClick={() => submitCanonicalReview(row.record_id, 'approved')}
                            className="rounded-lg border border-emerald-400/25 bg-emerald-400/10 p-2 text-emerald-200 hover:bg-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <CheckCircle className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            title="Reject canonical evidence"
                            disabled={isSaving}
                            onClick={() => submitCanonicalReview(row.record_id, 'rejected')}
                            className="rounded-lg border border-rose-400/25 bg-rose-400/10 p-2 text-rose-200 hover:bg-rose-400/15 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            title="Block canonical evidence pending remediation"
                            disabled={isSaving}
                            onClick={() => submitCanonicalReview(row.record_id, 'blocked')}
                            className="rounded-lg border border-slate-600 bg-slate-900 p-2 text-slate-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Ban className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              </table>
            </div>
          </div>
        )}
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
        <div>
          <div className="grid gap-3 lg:hidden">
            {filteredRows.map((row, rowIndex) => (
              <article key={`${row.evidence_record_id}-${rowIndex}`} className="sp-mobile-card">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white">{row.source_name || row.source_id}</p>
                    <TimeStamp value={row.timestamp_utc} mode="absolute" fallback="No timestamp" className="mt-1 block text-xs text-slate-500" />
                  </div>
                  <StatusBadge code={row.change_status || 'NOT_RUN'} />
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
                    <p className="text-slate-500">Source health</p>
                    <div className="mt-1"><StatusBadge code={row.source_health_status || 'NOT_RUN'} /></div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
                    <p className="text-slate-500">Quality</p>
                    <p className="mt-1 font-semibold text-slate-300">{row.extraction_quality ? String(row.extraction_quality).toLowerCase().replace(/^./, c => c.toUpperCase()) : 'Unknown'}</p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
                    <p className="text-slate-500">Hash</p>
                    <p className="sp-mono mt-1 truncate text-slate-300">{row.normalized_hash_short || 'not recorded'}</p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
                    <p className="text-slate-500">Assessment</p>
                    <p className="mt-1 font-semibold text-amber-200">{row.pending_review ? 'Pending' : row.impact_level || row.assessment_status || 'Assessed'}</p>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between gap-3">
                  <a href="/app/evidence" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200">Open evidence</a>
                  {row.official_url && (
                    <a href={row.official_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-slate-200">
                      Official source <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </article>
            ))}
          </div>

          <div className="hidden overflow-x-auto rounded-xl border border-slate-800 bg-[#0D1B2E] lg:block">
            <table className="sp-table w-full">
            <thead>
              <tr>
                {['Source', 'Change', 'Source health', 'Quality', 'Hash', 'Assessment', 'Reviewer', 'Actions'].map(header => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredRows.map((row, rowIndex) => (
                <tr key={`${row.evidence_record_id}-${rowIndex}`} className="hover:bg-slate-800/35">
                  <td className="max-w-[280px]">
                    <p className="truncate font-semibold text-white">{row.source_name || row.source_id}</p>
                    <TimeStamp value={row.timestamp_utc} mode="absolute" fallback="No timestamp" className="mt-1 block text-[11px] text-slate-500" />
                  </td>
                  <td>
                    <StatusBadge code={row.change_status || 'NOT_RUN'} />
                  </td>
                  <td><StatusBadge code={row.source_health_status || 'NOT_RUN'} /></td>
                  <td className="text-slate-300">{row.extraction_quality ? String(row.extraction_quality).toLowerCase().replace(/^./, c => c.toUpperCase()) : 'Unknown'}</td>
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

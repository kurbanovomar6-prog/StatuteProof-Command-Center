import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle, Clock, Download, FileText, Hash, History, Loader2, Shield } from 'lucide-react'

import { evidence as evidenceApi } from '../../api'

const STATUS_STYLES = {
  CHANGED:      { bg: 'bg-blue-500/10 border-blue-500/30',     text: 'text-blue-400',   label: 'CHANGED' },
  UNCHANGED:    { bg: 'bg-slate-700/30 border-slate-600/30',   text: 'text-slate-400',  label: 'UNCHANGED' },
  FIRST_SEEN:   { bg: 'bg-violet-500/10 border-violet-500/30', text: 'text-violet-400', label: 'FIRST SEEN' },
  FAILED:       { bg: 'bg-red-500/10 border-red-500/30',       text: 'text-red-400',    label: 'FAILED' },
  QUALITY_DROP: { bg: 'bg-amber-500/10 border-amber-500/30',   text: 'text-amber-400',  label: 'QUALITY DROP' },
}

const IMPACT_OPTIONS = [
  ['monitor', 'Monitor'],
  ['no_impact', 'No impact'],
  ['policy_review', 'Policy review'],
  ['escalate', 'Escalate'],
  ['external_counsel_review', 'External counsel review'],
]

function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.UNCHANGED
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  )
}

function EvidenceCard({ record }) {
  const [impactLevel, setImpactLevel] = useState('monitor')
  const [internalNote, setInternalNote] = useState('')
  const [nextAction, setNextAction] = useState('')
  const [assessment, setAssessment] = useState(record.assessment || null)
  const [assessmentMsg, setAssessmentMsg] = useState('')
  const [exportMsg, setExportMsg] = useState('')
  const [reviewHistory, setReviewHistory] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(Boolean(record.evidence_record_id))
  const [historyError, setHistoryError] = useState('')
  const [saving, setSaving] = useState(false)
  const [exportingFormat, setExportingFormat] = useState('')
  const canAssess = Boolean(record.proof_block_path && record.evidence_record_id)
  const detectedDate = record.detected_at
    ? new Date(record.detected_at).toLocaleString('en-GB', { timeZone: 'UTC', dateStyle: 'medium', timeStyle: 'short' }) + ' UTC'
    : 'Not recorded'

  useEffect(() => {
    if (!record.evidence_record_id) return
    let active = true
    evidenceApi.reviewHistory(record.evidence_record_id)
      .then(data => {
        if (!active) return
        setReviewHistory(data)
        if (data.latest_assessment) setAssessment(data.latest_assessment)
      })
      .catch(err => {
        if (!active) return
        setReviewHistory(null)
        setHistoryError(err.message || 'Review history could not be loaded.')
      })
      .finally(() => {
        if (active) setHistoryLoading(false)
      })
    return () => { active = false }
  }, [record.evidence_record_id])

  async function refreshReviewHistory() {
    if (!record.evidence_record_id) return
    try {
      const data = await evidenceApi.reviewHistory(record.evidence_record_id)
      setReviewHistory(data)
      if (data.latest_assessment) setAssessment(data.latest_assessment)
    } catch (err) {
      setHistoryError(err.message || 'Review history could not be refreshed.')
    }
  }

  async function handleAssess() {
    if (!canAssess || !internalNote.trim()) return
    setSaving(true)
    setAssessmentMsg('')
    try {
      const data = await evidenceApi.assess({
        evidence_record_id: record.evidence_record_id,
        impact_level: impactLevel,
        internal_note: internalNote,
        next_action: nextAction,
      })
      setAssessment(data.assessment)
      setAssessmentMsg('Assessment saved against the evidence record.')
      await refreshReviewHistory()
    } catch (err) {
      setAssessmentMsg(err.message || 'Assessment could not be saved.')
    } finally {
      setSaving(false)
    }
  }

  async function handleExport(format = 'pdf') {
    if (!record.evidence_record_id) return
    setExportingFormat(format)
    setExportMsg('')
    try {
      const data = await evidenceApi.exportAuditPack(record.evidence_record_id, format)
      const paths = data.export || {}
      const artifactPath = data.format === 'pdf'
        ? paths.pdf_path || data.pdf_path || 'PDF path unavailable'
        : paths.md_path || paths.html_path || 'Markdown/HTML path unavailable'
      setExportMsg(`${data.message || 'Audit pack exported.'} ${artifactPath}`)
    } catch (err) {
      setExportMsg(err.message || 'Audit export failed.')
    } finally {
      setExportingFormat('')
    }
  }

  return (
    <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-1 inline-flex rounded-md border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
            LIVE EVIDENCE RECORD
          </div>
          <h3 className="text-sm font-semibold text-white">{record.source}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{record.regulator} · {record.evidence_record_id}</p>
        </div>
        <StatusBadge status={record.status} />
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Checked
          </p>
          <p className="text-slate-200 font-medium">{detectedDate}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5">Source health</p>
          <p className="text-slate-200 font-medium">{record.source_health_status}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5 flex items-center gap-1">
            <Hash className="w-3 h-3" /> Normalized hash
          </p>
          <p className="text-slate-400 font-mono truncate">{record.new_hash || 'Not recorded'}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5">Proof path</p>
          <p className={record.proof_block_path ? 'text-cyan-300 truncate' : 'text-amber-300'}>
            {record.proof_block_path || 'No proof artifact linked'}
          </p>
        </div>
      </div>

      <div className="text-xs space-y-2">
        {record.official_url && (
          <div className="flex gap-2">
            <span className="text-slate-500 w-20 flex-shrink-0">Source:</span>
            <a href={record.official_url} target="_blank" rel="noopener noreferrer" className="text-[#16D9F5] hover:underline truncate">
              {record.official_url}
            </a>
          </div>
        )}
        <div className="flex gap-2">
          <span className="text-slate-500 w-20 flex-shrink-0">Diff:</span>
          <span className={record.diff_available ? 'text-emerald-400' : 'text-slate-500'}>
            {record.diff_available ? 'Available' : 'Not available'}
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-semibold text-white">Acknowledge & Assess</h4>
            <p className="mt-1 text-[11px] text-slate-500">Saved evidence only. This records an internal review note, not legal advice.</p>
          </div>
          {assessment ? <span className="text-[10px] font-bold text-emerald-300">ASSESSMENT SAVED</span> : null}
        </div>
        {!canAssess ? (
          <p className="text-xs text-amber-300">
            Assessment disabled because this record does not have a saved proof artifact.
          </p>
        ) : (
          <div className="space-y-2">
            <select
              value={impactLevel}
              onChange={event => setImpactLevel(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200"
            >
              {IMPACT_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <textarea
              value={internalNote}
              onChange={event => setInternalNote(event.target.value)}
              placeholder="Internal impact note"
              className="min-h-[80px] w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600"
            />
            <input
              value={nextAction}
              onChange={event => setNextAction(event.target.value)}
              placeholder="Next action (optional)"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600"
            />
            <button
              type="button"
              onClick={handleAssess}
              disabled={saving || !internalNote.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-400/25 px-3 py-2 text-xs font-semibold text-cyan-200 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-600"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5" />}
              Save assessment
            </button>
            {assessmentMsg && <p className="text-xs text-slate-400">{assessmentMsg}</p>}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h4 className="flex items-center gap-1.5 text-xs font-semibold text-white">
              <History className="h-3.5 w-3.5 text-[#16D9F5]" />
              Review History
            </h4>
            <p className="mt-1 text-[11px] text-slate-500">Only saved evidence and recorded assessment events are shown.</p>
          </div>
          {reviewHistory?.total_events ? (
            <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-semibold text-slate-300">
              {reviewHistory.total_events} events
            </span>
          ) : null}
        </div>
        {historyLoading ? (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Loading review history…
          </div>
        ) : historyError ? (
          <p className="text-xs text-amber-300">{historyError}</p>
        ) : reviewHistory?.events?.length ? (
          <div className="space-y-2">
            {reviewHistory.events.map(event => (
              <div key={event.event_id} className="rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2">
                <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[11px] font-bold text-slate-200">{event.event_type}</span>
                  <span className="text-[10px] text-slate-500">{event.timestamp || 'Timestamp not recorded'}</span>
                </div>
                <p className="text-[11px] leading-relaxed text-slate-400">{event.customer_safe_message}</p>
                {event.assessment_impact_level && (
                  <p className="mt-1 text-[11px] text-emerald-300">
                    Impact: {event.assessment_impact_level}
                    {event.assessment_note_preview ? ` · ${event.assessment_note_preview}` : ''}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">
            No review history has been recorded yet. Use Acknowledge & Assess after confirming this saved evidence record.
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => handleExport('pdf')}
          disabled={Boolean(exportingFormat) || !record.evidence_record_id}
          className="inline-flex items-center gap-1.5 rounded-lg bg-[#16D9F5] px-3 py-2 text-xs font-semibold text-[#07111F] disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-500"
        >
          {exportingFormat === 'pdf' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
          Export PDF audit pack
        </button>
        <button
          type="button"
          onClick={() => handleExport('md_html')}
          disabled={Boolean(exportingFormat) || !record.evidence_record_id}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 disabled:cursor-not-allowed disabled:border-slate-800 disabled:text-slate-600"
        >
          {exportingFormat === 'md_html' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
          Export Markdown/HTML
        </button>
        {exportMsg && <span className="text-xs text-slate-400">{exportMsg}</span>}
      </div>

      <p className="text-[10px] text-slate-600 border-t border-slate-800 pt-3">
        Monitoring intelligence only. Not legal advice. Evidence records support compliance review and do not determine legal obligations.
      </p>
    </div>
  )
}

function sourceHealthStatus(record) {
  if (record.change_status === 'FAILED' || record.change_status === 'QUALITY_DROP') return record.change_status
  if (record.access_status === 'failed' || record.access_status === 'restricted') return String(record.access_status || '').toUpperCase()
  return 'MONITOR_OK'
}

function mapEvidenceRecord(record, index) {
  return {
    evidence_record_id: record.evidence_record_id || record.run_id || `EVR-LIVE-${index + 1}`,
    source: record.source_name || record.source_id || 'Official source',
    source_id: record.source_id,
    regulator: record.category || 'AE source',
    detected_at: record.timestamp_utc,
    run_id: record.run_id,
    status: record.change_status || 'UNCHANGED',
    new_hash: record.normalized_hash || record.content_hash ? `sha256:${String(record.normalized_hash || record.content_hash)}` : null,
    diff_available: Boolean(record.diff_json_path || record.diff_md_path || record.change_status === 'CHANGED'),
    proof_block_path: record.proof_block_path || '',
    official_url: record.official_url || '',
    source_health_status: sourceHealthStatus(record),
    is_sample: false,
  }
}

export default function EvidencePage() {
  const [records, setRecords] = useState([])
  const [apiChecked, setApiChecked] = useState(false)
  const [apiError, setApiError] = useState('')

  useEffect(() => {
    let active = true
    evidenceApi.list('AE', 100)
      .then(data => {
        if (!active) return
        setRecords(Array.isArray(data.evidence) ? data.evidence.map(mapEvidenceRecord) : [])
        setApiError('')
      })
      .catch(err => {
        if (!active) return
        setRecords([])
        setApiError(err.message || 'Could not load live evidence records.')
      })
      .finally(() => {
        if (active) setApiChecked(true)
      })
    return () => { active = false }
  }, [])

  return (
    <div className="p-5 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-white mb-1">Evidence Records</h1>
          <p className="text-sm text-slate-400">
            Live monitored source runs with hashes, proof paths, source-health status, Acknowledge & Assess, and audit-pack export.
          </p>
        </div>
        <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full flex-shrink-0 text-emerald-300 bg-emerald-400/10 border border-emerald-400/20">
          <Shield className="w-3.5 h-3.5" />
          LIVE API ONLY
        </span>
      </div>

      <div className="bg-[#0D1B2E] border border-cyan-400/20 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-[#16D9F5] flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-sm font-semibold text-white mb-1">About evidence records</h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
              Evidence records are live source-run records. StatuteProof does not show sample hashes or fake alerts in this authenticated view.
              Acknowledge & Assess is available only when a saved proof artifact exists. Monitoring intelligence only. Not legal advice.
            </p>
          </div>
        </div>
      </div>

      {!apiChecked ? (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-10 text-center">
          <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-[#16D9F5]" />
          <p className="text-sm text-slate-400">Loading live evidence records…</p>
        </div>
      ) : apiError ? (
        <div className="flex items-center gap-2 rounded-lg border border-amber-400/25 bg-amber-400/5 px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">
            {apiError} No sample evidence is shown in authenticated workspace.
          </p>
        </div>
      ) : records.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-10 text-center">
          <FileText className="mx-auto mb-3 h-5 w-5 text-slate-500" />
          <p className="font-medium text-slate-300">No live evidence records yet</p>
          <p className="mt-2 text-sm text-slate-500">
            Evidence records appear after monitored sources produce saved run records with hashes and proof artifacts.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {records.map((record, index) => (
            <EvidenceCard key={`${record.evidence_record_id}-${index}`} record={record} />
          ))}
        </div>
      )}

      <p className="text-xs text-slate-600 text-center leading-relaxed">
        StatuteProof reports are for information and compliance review support only. Not legal advice.
        Users should verify official source material directly and consult qualified professionals before making regulatory decisions.
      </p>
    </div>
  )
}

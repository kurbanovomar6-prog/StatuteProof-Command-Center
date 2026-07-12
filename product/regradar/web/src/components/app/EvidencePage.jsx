import { useEffect, useState } from 'react'
import { Check, CheckCircle, Clock, Copy, Download, FileText, Hash, History, Loader2, Shield } from 'lucide-react'

import { apiFetch, evidence as evidenceApi } from '../../api'
import DiffViewer from '../DiffViewer'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import ErrorState from './ui/ErrorState'
import { formatGst } from '../../utils/time'

// Pull the server-provided filename from Content-Disposition, or fall back.
function filenameFromResponse(response, fallback) {
  const disposition = response.headers?.get?.('content-disposition') || ''
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)
  if (match && match[1]) {
    try {
      return decodeURIComponent(match[1])
    } catch {
      return match[1]
    }
  }
  return fallback
}

const IMPACT_OPTIONS = [
  ['monitor', 'Monitor'],
  ['no_impact', 'No impact'],
  ['policy_review', 'Policy review'],
  ['escalate', 'Escalate'],
  ['external_counsel_review', 'External counsel review'],
]

function CopyHashButton({ value }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      title="Copy full fingerprint"
      aria-label={copied ? 'Full fingerprint copied' : 'Copy full fingerprint'}
      className="flex-shrink-0 rounded p-1 text-[var(--text-secondary)] transition-colors hover:text-[var(--accent)]"
    >
      {copied ? <Check className="h-3 w-3 text-emerald-300" /> : <Copy className="h-3 w-3" />}
    </button>
  )
}

function EvidenceCard({ record }) {
  const [impactLevel, setImpactLevel] = useState('monitor')
  const [internalNote, setInternalNote] = useState('')
  const [nextAction, setNextAction] = useState('')
  const [assessment, setAssessment] = useState(record.assessment || null)
  const [assessmentMsg, setAssessmentMsg] = useState('')
  const [exportMsg, setExportMsg] = useState('')
  const [exportError, setExportError] = useState('') // holds the format that failed, '' when none
  const [reviewHistory, setReviewHistory] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(Boolean(record.evidence_record_id))
  const [historyError, setHistoryError] = useState('')
  const [saving, setSaving] = useState(false)
  const [exportingFormat, setExportingFormat] = useState('')
  const [diffText, setDiffText] = useState(null)
  const [diffLoading, setDiffLoading] = useState(false)
  const [diffError, setDiffError] = useState('')
  const [diffExpanded, setDiffExpanded] = useState(false)
  const canAssess = Boolean(record.evidence_record_id)
  const detectedDate = formatGst(record.detected_at) || 'Not recorded'

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

  async function handleLoadDiff() {
    if (!record.run_id || diffLoading) return
    if (diffText !== null) {
      setDiffExpanded(v => !v)
      return
    }
    setDiffLoading(true)
    setDiffError('')
    try {
      const data = await evidenceApi.fetchDiff(record.run_id)
      setDiffText(data.diff_text || '')
      setDiffExpanded(true)
    } catch (err) {
      setDiffError(err.message || 'Diff could not be loaded.')
    } finally {
      setDiffLoading(false)
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
    setExportError('')
    const downloadUrl = `/api/evidence/export-download?evidence_record_id=${encodeURIComponent(record.evidence_record_id)}&format=${encodeURIComponent(format)}`
    try {
      // Fetch the file first so we only claim a download after the bytes really arrive.
      const response = await apiFetch(downloadUrl)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const blob = await response.blob()
      if (!blob || blob.size === 0) throw new Error('Empty export')
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = filenameFromResponse(response, `statuteproof-audit-pack-${record.evidence_record_id}`)
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(objectUrl)
      setExportMsg('Download started. Check your downloads folder.')
    } catch {
      // Never claim a download that did not happen.
      setExportError(format)
    } finally {
      setExportingFormat('')
    }
  }

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-1 inline-flex rounded-md border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
            LIVE EVIDENCE RECORD
          </div>
          <h3 className="text-sm font-semibold text-white">{record.source}</h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">{record.regulator} · {record.evidence_record_id}</p>
        </div>
        <StatusBadge code={record.status} />
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
          <p className="text-[var(--text-muted)] mb-0.5 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Checked
          </p>
          <p className="text-[var(--text-primary)] font-medium">{detectedDate}</p>
        </div>
        <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
          <p className="text-[var(--text-muted)] mb-0.5">Source health</p>
          <StatusBadge code={record.source_health_status} />
        </div>
        <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
          <p className="text-[var(--text-muted)] mb-0.5 flex items-center gap-1" title="Tamper-evident fingerprint of the captured text">
            <Hash className="w-3 h-3" /> Normalized hash
          </p>
          <div className="flex items-center gap-1.5">
            <p className="text-[var(--text-secondary)] font-mono truncate" title={record.new_hash || 'Not recorded'}>{record.new_hash || 'Not recorded'}</p>
            {record.new_hash && <CopyHashButton value={record.new_hash} />}
          </div>
        </div>
        <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
          <p className="text-[var(--text-muted)] mb-0.5" title="Stored evidence file an auditor can open">Proof path</p>
          <p
            className={record.proof_block_path ? 'text-[var(--accent)] truncate' : 'text-[var(--text-secondary)]'}
            title={record.proof_block_path ? undefined : 'Expected while a run is still being validated.'}
          >
            {record.proof_block_path || 'No proof file linked yet'}
          </p>
        </div>
      </div>

      <div className="text-xs space-y-2">
        {record.official_url && (
          <div className="flex gap-2">
            <span className="text-[var(--text-muted)] w-20 flex-shrink-0">Source:</span>
            <a href={record.official_url} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline truncate">
              {record.official_url}
            </a>
          </div>
        )}
        <div className="flex gap-2">
          <span className="text-[var(--text-muted)] w-20 flex-shrink-0">Diff:</span>
          {record.diff_available ? (
            <button
              type="button"
              onClick={handleLoadDiff}
              className="text-[var(--accent)] hover:text-[var(--accent)] transition-colors"
            >
              {diffLoading ? 'Loading…' : diffExpanded ? 'Hide diff' : 'View diff'}
            </button>
          ) : (
            <span className="text-[var(--text-muted)]">Not available</span>
          )}
        </div>
        {diffError && (
          <p className="text-xs text-amber-300">{diffError}</p>
        )}
        {diffExpanded && diffText !== null && (
          <DiffViewer
            diffText={diffText}
            sourceId={record.source_id}
            detectedAt={detectedDate}
          />
        )}
      </div>

      <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-semibold text-white">Acknowledge & Assess</h4>
            <p className="mt-1 text-[11px] text-[var(--text-secondary)]">Saved evidence only. This records an internal review note, not legal advice.</p>
          </div>
          {assessment ? <span className="text-[10px] font-bold text-emerald-300">ASSESSMENT SAVED</span> : null}
        </div>
        {!canAssess ? (
          <p className="text-xs text-amber-300">
            Assessment requires an evidence record ID. This record has not been assigned one yet.
          </p>
        ) : (
          <div className="space-y-2">
            <select
              value={impactLevel}
              onChange={event => setImpactLevel(event.target.value)}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-primary)]"
            >
              {IMPACT_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <textarea
              value={internalNote}
              onChange={event => setInternalNote(event.target.value)}
              placeholder="Internal impact note"
              className="min-h-[80px] w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
            />
            <input
              value={nextAction}
              onChange={event => setNextAction(event.target.value)}
              placeholder="Next action (optional)"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
            />
            <button
              type="button"
              onClick={handleAssess}
              disabled={saving || !internalNote.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] px-3 py-2 text-xs font-semibold text-[var(--accent)] disabled:cursor-not-allowed disabled:border-[var(--border)] disabled:text-[var(--text-muted)]"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5" />}
              Save assessment
            </button>
            {assessmentMsg && <p className="text-xs text-[var(--text-secondary)]">{assessmentMsg}</p>}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <h4 className="flex items-center gap-1.5 text-xs font-semibold text-white">
              <History className="h-3.5 w-3.5 text-[var(--accent)]" />
              Review History
            </h4>
            <p className="mt-1 text-[11px] text-[var(--text-muted)]">Only saved evidence and recorded assessment events are shown.</p>
          </div>
          {reviewHistory?.total_events ? (
            <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-[10px] font-semibold text-[var(--text-primary)]">
              {reviewHistory.total_events} events
            </span>
          ) : null}
        </div>
        {historyLoading ? (
          <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Loading review history…
          </div>
        ) : historyError ? (
          <p className="text-xs text-amber-300">{historyError}</p>
        ) : reviewHistory?.events?.length ? (
          <div className="space-y-2">
            {reviewHistory.events.map(event => (
              <div key={event.event_id} className="rounded-md border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-3 py-2">
                <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[11px] font-bold text-[var(--text-primary)]">{event.event_type}</span>
                  <TimeStamp value={event.timestamp} mode="absolute" fallback="Timestamp not recorded" className="text-[10px] text-[var(--text-muted)]" />
                </div>
                <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">{event.customer_safe_message}</p>
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
          <p className="text-xs text-[var(--text-muted)]">
            No review history has been recorded yet. Use Acknowledge & Assess after confirming this saved evidence record.
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => handleExport('pdf')}
          disabled={Boolean(exportingFormat) || !record.evidence_record_id}
          className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent)] px-3 py-2 text-xs font-semibold text-[var(--ink)] disabled:cursor-not-allowed disabled:bg-[var(--bg-tooltip)] disabled:text-[var(--text-muted)]"
        >
          {exportingFormat === 'pdf' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
          Export PDF audit pack
        </button>
        <button
          type="button"
          onClick={() => handleExport('md_html')}
          disabled={Boolean(exportingFormat) || !record.evidence_record_id}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] disabled:cursor-not-allowed disabled:border-[var(--border-muted)] disabled:text-[var(--text-muted)]"
        >
          {exportingFormat === 'md_html' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
          Export Markdown/HTML
        </button>
        {exportMsg && <span className="text-xs text-emerald-300">{exportMsg}</span>}
        {exportError && (
          <span className="inline-flex items-center gap-2 text-xs text-rose-300">
            Export failed — nothing was downloaded.
            <button
              type="button"
              onClick={() => handleExport(exportError)}
              className="inline-flex items-center gap-1 rounded-md border border-rose-400/40 px-2 py-1 font-semibold text-rose-200 transition-colors hover:bg-rose-400/10"
            >
              Retry
            </button>
          </span>
        )}
      </div>

      <p className="text-[10px] text-[var(--text-secondary)] border-t border-[var(--border-muted)] pt-3">
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
    regulator: record.category ? String(record.category).replace(/_/g, ' ').replace(/\baml\b/gi, 'AML').replace(/^./, c => c.toUpperCase()) : 'AE source',
    detected_at: record.timestamp_utc,
    run_id: record.run_id,
    status: record.change_status || 'UNCHANGED',
    new_hash: record.normalized_hash || record.content_hash ? `sha256:${String(record.normalized_hash || record.content_hash)}` : null,
    diff_available: Boolean(record.run_id && (record.diff_json_path || record.diff_md_path || record.change_status === 'CHANGED')),
    proof_block_path: record.proof_block_path || '',
    official_url: record.official_url || '',
    source_health_status: sourceHealthStatus(record),
    is_sample: false,
  }
}

export default function EvidencePage({ navigate }) {
  const [records, setRecords] = useState([])
  const [apiChecked, setApiChecked] = useState(false)
  const [apiError, setApiError] = useState('')

  const [reloadKey, setReloadKey] = useState(0)

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
  }, [reloadKey])

  function retryEvidence() {
    setApiChecked(false)
    setApiError('')
    setReloadKey(k => k + 1)
  }

  return (
    <div className="space-y-5 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="mb-1 text-lg font-bold text-white">Evidence Records</h1>
          <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
            Every real change we capture, with a timestamp, a tamper-evident fingerprint, and a stored proof file you can export for an auditor.
          </p>
        </div>
        <span className="flex flex-shrink-0 items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-bold text-emerald-300">
          <Shield className="h-3.5 w-3.5" />
          Real monitoring runs only
        </span>
      </div>

      <div className="sp-command-panel p-5">
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 h-5 w-5 flex-shrink-0 text-[var(--accent)]" />
            <div>
              <h2 className="mb-1 text-sm font-semibold text-white">Evidence boundary</h2>
              <p className="max-w-3xl text-xs leading-relaxed text-[var(--text-secondary)]">
                These are live source-run evidence records. Customer brief eligibility requires canonical evidence,
                review decision, alert linkage, and delivery approval. No sample hashes or fake alerts are shown here.
              </p>
            </div>
          </div>
          <span className="rounded-full border border-amber-400/25 bg-amber-400/10 px-3 py-1 text-xs font-bold text-amber-200">
            Raw source records — not the reviewed briefs you send
          </span>
        </div>

        <div className="grid gap-2 md:grid-cols-4">
          {[
            ['Source run', 'proof + normalized hash'],
            ['Acknowledge', 'internal assessment note'],
            ['Canonical record', 'separate review gate'],
            ['Brief delivery', 'blocked until approved'],
          ].map(([title, body]) => (
            <div key={title} className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
              <p className="text-xs font-semibold text-white">{title}</p>
              <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-muted)]">{body}</p>
            </div>
          ))}
        </div>
      </div>

      {!apiChecked ? (
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-5 py-10 text-center">
          <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-[var(--accent)]" />
          <p className="text-sm text-[var(--text-secondary)]">Loading live evidence records…</p>
        </div>
      ) : apiError ? (
        <ErrorState
          title="Could not load live evidence records."
          detail={`${apiError} No sample evidence is shown in the authenticated workspace.`}
          onRetry={retryEvidence}
          className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]"
        />
      ) : records.length === 0 ? (
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-5 py-10 text-center">
          <FileText className="mx-auto mb-3 h-5 w-5 text-[var(--text-muted)]" />
          <p className="font-medium text-[var(--text-primary)]">Your first evidence record appears after your next monitoring run</p>
          <p className="mx-auto mt-2 max-w-md text-sm text-[var(--text-muted)]">
            Nothing to do now — we capture it automatically. You do not need to trigger anything.
          </p>
          {navigate && (
            <button
              type="button"
              onClick={() => navigate('sources')}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3.5 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:bg-[var(--trust-badge)]"
            >
              View monitored sources
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {records.map((record, index) => (
            <EvidenceCard key={`${record.evidence_record_id}-${index}`} record={record} />
          ))}
        </div>
      )}

      <p className="text-xs text-[var(--text-secondary)] text-center leading-relaxed">
        StatuteProof reports are for information and compliance review support only. Not legal advice.
        Users should verify official source material directly and consult qualified professionals before making regulatory decisions.
      </p>
    </div>
  )
}

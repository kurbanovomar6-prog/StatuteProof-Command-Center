import { useEffect, useMemo, useState } from 'react'
import { Download, ExternalLink, FileText, Search, ShieldCheck } from 'lucide-react'

import { apiFetch, evidence } from '../../api'
import AuditBinderExport from './AuditBinderExport'
import CoverageCertificatePanel from './CoverageCertificatePanel'
import EffectiveDatesCalendar from './EffectiveDatesCalendar'
import EvidencePackExport from './EvidencePackExport'
import EvidenceRoomPanel from './EvidenceRoomPanel'
import RegulatorBinderExport from './RegulatorBinderExport'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import { formatGst } from '../../utils/time'
import ErrorState from './ui/ErrorState'

function shortHash(value) {
  return value ? String(value).slice(0, 12) : 'not recorded'
}

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

export default function ReportsPage() {
  const [records, setRecords] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [exportState, setExportState] = useState({})

  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    evidence.list('AE', 100)
      .then(data => {
        if (!active) return
        const rows = data.evidence || []
        setRecords(rows)
        setSelectedId(rows[0]?.evidence_record_id || '')
      })
      .catch(err => {
        if (active) setError(err.message || 'Could not load evidence records.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [reloadKey])

  function retryReports() {
    setLoading(true)
    setError('')
    setReloadKey(k => k + 1)
  }

  const filtered = useMemo(() => records.filter(record => {
    const haystack = [
      record.source_name,
      record.source_id,
      record.official_url,
      record.change_status,
      record.extraction_quality,
    ].join(' ').toLowerCase()
    return !search || haystack.includes(search.toLowerCase())
  }), [records, search])

  const selected = records.find(record => record.evidence_record_id === selectedId) || filtered[0]

  // Unique sources the caller has evidence for — feeds the binder source picker.
  const binderSources = useMemo(() => {
    const seen = new Map()
    records.forEach(record => {
      const id = record.source_id
      if (id && !seen.has(id)) {
        seen.set(id, { id, name: record.source_name || id })
      }
    })
    return Array.from(seen.values())
  }, [records])

  async function handleExport(record, format = 'pdf') {
    if (!record?.evidence_record_id) return
    setExportState(prev => ({ ...prev, [record.evidence_record_id]: { status: 'exporting', format, message: '' } }))
    // Stream the audit pack to the browser as a real download. We fetch the
    // bytes first and only claim success once they arrive, so we never render a
    // server file path (which the customer cannot open) or say "exported" when
    // nothing downloaded — mirrors EvidencePage's export flow.
    const downloadUrl = `/api/evidence/export-download?evidence_record_id=${encodeURIComponent(record.evidence_record_id)}&format=${encodeURIComponent(format)}`
    try {
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
      setExportState(prev => ({
        ...prev,
        [record.evidence_record_id]: {
          status: 'ok',
          format,
          message: 'Download started. Check your downloads folder.',
        },
      }))
    } catch (err) {
      setExportState(prev => ({
        ...prev,
        [record.evidence_record_id]: { status: 'error', message: err.message || 'Could not export audit pack.' },
      }))
    }
  }

  return (
    <div className="min-h-full space-y-5 bg-[var(--bg-navy)] p-5 pb-10">
      <EffectiveDatesCalendar />
      <CoverageCertificatePanel />
      <RegulatorBinderExport sources={binderSources} />
      <EvidencePackExport sources={binderSources} />
      <EvidenceRoomPanel sources={binderSources} />
      <AuditBinderExport />

      <div>
        <h1 className="text-lg font-bold text-white mb-1">Audit Reports</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
          Real export-ready evidence records only. Audit packs can be exported as PDF or Markdown/HTML from saved evidence records.
        </p>
      </div>

      <div className="rounded-xl border border-[var(--trust-border)] bg-[var(--bg-elevated)] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Evidence-backed report exports</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
              Reports are generated only from saved evidence records with proof/hash metadata. No fabricated report cards are shown.
            </p>
          </div>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          type="text"
          placeholder="Search evidence records"
          value={search}
          onChange={event => setSearch(event.target.value)}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] py-2 pl-9 pr-3 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
        />
      </div>

      {loading && (
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-5 py-8 text-sm text-[var(--text-secondary)]">
          Loading report-ready evidence records...
        </div>
      )}

      {!loading && error && (
        <ErrorState
          title="Could not load report records."
          detail={error}
          onRetry={retryReports}
          className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]"
        />
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-base)] px-6 py-12 text-center">
          <FileText className="mx-auto mb-3 h-8 w-8 text-[var(--text-muted)]" />
          <p className="text-sm font-semibold text-white">No generated reports yet.</p>
          <p className="mx-auto mt-2 max-w-2xl text-sm leading-relaxed text-[var(--text-muted)]">
            Audit report exports will appear after saved evidence records exist. This page does not display sample reports in authenticated workspaces.
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
          <div className="space-y-2">
            {filtered.map((record, index) => {
              const status = String(record.change_status || 'NOT_RUN').toUpperCase()
              return (
                <button
                  key={`${record.evidence_record_id}-${index}`}
                  type="button"
                  onClick={() => setSelectedId(record.evidence_record_id)}
                  className={`w-full rounded-xl border p-3.5 text-left transition-all ${
                    selected?.evidence_record_id === record.evidence_record_id
                      ? 'border-[var(--trust-border)] bg-[var(--bg-elevated)] ring-1 ring-[var(--trust-border)]'
                      : 'border-[var(--border-muted)] bg-[var(--bg-elevated)] hover:border-[var(--border)]'
                  }`}
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <StatusBadge code={status} />
                    <TimeStamp value={record.timestamp_utc} fallback="No timestamp" className="text-[11px] text-[var(--text-muted)]" />
                  </div>
                  <p className="text-xs font-semibold leading-snug text-white">{record.source_name || record.source_id}</p>
                  <p className="mt-1 text-[11px] text-[var(--text-muted)]">Hash {shortHash(record.normalized_hash || record.content_hash)}</p>
                </button>
              )
            })}
          </div>

          <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]">
            {!selected ? (
              <div className="px-6 py-12 text-center text-sm text-[var(--text-secondary)]">No evidence record selected.</div>
            ) : (
              <>
                <div className="border-b border-[var(--border-muted)] px-5 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold text-[var(--text-muted)]">Evidence record</p>
                      <h2 className="mt-1 text-base font-semibold text-white">{selected.source_name || selected.source_id}</h2>
                    </div>
                    <StatusBadge code={String(selected.change_status || 'NOT_RUN').toUpperCase()} />
                  </div>
                </div>
                <div className="divide-y divide-[var(--border-muted)] text-xs">
                  {[
                    ['Official URL', selected.official_url || 'not recorded'],
                    ['Evidence ID', selected.evidence_record_id],
                    ['Timestamp', formatGst(selected.timestamp_utc) || 'Not recorded'],
                    ['Extraction quality', selected.extraction_quality ? String(selected.extraction_quality).toLowerCase().replace(/^./, c => c.toUpperCase()) : 'Unknown'],
                    ['Normalized hash', selected.normalized_hash || selected.content_hash || 'not recorded'],
                    ['Proof path', selected.proof_block_path || 'not recorded'],
                    ['Diff path', selected.diff_json_path || selected.diff_md_path || 'not recorded'],
                  ].map(([label, value]) => (
                    <div key={label} className="grid gap-2 px-5 py-3 sm:grid-cols-[150px_1fr]">
                      <p className="font-semibold text-[var(--text-muted)]">{label}</p>
                      <p className="break-all text-[var(--text-primary)]">{value}</p>
                    </div>
                  ))}
                </div>
                <div className="border-t border-[var(--border-muted)] px-5 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleExport(selected, 'pdf')}
                      disabled={exportState[selected.evidence_record_id]?.status === 'exporting'}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:bg-[var(--trust-badge)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <Download className="h-3.5 w-3.5" />
                      {exportState[selected.evidence_record_id]?.status === 'exporting' && exportState[selected.evidence_record_id]?.format === 'pdf' ? 'Exporting PDF...' : 'Export PDF audit pack'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExport(selected, 'md_html')}
                      disabled={exportState[selected.evidence_record_id]?.status === 'exporting'}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--border)] hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      {exportState[selected.evidence_record_id]?.status === 'exporting' && exportState[selected.evidence_record_id]?.format === 'md_html' ? 'Exporting...' : 'Export Markdown/HTML'}
                    </button>
                    {selected.official_url && (
                      <a
                        href={selected.official_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] hover:border-[var(--border)] hover:text-white"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                        Open source
                      </a>
                    )}
                  </div>
                  {exportState[selected.evidence_record_id]?.message && (
                    <p className={`mt-3 text-xs ${exportState[selected.evidence_record_id]?.status === 'ok' ? 'text-emerald-300' : 'text-rose-300'}`}>
                      {exportState[selected.evidence_record_id].message}
                    </p>
                  )}
                  <div className="mt-4 flex items-start gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3">
                    <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--text-muted)]" />
                    <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                      Monitoring intelligence only. Not legal advice. Audit exports preserve proof/hash context but do not determine compliance obligations.
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

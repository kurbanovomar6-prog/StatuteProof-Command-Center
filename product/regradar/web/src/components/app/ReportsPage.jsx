import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Download, ExternalLink, FileText, Search, ShieldCheck } from 'lucide-react'

import { evidence } from '../../api'

const STATUS_STYLE = {
  CHANGED: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
  FIRST_SEEN: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200',
  UNCHANGED: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200',
  FAILED: 'border-rose-400/30 bg-rose-400/10 text-rose-200',
  QUALITY_DROP: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
}

function shortHash(value) {
  return value ? String(value).slice(0, 12) : 'not recorded'
}

export default function ReportsPage() {
  const [records, setRecords] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [exportState, setExportState] = useState({})

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
  }, [])

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

  async function handleExport(record, format = 'pdf') {
    if (!record?.evidence_record_id) return
    setExportState(prev => ({ ...prev, [record.evidence_record_id]: { status: 'exporting', format, message: '' } }))
    try {
      const data = await evidence.exportAuditPack(record.evidence_record_id, format)
      const paths = data.export || {}
      const artifactPath = data.format === 'pdf'
        ? paths.pdf_path || data.pdf_path || 'PDF path unavailable'
        : paths.md_path || paths.html_path || 'Markdown/HTML path unavailable'
      const message = `${data.message || 'Audit pack exported.'} ${artifactPath}`
      setExportState(prev => ({
        ...prev,
        [record.evidence_record_id]: { status: 'ok', format: data.format, message, export: data.export },
      }))
    } catch (err) {
      setExportState(prev => ({
        ...prev,
        [record.evidence_record_id]: { status: 'error', message: err.message || 'Could not export audit pack.' },
      }))
    }
  }

  return (
    <div className="min-h-full space-y-5 bg-[#07111F] p-5 pb-10">
      <div>
        <h1 className="text-lg font-bold text-white mb-1">Audit Reports</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Real export-ready evidence records only. Audit packs can be exported as PDF or Markdown/HTML from saved evidence records.
        </p>
      </div>

      <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Evidence-backed report exports</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Reports are generated only from saved evidence records with proof/hash metadata. No fabricated report cards are shown.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Saved evidence only', 'PDF export', 'Markdown/HTML export', 'Not legal advice'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Search evidence records"
          value={search}
          onChange={event => setSearch(event.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
        />
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-8 text-sm text-slate-400">
          Loading report-ready evidence records...
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 px-5 py-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
          <div>
            <p className="text-sm font-semibold text-rose-200">Could not load report records.</p>
            <p className="mt-1 text-xs text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/35 px-6 py-12 text-center">
          <FileText className="mx-auto mb-3 h-8 w-8 text-slate-600" />
          <p className="text-sm font-semibold text-white">No generated reports yet.</p>
          <p className="mx-auto mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Audit report exports will appear after saved evidence records exist. This page does not display sample reports in authenticated workspaces.
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
          <div className="space-y-2">
            {filtered.map(record => {
              const status = String(record.change_status || 'UNKNOWN').toUpperCase()
              return (
                <button
                  key={record.evidence_record_id}
                  type="button"
                  onClick={() => setSelectedId(record.evidence_record_id)}
                  className={`w-full rounded-xl border p-3.5 text-left transition-all ${
                    selected?.evidence_record_id === record.evidence_record_id
                      ? 'border-cyan-500/30 bg-slate-900 ring-1 ring-cyan-500/20'
                      : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                  }`}
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${STATUS_STYLE[status] || 'border-slate-600 bg-slate-800 text-slate-300'}`}>
                      {status}
                    </span>
                    <span className="text-[11px] text-slate-500">{record.timestamp_utc || 'No timestamp'}</span>
                  </div>
                  <p className="text-xs font-semibold leading-snug text-white">{record.source_name || record.source_id}</p>
                  <p className="mt-1 text-[11px] text-slate-500">Hash {shortHash(record.normalized_hash || record.content_hash)}</p>
                </button>
              )
            })}
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#0D1B2E]">
            {!selected ? (
              <div className="px-6 py-12 text-center text-sm text-slate-400">No evidence record selected.</div>
            ) : (
              <>
                <div className="border-b border-slate-800 px-5 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence record</p>
                      <h2 className="mt-1 text-base font-semibold text-white">{selected.source_name || selected.source_id}</h2>
                    </div>
                    <span className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${STATUS_STYLE[String(selected.change_status || '').toUpperCase()] || 'border-slate-600 bg-slate-800 text-slate-300'}`}>
                      {selected.change_status || 'UNKNOWN'}
                    </span>
                  </div>
                </div>
                <div className="divide-y divide-slate-800 text-xs">
                  {[
                    ['Official URL', selected.official_url || 'not recorded'],
                    ['Evidence ID', selected.evidence_record_id],
                    ['Timestamp', selected.timestamp_utc || 'not recorded'],
                    ['Extraction quality', selected.extraction_quality || 'UNKNOWN'],
                    ['Normalized hash', selected.normalized_hash || selected.content_hash || 'not recorded'],
                    ['Proof path', selected.proof_block_path || 'not recorded'],
                    ['Diff path', selected.diff_json_path || selected.diff_md_path || 'not recorded'],
                  ].map(([label, value]) => (
                    <div key={label} className="grid gap-2 px-5 py-3 sm:grid-cols-[150px_1fr]">
                      <p className="font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                      <p className="break-all text-slate-300">{value}</p>
                    </div>
                  ))}
                </div>
                <div className="border-t border-slate-800 px-5 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleExport(selected, 'pdf')}
                      disabled={exportState[selected.evidence_record_id]?.status === 'exporting'}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <Download className="h-3.5 w-3.5" />
                      {exportState[selected.evidence_record_id]?.status === 'exporting' && exportState[selected.evidence_record_id]?.format === 'pdf' ? 'Exporting PDF...' : 'Export PDF audit pack'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExport(selected, 'md_html')}
                      disabled={exportState[selected.evidence_record_id]?.status === 'exporting'}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      {exportState[selected.evidence_record_id]?.status === 'exporting' && exportState[selected.evidence_record_id]?.format === 'md_html' ? 'Exporting...' : 'Export Markdown/HTML'}
                    </button>
                    {selected.official_url && (
                      <a
                        href={selected.official_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:border-slate-500 hover:text-white"
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
                  <div className="mt-4 flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3">
                    <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-500" />
                    <p className="text-xs leading-relaxed text-slate-500">
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

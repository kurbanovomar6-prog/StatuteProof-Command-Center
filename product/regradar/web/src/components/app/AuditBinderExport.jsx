import { useState } from 'react'
import { Download, FileJson, ShieldCheck } from 'lucide-react'
import { delivery } from '../../api'

export default function AuditBinderExport() {
  const [status, setStatus] = useState('idle') // idle | generating | success | error
  const [fileSize, setFileSize] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  async function handleExport() {
    setStatus('generating')
    setErrorMsg('')
    try {
      const data = await delivery.preview(60)
      const alerts = (data.preview?.matches || []).map(item => ({
        alert_id:          item.alert_id || '',
        title:             item.title || '',
        source_name:       item.source_name || '',
        risk_level:        item.risk_level || 'LOW',
        executive_summary: item.executive_summary || '',
        what_changed:      item.what_changed || '',
        risk_explanation:  item.risk_explanation || '',
        recommendations:   Array.isArray(item.recommendations) ? item.recommendations : [],
        deadline:          item.deadline || null,
        source_url:        item.source_url || '',
        market:            item.market || item.jurisdiction || '',
        review_status:     item.review_status || '',
        created_at:        item.created_at || '',
      }))

      const dataExport = {
        export_type:  'StatuteProof monitored-alert data export (JSON)',
        generated_at: new Date().toISOString(),
        period_days:  60,
        disclaimer:   'Raw monitored-alert data export. This JSON file is not the board-ready PDF audit pack. Monitoring intelligence only. Not legal advice. Verify official source material directly and consult qualified legal or compliance professionals before making regulatory decisions based on this record.',
        alert_count:  alerts.length,
        alerts,
      }

      const json = JSON.stringify(dataExport, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `statuteproof-monitored-alerts-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      const kb = (blob.size / 1024).toFixed(1)
      setFileSize(`${kb} KB — ${alerts.length} alert${alerts.length !== 1 ? 's' : ''}`)
      setStatus('success')
    } catch (err) {
      setErrorMsg(err.message || 'Export failed.')
      setStatus('error')
    }
  }

  return (
    <div className="sp-glass border-cyan-400/15 p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
          <FileJson className="h-4 w-4 text-cyan-300" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Monitored-alert data export (JSON)</h2>
          <p className="mt-0.5 text-xs text-slate-400">
            Download your monitored-alert data as a JSON file. For the board-ready PDF binder,
            use Export PDF audit pack.
          </p>
        </div>
      </div>

      {/* Primary auditor-facing path: the real PDF audit pack lives per-record below. */}
      <div className="mb-4 flex items-start gap-2 rounded-lg border border-cyan-400/20 bg-cyan-400/5 px-3 py-2.5">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
        <p className="text-[11px] leading-relaxed text-slate-300">
          Need a board-ready or auditor-ready binder? Select an evidence record below and choose
          <span className="font-semibold text-cyan-200"> Export PDF audit pack</span>. The JSON export
          here is raw data only — not a formatted audit binder.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleExport}
          disabled={status === 'generating'}
          className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-semibold transition-colors ${
            status === 'generating'
              ? 'cursor-wait border-slate-700 bg-slate-800/70 text-slate-500'
              : 'border-slate-700 bg-slate-900/60 text-slate-300 hover:border-slate-500 hover:text-white'
          }`}
        >
          <FileJson className="h-3.5 w-3.5" />
          {status === 'generating' ? 'Preparing JSON…' : 'Download JSON data'}
        </button>

        {status === 'success' && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-300">
            <Download className="h-3.5 w-3.5" />
            Downloaded — {fileSize}
          </div>
        )}
        {status === 'error' && (
          <p className="text-xs text-rose-300">{errorMsg}</p>
        )}
      </div>

      <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
        This JSON file contains raw monitored-alert data from the past 60 days. It is not the
        formatted PDF audit pack. Verify hashes and official source material directly, and consider
        consulting qualified legal or compliance professionals before acting on any alert.
        Monitoring intelligence only. Not legal advice.
      </p>
    </div>
  )
}

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

      const binder = {
        binder_type:  'StatuteProof Audit Binder',
        generated_at: new Date().toISOString(),
        period_days:  60,
        disclaimer:   'Monitoring intelligence only. Not legal advice. Verify official source material directly and consult qualified legal or compliance professionals before making regulatory decisions based on this record.',
        alert_count:  alerts.length,
        alerts,
      }

      const json = JSON.stringify(binder, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `statuteproof-audit-binder-${new Date().toISOString().slice(0, 10)}.json`
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
          <h2 className="text-sm font-semibold text-white">Audit Binder Export</h2>
          <p className="mt-0.5 text-xs text-slate-400">
            Download a verifiable JSON record of all monitored alerts for regulatory inspection use.
            Includes risk levels, AI insights, recommendations, and source references.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleExport}
          disabled={status === 'generating'}
          className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-semibold transition-colors ${
            status === 'generating'
              ? 'cursor-wait border-slate-700 bg-slate-800/70 text-slate-500'
              : 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/15'
          }`}
        >
          <Download className="h-3.5 w-3.5" />
          {status === 'generating' ? 'Generating…' : 'Generate Audit Binder'}
        </button>

        {status === 'success' && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" />
            Downloaded — {fileSize}
          </div>
        )}
        {status === 'error' && (
          <p className="text-xs text-rose-300">{errorMsg}</p>
        )}
      </div>

      <p className="mt-4 text-[11px] leading-relaxed text-slate-600">
        The exported binder is a JSON file containing all reviewed alerts from the past 60 days.
        You may wish to verify hashes and official source material directly before relying on this
        record in regulatory proceedings. It would be prudent to consider consulting qualified legal
        or compliance professionals before acting on any alert. Monitoring intelligence only.
        Not legal advice.
      </p>
    </div>
  )
}

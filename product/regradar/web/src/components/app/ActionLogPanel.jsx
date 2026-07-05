import { useEffect, useState } from 'react'
import { CheckCircle, ChevronDown, ChevronUp, ClipboardList } from 'lucide-react'
import { actionLog } from '../../api'

const DECISION_LABELS = {
  act: { label: 'Act', style: 'border-rose-500/30 bg-rose-500/10 text-rose-300' },
  monitor: { label: 'Monitor', style: 'border-amber-500/30 bg-amber-500/10 text-amber-300' },
  no_action: { label: 'No Action', style: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
}

export default function ActionLogPanel({ alertId }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [decision, setDecision] = useState('monitor')
  const [notes, setNotes] = useState('')
  const [reviewerName, setReviewerName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  // Reset loading when the alert changes — render-phase adjustment instead
  // of a synchronous setState inside the effect (react-hooks lint rule).
  const [loadedAlertId, setLoadedAlertId] = useState(alertId)
  if (loadedAlertId !== alertId) {
    setLoadedAlertId(alertId)
    setLoading(true)
  }

  useEffect(() => {
    let active = true
    actionLog.list(alertId)
      .then(data => { if (active) setEntries(data.entries || []) })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [alertId])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setSaveMsg('')
    try {
      const result = await actionLog.create({ alert_id: alertId, decision, notes, reviewer_name: reviewerName })
      setEntries(prev => [result.entry, ...prev])
      setNotes('')
      setFormOpen(false)
      setSaveMsg('Response logged.')
    } catch (err) {
      setSaveMsg(err.message || 'Could not save.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-4 rounded-xl border border-slate-700/40 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-3.5 w-3.5 text-cyan-400" />
          <p className="text-xs font-semibold text-slate-300">Response Log</p>
          {entries.length > 0 && (
            <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
              {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setFormOpen(f => !f)}
          className="inline-flex items-center gap-1 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-500/15"
        >
          Log response
          {formOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      </div>

      {formOpen && (
        <form onSubmit={handleSubmit} className="mb-3 space-y-2.5 rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">Decision</label>
            <div className="flex gap-2">
              {Object.entries(DECISION_LABELS).map(([key, { label, style }]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setDecision(key)}
                  className={`flex-1 rounded-lg border px-2 py-1.5 text-xs font-semibold transition-colors ${decision === key ? style : 'border-slate-700 text-slate-500 hover:text-slate-300'}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">Reviewer</label>
            <input
              type="text"
              value={reviewerName}
              onChange={e => setReviewerName(e.target.value)}
              placeholder="Your name or role (optional)"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
              maxLength={200}
            />
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Rationale, next steps, or reference (optional)"
              rows={2}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none resize-none"
              maxLength={2000}
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/15 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save response'}
            </button>
            {saveMsg && <span className="text-xs text-emerald-300">{saveMsg}</span>}
          </div>
        </form>
      )}

      {loading && <div className="sp-skeleton h-8 w-full rounded-lg" />}

      {!loading && entries.length === 0 && (
        <p className="text-xs text-slate-600">No response logged yet. Log your team's decision above.</p>
      )}

      {!loading && entries.length > 0 && (
        <div className="space-y-2">
          {entries.map(entry => {
            const d = DECISION_LABELS[entry.decision] || DECISION_LABELS.monitor
            return (
              <div key={entry.id} className="flex items-start gap-2.5 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2.5">
                <CheckCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-400" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${d.style}`}>{d.label}</span>
                    {entry.reviewer_name && (
                      <span className="text-[11px] text-slate-400">{entry.reviewer_name}</span>
                    )}
                    <span className="text-[11px] text-slate-600">{entry.created_at?.slice(0, 10)}</span>
                  </div>
                  {entry.notes && <p className="mt-1 text-xs leading-relaxed text-slate-400">{entry.notes}</p>}
                  <p className="mt-1 font-mono text-[9px] text-slate-700">Hash: {entry.action_hash?.slice(0, 16)}&hellip;</p>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <p className="mt-3 text-[10px] text-slate-700">
        Response log records are hashed at creation for audit trail purposes. Monitoring intelligence only. Not legal advice.
      </p>
    </div>
  )
}

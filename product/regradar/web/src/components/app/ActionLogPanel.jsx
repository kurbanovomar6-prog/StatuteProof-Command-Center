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
  const [loadError, setLoadError] = useState('')

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
      .then(data => { if (active) { setEntries(data.entries || []); setLoadError('') } })
      .catch(err => { if (active) setLoadError(err.message || 'Could not load the action log.') })
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
    <div className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-3.5 w-3.5 text-[var(--accent)]" />
          <p className="text-xs font-semibold text-[var(--text-primary)]">Response Log</p>
          {entries.length > 0 && (
            <span className="rounded-full border border-[var(--border)] bg-[var(--bg-raised)] px-2 py-0.5 text-[10px] text-[var(--text-secondary)]">
              {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setFormOpen(f => !f)}
          className="inline-flex items-center gap-1 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-2.5 py-1 text-[11px] font-semibold text-[var(--accent)] hover:bg-[var(--trust-badge)]"
        >
          Log response
          {formOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      </div>

      {formOpen && (
        <form onSubmit={handleSubmit} className="mb-3 space-y-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-raised)] p-3">
          <div>
            <label className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">Decision</label>
            <div className="flex gap-2">
              {Object.entries(DECISION_LABELS).map(([key, { label, style }]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setDecision(key)}
                  className={`flex-1 rounded-lg border px-2 py-1.5 text-xs font-semibold transition-colors ${decision === key ? style : 'border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">Reviewer</label>
            <input
              type="text"
              value={reviewerName}
              onChange={e => setReviewerName(e.target.value)}
              placeholder="Your name or role (optional)"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
              maxLength={200}
            />
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">Notes</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Rationale, next steps, or reference (optional)"
              rows={2}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none resize-none"
              maxLength={2000}
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-4 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--trust-badge)] disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save response'}
            </button>
            {saveMsg && <span className="text-xs text-emerald-300">{saveMsg}</span>}
          </div>
        </form>
      )}

      {loading && <div className="sp-skeleton h-8 w-full rounded-lg" />}

      {!loading && loadError && (
        <p className="text-xs text-amber-300">{loadError} Reopen this alert to retry.</p>
      )}

      {!loading && !loadError && entries.length === 0 && (
        <p className="text-xs text-[var(--text-muted)]">No response logged yet. Log your team's decision above.</p>
      )}

      {!loading && entries.length > 0 && (
        <div className="space-y-2">
          {entries.map(entry => {
            const d = DECISION_LABELS[entry.decision] || DECISION_LABELS.monitor
            return (
              <div key={entry.id} className="flex items-start gap-2.5 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
                <CheckCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-400" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${d.style}`}>{d.label}</span>
                    {entry.reviewer_name && (
                      <span className="text-[11px] text-[var(--text-secondary)]">{entry.reviewer_name}</span>
                    )}
                    <span className="text-[11px] text-[var(--text-muted)]">{entry.created_at?.slice(0, 10)}</span>
                  </div>
                  {entry.notes && <p className="mt-1 text-xs leading-relaxed text-[var(--text-secondary)]">{entry.notes}</p>}
                  <p className="mt-1 font-mono text-[9px] text-[var(--text-muted)]">Hash: {entry.action_hash?.slice(0, 16)}&hellip;</p>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <p className="mt-3 text-[10px] text-[var(--text-secondary)]">
        Response log records are hashed at creation for audit trail purposes. Monitoring intelligence only. Not legal advice.
      </p>
    </div>
  )
}

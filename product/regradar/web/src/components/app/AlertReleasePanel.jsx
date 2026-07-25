import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Loader2, Send, ShieldAlert } from 'lucide-react'
import { admin } from '../../api'

// The editorial gate between a drafted alert and every customer's inbox.
// Founder-only on the server (_admin_guard); this panel is convenience, never
// the control.
//
// The one thing this UI must not do is imply that "weekly" is the safe option.
// digest_cadence routes on risk_level, not on the weekly/urgent choice, so a
// HIGH-risk draft goes out INSTANTLY either way. The server tells us the real
// consequence per row in `delivery_if_approved`; we show it verbatim rather
// than inventing our own label for it.

const ACTIONS = [
  { value: 'approve_weekly', label: 'Approve', tone: 'accent' },
  { value: 'reject',         label: 'Reject',  tone: 'muted' },
  { value: 'needs_legal',    label: 'Hold for legal', tone: 'muted' },
]

export default function AlertReleasePanel() {
  const [alerts, setAlerts] = useState(null)
  const [permitted, setPermitted] = useState(true)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [blocked, setBlocked] = useState(null) // { alertId, action, issues }
  const [note, setNote] = useState('')

  const load = useCallback(async () => {
    try {
      const data = await admin.alertReviewQueue()
      setAlerts(data.alerts || [])
      setPermitted(true)
    } catch (err) {
      if (err?.status === 403) setPermitted(false)
      else setError(err?.message || 'Could not load the review queue.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => { load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function decide(alertId, action, { force = false, reason = '' } = {}) {
    setBusy(alertId); setError(''); setNotice('')
    try {
      await admin.reviewAlert({ alertId, action, note: reason, force })
      setBlocked(null); setNote('')
      setNotice(`Decision recorded for ${alertId}.`)
      await load()
    } catch (err) {
      if (err?.status === 409) {
        // Not a failure — the safety gate did its job. Surface exactly what it
        // objected to and require a written reason before any override.
        setBlocked({
          alertId,
          action,
          issues: err.payload?.safety_issues || [],
        })
      } else {
        setError(err?.message || 'Could not record that decision.')
      }
    } finally {
      setBusy('')
    }
  }

  if (!permitted) return null

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5 mt-4">
      <div className="flex items-center gap-2 mb-1">
        <ShieldAlert className="w-4 h-4 text-amber-400" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-white">Alert release</h2>
      </div>
      <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
        Approving makes an alert eligible for customer delivery on the next scheduler
        cycle. Delivery cannot be recalled.
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          Loading queue&hellip;
        </div>
      ) : (alerts || []).length === 0 ? (
        <p className="text-xs text-[var(--text-muted)]">Nothing is waiting for a decision.</p>
      ) : (
        <ul className="space-y-3">
          {alerts.map(row => (
            <li
              key={row.alert_id}
              className="rounded-lg border border-[var(--border)] p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs text-white truncate">{row.source_name || row.source_id}</p>
                  <p className="text-[11px] text-[var(--text-muted)] font-mono truncate">{row.alert_id}</p>
                </div>
                <span className="text-[11px] text-[var(--text-muted)]">
                  {row.risk_level} &middot; confidence {row.confidence}
                </span>
              </div>

              <p className="text-[11px] text-amber-300/90 mt-2">
                If approved: {row.delivery_if_approved}
              </p>

              {(row.safety_issues || []).length > 0 && (
                <ul className="mt-2 space-y-0.5">
                  {row.safety_issues.map(issue => (
                    <li key={issue} className="flex items-center gap-1.5 text-[11px] text-rose-300">
                      <AlertTriangle className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
                      {issue}
                    </li>
                  ))}
                </ul>
              )}

              <div className="flex flex-wrap gap-2 mt-3">
                {ACTIONS.map(a => (
                  <button
                    key={a.value}
                    type="button"
                    disabled={busy === row.alert_id}
                    onClick={() => decide(row.alert_id, a.value)}
                    className={
                      a.tone === 'accent'
                        ? 'inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[var(--accent)] text-[var(--accent-contrast)] disabled:opacity-40'
                        : 'text-xs font-medium px-3 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-white disabled:opacity-40'
                    }
                  >
                    {a.tone === 'accent' && <Send className="w-3 h-3" aria-hidden="true" />}
                    {a.label}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      {blocked && (
        <div role="alertdialog" aria-label="Approval blocked by safety checks"
             className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/5 p-3">
          <p className="text-xs font-semibold text-rose-300 mb-1">
            Approval blocked by safety checks
          </p>
          <ul className="mb-2 space-y-0.5">
            {blocked.issues.map(issue => (
              <li key={issue} className="text-[11px] text-rose-300/90">&bull; {issue}</li>
            ))}
          </ul>
          <p className="text-[11px] text-[var(--text-muted)] mb-2">
            Overriding sends this to customers anyway. The reason is stored in the
            review record.
          </p>
          <label className="sr-only" htmlFor="override-note">Reason for overriding</label>
          <input
            id="override-note"
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Why is this safe to send?"
            className="w-full bg-[var(--bg-base)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]"
          />
          <div className="flex gap-2 mt-2">
            <button
              type="button"
              disabled={!note.trim() || busy === blocked.alertId}
              onClick={() => decide(blocked.alertId, blocked.action, { force: true, reason: note })}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-400 text-white disabled:opacity-40"
            >
              Override and approve
            </button>
            <button
              type="button"
              onClick={() => { setBlocked(null); setNote('') }}
              className="text-xs font-medium px-3 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-white"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && <p role="alert" className="text-xs text-rose-400 mt-3">{error}</p>}
      {notice && <p role="status" className="text-xs text-emerald-400 mt-3">{notice}</p>}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { CalendarClock, Check, ListChecks, Plus, Trash2, User } from 'lucide-react'

import { checklist } from '../../api'

// Static fallback copy, matched to app/action_checklist.py FRAMING. The server
// returns the authoritative (forbidden-claims guarded) framing on GET; this is
// only used before the first response so the panel never renders empty labels.
const FALLBACK_FRAMING = {
  title: 'Your review checklist',
  subtitle: 'Review actions you choose to track for this alert.',
  add_label: 'Add a review action',
  add_placeholder: 'Describe a review step you want to track',
  empty: 'No review actions yet. Add the steps you choose to track for this alert.',
  disclaimer:
    'You author these items. For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

/**
 * AlertChecklistPanel — the user's OWN review to-do list for one alert.
 *
 * Obligation-workflow v1: a blank checklist the user authors themselves. The app
 * never prescribes or suggests a compliance action — every item is the user's
 * words. Tick an item done, add an action (with optional assignee + due date),
 * or delete one. All mutations are owner-scoped and audit-logged server-side.
 */
export default function AlertChecklistPanel({ alertId }) {
  const [items, setItems] = useState([])
  const [framing, setFraming] = useState(FALLBACK_FRAMING)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [text, setText] = useState('')
  const [assignee, setAssignee] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')
  const [busyId, setBusyId] = useState(null)

  // Reset loading when the alert changes — render-phase adjustment instead of a
  // synchronous setState inside the effect (react-hooks lint rule).
  const [loadedAlertId, setLoadedAlertId] = useState(alertId)
  if (loadedAlertId !== alertId) {
    setLoadedAlertId(alertId)
    setLoading(true)
  }

  useEffect(() => {
    let active = true
    checklist.list(alertId)
      .then(data => {
        if (!active) return
        setItems(data.items || [])
        if (data.framing) setFraming(data.framing)
        setLoadError('')
      })
      .catch(err => { if (active) setLoadError(err.message || 'Could not load the checklist.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [alertId])

  const openCount = items.filter(item => item.status !== 'done').length

  async function handleAdd(event) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    setSaving(true)
    setSaveMsg('')
    try {
      const result = await checklist.add({ alertId, text: trimmed, assignee, dueDate })
      setItems(prev => [...prev, result.item])
      setText('')
      setAssignee('')
      setDueDate('')
    } catch (err) {
      setSaveMsg(err.message || 'Could not add the review action.')
    } finally {
      setSaving(false)
    }
  }

  async function handleToggle(item) {
    const next = item.status === 'done' ? 'open' : 'done'
    setBusyId(item.id)
    setSaveMsg('')
    try {
      const result = await checklist.toggle(item.id, next)
      setItems(prev => prev.map(row => (row.id === item.id ? result.item : row)))
    } catch (err) {
      setSaveMsg(err.message || 'Could not update the item.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleRemove(item) {
    setBusyId(item.id)
    setSaveMsg('')
    try {
      await checklist.remove(item.id)
      setItems(prev => prev.filter(row => row.id !== item.id))
    } catch (err) {
      setSaveMsg(err.message || 'Could not delete the item.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--bg-elevated)] p-4">
      <div className="mb-3 flex items-center gap-2">
        <ListChecks className="h-3.5 w-3.5 text-[var(--accent)]" />
        <p className="text-xs font-semibold text-[var(--text-primary)]">{framing.title}</p>
        {openCount > 0 && (
          <span className="rounded-full border border-[var(--border)] bg-[var(--bg-raised)] px-2 py-0.5 text-[10px] text-[var(--text-secondary)]">
            {openCount} open
          </span>
        )}
      </div>
      <p className="-mt-1 mb-3 text-[11px] text-[var(--text-muted)]">{framing.subtitle}</p>

      <form onSubmit={handleAdd} className="mb-3 space-y-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-raised)] p-3">
        <div>
          <label htmlFor={`aci-text-${alertId}`} className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">
            {framing.add_label}
          </label>
          <input
            id={`aci-text-${alertId}`}
            type="text"
            value={text}
            onChange={event => setText(event.target.value)}
            placeholder={framing.add_placeholder}
            maxLength={500}
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="flex-1">
            <label htmlFor={`aci-assignee-${alertId}`} className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">
              Assignee (optional)
            </label>
            <input
              id={`aci-assignee-${alertId}`}
              type="text"
              value={assignee}
              onChange={event => setAssignee(event.target.value)}
              placeholder="Name or role"
              maxLength={120}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
            />
          </div>
          <div className="flex-1">
            <label htmlFor={`aci-due-${alertId}`} className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]">
              Due date (optional)
            </label>
            <input
              id={`aci-due-${alertId}`}
              type="date"
              value={dueDate}
              onChange={event => setDueDate(event.target.value)}
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none"
            />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving || !text.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-4 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--trust-badge)] disabled:opacity-50"
          >
            <Plus className="h-3.5 w-3.5" />
            {saving ? 'Adding...' : 'Add action'}
          </button>
          {saveMsg && <span className="text-xs text-rose-300">{saveMsg}</span>}
        </div>
      </form>

      {loading && <div className="sp-skeleton h-8 w-full rounded-lg" />}

      {!loading && loadError && (
        <p className="text-xs text-amber-300">{loadError} Reopen this alert to retry.</p>
      )}

      {!loading && !loadError && items.length === 0 && (
        <p className="text-xs text-[var(--text-muted)]">{framing.empty}</p>
      )}

      {!loading && items.length > 0 && (
        <ul className="space-y-2">
          {items.map(item => {
            const done = item.status === 'done'
            return (
              <li
                key={item.id}
                className="flex items-start gap-2.5 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5"
              >
                <button
                  type="button"
                  role="checkbox"
                  aria-checked={done}
                  aria-label={done ? `Mark "${item.text}" as not done` : `Mark "${item.text}" as done`}
                  disabled={busyId === item.id}
                  onClick={() => handleToggle(item)}
                  className={`mt-0.5 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border transition-colors disabled:opacity-50 ${
                    done
                      ? 'border-emerald-400 bg-emerald-400/20 text-emerald-300'
                      : 'border-[var(--border)] text-transparent hover:border-[var(--trust-border)]'
                  }`}
                >
                  <Check className="h-3 w-3" />
                </button>
                <div className="min-w-0 flex-1">
                  <p className={`text-xs leading-relaxed ${done ? 'text-[var(--text-muted)] line-through' : 'text-[var(--text-secondary)]'}`}>
                    {item.text}
                  </p>
                  {(item.assignee || item.due_date) && (
                    <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-[var(--text-muted)]">
                      {item.assignee && (
                        <span className="inline-flex items-center gap-1">
                          <User className="h-2.5 w-2.5" />
                          {item.assignee}
                        </span>
                      )}
                      {item.due_date && (
                        <span className="inline-flex items-center gap-1">
                          <CalendarClock className="h-2.5 w-2.5" />
                          {item.due_date}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  aria-label={`Delete "${item.text}"`}
                  disabled={busyId === item.id}
                  onClick={() => handleRemove(item)}
                  className="mt-0.5 flex-shrink-0 rounded p-0.5 text-[var(--text-muted)] transition-colors hover:text-rose-300 disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </li>
            )
          })}
        </ul>
      )}

      <p className="mt-3 text-[10px] leading-relaxed text-[var(--text-secondary)]">
        {framing.disclaimer}
      </p>
    </div>
  )
}

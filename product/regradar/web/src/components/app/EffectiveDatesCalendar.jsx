import { useEffect, useMemo, useState } from 'react'
import { CalendarClock, Download, ExternalLink, ShieldCheck } from 'lucide-react'

import { calendar } from '../../api'
import { buildEffectiveDatesIcs } from '../../utils/ics'

const HORIZON_DAYS = 90

// Detected-type chip. These are HONEST "detected type" hints derived from the
// wording around the date — never an assertion about the reader's obligations.
function TypeChip({ item }) {
  const map = {
    effective_date: 'bg-[var(--trust-badge)] text-[var(--accent)] border-[var(--trust-border)]',
    deadline: 'bg-amber-500/12 text-amber-200 border-amber-400/25',
    consultation_close: 'bg-[var(--bg-raised)] text-[var(--text-secondary)] border-[var(--border)]',
    transition: 'bg-[var(--bg-raised)] text-[var(--text-secondary)] border-[var(--border)]',
    other: 'bg-[var(--bg-tooltip)] text-[var(--text-primary)] border-[var(--border)]',
  }
  const cls = map[item.detected_type] || map.other
  return (
    <span
      title="detected type (from the changed text) — not your legal deadline"
      className={`inline-flex rounded-md border px-2 py-0.5 text-[11px] font-medium capitalize ${cls}`}
    >
      {item.type_label || 'date'}
    </span>
  )
}

function DaysBadge({ days }) {
  if (typeof days !== 'number') return null
  const tone =
    days <= 7
      ? 'border-rose-500/30 bg-rose-500/10 text-rose-300'
      : days <= 30
        ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
        : 'border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-secondary)]'
  return (
    <span
      title="days until this detected date falls — not a countdown to an action you must take"
      className={`rounded-md border px-2 py-0.5 text-[10px] font-bold tabular-nums ${tone}`}
    >
      {days}d
    </span>
  )
}

function monthLabel(iso) {
  try {
    return new Date(`${String(iso).slice(0, 10)}T12:00:00Z`).toLocaleDateString('en-GB', {
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    })
  } catch {
    return 'Upcoming'
  }
}

function dayLabel(iso) {
  try {
    return new Date(`${String(iso).slice(0, 10)}T12:00:00Z`).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      timeZone: 'UTC',
    })
  } catch {
    return String(iso).slice(0, 10)
  }
}

function triggerDownload(text, filename, mime) {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Effective-date / key-date calendar.
 *
 * A forward-looking view of dates StatuteProof DETECTED in the changed text of
 * monitored sources over the next ~90 days, grouped by month. Every date is
 * framed as a monitoring signal — "detected in the changed text of {source},
 * verify against the official source" — never the reader's legal deadline. Each
 * row links to its sealed evidence record (id + record hash) and the official
 * source. The "Export .ics" button builds a standards-valid calendar file
 * CLIENT-SIDE from the detected dates.
 */
export default function EffectiveDatesCalendar() {
  const [status, setStatus] = useState('loading') // loading | loaded | error
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    calendar
      .effectiveDates({ days: HORIZON_DAYS })
      .then(data => {
        if (!active) return
        setPayload(data)
        setStatus('loaded')
      })
      .catch(err => {
        if (!active) return
        setError(err.message || 'Could not load the detected-date calendar.')
        setStatus('error')
      })
    return () => {
      active = false
    }
  }, [])

  const dates = payload?.dates || []

  const groups = useMemo(() => {
    const byMonth = new Map()
    for (const item of dates) {
      const key = String(item.date).slice(0, 7)
      if (!byMonth.has(key)) byMonth.set(key, { label: monthLabel(item.date), items: [] })
      byMonth.get(key).items.push(item)
    }
    return Array.from(byMonth.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([, group]) => group)
  }, [dates])

  function handleExport() {
    if (!dates.length) return
    const ics = buildEffectiveDatesIcs(dates)
    triggerDownload(ics, 'statuteproof-detected-dates.ics', 'text/calendar;charset=utf-8')
  }

  return (
    <div className="rounded-xl border border-[var(--trust-border)] bg-[var(--bg-elevated)] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--trust-badge)]">
            <CalendarClock className="h-4 w-4 text-[var(--accent)]" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Detected key-date calendar</h2>
            <p className="mt-1 max-w-2xl text-[12px] leading-relaxed text-[var(--text-secondary)]">
              Dates StatuteProof detected in the <span className="text-[var(--text-primary)]">changed text</span> of
              monitored sources over the next {HORIZON_DAYS} days. Each is a monitoring signal to help you decide what
              to review — not your legal deadline. Verify every date against the official source.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleExport}
          disabled={!dates.length}
          className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:bg-[var(--trust-badge)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Download className="h-3.5 w-3.5" />
          Export .ics
        </button>
      </div>

      {status === 'loading' && (
        <div className="mt-4 space-y-2">
          <div className="sp-skeleton h-12 w-full rounded-lg" />
          <div className="sp-skeleton h-12 w-full rounded-lg" />
        </div>
      )}

      {status === 'error' && (
        <p className="mt-4 rounded-lg border border-rose-400/25 bg-rose-500/10 px-3 py-2.5 text-xs text-rose-200">
          {error}
        </p>
      )}

      {status === 'loaded' && dates.length === 0 && (
        <p className="mt-4 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3 text-xs leading-relaxed text-[var(--text-secondary)]">
          No dates were detected in the changed text of your monitored sources for the next {HORIZON_DAYS} days. This is
          best-effort detection over monitored sources only — it is not a statement that no relevant dates exist.
        </p>
      )}

      {status === 'loaded' && dates.length > 0 && (
        <div className="mt-4 space-y-5">
          {groups.map(group => (
            <div key={group.label}>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                {group.label}
              </p>
              <div className="space-y-2">
                {group.items.map(item => (
                  <article
                    key={`${item.record_hash}-${item.date}-${item.detected_type}`}
                    className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3.5 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-semibold tabular-nums text-white">
                        {dayLabel(item.date)}
                      </span>
                      <DaysBadge days={item.days_until} />
                      <TypeChip item={item} />
                      <span className="text-xs font-semibold text-[var(--text-primary)]">
                        {item.source_name || item.source_id}
                      </span>
                      {item.regulator && (
                        <span className="text-[11px] text-[var(--text-muted)]">({item.regulator})</span>
                      )}
                    </div>

                    {item.excerpt && (
                      <p className="mt-2 border-l-2 border-[var(--border)] pl-2.5 text-[12px] leading-relaxed text-[var(--text-secondary)]">
                        Detected in changed text: <span className="text-[var(--text-primary)]">{item.excerpt}</span>
                      </p>
                    )}

                    {item.date_ambiguous && (
                      <p className="mt-1.5 text-[11px] text-amber-300">
                        Date format is ambiguous (day/month vs month/day); verify against the source.
                      </p>
                    )}

                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-[var(--text-muted)]">
                      {item.evidence_record_id && (
                        <span className="font-mono">Evidence: {item.evidence_record_id}</span>
                      )}
                      {item.record_hash && (
                        <span className="font-mono">Hash {String(item.record_hash).slice(0, 20)}</span>
                      )}
                      {item.official_url && (
                        <a
                          href={item.official_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[var(--accent)] hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                          Open official source
                        </a>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--text-muted)]" />
        <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
          {payload?.disclaimer ||
            'For monitoring information only. Not legal advice and not a guarantee of compliance.'}{' '}
          Detected dates are parsed from monitored source text and may be incomplete or misread. Verify official source
          material directly before relying on any date.
        </p>
      </div>
    </div>
  )
}

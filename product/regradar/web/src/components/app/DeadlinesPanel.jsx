import { useEffect, useState } from 'react'
import { Calendar, Clock } from 'lucide-react'
import { delivery } from '../../api'

function daysUntil(dateStr) {
  try {
    const target = new Date(dateStr)
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    target.setHours(0, 0, 0, 0)
    return Math.ceil((target - now) / (1000 * 60 * 60 * 24))
  } catch {
    return null
  }
}

function DeadlineBadge({ days }) {
  if (days === null) return null
  if (days < 0) {
    return <span className="rounded-md border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-400">Passed</span>
  }
  if (days <= 7) {
    return <span className="rounded-md border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[10px] font-bold text-rose-300">{days}d</span>
  }
  if (days <= 30) {
    return <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-300">{days}d</span>
  }
  return <span className="rounded-md border border-slate-700 bg-slate-800/60 px-2 py-0.5 text-[10px] font-semibold text-slate-400">{days}d</span>
}

export default function DeadlinesPanel() {
  const [deadlines, setDeadlines] = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    let active = true
    delivery.preview(60)
      .then(res => {
        if (!active) return
        const matches = res.preview?.matches || []
        const withDeadlines = matches
          .filter(a => a.deadline && String(a.deadline).toLowerCase() !== 'null')
          .map(a => ({
            ...a,
            _days: daysUntil(a.deadline),
          }))
          .sort((a, b) => {
            if (a._days === null) return 1
            if (b._days === null) return -1
            return a._days - b._days
          })
        setDeadlines(withDeadlines)
      })
      .catch(() => { if (active) setDeadlines([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <div className="sp-glass p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10">
            <Calendar className="h-3.5 w-3.5 text-cyan-300" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Regulatory Deadlines</h2>
            <p className="text-[11px] text-slate-500">From AI-detected deadline fields — last 60 days</p>
          </div>
        </div>
        {deadlines.length > 0 && (
          <span className="rounded-full border border-amber-500/25 bg-amber-500/10 px-2.5 py-1 text-[11px] font-semibold text-amber-300">
            {deadlines.length} detected
          </span>
        )}
      </div>

      {loading && (
        <div className="space-y-2">
          <div className="sp-skeleton h-10 w-full rounded-lg" />
          <div className="sp-skeleton h-10 w-full rounded-lg" />
        </div>
      )}

      {!loading && deadlines.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Clock className="h-4 w-4 flex-shrink-0" />
          <span>No upcoming deadlines detected in monitored alerts. Deadlines are extracted from AI analysis of regulatory changes.</span>
        </div>
      )}

      {!loading && deadlines.length > 0 && (
        <div className="space-y-2">
          {deadlines.slice(0, 8).map(item => (
            <div key={item.alert_id} className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2.5">
              <DeadlineBadge days={item._days} />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-slate-200 truncate">
                  {item.source_name || item.title || 'Regulatory change'}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-500 truncate">
                  {item.what_changed || item.executive_summary?.slice(0, 100) || 'No change detail recorded'}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-600">Deadline: {item.deadline}</p>
              </div>
            </div>
          ))}
          {deadlines.length > 8 && (
            <p className="text-[11px] text-slate-400">+{deadlines.length - 8} more in Reviewed Alerts</p>
          )}
        </div>
      )}

      <p className="mt-3 text-[10px] text-slate-400">
        Deadline dates are extracted by AI from regulatory text and may not be complete. Verify official source material directly.
        Monitoring intelligence only. Not legal advice.
      </p>
    </div>
  )
}

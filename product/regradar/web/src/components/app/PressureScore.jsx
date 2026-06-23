import { useEffect, useState } from 'react'
import { TrendingUp } from 'lucide-react'
import { delivery } from '../../api'

function computeScore(alerts) {
  let score = 0
  let high = 0; let medium = 0; let low = 0
  for (const a of alerts) {
    const risk = String(a.risk_level || 'LOW').toUpperCase()
    if (risk === 'HIGH')        { score += 3; high++ }
    else if (risk === 'MEDIUM') { score += 1; medium++ }
    else                        { low++ }
  }
  return { score, high, medium, low }
}

export default function PressureScore() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    delivery.preview(14)
      .then(res => {
        if (!active) return
        const alerts = res.preview?.matches || []
        setData(computeScore(alerts))
      })
      .catch(() => { if (active) setData({ score: 0, high: 0, medium: 0, low: 0 }) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const score  = data?.score  ?? 0
  const high   = data?.high   ?? 0
  const medium = data?.medium ?? 0
  const low    = data?.low    ?? 0

  const MAX_SCORE = 30
  const pct = Math.min(100, Math.round((score / MAX_SCORE) * 100))

  const accentBorder = score >= 25 ? 'border-l-rose-500/60'
    : score >= 10  ? 'border-l-amber-500/60'
    : 'border-l-emerald-500/60'

  const scoreTone = score >= 25 ? 'text-rose-300'
    : score >= 10 ? 'text-amber-300'
    : 'text-emerald-300'

  const barColor = score >= 25 ? 'bg-rose-500/60'
    : score >= 10 ? 'bg-amber-500/60'
    : 'bg-emerald-500/60'

  return (
    <div className={`sp-glass border-l-4 ${accentBorder} p-5`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Regulatory Pressure</p>
          <p className="text-[11px] text-slate-600">Last 14 days</p>
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800">
          <TrendingUp className="h-4 w-4 text-slate-400" />
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          <div className="sp-skeleton h-8 w-24 rounded" />
          <div className="sp-skeleton h-3 w-full rounded" />
        </div>
      ) : (
        <>
          <p className={`text-3xl font-bold ${scoreTone}`}>{score}</p>

          <div className="mt-3 h-1.5 w-full rounded-full bg-slate-800">
            <div
              className={`h-1.5 rounded-full transition-all duration-700 ${barColor}`}
              style={{ width: `${pct}%` }}
            />
          </div>

          <div className="mt-3 flex gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-600">High</p>
              <p className="text-sm font-bold text-rose-300">{high}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-600">Medium</p>
              <p className="text-sm font-bold text-amber-300">{medium}</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-600">Low</p>
              <p className="text-sm font-bold text-emerald-300">{low}</p>
            </div>
          </div>

          <p className="mt-3 text-[10px] text-slate-700">
            Score = HIGH&times;3 + MEDIUM&times;1. Monitoring intelligence only. Not legal advice.
          </p>
        </>
      )}
    </div>
  )
}

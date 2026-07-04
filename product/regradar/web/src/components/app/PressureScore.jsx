import { useEffect, useState } from 'react'
import { TrendingUp } from 'lucide-react'
import { delivery } from '../../api'

function countByRisk(alerts) {
  let high = 0; let medium = 0; let low = 0
  for (const a of alerts) {
    const risk = String(a.risk_level || 'LOW').toUpperCase()
    if (risk === 'HIGH') high++
    else if (risk === 'MEDIUM') medium++
    else low++
  }
  return { total: alerts.length, high, medium, low }
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
        setData(countByRisk(alerts))
      })
      .catch(() => { if (active) setData({ total: 0, high: 0, medium: 0, low: 0 }) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const total  = data?.total  ?? 0
  const high   = data?.high   ?? 0
  const medium = data?.medium ?? 0
  const low    = data?.low    ?? 0

  const accentBorder = high > 0 ? 'border-l-rose-500/60'
    : medium > 0 ? 'border-l-amber-500/60'
    : 'border-l-emerald-500/60'

  const totalTone = high > 0 ? 'text-rose-300'
    : medium > 0 ? 'text-amber-300'
    : 'text-emerald-300'

  return (
    <div className={`sp-glass border-l-4 ${accentBorder} p-5`}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Reviewed alerts by risk</p>
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
          <p className={`text-3xl font-bold ${totalTone}`}>{total}</p>

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
            Counts of reviewed alerts matched to this workspace. Monitoring intelligence only. Not legal advice.
          </p>
        </>
      )}
    </div>
  )
}

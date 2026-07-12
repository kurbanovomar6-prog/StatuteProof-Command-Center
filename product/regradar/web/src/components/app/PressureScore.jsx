import { useEffect, useState } from 'react'
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

// Small severity dot. Rose is allowed as a category dot/chip (never as a hero
// ring); amber for medium, emerald for low.
function RiskRow({ color, label, value }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <span className="h-2 w-2 rounded-full" style={{ background: color }} aria-hidden="true" />
        {label}
      </span>
      <span className="font-mono text-sm tabular-nums text-[var(--text-primary)]">{value}</span>
    </div>
  )
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

  return (
    <div className="sp-glass p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Reviewed alerts by risk</h3>
          <p className="mt-0.5 text-xs text-[var(--text-muted)]">Last 14 days</p>
        </div>
        <span className="font-mono text-2xl font-semibold tabular-nums text-[var(--text-primary)]">
          {loading ? '—' : total}
        </span>
      </div>

      {loading ? (
        <div className="mt-4 space-y-2">
          <div className="sp-skeleton h-4 w-full rounded" />
          <div className="sp-skeleton h-4 w-full rounded" />
          <div className="sp-skeleton h-4 w-full rounded" />
        </div>
      ) : (
        <div className="mt-3 divide-y divide-[var(--border-subtle)]">
          <RiskRow color="#FB7185" label="High" value={high} />
          <RiskRow color="#F4B84A" label="Medium" value={medium} />
          <RiskRow color="#37D399" label="Low" value={low} />
        </div>
      )}

      <p className="mt-4 text-xs leading-relaxed text-[var(--text-secondary)]">
        Reviewed alerts matched to this workspace. Monitoring information only. Not legal advice.
      </p>
    </div>
  )
}

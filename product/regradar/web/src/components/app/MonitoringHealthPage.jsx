import { useEffect, useState } from 'react'
import {
  Activity, ShieldCheck, Clock, AlertTriangle, XCircle,
  Database, TriangleAlert, RotateCw,
} from 'lucide-react'

import { reports, health as healthApi } from '../../api'
import ErrorState from './ui/ErrorState'
import EmptyState from './ui/EmptyState'
import TimeStamp from './ui/TimeStamp'

// This is an OPERATIONAL surface: it reports whether the automated checks ran on
// each monitored source — not a compliance, legal, or regulatory status. Every
// number is derived from real recorded coverage-certificate evidence. A source
// that was not successfully checked is shown as Stale / No coverage, never hidden
// and never shown as healthy.

const DEFAULT_PERIOD_DAYS = 30
// A daily-monitored source whose last successful check trails the period end by
// this many days is "not current" — an honest staleness signal.
const STALE_LAST_CHECK_DAYS = 2
const DISCLAIMER = 'For monitoring information only. Not legal advice and not a guarantee of compliance.'

function isoDay(d) {
  return d.toISOString().slice(0, 10)
}

function daysAgo(n) {
  const d = new Date()
  return isoDay(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - n)))
}

/**
 * Derive operational monitoring health for one coverage-certificate source row
 * from the real recorded fields — never a compliance judgement.
 *
 * Priority (most severe first, so a clean screen shows no false green):
 *  1. no_coverage — zero successful checks recorded in the period.
 *  2. degraded    — checks ran but one or more failed / dropped quality.
 *  3. stale       — coverage exists but is not current (day gaps, or the last
 *                   check trails the period end) — partial continuity.
 *  4. healthy     — continuous proof through the period end, no failures.
 */
function deriveHealth(s) {
  const successful = Number(s.successful_checks || 0)
  if (successful === 0 || s.change_state === 'NO_PROOF' || s.continuity_status === 'NO_COVERAGE') {
    return 'no_coverage'
  }
  if (s.degraded) return 'degraded'
  const gapDays = Number(s.gap_days || 0)
  const lastCheckGap = Number(s.last_check_gap_days || 0)
  const stale = gapDays > 0 || lastCheckGap >= STALE_LAST_CHECK_DAYS || s.continuity_status === 'PARTIAL'
  return stale ? 'stale' : 'healthy'
}

const HEALTH = {
  healthy:     { label: 'Healthy',     tone: 'success',  icon: ShieldCheck,   note: 'Checks ran and recorded continuous proof through the end of the period, with no failures.' },
  stale:       { label: 'Stale',       tone: 'warning',  icon: Clock,         note: 'Coverage exists, but the checks are not current — the last successful check is old or days are missing.' },
  degraded:    { label: 'Degraded',    tone: 'warning',  icon: AlertTriangle, note: 'Checks ran but one or more failed or returned reduced content in the period. Operator attention needed.' },
  no_coverage: { label: 'No coverage', tone: 'critical', icon: XCircle,       note: 'No successful check recorded any proof for this source in the period. Shown, never hidden or treated as healthy.' },
}

// Semantic status tones, matching the vocabulary used across the dashboard
// (StatusBadge / CoverageCertificatePanel). Accent stays a CSS token.
const TONE_CLS = {
  success:  'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
  warning:  'border-amber-400/25 bg-amber-400/10 text-amber-300',
  critical: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
  neutral:  'border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-secondary)]',
}

// Non-healthy sorts to the top so the items that need attention lead.
const HEALTH_RANK = { no_coverage: 0, degraded: 1, stale: 2, healthy: 3 }

function HealthBadge({ status }) {
  const meta = HEALTH[status] || HEALTH.no_coverage
  const Icon = meta.icon
  return (
    <span
      title={meta.note}
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-semibold ${TONE_CLS[meta.tone]}`}
    >
      <Icon className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
      {meta.label}
    </span>
  )
}

function Tile({ label, value, tone = 'default' }) {
  const toneCls = tone === 'bad'
    ? 'text-rose-300'
    : tone === 'warn'
      ? 'text-amber-300'
      : tone === 'good'
        ? 'text-emerald-300'
        : 'text-white'
  return (
    <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
      <p className={`font-mono text-lg font-semibold tabular-nums ${toneCls}`}>{value}</p>
      <p className="mt-0.5 text-[11px] leading-tight text-[var(--text-muted)]">{label}</p>
    </div>
  )
}

// Compact top-of-page system signal from the existing /api/health endpoint. This
// is a reachability + last-pipeline-run signal, not a per-source verdict. When it
// is unreachable the page still renders the per-source coverage below.
function SystemStatus({ system }) {
  if (system === undefined) return null
  if (system === null) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-amber-400/25 bg-amber-400/10 px-3 py-2 text-[11px] text-amber-300">
        <TriangleAlert className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
        Could not reach the monitoring system status endpoint. Per-source coverage below is still shown.
      </div>
    )
  }
  const dbConnected = system.db === 'connected'
  const activeCount = Number(system.sources_active ?? -1)
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5 text-[11px]">
      <span className="inline-flex items-center gap-1.5 font-semibold text-[var(--text-primary)]">
        <Database className="h-3.5 w-3.5 flex-shrink-0 text-[var(--text-muted)]" aria-hidden="true" />
        Monitoring system
      </span>
      <span className={dbConnected ? 'text-emerald-300' : 'text-rose-300'}>
        {dbConnected ? 'Store connected' : 'Store unavailable'}
      </span>
      {activeCount >= 0 && (
        <span className="text-[var(--text-secondary)]">
          {activeCount} source{activeCount === 1 ? '' : 's'} active
        </span>
      )}
      <span className="inline-flex items-center gap-1.5 text-[var(--text-secondary)]">
        Last pipeline run
        <TimeStamp value={system.last_run_at} fallback="none recorded" className="text-[var(--text-primary)]" />
      </span>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4" aria-hidden="true">
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="sp-skeleton h-[62px]" />
        ))}
      </div>
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="sp-skeleton h-11" />
        ))}
      </div>
    </div>
  )
}

function HealthTable({ rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse text-xs">
        <thead>
          <tr className="border-b border-[var(--border-muted)] text-left text-[11px] text-[var(--text-muted)]">
            <th scope="col" className="px-3 py-2 font-semibold">Source</th>
            <th scope="col" className="px-3 py-2 font-semibold">Monitoring health</th>
            <th scope="col" className="px-3 py-2 font-semibold" title="Last recorded check for this source (UTC), not necessarily a successful one">
              Last check
            </th>
            <th scope="col" className="px-3 py-2 text-right font-semibold">Days w/ proof</th>
            <th scope="col" className="px-3 py-2 text-right font-semibold">Gap days</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(s => {
            const flagged = s.health !== 'healthy'
            const gapDays = Number(s.gap_days || 0)
            return (
              <tr
                key={s.source_id}
                className={`border-b border-[var(--border-muted)] align-top ${flagged ? 'bg-amber-500/[0.04]' : ''}`}
              >
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1.5">
                    {flagged && <TriangleAlert className="h-3 w-3 flex-shrink-0 text-amber-400" aria-hidden="true" />}
                    <span className="font-medium text-[var(--text-primary)]">{s.source_name || s.source_id}</span>
                  </div>
                  {s.gap_disclosure && (
                    <p className="mt-0.5 text-[11px] leading-tight text-amber-300/80">{s.gap_disclosure}</p>
                  )}
                  {Array.isArray(s.degraded_reasons) && s.degraded_reasons.length > 0 && (
                    <ul className="mt-1 space-y-0.5">
                      {s.degraded_reasons.map((reason, i) => (
                        <li key={i} className="text-[11px] leading-tight text-[var(--text-muted)]">— {reason}</li>
                      ))}
                    </ul>
                  )}
                </td>
                <td className="px-3 py-2.5"><HealthBadge status={s.health} /></td>
                <td className="px-3 py-2.5 text-[var(--text-secondary)]">
                  <TimeStamp value={s.last_check_utc} mode="absolute" fallback="none recorded" />
                </td>
                <td className="px-3 py-2.5 text-right font-mono tabular-nums text-[var(--text-primary)]">
                  {s.days_with_proof_hash}/{s.expected_days}
                </td>
                <td className={`px-3 py-2.5 text-right font-mono tabular-nums ${gapDays > 0 ? 'text-amber-300' : 'text-[var(--text-secondary)]'}`}>
                  {gapDays}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

/**
 * Monitoring health — live operational-status surface.
 *
 * For a chosen period (default: last 30 days) it shows, per monitored source,
 * whether the automated checks are healthy, when the last check was recorded,
 * and where coverage has gaps. It reuses the existing coverage-certificate
 * evidence (`reports.coverageCertificate`, format=json) and the existing
 * `/api/health` signal — no new backend. Nothing here is a compliance or legal
 * status.
 */
export default function MonitoringHealthPage() {
  const [periodStart, setPeriodStart] = useState(daysAgo(DEFAULT_PERIOD_DAYS - 1))
  const [periodEnd, setPeriodEnd] = useState(isoDay(new Date()))
  const [status, setStatus] = useState('loading') // loading | loaded | error
  const [cert, setCert] = useState(null)
  const [system, setSystem] = useState(undefined) // undefined = not checked, null = unreachable
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setStatus('loading')
    setError('')

    // Best-effort system health — a genuine failure marks it unreachable but never
    // blocks the primary per-source coverage below.
    healthApi.get()
      .then(data => { if (active) setSystem(data) })
      .catch(() => { if (active) setSystem(null) })

    reports.coverageCertificate({ periodStart, periodEnd, format: 'json' })
      .then(data => {
        if (!active) return
        if (data.status !== 'ok' || !data.certificate) {
          throw new Error(data.message || 'Could not load monitoring health.')
        }
        setCert(data.certificate)
        setStatus('loaded')
      })
      .catch(err => {
        if (!active) return
        setError(err.message || 'Could not load monitoring health.')
        setStatus('error')
      })

    return () => { active = false }
  }, [periodStart, periodEnd, reloadKey])

  function retry() {
    setReloadKey(k => k + 1)
  }

  const sources = cert?.sources || []
  const rows = sources
    .map(s => ({ ...s, health: deriveHealth(s) }))
    .sort((a, b) =>
      (HEALTH_RANK[a.health] - HEALTH_RANK[b.health]) ||
      String(a.source_name || a.source_id).localeCompare(String(b.source_name || b.source_id)),
    )

  const counts = rows.reduce(
    (acc, r) => {
      acc[r.health] += 1
      if (Number(r.gap_days || 0) > 0) acc.withGaps += 1
      return acc
    },
    { healthy: 0, stale: 0, degraded: 0, no_coverage: 0, withGaps: 0 },
  )

  return (
    <div className="space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="mb-1 flex items-center gap-2 text-lg font-bold text-white">
            <Activity className="h-5 w-5 text-[var(--accent)]" aria-hidden="true" />
            Monitoring health
          </h1>
          <p className="max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
            Operational status of the automated checks: for each monitored source, whether the checks
            are current, when the last check was recorded, and where coverage has gaps. This reports
            whether the checks ran — it is not a compliance, legal, or regulatory status.
          </p>
        </div>
        <button
          type="button"
          onClick={retry}
          disabled={status === 'loading'}
          className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] transition-colors hover:border-[var(--trust-border)] hover:text-white disabled:opacity-60"
        >
          <RotateCw className={`h-3.5 w-3.5 ${status === 'loading' ? 'animate-spin' : ''}`} aria-hidden="true" />
          {status === 'loading' ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      <div className="sp-command-panel space-y-4 p-5">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold text-[var(--text-muted)]">From</span>
            <input
              type="date"
              value={periodStart}
              max={periodEnd}
              onChange={e => setPeriodStart(e.target.value)}
              disabled={status === 'loading'}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-semibold text-[var(--text-muted)]">To</span>
            <input
              type="date"
              value={periodEnd}
              min={periodStart}
              onChange={e => setPeriodEnd(e.target.value)}
              disabled={status === 'loading'}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
            />
          </label>
          <p className="pb-2 text-[11px] text-[var(--text-muted)]">
            Health is derived from recorded checks in this window.
          </p>
        </div>

        <SystemStatus system={system} />

        {status === 'loading' && <LoadingSkeleton />}

        {status === 'error' && (
          <ErrorState
            title="Could not load monitoring health."
            detail={`${error} Nothing is inferred — only recorded checks are shown.`}
            onRetry={retry}
          />
        )}

        {status === 'loaded' && (
          rows.length === 0 ? (
            <EmptyState icon={Activity} title="No monitored sources resolved for this period.">
              Enable sources and let a monitoring run record its first check, then the health of each
              source appears here. A source with no successful check is shown as No coverage, never hidden.
            </EmptyState>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
                <Tile label="Monitored" value={rows.length} />
                <Tile label="Healthy" value={counts.healthy} tone={counts.healthy ? 'good' : 'default'} />
                <Tile label="Stale" value={counts.stale} tone={counts.stale ? 'warn' : 'default'} />
                <Tile label="Degraded" value={counts.degraded} tone={counts.degraded ? 'warn' : 'default'} />
                <Tile label="No coverage" value={counts.no_coverage} tone={counts.no_coverage ? 'bad' : 'default'} />
                <Tile label="With gaps" value={counts.withGaps} tone={counts.withGaps ? 'warn' : 'default'} />
              </div>

              <HealthTable rows={rows} />
            </div>
          )
        )}
      </div>

      <div className="flex items-start gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--text-muted)]" aria-hidden="true" />
        <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
          Every status is derived from real recorded source-run evidence; a source with no successful
          check is shown as Stale or No coverage, never hidden and never shown as healthy. {DISCLAIMER}
        </p>
      </div>
    </div>
  )
}

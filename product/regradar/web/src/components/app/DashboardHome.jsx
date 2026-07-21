import { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle, Clock } from 'lucide-react'

import { telegramPair, sources as sourcesApi, delivery } from '../../api'
import PlanBanner from './PlanBanner'
import SampleAlertEmptyState from './EmptyState'
import { isUnactivatedFreeAccount } from '../../data/mockData'
import { getWorkspaceProfile, profileLabel } from '../../data/workspaceProfile'
import DeadlinesPanel from './DeadlinesPanel'
import FirstRunBackfillPanel from './FirstRunBackfillPanel'
import PressureScore from './PressureScore'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import ErrorState from './ui/ErrorState'
import { hoursSince, fullStamp, timeAgo } from '../../utils/time'

const COV_COLOR = {
  emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  amber:   'text-amber-400 bg-amber-500/10 border-amber-500/20',
  slate:   'text-[var(--text-secondary)] bg-[var(--bg-raised)] border-[var(--border)]',
}

// DH-6: only genuinely-blocked sources belong here. AE-sca-regulations-listing was
// promoted to fresh_alert in the registry, so hardcoding it as "Needs remediation"
// under-claimed and contradicted the public site. (Guarded by
// coverageClaimsHonesty.test.js: no id here may be fresh_alert in sources.json.)
const REMEDIATION_SOURCE_IDS = new Set([
  'AE-uae-legislation-portal',
  'AE-uae-financial-intelligence-unit-uaefiu',
])

function StatusPill({ tone = 'slate', children }) {
  const styles = {
    emerald: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
    amber: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
    cyan: 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)]',
    rose: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
    slate: 'border-[var(--border)] bg-[var(--bg-raised)] text-[var(--text-primary)]',
  }
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold ${styles[tone] || styles.slate}`}>
      {children}
    </span>
  )
}

/**
 * Truthful monitoring freshness indicator derived from the most recent
 * recorded run. Never claims "active" — states when the last check happened
 * and flags staleness beyond 48 hours.
 */
function MonitoringFreshness({ lastRunAt }) {
  if (!lastRunAt) {
    return (
      <span
        title="No monitoring run has been recorded yet."
        className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--bg-raised)] px-2.5 py-1 text-[11px] font-semibold text-[var(--text-primary)]"
      >
        <Clock className="h-3.5 w-3.5" aria-hidden="true" />
        No runs recorded
      </span>
    )
  }
  const hours = hoursSince(lastRunAt)
  const stale = hours != null && hours > 48
  return (
    <span
      title={`Most recent recorded monitoring run: ${fullStamp(lastRunAt)}. ${
        stale ? 'This is older than 48 hours — treat monitored data as stale.' : ''
      }`.trim()}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
        stale
          ? 'border-amber-400/25 bg-amber-400/10 text-amber-300'
          : 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'
      }`}
    >
      <Clock className="h-3.5 w-3.5" aria-hidden="true" />
      {stale ? `Last check ${timeAgo(lastRunAt)} — stale` : `Last check ${timeAgo(lastRunAt)}`}
    </span>
  )
}

function displayPlanName(planState) {
  if (planState?.plan_name === 'evidence_preview') return 'Source Readiness Review'
  return planState?.plan_display || 'Source Readiness Review'
}

function ProfileSummaryCard({ profile, currentUser, navigate, planState }) {
  const hasProfile = profile.markets.length > 0 || profile.industries.length > 0 || profile.topics.length > 0
  const company = profile.company || currentUser?.company_name || 'Profile workspace'
  const planLabel = displayPlanName(planState)

  return (
    <div className="sp-glass sp-animate-fade-up border-[var(--trust-border)] p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex flex-wrap gap-2">
            <StatusPill tone="cyan">{planLabel}</StatusPill>
            <StatusPill tone={hasProfile ? 'emerald' : 'amber'}>
              {hasProfile ? 'Profile saved' : 'Profile setup'}
            </StatusPill>
          </div>
          <h1 className="text-xl font-bold text-white">UAE-first pilot workspace</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            {company}. Your selected source layers are listed below; our team activates monitoring after the readiness review.
          </p>
        </div>
        <button
          onClick={() => navigate('settings')}
          className="rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--border)] hover:text-white"
        >
          Edit profile
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold text-[var(--text-muted)]">Company</p>
          <p className="truncate text-sm text-[var(--text-primary)]">{company}</p>
        </div>
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold text-[var(--text-muted)]">Markets</p>
          <p className="truncate text-sm text-[var(--text-primary)]">{profile.markets.length ? profile.markets.join(', ') : 'Select in Settings'}</p>
        </div>
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold text-[var(--text-muted)]">Regulatory profile</p>
          <p className="truncate text-sm text-[var(--text-primary)]">{profile.industries.length ? profile.industries.join(', ') : 'Select in Settings'}</p>
        </div>
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold text-[var(--text-muted)]">Source layers</p>
          <p className="truncate text-sm text-[var(--text-primary)]">{profile.topics.length ? profile.topics.join(', ') : 'Select in Settings'}</p>
        </div>
      </div>
    </div>
  )
}

function WorkspaceChecklist({ profile, telegramStatus, telegramLoading, navigate }) {
  const hasProfile = profile.markets.length > 0 || profile.industries.length > 0 || profile.topics.length > 0
  const connected = Boolean(telegramStatus?.connected)
  const items = [
    { label: 'Account created', detail: 'Signed-in workspace account', status: 'Complete', tone: 'emerald' },
    { label: 'Profile saved', detail: hasProfile ? profileLabel(profile) : 'Add markets and licence profile', status: hasProfile ? 'Complete' : 'Pending', tone: hasProfile ? 'emerald' : 'amber', action: 'settings' },
    { label: 'Telegram connected', detail: connected ? 'Account pairing confirmed' : telegramStatus?.status_error ? 'Status check failed — open Integrations to retry' : 'Connect Telegram in Integrations', status: connected ? 'Complete' : telegramLoading ? 'Checking' : telegramStatus?.status_error ? 'Unavailable' : 'Pending', tone: connected ? 'emerald' : 'amber', action: 'integrations' },
    { label: 'Source map reviewed', detail: 'Review fresh-alert eligible, limited, and access-restricted sources', status: 'To do', tone: 'slate', action: 'sources' },
    { label: 'First reviewed brief', detail: 'Preview a reviewed brief by email or Telegram once review gates pass', status: 'Preview', tone: 'slate', action: 'briefs' },
  ]

  return (
    <div className="sp-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Pilot setup checklist</h2>
        <StatusPill tone="cyan">Pilot setup</StatusPill>
      </div>
      <div className="space-y-3">
        {items.map(item => (
          <button
            key={item.label}
            type="button"
            onClick={() => item.action && navigate(item.action)}
            className="w-full rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3 text-left transition-colors hover:border-[var(--border)]"
          >
            <div className="flex items-start gap-3">
              <CheckCircle className={`mt-0.5 h-4 w-4 flex-shrink-0 ${item.tone === 'emerald' ? 'text-emerald-300' : item.tone === 'amber' ? 'text-amber-300' : 'text-[var(--text-muted)]'}`} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-[var(--text-primary)]">{item.label}</p>
                  <StatusPill tone={item.tone}>{item.status}</StatusPill>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{item.detail}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function WhatHappensNextCard() {
  const steps = [
    ['Source readiness review', 'The StatuteProof team reviews your selected sources — usually within about 2 business days.'],
    ['A specialist contacts you', 'A StatuteProof specialist emails you to confirm your source pack and any limits before activation.'],
    ['We switch on monitoring', 'Live monitoring is activated by the StatuteProof team for the approved sources. You do not have to trigger it yourself.'],
  ]
  return (
    <div className="sp-panel p-5">
      <div className="mb-3 flex items-start gap-2">
        <Clock className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--accent)]" />
        <div>
          <h2 className="text-sm font-semibold text-white">What happens next</h2>
          <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">
            You have done your part. Live monitoring is switched on by our team — here is the rest of the path.
          </p>
        </div>
      </div>
      <ol className="space-y-3">
        {steps.map(([title, detail], index) => (
          <li key={title} className="flex gap-3">
            <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--trust-badge)] text-[11px] font-bold text-[var(--accent)]">
              {index + 1}
            </span>
            <div>
              <p className="text-xs font-semibold text-[var(--text-primary)]">{title}</p>
              <p className="mt-0.5 text-[11px] leading-relaxed text-[var(--text-muted)]">{detail}</p>
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-4 border-t border-[var(--border-muted)] pt-3 text-[11px] leading-relaxed text-[var(--text-secondary)]">
        No payment is taken during the founding pilot until activation is confirmed. Monitoring intelligence only. Not legal advice.
      </p>
    </div>
  )
}

function SourceReadinessCard({ navigate }) {
  return (
    <div className="sp-panel p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Source readiness</h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">Mapped does not mean approved for monitoring.</p>
        </div>
        <StatusPill tone="cyan">Activation readiness in progress</StatusPill>
      </div>

      <div className="space-y-2.5 text-sm text-[var(--text-secondary)]">
        {[
          'Monitoring activation requires evidence and baseline runs.',
          'Under-validation sources are disclosed before pilot scope.',
          'Limitations are reviewed before relying on a source map.',
        ].map(text => (
          <div key={text} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[var(--accent)]" />
            <span>{text}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => navigate('sources')}
        className="mt-5 w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[var(--ink)] transition-colors hover:bg-[var(--accent-hover)]"
      >
        Review source map
      </button>
      <button
        onClick={() => navigate('source-lab')}
        className="mt-2 w-full rounded-lg border border-[var(--trust-border)] px-4 py-2.5 text-sm font-semibold text-[var(--accent)] transition-colors hover:border-[var(--trust-border)]"
      >
        Open Source Lab
      </button>
    </div>
  )
}

// Derive summary widgets from real sources/status and sources/summary API responses
function buildWidgets(sourcesData, sourceSummary) {
  if (!sourcesData) return null
  const { sources = [], summary = {} } = sourcesData
  const changed   = summary.CHANGED     || 0
  const failed    = summary.FAILED      || 0
  const qualityDrop = summary.QUALITY_DROP || 0
  const firstSeen = summary.FIRST_SEEN  || 0
  const highRiskPending = sources.filter(s => s.change_status === 'CHANGED' || s.change_status === 'FIRST_SEEN').length
  return {
    enabledSources: sourceSummary?.enabled_count ?? sources.length,
    changedThisWeek: changed + firstSeen,
    failedSources: failed + qualityDrop,
    evidenceRecords: sources.filter(s => s.change_status !== 'NOT_RUN').length,
    reviewRequired: highRiskPending,
  }
}

const EXTRACTION_CLS = {
  GOOD:    'text-emerald-400',
  OK:      'text-amber-400',
  POOR:    'text-red-400',
  UNKNOWN: 'text-[var(--text-muted)]',
}

// Map a source row to one canonical status code understood by StatusBadge.
function readinessCode(source) {
  if (REMEDIATION_SOURCE_IDS.has(source.source_id)) return 'Needs remediation'
  if (source.change_status === 'FAILED' || source.access_status === 'failed') return 'FAILED'
  if (source.change_status === 'QUALITY_DROP') return 'QUALITY_DROP'
  if (source.change_status && source.change_status !== 'NOT_RUN') return 'Readiness supported'
  return 'Monitoring not started'
}

function CommandMetric({ label, value, tone = 'slate', detail }) {
  const toneClass = {
    cyan: 'border-[var(--trust-border)] bg-[var(--trust-badge)] text-[var(--accent)]',
    emerald: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
    amber: 'border-amber-400/25 bg-amber-400/10 text-amber-100',
    slate: 'border-[var(--border)] bg-[var(--bg-base)] text-[var(--text-primary)]',
  }[tone] || 'border-[var(--border)] bg-[var(--bg-base)] text-[var(--text-primary)]'

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-[11px] font-semibold opacity-70">{label}</p>
      <p className="sp-mono mt-2 text-3xl font-bold">{value}</p>
      {detail && <p className="mt-1 text-xs leading-relaxed opacity-70">{detail}</p>}
    </div>
  )
}

function EvidenceChainPanel() {
  const steps = [
    ['Source run', 'official source checked', 'done'],
    ['Canonical evidence', 'hash + proof verified', 'done'],
    ['Human review', 'reviewer decision needed', 'review'],
    ['Alert link', 'route to queue', 'review'],
    ['Draft brief', 'allowed after evidence', 'blocked'],
    ['Delivery approval', 'explicit separate gate', 'blocked'],
  ]

  return (
    <div className="sp-command-panel p-5">
      <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">Evidence-to-brief chain</h2>
          <p className="mt-1 max-w-3xl text-xs leading-relaxed text-[var(--text-muted)]">
            This is the internal gate map. A source change becomes a customer artifact only after every required gate passes.
          </p>
        </div>
        <StatusPill tone="slate">Customer delivery stays off until you approve</StatusPill>
      </div>

      <div className="sp-evidence-chain">
        {steps.map(([title, detail, state]) => (
          <div key={title} className={`sp-evidence-step ${state === 'blocked' ? 'is-blocked' : ''}`}>
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${
                state === 'done' ? 'bg-emerald-300' : state === 'review' ? 'bg-amber-300' : 'bg-[var(--bg-raised)]'
              }`} />
              <span className="text-[10px] font-bold text-[var(--text-muted)]">{state}</span>
            </div>
            <p className="text-xs font-semibold text-white">{title}</p>
            <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-muted)]">{detail}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// Review-queue summary on the dashboard. Fetches the same delivery preview that
// PressureScore uses and reflects the REAL reviewed-alert count — it must never
// assert "nothing is ready" when alerts exist (that is an active
// "nothing needs attention" misstatement on the primary screen). Falls back to
// the honest empty state only when the preview genuinely has zero matches.
function ReviewQueueSummary({ navigate, planState }) {
  const [count, setCount] = useState(null)   // null = loading, number = matches
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let active = true
    delivery.preview(14)
      .then(res => { if (active) setCount((res.preview?.matches || []).length) })
      .catch(() => { if (active) { setFailed(true); setCount(0) } })
    return () => { active = false }
  }, [])

  const hasAlerts = typeof count === 'number' && count > 0

  return (
    <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Review queue</h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            Customer alerts appear only after monitored evidence is reviewed and routed.
          </p>
        </div>
        <StatusPill tone="cyan">Live workspace</StatusPill>
      </div>

      {hasAlerts ? (
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-5 py-6">
          <p className="mb-1 text-sm text-[var(--text-primary)]">
            <span className="font-mono tabular-nums text-base font-semibold">{count}</span>{' '}
            reviewed customer alert{count === 1 ? '' : 's'} matched to this workspace in the last 14 days.
          </p>
          <p className="mb-4 text-xs text-[var(--text-secondary)]">
            Open Reviewed Alerts to triage, seal decisions, and preview delivery. Monitoring information only. Not legal advice.
          </p>
          <button
            onClick={() => navigate('alerts')}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:border-[var(--accent)]"
          >
            View reviewed alerts <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : !failed && count === 0 && isUnactivatedFreeAccount(planState) ? (
        // Genuinely empty AND unactivated: stand in with the clearly-labelled
        // first-session sample so a free account can see the evidence loop.
        <SampleAlertEmptyState />
      ) : (
        <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-5 py-8 text-center">
          <p className="mb-1 text-sm text-[var(--text-primary)]">
            {failed
              ? 'Reviewed alerts could not be loaded right now.'
              : count === null
                ? 'Checking for reviewed customer alerts…'
                : 'No reviewed customer alerts are ready for this workspace yet.'}
          </p>
          <p className="text-xs text-[var(--text-secondary)]">
            {failed
              ? 'The reviewed-alerts preview could not be loaded — this is not a confirmation that none exist. Open Reviewed Alerts to retry.'
              : 'Reviewed alerts appear after evidence records pass human review and delivery routing. No sample alerts are shown in the authenticated dashboard.'}
          </p>
        </div>
      )}
    </div>
  )
}

export default function DashboardHome({ navigate, currentUser, planState, onChoosePlan }) {
  const profile = getWorkspaceProfile()

  const [telegramStatus, setTelegramStatus]   = useState(null)
  const [telegramLoading, setTelegramLoading] = useState(true)
  const [sourcesData, setSourcesData]         = useState(null)
  const [sourceSummary, setSourceSummary]     = useState(null)
  const [sourcesLoading, setSourcesLoading]   = useState(true)
  const [sourcesError, setSourcesError]       = useState('')

  useEffect(() => {
    let active = true
    telegramPair.status()
      .then(data => { if (active) setTelegramStatus(data) })
      .catch(() => { if (active) setTelegramStatus({ status_error: true }) })
      .finally(() => { if (active) setTelegramLoading(false) })
    return () => { active = false }
  }, [])

  // Same two API calls as before; reloadKey lets the error state retry them.
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([sourcesApi.status('AE'), sourcesApi.summary('AE')])
      .then(([statusData, summaryData]) => {
        if (!active) return
        setSourcesData(statusData)
        setSourceSummary(summaryData)
        setSourcesError('')
      })
      .catch(err => { if (active) setSourcesError(err.message || 'Could not load source status.') })
      .finally(() => { if (active) setSourcesLoading(false) })
    return () => { active = false }
  }, [reloadKey])

  function retrySources() {
    setSourcesLoading(true)
    setSourcesError('')
    setReloadKey(k => k + 1)
  }

  const widgets = buildWidgets(sourcesData, sourceSummary)
  const attentionItems = [
    {
      label: 'Source-health flags',
      value: sourcesLoading ? '—' : widgets?.failedSources ?? 0,
      detail: 'Failed or quality-drop runs that need operator review.',
      tone: (widgets?.failedSources ?? 0) > 0 ? 'amber' : 'emerald',
      action: 'sources',
    },
    {
      label: 'Changes needing review',
      value: sourcesLoading ? '—' : widgets?.reviewRequired ?? 0,
      detail: 'Changed or first-seen sources before customer conclusions.',
      tone: (widgets?.reviewRequired ?? 0) > 0 ? 'amber' : 'emerald',
      action: 'review-queue',
    },
    {
      label: 'Coverage limits',
      value: sourceSummary ? `${(sourceSummary.candidate_count ?? 0) + (sourceSummary.remediation_count ?? 0)}` : '—',
      detail: 'Sources still in validation are excluded from your alert coverage — disclosed, not hidden.',
      tone: ((sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0)) > 0 ? 'amber' : 'emerald',
      action: 'sources',
    },
    {
      label: 'Brief delivery',
      value: 'Not yet enabled',
      detail: 'Switched on by our team after your source readiness review — nothing you need to fix.',
      tone: 'slate',
      action: 'briefs',
    },
  ]

  // Source status table — operator surface, rendered inside the collapsed
  // Monitoring operations block (2.2).
  function renderSourceTable() {
    if (sourcesLoading || sourcesError || !(sourcesData?.sources?.length > 0)) return null
    return (

        <div className="sp-panel p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Source status</h2>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Current monitoring status and extraction readiness for all active UAE sources.</p>
            </div>
            <span title="Rows come directly from the monitoring API for this workspace — no sample data." className="rounded-md border border-[var(--border)] bg-[var(--bg-raised)] px-2.5 py-1 text-[10px] font-semibold text-[var(--text-primary)]">Live data</span>
          </div>
          <div className="overflow-x-auto rounded-lg border border-[var(--border-muted)]">
            <table className="sp-table min-w-[860px]">
              <thead>
                <tr>
                  {['Source', 'Regulator', 'Last checked', 'Readiness', 'Extraction quality', 'Evidence', 'Action'].map(h => (
                    <th key={h} className="whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-muted)]">
                {sourcesData.sources.slice(0, 12).map(s => (
                  <tr key={s.source_id} className="transition-colors hover:bg-[var(--bg-raised)]">
                    <td className="font-medium text-white max-w-[260px] truncate">{s.name}</td>
                    <td className="text-[var(--text-secondary)] whitespace-nowrap">{s.category?.replace(/_/g, ' ') || '—'}</td>
                    <td className="text-[var(--text-muted)] whitespace-nowrap">
                      <TimeStamp value={s.last_run_at} fallback="Not run yet" />
                    </td>
                    <td className="whitespace-nowrap">
                      <StatusBadge code={readinessCode(s)} />
                    </td>
                    <td className={`whitespace-nowrap font-medium ${EXTRACTION_CLS[String(s.extraction_quality || '').toUpperCase()] || EXTRACTION_CLS.UNKNOWN}`}>
                      {s.extraction_quality ? String(s.extraction_quality).toLowerCase().replace(/^./, c => c.toUpperCase()) : 'Unknown'}
                    </td>
                    <td className="whitespace-nowrap">
                      <StatusBadge code={s.change_status && s.change_status !== 'NOT_RUN' ? 'PROOF_RECORDED' : 'AWAITING_RUN'} />
                    </td>
                    <td className="whitespace-nowrap">
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[var(--accent)] hover:underline text-xs font-semibold"
                      >
                        View source
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-[var(--text-secondary)]">
            {sourcesData.disclaimer || 'Not legal advice. For monitoring information only.'}
          </p>
        </div>
    )
  }

  return (
    <div className="min-h-full space-y-5 bg-[var(--bg-navy)] p-5 pb-10">
      <PlanBanner planState={planState} onChoosePlan={onChoosePlan} />

      <div className="sp-command-hero p-5 lg:p-6">
        <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="sp-heading max-w-4xl text-2xl font-semibold leading-tight text-white md:text-3xl">
                {sourcesError
                  ? 'Source readiness summary is unavailable right now.'
                  : sourcesLoading
                  ? 'Loading UAE source readiness summary…'
                  : `${sourceSummary?.fresh_alert_count ?? sourceSummary?.readiness_supported_count ?? 0} sources eligible for fresh alerts · ${((sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0)) || 0} scope limitations disclosed`}
              </h1>
              {!sourcesLoading && !sourcesError && (
                <MonitoringFreshness lastRunAt={sourceSummary?.last_run_at} />
              )}
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
              Review what changed and what needs a decision before relying on any alert,
              brief draft, or source claim. Monitoring intelligence only — not legal advice.
            </p>

            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {attentionItems.map(item => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => navigate(item.action)}
                  className="group rounded-2xl border border-[var(--border-muted)] bg-[var(--bg-base)] p-4 text-left transition hover:-translate-y-0.5 hover:border-[var(--trust-border)] hover:bg-[var(--bg-elevated)]"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <p className="text-[11px] font-bold text-[var(--text-muted)]">{item.label}</p>
                    <StatusPill tone={item.tone}>{item.tone === 'emerald' ? 'OK' : item.tone === 'amber' ? 'Review' : 'Pending'}</StatusPill>
                  </div>
                  <p className={typeof item.value === 'number' ? 'sp-mono text-3xl font-semibold text-white' : `font-semibold text-white ${String(item.value).length > 10 ? 'text-lg leading-snug' : 'text-3xl'}`}>{item.value}</p>
                  <p className="mt-2 min-h-[2.4rem] text-xs leading-relaxed text-[var(--text-muted)]">{item.detail}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[var(--accent)]">
                    Open <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-[var(--border-muted)] bg-[var(--bg-base)] p-5">
            <p className="text-xs font-semibold text-[var(--text-muted)]">Recommended next step</p>
            <h2 className="mt-2 text-lg font-semibold text-white">See what changed first.</h2>
            <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
              Open the review queue to see the latest sealed changes from your
              monitored sources and decide what matters for your firm. Every
              record carries its hash, timestamp and diff.
            </p>
            <button
              type="button"
              onClick={() => navigate('review-queue')}
              className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[var(--ink)] transition hover:bg-[var(--accent-hover)]"
            >
              Open the review queue <ArrowRight className="h-4 w-4" />
            </button>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <CommandMetric label="Enabled" value={sourceSummary?.enabled_count ?? '—'} detail="source records" />
              <CommandMetric label="Fresh-alert eligible" value={sourceSummary?.readiness_supported_count ?? '—'} tone="emerald" detail="validated for alerts" />
              <CommandMetric label="Limited scope" value={(sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0) || '—'} tone="amber" detail="excluded from claims" />
              <CommandMetric label="Evidence records" value={widgets?.evidenceRecords ?? '—'} detail="runs with proof data" />
            </div>
          </div>
        </div>
      </div>

      <ProfileSummaryCard profile={profile} currentUser={currentUser} navigate={navigate} planState={planState} />

      {sourcesError && (
        <ErrorState
          title="Could not load source status."
          detail={sourcesError}
          onRetry={retrySources}
          className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]"
        />
      )}

      {/* 2.2: operator surfaces live in a collapsed block — the customer's
          first screen leads with their sealed changes and review queue, not
          the internal gate map and ops tables. */}
      <details className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)]">
        <summary className="cursor-pointer select-none px-5 py-4 text-sm font-semibold text-[var(--text-secondary)] transition-colors hover:text-white">
          Monitoring operations — gate map, pressure score and per-source status
        </summary>
        <div className="space-y-5 px-5 pb-5">
          <EvidenceChainPanel />
          <PressureScore />
          {renderSourceTable()}
        </div>
      </details>


      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <ReviewQueueSummary navigate={navigate} planState={planState} />

          {/* First-run backfill: shows the latest already-sealed changes only
              while the alerts preview is empty; renders nothing otherwise. */}
          <FirstRunBackfillPanel />

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-white">Brief delivery readiness</h2>
                <StatusPill tone="cyan">Preview</StatusPill>
              </div>
              <div className="space-y-4 text-xs">
                <p className="leading-relaxed text-[var(--text-primary)]">
                  Reviewed weekly briefs render to Markdown/HTML for preview before anything reaches your inbox.
                  External email delivery is switched on by our team, never automatically.
                </p>
                <button onClick={() => navigate('integrations')} className="w-full rounded-lg border border-[var(--trust-border)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:border-[var(--trust-border)]">
                  Open delivery settings
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
              <h2 className="mb-4 text-sm font-semibold text-white">Source pack scope</h2>
              <div className="grid grid-cols-3 gap-2">
                <div className={`rounded-lg border p-3 text-center ${COV_COLOR.emerald}`}>
                  <span className="sp-mono text-lg font-bold">{sourceSummary?.fresh_alert_count ?? sourceSummary?.readiness_supported_count ?? '—'}</span>
                  <span className="mt-1 block text-xs">fresh-alert</span>
                </div>
                <div className={`rounded-lg border p-3 text-center ${COV_COLOR.amber}`}>
                  <span className="sp-mono text-lg font-bold">{sourceSummary?.evidence_library_count ?? '—'}</span>
                  <span className="mt-1 block text-xs">evidence-library</span>
                </div>
                <div className={`rounded-lg border p-3 text-center ${COV_COLOR.slate}`}>
                  <span className="sp-mono text-lg font-bold">Scoped</span>
                  <span className="mt-1 block text-xs">selected sources only</span>
                </div>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
                Coverage indicators are source-readiness signals, not a statement of complete market coverage.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <WorkspaceChecklist profile={profile} telegramStatus={telegramStatus} telegramLoading={telegramLoading} navigate={navigate} />
          <WhatHappensNextCard />
          <SourceReadinessCard navigate={navigate} />
          <DeadlinesPanel />

          <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
            <div className="mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-300" />
              <h2 className="text-sm font-semibold text-white">Delivery status</h2>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Manual reviewed-alert preview delivery is available from Alerts when Telegram is connected. Automatic scheduled delivery is not enabled yet.
            </p>
            <button
              onClick={() => navigate('sources')}
              className="mt-4 w-full rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--border)] hover:text-white"
            >
              Start with source readiness
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

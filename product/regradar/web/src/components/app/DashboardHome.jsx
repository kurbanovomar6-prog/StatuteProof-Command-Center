import { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle, Clock } from 'lucide-react'

import { telegramPair, sources as sourcesApi } from '../../api'
import PlanBanner from './PlanBanner'
import { getWorkspaceProfile, profileLabel } from '../../data/workspaceProfile'
import DeadlinesPanel from './DeadlinesPanel'
import PressureScore from './PressureScore'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import ErrorState from './ui/ErrorState'
import { hoursSince, fullStamp, timeAgo } from '../../utils/time'

const COV_COLOR = {
  emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  amber:   'text-amber-400 bg-amber-500/10 border-amber-500/20',
  slate:   'text-slate-400 bg-slate-500/10 border-slate-500/20',
}

const REMEDIATION_SOURCE_IDS = new Set([
  'AE-uae-legislation-portal',
  'AE-uae-financial-intelligence-unit-uaefiu',
  'AE-sca-regulations-listing',
])

function StatusPill({ tone = 'slate', children }) {
  const styles = {
    emerald: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
    amber: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
    cyan: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',
    rose: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
    slate: 'border-slate-600 bg-slate-800/80 text-slate-300',
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
        className="inline-flex items-center gap-1.5 rounded-full border border-slate-600 bg-slate-800/80 px-2.5 py-1 text-[11px] font-semibold text-slate-300"
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
    <div className="sp-glass sp-animate-fade-up border-cyan-400/20 p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex flex-wrap gap-2">
            <StatusPill tone="cyan">{planLabel}</StatusPill>
            <StatusPill tone={hasProfile ? 'emerald' : 'amber'}>
              {hasProfile ? 'Profile saved' : 'Profile setup'}
            </StatusPill>
          </div>
          <h1 className="text-xl font-bold text-white">UAE-first pilot workspace</h1>
          <p className="mt-1 text-sm text-slate-400">
            {company}. Source layers are shown for review and validation; activation requires proof/diff validation.
          </p>
        </div>
        <button
          onClick={() => navigate('settings')}
          className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
        >
          Edit profile
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-slate-800 bg-slate-950/45 px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Company</p>
          <p className="truncate text-sm text-slate-200">{company}</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/45 px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Markets</p>
          <p className="truncate text-sm text-slate-200">{profile.markets.length ? profile.markets.join(', ') : 'Select in Settings'}</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/45 px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Regulatory profile</p>
          <p className="truncate text-sm text-slate-200">{profile.industries.length ? profile.industries.join(', ') : 'Select in Settings'}</p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/45 px-3 py-2.5">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Source layers</p>
          <p className="truncate text-sm text-slate-200">{profile.topics.length ? profile.topics.join(', ') : 'Select in Settings'}</p>
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
    { label: 'Telegram connected', detail: connected ? 'Account pairing confirmed' : 'Connect Telegram in Integrations', status: connected ? 'Complete' : telegramLoading ? 'Checking' : 'Pending', tone: connected ? 'emerald' : 'amber', action: 'integrations' },
    { label: 'Source map reviewed', detail: 'Review fresh-alert eligible, limited, and access-restricted sources', status: 'To do', tone: 'slate', action: 'sources' },
    { label: 'First reviewed brief', detail: 'Use email test-mode or Telegram preview only after review gates pass', status: 'Test mode', tone: 'slate', action: 'briefs' },
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
            className="w-full rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3 text-left transition-colors hover:border-slate-700"
          >
            <div className="flex items-start gap-3">
              <CheckCircle className={`mt-0.5 h-4 w-4 flex-shrink-0 ${item.tone === 'emerald' ? 'text-emerald-300' : item.tone === 'amber' ? 'text-amber-300' : 'text-slate-500'}`} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-slate-200">{item.label}</p>
                  <StatusPill tone={item.tone}>{item.status}</StatusPill>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.detail}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function SourceReadinessCard({ navigate }) {
  return (
    <div className="sp-panel p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Source readiness</h2>
          <p className="mt-1 text-xs text-slate-500">Mapped does not mean approved for monitoring.</p>
        </div>
        <StatusPill tone="cyan">Activation readiness in progress</StatusPill>
      </div>

      <div className="space-y-2.5 text-sm text-slate-400">
        {[
          'Monitoring activation requires evidence and baseline runs.',
          'Under-validation sources are disclosed before pilot scope.',
          'Limitations are reviewed before relying on a source map.',
        ].map(text => (
          <div key={text} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#16D9F5]" />
            <span>{text}</span>
          </div>
        ))}
      </div>

      <button
        onClick={() => navigate('sources')}
        className="mt-5 w-full rounded-lg bg-[#16D9F5] px-4 py-2.5 text-sm font-semibold text-[#07111F] transition-colors hover:bg-[#11c2db]"
      >
        Review source map
      </button>
      <button
        onClick={() => navigate('source-lab')}
        className="mt-2 w-full rounded-lg border border-cyan-400/25 px-4 py-2.5 text-sm font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50"
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
  UNKNOWN: 'text-slate-500',
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
    cyan: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-100',
    emerald: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
    amber: 'border-amber-400/25 bg-amber-400/10 text-amber-100',
    slate: 'border-slate-700 bg-slate-950/55 text-slate-200',
  }[tone] || 'border-slate-700 bg-slate-950/55 text-slate-200'

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-[11px] font-semibold uppercase tracking-wide opacity-70">{label}</p>
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
          <p className="mt-1 max-w-3xl text-xs leading-relaxed text-slate-500">
            This is the internal gate map. A source change becomes a customer artifact only after every required gate passes.
          </p>
        </div>
        <StatusPill tone="slate">Delivery blocked by default</StatusPill>
      </div>

      <div className="sp-evidence-chain">
        {steps.map(([title, detail, state]) => (
          <div key={title} className={`sp-evidence-step ${state === 'blocked' ? 'is-blocked' : ''}`}>
            <div className="mb-2 flex items-center justify-between gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${
                state === 'done' ? 'bg-emerald-300' : state === 'review' ? 'bg-amber-300' : 'bg-slate-500'
              }`} />
              <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{state}</span>
            </div>
            <p className="text-xs font-semibold text-white">{title}</p>
            <p className="mt-1 text-[11px] leading-relaxed text-slate-500">{detail}</p>
          </div>
        ))}
      </div>
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
      .catch(() => { if (active) setTelegramStatus(null) })
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
      detail: 'Candidate and remediation rows stay outside fresh-alert claims.',
      tone: ((sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0)) > 0 ? 'amber' : 'emerald',
      action: 'sources',
    },
    {
      label: 'Brief delivery',
      value: 'Blocked',
      detail: 'Customer delivery remains off until evidence and human-review gates pass.',
      tone: 'slate',
      action: 'briefs',
    },
  ]

  return (
    <div className="min-h-full space-y-5 bg-[#07111F] p-5 pb-10">
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
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">
              Review what changed and what needs a decision before relying on any alert,
              brief draft, or source claim. Monitoring intelligence only — not legal advice.
            </p>

            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {attentionItems.map(item => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => navigate(item.action)}
                  className="group rounded-2xl border border-slate-800 bg-slate-950/45 p-4 text-left transition hover:-translate-y-0.5 hover:border-cyan-400/35 hover:bg-slate-900/70"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{item.label}</p>
                    <StatusPill tone={item.tone}>{item.tone === 'emerald' ? 'OK' : item.tone === 'amber' ? 'Review' : 'Gated'}</StatusPill>
                  </div>
                  <p className={`text-3xl font-semibold text-white ${typeof item.value === 'number' ? 'sp-mono' : ''}`}>{item.value}</p>
                  <p className="mt-2 min-h-[2.4rem] text-xs leading-relaxed text-slate-500">{item.detail}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-cyan-200">
                    Open <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/45 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recommended next step</p>
            <h2 className="mt-2 text-lg font-semibold text-white">Review source-health flags before brief work.</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Failed and quality-drop runs should be cleared or documented before source scope
              is presented to anyone outside the workspace.
            </p>
            <button
              type="button"
              onClick={() => navigate('sources')}
              className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-[#16D9F5] px-4 py-2.5 text-sm font-semibold text-[#07111F] transition hover:bg-[#11c2db]"
            >
              Review source health <ArrowRight className="h-4 w-4" />
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

      <EvidenceChainPanel />

      <ProfileSummaryCard profile={profile} currentUser={currentUser} navigate={navigate} planState={planState} />

      {sourcesError && (
        <ErrorState
          title="Could not load source status."
          detail={sourcesError}
          onRetry={retrySources}
          className="rounded-xl border border-slate-800 bg-[#0D1B2E]"
        />
      )}

      <PressureScore />

      {/* Real source table — from /api/sources/status */}
      {!sourcesLoading && !sourcesError && sourcesData?.sources?.length > 0 && (
        <div className="sp-panel p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Source status</h2>
              <p className="mt-1 text-xs text-slate-500">Current monitoring status and extraction readiness for all active UAE sources.</p>
            </div>
            <span title="Rows come directly from the monitoring API for this workspace — no sample data." className="rounded-md border border-slate-700 bg-slate-800/60 px-2.5 py-1 text-[10px] font-semibold text-slate-300">Live data</span>
          </div>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="sp-table min-w-[860px]">
              <thead>
                <tr>
                  {['Source', 'Regulator', 'Last checked', 'Readiness', 'Extraction quality', 'Evidence', 'Action'].map(h => (
                    <th key={h} className="whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {sourcesData.sources.slice(0, 12).map(s => (
                  <tr key={s.source_id} className="transition-colors hover:bg-slate-800/40">
                    <td className="font-medium text-white max-w-[260px] truncate">{s.name}</td>
                    <td className="text-slate-400 whitespace-nowrap">{s.category?.replace(/_/g, ' ') || '—'}</td>
                    <td className="text-slate-500 whitespace-nowrap">
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
                        className="text-[#16D9F5] hover:underline text-xs font-semibold"
                      >
                        View source
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-slate-600">
            {sourcesData.disclaimer || 'Not legal advice. For monitoring information only.'}
          </p>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-white">Review queue</h2>
                <p className="mt-1 text-xs text-slate-500">
                  Customer alerts appear only after monitored evidence is reviewed and routed.
                </p>
              </div>
              <StatusPill tone="cyan">Live workspace</StatusPill>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950/35 px-5 py-8 text-center">
              <p className="mb-1 text-sm text-slate-300">No reviewed customer alerts are ready for this workspace yet.</p>
              <p className="text-xs text-slate-600">
                Reviewed alerts appear after evidence records pass human review and delivery routing. No sample alerts are shown in the authenticated dashboard.
              </p>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-white">Brief delivery readiness</h2>
                <StatusPill tone="cyan">Test mode</StatusPill>
              </div>
              <div className="space-y-4 text-xs">
                <p className="leading-relaxed text-slate-300">
                  Reviewed weekly briefs can be rendered into Markdown/HTML and written to local email test-mode outbox.
                  External email delivery is not enabled automatically.
                </p>
                <button onClick={() => navigate('integrations')} className="w-full rounded-lg border border-cyan-400/25 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50">
                  Open delivery settings
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
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
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                Coverage indicators are source-readiness signals, not a statement of complete market coverage.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <WorkspaceChecklist profile={profile} telegramStatus={telegramStatus} telegramLoading={telegramLoading} navigate={navigate} />
          <SourceReadinessCard navigate={navigate} />
          <DeadlinesPanel />

          <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
            <div className="mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-300" />
              <h2 className="text-sm font-semibold text-white">Delivery status</h2>
            </div>
            <p className="text-sm leading-relaxed text-slate-400">
              Manual reviewed-alert preview delivery is available from Alerts when Telegram is connected. Automatic scheduled delivery is not enabled yet.
            </p>
            <button
              onClick={() => navigate('sources')}
              className="mt-4 w-full rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
            >
              Start with source readiness
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

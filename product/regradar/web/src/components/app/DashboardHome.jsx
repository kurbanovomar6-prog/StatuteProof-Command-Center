import { useEffect, useState } from 'react'
import { ArrowRight, Bell, CheckCircle, Clock, FileText, Globe, Link2, ShieldCheck, AlertTriangle } from 'lucide-react'

import { telegramPair, sources as sourcesApi } from '../../api'
import PlanBanner from './PlanBanner'
import { getWorkspaceProfile, profileLabel } from '../../data/workspaceProfile'
import DeadlinesPanel from './DeadlinesPanel'
import PressureScore from './PressureScore'

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

function InfoCard({ icon: Icon, tone, label, value, sub, isSourcesMonitored }) {
  const iconStyle = {
    cyan: 'bg-cyan-500/10 text-cyan-300',
    emerald: 'bg-emerald-500/10 text-emerald-300',
    amber: 'bg-amber-500/10 text-amber-300',
    slate: 'bg-slate-800 text-slate-400',
  }[tone] || 'bg-slate-800 text-slate-400'

  return (
    <div className="sp-glass p-4">
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
          {isSourcesMonitored && <span className="sp-live-dot" />}
        </div>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconStyle}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="sp-animate-stat text-2xl font-bold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
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
    { label: 'Source map reviewed', detail: 'Review fresh-alert eligible, limited, and access-restricted sources', status: 'Needs review', tone: 'amber', action: 'sources' },
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

      <div className="mb-4 grid grid-cols-2 gap-2">
        <StatusPill tone="emerald">Evidence confirmed</StatusPill>
        <StatusPill tone="amber">Baseline pending</StatusPill>
        <StatusPill tone="cyan">Needs adapter</StatusPill>
        <StatusPill tone="slate">Limited</StatusPill>
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
  const mostRecentRunAt = sources
    .map(s => s.last_run_at)
    .filter(Boolean)
    .sort()
    .pop()
  const lastCheck = mostRecentRunAt
    ? new Date(mostRecentRunAt).toLocaleString('en-GB', { timeZone: 'UTC', dateStyle: 'short', timeStyle: 'short' }) + ' UTC'
    : 'No runs yet'
  return {
    enabledSources: sourceSummary?.enabled_count ?? sources.length,
    supportedSources: sourceSummary?.readiness_supported_count ?? 0,
    remediationSources: sourceSummary?.remediation_count ?? 0,
    lastCheck,
    changedThisWeek: changed + firstSeen,
    highRiskPending,
    failedSources: failed + qualityDrop,
    evidenceRecords: sources.filter(s => s.change_status !== 'NOT_RUN').length,
    briefStatus: 'Test mode available',
    reviewRequired: highRiskPending,
  }
}

const EXTRACTION_CLS = {
  GOOD:    'text-emerald-400',
  OK:      'text-amber-400',
  POOR:    'text-red-400',
  UNKNOWN: 'text-slate-500',
}

function ReadinessBadge({ source }) {
  let label = 'ACTIVATION PENDING'
  let cls = 'border-slate-600/40 bg-slate-800/60 text-slate-300'
  if (REMEDIATION_SOURCE_IDS.has(source.source_id)) {
    label = 'NEEDS REVIEW'
    cls = 'border-amber-400/30 bg-amber-400/10 text-amber-200'
  } else if (source.change_status === 'FAILED' || source.access_status === 'failed') {
    label = 'BLOCKED'
    cls = 'border-rose-400/30 bg-rose-400/10 text-rose-200'
  } else if (source.change_status === 'QUALITY_DROP') {
    label = 'QUALITY DROP'
    cls = 'border-amber-400/30 bg-amber-400/10 text-amber-200'
  } else if (source.change_status && source.change_status !== 'NOT_RUN') {
    label = 'READINESS'
    cls = 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
  }
  return <span className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-bold ${cls}`}>{label}</span>
}

function EvidenceBadge({ source }) {
  const hasEvidence = source.change_status && source.change_status !== 'NOT_RUN'
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-bold ${
      hasEvidence
        ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200'
        : 'border-slate-600/40 bg-slate-800/60 text-slate-400'
    }`}>
      {hasEvidence ? 'PROOF RECORDED' : 'PENDING RUN'}
    </span>
  )
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

  useEffect(() => {
    let active = true
    Promise.all([sourcesApi.status('AE'), sourcesApi.summary('AE')])
      .then(([statusData, summaryData]) => {
        if (!active) return
        setSourcesData(statusData)
        setSourceSummary(summaryData)
      })
      .catch(err => { if (active) setSourcesError(err.message || 'Could not load source status.') })
      .finally(() => { if (active) setSourcesLoading(false) })
    return () => { active = false }
  }, [])

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
            <div className="mb-3 flex flex-wrap gap-2">
              <StatusPill tone="amber">Operator command center</StatusPill>
              <StatusPill tone="cyan">Evidence-readiness review</StatusPill>
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <h1 className="sp-heading max-w-4xl text-2xl font-semibold leading-tight text-white md:text-3xl">
                {sourcesError
                  ? 'Source readiness summary is unavailable right now.'
                  : sourcesLoading
                  ? 'Loading UAE source readiness summary...'
                  : `${sourceSummary?.fresh_alert_count ?? sourceSummary?.readiness_supported_count ?? 0} fresh-alert eligible sources, ${((sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0)) || 0} scope limitations to keep visible.`}
              </h1>
              {!sourcesLoading && !sourcesError && (
                <span className="sp-badge-trust">Monitoring active</span>
              )}
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">
              Use this screen to decide what needs operator review before relying on any alert,
              brief draft, or source claim. This is monitoring intelligence only, not legal advice.
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
                  <p className="sp-mono text-3xl font-semibold text-white">{item.value}</p>
                  <p className="mt-2 min-h-[2.4rem] text-xs leading-relaxed text-slate-500">{item.detail}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-cyan-200">
                    Open <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="sp-action-lane p-5">
            <p className="text-xs font-bold uppercase tracking-wide text-amber-200">Next safest action</p>
            <h2 className="mt-2 text-xl font-semibold text-white">Review source-health flags before any brief work.</h2>
            <p className="mt-2 text-sm leading-relaxed text-amber-50/80">
              Failed and quality-drop source runs are operator risks. Clear or document them before presenting source scope to a pilot buyer.
            </p>
            <button
              type="button"
              onClick={() => navigate('sources')}
              className="mt-5 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-amber-200 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-amber-100"
            >
              Review source health <ArrowRight className="h-4 w-4" />
            </button>
            <div className="mt-4 grid grid-cols-3 gap-2">
              <CommandMetric label="Enabled" value={sourceSummary?.enabled_count ?? '—'} detail="source records" />
              <CommandMetric label="Fresh-alert" value={sourceSummary?.readiness_supported_count ?? '—'} tone="emerald" detail="eligible" />
              <CommandMetric label="Limited" value={(sourceSummary?.candidate_count ?? 0) + (sourceSummary?.remediation_count ?? 0) || '—'} tone="amber" detail="not claimed" />
            </div>
          </div>
        </div>
      </div>

      <EvidenceChainPanel />

      <ProfileSummaryCard profile={profile} currentUser={currentUser} navigate={navigate} planState={planState} />

      {/* 8-widget row — real data from /api/sources/status */}
      {sourcesLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="sp-skeleton h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : sourcesError ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 px-5 py-4 flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <p className="text-sm text-rose-300">Could not load source status. Start the API server and refresh.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <InfoCard icon={Globe}     tone="cyan"    label="Sources enabled"      value={widgets?.enabledSources ?? 0}  sub="reviewed UAE source pack" isSourcesMonitored={true} />
          <InfoCard icon={CheckCircle} tone="emerald" label="Readiness-supported" value={widgets?.supportedSources ?? 0} sub="current registry review" />
          <InfoCard icon={AlertTriangle} tone="amber" label="Need remediation"  value={widgets?.remediationSources ?? 0} sub="UAE Legislation, FIU homepage, SCA listing" />
          <InfoCard icon={FileText}  tone="cyan"    label="Evidence records"     value={widgets?.evidenceRecords ?? 0} sub="runs with proof data" />
          <InfoCard icon={Bell}      tone="emerald" label="Changed sources"      value={widgets?.changedThisWeek ?? 0} sub="CHANGED + FIRST SEEN" />
          <InfoCard icon={AlertTriangle} tone="amber" label="High-risk pending"  value={widgets?.highRiskPending ?? 0} sub="changes needing review" />
          <InfoCard icon={ShieldCheck} tone={widgets?.failedSources > 0 ? 'amber' : 'emerald'} label="Failed / quality drop" value={widgets?.failedSources ?? 0} sub="source health flags" />
          <InfoCard icon={Link2}     tone={telegramStatus?.connected ? 'emerald' : 'amber'} label="Plan state" value={displayPlanName(planState)} sub={telegramStatus?.connected ? 'Telegram connected' : 'choose plan or connect delivery'} />
        </div>
      )}

      <PressureScore />

      {/* Real source table — from /api/sources/status */}
      {!sourcesLoading && !sourcesError && sourcesData?.sources?.length > 0 && (
        <div className="sp-panel p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Source status</h2>
              <p className="mt-1 text-xs text-slate-500">Live data from /api/sources/status, shown with readiness-safe labels.</p>
            </div>
            <span className="rounded-md border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold text-emerald-300">LIVE API</span>
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
                      {s.last_run_at
                        ? new Date(s.last_run_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
                        : 'Not run'}
                    </td>
                    <td className="whitespace-nowrap">
                      <ReadinessBadge source={s} />
                    </td>
                    <td className={`whitespace-nowrap font-medium ${EXTRACTION_CLS[s.extraction_quality] || EXTRACTION_CLS.UNKNOWN}`}>
                      {s.extraction_quality || 'UNKNOWN'}
                    </td>
                    <td className="whitespace-nowrap">
                      <EvidenceBadge source={s} />
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

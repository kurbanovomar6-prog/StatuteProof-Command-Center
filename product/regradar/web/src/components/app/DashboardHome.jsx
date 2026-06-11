import { useEffect, useState } from 'react'
import { Bell, CheckCircle, Clock, FileText, Globe, Link2, ShieldCheck } from 'lucide-react'

import { telegramPair } from '../../api'
import { MOCK_ALERTS, COVERAGE_MARKETS } from '../../data/appMockData'
import { getWorkspaceProfile, profileLabel, filterAlerts, filterCoverage } from '../../data/workspaceProfile'

const RISK_DARK = {
  HIGH:   'text-red-400 bg-red-500/15 border border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border border-amber-500/30',
  LOW:    'text-emerald-400 bg-emerald-500/15 border border-emerald-500/30',
  MIXED:  'text-blue-400 bg-blue-500/15 border border-blue-500/30',
}

const COV_COLOR = {
  emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  amber:   'text-amber-400 bg-amber-500/10 border-amber-500/20',
  slate:   'text-slate-400 bg-slate-500/10 border-slate-500/20',
}

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

function InfoCard({ icon: Icon, tone, label, value, sub }) {
  const iconStyle = {
    cyan: 'bg-cyan-500/10 text-cyan-300',
    emerald: 'bg-emerald-500/10 text-emerald-300',
    amber: 'bg-amber-500/10 text-amber-300',
    slate: 'bg-slate-800 text-slate-400',
  }[tone] || 'bg-slate-800 text-slate-400'

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
      <div className="mb-3 flex items-start justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconStyle}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  )
}

function RiskBadge({ risk }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${RISK_DARK[risk] || RISK_DARK.LOW}`}>
      {risk}
    </span>
  )
}

function ProfileSummaryCard({ profile, currentUser, navigate }) {
  const hasProfile = profile.markets.length > 0 || profile.industries.length > 0 || profile.topics.length > 0
  const company = profile.company || currentUser?.company_name || 'Profile workspace'

  return (
    <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="mb-2 flex flex-wrap gap-2">
            <StatusPill tone="cyan">Founding pilot</StatusPill>
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
    { label: 'Source map reviewed', detail: 'Review validated, under-validation and limited sources', status: 'Needs review', tone: 'amber', action: 'sources' },
    { label: 'First reviewed brief', detail: 'Sample brief delivery can be tested from Integrations', status: 'Sample available', tone: 'slate', action: 'briefs' },
  ]

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
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
    <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Source readiness</h2>
          <p className="mt-1 text-xs text-slate-500">Mapped does not mean active.</p>
        </div>
        <StatusPill tone="cyan">35+ source layers mapped</StatusPill>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2">
        <StatusPill tone="emerald">Validated</StatusPill>
        <StatusPill tone="amber">Under validation</StatusPill>
        <StatusPill tone="cyan">Needs adapter</StatusPill>
        <StatusPill tone="slate">Limited</StatusPill>
      </div>

      <div className="space-y-2.5 text-sm text-slate-400">
        {[
          'Validated sources only enter monitoring profiles.',
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
    </div>
  )
}

export default function DashboardHome({ navigate, currentUser }) {
  const profile = getWorkspaceProfile()
  const hasProfile = profile.markets.length > 0
  const alerts = filterAlerts(MOCK_ALERTS, profile)
  const coverage = filterCoverage(COVERAGE_MARKETS, profile)
  const selectedBrief = alerts[0] || null

  const [telegramStatus, setTelegramStatus] = useState(null)
  const [telegramLoading, setTelegramLoading] = useState(true)

  useEffect(() => {
    let active = true
    telegramPair.status()
      .then(data => { if (active) setTelegramStatus(data) })
      .catch(() => { if (active) setTelegramStatus(null) })
      .finally(() => { if (active) setTelegramLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <div className="min-h-full space-y-5 bg-[#07111F] p-5">
      <ProfileSummaryCard profile={profile} currentUser={currentUser} navigate={navigate} />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <InfoCard icon={Globe} tone="cyan" label="Markets in profile" value={hasProfile ? profile.markets.length : '—'} sub={hasProfile ? 'selected by workspace' : 'setup pending'} />
        <InfoCard icon={ShieldCheck} tone="emerald" label="Source activation" value="Gated" sub="validation required before monitoring" />
        <InfoCard icon={Link2} tone={telegramStatus?.connected ? 'emerald' : 'amber'} label="Telegram" value={telegramStatus?.connected ? 'Connected' : 'Not connected'} sub={telegramStatus?.connected ? 'test delivery available' : 'connect in Integrations'} />
        <InfoCard icon={FileText} tone="cyan" label="Brief delivery" value="Manual" sub="sample and reviewed-alert previews available" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
        <div className="space-y-5">
          <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-white">Sample signal preview</h2>
                <p className="mt-1 text-xs text-slate-500">
                  Sample briefs show the review format. They are not live customer alerts.
                </p>
              </div>
              <StatusPill tone="slate">Sample preview</StatusPill>
            </div>

            {alerts.length > 0 ? (
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-800/60">
                      {['Risk', 'Market', 'Source', 'Title', 'Affected', 'Status'].map(h => (
                        <th key={h} className="px-4 py-2.5 text-left font-medium text-slate-400 whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {alerts.slice(0, 5).map(a => (
                      <tr key={a.id} className="transition-colors hover:bg-slate-800/40">
                        <td className="px-4 py-3 whitespace-nowrap"><RiskBadge risk={a.risk} /></td>
                        <td className="px-4 py-3 whitespace-nowrap text-slate-300">{a.flag} {a.market}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-slate-400">{a.source}</td>
                        <td className="max-w-[240px] truncate px-4 py-3 text-slate-200">{a.title}</td>
                        <td className="max-w-[160px] truncate px-4 py-3 text-slate-400">{a.affected.slice(0, 2).join(', ')}</td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <StatusPill tone={a.status === 'Review required' ? 'amber' : 'slate'}>{a.status}</StatusPill>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="rounded-lg border border-slate-800 bg-slate-950/35 px-5 py-8 text-center">
                <p className="mb-1 text-sm text-slate-400">No sample items match your selected profile.</p>
                <p className="text-xs text-slate-600">Add more markets or industries in Settings.</p>
              </div>
            )}
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-white">Sample brief preview</h2>
                {selectedBrief && <RiskBadge risk={selectedBrief.risk} />}
              </div>
              {selectedBrief ? (
                <div className="space-y-4 text-xs">
                  <div>
                    <p className="mb-1.5 text-slate-500">Executive summary</p>
                    <p className="leading-relaxed text-slate-300">{selectedBrief.summary}</p>
                  </div>
                  <div>
                    <p className="mb-1.5 text-slate-500">Source proof direction</p>
                    <p className="leading-relaxed text-slate-300">
                      Briefs include official source, extraction quality, limitations and review status before delivery.
                    </p>
                  </div>
                  <button onClick={() => navigate('briefs')} className="w-full rounded-lg border border-cyan-400/25 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50">
                    Open brief workspace
                  </button>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Save a broader profile to view a matching sample brief.</p>
              )}
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
              <h2 className="mb-4 text-sm font-semibold text-white">Profile source coverage</h2>
              {coverage.length > 0 ? (
                <div className="grid grid-cols-4 gap-2">
                  {coverage.slice(0, 8).map(m => (
                    <div key={m.code} className={`flex flex-col items-center rounded-lg border p-2 ${COV_COLOR[m.color]}`}>
                      <span className="mb-1 text-base">{m.flag}</span>
                      <span className="text-xs font-bold">{m.code}</span>
                      <span className="mt-0.5 text-xs opacity-70">{m.score}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No source map selected yet.</p>
              )}
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                Coverage indicators are source-readiness signals, not a statement of complete market coverage.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <WorkspaceChecklist profile={profile} telegramStatus={telegramStatus} telegramLoading={telegramLoading} navigate={navigate} />
          <SourceReadinessCard navigate={navigate} />

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

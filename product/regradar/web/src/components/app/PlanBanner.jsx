import { AlertTriangle, Clock, ArrowRight, CheckCircle } from 'lucide-react'

export default function PlanBanner({ planState, onChoosePlan, onComparePlans }) {
  if (!planState) return null

  const { plan_name, plan_display, trial_expired, days_remaining, status } = planState
  const displayName = plan_name === 'evidence_preview' ? 'Source Readiness Review' : plan_display

  if (plan_name === 'evidence_preview') {
    const urgent = days_remaining !== null && days_remaining <= 2

    return (
      <div className={`rounded-xl border p-4 mb-5 ${
        urgent
          ? 'border-amber-500/40 bg-amber-500/5'
          : 'border-[#16D9F5]/20 bg-[#16D9F5]/5'
      }`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
              urgent ? 'bg-amber-500/20 text-amber-400' : 'bg-[#16D9F5]/10 text-[#16D9F5]'
            }`}>
              {urgent ? <AlertTriangle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="text-sm font-semibold text-white">
                  {trial_expired ? 'Source Readiness Review access ended' : 'Source Readiness Review enabled'}
                </span>
                {days_remaining !== null && !trial_expired && (
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                    urgent
                      ? 'border-amber-400/30 bg-amber-400/10 text-amber-300'
                      : 'border-[#16D9F5]/30 bg-[#16D9F5]/10 text-[#16D9F5]'
                  }`}>
                    {days_remaining} {days_remaining === 1 ? 'day' : 'days'} remaining
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed max-w-xl">
                {trial_expired
                  ? 'Your source readiness review access has ended. Choose a plan to start monitored sources and evidence records.'
                  : 'Explore the workspace with sample evidence and source-readiness tools. Choose a plan to unlock monitored sources, weekly briefs, and custom source activation.'}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={onChoosePlan}
              className="sp-btn-primary text-xs py-1.5 px-3 inline-flex items-center gap-1.5"
            >
              Choose plan <ArrowRight className="w-3.5 h-3.5" />
            </button>
            {onComparePlans && (
              <button
                onClick={onComparePlans}
                className="sp-btn-secondary text-xs py-1.5 px-3"
              >
                Compare plans
              </button>
            )}
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Current plan', value: displayName || 'Source Readiness Review' },
            { label: 'Live monitoring', value: 'Not included', muted: true },
            { label: 'Recommended', value: 'UAE Monitor' },
            { label: 'Next step', value: 'Choose your source pack' },
          ].map(({ label, value, muted }) => (
            <div key={label}>
              <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500 mb-0.5">{label}</p>
              <p className={`text-xs font-medium ${muted ? 'text-slate-500' : 'text-slate-200'}`}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Paid / Founding Pilot plan
  const caps = planState.capabilities || {}
  const sourceLimit = caps.sourceLimit ?? caps.source_limit
  const users = caps.users
  const retentionDays = caps.retentionDays ?? caps.retention_days
  return (
    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 mb-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center bg-emerald-500/20 text-emerald-400">
            <CheckCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-sm font-semibold text-white">{displayName} workspace</span>
              <span className="text-xs font-medium px-2 py-0.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
                {status === 'active' ? 'Plan enabled' : 'Pending activation'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Your source pack is staged for validation. Live monitoring starts after source readiness confirmation.
            </p>
            {status !== 'active' && (
              <p className="text-xs text-amber-400 mt-1">
                Plan state shown for pilot preview. Billing is manually activated — no payment has been processed.
              </p>
            )}
          </div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Current plan', value: displayName },
          { label: 'Source limit', value: sourceLimit > 100 ? 'Custom' : String(sourceLimit || '—') },
          { label: 'Users', value: users > 100 ? 'Custom' : String(users || 1) },
          { label: 'Evidence retention', value: retentionDays > 500 ? 'Custom' : retentionDays ? `${retentionDays} days` : '—' },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500 mb-0.5">{label}</p>
            <p className="text-xs font-medium text-slate-200">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

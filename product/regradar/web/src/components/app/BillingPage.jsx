import { ArrowRight, ShieldCheck } from 'lucide-react'
import { PLAN_CAPABILITIES } from '../../data/planCapabilities'

function Row({ label, value, highlight }) {
  return (
    <div className={`flex items-center justify-between py-2.5 border-b border-slate-800/60 last:border-0 ${highlight ? 'text-[#16D9F5]' : ''}`}>
      <span className="text-xs text-slate-400">{label}</span>
      <span className={`text-xs font-medium ${highlight ? 'text-[#16D9F5]' : 'text-slate-200'}`}>{value}</span>
    </div>
  )
}

const PLAN_DISPLAY = {
  evidence_preview: 'Source Readiness Review',
  starter_pilot: 'Founding Pilot',
  professional: 'UAE Monitor',
  consultant: 'Compliance Consultant',
}

export default function BillingPage({ planState }) {
  const status = planState?.status || 'evidence_preview'
  const activationPending = status === 'pending_manual_activation'
  const selectedPlan = planState?.plan_name || 'evidence_preview'
  const activePlan = activationPending ? (planState?.active_plan_name || 'evidence_preview') : selectedPlan
  const requestedPlan = activationPending ? (planState?.requested_plan || selectedPlan) : null
  const display = PLAN_DISPLAY[activePlan] || activePlan
  const requestedDisplay = requestedPlan ? (PLAN_DISPLAY[requestedPlan] || requestedPlan) : ''
  const caps = PLAN_CAPABILITIES[activePlan] || PLAN_CAPABILITIES.evidence_preview
  const statusLabel = status === 'active'
    ? 'Plan enabled'
    : status === 'trial_active'
      ? 'Review enabled'
      : activationPending
        ? 'Pending manual activation'
        : 'Pending'
  const currentStatusLabel = status === 'active'
    ? 'Plan enabled'
    : status === 'trial_active'
      ? 'Source Readiness Review enabled'
      : activationPending
        ? 'Plan intent saved; manual activation required'
        : 'Pending activation'

  return (
    <div className="mx-auto max-w-4xl space-y-5 p-6">
      <div>
        <div className="sp-kicker mb-3">Manual activation</div>
        <h1 className="text-2xl font-semibold text-white mb-1">Plan & Billing</h1>
        <p className="max-w-2xl text-sm text-slate-400">
          Founding pilots are manually activated after source readiness review. No payment method is stored,
          and Stripe self-serve checkout is not enabled for the first pilot cohort.
        </p>
      </div>

      {/* Current plan */}
      <div className="sp-panel p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1">Current Plan</p>
            <h2 className="text-lg font-bold text-white">{display}</h2>
          </div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            status === 'active'
              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300'
              : status === 'trial_active'
              ? 'border-[#16D9F5]/30 bg-[#16D9F5]/10 text-[#16D9F5]'
              : 'border-amber-400/30 bg-amber-400/10 text-amber-300'
          }`}>
            {statusLabel}
          </span>
        </div>

        <Row label="Current status" value={currentStatusLabel} highlight />
        {activationPending ? (
          <Row label="Requested plan" value={`${requestedDisplay} — pending manual activation`} />
        ) : null}
        <Row label="Live monitoring" value={caps.liveMonitoring ? 'Included after activation' : 'Not included'} />
        <Row label="Source limit" value={caps.sourceLimit > 100 ? 'Custom' : caps.sourceLimit === 0 ? 'Sample only' : String(caps.sourceLimit)} />
        <Row label="Custom source limit" value={caps.customSources > 100 ? 'Custom' : caps.customSources === 0 ? 'Not included' : `${caps.customSources} after review`} />
        <Row label="Weekly MLRO brief" value={caps.weeklyBriefs === true ? 'Included after delivery setup' : caps.weeklyBriefs === 'status_only' ? 'Source status summary' : 'Not included'} />
        <Row label="Audit binder export" value={caps.auditExport ? 'PDF audit pack + Markdown/HTML included' : 'Pilot roadmap'} />
        <Row label="PDF export" value={caps.pdfExport ? 'PDF audit pack included for saved evidence records' : 'Not enabled yet'} />
        <Row label="Users" value={caps.users > 100 ? 'Custom' : String(caps.users)} />
        <Row label="Evidence retention" value={caps.retentionDays > 500 ? 'Custom' : caps.retentionDays === 0 ? 'Sample only' : `${caps.retentionDays} days`} />
        <Row label="Multiple workspaces" value={caps.multipleWorkspaces ? 'Included' : 'Pilot roadmap'} />
      </div>

      {/* Billing note */}
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-slate-200 mb-1">Billing is manually activated</p>
            <p className="text-xs text-slate-400">
              No payment method is stored. During the founding pilot, billing is activated manually after source readiness review.
              Stripe billing can be connected later. You will receive advance notice before any charges.
            </p>
          </div>
        </div>
      </div>

      {/* Upgrade CTA */}
      {(selectedPlan === 'evidence_preview' || selectedPlan === 'starter_pilot') ? (
        <div className="bg-[#16D9F5]/5 border border-[#16D9F5]/20 rounded-xl p-4">
          <p className="text-sm font-semibold text-white mb-1">Upgrade to UAE Monitor</p>
          <p className="text-xs text-slate-400 mb-3">
            79 enabled UAE sources: 78 readiness-supported after proof and baseline gates, 1 under extraction remediation.
            Includes high-risk review queue, weekly MLRO brief after setup, and 180-day evidence retention.
          </p>
          <div className="flex gap-2">
            <a
              href="mailto:hello@statuteproof.com?subject=UAE%20Monitor%20Plan%20Enquiry"
              className="sp-btn-primary text-xs py-1.5 px-3 inline-flex items-center gap-1.5"
            >
              Request upgrade <ArrowRight className="w-3.5 h-3.5" />
            </a>
            <a
              href="mailto:hello@statuteproof.com?subject=Consultant%20Plan%20Enquiry"
              className="sp-btn-secondary text-xs py-1.5 px-3"
            >
              Talk to us (Consultant)
            </a>
          </div>
        </div>
      ) : null}

      <p className="text-xs text-slate-600 mt-5 text-center">
        Not legal advice. For monitoring information only. StatuteProof does not determine compliance outcomes or prevent fines.
      </p>
    </div>
  )
}

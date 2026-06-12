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
  evidence_preview: 'Evidence Preview',
  starter_pilot: 'Starter Pilot',
  professional: 'Professional',
  consultant: 'Compliance Consultant',
}

export default function BillingPage({ planState }) {
  const plan = planState?.plan_name || 'evidence_preview'
  const display = PLAN_DISPLAY[plan] || plan
  const caps = PLAN_CAPABILITIES[plan] || PLAN_CAPABILITIES.evidence_preview
  const status = planState?.status || 'evidence_preview'

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-1">Plan & Billing</h1>
      <p className="text-sm text-slate-400 mb-6">
        Founding pilots are manually activated after source readiness review. No payment method is stored.
      </p>

      {/* Current plan */}
      <div className="sp-card mb-5">
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
            {status === 'active' ? 'Active' : status === 'trial_active' ? 'Trial active' : 'Pending'}
          </span>
        </div>

        <Row label="Live monitoring" value={caps.liveMonitoring ? 'Included' : 'Not included'} />
        <Row label="Source limit" value={caps.sourceLimit > 100 ? 'Custom' : caps.sourceLimit === 0 ? 'Sample only' : String(caps.sourceLimit)} />
        <Row label="Custom sources" value={caps.customSources > 100 ? 'Custom' : caps.customSources === 0 ? 'Not included' : String(caps.customSources)} />
        <Row label="Weekly MLRO brief" value={caps.weeklyBriefs === true ? 'Included' : caps.weeklyBriefs === 'limited' ? 'Limited' : 'Not included'} />
        <Row label="Audit binder export" value={caps.auditExport ? 'Included' : 'Not included'} />
        <Row label="PDF export" value={caps.pdfExport ? 'Included' : 'Not included'} />
        <Row label="Users" value={caps.users > 100 ? 'Custom' : String(caps.users)} />
        <Row label="Evidence retention" value={caps.retentionDays > 500 ? 'Custom' : caps.retentionDays === 0 ? 'Sample only' : `${caps.retentionDays} days`} />
        <Row label="Multiple workspaces" value={caps.multipleWorkspaces ? 'Included' : 'Not included'} />
      </div>

      {/* Billing note */}
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 mb-5">
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
      {(plan === 'evidence_preview' || plan === 'starter_pilot') ? (
        <div className="bg-[#16D9F5]/5 border border-[#16D9F5]/20 rounded-xl p-4">
          <p className="text-sm font-semibold text-white mb-1">Upgrade to Professional</p>
          <p className="text-xs text-slate-400 mb-3">
            13–16 official UAE sources, weekly MLRO brief, audit binder export, 12-month evidence retention.
          </p>
          <div className="flex gap-2">
            <a
              href="mailto:hello@statuteproof.com?subject=Professional%20Plan%20Enquiry"
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
        Not legal advice. For monitoring information only. StatuteProof does not guarantee compliance or prevent fines.
      </p>
    </div>
  )
}

import { CheckCircle } from 'lucide-react'
import { pricingPlans } from '../data/mockData'
import {
  CONTACT_EMAIL,
  STRIPE_LINK_FOUNDING_PILOT,
  STRIPE_LINK_UAE_MONITOR,
  stripeCheckoutUrl,
} from '../data/constants'

const STRIPE_LINKS = {
  starter_pilot: STRIPE_LINK_FOUNDING_PILOT,
  professional:  STRIPE_LINK_UAE_MONITOR,
}

export default function Pricing({ onCreateWorkspace, onSourceReview, onSelectPlan, currentUser }) {
  function handleCta(plan) {
    if (plan.ctaType === 'source_review') {
      onSourceReview?.()
      return
    }
    if (plan.ctaType === 'consultant') {
      window.location.assign(`mailto:${CONTACT_EMAIL}?subject=Compliance%20Consultant%20Plan`)
      return
    }
    // Paid plans: open Stripe link if configured, otherwise route to registration.
    // A logged-in buyer carries their id as client_reference_id so the webhook
    // resolves them unambiguously; an anonymous buyer gets the plain link and
    // resolves via the verified-email fallback after registering.
    if (plan.routePlan) {
      const stripeLink = STRIPE_LINKS[plan.routePlan]
      if (stripeLink) {
        window.open(stripeCheckoutUrl(stripeLink, currentUser?.id), '_blank', 'noopener,noreferrer')
        return
      }
      onSelectPlan?.(plan.routePlan)
      return
    }
    onCreateWorkspace?.()
  }

  return (
    <section className="py-20 bg-[#07111F]" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10">
          <div className="sp-kicker mb-4">Pricing and activation</div>
          <h2 className="sp-heading text-3xl text-white mb-3">Plans with disclosed limits for source readiness and pilot monitoring</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Founding pilots are manually activated after source readiness review. No payment method
            is stored until billing is formally set up.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
          {pricingPlans.map(plan => (
            <div
              key={plan.name}
              className={`sp-glass p-6 flex flex-col transition-all ${
                plan.highlight
                  ? 'border-cyan-400/40 bg-[#16D9F5]/5 shadow-[0_0_30px_rgba(22,217,245,0.10)]'
                  : ''
              }`}
            >
              <div className="mb-6">
                {plan.highlight && (
                  <span className="sp-badge-trust mb-2">{plan.badge || 'Recommended'}</span>
                )}
                {!plan.highlight && plan.badge && (
                  <div className="mb-2 inline-flex rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] font-semibold text-slate-300">
                    {plan.badge}
                  </div>
                )}
                <h3 className="font-bold text-lg text-white mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-semibold text-white">
                    {plan.price}
                  </span>
                  <span className="text-sm text-slate-400">{plan.period}</span>
                </div>
                {plan.desc && (
                  <p className="text-sm text-slate-400 mt-4 leading-relaxed">{plan.desc}</p>
                )}
              </div>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map(f => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle
                      className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlight ? 'text-[var(--accent)]' : 'text-emerald-400'}`}
                    />
                    <span className="text-slate-300">{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleCta(plan)}
                className={`mt-auto w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  plan.highlight
                    ? 'bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]'
                    : 'border border-slate-700 text-slate-300 hover:border-[var(--accent)]/40 hover:text-white'
                }`}
              >
                {plan.cta}
              </button>
              <p className="text-xs text-slate-500 mt-3">No automatic charges · Cancel anytime · Human review included</p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap justify-center gap-3 mt-8">
          <span className="sp-badge-trust">SHA-256 evidence</span>
          <span className="sp-badge-trust">Official sources only</span>
          <span className="sp-badge-trust">Human review gate</span>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6 max-w-3xl mx-auto leading-relaxed">
          Monitoring scope is limited to selected official UAE regulatory sources across VARA, DFSA, ADGM/FSRA, DIFC and related public authorities.
          Features marked for activation or roadmap are not live by default. Source access, extraction quality, and any limitations are disclosed before pilot begins.
        </p>

      </div>
    </section>
  )
}

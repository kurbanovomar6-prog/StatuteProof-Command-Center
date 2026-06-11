import { CheckCircle } from 'lucide-react'
import { pricingPlans } from '../data/mockData'

export default function Pricing({ onCreateWorkspace }) {
  function handleCta(plan) {
    onCreateWorkspace?.()
  }

  return (
    <section className="py-20 bg-[#07111F]" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-white mb-3">Founding Pilot Terms</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            StatuteProof is in early access. Pricing reflects founding pilot terms — lower than our
            eventual standard rates — in exchange for working closely with the first clients to validate
            source coverage, alert quality, and brief format.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-6">
          {pricingPlans.map(plan => (
            <div
              key={plan.name}
              className={`rounded-xl border p-7 flex flex-col transition-all hover:shadow-lg ${
                plan.highlight
                  ? 'border-[#16D9F5]/40 bg-[#16D9F5]/5 shadow-[0_0_30px_rgba(22,217,245,0.08)]'
                  : 'border-slate-800 bg-[#0D1B2E]'
              }`}
            >
              <div className="mb-6">
                {plan.highlight && (
                  <div className="text-[10px] font-bold text-[#16D9F5] uppercase tracking-widest mb-2">
                    {plan.badge || 'Most popular'}
                  </div>
                )}
                <h3 className="font-bold text-lg text-white mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">
                    {plan.price === 'Free' ? plan.price : `From ${plan.price}`}
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
                      className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlight ? 'text-[#16D9F5]' : 'text-emerald-400'}`}
                    />
                    <span className="text-slate-300">{f}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleCta(plan)}
                className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  plan.highlight
                    ? 'bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]'
                    : 'border border-slate-700 text-slate-300 hover:border-[#16D9F5]/40 hover:text-white'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Founding pilot pricing is available to the first cohort of clients while we complete source
          validation and brief format refinement. Clients who join the founding pilot will receive advance
          notice of any pricing changes.
        </p>

      </div>
    </section>
  )
}

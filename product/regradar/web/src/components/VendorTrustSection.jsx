import { ShieldCheck, Lock, Archive, RadioTower, Mail } from 'lucide-react'

const CARDS = [
  {
    icon: ShieldCheck,
    title: 'UAE-focused compliance monitoring service',
    body: 'StatuteProof is operated by a UAE-based team. The service monitors selected official UAE regulatory sources and delivers evidence-backed monitoring briefs to compliance professionals. It does not provide legal advice, regulatory guidance, or compliance certification.',
  },
  {
    icon: Lock,
    title: 'Evidence records and data handling',
    body: 'Monitoring evidence records — source snapshots, SHA-256 hashes, timestamps, and diffs — are stored securely for the duration of your retention plan. You can export your complete evidence archive at any time in JSON or PDF format. No customer compliance decisions or internal notes are stored unless you log them through the response log feature.',
  },
  {
    icon: Archive,
    title: 'What happens if the service is discontinued',
    body: 'If StatuteProof discontinues its service, you will receive 60 days’ advance notice and a full export of your evidence archive in portable JSON and PDF format. Your monitoring records do not depend on continued service access for their evidentiary value — once exported, SHA-256 hashes and timestamps are self-verifying.',
  },
  {
    icon: RadioTower,
    title: 'Monitoring infrastructure and geo-access',
    body: 'Some UAE official sources apply geo-IP or infrastructure-level access restrictions that can affect automated monitoring. These sources are disclosed before pilot activation rather than monitored unreliably. Where a source is access-restricted, it is flagged as such in the source readiness report and is not counted as fresh-alert eligible coverage.',
  },
]

export default function VendorTrustSection() {
  return (
    <section className="py-20 bg-[#07111F]" id="vendor-trust">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-14">
          <span className="sp-kicker">
            Due diligence answers
          </span>
          <h2 className="text-3xl font-bold text-white mb-3 mt-4">
            Operator &amp; data transparency
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
            Institutional customers ask these questions before onboarding any monitoring tool.
            Here are direct, honest answers — no marketing language.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-5 mb-8">
          {CARDS.map((card) => {
            const Icon = card.icon
            return (
              <div
                key={card.title}
                className="sp-panel p-6 hover:border-cyan-400/25 transition-colors duration-200"
              >
                <div className="w-10 h-10 rounded-lg bg-cyan-400/10 border border-cyan-300/20 flex items-center justify-center mb-4 shrink-0">
                  <Icon className="w-5 h-5 text-cyan-300" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-2 leading-snug">
                  {card.title}
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {card.body}
                </p>
              </div>
            )
          })}
        </div>

        {/* Footer note */}
        <div className="rounded-xl border border-slate-800 bg-[#060E1A] p-6">
          <div className="flex items-start gap-3">
            <Mail className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
            <p className="text-sm leading-relaxed text-slate-400">
              Due diligence questions not answered here? The source readiness review includes a written scope
              disclosure before any pilot activation.{' '}
              <span className="text-slate-300">
                Contact us for data processing agreements, infrastructure documentation, or service level terms.
              </span>
            </p>
          </div>
          <p className="mt-4 text-[11px] text-slate-500 leading-relaxed border-t border-slate-800 pt-4">
            StatuteProof reports are generated from monitored official-source records and are provided for information
            and compliance review support only. StatuteProof does not constitute legal advice, regulatory advice,
            or compliance certification. Not a substitute for qualified legal or compliance professionals.
          </p>
        </div>

      </div>
    </section>
  )
}

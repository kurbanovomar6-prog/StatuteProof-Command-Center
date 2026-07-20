import { Hash, EyeOff, Scale, PlusCircle } from 'lucide-react'

const TRUST_CARDS = [
  {
    icon: Hash,
    objection: 'How do I know you actually captured the update?',
    answer:
      'Every monitoring run stores a cryptographic hash and a timestamped snapshot of what was extracted from the official source. Your compliance team can inspect the hash, the stored snapshot, and the diff record to verify exactly what was captured and when — without relying on our word. The evidence chain additionally supports RFC 3161 timestamp anchoring by a third-party time-stamping authority — when anchoring is enabled, each anchor covers the chain head at the time it is issued, the token is included in your evidence exports, and you can verify it offline on the public Verify page, independently of us.',
    verifyLink: true,
  },
  {
    icon: EyeOff,
    objection: 'What if a source blocks you or becomes inaccessible?',
    answer:
      'Source access status is disclosed before your pilot begins, not after a gap is discovered. Sources that are limited, blocked, or extraction-quality-constrained are documented upfront. Every failed or degraded run is logged and surfaced — it is never silently dropped from your evidence record.',
  },
  {
    icon: Scale,
    objection: 'Is this legal advice?',
    answer:
      'No. StatuteProof delivers monitoring intelligence: what an official source published, when it changed, and a structured brief for your review. Your compliance team or qualified legal counsel determines what the change means for your regulatory obligations and what action, if any, is required.',
  },
  {
    icon: PlusCircle,
    objection: 'What if I need a source you do not currently monitor?',
    answer:
      'Request a source readiness review. We assess accessibility, extraction quality, update frequency, and scope before activating any source. If a source cannot be monitored to the evidence standard required, we document that limitation before activation — not after a gap has already occurred.',
  },
]

export default function TrustLayer({ onVerify }) {
  return (
    <section className="py-20 bg-[#07111F]" id="trust">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-14">
          <span className="sp-kicker">
            Why trust StatuteProof
          </span>
          <h2 className="text-3xl font-bold text-white mb-3 mt-4">
            Questions compliance officers ask before committing
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
            A monitoring tool you cannot verify creates a different kind of risk. Here is how StatuteProof answers the questions that matter before you rely on it.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-5 mb-8">
          {TRUST_CARDS.map((card) => {
            const Icon = card.icon
            return (
              <div
                key={card.objection}
                className="sp-panel p-6 hover:border-cyan-400/25 transition-colors duration-200"
              >
                <div className="w-10 h-10 rounded-lg bg-cyan-400/10 border border-cyan-300/20 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-cyan-300" />
                </div>
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2 leading-snug">
                  {card.objection}
                </p>
                <p className="text-sm text-slate-200 leading-relaxed">
                  {card.answer}
                </p>
                {card.verifyLink ? (
                  <a
                    href="/verify#sample"
                    onClick={(event) => {
                      if (!onVerify) return
                      event.preventDefault()
                      onVerify()
                    }}
                    className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-cyan-300 transition-colors hover:text-white"
                  >
                    Verify a real record yourself — no account
                  </a>
                ) : null}
              </div>
            )
          })}
        </div>

        <div className="bg-[#060E1A] border border-slate-800 rounded-xl p-6">
          <p className="text-[11px] text-slate-400 leading-relaxed text-center max-w-3xl mx-auto">
            StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof does not constitute legal advice, regulatory advice, or compliance certification. Not a substitute for qualified legal or compliance professionals.
          </p>
        </div>

      </div>
    </section>
  )
}

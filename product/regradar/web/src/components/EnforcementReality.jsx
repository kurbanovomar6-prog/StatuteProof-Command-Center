import { AlertTriangle, ExternalLink, Scale, ShieldAlert } from 'lucide-react'

// ─── Block 4 — Why now (enforcement reality) ─────────────────────────────────
//
// These three cards are EXTERNAL regulatory news, not StatuteProof claims,
// predictions, or advice. Every figure is attributed to the public source that
// reported it, with a link the reader can open and verify. We do NOT claim to
// monitor enforcement broadly — that capability is on the roadmap. The only
// StatuteProof tie-in is the one narrow, true statement in the footer: VARA's
// regulatory-notices / enforcement index is among our fresh-alert-eligible
// sources (promoted 2026-07-21, per src/data/sourceQualityAudit.ts).
//
// Framing is deliberately "when did you know, and can you prove it" — never any
// fine-avoidance promise (forbidden, and untrue of a monitoring tool).

const CARDS = [
  {
    Icon: ShieldAlert,
    tag: 'Personal liability',
    accent: 'text-rose-300',
    accentBg: 'bg-rose-400/10 border border-rose-300/20',
    bar: 'bg-rose-400',
    headline: 'A UAE regulator fined the institution — and the individual personally.',
    body:
      'In June 2026 the CBUAE was reported to have imposed a financial penalty on a bank for AML control failures and, separately, a personal financial sanction of around AED 300,000 on the senior individual responsible. The takeaway compliance teams drew was not the amount — it was that accountability reached a named person.',
    source: 'As reported by TaxAdepts',
    href: 'https://taxadepts.com/cbuae-fined-mlro-personal-liability',
  },
  {
    Icon: Scale,
    tag: '“Should have known”',
    accent: 'text-amber-300',
    accentBg: 'bg-amber-400/10 border border-amber-300/20',
    bar: 'bg-amber-400',
    headline: 'The standard shifted from “did you know” to “should you have known”.',
    body:
      'Commentary on Federal Decree-Law No. 10 of 2025 describes a framework where a compliance officer can be held to what they reasonably should have known about a published regulatory change — not only what they were actually told. That makes the gap between a public update and your internal awareness date the thing a review examines.',
    source: 'Per Waystone regulatory update, June 2026',
    href: 'https://compliance.waystone.com/regulatory-update-june-2026-me-region',
  },
  {
    Icon: AlertTriangle,
    tag: 'VARA enforcement',
    accent: 'text-cyan-300',
    accentBg: 'bg-cyan-400/10 border border-cyan-300/20',
    bar: 'bg-[#16D9F5]',
    headline: 'VARA is issuing fines and cease-and-desist notices — publicly.',
    body:
      'The same June 2026 regional update reported a VARA financial penalty against a licensed exchange and cease-and-desist actions against unlicensed operators. These notices are published on VARA’s own site — the record of when they appeared is public, and so is the question of when your firm logged it.',
    source: 'Per Waystone regulatory update, June 2026',
    href: 'https://compliance.waystone.com/regulatory-update-june-2026-me-region',
  },
]

export default function EnforcementReality() {
  return (
    <section className="bg-[#07111F] py-20" id="why-now">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 text-center">
          <div className="sp-kicker inline-flex items-center gap-2 rounded-full border border-rose-300/20 bg-rose-400/10 px-4 py-1.5 text-sm font-medium text-rose-200 mb-4">
            Why compliance teams are acting now — external regulatory news
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            When did you know — and can you prove it?
          </h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            The cards below summarise public UAE enforcement news reported by
            third parties. They are provided so you can read the primary
            coverage yourself. StatuteProof does not predict enforcement, give
            legal advice, or claim to catch every action — it keeps a verifiable
            record of when a monitored change was detected.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {CARDS.map(({ Icon, tag, accent, accentBg, bar, headline, body, source, href }) => (
            <article
              key={tag}
              className="sp-panel relative flex flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#0A1628] p-6 shadow-[0_18px_48px_rgba(0,0,0,0.24)]"
            >
              <div className={`absolute left-0 right-0 top-0 h-[3px] ${bar}`} />
              <div className="mb-4 flex items-center gap-2">
                <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${accentBg}`}>
                  <Icon className={`h-4.5 w-4.5 ${accent}`} />
                </span>
                <span className={`text-xs font-semibold uppercase tracking-wide ${accent}`}>
                  {tag}
                </span>
              </div>
              <h3 className="mb-2 text-base font-semibold leading-snug text-slate-100">
                {headline}
              </h3>
              <p className="flex-1 text-sm leading-relaxed text-slate-400">{body}</p>
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-300 transition-colors hover:text-white"
              >
                {source}
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </article>
          ))}
        </div>

        <div className="mt-10 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] px-8 py-6">
          <p className="mx-auto max-w-3xl text-center text-sm leading-relaxed text-slate-300">
            Where StatuteProof fits: VARA’s regulatory-notices and enforcement
            index is one of our fresh-alert-eligible sources (promoted after two
            stable production runs, 2026-07-18/21). That is selected-source
            monitoring — not complete enforcement coverage. What we give you is a
            sealed, timestamped record of when a monitored change was detected,
            so the awareness date lives in evidence an auditor can check rather
            than in someone’s memory. Monitoring information only. Not legal
            advice.
          </p>
        </div>
      </div>
    </section>
  )
}

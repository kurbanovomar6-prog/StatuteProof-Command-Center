import { CheckCircle2, XCircle, ArrowRight } from 'lucide-react'

// Scroll-reveal removed deliberately: content renders instantly, matching the
// rest of the site (the CSS fade-up utilities were neutered for the same
// reason — no reveal gating, no reduced-motion traps).

// ─── Content ──────────────────────────────────────────────────────────────────
const BEFORE = [
  {
    headline: 'Check 12 regulator websites manually each week',
    detail: 'CBUAE, VARA, DFSA, ADGM, UAE FIU — each publishes independently. A compliance officer doing this by hand spends 2–4 hours weekly copying page text into a spreadsheet.',
  },
  {
    headline: 'Miss a Friday evening update until Monday',
    detail: 'Regulators publish on their schedule, not yours. Weekend publications sit undetected until someone does the next manual pass.',
  },
  {
    headline: "Can't prove to auditors when you found out",
    detail: 'A manually maintained spreadsheet with no timestamps and no source URLs does not hold up under board scrutiny or regulatory inquiry.',
  },
  {
    headline: 'Write the compliance memo yourself — from scratch',
    detail: 'Once a change is found, someone must read the whole document, determine relevance to your licence type, and draft a response brief — all before anyone is alerted.',
  },
]

const AFTER = [
  {
    headline: 'Changes captured from the official source once monitoring is activated',
    detail: 'Once activated, scheduled checks run against selected official portals on an operator-set cadence. No manual portal visits. No spreadsheet rows to maintain.',
  },
  {
    headline: 'Draft brief prepared for review when a change is detected',
    detail: 'When a change is detected, the system prepares a structured AI-written draft analysis: what changed, why it may matter, what to consider. Scoped to your licence type.',
  },
  {
    headline: 'Cryptographic timestamp records when a change was captured',
    detail: 'SHA-256 hash, detection timestamp, and source URL are stored at the moment of detection, so your evidence record is available for audit review from the first captured run.',
  },
  {
    headline: 'AI writes the first draft — you review and decide',
    detail: 'A structured monitoring brief reaches your MLRO for review — human sign-off is required before a brief is delivered to your team. High-risk alerts are held for review; routine alerts arrive automatically with the sealed evidence record.',
  },
]

// ─── Column component ─────────────────────────────────────────────────────────
function Column({ tone, items }) {
  const isBefore = tone === 'before'

  return (
    <div>
      {/* Column header */}
      <div
        className={`mb-4 flex items-center gap-3 rounded-xl px-4 py-3 ${
          isBefore
            ? 'border border-rose-400/15 bg-rose-500/[0.06]'
            : 'border border-emerald-400/20 bg-emerald-500/[0.06]'
        }`}
      >
        <div
          className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg ${
            isBefore
              ? 'border border-rose-400/20 bg-rose-400/10'
              : 'border border-emerald-400/25 bg-emerald-400/10'
          }`}
        >
          {isBefore ? (
            <XCircle className="h-4 w-4 text-rose-300" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-300" />
          )}
        </div>
        <h3 className="text-base font-bold text-white">
          {isBefore ? 'Before StatuteProof' : 'After StatuteProof'}
        </h3>
      </div>

      {/* Items */}
      <div className="space-y-3">
        {items.map((item, i) => (
          <div
            key={i}
            className={`rounded-xl border p-4 transition-all duration-200 hover:-translate-y-[2px] ${
              isBefore
                ? 'border-slate-800 bg-slate-950/50 hover:border-rose-400/20'
                : 'border-slate-800/70 bg-slate-900/40 hover:border-emerald-400/25'
            }`}
          >
            <div className="flex items-start gap-3">
              {isBefore ? (
                <XCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400/60" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-400" />
              )}
              <div>
                <p
                  className={`text-sm font-semibold leading-snug ${
                    isBefore ? 'text-slate-300' : 'text-slate-100'
                  }`}
                >
                  {item.headline}
                </p>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
                  {item.detail}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main section ─────────────────────────────────────────────────────────────
export default function WithoutWith() {
  return (
    <section
      className="py-24"
      style={{ background: 'linear-gradient(180deg, #040B16 0%, #07111F 50%, #040B16 100%)' }}
      id="before-after"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        {/* Section header */}
        <div className="mb-12 text-center">
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            What changes for your team
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
            A monitoring record your MLRO can show an auditor
          </h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            Most compliance teams are still running manual checks, finding out about regulatory
            changes from peers, and writing their own briefs from scratch. Here is what changes.
          </p>
        </div>

        {/* Two-column comparison */}
        <div className="grid gap-6 md:grid-cols-2">
          <Column tone="before" items={BEFORE} />
          <Column tone="after" items={AFTER} />
        </div>

        {/* Arrow bridge on desktop */}
        <div className="relative hidden md:block" aria-hidden="true">
          <div
            className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center"
            style={{ top: '-100%' }}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-400/10">
              <ArrowRight className="h-4 w-4 text-cyan-400" />
            </div>
          </div>
        </div>

        {/* Workflow step strip */}
        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-950/35 px-4 py-4">
          <p className="mb-3 text-center text-[10px] font-bold uppercase tracking-widest text-slate-600">
            The StatuteProof detection pipeline
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2 text-xs text-slate-400">
            {[
              'Official source checked',
              'Change detected',
              'Evidence record stored',
              'Before/after diff created',
              'AI brief drafted',
              'Scoped to your profile',
              'Human review',
              'Delivered to your team',
            ].map((step, index, arr) => (
              <span key={step} className="inline-flex items-center gap-2">
                <span className="text-slate-300">{step}</span>
                {index < arr.length - 1 && (
                  <span className="text-cyan-400/40">→</span>
                )}
              </span>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <p className="mt-6 text-center text-[11px] leading-relaxed text-slate-600">
          Monitoring intelligence only. Not legal advice. Not a guarantee of compliance.
          Selected-source scope — not a full regulatory universe. Consult qualified professionals
          before making regulatory or operational decisions.
        </p>

      </div>
    </section>
  )
}

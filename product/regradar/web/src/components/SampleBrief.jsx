import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileText,
  ShieldCheck,
  Users,
} from 'lucide-react'

const affected = ['Banks', 'Payment institutions', 'Fintech', 'Compliance teams']

const reviewSteps = [
  'Review full circular on cbuae.gov.ae',
  'Assess current CDD procedures against updated thresholds',
  'Escalate to compliance and legal teams for implementation guidance',
]

const proofItems = [
  ['Official source', 'cbuae.gov.ae'],
  ['Extraction quality', 'PASS (HTML monitoring)'],
  ['Known limitations', 'Full PDF attachment requires manual download to verify complete circular text'],
]

const deliveryItems = [
  ['Relevance profile', 'Banks · Payment institutions · Fintech'],
  ['Human review', 'Reviewed before delivery'],
]

function DetailRow({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm text-slate-200">{value}</div>
    </div>
  )
}

export default function SampleBrief() {
  return (
    <section className="bg-[#07111F] py-20" id="sample-brief">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <FileText className="h-4 w-4" />
            Sample output
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">What a monitoring brief looks like</h2>
          <p className="mx-auto max-w-3xl text-slate-400">
            When StatuteProof detects a change in an official UAE regulatory source, your compliance team
            receives a reviewed brief like this. Content below is illustrative — not live regulatory data.
          </p>
        </div>

        <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-[0_24px_70px_rgba(0,0,0,0.35)]">
          <div className="border-b border-slate-800 bg-slate-950 px-5 py-4 sm:px-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">
                    Sample output
                  </span>
                  <span className="rounded-full border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs font-semibold text-red-200">
                    HIGH
                  </span>
                </div>
                <h3 className="max-w-2xl text-lg font-semibold leading-snug text-white">
                  CBUAE Circular: Updated AML/CFT Obligations for Licensed Financial Institutions
                </h3>
              </div>
              <div className="text-left text-xs text-slate-400 sm:text-right">
                <div>Source: CBUAE — Central Bank of UAE</div>
                <div className="mt-1">Date detected: 2026-05-21 09:14 UTC</div>
              </div>
            </div>
          </div>

          <div className="grid gap-0 lg:grid-cols-[1fr_280px]">
            <div className="space-y-6 p-5 sm:p-6">
              <div>
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-cyan-300">
                  <AlertTriangle className="h-4 w-4" />
                  What changed
                </div>
                <p className="text-sm leading-relaxed text-slate-300">
                  The Central Bank of UAE published an updated circular on AML/CFT customer due diligence
                  requirements. Key changes include revised beneficial ownership identification thresholds
                  and enhanced monitoring obligations for high-risk customer segments.
                </p>
              </div>

              <div>
                <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-amber-300">
                  <ShieldCheck className="h-4 w-4" />
                  Why it matters
                </div>
                <p className="text-sm leading-relaxed text-slate-300">
                  Licensed banks, payment institutions and fintech companies operating under CBUAE supervision
                  must review their CDD procedures. Non-compliance may be raised in regulatory examination findings.
                </p>
              </div>

              <div>
                <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-emerald-300">
                  <Users className="h-4 w-4" />
                  Potentially affected
                </div>
                <div className="flex flex-wrap gap-2">
                  {affected.map(item => (
                    <span key={item} className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Suggested review steps
                </div>
                <ol className="space-y-2">
                  {reviewSteps.map((step, index) => (
                    <li key={step} className="flex gap-3 text-sm leading-relaxed text-slate-300">
                      <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-emerald-400/10 text-xs font-semibold text-emerald-300">
                        {index + 1}
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>

            <aside className="border-t border-slate-800 bg-slate-950/45 p-5 sm:p-6 lg:border-l lg:border-t-0">
              <div className="mb-5">
                <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <ExternalLink className="h-4 w-4" />
                  Source proof
                </div>
                <div className="space-y-3">
                  {proofItems.map(([label, value]) => (
                    <DetailRow key={label} label={label} value={value} />
                  ))}
                </div>
              </div>

              <div className="mb-5">
                <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <CheckCircle2 className="h-4 w-4" />
                  Delivery
                </div>
                <div className="space-y-3">
                  {deliveryItems.map(([label, value]) => (
                    <DetailRow key={label} label={label} value={value} />
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-amber-400/20 bg-amber-400/10 p-3 text-xs leading-relaxed text-amber-100">
                Not legal advice. Verify against official source and qualified counsel.
              </div>
            </aside>
          </div>
        </div>

        <p className="mx-auto mt-5 max-w-3xl text-center text-xs leading-relaxed text-slate-500">
          StatuteProof generates monitoring briefs for informational purposes only. All outputs are reviewed
          before delivery. This is sample content — not real regulatory data. StatuteProof does not guarantee
          detection of all regulatory changes.
        </p>
      </div>
    </section>
  )
}

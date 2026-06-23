import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileText,
  ShieldCheck,
  Lock,
} from 'lucide-react'

// SAMPLE / FAKE — illustrative content only, not real regulatory data

const DIFF_LINES = [
  { type: 'context', text: ' Section 4.3(b) — Suspicious Transaction Reporting' },
  { type: 'context', text: ' Regulated entities shall file a Suspicious Transaction' },
  { type: 'context', text: ' Report (STR) with the Financial Intelligence Unit for:' },
  { type: 'removed', text: '-  Transactions exceeding AED 55,000 that cannot be' },
  { type: 'added',   text: '+  Transactions exceeding AED 40,000 that cannot be' },
  { type: 'context', text: '   justified by a plausible lawful purpose, regardless' },
  { type: 'context', text: '   of whether the transaction is completed or not.' },
]

const ACTION_STEPS = [
  'Update AML system transaction monitoring threshold to AED 40,000',
  'Brief MLRO and all compliance officers on the revised threshold',
  'Review last 90 days of transactions between AED 40,000–55,000',
  'Update internal AML policy documentation and procedures manual',
  'File updated procedures with senior management by 1 March 2025',
]

const CIRCLE_NUMS = ['①', '②', '③', '④', '⑤']

export default function SampleBrief() {
  return (
    <section className="bg-[#07111F] py-20" id="sample-brief">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        {/* Section header */}
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <FileText className="h-4 w-4" />
            SAMPLE / DEMO — not a real regulatory update
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">What a monitoring brief looks like</h2>
          <p className="mx-auto max-w-3xl text-slate-400">
            When StatuteProof detects a change in an official UAE regulatory source, your compliance team
            receives a reviewed brief like this. Content below is illustrative — not live regulatory data.
          </p>
        </div>

        {/* Brief card */}
        <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-slate-700 bg-[#1e293b] shadow-[0_24px_70px_rgba(0,0,0,0.45)]">

          {/* ── Header bar ─────────────────────────────────────────────── */}
          <div className="border-b border-slate-700 bg-slate-950 px-5 py-4 sm:px-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex-1 min-w-0">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  {/* SAMPLE label — small, top-right intent is embedded here for accessibility */}
                  <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">
                    SAMPLE — Illustrative content only
                  </span>
                  <span className="rounded-full border border-red-500/40 bg-red-500/15 px-2.5 py-1 text-xs font-bold text-red-300">
                    HIGH RISK
                  </span>
                </div>
                <div className="text-[11px] font-semibold uppercase tracking-widest text-slate-500 mb-1">
                  STATUTEPROOF MONITORING BRIEF
                </div>
                <h3 className="max-w-2xl text-base font-semibold leading-snug text-white">
                  CBUAE — Anti-Money Laundering Guidance: STR Threshold Amendment
                </h3>
              </div>
              <div className="text-left text-xs text-slate-400 sm:text-right shrink-0">
                <div className="font-medium text-slate-300">Source: CBUAE</div>
                <div className="mt-1">cbuae.gov.ae</div>
                <div className="mt-1">Detected: 2025-01-15 07:23:41 UTC</div>
              </div>
            </div>
          </div>

          {/* ── Body ───────────────────────────────────────────────────── */}
          <div className="divide-y divide-slate-700/60">

            {/* WHAT CHANGED */}
            <div className="px-5 py-5 sm:px-6">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-cyan-300">
                <AlertTriangle className="h-3.5 w-3.5" />
                What Changed
              </div>
              <p className="mb-4 text-sm leading-relaxed text-slate-300">
                Section 4.3(b) of the CBUAE AML/CFT Guidance was amended. The reporting threshold
                for Suspicious Transaction Reports (STRs) was lowered from{' '}
                <span className="font-semibold text-white">AED 55,000</span> to{' '}
                <span className="font-semibold text-white">AED 40,000</span>. This applies to all
                licensed DNFBPs and financial institutions supervised by CBUAE.
              </p>

              {/* Inline diff */}
              <div className="overflow-hidden rounded-lg border border-slate-700 bg-[#0d1b2e]">
                <div className="flex items-center justify-between border-b border-slate-700 bg-slate-950/70 px-4 py-2">
                  <span className="font-mono text-xs text-slate-400">cbuae-aml-guidance.txt — diff</span>
                  <span className="text-xs text-slate-500">2025-01-15 07:23:41 UTC</span>
                </div>
                <div className="overflow-x-auto">
                  <pre className="p-4 text-xs leading-6">
                    {DIFF_LINES.map((line, i) => (
                      <div
                        key={i}
                        className={
                          line.type === 'added'
                            ? 'bg-emerald-950/40 text-emerald-300 pl-1'
                            : line.type === 'removed'
                            ? 'bg-red-950/40 text-red-300 pl-1'
                            : 'text-slate-500'
                        }
                      >
                        {line.text}
                      </div>
                    ))}
                  </pre>
                </div>
                <div className="border-t border-slate-700 bg-slate-950/45 px-4 py-2 text-xs text-slate-500">
                  SHA-256 hash recorded for both states · Diff is illustrative SAMPLE content
                </div>
              </div>
            </div>

            {/* WHY IT MATTERS */}
            <div className="px-5 py-5 sm:px-6">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-amber-300">
                <ShieldCheck className="h-3.5 w-3.5" />
                Why It Matters
              </div>
              <p className="text-sm leading-relaxed text-slate-300">
                All licensed DNFBPs and financial institutions supervised by CBUAE must update their
                transaction monitoring systems immediately. Failure to file STRs for transactions above the
                new AED 40,000 threshold may constitute a regulatory violation and could be identified
                in a CBUAE supervisory examination.
              </p>
            </div>

            {/* WHAT TO DO */}
            <div className="px-5 py-5 sm:px-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  What To Do
                </div>
                <span className="flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-300">
                  Urgency: HIGH
                </span>
              </div>
              <ol className="space-y-2.5">
                {ACTION_STEPS.map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm leading-relaxed text-slate-300">
                    <span className="shrink-0 text-base font-medium text-emerald-400 leading-none mt-0.5">
                      {CIRCLE_NUMS[i]}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* EVIDENCE CHAIN */}
            <div className="px-5 py-5 sm:px-6">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-slate-400">
                  <Lock className="h-3.5 w-3.5" />
                  Evidence Chain
                </div>
                <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/35 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-bold text-emerald-300">
                  &#10003; Verified
                </span>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4 space-y-3">
                {/* Hash row */}
                <div className="grid gap-1">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Current SHA-256</span>
                  <span className="font-mono text-xs text-emerald-300 break-all">
                    a3f8b2c1d4e5f6789abcde012345678f9012345678abcdef012345678abcdef01
                  </span>
                </div>
                {/* Previous hash row */}
                <div className="grid gap-1">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Previous SHA-256</span>
                  <span className="font-mono text-xs text-slate-400 break-all">
                    9f2e1a3b4c5d6e7f8901234567890abcdef1234567890abcdef1234567890abc
                  </span>
                </div>
                {/* Metadata row */}
                <div className="grid grid-cols-2 gap-3 pt-1 border-t border-slate-700">
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Captured</span>
                    <div className="mt-0.5 font-mono text-xs text-slate-300">2025-01-15 07:23:41 UTC</div>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Chain Status</span>
                    <div className="mt-0.5 flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block" />
                      <span className="text-xs font-bold text-emerald-300">INTACT</span>
                    </div>
                  </div>
                </div>
                {/* Source link */}
                <div className="flex items-center gap-2 pt-1 border-t border-slate-700">
                  <Lock className="h-3 w-3 text-emerald-400 shrink-0" />
                  <span className="font-mono text-xs text-blue-300">
                    https://cbuae.gov.ae/en-AE/Pages/AML/AML-Guidelines.aspx
                  </span>
                  <ExternalLink className="h-3 w-3 text-slate-500 shrink-0" />
                </div>
              </div>
            </div>

          </div>

          {/* ── Disclaimer footer ───────────────────────────────────────── */}
          <div className="flex items-start gap-2.5 border-t border-slate-700 bg-slate-950/50 px-5 py-4 sm:px-6">
            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed text-slate-500">
              <span className="font-semibold text-slate-400">SAMPLE / FAKE — illustrative content only.</span>
              {' '}StatuteProof reports are for monitoring information only. Not legal advice and not a guarantee of compliance.
              Verify all information against official source material and qualified legal or compliance counsel before acting.
            </p>
          </div>

        </div>

        <p className="mx-auto mt-5 max-w-3xl text-center text-xs leading-relaxed text-slate-600">
          StatuteProof generates monitoring briefs for informational purposes only. All outputs are reviewed
          before delivery. This is sample content — not real regulatory data. StatuteProof does not guarantee
          detection of all regulatory changes.
        </p>
      </div>
    </section>
  )
}

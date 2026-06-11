import { AlertTriangle, FileSearch, Link2 } from 'lucide-react'

const PANELS = [
  {
    icon: Link2,
    title: 'The source',
    body: [
      'Every brief names the official source — CBUAE, VARA, DFSA, or whichever regulator published the change. The brief includes a direct link to the official source page we monitored. Not a summary. Not a secondary report. The actual regulator portal.',
      'If the link is inaccessible at the time of the run, that failure is logged and disclosed — not silently dropped.',
    ],
  },
  {
    icon: FileSearch,
    title: 'The check',
    body: [
      'Each monitoring run produces a timestamped record: when we checked, what we extracted, what method we used (HTML structured content, PDF text, or page snapshot), and whether the extracted content met minimum quality thresholds. The delta status — UNCHANGED, CHANGED, QUALITY_DROP — is part of the brief record.',
      'When extraction quality drops, the run is flagged for review before any alert is dispatched. We do not send alerts based on degraded extraction.',
    ],
  },
  {
    icon: AlertTriangle,
    title: 'The limits',
    body: [
      'Every brief includes a Known Limitations field. If a source uses dynamic rendering that can produce false CHANGED signals, we state it. If a source is PDF-primary with variable extraction quality, we state it. If a source was inaccessible during the run, we state it. The limitations field is never empty and never optional.',
      'StatuteProof provides early-warning regulatory intelligence. It is not a law firm. Final compliance decisions should be reviewed by qualified legal or compliance professionals.',
    ],
  },
]

export default function TrustLayer() {
  return (
    <section className="py-20 bg-[#07111F]" id="trust">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <span className="inline-block text-xs font-semibold text-[#16D9F5] uppercase tracking-widest mb-4">
            Evidence Trail
          </span>
          <h2 className="text-3xl font-bold text-white mb-3">
            Every alert is auditable
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto leading-relaxed">
            The question a compliance officer should be able to answer after receiving any regulatory alert:
            <span className="italic"> can I verify this myself?</span> StatuteProof is designed so the answer is always yes.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-5 mb-8">
          {PANELS.map(panel => {
            const Icon = panel.icon
            return (
              <div
                key={panel.title}
                className="bg-[#0A1628] border border-slate-800 rounded-xl p-6 hover:border-[#16D9F5]/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-[#16D9F5]/10 border border-[#16D9F5]/20 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-[#16D9F5]" />
                </div>
                <h3 className="font-semibold text-white text-sm mb-3">{panel.title}</h3>
                <div className="space-y-3">
                  {panel.body.map(paragraph => (
                    <p key={paragraph} className="text-xs text-slate-400 leading-relaxed">{paragraph}</p>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        <div className="bg-[#0A1628] border border-slate-800 rounded-xl p-6">
          <p className="text-sm text-slate-400 leading-relaxed text-center max-w-3xl mx-auto">
            A compliance alert you cannot verify is a liability, not an asset. Source proof is not an
            optional feature. It is the baseline.
          </p>
        </div>

        <div className="bg-[#0A1628] text-slate-100 rounded-xl p-6 mt-6 border border-slate-800">
          <div className="text-[11px] font-bold text-cyan-300 uppercase tracking-widest mb-3">
            Sample evidence-backed brief — illustrative
          </div>
          <div className="grid md:grid-cols-2 gap-5">
            <div>
              <h3 className="font-bold text-lg mb-3 text-white">VARA publication change</h3>
              <dl className="space-y-2 text-sm">
                <div><dt className="font-semibold inline text-slate-300">Source:</dt> <dd className="inline text-slate-400">Virtual Assets Regulatory Authority (VARA)</dd></div>
                <div><dt className="font-semibold inline text-slate-300">Checked:</dt> <dd className="inline text-slate-400">Sample timestamp · 2026-05-30 14:32 UTC</dd></div>
                <div><dt className="font-semibold inline text-slate-300">Change status:</dt> <dd className="inline text-amber-300">Changed — sample</dd></div>
                <div><dt className="font-semibold inline text-slate-300">Relevant to:</dt> <dd className="inline text-slate-400">VASP operators, crypto exchanges, digital asset custodians</dd></div>
              </dl>
            </div>
            <div className="text-sm text-slate-400 leading-relaxed">
              <p className="mb-3">
                <strong className="text-white">What changed:</strong> Illustrative wording: VARA publication page includes a new item affecting licensing or custody obligations.
              </p>
              <p className="mb-3">
                <strong className="text-white">Recommended next step:</strong> Review obligations and consult UAE-qualified legal counsel before changing internal controls.
              </p>
              <p>
                <strong className="text-white">Proof:</strong> Official source URL, timestamp, extraction quality, and known limitations are attached to the reviewed brief.
              </p>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}

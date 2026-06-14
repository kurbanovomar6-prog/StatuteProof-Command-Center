import { useState } from 'react'
import {
  FileText, AlertTriangle, Users, CheckSquare, BookOpen,
  ExternalLink, Brain, ShieldCheck, ChevronDown, ChevronUp,
} from 'lucide-react'
import { Badge } from './ui/Badge'

const FEATURES = [
  {
    Icon: FileText,
    title: 'Explain what changed',
    desc: 'Summarizes official regulatory updates into clear, readable briefs without legal jargon.',
  },
  {
    Icon: AlertTriangle,
    title: 'Explain why it matters',
    desc: 'Highlights licensing, reporting, AML/CFT, tax, enforcement, deadline or penalty signals.',
  },
  {
    Icon: Users,
    title: 'Identify who may be affected',
    desc: 'Shows whether banks, fintechs, VASPs, payment companies, legal or compliance teams may need to review.',
  },
  {
    Icon: CheckSquare,
    title: 'Suggest review steps',
    desc: 'Cautious next steps: review official sources, check obligations, escalate to compliance or legal teams.',
  },
  {
    Icon: BookOpen,
    title: 'Generate weekly digests',
    desc: 'Turns multiple updates into management-friendly summaries by jurisdiction and risk level.',
  },
]

const AFFECTED_TAGS = ['DPT service providers', 'Crypto exchanges', 'Payment institutions', 'Compliance teams']

const REVIEW_STEPS = [
  'Review the official CBUAE or VARA source layer',
  'Assess licensing, AML/CFT and reporting relevance',
  'Escalate to compliance and legal teams for guidance',
]

const TRUST_POINTS = [
  { mark: '✓', text: 'Official source link included',                       c: 'text-emerald-400' },
  { mark: '✓', text: 'Paragraph-level change detected',                     c: 'text-emerald-400' },
  { mark: '✓', text: 'Source health: Evidence confirmed',                   c: 'text-emerald-400' },
  { mark: '✓', text: 'Risk signals: AML/CFT · reporting · licensing · deadline', c: 'text-emerald-400' },
  { mark: '~', text: 'AI confidence: Medium',                               c: 'text-amber-400'   },
  { mark: '~', text: 'Human review recommended for high-risk updates',      c: 'text-amber-400'   },
  { mark: '!', text: 'Not legal advice',                                    c: 'text-slate-500'   },
]

export default function AIAnalyst() {
  const [trustOpen, setTrustOpen] = useState(false)

  return (
    <section className="py-20 bg-slate-50" id="ai-analyst">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        {/* ── Header ───────────────────────────────────────────────────── */}
        <div className="text-center mb-14">
          <Badge variant="blue" className="mb-4">AI Intelligence</Badge>
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            StatuteProof AI Analyst
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed">
            StatuteProof does not only detect regulatory changes. It turns them into clear
            AI-assisted briefs with risk explanations, affected organizations, suggested
            review steps and official source links.
          </p>
        </div>

        {/* ── Two-column: features + brief mockup ──────────────────────── */}
        <div className="grid lg:grid-cols-2 gap-10 items-start mb-12">

          {/* Left — 5 feature cards */}
          <div className="space-y-3">
            {FEATURES.map(({ Icon, title, desc }) => (
              <div
                key={title}
                className="flex gap-4 bg-white border border-slate-200 rounded-xl p-5"
              >
                <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900 text-sm">{title}</p>
                  <p className="text-slate-500 text-xs mt-1 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Right — AI brief mockup */}
          <div className="rounded-2xl bg-slate-900 overflow-hidden shadow-xl border border-slate-700">

            {/* Chrome bar */}
            <div className="bg-slate-800 px-5 py-3 flex items-center justify-between border-b border-slate-700">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
                  AI Brief
                </span>
              </div>
              <div className="flex items-center gap-2.5">
                <span className="text-xs text-slate-400">AE · VARA</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-800">
                  HIGH
                </span>
              </div>
            </div>

            {/* Brief title */}
            <div className="px-5 pt-4 pb-3.5 border-b border-slate-800">
              <p className="text-white font-semibold text-sm leading-snug">
                VARA Rulebook Preview: Sample AML/CFT Requirements for VASP Teams
              </p>
              <p className="text-slate-500 text-xs mt-1.5">Sample · vara.ae</p>
            </div>

            <div className="divide-y divide-slate-800">

              {/* What changed */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                  What changed
                </p>
                <p className="text-slate-300 text-xs leading-relaxed">
                  A UAE virtual asset source layer is shown in sample format, including
                  source proof, profile relevance, human review status and limitation notes.
                </p>
              </div>

              {/* Why it matters */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1.5">
                  Why it matters
                </p>
                <p className="text-slate-300 text-xs leading-relaxed">
                  VASP and crypto compliance teams need source-backed review steps before
                  relying on any monitoring output or internal compliance action.
                </p>
              </div>

              {/* Affected */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Potentially affected
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {AFFECTED_TAGS.map(tag => (
                    <span
                      key={tag}
                      className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Review steps */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                  Suggested review steps
                </p>
                <ol className="space-y-1.5">
                  {REVIEW_STEPS.map((step, i) => (
                    <li key={i} className="flex gap-2 text-xs text-slate-300">
                      <span className="text-emerald-500 flex-shrink-0 font-medium">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>

              {/* Source link */}
              <div className="px-5 py-3.5 flex items-center justify-between">
                <p className="text-xs text-slate-500">Official source</p>
                <span className="inline-flex items-center gap-1.5 text-xs text-blue-400">
                  vara.ae / source-readiness-sample
                  <ExternalLink className="w-3 h-3" />
                </span>
              </div>

              {/* Why trust this alert? — collapsible */}
              <div>
                <button
                  onClick={() => setTrustOpen(v => !v)}
                  className="w-full px-5 py-3 flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 transition-colors border-t border-slate-800"
                >
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Why trust this alert?
                  </span>
                  {trustOpen
                    ? <ChevronUp className="w-3.5 h-3.5" />
                    : <ChevronDown className="w-3.5 h-3.5" />
                  }
                </button>
                {trustOpen && (
                  <div className="px-5 pb-4 space-y-1.5">
                    {TRUST_POINTS.map(({ mark, text, c }) => (
                      <div key={text} className="flex items-start gap-2">
                        <span className={`${c} text-xs font-bold w-3 flex-shrink-0`}>{mark}</span>
                        <p className="text-xs text-slate-300 leading-relaxed">{text}</p>
                      </div>
                    ))}
                    <p className="text-xs text-slate-500 pt-2 mt-1 border-t border-slate-800">
                      Every StatuteProof alert is backed by source-level evidence, detected changes,
                      risk signals and official links.
                    </p>
                  </div>
                )}
              </div>

            </div>

            {/* Disclaimer strip */}
            <div className="px-5 py-3 bg-slate-800/50 border-t border-slate-700 flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
              <p className="text-xs text-slate-500">
                Not legal advice. Verify against official sources and qualified counsel.
              </p>
            </div>

          </div>

        </div>

        {/* ── Safety disclaimer block ───────────────────────────────────── */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl px-6 py-5">
          <div className="flex gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800 leading-relaxed">
              <span className="font-semibold">StatuteProof is a regulatory monitoring and intelligence tool.</span>{' '}
              AI-assisted briefs do not replace legal advice. All outputs should be verified
              against official source links and qualified counsel when needed.
            </p>
          </div>
        </div>

      </div>
    </section>
  )
}

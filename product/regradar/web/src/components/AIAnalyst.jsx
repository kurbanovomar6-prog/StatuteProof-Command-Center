import { useState, useEffect, useRef } from 'react'
import {
  FileText, AlertTriangle, Users, CheckSquare, BookOpen,
  ExternalLink, Brain, ShieldCheck, ChevronDown, ChevronUp,
  Scale, MapPin,
} from 'lucide-react'
import { Badge } from './ui/Badge'

// SAMPLE / FAKE — illustrative content only, not real regulatory data

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
  'Review the official VARA source and compare to previous version',
  'Assess AML/CFT and licensing obligation relevance to your entity',
  'Escalate to compliance and legal teams for implementation guidance',
]

const TRUST_POINTS = [
  { mark: '✓', text: 'Official source link included',                            c: 'text-emerald-400' },
  { mark: '✓', text: 'Paragraph-level change detected and hashed',              c: 'text-emerald-400' },
  { mark: '✓', text: 'Source health: Evidence confirmed',                        c: 'text-emerald-400' },
  { mark: '✓', text: 'Risk signals: AML/CFT · reporting · licensing · deadline', c: 'text-emerald-400' },
  { mark: '~', text: 'AI confidence: 87% — high but not certain',               c: 'text-amber-400'   },
  { mark: '~', text: 'Human review recommended for high-risk updates',           c: 'text-amber-400'   },
  { mark: '!', text: 'Not legal advice',                                         c: 'text-slate-500'   },
]

const EXECUTIVE_SUMMARY =
  'VARA has amended Section 7.2 of the Virtual Assets Regulatory Rulebook to introduce mandatory AML/CFT controls for DPT service providers processing transactions above AED 35,000. Affected entities must update their transaction monitoring systems and appoint a designated AML Compliance Officer within 45 days of publication.'

// Typewriter hook — types the string character by character
function useTypewriter(text, speed = 22, startDelay = 400) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  const indexRef = useRef(0)
  const timerRef = useRef(null)

  // Reset during render when the target text changes (lint-safe pattern),
  // instead of a synchronous setState inside the effect.
  const [prevText, setPrevText] = useState(text)
  if (prevText !== text) {
    setPrevText(text)
    setDisplayed('')
    setDone(false)
    // indexRef is reset inside the effect (refs must not be written during render)
  }

  useEffect(() => {
    indexRef.current = 0

    const startTimer = setTimeout(() => {
      timerRef.current = setInterval(() => {
        indexRef.current += 1
        setDisplayed(text.slice(0, indexRef.current))
        if (indexRef.current >= text.length) {
          clearInterval(timerRef.current)
          setDone(true)
        }
      }, speed)
    }, startDelay)

    return () => {
      clearTimeout(startTimer)
      clearInterval(timerRef.current)
    }
  }, [text, speed, startDelay])

  return { displayed, done }
}

// Animated confidence meter bar
function ConfidenceMeter({ value }) {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setWidth(value), 600)
    return () => clearTimeout(t)
  }, [value])

  const color =
    value >= 80 ? 'bg-emerald-400' :
    value >= 60 ? 'bg-amber-400' :
    'bg-red-400'

  return (
    <div className="flex items-center gap-2.5">
      <div className="h-1.5 flex-1 rounded-full bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${color}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className={`text-xs font-bold tabular-nums ${value >= 80 ? 'text-emerald-300' : value >= 60 ? 'text-amber-300' : 'text-red-300'}`}>
        {value}%
      </span>
    </div>
  )
}

export default function AIAnalyst() {
  const [trustOpen, setTrustOpen] = useState(false)
  const { displayed, done } = useTypewriter(EXECUTIVE_SUMMARY)

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

            {/* Brief metadata row — legal area + jurisdiction */}
            <div className="bg-slate-800/50 border-b border-slate-700 px-5 py-2.5 flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-300">
                <Scale className="w-3 h-3" />
                Legal Area: AML/CFT
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-600 bg-slate-700/50 px-2.5 py-0.5 text-xs font-semibold text-slate-300">
                <MapPin className="w-3 h-3" />
                Jurisdiction: UAE — VARA
              </span>
              <span className="ml-auto text-[10px] text-slate-500">SAMPLE / FAKE</span>
            </div>

            {/* Brief title */}
            <div className="px-5 pt-4 pb-3.5 border-b border-slate-800">
              <p className="text-white font-semibold text-sm leading-snug">
                VARA Rulebook Amendment: AML/CFT Requirements for DPT Service Providers
              </p>
              <p className="text-slate-500 text-xs mt-1.5">Sample · vara.ae</p>
            </div>

            <div className="divide-y divide-slate-800">

              {/* Executive summary — typewriter effect */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Executive Summary
                </p>
                <p className="text-slate-300 text-xs leading-relaxed min-h-[4.5rem]">
                  {displayed}
                  {!done && (
                    <span className="inline-block w-0.5 h-3 bg-blue-400 ml-0.5 animate-pulse align-middle" />
                  )}
                </p>
              </div>

              {/* AI Confidence meter */}
              <div className="px-5 py-3.5">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    AI Confidence
                  </p>
                  <span className="text-[10px] text-slate-500">Source-backed analysis</span>
                </div>
                <ConfidenceMeter value={87} />
                <p className="text-[10px] text-slate-600 mt-1.5">
                  Human review recommended before any compliance action on high-risk updates
                </p>
              </div>

              {/* What changed */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                  What changed
                </p>
                <p className="text-slate-300 text-xs leading-relaxed">
                  Section 7.2 now mandates AML/CFT controls for DPT service providers processing
                  transactions above AED 35,000. A designated AML Compliance Officer is now required
                  within 45 days of publication.
                </p>
              </div>

              {/* Why it matters */}
              <div className="px-5 py-3.5">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1.5">
                  Why it matters
                </p>
                <p className="text-slate-300 text-xs leading-relaxed">
                  VASP and crypto compliance teams must update transaction monitoring thresholds
                  and appoint a compliance officer before the 45-day deadline or risk regulatory findings.
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
                  vara.ae / rulebook / section-7
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

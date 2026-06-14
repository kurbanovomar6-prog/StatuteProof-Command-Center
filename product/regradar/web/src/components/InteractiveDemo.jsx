import { useState } from 'react'
import { Brain, ShieldCheck, AlertTriangle, ArrowRight, ExternalLink, ChevronDown, ChevronUp, Shield } from 'lucide-react'
import { Badge } from './ui/Badge'
import { normalizeExternalUrl } from '../utils/url'

// ── Static data ────────────────────────────────────────────────────────────────

const JURISDICTIONS = ['UAE']
const INDUSTRIES    = ['Fintech', 'Crypto / VASP', 'Payments', 'Legal & Compliance']

const FLAGS = {
  UAE:          '🇦🇪',
}

const RISK_DARK = {
  HIGH:   'bg-red-950 text-red-300 border border-red-800',
  MEDIUM: 'bg-amber-950 text-amber-300 border border-amber-800',
  LOW:    'bg-emerald-950 text-emerald-300 border border-emerald-800',
}

const CONF_STYLE = {
  High:   'bg-emerald-50 text-emerald-700',
  Medium: 'bg-amber-50 text-amber-700',
  Low:    'bg-slate-100 text-slate-500',
}

const SOURCE_DETAILS = {
  'Central Bank UAE': {
    officialName: 'Central Bank of the UAE (CBUAE)',
    type: 'Central bank / payments / AML-CFT source layer',
    extraction: 'HTML / rulebook / adapter review',
  },
  'VARA': {
    officialName: 'Virtual Assets Regulatory Authority (VARA)',
    type: 'Crypto / VASP regulator',
    extraction: 'HTML + document-link validation',
  },
  'DFSA': {
    officialName: 'Dubai Financial Services Authority (DFSA)',
    type: 'DIFC financial regulator',
    extraction: 'HTML / item-level validation',
  },
  'ADGM / FSRA': {
    officialName: 'ADGM Financial Services Regulatory Authority (FSRA)',
    type: 'ADGM financial regulator',
    extraction: 'HTML row extraction / proof-diff validation',
  },
}
// ── Demo alert dataset (4 jurisdictions × 4 industries = 16 entries) ──────────

const ALERTS = {
  UAE: {
    Fintech: {
      risk: 'MEDIUM', source: 'Central Bank UAE', category: 'Fintech / Payments', date: 'Sample',
      sourceUrl: 'centralbank.ae', sourceHealth: 'Readiness snapshot', aiConfidence: 'Medium',
      changeType: 'Sample readiness view',
      title: 'CBUAE Payments Guidance Preview',
      summary: 'Sample preview showing how a CBUAE payments or fintech source layer would be summarized for a UAE pilot profile.',
      affected: ['Fintech companies', 'Payment institutions', 'Compliance teams'],
      steps: ['Review the official CBUAE source layer', 'Confirm extraction readiness before activation', 'Document limitations in the pilot source map'],
      whatChanged: 'A CBUAE source layer is shown in sample format for readiness review.',
      whyMatters: 'Payments and fintech teams need source proof and validation status before relying on monitoring output.',
      signals: ['Payments', 'Licensing', 'AML/CFT'],
    },
    'Crypto / VASP': {
      risk: 'HIGH', source: 'VARA', category: 'VASP Licensing', date: 'Sample',
      sourceUrl: 'vara.ae', sourceHealth: 'Readiness snapshot', aiConfidence: 'High',
      changeType: 'Sample rulebook update',
      title: 'VARA Rulebook Update Preview',
      summary: 'Sample preview showing how a VARA rulebook update would be framed for VASP and crypto compliance teams.',
      affected: ['VASPs', 'Crypto exchanges', 'Fintech legal teams', 'Compliance teams'],
      steps: ['Review the official VARA publication', 'Check affected licence activity', 'Confirm document extraction before activation'],
      whatChanged: 'A VARA rulebook layer is shown as changed for sample purposes.',
      whyMatters: 'VASP teams need human-reviewed source proof before acting on regulatory changes.',
      signals: ['VASP', 'AML/CFT', 'Licensing'],
    },
    Payments: {
      risk: 'MEDIUM', source: 'Central Bank UAE', category: 'Payment Regulation', date: 'Sample',
      sourceUrl: 'centralbank.ae', sourceHealth: 'Readiness snapshot', aiConfidence: 'Medium',
      changeType: 'Sample payment source layer',
      title: 'Payment Regulation Preview',
      summary: 'Sample preview showing payment-regulation brief structure for UAE banks, PSPs and fintech teams.',
      affected: ['Payment companies', 'Banks', 'Fintech operators'],
      steps: ['Review CBUAE payment source layer', 'Assess profile relevance', 'Validate proof/diff before activation'],
      whatChanged: 'A UAE payment source layer is shown in sample format.',
      whyMatters: 'Payment institutions need confirmed source monitoring before depending on alert delivery.',
      signals: ['Payments', 'Reporting', 'Licensing'],
    },
    'Legal & Compliance': {
      risk: 'LOW', source: 'DFSA', category: 'DIFC / Legal Framework', date: 'Sample',
      sourceUrl: 'dfsa.ae', sourceHealth: 'Readiness snapshot', aiConfidence: 'Medium',
      changeType: 'Sample consultation layer',
      title: 'DIFC / DFSA Consultation Preview',
      summary: 'Sample preview showing source proof and limitation notes for DIFC / DFSA legal and compliance teams.',
      affected: ['Legal teams', 'Compliance officers', 'DIFC firms'],
      steps: ['Review DFSA consultation layer', 'Check DIFC Laws context', 'Record limitations before pilot activation'],
      whatChanged: 'A DFSA source layer is shown in sample format.',
      whyMatters: 'DIFC firms need source transparency and human review before relying on brief output.',
      signals: ['Legal', 'Consultations', 'Source proof'],
    },
  },
}
// ── Helper components ──────────────────────────────────────────────────────────

function LightProofField({ label, value }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-xs text-slate-600">{value}</p>
    </div>
  )
}

function DemoProofTrail({ demo }) {
  const [open, setOpen] = useState(false)
  const src    = SOURCE_DETAILS[demo.source] || {}
  const url    = normalizeExternalUrl(demo.sourceUrl)
  const health = demo.sourceHealth === 'PASS'

  return (
    <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <p className="text-sm font-semibold text-slate-800">Proof Trail</p>
        <button
          onClick={() => setOpen(v => !v)}
          className="ml-auto flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 transition-colors"
        >
          <Shield className="w-3 h-3" />
          Source proof
          {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      <div className="space-y-3">
        {[
          { ok: true,   label: 'Official source link', value: demo.sourceUrl },
          { ok: health, label: 'Source health',         value: demo.sourceHealth },
          { ok: true,   label: 'Change detected',       value: demo.changeType },
          { ok: true,   label: 'Risk signals',          value: demo.signals.join(' · ') },
          { ok: true,   label: 'Last checked',          value: 'Today' },
        ].map(({ ok, label, value }) => (
          <div key={label} className="flex items-start gap-2">
            <span className={`text-xs font-bold flex-shrink-0 mt-0.5 ${ok ? 'text-emerald-500' : 'text-amber-500'}`}>
              {ok ? '✓' : '~'}
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-700">{label}</p>
              <p className="text-xs text-slate-500 truncate">{value}</p>
            </div>
          </div>
        ))}

        <div className="pt-2 border-t border-slate-200">
          <div className="flex items-center gap-1.5">
            <ExternalLink className="w-3 h-3 text-blue-500 flex-shrink-0" />
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 font-medium hover:underline"
              >
                {demo.sourceUrl}
              </a>
            ) : (
              <p className="text-xs text-blue-600 font-medium">{demo.sourceUrl}</p>
            )}
          </div>
        </div>

        {open && (
          <div className="pt-3 border-t border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-emerald-600" />
                Source Proof
              </p>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${CONF_STYLE[demo.aiConfidence]}`}>
                {demo.aiConfidence}
              </span>
            </div>
            {src.officialName && <LightProofField label="Official source" value={src.officialName} />}
            {src.type         && <LightProofField label="Source type"     value={src.type} />}
            {src.extraction   && <LightProofField label="Extraction"      value={src.extraction} />}
            <LightProofField label="Detection method" value="Official-source HTML monitoring" />
            <LightProofField label="Last checked"     value={`${demo.date} (demo)`} />
            <div className="pt-2 border-t border-slate-200">
              <p className="text-[10px] text-slate-400 leading-relaxed">
                Sample preview — not production monitoring. StatuteProof provides source-backed intelligence, not legal advice.
              </p>
            </div>
          </div>
        )}

        <div className="flex items-start gap-1.5">
          <AlertTriangle className="w-3 h-3 text-slate-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-slate-400">Not legal advice</p>
        </div>
      </div>
    </div>
  )
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function InteractiveDemo() {
  const [sel, setSel] = useState({ jurisdiction: 'UAE', industry: 'Fintech' })
  const [fading, setFading] = useState(false)

  const changeSelection = (key, value) => {
    if (sel[key] === value) return
    setFading(true)
    setTimeout(() => {
      setSel(prev => ({ ...prev, [key]: value }))
      setFading(false)
    }, 140)
  }

  const demo = ALERTS[sel.jurisdiction][sel.industry]

  return (
    <section className="py-20 bg-white" id="interactive-demo">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        {/* ── Header ────────────────────────────────────────────────────── */}
        <div className="text-center mb-12">
          <Badge variant="blue" className="mb-4">Interactive Demo</Badge>
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            See StatuteProof in action
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Choose a market and use case to see how StatuteProof turns official regulatory
            updates into risk-based alerts, AI-assisted briefs and source-level proof.
          </p>
        </div>

        {/* ── Main layout: filters sidebar + dashboard ───────────────────── */}
        <div className="grid lg:grid-cols-4 gap-6">

          {/* ── Filters sidebar ─────────────────────────────────────────── */}
          <div className="lg:col-span-1 space-y-6">

            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
                Jurisdiction
              </p>
              <div className="flex flex-wrap lg:flex-col gap-2">
                {JURISDICTIONS.map(j => (
                  <button
                    key={j}
                    onClick={() => changeSelection('jurisdiction', j)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left ${
                      sel.jurisdiction === j
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {FLAGS[j]} {j}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
                Industry
              </p>
              <div className="flex flex-wrap lg:flex-col gap-2">
                {INDUSTRIES.map(i => (
                  <button
                    key={i}
                    onClick={() => changeSelection('industry', i)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left ${
                      sel.industry === i
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {i}
                  </button>
                ))}
              </div>
            </div>

            {/* Risk indicator */}
            <div className="hidden lg:block">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
                Risk level
              </p>
              <div className={`inline-flex items-center gap-2 text-xs font-bold px-3 py-2 rounded-lg border ${RISK_DARK[demo.risk]}`}>
                <span className={`w-2 h-2 rounded-full ${
                  demo.risk === 'HIGH' ? 'bg-red-400' : demo.risk === 'MEDIUM' ? 'bg-amber-400' : 'bg-emerald-400'
                }`} />
                {demo.risk}
              </div>
            </div>

          </div>

          {/* ── Dashboard panels ─────────────────────────────────────────── */}
          <div
            className={`lg:col-span-3 space-y-4 transition-opacity duration-150 ${fading ? 'opacity-0' : 'opacity-100'}`}
          >

            {/* Alert card — dark */}
            <div className="bg-slate-900 rounded-2xl p-6 border border-slate-700 shadow-lg">

              {/* Header row */}
              <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${RISK_DARK[demo.risk]}`}>
                    {demo.risk}
                  </span>
                  <span className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full font-medium">
                    DEMO
                  </span>
                  <span className="text-xs text-slate-400">
                    {sel.jurisdiction} · {demo.source}
                  </span>
                  <span className="text-xs bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded-full">
                    {demo.category}
                  </span>
                </div>
                <span className="text-xs text-slate-500 flex-shrink-0">{demo.date}</span>
              </div>

              <h3 className="text-white font-semibold text-base mb-3 leading-snug">
                {demo.title}
              </h3>
              <p className="text-slate-300 text-sm leading-relaxed mb-4">
                {demo.summary}
              </p>

              {/* Affected */}
              <div className="mb-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Potentially affected
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {demo.affected.map(a => (
                    <span
                      key={a}
                      className="text-xs bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-full"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>

              {/* Suggested review */}
              <div>
                <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-2">
                  Suggested review
                </p>
                <ol className="space-y-1.5">
                  {demo.steps.map((step, i) => (
                    <li key={i} className="flex gap-2 text-xs text-slate-300">
                      <span className="text-emerald-500 font-semibold flex-shrink-0">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>

              {/* Source limitation note */}
              {demo.note && (
                <div className="mt-4 flex items-start gap-2 bg-amber-950/40 border border-amber-800 rounded-lg px-3 py-2.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-300 leading-relaxed">{demo.note}</p>
                </div>
              )}
            </div>

            {/* AI Brief + Proof Trail — two columns */}
            <div className="grid sm:grid-cols-2 gap-4">

              {/* AI Brief */}
              <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Brain className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <p className="text-sm font-semibold text-slate-800">AI Brief</p>
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${CONF_STYLE[demo.aiConfidence]}`}>
                    {demo.aiConfidence} confidence
                  </span>
                </div>

                <div className="space-y-3.5">
                  <div>
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">
                      What changed
                    </p>
                    <p className="text-xs text-slate-600 leading-relaxed">{demo.whatChanged}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">
                      Why it matters
                    </p>
                    <p className="text-xs text-slate-600 leading-relaxed">{demo.whyMatters}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                      Who may be affected
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {demo.affected.map(a => (
                        <span
                          key={a}
                          className="text-xs bg-white border border-slate-200 text-slate-600 px-1.5 py-0.5 rounded"
                        >
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Proof Trail — upgraded with DemoProofTrail */}
              <DemoProofTrail key={`${sel.jurisdiction}-${sel.industry}`} demo={demo} />

            </div>

          </div>
        </div>

        {/* ── Disclaimer + CTAs ─────────────────────────────────────────── */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-6 pt-8 border-t border-slate-100">
          <p className="text-xs text-slate-400 max-w-md text-center sm:text-left leading-relaxed">
            This is sample demo data. StatuteProof is a regulatory monitoring and intelligence tool
            and does not provide legal advice.
          </p>
          <div className="flex gap-3 flex-shrink-0">
            <button
              onClick={() => document.querySelector('#demo')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-5 py-2.5 rounded-xl border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              View Sample Report
            </button>
            <button
              onClick={() => document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' })}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-colors"
            >
              Request Pilot
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </section>
  )
}

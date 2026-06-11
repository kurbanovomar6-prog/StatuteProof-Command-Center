import { useState } from 'react'
import { FileText, ShieldCheck, AlertTriangle, ExternalLink, ArrowRight } from 'lucide-react'
import { Badge } from './ui/Badge'

// ── Risk style maps ────────────────────────────────────────────────────────────

const RISK_VARIANT = { HIGH: 'red', MEDIUM: 'yellow', MIXED: 'blue', LOW: 'green' }
const RISK_DARK    = {
  HIGH:   'bg-red-950 text-red-300 border border-red-800',
  MEDIUM: 'bg-amber-950 text-amber-300 border border-amber-800',
  MIXED:  'bg-blue-950 text-blue-300 border border-blue-800',
  LOW:    'bg-emerald-950 text-emerald-300 border border-emerald-800',
}
const CONF_STYLE = {
  High:   'bg-emerald-50 text-emerald-700',
  Medium: 'bg-amber-50 text-amber-700',
  Low:    'bg-slate-100 text-slate-500',
}

// ── Report dataset — 5 priority-market briefs ──────────────────────────────────

const REPORTS = [
  {
    id: 'uae-vasp-readiness',
    flag: '🇦🇪',
    market: 'UAE',
    source: 'VARA / CBUAE / UAE FIU',
    risk: 'HIGH',
    title: 'UAE VASP Source Readiness Review',
    audience: ['VASPs', 'Crypto exchanges', 'Fintech legal teams', 'Compliance teams'],
    summary: 'Sample readiness review for UAE virtual asset source layers, with activation dependent on proof/diff validation.',
    date: 'Sample',
    sourceUrl: 'vara.ae / centralbank.ae / uaefiu.gov.ae',
    executive: 'Sample preview showing how StatuteProof summarizes UAE VASP source readiness across VARA, CBUAE and UAE FIU layers. It is not a live monitoring report.',
    keyUpdate: 'Mapped source layers are grouped by validation state. Only validated sources enter monitoring profiles after proof/diff checks and limitations review.',
    whyMatters: 'VASP, crypto and AML teams need a clear source map before relying on regulatory monitoring outputs.',
    steps: [
      'Review mapped VARA, CBUAE and UAE FIU source layers',
      'Confirm which sources are validated, under validation or limited',
      'Document limitations before any pilot activation',
      'Use the sample as a readiness review, not legal advice',
    ],
    evidence: { sourceHealth: 'Readiness snapshot', changeType: 'Sample source map', aiConfidence: 'High', note: 'Sample preview only.' },
  },
  {
    id: 'cbuae-aml-preview',
    flag: '🇦🇪',
    market: 'UAE',
    source: 'CBUAE / UAE FIU / MoET AML',
    risk: 'MEDIUM',
    title: 'CBUAE / AML Brief Preview',
    audience: ['Banks', 'Payment institutions', 'Fintech companies', 'AML teams'],
    summary: 'Sample reviewed brief format for UAE AML/CFT source layers relevant to regulated financial teams.',
    date: 'Sample',
    sourceUrl: 'centralbank.ae / uaefiu.gov.ae / moec.gov.ae',
    executive: 'Sample preview showing how an AML/CFT update would be framed with source proof, profile relevance and a human review gate.',
    keyUpdate: 'A CBUAE or UAE FIU source layer is shown in sample format. Activation still requires source extraction validation.',
    whyMatters: 'Banks, payment providers and MLRO teams need source-backed review steps without treating sample content as live delivery.',
    steps: [
      'Review the official UAE AML/CFT source layer',
      'Confirm extraction readiness before activation',
      'Map the update to internal AML controls',
      'Escalate to compliance review before implementation',
    ],
    evidence: { sourceHealth: 'Under validation', changeType: 'Sample brief preview', aiConfidence: 'Medium', note: 'Human review required.' },
  },
  {
    id: 'dfsa-transparency',
    flag: '🇦🇪',
    market: 'DIFC',
    source: 'DFSA / DIFC Laws',
    risk: 'MEDIUM',
    title: 'DIFC / DFSA Source Transparency Report',
    audience: ['DIFC firms', 'Fund managers', 'Legal teams', 'Compliance teams'],
    summary: 'Source transparency sample for DIFC Laws, DFSA rulebook and DFSA consultation layers.',
    date: 'Sample',
    sourceUrl: 'dfsa.ae / difc.ae',
    executive: 'Sample report showing which DIFC / DFSA source layers are validated, under validation or limited for a pilot profile.',
    keyUpdate: 'The report separates mapped sources from validated sources and documents limitations near each source layer.',
    whyMatters: 'DIFC-regulated firms need clear source provenance before using any alert workflow.',
    steps: [
      'Review DFSA rulebook and consultation source layers',
      'Check DIFC Laws validation state',
      'Flag WAF or mirror limitations if present',
      'Confirm pilot scope before activation',
    ],
    evidence: { sourceHealth: 'Validated + under validation', changeType: 'Source transparency sample', aiConfidence: 'Medium', note: null },
  },
  {
    id: 'adgm-fsra-preview',
    flag: '🇦🇪',
    market: 'ADGM',
    source: 'ADGM / FSRA',
    risk: 'MEDIUM',
    title: 'ADGM / FSRA Circulars Preview',
    audience: ['ADGM firms', 'Financial services teams', 'Legal teams', 'Compliance teams'],
    summary: 'Sample preview for ADGM / FSRA publications and circular source layers.',
    date: 'Sample',
    sourceUrl: 'adgm.com',
    executive: 'Sample brief showing how ADGM / FSRA circulars would be reviewed with source proof and limitation notes.',
    keyUpdate: 'A circular source layer is shown as a readiness snapshot, not a live monitored update.',
    whyMatters: 'ADGM firms need documented proof/diff validation before depending on monitoring output.',
    steps: [
      'Review ADGM / FSRA publication layer',
      'Confirm row extraction or item-level validation',
      'Document limitations before pilot use',
      'Use the preview for internal readiness review',
    ],
    evidence: { sourceHealth: 'Under validation', changeType: 'Readiness snapshot', aiConfidence: 'Medium', note: 'Requires pilot setup.' },
  },
  {
    id: 'proof-diff-sample',
    flag: '🇦🇪',
    market: 'UAE',
    source: 'UAE source layers',
    risk: 'MIXED',
    title: 'Proof/Diff Artifact Sample',
    audience: ['Compliance teams', 'Legal firms', 'Payment providers', 'Consultants'],
    summary: 'Sample artifact showing how source proof, diff evidence and limitations are packaged for a pilot review.',
    date: 'Sample',
    sourceUrl: 'Official UAE source links',
    executive: 'Sample artifact for a UAE-first pilot workspace. It shows source proof format, not production delivery.',
    keyUpdate: 'Validated, under-validation, limited and blocked statuses are disclosed separately so mapped sources are not confused with active monitoring.',
    whyMatters: 'Buyer trust depends on clear limitations and source evidence before any pilot activation.',
    steps: [
      'Review the readiness status for each UAE source layer',
      'Check source proof and extraction limitations',
      'Agree pilot watchlist scope',
      'Activate only validated sources after proof/diff checks',
    ],
    evidence: { sourceHealth: 'Readiness snapshot', changeType: 'Proof/diff sample', aiConfidence: 'Medium', note: 'No production delivery implied.' },
  },
]
// ── Component ──────────────────────────────────────────────────────────────────

export default function SampleReports() {
  const [selectedId, setSelectedId] = useState('uae-vasp')
  const report = REPORTS.find(r => r.id === selectedId)

  return (
    <section className="py-20 bg-slate-50" id="sample-reports">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="text-center mb-12">
          <Badge variant="blue" className="mb-4">Sample Reports</Badge>
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            See the briefs your team would receive
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Explore sample regulatory briefs generated from monitored official sources — with risk levels,
            AI-assisted summaries, affected organizations, suggested review steps and source-level proof.
          </p>
        </div>

        {/* ── Main: card list + preview panel ────────────────────────────── */}
        <div className="grid lg:grid-cols-[288px_1fr] gap-6 mb-10">

          {/* ── Card list ─────────────────────────────────────────────────── */}
          <div className="space-y-3">
            {REPORTS.map(r => (
              <button
                key={r.id}
                onClick={() => setSelectedId(r.id)}
                className={`w-full text-left rounded-xl border p-4 transition-all ${
                  selectedId === r.id
                    ? 'border-blue-300 bg-white shadow-md ring-1 ring-blue-100'
                    : 'border-slate-200 bg-white hover:shadow-sm hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl leading-none">{r.flag}</span>
                    <span className="text-xs text-slate-500 leading-tight">{r.market}</span>
                  </div>
                  <Badge variant={RISK_VARIANT[r.risk]}>{r.risk}</Badge>
                </div>

                <p className="text-sm font-semibold text-slate-800 leading-snug mb-1">
                  {r.title}
                </p>
                <p className="text-xs text-slate-400 mb-2">{r.source}</p>

                <div className="flex flex-wrap gap-1">
                  {r.audience.slice(0, 2).map(a => (
                    <span key={a} className="text-xs bg-slate-50 border border-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                      {a}
                    </span>
                  ))}
                  {r.audience.length > 2 && (
                    <span className="text-xs text-slate-400 py-0.5">+{r.audience.length - 2}</span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* ── Preview panel ──────────────────────────────────────────────── */}
          <div className="bg-slate-900 rounded-2xl overflow-hidden border border-slate-700 shadow-xl flex flex-col min-h-[580px]">

            {/* Panel chrome */}
            <div className="bg-slate-800 px-5 py-3.5 flex items-center justify-between border-b border-slate-700 flex-shrink-0">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
                  Compliance Brief
                </span>
              </div>
              <span className="text-xs text-slate-500">{report.date}</span>
            </div>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-800">

              {/* Title row */}
              <div className="px-5 pt-4 pb-4">
                <div className="flex items-center gap-2.5 flex-wrap mb-3">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${RISK_DARK[report.risk]}`}>
                    {report.risk}
                  </span>
                  <span className="text-xs text-slate-400">{report.flag} {report.market}</span>
                  <span className="text-xs bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-full">
                    {report.source}
                  </span>
                </div>
                <h3 className="text-white font-semibold text-base leading-snug">{report.title}</h3>
              </div>

              {/* Executive summary */}
              <div className="px-5 py-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Executive Summary</p>
                <p className="text-slate-300 text-xs leading-relaxed">{report.executive}</p>
              </div>

              {/* Key update */}
              <div className="px-5 py-4">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-2">What Changed</p>
                <p className="text-slate-300 text-xs leading-relaxed">{report.keyUpdate}</p>
              </div>

              {/* Why it matters */}
              <div className="px-5 py-4">
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wide mb-2">Why It Matters</p>
                <p className="text-slate-300 text-xs leading-relaxed">{report.whyMatters}</p>
              </div>

              {/* Audience + Review steps */}
              <div className="px-5 py-4 grid sm:grid-cols-2 gap-5">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Affected Organizations</p>
                  <div className="flex flex-wrap gap-1.5">
                    {report.audience.map(a => (
                      <span key={a} className="text-xs bg-slate-800 text-slate-300 border border-slate-700 px-1.5 py-0.5 rounded-full">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-2">Suggested Review Steps</p>
                  <ol className="space-y-1.5">
                    {report.steps.map((s, i) => (
                      <li key={i} className="flex gap-2 text-xs text-slate-300 leading-relaxed">
                        <span className="text-emerald-500 font-semibold flex-shrink-0">{i + 1}.</span>
                        {s}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>

              {/* Deadline + AI confidence + Review required */}
              <div className="px-5 py-4 grid sm:grid-cols-3 gap-4">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Deadline</p>
                  <p className="text-xs text-slate-400 italic">Not specified in demo data</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">AI Confidence</p>
                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${CONF_STYLE[report.evidence.aiConfidence]}`}>
                    {report.evidence.aiConfidence}
                  </span>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Human Review</p>
                  <p className="text-xs text-amber-300">Yes — recommended</p>
                </div>
              </div>

              {/* Evidence trail */}
              <div className="px-5 py-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Evidence Trail</p>
                <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
                  {[
                    { ok: report.evidence.sourceHealth === 'PASS', label: 'Source health', value: report.evidence.sourceHealth },
                    { ok: true, label: 'Change type', value: report.evidence.changeType },
                  ].map(({ ok, label, value }) => (
                    <div key={label} className="flex items-start gap-2">
                      <span className={`text-xs font-bold flex-shrink-0 ${ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {ok ? '✓' : '~'}
                      </span>
                      <div>
                        <p className="text-xs text-slate-500">{label}</p>
                        <p className="text-xs text-slate-300 font-medium">{value}</p>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-bold text-emerald-400 flex-shrink-0">✓</span>
                    <div>
                      <p className="text-xs text-slate-500">AI confidence</p>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${CONF_STYLE[report.evidence.aiConfidence]}`}>
                        {report.evidence.aiConfidence}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <ExternalLink className="w-3 h-3 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-500">Official source</p>
                      <p className="text-xs text-blue-400">{report.sourceUrl}</p>
                    </div>
                  </div>
                </div>

                {report.evidence.note && (
                  <div className="mt-3 flex items-start gap-2 bg-amber-950/40 border border-amber-800 rounded-lg px-3 py-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-300 leading-relaxed">{report.evidence.note}</p>
                  </div>
                )}
              </div>

              {/* Disclaimer strip */}
              <div className="px-5 py-3 bg-slate-800/40 flex items-center gap-2 flex-shrink-0">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                <p className="text-xs text-slate-500">
                  This is sample demo data. Not legal advice. Verify against official sources and qualified counsel.
                </p>
              </div>

            </div>
          </div>
        </div>

        {/* ── CTA block ─────────────────────────────────────────────────────── */}
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-slate-50 px-8 py-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="max-w-md">
            <h3 className="text-lg font-bold text-slate-900 mb-2">
              Want a sample brief for your market?
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Tell us your target jurisdictions and source profile. We can prepare a pilot monitoring
              setup for your compliance team.
            </p>
            <p className="text-xs text-slate-400 mt-3">
              Sample reports use demonstration data and are not legal advice.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 flex-shrink-0">
            <button
              onClick={() => document.querySelector('#interactive-demo')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-5 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm whitespace-nowrap"
            >
              View Interactive Demo
            </button>
            <button
              onClick={() => document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' })}
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-colors shadow-sm whitespace-nowrap"
            >
              Request Early Access
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </section>
  )
}

import { useState, useEffect } from 'react'
import { CheckCircle, Download, ExternalLink, Brain } from 'lucide-react'
import { MOCK_ALERTS } from '../../data/appMockData'
import { getWorkspaceProfile, filterAlerts } from '../../data/workspaceProfile'

const RISK_DARK = {
  HIGH:   'text-red-400   bg-red-500/15   border border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border border-amber-500/30',
  LOW:    'text-emerald-400 bg-emerald-500/15 border border-emerald-500/30',
}

const CONF_COLOR = { High: 'text-emerald-400', Medium: 'text-amber-400', Low: 'text-red-400' }

export default function AIBriefPage() {
  const profile    = getWorkspaceProfile()
  const baseBriefs = filterAlerts(MOCK_ALERTS, profile)

  const [selectedId, setSelectedId] = useState(baseBriefs[0]?.id || 'a1')
  const [reviewed, setReviewed]     = useState(new Set())

  useEffect(() => {
    fetch('/api/briefs?market=AE', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        // When live briefs are available, they can be merged here.
        // Currently falls back silently to sample data.
        void data
      })
      .catch(() => {})
  }, [])

  const brief = baseBriefs.find(a => a.id === selectedId) || baseBriefs[0]

  return (
    <div className="p-5 flex flex-col h-full">
      <div className="mb-4">
        <h1 className="text-lg font-bold text-white mb-1">Reviewed Brief Previews</h1>
        <p className="text-sm text-slate-400">
          {profile.markets.length > 0
            ? `Reviewed brief previews for: ${profile.markets.join(', ')}`
            : 'Reviewed brief previews — select markets in Settings to filter.'}
        </p>
      </div>

      <div className="mb-4 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="mb-2">
              <span className="sp-demo-badge">SAMPLE / DEMO — not a real regulatory update</span>
            </div>
            <h2 className="text-sm font-semibold text-white">Brief structure preview</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Briefs are drafted from official source evidence and gated by human review before delivery.
              These examples show the brief structure only. Delivery requires an approved brief and integration setup.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Source proof', 'Human review gate', 'Limitation note', 'Delivery pending'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 grid lg:grid-cols-[300px_1fr] gap-4 min-h-0">

        {/* Left: brief list */}
        <div className="flex flex-col min-h-0 gap-2 overflow-y-auto">
          {baseBriefs.length === 0 && (
            <div className="text-center py-10 px-4">
              <p className="text-sm text-slate-400 mb-1">No briefs for your selected profile yet.</p>
              <p className="text-xs text-slate-600">Add more markets in Settings → Monitoring profile.</p>
            </div>
          )}
          {baseBriefs.map(a => (
            <button
              key={a.id}
              onClick={() => setSelectedId(a.id)}
              className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                selectedId === a.id
                  ? 'border-cyan-500/30 bg-slate-900 ring-1 ring-cyan-500/20'
                  : 'border-slate-800 bg-slate-900 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[a.risk]}`}>{a.risk}</span>
                <span className="text-xs text-slate-500">{a.date}</span>
              </div>
              <p className="text-xs font-semibold text-white leading-snug mb-1.5">{a.title}</p>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Brain className="w-3 h-3 text-cyan-500/60" />
              <span>Sample draft confidence: <span className={CONF_COLOR[a.aiConfidence]}>{a.aiConfidence}</span></span>
              </div>
              {reviewed.has(a.id) && (
                <div className="mt-2 flex items-center gap-1 text-emerald-400 text-xs">
                  <CheckCircle className="w-3 h-3" /> Reviewed
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Right: brief detail */}
        <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl flex flex-col min-h-0 overflow-hidden">

          {/* Header */}
          <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <Brain className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-semibold text-white">Sample Brief Preview</span>
              <span className="sp-demo-badge">SAMPLE / DEMO</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[brief.risk]}`}>{brief.risk}</span>
            </div>
            <span className="text-xs text-slate-500">{brief.date}</span>
          </div>

          {/* Scrollable body */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800 text-xs">

            {/* Title + Source */}
            <div className="px-5 py-4">
              <p className="text-slate-500 text-xs mb-1">{brief.flag} {brief.market} · {brief.source}</p>
              <h3 className="text-sm font-semibold text-white mb-3">{brief.title}</h3>
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-1.5">What changed</p>
              <p className="text-slate-300 leading-relaxed">{brief.summary}</p>
            </div>

            {/* What Changed */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-1.5">What Changed</p>
              <p className="text-slate-300 leading-relaxed">{brief.keyUpdate}</p>
            </div>

            {/* Why It Matters */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-1.5">Why It Matters</p>
              <p className="text-slate-300 leading-relaxed">{brief.whyMatters}</p>
            </div>

            {/* Affected */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Who may be affected</p>
              <div className="flex flex-wrap gap-1.5">
                {brief.affected.map(e => (
                  <span key={e} className="bg-slate-800 border border-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{e}</span>
                ))}
              </div>
            </div>

            {/* Required Action */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Suggested internal review</p>
              <ol className="space-y-1.5">
                {brief.steps.map((s, i) => (
                  <li key={i} className="flex gap-2 text-slate-300 leading-relaxed">
                    <span className="text-cyan-400 font-semibold flex-shrink-0">{i + 1}.</span>
                    {s}
                  </li>
                ))}
              </ol>
            </div>

            {/* Metadata grid */}
            <div className="px-5 py-4 grid sm:grid-cols-3 gap-4">
              {[
                { label: 'Deadline',       value: brief.deadline },
                { label: 'Urgency',        value: brief.urgency },
                { label: 'Materiality',    value: brief.materiality },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">{label}</p>
                  <p className="text-slate-200 font-medium">{value}</p>
                </div>
              ))}
            </div>

            {/* AI metadata */}
            <div className="px-5 py-4 grid sm:grid-cols-2 gap-4">
              <div>
                <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Draft Confidence</p>
                <p className={`font-semibold ${CONF_COLOR[brief.aiConfidence]}`}>{brief.aiConfidence}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Human Review Gate</p>
                <p className={`font-semibold ${brief.reviewRequired ? 'text-amber-400' : 'text-slate-400'}`}>
                  {brief.reviewRequired ? 'Required' : 'Not required'}
                </p>
              </div>
              {brief.reviewRequired && brief.reviewReason && (
                <div className="sm:col-span-2">
                  <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">Review Reason</p>
                  <p className="text-slate-400">{brief.reviewReason}</p>
                </div>
              )}
            </div>

            {/* Source proof */}
            <div className="px-5 py-4">
              <p className="text-slate-500 uppercase tracking-wide font-medium mb-2">Source proof</p>
              {['Reviewed sample', 'Official source link available', 'Human review gate', 'Limitation disclosed'].map(e => (
                <div key={e} className="flex items-center gap-1.5 text-slate-400 mb-1">
                  <span className="text-emerald-400 font-bold">✓</span> {e}
                </div>
              ))}
              <div className="flex items-center gap-1.5 text-slate-500 mt-2">
                <ExternalLink className="w-3 h-3" />
                <span>Official source: {brief.sourceUrl}</span>
              </div>
            </div>

            {/* Limitation note */}
            <div className="px-5 py-4 bg-slate-800/30">
              <p className="text-slate-500 text-xs leading-relaxed">
                {brief.limitationNote || 'SAMPLE / DEMO — not a real regulatory update. Real client delivery requires evidence records, approved routing, profile matching, integration setup, and human review.'}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="px-5 py-3.5 border-t border-slate-800 flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => setReviewed(prev => new Set([...prev, brief.id]))}
              disabled={reviewed.has(brief.id)}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border transition-colors ${
                reviewed.has(brief.id)
                  ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10'
                  : 'border-slate-700 text-slate-300 hover:border-slate-600 hover:text-white'
              }`}
            >
              <CheckCircle className="w-3.5 h-3.5" />
              {reviewed.has(brief.id) ? 'Reviewed' : 'Mark reviewed'}
            </button>
            <button
              type="button"
              disabled
              className="flex items-center gap-1.5 text-xs font-medium text-slate-500 border border-slate-700 bg-slate-800/70 px-3 py-2 rounded-lg cursor-not-allowed"
              title="PDF export requires activation."
            >
              <Download className="w-3.5 h-3.5" />
              PDF export requires activation
            </button>
            <button
              type="button"
              disabled
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-slate-700 bg-slate-800/70 text-slate-500 cursor-not-allowed"
              title="Delivery requires approved brief and integration setup."
            >
              Preview only
            </button>
            <span className="text-xs text-slate-500">Delivery requires approved brief and integration setup.</span>
          </div>

          {/* Mandatory legal disclaimer per brief */}
          <div className="px-5 py-3 border-t border-slate-800 bg-slate-950/40">
            <p className="text-[10px] text-slate-600 leading-relaxed">
              <strong className="text-slate-500">Not legal advice.</strong> StatuteProof reports are generated from monitored official-source records and are provided
              for information and compliance review support only. They do not constitute legal advice, regulatory advice,
              compliance determination, or a legal opinion. Users should verify official source material directly
              and consult qualified legal or compliance professionals before making regulatory decisions.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

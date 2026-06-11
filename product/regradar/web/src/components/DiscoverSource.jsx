import { useState } from 'react'
import { Search, Loader2, CheckCircle, AlertTriangle, XCircle, ExternalLink } from 'lucide-react'

const QUALITY_COLORS = {
  excellent:   'text-emerald-600 bg-emerald-50 border-emerald-200',
  good:        'text-emerald-600 bg-emerald-50 border-emerald-200',
  acceptable:  'text-amber-600 bg-amber-50 border-amber-200',
  weak:        'text-orange-600 bg-orange-50 border-orange-200',
  unusable:    'text-red-600 bg-red-50 border-red-200',
}

const VERDICT_ICON = {
  can_monitor:    <CheckCircle className="w-5 h-5 text-emerald-500" />,
  limited:        <AlertTriangle className="w-5 h-5 text-amber-500" />,
  cannot_monitor: <XCircle className="w-5 h-5 text-red-500" />,
}

function ScoreBar({ score }) {
  const pct = Math.min(100, Math.max(0, score))
  const color = score >= 65 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : score >= 35 ? 'bg-orange-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-semibold tabular-nums w-12 text-right">{score}/100</span>
    </div>
  )
}

function ResultCard({ result }) {
  if (!result) return null
  const qColor = QUALITY_COLORS[result.qualityLabel] ?? QUALITY_COLORS.unusable
  const icon = VERDICT_ICON[result.verdict] ?? VERDICT_ICON.cannot_monitor

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-100">
        {icon}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-900 truncate">{result.bestMonitoringUrl}</p>
          <p className="text-xs text-slate-500 mt-0.5">{result.reason}</p>
        </div>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${qColor}`}>
          {result.qualityLabel?.toUpperCase()}
        </span>
      </div>

      {/* Score */}
      <div className="px-5 py-4 border-b border-slate-100">
        <p className="text-xs font-medium text-slate-500 mb-2">Quality Score</p>
        <ScoreBar score={result.qualityScore} />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-slate-100">
        {[
          { label: 'Extracted', value: result.extractedChars?.toLocaleString() + 'c' },
          { label: 'Status', value: result.recommendedStatus },
          { label: 'Method', value: result.connectionMethod },
          { label: 'Language', value: result.language ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white px-4 py-3">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-sm font-medium text-slate-800 mt-0.5 truncate">{value}</p>
          </div>
        ))}
      </div>

      {/* Structural signals */}
      {(result.rssFeedsFound > 0 || result.sitemapsFound > 0 || result.documentsFound > 0 || result.apiEndpointsFound > 0) && (
        <div className="px-5 py-3 border-t border-slate-100 flex flex-wrap gap-2">
          {result.rssFeedsFound > 0 && <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">RSS ×{result.rssFeedsFound}</span>}
          {result.sitemapsFound > 0 && <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">Sitemap ×{result.sitemapsFound}</span>}
          {result.documentsFound > 0 && <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">Docs ×{result.documentsFound}</span>}
          {result.apiEndpointsFound > 0 && <span className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">API ×{result.apiEndpointsFound}</span>}
        </div>
      )}

      {/* Limitations */}
      {result.limitations?.length > 0 && (
        <div className="px-5 py-3 border-t border-slate-100">
          <p className="text-xs font-medium text-slate-500 mb-1">Limitations</p>
          {result.limitations.map((l, i) => (
            <p key={i} className="text-xs text-slate-600">• {l}</p>
          ))}
        </div>
      )}

      {/* Next steps */}
      {result.nextSteps?.length > 0 && (
        <div className="px-5 py-3 border-t border-slate-100 bg-slate-50">
          <p className="text-xs font-medium text-slate-500 mb-1">Next Steps</p>
          {result.nextSteps.map((s, i) => (
            <p key={i} className="text-xs text-slate-600">→ {s}</p>
          ))}
        </div>
      )}

      {/* Open URL */}
      <div className="px-5 py-3 border-t border-slate-100 flex justify-end">
        <a
          href={result.bestMonitoringUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800"
        >
          Open source <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  )
}

export default function DiscoverSource({ demoResult = null, compact = false }) {
  const [url, setUrl] = useState(demoResult?.submittedUrl ?? '')
  const [jurisdiction, setJurisdiction] = useState(demoResult?.jurisdiction ?? '')
  const [category, setCategory] = useState(demoResult?.category ?? '')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(demoResult)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const params = new URLSearchParams({ url: url.trim() })
      if (jurisdiction) params.set('jurisdiction', jurisdiction)
      if (category) params.set('category', category)

      const res = await fetch(`/api/discover-source?${params}`)
      if (!res.ok) {
        const msg = await res.text()
        throw new Error(msg || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const inner = (
    <div className={compact ? '' : 'max-w-2xl mx-auto'}>
      {!compact && (
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Add Your Own Source</h2>
          <p className="text-slate-500 mt-2 text-sm">
            Submit any regulatory URL — StatuteProof analyses it and tells you how well it can be monitored.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Source URL *</label>
            <input
              type="url"
              required
              placeholder="https://regulator.gov.xx/publications"
              value={url}
              onChange={e => setUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Jurisdiction (optional)</label>
              <input
                type="text"
                placeholder="e.g. AE, SG, KZ"
                maxLength={5}
                value={jurisdiction}
                onChange={e => setJurisdiction(e.target.value.toUpperCase())}
                className="w-full rounded-lg border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Category (optional)</label>
              <input
                type="text"
                placeholder="e.g. tax, aml, cyber"
                value={category}
                onChange={e => setCategory(e.target.value.toLowerCase())}
                className="w-full rounded-lg border border-slate-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {loading ? 'Analysing…' : 'Analyse Source'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <ResultCard result={result} />
      </div>
  )

  if (compact) return inner
  return <section className="py-16 px-4" id="add-source">{inner}</section>
}

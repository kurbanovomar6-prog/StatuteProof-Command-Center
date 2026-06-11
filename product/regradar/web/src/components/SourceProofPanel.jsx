import { ExternalLink, Shield } from 'lucide-react'
import { normalizeExternalUrl } from '../utils/url'

function ProofField({ label, value }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-xs text-slate-300">{value}</p>
    </div>
  )
}

function ConfidenceBadge({ confidence }) {
  const style =
    confidence === 'High'   ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
    confidence === 'Medium' ? 'bg-amber-500/15   text-amber-400   border-amber-500/30'   :
                              'bg-slate-500/15   text-slate-400   border-slate-500/30'
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${style}`}>
      {confidence || 'Medium'}
    </span>
  )
}

export function SourceProofPanel({ alert }) {
  const sp  = alert.sourceProof || {}
  const url = normalizeExternalUrl(sp.originalUrl || alert.sourceUrl || '')

  const name       = sp.officialSourceName || alert.source  || 'Official source'
  const type       = sp.sourceType         || 'Official public source'
  const jur        = sp.jurisdiction       || alert.market  || '—'
  const detection  = sp.detectionMethod    || 'Official-source monitoring'
  const extraction = sp.extractionMethod   || 'HTML/PDF extraction where available'
  const checked    = sp.lastChecked        || 'Demo timestamp'
  const confidence = sp.confidence         || 'Medium'
  const snippet    = sp.evidenceSnippet    || null
  const limits     = sp.limitations        || 'Coverage depends on source availability and access restrictions.'

  return (
    <div className="mt-3 bg-slate-900/60 border border-slate-700/50 rounded-xl p-4 space-y-3">

      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          Source Proof
        </p>
        <ConfidenceBadge confidence={confidence} />
      </div>

      <div className="grid grid-cols-2 gap-x-5 gap-y-2.5">
        <ProofField label="Official source"   value={name} />
        <ProofField label="Source type"       value={type} />
        <ProofField label="Jurisdiction"      value={jur} />
        <ProofField label="Last checked"      value={checked} />
        <ProofField label="Detection method"  value={detection} />
        <ProofField label="Extraction method" value={extraction} />
      </div>

      {snippet && (
        <div className="border-l-2 border-cyan-500/30 pl-3">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Evidence snippet</p>
          <p className="text-xs text-slate-400 italic leading-relaxed">{snippet}</p>
        </div>
      )}

      <div className="bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Known limitations</p>
        <p className="text-xs text-amber-400/80 leading-relaxed">{limits}</p>
      </div>

      <div className="pt-2.5 border-t border-slate-700/50 flex items-center justify-between gap-3">
        <p className="text-[10px] text-slate-600 leading-relaxed">
          StatuteProof provides early-warning regulatory intelligence for internal review, not counsel.
        </p>
        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition-colors whitespace-nowrap flex-shrink-0"
          >
            <ExternalLink className="w-3 h-3" />
            Open official source
          </a>
        ) : (
          <span className="text-xs text-slate-600 flex-shrink-0">Source URL unavailable in demo</span>
        )}
      </div>

    </div>
  )
}

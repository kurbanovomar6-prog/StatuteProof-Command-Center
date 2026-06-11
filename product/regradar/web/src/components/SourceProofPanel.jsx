import { ExternalLink, Shield, Copy, CheckCircle2, AlertTriangle, FileCode2, Clock } from 'lucide-react'
import { useState } from 'react'
import { normalizeExternalUrl } from '../utils/url'

function HashDisplay({ label, value }) {
  const [copied, setCopied] = useState(false)
  if (!value) return null
  const display = value.length > 16 ? `${value.slice(0, 8)}…${value.slice(-8)}` : value

  function handleCopy() {
    navigator.clipboard.writeText(value).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div>
      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">{label}</p>
      <div className="flex items-center gap-2">
        <code className="text-xs font-mono text-slate-300 bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 rounded">
          {display}
        </code>
        <button
          type="button"
          onClick={handleCopy}
          className="text-slate-500 hover:text-slate-300 transition-colors"
          title="Copy full hash"
        >
          {copied
            ? <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            : <Copy className="w-3 h-3" />
          }
        </button>
      </div>
    </div>
  )
}

function ProofField({ label, value }) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-xs text-slate-300">{value}</p>
    </div>
  )
}

export function SourceProofPanel({ alert }) {
  const sp  = alert.sourceProof || {}
  const url = normalizeExternalUrl(sp.originalUrl || alert.sourceUrl || '')

  const name        = sp.officialSourceName || alert.source  || 'Official source'
  const type        = sp.sourceType         || 'Official public source'
  const jur         = sp.jurisdiction       || alert.market  || '—'
  const detection   = sp.detectionMethod    || 'Official-source monitoring'
  const extraction  = sp.extractionMethod   || 'HTML/PDF extraction'
  const monitoredAt = sp.monitoredAt        || sp.lastChecked || 'Demo timestamp'
  const limits      = sp.limitations        || 'Coverage depends on source availability and access restrictions.'
  const snippet     = sp.evidenceSnippet    || null
  const newHash     = sp.newHash            || null
  const oldHash     = sp.oldHash            || null
  const diffAvail   = sp.diffAvailable      ?? (newHash && oldHash)
  const reviewReq   = sp.reviewRequired     ?? alert.reviewRequired ?? false
  const snapshotUrl = sp.snapshotUrl        || null
  const algo        = sp.hashAlgorithm      || 'SHA-256'
  const confidence  = sp.confidence         || 'Medium'
  const aiUsed      = sp.aiUsed             ?? false

  const confStyle =
    confidence === 'High'   ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
    confidence === 'Medium' ? 'bg-amber-500/15   text-amber-400   border-amber-500/30'   :
                              'bg-slate-500/15   text-slate-400   border-slate-500/30'

  return (
    <div className="mt-3 bg-slate-900/60 border border-slate-700/50 rounded-xl p-4 space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          Evidence Record
        </p>
        <div className="flex items-center gap-1.5">
          {reviewReq && (
            <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border bg-amber-500/15 text-amber-400 border-amber-500/30">
              <AlertTriangle className="w-2.5 h-2.5" />
              Human review required
            </span>
          )}
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${confStyle}`}>
            {confidence} confidence
          </span>
        </div>
      </div>

      {/* Timestamps + badges row */}
      <div className="flex flex-wrap items-center gap-2 pb-1">
        <span className="flex items-center gap-1 text-[10px] text-slate-400">
          <Clock className="w-3 h-3 text-slate-500" />
          {monitoredAt}
        </span>
        {diffAvail && (
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border bg-cyan-500/15 text-cyan-300 border-cyan-500/30">
            <FileCode2 className="w-2.5 h-2.5" />
            Diff available
          </span>
        )}
        <span className="text-[10px] text-slate-600 px-2 py-0.5 rounded-full border border-slate-800 bg-slate-900">
          {aiUsed ? '✅ AI-analyzed' : '📏 Rule-based'}
        </span>
      </div>

      {/* Hash fields — the core "proof" */}
      {(newHash || oldHash) && (
        <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3 space-y-3">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
            {algo} content fingerprint
          </p>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {newHash && <HashDisplay label="New hash (current)" value={newHash} />}
            {oldHash && <HashDisplay label="Previous hash" value={oldHash} />}
          </div>
          {newHash && oldHash && (
            <p className="text-[10px] text-emerald-400/80">
              ✓ Hash mismatch confirmed — change detected
            </p>
          )}
        </div>
      )}

      {/* Source metadata grid */}
      <div className="grid grid-cols-2 gap-x-5 gap-y-2.5">
        <ProofField label="Official source"   value={name} />
        <ProofField label="Source type"       value={type} />
        <ProofField label="Jurisdiction"      value={jur} />
        <ProofField label="Detection method"  value={detection} />
        <ProofField label="Extraction method" value={extraction} />
        <ProofField label="Hash algorithm"    value={algo} />
      </div>

      {/* Evidence snippet */}
      {snippet && (
        <div className="border-l-2 border-cyan-500/30 pl-3">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Evidence snippet</p>
          <p className="text-xs text-slate-400 italic leading-relaxed">{snippet}</p>
        </div>
      )}

      {/* Limitations */}
      <div className="bg-amber-500/5 border border-amber-500/15 rounded-lg px-3 py-2">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Known limitations</p>
        <p className="text-xs text-amber-400/80 leading-relaxed">{limits}</p>
      </div>

      {/* Footer links */}
      <div className="pt-1 border-t border-slate-700/50 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[10px] text-slate-600 leading-relaxed">
          StatuteProof provides early-warning regulatory intelligence for internal review, not counsel.
        </p>
        <div className="flex items-center gap-3 flex-shrink-0">
          {snapshotUrl && (
            <a
              href={normalizeExternalUrl(snapshotUrl)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              Snapshot
            </a>
          )}
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              Official source
            </a>
          ) : (
            <span className="text-xs text-slate-600">Source URL unavailable in demo</span>
          )}
        </div>
      </div>

    </div>
  )
}

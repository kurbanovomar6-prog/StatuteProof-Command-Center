import { Lock, ExternalLink, ShieldCheck } from 'lucide-react'

const STATUS_STYLES = {
  CHANGED:    'text-amber-200 bg-amber-400/10 border-amber-400/25',
  UNCHANGED:  'text-emerald-200 bg-emerald-400/10 border-emerald-400/25',
  FIRST_SEEN: 'text-blue-200 bg-blue-400/10 border-blue-400/25',
  ERROR:      'text-rose-200 bg-rose-400/10 border-rose-400/25',
}

export default function EvidenceCard({ record }) {
  if (!record) return null

  const statusStyle = STATUS_STYLES[record.change_status] || 'text-slate-300 bg-slate-800 border-slate-700'
  const chainOk     = record.proof_chain?.chain_verified ?? false
  const fullHash    = record.normalized_hash ?? ''
  const shortHash   = fullHash.length > 20 ? `${fullHash.slice(0, 20)}…${fullHash.slice(-8)}` : fullHash

  // Prefer an explicit UTC timestamp; fall back to run_at
  const rawTs    = record.proof_chain?.captured_at ?? record.run_at ?? ''
  const displayTs = rawTs ? `${rawTs.replace('T', ' ').slice(0, 19)} UTC` : '—'

  return (
    <div className="rounded-lg border border-slate-700 bg-[#0D1B2E] p-4 shadow-[0_18px_60px_rgba(0,0,0,0.25)]">

      {/* SAMPLE label */}
      {record._label && (
        <span className="mb-3 inline-flex rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
          SAMPLE / FAKE — not a real regulatory update
        </span>
      )}

      {/* Source header row */}
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="min-w-0">
          <span className="block text-xs font-mono text-slate-500 truncate">{record.source_id}</span>
          <h3 className="text-sm font-semibold text-white mt-0.5 leading-snug">{record.regulator}</h3>
          <span className="mt-1 text-[10px] text-slate-500">{record.jurisdiction}</span>
        </div>
        <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border ${statusStyle}`}>
          {record.change_status}
        </span>
      </div>

      {/* Chain status badge — prominent */}
      <div className={`flex items-center gap-2 rounded-lg border px-3 py-2 mb-4 ${
        chainOk
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-red-500/30 bg-red-500/10'
      }`}>
        <ShieldCheck className={`h-4 w-4 shrink-0 ${chainOk ? 'text-emerald-400' : 'text-red-400'}`} />
        <span className={`text-xs font-bold tracking-wide ${chainOk ? 'text-emerald-300' : 'text-red-300'}`}>
          {chainOk ? 'CHAIN INTACT' : 'CHAIN UNVERIFIED'}
        </span>
        <span className="ml-auto text-[10px] text-slate-500 font-mono">{displayTs}</span>
      </div>

      {/* SHA-256 hash — large monospace display */}
      <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-3 mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">SHA-256</span>
          <span className="text-[10px] text-slate-600">current hash</span>
        </div>
        {fullHash ? (
          <span className="font-mono text-xs text-emerald-300 break-all leading-relaxed">
            {fullHash}
          </span>
        ) : (
          <span className="font-mono text-xs text-slate-500 italic">hash not available</span>
        )}
      </div>

      {/* Quality + chars metadata */}
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 mb-4">
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2">
          <span className="text-slate-500 text-[10px] font-semibold uppercase tracking-wide">Quality</span>
          <div className="mt-0.5">{record.extraction_quality ?? '—'}</div>
        </div>
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2">
          <span className="text-slate-500 text-[10px] font-semibold uppercase tracking-wide">Chars</span>
          <div className="mt-0.5">{record.normalized_chars?.toLocaleString() ?? '—'}</div>
        </div>
      </div>

      {/* Diff excerpt if CHANGED */}
      {record.change_status === 'CHANGED' && record.diff_excerpt && (
        <div className="bg-amber-400/10 border border-amber-400/20 rounded p-2 text-xs text-amber-100 font-mono mb-4 break-all leading-relaxed">
          {record.diff_excerpt.slice(0, 200)}&hellip;
        </div>
      )}

      {/* Source URL with padlock */}
      {record.source_url && (
        <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/40 px-3 py-2">
          <Lock className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span className="font-mono text-xs text-blue-300 truncate flex-1">
            {record.source_url}
          </span>
          <ExternalLink className="h-3 w-3 text-slate-500 shrink-0" />
        </div>
      )}

    </div>
  )
}

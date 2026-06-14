const STATUS_STYLES = {
  CHANGED: 'text-amber-200 bg-amber-400/10 border-amber-400/25',
  UNCHANGED: 'text-emerald-200 bg-emerald-400/10 border-emerald-400/25',
  FIRST_SEEN: 'text-blue-200 bg-blue-400/10 border-blue-400/25',
  ERROR: 'text-rose-200 bg-rose-400/10 border-rose-400/25',
}

export default function EvidenceCard({ record }) {
  if (!record) return null
  const statusStyle = STATUS_STYLES[record.change_status] || 'text-slate-300 bg-slate-800 border-slate-700'

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0D1B2E] p-4 shadow-[0_18px_60px_rgba(0,0,0,0.25)]">
      {record._label && (
        <span className="mb-3 inline-flex rounded-md border border-amber-400/25 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
          SAMPLE / DEMO - not a real regulatory update
        </span>
      )}
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-mono text-slate-500">{record.source_id}</span>
          <h3 className="text-sm font-semibold text-white mt-0.5">{record.regulator}</h3>
        </div>
        <span className={`text-xs font-semibold px-2 py-1 rounded border ${statusStyle}`}>
          {record.change_status}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 mb-3">
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2"><span className="text-slate-500">Jurisdiction</span><br />{record.jurisdiction}</div>
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2"><span className="text-slate-500">Quality</span><br />{record.extraction_quality}</div>
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2"><span className="text-slate-500">Chars</span><br />{record.normalized_chars?.toLocaleString()}</div>
        <div className="rounded-md border border-slate-800 bg-slate-950/35 p-2"><span className="text-slate-500">Detected</span><br />{record.run_at?.slice(0, 10)}</div>
      </div>
      {record.change_status === 'CHANGED' && record.diff_excerpt && (
        <div className="bg-amber-400/10 border border-amber-400/20 rounded p-2 text-xs text-amber-100 font-mono mb-3">
          {record.diff_excerpt.slice(0, 200)}…
        </div>
      )}
      <div className="flex items-center gap-2 text-xs">
        <span className={`w-2 h-2 rounded-full ${record.proof_chain?.chain_verified ? 'bg-green-500' : 'bg-red-400'}`} />
        <span className="text-slate-500">
          {record.proof_chain?.chain_verified ? 'Hash verified' : 'Hash unverified'}
        </span>
        <span className="text-slate-300 mx-1">·</span>
        <span className="font-mono text-slate-400 truncate max-w-[140px]">{record.normalized_hash?.slice(0, 18)}…</span>
      </div>
    </div>
  )
}

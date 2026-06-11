import React from 'react';

const STATUS_STYLES = {
  CHANGED: 'text-amber-600 bg-amber-50 border-amber-200',
  UNCHANGED: 'text-green-700 bg-green-50 border-green-200',
  FIRST_SEEN: 'text-blue-700 bg-blue-50 border-blue-200',
  ERROR: 'text-red-700 bg-red-50 border-red-200',
};

export default function EvidenceCard({ record }) {
  if (!record) return null;
  const statusStyle = STATUS_STYLES[record.change_status] || 'text-slate-600 bg-slate-50 border-slate-200';

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-mono text-slate-500">{record.source_id}</span>
          <h3 className="text-sm font-semibold text-slate-800 mt-0.5">{record.regulator}</h3>
        </div>
        <span className={`text-xs font-semibold px-2 py-1 rounded border ${statusStyle}`}>
          {record.change_status}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 mb-3">
        <div><span className="text-slate-400">Jurisdiction</span><br />{record.jurisdiction}</div>
        <div><span className="text-slate-400">Quality</span><br />{record.extraction_quality}</div>
        <div><span className="text-slate-400">Chars</span><br />{record.normalized_chars?.toLocaleString()}</div>
        <div><span className="text-slate-400">Detected</span><br />{record.run_at?.slice(0, 10)}</div>
      </div>
      {record.change_status === 'CHANGED' && record.diff_excerpt && (
        <div className="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-800 font-mono mb-3">
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
  );
}

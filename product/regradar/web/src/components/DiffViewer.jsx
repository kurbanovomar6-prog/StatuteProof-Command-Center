import React from 'react';

export default function DiffViewer({ diffText, sourceId, detectedAt }) {
  if (!diffText) return null;

  const lines = diffText.split('\n');

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden shadow-sm">
      <div className="px-4 py-3 bg-slate-800 flex items-center justify-between">
        <span className="text-xs font-mono text-slate-300">{sourceId}</span>
        <span className="text-xs text-slate-400">{detectedAt}</span>
      </div>
      <div className="overflow-x-auto">
        <pre className="text-xs leading-5 p-4 bg-slate-900 text-slate-100 max-h-56 overflow-y-auto">
          {lines.map((line, i) => (
            <div
              key={i}
              className={
                line.startsWith('+') ? 'text-green-400' :
                line.startsWith('-') ? 'text-red-400' :
                'text-slate-400'
              }
            >
              {line || ' '}
            </div>
          ))}
        </pre>
      </div>
      <div className="px-4 py-2 bg-slate-50 text-xs text-slate-500 border-t border-slate-200">
        SHA-256 hash recorded · Human review required before any compliance action
      </div>
    </div>
  );
}

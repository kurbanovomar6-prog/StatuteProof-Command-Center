import React from 'react';

const SOURCES = [
  { source_id: 'AE-cbuae-homepage', regulator: 'CBUAE', jurisdiction: 'UAE', tier: 1, ready: true },
  { source_id: 'AE-vara-framework', regulator: 'VARA', jurisdiction: 'Dubai', tier: 1, ready: true },
  { source_id: 'AE-dfsa-rules', regulator: 'DFSA', jurisdiction: 'DIFC', tier: 1, ready: true },
  { source_id: 'AE-adgm-fsra-regulations', regulator: 'ADGM FSRA', jurisdiction: 'Abu Dhabi', tier: 1, ready: true },
  { source_id: 'AE-difc-laws-homepage', regulator: 'DIFC', jurisdiction: 'DIFC', tier: 1, ready: true },
  { source_id: 'AE-mof-homepage', regulator: 'UAE Ministry of Finance', jurisdiction: 'UAE', tier: 2, ready: true },
  { source_id: 'AE-uae-legislation', regulator: 'UAE Legislation Portal', jurisdiction: 'UAE', tier: 2, ready: true },
  { source_id: 'AE-moe-homepage', regulator: 'UAE Ministry of Economy', jurisdiction: 'UAE', tier: 2, ready: true },
  { source_id: 'AE-uaefiu-homepage', regulator: 'UAEFIU', jurisdiction: 'UAE', tier: 3, ready: true },
  { source_id: 'AE-vara-enforcement', regulator: 'VARA', jurisdiction: 'Dubai', tier: 1, ready: false },
  { source_id: 'AE-cbuae-regulations', regulator: 'CBUAE', jurisdiction: 'UAE', tier: 1, ready: false },
  { source_id: 'AE-dfsa-notices', regulator: 'DFSA', jurisdiction: 'DIFC', tier: 1, ready: false },
  { source_id: 'AE-adgm-fsra-rules', regulator: 'ADGM FSRA', jurisdiction: 'Abu Dhabi', tier: 1, ready: false },
  { source_id: 'AE-difc-legislation', regulator: 'DIFC', jurisdiction: 'DIFC', tier: 1, ready: false },
  { source_id: 'AE-uaefiu-circulars', regulator: 'UAEFIU', jurisdiction: 'UAE', tier: 3, ready: false },
  { source_id: 'AE-sca-decisions', regulator: 'SCA', jurisdiction: 'UAE', tier: 3, ready: false },
];

const readyCount = SOURCES.filter(s => s.ready).length;

export default function SourceCoverageTable() {
  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">UAE Source Coverage</h3>
        <span className="text-xs text-slate-500">{readyCount}/{SOURCES.length} sources ready</span>
      </div>
      <div className="overflow-y-auto max-h-72">
        <table className="w-full text-xs">
          <thead className="sticky top-0">
            <tr className="bg-slate-50 text-slate-500">
              <th className="px-4 py-2 text-left font-medium">Source</th>
              <th className="px-4 py-2 text-left font-medium">Jurisdiction</th>
              <th className="px-4 py-2 text-left font-medium">Tier</th>
              <th className="px-4 py-2 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {SOURCES.map(s => (
              <tr key={s.source_id} className="hover:bg-slate-50">
                <td className="px-4 py-2">
                  <div className="font-medium text-slate-800">{s.regulator}</div>
                  <div className="text-slate-400 font-mono text-xs">{s.source_id}</div>
                </td>
                <td className="px-4 py-2 text-slate-600">{s.jurisdiction}</td>
                <td className="px-4 py-2 text-slate-600">Tier {s.tier}</td>
                <td className="px-4 py-2">
                  {s.ready
                    ? <span className="text-green-700 bg-green-50 px-2 py-0.5 rounded text-xs font-medium">READY</span>
                    : <span className="text-slate-400 bg-slate-100 px-2 py-0.5 rounded text-xs font-medium">PENDING</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 border-t border-slate-100 text-xs text-slate-400">
        Pending sources have no baseline run yet and are not available for monitoring.
      </div>
    </div>
  );
}

/**
 * EvidencePage — SAMPLE / FAKE demonstration data only.
 *
 * No /api/evidence endpoint exists in the current backend.
 * All records shown here are sample data for interface demonstration.
 * Evidence records support compliance review and do not determine legal obligations.
 */
import { useEffect, useState } from 'react'
import { Shield, Clock, Hash, FileText, AlertTriangle } from 'lucide-react'

const SAMPLE_EVIDENCE_RECORDS = [
  {
    evidence_record_id: 'EVR-2026-AE-001',
    source:             'VARA Regulatory Framework',
    source_id:          'AE-dubai-virtual-assets-regulatory-authority-vara',
    regulator:          'VARA',
    detected_at:        '2026-06-10T09:14:22Z',
    run_id:             'RUN-20260610-091422-AE',
    status:             'CHANGED',
    old_hash:           'sha256:a3f8d9c2b1e4f7a0',
    new_hash:           'sha256:7b1e4a8f3c2d9e01',
    diff_available:     true,
    proof_block:        { chain_verified: false },
    review_status:      'NEEDS_REVIEW',
    official_url:       'https://www.vara.ae/en/regulatory-framework/',
    risk:               'HIGH',
    affected:           'VASP / MLRO / Compliance teams',
  },
  {
    evidence_record_id: 'EVR-2026-AE-002',
    source:             'CBUAE Regulations',
    source_id:          'AE-cbuae-regulations',
    regulator:          'CBUAE',
    detected_at:        '2026-06-09T14:33:01Z',
    run_id:             'RUN-20260609-143301-AE',
    status:             'UNCHANGED',
    old_hash:           'sha256:c5d8f1a2b9e4c3d7',
    new_hash:           'sha256:c5d8f1a2b9e4c3d7',
    diff_available:     false,
    proof_block:        { chain_verified: false },
    review_status:      'NO_ACTION',
    official_url:       'https://www.centralbank.ae/en/regulations/',
    risk:               'LOW',
    affected:           'Banks / Payment firms',
  },
  {
    evidence_record_id: 'EVR-2026-AE-003',
    source:             'DFSA Rules and Standards',
    source_id:          'AE-dubai-financial-services-authority-dfsa',
    regulator:          'DFSA',
    detected_at:        '2026-06-08T10:55:18Z',
    run_id:             'RUN-20260608-105518-AE',
    status:             'FIRST_SEEN',
    old_hash:           null,
    new_hash:           'sha256:9e2b6c4a7d1f8e05',
    diff_available:     false,
    proof_block:        { chain_verified: false },
    review_status:      'NEEDS_REVIEW',
    official_url:       'https://www.dfsa.ae/rules-and-standards',
    risk:               'MEDIUM',
    affected:           'DIFC-authorised firms',
  },
]

const STATUS_STYLES = {
  CHANGED:     { bg: 'bg-blue-500/10 border-blue-500/30',       text: 'text-blue-400',    label: 'CHANGED' },
  UNCHANGED:   { bg: 'bg-slate-700/30 border-slate-600/30',     text: 'text-slate-400',   label: 'UNCHANGED' },
  FIRST_SEEN:  { bg: 'bg-violet-500/10 border-violet-500/30',   text: 'text-violet-400',  label: 'FIRST SEEN' },
  FAILED:      { bg: 'bg-red-500/10 border-red-500/30',         text: 'text-red-400',     label: 'FAILED' },
  QUALITY_DROP:{ bg: 'bg-amber-500/10 border-amber-500/30',     text: 'text-amber-400',   label: 'QUALITY DROP' },
}

const RISK_STYLES = {
  HIGH:   'text-red-400 bg-red-500/10 border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  LOW:    'text-slate-400 bg-slate-700/30 border-slate-600/30',
}

function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.UNCHANGED
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  )
}

function RiskBadge({ risk }) {
  const cls = RISK_STYLES[risk] || RISK_STYLES.LOW
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border ${cls}`}>
      {risk}
    </span>
  )
}

function EvidenceCard({ record }) {
  const detectedDate = record.detected_at
    ? new Date(record.detected_at).toLocaleString('en-GB', { timeZone: 'UTC', dateStyle: 'medium', timeStyle: 'short' }) + ' UTC'
    : '—'

  return (
    <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5 space-y-4">
      {/* Header row */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded">
              SAMPLE — NOT REAL REGULATORY DATA
            </span>
          </div>
          <h3 className="text-sm font-semibold text-white">{record.source}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{record.regulator} · {record.evidence_record_id}</p>
        </div>
        <div className="flex gap-2 items-center">
          <StatusBadge status={record.status} />
          <RiskBadge risk={record.risk} />
        </div>
      </div>

      {/* Fields */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Detected
          </p>
          <p className="text-slate-200 font-medium">{detectedDate}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5">Review status</p>
          <p className="text-slate-200 font-medium">{record.review_status}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5 flex items-center gap-1">
            <Hash className="w-3 h-3" /> Old hash
          </p>
          <p className="text-slate-400 font-mono truncate">{record.old_hash || 'N/A (first seen)'}</p>
        </div>
        <div className="bg-slate-900/50 rounded-lg px-3 py-2.5">
          <p className="text-slate-500 mb-0.5 flex items-center gap-1">
            <Hash className="w-3 h-3" /> New hash
          </p>
          <p className={`font-mono truncate ${record.status === 'CHANGED' ? 'text-blue-400' : 'text-slate-400'}`}>
            {record.new_hash || '—'}
          </p>
        </div>
      </div>

      {/* Affected + URL */}
      <div className="text-xs space-y-2">
        <div className="flex gap-2">
          <span className="text-slate-500 w-20 flex-shrink-0">Affected:</span>
          <span className="text-slate-300">{record.affected}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-slate-500 w-20 flex-shrink-0">Diff:</span>
          <span className={record.diff_available ? 'text-emerald-400' : 'text-slate-500'}>
            {record.diff_available ? 'Available' : 'Not available'}
          </span>
        </div>
        {record.official_url && (
          <div className="flex gap-2">
            <span className="text-slate-500 w-20 flex-shrink-0">Source:</span>
            <a
              href={record.official_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#16D9F5] hover:underline truncate"
            >
              {record.official_url}
            </a>
          </div>
        )}
      </div>

      {/* Legal note */}
      <p className="text-[10px] text-slate-600 border-t border-slate-800 pt-3">
        Not legal advice. Evidence records support compliance review and do not determine legal obligations.
      </p>
    </div>
  )
}

export default function EvidencePage() {
  const [records, setRecords] = useState(SAMPLE_EVIDENCE_RECORDS)

  useEffect(() => {
    fetch('/api/evidence?market=AE', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.records?.length) setRecords(data.records)
      })
      .catch(() => {}) // silent fallback to SAMPLE data
  }, [])

  return (
    <div className="p-5 space-y-5">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-white mb-1">Evidence Records</h1>
          <p className="text-sm text-slate-400">
            Detected source changes are cryptographically hashed, timestamped, and stored for human review.
          </p>
        </div>
        <span className="flex items-center gap-1.5 text-xs font-bold text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1.5 rounded-full flex-shrink-0">
          <AlertTriangle className="w-3.5 h-3.5" />
          SAMPLE DATA
        </span>
      </div>

      {/* Info banner */}
      <div className="bg-[#0D1B2E] border border-cyan-400/20 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-[#16D9F5] flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-sm font-semibold text-white mb-1">About evidence records</h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
              When StatuteProof detects a text change in a monitored official source, it records a cryptographic hash of
              the old and new content, timestamps the detection, and flags the record for human review. Evidence records
              support compliance review and do not determine legal obligations. Users should verify official source material
              directly before relying on any record.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                ['CHANGED', 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'],
                ['UNCHANGED', 'bg-slate-700/30 text-slate-400 border-slate-600/30'],
                ['FIRST SEEN', 'bg-blue-500/10 text-blue-400 border-blue-500/30'],
                ['FAILED', 'bg-red-500/10 text-red-400 border-red-500/30'],
                ['QUALITY DROP', 'bg-amber-500/10 text-amber-400 border-amber-500/30'],
              ].map(([label, cls]) => (
                <span key={label} className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cls}`}>
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Sample notice */}
      <div className="flex items-center gap-2 rounded-lg border border-amber-400/25 bg-amber-400/5 px-4 py-3">
        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
        <p className="text-xs text-amber-300">
          <strong>SAMPLE / FAKE — demonstration only.</strong> No live evidence API is currently connected.
          Records below are sample data for interface review. Not real regulatory data.
        </p>
      </div>

      {/* Evidence cards */}
      <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        {records.map(record => (
          <EvidenceCard key={record.evidence_record_id} record={record} />
        ))}
      </div>

      {/* Backend gap note */}
      <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
        <div className="flex items-start gap-3">
          <FileText className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-slate-500 leading-relaxed">
            <p className="font-medium text-slate-400 mb-1">Live evidence API not yet available</p>
            <p>
              A <code className="text-slate-400 bg-slate-800 px-1 rounded">GET /api/evidence</code> endpoint
              is not yet implemented in the backend. When implemented, this page will display real evidence records
              from monitoring runs. Evidence records support compliance review and do not determine legal obligations.
            </p>
          </div>
        </div>
      </div>

      <p className="text-xs text-slate-600 text-center leading-relaxed">
        StatuteProof reports are for information and compliance review support only. Not legal advice.
        Users should verify official source material directly and consult qualified professionals
        before making regulatory decisions.
      </p>
    </div>
  )
}

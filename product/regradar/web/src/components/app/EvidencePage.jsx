/**
 * EvidencePage — SAMPLE / FAKE demonstration data only.
 *
 * The page attempts to load /api/evidence and falls back to clearly
 * labeled sample data when no live evidence records are available.
 * Evidence records support compliance review and do not determine legal obligations.
 */
import { useEffect, useState } from 'react'
import { Shield, Clock, Hash, FileText, AlertTriangle } from 'lucide-react'

const SAMPLE_EVIDENCE_RECORDS = [
  {
    is_sample:          true,
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
    is_sample:          true,
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
    is_sample:          true,
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
  REVIEW: 'text-cyan-300 bg-cyan-400/10 border-cyan-400/25',
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
          {record.is_sample ? (
            <div className="flex items-center gap-2 mb-1">
              <span className="sp-demo-badge">
                SAMPLE / DEMO — not a real regulatory update
              </span>
            </div>
          ) : (
            <div className="mb-1 inline-flex rounded-md border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
              LIVE EVIDENCE RECORD
            </div>
          )}
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
  const [sampleMode, setSampleMode] = useState(true)
  const [apiChecked, setApiChecked] = useState(false)

  useEffect(() => {
    fetch('/api/evidence?market=AE', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (Array.isArray(data?.evidence)) {
          setSampleMode(false)
          setRecords(data.evidence.map((record, index) => ({
            evidence_record_id: record.run_id || `EVR-LIVE-${index + 1}`,
            source: record.source_name || record.source_id || 'Official source',
            source_id: record.source_id,
            regulator: record.category || 'AE source',
            detected_at: record.timestamp_utc,
            run_id: record.run_id,
            status: record.change_status || 'UNCHANGED',
            old_hash: null,
            new_hash: record.content_hash ? `sha256:${String(record.content_hash).slice(0, 16)}` : null,
            diff_available: record.change_status === 'CHANGED',
            proof_block: { chain_verified: false },
            review_status: record.change_status === 'CHANGED' || record.change_status === 'FIRST_SEEN' ? 'NEEDS_REVIEW' : 'NO_ACTION',
            official_url: '',
            risk: record.change_status === 'CHANGED' ? 'REVIEW' : 'LOW',
            affected: record.error || `Extraction quality: ${record.extraction_quality || 'UNKNOWN'}`,
            is_sample: false,
          })))
        }
      })
      .catch(() => {}) // silent fallback to SAMPLE data
      .finally(() => setApiChecked(true))
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
        <span className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full flex-shrink-0 ${
          sampleMode
            ? 'text-amber-400 bg-amber-400/10 border border-amber-400/20'
            : 'text-emerald-300 bg-emerald-400/10 border border-emerald-400/20'
        }`}>
          <AlertTriangle className="w-3.5 h-3.5" />
          {sampleMode ? 'SAMPLE DATA' : 'LIVE API'}
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
      {sampleMode ? (
        <div className="flex items-center gap-2 rounded-lg border border-amber-400/25 bg-amber-400/5 px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">
            <strong>SAMPLE / DEMO — demonstration only.</strong> Records below are sample data for interface review.
            Not real regulatory data.
          </p>
        </div>
      ) : records.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-10 text-center">
          <p className="font-medium text-slate-300">No evidence-backed brief available yet</p>
          <p className="mt-2 text-sm text-slate-500">
            Evidence records appear after monitored sources produce run records with hashes and timestamps.
          </p>
        </div>
      ) : null}

      {/* Evidence cards */}
      {records.length > 0 && (
      <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        {records.map((record, index) => (
          <EvidenceCard key={`${record.evidence_record_id}-${index}`} record={record} />
        ))}
      </div>
      )}

      {/* Backend gap note */}
      <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
        <div className="flex items-start gap-3">
          <FileText className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-slate-500 leading-relaxed">
            <p className="font-medium text-slate-400 mb-1">
              {sampleMode ? 'Sample mode enabled' : apiChecked ? 'Live evidence endpoint checked' : 'Checking evidence endpoint'}
            </p>
            <p>
              This page reads from <code className="text-slate-400 bg-slate-800 px-1 rounded">GET /api/evidence</code> when available.
              Sample records are displayed only when the endpoint is unavailable. Evidence records support compliance
              review and do not determine legal obligations.
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

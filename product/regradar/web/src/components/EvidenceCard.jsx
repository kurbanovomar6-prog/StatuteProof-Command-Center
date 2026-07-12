import { Lock, ExternalLink, Copy, Check } from 'lucide-react'
import { useState } from 'react'

// Status = meaning, not decoration: neutral chip + a single colored dot.
const STATUS_DOT = {
  CHANGED:    'var(--status-changed)',
  UNCHANGED:  'var(--success)',
  FIRST_SEEN: 'var(--status-changed)',
  ERROR:      'var(--risk-high)',
}

function middleTruncate(value, head = 10, tail = 10) {
  if (!value) return ''
  return value.length > head + tail + 1 ? `${value.slice(0, head)}…${value.slice(-tail)}` : value
}

export default function EvidenceCard({ record }) {
  const [hashCopied, setHashCopied] = useState(false)
  if (!record) return null

  const dotColor  = STATUS_DOT[record.change_status] || 'var(--text-muted)'
  const chainOk   = record.proof_chain?.chain_verified ?? false
  const fullHash  = record.normalized_hash ?? ''

  // Prefer an explicit UTC timestamp; fall back to run_at
  const rawTs     = record.proof_chain?.captured_at ?? record.run_at ?? ''
  const displayTs = rawTs ? `${rawTs.replace('T', ' ').slice(0, 19)} UTC` : '—'

  function copyHash() {
    if (!fullHash) return
    navigator.clipboard?.writeText(fullHash).catch(() => {})
    setHashCopied(true)
    setTimeout(() => setHashCopied(false), 1800)
  }

  return (
    <div className="sp-card p-4">

      {/* SAMPLE label — single caps category chip (legal-safety requirement) */}
      {record._label && (
        <span className="mb-3 inline-flex rounded-md border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 text-[12px] font-semibold uppercase tracking-wide text-[var(--warning)]">
          SAMPLE / FAKE — not a real regulatory update
        </span>
      )}

      {/* Source header row */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className="sp-mono block truncate text-[12px] text-[var(--text-muted)]">{record.source_id}</span>
          <h3 className="mt-0.5 text-[15px] font-semibold leading-snug text-[var(--text-primary)]">{record.regulator}</h3>
          <span className="mt-1 block text-[12px] text-[var(--text-secondary)]">{record.jurisdiction}</span>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-2.5 py-1 text-[12px] font-medium text-[var(--text-secondary)]">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: dotColor }} aria-hidden="true" />
          {record.change_status}
        </span>
      </div>

      {/* Notarial line — dot + plain statement, no red block */}
      <div className="mb-4 flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
        <span
          className="h-1.5 w-1.5 flex-shrink-0 rounded-full"
          style={{ background: chainOk ? 'var(--success)' : 'var(--risk-high)' }}
          aria-hidden="true"
        />
        <span>
          {chainOk ? 'Verified · SHA-256 match · ' : 'Chain unverified · '}
          <span className="sp-mono tabular-nums">{displayTs}</span>
        </span>
      </div>

      {/* SHA-256 — inset data field */}
      <div className="mb-4 rounded-[var(--radius-card)] border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2.5">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-[12px] text-[var(--text-muted)]">SHA-256 fingerprint</span>
          <span className="text-[12px] text-[var(--text-muted)]">current record</span>
        </div>
        {fullHash ? (
          <div className="flex items-center gap-2">
            <code className="sp-mono min-w-0 flex-1 truncate tabular-nums text-[12px] text-[var(--text-secondary)]" title={fullHash}>
              {middleTruncate(fullHash)}
            </code>
            <button
              type="button"
              onClick={copyHash}
              title="Copy full hash"
              className="flex-shrink-0 text-[var(--text-muted)] transition-colors hover:text-[var(--text-secondary)]"
            >
              {hashCopied ? <Check className="h-3.5 w-3.5 text-[var(--success)]" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        ) : (
          <span className="sp-mono text-[12px] text-[var(--text-muted)]">Hash not available</span>
        )}
      </div>

      {/* Quality + chars metadata */}
      <div className="mb-4 grid grid-cols-2 gap-2">
        <div className="rounded-[var(--radius-card)] border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2">
          <span className="text-[12px] text-[var(--text-muted)]">Quality</span>
          <div className="mt-0.5 text-[13px] text-[var(--text-primary)]">{record.extraction_quality ?? '—'}</div>
        </div>
        <div className="rounded-[var(--radius-card)] border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2">
          <span className="text-[12px] text-[var(--text-muted)]">Chars</span>
          <div className="mt-0.5 text-[13px] tabular-nums text-[var(--text-primary)]">{record.normalized_chars?.toLocaleString() ?? '—'}</div>
        </div>
      </div>

      {/* Diff excerpt if CHANGED */}
      {record.change_status === 'CHANGED' && record.diff_excerpt && (
        <div className="mb-4 rounded-[var(--radius-card)] border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
          <span className="mb-1.5 inline-flex items-center gap-1.5 rounded-full border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 text-[12px] font-medium text-[var(--status-changed)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--status-changed)]" aria-hidden="true" />
            Changed
          </span>
          <p className="sp-mono break-all text-[12px] leading-relaxed text-[var(--text-secondary)]">
            {record.diff_excerpt.slice(0, 200)}&hellip;
          </p>
        </div>
      )}

      {/* Source URL */}
      {record.source_url && (
        <div className="flex items-center gap-2 rounded-[var(--radius-card)] border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2">
          <Lock className="h-3.5 w-3.5 flex-shrink-0 text-[var(--text-muted)]" />
          <span className="sp-mono min-w-0 flex-1 truncate text-[12px] text-[var(--text-secondary)]">
            {record.source_url}
          </span>
          <ExternalLink className="h-3 w-3 flex-shrink-0 text-[var(--text-muted)]" />
        </div>
      )}

    </div>
  )
}

import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, FileCheck } from 'lucide-react'

import TimeStamp from './ui/TimeStamp'

/**
 * AlertProofPanel — binds a reviewed alert to its sealed evidence record.
 *
 * Renders a compact "View proof" affordance when the routing match carries a
 * `proof` block (evidence_record_id + record_hash self-seal + run_id), and an
 * honest empty state when it does not. "Proof" here means hash integrity of
 * the captured bytes only — never legal proof; the page-level disclaimer on
 * AlertsPage covers the legal framing.
 */

// Shorten "sha256:<64 hex>" for display; the full value stays in the title.
function shortHash(value) {
  const text = String(value || '')
  return text.length > 26 ? `${text.slice(0, 26)}…` : text
}

export default function AlertProofPanel({ item, navigate }) {
  const [open, setOpen] = useState(false)
  const proof = item?.proof

  if (!proof) {
    return (
      <p className="mt-3 text-[11px] text-[var(--text-muted)]">
        No sealed record is linked to this alert.
      </p>
    )
  }

  function handleOpenEvidence(event) {
    if (navigate) {
      event.preventDefault()
      navigate('evidence')
    }
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
      >
        <FileCheck className="h-3.5 w-3.5 text-[var(--accent)]" />
        View proof
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {open && (
        <div className="mt-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
          <p className="text-[11px] font-semibold text-[var(--text-primary)]">
            Sealed evidence record — re-check its hashes yourself.
          </p>

          <dl className="mt-2 space-y-1.5 text-[11px]">
            <div className="flex gap-2">
              <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">Record</dt>
              <dd
                className="min-w-0 truncate text-[var(--text-secondary)]"
                style={{ fontFamily: 'var(--font-mono)' }}
                title={proof.evidence_record_id}
              >
                {proof.evidence_record_id}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">Seal</dt>
              <dd
                className="min-w-0 truncate text-[var(--text-secondary)]"
                style={{ fontFamily: 'var(--font-mono)' }}
                title={proof.record_hash}
              >
                {shortHash(proof.record_hash)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">Captured</dt>
              <dd className="text-[var(--text-secondary)]">
                <TimeStamp value={item.detected_at} mode="absolute" fallback="Not recorded" />
              </dd>
            </div>
          </dl>

          {item.diff_excerpt ? (
            <div className="mt-3">
              <p className="text-[11px] text-[var(--text-muted)]">What changed (excerpt)</p>
              <p
                className="mt-1 max-h-28 overflow-y-auto whitespace-pre-wrap rounded-md border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-2.5 py-2 text-[11px] leading-relaxed text-[var(--text-secondary)]"
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                {item.diff_excerpt}
              </p>
            </div>
          ) : null}

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <a
              href="/app/evidence"
              onClick={handleOpenEvidence}
              className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[var(--accent)] transition-colors hover:text-[var(--text-primary)]"
            >
              <ExternalLink className="h-3 w-3" />
              Open evidence record
            </a>
            <a
              href="/verify"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[var(--accent)] transition-colors hover:text-[var(--text-primary)]"
            >
              <ExternalLink className="h-3 w-3" />
              Verify independently
            </a>
          </div>
          <p className="mt-1.5 text-[10px] leading-relaxed text-[var(--text-muted)]">
            Open the evidence record (or export its pack), then paste it into the public verifier to
            re-check its hashes yourself — without trusting us.
          </p>
        </div>
      )}
    </div>
  )
}

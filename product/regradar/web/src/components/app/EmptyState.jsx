import { ExternalLink, ShieldCheck } from 'lucide-react'

import { sampleAlert } from '../../data/mockData'

// The single, clearly-labelled SAMPLE card shown in the first-session empty
// state. It is built entirely from the real sealed DIFC record (see
// data/mockData.js → sampleAlert), so "Verify this yourself" can prove the loop
// end-to-end at /verify#sample with zero setup. Muted, dashed styling plus the
// "Sample" badge and the "not your own monitored data" line make it impossible
// to mistake for a real customer alert.
export default function SampleAlertEmptyState() {
  const sample = sampleAlert

  return (
    <section
      aria-label="Sample evidence-backed alert"
      className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--bg-base)] p-5 opacity-95"
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-300">
          Sample
        </span>
        <span className="rounded-full border border-[var(--trust-border)] bg-[var(--trust-badge)] px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)]">
          {sample.runStatus}
        </span>
        <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
          Integrity {sample.integrityStatus}
        </span>
      </div>

      <p className="text-xs font-medium leading-relaxed text-[var(--text-muted)]">
        Sample — a real sealed record from an official source, shown so you can see
        what an alert looks like. This is not your own monitored data.
      </p>

      <h3 className="mt-3 text-sm font-semibold text-white">{sample.sourceName}</h3>
      <p className="mt-1 text-xs text-[var(--text-muted)]">
        {sample.regulator} · Captured {sample.capturedAt}
      </p>

      <div className="mt-3 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
          Sealed diff
        </p>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">{sample.diffSummary}</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words rounded bg-[var(--bg-base)] p-2 font-mono text-[11px] text-[var(--text-primary)]">
          {sample.diffExcerpt}
        </pre>
        <p className="mt-2 text-[11px] leading-relaxed text-[var(--text-muted)]">
          Flagged for review: {sample.reviewReason}
        </p>
      </div>

      <p className="mt-3 break-all font-mono text-[10px] text-[var(--text-muted)]" title={sample.recordId}>
        {sample.recordId}
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <a
          href={sample.verifyHref}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-2 text-xs font-semibold text-[var(--accent)] transition-colors hover:border-[var(--accent)]"
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          Verify this yourself
        </a>
        <a
          href={sample.sourceUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Official source
        </a>
      </div>

      <p className="mt-4 border-t border-[var(--border-muted)] pt-3 text-xs leading-relaxed text-[var(--text-muted)]">
        Your monitored sources appear here once your plan is activated.
      </p>
    </section>
  )
}

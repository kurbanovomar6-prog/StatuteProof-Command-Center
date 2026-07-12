import { AlertTriangle, RotateCw } from 'lucide-react'

/** Human-readable data-load error with an optional retry that re-runs the same request. */
export default function ErrorState({ title = 'Could not load this data.', detail, onRetry, className = '' }) {
  return (
    <div className={`px-5 py-10 text-center ${className}`}>
      <AlertTriangle className="mx-auto mb-3 h-5 w-5 text-amber-400" aria-hidden="true" />
      <p className="text-sm font-medium text-amber-300">{title}</p>
      {detail && <p className="mx-auto mt-1 max-w-md text-xs text-[var(--text-muted)]">{detail}</p>}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] transition-colors hover:border-[var(--trust-border)] hover:text-white"
        >
          <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  )
}

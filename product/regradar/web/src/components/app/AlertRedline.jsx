import { useEffect, useState } from 'react'
import { Minus, Plus } from 'lucide-react'

import { redline as redlineApi } from '../../api'

/**
 * AlertRedline — readable added/removed view of one alert's SEALED diff.
 *
 * Every rendered line is parsed server-side from the diff artifact the pipeline
 * sealed at ingest (it traces to the record_hash shown in the proof panel) —
 * nothing is re-diffed against the live source. This is a monitoring view of a
 * DETECTED change: the server-authored `framing` + short disclaimer ride on the
 * payload and are rendered verbatim below the lines.
 *
 * Mounted lazily (only when the proof panel is open) so the alerts list never
 * fans out N redline requests. Falls back to the raw `diff_excerpt` the alert
 * already carries when no structured redline is available.
 */
export default function AlertRedline({ alertId, fallbackExcerpt }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setFailed(false)
    redlineApi.get(alertId)
      .then(res => { if (active) setData(res.redline || null) })
      .catch(() => { if (active) setFailed(true) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [alertId])

  if (loading) {
    return <div className="sp-skeleton mt-3 h-14 w-full rounded-lg" />
  }

  // No structured redline (fetch failed, or the sealed record has no parseable
  // diff): fall back to the raw excerpt the alert already displayed, with the
  // server's honest note when we have one.
  if (failed || !data || !data.available) {
    return (
      <div className="mt-3">
        {fallbackExcerpt ? (
          <>
            <p className="text-[11px] text-[var(--text-muted)]">What changed (excerpt)</p>
            <p
              className="mt-1 max-h-28 overflow-y-auto whitespace-pre-wrap rounded-md border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-2.5 py-2 text-[11px] leading-relaxed text-[var(--text-secondary)]"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              {fallbackExcerpt}
            </p>
          </>
        ) : null}
        {!failed && data && data.note ? (
          <p className="mt-1.5 text-[10px] leading-relaxed text-[var(--text-muted)]">{data.note}</p>
        ) : null}
      </div>
    )
  }

  return (
    <div className="mt-3">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-[11px] text-[var(--text-muted)]">What changed (sealed redline)</p>
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-1.5 py-0.5 text-[10px] text-emerald-300">
          <Plus className="h-2.5 w-2.5" />
          {data.added_lines}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full border border-rose-400/25 bg-rose-400/10 px-1.5 py-0.5 text-[10px] text-rose-300">
          <Minus className="h-2.5 w-2.5" />
          {data.removed_lines}
        </span>
      </div>

      <div className="mt-1 max-h-64 overflow-y-auto rounded-md border border-[var(--border-muted)] bg-[var(--bg-elevated)]">
        {data.blocks.map((block, index) => (
          <div key={index}>
            {block.lines.map((line, lineIndex) => (
              <p
                key={lineIndex}
                className={`whitespace-pre-wrap border-l-2 px-2.5 py-0.5 text-[11px] leading-relaxed ${
                  block.op === 'added'
                    ? 'border-emerald-400/60 bg-emerald-400/5 text-emerald-200'
                    : 'border-rose-400/60 bg-rose-400/5 text-rose-200 line-through decoration-rose-400/40'
                }`}
                style={{ fontFamily: 'var(--font-mono)' }}
              >
                {line}
              </p>
            ))}
          </div>
        ))}
      </div>

      {(data.truncated || data.partial) && (
        <p className="mt-1 text-[10px] text-[var(--text-muted)]">
          {data.truncated ? 'Long change — the redline is truncated; the full sealed diff is in the evidence record. ' : ''}
          {data.partial ? data.note : ''}
        </p>
      )}

      <p className="mt-1.5 text-[10px] leading-relaxed text-[var(--text-muted)]">
        {data.framing} {data.disclaimer}
      </p>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { ExternalLink, FileCheck } from 'lucide-react'

import { delivery, evidence as evidenceApi } from '../../api'
import { getWorkspaceProfile } from '../../data/workspaceProfile'
import { BACKFILL_STRINGS } from './firstRunBackfillStrings'
import TimeStamp from './ui/TimeStamp'

/**
 * FirstRunBackfillPanel — "see your signal now" for a first-run dashboard.
 *
 * A new workspace has no reviewed alerts until a regulator actually publishes
 * something, so the first session can end on an empty dashboard. This panel
 * fills that gap honestly: when the alerts preview is EMPTY, it shows the most
 * recent already-sealed CHANGED evidence records (data the monitor captured
 * independently of this account) as a preview of what the evidence trail
 * looks like — explicitly NOT alerts for this workspace and NOT retroactive
 * coverage.
 *
 * Visibility is self-contained: it renders nothing while checking, nothing
 * when the user already has alerts, and nothing when either fetch fails (the
 * dashboard's existing empty state is the quiet fallback — never a broken
 * panel on first login).
 */

const MAX_RECORDS = 3
const PREVIEW_DAYS = 14
const EVIDENCE_FETCH_LIMIT = 50

// Onboarding market names → coverage market code (mirrors workspaceProfile).
const MARKET_TO_CODE = {
  UAE: 'AE',
  DIFC: 'AE',
  ADGM: 'AE',
  'Other UAE source': 'AE',
}

// The user's market scope where determinable from the saved profile; honest
// fallback to the default market (with a fallback label) otherwise.
function scopeFromProfile(profile) {
  const codes = [...new Set((profile?.markets || []).map(m => MARKET_TO_CODE[m]).filter(Boolean))]
  if (codes.length === 1) return { market: codes[0], scoped: true }
  return { market: 'AE', scoped: false }
}

// Shorten "sha256:<64 hex>" for display; the full value stays in the title.
function shortHash(value) {
  const text = String(value || '')
  return text.length > 26 ? `${text.slice(0, 26)}…` : text
}

function recordHash(record) {
  const hash = record.normalized_hash || record.content_hash
  return hash ? `sha256:${hash}` : ''
}

// One-line change summary IF the record carries one — the evidence API does
// not always forward it, and we never invent one client-side.
function changeSummary(record) {
  const text = record.change_summary || record.summary
  return typeof text === 'string' ? text.trim() : ''
}

function BackfillRecordCard({ record }) {
  const hash = recordHash(record)
  const summary = changeSummary(record)
  return (
    <div className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="min-w-0 truncate text-sm font-medium text-white">
          {record.source_name || record.source_id || 'Official source'}
        </p>
        <span className="inline-flex items-center gap-1 rounded-full border border-[var(--trust-border)] bg-[var(--trust-badge)] px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)]">
          <FileCheck className="h-3 w-3" aria-hidden="true" />
          {BACKFILL_STRINGS.sealedChip}
        </span>
      </div>

      <dl className="mt-2 space-y-1.5 text-[11px]">
        <div className="flex gap-2">
          <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">{BACKFILL_STRINGS.capturedLabel}</dt>
          <dd className="text-[var(--text-secondary)]">
            <TimeStamp value={record.timestamp_utc} mode="absolute" fallback="Not recorded" />
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">{BACKFILL_STRINGS.sealLabel}</dt>
          <dd
            className="min-w-0 truncate text-[var(--text-secondary)]"
            style={{ fontFamily: 'var(--font-mono)' }}
            title={hash || undefined}
          >
            {hash ? shortHash(hash) : 'Not recorded'}
          </dd>
        </div>
        {summary ? (
          <div className="flex gap-2">
            <dt className="w-16 flex-shrink-0 text-[var(--text-muted)]">{BACKFILL_STRINGS.changeNoteLabel}</dt>
            <dd className="min-w-0 truncate text-[var(--text-secondary)]" title={summary}>
              {summary}
            </dd>
          </div>
        ) : null}
      </dl>

      <a
        href="/verify"
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2.5 inline-flex items-center gap-1.5 text-[11px] font-semibold text-[var(--accent)] transition-colors hover:text-[var(--text-primary)]"
      >
        <ExternalLink className="h-3 w-3" aria-hidden="true" />
        {BACKFILL_STRINGS.verifyLink}
      </a>
    </div>
  )
}

export default function FirstRunBackfillPanel() {
  // Stable per-mount scope: read once so the effect never re-runs on renders.
  const [scope] = useState(() => scopeFromProfile(getWorkspaceProfile()))
  // 'checking' → preview fetch in flight (render nothing — most users have
  // alerts and must never see a skeleton flash); 'loading' → confirmed empty,
  // evidence fetch in flight (skeleton); 'ready' | 'empty' → final panel;
  // 'hidden' → user has alerts, or a fetch failed (quiet fallback).
  const [status, setStatus] = useState('checking')
  const [records, setRecords] = useState([])

  useEffect(() => {
    let active = true
    delivery
      .preview(PREVIEW_DAYS)
      .then(data => {
        if (!active) return null
        const matches = data?.preview?.matches || []
        if (matches.length > 0) {
          setStatus('hidden')
          return null
        }
        setStatus('loading')
        return evidenceApi.list(scope.market, EVIDENCE_FETCH_LIMIT).then(evidenceData => {
          if (!active) return
          const rows = Array.isArray(evidenceData?.evidence) ? evidenceData.evidence : []
          const changed = rows
            .filter(row => row.change_status === 'CHANGED')
            .sort((a, b) => String(b.timestamp_utc || '').localeCompare(String(a.timestamp_utc || '')))
            .slice(0, MAX_RECORDS)
          setRecords(changed)
          setStatus(changed.length > 0 ? 'ready' : 'empty')
        })
      })
      .catch(() => {
        if (active) setStatus('hidden')
      })
    return () => { active = false }
  }, [scope])

  if (status === 'checking' || status === 'hidden') return null

  return (
    <section aria-labelledby="first-run-backfill-heading" className="sp-panel p-5">
      <div className="mb-1 flex flex-wrap items-start justify-between gap-2">
        <h2 id="first-run-backfill-heading" className="text-sm font-semibold text-white">
          {BACKFILL_STRINGS.heading}
        </h2>
        <span className="inline-flex rounded-full border border-[var(--border)] bg-[var(--bg-raised)] px-2.5 py-1 text-[11px] font-semibold text-[var(--text-primary)]">
          {scope.scoped ? BACKFILL_STRINGS.scopeScoped : BACKFILL_STRINGS.scopeFallback}
        </span>
      </div>

      <p className="max-w-3xl text-xs leading-relaxed text-[var(--text-secondary)]">
        {BACKFILL_STRINGS.framing}
      </p>
      <p className="mt-1 max-w-3xl text-[11px] leading-relaxed text-[var(--text-muted)]">
        {BACKFILL_STRINGS.independence}
      </p>

      {status === 'loading' ? (
        <div className="mt-3 space-y-2" aria-hidden="true">
          <div className="sp-skeleton h-20 w-full rounded-lg" />
          <div className="sp-skeleton h-20 w-full rounded-lg" />
          <div className="sp-skeleton h-20 w-full rounded-lg" />
        </div>
      ) : status === 'empty' ? (
        <div className="mt-3 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-4 py-6 text-center">
          <p className="text-xs leading-relaxed text-[var(--text-secondary)]">{BACKFILL_STRINGS.empty}</p>
        </div>
      ) : (
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          {records.map((record, index) => (
            <BackfillRecordCard key={record.run_id || record.evidence_record_id || index} record={record} />
          ))}
        </div>
      )}

      <p className="mt-3 border-t border-[var(--border-muted)] pt-3 text-[10px] leading-relaxed text-[var(--text-muted)]">
        {BACKFILL_STRINGS.disclaimer}
      </p>
    </section>
  )
}

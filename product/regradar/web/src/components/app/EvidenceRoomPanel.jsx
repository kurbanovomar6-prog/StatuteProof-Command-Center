import { useEffect, useState } from 'react'
import { Copy, Link2, ShieldCheck, Trash2 } from 'lucide-react'

import { evidenceRoom } from '../../api'

function isoDaysAgo(days) {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - days)
  return d.toISOString().slice(0, 10)
}

const EXPIRY_OPTIONS = [7, 14, 30, 60, 90]

const STATUS_STYLES = {
  active: 'text-emerald-300',
  expired: 'text-amber-300',
  revoked: 'text-[var(--text-muted)]',
}

/**
 * Auditor Evidence Room — owner-side management.
 *
 * Creates a scoped, time-boxed, READ-ONLY link an examiner/auditor can open
 * without an account. The link is shown exactly ONCE at creation (the server
 * stores only a hash of it) and can be revoked here at any time.
 *
 * @param {{ sources?: { id: string, name: string }[] }} props
 */
export default function EvidenceRoomPanel({ sources = [] }) {
  const [sourceId, setSourceId] = useState('')
  const [dateFrom, setDateFrom] = useState(isoDaysAgo(90))
  const [dateTo, setDateTo] = useState(isoDaysAgo(0))
  const [expiresDays, setExpiresDays] = useState(30)
  const [displayName, setDisplayName] = useState('')
  const [status, setStatus] = useState('idle') // idle | working | success | error
  const [message, setMessage] = useState('')
  const [createdLink, setCreatedLink] = useState('')
  const [copied, setCopied] = useState(false)
  const [shares, setShares] = useState([])
  const [sharesError, setSharesError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const effectiveSourceId = sourceId || sources[0]?.id || ''
  const hasSources = sources.length > 0
  const isWorking = status === 'working'

  useEffect(() => {
    let active = true
    evidenceRoom.listShares()
      .then(data => {
        if (active) setShares(Array.isArray(data.shares) ? data.shares : [])
      })
      .catch(() => {
        if (active) setSharesError('Could not load existing shares.')
      })
    return () => { active = false }
  }, [reloadKey])

  async function handleCreate() {
    if (!effectiveSourceId) {
      setStatus('error')
      setMessage('Select a source to share.')
      return
    }
    setStatus('working')
    setMessage('')
    setCreatedLink('')
    setCopied(false)
    try {
      const data = await evidenceRoom.createShare({
        sourceIds: [effectiveSourceId],
        dateFrom,
        dateTo,
        expiresDays,
        orgDisplayName: displayName,
      })
      const origin = typeof window !== 'undefined' ? window.location.origin : ''
      setCreatedLink(`${origin}/room/${data.token}`)
      setStatus('success')
      setMessage(`Share created — ${data.record_count} sealed record(s) in scope. Expires ${data.expires_at}.`)
      setReloadKey(k => k + 1)
    } catch (err) {
      setStatus('error')
      setMessage(err.message || 'Could not create the share.')
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(createdLink)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  async function handleRevoke(shareId) {
    try {
      await evidenceRoom.revokeShare(shareId)
      setReloadKey(k => k + 1)
    } catch (err) {
      setSharesError(err.message || 'Could not revoke the share.')
    }
  }

  return (
    <div className="rounded-xl border border-[var(--border-muted)] bg-[var(--bg-elevated)] p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--bg-raised)]">
          <Link2 className="h-4 w-4 text-[var(--text-primary)]" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Auditor evidence room</h2>
          <p className="mt-0.5 max-w-2xl text-xs leading-relaxed text-[var(--text-secondary)]">
            A time-boxed, read-only link for your examiner or auditor. They see only the sealed
            records for the scope you choose — no account needed — and can check every hash
            independently. You can revoke the link at any time.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_auto_auto_auto]">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-[var(--text-muted)]">Source</span>
          <select
            value={effectiveSourceId}
            onChange={event => setSourceId(event.target.value)}
            disabled={!hasSources || isWorking}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
          >
            {!hasSources && <option value="">No sources with evidence yet</option>}
            {sources.map(source => (
              <option key={source.id} value={source.id}>{source.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-[var(--text-muted)]">From</span>
          <input
            type="date"
            value={dateFrom}
            max={dateTo}
            onChange={event => setDateFrom(event.target.value)}
            disabled={isWorking}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-[var(--text-muted)]">To</span>
          <input
            type="date"
            value={dateTo}
            min={dateFrom}
            onChange={event => setDateTo(event.target.value)}
            disabled={isWorking}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-[var(--text-muted)]">Link expires in</span>
          <select
            value={expiresDays}
            onChange={event => setExpiresDays(Number(event.target.value))}
            disabled={isWorking}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
          >
            {EXPIRY_OPTIONS.map(days => (
              <option key={days} value={days}>{days} days</option>
            ))}
          </select>
        </label>
      </div>

      <label className="mt-3 flex max-w-md flex-col gap-1">
        <span className="text-[11px] font-semibold text-[var(--text-muted)]">
          Shown to the reviewer as (optional)
        </span>
        <input
          type="text"
          value={displayName}
          maxLength={120}
          placeholder="e.g. Acme Exchange FZE"
          onChange={event => setDisplayName(event.target.value)}
          disabled={isWorking}
          className="rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none disabled:opacity-60"
        />
      </label>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleCreate}
          disabled={isWorking || !hasSources}
          className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-colors ${
            isWorking || !hasSources
              ? 'cursor-not-allowed bg-[var(--bg-raised)] text-[var(--text-muted)]'
              : 'bg-[var(--accent)] text-[var(--ink)] hover:bg-[var(--accent-hover)]'
          }`}
        >
          <Link2 className="h-3.5 w-3.5" />
          {isWorking ? 'Creating share…' : 'Create review link'}
        </button>
        {status === 'success' && <span className="text-xs text-emerald-300">{message}</span>}
        {status === 'error' && <span className="text-xs text-rose-300">{message}</span>}
      </div>

      {createdLink && (
        <div className="mt-4 rounded-lg border border-[var(--trust-border)] bg-[var(--bg-base)] px-3 py-3">
          <p className="text-[11px] font-semibold text-amber-300">
            Copy this link now — it is shown only once. The server stores a hash of it, not the
            link itself, so it cannot be displayed again.
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <code className="break-all text-[11px] text-[var(--text-primary)]">{createdLink}</code>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded-lg border border-[var(--border)] px-2 py-1 text-[11px] font-semibold text-[var(--text-primary)] hover:text-white"
            >
              <Copy className="h-3 w-3" />
              {copied ? 'Copied' : 'Copy link'}
            </button>
          </div>
        </div>
      )}

      {(shares.length > 0 || sharesError) && (
        <div className="mt-5 border-t border-[var(--border-muted)] pt-4">
          <h3 className="text-xs font-semibold text-white">Existing review links</h3>
          {sharesError && <p className="mt-2 text-xs text-rose-300">{sharesError}</p>}
          <ul className="mt-2 space-y-2">
            {shares.map(share => (
              <li
                key={share.share_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-xs text-[var(--text-primary)]">
                    {(share.source_ids || []).join(', ') || 'no sources'}
                    <span className="ml-2 text-[11px] text-[var(--text-muted)]">
                      {share.date_from} → {share.date_to}
                    </span>
                  </p>
                  <p className="mt-0.5 text-[11px] text-[var(--text-muted)]">
                    <span className={STATUS_STYLES[share.status] || 'text-[var(--text-muted)]'}>
                      {share.status}
                    </span>
                    {' · '}expires {share.expires_at}
                    {share.org_display_name ? ` · shown as ${share.org_display_name}` : ''}
                  </p>
                </div>
                {share.status === 'active' && (
                  <button
                    type="button"
                    onClick={() => handleRevoke(share.share_id)}
                    className="inline-flex items-center gap-1 rounded-lg border border-[var(--border)] px-2 py-1 text-[11px] font-semibold text-rose-300 transition-colors hover:border-rose-400/50"
                  >
                    <Trash2 className="h-3 w-3" />
                    Revoke
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-3 py-3">
        <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-[var(--text-muted)]" />
        <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
          The room shows your recorded monitoring evidence and its hashes so a reviewer can check
          them independently. For monitoring information only. Not legal advice and not a guarantee
          of compliance.
        </p>
      </div>
    </div>
  )
}

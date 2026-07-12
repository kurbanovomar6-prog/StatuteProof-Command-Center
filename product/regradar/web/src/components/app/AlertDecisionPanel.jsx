import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, FileSignature } from 'lucide-react'

import { decisions as decisionsApi } from '../../api'
import TimeStamp from './ui/TimeStamp'

// Static fallback copy, matched byte-for-byte to app/decision_records.py FRAMING.
// The server returns the authoritative (forbidden-claims guarded) framing on GET;
// this is only used before the first response so the panel never renders empty
// labels. The user's statement / correction reason are THEIR words — rendered
// verbatim, never rewritten client-side.
const FALLBACK_FRAMING = {
  title: 'Your decision record',
  subtitle:
    'Seal your own review decision for this change into the evidence record. You author the wording; StatuteProof records and time-stamps it, unchanged.',
  empty:
    'No sealed decisions yet. When you have reviewed this change, you can record your own decision and seal it into the evidence record.',
  statement_label: 'Your decision, in your own words',
  statement_placeholder: 'Record what you reviewed and the decision you are making.',
  kind_label: 'How you want to log this',
  seal_button: 'Seal my decision',
  confirm_title: 'Seal this decision?',
  confirm_body:
    'Once sealed, this decision is time-stamped and cannot be edited. If you need to correct it later, you can add a new, linked entry — the original stays in the record.',
  amend_button: 'Record a correction',
  amend_note:
    'This adds a new sealed entry that references the earlier one. The earlier decision remains unchanged in the record.',
  who_note:
    'Your name and account are recorded with the decision so the record shows who reviewed it.',
  disclaimer:
    'You author this decision; StatuteProof records your words without changing them and does not review, suggest, or assess the decision. For monitoring information only. Not legal advice and not a guarantee of compliance.',
}

// Fallback for the five neutral log-type slugs (app/decision_records.py KINDS);
// the server list on GET is authoritative.
const FALLBACK_KINDS = [
  'reviewed',
  'acknowledged',
  'escalated',
  'no_change_needed',
  'action_recorded',
]

// Bounds mirror the server (which REJECTS oversize — the user's words are never
// truncated, so the UI blocks the submit instead of clipping the text).
const MAX_STATEMENT_LEN = 4000
const MAX_REASON_LEN = 2000

// Neutral display label for a kind slug: "no_change_needed" → "No change needed".
function kindLabel(kind) {
  const text = String(kind || '').replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

// Shorten "sha256:<64 hex>" for display; the full value stays in the title.
function shortHash(value) {
  const text = String(value || '')
  return text.length > 26 ? `${text.slice(0, 26)}…` : text
}

/**
 * AlertDecisionPanel — the sealed decision log for ONE alert.
 *
 * A reviewer records their OWN sign-off in their OWN words; the server seals it
 * (unchanged) into the org's append-only hash chain, bound to the alert's
 * sealed evidence record. Sealing is irreversible by design — corrections are
 * new, linked entries. All framing copy is server-authored and guard-checked;
 * this component renders it verbatim. Mounted lazily (contents fetch only when
 * the panel is opened) so the alerts list never fans out N requests.
 */
export default function AlertDecisionPanel({ alertId }) {
  const [open, setOpen] = useState(false)
  const [entries, setEntries] = useState([])
  const [framing, setFraming] = useState(FALLBACK_FRAMING)
  const [kinds, setKinds] = useState(FALLBACK_KINDS)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [readOnlyMsg, setReadOnlyMsg] = useState('')

  const [kind, setKind] = useState('reviewed')
  const [statement, setStatement] = useState('')
  const [amendTarget, setAmendTarget] = useState('')
  const [amendReason, setAmendReason] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [sealing, setSealing] = useState(false)
  const [sealMsg, setSealMsg] = useState('')

  // Reset per-alert state when the alert changes (render-phase adjustment,
  // same pattern as AlertChecklistPanel). The draft statement/reason MUST be
  // cleared too: words typed for one alert can never carry into another
  // alert's seal flow — a sealed record is irreversible. readOnlyMsg persists
  // deliberately (a role denial is user-level, not alert-level).
  const [loadedAlertId, setLoadedAlertId] = useState(alertId)
  if (loadedAlertId !== alertId) {
    setLoadedAlertId(alertId)
    setOpen(false)
    setLoading(true)
    setEntries([])
    setStatement('')
    setAmendTarget('')
    setAmendReason('')
    setConfirming(false)
    setSealMsg('')
    setLoadError('')
  }

  useEffect(() => {
    if (!open) return undefined
    let active = true
    decisionsApi.list(alertId)
      .then(data => {
        if (!active) return
        setEntries(data.decisions || [])
        if (data.framing) setFraming(data.framing)
        if (Array.isArray(data.kinds) && data.kinds.length) setKinds(data.kinds)
        setLoadError('')
      })
      .catch(err => { if (active) setLoadError(err.message || 'Could not load the decision record.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [alertId, open])

  const trimmedStatement = statement.trim()
  const statementOver = statement.length > MAX_STATEMENT_LEN
  const reasonOver = amendReason.length > MAX_REASON_LEN
  const amendMissingReason = Boolean(amendTarget) && !amendReason.trim()
  const canSeal = Boolean(trimmedStatement) && !statementOver && !reasonOver && !amendMissingReason && !sealing

  // Corrections that reference an earlier entry, so the original can carry an
  // honest "a correction references this entry" note.
  const supersededIds = new Set(
    entries
      .map(entry => entry?.content?.supersedes_decision_id)
      .filter(Boolean),
  )

  function startAmend(decisionId) {
    setAmendTarget(decisionId)
    setAmendReason('')
    setConfirming(false)
    setSealMsg('')
  }

  function cancelAmend() {
    setAmendTarget('')
    setAmendReason('')
  }

  async function handleConfirmSeal() {
    setSealing(true)
    setSealMsg('')
    try {
      const body = { alert_id: alertId, kind, statement }
      if (amendTarget) {
        body.supersedes_decision_id = amendTarget
        body.amendment_reason = amendReason
      }
      const result = await decisionsApi.seal(body)
      setEntries(prev => [...prev, result.decision])
      setStatement('')
      setAmendTarget('')
      setAmendReason('')
      setConfirming(false)
    } catch (err) {
      setConfirming(false)
      if (err.status === 403) {
        // Role denial (e.g. an auditor seat): the log stays readable; the
        // compose form is replaced with the server's honest denial.
        setReadOnlyMsg(err.message || 'Your role does not permit this action.')
      } else {
        setSealMsg(err.message || 'The decision could not be sealed. Nothing was recorded.')
      }
    } finally {
      setSealing(false)
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
        <FileSignature className="h-3.5 w-3.5 text-[var(--accent)]" />
        {framing.title}
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {open && (
        <div className="mt-2 rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] p-3">
          <p className="text-[11px] leading-relaxed text-[var(--text-muted)]">{framing.subtitle}</p>

          {loading && <div className="sp-skeleton mt-3 h-10 w-full rounded-lg" />}

          {!loading && loadError && (
            <p className="mt-3 text-xs text-amber-300">{loadError} Reopen this panel to retry.</p>
          )}

          {!loading && !loadError && entries.length === 0 && (
            <p className="mt-3 text-xs text-[var(--text-muted)]">{framing.empty}</p>
          )}

          {!loading && entries.length > 0 && (
            <ol className="mt-3 space-y-2">
              {entries.map(entry => {
                const content = entry?.content || {}
                const decision = content.decision || {}
                const decidedBy = content.decided_by || {}
                return (
                  <li
                    key={entry.decision_id}
                    className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-elevated)] px-3 py-2.5"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-[var(--trust-border)] bg-[var(--trust-badge)] px-2 py-0.5 text-[10px] font-semibold text-[var(--accent)]">
                        {kindLabel(decision.kind)}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">
                        {decidedBy.display_name || 'Recorded reviewer'}
                      </span>
                      <TimeStamp
                        value={content.decided_at_utc}
                        mode="absolute"
                        className="text-[10px] text-[var(--text-muted)]"
                      />
                    </div>

                    {/* The reviewer's words, verbatim. */}
                    <p className="mt-1.5 whitespace-pre-wrap text-xs leading-relaxed text-[var(--text-secondary)]">
                      {decision.statement}
                    </p>

                    {content.supersedes_decision_id && (
                      <div className="mt-1.5 border-l-2 border-[var(--border)] pl-2">
                        <p className="text-[10px] text-[var(--text-muted)]">
                          Correction of{' '}
                          <span style={{ fontFamily: 'var(--font-mono)' }}>
                            {content.supersedes_decision_id}
                          </span>
                        </p>
                        {content.amendment_reason && (
                          <p className="mt-0.5 whitespace-pre-wrap text-[11px] leading-relaxed text-[var(--text-secondary)]">
                            {content.amendment_reason}
                          </p>
                        )}
                      </div>
                    )}

                    {supersededIds.has(entry.decision_id) && (
                      <p className="mt-1.5 text-[10px] text-[var(--text-muted)]">
                        A later correction references this entry. It remains unchanged in the record.
                      </p>
                    )}

                    <div className="mt-2 flex flex-wrap items-center gap-3">
                      <span
                        className="text-[10px] text-[var(--text-muted)]"
                        style={{ fontFamily: 'var(--font-mono)' }}
                        title={entry.record_hash}
                      >
                        {shortHash(entry.record_hash)}
                      </span>
                      <a
                        href="/verify"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--accent)] transition-colors hover:text-[var(--text-primary)]"
                      >
                        <ExternalLink className="h-2.5 w-2.5" />
                        Verify independently
                      </a>
                      {!readOnlyMsg && (
                        <button
                          type="button"
                          onClick={() => startAmend(entry.decision_id)}
                          className="text-[10px] font-semibold text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
                        >
                          {framing.amend_button}
                        </button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ol>
          )}

          {!loading && readOnlyMsg && (
            <p className="mt-3 text-xs text-[var(--text-muted)]">
              {readOnlyMsg} This decision record is read-only for your role.
            </p>
          )}

          {!loading && !loadError && !readOnlyMsg && (
            <div className="mt-3 rounded-lg border border-[var(--border)] bg-[var(--bg-raised)] p-3">
              {amendTarget && (
                <div className="mb-2.5 border-l-2 border-[var(--trust-border)] pl-2">
                  <p className="text-[10px] font-semibold text-[var(--text-secondary)]">
                    Correcting{' '}
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{amendTarget}</span>
                  </p>
                  <p className="mt-0.5 text-[10px] leading-relaxed text-[var(--text-muted)]">
                    {framing.amend_note}
                  </p>
                  <button
                    type="button"
                    onClick={cancelAmend}
                    className="mt-1 text-[10px] font-semibold text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
                  >
                    Cancel the correction
                  </button>
                </div>
              )}

              <label
                htmlFor={`adp-kind-${alertId}`}
                className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]"
              >
                {framing.kind_label}
              </label>
              <select
                id={`adp-kind-${alertId}`}
                value={kind}
                onChange={event => setKind(event.target.value)}
                className="mb-2.5 w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] py-1.5 pl-2.5 pr-8 text-xs text-[var(--text-primary)] focus:border-[var(--trust-border)] focus:outline-none sm:max-w-xs"
              >
                {kinds.map(value => (
                  <option key={value} value={value}>{kindLabel(value)}</option>
                ))}
              </select>

              <label
                htmlFor={`adp-statement-${alertId}`}
                className="mb-1 block text-[10px] font-semibold text-[var(--text-muted)]"
              >
                {framing.statement_label}
              </label>
              <textarea
                id={`adp-statement-${alertId}`}
                value={statement}
                onChange={event => setStatement(event.target.value)}
                placeholder={framing.statement_placeholder}
                rows={3}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
              />
              {statementOver && (
                <p className="mt-1 text-[10px] text-amber-300">
                  Longer than the {MAX_STATEMENT_LEN}-character limit. Your words are never
                  shortened for you — edit the statement to seal it.
                </p>
              )}

              {amendTarget && (
                <>
                  <label
                    htmlFor={`adp-reason-${alertId}`}
                    className="mb-1 mt-2.5 block text-[10px] font-semibold text-[var(--text-muted)]"
                  >
                    Your reason for the correction, in your own words
                  </label>
                  <textarea
                    id={`adp-reason-${alertId}`}
                    value={amendReason}
                    onChange={event => setAmendReason(event.target.value)}
                    rows={2}
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] px-3 py-1.5 text-xs text-white placeholder:text-[var(--text-muted)] focus:border-[var(--trust-border)] focus:outline-none"
                  />
                  {reasonOver && (
                    <p className="mt-1 text-[10px] text-amber-300">
                      Longer than the {MAX_REASON_LEN}-character limit. Your words are never
                      shortened for you — edit the reason to seal it.
                    </p>
                  )}
                </>
              )}

              {!confirming && (
                <div className="mt-2.5 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    disabled={!canSeal}
                    onClick={() => setConfirming(true)}
                    className="rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-4 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--trust-badge)] disabled:opacity-50"
                  >
                    {framing.seal_button}
                  </button>
                  {sealMsg && <span className="text-xs text-rose-300">{sealMsg}</span>}
                </div>
              )}

              {confirming && (
                <div className="mt-2.5 rounded-lg border border-[var(--trust-border)] bg-[var(--bg-elevated)] p-3">
                  <p className="text-xs font-semibold text-[var(--text-primary)]">
                    {framing.confirm_title}
                  </p>
                  <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-secondary)]">
                    {framing.confirm_body}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      disabled={sealing}
                      onClick={handleConfirmSeal}
                      className="rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-4 py-1.5 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--trust-badge)] disabled:opacity-50"
                    >
                      {sealing ? 'Sealing...' : framing.seal_button}
                    </button>
                    <button
                      type="button"
                      disabled={sealing}
                      onClick={() => setConfirming(false)}
                      className="rounded-lg border border-[var(--border)] px-4 py-1.5 text-xs font-semibold text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)] disabled:opacity-50"
                    >
                      Go back
                    </button>
                  </div>
                </div>
              )}

              <p className="mt-2.5 text-[10px] leading-relaxed text-[var(--text-muted)]">
                {framing.who_note}
              </p>
            </div>
          )}

          <p className="mt-3 text-[10px] leading-relaxed text-[var(--text-secondary)]">
            {framing.disclaimer}
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * RoomPage — the public Auditor Evidence Room (/room/<token>).
 *
 * The examiner-facing view of a share an account owner created: ONLY the frozen
 * scope (sources + period), each sealed record's hash and capture timestamp, a
 * coverage summary, and pointers to verify independently. No login — the token
 * in the URL is the credential; expired/revoked/unknown links all resolve to
 * the same honest "not available" state.
 *
 * Legal posture: this page faces an EXAMINER. It carries the FULL standard
 * disclaimer, uses negative-assurance wording only, and never claims
 * certification or completeness.
 */
import { useEffect, useState } from 'react'
import { CalendarClock, ExternalLink, FileSearch, Hash, ShieldAlert, ShieldCheck } from 'lucide-react'
import { evidenceRoom } from '../api'

function tokenFromLocation() {
  if (typeof window === 'undefined') return ''
  const path = window.location.pathname || ''
  if (!path.startsWith('/room/')) return ''
  return path.slice('/room/'.length).replace(/\/+$/, '')
}

function shortHash(value) {
  const text = String(value || '')
  if (!text) return 'not recorded'
  return text.length > 26 ? `${text.slice(0, 26)}…` : text
}

function StatCell({ label, value }) {
  return (
    <div className="sp-panel-muted p-3">
      <p className="text-[0.7rem] font-semibold uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums text-[var(--text-primary)]">{value}</p>
    </div>
  )
}

function RecordRow({ record }) {
  const changed = String(record.run_status || '').toUpperCase() === 'CHANGED'
  return (
    <li className="border-b border-[var(--border-subtle)] py-4 last:border-b-0">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-medium text-[var(--text-primary)]">
          {record.source_name || record.source_id}
        </p>
        <span
          className="text-[0.7rem] font-semibold uppercase tracking-wide"
          style={{ color: changed ? 'var(--accent)' : 'var(--text-muted)' }}
        >
          {record.run_status || 'recorded'}
        </span>
      </div>
      <p className="mt-1 text-xs tabular-nums text-[var(--text-secondary)]" style={{ fontFamily: 'var(--font-mono)' }}>
        {record.timestamp || 'timestamp not recorded'}
      </p>
      {record.change_summary ? (
        <p className="mt-2 text-[0.8rem] leading-relaxed text-[var(--text-secondary)]">{record.change_summary}</p>
      ) : null}
      {record.record_hash ? (
        <p
          className="mt-2 break-all text-[0.72rem] text-[var(--text-muted)]"
          style={{ fontFamily: 'var(--font-mono)' }}
          title={record.record_hash}
        >
          <Hash className="mr-1 inline h-3 w-3 align-[-1px]" aria-hidden="true" />
          record seal {shortHash(record.record_hash)}
        </p>
      ) : null}
      {record.normalized_hash ? (
        <p
          className={`${record.record_hash ? 'mt-1' : 'mt-2'} break-all text-[0.72rem] text-[var(--text-muted)]`}
          style={{ fontFamily: 'var(--font-mono)' }}
          title={record.normalized_hash}
        >
          <Hash className="mr-1 inline h-3 w-3 align-[-1px]" aria-hidden="true" />
          normalized {shortHash(record.normalized_hash)}
        </p>
      ) : null}
      {!record.record_hash && !record.normalized_hash ? (
        <p className="mt-2 text-[0.72rem] text-[var(--text-muted)]" style={{ fontFamily: 'var(--font-mono)' }}>
          hash not recorded
        </p>
      ) : null}
      <p className="mt-1 break-all text-[0.72rem] text-[var(--text-muted)]" style={{ fontFamily: 'var(--font-mono)' }}>
        {record.record_id}
      </p>
      {record.diff_excerpt ? (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs font-medium text-[var(--accent)]">
            Diff excerpt
          </summary>
          <pre
            className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg border border-[var(--border-subtle)] p-3 text-[0.72rem] leading-relaxed text-[var(--text-secondary)]"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            {record.diff_excerpt}
          </pre>
        </details>
      ) : null}
    </li>
  )
}

export default function RoomPage({ token: tokenProp }) {
  const token = tokenProp ?? tokenFromLocation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [room, setRoom] = useState(null)

  useEffect(() => {
    let active = true
    if (!token) {
      setError('This evidence room link is not available. It may have expired or been revoked.')
      setLoading(false)
      return () => { active = false }
    }
    evidenceRoom.view(token)
      .then(data => {
        if (active) setRoom(data.room || null)
      })
      .catch(err => {
        if (!active) return
        setError(
          err.status === 404
            ? (err.message || 'This evidence room link is not available. It may have expired or been revoked.')
            : 'The evidence room could not be loaded. Please try again.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [token])

  return (
    <div className="min-h-dvh bg-[var(--bg-base)] text-[var(--text-primary)]">
      <div className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
        <header>
          <p className="sp-section-eyebrow">Auditor evidence room</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-3xl">
            Evidence shared for regulatory review
          </h1>
        </header>

        {loading ? (
          <p className="mt-8 text-sm text-[var(--text-secondary)]" role="status">
            Loading the shared evidence…
          </p>
        ) : null}

        {!loading && error ? (
          <section className="sp-card mt-8" role="alert">
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" style={{ color: 'var(--text-muted)' }} />
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)]">Link not available</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--text-secondary)]">{error}</p>
                <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">
                  Evidence room links are time-boxed and revocable by the account holder. If you
                  expected this link to work, ask the person who shared it to issue a new one.
                </p>
              </div>
            </div>
          </section>
        ) : null}

        {!loading && !error && room ? (
          <>
            {room.shared_by ? (
              <p className="mt-3 text-sm text-[var(--text-secondary)]">
                Shared by <span className="font-medium text-[var(--text-primary)]">{room.shared_by}</span>
              </p>
            ) : null}
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">
              {room.note}
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <StatCell
                label="Period"
                value={`${room.period?.date_from || '—'} → ${room.period?.date_to || '—'}`}
              />
              <StatCell label="Sealed records" value={String(room.record_count ?? 0)} />
              <StatCell label="Detected changes" value={String(room.coverage?.changed_records ?? 0)} />
            </div>

            <p className="mt-3 flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
              Access to this room expires on{' '}
              <span className="tabular-nums" style={{ fontFamily: 'var(--font-mono)' }}>
                {room.expires_at || 'the recorded expiry date'}
              </span>
            </p>

            <section className="sp-card mt-6" aria-labelledby="room-sources">
              <h2 id="room-sources" className="text-sm font-semibold text-[var(--text-primary)]">
                Monitored sources in scope
              </h2>
              <ul className="mt-3 space-y-2">
                {(room.sources || []).map(source => (
                  <li key={source.source_id} className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
                    <span className="text-[var(--text-primary)]">
                      {source.source_name || source.source_id}
                      {source.regulator ? (
                        <span className="ml-2 text-xs text-[var(--text-muted)]">{source.regulator}</span>
                      ) : null}
                    </span>
                    {source.official_url ? (
                      <a
                        href={source.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-[var(--accent)] underline-offset-2 hover:underline"
                      >
                        Official source
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
              {room.coverage?.sources_without_records ? (
                <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
                  {room.coverage.sources_without_records} source(s) in scope have no sealed record in
                  this period. Gaps are disclosed, not hidden.
                </p>
              ) : null}
            </section>

            <section className="sp-card mt-6" aria-labelledby="room-records">
              <h2 id="room-records" className="text-sm font-semibold text-[var(--text-primary)]">
                Sealed evidence records
              </h2>
              {room.truncated ? (
                <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">
                  This view is capped and shows the first {room.record_count} records of the shared
                  period. Request the full evidence pack from the account holder for the complete set
                  of sealed records in this scope.
                </p>
              ) : null}
              {(room.records || []).length === 0 ? (
                <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
                  No sealed records exist for this scope yet. Records captured inside the shared
                  period will appear here.
                </p>
              ) : (
                <ul className="mt-2">
                  {(room.records || []).map(record => (
                    <RecordRow key={record.record_id} record={record} />
                  ))}
                </ul>
              )}
            </section>

            <section className="sp-card mt-6" aria-labelledby="room-verify">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" style={{ color: 'var(--accent)' }} />
                <div>
                  <h2 id="room-verify" className="text-sm font-semibold text-[var(--text-primary)]">
                    Verify independently
                  </h2>
                  <p className="mt-1 text-[0.8rem] leading-relaxed text-[var(--text-secondary)]">
                    {room.verification?.note}
                  </p>
                  <p className="mt-3 flex flex-wrap gap-4 text-xs font-medium">
                    <a
                      href={room.verification?.verify_url || '/verify'}
                      className="inline-flex items-center gap-1 text-[var(--accent)] underline-offset-2 hover:underline"
                    >
                      <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
                      Open the public verifier
                    </a>
                    <a
                      href={room.verification?.spec_url || '/api/verify-spec'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[var(--accent)] underline-offset-2 hover:underline"
                    >
                      Verification specification
                      <ExternalLink className="h-3 w-3" aria-hidden="true" />
                    </a>
                  </p>
                </div>
              </div>
            </section>

            <footer className="mt-8">
              <p className="text-xs font-semibold text-[var(--text-secondary)]">{room.disclaimer}</p>
              <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">{room.legal_notice}</p>
            </footer>
          </>
        ) : null}
      </div>
    </div>
  )
}

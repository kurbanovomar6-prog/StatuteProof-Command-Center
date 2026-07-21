import { useState } from 'react'
import { Check, Minus, ShieldAlert, ShieldCheck, X } from 'lucide-react'
import { verifyRecord } from '../api'

// ─── Block 2 — In-page evidence verifier ─────────────────────────────────────
//
// Runs a REAL logged-out round-trip against the public POST /api/verify
// endpoint, over the exact bytes of the shipped baseline record (the VARA
// Compliance & Risk Management Rulebook capture at /sample-record/*). The server
// never reads its own store — it re-hashes what this widget submits, the same as
// the full /verify page. The record is real public regulator content, so no
// SAMPLE/FAKE label is needed; the result is labelled honestly as a
// record-integrity check only, never legal advice or compliance.

const SAMPLE = {
  record: '/sample-record/record.json',
  raw: '/sample-record/raw.txt',
  normalized: '/sample-record/normalized.txt',
}

const STATUS_META = {
  pass: { Icon: Check, dot: 'var(--success,#37D399)', label: 'Pass' },
  fail: { Icon: X, dot: 'var(--danger,#F87171)', label: 'Fail' },
  skipped: { Icon: Minus, dot: 'var(--text-muted,#7C8BA1)', label: 'Skipped' },
}

const CHECK_TITLES = {
  record_is_object: 'Record shape',
  hash_formats: 'Hash formats',
  record_hash_self_consistent: 'Record hash self-consistent',
  raw_bytes_match: 'Raw bytes match',
  normalized_bytes_match: 'Normalized bytes match',
  normalization_reproducible: 'Normalization reproducible',
  diff_bytes_match: 'Sealed diff bytes match',
  capture_metadata_consistent: 'Capture metadata consistent',
  internal_error: 'Internal error',
}

async function fetchText(path) {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.text()
}

export default function InlineVerify({ onOpenFull }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function handleVerify() {
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const [recordStr, raw, normalized] = await Promise.all([
        fetchText(SAMPLE.record),
        fetchText(SAMPLE.raw),
        fetchText(SAMPLE.normalized),
      ])
      const data = await verifyRecord({
        record: JSON.parse(recordStr),
        raw,
        normalized,
      })
      setResult(data)
    } catch {
      setError(
        'Could not run the check right now. Open the full verifier to try again, or paste a record you hold.',
      )
    } finally {
      setLoading(false)
    }
  }

  const verified = result?.verified === true

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0A1628] p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white">Verify this record now — in page</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">
            Re-hashes the exact bytes of the VARA record above via the public
            /api/verify endpoint. No account. Confirms record integrity only —
            not legal advice, not compliance.
          </p>
        </div>
        <button
          type="button"
          onClick={handleVerify}
          disabled={loading}
          className="sp-btn-primary justify-center px-5 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Verifying…' : 'Verify this record'}
        </button>
      </div>

      {error ? (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-rose-400/40 bg-rose-400/10 px-3 py-2 text-sm text-rose-200"
        >
          {error}
        </p>
      ) : null}

      {result ? (
        <div className="mt-5" aria-live="polite">
          <div
            className="flex items-center gap-3 rounded-xl border px-4 py-3"
            style={{
              borderColor: verified ? 'var(--success,#37D399)' : 'var(--danger,#F87171)',
              background: verified ? 'rgba(55,211,153,0.08)' : 'rgba(248,113,113,0.08)',
            }}
          >
            {verified ? (
              <ShieldCheck className="h-5 w-5" style={{ color: 'var(--success,#37D399)' }} />
            ) : (
              <ShieldAlert className="h-5 w-5" style={{ color: 'var(--danger,#F87171)' }} />
            )}
            <div>
              <p
                className="text-sm font-semibold"
                style={{ color: verified ? 'var(--success,#37D399)' : 'var(--danger,#F87171)' }}
              >
                {verified ? 'Verified' : 'Not verified'}
              </p>
              <p className="text-xs text-slate-400">
                {verified
                  ? 'Every check that could run passed against the submitted bytes.'
                  : 'At least one check failed or could not be confirmed. See details below.'}
              </p>
            </div>
          </div>

          <ul className="mt-3 rounded-xl border border-slate-800 bg-slate-950/40 px-4">
            {(result.checks || []).map((check) => {
              const meta = STATUS_META[check.status] || STATUS_META.skipped
              const { Icon } = meta
              return (
                <li
                  key={check.name}
                  className="flex items-start gap-3 border-b border-slate-800/60 py-3 last:border-b-0"
                >
                  <span
                    className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full"
                    style={{ background: meta.dot }}
                    aria-hidden="true"
                  >
                    <Icon className="h-3 w-3" style={{ color: '#04111F' }} strokeWidth={3} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="text-sm font-medium text-slate-100">
                        {CHECK_TITLES[check.name] || check.name}
                      </p>
                      <span
                        className="text-[0.7rem] font-semibold uppercase tracking-wide"
                        style={{ color: meta.dot }}
                      >
                        {meta.label}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-400">{check.detail}</p>
                  </div>
                </li>
              )
            })}
          </ul>

          {result.disclaimer ? (
            <p className="mt-3 text-xs leading-relaxed text-slate-500">{result.disclaimer}</p>
          ) : null}

          {onOpenFull ? (
            <button
              type="button"
              onClick={onOpenFull}
              className="mt-3 text-sm font-semibold text-cyan-300 transition-colors hover:text-white"
            >
              Open the full verifier — upload your own record
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

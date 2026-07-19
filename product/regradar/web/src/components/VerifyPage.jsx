/**
 * VerifyPage — public, no-login evidence verifier.
 *
 * Paste a record.json (and optionally upload raw.txt / normalized.txt) and this
 * page runs standard SHA-256 over the bytes YOU hold via POST /api/verify. The
 * server never reads its own evidence store — that is the whole point: you do not
 * have to trust StatuteProof, you check the math yourself.
 *
 * "Load a real record" fills the form with a REAL evidence record of public
 * regulator content (the VARA Compliance & Risk Management Rulebook capture),
 * shipped as static assets under /sample-record/, so a first-time visitor can
 * run the check without holding a record. Deep link: /verify#sample auto-loads
 * that built-in record ONLY — the page never accepts records or URLs from
 * location params (no reflected-content vector).
 *
 * Disclaimer: verification confirms record integrity only. Not legal advice.
 */
import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ShieldCheck, ShieldAlert, Check, X, Minus, FileUp, FileSearch } from 'lucide-react'
import { verifyRecord } from '../api'

const SPEC_HREF = '/api/verify-spec'

// Static, repo-pinned assets: a real evidence record captured by the monitor
// from the official VARA Compliance & Risk Management Rulebook page, plus the
// exact raw and normalized text its hashes cover. Copied byte-for-byte from the
// evidence store; nothing in it is invented.
const SAMPLE_ASSETS = {
  record: '/sample-record/record.json',
  raw: '/sample-record/raw.txt',
  normalized: '/sample-record/normalized.txt',
}

async function fetchSampleAsset(path) {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.text()
}

const STATUS_META = {
  pass: {
    dot: 'var(--success)',
    label: 'Pass',
    Icon: Check,
  },
  fail: {
    dot: 'var(--danger)',
    label: 'Fail',
    Icon: X,
  },
  skipped: {
    dot: 'var(--text-muted)',
    label: 'Skipped',
    Icon: Minus,
  },
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

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error || new Error('Could not read file.'))
    reader.readAsText(file)
  })
}

function CheckRow({ check }) {
  const meta = STATUS_META[check.status] || STATUS_META.skipped
  const { Icon } = meta
  return (
    <li className="flex items-start gap-3 py-3 border-b border-[var(--border-subtle)] last:border-b-0">
      <span
        className="mt-1 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full"
        style={{ background: meta.dot }}
        aria-hidden="true"
      >
        <Icon className="h-3 w-3" style={{ color: '#04111F' }} strokeWidth={3} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-sm font-medium text-[var(--text-primary)]">
            {CHECK_TITLES[check.name] || check.name}
          </p>
          <span
            className="text-[0.7rem] font-semibold uppercase tracking-wide tabular-nums"
            style={{ color: meta.dot }}
          >
            {meta.label}
          </span>
        </div>
        <p className="mt-0.5 text-[0.8rem] leading-relaxed text-[var(--text-secondary)]">
          {check.detail}
        </p>
      </div>
    </li>
  )
}

export default function VerifyPage({ onBack }) {
  const [recordText, setRecordText] = useState('')
  const [rawText, setRawText] = useState(null)
  const [rawName, setRawName] = useState('')
  const [normalizedText, setNormalizedText] = useState(null)
  const [normalizedName, setNormalizedName] = useState('')
  const [diffText, setDiffText] = useState(null)
  const [diffName, setDiffName] = useState('')
  const [tokenB64, setTokenB64] = useState(null)
  const [tokenName, setTokenName] = useState('')
  const [tokenDigest, setTokenDigest] = useState('')
  const [loading, setLoading] = useState(false)
  const [sampleLoading, setSampleLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  // Guards the #sample deep-link against React StrictMode's double effect run.
  const autoLoadedRef = useRef(false)

  async function handleFile(event, setText, setName) {
    setError('')
    const file = event.target.files?.[0]
    if (!file) {
      setText(null)
      setName('')
      return
    }
    try {
      const text = await readFileAsText(file)
      setText(text)
      setName(file.name)
    } catch {
      setError('Could not read that file. Please choose a plain text file.')
      setText(null)
      setName('')
    }
  }

  async function handleTokenFile(event) {
    setError('')
    const file = event.target.files?.[0]
    if (!file) {
      setTokenB64(null)
      setTokenName('')
      return
    }
    // A real RFC 3161 token is 2–8KB; a mispicked large file would hang the
    // synchronous byte loop below, so fail fast instead.
    if (file.size > 64 * 1024) {
      setError('That file is too large to be an RFC 3161 token (max 64KB).')
      setTokenB64(null)
      setTokenName('')
      return
    }
    try {
      // .tsr is DER binary — read bytes and base64 them for the JSON body.
      const buf = await file.arrayBuffer()
      const bytes = new Uint8Array(buf)
      let bin = ''
      for (let i = 0; i < bytes.length; i += 1) bin += String.fromCharCode(bytes[i])
      setTokenB64(btoa(bin))
      setTokenName(file.name)
    } catch {
      setError('Could not read that timestamp token file.')
      setTokenB64(null)
      setTokenName('')
    }
  }

  // Shared verify runner: takes explicit values so the sample loader can run
  // the check immediately after loading, without racing setState.
  async function runVerify(record, raw, normalized, diff, timestampToken, timestampDigest) {
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await verifyRecord({
        record,
        raw: raw ?? undefined,
        normalized: normalized ?? undefined,
        diff: diff ?? undefined,
        timestampToken: timestampToken ?? undefined,
        timestampDigest: timestampDigest ?? undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Verification could not be completed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify() {
    setError('')
    setResult(null)

    const trimmed = recordText.trim()
    if (!trimmed) {
      setError('Paste a record.json object to verify.')
      return
    }

    let record
    try {
      record = JSON.parse(trimmed)
    } catch {
      setError('That is not valid JSON. Paste the exact contents of record.json.')
      return
    }

    await runVerify(record, rawText, normalizedText, diffText, tokenB64, tokenDigest)
  }

  async function handleLoadSample() {
    setError('')
    setResult(null)
    setSampleLoading(true)
    try {
      const [recordStr, raw, normalized] = await Promise.all([
        fetchSampleAsset(SAMPLE_ASSETS.record),
        fetchSampleAsset(SAMPLE_ASSETS.raw),
        fetchSampleAsset(SAMPLE_ASSETS.normalized),
      ])
      const record = JSON.parse(recordStr)
      setRecordText(recordStr.trim())
      setRawText(raw)
      setRawName('raw.txt')
      setNormalizedText(normalized)
      setNormalizedName('normalized.txt')
      // Clear any previously-chosen token: it belongs to a different record,
      // and leaving it staged would silently pair it with the sample on the
      // next manual Verify click while the auto-run below omits it.
      setTokenB64(null)
      setTokenName('')
      setTokenDigest('')
      await runVerify(record, raw, normalized)
    } catch {
      setError(
        'The real record could not be loaded right now. Please try again, or paste a record.json you hold.',
      )
    } finally {
      setSampleLoading(false)
    }
  }

  useEffect(() => {
    // Deep link: /verify#sample auto-loads the built-in real record ONLY.
    // Nothing else is ever read from the location — no arbitrary URLs, no
    // pasted records via params.
    if (autoLoadedRef.current) return
    if (typeof window !== 'undefined' && window.location.hash === '#sample') {
      autoLoadedRef.current = true
      // Defer past the effect body: the effect only reads the external URL and
      // schedules the load; all state updates happen in the microtask.
      queueMicrotask(handleLoadSample)
    }
    // Mount-only by design; handleLoadSample is stable in behaviour.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const verified = result?.verified === true
  const hasResult = result != null

  return (
    <div className="min-h-dvh bg-[var(--bg-base)] text-[var(--text-primary)]">
      <div className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        <header className="mt-8">
          <p className="sp-section-eyebrow">Open verification</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-3xl">
            Verify a StatuteProof evidence record
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">
            Runs standard SHA-256 in the open, over the bytes you hold — you don&apos;t have to trust
            StatuteProof. No login required. The server never reads its own evidence store; it only
            re-hashes what you submit. Read the{' '}
            <a
              href={SPEC_HREF}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-[var(--accent)] underline-offset-2 hover:underline"
            >
              open specification
            </a>
            . Not legal advice.
          </p>
        </header>

        <section className="sp-card mt-8" aria-labelledby="sample-loader-heading">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="min-w-0 flex-1" style={{ minWidth: '16rem' }}>
              <p id="sample-loader-heading" className="text-sm font-semibold text-[var(--text-primary)]">
                No record on hand? Load a real one.
              </p>
              <p className="mt-1 text-[0.8rem] leading-relaxed text-[var(--text-secondary)]">
                This is a real evidence record of public regulator content — a change our monitor
                captured on the official{' '}
                <a
                  href="https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-[var(--accent)] underline-offset-2 hover:underline"
                >
                  VARA Compliance &amp; Risk Management Rulebook
                </a>{' '}
                — a modern self-sealed record (every hash check runs), together with the exact raw
                and normalized text its hashes cover. Nothing in it is invented. Check the math yourself.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLoadSample}
              disabled={sampleLoading || loading}
              className="sp-btn-secondary shrink-0 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <FileSearch className="h-4 w-4 text-[var(--accent)]" />
              {sampleLoading ? 'Loading record…' : 'Load a real record'}
            </button>
          </div>
        </section>

        <section className="sp-card mt-4">
          <label htmlFor="record-json" className="sp-label">
            record.json
          </label>
          <textarea
            id="record-json"
            value={recordText}
            onChange={(event) => setRecordText(event.target.value)}
            placeholder='Paste the contents of record.json here, e.g. { "content": { "current_hash": "sha256:…" }, … }'
            spellCheck={false}
            rows={10}
            className="sp-input w-full resize-y"
            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', lineHeight: 1.6 }}
          />

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <FileField
              id="raw-file"
              label="raw.txt (optional)"
              hint="Checks sha256(raw) against raw_hash."
              fileName={rawName}
              onChange={(event) => handleFile(event, setRawText, setRawName)}
              onClear={() => {
                setRawText(null)
                setRawName('')
              }}
            />
            <FileField
              id="normalized-file"
              label="normalized.txt (optional)"
              hint="Checks sha256(normalized) against current_hash."
              fileName={normalizedName}
              onChange={(event) => handleFile(event, setNormalizedText, setNormalizedName)}
              onClear={() => {
                setNormalizedText(null)
                setNormalizedName('')
              }}
            />
            <FileField
              id="diff-file"
              label="diff.txt (optional)"
              hint="Checks sha256(diff) against the record's diff_hash — the sealed redline. Legacy/no-change records skip it."
              fileName={diffName}
              onChange={(event) => handleFile(event, setDiffText, setDiffName)}
              onClear={() => {
                setDiffText(null)
                setDiffName('')
              }}
            />
            <FileField
              id="token-file"
              label="RFC 3161 token (.tsr, optional)"
              hint="Reports the third-party timestamp offline. Chain-head tokens need the anchored digest below."
              fileName={tokenName}
              onChange={handleTokenFile}
              accept=".tsr,application/timestamp-reply,application/octet-stream"
              onClear={() => {
                setTokenB64(null)
                setTokenName('')
              }}
            />
            {tokenB64 ? (
              <div className="sp-panel-muted p-3">
                <label htmlFor="token-digest" className="sp-label mb-1">
                  Timestamp digest (optional)
                </label>
                <input
                  id="token-digest"
                  type="text"
                  value={tokenDigest}
                  onChange={(event) => setTokenDigest(event.target.value)}
                  placeholder="anchored_head_record_hash from the .tsr.json sidecar"
                  spellCheck={false}
                  className="sp-input w-full"
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}
                />
                <p className="mt-2 text-[0.7rem] leading-snug text-[var(--text-muted)]">
                  The value the token attests. Chain-head tokens (from an
                  evidence pack&apos;s timestamp/ folder) attest the anchored
                  head hash — paste it here. Left empty, the check runs against
                  this record&apos;s own record_hash.
                </p>
              </div>
            ) : null}
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              type="button"
              onClick={handleVerify}
              disabled={loading || sampleLoading}
              className="sp-btn-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Verifying…' : 'Verify'}
            </button>
            <p className="text-xs text-[var(--text-muted)]">
              Everything runs against the bytes you provide.
            </p>
          </div>

          {error ? (
            <p
              role="alert"
              className="mt-4 rounded-lg border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-3 py-2 text-sm text-[var(--danger)]"
            >
              {error}
            </p>
          ) : null}
        </section>

        {hasResult ? (
          <section className="mt-6" aria-live="polite">
            <div
              className="flex items-center gap-3 rounded-[var(--radius-card)] border px-4 py-3"
              style={{
                borderColor: verified ? 'var(--success)' : 'var(--danger)',
                background: verified ? 'rgba(55,211,153,0.08)' : 'rgba(248,113,113,0.08)',
              }}
            >
              {verified ? (
                <ShieldCheck className="h-5 w-5" style={{ color: 'var(--success)' }} />
              ) : (
                <ShieldAlert className="h-5 w-5" style={{ color: 'var(--danger)' }} />
              )}
              <div>
                <p
                  className="text-sm font-semibold"
                  style={{ color: verified ? 'var(--success)' : 'var(--danger)' }}
                >
                  {verified ? 'Verified' : 'Not verified'}
                </p>
                <p className="text-xs text-[var(--text-secondary)]">
                  {verified
                    ? 'Every check that could run passed against the submitted bytes.'
                    : 'At least one check failed or could not be confirmed. See the details below.'}
                </p>
              </div>
            </div>

            <div className="sp-card mt-4">
              <ul className="-my-0">
                {(result.checks || []).map((check) => (
                  <CheckRow key={check.name} check={check} />
                ))}
              </ul>
            </div>

            {result.external_timestamp?.present ? (
              <div className="sp-card mt-4">
                <p className="sp-label mb-2">External RFC 3161 timestamp</p>
                <p className="text-sm text-[var(--text-secondary)]">
                  {result.external_timestamp.verified
                    ? `Token verified offline: the third-party TSA attests the checked digest existed no later than ${result.external_timestamp.timestamp_utc || 'the signed time'}.`
                    : 'Token submitted but not verified — see the token checks below. This never affects the record-integrity result above.'}
                </p>
                {(result.external_timestamp.checks || []).length ? (
                  <ul className="mt-3 -my-0">
                    {result.external_timestamp.checks.map((check) => (
                      <CheckRow key={`ts-${check.name}`} check={check} />
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}

            {result.disclaimer ? (
              <p className="mt-4 text-xs leading-relaxed text-[var(--text-muted)]">
                {result.disclaimer}
              </p>
            ) : null}
          </section>
        ) : null}
      </div>
    </div>
  )
}

function FileField({ id, label, hint, fileName, onChange, onClear, accept = '.txt,text/plain' }) {
  return (
    // focus-within ring: the input is sr-only (focusable, in the tab order —
    // display:none would remove it from both), so the visible affordance
    // shows keyboard focus via the wrapper.
    <div className="sp-panel-muted p-3 focus-within:ring-1 focus-within:ring-[var(--accent)]">
      <label htmlFor={id} className="sp-label mb-1">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <label
          htmlFor={id}
          className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
        >
          <FileUp className="h-4 w-4 shrink-0 text-[var(--accent)]" />
          <span className="truncate" style={{ fontFamily: fileName ? 'var(--font-mono)' : 'inherit' }}>
            {fileName || 'Choose file'}
          </span>
        </label>
        {fileName && onClear ? (
          <button
            type="button"
            onClick={() => {
              const el = document.getElementById(id)
              if (el) el.value = ''
              onClear()
            }}
            aria-label={`Clear ${label}`}
            className="shrink-0 text-[var(--text-muted)] transition-colors hover:text-[var(--text-secondary)]"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </div>
      <input id={id} type="file" accept={accept} onChange={onChange} className="sr-only" />
      <p className="mt-2 text-[0.7rem] leading-snug text-[var(--text-muted)]">{hint}</p>
    </div>
  )
}

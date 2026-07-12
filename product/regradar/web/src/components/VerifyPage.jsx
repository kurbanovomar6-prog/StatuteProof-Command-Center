/**
 * VerifyPage — public, no-login evidence verifier.
 *
 * Paste a record.json (and optionally upload raw.txt / normalized.txt) and this
 * page runs standard SHA-256 over the bytes YOU hold via POST /api/verify. The
 * server never reads its own evidence store — that is the whole point: you do not
 * have to trust StatuteProof, you check the math yourself.
 *
 * Disclaimer: verification confirms record integrity only. Not legal advice.
 */
import { useState } from 'react'
import { ArrowLeft, ShieldCheck, ShieldAlert, Check, X, Minus, FileUp } from 'lucide-react'
import { verifyRecord } from '../api'

const SPEC_HREF = '/api/verify-spec'

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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

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

    setLoading(true)
    try {
      const data = await verifyRecord({
        record,
        raw: rawText ?? undefined,
        normalized: normalizedText ?? undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err.message || 'Verification could not be completed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

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

        <section className="sp-card mt-8">
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
            />
            <FileField
              id="normalized-file"
              label="normalized.txt (optional)"
              hint="Checks sha256(normalized) against current_hash."
              fileName={normalizedName}
              onChange={(event) => handleFile(event, setNormalizedText, setNormalizedName)}
            />
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              type="button"
              onClick={handleVerify}
              disabled={loading}
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

function FileField({ id, label, hint, fileName, onChange }) {
  return (
    <div className="sp-panel-muted p-3">
      <label htmlFor={id} className="sp-label mb-1">
        {label}
      </label>
      <label
        htmlFor={id}
        className="flex cursor-pointer items-center gap-2 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
      >
        <FileUp className="h-4 w-4 text-[var(--accent)]" />
        <span className="truncate" style={{ fontFamily: fileName ? 'var(--font-mono)' : 'inherit' }}>
          {fileName || 'Choose file'}
        </span>
      </label>
      <input id={id} type="file" accept=".txt,text/plain" onChange={onChange} className="hidden" />
      <p className="mt-2 text-[0.7rem] leading-snug text-[var(--text-muted)]">{hint}</p>
    </div>
  )
}

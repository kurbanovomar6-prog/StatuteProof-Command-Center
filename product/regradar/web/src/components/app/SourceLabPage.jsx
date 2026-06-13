import { useState } from 'react'
import { AlertTriangle, CheckCircle, Loader2, Search, ShieldCheck, XCircle } from 'lucide-react'

const STATUS_COLOR = {
  TEST_PASSED: 'text-emerald-300',
  EVIDENCE_CONFIRMED: 'text-emerald-300',
  BASELINE_PENDING: 'text-amber-300',
  MONITORING_CERTIFIED: 'text-emerald-300',
  CERTIFICATION_FAILED: 'text-rose-300',
  NEEDS_HUMAN_REVIEW: 'text-amber-300',
}

export default function SourceLabPage() {
  const [url, setUrl] = useState('')
  const [contentSelector, setContentSelector] = useState('')
  const [waitSelector, setWaitSelector] = useState('')
  const [useJs, setUseJs] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function runTest() {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/api/custom-sources/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          name: url,
          content_selector: contentSelector || undefined,
          wait_for_selector: waitSelector || undefined,
          fetch_method: useJs ? 'playwright' : undefined,
        }),
      })
      const data = await res.json()
      if (!data.ok) {
        setError(data.message || 'Source Lab test failed.')
      } else {
        setResult(data)
      }
    } catch {
      setError('API server not reachable. Start with: python run.py api')
    } finally {
      setLoading(false)
    }
  }

  const certification = result?.certification || {}
  const quality = result?.quality_breakdown || {}
  const components = quality.components || {}
  const penalties = quality.penalties || {}
  const isReady = result?.readiness_status === 'CONFIRMED_ACCESSIBLE'
  const isBlocked = ['BLOCKED', 'UNSUPPORTED', 'NAV_SHELL_ONLY'].includes(result?.readiness_status)

  return (
    <div className="p-5 space-y-5">
      <div className="flex flex-col gap-2">
        <h1 className="text-lg font-bold text-white">Source Lab</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Test one public source at a time. A passing test is not monitoring certification. Evidence and baseline runs are required before active monitoring can be certified.
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_180px_auto]">
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="https://official-source.example/page"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400/50"
          />
          <input
            value={contentSelector}
            onChange={e => setContentSelector(e.target.value)}
            placeholder="content selector"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400/50"
          />
          <input
            value={waitSelector}
            onChange={e => setWaitSelector(e.target.value)}
            placeholder="wait selector"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400/50"
          />
          <button
            onClick={runTest}
            disabled={!url || loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-4 py-2 text-sm font-semibold text-[#07111F] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Test
          </button>
        </div>
        <label className="mt-3 flex items-center gap-2 text-xs text-slate-400">
          <input type="checkbox" checked={useJs} onChange={e => setUseJs(e.target.checked)} />
          Use Playwright rendering for this single source test
        </label>
      </section>

      {error && (
        <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 p-4 text-sm text-rose-200">
          {error}
        </div>
      )}

      {result && (
        <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
          <section className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
            <div className="mb-4 flex items-start gap-3">
              {isReady ? <CheckCircle className="mt-0.5 h-5 w-5 text-emerald-400" /> : isBlocked ? <XCircle className="mt-0.5 h-5 w-5 text-rose-400" /> : <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-400" />}
              <div>
                <h2 className="text-sm font-semibold text-white">{result.readiness_status}</h2>
                <p className="text-xs leading-relaxed text-slate-400">
                  {isReady
                    ? 'Test passed — save evidence to confirm source. This is not monitoring certification.'
                    : result.failure_reason || 'This source needs review before evidence confirmation.'}
                </p>
              </div>
            </div>

            {result.remediation_hint && (
              <div className="mb-4 rounded-lg border border-amber-400/20 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
                {result.remediation_hint}
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Quality score" value={`${result.quality_score || 0}/100`} />
              <Metric label="Evidence level" value={result.evidence_level || 'PREVIEW_ONLY'} />
              <Metric label="Provider" value={result.provider_used || '—'} />
              <Metric label="Normalized chars" value={(result.normalized_length || result.chars || 0).toLocaleString()} />
              <Metric label="Hash" value={result.normalized_hash ? `${result.normalized_hash.slice(0, 16)}…` : '—'} mono />
              <Metric label="Policy" value={result.legal_policy_status || 'PUBLIC_SOURCE_ONLY'} />
            </div>

            {result.normalized_preview && (
              <div className="mt-4">
                <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">Normalized Preview</h3>
                <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs leading-relaxed text-slate-300">{result.normalized_preview}</pre>
              </div>
            )}
          </section>

          <section className="space-y-5">
            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
              <div className="mb-3 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-cyan-300" />
                <h2 className="text-sm font-semibold text-white">Certification</h2>
              </div>
              <p className={`text-sm font-semibold ${STATUS_COLOR[certification.certification_status] || 'text-slate-300'}`}>
                {certification.certification_status || result.certification_status || '—'}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Baseline {certification.baseline_runs_completed || 0}/{certification.baseline_runs_required || 2}
              </p>
              {(certification.remediation_hints || []).map(hint => (
                <p key={hint} className="mt-2 text-xs text-slate-400">{hint}</p>
              ))}
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
              <h2 className="mb-3 text-sm font-semibold text-white">Quality Breakdown</h2>
              <div className="space-y-2">
                {Object.entries(components).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3 text-xs">
                    <span className="text-slate-500">{key.replaceAll('_', ' ')}</span>
                    <span className="font-mono text-slate-300">{value}</span>
                  </div>
                ))}
                {Object.entries(penalties).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3 text-xs">
                    <span className="text-rose-300">{key.replaceAll('_', ' ')}</span>
                    <span className="font-mono text-rose-300">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, mono = false }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5">
      <p className="mb-1 text-[11px] text-slate-500">{label}</p>
      <p className={`truncate text-sm font-semibold text-slate-200 ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  )
}

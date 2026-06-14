import { useMemo, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  FileSearch,
  FileText,
  ListChecks,
  Loader2,
  LockKeyhole,
  RotateCcw,
  Save,
  Search,
  ShieldCheck,
  Wrench,
  XCircle,
} from 'lucide-react'

const JURISDICTIONS = ['UAE Federal', 'Dubai / VARA', 'DIFC / DFSA', 'ADGM / FSRA', 'Other public source']
const SOURCE_TYPES = ['Regulator publication page', 'Regulatory notices', 'Rulebook / legal database', 'Circulars / guidance', 'PDF collection', 'Other public source']

const STATUS_COLOR = {
  TEST_PASSED: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  CONFIRMED_ACCESSIBLE: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  EVIDENCE_CONFIRMED: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  BASELINE_PENDING: 'border-amber-400/25 bg-amber-400/10 text-amber-200',
  MONITORING_CERTIFIED: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-200',
  CERTIFICATION_FAILED: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
  NEEDS_HUMAN_REVIEW: 'border-amber-400/25 bg-amber-400/10 text-amber-200',
  BLOCKED: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
  UNSUPPORTED: 'border-slate-600 bg-slate-800 text-slate-300',
  NAV_SHELL_ONLY: 'border-rose-400/25 bg-rose-400/10 text-rose-200',
}

const STATUS_LABELS = {
  TEST_NOT_RUN: 'Test not run',
  TEST_PASSED: 'Readiness threshold met',
  CONFIRMED_ACCESSIBLE: 'Readiness threshold met',
  EVIDENCE_CONFIRMED: 'Evidence confirmed',
  BASELINE_PENDING: 'Baseline pending',
  BASELINE_REQUIRED: 'Baseline required',
  MONITORING_READY: 'Monitoring ready',
  MONITORING_CERTIFIED: 'Monitoring ready',
  CERTIFICATION_FAILED: 'Activation readiness failed',
  NEEDS_REMEDIATION: 'Needs remediation',
  NEEDS_HUMAN_REVIEW: 'Needs human review',
  NEEDS_REVIEW: 'Needs review',
  BLOCKED: 'Blocked',
  UNSUPPORTED: 'Unsupported',
  NAV_SHELL_ONLY: 'Navigation shell only',
}

const EVIDENCE_LEVEL_LABELS = {
  PREVIEW_ONLY: 'Preview only',
  CERTIFIED_EVIDENCE: 'Evidence confirmed',
}

function statusLabel(value) {
  return STATUS_LABELS[value] || value || 'Not available'
}

function evidenceLevelLabel(value) {
  return EVIDENCE_LEVEL_LABELS[value] || statusLabel(value)
}

function fieldClass(error) {
  return `sp-input ${error ? 'border-rose-400/70' : ''}`
}

function Metric({ label, value, tone = 'slate', mono = false }) {
  const tones = {
    cyan: 'border-cyan-400/20 bg-cyan-400/10',
    emerald: 'border-emerald-400/20 bg-emerald-400/10',
    amber: 'border-amber-400/20 bg-amber-400/10',
    rose: 'border-rose-400/20 bg-rose-400/10',
    slate: 'border-slate-800 bg-slate-950/35',
  }
  return (
    <div className={`rounded-lg border px-3 py-3 ${tones[tone] || tones.slate}`}>
      <p className="mb-1 text-[11px] font-medium text-slate-500">{label}</p>
      <p className={`truncate text-sm font-semibold text-slate-100 ${mono ? 'sp-mono' : ''}`}>{value}</p>
    </div>
  )
}

function ResultIcon({ result }) {
  const status = result?.readiness_status || result?.status
  if (result?.can_activate_monitoring || result?.can_save_for_validation) {
    return <CheckCircle className="h-5 w-5 text-emerald-300" />
  }
  if (['BLOCKED', 'UNSUPPORTED', 'NAV_SHELL_ONLY', 'CERTIFICATION_FAILED'].includes(status)) {
    return <XCircle className="h-5 w-5 text-rose-300" />
  }
  return <AlertTriangle className="h-5 w-5 text-amber-300" />
}

function customSourceLimit(planState) {
  const caps = planState?.active_capabilities || planState?.capabilities || {}
  return Number(caps.customSources ?? caps.custom_sources ?? 0)
}

export default function SourceLabPage({ planState, onChoosePlan }) {
  const [form, setForm] = useState({
    url: '',
    name: '',
    jurisdiction: 'UAE Federal',
    regulator: '',
    sourceType: 'Regulator publication page',
    contentSelector: '',
    waitSelector: '',
    expectedMinLength: 2500,
    useJs: false,
    pdfMode: false,
    adapterFamily: '',
    legalConfirmed: false,
  })
  const [advancedOpen, setAdvancedOpen] = useState(true)
  const [touched, setTouched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [discoveryLoading, setDiscoveryLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)
  const [discovery, setDiscovery] = useState(null)
  const [error, setError] = useState('')
  const [saveMessage, setSaveMessage] = useState('')

  const planAllowsCustom = customSourceLimit(planState) > 0
  const requiredErrors = useMemo(() => {
    const errs = {}
    if (!form.url.trim()) errs.url = 'URL is required.'
    else if (!/^https?:\/\/[^ ]+\.[^ ]+/.test(form.url.trim())) errs.url = 'Enter a public http(s) URL.'
    if (!form.name.trim()) errs.name = 'Source name is required.'
    if (!form.regulator.trim()) errs.regulator = 'Regulator or source owner is required.'
    if (!form.jurisdiction.trim()) errs.jurisdiction = 'Jurisdiction is required.'
    if (!form.sourceType.trim()) errs.sourceType = 'Source type is required.'
    if (!form.legalConfirmed) errs.legalConfirmed = 'Confirm this is a public source before testing.'
    return errs
  }, [form])

  const canTest = Object.keys(requiredErrors).length === 0 && !loading
  const canDiscover = Object.keys(requiredErrors).length === 0 && !discoveryLoading
  const canSave = Boolean(result?.can_save_for_validation) && planAllowsCustom && !saving
  const certification = result?.certification || {}
  const certificationStatus = certification.certification_status || result?.certification_status || 'TEST_NOT_RUN'
  const evidenceLevel = result?.evidence_level || 'PREVIEW_ONLY'
  const activationReadiness = result?.activation_readiness || certificationStatus
  const activateAllowed = Boolean(result?.can_activate_monitoring)
  const baselineDone = result?.baseline_runs_completed ?? certification.baseline_runs_completed ?? 0
  const baselineRequired = result?.baseline_runs_required ?? certification.baseline_runs_required ?? 2

  function set(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  async function runTest() {
    setTouched(true)
    setSaveMessage('')
    if (!canTest) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch('/api/custom-sources/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: form.url.trim(),
          name: form.name.trim(),
          content_selector: form.contentSelector || undefined,
          wait_for_selector: form.waitSelector || undefined,
          expected_min_length: Number(form.expectedMinLength) || undefined,
          pdf_mode: form.pdfMode,
          fetch_method: form.useJs ? 'playwright' : undefined,
          adapter_family: form.adapterFamily || undefined,
          adapter_config: form.adapterFamily ? {
            container_selector: form.contentSelector || result?.dom_investigation?.content_selector || 'main',
            content_selector: form.contentSelector || result?.dom_investigation?.content_selector || undefined,
            item_selector: result?.dom_investigation?.item_selector || undefined,
          } : undefined,
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

  async function runDiscovery() {
    setTouched(true)
    setSaveMessage('')
    if (!canDiscover) return
    setDiscoveryLoading(true)
    setError('')
    setDiscovery(null)
    try {
      const res = await fetch('/api/custom-sources/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: form.url.trim(),
          use_js: form.useJs,
          network: false,
          sitemap: true,
          feeds: true,
          documents: true,
          max_links: 50,
          max_depth: 1,
        }),
      })
      const data = await res.json()
      if (!data.ok) {
        setError(data.message || 'Source discovery failed.')
      } else {
        setDiscovery(data.discovery)
      }
    } catch {
      setError('API server not reachable. Start with: python run.py api')
    } finally {
      setDiscoveryLoading(false)
    }
  }

  function applyInvestigationSuggestion(adapterFamily) {
    const investigation = result?.dom_investigation || {}
    setForm(prev => ({
      ...prev,
      adapterFamily: adapterFamily || investigation.recommended_adapter_family || prev.adapterFamily,
      contentSelector: investigation.content_selector || prev.contentSelector,
      waitSelector: investigation.wait_selector || prev.waitSelector,
      useJs: true,
      pdfMode: adapterFamily === 'pdf_listing' || investigation.recommended_adapter_family === 'pdf_listing' || prev.pdfMode,
    }))
    setSaveMessage('Extraction settings updated from DOM investigation. Run the no-save test again.')
  }

  async function saveSource() {
    if (!canSave) return
    setSaving(true)
    setError('')
    setSaveMessage('')
    try {
      const res = await fetch('/api/custom-sources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: form.url.trim(),
          name: form.name.trim(),
          category: form.sourceType,
          jurisdiction: form.jurisdiction,
          legal_confirmed: form.legalConfirmed,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || !data.ok) {
        setError(data.message || 'Source could not be saved for validation.')
      } else {
        setSaveMessage(data.message || 'Source saved for validation. Monitoring is not ready yet.')
      }
    } catch {
      setError('API server not reachable. Source was not saved.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-full bg-[#07111F] p-5 pb-10">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="sp-kicker mb-3">
            <FileSearch className="h-4 w-4" />
            Custom source readiness
          </div>
          <h1 className="text-2xl font-semibold text-white">Source Lab</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
            Test one public official source at a time. A passing test is a readiness signal only;
            evidence records and baseline runs are required before monitoring can be approved for activation.
          </p>
        </div>
        {!planAllowsCustom && (
          <div className="rounded-lg border border-amber-400/25 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
            Custom source activation requires UAE Monitor or Consultant scope.
          </div>
        )}
      </div>

      <div className="grid gap-5 xl:grid-cols-[420px_1fr]">
        <section className="sp-panel p-5">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Source test request</h2>
            <span className="rounded-md border border-cyan-400/25 bg-cyan-400/10 px-2.5 py-1 text-[11px] font-semibold text-cyan-200">
              No-save test
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <label className="sp-label">Source URL *</label>
              <input
                value={form.url}
                onChange={e => set('url', e.target.value)}
                placeholder="https://regulator.gov/publications"
                className={fieldClass(touched && requiredErrors.url)}
              />
              {touched && requiredErrors.url && <p className="mt-1 text-xs text-rose-300">{requiredErrors.url}</p>}
            </div>

            <div>
              <label className="sp-label">Source name *</label>
              <input
                value={form.name}
                onChange={e => set('name', e.target.value)}
                placeholder="CBUAE regulations page"
                className={fieldClass(touched && requiredErrors.name)}
              />
              {touched && requiredErrors.name && <p className="mt-1 text-xs text-rose-300">{requiredErrors.name}</p>}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="sp-label">Jurisdiction *</label>
                <select value={form.jurisdiction} onChange={e => set('jurisdiction', e.target.value)} className={fieldClass(touched && requiredErrors.jurisdiction)}>
                  {JURISDICTIONS.map(item => <option key={item}>{item}</option>)}
                </select>
              </div>
              <div>
                <label className="sp-label">Source type *</label>
                <select value={form.sourceType} onChange={e => set('sourceType', e.target.value)} className={fieldClass(touched && requiredErrors.sourceType)}>
                  {SOURCE_TYPES.map(item => <option key={item}>{item}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="sp-label">Regulator / entity *</label>
              <input
                value={form.regulator}
                onChange={e => set('regulator', e.target.value)}
                placeholder="Central Bank of the UAE"
                className={fieldClass(touched && requiredErrors.regulator)}
              />
              {touched && requiredErrors.regulator && <p className="mt-1 text-xs text-rose-300">{requiredErrors.regulator}</p>}
            </div>

            <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/35 p-3">
              <input
                type="checkbox"
                checked={form.legalConfirmed}
                onChange={e => set('legalConfirmed', e.target.checked)}
                className="mt-0.5 h-4 w-4 accent-[#16D9F5]"
              />
              <span className="text-xs leading-relaxed text-slate-400">
                I confirm this is a public official source or public material we are authorized to review.
                Login-protected, paywalled, CAPTCHA-gated, private portal, and secret-bearing URLs are not supported.
              </span>
            </label>
            {touched && requiredErrors.legalConfirmed && <p className="text-xs text-rose-300">{requiredErrors.legalConfirmed}</p>}

            <button
              type="button"
              onClick={() => setAdvancedOpen(open => !open)}
              className="flex w-full items-center justify-between rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-2 text-sm font-semibold text-slate-200"
            >
              Advanced extraction options
              <ChevronDown className={`h-4 w-4 transition-transform ${advancedOpen ? 'rotate-180' : ''}`} />
            </button>

            {advancedOpen && (
              <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-950/25 p-3">
                <div>
                  <label className="sp-label">Content selector</label>
                  <input value={form.contentSelector} onChange={e => set('contentSelector', e.target.value)} placeholder="main, article, #content" className="sp-input" />
                </div>
                <div>
                  <label className="sp-label">Wait selector</label>
                  <input value={form.waitSelector} onChange={e => set('waitSelector', e.target.value)} placeholder=".publication-list" className="sp-input" />
                </div>
                <div>
                  <label className="sp-label">Expected minimum text length</label>
                  <input
                    type="number"
                    min="500"
                    step="500"
                    value={form.expectedMinLength}
                    onChange={e => set('expectedMinLength', e.target.value)}
                    className="sp-input"
                  />
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <label className="flex items-center gap-2 rounded-md border border-slate-800 bg-[#07111F]/70 px-3 py-2 text-xs text-slate-300">
                    <input type="checkbox" checked={form.useJs} onChange={e => set('useJs', e.target.checked)} className="accent-[#16D9F5]" />
                    JS rendering
                  </label>
                  <label className="flex items-center gap-2 rounded-md border border-slate-800 bg-[#07111F]/70 px-3 py-2 text-xs text-slate-300">
                    <input type="checkbox" checked={form.pdfMode} onChange={e => set('pdfMode', e.target.checked)} className="accent-[#16D9F5]" />
                    PDF mode
                  </label>
                </div>
              </div>
            )}

            <button
              onClick={runTest}
              disabled={!canTest}
              className="sp-btn-primary w-full justify-center disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Test Source
            </button>
            <button
              onClick={runDiscovery}
              disabled={!canDiscover}
              className="sp-btn-secondary w-full justify-center disabled:cursor-not-allowed disabled:opacity-45"
            >
              {discoveryLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSearch className="h-4 w-4" />}
              Discover endpoints
            </button>
          </div>
        </section>

        <section className="space-y-5">
          {!result && !error && (
            <div className="sp-panel flex min-h-[360px] items-center justify-center p-8 text-center">
              <div className="max-w-md">
                <ShieldCheck className="mx-auto mb-4 h-10 w-10 text-cyan-200" />
                <h2 className="text-lg font-semibold text-white">Ready for a no-save readiness test</h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">
                  The result will show readiness status, quality score, extraction provider,
                  normalized length, hash preview, evidence level, activation readiness,
                  warnings, remediation hints, and normalized text preview.
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-rose-500/25 bg-rose-500/10 p-4 text-sm text-rose-200">
              {error}
            </div>
          )}

          {saveMessage && (
            <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-4 text-sm text-emerald-100">
              {saveMessage}
            </div>
          )}

          {discovery && (
            <div className="sp-panel p-5">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-base font-semibold text-white">Discovery mode</h2>
                  <p className="mt-1 max-w-2xl text-xs leading-relaxed text-slate-400">
                    Endpoint candidates are inactive until no-save, proof, baseline, and review gates pass.
                  </p>
                </div>
                <span className="rounded-md border border-cyan-400/25 bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-100">
                  {(discovery.recommended_activation_paths || []).length} candidates
                </span>
              </div>
              <div className="grid gap-3 md:grid-cols-4">
                <Metric label="Sitemaps" value={(discovery.sitemap_urls || []).length} tone="cyan" />
                <Metric label="Feeds" value={(discovery.feed_urls || []).length} />
                <Metric label="Documents" value={(discovery.document_links || []).length} />
                <Metric label="Same-domain URLs" value={(discovery.same_domain_candidate_urls || []).length} />
              </div>
              {(discovery.recommended_activation_paths || []).length > 0 && (
                <div className="mt-4 space-y-2">
                  {(discovery.recommended_activation_paths || []).slice(0, 6).map(item => (
                    <div key={`${item.candidate_url}-${item.adapter_family}`} className="rounded-lg border border-slate-800 bg-slate-950/35 p-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-100">{item.title || item.candidate_url}</p>
                          <p className="mt-1 break-all text-xs text-slate-500">{item.candidate_url}</p>
                        </div>
                        <span className="shrink-0 rounded-md border border-slate-700 px-2 py-1 text-[11px] font-semibold text-slate-300">
                          {item.adapter_family || 'adapter'} · {item.confidence || 0}/100
                        </span>
                      </div>
                      <div className="mt-2 grid gap-2 md:grid-cols-3">
                        <Metric label="Next action" value={item.next_action || 'manual_review'} />
                        <Metric label="Noise risk" value={item.noise_risk || 'unknown'} tone={item.noise_risk === 'high' ? 'rose' : item.noise_risk === 'low' ? 'emerald' : 'amber'} />
                        <Metric label="Source-health" value={item.source_health_risk || 'unknown'} tone={item.source_health_risk === 'high' ? 'rose' : item.source_health_risk === 'low' ? 'emerald' : 'amber'} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {result && (
            <>
              <div className="sp-panel p-5">
                <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-3">
                    <ResultIcon result={result} />
                    <div>
                      <h2 className="text-base font-semibold text-white">{result.status_label || result.readiness_status}</h2>
                      <p className="mt-1 max-w-2xl text-xs leading-relaxed text-slate-400">
                        {result.can_save_for_validation
                          ? 'Readiness threshold met. Save queues this source for evidence validation. This is not monitoring approval.'
                          : result.failure_reason || 'This source needs remediation before evidence validation.'}
                      </p>
                    </div>
                  </div>
                  <span className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${STATUS_COLOR[result.readiness_status] || STATUS_COLOR[certificationStatus] || STATUS_COLOR.UNSUPPORTED}`}>
                    {statusLabel(result.readiness_status || result.status)}
                  </span>
                </div>

                {result.remediation_hint && (
                  <div className="mb-4 rounded-lg border border-amber-400/25 bg-amber-400/10 px-3 py-2 text-xs leading-relaxed text-amber-100">
                    {result.remediation_hint}
                  </div>
                )}

                <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-4">
                  <Metric label="Quality score" value={`${result.quality_score || 0}/100`} tone={result.quality_score >= 70 ? 'emerald' : result.quality_score >= 45 ? 'amber' : 'rose'} />
                  <Metric label="Extraction provider" value={result.provider_used || result.extraction_method || '—'} tone="cyan" />
                  <Metric label="Normalized length" value={(result.normalized_length || result.chars || 0).toLocaleString()} />
                  <Metric label="Hash preview" value={result.normalized_hash ? `${result.normalized_hash.slice(0, 16)}...` : '—'} mono />
                  <Metric label="Evidence level" value={evidenceLevelLabel(evidenceLevel)} tone={evidenceLevel === 'PREVIEW_ONLY' ? 'amber' : 'emerald'} />
                  <Metric label="Activation readiness" value={statusLabel(activationReadiness)} tone={activateAllowed ? 'emerald' : 'amber'} />
                  <Metric label="Baseline" value={`${baselineDone}/${baselineRequired}`} />
                  <Metric label="Policy" value={result.legal_policy_status || 'PUBLIC_SOURCE_ONLY'} />
                  <Metric label="Failure code" value={result.failure_code || '—'} tone={result.failure_code ? 'amber' : 'slate'} />
                  <Metric label="Noise risk" value={result.noise_risk || 'unknown'} tone={result.noise_risk === 'high' ? 'rose' : result.noise_risk === 'low' ? 'emerald' : 'amber'} />
                  <Metric label="Source-health risk" value={result.source_health_risk || 'unknown'} tone={result.source_health_risk === 'high' ? 'rose' : result.source_health_risk === 'low' ? 'emerald' : 'amber'} />
                </div>

                {result.dom_investigation && (
                  <div className="mt-4 rounded-lg border border-cyan-400/20 bg-cyan-400/10 p-3">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold text-cyan-100">DOM investigation</p>
                        <p className="mt-1 text-xs leading-relaxed text-cyan-100/75">
                          {result.dom_investigation.why_selector_was_chosen || 'Selector recommendation is available for a retry test.'}
                        </p>
                      </div>
                      <span className="rounded-md border border-cyan-400/25 px-2 py-1 text-[11px] font-semibold text-cyan-100">
                        {result.dom_investigation.detected_page_type || 'unknown'}
                      </span>
                    </div>
                    <div className="grid gap-2 md:grid-cols-3">
                      <Metric label="Recommended adapter" value={result.dom_investigation.recommended_adapter_name || result.dom_investigation.recommended_adapter_family || '—'} tone="cyan" />
                      <Metric label="Content selector" value={result.dom_investigation.content_selector || '—'} />
                      <Metric label="Selector confidence" value={`${result.dom_investigation.selector_confidence || 0}/100`} />
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-4">
                      <button type="button" onClick={() => applyInvestigationSuggestion(result.dom_investigation.recommended_adapter_family)} className="sp-btn-secondary justify-center py-2 text-xs">
                        <RotateCcw className="h-3.5 w-3.5" />
                        Retry with JS
                      </button>
                      <button type="button" onClick={() => applyInvestigationSuggestion('listing')} className="sp-btn-secondary justify-center py-2 text-xs">
                        <ListChecks className="h-3.5 w-3.5" />
                        Try listing adapter
                      </button>
                      <button type="button" onClick={() => applyInvestigationSuggestion('pdf_listing')} className="sp-btn-secondary justify-center py-2 text-xs">
                        <FileText className="h-3.5 w-3.5" />
                        Try PDF listing
                      </button>
                      <button type="button" disabled className="inline-flex min-h-9 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/55 px-3 py-2 text-xs font-semibold text-slate-500" title="Roadmap: marking remediation will write to the gated source work queue after review.">
                        <Wrench className="h-3.5 w-3.5" />
                        Mark remediation
                      </button>
                    </div>
                  </div>
                )}

                {(result.warnings?.length > 0 || result.nav_shell_detected || result.hash_collision) && (
                  <div className="mt-4 rounded-lg border border-amber-400/20 bg-amber-400/10 p-3">
                    <p className="mb-2 text-xs font-semibold text-amber-100">Warnings</p>
                    <ul className="space-y-1 text-xs text-amber-100/80">
                      {result.nav_shell_detected && <li>Nav shell detected: extracted text may be navigation, not regulatory content.</li>}
                      {result.hash_collision && <li>Hash collision detected with {result.collision_source_id || 'another source'}.</li>}
                      {(result.warnings || []).map(warning => <li key={warning}>{warning}</li>)}
                    </ul>
                  </div>
                )}

                {result.normalized_preview && (
                  <div className="mt-4">
                    <h3 className="mb-2 text-xs font-semibold text-slate-400">Normalized preview</h3>
                    <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs leading-relaxed text-slate-300">
                      {result.normalized_preview}
                    </pre>
                  </div>
                )}
              </div>

              <div className="sp-panel p-5">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold text-white">Activation gate</h2>
                    <p className="mt-1 text-xs leading-relaxed text-slate-500">
                      A source can be saved only after a passing test. Monitoring activation requires evidence and readiness gates.
                    </p>
                  </div>
                  {!planAllowsCustom && (
                    <button onClick={onChoosePlan} className="sp-btn-secondary py-2 text-xs">
                      Upgrade for custom sources
                    </button>
                  )}
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <button
                    onClick={saveSource}
                    disabled={!canSave}
                    className="sp-btn-primary justify-center disabled:cursor-not-allowed disabled:opacity-45"
                    title={!planAllowsCustom ? 'Custom sources require UAE Monitor or Consultant scope.' : !result.can_save_for_validation ? 'Save is enabled only when the source can be queued for validation.' : 'Save source for validation'}
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Save Source
                  </button>
                  <button
                    disabled
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/55 px-4 py-2 text-sm font-semibold text-slate-500"
                    title="Activation requires evidence records and monitoring readiness approval."
                  >
                    <LockKeyhole className="h-4 w-4" />
                    Activate Monitoring
                  </button>
                  <button
                    disabled
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/55 px-4 py-2 text-sm font-semibold text-slate-500"
                    title="Saved baseline requires the evidence-save workflow and repeat baseline gate."
                  >
                    <LockKeyhole className="h-4 w-4" />
                    Save baseline
                  </button>
                  <button
                    disabled={!activateAllowed}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-950/40 px-4 py-2 text-sm font-semibold text-slate-500"
                    title="Delivery requires approved brief and integration setup."
                  >
                    Delivery requires approved brief
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

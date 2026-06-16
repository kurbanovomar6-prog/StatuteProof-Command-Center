import { useState, useEffect, useRef } from 'react'
import { Plus, X, Loader2, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'
import { sources as sourcesApi } from '../../api'
import { getWorkspaceProfile } from '../../data/workspaceProfile'

// ── status display helpers ────────────────────────────────────────────────────

const INTAKE_STATUS_LABELS = {
  CONFIRMED_ACCESSIBLE:  'Readiness threshold met',
  JS_RENDERING_NEEDED:   'JS rendering needed',
  PDF_EXTRACTION_NEEDED: 'PDF extraction needed',
  NAV_SHELL_ONLY:        'Nav shell — selector needed',
  QUALITY_DROP:          'Quality below threshold',
  NEEDS_SELECTOR_REVIEW: 'Selector review needed',
  UNSUPPORTED:           'Not supported',
  BLOCKED:               'Blocked',
  // old api/source-test statuses (fallback compat)
  PASS:                  'Readiness threshold met',
  NEEDS_ADAPTER:         'Needs adapter',
  FAILED:                'Failed',
}

const INTAKE_STATUS_COLOR = {
  CONFIRMED_ACCESSIBLE:  'text-emerald-400',
  JS_RENDERING_NEEDED:   'text-amber-400',
  PDF_EXTRACTION_NEEDED: 'text-amber-400',
  NAV_SHELL_ONLY:        'text-rose-400',
  QUALITY_DROP:          'text-amber-400',
  NEEDS_SELECTOR_REVIEW: 'text-amber-400',
  UNSUPPORTED:           'text-slate-400',
  BLOCKED:               'text-rose-400',
  PASS:                  'text-emerald-400',
  NEEDS_ADAPTER:         'text-amber-400',
  FAILED:                'text-rose-400',
}

const INTAKE_STATUS_BG = {
  CONFIRMED_ACCESSIBLE:  'bg-emerald-500/10 border-emerald-500/20',
  JS_RENDERING_NEEDED:   'bg-amber-500/10 border-amber-500/20',
  PDF_EXTRACTION_NEEDED: 'bg-amber-500/10 border-amber-500/20',
  NAV_SHELL_ONLY:        'bg-rose-500/10 border-rose-500/20',
  QUALITY_DROP:          'bg-amber-500/10 border-amber-500/20',
  NEEDS_SELECTOR_REVIEW: 'bg-amber-500/10 border-amber-500/20',
  UNSUPPORTED:           'bg-slate-700/50 border-slate-600',
  BLOCKED:               'bg-rose-500/10 border-rose-500/20',
  PASS:                  'bg-emerald-500/10 border-emerald-500/20',
  NEEDS_ADAPTER:         'bg-amber-500/10 border-amber-500/20',
  FAILED:                'bg-rose-500/10 border-rose-500/20',
}

// legacy source table styles
const HEALTH_STYLE = {
  PASS:                 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  MONITOR_OK:           'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  'Evidence confirmed': 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  Review:               'text-amber-400   bg-amber-500/10   border-amber-500/20',
  'Not yet started':     'text-slate-400   bg-slate-700      border-slate-600',
  'Source health issue': 'text-amber-400   bg-amber-500/10   border-amber-500/20',
  Limited:              'text-slate-400   bg-slate-700      border-slate-600',
}
const STATUS_STYLE = {
  Confirmed:        'text-emerald-400',
  'Readiness supported': 'text-emerald-400',
  'Under validation': 'text-amber-400',
  Limited:          'text-amber-400',
  Partial:          'text-slate-400',
  'Needs adapter':  'text-amber-400',
  'Needs remediation': 'text-amber-400',
  'Monitoring not started': 'text-slate-400',
}

const FILTERS   = ['All', 'Readiness supported', 'Needs remediation', 'Monitoring not started', 'Limited', 'Partial', 'Needs adapter', 'User source']
const MARKETS   = ['UAE', 'DIFC', 'ADGM', 'Other UAE source']
const CATEGORIES = [
  'Central bank', 'Financial regulator', 'Crypto regulator', 'AML authority',
  'Capital markets', 'Tax authority', 'Legal database', 'Other',
]

const TEST_STEPS = [
  'Checking URL safety…',
  'Fetching page content…',
  'Extracting regulatory text…',
  'Evaluating extraction quality…',
]

const REMEDIATION_SOURCE_IDS = new Set([
  'AE-dubai-financial-services-authority-dfsa',
  'AE-dfsa-notices',
  'AE-difc-laws-and-regulations',
  'AE-uae-financial-intelligence-unit-uaefiu',
])

function statusFromApiSource(row) {
  if (REMEDIATION_SOURCE_IDS.has(row.source_id) || row.status === 'remediation') return 'Needs remediation'
  if (row.change_status === 'FAILED' || row.change_status === 'QUALITY_DROP') return 'Needs remediation'
  if (!row.last_run_at || row.change_status === 'NOT_RUN') return 'Monitoring not started'
  return 'Readiness supported'
}

function healthFromApiSource(row) {
  if (row.change_status === 'FAILED' || row.change_status === 'QUALITY_DROP') return 'Source health issue'
  if (!row.last_run_at || row.change_status === 'NOT_RUN') return 'Not yet started'
  return 'MONITOR_OK'
}

function mapApiSource(row) {
  return {
    id: row.source_id,
    source_id: row.source_id,
    url: row.url,
    name: row.name || row.source_id || 'Official source',
    market: 'UAE',
    flag: '🇦🇪',
    category: row.category || 'Official source',
    status: statusFromApiSource(row),
    extraction: row.extraction_quality || 'UNKNOWN',
    lastChecked: row.last_run_at || '',
    health: healthFromApiSource(row),
    accessStatus: row.access_status || 'unknown',
    changeStatus: row.change_status || 'NOT_RUN',
  }
}

// ── localStorage fallback (for dev mode / offline) ───────────────────────────

function loadLocalCustomSources() {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    return Array.isArray(p.customSources) ? p.customSources : []
  } catch { return [] }
}

function saveLocalCustomSource(source) {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    p.customSources = [...(p.customSources || []), source]
    localStorage.setItem('regradar_workspace_profile', JSON.stringify(p))
  } catch (e) { console.warn('localStorage fallback failed', e) }
}

// ── component ─────────────────────────────────────────────────────────────────

export default function SourcesPage({ onAddCustomSource }) {
  const profile = getWorkspaceProfile()

  const [filter, setFilter]               = useState('All')
  const [showModal, setShowModal]         = useState(false)
  const [form, setForm]                   = useState({ url: '', market: profile.markets[0] || '', category: '', notes: '' })
  const [formErrors, setFormErrors]       = useState({})
  const [testPhase, setTestPhase]         = useState('idle')   // idle | testing | result | saving | saved | error
  const [testResult, setTestResult]       = useState(null)
  const [testError, setTestError]         = useState('')
  const [legalConfirmed, setLegalConfirmed] = useState(false)
  const [saveError, setSaveError]         = useState('')
  const [stepIndex, setStepIndex]         = useState(0)
  const [customSources, setCustomSources] = useState(loadLocalCustomSources)
  const [realSources, setRealSources]     = useState([])
  const [sourcesLoading, setSourcesLoading] = useState(true)
  const [sourcesError, setSourcesError]   = useState('')
  const stepTimer                         = useRef(null)

  useEffect(() => {
    if (testPhase === 'testing') {
      stepTimer.current = setInterval(() => {
        setStepIndex(i => (i + 1) % TEST_STEPS.length)
      }, 1200)
    } else {
      clearInterval(stepTimer.current)
    }
    return () => clearInterval(stepTimer.current)
  }, [testPhase])

  useEffect(() => {
    let active = true
    sourcesApi.status('AE')
      .then(data => {
        if (!active) return
        setRealSources(Array.isArray(data.sources) ? data.sources.map(mapApiSource) : [])
        setSourcesError('')
      })
      .catch(err => {
        if (!active) return
        setSourcesError(err.message || 'Could not load source status.')
        setRealSources([])
      })
      .finally(() => {
        if (active) setSourcesLoading(false)
      })
    return () => { active = false }
  }, [])

  const filteredReal = realSources.filter(s => {
    if (filter === 'User source') return false
    if (filter === 'All') return true
    if (filter === 'Readiness supported') return sourceStatusLabel(s.status) === 'Readiness supported'
    if (filter === 'Needs remediation') return s.status === 'Needs remediation'
    if (filter === 'Monitoring not started') return s.status === 'Monitoring not started'
    if (filter === 'Needs adapter') return s.status === 'Needs adapter' || s.extraction?.includes('adapter') || s.extraction?.includes('Geo')
    return s.status === filter
  })

  const filteredCustom = customSources.filter(s => {
    if (filter === 'All' || filter === 'User source') return true
    if (filter === 'Readiness supported') return sourceStatusLabel(s.status) === 'Readiness supported'
    if (filter === 'Needs remediation') return s.status === 'Needs remediation'
    if (filter === 'Needs adapter') return s.status === 'Needs adapter'
    return s.status === filter
  })

  const allSources = [...filteredReal, ...filteredCustom.map(s => ({ ...s, userSource: true }))]

  function resetModal() {
    setTestPhase('idle')
    setTestResult(null)
    setTestError('')
    setSaveError('')
    setFormErrors({})
    setLegalConfirmed(false)
    setForm({ url: '', market: profile.markets[0] || '', category: '', notes: '' })
  }

  function validate() {
    const errs = {}
    if (!form.url.trim()) errs.url = 'URL is required.'
    else if (!/^https?:\/\//.test(form.url)) errs.url = 'Enter a valid URL starting with http(s)://'
    if (!form.market.trim())   errs.market   = 'Market is required.'
    if (!form.category.trim()) errs.category = 'Category is required.'
    return errs
  }

  // ── test source using new /api/custom-sources/test endpoint ──────────────
  async function handleTest() {
    const errs = validate()
    if (Object.keys(errs).length) { setFormErrors(errs); return }
    setStepIndex(0)
    setTestPhase('testing')
    setTestError('')
    setLegalConfirmed(false)

    try {
      const res  = await fetch('/api/custom-sources/test', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ url: form.url, name: form.url }),
      })
      const data = await res.json()
      if (data.ok) {
        setTestResult(data)
        setTestPhase('result')
      } else {
        setTestError(data.message || 'Source test failed.')
        setTestPhase('idle')
      }
    } catch {
      setTestError('API server not reachable. Start with: python run.py api')
      setTestPhase('idle')
    }
  }

  // ── save source using /api/custom-sources endpoint ────────────────────────
  async function handleSaveSource() {
    if (!testResult?.can_save_for_validation) return
    if (!legalConfirmed) return
    setSaveError('')
    setTestPhase('saving')

    let savedViaBackend = false
    try {
      const res = await fetch('/api/custom-sources', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          url:          form.url,
          name:         form.url,
          category:     form.category,
          jurisdiction: form.market,
          legal_confirmed: legalConfirmed,
        }),
      })
      const data = await res.json()
      if (data.ok) savedViaBackend = true
      else {
        setSaveError(data.message || 'Backend save failed. Source was not activated.')
        setTestPhase('result')
        return
      }
    } catch {
      setSaveError('API server not reachable — source saved locally only.')
    }

    // Always keep in local state for UI display
    const localSource = {
      id:          `user-${Date.now()}`,
      url:         form.url,
      name:        (() => { try { return new URL(form.url).hostname } catch { return form.url } })(),
      market:      form.market,
      category:    form.category,
      status:      savedViaBackend ? 'Under validation' : 'Under validation',
      extraction:  testResult.extraction_method || 'HTML',
      lastChecked: 'Just added',
      health:      savedViaBackend ? 'Review' : 'Review',
      userSource:  true,
    }
    saveLocalCustomSource(localSource)
    setCustomSources(cs => [...cs, localSource])
    setTestPhase('saved')
  }

  const inputCls = field =>
    `w-full bg-slate-900 border rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-[#16D9F5]/50 transition ${
      formErrors[field] ? 'border-rose-500/60' : 'border-slate-700'
    }`

  function sourceStatusLabel(status) {
    if (status === 'Active' || status === 'Validated' || status === 'Confirmed') return 'Readiness supported'
    return status
  }

  function sourceHealthLabel(health) {
    return health === 'PASS' ? 'Evidence confirmed' : health
  }

  function lastCheckedLabel(source) {
    if (source.userSource) return source.lastChecked || 'Saved for validation'
    if (!source.lastChecked) return 'Monitoring not yet started'
    try {
      return new Date(source.lastChecked).toLocaleString('en-GB', { timeZone: 'UTC', dateStyle: 'medium', timeStyle: 'short' }) + ' UTC'
    } catch {
      return source.lastChecked
    }
  }

  // ── result panel helpers ──────────────────────────────────────────────────

  const statusLabel = testResult
    ? (INTAKE_STATUS_LABELS[testResult.status] || testResult.status)
    : ''

  const isGood    = testResult?.can_save_for_validation === true || testResult?.status === 'CONFIRMED_ACCESSIBLE' || testResult?.status === 'PASS'
  const isFailed  = testResult?.status === 'BLOCKED' || testResult?.status === 'FAILED' || testResult?.status === 'UNSUPPORTED'
  const needsWork = !isGood && !isFailed

  const canSaveForValidation = testResult?.can_save_for_validation === true
  const saveEnabled  = canSaveForValidation && legalConfirmed

  return (
    <div className="p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h1 className="text-lg font-bold text-white mb-1">Source Map</h1>
          <p className="text-sm text-slate-400">
            {profile.markets.length > 0
              ? `Based on your saved profile: ${profile.markets.join(', ')}${profile.topics.length ? ` · ${profile.topics.slice(0, 4).join(', ')}` : ''}`
              : 'Profile source map preview — select markets in Settings to filter.'}
          </p>
        </div>
        <button
          onClick={() => {
            if (onAddCustomSource) {
              onAddCustomSource()
            } else {
              resetModal()
              setShowModal(true)
            }
          }}
          className="flex items-center gap-1.5 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add custom source
        </button>
      </div>

      {/* Info banner */}
      <div className="bg-[#0D1B2E] border border-cyan-400/20 rounded-xl p-5 mb-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white mb-1">Sources are checked before monitoring activates.</h2>
            <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
              StatuteProof tests public official sources for accessibility, extraction quality, and content depth.
              Sources are marked readiness-supported only when meaningful regulatory text is extracted and hashed.
              Custom sources are saved for readiness review — monitoring is not activated automatically.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              ['Readiness supported', 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'],
              ['Under validation', 'border-amber-400/25 bg-amber-400/10 text-amber-300'],
              ['Needs adapter', 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200'],
              ['Limited', 'border-slate-600 bg-slate-800 text-slate-300'],
            ].map(([label, cls]) => (
              <span key={label} className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${cls}`}>
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap mb-4">
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              filter === f
                ? 'bg-[#16D9F5]/10 text-[#16D9F5] border-[#16D9F5]/30'
                : 'text-slate-400 border-slate-700 hover:border-slate-600 hover:text-slate-300'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl overflow-hidden">
        {sourcesLoading ? (
          <div className="px-5 py-10 text-center">
            <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-[#16D9F5]" />
            <p className="text-sm text-slate-400 mb-1">Loading live source status…</p>
            <p className="text-xs text-slate-600">Authenticated source map uses the API, not sample source rows.</p>
          </div>
        ) : sourcesError ? (
          <div className="px-5 py-10 text-center">
            <AlertTriangle className="mx-auto mb-3 h-5 w-5 text-amber-400" />
            <p className="text-sm text-amber-300 mb-1">Could not load live source status.</p>
            <p className="text-xs text-slate-600">{sourcesError}</p>
          </div>
        ) : allSources.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-800/60 text-left">
                  {['Source', 'Market', 'Category', 'Status', 'Extraction', 'Last checked', 'Health'].map(h => (
                    <th key={h} className="px-4 py-3 text-slate-400 font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {allSources.map(s => (
                  <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-white whitespace-nowrap">
                      {s.name}
                      {s.userSource && (
                        <span className="ml-2 text-[10px] text-[#16D9F5] border border-[#16D9F5]/30 px-1.5 py-0.5 rounded-full">
                          User source
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-300 whitespace-nowrap">{s.flag} {s.market}</td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{s.category}</td>
                    <td className={`px-4 py-3 font-medium whitespace-nowrap ${STATUS_STYLE[sourceStatusLabel(s.status)] || STATUS_STYLE[s.status] || 'text-slate-400'}`}>
                      {sourceStatusLabel(s.status)}
                    </td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{s.extraction}</td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{lastCheckedLabel(s)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${HEALTH_STYLE[s.health] || 'text-slate-400 bg-slate-700 border-slate-600'}`}>
                        {sourceHealthLabel(s.health)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-5 py-10 text-center">
            <p className="text-sm text-slate-400 mb-1">No sources match the current filter.</p>
            <p className="text-xs text-slate-600">Try changing your filter or test a custom source. No sample sources are shown in authenticated source map.</p>
          </div>
        )}
      </div>

      {/* Add source modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0D1B2E] border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl">

            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-white">Test Custom Source</h3>
              <button onClick={() => { setShowModal(false); resetModal() }} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* PHASE: saved */}
            {testPhase === 'saved' && (
              <div className="px-6 py-8 text-center">
                <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                <p className="text-sm font-semibold text-white mb-1">
                  Source saved for validation.
                </p>
                <p className="text-xs text-slate-400 mb-3">
                  The source appears in your source map. Monitoring activates only after evidence validation is complete.
                </p>
                {saveError && (
                  <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2 mb-4">
                    {saveError}
                  </p>
                )}
                <div className="text-xs text-slate-500 bg-slate-800/50 rounded-lg px-3 py-2 mb-4 text-left">
                  <p className="font-medium text-slate-400 mb-1">Evidence note</p>
                  <p>This test met the readiness threshold without writing an evidence record. A full evidence record with hash, snapshot, and proof artifact is created during the first scheduled monitoring run.</p>
                </div>
                <button
                  onClick={() => { setShowModal(false); resetModal() }}
                  className="text-xs font-medium text-[#16D9F5] border border-[#16D9F5]/30 hover:border-[#16D9F5]/60 px-4 py-2 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}

            {/* PHASE: saving */}
            {testPhase === 'saving' && (
              <div className="px-6 py-8 text-center">
                <Loader2 className="w-10 h-10 text-[#16D9F5] animate-spin mx-auto mb-3" />
                <p className="text-sm text-slate-300">Saving source…</p>
              </div>
            )}

            {/* PHASE: result */}
            {testPhase === 'result' && testResult && (
              <div className="px-6 py-5 space-y-4">

                {/* Status banner */}
                <div className={`flex items-start gap-3 p-4 rounded-xl border ${INTAKE_STATUS_BG[testResult.status] || 'bg-slate-700/50 border-slate-600'}`}>
                  {isGood    && <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />}
                  {isFailed  && <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />}
                  {needsWork && <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
                  <div className="min-w-0">
                    <p className={`text-sm font-semibold mb-0.5 ${INTAKE_STATUS_COLOR[testResult.status] || 'text-slate-300'}`}>
                      {statusLabel}
                    </p>
                    {isGood && !testResult.evidence_written && (
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Threshold met — save required for evidence record.
                        Evidence hash, snapshot, and proof artifact are created during the first monitoring run.
                      </p>
                    )}
                    {(testResult.failure_reason) && (
                      <p className="text-xs text-slate-400 leading-relaxed">{testResult.failure_reason}</p>
                    )}
                  </div>
                </div>

                {/* Remediation hint (when not good) */}
                {!isGood && testResult.remediation_hint && (
                  <div className="flex items-start gap-2 bg-slate-800/50 rounded-lg px-3 py-2.5 text-xs text-slate-300">
                    <Info className="w-3.5 h-3.5 text-[#16D9F5] flex-shrink-0 mt-0.5" />
                    <span>{testResult.remediation_hint}</span>
                  </div>
                )}

                {/* Metric grid */}
                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                    <p className="text-slate-500 mb-0.5">Normalized chars</p>
                    <p className="text-slate-200 font-medium">{(testResult.chars || 0).toLocaleString()}</p>
                  </div>
                  <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                    <p className="text-slate-500 mb-0.5">Quality</p>
                    <p className={`font-medium ${testResult.quality === 'GOOD' ? 'text-emerald-400' : testResult.quality === 'ACCEPTABLE' ? 'text-amber-400' : 'text-slate-400'}`}>
                      {testResult.quality || '—'}
                    </p>
                  </div>
                  {testResult.extraction_method && (
                    <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                      <p className="text-slate-500 mb-0.5">Extraction</p>
                      <p className="text-slate-200 font-medium truncate">{testResult.extraction_method}</p>
                    </div>
                  )}
                  {testResult.normalized_hash && (
                    <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                      <p className="text-slate-500 mb-0.5">Content hash</p>
                      <p className="text-slate-200 font-mono font-medium">{testResult.normalized_hash}…</p>
                    </div>
                  )}
                </div>

                {/* Safety flags */}
                {(testResult.nav_shell_detected || testResult.hash_collision) && (
                  <div className="bg-rose-500/5 border border-rose-500/20 rounded-lg px-3 py-2.5 text-xs space-y-1">
                    {testResult.nav_shell_detected && (
                      <p className="text-rose-300">⚠ Nav shell detected — extracted text is primarily navigation items, not regulatory content.</p>
                    )}
                    {testResult.hash_collision && (
                      <p className="text-rose-300">⚠ Hash collision — this source produces identical content to {testResult.collision_source_id || 'another source'}.</p>
                    )}
                  </div>
                )}

                {/* Evidence note */}
                <div className="bg-slate-800/40 rounded-lg px-3 py-2.5 text-xs text-slate-500 flex items-start gap-2">
                  <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  <span>
                    {canSaveForValidation
                      ? 'Readiness threshold met. Save this source to queue it for evidence validation. No evidence record exists yet — the first monitoring run creates the hash, snapshot, and proof artifact.'
                      : 'This source cannot be activated until the extraction issue is resolved. See the remediation hint above.'}
                  </span>
                </div>

                {/* Legal confirmation (shown only when the source can be saved for validation) */}
                {canSaveForValidation && (
                  <label className="flex items-start gap-2.5 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={legalConfirmed}
                      onChange={e => setLegalConfirmed(e.target.checked)}
                      className="mt-0.5 w-4 h-4 rounded border-slate-600 bg-slate-900 text-[#16D9F5] cursor-pointer"
                    />
                    <span className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                      I confirm this is a publicly accessible official source, I am authorized to monitor it, and I understand that StatuteProof monitoring is for information only and does not constitute legal advice.
                    </span>
                  </label>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setTestPhase('idle'); setTestResult(null); setLegalConfirmed(false) }}
                    className="text-xs font-medium text-slate-400 border border-slate-700 hover:border-slate-600 py-2 px-4 rounded-lg transition-colors"
                  >
                    Test another
                  </button>
                  {canSaveForValidation ? (
                    <button
                      onClick={handleSaveSource}
                      disabled={!saveEnabled}
                      className={`flex-1 text-xs font-semibold py-2 rounded-lg transition-colors ${
                        saveEnabled
                          ? 'bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]'
                          : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                      }`}
                    >
                      {saveEnabled ? 'Save for validation' : 'Confirm above to save'}
                    </button>
                  ) : (
                    <button
                      onClick={() => { setShowModal(false); resetModal() }}
                      className="flex-1 text-xs font-medium text-slate-400 border border-slate-700 hover:border-slate-600 py-2 px-4 rounded-lg transition-colors"
                    >
                      Close
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* PHASE: testing */}
            {testPhase === 'testing' && (
              <div className="px-6 py-8">
                <div className="flex items-center gap-2 mb-5">
                  <Loader2 className="w-4 h-4 text-[#16D9F5] animate-spin flex-shrink-0" />
                  <p className="text-sm font-medium text-white">Testing source…</p>
                </div>
                <div className="space-y-2">
                  {TEST_STEPS.map((step, i) => (
                    <div key={step} className={`flex items-center gap-2.5 text-xs transition-colors ${
                      i < stepIndex  ? 'text-emerald-400' :
                      i === stepIndex ? 'text-[#16D9F5]' :
                      'text-slate-600'
                    }`}>
                      {i < stepIndex  && <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />}
                      {i === stepIndex && <Loader2 className="w-3.5 h-3.5 flex-shrink-0 animate-spin" />}
                      {i > stepIndex  && <span className="w-3.5 h-3.5 rounded-full border border-current flex-shrink-0" />}
                      {step}
                    </div>
                  ))}
                </div>
                <p className="mt-5 text-xs text-slate-600">
                  Only public sources are tested. Login, CAPTCHA, and private portals are not supported.
                </p>
              </div>
            )}

            {/* PHASE: idle (form) */}
            {testPhase === 'idle' && (
              <div className="px-6 py-4 space-y-3">
                <p className="text-xs text-slate-400">
                  Test whether a public regulatory source is accessible for monitoring.
                  Only public http(s) sources are supported.
                </p>

                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Source URL *</label>
                  <input
                    type="url"
                    placeholder="https://regulator.gov/publications"
                    value={form.url}
                    onChange={e => { setForm(f => ({ ...f, url: e.target.value })); setFormErrors(er => ({ ...er, url: '' })) }}
                    className={inputCls('url')}
                  />
                  {formErrors.url && <p className="text-rose-400 text-xs mt-1">{formErrors.url}</p>}
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Market *</label>
                  <select
                    value={form.market}
                    onChange={e => { setForm(f => ({ ...f, market: e.target.value })); setFormErrors(er => ({ ...er, market: '' })) }}
                    className={`${inputCls('market')} ${!form.market ? 'text-slate-500' : ''}`}
                  >
                    <option value="">Select market…</option>
                    {MARKETS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                  {formErrors.market && <p className="text-rose-400 text-xs mt-1">{formErrors.market}</p>}
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Category *</label>
                  <select
                    value={form.category}
                    onChange={e => { setForm(f => ({ ...f, category: e.target.value })); setFormErrors(er => ({ ...er, category: '' })) }}
                    className={`${inputCls('category')} ${!form.category ? 'text-slate-500' : ''}`}
                  >
                    <option value="">Select category…</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  {formErrors.category && <p className="text-rose-400 text-xs mt-1">{formErrors.category}</p>}
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Notes (optional)</label>
                  <textarea
                    rows={2}
                    placeholder="Any context about this source…"
                    value={form.notes}
                    onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                    className={`${inputCls('notes')} resize-none`}
                  />
                </div>

                {testError && (
                  <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                    {testError}
                  </p>
                )}

                <div className="pt-1 bg-slate-800/30 rounded-lg px-3 py-2.5 text-xs text-slate-500">
                  StatuteProof only monitors publicly accessible official sources.
                  Login-protected portals, CAPTCHA-gated sites, and private networks are not supported.
                  Testing does not write evidence records.
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setShowModal(false); resetModal() }}
                    className="flex-1 text-xs font-medium text-slate-400 border border-slate-700 hover:border-slate-600 py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTest}
                    className="flex-1 text-xs font-semibold bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] py-2 rounded-lg transition-colors"
                  >
                    Test source
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

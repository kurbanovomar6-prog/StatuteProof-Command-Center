import { useState, useEffect, useRef } from 'react'
import { Plus, X, Loader2, CheckCircle, AlertTriangle, XCircle, Info, History, Hash, Globe } from 'lucide-react'
import { sources as sourcesApi } from '../../api'
import { getWorkspaceProfile } from '../../data/workspaceProfile'
import StatusBadge from './ui/StatusBadge'
import TimeStamp from './ui/TimeStamp'
import EmptyState from './ui/EmptyState'
import ErrorState from './ui/ErrorState'

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
  UNSUPPORTED:           'text-[var(--text-secondary)]',
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
  UNSUPPORTED:           'bg-[var(--bg-tooltip)] border-[var(--border)]',
  BLOCKED:               'bg-rose-500/10 border-rose-500/20',
  PASS:                  'bg-emerald-500/10 border-emerald-500/20',
  NEEDS_ADAPTER:         'bg-amber-500/10 border-amber-500/20',
  FAILED:                'bg-rose-500/10 border-rose-500/20',
}

// Only statuses this table actually produces — no phantom filter options.
const FILTERS   = ['All', 'Readiness supported', 'Needs remediation', 'Monitoring not started', 'User source']
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
  'AE-uae-legislation-portal',
  'AE-uae-financial-intelligence-unit-uaefiu',
  'AE-sca-regulations-listing',
])

function statusFromApiSource(row) {
  if (REMEDIATION_SOURCE_IDS.has(row.source_id) || row.status === 'remediation') return 'Needs remediation'
  if (row.change_status === 'FAILED' || row.change_status === 'QUALITY_DROP') return 'Needs remediation'
  if (!row.last_run_at || row.change_status === 'NOT_RUN') return 'Monitoring not started'
  return 'Readiness supported'
}

const CATEGORY_ACRONYMS = { aml: 'AML', cft: 'CFT', fiu: 'FIU', cma: 'CMA' }

function prettyCategory(value) {
  if (!value) return 'Official source'
  return String(value)
    .split('_')
    .map(word => CATEGORY_ACRONYMS[word.toLowerCase()] || word)
    .join(' ')
    .replace(/^./, c => c.toUpperCase())
}

function mapApiSource(row) {
  return {
    id: row.source_id,
    source_id: row.source_id,
    url: row.url,
    name: row.name || row.source_id || 'Official source',
    market: 'UAE',
    category: prettyCategory(row.category),
    status: statusFromApiSource(row),
    extraction: row.extraction_quality || 'Unknown',
    lastChecked: row.last_run_at || '',
    accessStatus: row.access_status || 'unknown',
    changeStatus: row.change_status || 'NOT_RUN',
    lastEvidenceAt: row.last_evidence_at || '',
    normalizedHash: row.normalized_hash || '',
    proofPath: row.proof_block_path || '',
    timelineEventCount: Number(row.timeline_event_count || 0),
    remediationReason: row.remediation_reason || '',
  }
}

function shortHash(value) {
  const clean = String(value || '').replace(/^sha256:/, '')
  if (!clean) return 'Not recorded'
  return `sha256:${clean.slice(0, 12)}…`
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
  } catch { /* localStorage unavailable — custom source will not persist */ }
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
  const [timelineSource, setTimelineSource] = useState(null)
  const [timelineData, setTimelineData]     = useState(null)
  const [timelineLoading, setTimelineLoading] = useState(false)
  const [timelineError, setTimelineError]   = useState('')
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

  const [reloadKey, setReloadKey] = useState(0)

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
  }, [reloadKey])

  function reloadSources() {
    setSourcesLoading(true)
    setSourcesError('')
    setReloadKey(k => k + 1)
  }

  const filteredReal = realSources.filter(s => {
    if (filter === 'User source') return false
    if (filter === 'All') return true
    return sourceStatusLabel(s.status) === filter
  })

  const filteredCustom = customSources.filter(s => {
    if (filter === 'All' || filter === 'User source') return true
    return sourceStatusLabel(s.status) === filter
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
    `w-full bg-[var(--bg-elevated)] border rounded-lg px-3 py-2 text-sm text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--trust-border)] transition ${
      formErrors[field] ? 'border-rose-500/60' : 'border-[var(--border)]'
    }`

  function sourceStatusLabel(status) {
    if (status === 'Active' || status === 'Validated' || status === 'Confirmed') return 'Readiness supported'
    return status
  }

  async function openTimeline(source) {
    if (source.userSource) return
    setTimelineSource(source)
    setTimelineData(null)
    setTimelineError('')
    setTimelineLoading(true)
    try {
      const data = await sourcesApi.timeline(source.source_id || source.id)
      setTimelineData(data)
    } catch (err) {
      setTimelineError(err.message || 'Could not load source timeline.')
    } finally {
      setTimelineLoading(false)
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
          <p className="text-sm text-[var(--text-secondary)]">
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
          className="flex items-center gap-1.5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add custom source
        </button>
      </div>

      {/* Info banner */}
      <div className="bg-[var(--bg-elevated)] border border-[var(--trust-border)] rounded-xl p-5 mb-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white mb-1">Sources are checked before monitoring activates.</h2>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-3xl">
              StatuteProof tests public official sources for accessibility, extraction quality, and content depth.
              Sources are marked fresh-alert eligible only when meaningful regulatory text is extracted and hashed.
              Custom sources are saved for readiness review — monitoring is not activated automatically.
            </p>
          </div>
          <div className="flex flex-wrap content-start gap-2">
            {['Readiness supported', 'Needs remediation', 'Monitoring not started', 'Under validation'].map(code => (
              <StatusBadge key={code} code={code} />
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
                ? 'bg-[var(--trust-badge)] text-[var(--accent)] border-[var(--trust-border)]'
                : 'text-[var(--text-secondary)] border-[var(--border)] hover:border-[var(--border)] hover:text-[var(--text-primary)]'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl overflow-hidden">
        {sourcesLoading ? (
          <div className="space-y-0 p-4" aria-label="Loading source status">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 border-b border-[var(--border-muted)] py-3 last:border-b-0">
                <div className="sp-skeleton h-4 w-1/3 rounded" />
                <div className="sp-skeleton h-4 w-24 rounded" />
                <div className="sp-skeleton h-5 w-32 rounded-full" />
                <div className="sp-skeleton h-4 w-28 rounded" />
                <div className="sp-skeleton h-4 flex-1 rounded" />
              </div>
            ))}
          </div>
        ) : sourcesError ? (
          <ErrorState title="Could not load live source status." detail={sourcesError} onRetry={reloadSources} />
        ) : allSources.length > 0 ? (
          <table className="sp-table w-full table-fixed text-xs">
            <thead>
              <tr>
                <th className="w-[25%]">Source</th>
                <th className="w-[14%]">Category</th>
                <th className="w-[15%]">Status</th>
                <th className="w-[8%]">Extraction</th>
                <th className="w-[12%]">Last checked</th>
                <th className="w-[15%]">Evidence</th>
                <th className="w-[11%]">Timeline</th>
              </tr>
            </thead>
            <tbody>
              {allSources.map((s, index) => (
                <tr key={`${s.id || s.url || 'source'}-${index}`} className="transition-colors">
                  <td>
                    <p className="truncate font-medium text-white" title={`${s.name} — ${s.url}`}>{s.name}</p>
                    <p className="mt-0.5 truncate text-[11px] text-[var(--text-muted)]">
                      {s.market}
                      {s.userSource && <span className="ml-2 rounded-full border border-[var(--trust-border)] px-1.5 py-0.5 text-[10px] text-[var(--accent)]">User source</span>}
                    </p>
                  </td>
                  <td className="truncate text-[var(--text-secondary)]" title={s.category}>{s.category}</td>
                  <td>
                    <StatusBadge
                      code={sourceStatusLabel(s.status)}
                      explainSuffix={s.remediationReason ? `Note: ${s.remediationReason}` : ''}
                    />
                  </td>
                  <td className="text-[var(--text-secondary)]">{String(s.extraction).toLowerCase().replace(/^./, c => c.toUpperCase())}</td>
                  <td className="text-[var(--text-muted)]">
                    {s.userSource
                      ? <span>{s.lastChecked || 'Saved for validation'}</span>
                      : <TimeStamp value={s.lastChecked} fallback="Not run yet" />}
                  </td>
                  <td className="text-[var(--text-muted)]">
                    <TimeStamp value={s.lastEvidenceAt} fallback="No evidence yet" mode="relative" />
                    <div className="mt-1 flex items-center gap-1 truncate font-mono text-[10px] text-[var(--text-muted)]" title={s.normalizedHash ? `Normalized content hash: ${s.normalizedHash}` : 'No hash recorded yet'}>
                      <Hash className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">{shortHash(s.normalizedHash)}</span>
                    </div>
                  </td>
                  <td>
                    {s.userSource ? (
                      <span className="text-[11px] text-[var(--text-muted)]">Validation pending</span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => openTimeline(s)}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-2.5 py-1.5 text-[11px] font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--border)] hover:text-white"
                      >
                        <History className="h-3.5 w-3.5" />
                        Timeline ({s.timelineEventCount})
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState icon={Globe} title="No sources match the current filter.">
            Change the filter above or test a custom source. Validated official sources
            appear here with their monitoring status and evidence trail.
          </EmptyState>
        )}
      </div>

      {timelineSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(5,11,21,0.82)] p-4">
          <div className="max-h-[86vh] w-full max-w-3xl overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-elevated)] shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-[var(--border-muted)] px-5 py-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Source health timeline</h3>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">{timelineSource.name}</p>
              </div>
              <button onClick={() => setTimelineSource(null)} className="text-[var(--text-muted)] hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
              {timelineLoading ? (
                <div className="py-10 text-center">
                  <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-[var(--accent)]" />
                  <p className="text-sm text-[var(--text-secondary)]">Loading recorded timeline events…</p>
                </div>
              ) : timelineError ? (
                <div className="rounded-lg border border-amber-400/25 bg-amber-400/5 px-4 py-3 text-xs text-amber-300">
                  {timelineError}
                </div>
              ) : timelineData?.events?.length ? (
                <div className="space-y-3">
                  <div className="rounded-lg border border-[var(--trust-border)] bg-[var(--trust-badge)] px-3 py-2 text-xs text-[var(--accent)]">
                    {timelineData.source_health_status}: {timelineData.message}
                  </div>
                  {timelineData.events.slice().reverse().map(event => (
                    <div key={event.event_id} className="rounded-lg border border-[var(--border-muted)] bg-[var(--bg-base)] px-4 py-3">
                      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                        <span className="text-xs font-bold text-white">{String(event.event_type || '').replace(/_/g, ' ')}</span>
                        <TimeStamp value={event.timestamp} mode="absolute" fallback="Timestamp not recorded" className="text-[11px] text-[var(--text-muted)]" />
                      </div>
                      <p className="text-xs leading-relaxed text-[var(--text-primary)]">{event.customer_safe_message}</p>
                      <div className="mt-2 grid gap-2 text-[11px] text-[var(--text-muted)] sm:grid-cols-2">
                        <span>Health: {event.source_health_status || 'not recorded'}</span>
                        <span>Hash: {shortHash(event.normalized_hash)}</span>
                        <span className="truncate">Proof: {event.proof_path || 'not linked'}</span>
                        <span className="truncate">Diff: {event.diff_path || 'not linked'}</span>
                      </div>
                      {event.remediation_reason && (
                        <p className="mt-2 rounded-md border border-amber-400/15 bg-amber-400/5 px-2 py-1.5 text-[11px] text-amber-200">
                          {event.remediation_reason}
                        </p>
                      )}
                      {event.assessment_note_preview && (
                        <p className="mt-2 rounded-md border border-emerald-400/15 bg-emerald-400/5 px-2 py-1.5 text-[11px] text-emerald-200">
                          Assessment: {event.assessment_note_preview}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-10 text-center">
                  <History className="mx-auto mb-3 h-5 w-5 text-[var(--text-muted)]" />
                  <p className="font-medium text-[var(--text-primary)]">No timeline data yet</p>
                  <p className="mt-2 text-sm text-[var(--text-muted)]">
                    No monitoring history has been recorded yet. StatuteProof is not showing sample timeline events in this authenticated view.
                  </p>
                </div>
              )}
              <p className="mt-4 border-t border-[var(--border-muted)] pt-3 text-[10px] text-[var(--text-secondary)]">
                Monitoring intelligence only. Not legal advice. Hash drift and source-health events require human review before customer conclusions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add source modal */}
      {showModal && (
        <div className="fixed inset-0 bg-[rgba(5,11,21,0.82)] flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-elevated)] border border-[var(--border)] rounded-2xl w-full max-w-lg shadow-2xl">

            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-muted)]">
              <h3 className="text-sm font-semibold text-white">Test Custom Source</h3>
              <button onClick={() => { setShowModal(false); resetModal() }} className="text-[var(--text-muted)] hover:text-white">
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
                <p className="text-xs text-[var(--text-secondary)] mb-3">
                  The source appears in your source map. Monitoring activates only after evidence validation is complete.
                </p>
                {saveError && (
                  <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2 mb-4">
                    {saveError}
                  </p>
                )}
                <div className="text-xs text-[var(--text-muted)] bg-[var(--bg-raised)] rounded-lg px-3 py-2 mb-4 text-left">
                  <p className="font-medium text-[var(--text-secondary)] mb-1">Evidence note</p>
                  <p>This test met the readiness threshold without writing an evidence record. A full evidence record with hash, snapshot, and proof artifact is created during the first scheduled monitoring run.</p>
                </div>
                <button
                  onClick={() => { setShowModal(false); resetModal() }}
                  className="text-xs font-medium text-[var(--accent)] border border-[var(--trust-border)] hover:border-[var(--trust-border)] px-4 py-2 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}

            {/* PHASE: saving */}
            {testPhase === 'saving' && (
              <div className="px-6 py-8 text-center">
                <Loader2 className="w-10 h-10 text-[var(--accent)] animate-spin mx-auto mb-3" />
                <p className="text-sm text-[var(--text-primary)]">Saving source…</p>
              </div>
            )}

            {/* PHASE: result */}
            {testPhase === 'result' && testResult && (
              <div className="px-6 py-5 space-y-4">

                {/* Status banner */}
                <div className={`flex items-start gap-3 p-4 rounded-xl border ${INTAKE_STATUS_BG[testResult.status] || 'bg-[var(--bg-tooltip)] border-[var(--border)]'}`}>
                  {isGood    && <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />}
                  {isFailed  && <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />}
                  {needsWork && <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
                  <div className="min-w-0">
                    <p className={`text-sm font-semibold mb-0.5 ${INTAKE_STATUS_COLOR[testResult.status] || 'text-[var(--text-primary)]'}`}>
                      {statusLabel}
                    </p>
                    {isGood && !testResult.evidence_written && (
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                        Threshold met — save required for evidence record.
                        Evidence hash, snapshot, and proof artifact are created during the first monitoring run.
                      </p>
                    )}
                    {(testResult.failure_reason) && (
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{testResult.failure_reason}</p>
                    )}
                  </div>
                </div>

                {/* Remediation hint (when not good) */}
                {!isGood && testResult.remediation_hint && (
                  <div className="flex items-start gap-2 bg-[var(--bg-raised)] rounded-lg px-3 py-2.5 text-xs text-[var(--text-primary)]">
                    <Info className="w-3.5 h-3.5 text-[var(--accent)] flex-shrink-0 mt-0.5" />
                    <span>{testResult.remediation_hint}</span>
                  </div>
                )}

                {/* Metric grid */}
                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
                    <p className="text-[var(--text-muted)] mb-0.5">Normalized chars</p>
                    <p className="text-[var(--text-primary)] font-medium">{(testResult.chars || 0).toLocaleString()}</p>
                  </div>
                  <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
                    <p className="text-[var(--text-muted)] mb-0.5">Quality</p>
                    <p className={`font-medium ${testResult.quality === 'GOOD' ? 'text-emerald-400' : testResult.quality === 'ACCEPTABLE' ? 'text-amber-400' : 'text-[var(--text-secondary)]'}`}>
                      {testResult.quality || '—'}
                    </p>
                  </div>
                  {testResult.extraction_method && (
                    <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
                      <p className="text-[var(--text-muted)] mb-0.5">Extraction</p>
                      <p className="text-[var(--text-primary)] font-medium truncate">{testResult.extraction_method}</p>
                    </div>
                  )}
                  {testResult.normalized_hash && (
                    <div className="bg-[var(--bg-elevated)] rounded-lg px-3 py-2.5">
                      <p className="text-[var(--text-muted)] mb-0.5">Content hash</p>
                      <p className="text-[var(--text-primary)] font-mono font-medium">{testResult.normalized_hash}…</p>
                    </div>
                  )}
                </div>

                {/* Safety flags */}
                {(testResult.nav_shell_detected || testResult.hash_collision) && (
                  <div className="bg-rose-500/5 border border-rose-500/20 rounded-lg px-3 py-2.5 text-xs space-y-1">
                    {testResult.nav_shell_detected && (
                      <p className="flex items-start gap-1.5 text-rose-300"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />Navigation shell detected — extracted text is primarily navigation items, not regulatory content.</p>
                    )}
                    {testResult.hash_collision && (
                      <p className="flex items-start gap-1.5 text-rose-300"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />Hash collision — this source produces identical content to {testResult.collision_source_id || 'another source'}.</p>
                    )}
                  </div>
                )}

                {/* Evidence note */}
                <div className="bg-[var(--bg-raised)] rounded-lg px-3 py-2.5 text-xs text-[var(--text-muted)] flex items-start gap-2">
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
                      className="mt-0.5 w-4 h-4 rounded border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--accent)] cursor-pointer"
                    />
                    <span className="text-xs text-[var(--text-secondary)] leading-relaxed group-hover:text-[var(--text-primary)] transition-colors">
                      I confirm this is a publicly accessible official source, I am authorized to monitor it, and I understand that StatuteProof monitoring is for information only and does not constitute legal advice.
                    </span>
                  </label>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setTestPhase('idle'); setTestResult(null); setLegalConfirmed(false) }}
                    className="text-xs font-medium text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border)] py-2 px-4 rounded-lg transition-colors"
                  >
                    Test another
                  </button>
                  {canSaveForValidation ? (
                    <button
                      onClick={handleSaveSource}
                      disabled={!saveEnabled}
                      className={`flex-1 text-xs font-semibold py-2 rounded-lg transition-colors ${
                        saveEnabled
                          ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)]'
                          : 'bg-[var(--bg-raised)] text-[var(--text-muted)] cursor-not-allowed border border-[var(--border)]'
                      }`}
                    >
                      {saveEnabled ? 'Save for validation' : 'Confirm above to save'}
                    </button>
                  ) : (
                    <button
                      onClick={() => { setShowModal(false); resetModal() }}
                      className="flex-1 text-xs font-medium text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border)] py-2 px-4 rounded-lg transition-colors"
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
                  <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin flex-shrink-0" />
                  <p className="text-sm font-medium text-white">Testing source…</p>
                </div>
                <div className="space-y-2">
                  {TEST_STEPS.map((step, i) => (
                    <div key={step} className={`flex items-center gap-2.5 text-xs transition-colors ${
                      i < stepIndex  ? 'text-emerald-400' :
                      i === stepIndex ? 'text-[var(--accent)]' :
                      'text-[var(--text-muted)]'
                    }`}>
                      {i < stepIndex  && <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />}
                      {i === stepIndex && <Loader2 className="w-3.5 h-3.5 flex-shrink-0 animate-spin" />}
                      {i > stepIndex  && <span className="w-3.5 h-3.5 rounded-full border border-current flex-shrink-0" />}
                      {step}
                    </div>
                  ))}
                </div>
                <p className="mt-5 text-xs text-[var(--text-muted)]">
                  Only public sources are tested. Login, CAPTCHA, and private portals are not supported.
                </p>
              </div>
            )}

            {/* PHASE: idle (form) */}
            {testPhase === 'idle' && (
              <div className="px-6 py-4 space-y-3">
                <p className="text-xs text-[var(--text-secondary)]">
                  Test whether a public regulatory source is accessible for monitoring.
                  Only public http(s) sources are supported.
                </p>

                <div>
                  <label htmlFor="custom-source-url" className="block text-xs text-[var(--text-secondary)] mb-1.5">Source URL *</label>
                  <input
                    id="custom-source-url"
                    type="url"
                    placeholder="https://regulator.gov/publications"
                    value={form.url}
                    onChange={e => { setForm(f => ({ ...f, url: e.target.value })); setFormErrors(er => ({ ...er, url: '' })) }}
                    className={inputCls('url')}
                  />
                  {formErrors.url && <p className="text-rose-400 text-xs mt-1">{formErrors.url}</p>}
                </div>

                <div>
                  <label htmlFor="custom-source-market" className="block text-xs text-[var(--text-secondary)] mb-1.5">Market *</label>
                  <select
                    id="custom-source-market"
                    value={form.market}
                    onChange={e => { setForm(f => ({ ...f, market: e.target.value })); setFormErrors(er => ({ ...er, market: '' })) }}
                    className={`${inputCls('market')} ${!form.market ? 'text-[var(--text-muted)]' : ''}`}
                  >
                    <option value="">Select market…</option>
                    {MARKETS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                  {formErrors.market && <p className="text-rose-400 text-xs mt-1">{formErrors.market}</p>}
                </div>

                <div>
                  <label htmlFor="custom-source-category" className="block text-xs text-[var(--text-secondary)] mb-1.5">Category *</label>
                  <select
                    id="custom-source-category"
                    value={form.category}
                    onChange={e => { setForm(f => ({ ...f, category: e.target.value })); setFormErrors(er => ({ ...er, category: '' })) }}
                    className={`${inputCls('category')} ${!form.category ? 'text-[var(--text-muted)]' : ''}`}
                  >
                    <option value="">Select category…</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  {formErrors.category && <p className="text-rose-400 text-xs mt-1">{formErrors.category}</p>}
                </div>

                <div>
                  <label htmlFor="custom-source-notes" className="block text-xs text-[var(--text-secondary)] mb-1.5">Notes (optional)</label>
                  <textarea
                    id="custom-source-notes"
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

                <div className="pt-1 bg-[var(--bg-raised)] rounded-lg px-3 py-2.5 text-xs text-[var(--text-muted)]">
                  StatuteProof only monitors publicly accessible official sources.
                  Login-protected portals, CAPTCHA-gated sites, and private networks are not supported.
                  Testing does not write evidence records.
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setShowModal(false); resetModal() }}
                    className="flex-1 text-xs font-medium text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border)] py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTest}
                    className="flex-1 text-xs font-semibold bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-[var(--ink)] py-2 rounded-lg transition-colors"
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

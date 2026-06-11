import { useState, useEffect, useRef } from 'react'
import { Plus, X, Loader2, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import { MOCK_SOURCES } from '../../data/appMockData'
import { getWorkspaceProfile, filterSources } from '../../data/workspaceProfile'
import { profile as profileApi } from '../../api'

const HEALTH_STYLE = {
  PASS:    'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  Review:  'text-amber-400   bg-amber-500/10   border-amber-500/20',
  Limited: 'text-slate-400   bg-slate-700      border-slate-600',
}
const STATUS_STYLE = {
  Active:           'text-emerald-400',
  Validated:        'text-emerald-400',
  Limited:          'text-amber-400',
  Partial:          'text-slate-400',
  'Needs adapter':  'text-amber-400',
}

const FILTERS = ['All', 'Validated', 'Limited', 'Partial', 'Needs adapter', 'User source']

const MARKETS = ['UAE', 'DIFC', 'ADGM', 'Other UAE source']
const CATEGORIES = [
  'Central bank', 'Financial regulator', 'Crypto regulator', 'AML authority',
  'Capital markets', 'Tax authority', 'Legal database', 'Other',
]

const TEST_STEPS = [
  'Checking HTML accessibility…',
  'Looking for PDF documents…',
  'Checking RSS / sitemap…',
  'Evaluating content quality…',
]

const RESULT_MSG = {
  PASS:          'Source validation request saved.',
  LIMITED:       'Source saved for review. Additional configuration may be needed before monitoring.',
  NEEDS_ADAPTER: 'Source saved for adapter setup. StatuteProof may need a custom connector for this portal.',
  FAILED:        'Source could not be monitored reliably. Try another URL or contact support.',
}

function loadCustomSources() {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    return Array.isArray(p.customSources) ? p.customSources.map(normalizeCustomSource) : []
  } catch (e) {
    console.warn('loadCustomSources failed', e)
    return []
  }
}

function normalizeCustomSource(source) {
  let hostname = source.name || source.url || 'User source'
  try { if (source.url) hostname = new URL(source.url).hostname } catch { /* keep fallback */ }
  return {
    id: source.id || `user-${source.url || hostname}`,
    name: source.name || hostname,
    flag: source.flag || '🌐',
    market: source.market || '',
    category: source.category || '',
    status: source.status || 'Limited',
    extraction: source.extraction || 'Unknown',
    lastChecked: source.lastChecked || 'Saved',
    health: source.health || 'Review',
    userSource: true,
    ...source,
  }
}

function persistCustomSource(source) {
  try {
    const p = JSON.parse(localStorage.getItem('regradar_workspace_profile') || '{}')
    p.customSources = [...(p.customSources || []), source]
    localStorage.setItem('regradar_workspace_profile', JSON.stringify(p))
    return p.customSources
  } catch (e) {
    console.warn('persistCustomSource failed', e)
    return [source]
  }
}

function backendCustomSources(sources) {
  return sources
    .filter(s => typeof s?.url === 'string' && /^https?:\/\//.test(s.url))
    .map(s => ({
      url: s.url,
      market: s.market || '',
      category: s.category || '',
      notes: s.notes || '',
      status: s.status || '',
    }))
}

export default function SourcesPage() {
  const profile = getWorkspaceProfile()

  const [filter, setFilter]               = useState('All')
  const [showModal, setShowModal]         = useState(false)
  const [form, setForm]                   = useState({ url: '', market: profile.markets[0] || '', category: '', notes: '' })
  const [formErrors, setFormErrors]       = useState({})
  const [testPhase, setTestPhase]         = useState('idle')  // idle | testing | result | saved
  const [testResult, setTestResult]       = useState(null)
  const [testError, setTestError]         = useState('')
  const [saveWarning, setSaveWarning]     = useState('')
  const [stepIndex, setStepIndex]         = useState(0)
  const [customSources, setCustomSources] = useState(loadCustomSources)
  const stepTimer                         = useRef(null)

  // Manage step animation interval while testing (stepIndex reset happens in handleTest)
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

  const filteredMock = filterSources(MOCK_SOURCES, profile).filter(s => {
    if (filter === 'User source') return false
    if (filter === 'All') return true
    if (filter === 'Validated') return s.status === 'Active' || s.status === 'Validated'
    if (filter === 'Needs adapter') return s.extraction.includes('adapter') || s.extraction.includes('Geo')
    return s.status === filter
  })

  const filteredCustom = customSources.filter(s => {
    if (filter === 'All' || filter === 'User source') return true
    if (filter === 'Validated') return s.status === 'Active' || s.status === 'Validated'
    if (filter === 'Needs adapter') return s.status === 'Needs adapter'
    return s.status === filter
  })

  const allSources = [...filteredMock, ...filteredCustom]

  function resetModal() {
    setTestPhase('idle')
    setTestResult(null)
    setTestError('')
    setSaveWarning('')
    setFormErrors({})
    setForm({ url: '', market: profile.markets[0] || '', category: '', notes: '' })
  }

  function validate() {
    const errs = {}
    if (!form.url.trim())      errs.url      = 'URL is required.'
    else if (!/^https?:\/\//.test(form.url)) errs.url = 'Enter a valid URL starting with http(s)://'
    if (!form.market.trim())   errs.market   = 'Market is required.'
    if (!form.category.trim()) errs.category = 'Category is required.'
    return errs
  }

  async function handleTest() {
    const errs = validate()
    if (Object.keys(errs).length) { setFormErrors(errs); return }
    setStepIndex(0)
    setTestPhase('testing')
    setTestError('')
    try {
      const res  = await fetch('/api/source-test', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ url: form.url, market: form.market, category: form.category }),
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
      setTestError('API server not running. Start with: python run.py api')
      setTestPhase('idle')
    }
  }

  function handleSaveSource() {
    let hostname = form.url
    try { hostname = new URL(form.url).hostname } catch { /* use raw url as fallback */ }

    const source = {
      id:          `user-${Date.now()}`,
      url:         form.url,
      name:        hostname,
      flag:        '🌐',
      market:      form.market,
      category:    form.category,
      notes:       form.notes,
      status:      testResult.status === 'PASS' ? 'Validated' : testResult.status === 'NEEDS_ADAPTER' ? 'Needs adapter' : 'Limited',
      extraction:  testResult.extraction?.join(' + ') || 'Unknown',
      lastChecked: 'Just added',
      health:      testResult.status === 'PASS' ? 'PASS' : 'Review',
      userSource:  true,
    }
    const updatedCustomSources = persistCustomSource(source)
    setCustomSources(cs => [...cs, source])
    profileApi.update({ custom_sources: backendCustomSources(updatedCustomSources) }).catch(err => {
      console.warn('profile custom source save failed', err)
      setSaveWarning('Source added locally. Backend profile sync failed; try saving settings again.')
    })
    setTestPhase('saved')
  }

  const inputCls = (field) =>
    `w-full bg-slate-900 border rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-[#16D9F5]/50 transition ${
      formErrors[field] ? 'border-rose-500/60' : 'border-slate-700'
    }`

  function sourceStatusLabel(status) {
    return status === 'Active' ? 'Validated' : status
  }

  function lastCheckedLabel(source) {
    if (source.userSource) return source.lastChecked
    return 'Readiness snapshot'
  }

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
          onClick={() => { resetModal(); setShowModal(true) }}
          className="flex items-center gap-1.5 bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Request validation
        </button>
      </div>

      <div className="bg-[#0D1B2E] border border-cyan-400/20 rounded-xl p-5 mb-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white mb-1">Your source map is based on your saved profile.</h2>
            <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
              Adding a source here requests validation. It does not activate production monitoring automatically.
              Validated sources only enter a pilot profile after access, extraction and proof/diff checks.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              ['Validated', 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300'],
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
        {allSources.length > 0 ? (
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
                    <td className={`px-4 py-3 font-medium whitespace-nowrap ${STATUS_STYLE[sourceStatusLabel(s.status)] || STATUS_STYLE[s.status] || 'text-slate-400'}`}>{sourceStatusLabel(s.status)}</td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{s.extraction}</td>
                    <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{lastCheckedLabel(s)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${HEALTH_STYLE[s.health] || 'text-slate-400 bg-slate-700 border-slate-600'}`}>
                        {s.health}
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
            <p className="text-xs text-slate-600">Try changing your filter or add a source.</p>
          </div>
        )}
      </div>

      {/* Add source modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0D1B2E] border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl">

            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-white">Test Source Compatibility</h3>
              <button onClick={() => { setShowModal(false); resetModal() }} className="text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* PHASE: saved */}
            {testPhase === 'saved' && (
              <div className="px-6 py-8 text-center">
                <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                <p className="text-sm font-semibold text-white mb-1">
                  {RESULT_MSG[testResult?.status] || RESULT_MSG.PASS}
                </p>
                <p className="text-xs text-slate-400 mb-5">
                  {testResult?.status === 'PASS'
                    ? 'The source now appears in your source map for review.'
                    : 'The source is saved with its current status.'}
                </p>
                {saveWarning && (
                  <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2 mb-4">
                    {saveWarning}
                  </p>
                )}
                <button
                  onClick={() => { setShowModal(false); resetModal() }}
                  className="text-xs font-medium text-[#16D9F5] border border-[#16D9F5]/30 hover:border-[#16D9F5]/60 px-4 py-2 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}

            {/* PHASE: result */}
            {testPhase === 'result' && testResult && (
              <div className="px-6 py-5 space-y-4">
                {/* Status banner */}
                <div className={`flex items-start gap-3 p-4 rounded-xl border ${
                  testResult.status === 'PASS'
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : testResult.status === 'FAILED'
                    ? 'bg-rose-500/10 border-rose-500/20'
                    : 'bg-amber-500/10 border-amber-500/20'
                }`}>
                  {testResult.status === 'PASS'    && <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />}
                  {testResult.status === 'FAILED'  && <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />}
                  {testResult.status !== 'PASS' && testResult.status !== 'FAILED' && <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />}
                  <div>
                    <p className={`text-sm font-semibold mb-0.5 ${
                      testResult.status === 'PASS' ? 'text-emerald-400' :
                      testResult.status === 'FAILED' ? 'text-rose-400' : 'text-amber-400'
                    }`}>{testResult.recommendation}</p>
                    <p className="text-xs text-slate-400 leading-relaxed">{testResult.message}</p>
                  </div>
                </div>

                {/* Details */}
                {testResult.status !== 'FAILED' && (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                      <p className="text-slate-500 mb-0.5">Extraction</p>
                      <p className="text-slate-200 font-medium">{testResult.extraction?.join(' + ') || '—'}</p>
                    </div>
                    <div className="bg-slate-900 rounded-lg px-3 py-2.5">
                      <p className="text-slate-500 mb-0.5">Content size</p>
                      <p className="text-slate-200 font-medium">{testResult.chars?.toLocaleString() || '0'} chars</p>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => { setTestPhase('idle'); setTestResult(null) }}
                    className="text-xs font-medium text-slate-400 border border-slate-700 hover:border-slate-600 py-2 px-4 rounded-lg transition-colors"
                  >
                    Test another
                  </button>
                  {testResult.status !== 'FAILED' && (
                    <button
                      onClick={handleSaveSource}
                      className={`flex-1 text-xs font-semibold py-2 rounded-lg transition-colors ${
                        testResult.status === 'PASS'
                          ? 'bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]'
                          : 'border border-amber-500/40 text-amber-400 hover:border-amber-500/70'
                      }`}
                    >
                      {testResult.status === 'PASS' ? 'Save validation request' : 'Save for review'}
                    </button>
                  )}
                  {testResult.status === 'FAILED' && (
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
                  <p className="text-sm font-medium text-white">Testing source compatibility…</p>
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
                  Compatibility test — validation preview for this workspace.
                </p>
              </div>
            )}

            {/* PHASE: idle (form) */}
            {testPhase === 'idle' && (
              <div className="px-6 py-4 space-y-3">

                <p className="text-xs text-slate-400">
                  Add a source URL to test whether StatuteProof can monitor it automatically.
                </p>

                {/* URL */}
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

                {/* Market */}
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

                {/* Category */}
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

                {/* Notes */}
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
                    Test compatibility
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

import { useEffect, useState } from 'react'
import { Search, Download, CheckCircle, ChevronDown, ChevronUp, Shield, Send } from 'lucide-react'
import { SourceProofPanel } from '../SourceProofPanel'
import { MOCK_ALERTS } from '../../data/appMockData'
import { getWorkspaceProfile, filterAlerts } from '../../data/workspaceProfile'
import { delivery } from '../../api'

const RISK_DARK = {
  HIGH:   'text-red-400   bg-red-500/15   border border-red-500/30',
  MEDIUM: 'text-amber-400 bg-amber-500/15 border border-amber-500/30',
  LOW:    'text-emerald-400 bg-emerald-500/15 border border-emerald-500/30',
}


export default function AlertsPage() {
  const profile    = getWorkspaceProfile()
  const baseAlerts = filterAlerts(MOCK_ALERTS, profile)

  const [selectedId,   setSelectedId]   = useState(baseAlerts[0]?.id || 'a1')
  const [riskFilter,   setRiskFilter]   = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')
  const [search,       setSearch]       = useState('')
  const [reviewed,     setReviewed]     = useState(new Set())
  const [proofOpen,    setProofOpen]    = useState(false)
  const [preview,      setPreview]      = useState(null)
  const [previewLoading, setPreviewLoading] = useState(true)
  const [previewError, setPreviewError] = useState('')
  const [sendState,    setSendState]    = useState({})

  useEffect(() => {
    let active = true
    async function loadPreview() {
      setPreviewLoading(true)
      setPreviewError('')
      try {
        const data = await delivery.preview(14)
        if (active) setPreview(data.preview)
      } catch (err) {
        if (active) setPreviewError(err.message || 'Could not load routing preview.')
      } finally {
        if (active) setPreviewLoading(false)
      }
    }
    loadPreview()
    return () => { active = false }
  }, [])

  function selectAlert(id) {
    setSelectedId(id)
    setProofOpen(false)
  }

  const filtered = baseAlerts.filter(a => {
    if (riskFilter !== 'All' && a.risk !== riskFilter) return false
    if (statusFilter !== 'All' && a.status !== statusFilter) return false
    if (search && !a.title.toLowerCase().includes(search.toLowerCase()) && !a.source.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const alert = baseAlerts.find(a => a.id === selectedId) || baseAlerts[0]

  function handleMarkReviewed(id) { setReviewed(prev => new Set([...prev, id])) }

  async function handleSendPreviewAlert(alertId) {
    setSendState(prev => ({ ...prev, [alertId]: { status: 'sending', message: '' } }))
    try {
      const result = await delivery.sendPreviewAlert(alertId)
      setSendState(prev => ({
        ...prev,
        [alertId]: { status: 'ok', message: result.message || 'Preview alert sent.' },
      }))
      const data = await delivery.preview(14)
      setPreview(data.preview)
    } catch (err) {
      setSendState(prev => ({
        ...prev,
        [alertId]: { status: 'error', message: err.message || 'Could not send preview alert.' },
      }))
    }
  }

  const reviewedMatches = preview?.matches || []

  return (
    <div className="p-5 flex flex-col h-full">
      <div className="mb-4">
        <h1 className="text-lg font-bold text-white mb-1">Sample Alerts</h1>
        <p className="text-sm text-slate-400">
          {profile.markets.length > 0
            ? `Sample alert previews for: ${profile.markets.join(', ')}${profile.industries.length ? ` · ${profile.industries.join(', ')}` : ''}${profile.topics.length ? ` · ${profile.topics.slice(0, 4).join(', ')}` : ''}`
            : 'Sample alert previews — select markets in Settings to filter.'}
        </p>
      </div>

      <div className="mb-4 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Reviewed alert routing preview</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Approved alerts are matched against your saved profile before delivery. Manual preview delivery is available for reviewed alert previews when Telegram is connected. Automatic scheduled delivery is not enabled yet.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Approved only', 'Profile matched', 'Manual send', 'No bulk delivery'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mb-4 rounded-xl border border-slate-800 bg-[#0A1628] p-4">
        {previewLoading && (
          <p className="text-sm text-slate-400">Loading reviewed alert preview...</p>
        )}
        {!previewLoading && previewError && (
          <p className="text-sm text-rose-300">{previewError}</p>
        )}
        {!previewLoading && !previewError && reviewedMatches.length === 0 && (
          <div>
            <p className="text-sm font-semibold text-white">No approved reviewed alerts found in the last 14 days.</p>
            <p className="mt-1 text-sm text-slate-500">
              Sample format previews are still shown below. No fake approved alerts are created for this empty state.
            </p>
          </div>
        )}
        {!previewLoading && !previewError && reviewedMatches.length > 0 && (
          <div className="space-y-3">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-white">
                  {reviewedMatches.length} approved reviewed alert{reviewedMatches.length === 1 ? '' : 's'} considered
                </p>
                <p className="text-xs text-slate-500">
                  {preview.profile_ready ? 'Profile is ready for manual preview delivery.' : (preview.not_ready_reasons || []).join(' ')}
                </p>
              </div>
              <span className="rounded-full border border-amber-400/25 bg-amber-400/10 px-2.5 py-1 text-[11px] font-semibold text-amber-200">
                Dry-run only
              </span>
            </div>
            <div className="grid gap-3 xl:grid-cols-2">
              {reviewedMatches.map(item => {
                const state = sendState[item.alert_id] || {}
                const disabled = !item.delivery_ready || state.status === 'sending'
                const disabledText = item.already_sent
                  ? 'Sent'
                  : !item.matched
                  ? 'Not matched to profile'
                  : item.not_ready_reasons?.[0] || 'Not ready'
                return (
                  <div key={item.alert_id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${RISK_DARK[item.risk_level] || RISK_DARK.MEDIUM}`}>
                        {item.risk_level}
                      </span>
                      <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                        {item.review_status || 'Approved'}
                      </span>
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
                        item.matched
                          ? 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200'
                          : 'border-slate-700 bg-slate-900 text-slate-400'
                      }`}>
                        Relevance {item.score}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-white">{item.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.market || item.jurisdiction || 'Market not specified'} · {item.source_name}</p>
                    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-slate-400">{item.executive_summary}</p>
                    {item.reasons?.length > 0 && (
                      <div className="mt-3 space-y-1">
                        {item.reasons.slice(0, 3).map(reason => (
                          <p key={reason} className="text-[11px] text-slate-400">
                            <span className="text-cyan-300">•</span> {reason}
                          </p>
                        ))}
                      </div>
                    )}
                    {item.limitations?.length > 0 && (
                      <p className="mt-2 text-[11px] text-amber-200/80">
                        Limitation: {item.limitations[0]}
                      </p>
                    )}
                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-flex text-[11px] font-medium text-cyan-300 hover:text-cyan-200"
                      >
                        Source proof URL
                      </a>
                    )}
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        disabled={disabled}
                        onClick={() => handleSendPreviewAlert(item.alert_id)}
                        className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${
                          disabled
                            ? 'cursor-not-allowed border-slate-700 bg-slate-800/70 text-slate-500'
                            : 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/15'
                        }`}
                      >
                        <Send className="h-3.5 w-3.5" />
                        {state.status === 'sending' ? 'Sending...' : item.delivery_ready ? 'Send preview to Telegram' : disabledText}
                      </button>
                      {state.message && (
                        <span className={`text-xs ${state.status === 'ok' ? 'text-emerald-300' : 'text-rose-300'}`}>
                          {state.message}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Sample format preview</h2>
        <p className="mt-1 text-xs text-slate-500">
          These examples show the alert format only. They are not live approved alerts.
        </p>
      </div>

      <div className="flex-1 grid lg:grid-cols-[320px_1fr] gap-4 min-h-0">

        {/* Left: alert list */}
        <div className="flex flex-col min-h-0">
          <div className="space-y-2 mb-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search alerts…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {['All','HIGH','MEDIUM','LOW'].map(r => (
                <button key={r} onClick={() => setRiskFilter(r)}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${riskFilter === r ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-400 border-slate-700 hover:text-slate-300'}`}>
                  {r}
                </button>
              ))}
              <span className="text-slate-700">|</span>
              {['All','Review required','In review','Monitored'].map(s => (
                <button key={s} onClick={() => setStatusFilter(s)}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${statusFilter === s ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-400 border-slate-700 hover:text-slate-300'}`}>
                  {s === 'All' ? 'All status' : s}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2">
            {baseAlerts.length === 0 && (
              <div className="text-center py-10 px-4">
                <p className="text-sm text-slate-400 mb-1">No alerts for your selected profile yet.</p>
                <p className="text-xs text-slate-600">Add more markets or sources in Settings → Monitoring profile.</p>
              </div>
            )}
            {filtered.map(a => (
              <button
                key={a.id}
                onClick={() => selectAlert(a.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  selectedId === a.id
                    ? 'border-cyan-500/30 bg-slate-900 ring-1 ring-cyan-500/20'
                    : 'border-slate-800 bg-slate-900 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[a.risk]}`}>{a.risk}</span>
                  <span className="text-xs text-slate-500">{a.date}</span>
                </div>
                <p className="text-xs font-semibold text-white leading-snug mb-1">{a.title}</p>
                <p className="text-xs text-slate-500">{a.flag} {a.market} · {a.source}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                    {reviewed.has(a.id) ? 'Reviewed locally' : a.reviewStatus || 'Reviewed sample'}
                  </span>
                  <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-200">
                    Preview only
                  </span>
                </div>
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-8">No alerts match the current filters.</p>
            )}
          </div>
        </div>

        {/* Right: alert detail */}
        <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl flex flex-col min-h-0 overflow-hidden">
          {!alert && (
            <div className="flex-1 flex items-center justify-center text-center px-6 py-12">
              <div>
                <p className="text-sm text-slate-400 mb-1">No alert selected.</p>
                <p className="text-xs text-slate-600">Select an alert from the list.</p>
              </div>
            </div>
          )}
          {alert && (<>
          <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_DARK[alert.risk]}`}>{alert.risk}</span>
              <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-xs font-semibold text-cyan-200">Sample preview</span>
              <span className="text-xs text-slate-400">{alert.flag} {alert.market} · {alert.source}</span>
            </div>
            <span className="text-xs text-slate-500">{alert.date}</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800 text-xs">
            <div className="px-5 py-4">
              <h3 className="text-sm font-semibold text-white mb-2">{alert.title}</h3>
              <p className="text-slate-300 leading-relaxed">{alert.summary}</p>
            </div>
            <div className="px-5 py-4">
              <p className="text-slate-500 mb-1.5 uppercase tracking-wide font-medium">Why It Matters</p>
              <p className="text-slate-300 leading-relaxed">{alert.whyMatters}</p>
            </div>
            <div className="px-5 py-4">
              <p className="text-slate-500 mb-2 uppercase tracking-wide font-medium">Affected Organizations</p>
              <div className="flex flex-wrap gap-1.5">
                {alert.affected.map(e => (
                  <span key={e} className="bg-slate-800 border border-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{e}</span>
                ))}
              </div>
            </div>
            <div className="px-5 py-4 grid sm:grid-cols-3 gap-4">
              {[
                { label: 'Change type', value: alert.changeType || 'Regulatory update' },
                { label: 'Deadline',    value: alert.deadline },
                { label: 'Profile relevance', value: alert.affected?.slice(0, 2).join(', ') || 'Review required' },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-slate-500 mb-0.5 uppercase tracking-wide font-medium">{label}</p>
                  <p className="text-slate-200 font-medium">{value}</p>
                </div>
              ))}
            </div>
            <div className="px-5 py-4">
              <p className="text-slate-500 mb-2 uppercase tracking-wide font-medium">Required Action</p>
              <ol className="space-y-1.5">
                {alert.steps.map((s, i) => (
                  <li key={i} className="flex gap-2 text-slate-300 leading-relaxed">
                    <span className="text-cyan-400 font-semibold flex-shrink-0">{i + 1}.</span>
                    {s}
                  </li>
                ))}
              </ol>
            </div>
            <div className="px-5 py-4">
              <p className="text-slate-500 mb-1.5 uppercase tracking-wide font-medium">Limitation note</p>
              <p className="text-slate-300 leading-relaxed">{alert.limitationNote || 'Sample preview. Manual reviewed alert preview delivery is available from approved routing previews; automatic scheduled delivery is not enabled yet.'}</p>
            </div>
            <div className="px-5 py-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-slate-500 uppercase tracking-wide font-medium">Evidence Trail</p>
                <button
                  onClick={() => setProofOpen(v => !v)}
                  className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  <Shield className="w-3 h-3" />
                  Source proof
                  {proofOpen
                    ? <ChevronUp className="w-3 h-3" />
                    : <ChevronDown className="w-3 h-3" />
                  }
                </button>
              </div>
              {['Reviewed sample', 'Source proof available', 'Human review gate', 'Limitation disclosed'].map(e => (
                <div key={e} className="flex items-center gap-1.5 text-slate-400 mb-1">
                  <span className="text-emerald-400 font-bold">✓</span> {e}
                </div>
              ))}
              {proofOpen && <SourceProofPanel alert={alert} />}
            </div>
          </div>

          {/* Actions */}
          <div className="px-5 py-3.5 border-t border-slate-800 flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => handleMarkReviewed(alert.id)}
              disabled={reviewed.has(alert.id)}
              className={`flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border transition-colors ${
                reviewed.has(alert.id)
                  ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10'
                  : 'border-slate-700 text-slate-300 hover:border-slate-600 hover:text-white'
              }`}
            >
              <CheckCircle className="w-3.5 h-3.5" />
              {reviewed.has(alert.id) ? 'Reviewed' : 'Mark reviewed'}
            </button>
            <button className="flex items-center gap-1.5 text-xs font-medium text-slate-300 border border-slate-700 hover:border-slate-600 px-3 py-2 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" />
              Preview export
            </button>
            <button
              type="button"
              disabled
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-slate-700 bg-slate-800/70 text-slate-500 cursor-not-allowed"
              title="Use reviewed routing previews above for manual Telegram preview delivery."
            >
              Preview only
            </button>
            <span className="text-xs text-slate-500">Sample cards stay preview-only. Use reviewed routing previews above for manual Telegram preview delivery.</span>
          </div>
          </>)}
        </div>
      </div>
    </div>
  )
}
